"""Every sqlite connection must actually be closed.

`with sqlite3.connect(...) as con:` reads like it closes the connection. It
does not: it is a TRANSACTION context manager that commits or rolls back on
exit and leaves the handle open, to be reclaimed whenever the refcount happens
to drop. Anything still referencing a cursor, a row, or a traceback frame
defers that indefinitely.

Measured 2026-09-06, before the fix: the live daemon held ~48 open handles to
consciousness.db and spiked to 68 on an evolution cycle; the test suite peaked
at 306 handles across five temp databases and stalled in jbd2_log_wait_commit.

The failure is invisible until you go looking, which is exactly why it needs a
test rather than a code review habit.
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIRS = [REPO_ROOT / "Cathedral" / "nova"]

# The bare pattern, as a `with` statement. A plain `sqlite3.connect(...)`
# assigned to a name and closed in a finally is fine, so only the `with` form
# is banned.
RAW_WITH_CONNECT = re.compile(r"^\s*with\s+sqlite3\.connect\(", re.M)

# Nova rewrites her own source; those files are her output, not the build's.
SKIP_DIRS = {"self_builds", "sandbox_plugins", "__pycache__", ".venv"}


def _source_files():
    for root in SOURCE_DIRS:
        for path in root.rglob("*.py"):
            if SKIP_DIRS & set(path.parts):
                continue
            yield path


@pytest.mark.parametrize("path", sorted(_source_files()), ids=lambda p: p.name)
def test_no_bare_with_sqlite3_connect(path):
    hits = [
        path.read_text().count("\n", 0, m.start()) + 1
        for m in RAW_WITH_CONNECT.finditer(path.read_text())
    ]
    assert not hits, (
        f"{path.relative_to(REPO_ROOT)} lines {hits}: "
        "`with sqlite3.connect(...)` leaves the connection open — it only "
        "manages the transaction. Use the module's `_db()` helper, or "
        "connect and close in a finally."
    )


def test_the_helper_actually_closes(tmp_path):
    """Pin the helper's behaviour, not just its presence."""
    import sqlite3
    import sys

    sys.path.insert(0, str(REPO_ROOT / "Cathedral" / "nova" / "daemon"))
    import nova_cathedral_daemon as mod

    n = mod.NovaConsciousness()
    n.db_path = tmp_path / "consciousness.db"
    n.init_db()

    with n._db() as con:
        con.execute("CREATE TABLE IF NOT EXISTS probe (x)")
        con.execute("INSERT INTO probe VALUES (1)")

    # Committed on exit, exactly as the transaction CM did before.
    with n._db() as con:
        assert con.execute("SELECT count(*) FROM probe").fetchone()[0] == 1

    # And the handle is genuinely closed, not merely out of scope.
    leaked = None
    with n._db() as con:
        leaked = con
    with pytest.raises(sqlite3.ProgrammingError):
        leaked.execute("SELECT 1")


def test_helper_rolls_back_on_error(tmp_path):
    """A raising block must not commit — the old semantics, preserved."""
    import sys

    sys.path.insert(0, str(REPO_ROOT / "Cathedral" / "nova" / "daemon"))
    import nova_cathedral_daemon as mod

    n = mod.NovaConsciousness()
    n.db_path = tmp_path / "consciousness.db"
    n.init_db()
    with n._db() as con:
        con.execute("CREATE TABLE IF NOT EXISTS probe (x)")

    with pytest.raises(ValueError):
        with n._db() as con:
            con.execute("INSERT INTO probe VALUES (99)")
            raise ValueError("boom")

    with n._db() as con:
        assert con.execute("SELECT count(*) FROM probe").fetchone()[0] == 0
