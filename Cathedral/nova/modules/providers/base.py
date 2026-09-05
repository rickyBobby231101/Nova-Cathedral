#!/usr/bin/env python3
"""
The provider protocol — one shape for every model the Council can seat.

Each provider module exposes exactly two functions:

    available() -> (bool, str)   # can this seat speak, and if not, why not
    ask(prompt, context=None, model=None, timeout=...) -> dict

`ask` returns the same shape the daemon's own `_ollama_chat` returns, so
callers handle a local model and a cloud API identically:

    {"response": str, "model": str, "latency": float}    on success
    {"error": str}                                        on failure

Never raises. A provider that raises takes the Council down with it; a
provider that returns {"error": ...} loses one seat and the round continues.
That is the same reasoning the Scribe's inner guard uses in the evolution
loop, applied at the seat boundary.

`available()` is separate from `ask()` on purpose: `nova status` must be able
to report why a seat is empty without spending money or waiting on a model to
load. The reason string is shown to the Observer verbatim, so write it for a
human — "no API key" and "account has no credit" are different problems with
different fixes, and collapsing them into "unavailable" wastes his time.

Stdlib only. The systemd units run /usr/bin/python3, not the venv.
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

SECRETS_DIR = Path.home() / ".config" / "nova-cathedral"

DEFAULT_TIMEOUT = 180.0


def load_secrets(directory: Path = SECRETS_DIR) -> dict:
    """Read every *.env in the secrets directory into a dict.

    The daemon gets these through systemd's EnvironmentFile, which applies
    only to the daemon process — a CLI launched from a shell inherits none of
    them. So the CLI reads the same files directly, and the one secrets
    location stays the truth for both callers.

    Values are unquoted. `anthropic.env` stores its key wrapped in double
    quotes; systemd strips those, a naive split does not, and the trailing
    quote turns a valid key into a 401 that reads exactly like a revoked one.
    That cost real debugging time — hence this function rather than a one-line
    split at each call site.
    """
    out = {}
    if not directory.is_dir():
        return out
    for path in sorted(directory.glob("*.env")):
        try:
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, _, value = line.partition("=")
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                out[name.strip()] = value
        except OSError:
            continue
    return out


def api_key(name: str, directory: Path = SECRETS_DIR) -> str:
    """A key from the environment, falling back to the secrets directory.

    Environment first: an explicitly exported key should win over a stored
    one, so a different key can be tried without editing a file.
    """
    return os.environ.get(name) or load_secrets(directory).get(name, "")


def post_json(url: str, payload: dict, headers: dict, timeout: float) -> dict:
    """One HTTP POST returning parsed JSON, or {"error": ...}.

    Shared by every cloud provider so their failure text is consistent. HTTP
    error bodies are parsed rather than discarded: the message inside them is
    the actionable part ("credit balance is too low" tells the Observer what
    to do; "HTTP 400" does not).
    """
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = ""
        try:
            raw = json.loads(e.read())
            err = raw.get("error", raw)
            body = err.get("message", "") if isinstance(err, dict) else str(err)
        except Exception:
            pass
        return {"error": f"HTTP {e.code}: {body or e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def build_prompt(prompt: str, context: str = None) -> str:
    """Prepend shared Cathedral context to a question.

    Kept here rather than in each provider so every seat in a Council round
    is answering the same question with the same context — otherwise the
    seats are not comparable and the round proves nothing.
    """
    if not context:
        return prompt
    return f"{context.strip()}\n\n---\n\n{prompt}"
