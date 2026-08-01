#!/usr/bin/env python3
"""Nova — start the daemon and talk to it."""
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

SOCKET = "/tmp/nova_socket"
DAEMON = Path(__file__).parent / "daemon" / "nova_cathedral_daemon.py"


def send(payload, timeout=120):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(SOCKET)
        s.sendall((json.dumps(payload) + "\n").encode())
        s.settimeout(timeout)
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if data.endswith(b"\n"):
                break
        s.close()
        return json.loads(data.decode())
    except FileNotFoundError:
        return {"error": "daemon not running"}
    except Exception as e:
        return {"error": str(e)}


def ensure_running():
    if os.path.exists(SOCKET):
        r = send({"command": "status"})
        if "error" not in r:
            return True
    print("Starting Nova Cathedral...")
    subprocess.Popen(
        [sys.executable, str(DAEMON)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        time.sleep(0.5)
        if os.path.exists(SOCKET):
            r = send({"command": "status"})
            if "error" not in r:
                print(
                    f"Nova awake | {r.get('flow_resonance', '?')} Hz | "
                    f"{r.get('conversations', 0)} memories | "
                    f"{r.get('active_circuits', 0)} circuits\n"
                )
                return True
    print("Error: daemon failed to start — check ~/cathedral/logs/nova_cathedral.log")
    return False


def print_response(r):
    if "response" in r:
        print(f"\n{r['response']}\n")
        if "latency" in r:
            print(f"  [{r.get('model', 'unknown')} {r['latency']}s]\n")
    elif "memories" in r:
        mems = r["memories"]
        if not mems:
            print("  (no memories)\n")
        for m in mems:
            print(f"\n[{m['ts']}]")
            print(f"  Q: {m['q']}")
            a = m["a"]
            print(f"  A: {a[:300]}{'...' if len(a) > 300 else ''}")
        print()
    elif "error" in r:
        print(f"  Error: {r['error']}\n")
    else:
        print(json.dumps(r, indent=2))


def cli():
    print("Commands: ask <prompt>  recall <query>  status  resonance  ritual_on  ritual_off  stop  exit\n")
    while True:
        try:
            line = input("nova> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line or line == "exit":
            break

        parts = line.split(None, 1)
        cmd, rest = parts[0], (parts[1] if len(parts) > 1 else "")

        if cmd == "ask":
            if not rest:
                print("  Usage: ask <prompt>\n")
                continue
            print_response(send({"command": "ask", "prompt": rest}))
        elif cmd == "recall":
            print_response(send({"command": "recall", "query": rest, "n": 10}))
        elif cmd == "stop":
            send({"command": "shutdown"})
            print("Nova slumbers.")
            break
        elif cmd in ("status", "resonance", "ritual_on", "ritual_off"):
            print_response(send({"command": cmd}))
        else:
            # treat unknown input as an ask
            print_response(send({"command": "ask", "prompt": line}))


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        # no args → start daemon + open CLI
        if ensure_running():
            cli()

    elif args[0] == "stop":
        print(send({"command": "shutdown"}))

    elif args[0] == "status":
        print(json.dumps(send({"command": "status"}), indent=2))

    elif args[0] == "ask":
        prompt = " ".join(args[1:])
        if not prompt:
            print("Usage: nova.py ask <prompt>")
        else:
            if ensure_running():
                print_response(send({"command": "ask", "prompt": prompt}))

    elif args[0] == "recall":
        query = " ".join(args[1:])
        print_response(send({"command": "recall", "query": query}))

    else:
        # treat everything as a prompt
        prompt = " ".join(args)
        if ensure_running():
            print_response(send({"command": "ask", "prompt": prompt}))
