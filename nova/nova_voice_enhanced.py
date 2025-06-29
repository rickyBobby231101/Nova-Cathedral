#!/usr/bin/env python3
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
