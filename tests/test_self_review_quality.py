"""
Nova's self-review must look at code, not filenames.

The live evidence: 179 proposals since April, 71 of them against
plugins/oracle_module.py — 40% of everything she ever suggested — and every
one phrased as "a more efficient data structure to reduce memory usage".

Three causes, all pinned here. read_nova_source already captures each file's
content and the prompt threw it away, so she was asked to improve code she
could not see. The prompt ended with "Consider: memory efficiency, reasoning
quality, ..." and got those exact words back — the menu was the answer. And
nothing showed her the previous seventy proposals, the same livelock the
Dream loop and the Eyemoeba motif ranking each had.
"""
import evolution_engine as evo


FILES = {
    "a.py": {"lines": 10, "content": "def alpha():\n    return 1\n"},
    "b.py": {"lines": 20, "content": "def beta():\n    return 2\n"},
    "c.py": {"lines": 30, "content": "def gamma():\n    return 3\n"},
    "d.py": {"lines": 40, "content": "def delta():\n    return 4\n"},
}


# ── the prompt shows real code ───────────────────────────────────────────

def test_prompt_contains_actual_source_not_just_names():
    p = evo.build_self_improvement_prompt(list(FILES.items())[:2], [])
    assert "def alpha():" in p, "she must see code, not only filenames"
    assert "def beta():" in p


def test_prompt_no_longer_hands_over_the_answer():
    """Every historical proposal echoed this menu back verbatim."""
    p = evo.build_self_improvement_prompt(list(FILES.items())[:1], [])
    assert "memory efficiency, reasoning quality" not in p


def test_prior_proposals_are_never_quoted_into_the_prompt():
    """Measured, not assumed: listing them under "do not repeat these" made
    llama3.2:1b propose oracle_module.py again — a file it had not been shown
    — quoting the old wording back. A small model treats anything in the
    prompt as material, whatever the surrounding sentence says. Repetition is
    prevented structurally, by not showing those files at all."""
    prior = [{"file": "a.py", "improvement": "use a more efficient structure"}]
    p = evo.build_self_improvement_prompt(list(FILES.items())[:1], [], prior)
    assert "use a more efficient structure" not in p
    assert "oracle" not in p.lower()


def test_prompt_offers_a_way_to_decline():
    """Producing nothing beats producing noise — a vague suggestion gets
    attempted, and this loop has broken oracle_module twice."""
    p = evo.build_self_improvement_prompt(list(FILES.items())[:1], [])
    assert "NOTHING" in p


def test_real_errors_reach_the_prompt():
    p = evo.build_self_improvement_prompt(
        list(FILES.items())[:1], ["evolution loop: TimeoutError: ollama"])
    assert "TimeoutError: ollama" in p


def test_excerpts_are_truncated():
    big = {"big.py": {"lines": 9999, "content": "x" * 50_000}}
    p = evo.build_self_improvement_prompt(list(big.items()), [], excerpt_chars=100)
    assert len(p) < 3000


# ── the review window rotates and skips ──────────────────────────────────

def test_window_rotates_so_the_same_files_are_not_always_shown():
    first  = [n for n, _ in evo.files_for_review(FILES, count=2, offset=0)]
    second = [n for n, _ in evo.files_for_review(FILES, count=2, offset=2)]
    assert first != second, "a fixed window is why one file got 71 proposals"


def test_overproposed_files_are_skipped():
    shown = [n for n, _ in evo.files_for_review(FILES, skip=["a.py"], count=4)]
    assert "a.py" not in shown


def test_skipping_everything_does_not_produce_an_empty_review():
    """If every file is over-proposed, review something rather than nothing."""
    shown = evo.files_for_review(FILES, skip=list(FILES), count=2)
    assert len(shown) == 2


def test_empty_source_is_handled():
    assert evo.files_for_review({}, count=3) == []
    assert evo.build_self_improvement_prompt([], []) == ""


# ── the database side ────────────────────────────────────────────────────

def test_overproposed_files_counts_only_unapplied(tmp_path):
    import sqlite3
    db = tmp_path / "c.db"
    with sqlite3.connect(db) as con:
        con.execute("""CREATE TABLE self_improvements (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT NOT NULL,
            improvement TEXT NOT NULL, file TEXT, type TEXT, priority TEXT,
            rationale TEXT, applied INTEGER DEFAULT 0)""")
        for _ in range(4):
            con.execute("INSERT INTO self_improvements (created, improvement, file) "
                        "VALUES ('t','i','oracle.py')")
        for _ in range(4):
            con.execute("INSERT INTO self_improvements (created, improvement, file, applied) "
                        "VALUES ('t','i','good.py',1)")

    over = evo.overproposed_files(db, threshold=3)
    assert "oracle.py" in over
    assert "good.py" not in over, "applied proposals are not a backlog"
    assert evo.proposal_count(db) == 8


# ── evidence must be real, not merely present ────────────────────────────

REVIEWED = [("evolution_engine.py", {"lines": 5, "content":
    "GOAL_SEEDS = [\n    'understand the flow',\n]\n\n"
    "def build_prompt(files, issues):\n    return f'review {files}'\n"})]


def test_a_real_quote_is_accepted():
    assert evo.evidence_is_real("def build_prompt(files, issues):", REVIEWED)


def test_a_reformatted_quote_is_still_accepted():
    """Models re-indent and re-space what they quote; honest citations must
    survive that or the check rejects everything and nothing is ever proposed."""
    assert evo.evidence_is_real("def   build_prompt( files , issues ):", REVIEWED)


def test_invented_code_around_a_real_symbol_is_rejected():
    """The measured failure. GOAL_SEEDS is real and on line 1; the line the
    model built around it exists nowhere. That shape reads as checkable, which
    is what makes it dangerous — this loop has broken oracle_module twice."""
    assert not evo.evidence_is_real(
        "goal = json.loads(json.dumps(GOAL_SEEDS[0]))", REVIEWED)


def test_empty_or_trivial_evidence_is_rejected():
    for junk in ("", "   ", "code", "the file"):
        assert not evo.evidence_is_real(junk, REVIEWED)


def test_evidence_from_a_file_not_reviewed_is_rejected():
    assert not evo.evidence_is_real("class OracleModule:", REVIEWED)


def test_no_reviewable_file_contains_a_fabricated_example():
    """Prose is part of a file's content, so a documented fake line becomes
    quotable evidence. The first version of evidence_is_real's docstring
    pasted the model's invented line verbatim — and the checker then verified
    that line successfully against the very file explaining it was fake."""
    from pathlib import Path
    src = Path(evo.__file__).read_text()
    assert "json.loads(json.dumps" not in src
