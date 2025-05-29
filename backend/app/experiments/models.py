import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

import numpy as np
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    delete,
    select,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import Base
from .schemas import (
    AutoFailUnitType,
    EventType,
    Experiment,
    Notifications,
    ObservationType,
)


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
        primaryjoin="and_(ExperimentDB.experiment_id==ContextDB.experiment_id,"
        + "ExperimentDB.exp_type=='cmab')",
    )

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
    def context_list(self) -> list["ContextDB"] | list[None]:
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
                [context.to_dict() for context in self.context_list if context]
                if len(self.context_list) > 0
                else []
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
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspace.workspace_id"), nullable=False
    )
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiments.experiment_id"), nullable=False
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
            "n_outcomes": self.n_outcomes,
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
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspace.workspace_id"), nullable=False
    )
    client_id: Mapped[str] = mapped_column(
        String(length=36), ForeignKey("clients.client_id"), nullable=False
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
    context_val: Mapped[Optional[list[float]]] = mapped_column(
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

    __tablename__ = "context"

    # IDs
    context_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiments.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspace.workspace_id"), nullable=False
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
    experiment: Mapped[ExperimentDB] = relationship(
        "ExperimentDB",
        back_populates="clients",
        lazy="joined",
        primaryjoin="and_(ClientDB.experiment_id==ExperimentDB.experiment_id,"
        + "ExperimentDB.sticky_assignment == True)",
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
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspace.workspace_id"), nullable=False
    )
    notification_type: Mapped[EventType] = mapped_column(
        Enum(EventType), nullable=False
    )
    notification_value: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        """
        Convert the model to a dictionary.
        """
        return {
            "notification_id": self.notification_id,
            "experiment_id": self.experiment_id,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "notification_value": self.notification_value,
            "is_active": self.is_active,
        }


# --- ORM functions ---


# ---- Notifications functions ----
async def save_notifications_to_db(
    experiment_id: int,
    user_id: int,
    workspace_id: int,
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
            workspace_id=workspace_id,
            notification_type=EventType.TRIALS_COMPLETED,
            notification_value=notifications.numberOfTrials,
            is_active=True,
        )
        notification_records.append(notification_row)

    if notifications.onDaysElapsed:
        notification_row = NotificationsDB(
            experiment_id=experiment_id,
            user_id=user_id,
            workspace_id=workspace_id,
            notification_type=EventType.DAYS_ELAPSED,
            notification_value=notifications.daysElapsed,
            is_active=True,
        )
        notification_records.append(notification_row)

    if notifications.onPercentBetter:
        notification_row = NotificationsDB(
            experiment_id=experiment_id,
            user_id=user_id,
            workspace_id=workspace_id,
            notification_type=EventType.PERCENTAGE_BETTER,
            notification_value=notifications.percentBetterThreshold,
            is_active=True,
        )
        notification_records.append(notification_row)

    asession.add_all(notification_records)
    await asession.commit()

    return notification_records


async def get_notifications_from_db(
    experiment_id: int, user_id: int, workspace_id: int, asession: AsyncSession
) -> Sequence[NotificationsDB]:
    """
    Get notifications from the database
    """
    statement = (
        select(NotificationsDB)
        .where(NotificationsDB.experiment_id == experiment_id)
        .where(NotificationsDB.user_id == user_id)
        .where(NotificationsDB.workspace_id == workspace_id)
    )

    return (await asession.execute(statement)).scalars().all()


# --- Experiment functions ---
async def save_experiment_to_db(
    experiment: Experiment,
    user_id: int,
    workspace_id: int,
    asession: AsyncSession,
) -> ExperimentDB:
    """
    Save an experiment to the database.
    """
    len_contexts = len(experiment.contexts) if experiment.contexts else 1
    contexts = []

    arms = [
        ArmDB(
            user_id=user_id,
            workspace_id=workspace_id,
            # description
            name=arm.name,
            description=arm.description,
            n_outcomes=0,
            # prior variables
            mu_init=arm.mu_init,
            sigma_init=arm.sigma_init,
            mu=[arm.mu_init] * len_contexts,
            covariance=(
                (np.identity(len_contexts) * arm.sigma_init**2).tolist()
                if arm.sigma_init
                else [[None]]
            ),
            alpha_init=arm.alpha_init,
            beta_init=arm.beta_init,
            alpha=arm.alpha_init,
            beta=arm.beta_init,
        )
        for arm in experiment.arms
    ]
    if experiment.contexts and len_contexts > 0:
        contexts = [
            ContextDB(
                user_id=user_id,
                workspace_id=workspace_id,
                name=context.name,
                description=context.description,
                value_type=context.value_type,
            )
            for context in experiment.contexts
        ]

    experiment_db = ExperimentDB(
        user_id=user_id,
        workspace_id=workspace_id,
        # description
        name=experiment.name,
        description=experiment.description,
        is_active=experiment.is_active,
        # assignments config
        sticky_assignment=experiment.sticky_assignment,
        auto_fail=experiment.auto_fail,
        auto_fail_value=experiment.auto_fail_value,
        auto_fail_unit=experiment.auto_fail_unit,
        # experiment config
        exp_type=experiment.exp_type,
        prior_type=experiment.prior_type,
        reward_type=experiment.reward_type,
        # datetime
        created_datetime_utc=datetime.now(timezone.utc),
        n_trials=0,
        # relationships
        arms=arms,
        contexts=contexts,
    )

    asession.add(experiment_db)
    await asession.commit()
    await asession.refresh(experiment_db)

    return experiment_db


async def get_all_experiments_from_db(
    workspace_id: int, asession: AsyncSession
) -> Sequence[ExperimentDB]:
    """
    Get all experiments for a given workspace.
    """
    statement = (
        select(ExperimentDB)
        .where(ExperimentDB.workspace_id == workspace_id)
        .order_by(ExperimentDB.created_datetime_utc.desc())
    )
    return (await asession.execute(statement)).unique().scalars().all()


async def get_all_experiment_types_from_db(
    workspace_id: int, experiment_type: str, asession: AsyncSession
) -> Sequence[ExperimentDB]:
    """
    Get all experiments for a given workspace.
    """
    statement = (
        select(ExperimentDB)
        .where(ExperimentDB.workspace_id == workspace_id)
        .where(ExperimentDB.exp_type == experiment_type)
        .order_by(ExperimentDB.created_datetime_utc.desc())
    )
    return (await asession.execute(statement)).unique().scalars().all()


async def get_experiment_by_id_from_db(
    workspace_id: int, experiment_id: int, asession: AsyncSession
) -> ExperimentDB | None:
    """
    Get all experiments for a given workspace.
    """
    statement = (
        select(ExperimentDB)
        .where(ExperimentDB.workspace_id == workspace_id)
        .where(ExperimentDB.experiment_id == experiment_id)
    )
    return (await asession.execute(statement)).unique().scalars().one_or_none()


async def delete_experiment_by_id_from_db(
    workspace_id: int, experiment_id: int, asession: AsyncSession
) -> None:
    """
    Delete an experiment by ID for a given workspace.
    """
    await asession.execute(
        delete(NotificationsDB)
        .where(NotificationsDB.workspace_id == workspace_id)
        .where(NotificationsDB.experiment_id == experiment_id)
    )

    await asession.execute(
        delete(ContextDB)
        .where(ContextDB.workspace_id == workspace_id)
        .where(ContextDB.experiment_id == experiment_id)
    )

    await asession.execute(
        delete(ClientDB)
        .where(ClientDB.workspace_id == workspace_id)
        .where(ClientDB.experiment_id == experiment_id)
    )

    await asession.execute(
        delete(ArmDB)
        .where(ArmDB.workspace_id == workspace_id)
        .where(ArmDB.experiment_id == experiment_id)
    )
    await asession.execute(
        delete(DrawDB)
        .where(DrawDB.workspace_id == workspace_id)
        .where(DrawDB.experiment_id == experiment_id)
    )

    await asession.execute(
        delete(ExperimentDB)
        .where(ExperimentDB.workspace_id == workspace_id)
        .where(ExperimentDB.experiment_id == experiment_id)
    )

    await asession.commit()
    return None


# Draw functions
async def get_draw_by_id(draw_id: str, asession: AsyncSession) -> DrawDB | None:
    """
    Get a draw by its ID, which should be unique across the system.
    """
    statement = select(DrawDB).where(DrawDB.draw_id == draw_id)
    result = await asession.execute(statement)

    return result.unique().scalar_one_or_none()


async def save_draw_to_db(
    draw_id: str,
    arm_id: int,
    experiment_id: int,
    user_id: int | None,
    workspace_id: int,
    client_id: str,
    context: list[float] | None,
    asession: AsyncSession,
) -> DrawDB:
    """
    Save a draw to the database.
    """
    if not user_id:
        experiment = await get_experiment_by_id_from_db(
            experiment_id=experiment_id, workspace_id=workspace_id, asession=asession
        )
        if not experiment:
            raise ValueError(
                f"Experiment with id {experiment_id} not found for the given ID."
            )
        experiment_id = experiment.experiment_id
    draw = DrawDB(
        draw_id=draw_id,
        arm_id=arm_id,
        experiment_id=experiment_id,
        user_id=user_id,
        workspace_id=workspace_id,
        client_id=client_id,
        draw_datetime_utc=datetime.now(timezone.utc),
        context_val=context,
    )
    asession.add(draw)
    await asession.commit()
    await asession.refresh(draw)

    return draw
