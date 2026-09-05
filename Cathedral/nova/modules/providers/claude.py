#!/usr/bin/env python3
"""Claude — the Anthropic API seat.

Distinct from Claude Code, which is the interactive operator and is not a
Council seat: the operator writes the proposal under review, so seating it as
a reviewer would be self-review wearing two hats.

Thin adapter over `modules/claude_bridge.py`, which already implements this
call correctly and is pinned by 14 contract tests — including the two guards
that matter here, where a `refusal` stop and a `max_tokens` stop with no text
both arrive as ordinary successes carrying empty content. Reimplementing that
to fit a new interface would discard working, tested code to satisfy a shape.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from base import api_key, build_prompt

NAME = "claude"
ROLE = "implementation review (API)"
KEY_NAME = "ANTHROPIC_API_KEY"

try:
    import claude_bridge as _bridge
    _BRIDGE = True
except ImportError:                                  # pragma: no cover
    _BRIDGE = False


def available() -> tuple:
    if not _BRIDGE:
        return False, "modules/claude_bridge.py not importable"
    if not api_key(KEY_NAME):
        return False, "no ANTHROPIC_API_KEY in env or ~/.config/nova-cathedral/"
    return True, "key present (credit state unknown until first call)"


def ask(prompt: str, context: str = None, model: str = None,
        timeout: float = 180.0) -> dict:
    ok, why = available()
    if not ok:
        return {"error": why}
    # claude_bridge reads the key from the environment; the CLI does not
    # inherit systemd's EnvironmentFile, so put it there for this process.
    import os
    os.environ.setdefault(KEY_NAME, api_key(KEY_NAME))
    t0 = time.time()
    out = _bridge.ask_claude(
        build_prompt(prompt, context),
        model=model or _bridge.DEFAULT_MODEL,
        timeout=timeout,
    )
    if "error" in out:
        return out
    out.setdefault("latency", round(time.time() - t0, 2))
    return out
