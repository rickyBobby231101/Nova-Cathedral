#!/usr/bin/env python3
import sys
from claude_bridge import NovaClaude_Bridge

bridge = NovaClaude_Bridge()

# Get the latest message file
import glob
files = glob.glob('/home/daniel/Cathedral/bridge/nova_to_claude/*.json')
if files:
    latest_file = max(files)
    import json
    with open(latest_file, 'r') as f:
        message_data = json.load(f)
    
    print("Sending Nova's message to Claude...")
    response = bridge.send_to_claude(message_data)
    
    if "error" not in response:
        print("✨ Claude responded! Check claude_to_nova/ directory.")
    else:
        print(f"Error: {response['error']}")
