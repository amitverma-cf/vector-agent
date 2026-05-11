"""Refinement stage: request minimal structured patches from the model."""

from typing import Literal

from pydantic import BaseModel, Field

from src.models.schema import ComponentNode, LayoutBox, SceneDocument


class Patch(BaseModel):
    type: Literal["update_layout", "regenerate_geometry"]
    component_id: str
    params: LayoutBox | None = None


class PatchPlan(BaseModel):
    patches: list[Patch] = Field(default_factory=list, max_length=3)


def refine_stage(doc: SceneDocument, llm_client=None) -> list[Patch]:
    if llm_client is None:
        raise RuntimeError("LLM client required")

    comp_state = [
        {
            "id": n.id,
            "name": n.name,
            "parent_id": n.parent_id,
            "layout_box": n.layout_box.model_dump() if n.layout_box else None,
            "role": n.role.value,
            "geometry_kind": n.geometry.kind if n.geometry else None,
        }
        for n in doc.nodes.values()
        if isinstance(n, ComponentNode)
    ]

    system_prompt = """You are the refinement agent for a static SVG vector compiler.
Review only the structured component state.
Return only patches that are necessary. Return an empty patch list when no change is needed.

Patch rules:
- update_layout requires params with x, y, w, h
- regenerate_geometry requires params=null
- component_id must refer to an existing component
- return no patches when the structure is acceptable
"""

    plan = llm_client.generate_model(system_prompt, f"Review components: {comp_state}", PatchPlan)
    existing_ids = set(doc.nodes)
    for patch in plan.patches:
        if patch.component_id not in existing_ids:
            raise RuntimeError(f"Refinement patch references missing component {patch.component_id}")
        if patch.type == "update_layout" and patch.params is None:
            raise RuntimeError(f"update_layout patch for {patch.component_id} is missing params")
    return plan.patches
