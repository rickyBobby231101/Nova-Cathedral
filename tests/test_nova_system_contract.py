"""
Contract tests for nova_system — full shell access, deliberately.

`modules/nova_system.py` gives Nova unrestricted `subprocess.run(shell=True)`
over the socket. That is an accepted risk on this machine, not an oversight,
so these tests pin the *shape* the daemon destructures rather than arguing
with the design. What they must not do is exercise the dangerous half for
real.

**Nothing here kills a process, installs a package, or runs a destructive
command.** `kill_process` is tested against a patched `os.kill`, never a live
pid — a pid chosen as "surely not in use" is a pid the kernel is free to
reuse between the check and the call, and the target would be one of Chazel's
own processes. `shell_run` is exercised with `echo`, `false`, and a sleep that
is allowed to time out.

Note `shell_run` never raises: every failure path returns the same dict with
`ok: False`. That matters because the daemon calls it inside
`asyncio.to_thread` at daemon:4565 and returns the result straight to the
socket — an exception there is a dead command with no diagnosis.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT   = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "Cathedral" / "nova" / "modules"
if str(MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(MODULES_DIR))

import nova_system

SHELL_KEYS = {"ok", "stdout", "stderr", "returncode", "timed_out",
              "command", "duration"}


class TestSystemContract:
    def test_module_exports_what_the_daemon_calls(self):
        # daemon: _sys_module.shell_run / shell_run_bg / pip_install /
        #         pip_list / list_processes / system_snapshot
        for name in ("shell_run", "shell_run_bg", "pip_install", "pip_list",
                     "list_processes", "system_snapshot", "kill_process",
                     "pip_check", "which", "env_vars"):
            assert hasattr(nova_system, name), (
                f"the daemon calls nova_system.{name}"
            )

    def test_importing_the_module_is_silent(self, capsys):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_novasystem_silence_probe", MODULES_DIR / "nova_system.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = capsys.readouterr()
        assert out.out == "" and out.err == "", f"import printed: {out!r}"


class TestShellRun:
    """Every path returns the same seven keys — daemon:4565 returns it raw."""

    def test_a_successful_command(self):
        r = nova_system.shell_run("echo cathedral")
        assert SHELL_KEYS <= set(r), f"missing: {SHELL_KEYS - set(r)}"
        assert r["ok"] is True
        assert "cathedral" in r["stdout"]
        assert r["returncode"] == 0
        assert r["timed_out"] is False

    def test_a_failing_command_is_reported_not_raised(self):
        r = nova_system.shell_run("false")
        assert SHELL_KEYS <= set(r)
        assert r["ok"] is False
        assert r["returncode"] != 0

    def test_a_timeout_is_reported_not_hung(self):
        r = nova_system.shell_run("sleep 30", timeout=2)
        assert r["timed_out"] is True
        assert r["ok"] is False
        assert SHELL_KEYS <= set(r)

    def test_the_command_is_echoed_back(self):
        """The socket reply is the only record of what ran."""
        assert nova_system.shell_run("echo hi")["command"] == "echo hi"

    def test_a_command_that_cannot_start_still_returns_the_shape(self):
        r = nova_system.shell_run("echo hi", cwd="/nonexistent/directory/xyz")
        assert SHELL_KEYS <= set(r)
        assert r["ok"] is False

    def test_stdout_is_capped(self):
        """8000 chars. Without the cap a `cat` of something large is sent
        whole over the socket and into the GUI."""
        r = nova_system.shell_run("python3 -c \"print('x' * 20000)\"")
        assert len(r["stdout"]) <= 8000


class TestKillProcess:
    """Patched throughout — this never signals a real process."""

    def test_success_shape(self, monkeypatch):
        sent = {}
        monkeypatch.setattr(nova_system.os, "kill",
                            lambda pid, sig: sent.update(pid=pid, sig=sig))
        r = nova_system.kill_process(4242, 15)
        assert r == {"ok": True, "pid": 4242, "signal": 15}
        assert sent == {"pid": 4242, "sig": 15}

    def test_default_signal_is_term_not_kill(self, monkeypatch):
        """SIGTERM (15) lets a process shut down; SIGKILL (9) does not. The
        default must stay the recoverable one."""
        sent = {}
        monkeypatch.setattr(nova_system.os, "kill",
                            lambda pid, sig: sent.update(sig=sig))
        nova_system.kill_process(4242)
        assert sent["sig"] == 15

    def test_a_failure_is_reported_not_raised(self, monkeypatch):
        def boom(pid, sig):
            raise ProcessLookupError("No such process")
        monkeypatch.setattr(nova_system.os, "kill", boom)
        r = nova_system.kill_process(4242)
        assert r["ok"] is False
        assert "error" in r and r["pid"] == 4242


class TestReadOnlyInformation:
    def test_system_snapshot_has_the_fields_the_gui_reads(self):
        s = nova_system.system_snapshot()
        if "error" in s:
            pytest.skip(f"psutil unavailable: {s['error']}")
        for key in ("hostname", "cpu_pct", "mem_pct", "disk_pct", "uptime_s",
                    "timestamp", "python"):
            assert key in s, f"system_snapshot dropped {key!r}"

    def test_list_processes_returns_dicts(self):
        procs = nova_system.list_processes()
        assert isinstance(procs, list)
        if procs and "error" in procs[0]:
            pytest.skip("psutil unavailable")
        for p in procs[:3]:
            assert {"pid", "name", "status"} <= set(p)

    def test_list_processes_is_capped(self):
        """50. An uncapped listing on a busy machine is a large socket reply
        built to be read by a 1B model."""
        procs = nova_system.list_processes()
        if procs and "error" in procs[0]:
            pytest.skip("psutil unavailable")
        assert len(procs) <= 50

    def test_filtering_narrows_the_list(self):
        procs = nova_system.list_processes("python")
        if procs and "error" in procs[0]:
            pytest.skip("psutil unavailable")
        for p in procs:
            assert "python" in p["name"].lower()

    def test_which_finds_a_real_binary_and_shrugs_at_a_fake_one(self):
        assert nova_system.which("sh")
        assert nova_system.which("definitely-not-a-real-binary-xyz") == ""

    def test_pip_check_returns_a_bool(self):
        assert isinstance(nova_system.pip_check("pytest"), bool)
