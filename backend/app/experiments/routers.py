from fastapi import APIRouter, Depends
from .schemas import Experiment, ExperimentResponse
from .models import save_experiment_to_db
from ..database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("/", response_model=ExperimentResponse)
async def create_experiment(
    experiment: Experiment, asession: AsyncSession = Depends(get_async_session)
):
    """
    Create a new experiment.
    """
    response = await save_experiment_to_db(experiment, asession)
    return ExperimentResponse(
        experiment_id=response.experiment_id,
        arm_ids=[arm.arm_id for arm in response.arms],
    )
