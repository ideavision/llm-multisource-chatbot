from typing import cast

import yaml
from sqlalchemy.orm import Session

from payserai.configs.chat_configs import DEFAULT_NUM_CHUNKS_FED_TO_CHAT
from payserai.configs.chat_configs import PERSONAS_YAML
from payserai.configs.chat_configs import PROMPTS_YAML
from payserai.db.chat import get_prompt_by_name
from payserai.db.chat import upsert_passist
from payserai.db.chat import upsert_prompt
from payserai.db.document_set import get_or_create_document_set_by_name
from payserai.db.engine import get_sqlalchemy_engine
from payserai.db.models import DocumentSet as DocumentSetDBModel
from payserai.db.models import Prompt as PromptDBModel
from payserai.search.models import RecencyBiasSetting


def load_prompts_from_yaml(prompts_yaml: str = PROMPTS_YAML) -> None:
    with open(prompts_yaml, "r") as file:
        data = yaml.safe_load(file)

    all_prompts = data.get("prompts", [])
    with Session(get_sqlalchemy_engine()) as db_session:
        for prompt in all_prompts:
            upsert_prompt(
                user_id=None,
                prompt_id=prompt.get("id"),
                name=prompt["name"],
                description=prompt["description"].strip(),
                system_prompt=prompt["system"].strip(),
                task_prompt=prompt["task"].strip(),
                include_citations=prompt["include_citations"],
                datetime_aware=prompt.get("datetime_aware", True),
                default_prompt=True,
                passists=None,
                shared=True,
                db_session=db_session,
                commit=True,
            )


def load_passists_from_yaml(
    passists_yaml: str = PERSONAS_YAML,
    default_chunks: float = DEFAULT_NUM_CHUNKS_FED_TO_CHAT,
) -> None:
    with open(passists_yaml, "r") as file:
        data = yaml.safe_load(file)

    all_passists = data.get("passists", [])
    with Session(get_sqlalchemy_engine()) as db_session:
        for passist in all_passists:
            doc_set_names = passist["document_sets"]
            doc_sets: list[DocumentSetDBModel] | None = [
                get_or_create_document_set_by_name(db_session, name)
                for name in doc_set_names
            ]

            # Assume if user hasn't set any document sets for the passist, the user may want
            # to later attach document sets to the passist manually, therefore, don't overwrite/reset
            # the document sets for the passist
            if not doc_sets:
                doc_sets = None

            prompt_set_names = passist["prompts"]
            if not prompt_set_names:
                prompts: list[PromptDBModel | None] | None = None
            else:
                prompts = [
                    get_prompt_by_name(
                        prompt_name, user_id=None, shared=True, db_session=db_session
                    )
                    for prompt_name in prompt_set_names
                ]
                if any([prompt is None for prompt in prompts]):
                    raise ValueError("Invalid Passist configs, not all prompts exist")

                if not prompts:
                    prompts = None

            upsert_passist(
                user_id=None,
                passist_id=passist.get("id"),
                name=passist["name"],
                description=passist["description"],
                num_chunks=passist.get("num_chunks")
                if passist.get("num_chunks") is not None
                else default_chunks,
                llm_relevance_filter=passist.get("llm_relevance_filter"),
                llm_filter_extraction=passist.get("llm_filter_extraction"),
                llm_model_version_override=None,
                recency_bias=RecencyBiasSetting(passist["recency_bias"]),
                prompts=cast(list[PromptDBModel] | None, prompts),
                document_sets=doc_sets,
                default_passist=True,
                shared=True,
                db_session=db_session,
            )


def load_chat_yamls(
    prompt_yaml: str = PROMPTS_YAML,
    passists_yaml: str = PERSONAS_YAML,
) -> None:
    load_prompts_from_yaml(prompt_yaml)
    load_passists_from_yaml(passists_yaml)
