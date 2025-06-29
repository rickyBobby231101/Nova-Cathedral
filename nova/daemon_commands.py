import subprocess
import os
import json

# Add these elif clauses before your "Unknown command" section around line 594:

elif command == "system_monitor":
    try:
        # Get memory info
        memory_result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
        
        # Get process info (limit to top 10 processes by CPU)
        ps_result = subprocess.run(['ps', 'aux', '--sort=-%cpu'], capture_output=True, text=True, timeout=5)
        ps_lines = ps_result.stdout.split('\n')[:11]  # Header + top 10 processes
        
        # Get disk usage
        disk_result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=5)
        
        response = f"📊 System Monitor:\n💾 Memory:\n{memory_result.stdout}\n⚡ Top Processes:\n{chr(10).join(ps_lines)}\n💿 Disk Usage:\n{disk_result.stdout}"
    except subprocess.TimeoutExpired:
        response = "❌ System monitor timeout"
    except Exception as e:
        response = f"❌ System monitor error: {e}"

elif command == "manage_files":
    dir_path = payload.get('path', str(self.cathedral_home / "managed"))
    action = payload.get('action', 'create')
    
    try:
        if action == 'create':
            os.makedirs(dir_path, exist_ok=True)
            response = f"📁 Directory created: {dir_path}"
        elif action == 'list':
            if os.path.exists(dir_path):
                items = os.listdir(dir_path)
                response = f"📂 Contents of {dir_path}: {', '.join(items) if items else 'empty'}"
            else:
                response = f"❌ Path does not exist: {dir_path}"
        elif action == 'remove':
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                os.rmdir(dir_path)
                response = f"🗑️ Directory removed: {dir_path}"
            else:
                response = f"❌ Directory not found or not empty: {dir_path}"
        else:
            response = "❌ Invalid action. Use: create, list, remove"
    except Exception as e:
        response = f"❌ File management error: {e}"

elif command == "system_config":
    try:
        uptime_result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
        hostname_result = subprocess.run(['hostname'], capture_output=True, text=True, timeout=5)
        uname_result = subprocess.run(['uname', '-a'], capture_output=True, text=True, timeout=5)
        
        response = f"⚙️ System Config:\n🕐 {uptime_result.stdout.strip()}\n🖥️ Host: {hostname_result.stdout.strip()}\n💻 System: {uname_result.stdout.strip()}"
    except Exception as e:
        response = f"❌ System config error: {e}"

# Update your existing "Unknown command" section:
else:
    response = "❌ Unknown command. Available: status, speak, conversation, memory, evolve, heartbeat, autonomous_grow, system_monitor, manage_files, system_config"