"""
cognition CLI — persistent 3-layer cognitive memory for Claude Code.

Commands:
  save          Save a memory  (--type decision|learning|pattern|avoid|fact)
  recall        Search memories by keyword
  inject        Output session context (SessionStart hook)
  detect        Check action against negative patterns
  auto-capture  Auto-snapshot at session end (Stop hook)
  forget        Remove entries matching keywords
  edit          Update content of an entry
  merge         Alias for edit (find old → replace with new)
  prune         Remove old entries by age and/or type
  compact       Merge near-duplicate episodic entries
  status        Show graph stats
  graph         Dump full graph as JSON
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
    results = graph.recall(query, k=args.k, include_auto=args.include_auto)
    if not results:
        print(f"[cognition] No memories matching: {query}")
        return
    print(f"\n[cognition] Top {len(results)} for '{query}':\n")
    for score, layer, entry in results:
        if layer == "episodic":
            print(f"  [{layer}] {entry['content'][:120]}")
            print(f"           ts={entry.get('ts','')[:10]} · hits={entry.get('access_count',0)} · score={score:.3f}\n")
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


def cmd_forget(args):
    query = " ".join(args.query)
    graph = CognitionGraph()
    n = graph.forget(query)
    graph.save()
    print(f"[cognition] Removed {n} entr{'y' if n==1 else 'ies'} matching: {query}" if n
          else f"[cognition] No entry found matching: {query}")


def cmd_edit(args):
    query = " ".join(args.query)
    graph = CognitionGraph()
    ok = graph.edit(query, args.new)
    graph.save()
    print(f"[cognition] Updated: '{query}' → '{args.new[:60]}'" if ok
          else f"[cognition] No entry found matching: {query}")


def cmd_merge(args):
    query = " ".join(args.old_query)
    graph = CognitionGraph()
    ok = graph.merge(query, args.new)
    graph.save()
    print(f"[cognition] Merged: '{query}' → '{args.new[:60]}'" if ok
          else f"[cognition] No entry found matching: {query}")


def cmd_prune(args):
    graph = CognitionGraph()
    n = graph.prune(older_than_days=args.older_than, kind=args.type)
    graph.save()
    print(f"[cognition] Pruned {n} entr{'y' if n==1 else 'ies'} older than {args.older_than}d"
          + (f" of type '{args.type}'" if args.type else ""))


def cmd_compact(args):
    graph = CognitionGraph()
    n = graph.compact(threshold=args.threshold)
    graph.save()
    print(f"[cognition] Compacted {n} near-duplicate entr{'y' if n==1 else 'ies'} (threshold={args.threshold})")


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
    p = sub.add_parser("save", help="Save a memory")
    p.add_argument("content", nargs="+")
    p.add_argument("--type", "-t", default="episodic",
                   choices=["episodic", "decision", "learning", "pattern", "avoid", "fact"])
    p.add_argument("--project", "-p", default="")
    p.add_argument("--tags", nargs="*")
    p.set_defaults(func=cmd_save)

    # recall
    p = sub.add_parser("recall", help="Search memories")
    p.add_argument("query", nargs="+")
    p.add_argument("--k", type=int, default=7)
    p.add_argument("--include-auto", action="store_true")
    p.set_defaults(func=cmd_recall)

    # inject
    p = sub.add_parser("inject", help="Output session context (SessionStart hook)")
    p.add_argument("--project", "-p", default="")
    p.set_defaults(func=cmd_inject)

    # detect
    p = sub.add_parser("detect", help="Check action against negative patterns")
    p.add_argument("action", nargs="+")
    p.set_defaults(func=cmd_detect)

    # auto-capture
    p = sub.add_parser("auto-capture", help="Auto-snapshot at session end (Stop hook)")
    p.add_argument("--cwd", default="")
    p.set_defaults(func=cmd_auto_capture)

    # forget
    p = sub.add_parser("forget", help="Remove entries matching keywords")
    p.add_argument("query", nargs="+")
    p.set_defaults(func=cmd_forget)

    # edit
    p = sub.add_parser("edit", help="Update content of an entry")
    p.add_argument("query", nargs="+", help="Keywords to find the entry")
    p.add_argument("--new", required=True, help="New content")
    p.set_defaults(func=cmd_edit)

    # merge
    p = sub.add_parser("merge", help="Replace entry content (find old → write new)")
    p.add_argument("old_query", nargs="+")
    p.add_argument("--new", required=True)
    p.set_defaults(func=cmd_merge)

    # prune
    p = sub.add_parser("prune", help="Remove old entries")
    p.add_argument("--older-than", type=int, default=90, metavar="DAYS")
    p.add_argument("--type", default="", choices=["", "auto", "decision", "learning", "pattern"])
    p.set_defaults(func=cmd_prune)

    # compact
    p = sub.add_parser("compact", help="Merge near-duplicate entries")
    p.add_argument("--threshold", type=float, default=0.75)
    p.set_defaults(func=cmd_compact)

    # status
    p = sub.add_parser("status", help="Show graph stats")
    p.set_defaults(func=cmd_status)

    # graph
    p = sub.add_parser("graph", help="Dump full graph as JSON")
    p.set_defaults(func=cmd_graph)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
