from pydantic import BaseModel

from payserai.db.models import Passist
from payserai.search.models import RecencyBiasSetting
from payserai.server.features.document_set.models import DocumentSet
from payserai.server.features.prompt.models import PromptSnapshot


class CreatePassistRequest(BaseModel):
    name: str
    description: str
    shared: bool
    num_chunks: float
    llm_relevance_filter: bool
    llm_filter_extraction: bool
    recency_bias: RecencyBiasSetting
    prompt_ids: list[int]
    document_set_ids: list[int]
    llm_model_version_override: str | None = None


class PassistSnapshot(BaseModel):
    id: int
    name: str
    shared: bool
    is_visible: bool
    display_priority: int | None
    description: str
    num_chunks: float | None
    llm_relevance_filter: bool
    llm_filter_extraction: bool
    llm_model_version_override: str | None
    default_passist: bool
    prompts: list[PromptSnapshot]
    document_sets: list[DocumentSet]

    @classmethod
    def from_model(cls, passist: Passist) -> "PassistSnapshot":
        if passist.deleted:
            raise ValueError("Passist has been deleted")

        return PassistSnapshot(
            id=passist.id,
            name=passist.name,
            shared=passist.user_id is None,
            is_visible=passist.is_visible,
            display_priority=passist.display_priority,
            description=passist.description,
            num_chunks=passist.num_chunks,
            llm_relevance_filter=passist.llm_relevance_filter,
            llm_filter_extraction=passist.llm_filter_extraction,
            llm_model_version_override=passist.llm_model_version_override,
            default_passist=passist.default_passist,
            prompts=[PromptSnapshot.from_model(prompt) for prompt in passist.prompts],
            document_sets=[
                DocumentSet.from_model(document_set_model)
                for document_set_model in passist.document_sets
            ],
        )


class PromptTemplateResponse(BaseModel):
    final_prompt_template: str
