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
# A stable alias rather than a numbered version. `gemini-2.0-flash` was the
# default here until 2026-09-06, when the first real call returned:
#   HTTP 404: This model models/gemini-2.0-flash is no longer available.
# Numbered Gemini models retire; the `-latest` aliases do not, and a Council
# seat that breaks silently when a vendor sunsets a version is worse than one
# that occasionally shifts capability.
DEFAULT_MODEL = "gemini-flash-latest"
# Lighter, and reachable when the shared flash tier is saturated.
FALLBACK_MODEL = "gemini-flash-lite-latest"

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
    body = {"contents": [{"parts": [{"text": build_prompt(prompt, context)}]}]}
    data = post_json(ENDPOINT.format(model=model) + f"?key={key}", body, {}, timeout)

    # 503 means the free tier is busy, not that anything is wrong. Measured
    # 2026-09-06: flash-latest returned 503 while flash-lite-latest answered in
    # 15.7s. A seat that drops out because a shared free model is momentarily
    # loaded is a seat that will be empty exactly when the Council is busiest,
    # so fall to the lighter model once before giving up.
    if "error" in data and "503" in data["error"] and model == DEFAULT_MODEL:
        data = post_json(ENDPOINT.format(model=FALLBACK_MODEL) + f"?key={key}",
                         body, {}, timeout)
        if "error" not in data:
            model = FALLBACK_MODEL

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
