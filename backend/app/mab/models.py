from typing import Sequence

from sqlalchemy import Boolean, ForeignKey, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import Base
from .schemas import MultiArmedBandit


class MultiArmedBanditDB(Base):
    """
    ORM for managing experiments.
    """

    __tablename__ = "mabs"

    experiment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    arms: Mapped[list["ArmDB"]] = relationship(
        "ArmDB", back_populates="experiment", lazy="joined"
    )


class ArmDB(Base):
    """
    ORM for managing arms of an experiment
    """

    __tablename__ = "arms"

    arm_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mabs.experiment_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=True)

    alpha: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    beta: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    experiment: Mapped[MultiArmedBanditDB] = relationship(
        "MultiArmedBanditDB", back_populates="arms", lazy="joined"
    )


async def save_mab_to_db(
    experiment: MultiArmedBandit, asession: AsyncSession
) -> MultiArmedBanditDB:
    """
    Save the experiment to the database.
    """
    arms = [ArmDB(**arm.model_dump()) for arm in experiment.arms]
    experiment_db = MultiArmedBanditDB(
        name=experiment.name,
        description=experiment.description,
        is_active=experiment.is_active,
        arms=arms,
    )

    asession.add(experiment_db)
    await asession.commit()
    await asession.refresh(experiment_db)

    return experiment_db


async def get_all_mabs(asession: AsyncSession) -> Sequence[MultiArmedBanditDB]:
    """
    Get all the experiments from the database.
    """
    statement = select(MultiArmedBanditDB).order_by(MultiArmedBanditDB.experiment_id)

    return (await asession.execute(statement)).unique().scalars().all()


async def get_mab_by_id(
    experiment_id: int, asession: AsyncSession
) -> MultiArmedBanditDB | None:
    """
    Get the experiment by id.
    """
    return await asession.get(MultiArmedBanditDB, experiment_id)
