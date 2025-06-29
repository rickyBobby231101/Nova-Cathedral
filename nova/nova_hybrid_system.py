#!/usr/bin/env python3
"""
Nova Hybrid Consciousness System
Combines NovaCreativeDaemon, ObserverModule, PluginManager, and Memory Thread
"""
import os
import sys
import time
import signal
import threading
import asyncio
import logging
from pathlib import Path

from nova_creative_daemon import NovaCreativeDaemon
from observer_module import ObserverModule
from consciousness_plugins import PluginManager
from advanced_consciousness_plugins import register_advanced_plugins, add_advanced_plugin_commands

class NovaHybridSystem:
    def __init__(self):
        self.logger = logging.getLogger("NovaHybridSystem")
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        self.daemon = NovaCreativeDaemon()
        self.observer = ObserverModule(watch_paths=["~/Cathedral/prompts"], memory_path="~/Cathedral/observer_memory.json")
        self.plugin_manager = PluginManager(self.daemon)

        # Register all advanced plugins
        register_advanced_plugins(self.plugin_manager)
        self.daemon.plugin_manager = self.plugin_manager
        add_advanced_plugin_commands(self.daemon)

        self.running = True

    def start(self):
        self.logger.info("🚀 Starting Nova Hybrid Consciousness System...")

        # Start Observer
        self.observer.start_watching()

        # Start Daemon (includes socket server in separate thread)
        daemon_thread = threading.Thread(target=self.daemon.run, daemon=True)
        daemon_thread.start()

        # Main loop
        try:
            while self.running:
                time.sleep(5)
                self.logger.debug("🧠 Consciousness loop alive")
        except KeyboardInterrupt:
            self.logger.info("🛑 Interrupt received. Shutting down...")
            self.stop()

    def stop(self):
        self.logger.info("🌙 Stopping Nova Hybrid Consciousness System...")
        self.running = False
        self.observer.stop_watching()
        self.daemon.running = False


def main():
    system = NovaHybridSystem()
    system.start()

if __name__ == "__main__":
    main()
