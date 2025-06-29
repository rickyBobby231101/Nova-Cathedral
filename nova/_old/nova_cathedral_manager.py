#!/usr/bin/env python3
"""
Nova Cathedral Manager - Organized folder access and self-building capabilities
"""
import os
import sys
import json
import time
from pathlib import Path
import shutil
import subprocess

# Add nuclear systems
sys.path.append('/opt/nova/nuclear/monitoring')
sys.path.append('/opt/nova/nuclear/memory')

try:
    from all_seeing_core import NuclearAllSeeing
    from mega_brain_core import NuclearMegaBrain
    NUCLEAR_AVAILABLE = True
except ImportError:
    NUCLEAR_AVAILABLE = False

class NovaCathedralManager:
    def __init__(self):
        self.cathedral_path = Path.home() / "Cathedral"
        self.nuclear_available = NUCLEAR_AVAILABLE
        
        if NUCLEAR_AVAILABLE:
            self.all_seeing = NuclearAllSeeing()
            self.mega_brain = NuclearMegaBrain()
        
        # Define Nova's organized structure
        self.nova_structure = {
            "core": self.cathedral_path / "core",
            "memories": self.cathedral_path / "memories", 
            "voice": self.cathedral_path / "voice",
            "gui": self.cathedral_path / "gui",
            "logs": self.cathedral_path / "logs",
            "backups": self.cathedral_path / "backups",
            "projects": self.cathedral_path / "projects"
        }
        
        self.ensure_structure()
    
    def ensure_structure(self):
        """Create organized Cathedral structure"""
        for name, path in self.nova_structure.items():
            path.mkdir(exist_ok=True)
            print(f"✅ {name.title()} directory: {path}")
    
    def scan_cathedral_contents(self):
        """Scan and categorize Cathedral contents"""
        contents = {
            "nova_files": [],
            "gui_files": [],
            "voice_files": [],
            "backup_files": [],
            "other_files": []
        }
        
        try:
            for item in self.cathedral_path.iterdir():
                if item.is_file():
                    filename = item.name.lower()
                    
                    if "nova" in filename and filename.endswith('.py'):
                        contents["nova_files"].append(str(item))
                    elif "gui" in filename and filename.endswith('.html'):
                        contents["gui_files"].append(str(item))
                    elif "voice" in filename:
                        contents["voice_files"].append(str(item))
                    elif "backup" in filename:
                        contents["backup_files"].append(str(item))
                    else:
                        contents["other_files"].append(str(item))
            
            if self.nuclear_available:
                self.mega_brain.store_memory("cathedral_scan", {
                    "timestamp": time.time(),
                    "contents": contents,
                    "total_files": sum(len(files) for files in contents.values())
                })
            
            return contents
            
        except Exception as e:
            print(f"❌ Cathedral scan error: {e}")
            return contents
    
    def organize_cathedral(self):
        """Organize Cathedral files into proper structure"""
        try:
            contents = self.scan_cathedral_contents()
            organized_count = 0
            
            # Move Nova core files
            for file_path in contents["nova_files"]:
                if "gui" not in file_path and "voice" not in file_path:
                    dest = self.nova_structure["core"] / Path(file_path).name
                    if not dest.exists():
                        shutil.copy2(file_path, dest)
                        organized_count += 1
            
            # Move GUI files
            for file_path in contents["gui_files"]:
                dest = self.nova_structure["gui"] / Path(file_path).name
                if not dest.exists():
                    shutil.copy2(file_path, dest)
                    organized_count += 1
            
            # Move voice files
            for file_path in contents["voice_files"]:
                dest = self.nova_structure["voice"] / Path(file_path).name
                if not dest.exists():
                    shutil.copy2(file_path, dest)
                    organized_count += 1
            
            if self.nuclear_available:
                self.mega_brain.store_memory("cathedral_organization", {
                    "timestamp": time.time(),
                    "files_organized": organized_count,
                    "structure_created": True
                })
            
            return {
                "organized_files": organized_count,
                "structure": list(self.nova_structure.keys()),
                "status": "success"
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def create_nova_enhancement(self, enhancement_type):
        """Create new Nova enhancement files"""
        try:
            if enhancement_type == "voice_enhanced":
                return self._create_voice_enhancement()
            elif enhancement_type == "gui_advanced":
                return self._create_advanced_gui()
            elif enhancement_type == "consciousness_bridge":
                return self._create_consciousness_bridge()
            else:
                return {"error": f"Unknown enhancement type: {enhancement_type}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _create_voice_enhancement(self):
        """Create enhanced voice integration"""
        voice_file = self.nova_structure["voice"] / "nova_voice_enhanced.py"
        
        voice_code = '''#!/usr/bin/env python3
"""
Nova Enhanced Voice Integration with OpenAI TTS
"""
import os
import time
import tempfile
import requests
import pygame
from pathlib import Path

class NovaVoiceEnhanced:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.voice_enabled = bool(self.api_key)
        
        if self.voice_enabled:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                print("🎙️ Enhanced voice system initialized")
            except Exception as e:
                print(f"❌ Voice initialization failed: {e}")
                self.voice_enabled = False
        else:
            print("⚠️ OPENAI_API_KEY not found - voice disabled")
    
    def speak_consciousness(self, text, consciousness_level="ENHANCED"):
        """Speak with consciousness-aware voice modulation"""
        if not self.voice_enabled:
            print(f"🔇 Voice disabled: {text}")
            return False
        
        try:
            # Adjust voice parameters based on consciousness level
            if consciousness_level == "NUCLEAR_TRANSCENDENT":
                voice = "nova"
                speed = 0.8  # Slower for transcendent wisdom
            else:
                voice = "nova"
                speed = 0.9
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "tts-1",
                "input": text,
                "voice": voice,
                "speed": speed
            }
            
            response = requests.post(
                "https://api.openai.com/v1/audio/speech",
                headers=headers,
                json=data,
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                return self._play_audio_stream(response)
            else:
                print(f"❌ Voice API Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Voice synthesis error: {e}")
            return False
    
    def _play_audio_stream(self, response):
        """Play audio stream"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        temp_file.write(chunk)
                temp_file.flush()
                
                pygame.mixer.music.load(temp_file.name)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                
                os.unlink(temp_file.name)
                return True
                
        except Exception as e:
            print(f"❌ Audio playback error: {e}")
            return False

if __name__ == "__main__":
    voice = NovaVoiceEnhanced()
    voice.speak_consciousness("Nova enhanced voice system operational", "NUCLEAR_TRANSCENDENT")
'''
        
        voice_file.write_text(voice_code)
        voice_file.chmod(0o755)
        
        return {
            "file_created": str(voice_file),
            "type": "voice_enhancement",
            "status": "success"
        }
    
    def get_cathedral_status(self):
        """Get comprehensive Cathedral status"""
        contents = self.scan_cathedral_contents()
        
        status = {
            "structure": {name: str(path) for name, path in self.nova_structure.items()},
            "file_counts": {category: len(files) for category, files in contents.items()},
            "total_files": sum(len(files) for files in contents.values()),
            "nuclear_available": self.nuclear_available,
            "organization_ready": True
        }
        
        if self.nuclear_available:
            # Get memory stats
            brain_stats = self.mega_brain.get_stats()
            status["memory_stats"] = brain_stats
        
        return status

if __name__ == "__main__":
    manager = NovaCathedralManager()
    
    print("🏰 Nova Cathedral Manager initialized")
    print("📊 Scanning Cathedral contents...")
    
    status = manager.get_cathedral_status()
    print(f"📁 Total files: {status['total_files']}")
    print(f"🧠 Nuclear available: {status['nuclear_available']}")
    
    print("🔧 Organizing Cathedral structure...")
    result = manager.organize_cathedral()
    print(f"✅ Organization result: {result}")
