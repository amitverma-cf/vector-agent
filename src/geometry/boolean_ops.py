"""Boolean operations for closed primitive geometry."""

from __future__ import annotations

from math import cos, sin

from src.models.schema import (
    EllipseGeometry,
    GeometryTransform,
    LineGeometry,
    PathGeometry,
    PolygonGeometry,
    PolylineGeometry,
    PrimitiveGeometry,
    RectGeometry,
    ShapeInstance,
)


def _load_shapely():
    try:
        from shapely.affinity import affine_transform, rotate, translate
        from shapely.geometry import Polygon, box
        from shapely.ops import unary_union
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Composite subtract/intersect requires shapely. Install dependencies with uv sync."
        ) from exc
    return affine_transform, rotate, translate, Polygon, box, unary_union


def _ellipse_polygon(geometry: EllipseGeometry, segments: int = 48) -> Polygon:
    _, _, _, Polygon, _, _ = _load_shapely()
    points = []
    for index in range(segments):
        angle = 2.0 * 3.141592653589793 * index / segments
        points.append((geometry.cx + geometry.rx * cos(angle), geometry.cy + geometry.ry * sin(angle)))
    return Polygon(points)


def _primitive_to_polygon(geometry: PrimitiveGeometry):
    _, _, _, Polygon, box, _ = _load_shapely()
    if isinstance(geometry, RectGeometry):
        return box(geometry.x, geometry.y, geometry.x + geometry.w, geometry.y + geometry.h)
    if isinstance(geometry, EllipseGeometry):
        return _ellipse_polygon(geometry)
    if isinstance(geometry, PolygonGeometry):
        return Polygon([(point.x, point.y) for point in geometry.points])
    if isinstance(geometry, (LineGeometry, PolylineGeometry, PathGeometry)):
        raise RuntimeError(f"Boolean operations require closed primitive shapes, got {geometry.kind}")
    raise RuntimeError(f"Unsupported boolean primitive: {type(geometry)!r}")


def _apply_transform(polygon, transform: GeometryTransform):
    affine_transform, rotate, translate, _, _, _ = _load_shapely()
    shifted = translate(polygon, xoff=-transform.cx, yoff=-transform.cy)
    scaled = affine_transform(shifted, [transform.sx, 0, 0, transform.sy, 0, 0])
    rotated = rotate(scaled, transform.rotate, origin=(0, 0), use_radians=False)
    return translate(rotated, xoff=transform.cx + transform.tx, yoff=transform.cy + transform.ty)


def instance_to_polygon(instance: ShapeInstance):
    return _apply_transform(_primitive_to_polygon(instance.shape), instance.transform)


def composite_to_path_d(operation: str, shapes: list[ShapeInstance]) -> str:
    *_, unary_union = _load_shapely()
    polygons = [instance_to_polygon(instance) for instance in shapes]
    if not polygons:
        raise RuntimeError("Composite geometry requires at least one shape")

    if operation in {"group", "union"}:
        result = unary_union(polygons)
    elif operation == "intersect":
        result = polygons[0]
        for polygon in polygons[1:]:
            result = result.intersection(polygon)
    elif operation == "subtract":
        result = polygons[0]
        for polygon in polygons[1:]:
            result = result.difference(polygon)
    else:
        raise RuntimeError(f"Unsupported composite operation: {operation}")

    if result.is_empty:
        raise RuntimeError(f"Composite operation produced empty geometry: {operation}")

    return _polygonal_to_path_d(result)


def _ring_to_path(coords) -> str:
    points = list(coords)
    if not points:
        return ""
    first_x, first_y = points[0]
    commands = [f"M {first_x:g} {first_y:g}"]
    commands.extend(f"L {x:g} {y:g}" for x, y in points[1:])
    commands.append("Z")
    return " ".join(commands)


def _polygon_to_path_d(polygon: Polygon) -> str:
    parts = [_ring_to_path(polygon.exterior.coords)]
    parts.extend(_ring_to_path(interior.coords) for interior in polygon.interiors)
    return " ".join(part for part in parts if part)


def _polygonal_to_path_d(geometry) -> str:
    _, _, _, Polygon, _, _ = _load_shapely()
    if isinstance(geometry, Polygon):
        return _polygon_to_path_d(geometry)
    if hasattr(geometry, "geoms"):
        return " ".join(_polygon_to_path_d(polygon) for polygon in geometry.geoms if isinstance(polygon, Polygon))
    raise RuntimeError(f"Boolean operation produced unsupported geometry: {geometry.geom_type}")
