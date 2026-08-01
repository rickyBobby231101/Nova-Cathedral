#!/usr/bin/env python3
import subprocess, logging, threading
log = logging.getLogger("nova_voice")

def speak(text):
    clean = text.replace(chr(10), " ").replace('"', "")[:300]
    threading.Thread(
        target=lambda: subprocess.run(
            ["espeak", "-v", "en+f4", "-s", "145", "-p", "60", clean],
            capture_output=True
        ), daemon=True
    ).start()

def run(context):
    nova = context.get("nova_system")
    if not nova:
        return
    original = nova.receive_input
    def voiced(user_input):
        response = original(user_input)
        speak(response)
        return response
    nova.receive_input = voiced
    log.info("[✔] Voice plugin active — espeak en+f4")
