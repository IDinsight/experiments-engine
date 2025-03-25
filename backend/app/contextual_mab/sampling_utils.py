import numpy as np
from scipy.optimize import minimize

from ..schemas import ArmPriors, ContextLinkFunctions, RewardLikelihood
from .schemas import ContextualArmResponse, ContextualBanditSample


def sample_normal(
    mus: list[np.ndarray],
    covariances: list[np.ndarray],
    context: np.ndarray,
    link_function: ContextLinkFunctions,
) -> int:
    """
    Thompson Sampling with normal prior.

    Parameters
    ----------
    mus: mean of Normal distribution for each arm
    covariances: covariance matrix of Normal distribution for each arm
    context: context vector
    link_function: link function for the context
    """
    samples = np.array(
        [
            np.random.multivariate_normal(mean=mu, cov=cov)
            for mu, cov in zip(mus, covariances)
        ]
    ).reshape(-1, len(context))
    probs = link_function(samples @ context)
    return int(probs.argmax())


def update_arm_normal(
    current_mu: np.ndarray,
    current_covariance: np.ndarray,
    reward: float,
    context: np.ndarray,
    sigma_llhood: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Update the mean and covariance of the normal distribution.

    Parameters
    ----------
    current_mu : The mean of the normal distribution.
    current_covariance : The covariance matrix of the normal distribution.
    reward : The reward of the arm.
    context : The context vector.
    sigma_llhood : The stddev of the likelihood.
    """
    new_covariance_inv = (
        np.linalg.inv(current_covariance) + (context.T @ context) / sigma_llhood**2
    )
    new_covariance = np.linalg.inv(new_covariance_inv)

    new_mu = new_covariance @ (
        np.linalg.inv(current_covariance) @ current_mu
        + context * reward / sigma_llhood**2
    )
    return new_mu, new_covariance


def update_arm_laplace(
    current_mu: np.ndarray,
    current_covariance: np.ndarray,
    reward: np.ndarray,
    context: np.ndarray,
    link_function: ContextLinkFunctions,
    reward_likelihood: RewardLikelihood,
    prior_type: ArmPriors,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Update the mean and covariance using the Laplace approximation.

    Parameters
    ----------
    current_mu : The mean of the normal distribution.
    current_covariance : The covariance matrix of the normal distribution.
    reward : The list of rewards for the arm.
    context : The list of contexts for the arm.
    link_function : The link function for parameters to rewards.
    reward_likelihood : The likelihood function of the reward.
    prior_type : The prior type of the arm.
    """

    def objective(theta: np.ndarray) -> float:
        """
        Objective function for the Laplace approximation.

        Parameters
        ----------
        theta : The parameters of the arm.
        """
        # Log prior
        log_prior = prior_type(theta, mu=current_mu, covariance=current_covariance)

        # Log likelihood
        log_likelihood = reward_likelihood(reward, link_function(context @ theta))

        return -log_prior - log_likelihood

    result = minimize(objective, current_mu, method="L-BFGS-B", hess="2-point")
    new_mu = result.x
    covariance = result.hess_inv.todense()

    new_covariance = 0.5 * (covariance + covariance.T)
    return new_mu, new_covariance.astype(np.float64)


def choose_arm(experiment: ContextualBanditSample, context: list[float]) -> int:
    """
    Choose the arm with the highest probability.

    Parameters
    ----------
    experiment : The experiment object.
    context : The context vector.
    """
    link_function = (
        ContextLinkFunctions.NONE
        if experiment.reward_type == RewardLikelihood.NORMAL
        else ContextLinkFunctions.LOGISTIC
    )
    return sample_normal(
        mus=[np.array(arm.mu) for arm in experiment.arms],
        covariances=[np.array(arm.covariance) for arm in experiment.arms],
        context=np.array(context),
        link_function=link_function,
    )


def update_arm_params(
    arm: ContextualArmResponse,
    prior_type: ArmPriors,
    reward_type: RewardLikelihood,
    reward: list,
    context: list,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Update the arm parameters.

    Parameters
    ----------
    arm : The arm object.
    prior_type : The prior type of the arm.
    reward_type : The reward type of the arm.
    reward : All rewards for the arm.
    context : All context vectors for the arm.
    """
    if (prior_type == ArmPriors.NORMAL) and (reward_type == RewardLikelihood.NORMAL):
        return update_arm_normal(
            current_mu=np.array(arm.mu),
            current_covariance=np.array(arm.covariance),
            reward=reward[-1],
            context=np.array(context[-1]),
            sigma_llhood=1.0,  # TODO: need to implement likelihood stddev
        )
    elif (prior_type == ArmPriors.NORMAL) and (
        reward_type == RewardLikelihood.BERNOULLI
    ):
        return update_arm_laplace(
            current_mu=np.array(arm.mu),
            current_covariance=np.array(arm.covariance),
            reward=np.array(reward),
            context=np.array(context),
            link_function=ContextLinkFunctions.LOGISTIC,
            reward_likelihood=RewardLikelihood.BERNOULLI,
            prior_type=ArmPriors.NORMAL,
        )
    else:
        raise ValueError("Prior and reward type combination is not supported.")
