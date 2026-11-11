# Plan: where things stand and what's next

Written 2026-11-10 to pull together two parallel work sessions and several research threads. This is the entry point. The detail lives in the docs it links to.

**Current mode: design only.** No new code or features until the open design questions below are worked through.

## The project in one paragraph

The repo is a Claude Code plugin with two halves:
- **distill** turns a source (an essay, a book, later a codebase) into a *pyramid*: a DAG of idea nodes anchored to the source and tested by independent agents.
- **learn** (teach, review, visualize, md-log) teaches it to you.

The long-range aim is the closest achievable structured representation of a source's *essence*: verifiable, measurable, and useful above all for learning. The philosophy is in `docs/distill-essence.md`.

## Docs map

| Doc | What it holds |
|---|---|
| `docs/distill.md` | The spec: nodes, bases, strength (§4a), learner confidence (§4b), tests (§7), storage (§8), milestones (§11) |
| `docs/distill-m1.md`, `docs/distill-m2.md` | Results: the hand-built Mill pyramid, then test tooling and repair rounds |
| `docs/distill-essence.md` | What "essence" means, and the user's positions |
| `docs/distill-research.md` | Merged research shortlist from four scouts, plus Q&A decisions |
| `docs/ROADMAP.md` | Long-range ideas and TODOs |
| `README.md` | User-facing overview |

## What's done

**distill (spec v2, M1 and M2):**
- A hand-built pyramid of Mill's *On Liberty* Ch. 2: 95 nodes plus 92 atomic points.
- `distill_build.py` with strength scoring and the weakest-link trace, plus Canvas, outline and budgeted-index views.
- Test agents (extractor, regenerator, judge, auditor) and `distill_score.py`.
- A critique pass, done by a separate agent.
- **Held-out result (set B):** 100% core, 92% supporting (target 95%), 97% illustrative.
- **Apex strength:** 77.

**learn integration (v0.4.0):**
- Learner confidence per node: spec §4b and `scripts/confidence.py`.
  - three levels: recall, explain, apply;
  - evidence that fades over time;
  - caps from a node's inputs;
  - a learning frontier;
  - calibration of self-ratings;
  - agreement on contested nodes.
- `review.py` node commands.
- The teach skill can teach from a pyramid, and review quizzes pyramid nodes.

**Research and design:**
- The essence philosophy.
- Four research reports, merged.
- Decisions so far: anchors as pointers, a memory baseline, a size ratio, an extractor panel.

## Next steps

### Now: design (no code)
1. **Done:** Q&A on picks 1–6. Decisions are in `docs/distill-research.md`.
2. **Pin down two decisions from picks 4–5:**
   - the generativity test's holdout sets, and how the upward and downward directions are scored;
   - a loose structure for the `purpose` free text.
3. **Q&A on the bigger design threads** (`distill-research.md`, "Contradictions with the current spec"):
   - form as part of the essence;
   - legitimate loops;
   - one pyramid vs. a declared family;
   - a minimal-core schema;
   - fan-in 7 vs. 4.
4. **Teach sessions on core concepts:**
   - MDL and Kolmogorov complexity;
   - rate-distortion;
   - the information bottleneck;
   - knowledge space theory;
   - GEB's isomorphism and levels.

### Next: implementation, once design settles
Rough order: cheapest and most foundational first.
1. **Memory baseline on Mill:** title-only, scrambled pyramid, canary claims. Report the lift.
2. **Anchors as pointers, plus an automatic size ratio** in `distill_build.py`.
3. **Extractor panel:**
   - vote counts next to the labels;
   - an effort setting for how many extractors to run;
   - Krippendorff's alpha on weights;
   - confidence intervals on recall.
4. **Finish M2 leftovers:**
   - B195 and A104;
   - split two-clause points (finding 8);
   - a footnote voice rule (finding 12);
   - index ordering by strength or centrality (finding 10).
5. **Confidence (§4b):** use it on a real lesson and tune the placeholder constants.
6. **M3:** automate the build as a `distill` skill and pass the §7 targets with no hand edits.
7. **A pilot on a source the model hasn't seen** (post-cutoff or your own material), before GEB.
8. **Generativity test (pick 4)** as a standard §7 test:
   - several holdout sets;
   - an upward direction (base claims → apex) and a downward one (apex → base claims and premises).
9. **A `purpose` field (pick 5):** loosely structured free text in the manifest, set by the user.
10. **Weaker-reader baseline (pick 6):** a small or legacy model with and without the pyramid. The lift measures how effective the pyramid is.

### Later
- M4: recursion, mounts, versioning (spec §12).
- Codebase pyramids ("help me understand"). Live distillation during a session.
- Project-based assessment in learn.
- GEB, once form, loops and purpose have a design.
- **Long horizon** (`docs/ROADMAP.md`):
  - an objective verification figure (log-prob/MDL metrics, meta-analysis);
  - combined multi-purpose pyramids.

### Project questions
- **One coherent repo:** a staged plan to merge distill and learn.
- **Fork or own project:** upstream has no license, so ask the author before reusing upstream code elsewhere. Details in `docs/ROADMAP.md`.
