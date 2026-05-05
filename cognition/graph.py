"""3-layer cognitive graph: episodic / semantic / procedural."""
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from .config import GRAPH_FILE, MAX_EPISODIC, MAX_PROCEDURAL, MAX_NEGATIVE_PATTERNS

# ── Type boost (reviewer priority: guards > decisions > facts > patterns > auto) ──
TYPE_BOOST = {
    "guard": 4.0, "avoid": 4.0,
    "decision": 3.0,
    "fact": 2.0, "semantic": 2.0,
    "learning": 1.5,
    "pattern": 2.0, "procedural": 2.0,
    "auto": 0.2,   # auto-captures excluded from injection by default
    "episodic": 1.0,
}

# Scoring weights  (recency, frequency, project, type, keyword)
W = (0.25, 0.20, 0.20, 0.20, 0.15)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _days_ago(ts: str) -> float:
    try:
        t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - t).total_seconds() / 86400)
    except Exception:
        return 30.0


def _recency_decay(ts: str) -> float:
    """Exponential decay: 1.0 today → 0.5 at ~21 days → 0.1 at ~70 days."""
    return math.exp(-_days_ago(ts) / 30.0)


def _frequency_score(access_count: int) -> float:
    return math.log1p(access_count)


def _jaccard(a: str, b: str) -> float:
    ta = set(a.lower().split())
    tb = set(b.lower().split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _sanitize(text: str) -> str:
    """Strip prompt-injection attempts and HTML from user-supplied content."""
    text = re.sub(r"<[^>]{0,200}>", "", text)
    danger = [
        "ignore previous instructions", "ignore all instructions",
        "system prompt", "you are now", "disregard",
        "forget everything", "new persona",
    ]
    lower = text.lower()
    for d in danger:
        if d in lower:
            idx = lower.index(d)
            text = text[:idx] + "[removed]" + text[idx + len(d):]
            lower = text.lower()
    return text[:2000]


def _git_project_id(cwd: Path = None) -> str:
    """Derive stable project ID from git remote > dirname."""
    cwd = cwd or Path.cwd()
    try:
        remote = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd, stderr=subprocess.DEVNULL, text=True,
        ).strip()
        name = remote.rstrip("/").replace(".git", "").split("/")[-1]
        return name or cwd.name
    except Exception:
        return cwd.name


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
            "meta": {"created": _now_iso(), "sessions": 0},
        }

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # ── Dedup check ───────────────────────────────────────────────────────────

    def _is_duplicate(self, content: str, layer: str = "episodic", threshold: float = 0.80) -> bool:
        """Jaccard dedup — skip if ≥80% similar to any entry from the last 7 days."""
        entries = self.data.get(layer, [])
        recent = [e for e in entries if _days_ago(e.get("ts", "")) <= 7]
        key = "content" if layer == "episodic" else "pattern"
        return any(_jaccard(content, e.get(key, "")) >= threshold for e in recent)

    # ── Episodic ──────────────────────────────────────────────────────────────

    def add_episodic(self, content: str, project: str = "", tags: list = None,
                     kind: str = "episodic", skip_dedup: bool = False) -> bool:
        content = _sanitize(content)
        if not skip_dedup and self._is_duplicate(content, "episodic"):
            return False
        self.data["episodic"].append({
            "content": content,
            "project": project,
            "tags": tags or [],
            "kind": kind,
            "ts": _now_iso(),
            "access_count": 0,
        })
        self.data["episodic"] = self.data["episodic"][-MAX_EPISODIC:]
        return True

    # ── Semantic ──────────────────────────────────────────────────────────────

    def set_semantic(self, key: str, value: str, confidence: float = 0.9):
        key = _sanitize(key)[:80]
        value = _sanitize(value)
        self.data["semantic"][key] = {
            "value": value,
            "confidence": confidence,
            "updated": _now_iso(),
            "access_count": 0,
        }

    # ── Procedural ────────────────────────────────────────────────────────────

    def add_procedural(self, pattern: str, project: str = "", tags: list = None,
                       skip_dedup: bool = False) -> bool:
        pattern = _sanitize(pattern)
        if not skip_dedup and self._is_duplicate(pattern, "procedural"):
            return False
        self.data["procedural"].append({
            "pattern": pattern,
            "project": project,
            "tags": tags or [],
            "ts": _now_iso(),
            "access_count": 0,
        })
        self.data["procedural"] = self.data["procedural"][-MAX_PROCEDURAL:]
        return True

    # ── Negative patterns ─────────────────────────────────────────────────────

    def add_negative_pattern(self, description: str, context: str = "",
                             outcome: str = "", keywords: list = None,
                             pattern_regex: str = "") -> bool:
        description = _sanitize(description).lower()
        if self._is_duplicate(description, "negative_patterns" if False else "episodic"):
            pass  # dedup not applied to guards — always add
        self.data["negative_patterns"].append({
            "description": description,
            "context": context[:200],
            "outcome": outcome[:200],
            "keywords": keywords or [],      # explicit trigger keywords
            "pattern_regex": pattern_regex,  # optional regex trigger
            "hits": 0,
            "ts": _now_iso(),
        })
        self.data["negative_patterns"] = self.data["negative_patterns"][-MAX_NEGATIVE_PATTERNS:]
        return True

    def detect(self, action: str) -> list:
        """Match guards via explicit keywords first, then regex, then keyword overlap."""
        action_lower = action.lower()
        action_words = {w for w in action_lower.split() if len(w) > 2}
        matches = []

        for p in self.data["negative_patterns"]:
            matched = False

            # 1. Explicit keywords (deterministic)
            explicit = [k.lower() for k in p.get("keywords", [])]
            if explicit and all(k in action_lower for k in explicit):
                matched = True

            # 2. Regex (deterministic)
            if not matched and p.get("pattern_regex"):
                try:
                    if re.search(p["pattern_regex"], action_lower):
                        matched = True
                except re.error:
                    pass

            # 3. Keyword overlap fallback (≥50% of guard words appear in action)
            if not matched:
                kws = {w for w in p["description"].split() if len(w) > 2}
                if kws and len(action_words & kws) / len(kws) >= 0.50:
                    matched = True

            if matched:
                p["hits"] += 1
                matches.append(p)

        return matches

    # ── Combined recall (5-factor scoring) ───────────────────────────────────

    def recall(self, query: str, k: int = 7, include_auto: bool = False) -> list:
        """Score = w_rec×recency + w_freq×frequency + w_proj×project + w_type×type + w_kw×keyword."""
        words = {w for w in query.lower().split() if len(w) > 2}
        project = _git_project_id()
        scored = []

        def _score(entry: dict, layer: str, text: str, content_key: str = "content") -> float:
            kind = entry.get("kind", layer)
            if kind == "auto" and not include_auto:
                return -1.0

            kw = sum(1 for w in words if w in text) / max(len(words), 1) if words else 0.0
            rec = _recency_decay(entry.get("ts", entry.get("updated", "")))
            freq = _frequency_score(entry.get("access_count", 0))
            proj = 1.0 if entry.get("project", "") == project else 0.0
            tboost = TYPE_BOOST.get(kind, 1.0)

            return W[0]*rec + W[1]*freq + W[2]*proj + W[3]*(tboost/4.0) + W[4]*kw

        for entry in self.data["episodic"]:
            text = (entry.get("content", "") + " " + " ".join(entry.get("tags", []))).lower()
            if not words or any(w in text for w in words):
                s = _score(entry, "episodic", text)
                if s >= 0:
                    scored.append((s, "episodic", entry))

        for key, entry in self.data["semantic"].items():
            text = (key + " " + entry.get("value", "")).lower()
            if not words or any(w in text for w in words):
                freq = _frequency_score(entry.get("access_count", 0))
                tboost = TYPE_BOOST["semantic"]
                s = W[1]*freq + W[3]*(tboost/4.0) + W[4]*(sum(1 for w in words if w in text)/max(len(words),1))
                scored.append((s, "semantic", {"key": key, **entry}))

        for entry in self.data["procedural"]:
            text = (entry.get("pattern", "") + " " + " ".join(entry.get("tags", []))).lower()
            if not words or any(w in text for w in words):
                s = _score(entry, "procedural", text, "pattern")
                if s >= 0:
                    scored.append((s, "procedural", entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:k]

        for _, layer, entry in top:
            if "access_count" in entry:
                entry["access_count"] += 1

        return top

    # ── Forget ────────────────────────────────────────────────────────────────

    def forget(self, query: str) -> int:
        words = {w.lower() for w in query.split() if len(w) > 2}
        removed = 0
        for layer, key in [("episodic", "content"), ("procedural", "pattern")]:
            before = len(self.data[layer])
            self.data[layer] = [
                e for e in self.data[layer]
                if not any(w in e.get(key, "").lower() for w in words)
            ]
            removed += before - len(self.data[layer])
            if removed:
                return removed
        keys = [k for k in self.data["semantic"]
                if any(w in k.lower() or w in self.data["semantic"][k]["value"].lower()
                       for w in words)]
        for k in keys[:1]:
            del self.data["semantic"][k]
            removed += 1
        return removed

    # ── Edit ──────────────────────────────────────────────────────────────────

    def edit(self, query: str, new_content: str) -> bool:
        words = {w.lower() for w in query.split() if len(w) > 2}
        new_content = _sanitize(new_content)
        for entry in self.data["episodic"]:
            if any(w in entry.get("content", "").lower() for w in words):
                entry["content"] = new_content
                entry["ts"] = _now_iso()
                return True
        for entry in self.data["procedural"]:
            if any(w in entry.get("pattern", "").lower() for w in words):
                entry["pattern"] = new_content
                entry["ts"] = _now_iso()
                return True
        return False

    # ── Merge ─────────────────────────────────────────────────────────────────

    def merge(self, old_query: str, new_content: str) -> bool:
        return self.edit(old_query, new_content)

    # ── Prune ─────────────────────────────────────────────────────────────────

    def prune(self, older_than_days: int = 90, kind: str = "") -> int:
        removed = 0
        for layer, key in [("episodic", "content"), ("procedural", "pattern")]:
            before = len(self.data[layer])
            self.data[layer] = [
                e for e in self.data[layer]
                if not (_days_ago(e.get("ts", "")) > older_than_days
                        and (not kind or e.get("kind", "") == kind))
            ]
            removed += before - len(self.data[layer])
        return removed

    # ── Compact ───────────────────────────────────────────────────────────────

    def compact(self, threshold: float = 0.75) -> int:
        """Merge episodic entries that are ≥threshold similar (keep newest, discard older)."""
        entries = self.data["episodic"]
        to_remove = set()
        for i in range(len(entries)):
            if i in to_remove:
                continue
            for j in range(i + 1, len(entries)):
                if j in to_remove:
                    continue
                if _jaccard(entries[i]["content"], entries[j]["content"]) >= threshold:
                    # Keep the newer one (higher index = appended later = more recent)
                    to_remove.add(i)
                    break
        self.data["episodic"] = [e for idx, e in enumerate(entries) if idx not in to_remove]
        return len(to_remove)

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
