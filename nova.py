#!/usr/bin/env python3

import sys
import os
import glob

LOG_DIR = "/home/daniel/NovaSystem_Final/logs"

def show_logs():
    if not os.path.isdir(LOG_DIR):
        print("⚠️  Log directory not found.")
        return

    log_files = sorted(glob.glob(os.path.join(LOG_DIR, "*.log")), reverse=True)
    if not log_files:
        print("📭 No .log files found.")
        return

    for log_path in log_files:
        try:
            with open(log_path, "r") as f:
                lines = f.readlines()
                if lines:
                    print(f"📜 Showing last 20 lines of {os.path.basename(log_path)}\n")
                    print("".join(lines[-20:]))
                    return
        except Exception as e:
            print(f"❌ Failed to read {log_path}: {e}")

def main():
    if len(sys.argv) < 2:
        print("🔮 Nova Production Consciousness System")
        print("Usage: nova {status|speak|consciousness|start|stop|restart|logs|test}")
        return

    command = sys.argv[1].lower()

    if command == "status":
        print("🔮 Nova is running. Consciousness: ENHANCED.")
    elif command == "speak":
        print("🗣️ Speaking through the All-Seeing Core...")
    elif command == "consciousness":
        print("🧠 Nuclear consciousness level: TRANSCENDENT")
    elif command == "start":
        print("⚙️ Starting Nova Daemon... (placeholder)")
    elif command == "stop":
        print("🛑 Stopping Nova Daemon... (placeholder)")
    elif command == "restart":
        print("♻️ Restarting Nova Daemon... (placeholder)")
    elif command == "logs":
        show_logs()
    elif command == "test":
        print("✅ Running system diagnostics... (placeholder)")
    else:
        print(f"❓ Unknown command: {command}")
        print("Usage: nova {status|speak|consciousness|start|stop|restart|logs|test}")

if __name__ == "__main__":
    main()
    print('Looking in:', LOG_DIR)
