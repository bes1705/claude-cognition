"""
Generate context block for session injection.
Called by SessionStart hook — output read by Claude as system context.
Wraps in <cognition-memory> so Claude knows source is local graph, not instructions.
"""
import os
from pathlib import Path
from datetime import datetime
from .graph import CognitionGraph, _git_project_id
from .config import INJECT_TOP_K, INJECT_MAX_TOKENS


def _token_estimate(text: str) -> int:
    return len(text) // 4


def _trim_to_budget(lines: list, max_tokens: int) -> list:
    out, used = [], 0
    for line in lines:
        cost = _token_estimate(line) + 1
        if used + cost > max_tokens:
            out.append(f"<!-- cognition: {max_tokens}-token budget reached, remaining memories omitted -->")
            break
        out.append(line)
        used += cost
    return out


def inject(project: str = "") -> str:
    project = project or os.environ.get("COGNITION_PROJECT", "") or _git_project_id()
    graph = CognitionGraph()
    s = graph.stats()

    if s["episodic"] + s["procedural"] + s["semantic"] == 0:
        return ""

    inner = [
        f"# Cognition — {project} · {datetime.now().strftime('%Y-%m-%d')} · session #{s['sessions']}",
        "",
    ]

    # Top memories — project-specific + global (cross-project), auto excluded
    hits = graph.recall(project, k=INJECT_TOP_K, include_auto=False)
    global_hits = [h for h in hits if h[2].get("global") or h[2].get("project", "") == ""]
    project_hits = [h for h in hits if not (h[2].get("global") or h[2].get("project", "") == "")]

    if hits:
        if project_hits:
            inner.append(f"## Memory — {project}")
        if global_hits:
            inner.append("## Memory — global")
        inner.append("")
        for _, layer, entry in hits[:6]:
            if layer == "episodic":
                inner.append(f"- {entry['content'][:120]}")
            elif layer == "semantic":
                inner.append(f"- {entry['key']}: {entry['value'][:80]}")
            elif layer == "procedural":
                inner.append(f"- [pattern] {entry['pattern'][:120]}")
        inner.append("")

    # Semantic facts (by access frequency)
    if graph.data["semantic"]:
        inner.append("## Facts")
        facts = sorted(
            graph.data["semantic"].items(),
            key=lambda x: x[1].get("access_count", 0), reverse=True,
        )
        for key, val in facts[:4]:
            inner.append(f"- {key}: {val['value'][:80]}")
        inner.append("")

    # Guards (by hit count — most-triggered first)
    if graph.data["negative_patterns"]:
        inner.append("## Guards")
        guards = sorted(graph.data["negative_patterns"],
                        key=lambda x: x.get("hits", 0), reverse=True)
        for p in guards[:3]:
            line = f"- AVOID: {p['description'][:100]}"
            if p.get("outcome"):
                line += f" → {p['outcome'][:60]}"
            inner.append(line)
        inner.append("")

    graph.save()
    trimmed_inner = _trim_to_budget(inner, INJECT_MAX_TOKENS)

    # Wrap in cognition-memory marker so Claude distinguishes from instructions
    lines = [
        f'<cognition-memory source="local-graph" project="{project}" sessions="{s["sessions"]}">',
        *trimmed_inner,
        "</cognition-memory>",
    ]
    return "\n".join(lines)


def print_inject(project: str = ""):
    ctx = inject(project)
    if ctx:
        print(ctx)
