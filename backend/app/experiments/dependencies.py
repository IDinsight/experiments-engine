from sqlalchemy.ext.asyncio import AsyncSession

from .models import ExperimentDB, get_notifications_from_db
from .schemas import ExperimentResponse, NotificationsResponse


async def experiments_db_to_schema(
    experiments_db: list[ExperimentDB],
    asession: AsyncSession,
) -> list[ExperimentResponse]:
    """
    Convert a list of ExperimentDB objects to a list of ExperimentResponse schemas.
    """
    all_experiments = []
    for exp in experiments_db:
        exp_dict = exp.to_dict()
        exp_dict["notifications"] = [
            n.to_dict()
            for n in await get_notifications_from_db(
                experiment_id=exp.experiment_id, user_id=exp.user_id, asession=asession
            )
        ]
        all_experiments.append(
            ExperimentResponse.model_validate(
                {
                    **exp_dict,
                    "notifications": [
                        NotificationsResponse(**n) for n in exp_dict["notifications"]
                    ],
                }
            )
        )

    return all_experiments
