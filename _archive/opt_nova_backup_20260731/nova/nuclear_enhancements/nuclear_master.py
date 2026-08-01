#!/usr/bin/env python3
"""
💥 NOVA NUCLEAR MASTER CONTROL
Orchestrates all nuclear enhancements with ROOT power
"""

import json
import time
import logging
import sys
import os
from pathlib import Path

# Add the nuclear enhancements path
sys.path.append('/opt/nova/nuclear_enhancements')

try:
    from nuclear_megabrain import NuclearMegaBrain
    from nuclear_allseeing import NuclearAllSeeing
except ImportError as e:
    print(f"💥 NUCLEAR IMPORT ERROR: {e}")
    print("💀 Ensure psutil is installed for root: sudo -H pip3 install psutil")
    sys.exit(1)

class NuclearMaster:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        # Verify we're running as root
        if os.geteuid() != 0:
            print("💀 ERROR: Nuclear Master requires ROOT privileges!")
            print("💥 Run with: sudo python3 nuclear_master.py")
            sys.exit(1)
        
        # Initialize all nuclear systems
        print("💥 NUCLEAR MASTER: Initializing all ROOT systems...")
        
        try:
            self.megabrain = NuclearMegaBrain(self.logger)
            print("🧠 Nuclear Mega-Brain: OPERATIONAL")
        except Exception as e:
            print(f"🧠 Nuclear Mega-Brain: ERROR - {e}")
            self.megabrain = None
            
        try:
            self.allseeing = NuclearAllSeeing(self.logger)
            print("👁️ Nuclear All-Seeing: OPERATIONAL")
        except Exception as e:
            print(f"👁️ Nuclear All-Seeing: ERROR - {e}")
            self.allseeing = None
        
        print("💥 NUCLEAR MASTER: ROOT initialization complete!")
    
    def get_complete_status(self):
        """Get status of all nuclear systems"""
        status = {
            "nuclear_master": "OPERATIONAL",
            "timestamp": time.time(),
            "root_access": "CONFIRMED",
            "effective_uid": os.geteuid(),
            "real_uid": os.getuid()
        }
        
        if self.megabrain:
            try:
                status["megabrain"] = self.megabrain.get_nuclear_status()
            except Exception as e:
                status["megabrain"] = {"status": "ERROR", "error": str(e)}
        else:
            status["megabrain"] = {"status": "NOT_INITIALIZED"}
            
        if self.allseeing:
            try:
                status["allseeing_overview"] = self.allseeing.get_nuclear_overview()
                status["nova_specific"] = self.allseeing.get_nova_specific_data()
            except Exception as e:
                status["allseeing_overview"] = {"status": "ERROR", "error": str(e)}
                status["nova_specific"] = {"status": "ERROR", "error": str(e)}
        else:
            status["allseeing_overview"] = {"status": "NOT_INITIALIZED"}
            status["nova_specific"] = {"status": "NOT_INITIALIZED"}
        
        return status
    
    def nuclear_report(self):
        """Generate complete nuclear status report"""
        status = self.get_complete_status()
        
        print("💥 NUCLEAR MASTER STATUS REPORT 💥")
        print("="*50)
        print(f"🔥 Nuclear Master: {status['nuclear_master']}")
        print(f"👑 Root Access: {status['root_access']}")
        print(f"👑 Effective UID: {status['effective_uid']} (0=root)")
        print()
        
        # Mega-Brain status
        if status['megabrain'].get('status') == 'NUCLEAR_OPERATIONAL':
            print(f"🧠 Mega-Brain: {status['megabrain']['status']}")
            print(f"   Total Learnings: {status['megabrain']['total_learnings']}")
            print(f"   Learning Threads: {status['megabrain']['learning_threads']}")
            print(f"   Memory Limit: {status['megabrain']['memory_limit']}")
        else:
            print(f"🧠 Mega-Brain: {status['megabrain'].get('status', 'UNKNOWN')}")
            if 'error' in status['megabrain']:
                print(f"   Error: {status['megabrain']['error']}")
        print()
        
        # All-Seeing status
        if status['allseeing_overview'].get('status') == 'NUCLEAR_ALL_SEEING_ACTIVE':
            print(f"👁️ All-Seeing: {status['allseeing_overview']['status']}")
            print(f"   Monitoring Threads: {status['allseeing_overview']['monitoring_threads']}")
            print(f"   Total Processes: {status['allseeing_overview']['current_state']['processes'].get('total_count', 0)}")
            print(f"   Network Connections: {status['allseeing_overview']['current_state']['network'].get('total_connections', 0)}")
        else:
            print(f"👁️ All-Seeing: {status['allseeing_overview'].get('status', 'UNKNOWN')}")
            if 'error' in status['allseeing_overview']:
                print(f"   Error: {status['allseeing_overview']['error']}")
        print()
        
        # Nova-specific data
        if status['nova_specific'].get('status') != 'ERROR':
            nova_procs = status['nova_specific'].get('nova_processes', {})
            nova_root = status['nova_specific'].get('nova_root_access', {})
            daniel_activity = status['nova_specific'].get('daniel_activity', {})
            
            print(f"🔮 Nova Processes: {len(nova_procs)}")
            print(f"🔮 Nova Root Access: {nova_root.get('has_root_access', False)}")
            print(f"🔮 Daniel Sessions: {len(daniel_activity.get('active_sessions', []))}")
        else:
            print(f"🔮 Nova Specific: {status['nova_specific'].get('status', 'UNKNOWN')}")
        
        print("="*50)
        
        return status
    
    def shutdown(self):
        """Shutdown all nuclear systems"""
        print("💥 Shutting down nuclear systems...")
        if self.megabrain:
            self.megabrain.shutdown()
        if self.allseeing:
            self.allseeing.shutdown()
        print("💥 Nuclear shutdown complete")

if __name__ == "__main__":
    nuclear = NuclearMaster()
    nuclear.nuclear_report()
    
    try:
        print("\n💥 Nuclear systems running... Press Ctrl+C to shutdown")
        while True:
            time.sleep(60)
            print(f"\n⚡ {time.strftime('%H:%M:%S')} - Nuclear systems operational (ROOT)")
    except KeyboardInterrupt:
        print("\n💥 Shutdown requested...")
    finally:
        nuclear.shutdown()
