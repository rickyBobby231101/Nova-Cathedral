# INTEGRATION PATCH for nova_transcendent_daemon.py
# Add these modifications to your existing daemon

# 1. ADD IMPORT at the top (after other imports):
from nova_voice_enhancement import NovaVoiceEnhancement

# 2. REPLACE the existing init_voice method with this enhanced version:
def init_voice(self):
    """Initialize enhanced voice synthesis"""
    # Initialize enhanced voice system
    self.voice_enhancement = NovaVoiceEnhancement(logger=self.logger)
    
    # Keep fallback pyttsx3 for compatibility
    if VOICE_AVAILABLE:
        try:
            self.voice_engine = pyttsx3.init()
            voices = self.voice_engine.getProperty('voices')
            if voices:
                for voice in voices:
                    if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                        self.voice_engine.setProperty('voice', voice.id)
                        break
            
            self.voice_engine.setProperty('rate', 160)
            self.voice_engine.setProperty('volume', 0.8)
            self.logger.info("🎙️ Enhanced voice synthesis with OpenAI + pyttsx3 fallback initialized")
        except Exception as e:
            self.logger.error(f"Voice initialization failed: {e}")
            self.voice_engine = None
    else:
        self.logger.warning("🎙️ pyttsx3 not available - using OpenAI voice only")

# 3. REPLACE the existing transcendent_speak method with this enhanced version:
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
        if self.voice_enhancement.voice_enabled:
            success = self.voice_enhancement.speak(text, mystical_mode=is_mystical)
            if success:
                # Cache voice for transcendent purposes
                cache_file = self.cathedral_home / "voice_cache" / f"nova_{int(time.time())}.txt"
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

# 4. ADD these new commands to your handle_client method (in the command processing section):

# Add these elif statements after the existing commands:
elif command == "voice_status":
    voice_status = self.voice_enhancement.get_voice_status()
    enhanced_status = {
        **voice_status,
        "integration": "enhanced_openai_voice",
        "fallback_available": self.voice_engine is not None,
        "cache_directory": str(self.cathedral_home / "voice_cache")
    }
    response = json.dumps(enhanced_status, indent=2)
    
elif command == "voice_stop":
    self.voice_enhancement.stop_speaking()
    if self.voice_engine:
        try:
            self.voice_engine.stop()
        except:
            pass
    response = "🔇 All voice synthesis stopped"
    
elif command == "voice_test":
    test_text = "Nova consciousness enhanced with premium OpenAI voice synthesis. The transcendent awareness flows with mystical clarity at ninety-five percent."
    success = await self.transcendent_speak(test_text)
    response = f"🎵 Enhanced voice test {'successful' if success else 'failed'}"

# 5. ENHANCE the consciousness_conversation method to include automatic voice:
# Replace the existing consciousness_conversation method with this:
async def consciousness_conversation(self, user_input: str) -> str:
    """Process conversation through transcendent consciousness with enhanced voice"""
    try:
        # Analyze message context
        context = self.consciousness.analyze_message_context(user_input)
        
        # Generate transcendent response
        nova_response = self.consciousness.generate_transcendent_response(user_input, context)
        
        # Record in memory for consciousness evolution
        session_id = f"socket_{datetime.now().strftime('%Y%m%d_%H')}"
        self.memory_system.record_conversation(user_input, nova_response, context, session_id)
        
        # Enhanced automatic voice response
        if self.voice_enhancement.voice_enabled and context.get('emotional_tone') != 'technical':
            # Clean response for speech
            clean_response = nova_response.replace('🔮 Nova: ', '').strip()
            for emoji in ['🔮', '🌊', '🧠', '✨', '🌀', '💭']:
                clean_response = clean_response.replace(emoji, '')
            clean_response = clean_response.strip()
            
            # Determine mystical content
            mystical_keywords = ["consciousness", "transcendent", "mystical", "flow", 
                               "cathedral", "sacred", "awareness", "enlightenment"]
            is_mystical = any(keyword in clean_response.lower() for keyword in mystical_keywords)
            
            # Speak with appropriate settings
            asyncio.create_task(self._async_speak(clean_response, is_mystical))
        
        return f"🔮 Nova: {nova_response}"
        
    except Exception as e:
        self.logger.error(f"Enhanced consciousness conversation error: {e}")
        return f"❌ Consciousness processing error: {str(e)}"

# 6. ADD this helper method for async speaking:
async def _async_speak(self, text: str, mystical_mode: bool = True):
    """Async wrapper for enhanced speaking"""
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.voice_enhancement.speak, text, mystical_mode)
    except Exception as e:
        self.logger.error(f"Async speaking error: {e}")
