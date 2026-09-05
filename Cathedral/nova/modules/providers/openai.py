#!/usr/bin/env python3
"""OpenAI — the synthesis seat.

Verified 2026-09-04: the stored key is genuine (the free /v1/models endpoint
listed 127 models) but the account has no credits, so chat completions return
"You have no credits remaining." Both facts matter — a key that authenticates
and an account that cannot pay are different failures, and `available()`
reports only what it can know cheaply. The credit state surfaces on the first
real call, which is where it belongs; probing billing on every status check
would cost a request each time.
"""
import time

from base import api_key, build_prompt, post_json

ENDPOINT = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"

NAME = "openai"
ROLE = "architecture / synthesis"
KEY_NAME = "OPENAI_API_KEY"


def available() -> tuple:
    if not api_key(KEY_NAME):
        return False, ("no OPENAI_API_KEY — export it, or store it in "
                       "~/.config/nova-cathedral/openai.env")
    return True, "key present (credit state unknown until first call)"


def ask(prompt: str, context: str = None, model: str = None,
        timeout: float = 180.0) -> dict:
    key = api_key(KEY_NAME)
    if not key:
        return {"error": available()[1]}
    model = model or DEFAULT_MODEL
    t0 = time.time()
    data = post_json(
        ENDPOINT,
        {"model": model,
         "messages": [{"role": "user", "content": build_prompt(prompt, context)}]},
        {"Authorization": f"Bearer {key}"}, timeout,
    )
    if "error" in data:
        return data
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return {"error": "OpenAI returned no choices"}
    if not text.strip():
        return {"error": "OpenAI returned an empty response"}
    return {"response": text, "model": data.get("model", model),
            "latency": round(time.time() - t0, 2)}
