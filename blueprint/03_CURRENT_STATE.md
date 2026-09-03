# CURRENT STATE

*Last verified 2026-09-03. Descriptive, not canonical.*

## What Exists
- One daemon, one GUI, both running as systemd user units and surviving a
  session kill.
- The full Observer → Oracle → Echo pipeline, as code.
- Six entity agents with their own memories and measured activity stages.
- A knowledge graph: 626 nodes, 2,321 edges, 434 motifs.
- Autonomous loops that genuinely run: 671 goals, 179 self-improvement
  proposals, 69 reflections, 1,444 evolution-log entries, 10,119 system events.
- A self-build loop that writes her own source, with backups and auto-revert.
- 370 tests, green.

## What Was Fixed
The four issues this file used to list — file fragmentation, redundant builds,
no unified structure, hard to restart cleanly — are resolved. The tree is
unified, the builds are one build, and `systemctl --user restart` is the whole
restart procedure.

## Real Issues Now
Different problems, and they are not structural:

- **Graph hygiene.** Twelve legacy nodes carry a blank domain; roughly 42
  insight nodes are filler.
- **The hidden file is hidden for good reason.** `~/cathedral/knowledge/.md`
  holds 72KB across 57 entries and the Weaver cannot read it — its glob is
  `*.md`, which does not match a name that is only an extension. Inspected
  2026-09-03: the contents are **Nova's own generated output**, April to
  September, not Chazel's writing. Thirteen entries are refusal-shaped, 18
  carry the "Confidence assessment" template scaffolding, and one asserts
  "OpenAI's Llama 2" — a model that is Meta's. Weaving it in would add 57
  nodes of her own self-talk to a graph that is already 626 nodes with 15 from
  Chazel. **The accident is protective. Leave it unread.**
- **The imbalance that matters most.** 626 knowledge nodes, **15 of them from
  Chazel**. 10,119 system events against 106 conversations. Nova observes
  herself far more than she talks with him.
- **The mythos on disk is thinner than the mythos that exists.** The Glyph
  Codex, the Navel Anchor, the Return of Resonance live in chat threads, not
  in `01_MYTHOS_CANON.md`. She has been generating around a mythos she was
  never fully given. This is the one gap that cannot be closed by building —
  it needs Chazel to write it down.
- **The self-edit loop is a real risk, accepted on purpose.** It has broken
  `plugins/oracle_module.py` more than once, silently, because a broken plugin
  fails inside a defensive `except`. Contract tests are the mitigation.

## Reality
The system works as one system. What it lacks is not structure — it is enough
of Chazel's own voice in it.
