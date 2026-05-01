import sys
from core.agent import run_agent

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run src/main.py \"Goal\"")
        return
    
    goal = sys.argv[1]
    run_agent(goal)

if __name__ == "__main__":
    main()
