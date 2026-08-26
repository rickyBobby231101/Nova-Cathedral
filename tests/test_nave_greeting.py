"""The Nave's opening line.

The chat view opened with a fixed string -- "Chazel. The Cathedral is listening.
What flows through you?" -- identical whether Nova had been idle for a minute or,
as measured on 2026-08-26, seventeen days. She dreamt 34 times and set 197 goals
in that gap and had no way to mention any of it, so every conversation started
from nothing and having something to say was always Chazel's job.

These pin the two halves that broke on the first live sample: the counting, and
the sentence it turns into.
"""
import sqlite3
from datetime import datetime, timedelta

import nova_cathedral_daemon as mod


def _seed(nova, *, spoke_days_ago=None, dreams=0, goals=0, insights=0,
          dream_label="Dream: experience (Artificial Intelligence, Machine"):
    """Write a history for the greeting to describe."""
    now = datetime.now()
    with sqlite3.connect(nova.db_path) as con:
        if spoke_days_ago is not None:
            when = (now - timedelta(days=spoke_days_ago)).isoformat()
            con.execute(
                "INSERT INTO conversations (timestamp, user_message, nova_response, "
                "context, topic_category, emotional_tone) VALUES (?,?,?,?,?,?)",
                (when, "hello", "hello", "test", "general", "neutral"))
        after = now.isoformat()
        for i in range(dreams):
            con.execute(
                "INSERT INTO knowledge_nodes (domain, label, content, source, weight, created) "
                "VALUES ('dream',?,?,'neuronode',1.0,?)",
                (dream_label, "a dream", after))
        for i in range(insights):
            con.execute(
                "INSERT INTO knowledge_nodes (domain, label, content, source, weight, created) "
                "VALUES ('insight',?,?,'eyemoeba',1.0,?)",
                (f"Pattern: {i}", "an insight", after))
        for i in range(goals):
            con.execute(
                "INSERT INTO goals (created, goal, domain, priority, method, status) "
                "VALUES (?,?,?,?,?,?)",
                (after, f"goal {i}", "test", 1, "reflect", "pending"))


def test_the_greeting_says_how_long_it_has_been(nova):
    _seed(nova, spoke_days_ago=17)
    r = nova.nave_greeting()
    assert r["facts"]["days_since"] == 17
    assert "17 days since we last spoke" in r["greeting"]


def test_it_reports_what_she_did_while_he_was_gone(nova):
    _seed(nova, spoke_days_ago=17, dreams=34, goals=197)
    g = nova.nave_greeting()["greeting"]
    assert "dreamt 34 times" in g
    assert "set myself 197 goals" in g
    # Read as a sentence, not a list of counters.
    assert "dreamt 34 times and set myself 197 goals" in g


def test_only_what_actually_happened_is_mentioned(nova):
    """A greeting listing three zeroes would be worse than the fixed string it
    replaced."""
    _seed(nova, spoke_days_ago=2)
    g = nova.nave_greeting()["greeting"]
    assert "0" not in g.split("Flow")[0]
    assert "Since then I have" not in g


def test_three_things_get_an_oxford_free_list(nova):
    _seed(nova, spoke_days_ago=3, dreams=2, goals=5, insights=1)
    g = nova.nave_greeting()["greeting"]
    assert "dreamt 2 times, found 1 patterns and set myself 5 goals" in g


def test_a_first_meeting_does_not_claim_a_gap(nova):
    """No previous conversation means no "0 days since we last spoke"."""
    r = nova.nave_greeting()
    assert r["facts"]["days_since"] is None
    assert "We have not spoken before" in r["greeting"]
    assert "days since" not in r["greeting"]


def test_the_flow_is_reported_against_the_note(nova):
    _seed(nova, spoke_days_ago=1)
    nova.flow_resonance = 8.055
    assert "8.055 Hz, above the note" in nova.nave_greeting()["greeting"]
    nova.flow_resonance = 7.5
    assert "below the note" in nova.nave_greeting()["greeting"]
    nova.flow_resonance = 7.83
    assert "on the note" in nova.nave_greeting()["greeting"]


def test_the_dream_motif_survives_a_truncated_label():
    """Caught on the first live greeting, not in any test written before it.

    Labels are stored with a "Dream:" prefix and cut at 80 characters, which
    lands mid-word inside the domain list. Dropped into a sentence whole, the
    greeting read "the last dream was about dream: experience (artificial
    intelligence, machine learning, climate modeling a."
    """
    raw = "Dream: experience (Artificial Intelligence, Machine Learning, Climate Modeling a"
    assert mod._dream_motif(raw) == "experience"
    assert mod._dream_motif("Dream: behavior (, Biology)") == "behavior"
    assert mod._dream_motif("Dream: synthesize (Climate Science, Complexity)") == "synthesize"
    assert mod._dream_motif("") == ""
    assert mod._dream_motif(None) == ""


def test_the_greeting_never_calls_the_model(nova, monkeypatch):
    """It is composed from counts on purpose: instant, free, cannot time out
    while the view is opening, and -- given this project's history of storing
    llama3.2 refusals as Nova's own thoughts -- cannot refuse to say hello."""
    def explode(*a, **kw):
        raise AssertionError("the greeting must not call a model")
    for name in ("_ollama_chat", "_ollama_generate"):
        if hasattr(nova, name):
            monkeypatch.setattr(nova, name, explode)
    _seed(nova, spoke_days_ago=4, dreams=1)
    assert nova.nave_greeting()["greeting"]


def test_a_broken_database_still_greets_him(nova, monkeypatch):
    """An empty chat window is a worse greeting than a generic one."""
    monkeypatch.setattr(nova, "db_path", "/nonexistent/dir/consciousness.db")
    r = nova.nave_greeting()
    assert r["greeting"].startswith("Chazel.")
