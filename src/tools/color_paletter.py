import sys
import json

PALETTES = {
    "cyberpunk": ["#ff00ff", "#00ffff", "#ffff00", "#0000ff", "#000000"],
    "retro": ["#ff5f5f", "#f4a261", "#e9c46a", "#2a9d8f", "#264653"],
    "minimalist": ["#f8f9fa", "#e9ecef", "#dee2e6", "#ced4da", "#adb5bd"],
    "nature": ["#2b9348", "#55a630", "#80b918", "#aacc00", "#bfd200"]
}

def get_palette(theme):
    return PALETTES.get(theme.lower(), ["#000000", "#ffffff"])

if __name__ == "__main__":
    theme = sys.argv[1] if len(sys.argv) > 1 else "default"
    print(json.dumps(get_palette(theme)))
