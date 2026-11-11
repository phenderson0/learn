# distill — design (draft v1)

`/learn:distill` turns a source (an essay, a book, your own learn lessons, later a codebase) into a **pyramid**: a layered structure of ideas where each layer is generated from the one below it by explicit, typed operations, and every idea traces back to the exact place in the source it came from.

Status: design only. Nothing here is built yet. v1 resolves the review notes on v0 (contradictions, the coverage test, the data model). Items deferred to M4 are collected in §12.

## 1. What it is, and what it isn't

**Not a summary.** A summary keeps the important parts and throws the rest away. You can't get the rest back.

**Not a knowledge graph.** A graph of concepts linked by "related to" records *that* things are connected, not *how*. You can't regenerate anything from it.

**It's compression.** A lossless image codec doesn't store less of the image. It stores a model that predicts most of it, plus the residual the model gets wrong. A pyramid does the same with ideas:

- **Higher nodes are generators.** A node sits above others because they derive it, generalize into it, or support it. The node says which, and how.
- **Bases carry the operation.** So a node can be re-run from its inputs, and §7 tests that.
- **Residuals are kept.** What can't be derived (a number, a defining example, a name) is stored as a `detail` node beneath the idea it serves.

**Lossless, precisely:** a pyramid is *lossless at weight W* when independent agents, reading only the pyramid, can regenerate every claim in the source of weight W or above (§7). The target is lossless at `supporting`. `illustrative` claims are lossy by design: an anecdote may fold into the idea it illustrates. So "lossless" always means lossless at a stated weight, never in general.

### Decisions so far

| Question | Decision |
|---|---|
| What does "up" mean? | Both derivation and abstraction. The basis type says which. |
| What must be preserved? | Lossless at `supporting`. Illustrative claims are best effort. |
| Who reads it? | Humans and agents. Each pyramid is built in one mode (§8). There's one store per pyramid, and the mode sets T2's style. |
| Author's structure or the true logic? | The author's, faithfully. Structure the author never wrote is allowed but always labelled (`origin`, §3), and gaps are flagged, never filled with content. |
| One pyramid or many? | One per source. Pyramids combine recursively through interfaces and mounts (§6). |
| Tree or DAG? | DAG. A node can feed several parents. |
| v0 test text | Mill, *On Liberty*, Chapter 2, with the closing summary removed from the builder's copy (§7). |

## 2. Terms

| Term | Meaning |
|---|---|
| **source** | The thing being distilled. Stored as a normalized, paragraph-numbered copy (§8). |
| **anchor** | A pointer into the source: a verbatim quote plus a paragraph number, or a `file:line`, or a note path. |
| **claim** | One atomic assertion the source makes: a single statement that can be true or false on its own. An example or case counts as one claim. Claims are extracted separately from the pyramid and used only to test it. |
| **node** | One unit in the pyramid. Kinds: `idea`, `detail`, `mount`. |
| **basis** | How a node is produced: a typed operation over a set of lower nodes. Always stored on the higher node. |
| **level** | Longest path from the node down to the bottom, following bases only. Computed, never set by hand. Lateral edges don't affect it. |
| **premise** | An `idea` with `origin: source` whose only bases are `illustration`, or that has none. These are the source's starting points. They are computed, not declared. |
| **apex** | The single top node. |
| **interface** | The apex plus the inputs of its bases. If that's fewer than 3 nodes, extend one level down until there are 3 or no inputs remain. |
| **mount** | A node in one pyramid that stands for a whole other pyramid, through its interface. |

## 3. Nodes

### Fields

| Field | Values | Meaning |
|---|---|---|
| `kind` | `idea` · `detail` · `mount` | What it is. |
| `origin` | `source` · `structural` · `gap` | Who made it. `source`: the author states it, and it has anchors. `structural`: a grouping the builder added to respect fan-in. `gap`: a placeholder marking a missing step (§4). |
| `voice` | `author` · `reported` · `opponent` | Whose view it is. `author`: Mill asserts it. `reported`: Mill reports someone's view without taking a side. `opponent`: a view Mill raises in order to answer it. Only `origin: source` nodes have a voice. |
| `bases` | list | How it's produced (§4). |
| `lateral` | list | Non-hierarchical relations (§4). |
| `flags` | list | Node-level flags (§4). |

**Faithfulness rule:** content is only ever attributed to the source through anchors on `origin: source` nodes. `structural` and `gap` nodes never have anchors, and every view shows their origin. The builder may add structure, but never words in the author's mouth.

### Tiers

| Tier | Content | Limit | Lives in |
|---|---|---|---|
| T0 | label | ≤ 6 words | parent's input list, index |
| T1 | the claim, stated plainly | 1 sentence, ≤ 30 words | parent's input list, index |
| T2 | explanation: what the node says and how its bases produce it | ≤ 150 words | node file |
| T3 | anchors (quote + ¶) and residual specifics | as needed | node file |

There is one T2 per node, and its style follows the pyramid's mode: written to teach in `human` mode, terse in `agent` mode (§8).

`gap` nodes: T1 states the step that would be needed, phrased as missing ("Needed but not stated: …"). They have no T3.

`mount` nodes: T1 is the child's apex T1. T2 lists the child's interface at T1. T3 is the child's manifest path and pinned version (§12).

## 4. Bases, lateral edges and flags

### Bases (upward, stored on the higher node)

A basis lists the lower nodes the node is built from, read conjunctively: `derivation of [a, b]` means a and b together. Every basis has a one-line `how`, the operation that turns the inputs into this node.

| Type | The inputs… |
|---|---|
| `derivation` | entail this node, taken together. |
| `generalization` | are instances or cases this node abstracts over. This is chunking, and it's the only type `structural` nodes may use. |
| `support` | are evidence or argument for this node without entailing it. |
| `illustration` | are `detail` nodes that exemplify this node. |

Details always attach through an `illustration` (or `support`) basis on the idea above them, never by a field on the detail itself.

### Lateral (no hierarchy, can cross levels)

| Type | Meaning |
|---|---|
| `objects` | States an objection to the target. Usually from a `voice: opponent` node. |
| `rebuts` | Answers an objection. |
| `qualifies` | Limits the target's scope: conditions, exceptions. Kept lateral, because a limit is not support. |
| `contrasts` | A deliberate opposite or alternative. |
| `same-as` | The same idea in another pyramid (§6). |

### Flags

Basis flags record a problem with an inference:

| Flag | Meaning |
|---|---|
| `weak` | The inputs don't get you there; the inference is a stretch. |
| `missing-step` | A step is needed that the source never states. The basis then includes a `gap` node as an input, and the flag goes on that basis. |
| `circular` | This basis closes a loop: one of its inputs depends on this node. |

Node flags record a problem with a node:

| Flag | Meaning |
|---|---|
| `unsupported` | The author asserts it as a conclusion but gives no basis. This is different from a premise, which the source openly takes as a starting point. The builder decides which, and the call is reviewed in §7. |
| `repeated` | The source states it more than once. The anchors are merged into one node. |

**Circular arguments:** a basis flagged `circular` is stored, but it's excluded from level computation and from the cycle check. So the circularity is recorded faithfully, and upward edges still form an acyclic graph.

## 5. Structural rules

1. **Fan-in ≤ 7.** No node has more than 7 inputs in total, across all of its bases. If more are needed, chunk them into `structural` intermediate nodes using `generalization`. Fan-out is unrestricted.
2. **Grounding.**
   - An `origin: source` node has at least one anchor.
   - A `structural` node has a basis whose inputs are all grounded.
   - A `gap` node is grounded by the flagged basis that uses it.
   - A `mount` is grounded by its child's coverage report.
3. **Anchors are verbatim** after normalization (§8), and a script checks them.
4. **One idea, one node.** Restatements are merged and flagged `repeated`.
5. **Acyclic upward edges,** not counting bases flagged `circular`.
6. **One apex.** If the source has several equal theses, the apex is a `structural` node that generalizes over them, so no thesis is promoted above another.
7. **Views show ≤ 7 nodes at once.** That's a node plus its inputs, never a whole level.

## 6. Recursion: interfaces and mounts

Pyramids are modules. Each exports an interface (§2) at T0–T1 and keeps the rest private.

- A parent includes a whole child pyramid as one `mount` node.
- Parent edges may target the child's interface nodes as `<child>:<id>`. Deeper references are allowed, but they are only pointers until an agent follows them.
- Combining A and B reads only the two interfaces, adds `same-as` links, and builds new levels above them. The cost depends on interface size, not pyramid size.
- `same-as` is lateral, so it doesn't compare levels across pyramids.

Versioning, pinning, combined-pyramid storage and testing are designed in M4 (§12).

## 7. Testing

The coverage test is run by agents that never saw the pyramid being built, and it checks two things: that content is recoverable and that the structure is correct.

### Independence rules

- The builder never sees the claim sets.
- The claim extractors use different prompts from the builder's extraction step, and run as fresh subagents with no build context.
- **Mill:** the builder works from `source/builder.md`, which has the chapter's closing summary of the four grounds removed. Extraction and judging use the full source.

### Claim sets

Two independent extractions are made of the full source, with different prompts: **set A** (`claims-a.jsonl`) and **set B** (`claims-b.jsonl`). Each claim gets an anchor and a weight:
- `core`: the argument depends on it.
- `supporting`: a step, condition, or piece of evidence.
- `illustrative`: an example or anecdote.

Set A is used for the repair loop. **Set B is held out** and only used for the final score, so repairs can't overfit to it. A judge also reconciles A and B: claims that appear in only one set are logged, which shows how stable the extraction is.

### Content test: regenerate, then judge

1. **Regenerator** (fresh agent, sees only the pyramid): starts at `index.md`, traverses with a node budget, and writes out every claim it can recover from the pyramid, in its own words. It never sees any claim set. It logs which nodes it opened.
2. **Judge** (a separate fresh agent): matches the regenerated claims against the claim set. It reports:
   - **recall** by weight: claims recovered out of claims in the set,
   - **spurious claims**: regenerated claims that aren't in the source (pyramid hallucinations, or a misread `voice`),
   - **voice errors**: an opponent's view regenerated as the author's.

### Structure test

1. **Re-run:** sample nodes and give a fresh agent only each node's inputs (T1) and the basis `how`. It writes the node's T1. A judge rates whether it matches the real T1. This tests whether bases are actually generative.
2. **Audit:** a judge with the source in front of it samples bases, flags, `voice` values and premise-vs-`unsupported` decisions, and marks each correct or incorrect.

### Mechanical checks (script)

- Quote anchors exist in the normalized source at the cited ¶.
- Non-quote anchors (paths, `file:line`) exist.
- Fan-in ≤ 7, acyclic upward edges, one apex, grounding.
- Size limits on T0, T1 and T2, and the index budget (§8).

### Report and v0 targets (provisional)

`coverage.md` holds recall by weight on set B, spurious claims, voice errors, re-run and audit accuracy, mechanical failures, and traversal cost (nodes opened, tokens read).

| Metric | Target |
|---|---|
| Recall, `core` (set B) | 100% |
| Recall, `supporting` (set B) | ≥ 95% |
| Recall, `illustrative` (set B) | ≥ 80% |
| Spurious claims and voice errors | 0 |
| Re-run match | ≥ 80% |
| Audit accuracy | ≥ 90% |

**Mill check:** the interface should recover Mill's four grounds, or a recognizable equivalent, even though the builder never saw the passage that lists them.

## 8. Storage

```
distill/<slug>/
  manifest.json      # see below
  source/
    source.md        # normalized, ¶-numbered full source
    builder.md       # what the builder sees (same as source.md unless redacted)
  index.md           # agent entry: apex, interface, and the top levels only (bounded)
  map.md             # human entry: apex + interface diagram (human mode only)
  nodes/<id>.md      # frontmatter + input list + T2 + T3
  claims-a.jsonl
  claims-b.jsonl     # held out
  coverage.md
```

**Index is hierarchical, not flat.** A flat list at T0+T1 costs about 45 tokens per node and grows with the source, which undercuts "pay only for depth". So:
- `index.md` holds the apex, the interface and the levels below them until it reaches about 1.5k tokens. It ends with a pointer saying where the listing stops. Its size doesn't depend on the size of the source.
- Every node file opens with its **input list**: its inputs at T0+T1 with their IDs, ≤ 7 × ~45 tokens. An agent goes deeper one node at a time, and each step costs a bounded amount.
- For grep-style lookup the script can also generate an optional flat `index-full.md`. Agents aren't told to read it.

**Human view:** `map.md` shows the apex and interface as one diagram. Every node file with inputs renders a small mermaid diagram of itself plus its inputs (≤ 7). There are no per-level diagrams.

**Mode** (`human` · `agent`) is set at build time and stored in the manifest. `agent` mode writes T2 tersely and skips `map.md` and the per-node diagrams. Use it for codebases, workflows and system-prompt material.

**Source normalization** (done by script):
- NFKC Unicode, straight quotes and apostrophes, collapsed whitespace, line-break hyphenation joined.
- Paragraphs are blank-line-separated blocks, numbered ¶1… in `source.md`.
- `manifest.source` holds the original locator (URL or path), the edition, and the sha256 of `source.md`.

**IDs** are readable slugs, unique within a pyramid. Wikilinks are written with the path, `[[<slug>/nodes/<id>|label]]`, so they stay unambiguous when several pyramids share one Obsidian vault.

**Location:** `<project>/distill/` by default. It's gitignored in this plugin repo. In your own learning project, commit it if you want it versioned.

### Example node

```markdown
---
id: silencing-assumes-infallibility
kind: idea
origin: source
voice: author
bases:
  - type: derivation
    from: [all-humans-fallible, silencing-prevents-correction]
    how: If anyone might be wrong, suppressing an opinion treats one's own judgement as unable to err.
  - type: illustration
    from: [socrates-condemned, jesus-condemned]
    how: Both were condemned by authorities certain they were right, and both judgements are now seen as errors.
lateral:
  - type: rebuts
    target: authorities-must-act-on-conviction
flags: [repeated]
---
# Silencing assumes infallibility

**T1:** To suppress an opinion as false is to assume one's own certainty is the same as absolute certainty.

## Inputs
- `all-humans-fallible`: All humans are fallible / Any person or age can hold false beliefs with full confidence.
- `silencing-prevents-correction`: Silencing blocks correction / A suppressed opinion can't be heard, so an error in the received view can't be exposed.
- `socrates-condemned` (detail): Socrates condemned / …
- `jesus-condemned` (detail): Jesus condemned / …

## T2
<explanation, ≤150 words>

## T3
- ¶3: "All silencing of discussion is an assumption of infallibility."
```

## 9. Invocation and build pipeline

`/learn:distill <source> [--mode human|agent] [--slug name]`

- **v0 inputs:** a local text or markdown file, or a URL fetched to text. PDF and epub come later, through the pdf skill or conversion.
- **Later:** a learn notes folder (M4) and a codebase path (§11).

Pipeline:

1. **Ingest:** normalize the source, number paragraphs, write `source/` and the manifest.
2. **Extract** candidate bottom nodes per section (parallel subagents), with anchors, `voice` and weight hints.
3. **Merge** restatements (`repeated`) and attach details through `illustration` bases.
4. **Build upward in rounds.** Group nodes by the *logic* of the argument, not by the author's section breaks. Write each parent with typed bases, flag gaps as they appear, and use `structural` nodes when fan-in would exceed 7. Stop at one apex. Rounds are a build convenience: levels are recomputed from the graph afterwards, since a parent's inputs may sit at different depths.
5. **Interface:** computed by the rule in §2.
6. **Render:** the input lists, `index.md`, and in human mode `map.md` and the diagrams.
7. **Test** (§7), using fresh agents.
8. **Repair** against set A until the targets pass, then score once on set B.

Annotations (your own notes on a node) go in `distill/<slug>/annotations/<id>.md`. They're never generated or overwritten, so they survive a rebuild.

## 10. How it connects to the rest of learn

- **teach:** teach a source from its pyramid. Its premises are the source's *starting points*, not unconditional truths. Many of Mill's are contested. Teach treats them as candidates: it checks each one with the learner and states it as "Mill assumes…" when it isn't safe to take at face value. Bases are the motivated steps.
- **review:** nodes can go into the review ledger, and node T1s make good short-answer keys. How ledger entries reference nodes across rebuilds is in §12.
- **Your own knowledge base:** the learn notes plus the ledger form a source (M4).

## 11. Milestones

1. **M1: hand-built pyramid.** The main session builds Mill Ch. 2 by hand from `builder.md`, following this spec exactly. Writing down where the spec was unclear is part of the output.
2. **M2: test tooling.**
   - Ingest and normalization script, plus the mechanical checks script.
   - Claim sets A and B.
   - The regenerator, judge, re-run and audit agents. All are fresh subagents with no M1 context.

   Run them on M1 and revise the format.
3. **M3: automate.** Turn §9 into a `distill` skill and pass the §7 targets on Mill with no hand edits.
4. **M4: recursion and integration.** Resolve §12, distill your learn notes, combine them with Mill through mounts, and measure the cost of combining.
5. **Later:** an agent-mode pyramid of a codebase. Anchors become `file:line`, and claims become behaviours and conventions.

## 12. Deferred to M4

- **Versioning:** use per-version folders (`distill/<slug>/v<n>/`). Mounts pin a version, and so do deep references. Each rebuild writes an `idmap.json` mapping old IDs to new.
- **Combined pyramids:**
  - Where they live (likely `distill/<a>+<b>/`).
  - What their "source" is: the child interfaces plus any new anchors.
  - How they're tested: only the new upper levels are tested. Children keep their own reports.
- **Review integration:** ledger entries store `ref: <slug>@v<n>:<id>`, and `idmap.json` migrates them after a rebuild.
- **Interface changes:** can a mounted interface change in a later version, and what happens to parents that pinned the old one?

## 13. Open questions

- **Detail granularity:** what makes a detail carry enough weight to keep, beyond its claim weight?
- **Premise vs `unsupported`:** is the builder's call reliable enough, or does it need a rule? M1 will show.
- **Judge leniency:** does the judge need a calibration set of known matches and non-matches?
- **Index budget:** is ~1.5k tokens right? M2 traversal-cost numbers decide.
