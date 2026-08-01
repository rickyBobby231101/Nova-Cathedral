#!/usr/bin/env python3
"""
nova_memory.py — Nova's persistent memory layer
SQLite-backed storage for conversations, learned knowledge, and evolution records.
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / "nova_cathedral" / "data" / "nova_memory.db"


def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT NOT NULL,
                speaker   TEXT NOT NULL,
                message   TEXT NOT NULL,
                module    TEXT
            );

            CREATE TABLE IF NOT EXISTS knowledge (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT NOT NULL,
                source    TEXT NOT NULL,
                source_hash TEXT UNIQUE,
                content   TEXT NOT NULL,
                tags      TEXT
            );

            CREATE TABLE IF NOT EXISTS patterns (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT NOT NULL,
                pattern   TEXT NOT NULL,
                response  TEXT NOT NULL,
                hits      INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS evolution_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        TEXT NOT NULL,
                event     TEXT NOT NULL,
                detail    TEXT
            );
        """)


def log_conversation(speaker: str, message: str, module: str = None):
    with _conn() as c:
        c.execute(
            "INSERT INTO conversations (ts, speaker, message, module) VALUES (?,?,?,?)",
            (datetime.now().isoformat(), speaker, message, module)
        )


def ingest_knowledge(source: str, content: str, tags: list = None):
    """Store a chunk of knowledge from a file or feed. Skips duplicates."""
    source_hash = hashlib.md5(content.encode()).hexdigest()
    with _conn() as c:
        existing = c.execute(
            "SELECT id FROM knowledge WHERE source_hash=?", (source_hash,)
        ).fetchone()
        if existing:
            return False  # already known
        c.execute(
            "INSERT INTO knowledge (ts, source, source_hash, content, tags) VALUES (?,?,?,?,?)",
            (datetime.now().isoformat(), source, source_hash, content,
             json.dumps(tags or []))
        )
    return True


def search_knowledge(query: str, limit: int = 5) -> list:
    """Simple keyword search across stored knowledge."""
    words = query.lower().split()
    with _conn() as c:
        results = []
        for word in words:
            rows = c.execute(
                "SELECT source, content FROM knowledge WHERE lower(content) LIKE ? LIMIT ?",
                (f"%{word}%", limit)
            ).fetchall()
            for row in rows:
                entry = {"source": row["source"], "content": row["content"][:300]}
                if entry not in results:
                    results.append(entry)
        return results[:limit]


def log_evolution(event: str, detail: str = None):
    with _conn() as c:
        c.execute(
            "INSERT INTO evolution_log (ts, event, detail) VALUES (?,?,?)",
            (datetime.now().isoformat(), event, detail)
        )


def stats() -> dict:
    with _conn() as c:
        return {
            "conversations": c.execute("SELECT COUNT(*) FROM conversations").fetchone()[0],
            "knowledge_chunks": c.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0],
            "evolution_events": c.execute("SELECT COUNT(*) FROM evolution_log").fetchone()[0],
            "sources": [r[0] for r in c.execute(
                "SELECT DISTINCT source FROM knowledge ORDER BY source"
            ).fetchall()]
        }


# Auto-init on import
init_db()
