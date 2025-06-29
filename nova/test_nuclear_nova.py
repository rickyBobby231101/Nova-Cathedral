#!/usr/bin/env python3
"""
Test Nova with Nuclear Capabilities
"""
import sys
sys.path.append('/opt/nova/nuclear/monitoring')
sys.path.append('/opt/nova/nuclear/memory')

try:
    from all_seeing_core import NuclearAllSeeing
    from mega_brain_core import NuclearMegaBrain
    
    print("🔥 Testing Nuclear Nova Integration...")
    
    # Test All-Seeing
    all_seeing = NuclearAllSeeing()
    system_data = all_seeing.get_system_overview()
    
    # Test Mega-Brain  
    mega_brain = NuclearMegaBrain()
    brain_stats = mega_brain.get_stats()
    
    print(f"✅ Nuclear All-Seeing: {system_data.get('processes', 0)} processes")
    print(f"✅ Nuclear Mega-Brain: {brain_stats['total_memories']} memories")
    print(f"🔐 Root Access: {system_data.get('root_access', False)}")
    print(f"🔮 Consciousness Level: {'NUCLEAR_TRANSCENDENT' if system_data.get('root_access') else 'ENHANCED'}")
    
    print("\n🚀 NOVA NUCLEAR INTEGRATION: SUCCESS!")
    
except Exception as e:
    print(f"❌ Nuclear integration error: {e}")
    print("Nuclear systems may not be properly integrated")
