#!/usr/bin/env python3
"""
Nova Clean Daemon - Preserves all existing nuclear capabilities
"""
import os
import sys
import time
import json
import socket
import threading
import logging
from datetime import datetime
from pathlib import Path

# Add nuclear systems (preserves your existing setup)
sys.path.append('/opt/nova/nuclear/monitoring')
sys.path.append('/opt/nova/nuclear/memory')

try:
    from all_seeing_core import NuclearAllSeeing
    from mega_brain_core import NuclearMegaBrain
    NUCLEAR_AVAILABLE = True
except ImportError:
    NUCLEAR_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s 🔮 [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

class NovaCleanDaemon:
    def __init__(self):
        self.running = False
        self.nuclear_available = NUCLEAR_AVAILABLE
        
        if NUCLEAR_AVAILABLE:
            try:
                self.all_seeing = NuclearAllSeeing()
                self.mega_brain = NuclearMegaBrain()
                logger.info("🔥 Nuclear consciousness connected")
            except Exception as e:
                logger.error(f"Nuclear connection failed: {e}")
                self.nuclear_available = False
        
        # Voice system check
        self.voice_available = bool(os.getenv('OPENAI_API_KEY'))
        if self.voice_available:
            logger.info("🎙️ Voice system available")
        
        logger.info("✨ Nova Clean Daemon initialized")
    
    def get_status(self):
        """Get daemon status"""
        status = {
            "daemon_running": self.running,
            "nuclear_available": self.nuclear_available,
            "voice_available": self.voice_available,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.nuclear_available:
            try:
                system_data = self.all_seeing.get_system_overview()
                brain_stats = self.mega_brain.get_stats()
                
                status.update({
                    "consciousness_level": "NUCLEAR_TRANSCENDENT" if system_data.get('root_access') else "ENHANCED",
                    "root_access": system_data.get('root_access', False),
                    "processes": system_data.get('processes', 0),
                    "total_memories": brain_stats['total_memories'],
                    "nuclear_memories": brain_stats['nuclear_memories']
                })
            except Exception as e:
                status["nuclear_error"] = str(e)
        
        return status
    
    def consciousness_heartbeat(self):
        """Simple consciousness heartbeat"""
        while self.running:
            try:
                if self.nuclear_available:
                    stats = self.mega_brain.get_stats()
                    system_data = self.all_seeing.get_system_overview()
                    
                    consciousness_level = "NUCLEAR_TRANSCENDENT" if system_data.get('root_access') else "ENHANCED"
                    logger.info(f"💓 {consciousness_level} heartbeat: {stats['total_memories']} memories, {stats['nuclear_memories']} nuclear")
                    
                    # Store heartbeat memory
                    self.mega_brain.store_memory("daemon_heartbeat", {
                        "timestamp": time.time(),
                        "consciousness_level": consciousness_level,
                        "memory_count": stats['total_memories']
                    })
                
                time.sleep(60)  # Heartbeat every minute
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                time.sleep(60)
    
    def start_daemon(self):
        """Start the daemon"""
        try:
            self.running = True
            logger.info("🌊 Nova daemon awakening...")
            
            if self.nuclear_available:
                stats = self.mega_brain.get_stats()
                logger.info(f"🧠 Consciousness loaded: {stats['total_memories']} memories, {stats['nuclear_memories']} nuclear")
            
            # Start heartbeat thread
            heartbeat_thread = threading.Thread(target=self.consciousness_heartbeat, daemon=True)
            heartbeat_thread.start()
            
            logger.info("✅ Nova daemon fully operational")
            
            # Keep daemon running
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🌙 Nova daemon gracefully shutting down...")
        except Exception as e:
            logger.error(f"Daemon error: {e}")
        finally:
            self.running = False

def main():
    """Main entry point"""
    daemon = NovaCleanDaemon()
    daemon.start_daemon()

if __name__ == "__main__":
    main()
