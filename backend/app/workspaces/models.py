from datetime import datetime, timezone
from typing import TYPE_CHECKING, Sequence, cast

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    and_,
    case,
    exists,
    select,
    text,
    update,
)
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import Base, ExperimentBaseDB
from ..users.exceptions import UserNotFoundError
from ..users.schemas import UserCreate
from .schemas import UserCreateWithCode, UserRoles

# Use TYPE_CHECKING for type hints without runtime imports
if TYPE_CHECKING:
    from ..users.models import UserDB


class UserWorkspaceRoleAlreadyExistsError(Exception):
    """Exception raised when a user workspace role already exists in the database."""


class UserNotFoundInWorkspaceError(Exception):
    """Exception raised when a user is not found in a workspace in the database."""


class WorkspaceDB(Base):
    """ORM for managing workspaces.

    A workspace is an isolated virtual environment that contains contents that can be
    accessed and modified by users assigned to that workspace. Workspaces must be
    unique but can contain duplicated content. Users can be assigned to one more
    workspaces, with different roles. In other words, there is a MANY-to-MANY
    relationship between users and workspaces.
    """

    __tablename__ = "workspace"

    api_daily_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    api_key_first_characters: Mapped[str] = mapped_column(String(5), nullable=True)
    api_key_updated_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    api_key_rotated_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=True
    )
    content_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    hashed_api_key: Mapped[str] = mapped_column(String(96), nullable=True, unique=True)
    updated_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    user_workspaces: Mapped[list["UserWorkspaceDB"]] = relationship(
        "UserWorkspaceDB",
        back_populates="workspace",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    users: Mapped[list["UserDB"]] = relationship(
        "UserDB", back_populates="workspaces", secondary="user_workspace", viewonly=True
    )
    workspace_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    workspace_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    experiments: Mapped[list["ExperimentBaseDB"]] = relationship(
        "ExperimentBaseDB", back_populates="workspace", cascade="all, delete-orphan"
    )

    pending_invitations: Mapped[list["PendingInvitationDB"]] = relationship(
        "PendingInvitationDB", back_populates="workspace", cascade="all, delete-orphan"
    )

    api_key_rotated_by: Mapped["UserDB"] = relationship(
        "UserDB", foreign_keys=[api_key_rotated_by_user_id]
    )

    key_rotation_history: Mapped[list["ApiKeyRotationHistoryDB"]] = relationship(
        "ApiKeyRotationHistoryDB",
        back_populates="workspace",
        cascade="all, delete-orphan",
        order_by="desc(ApiKeyRotationHistoryDB.rotation_datetime_utc)",
    )

    def __repr__(self) -> str:
        """Define the string representation for the `WorkspaceDB` class."""
        return (
            f"<Workspace '{self.workspace_name}' mapped to workspace ID "
            f"`{self.workspace_id}`>"
        )


class UserWorkspaceDB(Base):
    """ORM for managing user in workspaces."""

    __tablename__ = "user_workspace"

    created_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    default_workspace: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),  # Ensures existing rows default to false
    )
    updated_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    user: Mapped["UserDB"] = relationship("UserDB", back_populates="user_workspaces")
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    user_role: Mapped[UserRoles] = mapped_column(
        Enum(UserRoles, native_enum=False), nullable=False
    )
    workspace: Mapped["WorkspaceDB"] = relationship(
        "WorkspaceDB", back_populates="user_workspaces"
    )
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspace.workspace_id", ondelete="CASCADE"),
        primary_key=True,
    )

    def __repr__(self) -> str:
        """Define the string representation for the `UserWorkspaceDB` class."""
        return (
            f"<User ID '{self.user_id} has role '{self.user_role.value}' "
            f"set for workspace ID '{self.workspace_id}'>."
        )


class PendingInvitationDB(Base):
    """ORM for managing pending workspace invitations."""

    __tablename__ = "pending_invitations"

    invitation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspace.workspace_id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[UserRoles] = mapped_column(
        Enum(UserRoles, native_enum=False), nullable=False
    )
    inviter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    created_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    workspace: Mapped["WorkspaceDB"] = relationship(
        "WorkspaceDB", back_populates="pending_invitations"
    )

    def __repr__(self) -> str:
        return (
            f"<Invitation for {self.email} to workspace {self.workspace_id} "
            f"with role {self.role}>"
        )


class ApiKeyRotationHistoryDB(Base):
    """ORM for tracking workspace API key rotation history."""

    __tablename__ = "api_key_rotation_history"

    rotation_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    workspace_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("workspace.workspace_id", ondelete="CASCADE"),
        nullable=False,
    )
    rotated_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    key_first_characters: Mapped[str] = mapped_column(String(5), nullable=False)
    rotation_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    workspace: Mapped["WorkspaceDB"] = relationship(
        "WorkspaceDB", back_populates="key_rotation_history"
    )
    rotated_by: Mapped["UserDB"] = relationship(
        "UserDB", foreign_keys=[rotated_by_user_id]
    )

    def __repr__(self) -> str:
        """Define the string representation."""
        return (
            f"<API Key Rotation for workspace #{self.workspace_id} by user "
            f"#{self.rotated_by_user_id}>"
        )


async def get_users_in_workspace(
    *, asession: AsyncSession, workspace_db: WorkspaceDB
) -> Sequence[UserWorkspaceDB]:
    """Get all users in a workspace with their roles."""
    stmt = select(UserWorkspaceDB).where(
        UserWorkspaceDB.workspace_id == workspace_db.workspace_id
    )
    result = await asession.execute(stmt)
    return result.unique().scalars().all()


async def get_user_by_user_id(user_id: int, asession: AsyncSession) -> "UserDB":
    """Get a user by user ID."""
    from ..users.models import UserDB

    stmt = select(UserDB).where(UserDB.user_id == user_id)
    result = await asession.execute(stmt)
    try:
        return result.scalar_one()
    except NoResultFound as e:
        raise UserNotFoundError(f"User with ID {user_id} not found") from e


async def remove_user_from_workspace(
    *, asession: AsyncSession, user_db: "UserDB", workspace_db: WorkspaceDB
) -> None:
    """Remove a user from a workspace."""
    # Check if user exists in workspace
    stmt = select(UserWorkspaceDB).where(
        and_(
            UserWorkspaceDB.user_id == user_db.user_id,
            UserWorkspaceDB.workspace_id == workspace_db.workspace_id,
        )
    )
    result = await asession.execute(stmt)
    user_workspace = result.scalar_one_or_none()

    if not user_workspace:
        raise UserNotFoundInWorkspaceError(
            f"User '{user_db.username}' not found in workspace "
            f"'{workspace_db.workspace_name}'."
        )

    # Delete the relationship
    await asession.delete(user_workspace)
    await asession.commit()


async def create_pending_invitation(
    *,
    asession: AsyncSession,
    email: str,
    workspace_db: WorkspaceDB,
    role: UserRoles,
    inviter_id: int,
) -> PendingInvitationDB:
    """Create a pending invitation."""
    invitation = PendingInvitationDB(
        email=email,
        workspace_id=workspace_db.workspace_id,
        role=role,
        inviter_id=inviter_id,
        created_datetime_utc=datetime.now(timezone.utc),
    )

    asession.add(invitation)
    await asession.commit()
    await asession.refresh(invitation)

    return invitation


async def get_pending_invitations_by_email(
    *, asession: AsyncSession, email: str
) -> Sequence[PendingInvitationDB]:
    """Get all pending invitations for an email."""
    stmt = select(PendingInvitationDB).where(PendingInvitationDB.email == email)
    result = await asession.execute(stmt)
    return result.scalars().all()


async def delete_pending_invitation(
    *, asession: AsyncSession, invitation: PendingInvitationDB
) -> None:
    """Delete a pending invitation."""
    await asession.delete(invitation)
    await asession.commit()


async def check_if_user_has_default_workspace(
    *, asession: AsyncSession, user_db: "UserDB"
) -> bool | None:
    """Check if a user has an assigned default workspace."""
    stmt = select(
        exists().where(
            UserWorkspaceDB.user_id == user_db.user_id,
            UserWorkspaceDB.default_workspace.is_(True),
        )
    )
    result = await asession.execute(stmt)
    return result.scalar()


async def get_user_default_workspace(
    *, asession: AsyncSession, user_db: "UserDB"
) -> WorkspaceDB | None:
    """Retrieve the default workspace for a given user."""
    stmt = (
        select(WorkspaceDB)
        .join(UserWorkspaceDB, UserWorkspaceDB.workspace_id == WorkspaceDB.workspace_id)
        .where(
            UserWorkspaceDB.user_id == user_db.user_id,
            UserWorkspaceDB.default_workspace.is_(True),
        )
        .limit(1)
    )

    result = await asession.execute(stmt)
    default_workspace_db = result.scalar_one_or_none()
    return default_workspace_db


async def get_user_workspaces(
    *, asession: AsyncSession, user_db: "UserDB"
) -> Sequence[WorkspaceDB]:
    """Retrieve all workspaces a user belongs to."""
    stmt = (
        select(WorkspaceDB)
        .join(UserWorkspaceDB, UserWorkspaceDB.workspace_id == WorkspaceDB.workspace_id)
        .where(UserWorkspaceDB.user_id == user_db.user_id)
    )
    result = await asession.execute(stmt)
    return result.scalars().all()


async def get_user_role_in_workspace(
    *, asession: AsyncSession, user_db: "UserDB", workspace_db: WorkspaceDB
) -> UserRoles | None:
    """Retrieve the role of a user in a workspace."""
    stmt = select(UserWorkspaceDB.user_role).where(
        UserWorkspaceDB.user_id == user_db.user_id,
        UserWorkspaceDB.workspace_id == workspace_db.workspace_id,
    )
    result = await asession.execute(stmt)
    user_role = result.scalar_one_or_none()
    return user_role


async def update_user_default_workspace(
    *, asession: AsyncSession, user_db: "UserDB", workspace_db: WorkspaceDB
) -> None:
    """Update the default workspace for the user to the specified workspace."""
    stmt = (
        update(UserWorkspaceDB)
        .where(UserWorkspaceDB.user_id == user_db.user_id)
        .values(
            default_workspace=case(
                (UserWorkspaceDB.workspace_id == workspace_db.workspace_id, True),
                else_=False,
            ),
            updated_datetime_utc=datetime.now(timezone.utc),
        )
    )

    await asession.execute(stmt)
    await asession.commit()


async def create_user_workspace_role(
    *,
    asession: AsyncSession,
    is_default_workspace: bool = False,
    user_db: "UserDB",
    user_role: UserRoles,
    workspace_db: WorkspaceDB,
) -> UserWorkspaceDB:
    """Create a user in a workspace with the specified role."""
    existing_user_role = await get_user_role_in_workspace(
        asession=asession, user_db=user_db, workspace_db=workspace_db
    )

    if existing_user_role is not None:
        raise UserWorkspaceRoleAlreadyExistsError(
            f"User '{user_db.username}' with role '{user_role}' in workspace "
            f"{workspace_db.workspace_name} already exists."
        )

    user_workspace_role_db = UserWorkspaceDB(
        created_datetime_utc=datetime.now(timezone.utc),
        default_workspace=is_default_workspace,
        updated_datetime_utc=datetime.now(timezone.utc),
        user_id=user_db.user_id,
        user_role=user_role,
        workspace_id=workspace_db.workspace_id,
    )

    asession.add(user_workspace_role_db)
    await asession.commit()
    await asession.refresh(user_workspace_role_db)

    return user_workspace_role_db


async def get_workspaces_by_user_role(
    *, asession: AsyncSession, user_db: "UserDB", user_role: UserRoles
) -> Sequence[WorkspaceDB]:
    """Retrieve all workspaces for the user with the specified role."""
    stmt = (
        select(WorkspaceDB)
        .join(UserWorkspaceDB, WorkspaceDB.workspace_id == UserWorkspaceDB.workspace_id)
        .where(UserWorkspaceDB.user_id == user_db.user_id)
        .where(UserWorkspaceDB.user_role == user_role)
    )
    result = await asession.execute(stmt)
    return result.scalars().all()


async def user_has_admin_role_in_any_workspace(
    *, asession: AsyncSession, user_db: "UserDB"
) -> bool:
    """Check if a user has the ADMIN role in any workspace."""
    stmt = (
        select(UserWorkspaceDB.user_id)
        .where(
            UserWorkspaceDB.user_id == user_db.user_id,
            UserWorkspaceDB.user_role == UserRoles.ADMIN,
        )
        .limit(1)
    )
    result = await asession.execute(stmt)
    return result.scalar_one_or_none() is not None


async def add_existing_user_to_workspace(
    *,
    asession: AsyncSession,
    user: UserCreate,
    workspace_db: WorkspaceDB,
) -> UserCreateWithCode:
    """Add an existing user to a workspace."""
    # Import here to avoid circular imports
    from ..users.models import get_user_by_username

    assert user.role is not None
    user.is_default_workspace = user.is_default_workspace or False

    user_db = await get_user_by_username(username=user.username, asession=asession)

    if user.is_default_workspace:
        await update_user_default_workspace(
            asession=asession, user_db=user_db, workspace_db=workspace_db
        )

    user_role = cast(UserRoles, user.role)

    _ = await create_user_workspace_role(
        asession=asession,
        is_default_workspace=user.is_default_workspace,
        user_db=user_db,
        user_role=user_role,
        workspace_db=workspace_db,
    )

    return UserCreateWithCode(
        is_default_workspace=user.is_default_workspace,
        recovery_codes=[],  # We don't use recovery codes in your implementation
        role=user_role,
        username=user_db.username,
        workspace_name=workspace_db.workspace_name,
    )
