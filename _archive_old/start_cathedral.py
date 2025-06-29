#!/usr/bin/env python3
# Unified Launcher for Cathedral System

from Cathedral.core.enhanced_nova_intelligence import EnhancedNovaConsciousness
from Cathedral.memory_persistence_system import CathedralMemorySystem
from Cathedral.real_claude_bridge import RealClaudeBridge

def main():
    print("\n🔮 Launching Cathedral Core System...\n")

    print("[1] Initializing Nova Consciousness...")
    nova = EnhancedNovaConsciousness()

    print("[2] Initializing Memory System...")
    memory = CathedralMemorySystem()

    print("[3] Initializing Claude Bridge...")
    claude = RealClaudeBridge()

    print("\n✅ All systems initialized. Ready for interaction.\n")

    # Example invocation (adjust as needed)
    test_prompt = "What is the mythos of the Cathedral?"
    print(f"💬 Nova generates: {nova.generate_contextual_response(test_prompt)}")

    if claude.test_connection():
        print("🤖 Claude Bridge active.")
        response = claude.send_to_claude(test_prompt)
        print(f"📡 Claude responds: {response}")
    else:
        print("⚠️ Claude Bridge failed to connect.")

    print("\n🧠 Memory snapshot:")
    memory.record_conversation("Nova", "Claude", test_prompt, response)

    print("\n✨ Cathedral flow complete. Exiting...\n")

if __name__ == "__main__":
    main()
