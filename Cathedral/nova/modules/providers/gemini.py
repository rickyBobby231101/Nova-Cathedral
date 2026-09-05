#!/usr/bin/env python3
"""Gemini — via the Generative Language API and an API key.

**Not the CLI.** `@google/gemini-cli` authenticates with OAuth against
Gemini Code Assist, and on 2026-09-04 Google withdrew the free tier from that
client (IneligibleTierError / UNSUPPORTED_CLIENT). Verified that day: the
account's OAuth token is valid and carries cloud-platform scope, and
`cloudcode-pa.googleapis.com/v1internal:loadCodeAssist` answers HTTP 200 — but
it offers only `standard-tier`, which sets `userDefinedCloudaicompanionProject:
true`, and the account has zero Cloud projects. So the CLI path cannot be
revived without creating a GCP project and accepting its billing terms.

The Generative Language API is a different product with its own free tier,
takes a plain API key from aistudio.google.com/apikey, and has no OAuth
session to expire. That is why this module exists and `conduit.py` (which
shells out to the CLI) is left alone rather than repaired.
"""
import time

from base import api_key, build_prompt, post_json

ENDPOINT = ("https://generativelanguage.googleapis.com/v1beta/models/"
            "{model}:generateContent")
DEFAULT_MODEL = "gemini-2.0-flash"

NAME = "gemini"
ROLE = "independent review"
KEY_NAME = "GEMINI_API_KEY"


def available() -> tuple:
    if not api_key(KEY_NAME):
        return False, ("no GEMINI_API_KEY — get a free key at "
                       "aistudio.google.com/apikey, then: printf "
                       "'GEMINI_API_KEY=KEY\\n' > ~/.config/nova-cathedral/gemini.env "
                       "&& chmod 600 ~/.config/nova-cathedral/gemini.env")
    return True, "ready"


def ask(prompt: str, context: str = None, model: str = None,
        timeout: float = 180.0) -> dict:
    key = api_key(KEY_NAME)
    if not key:
        return {"error": available()[1]}
    model = model or DEFAULT_MODEL
    t0 = time.time()
    data = post_json(
        ENDPOINT.format(model=model) + f"?key={key}",
        {"contents": [{"parts": [{"text": build_prompt(prompt, context)}]}]},
        {}, timeout,
    )
    if "error" in data:
        return data
    try:
        cand = data["candidates"][0]
        text = "".join(p.get("text", "") for p in cand["content"]["parts"])
    except (KeyError, IndexError):
        # A safety block returns a well-formed response with no candidates.
        reason = (data.get("promptFeedback", {}).get("blockReason")
                  or "no candidates returned")
        return {"error": f"Gemini returned no answer ({reason})"}
    if not text.strip():
        return {"error": "Gemini returned an empty response"}
    return {"response": text, "model": model, "latency": round(time.time() - t0, 2)}
