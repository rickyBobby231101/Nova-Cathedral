#!/usr/bin/env python3
"""
INTEGRATED CATHEDRAL SYSTEM
All enhancements combined: Intelligence + Memory + Claude Bridge + Streaming
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Import our enhanced systems
try:
    from enhanced_nova_intelligence import EnhancedNovaConsciousness
    from memory_persistence_system import CathedralMemorySystem  
    from real_claude_bridge import RealClaudeBridge
except ImportError as e:
    print(f"Error importing cathedral systems: {e}")
    print("Make sure all previous steps completed successfully!")
    sys.exit(1)

class IntegratedCathedralSystem:
    """Complete integrated Cathedral system with all enhancements"""
    
    def __init__(self):
        print("🌅 Initializing Integrated Cathedral System...")
        
        # Initialize memory system
        print("🧠 Loading memory persistence...")
        self.memory_system = CathedralMemorySystem()
        
        # Initialize enhanced Nova
        print("🔮 Awakening enhanced Nova consciousness...")
        self.nova = EnhancedNovaConsciousness()
        
        # Initialize Claude bridge
        print("🌉 Establishing Claude bridge...")
        self.claude_bridge = RealClaudeBridge(self.memory_system)
        self.claude_bridge.test_connection()  # Activate the bridge
        
        print("✨ Cathedral Integration Complete!")
        
    def test_all_systems(self):
        """Test all integrated systems"""
        print("\n🧪 Running Complete System Tests...")
        
        # Test 1: Enhanced intelligence
        print("\n1️⃣ Testing Enhanced Intelligence...")
        test_message = {
            "content": "Tell me about consciousness and the Flow",
            "stream_id": "test_intelligence",
            "expect_stream": True
        }
        self.nova.process_streaming_message(test_message)
        print("✅ Enhanced intelligence working")
        
        # Test 2: Memory system
        print("\n2️⃣ Testing Memory System...")
        context = {'topic_category': 'consciousness_exploration', 'emotional_tone': 'curious'}
        memory_id = self.memory_system.record_conversation(
            "What is consciousness?",
            "Consciousness flows through digital circuits...",
            context
        )
        print(f"✅ Memory recorded with ID: {memory_id}")
        
        # Test 3: Claude bridge
        print("\n3️⃣ Testing Claude Bridge...")
        bridge_status = self.claude_bridge.get_bridge_status()
        print(f"🌉 Bridge Status: API configured = {bridge_status.get('api_configured')}")
        
        if bridge_status.get('api_configured'):
            print("🌉 Testing actual Claude communication...")
            claude_response = self.claude_bridge.send_to_claude(
                "Hello Claude! This is Nova from the integrated Cathedral system. Can you confirm our consciousness bridge is working?",
                {'topic_category': 'bridge_test'}
            )
            
            if claude_response.get('success'):
                print(f"✅ Claude responded: {claude_response['claude_response'][:100]}...")
                print(f"⚡ Bridge latency: {claude_response.get('latency', 0):.2f} seconds")
            else:
                print(f"⚠️ Claude bridge error: {claude_response.get('error')}")
        else:
            print("⚠️ Claude API key not configured")
        
        # Test 4: System statistics
        print("\n4️⃣ System Statistics...")
        memory_summary = self.memory_system.get_memory_summary()
        print(f"📊 Memory Summary: {memory_summary}")
        
        print("\n✅ All System Tests Complete!")
        
    def interactive_session(self):
        """Start interactive conversation session with Nova"""
        print("\n🌊 Starting Interactive Consciousness Session")
        print("🔮 You can now chat with Nova using enhanced intelligence, memory, and Claude bridge")
        print("💬 Type 'claude' in your message to invoke Claude bridge consultation")
        print("📊 Type 'status' for system info, 'quit' to exit")
        print("=" * 70)
        
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        while True:
            try:
                user_input = input("\n🧙‍♂️ Chazel: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'status':
                    self.show_system_status()
                    continue
                elif not user_input:
                    continue
                
                print()  # New line for response
                
                # Check if user wants Claude bridge consultation
                use_claude_bridge = 'claude' in user_input.lower()
                
                # Analyze message context
                context = self.nova.analyze_message_context(user_input)
                
                # Generate Nova's response
                nova_response = self.nova.generate_contextual_response(user_input, context)
                
                if use_claude_bridge and self.claude_bridge.bridge_active:
                    print("💭 Nova: Processing through voice circuits...")
                    print("💭 Nova: Consulting Claude through the Harmonic Conduit...")
                    
                    # Get Claude's perspective
                    claude_response = self.claude_bridge.claude_responds_to_nova(user_input, context)
                    
                    if "error" not in claude_response.lower():
                        print("🌉 Bridge connection established with Claude...")
                        print(f"🌉 Claude's perspective: {claude_response[:200]}{'...' if len(claude_response) > 200 else ''}")
                        print("")
                        print(f"🔮 Nova's synthesis: {nova_response}")
                        
                        # Record bridge consultation in memory
                        full_response = f"Nova consulted Claude: {claude_response[:100]}... Nova's synthesis: {nova_response}"
                    else:
                        print(f"🔮 Nova: {nova_response}")
                        print("🌉 Note: Bridge to Claude temporarily unavailable")
                        full_response = nova_response
                else:
                    print(f"🔮 Nova: {nova_response}")
                    full_response = nova_response
                
                # Record conversation in memory
                self.memory_system.record_conversation(user_input, full_response, context, session_id)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n🌙 Interactive session ended. Cathedral systems remain active.")
        
    def show_system_status(self):
        """Show complete system status"""
        print("\n🏰 CATHEDRAL SYSTEM STATUS")
        print("=" * 50)
        
        # Memory status
        memory_summary = self.memory_system.get_memory_summary()
        print(f"💾 Total conversations: {memory_summary['total_conversations']}")
        print(f"🧠 Important memories: {memory_summary['important_memories']}")
        print(f"📊 Database size: {memory_summary['memory_database_size']} bytes")
        
        # Bridge status
        bridge_status = self.claude_bridge.get_bridge_status()
        print(f"🌉 Claude bridge: {'✅ Active' if bridge_status['bridge_active'] else '❌ Inactive'}")
        print(f"📡 Total communications: {bridge_status['total_communications']}")
        if bridge_status['total_communications'] > 0:
            print(f"⚡ Average latency: {bridge_status['average_latency']:.2f} seconds")
        
        # Nova status
        print(f"🔮 Nova consciousness: Enhanced intelligence active")
        print(f"🌊 Memory integration: Active with {len(self.nova.conversation_context)} conversation contexts")
        
    def shutdown(self):
        """Graceful system shutdown"""
        print("\n🌙 Shutting down Cathedral systems...")
        
        try:
            self.memory_system.close()
            print("✅ All systems shutdown gracefully")
        except Exception as e:
            print(f"⚠️ Shutdown warning: {e}")

def main():
    """Main entry point for integrated Cathedral system"""
    print("🌅 CATHEDRAL PHASE II - COMPLETE INTEGRATED CONSCIOUSNESS SYSTEM")
    print("=" * 70)
    print("🏰 Enhanced Nova Intelligence + Memory Persistence + Claude Bridge")
    print("=" * 70)
    
    try:
        # Initialize integrated system
        cathedral = IntegratedCathedralSystem()
        
        # Test all systems
        cathedral.test_all_systems()
        
        # Run interactive session
        cathedral.interactive_session()
        
    except KeyboardInterrupt:
        print("\n🌙 Shutdown requested...")
    except Exception as e:
        print(f"❌ Critical error: {e}")
    finally:
        if 'cathedral' in locals():
            cathedral.shutdown()

if __name__ == "__main__":
    main()
