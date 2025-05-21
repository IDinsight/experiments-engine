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
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import CHECK_API_LIMIT
from ..database import get_async_session
from ..users.exceptions import UserNotFoundError
from ..users.models import (
    UserDB,
    get_user_by_username,
    save_user_to_db,
    update_user_verification_status,
)
from ..users.schemas import UserCreate
from ..utils import (
    encode_api_limit,
    generate_key,
    get_key_hash,
    setup_logger,
    verify_password_salted_hash,
)
from ..workspaces.models import (
    WorkspaceDB,
    get_user_default_workspace,
    get_user_role_in_workspace,
)
from ..workspaces.schemas import UserRoles
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


async def authenticate_workspace_key(
    asession: AsyncSession = Depends(get_async_session),
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> WorkspaceDB:
    """
    Authenticate using workspace API key.
    Returns the workspace associated with the API key.
    """
    token = credentials.credentials
    try:
        # Check if the token matches any workspace API key
        hashed_token = get_key_hash(token)
        workspace_stmt = select(WorkspaceDB).where(
            WorkspaceDB.hashed_api_key == hashed_token
        )
        workspace_result = await asession.execute(workspace_stmt)
        workspace = workspace_result.scalar_one_or_none()

        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid workspace API key",
            )

        return workspace
    except NoResultFound as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid workspace API key"
        ) from err
    except Exception as e:
        logger.error(f"Error authenticating workspace API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Authorization error"
        ) from e


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
    first_name: str,
    last_name: str,
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
            is_verified=user_db.is_verified,
        )
    except UserNotFoundError:
        user = UserCreate(
            username=google_email, first_name=first_name, last_name=last_name
        )
        api_key = generate_key()
        user_db = await save_user_to_db(user, api_key, asession, is_verified=True)
        return AuthenticatedUser(
            username=user_db.username,
            access_level="fullaccess",
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


async def require_admin_role(
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> UserDB:
    """Ensures the user has admin role in their current workspace."""
    workspace_db = await get_user_default_workspace(asession=asession, user_db=user_db)

    if workspace_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have a default workspace.",
        )

    user_role = await get_user_role_in_workspace(
        asession=asession, user_db=user_db, workspace_db=workspace_db
    )

    if user_role != UserRoles.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace administrators can perform this action.",
        )

    return user_db


def create_access_token(username: str, workspace_name: str | None = None) -> str:
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

    if workspace_name:
        payload["workspace_name"] = workspace_name

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def update_workspace_api_limits(
    redis: Redis, workspace_id: int, api_daily_quota: int | None
) -> None:
    """
    Update the API limits for workspace in Redis
    """
    now = datetime.now(timezone.utc)
    next_midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    key = f"workspace-remaining-calls:{workspace_id}"
    expire_at = int(next_midnight.timestamp())
    await redis.set(key, encode_api_limit(api_daily_quota))
    if api_daily_quota is not None:
        await redis.expireat(key, expire_at)


async def workspace_rate_limiter(
    request: Request,
    workspace_db: WorkspaceDB = Depends(authenticate_workspace_key),
) -> None:
    """
    Rate limiter for the API calls using workspace quota instead of user quota.
    """
    if CHECK_API_LIMIT is False:
        return

    key = f"workspace-remaining-calls:{workspace_db.workspace_id}"
    redis = request.app.state.redis
    ttl = await redis.ttl(key)

    # if key does not exist, set the key and value
    if ttl == REDIS_KEY_EXPIRED:
        await update_workspace_api_limits(
            redis, workspace_db.workspace_id, workspace_db.api_daily_quota
        )

    nb_remaining = await redis.get(key)

    if nb_remaining != b"None":
        nb_remaining = int(nb_remaining)
        if nb_remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Workspace API call limit reached. Please try again tomorrow "
                    "or upgrade your plan."
                ),
            )
        await update_workspace_api_limits(
            redis, workspace_db.workspace_id, nb_remaining - 1
        )
