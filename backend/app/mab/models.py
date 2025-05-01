from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import (
    Float,
    ForeignKey,
    and_,
    delete,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import (
    ArmBaseDB,
    DrawsBaseDB,
    ExperimentBaseDB,
    NotificationsDB,
)
from ..schemas import ObservationType
from .schemas import MultiArmedBandit


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

    draws: Mapped[list["MABDrawDB"]] = relationship(
        "MABDrawDB", back_populates="experiment", lazy="joined"
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
            "sticky_assignment": self.sticky_assignment,
            "auto_fail": self.auto_fail,
            "auto_fail_value": self.auto_fail_value,
            "auto_fail_unit": self.auto_fail_unit,
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
    alpha_init: Mapped[float] = mapped_column(Float, nullable=True)
    beta_init: Mapped[float] = mapped_column(Float, nullable=True)
    mu_init: Mapped[float] = mapped_column(Float, nullable=True)
    sigma_init: Mapped[float] = mapped_column(Float, nullable=True)
    experiment: Mapped[MultiArmedBanditDB] = relationship(
        "MultiArmedBanditDB", back_populates="arms", lazy="joined"
    )

    draws: Mapped[list["MABDrawDB"]] = relationship(
        "MABDrawDB", back_populates="arm", lazy="joined"
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
            "alpha_init": self.alpha_init,
            "beta_init": self.beta_init,
            "mu_init": self.mu_init,
            "sigma_init": self.sigma_init,
            "draws": [draw.to_dict() for draw in self.draws],
        }


class MABDrawDB(DrawsBaseDB):
    """
    ORM for managing draws of an experiment
    """

    __tablename__ = "mab_draws"

    draw_id: Mapped[str] = mapped_column(
        ForeignKey("draws_base.draw_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    arm: Mapped[MABArmDB] = relationship(
        "MABArmDB", back_populates="draws", lazy="joined"
    )
    experiment: Mapped[MultiArmedBanditDB] = relationship(
        "MultiArmedBanditDB", back_populates="draws", lazy="joined"
    )

    __mapper_args__ = {"polymorphic_identity": "mab_draws"}

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "draw_id": self.draw_id,
            "draw_datetime_utc": self.draw_datetime_utc,
            "arm_id": self.arm_id,
            "experiment_id": self.experiment_id,
            "user_id": self.user_id,
            "reward": self.reward,
            "observation_type": self.observation_type,
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
            name=arm.name,
            description=arm.description,
            alpha_init=arm.alpha_init,
            beta_init=arm.beta_init,
            mu_init=arm.mu_init,
            sigma_init=arm.sigma_init,
            n_outcomes=arm.n_outcomes,
            alpha=arm.alpha_init,
            beta=arm.beta_init,
            mu=arm.mu_init,
            sigma=arm.sigma_init,
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
        sticky_assignment=experiment.sticky_assignment,
        auto_fail=experiment.auto_fail,
        auto_fail_value=experiment.auto_fail_value,
        auto_fail_unit=experiment.auto_fail_unit,
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
        delete(MABDrawDB).where(
            and_(
                MABDrawDB.draw_id == DrawsBaseDB.draw_id,
                DrawsBaseDB.user_id == user_id,
                DrawsBaseDB.experiment_id == experiment_id,
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


async def get_obs_by_experiment_arm_id(
    experiment_id: int, arm_id: int, user_id: int, asession: AsyncSession
) -> Sequence[MABDrawDB]:
    """
    Get the observations for the experiment and arm.
    """
    statement = (
        select(MABDrawDB)
        .where(MABDrawDB.user_id == user_id)
        .where(MABDrawDB.experiment_id == experiment_id)
        .where(MABDrawDB.reward.is_not(None))
        .where(MABDrawDB.arm_id == arm_id)
        .order_by(MABDrawDB.observed_datetime_utc)
    )

    return (await asession.execute(statement)).unique().scalars().all()


async def get_all_obs_by_experiment_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> Sequence[MABDrawDB]:
    """
    Get the observations for the experiment and arm.
    """
    statement = (
        select(MABDrawDB)
        .where(MABDrawDB.user_id == user_id)
        .where(MABDrawDB.experiment_id == experiment_id)
        .where(MABDrawDB.reward.is_not(None))
        .order_by(MABDrawDB.observed_datetime_utc)
    )

    return (await asession.execute(statement)).unique().scalars().all()


async def get_draw_by_id(
    draw_id: str, user_id: int, asession: AsyncSession
) -> MABDrawDB | None:
    """
    Get a draw by its ID
    """
    statement = (
        select(MABDrawDB)
        .where(MABDrawDB.draw_id == draw_id)
        .where(MABDrawDB.user_id == user_id)
    )
    result = await asession.execute(statement)

    return result.unique().scalar_one_or_none()


async def save_draw_to_db(
    experiment_id: int,
    arm_id: int,
    draw_id: str,
    user_id: int,
    asession: AsyncSession,
) -> MABDrawDB:
    """
    Save a draw to the database
    """

    draw_datetime_utc: datetime = datetime.now(timezone.utc)

    draw = MABDrawDB(
        draw_id=draw_id,
        experiment_id=experiment_id,
        user_id=user_id,
        arm_id=arm_id,
        draw_datetime_utc=draw_datetime_utc,
    )

    asession.add(draw)
    await asession.commit()
    await asession.refresh(draw)

    return draw


async def save_observation_to_db(
    draw: MABDrawDB,
    reward: float,
    asession: AsyncSession,
    observation_type: ObservationType = ObservationType.AUTO,
) -> MABDrawDB:
    """
    Save an observation to the database
    """

    draw.reward = reward
    draw.observed_datetime_utc = datetime.now(timezone.utc)
    draw.observation_type = observation_type
    asession.add(draw)
    await asession.commit()
    await asession.refresh(draw)

    return draw
