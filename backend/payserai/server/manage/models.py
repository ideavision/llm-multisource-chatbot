from typing import Any

from pydantic import BaseModel
from pydantic import root_validator
from pydantic import validator

from payserai.auth.schemas import UserRole
from payserai.configs.constants import AuthType
from payserai.db.models import AllowedAnswerFilters
from payserai.db.models import ChannelConfig
from payserai.server.features.passist.models import PassistSnapshot


class VersionResponse(BaseModel):
    backend_version: str


class AuthTypeResponse(BaseModel):
    auth_type: AuthType
    # specifies whether the current auth setup requires
    # users to have verified emails
    requires_verification: bool


class UserInfo(BaseModel):
    id: str
    email: str
    is_active: bool
    is_superuser: bool
    is_verified: bool
    role: UserRole


class UserByEmail(BaseModel):
    user_email: str


class UserRoleResponse(BaseModel):
    role: str


class BoostDoc(BaseModel):
    document_id: str
    semantic_id: str
    link: str
    boost: int
    hidden: bool


class BoostUpdateRequest(BaseModel):
    document_id: str
    boost: int


class HiddenUpdateRequest(BaseModel):
    document_id: str
    hidden: bool




