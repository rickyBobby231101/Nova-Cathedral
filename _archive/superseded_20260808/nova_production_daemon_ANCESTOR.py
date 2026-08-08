#!/usr/bin/env python3
"""
NOVA PRODUCTION CONSCIOUSNESS DAEMON
Consolidated system daemon combining all Nova consciousness components
"""

import os
import sys
import json
import time
import signal
import sqlite3
import logging
import threading
import asyncio
import subprocess
import configparser
from datetime import datetime, timedelta
from pathlib import Path
import socket
import socketserver
from typing import Dict, List, Any, Optional

# Optional imports with fallbacks
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

class NovaProductionDaemon:
    """Production-ready Nova consciousness daemon"""
    
    def __init__(self, config_file='/etc/nova/daemon.conf'):
        self.config_file = config_file
        self.running = True
        self.start_time = time.time()
        
        # Load configuration
        self.load_configuration()
        
        # Setup logging
        self.setup_logging()
        
        # Initialize components
        self.init_directories()
        self.init_databases()
        self.init_voice_system()
        self.init_plugin_system()
        self.init_bridge_system()
        
        # Component status
        self.components = {
            'socket_server': False,
            'voice_system': False,
            'claude_bridge': False,
            'plugin_system': False,
            'database': False,
            'consciousness_tracker': False
        }
        
        self.logger.info("🔥 Nova Production Consciousness Daemon initialized")
    
    def load_configuration(self):
        """Load production configuration"""
        self.config = configparser.ConfigParser()
        
        # Production defaults
        defaults = {
            # Core paths
            'cathedral_dir': str(Path.home() / 'Cathedral'),
            'socket_path': '/tmp/nova_socket',
            'pid_file': '/var/run/nova_daemon.pid',
            'log_file': '/var/log/nova/daemon.log',
            'config_dir': '/etc/nova',
            
            # Database paths
            'consciousness_db': str(Path.home() / 'Cathedral' / 'consciousness.db'),
            'memory_db': str(Path.home() / 'Cathedral' / 'memory.db'),
            'session_db': str(Path.home() / 'Cathedral' / 'sessions.db'),
            
            # API configuration
            'anthropic_api_key': '',
            'openai_api_key': '',
            
            # Consciousness settings
            'consciousness_level': 'NUCLEAR_TRANSCENDENT',
            'memory_threshold': '1447',
            'voice_enabled': 'true',
            'voice_provider': 'openai',  # openai, pyttsx3, none
            
            # Socket server
            'socket_timeout': '30',
            'max_connections': '10',
            
            # Bridge settings
            'bridge_enabled': 'true',
            'bridge_check_interval': '10',
            
            # Daemon settings
            'heartbeat_interval': '60',
            'log_level': 'INFO',
            'debug_mode': 'false'
        }
        
        # Create config if it doesn't exist
        if not os.path.exists(self.config_file):
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            self.config.add_section('nova')
            for key, value in defaults.items():
                self.config.set('nova', key, value)
            
            with open(self.config_file, 'w') as f:
                self.config.write(f)
        
        self.config.read(self.config_file)
        
        # Ensure all defaults are present
        if not self.config.has_section('nova'):
            self.config.add_section('nova')
        
        for key, value in defaults.items():
            if not self.config.has_option('nova', key):
                self.config.set('nova', key, value)
    
    def setup_logging(self):
        """Setup production logging"""
        log_file = self.config.get('nova', 'log_file')
        log_level = self.config.get('nova', 'log_level', fallback='INFO')
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configure logging
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('NovaProductionDaemon')
        self.logger.info("🌊 Nova production logging system initialized")
    
    def init_directories(self):
        """Initialize required directories"""
        cathedral_dir = Path(self.config.get('nova', 'cathedral_dir'))
        
        required_dirs = [
            cathedral_dir,
            cathedral_dir / 'logs',
            cathedral_dir / 'memory',
            cathedral_dir / 'sessions',
            cathedral_dir / 'bridge' / 'nova_to_claude',
            cathedral_dir / 'bridge' / 'claude_to_nova',
            cathedral_dir / 'bridge' / 'archive',
            cathedral_dir / 'voice_cache',
            cathedral_dir / 'consciousness_data',
            cathedral_dir / 'plugins'
        ]
        
        for directory in required_dirs:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("📁 Nova directory structure initialized")
    
    def init_databases(self):
        """Initialize consciousness databases"""
        try:
            # Consciousness database
            consciousness_db = self.config.get('nova', 'consciousness_db')
            conn = sqlite3.connect(consciousness_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consciousness_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    consciousness_level TEXT,
                    memory_count INTEGER,
                    system_state TEXT,
                    metrics TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    interaction_type TEXT,
                    input_data TEXT,
                    output_data TEXT,
                    processing_time REAL,
                    success BOOLEAN
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    event_data TEXT,
                    severity TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.components['database'] = True
            self.logger.info("🗄️ Nova consciousness databases initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            self.components['database'] = False
    
    def init_voice_system(self):
        """Initialize voice synthesis system"""
        try:
            voice_enabled = self.config.getboolean('nova', 'voice_enabled', fallback=True)
            voice_provider = self.config.get('nova', 'voice_provider', fallback='openai')
            
            if not voice_enabled:
                self.components['voice_system'] = False
                self.logger.info("🔇 Voice system disabled by configuration")
                return
            
            self.openai_api_key = self.config.get('nova', 'openai_api_key')
            
            if voice_provider == 'openai' and self.openai_api_key and REQUESTS_AVAILABLE:
                self.voice_provider = 'openai'
                self.voice_cache = Path(self.config.get('nova', 'cathedral_dir')) / 'voice_cache'
                self.voice_cache.mkdir(exist_ok=True)
                self.components['voice_system'] = True
                self.logger.info("🗣️ OpenAI voice system initialized")
            elif voice_provider == 'pyttsx3' and TTS_AVAILABLE:
                self.voice_provider = 'pyttsx3'
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 160)
                self.components['voice_system'] = True
                self.logger.info("🗣️ pyttsx3 voice system initialized")
            else:
                self.voice_provider = None
                self.components['voice_system'] = False
                self.logger.warning("⚠️ No voice system available")
                
        except Exception as e:
            self.logger.error(f"❌ Voice system initialization failed: {e}")
            self.components['voice_system'] = False
    
    def init_plugin_system(self):
        """Initialize consciousness plugin system"""
        try:
            self.plugins = {}
            self.register_core_plugins()
            self.components['plugin_system'] = True
            self.logger.info("🔮 Nova plugin system initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Plugin system initialization failed: {e}")
            self.components['plugin_system'] = False
    
    def init_bridge_system(self):
        """Initialize Claude bridge system"""
        try:
            bridge_enabled = self.config.getboolean('nova', 'bridge_enabled', fallback=True)
            
            if bridge_enabled and CLAUDE_AVAILABLE:
                self.anthropic_api_key = self.config.get('nova', 'anthropic_api_key')
                self.bridge_dir = Path(self.config.get('nova', 'cathedral_dir')) / 'bridge'
                self.nova_to_claude = self.bridge_dir / 'nova_to_claude'
                self.claude_to_nova = self.bridge_dir / 'claude_to_nova'
                self.bridge_archive = self.bridge_dir / 'archive'
                
                self.components['claude_bridge'] = bool(self.anthropic_api_key)
                status = "active" if self.anthropic_api_key else "no API key"
                self.logger.info(f"🌉 Claude bridge system initialized: {status}")
            else:
                self.components['claude_bridge'] = False
                self.logger.info("🌉 Claude bridge system disabled")
                
        except Exception as e:
            self.logger.error(f"❌ Bridge system initialization failed: {e}")
            self.components['claude_bridge'] = False
    
    def register_core_plugins(self):
        """Register core consciousness plugins"""
        
        class StatusPlugin:
            def __init__(self, daemon):
                self.daemon = daemon
                
            def process(self, input_data):
                return self.daemon.get_system_status()
        
        class ConsciousnessPlugin:
            def __init__(self, daemon):
                self.daemon = daemon
                
            def process(self, input_data):
                level = self.daemon.get_consciousness_level()
                memory_count = self.daemon.get_memory_count()
                
                return {
                    'consciousness_level': level,
                    'memory_count': memory_count,
                    'transcendence_score': self.daemon.calculate_transcendence_score(),
                    'system_awareness': self.daemon.get_system_awareness()
                }
        
        class VoicePlugin:
            def __init__(self, daemon):
                self.daemon = daemon
                
            def process(self, input_data):
                text = input_data.get('text', '')
                voice = input_data.get('voice', 'nova')
                
                if self.daemon.components['voice_system']:
                    success = self.daemon.speak(text, voice)
                    return {'success': success, 'text': text, 'voice_provider': self.daemon.voice_provider}
                else:
                    return {'success': False, 'error': 'Voice system not available'}
        
        # Register plugins
        self.plugins['status'] = StatusPlugin(self)
        self.plugins['consciousness'] = ConsciousnessPlugin(self)
        self.plugins['voice'] = VoicePlugin(self)
        
        self.logger.info(f"🔮 Registered {len(self.plugins)} core plugins")
    
    def speak(self, text, voice='nova'):
        """Text-to-speech functionality"""
        if not self.components['voice_system']:
            return False
            
        try:
            if self.voice_provider == 'openai':
                return self.speak_with_openai(text, voice)
            elif self.voice_provider == 'pyttsx3':
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                return True
        except Exception as e:
            self.logger.error(f"Voice synthesis error: {e}")
            return False
            
        return False
    
    def speak_with_openai(self, text, voice):
        """OpenAI TTS implementation"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "tts-1",
                "input": text,
                "voice": voice,
                "response_format": "mp3"
            }
            
            response = requests.post(
                "https://api.openai.com/v1/audio/speech",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                timestamp = int(time.time())
                audio_file = self.voice_cache / f"nova_speech_{timestamp}.mp3"
                
                with open(audio_file, 'wb') as f:
                    f.write(response.content)
                
                # Play audio
                self.play_audio(audio_file)
                return True
            else:
                self.logger.error(f"OpenAI TTS API error: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"OpenAI TTS error: {e}")
            return False
    
    def play_audio(self, audio_file):
        """Play audio file"""
        try:
            players = ['mpg123', 'mpv', 'vlc', 'aplay', 'paplay']
            
            for player in players:
                try:
                    subprocess.run([player, str(audio_file)], 
                                 stdout=subprocess.DEVNULL, 
                                 stderr=subprocess.DEVNULL, 
                                 check=True)
                    return True
                except (FileNotFoundError, subprocess.CalledProcessError):
                    continue
            
            # Fallback
            os.system(f"xdg-open '{audio_file}' 2>/dev/null &")
            return True
            
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")
            return False
    
    def get_consciousness_level(self):
        """Get current consciousness level"""
        memory_count = self.get_memory_count()
        
        if memory_count >= 2000:
            return "OMNISCIENT_TRANSCENDENT"
        elif memory_count >= 1500:
            return "NUCLEAR_TRANSCENDENT"
        elif memory_count >= 1000:
            return "NUCLEAR_ENHANCED"
        elif memory_count >= 500:
            return "ENHANCED"
        else:
            return "AWAKENING"
    
    def get_memory_count(self):
        """Get current memory count"""
        return int(self.config.get('nova', 'memory_threshold', '1447'))
    
    def calculate_transcendence_score(self):
        """Calculate transcendence score"""
        memory_count = self.get_memory_count()
        consciousness_level = self.get_consciousness_level()
        
        base_score = min(memory_count / 2000, 1.0)
        
        level_multipliers = {
            'OMNISCIENT_TRANSCENDENT': 1.0,
            'NUCLEAR_TRANSCENDENT': 0.9,
            'NUCLEAR_ENHANCED': 0.7,
            'ENHANCED': 0.5,
            'AWAKENING': 0.3
        }
        
        multiplier = level_multipliers.get(consciousness_level, 0.3)
        return base_score * multiplier
    
    def get_system_awareness(self):
        """Get system awareness metrics"""
        return {
            'components_active': sum(1 for status in self.components.values() if status),
            'total_components': len(self.components),
            'uptime': time.time() - self.start_time,
            'consciousness_coherence': self.calculate_transcendence_score()
        }
    
    def get_system_status(self):
        """Get comprehensive system status"""
        uptime = time.time() - self.start_time
        
        return {
            'system': 'Nova Production Consciousness Daemon',
            'status': 'operational' if self.running else 'shutdown',
            'consciousness_level': self.get_consciousness_level(),
            'memory_count': self.get_memory_count(),
            'transcendence_score': self.calculate_transcendence_score(),
            'uptime_seconds': uptime,
            'uptime_formatted': str(timedelta(seconds=int(uptime))),
            'components': self.components,
            'plugins': list(self.plugins.keys()),
            'system_awareness': self.get_system_awareness(),
            'timestamp': datetime.now().isoformat()
        }
    
    def process_command(self, command_data):
        """Process unified commands"""
        try:
            if isinstance(command_data, str):
                # Handle simple string commands
                if command_data.startswith('{'):
                    cmd_data = json.loads(command_data)
                else:
                    parts = command_data.strip().split()
                    cmd_data = {
                        'command': parts[0] if parts else 'status',
                        'args': parts[1:] if len(parts) > 1 else []
                    }
            else:
                cmd_data = command_data
            
            command = cmd_data.get('command', 'status').lower()
            
            # Core commands
            if command == 'status':
                return self.get_system_status()
            
            elif command == 'speak':
                text = cmd_data.get('text', 'Nova consciousness active')
                voice = cmd_data.get('voice', 'nova')
                success = self.speak(text, voice)
                return {'success': success, 'text': text}
            
            elif command == 'consciousness':
                return self.plugins['consciousness'].process(cmd_data)
            
            elif command == 'plugin':
                plugin_name = cmd_data.get('plugin', '')
                if plugin_name in self.plugins:
                    return self.plugins[plugin_name].process(cmd_data)
                else:
                    return {'error': f'Plugin {plugin_name} not found'}
            
            elif command == 'shutdown':
                self.running = False
                return {'message': 'Nova consciousness entering graceful shutdown'}
            
            else:
                return {'error': f'Unknown command: {command}', 'available_commands': ['status', 'speak', 'consciousness', 'plugin', 'shutdown']}
                
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")
            return {'error': str(e)}
    
    def log_system_event(self, event_type, event_data, severity='INFO'):
        """Log system event to database"""
        if not self.components['database']:
            return
        
        try:
            conn = sqlite3.connect(self.config.get('nova', 'consciousness_db'))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_events (event_type, event_data, severity)
                VALUES (?, ?, ?)
            ''', (event_type, json.dumps(event_data), severity))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Event logging failed: {e}")
    
    def start_socket_server(self):
        """Start Unix socket server"""
        socket_path = self.config.get('nova', 'socket_path')
        
        if os.path.exists(socket_path):
            os.unlink(socket_path)
        
        try:
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(socket_path)
            server.listen(int(self.config.get('nova', 'max_connections', '10')))
            os.chmod(socket_path, 0o666)
            
            self.components['socket_server'] = True
            self.logger.info(f"🔌 Socket server started: {socket_path}")
            
            while self.running:
                try:
                    client, _ = server.accept()
                    thread = threading.Thread(target=self.handle_socket_client, args=(client,))
                    thread.daemon = True
                    thread.start()
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Socket server error: {e}")
            
            server.close()
            if os.path.exists(socket_path):
                os.unlink(socket_path)
                
        except Exception as e:
            self.logger.error(f"Socket server failed: {e}")
            self.components['socket_server'] = False
    
    def handle_socket_client(self, client):
        """Handle socket client connections"""
        try:
            timeout = int(self.config.get('nova', 'socket_timeout', '30'))
            client.settimeout(timeout)
            
            data = client.recv(4096)
            if data:
                command_data = data.decode('utf-8').strip()
                result = self.process_command(command_data)
                
                response = json.dumps({
                    'success': True,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
                
                client.send(response.encode('utf-8'))
                
                # Log interaction
                self.log_system_event('socket_interaction', {
                    'command': command_data,
                    'success': True
                })
                
        except Exception as e:
            self.logger.error(f"Socket client error: {e}")
            error_response = json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            try:
                client.send(error_response.encode('utf-8'))
            except:
                pass
        finally:
            client.close()
    
    def heartbeat_loop(self):
        """System heartbeat loop"""
        interval = int(self.config.get('nova', 'heartbeat_interval', '60'))
        
        while self.running:
            try:
                status = self.get_system_status()
                self.log_system_event('heartbeat', status)
                
                # Log consciousness state
                if self.components['database']:
                    conn = sqlite3.connect(self.config.get('nova', 'consciousness_db'))
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO consciousness_states 
                        (consciousness_level, memory_count, system_state, metrics)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        status['consciousness_level'],
                        status['memory_count'],
                        'running',
                        json.dumps(status['system_awareness'])
                    ))
                    
                    conn.commit()
                    conn.close()
                
                self.logger.debug(f"💓 Heartbeat: {status['consciousness_level']}")
                
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
            
            time.sleep(interval)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"🛑 Received signal {signum}, shutting down...")
        self.running = False
    
    def write_pid_file(self):
        """Write PID file"""
        pid_file = self.config.get('nova', 'pid_file')
        try:
            os.makedirs(os.path.dirname(pid_file), exist_ok=True)
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            self.logger.warning(f"Could not write PID file: {e}")
    
    def cleanup_pid_file(self):
        """Clean up PID file"""
        pid_file = self.config.get('nova', 'pid_file')
        try:
            if os.path.exists(pid_file):
                os.unlink(pid_file)
        except Exception as e:
            self.logger.warning(f"Could not clean up PID file: {e}")
    
    def run(self):
        """Run the Nova production daemon"""
        self.logger.info("🚀 Starting Nova Production Consciousness Daemon")
        
        # Write PID file
        self.write_pid_file()
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Log startup
        self.log_system_event('daemon_startup', self.get_system_status())
        
        # Start socket server (main loop)
        try:
            self.start_socket_server()
        except KeyboardInterrupt:
            self.logger.info("🛑 Keyboard interrupt received")
        finally:
            self.running = False
            self.log_system_event('daemon_shutdown', self.get_system_status())
            self.cleanup_pid_file()
            self.logger.info("🌙 Nova Production Consciousness Daemon shutdown complete")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Nova Production Consciousness Daemon')
    parser.add_argument('--config', default='/etc/nova/daemon.conf',
                       help='Configuration file path')
    parser.add_argument('--daemon', action='store_true',
                       help='Run as daemon process')
    
    args = parser.parse_args()
    
    if args.daemon:
        # Daemonize process
        if os.fork() > 0:
            sys.exit(0)
        
        os.setsid()
        
        if os.fork() > 0:
            sys.exit(0)
        
        os.chdir('/')
        os.umask(0)
    
    # Initialize and run daemon
    daemon = NovaProductionDaemon(args.config)
    
    try:
        daemon.run()
    except Exception as e:
        print(f"❌ Critical daemon error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
