from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from numpy.random import beta
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session
from .models import get_all_mabs, get_mab_by_id, save_mab_to_db
from .schemas import (
    Arm,
    ArmResponse,
    MultiArmedBandit,
    MultiArmedBanditResponse,
    Outcome,
)

router = APIRouter(prefix="/mab", tags=["Multi-Armed Bandits"])


@router.post("/", response_model=MultiArmedBanditResponse)
async def create_mab(
    experiment: MultiArmedBandit, asession: AsyncSession = Depends(get_async_session)
) -> MultiArmedBanditResponse:
    """
    Create a new experiment.
    """
    response = await save_mab_to_db(experiment, asession)
    return MultiArmedBanditResponse.validate(response)


@router.get("/", response_model=list[MultiArmedBanditResponse])
async def get_mabs(
    asession: AsyncSession = Depends(get_async_session),
) -> list[MultiArmedBanditResponse]:
    """
    Get details of all experiments.
    """
    experiments = await get_all_mabs(asession)
    return [
        MultiArmedBanditResponse.model_validate(experiment)
        for experiment in experiments
    ]


@router.get("/{experiment_id}", response_model=MultiArmedBanditResponse)
async def get_mab(
    experiment_id: int, asession: AsyncSession = Depends(get_async_session)
) -> MultiArmedBanditResponse | HTTPException:
    """
    Get details of experiment with the provided `experiment_id`.
    """
    experiment = await get_mab_by_id(experiment_id, asession)
    if experiment is None:
        return HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    return MultiArmedBanditResponse.model_validate(experiment)


@router.get("/{experiment_id}/draw", response_model=Arm)
async def get_arm(
    experiment_id: int, asession: AsyncSession = Depends(get_async_session)
) -> ArmResponse | HTTPException:
    """
    Get which arm to pull next for provided experiment.
    """
    experiment = await get_mab_by_id(experiment_id, asession)
    if experiment is None:
        return HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    return thompson_sampling(experiment)


@router.put("/{experiment_id}/{arm_id}/{outcome}", response_model=Arm)
async def update_arm(
    experiment_id: int,
    arm_id: int,
    outcome: Outcome,
    asession: AsyncSession = Depends(get_async_session),
) -> ArmResponse | HTTPException:
    """
    Update the arm with the provided `arm_id` for the given `experiment_id` based on the `outcome`.
    """
    experiment = await get_mab_by_id(experiment_id, asession)
    if experiment is None:
        return HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    arms = [a for a in experiment.arms if a.arm_id == arm_id]
    if not arms:
        return HTTPException(status_code=404, detail=f"Arm with id {arm_id} not found")
    else:
        arm = arms[0]

    if outcome == Outcome.SUCCESS:
        arm.successes += 1
    else:
        arm.failures += 1

    await asession.commit()

    return ArmResponse.model_validate(arm)


def thompson_sampling(experiment) -> ArmResponse:
    """
    Perform Thompson sampling on the experiment.
    """
    alpha_param = [arm.beta_prior + arm.successes for arm in experiment.arms]
    beta_param = [arm.alpha_prior + arm.failures for arm in experiment.arms]

    samples = beta(alpha_param, beta_param)
    arm_id = samples.argmax()

    return ArmResponse.model_validate(experiment.arms[arm_id])
