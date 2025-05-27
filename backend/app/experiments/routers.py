from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import (
    require_admin_role,
)
from ..database import get_async_session
from ..users.models import UserDB
from ..utils import setup_logger
from ..workspaces.models import (
    get_user_default_workspace,
)
from .models import save_experiment_to_db, save_notifications_to_db
from .schemas import Experiment, ExperimentResponse

router = APIRouter(prefix="/experiment", tags=["Experiments"])

logger = setup_logger(__name__)


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
        notifications=experiment.notifications,
        asession=asession,
    )

    experiment_dict = experiment_db.to_dict()
    experiment_dict["notifications"] = [n.to_dict() for n in notifications]
    return ExperimentResponse.model_validate(experiment_dict)
