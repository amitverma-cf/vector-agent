"""
Phase 1: The Schema (Single Source of Truth) - Pydantic v2 Refactor

Pydantic models for all node types, roles, and document structures.
Optimized for Pydantic v2 and includes resilience for LLM outputs.
"""

from typing import Optional, List, Tuple, Literal, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from enum import Enum
import re


# ============================================================================
# Enums: Priorities, Roles
# ============================================================================

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Role(str, Enum):
    PRIMARY_SURFACE = "primary_surface"
    SECONDARY_SURFACE = "secondary_surface"
    OUTLINE = "outline"
    ACCENT = "accent"
    HIGHLIGHT = "highlight"
    SHADOW = "shadow"
    GLOW = "glow"
    DETAIL_LINE = "detail_line"
    BACKGROUND_FILL = "background_fill"


class OutputType(str, Enum):
    ICON = "icon"
    STICKER = "sticker"
    BADGE = "badge"
    EMBLEM = "emblem"


class StyleRecipe(str, Enum):
    FLAT = "flat"
    STICKER = "sticker"
    MONOCHROME = "monochrome"
    NEON = "neon"


class BackgroundType(str, Enum):
    TRANSPARENT = "transparent"
    SOLID_LIGHT = "solid_light"
    SOLID_DARK = "solid_dark"


class PaletteHint(str, Enum):
    COOL = "cool"
    WARM = "warm"
    NEUTRAL = "neutral"
    VIBRANT = "vibrant"
    MUTED = "muted"


class DetailLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ============================================================================
# Geometry Models
# ============================================================================

class Transform(BaseModel):
    """2D affine transform."""
    tx: float = 0.0
    ty: float = 0.0
    sx: float = 1.0
    sy: float = 1.0
    rotate: float = 0.0


class LayoutBox(BaseModel):
    """Bounding box relative to parent (0-100 scale)."""
    x: float = 0.0
    y: float = 0.0
    w: float = 100.0
    h: float = 100.0

    @model_validator(mode="after")
    def validate_box(self):
        if self.w <= 0 or self.h <= 0:
            raise ValueError("layout box width and height must be positive")
        if self.x < 0 or self.y < 0 or self.x + self.w > 100 or self.y + self.h > 100:
            raise ValueError("layout box must fit inside the parent 0-100 coordinate space")
        return self


class Point(BaseModel):
    """Point in a normalized 100x100 local component space."""
    x: float = Field(ge=0.0, le=100.0)
    y: float = Field(ge=0.0, le=100.0)


class RectGeometry(BaseModel):
    kind: Literal["rect"] = "rect"
    x: float = Field(ge=0.0, le=100.0)
    y: float = Field(ge=0.0, le=100.0)
    w: float = Field(gt=0.0, le=100.0)
    h: float = Field(gt=0.0, le=100.0)
    rx: float = Field(default=0.0, ge=0.0, le=50.0)
    ry: float = Field(default=0.0, ge=0.0, le=50.0)

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.x + self.w > 100 or self.y + self.h > 100:
            raise ValueError("rect geometry must fit inside the 100x100 local space")
        return self


class EllipseGeometry(BaseModel):
    kind: Literal["ellipse"] = "ellipse"
    cx: float = Field(ge=0.0, le=100.0)
    cy: float = Field(ge=0.0, le=100.0)
    rx: float = Field(gt=0.0, le=50.0)
    ry: float = Field(gt=0.0, le=50.0)

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.cx - self.rx < 0 or self.cx + self.rx > 100:
            raise ValueError("ellipse x bounds must fit inside the 100x100 local space")
        if self.cy - self.ry < 0 or self.cy + self.ry > 100:
            raise ValueError("ellipse y bounds must fit inside the 100x100 local space")
        return self


class LineGeometry(BaseModel):
    kind: Literal["line"] = "line"
    start: Point
    end: Point


class PolylineGeometry(BaseModel):
    kind: Literal["polyline"] = "polyline"
    points: List[Point] = Field(min_length=2, max_length=64)


class PolygonGeometry(BaseModel):
    kind: Literal["polygon"] = "polygon"
    points: List[Point] = Field(min_length=3, max_length=64)


class PathGeometry(BaseModel):
    kind: Literal["path"] = "path"
    d: str = Field(min_length=1, max_length=4000)


PrimitiveGeometry = Union[
    RectGeometry,
    EllipseGeometry,
    LineGeometry,
    PolylineGeometry,
    PolygonGeometry,
    PathGeometry,
]


class GeometryTransform(BaseModel):
    """Transform in normalized local geometry space."""
    tx: float = Field(default=0.0, ge=-100.0, le=100.0)
    ty: float = Field(default=0.0, ge=-100.0, le=100.0)
    sx: float = Field(default=1.0, ge=-10.0, le=10.0)
    sy: float = Field(default=1.0, ge=-10.0, le=10.0)
    rotate: float = Field(default=0.0, ge=-360.0, le=360.0)
    cx: float = Field(default=50.0, ge=0.0, le=100.0)
    cy: float = Field(default=50.0, ge=0.0, le=100.0)


class ShapeInstance(BaseModel):
    shape: PrimitiveGeometry
    transform: GeometryTransform = Field(default_factory=GeometryTransform)


class CompositeGeometry(BaseModel):
    kind: Literal["composite"] = "composite"
    operation: Literal["group", "union", "intersect", "subtract"] = "group"
    shapes: List[ShapeInstance] = Field(min_length=1, max_length=32)


GeometrySpec = Union[
    RectGeometry,
    EllipseGeometry,
    LineGeometry,
    PolylineGeometry,
    PolygonGeometry,
    PathGeometry,
    CompositeGeometry,
]


class ResolvedStyle(BaseModel):
    fill: str = "none"
    stroke: str = "none"
    stroke_width: float = Field(default=0.0, ge=0.0, le=64.0)
    fill_opacity: float = Field(default=1.0, ge=0.0, le=1.0)
    stroke_opacity: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("fill", "stroke")
    @classmethod
    def validate_paint(cls, v: str) -> str:
        if v == "none" or re.fullmatch(r"#[0-9A-Fa-f]{6}", v):
            return v
        raise ValueError("paint must be 'none' or a #RRGGBB color")


# ============================================================================
# Scene Node Types
# ============================================================================

def _normalize_enum_value(v: Any) -> str:
    """Normalize input string to match enum values (lowercase, snake_case)."""
    if isinstance(v, str):
        return v.lower().strip().replace(" ", "_")
    return v


def _validate_svg_id(v: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", v):
        raise ValueError("id must be a valid static SVG id")
    return v


class GroupNode(BaseModel):
    kind: Literal["group"] = "group"
    id: str
    parent_id: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    transform: Transform = Field(default_factory=Transform)
    priority: Priority = Priority.MEDIUM

    @field_validator("id")
    @classmethod
    def validate_id(cls, v):
        return _validate_svg_id(v)

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v):
        return _normalize_enum_value(v)


class ComponentNode(BaseModel):
    kind: Literal["component"] = "component"
    id: str
    name: str
    parent_id: Optional[str] = None
    role: Role = Role.PRIMARY_SURFACE
    priority: Priority = Priority.MEDIUM
    render_intent: Literal["rendered", "container"] = "rendered"
    layout_box: Optional[LayoutBox] = None
    children: List[str] = Field(default_factory=list)
    geometry: Optional[GeometrySpec] = None
    transform: Transform = Field(default_factory=Transform)
    resolved_style: Optional[ResolvedStyle] = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, v):
        return _validate_svg_id(v)

    @field_validator("role", "priority", mode="before")
    @classmethod
    def normalize_enums(cls, v):
        return _normalize_enum_value(v)


class MirrorNode(BaseModel):
    kind: Literal["mirror"] = "mirror"
    id: str
    parent_id: Optional[str] = None
    source_id: str
    axis: Literal["x", "y", "xy"] = "x"
    priority: Priority = Priority.MEDIUM
    transform: Transform = Field(default_factory=Transform)

    @field_validator("id", "source_id")
    @classmethod
    def validate_id(cls, v):
        return _validate_svg_id(v)

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v):
        return _normalize_enum_value(v)


class ArrayNode(BaseModel):
    kind: Literal["array"] = "array"
    id: str
    parent_id: Optional[str] = None
    source_id: str
    mode: Literal["grid", "radial", "line"] = "grid"
    count: int = Field(ge=2, le=16)
    params: dict = Field(default_factory=dict)
    priority: Priority = Priority.MEDIUM
    transform: Transform = Field(default_factory=Transform)

    @field_validator("id", "source_id")
    @classmethod
    def validate_id(cls, v):
        return _validate_svg_id(v)

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v):
        return _normalize_enum_value(v)


AnyNode = Union[GroupNode, ComponentNode, MirrorNode, ArrayNode]


# ============================================================================
# Brief (Phase 2)
# ============================================================================

class Brief(BaseModel):
    subject: str
    output_type: OutputType = OutputType.ICON
    style_recipe: Optional[StyleRecipe] = None
    background: Optional[BackgroundType] = None
    detail_level: Optional[DetailLevel] = None
    palette_hint: PaletteHint = PaletteHint.NEUTRAL
    contains_text: bool = False
    notes: List[str] = Field(default_factory=list)

    @field_validator("subject")
    @classmethod
    def subject_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("subject cannot be empty")
        return v.strip()

    @field_validator("output_type", "style_recipe", "background", "detail_level", "palette_hint", mode="before")
    @classmethod
    def normalize_brief_enums(cls, v):
        return _normalize_enum_value(v)


class CompositionPlan(BaseModel):
    subject: str
    reasoning: str
    visual_strategy: str
    focal_points: List[str] = Field(default_factory=list)
    required_parts: List[str] = Field(default_factory=list)
    optional_parts: List[str] = Field(default_factory=list)
    layout_strategy: str
    geometry_strategy: str

    @field_validator("subject")
    @classmethod
    def plan_subject_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("subject cannot be empty")
        return v.strip()


class ComponentSpec(BaseModel):
    id: str
    name: str
    parent_id: Optional[str] = None
    role: Role = Role.PRIMARY_SURFACE
    priority: Priority = Priority.MEDIUM
    render_intent: Literal["rendered", "container"] = "rendered"

    @field_validator("id")
    @classmethod
    def validate_id(cls, v):
        return _validate_svg_id(v)

    @field_validator("role", "priority", mode="before")
    @classmethod
    def normalize_enums(cls, v):
        return _normalize_enum_value(v)


# ============================================================================
# Component Plan (Phase 3: Decomposition)
# ============================================================================

class ComponentPlan(BaseModel):
    reasoning: str
    components: List[ComponentSpec]

    @model_validator(mode="after")
    def validate_component_ids(self):
        ids = [component.id for component in self.components]
        if len(ids) != len(set(ids)):
            raise ValueError("component ids must be unique")
        for component in self.components:
            if component.parent_id and component.parent_id not in ids:
                raise ValueError(f"{component.id} references missing parent {component.parent_id}")
        return self


# ============================================================================
# Local Path Result (Phase 5: Generation)
# ============================================================================

class GeometryResult(BaseModel):
    component_id: str
    geometry: GeometrySpec


class ComponentLayout(BaseModel):
    component_id: str
    layout_box: LayoutBox


class LayoutPlan(BaseModel):
    reasoning: str
    layouts: List[ComponentLayout]

    @model_validator(mode="after")
    def validate_layout_ids(self):
        ids = [layout.component_id for layout in self.layouts]
        if len(ids) != len(set(ids)):
            raise ValueError("layout component ids must be unique")
        return self


# ============================================================================
# Scene Document (Phase 6+)
# ============================================================================

class SceneDocument(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    canvas: Tuple[float, float] = (512, 512)
    style_recipe: StyleRecipe = StyleRecipe.FLAT
    background: BackgroundType = BackgroundType.TRANSPARENT
    palette_hint: PaletteHint = PaletteHint.NEUTRAL
    nodes: dict[str, AnyNode] = Field(default_factory=dict)
    node_order: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self):
        if len(set(self.node_order)) != len(self.node_order):
            raise ValueError("node_order contains duplicate ids")
        missing = [node_id for node_id in self.node_order if node_id not in self.nodes]
        if missing:
            raise ValueError(f"node_order references missing nodes: {missing}")
        for node_id, node in self.nodes.items():
            if node.parent_id and node.parent_id not in self.nodes:
                raise ValueError(f"{node_id} references missing parent {node.parent_id}")
        return self


# ============================================================================
# Validation Report (Phase 9)
# ============================================================================

class ValidationCheck(BaseModel):
    layer: Literal["schema", "geometry", "style", "render", "safety"]
    check_name: str
    status: Literal["pass", "repair", "fail"]
    details: Optional[str] = None


class ValidationReport(BaseModel):
    checks: List[ValidationCheck]
    overall_status: Literal["pass", "repair", "fail"]
    notes: List[str] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.overall_status == "pass"

    @property
    def repairable(self) -> bool:
        return self.overall_status == "repair"


# ============================================================================
# Final Output (Phase 9)
# ============================================================================

class CompileResult(BaseModel):
    main_svg: bytes
    diagnostic_id_svg: bytes
    diagnostic_bounds_svg: bytes
    diagnostic_labels_svg: bytes
    diagnostic_priority_svg: bytes


class RenderResult(BaseModel):
    png_1024: bytes
    png_64: bytes


class PipelineOutput(BaseModel):
    svg_bytes: bytes
    png_preview_1024: Optional[bytes] = None
    png_preview_64: Optional[bytes] = None
    scene_document: SceneDocument
    validation_report: ValidationReport
