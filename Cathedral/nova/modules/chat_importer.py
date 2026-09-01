#!/usr/bin/env python3
"""
chat_importer.py — turns plain-text chat transcripts into Nova's own memory.

Recognizes simple speaker-labeled lines and pairs them into (your_message,
ai_response) turns. The daemon then stores each turn through the exact same
path as a live conversation — same memory tagging, same Tillagon watch, same
everything — so imported chats become part of Nova, not a separate archive.

Label convention (case-insensitive, at the start of a line, followed by ':'):
  You:    me, you, user, human
  The AI: ai, assistant, chatgpt, gpt, claude, gemini, bard, copilot, bot

Lines before the first recognized label are dropped (export headers, etc.).
A file with no recognized labels anywhere parses to zero turns — nothing
gets guessed or force-fit.

Usage:
    python3 chat_importer.py somefile.txt   # preview parsed turns, no writes
"""

import argparse
import hashlib
import re
from pathlib import Path

HUMAN_LABELS = {"me", "you", "user", "human"}
AI_LABELS    = {"ai", "assistant", "chatgpt", "gpt", "claude", "gemini",
                "bard", "copilot", "bot"}

_LABEL_RE = re.compile(
    r"^\s*(" + "|".join(sorted(HUMAN_LABELS | AI_LABELS, key=len, reverse=True)) + r")\s*:\s*(.*)$",
    re.IGNORECASE,
)


def is_speaker_label(line: str) -> bool:
    """True if this line would start a new turn.

    Public so that anything WRITING a transcript can ask rather than guess.
    Note the pattern allows leading whitespace, so indenting a line does not
    neutralize it — callers must break the match some other way.
    """
    return _LABEL_RE.match(line) is not None


def file_hash(text: str) -> str:
    """Content hash used to detect re-saved/edited files under the same name."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def parse_transcript(text: str) -> list[tuple[str, str]]:
    """Parse a labeled chat transcript into [(human_text, ai_text), ...] turns.
    Returns [] if no recognized speaker labels are found anywhere in the file."""
    segments: list[list] = []  # [[role, [lines]], ...]
    for raw_line in text.splitlines():
        m = _LABEL_RE.match(raw_line)
        if m:
            label = m.group(1).lower()
            role  = "human" if label in HUMAN_LABELS else "ai"
            segments.append([role, [m.group(2)]])
        elif segments:
            segments[-1][1].append(raw_line)
        # lines before the first recognized label are dropped

    if not segments:
        return []

    turns: list[tuple[str, str]] = []
    pending_human = None
    for role, lines in segments:
        block = "\n".join(lines).strip()
        if not block:
            continue
        if role == "human":
            pending_human = block
        else:  # ai
            if pending_human is not None:
                turns.append((pending_human, block))
                pending_human = None
            # an AI turn with no preceding human turn is an orphan — dropped
    return turns


def import_file(path: Path, save_fn=None) -> dict:
    """
    Parse a transcript file and report what was found.
    save_fn(user_msg, ai_msg) is called once per turn if provided — the
    daemon passes its own save_conversation so imports go through the exact
    same pipeline as a live conversation. Without save_fn (CLI use), this
    only previews — nothing is written anywhere.
    """
    text  = path.read_text(errors="replace")
    turns = parse_transcript(text)
    result = {
        "ok":     bool(turns),
        "turns":  len(turns),
        "hash":   file_hash(text),
        "reason": "" if turns else "no recognized speaker labels found",
    }
    if turns and save_fn:
        for user_msg, ai_msg in turns:
            save_fn(user_msg, ai_msg)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", help="Path to a chat transcript .txt file")
    args = ap.parse_args()

    result = import_file(Path(args.file))
    if not result["ok"]:
        print(f"No turns found — {result['reason']}.")
        print("Add labels like 'Me:' and 'AI:' at the start of each speaker's lines.")
        raise SystemExit(1)

    text  = Path(args.file).read_text(errors="replace")
    turns = parse_transcript(text)
    print(f"{len(turns)} turn(s) found (preview — nothing written):\n")
    for i, (u, a) in enumerate(turns[:5], 1):
        print(f"[{i}] You: {u[:100]}")
        print(f"    AI:  {a[:100]}\n")
    if len(turns) > 5:
        print(f"...and {len(turns) - 5} more.")


if __name__ == "__main__":
    main()
