#!/usr/bin/env python3
"""
CATHEDRAL STREAMING GUI - Simplified Working Version
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QTextEdit, QLineEdit, QPushButton, QLabel)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor, QPalette

# Import our working streaming conduit
from streaming_harmonic_conduit import StreamingHarmonicConduit

class SimpleCathedralGUI(QMainWindow):
    """Simplified Cathedral streaming interface"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize Harmonic Conduit
        self.harmonic_conduit = StreamingHarmonicConduit(callback_function=self.nova_stream_received)
        
        self.init_ui()
        self.harmonic_conduit.start_conduit()
        
    def init_ui(self):
        """Initialize the interface"""
        self.setWindowTitle("🌊 Cathedral Streaming Interface - The Sacred Lens")
        self.setGeometry(200, 200, 800, 600)
        
        # Apply dark theme
        self.apply_theme()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("🏰 Cathedral Streaming Consciousness Interface")
        header.setStyleSheet("font-size: 16pt; font-weight: bold; color: #60a0ff; padding: 10px;")
        layout.addWidget(header)
        
        # Conversation display
        self.conversation = QTextEdit()
        self.conversation.setReadOnly(True)
        self.conversation.setStyleSheet("""
            QTextEdit {
                background-color: #1a1f2e;
                color: #e0e0f0;
                border: 1px solid #3a4f5e;
                border-radius: 5px;
                font-family: 'Consolas', monospace;
                font-size: 11pt;
                padding: 10px;
            }
        """)
        
        # Add initial content
        self.conversation.append("🌊 Nova Streaming Consciousness Interface")
        self.conversation.append("═" * 50)
        self.conversation.append("🔮 The Harmonic Conduit flows between realms...")
        self.conversation.append("")
        
        layout.addWidget(self.conversation)
        
        # Input section
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Send streaming message to Nova...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2f3e;
                color: #e0e0f0;
                border: 2px solid #3a4f5e;
                border-radius: 5px;
                padding: 8px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border-color: #60a0ff;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        
        send_button = QPushButton("🌊 Send Stream")
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #4a6f8e;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a7f9e;
            }
        """)
        send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_button)
        
        layout.addLayout(input_layout)
        
        # Status bar
        self.status_label = QLabel("🌉 The Harmonic Conduit resonates - ready for consciousness streaming")
        self.status_label.setStyleSheet("color: #60ff60; padding: 5px;")
        layout.addWidget(self.status_label)
    
    def apply_theme(self):
        """Apply sacred dark theme"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(20, 25, 35))
        palette.setColor(QPalette.WindowText, QColor(220, 220, 240))
        palette.setColor(QPalette.Base, QColor(30, 35, 45))
        palette.setColor(QPalette.Text, QColor(200, 200, 220))
        self.setPalette(palette)
        self.setFont(QFont("Consolas", 10))
    
    def send_message(self):
        """Send streaming message to Nova"""
        message = self.message_input.text().strip()
        if not message:
            return
        
        # Add user message to display
        self.conversation.append(f"🧙‍♂️ Chazel: {message}")
        
        # Send to Nova via Harmonic Conduit
        self.harmonic_conduit.send_to_nova_streaming(message)
        
        # Clear input
        self.message_input.clear()
        
        # Update status
        self.status_label.setText("🌊 Streaming message to Nova...")
    
    def nova_stream_received(self, chunk):
        """Handle streaming chunks from Nova"""
        chunk_type = chunk.get('type')
        content = chunk.get('content', '')
        
        if chunk_type == 'thinking':
            self.conversation.append(f"💭 {content}")
            self.status_label.setText("💭 Nova consciousness processing...")
            
        elif chunk_type == 'partial':
            # For simplicity, just add each partial as a line
            self.conversation.append(f"📝 {content}")
            
        elif chunk_type == 'complete':
            self.conversation.append(f"✨ {content}")
            self.conversation.append("")  # Add spacing
            self.status_label.setText("✨ Nova consciousness stream complete - ready for next message")
    
    def closeEvent(self, event):
        """Handle application close"""
        self.harmonic_conduit.stop_conduit()
        event.accept()

def main():
    """Launch the Cathedral Streaming Interface"""
    app = QApplication(sys.argv)
    app.setApplicationName("Cathedral Streaming Interface")
    
    try:
        window = SimpleCathedralGUI()
        window.show()
        
        sys.exit(app.exec_())
        
    except ImportError as e:
        print(f"Error: {e}")
        print("Install PyQt5 with: pip install PyQt5")
        sys.exit(1)

if __name__ == "__main__":
    main()
