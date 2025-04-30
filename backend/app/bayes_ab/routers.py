from typing import Annotated, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import authenticate_key, get_verified_user
from ..database import get_async_session
from ..models import get_notifications_from_db, save_notifications_to_db
from ..schemas import NotificationsResponse, ObservationType
from ..users.models import UserDB
from .models import (
    BayesianABDB,
    BayesianABDrawDB,
    delete_bayes_ab_experiment_by_id,
    get_all_bayes_ab_experiments,
    get_bayes_ab_draw_by_client_id,
    get_bayes_ab_draw_by_id,
    get_bayes_ab_experiment_by_id,
    get_bayes_ab_obs_by_experiment_id,
    save_bayes_ab_draw_to_db,
    save_bayes_ab_to_db,
)
from .observation import update_based_on_outcome
from .sampling_utils import choose_arm, update_arm_params
from .schemas import (
    BayesABArmResponse,
    BayesianAB,
    BayesianABDrawResponse,
    BayesianABObservationResponse,
    BayesianABResponse,
    BayesianABSample,
)

router = APIRouter(prefix="/bayes_ab", tags=["Bayesian A/B Testing"])


@router.post("/", response_model=BayesianABResponse)
async def create_ab_experiment(
    experiment: BayesianAB,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> BayesianABResponse:
    """
    Create a new experiment.
    """
    bayes_ab = await save_bayes_ab_to_db(experiment, user_db.user_id, asession)
    notifications = await save_notifications_to_db(
        experiment_id=bayes_ab.experiment_id,
        user_id=user_db.user_id,
        notifications=experiment.notifications,
        asession=asession,
    )

    bayes_ab_dict = bayes_ab.to_dict()
    bayes_ab_dict["notifications"] = [n.to_dict() for n in notifications]

    return BayesianABResponse.model_validate(bayes_ab_dict)


@router.get("/", response_model=list[BayesianABResponse])
async def get_bayes_abs(
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[BayesianABResponse]:
    """
    Get details of all experiments.
    """
    experiments = await get_all_bayes_ab_experiments(user_db.user_id, asession)

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
            BayesianABResponse.model_validate(
                {
                    **exp_dict,
                    "notifications": [
                        NotificationsResponse(**n) for n in exp_dict["notifications"]
                    ],
                }
            )
        )
    return all_experiments


@router.get("/{experiment_id}", response_model=BayesianABResponse)
async def get_bayes_ab(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> BayesianABResponse:
    """
    Get details of experiment with the provided `experiment_id`.
    """
    experiment = await get_bayes_ab_experiment_by_id(
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

    return BayesianABResponse.model_validate(experiment_dict)


@router.delete("/{experiment_id}", response_model=dict)
async def delete_bayes_ab(
    experiment_id: int,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> dict:
    """
    Delete the experiment with the provided `experiment_id`.
    """
    try:
        experiment = await get_bayes_ab_experiment_by_id(
            experiment_id, user_db.user_id, asession
        )
        if experiment is None:
            raise HTTPException(
                status_code=404, detail=f"Experiment with id {experiment_id} not found"
            )
        await delete_bayes_ab_experiment_by_id(experiment_id, user_db.user_id, asession)
        return {"message": f"Experiment with id {experiment_id} deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}") from e


@router.get("/{experiment_id}/draw", response_model=BayesianABDrawResponse)
async def draw_arm(
    experiment_id: int,
    draw_id: Optional[str] = None,
    client_id: Optional[str] = None,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> BayesianABDrawResponse:
    """
    Get which arm to pull next for provided experiment.
    """
    experiment = await get_bayes_ab_experiment_by_id(
        experiment_id, user_db.user_id, asession
    )

    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    if experiment.sticky_assignment and not client_id:
        raise HTTPException(
            status_code=400,
            detail="Client ID is required for sticky assignment.",
        )

    experiment_data = BayesianABSample.model_validate(experiment)
    chosen_arm = choose_arm(experiment=experiment_data)
    chosen_arm_id = experiment.arms[chosen_arm].arm_id
    if experiment.sticky_assignment and client_id:
        # Check if the client_id is already assigned to an arm
        previous_draw = await get_bayes_ab_draw_by_client_id(
            client_id=client_id, user_id=user_db.user_id, asession=asession
        )
        if previous_draw:
            chosen_arm_id = previous_draw.arm_id

    # Check for existing draws
    if draw_id is None:
        draw_id = str(uuid4())

    existing_draw = await get_bayes_ab_draw_by_id(
        draw_id=draw_id, user_id=user_db.user_id, asession=asession
    )
    if existing_draw:
        raise HTTPException(
            status_code=400,
            detail=f"Draw with id {draw_id} already exists for \
                experiment {experiment_id}",
        )

    try:
        await save_bayes_ab_draw_to_db(
            experiment_id=experiment.experiment_id,
            user_id=user_db.user_id,
            draw_id=draw_id,
            client_id=client_id,
            arm_id=chosen_arm_id,
            asession=asession,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving draw to database: {e}",
        ) from e

    return BayesianABDrawResponse.model_validate(
        {
            "draw_id": draw_id,
            "client_id": client_id,
            "arm": BayesABArmResponse.model_validate(
                [arm for arm in experiment.arms if arm.arm_id == chosen_arm_id][0],
            ),
        }
    )


@router.put("/{experiment_id}/{draw_id}/{outcome}", response_model=BayesABArmResponse)
async def save_observation_for_arm(
    experiment_id: int,
    draw_id: str,
    outcome: float,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> BayesABArmResponse:
    """
    Update the arm with the provided `arm_id` for the given
    `experiment_id` based on the `outcome`.
    """
    # Get and validate experiment
    experiment, draw = await validate_experiment_and_draw(
        experiment_id, draw_id, user_db.user_id, asession
    )

    return await update_based_on_outcome(
        experiment=experiment,
        draw=draw,
        outcome=outcome,
        asession=asession,
        observation=ObservationType.USER,
    )


@router.get(
    "/{experiment_id}/outcomes",
    response_model=list[BayesianABObservationResponse],
)
async def get_outcomes(
    experiment_id: int,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> list[BayesianABObservationResponse]:
    """
    Get the outcomes for the experiment.
    """
    experiment = await get_bayes_ab_experiment_by_id(
        experiment_id, user_db.user_id, asession
    )
    if not experiment:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    rewards = await get_bayes_ab_obs_by_experiment_id(
        experiment_id=experiment.experiment_id,
        user_id=user_db.user_id,
        asession=asession,
    )

    return [BayesianABObservationResponse.model_validate(reward) for reward in rewards]


@router.get(
    "/{experiment_id}/arms",
    response_model=list[BayesABArmResponse],
)
async def update_arms(
    experiment_id: int,
    user_db: UserDB = Depends(authenticate_key),
    asession: AsyncSession = Depends(get_async_session),
) -> list[BayesABArmResponse]:
    """
    Get the outcomes for the experiment.
    """
    # Check experiment params
    experiment = await get_bayes_ab_experiment_by_id(
        experiment_id, user_db.user_id, asession
    )
    if not experiment:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    # Prepare data for arms update
    (
        rewards,
        treatments,
        treatment_mu,
        treatment_sigma,
        control_mu,
        control_sigma,
    ) = await prepare_data_for_arms_update(
        experiment=experiment,
        user_id=user_db.user_id,
        asession=asession,
    )

    # Make updates
    arms_data = await make_updates_to_arms(
        experiment=experiment,
        treatment_mu=treatment_mu,
        treatment_sigma=treatment_sigma,
        control_mu=control_mu,
        control_sigma=control_sigma,
        rewards=rewards,
        treatments=treatments,
        asession=asession,
    )

    return arms_data


# ---- Helper functions ----


async def validate_experiment_and_draw(
    experiment_id: int, draw_id: str, user_id: int, asession: AsyncSession
) -> tuple[BayesianABDB, BayesianABDrawDB]:
    """Validate the experiment and draw"""
    experiment = await get_bayes_ab_experiment_by_id(experiment_id, user_id, asession)
    if experiment is None:
        raise HTTPException(
            status_code=404, detail=f"Experiment with id {experiment_id} not found"
        )

    draw = await get_bayes_ab_draw_by_id(
        draw_id=draw_id, user_id=user_id, asession=asession
    )
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
            detail=f"Draw with id {draw_id} already has an outcome.",
        )

    return experiment, draw


async def prepare_data_for_arms_update(
    experiment: BayesianABDB,
    user_id: int,
    asession: AsyncSession,
) -> tuple[list[float], list[float], float, float, float, float]:
    """
    Prepare the data for arm update.
    """
    # Get observations
    observations = await get_bayes_ab_obs_by_experiment_id(
        experiment_id=experiment.experiment_id,
        user_id=user_id,
        asession=asession,
    )

    if not observations:
        raise HTTPException(
            status_code=404,
            detail=f"No observations found for experiment {experiment.experiment_id}",
        )

    rewards = [obs.reward for obs in observations]

    # Get treatment and control arms
    arms_dict = {
        arm.arm_id: 1.0 if arm.is_treatment_arm else 0.0 for arm in experiment.arms
    }

    # Get params
    treatment_mu, treatment_sigma = [
        (arm.mu_init, arm.sigma_init) for arm in experiment.arms if arm.is_treatment_arm
    ][0]
    control_mu, control_sigma = [
        (arm.mu_init, arm.sigma_init)
        for arm in experiment.arms
        if not arm.is_treatment_arm
    ][0]

    treatments = [arms_dict[obs.arm_id] for obs in observations]

    return (
        rewards,
        treatments,
        treatment_mu,
        treatment_sigma,
        control_mu,
        control_sigma,
    )


async def make_updates_to_arms(
    experiment: BayesianABDB,
    treatment_mu: float,
    treatment_sigma: float,
    control_mu: float,
    control_sigma: float,
    rewards: list[float],
    treatments: list[float],
    asession: AsyncSession,
) -> list[BayesABArmResponse]:
    """
    Make updates to the arms of the experiment.
    """
    # Make updates
    experiment_data = BayesianABSample.model_validate(experiment)
    new_means, new_sigmas = update_arm_params(
        experiment=experiment_data,
        mus=[treatment_mu, control_mu],
        sigmas=[treatment_sigma, control_sigma],
        rewards=rewards,
        treatments=treatments,
    )

    arms_data = []
    for arm in experiment.arms:
        if arm.is_treatment_arm:
            arm.mu = new_means[0]
            arm.sigma = new_sigmas[0]
        else:
            arm.mu = new_means[1]
            arm.sigma = new_sigmas[1]

        asession.add(arm)
        arms_data.append(BayesABArmResponse.model_validate(arm))

    asession.add(experiment)

    await asession.commit()

    return arms_data
