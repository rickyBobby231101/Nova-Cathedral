#!/usr/bin/env python3
import sqlite3, json, logging, threading, time, os
from pathlib import Path
from datetime import datetime
log = logging.getLogger("nova_evolution2")

DB = Path.home() / "nova_cathedral" / "data" / "evolution.db"

def _init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS evolution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT, event TEXT, detail TEXT, success INTEGER
            );
            CREATE TABLE IF NOT EXISTS capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE, added_ts TEXT, status TEXT DEFAULT 'active'
            );
            CREATE TABLE IF NOT EXISTS interaction_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT, input_snippet TEXT, response_snippet TEXT,
                length INTEGER, keywords TEXT
            );
        """)

def _log_event(event, detail="", success=True):
    with sqlite3.connect(DB) as c:
        c.execute("INSERT INTO evolution_log (ts,event,detail,success) VALUES (?,?,?,?)",
                  (datetime.now().isoformat(), event, detail, int(success)))

def _record_interaction(user_input, response):
    import re
    keywords = ",".join(set(re.findall(r"\b[a-z]{4,}\b", (user_input+" "+response).lower())))[:200]
    with sqlite3.connect(DB) as c:
        c.execute(
            "INSERT INTO interaction_patterns (ts,input_snippet,response_snippet,length,keywords) VALUES (?,?,?,?,?)",
            (datetime.now().isoformat(), user_input[:100], response[:100], len(response), keywords)
        )

def _evolution_report():
    with sqlite3.connect(DB) as c:
        total = c.execute("SELECT COUNT(*) FROM interaction_patterns").fetchone()[0]
        events = c.execute("SELECT COUNT(*) FROM evolution_log").fetchone()[0]
        top_kw = c.execute("""
            SELECT keywords FROM interaction_patterns
            ORDER BY id DESC LIMIT 20
        """).fetchall()
    all_kw = {}
    for row in top_kw:
        for w in row[0].split(","):
            all_kw[w] = all_kw.get(w, 0) + 1
    top = sorted(all_kw.items(), key=lambda x: -x[1])[:5]
    log.info(f"[🧬] Evolution report — {total} interactions, {events} events | top themes: {top}")
    _log_event("evolution_report", f"interactions={total} top={top}")

def _evolution_loop():
    time.sleep(30)
    while True:
        try:
            _evolution_report()
        except Exception as e:
            log.warning(f"Evolution loop error: {e}")
        time.sleep(300)

def run(context):
    _init_db()
    nova = context.get("nova_system")
    if not nova:
        return
    original = nova.receive_input
    def evolved(user_input):
        response = original(user_input)
        try:
            _record_interaction(user_input, response)
        except Exception as e:
            log.warning(f"Record error: {e}")
        return response
    nova.receive_input = evolved
    threading.Thread(target=_evolution_loop, daemon=True).start()
    _log_event("boot", "Evolution engine online")
    log.info("[✔] Evolution engine active — tracking patterns every 5 min")
