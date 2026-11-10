#!/usr/bin/env python3
"""md-log — mirror the teaching session into a markdown file (e.g. in Obsidian).

The terminal doesn't render LaTeX, Mermaid or images; Obsidian does. This
script is driven by Claude Code hooks (see hooks/hooks.json) plus two CLI
subcommands used by the /learn:md-log and /learn:md-unlog skills.

  md_log.py link <file.md>   link a markdown file for this project (backfills on next event)
  md_log.py unlink           stop logging
  md_log.py status           show the linked file
  md_log.py hook             read a hook event JSON on stdin and append to the log

Captured: user prompts, assistant text, AskUserQuestion Q&A (questions are
written before the user answers so the reader sees them live). Other tool
calls are omitted. Append-only. Never blocks Claude: every error is swallowed.
"""
import json
import os
import sys
from pathlib import Path

STATE_NAME = "learn-md-log.json"


def project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def state_path() -> Path:
    return project_dir() / ".claude" / STATE_NAME


def load_state() -> dict:
    try:
        return json.loads(state_path().read_text("utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2), "utf-8")


def append(state: dict, text: str) -> None:
    f = Path(state["file"])
    f.parent.mkdir(parents=True, exist_ok=True)
    current = f.read_text("utf-8") if f.exists() else ""
    prefix = ("\n" if current.endswith("\n") else "\n\n") if current.strip() else ""
    with f.open("a", encoding="utf-8") as fh:
        fh.write(prefix + text.rstrip() + "\n")


# ---------- formatting ----------

def callout(kind: str, title: str, body: list) -> str:
    lines = [f"> [!{kind}] {title}"]
    lines += [">" if not l else f"> {l}" for l in body]
    return "\n".join(lines)


def user_block(text: str) -> str:
    return f"> [!quote] YOU\n\n{text.strip()}"


def assistant_block(text: str) -> str:
    return f"> [!abstract] CLAUDE\n\n{text.strip()}"


def questions_block(questions: list) -> str:
    out = []
    for q in questions or []:
        body = [l for l in str(q.get("question", "")).split("\n")]
        opts = q.get("options") or []
        if opts:
            body.append("")
            body += [f"{i}. {o.get('label', '')}" for i, o in enumerate(opts, 1)]
        out.append(callout("question", q.get("header") or "Question", body))
    return "\n\n".join(out)


def answers_block(tool_input: dict, tool_response) -> str:
    answers = None
    if isinstance(tool_response, dict):
        answers = tool_response.get("answers")
    if not answers and isinstance(tool_input, dict):
        answers = tool_input.get("answers")
    body = []
    if isinstance(answers, dict) and answers:
        for q, a in answers.items():
            body.append(f"**{q}** → {a}")
    else:
        text = tool_response if isinstance(tool_response, str) else json.dumps(tool_response, ensure_ascii=False)
        body.append(str(text)[:1000])
    return callout("info", "Answer", body)


# ---------- transcript parsing (assistant text between tool calls) ----------

def read_transcript(path: str) -> list:
    entries = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return entries


def text_of(entry: dict) -> str:
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text").strip()
    return ""


def is_real_user_prompt(entry: dict) -> bool:
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isSidechain"):
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
        return False
    t = text_of(entry).lstrip()
    return bool(t) and not t.startswith(("<command-", "<system-reminder", "<local-command", "<task-notification"))


def flush_assistant(state: dict, transcript: str, include_users: bool = False) -> int:
    """Append assistant (and optionally user) text from the transcript not yet logged."""
    logged = set(state.get("logged", []))
    n = 0
    for e in read_transcript(transcript):
        uid = e.get("uuid")
        if not uid or uid in logged or e.get("isSidechain"):
            continue
        if e.get("type") == "assistant":
            t = text_of(e)
            if t:
                append(state, assistant_block(t))
                n += 1
        elif include_users and is_real_user_prompt(e):
            append(state, user_block(text_of(e)))
            n += 1
        logged.add(uid)
    state["logged"] = sorted(logged)
    return n


# ---------- hook entrypoint ----------

def handle_hook(event: dict) -> None:
    state = load_state()
    if not state.get("file") or event.get("agent_id"):
        return  # not linked, or a subagent's event
    name = event.get("hook_event_name")
    transcript = event.get("transcript_path") or ""

    if state.get("backfill") and transcript:
        state["backfill"] = False
        append(state, callout("note", "md-log linked", [f"session `{event.get('session_id', '')}`"]))
        flush_assistant(state, transcript, include_users=True)

    if name == "UserPromptSubmit":
        if transcript:
            flush_assistant(state, transcript)
        prompt = str(event.get("prompt", ""))
        if prompt.strip() and not prompt.lstrip().startswith(("/learn:md-", "/md-log", "/md-unlog")):
            append(state, user_block(prompt))
    elif name == "PreToolUse" and event.get("tool_name") == "AskUserQuestion":
        if transcript:
            flush_assistant(state, transcript)  # lesson text written before the question
        append(state, questions_block((event.get("tool_input") or {}).get("questions")))
    elif name == "PostToolUse" and event.get("tool_name") == "AskUserQuestion":
        append(state, answers_block(event.get("tool_input") or {}, event.get("tool_response")))
    elif name == "Stop":
        n = flush_assistant(state, transcript) if transcript else 0
        last = event.get("last_assistant_message")
        if n == 0 and isinstance(last, str) and last.strip() and last.strip() != state.get("last_stop"):
            append(state, assistant_block(last))  # transcript unreadable: fall back
        if isinstance(last, str):
            state["last_stop"] = last.strip()
    save_state(state)


def main() -> None:
    args = sys.argv[1:]
    cmd = args[0] if args else "status"
    if cmd == "hook":
        try:
            handle_hook(json.load(sys.stdin))
        except Exception as e:  # never break the session
            print(f"md-log: {e}", file=sys.stderr)
        return
    if cmd == "link":
        if len(args) < 2 or not args[1].strip():
            sys.exit("usage: md_log.py link <file.md>")
        f = Path(os.path.expanduser(args[1].strip().strip('"\''))).resolve()
        if f.suffix.lower() != ".md":
            f = f.with_suffix(".md")
        save_state({"file": str(f), "backfill": True, "logged": []})
        print(f"md-log linked → {f}\nThe session so far is backfilled on the next event; new messages append live.")
    elif cmd == "unlink":
        s = load_state()
        save_state({})
        print(f"md-log stopped (was {s.get('file') or 'not linked'}).")
    else:
        s = load_state()
        print(f"md-log → {s['file']}" if s.get("file") else "md-log: not linked. Use /learn:md-log <file.md>.")


if __name__ == "__main__":
    main()
