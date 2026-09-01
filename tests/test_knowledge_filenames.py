"""
Topics for append_knowledge come from the model, so they are untrusted input
to a filename.

Two failures this pins. A blank topic produced the filename ".md", which the
Weaver skips as a dotfile — 57 research entries accumulated in it between
2026-04-15 and 2026-09-01 and never reached the knowledge graph. And a topic
containing a path separator would have written outside the knowledge
directory altogether.
"""
import filesystem


def test_blank_topic_does_not_become_a_dotfile():
    for blank in ("", "   ", None):
        assert filesystem.topic_filename(blank) == filesystem.UNCATEGORIZED


def test_normal_topic_is_slugified():
    assert filesystem.topic_filename("Machine Learning") == "machine_learning"
    assert filesystem.topic_filename("  Astro Physics  ") == "astro_physics"


def test_path_separators_cannot_escape_the_knowledge_directory():
    for hostile in ("../../etc/passwd", "/etc/passwd", "a/b/c"):
        stem = filesystem.topic_filename(hostile)
        assert "/" not in stem
        assert not stem.startswith(".")


def test_topic_of_only_punctuation_falls_back():
    """Slugifying '...' to '' would recreate the dotfile bug by another road."""
    assert filesystem.topic_filename("...") == filesystem.UNCATEGORIZED
    assert filesystem.topic_filename("---") == filesystem.UNCATEGORIZED


def test_result_is_always_weavable():
    """The Weaver skips names starting with '.', so no topic may produce one."""
    for topic in ("", ".", ".hidden", "..", "  .  ", "?!"):
        assert not filesystem.topic_filename(topic).startswith(".")
