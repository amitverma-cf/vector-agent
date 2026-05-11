"""Capability routing for explicit production support decisions."""

from enum import Enum

from pydantic import BaseModel

from src.models.schema import Brief


class RouteLabel(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"


class RouteDecision(BaseModel):
    label: RouteLabel
    reasons: list[str]


def route_stage(brief: Brief, llm_client=None) -> RouteDecision:
    if llm_client is None:
        raise RuntimeError("LLM client required")

    system_prompt = """You are the routing agent for a static SVG vector compiler.
Return supported only if the prompt can be represented as a simple static icon, sticker, badge, or emblem
using semantic components and SVG primitives/path geometry.
Return unsupported for photorealism, dense scenes, exact portraits, animation, external assets, or unsafe SVG features.
"""
    decision = llm_client.generate_model(
        system_prompt,
        f"Route this brief: {brief.model_dump()}",
        RouteDecision,
    )
    if decision.label == RouteLabel.UNSUPPORTED:
        raise RuntimeError(f"Unsupported prompt: {'; '.join(decision.reasons)}")
    return decision
