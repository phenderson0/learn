# distill — M2 first test run (Mill, Ch. 2, the M1 pyramid)

Run 2026-11-10 on the unrepaired M1 pyramid, as fresh general-purpose subagents built from `agents/distill-*.md`. Results files are in `distill/mill-liberty-2/` (gitignored): `claims-a/b.jsonl`, `regen-1.jsonl`, `judge-a-1.jsonl`, `rerun-*.jsonl`, `audit-1.jsonl`, `coverage.md`.

Set B was held out through repair round 1 and judged once, after repair round 2. See **Repair rounds** below.

## Results

| Test | Result | Target | |
|---|---|---|---|
| Recall, core (set A) | 88% (64 claims) | 100% | ✗ |
| Recall, supporting (set A) | 55% (148) | 95% | ✗ |
| Recall, illustrative (set A) | 70% (28) | 80% | ✗ |
| Spurious claims | 1 | 0 | ✗ |
| Voice errors | 1 | 0 | ✗ |
| Re-run match | 85% (11 of 13, 2 partial) | 80% | ✓ |
| Audit accuracy | 81% (96 of 119 checks) | 90% | ✗ |
| Traversal | 77 of 83 nodes opened, 125 claims regenerated | | |

Recovered counts as 1 and partial as 0.5. Verdicts on set A: 140 recovered, 35 partial, 64 lost, 1 voice error.

## What it means

1. **The structure is mostly right; the leaves are too coarse.** The re-run test passed, so bases do regenerate their nodes. But 83 nodes can't carry 148 supporting claims: most lost claims are sub-points folded into a node's T2 or left out entirely. Two examples are the ¶39 detail on the New Testament presupposing an earlier morality, and the ¶20 oath-rule argument. A quote-match check puts at most about 13 of the 64 losses on traversal; the rest are content.
2. **"Lossless at `supporting`" costs a much bigger pyramid.** Set A has 240 claims for 16k words. Hitting 95% of supporting claims probably means about 150–200 nodes, or much richer T1s. This is the central size-versus-fidelity tradeoff, and the spec has to choose (see Decisions).
3. **Builders drop hedges.** Four faithfulness failures came from qualifiers being stripped: Mill's "too often", "most of those who receive it" and "almost all" became universal laws. The 30-word T1 limit pushes builders this way. A hedge is content, so this is loss.
4. **Builders don't flag.** 12 of 17 audited nodes needed a flag nobody added (`missing-step`, `weak`, `circular`, `unsupported`). This confirms M1 finding 5, so the separate critique pass is required, not optional. The audit also found a real circularity: `infallibility-defined` builds the conclusion into an input of `silencing-assumes-infallibility`.
5. **Agents stop going deeper well before their budget.** The regenerator opened `open-challenge-only-warrant` but none of its six inputs, even with budget to spare. That subtree is levels 4–6, the deepest in the pyramid. Deep branches are the most fragile under agent traversal.
6. **Nodes carry their own residual.** Both re-run partials were content on the node itself (from its own anchors), not something the inputs failed to produce. The spec should separate the generated part of a node from its residual, so the re-run test scores only the generated part.
7. **Claim weights are unstable.** The two extractors gave core counts of 64 and 41. Recall targets are set per weight, so the scores depend on which extractor ran. The judge's A–B reconciliation (§7) is needed before targets can be trusted.

## Cost

Subagent tokens for the whole run were about 460k:

| Run | Tokens |
|---|---|
| Two extractors | ~160k |
| Regenerator | ~75k |
| Re-run and its judge | ~70k |
| Audit | ~87k |
| Judge | ~66k |

Extraction and judging each re-read the source. A routine pipeline would cache claim sets per source and only re-run the regenerator and judge after repairs.

## Decisions (2026-11-10)

- **Fidelity:** keep "lossless at `supporting`" and accept the larger pyramid.
- **Traversal:** two regenerator runs. A forced full traversal measures content loss. A budgeted run measures how well agents navigate.
- **Node values:** each node gets two numbers.
  - **Argument strength:** design under discussion; see the proposal in chat, to be folded into the spec once agreed. This replaces a separate hedge field.
  - **Learner confidence:** **TODO**, deliberately not designed yet. It ties into the teach skill so the teacher can target nodes precisely. Revisit once strength scoring and the M2 repairs are settled.

## Repair rounds

**Round 1.** Fixes for the losses on set A:
- Added a `points` field: atomic sub-claims `{p, c}` (claim, anchor) on a node, so sub-points stop disappearing into T2. The pyramid went from 83 to 95 nodes, plus 92 points.
- Hedges stay in the claim (T1 may run to 35 words when it carries them).
- A critique pass by a separate agent set validity, acceptability and flags. Results: 4 sound, 24 plausible and 5 weak bases; 11 uncontested, 41 reasonable and 17 contested nodes; 18 flags; 13 hedges, all applied. It confirmed the circular basis in `silencing-assumes-infallibility`.
- Premises are now declared explicitly, and satellites are attached with lateral edges.

**Round 2.** Removed builder text that the judge marked spurious (my own T2 wording, R15 and R20), and filled the remaining set A losses.

| Run | Core | Supporting | Illustrative | Lost | Spurious |
|---|---|---|---|---|---|
| Set A, before repair | 88% | 55% | 70% | 64 | 1 |
| Set A, round 1, full traversal | 97% | 93% | 88% ✓ | 1 | 2 |
| Set A, round 1, budget of 30 nodes | 59% | 32% | 14% | 140 | 0 |
| Set A, round 2, full traversal | 97% | 95% (just under) | 86% ✓ | 2 | 0 |
| **Set B (held out), round 2, full traversal** | **100% ✓** | **92%** | **97% ✓** | 2 | 1* |

\* The one spurious claim, R280, came from a builder error; see finding 9.

Run against held-out set B, round 2 reaches 100% core and 92% supporting. That is the honest number: set A has now been used for repairs, so its scores are inflated. Set B's two lost claims:
- B187 is the four-grounds recap in ¶42. That paragraph was redacted from the builder, so this loss is expected.
- B195: calls for restraint in invective are aimed only at the losing side. Set A lost the same claim (A225), so it is a real gap.

Set A also lost A104: we may harm ourselves by our treatment of dissenters as much as ever.

**Strength.** The apex scores 77. The weakest-link trace runs silencing-illegitimate (77) → numbers-dont-justify (38) → harm-not-private (50, contested).

## Further findings (repairs)

8. **Partials are now the main loss.** Most of what is left is a dropped second clause: the "why", a second limb, or a consequence (A39, A67, A109, A172). A point that holds two clauses tends to lose one when regenerated. The fix is to split points into atomic ones, or have the judge report missing clauses.
9. **Builder contamination from outside the source.** Ingest used the wrong end line, which cut footnote 10 mid-sentence. The builder (me) had read the full text elsewhere and wrote points from it, so the judge correctly marked them spurious. Fixed by re-ingesting to line 2462: only ¶53 grew and the anchors still pass. Rule: the builder only reads `builder.md`, and ingest checks that the last paragraph ends a sentence.
10. **A budgeted agent finds the top, not the depth.** With 30 nodes it gets 59% of core claims and almost no illustrative ones. A bounded traversal answers "what is the argument", not "what does it say". This is expected. It suggests an ordering for the index (strength or centrality), so a budget is spent on the nodes that matter most.
11. **Still bigger than the source.** The authored YAML is about 17.5k words, against 16.7k words of source; the rendered node files are about 39k tokens, against 24k. The spec's fidelity target makes this structure larger than its source, not smaller. Compression has to come from the *views* (index, outline, budgeted reads), not from storage.
12. **Voice labels on footnotes are ambiguous.** Facts that Mill reports in his own footnotes were tagged `reported` by the extractor and `author` by the pyramid. The spec needs a rule for footnotes.
