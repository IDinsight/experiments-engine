from datetime import datetime
from typing import Optional, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..schemas import (
    ArmPriors,
    AutoFailUnitType,
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
    alpha_init: Optional[float] = Field(
        default=None, examples=[None, 1.0], description="Alpha parameter for Beta prior"
    )
    beta_init: Optional[float] = Field(
        default=None, examples=[None, 1.0], description="Beta parameter for Beta prior"
    )
    mu_init: Optional[float] = Field(
        default=None,
        examples=[None, 0.0],
        description="Mean parameter for Normal prior",
    )
    sigma_init: Optional[float] = Field(
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
        alpha = self.alpha_init
        beta = self.beta_init
        sigma = self.sigma_init
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
    alpha: Optional[float]
    beta: Optional[float]
    mu: Optional[float]
    sigma: Optional[float]
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

    sticky_assignment: bool = Field(
        description="Whether the arm assignment is sticky or not.",
        default=False,
    )

    auto_fail: bool = Field(
        description=(
            "Whether the experiment should fail automatically after "
            "a certain period if no outcome is registered."
        ),
        default=False,
    )

    auto_fail_value: Optional[int] = Field(
        description="The time period after which the experiment should fail.",
        default=None,
    )

    auto_fail_unit: Optional[AutoFailUnitType] = Field(
        description="The time unit for the auto fail period.",
        default=None,
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
    def auto_fail_unit_and_value_set(self) -> Self:
        """
        Validate that the auto fail unit and value are set if auto fail is True.
        """
        if self.auto_fail:
            if (
                not self.auto_fail_value
                or not self.auto_fail_unit
                or self.auto_fail_value <= 0
            ):
                raise ValueError(
                    (
                        "Auto fail is enabled. "
                        "Please provide both auto_fail_value and auto_fail_unit."
                    )
                )
        return self

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
            ArmPriors.BETA: ("alpha_init", "beta_init"),
            ArmPriors.NORMAL: ("mu_init", "sigma_init"),
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
    workspace_id: int
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


class MABObservationResponse(BaseModel):
    """
    Pydantic model for binary observations of the experiment.
    """

    experiment_id: int
    arm_id: int
    reward: float
    draw_id: str
    client_id: str | None
    observed_datetime_utc: datetime

    model_config = ConfigDict(from_attributes=True)


class MABDrawResponse(BaseModel):
    """
    Pydantic model for the response of the draw endpoint.
    """

    draw_id: str
    client_id: str | None
    arm: ArmResponse
