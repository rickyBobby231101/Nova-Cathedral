"""
Tests for the Weaver's node-relabeling pass — reads node content, writes
clean titles. The LLM is mocked so these are fast and deterministic; they
pin down the batching, parsing, and that only in-batch IDs get updated.
"""
import sqlite3

import pytest


def _add(nova, domain, label, content):
    return nova._knowledge_add(domain, label, content)


def _label_of(nova, nid):
    with sqlite3.connect(nova.db_path) as con:
        return con.execute(
            "SELECT label FROM knowledge_nodes WHERE id=?", (nid,)
        ).fetchone()[0]


@pytest.mark.asyncio
async def test_relabels_nodes_from_llm_output(nova, monkeypatch):
    a = _add(nova, "research", "Cathedral's walls", "Load-bearing masonry and flying buttresses.")
    b = _add(nova, "research", "quantum thing", "Superposition and entanglement in physics.")

    async def fake_chat(messages, model=None, timeout=180):
        return {"response": f"{a}: Gothic Masonry\n{b}: Quantum Superposition\n"}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)

    res = await nova._weaver_relabel("research")
    assert res["relabeled"] == 2
    assert _label_of(nova, a) == "Gothic Masonry"
    assert _label_of(nova, b) == "Quantum Superposition"


@pytest.mark.asyncio
async def test_ignores_ids_outside_batch(nova, monkeypatch):
    a = _add(nova, "research", "orig", "some content about stars")

    async def fake_chat(messages, model=None, timeout=180):
        # 999 isn't a real node — must be ignored, not crash or mis-write.
        return {"response": f"999: Bogus\n{a}: Stellar Astronomy"}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    res = await nova._weaver_relabel("research")
    assert res["relabeled"] == 1
    assert _label_of(nova, a) == "Stellar Astronomy"


@pytest.mark.asyncio
async def test_strips_markdown_and_punctuation(nova, monkeypatch):
    a = _add(nova, "research", "x", "content")

    async def fake_chat(messages, model=None, timeout=180):
        return {"response": f'{a}: "**Sacred Geometry**"'}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    await nova._weaver_relabel("research")
    assert _label_of(nova, a) == "Sacred Geometry"


@pytest.mark.asyncio
async def test_domain_filter_scopes_relabeling(nova, monkeypatch):
    r = _add(nova, "research", "r", "research content")
    h = _add(nova, "herbal", "Yarrow", "herbal content")

    async def fake_chat(messages, model=None, timeout=180):
        # Weaver only ever sees research-domain ids; reply for r only.
        return {"response": f"{r}: Renamed Research"}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    await nova._weaver_relabel("research")
    assert _label_of(nova, r) == "Renamed Research"
    assert _label_of(nova, h) == "Yarrow"  # untouched


@pytest.mark.asyncio
async def test_empty_domain_returns_zero(nova, monkeypatch):
    async def fake_chat(messages, model=None, timeout=180):
        return {"response": ""}
    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    res = await nova._weaver_relabel("nonexistent")
    assert res["relabeled"] == 0


@pytest.mark.asyncio
async def test_batches_multiple_llm_calls(nova, monkeypatch):
    ids = [_add(nova, "research", f"n{i}", f"content {i}") for i in range(5)]
    calls = {"n": 0}

    async def fake_chat(messages, model=None, timeout=180):
        calls["n"] += 1
        # Echo back a clean title for whatever ids appear in the prompt.
        import re
        found = re.findall(r"\[(\d+)\]", messages[0]["content"])
        return {"response": "\n".join(f"{i}: Title {i}" for i in found)}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    res = await nova._weaver_relabel("research", batch_size=2)
    assert res["relabeled"] == 5
    assert calls["n"] == 3  # 2+2+1 across three batches
    assert _label_of(nova, ids[0]) == f"Title {ids[0]}"
