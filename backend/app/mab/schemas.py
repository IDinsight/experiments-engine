from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


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
    alpha_prior: int = Field(
        description="The alpha parameter of the beta distribution.",
        examples=[1, 10, 100],
    )
    beta_prior: int = Field(
        description="The beta parameter of the beta distribution.",
        examples=[1, 10, 100],
    )
    successes: int = Field(
        description="The number of successes for the arm.",
        examples=[0, 10, 100],
        default=0,
    )
    failures: int = Field(
        description="The number of failures for the arm.",
        examples=[0, 10, 100],
        default=0,
    )
    model_config = ConfigDict(from_attributes=True)


class ArmResponse(Arm):
    """
    Pydantic model for an response for arm creation
    """

    arm_id: int

    model_config = ConfigDict(from_attributes=True)


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
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class MultiArmedBandit(MultiArmedBanditBase):
    """
    Pydantic model for an experiment.
    """

    arms: list[Arm]

    model_config = ConfigDict(from_attributes=True)


class MultiArmedBanditResponse(MultiArmedBanditBase):
    """
    Pydantic model for an response for experiment creation.
    Returns the id of the experiment and the arms
    """

    experiment_id: int
    arms: list[ArmResponse]

    model_config = ConfigDict(from_attributes=True)


class Outcome(str, Enum):
    """
    Enum for the outcome of a trial.
    """

    SUCCESS = "success"
    FAILURE = "failure"
