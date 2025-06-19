import asyncio
import os
from datetime import datetime, timezone

from redis import asyncio as aioredis

from app.config import REDIS_HOST
from app.database import get_session
from app.users.models import UserDB
from app.utils import (
    encode_api_limit,
    get_key_hash,
    get_password_salted_hash,
    setup_logger,
)
from app.workspaces.models import UserRoles, UserWorkspaceDB, WorkspaceDB

logger = setup_logger()

# admin user
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin@idinsight.org")
ADMIN_FIRST_NAME = os.environ.get("ADMIN_FIRST_NAME", "Admin")
ADMIN_LAST_NAME = os.environ.get("ADMIN_LAST_NAME", "User")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "12345")


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

    try:
        # Check if any users already exist
        user_count = db_session.query(UserDB).count()

        if user_count > 0:
            logger.info(
                "Users already exist in the database. Skipping admin user creation."
            )
            exit(0)

        # Create the admin user
        user_db = UserDB(
            username=ADMIN_USERNAME,
            first_name=ADMIN_FIRST_NAME,
            last_name=ADMIN_LAST_NAME,
            hashed_password=get_password_salted_hash(ADMIN_PASSWORD),
            created_datetime_utc=datetime.now(timezone.utc),
            updated_datetime_utc=datetime.now(timezone.utc),
            is_active=True,
            is_verified=True,
            access_level="fullaccess",
        )

        db_session.add(user_db)
        db_session.flush()  # Generate user_id
        logger.info(f"Created admin user: {ADMIN_USERNAME}")

        # Create default workspace
        workspace_name = f"{ADMIN_USERNAME}'s Workspace"
        hashed_workspace_key = get_key_hash("workspace-api-key-" + workspace_name)
        workspace_db = WorkspaceDB(
            workspace_name=workspace_name,
            api_daily_quota=100,
            content_quota=10,
            created_datetime_utc=datetime.now(timezone.utc),
            updated_datetime_utc=datetime.now(timezone.utc),
            is_default=True,
            hashed_api_key=hashed_workspace_key,
            api_key_first_characters=hashed_workspace_key[:5],
            api_key_updated_datetime_utc=datetime.now(timezone.utc),
            api_key_rotated_by_user_id=user_db.user_id,
        )

        db_session.add(workspace_db)
        db_session.flush()  # Generate workspace_id
        logger.info(f"Created default workspace: {workspace_name}")

        # Create user-workspace relationship
        user_workspace = UserWorkspaceDB(
            user_id=user_db.user_id,
            workspace_id=workspace_db.workspace_id,
            user_role=UserRoles.ADMIN,
            default_workspace=True,
            created_datetime_utc=datetime.now(timezone.utc),
            updated_datetime_utc=datetime.now(timezone.utc),
        )

        db_session.add(user_workspace)
        db_session.commit()
        logger.info("Associated admin user with workspace")

        # Set API limit in Redis
        run_redis_async_tasks(
            f"remaining-calls:{workspace_db.workspace_id}", workspace_db.api_daily_quota
        )
        logger.info("Admin user setup completed successfully")

    except Exception as e:
        db_session.rollback()
        logger.error(f"Error creating admin user: {str(e)}")
        raise
    finally:
        db_session.close()
