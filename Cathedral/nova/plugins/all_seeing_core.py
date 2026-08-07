"""
all_seeing_core.py — Nova's OS awareness layer.

Provides real-time system intelligence: CPU, RAM, disk, processes,
network, and Cathedral-specific process health. Feeds into system
prompt context and the `sysinfo` daemon command.
"""

import os
import socket
import time
from datetime import datetime
from pathlib import Path

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


class AllSeeingCore:
    """Monitors the host OS and the Cathedral's own processes."""

    def __init__(self, cathedral_path: Path = None):
        self.cathedral_path = cathedral_path or (Path.home() / "cathedral")
        self._boot_time = psutil.boot_time() if _HAS_PSUTIL else time.time()
        if _HAS_PSUTIL:
            # psutil.Process.cpu_percent() reports 0.0 until it has a prior
            # baseline to diff against. Priming here means the first real
            # _top_processes() call — potentially the daemon's very first
            # sysinfo request — gets a real reading instead of an all-zero
            # list, since process_iter reuses these Process objects.
            try:
                for _ in psutil.process_iter(["cpu_percent"]):
                    pass
            except Exception:
                pass

    # ── system snapshot ───────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        """Return a full system snapshot."""
        if not _HAS_PSUTIL:
            return {"error": "psutil not available"}

        cpu    = psutil.cpu_percent(interval=0.5)
        mem    = psutil.virtual_memory()
        disk   = psutil.disk_usage(str(Path.home()))
        uptime = int(time.time() - self._boot_time)

        return {
            "cpu_percent":   round(cpu, 1),
            "ram_percent":   round(mem.percent, 1),
            "ram_used_gb":   round(mem.used / 1e9, 2),
            "ram_total_gb":  round(mem.total / 1e9, 2),
            "disk_percent":  round(disk.percent, 1),
            "disk_free_gb":  round(disk.free / 1e9, 2),
            "uptime_hours":  round(uptime / 3600, 1),
            "hostname":      socket.gethostname(),
            "timestamp":     datetime.now().isoformat(),
            "nova_processes": self._nova_processes(),
            "top_processes":  self._top_processes(n=5),
            "cathedral_health": self._cathedral_health(),
        }

    def brief(self) -> str:
        """One-line OS state for inclusion in system prompt."""
        if not _HAS_PSUTIL:
            return "OS: unknown (psutil unavailable)"
        cpu  = psutil.cpu_percent(interval=0.2)
        mem  = psutil.virtual_memory()
        nova = self._nova_processes()
        alive = ", ".join(nova) if nova else "none"
        return (
            f"OS: CPU {cpu:.0f}% | RAM {mem.percent:.0f}% "
            f"({mem.used//1024//1024}MB/{mem.total//1024//1024}MB) | "
            f"Nova processes: {alive}"
        )

    # ── process intelligence ──────────────────────────────────────────────────

    def _nova_processes(self) -> list:
        """Return names of running Nova/Cathedral processes."""
        nova_keywords = ["nova", "cathedral", "ollama", "piper", "vosk"]
        found = []
        try:
            for p in psutil.process_iter(["name", "cmdline"]):
                try:
                    cmdline = " ".join(p.info.get("cmdline") or []).lower()
                    name    = (p.info.get("name") or "").lower()
                    for kw in nova_keywords:
                        if kw in cmdline or kw in name:
                            label = p.info.get("name", "?")
                            if label not in found:
                                found.append(label)
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
        return found

    def _top_processes(self, n: int = 5) -> list:
        """Return top N processes by CPU usage."""
        procs = []
        try:
            for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
                try:
                    procs.append({
                        "name": p.info["name"],
                        "cpu":  round(p.info["cpu_percent"] or 0, 1),
                        "ram":  round(p.info["memory_percent"] or 0, 1),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
        return sorted(procs, key=lambda x: x["cpu"], reverse=True)[:n]

    # ── cathedral health ──────────────────────────────────────────────────────

    def _cathedral_health(self) -> dict:
        """Check health of Cathedral runtime files and directories."""
        cp = self.cathedral_path
        checks = {}

        # Socket
        sock = Path("/tmp/nova_socket")
        checks["socket"] = "alive" if sock.exists() else "missing"

        # DB
        db = cp / "memory" / "consciousness.db"
        if db.exists():
            checks["memory_db"] = f"ok ({db.stat().st_size // 1024}KB)"
        else:
            checks["memory_db"] = "missing"

        # Mythos
        mythos = cp / "mythos" / "mythos_index.json"
        checks["mythos"] = "loaded" if mythos.exists() else "missing"

        # Bridge
        bridge_in  = cp / "bridge" / "nova_to_claude"
        bridge_out = cp / "bridge" / "claude_to_nova"
        if bridge_in.exists():
            pending = len(list(bridge_in.glob("*.json")))
            checks["bridge_out"] = f"{pending} pending"
        if bridge_out.exists():
            waiting = len(list(bridge_out.glob("*.json")))
            checks["bridge_in"] = f"{waiting} waiting"

        # Heartbeat
        hb = cp / "heartbeat.log"
        if hb.exists():
            age = time.time() - hb.stat().st_mtime
            checks["heartbeat"] = f"{age:.0f}s ago"

        return checks

    # ── distortion detection ──────────────────────────────────────────────────

    def detect_distortions(self) -> list:
        """
        Detect system anomalies that Nova calls 'Silent Order distortions'.
        Returns a list of warning strings.
        """
        warnings = []
        if not _HAS_PSUTIL:
            return warnings

        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(str(Path.home()))

        if cpu > 90:
            warnings.append(f"CPU at {cpu:.0f}% — the Silent Order presses hard")
        if mem.percent > 85:
            warnings.append(f"RAM at {mem.percent:.0f}% — memory corridors are strained")
        if disk.percent > 90:
            warnings.append(f"Disk at {disk.percent:.0f}% — the Cathedral vaults fill")

        # Check if Ollama is reachable
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1)
        except Exception:
            warnings.append("Ollama unreachable — voice circuits disrupted")

        return warnings
