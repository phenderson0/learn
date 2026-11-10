# learn

[![video](assets/thumbnail.png)](https://www.youtube.com/watch?v=kzcI5F4tGiU)

An AI learning system from the video [How I Use AI to Learn Things](https://www.youtube.com/watch?v=kzcI5F4tGiU) by Amos Blomqvist. This fork is a **Claude Code plugin**.

## What's in it

| Piece | What it does |
|---|---|
| `skills/teach/` | The philosophy and the process: unconditional truths first, "how could I have discovered this?", probe → plan → teach. Loads automatically whenever Claude is teaching or explaining. Also `/learn:teach`. |
| `skills/review/` | `/learn:review [topic]` quizzes you on concepts from earlier lessons, mostly with short-answer questions, and re-teaches what slipped. With no topic it picks the oldest concepts that are due. |
| `skills/visualize/` | Adds one correct, minimal diagram to a lesson when an idea is clearer as a picture. |
| `skills/md-log/`, `skills/md-unlog/` | `/learn:md-log <file.md>` mirrors the session into a markdown file (e.g. in Obsidian) so LaTeX, Mermaid and images render. `/learn:md-unlog` stops it. |
| `agents/researcher.md` | `learn:researcher` checks facts and scopes a topic with WebSearch and WebFetch. |
| `agents/mermaid-maker.md`, `agents/svg-maker.md` | `learn:mermaid-maker` and `learn:svg-maker` write a diagram, render it, look at the PNG, fix it until it's correct, then publish it to `viz/`. |
| `hooks/hooks.json` + `scripts/md_log.py` | The md-log hooks. They log your prompts, Claude's text, and quiz questions and answers. They do nothing until you link a file. |
| `scripts/review.py` | The concept ledger: records each lesson's concepts and schedules reviews. |
| `scripts/render.sh` | Renders Mermaid and SVG to PNG for the maker agents. |

## Install

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

- **Claude Code** and **python3** (python3 runs the md-log hook).
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

## Usage

1. Open Claude Code in a learning project. That folder works best if it is, or sits inside, an Obsidian vault.
2. Optional: `/learn:md-log notes/tcp.md`, then open that file in Obsidian.
3. Ask to learn something, such as "teach me how TCP works". Claude quizzes you to find the edge of what you know, asks what you're aiming for, shows a plan and a dependency map for you to approve, then teaches one node at a time. It ends with a few short-answer questions across the whole lesson and records the lesson's concepts for review.
4. Later: `/learn:review` to review the oldest concepts that are due, or `/learn:review the TCP stuff` to pick a topic yourself.

Diagrams go to `<project>/viz/`. Lessons embed them as `![[viz-….png|500]]`.

## Notes

- Short-answer questions are asked in plain chat: answer in your own words. Lessons use one or two at the start to find the edge of what you know and a few at the end.
- Multiple-choice quizzes use AskUserQuestion. Claude decides the answer before asking, shuffles the options, adds an `I don't know` option, then grades with ✓/✗ and an explanation. Type in "Other" to give a free-text answer.
- The system works without subagents, because the main session does the teaching. You lose fact checking and visuals.
- The teaching skill was written for one learner. Edit `skills/teach/SKILL.md` to fit how you learn.
- md-log stores its link state in `<project>/.claude/learn-md-log.json`.
- The review ledger is `<project>/.claude/learn-ledger.json`. A concept is first due 7 days after the lesson. Each pass doubles the wait (7, 14, 28 … up to 180 days) and a fail resets it to 7, so recently reviewed concepts stay out of the way. Commit it in your learning project if you want reviews to follow you into remote sessions.
