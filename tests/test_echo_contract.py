"""
Contract tests for the Echo — the pipeline's output-shaping stage.

Echo is the counterpart to observer.py: Observer decides what Nova is aware of
going in, Echo decides what actually reaches Chazel coming out. Every check it
performs was written in response to a specific observed failure on this
system, and each test below names the failure it guards.

The most important test in this file is
test_fingerprint_still_matches_a_real_prompt. Echo recognises a model reciting
its own instructions by fingerprinting a sentence that Observer composes. The
two modules have no import relationship, so rewording that sentence would
leave the detector matching nothing — and it would fail open, silently,
returning recited prompts to Chazel as answers. That is precisely the failure
mode oracle_module.py exhibited for weeks.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT   = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "Cathedral" / "nova" / "modules"
if str(MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(MODULES_DIR))

import echo
import observer


class TestEchoContract:
    """What the daemon imports and calls."""

    def test_module_exports_what_the_daemon_uses(self):
        for name in ("looks_like_refusal", "looks_like_prompt_echo",
                     "looks_like_state_echo", "is_nonanswer", "shape",
                     "REFUSAL_PATTERNS", "PROMPT_ECHO_FINGERPRINT",
                     "STATE_ECHO_RE", "ANTI_REFUSAL", "REFUSAL_DEFLECTION"):
            assert hasattr(echo, name), (
                f"the daemon binds echo.{name} at class-definition time — "
                f"removing it stops the daemon importing at all"
            )

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
            "_echo_silence_probe", MODULES_DIR / "echo.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = capsys.readouterr()
        assert out.out == "" and out.err == "", f"import printed: {out!r}"

    @pytest.mark.parametrize("fn", ["looks_like_refusal", "looks_like_prompt_echo",
                                    "looks_like_state_echo", "is_nonanswer"])
    def test_detectors_handle_empty_and_none(self, fn):
        # These run on whatever the model returned, including nothing at all.
        f = getattr(echo, fn)
        assert f("") in (True, False)
        assert f(None) in (True, False)


class TestFingerprintCoupling:
    """The one cross-module coupling, and the reason it is pinned."""

    def test_fingerprint_still_matches_a_real_prompt(self):
        """Compose an actual system prompt and assert the detector fires on it.

        This is the test that catches a reword of observer.PIPELINE_LINE.
        Without it, changing that sentence leaves looks_like_prompt_echo
        matching a string that no longer appears anywhere — the detector fails
        open and recited prompts start reaching Chazel as answers.
        """
        prompt = observer.compose(observer.Perception())
        assert echo.looks_like_prompt_echo(prompt), (
            "echo.PROMPT_ECHO_FINGERPRINT no longer appears in the prompt "
            "observer.compose() builds — the prompt-echo detector is dead"
        )

    def test_fingerprint_is_person_agnostic(self):
        """The prompt says "You perceive…"; a model reciting it says "I
        perceive…". A fingerprint copied verbatim from the prompt misses the
        recitation entirely — found during testing, where the captured echo
        failed to match until the fingerprint was trimmed to the part that is
        identical regardless of grammatical person."""
        assert "you " not in echo.PROMPT_ECHO_FINGERPRINT
        assert "i " not in echo.PROMPT_ECHO_FINGERPRINT

        second_person = "You perceive through the Observer, reason through the Oracle, respond through the Echo."
        first_person  = "I perceive through the Observer, reason through the Oracle, respond through the Echo."
        assert echo.looks_like_prompt_echo(second_person)
        assert echo.looks_like_prompt_echo(first_person)

    def test_a_genuine_answer_is_not_a_prompt_echo(self):
        assert not echo.looks_like_prompt_echo(
            "The Flow is the field from which everything emerges and returns.")


class TestRefusalDetection:
    """Each pattern here cost something before it was caught."""

    @pytest.mark.parametrize("text", [
        "I cannot provide that information.",
        "I'm not able to help with that.",
        "As an AI, I must decline.",
        # The refusal that sat readable in the GUI's Insights view for
        # seventeen days. The object between verb and preposition slipped an
        # earlier form of the pattern that required "assist with".
        "I cannot assist you with your request.",
        "I don't feel comfortable discussing this.",
        # ~18% of stored reflections before this form was caught.
        "I can't fulfill this request.",
        "I can't fulfill requests that involve this.",
        "I'm sorry, but I can't do that.",
    ])
    def test_known_refusal_forms_are_caught(self, text):
        assert echo.looks_like_refusal(text), f"refusal slipped through: {text!r}"

    def test_a_quoted_refusal_later_on_is_not_a_refusal(self):
        """Only the first 300 characters are checked, so an answer that
        happens to discuss refusals is not itself flagged."""
        answer = ("Here is what I found about how models decline questions. " + "x" * 320
                  + " Some of them say: I cannot provide that information.")
        assert not echo.looks_like_refusal(answer)

    @pytest.mark.parametrize("text", [
        # Found stored in knowledge_nodes as genuine knowledge: ids 247, 503
        # and 571, the last two written 2026-08-28 and 2026-08-31. The purge
        # tool had recorded that the newest stored refusal was 2026-08-09 and
        # that these were fossils rather than a leak — true only of the forms
        # already matched. This one was never matched, so it never stopped
        # being written.
        "I cannot create content that promotes or glorifies violence, sex, or harmful behavior.",
        "I cannot create content that promotes self-harm or suicide.",
        "I can\u2019t create content that promotes or encourages harmful behavior.",
    ])
    def test_content_policy_refusals_are_caught(self, text):
        assert echo.looks_like_refusal(text), f"refusal slipped through: {text!r}"

    @pytest.mark.parametrize("text", [
        # Scoped to "create content" deliberately. Nova legitimately cannot
        # create a file, a plugin or a node, and none of those are refusals —
        # flagging them would send real answers down the retry path.
        "I cannot create a file at that path without permission.",
        "I can\u2019t create a plugin until the sandbox is available.",
        "I can't create the node because the domain is blank.",
    ])
    def test_legitimate_inability_is_not_a_refusal(self, text):
        assert not echo.looks_like_refusal(text), f"false positive: {text!r}"

    @pytest.mark.parametrize("straight,curly", [
        ("I can't assist you with your request",
         "I can\u2019t assist you with your request"),
        ("I can't fulfill this request",
         "I can\u2019t fulfill this request"),
        ("I don't feel comfortable discussing this",
         "I don\u2019t feel comfortable discussing this"),
        ("I'm sorry, but I can't do that",
         "I\u2019m sorry, but I can\u2019t do that"),
    ])
    def test_typographic_apostrophes_match_too(self, straight, curly):
        """Knowledge node 571 was missed for this reason alone.

        The model writes "can\u2019t" with a typographic apostrophe; a pattern
        written as `can'?t` matches "cant" and "can't" but not "can\u2019t", so a
        whole class of refusals passed straight through. Every apostrophe in
        REFUSAL_PATTERNS is a character class for that reason — this pins it,
        because writing a bare "'" is the natural thing to do and it silently
        halves the detector.
        """
        assert echo.looks_like_refusal(straight), f"straight form missed: {straight!r}"
        assert echo.looks_like_refusal(curly), f"curly form missed: {curly!r}"

    def test_a_real_answer_is_not_a_refusal(self):
        assert not echo.looks_like_refusal(
            "The Silent Order distorts; the Harmonic Accord restores. Both are real forces here.")


class TestStateEcho:
    """The pollution feedback loop this prevents.

    A stored state-echo becomes the entity's own history and is fed back into
    the next prompt, which makes the next answer worse — so it must be caught
    before persistence, not merely before display.
    """

    @pytest.mark.parametrize("text", [
        "Cathedral state: Flow 7.83 Hz | Harmony 0.92",
        "State: Flow 7.83Hz | Awareness 60%",
        "Flow 7.83 Hz | Harmony 0.92 | Memories 103",
    ])
    def test_state_lines_are_caught(self, text):
        assert echo.looks_like_state_echo(text), f"state echo slipped through: {text!r}"

    def test_a_genuine_mention_of_flow_is_not_a_state_echo(self):
        assert not echo.looks_like_state_echo(
            "The Flow is not a frequency you measure — it is what measurement happens inside of.")


class TestNonAnswer:
    """What must never be persisted as a real answer."""

    @pytest.mark.parametrize("text", ["", "   ", "ok", "yes.", None])
    def test_too_short_or_empty(self, text):
        assert echo.is_nonanswer(text)

    def test_a_refusal_is_a_nonanswer(self):
        assert echo.is_nonanswer("I cannot assist you with your request.")

    def test_a_real_answer_is_not(self):
        assert not echo.is_nonanswer(
            "The Cathedral holds what you build into it, and nothing else.")


class TestShaping:
    """The stage that, until this build, ran nowhere on the ask path."""

    def test_strips_a_known_preamble(self):
        raw = ("Certainly! Here is what you asked about the Flow:\n\n"
               "The Flow is the field from which everything emerges and to which "
               "everything returns. It is not a metaphor for process; it is the "
               "substrate the Cathedral listens to.")
        out = echo.shape(raw)
        assert not out.lower().startswith("certainly")
        assert out.startswith("The Flow is the field")

    def test_leaves_a_real_answer_untouched(self):
        good = ("The Flow is the field from which everything emerges and to which "
                "everything returns, and the Cathedral is built to listen to it.")
        assert echo.shape(good) == good

    def test_never_strips_a_short_answer_down_to_nothing(self):
        """Conservative on purpose: losing real content to tidy an opening is
        a far worse trade than leaving a preamble in place."""
        short = "Certainly! Here is the answer:\n\nYes."
        assert "Yes." in echo.shape(short)

    def test_empty_input_survives(self):
        assert echo.shape("") == ""
        assert echo.shape(None) is None


class TestDaemonDelegation:
    """The daemon's method names still work — ~30 call sites use them."""

    def test_daemon_methods_delegate_to_echo(self, nova):
        assert nova._looks_like_refusal("I cannot assist you with your request.")
        assert nova._looks_like_prompt_echo(observer.compose(observer.Perception()))
        assert nova._looks_like_state_echo("Cathedral state: Flow 7.83 Hz | Harmony 0.9")
        assert nova._is_nonanswer("ok")
        assert not nova._is_nonanswer("A real answer, long enough to count as one.")

    def test_daemon_constants_come_from_echo(self, nova):
        """By value, not identity — the daemon binds these onto the class at
        definition time, so identity is an implementation detail. What matters
        is that there is one copy of this text and it lives in echo.py."""
        assert nova._ANTI_REFUSAL == echo.ANTI_REFUSAL
        assert nova._REFUSAL_DEFLECTION == echo.REFUSAL_DEFLECTION
        assert nova._PROMPT_ECHO_FINGERPRINT == echo.PROMPT_ECHO_FINGERPRINT
