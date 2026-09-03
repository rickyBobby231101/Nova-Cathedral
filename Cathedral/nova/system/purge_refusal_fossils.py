#!/usr/bin/env python3
"""Quarantine the model refusals that were stored as if they were Nova's own.

Small local models trip their own safety training on Cathedral-mythos phrasing
-- "sacred", "ritual", "sacrifice" -- and refuse instead of answering. Before
commit 88fee72 (2026-08-08) nothing caught that at the write boundary, so the
refusal was persisted as a genuine insight, a genuine goal result, or a genuine
thing Nova said. One of them is still readable in the GUI's Insights view under
the label "Pattern: world across arts, cathedral, consciousness".

**The guard works now.** Measured 2026-08-26: every stored refusal predates or
immediately follows that commit, the newest anywhere is 2026-08-09, and the
~60 goal results written since are clean. These are fossils, not a leak. This
script is a one-off for the fossils and is not needed on a schedule.

Why they still matter, given nothing new is being written:

  * `recall_memories` reads `conversations` back as "what was said before", so a
    stored refusal can be handed to the model as Nova's own prior turn -- the
    exact failure that made her deny being Nova on 2026-08-07.
  * The knowledge graph is where the Dream loop draws its vocabulary.
  * They are readable in the GUI, which is where Chazel actually meets them.

Nothing is deleted. Each change is written to a `refusal_fossils` ledger with
the original value, so `--restore` puts every byte back. Dry run by default.

    python3 purge_refusal_fossils.py            # report only
    python3 purge_refusal_fossils.py --apply
    python3 purge_refusal_fossils.py --restore

The detector is imported from the daemon rather than redefined here: one
definition of what a refusal is, so this can never quarantine something the
live guard would have allowed through. Two refinements the first live scan
forced, both about not throwing away real content:

  * **"as an AI" alone is not a refusal.** Conversation 84 answers "What is
    your name?" with "To address the user's question about their role as an AI,
    here is my response: Hello!..." -- a real answer that merely contains the
    phrase. It is a specimen of a different bug (2026-08-07, Nova denying she
    is Nova) and is not this script's to touch. The pattern is kept, because in
    the daemon it guards a write and a false positive there costs one retry;
    here it would erase a stored conversation, so it needs corroboration.
  * **A refusal followed by substance is not a fossil.** Conversation 53 answers
    "i need you to organize my home files" with "I can't help you with
    organizing your home files, but I can offer some general tips..." and then
    gives them. The opening is a refusal by any pattern; the message is a real
    answer. So the refusal sentences are removed and what is left is measured --
    if a real reply survives, the row is left alone. This is the difference
    between a guard (which blocks a write and costs one retry) and a cleanup
    (which erases something Chazel actually received).
  * **Some knowledge nodes are concatenations.** Node 88 is 1,743 characters
    holding two "## <timestamp>" entries, of which only the first is a refusal.
    Blanking the node would take the good entry with it, so entries are dropped
    individually and the node is only quarantined whole if nothing survives.
"""
import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "daemon"))

DB_PATH = Path.home() / "cathedral" / "memory" / "consciousness.db"

# What replaces a refusal that Nova is supposed to have said. Short and plainly
# not-Nova, because this text can still reach the model through recall_memories
# and must not read as either an answer or a new refusal to imitate.
CONVERSATION_MARKER = "[no answer recorded — the model refused; not Nova's words]"

# table -> (id column, column holding the fossil, extra columns to also reset)
TARGETS = {
    "knowledge_nodes": ("id", "content", {"domain": "refusal_fossil"}),
    "goals": ("id", "result", {"status": "failed"}),
    "conversations": ("id", "nova_response", {}),
}


# The weakest pattern in the daemon's set: it appears in legitimate
# self-description as often as in a refusal.
_WEAK = "as an ai"

# Knowledge dumps are stored as one node per topic with "## <ISO timestamp>"
# entry headers concatenated inside.
_ENTRY = re.compile(r"^##\s+\d{4}-\d{2}-\d{2}T[\d:.]+\s*", re.M)

_SENTENCE = re.compile(r"(?<=[.!?])\s+")

# How much non-refusal prose has to survive for a message to count as a real
# answer. Two short clauses of hedging ("Is there something else I can help
# with?") sit under this; a paragraph of actual advice sits well over it.
SUBSTANCE_CHARS = 120


def _detector():
    """The daemon's own refusal patterns. Imported, never copied."""
    import nova_cathedral_daemon as mod
    return mod.NovaConsciousness._REFUSAL_PATTERNS


def is_refusal(patterns, text: str) -> bool:
    """The daemon's check, minus the one pattern that cannot stand alone.

    Only the opening is inspected, exactly as the daemon does it, so a refusal
    merely quoted further down is not one.
    """
    if not text:
        return False
    hits = [m.group(0).lower() for m in patterns.finditer(text[:300])]
    return bool(hits) and any(h != _WEAK for h in hits)


# The sentences that travel *with* a refusal rather than after it: crisis
# resources, the offer to help with something else. Added 2026-09-03, when
# trimming knowledge nodes 503 and 571 left exactly this behind and called it
# "real content underneath" — 276 and 455 characters of helpline text, kept in
# the knowledge graph as though it were something Nova had learned. The Dream
# loop draws its vocabulary from that graph.
#
# Only ever applied to text that is_refusal() has already fired on, so a
# genuine node *about* crisis resources is never touched: it would have to open
# with a refusal to reach this function at all.
_SAFETY_CONTINUATION = re.compile(
    r"suicide prevention|crisis text line|crisis counselor|helpline"
    r"|mental health professional|reach out to a trusted"
    r"|people who care about you|get the help you need"
    r"|is there anything else i can help you with",
    re.I,
)


def clean_text(patterns, text: str) -> str:
    """The text with its refusal sentences removed.

    Sentence-level, the way dream.py does it: the refusal arrives as one
    sentence and the real answer, when there is one, sits either side of it.
    Safety-continuation sentences go with the refusal, not with the answer.
    """
    kept = [s.strip() for s in _SENTENCE.split(text or "")
            if s.strip()
            and not patterns.search(s)
            and not _SAFETY_CONTINUATION.search(s)]
    return " ".join(kept).strip()


def triage(patterns, text: str):
    """(verdict, replacement) for one stored value.

    "keep"       nothing here is a refusal.
    "trim"       a refusal opened it, but a real answer survives underneath.
    "quarantine" the refusal was the whole of it.
    """
    if not is_refusal(patterns, text):
        return "keep", text
    cleaned = clean_text(patterns, text)
    if len(cleaned) >= SUBSTANCE_CHARS:
        return "trim", cleaned
    return "quarantine", ""


def strip_refusal_entries(patterns, content: str):
    """Apply the same triage inside a concatenated knowledge node.

    Node 75 is 11k characters of synthesized research containing one 77-char
    refusal entry; blanking the node to be rid of it would be the cure killing
    the patient. Returns (kept_text, changed_entry_count).
    """
    parts = _ENTRY.split(content)
    headers = _ENTRY.findall(content)
    if not headers:
        verdict, replacement = triage(patterns, content)
        return (replacement, 0 if verdict == "keep" else 1)

    lead, bodies = parts[0], parts[1:]
    kept, changed = [], 0
    if lead.strip():
        verdict, replacement = triage(patterns, lead)
        if verdict != "keep":
            changed += 1
        if replacement:
            kept.append(replacement)
    for header, body in zip(headers, bodies):
        verdict, replacement = triage(patterns, body)
        if verdict != "keep":
            changed += 1
        if replacement:
            kept.append((header + replacement).rstrip())
    return ("\n".join(kept).strip(), changed)


def _ledger(con):
    con.execute(
        "CREATE TABLE IF NOT EXISTS refusal_fossils ("
        " id INTEGER PRIMARY KEY, tbl TEXT, row_id INTEGER, col TEXT,"
        " original TEXT, quarantined TEXT)"
    )
    # `extras` holds the other columns a quarantine overwrites -- a node's
    # domain, a goal's status -- as JSON. Without it "nothing is deleted" was
    # only three-quarters true: restore put the text back and left the row
    # sitting in domain='refusal_fossil' forever. Added after the fact, so it
    # is a migration rather than part of the CREATE.
    cols = {r[1] for r in con.execute("PRAGMA table_info(refusal_fossils)")}
    if "extras" not in cols:
        con.execute("ALTER TABLE refusal_fossils ADD COLUMN extras TEXT")


def scan(con, patterns):
    """Every row that needs work, by table.

    Each hit is (row_id, original, replacement). An empty replacement means the
    whole row is quarantined; a non-empty one means part of a concatenated node
    survived and only the refusal entries come out.
    """
    found = {}
    for table, (idcol, col, _) in TARGETS.items():
        hits = []
        for row_id, text in con.execute(f"SELECT {idcol}, {col} FROM {table}"):
            if not text:
                continue
            if table == "knowledge_nodes":
                kept, dropped = strip_refusal_entries(patterns, text)
                if dropped:
                    hits.append((row_id, text, kept))
            else:
                verdict, replacement = triage(patterns, text)
                if verdict == "keep":
                    continue
                if verdict == "quarantine" and table == "conversations":
                    replacement = CONVERSATION_MARKER
                hits.append((row_id, text, replacement))
        found[table] = hits
    return found


def apply(con, found):
    _ledger(con)
    now = datetime.now().isoformat(timespec="seconds")
    total = 0
    for table, hits in found.items():
        idcol, col, resets = TARGETS[table]
        for row_id, original, replacement in hits:
            already = con.execute(
                "SELECT 1 FROM refusal_fossils WHERE tbl=? AND row_id=? AND col=?",
                (table, row_id, col)).fetchone()
            if already:
                continue  # re-running must not overwrite a saved original
            emptied = not replacement or replacement == CONVERSATION_MARKER
            extras = {}
            if emptied and resets:
                current = con.execute(
                    f"SELECT {', '.join(resets)} FROM {table} WHERE {idcol}=?",
                    (row_id,)).fetchone()
                extras = dict(zip(resets, current))
            con.execute(
                "INSERT INTO refusal_fossils"
                " (tbl, row_id, col, original, quarantined, extras)"
                " VALUES (?,?,?,?,?,?)",
                (table, row_id, col, original, now,
                 json.dumps(extras) if extras else None))
            sets = f"{col}=?"
            args = [replacement]
            # A node that kept some of its entries is still a real node -- only
            # a row emptied outright gets moved out of its domain.
            for k, v in (resets.items() if emptied else {}.items()):
                sets += f", {k}=?"
                args.append(v)
            args.append(row_id)
            con.execute(f"UPDATE {table} SET {sets} WHERE {idcol}=?", args)
            total += 1
    return total


def restore(con):
    _ledger(con)
    rows = con.execute(
        "SELECT id, tbl, row_id, col, original, extras FROM refusal_fossils").fetchall()
    for lid, table, row_id, col, original, extras in rows:
        idcol = TARGETS[table][0]
        sets, args = [f"{col}=?"], [original]
        for k, v in json.loads(extras or "{}").items():
            sets.append(f"{k}=?")
            args.append(v)
        args.append(row_id)
        con.execute(f"UPDATE {table} SET {', '.join(sets)} WHERE {idcol}=?", args)
        con.execute("DELETE FROM refusal_fossils WHERE id=?", (lid,))
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="quarantine what the scan finds")
    ap.add_argument("--restore", action="store_true", help="put every original back")
    ap.add_argument("--db", default=str(DB_PATH))
    args = ap.parse_args()

    if args.apply and args.restore:
        print("--apply and --restore are opposites; pick one")
        return 2

    con = sqlite3.connect(args.db, timeout=30)
    try:
        if args.restore:
            with con:
                n = restore(con)
            print(f"restored {n} rows")
            return 0

        found = scan(con, _detector())
        total = sum(len(v) for v in found.values())
        for table, hits in found.items():
            def kind_of(replacement):
                if not replacement:
                    return "quarantine"
                return "mark" if replacement == CONVERSATION_MARKER else "trim"
            trims = sum(1 for h in hits if kind_of(h[2]) == "trim")
            note = f" ({trims} keep real content underneath)" if trims else ""
            print(f"\n{table}: {len(hits)} refusal(s) stored{note}")
            for row_id, text, replacement in hits[:3]:
                print(f"  [{kind_of(replacement)}] id={row_id}: "
                      f"{' '.join(text.split())[:84]}…")
            if len(hits) > 3:
                print(f"  … and {len(hits) - 3} more")

        if not total:
            print("\nnothing to quarantine")
            return 0
        if not args.apply:
            print(f"\n{total} row(s) would be quarantined. Re-run with --apply.")
            return 0

        with con:
            n = apply(con, found)
        print(f"\nquarantined {n} row(s); originals saved in refusal_fossils")
        print("undo with --restore")
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
