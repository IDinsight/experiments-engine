from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.requests import Request
from redis.asyncio import Redis
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_current_user, get_verified_user
from ..auth.utils import generate_verification_token
from ..database import get_async_session, get_redis
from ..email import EmailService
from ..users.models import (
    UserAlreadyExistsError,
    UserDB,
    save_user_to_db,
    update_user_api_key,
)
from ..utils import generate_key, setup_logger, update_api_limits
from .schemas import KeyResponse, UserCreate, UserCreateWithPassword, UserRetrieve

# Router setup
TAG_METADATA = {
    "name": "Admin",
    "description": "_Requires user login._ Only administrator user has access to these "
    "endpoints.",
}

router = APIRouter(prefix="/user", tags=["Users"])
logger = setup_logger()
email_service = EmailService()


@router.post("/", response_model=UserCreate)
async def create_user(
    user: UserCreateWithPassword,
    request: Request,
    background_tasks: BackgroundTasks,
    asession: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis),
) -> UserCreate | None:
    """
    Create user endpoint.
    """

    try:
        new_api_key = generate_key()
        user_new = await save_user_to_db(
            user=user,
            api_key=new_api_key,
            asession=asession,
            is_verified=False,
        )
        await update_api_limits(redis, user_new.username, user_new.api_daily_quota)

        token = await generate_verification_token(
            user_new.user_id, user_new.username, redis
        )

        background_tasks.add_task(
            email_service.send_verification_email,
            user_new.username,
            user_new.first_name,
            token,
        )

        return UserCreate(
            username=user_new.username,
            first_name=user_new.first_name,
            last_name=user_new.last_name,
            experiments_quota=user_new.experiments_quota,
            api_daily_quota=user_new.api_daily_quota,
        )
    except UserAlreadyExistsError as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=400, detail="User with that username already exists."
        ) from e


@router.get("/", response_model=UserRetrieve)
async def get_user(
    user_db: Annotated[UserDB, Depends(get_current_user)],
) -> UserRetrieve | None:
    """
    Get user endpoint. Returns the user object for the requester.
    """

    return UserRetrieve.model_validate(user_db)


@router.put("/rotate-key", response_model=KeyResponse)
async def get_new_api_key(
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> KeyResponse | None:
    """
    Generate a new API key for the requester's account. Takes a user object,
    generates a new key, replaces the old one in the database, and returns
    a user object with the new key.
    """

    new_api_key = generate_key()

    try:
        # this is neccesarry to attach the user_db to the session
        asession.add(user_db)
        await update_user_api_key(
            user_db=user_db,
            new_api_key=new_api_key,
            asession=asession,
        )
        return KeyResponse(
            username=user_db.username,
            new_api_key=new_api_key,
        )
    except SQLAlchemyError as e:
        logger.error(f"Error updating user api key: {e}")
        raise HTTPException(
            status_code=500, detail="Error updating user api key"
        ) from e
