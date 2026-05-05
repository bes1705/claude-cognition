"""
cognition CLI — persistent 3-layer cognitive memory for Claude Code.

Commands:
  save      Save a memory  (--type decision|learning|pattern|avoid|fact)
  recall    Search memories by keyword
  inject    Output session context (used by SessionStart hook)
  detect    Check action against negative patterns
  auto-capture  Auto-snapshot at session end (used by Stop hook)
  status    Show graph stats
  graph     Dump full graph as JSON
"""
import sys
import json
import argparse
from pathlib import Path

from .capture import save, auto_capture
from .inject import print_inject
from .detect import print_detect
from .graph import CognitionGraph


def cmd_save(args):
    content = " ".join(args.content)
    msg = save(content, kind=args.type, project=args.project, tags=args.tags or [])
    print(msg)


def cmd_recall(args):
    query = " ".join(args.query)
    graph = CognitionGraph()
    results = graph.recall(query, k=args.k)
    if not results:
        print(f"[cognition] No memories matching: {query}")
        return
    print(f"\n[cognition] Top {len(results)} memories for '{query}':\n")
    for score, layer, entry in results:
        if layer == "episodic":
            print(f"  [{layer}] {entry['content'][:120]}")
            print(f"           project={entry.get('project','')} · ts={entry.get('ts','')[:10]}\n")
        elif layer == "semantic":
            print(f"  [{layer}] {entry['key']}: {entry['value'][:80]}\n")
        elif layer == "procedural":
            print(f"  [{layer}] {entry['pattern'][:120]}\n")


def cmd_inject(args):
    print_inject(args.project)


def cmd_detect(args):
    action = " ".join(args.action)
    print_detect(action)


def cmd_auto_capture(args):
    auto_capture(Path(args.cwd) if args.cwd else None)


def cmd_status(args):
    graph = CognitionGraph()
    s = graph.stats()
    print("\n── Cognition Status ─────────────────")
    print(f"  Sessions     : {s['sessions']}")
    print(f"  Episodic     : {s['episodic']} memories")
    print(f"  Semantic     : {s['semantic']} facts")
    print(f"  Procedural   : {s['procedural']} patterns")
    print(f"  Guards       : {s['negative_patterns']} negative patterns")
    print(f"  Storage      : ~/.cognition/")
    print("─────────────────────────────────────\n")


def cmd_graph(args):
    graph = CognitionGraph()
    print(json.dumps(graph.data, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        prog="cognition",
        description="Persistent 3-layer cognitive memory for Claude Code",
    )
    sub = parser.add_subparsers(dest="command")

    # save
    p_save = sub.add_parser("save", help="Save a memory")
    p_save.add_argument("content", nargs="+")
    p_save.add_argument("--type", "-t", default="episodic",
                        choices=["episodic", "decision", "learning", "pattern", "avoid", "fact"])
    p_save.add_argument("--project", "-p", default="")
    p_save.add_argument("--tags", nargs="*")
    p_save.set_defaults(func=cmd_save)

    # recall
    p_recall = sub.add_parser("recall", help="Search memories")
    p_recall.add_argument("query", nargs="+")
    p_recall.add_argument("--k", type=int, default=7)
    p_recall.set_defaults(func=cmd_recall)

    # inject
    p_inject = sub.add_parser("inject", help="Output session context (SessionStart hook)")
    p_inject.add_argument("--project", "-p", default="")
    p_inject.set_defaults(func=cmd_inject)

    # detect
    p_detect = sub.add_parser("detect", help="Check action against negative patterns")
    p_detect.add_argument("action", nargs="+")
    p_detect.set_defaults(func=cmd_detect)

    # auto-capture
    p_ac = sub.add_parser("auto-capture", help="Auto-snapshot at session end (Stop hook)")
    p_ac.add_argument("--cwd", default="")
    p_ac.set_defaults(func=cmd_auto_capture)

    # status
    p_status = sub.add_parser("status", help="Show graph stats")
    p_status.set_defaults(func=cmd_status)

    # graph
    p_graph = sub.add_parser("graph", help="Dump full graph as JSON")
    p_graph.set_defaults(func=cmd_graph)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
