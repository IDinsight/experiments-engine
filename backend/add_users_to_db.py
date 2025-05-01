import asyncio
import os
from datetime import datetime, timezone

from redis import asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from app.config import REDIS_HOST
from app.database import get_session
from app.users.models import UserDB
from app.utils import (
    encode_api_limit,
    get_key_hash,
    get_password_salted_hash,
    setup_logger,
)

logger = setup_logger()

# admin user
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin@idinsight.org")
ADMIN_FIRST_NAME = os.environ.get("ADMIN_FIRST_NAME", "Admin")
ADMIN_LAST_NAME = os.environ.get("ADMIN_LAST_NAME", "User")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "12345")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "admin-key")
ADMIN_EXPERIMENT_QUOTA = os.environ.get("ADMIN_EXPERIMENT_QUOTA", None)
ADMIN_API_DAILY_QUOTA = os.environ.get("ADMIN_API_DAILY_QUOTA", None)


user_db = UserDB(
    username=ADMIN_USERNAME,
    first_name=ADMIN_FIRST_NAME,
    last_name=ADMIN_LAST_NAME,
    hashed_password=get_password_salted_hash(ADMIN_PASSWORD),
    hashed_api_key=get_key_hash(ADMIN_API_KEY),
    api_key_first_characters=ADMIN_API_KEY[:5],
    api_key_updated_datetime_utc=datetime.now(timezone.utc),
    experiments_quota=ADMIN_EXPERIMENT_QUOTA,
    api_daily_quota=ADMIN_API_DAILY_QUOTA,
    created_datetime_utc=datetime.now(timezone.utc),
    updated_datetime_utc=datetime.now(timezone.utc),
    is_active=True,
    is_verified=True,
)


async def async_redis_operations(key: str, value: int | None) -> None:
    """
    Asynchronous Redis operations to set the remaining API calls for a user.
    """
    redis = await aioredis.from_url(REDIS_HOST)

    await redis.set(key, encode_api_limit(value))

    await redis.aclose()


def run_redis_async_tasks(key: str, value: int | str) -> None:
    """
    Run asynchronous Redis operations to set the remaining API calls for a user.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    value_int = int(value) if value is not None else None
    loop.run_until_complete(async_redis_operations(key, value_int))


if __name__ == "__main__":
    db_session = next(get_session())
    stmt = select(UserDB).where(UserDB.username == user_db.username)
    result = db_session.execute(stmt)
    try:
        result.one()
        logger.info(f"User with username {user_db.username} already exists.")
    except NoResultFound:
        db_session.add(user_db)
        run_redis_async_tasks(
            f"remaining-calls:{user_db.username}", user_db.api_daily_quota
        )
        logger.info(f"User with username {user_db.username} added to local database.")

    except MultipleResultsFound:
        logger.error(
            f"Multiple users with username {user_db.username} found in local database."
        )

    db_session.commit()
