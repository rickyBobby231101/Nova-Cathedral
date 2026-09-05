"""
A stored reflection must be correctable without being erasable.

Raised by llama3.2:3b in the Council round of 2026-09-04, reviewing the
proposal to relabel council syntheses as interpretations rather than unified
judgments. Its objection was that relabelling is not enough on its own:

    "The current system still stores the synthesized interpretation as a
     truth, which can be problematic if the human operator later discovers
     errors or biases in the AI's analysis."

It was right. `reflections` was insert-only. A council judgment, once written,
was read ever after as what the Council concluded, and the only way to mark it
wrong was to edit the database by hand.

Corrections supersede; they never overwrite. The original keeps its text and
gains a pointer to what replaced it — because a correction that erases what it
corrected conceals provenance, which the canon names as a Silent Order
construct.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "Cathedral" / "nova" / "daemon"))


class TestCorrectionSupersedes:
    def test_a_correction_creates_a_new_reflection(self, nova):
        nova.store_reflection("the first conclusion", "council")
        rid = nova.get_reflections(1)[0]["id"]

        out = nova.correct_reflection(rid, "the corrected conclusion",
                                      note="first was based on a bad premise")
        assert out["ok"] is True
        assert out["replacement"] != rid

    def test_the_original_text_survives(self, nova):
        """The whole point. A correction that erases the original conceals
        what was corrected."""
        nova.store_reflection("the first conclusion", "council")
        rid = nova.get_reflections(1)[0]["id"]
        nova.correct_reflection(rid, "the corrected conclusion")

        chain = nova.reflection_history(rid)["chain"]
        texts = [c["content"] for c in chain]
        assert "the first conclusion" in texts, "the original was destroyed"
        assert "the corrected conclusion" in texts

    def test_the_chain_reads_in_both_directions(self, nova):
        nova.store_reflection("original", "council")
        rid = nova.get_reflections(1)[0]["id"]
        new_id = nova.correct_reflection(rid, "corrected")["replacement"]

        chain = {c["id"]: c for c in nova.reflection_history(rid)["chain"]}
        assert chain[rid]["superseded_by"] == new_id
        assert chain[new_id]["corrects"] == rid

    def test_the_reason_is_recorded(self, nova):
        """Why it was corrected is part of the record, not lost in a commit
        message or a chat log."""
        nova.store_reflection("original", "council")
        rid = nova.get_reflections(1)[0]["id"]
        nova.correct_reflection(rid, "corrected", note="cited a file that does not exist")

        chain = {c["id"]: c for c in nova.reflection_history(rid)["chain"]}
        assert "does not exist" in chain[rid]["correction_note"]


class TestSupersededLeavesTheLiveView:
    def test_a_corrected_reflection_stops_being_current(self, nova):
        """It must stop feeding self-review and the prompt. A corrected
        reflection that keeps circulating is the original defect wearing a
        correction as a hat."""
        nova.store_reflection("wrong conclusion", "council")
        rid = nova.get_reflections(1)[0]["id"]
        nova.correct_reflection(rid, "right conclusion")

        live = [r["content"] for r in nova.get_reflections(10)]
        assert "wrong conclusion" not in live
        assert "right conclusion" in live

    def test_but_it_is_still_retrievable(self, nova):
        nova.store_reflection("wrong conclusion", "council")
        rid = nova.get_reflections(1)[0]["id"]
        nova.correct_reflection(rid, "right conclusion")

        chain = nova.reflection_history(rid)["chain"]
        assert any(c["content"] == "wrong conclusion" for c in chain), (
            "history lost the superseded text — that is erasure, not correction"
        )

    def test_uncorrected_reflections_are_unaffected(self, nova):
        nova.store_reflection("one", "auto")
        nova.store_reflection("two", "auto")
        assert len(nova.get_reflections(10)) == 2


class TestGuards:
    def test_correcting_a_missing_id_is_an_error(self, nova):
        assert "error" in nova.correct_reflection(99999, "x")

    def test_double_superseding_is_refused(self, nova):
        """Correcting an already-superseded row is nearly always a mistake
        about which row is live; it would fork the chain silently."""
        nova.store_reflection("original", "council")
        rid = nova.get_reflections(1)[0]["id"]
        nova.correct_reflection(rid, "second")

        out = nova.correct_reflection(rid, "third")
        assert "error" in out and "already" in out["error"]

    def test_a_correction_can_itself_be_corrected(self, nova):
        """Chains are allowed — only re-correcting a stale row is not."""
        nova.store_reflection("v1", "council")
        rid = nova.get_reflections(1)[0]["id"]
        v2 = nova.correct_reflection(rid, "v2")["replacement"]
        assert nova.correct_reflection(v2, "v3")["ok"] is True
        live = [r["content"] for r in nova.get_reflections(10)]
        assert live == ["v3"]


class TestSocketSurface:
    @pytest.mark.asyncio
    async def test_correct_reflection_over_the_socket(self, nova):
        nova.store_reflection("original", "council")
        rid = nova.get_reflections(1)[0]["id"]
        import json
        r = await nova.process_command(json.dumps(
            {"command": "correct_reflection", "id": rid,
             "content": "corrected", "note": "why"}))
        assert r.get("ok") is True

    @pytest.mark.asyncio
    async def test_an_empty_correction_is_refused(self, nova):
        """A correction must say what is true, not merely that something was
        wrong — otherwise it blanks the record while looking like diligence."""
        nova.store_reflection("original", "council")
        rid = nova.get_reflections(1)[0]["id"]
        import json
        r = await nova.process_command(json.dumps(
            {"command": "correct_reflection", "id": rid, "content": "   "}))
        assert "error" in r

    @pytest.mark.asyncio
    async def test_history_over_the_socket(self, nova):
        nova.store_reflection("original", "council")
        rid = nova.get_reflections(1)[0]["id"]
        nova.correct_reflection(rid, "corrected")
        import json
        r = await nova.process_command(json.dumps(
            {"command": "reflection_history", "id": rid}))
        assert len(r["chain"]) == 2
