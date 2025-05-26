import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Sequence

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    select,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .schemas import (
    AutoFailUnitType,
    EventType,
    Notifications,
    ObservationType,
)

if TYPE_CHECKING:
    from .workspaces.models import WorkspaceDB


# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass


# --- Base model for experiments ---
class ExperimentDB(Base):
    """
    Base model for experiments.
    """

    __tablename__ = "experiments"

    # IDs
    experiment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspace.workspace_id"), nullable=False
    )

    # Description
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Assignments config
    sticky_assignment: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    auto_fail: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_fail_value: Mapped[int] = mapped_column(Integer, nullable=True)
    auto_fail_unit: Mapped[AutoFailUnitType] = mapped_column(
        Enum(AutoFailUnitType), nullable=True
    )

    # Experiment config
    exp_type: Mapped[str] = mapped_column(String(length=50), nullable=False)
    prior_type: Mapped[str] = mapped_column(String(length=50), nullable=False)
    reward_type: Mapped[str] = mapped_column(String(length=50), nullable=False)

    # State variables
    created_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    n_trials: Mapped[int] = mapped_column(Integer, nullable=False)
    last_trial_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    workspace: Mapped["WorkspaceDB"] = relationship(
        "WorkspaceDB", back_populates="experiments"
    )
    arms: Mapped[list["ArmDB"]] = relationship(
        "ArmDB", back_populates="experiment", lazy="joined"
    )
    draws: Mapped[list["DrawDB"]] = relationship(
        "DrawDB",
        back_populates="experiment",
        primaryjoin="ExperimentDB.experiment_id==DrawDB.experiment_id",
        lazy="joined",
    )
    clients: Mapped[list["ClientDB"]] = relationship(
        "ClientDB",
        back_populates="experiment",
        lazy="joined",
    )
    contexts: Mapped[Optional[list["ContextDB"]]] = relationship(
        "ContextDB",
        back_populates="experiment",
        lazy="joined",
        primaryjoin="and_(ExperimentDB.experiment_id==ContextDB.experiment_id, "
        "ExperimentDB.exp_type=='cmab')",
    )

    __mapper_args__ = {
        "polymorphic_identity": "experiment",
        "polymorphic_on": "exp_type",
    }

    def __repr__(self) -> str:
        """
        String representation of the model
        """
        return f"<Experiment(name={self.name}, type={self.exp_type})>"

    @property
    def has_contexts(self) -> bool:
        """Check if this experiment type supports contexts."""
        return self.exp_type == "cmab"

    @property
    def context_list(self) -> list["ContextDB"]:
        """Get contexts, returning empty list if not applicable."""
        return self.contexts if self.has_contexts else []

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "experiment_id": self.experiment_id,
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "description": self.description,
            "sticky_assignment": self.sticky_assignment,
            "auto_fail": self.auto_fail,
            "auto_fail_value": self.auto_fail_value,
            "auto_fail_unit": self.auto_fail_unit,
            "exp_type": self.exp_type,
            "prior_type": self.prior_type,
            "reward_type": self.reward_type,
            "created_datetime_utc": self.created_datetime_utc,
            "is_active": self.is_active,
            "n_trials": self.n_trials,
            "last_trial_datetime_utc": self.last_trial_datetime_utc,
            "arms": [arm.to_dict() for arm in self.arms],
            "draws": [draw.to_dict() for draw in self.draws],
            "contexts": (
                [context.to_dict() for context in self.context_list]
                if self.has_contexts
                else None
            ),
        }


# --- Arm model ---
class ArmDB(Base):
    """
    Base model for arms.
    """

    __tablename__ = "arms"

    # IDs
    arm_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiments.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )

    # Description
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=False)
    n_outcomes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Prior variables
    mu_init: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sigma_init: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mu: Mapped[Optional[list[float]]] = mapped_column(ARRAY(Float), nullable=True)
    covariance: Mapped[Optional[list[float]]] = mapped_column(
        ARRAY(Float), nullable=True
    )

    alpha_init: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    beta_init: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    alpha: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    beta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    experiment: Mapped[ExperimentDB] = relationship(
        "ExperimentDB", back_populates="arms", lazy="joined"
    )
    draws: Mapped[list["DrawDB"]] = relationship(
        "DrawDB",
        back_populates="arm",
        lazy="joined",
    )

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "arm_id": self.arm_id,
            "experiment_id": self.experiment_id,
            "name": self.name,
            "description": self.description,
            "alpha": self.alpha,
            "beta": self.beta,
            "mu": self.mu,
            "covariance": self.covariance,
            "alpha_init": self.alpha_init,
            "beta_init": self.beta_init,
            "mu_init": self.mu_init,
            "sigma_init": self.sigma_init,
            "draws": [draw.to_dict() for draw in self.draws],
        }


# --- Draw model ---
class DrawDB(Base):
    """
    Base model for draws.
    """

    __tablename__ = "draws"

    # IDs
    draw_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda x: str(uuid.uuid4())
    )
    arm_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("arms.arm_id"), nullable=False
    )
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiments.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    client_id = Mapped[str] = mapped_column(
        String, ForeignKey("clients.client_id"), nullable=True
    )

    # Logging
    draw_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    observed_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    observation_type: Mapped[ObservationType] = mapped_column(
        Enum(ObservationType), nullable=True
    )
    reward: Mapped[float] = mapped_column(Float, nullable=True)
    context_val = Mapped[Optional[list[float]]] = mapped_column(
        ARRAY(Float), nullable=True
    )

    # Relationships
    arm: Mapped[ArmDB] = relationship("ArmDB", back_populates="draws", lazy="joined")
    experiment: Mapped[ExperimentDB] = relationship(
        "ExperimentDB", back_populates="draws", lazy="joined"
    )
    client: Mapped[Optional["ClientDB"]] = relationship(
        "ClientDB",
        back_populates="draws",
        lazy="joined",
        primaryjoin="and_(DrawDB.client_id==ClientDB.client_id, ExperimentDB.sticky_assignment == True)",  # noqa: E501
    )

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "draw_id": self.draw_id,
            "arm_id": self.arm_id,
            "experiment_id": self.experiment_id,
            "user_id": self.user_id,
            "client_id": self.client_id,
            "draw_datetime_utc": self.draw_datetime_utc,
            "observed_datetime_utc": self.observed_datetime_utc,
            "observation_type": self.observation_type,
            "reward": self.reward,
            "context_val": self.context_val,
        }


# --- Context model ---
class ContextDB(Base):
    """
    ORM for managing context for an experiment
    """

    __tablename__ = "contexts"

    # IDs
    context_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contextual_mabs.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )

    # Description
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=True)
    value_type: Mapped[str] = mapped_column(String(length=50), nullable=False)

    # Relationships
    experiment: Mapped[ExperimentDB] = relationship(
        "ExperimentDB", back_populates="contexts", lazy="joined"
    )

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "context_id": self.context_id,
            "name": self.name,
            "description": self.description,
            "value_type": self.value_type,
        }


# --- Client model ---
class ClientDB(Base):
    """
    ORM for managing clients for an experiment
    """

    __tablename__ = "clients"

    # IDs
    client_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda x: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiments.experiment_id"), nullable=False
    )
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspace.workspace_id"), nullable=False
    )

    # Relationships
    draws: Mapped[list[DrawDB]] = relationship(
        "DrawDB",
        back_populates="client",
        lazy="joined",
    )


# --- Notifications model ---
class NotificationsDB(Base):
    """
    Model for notifications.
    Note: if you are updating this, you should also update models in
    the background celery job
    """

    __tablename__ = "notifications"

    notification_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False
    )
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiments.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    notification_type: Mapped[EventType] = mapped_column(
        Enum(EventType), nullable=False
    )
    notification_value: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        """
        Convert the model to a dictionary
        """
        return {
            "notification_id": self.notification_id,
            "experiment_id": self.experiment_id,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "notification_value": self.notification_value,
            "is_active": self.is_active,
        }


# --- Experiments functions ---


# ---- Notifications functions ----
async def save_notifications_to_db(
    experiment_id: int,
    user_id: int,
    notifications: Notifications,
    asession: AsyncSession,
) -> list[NotificationsDB]:
    """
    Save notifications to the database
    """
    notification_records = []

    if notifications.onTrialCompletion:
        notification_row = NotificationsDB(
            experiment_id=experiment_id,
            user_id=user_id,
            notification_type=EventType.TRIALS_COMPLETED,
            notification_value=notifications.numberOfTrials,
            is_active=True,
        )
        notification_records.append(notification_row)

    if notifications.onDaysElapsed:
        notification_row = NotificationsDB(
            experiment_id=experiment_id,
            user_id=user_id,
            notification_type=EventType.DAYS_ELAPSED,
            notification_value=notifications.daysElapsed,
            is_active=True,
        )
        notification_records.append(notification_row)

    if notifications.onPercentBetter:
        notification_row = NotificationsDB(
            experiment_id=experiment_id,
            user_id=user_id,
            notification_type=EventType.PERCENTAGE_BETTER,
            notification_value=notifications.percentBetterThreshold,
            is_active=True,
        )
        notification_records.append(notification_row)

    asession.add_all(notification_records)
    await asession.commit()

    return notification_records


async def get_notifications_from_db(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> Sequence[NotificationsDB]:
    """
    Get notifications from the database
    """
    statement = (
        select(NotificationsDB)
        .where(NotificationsDB.experiment_id == experiment_id)
        .where(NotificationsDB.user_id == user_id)
    )

    return (await asession.execute(statement)).scalars().all()
