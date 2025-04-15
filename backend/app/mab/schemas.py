from datetime import datetime
from typing import Optional, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..schemas import (
    ArmPriors,
    Notifications,
    NotificationsResponse,
    RewardLikelihood,
    allowed_combos_mab,
)


class Arm(BaseModel):
    """
    Pydantic model for a arm of the experiment.
    """

    name: str = Field(
        max_length=150,
        examples=["Arm 1"],
    )
    description: str = Field(
        max_length=500,
        examples=["This is a description of the arm."],
    )

    # prior variables
    alpha: Optional[float] = Field(
        default=None, examples=[None, 1.0], description="Alpha parameter for Beta prior"
    )
    beta: Optional[float] = Field(
        default=None, examples=[None, 1.0], description="Beta parameter for Beta prior"
    )
    mu: Optional[float] = Field(
        default=None,
        examples=[None, 0.0],
        description="Mean parameter for Normal prior",
    )
    sigma: Optional[float] = Field(
        default=None,
        examples=[None, 1.0],
        description="Standard deviation parameter for Normal prior",
    )
    n_outcomes: Optional[int] = Field(
        default=0,
        description="Number of outcomes for the arm",
        examples=[0, 10, 15],
    )

    @model_validator(mode="after")
    def check_values(self) -> Self:
        """
        Check if the values are unique.
        """
        alpha = self.alpha
        beta = self.beta
        sigma = self.sigma
        if alpha is not None and alpha <= 0:
            raise ValueError("Alpha must be greater than 0.")
        if beta is not None and beta <= 0:
            raise ValueError("Beta must be greater than 0.")
        if sigma is not None and sigma <= 0:
            raise ValueError("Sigma must be greater than 0.")
        return self


class ArmResponse(Arm):
    """
    Pydantic model for an response for arm creation
    """

    arm_id: int
    model_config = ConfigDict(
        from_attributes=True,
    )


class MultiArmedBanditBase(BaseModel):
    """
    Pydantic model for an experiment - Base model.
    Note: Do not use this model directly. Use `MultiArmedBandit` instead.
    """

    name: str = Field(
        max_length=150,
        examples=["Experiment 1"],
    )

    description: str = Field(
        max_length=500,
        examples=["This is a description of the experiment."],
    )

    reward_type: RewardLikelihood = Field(
        description="The type of reward we observe from the experiment.",
        default=RewardLikelihood.BERNOULLI,
    )
    prior_type: ArmPriors = Field(
        description="The type of prior distribution for the arms.",
        default=ArmPriors.BETA,
    )

    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class MultiArmedBandit(MultiArmedBanditBase):
    """
    Pydantic model for an experiment.
    """

    arms: list[Arm]
    notifications: Notifications

    @model_validator(mode="after")
    def arms_at_least_two(self) -> Self:
        """
        Validate that the experiment has at least two arms.
        """
        if len(self.arms) < 2:
            raise ValueError("The experiment must have at least two arms.")
        return self

    @model_validator(mode="after")
    def check_prior_reward_type_combo(self) -> Self:
        """
        Validate that the prior and reward type combination is allowed.
        """

        if (self.prior_type, self.reward_type) not in allowed_combos_mab:
            raise ValueError("Prior and reward type combo not supported.")
        return self

    @model_validator(mode="after")
    def check_arm_missing_params(self) -> Self:
        """
        Check if the arm reward type is same as the experiment reward type.
        """
        prior_type = self.prior_type
        arms = self.arms

        prior_params = {
            ArmPriors.BETA: ("alpha", "beta"),
            ArmPriors.NORMAL: ("mu", "sigma"),
        }

        for arm in arms:
            arm_dict = arm.model_dump()
            if prior_type in prior_params:
                missing_params = []
                for param in prior_params[prior_type]:
                    if param not in arm_dict.keys():
                        missing_params.append(param)
                    elif arm_dict[param] is None:
                        missing_params.append(param)

                if missing_params:
                    val = prior_type.value
                    raise ValueError(f"{val} prior needs {','.join(missing_params)}.")
        return self

    model_config = ConfigDict(from_attributes=True)


class MultiArmedBanditResponse(MultiArmedBanditBase):
    """
    Pydantic model for an response for experiment creation.
    Returns the id of the experiment and the arms
    """

    experiment_id: int
    arms: list[ArmResponse]
    notifications: list[NotificationsResponse]
    created_datetime_utc: datetime
    last_trial_datetime_utc: Optional[datetime] = None
    n_trials: int
    model_config = ConfigDict(from_attributes=True, revalidate_instances="always")


class MultiArmedBanditSample(MultiArmedBanditBase):
    """
    Pydantic model for an experiment sample.
    """

    experiment_id: int
    arms: list[ArmResponse]


class MABObservation(BaseModel):
    """
    Pydantic model for an observation of the experiment.
    """

    experiment_id: int
    arm_id: int
    reward: float

    model_config = ConfigDict(from_attributes=True)


class MABObservationResponse(MABObservation):
    """
    Pydantic model for binary observations of the experiment.
    """

    observation_id: int
    observed_datetime_utc: datetime

    model_config = ConfigDict(from_attributes=True)
