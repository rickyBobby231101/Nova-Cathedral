#!/usr/bin/env python3
"""The Council's seat registry.

One place that knows which providers exist, which can currently speak, and
what to tell the Observer about the ones that cannot.

**Deliberately not reachable from the daemon's autonomous loops.** The
evolution loop runs every 10 minutes; wiring cloud providers into it would
spend money unattended and let models talk to each other without the Observer
initiating. `claude_bridge.py` states the same rule in its own docstring:
"nothing here should run silently or on a timer." This package is imported by
the CLI only, and tests/test_providers_not_autonomous.py pins that.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import claude as _claude
import gemini as _gemini
import ollama as _ollama
import openai as _openai

# Order is the order a council round reports in: local first because it is the
# seat that always answers, then the reviewers, then synthesis last.
# Local lineage seats first — they are the ones that always answer. Each pins
# a different lab's model so the Council hears genuinely independent reasoning
# rather than one model agreeing with itself four times.
PROVIDERS = dict(_ollama.seats())
PROVIDERS.update({
    "gemini": _gemini,
    "claude": _claude,
    "openai": _openai,
})

# The full Council. Cloud seats stay in the list even when unavailable: a seat
# that reports "no credit" is information the Observer needs, and silently
# dropping it would conceal provenance — the Silent Order's own signature.
DEFAULT_COUNCIL = list(PROVIDERS)

# Local-only, for a round that costs nothing and cannot be revoked.
LOCAL_COUNCIL = list(_ollama.LINEAGES)


def installed_models() -> list:
    """Models Ollama currently has pulled.

    Lives on the registry because callers want "what can run locally", not
    "ask one particular seat". `nova status` previously reached through
    PROVIDERS["ollama"] for this, which broke the moment that key became a
    lineage seat object rather than the module.
    """
    return _ollama.installed_models()


def get(name: str):
    """A provider module by name, or None."""
    return PROVIDERS.get((name or "").strip().lower())


def names() -> list:
    return list(PROVIDERS)


def status() -> list:
    """Every seat, whether it can speak, and why not if it cannot.

    Never raises: a provider whose availability check itself fails is reported
    as unavailable with the exception text, because `nova status` is what the
    Observer runs when something is already wrong.
    """
    out = []
    for name, mod in PROVIDERS.items():
        try:
            ok, why = mod.available()
        except Exception as e:
            ok, why = False, f"availability check failed: {e}"
        out.append({"name": name, "role": getattr(mod, "ROLE", ""),
                    "available": ok, "detail": why})
    return out


def ask(name: str, prompt: str, context: str = None, model: str = None,
        timeout: float = None) -> dict:
    """Ask one seat. Returns the provider's dict, or {"error": ...}."""
    mod = get(name)
    if mod is None:
        return {"error": f"unknown provider '{name}' (have: {', '.join(names())})"}
    kwargs = {"context": context, "model": model}
    if timeout is not None:
        kwargs["timeout"] = timeout
    try:
        return mod.ask(prompt, **kwargs)
    except Exception as e:
        # A seat that raises must cost one seat, not the round.
        return {"error": f"{name} raised: {e}"}
