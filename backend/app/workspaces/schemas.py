from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRoles(str, Enum):
    """Enumeration for user roles.

    There are 2 different types of users:

    1. (Read-Only) Users: These users are assigned to workspaces and can only read the
         contents within their assigned workspaces. They cannot modify existing
         contents or add new contents to their workspaces, add or delete users from
         their workspaces, or add or delete workspaces.
    2. Admin Users: These users are assigned to workspaces and can read and modify the
         contents within their assigned workspaces. They can also add or delete users
         from their own workspaces and can also add new workspaces or delete their own
         workspaces. Admin users have no control over workspaces that they are not
        assigned to.
    """

    ADMIN = "admin"
    READ_ONLY = "read_only"


class WorkspaceCreate(BaseModel):
    """Pydantic model for workspace creation."""

    api_daily_quota: int | None = None
    content_quota: int | None = None
    workspace_name: str

    model_config = ConfigDict(from_attributes=True)


class WorkspaceKeyResponse(BaseModel):
    """Pydantic model for updating workspace API key."""

    new_api_key: str
    workspace_name: str

    model_config = ConfigDict(from_attributes=True)


class WorkspaceRetrieve(BaseModel):
    """Pydantic model for workspace retrieval."""

    api_daily_quota: Optional[int] = None
    api_key_first_characters: Optional[str] = None
    api_key_updated_datetime_utc: Optional[datetime] = None
    api_key_rotated_by_user_id: Optional[int] = None
    api_key_rotated_by_username: Optional[str] = None
    content_quota: Optional[int] = None
    created_datetime_utc: datetime
    updated_datetime_utc: Optional[datetime] = None
    workspace_id: int
    workspace_name: str
    is_default: bool = False

    model_config = ConfigDict(from_attributes=True)


class WorkspaceSwitch(BaseModel):
    """Pydantic model for switching workspaces."""

    workspace_name: str

    model_config = ConfigDict(from_attributes=True)


class WorkspaceUpdate(BaseModel):
    """Pydantic model for workspace updates."""

    workspace_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserWorkspace(BaseModel):
    """Pydantic model for user workspace information."""

    user_role: UserRoles
    workspace_id: int
    workspace_name: str
    is_default: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserCreateWithCode(BaseModel):
    """Pydantic model for user creation with recovery codes."""

    is_default_workspace: bool = False
    recovery_codes: List[str] = []
    role: UserRoles
    username: str
    workspace_name: str

    model_config = ConfigDict(from_attributes=True)


class WorkspaceInvite(BaseModel):
    """Pydantic model for inviting users to a workspace."""

    email: EmailStr
    role: UserRoles = UserRoles.READ_ONLY
    workspace_name: str

    model_config = ConfigDict(from_attributes=True)


class WorkspaceInviteResponse(BaseModel):
    """Pydantic model for workspace invite response."""

    message: str
    email: EmailStr
    workspace_name: str
    user_exists: bool

    model_config = ConfigDict(from_attributes=True)


class WorkspaceUserResponse(BaseModel):
    """Pydantic model for workspace user information."""

    user_id: int
    username: str
    first_name: str
    last_name: str
    role: UserRoles
    is_default_workspace: bool
    created_datetime_utc: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyRotationHistory(BaseModel):
    """Pydantic model for API key rotation history."""

    rotation_id: int
    workspace_id: int
    rotated_by_user_id: int
    rotated_by_username: str
    key_first_characters: str
    rotation_datetime_utc: datetime

    model_config = ConfigDict(from_attributes=True)
