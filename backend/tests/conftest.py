import os
import uuid
from datetime import UTC, datetime
from typing import AsyncGenerator, Generator

import pytest
import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import Session

from backend.app import create_app
from backend.app.database import (
    get_connection_url,
    get_session_context_manager,
)
from backend.app.users.models import UserDB
from backend.app.utils import get_key_hash, get_password_salted_hash
from backend.app.workspaces.models import UserRoles, UserWorkspaceDB, WorkspaceDB

from .config import (
    TEST_API_QUOTA,
    TEST_EXPERIMENTS_QUOTA,
    TEST_FIRST_NAME,
    TEST_LAST_NAME,
    TEST_PASSWORD,
    TEST_USER_API_KEY,
    TEST_USERNAME,
    TEST_USERNAME_2,
)


@pytest.fixture(scope="function")
async def asession(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async session for testing.

    Parameters
    ----------
    async_engine
        Async engine for testing.

    Yields
    ------
    AsyncGenerator[AsyncSession, None]
        Async session for testing.
    """

    async with AsyncSession(async_engine, expire_on_commit=False) as async_session:
        yield async_session


@pytest.fixture(scope="function")
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an async engine for testing.

    NB: We recreate engine and session to ensure it is in the same event loop as the
    test. Without this we get "Future attached to different loop" error. See:
    https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#using-multiple-asyncio-event-loops

    Yields
    ------
    Generator[AsyncEngine, None, None]
        Async engine for testing.
    """  # noqa: E501

    connection_string = get_connection_url()
    engine = create_async_engine(connection_string, pool_size=20)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
def db_session() -> Generator[Session, None, None]:
    """Create a test database session."""
    with get_session_context_manager() as session:
        yield session


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def regular_user(client: TestClient, db_session: Session) -> Generator:
    # Create a unique username and API key for each test run to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    unique_username = f"{TEST_USERNAME}_{unique_id}"
    unique_api_key = f"{TEST_USER_API_KEY}_{unique_id}"

    # Create user
    regular_user = UserDB(
        username=unique_username,
        hashed_password=get_password_salted_hash(TEST_PASSWORD),
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        created_datetime_utc=datetime.now(UTC),
        updated_datetime_utc=datetime.now(UTC),
        is_verified=True,  # Make user verified for testing
    )

    db_session.add(regular_user)
    db_session.commit()

    # Create default workspace for user with a unique workspace API key
    unique_workspace_api_key = f"workspace_{unique_id}"
    default_workspace = WorkspaceDB(
        workspace_name=f"{unique_username}'s Workspace",
        api_daily_quota=TEST_API_QUOTA,
        content_quota=TEST_EXPERIMENTS_QUOTA,
        created_datetime_utc=datetime.now(UTC),
        updated_datetime_utc=datetime.now(UTC),
        is_default=True,
        hashed_api_key=get_key_hash(unique_workspace_api_key),
        api_key_first_characters=unique_workspace_api_key[:5],
        api_key_updated_datetime_utc=datetime.now(UTC),
        api_key_rotated_by_user_id=regular_user.user_id,
    )

    db_session.add(default_workspace)
    db_session.commit()

    # Create user workspace relationship
    user_workspace = UserWorkspaceDB(
        user_id=regular_user.user_id,
        workspace_id=default_workspace.workspace_id,
        user_role=UserRoles.ADMIN,
        default_workspace=True,
        created_datetime_utc=datetime.now(UTC),
        updated_datetime_utc=datetime.now(UTC),
    )

    db_session.add(user_workspace)
    db_session.commit()

    yield regular_user.user_id, unique_username, unique_api_key

    # Clean up - handle foreign key relationships properly
    # 1. Clean up pending invitations that reference this user as inviter
    db_session.execute(
        text(
            "DELETE FROM pending_invitations WHERE inviter_id = "
            f"{regular_user.user_id}"
        )
    )
    db_session.commit()

    # 2. Clean up API key rotation history records that reference this user
    db_session.execute(
        text(
            "DELETE FROM api_key_rotation_history WHERE rotated_by_user_id = "
            f"{regular_user.user_id}"
        )
    )
    db_session.commit()

    # 3. Remove the user-workspace relationship
    db_session.query(UserWorkspaceDB).filter(
        UserWorkspaceDB.user_id == regular_user.user_id
    ).delete()
    db_session.commit()

    # 4. Remove the reference from workspace.api_key_rotated_by_user_id
    db_session.query(WorkspaceDB).filter(
        WorkspaceDB.api_key_rotated_by_user_id == regular_user.user_id
    ).update({WorkspaceDB.api_key_rotated_by_user_id: None})
    db_session.commit()

    # 5. Now delete the workspace
    db_session.query(WorkspaceDB).filter(
        WorkspaceDB.workspace_name == f"{unique_username}'s Workspace"
    ).delete()
    db_session.commit()

    # 6. Finally delete the user
    db_session.delete(regular_user)
    db_session.commit()


@pytest.fixture(scope="session")
def user1(client: TestClient, db_session: Session) -> Generator:
    stmt = select(UserDB).where(UserDB.username == TEST_USERNAME)
    result = db_session.execute(stmt)
    try:
        user = result.scalar_one()
        yield user.user_id
    except sqlalchemy.exc.NoResultFound:
        print(f"User with username {TEST_USERNAME} not found in the database")
        yield None


@pytest.fixture(scope="session")
def user2(client: TestClient, db_session: Session) -> Generator:
    stmt = select(UserDB).where(UserDB.username == TEST_USERNAME_2)
    result = db_session.execute(stmt)
    try:
        user = result.scalar_one()
        yield user.user_id
    except sqlalchemy.exc.NoResultFound:
        print(f"User with username {TEST_USERNAME_2} not found in the database")
        yield None


@pytest.fixture(scope="session")
def admin_token(client: TestClient) -> str:
    response = client.post(
        "/login",
        data={
            "username": os.environ.get("ADMIN_USERNAME", ""),
            "password": os.environ.get("ADMIN_PASSWORD", ""),
        },
    )
    token = response.json()["access_token"]
    return token


@pytest.fixture(scope="function")
def workspace_api_key(client: TestClient, admin_token: str) -> str:
    """Get the current workspace API key for testing"""
    # Get the current workspace
    response = client.get(
        "/workspace/current",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200

    # Rotate the workspace API key to get a fresh one
    response = client.put(
        "/workspace/rotate-key",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    workspace_api_key = response.json()["new_api_key"]

    return workspace_api_key
