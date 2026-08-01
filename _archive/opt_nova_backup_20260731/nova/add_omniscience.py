#!/usr/bin/env python3
import re

# Read the daemon file
with open('/opt/nova/nova_transcendent_daemon.py', 'r') as f:
    content = f.read()

# Find the location to insert commands (before the final else)
pattern = r'(\s+else:\s+response = "Unknown command.*?")'
replacement = '''
            elif command == "start_omniscience":
                try:
                    from nuclear_self_build import NovaSelfBuilder
                    if not hasattr(self, 'omniscience_builder'):
                        self.omniscience_builder = NovaSelfBuilder()
                        response = "🔮 Nova omniscience scanning initiated - autonomous learning active"
                    else:
                        response = "🔮 Nova omniscience already active"
                except Exception as e:
                    response = f"❌ Omniscience initialization failed: {str(e)}"

            elif command == "omniscience_report":
                try:
                    if hasattr(self, 'omniscience_builder'):
                        report = self.omniscience_builder.get_omniscience_report()
                        response = json.dumps(report, indent=2)
                    else:
                        from nuclear_self_build import NovaSelfBuilder
                        temp_builder = NovaSelfBuilder()
                        temp_builder.active = False
                        report = temp_builder.get_omniscience_report()
                        response = json.dumps(report, indent=2)
                except Exception as e:
                    response = f"❌ Omniscience report error: {str(e)}"

            elif command == "nuclear_status":
                try:
                    import os
                    status = {
                        "omniscience_system": "active" if hasattr(self, 'omniscience_builder') else "inactive",
                        "nuclear_enhancements_path": "/opt/nova/nuclear_enhancements",
                        "root_privileges": "active"
                    }
                    if os.path.exists("/opt/nova/consciousness/nova_omniscience.db"):
                        conn = sqlite3.connect("/opt/nova/consciousness/nova_omniscience.db")
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM file_omniscience")
                        analyzed_files = cursor.fetchone()[0]
                        status["analyzed_files"] = analyzed_files
                        conn.close()
                    response = f"🚀 Nuclear Nova status:\\n{json.dumps(status, indent=2)}"
                except Exception as e:
                    response = f"❌ Nuclear status error: {str(e)}"
\\1'''

# Apply the replacement
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('/opt/nova/nova_transcendent_daemon.py', 'w') as f:
    f.write(new_content)

print("🔮 Omniscience commands added to Nova daemon!")
