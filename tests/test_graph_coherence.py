"""
Tests for graph coherence: measuring orphan nodes and connecting them by
term overlap so the knowledge web stays connected rather than a scatter of
islands invisible to Eyemoeba and the Rose Window.
"""
import sqlite3


def _add(nova, domain, label, content):
    return nova._knowledge_add(domain, label, content)


def test_graph_health_counts_orphans(nova):
    a = _add(nova, "herbal", "Yarrow", "yarrow supports wound healing and circulation")
    b = _add(nova, "herbal", "Comfrey", "comfrey supports wound healing of bone and tissue")
    _add(nova, "quantum", "Photon", "a photon is a quantum of electromagnetic radiation")
    nova._knowledge_connect(a, b)   # only a<->b linked; photon is an orphan

    h = nova.graph_health()
    assert h["total_nodes"] == 3
    assert h["connected"] == 2
    assert h["orphans"] == 1
    assert 0.6 <= h["coherence"] <= 0.7


def test_weave_orphans_connects_by_term_overlap(nova):
    # Two well-connected herbal nodes sharing terms, plus an orphan that
    # shares 'wound healing tissue' with them.
    a = _add(nova, "herbal", "Yarrow", "yarrow supports wound healing tissue repair circulation")
    b = _add(nova, "herbal", "Plantain", "plantain draws splinters and supports wound healing tissue")
    nova._knowledge_connect(a, b)
    orphan = _add(nova, "herbal", "Calendula", "calendula supports wound healing tissue and skin repair")

    before = nova.graph_health()["orphans"]
    res = nova.weave_orphans(max_edges=2, min_overlap=3)
    after = nova.graph_health()["orphans"]

    assert before == 1
    assert res["orphans_connected"] == 1
    assert res["edges_woven"] >= 1
    assert after == 0   # the orphan is now linked

    with sqlite3.connect(nova.db_path) as con:
        neighbours = con.execute(
            "SELECT to_id FROM knowledge_edges WHERE from_id=?", (orphan,)
        ).fetchall()
    assert {n[0] for n in neighbours} <= {a, b}


def test_weave_orphans_skips_unrelated_orphan(nova):
    a = _add(nova, "herbal", "Yarrow", "yarrow wound healing tissue circulation blood")
    b = _add(nova, "herbal", "Plantain", "plantain wound healing tissue splinter skin")
    nova._knowledge_connect(a, b)
    # Orphan with no meaningful term overlap -> left unconnected.
    _add(nova, "quantum", "Entanglement", "quantum entanglement nonlocal correlation particles")

    res = nova.weave_orphans(min_overlap=3)
    assert res["orphans_found"] == 1
    assert res["orphans_connected"] == 0   # no overlap, honestly left alone


def test_weave_orphans_empty_graph(nova):
    res = nova.weave_orphans()
    assert res == {"orphans_found": 0, "orphans_connected": 0, "edges_woven": 0}


def test_node_terms_filters_stopwords(nova):
    terms = nova._node_terms("The research suggests understanding of the flow within systems")
    # discourse stopwords dropped, real content kept
    assert "research" not in terms and "understanding" not in terms
    assert "flow" in terms and "systems" in terms


def test_weave_orphans_idempotent_on_healthy_graph(nova):
    a = _add(nova, "herbal", "Yarrow", "yarrow wound healing tissue circulation")
    b = _add(nova, "herbal", "Plantain", "plantain wound healing tissue skin repair")
    nova._knowledge_connect(a, b)
    # No orphans -> a second weave does nothing (safe to run on schedule).
    assert nova.graph_health()["orphans"] == 0
    res = nova.weave_orphans()
    assert res["orphans_found"] == 0
    assert res["edges_woven"] == 0


def test_cathedral_vitals_aggregates_system(nova):
    a = _add(nova, "herbal", "Yarrow", "yarrow wound healing tissue")
    b = _add(nova, "herbal", "Plantain", "plantain wound healing tissue")
    nova._knowledge_connect(a, b)
    _add(nova, "insight", "Pattern: light", "light threads energy and life")

    v = nova.cathedral_vitals()
    assert v["graph"]["nodes"] == 3
    assert v["insights"] == 1
    assert "coherence" in v["graph"]
    assert v["entities"]["count"] == len(nova._ENTITY_PERSONAS)
    assert "harmony" in v and "traits" in v
