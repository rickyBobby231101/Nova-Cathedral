"""The self-edit reject list — which files the evolution loop may never rewrite.

`_SELF_EDIT_PROTECTED` had no test coverage at all before this file, despite
being the only thing standing between the autonomous `code_evolve` loop and
the daemon entrypoint it runs as.

Two of the three entries are structural (the live entrypoint, the rollback
mechanism). The third, oracle_module.py, is empirical: it is the loop's most
frequent target and its edits have repeatedly broken the `oracle` command in
ways nothing caught, because a broken plugin fails silently inside the
daemon's `except Exception: pass` instead of crashing the process the crash
guard watches.
"""
import nova_cathedral_daemon as mod

import pytest


class TestProtectedSet:
    def test_the_three_protected_files(self):
        assert set(mod._SELF_EDIT_PROTECTED) == {
            "nova_cathedral_daemon.py",
            "nova_self_builder.py",
            "oracle_module.py",
        }

    def test_every_entry_explains_itself(self):
        """The refusal quotes these, so an empty reason would be a bare error."""
        for name, reason in mod._SELF_EDIT_PROTECTED.items():
            assert isinstance(reason, str) and len(reason) > 20, name


class TestSelfEvolveRefuses:
    """The enforcement site, which is the only thing that actually matters."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("name", [
        "nova_cathedral_daemon.py",
        "nova_self_builder.py",
        "oracle_module.py",
    ])
    async def test_protected_file_is_refused(self, nova, name):
        r = await nova._self_evolve_file(f"/any/path/to/{name}", "improve it")
        assert "error" in r
        assert "excluded from self-modification" in r["error"]
        assert name in r["error"]

    @pytest.mark.asyncio
    async def test_refusal_carries_the_specific_reason(self, nova):
        r = await nova._self_evolve_file("/x/oracle_module.py", "improve it")
        # Not the daemon-entrypoint reason — the oracle's own.
        assert "most frequent target" in r["error"]
        assert "crash loop" not in r["error"]

    @pytest.mark.asyncio
    async def test_protection_is_by_basename_not_full_path(self, nova):
        """The loop picks targets by scanning directories, so the same file
        arrives under different paths."""
        for path in ("oracle_module.py",
                     "./Cathedral/nova/plugins/oracle_module.py",
                     "/home/daniel/Nova-Cathedral/Cathedral/nova/plugins/oracle_module.py"):
            r = await nova._self_evolve_file(path, "improve it")
            assert "error" in r, path

    @pytest.mark.asyncio
    async def test_unprotected_file_is_not_refused_by_the_guard(self, nova, monkeypatch):
        """The guard must not become a blanket ban — an ordinary module still
        reaches the builder. Stopped at the read step so no LLM call happens.
        """
        monkeypatch.setattr(mod, "_BUILDER_AVAILABLE", True)
        monkeypatch.setattr(
            mod._builder, "read_source",
            lambda path: {"error": "sentinel: reached the builder"},
        )
        r = await nova._self_evolve_file("/x/some_ordinary_module.py", "improve it")
        assert r["error"] == "sentinel: reached the builder", (
            "an unprotected file was blocked before reaching the builder"
        )

    @pytest.mark.asyncio
    async def test_guard_runs_before_the_builder_availability_check(self, nova, monkeypatch):
        """Protection must not depend on an optional module being importable —
        a self-edit that broke nova_self_builder shouldn't also disable the
        list that protects nova_self_builder."""
        monkeypatch.setattr(mod, "_BUILDER_AVAILABLE", False)
        r = await nova._self_evolve_file("/x/oracle_module.py", "improve it")
        assert "excluded from self-modification" in r["error"], (
            "with the builder unavailable the guard was skipped; a protected "
            "file must be refused as protected, not as 'module not available'"
        )
