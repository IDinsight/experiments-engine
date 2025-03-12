from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import authenticate_key, get_current_user
from ..database import get_async_session
from ..models import get_notifications_from_db, save_notifications_to_db
from ..schemas import NotificationsResponse, Outcome, RewardLikelihood
from ..users.models import UserDB
from .models import (
    delete_mab_by_id,
    get_all_mabs,
    get_all_rewards_by_experiment_id,
    get_mab_by_id,
    save_mab_to_db,
    save_observation_to_db,
)
from .sampling_utils import choose_arm, update_arm_params
from .schemas import (
    ArmResponse,
    MABObservation,
    MABObservationResponse,
    MultiArmedBandit,
    MultiArmedBanditResponse,
    MultiArmedBanditSample,
)

router = APIRouter(prefix="/mab", tags=["Multi-Armed Bandits"])


@router.post("/", response_model=MultiArmedBanditResponse)
async def create_mab(
    experiment: MultiArmedBandit,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> MultiArmedBanditResponse:
    """
    Create a new experiment.
    """
    mab = await save_mab_to_db(experiment, user_db.user_id, asession)
    notifications = await save_notifications_to_db(
        experiment_id=mab.experiment_id,
        user_id=user_db.user_id,
        notifications=experiment.notifications,
        asession=asession,
    )

    mab_dict = mab.to_dict()
    mab_dict["notifications"] = [n.to_dict() for n in notifications]

    return MultiArmedBanditResponse.model_validate(mab_dict)


@router.get("/", response_model=list[MultiArmedBanditResponse])
async def get_mabs(
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[MultiArmedBanditResponse]:
    """
    Get details of all experiments.
    """
    experiments = await get_all_mabs(user_db.user_id, asession)

    all_experiments = []
    for exp in experiments:
        exp_dict = exp.to_dict()
        exp_dict["notifications"] = [
            n.to_dict()
            for n in await get_notifications_from_db(
                exp.experiment_id, exp.user_id, asession
            )
        ]
        all_experiments.append(
            MultiArmedBanditResponse.model_validate(
                {
                    **exp_dict,
                    "notifications": [
                        NotificationsResponse(**n) for n in exp_dict["notifications"]
                    ],
                }
            )
        )
    return all_experiments


@router.get("/{experiment_id}", response_model=MultiArmedBanditResponse)
async def get_mab(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> MultiArmedBanditResponse:
    """
    Get details of experiment with the provided `experiment_id`.
    """
    experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)

    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    experiment_dict = experiment.to_dict()
    experiment_dict["notifications"] = [
        n.to_dict()
        for n in await get_notifications_from_db(
            experiment.experiment_id, experiment.user_id, asession
        )
    ]

    return MultiArmedBanditResponse.model_validate(experiment_dict)


@router.delete("/{experiment_id}", response_model=dict)
async def delete_mab(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Delete the experiment with the provided `experiment_id`.
    """
    try:
        experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
        if experiment is None:
            raise HTTPException(
                status_code=404, detail=f"Experiment with id {experiment_id} not found"
            )
        await delete_mab_by_id(experiment_id, user_db.user_id, asession)
        return {"message": f"Experiment with id {experiment_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}") from e


@router.get("/{experiment_id}/draw", response_model=ArmResponse)
async def draw_arm(
    experiment_id: int,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ArmResponse:
    """
    Get which arm to pull next for provided experiment.
    """
    experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )
    experiment_data = MultiArmedBanditSample.model_validate(experiment)
    chosen_arm = choose_arm(experiment=experiment_data)
    return ArmResponse.model_validate(experiment.arms[chosen_arm])


@router.put("/{experiment_id}/{arm_id}/{outcome}", response_model=ArmResponse)
async def update_arm(
    experiment_id: int,
    arm_id: int,
    outcome: float,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ArmResponse:
    """
    Update the arm with the provided `arm_id` for the given
    `experiment_id` based on the `outcome`.
    """
    # Get and validate experiment
    experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )
    experiment.n_trials += 1
    experiment_data = MultiArmedBanditSample.model_validate(experiment)

    # Get and validate arm
    arms = [a for a in experiment.arms if a.arm_id == arm_id]
    if not arms:
        raise HTTPException(status_code=404, detail=f"Arm with id {arm_id} not found")

    arm = arms[0]

    # Update arm based on reward type
    if experiment_data.reward_type == RewardLikelihood.BERNOULLI:
        Outcome(outcome)  # Check if reward is 0 or 1
        arm.alpha, arm.beta = update_arm_params(
            ArmResponse.model_validate(arm),
            experiment_data.prior_type,
            experiment_data.reward_type,
            outcome,
        )

    elif experiment_data.reward_type == RewardLikelihood.NORMAL:
        arm.mu, arm.sigma = update_arm_params(
            ArmResponse.model_validate(arm),
            experiment_data.prior_type,
            experiment_data.reward_type,
            outcome,
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="Reward type not supported.",
        )

    # Save modified arm to database
    asession.add(arm)
    await asession.commit()

    observation = MABObservation(
        experiment_id=experiment.experiment_id,
        arm_id=arm.arm_id,
        reward=outcome,
    )
    await save_observation_to_db(observation, user_db.user_id, asession)

    return ArmResponse.model_validate(arm)


@router.get(
    "/{experiment_id}/outcomes",
    response_model=list[MABObservationResponse],
)
async def get_outcomes(
    experiment_id: int,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> list[MABObservationResponse]:
    """
    Get the outcomes for the experiment.
    """
    experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
    if not experiment:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )
    experiment.n_trials += 1

    rewards = await get_all_rewards_by_experiment_id(
        experiment_id=experiment.experiment_id,
        user_id=user_db.user_id,
        asession=asession,
    )

    return [MABObservationResponse.model_validate(reward) for reward in rewards]
