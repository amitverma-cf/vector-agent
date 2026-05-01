import sys
import re

def optimize_svg(svg_content):
    svg_content = re.sub(r'<!--.*?-->', '', svg_content, flags=re.DOTALL)
    svg_content = re.sub(r'<\?xml.*?\?>', '', svg_content)
    svg_content = re.sub(r'<!DOCTYPE.*?>', '', svg_content)
    svg_content = re.sub(r'>\s+<', '><', svg_content)
    def round_coords(match):
        prefix = match.group(1)
        number = float(match.group(2))
        return f"{prefix}{number:.2f}"
    svg_content = re.sub(r'([=\s,])(-?\d+\.\d+)', round_coords, svg_content)
    return svg_content.strip()

if __name__ == "__main__":
    content = sys.stdin.read()
    print(optimize_svg(content))
