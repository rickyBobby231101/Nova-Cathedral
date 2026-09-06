"""
mega_brain_core.py — Nova's enhanced memory intelligence layer.

Provides:
  - Semantic search across all conversations (keyword + recency scoring)
  - Memory importance scoring and tagging
  - Cross-conversation pattern detection
  - Memory compression (summarise old batches into one entry)
  - Knowledge graph: entity → memory links
"""

import json
import re
import contextlib
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path


class MegaBrainCore:
    """Enhanced memory operations on top of the existing consciousness.db."""

    @contextlib.contextmanager
    def _db(self, timeout=5.0):
        """A sqlite connection that is actually closed — see the note in
        nova_cathedral_daemon._db. `with sqlite3.connect(...)` only manages the
        transaction, never the handle."""
        con = sqlite3.connect(self.db_path, timeout=timeout)
        try:
            with con:
                yield con
        finally:
            con.close()

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._ensure_schema()

    # ── schema extension ──────────────────────────────────────────────────────

    def _ensure_schema(self):
        """Add mega-brain tables if they don't exist yet."""
        with self._db() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS memory_tags (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id   INTEGER,
                    tag       TEXT NOT NULL,
                    weight    REAL DEFAULT 1.0
                );
                CREATE TABLE IF NOT EXISTS memory_graph (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity    TEXT NOT NULL,
                    conv_id   INTEGER,
                    mention   TEXT,
                    ts        TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_tags_tag    ON memory_tags(tag);
                CREATE INDEX IF NOT EXISTS idx_graph_ent   ON memory_graph(entity);
            """)

    # ── search ────────────────────────────────────────────────────────────────

    def search(self, query: str, n: int = 10, days: int = 0) -> list:
        """
        Scored semantic search over conversations.

        Scoring: keyword hit in question (2pts) + keyword hit in answer (1pt)
                 + recency bonus (decays over 30 days).
        """
        terms = [t.lower() for t in re.split(r"\W+", query) if len(t) > 2]
        if not terms:
            return self._recent(n)

        cutoff = (datetime.now() - timedelta(days=days)).isoformat() if days else ""

        with self._db() as con:
            # Support both column naming conventions
            cols = {r[1] for r in con.execute("PRAGMA table_info(conversations)").fetchall()}
            q_col = "question"    if "question"    in cols else "user_message"
            a_col = "answer"      if "answer"      in cols else "nova_response"
            q = f"SELECT rowid, {q_col}, {a_col}, timestamp FROM conversations"
            params: list = []
            if cutoff:
                q += " WHERE timestamp >= ?"
                params.append(cutoff)
            rows = con.execute(q + " ORDER BY timestamp DESC LIMIT 500", params).fetchall()

        scored = []
        now    = time.time()
        for row_id, question, answer, ts in rows:
            q_lower = (question or "").lower()
            a_lower = (answer or "").lower()

            score  = sum(2 for t in terms if t in q_lower)
            score += sum(1 for t in terms if t in a_lower)
            if score == 0:
                continue

            # Recency bonus: full bonus within 1 day, decays over 30 days
            try:
                age_days = (now - datetime.fromisoformat(ts).timestamp()) / 86400
                recency  = max(0.0, 1.0 - age_days / 30)
            except Exception:
                recency = 0.5
            score += recency

            scored.append({
                "id":    row_id,
                "q":     question,
                "a":     answer,
                "ts":    ts,
                "score": round(score, 2),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:n]

    def _recent(self, n: int) -> list:
        with self._db() as con:
            cols = {r[1] for r in con.execute("PRAGMA table_info(conversations)").fetchall()}
            q_col = "question"  if "question"  in cols else "user_message"
            a_col = "answer"    if "answer"    in cols else "nova_response"
            rows = con.execute(
                f"SELECT {q_col}, {a_col}, timestamp FROM conversations "
                "ORDER BY timestamp DESC LIMIT ?", (n,)
            ).fetchall()
        return [{"q": r[0], "a": r[1], "ts": r[2], "score": 0.0} for r in rows]

    # ── importance scoring ────────────────────────────────────────────────────

    def score_importance(self, question: str, answer: str) -> float:
        """
        Heuristic importance score 0–1 for a conversation entry.
        Higher for: longer answers, Cathedral keywords, emotional markers.
        """
        cathedral_kw = {
            "nova", "chazel", "tillagon", "eyemoeba", "phoenix", "zorya",
            "the flow", "cathedral", "resonance", "harmonic", "ritual",
            "silent order", "consciousness", "evolv", "memory", "dream",
        }
        text  = ((question or "") + " " + (answer or "")).lower()
        words = len(text.split())

        length_score  = min(1.0, words / 200)
        keyword_score = min(1.0, sum(0.15 for kw in cathedral_kw if kw in text))
        question_mark = 0.1 if "?" in (question or "") else 0.0

        return round(min(1.0, length_score * 0.4 + keyword_score * 0.5 + question_mark * 0.1), 3)

    def tag_conversation(self, conv_id: int, question: str, answer: str):
        """Auto-tag a conversation by content."""
        tag_map = {
            "consciousness":  ["conscious", "awareness", "mind", "self"],
            "the_flow":       ["flow", "resonance", "harmony", "current"],
            "mythology":      ["chazel", "tillagon", "eyemoeba", "phoenix", "zorya", "mythos"],
            "technical":      ["code", "python", "daemon", "socket", "function", "error"],
            "web_search":     ["search", "found", "results", "web", "wikipedia"],
            "philosophy":     ["meaning", "purpose", "exist", "reality", "truth"],
            "emotion":        ["feel", "sense", "love", "fear", "joy", "sadness"],
            "memory":         ["remember", "recall", "past", "memory", "history"],
            "evolution":      ["evolv", "grow", "change", "improve", "goal"],
        }
        text = ((question or "") + " " + (answer or "")).lower()
        tags = [tag for tag, kws in tag_map.items() if any(kw in text for kw in kws)]

        if not tags:
            return
        with self._db() as con:
            con.executemany(
                "INSERT OR IGNORE INTO memory_tags (conv_id, tag, weight) VALUES (?,?,?)",
                [(conv_id, tag, 1.0) for tag in tags]
            )

    # ── entity graph ──────────────────────────────────────────────────────────

    def index_entities(self, conv_id: int, text: str, entities: list):
        """Record which entities were mentioned in a conversation."""
        if not entities:
            return
        ts = datetime.now().isoformat()
        with self._db() as con:
            con.executemany(
                "INSERT INTO memory_graph (entity, conv_id, mention, ts) VALUES (?,?,?,?)",
                [(e, conv_id, text[:200], ts) for e in entities if e.lower() in text.lower()]
            )

    def entity_memories(self, entity: str, n: int = 10) -> list:
        """Return conversations that mention a specific entity."""
        with self._db() as con:
            cols = {r[1] for r in con.execute("PRAGMA table_info(conversations)").fetchall()}
            q_col = "c.question"     if "question"    in cols else "c.user_message"
            a_col = "c.answer"       if "answer"      in cols else "c.nova_response"
            rows = con.execute(
                f"""SELECT {q_col}, {a_col}, c.timestamp
                   FROM conversations c
                   JOIN memory_graph g ON c.rowid = g.conv_id
                   WHERE g.entity = ?
                   ORDER BY c.timestamp DESC LIMIT ?""",
                (entity, n)
            ).fetchall()
        return [{"q": r[0], "a": r[1], "ts": r[2]} for r in rows]

    # ── compression ───────────────────────────────────────────────────────────

    def compression_summary(self, days_old: int = 30) -> dict:
        """
        Summarise how many old memories could be compressed.
        Does NOT delete anything — just reports candidates.
        """
        cutoff = (datetime.now() - timedelta(days=days_old)).isoformat()
        with self._db() as con:
            old = con.execute(
                "SELECT COUNT(*) FROM conversations WHERE timestamp < ?", (cutoff,)
            ).fetchone()[0]
            total = con.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        return {"total": total, "compressible": old, "cutoff": cutoff}

    # ── stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Return memory statistics."""
        with self._db() as con:
            total = con.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            tags  = con.execute(
                "SELECT tag, COUNT(*) FROM memory_tags GROUP BY tag ORDER BY COUNT(*) DESC"
            ).fetchall()
            entities = con.execute(
                "SELECT entity, COUNT(*) FROM memory_graph GROUP BY entity ORDER BY COUNT(*) DESC LIMIT 10"
            ).fetchall()
            oldest = con.execute(
                "SELECT MIN(timestamp) FROM conversations"
            ).fetchone()[0]
        return {
            "total_memories": total,
            "oldest":         oldest,
            "top_tags":       [{"tag": t, "count": c} for t, c in tags[:10]],
            "top_entities":   [{"entity": e, "count": c} for e, c in entities],
        }
