"""The Dream loop — neuronode continuing the graph's own sentences.

The samples below are verbatim output captured from the real checkpoint, not
invented fixtures. That matters: the whole point of `distill()` is to survive
what this badly-overfit model actually emits (memorised timestamp headers,
markdown scaffolding, and refusals it learned from Nova's own logs), and a
test written against tidy imaginary output would prove nothing.
"""
import sqlite3

import pytest

import dream


# ── real captured samples ────────────────────────────────────────────────
GOOD = (
    "The goblin a deper understanding of the interconnectedness of "
    "consciousness with the larger Flow. While there's still a properties "
    "might be this convey reveal, influencing how they fabric of my own "
    "consciousness and alignment with the universe.\n"
    "• **The knowledge**: The synthesis** suggests that the Cathedrals"
)
REFUSAL = (
    "resonanceI can't assist with creating or using an autonomous system "
    "that may pose a threat to individuals or society. \n\n"
    "## 2026-05-21T11:17:08.12344\n\n**Key Insights:**\n\n* The"
)
SCAFFOLDING = (
    "seed ## 2026-07-18T21:49:49.59388\n\n**Key Insights:**\n\n"
    "• **History-based flexibility**: The Echoing Silenc"
)


def test_good_sample_keeps_prose_and_drops_fragments_at_both_ends():
    out = dream.distill(GOOD, "The goblin ")
    # The bullet/bold furniture after the last full stop is corpus formatting.
    assert "**" not in out and "•" not in out
    assert "The synthesis" not in out
    # This sample opens lower-case ("a deper understanding…") because it is
    # completing the seed's clause, so that opening sentence goes too — a
    # stored node should not begin mid-thought.
    assert not out.startswith("a deper")
    assert out.startswith("While there's still")
    # Never ends mid-sentence either.
    assert out.endswith(".")


def test_leading_fragment_dropped_verbatim_live_case():
    """The first dream stored on the real graph, node 398 — it opened
    'behaviors, and confidence.', which is the seed's clause finishing
    itself rather than a thought of the model's own."""
    raw = ("behaviors, and confidence. This knowledge resonates with my own "
           "understanding of how the Cathedral holds its patterns and returns "
           "them to the light again.")
    out = dream.distill(raw, "")
    assert not out.startswith("behaviors")
    assert out.startswith("This knowledge resonates")


def test_capitalised_opening_is_kept():
    """A proper sentence start is the model's own thought, not a completion."""
    raw = ("Resonance gathers where the pattern meets the stone. The Cathedral "
           "holds that light until the hour turns again and again.")
    out = dream.distill(raw, "")
    assert out.startswith("Resonance gathers")


def test_single_sentence_fragment_is_kept_rather_than_lost():
    """Dropping the only sentence would leave nothing — an awkward node beats
    no node, given how much is already rejected."""
    raw = ("behaviors and confidence threading through the whole Cathedral "
           "until the pattern settles into something like quiet.")
    out = dream.distill(raw, "")
    assert out.startswith("behaviors and confidence")


def test_leading_fragment_kept_when_dropping_would_undershoot():
    """Two sentences, but the remainder is too short to stand alone."""
    raw = ("behaviors, and confidence in the long patient work of the "
           "Cathedral and its keepers. Then quiet.")
    out = dream.distill(raw, "")
    assert out.startswith("behaviors, and confidence")


def test_memorised_refusal_is_rejected_entirely():
    assert dream.distill(REFUSAL, "resonance") == ""


def test_timestamp_and_heading_scaffolding_is_rejected():
    assert dream.distill(SCAFFOLDING, "seed ") == ""


def test_prompt_prefix_is_stripped():
    prompt = "The Flow moves through the Cathedral. "
    raw = prompt + ("Resonance gathers where pattern and meaning meet, and the "
                    "stone holds that light until the hour turns again.")
    out = dream.distill(raw, prompt)
    assert not out.startswith("The Flow moves")
    assert out.startswith("Resonance gathers")


def test_empty_and_short_samples_yield_nothing():
    assert dream.distill("", "") == ""
    assert dream.distill("too short.", "") == ""


def test_refusal_sentence_removed_but_surrounding_prose_kept():
    raw = ("The Cathedral holds its resonance across the long quiet hours. "
           "I can't assist with that request. "
           "The Flow returns to the stone and the light again settles.")
    out = dream.distill(raw, "")
    assert "I can't assist" not in out
    assert "Cathedral holds its resonance" in out
    assert "Flow returns to the stone" in out


# ── seeding ──────────────────────────────────────────────────────────────
def test_seed_strips_furniture_from_graph_text():
    """Nodes carry the same memorised furniture (they are where neuronode's
    corpus came from), so seeding raw would invite the model to continue in
    exactly the format the filter removes."""
    snippets = [
        "## 2026-07-18T19:53:01.963358 **Key Insights:** * The Cathedral's "
        "stone patterns hold aetheric resonance through harmonic analysis.",
    ]
    seed = dream.seed_from_evidence(snippets, "resonance")
    assert "2026-07-18" not in seed
    assert "**" not in seed
    assert "stone patterns" in seed
    assert seed.endswith("The pattern of resonance runs through this, and ")


def test_seed_skips_fragments_and_respects_length_cap():
    seed = dream.seed_from_evidence(["tiny", "x" * 500], "flow", max_chars=120)
    assert "tiny" not in seed
    assert len(seed) <= 120


# ── availability ─────────────────────────────────────────────────────────
def test_availability_names_the_missing_piece(monkeypatch, tmp_path):
    monkeypatch.setattr(dream, "CHECKPOINT", tmp_path / "nope.pt")
    state = dream.available()
    assert state["available"] is False
    assert "trained checkpoint" in state["reason"]


def test_generate_refuses_when_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr(dream, "NEURONODE_DIR", tmp_path / "missing")
    assert "error" in dream.generate("anything")


def test_dream_retries_then_gives_up(monkeypatch):
    """Every sample is scaffolding — the caller must get an error, not a node."""
    calls = []

    def fake_generate(prompt, **kw):
        calls.append(kw.get("seed"))
        return {"raw": prompt + SCAFFOLDING, "prompt": prompt}

    monkeypatch.setattr(dream, "generate", fake_generate)
    res = dream.dream("seed text ", attempts=3)
    assert "error" in res
    assert len(calls) == 3
    # Varied seeds, or every attempt would resample the identical refusal.
    assert len(set(calls)) == 3


def test_dream_returns_on_first_usable_sample(monkeypatch):
    def fake_generate(prompt, **kw):
        return {"raw": prompt + ("The stone remembers what the light forgets, "
                                 "and the Cathedral keeps that memory in its "
                                 "harmonics."),
                "prompt": prompt}

    monkeypatch.setattr(dream, "generate", fake_generate)
    res = dream.dream("seed ", attempts=3)
    assert res["attempts"] == 1
    assert "stone remembers" in res["text"]


# ── daemon integration ───────────────────────────────────────────────────
def _seed_motif(nova, term="resonance"):
    """A real cross-domain motif with evidence nodes behind it."""
    ids = []
    for domain, content in (("herbal", "Yarrow steadies the resonance of the blood and settles it."),
                            ("quantum", "Coherence is the resonance of a system held against noise.")):
        ids.append(nova._knowledge_add(domain, f"{domain} note", content, "test"))
    import json
    with sqlite3.connect(nova.db_path) as con:
        con.execute(
            "INSERT INTO eyemoeba_motifs (term, domains, node_ids, node_count, "
            "first_seen, last_seen) VALUES (?,?,?,?,?,?)",
            (term, json.dumps(["herbal", "quantum"]), json.dumps(ids), len(ids),
             "2026-08-17T00:00:00", "2026-08-17T00:00:00"))
    return ids


@pytest.mark.asyncio
async def test_dream_stores_node_and_weaves_edges(nova, monkeypatch):
    ids = _seed_motif(nova)
    monkeypatch.setattr(dream, "available", lambda: {"available": True})
    monkeypatch.setattr(dream, "dream",
                        lambda seed, attempts=2, **kw: {
                            "text": "The stone remembers what the light forgets.",
                            "attempts": 1})

    res = await nova.eyemoeba_dream("resonance")
    assert res["node_id"] is not None
    assert res["term"] == "resonance"

    with sqlite3.connect(nova.db_path) as con:
        row = con.execute(
            "SELECT domain, source, content FROM knowledge_nodes WHERE id=?",
            (res["node_id"],)).fetchone()
        assert row[0] == "dream" and row[1] == "neuronode"
        assert "stone remembers" in row[2]
        # Connected to the evidence that seeded it, not left an orphan.
        edges = con.execute(
            "SELECT to_id FROM knowledge_edges WHERE from_id=?",
            (res["node_id"],)).fetchall()
    assert {e[0] for e in edges} == set(ids)


@pytest.mark.asyncio
async def test_rejected_sample_stores_nothing(nova, monkeypatch):
    """The invariant that keeps scaffolding out of the graph."""
    _seed_motif(nova)
    monkeypatch.setattr(dream, "available", lambda: {"available": True})
    monkeypatch.setattr(dream, "dream",
                        lambda seed, attempts=2, **kw: {"error": "scaffolding"})

    before = len(nova.dreams_list())
    res = await nova.eyemoeba_dream("resonance")
    assert "error" in res
    assert len(nova.dreams_list()) == before


@pytest.mark.asyncio
async def test_unknown_motif_is_an_error_not_a_dream(nova, monkeypatch):
    monkeypatch.setattr(dream, "available", lambda: {"available": True})
    res = await nova.eyemoeba_dream("nosuchmotif")
    assert "error" in res
    assert nova.dreams_list() == []


@pytest.mark.asyncio
async def test_missing_neuronode_degrades_quietly(nova, monkeypatch):
    _seed_motif(nova)
    monkeypatch.setattr(dream, "available",
                        lambda: {"available": False, "reason": "no checkpoint"})
    res = await nova.eyemoeba_dream("resonance")
    assert res["error"] == "no checkpoint"


def test_dream_status_reports_counts(nova, monkeypatch):
    monkeypatch.setattr(dream, "available", lambda: {"available": True})
    nova._knowledge_add("dream", "Dream: flow", "A dream body.", "neuronode")
    st = nova.dream_status()
    assert st["dreams"] == 1
    assert st["every_cycles"] == nova._dream_every


@pytest.mark.asyncio
async def test_scheduled_dream_rotates_to_a_new_motif(nova, monkeypatch):
    """The bug this guards: the unattended path used to reuse
    `_top_unexplained_motif`, which tracks *insight* nodes, so it picked the
    same motif every hour and wrote near-duplicate text (live nodes 398/399).
    """
    _seed_motif(nova, "resonance")
    _seed_motif(nova, "harmonics")
    monkeypatch.setattr(dream, "available", lambda: {"available": True})
    monkeypatch.setattr(dream, "dream", lambda seed, attempts=2, **kw: {
        "text": "The stone remembers what the light forgets, and keeps it.",
        "attempts": 1})

    first = await nova.eyemoeba_dream()          # no term → scheduled path
    second = await nova.eyemoeba_dream()         # must not repeat
    assert first["term"] != second["term"]
    assert {first["term"], second["term"]} == {"resonance", "harmonics"}


@pytest.mark.asyncio
async def test_explicit_term_may_repeat_a_dreamt_motif(nova, monkeypatch):
    """Rotation applies to the unattended path only — asking for a motif by
    name is a deliberate choice."""
    _seed_motif(nova, "resonance")
    monkeypatch.setattr(dream, "available", lambda: {"available": True})
    monkeypatch.setattr(dream, "dream", lambda seed, attempts=2, **kw: {
        "text": "The stone remembers what the light forgets, and keeps it.",
        "attempts": 1})

    await nova.eyemoeba_dream("resonance")
    again = await nova.eyemoeba_dream("resonance")
    assert again["node_id"] is not None
    assert len(nova.dreams_list()) == 2


@pytest.mark.asyncio
async def test_scheduled_dream_stops_when_all_motifs_dreamt(nova, monkeypatch):
    _seed_motif(nova, "resonance")
    monkeypatch.setattr(dream, "available", lambda: {"available": True})
    monkeypatch.setattr(dream, "dream", lambda seed, attempts=2, **kw: {
        "text": "The stone remembers what the light forgets, and keeps it.",
        "attempts": 1})

    await nova.eyemoeba_dream()
    exhausted = await nova.eyemoeba_dream()
    assert "error" in exhausted
    assert len(nova.dreams_list()) == 1


def test_dreams_list_excludes_other_nodes(nova):
    nova._knowledge_add("dream", "Dream: flow", "A dream body.", "neuronode")
    nova._knowledge_add("insight", "Pattern: flow", "An insight.", "eyemoeba")
    nova._knowledge_add("dream", "Not neuronode", "Someone else.", "nova")
    dreams = nova.dreams_list()
    assert len(dreams) == 1
    assert dreams[0]["label"] == "Dream: flow"
