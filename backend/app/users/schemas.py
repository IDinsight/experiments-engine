from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    """
    Pydantic model for user creation
    """

    username: str
    first_name: str
    last_name: str
    experiments_quota: Optional[int] = None
    api_daily_quota: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UserCreateWithPassword(UserCreate):
    """
    Pydantic model for user creation with password.
    """

    password: str

    model_config = ConfigDict(from_attributes=True)


class UserRetrieve(UserCreate):
    """
    Pydantic model for user retrieval
    """

    user_id: int
    api_key_first_characters: str
    api_key_updated_datetime_utc: datetime
    created_datetime_utc: datetime
    updated_datetime_utc: datetime
    is_active: bool
    is_verified: bool
    access_level: str

    model_config = ConfigDict(from_attributes=True)


class KeyResponse(BaseModel):
    """
    Pydantic model for key response
    """

    username: str
    new_api_key: str
    model_config = ConfigDict(from_attributes=True)


class PasswordResetRequest(BaseModel):
    """
    Pydantic model for password reset request
    """

    username: EmailStr
    model_config = ConfigDict(from_attributes=True)


class PasswordResetConfirm(BaseModel):
    """
    Pydantic model for password reset confirmation
    """

    token: str
    new_password: str
    model_config = ConfigDict(from_attributes=True)


class EmailVerificationRequest(BaseModel):
    """
    Pydantic model for email verification
    """

    token: str
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """
    Pydantic model for generic message responses
    """

    message: str
    model_config = ConfigDict(from_attributes=True)
