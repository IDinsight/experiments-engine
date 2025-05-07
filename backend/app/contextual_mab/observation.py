from datetime import datetime, timezone
from typing import Sequence

import numpy as np
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import (
    ObservationType,
    RewardLikelihood,
)
from ..users.models import UserDB
from .models import (
    ContextualArmDB,
    ContextualBanditDB,
    ContextualDrawDB,
    get_contextual_obs_by_experiment_arm_id,
    save_contextual_obs_to_db,
)
from .sampling_utils import update_arm_params
from .schemas import (
    ContextualArmResponse,
    ContextualBanditSample,
)


async def update_based_on_outcome(
    experiment: ContextualBanditDB,
    draw: ContextualDrawDB,
    reward: float,
    asession: AsyncSession,
    user_db: UserDB,
    observation_type: ObservationType,
) -> ContextualArmResponse:
    """
    Update the arm based on the outcome of the outcome.

    This is a helper function to allow `auto_fail` job to call
    it as well.
    """

    update_experiment_metadata(experiment)

    arm = get_arm_from_experiment(experiment, draw.arm_id)
    arm.n_outcomes += 1

    # Ensure reward is binary for Bernoulli reward type
    if experiment.reward_type == RewardLikelihood.BERNOULLI.value:
        if reward not in [0, 1]:
            raise HTTPException(
                status_code=400,
                detail="Reward must be 0 or 1 for Bernoulli reward type.",
            )

    # Get data for arm update
    all_obs, contexts, rewards = await prepare_data_for_arm_update(
        experiment.experiment_id, arm.arm_id, user_db.user_id, asession, draw, reward
    )

    experiment_data = ContextualBanditSample.model_validate(experiment)
    mu, covariance = update_arm_params(
        arm=ContextualArmResponse.model_validate(arm),
        prior_type=experiment_data.prior_type,
        reward_type=experiment_data.reward_type,
        context=contexts,
        reward=rewards,
    )

    await save_updated_data(
        arm, mu, covariance, draw, reward, observation_type, asession
    )

    return ContextualArmResponse.model_validate(arm)


def update_experiment_metadata(experiment: ContextualBanditDB) -> None:
    """Update experiment metadata with new trial information"""
    experiment.n_trials += 1
    experiment.last_trial_datetime_utc = datetime.now(tz=timezone.utc)


def get_arm_from_experiment(
    experiment: ContextualBanditDB, arm_id: int
) -> ContextualArmDB:
    """Get and validate the arm from the experiment"""
    arms = [a for a in experiment.arms if a.arm_id == arm_id]
    if not arms:
        raise HTTPException(status_code=404, detail=f"Arm with id {arm_id} not found")
    return arms[0]


async def prepare_data_for_arm_update(
    experiment_id: int,
    arm_id: int,
    user_id: int,
    asession: AsyncSession,
    draw: ContextualDrawDB,
    reward: float,
) -> tuple[Sequence[ContextualDrawDB], list[list], list[float]]:
    """Prepare the data needed for updating arm parameters"""
    all_obs = await get_contextual_obs_by_experiment_arm_id(
        experiment_id=experiment_id,
        arm_id=arm_id,
        user_id=user_id,
        asession=asession,
    )

    rewards = [obs.reward for obs in all_obs] + [reward]
    contexts = [obs.context_val for obs in all_obs]
    contexts.append(draw.context_val)

    return all_obs, contexts, rewards


async def save_updated_data(
    arm: ContextualArmDB,
    mu: np.ndarray,
    covariance: np.ndarray,
    draw: ContextualDrawDB,
    reward: float,
    observation_type: ObservationType,
    asession: AsyncSession,
) -> None:
    """Save the updated arm and observation data"""
    arm.mu = mu.tolist()
    arm.covariance = covariance.tolist()
    asession.add(arm)
    await asession.commit()

    await save_contextual_obs_to_db(draw, reward, asession, observation_type)
