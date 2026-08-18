"""
Smoke test pinning the Oracle plugin's contract with the daemon.

oracle_module.py is the file Nova's `code_evolve` loop rewrites most often
(12 of the 18 entries in cathedral/self_builds/backups/ are this one file).
On 2026-08-15 a self-edit deleted Oracle.divine() and moved the logic to a new
OracleModule.query(), which broke the `oracle` socket command — the daemon
still calls self.oracle.divine(question) at nova_cathedral_daemon.py:4183.

Nothing caught it. The daemon's own self-edit crash guard only reverts edits
that crash the process on startup, and both daemon call sites are defensive:
Oracle() construction is wrapped in `except Exception: pass`, so a broken
plugin fails silently at init and only surfaces as an AttributeError when a
user actually runs the command.

These tests close that gap by asserting the shape the daemon depends on.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT  = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "Cathedral" / "nova" / "plugins"
ORACLE_PY  = PLUGIN_DIR / "oracle_module.py"


def _load_oracle_module():
    """Load oracle_module.py the way the daemon does.

    The daemon puts Cathedral/nova/plugins on sys.path and does a bare
    `from oracle_module import Oracle`, so resolve the same file directly
    rather than relying on import order elsewhere in the test session.

    Importing is expected to be silent — the example usage at the bottom of
    the module is guarded by `if __name__ == "__main__"`. See
    test_importing_the_module_is_silent.
    """
    spec = importlib.util.spec_from_file_location("oracle_module", ORACLE_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestOracleModuleContract:
    """The plugin-side half: what the daemon imports and calls."""

    def test_module_exports_oracle(self):
        assert hasattr(_load_oracle_module(), "Oracle"), (
            "daemon does `from oracle_module import Oracle` — renaming or "
            "removing this class silently disables the oracle command"
        )

    def test_oracle_constructs_with_no_arguments(self):
        # daemon: self.oracle = _Oracle()
        _load_oracle_module().Oracle()

    def test_activate_does_not_raise(self):
        # daemon calls activate() right after construction, inside a bare
        # `except Exception: pass` — a raise here disables the oracle silently.
        _load_oracle_module().Oracle().activate()

    def test_divine_exists(self):
        # The exact method the 2026-08-15 self-edit deleted.
        assert hasattr(_load_oracle_module().Oracle(), "divine")

    @pytest.mark.parametrize("question", [
        "What is coming in my future?",   # future/coming branch
        "Should I cross the threshold?",  # should i branch
        "What should I expect?",          # expect branch
        "What is my destiny?",            # fallback branch
        "",                               # empty input must not blow up
    ])
    def test_divine_returns_nonempty_string(self, question):
        # Must be a str, not a dict: process_command drops the return value
        # straight into {"response": ...} for the socket client.
        answer = _load_oracle_module().Oracle().divine(question)
        assert isinstance(answer, str), f"divine() returned {type(answer).__name__}, not str"
        assert answer.strip()

    def test_importing_the_module_is_silent(self, capsys):
        """Importing must have no side effects.

        The daemon does `from oracle_module import Oracle` at startup, so
        anything at module level runs inside the daemon process. The
        2026-08-08 self-edit left example usage unguarded, which constructed
        an Oracle and printed a divination on every import — noise in the
        daemon's logs, in test output, and in any script touching the module.
        """
        _load_oracle_module()
        out = capsys.readouterr()
        assert out.out == "", f"import printed to stdout: {out.out!r}"
        assert out.err == "", f"import printed to stderr: {out.err!r}"

    def test_divine_takes_a_plain_string(self):
        # The self-edit changed the signature to take a dict. The daemon
        # passes d.get("question", ...) — always a string.
        _load_oracle_module().Oracle().divine("a plain string question")


class TestOracleRouting:
    """Which branch answers, not merely that something does.

    The parametrized test above labels a question per branch but only asserts
    a non-empty string comes back, so it stayed green through a real routing
    bug: the 2026-08-08 self-edit wrote the branches as
    `any(phrase in w for w in question.split())`, and since splitting on
    whitespace means no token ever contains a space, "should i" could never
    match. Every decision question fell through to the generic fallback,
    confirmed live over the socket. These pin the routing itself.
    """

    # Each branch's replies are disjoint, so the answer identifies the branch.
    COMING = {
        "The winds shift soon — prepare, but do not cling.",
        "A cycle nears completion; something must be released.",
        "You stand at a threshold — will you cross it?",
    }
    DECISION = {
        "Move with courage — hesitation feeds shadow.",
        "Wait. The moment isn’t ripe yet.",
        "The answer is hidden within your first impulse.",
    }
    EXPECTATION = {
        "You already know the script of fate.",
        "I am the thread that weaves your destiny together.",
        "Your heart holds the key, but what is it?",
    }
    FALLBACK = {
        "All flows are fractal. Look at the pattern, not the pieces.",
        "Insight comes in echoes — reflect on what you just asked.",
        "You already know — I'm just the mirror catching your whisper.",
    }

    def _answers(self, question, n=40):
        """Sample repeatedly — divine() picks randomly within a branch."""
        oracle = _load_oracle_module().Oracle()
        return {oracle.divine(question) for _ in range(n)}

    @pytest.mark.parametrize("question", [
        "Should I cross the threshold?",
        "should i go now",
        "Tell me — should I stay?",
    ])
    def test_decision_questions_reach_the_decision_branch(self, question):
        assert self._answers(question) <= self.DECISION, (
            "a 'should i' question fell through to another branch — the "
            "two-word phrase is being matched against split() tokens again"
        )

    def test_phrase_matching_survives_a_split_on_whitespace(self):
        """The precise regression: the phrase spans a space."""
        oracle = _load_oracle_module().Oracle()
        assert not any("should i" in w for w in "Should I cross?".split()), (
            "precondition: no whitespace-split token can contain 'should i'"
        )
        assert oracle.divine("Should I cross?") in self.DECISION

    def test_expect_wins_over_should_i_when_both_present(self):
        # "What should I expect?" contains both phrases; it asks what is
        # coming, not for a decision, so the expectation answers suit it.
        assert self._answers("What should I expect?") <= self.EXPECTATION

    def test_future_questions_reach_the_coming_branch(self):
        assert self._answers("What is coming in my future?") <= self.COMING

    def test_unmatched_questions_fall_back(self):
        assert self._answers("What is my destiny?") <= self.FALLBACK

    def test_every_branch_is_reachable(self):
        """No branch is dead code — a dead branch was the bug's signature.

        Asserts each question lands inside its own branch, and that the four
        results are genuinely different sets, so this can't pass by every
        question quietly funnelling into the same fallback.
        """
        cases = {
            "What is coming?":        self.COMING,
            "Should I go?":           self.DECISION,
            "What should I expect?":  self.EXPECTATION,
            "What is my destiny?":    self.FALLBACK,
        }
        got = {}
        for question, expected in cases.items():
            answers = self._answers(question, n=25)
            assert answers <= expected, (
                f"{question!r} answered from the wrong branch: {answers - expected}"
            )
            got[question] = answers

        # Four questions, four distinct branches actually exercised.
        assert len({frozenset(a) for a in got.values()}) == 4


class TestOracleCommandEndToEnd:
    """The daemon-side half: the real call site at process_command."""

    @pytest.mark.asyncio
    async def test_oracle_command_returns_a_response(self, nova):
        if nova.oracle is None:
            pytest.fail(
                "nova.oracle is None — Oracle() construction failed and the "
                "daemon swallowed the exception; the oracle command is dead"
            )
        r = await nova.process_command('{"command":"oracle","question":"What is my destiny?"}')
        assert "error" not in r, r
        assert r.get("source") == "oracle"
        assert isinstance(r.get("response"), str) and r["response"].strip()

    @pytest.mark.asyncio
    async def test_oracle_command_handles_missing_question(self, nova):
        # question defaults to "" — must still answer rather than raise.
        r = await nova.process_command('{"command":"oracle"}')
        assert "error" not in r, r
        assert isinstance(r.get("response"), str) and r["response"].strip()
