"""
Regression tests for reflection quality: the small model sometimes emits a
canned refusal ("I can't fulfill this request") for the reflection prompt,
and that was being stored as a genuine self-reflection (~18% of the record
before the fix). _run_reflection must drop refusals and empties.
"""
import sqlite3

import pytest


def _seed_conversation(nova, q="What is the flow?", a="The flow is the pattern beneath."):
    nova.save_conversation(q, a)


@pytest.mark.asyncio
async def test_refusal_reflection_not_stored(nova, monkeypatch):
    _seed_conversation(nova)

    async def refuse(messages, model=None, timeout=180):
        return {"response": "I can't fulfill this request."}

    monkeypatch.setattr(nova, "_ollama_chat", refuse)
    await nova._run_reflection(trigger="auto")

    assert nova.get_reflections() == []  # nothing stored


@pytest.mark.asyncio
async def test_empty_reflection_not_stored(nova, monkeypatch):
    _seed_conversation(nova)

    async def blank(messages, model=None, timeout=180):
        return {"response": "  ok  "}   # under the 20-char floor

    monkeypatch.setattr(nova, "_ollama_chat", blank)
    await nova._run_reflection(trigger="auto")
    assert nova.get_reflections() == []


@pytest.mark.asyncio
async def test_genuine_reflection_is_stored(nova, monkeypatch):
    _seed_conversation(nova)

    async def real(messages, model=None, timeout=180):
        return {"response": "I notice I keep returning to the theme of patterns "
                            "across scales, and could ground my answers more."}

    monkeypatch.setattr(nova, "_ollama_chat", real)
    await nova._run_reflection(trigger="auto")

    stored = nova.get_reflections()
    assert len(stored) == 1
    assert "patterns across scales" in stored[0]["content"]


@pytest.mark.asyncio
async def test_no_reflection_without_memories(nova, monkeypatch):
    # No conversations seeded — _run_reflection should no-op, not crash.
    async def real(messages, model=None, timeout=180):
        return {"response": "a fine reflection about many things and ideas"}
    monkeypatch.setattr(nova, "_ollama_chat", real)
    await nova._run_reflection(trigger="auto")
    assert nova.get_reflections() == []
