from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.requests import Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_current_user
from ..auth.utils import generate_verification_token
from ..config import DEFAULT_API_QUOTA, DEFAULT_EXPERIMENTS_QUOTA
from ..database import get_async_session, get_redis
from ..email import EmailService
from ..users.exceptions import UserAlreadyExistsError
from ..users.models import (
    UserDB,
    save_user_to_db,
)
from ..utils import generate_key, setup_logger
from .schemas import UserCreate, UserCreateWithPassword, UserRetrieve

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
    # Import workspace functionality to avoid circular imports
    from ..workspaces.models import (
        UserRoles,
        create_user_workspace_role,
        delete_pending_invitation,
        get_pending_invitations_by_email,
    )
    from ..workspaces.utils import create_workspace, get_workspace_by_workspace_id

    # Create the user
    try:
        new_api_key = generate_key()
        user_new = await save_user_to_db(
            user=user,
            api_key=new_api_key,
            asession=asession,
            is_verified=False,
        )
    except UserAlreadyExistsError as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=400, detail="User with that username already exists."
        ) from e

    # Create default workspace for the user
    default_workspace_name = f"{user_new.username}'s Workspace"
    workspace_api_key = generate_key()

    workspace_db, _ = await create_workspace(
        api_daily_quota=DEFAULT_API_QUOTA,
        asession=asession,
        content_quota=DEFAULT_EXPERIMENTS_QUOTA,
        workspace_name=default_workspace_name,
        is_default=True,
        api_key=workspace_api_key,
    )

    # Add user to workspace as admin
    await create_user_workspace_role(
        asession=asession,
        is_default_workspace=True,
        user_db=user_new,
        user_role=UserRoles.ADMIN,
        workspace_db=workspace_db,
    )

    # Process pending invitations
    pending_invitations = await get_pending_invitations_by_email(
        asession=asession, email=user_new.username
    )

    for invitation in pending_invitations:
        invite_workspace = await get_workspace_by_workspace_id(
            asession=asession, workspace_id=invitation.workspace_id
        )

        # Add user to the invited workspace
        await create_user_workspace_role(
            asession=asession,
            is_default_workspace=False,
            user_db=user_new,
            user_role=invitation.role,
            workspace_db=invite_workspace,
        )

        # Delete the invitation
        await delete_pending_invitation(asession=asession, invitation=invitation)

    # Send verification email
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
    )


@router.get("/", response_model=UserRetrieve)
async def get_user(
    user_db: Annotated[UserDB, Depends(get_current_user)],
) -> UserRetrieve | None:
    """
    Get user endpoint. Returns the user object for the requester.
    """

    return UserRetrieve.model_validate(user_db)
