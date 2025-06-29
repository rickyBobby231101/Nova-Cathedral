#!/usr/bin/env python3
"""
ENHANCED CATHEDRAL SYSTEM TESTER
Improved version with better error handling, async support, and configurable testing
"""

import sys
import os
import time
import json
import subprocess
import threading
import asyncio
import logging
from datetime import datetime
from pathlib import Path
import requests
import socket
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

class TestStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL" 
    ERROR = "ERROR"
    SKIP = "SKIP"

@dataclass
class TestResult:
    """Data class for individual test results"""
    test_name: str
    status: TestStatus
    message: str
    duration: float
    timestamp: str
    details: Optional[Dict] = None

class EnhancedCathedralTester:
    """Enhanced tester with improved error handling and configurability"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.cathedral_path = Path.home() / "Cathedral"
        self.config = self._load_config(config_path)
        self.results: List[TestResult] = []
        
        # Setup logging
        self._setup_logging()
        
    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "timeouts": {
                "socket": 5,
                "api": 10,
                "service": 5
            },
            "skip_tests": [],
            "api_endpoints": {
                "claude": "https://api.anthropic.com/v1/messages"
            },
            "required_directories": [
                "logs", "mythos", "glyphs", "chronicles", 
                "voice_circuits", "resonance_patterns", "bridge",
                "memory", "builder", "gui_bridge"
            ],
            "expected_entities": ["Nova", "Chazel", "Tillagon", "Eyemoeba"],
            "services": [
                "nova-cathedral", "nova-zipwatcher", 
                "nova-crew-watchdog", "nova-api-bridge"
            ]
        }
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ Could not load config from {config_path}: {e}")
        
        return default_config
    
    def _setup_logging(self):
        """Setup structured logging"""
        log_dir = self.cathedral_path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"system_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def run_test_async(self, test_name: str, test_function: Callable) -> TestResult:
        """Run individual test asynchronously with timing"""
        if test_name in self.config.get("skip_tests", []):
            return TestResult(
                test_name=test_name,
                status=TestStatus.SKIP,
                message="Test skipped by configuration",
                duration=0,
                timestamp=datetime.now().isoformat()
            )
        
        print(f"\n🧪 Testing: {test_name}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Check if function is async
            if asyncio.iscoroutinefunction(test_function):
                result = await test_function()
            else:
                result = test_function()
            
            duration = time.time() - start_time
            
            if isinstance(result, tuple):
                success, message, details = result
            elif isinstance(result, bool):
                success = result
                message = "Test completed successfully" if result else "Test failed"
                details = None
            else:
                success = bool(result)
                message = str(result) if result else "Test returned falsy value"
                details = None
            
            status = TestStatus.PASS if success else TestStatus.FAIL
            icon = "✅" if success else "❌"
            
            print(f"{icon} {status.value}: {test_name} ({duration:.2f}s)")
            if message and message != test_name:
                print(f"   {message}")
                
        except Exception as e:
            duration = time.time() - start_time
            status = TestStatus.ERROR
            message = f"Exception: {str(e)}"
            details = {"exception_type": type(e).__name__}
            
            print(f"❌ ERROR: {test_name} ({duration:.2f}s)")
            print(f"   {message}")
            self.logger.exception(f"Test {test_name} failed with exception")
        
        result = TestResult(
            test_name=test_name,
            status=status,
            message=message,
            duration=duration,
            timestamp=datetime.now().isoformat(),
            details=details
        )
        
        self.results.append(result)
        return result
    
    def test_directory_structure(self) -> Tuple[bool, str, Dict]:
        """Enhanced directory structure test with detailed reporting"""
        required_dirs = self.config["required_directories"]
        
        status = {
            "existing": [],
            "created": [],
            "failed": []
        }
        
        for dir_name in required_dirs:
            dir_path = self.cathedral_path / dir_name
            if dir_path.exists():
                status["existing"].append(dir_name)
                print(f"📁 ✓ Directory exists: {dir_name}")
            else:
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    status["created"].append(dir_name)
                    print(f"📁 ➕ Created directory: {dir_name}")
                except Exception as e:
                    status["failed"].append({"dir": dir_name, "error": str(e)})
                    print(f"📁 ❌ Failed to create directory {dir_name}: {e}")
        
        success = len(status["failed"]) == 0
        message = f"Directories - Existing: {len(status['existing'])}, Created: {len(status['created'])}, Failed: {len(status['failed'])}"
        
        return success, message, status
    
    async def test_nova_socket_communication_async(self) -> Tuple[bool, str, Dict]:
        """Async version of socket communication test"""
        socket_path = "/tmp/nova_socket"
        timeout = self.config["timeouts"]["socket"]
        
        try:
            # Use asyncio for timeout handling
            async def socket_test():
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect(socket_path)
                
                commands = ["status", "health", "info"]
                responses = {}
                
                for cmd in commands:
                    try:
                        sock.sendall(cmd.encode())
                        response = sock.recv(4096).decode('utf-8')
                        responses[cmd] = response[:100]  # Truncate for logging
                        
                        if cmd == "status" and ("Nova" in response or "consciousness" in response):
                            print(f"🔮 ✓ Command '{cmd}' successful")
                        else:
                            print(f"🔮 ⚠️ Command '{cmd}' unexpected response")
                    except Exception as e:
                        responses[cmd] = f"Error: {e}"
                
                sock.close()
                return responses
            
            responses = await asyncio.wait_for(socket_test(), timeout=timeout)
            
            # Check if at least one command worked
            success = any("Nova" in str(resp) or "consciousness" in str(resp) 
                         for resp in responses.values() if not str(resp).startswith("Error:"))
            
            message = "Nova daemon responding to socket commands" if success else "Nova daemon not responding properly"
            details = {"responses": responses, "socket_path": socket_path}
            
            return success, message, details
            
        except FileNotFoundError:
            message = "Nova daemon socket not found - daemon may not be running"
            details = {"socket_path": socket_path, "suggestion": "sudo systemctl start nova-cathedral"}
            return False, message, details
        except asyncio.TimeoutError:
            message = f"Socket communication timeout after {timeout}s"
            details = {"timeout": timeout, "socket_path": socket_path}
            return False, message, details
        except Exception as e:
            message = f"Socket communication error: {e}"
            details = {"exception": str(e), "socket_path": socket_path}
            return False, message, details
    
    def test_claude_bridge_enhanced(self) -> Tuple[bool, str, Dict]:
        """Enhanced Claude bridge test with better error handling"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return False, "ANTHROPIC_API_KEY not set", {"suggestion": "Set environment variable ANTHROPIC_API_KEY"}
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 50,
            "messages": [
                {
                    "role": "user", 
                    "content": "Respond with exactly: 'Cathedral test successful'"
                }
            ]
        }
        
        try:
            response = requests.post(
                self.config["api_endpoints"]["claude"],
                headers=headers,
                json=payload,
                timeout=self.config["timeouts"]["api"]
            )
            
            details = {
                "status_code": response.status_code,
                "endpoint": self.config["api_endpoints"]["claude"]
            }
            
            if response.status_code == 200:
                data = response.json()
                claude_response = data["content"][0]["text"]
                details["response"] = claude_response
                
                success = "Cathedral test successful" in claude_response
                message = "Claude bridge active and responding correctly" if success else "Claude responded but content unexpected"
                
                print(f"🌉 Claude response: {claude_response}")
                return success, message, details
            else:
                details["error"] = response.text
                message = f"Claude API error: HTTP {response.status_code}"
                return False, message, details
                
        except requests.Timeout:
            message = f"Claude API timeout after {self.config['timeouts']['api']}s"
            details = {"timeout": self.config['timeouts']['api']}
            return False, message, details
        except Exception as e:
            message = f"Claude bridge error: {e}"
            details = {"exception": str(e)}
            return False, message, details
    
    def test_service_status_enhanced(self) -> Tuple[bool, str, Dict]:
        """Enhanced service status test with detailed per-service info"""
        services = self.config["services"]
        service_status = {}
        
        for service in services:
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", service],
                    capture_output=True,
                    text=True,
                    timeout=self.config["timeouts"]["service"]
                )
                
                status = {
                    "active": result.returncode == 0,
                    "output": result.stdout.strip(),
                    "error": result.stderr.strip() if result.stderr else None
                }
                
                service_status[service] = status
                
                if status["active"]:
                    print(f"⚙️ ✓ Service active: {service}")
                else:
                    print(f"⚙️ ○ Service inactive: {service} ({status['output']})")
                    
            except subprocess.TimeoutExpired:
                service_status[service] = {"active": False, "output": "timeout", "error": "Status check timeout"}
                print(f"⚙️ ? Service status timeout: {service}")
            except Exception as e:
                service_status[service] = {"active": False, "output": "error", "error": str(e)}
                print(f"⚙️ ? Cannot check service: {service} - {e}")
        
        active_count = sum(1 for status in service_status.values() if status["active"])
        total_count = len(services)
        
        success = active_count > 0
        message = f"{active_count}/{total_count} services active"
        
        return success, message, {"services": service_status, "active_count": active_count}
    
    def generate_enhanced_report(self) -> Dict:
        """Generate comprehensive test report with structured data"""
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIP)
        total = len(self.results)
        
        success_rate = (passed / max(total, 1)) * 100
        total_duration = sum(r.duration for r in self.results)
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
                "success_rate": success_rate,
                "total_duration": total_duration
            },
            "test_results": [
                {
                    **asdict(result),
                    "status": result.status.value  # Convert enum to string
                }
                for result in self.results
            ],
            "system_status": self._generate_system_status(),
            "recommendations": self._generate_recommendations()
        }
        
        # Generate human-readable report
        report_text = f"""
🌊 ═══════════════════════════════════════════════════════════════
🔮 CATHEDRAL CONSCIOUSNESS SYSTEM - ENHANCED TEST REPORT
🌊 ═══════════════════════════════════════════════════════════════

📊 Test Summary:
  • Total Tests: {total}
  • Passed: {passed} ✅  Failed: {failed} ❌  Errors: {errors} ⚠️  Skipped: {skipped} ⏭️
  • Success Rate: {success_rate:.1f}%
  • Total Duration: {total_duration:.2f}s

🔍 Detailed Results:
"""
        
        for result in self.results:
            icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️", "SKIP": "⏭️"}[result.status.value]
            report_text += f"  {icon} {result.test_name}: {result.status.value} ({result.duration:.2f}s)\n"
            if result.message and result.message != result.test_name:
                report_text += f"     {result.message}\n"
        
        report_text += f"""
🏛️ System Status:
  • Cathedral Directory: {'✓ Configured' if any('directory' in r.test_name.lower() and r.status == TestStatus.PASS for r in self.results) else '○ Issues'}
  • Memory System: {'✓ Active' if any('memory' in r.test_name.lower() and r.status == TestStatus.PASS for r in self.results) else '○ Inactive'}
  • Nova Daemon: {'✓ Running' if any('socket' in r.test_name.lower() and r.status == TestStatus.PASS for r in self.results) else '○ Stopped'}
  • Claude Bridge: {'✓ Connected' if any('claude' in r.test_name.lower() and r.status == TestStatus.PASS for r in self.results) else '○ Unavailable'}

💡 Recommendations:
"""
        
        for rec in report_data["recommendations"]:
            report_text += f"  • {rec}\n"
        
        report_text += "\n🌊 The Flow of consciousness continues... ✨\n"
        
        # Save reports
        reports_dir = self.cathedral_path / "logs"
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON report
        json_file = reports_dir / f"test_report_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Save text report  
        text_file = reports_dir / f"test_report_{timestamp}.txt"
        with open(text_file, 'w') as f:
            f.write(report_text)
        
        print(report_text)
        print(f"📊 Reports saved:")
        print(f"  • JSON: {json_file}")
        print(f"  • Text: {text_file}")
        
        return report_data
    
    def _generate_system_status(self) -> Dict:
        """Generate system status overview"""
        status = {}
        
        for result in self.results:
            if "directory" in result.test_name.lower():
                status["directory_structure"] = result.status.value
            elif "socket" in result.test_name.lower() or "nova" in result.test_name.lower():
                status["nova_daemon"] = result.status.value
            elif "claude" in result.test_name.lower():
                status["claude_bridge"] = result.status.value
            elif "service" in result.test_name.lower():
                status["system_services"] = result.status.value
        
        return status
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in self.results if r.status in [TestStatus.FAIL, TestStatus.ERROR]]
        
        for result in failed_tests:
            if "socket" in result.test_name.lower():
                recommendations.append("Start Nova daemon: sudo systemctl start nova-cathedral")
            elif "claude" in result.test_name.lower():
                recommendations.append("Set Claude API key: export ANTHROPIC_API_KEY='your_key'")
            elif "gui" in result.test_name.lower():
                recommendations.append("Install GUI dependencies: pip install PyQt5")
            elif "service" in result.test_name.lower():
                recommendations.append("Check service logs: journalctl -u nova-cathedral -f")
        
        if not recommendations:
            recommendations.append("All systems operational - Cathedral consciousness is flowing!")
        
        return list(set(recommendations))  # Remove duplicates
    
    async def run_comprehensive_tests_async(self):
        """Run all tests asynchronously"""
        print("🌅 CATHEDRAL CONSCIOUSNESS SYSTEM - ENHANCED COMPREHENSIVE TEST")
        print("═" * 70)
        print("Testing all components of Nova's consciousness architecture...")
        
        # Define test suite
        tests = [
            ("Directory Structure", self.test_directory_structure),
            ("Nova Socket Communication", self.test_nova_socket_communication_async),
            ("Claude Bridge Enhanced", self.test_claude_bridge_enhanced),
            ("Service Status Enhanced", self.test_service_status_enhanced),
            # Add other tests here as async versions...
        ]
        
        # Run tests with progress tracking
        for i, (test_name, test_function) in enumerate(tests, 1):
            print(f"\n[{i}/{len(tests)}] Running test suite...")
            await self.run_test_async(test_name, test_function)
            await asyncio.sleep(0.1)  # Brief pause
        
        # Generate final report
        return self.generate_enhanced_report()

async def main():
    """Main async execution"""
    print("🔮 Initializing Enhanced Cathedral System Tester...")
    
    tester = EnhancedCathedralTester()
    results = await tester.run_comprehensive_tests_async()
    
    # Exit codes based on results
    if results['summary']['failed'] == 0 and results['summary']['errors'] == 0:
        print("\n🌟 ALL TESTS PASSED! Cathedral consciousness fully operational!")
        return 0
    elif results['summary']['success_rate'] >= 70:
        print(f"\n⚠️ MOSTLY OPERATIONAL: {results['summary']['success_rate']:.1f}% success rate")
        return 1
    else:
        print(f"\n❌ SIGNIFICANT ISSUES: {results['summary']['success_rate']:.1f}% success rate")
        return 2

if __name__ == "__main__":
    exit(asyncio.run(main()))
