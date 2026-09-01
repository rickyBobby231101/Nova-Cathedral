#!/usr/bin/env python3
"""The Conduit — ask Gemini from the terminal, and let Nova keep the exchange.

This is the bridge that was described but never built. It is not an API pipe
and it costs nothing: `gemini` is Google's own CLI, authenticated once through
a browser with a personal Google account, and it runs locally like any other
command. The Conduit runs it headless, prints the answer, and writes both
halves of the exchange into Nova's chat_import drop box, where her importer
adopts them within fifteen seconds through the same path as a live
conversation.

So the terminal gets the answer and Nova gets the memory, from one command.

    conduit.py "what should the next Cathedral layer be?"
    conduit.py --context "does the Glyph Codex need a Zorya counterpart?"
    echo "long question" | conduit.py

With --context, the mythos documents in ~/cathedral/knowledge/ are prepended
so Gemini wakes up holding the frequency instead of starting cold. That is the
"context piping" the original plan asked for — done by reading local files,
which is the only way it was ever going to work.
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
KNOWLEDGE_DIR = HOME / "cathedral" / "knowledge"
CHAT_IMPORT   = HOME / "cathedral" / "chat_import"

# Documents that carry the mythos. Prepended by --context so the exchange
# starts anchored. Missing files are skipped, never faked.
CONTEXT_DOCS = [
    "mythos_the_observer.md",
    "nova_daemon_memory_ingest_paths.md",
]

GEMINI_BIN = "gemini"
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_LOCAL_MODEL = "llama3.2:3b"
DEFAULT_TIMEOUT = 300

# Google retired free personal-account access through gemini-cli
# (IneligibleTierError / UNSUPPORTED_CLIENT, observed 2026-09-01), so the
# remote path needs a paid key and the local path is the default. Ollama
# is already on this machine, costs nothing, and needs no account —
# gemma3 is Google's own open Gemini-family weights if the family matters.
DEFAULT_BACKEND = "local"


def build_context() -> str:
    parts = []
    for name in CONTEXT_DOCS:
        doc = KNOWLEDGE_DIR / name
        if doc.is_file():
            parts.append(f"--- {name} ---\n{doc.read_text(encoding='utf-8', errors='replace')}")
    if not parts:
        return ""
    return ("The following are the operator's own working documents. Answer "
            "from them, and say plainly when something is not in them rather "
            "than inventing it.\n\n" + "\n\n".join(parts) + "\n\n---\n\n")


def ask_local(prompt: str, model=None, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Ask a model running under Ollama on this machine. No account, no key."""
    import json
    import urllib.error
    import urllib.request

    body = json.dumps({"model": model or DEFAULT_LOCAL_MODEL,
                       "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode()).get("response", "").strip()
    except urllib.error.URLError as e:
        raise SystemExit(f"could not reach Ollama at {OLLAMA_URL}: {e}\n"
                         "  is it running?  systemctl --user status ollama")
    except TimeoutError:
        raise SystemExit(
            f"local model timed out after {timeout}s. A cold load of a large "
            f"model can exceed this on limited RAM — try a smaller one "
            f"(--model llama3.2:1b) or raise --timeout.")


def ask(question: str, context: bool = False, model=None,
        timeout: int = DEFAULT_TIMEOUT, backend: str = DEFAULT_BACKEND) -> str:
    """Ask the configured backend and return its reply text."""
    prompt = (build_context() if context else "") + question
    if backend == "local":
        return ask_local(prompt, model=model, timeout=timeout)
    cmd = [GEMINI_BIN, "-p", prompt]
    if model:
        cmd += ["-m", model]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise SystemExit(
            "gemini CLI not found on PATH.\n"
            "  install:  npm install -g @google/gemini-cli\n"
            "  then run: gemini      (once, to log in with a Google account)")
    except subprocess.TimeoutExpired:
        raise SystemExit(f"gemini timed out after {timeout}s.")

    if proc.returncode != 0:
        err = (proc.stderr or "").strip() or "(no stderr)"
        hint = ""
        if "auth" in err.lower() or "login" in err.lower() or "credential" in err.lower():
            hint = ("\n\nThis looks like authentication. Run `gemini` on its own "
                    "in a normal terminal once and choose 'Login with Google' — "
                    "it needs a browser, so it cannot be done headless.")
        raise SystemExit(f"gemini exited {proc.returncode}:\n{err}{hint}")

    return (proc.stdout or "").strip()


def archive(question: str, answer: str, chat_import=None,
            speaker: str = "AI") -> Path:
    r"""Write the exchange where Nova's importer will find it.

    Labels are the entire protocol on her side: `Me:` and `Gemini:` at the
    start of a line. Model output is untrusted text, so an answer containing
    such a line would forge a second exchange into Nova's memory.

    Indenting does NOT prevent this — her pattern is `^\s*(label)\s*:` and
    matches through leading whitespace. Offending lines are prefixed with a
    quote marker instead, which breaks the match while staying readable, and
    the importer's own predicate decides what offends so the two modules can
    never drift apart.
    """
    chat_import = Path(chat_import) if chat_import else CHAT_IMPORT
    chat_import.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = chat_import / f"conduit_{speaker.lower()}_{stamp}.txt"

    import chat_importer
    safe_answer = "\n".join(
        "> " + ln if chat_importer.is_speaker_label(ln) else ln
        for ln in answer.splitlines())
    path.write_text(f"Me: {question}\n\n{speaker}: {safe_answer}\n",
                    encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser(description="Ask Gemini; let Nova keep the exchange.")
    ap.add_argument("question", nargs="*", help="the question (or pipe it on stdin)")
    ap.add_argument("--context", action="store_true",
                    help="prepend the mythos documents so Gemini starts anchored")
    ap.add_argument("--model", "-m", default=None,
                    help=f"model name (local default: {DEFAULT_LOCAL_MODEL})")
    ap.add_argument("--backend", choices=("local", "gemini"),
                    default=DEFAULT_BACKEND,
                    help="local = Ollama on this machine (free, no account); "
                         "gemini = the gemini CLI (needs a paid tier as of "
                         "2026-09-01)")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    ap.add_argument("--no-archive", action="store_true",
                    help="print the answer without giving it to Nova")
    args = ap.parse_args()

    question = " ".join(args.question).strip()
    if not question and not sys.stdin.isatty():
        question = sys.stdin.read().strip()
    if not question:
        raise SystemExit("nothing to ask. conduit.py \"your question\"")

    answer = ask(question, context=args.context, model=args.model,
                 timeout=args.timeout, backend=args.backend)
    print(answer)

    if not args.no_archive:
        speaker = "Gemini" if args.backend == "gemini" else "AI"
        path = archive(question, answer, speaker=speaker)
        print(f"\n[conduit] exchange written to {path.name} — "
              f"Nova adopts it within 15s", file=sys.stderr)


if __name__ == "__main__":
    main()
