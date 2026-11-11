# Roadmap and TODO

Long-range ideas, written down so they aren't lost. None of this is scheduled yet. Each item can be handed to a subagent to research, or picked up and fleshed out later. Current work is in `docs/distill.md` (spec), `docs/distill-m1.md` and `docs/distill-m2.md` (results).

## The goal of distill

A digital representation of information that is **neither storage compression nor summarization, but a combination of both that does better than either**:

- **Lossless (at a stated weight):** nothing important is lost, and that is checked, not assumed (spec §7).
- **Easier to traverse,** for a human (map, outline, canvas) and for an agent (a bounded index, one node at a time).
- **Smaller than the original.** Not true yet: Mill's authored YAML is about 16k tokens against 24k for the source, but the rendered files are about 30k. That needs to be measured and tracked.
- **General:** ultimately a data structure for representing any concept or body of information, not only argumentative essays.

## Research

- [ ] **Argumentation theory.** Gradual semantics for bipolar argumentation frameworks (support and attack), DF-QuAD, and other quantitative argumentation schemes. Feeds the strength score (spec §4).
- [ ] **Related fields.** Possible leads to check, not yet verified as relevant:
  - the hypercorrection effect and calibration of confidence (for §4b),
  - argument mapping and the Toulmin model,
  - Rhetorical Structure Theory (how texts are built from relations between parts),
  - Novak's concept maps,
  - schema theory and chunking in cognitive psychology,
  - knowledge space theory (what a learner knows, as structure),
  - minimum description length and Kolmogorov complexity (compression as understanding).
- [ ] **The limit is extraction quality.** The structure can only be as good as the LLM's extraction. Ways to address it:
  - multiple independent extractions,
  - the critique pass,
  - mechanical checks,
  - held-out claim sets,
  - agreement measures between raters.

  Look for more.

## distill features

- [ ] **Anchors as pointers.** Store anchors in `src/*.yaml` as `{p, start, end}` into `source.md` instead of verbatim quotes. Builders still write quotes, the build script resolves them, and views expand them back. Decided 2026-11-10, see `docs/distill-essence.md`. Needs a spec §8 update and a `distill_build.py` change.
- [ ] **Track size.** Report canonical-store size over source size per pyramid, and check it grows at most linearly (`docs/distill-essence.md` §4).

- [ ] **Learner confidence per node.** Designed in spec §4b (2026-11-10): three levels (recall, explain, apply), self-rating with calibration, capping by inputs plus a frontier, and agreement on contested nodes. Still to do: ledger schema, a script, and the teach and review integration.
- [ ] **"Help me understand" for codebases and projects.** For people who vibe-coded further than they understand. Distill a codebase in agent and human modes, then teach it through `learn`, fully, losing nothing important, until the user could explain the project to someone else. Also applies to books.
- [ ] **Live distillation during a Claude Code session.** Build or update nodes as the session works. Plugin hooks on Edit/Write and Stop could append to a session pyramid, so you can go back and understand what the model did and why.

## learn features

- [ ] **Assessment by projects, not just questions.** Beyond short-answer and multiple-choice quizzes: show understanding by *using* it to make something new. This needs design per domain:
  - **Code:** build something that uses the concept.
  - **Math and STEM:** work on paper, derivations, applying ideas to new problems.
  - **Books:** a separate kind of project that proves you understood the book.

## Project

- [ ] **Roadmap to one repo.** Merge distill, learn, review and the integrations above into one coherent plugin, with a staged plan.
- [ ] **Ethics: fork or own project?** At what point is this repo its own work rather than a fork of `amosblomqvist/learn`? Points to discuss:
  - distill is new and original, while teach, visualize and md-log come from upstream.
  - **The upstream repo has no license.** By default that means its author keeps all rights, and GitHub's terms only cover viewing and forking on GitHub. Worth asking the original author for a license or permission before treating upstream code as reusable elsewhere. (Not legal advice.)
  - Options include keeping a fork with clear credit, splitting distill into its own repo with its own license, or both.
