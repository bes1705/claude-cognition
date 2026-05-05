"""
Cross-machine sync via a private git remote.
~/.cognition becomes a git repo — push/pull syncs memory across machines.

Setup (one-time):
  cognition sync init --remote git@github.com:you/my-cognition.git

Daily:
  cognition sync push    # after a session
  cognition sync pull    # at the start of a new machine session
  cognition sync status  # see what's changed
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from .config import COGNITION_DIR


def _git(args: list, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=COGNITION_DIR,
        capture_output=True,
        text=True,
        check=check,
    )


def _is_git_repo() -> bool:
    r = _git(["rev-parse", "--is-inside-work-tree"], check=False)
    return r.returncode == 0


def init(remote: str) -> None:
    """Initialize ~/.cognition as a git repo and set remote."""
    if not _is_git_repo():
        _git(["init", "-b", "main"])
        print(f"[sync] Initialized git repo in {COGNITION_DIR}")
    else:
        print(f"[sync] Already a git repo — configuring remote")

    # .gitignore — exclude logs, keep graph + memories
    gi = COGNITION_DIR / ".gitignore"
    gi.write_text("*.log\n*.tmp\n", encoding="utf-8")

    # Set remote
    remotes = _git(["remote"], check=False).stdout.strip().split()
    if "origin" in remotes:
        _git(["remote", "set-url", "origin", remote])
    else:
        _git(["remote", "add", "origin", remote])

    print(f"[sync] Remote: {remote}")

    # Initial commit if nothing exists
    r = _git(["status", "--porcelain"], check=False)
    if r.stdout.strip():
        _git(["add", "."])
        _git(["commit", "-m", "cognition: initial sync setup"])
        print("[sync] Initial commit created")

    print("[sync] Done — run `cognition sync push` to upload")


def push() -> None:
    """Commit all changes and push to remote."""
    if not _is_git_repo():
        print("[sync] ERROR: Not initialized. Run: cognition sync init --remote <url>")
        sys.exit(1)

    r = _git(["status", "--porcelain"], check=False)
    if not r.stdout.strip():
        print("[sync] Nothing to push — graph is up to date")
        return

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    _git(["add", "."])
    _git(["commit", "-m", f"cognition sync {ts}"])
    result = _git(["push", "-u", "origin", "main"], check=False)
    if result.returncode == 0:
        print(f"[sync] Pushed to remote ({ts})")
    else:
        print(f"[sync] Push failed:\n{result.stderr}")
        sys.exit(1)


def pull() -> None:
    """Pull latest memory from remote and rebase."""
    if not _is_git_repo():
        print("[sync] ERROR: Not initialized. Run: cognition sync init --remote <url>")
        sys.exit(1)

    result = _git(["pull", "--rebase", "origin", "main"], check=False)
    if result.returncode == 0:
        print(f"[sync] Pulled from remote\n{result.stdout.strip()}")
    else:
        print(f"[sync] Pull failed:\n{result.stderr}")
        sys.exit(1)


def status() -> None:
    """Show sync status."""
    if not _is_git_repo():
        print("[sync] Not initialized. Run: cognition sync init --remote <url>")
        return

    remote = _git(["remote", "get-url", "origin"], check=False).stdout.strip()
    log = _git(["log", "--oneline", "-5"], check=False).stdout.strip()
    dirty = _git(["status", "--porcelain"], check=False).stdout.strip()

    print(f"\n── Cognition Sync Status ─────────────")
    print(f"  Remote : {remote or 'none'}")
    print(f"  Dirty  : {'yes — run sync push' if dirty else 'clean'}")
    print(f"  Recent commits:")
    for line in log.splitlines():
        print(f"    {line}")
    print("──────────────────────────────────────\n")
