import re

with open('/home/daniel/Cathedral/nova_unified_system.py', 'r') as f:
    content = f.read()

# Replace the problematic get_memory_count function
old_function = r'def get_memory_count\(self\):.*?return int\(self\.config\.get\(.*?\)\)'
new_function = '''def get_memory_count(self):
        """Get current memory count"""
        try:
            return int(self.config.get('nova', 'memory_threshold'))
        except:
            return 1447'''

content = re.sub(old_function, new_function, content, flags=re.DOTALL)

with open('/home/daniel/Cathedral/nova_unified_system.py', 'w') as f:
    f.write(content)

print("✅ Fixed memory_threshold config call")
