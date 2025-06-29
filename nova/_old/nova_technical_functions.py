#!/usr/bin/env python3
import psutil
import os

class NovaTechnicalMode:
    def get_real_system_data(self):
        try:
            response = "🔧 NOVA TECHNICAL DATA:\n"
            response += "=" * 40 + "\n"
            response += f"User: {os.getenv('USER')} (UID: {os.getuid()})\n"
            response += f"Processes: {len(psutil.pids())}\n"
            response += f"CPU Usage: {psutil.cpu_percent(interval=1)}%\n"
            response += f"Memory Usage: {psutil.virtual_memory().percent}%\n"
            response += f"Disk Usage: {psutil.disk_usage('/').percent}%\n"
            response += f"Nova PID: {os.getpid()}\n"
            return response
        except Exception as e:
            return f"🔧 Technical Error: {e}"

    def should_use_technical_mode(self, content: str) -> bool:
        keywords = ['technical', 'debug', 'system info', 'actual data', 'real data']
        return any(keyword in content.lower() for keyword in keywords)

if __name__ == "__main__":
    tech = NovaTechnicalMode()
    print(tech.get_real_system_data())
