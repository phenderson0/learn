"""confidence — learner confidence per distill node (docs/distill.md §4b).

A library used by review.py. The pyramid says what depends on what; the
learner's ledger holds the evidence. Nothing here writes to the pyramid.

Ledger additions (in <project>/.claude/learn-ledger.json):

  "pyramids": {"<slug>": "<path to distill/<slug>, relative to the project>"},
  "nodes": {
    "<slug>#<node-id>": {
      "records": [{"t": "YYYY-MM-DD", "level": "recall|explain|apply",
                   "result": "pass|partial|fail", "self": "sure|unsure|guess"?, "q": "..."?}],
      "agree": {"t": ..., "stance": "agree|partly|disagree", "reason": "..."}?
    }
  }
"""
import os
import sys
from datetime import date, timedelta
from pathlib import Path

LEVELS = ["recall", "explain", "apply"]
RESULT = {"pass": 1.0, "partial": 0.5, "fail": 0.0}
SELF = {"sure": 0.9, "unsure": 0.6, "guess": 0.3}
STANCES = {"agree", "partly", "disagree"}
KNOWN = 0.7          # a level is known at or above this
INFER = 0.5          # downward credit: inputs get INFER x explain(parent)
BASE_DAYS, MAX_DAYS = 7, 180
PREREQ_LATERAL = {"objects", "rebuts", "qualifies", "applies"}  # the target must be known first
CALIBRATION_WINDOW = 20


def today() -> date:
    """Today, or LEARN_TODAY (YYYY-MM-DD) for testing."""
    t = os.environ.get("LEARN_TODAY")
    return date.fromisoformat(t) if t else date.today()


def load_pyramid(path: Path):
    """Build a checked, analysed pyramid with strength (distill_build.Pyramid)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from distill_build import Pyramid  # needs pyyaml; imported lazily so concept review works without it
    p = Pyramid(path)
    p.check()
    if not p.errors:
        p.analyse()
    if not p.errors:
        p.compute_strength()
    if p.errors:
        sys.exit(f"pyramid {path} has errors; run distill_build.py on it:\n  " + "\n  ".join(p.errors[:5]))
    return p


def migrate_renames(ledger: dict, slug: str, renames: dict) -> int:
    """Move evidence from renamed node ids (manifest "renames": {old: new}) to their new keys."""
    nodes, moved = ledger.setdefault("nodes", {}), 0
    for old, new in renames.items():
        k_old, k_new = f"{slug}#{old}", f"{slug}#{new}"
        if k_old in nodes:
            dst = nodes.setdefault(k_new, {"records": []})
            dst["records"] = sorted(dst["records"] + nodes[k_old]["records"], key=lambda r: r["t"])
            if "agree" in nodes[k_old] and "agree" not in dst:
                dst["agree"] = nodes[k_old]["agree"]
            del nodes[k_old]
            moved += 1
    return moved


def level_records(records: list, level: str) -> list:
    """Records that count as evidence at `level`. Levels are cumulative: a pass at a higher level counts below."""
    k = LEVELS.index(level)
    return [r for r in records
            if r["level"] == level or (LEVELS.index(r["level"]) > k and r["result"] == "pass")]


def direct(records: list, level: str, now: date):
    """(confidence, half-life days, last record) from the learner's own answers, or None with no evidence.

    confidence = latest result x 2^(-age / h), h = 7 x 2^streak days (cap 180),
    streak = passes in a row at the end. Matches the review ledger's cooldowns.
    """
    rs = sorted(level_records(records, level), key=lambda r: r["t"])  # stable: same-day order kept
    if not rs:
        return None
    streak = 0
    for r in reversed(rs):
        if r["result"] != "pass":
            break
        streak += 1
    h = min(BASE_DAYS * 2 ** streak, MAX_DAYS)
    last = rs[-1]
    age = (now - date.fromisoformat(last["t"])).days
    return RESULT[last["result"]] * 2 ** (-max(age, 0) / h), h, last


class Learner:
    """Confidence for every teachable node of one pyramid, for one learner."""

    def __init__(self, pyramid, ledger: dict, now: date = None):
        self.p, self.now = pyramid, now or today()
        self.slug = pyramid.slug
        self.N = pyramid.nodes
        self.ev = {k.split("#", 1)[1]: v for k, v in ledger.get("nodes", {}).items()
                   if k.split("#", 1)[0] == self.slug}
        self.teachable = [i for i, n in self.N.items()
                          if n.get("origin", "source") != "gap" and n.get("kind") != "mount"]
        self.compute()

    # ----- graph -----
    def core_inputs(self, i):
        """Inputs through derivation, support or generalization bases (not illustration, not circular)."""
        out = []
        for b in self.N[i]["bases"]:
            if b["type"] == "illustration" or "circular" in b.get("flags", []):
                continue
            out += [x for x in b["from"] if x in self.N and x in self.teachable]
        return list(dict.fromkeys(out))

    def prereqs(self, i):
        """What must be known before i: core inputs, plus what an objection or rebuttal is aimed at."""
        lat = [e["target"] for e in self.N[i]["lateral"]
               if e.get("type") in PREREQ_LATERAL and e["target"] in self.N and e["target"] in self.teachable]
        return list(dict.fromkeys(self.core_inputs(i) + lat))

    def importance(self, i):
        if not hasattr(self, "_trace"):
            self._trace = {s.split(" (")[0] for s in self.p.weakest_link()}
        return (1 + (i in self.p.interface) + (i in self._trace)
                + 0.25 * len(set(self.p.parents.get(i, []))))

    # ----- confidence -----
    def records(self, i):
        return self.ev.get(i, {}).get("records", [])

    def compute(self):
        now = self.now
        self.d = {L: {} for L in LEVELS}      # direct (confidence, h, last) or None
        for i in self.teachable:
            for L in LEVELS:
                self.d[L][i] = direct(self.records(i), L, now)
        # recall: direct, else inferred from parents explained
        self.inferred = {}
        for i in self.teachable:
            de = self.d["explain"][i]
            if de and de[0] > 0:
                for x in self.core_inputs(i):
                    if self.d["recall"][x] is None:
                        self.inferred[x] = max(self.inferred.get(x, 0), INFER * de[0])
        self.c = {L: {} for L in LEVELS}
        self.unverified = set()
        for i in self.teachable:
            dr = self.d["recall"][i]
            self.c["recall"][i] = dr[0] if dr else self.inferred.get(i)
        # explain: capped by inputs' recall
        for i in self.teachable:
            de = self.d["explain"][i]
            if de is None:
                self.c["explain"][i] = None
                continue
            caps = []
            for x in self.core_inputs(i):
                r = self.c["recall"][x]
                if r is None:
                    self.unverified.add(i)
                else:
                    caps.append(r)
            self.c["explain"][i] = min([de[0]] + caps)
        # apply: capped by recall of the node itself
        for i in self.teachable:
            da = self.d["apply"][i]
            r = self.c["recall"][i]
            self.c["apply"][i] = None if da is None else (min(da[0], r) if r is not None else da[0])

    def known(self, i, L):
        c = self.c[L].get(i)
        return c is not None and c >= KNOWN

    def grasp(self, i):
        g = None
        for L in LEVELS:
            if self.known(i, L):
                g = L
        return g

    def due(self, i):
        """Due when recall confidence has halved: last recall-level evidence + its half-life. None if untested."""
        dr = self.d["recall"][i]
        if not dr:
            return None
        return date.fromisoformat(dr[2]["t"]) + timedelta(days=dr[1])

    def confident_error(self, i):
        rs = sorted(self.records(i), key=lambda r: r["t"])
        return bool(rs) and rs[-1].get("self") == "sure" and rs[-1]["result"] == "fail"

    def wants_agreement(self, i):
        """Contested nodes, once explained (leaves: once recalled), with no stance recorded yet."""
        n = self.N[i]
        if n.get("acceptability") != "contested" or "agree" in self.ev.get(i, {}):
            return False
        return self.known(i, "explain") or (not self.core_inputs(i) and self.known(i, "recall"))

    # ----- targeting -----
    def frontier(self):
        """[(priority, node, target level, confidence at target, notes)] — what the learner is ready for next."""
        out = []
        for i in self.teachable:
            pre = self.prereqs(i)
            ready = all(self.known(x, "recall") for x in pre)
            notes = []
            if self.confident_error(i):
                notes.append("confident error")
            if i in self.unverified:
                notes.append("explain unverified: an input was never tested")
            if self.wants_agreement(i):
                notes.append("ask agreement")
            if not self.known(i, "recall"):
                if not ready:
                    continue
                target = "recall"
            elif self.core_inputs(i) and not self.known(i, "explain"):
                if not ready:
                    continue
                target = "explain"
            elif self.N[i].get("kind") == "idea" and not self.known(i, "apply"):
                target = "apply"
            elif "ask agreement" in notes:
                target = "agree"
            else:
                continue
            c = self.c[target].get(i) if target in LEVELS else 1.0
            pr = self.importance(i) * (1 - (c or 0))
            if target == "apply":
                pr *= 0.5        # applying is worth less than first understanding
            if "confident error" in notes:
                pr += 10         # re-teach first (hypercorrection)
            if target == "agree":
                pr = max(pr, 0.5)
            out.append((pr, i, target, c, notes))
        return sorted(out, key=lambda x: (-x[0], x[1]))

    def due_nodes(self):
        now = self.now
        out = []
        for i in self.teachable:
            d = self.due(i)
            if d and d <= now:
                c = self.c["recall"][i] or 0
                out.append((self.importance(i) * (1 - c) + 10 * self.confident_error(i), i, d))
        return sorted(out, key=lambda x: (-x[0], x[1]))


def calibration(ledger: dict, window: int = CALIBRATION_WINDOW):
    """(bias, n) over the last `window` self-rated answers across all pyramids. bias = mean(self - result)."""
    rs = [r for v in ledger.get("nodes", {}).values() for r in v["records"] if r.get("self") in SELF]
    rs = sorted(rs, key=lambda r: r["t"])[-window:]
    if not rs:
        return None, 0
    return sum(SELF[r["self"]] - RESULT[r["result"]] for r in rs) / len(rs), len(rs)
