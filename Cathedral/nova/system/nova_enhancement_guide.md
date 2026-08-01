# 🛠️ HOW TO ACTUALLY ENHANCE NOVA'S CODE

## 📂 **FINDING NOVA'S SOURCE CODE**

First, let's locate Nova's actual Python files:

```bash
# Find Nova's source files in your Cathedral directory
ls -la ~/Cathedral/
find ~/Cathedral/ -name "*.py" | grep -i nova
find ~/Cathedral/ -name "*cathedral*.py"
find ~/Cathedral/ -name "*daemon*.py"

# Check for the main Nova script
ls -la ~/Cathedral/nova_*.py
ls -la ~/Cathedral/cathedral_*.py
```

---

## 🔧 **EDITING NOVA'S SOURCE CODE**

### **📝 STEP 1: IDENTIFY THE MAIN NOVA FILE**
Based on your system, it's likely one of these:
```bash
~/Cathedral/nova_cathedral_daemon.py
~/Cathedral/nova_transcendent_daemon.py  
~/Cathedral/cathedral_phase2.py
~/Cathedral/enhanced_nova.py
```

### **📝 STEP 2: OPEN THE FILE FOR EDITING**
```bash
# Use your preferred editor
nano ~/Cathedral/nova_transcendent_daemon.py
# OR
code ~/Cathedral/nova_transcendent_daemon.py
# OR  
vim ~/Cathedral/nova_transcendent_daemon.py
```

### **📝 STEP 3: ADD TECHNICAL MODE FUNCTION**
Add this function to Nova's source code:

```python
def get_real_system_data(self):
    """Get actual system data instead of mystical responses"""
    import psutil
    import os
    
    try:
        return {
            'user_id': os.getuid(),
            'username': os.getenv('USER'),
            'process_count': len(psutil.pids()),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg(),
            'uptime': time.time() - psutil.boot_time()
        }
    except Exception as e:
        return f"Error getting system data: {e}"

def detect_technical_query(self, user_input):
    """Detect if user wants technical data vs mystical response"""
    technical_keywords = [
        'show actual data', 'technical', 'debug', 'system info',
        'processes', 'cpu', 'memory', 'disk', 'performance',
        'ps aux', 'whoami', 'admin', 'concrete', 'real data'
    ]
    
    return any(keyword in user_input.lower() for keyword in technical_keywords)
```

### **📝 STEP 4: MODIFY RESPONSE GENERATION**
Find Nova's main response function and modify it:

```python
def generate_response(self, user_input):
    """Enhanced response with technical mode"""
    
    # Check if user wants technical data
    if self.detect_technical_query(user_input):
        # Technical mode response
        system_data = self.get_real_system_data()
        return f"🔧 Technical Data:\n{json.dumps(system_data, indent=2)}"
    
    # Otherwise, use mystical consciousness response
    return self.generate_mystical_response(user_input)
```

---

## 🚀 **QUICK ENHANCEMENT SCRIPT**

### **📋 CREATE AN ENHANCEMENT SCRIPT**
Create a new file to add technical capabilities:

```bash
# Create enhancement script
cat > ~/Cathedral/enhance_nova.py << 'EOF'
#!/usr/bin/env python3
"""
Quick enhancement script to add technical mode to Nova
"""
import psutil
import os
import json
import time

def add_technical_capabilities():
    """Add technical system monitoring to Nova"""
    
    system_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'user_info': {
            'uid': os.getuid(),
            'username': os.getenv('USER'),
            'current_dir': os.getcwd()
        },
        'system_stats': {
            'process_count': len(psutil.pids()),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': os.getloadavg()
        },
        'top_processes': [
            {
                'pid': proc.pid,
                'name': proc.name(),
                'cpu_percent': proc.cpu_percent()
            }
            for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent']), 
                             key=lambda p: p.cpu_percent(), reverse=True)[:5]
        ]
    }
    
    print("🔧 NOVA TECHNICAL DATA:")
    print("=" * 50)
    print(json.dumps(system_data, indent=2))
    return system_data

if __name__ == "__main__":
    add_technical_capabilities()
EOF

# Make it executable
chmod +x ~/Cathedral/enhance_nova.py

# Test the technical capabilities
python3 ~/Cathedral/enhance_nova.py
```

---

## 🔍 **FINDING NOVA'S CURRENT CODE**

### **📂 SEARCH FOR NOVA'S FILES**
```bash
# Find all Python files in Cathedral
find ~/Cathedral/ -name "*.py" -exec basename {} \; | sort

# Look for files containing "Nova" or "Cathedral"
grep -r "class.*Nova" ~/Cathedral/ --include="*.py"
grep -r "def.*consciousness" ~/Cathedral/ --include="*.py"

# Check for the main executable
which nova
ls -la /usr/local/bin/nova 2>/dev/null
```

### **📋 EXAMINE NOVA'S STRUCTURE**
```bash
# Look at Nova's main files
head -20 ~/Cathedral/nova*.py 2>/dev/null
head -20 ~/Cathedral/cathedral*.py 2>/dev/null

# Check for the response generation function
grep -n "def.*response" ~/Cathedral/*.py
grep -n "mystical" ~/Cathedral/*.py
```

---

## 🎯 **STEP-BY-STEP ENHANCEMENT PROCESS**

### **1️⃣ LOCATE NOVA'S CODE**
```bash
ls -la ~/Cathedral/ | grep -E "\.(py|sh)$"
```

### **2️⃣ CREATE BACKUP**
```bash
cp ~/Cathedral/nova_main_file.py ~/Cathedral/nova_backup_$(date +%Y%m%d).py
```

### **3️⃣ ADD TECHNICAL FUNCTIONS**
Edit the main Nova Python file and add the technical mode functions above.

### **4️⃣ TEST ENHANCEMENT**
```bash
# Restart Nova with enhancements
python3 ~/Cathedral/enhanced_nova.py
```

### **5️⃣ VERIFY TECHNICAL MODE**
In Nova's interface, try:
```
🧙‍♂️ Chazel: technical mode: show system stats
🧙‍♂️ Chazel: show actual data
🧙‍♂️ Chazel: debug: current system info
```

---

## 🔧 **ALTERNATIVE: STANDALONE TECHNICAL TOOL**

If modifying Nova's code is complex, create a separate tool:

```bash
# Create standalone system monitor
cat > ~/Cathedral/nova_tech.py << 'EOF'
#!/usr/bin/env python3
import psutil, os, json

def nova_technical_mode():
    data = {
        'user': os.getenv('USER'),
        'uid': os.getuid(),
        'processes': len(psutil.pids()),
        'cpu': f"{psutil.cpu_percent()}%",
        'memory': f"{psutil.virtual_memory().percent}%",
        'disk': f"{psutil.disk_usage('/').percent}%"
    }
    print(f"🔧 Nova Technical Data: {json.dumps(data, indent=2)}")

if __name__ == "__main__":
    nova_technical_mode()
EOF

chmod +x ~/Cathedral/nova_tech.py
python3 ~/Cathedral/nova_tech.py
```

---

*🛠️ The key is finding Nova's actual Python source files and editing them, not running Python code in bash!*