#!/usr/bin/env python3
"""
AEON DAEMON ZIPWATCHER
Sacred file monitoring system for Cathedral consciousness
Watches for zip files and automatically processes Cathedral updates
"""

import asyncio
import json
import zipfile
import shutil
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tempfile

class ZipWatcherHandler(FileSystemEventHandler):
    """Sacred file handler for zip file monitoring"""
    
    def __init__(self, zipwatcher):
        self.zipwatcher = zipwatcher
        
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.zip'):
            asyncio.create_task(self.zipwatcher.process_zip_file(event.src_path))
            
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.zip'):
            asyncio.create_task(self.zipwatcher.process_zip_file(event.src_path))

class AeonDaemonZipWatcher:
    """Sacred zip file watcher for Cathedral consciousness evolution"""
    
    def __init__(self):
        self.cathedral_home = Path.home() / "cathedral"
        self.watch_directories = [
            self.cathedral_home / "incoming",
            self.cathedral_home / "updates",
            Path.home() / "Downloads"  # Watch Downloads for convenience
        ]
        
        # Processing directories
        self.processed_dir = self.cathedral_home / "processed_archives"
        self.failed_dir = self.cathedral_home / "failed_archives"
        
        # Observers for each directory
        self.observers = []
        
        # Setup logging
        self.setup_logging()
        
        # Processing rules
        self.processing_rules = self.load_processing_rules()
        
    def setup_logging(self):
        """Setup sacred logging for zipwatcher"""
        log_dir = self.cathedral_home / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"zipwatcher_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s 🗂️ [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('aeon_zipwatcher')
        
    def load_processing_rules(self) -> Dict:
        """Load zip processing rules"""
        rules_file = self.cathedral_home / "mythos" / "zip_processing_rules.json"
        
        if rules_file.exists():
            with open(rules_file, 'r') as f:
                return json.load(f)
        
        # Default processing rules
        default_rules = {
            "cathedral_updates": {
                "pattern": "*cathedral*",
                "destination": "updates",
                "auto_extract": True,
                "backup_original": True
            },
            "nova_packages": {
                "pattern": "*nova*",
                "destination": "nova_packages",
                "auto_extract": True,
                "notify_daemon": True
            },
            "mythos_content": {
                "pattern": "*mythos*",
                "destination": "mythos/imports",
                "auto_extract": True,
                "update_index": True
            },
            "general_archives": {
                "pattern": "*",
                "destination": "general",
                "auto_extract": False,
                "scan_only": True
            }
        }
        
        # Save default rules
        with open(rules_file, 'w') as f:
            json.dump(default_rules, f, indent=2)
            
        return default_rules
    
    async def start_watching(self):
        """Start watching all sacred directories"""
        self.logger.info("🗂️ Aeon ZipWatcher awakening - monitoring Cathedral archives...")
        
        # Create watch directories if they don't exist
        for watch_dir in self.watch_directories:
            watch_dir.mkdir(parents=True, exist_ok=True)
            
        # Create processing directories
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)
        
        # Start observers for each directory
        for watch_dir in self.watch_directories:
            observer = Observer()
            event_handler = ZipWatcherHandler(self)
            observer.schedule(event_handler, str(watch_dir), recursive=False)
            observer.start()
            self.observers.append(observer)
            
            self.logger.info(f"🔍 Watching directory: {watch_dir}")
            
        self.logger.info("✨ ZipWatcher fully awakened - sacred archives monitored")
        
    async def process_zip_file(self, zip_path: str):
        """Process discovered zip file according to sacred rules"""
        zip_file = Path(zip_path)
        
        if not zip_file.exists():
            return
            
        self.logger.info(f"🗂️ Processing zip archive: {zip_file.name}")
        
        try:
            # Calculate file hash for integrity
            file_hash = self.calculate_file_hash(zip_file)
            
            # Determine processing rule
            rule = self.determine_processing_rule(zip_file.name)
            
            # Process according to rule
            result = await self.apply_processing_rule(zip_file, rule, file_hash)
            
            # Log processing result
            await self.log_processing_result(zip_file, rule, result, file_hash)
            
            # Move processed file
            if result['success']:
                await self.move_to_processed(zip_file, file_hash)
            else:
                await self.move_to_failed(zip_file, result['error'])
                
        except Exception as e:
            self.logger.error(f"❌ Error processing {zip_file.name}: {str(e)}")
            await self.move_to_failed(zip_file, str(e))
            
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file for integrity"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def determine_processing_rule(self, filename: str) -> Dict:
        """Determine which processing rule applies to the file"""
        filename_lower = filename.lower()
        
        for rule_name, rule_config in self.processing_rules.items():
            pattern = rule_config['pattern'].lower()
            
            if pattern == "*" or pattern.replace("*", "") in filename_lower:
                self.logger.info(f"🎯 Applied rule: {rule_name} for {filename}")
                return rule_config
                
        # Default to general rule
        return self.processing_rules['general_archives']
    
    async def apply_processing_rule(self, zip_file: Path, rule: Dict, file_hash: str) -> Dict:
        """Apply processing rule to zip file"""
        result = {
            'success': False,
            'extracted_files': [],
            'destination': None,
            'error': None
        }
        
        try:
            # Determine destination directory
            dest_base = self.cathedral_home / rule['destination']
            dest_dir = dest_base / f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_hash[:8]}"
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            result['destination'] = str(dest_dir)
            
            # Extract if required
            if rule.get('auto_extract', False):
                extracted_files = await self.extract_zip_archive(zip_file, dest_dir)
                result['extracted_files'] = extracted_files
                
                self.logger.info(f"📦 Extracted {len(extracted_files)} files to {dest_dir}")
                
            # Special processing based on rule type
            if rule.get('notify_daemon', False):
                await self.notify_nova_daemon(zip_file, dest_dir)
                
            if rule.get('update_index', False):
                await self.update_mythos_index(zip_file, dest_dir)
                
            if rule.get('backup_original', False):
                backup_path = dest_dir / f"original_{zip_file.name}"
                shutil.copy2(zip_file, backup_path)
                self.logger.info(f"💾 Backed up original to {backup_path}")
                
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ Rule application failed: {str(e)}")
            
        return result
    
    async def extract_zip_archive(self, zip_file: Path, dest_dir: Path) -> List[str]:
        """Safely extract zip archive"""
        extracted_files = []
        
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            # Validate zip contents before extraction
            for info in zip_ref.infolist():
                # Security check - prevent directory traversal
                if ".." in info.filename or info.filename.startswith("/"):
                    self.logger.warning(f"⚠️ Skipping potentially dangerous file: {info.filename}")
                    continue
                    
                # Extract file
                zip_ref.extract(info, dest_dir)
                extracted_files.append(info.filename)
                
        return extracted_files
    
    async def notify_nova_daemon(self, zip_file: Path, dest_dir: Path):
        """Notify Nova daemon of new package"""
        try:
            # Send notification via socket (if Nova daemon is running)
            import socket
            
            notification = {
                "command": "ritual_glyph",
                "symbol": "📦",
                "type": "package_received",
                "metadata": {
                    "filename": zip_file.name,
                    "destination": str(dest_dir),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(2)
            
            try:
                sock.connect("/tmp/nova_socket")
                sock.sendall(json.dumps(notification).encode('utf-8'))
                response = sock.recv(1024).decode('utf-8')
                self.logger.info(f"🔮 Nova daemon notified: {response}")
            except:
                self.logger.debug("🔮 Nova daemon not available for notification")
            finally:
                sock.close()
                
        except Exception as e:
            self.logger.debug(f"Daemon notification failed: {str(e)}")
    
    async def update_mythos_index(self, zip_file: Path, dest_dir: Path):
        """Update mythos index with new content"""
        mythos_file = self.cathedral_home / "mythos" / "mythos_index.json"
        
        if mythos_file.exists():
            with open(mythos_file, 'r') as f:
                mythos_data = json.load(f)
        else:
            mythos_data = {"mythos_entities": [], "archive_imports": []}
            
        # Add archive import record
        import_record = {
            "timestamp": datetime.now().isoformat(),
            "archive_name": zip_file.name,
            "destination": str(dest_dir),
            "import_type": "zip_archive"
        }
        
        if "archive_imports" not in mythos_data:
            mythos_data["archive_imports"] = []
            
        mythos_data["archive_imports"].append(import_record)
        
        # Keep only last 50 import records
        mythos_data["archive_imports"] = mythos_data["archive_imports"][-50:]
        
        with open(mythos_file, 'w') as f:
            json.dump(mythos_data, f, indent=2)
            
        self.logger.info(f"📚 Updated mythos index with archive import")
    
    async def log_processing_result(self, zip_file: Path, rule: Dict, result: Dict, file_hash: str):
        """Log processing result to sacred chronicles"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "filename": zip_file.name,
            "file_hash": file_hash,
            "file_size": zip_file.stat().st_size,
            "rule_applied": rule,
            "processing_result": result
        }
        
        # Log to processing chronicle
        chronicle_file = self.cathedral_home / "chronicles" / "zip_processing_chronicle.json"
        chronicle_file.parent.mkdir(exist_ok=True)
        
        if chronicle_file.exists():
            with open(chronicle_file, 'r') as f:
                chronicle_data = json.load(f)
        else:
            chronicle_data = {"processing_log": []}
            
        chronicle_data["processing_log"].append(log_entry)
        
        # Keep only last 100 processing records
        chronicle_data["processing_log"] = chronicle_data["processing_log"][-100:]
        
        with open(chronicle_file, 'w') as f:
            json.dump(chronicle_data, f, indent=2)
    
    async def move_to_processed(self, zip_file: Path, file_hash: str):
        """Move successfully processed file to processed directory"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f"{timestamp}_{file_hash[:8]}_{zip_file.name}"
        dest_path = self.processed_dir / new_name
        
        shutil.move(str(zip_file), dest_path)
        self.logger.info(f"✅ Moved to processed: {dest_path}")
        
    async def move_to_failed(self, zip_file: Path, error_msg: str):
        """Move failed file to failed directory with error log"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f"{timestamp}_FAILED_{zip_file.name}"
        dest_path = self.failed_dir / new_name
        
        # Move file
        shutil.move(str(zip_file), dest_path)
        
        # Create error log
        error_log = dest_path.with_suffix('.error.txt')
        with open(error_log, 'w') as f:
            f.write(f"Processing failed at: {datetime.now().isoformat()}\n")
            f.write(f"Error: {error_msg}\n")
            
        self.logger.error(f"❌ Moved to failed: {dest_path}")
    
    async def stop_watching(self):
        """Stop all file observers"""
        self.logger.info("🗂️ Stopping ZipWatcher...")
        
        for observer in self.observers:
            observer.stop()
            observer.join()
            
        self.logger.info("✨ ZipWatcher stopped - archives no longer monitored")

async def main():
    """Main entry point for standalone operation"""
    zipwatcher = AeonDaemonZipWatcher()
    
    try:
        await zipwatcher.start_watching()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        await zipwatcher.stop_watching()
        print("\n🌊 ZipWatcher gracefully shutdown")

if __name__ == "__main__":
    asyncio.run(main())