# distill — M1 findings (Mill, *On Liberty*, Ch. 2, built by hand)

Built 2026-11-10 by the main session from `source/builder.md` (¶42–45 redacted), following `docs/distill.md` v1. The pyramid lives in `distill/mill-liberty-2/` (gitignored). The authored input is `src/*.yaml`, one file per branch. `scripts/distill_build.py` checks it and renders `nodes/`, `index.md` and `map.md`.

## Numbers

| | |
|---|---|
| Source | 16.4k words, 53 ¶, about 24k tokens |
| Nodes | 83: 60 idea, 23 detail. 7 have `voice: opponent`. |
| Shape | Apex at level 6. 17 satellites (joined only by lateral edges). |
| Paragraph coverage | Every content ¶ has at least one anchor. The only unanchored ¶ are headings, the redacted ¶42–45 and "FOOTNOTES:". |
| Authored content | About 16k tokens: T0+T1 3.8k, T2 5.4k, anchors 5.5k, `how` lines 1.3k |
| Rendered node files | About 30k tokens, more than the source |
| `index.md` | About 1.6k tokens. Covers depth 0–2 (21 nodes) plus the satellite list. |
| Build cost | About 28k tokens to read the source, plus about 25k tokens of output |
| Mechanical checks | They caught 4 real errors, including a quote I had silently "corrected" (Gutenberg's text reads "than when in or opposition to it"). That is exactly the class of error anchors exist to catch. |

**The compression isn't in total size, it's in what you have to read.** The full pyramid is bigger than the source. But the whole argument down to depth 2 costs 1.6k tokens, and each step deeper costs about 360 tokens per node. Measured against the alternative of reading 24k tokens, that's the win the design aims for.

## Mill check (not blind)

This check isn't blind: the builder had read ¶42–45 and knows Mill from training. So it shows the pyramid agrees with a known answer, not that the method recovers structure on its own.

| Mill's recap | Pyramid |
|---|---|
| 1. The silenced opinion may be true | `opinion-may-be-true` (interface) |
| 2. A false opinion may contain part of the truth | `partial-truths` (interface) |
| 3. Truth uncontested is held as prejudice | `grounds-unknown`, **one level below** the interface |
| 4. Its meaning is lost | `meaning-lost`, **one level below** the interface |

The pyramid follows the chapter body. ¶23 announces grounds 3 and 4 as one "second division", so they sit under `true-opinion-dies`. Mill's recap splits them. Both readings are faithful to the text, and the choice between them is a judgement call the spec gives no rule for.

The interface also carries three strands the recap leaves out:
- `numbers-dont-justify`
- `suppression-cramps-minds` (¶20–22, a substantial argument about what intolerance does to minds)
- `welcome-dissenters`

**A faithful map of the body holds more than the author's own summary.** That supports "lossless ≠ summary".

## Spec problems found

1. **Applications and corollaries have no edge type.** Three nodes apply the thesis rather than support it or limit it:
   - `manner-not-for-law` (¶46),
   - `tyrannicide-limit` (fn 6),
   - `welcome-dissenters` (¶35).

   They were forced into `qualifies` or `support`, and `welcome-dissenters` as support of the apex is a stretch. Proposal: add a lateral type `applies` (the node applies the target to a new case).
2. **Satellites need to be in the spec.** 20% of nodes (17 of 83) are reachable only through lateral edges: opponent views, some rebuttals, scope notes, the ¶46 section. The script now defines satellites (nodes outside the apex's subtree joined by lateral edges) and treats an unjoined node as an orphan error. The spec should say this.
3. **Rebuttals are placed inconsistently.** Some rebuttals are inputs to the node they defend: `presume-vs-assume` and `usefulness-is-opinion` support `silencing-assumes-infallibility`. Others hang loose as satellites (`persecution-ungrateful`). Proposed rule: a rebuttal that defends a node is a `support` input of that node, and only rebuttals with no node to defend are satellites.
4. **The computed premise definition is useless.** 40 of 60 ideas qualify (33 with author voice), because every leaf idea counts. A leaf isn't a starting point. Proposal: make `premise: true` an explicit field set by the builder and checked by the audit.
5. **Gap flags were almost unused.** The builder (me) flagged nothing as `weak` or `unsupported`, even though there are candidates. `errors-corrigible` rests on the hedged assumption that rational opinion does prevail, and I put that in a residual note instead of flagging it. A builder focused on mapping doesn't critique. Proposal: a separate critique pass after building, whose only job is flagging.
6. **Grouping is a judgement with no rule** (see the Mill check). The re-run and audit tests in §7 matter more than expected.
7. **Rendered overhead.** Input lists repeat each child's T1 in every parent; in a DAG some children appear several times. Add the per-node "used by" lists, mermaid diagrams and wikilinks, and the files end up 1.9× the authored content. Agent mode should drop the diagrams and wikilinks.
8. **Anchors are the largest authored part (5.5k tokens).** Proposal: a locator quote of 15 words or fewer is enough for the check. Longer quotes only where the wording itself carries weight.
9. **¶ anchors are coarse.** Mill averages about 310 words per paragraph, so the quote does the real locating. Sentence-level positions would make anchors cheaper.
10. **The index budget leaked.** The satellite list wasn't counted, so `index.md` came out about 1.6k tokens against a budget of 1.5k. Fixable in the script.
11. **The authoring format should be the canonical store.** Writing one YAML file per branch was much easier than writing 83 node files, and rendering from it guarantees consistent input lists. Proposal: `src/*.yaml` becomes canonical and `nodes/` is generated. Update §8.
12. **`voice` worked well.** The 7 opponent views are clearly separated from Mill's own, in both the index and the node files.

## Toward cheaper builds for books

The builder's one hard cost is reading the source once. Everything above that can be made cheaper:

- **Build section by section** with a running list of the nodes made so far (T0/T1 only, a few hundred tokens), not the full text. Each section is read once.
- **Build upper levels from T1s only.** Grouping and writing parents never needs the source text, only the lower nodes' claims. For Mill the whole list of T1s is about 3.8k tokens, against 24k for the source.
- **Mix models.** Use a cheap model for section extraction and anchors, where the mechanical checks catch mistakes. Save the strong model for grouping and bases, where the judgement is.

Estimate for a 100k-word book: one read of about 150k tokens, split across section subagents, plus upper-level building over T1s (about 25k tokens). It's linear in the book's length, with no full-book context needed anywhere.

## Next (M2)

1. Write the spec changes for findings 1–4, 8 and 11 into `docs/distill.md`.
2. Fix the index budget (finding 10). Add an agent-mode render.
3. Build the §7 test agents: two claim extractors, the regenerator and judge, and the re-run and audit agents. Run them on this pyramid.
4. Choose a second source unlikely to be in training data, so the structure-recovery check is real.
