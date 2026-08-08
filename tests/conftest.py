import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DAEMON_DIR = REPO_ROOT / "Cathedral" / "nova" / "daemon"
GUI_DIR    = REPO_ROOT / "Cathedral" / "nova" / "gui"

for p in (DAEMON_DIR, GUI_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import pytest


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
