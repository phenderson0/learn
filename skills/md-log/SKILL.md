---
name: md-log
description: Link a markdown file (e.g. in an Obsidian vault) that mirrors this teaching session — prompts, lesson text, and quiz Q&A — so LaTeX, Mermaid and diagrams render.
argument-hint: <path/to/file.md>
disable-model-invocation: true
---

Run this with Bash, then tell the user the one-line result:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/md_log.py" link "$ARGUMENTS"
```

If no path was given, run it with `status` instead of `link "…"` and ask the user for a path.

The plugin's hooks backfill the session so far into the file on the next event and append new messages live. Keep writing as usual — LaTeX (`$…$`, `$$…$$`), ```mermaid``` blocks, and `![[viz-….png|500]]` embeds will render in Obsidian.
