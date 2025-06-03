# Bayesian A/B Testing

Bayesian A/B testing compares two variants: treatment (e.g. a new feature) and control (e.g. an existing feature). This is a useful experiment when you need intuitive probability statements about which arm is better for making downstream decisions, and have the resources to balance how your arms are allocated to your experimental cohort. Choose this over the bandit algorithms when you're trying to make a "permanent" decision about which variant is better, as opposed to trying to dynamically pick the best performing variant as data comes in.

## What is Bayesian A/B testing?

With A/B testing, you have 2 variants of a feature / implementation (one is ideally a baseline / existing feature that you want to compare the other, a new feature, against). We currently implement only 2 arms for the experiment. You present users with one of the variants at a random but with a _fixed_ probability throughout the experiment and observe the outcome of their interaction with it.
Unlike frequentist A/B testing, this method lets you set prior probabilities for the treatment and control arms, similarly to the bandit experiments.
However, unlike the bandit methods, the posterior is computed at the _end_ of the experiment, and not with every observed outcome.

## Show me some math!
In our current implementation of Bayesian A/B testing, we use Gaussian priors and support either real-valued or binary outcomes.

The outcome $y$ has a likelihood distribution given by:
$$
\begin{equation}
y \sim p(f(w_{\text{treatment}}\ \mathbb{I}(\text{treatment})\ +\ w_{\text{control}}\ \mathbb{I}(\text{control})\ +\ \text{bias}))
\end{equation}
$$
where $w_{\text{treatment}}$ and $w_{\text{control}}$ denote the treatment and control effect respectively. If $y$ were binary-valued, $p$ denotes the Bernoulli distribution, and $f$ the sigmoid function. For real-valued $y$, $p$ is a Gaussian distribution, $f$ is the identity function.

We also assume Gaussian priors for $w_{\text{treatment}}$ and $w_{\text{control}}$:

$$
\begin{equation}
w_{(\cdot)} \sim \mathcal{N} (\mathbf{\mu}_{(\cdot)}, \Sigma_{(\cdot)})
\end{equation}
$$

During the course of the experiment, we choose the variant to present to the user with 50% probability for either arm.

Once we have observed all the outcomes $[y]_{j=1}^M$, we can obtain the posterior distribution for the treatment and control arms using the Laplace approximation i.e. the log likelihood can be written down as follows:

$$
\begin{align*}
\log \mathcal{L} &= \sum_{j=1}^M \log p(y_j | f(w_{\text{treatment}}\ \mathbb{I}(\text{treatment})\ +\ w_{\text{control}}\ \mathbb{I}(\text{control})\ +\ \text{bias})) \\
\end{align*}
$$

Then we calculate:

$$
\begin{align*}
\mu_i^{\text(post)} &= \theta_i^* = \underset{\theta_i}{\text{argmax}} \log \mathcal{L}  \\
(\Sigma_i^{\text{post}})^{-1} &= (\Sigma_i^*)^{-1} = \frac{d^2}{d\theta_i^2} \log \mathcal{L} \ \bigg|_{\theta_i^*}
\end{align*}
$$

We obtain the posterior parameters at the _end_ of the experiment, by using MAPE[^1] with the joint likelihood of all the observations.

Next, we'll walk you through [setting up the experiment](./setting-up.md).


## Additional Resources

1. [Bayesian A/B testing](https://www.youtube.com/watch?v=nRLI_KbvZTQ)

2. [The Bayesian Approach to A/B Testing](https://www.dynamicyield.com/lesson/bayesian-approach-to-ab-testing/)

[^1]: Maximum a posteriori estimation (MAPE) is a method for estimating parameter valuess based on empirical data. It's similar to maximum likelihood estimation (MLE) but incorporates prior beliefs about the parameters.
