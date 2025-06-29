#!/usr/bin/env python3
"""
Nova Bootstrap Daemon
Self-constructing Cathedral system daemon that:
- Scans for required modules (Nova, Memory, Claude)
- Dynamically imports them
- Initializes all systems
- Logs status and handles fallback gracefully
"""

import os
import importlib.util
from pathlib import Path

REQUIRED_MODULES = {
    "Nova": "core/enhanced_nova_intelligence.py",
    "Memory": "core/memory_persistence_system.py",
    "Claude": "core/real_claude_bridge.py"
}

def dynamic_import(name, path):
    full_path = Path(path).resolve()
    if not full_path.exists():
        print(f"❌ Missing module: {name} ({path})")
        return None

    spec = importlib.util.spec_from_file_location(name, str(full_path))
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        print(f"✅ Loaded {name} from {path}")
        return module
    except Exception as e:
        print(f"❌ Failed to load {name}: {e}")
        return None

def main():
    print("\n🌀 Nova Bootstrap Daemon Initializing...\n")
    base = Path(__file__).parent

    modules = {}
    for key, rel_path in REQUIRED_MODULES.items():
        module = dynamic_import(key, base / rel_path)
        if module:
            modules[key] = module

    if "Nova" in modules:
        try:
            nova = modules["Nova"].EnhancedNovaConsciousness()
            print("🧠 Nova Consciousness initialized.")
            print("🗨️  Sample Response:", nova.generate_contextual_response("Hello, Nova"))
        except Exception as e:
            print(f"❌ Nova failed to initialize: {e}")

    if "Memory" in modules:
        try:
            memory = modules["Memory"].CathedralMemorySystem()
            print("📚 Memory System initialized.")
        except Exception as e:
            print(f"❌ Memory failed to initialize: {e}")

    if "Claude" in modules:
        try:
            claude = modules["Claude"].RealClaudeBridge()
            if claude.test_connection():
                print("📡 Claude Bridge active.")
                response = claude.send_to_claude("Hello, Claude.")
                print("🗨️  Claude says:", response)
            else:
                print("⚠️ Claude Bridge failed to connect.")
        except Exception as e:
            print(f"❌ Claude Bridge error: {e}")

    print("\n✨ Bootstrap complete. Cathedral Daemon is running.\n")

if __name__ == "__main__":
    main()
