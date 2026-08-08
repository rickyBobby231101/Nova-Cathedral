import sqlite3
DB = "/home/daniel/cathedral/memory/consciousness.db"
con = sqlite3.connect(DB)

# Guard: don't double-run
already = con.execute(
    "SELECT COUNT(*) FROM knowledge_nodes WHERE domain='research' AND source='autonomous'"
).fetchone()[0]
if already:
    print(f"Backfill already ran ({already} research nodes present). Aborting to avoid dupes.")
    raise SystemExit

# Source rows: genuine web_search research with a real topic + content
rows = con.execute(
    "SELECT created, topic, content FROM knowledge_base "
    "WHERE source='web_search' AND topic!='' AND length(content)>100 "
    "ORDER BY created ASC"
).fetchall()

# Existing node labels for dedup
existing = {r[0] for r in con.execute(
    "SELECT label FROM knowledge_nodes"
).fetchall()}

inserted = skipped = 0
for created, topic, content in rows:
    label = topic[:80]
    if label in existing:
        skipped += 1
        continue
    con.execute(
        "INSERT INTO knowledge_nodes (domain, label, content, source, weight, created) "
        "VALUES (?,?,?,?,?,?)",
        ("research", label, content, "autonomous", 1.0, created)
    )
    existing.add(label)
    inserted += 1

con.commit()
total = con.execute("SELECT COUNT(*) FROM knowledge_nodes").fetchone()[0]
print(f"inserted {inserted}, skipped {skipped} dupes; knowledge_nodes now {total}")
con.close()
