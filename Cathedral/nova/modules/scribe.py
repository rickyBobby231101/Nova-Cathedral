#!/usr/bin/env python3
"""The Scribe — frontmatter-driven document filing for the Cathedral.

Watches a drop directory for markdown files carrying YAML frontmatter, files
each one into a destination chosen by its `type:` field, indexes every `tags:`
entry into a master index, and writes a confirmation back into the file so the
author can see it was read.

This is the counterpart to the Weaver, and the division matters:

    The Weaver READS  ~/cathedral/knowledge/*.md into the knowledge graph.
                      It never moves or edits a file.
    The Scribe MOVES and ANNOTATES files in ~/cathedral/scribe/.
                      It never touches the graph.

The Scribe keeps its own tree so that filing a log can never pollute the rose
window. A document meant for the graph declares a promoting type (see
KNOWLEDGE_TYPES) and is filed into the Weaver's directory on purpose, never by
accident.

Safety properties, all load-bearing:
  * A file with NO frontmatter is invisible to the Scribe. The 170+ existing
    knowledge documents have none, so they can never be moved.
  * An unrecognized `type:` is reported, never guessed — the file stays put.
  * A destination that already holds that filename is a conflict; the Scribe
    skips it rather than overwriting.
  * Every resolved destination is checked to be inside a permitted root.
  * Filing is idempotent: the Scribe stamps `scribe_filed:` into the
    frontmatter and skips anything already stamped.

Usage:
    python3 scribe.py --dry-run   # show what would be filed, change nothing
    python3 scribe.py             # file, annotate, rebuild the index
"""

import argparse
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

HOME = Path.home()
SCRIBE_ROOT   = HOME / "cathedral" / "scribe"
INBOX         = SCRIBE_ROOT / "inbox"
KNOWLEDGE_DIR = HOME / "cathedral" / "knowledge"
INDEX_PATH    = SCRIBE_ROOT / "INDEX.md"

# type: -> subdirectory of the Scribe's own tree.
TYPE_ROUTES = {
    "system_log": "logs",
    "log":        "logs",
    "session":    "logs",
    "archive":    "archive",
    "note":       "notes",
    "reference":  "reference",
    "transcript": "transcripts",
}

# type: -> filed into the Weaver's directory instead, so the Weaver takes it
# into the knowledge graph on its next pass. Declared, never inferred.
KNOWLEDGE_TYPES = {
    "knowledge": "",
    "codex":     "codex",
    "mythos":    "mythos",
    "research":  "research",
}

CONFIRMATION_TOKEN = "[NOVA_CONFIRMATION_PENDING]"
STAMP_KEY = "scribe_filed"

_FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.DOTALL)


def split_frontmatter(text: str):
    """Return (meta_dict, frontmatter_source, body) or (None, '', text).

    A file without a leading `---` block, or whose block is not a YAML mapping,
    has no frontmatter as far as the Scribe is concerned — and a file with no
    frontmatter is one the Scribe must not touch.
    """
    m = _FM_RE.match(text)
    if not m:
        return None, "", text
    try:
        meta = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, "", text
    if not isinstance(meta, dict):
        return None, "", text
    return meta, m.group(0), text[m.end():]


def destination_dir(doc_type: str):
    """Resolve a `type:` to a directory, or None if the type is unrecognized."""
    t = str(doc_type or "").strip().lower()
    if t in TYPE_ROUTES:
        return SCRIBE_ROOT / TYPE_ROUTES[t]
    if t in KNOWLEDGE_TYPES:
        sub = KNOWLEDGE_TYPES[t]
        return KNOWLEDGE_DIR / sub if sub else KNOWLEDGE_DIR
    return None


def _within(path: Path, roots) -> bool:
    """True only if `path` resolves inside one of `roots`. A type route is data,
    and data can be edited — this is what stops a route from writing anywhere."""
    rp = path.resolve()
    for root in roots:
        try:
            rp.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def _atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".scribe-tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def annotate(fm_source: str, body: str, stamp: str, destination: str) -> str:
    """Stamp the frontmatter and answer the write-back token in the body.

    The frontmatter is edited as text, not re-serialized: round-tripping it
    through yaml.dump would reorder keys and restyle lists, rewriting the
    author's file for no reason. One line is inserted before the closing ---.
    """
    confirmation = (f"**NOVA CONFIRMED {stamp}** — read by the Scribe and "
                    f"filed to `{destination}`.")
    body = body.replace(CONFIRMATION_TOKEN + "...", confirmation)
    body = body.replace(CONFIRMATION_TOKEN, confirmation)

    lines = fm_source.rstrip("\n").split("\n")
    # lines[-1] is the closing '---'
    lines.insert(len(lines) - 1, f"{STAMP_KEY}: {stamp}")
    return "\n".join(lines) + "\n" + body


def organize(inbox=None, dry_run=False) -> dict:
    """File every stamped-ready document in the inbox. Returns a summary.

    Paths resolve at call time, not as default arguments: a default binds the
    module global once at import, which silently ignores any later redirection
    of the tree (tests, or a daemon pointed at a different cathedral).
    """
    inbox = Path(inbox) if inbox else INBOX
    summary = {"scanned": 0, "filed": 0, "skipped_no_frontmatter": 0,
               "skipped_already_filed": 0, "unrouted": [], "conflicts": [],
               "moves": []}
    if not inbox.is_dir():
        return summary

    roots = [SCRIBE_ROOT, KNOWLEDGE_DIR]
    for doc in sorted(inbox.glob("*.md")):
        if doc.name.startswith("."):
            continue
        summary["scanned"] += 1
        text = doc.read_text(encoding="utf-8", errors="replace")
        meta, fm_source, body = split_frontmatter(text)

        if meta is None:
            summary["skipped_no_frontmatter"] += 1
            continue
        if meta.get(STAMP_KEY):
            summary["skipped_already_filed"] += 1
            continue

        dest_dir = destination_dir(meta.get("type"))
        if dest_dir is None:
            summary["unrouted"].append((doc.name, meta.get("type")))
            continue
        if not _within(dest_dir, roots):
            summary["unrouted"].append((doc.name, "route escapes cathedral"))
            continue

        target = dest_dir / doc.name
        if target.exists():
            summary["conflicts"].append((doc.name, str(dest_dir)))
            continue

        try:
            rel = dest_dir.relative_to(HOME / "cathedral")
        except ValueError:
            rel = dest_dir
        summary["moves"].append((doc.name, str(rel)))

        if dry_run:
            continue

        stamp = datetime.now().isoformat(timespec="seconds")
        _atomic_write(doc, annotate(fm_source, body, stamp, str(rel)))
        dest_dir.mkdir(parents=True, exist_ok=True)
        os.replace(doc, target)
        summary["filed"] += 1

    return summary


def collect_tags(roots=None) -> dict:
    """Map tag -> [(title, path-relative-to-cathedral), ...] across filed docs."""
    roots = roots or [SCRIBE_ROOT, KNOWLEDGE_DIR]
    tags: dict = {}
    for root in roots:
        root = Path(root)
        if not root.is_dir():
            continue
        for doc in sorted(root.rglob("*.md")):
            if doc.name.startswith(".") or doc.resolve() == INDEX_PATH.resolve():
                continue
            meta, _, _ = split_frontmatter(
                doc.read_text(encoding="utf-8", errors="replace"))
            if not meta:
                continue
            raw = meta.get("tags") or []
            if isinstance(raw, str):
                raw = [t.strip() for t in raw.split(",")]
            try:
                rel = doc.relative_to(HOME / "cathedral")
            except ValueError:
                rel = doc
            title = str(meta.get("title") or doc.stem)
            for t in raw:
                t = str(t).strip()
                if t:
                    tags.setdefault(t, []).append((title, str(rel)))
    return tags


def build_index(index_path=None, dry_run=False) -> dict:
    """Rebuild the master tag index. Returns {'tags': n, 'entries': n}."""
    index_path = Path(index_path) if index_path else INDEX_PATH
    tags = collect_tags()
    total = sum(len(v) for v in tags.values())
    if not dry_run:
        now = datetime.now().isoformat(timespec="seconds")
        out = ["# Scribe Index", "",
               f"*{len(tags)} tags across {total} filed entries. "
               f"Rebuilt {now}. Generated — edits here are overwritten.*", ""]
        for tag in sorted(tags):
            out.append(f"## {tag}")
            for title, rel in sorted(set(tags[tag])):
                out.append(f"- [{title}]({rel})")
            out.append("")
        _atomic_write(index_path, "\n".join(out).rstrip() + "\n")
    return {"tags": len(tags), "entries": total}


def run(dry_run=False) -> dict:
    """Full pass: file the inbox, then rebuild the index."""
    s = organize(dry_run=dry_run)
    s["index"] = build_index(dry_run=dry_run)
    return s


def main():
    ap = argparse.ArgumentParser(description="The Scribe — file markdown by frontmatter.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    s = run(dry_run=args.dry_run)
    verb = "would file" if args.dry_run else "filed"
    print(f"{s['scanned']} document(s) in the inbox: {verb} {len(s['moves'])}")
    for name, dest in s["moves"]:
        print(f"  {name}  ->  {dest}/")
    if s["skipped_no_frontmatter"]:
        print(f"  {s['skipped_no_frontmatter']} skipped (no frontmatter — not the Scribe's)")
    if s["skipped_already_filed"]:
        print(f"  {s['skipped_already_filed']} skipped (already filed)")
    for name, t in s["unrouted"]:
        print(f"  ! {name}: unrecognized type '{t}' — left in the inbox")
    for name, dest in s["conflicts"]:
        print(f"  ! {name}: already exists in {dest} — left in the inbox")
    print(f"index: {s['index']['tags']} tags, {s['index']['entries']} entries")


if __name__ == "__main__":
    main()
