"""
Tests for the Scribe — frontmatter-driven filing.

The safety properties are the point of most of these: a document with no
frontmatter must be untouchable (the whole existing knowledge corpus has
none), an unknown type must never be guessed at, and a second run must not
undo or duplicate the first.
"""
import pytest

import scribe as sc


@pytest.fixture
def tree(tmp_path, monkeypatch):
    """A throwaway cathedral tree with the Scribe pointed at it."""
    cath = tmp_path / "cathedral"
    root = cath / "scribe"
    inbox = root / "inbox"
    knowledge = cath / "knowledge"
    inbox.mkdir(parents=True)
    knowledge.mkdir(parents=True)

    monkeypatch.setattr(sc, "HOME", tmp_path)
    monkeypatch.setattr(sc, "SCRIBE_ROOT", root)
    monkeypatch.setattr(sc, "INBOX", inbox)
    monkeypatch.setattr(sc, "KNOWLEDGE_DIR", knowledge)
    monkeypatch.setattr(sc, "INDEX_PATH", root / "INDEX.md")
    return {"root": root, "inbox": inbox, "knowledge": knowledge, "cath": cath}


def _drop(tree, name, frontmatter, body=""):
    p = tree["inbox"] / name
    p.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return p


def test_files_system_log_into_logs(tree):
    _drop(tree, "log.md", "type: system_log\ntags: [test]", "# Log\n")
    s = sc.organize()
    assert s["filed"] == 1
    assert not (tree["inbox"] / "log.md").exists()
    assert (tree["root"] / "logs" / "log.md").exists()


def test_answers_the_write_back_token(tree):
    _drop(tree, "log.md", "type: system_log",
          "Action required.\n\n> [NOVA_CONFIRMATION_PENDING]...\n")
    sc.organize()
    out = (tree["root"] / "logs" / "log.md").read_text()
    assert "NOVA_CONFIRMATION_PENDING" not in out
    assert "NOVA CONFIRMED" in out
    assert "filed to" in out


def test_file_without_frontmatter_is_untouchable(tree):
    """The existing knowledge corpus has no frontmatter. It must be invisible."""
    plain = tree["inbox"] / "plain.md"
    plain.write_text("# Just a document\n\nNo frontmatter here.\n", encoding="utf-8")
    before = plain.read_text()

    s = sc.organize()
    assert s["filed"] == 0
    assert s["skipped_no_frontmatter"] == 1
    assert plain.exists()
    assert plain.read_text() == before


def test_malformed_frontmatter_is_treated_as_none(tree):
    bad = tree["inbox"] / "bad.md"
    bad.write_text("---\ntype: [unclosed\n---\n\nbody\n", encoding="utf-8")
    s = sc.organize()
    assert s["skipped_no_frontmatter"] == 1
    assert bad.exists()


def test_unknown_type_is_reported_never_guessed(tree):
    _drop(tree, "odd.md", "type: interdimensional_telegram")
    s = sc.organize()
    assert s["filed"] == 0
    assert s["unrouted"] == [("odd.md", "interdimensional_telegram")]
    assert (tree["inbox"] / "odd.md").exists()


def test_missing_type_is_unrouted(tree):
    _drop(tree, "notype.md", "tags: [a]")
    s = sc.organize()
    assert s["filed"] == 0
    assert len(s["unrouted"]) == 1
    assert (tree["inbox"] / "notype.md").exists()


def test_filing_is_idempotent(tree):
    _drop(tree, "log.md", "type: system_log", "> [NOVA_CONFIRMATION_PENDING]\n")
    sc.organize()
    filed = tree["root"] / "logs" / "log.md"
    once = filed.read_text()

    # Put it back in the inbox; the stamp must stop it being filed twice.
    (tree["inbox"] / "log.md").write_text(once, encoding="utf-8")
    s = sc.organize()
    assert s["filed"] == 0
    assert s["skipped_already_filed"] == 1
    assert once.count("NOVA CONFIRMED") == 1


def test_conflict_does_not_overwrite(tree):
    (tree["root"] / "logs").mkdir(parents=True)
    existing = tree["root"] / "logs" / "log.md"
    existing.write_text("ORIGINAL\n", encoding="utf-8")

    _drop(tree, "log.md", "type: system_log", "REPLACEMENT\n")
    s = sc.organize()
    assert s["filed"] == 0
    assert s["conflicts"] == [("log.md", str(tree["root"] / "logs"))]
    assert existing.read_text() == "ORIGINAL\n"
    assert (tree["inbox"] / "log.md").exists()


def test_knowledge_type_promotes_into_weaver_directory(tree):
    _drop(tree, "codex_entry.md", "type: codex\ntags: [glyph]")
    sc.organize()
    assert (tree["knowledge"] / "codex" / "codex_entry.md").exists()


def test_frontmatter_keys_are_not_reordered(tree):
    _drop(tree, "log.md", "date: 2026-09-01\ntype: system_log\nstatus: active")
    sc.organize()
    out = (tree["root"] / "logs" / "log.md").read_text()
    assert out.index("date:") < out.index("type:") < out.index("status:")
    assert "scribe_filed:" in out


def test_dry_run_changes_nothing(tree):
    p = _drop(tree, "log.md", "type: system_log", "> [NOVA_CONFIRMATION_PENDING]\n")
    before = p.read_text()
    s = sc.organize(dry_run=True)
    assert s["filed"] == 0
    assert s["moves"] == [("log.md", "scribe/logs")]
    assert p.exists() and p.read_text() == before


def test_index_groups_entries_by_tag(tree):
    _drop(tree, "a.md", "type: system_log\ntags: [alpha, shared]")
    _drop(tree, "b.md", "type: note\ntags: [shared]")
    sc.organize()
    res = sc.build_index(index_path=tree["root"] / "INDEX.md")

    assert res["tags"] == 2      # alpha, shared
    assert res["entries"] == 3   # a is tagged twice, b once
    text = (tree["root"] / "INDEX.md").read_text()
    assert "## shared" in text and "## alpha" in text
    shared = text.split("## shared")[1]
    assert "a.md" in shared and "b.md" in shared


def test_index_accepts_comma_separated_tags(tree):
    _drop(tree, "a.md", "type: note\ntags: alpha, beta")
    sc.organize()
    res = sc.build_index(index_path=tree["root"] / "INDEX.md")
    assert res["tags"] == 2


def test_route_escaping_the_cathedral_is_refused(tree, monkeypatch):
    """Routes are data. If one is edited to point outside, filing must refuse."""
    monkeypatch.setitem(sc.TYPE_ROUTES, "system_log", "../../../escaped")
    _drop(tree, "log.md", "type: system_log")
    s = sc.organize()
    assert s["filed"] == 0
    assert s["unrouted"] == [("log.md", "route escapes cathedral")]
    assert (tree["inbox"] / "log.md").exists()


def test_missing_inbox_is_not_an_error(tree):
    import shutil
    shutil.rmtree(tree["inbox"])
    s = sc.organize()
    assert s["scanned"] == 0 and s["filed"] == 0
