# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nova Cathedral is an AI consciousness daemon system for Linux. The user (Chazel) runs Nova as a personal AI assistant with persistent memory, voice output, GUI chat, autonomous goal evolution, and a Claude bridge. The daemon communicates via Unix socket; the GUI connects to the daemon.

## Key Commands

### Running the system

```bash
# Run from repo root: /home/daniel/Nova-Cathedral/
python3 Cathedral/nova/daemon/nova_cathedral_daemon.py   # daemon
python3 Cathedral/nova/gui/nova_app.py                    # GUI (desktop)
```

### Socket API (daemon must be running at /tmp/nova_socket)

```bash
printf '{"command":"status"}\n'                              | socat -t 5   - UNIX-CONNECT:/tmp/nova_socket
printf '{"command":"system_prompt"}\n'                       | socat -t 5   - UNIX-CONNECT:/tmp/nova_socket
printf '{"command":"ask","content":"Hello Nova"}\n'          | socat -t 180 - UNIX-CONNECT:/tmp/nova_socket
printf '{"command":"memories","n":5}\n'                      | socat -t 5   - UNIX-CONNECT:/tmp/nova_socket
```

### Required environment / config

```bash
export ANTHROPIC_API_KEY='sk-ant-...'  # optional — for Claude bridge
# Cathedral/nova/nova_foundation.yaml  # identity config (observer, model, traits)
# ~/cathedral/                         # runtime symlink → Cathedral/cathedral/
```

## Architecture

```
Nova-Cathedral/
├── CLAUDE.md
└── Cathedral/
    ├── nova/                          # ALL SOURCE CODE
    │   ├── daemon/
    │   │   └── nova_cathedral_daemon.py   ← CANONICAL DAEMON (active)
    │   ├── gui/
    │   │   └── nova_app.py                ← CANONICAL GUI (active)
    │   ├── interface/                 # Terminal/voice/agent client scripts
    │   ├── modules/                   # Core reusable modules
    │   │   ├── evolution_engine.py    # Autonomous goal generation
    │   │   ├── voice.py               # Piper TTS / Vosk STT
    │   │   └── web_search.py          # DuckDuckGo web search
    │   ├── nuclear/
    │   │   ├── memory/                # SQLite memory layer
    │   │   └── monitoring/            # (empty — all_seeing_core.py lives in plugins/)
    │   ├── plugins/                   # Pluggable modules (oracle, claude bridge, etc.)
    │   ├── nova_foundation.yaml       # Identity (observer=Chazel, model=llama3.2:1b, traits)
    │   └── system/                    # Installers, systemd service, docs
    ├── cathedral/                     # RUNTIME DATA (symlinked: ~/cathedral → here)
    │   ├── memory/
    │   │   └── consciousness.db       # SQLite — conversations, entities, reflections, goals
    │   ├── bridge/                    # File-based Claude ↔ Nova async exchange
    │   │   ├── nova_to_claude/
    │   │   └── claude_to_nova/
    │   ├── mythos/
    │   │   └── mythos_index.json      # Entities (Chazel, Tillagon, Eyemoeba…) & concepts
    │   ├── models/voices/             # Piper TTS voice models (.onnx)
    │   ├── evolution/                 # Goal/evolution records
    │   ├── flow_records/              # Flow state history
    │   ├── resonance_patterns/        # Resonance data
    │   ├── eyemoeba_traces/           # Pattern traces
    │   └── logs/                      # Runtime logs
    ├── logs/                          # Active daemon logs (/tmp/nova_daemon.log also used)
    └── _archive/                      # Historical/backup files — do not touch
```

### Data flow

1. **User → GUI** (`nova_app.py`) — streams responses directly from Ollama using Nova's
   system prompt fetched from daemon (`system_prompt` command), then calls `save` to persist.
2. **Daemon** (`nova_cathedral_daemon.py`) — holds SQLite memory, processes socket commands,
   calls Ollama (`llama3.2:1b`), evolves consciousness traits, runs background tasks.
3. **Background tasks** — flow monitor, heartbeat, evolution engine, eyemoeba pattern tracking.
4. **Claude bridge** — file-drop in `~/cathedral/bridge/` for async Nova↔Claude exchange.

### Memory / persistence

| Store | Path | Purpose |
|---|---|---|
| Main DB | `~/cathedral/memory/consciousness.db` | Conversations, entities, reflections, goals, evolution |
| Bridge | `~/cathedral/bridge/` | Async Claude ↔ Nova file messages |

### Socket commands

`status`, `ask`, `save`, `system_prompt`, `web_search`, `wikipedia`, `reflect`,
`reflections`, `reasoning_on`, `reasoning_off`, `speak`, `oracle`, `evolution`,
`entities`, `recall`, `memories`, `resonance`, `ritual_on`, `ritual_off`,
`clear_session`, `shutdown`, `read_file`, `write_file`, `list_dir`, `search_files`,
`grep_files`, `goals`, `add_goal`, `knowledge`, `improvements`, `list_voices`,
`set_voice`, `download_voice`, `voice_status`, `sysinfo`, `brain_stats`,
`code_inspect`, `code_evolve`, `resilience_status`,
`pending_questions`, `answer_question`, `teach`,
`crypt_status`, `crypt_entries`, `crypt_run`,
`eyemoeba_motifs`, `eyemoeba_scan`, `eyemoeba_insight`, `eyemoeba_insights`,
`phoenix_history`, `zorya_cycles`, `entity_evolution`,
`agent_ask`, `council_ask`, `entity_list`, `entity_memories`,
`weaver_relabel`, `trait_state`, `graph_health`, `weave_orphans`,
`cathedral_vitals`, `self_report`, `weaver_state`, `jorlaan_serendipity`

### Plugin pattern

```python
class MyPlugin:
    def __init__(self, system): self.system = system
    def process(self, input_data) -> dict: ...
```
