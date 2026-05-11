"""Deterministic geometry validation."""

from __future__ import annotations

from svgpathtools import parse_path

from src.models.schema import ComponentNode, CompositeGeometry, PathGeometry, SceneDocument, ValidationCheck


def validate_scene_geometry(doc: SceneDocument) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []

    for node_id in doc.node_order:
        node = doc.nodes[node_id]
        if not isinstance(node, ComponentNode):
            continue

        if node.layout_box is None:
            checks.append(
                ValidationCheck(
                    layer="geometry",
                    check_name="component_layout_present",
                    status="fail",
                    details=f"{node_id} has no layout_box",
                )
            )

        if node.render_intent == "container":
            if node.geometry is not None:
                checks.append(
                    ValidationCheck(
                        layer="geometry",
                        check_name="container_geometry_absent",
                        status="fail",
                        details=f"{node_id} is a container but has geometry",
                    )
                )
            continue

        if node.geometry is None:
            checks.append(
                ValidationCheck(
                    layer="geometry",
                    check_name="component_geometry_present",
                    status="fail",
                    details=f"{node_id} has no geometry",
                )
            )
            continue

        geometry = node.geometry
        if isinstance(geometry, PathGeometry):
            try:
                parse_path(geometry.d)
            except Exception as exc:
                checks.append(
                    ValidationCheck(
                        layer="geometry",
                        check_name="path_parse",
                        status="fail",
                        details=f"{node_id}: {exc}",
                    )
                )

        if isinstance(geometry, CompositeGeometry):
            for index, instance in enumerate(geometry.shapes):
                if isinstance(instance.shape, PathGeometry):
                    try:
                        parse_path(instance.shape.d)
                    except Exception as exc:
                        checks.append(
                            ValidationCheck(
                                layer="geometry",
                                check_name="composite_path_parse",
                                status="fail",
                                details=f"{node_id}[{index}]: {exc}",
                            )
                        )

    if not checks:
        checks.append(
            ValidationCheck(
                layer="geometry",
                check_name="component_geometry",
                status="pass",
            )
        )

    return checks
