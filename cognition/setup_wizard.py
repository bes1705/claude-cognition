"""
cognition setup — interactive onboarding for non-technical users.
Guides through 3 questions, patches Claude Code settings.json, saves first memories.
"""
import json
import subprocess
import sys
from pathlib import Path
from .graph import CognitionGraph, _git_project_id
from .config import COGNITION_DIR


CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"

BANNER = """
╔═══════════════════════════════════════════════╗
║         cognition — setup wizard              ║
║   Persistent memory for Claude Code           ║
╚═══════════════════════════════════════════════╝
"""

def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"{prompt}{suffix}: ").strip()
        return val or default
    except (KeyboardInterrupt, EOFError):
        print("\n[setup] Cancelled.")
        sys.exit(0)


def _patch_hooks() -> bool:
    """Add SessionStart and Stop hooks to Claude Code settings.json."""
    settings = {}
    if CLAUDE_SETTINGS.exists():
        try:
            settings = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
        except Exception:
            pass

    hooks = settings.setdefault("hooks", {})

    start = hooks.setdefault("SessionStart", [])
    stop = hooks.setdefault("Stop", [])

    hook_inject = "python -m cognition inject"
    hook_capture = "python -m cognition auto-capture"

    changed = False
    if not any(hook_inject in str(h) for h in start):
        start.append({"command": hook_inject})
        changed = True
    if not any(hook_capture in str(h) for h in stop):
        stop.append({"command": hook_capture})
        changed = True

    if changed:
        CLAUDE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        CLAUDE_SETTINGS.write_text(
            json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return changed


def run() -> None:
    print(BANNER)
    print("This takes 60 seconds. You'll never re-explain yourself to Claude again.\n")

    # Step 1 — Project
    project = _git_project_id()
    print(f"Step 1/3 — Your current project")
    project = _ask("  Project name", default=project)

    # Step 2 — Stack / key fact
    print(f"\nStep 2/3 — One fact Claude should always know about you")
    print("  Examples: 'stack: FastAPI + React + Postgres'")
    print("            'deploy: VPS Hetzner 178.x.x.x port 22'")
    print("            'language: Python, prefer stdlib over heavy deps'")
    fact = _ask("  Your fact")

    # Step 3 — One thing to never repeat
    print(f"\nStep 3/3 — One mistake you never want to repeat")
    print("  Examples: 'never push to main without running tests'")
    print("            'never modify trading bot config under pressure'")
    guard = _ask("  Your guard (or press Enter to skip)")

    # Save to graph
    print("\n── Saving to memory graph... ", end="", flush=True)
    g = CognitionGraph()

    if fact:
        key = fact.split(":")[0].strip() if ":" in fact else "key-fact"
        val = fact.split(":", 1)[1].strip() if ":" in fact else fact
        g.set_semantic(key, val)

    if guard:
        g.add_negative_pattern(guard, context=project, outcome="user-defined guard")

    g.increment_sessions()
    g.save()
    print("done")

    # Patch hooks
    print("── Patching Claude Code settings.json... ", end="", flush=True)
    patched = _patch_hooks()
    print("done" if patched else "already configured")

    # Verify pip install
    print("── Verifying cognition CLI... ", end="", flush=True)
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-e",
             str(Path(__file__).parent.parent), "-q"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        print("done")
    except Exception:
        print("skipped (already installed)")

    print(f"""
╔═══════════════════════════════════════════════╗
║              Setup complete!                  ║
╚═══════════════════════════════════════════════╝

  Memory saved   : {COGNITION_DIR / 'graph.json'}
  Hooks active   : SessionStart → inject · Stop → auto-capture

  Next session Claude will know:
    · {fact or '(add more with: cognition save --type fact "...")'}
  {"  Guard active  : " + guard[:60] if guard else ""}

  Useful commands:
    cognition save --type decision "chose X over Y because Z"
    cognition save --type avoid "never do X without Y"
    cognition save --global "rule that applies to all projects"
    cognition recall "topic"
    cognition status

  Cross-machine sync (optional):
    cognition sync init --remote git@github.com:you/my-cognition.git
    cognition sync push

  Docs: https://github.com/bes1705/claude-cognition
""")
