#!/usr/bin/env python3
"""
The playground — where the seats build, and nothing they build can reach anything.

Daniel, 2026-09-06: "let them go do whatever. open playground and build."

"Whatever" needs a floor under it. Several models writing into the trees the
daemon and the game are running from is not collaboration, it is a race with
no referee — and the canon is explicit that hidden execution and unattended
action are the Silent Order's own signature.

So the seats get a room of their own:

    ~/nova_playground/<session>/<seat>/   what each one wrote
    ~/nova_playground/<session>/TASK.md   what they were asked
    ~/nova_playground/<session>/index.json

Three properties, and they are the whole design:

  **Nothing is executed.** Output is written to disk and read by a human. The
  playground never runs what a model produced, never imports it, and is not on
  any import path. A model that writes `os.system("rm -rf ~")` produces a file
  containing that text and nothing happens.

  **Nothing reaches the live trees.** Every path is built under PLAYGROUND_DIR
  and checked against it before writing. Nova-Cathedral, nova-dm, ~/cathedral
  and the services are outside and stay outside.

  **Every file is attributed.** One directory per seat, never merged. The
  Council rule applies to code as it does to opinions: preserve disagreement,
  and let no model silently rewrite another's contribution.

Stdlib only — the systemd units run /usr/bin/python3.
"""

import json
import re
from datetime import datetime
from pathlib import Path

PLAYGROUND_DIR = Path.home() / "nova_playground"

# A seat writes one file per answer. More than this and it is not building, it
# is spraying — and nobody reads twenty files from a 4B model.
MAX_FILES_PER_SEAT = 5

# Fenced blocks the model emits, as ```lang path/to/file.py … ```
_FENCE = re.compile(
    r"```(?P<lang>[\w+.-]*)[ \t]*(?P<path>[\w./-]*)?\r?\n(?P<body>.*?)```",
    re.S,
)

_EXT = {"python": ".py", "py": ".py", "javascript": ".js", "js": ".js",
        "bash": ".sh", "sh": ".sh", "json": ".json", "yaml": ".yml",
        "markdown": ".md", "md": ".md", "html": ".html", "css": ".css",
        "sql": ".sql", "": ".txt"}


def session_dir(session_id: str, root: Path = None) -> Path:
    return (root or PLAYGROUND_DIR) / session_id


def safe_name(name: str) -> str:
    """A filename that cannot climb out of the seat's directory.

    Models emit paths like `../../etc/passwd` and `/home/daniel/.bashrc` when
    asked for a filename, not usually maliciously — but the difference does not
    matter here, because the result is the same either way.
    """
    name = (name or "").strip().replace("\\", "/")
    name = name.split("/")[-1]                    # basename only, no traversal
    name = re.sub(r"[^\w.-]", "_", name).lstrip(".")
    return name[:64] or "output.txt"


def extract_files(text: str, lang_default: str = "") -> list:
    """Fenced code blocks from a model's answer, as (filename, body).

    Falls back to the whole answer as prose when there are no fences: a seat
    that explains rather than codes has still said something, and discarding it
    would silently lose the contribution.
    """
    out, seen = [], set()
    for i, m in enumerate(_FENCE.finditer(text or ""), 1):
        body = m.group("body")
        if not body.strip():
            continue
        # safe_name() has its own fallback, so ask it only when a path was
        # actually given — otherwise "" comes back as "output.txt", which looks
        # like a real filename and skips the language-extension branch below.
        raw = (m.group("path") or "").strip()
        given = safe_name(raw) if raw else ""
        if not given or "." not in given:
            ext = _EXT.get((m.group("lang") or lang_default).lower(), ".txt")
            given = f"block_{i}{ext}"
        while given in seen:                      # two blocks, one name
            stem, _, ext = given.rpartition(".")
            given = f"{stem}_{i}.{ext}"
        seen.add(given)
        out.append((given, body))
        if len(out) >= MAX_FILES_PER_SEAT:
            break
    if not out and (text or "").strip():
        out.append(("answer.md", text.strip()))
    return out


def write_seat(session_id: str, seat: str, text: str, root: Path = None) -> dict:
    """Write one seat's output into its own directory.

    Returns what was written. Never raises on a bad path: a seat that produces
    something unwritable loses its own contribution, not the round.
    """
    base = (root or PLAYGROUND_DIR).resolve()
    d = (session_dir(session_id, root) / safe_name(seat)).resolve()
    # Belt and braces: even after safe_name, confirm we are still inside.
    if not str(d).startswith(str(base)):
        return {"error": f"refused: {seat} resolved outside the playground"}
    d.mkdir(parents=True, exist_ok=True)

    written = []
    for name, body in extract_files(text):
        try:
            (d / name).write_text(body)
            written.append(name)
        except OSError as e:
            written.append(f"({name}: {e})")
    return {"seat": seat, "dir": str(d), "files": written}


def open_session(task: str, root: Path = None) -> str:
    """Start a build session and record the task."""
    sid = datetime.now().strftime("%Y%m%d-%H%M%S")
    d = session_dir(sid, root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "TASK.md").write_text(
        f"# Playground build — {sid}\n\n{task.strip()}\n\n"
        "---\n\nOne directory per seat. Nothing here has been executed, "
        "reviewed, or merged.\n")
    return sid


def close_session(session_id: str, task: str, results: list, root: Path = None) -> Path:
    """Write the index a human reads to see who built what."""
    d = session_dir(session_id, root)
    (d / "index.json").write_text(json.dumps(
        {"session_id": session_id, "timestamp": datetime.now().isoformat(),
         "task": task, "seats": results, "executed": False, "reviewed": False},
        indent=2))
    return d


def sessions(root: Path = None) -> list:
    """Every build session, newest first."""
    base = root or PLAYGROUND_DIR
    if not base.is_dir():
        return []
    out = []
    for p in sorted(base.glob("*/index.json"), reverse=True):
        try:
            out.append(json.loads(p.read_text()))
        except (OSError, json.JSONDecodeError):
            continue
    return out
