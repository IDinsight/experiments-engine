from typing import Annotated, List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import authenticate_key, get_current_user
from ..database import get_async_session
from ..models import get_notifications_from_db, save_notifications_to_db
from ..schemas import ContextType, NotificationsResponse, Outcome
from ..users.models import UserDB
from .models import (
    delete_contextual_mab_by_id,
    get_all_contextual_mabs,
    get_all_contextual_obs_by_experiment_id,
    get_contextual_mab_by_id,
    get_contextual_obs_by_experiment_arm_id,
    save_contextual_mab_to_db,
    save_contextual_obs_to_db,
)
from .sampling_utils import choose_arm, update_arm_params
from .schemas import (
    CMABObservation,
    CMABObservationResponse,
    ContextInput,
    ContextualArmResponse,
    ContextualBandit,
    ContextualBanditResponse,
    ContextualBanditSample,
)

router = APIRouter(prefix="/contextual_mab", tags=["Contextual Bandits"])


@router.post("/", response_model=ContextualBanditResponse)
async def create_contextual_mabs(
    experiment: ContextualBandit,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualBanditResponse | HTTPException:
    """
    Create a new contextual experiment with different priors for each context.
    """
    cmab = await save_contextual_mab_to_db(experiment, user_db.user_id, asession)
    notifications = await save_notifications_to_db(
        experiment_id=cmab.experiment_id,
        user_id=user_db.user_id,
        notifications=experiment.notifications,
        asession=asession,
    )
    cmab_dict = cmab.to_dict()
    cmab_dict["notifications"] = [n.to_dict() for n in notifications]
    return ContextualBanditResponse.model_validate(cmab_dict)


@router.get("/", response_model=list[ContextualBanditResponse])
async def get_contextual_mabs(
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[ContextualBanditResponse]:
    """
    Get details of all experiments.
    """
    experiments = await get_all_contextual_mabs(user_db.user_id, asession)
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
            ContextualBanditResponse.model_validate(
                {
                    **exp_dict,
                    "notifications": [
                        NotificationsResponse.model_validate(n)
                        for n in exp_dict["notifications"]
                    ],
                }
            )
        )

    return all_experiments


@router.get("/{experiment_id}", response_model=ContextualBanditResponse)
async def get_contextual_mab(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualBanditResponse | HTTPException:
    """
    Get details of experiment with the provided `experiment_id`.
    """
    experiment = await get_contextual_mab_by_id(
        experiment_id, user_db.user_id, asession
    )
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
    return ContextualBanditResponse.model_validate(experiment_dict)


@router.delete("/{experiment_id}", response_model=dict)
async def delete_contextual_mab(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Delete the experiment with the provided `experiment_id`.
    """
    try:
        experiment = await get_contextual_mab_by_id(
            experiment_id, user_db.user_id, asession
        )
        if experiment is None:
            raise HTTPException(
                status_code=404, detail=f"Experiment with id {experiment_id} not found"
            )
        await delete_contextual_mab_by_id(experiment_id, user_db.user_id, asession)
        return {"detail": f"Experiment {experiment_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}") from e


@router.post("/{experiment_id}/draw", response_model=ContextualArmResponse)
async def draw_arm(
    experiment_id: int,
    context: List[ContextInput],
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualArmResponse:
    """
    Get which arm to pull next for provided experiment.
    """
    experiment = await get_contextual_mab_by_id(
        experiment_id, user_db.user_id, asession
    )

    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    if len(experiment.contexts) != len(context):
        raise HTTPException(
            status_code=400,
            detail="Number of contexts provided does not match the num contexts.",
        )

    for c_input, c_exp in zip(
        sorted(context, key=lambda x: x.context_id),
        sorted(experiment.contexts, key=lambda x: x.context_id),
    ):
        if c_exp.value_type == ContextType.BINARY.value:
            Outcome(c_input.context_value)

    experiment_data = ContextualBanditSample.model_validate(experiment)
    chosen_arm = choose_arm(
        experiment_data,
        [c.context_value for c in sorted(context, key=lambda x: x.context_id)],
    )

    return ContextualArmResponse.model_validate(experiment.arms[chosen_arm])


@router.put("/{experiment_id}/{arm_id}/{outcome}", response_model=ContextualArmResponse)
async def update_arm(
    experiment_id: int,
    arm_id: int,
    reward: float,
    context: List[ContextInput],
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualArmResponse:
    """
    Update the arm with the provided `arm_id` for the given
    `experiment_id` based on the `outcome`.
    """
    # Get the experiment and do checks
    experiment = await get_contextual_mab_by_id(
        experiment_id, user_db.user_id, asession
    )
    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    if len(experiment.contexts) != len(context):
        raise HTTPException(
            status_code=400,
            detail="Number of contexts provided does not match the num contexts.",
        )

    for c_input, c_exp in zip(
        sorted(context, key=lambda x: x.context_id),
        sorted(experiment.contexts, key=lambda x: x.context_id),
    ):
        if c_exp.value_type == ContextType.BINARY.value:
            Outcome(c_input.context_value)

    experiment_data = ContextualBanditSample.model_validate(experiment)

    # Get the arm
    arms = [a for a in experiment.arms if a.arm_id == arm_id]

    if not arms:
        raise HTTPException(status_code=404, detail=f"Arm with id {arm_id} not found")
    else:
        arm = arms[0]

        # Get all observations for the arm
        all_obs = await get_contextual_obs_by_experiment_arm_id(
            experiment_id=experiment_id,
            arm_id=arm_id,
            user_id=user_db.user_id,
            asession=asession,
        )
        rewards = [obs.reward for obs in all_obs] + [reward]
        contexts = [obs.context_val for obs in all_obs] + [
            sorted(
                float(context.context_value)
                for context in sorted(context, key=lambda x: x.context_id)
            )
        ]

        # Update the arm
        mu, covariance = update_arm_params(
            arm=ContextualArmResponse.model_validate(arm),
            prior_type=experiment_data.prior_type,
            reward_type=experiment_data.reward_type,
            context=contexts,
            reward=rewards,
        )

        # Update the arm in the database
        arm.mu = mu.tolist()
        arm.covariance = covariance.tolist()
        asession.add(arm)
        await asession.commit()

        # Save the observation
        observation = CMABObservation.model_validate(
            dict(
                arm_id=arm_id,
                reward=reward,
                context_val=[
                    c.context_value for c in sorted(context, key=lambda x: x.context_id)
                ],
            )
        )
        await save_contextual_obs_to_db(
            observation=observation,
            experiment_id=experiment_id,
            user_id=user_db.user_id,
            asession=asession,
        )

        return ContextualArmResponse.model_validate(arm)


@router.get(
    "/{experiment_id}/outcomes",
    response_model=list[CMABObservation],
)
async def get_outcomes(
    experiment_id: int,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> list[CMABObservation]:
    """
    Get the outcomes for the experiment.
    """
    experiment = await get_contextual_mab_by_id(
        experiment_id, user_db.user_id, asession
    )
    if not experiment:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    observations = await get_all_contextual_obs_by_experiment_id(
        experiment_id=experiment.experiment_id,
        user_id=user_db.user_id,
        asession=asession,
    )
    return [CMABObservationResponse.model_validate(obs) for obs in observations]
