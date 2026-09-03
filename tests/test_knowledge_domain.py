"""
No node may enter the graph with a blank domain.

Twelve reached the live graph before this guard. They render as
"Pattern: neural across , Artificial Intelligence", and the motif scan had to
grow a special case to skip them — a blank field creating downstream
workarounds instead of being refused at the door.

The original hole: `d.get("domain", "general")`. A .get default fires only
when the key is missing, so an explicit "" passed straight through.
"""


def test_blank_domain_is_normalized(nova):
    for blank in ("", "   ", None):
        nid = nova._knowledge_add(blank, "A label", "some content")
        assert _domain_of(nova, nid) == nova.DEFAULT_DOMAIN


def test_a_real_domain_is_untouched(nova):
    nid = nova._knowledge_add("herbal", "Yarrow", "content")
    assert _domain_of(nova, nid) == "herbal"


def test_surrounding_whitespace_is_trimmed(nova):
    nid = nova._knowledge_add("  cosmos  ", "Pulsar", "content")
    assert _domain_of(nova, nid) == "cosmos"


def test_no_blank_domains_can_accumulate(nova):
    import sqlite3
    for d in ("", "  ", None, "herbal"):
        nova._knowledge_add(d, "L", "C")
    with sqlite3.connect(nova.db_path) as con:
        blanks = con.execute(
            "SELECT COUNT(*) FROM knowledge_nodes WHERE domain='' OR domain IS NULL"
        ).fetchone()[0]
    assert blanks == 0


def _domain_of(nova, nid):
    import sqlite3
    with sqlite3.connect(nova.db_path) as con:
        return con.execute(
            "SELECT domain FROM knowledge_nodes WHERE id=?", (nid,)).fetchone()[0]
