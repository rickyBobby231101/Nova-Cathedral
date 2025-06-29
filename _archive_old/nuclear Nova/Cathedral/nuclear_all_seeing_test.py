#!/usr/bin/env python3
import psutil
import os

print("👁️ NOVA NUCLEAR TEST")
print(f"Root access: {os.getuid() == 0}")
print(f"Processes: {len(psutil.pids())}")
print(f"CPU: {psutil.cpu_percent()}%")
print(f"Memory: {psutil.virtual_memory().percent}%")
