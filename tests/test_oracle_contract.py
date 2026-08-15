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

    Note: the module runs example usage at import time and prints to stdout.
    That's pre-existing; pytest captures it.
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

    def test_divine_takes_a_plain_string(self):
        # The self-edit changed the signature to take a dict. The daemon
        # passes d.get("question", ...) — always a string.
        _load_oracle_module().Oracle().divine("a plain string question")


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
