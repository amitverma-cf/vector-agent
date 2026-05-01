import base64
import requests
import os
from core.config import Config

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_vlm_critique(image_path, goal):
    if not os.path.exists(image_path):
        return "CRITIQUE ERROR: Image not found."
    
    base64_image = encode_image(image_path)
    
    # Using local llama-server (which supports mmproj)
    # The endpoint is often /v1/chat/completions with image data
    url = f"{Config.LLM_BASE_URL}/chat/completions"
    
    payload = {
        "model": "vlm", # Placeholder name
        "messages": [
            {
                "role": "system",
                "content": "You are a strict Geometric Art Director. Analyze the provided PNG image."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"The goal was to draw: '{goal}'. Look at the image and provide a 2-sentence critique focusing on geometric accuracy, symmetry, and visual appeal. Be blunt. Do not write math."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 150,
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, json=payload, timeout=90)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"CRITIQUE SKIPPED (VLM Error): {str(e)}"
