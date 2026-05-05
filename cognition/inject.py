"""
Generate context block for session injection.
Called by SessionStart hook — output is read by Claude as system context.
"""
import os
from pathlib import Path
from datetime import datetime
from .graph import CognitionGraph
from .config import INJECT_TOP_K


def inject(project: str = "", verbose: bool = False) -> str:
    project = project or os.environ.get("COGNITION_PROJECT", Path.cwd().name)
    graph = CognitionGraph()
    s = graph.stats()

    if s["episodic"] + s["procedural"] + s["semantic"] == 0:
        return ""

    lines = [
        f"<!-- cognition v1.0 · {s['sessions']} sessions · {s['episodic']} memories -->",
        f"# Cognition Context — {project} · {datetime.now().strftime('%Y-%m-%d')}",
        "",
    ]

    # Project-specific memories first
    project_hits = graph.recall(project, k=INJECT_TOP_K)
    if project_hits:
        lines.append("## Recent memory")
        for _, layer, entry in project_hits[:5]:
            if layer == "episodic":
                lines.append(f"- {entry['content'][:120]}")
            elif layer == "semantic":
                lines.append(f"- {entry['key']}: {entry['value'][:80]}")
            elif layer == "procedural":
                lines.append(f"- [pattern] {entry['pattern'][:120]}")
        lines.append("")

    # Semantic facts (always useful)
    if graph.data["semantic"]:
        lines.append("## Known facts")
        for key, val in list(graph.data["semantic"].items())[:5]:
            lines.append(f"- {key}: {val['value'][:80]}")
        lines.append("")

    # Top procedural patterns
    if graph.data["procedural"]:
        lines.append("## Active patterns")
        for p in reversed(graph.data["procedural"][-3:]):
            lines.append(f"- {p['pattern'][:120]}")
        lines.append("")

    # Negative patterns (guards)
    if graph.data["negative_patterns"]:
        lines.append("## Guards — avoid repeating")
        for p in graph.data["negative_patterns"][-3:]:
            lines.append(f"- AVOID: {p['description'][:100]}")
        lines.append("")

    return "\n".join(lines)


def print_inject(project: str = ""):
    ctx = inject(project)
    if ctx:
        print(ctx)
