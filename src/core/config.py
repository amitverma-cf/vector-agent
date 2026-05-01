import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    # LLM Settings
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8080/v1")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-no-key-required")
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen-0.8b")
    
    # Paths
    ROOT_DIR = Path(__file__).parent.parent.parent
    SRC_DIR = ROOT_DIR / "src"
    TOOLS_DIR = SRC_DIR / "tools"
    OUTPUT_DIR = ROOT_DIR / os.getenv("OUTPUT_DIR", "output")
    
    # Agent Settings
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))

# Ensure output directory exists
Config.OUTPUT_DIR.mkdir(exist_ok=True)
