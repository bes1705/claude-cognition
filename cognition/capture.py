"""
Save memories explicitly or auto-capture from project context.
Called manually: cognition save --type decision "chose X over Y because Z"
Called by Stop hook: cognition auto-capture
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path
from .graph import CognitionGraph
from .config import MEMORIES_DIR


def _git_context(cwd: Path) -> str:
    try:
        log = subprocess.check_output(
            ["git", "log", "--oneline", "-10"], cwd=cwd, stderr=subprocess.DEVNULL, text=True
        )
        diff = subprocess.check_output(
            ["git", "diff", "--stat", "HEAD~1"], cwd=cwd, stderr=subprocess.DEVNULL, text=True
        )
        return f"Recent commits:\n{log}\nRecent changes:\n{diff}"
    except Exception:
        return ""


def save(content: str, kind: str = "episodic", project: str = "", tags: list = None):
    """Save a single memory to the graph."""
    graph = CognitionGraph()
    project = project or Path.cwd().name

    if kind == "decision":
        graph.add_episodic(f"[DECISION] {content}", project=project, tags=(tags or []) + ["decision"])
    elif kind == "learning":
        graph.add_episodic(f"[LEARNING] {content}", project=project, tags=(tags or []) + ["learning"])
    elif kind == "pattern":
        graph.add_procedural(content, project=project, tags=tags or [])
    elif kind == "avoid":
        graph.add_negative_pattern(content, context=project)
    elif kind == "fact":
        key = content.split(":")[0].strip() if ":" in content else content[:40]
        val = content.split(":", 1)[1].strip() if ":" in content else content
        graph.set_semantic(key, val)
    else:
        graph.add_episodic(content, project=project, tags=tags or [])

    graph.save()

    date_str = datetime.now().strftime("%Y-%m-%d")
    mem_file = MEMORIES_DIR / f"{date_str}_{project[:30]}_{kind}.md"
    with open(mem_file, "a", encoding="utf-8") as f:
        f.write(f"- [{kind}] {content}\n")

    return f"[cognition] Saved ({kind}): {content[:80]}"


def auto_capture(cwd: Path = None):
    """Auto-capture project context at session end (Stop hook)."""
    cwd = cwd or Path.cwd()
    graph = CognitionGraph()
    graph.increment_sessions()
    project = os.environ.get("COGNITION_PROJECT", cwd.name)

    ctx = _git_context(cwd)
    if ctx:
        graph.add_episodic(
            f"[AUTO] Session end snapshot\n{ctx[:500]}",
            project=project,
            tags=["auto", "snapshot"],
        )

    graph.save()
    s = graph.stats()
    print(
        f"[cognition] Auto-capture done — "
        f"{s['episodic']} episodic · {s['procedural']} patterns · "
        f"{s['negative_patterns']} guards · session #{s['sessions']}"
    )
