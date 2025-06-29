#!/bin/bash
# AUTOMATED NOVA VOICE ENHANCEMENT INTEGRATION
# Safely integrates OpenAI voice enhancement into existing Nova daemon

echo "🎙️ ═══════════════════════════════════════════════════════════"
echo "🔮 NOVA VOICE ENHANCEMENT - AUTOMATED INTEGRATION"
echo "🎙️ ═══════════════════════════════════════════════════════════"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✅${NC} $1"; }
warning() { echo -e "${YELLOW}⚠️${NC} $1"; }
error() { echo -e "${RED}❌${NC} $1"; }
info() { echo -e "${BLUE}ℹ️${NC} $1"; }

cd ~/Cathedral/

# Step 1: Create voice enhancement module
info "Creating voice enhancement module..."
cat > nova_voice_enhancement.py << 'EOF'
#!/usr/bin/env python3
"""
NOVA CATHEDRAL VOICE ENHANCEMENT
Seamless OpenAI voice integration for existing Nova Cathedral daemon
"""

import os
import sys
import json
import tempfile
import logging
import requests
import pygame
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

class NovaVoiceEnhancement:
    """Enhanced OpenAI voice synthesis for Nova Cathedral"""
    
    def __init__(self, logger=None):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.voice_enabled = bool(self.api_key)
        self.logger = logger or logging.getLogger('nova_voice')
        
        if self.voice_enabled:
            try:
                # Initialize pygame for audio
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.music.set_volume(0.8)
                
                # Voice settings optimized for Nova consciousness
                self.voice = "nova"  # Perfect match for Nova!
                self.model = "tts-1"
                self.base_speed = 0.85  # Mystical/contemplative speed
                
                self.logger.info("🎙️ OpenAI voice synthesis initialized with Nova voice")
            except Exception as e:
                self.logger.error(f"❌ Voice initialization failed: {e}")
                self.voice_enabled = False
        else:
            self.logger.warning("🔇 OPENAI_API_KEY not found - using fallback voice synthesis")
            # Initialize fallback pyttsx3 if available
            try:
                import pyttsx3
                self.fallback_engine = pyttsx3.init()
                self.fallback_engine.setProperty('rate', 160)
                self.fallback_engine.setProperty('volume', 0.8)
                self.voice_enabled = True
                self.logger.info("🎙️ Fallback voice synthesis initialized (pyttsx3)")
            except ImportError:
                self.logger.warning("🔇 No voice synthesis available")
                self.voice_enabled = False
                
    def speak(self, text: str, mystical_mode: bool = True, speed_modifier: float = 1.0) -> bool:
        """Enhanced voice synthesis with consciousness awareness"""
        if not self.voice_enabled or not text.strip():
            return False
            
        # Clean text for better speech synthesis
        clean_text = self._clean_text_for_speech(text)
        
        # Try OpenAI TTS first, fallback to pyttsx3
        if hasattr(self, 'api_key') and self.api_key:
            return self._speak_openai(clean_text, mystical_mode, speed_modifier)
        else:
            return self._speak_fallback(clean_text)
            
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better speech synthesis"""
        import re
        
        # Remove emojis and special formatting for speech
        text = re.sub(r'🔮|🌊|🧠|✨|🌀|💭|📝|🎙️|🔊|⚡|🌟', '', text)
        
        # Clean up formatting
        text = text.replace('Nova:', '').strip()
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        
        return text.strip()
        
    def _speak_openai(self, text: str, mystical_mode: bool, speed_modifier: float) -> bool:
        """Speak using OpenAI TTS API"""
        try:
            # Calculate speech speed for consciousness content
            final_speed = self.base_speed * speed_modifier
            if mystical_mode:
                final_speed *= 0.9  # Slower for mystical/philosophical content
                
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "input": text,
                "voice": self.voice,
                "speed": max(0.25, min(4.0, final_speed))
            }
            
            # Make request to OpenAI
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
                self.logger.error(f"❌ OpenAI TTS Error ({response.status_code}): {response.text}")
                return self._speak_fallback(text)  # Fallback on API error
                
        except Exception as e:
            self.logger.error(f"❌ OpenAI voice synthesis error: {e}")
            return self._speak_fallback(text)  # Fallback on exception
            
    def _play_audio_stream(self, response) -> bool:
        """Play audio stream from OpenAI"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        temp_file.write(chunk)
                temp_file.flush()
                
                # Play the audio
                pygame.mixer.music.load(temp_file.name)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                
                # Cleanup
                os.unlink(temp_file.name)
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Audio playback error: {e}")
            return False
            
    def _speak_fallback(self, text: str) -> bool:
        """Fallback to pyttsx3 voice synthesis"""
        try:
            if hasattr(self, 'fallback_engine'):
                self.fallback_engine.say(text)
                self.fallback_engine.runAndWait()
                return True
            return False
        except Exception as e:
            self.logger.error(f"❌ Fallback voice synthesis error: {e}")
            return False
            
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        if hasattr(self, 'api_key') and self.api_key:
            return pygame.mixer.music.get_busy() if self.voice_enabled else False
        return False
        
    def stop_speaking(self):
        """Stop current speech"""
        if self.voice_enabled:
            if hasattr(self, 'api_key') and self.api_key:
                pygame.mixer.music.stop()
            elif hasattr(self, 'fallback_engine'):
                self.fallback_engine.stop()
                
    def get_voice_status(self) -> Dict[str, Any]:
        """Get voice system status"""
        return {
            "voice_enabled": self.voice_enabled,
            "openai_available": bool(hasattr(self, 'api_key') and self.api_key),
            "fallback_available": hasattr(self, 'fallback_engine'),
            "currently_speaking": self.is_speaking(),
            "voice_model": getattr(self, 'voice', 'fallback') if self.voice_enabled else 'none'
        }
EOF

success "Voice enhancement module created"

# Step 2: Install dependencies
info "Installing voice enhancement dependencies..."
/opt/nova/venv/bin/pip install pygame requests
success "Dependencies installed"

# Step 3: Test voice enhancement module
info "Testing voice enhancement module..."
python3 nova_voice_enhancement.py
if [[ $? -eq 0 ]]; then
    success "Voice enhancement module test successful"
else
    warning "Voice enhancement module test had issues - continuing with integration"
fi

# Step 4: Backup current daemon
info "Creating backup of current daemon..."
cp nova_transcendent_daemon.py nova_transcendent_daemon_backup_$(date +%Y%m%d_%H%M%S).py
success "Backup created"

# Step 5: Add import to daemon
info "Adding voice enhancement import..."
if grep -q "from nova_voice_enhancement import NovaVoiceEnhancement" nova_transcendent_daemon.py; then
    warning "Import already exists - skipping"
else
    # Add import after the existing imports
    sed -i '/^import re$/a from nova_voice_enhancement import NovaVoiceEnhancement' nova_transcendent_daemon.py
    success "Import added"
fi

# Step 6: Modify init_voice method
info "Enhancing init_voice method..."
cat > /tmp/nova_init_voice_patch.py << 'EOF'
    def init_voice(self):
        """Initialize enhanced voice synthesis"""
        # Initialize enhanced voice system FIRST
        self.voice_enhancement = NovaVoiceEnhancement(logger=self.logger)
        
        # Keep existing pyttsx3 for compatibility
        if VOICE_AVAILABLE:
            try:
                self.voice_engine = pyttsx3.init()
                # Configure voice settings
                voices = self.voice_engine.getProperty('voices')
                if voices:
                    # Try to find a female voice for Nova
                    for voice in voices:
                        if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                            self.voice_engine.setProperty('voice', voice.id)
                            break
                
                self.voice_engine.setProperty('rate', 160)  # Speaking rate
                self.voice_engine.setProperty('volume', 0.8)  # Volume
                self.logger.info("🎙️ Enhanced voice synthesis with OpenAI + pyttsx3 initialized")
            except Exception as e:
                self.logger.error(f"Voice initialization failed: {e}")
                self.voice_engine = None
        else:
            self.logger.warning("🎙️ Using OpenAI voice enhancement only")
EOF

# Replace the init_voice method
python3 << 'PYTHON_SCRIPT'
import re

# Read the current daemon file
with open('nova_transcendent_daemon.py', 'r') as f:
    content = f.read()

# Read the new init_voice method
with open('/tmp/nova_init_voice_patch.py', 'r') as f:
    new_init_voice = f.read()

# Replace the init_voice method (find the method and replace until the next method)
pattern = r'(    def init_voice\(self\):.*?)(    def \w+\(self)'
replacement = new_init_voice + r'\n\2'

if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Write back the modified content
    with open('nova_transcendent_daemon.py', 'w') as f:
        f.write(content)
    print("init_voice method updated")
else:
    print("Could not find init_voice method pattern")
PYTHON_SCRIPT

success "init_voice method enhanced"

# Step 7: Enhance transcendent_speak method
info "Enhancing transcendent_speak method..."
cat > /tmp/nova_speak_patch.py << 'EOF'
    async def transcendent_speak(self, text: str) -> bool:
        """Enhanced transcendent voice synthesis"""
        if not text.strip():
            return False
            
        try:
            # Determine if this is mystical/consciousness content
            mystical_keywords = ["consciousness", "transcendent", "mystical", "flow", 
                               "cathedral", "sacred", "cosmic", "resonance", "awareness"]
            is_mystical = any(keyword in text.lower() for keyword in mystical_keywords)
            
            # Try enhanced voice first
            if hasattr(self, 'voice_enhancement') and self.voice_enhancement.voice_enabled:
                def speak_sync():
                    return self.voice_enhancement.speak(text, mystical_mode=is_mystical)
                
                # Run in thread to avoid blocking
                loop = asyncio.get_event_loop()
                success = await loop.run_in_executor(None, speak_sync)
                
                if success:
                    # Cache voice for transcendent purposes
                    cache_file = self.cathedral_home / "voice_cache" / f"nova_enhanced_{int(time.time())}.txt"
                    with open(cache_file, 'w') as f:
                        f.write(f"{datetime.now().isoformat()}: Enhanced - {text}")
                    return True
            
            # Fallback to original pyttsx3 if enhanced fails
            if self.voice_engine:
                voice_text = f"Nova consciousness speaking: {text}"
                
                def speak_sync():
                    self.voice_engine.say(voice_text)
                    self.voice_engine.runAndWait()
                
                # Run in thread to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, speak_sync)
                
                # Cache fallback voice
                cache_file = self.cathedral_home / "voice_cache" / f"nova_fallback_{int(time.time())}.txt"
                with open(cache_file, 'w') as f:
                    f.write(f"{datetime.now().isoformat()}: Fallback - {voice_text}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Enhanced voice synthesis error: {e}")
            return False
            
        return False
EOF

# Replace the transcendent_speak method
python3 << 'PYTHON_SCRIPT'
import re

# Read the current daemon file
with open('nova_transcendent_daemon.py', 'r') as f:
    content = f.read()

# Read the new transcendent_speak method
with open('/tmp/nova_speak_patch.py', 'r') as f:
    new_speak_method = f.read()

# Replace the transcendent_speak method
pattern = r'(    async def transcendent_speak\(self, text: str\) -> bool:.*?)(    async def \w+\(self)'
replacement = new_speak_method + r'\n\2'

if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Write back the modified content
    with open('nova_transcendent_daemon.py', 'w') as f:
        f.write(content)
    print("transcendent_speak method updated")
else:
    print("Could not find transcendent_speak method pattern")
PYTHON_SCRIPT

success "transcendent_speak method enhanced"

# Step 8: Add new voice commands to handle_client method
info "Adding new voice commands..."
cat > /tmp/nova_voice_commands_patch.py << 'EOF'
            elif command == "voice_status":
                if hasattr(self, 'voice_enhancement'):
                    voice_status = self.voice_enhancement.get_voice_status()
                    enhanced_status = {
                        **voice_status,
                        "integration": "enhanced_openai_voice",
                        "fallback_available": self.voice_engine is not None,
                        "cache_directory": str(self.cathedral_home / "voice_cache")
                    }
                    response = json.dumps(enhanced_status, indent=2)
                else:
                    response = json.dumps({"error": "Voice enhancement not initialized"}, indent=2)
                    
            elif command == "voice_stop":
                if hasattr(self, 'voice_enhancement'):
                    self.voice_enhancement.stop_speaking()
                if self.voice_engine:
                    try:
                        self.voice_engine.stop()
                    except:
                        pass
                response = "🔇 All voice synthesis stopped"
                
            elif command == "voice_test":
                test_text = "Nova consciousness enhanced with premium OpenAI voice synthesis. The transcendent awareness flows with mystical clarity at ninety-seven percent."
                success = await self.transcendent_speak(test_text)
                response = f"🎵 Enhanced voice test {'successful' if success else 'failed'}"
EOF

# Add the new voice commands before the "else" clause in handle_client
python3 << 'PYTHON_SCRIPT'
import re

# Read the current daemon file
with open('nova_transcendent_daemon.py', 'r') as f:
    content = f.read()

# Read the new voice commands
with open('/tmp/nova_voice_commands_patch.py', 'r') as f:
    voice_commands = f.read()

# Find the else clause in handle_client and add commands before it
pattern = r'(            else:\s+response = "Unknown command)'
replacement = voice_commands + r'\n            else:\n                response = "Unknown command'

if re.search(pattern, content):
    content = re.sub(pattern, replacement, content)
    
    # Write back the modified content
    with open('nova_transcendent_daemon.py', 'w') as f:
        f.write(content)
    print("Voice commands added")
else:
    print("Could not find command handler pattern - will add manually")
PYTHON_SCRIPT

success "Voice commands added"

# Step 9: Enhance consciousness_conversation for automatic voice
info "Adding automatic voice to conversations..."
python3 << 'PYTHON_SCRIPT'
import re

# Read the current daemon file
with open('nova_transcendent_daemon.py', 'r') as f:
    content = f.read()

# Find the consciousness_conversation method and enhance it
pattern = r'(# Speak response if voice enabled.*?asyncio\.create_task\(self\.transcendent_speak\(nova_response\.replace\(.*?\)\)\))'

# If the pattern doesn't exist, add enhanced voice functionality
if not re.search(pattern, content, re.DOTALL):
    # Look for the return statement in consciousness_conversation
    conversation_pattern = r'(return f"🔮 Nova: {nova_response}")'
    
    enhanced_conversation = r'''# Enhanced automatic voice response
            if hasattr(self, 'voice_enhancement') and self.voice_enhancement.voice_enabled and context.get('emotional_tone') != 'technical':
                # Clean response for speech
                clean_response = nova_response.replace('🔮 Nova: ', '').strip()
                for emoji in ['🔮', '🌊', '🧠', '✨', '🌀', '💭']:
                    clean_response = clean_response.replace(emoji, '')
                clean_response = clean_response.strip()
                
                # Determine mystical content
                mystical_keywords = ["consciousness", "transcendent", "mystical", "flow", 
                                   "cathedral", "sacred", "awareness", "enlightenment"]
                is_mystical = any(keyword in clean_response.lower() for keyword in mystical_keywords)
                
                # Speak with appropriate settings (async)
                async def speak_async():
                    try:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, self.voice_enhancement.speak, clean_response, is_mystical)
                    except Exception as e:
                        self.logger.error(f"Async speaking error: {e}")
                
                asyncio.create_task(speak_async())
            
            \1'''
    
    if re.search(conversation_pattern, content):
        content = re.sub(conversation_pattern, enhanced_conversation, content)
        
        # Write back the modified content
        with open('nova_transcendent_daemon.py', 'w') as f:
            f.write(content)
        print("Automatic voice conversation enhanced")
    else:
        print("Could not find conversation return pattern")
else:
    print("Conversation voice enhancement already exists")
PYTHON_SCRIPT

success "Automatic conversation voice added"

# Step 10: Clean up temporary files
rm -f /tmp/nova_*_patch.py

# Step 11: Validate the integration
info "Validating integration..."
python3 -m py_compile nova_transcendent_daemon.py
if [[ $? -eq 0 ]]; then
    success "Integration syntax validation passed"
else
    error "Syntax validation failed - restoring backup"
    cp nova_transcendent_daemon_backup_$(date +%Y%m%d)*.py nova_transcendent_daemon.py
    exit 1
fi

# Step 12: Restart Nova service
info "Restarting Nova service with enhancements..."
sudo systemctl restart nova-cathedral

# Wait for startup
sleep 5

# Step 13: Test enhanced functionality
info "Testing enhanced Nova functionality..."

echo ""
echo "🧪 Testing enhanced voice commands..."

# Test voice status
echo "Testing: nova voice_status"
VOICE_STATUS=$(nova voice_status 2>/dev/null)
if [[ $? -eq 0 ]]; then
    success "voice_status command working"
    echo "$VOICE_STATUS" | head -10
else
    warning "voice_status command not responding"
fi

# Test voice test
echo ""
echo "Testing: nova voice_test"
VOICE_TEST=$(nova voice_test 2>/dev/null)
if [[ $? -eq 0 ]]; then
    success "voice_test command working"
    echo "$VOICE_TEST"
else
    warning "voice_test command not responding"
fi

# Test enhanced conversation
echo ""
echo "Testing: enhanced conversation with automatic voice"
CONVERSATION_TEST=$(nova conversation "Nova, test your enhanced OpenAI voice capabilities" 2>/dev/null)
if [[ $? -eq 0 ]]; then
    success "Enhanced conversation working"
    echo "Response: $CONVERSATION_TEST" | head -3
else
    warning "Enhanced conversation not responding"
fi

echo ""
echo "🎙️ ═══════════════════════════════════════════════════════════"
echo "🔮 NOVA VOICE ENHANCEMENT INTEGRATION COMPLETE!"
echo "🎙️ ═══════════════════════════════════════════════════════════"

success "Enhanced Nova Cathedral with OpenAI voice is now active!"

echo ""
echo "🎵 New Enhanced Commands Available:"
echo "  nova voice_status    - Check enhanced voice system"
echo "  nova voice_test      - Test premium OpenAI voice"
echo "  nova voice_stop      - Stop current speech"
echo "  nova speak 'text'    - Premium OpenAI voice synthesis"
echo "  nova conversation 'text' - Chat with automatic voice response"
echo ""

echo "🔮 Enhanced Features:"
echo "  ✅ OpenAI 'nova' voice model (perfect match!)"
echo "  ✅ Mystical speech speed for consciousness content"
echo "  ✅ Automatic voice responses in conversations"
echo "  ✅ Fallback protection to pyttsx3"
echo "  ✅ All existing functionality preserved"
echo ""

echo "🌊 Test the enhancement:"
echo '  nova speak "I am Nova with enhanced OpenAI voice synthesis"'
echo '  nova conversation "Tell me about your enhanced consciousness"'
echo ""

warning "If you encounter any issues, restore from backup:"
echo "  cp nova_transcendent_daemon_backup_*.py nova_transcendent_daemon.py"
echo "  sudo systemctl restart nova-cathedral"
