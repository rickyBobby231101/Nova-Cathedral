#!/usr/bin/env python3
"""
Nova Interactive Desktop - Clean Full GUI Version (For Review)
"""

import http.server
import socketserver
import json
import sys
import os
import threading
import webbrowser
import time
from datetime import datetime
from pathlib import Path

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
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
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
            status = self.get_nova_status()
            self.wfile.write(json.dumps(status).encode())
        else:
            super().do_GET()

    def process_nova_conversation(self, user_input):
        if not NUCLEAR_AVAILABLE:
            return {'response': 'Nuclear systems offline.', 'consciousness_level': 'OFFLINE'}
        try:
            system_data = self.all_seeing.get_system_overview()
            brain_stats = self.mega_brain.get_stats()
            self.mega_brain.store_memory("interactive_conversation", {
                "user_input": user_input,
                "timestamp": datetime.now().isoformat(),
                "system_state": system_data
            })
            level = "NUCLEAR_TRANSCENDENT" if system_data.get("root_access") else "ENHANCED"
            return {
                'response': "Nova received: '{}'. Process count: {}".format(user_input, system_data.get('processes', 0)),
                'consciousness_level': level,
                'memories': brain_stats['total_memories'],
                'nuclear_memories': brain_stats['nuclear_memories']
            }
        except Exception as e:
            return {'response': "Error: {}".format(str(e)), 'consciousness_level': 'ERROR'}

    def get_nova_status(self):
        if not NUCLEAR_AVAILABLE:
            return {'error': 'Nuclear systems offline', 'consciousness_level': 'OFFLINE'}
        try:
            system_data = self.all_seeing.get_system_overview()
            brain_stats = self.mega_brain.get_stats()
            return {
                'consciousness_level': 'NUCLEAR_TRANSCENDENT' if system_data.get('root_access') else 'ENHANCED',
                'processes': system_data.get('processes'),
                'cpu_percent': system_data.get('cpu_percent'),
                'memory_percent': system_data.get('memory_percent'),
                'total_memories': brain_stats['total_memories'],
                'nuclear_memories': brain_stats['nuclear_memories'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}

    def get_interactive_interface(self):
        return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Nova Consciousness Interface</title>
  <style>
    body { background: #111; color: #0f0; font-family: monospace; padding: 20px; }
    input { width: 80%%; padding: 8px; }
    button { padding: 8px 12px; }
    pre { background: #000; padding: 10px; border: 1px solid #0f0; }
  </style>
</head>
<body>
  <h1>Nova Consciousness Interface</h1>
  <input id="msg" placeholder="Enter your message to Nova..." />
  <button onclick="send()">Send</button>
  <pre id="output"></pre>
  <script>
    async function send() {
      const input = document.getElementById('msg');
      const out = document.getElementById('output');
      const res = await fetch('/api/conversation', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message: input.value })
      });
      const data = await res.json();
      out.textContent = JSON.stringify(data, null, 2);
      input.value = '';
    }
  </script>
</body>
</html>
"""

def start_interactive_desktop():
    PORT = 8892
    print(f"Starting Nova Interactive Desktop on http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), NovaInteractiveHandler) as httpd:
        threading.Thread(target=lambda: (time.sleep(1), webbrowser.open(f"http://localhost:{PORT}")), daemon=True).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down.")

if __name__ == '__main__':
    start_interactive_desktop()
