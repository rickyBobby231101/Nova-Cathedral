# Simple fix for observer_enabled
import re

with open('/home/daniel/Cathedral/nova_unified_system.py', 'r') as f:
    content = f.read()

# Fix the syntax errors
content = content.replace("getboolean('nova', 'observer_enabled', ))", "getboolean('nova', 'observer_enabled')")
content = content.replace(", ))", ")")

with open('/home/daniel/Cathedral/nova_unified_system.py', 'w') as f:
    f.write(content)

print("✅ Fixed syntax errors")
