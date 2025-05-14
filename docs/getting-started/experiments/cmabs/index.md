# Contextual Bandits
Contextual bandits (CMABs), similarly to [multi-armed bandits (MABs)](../mabs/index.md), are useful for running experiments where you have multiple variants of a feature / implementation that you want to test. However, the key difference is that contextual bandits take information about the end-user (e.g. gender, age, engagement history) into account while converging to the best-performing variant.

## What are Contextual Bandits (CMABs)?
Contextual bandits work more or less in the same way as MABs do. You have $N$ variants of a feature / implementation, with corresponding probability of achieving a desired outcome. As you serve beneficiaries these variants and observe the outcome of their interaction with it, you update these probabilities.

The strategy for updating these probabilities is also similar. The crucial difference is that we take user information into account while updating these probabilities for contextual bandits. Thus, rather than having a single best-performing variant at the end of an experiment, you instead have the best-performing variant that depends on the user context.


## Show me some math!
In our current implementation of CMABs, we use Gaussian priors and support either real-valued or binary outcomes. We also allow for either real-valued or binary context values.

Given $N$ variants of a feature or implementation, and assuming that context for a user is captured by a vector $\mathbf{x}$, the outcome $y$ has a likelihood distribution given by:
$$
\begin{equation}
y \sim p(f(\theta_i \cdot \mathbf{x}))
\end{equation}
$$
If $y$ where binary-values, $p$ denotes the Bernoulli distribution, $f$ the sigmoid function and $\theta_i \cdot \mathbf{x}$ the log odds of the outcome $y$ under variant $i (= 1, \ldots .N)$, dependent on the user context $\mathbf{x}$.

Similarly, for real-valued $y$, $p$ is a Gaussian distribution, $f$ is the identity function, and $\theta_i \cdot \mathbf{x}$ is the mean of the Gaussian distribution (we assume the variance to be 1 currently).

We also assume multi-variate Gaussian priors for $\theta_i$:
$$
\begin{equation}
\theta_i \sim \mathcal{N} (\mathbf{\mu}_i, \Sigma_i^{-1})
\end{equation}
$$

While configuring the experiment, we require users to set a _scalar_ value of mean $m_i$ and standard deviation $\sigma_i$, which we then expand into vector mean $\mu_i = \begin{bmatrix} 1 \\ 1 \end{bmatrix} \cdot m_i$ and diagonal covariance matrix $\Sigma = \begin{bmatrix} \sigma_i & 0 \\ 0 & \sigma_i \end{bmatrix}$.

During the course of the experiment, we choose the variant $j$ to present to the user using Thompson sampling, dependent on the user's input context $\mathbf{x}$:
$$
\begin{equation}
j = \text{argmax}\ \[ f(\theta_i \cdot \mathbf{x}\]^N_{i = 1}
\end{equation}
$$
after sampling $\theta_i$ from the corresponding Gaussian distribution.

Once we have observed an outcome $y$ for a given variant and user context $\mathbf{x}$, we can obtain the posterior distribution for that variant. In the case of the real-valued outcomes, the likelihood and priors are conjugate, so the update is straightforward update: i.e. given an observation $y$,
$$
  {\Sigma }^{(\text{post})}_i = (\Sigma_i + \mathbf{x}^T \mathbf{x}) ^ {-1}
$$
$$
  \mu^{(\text{post})}_i = \Sigma^{\text{post}}_i \big(\Sigma_i^{-1} \mu_i + \mathbf{x}\ y \big)
$$
$$
\begin{equation}
  \theta^{(\text{post})}_i \sim N (\mu^{(\text{post})}_i, (\sigma^{(\text{post})}_i)^2)
\end{equation}
$$
This is now the new prior from which we sample while choosing variants or arms to serve the user.

## Laplace approximation for posterior updates with binary outcomes
When the outcome $y$ is binary valued (and therefore has a Bernoulli likelihood), the Gaussian priors for $\theta_i$ and the likelihood are non-conjugate. This means that we cannot update the posteriors in closed form as in the equations above.

We will instead use the Laplace approximation i.e. we will _assume_ that the posterior distribution is a Gaussian whose mean is given by the _maximum a posteriori_ (MAP) estimate $\theta_i^*$, and whose covariance is given by the inverse Hessian of the Bernoulli log likelihood, evaluated at $\theta_i^*$ i.e. for $M$ context-observations pairs $\{\mathbf{x}, y\}_{j=1}^M$ the log likelihood can be written down as follows:

$$
\begin{align*}
\log \mathcal{L} &= \sum_{j=1}^M \log p(y_j | f(\theta_i \cdot \mathbf{x}_j)) \\
&= \sum_j y_j \log(\theta_i \cdot \mathbf{x}_j) + (1 - y_j) \log (1 - \theta_i \cdot \mathbf{x}_j)
\end{align*}
$$

Then we calculate:

$$
\begin{align*}
\mu_i^{\text(post)} &= \theta_i^* = \underset{\theta_i}{\text{argmax}} \log \mathcal{L}  \\
(\Sigma_i^{\text{post}})^{-1} &= (\Sigma_i^*)^{-1} = \frac{d^2}{d\theta_i^2} \log \mathcal{L} \ \bigg|_{\theta_i^*}
\end{align*}
$$

We update these parameters by repeating the MAP estimation every time a new outcome is logged.

Next, we'll show you how to [set up the CMAB](./setting-up.md), and configure the contexts and outcomes.

### Addiitional Resources
You can learn more about contextual bandits from the following resources:

1. [Contextual Bandits](https://www.youtube.com/watch?v=JmbEheH7gVw&pp=ygUSY29udGV4dHVhbCBiYW5kaXRz)

2. [Reinforcement Learning: An Introduction, Sutton and Barto, Chapter 2, Section 2.9](http://www.incompleteideas.net/book/RLbook2020.pdf)
