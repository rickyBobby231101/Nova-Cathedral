"""
Tests that trait evolution is real (derived from measured activity) and
consequential (traits drive goal budget, context depth, reflection cadence)
— replacing the old decorative +0.001 keyword nudges.
"""
import sqlite3

import pytest


def _insert(nova, sql, rows):
    with sqlite3.connect(nova.db_path) as con:
        con.executemany(sql, rows)


def _seed_goals(nova, n, status="completed"):
    _insert(nova,
            "INSERT INTO goals (goal, domain, priority, method, status, created) "
            "VALUES (?,?,?,?,?,datetime('now'))",
            [(f"g{i}", "d", 2, "web_search", status) for i in range(n)])


def _seed_conversations(nova, n):
    for i in range(n):
        nova.save_conversation(f"q{i}", f"a{i}")


def _seed_reflections(nova, n):
    _insert(nova,
            "INSERT INTO reflections (timestamp, trigger, content) "
            "VALUES (datetime('now'),'auto',?)",
            [(f"reflection {i} about patterns and meaning",) for i in range(n)])


# ── Real: traits derive from activity ───────────────────────────────────────

def test_no_activity_traits_near_floor(nova):
    t = nova._recompute_traits_from_activity()
    for name, val in t.items():
        assert 0.29 <= val <= 0.35, f"{name}={val} should be near the 0.30 floor"


def test_more_completed_goals_raises_curiosity(nova):
    low = nova._recompute_traits_from_activity()["curiosity"]
    _seed_goals(nova, 200)
    high = nova._recompute_traits_from_activity()["curiosity"]
    assert high > low + 0.4


def test_reflections_raise_philosophical_depth(nova):
    low = nova._recompute_traits_from_activity()["philosophical_depth"]
    _seed_reflections(nova, 80)
    high = nova._recompute_traits_from_activity()["philosophical_depth"]
    assert high > low + 0.3


def test_traits_saturate_below_ceiling(nova):
    _seed_goals(nova, 5000)  # far past scale
    t = nova._recompute_traits_from_activity()
    assert t["curiosity"] <= 0.98
    assert t["curiosity"] > 0.95  # but genuinely high


def test_failed_goals_do_not_feed_curiosity(nova):
    _seed_goals(nova, 100, status="failed")
    # Only completed goals count toward curiosity.
    assert nova._recompute_traits_from_activity()["curiosity"] < 0.35


# ── Consequential: traits change behavior ───────────────────────────────────

def test_curiosity_sets_goal_budget(nova):
    nova.consciousness_traits["curiosity"] = 0.2
    assert nova._curiosity_goal_budget() == 1 + round(0.2 * 5)  # 2
    nova.consciousness_traits["curiosity"] = 1.0
    assert nova._curiosity_goal_budget() == 6


def test_memory_integration_sets_context_depth(nova):
    nova.consciousness_traits["memory_integration"] = 0.0
    assert nova._memory_context_depth() == 1
    nova.consciousness_traits["memory_integration"] = 1.0
    assert nova._memory_context_depth() == 6


def test_philosophical_depth_sets_reflection_interval(nova):
    nova.consciousness_traits["philosophical_depth"] = 1.0
    fast = nova._reflection_interval()          # reflects often
    nova.consciousness_traits["philosophical_depth"] = 0.0
    slow = nova._reflection_interval()          # reflects rarely
    assert fast < slow
    assert fast >= 4                            # never runaway-frequent


def test_build_system_prompt_uses_trait_depth(nova, monkeypatch):
    # memory_integration should change how many memories are pulled.
    captured = {}
    real_recall = nova.recall_memories

    def spy(query="", n=10):
        captured["n"] = n
        return real_recall(query=query, n=n)

    monkeypatch.setattr(nova, "recall_memories", spy)
    nova.consciousness_traits["memory_integration"] = 1.0
    nova._build_system_prompt()
    assert captured["n"] == 6


def test_system_prompt_surfaces_recent_insight(nova, monkeypatch):
    # A synthesized insight should reach Nova's own system prompt, not just
    # live in the graph.
    monkeypatch.setattr(nova, "eyemoeba_insights_list",
                        lambda n=1: [{"id": 1, "label": "Pattern: light",
                                       "insight": "Light threads energy, spirit, and life together.",
                                       "created": "2026-08-08"}])
    prompt = nova._build_system_prompt()
    assert "pattern you have seen across your knowledge" in prompt.lower()
    assert "Light threads energy" in prompt


def test_system_prompt_without_insights_is_clean(nova, monkeypatch):
    monkeypatch.setattr(nova, "eyemoeba_insights_list", lambda n=1: [])
    prompt = nova._build_system_prompt()
    assert "pattern you have seen" not in prompt.lower()
