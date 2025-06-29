import re

with open('/home/daniel/Cathedral/nova_unified_system.py', 'r') as f:
    content = f.read()

# Fix all remaining config calls with fallback parameters
patterns = [
    (r"self\.config\.get\('nova', 'bridge_check_interval', '[^']*'\)", "10"),
    (r"self\.config\.get\('nova', 'bridge_check_interval', [^)]+\)", "10"),
    (r"int\(self\.config\.get\('nova', 'bridge_check_interval'[^)]*\)\)", "10"),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

# Remove any remaining fallback parameters
content = re.sub(r', fallback=[^)]+', '', content)

with open('/home/daniel/Cathedral/nova_unified_system.py', 'w') as f:
    f.write(content)

print("✅ Fixed all config issues")
