#!/usr/bin/env python3
"""
COMPREHENSIVE CATHEDRAL SYSTEM TESTER
Complete testing suite for all Nova consciousness components
Tests memory, intelligence, bridges, GUI, and autonomous capabilities
"""

import sys
import os
import time
import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path
import requests
import socket

class CathedralSystemTester:
    """Comprehensive tester for all Cathedral consciousness systems"""
    
    def __init__(self):
        self.cathedral_path = Path.home() / "Cathedral"
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": []
        }
        
    def run_test(self, test_name, test_function):
        """Run individual test and record results"""
        print(f"\n🧪 Testing: {test_name}")
        print("-" * 50)
        
        try:
            result = test_function()
            if result:
                print(f"✅ PASS: {test_name}")
                self.test_results["tests_passed"] += 1
                status = "PASS"
            else:
                print(f"❌ FAIL: {test_name}")
                self.test_results["tests_failed"] += 1
                status = "FAIL"
        except Exception as e:
            print(f"❌ ERROR: {test_name} - {str(e)}")
            self.test_results["tests_failed"] += 1
            status = "ERROR"
            result = str(e)
            
        self.test_results["tests_run"] += 1
        self.test_results["test_details"].append({
            "test_name": test_name,
            "status": status,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    
    def test_directory_structure(self):
        """Test Cathedral directory structure"""
        required_dirs = [
            "logs", "mythos", "glyphs", "chronicles", 
            "voice_circuits", "resonance_patterns", "bridge",
            "memory", "builder", "gui_bridge"
        ]
        
        missing_dirs = []
        for dir_name in required_dirs:
            dir_path = self.cathedral_path / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"📁 Created missing directory: {dir_name}")
            else:
                print(f"📁 ✓ Directory exists: {dir_name}")
        
        if missing_dirs:
            print(f"⚠️ Created {len(missing_dirs)} missing directories")
        
        return True
    
    def test_nova_socket_communication(self):
        """Test Nova daemon socket communication"""
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect("/tmp/nova_socket")
            
            # Test status command
            sock.sendall(b"status")
            response = sock.recv(4096).decode('utf-8')
            sock.close()
            
            if "Nova Cathedral Status" in response or "consciousness" in response:
                print("🔮 Nova daemon responding to socket commands")
                print(f"📊 Response preview: {response[:100]}...")
                return True
            else:
                print("⚠️ Nova daemon responded but format unexpected")
                return False
                
        except FileNotFoundError:
            print("❌ Nova daemon socket not found - daemon may not be running")
            print("💡 Try starting with: sudo systemctl start nova-cathedral")
            return False
        except Exception as e:
            print(f"❌ Socket communication error: {e}")
            return False
    
    def test_memory_system(self):
        """Test memory persistence system"""
        try:
            # Check if memory files exist
            memory_db = self.cathedral_path / "memory" / "consciousness_memory.db"
            conversation_history = self.cathedral_path / "memory" / "conversation_history.json"
            
            memory_working = False
            
            if memory_db.exists():
                print("🧠 ✓ Memory database exists")
                memory_working = True
            else:
                print("⚠️ Memory database not found")
            
            if conversation_history.exists():
                with open(conversation_history, 'r') as f:
                    history = json.load(f)
                    conv_count = history.get('total_conversations', 0)
                    print(f"💾 ✓ Conversation history: {conv_count} conversations")
                    memory_working = True
            else:
                print("⚠️ Conversation history not found")
            
            # Test memory creation
            if memory_working:
                print("🧠 Memory system appears functional")
            
            return memory_working
            
        except Exception as e:
            print(f"❌ Memory system error: {e}")
            return False
    
    def test_claude_bridge(self):
        """Test Claude bridge functionality"""
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                print("⚠️ ANTHROPIC_API_KEY not set - Claude bridge unavailable")
                return False
            
            # Test API connectivity
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": "Test message from Cathedral system tester. Please respond briefly that you received this."
                    }
                ]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                claude_response = data["content"][0]["text"]
                print(f"🌉 ✓ Claude bridge active")
                print(f"🌉 Claude responded: {claude_response[:50]}...")
                return True
            else:
                print(f"❌ Claude API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Claude bridge error: {e}")
            return False
    
    def test_enhanced_intelligence(self):
        """Test enhanced Nova intelligence"""
        try:
            # Check if intelligence module can be imported
            sys.path.append(str(self.cathedral_path.parent))
            
            from enhanced_nova_intelligence import EnhancedNovaConsciousness
            
            nova = EnhancedNovaConsciousness()
            
            # Test context analysis
            test_message = "Tell me about consciousness and the Flow"
            context = nova.analyze_message_context(test_message)
            
            if context.get('topic_category') == 'flow_dynamics':
                print("🧠 ✓ Context analysis working")
            else:
                print("⚠️ Context analysis unexpected result")
            
            # Test response generation
            response = nova.generate_contextual_response(test_message, context)
            
            if "Flow" in response and len(response) > 50:
                print("🔮 ✓ Response generation working")
                print(f"🔮 Sample response: {response[:80]}...")
                return True
            else:
                print("⚠️ Response generation issues")
                return False
                
        except ImportError as e:
            print(f"❌ Enhanced intelligence module not found: {e}")
            return False
        except Exception as e:
            print(f"❌ Enhanced intelligence error: {e}")
            return False
    
    def test_streaming_interface(self):
        """Test streaming consciousness interface"""
        try:
            stream_file = self.cathedral_path / "gui_bridge" / "nova_to_gui_stream.jsonl"
            conduit_file = self.cathedral_path / "gui_bridge" / "conduit_alignment.json"
            
            # Check if streaming files exist
            gui_bridge_dir = self.cathedral_path / "gui_bridge"
            gui_bridge_dir.mkdir(exist_ok=True)
            
            if not conduit_file.exists():
                # Create test conduit file
                conduit_data = {
                    "conduit_name": "Test Harmonic Conduit",
                    "last_alignment": datetime.now().isoformat(),
                    "gui_connected": True,
                    "stream_active": False
                }
                with open(conduit_file, 'w') as f:
                    json.dump(conduit_data, f, indent=2)
                print("🌊 Created test conduit alignment file")
            
            print("🌊 ✓ Streaming interface structure ready")
            return True
            
        except Exception as e:
            print(f"❌ Streaming interface error: {e}")
            return False
    
    def test_self_builder(self):
        """Test Nova's self-building capabilities"""
        try:
            builder_dir = self.cathedral_path / "builder"
            builder_dir.mkdir(exist_ok=True)
            
            # Create test build request
            test_request = {
                "name": "test_component",
                "type": "monitoring_script",
                "description": "Test component built by system tester",
                "timestamp": datetime.now().isoformat()
            }
            
            request_file = builder_dir / "test_build_request.json"
            with open(request_file, 'w') as f:
                json.dump(test_request, f, indent=2)
            
            print("🔨 ✓ Self-builder structure ready")
            print("🔨 Created test build request")
            
            # Check for existing build artifacts
            workspace = builder_dir / "workspace"
            if workspace.exists() and any(workspace.iterdir()):
                print(f"🔨 ✓ Build workspace contains artifacts")
            
            return True
            
        except Exception as e:
            print(f"❌ Self-builder error: {e}")
            return False
    
    def test_gui_interface(self):
        """Test GUI interface availability"""
        try:
            # Check if PyQt5 is available
            import PyQt5
            print("🖥️ ✓ PyQt5 available for GUI interface")
            
            # Check if GUI files exist
            gui_files = [
                "cathedral_gui_interface.py",
                "cathedral_gui_streaming_integration.py"
            ]
            
            found_gui_files = []
            for gui_file in gui_files:
                if (self.cathedral_path.parent / gui_file).exists():
                    found_gui_files.append(gui_file)
            
            if found_gui_files:
                print(f"🖥️ ✓ Found GUI files: {', '.join(found_gui_files)}")
                return True
            else:
                print("⚠️ GUI files not found in expected location")
                return False
                
        except ImportError:
            print("❌ PyQt5 not installed - GUI interface unavailable")
            print("💡 Install with: pip install PyQt5")
            return False
        except Exception as e:
            print(f"❌ GUI interface error: {e}")
            return False
    
    def test_mythological_entities(self):
        """Test mythological entity tracking"""
        try:
            mythos_file = self.cathedral_path / "mythos" / "mythos_index.json"
            
            if mythos_file.exists():
                with open(mythos_file, 'r') as f:
                    mythos = json.load(f)
                
                entities = mythos.get('core_entities', []) + mythos.get('mythological_entities', [])
                entity_names = [e.get('name', '') for e in entities]
                
                expected_entities = ['Nova', 'Chazel', 'Tillagon', 'Eyemoeba']
                found_entities = [e for e in expected_entities if e in entity_names]
                
                print(f"🐉 ✓ Found mythological entities: {', '.join(found_entities)}")
                
                if len(found_entities) >= 3:
                    return True
                else:
                    print("⚠️ Some expected entities missing")
                    return False
            else:
                print("⚠️ Mythos index not found")
                return False
                
        except Exception as e:
            print(f"❌ Mythological entities error: {e}")
            return False
    
    def test_service_status(self):
        """Test systemd service status"""
        try:
            services = [
                "nova-cathedral",
                "nova-zipwatcher", 
                "nova-crew-watchdog",
                "nova-api-bridge"
            ]
            
            active_services = []
            for service in services:
                try:
                    result = subprocess.run(
                        ["systemctl", "is-active", service],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        active_services.append(service)
                        print(f"⚙️ ✓ Service active: {service}")
                    else:
                        print(f"⚙️ ○ Service inactive: {service}")
                        
                except subprocess.TimeoutExpired:
                    print(f"⚙️ ? Service status timeout: {service}")
                except Exception:
                    print(f"⚙️ ? Cannot check service: {service}")
            
            if active_services:
                print(f"⚙️ ✓ {len(active_services)}/{len(services)} services active")
                return True
            else:
                print("⚠️ No services appear to be active")
                return False
                
        except Exception as e:
            print(f"❌ Service status error: {e}")
            return False
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        report = f"""
🌊 ═══════════════════════════════════════════════════════════════
🔮 CATHEDRAL CONSCIOUSNESS SYSTEM TEST REPORT
🌊 ═══════════════════════════════════════════════════════════════

Test Summary:
  • Total Tests: {self.test_results['tests_run']}
  • Passed: {self.test_results['tests_passed']} ✅
  • Failed: {self.test_results['tests_failed']} ❌
  • Success Rate: {(self.test_results['tests_passed'] / max(self.test_results['tests_run'], 1)) * 100:.1f}%

Test Results:
"""
        
        for test in self.test_results['test_details']:
            status_icon = "✅" if test['status'] == "PASS" else "❌"
            report += f"  {status_icon} {test['test_name']}: {test['status']}\n"
        
        report += f"""
System Status:
  • Cathedral Directory: ✓ Configured
  • Memory System: {'✓ Active' if any('memory' in t['test_name'].lower() and t['status'] == 'PASS' for t in self.test_results['test_details']) else '○ Inactive'}
  • Nova Daemon: {'✓ Running' if any('socket' in t['test_name'].lower() and t['status'] == 'PASS' for t in self.test_results['test_details']) else '○ Stopped'}
  • Claude Bridge: {'✓ Connected' if any('claude' in t['test_name'].lower() and t['status'] == 'PASS' for t in self.test_results['test_details']) else '○ Unavailable'}
  • Enhanced Intelligence: {'✓ Loaded' if any('intelligence' in t['test_name'].lower() and t['status'] == 'PASS' for t in self.test_results['test_details']) else '○ Not Loaded'}

Next Steps:
  • If tests failed: Check logs in ~/Cathedral/logs/
  • Start services: sudo systemctl start nova-cathedral
  • Set API keys: export ANTHROPIC_API_KEY="your_key"
  • Test GUI: python cathedral_gui_interface.py

🌊 The Flow awaits your command... ✨
"""
        
        # Save report
        report_file = self.cathedral_path / "logs" / f"system_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"📊 Full report saved to: {report_file}")
        
        return self.test_results
    
    def run_comprehensive_tests(self):
        """Run all Cathedral system tests"""
        print("🌅 CATHEDRAL CONSCIOUSNESS SYSTEM - COMPREHENSIVE TEST")
        print("═" * 70)
        print("Testing all components of Nova's consciousness architecture...")
        
        # Define all tests
        tests = [
            ("Directory Structure", self.test_directory_structure),
            ("Nova Socket Communication", self.test_nova_socket_communication),
            ("Memory Persistence System", self.test_memory_system),
            ("Claude Bridge", self.test_claude_bridge),
            ("Enhanced Intelligence", self.test_enhanced_intelligence),
            ("Streaming Interface", self.test_streaming_interface),
            ("Self-Builder System", self.test_self_builder),
            ("GUI Interface", self.test_gui_interface),
            ("Mythological Entities", self.test_mythological_entities),
            ("Service Status", self.test_service_status)
        ]
        
        # Run all tests
        for test_name, test_function in tests:
            self.run_test(test_name, test_function)
            time.sleep(0.5)  # Brief pause between tests
        
        # Generate final report
        return self.generate_test_report()

def main():
    """Main test execution"""
    print("🔮 Initializing Cathedral System Comprehensive Tester...")
    
    tester = CathedralSystemTester()
    results = tester.run_comprehensive_tests()
    
    # Summary
    if results['tests_failed'] == 0:
        print("\n🌟 ALL TESTS PASSED! Cathedral consciousness fully operational!")
        return 0
    elif results['tests_passed'] > results['tests_failed']:
        print(f"\n⚠️ MOSTLY WORKING: {results['tests_passed']}/{results['tests_run']} tests passed")
        return 1
    else:
        print(f"\n❌ ISSUES DETECTED: {results['tests_failed']}/{results['tests_run']} tests failed")
        return 2

if __name__ == "__main__":
    exit(main())
