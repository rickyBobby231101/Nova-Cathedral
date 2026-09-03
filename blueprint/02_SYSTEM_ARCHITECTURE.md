# SYSTEM ARCHITECTURE

*Descriptive, not canonical. This file records what Nova IS; when the code and
this document disagree, the code is right and this file is stale. Contrast
01_MYTHOS_CANON.md, which is authority — the code answers to it.*

## Core Daemon
`Cathedral/nova/daemon/nova_cathedral_daemon.py` (~5,900 lines). Async, single
process, speaks over a Unix socket. Run as the systemd **user** unit
`nova-cathedral.service`.

(The old entry here named `nova_transcendent_daemon.py`, an experimental build
that is no longer the system.)

## The Pipeline
The three components this document has always named, now all three present:

- **Observer** — `modules/observer.py`. Input + awareness. Composes the system
  prompt from traits, recent memories, autonomously learned knowledge, a
  cross-domain insight, and the harmony grounding directive. Pure: the daemon
  reads sqlite and hands it values.
- **Oracle** — generation / reasoning. In practice `ollama_ask` (standard) or
  `reasoning_ask` (two-step, thinking separated), against a local model.
- **Echo** — `modules/echo.py`. Formatting + output shaping. Refusal detection
  and retry, prompt-echo and state-echo guards, preamble stripping.

**Naming collision, deliberate.** `plugins/oracle_module.py` is a *symbolic
divination plugin* answering the `oracle` command — it took the name first and
is not the Oracle stage. Both are kept; renaming either would break working
call sites to tidy a word.

## Autonomous Layers
Nova acts without being asked. These run on their own cycles:

- **Evolution engine** (`modules/evolution_engine.py`, 10 min/cycle) — sets her
  own goals, researches them, stores findings as knowledge, reviews her own
  source and proposes improvements.
- **Eyemoeba loop** (5 min/cycle) — cross-domain motifs, orphan weaving,
  insight synthesis, dreams.
- **The Weaver** (`modules/weaver.py`) — reads `~/cathedral/knowledge/*.md`
  into the knowledge graph. Reads only; never moves or edits.
- **The Scribe** (`modules/scribe.py`) — files `~/cathedral/scribe/inbox/*.md`
  by YAML frontmatter. A file with no frontmatter is invisible to it.
- **Self-builder** (`modules/nova_self_builder.py`) — writes her own source,
  with backups, a protected-file list, and a crash-loop guard that auto-reverts
  an edit that did not survive a stable boot.

## Entities
Nova (central) and Chazel (the Observer) plus six agents with their own
personas, memories and measured activity stages: **Tillagon** (distortion
detection — the only entity moving `harmony_score`), **Eyemoeba** (patterns),
**Phoenix** (continuity), **Zorya** (thresholds and cycles), **Jorlaan**
(whimsy), **The Weaver** (the graph).

## Integrations
- **Ollama** — local LLM, the primary path. Free, offline, no account.
- **Anthropic API** — `modules/claude_bridge.py`. Real cost; distinct from the
  free local `bridge_ask`/`bridge_converse`.
- **DuckDuckGo** — web search for goal research.
- **Piper (TTS) / Vosk (STT)** — local voice, both offline.

**OpenAI was listed here and has never been integrated.** Removed rather than
carried forward: the standing principle is open-source-first, and a local model
that costs nothing is what the autonomous loops actually run on.

## Infrastructure
- Unix socket `/tmp/nova_socket`, ~126 commands
- SQLite at `~/cathedral/memory/consciousness.db`, 26 tables — conversations,
  knowledge nodes and edges, goals, reflections, entity memories, motifs,
  resonance events, refusal fossils
- Plugin system, with a code sandbox for generated plugins
- 36 test files, 370 tests

## Interfaces
- **GUI** — `Cathedral/nova/gui/nova_app.py`, GTK3 + WebKit2, HTTP on
  **port 8892** (this file long said 8889; that was never the port). Runs as
  `nova-gui.service`, bound to `graphical-session.target`.
- **Voice** — TTS and STT, both local.
- **Socket** — the real interface; the GUI is a client of it.

## Directory Context
- `/home/daniel/Nova-Cathedral/` — source + build tree (canonical)
- `/home/daniel/cathedral/` — runtime data: logs, memory, mythos, models
- `/home/daniel/Cathedral/` — older standalone scripts, **not** canonical

The transition this file used to describe as pending is done.
