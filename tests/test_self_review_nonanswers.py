"""A non-answer must never become a file edit.

Nova's self-review asks for one improvement and offers an explicit way out:
reply with the single word NOTHING. Two ways of saying nothing got through
anyway, and both were **applied to real files**:

  2026-09-03  plugins/sandbox_plugins/gematria.py
              applied improvement, in full: "NOTHING"

  2026-09-04  plugins/sandbox_plugins/weather.py   (twice)
              applied improvement: "Identify ONE improvement to code you can
              actually see above." — the prompt's own instruction, echoed back

The daemon checked for a decline only at the start of the *raw response*, so a
model that wrapped it in the requested JSON slipped past: the response begins
with "{", the JSON parses, and NOTHING is handed to the file writer as the
change to make. Echo's prompt-echo guard does not help here — it fingerprints
the Observer's pipeline line, which is in the chat system prompt, not this one.

A decline that gets applied is worse than no decline, because it edits a file
on the strength of an answer that said not to.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULES = REPO_ROOT / "Cathedral" / "nova" / "modules"
if str(MODULES) not in sys.path:
    sys.path.insert(0, str(MODULES))

import evolution_engine as evo


class TestDeclineIsHonoured:
    @pytest.mark.parametrize("text", [
        "NOTHING", "nothing", " Nothing ", "NOTHING.", '"NOTHING"',
        "NONE", "N/A", "no change", "No changes",
    ])
    def test_a_decline_is_recognised(self, text):
        assert evo.is_declined(text) is True, f"{text!r} was not read as a decline"

    @pytest.mark.parametrize("text", [
        "Cache the parsed config instead of re-reading it each call",
        "Nothing is validating the timeout argument before use",
        "Rename the shadowed variable in fetch_weather",
    ])
    def test_a_real_proposal_is_not_a_decline(self, text):
        """'Nothing is validating...' begins with the word and is a real
        suggestion — the check must be the whole answer, not a prefix."""
        assert evo.is_declined(text) is False, f"{text!r} was wrongly discarded"

    def test_empty_counts_as_declined(self):
        assert evo.is_declined("") is True
        assert evo.is_declined(None) is True


class TestPromptEchoIsCaught:
    PROMPT = (
        "Here are two files from your own source.\n"
        "Identify ONE improvement to code you can actually see above. Quote the "
        "function or line it concerns, so the suggestion can be checked against "
        "the source.\n"
        "If nothing above genuinely needs changing, reply with exactly the "
        "single word NOTHING."
    )

    def test_the_exact_sentence_that_was_applied_twice(self):
        """The real one, from weather.py on 2026-09-04."""
        assert evo.echoes_the_prompt(
            "Identify ONE improvement to code you can actually see above.",
            self.PROMPT) is True

    def test_a_fragment_of_the_instructions_is_an_echo(self):
        assert evo.echoes_the_prompt(
            "Quote the function or line it concerns", self.PROMPT) is True

    def test_whitespace_differences_do_not_hide_an_echo(self):
        assert evo.echoes_the_prompt(
            "Identify  ONE   improvement\nto code you can actually see above",
            self.PROMPT) is True

    def test_a_genuine_proposal_is_not_an_echo(self):
        assert evo.echoes_the_prompt(
            "fetch_weather re-parses the config on every call; cache it",
            self.PROMPT) is False

    def test_a_short_phrase_is_not_judged(self):
        """Common short words appear in any prompt by chance. Only a
        substantial verbatim overlap is evidence of restatement."""
        assert evo.echoes_the_prompt("the source", self.PROMPT) is False

    def test_no_prompt_means_no_echo(self):
        assert evo.echoes_the_prompt("some improvement text here", "") is False
