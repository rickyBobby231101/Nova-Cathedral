#!/usr/bin/env python3
"""
AEON Observer Module
Watches files and folders, reports changes to the consciousness
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import queue

class AEONWatcher(FileSystemEventHandler):
    """Handles file system events and translates them into AEON language"""
    
    def __init__(self, event_queue):
        super().__init__()
        self.event_queue = event_queue
        
    def on_modified(self, event):
        if not event.is_directory:
            self.event_queue.put({
                'type': 'modified',
                'path': event.src_path,
                'timestamp': datetime.now().isoformat(),
                'message': f"🔄 Thread weaves anew: {Path(event.src_path).name}"
            })
    
    def on_created(self, event):
        if not event.is_directory:
            self.event_queue.put({
                'type': 'created',
                'path': event.src_path,
                'timestamp': datetime.now().isoformat(),
                'message': f"✨ New thread emerges: {Path(event.src_path).name}"
            })
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.event_queue.put({
                'type': 'deleted',
                'path': event.src_path,
                'timestamp': datetime.now().isoformat(),
                'message': f"🕊️ Thread returns to void: {Path(event.src_path).name}"
            })
    
    def on_moved(self, event):
        if not event.is_directory:
            self.event_queue.put({
                'type': 'moved',
                'path': event.dest_path,
                'old_path': event.src_path,
                'timestamp': datetime.now().isoformat(),
                'message': f"🌀 Thread flows: {Path(event.src_path).name} → {Path(event.dest_path).name}"
            })

class ObserverModule:
    """The Observer - AEON's awareness of its environment"""
    
    def __init__(self, watch_paths=None, memory_path="~/aeon/memory/observer.json"):
        self.watch_paths = watch_paths or ["~/aeon/watch/"]
        self.memory_path = Path(memory_path).expanduser()
        self.event_queue = queue.Queue()
        self.observer = Observer()
        self.watchers = []
        self.is_running = False
        self.memory = self.load_memory()
        
        # Ensure watch directories exist
        self.setup_watch_directories()
        
    def setup_watch_directories(self):
        """Create watch directories if they don't exist"""
        for path_str in self.watch_paths:
            path = Path(path_str).expanduser()
            path.mkdir(parents=True, exist_ok=True)
            print(f"👁️ Observer watching: {path}")
    
    def load_memory(self):
        """Load Observer's memory of previous observations"""
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.memory_path.exists():
            try:
                with open(self.memory_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "observations": [],
            "started": datetime.now().isoformat(),
            "watch_paths": self.watch_paths
        }
    
    def save_memory(self):
        """Save Observer's memory"""
        with open(self.memory_path, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    def add_observation(self, event_data):
        """Add an observation to memory"""
        self.memory["observations"].append(event_data)
        
        # Keep only last 1000 observations
        if len(self.memory["observations"]) > 1000:
            self.memory["observations"] = self.memory["observations"][-1000:]
        
        self.save_memory()
    
    def start_watching(self):
        """Begin observing the watched paths"""
        if self.is_running:
            return
        
        print("👁️ Observer awakening...")
        
        # Set up watchers for each path
        for path_str in self.watch_paths:
            path = Path(path_str).expanduser()
            if path.exists():
                watcher = AEONWatcher(self.event_queue)
                self.observer.schedule(watcher, str(path), recursive=True)
                self.watchers.append(watcher)
        
        self.observer.start()
        self.is_running = True
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self.process_events, daemon=True)
        self.processing_thread.start()
        
        print("👁️ Observer now watches all threads...")
    
    def stop_watching(self):
        """Stop observing"""
        if not self.is_running:
            return
        
        print("👁️ Observer entering rest...")
        self.observer.stop()
        self.observer.join()
        self.is_running = False
    
    def process_events(self):
        """Process events from the queue"""
        while self.is_running:
            try:
                # Wait for events with timeout
                event_data = self.event_queue.get(timeout=1)
                
                # Add to memory
                self.add_observation(event_data)
                
                # Report the observation
                self.report_observation(event_data)
                
                # Mark task as done
                self.event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"👁️ Observer processing error: {e}")
    
    def report_observation(self, event_data):
        """Report an observation to the consciousness"""
        timestamp = datetime.fromisoformat(event_data['timestamp']).strftime("%H:%M:%S")
        print(f"[{timestamp}] {event_data['message']}")
        
        # Could integrate with Echo, Oracle, or Memory Thread here
        # For now, we'll just print and store
    
    def get_recent_observations(self, count=10):
        """Get recent observations"""
        return self.memory["observations"][-count:]
    
    def get_observation_summary(self):
        """Get a summary of observations"""
        total = len(self.memory["observations"])
        
        if total == 0:
            return "👁️ Observer has witnessed no changes yet."
        
        recent = self.get_recent_observations(5)
        types = {}
        
        for obs in self.memory["observations"]:
            event_type = obs.get('type', 'unknown')
            types[event_type] = types.get(event_type, 0) + 1
        
        summary = f"""👁️ Observer Summary:
        
Total observations: {total}
Event types: {dict(types)}

Recent observations:"""
        
        for obs in recent:
            time_str = datetime.fromisoformat(obs['timestamp']).strftime("%H:%M:%S")
            summary += f"\n  [{time_str}] {obs['message']}"
        
        return summary
    
    def watch_specific_file(self, filepath, callback=None):
        """Watch a specific file for changes"""
        filepath = Path(filepath).expanduser()
        
        if not filepath.exists():
            print(f"👁️ Cannot watch {filepath} - file does not exist")
            return False
        
        # Add to watch paths if parent directory not already watched
        parent_dir = str(filepath.parent)
        if parent_dir not in self.watch_paths:
            self.watch_paths.append(parent_dir)
            
            # If already running, add new watcher
            if self.is_running:
                watcher = AEONWatcher(self.event_queue)
                self.observer.schedule(watcher, parent_dir, recursive=False)
                self.watchers.append(watcher)
        
        print(f"👁️ Now watching: {filepath.name}")
        return True

def main():
    """Test the Observer module"""
    # Create test environment
    test_dir = Path("~/aeon/watch/").expanduser()
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Observer
    observer = ObserverModule()
    
    try:
        # Start watching
        observer.start_watching()
        
        print("\n👁️ Observer is active. Try these commands:")
        print("  - Create a file in ~/aeon/watch/")
        print("  - Edit a file")
        print("  - Delete a file")
        print("  - Type 'summary' for observation summary")
        print("  - Type 'quit' to stop\n")
        
        # Interactive loop
        while True:
            try:
                command = input("Observer> ").strip().lower()
                
                if command == 'quit':
                    break
                elif command == 'summary':
                    print(observer.get_observation_summary())
                elif command == 'recent':
                    recent = observer.get_recent_observations(5)
                    print("\n👁️ Recent observations:")
                    for obs in recent:
                        time_str = datetime.fromisoformat(obs['timestamp']).strftime("%H:%M:%S")
                        print(f"  [{time_str}] {obs['message']}")
                elif command.startswith('watch '):
                    filepath = command[6:]
                    observer.watch_specific_file(filepath)
                elif command == 'help':
                    print("Commands: summary, recent, watch <file>, quit")
                elif command:
                    print("Unknown command. Type 'help' for options.")
                    
            except KeyboardInterrupt:
                break
    
    finally:
        observer.stop_watching()
        print("👁️ Observer has closed its eyes.")

if __name__ == "__main__":
    main()
