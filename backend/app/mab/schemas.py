from pydantic import BaseModel, Field, ConfigDict


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
    alpha: int = Field(
        description="The alpha parameter of the beta distribution.",
        examples=[1, 10, 100],
    )
    beta: int = Field(
        description="The beta parameter of the beta distribution.",
        examples=[1, 10, 100],
    )


class ArmResponse(Arm):
    """
    Pydantic model for an response for arm creation
    """

    arm_id: int

    model_config = ConfigDict(from_attributes=True)


class MultiArmedBandit(BaseModel):
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


class MultiArmedBanditResponse(BaseModel):
    """
    Pydantic model for an response for experiment creation
    """

    experiment_id: int
    arm_ids: list[int]
