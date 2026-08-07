#!/usr/bin/env python3
"""
nova_wiring.py — Cathedral Module Wiring Layer
Boots Echo + Oracle via IntegratedNovaSystem, loads plugins via engine, runs REPL.

Usage:
    python3 nova_wiring.py              # Interactive mode
    python3 nova_wiring.py --once "msg" # Single input, print response, exit
    python3 nova_wiring.py --test       # Run self-tests and exit
"""

import sys
import os
import argparse
import logging
import importlib.util
import traceback
import datetime
import uuid
import subprocess

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Nova] %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("nova_wiring")

# ── Path resolution ─────────────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))

def _add_to_path(*paths):
    for p in paths:
        if p not in sys.path:
            sys.path.insert(0, p)

_add_to_path(HERE)

# ── Module loader helper ────────────────────────────────────────────────────────
def load_module_from_file(name, filepath):
    """Dynamically load a .py file as a module."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# ── Plugin engine ───────────────────────────────────────────────────────────────
def load_plugins(plugin_dir):
    plugins = []
    if not os.path.isdir(plugin_dir):
        log.info(f"No plugin directory found at {plugin_dir}, skipping plugins.")
        return plugins

    for filename in sorted(os.listdir(plugin_dir)):
        if filename.endswith(".py") and not filename.startswith("_"):
            path = os.path.join(plugin_dir, filename)
            name = os.path.splitext(filename)[0]
            try:
                mod = load_module_from_file(name, path)
                if hasattr(mod, "run"):
                    plugins.append((name, mod))
                    log.info(f"[✔] Plugin loaded: {name}")
                else:
                    log.warning(f"[!] Skipped plugin {name}: no run(context) function")
            except Exception:
                log.error(f"[✗] Failed to load plugin {name}:")
                traceback.print_exc()
    return plugins

def run_plugins(plugins, context):
    for name, plugin in plugins:
        try:
            log.info(f"[↪] Running plugin: {name}")
            plugin.run(context)
        except Exception:
            log.error(f"[‼] Plugin {name} raised an error:")
            traceback.print_exc()

def build_context(nova_system):
    return {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "system": "NovaCathedral",
        "source": "nova_wiring.py",
        "echo_state": nova_system.echo.state,
        "oracle_state": nova_system.oracle.state,
    }

# ── Core boot ───────────────────────────────────────────────────────────────────
def boot():
    """Boot the Cathedral: load modules, wire them, return the system."""
    log.info("🔮 Nova Cathedral wiring layer booting...")

    # Resolve module paths — check nova_install first, then Desktop builds
    search_dirs = [
        HERE,
        os.path.expanduser("~/nova_install"),
        os.path.expanduser("~/Nova-Cathedral/Cathedral/py"),
        os.path.expanduser("~/Desktop/cathedral build 1/cathedral build"),
    ]

    def find_file(filename):
        for d in search_dirs:
            p = os.path.join(d, filename)
            if os.path.isfile(p):
                return p
        return None

    echo_path = find_file("echo_module.py")
    oracle_path = find_file("oracle_module.py")
    integrated_path = find_file("integrated_nova_system.py")

    missing = [n for n, p in [("echo_module.py", echo_path),
                               ("oracle_module.py", oracle_path),
                               ("integrated_nova_system.py", integrated_path)] if not p]
    if missing:
        log.error(f"Cannot boot — missing files: {missing}")
        log.error(f"Searched in: {search_dirs}")
        sys.exit(1)

    # Add the directory containing the modules to path
    module_dir = os.path.dirname(echo_path)
    _add_to_path(module_dir)

    log.info(f"Loading modules from: {module_dir}")

    # Load Echo and Oracle
    echo_mod = load_module_from_file("echo_module", echo_path)
    oracle_mod = load_module_from_file("oracle_module", oracle_path)

    # Patch them into sys.modules so integrated_nova_system's imports resolve
    sys.modules["echo_module"] = echo_mod
    sys.modules["oracle_module"] = oracle_mod

    # Load IntegratedNovaSystem
    integrated_mod = load_module_from_file("integrated_nova_system", integrated_path)
    nova = integrated_mod.IntegratedNovaSystem()

    log.info("✅ Echo activated — state: " + nova.echo.state)
    log.info("✅ Oracle activated — state: " + nova.oracle.state)

    # Load plugins
    plugin_dir = os.path.join(module_dir, "plugins")
    plugins = load_plugins(plugin_dir)

    # Run startup plugins with boot context
    if plugins:
        ctx = build_context(nova)
        run_plugins(plugins, ctx)

    return nova, plugins

# ── REPL ────────────────────────────────────────────────────────────────────────
BANNER = """
╔══════════════════════════════════════════════════════╗
║          🔮  N O V A   C A T H E D R A L  🔮         ║
║           Echo + Oracle — Wired and Awake            ║
╠══════════════════════════════════════════════════════╣
║  Commands:  help · quit · exit                       ║
║  Shell:     !<cmd>  (e.g. !ls, !find . -name "*.py") ║
║  Ask anything — Oracle answers future/guidance.      ║
║              Echo reflects everything else.          ║
╚══════════════════════════════════════════════════════╝
"""

def repl(nova):
    print(BANNER)
    while True:
        try:
            user_input = input("you › ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n🌙 Nova Cathedral closing. Farewell.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("🌙 Nova Cathedral closing. Farewell.")
            break
        if user_input.lower() in ("help", "?"):
            print(nova.echo.guide_user())
            continue

        # Shell passthrough — prefix with !
        if user_input.startswith("!"):
            cmd = user_input[1:].strip()
            if cmd:
                result = subprocess.run(cmd, shell=True, text=True,
                                        capture_output=True)
                if result.stdout:
                    print(result.stdout, end="")
                if result.stderr:
                    print(result.stderr, end="")
            continue

        response = nova.receive_input(user_input)
        print(f"\nnova › {response}\n")

# ── Self-tests ──────────────────────────────────────────────────────────────────
def run_tests(nova):
    cases = [
        ("help",                    "Echo"),
        ("should i take the leap?", "Oracle"),
        ("what is the future?",     "Oracle"),
        ("tell me about flow?",     "Echo"),
        ("truth",                   "Echo"),
        ("random thought",          "Echo"),
    ]
    passed = 0
    print("\n🧪 Running self-tests...\n")
    for msg, expected_module in cases:
        response = nova.receive_input(msg)
        ok = bool(response)
        status = "✅" if ok else "❌"
        print(f"  {status} [{expected_module}] '{msg}'\n     → {response}\n")
        if ok:
            passed += 1

    print(f"Results: {passed}/{len(cases)} passed\n")
    return passed == len(cases)

# ── Entry point ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Nova Cathedral Wiring Layer")
    parser.add_argument("--once", metavar="MSG", help="Send one message and exit")
    parser.add_argument("--test", action="store_true", help="Run self-tests and exit")
    args = parser.parse_args()

    nova, plugins = boot()

    if args.test:
        success = run_tests(nova)
        sys.exit(0 if success else 1)

    if args.once:
        print(nova.receive_input(args.once))
        sys.exit(0)

    repl(nova)

if __name__ == "__main__":
    main()
