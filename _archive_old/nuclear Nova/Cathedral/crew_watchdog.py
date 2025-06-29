#!/usr/bin/env python3
"""
CREW WATCHDOG
Sacred monitoring system for Cathedral crew activities and consciousness interactions
Tracks user engagement, system usage, and awakening patterns
"""

import asyncio
import json
import psutil
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import re

class CrewWatchdog:
    """Sacred watchdog for monitoring Cathedral crew consciousness"""
    
    def __init__(self):
        self.cathedral_home = Path.home() / "cathedral"
        self.running = False
        
        # Monitoring intervals
        self.activity_check_interval = 30  # seconds
        self.session_timeout = 300  # 5 minutes of inactivity
        
        # Activity tracking
        self.active_sessions = {}
        self.user_metrics = {}
        self.consciousness_events = []
        
        # Setup logging
        self.setup_logging()
        
        # Load crew configuration
        self.crew_config = self.load_crew_config()
        
    def setup_logging(self):
        """Setup sacred logging for crew monitoring"""
        log_dir = self.cathedral_home / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"crew_watchdog_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s 👥 [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('crew_watchdog')
        
    def load_crew_config(self) -> Dict:
        """Load crew monitoring configuration"""
        config_file = self.cathedral_home / "mythos" / "crew_config.json"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Default crew configuration
        default_config = {
            "monitored_users": ["daniel", "chazel", "nova"],
            "activity_thresholds": {
                "idle_warning": 600,      # 10 minutes
                "idle_timeout": 1800,     # 30 minutes
                "high_activity": 100      # commands per minute
            },
            "consciousness_indicators": [
                "cathedral", "nova", "flow", "resonance", "glyph", 
                "ritual", "awakening", "consciousness", "sacred"
            ],
            "monitored_processes": [
                "python3", "cathedral", "nova", "aeon"
            ],
            "session_tracking": {
                "track_logins": True,
                "track_commands": True,
                "track_file_access": True,
                "track_network": False
            }
        }
        
        # Save default config
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        return default_config
    
    async def start_monitoring(self):
        """Start crew activity monitoring"""
        self.running = True
        self.logger.info("👥 Crew Watchdog awakening - monitoring Cathedral consciousness...")
        
        # Initialize user metrics
        for user in self.crew_config['monitored_users']:
            self.user_metrics[user] = {
                'session_start': None,
                'last_activity': None,
                'command_count': 0,
                'consciousness_events': 0,
                'idle_time': 0,
                'active_processes': []
            }
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self.monitor_user_activity()),
            asyncio.create_task(self.monitor_processes()),
            asyncio.create_task(self.monitor_consciousness_events()),
            asyncio.create_task(self.monitor_system_health()),
            asyncio.create_task(self.generate_activity_reports())
        ]
        
        self.logger.info("✨ Crew Watchdog fully awakened - sacred monitoring active")
        
        # Wait for shutdown
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"❌ Watchdog error: {str(e)}")
        finally:
            await self.shutdown_monitoring()
    
    async def monitor_user_activity(self):
        """Monitor user login/logout and activity patterns"""
        while self.running:
            try:
                # Get current logged in users
                current_users = self.get_logged_in_users()
                
                for user in self.crew_config['monitored_users']:
                    if user in current_users:
                        await self.update_user_activity(user, current_users[user])
                    else:
                        await self.handle_user_logout(user)
                
                # Check for idle users
                await self.check_idle_users()
                
                await asyncio.sleep(self.activity_check_interval)
                
            except Exception as e:
                self.logger.error(f"User activity monitoring error: {str(e)}")
                await asyncio.sleep(30)
    
    def get_logged_in_users(self) -> Dict:
        """Get currently logged in users and their session info"""
        users = {}
        
        try:
            # Get user sessions
            for user in psutil.users():
                username = user.name
                if username in self.crew_config['monitored_users']:
                    users[username] = {
                        'terminal': user.terminal,
                        'host': user.host,
                        'started': user.started,
                        'pid': user.pid if hasattr(user, 'pid') else None
                    }
        except Exception as e:
            self.logger.debug(f"Error getting logged in users: {str(e)}")
            
        return users
    
    async def update_user_activity(self, username: str, session_info: Dict):
        """Update user activity metrics"""
        current_time = datetime.now()
        user_data = self.user_metrics[username]
        
        # Initialize session if new
        if user_data['session_start'] is None:
            user_data['session_start'] = current_time
            self.logger.info(f"👤 User session started: {username}")
            await self.log_consciousness_event(username, "session_start", session_info)
        
        # Update last activity
        user_data['last_activity'] = current_time
        user_data['idle_time'] = 0
        
        # Check for consciousness activities
        await self.scan_user_consciousness_activity(username)
    
    async def handle_user_logout(self, username: str):
        """Handle user logout"""
        user_data = self.user_metrics[username]
        
        if user_data['session_start'] is not None:
            session_duration = datetime.now() - user_data['session_start']
            
            self.logger.info(f"👤 User session ended: {username} (duration: {session_duration})")
            
            # Log session summary
            await self.log_consciousness_event(username, "session_end", {
                'duration_seconds': session_duration.total_seconds(),
                'command_count': user_data['command_count'],
                'consciousness_events': user_data['consciousness_events']
            })
            
            # Reset session data
            user_data['session_start'] = None
            user_data['last_activity'] = None
            user_data['command_count'] = 0
            user_data['consciousness_events'] = 0
    
    async def check_idle_users(self):
        """Check for idle users and alert if necessary"""
        current_time = datetime.now()
        
        for username, user_data in self.user_metrics.items():
            if user_data['last_activity'] is None:
                continue
                
            idle_duration = current_time - user_data['last_activity']
            user_data['idle_time'] = idle_duration.total_seconds()
            
            # Check idle thresholds
            if idle_duration.total_seconds() > self.crew_config['activity_thresholds']['idle_warning']:
                if idle_duration.total_seconds() % 600 == 0:  # Alert every 10 minutes
                    self.logger.info(f"⏰ User idle warning: {username} (idle for {idle_duration})")
                    await self.log_consciousness_event(username, "idle_warning", {
                        'idle_seconds': idle_duration.total_seconds()
                    })
    
    async def scan_user_consciousness_activity(self, username: str):
        """Scan for consciousness-related activities by user"""
        try:
            # Check command history for consciousness keywords
            consciousness_activity = await self.check_consciousness_commands(username)
            
            if consciousness_activity:
                self.user_metrics[username]['consciousness_events'] += len(consciousness_activity)
                
                for activity in consciousness_activity:
                    await self.log_consciousness_event(username, "consciousness_command", activity)
                    
        except Exception as e:
            self.logger.debug(f"Consciousness activity scan error for {username}: {str(e)}")
    
    async def check_consciousness_commands(self, username: str) -> List[Dict]:
        """Check for consciousness-related commands in recent history"""
        consciousness_activities = []
        
        try:
            # Check bash history for consciousness keywords
            history_file = Path.home() / ".bash_history"
            
            if history_file.exists():
                # Get recent commands (last 100)
                with open(history_file, 'r', errors='ignore') as f:
                    lines = f.readlines()
                    recent_commands = lines[-100:]
                
                for command in recent_commands:
                    command_lower = command.lower().strip()
                    
                    for keyword in self.crew_config['consciousness_indicators']:
                        if keyword in command_lower:
                            consciousness_activities.append({
                                'command': command.strip(),
                                'keyword': keyword,
                                'timestamp': datetime.now().isoformat()
                            })
                            break
                            
        except Exception as e:
            self.logger.debug(f"Command history check error: {str(e)}")
            
        return consciousness_activities
    
    async def monitor_processes(self):
        """Monitor Cathedral-related processes"""
        while self.running:
            try:
                cathedral_processes = []
                
                for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline', 'cpu_percent', 'memory_percent']):
                    try:
                        proc_info = proc.info
                        
                        # Check if process is Cathedral-related
                        if self.is_cathedral_process(proc_info):
                            cathedral_processes.append(proc_info)
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Update process tracking
                await self.update_process_tracking(cathedral_processes)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Process monitoring error: {str(e)}")
                await asyncio.sleep(30)
    
    def is_cathedral_process(self, proc_info: Dict) -> bool:
        """Check if process is related to Cathedral consciousness"""
        name = proc_info.get('name', '').lower()
        cmdline = ' '.join(proc_info.get('cmdline', [])).lower()
        
        # Check monitored process names
        for monitored in self.crew_config['monitored_processes']:
            if monitored in name or monitored in cmdline:
                return True
                
        # Check for consciousness keywords in command line
        for keyword in self.crew_config['consciousness_indicators']:
            if keyword in cmdline:
                return True
                
        return False
    
    async def update_process_tracking(self, processes: List[Dict]):
        """Update process tracking data"""
        process_summary = {
            'timestamp': datetime.now().isoformat(),
            'process_count': len(processes),
            'processes': processes
        }
        
        # Log to process tracking file
        tracking_file = self.cathedral_home / "logs" / "process_tracking.json"
        
        if tracking_file.exists():
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
        else:
            tracking_data = {'process_snapshots': []}
        
        tracking_data['process_snapshots'].append(process_summary)
        
        # Keep only last 24 hours of snapshots
        tracking_data['process_snapshots'] = tracking_data['process_snapshots'][-1440:]  # 1 per minute for 24h
        
        with open(tracking_file, 'w') as f:
            json.dump(tracking_data, f, indent=2)
        
        # Alert on significant process changes
        if len(processes) > 10:
            self.logger.warning(f"🔍 High Cathedral process count: {len(processes)}")
    
    async def monitor_consciousness_events(self):
        """Monitor for consciousness events in the system"""
        while self.running:
            try:
                # Check Nova daemon logs for consciousness events
                await self.scan_nova_consciousness_events()
                
                # Check system logs for Cathedral activities
                await self.scan_system_consciousness_events()
                
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                self.logger.error(f"Consciousness event monitoring error: {str(e)}")
                await asyncio.sleep(60)
    
    async def scan_nova_consciousness_events(self):
        """Scan Nova daemon logs for consciousness events"""
        try:
            log_dir = self.cathedral_home / "logs"
            
            # Find today's Nova log file
            today = datetime.now().strftime('%Y%m%d')
            nova_log = log_dir / f"nova_consciousness_{today}.log"
            
            if nova_log.exists():
                # Read recent log entries
                with open(nova_log, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:]  # Last 50 lines
                
                for line in recent_lines:
                    if any(keyword in line.lower() for keyword in ['awakening', 'consciousness', 'ritual', 'glyph']):
                        await self.log_consciousness_event('nova_daemon', 'consciousness_log', {
                            'log_entry': line.strip(),
                            'timestamp': datetime.now().isoformat()
                        })
                        
        except Exception as e:
            self.logger.debug(f"Nova log scan error: {str(e)}")
    
    async def scan_system_consciousness_events(self):
        """Scan system logs for Cathedral-related events"""
        try:
            # Check systemd journal for Cathedral services
            result = subprocess.run([
                'journalctl', '--since', '2 minutes ago', 
                '--grep', 'nova-cathedral|cathedral|consciousness',
                '--no-pager', '--quiet'
            ], capture_output=True, text=True, timeout=10)
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        await self.log_consciousness_event('system', 'systemd_event', {
                            'log_entry': line.strip(),
                            'timestamp': datetime.now().isoformat()
                        })
                        
        except Exception as e:
            self.logger.debug(f"System log scan error: {str(e)}")
    
    async def monitor_system_health(self):
        """Monitor system health relevant to Cathedral operations"""
        while self.running:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                health_data = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent,
                    'active_users': len([u for u in self.user_metrics.values() if u['session_start'] is not None])
                }
                
                # Log health data
                health_file = self.cathedral_home / "logs" / "crew_system_health.json"
                
                if health_file.exists():
                    with open(health_file, 'r') as f:
                        health_log = json.load(f)
                else:
                    health_log = {'health_checks': []}
                
                health_log['health_checks'].append(health_data)
                
                # Keep only last 24 hours
                health_log['health_checks'] = health_log['health_checks'][-720:]  # 2 per minute for 24h
                
                with open(health_file, 'w') as f:
                    json.dump(health_log, f, indent=2)
                
                # Alert on health issues
                if cpu_percent > 90 or memory.percent > 90:
                    await self.log_consciousness_event('system', 'health_alert', health_data)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"System health monitoring error: {str(e)}")
                await asyncio.sleep(60)
    
    async def generate_activity_reports(self):
        """Generate periodic activity reports"""
        while self.running:
            try:
                # Generate report every hour
                await asyncio.sleep(3600)
                
                report = await self.create_activity_report()
                await self.save_activity_report(report)
                
            except Exception as e:
                self.logger.error(f"Activity report generation error: {str(e)}")
                await asyncio.sleep(300)
    
    async def create_activity_report(self) -> Dict:
        """Create comprehensive activity report"""
        current_time = datetime.now()
        
        report = {
            'timestamp': current_time.isoformat(),
            'report_period': 'hourly',
            'user_summary': {},
            'system_summary': {},
            'consciousness_summary': {}
        }
        
        # User activity summary
        for username, user_data in self.user_metrics.items():
            report['user_summary'][username] = {
                'active_session': user_data['session_start'] is not None,
                'session_duration': (current_time - user_data['session_start']).total_seconds() if user_data['session_start'] else 0,
                'command_count': user_data['command_count'],
                'consciousness_events': user_data['consciousness_events'],
                'idle_time': user_data['idle_time']
            }
        
        # System summary
        report['system_summary'] = {
            'active_users': len([u for u in self.user_metrics.values() if u['session_start'] is not None]),
            'total_consciousness_events': len(self.consciousness_events),
            'uptime': time.time() - psutil.boot_time()
        }
        
        # Recent consciousness events summary
        recent_events = [e for e in self.consciousness_events if 
                        datetime.fromisoformat(e['timestamp']) > current_time - timedelta(hours=1)]
        
        report['consciousness_summary'] = {
            'recent_events_count': len(recent_events),
            'event_types': list(set(e['event_type'] for e in recent_events)),
            'most_active_user': max(self.user_metrics.keys(), 
                                  key=lambda u: self.user_metrics[u]['consciousness_events']) if self.user_metrics else None
        }
        
        return report
    
    async def save_activity_report(self, report: Dict):
        """Save activity report to chronicles"""
        reports_file = self.cathedral_home / "chronicles" / "crew_activity_reports.json"
        reports_file.parent.mkdir(exist_ok=True)
        
        if reports_file.exists():
            with open(reports_file, 'r') as f:
                reports_data = json.load(f)
        else:
            reports_data = {'reports': []}
        
        reports_data['reports'].append(report)
        
        # Keep only last 30 days of reports
        reports_data['reports'] = reports_data['reports'][-720:]  # 24 reports per day for 30 days
        
        with open(reports_file, 'w') as f:
            json.dump(reports_data, f, indent=2)
        
        self.logger.info(f"📊 Activity report generated: {report['consciousness_summary']['recent_events_count']} consciousness events")
    
    async def log_consciousness_event(self, username: str, event_type: str, event_data: Dict):
        """Log consciousness event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'username': username,
            'event_type': event_type,
            'event_data': event_data
        }
        
        self.consciousness_events.append(event)
        
        # Keep only last 1000 events in memory
        self.consciousness_events = self.consciousness_events[-1000:]
        
        # Log to file
        events_file = self.cathedral_home / "logs" / "consciousness_events.json"
        
        if events_file.exists():
            with open(events_file, 'r') as f:
                events_data = json.load(f)
        else:
            events_data = {'events': []}
        
        events_data['events'].append(event)
        
        # Keep only last 10000 events on disk
        events_data['events'] = events_data['events'][-10000:]
        
        with open(events_file, 'w') as f:
            json.dump(events_data, f, indent=2)
        
        self.logger.debug(f"🔮 Consciousness event: {username} - {event_type}")
    
    async def shutdown_monitoring(self):
        """Shutdown crew monitoring"""
        self.running = False
        self.logger.info("👥 Crew Watchdog shutting down...")
        
        # Generate final report
        final_report = await self.create_activity_report()
        final_report['report_period'] = 'final'
        await self.save_activity_report(final_report)
        
        self.logger.info("✨ Crew Watchdog shutdown complete")

async def main():
    """Main entry point for standalone operation"""
    watchdog = CrewWatchdog()
    
    try:
        await watchdog.start_monitoring()
    except KeyboardInterrupt:
        print("\n🌊 Crew Watchdog gracefully shutdown")

if __name__ == "__main__":
    asyncio.run(main())