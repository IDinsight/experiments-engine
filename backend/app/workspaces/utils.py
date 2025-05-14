from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from ..users.models import UserDB
from ..utils import get_key_hash
from .models import ApiKeyRotationHistoryDB, WorkspaceDB
from .schemas import WorkspaceUpdate


class WorkspaceNotFoundError(Exception):
    """Exception raised when a workspace is not found in the database."""


async def check_if_workspaces_exist(*, asession: AsyncSession) -> bool:
    """Check if workspaces exist in the `WorkspaceDB` database."""
    stmt = select(WorkspaceDB.workspace_id).limit(1)
    result = await asession.scalars(stmt)
    return result.first() is not None


async def create_workspace(
    *,
    api_daily_quota: Optional[int] = None,
    asession: AsyncSession,
    content_quota: Optional[int] = None,
    workspace_name: str,
    is_default: bool = False,
    api_key: Optional[str] = None,
) -> tuple[WorkspaceDB, bool]:
    """Create a workspace in the `WorkspaceDB` database. If the workspace already
    exists, then it is returned.
    """
    assert api_daily_quota is None or api_daily_quota >= 0
    assert content_quota is None or content_quota >= 0

    result = await asession.execute(
        select(WorkspaceDB).where(WorkspaceDB.workspace_name == workspace_name)
    )
    workspace_db = result.scalar_one_or_none()
    new_workspace = False

    if workspace_db is None:
        new_workspace = True
        workspace_db = WorkspaceDB(
            api_daily_quota=api_daily_quota,
            content_quota=content_quota,
            created_datetime_utc=datetime.now(timezone.utc),
            updated_datetime_utc=datetime.now(timezone.utc),
            workspace_name=workspace_name,
            is_default=is_default,
        )

        if api_key:
            workspace_db.hashed_api_key = get_key_hash(api_key)
            workspace_db.api_key_first_characters = api_key[:5]
            workspace_db.api_key_updated_datetime_utc = datetime.now(timezone.utc)

        asession.add(workspace_db)
        await asession.commit()
        await asession.refresh(workspace_db)

    return workspace_db, new_workspace


async def get_workspace_by_workspace_id(
    *, asession: AsyncSession, workspace_id: int
) -> WorkspaceDB:
    """Retrieve a workspace by workspace ID."""
    stmt = select(WorkspaceDB).where(WorkspaceDB.workspace_id == workspace_id)
    result = await asession.execute(stmt)
    try:
        workspace_db = result.scalar_one()
        return workspace_db
    except NoResultFound as err:
        raise WorkspaceNotFoundError(
            f"Workspace with ID {workspace_id} does not exist."
        ) from err


async def get_workspace_by_workspace_name(
    *, asession: AsyncSession, workspace_name: str
) -> WorkspaceDB:
    """Retrieve a workspace by workspace name."""
    stmt = select(WorkspaceDB).where(WorkspaceDB.workspace_name == workspace_name)
    result = await asession.execute(stmt)
    try:
        workspace_db = result.scalar_one()
        return workspace_db
    except NoResultFound as err:
        raise WorkspaceNotFoundError(
            f"Workspace with name {workspace_name} does not exist."
        ) from err


async def is_workspace_name_valid(
    *, asession: AsyncSession, workspace_name: str
) -> bool:
    """Check if a workspace name is valid. A workspace name is valid if it doesn't
    already exist in the database.
    """
    stmt = select(WorkspaceDB).where(WorkspaceDB.workspace_name == workspace_name)
    result = await asession.execute(stmt)
    try:
        result.scalar_one()
        return False
    except NoResultFound:
        return True


async def update_workspace_api_key(
    *,
    asession: AsyncSession,
    new_api_key: str,
    workspace_db: WorkspaceDB,
    user_db: "UserDB",
) -> WorkspaceDB:
    """Update a workspace API key and record the rotation history."""
    workspace_db.hashed_api_key = get_key_hash(key=new_api_key)
    workspace_db.api_key_first_characters = new_api_key[:5]
    workspace_db.api_key_updated_datetime_utc = datetime.now(timezone.utc)
    workspace_db.api_key_rotated_by_user_id = user_db.user_id
    workspace_db.updated_datetime_utc = datetime.now(timezone.utc)

    rotation_history = ApiKeyRotationHistoryDB(
        workspace_id=workspace_db.workspace_id,
        rotated_by_user_id=user_db.user_id,
        key_first_characters=new_api_key[:5],
        rotation_datetime_utc=datetime.now(timezone.utc),
    )

    asession.add(rotation_history)
    await asession.commit()
    await asession.refresh(workspace_db)

    return workspace_db


async def update_workspace_name_and_quotas(
    *, asession: AsyncSession, workspace: WorkspaceUpdate, workspace_db: WorkspaceDB
) -> WorkspaceDB:
    """Update workspace name"""
    if workspace.workspace_name is not None:
        workspace_db.workspace_name = workspace.workspace_name

    workspace_db.updated_datetime_utc = datetime.now(timezone.utc)

    await asession.commit()
    await asession.refresh(workspace_db)

    return workspace_db
