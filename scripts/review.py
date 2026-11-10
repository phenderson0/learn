#!/usr/bin/env python3
"""review — the concept ledger behind /learn:review.

Every finished lesson records its concepts here. Review sessions pick the
concepts that have gone longest without being touched and skip the ones that
are still cooling down after a recent review.

Ledger: <project>/.claude/learn-ledger.json

  review.py add                   read {"topic","note","concepts":[{"name","summary"}]} on stdin
  review.py pick [-n N]           the N oldest concepts that are due (default 8)
  review.py list [--topic TEXT]   every concept, with when it's next due
  review.py mark --pass ID... --fail ID...   record a review

Cooldown after a review: 7 days x 2^(passes in a row), capped at 180 days.
A pass doubles the gap; a fail resets it to 7 days. A newly learned concept is
first due 7 days after the lesson.
"""
import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

BASE_DAYS = 7
MAX_DAYS = 180


def ledger_path() -> Path:
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    return root / ".claude" / "learn-ledger.json"


def load() -> dict:
    try:
        return json.loads(ledger_path().read_text("utf-8"))
    except FileNotFoundError:
        return {"next_id": 1, "concepts": []}


def save(ledger: dict) -> None:
    p = ledger_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", "utf-8")


def last_touched(c: dict) -> date:
    return date.fromisoformat(c.get("last_reviewed") or c["learned"])


def due_date(c: dict) -> date:
    gap = min(BASE_DAYS * 2 ** c.get("streak", 0), MAX_DAYS)
    return last_touched(c) + timedelta(days=gap)


def fmt(c: dict, today: date) -> str:
    due = due_date(c)
    when = "due now" if due <= today else f"cooling until {due.isoformat()}"
    reviewed = c.get("last_reviewed") or "never"
    note = f"  note: {c['note']}" if c.get("note") else ""
    return (f"[{c['id']}] {c['topic']} :: {c['name']} — {c['summary']}\n"
            f"     learned {c['learned']}, last reviewed {reviewed}, {when}{note}")


def cmd_add(_args) -> None:
    data = json.load(sys.stdin)
    ledger = load()
    today = date.today().isoformat()
    added = []
    for item in data["concepts"]:
        c = {
            "id": ledger["next_id"],
            "topic": data["topic"],
            "name": item["name"],
            "summary": item.get("summary", ""),
            "note": data.get("note") or "",
            "learned": item.get("learned") or data.get("learned") or today,
            "last_reviewed": None,
            "streak": 0,
        }
        ledger["next_id"] += 1
        ledger["concepts"].append(c)
        added.append(c)
    save(ledger)
    print(f"Added {len(added)} concept(s) under '{data['topic']}': "
          + ", ".join(f"[{c['id']}] {c['name']}" for c in added))


def cmd_pick(args) -> None:
    today = date.today()
    concepts = load()["concepts"]
    due = sorted((c for c in concepts if due_date(c) <= today), key=last_touched)
    if not concepts:
        print("Ledger is empty: no lessons recorded yet.")
        return
    if not due:
        soonest = min(concepts, key=due_date)
        print(f"Nothing is due. {len(concepts)} concept(s) are cooling down; "
              f"the next is due {due_date(soonest).isoformat()}.")
        return
    picked = due[: args.n]
    print(f"{len(due)} concept(s) due; the {len(picked)} oldest:")
    for c in picked:
        print(fmt(c, today))


def cmd_list(args) -> None:
    today = date.today()
    concepts = load()["concepts"]
    if args.topic:
        t = args.topic.lower()
        concepts = [c for c in concepts if t in c["topic"].lower() or t in c["name"].lower()]
    if not concepts:
        print("No matching concepts in the ledger.")
        return
    for c in sorted(concepts, key=lambda c: (c["topic"], c["id"])):
        print(fmt(c, today))


def cmd_mark(args) -> None:
    ledger = load()
    by_id = {c["id"]: c for c in ledger["concepts"]}
    today = date.today().isoformat()
    unknown = [i for i in args.passed + args.failed if i not in by_id]
    if unknown:
        sys.exit(f"Unknown id(s): {unknown}. Nothing recorded.")
    for i in args.passed:
        by_id[i]["streak"] = by_id[i].get("streak", 0) + 1
        by_id[i]["last_reviewed"] = today
    for i in args.failed:
        by_id[i]["streak"] = 0
        by_id[i]["last_reviewed"] = today
    save(ledger)
    for i in args.passed + args.failed:
        c = by_id[i]
        print(f"[{i}] {c['name']}: {'pass' if i in args.passed else 'fail'}, "
              f"next due {due_date(c).isoformat()}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("add")
    p = sub.add_parser("pick")
    p.add_argument("-n", type=int, default=8)
    p = sub.add_parser("list")
    p.add_argument("--topic")
    p = sub.add_parser("mark")
    p.add_argument("--pass", dest="passed", type=int, nargs="*", default=[])
    p.add_argument("--fail", dest="failed", type=int, nargs="*", default=[])
    args = ap.parse_args()
    {"add": cmd_add, "pick": cmd_pick, "list": cmd_list, "mark": cmd_mark}[args.cmd](args)


if __name__ == "__main__":
    main()
