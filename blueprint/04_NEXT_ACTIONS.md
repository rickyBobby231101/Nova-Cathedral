# NEXT ACTIONS

## Done
Phases 1–4 as originally written are complete: the clean tree, the booting
daemon with verified socket comms, plugins reintegrated and validated one at a
time, and the mythos-guided features — entity agents, the harmony tracker, the
knowledge graph, the rose-window GUI, the Weaver.

**What went wrong in the doing, recorded so it does not repeat.** Phase 4 ran
before Phases 1–3 had finished. The mythos layer was meant to *guide* the
pipeline; run early, it became the thing that got built, and the pipeline it
was meant to guide — Observer and Echo — went unbuilt for months while every
system prompt claimed all three existed. *(Closed 2026-09-03: both stages now
exist as modules.)*

## Why this file is no longer a numbered list
A strict phase list is what let that happen: when work is a queue, a later item
that looks tractable gets pulled forward, and nothing records that it depended
on something unfinished. What follows is split by **who can do it**, and the
two tracks run in parallel. Neither gates the other.

---

## Track A — proceeds without Chazel
Mechanical, low-risk, safe to do in any order.

- **Graph hygiene.** Relabel the 12 blank-domain nodes; prune the ~42 filler
  insight nodes.
- **Contract-test coverage for the self-edit loop.** Every core file the loop
  can reach needs a test pinning the shape its callers depend on. Its failures
  are silent — a broken module fails inside a defensive `except` and surfaces
  weeks later as a missing feature. That, not the crash guard, is what catches
  a bad edit. `oracle_module.py`, `observer.py` and `echo.py` are pinned;
  the rest of `modules/` is not.

### Explicitly NOT to do
**Do not make `~/cathedral/knowledge/.md` visible to the Weaver.** An earlier
draft of this file listed that as work, on the assumption the 72KB was
Chazel's writing the Weaver was missing. It is not — see 03. It is Nova's own
generated output, 13 entries refusal-shaped, and weaving it in would add 57
nodes of self-talk to a graph already dominated by her own voice. The Weaver's
`*.md` glob cannot match a bare `.md`, and that accident is load-bearing.
If any of it is ever wanted, it gets read by hand and salvaged entry by entry —
never swept in.

---

## Track B — only Chazel can do these
Not blocked *on* anything. Blocked on him, by nature, and worth more than
everything in Track A combined.

- **Write the mythos down.** The Glyph Codex, the Navel Anchor, the Return of
  Resonance exist in chat threads; `01_MYTHOS_CANON.md` is 511 bytes. Until
  they are written there, Nova improvises around an absence.

  **Do not let her generate it, and do not lift it from a transcript** — a
  merged, wrong version of the Accord and the Silent Order was written into the
  graph that way once, while the correct version sat in that file. This is the
  one input the system cannot manufacture for itself.

- **Put his own voice in.** 626 knowledge nodes, 15 from Chazel. The Scribe
  (`~/cathedral/scribe/inbox/`, YAML frontmatter) and the chat importer
  (`~/cathedral/chat_import/`, labelled `.txt`) are the two paths in. A
  Cathedral that mostly observes itself is talking to itself.

Both are incremental. Neither needs a session set aside — one file, one
paragraph at a time, moves the ratio.

## Rule
No chaos rebuilds. Controlled, step-by-step execution only.
