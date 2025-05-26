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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import Base
from ..users.exceptions import UserAlreadyExistsError, UserNotFoundError
from ..utils import get_password_salted_hash, get_random_string
from ..workspaces.models import UserWorkspaceDB, WorkspaceDB
from .schemas import UserCreate, UserCreateWithPassword

PASSWORD_LENGTH = 12


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

    user_workspaces: Mapped[list["UserWorkspaceDB"]] = relationship(
        "UserWorkspaceDB",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    workspaces: Mapped[list["WorkspaceDB"]] = relationship(
        "WorkspaceDB", back_populates="users", secondary="user_workspace", viewonly=True
    )

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
        hashed_password=hashed_password,
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
