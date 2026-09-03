"""
A goal must run under a method that can actually answer it.

Two failures measured on the live goals table, 2026-09-02:

  web_search : 163 completed /   6 failed
  reflect    : 160 completed / 152 failed
  invalid    :   0 completed /  48 failed

`method` defaults to 'reflect' in the schema, and reflect researches by
recalling past conversations. Every goal Chazel has ever set carries that
default, and every one had failed — "study stoisism" cannot be answered from
a history that never mentions Stoicism. Separately, 48 goals carry method
names the model invented (quantum_computing, "literature review",
"web_search|file_read") which match no branch in _process_goal, so context
stays empty and they fail without ever raising.
"""
import evolution_engine as evo


# ── the goals that actually failed ───────────────────────────────────────

def test_chazels_real_goals_route_somewhere_that_can_answer_them():
    cases = {
        "study stoisism":                                        "web_search",
        "learn about gnostic":                                   "web_search",
        "do some research on something i may find intereing":    "web_search",
        "learn as much as you can over the net 12 hours":        "web_search",
        "read all files on this system and auto evolve":         "file_read",
        "read the files it this repo and see what could be useful": "file_read",
        "search for any self improvements":                      "self_read",
    }
    for goal, expected in cases.items():
        assert evo.resolve_method("reflect", goal) == expected, goal


def test_a_learning_goal_never_stays_on_reflect():
    """The subject of "learn X" is by definition not in the history."""
    for goal in ("study stoicism", "learn about gnosticism",
                 "what is the holographic principle", "explain entanglement"):
        assert evo.resolve_method("reflect", goal) != "reflect", goal


# ── invented method names ────────────────────────────────────────────────

def test_invented_methods_are_replaced_not_run():
    """These match no branch, so they fail 100% of the time."""
    for junk in ("quantum_computing", "poetic_computation", "literature review",
                 "web_search|file_read", "reflect_self_read", "", None):
        m = evo.resolve_method(junk, "study stoicism")
        assert m in evo.VALID_METHODS, f"{junk!r} -> {m!r}"


def test_an_invented_method_on_an_unclassifiable_goal_still_lands_valid():
    m = evo.resolve_method("neuroimaging|scdb_search", "zzzz qqqq")
    assert m in evo.VALID_METHODS


# ── what must NOT change ─────────────────────────────────────────────────

def test_an_explicit_non_default_method_is_respected():
    """Only 'reflect' is treated as the schema default. A deliberate choice
    stands, or this becomes a second layer of guessing over the first."""
    for m in ("web_search", "file_read", "self_read", "code"):
        assert evo.resolve_method(m, "study stoicism") == m


def test_a_genuinely_reflective_goal_stays_on_reflect():
    for goal in ("reflect on my own growth", "consider the last conversation"):
        assert evo.resolve_method("reflect", goal) == "reflect", goal


def test_web_unavailable_falls_back_rather_than_routing_nowhere():
    m = evo.resolve_method("reflect", "study stoicism", web_available=False)
    assert m == "reflect"


def test_case_and_whitespace_are_tolerated():
    assert evo.resolve_method("  WEB_SEARCH  ", "anything") == "web_search"
