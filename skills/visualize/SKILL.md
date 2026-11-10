---
name: visualize
description: "Add a correct, minimal visual to a lesson — a diagram or geometric picture — that renders inline in the Obsidian md-log. Use when an idea is genuinely clearer as a picture: a dependency graph, system/flow, sequence, state machine, tree, comparison, or a spatial/geometric thing (coordinate geometry, number line, vectors, a plot, a physical layout). Outsources authoring+rendering to a maker subagent that verifies the image by looking at it, then you embed the returned file."
---

# Visualize

A picture earns its place only when it shows something words can't — shape, structure, direction, relationship, geometry. This skill produces ONE such picture, guarantees it is **correct** (the maker renders it and looks at it before returning), and drops it into the lesson so it renders inline in the Obsidian `md-log` file.

You are the **creative director**. You decide the exact idea and distill it to its fewest carrying elements. A **maker subagent** does the authoring, rendering, visual verification, and saving, then returns a filename. You embed that filename in your reply.

## When to visualize (and when not to)

This teaching system builds a **dependency graph in the learner's head** — unconditional truths at the root, derived facts hanging off them. A visual is powerful exactly when it makes that structure (or a geometry) visible. Reach for one when:

- The idea is a **structure or relationship**: dependencies, a system with parts and arrows, a flow/pipeline, a sequence of exchanges, a state machine, a tree/hierarchy, a comparison, a containment (what's inside vs outside).
- The idea is **spatial or geometric**: coordinate geometry, a number line, vectors, a function's shape, a physical arrangement.

Do NOT visualize when prose or a single equation already carries it. A decorative diagram that just restates the sentence next to it adds noise and a chance to be wrong. When in doubt, don't — a missing visual is cheaper than a false one.

## Choose the maker

Two maker agents ship with this plugin:

- **`learn:mermaid-maker`** — structural/relational visuals: dependency graphs, flowcharts, sequence/state/ER/class diagrams, trees, mindmaps, timelines. This is the default and fits the dependency-graph pedagogy directly.
- **`learn:svg-maker`** — spatial/geometric visuals Mermaid can't lay out: exact coordinates, geometry figures, number lines, vectors, plots, custom shapes.

Rule of thumb: if it's *nodes-and-edges / relationships*, use mermaid-maker. If it's *positions-and-shapes / geometry*, use svg-maker.

## Brief the maker well: one idea, fewest elements

The most common failure is **cramming** — every extra label makes the picture harder to read AND harder to lay out correctly. Before briefing, prune to the fewest elements that carry the idea, and for each ask: *"if I delete this, is the idea still clear?"* If yes, delete it.

Give the maker the concept AND the concrete elements you want — not a vague topic, and not a long checklist.

- BAD: "make a diagram about how TCP works"
- GOOD: "graph TD: a node 'packet' at the top; arrows down to 'ordering' and 'retransmit on loss'; both arrows down into 'reliable stream'. No title. Show that reliability is built FROM packets, not alongside them."

Keep the idea intact but trust the maker to compose; if your brief lists more than ~5–7 elements, cut it first.

## Invoke

Dispatch the maker with the **Agent** tool (`subagent_type: "learn:mermaid-maker"` or `"learn:svg-maker"`). The maker starts cold, so the prompt must carry everything:

```
Brief: <your minimal, concrete brief>
Render script: ${CLAUDE_PLUGIN_ROOT}/scripts/render.sh
Scratch dir: <a fresh folder under your scratchpad directory, or /tmp/learn-viz-<slug>>
Publish dir: <project root>/viz   (export LEARN_VIZ_DIR=<it> before publishing if the cwd differs)
```

The maker authors the source, renders it to a PNG with the script, **looks at the PNG (Read) and iterates until it is correct and clean**, publishes it into `viz/` with a unique filename, and returns:

```
RESULT:
filename: viz-<slug>-<timestamp>.png
path: <project>/viz/viz-<slug>-<timestamp>.png
```

If it returns `RESULT: NONE`, it couldn't make a correct picture of the brief — simplify or rethink, or decide the visual isn't worth it. If the reason is a missing renderer, tell the user once (`bash ${CLAUDE_PLUGIN_ROOT}/scripts/render.sh check` shows what's installed; see the plugin README) and carry on in prose. Never hand-author or fake a diagram yourself; correctness depends on the maker's render-and-inspect loop.

## Embed it in the lesson

Put the embed directly in your teaching reply, using Obsidian's wikilink embed with the returned **filename** (not the full path) and a display width:

```
![[viz-<slug>-<timestamp>.png|500]]
```

The md-log hook (`/learn:md-log`) mirrors your reply into the linked `.md`, and Obsidian resolves the embed by filename anywhere in the vault — so keep `viz/` inside the vault (i.e. the learning project is, or lives in, the vault). The terminal can't show images, so also give the absolute path on its own line for anyone reading there. Width `|500` is a good default; use larger for dense diagrams. Introduce the visual in a sentence, then let it carry the idea — don't narrate every element back in prose.

## Why this is reliable

- The maker never returns a picture it hasn't **looked at**, so "renders fine but says something false" is caught before it reaches the learner.
- PNG embed means **what the maker verified is pixel-identical to what the learner sees** — no re-render drift.
- Unique filenames keep Obsidian's by-filename embed resolution unambiguous.

> The makers render through `scripts/render.sh` (Mermaid via `mmdc` / `npx @mermaid-js/mermaid-cli` + an installed Chrome/Chromium; SVG via `rsvg-convert`, fallback ImageMagick or cairosvg). You don't render anything yourself — you only brief the maker and embed the filename it returns.
