import os
from datetime import datetime
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import Session

from backend.app import create_app
from backend.app.database import (
    get_connection_url,
    get_session_context_manager,
)
from backend.app.users.models import UserDB
from backend.app.utils import get_key_hash, get_password_salted_hash

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
    regular_user = UserDB(
        username=TEST_USERNAME,
        hashed_password=get_password_salted_hash(TEST_PASSWORD),
        first_name=TEST_FIRST_NAME,
        last_name=TEST_LAST_NAME,
        hashed_api_key=get_key_hash(TEST_USER_API_KEY),
        api_key_first_characters=TEST_USER_API_KEY[:5],
        api_key_updated_datetime_utc=datetime.utcnow(),
        experiments_quota=TEST_EXPERIMENTS_QUOTA,
        api_daily_quota=TEST_API_QUOTA,
        created_datetime_utc=datetime.utcnow(),
        updated_datetime_utc=datetime.utcnow(),
    )

    db_session.add(regular_user)
    db_session.commit()
    yield regular_user.user_id

    db_session.delete(regular_user)
    db_session.commit()


@pytest.fixture(scope="session")
def user1(client: TestClient, db_session: Session) -> Generator:
    stmt = select(UserDB).where(UserDB.username == TEST_USERNAME)
    result = db_session.execute(stmt)
    user = result.scalar_one()
    yield user.user_id


@pytest.fixture(scope="session")
def user2(client: TestClient, db_session: Session) -> Generator:
    stmt = select(UserDB).where(UserDB.username == TEST_USERNAME_2)
    result = db_session.execute(stmt)
    user = result.scalar_one()
    yield user.user_id


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
