"""
One failing evolution step must not cost the six that follow it.

For 35 days it did. Seven subsystems shared a single try/except; goal
generation runs first, and a four-line bind bug in it silently aborted goal
processing, self-review, code study, resource maintenance, the Scribe and the
Weaver on every cycle. The journal showed one line about parameter binding and
nothing about the six subsystems that had quietly stopped.

The Scribe already had its own inner guard — "Filing must never take the
evolution loop down with it." That reasoning was right and had simply never
been applied to its siblings.

The second half of the failure was the response to it. Auto-heal's three
remedies (clear stale temp, reset DB connections, VACUUM) address resource and
I/O faults. Run against a code defect they accomplish nothing, and they did so
257 times — every auto-heal firing in the system's history, each reporting
"cleared 0 stale", each logging "Auto-heal ran" as though something had been
repaired.
"""
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "Cathedral" / "nova" / "daemon"))


async def _boom(exc=None):
    raise (exc or RuntimeError("step failed"))


async def _fine(record, name):
    record.append(name)


class TestStepIsolation:
    @pytest.mark.asyncio
    async def test_a_failing_step_returns_false_rather_than_raising(self, nova):
        assert await nova._evolution_step("thing", _boom()) is False

    @pytest.mark.asyncio
    async def test_a_successful_step_returns_true(self, nova):
        seen = []
        assert await nova._evolution_step("thing", _fine(seen, "ran")) is True
        assert seen == ["ran"]

    @pytest.mark.asyncio
    async def test_a_failure_does_not_stop_later_steps(self, nova):
        """The exact 35-day regression, in miniature."""
        seen = []
        await nova._evolution_step("first",  _boom())
        await nova._evolution_step("second", _fine(seen, "second"))
        await nova._evolution_step("third",  _fine(seen, "third"))
        assert seen == ["second", "third"], (
            "a failure in the first step suppressed the ones after it"
        )

    @pytest.mark.asyncio
    async def test_the_failure_is_recorded_for_self_review(self, nova):
        await nova._evolution_step("goal_generation", _boom(ValueError("bad json")))
        joined = " ".join(nova._recent_errors)
        assert "evolution:goal_generation" in joined
        assert "ValueError" in joined


class TestHealOnlyWhatHealingCanFix:
    """Auto-heal addresses resource faults. A code defect is not one."""

    @pytest.mark.parametrize("exc", [
        # The precise class raised by binding a list into a query — the error
        # that drove all 257 futile heal cycles.
        sqlite3.InterfaceError("Error binding parameter 5: type 'list' is not supported"),
        TypeError("unsupported operand"),
        ValueError("bad json"),
        AttributeError("'list' object has no attribute 'strip'"),
        KeyError("missing"),
    ])
    def test_code_defects_are_not_healable(self, nova, exc):
        assert nova._should_attempt_heal(exc) is False, (
            f"{type(exc).__name__} would still trigger a futile heal cycle"
        )

    @pytest.mark.parametrize("exc", [
        sqlite3.OperationalError("database is locked"),
        sqlite3.OperationalError("disk I/O error"),
        OSError("No space left on device"),
        MemoryError(),
    ])
    def test_resource_faults_remain_healable(self, nova, exc):
        assert nova._should_attempt_heal(exc) is True, (
            f"{type(exc).__name__} is exactly what auto-heal exists for"
        )

    @pytest.mark.asyncio
    async def test_a_code_defect_triggers_no_heal(self, nova, monkeypatch):
        called = []
        import nova_cathedral_daemon as mod
        if mod._EVO_AVAILABLE:
            monkeypatch.setattr(mod._evo, "attempt_auto_heal",
                                lambda *a, **k: called.append(1) or {"actions": []})
        await nova._evolution_step("goal_generation",
                                   _boom(sqlite3.InterfaceError("bind failed")))
        assert not called, "a type error still ran the heal chain"


class TestRepetitionEscalates:
    """The same error 257 times is a defect, not 257 incidents."""

    def test_repeat_count_rises_for_the_same_error(self, nova):
        e = ValueError("same")
        assert [nova._repeat_count("s", e) for _ in range(3)] == [1, 2, 3]

    def test_a_different_error_resets_the_count(self, nova):
        nova._repeat_count("s", ValueError("one"))
        nova._repeat_count("s", ValueError("one"))
        assert nova._repeat_count("s", ValueError("different")) == 1

    def test_counts_are_tracked_per_step(self, nova):
        e = ValueError("same")
        nova._repeat_count("weaver", e)
        assert nova._repeat_count("scribe", e) == 1

    @pytest.mark.asyncio
    async def test_success_clears_the_count(self, nova):
        e = ValueError("x")
        nova._repeat_count("s", e)
        nova._repeat_count("s", e)
        await nova._evolution_step("s", _fine([], "ok"))
        assert nova._repeat_count("s", e) == 1

    @pytest.mark.asyncio
    async def test_persistent_failure_stops_healing(self, nova, monkeypatch):
        """Past the escalation threshold, stop pretending to repair it."""
        import nova_cathedral_daemon as mod
        calls = []
        if mod._EVO_AVAILABLE:
            monkeypatch.setattr(mod._evo, "attempt_auto_heal",
                                lambda *a, **k: calls.append(1) or {"actions": []})
        err = sqlite3.OperationalError("database is locked")   # healable
        for _ in range(6):
            await nova._evolution_step("goal_processing", _boom(err))
        assert len(calls) < 6, "healing continued indefinitely on a persistent fault"
        assert len(calls) == nova._REPEAT_ESCALATION - 1

    @pytest.mark.asyncio
    async def test_persistent_failure_is_logged_as_a_defect(self, nova, caplog):
        import logging
        caplog.set_level(logging.WARNING)
        for _ in range(nova._REPEAT_ESCALATION):
            await nova._evolution_step("weaver", _boom(ValueError("same")))
        assert any("PERSISTENT FAILURE" in r.getMessage() for r in caplog.records), (
            "a repeating defect never escalated above the noise floor"
        )
