"""
Tests for Eyemoeba's real pattern recognition (cross-domain motif
detection over the knowledge graph). This replaced a placeholder that
hashed the runtime directory's file count — these tests pin down that the
new analysis finds genuine cross-domain terms and ignores noise.
"""
import json
import sqlite3


def _add_node(nova, domain, label, content):
    return nova._knowledge_add(domain, label, content)


def _seed_graph(nova):
    # "resonance" spans three domains — a real motif.
    _add_node(nova, "herbal", "Yarrow", "Yarrow promotes resonance in the body's healing systems")
    _add_node(nova, "quantum", "Entanglement", "Quantum entanglement shows resonance between distant particles")
    _add_node(nova, "consciousness", "Meditation", "Deep meditation produces resonance across brain regions")
    # "photosynthesis" appears only in one domain — not a motif.
    _add_node(nova, "herbal", "Chlorophyll", "Chlorophyll drives photosynthesis in green plants")
    # Enough filler that a 3-node motif stays under the 25% ubiquity cap
    # (3/14 ≈ 21%) — mirrors a realistically-sized graph rather than a
    # toy one where every real motif looks ubiquitous.
    _add_node(nova, "cathedral", "Spire", "The spire reaches upward toward aspiration")
    _add_node(nova, "cathedral", "Nave", "The nave holds the central gathering space")
    _add_node(nova, "cathedral", "Crypt", "The crypt keeps compressed old memory below")
    _add_node(nova, "mythos", "Tillagon", "Tillagon watches for distortion constructs")
    _add_node(nova, "mythos", "Phoenix", "Phoenix guards continuity across cycles")
    _add_node(nova, "arts", "Fresco", "Frescoes decorate sacred ceilings with pigment")
    _add_node(nova, "arts", "Stained", "Stained glass windows scatter colored light")
    _add_node(nova, "cosmos", "Nebula", "Nebulae birth stars from collapsing dust")
    _add_node(nova, "cosmos", "Pulsar", "Pulsars sweep lighthouse beams of radiation")
    _add_node(nova, "wellbeing", "Sleep", "Sleep consolidates learning overnight")


def test_cross_domain_term_is_detected(nova):
    _seed_graph(nova)
    motifs = nova._eyemoeba_analyze()
    terms = {m["term"] for m in motifs}
    assert "resonance" in terms
    resonance = next(m for m in motifs if m["term"] == "resonance")
    assert set(resonance["domains"]) == {"herbal", "quantum", "consciousness"}
    assert resonance["node_count"] == 3


def test_single_domain_term_is_not_a_motif(nova):
    _seed_graph(nova)
    terms = {m["term"] for m in nova._eyemoeba_analyze()}
    assert "photosynthesis" not in terms


def test_stopwords_never_become_motifs(nova):
    _seed_graph(nova)
    terms = {m["term"] for m in nova._eyemoeba_analyze()}
    assert not terms & nova._EYEMOEBA_STOPWORDS


def test_ubiquitous_term_is_capped(nova):
    # A term in every single node carries no cross-domain signal.
    for i, domain in enumerate(["herbal", "quantum", "consciousness", "cathedral", "mythos"]):
        _add_node(nova, domain, f"node{i}", "the cathedral hums everywhere always")
    terms = {m["term"] for m in nova._eyemoeba_analyze()}
    assert "cathedral" not in terms
    assert "everywhere" not in terms


def test_empty_graph_yields_nothing(nova):
    assert nova._eyemoeba_analyze() == []


def test_store_motifs_returns_only_new(nova):
    _seed_graph(nova)
    motifs = nova._eyemoeba_analyze()
    first = nova._eyemoeba_store_motifs(motifs)
    assert len(first) == len(motifs)
    second = nova._eyemoeba_store_motifs(motifs)
    assert second == []  # everything already known


def test_weave_edges_links_motif_nodes(nova):
    _seed_graph(nova)
    motif = next(m for m in nova._eyemoeba_analyze() if m["term"] == "resonance")
    added = nova._eyemoeba_weave_edges(motif)
    assert added == 2  # first node linked to the other two

    with sqlite3.connect(nova.db_path) as con:
        edges = con.execute(
            "SELECT from_id, to_id FROM knowledge_edges"
        ).fetchall()
    assert len(edges) == 2
    froms = {e[0] for e in edges}
    assert froms == {motif["node_ids"][0]}

    # Weaving again must not duplicate (UNIQUE constraint honored).
    assert nova._eyemoeba_weave_edges(motif) == 0


def test_motifs_list_orders_by_domain_span(nova):
    _seed_graph(nova)
    # "healing" also spans 2 domains if we add a second node using it.
    _add_node(nova, "consciousness", "Breathwork", "Breathwork supports healing through rhythm")
    nova._eyemoeba_store_motifs(nova._eyemoeba_analyze())
    listed = nova.eyemoeba_motifs_list()
    assert listed, "expected stored motifs"
    spans = [len(m["domains"]) for m in listed]
    assert spans == sorted(spans, reverse=True)


def test_entity_prompt_includes_real_motifs(nova):
    _seed_graph(nova)
    nova._eyemoeba_store_motifs(nova._eyemoeba_analyze())
    prompt = nova._entity_system_prompt("eyemoeba")
    assert "resonance" in prompt
    assert "real analysis, not imagination" in prompt


def test_other_entity_prompts_unaffected(nova):
    _seed_graph(nova)
    nova._eyemoeba_store_motifs(nova._eyemoeba_analyze())
    prompt = nova._entity_system_prompt("tillagon")
    assert "real analysis, not imagination" not in prompt
