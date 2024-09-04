from fastapi import APIRouter, Depends
from .schemas import MultiArmedBandit, MultiArmedBanditResponse
from .models import save_mab_to_db
from ..database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/mab", tags=["experiments"])


@router.post("/", response_model=MultiArmedBanditResponse)
async def create_mab(
    experiment: MultiArmedBandit, asession: AsyncSession = Depends(get_async_session)
):
    """
    Create a new experiment.
    """
    response = await save_mab_to_db(experiment, asession)
    return MultiArmedBanditResponse(
        experiment_id=response.experiment_id,
        arm_ids=[arm.arm_id for arm in response.arms],
    )
