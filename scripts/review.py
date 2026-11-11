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

Distill pyramids (learner confidence per node, docs/distill.md §4b). PYRAMID is
a path to distill/<slug> or just the slug:

  review.py frontier PYRAMID [-n N]     what the learner is ready for next, by priority
  review.py nodes PYRAMID [--all]       confidence per node (tested or inferred; --all for every node)
  review.py node-mark PYRAMID           read [{"node","level","result","self"?,"q"?}] on stdin
  review.py agree PYRAMID NODE STANCE [--reason TEXT]   agree | partly | disagree (contested nodes)
  review.py calibration                 self-rating vs results over the last 20 rated answers

`pick` also lists pyramid nodes that are due (recall confidence has halved).
Set LEARN_TODAY=YYYY-MM-DD to test with a different date.
"""
import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import confidence as conf  # noqa: E402  (pyramid code inside is imported lazily)

BASE_DAYS = 7
MAX_DAYS = 180


def project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def ledger_path() -> Path:
    return project_root() / ".claude" / "learn-ledger.json"


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
    today = conf.today().isoformat()
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
    today = conf.today()
    ledger = load()
    concepts = ledger["concepts"]
    due = sorted((c for c in concepts if due_date(c) <= today), key=last_touched)
    if not concepts and not ledger.get("nodes"):
        print("Ledger is empty: no lessons recorded yet.")
        return
    if concepts and not due:
        soonest = min(concepts, key=due_date)
        print(f"No concepts are due. {len(concepts)} concept(s) are cooling down; "
              f"the next is due {due_date(soonest).isoformat()}.")
    elif due:
        picked = due[: args.n]
        print(f"{len(due)} concept(s) due; the {len(picked)} oldest:")
        for c in picked:
            print(fmt(c, today))
    for slug, rel in sorted(ledger.get("pyramids", {}).items()):
        path = project_root() / rel
        if not (path / "manifest.json").exists():
            print(f"\nPyramid {slug}: not found at {rel}, skipped.")
            continue
        L = learner(ledger, path)
        nodes = L.due_nodes()
        if not nodes:
            dates = [d for d in (L.due(i) for i in L.teachable) if d]
            nxt = f"; the next is due {min(dates).isoformat()}" if dates else ""
            print(f"\nPyramid {slug}: no nodes due{nxt}.")
            continue
        print(f"\nPyramid {slug}: {len(nodes)} node(s) due; the {min(len(nodes), args.n)} most important:")
        for pr, i, d in nodes[: args.n]:
            print(fmt_node(L, i))


def cmd_list(args) -> None:
    today = conf.today()
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
    today = conf.today().isoformat()
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


# ---------- distill pyramids (docs/distill.md §4b) ----------

def resolve_pyramid(arg: str, ledger: dict) -> Path:
    root = project_root()
    known = ledger.get("pyramids", {}).get(arg)
    for cand in [Path(arg), root / arg, root / "distill" / arg] + ([root / known] if known else []):
        if (cand / "manifest.json").exists():
            return cand.resolve()
    sys.exit(f"No pyramid at {arg!r} (looked for a path, distill/{arg}, and the ledger's pyramids).")


def learner(ledger: dict, path: Path) -> "conf.Learner":
    p = conf.load_pyramid(path)
    renames = p.manifest.get("renames") or {}
    if renames and conf.migrate_renames(ledger, p.slug, renames):
        save(ledger)
    try:
        rel = str(path.resolve().relative_to(project_root().resolve()))
    except ValueError:
        rel = str(path.resolve())
    if ledger.setdefault("pyramids", {}).get(p.slug) != rel:
        ledger["pyramids"][p.slug] = rel
        save(ledger)
    return conf.Learner(p, ledger)


def pct(x) -> str:
    return "—" if x is None else f"{x * 100:.0f}"


def fmt_node(L, i: str, target: str = None, notes=()) -> str:
    n = L.N[i]
    tags = []
    if n.get("premise"):
        tags.append("premise: the author assumes this")
    if n.get("voice") and n["voice"] != "author":
        tags.append(f"voice: {n['voice']}")
    if n.get("acceptability") == "contested":
        tags.append("contested")
    if i in L.inferred and L.d["recall"][i] is None:
        tags.append("recall inferred")
    tags += list(notes)
    due = L.due(i)
    head = f"[{L.slug}#{i}]" + (f" → {target}" if target else "")
    return (f"{head} {n['label']} — {n['claim']}\n"
            f"     recall {pct(L.c['recall'][i])} · explain {pct(L.c['explain'][i])} · apply {pct(L.c['apply'][i])}"
            f" · grasp {L.grasp(i) or 'none'}" + (f" · due {due.isoformat()}" if due else "")
            + (f"\n     {'; '.join(tags)}" if tags else ""))


def cmd_frontier(args) -> None:
    ledger = load()
    L = learner(ledger, resolve_pyramid(args.pyramid, ledger))
    front = L.frontier()
    tested = sum(1 for i in L.teachable if L.records(i))
    print(f"{L.slug}: {len(L.teachable)} teachable nodes, {tested} tested, "
          f"{sum(1 for i in L.teachable if L.known(i, 'recall'))} known at recall. Apex: {L.p.apex}.")
    if not front:
        print("Nothing on the frontier: every node is known at every level.")
        return
    print(f"Frontier ({len(front)} nodes ready); the top {min(args.n, len(front))} by priority:")
    for pr, i, target, c, notes in front[: args.n]:
        print(fmt_node(L, i, target, notes))


def cmd_nodes(args) -> None:
    ledger = load()
    L = learner(ledger, resolve_pyramid(args.pyramid, ledger))
    shown = [i for i in L.teachable if args.all or L.records(i) or i in L.inferred]
    if not shown:
        print(f"{L.slug}: no node has been tested yet. Try `frontier`.")
        return
    order = {i: k for k, i in enumerate(sorted(L.teachable, key=lambda i: (-L.p.level[i], i)))}
    for i in sorted(shown, key=order.get):
        print(fmt_node(L, i))
    g = [L.grasp(i) for i in L.teachable]
    print(f"\n{L.slug}: grasp across {len(g)} nodes: "
          + ", ".join(f"{lv} {g.count(lv)}" for lv in conf.LEVELS) + f", none {g.count(None)}")


def cmd_node_mark(args) -> None:
    ledger = load()
    path = resolve_pyramid(args.pyramid, ledger)
    L = learner(ledger, path)
    data = json.load(sys.stdin)
    data = data.get("records", data) if isinstance(data, dict) else data
    problems = []
    for r in data:
        if r.get("node") not in L.teachable:
            problems.append(f"unknown or unteachable node {r.get('node')!r}")
        if r.get("level") not in conf.LEVELS:
            problems.append(f"{r.get('node')}: level must be one of {conf.LEVELS}")
        if r.get("result") not in conf.RESULT:
            problems.append(f"{r.get('node')}: result must be pass, partial or fail")
        if r.get("self") is not None and r["self"] not in conf.SELF:
            problems.append(f"{r.get('node')}: self must be sure, unsure or guess")
    if problems:
        sys.exit("Nothing recorded:\n  " + "\n  ".join(problems))
    t = conf.today().isoformat()
    for r in data:
        rec = {"t": t, "level": r["level"], "result": r["result"]}
        for k in ("self", "q"):
            if r.get(k):
                rec[k] = r[k]
        ledger.setdefault("nodes", {}).setdefault(f"{L.slug}#{r['node']}", {"records": []})["records"].append(rec)
    save(ledger)
    L = conf.Learner(L.p, ledger)
    print(f"Recorded {len(data)} answer(s).")
    for i in dict.fromkeys(r["node"] for r in data):
        print(fmt_node(L, i))
    bias, n = conf.calibration(ledger)
    if n >= 5:
        print(calibration_line(bias, n))


def cmd_agree(args) -> None:
    ledger = load()
    L = learner(ledger, resolve_pyramid(args.pyramid, ledger))
    if args.node not in L.teachable:
        sys.exit(f"Unknown node {args.node!r}.")
    if args.stance not in conf.STANCES:
        sys.exit("Stance must be agree, partly or disagree.")
    e = ledger.setdefault("nodes", {}).setdefault(f"{L.slug}#{args.node}", {"records": []})
    e["agree"] = {"t": conf.today().isoformat(), "stance": args.stance, "reason": args.reason or ""}
    save(ledger)
    note = "" if L.N[args.node].get("acceptability") == "contested" else \
        " (note: this node isn't rated contested; agreement is normally asked only on contested nodes)"
    print(f"[{L.slug}#{args.node}] stance: {args.stance}{note}. Confidence is unchanged.")


def calibration_line(bias, n) -> str:
    if bias > 0.2:
        verdict = "overconfident: you rate yourself higher than your answers show"
    elif bias < -0.2:
        verdict = "underconfident: your answers are better than you rate them"
    else:
        verdict = "well calibrated"
    return f"Calibration over {n} rated answers: bias {bias:+.2f}, {verdict}."


def cmd_calibration(_args) -> None:
    bias, n = conf.calibration(load())
    print("No self-rated answers yet." if not n else calibration_line(bias, n))


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
    p = sub.add_parser("frontier")
    p.add_argument("pyramid")
    p.add_argument("-n", type=int, default=8)
    p = sub.add_parser("nodes")
    p.add_argument("pyramid")
    p.add_argument("--all", action="store_true")
    p = sub.add_parser("node-mark")
    p.add_argument("pyramid")
    p = sub.add_parser("agree")
    p.add_argument("pyramid")
    p.add_argument("node")
    p.add_argument("stance")
    p.add_argument("--reason")
    sub.add_parser("calibration")
    args = ap.parse_args()
    {"add": cmd_add, "pick": cmd_pick, "list": cmd_list, "mark": cmd_mark,
     "frontier": cmd_frontier, "nodes": cmd_nodes, "node-mark": cmd_node_mark,
     "agree": cmd_agree, "calibration": cmd_calibration}[args.cmd](args)


if __name__ == "__main__":
    main()
