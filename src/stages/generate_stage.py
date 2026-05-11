"""Geometry generation stage with small looped model outputs."""

from typing import Any, Literal

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from src.models.schema import (
    ComponentNode,
    CompositeGeometry,
    GeometryResult,
    GeometrySpec,
    GeometryTransform,
    PrimitiveGeometry,
    ShapeInstance,
)


class GeometryChoice(BaseModel):
    mode: Literal["primitive", "composite"]
    operation: Literal["group", "union", "intersect", "subtract"] = "group"
    primitive_kind: Literal["rect", "ellipse", "line", "polyline", "polygon", "path"] = "path"
    reasoning: str


class ShapePart(BaseModel):
    id: str
    purpose: str
    primitive_kind: Literal["rect", "ellipse", "line", "polyline", "polygon", "path"]
    transform: GeometryTransform = Field(default_factory=GeometryTransform)


class ShapePlan(BaseModel):
    parts: list[ShapePart] = Field(min_length=1, max_length=24)


class PrimitiveDraft(BaseModel):
    primitive: dict[str, Any]


def _brief_validation_error(exc: ValidationError) -> str:
    messages = []
    for error in exc.errors()[:4]:
        loc = ".".join(str(part) for part in error["loc"])
        messages.append(f"{loc}: {error['msg']}")
    return "; ".join(messages)


def _normalize_choice(raw_choice: dict[str, Any]) -> dict[str, Any]:
    aliases = {
        "circle": "ellipse",
        "oval": "ellipse",
        "square": "rect",
        "rectangle": "rect",
        "rounded_rectangle": "rect",
        "rounded_rect": "rect",
        "capsule": "rect",
        "curve": "path",
    }
    primitive_kind = raw_choice.get("primitive_kind")
    if isinstance(primitive_kind, str):
        raw_choice["primitive_kind"] = aliases.get(primitive_kind.lower(), primitive_kind)
    return raw_choice


def _generate_shape_plan(system_prompt: str, component_id: str, llm_client) -> ShapePlan:
    errors: list[str] = []
    user_prompt = f"Plan primitive parts for component {component_id}."
    for _ in range(3):
        prompt = user_prompt if not errors else f"{user_prompt}\nPrevious shape plan was invalid: {errors[-1]}"
        raw_shape_plan = llm_client.generate_json_text(
            system_prompt + "\nReturn only JSON with key: parts. parts must be an array.",
            prompt,
        )
        try:
            return ShapePlan.model_validate(raw_shape_plan)
        except ValidationError as exc:
            errors.append(str(exc))
    raise RuntimeError(f"Shape planning failed for {component_id}: {errors[-1] if errors else 'unknown error'}")


def _generate_primitive(
    component: ComponentNode,
    context_summary: str,
    llm_client,
    primitive_kind: str | None = None,
    part: ShapePart | None = None,
) -> PrimitiveGeometry:
    adapter = TypeAdapter(PrimitiveGeometry)
    kind_text = primitive_kind or "the simplest suitable primitive"
    part_text = f"\nPart purpose: {part.purpose}\nPrimitive kind: {part.primitive_kind}" if part else ""
    system_prompt = f"""You are a vector primitive agent.
Return one primitive geometry object for a 100x100 local coordinate space.

Component: {component.name}
Role: {component.role.value}
Context: {context_summary}
Required primitive: {kind_text}{part_text}

Allowed primitive kinds:
- rect: kind, x, y, w, h, optional rx, ry
- ellipse: kind, cx, cy, rx, ry
- line: kind, start {{x,y}}, end {{x,y}}
- polyline: kind, points
- polygon: kind, points
- path: kind, d

Return a small object. Do not return composite geometry here.
The response must contain a primitive object with the required primitive fields.
All coordinates must remain inside 0-100.

Examples:
{{"primitive": {{"kind": "ellipse", "cx": 50, "cy": 50, "rx": 35, "ry": 35}}}}
{{"primitive": {{"kind": "line", "start": {{"x": 20, "y": 20}}, "end": {{"x": 80, "y": 80}}}}}}
"""
    user_prompt = f"Generate the primitive for component {component.id}."
    errors: list[str] = []
    for _ in range(3):
        prompt = user_prompt if not errors else f"{user_prompt}\nPrevious primitive was invalid: {errors[-1]}"
        raw = llm_client.generate_json_text(system_prompt, prompt)
        if "primitive" not in raw and "kind" in raw:
            raw = {"primitive": raw}
        elif isinstance(raw.get("primitive"), str):
            primitive_kind = raw["primitive"]
            raw = {"primitive": {"kind": primitive_kind, **{k: v for k, v in raw.items() if k != "primitive"}}}
        elif "primitive" not in raw and isinstance(raw.get("geometry"), dict):
            raw = {"primitive": raw["geometry"]}
        elif "primitive" not in raw and isinstance(raw.get("shape"), dict):
            raw = {"primitive": raw["shape"]}
        try:
            draft = PrimitiveDraft.model_validate(raw)
        except ValidationError as exc:
            errors.append(f"{_brief_validation_error(exc)}; returned keys: {sorted(raw.keys())}")
            continue
        try:
            primitive = adapter.validate_python(draft.primitive)
            if primitive_kind and primitive.kind != primitive_kind:
                errors.append(f"primitive kind must be {primitive_kind}, got {primitive.kind}")
                continue
            return primitive
        except ValidationError as exc:
            errors.append(_brief_validation_error(exc))
    raise RuntimeError(f"Primitive generation failed for {component.id}: {errors[-1] if errors else 'unknown error'}")


def generate_component_geometry(
    component: ComponentNode,
    context_summary: str,
    llm_client=None,
) -> GeometryResult:
    if llm_client is None:
        raise RuntimeError("LLM client required")
    if component.render_intent == "container":
        raise RuntimeError(f"Container component {component.id} does not need geometry")

    choice_prompt = f"""You are a vector drawing planner.
Choose how to draw this single component without producing the geometry yet.

Component: {component.name}
Role: {component.role.value}
Context: {context_summary}

Use primitive when one shape is enough.
Use composite when the component genuinely needs multiple primitives merged or grouped.
If composite, choose operation: group, union, subtract, or intersect.
Always choose primitive_kind. For primitive mode, this is the kind to draw.
Most components should be primitive.
A ring, rim, outline, border, shaft, handle, highlight, or shadow is usually one primitive with the component style, not a composite.
Choose subtract/intersect only when the named component cannot be drawn as a primitive, stroke, or path.
"""
    raw_choice = llm_client.generate_json_text(
        choice_prompt + "\nReturn only JSON with keys: mode, operation, primitive_kind, reasoning.",
        f"Choose geometry mode for component {component.id}.",
    )
    if raw_choice.get("mode") == "primitive" and raw_choice.get("operation") in (None, "none", "None", ""):
        raw_choice["operation"] = "group"
    raw_choice = _normalize_choice(raw_choice)
    choice = GeometryChoice.model_validate(raw_choice)

    if choice.mode == "primitive":
        primitive = _generate_primitive(component, context_summary, llm_client, primitive_kind=choice.primitive_kind)
        return GeometryResult(component_id=component.id, geometry=TypeAdapter(GeometrySpec).validate_python(primitive.model_dump()))

    operation = choice.operation
    shape_plan_prompt = f"""You are a vector shape planner.
List the primitive parts needed for this composite component, but do not draw them.

Component: {component.name}
Role: {component.role.value}
Composite operation: {operation}
Context: {context_summary}

Each part needs id, purpose, primitive_kind, and optional transform.
Keep each part visually necessary.
"""
    shape_plan = _generate_shape_plan(shape_plan_prompt, component.id, llm_client)

    shapes: list[ShapeInstance] = []
    for part in shape_plan.parts:
        primitive = _generate_primitive(
            component,
            context_summary,
            llm_client,
            primitive_kind=part.primitive_kind,
            part=part,
        )
        shapes.append(ShapeInstance(shape=primitive, transform=part.transform))

    composite = CompositeGeometry(operation=operation, shapes=shapes)
    return GeometryResult(component_id=component.id, geometry=composite)
