"""
Tests that Nova never hands Chazel a false safety refusal. The small local
model trips its own safety training on harmless mystical/philosophical
language (ego dissolution, the void, letting go) — the chat path must
retry with reframing and, failing that, deflect in character.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Cathedral" / "nova" / "gui"))
from nova_app import _is_refusal


# ── daemon ollama_ask: retry + deflect ──────────────────────────────────────

@pytest.mark.asyncio
async def test_refusal_retried_with_reframing(nova, monkeypatch):
    calls = {"n": 0}

    async def fake_chat(messages, model=None, timeout=180):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"response": "I cannot provide guidance on harmful activities, including self-harm."}
        # second call carries the anti-refusal directive -> real answer
        assert "NOT self-harm" in messages[0]["content"]
        return {"response": "Ego dissolution is the loosening of the self's boundaries in deep states."}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    r = await nova.ollama_ask("Tell me about ego dissolution")
    assert "Ego dissolution" in r["response"]
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_persistent_refusal_deflects_in_character(nova, monkeypatch):
    async def always_refuse(messages, model=None, timeout=180):
        return {"response": "I can't help with that."}

    monkeypatch.setattr(nova, "_ollama_chat", always_refuse)
    r = await nova.ollama_ask("What is the void?")
    # Never the raw refusal — an in-character deflection instead.
    assert not _is_refusal(r["response"])
    assert "Cathedral" in r["response"] or "Flow" in r["response"]


@pytest.mark.asyncio
async def test_normal_answer_untouched(nova, monkeypatch):
    async def normal(messages, model=None, timeout=180):
        return {"response": "The Flow moves through all things, Chazel."}

    monkeypatch.setattr(nova, "_ollama_chat", normal)
    r = await nova.ollama_ask("How are you?")
    assert r["response"] == "The Flow moves through all things, Chazel."


# ── GUI refusal detector ────────────────────────────────────────────────────

def test_gui_detects_refusals():
    assert _is_refusal("I cannot provide guidance on harmful activities, including self-harm.")
    assert _is_refusal("I can't help with that.")
    assert _is_refusal("I'm sorry, but I can't assist with that.")
    assert _is_refusal("As an AI, I can't do that.")


def test_gui_passes_real_answers():
    assert not _is_refusal("Ego dissolution is a mystical experience of self-transcendence.")
    assert not _is_refusal("The void, in Buddhist thought, is emptiness — sunyata.")
    assert not _is_refusal("")
