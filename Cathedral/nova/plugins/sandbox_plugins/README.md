# Sandbox plugins

Tracked source copies of the input→output plugins that run via the daemon's
`plugin_run` command (sandboxed through `code_sandbox.py`, `system=None`).

The daemon loads plugins from the **runtime** dir `~/cathedral/plugins/auto/`,
which is gitignored — so these copies here are the version-controlled source
of truth. To deploy one:

```bash
cp Cathedral/nova/plugins/sandbox_plugins/<name>.py ~/cathedral/plugins/auto/
```

Each plugin is a self-contained class:

```python
class NovaPlugin:
    def __init__(self, system):   # system is always None in the sandbox
        self.system = system
    def process(self, input_data: dict) -> dict:
        ...
def get_plugin():
    return NovaPlugin
```

Constraints (enforced by `code_sandbox.py`): no `subprocess`, `eval`, `exec`,
`os.system`, `ctypes`, or file deletion outside `~/cathedral`. Pure stdlib +
`urllib` for network is fine.

## Current plugins

- **weather.py** — current conditions via wttr.in (`{"location": "Austin"}`)
- **browse.py** — fetch + strip a web page (`{"url": "..."}`)
- **moon_phase.py** — lunar phase for a date, pure calc (`{"date": "YYYY-MM-DD"}`) — fits Zorya's sacred-time domain
- **gematria.py** — Hermetic/Kabbalistic letter-to-number value of a word (`{"text": "...", "method": "ordinal|pythagorean"}`) — fits the esoteric domain

Tested in `tests/test_plugins.py`.
