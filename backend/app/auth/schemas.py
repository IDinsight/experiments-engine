from typing import Literal

from pydantic import BaseModel, ConfigDict

AccessLevel = Literal["fullaccess"]
TokenType = Literal["bearer"]


class AuthenticatedUser(BaseModel):
    """
    Pydantic model for authenticated user
    """

    username: str
    access_level: AccessLevel
    api_key_first_characters: str
    is_verified: bool
    model_config = ConfigDict(from_attributes=True)


class GoogleLoginData(BaseModel):
    """
    Pydantic model for Google login data
    """

    client_id: str
    credential: str

    model_config = ConfigDict(from_attributes=True)


class AuthenticationDetails(BaseModel):
    """
    Pydantic model for authentication details
    """

    access_token: str
    token_type: TokenType
    access_level: AccessLevel
    api_key_first_characters: str
    username: str
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
