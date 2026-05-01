import math
import json
from pydantic import BaseModel
from typing import List, Optional

class CurveModel(BaseModel):
    id: str
    x_eq: str
    y_eq: str
    t_min: float = 0
    t_max: float = 6.283
    samples: int = 100
    scale: float = 1.0
    translate_x: float = 0.0
    translate_y: float = 0.0
    stroke: str = "black"
    stroke_width: float = 1.0
    fill: str = "none"
    repeat_rotate: int = 1

class CanvasModel(BaseModel):
    width: int = 500
    height: int = 500

class ParametricProject(BaseModel):
    canvas: CanvasModel
    curves: List[CurveModel]

def safe_eval(expr, t, rotate_angle=0):
    # Standardize syntax (handle ^ as **)
    expr = expr.replace("^", "**")
    
    # Restricted globals for safe mathematical evaluation
    safe_dict = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "sqrt": math.sqrt,
        "abs": abs,
        "pi": math.pi,
        "e": math.e,
        "pow": pow,
        "exp": math.exp,
        "log": math.log,
        "log10": math.log10,
        "ceil": math.ceil,
        "floor": math.floor,
        "t": t,
        "math": math
    }
    # We evaluate the expression
    # Note: Small LLMs might use different syntax, we should be robust
    try:
        return eval(expr, {"__builtins__": None}, safe_dict)
    except Exception as e:
        raise ValueError(f"Math Error in '{expr}': {str(e)}")

def generate_curve_path(curve: CurveModel):
    all_paths = []
    
    for r in range(curve.repeat_rotate):
        angle = (2 * math.pi / curve.repeat_rotate) * r
        points = []
        
        for i in range(curve.samples + 1):
            t = curve.t_min + (curve.t_max - curve.t_min) * (i / curve.samples)
            
            # Calculate raw x, y
            raw_x = safe_eval(curve.x_eq, t)
            raw_y = safe_eval(curve.y_eq, t)
            
            # Apply Rotation (Symmetry)
            # x' = x cos - y sin, y' = x sin + y cos
            rot_x = raw_x * math.cos(angle) - raw_y * math.sin(angle)
            rot_y = raw_x * math.sin(angle) + raw_y * math.cos(angle)
            
            # Apply Scale and Translate
            final_x = (rot_x * curve.scale) + curve.translate_x
            final_y = (rot_y * curve.scale) + curve.translate_y
            
            points.append(f"{final_x:.2f},{final_y:.2f}")
            
        path_d = f"M {points[0]} " + " ".join([f"L {p}" for p in points[1:]])
        if curve.fill != "none":
            path_d += " Z"
            
        all_paths.append(f'<path d="{path_d}" fill="{curve.fill}" stroke="{curve.stroke}" stroke-width="{curve.stroke_width}" stroke-linecap="round" stroke-linejoin="round" />')
        
    return "\n".join(all_paths)

def compile_math_to_svg(json_str):
    try:
        data = json.loads(json_str)
        project = ParametricProject(**data)
    except Exception as e:
        return None, f"JSON/Schema Error: {str(e)}"
    
    svg_parts = [
        f'<svg viewBox="0 0 {project.canvas.width} {project.canvas.height}" xmlns="http://www.w3.org/2000/svg" width="{project.canvas.width}" height="{project.canvas.height}">'
    ]
    
    # Background for contrast
    svg_parts.append(f'<rect width="100%" height="100%" fill="#FFFFFF" />')
    
    for curve in project.curves:
        try:
            svg_parts.append(generate_curve_path(curve))
        except Exception as e:
            return None, f"Runtime Error in curve '{curve.id}': {str(e)}"
            
    svg_parts.append('</svg>')
    return "\n".join(svg_parts), "SUCCESS"
