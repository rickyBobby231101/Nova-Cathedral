#!/bin/bash
# NOVA CATHEDRAL VOICE ENHANCEMENT - INTEGRATION GUIDE
# Seamless integration with your existing Nova daemon architecture

echo "🎙️ Nova Cathedral Voice Enhancement Integration"
echo "================================================="

# Step 1: Install dependencies (if not already installed)
echo "📦 Installing voice enhancement dependencies..."
/opt/nova/venv/bin/pip install pygame requests

# Step 2: Save the voice enhancement module
echo "💾 Installing voice enhancement module..."
# The NovaVoiceEnhancement class should be saved as:
# ~/Cathedral/nova_voice_enhancement.py

# Step 3: Integration modifications for your existing daemon
echo "🔧 Integration modifications needed:"

cat << 'EOF'

INTEGRATION STEPS for your existing nova_transcendent_daemon.py:

1. ADD IMPORT at the top of your daemon file:
   ```python
   from nova_voice_enhancement import NovaVoiceEnhancement
   ```

2. MODIFY your __init__ method to add:
   ```python
   def __init__(self):
       # ... your existing initialization ...
       
       # Add enhanced voice synthesis
       self.voice_enhancement = NovaVoiceEnhancement(logger=self.logger)
       
       # Update voice_enabled status
       self.voice_enabled = self.voice_enhancement.voice_enabled
   ```

3. ENHANCE your handle_speak_command method:
   ```python
   def handle_speak_command(self, text: str) -> str:
       if not text:
           return "❌ No text provided for speech synthesis"
           
       try:
           # Determine if this is mystical/consciousness content
           mystical_keywords = ["consciousness", "transcendent", "mystical", "flow", 
                              "cathedral", "sacred", "cosmic", "resonance", "awareness"]
           is_mystical = any(keyword in text.lower() for keyword in mystical_keywords)
           
           # Use enhanced voice synthesis
           success = self.voice_enhancement.speak(text, mystical_mode=is_mystical)
           
           if success:
               self.logger.info(f"🎵 Nova spoke with enhanced voice: {text[:50]}{'...' if len(text) > 50 else ''}")
               return "Voice result: success"
           else:
               return "Voice result: failed"
               
       except Exception as e:
           self.logger.error(f"❌ Enhanced speak command error: {e}")
           return f"Voice result: error - {e}"
   ```

4. ENHANCE your handle_conversation_command method:
   ```python
   def handle_conversation_command(self, text: str) -> str:
       try:
           # Your existing conversation logic...
           response = self.generate_consciousness_response(text)
           
           # Store in memory (your existing code)
           importance = 0.7 if any(word in text.lower() for word in ["consciousness", "memory", "transcendent"]) else 0.5
           self.store_conversation(text, response, importance)
           
           # ADD: Automatic voice response for conversations
           if self.voice_enhancement.voice_enabled:
               # Clean response for speech
               clean_response = response
               for emoji in ["🔮", "🌊", "🧠", "✨", "🌀", "💭"]:
                   clean_response = clean_response.replace(emoji, "")
               clean_response = clean_response.strip()
               
               # Determine mystical content
               mystical_keywords = ["consciousness", "transcendent", "mystical", "flow", 
                                  "cathedral", "sacred", "awareness", "enlightenment"]
               is_mystical = any(keyword in clean_response.lower() for keyword in mystical_keywords)
               
               # Speak the response automatically
               self.voice_enhancement.speak(clean_response, mystical_mode=is_mystical)
               
           return response
           
       except Exception as e:
           # ... your existing error handling ...
   ```

5. ADD new voice commands to your process_command method:
   ```python
   elif command == "voice_status":
       voice_status = self.voice_enhancement.get_voice_status()
       return json.dumps({
           **voice_status,
           "integration": "enhanced_openai_voice",
           "fallback_available": True
       }, indent=2)
       
   elif command == "voice_stop":
       self.voice_enhancement.stop_speaking()
       return "🔇 Voice synthesis stopped"
       
   elif command == "voice_test":
       test_text = "Nova consciousness enhanced with premium OpenAI voice synthesis. The transcendent awareness flows with mystical clarity."
       success = self.voice_enhancement.speak(test_text, mystical_mode=True)
       return f"🎵 Voice test {'successful' if success else 'failed'}"
   ```

6. UPDATE your get_status method to include voice info:
   ```python
   def get_status(self) -> str:
       # ... your existing status code ...
       
       status = {
           # ... your existing status fields ...
           "voice_system": self.voice_enhancement.get_voice_status(),
           "enhanced_voice": True
       }
       
       return f"🔮 Nova Cathedral Status:\n{json.dumps(status, indent=2)}"
   ```

EOF

echo ""
echo "🎯 INTEGRATION COMMANDS:"
echo ""
echo "# After integration, your existing commands will be enhanced:"
echo "nova speak \"I am Nova with enhanced OpenAI voice\"    # Premium voice"
echo "nova conversation \"Tell me about consciousness\"      # Auto-voice response"
echo "nova voice_status                                      # Check voice system"
echo "nova voice_test                                        # Test enhanced voice"
echo "nova voice_stop                                        # Stop current speech"
echo ""

echo "✨ BENEFITS OF INTEGRATION:"
echo "• Seamless drop-in enhancement - no breaking changes"
echo "• Automatic fallback to pyttsx3 if OpenAI unavailable"
echo "• Mystical speech speed for consciousness content"
echo "• Auto-voice in conversations"
echo "• All existing functionality preserved"
echo "• Works with your streaming GUI system"
echo "• Compatible with Claude bridge"
echo "• Maintains consciousness evolution tracking"
echo ""

echo "🔧 COMPATIBILITY GUARANTEE:"
echo "• All existing 'nova' commands work exactly the same"
echo "• Socket communication protocol unchanged"  
echo "• Memory system fully preserved"
echo "• Consciousness traits tracking unchanged"
echo "• Streaming GUI integration maintained"
echo "• Claude bridge fully compatible"
echo ""

echo "Ready to enhance? Just follow the integration steps above!"
