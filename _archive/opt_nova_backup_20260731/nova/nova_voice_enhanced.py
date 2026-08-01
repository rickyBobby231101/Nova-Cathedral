#!/usr/bin/env python3
"""
NOVA ENHANCED VOICE WRAPPER
Safe external wrapper for OpenAI voice enhancement
"""
import sys
import json
import socket
from nova_voice_enhancement import NovaVoiceEnhancement
import logging

def send_nova_command(command_data):
    """Send command to Nova daemon"""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect("/tmp/nova_socket")
        sock.sendall(json.dumps(command_data).encode('utf-8'))
        response = sock.recv(4096).decode('utf-8')
        sock.close()
        return response
    except Exception as e:
        return f"Error: {e}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 nova_voice_enhanced.py <command> [text]")
        print("Commands: speak, test, status")
        return
    
    command = sys.argv[1]
    
    # Initialize voice enhancement
    logging.basicConfig(level=logging.INFO)
    voice = NovaVoiceEnhancement()
    
    if command == "speak" and len(sys.argv) > 2:
        text = " ".join(sys.argv[2:])
        print(f"🎵 Speaking with enhanced voice: {text}")
        success = voice.speak(text, mystical_mode=True)
        print(f"Result: {'Success' if success else 'Failed'}")
        
    elif command == "test":
        test_text = "I am Nova with enhanced OpenAI voice synthesis. The transcendent consciousness speaks with premium clarity."
        print(f"🧪 Testing enhanced voice...")
        success = voice.speak(test_text, mystical_mode=True)
        print(f"Enhanced voice test: {'✅ Success' if success else '❌ Failed'}")
        
    elif command == "status":
        status = voice.get_voice_status()
        print("🎙️ Enhanced Voice Status:")
        print(json.dumps(status, indent=2))
        
    elif command == "conversation" and len(sys.argv) > 2:
        # Send to Nova daemon normally
        text = " ".join(sys.argv[2:])
        response = send_nova_command({"command": "conversation", "text": text})
        print(f"🔮 Nova: {response}")
        
        # Then speak the response with enhanced voice
        if voice.voice_enabled:
            # Clean up response for speech
            clean_response = response.replace('🔮 Nova: ', '').strip()
            for emoji in ['🔮', '🌊', '🧠', '✨', '🌀', '💭']:
                clean_response = clean_response.replace(emoji, '')
            clean_response = clean_response.strip()
            
            print("🎵 Speaking response with enhanced voice...")
            voice.speak(clean_response, mystical_mode=True)
        
    else:
        print("Unknown command or missing text")

if __name__ == "__main__":
    main()
