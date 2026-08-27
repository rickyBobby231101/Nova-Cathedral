"""Node labels that read as whole phrases.

Both faults below were live in the graph, visible in the GUI's Insights and
Dreams views, and invisible to every test written before them.
"""
import nova_cathedral_daemon as mod


def test_a_blank_domain_does_not_become_a_leading_comma():
    """Six nodes carry domain='', which rendered as
    "Pattern: neural across , Artificial Intelligence, ..." """
    label = mod._label("Pattern", "neural",
                       ["", "Artificial Intelligence", "Machine Learning"])
    assert "across ," not in label
    assert label.startswith("Pattern: neural across Artificial Intelligence")


def test_a_label_never_ends_mid_word():
    """The old code cut with a bare [:80], landing inside whatever domain name
    straddled the boundary: "... Machine Learning, Climate Modeling a"."""
    label = mod._label("Dream", "experience",
                       ["Artificial Intelligence", "Machine Learning", "Climate Modeling"])
    assert len(label) <= 80
    assert not label.endswith("Climate Modeling a")
    assert label.endswith(")"), "a dream label keeps its bracket closed"


def test_dropping_a_domain_is_marked_as_elision():
    label = mod._label("Pattern", "neural",
                       ["Artificial Intelligence", "Machine Learning", "Computer Vision",
                        "Neuroscience of Memory Formation"])
    assert len(label) <= 80
    assert "…" in label, "a reader should see that the list was cut"


def test_every_shape_stays_inside_the_limit():
    for prefix in ("Pattern", "Dream"):
        for domains in ([""], ["", ""], ["A" * 200], ["x"],
                        ["Quantum Mechanics"] * 6, []):
            label = mod._label(prefix, "motif", list(domains))
            assert len(label) <= 80, label
            assert "(," not in label and "across ," not in label
            assert not label.endswith(",")
            # No dangling bracket when there was nothing to put in it.
            assert label.count("(") == label.count(")"), label


def test_a_motif_with_no_real_domains_is_still_named():
    assert mod._label("Dream", "x", ["", ""]) == "Dream: x"
    assert mod._label("Pattern", "y", []) == "Pattern: y"


def test_a_node_without_a_domain_is_not_evidence_of_a_cross_domain_pattern(nova):
    """Counting '' as a domain inflated the span the ranking is built on."""
    nova._knowledge_add("", "Orphan", "resonance appears in this undomained node")
    nova._knowledge_add("herbal", "Yarrow", "resonance runs through the body")
    for i in range(30):
        nova._knowledge_add(f"pad{i % 5}", f"Pad {i}", f"filler {i} words zzz{i}")

    for m in nova._eyemoeba_analyze():
        assert "" not in m["domains"], "a blank domain is not a domain"
