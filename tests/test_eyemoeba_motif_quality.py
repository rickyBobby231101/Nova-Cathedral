"""
Eyemoeba must stop rather than descend into filler.

The motif list is ordered by strength. Once the strong terms are explained,
walking further down guarantees a result about the weakest term available —
and each synthesis costs real time and then joins the corpus, so its
vocabulary feeds the next scan. The live graph on 2026-09-01 held insight
nodes titled "Pattern: crucial", "Pattern: ourselves" and "Pattern: make".
"""
import pytest


def _add(nova, domain, label, content):
    return nova._knowledge_add(domain, label, content)


def test_evaluative_filler_is_not_a_motif(nova):
    """These are the corpus praising itself, not a pattern in it."""
    for w in ("crucial", "ourselves", "effective", "unique", "particularly",
              "incorporating", "nuanced", "leading"):
        assert w in nova._EYEMOEBA_STOPWORDS, f"{w} would still rank as a motif"


def test_the_words_this_files_own_docstring_names_are_filtered(nova):
    """"make" was named in the stopword list's third-pass comment as an example
    of what it was filtering, and then not added — the live graph still held a
    "Pattern: make" insight node on 2026-09-03, next to "Pattern: solid".

    A comment describing intent is not the same as the intent being
    implemented, and nothing was checking the two against each other.
    """
    for w in ("make", "solid", "crucial", "ourselves"):
        assert w in nova._EYEMOEBA_STOPWORDS, f"{w} would still rank as a motif"


def test_subject_matter_is_still_allowed_through(nova):
    """The stopword passes must not eat the actual subjects of the corpus."""
    for w in ("harmony", "fractal", "network", "mechanics", "language",
              "behavior", "resonance"):
        assert w not in nova._EYEMOEBA_STOPWORDS, f"{w} was wrongly filtered"


def test_synthesis_stops_instead_of_descending(nova):
    """Once everything within the depth is spent, the answer is None — not
    the next weakest term."""
    for i in range(nova._EYEMOEBA_MOTIF_DEPTH + 8):
        for d in ("alpha", "beta", "gamma"):
            _add(nova, d, f"{d} {i}", f"a sentence carrying motif{i:02d} here")
    for i in range(40):
        _add(nova, f"pad{i % 6}", f"Pad {i}", f"unrelated filler qqq{i}")
    nova._eyemoeba_store_motifs(nova._eyemoeba_analyze())

    seen = set()
    while True:
        term = nova._top_unexplained_motif()
        if term is None:
            break
        assert term not in seen, "the same term came back twice"
        seen.add(term)
        nova._eyemoeba_failed_motifs.add(term)
        assert len(seen) <= nova._EYEMOEBA_MOTIF_DEPTH, "descended past the floor"

    assert nova._top_unexplained_motif() is None


def test_the_floor_is_not_deeper_than_the_listing(nova):
    """A depth above the list length would silently reinstate the old walk."""
    assert nova._EYEMOEBA_MOTIF_DEPTH <= 25
