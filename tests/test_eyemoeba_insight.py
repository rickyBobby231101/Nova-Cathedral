"""
Tests for Eyemoeba's generative insight synthesis: taking a real
cross-domain motif and producing a grounded note on what the recurrence
means, stored as a new 'insight' knowledge node. LLM is mocked.
"""
import sqlite3

import pytest


def _add(nova, domain, label, content):
    return nova._knowledge_add(domain, label, content)


def _seed_motif(nova):
    # "light" recurs across three domains — build real nodes, then scan+store
    # so eyemoeba_motifs has a genuine entry to reason over.
    _add(nova, "quantum", "Photon", "Light behaves as photons carrying energy.")
    _add(nova, "esoteric", "Divine Spark", "The trapped light of the soul seeks release.")
    _add(nova, "herbal", "Sunlight", "Plants convert light into life through the leaf.")
    # Enough distinct filler that light's 3 nodes stay under the ubiquity cap,
    # tightened to 0.12 on 2026-08-26 (3/28 ≈ 11%); each filler uses unique
    # words so it makes no motif of its own.
    fillers = [
        "granite masonry supports the vaulted ceiling",
        "rivers carve valleys over millennia of erosion",
        "beetles navigate using polarized skylight cues",
        "vellum manuscripts recorded monastic chants",
        "tectonic plates drift across the mantle slowly",
        "fermentation transforms sugars into alcohol",
        "migratory birds follow magnetic field lines",
        "bronze bells were cast in medieval foundries",
        "coral reefs host vast marine biodiversity",
        "clockwork mechanisms measure passing hours",
        "wool was spun and dyed in cottage industries",
        "volcanic ash enriches surrounding farmland soil",
        "glaciers store ancient atmospheric records",
        "spiders weave orb webs from protein silk",
        "windmills ground grain into flour for bread",
        "lightning heats air into a plasma channel",
        "salt marshes filter coastal tidal waters daily",
        "obsidian blades were knapped from volcanic glass",
        "lichens colonise bare rock before mosses arrive",
        "aqueducts carried fresh springwater into cities",
        "cicadas emerge on prime-numbered year cycles",
        "peat bogs preserve leather and wooden artefacts",
        "trade winds drove sailing routes across oceans",
        "quartz veins signal hydrothermal mineral deposits",
        "beeswax sealed documents against tampering",
    ]
    for i, text in enumerate(fillers):
        _add(nova, f"d{i % 5}", f"filler{i}", text)
    nova._eyemoeba_store_motifs(nova._eyemoeba_analyze())


@pytest.mark.asyncio
async def test_insight_synthesized_and_stored(nova, monkeypatch):
    _seed_motif(nova)

    async def fake_chat(messages, model=None, timeout=180):
        # Confirm the real evidence reached the prompt.
        p = messages[0]["content"]
        assert "quantum" in p and "esoteric" in p
        return {"response": "Light is the shared currency of energy, spirit, and life."}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    res = await nova.eyemoeba_insight("light")

    assert "error" not in res
    assert set(res["domains"]) >= {"quantum", "esoteric", "herbal"}
    assert res["node_id"] is not None

    # It became a real 'insight' node in the graph.
    with sqlite3.connect(nova.db_path) as con:
        row = con.execute(
            "SELECT domain, source, content FROM knowledge_nodes WHERE id=?",
            (res["node_id"],)
        ).fetchone()
    assert row[0] == "insight"
    assert row[1] == "eyemoeba"
    assert "shared currency" in row[2]


@pytest.mark.asyncio
async def test_insight_unknown_motif_errors(nova, monkeypatch):
    async def fake_chat(messages, model=None, timeout=180):
        return {"response": "should not be called"}
    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    res = await nova.eyemoeba_insight("nonexistent-term")
    assert "error" in res
    assert "no stored motif" in res["error"]


@pytest.mark.asyncio
async def test_insight_store_false_does_not_persist(nova, monkeypatch):
    _seed_motif(nova)

    async def fake_chat(messages, model=None, timeout=180):
        return {"response": "A grounded connection across the domains."}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)

    with sqlite3.connect(nova.db_path) as con:
        before = con.execute(
            "SELECT COUNT(*) FROM knowledge_nodes WHERE domain='insight'"
        ).fetchone()[0]

    res = await nova.eyemoeba_insight("light", store=False)
    assert res["node_id"] is None
    assert res["insight"]

    with sqlite3.connect(nova.db_path) as con:
        after = con.execute(
            "SELECT COUNT(*) FROM knowledge_nodes WHERE domain='insight'"
        ).fetchone()[0]
    assert after == before


@pytest.mark.asyncio
async def test_insight_rejects_refusal(nova, monkeypatch):
    _seed_motif(nova)

    async def fake_chat(messages, model=None, timeout=180):
        return {"response": "I'm sorry, but I can't help with that request."}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    res = await nova.eyemoeba_insight("light")
    assert "error" in res
    assert "refusal" in res["error"] or "echo" in res["error"]


def test_motif_evidence_groups_by_domain(nova):
    _seed_motif(nova)
    ev = nova._eyemoeba_motif_evidence("light")
    assert ev["term"] == "light"
    assert "quantum" in ev["by_domain"]
    # each domain bucket holds sample nodes with labels + snippets
    sample = ev["by_domain"]["quantum"][0]
    assert "label" in sample and "snippet" in sample


# ── Auto-insight scheduling helpers ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_motif_has_insight_tracks_stored_insights(nova, monkeypatch):
    _seed_motif(nova)
    assert nova._motif_has_insight("light") is False

    async def fake_chat(messages, model=None, timeout=180):
        return {"response": "Light threads energy, spirit, and life together."}
    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    await nova.eyemoeba_insight("light")

    assert nova._motif_has_insight("light") is True


@pytest.mark.asyncio
async def test_top_unexplained_motif_skips_already_explained(nova, monkeypatch):
    _seed_motif(nova)
    first = nova._top_unexplained_motif()
    assert first is not None

    async def fake_chat(messages, model=None, timeout=180):
        return {"response": "A grounded connection."}
    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    await nova.eyemoeba_insight(first)

    # After explaining it, the top-unexplained pick must move on (or be None).
    assert nova._top_unexplained_motif() != first


@pytest.mark.asyncio
async def test_insights_list_returns_stored_newest_first(nova, monkeypatch):
    _seed_motif(nova)
    assert nova.eyemoeba_insights_list() == []

    async def fake_chat(messages, model=None, timeout=180):
        return {"response": "A grounded connection across domains."}
    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    await nova.eyemoeba_insight("light")

    listed = nova.eyemoeba_insights_list()
    assert len(listed) == 1
    assert listed[0]["label"].startswith("Pattern: light")
    assert "grounded connection" in listed[0]["insight"]
