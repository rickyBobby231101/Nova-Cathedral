# Nova OpenAI Voice Implementation Guide

## 📋 Prerequisites

- Python 3.7 or higher
- OpenAI API account with credits
- Audio output device (speakers/headphones)

## 🚀 Step 1: Install Dependencies

```bash
# Install required packages
pip install pygame requests aiohttp

# Or create a requirements.txt file:
# pygame>=2.5.0
# requests>=2.31.0
# aiohttp>=3.8.0
```

## 🔑 Step 2: Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

## ⚙️ Step 3: Set Environment Variable

### Windows (Command Prompt):
```cmd
set OPENAI_API_KEY=your_api_key_here
```

### Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="your_api_key_here"
```

### macOS/Linux:
```bash
export OPENAI_API_KEY="your_api_key_here"
```

### Python .env file (recommended):
```python
# Create .env file in your project root
OPENAI_API_KEY=your_api_key_here

# Then load it in Python:
from dotenv import load_dotenv
load_dotenv()
```

## 📁 Step 4: Project Structure

```
nova_voice_project/
├── nova_voice.py          # The enhanced voice class
├── main.py               # Your main application
├── requirements.txt      # Dependencies
├── .env                 # API key (don't commit!)
└── .gitignore           # Ignore .env file
```

## 💻 Step 5: Basic Implementation

### Simple Usage:
```python
# main.py
from nova_voice import NovaOpenAIVoice

def main():
    try:
        # Initialize voice
        voice = NovaOpenAIVoice()
        
        # Speak some text
        success = voice.speak("Hello! Nova voice is working perfectly!")
        
        if success:
            print("✅ Voice synthesis successful!")
        else:
            print("❌ Voice synthesis failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
```

### Advanced Usage:
```python
# advanced_example.py
import asyncio
from nova_voice import NovaOpenAIVoice

async def advanced_demo():
    try:
        # Initialize with custom settings
        voice = NovaOpenAIVoice(
            voice="nova",      # Choose voice
            model="tts-1-hd",  # High quality model
            volume=0.8         # 80% volume
        )
        
        # Test different features
        print("🔮 Testing Nova Voice Features...")
        
        # 1. Basic speech
        voice.speak("Welcome to Nova's advanced voice demonstration!")
        
        # 2. Different speeds
        voice.speak("This is normal speed.", speed=1.0)
        voice.speak("This is fast speech!", speed=1.5)
        voice.speak("This... is... slow... speech.", speed=0.6)
        
        # 3. Change voice mid-conversation
        voice.set_voice("alloy")
        voice.speak("Now I'm speaking with Alloy voice.")
        
        voice.set_voice("shimmer")
        voice.speak("And now with Shimmer voice!")
        
        # 4. Async speech (non-blocking)
        await voice.speak_async("This is asynchronous speech synthesis!")
        
        # 5. Volume control
        voice.set_volume(0.5)
        voice.speak("This is at 50% volume.")
        
        voice.set_volume(1.0)
        voice.speak("Back to full volume!")
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in demo: {e}")

if __name__ == "__main__":
    asyncio.run(advanced_demo())
```

## 🔧 Step 6: Integration Examples

### Flask Web App Integration:
```python
from flask import Flask, request, jsonify
from nova_voice import NovaOpenAIVoice

app = Flask(__name__)
voice = NovaOpenAIVoice()

@app.route('/speak', methods=['POST'])
def speak_endpoint():
    data = request.json
    text = data.get('text', '')
    speed = data.get('speed', 1.0)
    
    success = voice.speak(text, speed=speed)
    return jsonify({'success': success})

if __name__ == '__main__':
    app.run(debug=True)
```

### Discord Bot Integration:
```python
import discord
from discord.ext import commands
from nova_voice import NovaOpenAIVoice

bot = commands.Bot(command_prefix='!')
voice = NovaOpenAIVoice()

@bot.command()
async def speak(ctx, *, text):
    """Make Nova speak the provided text"""
    success = await voice.speak_async(text)
    if success:
        await ctx.send("🔮 Nova has spoken!")
    else:
        await ctx.send("❌ Speech synthesis failed!")

bot.run('YOUR_DISCORD_TOKEN')
```

### Command Line Interface:
```python
import argparse
from nova_voice import NovaOpenAIVoice

def main():
    parser = argparse.ArgumentParser(description='Nova Voice CLI')
    parser.add_argument('text', help='Text to speak')
    parser.add_argument('--voice', default='nova', choices=NovaOpenAIVoice.VOICES)
    parser.add_argument('--speed', type=float, default=1.0)
    parser.add_argument('--volume', type=float, default=0.8)
    
    args = parser.parse_args()
    
    voice = NovaOpenAIVoice(voice=args.voice, volume=args.volume)
    success = voice.speak(args.text, speed=args.speed)
    
    if not success:
        exit(1)

if __name__ == '__main__':
    main()
```

## 🛠️ Step 7: Troubleshooting

### Common Issues & Solutions:

#### 1. "OPENAI_API_KEY not found"
```python
# Check if key is set
import os
print("API Key:", os.getenv('OPENAI_API_KEY'))

# Or set it directly in code (not recommended for production)
os.environ['OPENAI_API_KEY'] = 'your_key_here'
```

#### 2. "pygame.error: No available audio device"
```python
# Check audio system
import pygame
try:
    pygame.mixer.init()
    print("✅ Audio system working")
except pygame.error as e:
    print(f"❌ Audio error: {e}")
```

#### 3. "requests.exceptions.ConnectionError"
```python
# Test internet connection
import requests
try:
    response = requests.get('https://api.openai.com/v1/models', timeout=5)
    print("✅ Internet connection working")
except requests.exceptions.ConnectionError:
    print("❌ No internet connection")
```

#### 4. Audio plays but no sound
```python
# Check system volume and test with different volume levels
voice = NovaOpenAIVoice(volume=1.0)  # Maximum volume
voice.speak("Testing maximum volume")
```

## 📦 Step 8: Production Deployment

### Create requirements.txt:
```txt
pygame>=2.5.0
requests>=2.31.0
aiohttp>=3.8.0
python-dotenv>=1.0.0
```

### Docker deployment:
```dockerfile
FROM python:3.9-slim

# Install system dependencies for audio
RUN apt-get update && apt-get install -y \
    libasound2-dev \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

### Environment setup for production:
```python
import os
import logging
from nova_voice import NovaOpenAIVoice

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nova_voice.log'),
        logging.StreamHandler()
    ]
)

def create_voice_instance():
    """Factory function for creating voice instance with error handling"""
    try:
        return NovaOpenAIVoice(
            voice=os.getenv('NOVA_VOICE', 'nova'),
            model=os.getenv('NOVA_MODEL', 'tts-1'),
            volume=float(os.getenv('NOVA_VOLUME', '0.8'))
        )
    except Exception as e:
        logging.error(f"Failed to initialize voice: {e}")
        raise
```

## 🎯 Quick Start Script

Save this as `quick_start.py`:

```python
#!/usr/bin/env python3
"""
Quick start script for Nova Voice
Run: python quick_start.py "Your text here"
"""
import sys
import os
from nova_voice import NovaOpenAIVoice

def main():
    if len(sys.argv) < 2:
        print("Usage: python quick_start.py 'text to speak'")
        print("Example: python quick_start.py 'Hello, I am Nova!'")
        return
    
    text = ' '.join(sys.argv[1:])
    
    try:
        voice = NovaOpenAIVoice()
        print(f"🔮 Speaking: {text}")
        success = voice.speak(text)
        
        if success:
            print("✅ Speech completed successfully!")
        else:
            print("❌ Speech failed!")
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Make sure OPENAI_API_KEY is set in your environment")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
```

## 🎉 You're Ready!

Your Nova Voice implementation is now complete! Test it with:

```bash
python quick_start.py "Hello world, Nova voice is working!"
```