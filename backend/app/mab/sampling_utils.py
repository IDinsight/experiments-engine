import numpy as np
from numpy.random import beta, normal

from ..mab.schemas import ArmResponse, MultiArmedBanditSample
from ..schemas import ArmPriors, Outcome, RewardLikelihood


def sample_beta_binomial(alphas: np.ndarray, betas: np.ndarray) -> int:
    """
    Thompson Sampling with Beta-Binomial distribution.

    Parameters
    ----------
    alphas : alpha parameter of Beta distribution for each arm
    betas : beta parameter of Beta distribution for each arm
    """
    samples = beta(alphas, betas)
    return int(samples.argmax())


def sample_normal(mus: np.ndarray, sigmas: np.ndarray) -> int:
    """
    Thompson Sampling with conjugate normal distribution.

    Parameters
    ----------
    mus: mean of Normal distribution for each arm
    sigmas: standard deviation of Normal distribution for each arm
    """
    samples = normal(loc=mus, scale=sigmas)
    return int(samples.argmax())


def update_arm_beta_binomial(
    alpha: float, beta: float, reward: Outcome
) -> tuple[float, float]:
    """
    Update the alpha and beta parameters of the Beta distribution.

    Parameters
    ----------
    alpha : int
        The alpha parameter of the Beta distribution.
    beta : int
        The beta parameter of the Beta distribution.
    reward : Outcome
        The reward of the arm.
    """
    if reward == Outcome.SUCCESS:

        return alpha + 1, beta
    else:
        return alpha, beta + 1


def update_arm_normal(
    current_mu: float, current_sigma: float, reward: float, sigma_llhood: float
) -> tuple[float, float]:
    """
    Update the mean and standard deviation of the Normal distribution.

    Parameters
    ----------
    current_mu : The mean of the Normal distribution.
    current_sigma : The standard deviation of the Normal distribution.
    reward : The reward of the arm.
    sigma_llhood : The likelihood of the standard deviation.
    """
    denom = sigma_llhood**2 + current_sigma**2
    new_sigma = sigma_llhood * current_sigma / np.sqrt(denom)
    new_mu = (current_mu * sigma_llhood**2 + reward * current_sigma**2) / denom
    return new_mu, new_sigma


def choose_arm(experiment: MultiArmedBanditSample) -> int:
    """
    Choose arm based on posterior

    Parameters
    ----------
    experiment : MultiArmedBanditResponse
        The experiment data containing priors and rewards for each arm.
    """
    if (experiment.prior_type == ArmPriors.BETA) and (
        experiment.reward_type == RewardLikelihood.BERNOULLI
    ):
        alphas = np.array([arm.alpha for arm in experiment.arms])
        betas = np.array([arm.beta for arm in experiment.arms])

        return sample_beta_binomial(alphas=alphas, betas=betas)

    elif (experiment.prior_type == ArmPriors.NORMAL) and (
        experiment.reward_type == RewardLikelihood.NORMAL
    ):
        mus = np.array([arm.mu for arm in experiment.arms])
        sigmas = np.array([arm.sigma for arm in experiment.arms])
        # TODO: add support for non-std sigma_llhood
        return sample_normal(mus=mus, sigmas=sigmas)
    else:
        raise ValueError("Prior and reward type combination is not supported.")


def update_arm_params(
    arm: ArmResponse,
    prior_type: ArmPriors,
    reward_type: RewardLikelihood,
    reward: float,
) -> tuple:
    """
    Update the arm with the provided `arm_id` based on the `reward`.

    Parameters
    ----------
    arm: The arm to update.
    prior_type: The type of prior distribution for the arms.
    reward_type: The likelihood distribution of the reward.
    reward: The reward of the arm.
    """

    if (prior_type == ArmPriors.BETA) and (reward_type == RewardLikelihood.BERNOULLI):
        if arm.alpha is None or arm.beta is None:
            raise ValueError("Beta prior requires alpha and beta.")
        outcome = Outcome(reward)
        return update_arm_beta_binomial(alpha=arm.alpha, beta=arm.beta, reward=outcome)

    elif (
        (prior_type == ArmPriors.NORMAL)
        and (reward_type == RewardLikelihood.NORMAL)
        and (arm.mu and arm.sigma)
    ):
        return update_arm_normal(
            current_mu=arm.mu,
            current_sigma=arm.sigma,
            reward=reward,
            sigma_llhood=1.0,  # TODO: add support for non-std sigma_llhood
        )
    else:
        raise ValueError("Prior and reward type combination is not supported.")
