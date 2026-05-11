"""Composition planning stage."""

from src.models.schema import Brief, CompositionPlan


def plan_stage(brief: Brief, llm_client=None) -> CompositionPlan:
    if llm_client is None:
        raise RuntimeError("LLM client required")

    system_prompt = """You are the composition planner for a static SVG vector compiler.
Reason about what the image needs before any component decomposition.
Let the subject determine the component set naturally.
Decide the visual strategy from the subject, output type, style, background, and detail level.
Identify only the parts that are visually necessary, plus optional details that can improve recognizability.
"""
    user_prompt = f"Plan this vector graphic brief: {brief.model_dump()}"
    return llm_client.generate_model(system_prompt, user_prompt, CompositionPlan)
