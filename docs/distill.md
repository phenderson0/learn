# distill — design (draft v2)

`/learn:distill` turns a source (an essay, a book, your own learn lessons, later a codebase) into a **pyramid**: a layered structure of ideas where each layer is generated from the one below it by explicit, typed operations, and every idea traces back to the exact place in the source it came from.

Status: M1 is done (a hand-built Mill pyramid, findings in `docs/distill-m1.md`). M2 is in progress. v2 folds in the M1 findings: an `applies` edge, satellites, explicit premises, a rebuttal placement rule, locator quotes, YAML as the canonical store, a critique pass, and hierarchical views. Items deferred to M4 are collected in §12.

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
| **premise** | A starting point the source takes as given. **Declared** with `premise: true` by the builder, only on author-voiced source ideas, and checked by the audit (§7). M1 showed the computed version (any leaf idea) marks most of the pyramid. |
| **satellite** | A node outside the apex's subtree that is joined to it only by lateral edges: opponent views, rebuttals with no node to defend, applications, scope notes. About 25% of Mill's nodes. A node joined to nothing is an orphan, which is an error. |
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
| `acceptability` | `uncontested` · `reasonable` · `contested` | Leaves only (premises, details, and ideas with no derivation, support or generalization basis): how acceptable it is as a starting point. Set by the critique pass (§9), with evidence. Feeds strength (§4a). |
| `points` | list of `{p, c}` | Atomic sub-claims the node carries but doesn't argue for: one clause each, ≤ 35 words, with the ¶ it comes from. They hold the supporting content that would otherwise vanish into T2 (M2 finding 1). See the atomic-points rule below. |
| `strength` | 0–100 | **Computed, never written by hand.** How well the source supports this claim on its own terms (§4a). |
| `confidence` | per learner | **Not stored in the pyramid.** The learner's grasp of this node lives in the learner's ledger, keyed by node id (§4b). |

**Hedges stay in the claim.** A qualifier in the source ("too often", "almost all", "I believe", "in most cases") is content: it sets the claim's scope. T1 must keep it, and T1 may run to 35 words to fit it. Strength is a separate number and never replaces the words. A claim can be strongly argued *and* hedged.

**Points are atomic.** A point states one clause. When the source joins a claim to its reason, a second limb, or its consequence ("X, because Y"; "not only X but Y"; "X, so that Z"), split it into separate points, or make the reason a basis if it argues for the node. In M2 most of the remaining loss was half-recovered compound points: a regenerator keeps the first clause and drops the "why" (M2 finding 8). The build check warns on points that look compound; the builder splits them, or leaves them if the clauses can't stand alone.

**Faithfulness rule:** content is only ever attributed to the source through anchors on `origin: source` nodes. `structural` and `gap` nodes never have anchors, and every view shows their origin. The builder may add structure, but never words in the author's mouth.

### Tiers

| Tier | Content | Limit | Lives in |
|---|---|---|---|
| T0 | label | ≤ 6 words | parent's input list, index |
| T1 | the claim, stated plainly, hedges kept | 1 sentence, ≤ 30 words (35 with qualifiers) | parent's input list, index |
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

**Rebuttals:** a rebuttal that defends a node in the pyramid is a `support` input of that node, plus a `rebuts` edge to the objection. Only a rebuttal with no node to defend is a satellite.

### Lateral (no hierarchy, can cross levels)

| Type | Meaning |
|---|---|
| `objects` | States an objection to the target. Usually from a `voice: opponent` node. |
| `rebuts` | Answers an objection. |
| `qualifies` | Limits the target's scope: conditions, exceptions. Kept lateral, because a limit is not support. |
| `applies` | Applies the target to a new case: a corollary or practical consequence, such as Mill's ¶46 on the manner of discussion. Not support, since the target doesn't depend on it. |
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

**Objections:** an opponent node has an `objects` edge to the node it attacks, and its rebuttal has a `rebuts` edge to the objection. Both are needed to compute strength.

## 4a. Strength

Strength is *how well the source supports a claim on its own terms*, not whether the claim is true. It is built so that agents only make small, checkable, local judgements, and arithmetic does the rest.

**Local judgements** are made by the critique pass, each on a 3-level scale with a quoted reason. Three levels keep judgements repeatable; agreement between two critics is measured in §7.

| Judged on | Field | Levels → value |
|---|---|---|
| each basis | `validity`: does this inference hold? | `sound` 1.0 · `plausible` 0.75 · `weak` 0.4 |
| each leaf | `acceptability` (§3) | `uncontested` 0.95 · `reasonable` 0.75 · `contested` 0.5 |

The flags imply a ceiling: `weak` and `missing-step` cap validity at `plausible`. A `circular` basis contributes nothing.

**Propagation** is done by script, bottom up. With *s* for input strengths and *v* for validity:

| Basis | Value |
|---|---|
| `derivation` | v · min(s): a chain is only as strong as its weakest link |
| `support` | v · (1 − ∏(1 − sᵢ)): independent supports accumulate |
| `generalization` | v · mean(s) · min(1, 0.5 + 0.1·n) for n instances: more cases help, with a cap |
| `illustration` | no basis value. Adds a bonus of +0.05 per example (max 0.1) of the remaining gap: s + (1 − s)·bonus |

- **A node** combines its basis values the same way supports combine: 1 − ∏(1 − bᵢ). It then gets the illustration bonus. A leaf's strength is its acceptability.
- **Attack:** an objection with strength *a* lowers its target to s · (1 − 0.5 · a · (1 − r)), where *r* is the strongest rebuttal's strength. So a well-answered objection costs almost nothing, and an unanswered one costs up to half.
- Strength is shown as 0–100.

**What it gives:**
- the apex strength, the whole argument's strength,
- a **weakest-link trace**: the path of minimum contribution from the apex down, which shows what the argument most depends on,
- a list of the bases that cost the most strength.

The constants are v0 placeholders. This is a simplified form of the gradual semantics used for bipolar argumentation frameworks, such as DF-QuAD. Calibrating against that literature is a research item in `docs/ROADMAP.md`.

## 4b. Learner confidence

Strength is about the *argument*, and it is the same for every reader. Confidence is about *a learner*, and it differs for each one. So confidence never lives in the pyramid's files. It lives in the learner's ledger (`<project>/.claude/learn-ledger.json`) under `nodes`, keyed `<slug>#<node-id>`. Teach and review write it; `distill_build.py` and teach read it.

Like strength, the design is small local measurements plus arithmetic.

### Three levels

| Level | The learner can… | Typical check |
|---|---|---|
| `recall` | state the claim (T1) in their own words | short answer: "What does Mill say about…?" |
| `explain` | say how the node's inputs produce it (bases, T2) | short answer: "Why does that follow?" |
| `apply` | use it on a case the source doesn't cover | a new case, or a project (`docs/ROADMAP.md`) |

The levels are cumulative: passing a higher level also counts as recall evidence. A node's *grasp* is the highest level with confidence ≥ 0.7.

### Evidence

Every graded question about a node appends one record: `{t, level, result, self}`.

- `result`: `pass` 1 · `partial` 0.5 · `fail` 0, from the ✓/◐/✗ grade.
- `self`: the learner's own rating, given *with* the answer and before the grade: `sure` 0.9 · `unsure` 0.6 · `guess` 0.3. It's optional, and missing ratings are simply not used for calibration.

**Direct confidence** at a level is the latest result, faded by time: d = result · 2^(−age / h). The half-life h = 7 · 2^streak days (cap 180), where streak counts consecutive passes at that level. This matches the review ledger's cooldowns, so a node is due for review about when its confidence has halved. With no evidence, d is *unknown*, which is not the same as 0.

### Propagation

The pyramid says what depends on what, so evidence on one node says something about its neighbours:

- **Cap by inputs.** You can't really explain a conclusion whose inputs you can't recall. explain(n) ≤ min of recall(i) over the inputs of n's non-illustration bases. Inputs with unknown recall don't cap; instead the result is marked *unverified*.
- **Weak credit downward.** A pass at `explain` on n gives each input with *no direct evidence* an inferred recall of 0.5 · d. Inferred values never override direct evidence, and they're shown as inferred.
- **Apply is capped by recall:** apply(n) ≤ recall(n).

### The frontier

A node is *known* at a level when its confidence there is ≥ 0.7. The **frontier** is the set of nodes not yet known at recall whose inputs are all known (premises and other leaves are on the frontier whenever they're unknown). This is the outer fringe from knowledge space theory: what the learner is ready to learn next.

Teach picks from the frontier by **priority = importance · (1 − confidence)**, where importance = 1 + 1 if the node is in the interface + 1 if it's on the weakest-link trace (§4a) + 0.25 per node that uses it. Review uses the same priority for nodes that are due.

### Calibration

Calibration compares self-rating with result over the learner's last 20 rated answers: bias = mean(self − result). A bias above +0.2 means overconfident, and below −0.2 means underconfident. Teach reports this occasionally, not after every question.

**Confident errors** (`sure` and `fail`) get top priority for re-teaching. Research on the hypercorrection effect suggests that errors made with high confidence are often corrected well once feedback is given. This is a lead, to check under the research items.

### Agreement (contested nodes only)

Understanding is not agreeing. On nodes whose acceptability is `contested`, and on contested starting points on the weakest-link trace, teach asks *after* the learner passes `explain`: agree · partly · disagree, plus a one-line reason. It's stored with the node's evidence but **never changes confidence**. Teach uses it to discuss the objection instead of re-teaching.

Idea for later: recompute the apex strength with the learner's agreement standing in for acceptability, giving "how strong this argument is by your lights".

### Stable ids

Ledger keys use node ids, so renaming a node orphans its evidence. Plan: `distill_build.py` keeps a `renames` map in the manifest, and the ledger follows it (not built yet). Splitting or merging nodes across rebuilds is covered by §12.

The constants (0.7, 0.5, the importance weights) are v0 placeholders.

## 5. Structural rules

1. **Fan-in ≤ 7.** No node has more than 7 inputs in total, across all of its bases. If more are needed, chunk them into `structural` intermediate nodes using `generalization`. Fan-out is unrestricted.
2. **Grounding.**
   - An `origin: source` node has at least one anchor.
   - A `structural` node has a basis whose inputs are all grounded.
   - A `gap` node is grounded by the flagged basis that uses it.
   - A `mount` is grounded by its child's coverage report.
3. **Anchors are verbatim** after normalization (§8), and a script checks them. A quote is a *locator*: 25 words or fewer, longer only where the exact wording carries weight. Anchors were the largest authored part in M1.
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

1. **Regenerator** (fresh agent, sees only the pyramid), run twice:
   - **Full run:** it must open every reachable node. This measures content loss only.
   - **Budgeted run:** it starts at `index.md` and navigates freely within a node budget. This measures traversal: what an agent actually finds. M2 showed agents give up on deep branches well before their budget runs out.

   Both runs write out every claim they can recover, in their own words, and log which nodes they opened. Neither ever sees a claim set. Recall is scored on the full run; traversal cost and the gap between the two runs are reported separately.
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
  src/*.yaml         # CANONICAL: the nodes, one file per branch or section
  index.md           # generated. Agent entry: apex, interface, top levels (bounded)
  nodes/<id>.md      # generated. Input list + lateral + used-by + T2 + T3
  map.md             # generated, human mode. Apex + interface diagram
  map.canvas         # generated, human mode. Obsidian Canvas, apex at top, one row per depth
  outline.md         # generated, human mode. The pyramid as a foldable nested list
  claims-a.jsonl
  claims-b.jsonl     # held out
  coverage.md
```

**`src/*.yaml` is the canonical store** (changed after M1). Builders, whether human or agent, write one YAML file per branch or section. `scripts/distill_build.py` checks it and generates everything else, which keeps input lists consistent. Never edit generated files.

**Index is hierarchical, not flat.** A flat list at T0+T1 costs about 45 tokens per node and grows with the source, which undercuts "pay only for depth". So:
- `index.md` holds the apex, the interface and the levels below them until it reaches about 1.5k tokens. It lists only the satellites attached to the nodes it shows. It ends with a pointer saying where the listing stops. Its size doesn't depend on the size of the source.
- Every node file opens with its **input list**: its inputs at T0+T1 with their IDs, ≤ 7 × ~45 tokens. An agent goes deeper one node at a time, and each step costs a bounded amount.
- For grep-style lookup the script can also generate an optional flat `index-full.md`. Agents aren't told to read it.

**Human view:**
- `map.md` shows the apex and interface as one diagram.
- Every node file with inputs renders a small mermaid diagram of itself plus its inputs (≤ 7).
- Obsidian's graph view is force-directed and puts the apex in the middle. So two hierarchical views are generated: `map.canvas`, a Canvas laid out as a tree with the apex on top, and `outline.md`, a foldable nested list. In both, a node with several parents appears under its first parent, and satellites appear under the node they're joined to.

**Mode** (`human` · `agent`) is set at build time and stored in the manifest. `agent` mode writes T2 tersely, skips `map.md`, `map.canvas` and `outline.md`, and leaves diagrams and wikilinks out of node files. Use it for codebases, workflows and system-prompt material.

**Source normalization** (done by script):
- NFKC Unicode, straight quotes and apostrophes, collapsed whitespace, line-break hyphenation joined.
- Paragraphs are blank-line-separated blocks, numbered ¶1… in `source.md`.
- `manifest.source` holds the original locator (URL or path), the edition, and the sha256 of `source.md`.

**IDs** are readable slugs, unique within a pyramid. Wikilinks are written with the path, `[[<slug>/nodes/<id>|label]]`, so they stay unambiguous when several pyramids share one Obsidian vault.

**Location:** `<project>/distill/` by default. It's gitignored in this plugin repo. In your own learning project, commit it if you want it versioned.

### Example node

This shows the *generated* node file. In `src/*.yaml` the same node is one list item with the fields from the frontmatter plus `label`, `claim`, `anchors` (`{p, q}`), `t2` and an optional `residual`. Everything else is generated.

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
4. **Build upward in rounds.** Upper levels are built from the lower nodes' T1s, not the source text. Group nodes by the *logic* of the argument, not by the author's section breaks. Write each parent with typed bases, flag gaps as they appear, and use `structural` nodes when fan-in would exceed 7. Stop at one apex. Rounds are a build convenience: levels are recomputed from the graph afterwards, since a parent's inputs may sit at different depths.
5. **Critique pass** (a separate agent, source in hand): add gap flags (`weak`, `missing-step`, `unsupported`, `circular`), set `validity` on every basis and `acceptability` on every leaf (§4a) with a quoted reason, check premise declarations, and check that hedges survived in T1. In M1, a builder focused on mapping flagged nothing; in M2 the audit found 12 of 17 nodes missing a flag.
6. **Split compound points** flagged by the build check (§3, atomic points). This is mechanical and doesn't change the structure.
7. **Interface:** computed by the rule in §2.
8. **Render:** `scripts/distill_build.py`.
9. **Test** (§7), using fresh agents.
10. **Repair** against set A until the targets pass, then score once on set B.

Annotations (your own notes on a node) go in `distill/<slug>/annotations/<id>.md`. They're never generated or overwritten, so they survive a rebuild.

## 10. How it connects to the rest of learn

- **teach:** teach a source from its pyramid. Its premises are the source's *starting points*, not unconditional truths. Many of Mill's are contested. Teach treats them as candidates: it checks each one with the learner and states it as "Mill assumes…" when it isn't safe to take at face value. Bases are the motivated steps.
- **teach (targeting):** teach picks nodes from the learner's frontier by priority, and asks recall, explain and apply questions per node (§4b). Contested nodes get an agreement question once explained.
- **review:** nodes go into the review ledger with per-level evidence (§4b), and node T1s make good short-answer keys. A node is due when its confidence has roughly halved. How ledger entries reference nodes across rebuilds is in §12.
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
