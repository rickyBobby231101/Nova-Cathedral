"""
Regression test for the Ollama stream-cancellation fix.

Root cause this guards against: _ollama_chat used to send stream:false, so
Ollama computed the whole response server-side before writing anything —
a client timeout had no in-flight I/O to fail on, so timed-out generations
kept running as orphaned `ollama runner` processes for minutes, burning CPU
against every queued request. The fix streams chunks and explicitly closes
the connection once the wall-clock budget is exceeded, which reaches
Ollama as a broken pipe on its next write and does get it to stop.

These tests mock urllib entirely — no real Ollama/network involved — and
check the two things that actually matter: (1) resp.close() is called when
the timeout is exceeded, since that's the real cancellation mechanism, not
just the exception, and (2) a normal, fast stream still reconstructs the
full response correctly.
"""
import json
import time

import pytest


class _FakeTagsResponse:
    """Stands in for the /api/tags reachability check."""
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return b"{}"


class _FakeStreamResponse:
    """Iterating yields NDJSON lines like Ollama's real streaming response.
    Optionally sleeps between chunks so real wall-clock time can exceed a
    short test timeout without needing to fake time.time() globally.
    """
    def __init__(self, chunks, delay=0.0):
        self._chunks = chunks
        self._delay = delay
        self.closed = False
        self.close_call_count = 0

    def __iter__(self):
        for c in self._chunks:
            if self._delay:
                time.sleep(self._delay)
            yield json.dumps(c).encode()

    def close(self):
        self.closed = True
        self.close_call_count += 1


def _install_fake_urlopen(monkeypatch, mod, stream_response):
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        # First call is always the /api/tags reachability probe.
        if calls["n"] == 1:
            return _FakeTagsResponse()
        return stream_response

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)
    return calls


@pytest.mark.asyncio
async def test_normal_stream_reconstructs_full_text(nova, monkeypatch):
    import nova_cathedral_daemon as mod

    chunks = [
        {"message": {"content": "Hello"}, "done": False},
        {"message": {"content": " there"}, "done": False},
        {"message": {"content": "."}, "done": True},
    ]
    resp = _FakeStreamResponse(chunks)
    _install_fake_urlopen(monkeypatch, mod, resp)

    result = await nova._ollama_chat([{"role": "user", "content": "hi"}], timeout=30)

    assert result["response"] == "Hello there."
    assert resp.close_call_count == 1  # closed exactly once, via the finally block


@pytest.mark.asyncio
async def test_exceeding_timeout_closes_connection_and_reports_error(nova, monkeypatch):
    import nova_cathedral_daemon as mod

    # Each chunk sleeps 0.05s; timeout=0.03s means the *first* time-check
    # after a chunk already exceeds budget — mirrors a real slow generation
    # blowing through the deadline mid-stream, not just at the start.
    chunks = [
        {"message": {"content": "slow"}, "done": False},
        {"message": {"content": " token"}, "done": False},
        {"message": {"content": " by token"}, "done": False},
        {"message": {"content": " forever"}, "done": True},
    ]
    resp = _FakeStreamResponse(chunks, delay=0.05)
    _install_fake_urlopen(monkeypatch, mod, resp)

    result = await nova._ollama_chat([{"role": "user", "content": "hi"}], timeout=0.03)

    assert "error" in result
    assert "exceeded" in result["error"]
    # This is the actual fix, not the exception — close() must have been
    # called on the still-open response before we gave up, since that's
    # what causes Ollama to notice (broken pipe on its next write) and
    # actually stop generating instead of running on as an orphan.
    assert resp.close_call_count >= 1
    assert resp.closed is True


@pytest.mark.asyncio
async def test_ollama_unreachable_reports_clean_error(nova, monkeypatch):
    import nova_cathedral_daemon as mod

    def fake_urlopen(req, timeout=None):
        raise OSError("connection refused")

    monkeypatch.setattr(mod.urllib.request, "urlopen", fake_urlopen)

    result = await nova._ollama_chat([{"role": "user", "content": "hi"}], timeout=5)
    assert "error" in result
    assert "Ollama not running" in result["error"]
