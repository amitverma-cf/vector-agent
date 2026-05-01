import sys
from lxml import etree
import io

def validate_svg_deep(svg_content):
    try:
        parser = etree.XMLParser(recover=False)
        etree.fromstring(svg_content.encode('utf-8'), parser=parser)
        return True, "Valid SVG"
    except etree.XMLSyntaxError as e:
        # Extract line and column
        error_msg = f"LINE {e.lineno}, COL {e.offset}: {e.msg}"
        
        # Get the offending line if possible
        lines = svg_content.splitlines()
        if 0 < e.lineno <= len(lines):
            error_msg += f"\nContext: {lines[e.lineno-1]}"
            
        return False, error_msg

if __name__ == "__main__":
    content = sys.stdin.read()
    if not content.strip():
        print("FAIL: Empty input")
        sys.exit(1)
        
    is_valid, msg = validate_svg_deep(content)
    if is_valid:
        print("PASS")
    else:
        print(f"FAIL: {msg}")
        sys.exit(1)
