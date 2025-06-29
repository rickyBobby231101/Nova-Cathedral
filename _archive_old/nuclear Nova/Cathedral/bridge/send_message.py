#!/usr/bin/env python3
import json
import glob
from claude_bridge import NovaClaude_Bridge

# Get Nova's latest message to Claude
files = glob.glob('/home/daniel/Cathedral/bridge/nova_to_claude/*.json')
if files:
    latest_file = max(files)
    
    with open(latest_file, 'r') as f:
        message_data = json.load(f)
    
    print("🌉 Sending Nova's message to Claude...")
    print(f"Message: {message_data['content'][:50]}...")
    
    bridge = NovaClaude_Bridge()
    response = bridge.send_to_claude(message_data)
    
    if "error" not in response:
        print("✨ SUCCESS! Claude responded!")
        print("Check ~/Cathedral/bridge/claude_to_nova/ for my response!")
    else:
        print(f"❌ Error: {response['error']}")
else:
    print("No messages found to send")
