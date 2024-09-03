from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import Experiment
from ..models import Base


class ExperimentDB(Base):
    """
    ORM for managing experiments.
    """

    __tablename__ = "experiments"

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
        Integer, ForeignKey("experiments.experiment_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    description: Mapped[str] = mapped_column(String(length=500), nullable=True)

    alpha_prior: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    beta_prior: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


async def save_experiment_to_db(experiment: Experiment, asession: AsyncSession):
    """
    Save the experiment to the database.
    """
    arms = [ArmDB(**arm.model_dump()) for arm in experiment.arms]
    experiment_db = ExperimentDB(
        name=experiment.name,
        description=experiment.description,
        is_active=experiment.is_active,
        arms=arms,
    )

    asession.add(experiment_db)
    await asession.commit()
