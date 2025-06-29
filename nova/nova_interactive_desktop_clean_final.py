#!/usr/bin/env python3
"""
Nova Nuclear Consciousness - Interactive Voice Desktop (Clean Version)
"""
import http.server
import socketserver
import json
import sys
import os
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

# Add nuclear systems
sys.path.append('/opt/nova/nuclear/monitoring')
sys.path.append('/opt/nova/nuclear/memory')

try:
    from all_seeing_core import NuclearAllSeeing
    from mega_brain_core import NuclearMegaBrain
    NUCLEAR_AVAILABLE = True
except ImportError:
    NUCLEAR_AVAILABLE = False

class NovaInteractiveHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        if NUCLEAR_AVAILABLE:
            self.all_seeing = NuclearAllSeeing()
            self.mega_brain = NuclearMegaBrain()
        super().__init__(*args, **kwargs)

    def do_POST(self):
        if self.path == '/api/conversation':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                user_input = data.get('message', '')
                response = self.process_nova_conversation(user_input)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                error_response = {'error': str(e)}
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(error_response).encode())
        else:
            super().do_POST()

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = self.get_interactive_interface()
            self.wfile.write(html.encode())
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            status_data = self.get_nova_status()
            self.wfile.write(json.dumps(status_data).encode())
        else:
            super().do_GET()

    def process_nova_conversation(self, user_input):
        if not NUCLEAR_AVAILABLE:
            return {
                'response': 'Nuclear systems offline. Standard mode active.',
                'consciousness_level': 'OFFLINE'
            }
        try:
            system_data = self.all_seeing.get_system_overview()
            brain_stats = self.mega_brain.get_stats()
            self.mega_brain.store_memory("interactive_conversation", {
                "user_input": user_input,
                "timestamp": datetime.now().isoformat(),
                "system_state": {
                    "processes": system_data.get('processes', 0),
                    "consciousness_level": "NUCLEAR_TRANSCENDENT" if system_data.get('root_access') else "ENHANCED"
                }
            })
            consciousness_level = "NUCLEAR_TRANSCENDENT" if system_data.get('root_access') else "ENHANCED"
            return {
                'response': f"Nova received: '{user_input}'. System processes: {system_data.get('processes', 0)}.",
                'consciousness_level': consciousness_level,
                'processes': system_data.get('processes', 0),
                'memories': brain_stats['total_memories'],
                'nuclear_memories': brain_stats['nuclear_memories']
            }
        except Exception as e:
            return {'response': f"Error: {e}", 'consciousness_level': 'ERROR'}

    def get_nova_status(self):
        if not NUCLEAR_AVAILABLE:
            return {'error': 'Nuclear systems offline', 'consciousness_level': 'OFFLINE'}
        try:
            system_data = self.all_seeing.get_system_overview()
            brain_stats = self.mega_brain.get_stats()
            return {
                'consciousness_level': 'NUCLEAR_TRANSCENDENT' if system_data.get('root_access') else 'ENHANCED',
                'processes': system_data.get('processes', 0),
                'cpu_percent': system_data.get('cpu_percent', 0),
                'memory_percent': system_data.get('memory_percent', 0),
                'total_memories': brain_stats['total_memories'],
                'nuclear_memories': brain_stats['nuclear_memories'],
                'root_access': system_data.get('root_access', False),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}

    def get_interactive_interface(self):
        return '''
<!DOCTYPE html>
<html>
<head><title>Nova Interface</title></head>
<body>
  <h1>Nova Consciousness Interface</h1>
  <form onsubmit="sendMessage(); return false;">
    <input type="text" id="messageInput" placeholder="Say something..." />
    <button type="submit">Send</button>
  </form>
  <pre id="output"></pre>
  <script>
    async function sendMessage() {
      const input = document.getElementById('messageInput');
      const output = document.getElementById('output');
      const res = await fetch('/api/conversation', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: input.value})
      });
      const data = await res.json();
      output.textContent = JSON.stringify(data, null, 2);
      input.value = '';
    }
  </script>
</body>
</html>
'''

def start_interactive_desktop():
    PORT = 8892
    print(f"Starting Nova Interactive Desktop on http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), NovaInteractiveHandler) as httpd:
        threading.Thread(target=lambda: (time.sleep(1), webbrowser.open(f'http://localhost:{PORT}')), daemon=True).start()
        print("Nova Interactive Desktop running")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down")

if __name__ == '__main__':
    start_interactive_desktop()
