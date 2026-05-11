"""Static SVG safety validation."""

from __future__ import annotations

from lxml import etree

from src.models.schema import ValidationCheck


ALLOWED_ELEMENTS = {
    "svg",
    "g",
    "path",
    "rect",
    "circle",
    "ellipse",
    "polygon",
    "polyline",
    "line",
    "defs",
    "linearGradient",
    "radialGradient",
    "stop",
    "clipPath",
    "mask",
    "title",
    "desc",
}

ALLOWED_ATTRS = {
    "id",
    "xmlns",
    "viewBox",
    "width",
    "height",
    "x",
    "y",
    "x1",
    "y1",
    "x2",
    "y2",
    "cx",
    "cy",
    "r",
    "rx",
    "ry",
    "d",
    "points",
    "fill",
    "stroke",
    "stroke-width",
    "fill-opacity",
    "stroke-opacity",
    "stroke-linecap",
    "stroke-linejoin",
    "transform",
    "opacity",
    "offset",
    "stop-color",
    "stop-opacity",
}


def validate_static_svg(svg_bytes: bytes) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []
    parser = etree.XMLParser(resolve_entities=False, no_network=True)

    try:
        root = etree.fromstring(svg_bytes, parser=parser)
    except etree.XMLSyntaxError as exc:
        return [
            ValidationCheck(
                layer="safety",
                check_name="xml_parse",
                status="fail",
                details=str(exc),
            )
        ]

    for element in root.iter():
        tag = etree.QName(element).localname
        if tag not in ALLOWED_ELEMENTS:
            checks.append(
                ValidationCheck(
                    layer="safety",
                    check_name="allowed_element",
                    status="fail",
                    details=f"Disallowed element: {tag}",
                )
            )

        for attr_name, attr_value in element.attrib.items():
            local_attr = etree.QName(attr_name).localname
            if local_attr not in ALLOWED_ATTRS or local_attr.lower().startswith("on"):
                checks.append(
                    ValidationCheck(
                        layer="safety",
                        check_name="allowed_attribute",
                        status="fail",
                        details=f"Disallowed attribute on {tag}: {local_attr}",
                    )
                )
            if isinstance(attr_value, str) and ("javascript:" in attr_value.lower() or "http://" in attr_value.lower() or "https://" in attr_value.lower()):
                checks.append(
                    ValidationCheck(
                        layer="safety",
                        check_name="external_reference",
                        status="fail",
                        details=f"Unsafe value on {tag}.{local_attr}",
                    )
                )

    if not checks:
        checks.append(
            ValidationCheck(
                layer="safety",
                check_name="static_svg_profile",
                status="pass",
            )
        )

    return checks
