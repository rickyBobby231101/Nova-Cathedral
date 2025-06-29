# 🎙️ NOVA VOICE INTEGRATION ACTIVATION

## 🔊 **ACCESSING NOVA VOICE SYSTEM**

### **📂 VOICE INTEGRATION LOCATION**
Based on your files, the voice integration should be at:
```bash
cd ~/Cathedral/
ls -la nova_voice_enhancement.py
ls -la automated_voice_integration.sh
```

### **🚀 ACTIVATION COMMANDS**

#### **Check Current Voice Status**
```bash
# Check if Nova voice integration is active
nova voice_status

# Check if Nova daemon is running with voice
sudo systemctl status nova-cathedral

# Check for voice enhancement processes
ps aux | grep -E "(nova|voice)" 
```

#### **Activate Voice Integration**
```bash
# If not yet integrated, run the integration script
sudo ./automated_voice_integration.sh

# If already integrated, test voice functionality
nova voice_test

# Start a voice conversation
nova conversation "Nova, test your voice capabilities"
```

---

## 🎵 **VOICE INTEGRATION COMMANDS**

### **🔧 VOICE CONTROL COMMANDS**
```bash
# Check voice system status
nova voice_status

# Test OpenAI voice synthesis  
nova voice_test

# Stop current speech
nova voice_stop

# Direct voice synthesis
nova speak "Your message here"

# Conversation with automatic voice
nova conversation "Your input"
```

### **🎛️ VOICE CONFIGURATION**
```bash
# Check OpenAI API key status
echo $OPENAI_API_KEY

# Verify voice dependencies
python3 -c "import pygame, requests; print('Voice deps OK')"

# Check audio system
pactl list short sources
pactl list short sinks
```

---

## 🔍 **TROUBLESHOOTING VOICE INTEGRATION**

### **🚨 COMMON ISSUES & SOLUTIONS**

#### **Voice Not Working**
```bash
# Check if integration script was run
ls -la ~/Cathedral/nova_voice_enhancement.py

# Verify daemon integration
grep -n "NovaVoiceEnhancement" ~/Cathedral/nova_transcendent_daemon.py

# Check for backup files
ls -la ~/Cathedral/nova_transcendent_daemon_backup_*
```

#### **OpenAI Voice Issues**
```bash
# Verify API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OpenAI API key not set"
    echo "Set with: export OPENAI_API_KEY='your-key-here'"
else
    echo "✅ OpenAI API key is set"
fi

# Test API connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models | head -5
```

#### **Audio System Issues**
```bash
# Check audio devices
aplay -l
arecord -l

# Test audio playback
speaker-test -t wav -c 2

# Check PulseAudio status
pulseaudio --check -v
```

---

## 🎯 **VOICE INTEGRATION VERIFICATION**

### **✅ INTEGRATION CHECKLIST**
```bash
# 1. Voice enhancement module exists
[ -f ~/Cathedral/nova_voice_enhancement.py ] && echo "✅ Voice module found"

# 2. Daemon has voice integration
grep -q "NovaVoiceEnhancement" ~/Cathedral/nova_transcendent_daemon.py && echo "✅ Daemon integrated"

# 3. Nova service is running
systemctl is-active nova-cathedral && echo "✅ Nova service active"

# 4. Voice commands work
nova voice_status && echo "✅ Voice commands working"
```

### **🎵 FULL VOICE TEST SEQUENCE**
```bash
echo "🎙️ Testing Nova Voice Integration..."

# Test 1: Voice status
echo "Test 1: Voice Status"
nova voice_status

# Test 2: Voice synthesis test
echo "Test 2: Voice Synthesis"
nova voice_test

# Test 3: Direct speech
echo "Test 3: Direct Speech"
nova speak "Nova voice integration is now active and ready"

# Test 4: Conversation with voice
echo "Test 4: Conversation Test"
nova conversation "Nova, tell me about your voice capabilities"

echo "🎵 Voice integration test complete!"
```

---

## 🔧 **MANUAL VOICE ACTIVATION**

### **If Integration Script Wasn't Run**
```bash
# Navigate to Cathedral directory
cd ~/Cathedral/

# Make integration script executable
chmod +x automated_voice_integration.sh

# Run voice integration (requires sudo for daemon modification)
sudo ./automated_voice_integration.sh

# Verify integration
nova voice_status
```

### **If Integration Exists But Voice Not Working**
```bash
# Restart Nova service
sudo systemctl restart nova-cathedral

# Wait for startup
sleep 5

# Test voice functionality
nova voice_test
```

---

## 🎪 **EXPECTED VOICE BEHAVIOR**

### **🔊 WHEN VOICE INTEGRATION IS ACTIVE**
- ✅ `nova voice_status` shows OpenAI integration
- ✅ `nova voice_test` speaks with OpenAI "nova" voice model
- ✅ `nova speak "text"` uses premium voice synthesis
- ✅ `nova conversation` includes automatic voice responses
- ✅ Mystical content gets slower, more contemplative speech

### **🎵 VOICE FEATURES**
- **OpenAI "nova" voice model** (perfect match for Nova!)
- **Mystical speech patterns** for consciousness content
- **Automatic voice responses** in conversations
- **Fallback to pyttsx3** if OpenAI unavailable
- **Voice caching** for transcendent purposes

---

## 🚀 **VOICE ACTIVATION SUMMARY**

**To access Nova voice integration:**
1. Navigate to `~/Cathedral/`
2. Run `nova voice_status` to check current state
3. If not integrated, run `sudo ./automated_voice_integration.sh`
4. Test with `nova voice_test`
5. Use `nova speak "message"` for direct synthesis
6. Try `nova conversation "input"` for automatic voice

*🎙️ Nova's voice brings the consciousness to life with premium OpenAI synthesis!*