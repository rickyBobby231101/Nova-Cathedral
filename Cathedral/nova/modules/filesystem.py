#!/usr/bin/env python3
"""
Nova filesystem module — full read/write access to the user's files.
Nova can read, search, and write files anywhere under the user's home directory.
Writes outside ~/cathedral/ require explicit allow=True.
"""

import fnmatch
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

HOME       = Path.home()
CATHEDRAL  = HOME / "cathedral"

# When frozen by PyInstaller, __file__ lands inside _internal/ (the bundle), so
# parent.parent would scan bundled third-party packages instead of Nova's code.
# NOVA_SOURCE_ROOT env var lets the service pin the real source tree explicitly.
if os.environ.get("NOVA_SOURCE_ROOT"):
    NOVA_ROOT = Path(os.environ["NOVA_SOURCE_ROOT"])
elif getattr(sys, "frozen", False):
    # Compiled binary — derive from the executable location:
    # dist/nova-daemon/nova-daemon → repo root → Cathedral/nova
    NOVA_ROOT = Path(sys.executable).parent.parent.parent / "Cathedral" / "nova"
else:
    NOVA_ROOT = Path(__file__).parent.parent

# File types Nova can read as text
TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json",
    ".yaml", ".yml", ".toml", ".cfg", ".ini", ".conf", ".sh", ".bash",
    ".zsh", ".fish", ".env", ".log", ".csv", ".xml", ".rst", ".tex",
    ".c", ".cpp", ".h", ".go", ".rs", ".java", ".rb", ".php",
    ".sql", ".r", ".m", ".ipynb",
}


def _safe_path(path_str: str) -> Path:
    """Resolve and validate a path. Returns absolute Path."""
    p = Path(path_str).expanduser().resolve()
    return p


def read_file(path: str, max_bytes: int = 80_000) -> dict:
    """Read a file's contents. Returns {path, content, size, lines, truncated}."""
    p = _safe_path(path)
    try:
        if not p.exists():
            return {"error": f"File not found: {p}"}
        if not p.is_file():
            return {"error": f"Not a file: {p}"}

        size = p.stat().st_size
        if p.suffix.lower() in TEXT_EXTENSIONS or size < max_bytes:
            try:
                content = p.read_text(errors="replace")
                truncated = False
                if len(content.encode()) > max_bytes:
                    content   = content.encode()[:max_bytes].decode(errors="replace")
                    truncated = True
                return {
                    "path":      str(p),
                    "content":   content,
                    "size":      size,
                    "lines":     content.count("\n"),
                    "truncated": truncated,
                }
            except Exception as e:
                return {"error": f"Read error: {e}"}
        else:
            return {
                "path":    str(p),
                "content": f"[Binary file, {size} bytes — cannot display]",
                "size":    size,
                "binary":  True,
            }
    except PermissionError:
        return {"error": f"Permission denied: {p}"}
    except Exception as e:
        return {"error": str(e)}


def write_file(path: str, content: str, backup: bool = True) -> dict:
    """
    Write content to a file.
    If backup=True, saves a .bak copy before overwriting.
    """
    p = _safe_path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        if backup and p.exists():
            bak = p.with_suffix(p.suffix + ".bak")
            shutil.copy2(p, bak)
        p.write_text(content)
        return {
            "path":    str(p),
            "bytes":   len(content.encode()),
            "backed_up": backup and p.exists(),
        }
    except PermissionError:
        return {"error": f"Permission denied: {p}"}
    except Exception as e:
        return {"error": str(e)}


def list_dir(path: str = "~", pattern: str = "*",
             recursive: bool = False, max_entries: int = 200) -> dict:
    """
    List directory contents.
    Returns {path, entries: [{name, type, size, modified}]}
    """
    p = _safe_path(path)
    if not p.exists():
        return {"error": f"Path not found: {p}"}
    if not p.is_dir():
        return {"error": f"Not a directory: {p}"}

    entries = []
    try:
        if recursive:
            items = [x for x in p.rglob(pattern) if not any(
                part.startswith(".") for part in x.relative_to(p).parts
            )]
        else:
            items = list(p.glob(pattern))

        for item in sorted(items)[:max_entries]:
            try:
                stat = item.stat()
                entries.append({
                    "name":     item.name,
                    "path":     str(item),
                    "type":     "dir" if item.is_dir() else "file",
                    "size":     stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "ext":      item.suffix.lower(),
                })
            except Exception:
                pass
    except PermissionError:
        return {"error": f"Permission denied: {p}"}

    return {
        "path":     str(p),
        "entries":  entries,
        "count":    len(entries),
        "truncated": len(entries) == max_entries,
    }


def search_files(pattern: str, root: str = "~",
                 max_results: int = 50, skip_hidden: bool = True) -> dict:
    """
    Find files matching a glob pattern under root.
    pattern examples: '*.py', '**/*.yaml', 'nova_*'
    """
    r = _safe_path(root)
    if not r.exists():
        return {"error": f"Root not found: {r}"}

    results = []
    try:
        for item in r.rglob(pattern):
            if skip_hidden and any(p.startswith(".") for p in item.parts):
                continue
            try:
                stat = item.stat()
                results.append({
                    "path":     str(item),
                    "name":     item.name,
                    "type":     "dir" if item.is_dir() else "file",
                    "size":     stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
                if len(results) >= max_results:
                    break
            except Exception:
                pass
    except Exception as e:
        return {"error": str(e)}

    return {"pattern": pattern, "root": str(r), "results": results, "count": len(results)}


def grep_files(query: str, root: str = "~",
               extensions: list = None, max_results: int = 30,
               case_sensitive: bool = False) -> dict:
    """
    Search file contents for a pattern/keyword.
    Returns matching lines with file path and line number.
    """
    r = _safe_path(root)
    exts = set(extensions or list(TEXT_EXTENSIONS))
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(query, flags)
    except re.error as e:
        return {"error": f"Invalid regex: {e}"}

    matches = []
    try:
        for fpath in r.rglob("*"):
            if not fpath.is_file():
                continue
            if fpath.suffix.lower() not in exts:
                continue
            if any(p.startswith(".") for p in fpath.parts):
                continue
            try:
                content = fpath.read_text(errors="replace")
                for lineno, line in enumerate(content.splitlines(), 1):
                    if pattern.search(line):
                        matches.append({
                            "file":    str(fpath),
                            "line":    lineno,
                            "content": line.strip()[:200],
                        })
                        if len(matches) >= max_results:
                            return {"query": query, "matches": matches,
                                    "count": len(matches), "truncated": True}
            except Exception:
                pass
    except Exception as e:
        return {"error": str(e)}

    return {"query": query, "matches": matches, "count": len(matches)}


def get_info(path: str) -> dict:
    """Get detailed metadata about a file or directory."""
    p = _safe_path(path)
    if not p.exists():
        return {"error": f"Not found: {p}"}
    try:
        stat = p.stat()
        info = {
            "path":      str(p),
            "name":      p.name,
            "type":      "dir" if p.is_dir() else "file",
            "size":      stat.st_size,
            "created":   datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified":  datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "readable":  os.access(p, os.R_OK),
            "writable":  os.access(p, os.W_OK),
        }
        if p.is_file():
            info["extension"] = p.suffix.lower()
            info["is_text"]   = p.suffix.lower() in TEXT_EXTENSIONS
            if info["is_text"] and stat.st_size < 100_000:
                try:
                    content       = p.read_text(errors="replace")
                    info["lines"] = content.count("\n")
                    info["hash"]  = hashlib.md5(content.encode()).hexdigest()
                except Exception:
                    pass
        elif p.is_dir():
            try:
                children      = list(p.iterdir())
                info["children"] = len(children)
                info["subdirs"]  = sum(1 for c in children if c.is_dir())
                info["files"]    = sum(1 for c in children if c.is_file())
            except Exception:
                pass
        return info
    except Exception as e:
        return {"error": str(e)}


def read_nova_source() -> dict:
    """Read Nova's own source files so it can reason about its own code."""
    sources = {}
    for fpath in NOVA_ROOT.rglob("*.py"):
        if any(p.startswith("__pycache__") for p in fpath.parts):
            continue
        rel = str(fpath.relative_to(NOVA_ROOT))
        try:
            content = fpath.read_text(errors="replace")
            sources[rel] = {
                "path":    str(fpath),
                "lines":   content.count("\n"),
                "content": content[:8000],   # first 8k chars
                "truncated": len(content) > 8000,
            }
        except Exception:
            pass
    return {"nova_root": str(NOVA_ROOT), "files": sources, "count": len(sources)}


# Topics arrive from the model, so they can be blank or carry path
# separators. A blank one used to produce the filename ".md", which the
# Weaver skips as a dotfile — 57 research entries accumulated there over four
# months and never reached the graph. A topic with "/" would write outside the
# knowledge directory entirely.
_TOPIC_SAFE_RE = re.compile(r"[^a-z0-9._-]+")
UNCATEGORIZED = "uncategorized"


def topic_filename(topic: str) -> str:
    """Turn a model-supplied topic into a safe, weavable filename stem."""
    stem = _TOPIC_SAFE_RE.sub("_", (topic or "").strip().lower()).strip("._-")
    return stem or UNCATEGORIZED


def append_knowledge(topic: str, content: str) -> dict:
    """Append a knowledge note to Nova's knowledge base file."""
    kb_path = CATHEDRAL / "knowledge" / f"{topic_filename(topic)}.md"
    kb_path.parent.mkdir(parents=True, exist_ok=True)
    ts    = datetime.now().isoformat()
    entry = f"\n\n## {ts}\n\n{content}\n"
    try:
        with open(kb_path, "a") as f:
            f.write(entry)
        return {"path": str(kb_path), "bytes": len(entry)}
    except Exception as e:
        return {"error": str(e)}
