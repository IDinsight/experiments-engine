from typing import Any, Optional

from pydantic import BaseModel

from ..experiments.schemas import ExperimentsEnum


class ExperimentAIGenerateRequest(BaseModel):
    """Request model for experiment generation."""

    goal: str
    outcome: str
    num_variants: int


class ExperimentAIGenerateResponse(BaseModel):
    """Response model for experiment generation."""

    name: str
    description: str
    experiment_type: str


class baysABArmsSuggestionRequest(BaseModel):
    """Request model for Bayesian A/B arms suggestion."""

    name: str
    description: str
    methodType: ExperimentsEnum
    goal: str
    outcome: str
    numVariants: int
    reward_type: str


class CompleteExperimentResponse(BaseModel):
    """Response model for complete experiment generation."""

    name: str
    description: str
    experiment_type: str
    arms: list[dict[str, Any]]
    contexts: Optional[list[dict[str, Any]]] = None


class MABArmsSuggestionRequest(BaseModel):
    """Request model for MAB arms suggestion."""

    name: str
    description: str
    methodType: ExperimentsEnum
    goal: str
    outcome: str
    numVariants: int
    prior_type: str
    reward_type: str


class CMABContextSuggestionRequest(BaseModel):
    """Request model for CMAB context suggestion."""

    name: str
    description: str
    methodType: ExperimentsEnum
    goal: str
    outcome: str
    numVariants: int
    prior_type: str
    reward_type: str


class CMABArmContext(BaseModel):
    """Model for CMAB arm context."""

    name: str
    description: str
    value_type: str


class CMABArmsSuggestionRequest(BaseModel):
    """Request model for CMAB arms suggestion."""

    name: str
    description: str
    methodType: ExperimentsEnum
    goal: str
    outcome: str
    numVariants: int
    prior_type: str
    reward_type: str
    contexts: list[CMABArmContext]
