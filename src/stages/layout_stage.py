"""Layout stage: place semantic components with small looped model outputs."""

from pydantic import ValidationError

from src.models.schema import ComponentLayout, ComponentNode, CompositionPlan, SceneDocument


def _component_summary(node: ComponentNode) -> dict:
    return {
        "id": node.id,
        "name": node.name,
        "parent_id": node.parent_id,
        "role": node.role.value,
        "priority": node.priority.value,
        "render_intent": node.render_intent,
        "children": node.children,
    }


def _generate_component_layout(
    doc: SceneDocument,
    component: ComponentNode,
    plan: CompositionPlan,
    llm_client,
) -> ComponentLayout:
    siblings = [
        _component_summary(node)
        for node in doc.nodes.values()
        if isinstance(node, ComponentNode) and node.parent_id == component.parent_id
    ]
    parent = doc.nodes.get(component.parent_id) if component.parent_id else None
    parent_summary = _component_summary(parent) if isinstance(parent, ComponentNode) else None

    system_prompt = """You are a vector layout agent.
Assign one component a layout_box in its parent's 0-100 coordinate space.
Return only JSON with keys: component_id, layout_box.
layout_box has x, y, w, h.
The box must fit inside the parent.
Use the composition plan, parent, and siblings to make a coherent layout.
"""
    user_prompt = (
        f"Composition plan: {plan.model_dump()}\n"
        f"Parent: {parent_summary}\n"
        f"Siblings: {siblings}\n"
        f"Place component: {_component_summary(component)}"
    )

    errors: list[str] = []
    for _ in range(3):
        prompt = user_prompt if not errors else f"{user_prompt}\nPrevious layout was invalid: {errors[-1]}"
        raw = llm_client.generate_json_text(system_prompt, prompt)
        try:
            layout = ComponentLayout.model_validate(raw)
        except ValidationError as exc:
            errors.append(str(exc))
            continue
        if layout.component_id != component.id:
            errors.append(f"component_id must be {component.id}, got {layout.component_id}")
            continue
        return layout

    raise RuntimeError(f"Layout failed for {component.id}: {errors[-1] if errors else 'unknown error'}")


def layout_stage(doc: SceneDocument, plan: CompositionPlan, llm_client=None) -> SceneDocument:
    if llm_client is None:
        raise RuntimeError("LLM client required")

    for node_id in doc.node_order:
        node = doc.nodes[node_id]
        if not isinstance(node, ComponentNode):
            continue
        layout = _generate_component_layout(doc, node, plan, llm_client)
        node.layout_box = layout.layout_box

    return doc
