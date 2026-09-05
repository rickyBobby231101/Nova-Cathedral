"""
An undecided Council round must not look finished.

Raised by qwen3:4b in the round of 2026-09-04, reviewing the proposal to
relabel syntheses as interpretations:

    "What it misses: ensuring human action. If the human operator ignores the
     labeled interpretation, the system fails to fulfill its purpose ...
     This change prioritizes transparency but risks assuming human engagement."

It was right. Every session written up to that point carried `decision: null`
and nothing anywhere said so — an honour system reported as a process.

What this does NOT do is compel a decision. Compelling one would be its own
coercion, and the canon puts the ruling with the Observer. It makes the absence
of one visible and counted.
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULES = REPO_ROOT / "Cathedral" / "nova" / "modules"
if str(MODULES) not in sys.path:
    sys.path.insert(0, str(MODULES))

import council_log


def _session(d: Path, sid: str, voices: int = 2, decision=None):
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sid}.json").write_text(json.dumps({
        "session_id": sid, "timestamp": "2026-09-05T00:00:00",
        "request": "a question", "context_used": False,
        "seats": [], "voices_heard": voices, "decision": decision}))
    (d / f"{sid}.md").write_text(
        f"# Council — {sid}\n\n## Decision\n\n*Awaiting the Observer.*\n")
    return d / f"{sid}.json"


class TestPending:
    def test_an_undecided_round_is_pending(self, tmp_path):
        _session(tmp_path, "s1")
        assert [s["session_id"] for s in council_log.pending(tmp_path)] == ["s1"]

    def test_a_decided_round_is_not(self, tmp_path):
        _session(tmp_path, "s1", decision="we ship it")
        assert council_log.pending(tmp_path) == []

    def test_whitespace_is_not_a_decision(self, tmp_path):
        _session(tmp_path, "s1", decision="   ")
        assert len(council_log.pending(tmp_path)) == 1

    def test_a_round_nobody_answered_is_not_pending(self, tmp_path):
        """There is nothing to decide about a round that produced no opinions.
        Counting them would train the Observer to ignore the number, which is
        the failure this exists to prevent."""
        _session(tmp_path, "silent", voices=0)
        assert council_log.pending(tmp_path) == []

    def test_a_malformed_record_is_skipped_not_fatal(self, tmp_path):
        _session(tmp_path, "good")
        (tmp_path / "broken.json").write_text("{not json")
        assert len(council_log.load_sessions(tmp_path)) == 1

    def test_no_sessions_directory_is_empty_not_fatal(self, tmp_path):
        assert council_log.pending(tmp_path / "nope") == []


class TestRecordingADecision:
    def test_a_decision_is_written_and_timestamped(self, tmp_path):
        _session(tmp_path, "s1")
        out = council_log.record_decision("s1", "adopt llama's finding", tmp_path)
        assert out["ok"] is True

        rec = json.loads((tmp_path / "s1.json").read_text())
        assert rec["decision"] == "adopt llama's finding"
        assert rec["decided_at"]

    def test_it_reaches_the_readable_transcript(self, tmp_path):
        """The .md is what actually gets read. A decision recorded only in JSON
        is a decision nobody sees."""
        _session(tmp_path, "s1")
        council_log.record_decision("s1", "adopt it", tmp_path)
        md = (tmp_path / "s1.md").read_text()
        assert "Awaiting the Observer" not in md
        assert "adopt it" in md

    def test_an_existing_decision_is_never_overwritten(self, tmp_path):
        """A ruling that silently replaced an earlier one would lose the fact
        that the Observer changed his mind — the same provenance the reflection
        correction path exists to keep."""
        _session(tmp_path, "s1", decision="first ruling")
        out = council_log.record_decision("s1", "second ruling", tmp_path)
        assert "error" in out and "already decided" in out["error"]
        assert json.loads((tmp_path / "s1.json").read_text())["decision"] == "first ruling"

    def test_an_empty_decision_is_refused(self, tmp_path):
        _session(tmp_path, "s1")
        assert "error" in council_log.record_decision("s1", "   ", tmp_path)
        assert len(council_log.pending(tmp_path)) == 1

    def test_an_unknown_session_is_an_error(self, tmp_path):
        assert "error" in council_log.record_decision("nope", "x", tmp_path)

    def test_deciding_clears_it_from_pending(self, tmp_path):
        _session(tmp_path, "s1")
        _session(tmp_path, "s2")
        council_log.record_decision("s1", "done", tmp_path)
        assert [s["session_id"] for s in council_log.pending(tmp_path)] == ["s2"]


class TestNoCoercion:
    def test_nothing_here_makes_a_decision_on_its_own(self, tmp_path):
        """The module reports and records; it never rules. Reading pending
        sessions must not mutate them."""
        _session(tmp_path, "s1")
        before = (tmp_path / "s1.json").read_text()
        council_log.pending(tmp_path)
        council_log.load_sessions(tmp_path)
        assert (tmp_path / "s1.json").read_text() == before
