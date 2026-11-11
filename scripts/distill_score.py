#!/usr/bin/env python3
"""distill_score — turn judge verdicts into the coverage metrics (docs/distill.md §7).

  distill_score.py <pyramid_dir> <claims.jsonl> <judge.jsonl> [<regen.jsonl>] [--label NAME]

Prints recall by weight (recovered = 1, partial = 0.5), voice errors, spurious and
extra counts, lost claims, and traversal cost; appends the report to coverage.md.
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

TARGETS = {"core": 1.0, "supporting": 0.95, "illustrative": 0.80}


def jsonl(p):
    return [json.loads(l) for l in Path(p).read_text("utf-8").splitlines() if l.strip()]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else Path(args[1]).stem
    root, claims, verdicts = Path(args[0]), jsonl(args[1]), jsonl(args[2])
    regen = jsonl(args[3]) if len(args) > 3 else []
    if label in args:
        args.remove(label)
    by_ref = {v["ref"]: v for v in verdicts if "ref" in v}
    missing = [c["id"] for c in claims if c["id"] not in by_ref]
    score, total, lost = defaultdict(float), Counter(), defaultdict(list)
    counts = Counter(v["verdict"] for v in verdicts)
    for c in claims:
        w, v = c["weight"], by_ref.get(c["id"], {}).get("verdict", "lost")
        total[w] += 1
        score[w] += {"recovered": 1, "partial": 0.5}.get(v, 0)
        if v != "recovered":
            lost[w].append(f"{c['id']} ({v}): {c['claim']}" + (f" — {by_ref[c['id']].get('note', '')}" if c["id"] in by_ref else ""))
    opened = next((r.get("opened") for r in regen if "opened" in r), None)
    out = [f"## {label} — {date.today().isoformat()}", "",
           "| Weight | Claims | Recall | Target | |", "|---|---|---|---|---|"]
    for w in ("core", "supporting", "illustrative"):
        if total[w]:
            r = score[w] / total[w]
            out.append(f"| {w} | {total[w]} | {r:.0%} | {TARGETS[w]:.0%} | {'✓' if r >= TARGETS[w] else '✗'} |")
    out += ["", f"Verdicts: {dict(counts)}"]
    if missing:
        out.append(f"Reference claims the judge skipped (counted lost): {len(missing)}")
    if opened is not None:
        out.append(f"Traversal: {len(opened)} files opened")
    for w in ("core", "supporting", "illustrative"):
        if lost[w]:
            out += ["", f"### Not fully recovered: {w}"] + [f"- {x}" for x in lost[w]]
    spur = [v for v in verdicts if v.get("verdict") == "spurious"]
    if spur:
        out += ["", "### Spurious"] + [f"- {v['regen']}: {v.get('note', '')}" for v in spur]
    report = "\n".join(out) + "\n"
    with (root / "coverage.md").open("a", encoding="utf-8") as f:
        f.write("\n" + report)
    print(report)


if __name__ == "__main__":
    main()
