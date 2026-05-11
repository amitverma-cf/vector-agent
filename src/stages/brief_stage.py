"""Brief stage: convert the user prompt into a typed design brief."""

from src.models.schema import Brief


BRIEF_SYSTEM_PROMPT = """You are the brief agent for a static SVG vector compiler.
Return a complete Brief object.

Required values:
- output_type: icon, sticker, badge, emblem
- style_recipe: flat, sticker, monochrome, neon
- background: transparent, solid_light, solid_dark
- detail_level: low, medium, high
- palette_hint: cool, warm, neutral, vibrant, muted

Do not include unsupported enum values. Do not invent placeholder notes.
"""


def brief_stage(prompt: str, llm_client=None) -> Brief:
    if llm_client is None:
        raise RuntimeError("LLM client required")
    return llm_client.generate_model(BRIEF_SYSTEM_PROMPT, prompt, Brief)
