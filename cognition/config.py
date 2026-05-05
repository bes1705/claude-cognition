from pathlib import Path

COGNITION_DIR = Path.home() / ".cognition"
MEMORIES_DIR = COGNITION_DIR / "memories"
GRAPH_FILE = COGNITION_DIR / "graph.json"
PATTERNS_FILE = COGNITION_DIR / "patterns.json"
LOG_FILE = COGNITION_DIR / "cognition.log"

COGNITION_DIR.mkdir(parents=True, exist_ok=True)
MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

MAX_EPISODIC = 1000
MAX_PROCEDURAL = 300
MAX_NEGATIVE_PATTERNS = 100
INJECT_TOP_K = 7
