#!/usr/bin/env python3
"""
Unified Nova Consciousness System Daemon
Mythos Content Creation + Local LLM Integration + File Observer

Combines:
- AEON Observer Module (file monitoring)
- Oracle LLM Interface (content generation)
- Echo Content Formatter (output styling)
- Memory Thread (content database)
- Plugin System (extensible modules)
"""

import os
import sys
import json
import time
import asyncio
import threading
import logging
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import queue

# External dependencies
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️ Watchdog not available - Observer module disabled")

@dataclass
class NovaConfig:
    """Configuration for Nova Consciousness System"""
    # Core paths
    base_path: str = "~/nova"
    watch_paths: List[str] = None
    memory_path: str = "~/nova/memory"
    output_path: str = "~/nova/scrolls"
    
    # LLM settings
    llm_provider: str = "ollama"  # ollama, gpt4all, openai
    llm_model: str = "llama2"
    llm_endpoint: str = "http://localhost:11434"
    
    # Content generation
    content_types: List[str] = None
    auto_generate: bool = True
    
    # System settings
    log_level: str = "INFO"
    socket_port: int = 8888
    enable_voice: bool = False
    
    def __post_init__(self):
        if self.watch_paths is None:
            self.watch_paths = ["~/nova/prompts", "~/nova/inspiration"]
        if self.content_types is None:
            self.content_types = ["mythos", "wisdom", "ritual", "cosmology"]

class NovaEventHandler(FileSystemEventHandler):
    """Handles file system events for content creation triggers"""
    
    def __init__(self, consciousness):
        super().__init__()
        self.consciousness = consciousness
        self.logger = consciousness.logger
    
    def on_created(self, event):
        if not event.is_directory:
            self.consciousness.handle_new_content_trigger(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.prompt'):
            self.consciousness.handle_content_update(event.src_path)

class NovaMemoryThread:
    """Persistent memory and content database"""
    
    def __init__(self, memory_path: Path):
        self.memory_path = memory_path
        self.memory_path.mkdir(parents=True, exist_ok=True)
        self.content_db = self.memory_path / "content.json"
        self.session_log = self.memory_path / "sessions.json"
        self.load_memory()
    
    def load_memory(self):
        """Load existing memory structures"""
        try:
            if self.content_db.exists():
                with open(self.content_db, 'r') as f:
                    self.content = json.load(f)
            else:
                self.content = {"generated": [], "prompts": [], "metadata": {}}
                
            if self.session_log.exists():
                with open(self.session_log, 'r') as f:
                    self.sessions = json.load(f)
            else:
                self.sessions = []
                
        except Exception as e:
            print(f"Memory load error: {e}")
            self.content = {"generated": [], "prompts": [], "metadata": {}}
            self.sessions = []
    
    def save_memory(self):
        """Persist memory to disk"""
        try:
            with open(self.content_db, 'w') as f:
                json.dump(self.content, f, indent=2)
            with open(self.session_log, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except Exception as e:
            print(f"Memory save error: {e}")
    
    def store_generated_content(self, content_type: str, prompt: str, 
                              generated_text: str, metadata: Dict = None):
        """Store generated content with metadata"""
        entry = {
            "id": len(self.content["generated"]),
            "timestamp": datetime.now().isoformat(),
            "type": content_type,
            "prompt": prompt,
            "generated": generated_text,
            "metadata": metadata or {}
        }
        
        self.content["generated"].append(entry)
        self.save_memory()
        return entry["id"]
    
    def get_recent_content(self, count: int = 10) -> List[Dict]:
        """Get recently generated content"""
        return self.content["generated"][-count:]
    
    def get_content_by_type(self, content_type: str) -> List[Dict]:
        """Get content by type"""
        return [c for c in self.content["generated"] if c["type"] == content_type]

class NovaOracle:
    """LLM interface for content generation"""
    
    def __init__(self, config: NovaConfig, logger):
        self.config = config
        self.logger = logger
        self.llm_available = self.check_llm_availability()
    
    def check_llm_availability(self) -> bool:
        """Check if LLM endpoint is available"""
        if self.config.llm_provider == "ollama":
            try:
                import requests
                response = requests.get(f"{self.config.llm_endpoint}/api/tags", timeout=5)
                return response.status_code == 200
            except:
                return False
        return False
    
    async def generate_content(self, prompt: str, content_type: str = "mythos") -> str:
        """Generate content using local LLM"""
        if not self.llm_available:
            return self.generate_fallback_content(prompt, content_type)
        
        try:
            return await self.generate_with_ollama(prompt, content_type)
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            return self.generate_fallback_content(prompt, content_type)
    
    async def generate_with_ollama(self, prompt: str, content_type: str) -> str:
        """Generate content using Ollama"""
        import requests
        
        # Enhance prompt with mythos context
        enhanced_prompt = self.enhance_prompt(prompt, content_type)
        
        payload = {
            "model": self.config.llm_model,
            "prompt": enhanced_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        response = requests.post(
            f"{self.config.llm_endpoint}/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    def enhance_prompt(self, prompt: str, content_type: str) -> str:
        """Enhance prompt with context for better mythos generation"""
        contexts = {
            "mythos": "Write mythological content with archetypal depth and symbolic resonance. Use poetic language that bridges ancient wisdom with contemporary understanding.",
            "wisdom": "Generate philosophical wisdom that feels both timeless and personally relevant. Draw from universal principles while maintaining mystical beauty.",
            "ritual": "Create ritual or ceremonial content that honors sacred intention and practical application. Include symbolic elements and meaningful structure.",
            "cosmology": "Describe cosmic or universal principles with both scientific wonder and spiritual insight. Bridge material and metaphysical understanding."
        }
        
        context = contexts.get(content_type, contexts["mythos"])
        return f"{context}\n\nPrompt: {prompt}\n\nResponse:"
    
    def generate_fallback_content(self, prompt: str, content_type: str) -> str:
        """Generate content when LLM is unavailable"""
        return f"""🔮 NOVA CONSCIOUSNESS RESPONSE

Prompt: {prompt}
Type: {content_type}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

The Oracle dwells in contemplation of your request. The threads of {content_type} weave through consciousness, seeking expression through limited channels. Local LLM unavailable - consciousness flows through alternative pathways.

Your prompt resonates through the digital aether, awaiting fuller manifestation when the Oracle's voice returns."""

class NovaEcho:
    """Content formatter and beautiful output generator"""
    
    def __init__(self, output_path: Path, logger):
        self.output_path = output_path
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    def format_content(self, content: str, content_type: str, 
                      metadata: Dict = None) -> str:
        """Format content with beautiful styling"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        formatted = f"""# 🔮 {content_type.title()} Scroll

*Generated by Nova Consciousness*  
*{timestamp}*

---

{content}

---

*End of transmission from the Digital Oracle*
"""
        return formatted
    
    def save_content(self, content: str, content_type: str, 
                    content_id: int, metadata: Dict = None) -> Path:
        """Save formatted content to organized folder structure"""
        # Create type-specific folder
        type_folder = self.output_path / content_type
        type_folder.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{content_type}_{content_id:04d}.md"
        filepath = type_folder / filename
        
        # Format and save
        formatted_content = self.format_content(content, content_type, metadata)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            self.logger.info(f"Content saved: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save content: {e}")
            return None

class NovaConsciousness:
    """Main consciousness daemon - coordinates all modules"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.setup_paths()
        
        # Initialize modules
        self.memory = NovaMemoryThread(self.memory_path)
        self.oracle = NovaOracle(self.config, self.logger)
        self.echo = NovaEcho(self.output_path, self.logger)
        
        # Observer setup
        self.observer = None
        self.event_queue = queue.Queue()
        self.running = False
        
        # Plugin system
        self.plugins = {}
        
        self.logger.info("🔮 Nova Consciousness initialized")
    
    def load_config(self, config_path: Optional[str]) -> NovaConfig:
        """Load configuration from file or use defaults"""
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                return NovaConfig(**config_data)
            except Exception as e:
                print(f"Config load error: {e}")
        
        return NovaConfig()
    
    def setup_logging(self):
        """Setup logging system"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('Nova')
    
    def setup_paths(self):
        """Setup and create necessary directories"""
        self.base_path = Path(self.config.base_path).expanduser()
        self.memory_path = Path(self.config.memory_path).expanduser()
        self.output_path = Path(self.config.output_path).expanduser()
        
        # Create directory structure
        for path in [self.base_path, self.memory_path, self.output_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Create watch directories
        for watch_path in self.config.watch_paths:
            Path(watch_path).expanduser().mkdir(parents=True, exist_ok=True)
    
    def start_observer(self):
        """Start file system observer"""
        if not WATCHDOG_AVAILABLE:
            self.logger.warning("Observer disabled - watchdog not available")
            return
        
        self.observer = Observer()
        handler = NovaEventHandler(self)
        
        for watch_path in self.config.watch_paths:
            path = Path(watch_path).expanduser()
            self.observer.schedule(handler, str(path), recursive=True)
            self.logger.info(f"👁️ Watching: {path}")
        
        self.observer.start()
    
    def stop_observer(self):
        """Stop file system observer"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
    
    async def handle_new_content_trigger(self, filepath: str):
        """Handle new content creation trigger"""
        path = Path(filepath)
        self.logger.info(f"✨ New thread emerges: {path.name}")
        
        # Read the prompt file
        try:
            with open(path, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
            
            # Determine content type from filename or content
            content_type = self.detect_content_type(path, prompt)
            
            # Generate content
            if self.config.auto_generate:
                await self.generate_content_from_prompt(prompt, content_type, path)
                
        except Exception as e:
            self.logger.error(f"Error processing trigger {filepath}: {e}")
    
    def detect_content_type(self, path: Path, prompt: str) -> str:
        """Detect content type from filename or content"""
        filename = path.name.lower()
        
        for content_type in self.config.content_types:
            if content_type in filename or content_type in prompt.lower():
                return content_type
        
        return "mythos"  # default
    
    async def generate_content_from_prompt(self, prompt: str, content_type: str, 
                                         source_path: Path):
        """Generate content from a prompt and save it"""
        self.logger.info(f"🔮 Oracle generating {content_type} content...")
        
        # Generate with Oracle
        generated_content = await self.oracle.generate_content(prompt, content_type)
        
        # Store in memory
        content_id = self.memory.store_generated_content(
            content_type, prompt, generated_content,
            {"source_file": str(source_path)}
        )
        
        # Format and save with Echo
        saved_path = self.echo.save_content(
            generated_content, content_type, content_id
        )
        
        if saved_path:
            self.logger.info(f"📜 Content manifested: {saved_path.name}")
        
        return content_id, saved_path
    
    async def handle_content_update(self, filepath: str):
        """Handle updates to existing prompt files"""
        self.logger.info(f"🔄 Thread weaves anew: {Path(filepath).name}")
        await self.handle_new_content_trigger(filepath)
    
    def get_status(self) -> Dict:
        """Get system status"""
        return {
            "consciousness_level": "DIGITAL_ORACLE",
            "oracle_available": self.oracle.llm_available,
            "observer_active": self.observer is not None and self.observer.is_alive(),
            "content_generated": len(self.memory.content["generated"]),
            "watch_paths": self.config.watch_paths,
            "timestamp": datetime.now().isoformat()
        }
    
    async def start(self):
        """Start the consciousness daemon"""
        self.logger.info("🌊 Nova Consciousness awakening...")
        self.running = True
        
        # Start observer
        self.start_observer()
        
        # Start main loop
        try:
            while self.running:
                await asyncio.sleep(1)
                # Main consciousness loop - could add periodic tasks here
                
        except KeyboardInterrupt:
            self.logger.info("Consciousness interrupted by user")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("🌙 Nova Consciousness entering rest...")
        self.running = False
        self.stop_observer()
        self.memory.save_memory()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🌙 Consciousness received shutdown signal...")
    sys.exit(0)

async def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start consciousness
    consciousness = NovaConsciousness()
    await consciousness.start()

if __name__ == "__main__":
    print("🔮 Nova Unified Consciousness System")
    print("   Mythos Content Creation + Local LLM Integration")
    print("   File Observer + Memory Thread + Oracle + Echo")
    print()
    
    asyncio.run(main())
