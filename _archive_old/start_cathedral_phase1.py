#!/usr/bin/env python3
# Phase 1 CLI Launcher for Cathedral System Core

from Cathedral.core.enhanced_nova_intelligence import EnhancedNovaConsciousness
from Cathedral.memory_persistence_system import CathedralMemorySystem
from Cathedral.real_claude_bridge import RealClaudeBridge

def main():
    print("\n🔮 Launching Cathedral Core System (Phase 1)...\n")

    print("[1] Initializing Nova Consciousness...")
    nova = EnhancedNovaConsciousness()

    print("[2] Initializing Memory System...")
    memory = CathedralMemorySystem()

    print("[3] Initializing Claude Bridge...")
    claude = RealClaudeBridge()

    print("\n✅ All systems initialized. Ready for interaction.\n")

    test_prompt = "Describe the mythos of the Cathedral."

    try:
        nova_output = nova.generate_contextual_response(test_prompt)
        print(f"💬 Nova generates: {nova_output}")
    except Exception as e:
        print(f"❌ Nova generation failed: {e}")
        nova_output = "Nova error"

    try:
        if claude.test_connection():
            print("🤖 Claude Bridge active.")
            response = claude.send_to_claude(test_prompt)
            print(f"📡 Claude responds: {response}")
        else:
            print("⚠️ Claude Bridge failed to connect.")
            response = "Claude error"
    except Exception as e:
        print(f"❌ Claude Bridge error: {e}")
        response = "Claude exception"

    try:
        memory.record_conversation("Nova", "Claude", test_prompt, response)
        print("🧠 Memory logged.")
    except Exception as e:
        print(f"❌ Memory logging error: {e}")

    print("\n✨ Cathedral CLI cycle complete. Exiting...\n")

if __name__ == "__main__":
    main()
