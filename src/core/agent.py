import re
import requests
import json
from pydantic import BaseModel
from core.config import Config
from tools.math_engine import compile_math_to_svg
from tools.render_svg import render_svg_to_png
from tools.vlm_critic import get_vlm_critique

# Simplified Parametric Prompt
SYSTEM_PROMPT = """You are a Math-to-SVG Agent. 
Grid: 500x500. Center: (250,250).
Output format:
<thought>Plan coordinates.</thought>
<cmd:math_to_svg>
{
  "canvas": {"width": 500, "height": 500},
  "curves": [{
    "id": "shape",
    "x_eq": "formula_with_t",
    "y_eq": "formula_with_t",
    "scale": 10, "translate_x": 250, "translate_y": 250,
    "stroke": "red", "fill": "none", "repeat_rotate": 1
  }]
}
</cmd:math_to_svg>

### EXAMPLE MANDALA
<thought>Plan: A spirograph-like flower with 12 petals using repeat_rotate.</thought>
<cmd:math_to_svg>
{
  "canvas": {"width": 500, "height": 500},
  "curves": [{
    "id": "petal",
    "x_eq": "20 * sin(t)", "y_eq": "10 * cos(t) - 50",
    "repeat_rotate": 12, "scale": 2, "translate_x": 250, "translate_y": 250,
    "stroke": "fuchsia"
  }]
}
</cmd:math_to_svg>

Available: sin, cos, tan, sqrt, abs, pi, e, pow. Use t from 0 to 6.28.
"""

class State(BaseModel):
    goal: str
    last_feedback: str = "Start."
    iteration: int = 0
    done: bool = False
    current_svg: str = ""

def parse_llm_response(text):
    thought = re.search(r'<thought>(.*?)(?:</thought>|$)', text, re.DOTALL | re.IGNORECASE)
    thought = thought.group(1).strip() if thought else "No reasoning."
    
    cmd_match = re.search(r'<cmd:math_to_svg>(.*?)(?:</cmd:math_to_svg>|$)', text, re.DOTALL | re.IGNORECASE)
    cmd_name = "math_to_svg" if cmd_match else None
    cmd_body = cmd_match.group(1).strip() if cmd_match else ""
    
    if "final_submit" in text.lower():
        cmd_name = "final_submit"
        
    return thought, cmd_name, cmd_body

def query_llm(state: State):
    url = f"{Config.LLM_BASE_URL}/completions"
    prompt = f"{SYSTEM_PROMPT}\nGOAL: {state.goal}\nFEEDBACK: {state.last_feedback}\n\nResponse:\n<thought>"
    
    payload = {
        "prompt": prompt,
        "max_tokens": 1024,
        "temperature": 0.1,
        "stop": ["</cmd:math_to_svg>", "###"],
        "repeat_penalty": 1.1
    }
    try:
        res = requests.post(url, json=payload, timeout=90)
        return "<thought>" + res.json()["choices"][0]["text"].strip()
    except Exception as e:
        return f"ERROR: {e}"

def run_agent(goal):
    state = State(goal=goal)
    print(f"[*] Parametric Engine Started: {goal}")
    
    while state.iteration < 5 and not state.done:
        state.iteration += 1
        print(f"\n[Turn {state.iteration}]")
        
        raw = query_llm(state)
        print(f"DEBUG RAW:\n{raw[:300]}...\n")
        thought, cmd, body = parse_llm_response(raw)
        
        if not cmd:
            state.last_feedback = "ERROR: Missing <cmd:math_to_svg> tag."
            continue
            
        if cmd == "math_to_svg":
            svg, msg = compile_math_to_svg(body)
            if msg != "SUCCESS":
                state.last_feedback = f"MATH ERROR: {msg}"
                print(f"!! {state.last_feedback}")
            else:
                state.current_svg = svg
                png_path = Config.OUTPUT_DIR / f"turn_{state.iteration}.png"
                render_svg_to_png(svg, str(png_path))
                
                print("[*] Calling VLM Critic...")
                critique = get_vlm_critique(str(png_path), state.goal)
                
                if "SKIPPED" in critique or "ERROR" in critique:
                    state.last_feedback = "SYSTEM: Image rendered. Please refine your math if needed. If finished, output 'final_submit'."
                else:
                    state.last_feedback = f"CRITIQUE: {critique}"
                    
                print(f">> Critic: {state.last_feedback}")
                
                if "good" in critique.lower() or "perfect" in critique.lower():
                    state.done = True
        
        elif cmd == "final_submit":
            state.done = True
            print(f"[!] SUCCESS: Graphics finalized.")
        
    # Save final
    if state.current_svg:
        with open(Config.OUTPUT_DIR / "final.svg", "w", encoding='utf-8') as f:
            f.write(state.current_svg)
            
    print("[!] REPL End.")
    return state
