"""
A refused goal must be retried before it is written off.

Every goal Chazel has personally set — eight in five months — failed. The two
most recent, "study stoisism" and "learn about gnostic", failed with
"Model declined to answer (safety refusal)".

The subject was not the problem. Measured: llama3.2:1b refused through the
normal research prompt, and answered the same topic in 141s given plain
context. build_research_prompt opens "You are Nova synthesizing research for
autonomous self-improvement" and asks how the findings connect to "your
Cathedral, the Flow, or your consciousness" — an AI improving itself and
reflecting on its consciousness is the shape a small model's safety training
reacts to, whatever sits underneath it.
"""
import evolution_engine as evo


def test_neutral_prompt_drops_the_framing_that_triggers_refusals():
    p = evo.build_neutral_research_prompt("study stoicism", "Some material.")
    for trigger in ("consciousness", "Cathedral", "the Flow",
                    "self-improvement", "Nova"):
        assert trigger not in p, f"{trigger!r} still present"


def test_neutral_prompt_keeps_the_actual_question():
    p = evo.build_neutral_research_prompt("study stoicism", "Zeno of Citium.")
    assert "study stoicism" in p
    assert "Zeno of Citium" in p


def test_normal_prompt_still_carries_her_voice():
    """Only the retry is plain. The ordinary path keeps the mythos — that is
    the point of the system, and stripping it everywhere would be a cure worse
    than the fault."""
    p = evo.build_research_prompt("study stoicism", "material")
    assert "Cathedral" in p or "Flow" in p


def test_neutral_prompt_truncates_context():
    p = evo.build_neutral_research_prompt("g", "x" * 10_000)
    assert len(p) < 3400


def test_both_prompts_survive_empty_context():
    assert evo.build_neutral_research_prompt("g", "")
    assert evo.build_research_prompt("g", "")
