import sys
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import io

def render_svg_to_png(svg_content, output_path):
    drawing = svg2rlg(io.BytesIO(svg_content.encode('utf-8')))
    renderPM.drawToFile(drawing, output_path, fmt="PNG")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    svg_input = sys.argv[1]
    out_file = sys.argv[2]
    try:
        render_svg_to_png(svg_input, out_file)
        print(f"Successfully rendered to {out_file}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
