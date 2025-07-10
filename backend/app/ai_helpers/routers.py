import json
import os
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel

router = APIRouter(prefix="/ai_helpers", tags=["AI Helpers"])


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
    methodType: str
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
    methodType: str
    goal: str
    outcome: str
    numVariants: int
    prior_type: str
    reward_type: str


class CMABContextSuggestionRequest(BaseModel):
    """Request model for CMAB context suggestion."""

    name: str
    description: str
    methodType: str
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
    methodType: str
    goal: str
    outcome: str
    numVariants: int
    prior_type: str
    reward_type: str
    contexts: list[CMABArmContext]


api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise HTTPException(status_code=500, detail="Gemini API key not set")

client = genai.Client(api_key=api_key)


@router.post("/suggestBaysAB-arms")
async def suggest_arms(
    request: baysABArmsSuggestionRequest,
) -> list[dict[str, Any]]:
    """Suggest arms for Bayesian A/B test."""
    # System instruction for arms suggestion
    system_instruction = (
        "You are an assistant for a tool that helps social sector "
        "organizations run digital experiments.\n"
        "Given the experiment details below, suggest concise names and "
        "descriptions for each arm (variant) of the experiment.\n"
        "For Bayesian A/B tests, there are usually two arms: a control "
        "(existing/baseline) and a treatment (new/changed feature). "
        "For other experiment types, use the number of variants provided.\n"
        "For each arm, also suggest reasonable initial values for mu_init "
        "(mean prior, between 0 and 1 for rates) and sigma_init "
        "(standard deviation).\n"
        "Respond ONLY with a valid JSON array. Each array element should be "
        "an object with keys: name, description, mu_init, sigma_init. "
        "No explanation, no markdown."
    )

    user_prompt = (
        f"Experiment details:\n"
        f"- Name: {request.name}\n"
        f"- Description: {request.description}\n"
        f"- Method type: {request.methodType}\n"
        f"- Goal: {request.goal}\n"
        f"- Outcome: {request.outcome}\n"
        f"- Number of variants: {request.numVariants}\n"
        f"- Reward type: {request.reward_type}\n"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=500,
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {e}") from e


@router.post("/suggestMAB-arms")
async def suggest_mab_arms(
    request: MABArmsSuggestionRequest,
) -> list[dict[str, Any]]:
    """Suggest arms for Multi-Armed Bandit experiment."""
    system_instruction = (
        "You are an assistant for a tool that helps social sector "
        "organizations run digital experiments.\n"
        "Given the experiment details below, suggest concise names and "
        "descriptions for each arm (variant) of the experiment.\n"
        "For multi-armed bandit (MAB) experiments, use the number of "
        "variants provided.\n"
        "For each arm, also suggest reasonable initial values for alpha_init "
        "and beta_init (for beta prior) or mu_init and sigma_init "
        "(for normal prior), depending on the prior_type.\n"
        "Respond ONLY with a valid JSON array. Each array element should be "
        "an object with keys: name, description, and the appropriate prior "
        "parameters. No explanation, no markdown."
    )

    user_prompt = (
        f"Experiment details:\n"
        f"- Name: {request.name}\n"
        f"- Description: {request.description}\n"
        f"- Method type: {request.methodType}\n"
        f"- Goal: {request.goal}\n"
        f"- Outcome: {request.outcome}\n"
        f"- Number of variants: {request.numVariants}\n"
        f"- Prior type: {request.prior_type}\n"
        f"- Reward type: {request.reward_type}\n"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=500,
                temperature=0.9,
                response_mime_type="application/json",
            ),
        )
        print(response.text)
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {e}") from e


@router.post("/suggestCMAB-contexts")
async def suggest_cmab_contexts(
    request: CMABContextSuggestionRequest,
) -> list[dict[str, Any]]:
    """Suggest contexts for Contextual Multi-Armed Bandit experiment."""
    system_instruction = (
        "You are an assistant for a tool that helps social sector "
        "organizations run digital experiments.\n"
        "Given the experiment details below, suggest relevant user contexts "
        "for a Contextual Bandit (CMAB) experiment.\n"
        "Contexts are user attributes (e.g., age, location, engagement level) "
        "that might influence how they respond to different variants.\n"
        "For each context, provide a concise 'name', a 'description', and "
        "a 'value_type' ('binary' or 'real-valued').\n"
        "Respond ONLY with a valid JSON array. Each array element should be "
        "an object with keys: name, description, value_type. No explanation, "
        "no markdown."
    )

    user_prompt = (
        f"Experiment details:\n"
        f"- Name: {request.name}\n"
        f"- Description: {request.description}\n"
        f"- Method type: {request.methodType}\n"
        f"- Goal: {request.goal}\n"
        f"- Outcome: {request.outcome}\n"
        f"- Number of variants: {request.numVariants}\n"
        f"- Prior type: {request.prior_type}\n"
        f"- Reward type: {request.reward_type}\n"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=500,
                temperature=0.7,
                response_mime_type="application/json",
            ),
        )
        print(response.text)
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {e}") from e


@router.post("/suggestCMAB-arms")
async def suggest_cmab_arms(
    request: CMABArmsSuggestionRequest,
) -> list[dict[str, Any]]:
    """Suggest arms for Contextual Multi-Armed Bandit experiment."""
    system_instruction = (
        "You are an assistant for a tool that helps social sector "
        "organizations run digital experiments.\n"
        "Given the experiment details and user contexts below, suggest "
        "concise names and descriptions for each arm (variant) of a "
        "Contextual Bandit (CMAB) experiment.\n"
        "The arms should be distinct variations of a feature that is being "
        "tested.\n"
        "For each arm, also suggest reasonable initial values for mu_init "
        "(mean prior) and sigma_init (standard deviation prior).\n"
        "Respond ONLY with a valid JSON array. Each array element should be "
        "an object with keys: name, description, mu_init, sigma_init. "
        "No explanation, no markdown."
    )

    contexts_str = "\n".join(
        [f"- {c.name} ({c.value_type}): {c.description}" for c in request.contexts]
    )

    user_prompt = (
        f"Experiment details:\n"
        f"- Name: {request.name}\n"
        f"- Description: {request.description}\n"
        f"- Method type: {request.methodType}\n"
        f"- Goal: {request.goal}\n"
        f"- Outcome: {request.outcome}\n"
        f"- Number of variants: {request.numVariants}\n"
        f"- Prior type: {request.prior_type}\n"
        f"- Reward type: {request.reward_type}\n"
        f"User Contexts:\n{contexts_str}\n"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=500,
                temperature=0.7,
                response_mime_type="application/json",
            ),
        )
        print(response.text)
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {e}") from e


async def generate_experiment_fields_logic(
    data: ExperimentAIGenerateRequest,
) -> ExperimentAIGenerateResponse:
    """Generate experiment name, description, and type based on user inputs."""
    try:
        system_instruction = (
            "You are an assistant for a tool that helps social sector "
            "organizations run digital experiments.\n"
            "Below are documentation excerpts about different experiment "
            "types. Use this context to choose the most appropriate "
            "experiment type and generate relevant names and descriptions.\n"
            "-----\n"
            "# Bayesian A/B Testing\n"
            "Bayesian A/B testing compares two variants: treatment (e.g. a "
            "new feature) and control (e.g. an existing feature). This is a "
            "useful experiment when you need intuitive probability statements "
            "about which arm is better for making downstream decisions, and "
            "have the resources to balance how your arms are allocated to "
            "your experimental cohort. Choose this over the bandit algorithms "
            "when you're trying to make a 'permanent' decision about which "
            "variant is better, as opposed to trying to dynamically pick the "
            "best performing variant as data comes in.\n"
            "With A/B testing, you have 2 variants of a feature / "
            "implementation (one is ideally a baseline / existing feature "
            "that you want to compare the other, a new feature, against). "
            "You present users with one of the variants at a random but with "
            "a fixed probability throughout the experiment and observe the "
            "outcome of their interaction with it. Unlike frequentist A/B "
            "testing, this method lets you set prior probabilities for the "
            "treatment and control arms, similarly to the bandit experiments. "
            "However, unlike the bandit methods, the posterior is computed at "
            "the end of the experiment, and not with every observed outcome.\n"
            "-----\n"
            "# Contextual Bandits (CMABs)\n"
            "Contextual bandits (CMABs), similarly to multi-armed bandits "
            "(MABs), are useful for running experiments where you have "
            "multiple variants of a feature / implementation that you want to "
            "test. However, the key difference is that contextual bandits "
            "take information about the end-user (e.g. gender, age, "
            "engagement history) into account while converging to the "
            "best-performing variant. The crucial difference is that we take "
            "user information into account while updating these probabilities "
            "for contextual bandits. Thus, rather than having a single "
            "best-performing variant at the end of an experiment, you instead "
            "have the best-performing variant that depends on the user "
            "context.\n"
            "-----\n"
            "# Multi-Armed Bandits (MABs)\n"
            "Multi-armed Bandits (MABs) are useful for running experiments "
            "where you have multiple variants of a feature / implementation "
            "that you want to test, and want to automatically converge to "
            "the variant that produces the best results. MABs are a "
            "specialized reinforcement learning algorithm: let's imagine that "
            "you have set up N variants of an experiment, and for each "
            "variant you have some prior probability of a desired result. "
            "You serve each of your users one of these variants (the strategy "
            "for choosing the variant is based on the prior probabilities), "
            "and observe the result of their interaction with it. Once you "
            "have observed the result, the algorithm updates your arm / "
            "variant's probability of achieving the desired result. The next "
            "time you serve a user one of the variants, the experiments "
            "engine uses these updated probabilities to determine which "
            "variant to show them. Since we update the probabilities for the "
            "variants with every result observation, at any given time you "
            "can observe the updated probability of success for every arm. "
            "The best-performing variant at the end of the experiment is the "
            "one with the highest probability.\n"
            "-----\n"
            "Given a goal, outcome, and number of variants, generate:\n"
            "1. A concise and descriptive experiment name (max 8 words).\n"
            "2. A detailed description of the experiment.\n"
            "3. The most appropriate experiment type: 'mab' (multi-armed "
            "bandit), 'bayes_ab' (Bayesian A/B test), or 'cmab' "
            "(contextual bandit).\n"
            "Respond ONLY with a valid JSON object with keys: name, "
            "description, experiment_type. No explanation, no markdown."
        )
        user_prompt = (
            f"User inputs:\n"
            f"- Goal: {data.goal}\n"
            f"- Outcome: {data.outcome}\n"
            f"- Number of variants: {data.num_variants}\n"
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=500,
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=ExperimentAIGenerateResponse,
            ),
        )

        response_data = json.loads(response.text)
        return ExperimentAIGenerateResponse(**response_data)

    except Exception as e:
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

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating complete experiment: {e}"
        ) from e
