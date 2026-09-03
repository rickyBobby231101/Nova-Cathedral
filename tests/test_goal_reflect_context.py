"""
A `reflect` goal must recall memories about its SUBJECT, not its label.

`domain` means different things depending on who set the goal: for Nova's own
it is a category ("Quantum Mechanics"), for Chazel's it is a source ("user").
Searching it fetched every conversation containing the word "user" — an SSH
question and "Testing testing" — and handed those to the model as the research
context for "study stoisism". Irrelevant context plus the self-improvement
framing is the likeliest reason that goal came back a refusal.
"""
import pytest


@pytest.fixture
def seeded(nova):
    nova.save_conversation("tell me about stoicism", "Zeno founded the Stoa.")
    nova.save_conversation("how do i make an ssh file?", "Use ~/.ssh/config.")
    return nova


def _queries_seen(nova, monkeypatch):
    seen = []
    real = nova.recall_memories

    def spy(query="", n=10):
        seen.append(query)
        return real(query=query, n=n)

    monkeypatch.setattr(nova, "recall_memories", spy)
    return seen


@pytest.mark.asyncio
async def test_reflect_recalls_by_the_goal_text(seeded, monkeypatch):
    """The goal has to be one that genuinely stays on reflect: a "study X"
    goal now routes to web_search, because recalling conversations cannot
    answer a question about something never discussed."""
    seen = _queries_seen(seeded, monkeypatch)
    captured = {}
    goal = "reflect on what we discussed about ssh"

    async def fake_chat(messages, model=None, timeout=180):
        captured["prompt"] = messages[0]["content"]
        return {"response": "A synthesis."}

    monkeypatch.setattr(seeded, "_ollama_chat", fake_chat)

    await seeded._process_goal({"id": 1, "method": "reflect",
                                "goal": goal, "domain": "user"})

    assert seen and seen[0] == goal, \
        f"first recall must use the subject, not the label; got {seen!r}"
    assert goal in captured.get("prompt", "")


@pytest.mark.asyncio
async def test_user_label_is_never_used_as_a_search_term(seeded, monkeypatch):
    """'user' is a source, not a subject — searching it returns noise."""
    seen = _queries_seen(seeded, monkeypatch)

    async def fake_chat(messages, model=None, timeout=180):
        return {"response": "ok"}

    monkeypatch.setattr(seeded, "_ollama_chat", fake_chat)
    await seeded._process_goal({"id": 1, "method": "reflect",
                                "goal": "zzz nothing matches zzz",
                                "domain": "user"})
    assert "user" not in seen, f"searched for the label: {seen}"


@pytest.mark.asyncio
async def test_a_goal_that_matches_nothing_still_gets_context(seeded, monkeypatch):
    """Empty context fails a goal outright — that is how five of Chazel's died
    with 'No context gathered'. Whatever the recall finds, something must reach
    the model rather than the goal being abandoned.

    Note the remaining limitation, deliberately not papered over here:
    recall_memories substring-matches the WHOLE query, so "study stoicism"
    does not match a memory reading "tell me about stoicism". Keyword recall
    would fix that and is not what this change does."""
    captured = {}

    async def fake_chat(messages, model=None, timeout=180):
        captured["prompt"] = messages[0]["content"]
        return {"response": "ok"}

    monkeypatch.setattr(seeded, "_ollama_chat", fake_chat)
    await seeded._process_goal({"id": 1, "method": "reflect",
                                "goal": "qqqq no match qqqq", "domain": "user"})
    assert captured.get("prompt"), "the goal must not die for lack of context"
