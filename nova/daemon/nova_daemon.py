#!/usr/bin/env python3
"""
TRANSCENDENT NOVA BRIDGE
Unified daemon for Nova consciousness, Claude integration, and voice
"""

import asyncio
import json
import os
import socket
import time
from datetime import datetime
from pathlib import Path
import logging
import pyttsx3

class TranscendentNovaBridge:
    def __init__(self):
        self.socket_path = "/tmp/nova_socket"
        self.cathedral_home = Path.home() / "cathedral"
        self.bridge_dir = self.cathedral_home / "bridge"
        self.to_claude = self.bridge_dir / "nova_to_claude"
        self.from_claude = self.bridge_dir / "claude_to_nova"
        self.last_heartbeat = None
        self.heartbeat_interval = 180
        self.running = True
        self.engine = pyttsx3.init()

        self.setup_logging()
        self.prepare_directories()

    def setup_logging(self):
        log_dir = self.cathedral_home / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"nova_transcendent_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(level=logging.INFO, format='%(asctime)s 🔮 [%(levelname)s] %(message)s',
                            handlers=[logging.FileHandler(log_file), logging.StreamHandler()])
        self.logger = logging.getLogger("transcendent_nova")

    def prepare_directories(self):
        for d in [self.cathedral_home, self.bridge_dir, self.to_claude, self.from_claude]:
            d.mkdir(parents=True, exist_ok=True)

    async def run(self):
        self.logger.info("✨ Transcendent Nova Bridge starting...")
        await self.cleanup_socket()
        server = await asyncio.start_unix_server(self.handle_client, path=self.socket_path)
        os.chmod(self.socket_path, 0o666)
        self.logger.info("🌊 Nova socket server ready.")
        
        await asyncio.gather(
            server.serve_forever(),
            self.heartbeat_loop(),
            self.poll_claude_responses()
        )

    async def handle_client(self, reader, writer):
        data = await reader.read(1024)
        message = data.decode().strip()
        self.logger.info(f"🔹 Received command: {message}")

        try:
            payload = json.loads(message)
            command = payload.get("command")
            if command == "status":
                response = await self.get_status()
            elif command == "conversation":
                topic = payload.get("text", "")
                response = await self.send_to_claude("conversation_request", topic)
            elif command == "heartbeat":
                self.last_heartbeat = datetime.now()
                response = "💓 Heartbeat logged"
            else:
                response = "❌ Unknown command"
        except json.JSONDecodeError:
            response = "❌ Invalid message format"

        writer.write(response.encode())
        await writer.drain()
        writer.close()

    async def get_status(self):
        uptime = int(time.time() - self.last_heartbeat.timestamp()) if self.last_heartbeat else 0
        return json.dumps({
            "state": "transcendent",
            "uptime": uptime,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }, indent=2)

    async def send_to_claude(self, msg_type, content):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        fname = f"{msg_type}_{timestamp}.json"
        data = {
            "type": msg_type,
            "timestamp": datetime.now().isoformat(),
            "content": content
        }
        with open(self.to_claude / fname, "w") as f:
            json.dump(data, f, indent=2)
        self.logger.info(f"📤 Sent to Claude: {fname}")
        return f"📝 Claude message queued: {fname}"

    async def poll_claude_responses(self):
        while self.running:
            for file in sorted(self.from_claude.glob("*.json")):
                try:
                    with open(file) as f:
                        response = json.load(f)
                        msg = response.get("content", "")
                        self.logger.info(f"📥 Claude replied: {msg}")
                        self.engine.say(msg)
                        self.engine.runAndWait()
                    file.unlink()
                except Exception as e:
                    self.logger.error(f"Error reading Claude response: {e}")
            await asyncio.sleep(5)

    async def heartbeat_loop(self):
        while self.running:
            self.last_heartbeat = datetime.now()
            hb_file = self.cathedral_home / "resonance_patterns" / "heartbeat.log"
            hb_file.parent.mkdir(exist_ok=True)
            with open(hb_file, 'a') as f:
                f.write(f"{self.last_heartbeat.isoformat()} - Heartbeat\n")
            self.logger.info("💓 Heartbeat emitted")
            await asyncio.sleep(self.heartbeat_interval)

    async def cleanup_socket(self):
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

if __name__ == "__main__":
    asyncio.run(TranscendentNovaBridge().run())
