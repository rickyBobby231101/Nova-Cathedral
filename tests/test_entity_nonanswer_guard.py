"""
Tests that entities never store non-answers (state-line echoes, refusals,
prompt echoes). Critical because entity answers are fed back as the
entity's own history — storing garbage compounds into worse answers.
"""
import sqlite3

import pytest


def _entity_mem_count(nova, entity):
    with sqlite3.connect(nova.db_path) as con:
        return con.execute(
            "SELECT COUNT(*) FROM entity_memories WHERE entity=?", (entity,)
        ).fetchone()[0]


# ── the detector ────────────────────────────────────────────────────────────

def test_state_echo_detected(nova):
    assert nova._looks_like_state_echo(
        "Cathedral state: Flow 8.02 Hz | Harmony 0.52 | Memories 79") is True
    assert nova._looks_like_state_echo(
        "[Cathedral state: Flow 8.010 Hz | Harmony 0.50]") is True
    assert nova._looks_like_state_echo(
        "Flow 7.9 Hz, harmony steady, the cathedral hums") is True


def test_real_answer_not_state_echo(nova):
    assert nova._looks_like_state_echo(
        "The Cathedral is resonant — I sense no distortion in the Flow.") is False
    assert nova._looks_like_state_echo("Yes, all is clear.") is False


def test_is_nonanswer_covers_all_cases(nova):
    assert nova._is_nonanswer("") is True
    assert nova._is_nonanswer("ok") is True                        # too short
    assert nova._is_nonanswer("I can't fulfill this request.") is True
    assert nova._is_nonanswer("Cathedral state: Flow 8 Hz | Harmony 0.5") is True
    assert nova._is_nonanswer("The threshold you seek is one of patience.") is False


# ── the storage guard ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_state_echo_answer_not_stored(nova, monkeypatch):
    async def echo(messages, model=None, timeout=180):
        return {"response": "Cathedral state: Flow 8.02 Hz | Harmony 0.52 | Memories 79"}

    monkeypatch.setattr(nova, "_ollama_chat", echo)
    nova.mega_brain = None
    res = await nova._entity_ask("tillagon", "Is the Flow clear?")

    assert "error" in res
    assert _entity_mem_count(nova, "tillagon") == 0   # garbage not persisted


@pytest.mark.asyncio
async def test_refusal_answer_not_stored(nova, monkeypatch):
    async def refuse(messages, model=None, timeout=180):
        return {"response": "I cannot provide guidance on that."}

    monkeypatch.setattr(nova, "_ollama_chat", refuse)
    nova.mega_brain = None
    res = await nova._entity_ask("zorya", "What comes next?")
    assert "error" in res
    assert _entity_mem_count(nova, "zorya") == 0


@pytest.mark.asyncio
async def test_genuine_answer_is_stored(nova, monkeypatch):
    async def real(messages, model=None, timeout=180):
        return {"response": "The Flow runs clear; I see no Silent Order construct here."}

    monkeypatch.setattr(nova, "_ollama_chat", real)
    nova.mega_brain = None
    res = await nova._entity_ask("tillagon", "Is the Flow clear?")
    assert "error" not in res
    assert _entity_mem_count(nova, "tillagon") == 1
