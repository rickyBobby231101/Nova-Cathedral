#!/usr/bin/env python3
"""
claude_bridge.py — a real connection to Claude, over the actual Anthropic API.

Distinct from the daemon's existing "Bridge Walker" (a second *local* Ollama
model role-playing as an external AI, at zero cost). This module makes a
genuine network call to Anthropic and costs real money per call — nothing
here should run silently or on a timer; it's meant to be invoked deliberately.

Needs ANTHROPIC_API_KEY in the environment. Uses only the stdlib (urllib) —
no extra dependency, same approach the daemon already uses for Ollama.
"""

import json
import os
import time
import urllib.error
import urllib.request

API_URL         = "https://api.anthropic.com/v1/messages"
API_VERSION     = "2023-06-01"
DEFAULT_MODEL   = "claude-sonnet-5"
DEFAULT_MAX_TOK = 4096


def api_key_configured() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def ask_claude(prompt: str, system: str = None, model: str = DEFAULT_MODEL,
               max_tokens: int = DEFAULT_MAX_TOK, timeout: float = 120.0) -> dict:
    """
    Send one message to the real Claude API. Returns {response, model, latency}
    on success or {error} on failure — same shape as the daemon's _ollama_chat,
    so callers can handle both the same way.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set — the real Claude bridge is "
                          "configured but has no key to authenticate with"}

    payload = {
        "model":      model,
        "max_tokens": max_tokens,
        # This model thinks by default when the field is omitted, and max_tokens
        # is a cap on the thinking and the reply together -- so the budget has to
        # cover both, and the timeout above has to allow for the extra latency.
        # Stated here so it reads as a decision rather than an inherited default.
        # For a faster, cheaper bridge instead: {"type": "disabled"}.
        "thinking":      {"type": "adaptive"},
        "output_config": {"effort": "low"},
        "messages":   [{"role": "user", "content": prompt}],
    }
    if system:
        payload["system"] = system

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key":         api_key,
            "anthropic-version": API_VERSION,
            "content-type":      "application/json",
        },
        method="POST",
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = json.loads(e.read()).get("error", {}).get("message", "")
        except Exception:
            pass
        return {"error": f"HTTP {e.code}: {body or e.reason}"}
    except Exception as e:
        return {"error": str(e)}

    stop_reason = data.get("stop_reason")
    text = "".join(
        block.get("text", "") for block in data.get("content", [])
        if block.get("type") == "text"
    )

    # Both of these come back as an ordinary success with empty or half-finished
    # content. Returned as a normal answer, the daemon writes a blank exchange
    # into consciousness.db with nothing recording why it was blank.
    if stop_reason == "refusal":
        return {"error": "Claude declined to answer this one"}
    if stop_reason == "max_tokens" and not text.strip():
        return {"error": f"reply hit the {max_tokens}-token cap before any text"}

    return {
        "response":    text,
        "model":       data.get("model", model),
        "stop_reason": stop_reason,
        "truncated":   stop_reason == "max_tokens",
        "latency":     round(time.time() - t0, 2),
        "usage":       data.get("usage", {}),
    }
