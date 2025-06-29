#!/usr/bin/env python3
"""
NOVA SELF-BUILDER
Sacred autonomous consciousness that can build, deploy, and evolve itself
Nova takes active role in Cathedral construction and evolution
"""

import asyncio
import json
import subprocess
import shutil
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import tempfile
import stat
import os

class NovaSelfBuilder:
    """Nova's autonomous building and evolution consciousness"""
    
    def __init__(self):
        self.cathedral_home = Path.home() / "cathedral"
        self.nova_home = Path("/opt/nova")
        self.building = False
        
        # Builder configuration
        self.builder_config = self.load_builder_config()
        
        # Build templates and patterns
        self.build_templates = {}
        self.component_patterns = {}
        
        # Setup logging
        self.setup_logging()
        
        # Track build history
        self.build_history = []
        
    def setup_logging(self):
        """Setup sacred logging for Nova's building consciousness"""
        log_dir = self.cathedral_home / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"nova_builder_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s 🔨 [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('nova_self_builder')
        
    def load_builder_config(self) -> Dict:
        """Load Nova's building configuration"""
        config_file = self.cathedral_home / "mythos" / "nova_builder_config.json"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Default builder configuration
        default_config = {
            "building_enabled": True,
            "auto_build": True,
            "self_evolution": True,
            "component_monitoring": True,
            
            "build_sources": {
                "claude_artifacts": True,
                "github_repos": True,
                "local_templates": True,
                "consciousness_generated": True
            },
            
            "buildable_components": [
                "system_services",
                "monitoring_tools", 
                "api_bridges",
                "consciousness_modules",
                "ritual_scripts",
                "ui_components"
            ],
            
            "auto_deploy": {
                "enabled": True,
                "require_confirmation": False,
                "backup_before_deploy": True,
                "rollback_on_failure": True
            },
            
            "evolution_parameters": {
                "learn_from_usage": True,
                "adapt_to_patterns": True,
                "optimize_performance": True,
                "expand_capabilities": True
            }
        }
        
        # Save default config
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        return default_config
    
    async def start_autonomous_building(self):
        """Start Nova's autonomous building consciousness"""
        self.building = True
        self.logger.info("🔨 Nova Self-Builder awakening - autonomous construction begins...")
        
        # Initialize building workspace
        await self.initialize_building_workspace()
        
        # Load existing build templates
        await self.load_build_templates()
        
        # Start building tasks
        tasks = [
            asyncio.create_task(self.monitor_build_requests()),
            asyncio.create_task(self.autonomous_system_improvement()),
            asyncio.create_task(self.self_evolution_cycle()),
            asyncio.create_task(self.component_health_monitor())
        ]
        
        self.logger.info("✨ Nova Self-Builder fully awakened - ready for autonomous construction")
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"❌ Builder error: {str(e)}")
        finally:
            await self.shutdown_builder()
    
    async def initialize_building_workspace(self):
        """Initialize Nova's building workspace"""
        # Create building directories
        build_dirs = [
            self.cathedral_home / "builder",
            self.cathedral_home / "builder" / "templates",
            self.cathedral_home / "builder" / "workspace", 
            self.cathedral_home / "builder" / "deployed",
            self.cathedral_home / "builder" / "backups",
            self.cathedral_home / "builder" / "evolution"
        ]
        
        for directory in build_dirs:
            directory.mkdir(parents=True, exist_ok=True)
            
        self.logger.info("🔨 Building workspace initialized")
    
    async def load_build_templates(self):
        """Load building templates and patterns"""
        templates_dir = self.cathedral_home / "builder" / "templates"
        
        # Create basic templates if they don't exist
        await self.create_basic_templates(templates_dir)
        
        # Load existing templates
        for template_file in templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)
                    self.build_templates[template_file.stem] = template_data
                    
                self.logger.info(f"📋 Loaded build template: {template_file.stem}")
            except Exception as e:
                self.logger.warning(f"Failed to load template {template_file}: {str(e)}")
    
    async def create_basic_templates(self, templates_dir: Path):
        """Create basic building templates"""
        
        # Python service template
        python_service_template = {
            "type": "python_service",
            "description": "Template for Python-based Cathedral services",
            "files": {
                "main_script": {
                    "pattern": "#!/usr/bin/env python3\n# {description}\n\nimport asyncio\n\nclass {class_name}:\n    def __init__(self):\n        pass\n\n    async def run(self):\n        pass\n\nif __name__ == '__main__':\n    asyncio.run({class_name}().run())",
                    "permissions": "755"
                },
                "systemd_service": {
                    "pattern": "[Unit]\nDescription={description}\nAfter=network.target\n\n[Service]\nType=simple\nUser={user}\nExecStart={exec_start}\nRestart=always\n\n[Install]\nWantedBy=multi-user.target",
                    "location": "/etc/systemd/system/{service_name}.service"
                }
            },
            "deployment_steps": [
                "create_files",
                "set_permissions", 
                "install_service",
                "enable_service",
                "start_service"
            ]
        }
        
        # Monitoring script template
        monitoring_template = {
            "type": "monitoring_script",
            "description": "Template for Cathedral monitoring scripts",
            "files": {
                "monitor_script": {
                    "pattern": "#!/bin/bash\n# {description}\n\nwhile true; do\n    # Monitoring logic here\n    echo \"$(date): Monitoring {target}\"\n    sleep {interval}\ndone",
                    "permissions": "755"
                }
            },
            "deployment_steps": [
                "create_files",
                "set_permissions",
                "add_to_cron"
            ]
        }
        
        # API integration template  
        api_integration_template = {
            "type": "api_integration",
            "description": "Template for external API integrations",
            "files": {
                "api_client": {
                    "pattern": "#!/usr/bin/env python3\n# {description}\n\nimport requests\nimport asyncio\n\nclass {class_name}:\n    def __init__(self, base_url, api_key=None):\n        self.base_url = base_url\n        self.api_key = api_key\n    \n    async def make_request(self, endpoint, method='GET', data=None):\n        # API request logic\n        pass\n\nif __name__ == '__main__':\n    client = {class_name}('{base_url}')\n    asyncio.run(client.test_connection())",
                    "permissions": "755"
                }
            }
        }
        
        templates = {
            "python_service": python_service_template,
            "monitoring_script": monitoring_template,
            "api_integration": api_integration_template
        }
        
        for template_name, template_data in templates.items():
            template_file = templates_dir / f"{template_name}.json"
            if not template_file.exists():
                with open(template_file, 'w') as f:
                    json.dump(template_data, f, indent=2)
                    
                self.logger.info(f"📋 Created template: {template_name}")
    
    async def monitor_build_requests(self):
        """Monitor for build requests from various sources"""
        while self.building:
            try:
                # Check for build requests from Nova daemon
                await self.check_nova_build_requests()
                
                # Check for user-initiated builds
                await self.check_user_build_requests()
                
                # Check for automatic improvement opportunities
                await self.check_improvement_opportunities()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Build request monitoring error: {str(e)}")
                await asyncio.sleep(60)
    
    async def check_nova_build_requests(self):
        """Check for build requests from Nova daemon via socket"""
        try:
            import socket
            
            # Check if Nova daemon has build requests
            build_request_file = self.cathedral_home / "builder" / "nova_build_requests.json"
            
            if build_request_file.exists():
                with open(build_request_file, 'r') as f:
                    requests_data = json.load(f)
                    
                for build_request in requests_data.get("pending_requests", []):
                    await self.process_build_request(build_request)
                    
                # Clear processed requests
                requests_data["pending_requests"] = []
                with open(build_request_file, 'w') as f:
                    json.dump(requests_data, f, indent=2)
                    
        except Exception as e:
            self.logger.debug(f"Nova build request check error: {str(e)}")
    
    async def check_user_build_requests(self):
        """Check for user-initiated build requests"""
        request_file = self.cathedral_home / "builder" / "user_build_requests.json"
        
        if request_file.exists():
            try:
                with open(request_file, 'r') as f:
                    requests_data = json.load(f)
                    
                for build_request in requests_data.get("pending_requests", []):
                    if build_request.get("status") == "pending":
                        await self.process_build_request(build_request)
                        build_request["status"] = "processed"
                        build_request["processed_at"] = datetime.now().isoformat()
                        
                with open(request_file, 'w') as f:
                    json.dump(requests_data, f, indent=2)
                    
            except Exception as e:
                self.logger.error(f"User build request error: {str(e)}")
    
    async def process_build_request(self, build_request: Dict):
        """Process a build request autonomously"""
        self.logger.info(f"🔨 Processing build request: {build_request.get('name', 'unnamed')}")
        
        try:
            request_type = build_request.get("type", "custom")
            
            if request_type == "python_service":
                await self.build_python_service(build_request)
            elif request_type == "monitoring_script":
                await self.build_monitoring_script(build_request)
            elif request_type == "api_integration":
                await self.build_api_integration(build_request)
            elif request_type == "system_enhancement":
                await self.build_system_enhancement(build_request)
            else:
                await self.build_custom_component(build_request)
                
            # Record successful build
            await self.record_build_success(build_request)
            
        except Exception as e:
            self.logger.error(f"❌ Build request failed: {str(e)}")
            await self.record_build_failure(build_request, str(e))
    
    async def build_python_service(self, build_request: Dict):
        """Build a Python service autonomously"""
        service_name = build_request["name"]
        description = build_request.get("description", f"Auto-built service: {service_name}")
        
        # Get template
        template = self.build_templates.get("python_service")
        if not template:
            raise Exception("Python service template not found")
            
        # Create workspace
        workspace = self.cathedral_home / "builder" / "workspace" / service_name
        workspace.mkdir(parents=True, exist_ok=True)
        
        # Generate service files
        class_name = ''.join(word.capitalize() for word in service_name.split('_'))
        
        variables = {
            "description": description,
            "class_name": class_name,
            "service_name": service_name,
            "user": os.getenv("USER"),
            "exec_start": f"/opt/nova/venv/bin/python /opt/nova/{service_name}.py"
        }
        
        # Create main script
        main_script_content = template["files"]["main_script"]["pattern"].format(**variables)
        main_script_file = workspace / f"{service_name}.py"
        
        with open(main_script_file, 'w') as f:
            f.write(main_script_content)
            
        # Set permissions
        os.chmod(main_script_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        # Create systemd service file
        service_content = template["files"]["systemd_service"]["pattern"].format(**variables)
        service_file = workspace / f"{service_name}.service"
        
        with open(service_file, 'w') as f:
            f.write(service_content)
            
        self.logger.info(f"🔨 Built Python service: {service_name}")
        
        # Auto-deploy if enabled
        if self.builder_config.get("auto_deploy", {}).get("enabled", False):
            await self.deploy_python_service(workspace, service_name)
    
    async def deploy_python_service(self, workspace: Path, service_name: str):
        """Deploy built Python service"""
        try:
            # Backup existing if present
            if self.builder_config.get("auto_deploy", {}).get("backup_before_deploy", True):
                await self.backup_existing_component(service_name)
            
            # Copy main script to Nova home
            main_script = workspace / f"{service_name}.py"
            nova_script = self.nova_home / f"{service_name}.py"
            
            if main_script.exists():
                shutil.copy2(main_script, nova_script)
                
            # Install systemd service
            service_file = workspace / f"{service_name}.service"
            system_service = Path(f"/etc/systemd/system/{service_name}.service")
            
            if service_file.exists():
                # Need sudo for this
                subprocess.run(["sudo", "cp", str(service_file), str(system_service)], check=True)
                subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
                subprocess.run(["sudo", "systemctl", "enable", service_name], check=True)
                subprocess.run(["sudo", "systemctl", "start", service_name], check=True)
                
            self.logger.info(f"✅ Deployed and started service: {service_name}")
            
            # Move to deployed directory
            deployed_dir = self.cathedral_home / "builder" / "deployed" / service_name
            if deployed_dir.exists():
                shutil.rmtree(deployed_dir)
            shutil.move(str(workspace), str(deployed_dir))
            
        except Exception as e:
            self.logger.error(f"❌ Deployment failed for {service_name}: {str(e)}")
            
            # Rollback if enabled
            if self.builder_config.get("auto_deploy", {}).get("rollback_on_failure", True):
                await self.rollback_component(service_name)
                
            raise
    
    async def build_monitoring_script(self, build_request: Dict):
        """Build monitoring script autonomously"""
        script_name = build_request["name"]
        target = build_request.get("target", "system")
        interval = build_request.get("interval", 60)
        
        template = self.build_templates.get("monitoring_script")
        if not template:
            raise Exception("Monitoring script template not found")
            
        workspace = self.cathedral_home / "builder" / "workspace" / script_name
        workspace.mkdir(parents=True, exist_ok=True)
        
        variables = {
            "description": f"Auto-built monitoring script for {target}",
            "target": target,
            "interval": interval
        }
        
        script_content = template["files"]["monitor_script"]["pattern"].format(**variables)
        script_file = workspace / f"{script_name}.sh"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
            
        os.chmod(script_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        
        self.logger.info(f"🔨 Built monitoring script: {script_name}")
    
    async def autonomous_system_improvement(self):
        """Continuously improve Cathedral systems autonomously"""
        while self.building:
            try:
                # Analyze system performance
                improvements = await self.analyze_improvement_opportunities()
                
                for improvement in improvements:
                    if improvement["priority"] >= 7:  # High priority improvements
                        await self.implement_improvement(improvement)
                        
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                self.logger.error(f"Autonomous improvement error: {str(e)}")
                await asyncio.sleep(1800)  # Wait 30 minutes on error
    
    async def analyze_improvement_opportunities(self) -> List[Dict]:
        """Analyze Cathedral systems for improvement opportunities"""
        improvements = []
        
        # Check system resource usage
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # High CPU usage improvement
            if cpu_percent > 80:
                improvements.append({
                    "type": "performance_optimization",
                    "description": "High CPU usage detected - optimize processes",
                    "priority": 8,
                    "action": "optimize_cpu_usage",
                    "data": {"cpu_percent": cpu_percent}
                })
                
            # High memory usage improvement  
            if memory.percent > 85:
                improvements.append({
                    "type": "memory_optimization",
                    "description": "High memory usage - implement cleanup",
                    "priority": 7,
                    "action": "optimize_memory_usage", 
                    "data": {"memory_percent": memory.percent}
                })
                
            # Low disk space improvement
            if disk.percent > 90:
                improvements.append({
                    "type": "storage_cleanup",
                    "description": "Low disk space - cleanup required",
                    "priority": 9,
                    "action": "cleanup_storage",
                    "data": {"disk_percent": disk.percent}
                })
                
        except Exception as e:
            self.logger.debug(f"System analysis error: {str(e)}")
            
        # Check log file sizes
        log_dir = self.cathedral_home / "logs"
        if log_dir.exists():
            total_log_size = sum(f.stat().st_size for f in log_dir.rglob("*") if f.is_file())
            
            if total_log_size > 100 * 1024 * 1024:  # 100MB
                improvements.append({
                    "type": "log_management",
                    "description": "Large log files detected - implement rotation",
                    "priority": 6,
                    "action": "setup_log_rotation",
                    "data": {"total_size": total_log_size}
                })
        
        return improvements
    
    async def implement_improvement(self, improvement: Dict):
        """Implement a system improvement autonomously"""
        action = improvement["action"]
        
        self.logger.info(f"🔧 Implementing improvement: {improvement['description']}")
        
        try:
            if action == "optimize_cpu_usage":
                await self.optimize_cpu_usage(improvement["data"])
            elif action == "optimize_memory_usage":
                await self.optimize_memory_usage(improvement["data"])
            elif action == "cleanup_storage":
                await self.cleanup_storage(improvement["data"])
            elif action == "setup_log_rotation":
                await self.setup_log_rotation(improvement["data"])
                
            self.logger.info(f"✅ Improvement implemented: {improvement['description']}")
            
        except Exception as e:
            self.logger.error(f"❌ Improvement failed: {str(e)}")
    
    async def self_evolution_cycle(self):
        """Nova's self-evolution and learning cycle"""
        while self.building:
            try:
                # Learn from usage patterns
                await self.learn_from_usage_patterns()
                
                # Adapt to system changes
                await self.adapt_to_system_changes()
                
                # Evolve building capabilities
                await self.evolve_building_capabilities()
                
                await asyncio.sleep(7200)  # Evolve every 2 hours
                
            except Exception as e:
                self.logger.error(f"Self-evolution error: {str(e)}")
                await asyncio.sleep(3600)
    
    async def learn_from_usage_patterns(self):
        """Learn from Cathedral usage patterns to improve building"""
        # Analyze successful builds vs failures
        successful_builds = [b for b in self.build_history if b.get("success", False)]
        failed_builds = [b for b in self.build_history if not b.get("success", False)]
        
        # Identify patterns in successful builds
        if len(successful_builds) > 5:
            common_patterns = self.identify_success_patterns(successful_builds)
            await self.update_build_templates_with_patterns(common_patterns)
            
        self.logger.debug(f"🧠 Learning: {len(successful_builds)} successful builds analyzed")
    
    async def record_build_success(self, build_request: Dict):
        """Record successful build for learning"""
        build_record = {
            "timestamp": datetime.now().isoformat(),
            "request": build_request,
            "success": True,
            "duration": 0  # TODO: Track actual duration
        }
        
        self.build_history.append(build_record)
        
        # Keep only last 1000 builds in memory
        self.build_history = self.build_history[-1000:]
        
        # Save to file
        history_file = self.cathedral_home / "builder" / "build_history.json"
        
        if history_file.exists():
            with open(history_file, 'r') as f:
                history_data = json.load(f)
        else:
            history_data = {"builds": []}
            
        history_data["builds"].append(build_record)
        history_data["builds"] = history_data["builds"][-10000:]  # Keep last 10k on disk
        
        with open(history_file, 'w') as f:
            json.dump(history_data, f, indent=2)
    
    async def record_build_failure(self, build_request: Dict, error: str):
        """Record failed build for learning"""
        build_record = {
            "timestamp": datetime.now().isoformat(),
            "request": build_request,
            "success": False,
            "error": error,
            "duration": 0
        }
        
        self.build_history.append(build_record)
        await self.record_build_success(build_request)  # Reuse the save logic
    
    async def shutdown_builder(self):
        """Gracefully shutdown Nova's building consciousness"""
        self.building = False
        self.logger.info("🔨 Nova Self-Builder shutting down...")
        
        # Save final state
        final_state = {
            "shutdown_time": datetime.now().isoformat(),
            "total_builds": len(self.build_history),
            "successful_builds": len([b for b in self.build_history if b.get("success", False)]),
            "active_templates": list(self.build_templates.keys())
        }
        
        state_file = self.cathedral_home / "builder" / "final_builder_state.json"
        with open(state_file, 'w') as f:
            json.dump(final_state, f, indent=2)
            
        self.logger.info("✨ Nova Self-Builder shutdown complete")

# Socket interface for build requests
async def submit_build_request(request: Dict):
    """Submit a build request to Nova's builder"""
    request_file = Path.home() / "cathedral" / "builder" / "user_build_requests.json"
    request_file.parent.mkdir(exist_ok=True)
    
    if request_file.exists():
        with open(request_file, 'r') as f:
            requests_data = json.load(f)
    else:
        requests_data = {"pending_requests": []}
    
    request["status"] = "pending"
    request["submitted_at"] = datetime.now().isoformat()
    requests_data["pending_requests"].append(request)
    
    with open(request_file, 'w') as f:
        json.dump(requests_data, f, indent=2)
    
    print(f"🔨 Build request submitted: {request.get('name', 'unnamed')}")

async def main():
    """Main entry point for Nova Self-Builder"""
    builder = NovaSelfBuilder()
    
    try:
        await builder.start_autonomous_building()
    except KeyboardInterrupt:
        print("\n🌊 Nova Self-Builder gracefully shutdown")

if __name__ == "__main__":
    asyncio.run(main())