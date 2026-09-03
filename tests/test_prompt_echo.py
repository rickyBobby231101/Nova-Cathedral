"""
A result must answer the goal, not restate it.

Measured on the live table 2026-09-02: 139 of 417 completed goals opened by
restating the prompt — a third of everything Nova has ever produced. The
prompt began "You are Nova synthesizing research for autonomous
self-improvement" and the answers began "I'm Nova, synthesizing research for
autonomous self-improvement."

Same shape as the self-review's "Consider: memory efficiency, reasoning
quality..." menu, which came back as the text of a hundred proposals. What is
in the prompt is available to be repeated, whatever the surrounding sentence
asks for — so the prompt no longer describes her, and what slips through
anyway is trimmed.
"""
import evolution_engine as evo


REAL_OPENINGS = [
    "I'm Nova, synthesizing research for autonomous self-improvement.\n\n**Key Insights:**\n* Entanglement is a resource for quantum technologies and real limits apply.",
    "I'd be delighted to synthesize the research for you.\n\n**Key Insights:**\n* Asynchronous patterns shape the emergence of novel syntax in generation.",
    "I'm so excited to dive into these fascinating motif results! Here's a synthesis:\n\n**Key Insights:**\n* Entangled particles can carry information under strict limits.",
    "I'm synthesizing this research into three key insights:\n\n* Star formation rates correlate with the Hubble constant across sampled galaxies.",
]


def test_the_prompt_no_longer_describes_her():
    p = evo.build_research_prompt("study stoicism", "material")
    assert "You are Nova synthesizing" not in p
    assert "Do not introduce yourself" in p


def test_real_observed_openings_are_stripped():
    for raw in REAL_OPENINGS:
        out = evo.strip_preamble(raw)
        first = out.splitlines()[0].lower()
        assert not first.startswith(("i'm nova", "i'd be", "i'm so excited",
                                     "i'm synthesizing")), out[:60]
        assert len(out) > 40, "the answer itself must survive"


def test_the_substance_is_kept():
    out = evo.strip_preamble(REAL_OPENINGS[0])
    assert "Entanglement is a resource" in out


def test_a_direct_answer_is_untouched():
    good = "**Key Insights:**\n* Stoicism holds that virtue is the only good.\n* Zeno founded the school."
    assert evo.strip_preamble(good) == good


def test_a_short_answer_is_never_stripped_to_nothing():
    """Losing real content to tidy an opening is the worse trade, so anything
    that would leave less than a paragraph behind is left alone."""
    short = "I'm Nova. Yes."
    assert evo.strip_preamble(short) == short
    barely = "I'm Nova, synthesizing research.\n\nYes, briefly."
    assert evo.strip_preamble(barely) == barely


def test_a_long_first_line_is_prose_not_preamble():
    long_line = "Let me " + "x" * 400 + "\n\nrest of the answer here, substantial enough to keep around."
    assert evo.strip_preamble(long_line) == long_line


def test_stacked_preambles_are_removed():
    stacked = ("Sure, here you go.\nI'm Nova, synthesizing research.\n\n"
               "**Key Insights:**\n* The actual content of the answer lives here, "
               "and it is long enough to sit above the floor that protects short "
               "answers from being stripped away entirely.")
    out = evo.strip_preamble(stacked)
    assert out.startswith("**Key Insights:**")


def test_empty_input_is_safe():
    assert evo.strip_preamble("") == ""
    assert evo.strip_preamble(None) == ""
