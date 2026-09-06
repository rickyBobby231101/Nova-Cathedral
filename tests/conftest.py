import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DAEMON_DIR  = REPO_ROOT / "Cathedral" / "nova" / "daemon"
GUI_DIR     = REPO_ROOT / "Cathedral" / "nova" / "gui"
# The daemon puts this on sys.path itself at import time, but tests that
# exercise a module directly need it before the daemon is ever imported.
MODULES_DIR = REPO_ROOT / "Cathedral" / "nova" / "modules"

for p in (DAEMON_DIR, GUI_DIR, MODULES_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import pytest


def pytest_configure(config):
    """Put the throwaway test databases on tmpfs when one is available.

    Nearly every test builds a fresh consciousness.db, and init_db() fsyncs
    through a schema script and PRAGMA journal_mode=WAL. On a disk-backed /tmp
    that cost is the entire suite: measured 2026-09-06, 592 tests took 766s
    wall while using 27s of CPU, the process sitting in D state in
    jbd2_log_wait_commit. The same suite on /dev/shm ran in 36s.

    Only a default is set here — an explicit --basetemp on the command line
    still wins, and a system without a writable /dev/shm keeps pytest's normal
    /tmp behaviour. Set NOVA_TEST_TMPFS=0 to opt out.
    """
    if config.option.basetemp is not None:
        return
    if os.environ.get("NOVA_TEST_TMPFS") == "0":
        return
    shm = Path("/dev/shm")
    if not (shm.is_dir() and os.access(shm, os.W_OK)):
        return
    # pytest empties basetemp at session start, so this must be a path nothing
    # else owns — never a shared or pre-existing directory.
    config.option.basetemp = shm / "pytest-nova"


@pytest.fixture
def nova(tmp_path, monkeypatch):
    """A NovaConsciousness instance pointed at a throwaway sqlite db.

    __init__ itself does no I/O (just sets paths/defaults), so it's safe to
    construct directly and then redirect db_path before init_db() creates
    the schema — this never touches the real ~/cathedral database.
    """
    import nova_cathedral_daemon as mod

    n = mod.NovaConsciousness()
    n.db_path = tmp_path / "consciousness.db"
    n.init_db()
    return n
