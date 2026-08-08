"""
Regression test for the "Nova denies being Nova" bug: /api/chat's error
placeholder strings must never be mistaken for a real assistant reply, or
they get appended to conversation history/context and the model spirals
trying to make sense of a "previous reply" that was actually a system
error — confirmed live, this is exactly what happened before the fix.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Cathedral" / "nova" / "gui"))

from nova_app import _is_chat_error_reply


def test_detects_reasoning_failure_placeholder():
    assert _is_chat_error_reply("[Reasoning call failed: timed out]") is True


def test_detects_ollama_error_placeholder():
    assert _is_chat_error_reply("[Ollama error: connection refused]") is True


def test_normal_reply_is_not_an_error():
    assert _is_chat_error_reply("Sure, here's what I found.") is False


def test_reply_merely_mentioning_ollama_is_not_an_error():
    # Must match on the placeholder's exact leading format, not just
    # loosely contain these words — a real reply that happens to discuss
    # Ollama or reasoning should never be misclassified as a failure.
    assert _is_chat_error_reply("Ollama error handling is a good topic to discuss.") is False
    assert _is_chat_error_reply("Reasoning call failed once but I recovered.") is False
