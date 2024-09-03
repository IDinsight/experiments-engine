from pydantic import BaseModel, Field


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


class Experiment(BaseModel):
    """
    Pydantic model for an experiment.
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
    arms: list[Arm]


class ExperimentResponse(BaseModel):
    """
    Pydantic model for an response for experiment creation
    """

    experiment_id: int
    arm_ids: list[int]
