from datetime import datetime, timedelta, timezone
from typing import Annotated, Dict, Optional, Union

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.requests import Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import CHECK_API_LIMIT, DEFAULT_API_QUOTA, DEFAULT_EXPERIMENTS_QUOTA
from ..database import get_async_session
from ..users.models import (
    UserDB,
    UserNotFoundError,
    get_user_by_api_key,
    get_user_by_username,
    save_user_to_db,
    update_user_verification_status,
)
from ..users.schemas import UserCreate
from ..utils import (
    generate_key,
    setup_logger,
    update_api_limits,
    verify_password_salted_hash,
)
from .config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET,
    REDIS_KEY_EXPIRED,
)
from .schemas import AuthenticatedUser

logger = setup_logger()

bearer = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def authenticate_key(
    asession: AsyncSession = Depends(get_async_session),
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> UserDB:
    """
    Authenticate using basic bearer token. Used for calling
    the question-answering endpoints. In case the JWT token is
    provided instead of the API key, it will fall back to JWT
    """
    token = credentials.credentials
    try:
        user_db = await get_user_by_api_key(token, asession)

        if not user_db.is_active:
            raise HTTPException(
                status_code=403, detail="Account is inactive. Please contact support."
            )

        return user_db
    except UserNotFoundError as e:
        raise HTTPException(status_code=403, detail="Invalid API key") from e


async def authenticate_credentials(
    *, username: str, password: str, asession: AsyncSession
) -> Optional[AuthenticatedUser]:
    """
    Authenticate user using username and password.
    """
    try:
        user_db = await get_user_by_username(username, asession)

        if not user_db.is_active:
            logger.warning(f"Inactive user {username} attempted to login")
            return None

        if verify_password_salted_hash(password, user_db.hashed_password):
            # hardcode "fullaccess" now, but may use it in the future
            return AuthenticatedUser(
                username=username,
                access_level="fullaccess",
                api_key_first_characters=user_db.api_key_first_characters,
                is_verified=user_db.is_verified,
            )
        else:
            return None
    except UserNotFoundError:
        return None


async def authenticate_or_create_google_user(
    *,
    request: Request,
    google_email: str,
    asession: AsyncSession,
) -> Optional[AuthenticatedUser]:
    """
    Check if user exists in Db. If not, create user.
    Google authenticated users are automatically verified.
    """
    try:
        user_db = await get_user_by_username(google_email, asession)

        if not user_db.is_verified:
            asession.add(user_db)
            await update_user_verification_status(user_db, True, asession)

        return AuthenticatedUser(
            username=user_db.username,
            access_level="fullaccess",
            api_key_first_characters=user_db.api_key_first_characters,
            is_verified=user_db.is_verified,
        )
    except UserNotFoundError:
        user = UserCreate(
            username=google_email,
            experiments_quota=DEFAULT_EXPERIMENTS_QUOTA,
            api_daily_quota=DEFAULT_API_QUOTA,
        )
        api_key = generate_key()
        user_db = await save_user_to_db(user, api_key, asession, is_verified=True)
        await update_api_limits(
            request.app.state.redis, user_db.username, user_db.api_daily_quota
        )
        return AuthenticatedUser(
            username=user_db.username,
            access_level="fullaccess",
            api_key_first_characters=user_db.api_key_first_characters,
            is_verified=True,
        )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    asession: AsyncSession = Depends(get_async_session),
) -> UserDB:
    """
    Get the current user from the access token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception

        # fetch user from database
        try:
            user_db = await get_user_by_username(username, asession)

            if not user_db.is_active:
                raise HTTPException(
                    status_code=403,
                    detail="Account is inactive. Please contact support.",
                )

            return user_db
        except UserNotFoundError as err:
            raise credentials_exception from err
    except InvalidTokenError as err:
        raise credentials_exception from err


async def get_verified_user(
    user_db: Annotated[UserDB, Depends(get_current_user)],
) -> UserDB:
    """
    Check if the user is verified
    """
    if not user_db.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Account not verified. Please check your email to verify "
            "your account.",
        )
    return user_db


def create_access_token(username: str) -> str:
    """
    Create an access token for the user
    """
    payload: Dict[str, Union[str, datetime]] = {}
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload["exp"] = expire
    payload["iat"] = datetime.now(timezone.utc)
    payload["sub"] = username
    payload["type"] = "access_token"

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def rate_limiter(
    request: Request,
    user_db: UserDB = Depends(authenticate_key),
) -> None:
    """
    Rate limiter for the API calls. Gets daily quota and decrement it
    """
    if CHECK_API_LIMIT is False:
        return
    username = user_db.username
    key = f"remaining-calls:{username}"
    redis = request.app.state.redis
    ttl = await redis.ttl(key)
    # if key does not exist, set the key and value
    if ttl == REDIS_KEY_EXPIRED:
        await update_api_limits(redis, username, user_db.api_daily_quota)

    nb_remaining = await redis.get(key)

    if nb_remaining != b"None":
        nb_remaining = int(nb_remaining)
        if nb_remaining <= 0:
            raise HTTPException(status_code=429, detail="API call limit reached.")
        await update_api_limits(redis, username, nb_remaining - 1)
