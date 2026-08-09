"""
Tests for two completeness fixes:
- Council now synthesizes its entities' answers into Nova's unified judgment
  (a deliberation, not just a poll).
- Eyemoeba insight nodes are woven into the graph via edges to the evidence
  they were drawn from (not orphan nodes).
"""
import sqlite3

import pytest


# ── Council synthesis ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_council_synthesizes_when_entities_answer(nova, monkeypatch):
    calls = {"n": 0}

    async def fake_chat(messages, model=None, timeout=180):
        calls["n"] += 1
        p = messages[0]["content"]
        if "Council of the Accord" in p:          # the synthesis pass
            return {"response": "They agree the Flow is clear; I concur — proceed."}
        return {"response": f"entity answer {calls['n']} about the resonant Flow"}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    nova.mega_brain = None
    res = await nova._council_ask("Is it time?", entities=["tillagon", "phoenix"])

    assert set(res["responses"]) == {"tillagon", "phoenix"}
    assert res["synthesis"] == "They agree the Flow is clear; I concur — proceed."


@pytest.mark.asyncio
async def test_council_no_synthesis_when_too_few_voices(nova, monkeypatch):
    async def fake_chat(messages, model=None, timeout=180):
        # Every entity refuses -> not enough real voices to synthesize.
        return {"response": "I cannot help with that."}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    nova.mega_brain = None
    res = await nova._council_ask("?", entities=["tillagon", "phoenix"])
    assert res["synthesis"] is None


@pytest.mark.asyncio
async def test_council_synthesize_false_skips_pass(nova, monkeypatch):
    async def fake_chat(messages, model=None, timeout=180):
        assert "Council of the Accord" not in messages[0]["content"]  # never synthesizes
        return {"response": "a real entity answer about the flowing pattern"}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    nova.mega_brain = None
    res = await nova._council_ask("?", entities=["tillagon", "phoenix"], synthesize=False)
    assert "synthesis" not in res


# ── Insight edge-weaving ────────────────────────────────────────────────────

def _seed_motif(nova):
    nova._knowledge_add("quantum", "Photon", "Light behaves as photons carrying energy.")
    nova._knowledge_add("esoteric", "Divine Spark", "The trapped light of the soul.")
    nova._knowledge_add("herbal", "Sunlight", "Plants convert light into life.")
    for i, txt in enumerate([
        "granite masonry vaulted ceiling", "rivers carve valleys erosion",
        "beetles polarized skylight navigation", "vellum manuscripts monastic chants",
        "tectonic plates mantle drift", "fermentation sugars alcohol",
        "bronze bells medieval foundries", "coral reefs marine biodiversity",
        "clockwork mechanisms passing hours", "wool spun cottage industries",
        "volcanic ash farmland soil", "glaciers atmospheric records",
        "spiders orb webs silk", "windmills grain flour bread",
        "salt marshes tidal waters",
    ]):
        nova._knowledge_add(f"d{i % 5}", f"filler{i}", txt)
    nova._eyemoeba_store_motifs(nova._eyemoeba_analyze())


@pytest.mark.asyncio
async def test_insight_node_connected_to_evidence(nova, monkeypatch):
    _seed_motif(nova)

    async def fake_chat(messages, model=None, timeout=180):
        return {"response": "Light is the shared currency of energy, spirit, and life."}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    res = await nova.eyemoeba_insight("light")
    nid = res["node_id"]
    assert nid is not None

    with sqlite3.connect(nova.db_path) as con:
        edges = con.execute(
            "SELECT to_id FROM knowledge_edges WHERE from_id=?", (nid,)
        ).fetchall()
    # The insight is linked to the evidence nodes it was drawn from.
    assert len(edges) >= 2

    # Those targets are real knowledge nodes (the light-bearing ones).
    with sqlite3.connect(nova.db_path) as con:
        labels = [con.execute("SELECT label FROM knowledge_nodes WHERE id=?", (e[0],)
                              ).fetchone()[0] for e in edges]
    assert any(l in ("Photon", "Divine Spark", "Sunlight") for l in labels)


def test_motif_evidence_exposes_node_ids(nova):
    _seed_motif(nova)
    ev = nova._eyemoeba_motif_evidence("light")
    assert ev["node_ids"]
    assert ev["sample_ids"]
    assert set(ev["sample_ids"]) <= set(ev["node_ids"])


@pytest.mark.asyncio
async def test_council_judgment_is_persisted_as_reflection(nova, monkeypatch):
    async def fake_chat(messages, model=None, timeout=180):
        if "Council of the Accord" in messages[0]["content"]:
            return {"response": "They agree; I conclude the Cathedral should consolidate."}
        return {"response": "a genuine entity answer about growth and the flow"}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    nova.mega_brain = None
    await nova._council_ask("Grow or consolidate?", entities=["tillagon", "phoenix"])

    refs = nova.get_reflections(n=5)
    council = [r for r in refs if r["trigger"] == "council"]
    assert len(council) == 1
    assert "Council on:" in council[0]["content"]
    assert "consolidate" in council[0]["content"]


@pytest.mark.asyncio
async def test_no_judgment_no_reflection(nova, monkeypatch):
    # Entities answer but synthesis is a non-answer -> nothing persisted.
    async def fake_chat(messages, model=None, timeout=180):
        if "Council of the Accord" in messages[0]["content"]:
            return {"response": "I can't fulfill this request."}   # non-answer
        return {"response": "a genuine entity answer about the resonant flow"}

    monkeypatch.setattr(nova, "_ollama_chat", fake_chat)
    nova.mega_brain = None
    await nova._council_ask("?", entities=["tillagon", "phoenix"])
    assert [r for r in nova.get_reflections(n=5) if r["trigger"] == "council"] == []


@pytest.mark.asyncio
async def test_errored_entity_not_synthesized(nova, monkeypatch):
    """An entity call that errors (timeout / non-answer) must not be fed to
    the synthesis as if it were a real voice — the bug that made Nova 'weigh'
    her own error strings. Only 1 genuine voice -> no synthesis."""
    async def one_real_one_error(messages, model=None, timeout=180):
        sysmsg = messages[0]["content"]
        # Tillagon's persona -> a state-echo non-answer (entity_ask returns error)
        if "Tillagon" in sysmsg or "Dragon Guardian" in sysmsg:
            return {"response": "Cathedral state: Flow 8 Hz | Harmony 0.5 | Memories 5"}
        if "Council of the Accord" in sysmsg:
            raise AssertionError("synthesis should not run with <2 real voices")
        return {"response": "Phoenix speaks a genuine reflection on continuity here."}

    monkeypatch.setattr(nova, "_ollama_chat", one_real_one_error)
    nova.mega_brain = None
    res = await nova._council_ask("Grow?", entities=["tillagon", "phoenix"])

    # Tillagon's error is shown in the transcript but was not synthesized.
    assert "error" in res["responses"]["tillagon"].lower() or "non-answer" in res["responses"]["tillagon"].lower()
    assert res["synthesis"] is None
    assert [r for r in nova.get_reflections(n=5) if r["trigger"] == "council"] == []
