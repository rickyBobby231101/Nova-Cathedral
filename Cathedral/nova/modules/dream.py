"""The Dream loop — neuronode speaking back into the knowledge graph.

`~/neuronode` holds a 4.8M-parameter character-level transformer trained from
scratch on the Cathedral's own text (mythos, blueprint, knowledge dump, plugin
source). It is not an assistant and cannot be asked anything: it only continues
text. That single capability is enough for one honest job — given a real
sentence from the graph, it produces the Cathedral's own vocabulary recombined,
which Eyemoeba can then mine for motifs like any other node.

So this is deliberately NOT a sixth conversational entity. It is a stochastic
echo of what the Cathedral has already written, and the loop reads:

    a real cross-domain motif
      -> seeded with real evidence text from the nodes carrying it
        -> neuronode continues it
          -> stored as a 'dream' node in knowledge_nodes
            -> Eyemoeba's next scan reads it like any other node

Nothing new is needed to close that last step: `_eyemoeba_analyze` already
scans every row of knowledge_nodes, so a stored dream is mined automatically.

WHY THE FILTERING BELOW IS NOT OPTIONAL
---------------------------------------
The model is badly overfit — 4.8M parameters against 307KB of text, final
train loss 0.155 against val loss 1.692 — and 91% of its corpus was a single
knowledge dump carrying 185 ISO-timestamp headers and 13 stored LLM refusals.
It memorised that scaffolding. Sampled directly it very often opens with a
verbatim timestamp header, a "**Key Insights:**" heading, or the refusal
"I can't assist with creating or using an autonomous system…" — none of which
is Cathedral content, all of which would be nonsense inside a knowledge node.

Nova has been bitten twice by exactly this class of bug (stored reflection
refusals, entity non-answers fed back as context), and the lesson recorded both
times was to gate on real imperfect output rather than trust the happy path.
`distill()` is that gate: it strips the memorised furniture, and if what
remains is not real prose it returns "" so the caller stores nothing.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

# Where neuronode lives. Overridable so the daemon can run against a copy
# (or a future retrained checkpoint) without editing code.
NEURONODE_DIR = Path(os.environ.get(
    "NOVA_NEURONODE_DIR", str(Path.home() / "neuronode")))

# neuronode has its own virtualenv holding torch; the daemon runs on the system
# interpreter and must not import torch into its own process. Shelling out
# keeps that dependency entirely on the other side of a process boundary —
# the same isolation stance code_sandbox takes for plugins.
VENV_PYTHON = NEURONODE_DIR / ".venv" / "bin" / "python"
GENERATE_PY = NEURONODE_DIR / "generate.py"
CHECKPOINT = NEURONODE_DIR / "checkpoints" / "latest.pt"

# ~57s for 400 tokens on this CPU, so these are chosen for a background cycle
# rather than for a rich sample: enough characters to carry a few sentences,
# little enough that a dream never pins a core for a full minute.
DEFAULT_TOKENS = 260
DEFAULT_TEMPERATURE = 0.85
DEFAULT_TOP_K = 40
DEFAULT_TIMEOUT = 180

# A dream shorter than this after distilling isn't worth a node.
MIN_DREAM_CHARS = 80

# ── memorised furniture, all of it observed in real samples ───────────────
# Every pattern here removes a *token*, never a whole line. Knowledge nodes
# routinely run header and prose together on one line — "## 2026-07-18T19:53
# **Key Insights:** * The Cathedral's stone patterns hold aetheric resonance"
# — so dropping matched lines threw the sentence away with the scaffolding.
#
# "## 2026-05-21T11:17:08.12344" — the knowledge dump's per-entry header,
# which appears both alone on a line and inline ahead of real text.
_TIMESTAMP = re.compile(r"#{0,6}\s*\d{4}-\d{2}-\d{2}T[\d:.]+")
# Leading "#"/"###" markers; whatever follows them may well be prose.
_HEADING_MARKER = re.compile(r"^\s*#{1,6}\s*")
# "**Key Insights:**", "**History-based flexibility**:" — corpus formatting.
_BOLD_LABEL = re.compile(r"\*\*([^*]{2,60})\*\*\s*:?\s*")
# Bullet furniture at the head of a line; the text after it may be fine.
_BULLET_PREFIX = re.compile(r"^\s*([*•\-]|\d+\.)\s+")

# Refusals memorised verbatim from conversations logged before Nova's own
# refusal purge (commit 88fee72) — the corpus was harvested three days
# earlier, so the model learned them as ordinary Cathedral text.
_REFUSAL_MARKERS = (
    "i can't assist",
    "i cannot assist",
    "i can't fulfill",
    "i cannot fulfill",
    "i can't help with that",
    "i'm not able to provide",
    "can i help you with som",
    "is there anything else",
)

_SENTENCE_END = re.compile(r"[.!?]")


def available() -> dict:
    """Whether a dream can be generated at all, and if not, precisely why.

    Returned rather than raised: the daemon calls this on a schedule, and a
    missing checkpoint is an ordinary state (neuronode is a separate project
    that may not be present), not an error worth a traceback.
    """
    for label, path in (("neuronode directory", NEURONODE_DIR),
                        ("neuronode venv python", VENV_PYTHON),
                        ("generate.py", GENERATE_PY),
                        ("trained checkpoint", CHECKPOINT)):
        if not path.exists():
            return {"available": False,
                    "reason": f"{label} not found at {path}"}
    return {"available": True, "checkpoint": str(CHECKPOINT)}


def _strip_refusal_sentences(text: str) -> str:
    """Drop whole sentences that are memorised refusals.

    Sentence-level rather than line-level: the refusal usually arrives as one
    complete sentence sitting in front of otherwise usable continuation, so
    cutting the line would throw away good text with it.
    """
    parts = re.split(r"(?<=[.!?])\s+", text)
    kept = [p for p in parts
            if not any(m in p.lower() for m in _REFUSAL_MARKERS)]
    return " ".join(kept)


def _strip_furniture(text: str) -> str:
    """Remove the memorised markdown scaffolding, keeping the prose.

    Used on both ends of the loop. On the way out it cleans the model's
    sample; on the way in it cleans the evidence text used as a seed — the
    knowledge nodes carry this same furniture (Nova's own LLM wrote them, and
    they are where neuronode's corpus came from), so seeding straight from a
    node would prompt the model to continue in exactly the memorised format
    the filter is trying to remove. Observed live: a seed built from raw node
    content opened "## 2026-07-18T19:53:01 **Key Insights:**".
    """
    lines = []
    for line in text.splitlines():
        # Order matters: the bold label has to go before the bullet, because
        # a line often reads "* **Label**: prose" and removing the label is
        # what exposes the bullet as the leading token.
        line = _TIMESTAMP.sub(" ", line)
        line = _HEADING_MARKER.sub("", line)
        line = _BOLD_LABEL.sub("", line)
        line = _BULLET_PREFIX.sub("", line)
        line = line.replace("*", "").strip()
        if line:
            lines.append(line)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def _drop_leading_fragment(text: str) -> str:
    """Drop an opening half-sentence left over from completing the seed.

    The seed deliberately ends on an open clause ("…runs through this, and "),
    so the model's first sentence is a fragment finishing *that* clause rather
    than a thought of its own. Read as a continuation it is fine; stored alone
    as a node it reads as starting mid-thought — the first live dream opened
    "behaviors, and confidence.", which is what prompted this.

    Only fires when the opening really looks like a continuation (its first
    letter is lower-case) and when enough text survives without it. A slightly
    awkward node beats no node, given how many samples are already rejected.
    """
    stripped = text.lstrip()
    first_letter = next((c for c in stripped if c.isalpha()), "")
    if not first_letter or not first_letter.islower():
        return text

    ends = [m.end() for m in _SENTENCE_END.finditer(text)]
    if len(ends) < 2:
        # One sentence only: dropping it would leave nothing at all.
        return text

    remainder = text[ends[0]:].strip()
    return remainder if len(remainder) >= MIN_DREAM_CHARS else text


def distill(raw: str, prompt: str = "") -> str:
    """Turn a raw sample into storable prose, or "" if there isn't any.

    Returning "" is a normal outcome and means the caller must not store a
    node. Given how strongly this checkpoint is drawn to its memorised
    scaffolding, an empty result is expected a fair share of the time —
    three of the first four real samples taken in development were rejected
    here, which is the filter working, not failing.
    """
    if not raw:
        return ""

    # generate.py decodes the seed along with the continuation, so the prompt
    # comes back as a prefix. Only the continuation is the model's own.
    text = raw
    if prompt and text.startswith(prompt):
        text = text[len(prompt):]

    text = _strip_furniture(text)
    text = _strip_refusal_sentences(text)
    text = re.sub(r"\s+", " ", text).strip()

    # The sample almost always stops mid-word at the token limit. Cut back to
    # the last completed sentence so a node never ends on a fragment.
    ends = [m.end() for m in _SENTENCE_END.finditer(text)]
    if ends:
        text = text[:ends[-1]].strip()
    elif len(text) < MIN_DREAM_CHARS:
        # No sentence boundary and not much text: nothing usable here.
        return ""

    text = _drop_leading_fragment(text)

    if len(text) < MIN_DREAM_CHARS:
        return ""
    return text


def seed_from_evidence(snippets: list[str], term: str,
                       max_chars: int = 400) -> str:
    """Build the seed text for a dream out of real nodes carrying `term`.

    This is the part that makes the loop a conversation between nodes rather
    than free association: the model is handed actual sentences the graph has
    already written about the motif, and its continuation is a continuation
    of *those*. The trailing clause is an open one so the sample begins
    mid-thought instead of starting a fresh document (which is what invites
    the memorised "## <timestamp>" header).

    Truncated from the end because the model's context is 256 characters —
    the tail is what it actually conditions on.
    """
    cleaned = []
    for s in snippets:
        s = _strip_furniture(s)
        # Whole-sentence fragments only; a half sentence teaches it nothing.
        if len(s) >= 40:
            cleaned.append(s[:180].strip())
    lead = " ".join(cleaned[:2])
    bridge = f" The pattern of {term} runs through this, and "
    return (lead + bridge)[-max_chars:]


def generate(prompt: str,
             max_new_tokens: int = DEFAULT_TOKENS,
             temperature: float = DEFAULT_TEMPERATURE,
             top_k: int = DEFAULT_TOP_K,
             seed: int | None = None,
             timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Run one sample through neuronode's own interpreter.

    Blocking and CPU-bound for roughly a minute — callers inside the daemon
    must hand this to a thread rather than run it on the event loop.
    """
    state = available()
    if not state["available"]:
        return {"error": state["reason"]}

    cmd = [str(VENV_PYTHON), str(GENERATE_PY),
           "--prompt", prompt,
           "--max_new_tokens", str(max_new_tokens),
           "--temperature", str(temperature),
           "--top_k", str(top_k)]
    if seed is not None:
        cmd += ["--seed", str(seed)]

    try:
        proc = subprocess.run(
            cmd, cwd=str(NEURONODE_DIR), capture_output=True,
            text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"error": f"neuronode did not finish within {timeout}s"}
    except OSError as e:
        return {"error": f"could not run neuronode: {e}"}

    if proc.returncode != 0:
        detail = (proc.stderr or "").strip().splitlines()
        return {"error": "neuronode failed: "
                         + (detail[-1] if detail else "no output")}

    return {"raw": proc.stdout, "prompt": prompt}


def dream(prompt: str, attempts: int = 2, **kwargs) -> dict:
    """Sample until something survives distilling, up to `attempts` tries.

    Each attempt costs most of a minute, so this stays deliberately small —
    it exists because the refusal opening is common enough that one rejected
    sample shouldn't waste the whole cycle, not to brute-force good output.
    """
    last_error = None
    for i in range(max(1, attempts)):
        # Vary the seed per attempt; without it a fixed seed would resample
        # the identical refusal every time.
        result = generate(prompt, seed=kwargs.pop("seed", None) or (i + 1) * 17,
                          **kwargs)
        if "error" in result:
            last_error = result["error"]
            continue
        text = distill(result["raw"], prompt)
        if text:
            return {"text": text, "attempts": i + 1, "raw": result["raw"]}
        last_error = "sample was memorised scaffolding or a refusal"
    return {"error": last_error or "no usable sample"}
