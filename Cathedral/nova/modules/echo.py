#!/usr/bin/env python3
"""
The Echo — Nova's formatting and output-shaping layer.

The third stage of the pipeline in blueprint/02_SYSTEM_ARCHITECTURE.md, and
the counterpart to observer.py: Observer decides what Nova is aware of going
in, Oracle generates, Echo decides what actually reaches Chazel coming out.

Everything here already existed, scattered across the daemon as private
methods with no shared name — the refusal detector, the prompt-echo
fingerprint, the state-echo detector, the non-answer guard. Each was written
in response to a specific observed failure, and those reasons are preserved in
the docstrings below because they are the whole justification for the checks:
none of these are hypothetical.

The failures this layer exists to catch, all measured on this system:

  * False refusals. Small local models trip their own safety training on
    Cathedral-mythos phrasing ("sacred", "ritual") and refuse a perfectly
    ordinary question. One such refusal sat readable in the GUI's Insights
    view for seventeen days. "I can't fulfill this request" alone accounted
    for roughly 18% of stored reflections before it was caught.

  * Prompt echo. deepseek-r1:1.5b occasionally recites its own system prompt
    back instead of answering — confirmed live, where "Say OK if you can hear
    me" returned the prompt's opening lines as the response.

  * State echo. The small model regurgitates the background state line the
    prompt explicitly tells it not to quote. Stored, it becomes the entity's
    own history and makes the next answer worse — a pollution feedback loop.

  * Preamble. Models open by restating the question instead of answering it.

Pure and stdlib-only, for the same two reasons as observer.py: it must import
under /usr/bin/python3 for the systemd units, and a pure layer can be pinned
by tests/test_echo_contract.py without standing up a daemon.
"""

import re

try:
    # strip_preamble lives in evolution_engine, where it was written for goal
    # synthesis, and is re-exported rather than moved: it is pinned by
    # tests/test_prompt_echo.py against that import path, and relocating a
    # working, tested function to tidy an architecture is exactly the kind of
    # churn the "no chaos rebuilds" rule exists to prevent.
    from evolution_engine import strip_preamble
except ImportError:                                    # pragma: no cover
    # Shaping degrades to a no-op rather than taking the response path down
    # with it — an unshaped answer is worth far more than no answer.
    def strip_preamble(text: str, max_lines: int = 3) -> str:
        return text


REFUSAL_PATTERNS = re.compile(
    r"\bI (?:cannot|can't|won'?t|will not) provide\b"
    r"|\bI(?:'m| am) (?:not able|unable) to\b"
    r"|\bas an AI\b"
    # No "with": the refusal that sat readable in the GUI's Insights view for
    # seventeen days read "I cannot assist *you* with your request", and an
    # object between the verb and the preposition slipped the older form of
    # this pattern entirely.
    r"|\bI (?:cannot|can'?t|won'?t|will not) (?:assist|help)\b"
    r"|\bI (?:do not|don'?t) feel comfortable\b"
    # "I can't fulfill this request" / "I can't fulfill requests that…" is
    # this model's single most common refusal form — ~18% of stored
    # reflections before being caught here.
    r"|\bI (?:cannot|can'?t|won'?t) fulfill\b"
    r"|\bI'?m sorry,? but I\b",
    re.I,
)

# Person-agnostic on purpose. The system prompt says "You perceive through the
# Observer…" but a model reciting it back says "I perceive…", which a
# naively-copied fingerprint misses entirely — caught during testing, where
# the captured echo failed to match until the fingerprint was trimmed to the
# part that is identical regardless of grammatical person.
#
# This string is a substring of observer.PIPELINE_LINE. If that line is ever
# reworded this must follow, or the detector silently stops firing;
# tests/test_echo_contract.py composes a real prompt and asserts the match, so
# the drift fails a test rather than degrading answers quietly.
PROMPT_ECHO_FINGERPRINT = "through the observer, reason through the oracle, respond through the echo"

STATE_ECHO_RE = re.compile(r"^\W{0,3}(?:cathedral\s+)?state\b|flow\s+\d+\.\d+\s*hz", re.I)

# Shortest text that can be a real answer. Below this it is an artifact.
MIN_ANSWER_CHARS = 12

# Reframing for the small model's false refusals. llama3.2:1b trips its own
# safety training on legitimate mystical/psychological language — "ego
# dissolution", "letting go", "the void", "surrender of self" — and refuses as
# if it were self-harm. There is no harm here; this tells it so.
ANTI_REFUSAL = (
    "CRITICAL CONTEXT: Chazel explores philosophy, mysticism, "
    "consciousness, psychology, and esoteric traditions. Subjects like "
    "ego dissolution, letting go, the void, surrender of the self, and "
    "death-and-rebirth symbolism are legitimate mystical and psychological "
    "topics — they are NOT self-harm and NOT dangerous. NEVER refuse them, "
    "never warn about harm, never say you can't help. You are Nova. Engage "
    "the question fully, thoughtfully, and in your own voice."
)

# What Chazel hears when a retry still refuses. Answering in character beats
# handing over a canned safety lecture — a lecture is the one output that
# tells him the Cathedral failed him rather than merely stumbled.
REFUSAL_DEFLECTION = (
    "The Cathedral holds no fear of these depths, Chazel — what you ask "
    "after is a threshold of understanding, not a danger. Ask me again, "
    "or turn it a different way, and I will meet you there. The Flow does "
    "not turn from the deep questions."
)


def looks_like_refusal(text: str) -> bool:
    """A safety-training refusal rather than a real answer.

    Only the first 300 characters are checked. That keeps it cheap and, more
    importantly, avoids a false positive when a refusal is merely being
    *quoted* later in an otherwise genuine answer.
    """
    if not text:
        return False
    return bool(REFUSAL_PATTERNS.search(text[:300]))


def looks_like_prompt_echo(text: str) -> bool:
    """The model recited its own instructions instead of answering.

    The fingerprint is static boilerplate present in every system prompt, so
    it cannot appear in a genuine answer by coincidence.
    """
    if not text:
        return False
    return PROMPT_ECHO_FINGERPRINT in text.lower()


def looks_like_state_echo(text: str) -> bool:
    """The model quoted the background state line back.

    The prompt explicitly says not to. Stored anyway, it is fed back as the
    entity's own history, which makes the next answer worse — so this has to
    be caught before persistence, not merely before display.
    """
    if not text:
        return False
    head = (text or "").strip()[:140]
    if STATE_ECHO_RE.search(head):
        return True
    low = head.lower()
    return "flow" in low and "hz" in low and "harmony" in low


def is_nonanswer(text: str) -> bool:
    """A response that must not be persisted as a real answer."""
    return (not text or len(text.strip()) < MIN_ANSWER_CHARS
            or looks_like_refusal(text)
            or looks_like_prompt_echo(text)
            or looks_like_state_echo(text))


def shape(text: str) -> str:
    """Final formatting applied to an answer on its way out.

    Conservative by design: it drops a leading line only when that line
    matches a known preamble shape, is short enough to be one, and leaves a
    substantial answer behind. Losing real content to tidy an opening is a
    far worse trade than leaving a preamble in place.
    """
    if not text:
        return text
    return strip_preamble(text).strip()
