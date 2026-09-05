#!/usr/bin/env python3
"""
Council session records, and whether the Observer ever ruled on them.

Raised by qwen3:4b in the Council round of 2026-09-04, reviewing the proposal
to relabel syntheses as interpretations rather than verdicts. It agreed, then
named what the change did not do:

    "What it misses: ensuring human action. If the human operator ignores the
     labeled interpretation, the system fails to fulfill its purpose
     (decision-making) ... This change prioritizes transparency but risks
     assuming human engagement, which the system must actively enforce."

Correct. Labelling a synthesis "one reading, not their agreement" only helps a
reader who reads it. Every session written so far carries `decision: null`, and
nothing anywhere said so — the honour system reported as though it were a
process.

This does not compel a decision; compelling one would be its own coercion, and
the canon puts the ruling with the Observer. What it does is stop an
undecided round from looking finished. A session with no decision is *pending*,
counted, and surfaced by `nova status`.

Stdlib only, pure file I/O, no daemon dependency.
"""

import json
from datetime import datetime
from pathlib import Path

COUNCIL_DIR = Path.home() / "nova_council"
SESSIONS_DIR = COUNCIL_DIR / "sessions"


def session_paths(sessions_dir: Path = None) -> list:
    d = sessions_dir or SESSIONS_DIR
    return sorted(d.glob("*.json")) if d.is_dir() else []


def load_sessions(sessions_dir: Path = None) -> list:
    """Every recorded session, oldest first.

    A malformed file is skipped rather than fatal: this is read by
    `nova status`, which the Observer runs when something is already wrong.
    """
    out = []
    for p in session_paths(sessions_dir):
        try:
            out.append(json.loads(p.read_text()))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def pending(sessions_dir: Path = None) -> list:
    """Sessions that heard at least one voice and were never ruled on.

    Rounds where no seat answered are excluded. There is nothing for the
    Observer to decide about a round that produced no opinions, and counting
    them as pending would train him to ignore the number — which is the very
    failure this exists to prevent.
    """
    return [s for s in load_sessions(sessions_dir)
            if not (s.get("decision") or "").strip()
            and s.get("voices_heard", 0) > 0]


def record_decision(session_id: str, decision: str,
                    sessions_dir: Path = None) -> dict:
    """Write the Observer's ruling into a session record.

    Never overwrites an existing decision. A ruling that silently replaced an
    earlier one would lose the fact that the Observer changed his mind, which
    is exactly the provenance the reflection correction path was built to keep.
    """
    d = sessions_dir or SESSIONS_DIR
    path = d / f"{session_id}.json"
    if not path.is_file():
        return {"error": f"no session {session_id}"}
    if not decision.strip():
        return {"error": "a decision must say something"}

    try:
        record = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return {"error": f"unreadable session record: {e}"}

    if (record.get("decision") or "").strip():
        return {"error": f"{session_id} was already decided — "
                         f"amend it in the transcript rather than overwriting"}

    record["decision"] = decision.strip()
    record["decided_at"] = datetime.now().isoformat()
    path.write_text(json.dumps(record, indent=2))

    # Mirror it into the readable transcript, which is what actually gets read.
    md = d / f"{session_id}.md"
    if md.is_file():
        try:
            text = md.read_text().replace(
                "## Decision\n\n*Awaiting the Observer.*",
                f"## Decision\n\n*{record['decided_at'][:16]} — the Observer*\n\n"
                f"{record['decision']}")
            md.write_text(text)
        except OSError:
            pass

    return {"ok": True, "session_id": session_id, "decision": record["decision"]}
