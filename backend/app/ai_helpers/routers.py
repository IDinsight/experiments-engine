import json
import os
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from google import api_core, genai
from google.genai import types

from . import prompts
from .schemas import (
    CMABArmContext,
    CMABArmsSuggestionRequest,
    CMABContextSuggestionRequest,
    CompleteExperimentResponse,
    ExperimentAIGenerateRequest,
    ExperimentAIGenerateResponse,
    MABArmsSuggestionRequest,
    baysABArmsSuggestionRequest,
)

router = APIRouter(prefix="/ai_helpers", tags=["AI Helpers"])


api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

client = genai.Client(api_key=api_key)


@router.post("/suggestBaysAB-arms")
async def suggest_arms(
    request: baysABArmsSuggestionRequest,
) -> list[dict[str, Any]]:
    """Suggest arms for Bayesian A/B test."""

    user_prompt = request.model_dump_json()

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=prompts.SUGGEST_BAYS_AB_ARMS,
                max_output_tokens=500,
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except api_core.exceptions.GoogleAPICallError as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {e}") from e


@router.post("/suggestMAB-arms")
async def suggest_mab_arms(
    request: MABArmsSuggestionRequest,
) -> list[dict[str, Any]]:
    """Suggest arms for Multi-Armed Bandit experiment."""

    user_prompt = request.model_dump_json()

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=prompts.SUGGEST_MAB_ARMS,
                max_output_tokens=500,
                temperature=0.9,
                response_mime_type="application/json",
            ),
        )
        print(response.text)
        return json.loads(response.text)
    except api_core.exceptions.GoogleAPICallError as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {e}") from e


@router.post("/suggestCMAB-contexts")
async def suggest_cmab_contexts(
    request: CMABContextSuggestionRequest,
) -> list[dict[str, Any]]:
    """Suggest contexts for Contextual Multi-Armed Bandit experiment."""

    user_prompt = request.model_dump_json()

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=prompts.SUGGEST_CMAB_CONTEXTS,
                max_output_tokens=500,
                temperature=0.7,
                response_mime_type="application/json",
            ),
        )
        print(response.text)
        return json.loads(response.text)
    except api_core.exceptions.GoogleAPICallError as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {e}") from e


@router.post("/suggestCMAB-arms")
async def suggest_cmab_arms(
    request: CMABArmsSuggestionRequest,
) -> list[dict[str, Any]]:
    """Suggest arms for Contextual Multi-Armed Bandit experiment."""

    user_prompt = request.model_dump_json()

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=prompts.SUGGEST_CMAB_ARMS,
                max_output_tokens=500,
                temperature=0.7,
                response_mime_type="application/json",
            ),
        )
        print(response.text)
        return json.loads(response.text)
    except api_core.exceptions.GoogleAPICallError as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {e}") from e


async def generate_experiment_fields_logic(
    data: ExperimentAIGenerateRequest,
) -> ExperimentAIGenerateResponse:
    """Generate experiment name, description, and type based on user inputs."""
    try:
        user_prompt = data.model_dump_json()

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=prompts.GENERATE_EXPERIMENT_FIELDS,
                max_output_tokens=500,
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=ExperimentAIGenerateResponse,
            ),
        )

        response_data = json.loads(response.text)
        return ExperimentAIGenerateResponse(**response_data)

    except api_core.exceptions.GoogleAPICallError as e:
        raise RuntimeError(f"Gemini API error: {e}") from e


@router.post("/generate-whole-experiment", response_model=CompleteExperimentResponse)
async def generate_whole_experiment(
    data: ExperimentAIGenerateRequest,
) -> CompleteExperimentResponse:
    """Generate a complete experiment configuration."""
    try:
        experiment_fields = await generate_experiment_fields_logic(data)

        arms: list[dict[str, Any]] = []
        contexts: Optional[list[dict[str, Any]]] = None

        if experiment_fields.experiment_type == "bayes_ab":
            # Generate arms for Bayesian A/B test
            bayes_request = baysABArmsSuggestionRequest(
                name=experiment_fields.name,
                description=experiment_fields.description,
                methodType=experiment_fields.experiment_type,
                goal=data.goal,
                outcome=data.outcome,
                numVariants=data.num_variants,
                reward_type="binary",  # Default for A/B tests
            )
            arms = await suggest_arms(bayes_request)

        elif experiment_fields.experiment_type == "mab":
            # Generate arms for Multi-Armed Bandit
            mab_request = MABArmsSuggestionRequest(
                name=experiment_fields.name,
                description=experiment_fields.description,
                methodType=experiment_fields.experiment_type,
                goal=data.goal,
                outcome=data.outcome,
                numVariants=data.num_variants,
                prior_type="beta",  # Default prior type
                reward_type="binary",  # Default reward type
            )
            arms = await suggest_mab_arms(mab_request)

        elif experiment_fields.experiment_type == "cmab":
            # Generate contexts first for Contextual Bandit
            context_request = CMABContextSuggestionRequest(
                name=experiment_fields.name,
                description=experiment_fields.description,
                methodType=experiment_fields.experiment_type,
                goal=data.goal,
                outcome=data.outcome,
                numVariants=data.num_variants,
                prior_type="normal",  # Default prior type
                reward_type="binary",  # Default reward type
            )
            contexts = await suggest_cmab_contexts(context_request)

            # Generate arms for Contextual Bandit
            if contexts is not None:
                cmab_contexts = [CMABArmContext(**ctx) for ctx in contexts]
                cmab_request = CMABArmsSuggestionRequest(
                    name=experiment_fields.name,
                    description=experiment_fields.description,
                    methodType=experiment_fields.experiment_type,
                    goal=data.goal,
                    outcome=data.outcome,
                    numVariants=data.num_variants,
                    prior_type="normal",  # Default prior type
                    reward_type="binary",  # Default reward type
                    contexts=cmab_contexts,
                )
                arms = await suggest_cmab_arms(cmab_request)

        return CompleteExperimentResponse(
            name=experiment_fields.name,
            description=experiment_fields.description,
            experiment_type=experiment_fields.experiment_type,
            arms=arms,
            contexts=contexts,
        )

    except (RuntimeError, api_core.exceptions.GoogleAPICallError) as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating complete experiment: {e}"
        ) from e
