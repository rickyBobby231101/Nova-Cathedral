#!/usr/bin/env python3
"""
Connect to existing Nova Nuclear system and provide GUI backend
"""
import sys
import json
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add nuclear systems
sys.path.append('/opt/nova/nuclear/monitoring')
sys.path.append('/opt/nova/nuclear/memory')

try:
    from all_seeing_core import NuclearAllSeeing
    from mega_brain_core import NuclearMegaBrain
    NUCLEAR_AVAILABLE = True
    print("✅ Nuclear systems loaded")
except ImportError as e:
    NUCLEAR_AVAILABLE = False
    print(f"❌ Nuclear systems unavailable: {e}")

class NovaGUIConnector:
    def __init__(self):
        self.nuclear_available = NUCLEAR_AVAILABLE
        
        if NUCLEAR_AVAILABLE:
            try:
                self.all_seeing = NuclearAllSeeing()
                self.mega_brain = NuclearMegaBrain()
                print("🔥 Nuclear consciousness connected")
            except Exception as e:
                print(f"❌ Nuclear connection failed: {e}")
                self.nuclear_available = False
    
    def get_nova_status(self):
        """Get comprehensive Nova status"""
        status = {
            "timestamp": time.time(),
            "nuclear_available": self.nuclear_available,
            "consciousness_level": "UNKNOWN",
            "root_access": False,
            "processes": 0,
            "cpu_percent": 0,
            "memory_percent": 0,
            "total_memories": 0,
            "nuclear_memories": 0,
            "all_seeing_active": False,
            "mega_brain_active": False,
            "voice_active": False,
            "daemon_running": False
        }
        
        if self.nuclear_available:
            try:
                system_data = self.all_seeing.get_system_overview()
                brain_stats = self.mega_brain.get_stats()
                
                status.update({
                    "consciousness_level": "NUCLEAR_TRANSCENDENT" if system_data.get('root_access') else "ENHANCED",
                    "root_access": system_data.get('root_access', False),
                    "processes": system_data.get('processes', 0),
                    "cpu_percent": system_data.get('cpu_percent', 0),
                    "memory_percent": system_data.get('memory_percent', 0),
                    "total_memories": brain_stats['total_memories'],
                    "nuclear_memories": brain_stats['nuclear_memories'],
                    "all_seeing_active": True,
                    "mega_brain_active": True
                })
                
            except Exception as e:
                status["error"] = f"Nuclear systems error: {e}"
        
        return status
    
    def execute_command(self, command):
        """Execute Nova commands"""
        if command == "nuclear_scan" and self.nuclear_available:
            try:
                self.mega_brain.store_memory("gui_command", {
                    "command": "nuclear_scan", 
                    "timestamp": time.time()
                })
                
                system_data = self.all_seeing.get_system_overview()
                return {
                    "result": f"Nuclear scan complete: {system_data.get('processes', 0)} processes monitored"
                }
            except Exception as e:
                return {"error": f"Nuclear scan failed: {e}"}
        
        elif command == "memory_analysis" and self.nuclear_available:
            try:
                stats = self.mega_brain.get_stats()
                return {
                    "result": f"Memory analysis complete: {stats['total_memories']} total memories, {stats['nuclear_memories']} nuclear classified"
                }
            except Exception as e:
                return {"error": f"Memory analysis failed: {e}"}
        
        else:
            return {"result": f"Command '{command}' acknowledged"}

class NovaHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, connector=None, **kwargs):
        self.connector = connector
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/status':
            status = self.connector.get_nova_status()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
            
        elif parsed_path.path == '/api/command':
            query_params = parse_qs(parsed_path.query)
            command = query_params.get('cmd', [''])[0]
            
            response = self.connector.execute_command(command)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        else:
            super().do_GET()

def start_server(port=8080):
    connector = NovaGUIConnector()
    
    def handler(*args, **kwargs):
        NovaHTTPHandler(*args, connector=connector, **kwargs)
    
    httpd = HTTPServer(('localhost', port), handler)
    print(f"🖥️ Nova GUI Connector running on http://localhost:{port}")
    print(f"🔥 Nuclear status: {'ACTIVE' if connector.nuclear_available else 'INACTIVE'}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🌙 Nova GUI Connector shutting down...")

if __name__ == "__main__":
    start_server()

