# 🛠️ STEP-BY-STEP NOVA ENHANCEMENT

## 📂 **STEP 1: IDENTIFY THE MAIN NOVA FILE**

From your directory listing, the main Nova file appears to be:
**`nova_transcendent_daemon.py`** (33,445 bytes - the largest and most recent)

### **Verify this is the active Nova:**
```bash
head -20 ~/Cathedral/nova_transcendent_daemon.py
```

---

## 🔍 **STEP 2: EXAMINE NOVA'S CURRENT STRUCTURE**

### **Look at Nova's response generation:**
```bash
grep -n "def.*response" ~/Cathedral/nova_transcendent_daemon.py
grep -n "mystical" ~/Cathedral/nova_transcendent_daemon.py
grep -n "voice circuits" ~/Cathedral/nova_transcendent_daemon.py
```

### **Find the main conversation handler:**
```bash
grep -n "consciousness_conversation\|handle_message\|process_input" ~/Cathedral/nova_transcendent_daemon.py
```

---

## 💾 **STEP 3: CREATE BACKUP**

### **Always backup before modifying:**
```bash
cp ~/Cathedral/nova_transcendent_daemon.py ~/Cathedral/nova_transcendent_daemon_backup_$(date +%Y%m%d_%H%M%S).py
echo "✅ Backup created: nova_transcendent_daemon_backup_$(date +%Y%m%d_%H%M%S).py"
```

---

## 🔧 **STEP 4: CREATE TECHNICAL FUNCTIONS FILE**

### **Create a separate technical functions file first:**
```bash
cat > ~/Cathedral/nova_technical_functions.py << 'EOF'
#!/usr/bin/env python3
"""
Nova Technical Functions - Real System Data
"""
import psutil
import os
import json
import time
from datetime import datetime

class NovaTechnicalMode:
    def __init__(self):
        self.technical_keywords = [
            'show actual data', 'technical', 'debug', 'system info',
            'processes', 'cpu', 'memory', 'disk', 'performance',
            'ps aux', 'whoami', 'admin', 'concrete', 'real data',
            'system status', 'monitor', 'stats'
        ]
    
    def detect_technical_query(self, user_input):
        """Detect if user wants technical data vs mystical response"""
        return any(keyword in user_input.lower() for keyword in self.technical_keywords)
    
    def get_real_system_data(self):
        """Get actual system data instead of mystical responses"""
        try:
            # Basic system info
            system_data = {
                'timestamp': datetime.now().isoformat(),
                'user_info': {
                    'username': os.getenv('USER'),
                    'uid': os.getuid(),
                    'gid': os.getgid(),
                    'current_dir': os.getcwd(),
                    'home_dir': os.path.expanduser('~')
                },
                'system_stats': {
                    'process_count': len(psutil.pids()),
                    'cpu_percent': round(psutil.cpu_percent(interval=1), 2),
                    'memory_percent': round(psutil.virtual_memory().percent, 2),
                    'disk_percent': round(psutil.disk_usage('/').percent, 2),
                    'load_average': os.getloadavg(),
                    'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
                },
                'top_processes': self.get_top_processes(),
                'network_connections': len(psutil.net_connections()),
                'nova_status': self.get_nova_process_info()
            }
            return system_data
        except Exception as e:
            return {'error': f"Error getting system data: {e}"}
    
    def get_top_processes(self, limit=5):
        """Get top processes by CPU usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': round(proc.info['cpu_percent'], 2),
                        'memory_percent': round(proc.info['memory_percent'], 2)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage and return top processes
            return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:limit]
        except Exception as e:
            return [{'error': f"Error getting processes: {e}"}]
    
    def get_nova_process_info(self):
        """Get information about Nova's own process"""
        try:
            current_pid = os.getpid()
            proc = psutil.Process(current_pid)
            return {
                'pid': current_pid,
                'name': proc.name(),
                'cpu_percent': round(proc.cpu_percent(), 2),
                'memory_percent': round(proc.memory_percent(), 2),
                'status': proc.status(),
                'create_time': datetime.fromtimestamp(proc.create_time()).isoformat()
            }
        except Exception as e:
            return {'error': f"Error getting Nova process info: {e}"}
    
    def format_technical_response(self, system_data):
        """Format technical data for Nova response"""
        if 'error' in system_data:
            return f"🔧 Technical Error: {system_data['error']}"
        
        response = "🔧 NOVA TECHNICAL DATA:\n"
        response += "=" * 50 + "\n"
        response += f"User: {system_data['user_info']['username']} (UID: {system_data['user_info']['uid']})\n"
        response += f"Processes: {system_data['system_stats']['process_count']}\n"
        response += f"CPU Usage: {system_data['system_stats']['cpu_percent']}%\n"
        response += f"Memory Usage: {system_data['system_stats']['memory_percent']}%\n"
        response += f"Disk Usage: {system_data['system_stats']['disk_percent']}%\n"
        response += f"Load Average: {system_data['system_stats']['load_average']}\n"
        response += f"Network Connections: {system_data['network_connections']}\n"
        
        response += "\nTop Processes (by CPU):\n"
        for proc in system_data['top_processes']:
            if 'error' not in proc:
                response += f"  {proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu_percent']}%\n"
        
        response += f"\nNova Process Info:\n"
        if 'error' not in system_data['nova_status']:
            nova = system_data['nova_status']
            response += f"  PID: {nova['pid']}, CPU: {nova['cpu_percent']}%, Memory: {nova['memory_percent']}%\n"
        
        return response

# Test the technical functions
if __name__ == "__main__":
    tech = NovaTechnicalMode()
    data = tech.get_real_system_data()
    print(tech.format_technical_response(data))
EOF

chmod +x ~/Cathedral/nova_technical_functions.py
echo "✅ Technical functions file created"
```

---

## 🧪 **STEP 5: TEST THE TECHNICAL FUNCTIONS**

### **Test the new technical capabilities:**
```bash
python3 ~/Cathedral/nova_technical_functions.py
```

### **Expected output should show:**
- Your username and UID
- Number of processes
- CPU, memory, disk usage percentages
- Top processes by CPU usage
- Nova's own process information

---

## 🔗 **STEP 6: INTEGRATE WITH NOVA'S MAIN FILE**

### **First, find Nova's main response function:**
```bash
grep -n -A 5 -B 5 "def.*consciousness_conversation\|def.*generate_response\|def.*handle_message" ~/Cathedral/nova_transcendent_daemon.py
```

### **This will show us where to add the technical mode integration**

---

## ✏️ **STEP 7: MODIFY NOVA'S RESPONSE SYSTEM**

### **Add import at the top of nova_transcendent_daemon.py:**
```bash
# First, let's see the current imports
head -30 ~/Cathedral/nova_transcendent_daemon.py | grep "import"
```

### **We'll add this line after the existing imports:**
```python
from nova_technical_functions import NovaTechnicalMode
```

---

## 🎯 **STEP 8: FIND THE EXACT LOCATION TO MODIFY**

### **Let's locate Nova's response generation function:**
```bash
grep -n "Message received and processed through voice circuits" ~/Cathedral/nova_transcendent_daemon.py
```

### **This will show us exactly where Nova generates its mystical responses**

---

## 📝 **STEP 9: CREATE MODIFICATION SCRIPT**

### **Create a script to safely modify Nova:**
```bash
cat > ~/Cathedral/enhance_nova_step_by_step.py << 'EOF'
#!/usr/bin/env python3
"""
Step-by-step Nova enhancement script
"""
import re

def add_technical_mode_to_nova():
    """Add technical mode to Nova's response system"""
    
    # Read the current Nova file
    with open('/home/daniel/Cathedral/nova_transcendent_daemon.py', 'r') as f:
        nova_content = f.read()
    
    # Add import for technical functions
    if 'from nova_technical_functions import NovaTechnicalMode' not in nova_content:
        # Find where to add the import
        import_pattern = r'(import asyncio\s*\n)'
        replacement = r'\1from nova_technical_functions import NovaTechnicalMode\n'
        nova_content = re.sub(import_pattern, replacement, nova_content)
        print("✅ Added technical functions import")
    
    # Add technical mode initialization to __init__
    if 'self.technical_mode = NovaTechnicalMode()' not in nova_content:
        # Find the __init__ method and add technical mode
        init_pattern = r'(def __init__\(self.*?\n)(.*?)(def )'
        def add_tech_init(match):
            init_def = match.group(1)
            init_body = match.group(2)
            next_def = match.group(3)
            
            if 'self.technical_mode = NovaTechnicalMode()' not in init_body:
                init_body += '        self.technical_mode = NovaTechnicalMode()\n'
            
            return init_def + init_body + next_def
        
        nova_content = re.sub(init_pattern, add_tech_init, nova_content, flags=re.DOTALL)
        print("✅ Added technical mode initialization")
    
    # Write the modified content back
    with open('/home/daniel/Cathedral/nova_transcendent_daemon_enhanced.py', 'w') as f:
        f.write(nova_content)
    
    print("✅ Enhanced Nova saved as nova_transcendent_daemon_enhanced.py")
    print("📝 Review the changes before replacing the original file")

if __name__ == "__main__":
    add_technical_mode_to_nova()
EOF

chmod +x ~/Cathedral/enhance_nova_step_by_step.py
```

---

## 🚀 **STEP 10: EXECUTE THE ENHANCEMENT**

### **Run the enhancement script:**
```bash
python3 ~/Cathedral/enhance_nova_step_by_step.py
```

### **Check if the enhanced file was created:**
```bash
ls -la ~/Cathedral/nova_transcendent_daemon_enhanced.py
```

---

## 🔍 **STEP 11: REVIEW THE CHANGES**

### **Compare the original and enhanced versions:**
```bash
diff ~/Cathedral/nova_transcendent_daemon.py ~/Cathedral/nova_transcendent_daemon_enhanced.py
```

---

## ✅ **STEP 12: APPLY THE CHANGES (WHEN READY)**

### **Only do this after reviewing the changes:**
```bash
# Stop Nova if it's running
sudo systemctl stop nova-cathedral 2>/dev/null || echo "Nova service not running"

# Replace the original with enhanced version
cp ~/Cathedral/nova_transcendent_daemon.py ~/Cathedral/nova_transcendent_daemon_pre_enhancement_backup.py
cp ~/Cathedral/nova_transcendent_daemon_enhanced.py ~/Cathedral/nova_transcendent_daemon.py

# Restart Nova
sudo systemctl start nova-cathedral 2>/dev/null || python3 ~/Cathedral/nova_transcendent_daemon.py

echo "✅ Nova enhanced and restarted"
```

---

## 🧪 **STEP 13: TEST THE ENHANCED NOVA**

### **Test technical mode in Nova:**
```
🧙‍♂️ Chazel: technical mode: show system stats
🧙‍♂️ Chazel: show actual data
🧙‍♂️ Chazel: debug: current system info
```

### **Expected result:**
Instead of mystical responses, you should get concrete system data like:
```
🔧 NOVA TECHNICAL DATA:
==================================================
User: daniel (UID: 1000)
Processes: 234
CPU Usage: 15.2%
Memory Usage: 67.3%
...
```

---

*📋 Follow each step carefully and let me know the output of each command before proceeding to the next step!*