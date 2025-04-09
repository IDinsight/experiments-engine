from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    and_,
    delete,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import (
    ArmBaseDB,
    ExperimentBaseDB,
    NotificationsDB,
    ObservationsBaseDB,
)
from .schemas import MABObservation, MultiArmedBandit


class MultiArmedBanditDB(ExperimentBaseDB):
    """
    ORM for managing experiments.
    """

    __tablename__ = "mabs"

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments_base.experiment_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    arms: Mapped[list["MABArmDB"]] = relationship(
        "MABArmDB", back_populates="experiment", lazy="joined"
    )

    observations: Mapped[list["MABObservationDB"]] = relationship(
        "MABObservationDB", back_populates="experiment", lazy="joined"
    )

    __mapper_args__ = {"polymorphic_identity": "mabs"}

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "experiment_id": self.experiment_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "created_datetime_utc": self.created_datetime_utc,
            "is_active": self.is_active,
            "n_trials": self.n_trials,
            "arms": [arm.to_dict() for arm in self.arms],
            "prior_type": self.prior_type,
            "reward_type": self.reward_type,
        }


class MABArmDB(ArmBaseDB):
    """
    ORM for managing arms of an experiment
    """

    __tablename__ = "mab_arms"

    arm_id: Mapped[int] = mapped_column(
        ForeignKey("arms_base.arm_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    # prior variables for MAB arms
    alpha: Mapped[float] = mapped_column(Float, nullable=True)
    beta: Mapped[float] = mapped_column(Float, nullable=True)
    mu: Mapped[float] = mapped_column(Float, nullable=True)
    sigma: Mapped[float] = mapped_column(Float, nullable=True)
    n_outcomes: Mapped[int] = mapped_column(Integer, nullable=False)
    experiment: Mapped[MultiArmedBanditDB] = relationship(
        "MultiArmedBanditDB", back_populates="arms", lazy="joined"
    )

    observations: Mapped[list["MABObservationDB"]] = relationship(
        "MABObservationDB", back_populates="arm", lazy="joined"
    )

    __mapper_args__ = {"polymorphic_identity": "mab_arms"}

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "arm_id": self.arm_id,
            "name": self.name,
            "description": self.description,
            "alpha": self.alpha,
            "beta": self.beta,
            "mu": self.mu,
            "sigma": self.sigma,
            "observations": [obs.to_dict() for obs in self.observations],
        }


class MABObservationDB(ObservationsBaseDB):
    """
    ORM for managing observations of an experiment
    """

    __tablename__ = "mab_observations"

    observation_id: Mapped[int] = mapped_column(
        ForeignKey("observations_base.observation_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    reward: Mapped[float] = mapped_column(Float, nullable=False)

    arm: Mapped[MABArmDB] = relationship(
        "MABArmDB", back_populates="observations", lazy="joined"
    )
    experiment: Mapped[MultiArmedBanditDB] = relationship(
        "MultiArmedBanditDB", back_populates="observations", lazy="joined"
    )
    __mapper_args__ = {"polymorphic_identity": "mab_observations"}

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "observation_id": self.observation_id,
            "reward": self.reward,
            "observed_datetime_utc": self.observed_datetime_utc,
        }


async def save_mab_to_db(
    experiment: MultiArmedBandit,
    user_id: int,
    asession: AsyncSession,
) -> MultiArmedBanditDB:
    """
    Save the experiment to the database.
    """
    arms = [
        MABArmDB(
            **arm.model_dump(),
            user_id=user_id,
        )
        for arm in experiment.arms
    ]
    experiment_db = MultiArmedBanditDB(
        name=experiment.name,
        description=experiment.description,
        user_id=user_id,
        is_active=experiment.is_active,
        created_datetime_utc=datetime.now(timezone.utc),
        n_trials=0,
        arms=arms,
        prior_type=experiment.prior_type.value,
        reward_type=experiment.reward_type.value,
    )

    asession.add(experiment_db)
    await asession.commit()
    await asession.refresh(experiment_db)

    return experiment_db


async def get_all_mabs(
    user_id: int,
    asession: AsyncSession,
) -> Sequence[MultiArmedBanditDB]:
    """
    Get all the experiments from the database.
    """
    statement = (
        select(MultiArmedBanditDB)
        .where(
            MultiArmedBanditDB.user_id == user_id,
        )
        .order_by(MultiArmedBanditDB.experiment_id)
    )

    return (await asession.execute(statement)).unique().scalars().all()


async def get_mab_by_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> MultiArmedBanditDB | None:
    """
    Get the experiment by id.
    """
    result = await asession.execute(
        select(MultiArmedBanditDB)
        .where(MultiArmedBanditDB.user_id == user_id)
        .where(MultiArmedBanditDB.experiment_id == experiment_id)
    )

    return result.unique().scalar_one_or_none()


async def delete_mab_by_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> None:
    """
    Delete the experiment by id.
    """
    await asession.execute(
        delete(NotificationsDB)
        .where(NotificationsDB.user_id == user_id)
        .where(NotificationsDB.experiment_id == experiment_id)
    )

    await asession.execute(
        delete(MABObservationDB).where(
            and_(
                MABObservationDB.observation_id == ObservationsBaseDB.observation_id,
                ObservationsBaseDB.user_id == user_id,
                ObservationsBaseDB.experiment_id == experiment_id,
            )
        )
    )
    await asession.execute(
        delete(MABArmDB).where(
            and_(
                MABArmDB.arm_id == ArmBaseDB.arm_id,
                ArmBaseDB.user_id == user_id,
                ArmBaseDB.experiment_id == experiment_id,
            )
        )
    )
    await asession.execute(
        delete(MultiArmedBanditDB).where(
            and_(
                MultiArmedBanditDB.experiment_id == experiment_id,
                MultiArmedBanditDB.experiment_id == ExperimentBaseDB.experiment_id,
                MultiArmedBanditDB.user_id == user_id,
            )
        )
    )
    await asession.commit()
    return None


async def save_observation_to_db(
    observation: MABObservation,
    user_id: int,
    asession: AsyncSession,
) -> MABObservationDB:
    """
    Save the observation to the database.
    """
    observation_db = MABObservationDB(
        **observation.model_dump(),
        user_id=user_id,
        observed_datetime_utc=datetime.now(timezone.utc),
    )

    asession.add(observation_db)
    await asession.commit()
    await asession.refresh(observation_db)

    return observation_db


async def get_rewards_by_experiment_arm_id(
    experiment_id: int, arm_id: int, user_id: int, asession: AsyncSession
) -> Sequence[MABObservationDB]:
    """
    Get the observations for the experiment and arm.
    """
    statement = (
        select(MABObservationDB)
        .where(MABObservationDB.user_id == user_id)
        .where(MABObservationDB.experiment_id == experiment_id)
        .where(MABObservationDB.arm_id == arm_id)
        .order_by(MABObservationDB.observed_datetime_utc)
    )

    return (await asession.execute(statement)).unique().scalars().all()


async def get_all_rewards_by_experiment_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> Sequence[MABObservationDB]:
    """
    Get the observations for the experiment and arm.
    """
    statement = (
        select(MABObservationDB)
        .where(MABObservationDB.user_id == user_id)
        .where(MABObservationDB.experiment_id == experiment_id)
        .order_by(MABObservationDB.observed_datetime_utc)
    )

    return (await asession.execute(statement)).unique().scalars().all()
