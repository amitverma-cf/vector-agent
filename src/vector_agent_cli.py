"""Installed console entry point."""

import argparse
import sys
from pathlib import Path

from src.pipeline import run_pipeline
from src.utils.llm import get_default_llm_client


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Vector Graphics Compiler - Convert text to SVG icons"
    )
    parser.add_argument("prompt", nargs="?", default=None)
    parser.add_argument("--output", "-o", type=str, default="output")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if not args.prompt:
        parser.print_help()
        sys.exit(1)

    llm_client = get_default_llm_client()
    result = run_pipeline(args.prompt, llm_client=llm_client)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    svg_path = output_dir / "output.svg"
    svg_path.write_bytes(result.svg_bytes)
    print(f"SVG: {svg_path}")

    scene_json = output_dir / "scene.json"
    scene_json.write_text(result.scene_document.model_dump_json(indent=2))
    print(f"Scene document: {scene_json}")

    report_json = output_dir / "report.json"
    report_json.write_text(result.validation_report.model_dump_json(indent=2))
    print(f"Validation report: {report_json}")


if __name__ == "__main__":
    main()
