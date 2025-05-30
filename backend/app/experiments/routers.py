from typing import Annotated, Optional
from uuid import uuid4

import numpy as np
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import (
    authenticate_workspace_key,
    get_verified_user,
    require_admin_role,
)
from ..database import get_async_session
from ..users.models import UserDB
from ..utils import setup_logger
from ..workspaces.models import (
    WorkspaceDB,
    get_user_default_workspace,
)
from .dependencies import (
    experiments_db_to_schema,
    format_rewards_for_arm_update,
    save_updated_data,
    update_arm_parameters,
    validate_experiment_and_draw,
)
from .models import (
    delete_experiment_by_id_from_db,
    get_all_experiment_types_from_db,
    get_all_experiments_from_db,
    get_draw_by_id,
    get_draws_by_experiment_id,
    get_experiment_by_id_from_db,
    save_draw_to_db,
    save_experiment_to_db,
    save_notifications_to_db,
)
from .sampling_utils import choose_arm
from .schemas import (
    ArmResponse,
    ContextInput,
    ContextType,
    DrawResponse,
    Experiment,
    ExperimentSample,
    ExperimentsEnum,
    Outcome,
)

router = APIRouter(prefix="/experiment", tags=["Experiments"])

logger = setup_logger(__name__)


# --- POST experiments routers ---
@router.post("/", response_model=ExperimentSample)
async def create_experiment(
    experiment: Experiment,
    user_db: Annotated[UserDB, Depends(require_admin_role)],
    asession: AsyncSession = Depends(get_async_session),
) -> ExperimentSample:
    """
    Create a new experiment in the current user's workspace.
    """
    workspace_db = await get_user_default_workspace(asession=asession, user_db=user_db)

    if workspace_db is None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found. Please create a workspace first.",
        )

    experiment_db = await save_experiment_to_db(
        experiment=experiment,
        workspace_id=workspace_db.workspace_id,
        user_id=user_db.user_id,
        asession=asession,
    )
    notifications = await save_notifications_to_db(
        experiment_id=experiment_db.experiment_id,
        user_id=user_db.user_id,
        workspace_id=workspace_db.workspace_id,
        notifications=experiment.notifications,
        asession=asession,
    )

    experiment_dict = experiment_db.to_dict()
    experiment_dict["notifications"] = [n.to_dict() for n in notifications]
    return ExperimentSample.model_validate(experiment_dict)


# -- GET experiment routers ---
@router.get("/", response_model=list[ExperimentSample])
async def get_all_experiments(
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[ExperimentSample]:
    """
    Retrieve all experiments for the current user's workspace.
    """
    workspace_db = await get_user_default_workspace(asession=asession, user_db=user_db)

    if workspace_db is None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found. Please create a workspace first.",
        )

    experiments = await get_all_experiments_from_db(
        workspace_id=workspace_db.workspace_id,
        asession=asession,
    )

    all_experiments = await experiments_db_to_schema(
        experiments_db=list(experiments),
        asession=asession,
    )
    return all_experiments


@router.get("/type/{experiment_type}", response_model=list[ExperimentSample])
async def get_all_experiments_by_type(
    experiment_type: ExperimentsEnum,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[ExperimentSample]:
    """
    Retrieve all experiments for the current user's workspace.
    """
    workspace_db = await get_user_default_workspace(asession=asession, user_db=user_db)

    if workspace_db is None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found. Please create a workspace first.",
        )

    experiments = await get_all_experiment_types_from_db(
        workspace_id=workspace_db.workspace_id,
        experiment_type=experiment_type.value,
        asession=asession,
    )

    all_experiments = await experiments_db_to_schema(
        experiments_db=list(experiments),
        asession=asession,
    )
    return all_experiments


@router.get("/id/{experiment_id}", response_model=ExperimentSample)
async def get_experiment_by_id(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> ExperimentSample:
    """
    Retrieve a specific experiment by ID for the current user's workspace.
    """
    workspace_db = await get_user_default_workspace(asession=asession, user_db=user_db)

    if workspace_db is None:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found. Please create a workspace first.",
        )

    experiment = await get_experiment_by_id_from_db(
        workspace_id=workspace_db.workspace_id,
        experiment_id=experiment_id,
        asession=asession,
    )

    if not experiment:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found.",
        )

    experiment_dict = await experiments_db_to_schema(
        experiments_db=[experiment],
        asession=asession,
    )

    return experiment_dict[0]


# -- DELETE experiment routers ---
@router.delete("/type/{experiment_type}", response_model=dict[str, str])
async def delete_experiment_by_type(
    experiment_type: ExperimentsEnum,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """
    Retrieve a specific experiment by ID for the current user's workspace.
    """
    try:
        workspace_db = await get_user_default_workspace(
            asession=asession, user_db=user_db
        )

        if workspace_db is None:
            raise HTTPException(
                status_code=404,
                detail="Workspace not found. Please create a workspace first.",
            )

        experiments = await get_all_experiment_types_from_db(
            workspace_id=workspace_db.workspace_id,
            experiment_type=experiment_type.value,
            asession=asession,
        )

        if len(experiments) == 0:
            raise HTTPException(
                status_code=404,
                detail="No experiments found.",
            )

        for exp in experiments:
            await delete_experiment_by_id_from_db(
                workspace_id=workspace_db.workspace_id,
                experiment_id=exp.experiment_id,
                asession=asession,
            )

        return {
            "message": f"Experiments of type {experiment_type} deleted successfully."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}",
        ) from e


@router.delete("/id/{experiment_id}", response_model=dict[str, str])
async def delete_experiment_by_id(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    """
    Retrieve a specific experiment by ID for the current user's workspace.
    """
    try:
        workspace_db = await get_user_default_workspace(
            asession=asession, user_db=user_db
        )

        if workspace_db is None:
            raise HTTPException(
                status_code=404,
                detail="Workspace not found. Please create a workspace first.",
            )

        experiment = await get_experiment_by_id_from_db(
            workspace_id=workspace_db.workspace_id,
            experiment_id=experiment_id,
            asession=asession,
        )

        if not experiment:
            raise HTTPException(
                status_code=404,
                detail="Experiment not found.",
            )

        await delete_experiment_by_id_from_db(
            workspace_id=workspace_db.workspace_id,
            experiment_id=experiment_id,
            asession=asession,
        )

        return {"message": f"Experiment with id {experiment_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}",
        ) from e


# --- Draw and update arms ---
@router.get("/{experiment_id}/draw", response_model=DrawResponse)
async def draw_arm(
    experiment_id: int,
    contexts: Optional[list[ContextInput]] = None,
    draw_id: Optional[str] = None,
    workspace_db: WorkspaceDB = Depends(authenticate_workspace_key),
    asession: AsyncSession = Depends(get_async_session),
) -> DrawResponse:
    """
    Draw an arm from the specified experiment.
    """
    workspace_id = workspace_db.workspace_id

    experiment = await get_experiment_by_id_from_db(
        workspace_id=workspace_id, experiment_id=experiment_id, asession=asession
    )
    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    # Check contexts
    if (experiment.exp_type == ExperimentsEnum.CMAB.value) and (not contexts):
        raise HTTPException(
            status_code=400, detail="Context is required for CMAB experiments."
        )
    elif (experiment.exp_type == ExperimentsEnum.CMAB.value) and contexts:
        if len(contexts) != len(experiment.contexts):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Expected {len(experiment.contexts)} contexts"
                    f" but got {len(contexts)}."
                ),
            )

    # Check for existing draws
    if draw_id is None:
        draw_id = str(uuid4())

    existing_draw = await get_draw_by_id(draw_id=draw_id, asession=asession)
    if existing_draw:
        raise HTTPException(
            status_code=400, detail=f"Draw with id {draw_id} already exists."
        )

    # -- Perform the draw ---
    experiment_data = ExperimentSample.model_validate(experiment)

    # Validate contexts input
    if contexts:
        sorted_contexts = list(sorted(contexts, key=lambda x: x.context_id))
        try:
            for c_input, c_exp in zip(
                sorted_contexts,
                sorted(experiment_data.contexts, key=lambda x: x.context_id),
            ):
                if c_exp.value_type == ContextType.BINARY.value:
                    Outcome(c_input.context_value)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid context value: {e}",
            ) from e

    # Choose arm
    chosen_arm = choose_arm(
        experiment=experiment_data,
        context=[c.context_value for c in sorted_contexts] if contexts else None,
    )
    chosen_arm_id = experiment.arms[chosen_arm].arm_id

    try:
        draw = await save_draw_to_db(
            draw_id=draw_id,
            arm_id=chosen_arm_id,
            experiment_id=experiment_id,
            workspace_id=workspace_id,
            client_id=None,  # TODO: Update for sticky assignment
            context=[c.context_value for c in sorted_contexts],
            asession=asession,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving draw: {str(e)}",
        ) from e

    return DrawResponse.model_validate(
        draw_id=draw_id,
        draw_datetime_utc=draw.draw_datetime_utc,
        arm=experiment_data.arms[chosen_arm],
        context_val=draw.context_val,
    )


@router.put("/{experiment_id}/{draw_id}/{reward}", response_model=ArmResponse)
async def update_arm(
    experiment_id: int,
    draw_id: str,
    reward: float,
    workspace_db: WorkspaceDB = Depends(authenticate_workspace_key),
    asession: AsyncSession = Depends(get_async_session),
) -> ArmResponse:
    """
    Update the arm with the given reward.
    """

    experiment, draw = await validate_experiment_and_draw(
        experiment_id=experiment_id,
        draw_id=draw_id,
        workspace_id=workspace_db.workspace_id,
        asession=asession,
    )

    # Get rewards
    chosen_arm_index = int(
        np.argwhere(np.array([arm.arm_id for arm in experiment.arms]) == draw.arm_id)[
            0
        ][0],
    )
    rewards, contexts, treatments = await format_rewards_for_arm_update(
        experiment=experiment, chosen_arm_id=draw.arm_id, asession=asession
    )
    rewards = ([reward] + rewards) if rewards else [reward]
    contexts = ([draw.context_val] + contexts) if contexts else [draw.context_val]
    new_treatment = [float(experiment.arms[chosen_arm_index].is_treatment_arm)]
    treatments = (new_treatment + treatments) if treatments else new_treatment
    # Update the arm with the given reward
    try:
        arm = await update_arm_parameters(
            arm=experiment.arms[chosen_arm_index],
            experiment_data=ExperimentSample.model_validate(experiment),
            chosen_arm=chosen_arm_index,
            rewards=rewards,
            contexts=contexts,
            treatments=treatments,
        )
        await save_updated_data(
            arm=arm,
            draw=draw,
            reward=reward,
            observation_type=experiment.observation_type,
            asession=asession,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating arm: {str(e)}",
        ) from e

    return ArmResponse.model_validate(arm)


@router.get("/{experiment_id}/rewards", response_model=list[DrawResponse])
async def get_rewards(
    experiment_id: int,
    workspace_db: WorkspaceDB = Depends(authenticate_workspace_key),
    asession: AsyncSession = Depends(get_async_session),
) -> list[DrawResponse]:
    """
    Retrieve all rewards for the specified experiment.
    """
    experiment = await get_experiment_by_id_from_db(
        workspace_id=workspace_db.workspace_id,
        experiment_id=experiment_id,
        asession=asession,
    )

    if not experiment:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    draws = await get_draws_by_experiment_id(
        experiment_id=experiment_id, asession=asession
    )

    return [DrawResponse.model_validate(draw) for draw in draws]
