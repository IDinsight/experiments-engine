from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import ObservationType, Outcome, RewardLikelihood
from .models import (
    MABArmDB,
    MABDrawDB,
    MultiArmedBanditDB,
    save_observation_to_db,
)
from .sampling_utils import update_arm_params
from .schemas import (
    ArmResponse,
    MultiArmedBanditSample,
)


async def update_based_on_outcome(
    experiment: MultiArmedBanditDB,
    draw: MABDrawDB,
    outcome: float,
    asession: AsyncSession,
    observation_type: ObservationType,
) -> ArmResponse:
    """
    Update the arm parameters based on the outcome.

    This is a helper function to allow `auto_fail` job to call
    it as well.
    """
    update_experiment_metadata(experiment)

    arm = get_arm_from_experiment(experiment, draw.arm_id)
    arm.n_outcomes += 1

    experiment_data = MultiArmedBanditSample.model_validate(experiment)
    await update_arm_parameters(arm, experiment_data, outcome)
    await save_updated_data(arm, draw, outcome, observation_type, asession)

    return ArmResponse.model_validate(arm)


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
    arm: MABArmDB,
    draw: MABDrawDB,
    outcome: float,
    observation_type: ObservationType,
    asession: AsyncSession,
) -> None:
    """Save the updated arm and observation data"""
    await asession.commit()
    await save_observation_to_db(draw, outcome, asession, observation_type)
