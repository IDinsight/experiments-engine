from datetime import datetime, timezone

from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import ObservationType, Outcome, RewardLikelihood
from .models import (
    BayesianABArmDB,
    BayesianABDB,
    BayesianABDrawDB,
    save_bayes_ab_observation_to_db,
)
from .schemas import (
    BayesABArmResponse,
    BayesianABSample,
)


async def update_based_on_outcome(
    experiment: BayesianABDB,
    draw: BayesianABDrawDB,
    outcome: float,
    asession: AsyncSession,
    observation: ObservationType,
) -> BayesABArmResponse:
    """
    Update the arm parameters based on the outcome.

    This is a helper function to allow `auto_fail` job to call
    it as well.
    """
    update_experiment_metadata(experiment)

    arm = get_arm_from_experiment(experiment, draw.arm_id)
    arm.n_outcomes += 1

    experiment_data = BayesianABSample.model_validate(experiment)
    if experiment_data.reward_type == RewardLikelihood.BERNOULLI:
        Outcome(outcome)  # Check if reward is 0 or 1

    await save_updated_data(arm, draw, outcome, asession)

    return BayesABArmResponse.model_validate(arm)


def update_experiment_metadata(experiment: BayesianABDB) -> None:
    """
    Update the experiment metadata with new information.
    """
    experiment.n_trials += 1
    experiment.last_trial_datetime_utc = datetime.now(tz=timezone.utc)


def get_arm_from_experiment(experiment: BayesianABDB, arm_id: int) -> BayesianABArmDB:
    """
    Get and validate the arm from the experiment.
    """
    arms = [a for a in experiment.arms if a.arm_id == arm_id]
    if not arms:
        raise HTTPException(status_code=404, detail=f"Arm with id {arm_id} not found")
    return arms[0]


async def save_updated_data(
    arm: BayesianABArmDB,
    draw: BayesianABDrawDB,
    outcome: float,
    asession: AsyncSession,
) -> None:
    """
    Save the updated data to the database.
    """
    asession.add(arm)
    await asession.commit()
    await save_bayes_ab_observation_to_db(draw, outcome, asession)
