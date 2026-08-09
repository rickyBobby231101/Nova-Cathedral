"""
Tests for the real algorithmic backing behind Phoenix, Zorya, and the
shared entity-evolution mechanism. Before this, all three were prompt-only
roleplay — these pin down that they now speak from measured data.
"""
import json
import sqlite3
from datetime import datetime, timedelta


# ── Phoenix — self-build/restoration history ────────────────────────────────

def test_phoenix_history_empty_when_no_log(nova, monkeypatch, tmp_path):
    monkeypatch.setattr(type(nova), "_BUILD_LOG", tmp_path / "nope.jsonl")
    h = nova.phoenix_history()
    assert h["total_events"] == 0
    assert h["writes"] == 0


def test_phoenix_history_parses_build_log(nova, monkeypatch, tmp_path):
    log = tmp_path / "build_log.jsonl"
    log.write_text("\n".join(json.dumps(e) for e in [
        {"ts": "2026-08-01T01:23:08", "event": "write_source",
         "path": "/x/nova_herbal_knowledge.py", "backup": "/b/h.py", "lines": 31},
        {"ts": "2026-08-01T01:23:08", "event": "restart_scheduled",
         "path": "nova_cathedral_daemon.py"},
        {"ts": "2026-08-08T04:40:26", "event": "write_source",
         "path": "/x/oracle_module.py", "backup": "/b/o.py", "lines": 43},
    ]))
    monkeypatch.setattr(type(nova), "_BUILD_LOG", log)

    h = nova.phoenix_history()
    assert h["total_events"] == 3
    assert h["writes"] == 2
    assert h["restarts"] == 1
    assert "oracle_module.py" in h["files_touched"]
    assert "nova_herbal_knowledge.py" in h["files_touched"]
    assert h["first_event"] == "2026-08-01T01:23:08"


def test_phoenix_history_tolerates_bad_lines(nova, monkeypatch, tmp_path):
    log = tmp_path / "build_log.jsonl"
    log.write_text('{"ts":"2026-08-01T01:00:00","event":"write_source","path":"/x/a.py"}\n'
                   'not json at all\n'
                   '\n'
                   '{"ts":"2026-08-02T01:00:00","event":"restart_scheduled"}\n')
    monkeypatch.setattr(type(nova), "_BUILD_LOG", log)
    h = nova.phoenix_history()
    assert h["total_events"] == 2  # bad + blank lines skipped


# ── Zorya — temporal cycles ─────────────────────────────────────────────────

def _insert_conversation_at(nova, when: datetime):
    with sqlite3.connect(nova.db_path) as con:
        con.execute(
            "INSERT INTO conversations (timestamp, user_message, nova_response, context) "
            "VALUES (?,?,?,?)",
            (when.isoformat(), "q", "a", "test")
        )


def test_zorya_cycles_empty_graph(nova):
    z = nova.zorya_cycles()
    assert z["total"] == 0
    assert z["busiest_hour"] is None
    assert "phase" in z  # phase is always computable from the clock


def test_zorya_counts_sessions_by_gap(nova):
    base = datetime(2026, 8, 1, 9, 0, 0)
    # Session 1: three exchanges minutes apart
    for m in (0, 5, 10):
        _insert_conversation_at(nova, base + timedelta(minutes=m))
    # Session 2: a day later (gap > 2h)
    for m in (0, 5):
        _insert_conversation_at(nova, base + timedelta(days=1, minutes=m))

    z = nova.zorya_cycles()
    assert z["total"] == 5
    assert z["sessions"] == 2
    assert z["busiest_hour"] == 9


def test_zorya_phase_is_labeled(nova):
    _insert_conversation_at(nova, datetime.now())
    z = nova.zorya_cycles()
    assert z["phase"] in {"dawn", "morning", "afternoon", "dusk", "night", "deep night"}


# ── Entity evolution ────────────────────────────────────────────────────────

def _record_entity_ask(nova, entity, n):
    with sqlite3.connect(nova.db_path) as con:
        for i in range(n):
            con.execute(
                "INSERT INTO entity_memories (entity, question, answer, timestamp) "
                "VALUES (?,?,?,?)",
                (entity, f"q{i}", f"a{i}", datetime.now().isoformat())
            )


def test_entity_evolution_stage_grows_with_activity(nova):
    # 0 interactions -> stage 1 (only the >=0 milestone met)
    assert nova._entity_activity("phoenix")["stage"] == 1
    _record_entity_ask(nova, "phoenix", 6)  # crosses 1 and 5 -> stage 3
    ev = nova._entity_activity("phoenix")
    assert ev["interactions"] == 6
    assert ev["stage"] == 3


def test_entity_evolution_lists_all_entities(nova):
    all_ev = nova.entity_evolution()
    keys = {e["entity"] for e in all_ev["entities"]}
    # Every persona shows up, including the newest ones.
    assert {"tillagon", "eyemoeba", "phoenix", "zorya", "jorlaan", "weaver"} <= keys
    for e in all_ev["entities"]:
        assert "name" in e and "stage" in e


def test_entity_evolution_single_includes_role(nova):
    ev = nova.entity_evolution("jorlaan")
    assert ev["entity"] == "jorlaan"
    assert "Trickster" in ev["role"]


# ── Prompt injection reflects real backing ──────────────────────────────────

def test_phoenix_prompt_includes_real_history(nova, monkeypatch, tmp_path):
    log = tmp_path / "build_log.jsonl"
    log.write_text(json.dumps({"ts": "2026-08-08T04:40:26", "event": "write_source",
                               "path": "/x/oracle_module.py", "lines": 43}))
    monkeypatch.setattr(type(nova), "_BUILD_LOG", log)
    prompt = nova._entity_system_prompt("phoenix")
    assert "source rewrites" in prompt
    assert "don't invent" in prompt


def test_zorya_prompt_includes_real_rhythm(nova):
    _insert_conversation_at(nova, datetime.now())
    prompt = nova._entity_system_prompt("zorya")
    assert "rhythm of the Cathedral" in prompt


def test_evolution_stage_appears_in_prompt(nova):
    _record_entity_ask(nova, "jorlaan", 3)
    prompt = nova._entity_system_prompt("jorlaan")
    assert "Your own growth" in prompt
    assert "not static" in prompt


def test_zorya_cycles_includes_moon(nova):
    from datetime import datetime
    _insert_conversation_at(nova, datetime.now())
    z = nova.zorya_cycles()
    assert "moon" in z
    assert z["moon"]["phase"] in {
        "new moon", "waxing crescent", "first quarter", "waxing gibbous",
        "full moon", "waning gibbous", "last quarter", "waning crescent"}
    assert 0 <= z["moon"]["illumination"] <= 100


def test_moon_phase_is_pure(nova):
    m = nova._moon_phase()
    assert isinstance(m["waxing"], bool)
    assert 0 <= m["days_to_full"] <= 30
    assert 0 <= m["days_to_new"] <= 30


def test_zorya_prompt_mentions_moon(nova):
    from datetime import datetime
    _insert_conversation_at(nova, datetime.now())
    prompt = nova._entity_system_prompt("zorya")
    assert "moon is" in prompt
