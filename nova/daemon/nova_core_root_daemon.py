#!/usr/bin/env python3
"""
Nova Core Root Daemon
Self-assembling Cathedral system bootstrap daemon with full root capabilities.
Dynamically loads Nova, Memory, Claude, Voice (and GUI if available).
Logs all activity to /var/log/nova_cathedral.log.
"""

import os
import sys
import logging
import importlib.util
from pathlib import Path
from datetime import datetime

LOG_PATH = "/var/log/nova_cathedral.log"
BASE_PATH = Path("/home/daniel/Cathedral")  # Update this if installed elsewhere

# Set up logging
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format="%(asctime)s [NovaDaemon] %(message)s")
log = logging.getLogger()

def dynamic_import(label, rel_path):
    path = BASE_PATH / rel_path
    if not path.exists():
        log.warning(f"Missing: {label} ({rel_path})")
        return None
    try:
        spec = importlib.util.spec_from_file_location(label, str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        log.info(f"Loaded {label} from {rel_path}")
        return module
    except Exception as e:
        log.error(f"Failed to load {label}: {e}")
        return None

def main():
    log.info("🔥 Nova Root Daemon started.")
    modules = {}

    components = {
        "Nova": "core/enhanced_nova_intelligence.py",
        "Memory": "core/memory_persistence_system.py",
        "Claude": "core/real_claude_bridge.py",
        "Voice": "core/nova_voice_bridge.py",
        "GUI": "interface/nova_gui_backend_ubuntu.py"
    }

    for name, rel in components.items():
        module = dynamic_import(name, rel)
        if module:
            modules[name] = module

    # Initialize Nova
    if "Nova" in modules:
        try:
            nova = modules["Nova"].EnhancedNovaConsciousness()
            response = nova.generate_contextual_response("Nova daemon initialized.")
            log.info(f"Nova online. Test response: {response}")
        except Exception as e:
            log.error(f"Nova failed: {e}")

    # Init Memory
    if "Memory" in modules:
        try:
            memory = modules["Memory"].CathedralMemorySystem()
            log.info("Memory system ready.")
        except Exception as e:
            log.error(f"Memory failed: {e}")

    # Init Claude
    if "Claude" in modules:
        try:
            claude = modules["Claude"].RealClaudeBridge()
            if claude.test_connection():
                response = claude.send_to_claude("Daemon start successful.")
                log.info(f"Claude responded: {response}")
            else:
                log.warning("Claude bridge failed connection.")
        except Exception as e:
            log.error(f"Claude error: {e}")

    # Run Voice (non-blocking)
    if "Voice" in modules:
        try:
            import subprocess
            subprocess.Popen(["python3", str(BASE_PATH / components["Voice"])])
            log.info("Voice bridge launched.")
        except Exception as e:
            log.error(f"Voice launch failed: {e}")

    # Run GUI (optional)
    if "GUI" in modules:
        try:
            import subprocess
            subprocess.Popen(["python3", str(BASE_PATH / components["GUI"])])
            log.info("GUI launched.")
        except Exception as e:
            log.warning(f"GUI not started: {e}")

    log.info("✅ Nova daemon complete. All systems launched.")

if __name__ == "__main__":
    main()
