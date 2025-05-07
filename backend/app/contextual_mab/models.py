from datetime import datetime, timezone
from typing import Sequence

import numpy as np
from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    String,
    and_,
    delete,
    select,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import (
    ArmBaseDB,
    Base,
    DrawsBaseDB,
    ExperimentBaseDB,
    NotificationsDB,
)
from ..schemas import ObservationType
from .schemas import ContextualBandit


class ContextualBanditDB(ExperimentBaseDB):
    """
    ORM for managing contextual experiments.
    """

    __tablename__ = "contextual_mabs"

    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments_base.experiment_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    arms: Mapped[list["ContextualArmDB"]] = relationship(
        "ContextualArmDB", back_populates="experiment", lazy="joined"
    )

    contexts: Mapped[list["ContextDB"]] = relationship(
        "ContextDB", back_populates="experiment", lazy="joined"
    )

    draws: Mapped[list["ContextualDrawDB"]] = relationship(
        "ContextualDrawDB", back_populates="experiment", lazy="joined"
    )

    __mapper_args__ = {"polymorphic_identity": "contextual_mabs"}

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
            "contexts": [context.to_dict() for context in self.contexts],
            "prior_type": self.prior_type,
            "reward_type": self.reward_type,
        }


class ContextualArmDB(ArmBaseDB):
    """
    ORM for managing contextual arms of an experiment
    """

    __tablename__ = "contextual_arms"

    arm_id: Mapped[int] = mapped_column(
        ForeignKey("arms_base.arm_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    # prior variables for CMAB arms
    mu_init: Mapped[float] = mapped_column(Float, nullable=False)
    sigma_init: Mapped[float] = mapped_column(Float, nullable=False)
    mu: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    covariance: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)

    experiment: Mapped[ContextualBanditDB] = relationship(
        "ContextualBanditDB", back_populates="arms", lazy="joined"
    )
    draws: Mapped[list["ContextualDrawDB"]] = relationship(
        "ContextualDrawDB", back_populates="arm", lazy="joined"
    )

    __mapper_args__ = {"polymorphic_identity": "contextual_arms"}

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
            "covariance": self.covariance,
            "draws": [draw.to_dict() for draw in self.draws],
        }


class ContextDB(Base):
    """
    ORM for managing context for an experiment
    """

    __tablename__ = "contexts"

    context_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contextual_mabs.experiment_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=True)
    value_type: Mapped[str] = mapped_column(String(length=50), nullable=False)

    experiment: Mapped[ContextualBanditDB] = relationship(
        "ContextualBanditDB", back_populates="contexts", lazy="joined"
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


class ContextualDrawDB(DrawsBaseDB):
    """
    ORM for managing draws of an experiment
    """

    __tablename__ = "contextual_draws"

    draw_id: Mapped[str] = mapped_column(
        ForeignKey("draws_base.draw_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    context_val: Mapped[list] = mapped_column(ARRAY(Float), nullable=False)
    arm: Mapped[ContextualArmDB] = relationship(
        "ContextualArmDB", back_populates="draws", lazy="joined"
    )
    experiment: Mapped[ContextualBanditDB] = relationship(
        "ContextualBanditDB", back_populates="draws", lazy="joined"
    )

    __mapper_args__ = {"polymorphic_identity": "contextual_draws"}

    def to_dict(self) -> dict:
        """
        Convert the ORM object to a dictionary.
        """
        return {
            "draw_id": self.draw_id,
            "client_id": self.client_id,
            "draw_datetime_utc": self.draw_datetime_utc,
            "context_val": self.context_val,
            "arm_id": self.arm_id,
            "experiment_id": self.experiment_id,
            "user_id": self.user_id,
            "reward": self.reward,
            "observation_type": self.observation_type,
            "observed_datetime_utc": self.observed_datetime_utc,
        }


async def save_contextual_mab_to_db(
    experiment: ContextualBandit,
    user_id: int,
    asession: AsyncSession,
) -> ContextualBanditDB:
    """
    Save the experiment to the database.
    """
    contexts = [
        ContextDB(
            name=context.name,
            description=context.description,
            value_type=context.value_type.value,
            user_id=user_id,
        )
        for context in experiment.contexts
    ]
    arms = []
    for arm in experiment.arms:
        arms.append(
            ContextualArmDB(
                name=arm.name,
                description=arm.description,
                mu_init=arm.mu_init,
                sigma_init=arm.sigma_init,
                mu=(np.ones(len(experiment.contexts)) * arm.mu_init).tolist(),
                covariance=(
                    np.identity(len(experiment.contexts)) * arm.sigma_init
                ).tolist(),
                user_id=user_id,
                n_outcomes=arm.n_outcomes,
            )
        )

    experiment_db = ContextualBanditDB(
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
        contexts=contexts,
        prior_type=experiment.prior_type.value,
        reward_type=experiment.reward_type.value,
    )

    asession.add(experiment_db)
    await asession.commit()
    await asession.refresh(experiment_db)

    return experiment_db


async def get_all_contextual_mabs(
    user_id: int,
    asession: AsyncSession,
) -> Sequence[ContextualBanditDB]:
    """
    Get all the contextual experiments from the database.
    """
    statement = (
        select(ContextualBanditDB)
        .where(
            ContextualBanditDB.user_id == user_id,
        )
        .order_by(ContextualBanditDB.experiment_id)
    )

    return (await asession.execute(statement)).unique().scalars().all()


async def get_contextual_mab_by_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> ContextualBanditDB | None:
    """
    Get the contextual experiment by id.
    """
    result = await asession.execute(
        select(ContextualBanditDB)
        .where(ContextualBanditDB.user_id == user_id)
        .where(ContextualBanditDB.experiment_id == experiment_id)
    )

    return result.unique().scalar_one_or_none()


async def delete_contextual_mab_by_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> None:
    """
    Delete the contextual experiment by id.
    """
    await asession.execute(
        delete(NotificationsDB)
        .where(NotificationsDB.user_id == user_id)
        .where(NotificationsDB.experiment_id == experiment_id)
    )

    await asession.execute(
        delete(ContextualDrawDB).where(
            and_(
                ContextualDrawDB.user_id == DrawsBaseDB.user_id,
                ContextualDrawDB.user_id == user_id,
                ContextualDrawDB.experiment_id == experiment_id,
            )
        )
    )

    await asession.execute(
        delete(ContextDB)
        .where(ContextDB.user_id == user_id)
        .where(ContextDB.experiment_id == experiment_id)
    )

    await asession.execute(
        delete(ContextualArmDB).where(
            and_(
                ContextualArmDB.user_id == user_id,
                ContextualArmDB.experiment_id == experiment_id,
            )
        )
    )

    await asession.execute(
        delete(ContextualBanditDB).where(
            and_(
                ContextualBanditDB.user_id == user_id,
                ContextualBanditDB.experiment_id == experiment_id,
                ContextualBanditDB.experiment_id == ExperimentBaseDB.experiment_id,
            )
        )
    )
    await asession.commit()
    return None


async def save_contextual_obs_to_db(
    draw: ContextualDrawDB,
    reward: float,
    asession: AsyncSession,
    observation_type: ObservationType,
) -> ContextualDrawDB:
    """
    Save the observation to the database.
    """
    draw.reward = reward
    draw.observed_datetime_utc = datetime.now(timezone.utc)
    draw.observation_type = observation_type  # Remove .value, pass enum directly

    await asession.commit()
    await asession.refresh(draw)

    return draw


async def get_contextual_obs_by_experiment_arm_id(
    experiment_id: int, arm_id: int, user_id: int, asession: AsyncSession
) -> Sequence[ContextualDrawDB]:
    """
    Get the rewards for an arm of an experiment.
    """
    statement = (
        select(ContextualDrawDB)
        .where(ContextualDrawDB.user_id == user_id)
        .where(ContextualDrawDB.experiment_id == experiment_id)
        .where(ContextualDrawDB.reward.is_not(None))
        .where(ContextualDrawDB.arm_id == arm_id)
        .order_by(ContextualDrawDB.observed_datetime_utc)
    )

    return (await asession.execute(statement)).unique().scalars().all()


async def get_all_contextual_obs_by_experiment_id(
    experiment_id: int, user_id: int, asession: AsyncSession
) -> Sequence[ContextualDrawDB]:
    """
    Get the rewards for an experiment.
    """
    statement = (
        select(ContextualDrawDB)
        .where(ContextualDrawDB.user_id == user_id)
        .where(ContextualDrawDB.reward.is_not(None))
        .where(ContextualDrawDB.experiment_id == experiment_id)
        .order_by(ContextualDrawDB.observed_datetime_utc)
    )

    return (await asession.execute(statement)).unique().scalars().all()


async def get_draw_by_id(
    draw_id: str, user_id: int, asession: AsyncSession
) -> ContextualDrawDB | None:
    """
    Get the draw by id.
    """
    statement = (
        select(ContextualDrawDB)
        .where(ContextualDrawDB.user_id == user_id)
        .where(ContextualDrawDB.draw_id == draw_id)
    )
    result = await asession.execute(statement)

    return result.unique().scalar_one_or_none()


async def get_draw_by_client_id(
    client_id: str, user_id: int, asession: AsyncSession
) -> ContextualDrawDB | None:
    """
    Get the draw by id.
    """
    statement = (
        select(ContextualDrawDB)
        .where(ContextualDrawDB.user_id == user_id)
        .where(ContextualDrawDB.client_id.is_not(None))
        .where(ContextualDrawDB.client_id == client_id)
    )
    result = await asession.execute(statement)

    return result.unique().scalars().first()


async def save_draw_to_db(
    experiment_id: int,
    arm_id: int,
    context_val: list[float],
    draw_id: str,
    client_id: str | None,
    user_id: int,
    asession: AsyncSession,
) -> ContextualDrawDB:
    """
    Save the draw to the database.
    """
    draw_db = ContextualDrawDB(
        draw_id=draw_id,
        client_id=client_id,
        arm_id=arm_id,
        experiment_id=experiment_id,
        user_id=user_id,
        context_val=context_val,
        draw_datetime_utc=datetime.now(timezone.utc),
    )

    asession.add(draw_db)
    await asession.commit()
    await asession.refresh(draw_db)

    return draw_db
