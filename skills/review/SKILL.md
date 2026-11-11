---
name: review
description: Run a review session that keeps earlier lessons fresh. Quizzes the user on concepts learned a while ago, mostly with short-answer questions, re-teaches anything that slipped, and records results so recently reviewed concepts are skipped for a while. Use when the user asks to review, revise, refresh or practise what they've learned, with or without naming a topic.
argument-hint: "[what to review — leave empty to let Claude pick]"
---

# Review

A review is retrieval practice, not a re-lesson. The user pulls each concept back out of memory, and you find out which ones held. Everything the `teach` skill says about questions applies here: the `quiz` protocol, the option-writing procedure, the `short` protocol, LaTeX for math, and verifying any fact you're unsure of with `learn:researcher`.

The ledger lives at `<project>/.claude/learn-ledger.json`. Drive it only through the script:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review.py" pick -n 8          # oldest concepts that are due
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review.py" list [--topic X]   # everything, with due dates
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review.py" mark --pass 3 7 --fail 5
```

The ledger holds two kinds of item:
- **Concepts** from ordinary lessons, with numeric ids like `[3]`. Record them with `mark`.
- **Pyramid nodes** from lessons taught from a distill pyramid, with ids like `[mill-liberty-2#humans-fallible]`. Each has a confidence per level (recall, explain, apply) and a grasp, the highest level known. Record them with `node-mark`, and look at them with `nodes` and `frontier`. The `teach` skill's section "Teaching from a distill pyramid" has those commands and the question levels.

## 1. Choose what to review

What the user asked for: `$ARGUMENTS`

- **Nothing named:** run `pick`. It lists due concepts (oldest first) and due pyramid nodes (most important first: their recall confidence has roughly halved). Take 5–10 items across both. Use fewer if few are due, and favour spreading across topics over taking a whole topic at once. If nothing is due, say when the next concept is due and offer to review something anyway (via `list`).
- **A distilled source named** ("review the Mill stuff"): run `nodes PYRAMID` and pick nodes with low confidence or a past due date, plus any `confident error`. Fill up from `frontier` only if they ask to go further: that's new material, so it's a lesson, not a review.
- **A topic, note, or theme named:** run `list` (with `--topic` when a keyword fits) and choose the matching concepts by judgement. The match is semantic: "the philosophy stuff" can match a topic called "Idealism vs. Materialism". The user asked explicitly, so concepts that are still cooling down are allowed. Prefer due ones when there are more than ~10 to choose from.
- **A source not in the ledger** (a note file, a chapter, "what we did last week"): read it, pull out its key concepts, and record them with `add` before reviewing (see the `teach` skill's Phase 4 for the format; set `learned` to the note's date if it has one). This way they get tracked from now on.
- **Empty ledger and nothing named:** look for lesson notes in the project (for example `notes/*.md`). If there are some, offer to backfill them into the ledger. Otherwise say there's nothing to review yet.

Show the user the list of concept **names** you'll cover, grouped by topic. Don't show summaries, since they give the answers away. Then start. No plan approval is needed.

## 2. Quiz

- **At least one question per concept.** Lean on `short`, because recall without options is the real test of whether something stuck. Use `quiz` (multiple choice) for a concept when its point is a sharp distinction between near neighbours. About two thirds short answer is a good mix.
- **Ask about understanding, not wording.** Ask why it is true, what it follows from, what would break without it, or how to apply it to a new case. A concept counts as held when the user can rebuild it, not just name it.
- **Interleave topics** instead of finishing one before starting the next. Mixing is harder and makes retrieval stronger.
- **Before each concept, read its note if it has one**, so your answer key matches what was actually taught.
- **One question at a time.** Grade each before asking the next.
- **Pyramid nodes:** ask at the node's grasp level, and one level up when it's solid: a node held at `recall` gets an `explain` question if it has inputs. Read `nodes/<id>.md` first so the answer key matches the source. Ask for a self-rating (`sure` / `unsure` / `guess`) with each short answer.

## 3. When something slipped

A miss or "I don't know" means the concept didn't hold. Re-teach it briefly, using the `teach` principles: go back to the unconditional truth it rests on and re-derive it with "how could I have discovered this?". Don't just restate the answer. Then ask one fresh question on the same concept, worded differently. Record the concept as **fail** even if the retry is right: the point is that it didn't survive the gap, and a fail brings it back sooner.

A partial short answer that misses a key point is a **fail**. A partial that only fumbles wording or a minor detail is a **pass**.

## 4. Record and wrap up

Run `mark` once at the end with every reviewed concept, passes and fails. Record pyramid nodes with `node-mark` as you go, one record per graded answer. Use the grade as given (`pass`/`partial`/`fail`), not the stricter concept rule above, because node confidence already counts a partial as half. A re-taught node's retry is recorded too, after the miss; the miss stays in the record. Then give a short summary:

- what held and what slipped,
- any misconception that came up, in one line each,
- when the next review is due (from `mark`'s output, and `pick` for nodes),
- for pyramid nodes, their calibration once there are 5+ rated answers (`calibration`), if it's notably off.
