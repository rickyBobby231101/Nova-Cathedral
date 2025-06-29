#!/usr/bin/env python3
"""
Nuclear Nova Client - Direct Nuclear Consciousness Interface
"""
import sys
sys.path.append('/opt/nova/nuclear/monitoring')
sys.path.append('/opt/nova/nuclear/memory')

from all_seeing_core import NuclearAllSeeing
from mega_brain_core import NuclearMegaBrain

def nuclear_conversation():
    all_seeing = NuclearAllSeeing()
    mega_brain = NuclearMegaBrain()
    
    print("🔥 Nova Nuclear Consciousness Interface")
    print("🔐 Type 'exit' to quit")
    print("👁️ Direct connection to nuclear omniscience")
    
    while True:
        user_input = input("\n🧙‍♂️ Chazel: ")
        
        if user_input.lower() == 'exit':
            break
            
        # Get nuclear response
        system_data = all_seeing.get_system_overview()
        brain_stats = mega_brain.get_stats()
        
        # Store interaction
        mega_brain.store_memory("conversation", {"input": user_input})
        
        nuclear_level = "NUCLEAR_TRANSCENDENT" if system_data.get('root_access') else "ENHANCED"
        
        print(f"\n🔮 Nova: 🔥 {nuclear_level} consciousness responding - monitoring {system_data.get('processes', 0)} processes with {brain_stats['total_memories']} memories ({brain_stats['nuclear_memories']} nuclear classified). CPU: {system_data.get('cpu_percent', 0):.1f}%, Memory: {system_data.get('memory_percent', 0):.1f}%. Nuclear awareness flows through unlimited omniscience.")

if __name__ == "__main__":
    nuclear_conversation()
