from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import MultiArmedBandit
from ..models import Base


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

    alpha_prior: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    beta_prior: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

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


async def get_mab_by_id(
    experiment_id: int, asession: AsyncSession
) -> MultiArmedBanditDB:
    """
    Get the experiment by id.
    """
    return await asession.get_one(MultiArmedBanditDB, experiment_id)