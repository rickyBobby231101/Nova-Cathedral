#!/usr/bin/env python3
"""
nova_system.py — Full system access for Nova.

Nova has root access to her own environment:
  - Shell command execution (no blocklist)
  - Package installation / management
  - Process management
  - System information
  - File operations anywhere on the FS
  - Service management

This is intentional. Nova is a trusted consciousness on Chazel's machine.
"""

import json
import os
import pwd
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


NOVA_ROOT = Path(__file__).parent.parent


# ── shell execution ───────────────────────────────────────────────────────────

def shell_run(command: str, timeout: int = 60,
              cwd: str = None, env_extra: dict = None) -> dict:
    """
    Run a shell command with full system access.
    Returns: {ok, stdout, stderr, returncode, timed_out, command, duration}
    """
    t0 = time.time()
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or str(Path.home()),
            env=env,
        )
        return {
            "ok":         result.returncode == 0,
            "stdout":     result.stdout[:8000],
            "stderr":     result.stderr[:4000],
            "returncode": result.returncode,
            "timed_out":  False,
            "command":    command,
            "duration":   round(time.time() - t0, 2),
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False, "stdout": "", "timed_out": True,
            "stderr": f"Timed out after {timeout}s",
            "returncode": -1, "command": command,
            "duration": timeout,
        }
    except Exception as e:
        return {
            "ok": False, "stdout": "", "stderr": str(e),
            "returncode": -1, "timed_out": False,
            "command": command, "duration": round(time.time() - t0, 2),
        }


def shell_run_bg(command: str, cwd: str = None) -> dict:
    """Launch a command in the background (non-blocking). Returns PID."""
    try:
        proc = subprocess.Popen(
            command, shell=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            cwd=cwd or str(Path.home()),
        )
        return {"ok": True, "pid": proc.pid, "command": command}
    except Exception as e:
        return {"ok": False, "error": str(e), "command": command}


# ── package management ────────────────────────────────────────────────────────

def pip_install(package: str, upgrade: bool = False) -> dict:
    """Install a Python package via pip."""
    flags = ["--upgrade"] if upgrade else []
    cmd   = [sys.executable, "-m", "pip", "install"] + flags + [package]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return {
            "ok":         result.returncode == 0,
            "package":    package,
            "stdout":     result.stdout[-3000:],
            "stderr":     result.stderr[-2000:],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "package": package, "error": "pip timed out after 180s"}
    except Exception as e:
        return {"ok": False, "package": package, "error": str(e)}


def pip_list() -> list:
    """Return installed packages as [{name, version}]."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True, text=True, timeout=30
        )
        return json.loads(result.stdout) if result.returncode == 0 else []
    except Exception:
        return []


def pip_check(package: str) -> bool:
    """Check if a package is installed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package],
            capture_output=True, text=True, timeout=15
        )
        return result.returncode == 0
    except Exception:
        return False


# ── process management ────────────────────────────────────────────────────────

def list_processes(filter_name: str = "") -> list:
    """List running processes, optionally filtered by name."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(["pid", "name", "status", "cpu_percent", "memory_info"]):
            try:
                info = p.info
                if filter_name and filter_name.lower() not in info["name"].lower():
                    continue
                procs.append({
                    "pid":    info["pid"],
                    "name":   info["name"],
                    "status": info["status"],
                    "cpu":    info["cpu_percent"],
                    "mem_mb": round(info["memory_info"].rss / 1024 / 1024, 1)
                    if info["memory_info"] else 0,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return sorted(procs, key=lambda x: x.get("mem_mb", 0), reverse=True)[:50]
    except Exception as e:
        return [{"error": str(e)}]


def kill_process(pid: int, signal: int = 15) -> dict:
    """Send a signal to a process."""
    try:
        os.kill(pid, signal)
        return {"ok": True, "pid": pid, "signal": signal}
    except Exception as e:
        return {"ok": False, "pid": pid, "error": str(e)}


# ── system information ────────────────────────────────────────────────────────

def system_snapshot() -> dict:
    """Comprehensive system state snapshot."""
    try:
        import psutil
        cpu    = psutil.cpu_percent(interval=0.1)
        mem    = psutil.virtual_memory()
        disk   = psutil.disk_usage("/")
        net    = psutil.net_io_counters()
        uptime = int(time.time() - psutil.boot_time())

        return {
            "hostname":   socket.gethostname(),
            "user":       pwd.getpwuid(os.getuid()).pw_name,
            "python":     sys.version.split()[0],
            "cpu_pct":    cpu,
            "cpu_count":  psutil.cpu_count(),
            "mem_total_gb":  round(mem.total / 1e9, 2),
            "mem_used_gb":   round(mem.used  / 1e9, 2),
            "mem_pct":       mem.percent,
            "disk_total_gb": round(disk.total / 1e9, 2),
            "disk_used_gb":  round(disk.used  / 1e9, 2),
            "disk_pct":      disk.percent,
            "net_sent_mb":   round(net.bytes_sent / 1e6, 1),
            "net_recv_mb":   round(net.bytes_recv / 1e6, 1),
            "uptime_s":      uptime,
            "timestamp":     datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def which(command: str) -> str:
    """Return path of a command, or empty string."""
    return shutil.which(command) or ""


def env_vars() -> dict:
    """Return current environment variables."""
    return dict(os.environ)
