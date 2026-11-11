#!/usr/bin/env python3
"""distill_build — check a pyramid and render its views (docs/distill.md §5, §7, §8).

  distill_build.py <pyramid_dir>            check, then render if there are no errors
  distill_build.py <pyramid_dir> --check    check only

Reads every node from <pyramid_dir>/src/*.yaml, checks the structural rules and
anchors against source/source.md, computes levels, premises, satellites and the
interface, then writes nodes/<id>.md, index.md, and in human mode map.md,
map.canvas (Obsidian Canvas, apex at the top) and outline.md (foldable tree).
Updates manifest.json. Exit code 1 if any check fails.
"""
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from distill_ingest import normalize  # noqa: E402

BASIS_TYPES = {"derivation", "generalization", "support", "illustration"}
LATERAL_TYPES = {"objects", "rebuts", "qualifies", "applies", "contrasts", "same-as"}
LOCATOR_WORDS = 25  # quotes longer than this get a warning
# a point joining a claim to its reason, second limb or consequence (§3, atomic points)
COMPOUND = re.compile(r";|\b(because|since|so that|not only|but also|whereas|and therefore|and thus|and hence)\b", re.I)
BASIS_FLAGS = {"weak", "missing-step", "circular"}
NODE_FLAGS = {"unsupported", "repeated"}
MAX_FAN_IN, INDEX_BUDGET = 7, 1500  # tokens
VALIDITY = {"sound": 1.0, "plausible": 0.75, "weak": 0.4}
ACCEPTABILITY = {"uncontested": 0.95, "reasonable": 0.75, "contested": 0.5}
DEFAULT_V, DEFAULT_A = "plausible", "reasonable"  # used when the critique pass hasn't judged yet


def words(s):
    return len((s or "").split())


def tokens(s):
    return round(len(s) / 4)  # rough: ~4 chars per token


class Pyramid:
    def __init__(self, root: Path):
        self.root = root
        self.slug = root.name
        self.manifest = json.loads((root / "manifest.json").read_text("utf-8"))
        if "--mode" in sys.argv:
            self.manifest["mode"] = sys.argv[sys.argv.index("--mode") + 1]
        self.human = self.manifest.get("mode", "human") == "human"
        self.errors, self.warnings = [], []
        self.nodes = {}
        for f in sorted((root / "src").glob("*.yaml")):
            for n in yaml.safe_load(f.read_text("utf-8")) or []:
                if n["id"] in self.nodes:
                    self.errors.append(f"duplicate id {n['id']} ({f.name})")
                n.setdefault("bases", []), n.setdefault("lateral", []), n.setdefault("flags", [])
                n.setdefault("anchors", []), n.setdefault("points", [])
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
        self.premises = [i for i, n in N.items() if n.get("premise")]
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
                if b.get("validity") and b["validity"] not in VALIDITY:
                    self.errors.append(f"{where} bad validity {b['validity']}")
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
            if n.get("premise"):
                if n["kind"] != "idea" or n["origin"] != "source" or n.get("voice") != "author":
                    self.errors.append(f"{where} premise must be an author-voiced source idea")
                if any(b["type"] in {"derivation", "support"} for b in n["bases"]):
                    self.warnings.append(f"{where} premise has derivation/support bases")
            # grounding + anchors
            if n["origin"] == "source" and not n["anchors"]:
                self.errors.append(f"{where} source node without anchors")
            if n["origin"] in {"structural", "gap"} and n["anchors"]:
                self.errors.append(f"{where} {n['origin']} node must not have anchors")
            for a in n["anchors"]:
                if words(a.get("q")) > LOCATOR_WORDS:
                    self.warnings.append(f"{where} quote of {words(a['q'])} words (locator quotes should be <= {LOCATOR_WORDS})")
                p = self.paras.get(a.get("p"))
                if p is None:
                    self.errors.append(f"{where} anchor ¶{a.get('p')} doesn't exist")
                elif normalize(a["q"]) not in p:
                    hit = [k for k, v in self.paras.items() if normalize(a["q"]) in v]
                    self.errors.append(f"{where} quote not found in ¶{a['p']}"
                                       + (f" (found in ¶{hit})" if hit else " (not found anywhere)")
                                       + f": {a['q'][:60]}…")
            for pt in n["points"]:
                if not isinstance(pt, dict) or "p" not in pt or "c" not in pt:
                    self.errors.append(f"{where} point must be {{p, c}}: {pt}")
                elif pt["p"] not in self.paras:
                    self.errors.append(f"{where} point ¶{pt['p']} doesn't exist")
                elif words(pt["c"]) > 35:
                    self.errors.append(f"{where} point {words(pt['c'])} words > 35")
                elif COMPOUND.search(pt["c"]):
                    self.warnings.append(f"{where} point may be compound, split it (§3): {pt['c'][:60]}…")
            # sizes
            if words(n.get("label")) > 6:
                self.errors.append(f"{where} T0 label {words(n['label'])} words > 6")
            if n.get("acceptability") and n["acceptability"] not in ACCEPTABILITY:
                self.errors.append(f"{where} bad acceptability {n['acceptability']}")
            if words(n.get("claim")) > 35:
                self.errors.append(f"{where} T1 claim {words(n['claim'])} words > 35")
            if words(n.get("t2")) > 150:
                self.errors.append(f"{where} T2 {words(n['t2'])} words > 150")
            if not n.get("t2"):
                self.warnings.append(f"{where} no T2")
        # lateral edge that duplicates a basis relation
        for i, n in N.items():
            for e in n["lateral"]:
                if e["target"] in N and i in self.inputs(N[e["target"]], False):
                    self.warnings.append(f"{i}: lateral {e['type']} -> {e['target']} duplicates a basis input")

    # ---------- strength (spec §4a) ----------
    def compute_strength(self):
        N = self.nodes
        self.strength, self.contrib, self.defaulted = {}, {}, set()

        def validity(i, b):
            v = b.get("validity")
            if not v:
                self.defaulted.add(f"{i}:basis"); v = DEFAULT_V
            val = VALIDITY[v]
            if set(b.get("flags", [])) & {"weak", "missing-step"}:
                val = min(val, VALIDITY["plausible"])
            return val

        def s(i, stack=()):
            if i in self.strength:
                return self.strength[i]
            if i in stack:
                return 0.0
            n = N[i]
            core = [b for b in n["bases"] if b["type"] != "illustration" and "circular" not in b.get("flags", [])]
            if not core:
                a = n.get("acceptability")
                if not a:
                    self.defaulted.add(f"{i}:leaf"); a = DEFAULT_A
                val, parts = ACCEPTABILITY[a], []
            else:
                parts = []
                for b in core:
                    ins = [s(x, stack + (i,)) for x in b["from"] if x in N]
                    if not ins:
                        continue
                    v = validity(i, b)
                    if b["type"] == "derivation":
                        bv = v * min(ins)
                    elif b["type"] == "support":
                        bv = v * (1 - math.prod(1 - x for x in ins))
                    else:  # generalization
                        bv = v * (sum(ins) / len(ins)) * min(1, 0.5 + 0.1 * len(ins))
                    parts.append((bv, b))
                val = 1 - math.prod(1 - bv for bv, _ in parts) if parts else 0.0
            k = sum(len(b["from"]) for b in n["bases"] if b["type"] == "illustration")
            val = val + (1 - val) * min(0.1, 0.05 * k)
            # attacks: objections that target this node, softened by their strongest rebuttal
            for j, m in N.items():
                if any(e["type"] == "objects" and e["target"] == i for e in m["lateral"]):
                    a = s(j, stack + (i,))
                    reb = [s(r_, stack + (i,)) for r_, rn in N.items()
                           if any(e["type"] == "rebuts" and e["target"] == j for e in rn["lateral"])]
                    val *= 1 - 0.5 * a * (1 - max(reb, default=0.0))
            self.strength[i], self.contrib[i] = val, parts
            return val

        for i in N:
            s(i)

    def weakest_link(self):
        path, i = [], self.apex
        while True:
            path.append(f"{i} ({self.strength[i] * 100:.0f})")
            parts = self.contrib.get(i) or []
            if not parts:
                return path
            bv, b = min(parts, key=lambda p: p[0])
            ins = [x for x in b["from"] if x in self.nodes]
            i = min(ins, key=lambda x: self.strength[x])

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
        st = f" [{self.strength[i] * 100:.0f}]" if getattr(self, "strength", None) else ""
        return f"- `{i}`{self.tag(i)}{st}: {n['label']} / {n['claim']}"

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
            + f" · level {self.level[i]} · strength {self.strength[i] * 100:.0f}" \
            + (f" · {n['acceptability']}" if n.get("acceptability") else "") + (" · premise" if i in self.premises else "") \
            + (" · satellite" if i in self.satellites else "") + "*"
        out = [f"# {n['label']}", "", f"**T1:** {n['claim']}", "", meta]
        if n["flags"]:
            out.append(f"\nFlags: {', '.join(n['flags'])}")
        if n["bases"]:
            out += ["", "## Inputs"]
            for b in n["bases"]:
                fl = f" [{', '.join(b['flags'])}]" if b.get("flags") else ""
                fl += f" ({b['validity']})" if b.get("validity") else ""
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
        if self.human and n["bases"]:
            out += ["", self.mermaid(i, [x for x in self.inputs(n, False) if x in self.nodes])]
        out += ["", "## T2", (n.get("t2") or "").strip()]
        if n["points"]:
            out += ["", "## Also in the source"] + [f"- {pt['c']} (¶{pt['p']})" for pt in n["points"]]
        out += ["", "## T3"] + [f"- ¶{a['p']}: \"{a['q']}\"" for a in n["anchors"]]
        if n.get("residual"):
            out.append(f"- Residual: {n['residual'].strip()}")
        if self.human:
            links = sorted(set(self.inputs(n, False)) | set(self.parents[i])
                           | {e["target"] for e in n["lateral"] if e["target"] in self.nodes})
            out += ["", "<!-- links for Obsidian's graph -->", " ".join(self.link(x) for x in links)]
        return "\n".join(out) + "\n"

    def render_index(self):
        N = self.nodes
        head = [f"# {self.manifest['title']} — index", "",
                f"Apex: `{self.apex}`. Each node file starts with its inputs at T0/T1, so go deeper one node at a time.",
                "Tags: kind/origin/voice when not idea/source/author.", ""]
        def tail_for(shown):
            sat = [f"- `{i}`{self.tag(i)}: {N[i]['label']} ({e['type']} `{e['target']}`)"
                   for i in self.satellites for e in N[i]["lateral"] if e["target"] in shown]
            rest = len(self.satellites) - len(sat)
            return (["## Satellites attached to the nodes above"] + sat if sat else []) + \
                ([f"\n*{rest} more satellites: see each node's Lateral section.*"] if rest else [])

        body, seen, frontier, depth = [], set(), [self.apex], 0
        tail = tail_for(seen)
        while frontier:
            block = [f"## Depth {depth}"] + [self.line(i) for i in frontier]
            tail = tail_for(seen | set(frontier))
            if tokens("\n".join(head + body + block + tail)) > INDEX_BUDGET and body:
                # fill the overflowing depth with as many nodes as fit, then stop
                part = [f"## Depth {depth} (partial)"]
                for k in frontier:
                    trial = tail_for(seen | {x for x in frontier[:frontier.index(k) + 1]})
                    if tokens("\n".join(head + body + part + [self.line(k)] + trial)) > INDEX_BUDGET:
                        break
                    part.append(self.line(k)); seen.add(k)
                tail = tail_for(seen)
                if len(part) > 1:
                    body += part + [""]
                body.append(f"\n*Listing stops partway through depth {depth}. Deeper nodes: open a node file and follow its inputs.*")
                break
            body += block + [""]
            seen |= set(frontier)
            frontier = list(dict.fromkeys(x for f in frontier for x in self.inputs(N[f], False)
                                          if x not in seen and N[x]["kind"] == "idea"))
            depth += 1
        return "\n".join(head + body + [""] + tail) + "\n"

    def render_map(self):
        kids = [x for x in self.inputs(self.nodes[self.apex], False)]
        return "\n".join([f"# {self.manifest['title']}", "", f"**{self.nodes[self.apex]['claim']}**", "",
                          self.mermaid(self.apex, kids), "",
                          "Open any node to see its own inputs. Each view shows at most 7.", ""]
                         + [f"- {self.link(k)}: {self.nodes[k]['claim']}" for k in kids]) + "\n"

    # ---------- hierarchical views ----------
    def tree(self):
        """Spanning tree from the apex: each node hangs under its first parent (by basis order).
        Satellites hang under the main-pyramid node they're laterally joined to, marked with the edge type."""
        N = self.nodes
        kids, placed, how = defaultdict(list), {self.apex}, {}
        order = [self.apex]
        for i in order:
            for b in N[i]["bases"]:
                for x in b["from"]:
                    if x in N and x not in placed:
                        placed.add(x); kids[i].append(x); how[x] = b["type"]; order.append(x)
        pending = [i for i in N if i not in placed]
        while pending:
            progress = False
            for i in list(pending):
                if i in placed:
                    continue
                anchor = next((e["target"] for e in N[i]["lateral"] if e["target"] in placed), None)
                if anchor is None:
                    anchor = next((j for j in placed for e in N[j]["lateral"] if e["target"] == i), None)
                    t = next((e["type"] for e in N[anchor]["lateral"] if e["target"] == i), None) if anchor else None
                    label = f"← {t}" if t else None
                else:
                    label = next(e["type"] for e in N[i]["lateral"] if e["target"] == anchor)
                if anchor is None:
                    anchor = next((j for j in placed if i in self.inputs(N[j], False)), None)
                    label = "input" if anchor else None
                if anchor:
                    placed.add(i); kids[anchor].append(i); how[i] = label; pending.remove(i); progress = True
                    queue = [i]
                    for q in queue:
                        for b in N[q]["bases"]:
                            for x in b["from"]:
                                if x in N and x not in placed:
                                    placed.add(x); kids[q].append(x); how[x] = b["type"]; queue.append(x)
                                    pending.remove(x)
            if not progress:
                break
        return kids, how

    def color(self, i):
        n = self.nodes[i]
        if i == self.apex or i in self.interface:
            return "6"
        if n.get("voice") == "opponent":
            return "1"
        if n["origin"] != "source":
            return "2"
        if n["kind"] == "detail":
            return "4"
        if i in self.satellites:
            return "3"
        return None

    def render_canvas(self):
        N = self.nodes
        kids, how = self.tree()
        W, H, GX, GY = 340, 190, 40, 140
        pos, cursor = {}, [0]

        def place(i, depth):
            ch = kids[i]
            for c in ch:
                place(c, depth + 1)
            x = (pos[ch[0]][0] + pos[ch[-1]][0]) / 2 if ch else cursor[0]
            if not ch:
                cursor[0] += W + GX
            pos[i] = (x, depth * (H + GY))

        place(self.apex, 0)
        nodes, edges = [], []
        for i, (x, y) in pos.items():
            n = N[i]
            tag = self.tag(i).strip(" ()")
            text = f"**{n['label']}**" + (f"  \n*{tag}*" if tag else "") + f"\n\n{n['claim']}\n\n[[{self.slug}/nodes/{i}|open]]"
            card = {"id": i, "type": "text", "text": text, "x": round(x), "y": round(y), "width": W, "height": H}
            if self.color(i):
                card["color"] = self.color(i)
            nodes.append(card)
        k = 0
        for i, n in N.items():
            for b in n["bases"]:
                for x in b["from"]:
                    if x in pos and i in pos:
                        k += 1
                        e = {"id": f"e{k}", "fromNode": x, "fromSide": "top", "toNode": i, "toSide": "bottom"}
                        if b["type"] != "derivation":
                            e["label"] = b["type"]
                        if "circular" in b.get("flags", []):
                            e["color"] = "1"
                        edges.append(e)
            for e in n["lateral"]:
                if e["target"] in pos and i in pos:
                    k += 1
                    edges.append({"id": f"e{k}", "fromNode": i, "fromSide": "left", "toNode": e["target"],
                                  "toSide": "right", "label": e["type"], "color": "3"})
        return {"nodes": nodes, "edges": edges}

    def render_outline(self):
        N = self.nodes
        kids, how = self.tree()
        out = [f"# {self.manifest['title']} — outline", "",
               "The pyramid as a tree, apex first. Fold any item. A node with several parents appears under its first.",
               "Satellites appear under the node they are joined to, marked with the lateral edge (← means the edge points at this side).", ""]

        def walk(i, depth):
            n = N[i]
            rel = f"*{how[i]}* · " if i in how and how[i] not in ("derivation",) else ""
            out.append("\t" * depth + f"- {rel}{self.link(i)}{self.tag(i)}: {n['claim']}")
            for c in kids[i]:
                walk(c, depth + 1)

        walk(self.apex, 0)
        return "\n".join(out) + "\n"

    def write(self):
        nd = self.root / "nodes"
        nd.mkdir(exist_ok=True)
        for f in nd.glob("*.md"):
            f.unlink()
        for i in self.nodes:
            (nd / f"{i}.md").write_text(self.render_node(i), "utf-8")
        index = self.render_index()
        (self.root / "index.md").write_text(index, "utf-8")
        for f in ("map.md", "map.canvas", "outline.md"):
            (self.root / f).unlink(missing_ok=True)
        if self.human:
            (self.root / "map.md").write_text(self.render_map(), "utf-8")
            (self.root / "map.canvas").write_text(json.dumps(self.render_canvas(), indent=1), "utf-8")
            (self.root / "outline.md").write_text(self.render_outline(), "utf-8")
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
        anchored = {a["p"] for n in N.values() for a in n["anchors"]} | {pt["p"] for n in N.values() for pt in n["points"]}
        unanchored = [p for p in sorted(self.paras) if p not in anchored]
        lines = [
            f"nodes: {len(N)} ({', '.join(f'{k} {v}' for k, v in sorted(by.items()))}); points {sum(len(n['points']) for n in N.values())}",
            f"levels: apex at {self.level.get(self.apex)}; satellites {len(self.satellites)}",
            f"interface: {self.interface}",
            f"premises: {len(self.premises)} {self.premises}",
            f"source ¶ with no anchor: {unanchored}",
            f"strength: apex {self.strength[self.apex] * 100:.0f}; judgements defaulted: {len(self.defaulted)}",
            f"weakest link: {' -> '.join(self.weakest_link())}",
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
    if not p.errors:
        p.compute_strength()
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
