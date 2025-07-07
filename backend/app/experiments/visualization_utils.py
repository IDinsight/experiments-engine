import numpy as np

from .schemas import ArmPriors, DrawResponse, ExperimentResponse, ExperimentsEnum


def get_experiment_params(experiment: ExperimentResponse) -> tuple[list, list]:
    """
    Extracts and returns the parameters of the experiment by generating samples from
    prior and posterior distributions.

    Args:
        experiment (ExperimentResponse): Experiment object containing configuration
          and parameters for arms including prior and posterior distribution parameters

    Returns:
        tuple[list, list]: Two lists containing:
            - prior_samples: List of samples drawn from prior distributions for each arm
            - posterior_samples: List of samples drawn from posterior distributions
                for each arm

    Raises:
        ValueError: If the experiment type or prior type is not supported
            (currently supports Beta and Normal priors except for CMAB experiments)

    Notes:
        - For Beta priors: Uses alpha and beta parameters to generate samples
        - For Normal priors: Uses mean (mu) and standard deviation (sigma) to
            generate samples
        - Each arm generates 1000 samples from both prior and posterior distributions
        - We can use these samples to make boxplots visualizing the
            distributions of arms
    """
    prior_samples = []
    posterior_samples = []
    try:
        if experiment.prior_type == ArmPriors.BETA:
            prior_samples = [
                np.random.beta(
                    float(arm.alpha_init) if arm.alpha_init is not None else 1.0,
                    float(arm.beta_init) if arm.beta_init is not None else 1.0,
                    1000,
                ).tolist()
                for arm in experiment.arms
            ]
            posterior_samples = [
                np.random.beta(
                    float(arm.alpha) if arm.alpha is not None else 1.0,
                    float(arm.beta) if arm.beta is not None else 1.0,
                    1000,
                ).tolist()
                for arm in experiment.arms
            ]
        elif (
            experiment.prior_type == ArmPriors.NORMAL
            and experiment.exp_type != ExperimentsEnum.CMAB
        ):
            prior_samples = [
                np.random.normal(
                    loc=float(arm.mu_init) if arm.mu_init is not None else 0.0,
                    scale=float(arm.sigma_init) if arm.sigma_init is not None else 1.0,
                    size=1000,
                ).tolist()
                for arm in experiment.arms
            ]
            posterior_samples = [
                np.random.normal(
                    loc=(float(arm.mu[0]) if arm.mu and arm.mu[0] is not None else 0.0),
                    scale=(
                        float(np.array(arm.covariance).ravel()[0])
                        if arm.covariance
                        and np.array(arm.covariance).ravel()[0] is not None
                        else 1.0
                    ),
                    size=1000,
                ).tolist()
                for arm in experiment.arms
            ]
        else:
            raise ValueError("Unsupported experiment type or prior type.")
    except Exception as e:
        raise ValueError(f"Error generating samples: {e}") from e
    return prior_samples, posterior_samples


def get_posteriors_over_time(
    experiment: ExperimentResponse, draws: list[DrawResponse]
) -> tuple[list, list]:
    """
    Extracts and returns the posterior samples (means and standard deviations) over
    time for each arm in an experiment.

    Args:
        experiment (ExperimentResponse): Experiment data containing arms and prior
            type information
        draws (list[DrawResponse]): List of draw responses containing
            posterior distribution parameters
    Returns:
        tuple[list, list]: Two lists containing:
            - means: Posterior mean estimates for each arm over time
            - stds: Posterior standard deviation estimates for each arm over time
    Raises:
        NotImplementedError: If the prior type is not supported (currently
        supports Beta and Normal prior distributions, but NOT for CMAB experiments)
    Notes:
        The function processes draws in reverse chronological order, updating the
        mean and std for the drawn arm and maintaining previous values for arms
        that are not drawn.
        Supports both Beta and Normal prior distributions but NOT for CMAB experiments.
    """
    arm_id_to_index = {arm.arm_id: i for i, arm in enumerate(experiment.arms)}

    means = np.zeros((len(experiment.arms), len(draws)))
    stds = np.zeros((len(experiment.arms), len(draws)))
    for i, draw in enumerate(draws[::-1]):
        arm_index = arm_id_to_index[draw.arm.arm_id]
        not_arm_index = list(arm_id_to_index.values())
        not_arm_index.remove(arm_index)

        if experiment.prior_type == ArmPriors.BETA:
            assert (
                draw.current_alpha and draw.current_beta
            ), "current_alpha and current_beta must be provided for Beta prior"
            means[arm_index, i] = draw.current_alpha / (
                draw.current_alpha + draw.current_beta
            )
            stds[arm_index, i] = np.sqrt(
                (draw.current_alpha * draw.current_beta)
                / (
                    (draw.current_alpha + draw.current_beta) ** 2
                    * (draw.current_alpha + draw.current_beta + 1)
                )
            )
        elif (
            experiment.prior_type == ArmPriors.NORMAL
            and experiment.exp_type != ExperimentsEnum.CMAB
        ):
            assert (
                draw.current_mu and draw.current_covariance
            ), "current_mu and current_covariance must be provided for Normal prior"
            means[arm_index, i] = np.array(draw.current_mu).ravel()[0]
            stds[arm_index, i] = np.sqrt(np.array(draw.current_covariance).ravel())[0]

        else:
            raise ValueError(
                "Unsupported prior type or experiment type for posterior"
                + "calculation"
            )

        for j in not_arm_index:
            means[j, i] = means[j, i - 1]
            stds[j, i] = stds[j, i - 1]

    return means.tolist(), stds.tolist()


def get_volume_assigned_over_time(
    experiment: ExperimentResponse, draws: list[DrawResponse]
) -> list:
    """
    Extracts and returns the volume assigned to each arm over time.

    Args:
        experiment (ExperimentResponse): Experiment data containing arms and prior
            type information
        draws (list[DrawResponse]): List of draw responses containing arm assignments
    Returns:
        list: A 2D list where each sublist contains the volume assigned to each arm
                at each time step, with the same order as the arms in the experiment.
    Notes:
        The function processes draws in reverse chronological order, counting the
        number of times each arm was assigned and calculating the cumulative volume
        assigned to each arm at each time step.
    """
    arm_id_to_index = {arm.arm_id: i for i, arm in enumerate(experiment.arms)}
    volumes = np.zeros((len(experiment.arms), len(draws)))
    arms_assigned = [arm_id_to_index[draw.arm.arm_id] for draw in draws[::-1]]

    for i in arm_id_to_index.values():
        arms_assigned_count = np.cumsum(np.array(arms_assigned) == i)
        volumes[i, :] = arms_assigned_count / (np.arange(len(draws)) + 1)
    return volumes.tolist()


def get_required_plotting_data(
    experiment: ExperimentResponse, draws: list[DrawResponse]
) -> dict:
    """
    Extracts and returns the data required for plotting.
    """
    prior_samples, posterior_samples = get_experiment_params(experiment)
    posterior_means, posterior_stds = get_posteriors_over_time(experiment, draws)
    volumes = get_volume_assigned_over_time(experiment, draws)

    return {
        "prior_samples": prior_samples,
        "posterior_samples": posterior_samples,
        "posterior_means": posterior_means,
        "posterior_stds": posterior_stds,
        "volumes": volumes,
    }
