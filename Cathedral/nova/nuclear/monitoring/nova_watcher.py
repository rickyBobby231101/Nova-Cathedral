#!/usr/bin/env python3
import os, hashlib, sqlite3, logging, threading, time
from pathlib import Path
log = logging.getLogger("nova_watcher")
FEED_DIR = Path.home() / "nova_cathedral" / "feed"
MEM_DB = Path.home() / "nova_cathedral" / "data" / "nova_memory.db"
SEEN_FILE = Path.home() / "nova_cathedral" / "data" / ".watcher_seen"

def _seen():
    if SEEN_FILE.exists():
        return set(SEEN_FILE.read_text().splitlines())
    return set()

def _mark_seen(path):
    seen = _seen()
    seen.add(str(path))
    SEEN_FILE.write_text("\n".join(seen))

def _ingest(filepath):
    try:
        text = Path(filepath).read_text(errors="ignore")
        if len(text.strip()) < 20:
            return
        h = hashlib.md5(text.encode()).hexdigest()
        with sqlite3.connect(MEM_DB) as c:
            exists = c.execute("SELECT id FROM knowledge WHERE source_hash=?", (h,)).fetchone()
            if exists:
                return
            chunks = [text[i:i+800] for i in range(0, min(len(text), 8000), 800)]
            for chunk in chunks:
                ch = hashlib.md5(chunk.encode()).hexdigest()
                c.execute(
                    "INSERT OR IGNORE INTO knowledge (ts,source,source_hash,content,tags) VALUES (datetime(),?,?,?,?)",
                    (str(filepath), ch, chunk, "[]")
                )
        log.info(f"[📥] Ingested: {Path(filepath).name} ({len(chunks)} chunks)")
    except Exception as e:
        log.warning(f"Ingest error {filepath}: {e}")

def _watch_loop():
    log.info(f"[👁] Watching feed dir: {FEED_DIR}")
    while True:
        try:
            seen = _seen()
            for root, _, files in os.walk(FEED_DIR):
                for f in files:
                    if f.startswith(".") or f.endswith((".db",".sock",".pyc")):
                        continue
                    path = str(Path(root) / f)
                    if path not in seen:
                        _ingest(path)
                        _mark_seen(path)
        except Exception as e:
            log.warning(f"Watcher error: {e}")
        time.sleep(60)

def run(context):
    FEED_DIR.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=_watch_loop, daemon=True).start()
    log.info("[✔] Feed watcher active — scanning every 60s")
