"""Why Eyemoeba synthesized nothing between 2026-08-09 and 2026-08-26.

Four faults compounding, found by looking at the live graph rather than the
code. Each is pinned below.

  1. The motifs were the corpus's own vocabulary. At a 0.25 ubiquity cap the
     top "cross-domain patterns" were relationships, might, used, world --
     present in a quarter of all nodes because every model-written node
     contains them.
  2. The motif table is upsert-only, so a term that stopped qualifying kept its
     row forever. That made the thresholds decorative: tightening the cap
     changed what was *found* and nothing about what was *listed*.
  3. Evidence was gathered from every domain a motif touched. "relationships"
     spans 49 domains, which built ~19,600 characters of prompt -- about 400
     seconds of reading before a word came back, against a 90s budget.
  4. Nothing remembered the failure, and the ranking is deterministic, so the
     same doomed term was chosen again every sixth cycle for seventeen days.
     The Dream loop had this exact bug (ad660a1); it did not transfer because
     the two loops track different node types.
"""
import pytest


def _add(nova, domain, label, content):
    return nova._knowledge_add(domain, label, content)


def test_a_word_in_a_quarter_of_the_graph_is_not_a_motif(nova):
    """The vocabulary test. "resonance" is in most nodes here, spanning many
    domains -- exactly the shape that used to rank first."""
    for i in range(20):
        _add(nova, f"domain{i % 8}", f"Node {i}",
             "This node discusses resonance among other things")
    for i in range(4):
        _add(nova, f"other{i}", f"Quiet {i}", f"unique padding term{i} zzz{i}")

    terms = {m["term"] for m in nova._eyemoeba_analyze()}
    assert "resonance" not in terms, "a term in most of the graph is its vocabulary"


def test_a_motif_that_stops_qualifying_stops_being_listed(nova):
    """The upsert-only table meant a stale row outlived the rule that made it.

    Without this, tightening a threshold has no effect on what the insight loop
    actually picks, which is how "relationships" stayed top for seventeen days.
    """
    _add(nova, "herbal", "Yarrow", "yarrow carries resonance through the body")
    _add(nova, "quantum", "Photon", "a photon shows resonance between states")
    for i in range(24):
        _add(nova, f"pad{i % 6}", f"Pad {i}", f"unrelated filler sentence {i} qqq{i}")
    nova._eyemoeba_store_motifs(nova._eyemoeba_analyze())
    assert "resonance" in {m["term"] for m in nova.eyemoeba_motifs_list(n=50)}

    # Now flood the graph so "resonance" becomes ubiquitous and is no longer a
    # motif, while "tessellation" takes its place as a real one. Resonance's row
    # still exists -- it must simply stop being listed.
    for i in range(40):
        _add(nova, f"flood{i % 4}", f"Flood {i}", "resonance resonance everywhere now")
    _add(nova, "mathematics", "Penrose", "tessellation covers the plane without gaps")
    _add(nova, "arts", "Alhambra", "tessellation patterns tile the palace walls")
    nova._eyemoeba_store_motifs(nova._eyemoeba_analyze())

    listed = {m["term"] for m in nova.eyemoeba_motifs_list(n=50)}
    assert "tessellation" in listed, "the new scan's motifs are what gets listed"

    assert "resonance" not in {m["term"] for m in nova.eyemoeba_motifs_list(n=50)}
    import sqlite3
    with sqlite3.connect(nova.db_path) as con:
        still_there = con.execute(
            "SELECT COUNT(*) FROM eyemoeba_motifs WHERE term='resonance'").fetchone()[0]
    assert still_there == 1, "the history is kept, only the listing moves on"


def test_evidence_is_capped_so_a_wide_motif_still_fits_the_budget(nova):
    """A motif spanning 30 domains must not build a 30-domain prompt."""
    for i in range(12):
        _add(nova, f"domain{i}", f"Node {i}", "networks appear here as a structure")
    # Enough graph that 12 nodes is under the ubiquity cap.
    for i in range(120):
        _add(nova, f"pad{i % 5}", f"Pad {i}", f"unique padding {i} with words www{i}")
    nova._eyemoeba_store_motifs(nova._eyemoeba_analyze())

    ev = nova._eyemoeba_motif_evidence("networks")
    assert ev, "the motif should be stored"
    assert len(ev["by_domain"]) <= nova._EYEMOEBA_EVIDENCE_DOMAINS
    # The motif is still described as wide; only the shown evidence is capped.
    assert len(ev["domains"]) > nova._EYEMOEBA_EVIDENCE_DOMAINS


def test_a_failed_motif_is_not_chosen_again(nova):
    """The livelock. The ranking is deterministic, so without this the same
    term is picked every cycle forever -- seventeen days, in the real case."""
    _add(nova, "herbal", "Yarrow", "yarrow carries resonance through the body")
    _add(nova, "quantum", "Photon", "a photon shows resonance between states")
    _add(nova, "cosmos", "Pulsar", "a pulsar beats resonance across the void")
    for i in range(30):
        _add(nova, f"pad{i % 6}", f"Pad {i}", f"unrelated filler sentence {i} qqq{i}")
    nova._eyemoeba_store_motifs(nova._eyemoeba_analyze())

    first = nova._top_unexplained_motif()
    assert first, "there should be an unexplained motif to pick"
    assert nova._top_unexplained_motif() == first, "the ranking is deterministic"

    nova._eyemoeba_failed_motifs.add(first)
    assert nova._top_unexplained_motif() != first, "a failed motif must not be retried"


def test_the_failure_set_starts_empty(nova):
    """A restart is a fair moment to try again: the usual cause is a timeout."""
    assert nova._eyemoeba_failed_motifs == set()
