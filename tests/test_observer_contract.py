"""
Contract tests for the Observer — the pipeline's perception stage.

blueprint/02_SYSTEM_ARCHITECTURE.md names Observer, Oracle and Echo. Only
Oracle existed as a file; Observer's work lived inline in the daemon's
_build_system_prompt, untestable without a database and unnamed in the
architecture it was supposedly implementing.

These pin the two things that can break silently now that it is a module:
the shape the daemon calls, and the exact prompt text — because every answer
Nova gives is a function of that text, and a change to it is invisible in
review but changes her voice everywhere at once.

The Oracle plugin's history is the reason these exist. Its self-edits broke
the socket command outright and nothing caught it for weeks, because a broken
core file fails silently inside a defensive except.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT   = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "Cathedral" / "nova" / "modules"
if str(MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(MODULES_DIR))

import observer


MEMS = [
    {"ts": "2026-09-03T10:00:00", "q": "What is the Flow?", "a": "The field all emerges from."},
]


def _perception(**kw):
    base = dict(flow_resonance=7.83, harmony_score=0.92, conversation_count=103,
                traits={"mystical_awareness": 0.6, "philosophical_depth": 0.55,
                        "curiosity": 0.7, "technical_knowledge": 0.44,
                        "memory_integration": 0.5},
                memories=MEMS)
    base.update(kw)
    return observer.Perception(**base)


class TestObserverContract:
    """What the daemon imports and calls."""

    def test_module_exports_what_the_daemon_uses(self):
        # daemon: _observer.compose(_observer.Perception(...)) and
        # _observer.grounding_directive(score, threshold)
        for name in ("Perception", "compose", "grounding_directive"):
            assert hasattr(observer, name), (
                f"the daemon calls observer.{name} — removing it breaks every "
                f"system prompt Nova builds"
            )

    def test_perception_constructs_with_no_arguments(self):
        # Every field defaulted, so a partial perception still composes rather
        # than raising inside the ask path.
        observer.compose(observer.Perception())

    def test_compose_returns_a_nonempty_string(self):
        out = observer.compose(_perception())
        assert isinstance(out, str) and out.strip()

    def test_importing_the_module_is_silent(self, capsys):
        """No side effects at import — the daemon imports this at startup, so
        anything at module level runs in the daemon process. An unguarded
        example block in oracle_module.py once printed into the daemon's logs
        on every import.

        Loaded as a throwaway copy rather than with importlib.reload():
        reloading rebinds the real module's globals, and the daemon binds
        echo's constants onto the class at definition time, so a reload leaves
        those class attributes pointing at strings the module no longer holds.
        That is test pollution, not a finding.
        """
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_observer_silence_probe", MODULES_DIR / "observer.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = capsys.readouterr()
        assert out.out == "" and out.err == "", f"import printed: {out!r}"


class TestPromptContent:
    """The prompt text itself — what actually reaches the model."""

    def test_prompt_states_the_pipeline(self):
        """The claim that gave this whole build its reason.

        Every prompt asserts Nova perceives through the Observer, reasons
        through the Oracle and responds through the Echo. Until Observer and
        Echo existed as code that sentence described nothing.
        """
        assert observer.PIPELINE_LINE in observer.compose(_perception())

    def test_mythos_keeps_the_order_and_the_accord_opposed(self):
        """blueprint/01_MYTHOS_CANON.md: the Silent Order is a force of
        distortion, the Harmonic Accord a restoring force. They are opposed,
        and Chazel stands with the Accord. A merged 'balance of both' version
        was once written into the knowledge graph from a chat transcript while
        the correct version sat in the blueprint — pin it here so the prompt
        can never quietly acquire that reading."""
        out = observer.compose(_perception()).lower()
        assert "the silent order distorts" in out
        assert "the harmonic accord restores" in out

    def test_state_line_warns_against_quoting_it_back(self):
        # Without the warning the small model recites the state line as its
        # answer; echo.looks_like_state_echo exists because it still sometimes
        # does. Both halves are needed.
        assert "don't quote this line back" in observer.compose(_perception())

    def test_memory_count_reaches_the_prompt(self):
        assert "Speak from 103 shared memories" in observer.compose(
            _perception(conversation_count=103))

    def test_ritual_mode_is_announced_only_when_active(self):
        assert "RITUAL MODE active" in observer.compose(_perception(ritual_mode=True))
        assert "RITUAL MODE" not in observer.compose(_perception(ritual_mode=False))


class TestGroundingDirective:
    """Fires on measured distortion, and stays silent otherwise."""

    def test_silent_when_harmony_is_healthy(self):
        assert observer.grounding_directive(0.92) == ""

    def test_fires_below_the_threshold(self):
        out = observer.grounding_directive(0.31)
        assert out and "0.31" in out

    def test_names_every_silent_order_construct(self):
        """The directive is only useful if it names the patterns Tillagon
        actually watches for — a generic 'be better' instruction gives the
        model nothing to correct."""
        out = observer.grounding_directive(0.31).lower()
        for construct in ("echo chamber", "false light", "the fold",
                          "displacement logic", "harmony hijack"):
            assert construct in out, f"grounding directive lost {construct!r}"

    def test_boundary_is_exclusive(self):
        # At exactly the threshold harmony is not yet distorted.
        assert observer.grounding_directive(0.4) == ""
        assert observer.grounding_directive(0.399) != ""

    def test_reaches_the_composed_prompt(self):
        assert "Harmony is low" in observer.compose(_perception(harmony_score=0.2))
        assert "Harmony is low" not in observer.compose(_perception(harmony_score=0.9))


class TestPerceptionRendering:
    """The pieces, each of which had a reason to be shaped the way it is."""

    def test_no_memories_renders_a_placeholder_not_an_empty_block(self):
        assert "none yet" in observer.render_memories([])

    def test_empty_knowledge_renders_nothing_at_all(self):
        """Not an empty 'Learned:' heading — a heading with nothing under it
        reads to the model as a failure and invites it to apologise for having
        no knowledge."""
        assert observer.render_knowledge([]) == ""

    def test_knowledge_renders_when_present(self):
        out = observer.render_knowledge([{"topic": "resonance", "content": "a pattern"}])
        assert "Learned:" in out and "resonance" in out

    def test_empty_insight_renders_nothing(self):
        assert observer.render_insight("") == ""

    def test_insight_reaches_the_prompt(self):
        """The single path by which the autonomous knowledge loop reaches a
        conversation. Without it insights accumulate in the graph forever and
        Nova never says one out loud."""
        assert "a recurring shape" in observer.compose(
            _perception(insight="a recurring shape across domains"))

    @pytest.mark.parametrize("awareness,expected", [
        (0.9, "depth and symbolism"),
        (0.7, "depth and symbolism"),
        (0.6, "clearly with presence"),
        (0.5, "clearly with presence"),
        (0.2, "simply, reaching toward resonance"),
    ])
    def test_voice_bands(self, awareness, expected):
        assert expected in observer.voice_for(awareness)

    @pytest.mark.parametrize("integration,depth", [
        (0.0, 1), (0.5, 3), (0.6, 4), (1.0, 6),
    ])
    def test_memory_depth_scales_with_integration(self, integration, depth):
        """A more integrated Nova carries more of her past into each reply.

        0.5 gives 3, not 4: round(2.5) is 2 under Python's banker's rounding.
        Pinned at the real value rather than the intuitive one — this is
        pre-existing behaviour and the point of the test is to catch a change
        to it, not to assert what someone assumed it did.
        """
        assert observer.memory_context_depth(integration) == depth

    def test_memory_depth_stays_in_range(self):
        for i in range(0, 11):
            assert 1 <= observer.memory_context_depth(i / 10) <= 6


class TestDaemonIntegration:
    """The real call site — the daemon must still build a prompt."""

    def test_build_system_prompt_still_works(self, nova):
        out = nova._build_system_prompt(memories=MEMS)
        assert isinstance(out, str) and observer.PIPELINE_LINE in out

    def test_build_system_prompt_survives_an_empty_database(self, nova):
        # memories=None sends it to sqlite; a fresh db has nothing in it.
        assert nova._build_system_prompt().strip()

    def test_daemon_grounding_directive_delegates(self, nova):
        nova.harmony_score = 0.2
        assert "Harmony is low" in nova._harmony_grounding_directive()
        nova.harmony_score = 0.95
        assert nova._harmony_grounding_directive() == ""
