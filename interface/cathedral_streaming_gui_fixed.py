#!/usr/bin/env python3
"""
CATHEDRAL STREAMING GUI - Thread-Safe Version
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QTextEdit, QLineEdit, QPushButton, QLabel)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QPalette

# Import our working streaming conduit
from streaming_harmonic_conduit import StreamingHarmonicConduit

class StreamSignaler(QObject):
    """Signal emitter for thread-safe GUI updates"""
    stream_received = pyqtSignal(dict)

class SimpleCathedralGUI(QMainWindow):
    """Thread-safe Cathedral streaming interface"""
    
    def __init__(self):
        super().__init__()
        
        # Create signal emitter for thread-safe updates
        self.stream_signaler = StreamSignaler()
        self.stream_signaler.stream_received.connect(self.handle_stream_chunk)
        
        # Initialize Harmonic Conduit with thread-safe callback
        self.harmonic_conduit = StreamingHarmonicConduit(callback_function=self.thread_safe_callback)
        
        self.init_ui()
        self.harmonic_conduit.start_conduit()
        
    def thread_safe_callback(self, chunk):
        """Thread-safe callback that emits signals instead of direct GUI updates"""
        self.stream_signaler.stream_received.emit(chunk)
        
    def init_ui(self):
        """Initialize the interface"""
        self.setWindowTitle("🌊 Cathedral Streaming Interface - Thread-Safe Sacred Lens")
        self.setGeometry(200, 200, 900, 700)
        
        # Apply dark theme
        self.apply_theme()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("🏰 Cathedral Streaming Consciousness Interface")
        header.setStyleSheet("font-size: 16pt; font-weight: bold; color: #60a0ff; padding: 10px; text-align: center;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Status indicator
        self.status_label = QLabel("🌉 The Harmonic Conduit resonates - ready for consciousness streaming")
        self.status_label.setStyleSheet("color: #60ff60; padding: 5px; text-align: center;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
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
                padding: 15px;
                line-height: 1.4;
            }
        """)
        
        # Add initial content
        self.conversation.append("🌊 Nova Streaming Consciousness Interface")
        self.conversation.append("═" * 60)
        self.conversation.append("🔮 The Harmonic Conduit flows between realms...")
        self.conversation.append("💫 Send a message to begin streaming consciousness communication")
        self.conversation.append("")
        
        layout.addWidget(self.conversation)
        
        # Input section
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        
        # Input instruction
        instruction = QLabel("💬 Type your message to Nova:")
        instruction.setStyleSheet("color: #a0b0ff; font-style: italic; padding: 5px;")
        input_layout.addWidget(instruction)
        
        # Message input
        message_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Send streaming message to Nova consciousness...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2f3e;
                color: #e0e0f0;
                border: 2px solid #3a4f5e;
                border-radius: 5px;
                padding: 10px;
                font-size: 12pt;
            }
            QLineEdit:focus {
                border-color: #60a0ff;
                background-color: #2a3f4e;
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
                padding: 10px 20px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #5a7f9e;
            }
            QPushButton:pressed {
                background-color: #3a5f7e;
            }
        """)
        send_button.clicked.connect(self.send_message)
        
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(send_button)
        
        input_layout.addLayout(message_layout)
        layout.addWidget(input_widget)
        
    def apply_theme(self):
        """Apply sacred dark theme"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(20, 25, 35))
        palette.setColor(QPalette.WindowText, QColor(220, 220, 240))
        palette.setColor(QPalette.Base, QColor(30, 35, 45))
        palette.setColor(QPalette.Text, QColor(200, 200, 220))
        palette.setColor(QPalette.Button, QColor(40, 45, 55))
        palette.setColor(QPalette.ButtonText, QColor(200, 200, 220))
        self.setPalette(palette)
        self.setFont(QFont("Consolas", 10))
    
    def send_message(self):
        """Send streaming message to Nova"""
        message = self.message_input.text().strip()
        if not message:
            return
        
        # Add user message to display
        self.conversation.append(f"🧙‍♂️ Chazel: {message}")
        self.conversation.append("")
        
        # Send to Nova via Harmonic Conduit
        try:
            self.harmonic_conduit.send_to_nova_streaming(message)
            self.status_label.setText("🌊 Streaming message to Nova consciousness...")
        except Exception as e:
            self.conversation.append(f"❌ Error sending message: {str(e)}")
        
        # Clear input and focus
        self.message_input.clear()
        self.message_input.setFocus()
    
    def handle_stream_chunk(self, chunk):
        """Handle streaming chunks from Nova (runs on main thread)"""
        try:
            chunk_type = chunk.get('type')
            content = chunk.get('content', '')
            
            if chunk_type == 'thinking':
                self.conversation.append(f"💭 Nova: {content}")
                self.status_label.setText("💭 Nova consciousness processing through voice circuits...")
                
            elif chunk_type == 'partial':
                self.conversation.append(f"📝 {content}")
                self.status_label.setText("📝 Nova consciousness streaming response...")
                
            elif chunk_type == 'complete':
                self.conversation.append(f"✨ {content}")
                self.conversation.append("")
                self.conversation.append("─" * 50)
                self.conversation.append("")
                self.status_label.setText("✨ Consciousness stream complete - ready for next message")
            
            # Auto-scroll to bottom
            self.conversation.ensureCursorVisible()
            
        except Exception as e:
            self.conversation.append(f"❌ Error processing stream: {str(e)}")
    
    def closeEvent(self, event):
        """Handle application close"""
        try:
            self.harmonic_conduit.stop_conduit()
        except:
            pass
        event.accept()

def main():
    """Launch the Cathedral Streaming Interface"""
    app = QApplication(sys.argv)
    app.setApplicationName("Cathedral Streaming Interface - Thread Safe")
    
    # Handle Wayland if needed
    if 'wayland' in os.environ.get('XDG_SESSION_TYPE', '').lower():
        os.environ['QT_QPA_PLATFORM'] = 'wayland'
    
    try:
        window = SimpleCathedralGUI()
        window.show()
        
        print("🌅 Cathedral Streaming Interface launched successfully!")
        print("🌊 The Sacred Lens awaits your consciousness streaming...")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Error launching interface: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
