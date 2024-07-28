from typing import Any
from typing import cast

import nltk  # type:ignore
import torch
import uvicorn
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from httpx_oauth.clients.google import GoogleOAuth2
from sqlalchemy.orm import Session

from payserai import __version__
from payserai.auth.schemas import UserCreate
from payserai.auth.schemas import UserRead
from payserai.auth.schemas import UserUpdate
from payserai.auth.users import auth_backend
from payserai.auth.users import fastapi_users
from payserai.chat.load_yamls import load_chat_yamls
from payserai.configs.app_configs import APP_API_PREFIX
from payserai.configs.app_configs import APP_HOST
from payserai.configs.app_configs import APP_PORT
from payserai.configs.app_configs import AUTH_TYPE
from payserai.configs.app_configs import DISABLE_GENERATIVE_AI
from payserai.configs.app_configs import MODEL_SERVER_HOST
from payserai.configs.app_configs import MODEL_SERVER_PORT
from payserai.configs.app_configs import OAUTH_CLIENT_ID
from payserai.configs.app_configs import OAUTH_CLIENT_SECRET
from payserai.configs.app_configs import SECRET
from payserai.configs.app_configs import WEB_DOMAIN
from payserai.configs.chat_configs import MULTILINGUAL_QUERY_EXPANSION
from payserai.configs.constants import AuthType
from payserai.configs.model_configs import ASYM_PASSAGE_PREFIX
from payserai.configs.model_configs import ASYM_QUERY_PREFIX
from payserai.configs.model_configs import DOCUMENT_ENCODER_MODEL
from payserai.configs.model_configs import ENABLE_RERANKING_REAL_TIME_FLOW
from payserai.configs.model_configs import FAST_GEN_AI_MODEL_VERSION
from payserai.configs.model_configs import GEN_AI_API_ENDPOINT
from payserai.configs.model_configs import GEN_AI_MODEL_PROVIDER
from payserai.configs.model_configs import GEN_AI_MODEL_VERSION
from payserai.db.connector import create_initial_default_connector
from payserai.db.connector_credential_pair import associate_default_cc_pair
from payserai.db.credentials import create_initial_public_credential
from payserai.db.engine import get_sqlalchemy_engine
from payserai.document_index.factory import get_default_document_index
from payserai.llm.factory import get_default_llm
from payserai.search.search_nlp_models import warm_up_models
from payserai.server.payserai_api.ingestion import get_payserai_api_key
from payserai.server.payserai_api.ingestion import router as payserai_api_router
from payserai.server.documents.cc_pair import router as cc_pair_router
from payserai.server.documents.connector import router as connector_router
from payserai.server.documents.credential import router as credential_router
from payserai.server.documents.document import router as document_router
from payserai.server.features.document_set.api import router as document_set_router
from payserai.server.features.passist.api import admin_router as admin_passist_router
from payserai.server.features.passist.api import basic_router as passist_router
from payserai.server.features.prompt.api import basic_router as prompt_router
from payserai.server.manage.administrative import router as admin_router
from payserai.server.manage.get_state import router as state_router
from payserai.server.manage.users import router as user_router
from payserai.server.query_and_chat.chat_backend import router as chat_router
from payserai.server.query_and_chat.query_backend import (
    admin_router as admin_query_router,
)
from payserai.server.query_and_chat.query_backend import basic_router as query_router
from payserai.utils.logger import setup_logger
from payserai.utils.telemetry import optional_telemetry
from payserai.utils.telemetry import RecordType
from payserai.utils.variable_functionality import fetch_versioned_implementation


logger = setup_logger()


def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logger.exception(f"{request}: {exc_str}")
    content = {"status_code": 422, "message": exc_str, "data": None}
    return JSONResponse(content=content, status_code=422)


def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    try:
        raise (exc)
    except Exception:
        # log stacktrace
        logger.exception("ValueError")
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )


def include_router_with_global_prefix_prepended(
    application: FastAPI, router: APIRouter, **kwargs: Any
) -> None:
    """Adds the global prefix to all routes in the router."""
    processed_global_prefix = f"/{APP_API_PREFIX.strip('/')}" if APP_API_PREFIX else ""

    passed_in_prefix = cast(str | None, kwargs.get("prefix"))
    if passed_in_prefix:
        final_prefix = f"{processed_global_prefix}/{passed_in_prefix.strip('/')}"
    else:
        final_prefix = f"{processed_global_prefix}"
    final_kwargs: dict[str, Any] = {
        **kwargs,
        "prefix": final_prefix,
    }

    application.include_router(router, **final_kwargs)


def get_application() -> FastAPI:
    application = FastAPI(title="Payserai Backend", version=__version__)

    include_router_with_global_prefix_prepended(application, chat_router)
    include_router_with_global_prefix_prepended(application, query_router)
    include_router_with_global_prefix_prepended(application, document_router)
    include_router_with_global_prefix_prepended(application, admin_query_router)
    include_router_with_global_prefix_prepended(application, admin_router)
    include_router_with_global_prefix_prepended(application, user_router)
    include_router_with_global_prefix_prepended(application, connector_router)
    include_router_with_global_prefix_prepended(application, credential_router)
    include_router_with_global_prefix_prepended(application, cc_pair_router)
    include_router_with_global_prefix_prepended(application, document_set_router)
    include_router_with_global_prefix_prepended(application, passist_router)
    include_router_with_global_prefix_prepended(application, admin_passist_router)
    include_router_with_global_prefix_prepended(application, prompt_router)
    include_router_with_global_prefix_prepended(application, state_router)
    include_router_with_global_prefix_prepended(application, payserai_api_router)

    if AUTH_TYPE == AuthType.DISABLED:
        # Server logs this during auth setup verification step
        pass

    elif AUTH_TYPE == AuthType.BASIC:
        include_router_with_global_prefix_prepended(
            application,
            fastapi_users.get_auth_router(auth_backend),
            prefix="/auth",
            tags=["auth"],
        )
        include_router_with_global_prefix_prepended(
            application,
            fastapi_users.get_register_router(UserRead, UserCreate),
            prefix="/auth",
            tags=["auth"],
        )
        include_router_with_global_prefix_prepended(
            application,
            fastapi_users.get_reset_password_router(),
            prefix="/auth",
            tags=["auth"],
        )
        include_router_with_global_prefix_prepended(
            application,
            fastapi_users.get_verify_router(UserRead),
            prefix="/auth",
            tags=["auth"],
        )
        include_router_with_global_prefix_prepended(
            application,
            fastapi_users.get_users_router(UserRead, UserUpdate),
            prefix="/users",
            tags=["users"],
        )

    elif AUTH_TYPE == AuthType.GOOGLE_OAUTH:
        oauth_client = GoogleOAuth2(OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET)
        include_router_with_global_prefix_prepended(
            application,
            fastapi_users.get_oauth_router(
                oauth_client,
                auth_backend,
                SECRET,
                associate_by_email=True,
                is_verified_by_default=True,
                # Points the user back to the login page
                redirect_url=f"{WEB_DOMAIN}/auth/oauth/callback",
            ),
            prefix="/auth/oauth",
            tags=["auth"],
        )
        # Need basic auth router for `logout` endpoint
        include_router_with_global_prefix_prepended(
            application,
            fastapi_users.get_logout_router(auth_backend),
            prefix="/auth",
            tags=["auth"],
        )

    application.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )

    application.add_exception_handler(ValueError, value_error_handler)

    @application.on_event("startup")
    def startup_event() -> None:
        verify_auth = fetch_versioned_implementation(
            "payserai.auth.users", "verify_auth_setting"
        )
        # Will throw exception if an issue is found
        verify_auth()

        # Payserai APIs key
        api_key = get_payserai_api_key()
        logger.info(f"Payserai API Key: {api_key}")

        if OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET:
            logger.info("Both OAuth Client ID and Secret are configured.")

        if DISABLE_GENERATIVE_AI:
            logger.info("Generative AI Q&A disabled")
        else:
            logger.info(f"Using LLM Provider: {GEN_AI_MODEL_PROVIDER}")
            logger.info(f"Using LLM Model Version: {GEN_AI_MODEL_VERSION}")
            if GEN_AI_MODEL_VERSION != FAST_GEN_AI_MODEL_VERSION:
                logger.info(
                    f"Using Fast LLM Model Version: {FAST_GEN_AI_MODEL_VERSION}"
                )
            if GEN_AI_API_ENDPOINT:
                logger.info(f"Using LLM Endpoint: {GEN_AI_API_ENDPOINT}")

            # Any additional model configs logged here
            get_default_llm().log_model_configs()

        if MULTILINGUAL_QUERY_EXPANSION:
            logger.info(
                f"Using multilingual flow with languages: {MULTILINGUAL_QUERY_EXPANSION}"
            )

        if ENABLE_RERANKING_REAL_TIME_FLOW:
            logger.info("Reranking step of search flow is enabled.")

        logger.info(f'Using Embedding model: "{DOCUMENT_ENCODER_MODEL}"')
        if ASYM_QUERY_PREFIX or ASYM_PASSAGE_PREFIX:
            logger.info(f'Query embedding prefix: "{ASYM_QUERY_PREFIX}"')
            logger.info(f'Passage embedding prefix: "{ASYM_PASSAGE_PREFIX}"')

        if MODEL_SERVER_HOST:
            logger.info(
                f"Using Model Server: http://{MODEL_SERVER_HOST}:{MODEL_SERVER_PORT}"
            )
        else:
            logger.info("Warming up local NLP models.")
            warm_up_models(skip_cross_encoders=not ENABLE_RERANKING_REAL_TIME_FLOW)

            if torch.cuda.is_available():
                logger.info("GPU is available")
            else:
                logger.info("GPU is not available")
            logger.info(f"Torch Threads: {torch.get_num_threads()}")

        logger.info("Verifying query preprocessing (NLTK) data is downloaded")
        nltk.download("stopwords", quiet=True)
        nltk.download("wordnet", quiet=True)
        nltk.download("punkt", quiet=True)

        logger.info("Verifying default connector/credential exist.")
        with Session(get_sqlalchemy_engine(), expire_on_commit=False) as db_session:
            create_initial_public_credential(db_session)
            create_initial_default_connector(db_session)
            associate_default_cc_pair(db_session)

        logger.info("Loading default Prompts and Passists")
        load_chat_yamls()

        logger.info("Verifying Document Index(s) is/are available.")
        get_default_document_index().ensure_indices_exist()

        optional_telemetry(
            record_type=RecordType.VERSION, data={"version": __version__}
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Change this to the list of allowed origins if needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return application


app = get_application()


if __name__ == "__main__":
    logger.info(
        f"Starting Payserai Backend version {__version__} on http://{APP_HOST}:{str(APP_PORT)}/"
    )
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
