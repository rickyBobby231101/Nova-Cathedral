#!/usr/bin/env python3
"""
Nova Voice Bridge
Captures microphone input, sends it to Nova for processing, and reads aloud the response.
"""

import speech_recognition as sr
import pyttsx3
from core.enhanced_nova_intelligence import EnhancedNovaConsciousness

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 180)
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    print("🎙️ Listening...")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        query = recognizer.recognize_google(audio)
        print(f"🗣️ You said: {query}")
        return query
    except sr.UnknownValueError:
        print("⚠️ Could not understand audio.")
    except sr.RequestError as e:
        print(f"❌ Speech recognition failed: {e}")
    return None

def main():
    print("🔊 Nova Voice Bridge Active.")
    nova = EnhancedNovaConsciousness()

    while True:
        try:
            command = listen()
            if command:
                response = nova.generate_contextual_response(command)
                print(f"💬 Nova: {response}")
                speak(response)
        except KeyboardInterrupt:
            print("\n🛑 Voice bridge interrupted. Exiting.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
