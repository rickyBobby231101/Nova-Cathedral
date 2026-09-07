#!/usr/bin/env python3
"""
nova — the Observer's terminal into the Cathedral.

    nova ask <provider> "question"     one seat
    nova council "question"            every available seat, transcript saved
    nova status                        daemon, Ollama, seats, memory

Three deliberate properties:

**The Observer initiates.** Nothing here runs on a timer and nothing is
reachable from the daemon's autonomous loops. Models answer when asked and
do not talk to each other unprompted.

**Local data is the source of truth.** Council transcripts are written to
~/nova_council/sessions/ and every exchange is recorded locally. No vendor's
conversation memory is required for continuity.

**A dead seat costs one seat.** Council collects errors as results and reports
them; it never aborts the round because one provider is out of credit.

Installed as ~/.local/bin/nova, which precedes /usr/bin on PATH and therefore
shadows OpenStack's novaclient without removing that package.
"""

import argparse
import json
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

NOVA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(NOVA_ROOT / "modules"))

import council_log                                  # noqa: E402
import playground                                   # noqa: E402
import providers                                    # noqa: E402

SOCKET_PATH = "/tmp/nova_socket"
COUNCIL_DIR = Path.home() / "nova_council"
SESSIONS_DIR = COUNCIL_DIR / "sessions"


# ── daemon socket ────────────────────────────────────────────────────────────

def daemon_command(command: str, timeout: float = 300.0, **kw) -> dict:
    """One request to the daemon.

    Reads until the socket closes, and uses a timeout measured against real
    generation latency. The existing interface/nova_socket_client.py does a
    single recv(4096) with a 5-second timeout, which truncates any reply over
    4 KB and cannot complete an `ask` at all — a measured ask takes ~35 s.
    """
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(SOCKET_PATH)
        s.sendall(json.dumps({"command": command, **kw}).encode())
        chunks = []
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
        s.close()
        return json.loads(b"".join(chunks).decode())
    except FileNotFoundError:
        return {"error": "daemon not running (no socket at /tmp/nova_socket)"}
    except ConnectionRefusedError:
        return {"error": "socket exists but nothing is listening"}
    except socket.timeout:
        return {"error": f"daemon did not answer within {timeout:.0f}s"}
    except Exception as e:
        return {"error": str(e)}


# ── context ──────────────────────────────────────────────────────────────────

def cathedral_context() -> str:
    """Shared context for a Council round.

    Deliberately small. CATHEDRAL_STATE.md is written and curated by hand for
    the task at hand; dumping the database or the source tree into every
    prompt would blow the context budget of every local model and bury the
    question. If the file is absent, seats answer without it rather than the
    round failing.
    """
    state = COUNCIL_DIR / "CATHEDRAL_STATE.md"
    if state.is_file():
        text = state.read_text().strip()
        if text:
            return f"# Cathedral context\n\n{text}"
    return ""


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_ask(args) -> int:
    ctx = cathedral_context() if args.context else None
    print(f"→ {args.provider} …", file=sys.stderr, flush=True)
    r = providers.ask(args.provider, args.prompt, context=ctx, model=args.model)
    if "error" in r:
        print(f"✗ {args.provider}: {r['error']}", file=sys.stderr)
        return 1
    print(r["response"].strip())
    print(f"\n— {r.get('model','?')} in {r.get('latency','?')}s", file=sys.stderr)
    return 0


def cmd_council(args) -> int:
    if args.seats:
        seats = args.seats.split(",")
    elif args.local:
        seats = providers.LOCAL_COUNCIL
    else:
        seats = providers.DEFAULT_COUNCIL
    # Context is not free on this hardware. Prepending CATHEDRAL_STATE.md costs
    # a local 4B model more time than answering the question does, and a seat
    # that times out contributes nothing. --no-context trades the shared frame
    # for an answer, which is the right trade when the question stands alone.
    ctx = "" if args.no_context else cathedral_context()
    session = datetime.now().strftime("%Y%m%d-%H%M%S")

    print(f"Council session {session}")
    print(f"Question: {args.prompt}")
    if ctx:
        print(f"Context:  CATHEDRAL_STATE.md ({len(ctx)} chars)")
    print()

    results, spoke = [], 0
    for name in seats:
        mod = providers.get(name)
        if mod is None:
            print(f"  ✗ {name}: unknown seat")
            continue
        ok, why = mod.available()
        if not ok:
            print(f"  ✗ {name}: {why}")
            results.append({"provider": name, "status": "unavailable",
                            "detail": why, "response": None})
            continue
        print(f"  → {name} …", end=" ", flush=True)
        t0 = time.time()
        r = providers.ask(name, args.prompt, context=ctx)
        if "error" in r:
            print(f"✗ {r['error'][:80]}")
            results.append({"provider": name, "status": "error",
                            "detail": r["error"], "response": None})
        else:
            print(f"✓ {r.get('model','?')} ({r.get('latency','?')}s)")
            results.append({"provider": name, "status": "ok",
                            "model": r.get("model"), "latency": r.get("latency"),
                            "response": r["response"]})
            spoke += 1

    record = {"session_id": session,
              "timestamp": datetime.now().isoformat(),
              "request": args.prompt,
              "context_used": bool(ctx),
              "seats": results,
              "voices_heard": spoke,
              "decision": None}          # the Observer fills this in

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    out = SESSIONS_DIR / f"{session}.json"
    out.write_text(json.dumps(record, indent=2))

    md = SESSIONS_DIR / f"{session}.md"
    lines = [f"# Council — {session}", "", f"**Question:** {args.prompt}", ""]
    for r in results:
        lines.append(f"## {r['provider']}")
        if r["response"]:
            lines += [f"*{r.get('model','?')} · {r.get('latency','?')}s*", "",
                      r["response"].strip(), ""]
        else:
            lines += [f"**{r['status']}** — {r['detail']}", ""]
    lines += ["## Decision", "", "*Awaiting the Observer.*", ""]
    md.write_text("\n".join(lines))

    print(f"\n{spoke} of {len(seats)} seats answered")
    if spoke < 2:
        print("⚠  fewer than two voices — this is not a council, it is one opinion")
    print(f"transcript: {md}")

    # A round is not finished when the models stop talking. Raised by qwen3:4b:
    # labelling a synthesis as one reading only helps a reader who reads it, so
    # an undecided round must not look complete.
    waiting = council_log.pending()
    if waiting:
        print(f"\n⧗ {len(waiting)} session(s) awaiting your decision:")
        for w in waiting:
            print(f"    nova decide {w['session_id']} \"...\"")
    return 0 if spoke else 1


def cmd_build(args) -> int:
    """Turn the seats loose on a build task, in a room they cannot leave.

    Every seat gets the same task and writes into its own directory. Nothing
    is executed, nothing is merged, and nothing reaches the live trees — the
    output is files on disk for the Observer to read.
    """
    seats = args.seats.split(",") if args.seats else providers.LOCAL_COUNCIL
    sid = playground.open_session(args.task)

    print(f"Playground session {sid}")
    print(f"Task: {args.task[:90]}{'…' if len(args.task) > 90 else ''}")
    print(f"Seats: {', '.join(seats)}")
    print()

    brief = (
        f"{args.task}\n\n"
        "Write the code. Put each file in its own fenced block and name it on "
        "the fence, like:\n"
        "```python thing.py\n...\n```\n"
        "Keep it small and complete. No preamble."
    )

    results, built = [], 0
    for name in seats:
        mod = providers.get(name)
        if mod is None:
            print(f"  ✗ {name}: unknown seat")
            continue
        ok, why = mod.available()
        if not ok:
            print(f"  ✗ {name}: {why[:60]}")
            results.append({"seat": name, "status": "unavailable", "detail": why})
            continue
        print(f"  → {name} …", end=" ", flush=True)
        r = providers.ask(name, brief)
        if "error" in r:
            print(f"✗ {r['error'][:60]}")
            results.append({"seat": name, "status": "error", "detail": r["error"]})
            continue
        w = playground.write_seat(sid, name, r["response"])
        print(f"✓ {', '.join(w.get('files', [])) or w.get('error', '?')}")
        results.append({"seat": name, "status": "ok", "model": r.get("model"),
                        "latency": r.get("latency"), **w})
        built += 1

    d = playground.close_session(sid, args.task, results)
    print(f"\n{built} of {len(seats)} seats built something")
    print(f"  {d}")
    print("\n  Nothing here has been executed, reviewed, or merged.")
    return 0 if built else 1


def cmd_status(args) -> int:
    print("NOVA CATHEDRAL — STATUS\n")

    st = daemon_command("status", timeout=20)
    if "error" in st:
        print(f"  daemon      ✗ {st['error']}")
    else:
        print(f"  daemon      ✓ up {st.get('uptime', 0) // 60} min | "
              f"model {st.get('model')} | harmony {st.get('harmony_score')}")

    models = providers.installed_models()
    print(f"  ollama      {'✓ ' + str(len(models)) + ' models' if models else '✗ not responding'}")

    db = Path.home() / "cathedral" / "memory" / "consciousness.db"
    if db.is_file():
        import sqlite3
        try:
            # `with sqlite3.connect(...)` manages the transaction, not the
            # handle — close it explicitly so `nova status` never leaves a
            # reader open against the live database.
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            try:
                n = con.execute("SELECT count(*) FROM conversations").fetchone()[0]
                k = con.execute("SELECT count(*) FROM knowledge_nodes").fetchone()[0]
            finally:
                con.close()
            print(f"  memory      ✓ {db.stat().st_size // 1024 // 1024} MB | "
                  f"{n} conversations | {k} knowledge nodes")
        except Exception as e:
            print(f"  memory      ⚠ {e}")
    else:
        print("  memory      ✗ consciousness.db not found")

    print("\n  COUNCIL SEATS")
    for s in providers.status():
        # Widths track the longest seat name and role; lineage seats
        # ("ollama:deepseek", "local voice (DeepSeek, reasoning-tuned)") are
        # considerably longer than the original four and blew the old columns.
        print(f"    {'✓' if s['available'] else '✗'} {s['name']:<16} "
              f"{s['role']:<40} {s['detail']}")

    avail = sum(1 for s in providers.status() if s["available"])
    print(f"\n  {avail} of {len(providers.names())} seats available")

    waiting = council_log.pending()
    total = len(council_log.load_sessions())
    if waiting:
        print(f"\n  ⧗ {len(waiting)} of {total} council session(s) awaiting your decision")
        for w in waiting:
            print(f"      {w['session_id']}  ({w['voices_heard']} voices)  "
                  f"{w['request'][:46]}…")
    elif total:
        print(f"\n  ✓ all {total} council session(s) decided")
    return 0


def cmd_decide(args) -> int:
    """Record the Observer's ruling on a council session.

    The Council does not decide; it advises. This is where the deciding is
    written down, and until it is written the session stays pending.
    """
    r = council_log.record_decision(args.session_id, args.decision)
    if "error" in r:
        print(f"✗ {r['error']}", file=sys.stderr)
        return 1
    print(f"✓ {r['session_id']} decided")
    left = council_log.pending()
    print(f"  {len(left)} session(s) still awaiting a decision" if left
          else "  all council sessions are now decided")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="nova", description="Nova Cathedral terminal")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("ask", help="ask one provider")
    a.add_argument("provider", choices=providers.names())
    a.add_argument("prompt")
    a.add_argument("--model")
    a.add_argument("--context", action="store_true",
                   help="prepend CATHEDRAL_STATE.md")
    a.set_defaults(fn=cmd_ask)

    c = sub.add_parser("council", help="ask every available seat")
    c.add_argument("prompt")
    c.add_argument("--seats", help="comma-separated subset")
    c.add_argument("--local", action="store_true",
                   help="local lineage seats only — free, offline, ~4x slower")
    c.add_argument("--no-context", action="store_true",
                   help="skip CATHEDRAL_STATE.md — much faster for local seats")
    c.set_defaults(fn=cmd_council)

    dec = sub.add_parser("decide", help="record your ruling on a council session")
    dec.add_argument("session_id")
    dec.add_argument("decision")
    dec.set_defaults(fn=cmd_decide)

    b = sub.add_parser("build", help="turn the seats loose in the playground")
    b.add_argument("task")
    b.add_argument("--seats", help="comma-separated subset (default: local only)")
    b.set_defaults(fn=cmd_build)

    s = sub.add_parser("status", help="daemon, ollama, seats, memory")
    s.set_defaults(fn=cmd_status)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
