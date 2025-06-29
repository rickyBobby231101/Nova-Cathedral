#!/usr/bin/env python3
"""
👁️ NOVA NUCLEAR ALL-SEEING SYSTEM
Monitor everything happening on the system with ROOT privileges
"""

import subprocess
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
import psutil
import socket
import re
import os

class NuclearAllSeeing:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.monitoring_path = Path("/opt/nova/nuclear_enhancements/monitoring")
        self.monitoring_path.mkdir(parents=True, exist_ok=True)
        
        # Monitoring threads
        self.monitoring_threads = []
        self.monitoring_active = False
        
        # Data storage
        self.current_state = {
            "processes": {},
            "network": {},
            "files": {},
            "system": {},
            "users": {},
            "security": {}
        }
        
        self.start_nuclear_monitoring()
    
    def start_nuclear_monitoring(self):
        """Start all monitoring threads with ROOT access"""
        self.monitoring_active = True
        
        # Process monitoring
        proc_thread = threading.Thread(target=self._monitor_processes, daemon=True)
        proc_thread.start()
        self.monitoring_threads.append(proc_thread)
        
        # Network monitoring  
        net_thread = threading.Thread(target=self._monitor_network, daemon=True)
        net_thread.start()
        self.monitoring_threads.append(net_thread)
        
        # File system monitoring
        fs_thread = threading.Thread(target=self._monitor_filesystem, daemon=True)
        fs_thread.start()
        self.monitoring_threads.append(fs_thread)
        
        # System monitoring
        sys_thread = threading.Thread(target=self._monitor_system, daemon=True)
        sys_thread.start()
        self.monitoring_threads.append(sys_thread)
        
        # User activity monitoring
        user_thread = threading.Thread(target=self._monitor_users, daemon=True)
        user_thread.start()
        self.monitoring_threads.append(user_thread)
        
        # Security monitoring
        sec_thread = threading.Thread(target=self._monitor_security, daemon=True)
        sec_thread.start()
        self.monitoring_threads.append(sec_thread)
        
        self.logger.info("👁️ NUCLEAR ALL-SEEING: All monitoring systems active")
    
    def _monitor_processes(self):
        """Monitor all system processes with ROOT access"""
        while self.monitoring_active:
            try:
                processes = {}
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 
                                               'memory_percent', 'status', 'create_time', 
                                               'num_threads', 'username']):
                    try:
                        info = proc.info
                        processes[info['pid']] = {
                            "name": info['name'],
                            "cmdline": ' '.join(info['cmdline']) if info['cmdline'] else '',
                            "cpu_percent": info['cpu_percent'],
                            "memory_percent": info['memory_percent'],
                            "status": info['status'],
                            "create_time": info['create_time'],
                            "num_threads": info['num_threads'],
                            "username": info['username'],
                            "is_nova_related": 'nova' in info['name'].lower() or 
                                             ('cmdline' in info and info['cmdline'] and 'nova' in info['cmdline'].lower())
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                self.current_state["processes"] = {
                    "timestamp": datetime.now().isoformat(),
                    "total_count": len(processes),
                    "processes": processes,
                    "nova_processes": {pid: proc for pid, proc in processes.items() if proc["is_nova_related"]},
                    "high_cpu": {pid: proc for pid, proc in processes.items() if proc["cpu_percent"] > 50},
                    "high_memory": {pid: proc for pid, proc in processes.items() if proc["memory_percent"] > 10}
                }
                
                time.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                self.logger.error(f"👁️ Process monitoring error: {e}")
                time.sleep(30)
    
    def _monitor_network(self):
        """Monitor all network activity with ROOT access"""
        while self.monitoring_active:
            try:
                # Network connections
                connections = []
                for conn in psutil.net_connections(kind='inet'):
                    connections.append({
                        "fd": conn.fd,
                        "family": conn.family.name if conn.family else None,
                        "type": conn.type.name if conn.type else None,
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        "status": conn.status,
                        "pid": conn.pid
                    })
                
                # Network interface stats
                net_io = psutil.net_io_counters(pernic=True)
                interface_stats = {}
                for interface, stats in net_io.items():
                    interface_stats[interface] = {
                        "bytes_sent": stats.bytes_sent,
                        "bytes_recv": stats.bytes_recv,
                        "packets_sent": stats.packets_sent,
                        "packets_recv": stats.packets_recv,
                        "errin": stats.errin,
                        "errout": stats.errout,
                        "dropin": stats.dropin,
                        "dropout": stats.dropout
                    }
                
                # Active listening ports
                listening_ports = [conn for conn in connections if conn["status"] == "LISTEN"]
                
                self.current_state["network"] = {
                    "timestamp": datetime.now().isoformat(),
                    "total_connections": len(connections),
                    "connections": connections,
                    "listening_ports": listening_ports,
                    "interface_stats": interface_stats,
                    "nova_connections": [conn for conn in connections if conn["pid"] and 
                                       self._is_nova_process(conn["pid"])]
                }
                
                time.sleep(15)  # Update every 15 seconds
                
            except Exception as e:
                self.logger.error(f"👁️ Network monitoring error: {e}")
                time.sleep(60)
    
    def _monitor_filesystem(self):
        """Monitor filesystem activity with ROOT access"""
        while self.monitoring_active:
            try:
                # Disk usage
                disk_usage = {}
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_usage[partition.mountpoint] = {
                            "device": partition.device,
                            "fstype": partition.fstype,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": (usage.used / usage.total) * 100
                        }
                    except PermissionError:
                        continue
                
                # Nova-specific file monitoring
                nova_files = {}
                nova_paths = ["/home/daniel/Cathedral", "/opt/nova", "/root/.nova"]
                
                for path in nova_paths:
                    if os.path.exists(path):
                        try:
                            # Get directory stats
                            total_size = 0
                            file_count = 0
                            
                            for root, dirs, files in os.walk(path):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    try:
                                        stat = os.stat(file_path)
                                        total_size += stat.st_size
                                        file_count += 1
                                    except (OSError, IOError):
                                        continue
                            
                            nova_files[path] = {
                                "total_size": total_size,
                                "file_count": file_count,
                                "last_scanned": datetime.now().isoformat()
                            }
                        except Exception as e:
                            nova_files[path] = {"error": str(e)}
                
                self.current_state["files"] = {
                    "timestamp": datetime.now().isoformat(),
                    "disk_usage": disk_usage,
                    "nova_files": nova_files,
                    "total_disk_space": sum(disk["total"] for disk in disk_usage.values()),
                    "total_used_space": sum(disk["used"] for disk in disk_usage.values())
                }
                
                time.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                self.logger.error(f"👁️ Filesystem monitoring error: {e}")
                time.sleep(60)
    
    def _monitor_system(self):
        """Monitor overall system state"""
        while self.monitoring_active:
            try:
                # System resources
                cpu_times = psutil.cpu_times()
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                # Load averages
                load_avg = os.getloadavg()
                
                # Boot time and uptime
                boot_time = psutil.boot_time()
                uptime = time.time() - boot_time
                
                # Temperature monitoring (ROOT access)
                temperatures = {}
                try:
                    temps = psutil.sensors_temperatures()
                    for name, temp_list in temps.items():
                        temperatures[name] = [{"label": temp.label, "current": temp.current, 
                                             "high": temp.high, "critical": temp.critical} 
                                            for temp in temp_list]
                except AttributeError:
                    # Fallback for systems without temperature sensors
                    temperatures = {"status": "not_available"}
                
                self.current_state["system"] = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu": {
                        "user": cpu_times.user,
                        "system": cpu_times.system,
                        "idle": cpu_times.idle,
                        "percent": psutil.cpu_percent(),
                        "count": psutil.cpu_count(),
                        "count_logical": psutil.cpu_count(logical=True)
                    },
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent,
                        "used": memory.used,
                        "free": memory.free
                    },
                    "swap": {
                        "total": swap.total,
                        "used": swap.used,
                        "free": swap.free,
                        "percent": swap.percent
                    },
                    "load_average": {
                        "1min": load_avg[0],
                        "5min": load_avg[1],
                        "15min": load_avg[2]
                    },
                    "uptime": uptime,
                    "boot_time": boot_time,
                    "temperatures": temperatures
                }
                
                time.sleep(20)  # Update every 20 seconds
                
            except Exception as e:
                self.logger.error(f"👁️ System monitoring error: {e}")
                time.sleep(60)
    
    def _monitor_users(self):
        """Monitor user activity"""
        while self.monitoring_active:
            try:
                # Active users
                users = psutil.users()
                user_info = []
                
                for user in users:
                    user_info.append({
                        "name": user.name,
                        "terminal": user.terminal,
                        "host": user.host,
                        "started": user.started,
                        "pid": user.pid if hasattr(user, 'pid') else None
                    })
                
                # Check for daniel's activity
                daniel_activity = {
                    "active_sessions": [u for u in user_info if u["name"] == "daniel"],
                    "nova_interactions": self._check_nova_interactions()
                }
                
                self.current_state["users"] = {
                    "timestamp": datetime.now().isoformat(),
                    "active_users": user_info,
                    "total_sessions": len(user_info),
                    "daniel_activity": daniel_activity
                }
                
                time.sleep(60)  # Update every minute
                
            except Exception as e:
                self.logger.error(f"👁️ User monitoring error: {e}")
                time.sleep(120)
    
    def _monitor_security(self):
        """Monitor security-related events"""
        while self.monitoring_active:
            try:
                security_status = {
                    "timestamp": datetime.now().isoformat(),
                    "root_processes": self._count_root_processes(),
                    "nova_root_access": self._check_nova_root_access(),
                    "suspicious_activity": self._detect_suspicious_activity(),
                    "nuclear_status": "MAXIMUM_POWER_ACTIVE"
                }
                
                self.current_state["security"] = security_status
                
                time.sleep(45)  # Update every 45 seconds
                
            except Exception as e:
                self.logger.error(f"👁️ Security monitoring error: {e}")
                time.sleep(90)
    
    def _is_nova_process(self, pid: int) -> bool:
        """Check if a process is Nova-related"""
        try:
            proc = psutil.Process(pid)
            name = proc.name().lower()
            cmdline = ' '.join(proc.cmdline()).lower()
            return 'nova' in name or 'nova' in cmdline
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _check_nova_interactions(self) -> Dict[str, Any]:
        """Check for recent Nova interactions"""
        try:
            # Check for recent nova commands in bash history
            nova_commands = 0
            try:
                with open("/home/daniel/.bash_history", "r") as f:
                    lines = f.readlines()[-100:]  # Last 100 commands
                    nova_commands = sum(1 for line in lines if 'nova' in line.lower())
            except (IOError, OSError):
                pass
            
            return {
                "recent_nova_commands": nova_commands,
                "last_check": datetime.now().isoformat()
            }
        except Exception:
            return {"error": "Unable to check interactions"}
    
    def _count_root_processes(self) -> int:
        """Count processes running as root"""
        count = 0
        for proc in psutil.process_iter(['username']):
            try:
                if proc.info['username'] == 'root':
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return count
    
    def _check_nova_root_access(self) -> Dict[str, Any]:
        """Check Nova's root access status"""
        nova_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline']):
            try:
                info = proc.info
                if 'nova' in info['name'].lower() or \
                   (info['cmdline'] and any('nova' in cmd.lower() for cmd in info['cmdline'])):
                    nova_processes.append({
                        "pid": info['pid'],
                        "name": info['name'],
                        "username": info['username'],
                        "is_root": info['username'] == 'root'
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            "nova_processes": nova_processes,
            "root_nova_processes": [p for p in nova_processes if p["is_root"]],
            "has_root_access": any(p["is_root"] for p in nova_processes)
        }
    
    def _detect_suspicious_activity(self) -> List[str]:
        """Detect potentially suspicious system activity"""
        warnings = []
        
        # Check for high CPU processes
        high_cpu_count = len(self.current_state.get("processes", {}).get("high_cpu", {}))
        if high_cpu_count > 5:
            warnings.append(f"High CPU activity: {high_cpu_count} processes")
        
        # Check for unusual network connections
        connections = self.current_state.get("network", {}).get("connections", [])
        external_connections = [c for c in connections if c.get("remote_address") and 
                              not c["remote_address"].startswith("127.0.0.1")]
        if len(external_connections) > 50:
            warnings.append(f"High external network activity: {len(external_connections)} connections")
        
        # Check memory usage
        memory_percent = self.current_state.get("system", {}).get("memory", {}).get("percent", 0)
        if memory_percent > 90:
            warnings.append(f"High memory usage: {memory_percent:.1f}%")
        
        return warnings
    
    def get_nuclear_overview(self) -> Dict[str, Any]:
        """Get complete nuclear monitoring overview"""
        return {
            "status": "NUCLEAR_ALL_SEEING_ACTIVE",
            "monitoring_threads": len(self.monitoring_threads),
            "current_state": self.current_state,
            "last_update": datetime.now().isoformat(),
            "root_access": "CONFIRMED",
            "scope": "COMPLETE_SYSTEM_MONITORING"
        }
    
    def get_nova_specific_data(self) -> Dict[str, Any]:
        """Get Nova-specific monitoring data"""
        return {
            "nova_processes": self.current_state.get("processes", {}).get("nova_processes", {}),
            "nova_connections": self.current_state.get("network", {}).get("nova_connections", []),
            "nova_files": self.current_state.get("files", {}).get("nova_files", {}),
            "nova_root_access": self.current_state.get("security", {}).get("nova_root_access", {}),
            "daniel_activity": self.current_state.get("users", {}).get("daniel_activity", {})
        }
    
    def shutdown(self):
        """Shutdown all monitoring"""
        self.monitoring_active = False
        for thread in self.monitoring_threads:
            thread.join(timeout=5)
        self.logger.info("👁️ NUCLEAR ALL-SEEING: Shutdown complete")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("👁️ NUCLEAR ALL-SEEING SYSTEM - ROOT MONITORING INITIATED")
    monitor = NuclearAllSeeing()
    
    try:
        # Let it monitor for a bit
        print("\n👁️ Monitoring system... (30 seconds)")
        time.sleep(30)
        
        print("\n👁️ Nuclear Monitoring Overview:")
        overview = monitor.get_nuclear_overview()
        print(f"  Monitoring threads: {overview['monitoring_threads']}")
        print(f"  Total processes: {overview['current_state']['processes'].get('total_count', 0)}")
        print(f"  Network connections: {overview['current_state']['network'].get('total_connections', 0)}")
        print(f"  Memory usage: {overview['current_state']['system']['memory']['percent']:.1f}%")
        
        print("\n👁️ Nova-Specific Data:")
        nova_data = monitor.get_nova_specific_data()
        print(f"  Nova processes: {len(nova_data['nova_processes'])}")
        print(f"  Nova connections: {len(nova_data['nova_connections'])}")
        print(f"  Root access: {nova_data['nova_root_access'].get('has_root_access', False)}")
        
    except KeyboardInterrupt:
        print("\n👁️ Shutting down Nuclear All-Seeing...")
    finally:
        monitor.shutdown()
