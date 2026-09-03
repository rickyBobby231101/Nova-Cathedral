"""
Contract tests for nova_self_builder — the mechanism that puts things back.

This is the file the whole self-edit risk stance rests on. The loop is left
unsupervised on purpose; what makes that acceptable is that every write is
backed up first, syntax-checked before it lands, and revertible. If this
module quietly stops backing up, nothing announces it — the next bad self-edit
is simply unrecoverable, and the first sign is a broken Cathedral with no
backup to restore.

It is in `_SELF_EDIT_PROTECTED`, so the loop cannot rewrite it — that much is
pinned by test_self_edit_protection.py. This file pins the API instead: a human
edit, a refactor, or a bad merge can break a rollback mechanism just as
thoroughly as a self-edit can, and neither the crash guard nor the protection
list would notice.

**Every path is redirected into tmp_path.** In particular RESTART_FLAG, which
is `/tmp/nova_self_restart` and is polled by the *running* daemon's main loop
(daemon:5979) — a test that wrote the real flag would restart Chazel's live
Cathedral mid-suite. No test here touches the real backup directory, the real
build log, or any real source file.
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT   = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "Cathedral" / "nova" / "modules"
if str(MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(MODULES_DIR))

import nova_self_builder as builder


GOOD = "def f():\n    return 1\n"
ALSO_GOOD = "def f():\n    return 2\n"
BROKEN = "def f(:\n    return 1\n"


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Redirect every path the module writes to into tmp_path.

    RESTART_FLAG especially: the real one is watched by the live daemon.
    """
    monkeypatch.setattr(builder, "NOVA_ROOT", tmp_path / "src")
    monkeypatch.setattr(builder, "BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(builder, "BUILD_LOG", tmp_path / "build_log.jsonl")
    monkeypatch.setattr(builder, "RESTART_FLAG", tmp_path / "restart_flag")
    (tmp_path / "src").mkdir()
    return tmp_path


@pytest.fixture
def source(sandbox):
    p = sandbox / "src" / "target.py"
    p.write_text(GOOD)
    return p


class TestBuilderContract:
    def test_module_exports_every_name_the_daemon_calls(self):
        for name in ("list_source_files", "read_source", "write_source",
                     "syntax_check", "revert", "list_backups",
                     "schedule_restart", "check_restart_flag",
                     "build_history", "apply_patch", "inject_after"):
            assert hasattr(builder, name), f"the daemon calls _builder.{name}"

    def test_importing_the_module_is_silent(self, capsys):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_builder_silence_probe", MODULES_DIR / "nova_self_builder.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = capsys.readouterr()
        assert out.out == "" and out.err == "", f"import printed: {out!r}"

    def test_read_source_of_a_missing_file_returns_an_error_dict(self, sandbox):
        """daemon:4621 returns this straight to the socket."""
        out = builder.read_source("does_not_exist.py")
        assert "error" in out and "content" not in out


class TestSyntaxCheckHappensBeforeTheWrite:
    """The single most important property in the module.

    A syntactically broken proposal must never reach the file. If it does, and
    the file is one the daemon imports, the next restart fails — and the crash
    guard's window is the only thing standing between that and a loop.
    """

    def test_broken_content_is_refused(self, source):
        out = builder.write_source(str(source), BROKEN)
        assert out["ok"] is False
        assert "syntax" in out["error"].lower()

    def test_and_the_original_file_is_untouched(self, source):
        builder.write_source(str(source), BROKEN)
        assert source.read_text() == GOOD, (
            "a syntactically invalid proposal overwrote the original — the "
            "check ran after the write, or not at all"
        )

    def test_no_backup_is_taken_for_a_refused_write(self, sandbox, source):
        """Refusing before backing up keeps the backup directory meaningful:
        every file in it corresponds to a change that actually happened."""
        builder.write_source(str(source), BROKEN)
        assert builder.list_backups() == []

    def test_valid_content_is_written(self, source):
        out = builder.write_source(str(source), ALSO_GOOD)
        assert out["ok"] is True, out
        assert source.read_text() == ALSO_GOOD

    def test_a_non_python_file_skips_the_syntax_check(self, sandbox):
        p = sandbox / "src" / "notes.md"
        p.write_text("# notes\n")
        out = builder.write_source(str(p), "# other notes\n")
        assert out["ok"] is True


class TestBackupBeforeWrite:
    def test_a_backup_is_taken_and_reported(self, source):
        out = builder.write_source(str(source), ALSO_GOOD)
        assert out["backup"], "write_source reported no backup path"
        assert Path(out["backup"]).exists()

    def test_the_backup_holds_the_pre_write_content(self, source):
        out = builder.write_source(str(source), ALSO_GOOD)
        assert Path(out["backup"]).read_text() == GOOD, (
            "the backup captured the new content, not the original — a revert "
            "would restore the change it was meant to undo"
        )

    def test_backups_accumulate_rather_than_overwrite(self, source):
        """Two writes in the same second must produce two backups.

        They did not until 2026-09-03: the backup timestamp was second-
        resolution, so the second write reused the first's filename and
        shutil.copy2 overwrote it. Losing a backup is the smaller half of the
        problem — the surviving file then held the *intermediate* content, so
        revert() would restore the very change it was asked to undo. Both
        writes here land inside one second deliberately; that is the case that
        used to fail.
        """
        builder.write_source(str(source), ALSO_GOOD)
        builder.write_source(str(source), "def f():\n    return 3\n")
        backups = builder.list_backups()
        assert len(backups) >= 2, (
            f"two writes produced {len(backups)} backup(s) — timestamps are "
            f"colliding and one was overwritten"
        )

    def test_revert_after_two_writes_in_one_second_undoes_only_the_last(self, source):
        """The consequence of the collision, pinned directly."""
        builder.write_source(str(source), ALSO_GOOD)
        builder.write_source(str(source), "def f():\n    return 3\n")
        builder.revert(str(source))
        assert source.read_text() == ALSO_GOOD, (
            "revert skipped past the intermediate state — the backup holding "
            "it was overwritten by a colliding timestamp"
        )

    def test_writing_a_new_file_needs_no_backup(self, sandbox):
        p = sandbox / "src" / "brand_new.py"
        out = builder.write_source(str(p), GOOD)
        assert out["ok"] is True
        assert out["backup"] == ""


class TestRevert:
    def test_restores_the_previous_content(self, source):
        builder.write_source(str(source), ALSO_GOOD)
        assert source.read_text() == ALSO_GOOD

        out = builder.revert(str(source))
        assert out["ok"] is True, out
        assert source.read_text() == GOOD

    def test_restores_the_most_recent_backup_not_the_oldest(self, source):
        # No sleep needed: backup timestamps carry microseconds, so two writes
        # in the same second are still ordered. This test slept for 1.05s until
        # 2026-09-03 to work around the second-resolution timestamp that has
        # since been fixed.
        builder.write_source(str(source), ALSO_GOOD)                     # backs up GOOD
        builder.write_source(str(source), "def f():\n    return 3\n")    # backs up ALSO_GOOD

        builder.revert(str(source))
        assert source.read_text() == ALSO_GOOD, (
            "revert restored an older backup — one undo should step back one "
            "change, not all of them"
        )

    def test_no_backups_reports_an_error_rather_than_raising(self, source):
        out = builder.revert(str(source))
        assert out["ok"] is False
        assert "error" in out

    def test_list_backups_can_filter_by_file(self, sandbox, source):
        other = sandbox / "src" / "other.py"
        other.write_text(GOOD)
        builder.write_source(str(source), ALSO_GOOD)
        builder.write_source(str(other), ALSO_GOOD)

        assert len(builder.list_backups()) >= 2
        only = builder.list_backups("target.py")
        assert only and all("target" in b["file"] for b in only)


class TestRestartFlag:
    """Consumed on read — that is what stops a restart becoming a loop."""

    def test_scheduling_writes_the_flag(self, sandbox):
        out = builder.schedule_restart(5)
        assert out["ok"] is True and out["restart_in"] == 5
        assert builder.RESTART_FLAG.exists()

    def test_checking_returns_the_delay(self, sandbox):
        builder.schedule_restart(7)
        assert builder.check_restart_flag() == 7

    def test_checking_consumes_the_flag(self, sandbox):
        """The daemon polls this every loop. A flag that survives being read
        restarts the Cathedral on every pass — an unrecoverable loop, and one
        the crash guard cannot help with because each boot is 'successful'."""
        builder.schedule_restart(3)
        assert builder.check_restart_flag() == 3
        assert builder.check_restart_flag() == 0, "the flag was not consumed"
        assert not builder.RESTART_FLAG.exists()

    def test_no_flag_means_zero(self, sandbox):
        assert builder.check_restart_flag() == 0

    def test_a_corrupt_flag_is_removed_not_retried_forever(self, sandbox):
        builder.RESTART_FLAG.write_text("not a number")
        assert builder.check_restart_flag() == 3
        assert not builder.RESTART_FLAG.exists(), (
            "an unparseable flag survived the read — the daemon would restart "
            "on it every loop, forever"
        )

    def test_the_delay_is_never_below_one_second(self, sandbox):
        builder.RESTART_FLAG.write_text("0")
        assert builder.check_restart_flag() >= 1


class TestPatchHelpers:
    def test_apply_patch_replaces_the_target(self, source):
        out = builder.apply_patch(str(source), "return 1", "return 42")
        assert out["ok"] is True, out
        assert "return 42" in source.read_text()

    def test_apply_patch_replaces_only_the_first_occurrence(self, sandbox):
        p = sandbox / "src" / "twice.py"
        p.write_text("x = 1\ny = 1\n")
        builder.apply_patch(str(p), "1", "2")
        assert p.read_text() == "x = 2\ny = 1\n", (
            "apply_patch replaced every occurrence — a targeted change became "
            "a global one"
        )

    def test_a_missing_target_is_reported_not_silently_ignored(self, source):
        out = builder.apply_patch(str(source), "not in the file", "x")
        assert out["ok"] is False
        assert "not found" in out["error"].lower()
        assert source.read_text() == GOOD

    def test_a_patch_producing_broken_syntax_is_refused(self, source):
        """apply_patch routes through write_source, so it inherits the syntax
        gate. Pinned separately because a future refactor could bypass it."""
        out = builder.apply_patch(str(source), "def f():", "def f(:")
        assert out["ok"] is False
        assert source.read_text() == GOOD

    def test_inject_after_inserts_at_the_anchor(self, source):
        out = builder.inject_after(str(source), "def f():", "    # injected")
        assert out["ok"] is True, out
        text = source.read_text()
        assert "# injected" in text
        assert text.index("def f():") < text.index("# injected")

    def test_inject_after_reports_a_missing_anchor(self, source):
        out = builder.inject_after(str(source), "no such anchor", "x = 1")
        assert out["ok"] is False
        assert "not found" in out["error"].lower()


class TestBuildLog:
    def test_a_write_is_recorded(self, sandbox, source):
        builder.write_source(str(source), ALSO_GOOD)
        history = builder.build_history()
        assert history and history[0]["event"] == "write_source"
        assert history[0]["path"].endswith("target.py")

    def test_a_revert_is_recorded(self, sandbox, source):
        builder.write_source(str(source), ALSO_GOOD)
        builder.revert(str(source))
        assert any(e["event"] == "revert" for e in builder.build_history())

    def test_history_is_newest_first(self, sandbox, source):
        builder.write_source(str(source), ALSO_GOOD)
        builder.schedule_restart(3)
        assert builder.build_history()[0]["event"] == "restart_scheduled"

    def test_a_malformed_line_does_not_break_history(self, sandbox, source):
        """Phoenix parses this log for continuity; one bad line must not take
        the whole history with it."""
        builder.write_source(str(source), ALSO_GOOD)
        with open(builder.BUILD_LOG, "a") as f:
            f.write("this is not json\n")
        assert builder.build_history(), "one unparseable line emptied the history"

    def test_no_log_file_returns_an_empty_list(self, sandbox):
        assert builder.build_history() == []
