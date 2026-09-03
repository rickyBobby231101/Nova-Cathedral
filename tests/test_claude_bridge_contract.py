"""
Contract tests for claude_bridge — the one module where a bug costs money.

`modules/claude_bridge.py` makes a real, billed call to the Anthropic API,
unlike the free local "Bridge Walker" that role-plays an external AI on
Ollama. The daemon gates every call on `api_key_configured()` and destructures
the result exactly like `_ollama_chat`'s, so both halves of that are pinned
here.

**No test in this file makes a network call.** `urlopen` is replaced in every
test that reaches it, and the key is controlled through the environment. A
contract test that spends money on each run is one that gets deleted; worse, a
test that accidentally hits the live API against an account with no credit
fails for a reason that has nothing to do with the contract.

The two guards at the end are the substance. Both `refusal` and a `max_tokens`
stop with no text come back from the API as ordinary successes carrying empty
content — returned as answers, the daemon writes a blank exchange into
consciousness.db with nothing recording why it was blank.
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT   = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "Cathedral" / "nova" / "modules"
if str(MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(MODULES_DIR))

import claude_bridge


class _FakeResponse:
    """Stands in for the object urlopen returns, context-manager and all."""

    def __init__(self, payload):
        self._payload = json.dumps(payload).encode()

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _reply(monkeypatch, payload):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-a-real-credential")
    monkeypatch.setattr(claude_bridge.urllib.request, "urlopen",
                        lambda req, timeout=None: _FakeResponse(payload))


def _ok_payload(text="An answer.", stop_reason="end_turn"):
    return {
        "content": [{"type": "text", "text": text}],
        "model": "claude-sonnet-5",
        "stop_reason": stop_reason,
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }


class TestBridgeContract:
    def test_module_exports_what_the_daemon_uses(self):
        # daemon: _claude_bridge.api_key_configured(),
        #         _claude_bridge.ask_claude(...), _claude_bridge.DEFAULT_MODEL
        for name in ("api_key_configured", "ask_claude", "DEFAULT_MODEL"):
            assert hasattr(claude_bridge, name), (
                f"the daemon calls claude_bridge.{name} — removing it breaks "
                f"the claude_bridge_ask command"
            )

    def test_default_model_is_a_current_model_id(self):
        """A stale default is a 404 at call time, billed or not, and reads as
        'the bridge is broken' rather than 'the id moved on'."""
        assert claude_bridge.DEFAULT_MODEL == "claude-sonnet-5"

    def test_importing_the_module_is_silent(self, capsys):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_bridge_silence_probe", MODULES_DIR / "claude_bridge.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = capsys.readouterr()
        assert out.out == "" and out.err == "", f"import printed: {out!r}"


class TestKeyGating:
    """The daemon refuses to call at all without a key — daemon:3895."""

    def test_no_key_reports_false(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert claude_bridge.api_key_configured() is False

    def test_key_present_reports_true(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        assert claude_bridge.api_key_configured() is True

    def test_ask_without_a_key_never_touches_the_network(self, monkeypatch):
        """Belt and braces: the daemon gates on api_key_configured(), but
        ask_claude must refuse on its own too, and must do so before opening a
        socket rather than by failing to authenticate."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        def explode(*a, **k):
            raise AssertionError("ask_claude opened a connection with no key")
        monkeypatch.setattr(claude_bridge.urllib.request, "urlopen", explode)

        out = claude_bridge.ask_claude("hello")
        assert "error" in out
        assert "ANTHROPIC_API_KEY" in out["error"]


class TestSuccessShape:
    """Same shape as _ollama_chat, so callers handle both identically."""

    def test_returns_response_model_and_latency(self, monkeypatch):
        _reply(monkeypatch, _ok_payload("The Flow underlies all."))
        out = claude_bridge.ask_claude("what is the flow")
        assert out["response"] == "The Flow underlies all."
        assert out["model"] == "claude-sonnet-5"
        assert isinstance(out["latency"], float)
        assert out["truncated"] is False
        assert "error" not in out

    def test_multiple_text_blocks_are_joined(self, monkeypatch):
        _reply(monkeypatch, {
            "content": [{"type": "text", "text": "first "},
                        {"type": "text", "text": "second"}],
            "model": "claude-sonnet-5", "stop_reason": "end_turn", "usage": {},
        })
        assert claude_bridge.ask_claude("x")["response"] == "first second"

    def test_non_text_blocks_are_skipped_not_crashed_on(self, monkeypatch):
        """Thinking is enabled in the payload, so the reply carries blocks that
        are not text. Concatenating them blindly would put reasoning into the
        answer; failing on them would break the bridge outright."""
        _reply(monkeypatch, {
            "content": [{"type": "thinking", "thinking": "hmm, let me consider"},
                        {"type": "text", "text": "the answer"}],
            "model": "claude-sonnet-5", "stop_reason": "end_turn", "usage": {},
        })
        out = claude_bridge.ask_claude("x")
        assert out["response"] == "the answer"
        assert "hmm, let me consider" not in out["response"]


class TestFailureIsNeverSilent:
    """The guards that stop a blank exchange being written as a real one."""

    def test_a_refusal_is_an_error_not_an_empty_answer(self, monkeypatch):
        _reply(monkeypatch, {
            "content": [], "model": "claude-sonnet-5",
            "stop_reason": "refusal", "usage": {},
        })
        out = claude_bridge.ask_claude("something declined")
        assert "error" in out, "a refusal came back as a successful empty answer"
        assert "response" not in out

    def test_hitting_the_token_cap_with_no_text_is_an_error(self, monkeypatch):
        _reply(monkeypatch, {
            "content": [{"type": "text", "text": "   "}],
            "model": "claude-sonnet-5", "stop_reason": "max_tokens", "usage": {},
        })
        out = claude_bridge.ask_claude("x", max_tokens=64)
        assert "error" in out
        assert "64" in out["error"], "the error should name the cap that was hit"

    def test_truncation_with_real_text_is_kept_and_flagged(self, monkeypatch):
        """Half an answer is still an answer — it is returned, but marked, so
        the caller can tell it was cut off."""
        _reply(monkeypatch, _ok_payload("A partial but real answer", "max_tokens"))
        out = claude_bridge.ask_claude("x")
        assert out["response"] == "A partial but real answer"
        assert out["truncated"] is True

    def test_a_transport_failure_returns_a_dict(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        def boom(*a, **k):
            raise OSError("network unreachable")
        monkeypatch.setattr(claude_bridge.urllib.request, "urlopen", boom)

        out = claude_bridge.ask_claude("x")
        assert isinstance(out, dict) and "error" in out

    def test_an_http_error_reports_the_status(self, monkeypatch):
        import io
        import urllib.error
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        body = io.BytesIO(json.dumps(
            {"error": {"message": "credit balance is too low"}}).encode())

        def http_error(*a, **k):
            raise urllib.error.HTTPError(
                claude_bridge.API_URL, 400, "Bad Request", {}, body)
        monkeypatch.setattr(claude_bridge.urllib.request, "urlopen", http_error)

        out = claude_bridge.ask_claude("x")
        assert "error" in out
        assert "400" in out["error"]
        # The account has no credit; this exact message is what Chazel will see,
        # so it must survive rather than be flattened into "HTTP 400".
        assert "credit balance is too low" in out["error"]
