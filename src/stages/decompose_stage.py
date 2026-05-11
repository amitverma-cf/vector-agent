"""Decomposition stage: plan semantic components with relative boxes."""

from src.models.schema import Brief, ComponentPlan, CompositionPlan


def decompose_stage(brief: Brief, plan: CompositionPlan, llm_client=None) -> ComponentPlan:
    if llm_client is None:
        raise RuntimeError("LLM client is required for decompose_stage")

    system_prompt = f"""You are the decomposition agent for a static SVG vector compiler.
Decompose only the parts needed for: {brief.subject}

Every component must be kind="component" and include:
- id: valid SVG id, unique, stable, descriptive
- name
- parent_id: another component id or null
- role: primary_surface, secondary_surface, outline, accent, highlight, shadow, glow, detail_line, background_fill
- priority: high, medium, low
- render_intent: rendered or container

Do not assign layout boxes here.
Use as many components as the design needs for recognizability, editability, and clarity.
Prefer fewer semantic components for simple symbols and richer component trees for complex subjects.
Use container only for organizational parent nodes that should not directly draw a visible shape.
Do not include unsupported fields.
"""

    user_prompt = f"Composition plan: {plan.model_dump()}\nDecompose {brief.subject} as a {brief.output_type.value}."
    return llm_client.generate_model(system_prompt, user_prompt, ComponentPlan)
