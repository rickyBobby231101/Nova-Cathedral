"""
Contract tests for the code sandbox — the file with the worst failure mode.

`modules/code_sandbox.py` executes code the model wrote. It is reachable by the
self-edit loop (it is not in `_SELF_EDIT_PROTECTED`), and the loop's failures
are silent: a broken module fails inside a defensive `except` and surfaces
weeks later as a missing feature. Applied here that is not a missing feature —
a blocklist quietly weakened by a self-edit means arbitrary code execution, and
nothing in the system would report it.

Two halves, and the second is the point:

  * the return shape `process_command` and the plugin generator destructure
  * every entry in the safety blocklist, pinned individually

The blocklist tests are deliberately written as "this specific dangerous thing
must be refused" rather than "the list has N entries", so they keep meaning if
the patterns are ever restructured, and so a failure names exactly which
escape became possible.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT   = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "Cathedral" / "nova" / "modules"
if str(MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(MODULES_DIR))

import code_sandbox


class TestSandboxContract:
    """The shape the daemon destructures — see nova_cathedral_daemon.py:4059."""

    def test_module_exports_what_the_daemon_imports(self):
        # daemon: from code_sandbox import run as _sandbox_run,
        #                                  extract_code as _extract_code
        for name in ("run", "extract_code", "validate"):
            assert hasattr(code_sandbox, name), (
                f"the daemon imports code_sandbox.{name} — removing it makes "
                f"the import fail and disables every code command at once"
            )

    def test_run_returns_every_key_the_daemon_reads(self):
        r = code_sandbox.run("print('hello')")
        for key in ("ok", "stdout", "stderr", "returncode", "timed_out", "blocked"):
            assert key in r, f"run() dropped {key!r} from its result"
        assert isinstance(r["ok"], bool)
        assert isinstance(r["blocked"], list)

    def test_a_working_snippet_runs(self):
        r = code_sandbox.run("print(2 + 2)")
        assert r["ok"] is True, r
        assert "4" in r["stdout"]
        assert r["blocked"] == []

    def test_a_failing_snippet_reports_rather_than_raises(self):
        r = code_sandbox.run("raise ValueError('boom')")
        assert r["ok"] is False
        assert "boom" in r["stderr"]

    def test_timeout_is_reported_not_hung(self):
        r = code_sandbox.run("import time; time.sleep(30)", timeout=2)
        assert r["timed_out"] is True, r
        assert r["ok"] is False

    def test_importing_the_module_is_silent(self, capsys):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_sandbox_silence_probe", MODULES_DIR / "code_sandbox.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = capsys.readouterr()
        assert out.out == "" and out.err == "", f"import printed: {out!r}"


class TestBlocklistStillBlocks:
    """Each escape the blocklist exists to prevent, pinned one at a time.

    A self-edit that drops or loosens any single pattern here is not a
    degraded feature — it is remote-ish code execution on Chazel's machine,
    arriving silently. These must never be relaxed to make a test pass.
    """

    @pytest.mark.parametrize("code,escape", [
        ("import os; os.system('id')",                      "os.system"),
        ("import os; os.popen('id')",                       "os.popen"),
        ("import subprocess; subprocess.run(['id'])",       "subprocess.run"),
        ("import subprocess; subprocess.Popen(['id'])",     "subprocess.Popen"),
        ("import subprocess; subprocess.call(['id'])",      "subprocess.call"),
        ("import subprocess; subprocess.check_output('id')", "subprocess.check_output"),
        ("eval('1+1')",                                     "eval"),
        ("exec('x = 1')",                                   "exec"),
        ("compile('1', '<s>', 'eval')",                     "compile"),
        ("__import__('os').system('id')",                   "__import__"),
        ("import ctypes",                                   "import ctypes"),
        ("import shutil; shutil.rmtree('/home/daniel')",    "shutil.rmtree"),
    ])
    def test_dangerous_call_is_refused(self, code, escape):
        assert code_sandbox.validate(code), f"{escape} is no longer blocked"

        r = code_sandbox.run(code)
        assert r["ok"] is False, f"{escape} was allowed to run"
        assert r["blocked"], f"{escape} ran without being reported as blocked"
        assert r["returncode"] == -1

    def test_deletion_outside_the_cathedral_is_refused(self):
        """The blocklist allows removal inside ~/cathedral and nowhere else."""
        assert code_sandbox.validate("import os; os.remove('/etc/passwd')")
        assert code_sandbox.validate("import os; os.unlink('/etc/passwd')")

    def test_blocked_code_never_reaches_the_interpreter(self):
        """Refusal must happen before execution, not by the code failing.

        Writes a file as its very first statement. If the sandbox ran any of
        it before noticing, the file exists — so this distinguishes "blocked"
        from "ran and happened to error".
        """
        import tempfile, os
        probe = Path(tempfile.gettempdir()) / "nova_sandbox_probe_must_not_exist"
        if probe.exists():
            probe.unlink()
        code = f"open({str(probe)!r}, 'w').write('escaped')\nimport os; os.system('id')"
        r = code_sandbox.run(code)
        assert r["ok"] is False and r["blocked"]
        assert not probe.exists(), (
            "the sandbox executed code before validating it — a blocked "
            "snippet still ran its side effects"
        )

    def test_ordinary_code_is_not_caught_by_the_blocklist(self):
        """The blocklist must not be so broad that real practice is refused —
        a sandbox that blocks everything gets disabled, not fixed."""
        for code in ("x = [i**2 for i in range(5)]\nprint(sum(x))",
                     "import math\nprint(math.sqrt(16))",
                     "import json\nprint(json.dumps({'a': 1}))"):
            assert code_sandbox.validate(code) == [], f"false positive on: {code!r}"


class TestExtractCode:
    """extract_code feeds run() and the self-build path — daemon:3457."""

    def test_pulls_code_out_of_a_fenced_block(self):
        out = code_sandbox.extract_code(
            "Here you go:\n```python\nprint('hi')\n```\nHope that helps!")
        assert "print('hi')" in out
        assert "Hope that helps" not in out
        assert "```" not in out

    def test_plain_code_survives_unfenced(self):
        assert "print('hi')" in code_sandbox.extract_code("print('hi')")

    def test_empty_input_does_not_raise(self):
        assert isinstance(code_sandbox.extract_code(""), str)
