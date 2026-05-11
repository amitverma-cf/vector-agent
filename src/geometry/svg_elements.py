"""Compile normalized geometry specs into SVG elements."""

from __future__ import annotations

from lxml import etree

from src.geometry.boolean_ops import composite_to_path_d
from src.models.schema import (
    CompositeGeometry,
    EllipseGeometry,
    GeometryTransform,
    GeometrySpec,
    LineGeometry,
    PathGeometry,
    PolygonGeometry,
    PolylineGeometry,
    RectGeometry,
    ResolvedStyle,
)


SVG_NS = "http://www.w3.org/2000/svg"


def svg_tag(name: str) -> str:
    return f"{{{SVG_NS}}}{name}"


def _point_list(points) -> str:
    return " ".join(f"{point.x:g},{point.y:g}" for point in points)


def style_attrs(style: ResolvedStyle | None) -> dict[str, str]:
    style = style or ResolvedStyle()
    attrs = {
        "fill": style.fill,
        "stroke": style.stroke,
    }
    if style.stroke_width > 0:
        attrs["stroke-width"] = f"{style.stroke_width:g}"
    if style.fill_opacity < 1:
        attrs["fill-opacity"] = f"{style.fill_opacity:g}"
    if style.stroke_opacity < 1:
        attrs["stroke-opacity"] = f"{style.stroke_opacity:g}"
    return attrs


def _apply_local_transform(element: etree._Element, transform: GeometryTransform) -> None:
    parts = []
    if transform.tx != 0 or transform.ty != 0:
        parts.append(f"translate({transform.tx:g} {transform.ty:g})")
    if transform.rotate != 0:
        parts.append(f"rotate({transform.rotate:g} {transform.cx:g} {transform.cy:g})")
    if transform.sx != 1 or transform.sy != 1:
        parts.append(
            f"translate({transform.cx:g} {transform.cy:g}) "
            f"scale({transform.sx:g} {transform.sy:g}) "
            f"translate({-transform.cx:g} {-transform.cy:g})"
        )
    if parts:
        element.set("transform", " ".join(parts))


def _primitive_to_element(geometry: GeometrySpec, element_id: str, style: ResolvedStyle | None) -> etree._Element:
    attrs = {"id": element_id, **style_attrs(style)}

    if isinstance(geometry, RectGeometry):
        attrs.update(
            {
                "x": f"{geometry.x:g}",
                "y": f"{geometry.y:g}",
                "width": f"{geometry.w:g}",
                "height": f"{geometry.h:g}",
            }
        )
        if geometry.rx:
            attrs["rx"] = f"{geometry.rx:g}"
        if geometry.ry:
            attrs["ry"] = f"{geometry.ry:g}"
        return etree.Element(svg_tag("rect"), attrs)

    if isinstance(geometry, EllipseGeometry):
        attrs.update(
            {
                "cx": f"{geometry.cx:g}",
                "cy": f"{geometry.cy:g}",
                "rx": f"{geometry.rx:g}",
                "ry": f"{geometry.ry:g}",
            }
        )
        return etree.Element(svg_tag("ellipse"), attrs)

    if isinstance(geometry, LineGeometry):
        attrs.update(
            {
                "x1": f"{geometry.start.x:g}",
                "y1": f"{geometry.start.y:g}",
                "x2": f"{geometry.end.x:g}",
                "y2": f"{geometry.end.y:g}",
                "fill": "none",
            }
        )
        return etree.Element(svg_tag("line"), attrs)

    if isinstance(geometry, PolylineGeometry):
        attrs.update({"points": _point_list(geometry.points), "fill": "none"})
        return etree.Element(svg_tag("polyline"), attrs)

    if isinstance(geometry, PolygonGeometry):
        attrs["points"] = _point_list(geometry.points)
        return etree.Element(svg_tag("polygon"), attrs)

    if isinstance(geometry, PathGeometry):
        attrs["d"] = geometry.d
        return etree.Element(svg_tag("path"), attrs)

    raise TypeError(f"Unsupported geometry type: {type(geometry)!r}")


def geometry_to_element(geometry: GeometrySpec, element_id: str, style: ResolvedStyle | None) -> etree._Element:
    if isinstance(geometry, CompositeGeometry):
        if geometry.operation == "group":
            group = etree.Element(svg_tag("g"), {"id": element_id})
            for index, instance in enumerate(geometry.shapes):
                child = _primitive_to_element(instance.shape, f"{element_id}_{index}", style)
                _apply_local_transform(child, instance.transform)
                group.append(child)
            return group

        path_d = composite_to_path_d(geometry.operation, geometry.shapes)
        return etree.Element(
            svg_tag("path"),
            {"id": element_id, "d": path_d, **style_attrs(style)},
        )

    return _primitive_to_element(geometry, element_id, style)
