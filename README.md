# distill + learn

**Turn a source into a map of its ideas, then learn from that map.**

This repo has two parts that are meant to work as one system:

- **distill** (the main project, in development) breaks a source (an essay, a chapter, eventually a book or a codebase) into a layered *pyramid* of connected ideas. It is close to lossless, every claim is traceable to the text, and each argument's strength is scored. Both people and AI agents can move through it.
- **learn** (working, a Claude Code plugin) is a teaching system. It probes what you know, teaches one idea at a time, quizzes you, and schedules reviews so ideas stay fresh.

distill builds the map, and learn walks you through it.

> learn started as a fork of [amosblomqvist/learn](https://github.com/amosblomqvist/learn), the system from Amos Blomqvist's video [How I Use AI to Learn Things](https://www.youtube.com/watch?v=kzcI5F4tGiU). The teaching skill, visuals and md-log come from that project. distill, review, short-answer questions and the plugin packaging were added here.

---

## distill

### The idea

A summary throws detail away, and compression keeps everything but can't be read. distill aims between the two:

| | Summary | Compression | **distill** |
|---|---|---|---|
| Keeps the important content | partly | yes | **yes, and it's tested** |
| Can be read and navigated | yes | no | **yes, layer by layer** |
| Shows how ideas depend on each other | no | no | **yes, with typed links** |
| Can be traced back to the source | rarely | n/a | **every claim cites its paragraph** |

### What a pyramid looks like

```
                    ┌───────────────────────┐
                    │  apex: the thesis     │   T0 label  (≤ 6 words)
                    └──────────▲────────────┘   T1 claim  (one sentence)
              derivation │     │ support        T2 explanation
           ┌─────────────┴─┐ ┌─┴─────────────┐  T3 quotes + ¶ anchors
           │ main argument │ │ main argument │
           └──▲─────────▲──┘ └──▲────────────┘
              │         │       │    ◄── objects ── opponent view
          premise    detail   detail
```

- **Nodes** are typed. An *idea* is a claim, a *detail* is evidence or an example, and a *mount* is a whole sub-pyramid plugged in. Each node records where it came from (the source, structure added by the builder, or a gap the source leaves) and whose voice it is (the author, a view the author reports, or an opponent).
- **Tiers** let you read at any depth. A label, a one-sentence claim, an explanation, then the exact quotes.
- **Bases** say *how* a node follows from the nodes below it: derivation, support, generalization or illustration. **Lateral edges** connect ideas across the tree: objects, rebuts, qualifies, applies, contrasts, same-as.
- **Strength** is computed, never guessed. A critique pass rates how valid each step is and how acceptable each starting point is. A small set of rules then combines those ratings up the tree, so every claim gets a 0–100 score and a *weakest link* you can follow down to see where an argument is thinnest.
- **Faithful, with gaps flagged.** The builder may add structure, but never words in the author's mouth. Missing steps, weak inferences and circular arguments are flagged, not fixed.
- **Recursive by design.** Each pyramid exposes a small *interface* (its apex and that apex's inputs), so pyramids can be mounted inside larger ones. Big sources stay navigable instead of becoming one enormous graph.

### Outputs

Run on a source, distill writes `distill/<slug>/`:

| File | For |
|---|---|
| `src/*.yaml` | The authored pyramid, the one source of truth |
| `nodes/<id>.md` | One page per node: inputs, lateral links, used-by, explanation, quotes. Obsidian wikilinks included |
| `index.md` | A token-budgeted entry point for agents (about 1.5k tokens) |
| `map.canvas` | An Obsidian canvas, apex at the top |
| `outline.md` | A foldable outline of the whole argument |

### Is it any good? (tested on Mill, *On Liberty*, Ch. 2)

Fidelity is **measured, not assumed**. Independent agents pull out every claim in the source, a fresh agent rebuilds the text from the pyramid alone, and a strict judge compares the two. The final score uses a claim set that was **held out** during repairs:

| Claim weight | Recall | Target |
|---|---|---|
| Core | **100%** | 100% ✓ |
| Supporting | **92%** | 95% |
| Illustrative | **97%** | 80% ✓ |

Full results are in [`docs/distill-m1.md`](docs/distill-m1.md) and [`docs/distill-m2.md`](docs/distill-m2.md).

### Status

distill is **experimental**. The design is settled ([`docs/distill.md`](docs/distill.md)), and the scripts and test agents work. A one-command `/learn:distill` isn't built yet: today the pipeline is run by hand from a Claude Code session.

| Piece | What it does |
|---|---|
| `scripts/distill_ingest.py` | Normalizes the source, numbers its paragraphs, and optionally hides a range from the builder (a blind check) |
| `scripts/distill_build.py` | Checks the pyramid (anchors, sizes, fan-in, premises, compound points), computes levels, the interface and strength, and renders every view |
| `scripts/distill_critique_merge.py` | Folds a critique pass's ratings and flags into the pyramid |
| `scripts/distill_score.py` | Scores a regeneration run against a claim set |
| `agents/distill-*.md` | Test agents: extractor, regenerator, judge, auditor |

What's next is in [`docs/ROADMAP.md`](docs/ROADMAP.md): learner confidence per node, a "help me understand this codebase" mode, distilling a Claude Code session live, and merging pyramids.

---

## learn

A teaching system for Claude Code, built on two principles: **unconditional truths first**, and **"how could I have discovered this?"**

### How a lesson goes

1. **Probe.** A few quick questions find the edge of what you know, including one or two short-answer questions in your own words.
2. **Plan.** Claude asks what you're aiming for, then shows a plan and a dependency map for you to approve.
3. **Teach.** One node at a time, with multiple-choice quizzes and a diagram where a picture is clearer.
4. **Consolidate.** Short-answer questions across the whole lesson. Then the lesson's concepts are recorded for review.

Later, `/learn:review` brings back concepts that are due. Each pass doubles the wait before the next review, and a miss resets it, so you're asked about what's fading, not what you just saw.

### What's in it

| Piece | What it does |
|---|---|
| `skills/teach/` | The philosophy and the process: probe → plan → teach → consolidate. Loads automatically whenever Claude is teaching or explaining. Also `/learn:teach`. |
| `skills/review/` | `/learn:review [topic]` quizzes you on concepts from earlier lessons, mostly with short-answer questions, and re-teaches what slipped. With no topic it picks the oldest concepts that are due. |
| `skills/visualize/` | Adds one correct, minimal diagram to a lesson when an idea is clearer as a picture. |
| `skills/md-log/`, `skills/md-unlog/` | `/learn:md-log <file.md>` mirrors the session into a markdown file (e.g. in Obsidian) so LaTeX, Mermaid and images render. `/learn:md-unlog` stops it. |
| `agents/researcher.md` | `learn:researcher` checks facts and scopes a topic with WebSearch and WebFetch. |
| `agents/mermaid-maker.md`, `agents/svg-maker.md` | `learn:mermaid-maker` and `learn:svg-maker` write a diagram, render it, look at the PNG, fix it until it's correct, then publish it to `viz/`. |
| `hooks/hooks.json` + `scripts/md_log.py` | The md-log hooks. They log your prompts, Claude's text, and quiz questions and answers. They do nothing until you link a file. |
| `scripts/review.py` | The concept ledger: records each lesson's concepts and schedules reviews. |
| `scripts/render.sh` | Renders Mermaid and SVG to PNG for the maker agents. |

### Usage

1. Open Claude Code in a learning project. That folder works best if it is, or sits inside, an Obsidian vault.
2. Optional: `/learn:md-log notes/tcp.md`, then open that file in Obsidian.
3. Ask to learn something, such as "teach me how TCP works".
4. Later: `/learn:review` to review the oldest concepts that are due, or `/learn:review the TCP stuff` to pick a topic yourself.

Diagrams go to `<project>/viz/`. Lessons embed them as `![[viz-….png|500]]`.

---

## Install

Everything ships as one Claude Code plugin, named `learn`.

From GitHub:

```
/plugin marketplace add phenderson0/learn
/plugin install learn@learn-marketplace
```

From this folder, without pushing:

```
/plugin marketplace add /path/to/learn
/plugin install learn@learn-marketplace
```

To try it for one session: `claude --plugin-dir /path/to/learn`.

### Remote sessions (Claude Code on the web)

Cloud sessions don't read your local `~/.claude`. They read `.claude/settings.json` in the repo you open. Add this to any project where you want the plugin:

```json
{
  "extraKnownMarketplaces": {
    "learn-marketplace": { "source": { "source": "github", "repo": "phenderson0/learn" } }
  },
  "enabledPlugins": { "learn@learn-marketplace": true }
}
```

## Requirements

- **Claude Code** and **python3** (python3 runs the md-log hook and the review ledger).
- **For distill:** `pip install pyyaml`.
- **Optional, for diagrams.** Without these, `visualize` tells you once and the lesson continues in prose.
  - Mermaid: Node.js. `npx` fetches `@mermaid-js/mermaid-cli`. Chrome or Chromium is also needed; set `PUPPETEER_EXECUTABLE_PATH` to use a specific one.
  - SVG: `rsvg-convert`, ImageMagick, or `pip install cairosvg`.
  - On Debian/Ubuntu/WSL: `sudo apt install nodejs npm librsvg2-bin chromium`
  - To see what's installed: `bash scripts/render.sh check`
  - **WSL notes:**
    - If `apt` fails with `Network is unreachable` on IPv6 addresses, force IPv4: `echo 'Acquire::ForceIPv4 "true";' | sudo tee /etc/apt/apt.conf.d/99force-ipv4`
    - `sudo npm i -g` can skip mermaid-cli's Chrome download. Install it as your own user:
      `sudo apt install -y unzip libasound2t64` then `npx -y @puppeteer/browsers install chrome-headless-shell@<version in the mmdc error> --path ~/.cache/puppeteer`
    - If Chrome still won't start, `ldd ~/.cache/puppeteer/chrome-headless-shell/*/*/chrome-headless-shell | grep "not found"` lists any other missing libraries.

## Notes

- Short-answer questions are asked in plain chat: answer in your own words.
- Multiple-choice quizzes use AskUserQuestion. Claude decides the answer before asking, shuffles the options, adds an `I don't know` option, then grades with ✓/✗ and an explanation. Type in "Other" to give a free-text answer.
- The system works without subagents, because the main session does the teaching. You lose fact checking and visuals.
- The teaching skill was written for one learner. Edit `skills/teach/SKILL.md` to fit how you learn.
- md-log stores its link state in `<project>/.claude/learn-md-log.json`.
- The review ledger is `<project>/.claude/learn-ledger.json`. A concept is first due 7 days after the lesson. Each pass doubles the wait (7, 14, 28 … up to 180 days) and a fail resets it to 7. Commit it in your learning project if you want reviews to follow you into remote sessions.
- `distill/` output folders are gitignored here, since they contain the full source text.
