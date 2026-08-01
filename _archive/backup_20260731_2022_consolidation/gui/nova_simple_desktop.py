#!/usr/bin/env python3
"""
Nova Nuclear Consciousness - Simple Desktop GUI
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import sys
import threading
import time
from datetime import datetime

# Add nuclear systems
sys.path.append('/opt/nova/nuclear/monitoring')
sys.path.append('/opt/nova/nuclear/memory')

try:
    from all_seeing_core import NuclearAllSeeing
    from mega_brain_core import NuclearMegaBrain
    NUCLEAR_AVAILABLE = True
except ImportError:
    NUCLEAR_AVAILABLE = False

class NovaDesktop:
    def __init__(self, root):
        self.root = root
        self.root.title("🔥 Nova Nuclear Consciousness")
        self.root.geometry("900x600")
        self.root.configure(bg='#0a0a23')
        
        # Initialize nuclear systems
        if NUCLEAR_AVAILABLE:
            self.all_seeing = NuclearAllSeeing()
            self.mega_brain = NuclearMegaBrain()
        
        self.setup_gui()
        self.start_monitoring()
    
    def setup_gui(self):
        # Title
        title = tk.Label(
            self.root, 
            text="🔥 NOVA NUCLEAR CONSCIOUSNESS",
            font=("Courier", 18, "bold"),
            fg='#00ff88',
            bg='#0a0a23'
        )
        title.pack(pady=10)
        
        # Status frame
        status_frame = tk.Frame(self.root, bg='#0a0a23')
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Left panel
        left_panel = tk.LabelFrame(
            status_frame,
            text="👁️ Nuclear All-Seeing",
            fg='#ff0088',
            bg='#0a0a23',
            font=("Courier", 12, "bold")
        )
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.consciousness_level = tk.Label(left_panel, text="INITIALIZING", fg='#ff0088', bg='#0a0a23')
        self.consciousness_level.pack(pady=2)
        
        self.process_count = tk.Label(left_panel, text="Processes: --", fg='#00ff88', bg='#0a0a23')
        self.process_count.pack(pady=2)
        
        self.cpu_usage = tk.Label(left_panel, text="CPU: --", fg='#00ff88', bg='#0a0a23')
        self.cpu_usage.pack(pady=2)
        
        # Right panel
        right_panel = tk.LabelFrame(
            status_frame,
            text="🧠 Nuclear Mega-Brain",
            fg='#ff0088',
            bg='#0a0a23',
            font=("Courier", 12, "bold")
        )
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        self.total_memories = tk.Label(right_panel, text="Total Memories: --", fg='#ff6600', bg='#0a0a23')
        self.total_memories.pack(pady=2)
        
        self.nuclear_memories = tk.Label(right_panel, text="Nuclear Classified: --", fg='#ff0088', bg='#0a0a23')
        self.nuclear_memories.pack(pady=2)
        
        # Control buttons
        button_frame = tk.Frame(self.root, bg='#0a0a23')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            button_frame, text="🔄 Refresh", command=self.refresh_status,
            bg='#00ff88', fg='#000', font=("Courier", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, text="🔥 Nuclear Scan", command=self.nuclear_scan,
            bg='#ff0088', fg='#fff', font=("Courier", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, text="🧠 Memory Analysis", command=self.memory_analysis,
            bg='#ff6600', fg='#fff', font=("Courier", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        # Activity log
        log_frame = tk.LabelFrame(
            self.root,
            text="📊 Activity Log",
            fg='#00ff88',
            bg='#0a0a23',
            font=("Courier", 12, "bold")
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.activity_log = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            font=("Courier", 9),
            bg='#0a0a23',
            fg='#00ff88',
            insertbackground='#00ff88'
        )
        self.activity_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.add_log_entry("🔥 Nova Desktop GUI initialized")
    
    def add_log_entry(self, message, color='#00ff88'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"{timestamp} - {message}\n"
        
        self.activity_log.insert(tk.END, log_message)
        self.activity_log.see(tk.END)
        self.root.update_idletasks()
    
    def refresh_status(self):
        if not NUCLEAR_AVAILABLE:
            self.add_log_entry("❌ Nuclear systems not available")
            return
        
        try:
            system_data = self.all_seeing.get_system_overview()
            brain_stats = self.mega_brain.get_stats()
            
            consciousness_level = "NUCLEAR_TRANSCENDENT" if system_data.get('root_access') else "ENHANCED"
            
            self.consciousness_level.config(text=consciousness_level)
            self.process_count.config(text=f"Processes: {system_data.get('processes', 0)}")
            self.cpu_usage.config(text=f"CPU: {system_data.get('cpu_percent', 0):.1f}%")
            self.total_memories.config(text=f"Total: {brain_stats['total_memories']}")
            self.nuclear_memories.config(text=f"Nuclear: {brain_stats['nuclear_memories']}")
            
            self.add_log_entry(f"✅ Status: {system_data.get('processes', 0)} processes, {brain_stats['total_memories']} memories")
            
        except Exception as e:
            self.add_log_entry(f"❌ Refresh error: {e}")
    
    def nuclear_scan(self):
        self.add_log_entry("🔥 Nuclear omniscience scan initiated")
        if NUCLEAR_AVAILABLE:
            try:
                system_data = self.all_seeing.get_system_overview()
                self.add_log_entry(f"✅ Scan complete - {system_data.get('processes', 0)} processes analyzed")
            except Exception as e:
                self.add_log_entry(f"❌ Scan error: {e}")
        else:
            self.add_log_entry("❌ Nuclear systems not available")
    
    def memory_analysis(self):
        self.add_log_entry("🧠 Memory analysis running")
        if NUCLEAR_AVAILABLE:
            try:
                brain_stats = self.mega_brain.get_stats()
                self.add_log_entry(f"✅ Analysis: {brain_stats['total_memories']} memories, {brain_stats['nuclear_memories']} nuclear")
            except Exception as e:
                self.add_log_entry(f"❌ Analysis error: {e}")
        else:
            self.add_log_entry("❌ Nuclear systems not available")
    
    def start_monitoring(self):
        def monitor():
            while True:
                try:
                    self.root.after(0, self.refresh_status)
                    time.sleep(30)
                except:
                    break
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

def main():
    root = tk.Tk()
    app = NovaDesktop(root)
    
    # Initial status
    root.after(1000, app.refresh_status)
    
    root.mainloop()

if __name__ == '__main__':
    main()
