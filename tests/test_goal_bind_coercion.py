"""
add_goals() must survive whatever shape the local model emits.

Measured on the live daemon 2026-09-04: ten occurrences in twelve hours of

    Autonomous evolution error: Error binding parameter 5: type 'list' is not supported

Parameter 5 in the goals INSERT is `method`, and llama3.2:1b had returned a
list where a string was asked for. `_as_sqlite_scalar` already existed for
exactly this failure — its docstring names it — but had only been applied in
`store_improvement()`. This call site was missed.

The cost was not one goal. Goal generation runs first in the evolution cycle,
so the exception aborted the entire cycle at the daemon's broad handler
(daemon:3193). By the time it was found, the goals table held 452 completed,
234 failed, and **one** pending row.

These tests pin each field separately, so a failure names which one regressed
rather than reporting "goals broke".
"""
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT   = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "Cathedral" / "nova" / "modules"
if str(MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(MODULES_DIR))

import evolution_engine as evo


@pytest.fixture
def db(tmp_path):
    p = tmp_path / "consciousness.db"
    evo.init_goals_table(p)
    return p


def _rows(db):
    with sqlite3.connect(db) as con:
        return con.execute(
            "SELECT goal, domain, priority, method, status FROM goals").fetchall()


class TestListFieldsDoNotAbortTheCycle:
    """The exact regression: a list in any model-supplied field."""

    def test_method_as_a_list_is_the_measured_failure(self, db):
        """Parameter 5. This is the one that was firing in production."""
        assert evo.add_goals(db, [{
            "goal": "study resonance in coupled oscillators",
            "domain": "physics",
            "priority": 2,
            "method": ["web_search", "reflect"],
        }]) == 1
        assert _rows(db)[0][3] == "web_search, reflect"

    def test_priority_as_a_list(self, db):
        assert evo.add_goals(db, [{"goal": "g", "priority": ["high"]}]) == 1
        assert _rows(db)[0][2] == "high"

    def test_domain_as_a_list(self, db):
        assert evo.add_goals(db, [{"goal": "g", "domain": ["cosmos", "mythos"]}]) == 1
        assert _rows(db)[0][1] == "cosmos, mythos"

    def test_goal_as_a_list_does_not_raise_on_strip(self, db):
        """`goal` is coerced before .strip(), not at the bind.

        A list here never reaches sqlite — it raises AttributeError on
        .strip() first, a different crash with a different message. Coercing
        inside the execute() call would not have caught it.
        """
        assert evo.add_goals(db, [{"goal": ["study", "the flow"]}]) == 1
        assert _rows(db)[0][0] == "study, the flow"

    def test_a_dict_field_is_also_survivable(self, db):
        """Models emit objects as well as lists."""
        assert evo.add_goals(db, [{"goal": "g", "method": {"kind": "web"}}]) == 1
        assert isinstance(_rows(db)[0][3], str)

    def test_none_falls_back_to_the_documented_default(self, db):
        evo.add_goals(db, [{"goal": "g", "method": None, "priority": None}])
        goal, domain, priority, method, status = _rows(db)[0]
        assert method == "reflect"
        assert priority == 2


class TestOneBadGoalDoesNotCostTheBatch:
    """The blast-radius property, which is the real point of the fix."""

    def test_a_malformed_goal_does_not_prevent_the_others(self, db):
        added = evo.add_goals(db, [
            {"goal": "first good goal",  "method": "web_search"},
            {"goal": "malformed one",    "method": ["web_search", "reflect"]},
            {"goal": "second good goal", "method": "reflect"},
        ])
        assert added == 3, "a malformed field still cost the batch"
        assert len(_rows(db)) == 3


class TestOrdinaryBehaviourIsUnchanged:
    """The fix must not alter the normal path."""

    def test_well_formed_goals_store_exactly_as_before(self, db):
        evo.add_goals(db, [{"goal": "study X", "domain": "cosmos",
                            "priority": 1, "method": "web_search"}])
        assert _rows(db)[0] == ("study X", "cosmos", 1, "web_search", "pending")

    def test_plain_strings_still_accepted(self, db):
        assert evo.add_goals(db, ["a bare string goal"]) == 1
        assert _rows(db)[0][3] == "reflect"

    def test_duplicates_still_skipped(self, db):
        evo.add_goals(db, [{"goal": "same goal"}])
        assert evo.add_goals(db, [{"goal": "same goal"}]) == 0

    def test_empty_and_non_dict_entries_still_skipped(self, db):
        assert evo.add_goals(db, [{"goal": "   "}, {}, 42, None]) == 0
