#!/usr/bin/env python3
"""distill_ingest — normalize a source and number its paragraphs (docs/distill.md §8).

  distill_ingest.py <input.txt> <out_dir> --title T --locator URL [--edition E]
                    [--start-line N] [--end-line M]
                    [--redact-from TEXT --redact-to TEXT]

Writes <out_dir>/source/source.md, <out_dir>/source/builder.md and
<out_dir>/manifest.json. Paragraphs are blank-line-separated blocks, numbered
from 1. builder.md is identical to source.md except that the paragraphs from
the one containing --redact-from to the one containing --redact-to are
replaced by a placeholder, so paragraph numbers stay the same in both files.

normalize() is also what the anchor check uses on quotes, so a quote matches
when the two normalize to the same text.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

QUOTES = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "--"}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    for a, b in QUOTES.items():
        text = text.replace(a, b)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)   # join line-break hyphenation
    text = text.replace("_", "")                    # Gutenberg italics markers
    return re.sub(r"\s+", " ", text).strip()


def paragraphs(raw: str) -> list:
    return [normalize(b) for b in re.split(r"\n\s*\n", raw) if b.strip()]


def render(paras: list, redact: range = range(0)) -> str:
    out, i = [], 0
    while i < len(paras):
        if i in redact:
            out.append(f"**¶{redact.start + 1}–{redact.stop}** [redacted for the builder]")
            i = redact.stop
            continue
        out.append(f"**¶{i + 1}** {paras[i]}")
        i += 1
    return "\n\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("out_dir")
    ap.add_argument("--title", required=True)
    ap.add_argument("--locator", required=True)
    ap.add_argument("--edition", default="")
    ap.add_argument("--start-line", type=int, default=1)
    ap.add_argument("--end-line", type=int)
    ap.add_argument("--redact-from")
    ap.add_argument("--redact-to")
    a = ap.parse_args()

    lines = Path(a.input).read_text("utf-8").splitlines()
    paras = paragraphs("\n".join(lines[a.start_line - 1 : a.end_line]))

    redact = range(0)
    if a.redact_from:
        def find(t):
            hits = [i for i, p in enumerate(paras) if normalize(t) in p]
            if len(hits) != 1:
                raise SystemExit(f"redact marker {t!r} matched {len(hits)} paragraphs, need exactly 1")
            return hits[0]
        lo, hi = find(a.redact_from), find(a.redact_to or a.redact_from)
        redact = range(lo, hi + 1)

    out = Path(a.out_dir)
    (out / "source").mkdir(parents=True, exist_ok=True)
    source = render(paras)
    (out / "source" / "source.md").write_text(source, "utf-8")
    (out / "source" / "builder.md").write_text(render(paras, redact), "utf-8")
    manifest = {
        "id": out.name,
        "title": a.title,
        "source": {
            "locator": a.locator,
            "edition": a.edition,
            "lines": [a.start_line, a.end_line],
            "sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "paragraphs": len(paras),
            "redacted_for_builder": [redact.start + 1, redact.stop] if redact else None,
        },
        "mode": "human",
        "version": 1,
        "created": date.today().isoformat(),
        "interface": [],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", "utf-8")
    words = sum(len(p.split()) for p in paras)
    if paras and not paras[-1].rstrip().rstrip('"\')]*').endswith((".", "?", "!", ":")):
        print(f"WARNING: last paragraph doesn't end a sentence — check --end-line: ...{paras[-1][-60:]!r}")
    print(f"{len(paras)} paragraphs, {words} words -> {out}"
          + (f"; redacted ¶{redact.start + 1}–{redact.stop} in builder.md" if redact else ""))


if __name__ == "__main__":
    main()
