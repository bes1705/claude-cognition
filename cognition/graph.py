"""3-layer cognitive graph: episodic / semantic / procedural."""
import json
from datetime import datetime
from pathlib import Path
from .config import GRAPH_FILE, MAX_EPISODIC, MAX_PROCEDURAL, MAX_NEGATIVE_PATTERNS


class CognitionGraph:
    def __init__(self, path: Path = GRAPH_FILE):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "episodic": [],
            "semantic": {},
            "procedural": [],
            "negative_patterns": [],
            "meta": {"created": datetime.now().isoformat(), "sessions": 0},
        }

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # ── Episodic ──────────────────────────────────────────────────────────────

    def add_episodic(self, content: str, project: str = "", tags: list = None):
        self.data["episodic"].append({
            "content": content,
            "project": project,
            "tags": tags or [],
            "ts": datetime.now().isoformat(),
        })
        self.data["episodic"] = self.data["episodic"][-MAX_EPISODIC:]

    # ── Semantic ──────────────────────────────────────────────────────────────

    def set_semantic(self, key: str, value: str, confidence: float = 0.9):
        self.data["semantic"][key] = {
            "value": value,
            "confidence": confidence,
            "updated": datetime.now().isoformat(),
        }

    # ── Procedural ────────────────────────────────────────────────────────────

    def add_procedural(self, pattern: str, project: str = "", tags: list = None):
        self.data["procedural"].append({
            "pattern": pattern,
            "project": project,
            "tags": tags or [],
            "ts": datetime.now().isoformat(),
        })
        self.data["procedural"] = self.data["procedural"][-MAX_PROCEDURAL:]

    # ── Negative patterns ─────────────────────────────────────────────────────

    def add_negative_pattern(self, description: str, context: str = "", outcome: str = ""):
        self.data["negative_patterns"].append({
            "description": description.lower(),
            "context": context,
            "outcome": outcome,
            "hits": 0,
            "ts": datetime.now().isoformat(),
        })
        self.data["negative_patterns"] = self.data["negative_patterns"][-MAX_NEGATIVE_PATTERNS:]

    def detect(self, action: str) -> list:
        """Return negative patterns matching the action (≥50% keyword overlap)."""
        words = set(action.lower().split())
        matches = []
        for p in self.data["negative_patterns"]:
            kws = set(p["description"].split())
            if kws and len(words & kws) / len(kws) >= 0.5:
                p["hits"] += 1
                matches.append(p)
        return matches

    # ── Recall ────────────────────────────────────────────────────────────────

    def recall(self, query: str, k: int = 7) -> list:
        """Keyword-scored recall across all 3 layers."""
        words = set(query.lower().split())
        scored = []

        for entry in reversed(self.data["episodic"]):
            text = (entry.get("content", "") + " " + " ".join(entry.get("tags", []))).lower()
            score = sum(1 for w in words if w in text)
            if score:
                scored.append((score, "episodic", entry))

        for key, entry in self.data["semantic"].items():
            text = (key + " " + entry.get("value", "")).lower()
            score = sum(1 for w in words if w in text)
            if score:
                scored.append((score, "semantic", {"key": key, **entry}))

        for entry in reversed(self.data["procedural"]):
            text = (entry.get("pattern", "") + " " + " ".join(entry.get("tags", []))).lower()
            score = sum(1 for w in words if w in text)
            if score:
                scored.append((score, "procedural", entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:k]

    # ── Stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "episodic": len(self.data["episodic"]),
            "semantic": len(self.data["semantic"]),
            "procedural": len(self.data["procedural"]),
            "negative_patterns": len(self.data["negative_patterns"]),
            "sessions": self.data["meta"].get("sessions", 0),
        }

    def increment_sessions(self):
        self.data["meta"]["sessions"] = self.data["meta"].get("sessions", 0) + 1
