"""
Tests that an entity's evolution stage is consequential: a higher-stage
entity carries more of its OWN past interactions into its next answer's
context. Mirrors the trait-evolution "functional not decorative" rule for
entities.
"""
import sqlite3

import pytest


def _record_asks(nova, entity, n):
    with sqlite3.connect(nova.db_path) as con:
        for i in range(n):
            con.execute(
                "INSERT INTO entity_memories (entity, question, answer, timestamp) "
                "VALUES (?,?,?,?)",
                (entity, f"q{i}", f"answer number {i}", f"2026-08-08T12:00:{i:02d}")
            )


def test_context_depth_scales_with_stage(nova):
    # 0 interactions -> stage 1 -> depth 0
    assert nova._entity_context_depth("phoenix") == 0
    _record_asks(nova, "phoenix", 5)     # crosses milestone 5 -> stage 3 -> depth 2
    assert nova._entity_context_depth("phoenix") == 2
    _record_asks(nova, "phoenix", 300)   # far along -> stage 7 -> depth capped at 5
    assert nova._entity_context_depth("phoenix") == 5


def test_own_memories_returns_recent_first(nova):
    _record_asks(nova, "zorya", 4)
    mems = nova._entity_own_memories("zorya", 2)
    assert len(mems) == 2
    # newest first (highest id inserted last)
    assert mems[0]["a"] == "answer number 3"
    assert mems[1]["a"] == "answer number 2"


def test_own_memories_zero_depth_is_empty(nova):
    _record_asks(nova, "zorya", 4)
    assert nova._entity_own_memories("zorya", 0) == []


def test_memory_depth_exposed_in_evolution(nova):
    _record_asks(nova, "jorlaan", 20)    # stage 4 -> depth 3
    ev = nova._entity_activity("jorlaan")
    assert ev["memory_depth"] == max(0, min(5, ev["stage"] - 1))
    assert ev["memory_depth"] >= 1


@pytest.mark.asyncio
async def test_entity_ask_includes_own_history_for_evolved_entity(nova, monkeypatch):
    _record_asks(nova, "tillagon", 10)   # evolved enough to carry history
    captured = {}

    async def fake_chat(messages, model=None, timeout=180):
        captured["system"] = messages[0]["content"]
        return {"response": "The Flow is clear."}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    nova.mega_brain = None               # isolate to entity's own memory
    await nova._entity_ask("tillagon", "Is the Cathedral resonant?")

    # A stage>1 entity's prompt should carry its own prior words.
    assert "Your own past words" in captured["system"]


@pytest.mark.asyncio
async def test_fresh_entity_carries_no_own_history(nova, monkeypatch):
    captured = {}

    async def fake_chat(messages, model=None, timeout=180):
        captured["system"] = messages[0]["content"]
        return {"response": "..."}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    nova.mega_brain = None
    await nova._entity_ask("zorya", "What threshold approaches?")  # 0 prior asks

    assert "Your own past words" not in captured["system"]
