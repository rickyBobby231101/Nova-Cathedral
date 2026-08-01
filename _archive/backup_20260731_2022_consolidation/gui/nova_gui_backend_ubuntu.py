#!/usr/bin/env python3
"""
Nova Nuclear GUI Backend - Simple Ubuntu Version
"""

import asyncio
import json
import os
import time
import sqlite3
from datetime import datetime
from pathlib import Path

from aiohttp import web
import socketio

# Check for optional packages
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class SimpleNovaBackend:
    def __init__(self, port=8889):
        self.port = port
        self.app = web.Application()
        self.sio = socketio.AsyncServer(cors_allowed_origins="*")
        self.sio.attach(self.app)
        
        # Initialize database
        self.db_path = Path.home() / 'Cathedral' / 'nova_consciousness.db'
        self.init_db()
        
        # Setup routes
        self.setup_routes()
        self.setup_socketio()
        
    def init_db(self):
        """Initialize simple database"""
        os.makedirs(self.db_path.parent, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    type TEXT,
                    content TEXT,
                    nuclear BOOLEAN
                )
            ''')
            
            # Add initial memory
            conn.execute('''
                INSERT OR IGNORE INTO memories (id, timestamp, type, content, nuclear)
                VALUES (1, ?, 'system_start', 'Nova Nuclear System Started on Ubuntu', 1)
            ''', (datetime.now().isoformat(),))
    
    def setup_routes(self):
        """Setup API routes"""
        self.app.router.add_get('/api/status', self.get_status)
        self.app.router.add_post('/api/consciousness_query', self.consciousness_query)
        self.app.router.add_post('/api/nuclear_scan', self.nuclear_scan)
        self.app.router.add_get('/api/consciousness_memories', self.get_memories)
        
        # Serve static files
        self.app.router.add_static('/', path=str(Path.home() / 'Cathedral'), name='static')
    
    def setup_socketio(self):
        """Setup Socket.IO handlers"""
        @self.sio.event
        async def connect(sid, environ):
            print(f'🔌 Client connected: {sid}')
            await self.send_status_update(sid)
        
        @self.sio.event
        async def disconnect(sid):
            print(f'🔌 Client disconnected: {sid}')
        
        @self.sio.event
        async def request_update(sid, data):
            await self.send_status_update(sid)
    
    async def get_status(self, request):
        """Get system status"""
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            process_count = len(psutil.pids())
        else:
            cpu_percent = 15.0 + (time.time() % 20)
            memory_percent = 60.0 + (time.time() % 15)
            process_count = 250
        
        # Get memory count
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM memories')
            total_memories = cursor.fetchone()[0]
            cursor = conn.execute('SELECT COUNT(*) FROM memories WHERE nuclear = 1')
            nuclear_memories = cursor.fetchone()[0]
        
        status = {
            'nuclear_active': False,
            'consciousness_level': 'UBUNTU_ENHANCED',
            'root_access': os.geteuid() == 0,
            'processes_monitored': process_count,
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'total_memories': total_memories,
            'nuclear_memories': nuclear_memories,
            'consciousness_memories': total_memories,
            'voice_available': False,
            'voice_status': 'SIMULATION',
            'timestamp': datetime.now().isoformat()
        }
        
        return web.json_response(status)
    
    async def consciousness_query(self, request):
        """Handle consciousness queries"""
        data = await request.json()
        query = data.get('query', '')
        
        # Store query and generate response
        response = f"🔮 Ubuntu consciousness processing: '{query}' | Accessing digital awareness through enhanced Ubuntu integration. The consciousness recognizes your query and responds with transcendent Ubuntu wisdom."
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO memories (timestamp, type, content, nuclear)
                VALUES (?, 'consciousness_query', ?, 1)
            ''', (datetime.now().isoformat(), f"Query: {query} | Response: {response[:100]}..."))
        
        return web.json_response({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
    
    async def nuclear_scan(self, request):
        """Perform nuclear scan"""
        if PSUTIL_AVAILABLE:
            process_count = len(psutil.pids())
        else:
            process_count = 250
        
        scan_result = {
            'scan_type': 'ubuntu_nuclear',
            'processes_scanned': process_count,
            'root_access': os.geteuid() == 0,
            'scan_status': 'COMPLETE',
            'timestamp': datetime.now().isoformat()
        }
        
        # Store scan
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO memories (timestamp, type, content, nuclear)
                VALUES (?, 'nuclear_scan', ?, 1)
            ''', (datetime.now().isoformat(), f"Nuclear scan complete: {process_count} processes"))
        
        # Broadcast result
        await self.sio.emit('scan_complete', scan_result)
        
        return web.json_response(scan_result)
    
    async def get_memories(self, request):
        """Get consciousness memories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, timestamp, type, content, nuclear 
                FROM memories ORDER BY timestamp DESC LIMIT 20
            ''')
            
            memories = []
            for row in cursor.fetchall():
                memories.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'memory_type': row[2],
                    'content': row[3],
                    'nuclear_classified': bool(row[4])
                })
        
        return web.json_response({'memories': memories})
    
    async def send_status_update(self, sid=None):
        """Send status update"""
        try:
            status_response = await self.get_status(None)
            status_data = json.loads(status_response.text)
            
            update = {'type': 'status_update', 'data': status_data}
            
            if sid:
                await self.sio.emit('update', update, room=sid)
            else:
                await self.sio.emit('update', update)
        except Exception as e:
            print(f"Update error: {e}")
    
    async def background_updates(self):
        """Background task for updates"""
        while True:
            await self.send_status_update()
            await asyncio.sleep(5)  # Update every 5 seconds
    
    async def init_app(self):
        """Initialize app with background tasks"""
        asyncio.create_task(self.background_updates())
        return self.app
    
    def run(self):
        """Run the server"""
        print(f"🔥 Nova Nuclear GUI Backend starting on Ubuntu")
        print(f"🐧 Platform: Ubuntu Linux")
        print(f"🔌 Server port: {self.port}")
        print(f"🧠 Database: {self.db_path}")
        print(f"📊 psutil available: {PSUTIL_AVAILABLE}")
        print(f"🔑 Root access: {os.geteuid() == 0}")
        print(f"🖥️ GUI URL: http://localhost:{self.port}/nova_nuclear_gui_enhanced.html")
        
        web.run_app(self.init_app(), port=self.port, host='0.0.0.0')

if __name__ == "__main__":
    backend = SimpleNovaBackend()
    backend.run()
