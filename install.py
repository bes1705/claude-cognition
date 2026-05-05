"""
One-command install: python install.py
Adds cognition hooks to Claude Code settings.json
"""
import json
import subprocess
import sys
from pathlib import Path

CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
HOOK_INJECT = "python -m cognition inject"
HOOK_CAPTURE = "python -m cognition auto-capture"


def install():
    # 1. Install the package
    print("[cognition] Installing package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])

    # 2. Patch Claude Code settings.json
    print(f"[cognition] Patching {CLAUDE_SETTINGS}...")
    settings = {}
    if CLAUDE_SETTINGS.exists():
        try:
            settings = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
        except Exception:
            pass

    hooks = settings.setdefault("hooks", {})

    # SessionStart — inject context
    start_hooks = hooks.setdefault("SessionStart", [])
    if not any(HOOK_INJECT in str(h) for h in start_hooks):
        start_hooks.append({"command": HOOK_INJECT})

    # Stop — auto-capture
    stop_hooks = hooks.setdefault("Stop", [])
    if not any(HOOK_CAPTURE in str(h) for h in stop_hooks):
        stop_hooks.append({"command": HOOK_CAPTURE})

    CLAUDE_SETTINGS.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n✅ Cognition installed successfully!")
    print("   SessionStart hook → cognition inject")
    print("   Stop hook         → cognition auto-capture")
    print("\nQuick start:")
    print("  cognition save --type decision 'chose React over Vue because team knows it'")
    print("  cognition save --type avoid 'never modify trading config under pressure'")
    print("  cognition recall 'trading'")
    print("  cognition status\n")


if __name__ == "__main__":
    install()
