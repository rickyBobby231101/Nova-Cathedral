#!/usr/bin/env python3
"""
nova_self_builder.py — Nova's self-modification system.

Nova can read, analyze, propose, write, test, and apply changes to her own
source code. Every modification is backed up first. The blueprint rule applies:
"No chaos rebuilds. Controlled, step-by-step execution only."

Workflow:
  1. read_source(path)            — read a file
  2. propose_patch(path, intent)  — LLM generates a targeted change
  3. write_source(path, content)  — write with backup + syntax check
  4. syntax_check(path)           — py_compile validation
  5. schedule_restart()           — write restart flag; daemon picks it up
  6. revert(path)                 — restore last backup
"""

import ast
import importlib.util
import os
import py_compile
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path


NOVA_ROOT    = Path(__file__).parent.parent
BACKUP_DIR   = NOVA_ROOT.parent.parent / "cathedral" / "self_builds" / "backups"
BUILD_LOG    = NOVA_ROOT.parent.parent / "cathedral" / "self_builds" / "build_log.jsonl"
RESTART_FLAG = Path("/tmp/nova_self_restart")


# ── source file management ────────────────────────────────────────────────────

def list_source_files() -> list[dict]:
    """Return all Nova Python source files with metadata."""
    files = []
    for path in sorted(NOVA_ROOT.rglob("*.py")):
        # Skip caches and venvs
        if any(p in path.parts for p in ("__pycache__", "venv", "_archive", "site-packages")):
            continue
        try:
            stat = path.stat()
            files.append({
                "path":     str(path),
                "rel":      str(path.relative_to(NOVA_ROOT)),
                "size":     stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "lines":    sum(1 for _ in open(path, errors="replace")),
            })
        except Exception:
            pass
    return files


def read_source(path: str) -> dict:
    """Read a source file. Returns {content, lines, path}."""
    p = Path(path)
    if not p.is_absolute():
        p = NOVA_ROOT / path
    try:
        content = p.read_text(errors="replace")
        return {"content": content, "lines": len(content.splitlines()), "path": str(p)}
    except FileNotFoundError:
        return {"error": f"File not found: {path}"}
    except Exception as e:
        return {"error": str(e)}


def syntax_check(path: str) -> dict:
    """Check Python syntax. Returns {ok, error, path}."""
    p = Path(path)
    if not p.is_absolute():
        p = NOVA_ROOT / path
    try:
        py_compile.compile(str(p), doraise=True)
        return {"ok": True, "path": str(p)}
    except py_compile.PyCompileError as e:
        return {"ok": False, "error": str(e), "path": str(p)}
    except Exception as e:
        return {"ok": False, "error": str(e), "path": str(p)}


def _backup(path: str) -> str:
    """Create a timestamped backup of a file. Returns backup path."""
    p = Path(path)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    bk_name = f"{p.stem}__{ts}{p.suffix}"
    bk_path = BACKUP_DIR / bk_name
    shutil.copy2(p, bk_path)
    return str(bk_path)


def write_source(path: str, content: str,
                 skip_syntax_check: bool = False) -> dict:
    """
    Write modified source to a file.
    - Backs up original first
    - Syntax-checks the new content before writing
    - Logs the modification
    Returns {ok, path, backup, error}
    """
    p = Path(path)
    if not p.is_absolute():
        p = NOVA_ROOT / path

    # Syntax check new content before touching the file
    if not skip_syntax_check and p.suffix == ".py":
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            check = syntax_check(tmp_path)
        finally:
            os.unlink(tmp_path)
        if not check["ok"]:
            return {"ok": False, "path": str(p),
                    "error": f"Syntax error in proposed content: {check['error']}"}

    # Backup original
    backup_path = ""
    if p.exists():
        try:
            backup_path = _backup(str(p))
        except Exception as e:
            return {"ok": False, "path": str(p),
                    "error": f"Backup failed: {e}"}

    # Write new content
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    except Exception as e:
        # Restore backup on write failure
        if backup_path and Path(backup_path).exists():
            shutil.copy2(backup_path, p)
        return {"ok": False, "path": str(p), "error": f"Write failed: {e}"}

    # Log the modification
    _log_build_event("write_source", str(p), backup=backup_path,
                     lines=len(content.splitlines()))

    return {"ok": True, "path": str(p), "backup": backup_path,
            "lines": len(content.splitlines())}


def revert(path: str) -> dict:
    """Restore the most recent backup of a file."""
    p = Path(path)
    if not p.is_absolute():
        p = NOVA_ROOT / path

    stem = p.stem
    backups = sorted(BACKUP_DIR.glob(f"{stem}__*.py"), reverse=True)
    if not backups:
        return {"ok": False, "error": f"No backups found for {stem}"}

    latest = backups[0]
    shutil.copy2(latest, p)
    _log_build_event("revert", str(p), backup=str(latest))
    return {"ok": True, "path": str(p), "restored_from": str(latest)}


def list_backups(path: str = "") -> list[dict]:
    """List available backups, optionally filtered by file name."""
    if not BACKUP_DIR.exists():
        return []
    results = []
    pattern = f"{Path(path).stem}__*.py" if path else "*.py"
    for f in sorted(BACKUP_DIR.glob(pattern), reverse=True):
        results.append({
            "file":     f.name,
            "path":     str(f),
            "size":     f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        })
    return results[:50]


# ── restart ───────────────────────────────────────────────────────────────────

def schedule_restart(delay_secs: int = 3) -> dict:
    """
    Write a restart flag that the daemon's main loop watches.
    The daemon will shut down cleanly and re-exec itself.
    """
    RESTART_FLAG.write_text(str(delay_secs))
    _log_build_event("restart_scheduled", "nova_cathedral_daemon.py",
                     note=f"restart in {delay_secs}s")
    return {"ok": True, "restart_in": delay_secs, "flag": str(RESTART_FLAG)}


def check_restart_flag() -> int:
    """
    Returns delay_secs if restart is pending, else 0.
    Consumes (deletes) the flag on read.
    """
    if RESTART_FLAG.exists():
        try:
            delay = int(RESTART_FLAG.read_text().strip())
            RESTART_FLAG.unlink()
            return max(1, delay)
        except Exception:
            RESTART_FLAG.unlink(missing_ok=True)
            return 3
    return 0


# ── build log ─────────────────────────────────────────────────────────────────

def _log_build_event(event: str, path: str, **kwargs):
    import json
    BUILD_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": datetime.now().isoformat(), "event": event,
             "path": path, **kwargs}
    with open(BUILD_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def build_history(n: int = 30) -> list[dict]:
    """Return recent build log entries."""
    import json
    if not BUILD_LOG.exists():
        return []
    lines = BUILD_LOG.read_text().splitlines()
    entries = []
    for line in reversed(lines[-n*2:]):
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries[:n]


# ── patch helpers ─────────────────────────────────────────────────────────────

def apply_patch(path: str, old: str, new: str) -> dict:
    """
    Replace an exact string in a source file.
    Backs up first. Returns {ok, path, backup, replaced}.
    """
    src_result = read_source(path)
    if "error" in src_result:
        return src_result

    content = src_result["content"]
    if old not in content:
        return {"ok": False, "path": path,
                "error": "Target string not found in file"}

    new_content = content.replace(old, new, 1)
    return write_source(path, new_content)


def inject_after(path: str, anchor: str, insertion: str) -> dict:
    """Insert code immediately after an anchor string in a source file."""
    src_result = read_source(path)
    if "error" in src_result:
        return src_result

    content = src_result["content"]
    idx = content.find(anchor)
    if idx == -1:
        return {"ok": False, "path": path,
                "error": "Anchor string not found in file"}

    insert_at = idx + len(anchor)
    new_content = content[:insert_at] + "\n" + insertion + content[insert_at:]
    return write_source(path, new_content)
