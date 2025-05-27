from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import (
    get_verified_user,
    require_admin_role,
)
from ..database import get_async_session
from ..users.models import UserDB
from ..utils import setup_logger
from ..workspaces.models import (
    get_user_default_workspace,
)
from .dependencies import experiments_db_to_schema
from .models import (
    delete_experiment_by_id_from_db,
    get_all_experiment_types_from_db,
    get_all_experiments_from_db,
    get_experiment_by_id_from_db,
    save_experiment_to_db,
    save_notifications_to_db,
)
from .schemas import (
    Experiment,
    ExperimentResponse,
    ExperimentsEnum,
)

router = APIRouter(prefix="/experiment", tags=["Experiments"])

logger = setup_logger(__name__)


# --- POST experiments routers ---
@router.post("/", response_model=ExperimentResponse)
async def create_experiment(
    experiment: Experiment,
    user_db: Annotated[UserDB, Depends(require_admin_role)],
    asession: AsyncSession = Depends(get_async_session),
) -> ExperimentResponse:
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
    return ExperimentResponse.model_validate(experiment_dict)


# -- GET experiment routers ---
@router.get("/", response_model=list[ExperimentResponse])
async def get_all_experiments(
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[ExperimentResponse]:
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


@router.get("/type/{experiment_type}", response_model=list[ExperimentResponse])
async def get_all_experiments_by_type(
    experiment_type: ExperimentsEnum,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[ExperimentResponse]:
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


@router.get("/id/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment_by_id(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> ExperimentResponse:
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
