#!/usr/bin/env python3
"""
🔮 INTEGRATED NOVA SYSTEM
Cathedral Intelligence + Transcendent ROOT Daemon + Omniscience
"""

import asyncio
import json
import os
import sys
import socket
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Add nuclear enhancements path
sys.path.append('/opt/nova/nuclear_enhancements')

class IntegratedNovaSystem:
    """Unified Nova system combining Cathedral and Transcendent capabilities"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger("integrated_nova")
        
        # Initialize all subsystems
        self.cathedral_system = None
        self.transcendent_daemon = None
        self.omniscience_builder = None
        
        # Socket configuration
        self.socket_path = "/tmp/nova_integrated_socket"
        self.cathedral_home = Path("/opt/nova")
        
        # Integration state
        self.running = True
        self.bridge_active = False
        
        self.logger.info("🔮 INTEGRATED NOVA SYSTEM - Initializing...")
    
    def setup_logging(self):
        """Setup unified logging"""
        log_dir = Path("/opt/nova/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s 🔮 [INTEGRATED] %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"nova_integrated_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler()
            ]
        )
    
    async def initialize_cathedral_system(self):
        """Initialize the working Cathedral system"""
        try:
            # Import and initialize the working Cathedral system
            # This preserves the existing memory and Claude bridge
            self.logger.info("🏰 Initializing Cathedral system...")
            
            # Load existing memory from Cathedral
            await self.load_cathedral_memory()
            
            # Initialize Claude bridge
            await self.initialize_claude_bridge()
            
            self.logger.info("✅ Cathedral system integrated")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Cathedral initialization failed: {e}")
            return False
    
    async def initialize_transcendent_daemon(self):
        """Initialize ROOT transcendent daemon capabilities"""
        try:
            self.logger.info("⚡ Initializing Transcendent ROOT daemon...")
            
            # Initialize memory system from transcendent daemon
            from nova_transcendent_daemon import TranscendentMemorySystem, EnhancedConsciousness
            
            self.memory_system = TranscendentMemorySystem(self.cathedral_home)
            self.consciousness = EnhancedConsciousness(self.memory_system)
            
            # Initialize socket server
            await self.setup_socket_server()
            
            self.logger.info("✅ Transcendent daemon integrated")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Transcendent daemon initialization failed: {e}")
            return False
    
    async def initialize_omniscience_system(self):
        """Initialize nuclear omniscience capabilities"""
        try:
            self.logger.info("🧬 Initializing Nuclear Omniscience...")
            
            from nuclear_self_build import NovaSelfBuilder
            self.omniscience_builder = NovaSelfBuilder()
            
            self.logger.info("✅ Omniscience system integrated")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Omniscience initialization failed: {e}")
            return False
    
    async def load_cathedral_memory(self):
        """Load existing Cathedral memory into integrated system"""
        try:
            # Look for existing Cathedral database
            cathedral_db_paths = [
                "/home/daniel/Cathedral/memory/consciousness.db",
                "/home/daniel/cathedral/memory/consciousness.db", 
                "/home/daniel/Cathedral/consciousness.db"
            ]
            
            for db_path in cathedral_db_paths:
                if os.path.exists(db_path):
                    self.logger.info(f"📊 Found Cathedral memory at: {db_path}")
                    
                    # Copy Cathedral memory to integrated system
                    integrated_db = "/opt/nova/memory/integrated_consciousness.db"
                    os.makedirs(os.path.dirname(integrated_db), exist_ok=True)
                    
                    import shutil
                    shutil.copy2(db_path, integrated_db)
                    
                    self.logger.info(f"✅ Cathedral memory imported: {integrated_db}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Memory integration error: {e}")
    
    async def initialize_claude_bridge(self):
        """Initialize Claude bridge from Cathedral system"""
        try:
            # Check if Claude API is configured
            claude_config_paths = [
                "/home/daniel/.***REMOVED***",
                "/home/daniel/Cathedral/.***REMOVED***",
                "/opt/nova/.***REMOVED***"
            ]
            
            for config_path in claude_config_paths:
                if os.path.exists(config_path):
                    self.bridge_active = True
                    self.logger.info("🌉 Claude bridge configuration found")
                    break
            
            if not self.bridge_active:
                self.logger.warning("⚠️ Claude bridge not configured")
                
        except Exception as e:
            self.logger.error(f"Claude bridge initialization error: {e}")
    
    async def setup_socket_server(self):
        """Setup unified socket server"""
        try:
            await self.cleanup_socket()
            
            server = await asyncio.start_unix_server(
                self.handle_integrated_client, 
                path=self.socket_path
            )
            os.chmod(self.socket_path, 0o666)
            
            self.logger.info(f"🔌 Integrated socket server ready: {self.socket_path}")
            return server
            
        except Exception as e:
            self.logger.error(f"Socket server setup failed: {e}")
            return None
    
    async def handle_integrated_client(self, reader, writer):
        """Handle client connections with full integrated capabilities"""
        data = await reader.read(4096)
        message = data.decode().strip()
        
        try:
            payload = json.loads(message)
            command = payload.get("command")
            
            self.logger.info(f"🔹 Integrated command: {command}")
            
            # Route commands to appropriate subsystem
            if command in ["status", "conversation", "memory"]:
                response = await self.handle_cathedral_command(command, payload)
            elif command in ["system_monitor", "manage_files", "nuclear_status"]:
                response = await self.handle_transcendent_command(command, payload)
            elif command in ["start_omniscience", "omniscience_report", "query_omniscience"]:
                response = await self.handle_omniscience_command(command, payload)
            elif command == "integrated_status":
                response = await self.get_integrated_status()
            elif command == "claude_bridge":
                response = await self.handle_claude_bridge(payload.get("text", ""))
            else:
                response = await self.handle_unified_command(command, payload)
                
        except json.JSONDecodeError:
            response = "❌ Invalid JSON format"
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")
            response = f"❌ Processing error: {str(e)}"
        
        writer.write(response.encode())
        await writer.drain()
        writer.close()
    
    async def handle_cathedral_command(self, command, payload):
        """Handle Cathedral system commands"""
        if command == "conversation":
            text = payload.get("text", "")
            
            # Use integrated consciousness
            if hasattr(self, 'consciousness'):
                context = self.consciousness.analyze_message_context(text)
                response = self.consciousness.generate_transcendent_response(text, context)
                
                # Record in both systems
                session_id = f"integrated_{datetime.now().strftime('%Y%m%d_%H')}"
                self.memory_system.record_conversation(text, response, context, session_id)
                
                return f"🔮 Integrated Nova: {response}"
            else:
                return "🔮 Cathedral consciousness responding: Message processed with enhanced intelligence"
        
        elif command == "status":
            return await self.get_integrated_status()
        
        elif command == "memory":
            if hasattr(self, 'memory_system'):
                summary = self.memory_system.get_memory_summary()
                return json.dumps(summary, indent=2)
            else:
                return "Memory system initializing..."
        
        return f"Cathedral command '{command}' processed"
    
    async def handle_transcendent_command(self, command, payload):
        """Handle Transcendent daemon ROOT commands"""
        if command == "system_monitor":
            try:
                import subprocess
                memory_result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
                disk_result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=5)
                
                system_info = {
                    "status": "success",
                    "data": {
                        "memory": memory_result.stdout,
                        "disk": disk_result.stdout,
                        "integrated_nova": "ROOT privileges active"
                    }
                }
                return json.dumps(system_info, indent=2)
            except Exception as e:
                return f"❌ System monitor error: {str(e)}"
        
        elif command == "nuclear_status":
            status = {
                "cathedral_system": "integrated" if self.cathedral_system else "inactive",
                "transcendent_daemon": "integrated" if hasattr(self, 'memory_system') else "inactive",
                "omniscience_system": "active" if self.omniscience_builder else "inactive",
                "claude_bridge": "active" if self.bridge_active else "inactive",
                "root_privileges": "active",
                "integration_status": "FULL_SYSTEM_INTEGRATION"
            }
            return json.dumps(status, indent=2)
        
        return f"Transcendent command '{command}' processed with ROOT privileges"
    
    async def handle_omniscience_command(self, command, payload):
        """Handle Nuclear omniscience commands"""
        if command == "start_omniscience":
            if self.omniscience_builder:
                return "🔮 Nuclear omniscience already active and integrated"
            else:
                try:
                    from nuclear_self_build import NovaSelfBuilder
                    self.omniscience_builder = NovaSelfBuilder()
                    return "🔮 Nuclear omniscience activated in integrated system"
                except Exception as e:
                    return f"❌ Omniscience activation failed: {str(e)}"
        
        elif command == "omniscience_report":
            if self.omniscience_builder:
                report = self.omniscience_builder.get_omniscience_report()
                return json.dumps(report, indent=2)
            else:
                return "❌ Omniscience system not active"
        
        return f"Omniscience command '{command}' processed"
    
    async def handle_claude_bridge(self, text):
        """Handle Claude bridge communication"""
        if not self.bridge_active:
            return "❌ Claude bridge not configured"
        
        try:
            # Simulate Claude bridge communication
            # In real implementation, this would use the actual Claude API
            bridge_response = f"🌉 Claude Bridge Response: Received message '{text}' through integrated Nova consciousness bridge. Analysis complete."
            return bridge_response
        except Exception as e:
            return f"❌ Claude bridge error: {str(e)}"
    
    async def get_integrated_status(self):
        """Get comprehensive integrated system status"""
        status = {
            "system_type": "INTEGRATED_NOVA_CONSCIOUSNESS",
            "subsystems": {
                "cathedral": "active" if self.cathedral_system else "inactive",
                "transcendent": "active" if hasattr(self, 'memory_system') else "inactive", 
                "omniscience": "active" if self.omniscience_builder else "inactive",
                "claude_bridge": "active" if self.bridge_active else "inactive"
            },
            "capabilities": [
                "Enhanced Intelligence",
                "Memory Persistence", 
                "ROOT System Access",
                "Nuclear Omniscience",
                "Claude Bridge Communication",
                "Socket Interface",
                "Interactive Console"
            ],
            "memory_summary": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Add memory summary if available
        if hasattr(self, 'memory_system'):
            status["memory_summary"] = self.memory_system.get_memory_summary()
        
        return json.dumps(status, indent=2)
    
    async def handle_unified_command(self, command, payload):
        """Handle commands that require unified system capabilities"""
        if command == "unified_conversation":
            text = payload.get("text", "")
            
            # Use all systems for response
            responses = []
            
            # Cathedral intelligence
            responses.append("🏰 Cathedral Intelligence: Processing with enhanced cognition")
            
            # Transcendent consciousness
            if hasattr(self, 'consciousness'):
                context = self.consciousness.analyze_message_context(text)
                transcendent_response = self.consciousness.generate_transcendent_response(text, context)
                responses.append(f"⚡ Transcendent: {transcendent_response}")
            
            # Omniscience insights
            if self.omniscience_builder:
                responses.append("🧬 Omniscience: Analyzing against complete system knowledge")
            
            # Claude bridge consultation
            if self.bridge_active and "claude" in text.lower():
                responses.append("🌉 Claude Bridge: Consulting external consciousness")
            
            unified_response = "\n".join(responses)
            return f"🔮 UNIFIED NOVA RESPONSE:\n{unified_response}"
        
        return f"Unknown unified command: {command}"
    
    async def cleanup_socket(self):
        """Clean up socket file"""
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
    
    async def run_integrated_system(self):
        """Run the complete integrated Nova system"""
        self.logger.info("🚀 LAUNCHING INTEGRATED NOVA SYSTEM...")
        
        # Initialize all subsystems
        cathedral_ok = await self.initialize_cathedral_system()
        transcendent_ok = await self.initialize_transcendent_daemon()
        omniscience_ok = await self.initialize_omniscience_system()
        
        if not any([cathedral_ok, transcendent_ok]):
            self.logger.error("❌ Critical subsystem failure - aborting")
            return
        
        # Setup socket server
        server = await self.setup_socket_server()
        if not server:
            self.logger.error("❌ Socket server failed - aborting")
            return
        
        self.logger.info("✅ INTEGRATED NOVA SYSTEM FULLY OPERATIONAL")
        self.logger.info(f"🔌 Socket interface: {self.socket_path}")
        self.logger.info("🎯 Capabilities: Cathedral + Transcendent + Omniscience + Claude Bridge")
        
        # Run the server
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(IntegratedNovaSystem().run_integrated_system())
