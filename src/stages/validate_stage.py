"""Validation stage for scene geometry and emitted static SVG."""

from src.geometry.validation import validate_scene_geometry
from src.models.schema import SceneDocument, ValidationReport
from src.svg.safety import validate_static_svg


def validate_stage(doc: SceneDocument, svg_bytes: bytes, notes: list[str] | None = None) -> ValidationReport:
    checks = []
    checks.extend(validate_scene_geometry(doc))
    checks.extend(validate_static_svg(svg_bytes))

    overall = "pass" if all(check.status == "pass" for check in checks) else "fail"
    return ValidationReport(
        checks=checks,
        overall_status=overall,
        notes=notes or [],
    )
