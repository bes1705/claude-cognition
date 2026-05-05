from pathlib import Path

COGNITION_DIR = Path.home() / ".cognition"
MEMORIES_DIR = COGNITION_DIR / "memories"
GRAPH_FILE = COGNITION_DIR / "graph.json"
LOG_FILE = COGNITION_DIR / "cognition.log"

COGNITION_DIR.mkdir(parents=True, exist_ok=True)
MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

MAX_EPISODIC = 1000
MAX_PROCEDURAL = 300
MAX_NEGATIVE_PATTERNS = 100
INJECT_TOP_K = 8
INJECT_MAX_TOKENS = 1500  # hard cap — 8 excellent memories beat 40 mediocre ones
AUTO_CAPTURE_DEDUP_DAYS = 7  # skip auto-capture if similar entry exists within N days
