from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import authenticate_key, get_verified_user
from ..database import get_async_session
from ..models import get_notifications_from_db, save_notifications_to_db
from ..schemas import NotificationsResponse, Outcome, RewardLikelihood
from ..users.models import UserDB
from ..utils import setup_logger
from .models import (
    MABArmDB,
    MABDrawDB,
    MultiArmedBanditDB,
    delete_mab_by_id,
    get_all_mabs,
    get_all_obs_by_experiment_id,
    get_draw_by_id,
    get_mab_by_id,
    save_draw_to_db,
    save_mab_to_db,
    save_observation_to_db,
)
from .sampling_utils import choose_arm, update_arm_params
from .schemas import (
    ArmResponse,
    MABDrawResponse,
    MABObservationResponse,
    MultiArmedBandit,
    MultiArmedBanditResponse,
    MultiArmedBanditSample,
)

router = APIRouter(prefix="/mab", tags=["Multi-Armed Bandits"])

logger = setup_logger(__name__)


@router.post("/", response_model=MultiArmedBanditResponse)
async def create_mab(
    experiment: MultiArmedBandit,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
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
    user_db: Annotated[UserDB, Depends(get_verified_user)],
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
    user_db: Annotated[UserDB, Depends(get_verified_user)],
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
    user_db: Annotated[UserDB, Depends(get_verified_user)],
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


@router.get("/{experiment_id}/draw", response_model=MABDrawResponse)
async def draw_arm(
    experiment_id: int,
    draw_id: Optional[str] = None,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> MABDrawResponse:
    """
    Draw an arm for the provided experiment.
    """
    experiment = await get_mab_by_id(experiment_id, user_db.user_id, asession)
    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )
    experiment_data = MultiArmedBanditSample.model_validate(experiment)
    chosen_arm = choose_arm(experiment=experiment_data)

    if draw_id is None:
        draw_id = str(uuid4())

    existing_draw = await get_draw_by_id(draw_id, user_db.user_id, asession)
    if existing_draw:
        raise HTTPException(
            status_code=400,
            detail=f"Draw ID {draw_id} already exists.",
        )

    try:
        _ = await save_draw_to_db(
            experiment_id=experiment.experiment_id,
            arm_id=experiment.arms[chosen_arm].arm_id,
            draw_id=draw_id,
            user_id=user_db.user_id,
            asession=asession,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving draw to database: {e}",
        ) from e

    return MABDrawResponse.model_validate(
        {
            "draw_id": draw_id,
            "arm": ArmResponse.model_validate(experiment.arms[chosen_arm]),
        }
    )


@router.put("/{experiment_id}/{draw_id}/{outcome}", response_model=ArmResponse)
async def update_arm(
    experiment_id: int,
    draw_id: str,
    outcome: float,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ArmResponse:
    """
    Update the arm with the provided `arm_id` for the given
    `experiment_id` based on the `outcome`.
    """
    experiment, draw = await validate_experiment_and_draw(
        experiment_id, draw_id, user_db.user_id, asession
    )

    update_experiment_metadata(experiment)

    arm = get_arm_from_experiment(experiment, draw.arm_id)
    arm.n_outcomes += 1

    experiment_data = MultiArmedBanditSample.model_validate(experiment)
    await update_arm_parameters(arm, experiment_data, outcome)
    await save_updated_data(arm, draw, outcome, asession)

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

    rewards = await get_all_obs_by_experiment_id(
        experiment_id=experiment.experiment_id,
        user_id=user_db.user_id,
        asession=asession,
    )

    return [MABObservationResponse.model_validate(reward) for reward in rewards]


async def validate_experiment_and_draw(
    experiment_id: int, draw_id: str, user_id: int, asession: AsyncSession
) -> tuple[MultiArmedBanditDB, MABDrawDB]:
    """Validate the experiment and draw"""
    experiment = await get_mab_by_id(experiment_id, user_id, asession)
    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    draw = await get_draw_by_id(draw_id=draw_id, user_id=user_id, asession=asession)
    if draw is None:
        raise HTTPException(status_code=404, detail=f"Draw with id {draw_id} not found")

    if draw.experiment_id != experiment_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Draw with id {draw_id} does not belong "
                f"to experiment with id {experiment_id}",
            ),
        )

    if draw.reward is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Draw with id {draw_id} already has an outcome.",
        )

    return experiment, draw


def update_experiment_metadata(experiment: MultiArmedBanditDB) -> None:
    """Update experiment metadata with new trial information"""
    experiment.n_trials += 1
    experiment.last_trial_datetime_utc = datetime.now(tz=timezone.utc)


def get_arm_from_experiment(experiment: MultiArmedBanditDB, arm_id: int) -> MABArmDB:
    """Get and validate the arm from the experiment"""
    arms = [a for a in experiment.arms if a.arm_id == arm_id]
    if not arms:
        raise HTTPException(status_code=404, detail=f"Arm with id {arm_id} not found")
    return arms[0]


async def update_arm_parameters(
    arm: MABArmDB, experiment_data: MultiArmedBanditSample, outcome: float
) -> None:
    """Update the arm parameters based on the reward type and outcome"""
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


async def save_updated_data(
    arm: MABArmDB, draw: MABDrawDB, outcome: float, asession: AsyncSession
) -> None:
    """Save the updated arm and observation data"""
    asession.add(arm)
    await asession.commit()
    await save_observation_to_db(draw, outcome, asession)
