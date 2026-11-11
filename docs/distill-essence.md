# distill: what "essence" means

The design philosophy behind distill's long-range goal, written down on 2026-11-10 after a question-and-answer session. The spec (`docs/distill.md`) says what distill *does*. This file says what it is *for*, and how we'd know it worked. Open threads are tracked in `docs/ROADMAP.md`.

**Inspiration:** Douglas Hofstadter, especially *Gödel, Escher, Bach* (GEB). GEB is a planned future test text for distill.

## The goal

The closest achievable approximation of storing the *essence* of a topic, book, codebase or other body of information in a structured data set. The approximation should be verifiable and quantifiable, and it should be useful above all for learning.

### Working definition

> A structure S captures the essence of a source T for a purpose P if a reader R, given only S plus its own background knowledge K, can do what P requires with T's content (regenerate it, answer from it, learn it, extend it) within a stated error d, and S is meaningfully smaller than T.

This is rate-distortion framing: the best fidelity for a given size. "Lossless at weight W" (spec §1) is the special case where P = regenerate claims and d = 0 above W.

## Positions

### 1. What test shows the essence was captured
Four tests, layered:

| Test | Question it answers | Serves |
|---|---|---|
| **Regeneration** | Is the content in the structure at all? | the floor; content loss |
| **Answerability** | Can an agent answer questions about the source from the structure, on a budget? | agent use |
| **Equivalent learner** | Does studying the structure teach as well as reading the source? | learning |
| **Generativity** | Can you produce *new*, correct things in the source's spirit (examples, applications, extensions)? | **the ideal** |

Generativity is the goal even if it is never fully reached. "Correct in the source's spirit" is deliberately broader than "what the author would agree with", because distill must also work on codebases and other information structures, not only books.

### 2. Whose essence
No single answer. The essence is not just what the author meant, nor just what the text literally says, nor just what one reader takes away. It is some combination, and the right combination **depends on the purpose**:

- **Textbook:** what the text literally says is closest to its essence.
- **Poem:** closer to what the author meant or what a competent reader takes away.
- **Default for learning:** lean toward what the author meant.

This works like **translation**: every translation loses something, and what to keep depends on what the translation is for. Distillation is the same. The best we can do is make sure the pyramid serves its use case, and *say* which kind of essence it targets.

A possible mechanism: the build pipeline classifies which kind of essence the source calls for. Or build **several pyramids per source**, each targeting a different kind of essence, which together come closer to the whole. Hofstadter's *Le Ton beau de Marot* argues this for translation.

### 3. Form
Form is part of the essence. GEB is the clearest case: the Crab Canon reads the same forwards and backwards, and the dialogues act out the chapters that follow them. A list of claims loses all of that. What "form" means depends on the subject:

- **Literature:** literal structure.
- **Code:** the meta-structure (architecture, decomposition), not styling or the layout of a single function.

How to represent and test form is open. It will need more thought once distill is more fleshed out.

### 4. Size and minimum description length
- **The foremost application is learning.** A good pyramid is the shortest path from base claims up to the apex. This is the case for minimum description length (MDL): understanding as the shortest description that still regenerates the content.
- **Hope:** for long sources (over about 100 pages), the canonical store is smaller on disk than the source text.
- **Hard limit:** size grows at worst linearly with the source. Worse than linear means the structure needs rethinking.
- **Realistic expectation:**
  - Smaller than the raw text is plausible, because long books repeat their ideas and the ratio should improve with length.
  - Mill's authored YAML is already about 0.67× the source.
  - Beating a *gzipped* source is not a goal: gzip keeps every byte and understands nothing.
  - Measure the canonical store, not the rendered views.
- **Anchors become pointers into the source** instead of verbatim quotes. Quotes copy the source into the pyramid. See the decision below.

### 5. Measurement
- **LLM judges and extractors are necessary** for distill to be automatic and efficient.
- **Non-LLM, mechanical measures are preferred** wherever they are possible: anchor checks, structural checks, form predicates, and possibly likelihood-based measures.
- A philosophically pure representation would need more mechanical machinery. That is a direction, not a requirement.

### 6. Schema
- **Now:** distill stays built around argument, so it reliably builds good trees first.
- **Long term:** a dynamic, self-describing structure that can store very complex data while staying navigable for humans and agents. It should have as few fixed rules as possible, so the structure can emerge from the source itself rather than be imposed. The aim is to represent the information as faithfully as is physically possible.
- **Distilling distill** is in scope. It probably needs only minor changes to the current structure.

## Decision: anchors as pointers (2026-11-10)

Store anchors in the canonical YAML as **pointers into `source/source.md`**, not as verbatim quotes.

- **Builders still write quotes.** LLMs can't count character offsets. At build time, `distill_build.py` finds each quote in its cited ¶ and replaces it with `{p, start, end}`.
- **Pin the source to its hash.** `manifest.source` already stores the sha256 of `source.md`, so pointers stay valid as long as the source doesn't change. If the hash changes, every anchor is flagged for re-resolution.
- **Views still show the quote.** The generated node files expand pointers back into quotes, so humans and agents reading a node see the text, and only the canonical store shrinks.
- **Tradeoff:** a pyramid is no longer self-contained without its `source.md`. That's acceptable, because anchors were always pointers into it.

## Research leads

Four research scouts reported on 2026-11-10: Hofstadter's toolkit, information theory, knowledge structure, and measuring fidelity. Their merged shortlist is in `docs/distill-research.md`. Their main tensions with the current spec:

- **Claims are true/false statements** (spec §2, §7), so form is invisible to the tests.
- **Loops are treated as defects** (the `circular` flag, §5). In GEB, a tangled hierarchy is the point.
- **One pyramid per source** (§1), versus a family of pyramids that each declare their constraints.
- **The node types are fixed before reading** (§3–4), versus a schema that emerges from the source.
- **The regenerator's background knowledge is uncontrolled** (§7). LLMs already know Mill and GEB, so recall needs a no-pyramid baseline.
