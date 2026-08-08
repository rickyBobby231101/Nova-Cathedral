"""
Regression tests for the daemon's pure text-pattern detectors.

These exist because both bugs were caught live, by hand, mid-session:
prompt-echo (small model reciting its own system prompt instead of
answering) and the refusal detector storing an LLM's "I can't help with
that" as if it were real knowledge. Neither had a test before this.
"""


def test_prompt_echo_detects_first_person_recitation(nova):
    # The actual failure text, first-person, is what the model produces —
    # the initial (buggy) version of this check used a second-person
    # "you perceive" fingerprint and missed this exact case.
    text = (
        "I perceive through the observer, reason through the oracle, "
        "respond through the echo, always guided by the flow."
    )
    assert nova._looks_like_prompt_echo(text) is True


def test_prompt_echo_ignores_normal_reply(nova):
    assert nova._looks_like_prompt_echo("The answer is 42.") is False


def test_prompt_echo_is_case_insensitive(nova):
    text = "THROUGH THE OBSERVER, REASON THROUGH THE ORACLE, RESPOND THROUGH THE ECHO"
    assert nova._looks_like_prompt_echo(text) is True


def test_refusal_detector_catches_common_refusal(nova):
    assert nova._looks_like_refusal("I'm sorry, but I can't help with that request.") is True


def test_refusal_detector_ignores_normal_reply(nova):
    assert nova._looks_like_refusal("Sure — here's how tide pools form.") is False


def test_refusal_detector_only_checks_leading_text(nova):
    # A refusal phrase deep inside an otherwise normal, long answer
    # shouldn't trip the detector — it only looks at the first ~300 chars,
    # matching how a genuine refusal actually opens a reply.
    padding = "This is a long, substantive answer about geology. " * 20
    text = padding + " I'm sorry, but I can't help with that."
    assert nova._looks_like_refusal(text) is False


def test_tillagon_detects_the_fold(nova):
    # Complex question, very short answer — a real "collapse" pattern.
    q = "What is the meaning of the deep flow of the cathedral and its many layered structures within Nova's consciousness?"
    r = "Yes."
    detections = nova._tillagon_watch(q, r)
    names = [d["construct"] for d in detections]
    assert "The Fold" in names


def test_tillagon_clean_exchange_detects_nothing(nova):
    q = "What's 2 + 2?"
    r = "4."
    assert nova._tillagon_watch(q, r) == []


def test_tillagon_detects_false_light(nova):
    q = "Are you sure about that?"
    r = "Obviously, this is undeniably correct without a doubt."
    detections = nova._tillagon_watch(q, r)
    names = [d["construct"] for d in detections]
    assert "False Light" in names
