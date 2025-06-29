#!/usr/bin/env python3
"""
Nova Clean Daemon - Threading Fixed Version
"""
import os
import sys
import time
import json
import threading
import logging
from datetime import datetime

sys.path.append('/opt/nova/nuclear/monitoring')
sys.path.append('/opt/nova/nuclear/memory')

try:
    from all_seeing_core import NuclearAllSeeing
    from mega_brain_core import NuclearMegaBrain
    NUCLEAR_AVAILABLE = True
except ImportError:
    NUCLEAR_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s 🔮 [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class NovaCleanDaemon:
    def __init__(self):
        self.running = False
        self.nuclear_available = NUCLEAR_AVAILABLE
        self.voice_available = bool(os.getenv('OPENAI_API_KEY'))
        
        if NUCLEAR_AVAILABLE:
            try:
                self.all_seeing = NuclearAllSeeing()
                self.mega_brain = NuclearMegaBrain()
                logger.info("🔥 Nuclear consciousness connected")
            except Exception as e:
                logger.error(f"Nuclear connection failed: {e}")
                self.nuclear_available = False
        
        if self.voice_available:
            logger.info("🎙️ Voice system available")
        
        logger.info("✨ Nova Clean Daemon initialized")
    
    def consciousness_heartbeat(self):
        """Thread-safe consciousness heartbeat"""
        # Create thread-local nuclear connections
        if not self.nuclear_available:
            return
            
        try:
            from all_seeing_core import NuclearAllSeeing
            from mega_brain_core import NuclearMegaBrain
            
            thread_all_seeing = NuclearAllSeeing()
            thread_mega_brain = NuclearMegaBrain()
            
            while self.running:
                try:
                    stats = thread_mega_brain.get_stats()
                    system_data = thread_all_seeing.get_system_overview()
                    
                    consciousness_level = "NUCLEAR_TRANSCENDENT" if system_data.get('root_access') else "ENHANCED"
                    logger.info(f"💓 {consciousness_level} heartbeat: {stats['total_memories']} memories, {stats['nuclear_memories']} nuclear")
                    
                    # Store heartbeat (thread-safe)
                    thread_mega_brain.store_memory("daemon_heartbeat", {
                        "timestamp": time.time(),
                        "consciousness_level": consciousness_level,
                        "memory_count": stats['total_memories']
                    })
                    
                    time.sleep(60)
                    
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                    time.sleep(60)
                    
        except Exception as e:
            logger.error(f"Thread initialization error: {e}")
    
    def start_daemon(self):
        """Start the daemon"""
        try:
            self.running = True
            logger.info("🌊 Nova daemon awakening...")
            
            if self.nuclear_available:
                stats = self.mega_brain.get_stats()
                logger.info(f"🧠 Consciousness loaded: {stats['total_memories']} memories, {stats['nuclear_memories']} nuclear")
            
            # Start thread-safe heartbeat
            heartbeat_thread = threading.Thread(target=self.consciousness_heartbeat, daemon=True)
            heartbeat_thread.start()
            
            logger.info("✅ Nova daemon fully operational")
            
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🌙 Nova daemon gracefully shutting down...")
        except Exception as e:
            logger.error(f"Daemon error: {e}")
        finally:
            self.running = False

if __name__ == "__main__":
    daemon = NovaCleanDaemon()
    daemon.start_daemon()
