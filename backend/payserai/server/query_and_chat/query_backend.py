from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from payserai.auth.users import current_admin_user
from payserai.auth.users import current_user
from payserai.configs.chat_configs import DISABLE_LLM_CHUNK_FILTER
from payserai.configs.constants import DocumentSource
from payserai.db.engine import get_session
from payserai.db.models import User
from payserai.db.tag import get_tags_by_value_prefix_for_source_types
from payserai.document_index.factory import get_default_document_index
from payserai.document_index.vespa.index import VespaIndex
from payserai.one_shot_answer.answer_question import stream_search_answer
from payserai.one_shot_answer.models import DirectQARequest
from payserai.search.access_filters import build_access_filters_for_user
from payserai.search.payserai_helper import recommend_search_flow
from payserai.search.models import IndexFilters
from payserai.search.models import SavedSearchDoc
from payserai.search.models import SearchDoc
from payserai.search.models import SearchQuery
from payserai.search.models import SearchResponse
from payserai.search.search_runner import chunks_to_search_docs
from payserai.search.search_runner import full_chunk_search
from payserai.secondary_llm_flows.query_validation import get_query_answerability
from payserai.secondary_llm_flows.query_validation import stream_query_answerability
from payserai.server.query_and_chat.models import AdminSearchRequest
from payserai.server.query_and_chat.models import AdminSearchResponse
from payserai.server.query_and_chat.models import DocumentSearchRequest
from payserai.server.query_and_chat.models import HelperResponse
from payserai.server.query_and_chat.models import QueryValidationResponse
from payserai.server.query_and_chat.models import SimpleQueryRequest
from payserai.server.query_and_chat.models import SourceTag
from payserai.server.query_and_chat.models import TagResponse
from payserai.utils.logger import setup_logger

logger = setup_logger()

admin_router = APIRouter(prefix="/admin")
basic_router = APIRouter(prefix="/query")


@admin_router.post("/search")
def admin_search(
    question: AdminSearchRequest,
    user: User | None = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> AdminSearchResponse:
    query = question.query
    logger.info(f"Received admin search query: {query}")

    user_acl_filters = build_access_filters_for_user(user, db_session)
    final_filters = IndexFilters(
        source_type=question.filters.source_type,
        document_set=question.filters.document_set,
        time_cutoff=question.filters.time_cutoff,
        access_control_list=user_acl_filters,
    )
    document_index = get_default_document_index()
    if not isinstance(document_index, VespaIndex):
        raise HTTPException(
            status_code=400,
            detail="Cannot use admin-search when using a non-Vespa document index",
        )

    matching_chunks = document_index.admin_retrieval(query=query, filters=final_filters)

    documents = chunks_to_search_docs(matching_chunks)

    # Deduplicate documents by id
    deduplicated_documents: list[SearchDoc] = []
    seen_documents: set[str] = set()
    for document in documents:
        if document.document_id not in seen_documents:
            deduplicated_documents.append(document)
            seen_documents.add(document.document_id)
    return AdminSearchResponse(documents=deduplicated_documents)


@basic_router.get("/valid-tags")
def get_tags(
    match_pattern: str | None = None,
    # If this is empty or None, then tags for all sources are considered
    sources: list[DocumentSource] | None = None,
    allow_prefix: bool = True,  # This is currently the only option
    _: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> TagResponse:
    if not allow_prefix:
        raise NotImplementedError("Cannot disable prefix match for now")

    db_tags = get_tags_by_value_prefix_for_source_types(
        tag_value_prefix=match_pattern,
        sources=sources,
        db_session=db_session,
    )
    server_tags = [
        SourceTag(
            tag_key=db_tag.tag_key, tag_value=db_tag.tag_value, source=db_tag.source
        )
        for db_tag in db_tags
    ]
    return TagResponse(tags=server_tags)


@basic_router.post("/search-intent")
def get_search_type(
    simple_query: SimpleQueryRequest, _: User = Depends(current_user)
) -> HelperResponse:
    logger.info(f"Calculating intent for {simple_query.query}")
    return recommend_search_flow(simple_query.query)


@basic_router.post("/query-validation")
def query_validation(
    simple_query: SimpleQueryRequest, _: User = Depends(current_user)
) -> QueryValidationResponse:
    # Note if weak model prompt is chosen, this check does not occur and will simply return that
    # the query is valid, this is because weaker models cannot really handle this task well.
    # Additionally, some weak model servers cannot handle concurrent inferences.
    logger.info(f"Validating query: {simple_query.query}")
    reasoning, answerable = get_query_answerability(simple_query.query)
    return QueryValidationResponse(reasoning=reasoning, answerable=answerable)


@basic_router.post("/stream-query-validation")
def stream_query_validation(
    simple_query: SimpleQueryRequest, _: User = Depends(current_user)
) -> StreamingResponse:
    # Note if weak model prompt is chosen, this check does not occur and will simply return that
    # the query is valid, this is because weaker models cannot really handle this task well.
    # Additionally, some weak model servers cannot handle concurrent inferences.
    logger.info(f"Validating query: {simple_query.query}")
    return StreamingResponse(
        stream_query_answerability(simple_query.query), media_type="application/json"
    )


@basic_router.post("/document-search")
def handle_search_request(
    search_request: DocumentSearchRequest,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
    # Default to running LLM filter unless globally disabled
    disable_llm_chunk_filter: bool = DISABLE_LLM_CHUNK_FILTER,
) -> SearchResponse:
    """Simple search endpoint, does not create a new message or records in the DB"""
    query = search_request.message
    filters = search_request.retrieval_options.filters

    logger.info(f"Received document search query: {query}")

    user_acl_filters = build_access_filters_for_user(user, db_session)
    final_filters = IndexFilters(
        source_type=filters.source_type if filters else None,
        document_set=filters.document_set if filters else None,
        time_cutoff=filters.time_cutoff if filters else None,
        access_control_list=user_acl_filters,
    )

    search_query = SearchQuery(
        query=query,
        search_type=search_request.search_type,
        filters=final_filters,
        recency_bias_multiplier=search_request.recency_bias_multiplier,
        skip_rerank=search_request.skip_rerank,
        skip_llm_chunk_filter=disable_llm_chunk_filter,
    )

    top_chunks, llm_selection = full_chunk_search(
        query=search_query,
        document_index=get_default_document_index(),
    )

    top_docs = chunks_to_search_docs(top_chunks)
    llm_selection_indices = [
        index for index, value in enumerate(llm_selection) if value
    ]

    # No need to save the docs for this API
    fake_saved_docs = [SavedSearchDoc.from_search_doc(doc) for doc in top_docs]

    return SearchResponse(
        top_documents=fake_saved_docs, llm_indices=llm_selection_indices
    )


@basic_router.post("/stream-answer-with-quote")
def get_answer_with_quote(
    query_request: DirectQARequest,
    user: User = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> StreamingResponse:
    query = query_request.messages[0].message
    logger.info(f"Received query for one shot answer with quotes: {query}")
    packets = stream_search_answer(
        query_req=query_request, user=user, db_session=db_session
    )
    return StreamingResponse(packets, media_type="application/json")
