"""
The Weaver must not weave a filed document's frontmatter into the graph.

A document promoted by the Scribe (type: codex/mythos/research) lands in the
knowledge directory still carrying its YAML block. Weaving it whole puts the
filing metadata into the node's vocabulary, and since every filed document
carries the same keys they would link to each other on metadata rather than
meaning — the same failure as motifs that turned out to be the corpus's own
vocabulary.
"""
import weaver


FILED = """---
date: 2026-09-01
type: codex
status: active
tags: [glyph, observer]
scribe_filed: 2026-09-01T17:28:51
---

The observer glyph governs attention and the return of resonance.
"""


def test_frontmatter_is_stripped_before_weaving():
    body = weaver.strip_frontmatter(FILED)
    assert body.lstrip().startswith("The observer glyph")
    assert "scribe_filed" not in body


def test_filing_metadata_never_reaches_the_vocabulary():
    words = weaver.significant_words(weaver.strip_frontmatter(FILED))
    for leaked in ("scribe", "filed", "status", "active", "codex"):
        assert leaked not in words, f"{leaked} leaked into graph vocabulary"


def test_document_without_frontmatter_is_untouched():
    plain = "# Just a document\n\nNo frontmatter here.\n"
    assert weaver.strip_frontmatter(plain) == plain


def test_malformed_frontmatter_block_is_still_dropped():
    """The Scribe refuses to file these, but if one reaches the directory by
    hand the Weaver should still not put `type: [unclosed` into the graph."""
    bad = "---\ntype: [unclosed\n---\n\nreal body text\n"
    assert weaver.strip_frontmatter(bad).strip() == "real body text"


def test_a_horizontal_rule_is_not_mistaken_for_frontmatter():
    """`---` mid-document is a rule, not a block. Only a leading block counts."""
    doc = "# Title\n\nSome text.\n\n---\n\nMore text.\n"
    assert weaver.strip_frontmatter(doc) == doc
