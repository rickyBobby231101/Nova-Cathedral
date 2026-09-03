"""
Contract tests for web_search — the backbone of goal research.

`resolve_method` routes research goals to web_search, and it is the method that
actually works: 163 of 169 goals completed through it, against reflect's
160 of 312. If this module's return shape drifts, goal research does not crash
— it silently produces goals that fail, which is exactly the failure that hid
for five months and made every goal Chazel set himself fail.

The daemon reads `context` and `error` off the returned dict and nothing else,
so those are what is pinned here.

**No test in this file touches the network.** DDGS and urlopen are replaced,
so the suite stays deterministic and runnable offline — a contract test that
needs the internet is one that gets skipped, and a skipped test guards nothing.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT   = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "Cathedral" / "nova" / "modules"
if str(MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(MODULES_DIR))

import web_search


class TestWebSearchContract:
    def test_module_exports_what_the_daemon_imports(self):
        # daemon: from web_search import search_and_summarize, wikipedia_summary
        for name in ("search_and_summarize", "wikipedia_summary",
                     "search_web", "fetch_page"):
            assert hasattr(web_search, name), (
                f"the daemon imports web_search.{name}; without it "
                f"_WEB_SEARCH_AVAILABLE goes False and every research goal "
                f"silently reroutes"
            )

    def test_importing_the_module_is_silent(self, capsys):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_websearch_silence_probe", MODULES_DIR / "web_search.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = capsys.readouterr()
        assert out.out == "" and out.err == "", f"import printed: {out!r}"


class TestSearchAndSummarize:
    """The dict the daemon destructures at three call sites."""

    def _fake_results(self, monkeypatch, results):
        monkeypatch.setattr(web_search, "search_web",
                            lambda q, n=3: results)

    def test_returns_query_results_and_context(self, monkeypatch):
        self._fake_results(monkeypatch, [
            {"title": "The Flow", "href": "https://example.invalid/a",
             "body": "A field from which everything emerges."},
        ])
        out = web_search.search_and_summarize("what is the flow")
        assert out["query"] == "what is the flow"
        assert isinstance(out["results"], list)
        assert "error" not in out

    def test_context_carries_the_body_text(self, monkeypatch):
        """`context` is the only field that reaches the model — the daemon
        injects it into the prompt. A shape change that keeps `results` but
        empties `context` produces research goals that complete having learned
        nothing, and nothing reports it."""
        self._fake_results(monkeypatch, [
            {"title": "Resonance", "href": "https://example.invalid/b",
             "body": "Standing waves reinforce at matching frequencies."},
        ])
        ctx = web_search.search_and_summarize("resonance")["context"]
        assert "Standing waves reinforce" in ctx
        assert "Resonance" in ctx

    def test_an_upstream_error_is_reported_not_raised(self, monkeypatch):
        """The daemon calls this inside asyncio.to_thread; a raise there
        becomes a failed goal with no reason recorded."""
        self._fake_results(monkeypatch, [{"error": "duckduckgo-search not installed"}])
        out = web_search.search_and_summarize("anything")
        assert "error" in out
        assert out["context"] == ""
        assert out["results"] == []
        assert out["query"] == "anything"

    def test_no_results_still_returns_the_full_shape(self, monkeypatch):
        self._fake_results(monkeypatch, [])
        out = web_search.search_and_summarize("a query matching nothing")
        for key in ("query", "results", "context"):
            assert key in out
        assert out["context"] == ""

    def test_missing_fields_in_a_result_do_not_raise(self, monkeypatch):
        """Upstream shape is not guaranteed — a result missing body or href
        must degrade, not explode inside the research loop."""
        self._fake_results(monkeypatch, [{"title": "only a title"}, {}])
        out = web_search.search_and_summarize("partial")
        assert isinstance(out["context"], str)


class TestWikipediaSummary:
    def test_a_failure_returns_a_dict_not_an_exception(self, monkeypatch):
        """Offline, DNS-blocked, rate-limited — all of it has to come back as
        a dict, because the caller does `return wikipedia_summary(topic)`
        straight into the socket reply."""
        def boom(*a, **k):
            raise OSError("network unreachable")
        monkeypatch.setattr(web_search.urllib.request, "urlopen", boom)

        out = web_search.wikipedia_summary("The Flow")
        assert isinstance(out, dict)
        assert "error" in out
        assert out["title"] == "The Flow"
        assert out["summary"] == ""

    def test_a_successful_lookup_maps_the_fields(self, monkeypatch):
        import io, json

        payload = json.dumps({
            "title": "Resonance",
            "extract": "A phenomenon of amplified oscillation.",
            "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Resonance"}},
        }).encode()
        monkeypatch.setattr(web_search.urllib.request, "urlopen",
                            lambda *a, **k: io.BytesIO(payload))

        out = web_search.wikipedia_summary("Resonance")
        assert out["title"] == "Resonance"
        assert "amplified oscillation" in out["summary"]
        assert out["url"].endswith("/Resonance")
        assert "error" not in out
