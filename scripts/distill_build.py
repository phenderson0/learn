#!/usr/bin/env python3
"""distill_build — check a pyramid and render its views (docs/distill.md §5, §7, §8).

  distill_build.py <pyramid_dir>            check, then render if there are no errors
  distill_build.py <pyramid_dir> --check    check only

Reads every node from <pyramid_dir>/src/*.yaml, checks the structural rules and
anchors against source/source.md, computes levels, premises, satellites and the
interface, then writes nodes/<id>.md, index.md, map.md (human mode) and updates
manifest.json. Exit code 1 if any check fails.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from distill_ingest import normalize  # noqa: E402

BASIS_TYPES = {"derivation", "generalization", "support", "illustration"}
LATERAL_TYPES = {"objects", "rebuts", "qualifies", "contrasts", "same-as"}
BASIS_FLAGS = {"weak", "missing-step", "circular"}
NODE_FLAGS = {"unsupported", "repeated"}
MAX_FAN_IN, INDEX_BUDGET = 7, 1500  # tokens


def words(s):
    return len((s or "").split())


def tokens(s):
    return round(len(s) / 4)  # rough: ~4 chars per token


class Pyramid:
    def __init__(self, root: Path):
        self.root = root
        self.slug = root.name
        self.manifest = json.loads((root / "manifest.json").read_text("utf-8"))
        self.errors, self.warnings = [], []
        self.nodes = {}
        for f in sorted((root / "src").glob("*.yaml")):
            for n in yaml.safe_load(f.read_text("utf-8")) or []:
                if n["id"] in self.nodes:
                    self.errors.append(f"duplicate id {n['id']} ({f.name})")
                n.setdefault("bases", []), n.setdefault("lateral", []), n.setdefault("flags", [])
                n.setdefault("anchors", [])
                self.nodes[n["id"]] = n
        self.paras = {}
        for m in re.finditer(r"^\*\*¶(\d+)\*\* (.*)$", (root / "source" / "source.md").read_text("utf-8"), re.M):
            self.paras[int(m.group(1))] = m.group(2)

    # ---------- graph ----------
    def inputs(self, n, upward_only=True):
        out = []
        for b in n["bases"]:
            if upward_only and "circular" in b.get("flags", []):
                continue
            out += b["from"]
        return out

    def analyse(self):
        N = self.nodes
        self.parents = defaultdict(list)
        for n in N.values():
            for i in self.inputs(n, upward_only=False):
                self.parents[i].append(n["id"])
        # levels (longest path down) + cycle detection
        self.level, state = {}, {}

        def lvl(i, stack):
            if state.get(i) == 1:
                self.errors.append(f"cycle in upward edges: {' -> '.join(stack + [i])}")
                return 0
            if i in self.level:
                return self.level[i]
            state[i] = 1
            ins = [x for x in self.inputs(N[i]) if x in N]
            self.level[i] = 1 + max((lvl(x, stack + [i]) for x in ins), default=-1)
            state[i] = 2
            return self.level[i]

        for i in N:
            lvl(i, [])
        tops = [i for i in N if not self.parents[i]]
        # main pyramid = tops that sit above some input; a satellite is a top joined to it only laterally
        main_tops = [i for i in tops if self.level[i] == max(self.level[t] for t in tops)]
        self.apex = main_tops[0] if len(main_tops) == 1 else None
        if not self.apex:
            self.errors.append(f"expected one apex, found {main_tops}")
            return
        self.main = set()
        stack = [self.apex]
        while stack:
            i = stack.pop()
            if i not in self.main:
                self.main.add(i)
                stack += [x for x in self.inputs(N[i], upward_only=False) if x in N]
        self.satellites = [i for i in N if i not in self.main]
        joined = set()
        for i in self.satellites:
            for e in N[i]["lateral"]:
                if e["target"] in self.main:
                    joined.add(i)
            for j in self.main:
                if any(e["target"] == i for e in N[j]["lateral"]):
                    joined.add(i)
        changed = True
        while changed:  # satellites joined through other satellites or their own inputs
            changed = False
            for i in self.satellites:
                if i in joined:
                    continue
                linked = any(e["target"] in joined for e in N[i]["lateral"]) \
                    or any(i in self.inputs(N[j], False) for j in joined) \
                    or any(e["target"] == i for j in joined for e in N[j]["lateral"])
                if linked:
                    joined.add(i)
                    changed = True
        for i in self.satellites:
            if i not in joined:
                self.errors.append(f"orphan: {i} is connected to nothing in the pyramid")
        # premises, two definitions
        self.premises = [i for i, n in N.items() if n["kind"] == "idea" and n["origin"] == "source"
                         and all(b["type"] == "illustration" for b in n["bases"])]
        self.premises_author = [i for i in self.premises if N[i].get("voice") == "author"]
        # interface
        iface, frontier = [self.apex], [self.apex]
        while frontier:
            nxt = [x for f in frontier for x in self.inputs(N[f]) if x not in iface]
            iface += list(dict.fromkeys(nxt))
            if len(iface) >= 3 or not nxt:
                break
            frontier = nxt
        self.interface = iface

    # ---------- checks ----------
    def check(self):
        N = self.nodes
        for i, n in N.items():
            where = f"{i}:"
            if n.get("kind") not in {"idea", "detail", "mount"}:
                self.errors.append(f"{where} bad kind {n.get('kind')}")
            if n.get("origin") not in {"source", "structural", "gap"}:
                self.errors.append(f"{where} bad origin {n.get('origin')}")
            if n["origin"] == "source" and n.get("voice") not in {"author", "reported", "opponent"}:
                self.errors.append(f"{where} source node needs a voice")
            for f in n["flags"]:
                if f not in NODE_FLAGS:
                    self.errors.append(f"{where} bad node flag {f}")
            fan_in = len(self.inputs(n, upward_only=False))
            if fan_in > MAX_FAN_IN:
                self.errors.append(f"{where} fan-in {fan_in} > {MAX_FAN_IN}")
            for b in n["bases"]:
                if b.get("type") not in BASIS_TYPES:
                    self.errors.append(f"{where} bad basis type {b.get('type')}")
                if not b.get("how"):
                    self.errors.append(f"{where} basis without how")
                for f in b.get("flags", []):
                    if f not in BASIS_FLAGS:
                        self.errors.append(f"{where} bad basis flag {f}")
                for x in b["from"]:
                    if x not in N:
                        self.errors.append(f"{where} basis input {x} doesn't exist")
                if n["origin"] == "structural" and b["type"] != "generalization":
                    self.errors.append(f"{where} structural node with {b['type']} basis")
            for e in n["lateral"]:
                if e.get("type") not in LATERAL_TYPES:
                    self.errors.append(f"{where} bad lateral type {e.get('type')}")
                if e["target"] not in N and ":" not in e["target"]:
                    self.errors.append(f"{where} lateral target {e['target']} doesn't exist")
            # grounding + anchors
            if n["origin"] == "source" and not n["anchors"]:
                self.errors.append(f"{where} source node without anchors")
            if n["origin"] in {"structural", "gap"} and n["anchors"]:
                self.errors.append(f"{where} {n['origin']} node must not have anchors")
            for a in n["anchors"]:
                p = self.paras.get(a.get("p"))
                if p is None:
                    self.errors.append(f"{where} anchor ¶{a.get('p')} doesn't exist")
                elif normalize(a["q"]) not in p:
                    hit = [k for k, v in self.paras.items() if normalize(a["q"]) in v]
                    self.errors.append(f"{where} quote not found in ¶{a['p']}"
                                       + (f" (found in ¶{hit})" if hit else " (not found anywhere)")
                                       + f": {a['q'][:60]}…")
            # sizes
            if words(n.get("label")) > 6:
                self.errors.append(f"{where} T0 label {words(n['label'])} words > 6")
            if words(n.get("claim")) > 30:
                self.errors.append(f"{where} T1 claim {words(n['claim'])} words > 30")
            if words(n.get("t2")) > 150:
                self.errors.append(f"{where} T2 {words(n['t2'])} words > 150")
            if not n.get("t2"):
                self.warnings.append(f"{where} no T2")
        # lateral edge that duplicates a basis relation
        for i, n in N.items():
            for e in n["lateral"]:
                if e["target"] in N and i in self.inputs(N[e["target"]], False):
                    self.warnings.append(f"{i}: lateral {e['type']} -> {e['target']} duplicates a basis input")

    # ---------- rendering ----------
    def link(self, i):
        return f"[[{self.slug}/nodes/{i}|{self.nodes[i]['label']}]]"

    def tag(self, i):
        n = self.nodes[i]
        bits = []
        if n["kind"] != "idea":
            bits.append(n["kind"])
        if n["origin"] != "source":
            bits.append(n["origin"])
        if n.get("voice") and n["voice"] != "author":
            bits.append(n["voice"])
        return f" ({', '.join(bits)})" if bits else ""

    def line(self, i):
        n = self.nodes[i]
        return f"- `{i}`{self.tag(i)}: {n['label']} / {n['claim']}"

    def mermaid(self, i, kids):
        def q(x):
            return self.nodes[x]["label"].replace('"', "'")
        lines = ["```mermaid", "graph BT", f'  {i}["{q(i)}"]']
        for k in kids:
            lines.append(f'  {k}["{q(k)}"] --> {i}')
        return "\n".join(lines + ["```"])

    def render_node(self, i):
        n = self.nodes[i]
        meta = f"*{n['kind']} · origin {n['origin']}" + (f" · voice {n['voice']}" if n.get("voice") else "") \
            + f" · level {self.level[i]}" + (" · premise" if i in self.premises else "") \
            + (" · satellite" if i in self.satellites else "") + "*"
        out = [f"# {n['label']}", "", f"**T1:** {n['claim']}", "", meta]
        if n["flags"]:
            out.append(f"\nFlags: {', '.join(n['flags'])}")
        if n["bases"]:
            out += ["", "## Inputs"]
            for b in n["bases"]:
                fl = f" [{', '.join(b['flags'])}]" if b.get("flags") else ""
                out.append(f"\n**{b['type']}**{fl}: {b['how']}")
                out += [self.line(x) for x in b["from"] if x in self.nodes]
        if n["lateral"] or any(e["target"] == i for m in self.nodes.values() for e in m["lateral"]):
            out += ["", "## Lateral"]
            out += [f"- {e['type']} → `{e['target']}`: {self.nodes[e['target']]['label']}"
                    for e in n["lateral"] if e["target"] in self.nodes]
            out += [f"- ← {e['type']} from `{j}`{self.tag(j)}: {m['label']}"
                    for j, m in self.nodes.items() for e in m["lateral"] if e["target"] == i]
        if self.parents[i]:
            out += ["", "## Used by"] + [f"- `{p}`: {self.nodes[p]['label']}" for p in self.parents[i]]
        if self.manifest.get("mode", "human") == "human" and n["bases"]:
            out += ["", self.mermaid(i, [x for x in self.inputs(n, False) if x in self.nodes])]
        out += ["", "## T2", (n.get("t2") or "").strip()]
        out += ["", "## T3"] + [f"- ¶{a['p']}: \"{a['q']}\"" for a in n["anchors"]]
        if n.get("residual"):
            out.append(f"- Residual: {n['residual'].strip()}")
        links = sorted(set(self.inputs(n, False)) | set(self.parents[i])
                       | {e["target"] for e in n["lateral"] if e["target"] in self.nodes})
        out += ["", "<!-- links for Obsidian's graph -->", " ".join(self.link(x) for x in links)]
        return "\n".join(out) + "\n"

    def render_index(self):
        N = self.nodes
        head = [f"# {self.manifest['title']} — index", "",
                f"Apex: `{self.apex}`. Each node file starts with its inputs at T0/T1, so go deeper one node at a time.",
                "Tags: kind/origin/voice when not idea/source/author.", ""]
        body, seen, frontier, depth = [], set(), [self.apex], 0
        while frontier:
            block = [f"## Depth {depth}"] + [self.line(i) for i in frontier]
            if tokens("\n".join(head + body + block)) > INDEX_BUDGET and body:
                body.append(f"\n*Stops at depth {depth - 1}. Deeper nodes: open a node file and follow its inputs.*")
                break
            body += block + [""]
            seen |= set(frontier)
            frontier = list(dict.fromkeys(x for f in frontier for x in self.inputs(N[f], False)
                                          if x not in seen and N[x]["kind"] == "idea"))
            depth += 1
        sat = [f"- `{i}`{self.tag(i)}: {N[i]['label']}" for i in self.satellites]
        tail = ["## Satellites (joined only by lateral edges)"] + sat
        return "\n".join(head + body + [""] + tail) + "\n"

    def render_map(self):
        kids = [x for x in self.inputs(self.nodes[self.apex], False)]
        return "\n".join([f"# {self.manifest['title']}", "", f"**{self.nodes[self.apex]['claim']}**", "",
                          self.mermaid(self.apex, kids), "",
                          "Open any node to see its own inputs. Each view shows at most 7.", ""]
                         + [f"- {self.link(k)}: {self.nodes[k]['claim']}" for k in kids]) + "\n"

    def write(self):
        nd = self.root / "nodes"
        nd.mkdir(exist_ok=True)
        for f in nd.glob("*.md"):
            f.unlink()
        for i in self.nodes:
            (nd / f"{i}.md").write_text(self.render_node(i), "utf-8")
        index = self.render_index()
        (self.root / "index.md").write_text(index, "utf-8")
        if self.manifest.get("mode", "human") == "human":
            (self.root / "map.md").write_text(self.render_map(), "utf-8")
        self.manifest["interface"] = self.interface
        (self.root / "manifest.json").write_text(json.dumps(self.manifest, indent=2, ensure_ascii=False) + "\n", "utf-8")
        return index

    def stats(self, index=None):
        N = self.nodes
        by = defaultdict(int)
        for n in N.values():
            by[n["kind"]] += 1
            if n.get("voice") == "opponent":
                by["opponent"] += 1
        node_tokens = sum(tokens((self.root / "nodes" / f"{i}.md").read_text("utf-8"))
                          for i in N if (self.root / "nodes" / f"{i}.md").exists())
        src_tokens = tokens((self.root / "source" / "source.md").read_text("utf-8"))
        anchored = {a["p"] for n in N.values() for a in n["anchors"]}
        unanchored = [p for p in sorted(self.paras) if p not in anchored]
        lines = [
            f"nodes: {len(N)} ({', '.join(f'{k} {v}' for k, v in sorted(by.items()))})",
            f"levels: apex at {self.level.get(self.apex)}; satellites {len(self.satellites)}",
            f"interface: {self.interface}",
            f"premises: {len(self.premises)} (author voice only: {len(self.premises_author)})",
            f"source ¶ with no anchor: {unanchored}",
            f"tokens: source {src_tokens}, all node files {node_tokens}"
            + (f", index.md {tokens(index)}" if index else ""),
        ]
        return "\n".join(lines)


def main():
    root = Path(sys.argv[1])
    p = Pyramid(root)
    p.check()
    if not p.errors:
        p.analyse()
    for w in p.warnings:
        print("warn:", w)
    for e in p.errors:
        print("ERROR:", e)
    if p.errors:
        sys.exit(1)
    index = None if "--check" in sys.argv else p.write()
    print(p.stats(index))


if __name__ == "__main__":
    main()
