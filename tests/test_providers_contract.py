"""
Contract tests for the Council's provider seats.

Every seat must behave identically from the caller's side, because
`nova council` fans out to all of them and a round must survive any subset
being dead. On 2026-09-04 that was not hypothetical: Anthropic and OpenAI were
both out of credit and Gemini had no key, and the round still had to report
cleanly rather than crash.

**No test here makes a network call or spends money.** HTTP is stubbed at
`post_json`, which every cloud provider routes through.

The load-bearing property is the last class: nothing in the daemon's
autonomous loops may import these. The loops run every 5 and 10 minutes; a
cloud provider reachable from one would spend money unattended and let models
talk without the Observer initiating.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULES   = REPO_ROOT / "Cathedral" / "nova" / "modules"
PROV_DIR  = MODULES / "providers"
for p in (str(MODULES), str(PROV_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import base                      # noqa: E402
import providers                 # noqa: E402

CLOUD = ["gemini", "openai", "claude"]
LOCAL = ["ollama", "ollama:gemma", "ollama:llama", "ollama:deepseek"]
ALL   = LOCAL + CLOUD


class TestRegistry:
    def test_every_seat_is_registered(self):
        assert set(providers.names()) == set(ALL)

    def test_each_local_seat_pins_a_distinct_model(self):
        """Four seats on one model is one opinion repeated, not a council.

        The whole value of the local seats is that they come from different
        labs — Alibaba, Google, Meta, DeepSeek — with different training
        corpora and different failure modes. If two seats resolve to the same
        model their agreement proves nothing, and the Council would be
        manufacturing the consensus the Accord says must emerge.
        """
        models = [providers.get(n).MODEL for n in LOCAL]
        assert len(set(models)) == len(models), f"duplicate models: {models}"

    def test_cloud_seats_stay_listed_when_unavailable(self):
        """A seat reporting "no credit" is information the Observer needs.
        Dropping it silently would conceal provenance."""
        assert set(CLOUD) <= set(providers.DEFAULT_COUNCIL)

    def test_registry_exposes_installed_models(self):
        """`nova status` needs "what can run locally" without reaching through
        a seat. It used to do PROVIDERS["ollama"].installed_models(), which
        broke silently the moment that key became a lineage seat object — the
        CLI crashed mid-report, after printing the daemon line."""
        assert callable(providers.installed_models)
        assert isinstance(providers.installed_models(), list)

    def test_no_seat_is_assumed_to_be_a_module(self):
        """Every registry value must satisfy the protocol, whether it is a
        module or a seat instance. Mixing the two is what broke status."""
        for name in providers.names():
            seat = providers.get(name)
            for attr in ("ask", "available", "NAME", "ROLE"):
                assert hasattr(seat, attr), f"{name} lacks {attr}"

    def test_local_council_is_cloud_free(self):
        """LOCAL_COUNCIL must never reach a paid seat."""
        assert set(providers.LOCAL_COUNCIL) == set(LOCAL)
        assert not (set(providers.LOCAL_COUNCIL) & set(CLOUD))

    def test_unknown_seat_is_an_error_not_an_exception(self):
        r = providers.ask("nonexistent", "hello")
        assert "error" in r and "unknown provider" in r["error"]

    def test_status_reports_every_seat(self):
        st = providers.status()
        assert {s["name"] for s in st} == set(ALL)
        for s in st:
            assert isinstance(s["available"], bool)
            assert s["detail"], f"{s['name']} gave no reason"

    def test_a_seat_that_raises_costs_only_that_seat(self, monkeypatch):
        """A provider raising must not take the round down."""
        mod = providers.get("ollama")
        monkeypatch.setattr(mod, "ask",
                            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
        r = providers.ask("ollama", "hi")
        assert "error" in r and "boom" in r["error"]


class TestUniformShape:
    @pytest.mark.parametrize("name", ALL)
    def test_seat_exposes_the_protocol(self, name):
        mod = providers.get(name)
        for attr in ("ask", "available", "NAME", "ROLE"):
            assert hasattr(mod, attr), f"{name} is missing {attr}"

    @pytest.mark.parametrize("name", ALL)
    def test_available_returns_bool_and_reason(self, name):
        ok, why = providers.get(name).available()
        assert isinstance(ok, bool) and isinstance(why, str) and why

    @pytest.mark.parametrize("name", CLOUD)
    def test_missing_key_is_an_error_dict_not_a_raise(self, name, monkeypatch):
        monkeypatch.setattr(base, "api_key", lambda *a, **k: "")
        mod = providers.get(name)
        monkeypatch.setattr(mod, "api_key", lambda *a, **k: "", raising=False)
        r = mod.ask("hello")
        assert isinstance(r, dict) and "error" in r


class TestSecretsLoading:
    def test_quoted_values_are_unquoted(self, tmp_path):
        """anthropic.env stores its key in double quotes. systemd strips them;
        a naive split does not, and the trailing quote produces a 401 that
        reads exactly like a revoked key. That cost real debugging time."""
        (tmp_path / "x.env").write_text('ANTHROPIC_API_KEY="sk-ant-abc123"\n')
        assert base.load_secrets(tmp_path)["ANTHROPIC_API_KEY"] == "sk-ant-abc123"

    def test_single_quotes_and_bare_values(self, tmp_path):
        (tmp_path / "a.env").write_text("A='one'\nB=two\n# c=comment\n\n")
        s = base.load_secrets(tmp_path)
        assert s == {"A": "one", "B": "two"}

    def test_missing_directory_is_empty_not_fatal(self, tmp_path):
        assert base.load_secrets(tmp_path / "nope") == {}

    def test_environment_wins_over_file(self, tmp_path, monkeypatch):
        (tmp_path / "a.env").write_text("K=from_file\n")
        monkeypatch.setenv("K", "from_env")
        assert base.api_key("K", tmp_path) == "from_env"


class TestErrorMessagesStaySpecific:
    """The message inside an HTTP error body is the actionable part."""

    def test_http_error_body_is_surfaced(self, monkeypatch):
        import io, json as _json, urllib.error, urllib.request

        body = io.BytesIO(_json.dumps(
            {"error": {"message": "Your credit balance is too low"}}).encode())

        def boom(*a, **k):
            raise urllib.error.HTTPError("u", 400, "Bad Request", {}, body)
        monkeypatch.setattr(urllib.request, "urlopen", boom)

        r = base.post_json("https://example.invalid", {}, {}, 5)
        assert "credit balance is too low" in r["error"], (
            "the actionable message was flattened away"
        )

    def test_transport_failure_is_a_dict(self, monkeypatch):
        import urllib.request
        monkeypatch.setattr(urllib.request, "urlopen",
                            lambda *a, **k: (_ for _ in ()).throw(OSError("no route")))
        assert "error" in base.post_json("https://example.invalid", {}, {}, 5)


class TestContextIsShared:
    def test_context_is_prepended_once_and_separated(self):
        out = base.build_prompt("the question", "the context")
        assert out.startswith("the context")
        assert out.endswith("the question")
        assert "---" in out

    def test_no_context_returns_the_prompt_unchanged(self):
        assert base.build_prompt("q", None) == "q"
        assert base.build_prompt("q", "") == "q"


class TestNotReachableFromAutonomousLoops:
    """The Observer initiates. Models do not talk on a timer.

    The daemon's evolution loop (10 min) and eyemoeba loop (5 min) run
    unattended. If either could reach a cloud provider, Nova would spend money
    without being asked — the exact thing claude_bridge.py's own docstring
    forbids: "nothing here should run silently or on a timer."
    """

    def test_the_daemon_does_not_import_providers(self):
        src = (REPO_ROOT / "Cathedral" / "nova" / "daemon"
               / "nova_cathedral_daemon.py").read_text()
        for form in ("import providers", "from providers"):
            assert form not in src, (
                f"the daemon imports the provider registry ({form!r}) — a "
                f"cloud seat is now reachable from an autonomous loop"
            )

    def test_no_module_outside_the_cli_imports_providers(self):
        offenders = []
        for py in (REPO_ROOT / "Cathedral" / "nova" / "modules").glob("*.py"):
            if "import providers" in py.read_text():
                offenders.append(py.name)
        assert not offenders, f"providers imported outside the CLI by: {offenders}"
