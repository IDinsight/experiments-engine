from typing import Annotated, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import (
    create_access_token,
    get_current_user,
    get_verified_user,
    require_admin_role,
)
from ..auth.schemas import AuthenticationDetails
from ..config import DEFAULT_API_QUOTA, DEFAULT_EXPERIMENTS_QUOTA
from ..database import get_async_session, get_redis
from ..email import EmailService
from ..users.exceptions import UserNotFoundError
from ..users.models import (
    UserDB,
    get_user_by_username,
)
from ..users.schemas import MessageResponse, UserCreate
from ..utils import generate_key, setup_logger
from .models import (
    ApiKeyRotationHistoryDB,
    UserNotFoundInWorkspaceError,
    add_existing_user_to_workspace,
    check_if_user_has_default_workspace,
    create_pending_invitation,
    get_user_by_user_id,
    get_user_default_workspace,
    get_user_role_in_workspace,
    get_user_workspaces,
    get_users_in_workspace,
    remove_user_from_workspace,
    update_user_default_workspace,
)
from .schemas import (
    ApiKeyRotationHistory,
    UserRoles,
    WorkspaceCreate,
    WorkspaceInvite,
    WorkspaceInviteResponse,
    WorkspaceKeyResponse,
    WorkspaceRetrieve,
    WorkspaceSwitch,
    WorkspaceUpdate,
    WorkspaceUserResponse,
)
from .utils import (
    WorkspaceNotFoundError,
    create_workspace,
    get_workspace_by_workspace_id,
    get_workspace_by_workspace_name,
    is_workspace_name_valid,
    update_workspace_api_key,
    update_workspace_name_and_quotas,
)

TAG_METADATA = {
    "name": "Workspace",
    "description": "_Requires user login._ Only administrator user has access to these "
    "endpoints and only for the workspaces that they are assigned to.",
}

router = APIRouter(prefix="/workspace", tags=["Workspace"])
logger = setup_logger()
email_service = EmailService()


@router.post("/", response_model=WorkspaceRetrieve)
async def create_workspace_endpoint(
    calling_user_db: Annotated[UserDB, Depends(get_current_user)],
    workspace: WorkspaceCreate,
    asession: AsyncSession = Depends(get_async_session),
) -> WorkspaceRetrieve:
    """Create a new workspace. Workspaces can only be created by authenticated users."""
    if not await check_if_user_has_default_workspace(
        asession=asession, user_db=calling_user_db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "User must be assigned to a workspace first before creating "
                "new workspaces."
            ),
        )

    # Check if workspace name is valid
    if not await is_workspace_name_valid(
        asession=asession, workspace_name=workspace.workspace_name
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workspace with name '{workspace.workspace_name}' already exists.",
        )

    # Create new workspace
    api_key = generate_key()
    workspace_db, is_new_workspace = await create_workspace(
        api_daily_quota=workspace.api_daily_quota or DEFAULT_API_QUOTA,
        asession=asession,
        content_quota=workspace.content_quota or DEFAULT_EXPERIMENTS_QUOTA,
        workspace_name=workspace.workspace_name,
        api_key=api_key,
    )

    if is_new_workspace:
        # Add the calling user as an admin to the new workspace
        await add_existing_user_to_workspace(
            asession=asession,
            user=UserCreate(
                is_default_workspace=False,  # Don't make it default automatically
                role=UserRoles.ADMIN,
                username=calling_user_db.username,
                first_name=calling_user_db.first_name,
                last_name=calling_user_db.last_name,
                workspace_name=workspace_db.workspace_name,
            ),
            workspace_db=workspace_db,
        )

        # Update with API key rotation user info
        workspace_db.api_key_rotated_by_user_id = calling_user_db.user_id
        await asession.commit()
        await asession.refresh(workspace_db)

        return WorkspaceRetrieve(
            api_daily_quota=workspace_db.api_daily_quota,
            api_key_first_characters=workspace_db.api_key_first_characters,
            api_key_updated_datetime_utc=workspace_db.api_key_updated_datetime_utc,
            api_key_rotated_by_user_id=workspace_db.api_key_rotated_by_user_id,
            api_key_rotated_by_username=calling_user_db.username,
            content_quota=workspace_db.content_quota,
            created_datetime_utc=workspace_db.created_datetime_utc,
            updated_datetime_utc=workspace_db.updated_datetime_utc,
            workspace_id=workspace_db.workspace_id,
            workspace_name=workspace_db.workspace_name,
            is_default=workspace_db.is_default,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace already exists.",
        )


@router.get("/", response_model=List[WorkspaceRetrieve])
async def retrieve_all_workspaces(
    calling_user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> List[WorkspaceRetrieve]:
    """Return a list of all workspaces the user has access to."""
    user_workspaces = await get_user_workspaces(
        asession=asession, user_db=calling_user_db
    )

    result = []
    for workspace_db in user_workspaces:
        # Get username of the person who rotated the key if available
        rotator_username = None
        if workspace_db.api_key_rotated_by_user_id:
            try:
                rotator_user = await get_user_by_user_id(
                    workspace_db.api_key_rotated_by_user_id, asession
                )
                rotator_username = rotator_user.username
            except UserNotFoundError:
                rotator_username = "Unknown User"

        result.append(
            WorkspaceRetrieve(
                api_daily_quota=workspace_db.api_daily_quota,
                api_key_first_characters=workspace_db.api_key_first_characters,
                api_key_updated_datetime_utc=workspace_db.api_key_updated_datetime_utc,
                api_key_rotated_by_user_id=workspace_db.api_key_rotated_by_user_id,
                api_key_rotated_by_username=rotator_username,
                content_quota=workspace_db.content_quota,
                created_datetime_utc=workspace_db.created_datetime_utc,
                updated_datetime_utc=workspace_db.updated_datetime_utc,
                workspace_id=workspace_db.workspace_id,
                workspace_name=workspace_db.workspace_name,
                is_default=workspace_db.is_default,
            )
        )

    return result


@router.get("/current", response_model=WorkspaceRetrieve)
async def get_current_workspace(
    calling_user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> WorkspaceRetrieve:
    """Return the current default workspace for the user."""
    try:
        workspace_db = await get_user_default_workspace(
            asession=asession, user_db=calling_user_db
        )

        if workspace_db is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No default workspace found for the user.",
            )

        # Get username of the person who rotated the key if available
        rotator_username = None
        if workspace_db.api_key_rotated_by_user_id:
            try:
                rotator_user = await get_user_by_user_id(
                    workspace_db.api_key_rotated_by_user_id, asession
                )
                rotator_username = rotator_user.username
            except UserNotFoundError:
                rotator_username = "Unknown User"

        return WorkspaceRetrieve(
            api_daily_quota=workspace_db.api_daily_quota,
            api_key_first_characters=workspace_db.api_key_first_characters,
            api_key_updated_datetime_utc=workspace_db.api_key_updated_datetime_utc,
            api_key_rotated_by_user_id=workspace_db.api_key_rotated_by_user_id,
            api_key_rotated_by_username=rotator_username,
            content_quota=workspace_db.content_quota,
            created_datetime_utc=workspace_db.created_datetime_utc,
            updated_datetime_utc=workspace_db.updated_datetime_utc,
            workspace_id=workspace_db.workspace_id,
            workspace_name=workspace_db.workspace_name,
            is_default=workspace_db.is_default,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default workspace found for the user.",
        ) from e


@router.post("/switch", response_model=AuthenticationDetails)
async def switch_workspace(
    calling_user_db: Annotated[UserDB, Depends(get_current_user)],
    workspace_switch: WorkspaceSwitch,
    asession: AsyncSession = Depends(get_async_session),
) -> AuthenticationDetails:
    """Switch to a different workspace."""
    # Find the workspace
    try:
        workspace_db = await get_workspace_by_workspace_name(
            asession=asession, workspace_name=workspace_switch.workspace_name
        )
    except WorkspaceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace '{workspace_switch.workspace_name}' not found.",
        ) from e

    # Check if user belongs to this workspace
    user_role = await get_user_role_in_workspace(
        asession=asession, user_db=calling_user_db, workspace_db=workspace_db
    )

    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"User does not have access to workspace "
                f"'{workspace_switch.workspace_name}'."
            ),
        )

    # Set this workspace as the default for the user
    await update_user_default_workspace(
        asession=asession, user_db=calling_user_db, workspace_db=workspace_db
    )

    # Create a new token with the updated workspace information
    return AuthenticationDetails(
        access_level="fullaccess",
        access_token=create_access_token(calling_user_db.username),
        token_type="bearer",
        username=calling_user_db.username,
        is_verified=calling_user_db.is_verified,
        api_key_first_characters=calling_user_db.api_key_first_characters,
    )


@router.put("/rotate-key", response_model=WorkspaceKeyResponse)
async def rotate_workspace_api_key(
    calling_user_db: Annotated[UserDB, Depends(require_admin_role)],
    asession: AsyncSession = Depends(get_async_session),
) -> WorkspaceKeyResponse:
    """Generate a new API key for the current workspace."""
    try:
        # Get the user's default workspace
        workspace_db = await get_user_default_workspace(
            asession=asession, user_db=calling_user_db
        )

        if workspace_db is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found.",
            )

        # Generate and update the API key
        new_api_key = generate_key()
        asession.add(workspace_db)
        workspace_db = await update_workspace_api_key(
            asession=asession,
            new_api_key=new_api_key,
            workspace_db=workspace_db,
            user_db=calling_user_db,
        )

        return WorkspaceKeyResponse(
            new_api_key=new_api_key,
            workspace_name=workspace_db.workspace_name,
        )
    except Exception as e:
        logger.error(f"Error rotating workspace API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error rotating workspace API key.",
        ) from e


@router.get("/{workspace_id}/key-history", response_model=list[ApiKeyRotationHistory])
async def get_workspace_key_history(
    workspace_id: int,
    calling_user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[ApiKeyRotationHistory]:
    """Get API key rotation history for a workspace."""
    try:
        workspace_db = await get_workspace_by_workspace_id(
            asession=asession, workspace_id=workspace_id
        )

        user_role = await get_user_role_in_workspace(
            asession=asession, user_db=calling_user_db, workspace_db=workspace_db
        )

        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"User does not have access to workspace with ID {workspace_id}."
                ),
            )

        # Query for rotation history
        stmt = (
            select(ApiKeyRotationHistoryDB)
            .where(ApiKeyRotationHistoryDB.workspace_id == workspace_id)
            .order_by(ApiKeyRotationHistoryDB.rotation_datetime_utc.desc())
        )

        result = await asession.execute(stmt)
        rotation_history = result.scalars().all()

        formatted_history = []
        for history in rotation_history:
            try:
                rotator_user = await get_user_by_user_id(
                    history.rotated_by_user_id, asession
                )
                rotator_username = rotator_user.username
            except UserNotFoundError:
                rotator_username = "Unknown User"

            formatted_history.append(
                ApiKeyRotationHistory(
                    rotation_id=history.rotation_id,
                    workspace_id=history.workspace_id,
                    rotated_by_user_id=history.rotated_by_user_id,
                    rotated_by_username=rotator_username,
                    key_first_characters=history.key_first_characters,
                    rotation_datetime_utc=history.rotation_datetime_utc,
                )
            )

        return formatted_history
    except WorkspaceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {workspace_id} not found.",
        ) from e


@router.get("/{workspace_id}", response_model=WorkspaceRetrieve)
async def retrieve_workspace_by_workspace_id(
    calling_user_db: Annotated[UserDB, Depends(get_current_user)],
    workspace_id: int,
    asession: AsyncSession = Depends(get_async_session),
) -> WorkspaceRetrieve:
    """Retrieve a workspace by ID."""
    try:
        # Get the workspace
        workspace_db = await get_workspace_by_workspace_id(
            asession=asession, workspace_id=workspace_id
        )

        # Check if user has access to this workspace
        user_role = await get_user_role_in_workspace(
            asession=asession, user_db=calling_user_db, workspace_db=workspace_db
        )

        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"User does not have access to workspace with ID {workspace_id}."
                ),
            )

        # Get username of the person who rotated the key if available
        rotator_username = None
        if workspace_db.api_key_rotated_by_user_id:
            try:
                rotator_user = await get_user_by_user_id(
                    workspace_db.api_key_rotated_by_user_id, asession
                )
                rotator_username = rotator_user.username
            except UserNotFoundError:
                rotator_username = "Unknown User"

        return WorkspaceRetrieve(
            api_daily_quota=workspace_db.api_daily_quota,
            api_key_first_characters=workspace_db.api_key_first_characters,
            api_key_updated_datetime_utc=workspace_db.api_key_updated_datetime_utc,
            api_key_rotated_by_user_id=workspace_db.api_key_rotated_by_user_id,
            api_key_rotated_by_username=rotator_username,
            content_quota=workspace_db.content_quota,
            created_datetime_utc=workspace_db.created_datetime_utc,
            updated_datetime_utc=workspace_db.updated_datetime_utc,
            workspace_id=workspace_db.workspace_id,
            workspace_name=workspace_db.workspace_name,
            is_default=workspace_db.is_default,
        )
    except WorkspaceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {workspace_id} not found.",
        ) from e


@router.put("/{workspace_id}", response_model=WorkspaceRetrieve)
async def update_workspace_endpoint(
    workspace_id: int,
    workspace_update: WorkspaceUpdate,
    calling_user_db: Annotated[UserDB, Depends(require_admin_role)],
    asession: AsyncSession = Depends(get_async_session),
) -> WorkspaceRetrieve:
    """Update workspace details (name, quotas)."""
    try:
        # Get the workspace
        workspace_db = await get_workspace_by_workspace_id(
            asession=asession, workspace_id=workspace_id
        )

        # Check if the new workspace name is valid
        if (
            workspace_update.workspace_name
            and workspace_update.workspace_name != workspace_db.workspace_name
        ):
            if not await is_workspace_name_valid(
                asession=asession, workspace_name=workspace_update.workspace_name
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Workspace with name '{workspace_update.workspace_name}' "
                        "already exists."
                    ),
                )

        # Update the workspace
        asession.add(workspace_db)
        updated_workspace = await update_workspace_name_and_quotas(
            asession=asession, workspace=workspace_update, workspace_db=workspace_db
        )

        return WorkspaceRetrieve(
            api_daily_quota=updated_workspace.api_daily_quota,
            api_key_first_characters=updated_workspace.api_key_first_characters,
            api_key_updated_datetime_utc=updated_workspace.api_key_updated_datetime_utc,
            content_quota=updated_workspace.content_quota,
            created_datetime_utc=updated_workspace.created_datetime_utc,
            updated_datetime_utc=updated_workspace.updated_datetime_utc,
            workspace_id=updated_workspace.workspace_id,
            workspace_name=updated_workspace.workspace_name,
            is_default=updated_workspace.is_default,
        )
    except WorkspaceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {workspace_id} not found.",
        ) from e
    except SQLAlchemyError as e:
        logger.error(f"Database error when updating workspace: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error when updating workspace.",
        ) from e


@router.post("/invite", response_model=WorkspaceInviteResponse)
async def invite_user_to_workspace(
    calling_user_db: Annotated[UserDB, Depends(require_admin_role)],
    invite: WorkspaceInvite,
    background_tasks: BackgroundTasks,
    asession: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis),
) -> WorkspaceInviteResponse:
    """Invite a user to join a workspace."""
    try:
        # Get the workspace
        workspace_db = await get_workspace_by_workspace_name(
            asession=asession, workspace_name=invite.workspace_name
        )

        # Check if it's a default workspace
        # (users can't invite others to default workspaces)
        if workspace_db.is_default:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Users cannot be invited to default workspaces.",
            )

        try:
            invited_user = await get_user_by_username(
                username=invite.email, asession=asession
            )

            # Add existing user to workspace
            await add_existing_user_to_workspace(
                asession=asession,
                user=UserCreate(
                    role=invite.role,
                    username=invite.email,
                    first_name=invited_user.first_name,
                    last_name=invited_user.last_name,
                    workspace_name=invite.workspace_name,
                ),
                workspace_db=workspace_db,
            )

            # Send invitation email to existing user
            background_tasks.add_task(
                email_service.send_workspace_invitation_email,
                invite.email,
                invite.email,
                calling_user_db.username,
                workspace_db.workspace_name,
                True,  # user exists
            )

            return WorkspaceInviteResponse(
                message=(
                    f"User {invite.email} has been added to workspace "
                    f"'{workspace_db.workspace_name}'."
                ),
                email=invite.email,
                workspace_name=workspace_db.workspace_name,
                user_exists=True,
            )

        except UserNotFoundError:
            # User doesn't exist, create pending invitation
            await create_pending_invitation(
                asession=asession,
                email=invite.email,
                workspace_db=workspace_db,
                role=invite.role,
                inviter_id=calling_user_db.user_id,
            )

            # Send invitation email
            background_tasks.add_task(
                email_service.send_workspace_invitation_email,
                invite.email,
                invite.email,
                calling_user_db.username,
                workspace_db.workspace_name,
                False,  # user doesn't exist
            )

            return WorkspaceInviteResponse(
                message=(
                    f"Invitation sent to {invite.email} to join workspace "
                    f"'{workspace_db.workspace_name}'."
                ),
                email=invite.email,
                workspace_name=workspace_db.workspace_name,
                user_exists=False,
            )

    except WorkspaceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace '{invite.workspace_name}' not found.",
        ) from e
    except Exception as e:
        logger.error(f"Error inviting user to workspace: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error inviting user to workspace.",
        ) from e


@router.get("/{workspace_id}/users", response_model=list[WorkspaceUserResponse])
async def get_workspace_users(
    workspace_id: int,
    calling_user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[WorkspaceUserResponse]:
    """Get all users in a workspace."""
    try:
        workspace_db = await get_workspace_by_workspace_id(
            asession=asession, workspace_id=workspace_id
        )

        user_role = await get_user_role_in_workspace(
            asession=asession, user_db=calling_user_db, workspace_db=workspace_db
        )

        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"User does not have access to workspace with ID {workspace_id}."
                ),
            )

        user_workspaces = await get_users_in_workspace(
            asession=asession, workspace_db=workspace_db
        )

        result = []
        for uw in user_workspaces:
            user = await get_user_by_user_id(uw.user_id, asession)
            result.append(
                WorkspaceUserResponse(
                    user_id=user.user_id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=uw.user_role,
                    is_default_workspace=uw.default_workspace,
                    created_datetime_utc=uw.created_datetime_utc,
                )
            )

        return result
    except WorkspaceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {workspace_id} not found.",
        ) from e


@router.delete("/{workspace_id}/users/{username}", response_model=MessageResponse)
async def remove_user_from_workspace_endpoint(
    workspace_id: int,
    username: str,
    calling_user_db: Annotated[UserDB, Depends(require_admin_role)],
    asession: AsyncSession = Depends(get_async_session),
) -> MessageResponse:
    """Remove a user from a workspace."""
    try:
        workspace_db = await get_workspace_by_workspace_id(
            asession=asession, workspace_id=workspace_id
        )

        if workspace_db.is_default:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove users from default workspaces.",
            )

        if username == calling_user_db.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot remove yourself from a workspace.",
            )

        try:
            user_to_remove = await get_user_by_username(
                username=username, asession=asession
            )
        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with username '{username}' not found.",
            ) from e

        try:
            await remove_user_from_workspace(
                asession=asession, user_db=user_to_remove, workspace_db=workspace_db
            )
            return MessageResponse(
                message=(
                    f"User '{username}' successfully removed from workspace "
                    f"'{workspace_db.workspace_name}'."
                )
            )
        except UserNotFoundInWorkspaceError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"User '{username}' is not a member of workspace "
                    f"'{workspace_db.workspace_name}'."
                ),
            ) from e
    except WorkspaceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {workspace_id} not found.",
        ) from e
