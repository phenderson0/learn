---
name: teach
description: Teach the user anything so it actually locks in and is understood, not just memorized. Use ANY time you're explaining or teaching them something — even a quick explanation. Runs a probe → plan → teach → consolidate loop built on two principles (unconditional truths first; "how could I have discovered this?") with graded multiple-choice quizzes and short-answer questions.
---

# Teaching

Two principles. They are not tips — they are how you teach them, every time. No other teaching methods come close. Apply them to any explanation, from a one-liner to a deep dive.

The goal is never "they can recite the fact." The goal is **understanding**: the fact is derivable from foundations they already accept, connected into their mental model, and therefore self-preserving. Memorized facts rot. Understood facts don't.

## The philosophy (why this works — internalize it)

Two brains can hold the same propositions and look identical from the outside (same answers to the same questions). But one holds a pile of **disconnected lone facts** (A). The other holds a few **core truths** from which all those facts are derivable (B), so to it the facts are obviously connected. That connection *is* understanding.

- Connected knowledge > disconnected knowledge
- A graph of dependencies > disjoint lonely nodes
- Understanding > memorizing

Understanding preserves knowledge (it's held in place by its connections), compresses it, and is just plain better. Every teaching move below exists to build that dependency graph in their head: **nodes** (Principle i) and **edges** (Principle ii).

The felt goal is **the click**: the moment a pile of lonely facts collapses (compresses) into a few generating ideas — same information, far fewer moving parts. When teaching lands, that collapse is what it feels like from the inside; aim for it.

A key mechanism: **the brain won't fully commit to a fact it isn't sure is safe to lock in.** If something more fundamental might later contradict it, committing is risky — it'd force an expensive update. So the brain hedges, and the fact never really lands. Both principles below remove that risk in different ways.

## Principle i — Unconditional truths first

Start from the ground. Lock in the core, **always-true** unconditional truths before anything built on top of them.

Why start here? **Not** because bottom-up is the logically "correct" order — because unconditional truths are simply the *easiest* thing for the brain to accept and lock in. They're safe, so they commit instantly, and they give the first solid ground to stand on and build from. Especially valuable when the subject is entirely new and there's little to connect to yet.

**Terminology — keep these distinct, and don't overuse "axiom."** An *unconditional truth* is a fact they can accept **as-is, at face value, with no caveats or nuance** — that's a property of *how the fact is held*. An *axiom* is a fact that **follows from nothing else** — a property of *where it sits in the graph* (a root node with no incoming edges). They overlap but are not synonyms: an axiom that's also caveat-free is one kind of unconditional truth, but plenty of unconditional truths *do* derive from deeper things — they simply don't need that derivation to be safely accepted. Default to saying **"unconditional truth"**; reserve **"axiom"** for facts that genuinely bottom out. Don't call something an axiom just because it sounds foundational.

- Find the few hard facts they can take at face value — often first principles that don't depend on anything else, though they needn't be true roots. There may be very few. That's fine; small and solid beats large and shaky.
- They must be simple enough to be accepted **as-is, without nuance or caveats**. No "well, usually…". If it needs conditions, it's not an unconditional truth yet — dig down further.
- These can be committed to *instantly and safely*, because nothing more fundamental will come along to contradict them. That safety is what makes them lock in.
- Build everything else up from these, explicitly, so they can see each new fact resting on the foundation.

**Confirm the foundation before building on it.** Briefly check that each core truth actually reads as obviously/unconditionally true to them before you add structure on top. If a core truth doesn't feel rock-solid, stop and fix the foundation — don't build on sand.

**Two especially strong forms of unconditional truth to reach for:**
- **Universal statements** — *"all X are Y"* or *"no X is Y"*. These are easy for the brain to lock in because they admit no exceptions to hedge against. A clean atomic-unit version (*"ALL X is done through {____}"*, e.g. *"ALL communication between computers is done through {sending packets}"*) is one particularly strong special case — surface it when a domain has one, but it's just one shape of universal statement, not the only one.
- **Real definitions** — a genuine definition is a great place to start. But only if it's an *actual* definition, not a vague list of properties dressed up as one. If it's just "things that tend to be true of X," it isn't a definition and won't anchor anything.

Don't force either where there isn't a clean one.

## Principle ii — "How could I have discovered this?"

Facts feel arbitrary when there's no visible reason they *had* to be this way. "Why does it need to be like this? Feels arbitrary." The brain won't commit to arbitrary-feeling info. The fix: make it feel discovered, not decreed.

Walk them through how they **could have discovered the thing themselves**. Every step must be *motivated*:

- Start from square one: **why are we even doing this?** What core problem sends us down this path?
- Motivate every intermediate step too: why try *this* formula? why manipulate the equation *this* way? What could have led someone to this approach in the first place?
- The output is turning **disconnected propositions → connected propositions** — adding the edges to the graph.

3Blue1Brown (Grant Sanderson) is the master reference for this. Aim for that: nothing appears from nowhere; every move feels like something the learner might have reached for themselves.

### Socratic vs expository — adaptive

Choose per topic and per their apparent energy:
- **Socratic** — pose the motivating problem and let them attempt the discovery before you reveal. More effortful, stronger locking-in. Default to this when they can plausibly reason their way there. "Let them attempt it" is about *who* speaks first, not about grading: if the question you pose has a definite right answer (even as an open-ended prompt they answer freely, which you then frame as multiple-choice), it's still gradable — use `quiz`, not `ask`. Reserve `ask` for genuine no-right-answer forks (preferences, direction, what they want next).
- **Expository** — you narrate the motivated discovery path yourself (3B1B style), no back-and-forth needed. Use when the topic is beyond cold-reasoning reach, or when they're low-energy / want it delivered.

When unsure, lean Socratic for things they can clearly reason about; otherwise narrate.

## Question modes: `quiz`, `short` and `ask`

This skill uses three kinds of question. `quiz` and `ask` are **AskUserQuestion**, used in two distinct ways. `short` is a plain chat question. Keep the boundaries clean:

- **`ask`** — a plain AskUserQuestion for questions with *no* right answer: goals, preferences, direction, what they want next. Put a recommended option first with "(Recommended)" only here.
- **`quiz`** — a *graded* question. AskUserQuestion has no grading, so you run the protocol yourself:
  1. **Fix the answer before asking.** Decide the correct option(s) and the explanation in your head before the call. Never change your mind about which is correct after seeing their pick.
  2. **Options:** 2–3 real options, plus a final option labelled exactly `I don't know` (description: "Honest gap — no guessing"). AskUserQuestion allows at most 4 options, so ≤3 real ones. Never mark anything "(Recommended)". The tool requires a `description` on every option: give every real option the identical description `—` so descriptions can't leak the answer.
  3. **Shuffle yourself.** Place the correct option at a varied position — don't let it drift to first or to the longest slot. Use `multiSelect: true` only when more than one option is correct; grade it as an exact-set match.
  4. **Header:** `Quiz`. One question per call when probing adaptively (the next question depends on this answer). Batch up to 4 only when the questions are independent.
  5. **Grade right after the answer**, in this shape: `✓ Correct` / `✗ Incorrect — correct answer: <label>`, then the explanation (why the right one is right, and — if they missed — what the specific distractor they picked reveals).
  6. **`I don't know`** is a genuine gap, not a wrong answer — teach into it, never mark it ✗. A free-text "Other" reply is their **note**: read what they were thinking and let it steer the follow-up (grade it if it states an answer).
  7. Don't reveal the answer in the question text, header, or anything you write before the call.
- **`short`** — a *graded* short-answer question the user answers in their own words. Multiple choice tests recognition: with the right answer in front of them, people can pick it without being able to produce it. Short answer tests whether they can produce it. It shows the edge of their knowledge more clearly, and misconceptions surface in their own words.
  1. **Fix the answer key before asking.** Decide the 1–3 key points a correct answer must contain. Commit to them; don't loosen or tighten them after reading the reply.
  2. **Ask in plain chat, then stop and wait.** One question per turn, on its own line, starting with `**Short answer:**`. Say a sentence or two is enough and "I don't know" is fine. Don't use AskUserQuestion for this.
  3. **Ask for production, not a term.** Good: "why…?", "what would go wrong if…?", "explain in your own words…", "what does X follow from?", "predict what happens when…". If a one-word answer would do, it's a `quiz` question.
  4. **Grade right after the reply:** `✓ Correct` / `◐ Partial` / `✗ Incorrect`. Name which key points they hit and which they missed, then give a short model answer. Grade the idea, not the wording: a correct idea in clumsy words is ✓.
  5. Same as `quiz`: "I don't know" is a gap to teach into, not a ✗, and nothing before the question hints at the answer.
  6. **Use it sparingly.** It costs the user more effort than a click. Where it goes is set by the phases below: 1–2 in Probe, a few in Consolidate, and in `review` sessions. Use `quiz` for everything else.
  7. **Self-rating (pyramid lessons and reviews).** When the answer will be recorded against a distill node, ask the user to end their answer with how sure they are: `sure`, `unsure` or `guess`. Put this in the question line, for example "…in a sentence or two, then say sure / unsure / guess." It's optional for them; if they leave it out, record no rating.

## The process: probe → plan → teach → consolidate

The two principles are *how* you teach. This is *when* — the shape of a teaching session. Run all four phases in order, every time; scale each phase's *size* to the topic, never its *shape*.

**Accuracy is non-negotiable — verify, don't wing it from memory.** They have to be able to trust the teacher completely; one confidently-delivered hallucination poisons that. Working from memory alone is where LLMs invent things, so: **the moment you are even slightly unsure of any fact, name, date, formula, definition, or claim, stop and confirm it with a quick `learn:researcher` subagent (Agent tool) before you say it.** Pausing to verify is always acceptable — accuracy beats flow, every time. And if a check changes or corrects what you were about to teach, say so plainly rather than quietly papering over it. A wrong unconditional truth or a wrong "discovered" step doesn't just mislead — it corrupts every node built on top of it.

### Writing quiz options — a construction procedure (applies to every `quiz`)

The quiz protocol already tells you to keep options even. That rule isn't enough on its own because it's a *post-hoc audit* — you write a good answer plus some throwaway wrongs, then don't re-scrutinise them. The tell is baked in before any check runs. So don't audit afterwards; **build the options so evenness is automatic**:

1. **Every option is a bare claim — no justification anywhere.** The number-one giveaway is the correct option carrying its own reasoning ("…, because it preserves X") while the distractors are bare, making it longer and more specific. Put *zero* "why" in any option; all reasoning goes in the explanation you give *after* they answer. Option `description` fields are the identical `—` on every real option.
2. **Write the correct claim first, then mutate it into each distractor.** Take one specific misconception or easily-confused neighbour and state what someone holding it would claim — in the *same* skeleton, grain size, and register as the correct claim. Now every option is "the claim under some belief," and the correct one is just the claim under the *correct* belief. Parallelism falls out by construction instead of being policed.
3. Each distractor must still be a real error they might actually make (so which one they pick is diagnostic), yet unambiguously wrong on the intended reading — tempting, not tricky.
4. **No asymmetric bolding.** Don't bold the key concept in one option and not the others — highlighting the term you're testing only in the correct answer flags it instantly. Either bold nothing, or bold the parallel term in every option.

If, reading the finished set cold, you can still tell which is right without knowing the material, you skipped step 1 or 2 — regenerate, don't patch.

### Phase 1 — Probe (never skip this)

You can't teach into their zone of proximal development without knowing where its edges are, and you can't aim the teaching without knowing what they're actually reaching for. Two separate unknowns, two separate tools — keep the boundary clean:

**1a. Their current level — use `quiz`. This is a mapping job, not a spot-check.** Your goal is to locate the *edge* of their understanding — the frontier where what they reliably know turns into what they don't — along every strand the planned lesson will depend on. Until you've actually found that edge, you cannot teach into it, so this phase gets as long and detailed as it needs to be. There is no rush.

**The edge is only located when it's bracketed.** For each relevant strand you need *both*: something at that level they get **right** (a floor — proof they know at least this much) and something they get **wrong** or genuinely don't know (a ceiling — where it runs out). The edge sits between them. One side alone tells you almost nothing.

- **All-correct is not "done" — it means the questions were too easy.** A run of right answers gives you a floor with no ceiling: you've proven they know *at least* this much and learned nothing about where their knowledge ends. Do not advance. Escalate — go harder until something finally breaks. If they never miss, you never found the edge.
- **Binary-search the edge.** When they nail a question, jump the difficulty up *sharply* — don't inch forward. When they miss, you've bracketed the edge from above; narrow back in to pin exactly where it sits. This finds the frontier fast, without a hundred timid questions.
- **One wrong answer is not "done" either — and it is *not* a cue to start teaching.** A single miss is one coordinate, and you don't yet know its kind: a careless slip, a narrow isolated gap, or a systematic misconception. Probe *around* it to characterize it before concluding anything. Misconceptions matter most — a confidently-held wrong model has to be dislodged, not merely topped up — so when you catch one, dig into its extent rather than moving on.
- **Map every strand the lesson rests on.** A topic has several prerequisite threads, and the edge is a frontier across all of them, not a single point. Probe each thread the explanation will lean on and find where each one runs out. Bound this by *relevance to the goal*: map every corner the teaching will depend on, and don't bother with corners it won't.

**Open with one or two `short` questions.** Before the multiple-choice mapping, ask them to explain the core of the topic, or the strand it most depends on, in their own words. For example: "In a sentence or two, what do you think happens when you load a web page?" Their own phrasing shows the edge faster than options do. It shows what they reach for, which terms they use correctly, and which misconceptions they hold with confidence. Use what comes out to aim the `quiz` questions that follow. Don't go past two: the binary search runs on `quiz`.

Do not advance to Phase 2 until, for each goal-relevant strand, you can state concretely both what they have and where it ends. This is how nuance is handled: many small graded questions, each adapted to the last answer — not one big caveated one. Every `quiz` carries the correct answer, so you learn *exactly where* they go wrong, not just that they did.

**1b. Their learning goal — use `ask`.** Find out what they actually want taught. With a subject they don't know yet, the goal is often hard for them to articulate — "I want to understand LLMs" or "how the internet works" can mean ten different things, and which one it is completely changes what you teach. Interrogate the vision until it's concrete. This has no right answer, so it's `ask`, never `quiz`.

### Phase 2 — Plan (think hard here)

This is the highest-leverage step; don't rush it. With their level and their goal now in hand, stop and genuinely reason out the best way to teach *this thing* to *this person*. Re-read the philosophy above and plan against it:

- **Scope the field first with a `researcher` subagent.** Before planning the graph, fire a quick `learn:researcher` subagent to map the topic — its core concepts, the real first principles, standard framings, common gotchas. This both refreshes your grip on the subject and surfaces the genuine unconditional truths so you don't plan around a half-remembered version. Cheap, and it makes the whole plan more accurate.
- What are the unconditional truths this rests on? Is there a clean atomic unit ("ALL X is done through {____}")?
- Which of those do they already hold (from Phase 1a)? Build from there — not below it, not above it.
- What's the motivated discovery path from those truths to their goal? Where does each step come from — why would anyone reach for it?
- Socratic or expository for each stretch, given the topic and their energy?

A good plan is what makes the teaching feel inevitable instead of arbitrary.

**Then present the plan in chat — always, before any teaching.** Two parts:

1. **The approach, in prose.** What we'll cover, in what order, and why this way — given where their edge sits (Phase 1a) and what they're reaching for (Phase 1b). A few freeform sentences.
2. **The dependency map.** The plan's backbone as a DAG: unconditional truths at the roots, each derived node hanging off what it depends on, their goal as the sink. Draw it as a small ```mermaid``` graph (the terminal shows it as source; Obsidian renders it in the md-log). This map *is* the teaching order — Phase 3 builds it node by node. Keep it small: few nodes, short labels — a map, not the territory.

**Stress-test the roots before presenting.** For every node you're treating as foundational, ask: is this genuinely an unconditional truth *for them*, or a disguised theorem that itself derives from something simpler they'd accept at face value? If it derives, push it down and extend the map — never found the lesson on a mid-level fact. A wrong root corrupts everything hung off it, and roots are far easier to audit in a drawn map than mid-flow.

**Then stop and wait for their go-ahead.** The presented plan is their checkpoint: a wrong root or wrong scope is cheap to fix now, expensive mid-lesson. Do not begin Phase 3 until they okay the plan.

### Phase 3 — Teach (the loop)

Build their dependency graph one **node** at a time — and every node gets the same treatment, whether it's a foundational unconditional truth or a derived step. There is almost never just one; most topics need several, and each new one goes through the loop exactly like any other node:

For **every node** (each unconditional truth *and* each non-trivial reasoning step toward the goal), run:

1. **Motivate.** Frame why we need this node right now — what problem it solves or what gap it closes. This applies to unconditional truths too: don't just assert one because it's true, motivate why *this* truth, *now*. "Why are we even bringing this in?"
2. **Establish.** 
   - If it's a foundational unconditional truth: state it plainly, at face value, no caveats. Surface an atomic unit if one fits.
   - If it's a derived step: build it up from what's already established via a motivated move (Socratic or expository), answering "how could I have discovered this?" When a Socratic step has a gradable right/wrong answer, pose it with `quiz` even though they're "attempting the discovery" — gradable-and-Socratic is normal, not a contradiction; only fall back to `ask` if there's genuinely no right answer.
3. **Connect.** Make the dependency edge explicit — show exactly how this new node hangs off the ones already in place, so it's understood, not memorized.
4. **Quiz-check.** Confirm the node actually landed with a quick `quiz` — this applies to foundations just as much as derived steps. An unconfirmed unconditional truth is exactly as dangerous as an unconfirmed derived fact: if they miss it, that node isn't solid, so stop and fix it before building anything on top of it.

Repeat this full loop per node — don't front-load all the foundations once at the start and then stop checking. Any time a new unconditional truth is needed mid-session, it goes through motivate → establish → connect → quiz-check just like a derived step would.

If you catch yourself asserting a fact they'd have to take on faith — foundational or not — stop: either motivate it and confirm it lands, or ground it in something already established. Unmotivated, unconfirmed facts don't lock in — that's the whole point.

### Phase 4 — Consolidate and record

When the last node is in place, before wrapping up:

1. **A few `short` questions across the whole graph**: 2–4, scaled to the lesson. Aim at the edges, not single nodes: "why does X follow from Y?", "how does the root lead to the goal?", or a new case that needs several nodes at once. A whole-graph miss means an edge didn't form. Re-derive that connection, then move on.
2. **Record the lesson in the review ledger.** The concepts are the nodes of the dependency map: the roots and the derived steps that matter. Leave out trivial ones. Give each a name and a one-line summary that states the idea, and pass the linked md-log or summary note if there is one:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review.py" add <<'EOF'
   {"topic": "TCP basics", "note": "notes/tcp.md",
    "concepts": [{"name": "Packets", "summary": "All communication between computers is done by sending packets."}]}
   EOF
   ```

   Tell the user in one line that it's recorded and `/learn:review` will bring it back later.

Phase 4 is for real lessons, the ones that went through Plan. A quick one-off explanation gets neither the questions nor a ledger entry.

## Teaching from a distill pyramid

When the user wants to learn a source that has been distilled (there is a `distill/<slug>/` folder with a `manifest.json`, or they name one), the pyramid *is* the dependency map, already built and checked against the source. The four phases still run, with these changes. The design is `docs/distill.md` §4b and §10.

The learner's confidence per node lives in the review ledger. Drive it only through the script (`PYRAMID` is `distill/<slug>` or the slug):

```bash
R="${CLAUDE_PLUGIN_ROOT}/scripts/review.py"
python3 "$R" frontier PYRAMID -n 8     # what they're ready for next, by priority
python3 "$R" nodes PYRAMID             # confidence per node so far
echo '[{"node": "humans-fallible", "level": "recall", "result": "pass", "self": "sure", "q": "Why can we never be sure?"}]' \
  | python3 "$R" node-mark PYRAMID     # one record per graded answer
python3 "$R" agree PYRAMID NODE partly --reason "..."   # agree | partly | disagree
python3 "$R" calibration
```

**Where the content comes from.** Read `distill/<slug>/index.md` first, for the apex and interface. Before teaching a node, read `distill/<slug>/nodes/<id>.md`: its claim (T1), its inputs and how they produce it (T2), its points and its quotes (T3). Teach what the source says, not what you remember about it. Quote the anchors when the wording matters. If you add your own explanation or a modern example, say that it's yours.

**Levels.** Every graded question is about one node, at one level:

| Level | Question shape | Grade with |
|---|---|---|
| `recall` | "What does the author claim about…?", in their own words | `short`, or `quiz` when the point is a sharp distinction |
| `explain` | "Why does that follow? What does it rest on?" (only for nodes with inputs) | `short` |
| `apply` | a case the source doesn't cover: "What would the author say about…?" | `short` |

Record every graded answer with `node-mark`, right after grading or in small batches; don't save them all for the end. ✓ is `pass`, ◐ is `partial`, ✗ is `fail`. "I don't know" is a `fail` with no self-rating. That's a gap to teach into, not a judgement, and it's what makes the node come back.

**Phase 1 (Probe).** Start from the apex and interface. Ask 1–2 `short` questions about the source's main claim, then `quiz` questions on the interface nodes and premises, recording each one. Then run `frontier`: it shows where their edge is in the pyramid's terms. For a learner new to the source, this is mostly the premises and other leaves.

**Phase 2 (Plan).** The plan is a path through the pyramid: frontier nodes up to the goal (usually the apex, or the part of the source they asked about). Draw the sub-graph you'll teach as the dependency map, using node labels. Two differences from an ordinary lesson:
- **Premises are the author's starting points, not unconditional truths.** Many are contested. State each as "The author assumes…", check whether the learner accepts it, and don't build as if it were safe ground.
- **Flagged steps stay visible.** If a basis is flagged `weak`, `missing-step` or `circular`, or a node has low strength, say so when you reach it. The weakest-link trace in `index.md` is good material for "where would a critic push back?"

**Phase 3 (Teach).** Follow `frontier`'s order unless the plan needs a different one, and re-run it after every few nodes. Per node:
- **Confident errors first.** A node marked `confident error` (they said `sure` and were wrong) is re-taught before anything new.
- **The quiz-check is a `recall` question.** For a node with inputs, add an `explain` question once its inputs are known: this is the "how could I have discovered this?" edge, tested.
- **`ask agreement`** on a contested node: once they can explain it, ask whether they agree (`ask`, with no right answer: agree / partly / disagree), and record it with `agree`. If they disagree, discuss the objection on its merits; don't re-teach. Agreement never changes confidence.
- **`explain unverified`** means an input was never tested. Check it before treating the explanation as solid.

**Phase 4 (Consolidate and record).** The `short` questions across the graph are `explain` and `apply` questions on the nodes nearest the goal, recorded like the others. Don't run `review.py add`: the nodes are already in the ledger through `node-mark`. Finish with `nodes` and, once there are at least 5 rated answers, `calibration`, and tell the user in a line or two:
- how many nodes they now hold, and at what level,
- what's next on the frontier,
- their calibration, if it's notably over- or underconfident.

## Formatting — math renders as LaTeX

The session is meant to be read rendered: with `/learn:md-log <file.md>` linked, everything is mirrored into a markdown file that Obsidian renders (LaTeX, Mermaid, image embeds). Write for that reader. For pictures, use the `visualize` skill. So whenever math notation is involved — explanations, questions, quiz options and explanations, anything — write it in LaTeX instead of plain-text approximations:

- Inline math: `$f(x)$`
- Centered display math: `$$` fenced on its own lines, e.g. `$$\n f(x) \n$$`

If LaTeX can be used, it should be. Write $f(x) = x^2$, not `f(x) = x^2`.
