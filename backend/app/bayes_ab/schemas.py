from datetime import datetime
from typing import Optional, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..mab.schemas import (
    MABObservationResponse,
    MultiArmedBanditBase,
)
from ..schemas import Notifications, NotificationsResponse, allowed_combos_bayes_ab


class BayesABArm(BaseModel):
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

    mu_init: float = Field(
        default=0.0, description="Mean parameter for treatment effect prior"
    )
    sigma_init: float = Field(
        default=1.0, description="Std dev parameter for treatment effect prior"
    )
    n_outcomes: Optional[int] = Field(
        default=0,
        description="Number of outcomes for the arm",
        examples=[0, 10, 15],
    )
    is_treatment_arm: bool = Field(
        default=True,
        description="Is the arm a treatment arm",
        examples=[True, False],
    )

    @model_validator(mode="after")
    def check_values(self) -> Self:
        """
        Check if the values are unique and set new attributes.
        """
        if self.sigma_init is not None and self.sigma_init <= 0:
            raise ValueError("Std dev must be greater than 0.")
        return self

    model_config = ConfigDict(from_attributes=True)


class BayesABArmResponse(BayesABArm):
    """
    Pydantic model for a response for contextual arm creation
    """

    arm_id: int
    mu: float
    sigma: float
    model_config = ConfigDict(from_attributes=True)


class BayesianAB(MultiArmedBanditBase):
    """
    Pydantic model for an A/B experiment.
    """

    arms: list[BayesABArm]
    notifications: Notifications
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def arms_exactly_two(self) -> Self:
        """
        Validate that the experiment has exactly two arms.
        """
        if len(self.arms) != 2:
            raise ValueError("The experiment must have at exactly two arms.")
        return self

    @model_validator(mode="after")
    def check_prior_reward_type_combo(self) -> Self:
        """
        Validate that the prior and reward type combination is allowed.
        """

        if (self.prior_type, self.reward_type) not in allowed_combos_bayes_ab:
            raise ValueError("Prior and reward type combo not supported.")
        return self

    @model_validator(mode="after")
    def check_treatment_and_control_arm(self) -> Self:
        """
        Validate that the experiment has at least one control arm.
        """
        if sum(arm.is_treatment_arm for arm in self.arms) != 1:
            raise ValueError("The experiment must have one treatment and control arm.")
        return self


class BayesianABResponse(MultiArmedBanditBase):
    """
    Pydantic model for a response for an A/B experiment.
    """

    experiment_id: int
    arms: list[BayesABArmResponse]
    notifications: list[NotificationsResponse]
    created_datetime_utc: datetime
    last_trial_datetime_utc: Optional[datetime] = None
    n_trials: int

    model_config = ConfigDict(from_attributes=True)


class BayesianABSample(MultiArmedBanditBase):
    """
    Pydantic model for a sample A/B experiment.
    """

    experiment_id: int
    arms: list[BayesABArmResponse]


class BayesianABObservationResponse(MABObservationResponse):
    """
    Pydantic model for an observation response in an A/B experiment.
    """

    pass


class BayesianABDrawResponse(BaseModel):
    """
    Pydantic model for a draw response in an A/B experiment.
    """

    draw_id: str
    arm: BayesABArmResponse
