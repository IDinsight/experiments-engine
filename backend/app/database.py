from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from collections.abc import AsyncGenerator

from .config import (
    DB_POOL_SIZE,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)

ASYNC_DB_API = "asyncpg"

_ASYNC_ENGINE: AsyncEngine | None = None


def get_connection_url(
    *,
    db_api: str = ASYNC_DB_API,
    user: str = POSTGRES_USER,
    password: str = POSTGRES_PASSWORD,
    host: str = POSTGRES_HOST,
    port: int | str = POSTGRES_PORT,
    db: str = POSTGRES_DB,
    render_as_string: bool = False,
) -> URL:
    """Return a connection string for the given database."""
    return URL.create(
        drivername="postgresql+" + db_api,
        username=user,
        host=host,
        password=password,
        port=int(port),
        database=db,
    )


def get_sqlalchemy_async_engine() -> AsyncEngine:
    """Return a SQLAlchemy async engine generator."""
    global _ASYNC_ENGINE
    if _ASYNC_ENGINE is None:
        connection_string = get_connection_url()
        _ASYNC_ENGINE = create_async_engine(connection_string, pool_size=DB_POOL_SIZE)
    return _ASYNC_ENGINE


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Return a SQLAlchemy async session."""
    async with AsyncSession(
        get_sqlalchemy_async_engine(), expire_on_commit=False
    ) as async_session:
        yield async_session
