from fastapi import APIRouter

from payserai import __version__
from payserai.auth.users import user_needs_to_be_verified
from payserai.configs.app_configs import AUTH_TYPE
from payserai.server.manage.models import AuthTypeResponse
from payserai.server.manage.models import VersionResponse
from payserai.server.models import StatusResponse

router = APIRouter()


@router.get("/health")
def healthcheck() -> StatusResponse:
    return StatusResponse(success=True, message="ok")


@router.get("/auth/type")
def get_auth_type() -> AuthTypeResponse:
    return AuthTypeResponse(
        auth_type=AUTH_TYPE, requires_verification=user_needs_to_be_verified()
    )


@router.get("/version")
def get_version() -> VersionResponse:
    return VersionResponse(backend_version=__version__)
