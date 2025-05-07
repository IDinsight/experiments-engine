from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import (
    Boolean,
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
from .schemas import BayesianAB


class BayesianABDB(ExperimentBaseDB):
    """
    ORM for managing experiments.
    """

    __tablename__ = "bayes_ab_experiments"

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments_base.experiment_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    arms: Mapped[list["BayesianABArmDB"]] = relationship(
        "BayesianABArmDB", back_populates="experiment", lazy="selectin"
    )

    draws: Mapped[list["BayesianABDrawDB"]] = relationship(
        "BayesianABDrawDB", back_populates="experiment", lazy="joined"
    )

    __mapper_args__ = {"polymorphic_identity": "bayes_ab_experiments"}

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


class BayesianABArmDB(ArmBaseDB):
    """
    ORM for managing arms.
    """

    __tablename__ = "bayes_ab_arms"

    arm_id: Mapped[int] = mapped_column(
        ForeignKey("arms_base.arm_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    # prior variables for AB arms
    mu_init: Mapped[float] = mapped_column(Float, nullable=False)
    sigma_init: Mapped[float] = mapped_column(Float, nullable=False)
    mu: Mapped[float] = mapped_column(Float, nullable=False)
    sigma: Mapped[float] = mapped_column(Float, nullable=False)
    is_treatment_arm: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    experiment: Mapped[BayesianABDB] = relationship(
        "BayesianABDB", back_populates="arms", lazy="joined"
    )
    draws: Mapped[list["BayesianABDrawDB"]] = relationship(
        "BayesianABDrawDB", back_populates="arm", lazy="joined"
    )

    __mapper_args__ = {"polymorphic_identity": "bayes_ab_arms"}

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "arm_id": self.arm_id,
            "name": self.name,
            "description": self.description,
            "mu_init": self.mu_init,
            "sigma_init": self.sigma_init,
            "mu": self.mu,
            "sigma": self.sigma,
            "is_treatment_arm": self.is_treatment_arm,
            "draws": [draw.to_dict() for draw in self.draws],
        }


class BayesianABDrawDB(DrawsBaseDB):
    """
    ORM for managing draws of AB experiment.
    """

    __tablename__ = "bayes_ab_draws"

    draw_id: Mapped[str] = mapped_column(  # Changed from int to str
        ForeignKey("draws_base.draw_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    arm: Mapped[BayesianABArmDB] = relationship(
        "BayesianABArmDB", back_populates="draws", lazy="joined"
    )
    experiment: Mapped[BayesianABDB] = relationship(
        "BayesianABDB", back_populates="draws", lazy="joined"
    )

    __mapper_args__ = {"polymorphic_identity": "bayes_ab_draws"}

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "draw_id": self.draw_id,
            "client_id": self.client_id,
            "draw_datetime_utc": self.draw_datetime_utc,
            "arm_id": self.arm_id,
            "experiment_id": self.experiment_id,
            "user_id": self.user_id,
            "reward": self.reward,
            "observation_type": self.observation_type,
            "observed_datetime_utc": self.observed_datetime_utc,
        }


async def save_bayes_ab_to_db(
    ab_experiment: BayesianAB,
    user_id: int,
    asession: AsyncSession,
) -> BayesianABDB:
    """
    Save the A/B experiment to the database.
    """
    arms = [
        BayesianABArmDB(
            name=arm.name,
            description=arm.description,
            mu_init=arm.mu_init,
            sigma_init=arm.sigma_init,
            n_outcomes=arm.n_outcomes,
            is_treatment_arm=arm.is_treatment_arm,
            mu=arm.mu_init,
            sigma=arm.sigma_init,
            user_id=user_id,
        )
        for arm in ab_experiment.arms
    ]

    bayes_ab_db = BayesianABDB(
        name=ab_experiment.name,
        description=ab_experiment.description,
        user_id=user_id,
        is_active=ab_experiment.is_active,
        created_datetime_utc=datetime.now(timezone.utc),
        n_trials=0,
        arms=arms,
        sticky_assignment=ab_experiment.sticky_assignment,
        auto_fail=ab_experiment.auto_fail,
        auto_fail_value=ab_experiment.auto_fail_value,
        auto_fail_unit=ab_experiment.auto_fail_unit,
        prior_type=ab_experiment.prior_type.value,
        reward_type=ab_experiment.reward_type.value,
    )

    asession.add(bayes_ab_db)
    await asession.commit()
    await asession.refresh(bayes_ab_db)

    return bayes_ab_db


async def get_all_bayes_ab_experiments(
    user_id: int,
    asession: AsyncSession,
) -> Sequence[BayesianABDB]:
    """
    Get all the A/B experiments from the database.
    """
    stmt = (
        select(BayesianABDB)
        .where(BayesianABDB.user_id == user_id)
        .order_by(BayesianABDB.experiment_id)
    )
    result = await asession.execute(stmt)
    return result.unique().scalars().all()


async def get_bayes_ab_experiment_by_id(
    experiment_id: int,
    user_id: int,
    asession: AsyncSession,
) -> BayesianABDB | None:
    """
    Get the A/B experiment by id.
    """
    stmt = select(BayesianABDB).where(
        and_(
            BayesianABDB.user_id == user_id,
            BayesianABDB.experiment_id == experiment_id,
        )
    )
    result = await asession.execute(stmt)
    return result.unique().scalar_one_or_none()


async def delete_bayes_ab_experiment_by_id(
    experiment_id: int,
    user_id: int,
    asession: AsyncSession,
) -> None:
    """
    Delete the A/B experiment by id.
    """
    stmt = delete(BayesianABDB).where(
        and_(
            BayesianABDB.user_id == user_id,
            BayesianABDB.experiment_id == experiment_id,
            BayesianABDB.experiment_id == ExperimentBaseDB.experiment_id,
        )
    )
    await asession.execute(stmt)

    stmt = delete(NotificationsDB).where(
        and_(
            NotificationsDB.user_id == user_id,
            NotificationsDB.experiment_id == experiment_id,
        )
    )
    await asession.execute(stmt)

    stmt = delete(BayesianABDrawDB).where(
        and_(
            BayesianABDrawDB.draw_id == DrawsBaseDB.draw_id,
            DrawsBaseDB.user_id == user_id,
            BayesianABDrawDB.experiment_id == experiment_id,
        )
    )
    await asession.execute(stmt)

    stmt = delete(BayesianABArmDB).where(
        and_(
            BayesianABArmDB.arm_id == ArmBaseDB.arm_id,
            BayesianABArmDB.user_id == user_id,
            BayesianABArmDB.experiment_id == experiment_id,
        )
    )
    await asession.execute(stmt)

    await asession.commit()
    return None


async def save_bayes_ab_observation_to_db(
    draw: BayesianABDrawDB,
    reward: float,
    asession: AsyncSession,
    observation_type: ObservationType = ObservationType.AUTO,
) -> BayesianABDrawDB:
    """
    Save the A/B observation to the database.
    """
    draw.reward = reward
    draw.observed_datetime_utc = datetime.now(timezone.utc)
    draw.observation_type = observation_type

    await asession.commit()
    await asession.refresh(draw)

    return draw


async def save_bayes_ab_draw_to_db(
    experiment_id: int,
    arm_id: int,
    draw_id: str,
    client_id: str | None,
    user_id: int,
    asession: AsyncSession,
) -> BayesianABDrawDB:
    """
    Save a draw to the database
    """

    draw_datetime_utc: datetime = datetime.now(timezone.utc)

    draw = BayesianABDrawDB(
        draw_id=draw_id,
        client_id=client_id,
        experiment_id=experiment_id,
        user_id=user_id,
        arm_id=arm_id,
        draw_datetime_utc=draw_datetime_utc,
    )

    asession.add(draw)
    await asession.commit()
    await asession.refresh(draw)

    return draw


async def get_bayes_ab_obs_by_experiment_arm_id(
    experiment_id: int,
    arm_id: int,
    user_id: int,
    asession: AsyncSession,
) -> Sequence[BayesianABDrawDB]:
    """
    Get the observations of the A/B experiment by id.
    """
    stmt = (
        select(BayesianABDrawDB)
        .where(
            and_(
                BayesianABDrawDB.user_id == user_id,
                BayesianABDrawDB.experiment_id == experiment_id,
                BayesianABDrawDB.arm_id == arm_id,
                BayesianABDrawDB.reward.is_not(None),
            )
        )
        .order_by(BayesianABDrawDB.observed_datetime_utc)
    )

    result = await asession.execute(stmt)
    return result.unique().scalars().all()


async def get_bayes_ab_obs_by_experiment_id(
    experiment_id: int,
    user_id: int,
    asession: AsyncSession,
) -> Sequence[BayesianABDrawDB]:
    """
    Get the observations of the A/B experiment by id.
    """
    stmt = (
        select(BayesianABDrawDB)
        .where(
            and_(
                BayesianABDrawDB.user_id == user_id,
                BayesianABDrawDB.experiment_id == experiment_id,
                BayesianABDrawDB.reward.is_not(None),
            )
        )
        .order_by(BayesianABDrawDB.observed_datetime_utc)
    )

    result = await asession.execute(stmt)
    return result.unique().scalars().all()


async def get_bayes_ab_draw_by_id(
    draw_id: str, user_id: int, asession: AsyncSession
) -> BayesianABDrawDB | None:
    """
    Get a draw by its ID
    """
    statement = (
        select(BayesianABDrawDB)
        .where(BayesianABDrawDB.draw_id == draw_id)
        .where(BayesianABDrawDB.user_id == user_id)
    )
    result = await asession.execute(statement)

    return result.unique().scalar_one_or_none()


async def get_bayes_ab_draw_by_client_id(
    client_id: str, user_id: int, asession: AsyncSession
) -> BayesianABDrawDB | None:
    """
    Get a draw by its ID
    """
    statement = (
        select(BayesianABDrawDB)
        .where(BayesianABDrawDB.client_id == client_id)
        .where(BayesianABDrawDB.client_id.is_not(None))
        .where(BayesianABDrawDB.user_id == user_id)
    )
    result = await asession.execute(statement)

    return result.unique().scalars().first()
