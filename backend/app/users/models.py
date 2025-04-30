from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    select,
)
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Base
from ..utils import get_key_hash, get_password_salted_hash, get_random_string
from .schemas import UserCreate, UserCreateWithPassword

PASSWORD_LENGTH = 12


class UserNotFoundError(Exception):
    """Exception raised when a user is not found in the database."""


class UserAlreadyExistsError(Exception):
    """Exception raised when a user already exists in the database."""


class UserDB(Base):
    """
    SQL Alchemy data model for users
    """

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(96), nullable=False)
    hashed_api_key: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)
    api_key_first_characters: Mapped[str] = mapped_column(String(5), nullable=False)
    api_key_updated_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    experiments_quota: Mapped[int] = mapped_column(Integer, nullable=True)
    api_daily_quota: Mapped[int] = mapped_column(Integer, nullable=True)
    created_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    access_level: Mapped[str] = mapped_column(
        String, nullable=False, default="fullaccess"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        """Pretty Print"""
        return f"<{self.username} mapped to #{self.user_id}>"


async def save_user_to_db(
    user: UserCreateWithPassword | UserCreate,
    api_key: str,
    asession: AsyncSession,
    is_verified: bool = False,
) -> UserDB:
    """
    Saves a user in the database
    """

    # Check if user with same username already exists
    stmt = select(UserDB).where(UserDB.username == user.username)
    result = await asession.execute(stmt)
    try:
        result.one()
        raise UserAlreadyExistsError(
            f"User with username {user.username} already exists."
        )
    except NoResultFound:
        pass

    if isinstance(user, UserCreateWithPassword):
        hashed_password = get_password_salted_hash(user.password)
    else:
        random_password = get_random_string(PASSWORD_LENGTH)
        hashed_password = get_password_salted_hash(random_password)

    user_db = UserDB(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        experiments_quota=user.experiments_quota,
        api_daily_quota=user.api_daily_quota,
        hashed_password=hashed_password,
        hashed_api_key=get_key_hash(api_key),
        api_key_updated_datetime_utc=datetime.now(timezone.utc),
        api_key_first_characters=api_key[:5],
        created_datetime_utc=datetime.now(timezone.utc),
        updated_datetime_utc=datetime.now(timezone.utc),
        is_active=True,
        is_verified=is_verified,
        access_level="fullaccess",
    )

    asession.add(user_db)
    await asession.commit()
    await asession.refresh(user_db)

    return user_db


async def update_user_api_key(
    user_db: UserDB,
    new_api_key: str,
    asession: AsyncSession,
) -> UserDB:
    """
    Updates a user's API key
    """

    user_db.hashed_api_key = get_key_hash(new_api_key)
    user_db.api_key_first_characters = new_api_key[:5]
    user_db.api_key_updated_datetime_utc = datetime.now(timezone.utc)
    user_db.updated_datetime_utc = datetime.now(timezone.utc)

    await asession.commit()
    await asession.refresh(user_db)

    return user_db


async def update_user_verification_status(
    user_db: UserDB,
    is_verified: bool,
    asession: AsyncSession,
) -> UserDB:
    """
    Updates a user's verification status
    """
    user_db.is_verified = is_verified
    user_db.updated_datetime_utc = datetime.now(timezone.utc)

    await asession.commit()
    await asession.refresh(user_db)

    return user_db


async def update_user_active_status(
    user_db: UserDB,
    is_active: bool,
    asession: AsyncSession,
) -> UserDB:
    """
    Updates a user's active status
    """
    user_db.is_active = is_active
    user_db.updated_datetime_utc = datetime.now(timezone.utc)

    await asession.commit()
    await asession.refresh(user_db)

    return user_db


async def update_user_password(
    user_db: UserDB,
    new_password: str,
    asession: AsyncSession,
) -> UserDB:
    """
    Updates a user's password
    """
    user_db.hashed_password = get_password_salted_hash(new_password)
    user_db.updated_datetime_utc = datetime.now(timezone.utc)

    await asession.commit()
    await asession.refresh(user_db)

    return user_db


async def get_user_by_username(
    username: str,
    asession: AsyncSession,
) -> UserDB:
    """
    Retrieves a user by username
    """
    stmt = select(UserDB).where(UserDB.username == username)
    result = await asession.execute(stmt)
    try:
        user = result.scalar_one()
        return user
    except NoResultFound as err:
        raise UserNotFoundError(
            f"User with username {username} does not exist."
        ) from err


async def get_experiments_quota_by_userid(
    user_id: int,
    asession: AsyncSession,
) -> int:
    """
    Retrieves a user's content quota by user_id
    """
    stmt = select(UserDB).where(UserDB.user_id == user_id)
    result = await asession.execute(stmt)
    try:
        experiments_quota = result.scalar_one().experiments_quota
        return experiments_quota
    except NoResultFound as err:
        raise UserNotFoundError(f"User with user_id {user_id} does not exist.") from err


async def get_user_by_api_key(
    token: str,
    asession: AsyncSession,
) -> UserDB:
    """
    Retrieves a user by token
    """

    hashed_token = get_key_hash(token)

    stmt = select(UserDB).where(UserDB.hashed_api_key == hashed_token)
    result = await asession.execute(stmt)
    try:
        user = result.scalar_one()
        return user
    except NoResultFound as err:
        raise UserNotFoundError("User with given token does not exist.") from err
