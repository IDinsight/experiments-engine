from fastapi import APIRouter, Depends
from .schemas import MultiArmedBandit, MultiArmedBanditResponse, Arm, ArmResponse
from .models import save_mab_to_db, get_mab_by_id
from ..database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from numpy.random import beta

router = APIRouter(prefix="/mab", tags=["experiments"])


@router.post("/", response_model=MultiArmedBanditResponse)
async def create_mab(
    experiment: MultiArmedBandit, asession: AsyncSession = Depends(get_async_session)
) -> MultiArmedBanditResponse:
    """
    Create a new experiment.
    """
    response = await save_mab_to_db(experiment, asession)
    return MultiArmedBanditResponse(
        experiment_id=response.experiment_id,
        arm_ids=[arm.arm_id for arm in response.arms],
    )


@router.get("/{experiment_id}", response_model=Arm)
async def get_arm(
    experiment_id: int, asession: AsyncSession = Depends(get_async_session)
) -> ArmResponse:
    """
    Get an arm from an experiment.
    """
    experiment = await get_mab_by_id(experiment_id, asession)
    return thompson_sampling(experiment)


def thompson_sampling(experiment) -> ArmResponse:
    """
    Perform Thompson sampling on the experiment.
    """
    num_failures = [arm.beta for arm in experiment.arms]
    num_successes = [arm.alpha for arm in experiment.arms]

    samples = beta(num_successes, num_failures)
    arm_id = samples.argmax()

    return ArmResponse.model_validate(experiment.arms[arm_id])
