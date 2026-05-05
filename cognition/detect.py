"""
Temporal pattern detection — warns before repeating a known mistake.
Usage: cognition detect "I'm about to modify the trading bot config"
"""
from .graph import CognitionGraph


def detect(action: str) -> list[dict]:
    graph = CognitionGraph()
    matches = graph.detect(action)
    graph.save()
    return matches


def print_detect(action: str):
    matches = detect(action)
    if not matches:
        print(f"[cognition] No known negative patterns for: {action[:60]}")
        return

    print(f"\n⚠️  COGNITION ALERT — {len(matches)} pattern(s) detected:\n")
    for m in matches:
        print(f"  Pattern : {m['description']}")
        if m.get("outcome"):
            print(f"  Outcome : {m['outcome']}")
        if m.get("context"):
            print(f"  Context : {m['context']}")
        print(f"  Hits    : {m['hits']} time(s)\n")
