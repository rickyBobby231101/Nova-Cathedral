#!/usr/bin/env python3
"""Ollama — the local seat. Free, offline, and the only one that never
depends on a vendor's billing or tier decisions.

This is the seat that keeps the Council functional. On 2026-09-04 all three
cloud seats were simultaneously unavailable — Anthropic and OpenAI out of
credit, Gemini's free CLI tier withdrawn by Google — and this one still
answered. That is not a fallback; on this machine it is the baseline.

Model choice matters for a Council. The daemon runs llama3.2:1b; seating the
same model twice produces agreement that means nothing. `COUNCIL_MODEL`
defaults to a different family so the second voice is genuinely independent.
"""
import json
import time
import urllib.request

from base import build_prompt, post_json

DEFAULT_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:4b"          # deliberately not the daemon's llama3.2:1b

NAME = "ollama"
ROLE = "local independent voice"

# One seat per model lineage. Seating the same model twice produces agreement
# that means nothing; seating four labs' models produces disagreement that
# does. All local, all free, and none of them revocable by a vendor tier
# decision — which is the whole argument for them after Google withdrew the
# Gemini CLI's free tier mid-project.
#
# Cost is real and is CPU time, not money: ~250-550s per seat on this box
# (7.6 GB, no GPU), so a four-seat local round is a background task rather
# than an interactive one. That trade was made deliberately.
LINEAGES = {
    "ollama":          ("qwen3:4b",         "Alibaba"),
    "ollama:gemma":    ("gemma3:4b",        "Google"),
    "ollama:llama":    ("llama3.2:3b",      "Meta"),
    "ollama:deepseek": ("deepseek-r1:1.5b", "DeepSeek, reasoning-tuned"),
}


def installed_models(url: str = DEFAULT_URL, timeout: float = 5.0) -> list:
    try:
        with urllib.request.urlopen(f"{url}/api/tags", timeout=timeout) as r:
            return [m["name"] for m in json.loads(r.read()).get("models", [])]
    except Exception:
        return []


def available(model: str = None) -> tuple:
    models = installed_models()
    if not models:
        return False, "Ollama is not responding on localhost:11434"
    want = model or DEFAULT_MODEL
    if want not in models:
        return True, f"ready (note: {want} not pulled; have {', '.join(models[:3])})"
    return True, f"ready ({want})"


# 600s, from measurement rather than taste. A bare question to qwen3:4b took
# 228s on this box (7.6 GB, CPU-only). The same question with 5.7 KB of
# CATHEDRAL_STATE.md prepended exceeded 300s and timed out — consistent with
# the existing note that a 7000-character prompt did not finish in 400s. A
# council seat that times out is worse than a slow one: the round reports no
# voices and the Observer learns nothing.
COUNCIL_TIMEOUT = 600.0


def ask(prompt: str, context: str = None, model: str = None,
        timeout: float = COUNCIL_TIMEOUT) -> dict:
    model = model or DEFAULT_MODEL
    models = installed_models()
    if models and model not in models:
        model = models[0]          # answer with what is here rather than fail
    t0 = time.time()
    data = post_json(
        f"{DEFAULT_URL}/api/chat",
        {"model": model,
         "messages": [{"role": "user", "content": build_prompt(prompt, context)}],
         "stream": False},
        {}, timeout,
    )
    if "error" in data:
        return data
    text = (data.get("message") or {}).get("content", "")
    if not text.strip():
        return {"error": f"{model} returned an empty response"}
    return {"response": text, "model": model, "latency": round(time.time() - t0, 2)}


class _Seat:
    """One local seat pinned to one model.

    Presents the same surface as a provider module (NAME, ROLE, available,
    ask) so the registry treats a lineage seat and a cloud seat identically.
    Pinning matters: without it every local seat would answer on whatever
    model happened to be default, and four identical answers would look like
    consensus.
    """

    def __init__(self, name: str, model: str, lab: str):
        self.NAME = name
        self.MODEL = model
        self.ROLE = f"local voice ({lab})"

    def available(self):
        models = installed_models()
        if not models:
            return False, "Ollama is not responding on localhost:11434"
        if self.MODEL not in models:
            return False, f"{self.MODEL} not pulled (ollama pull {self.MODEL})"
        return True, f"ready ({self.MODEL})"

    def ask(self, prompt: str, context: str = None, model: str = None,
            timeout: float = COUNCIL_TIMEOUT) -> dict:
        # The seat's own model wins unless the caller names one explicitly.
        return ask(prompt, context=context, model=model or self.MODEL,
                   timeout=timeout)


def seats() -> dict:
    """Every local lineage seat, keyed by seat name."""
    return {name: _Seat(name, model, lab)
            for name, (model, lab) in LINEAGES.items()}
