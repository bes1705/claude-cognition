"""
Save memories explicitly or auto-capture from trusted project sources only.
Trusted sources: git log, git diff --stat, modified file list. Never tool outputs.
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path
from .graph import CognitionGraph, _git_project_id
from .config import MEMORIES_DIR, AUTO_CAPTURE_DEDUP_DAYS


def _git_log(cwd: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "log", "--oneline", "-5"],
            cwd=cwd, stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except Exception:
        return ""


def _git_diff_stat(cwd: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "diff", "--stat", "HEAD~1"],
            cwd=cwd, stderr=subprocess.DEVNULL, text=True,
        ).strip()[:300]
    except Exception:
        return ""


def _has_new_commits(cwd: Path) -> bool:
    """True if there are commits in the last 2 hours."""
    try:
        out = subprocess.check_output(
            ["git", "log", "--oneline", "--since=2 hours ago"],
            cwd=cwd, stderr=subprocess.DEVNULL, text=True,
        ).strip()
        return bool(out)
    except Exception:
        return False


def save(content: str, kind: str = "episodic", project: str = "", tags: list = None) -> str:
    graph = CognitionGraph()
    project = project or _git_project_id()
    tags = tags or []

    if kind == "decision":
        ok = graph.add_episodic(f"[DECISION] {content}", project=project,
                                tags=tags + ["decision"], kind="decision")
    elif kind == "learning":
        ok = graph.add_episodic(f"[LEARNING] {content}", project=project,
                                tags=tags + ["learning"], kind="learning")
    elif kind == "pattern":
        ok = graph.add_procedural(content, project=project, tags=tags)
    elif kind == "avoid":
        ok = graph.add_negative_pattern(content, context=project)
    elif kind == "fact":
        key = content.split(":")[0].strip() if ":" in content else content[:40]
        val = content.split(":", 1)[1].strip() if ":" in content else content
        graph.set_semantic(key, val)
        ok = True
    else:
        ok = graph.add_episodic(content, project=project, tags=tags, kind=kind)

    graph.save()

    if ok:
        date_str = datetime.now().strftime("%Y-%m-%d")
        mem_file = MEMORIES_DIR / f"{date_str}_{project[:30]}_{kind}.md"
        with open(mem_file, "a", encoding="utf-8") as f:
            f.write(f"- [{kind}] {content}\n")
        return f"[cognition] Saved ({kind}): {content[:80]}"
    return f"[cognition] Skipped (duplicate within {AUTO_CAPTURE_DEDUP_DAYS}d): {content[:60]}"


def auto_capture(cwd: Path = None) -> None:
    """
    Auto-capture at session end (Stop hook).
    Only captures trusted git sources. Skips if no new commits and no manual saves.
    Marks entries as kind='auto' so they're excluded from injection by default.
    """
    cwd = cwd or Path.cwd()
    graph = CognitionGraph()
    graph.increment_sessions()
    project = os.environ.get("COGNITION_PROJECT", "") or _git_project_id(cwd)

    # Skip if no new commits since last session (avoid polluting episodic with noise)
    if not _has_new_commits(cwd):
        graph.save()
        s = graph.stats()
        print(f"[cognition] Auto-capture skipped (no new commits) — session #{s['sessions']}")
        return

    log = _git_log(cwd)
    diff = _git_diff_stat(cwd)

    if log:
        snapshot = f"[AUTO] {datetime.now().strftime('%Y-%m-%d')} git: {log[:200]}"
        if diff:
            snapshot += f"\nchanges: {diff[:150]}"
        graph.add_episodic(snapshot, project=project, tags=["auto", "snapshot"], kind="auto")

    graph.save()
    s = graph.stats()
    print(
        f"[cognition] Auto-capture — session #{s['sessions']} · "
        f"{s['episodic']} episodic · {s['procedural']} patterns · "
        f"{s['negative_patterns']} guards"
    )
