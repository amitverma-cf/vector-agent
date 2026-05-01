# SVG Actor-Critic REPL

An autonomous agentic sandbox optimized for sub-1B parameter models (e.g., Qwen3.5-0.8B) to generate and iteratively refine SVG graphics via a strict tag-based REPL.

## 🏗️ Architecture (Agentic OS)

This project implements an **Actor-Critic REPL** loop:
- **Actor**: The LLM, constrained to a specific XML-like ISA (Instruction Set Architecture).
- **Critic**: A set of modular Python tools that validate, optimize, and render the Actor's output, providing "reward" feedback to guide the next iteration.

### Key Components
- **`src/core/agent.py`**: The main orchestration loop. Uses a Working Memory approach to manage context limits.
- **`src/tools/`**:
  - `svg_validator.py`: Deep syntax linting using `lxml`.
  - `svg_optimizer.py`: Minifies SVG for context window survival.
  - `render_svg.py`: Pure-Python rendering (SVG -> PNG) using `svglib` and `reportlab`.
- **`output/`**: Execution artifacts (PNG renders and the final `final.svg`).

## 🚀 Getting Started

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Configure Environment**:
   Create a `.env` file based on `.env.example`:
   ```env
   LLM_BASE_URL=http://127.0.0.1:8080/v1
   LLM_API_KEY=sk-no-key-required
   LLM_MODEL=qwen-0.8b
   MAX_ITERATIONS=10
   OUTPUT_DIR=output
   ```

3. **Run Local Inference (Optional)**:
   Place your GGUF models in `models/` and start `llama-server`.
   ```powershell
   .\scripts\start_server.ps1
   ```

4. **Execute the Agent**:
   ```bash
   uv run src/main.py "Draw a red circle"
   ```

## 🔒 Security & Privacy
- Local infrastructure (`models/`, `scripts/`) and environment configs (`.env`) are git-ignored.
- No external API calls are made if configured for a local `llama-server`.
