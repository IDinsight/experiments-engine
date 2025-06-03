from datetime import datetime, timezone
from typing import Union

import numpy as np
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    ArmDB,
    DrawDB,
    ExperimentDB,
    get_draw_by_id,
    get_draws_with_rewards_by_experiment_id,
    get_experiment_by_id_from_db,
    get_notifications_from_db,
    save_observation_to_db,
)
from .sampling_utils import update_arm
from .schemas import (
    ArmPriors,
    ArmResponse,
    ExperimentSample,
    ExperimentsEnum,
    NotificationsResponse,
    ObservationType,
    Outcome,
    RewardLikelihood,
)


async def experiments_db_to_schema(
    experiments_db: list[ExperimentDB],
    asession: AsyncSession,
) -> list[ExperimentSample]:
    """
    Convert a list of ExperimentDB objects to a list of ExperimentResponse schemas.
    """
    all_experiments = []
    for exp in experiments_db:
        exp_dict = exp.to_dict()
        exp_dict["notifications"] = [
            n.to_dict()
            for n in await get_notifications_from_db(
                experiment_id=exp.experiment_id,
                user_id=exp.user_id,
                workspace_id=exp.workspace_id,
                asession=asession,
            )
        ]
        all_experiments.append(
            ExperimentSample.model_validate(
                {
                    **exp_dict,
                    "notifications": [
                        NotificationsResponse(**n) for n in exp_dict["notifications"]
                    ],
                }
            )
        )

    return all_experiments


async def validate_experiment_and_draw(
    experiment_id: int, draw_id: str, workspace_id: int, asession: AsyncSession
) -> tuple[ExperimentDB, DrawDB]:
    """
    Validate the experiment and draw.
    """
    experiment = await get_experiment_by_id_from_db(
        workspace_id=workspace_id, experiment_id=experiment_id, asession=asession
    )
    # Check experiment
    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    draw = await get_draw_by_id(draw_id=draw_id, asession=asession)
    # Check draw
    if draw is None:
        raise HTTPException(status_code=404, detail=f"Draw with id {draw_id} not found")
    if draw.experiment_id != experiment_id:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Draw with id {draw_id} does not belong to "
                f"experiment with id {experiment_id}"
            ),
        )
    if draw.reward:
        raise HTTPException(
            status_code=400,
            detail=f"Draw with id {draw_id} has already been updated with a reward.",
        )

    return experiment, draw


async def format_rewards_for_arm_update(
    experiment: ExperimentDB, chosen_arm_id: int, reward: float, asession: AsyncSession
) -> tuple[list[float], list[list[float]] | None, list[float] | None]:
    """
    Format the rewards for the arm update.
    """
    previous_rewards = await get_draws_with_rewards_by_experiment_id(
        experiment_id=experiment.experiment_id, asession=asession
    )
    if not previous_rewards:
        return [], None, None

    rewards = []
    treatments = None
    contexts = None

    if experiment.exp_type != ExperimentsEnum.BAYESAB.value:
        rewards = [
            draw.reward for draw in previous_rewards if draw.arm_id == chosen_arm_id
        ]
    else:
        treatments = []
        for draw in previous_rewards:
            rewards.append(draw.reward)
            treatments.append(
                [
                    float(arm.is_treatment_arm)
                    for arm in experiment.arms
                    if arm.arm_id == draw.arm_id
                ][0]
            )

    if experiment.exp_type == ExperimentsEnum.CMAB.value:
        contexts = []
        for draw in previous_rewards:
            if draw.context_val:
                contexts.append(draw.context_val)
            else:
                raise ValueError(
                    f"Context value is missing for draw id {draw.draw_id}"
                    f" in CMAB experiment {draw.experiment_id}."
                )

    rewards_list = [reward] if rewards is None else [reward] + rewards

    context_list = None if not draw.context_val else [draw.context_val]
    if contexts and context_list:
        context_list = context_list + contexts

    chosen_arm_index = int(
        np.argwhere([a.arm_id == chosen_arm_id for a in experiment.arms])[0][0]
    )
    new_treatment = [float(experiment.arms[chosen_arm_index].is_treatment_arm)]
    treatments_list = (
        new_treatment if treatments is None else new_treatment + treatments
    )

    return rewards_list, context_list, treatments_list


async def update_arm_based_on_outcome(
    experiment: ExperimentDB,
    draw: DrawDB,
    rewards: list[float],
    contexts: Union[list[list[float]], None],
    treatments: Union[list[float], None],
) -> ArmResponse:
    """
    Update the arm parameters based on the outcome.

    This is a helper function to allow `auto_fail` job to call
    it as well.
    """
    update_experiment_metadata(experiment)

    arm = get_arm_from_experiment(experiment, draw.arm_id)
    arm.n_outcomes += 1

    chosen_arm = int(
        np.argwhere([a.arm_id == arm.arm_id for a in experiment.arms])[0][0]
    )

    await update_arm_parameters(
        arm=arm,
        experiment=experiment,
        chosen_arm=chosen_arm,
        rewards=rewards,
        contexts=contexts,
        treatments=treatments,
    )

    return ArmResponse.model_validate(arm)


def update_experiment_metadata(experiment: ExperimentDB) -> None:
    """Update experiment metadata with new trial information"""
    experiment.n_trials += 1
    experiment.last_trial_datetime_utc = datetime.now(tz=timezone.utc)


def get_arm_from_experiment(experiment: ExperimentDB, arm_id: int) -> ArmDB:
    """Get and validate the arm from the experiment"""
    arms = [a for a in experiment.arms if a.arm_id == arm_id]
    if not arms:
        raise HTTPException(status_code=404, detail=f"Arm with id {arm_id} not found")
    return arms[0]


async def update_arm_parameters(
    arm: ArmDB,
    experiment: ExperimentDB,
    chosen_arm: int,
    rewards: list[float],
    contexts: Union[list[list[float]], None],
    treatments: Union[list[float], None],
) -> None:
    """Update the arm parameters based on the reward type and outcome"""
    experiment_data = ExperimentSample.model_validate(experiment.to_dict())
    if experiment_data.reward_type == RewardLikelihood.BERNOULLI:
        Outcome(rewards[0])  # Check if reward is 0 or 1
    params = update_arm(
        experiment=experiment_data,
        rewards=rewards,
        arm_to_update=chosen_arm,
        context=contexts,
        treatments=treatments,
    )

    if experiment_data.exp_type == ExperimentsEnum.BAYESAB:
        if experiment_data.prior_type == ArmPriors.NORMAL:
            mus, covariances = params
            for arm in experiment.arms:
                if arm.is_treatment_arm:
                    arm.mu = [mus[0]]
                    arm.covariance = covariances[0]
                else:
                    arm.mu = [mus[1]]
                    arm.covariance = covariances[1]
        else:
            raise HTTPException(
                status_code=400,
                detail="Prior type not supported for Bayesian A/B experiments.",
            )
    else:
        if experiment_data.prior_type == ArmPriors.BETA:
            arm.alpha, arm.beta = params
        elif experiment_data.prior_type == ArmPriors.NORMAL:
            arm.mu, arm.covariance = params
        else:
            raise HTTPException(
                status_code=400,
                detail="Prior type not supported.",
            )


async def save_updated_data(
    arm: ArmDB,
    draw: DrawDB,
    reward: float,
    observation_type: ObservationType,
    asession: AsyncSession,
) -> None:
    """Save the updated arm and observation data"""
    await asession.commit()
    await save_observation_to_db(
        draw=draw, reward=reward, observation_type=observation_type, asession=asession
    )
