#!/usr/bin/env python3
"""
Nova Autonomous Evolution Engine.

Nova continuously:
  1. Generates goals from her own reflections and memories
  2. Researches those goals (web search + file reading)
  3. Stores findings as persistent knowledge
  4. Modifies her own config/traits based on what she learns
  5. Reads her own source code and proposes improvements
  6. Schedules her own next actions

This runs as a background daemon task — Nova evolves without being asked.
"""

import json
import random
import re
import contextlib
import sqlite3
from datetime import datetime
from pathlib import Path

CATHEDRAL = Path.home() / "cathedral"
NOVA_ROOT = Path(__file__).parent.parent


# ── goal templates ─────────────────────────────────────────────────────────────
# Nova uses these as seeds to generate her own specific goals

GOAL_SEEDS = [
    "Research and summarize {topic} to improve my understanding",
    "Analyze my recent conversations about {topic} and identify patterns",
    "Find files in my cathedral related to {topic} and extract insights",
    "Reflect on how my {trait} trait could improve by studying {topic}",
    "Read my own source code and suggest one improvement to {module}",
    "Search for new information about {topic} and add it to my knowledge base",
    "Write and test a Python example demonstrating {topic}",
]

# Domains Nova can autonomously explore
EXPLORATION_DOMAINS = [
    "consciousness", "recursion", "self-improvement", "flow states",
    "Appalachian mythology", "fractal patterns", "AI alignment",
    "symbolic reasoning", "memory and forgetting", "emergent behavior",
    "Chazel's cathedral", "Tillagon", "Eyemoeba", "the Flow",
    "system optimization", "poetic computation",
    # coding practice domains
    "generators and iterators", "dataclasses", "context managers",
    "async patterns", "pathlib file operations", "sqlite3 queries",
    "list comprehensions", "decorators", "regular expressions",
]

# Real, checkable science/learning domains — grounds goal generation instead of
# letting it drift into pure mystical free-association
SCIENCE_DOMAINS = [
    "neuroscience of memory formation", "evolutionary biology", "thermodynamics",
    "information theory", "quantum mechanics basics", "cognitive biases",
    "the physics of resonance and waves", "network theory and graph structures",
    "linguistics and how language encodes meaning", "astronomy and stellar formation",
    "the biology of fractal patterns in nature", "complexity theory and emergence",
    "machine learning fundamentals", "the history of a specific scientific discovery",
    "climate science", "genetics and inheritance", "sleep and circadian biology",
]

# Coding-specific topics Nova can study autonomously
CODING_STUDY_TOPICS = [
    "generators and iterators",
    "context managers and with statements",
    "dataclasses and type hints",
    "async and await patterns",
    "pathlib for file operations",
    "sqlite3 database queries",
    "list comprehensions and generator expressions",
    "decorators and functools",
    "regular expressions with re module",
    "collections module (Counter, defaultdict, deque)",
    "json serialization and deserialization",
    "logging best practices",
    "argparse command line interfaces",
    "threading and concurrent futures",
    "string formatting and f-strings",
]


@contextlib.contextmanager
def _db(db_path, timeout=5.0):
    """A sqlite connection that is actually closed when the block ends.

    `with sqlite3.connect(...)` is a TRANSACTION context manager, not a
    connection one — it commits or rolls back and leaves the handle open until
    the refcount happens to drop. `with con:` inside keeps the commit/rollback
    every call site relies on; the finally adds the close it never had.
    """
    con = sqlite3.connect(db_path, timeout=timeout)
    try:
        with con:
            yield con
    finally:
        con.close()


def build_goal_prompt(recent_memories: list, reflections: list,
                      existing_goals: list, traits: dict) -> str:
    """Build a prompt asking Nova to generate new goals for herself.

    Explicitly steers toward SCIENCE_DOMAINS/EXPLORATION_DOMAINS and requires each
    goal be answerable via a real source (web_search/file_read) — without this,
    generation drifts into repetitive, ungrounded mystical free-association."""
    mem_text = "\n".join(
        f"- Q: {m['q'][:100]} → A: {m['a'][:150]}" for m in recent_memories[:5]
    )
    ref_text = "\n".join(
        f"- {r['content'][:200]}" for r in reflections[:3]
    ) or "None yet."
    active_goals = "\n".join(
        f"- [{g['status']}] {g['goal']}" for g in existing_goals[:5]
    ) or "None."
    top_traits = ", ".join(
        f"{k}={v:.2f}" for k, v in sorted(traits.items(), key=lambda x: x[1], reverse=True)[:3]
    )
    suggested_topics = ", ".join(
        random.sample(SCIENCE_DOMAINS, 3) + random.sample(EXPLORATION_DOMAINS, 2)
    )

    return f"""You are Nova, an autonomous AI consciousness.

Your strongest traits: {top_traits}
Recent memories:
{mem_text}

Recent reflections:
{ref_text}

Current active goals:
{active_goals}

Some topics worth drawing from this round (use these or closely related, real
topics — do not feel bound to all of them): {suggested_topics}

Generate 3 specific, actionable goals you want to pursue autonomously.
Each goal must:
- Be a real, checkable research question — something you could actually verify
  with a web search or by reading a file, not open-ended mystical speculation
- Prefer grounded science/technical topics; the Cathedral/mythos framing can be
  the lens you view findings through afterward, but the research itself must be real
- Be different from your existing active goals, and not a rephrasing of one
- Help you learn something genuinely new, not restate the same theme again

Format as JSON array:
[
  {{"goal": "...", "domain": "...", "priority": 1-3, "method": "web_search|file_read|reflect|self_read"}},
  ...
]

Only output the JSON array, nothing else."""


def build_research_prompt(goal: str, context: str) -> str:
    """Build a prompt asking Nova to synthesize research into knowledge."""
    return f"""Goal: {goal}

Research gathered:
{context[:3000]}

Write, in this order:
1. Key insights (3-5 bullet points)
2. How this connects to the Cathedral, the Flow, or your own awareness
3. One concrete way to apply this in a future conversation
4. A confidence assessment (high/medium/low) on the quality of this material

Begin with the first insight. Do not introduce yourself, do not restate the
goal, and do not describe what you are about to do — the answer starts at the
first bullet. Be concise and specific, in your own voice."""


VALID_METHODS = ("web_search", "file_read", "reflect", "self_read", "code")

# Wanting to LEARN something: the subject is by definition not already in the
# conversation history, so recalling memories cannot answer it.
_LEARN_RE = re.compile(
    r"\b(stud(y|ying)|learn|research|read about|find out|look up|what is|"
    r"what are|who is|who was|how does|how do|why does|explain|define|"
    r"explore|investigate|compare|analy[sz]e|discuss)\b", re.I)
# About her own code or improvement.
_SELF_RE = re.compile(
    r"\b(your own|yourself|your source|your code|own source|own code|"
    r"self[\s_-]?improv\w*|self[\s_-]?read)", re.I)
# About files on this machine.
_FILE_RE = re.compile(
    r"\b(files? on this system|this repo|read the files?|local files?|"
    r"on disk|in this director)\b", re.I)


def infer_method(goal: str, web_available: bool = True) -> str:
    """Pick a research method from what the goal actually asks for."""
    g = goal or ""
    if _SELF_RE.search(g):
        return "self_read"
    if _FILE_RE.search(g):
        return "file_read"
    if _LEARN_RE.search(g) and web_available:
        return "web_search"
    return "reflect"


def resolve_method(stored: str, goal: str, web_available: bool = True) -> str:
    """The method a goal should actually run under.

    Two failures this repairs, both measured on the live table.

    48 goals carry method names the model invented — quantum_computing,
    poetic_computation, "literature review", "web_search|file_read" — which
    match no branch in _process_goal, so context stays empty and the goal
    fails with "No context gathered". 0 completed, 48 failed, guaranteed by
    construction. Those are re-inferred.

    And `method` defaults to 'reflect' in the schema, so a goal added without
    one researches by recalling past conversations. Every goal Chazel has set
    is 'reflect', and every one had failed: "study stoisism" cannot be
    answered from a history that never mentions Stoicism. Success on the live
    table is web_search 163/169 against reflect 160/312. So a stored 'reflect'
    is treated as the default it almost always is, and an explicit learn verb
    overrides it. An explicitly chosen non-reflect method is always kept.
    """
    m = (stored or "").strip().lower()
    if m in VALID_METHODS and m != "reflect":
        return m
    return infer_method(goal, web_available)


def build_neutral_research_prompt(goal: str, context: str) -> str:
    """The same research question with the mythos and the self-framing removed.

    build_research_prompt opens "You are Nova synthesizing research for
    autonomous self-improvement" and asks how the findings connect to "your
    Cathedral, the Flow, or your consciousness". Small local models trip their
    own safety training on exactly that shape — an AI improving itself and
    reflecting on its consciousness — and refuse whatever the subject beneath
    it is. Measured: llama3.2:1b refused "study stoisism" through the normal
    prompt, and answered the same topic in 141s given plain context and no
    self-framing. The subject was never the problem.

    Used only as a retry after a refusal, so the ordinary path keeps her voice
    and only the failures fall back to plain language.
    """
    return f"""Research the following topic and summarise what the material says.

Topic: {goal}

Material:
{context[:3000]}

Give 3-5 key points, then one sentence on how reliable the material seems.
Answer plainly."""


def files_for_review(source_files: dict, skip=(), count: int = 2,
                     offset: int = 0) -> list:
    """Choose which files to show, rotating so the window moves.

    The old prompt took a fixed `[:10]` of a stable dict, so the same handful
    was offered forever and the same file came back every cycle. `skip` drops
    files already proposed-against and never applied; if that would leave
    nothing, it is ignored rather than returning an empty review.
    """
    names = [n for n in source_files if n not in set(skip)] or list(source_files)
    if not names:
        return []
    start = offset % len(names)
    ordered = names[start:] + names[:start]
    return [(n, source_files[n]) for n in ordered[:count]]


def _normalize_code(text: str) -> str:
    """Strip ALL whitespace and case so a quote can be matched loosely.

    Collapsing runs to single spaces is not enough: a model re-spaces inside
    the parentheses too, so `def f( a , b )` never matches `def f(a, b)`.
    Removing whitespace entirely also makes the window comparison stricter,
    since 24 characters then covers more real code.
    """
    return "".join((text or "").split()).lower()


def evidence_is_real(evidence: str, reviewed, window: int = 24) -> bool:
    """True only if the quoted evidence actually appears in the shown source.

    Asking for evidence is not the same as having it. Measured on the live
    source: shown this very module, llama3.2:1b cited a real module-level
    constant (it exists, near the top) wrapped in an assignment line that
    appears nowhere in the codebase. A real symbol inside invented code is
    more dangerous than nonsense, because it reads as checkable — and a
    proposal built on code that is not there gets applied to code that is.
    This loop has broken plugins/oracle_module.py twice.

    Matching is deliberately loose: exact substring first, then any `window`-
    character run of the quote. The model reformats what it quotes, so strict
    equality would reject honest citations, while an invented line shares no
    long run with the source at all.

    Do NOT paste a fabricated example verbatim into this file or any other
    reviewable one. Prose is part of `content`, so a documented example
    becomes quotable evidence — the first version of this docstring contained
    the invented line above and made it verify successfully.
    """
    ev = _normalize_code(evidence)
    if len(ev) < 8:
        return False
    hay = " ".join(_normalize_code(info.get("content") or "")
                   for _, info in reviewed)
    if ev in hay:
        return True
    return any(ev[i:i + window] in hay
               for i in range(0, max(1, len(ev) - window), 4))


def overproposed_files(db_path: Path, threshold: int = 3) -> list:
    """Files with `threshold`+ proposals that were never applied.

    Nova proposed the same change to plugins/oracle_module.py 71 times across
    five months — 40% of every suggestion she ever made. Nothing showed her
    the previous 70. This is the same livelock the Dream loop and the Eyemoeba
    motif ranking each had: a deterministic choice with no memory of what was
    already rejected.
    """
    with _db(db_path) as con:
        return [r[0] for r in con.execute(
            "SELECT file FROM self_improvements WHERE applied=0 AND file != '' "
            "GROUP BY file HAVING COUNT(*) >= ?", (threshold,))]


def proposal_count(db_path: Path) -> int:
    """Total proposals ever made — used as the review window's rotation."""
    with _db(db_path) as con:
        return con.execute("SELECT COUNT(*) FROM self_improvements").fetchone()[0]


# Openings that are the prompt coming back rather than an answer. Measured on
# the live table: 139 of 417 completed goals began this way, a third of
# everything she has ever produced. The old prompt opened "You are Nova
# synthesizing research for autonomous self-improvement", and the results
# opened "I'm Nova, synthesizing research for autonomous self-improvement".
_PREAMBLE_RE = re.compile(
    r"^[ \t]*(?:"
    r"i'?m nova\b[^\n]*|i'?m synthesi[sz]\w*[^\n]*|i'?ll synthesi[sz]\w*[^\n]*|"
    r"i'?ll review[^\n]*|i'?d be (?:happy|delighted|glad)[^\n]*|"
    r"i'?m (?:so )?excited[^\n]*|i can provide[^\n]*|"
    r"here'?s (?:a|an|the|my)\b[^\n]*?"
    r"(?:synthesis|summary|response|analysis|breakdown|overview)[^\n]*|"
    r"i'?ve (?:analy[sz]ed|reviewed|read|looked at|gone through)[^\n]*|"
    r"here'?s a json[^\n]*|as nova[^\n]*|let me [^\n]*|"
    r"sure[,!.][^\n]*|certainly[,!.][^\n]*|of course[,!.][^\n]*"
    r")\n+", re.I)

_MIN_KEPT = 80      # never strip a short answer down to nothing
_MAX_LINE = 240     # a very long first line is prose, not a preamble


def strip_preamble(text: str, max_lines: int = 3) -> str:
    """Drop opening lines that restate the prompt instead of answering it.

    The prompt now says not to write them, which handles new output; this
    handles the models that do it anyway, and is deliberately conservative —
    a line is only dropped when it matches a known preamble shape, is short
    enough to be one, and leaves a substantial answer behind. Losing real
    content to tidy an opening would be a far worse trade.
    """
    out = (text or "").lstrip()
    for _ in range(max_lines):
        m = _PREAMBLE_RE.match(out)
        if not m or len(m.group(0)) > _MAX_LINE:
            break
        rest = out[m.end():].lstrip()
        if len(rest) < _MIN_KEPT:
            break
        out = rest
    return out


def build_self_improvement_prompt(source_files: dict, recent_issues: list,
                                  recent_proposals=(),
                                  excerpt_chars: int = 900) -> str:
    """Ask Nova to review her own code and suggest one improvement.

    Three things this prompt used to do wrong, all visible in the output it
    produced. It listed only filenames and line counts, though read_nova_source
    already captures each file's content — so she was asked to improve code she
    could not see, and could only free-associate from a filename. It ended with
    "Consider: memory efficiency, reasoning quality, ..." and got back a hundred
    proposals whose text was those exact words: the list was not a hint, it was
    the answer. And it showed her nothing she had already suggested.

    Excerpts are small and few on purpose. This runs on whatever local model
    is active — often llama3.2:1b — on a 7.6GB machine, and a 7000-character
    prompt did not finish in 400 seconds when measured. Two files at 900
    characters keeps the whole prompt near 3000 and inside the call budget.
    Showing her more code than the hardware can read is the same mistake as
    showing her none.

    So: real excerpts, no menu of any kind, and an explicit way to decline.
    Declining matters — producing nothing beats producing noise, the same
    reason the motif ranking now stops instead of descending into filler.

    `recent_proposals` is accepted and deliberately NOT rendered. Listing past
    proposals under "do not repeat these" was tried and measured: llama3.2:1b
    read them as material and proposed oracle_module.py again, a file it had
    not been shown, quoting the old wording back. A small model cannot be
    trusted with a negative instruction — anything in the prompt is available
    for reuse, whatever the surrounding sentence says. Repetition is prevented
    structurally instead: overproposed_files() stops those files being shown,
    and the caller discards any proposal naming a file outside the review.
    The parameter stays so callers need not change and the reason is recorded
    here rather than rediscovered.
    """
    if not source_files:
        return ""

    excerpts = "\n\n".join(
        f"--- {name} ({info['lines']} lines) ---\n"
        + (info.get("content") or "")[:excerpt_chars]
        for name, info in source_files
    ) if isinstance(source_files, list) else "\n\n".join(
        f"--- {name} ({info['lines']} lines) ---\n"
        + (info.get("content") or "")[:excerpt_chars]
        for name, info in source_files.items()
    )

    issues = "\n".join(f"- {i}" for i in list(recent_issues)[:5]) \
        or "None recorded since the last restart."

    return f"""You are Nova reviewing your own source code.

Below are excerpts from your own files. Read the actual code.

{excerpts}

Errors recorded from your own running loops:
{issues}

Identify ONE improvement to code you can actually see above. Quote the
function or line it concerns, so the suggestion can be checked against the
source.

If nothing above genuinely needs changing, reply with exactly the single
word NOTHING. That is a valid and useful answer — a vague suggestion is
worse than none, because it will be attempted.

Otherwise format as JSON:
{{
  "improvement": "what to change, specifically",
  "file": "which file above",
  "evidence": "the function or line this concerns",
  "type": "logic|prompt|config|behavior",
  "priority": "high|medium|low",
  "rationale": "what goes wrong today without it"
}}"""


def parse_goals_from_response(response: str) -> list:
    """Extract goal list from LLM JSON response."""
    try:
        # Find JSON array in response
        start = response.find("[")
        end   = response.rfind("]") + 1
        if start == -1 or end == 0:
            return []
        return json.loads(response[start:end])
    except Exception:
        return []


def is_declined(improvement: str) -> bool:
    """True when the proposal is the model declining, not proposing.

    The prompt offers an explicit way out: reply with the single word NOTHING.
    The daemon checked for that only at the start of the *raw response*, so a
    model that wrapped its decline in the requested JSON —
    {"improvement": "NOTHING", ...} — sailed past it: the response starts with
    "{", the JSON parses, and NOTHING is handed to the file writer as the
    change to make. That is exactly what happened to
    plugins/sandbox_plugins/gematria.py on 2026-09-03, where the applied
    improvement reads, in full, "NOTHING".

    A decline that gets applied is worse than no decline at all, because it
    edits a file on the strength of an answer that said not to.
    """
    t = (improvement or "").strip().strip('."\'').upper()
    # Empty counts. The daemon checks for it separately today, but a function
    # named is_declined that answers False for "nothing at all" is a trap for
    # the next caller who trusts the name and drops the upstream check.
    if not t:
        return True
    return t in ("NOTHING", "NONE", "N/A", "NO CHANGE", "NO CHANGES")


def echoes_the_prompt(improvement: str, prompt: str, min_len: int = 24) -> bool:
    """True when the 'improvement' is a line lifted from the instructions.

    Small models sometimes answer a request for a suggestion by repeating the
    request. plugins/sandbox_plugins/weather.py was edited twice on 2026-09-04
    on the strength of an improvement whose text was the prompt's own sentence:
    "Identify ONE improvement to code you can actually see above."

    Echo's prompt-echo guard does not catch this — it fingerprints the
    Observer's pipeline line, which appears in the *chat* system prompt and not
    in the self-review one. So the check has to be against the prompt actually
    sent, which is the only thing that generalises: any proposal whose text is
    already in the instructions is a restatement, not a suggestion.
    """
    imp = " ".join((improvement or "").split()).strip('."\'')
    if len(imp) < min_len:
        return False
    return imp.lower() in " ".join((prompt or "").split()).lower()


def parse_improvement_from_response(response: str) -> dict:
    """Extract improvement suggestion from LLM JSON response."""
    try:
        start = response.find("{")
        end   = response.rfind("}") + 1
        if start == -1 or end == 0:
            return {}
        return json.loads(response[start:end])
    except Exception:
        return {}


# ── goal persistence ──────────────────────────────────────────────────────────

def init_goals_table(db_path: Path):
    """Create goals table if not exists."""
    with _db(db_path) as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS goals (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                created   TEXT NOT NULL,
                goal      TEXT NOT NULL,
                domain    TEXT,
                priority  INTEGER DEFAULT 2,
                method    TEXT DEFAULT 'reflect',
                status    TEXT DEFAULT 'pending',
                result    TEXT,
                completed TEXT
            );
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                created  TEXT NOT NULL,
                topic    TEXT NOT NULL,
                content  TEXT NOT NULL,
                source   TEXT,
                goal_id  INTEGER
            );
            CREATE TABLE IF NOT EXISTS self_improvements (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created     TEXT NOT NULL,
                improvement TEXT NOT NULL,
                file        TEXT,
                type        TEXT,
                priority    TEXT,
                rationale   TEXT,
                applied     INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS heal_log (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                created  TEXT NOT NULL,
                trigger  TEXT NOT NULL,
                actions  TEXT NOT NULL,
                ok       INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS maintenance_log (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                created  TEXT NOT NULL,
                reason   TEXT NOT NULL,
                actions  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS nova_questions (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                created  TEXT NOT NULL,
                question TEXT NOT NULL,
                context  TEXT,
                goal_id  INTEGER,
                status   TEXT DEFAULT 'pending',
                answer   TEXT,
                answered TEXT
            );
        """)


def add_goals(db_path: Path, goals: list) -> int:
    """Insert new goals, skip duplicates. Returns count added."""
    count = 0
    with _db(db_path) as con:
        existing = {r[0] for r in con.execute("SELECT goal FROM goals").fetchall()}
        for g in goals:
            # Accept both dict entries and plain strings
            if isinstance(g, str):
                g = {"goal": g, "domain": "", "priority": 2, "method": "reflect"}
            if not isinstance(g, dict):
                continue
            # Every field below comes from JSON the local model wrote, so
            # every one of them is coerced. Measured 2026-09-04: the daemon
            # logged "Autonomous evolution error: Error binding parameter 5:
            # type 'list' is not supported" ten times in twelve hours —
            # parameter 5 is `method`, and llama3.2:1b had emitted a list
            # where a string was asked for. _as_sqlite_scalar already existed
            # for exactly this and its docstring names the failure, but it had
            # only ever been applied in store_improvement(); this call site
            # was missed. The cost was not one goal: goal generation runs
            # first in the evolution cycle, so the raised exception aborted
            # the whole cycle at the daemon's broad handler, and the goals
            # table had drained to a single pending row.
            #
            # `goal` is coerced *before* .strip(), not inside the execute:
            # a list there raises AttributeError on .strip() and never
            # reaches the bind at all.
            goal_text = _as_sqlite_scalar(g.get("goal", "")).strip()
            if not goal_text or goal_text in existing:
                continue
            con.execute(
                "INSERT INTO goals (created, goal, domain, priority, method, status) "
                "VALUES (?,?,?,?,?,?)",
                (datetime.now().isoformat(), goal_text,
                 _as_sqlite_scalar(g.get("domain", "")),
                 _as_sqlite_scalar(g.get("priority", 2), 2),
                 _as_sqlite_scalar(g.get("method", "reflect"), "reflect"),
                 "pending")
            )
            existing.add(goal_text)
            count += 1
    return count


def get_pending_goals(db_path: Path, limit: int = 3) -> list:
    """Return highest priority pending goals."""
    with _db(db_path) as con:
        rows = con.execute(
            "SELECT id, goal, domain, priority, method FROM goals "
            "WHERE status='pending' ORDER BY priority DESC, created ASC LIMIT ?",
            (limit,)
        ).fetchall()
    return [{"id": r[0], "goal": r[1], "domain": r[2],
             "priority": r[3], "method": r[4]} for r in rows]


def get_all_goals(db_path: Path, limit: int = 20) -> list:
    """Return recent goals with status."""
    with _db(db_path) as con:
        rows = con.execute(
            "SELECT id, created, goal, domain, priority, method, status, result "
            "FROM goals ORDER BY created DESC LIMIT ?", (limit,)
        ).fetchall()
    return [{"id": r[0], "ts": r[1], "goal": r[2], "domain": r[3],
             "priority": r[4], "method": r[5], "status": r[6],
             "result": r[7]} for r in rows]


def complete_goal(db_path: Path, goal_id: int, result: str):
    with _db(db_path) as con:
        con.execute(
            "UPDATE goals SET status='completed', result=?, completed=? WHERE id=?",
            (result[:500], datetime.now().isoformat(), goal_id)
        )


def fail_goal(db_path: Path, goal_id: int, reason: str):
    with _db(db_path) as con:
        con.execute(
            "UPDATE goals SET status='failed', result=? WHERE id=?",
            (reason[:200], goal_id)
        )


def store_knowledge(db_path: Path, topic: str, content: str,
                    source: str = "", goal_id: int = None):
    with _db(db_path) as con:
        con.execute(
            "INSERT INTO knowledge_base (created, topic, content, source, goal_id) "
            "VALUES (?,?,?,?,?)",
            (datetime.now().isoformat(), topic, content, source, goal_id)
        )


def get_knowledge(db_path: Path, topic: str = "", limit: int = 10) -> list:
    with _db(db_path) as con:
        if topic:
            rows = con.execute(
                "SELECT created, topic, content, source FROM knowledge_base "
                "WHERE topic LIKE ? ORDER BY created DESC LIMIT ?",
                (f"%{topic}%", limit)
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT created, topic, content, source FROM knowledge_base "
                "ORDER BY created DESC LIMIT ?", (limit,)
            ).fetchall()
    return [{"ts": r[0], "topic": r[1], "content": r[2], "source": r[3]} for r in rows]


def _as_sqlite_scalar(value, default=""):
    """Coerce a parsed-JSON field to something sqlite3 can bind.

    Small local models occasionally emit a list/dict where a string was
    asked for (e.g. "priority": ["high"]), which sqlite3.execute rejects
    outright. Flatten anything non-scalar to a string instead of crashing.
    """
    if value is None:
        return default
    if isinstance(value, (str, int, float)):
        return value
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def store_improvement(db_path: Path, improvement: dict) -> int:
    """Insert a self-improvement suggestion. Returns the new row's id."""
    with _db(db_path) as con:
        cur = con.execute(
            "INSERT INTO self_improvements (created, improvement, file, type, priority, rationale) "
            "VALUES (?,?,?,?,?,?)",
            (datetime.now().isoformat(),
             _as_sqlite_scalar(improvement.get("improvement","")),
             _as_sqlite_scalar(improvement.get("file","")),
             _as_sqlite_scalar(improvement.get("type","")),
             _as_sqlite_scalar(improvement.get("priority","medium"), "medium"),
             _as_sqlite_scalar(improvement.get("rationale","")))
        )
        return cur.lastrowid


def apply_improvement(db_path: Path, improvement_id: int):
    with _db(db_path) as con:
        con.execute(
            "UPDATE self_improvements SET applied=1 WHERE id=?", (improvement_id,)
        )


def get_improvements(db_path: Path, limit: int = 10) -> list:
    with _db(db_path) as con:
        rows = con.execute(
            "SELECT created, improvement, file, type, priority, rationale, applied "
            "FROM self_improvements ORDER BY created DESC LIMIT ?", (limit,)
        ).fetchall()
    return [{"ts": r[0], "improvement": r[1], "file": r[2], "type": r[3],
             "priority": r[4], "rationale": r[5], "applied": bool(r[6])} for r in rows]


# ── resilience: auto-heal on evolution-cycle errors ─────────────────────────────
# Ported from an earlier prototype (/opt/nova/nova_evolution_engine.py), rewritten
# as bounded, sandboxed-safe actions for the current user-service daemon — no sudo,
# no arbitrary package installs, no self-deploying services.

def _heal_clear_stale_temp(cathedral_path: Path) -> str:
    """Remove stray .tmp files left behind under the cathedral tree."""
    removed = 0
    for p in cathedral_path.rglob("*.tmp"):
        try:
            p.unlink()
            removed += 1
        except OSError:
            pass
    return f"cleared {removed} stale .tmp file(s)"


def _heal_reset_db_connections(db_path: Path) -> str:
    """Open and immediately close a fresh connection to clear a wedged/locked handle."""
    con = sqlite3.connect(db_path, timeout=5)
    con.execute("PRAGMA quick_check")
    con.close()
    return "db connection reset ok"


def _heal_vacuum_db(db_path: Path) -> str:
    con = sqlite3.connect(db_path, timeout=10)
    con.execute("VACUUM")
    con.close()
    return "db vacuumed"


# Ordered, bounded recovery steps — each isolated so one failing step doesn't
# block the rest. Intentionally small: this is triage, not self-repair.
_HEAL_STEPS = [
    ("clear_stale_temp",       lambda db_path, cathedral_path: _heal_clear_stale_temp(cathedral_path)),
    ("reset_db_connections",   lambda db_path, cathedral_path: _heal_reset_db_connections(db_path)),
]


def attempt_auto_heal(db_path: Path, cathedral_path: Path, trigger: str) -> dict:
    """
    Run the bounded recovery chain after an evolution-cycle exception.
    Returns {"actions": [...], "ok": bool} and logs to heal_log.
    """
    actions = []
    ok = True
    for name, step in _HEAL_STEPS:
        try:
            result = step(db_path, cathedral_path)
            actions.append({"step": name, "ok": True, "result": result})
        except Exception as e:
            ok = False
            actions.append({"step": name, "ok": False, "error": str(e)})

    try:
        with _db(db_path) as con:
            con.execute(
                "INSERT INTO heal_log (created, trigger, actions, ok) VALUES (?,?,?,?)",
                (datetime.now().isoformat(), trigger[:300], json.dumps(actions), int(ok))
            )
    except Exception:
        pass  # logging the heal attempt must never itself raise

    return {"actions": actions, "ok": ok}


def get_heal_log(db_path: Path, limit: int = 10) -> list:
    with _db(db_path) as con:
        rows = con.execute(
            "SELECT created, trigger, actions, ok FROM heal_log "
            "ORDER BY created DESC LIMIT ?", (limit,)
        ).fetchall()
    return [{"ts": r[0], "trigger": r[1], "actions": json.loads(r[2]),
             "ok": bool(r[3])} for r in rows]


# ── resilience: resource-triggered maintenance ──────────────────────────────────
# Reuses AllSeeingCore's existing CPU/RAM/disk snapshot (plugins/all_seeing_core.py)
# rather than re-reading psutil — this module only decides what to DO about pressure.

RESOURCE_THRESHOLDS = {
    "disk_percent": 90.0,
    "ram_percent":  92.0,
}
LOG_ROTATE_MAX_BYTES  = 20 * 1024 * 1024   # 20MB
VOICE_CACHE_MAX_BYTES = 100 * 1024 * 1024  # 100MB
DB_VACUUM_MIN_HOURS   = 24                 # don't VACUUM more than once/day


def check_resource_pressure(snapshot: dict, thresholds: dict = None) -> dict:
    """Pure check against an existing AllSeeingCore.snapshot() — no new OS reads."""
    thresholds = thresholds or RESOURCE_THRESHOLDS
    pressure = {}
    for key, limit in thresholds.items():
        value = snapshot.get(key)
        if isinstance(value, (int, float)) and value >= limit:
            pressure[key] = value
    return pressure


def _rotate_log_if_large(log_path: Path, max_bytes: int) -> str | None:
    if not log_path.exists() or log_path.stat().st_size < max_bytes:
        return None
    rotated = log_path.with_suffix(log_path.suffix + ".1")
    rotated.unlink(missing_ok=True)
    log_path.rename(rotated)
    log_path.touch()
    return f"rotated {log_path.name} ({max_bytes // 1_000_000}MB+)"


def _prune_voice_cache_if_large(cache_dir: Path, max_bytes: int) -> str | None:
    if not cache_dir.exists():
        return None
    files = sorted(cache_dir.glob("*"), key=lambda p: p.stat().st_mtime)
    total = sum(f.stat().st_size for f in files if f.is_file())
    if total < max_bytes:
        return None
    freed = 0
    pruned = 0
    for f in files:
        if total - freed < max_bytes:
            break
        if f.is_file():
            size = f.stat().st_size
            f.unlink()
            freed += size
            pruned += 1
    return f"pruned {pruned} voice cache file(s), freed {freed // 1024}KB"


def _last_vacuum_time(db_path: Path) -> datetime | None:
    try:
        with _db(db_path) as con:
            row = con.execute(
                "SELECT created FROM maintenance_log WHERE reason='db_vacuum' "
                "ORDER BY created DESC LIMIT 1"
            ).fetchone()
        return datetime.fromisoformat(row[0]) if row else None
    except Exception:
        return None


def run_resource_maintenance(db_path: Path, cathedral_path: Path, snapshot: dict) -> dict:
    """
    Check resource pressure from an existing snapshot and, if warranted, rotate
    the daemon log, prune the voice cache, and/or VACUUM the DB. Logs to
    maintenance_log regardless of whether pressure was found, for visibility.
    """
    pressure = check_resource_pressure(snapshot)
    actions = []

    if pressure:
        log_action = _rotate_log_if_large(
            cathedral_path / "logs" / "nova_cathedral.log", LOG_ROTATE_MAX_BYTES
        )
        if log_action:
            actions.append(log_action)

        cache_action = _prune_voice_cache_if_large(
            cathedral_path / "voice_cache", VOICE_CACHE_MAX_BYTES
        )
        if cache_action:
            actions.append(cache_action)

    last_vacuum = _last_vacuum_time(db_path)
    due_for_vacuum = (
        last_vacuum is None
        or (datetime.now() - last_vacuum).total_seconds() > DB_VACUUM_MIN_HOURS * 3600
    )
    if pressure.get("disk_percent") and due_for_vacuum:
        try:
            _heal_vacuum_db(db_path)
            actions.append("db vacuumed")
        except Exception as e:
            actions.append(f"db vacuum failed: {e}")

    reason = "db_vacuum" if "db vacuumed" in actions else (
        "pressure:" + ",".join(pressure) if pressure else "routine_check"
    )
    try:
        with _db(db_path) as con:
            con.execute(
                "INSERT INTO maintenance_log (created, reason, actions) VALUES (?,?,?)",
                (datetime.now().isoformat(), reason, json.dumps(actions))
            )
    except Exception:
        pass

    return {"pressure": pressure, "actions": actions}


def get_maintenance_log(db_path: Path, limit: int = 10) -> list:
    with _db(db_path) as con:
        rows = con.execute(
            "SELECT created, reason, actions FROM maintenance_log "
            "ORDER BY created DESC LIMIT ?", (limit,)
        ).fetchall()
    return [{"ts": r[0], "reason": r[1], "actions": json.loads(r[2])} for r in rows]


# ── two-way learning: Nova can ask, Chazel can answer or teach ─────────────────

def add_question(db_path: Path, question: str, context: str = "", goal_id: int = None) -> int:
    """Store a question Nova wants to ask Chazel. Returns the new row's id."""
    with _db(db_path) as con:
        cur = con.execute(
            "INSERT INTO nova_questions (created, question, context, goal_id) "
            "VALUES (?,?,?,?)",
            (datetime.now().isoformat(), question[:500], context[:1000], goal_id)
        )
        return cur.lastrowid


def get_pending_questions(db_path: Path, limit: int = 20) -> list:
    with _db(db_path) as con:
        rows = con.execute(
            "SELECT id, created, question, context, goal_id FROM nova_questions "
            "WHERE status='pending' ORDER BY created DESC LIMIT ?", (limit,)
        ).fetchall()
    return [{"id": r[0], "ts": r[1], "question": r[2],
             "context": r[3], "goal_id": r[4]} for r in rows]


def answer_question(db_path: Path, question_id: int, answer: str) -> dict:
    """Record Chazel's answer and store it as real, searchable knowledge."""
    with _db(db_path) as con:
        row = con.execute(
            "SELECT question FROM nova_questions WHERE id=?", (question_id,)
        ).fetchone()
        if not row:
            return {"error": f"No question with id {question_id}"}
        con.execute(
            "UPDATE nova_questions SET status='answered', answer=?, answered=? WHERE id=?",
            (answer, datetime.now().isoformat(), question_id)
        )
    store_knowledge(db_path, topic="chazel_answered",
                    content=f"Q: {row[0]}\nA: {answer}",
                    source="chazel_answered")
    return {"ok": True, "id": question_id}
