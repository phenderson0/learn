#!/usr/bin/env python3
"""distill_critique_merge — fold a critique pass's judgements into src/*.yaml (docs/distill.md §4a, §9).

  distill_critique_merge.py <pyramid_dir> <critique.jsonl>

Applies `validity` to bases (by index), `acceptability` to nodes, basis flags
(weak, missing-step, circular), node flag `unsupported`, and removes `premise`
on premise-wrong. Prints what it can't apply automatically (hedges,
premise-missing) for the builder to handle, and any target that got no judgement.
"""
import glob
import json
import sys
from pathlib import Path

import yaml

BASIS_FLAGS = {"weak", "missing-step", "circular"}


class Dumper(yaml.SafeDumper):
    pass


Dumper.add_representer(str, lambda d, s: d.represent_scalar(
    "tag:yaml.org,2002:str", s, style="|" if "\n" in s else None))


def main():
    root, crit = Path(sys.argv[1]), Path(sys.argv[2])
    files = {f: yaml.safe_load(open(f)) for f in sorted(glob.glob(str(root / "src" / "*.yaml")))}
    N = {n["id"]: n for nodes in files.values() for n in nodes}
    manual, applied, problems = [], 0, []
    for line in crit.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        j = json.loads(line)
        n = N.get(j.get("node"))
        if n is None:
            problems.append(f"unknown node {j.get('node')}")
            continue
        b = None
        if j.get("basis") is not None:
            try:
                b = n["bases"][int(j["basis"])]
            except (IndexError, ValueError, KeyError):
                problems.append(f"{n['id']}: no basis {j['basis']}")
                continue
        if "validity" in j and b is not None:
            b["validity"] = j["validity"]; applied += 1
        elif "acceptability" in j:
            n["acceptability"] = j["acceptability"]; applied += 1
        elif "flag" in j:
            f = j["flag"]
            if f in BASIS_FLAGS and b is not None:
                b.setdefault("flags", [])
                if f not in b["flags"]:
                    b["flags"].append(f)
                applied += 1
            elif f in BASIS_FLAGS:
                manual.append(f"{n['id']}: flag {f} without a basis index — {j.get('reason', '')}")
            elif f == "unsupported":
                n.setdefault("flags", [])
                if f not in n["flags"]:
                    n["flags"].append(f)
                applied += 1
            elif f == "premise-wrong":
                n.pop("premise", None); applied += 1
            else:
                manual.append(f"{n['id']}: {f} — {j.get('reason', '')}")
        elif "hedge" in j:
            manual.append(f"{n['id']}: hedge '{j['hedge']}' — {j.get('reason', '')}")
    for f, nodes in files.items():
        Path(f).write_text(yaml.dump(nodes, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=10_000), "utf-8")
    # coverage of judgements
    missing = []
    for n in N.values():
        core = [b for b in n.get("bases", []) if b["type"] != "illustration"]
        if not core and not n.get("acceptability"):
            missing.append(f"{n['id']}: leaf without acceptability")
        missing += [f"{n['id']}: basis without validity" for b in core if not b.get("validity")]
    print(f"applied {applied}")
    for x in problems:
        print("problem:", x)
    for x in missing:
        print("unjudged:", x)
    for x in manual:
        print("manual:", x)


if __name__ == "__main__":
    main()
