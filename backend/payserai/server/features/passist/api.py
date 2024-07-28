from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from payserai.auth.users import current_admin_user
from payserai.auth.users import current_user
from payserai.configs.model_configs import GEN_AI_MODEL_PROVIDER
from payserai.configs.model_configs import GEN_AI_MODEL_VERSION
from payserai.db.chat import get_passist_by_id
from payserai.db.chat import get_passists
from payserai.db.chat import get_prompts_by_ids
from payserai.db.chat import mark_passist_as_deleted
from payserai.db.chat import update_all_passists_display_priority
from payserai.db.chat import update_passist_visibility
from payserai.db.chat import upsert_passist
from payserai.db.document_set import get_document_sets_by_ids
from payserai.db.engine import get_session
from payserai.db.models import User
from payserai.one_shot_answer.qa_block import build_dummy_prompt
from payserai.server.features.passist.models import CreatePassistRequest
from payserai.server.features.passist.models import PassistSnapshot
from payserai.server.features.passist.models import PromptTemplateResponse
from payserai.utils.logger import setup_logger

logger = setup_logger()


admin_router = APIRouter(prefix="/admin/passist")
basic_router = APIRouter(prefix="/passist")


def create_update_passist(
    passist_id: int | None,
    create_passist_request: CreatePassistRequest,
    user: User | None,
    db_session: Session,
) -> PassistSnapshot:
    user_id = user.id if user is not None else None

    # Permission to actually use these is checked later
    document_sets = list(
        get_document_sets_by_ids(
            document_set_ids=create_passist_request.document_set_ids,
            db_session=db_session,
        )
    )
    prompts = list(
        get_prompts_by_ids(
            prompt_ids=create_passist_request.prompt_ids,
            db_session=db_session,
        )
    )

    try:
        passist = upsert_passist(
            passist_id=passist_id,
            user_id=user_id,
            name=create_passist_request.name,
            description=create_passist_request.description,
            num_chunks=create_passist_request.num_chunks,
            llm_relevance_filter=create_passist_request.llm_relevance_filter,
            llm_filter_extraction=create_passist_request.llm_filter_extraction,
            recency_bias=create_passist_request.recency_bias,
            prompts=prompts,
            document_sets=document_sets,
            llm_model_version_override=create_passist_request.llm_model_version_override,
            shared=create_passist_request.shared,
            db_session=db_session,
        )
    except ValueError as e:
        logger.exception("Failed to create passist")
        raise HTTPException(status_code=400, detail=str(e))
    return PassistSnapshot.from_model(passist)


@admin_router.post("")
def create_passist(
    create_passist_request: CreatePassistRequest,
    user: User | None = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> PassistSnapshot:
    return create_update_passist(
        passist_id=None,
        create_passist_request=create_passist_request,
        user=user,
        db_session=db_session,
    )


@admin_router.patch("/{passist_id}")
def update_passist(
    passist_id: int,
    update_passist_request: CreatePassistRequest,
    user: User | None = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> PassistSnapshot:
    return create_update_passist(
        passist_id=passist_id,
        create_passist_request=update_passist_request,
        user=user,
        db_session=db_session,
    )


class IsVisibleRequest(BaseModel):
    is_visible: bool


@admin_router.patch("/{passist_id}/visible")
def patch_passist_visibility(
    passist_id: int,
    is_visible_request: IsVisibleRequest,
    _: User | None = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> None:
    update_passist_visibility(
        passist_id=passist_id,
        is_visible=is_visible_request.is_visible,
        db_session=db_session,
    )


class DisplayPriorityRequest(BaseModel):
    # maps passist id to display priority
    display_priority_map: dict[int, int]


@admin_router.put("/display-priority")
def patch_passist_display_priority(
    display_priority_request: DisplayPriorityRequest,
    _: User | None = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> None:
    update_all_passists_display_priority(
        display_priority_map=display_priority_request.display_priority_map,
        db_session=db_session,
    )


@admin_router.delete("/{passist_id}")
def delete_passist(
    passist_id: int,
    user: User | None = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> None:
    mark_passist_as_deleted(
        passist_id=passist_id,
        user_id=user.id if user is not None else None,
        db_session=db_session,
    )


@basic_router.get("")
def list_passists(
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> list[PassistSnapshot]:
    user_id = user.id if user is not None else None
    return [
        PassistSnapshot.from_model(passist)
        for passist in get_passists(user_id=user_id, db_session=db_session)
    ]


@basic_router.get("/{passist_id}")
def get_passist(
    passist_id: int,
    user: User | None = Depends(current_user),
    db_session: Session = Depends(get_session),
) -> PassistSnapshot:
    return PassistSnapshot.from_model(
        get_passist_by_id(
            passist_id=passist_id,
            user_id=user.id if user is not None else None,
            db_session=db_session,
        )
    )


@basic_router.get("/utils/prompt-explorer")
def build_final_template_prompt(
    system_prompt: str,
    task_prompt: str,
    retrieval_disabled: bool = False,
    _: User | None = Depends(current_user),
) -> PromptTemplateResponse:
    return PromptTemplateResponse(
        final_prompt_template=build_dummy_prompt(
            system_prompt=system_prompt,
            task_prompt=task_prompt,
            retrieval_disabled=retrieval_disabled,
        )
    )


"""Utility endpoints for selecting which model to use for a passist.
Putting here for now, since we have no other flows which use this."""

GPT_4_MODEL_VERSIONS = [
    "gpt-4-1106-preview",
    "gpt-4",
    "gpt-4-32k",
    "gpt-4-0613",
    "gpt-4-32k-0613",
    "gpt-4-0314",
    "gpt-4-32k-0314",
]
GPT_3_5_TURBO_MODEL_VERSIONS = [
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-0613",
    "gpt-3.5-turbo-16k-0613",
    "gpt-3.5-turbo-0301",
]


@admin_router.get("/utils/list-available-models")
def list_available_model_versions(
    _: User | None = Depends(current_admin_user),
) -> list[str]:
    # currently only support selecting different models for OpenAI
    if GEN_AI_MODEL_PROVIDER != "openai":
        return []

    return GPT_4_MODEL_VERSIONS + GPT_3_5_TURBO_MODEL_VERSIONS


@admin_router.get("/utils/default-model")
def get_default_model(
    _: User | None = Depends(current_admin_user),
) -> str:
    # currently only support selecting different models for OpenAI
    if GEN_AI_MODEL_PROVIDER != "openai":
        return ""

    return GEN_AI_MODEL_VERSION
