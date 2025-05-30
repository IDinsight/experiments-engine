from typing import Any, Optional, Union

import numpy as np
from numpy.random import beta
from scipy.optimize import minimize

from .schemas import (
    ArmPriors,
    ContextLinkFunctions,
    ExperimentSample,
    ExperimentsEnum,
    Outcome,
    RewardLikelihood,
)


# ------------- Utilities for sampling and updating arms ----------------
# --- Sampling functions for Thompson Sampling ---
def _sample_beta_binomial(alphas: np.ndarray, betas: np.ndarray) -> int:
    """
    Thompson Sampling with Beta-Binomial distribution.

    Parameters
    ----------
    alphas : alpha parameter of Beta distribution for each arm
    betas : beta parameter of Beta distribution for each arm
    """
    samples = beta(alphas, betas)
    return int(samples.argmax())


def _sample_normal(
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


# --- Arm update functions ---
def _update_arm_beta_binomial(
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


def _update_arm_normal(
    current_mu: np.ndarray,
    current_covariance: np.ndarray,
    reward: float,
    llhood_sigma: float,
    context: Optional[np.ndarray] = None,
) -> tuple[float, np.ndarray]:
    """
    Update the mean and standard deviation of the Normal distribution.

    Parameters
    ----------
    current_mu : The mean of the Normal distribution.
    current_covariance : The covariance of the Normal distribution.
    reward : The reward of the arm.
    llhood_sigma : The standard deviation of the likelihood.
    context : The context vector.
    """
    # Likelihood covariance matrix inverse
    llhood_covariance_inv = np.eye(len(current_mu)) / llhood_sigma**2
    if context:
        llhood_covariance_inv *= context.T @ context

    # Prior covariance matrix inverse
    prior_covariance_inv = np.linalg.inv(current_covariance)

    # New covariance
    new_covariance = np.linalg.inv(prior_covariance_inv + llhood_covariance_inv)

    # New mean
    llhood_term: Union[np.ndarray, float] = reward / llhood_sigma**2
    if context:
        llhood_term = context.T * llhood_term
    new_mu = new_covariance @ ((prior_covariance_inv @ current_mu) + llhood_term)

    return new_mu.tolist(), new_covariance.tolist()


def _update_arm_laplace(
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

    result = minimize(
        objective, x0=np.zeros_like(current_mu), method="L-BFGS-B", hess="2-point"
    )
    new_mu = result.x
    covariance = result.hess_inv.todense()  # type: ignore

    new_covariance = 0.5 * (covariance + covariance.T)
    return new_mu.tolist(), new_covariance.tolist()


# ------------- Import functions ----------------
# --- Choose arm function ---
def choose_arm(
    experiment: ExperimentSample, context: Optional[Union[list, np.ndarray, None]]
) -> int:
    """
    Choose arm based on posterior using Thompson Sampling.

    Parameters
    ----------
    experiment: The experiment data containing priors and rewards for each arm.
    context: Optional context vector for the experiment.
    """
    # Choose arms with equal probability for Bayesian A/B tests
    if experiment.exp_type == ExperimentsEnum.BAYESAB:
        index = np.random.choice(len(experiment.arms), size=1)
        return int(index[0])
    else:
        if experiment.prior_type == ArmPriors.BETA:
            if experiment.reward_type != RewardLikelihood.BERNOULLI:
                raise ValueError("Beta prior is only supported for Bernoulli rewards.")
            alphas = np.array([arm.alpha for arm in experiment.arms])
            betas = np.array([arm.beta for arm in experiment.arms])

            return _sample_beta_binomial(alphas=alphas, betas=betas)

        elif experiment.prior_type == ArmPriors.NORMAL:
            mus = [np.array(arm.mu) for arm in experiment.arms]
            covariances = [np.array(arm.covariance) for arm in experiment.arms]

            context_array = (
                np.ones_like(mus[0]) if context is None else np.array(context)
            )

            return _sample_normal(
                mus=mus,
                covariances=covariances,
                context=context_array,
                link_function=(
                    ContextLinkFunctions.NONE
                    if experiment.reward_type == RewardLikelihood.NORMAL
                    else ContextLinkFunctions.LOGISTIC
                ),
            )


# --- Update arm parameters ---
def update_arm(
    experiment: ExperimentSample,
    rewards: list[float],
    arm_to_update: Optional[int] = None,
    context: Optional[Union[list, np.ndarray, None]] = None,
    treatments: Optional[list[float]] = None,
) -> Any:
    """
    Update the arm parameters based on the experiment type and reward.

    Parameters
    ----------
    experiment: The experiment data containing arms, prior type and reward
        type information.
    rewards: The rewards received from the arm.
    context: The context vector for the arm.
    treatments: The treatments applied to the arm, for a Bayesian A/B test.
    """

    # NB: For Bayesian AB tests, we assume that the update runs
    # AFTER all rewards have been observed.
    # We hijack the Laplace approximation function to update the
    # model parameters as follows:
    # 1. current_mu -> [treatment_mu, control_mu, bias_mu = 0]
    # 2. current_covariance -> [treatment_sigma, control_sigma, bias_sigma = 1]
    # 3. context -> [is_treatment_arm, is_control_arm, 1]
    if experiment.exp_type == ExperimentsEnum.BAYESAB:

        assert treatments, "Treatments must be provided for Bayesian A/B tests."

        mus = np.array([arm.mu for arm in experiment.arms] + [0.0])
        covariances = np.diag(
            [np.array(arm.covariance).ravel()[0] for arm in experiment.arms] + [1.0]
        )

        context = np.zeros((len(rewards), 3))
        context[:, 0] = np.array(treatments)
        context[:, 1] = 1.0 - np.array(treatments)
        context[:, 2] = 1.0

        new_mus, new_covariances = _update_arm_laplace(
            current_mu=mus,
            current_covariance=covariances,
            reward=np.array(rewards),
            context=context,
            link_function=(
                ContextLinkFunctions.NONE
                if experiment.reward_type == RewardLikelihood.NORMAL
                else ContextLinkFunctions.LOGISTIC
            ),
            reward_likelihood=experiment.reward_type,
            prior_type=experiment.prior_type,
        )

        treatment_mu, control_mu, _ = new_mus
        treatment_sigma, control_sigma, _ = np.diag(new_covariances)
        return [treatment_mu, control_mu], [[treatment_sigma]], [[control_sigma]]
    else:
        # Update for MABs and CMABs
        assert (
            arm_to_update
        ), f"arm_to_update must be provided for {experiment.exp_type} experiments."

        arm = experiment.arms[arm_to_update]
        assert arm.alpha and arm.beta, "Arm must have alpha and beta parameters."

        # Beta-binomial priors
        if experiment.prior_type == ArmPriors.BETA:
            return _update_arm_beta_binomial(
                alpha=arm.alpha, beta=arm.beta, reward=Outcome(rewards[0])
            )

        # Normal priors
        elif experiment.prior_type == ArmPriors.NORMAL:
            if context is None:
                context = np.ones_like(arm.mu)
            # Normal likelihood
            if experiment.reward_type == RewardLikelihood.NORMAL:
                return _update_arm_normal(
                    current_mu=np.array(arm.mu),
                    current_covariance=np.array(arm.covariance),
                    reward=rewards[0],
                    llhood_sigma=1.0,  # TODO: Assuming a fixed likelihood sigma
                    context=np.array(context),
                )
            # TODO: only supports Bernoulli likelihood
            else:
                return _update_arm_laplace(
                    current_mu=np.array(arm.mu),
                    current_covariance=np.array(arm.covariance),
                    reward=np.array(rewards),
                    context=np.array(context),
                    link_function=ContextLinkFunctions.LOGISTIC,
                    reward_likelihood=experiment.reward_type,
                    prior_type=experiment.prior_type,
                )
        else:
            raise ValueError("Unsupported prior type for arm update.")
