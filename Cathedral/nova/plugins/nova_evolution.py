#!/usr/bin/env python3
"""
Plugin: nova_evolution
Scans the cathedral folder and ~/nova_cathedral/feed/ for files to learn from.
Stores extracted knowledge in Nova's memory. Runs on every boot.
"""

import os
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

try:
    import nova_memory as mem
except ImportError:
    mem = None

CATHEDRAL_DIR = Path.home() / "nova_cathedral"
FEED_DIR      = CATHEDRAL_DIR / "feed"
CONSUMED_DIR  = FEED_DIR / "consumed"

# File types Nova will read
READABLE = {".py", ".md", ".txt", ".json", ".yaml", ".log"}

# Paths to skip
SKIP_DIRS = {"__pycache__", ".git", "data", "consumed"}


def _chunk(text: str, size: int = 800) -> list:
    """Split text into overlapping chunks for storage."""
    chunks = []
    for i in range(0, len(text), size - 100):
        chunks.append(text[i:i + size])
    return chunks


def _ingest_file(path: Path, label: str = None) -> int:
    """Read a file and store its content as knowledge chunks. Returns count ingested."""
    if mem is None:
        return 0
    try:
        text = path.read_text(errors="ignore").strip()
        if not text:
            return 0
        source = label or str(path.relative_to(Path.home()))
        ext = path.suffix.lower()
        tags = [ext.lstrip("."), "auto-ingested"]
        count = 0
        for chunk in _chunk(text):
            if mem.ingest_knowledge(source, chunk, tags):
                count += 1
        return count
    except Exception as e:
        print(f"  [evolution] Could not read {path.name}: {e}")
        return 0


def run(context):
    if mem is None:
        print("[evolution] nova_memory not available — skipping.")
        return

    total_new = 0

    # 1. Scan cathedral directory (py/md files — source of truth)
    print("🧬 Evolution engine scanning cathedral...")
    for path in sorted(CATHEDRAL_DIR.rglob("*")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in READABLE:
            n = _ingest_file(path)
            if n:
                print(f"  📄 Learned from {path.name} ({n} chunks)")
                total_new += n

    # 2. Consume feed/ directory — drop any file here for Nova to absorb
    if FEED_DIR.exists():
        CONSUMED_DIR.mkdir(exist_ok=True)
        for path in sorted(FEED_DIR.iterdir()):
            if path.is_file() and path.suffix in READABLE:
                n = _ingest_file(path, label=f"feed/{path.name}")
                if n:
                    print(f"  🍃 Consumed feed: {path.name} ({n} chunks)")
                    total_new += n
                    # Move to consumed so it isn't re-read next boot
                    path.rename(CONSUMED_DIR / path.name)

    # 3. Log the evolution event
    mem.log_evolution(
        "boot_scan",
        json.dumps({"new_chunks": total_new, "run_id": context.get("run_id")})
    )

    s = mem.stats()
    print(f"🧬 Evolution complete — {total_new} new chunks | "
          f"total knowledge: {s['knowledge_chunks']} chunks across {len(s['sources'])} sources")
