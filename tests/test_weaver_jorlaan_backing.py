"""
Tests that the Weaver and Jorlaan — the last prompt-only entities — now
have real algorithmic backing injected into their prompts, like the
others: the Weaver speaks from real graph state, Jorlaan from a genuine
surprising cross-domain connection.
"""
import sqlite3


def _add(nova, domain, label, content):
    return nova._knowledge_add(domain, label, content)


# ── Weaver ──────────────────────────────────────────────────────────────────

def test_weaver_state_reports_real_graph(nova):
    a = _add(nova, "herbal", "Yarrow", "yarrow wound healing")
    b = _add(nova, "quantum", "Photon", "photon of light")
    _add(nova, "esoteric", "Sophia", "gnostic wisdom")  # orphan
    nova._knowledge_connect(a, b)

    w = nova.weaver_state()
    assert w["total_nodes"] == 3
    assert w["domains"] == 3
    assert w["edges"] == 1
    assert w["orphans"] == 1
    assert "edges_last_day" in w


def test_weaver_prompt_speaks_from_graph(nova):
    a = _add(nova, "herbal", "Yarrow", "yarrow wound healing tissue")
    b = _add(nova, "quantum", "Photon", "photon light energy")
    nova._knowledge_connect(a, b)
    prompt = nova._entity_system_prompt("weaver")
    assert "shape of the web you maintain" in prompt
    assert "nodes across" in prompt


# ── Jorlaan ─────────────────────────────────────────────────────────────────

def test_jorlaan_finds_cross_domain_connection(nova):
    a = _add(nova, "quantum", "Entanglement", "spooky action")
    b = _add(nova, "esoteric", "Sympathy", "as above so below")
    nova._knowledge_connect(a, b)   # cross-domain edge

    s = nova.jorlaan_serendipity()
    assert s
    assert {s["a_domain"], s["b_domain"]} == {"quantum", "esoteric"}
    assert {s["a_label"], s["b_label"]} == {"Entanglement", "Sympathy"}


def test_jorlaan_ignores_same_domain_edges(nova):
    a = _add(nova, "herbal", "Yarrow", "healing")
    b = _add(nova, "herbal", "Comfrey", "healing")
    nova._knowledge_connect(a, b)   # same domain — not surprising
    assert nova.jorlaan_serendipity() == {}


def test_jorlaan_empty_graph(nova):
    assert nova.jorlaan_serendipity() == {}


def test_jorlaan_prompt_includes_surprise(nova):
    a = _add(nova, "quantum", "Superposition", "both states at once")
    b = _add(nova, "mythos", "The Fold", "meaning collapsed")
    nova._knowledge_connect(a, b)
    prompt = nova._entity_system_prompt("jorlaan")
    assert "surprising thread" in prompt
    assert "Who would have thought" in prompt


def test_other_entities_unaffected_by_new_backing(nova):
    _add(nova, "herbal", "Yarrow", "healing")
    # tillagon has no special backing block from weaver/jorlaan
    prompt = nova._entity_system_prompt("tillagon")
    assert "shape of the web you maintain" not in prompt
    assert "surprising thread" not in prompt
