#!/usr/bin/env python3
"""The Weaver — knowledge graph architect of the Rose Cathedral.

Weaves Nova's learned knowledge documents (~/cathedral/knowledge/*.md) into
the knowledge graph: each document becomes a node in a domain petal, and
documents that share enough significant vocabulary get connected by edges
(light-threads). Re-runnable: already-woven documents (matched by label with
source='weaver') are skipped, and edge weaving strengthens existing threads
rather than duplicating them (mirrors the daemon's ON CONFLICT upsert).

Usage:
    python3 weaver.py            # weave new docs + edges
    python3 weaver.py --dry-run  # show what would be woven, change nothing
"""

import argparse
import re
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path

HOME = Path.home()
KNOWLEDGE_DIR = HOME / "cathedral" / "knowledge"
DB_PATH = HOME / "cathedral" / "memory" / "consciousness.db"

# Domain petals: first matching bucket wins on score. Keep the list short —
# each domain is a petal in the rose window, and 24 is the geometric maximum.
DOMAIN_KEYWORDS = {
    "herbal": ["herb", "plant", "chamomile", "valerian", "tincture", "remedy",
               "botanical", "medicinal", "herbalis", "holistic"],
    "cosmos": ["astronomy", "celestial", "star", "cosmic", "aerospace",
               "atlas", "navigat", "planet", "orbit"],
    "cathedral": ["cathedral", "conduit", "stone", "archive", "sanctum",
                  "spire", "nave", "harmonic conduit"],
    "consciousness": ["consciousness", "awareness", "meditation", "mind",
                      "dream", "transcend", "mystical", "perception"],
    "wellbeing": ["sleep", "circadian", "health", "healing", "wellness",
                  "relaxation", "stress"],
    "arts": ["art", "music", "history", "painting", "sculpture", "poetry"],
    "systems": ["plugin", "code", "python", "module", "daemon", "database",
                "algorithm", "protocol"],
    "mythos": ["mythos", "silent order", "harmonic accord", "tillagon",
               "eyemoeba", "phoenix", "zorya", "the flow", "distortion"],
}

STOPWORDS = set("""
the and for with that this from have will your which their about would there
been they them then than what when where into more some also each other
such only over very just like most make made through being under between
""".split())


def classify_domain(name: str, text: str) -> str:
    # Filename is the strongest signal — every doc's *content* talks about the
    # Cathedral, so without this weighting everything lands in one petal.
    fname = name.lower()
    body = text[:3000].lower()
    scores = {}
    for domain, keys in DOMAIN_KEYWORDS.items():
        scores[domain] = sum(fname.count(k) * 5 + body.count(k) for k in keys)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "knowledge"


def significant_words(text: str, top: int = 60) -> set:
    words = re.findall(r"[a-z]{5,}", text.lower())
    counts = Counter(w for w in words if w not in STOPWORDS)
    return {w for w, _ in counts.most_common(top)}


def prettify(stem: str) -> str:
    label = re.sub(r"[_\-]+", " ", stem).strip()
    return label[:1].upper() + label[1:]


def weave(db_path=DB_PATH, knowledge_dir=KNOWLEDGE_DIR,
          min_similarity=0.18, max_edges_per_node=3, dry_run=False) -> dict:
    """Weave new knowledge docs into the graph. Returns a summary dict.

    Callable from the daemon (cheap when nothing is new: one SELECT plus
    file stats) or from the CLI below.
    """
    docs = sorted(Path(knowledge_dir).rglob("*.md"))
    con = sqlite3.connect(db_path)
    existing = {r[0] for r in con.execute(
        "SELECT label FROM knowledge_nodes WHERE source='weaver'")}

    woven, skipped = [], 0
    for doc in docs:
        if doc.name.startswith("."):   # dotfiles = daemon naming bug, not docs
            continue
        label = prettify(doc.stem)
        if label in existing:
            skipped += 1
            continue
        text = doc.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            continue
        domain = classify_domain(doc.stem, text)
        weight = max(0.6, min(2.0, len(text) / 4000))
        woven.append({"label": label, "domain": domain, "text": text,
                      "weight": round(weight, 2)})

    summary = {
        "documents": len(docs), "woven": len(woven), "skipped": skipped,
        "edges_added": 0, "domains": dict(Counter(d["domain"] for d in woven)),
        "sample": [(d["domain"], d["label"], d["weight"]) for d in woven[:15]],
    }

    if dry_run or not woven:
        con.close()
        return summary

    now = datetime.now().isoformat()
    for d in woven:
        cur = con.execute(
            "INSERT INTO knowledge_nodes (domain, label, content, source, weight, created) "
            "VALUES (?,?,?,?,?,?)",
            (d["domain"], d["label"], d["text"], "weaver", d["weight"], now))
        d["id"] = cur.lastrowid
    con.commit()

    # Weave edges across ALL nodes so new docs connect to old ones
    rows = con.execute("SELECT id, label, content FROM knowledge_nodes").fetchall()
    vocab = {r[0]: significant_words(r[2]) for r in rows}
    ids = [r[0] for r in rows]

    candidates = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            va, vb = vocab[a], vocab[b]
            if not va or not vb:
                continue
            sim = len(va & vb) / len(va | vb)
            if sim >= min_similarity:
                candidates.append((sim, a, b))
    candidates.sort(reverse=True)

    edge_count = Counter()
    for sim, a, b in candidates:
        if edge_count[a] >= max_edges_per_node or edge_count[b] >= max_edges_per_node:
            continue
        strength = round(min(0.9, sim * 2.5), 2)
        con.execute(
            """INSERT INTO knowledge_edges (from_id, to_id, strength, resonance_score, created)
               VALUES (?,?,?,?,?)
               ON CONFLICT(from_id, to_id) DO UPDATE SET
                   strength        = MAX(strength, excluded.strength),
                   resonance_score = (resonance_score + excluded.resonance_score) / 2""",
            (a, b, strength, 0.5, now))
        edge_count[a] += 1
        edge_count[b] += 1
        summary["edges_added"] += 1
    con.commit()

    summary["total_nodes"] = con.execute("SELECT COUNT(*) FROM knowledge_nodes").fetchone()[0]
    summary["total_edges"] = con.execute("SELECT COUNT(*) FROM knowledge_edges").fetchone()[0]
    con.close()
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-similarity", type=float, default=0.18,
                    help="jaccard threshold for weaving an edge")
    ap.add_argument("--max-edges-per-node", type=int, default=3)
    args = ap.parse_args()

    s = weave(min_similarity=args.min_similarity,
              max_edges_per_node=args.max_edges_per_node, dry_run=args.dry_run)
    print(f"{s['documents']} documents: {s['woven']} to weave, {s['skipped']} already woven")
    for dom, count in sorted(s["domains"].items(), key=lambda kv: -kv[1]):
        print(f"  {dom}: {count}")
    if args.dry_run:
        for dom, label, w in s["sample"]:
            print(f"  [{dom}] {label} (weight {w})")
    elif s["woven"]:
        print(f"woven: {s['woven']} nodes, {s['edges_added']} light-threads "
              f"(graph now {s['total_nodes']} nodes, {s['total_edges']} edges)")


if __name__ == "__main__":
    main()
