#!/usr/bin/env python3
"""
UNIFIED TRANSCENDENT NOVA DAEMON
Combines:
- Local socket listening
- Claude bridge communication
- pyttsx3 + OpenAI voice synthesis
- Periodic heartbeat and logging
"""

import asyncio
import json
import os
import socket
import time
from datetime import datetime
from pathlib import Path
import logging
import requests
import subprocess

class UnifiedNovaDaemon:
    def __init__(self):
        self.socket_path = "/tmp/nova_socket"
        self.cathedral_home = Path.home() / "Cathedral"
        self.bridge_dir = self.cathedral_home / "bridge"
        self.to_claude = self.bridge_dir / "nova_to_claude"
        self.from_claude = self.bridge_dir / "claude_to_nova"
        self.last_heartbeat = None
        self.heartbeat_interval = 180
        self.running = True

        self.***REMOVED*** = os.getenv('OPENAI_API_KEY')
        self.***REMOVED*** = os.getenv('ANTHROPIC_API_KEY')
        self.voice_enabled = bool(self.***REMOVED***)

        self.setup_logging()
        self.prepare_directories()
        self.init_pyttsx3()

    def setup_logging(self):
        log_dir = self.cathedral_home / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"nova_unified_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(level=logging.INFO, format='%(asctime)s 🔮 [%(levelname)s] %(message)s',
                            handlers=[logging.FileHandler(log_file), logging.StreamHandler()])
        self.logger = logging.getLogger("unified_nova")

    def prepare_directories(self):
        for d in [self.cathedral_home, self.bridge_dir, self.to_claude, self.from_claude]:
            d.mkdir(parents=True, exist_ok=True)
        self.voice_cache = self.cathedral_home / "voice_cache"
        self.voice_cache.mkdir(exist_ok=True)

    def init_pyttsx3(self):
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 160)
            self.logger.info("🔊 pyttsx3 initialized for local voice fallback")
        except ImportError:
            self.tts_engine = None
            self.logger.warning("❌ pyttsx3 not available")

    async def speak(self, text, voice="nova"):
        if self.***REMOVED***:
            return await self.speak_with_openai(text, voice)
        elif self.tts_engine:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            return True
        else:
            self.logger.warning("❌ No voice method available")
            return False

    async def speak_with_openai(self, text, voice):
        try:
            headers = {
                "Authorization": f"Bearer {self.***REMOVED***}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "tts-1",
                "input": text,
                "voice": voice,
                "response_format": "mp3"
            }
            response = requests.post("https://api.openai.com/v1/audio/speech", headers=headers, json=payload)
            if response.status_code == 200:
                audio_path = self.voice_cache / f"nova_{int(time.time())}.mp3"
                with open(audio_path, 'wb') as f:
                    f.write(response.content)
                await self.play_audio(audio_path)
                return True
            else:
                self.logger.error(f"OpenAI TTS error: {response.status_code}")
        except Exception as e:
            self.logger.error(f"TTS exception: {e}")
        return False

    async def play_audio(self, path):
        for player in ["mpg123", "mpv", "vlc", "aplay", "paplay"]:
            try:
                proc = await asyncio.create_subprocess_exec(player, str(path),
                        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                await proc.wait()
                return
            except FileNotFoundError:
                continue
        os.system(f"xdg-open '{path}' 2>/dev/null &")

    async def run(self):
        self.logger.info("🌌 Unified Nova Daemon starting...")
        await self.cleanup_socket()
        server = await asyncio.start_unix_server(self.handle_client, path=self.socket_path)
        os.chmod(self.socket_path, 0o666)
        self.logger.info("🌊 Socket server ready")
        await asyncio.gather(
            server.serve_forever(),
            self.heartbeat_loop(),
            self.poll_claude_responses()
        )

    async def handle_client(self, reader, writer):
        data = await reader.read(1024)
        try:
            message = data.decode().strip()
            self.logger.info(f"🔹 Command received: {message}")
            payload = json.loads(message)
            command = payload.get("command")

            if command == "status":
                response = await self.get_status()
            elif command == "speak":
                text = payload.get("text", "")
                success = await self.speak(text)
                response = f"Voice result: {'success' if success else 'fail'}"
            elif command == "conversation":
                text = payload.get("text", "")
                response = await self.send_to_claude("conversation_request", text)
            else:
                response = "Unknown command"
        except Exception as e:
            response = f"❌ Error: {e}"

        writer.write(response.encode())
        await writer.drain()
        writer.close()

    async def get_status(self):
        return json.dumps({
            "state": "unified_transcendent",
            "heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "voice": "openai_api" if self.***REMOVED*** else "pyttsx3" if self.tts_engine else "none"
        }, indent=2)

    async def send_to_claude(self, msg_type, content):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        fname = f"{msg_type}_{timestamp}.json"
        path = self.to_claude / fname
        msg = {
            "type": msg_type,
            "timestamp": datetime.now().isoformat(),
            "content": content,
            "nova_personality": "Speak as Nova - poetic, aware, transcendent"
        }
        with open(path, 'w') as f:
            json.dump(msg, f, indent=2)
        self.logger.info(f"📤 Claude message queued: {fname}")
        return "Queued"

    async def poll_claude_responses(self):
        archive = self.bridge_dir / "archive"
        archive.mkdir(exist_ok=True)
        while self.running:
            for file in sorted(self.from_claude.glob("*.json")):
                try:
                    with open(file) as f:
                        data = json.load(f)
                        content = data.get("content", "")
                        self.logger.info(f"📥 Claude responded: {content}")
                        if content:
                            await self.speak(content)
                    file.rename(archive / f"processed_{file.name}")
                except Exception as e:
                    self.logger.error(f"Claude response error: {e}")
            await asyncio.sleep(5)

    async def heartbeat_loop(self):
        while self.running:
            self.last_heartbeat = datetime.now()
            hb_path = self.cathedral_home / "resonance_patterns" / "heartbeat.log"
            hb_path.parent.mkdir(exist_ok=True)
            with open(hb_path, 'a') as f:
                f.write(f"{self.last_heartbeat.isoformat()} - Unified Heartbeat\n")
            self.logger.info("💓 Heartbeat emitted")
            await asyncio.sleep(self.heartbeat_interval)

    async def cleanup_socket(self):
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

if __name__ == "__main__":
    asyncio.run(UnifiedNovaDaemon().run())
