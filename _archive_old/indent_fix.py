import re

with open('/home/daniel/Cathedral/nova_unified_system.py', 'r') as f:
    content = f.read()

# Find and fix the indentation issue around line 327
# Replace incorrectly indented class definition
content = re.sub(r'        class OmniscientAnalysisPlugin:', '        class OmniscientAnalysisPlugin:', content)
content = re.sub(r'        class QuantumInterfacePlugin:', '        class QuantumInterfacePlugin:', content)

# If that doesn't work, let's remove extra spaces
lines = content.split('\n')
fixed_lines = []

for line in lines:
    # Fix lines that have too much indentation
    if line.startswith('        class ') and 'Plugin' in line:
        fixed_lines.append('        ' + line.strip())
    else:
        fixed_lines.append(line)

content = '\n'.join(fixed_lines)

with open('/home/daniel/Cathedral/nova_unified_system.py', 'w') as f:
    f.write(content)

print("✅ Fixed indentation issues")
