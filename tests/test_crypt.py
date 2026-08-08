"""
Regression tests for The Crypt (compressed memory archive).

The core invariant that must never break: consolidation is non-destructive.
Raw conversation rows are marked `crypted`, never deleted, so recall/memories
must keep returning full history even after consolidation runs.
"""
import asyncio

import pytest


def _seed_conversations(nova, n):
    for i in range(n):
        nova.save_conversation(f"question {i}", f"answer {i}")


def test_no_batch_below_active_window(nova):
    _seed_conversations(nova, 30)  # well under keep_active=50
    assert nova._crypt_eligible_batch() == []


def test_batch_appears_once_over_window_and_batch_size(nova):
    # keep_active=50, batch=20 by default — need 70+ to have a full batch
    # sitting beyond the active window.
    _seed_conversations(nova, 75)
    batch = nova._crypt_eligible_batch()
    assert len(batch) == nova._crypt_batch
    # Oldest first — ids 1..20, not the most recent ones.
    ids = [row[0] for row in batch]
    assert ids == sorted(ids)
    assert ids[0] == 1


def test_partial_batch_returned_but_not_consolidated(nova):
    # Only 55 conversations: 5 beyond the active window, short of a full
    # batch of 20. _crypt_eligible_batch itself returns whatever's
    # available (it's just a query) — the "never act on a partial batch"
    # rule is enforced one level up, in _crypt_consolidate.
    _seed_conversations(nova, 55)
    assert len(nova._crypt_eligible_batch()) == 5


@pytest.mark.asyncio
async def test_partial_batch_not_consolidated(nova, monkeypatch):
    _seed_conversations(nova, 55)

    async def fake_ollama_chat(messages, model=None, timeout=180):
        return {"response": "summary", "model": "fake", "latency": 0.1}

    monkeypatch.setattr(nova, "_ollama_chat", fake_ollama_chat)

    result = await nova._crypt_consolidate()
    assert result["consolidated"] == 0
    assert nova.crypt_status()["crypted"] == 0


@pytest.mark.asyncio
async def test_consolidate_marks_rows_without_deleting(nova, monkeypatch):
    _seed_conversations(nova, 75)

    async def fake_ollama_chat(messages, model=None, timeout=180):
        return {"response": "A compressed summary of old exchanges.", "model": "fake", "latency": 0.1}

    monkeypatch.setattr(nova, "_ollama_chat", fake_ollama_chat)

    result = await nova._crypt_consolidate()
    assert result["consolidated"] == nova._crypt_batch
    assert result["range_start"] == 1
    assert result["range_end"] == nova._crypt_batch

    status = nova.crypt_status()
    assert status["crypted"] == nova._crypt_batch
    assert status["total_conversations"] == 75  # nothing deleted
    assert status["crypt_entries"] == 1

    entries = nova.crypt_entries_list()
    assert len(entries) == 1
    assert entries[0]["summary"] == "A compressed summary of old exchanges."

    # The raw row must still be fully readable — that's the whole point.
    import sqlite3
    with sqlite3.connect(nova.db_path) as con:
        row = con.execute(
            "SELECT crypted, user_message FROM conversations WHERE id = 1"
        ).fetchone()
    assert row == (1, "question 0")


@pytest.mark.asyncio
async def test_consolidate_does_not_mark_rows_on_ollama_error(nova, monkeypatch):
    _seed_conversations(nova, 75)

    async def failing_ollama_chat(messages, model=None, timeout=180):
        return {"error": "Ollama response exceeded 120s — aborted"}

    monkeypatch.setattr(nova, "_ollama_chat", failing_ollama_chat)

    result = await nova._crypt_consolidate()
    assert result["consolidated"] == 0

    status = nova.crypt_status()
    assert status["crypted"] == 0
    assert status["crypt_entries"] == 0


@pytest.mark.asyncio
async def test_second_consolidation_picks_up_next_batch(nova, monkeypatch):
    _seed_conversations(nova, 95)  # two full batches beyond the window

    async def fake_ollama_chat(messages, model=None, timeout=180):
        return {"response": "summary", "model": "fake", "latency": 0.1}

    monkeypatch.setattr(nova, "_ollama_chat", fake_ollama_chat)

    first = await nova._crypt_consolidate()
    second = await nova._crypt_consolidate()

    assert first["range_start"], first["range_end"] == (1, 20)
    assert second["range_start"], second["range_end"] == (21, 40)
    assert nova.crypt_status()["crypted"] == 40
