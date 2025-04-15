from datetime import datetime
from typing import Sequence

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .schemas import EventType, Notifications


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass


class ExperimentBaseDB(Base):
    """
    Base model for experiments.
    """

    __tablename__ = "experiments_base"

    experiment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    exp_type: Mapped[str] = mapped_column(String(length=50), nullable=False)
    prior_type: Mapped[str] = mapped_column(String(length=50), nullable=False)
    reward_type: Mapped[str] = mapped_column(String(length=50), nullable=False)

    created_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    n_trials: Mapped[int] = mapped_column(Integer, nullable=False)
    last_trial_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
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


class ArmBaseDB(Base):
    """
    Base model for arms.
    """

    __tablename__ = "arms_base"

    arm_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiments_base.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=False)
    arm_type: Mapped[str] = mapped_column(String(length=50), nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "arm",
        "polymorphic_on": "arm_type",
    }


class ObservationsBaseDB(Base):
    """
    Base model for observations.
    """

    __tablename__ = "observations_base"

    observation_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False
    )
    arm_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("arms_base.arm_id"), nullable=False
    )
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiments_base.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    observed_datetime_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    obs_type: Mapped[str] = mapped_column(String(length=50), nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "observation",
        "polymorphic_on": "obs_type",
    }


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
        Integer, ForeignKey("experiments_base.experiment_id"), nullable=False
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
