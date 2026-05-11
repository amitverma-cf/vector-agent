"""
CLI Entry Point for Vector Graphics Compiler

Usage:
    python -m svg_agent "your prompt here"
    python -m svg_agent --help
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import run_pipeline
from src.utils.llm import get_default_llm_client


def main():
    parser = argparse.ArgumentParser(
        description="Vector Graphics Compiler - Convert text to SVG icons"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Text prompt describing the graphic to generate"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output",
        help="Output directory (default: output)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if not args.prompt:
        parser.print_help()
        sys.exit(1)
    
    # Run pipeline
    if args.verbose:
        print(f"Prompt: {args.prompt}")
        print("Running pipeline...")
    
    llm_client = get_default_llm_client()
    if args.verbose:
        print(f"LLM client: {'configured' if llm_client else 'not configured'}")

    try:
        result = run_pipeline(args.prompt, llm_client=llm_client)
    except Exception as e:
        print(f"Error: {e}")
        print("Hint: Ensure your LLM is reachable and LLM_BASE_URL / LLM_API_KEY / LLM_MODEL are correct.")
        sys.exit(2)
    
    if args.verbose:
        print(f"Validation: {result.validation_report.overall_status}")
        print(f"Notes: {result.validation_report.notes}")
        print(f"Canvas: {result.scene_document.canvas}")
        print(f"Recipe: {result.scene_document.style_recipe}")
        print(f"Background: {result.scene_document.background}")
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write outputs
    if result.svg_bytes:
        svg_path = output_dir / "output.svg"
        svg_path.write_bytes(result.svg_bytes)
        print(f"SVG: {svg_path}")
    
    if result.png_preview_1024:
        png_path = output_dir / "preview_1024.png"
        png_path.write_bytes(result.png_preview_1024)
        print(f"PNG 1024px: {png_path}")
    
    if result.png_preview_64:
        png_path = output_dir / "preview_64.png"
        png_path.write_bytes(result.png_preview_64)
        print(f"PNG 64px: {png_path}")
    
    # Write scene document
    scene_json = output_dir / "scene.json"
    scene_json.write_text(result.scene_document.model_dump_json(indent=2))
    print(f"Scene document: {scene_json}")
    
    # Write validation report
    report_json = output_dir / "report.json"
    report_json.write_text(result.validation_report.model_dump_json(indent=2))
    print(f"Validation report: {report_json}")
    
    print("\nPipeline complete!")


if __name__ == "__main__":
    main()
