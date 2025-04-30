from typing import Annotated, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import authenticate_key, get_verified_user
from ..database import get_async_session
from ..models import get_notifications_from_db, save_notifications_to_db
from ..schemas import (
    ContextType,
    NotificationsResponse,
    ObservationType,
    Outcome,
)
from ..users.models import UserDB
from ..utils import setup_logger
from .models import (
    ContextualBanditDB,
    ContextualDrawDB,
    delete_contextual_mab_by_id,
    get_all_contextual_mabs,
    get_all_contextual_obs_by_experiment_id,
    get_contextual_mab_by_id,
    get_draw_by_client_id,
    get_draw_by_id,
    save_contextual_mab_to_db,
    save_draw_to_db,
)
from .observation import update_based_on_outcome
from .sampling_utils import choose_arm
from .schemas import (
    CMABDrawResponse,
    CMABObservationResponse,
    ContextInput,
    ContextualArmResponse,
    ContextualBandit,
    ContextualBanditResponse,
    ContextualBanditSample,
)

router = APIRouter(prefix="/contextual_mab", tags=["Contextual Bandits"])

logger = setup_logger(__name__)


@router.post("/", response_model=ContextualBanditResponse)
async def create_contextual_mabs(
    experiment: ContextualBandit,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
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
    user_db: Annotated[UserDB, Depends(get_verified_user)],
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
    user_db: Annotated[UserDB, Depends(get_verified_user)],
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
    user_db: Annotated[UserDB, Depends(get_verified_user)],
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


@router.post("/{experiment_id}/draw", response_model=CMABDrawResponse)
async def draw_arm(
    experiment_id: int,
    context: List[ContextInput],
    draw_id: Optional[str] = None,
    client_id: Optional[str] = None,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> CMABDrawResponse:
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

    # Check context inputs
    if len(experiment.contexts) != len(context):
        raise HTTPException(
            status_code=400,
            detail="Number of contexts provided does not match the num contexts.",
        )
    experiment_data = ContextualBanditSample.model_validate(experiment)
    sorted_context = list(sorted(context, key=lambda x: x.context_id))

    try:
        for c_input, c_exp in zip(
            sorted_context,
            sorted(experiment.contexts, key=lambda x: x.context_id),
        ):
            if c_exp.value_type == ContextType.BINARY.value:
                Outcome(c_input.context_value)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid context value: {e}",
        ) from e

    # Generate UUID if not provided
    if draw_id is None:
        draw_id = str(uuid4())

    existing_draw = await get_draw_by_id(draw_id, user_db.user_id, asession)
    if existing_draw:
        raise HTTPException(
            status_code=400,
            detail=f"Draw ID {draw_id} already exists.",
        )

    # Check if sticky assignment
    if experiment.sticky_assignment and not client_id:
        raise HTTPException(
            status_code=400,
            detail="Client ID is required for sticky assignment.",
        )

    chosen_arm = choose_arm(
        experiment_data,
        [c.context_value for c in sorted_context],
    )
    chosen_arm_id = experiment.arms[chosen_arm].arm_id
    if experiment.sticky_assignment and client_id:
        previous_draw = await get_draw_by_client_id(
            client_id=client_id,
            user_id=user_db.user_id,
            asession=asession,
        )
        if previous_draw:
            chosen_arm_id = previous_draw.arm_id

    try:
        _ = await save_draw_to_db(
            experiment_id=experiment.experiment_id,
            arm_id=chosen_arm_id,
            context_val=[c.context_value for c in sorted_context],
            draw_id=draw_id,
            client_id=client_id,
            user_id=user_db.user_id,
            asession=asession,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving draw to database: {e}",
        ) from e

    return CMABDrawResponse.model_validate(
        {
            "draw_id": draw_id,
            "client_id": client_id,
            "arm": ContextualArmResponse.model_validate(
                [arm for arm in experiment.arms if arm.arm_id == chosen_arm_id][0]
            ),
        }
    )


@router.put("/{experiment_id}/{draw_id}/{reward}", response_model=ContextualArmResponse)
async def update_arm(
    experiment_id: int,
    draw_id: str,
    reward: float,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ContextualArmResponse:
    """
    Update the arm with the provided `arm_id` for the given
    `experiment_id` based on the reward.
    """
    experiment, draw = await validate_experiment_and_draw(
        experiment_id, draw_id, user_db.user_id, asession
    )

    return await update_based_on_outcome(
        experiment, draw, reward, asession, user_db, ObservationType.USER
    )


@router.get(
    "/{experiment_id}/outcomes",
    response_model=list[CMABObservationResponse],
)
async def get_outcomes(
    experiment_id: int,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> list[CMABObservationResponse]:
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


async def validate_experiment_and_draw(
    experiment_id: int, draw_id: str, user_id: int, asession: AsyncSession
) -> tuple[ContextualBanditDB, ContextualDrawDB]:
    """Validate the experiment and draw"""
    experiment = await get_contextual_mab_by_id(experiment_id, user_id, asession)
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
            detail=f"Draw with id {draw_id} already has a reward.",
        )

    return experiment, draw
