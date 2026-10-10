import sys
import os
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import threading
import random

from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                             QWidget, QMenu, QSystemTrayIcon, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QRect, QSize, QPoint
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import QObject

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")  # Set this as environment variable
SUGGESTION_INTERVAL = 60000  # Check every 60 seconds
CODING_KEYWORDS = ["code", "editor", "terminal", "git", "python", "javascript", 
                   "vscode", "pycharm", "sublime", "atom", "visual studio"]

class SuggestionWorker(QThread):
    """Worker thread to fetch AI suggestions without blocking UI"""
    suggestion_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, code_context):
        super().__init__()
        self.code_context = code_context
        self.running = True
    
    def run(self):
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""You are a helpful coding assistant pet. Based on this coding context, 
            provide ONE short, specific suggestion (max 2 sentences) to help the developer.
            
            Coding context: {self.code_context}
            
            Suggestion should be:
            - Practical and actionable
            - Related to the language/tools being used
            - Friendly and concise
            - Either a code tip, useful library, prompt idea, or debugging hint
            
            Just provide the suggestion, no preamble."""
            
            response = model.generate_content(prompt)
            suggestion = response.text.strip()
            self.suggestion_ready.emit(suggestion)
        
        except Exception as e:
            self.error_occurred.emit(f"Error: {str(e)}")
    
    def stop(self):
        self.running = False


class CodingPet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pet_state = "happy"
        self.last_suggestion = None
        self.suggestion_visible = False
        self.pet_x = 100
        self.pet_y = 100
        self.animation_frame = 0
        self.suggestion_worker = None
        self.suggestion_log = []
        
        self.init_ui()
        self.setup_timers()
        
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Coding Pet")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main widget
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(main_widget)
        
        # Pet canvas - larger for animation
        self.pet_label = QLabel()
        self.pet_label.setFixedSize(120, 120)
        self.pet_label.setCursor(Qt.PointingHandCursor)
        self.pet_label.mousePressEvent = self.pet_clicked
        
        # Suggestion label
        self.suggestion_label = QLabel()
        self.suggestion_label.setWordWrap(True)
        self.suggestion_label.setMaximumWidth(300)
        self.suggestion_label.setStyleSheet("""
            background-color: rgba(100, 200, 255, 200);
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: bold;
        """)
        self.suggestion_label.hide()
        
        layout = QVBoxLayout()
        layout.addWidget(self.pet_label)
        layout.addWidget(self.suggestion_label)
        layout.setContentsMargins(0, 0, 0, 0)
        main_widget.setLayout(layout)
        
        # Set initial window size
        self.setGeometry(100, 100, 120, 120)
        
        # Create context menu
        self.create_context_menu()
        
    def create_context_menu(self):
        """Create right-click context menu"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def show_context_menu(self, pos):
        """Show context menu on right-click"""
        menu = QMenu(self)
        
        menu.addAction("Get Suggestion Now", self.request_suggestion)
        menu.addAction("View Suggestion Log", self.show_log)
        menu.addSeparator()
        menu.addAction("Settings", self.show_settings)
        menu.addAction("Quit", QApplication.quit)
        
        menu.exec_(self.mapToGlobal(pos))
    
    def pet_clicked(self, event):
        """Handle pet click"""
        if self.suggestion_visible:
            self.suggestion_label.hide()
            self.suggestion_visible = False
            self.pet_state = "happy"
        else:
            self.request_suggestion()
    
    def setup_timers(self):
        """Setup timers for animation and suggestions"""
        # Animation timer
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate_pet)
        self.anim_timer.start(200)
        
        # Suggestion timer
        self.suggestion_timer = QTimer()
        self.suggestion_timer.timeout.connect(self.check_and_suggest)
        self.suggestion_timer.start(SUGGESTION_INTERVAL)
        
        # Draw timer
        self.draw_timer = QTimer()
        self.draw_timer.timeout.connect(self.draw_pet)
        self.draw_timer.start(100)
    
    def get_active_window(self):
        """Get the active window title"""
        try:
            if sys.platform == "linux":
                result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True, text=True
                )
                return result.stdout.strip()
            elif sys.platform == "darwin":  # macOS
                script = 'tell application "System Events" to name of first application process where frontmost is true'
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True, text=True
                )
                return result.stdout.strip()
            elif sys.platform == "win32":  # Windows
                import win32gui
                window = win32gui.GetForegroundWindow()
                return win32gui.GetWindowText(window)
        except:
            return "unknown"
        return "unknown"
    
    def is_coding_activity(self, window_title):
        """Check if current window indicates coding activity"""
        window_title = window_title.lower()
        return any(keyword in window_title for keyword in CODING_KEYWORDS)
    
    def check_and_suggest(self):
        """Check if user is coding and request suggestion"""
        window_title = self.get_active_window()
        
        if self.is_coding_activity(window_title) and not self.suggestion_visible:
            # Extract context from window title
            context = f"User is working in: {window_title}"
            self.request_suggestion(context)
    
    def request_suggestion(self, context=None):
        """Request a suggestion from Google Gemini"""
        if not GOOGLE_API_KEY:
            self.show_message("Error", "Set GOOGLE_API_KEY environment variable")
            return
        
        if context is None:
            window_title = self.get_active_window()
            context = f"User is working in: {window_title}"
        
        self.pet_state = "thinking"
        self.suggestion_label.setText("🤔 Thinking...")
        self.suggestion_label.show()
        self.suggestion_visible = True
        
        # Cancel previous worker if still running
        if self.suggestion_worker and self.suggestion_worker.isRunning():
            self.suggestion_worker.stop()
            self.suggestion_worker.wait()
        
        # Create new worker thread
        self.suggestion_worker = SuggestionWorker(context)
        self.suggestion_worker.suggestion_ready.connect(self.display_suggestion)
        self.suggestion_worker.error_occurred.connect(self.handle_error)
        self.suggestion_worker.start()
    
    def display_suggestion(self, suggestion):
        """Display the suggestion from Gemini"""
        self.pet_state = "happy"
        self.last_suggestion = suggestion
        self.suggestion_log.append({
            "timestamp": datetime.now().isoformat(),
            "suggestion": suggestion
        })
        
        # Truncate suggestion if too long
        if len(suggestion) > 200:
            suggestion = suggestion[:200] + "..."
        
        self.suggestion_label.setText(f"💡 {suggestion}")
        self.suggestion_label.show()
        self.suggestion_visible = True
    
    def handle_error(self, error_msg):
        """Handle error from suggestion worker"""
        self.pet_state = "sad"
        self.suggestion_label.setText(f"❌ {error_msg}")
        self.suggestion_label.show()
    
    def animate_pet(self):
        """Update animation frame"""
        self.animation_frame = (self.animation_frame + 1) % 4
    
    def draw_pet(self):
        """Draw the pet character"""
        pixmap = QPixmap(120, 120)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw pet based on state
        if self.pet_state == "thinking":
            self.draw_thinking_pet(painter)
        elif self.pet_state == "happy":
            self.draw_happy_pet(painter)
        elif self.pet_state == "sad":
            self.draw_sad_pet(painter)
        
        painter.end()
        self.pet_label.setPixmap(pixmap)
    
    def draw_happy_pet(self, painter):
        """Draw happy pet (simple emoji-style)"""
        center_x, center_y = 60, 60
        
        # Body
        painter.setBrush(QBrush(QColor(100, 200, 255)))
        painter.drawEllipse(center_x - 30, center_y - 35, 60, 70)
        
        # Head
        painter.setBrush(QBrush(QColor(150, 220, 255)))
        painter.drawEllipse(center_x - 25, center_y - 50, 50, 50)
        
        # Eyes
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(center_x - 12, center_y - 35, 8, 8)
        painter.drawEllipse(center_x + 4, center_y - 35, 8, 8)
        
        # Mouth (smile)
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawArc(center_x - 10, center_y - 20, 20, 15, 0, -180 * 16)
        
        # Ears
        painter.setBrush(QBrush(QColor(100, 200, 255)))
        painter.drawEllipse(center_x - 28, center_y - 55, 12, 20)
        painter.drawEllipse(center_x + 16, center_y - 55, 12, 20)
    
    def draw_thinking_pet(self, painter):
        """Draw thinking pet"""
        center_x, center_y = 60, 60
        
        # Body
        painter.setBrush(QBrush(QColor(200, 180, 100)))
        painter.drawEllipse(center_x - 30, center_y - 35, 60, 70)
        
        # Head
        painter.setBrush(QBrush(QColor(220, 200, 120)))
        painter.drawEllipse(center_x - 25, center_y - 50, 50, 50)
        
        # Eyes (thinking look)
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(center_x - 12, center_y - 35, 8, 8)
        painter.drawEllipse(center_x + 4, center_y - 35, 8, 8)
        
        # Thought bubble
        bubble_offset = self.animation_frame * 3
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.drawEllipse(center_x + 20 + bubble_offset, center_y - 55, 15, 15)
    
    def draw_sad_pet(self, painter):
        """Draw sad pet"""
        center_x, center_y = 60, 60
        
        # Body
        painter.setBrush(QBrush(QColor(255, 150, 150)))
        painter.drawEllipse(center_x - 30, center_y - 35, 60, 70)
        
        # Head
        painter.setBrush(QBrush(QColor(255, 180, 180)))
        painter.drawEllipse(center_x - 25, center_y - 50, 50, 50)
        
        # Eyes (sad)
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(center_x - 12, center_y - 35, 8, 8)
        painter.drawEllipse(center_x + 4, center_y - 35, 8, 8)
        
        # Mouth (frown)
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawArc(center_x - 10, center_y - 15, 20, 15, 0, 180 * 16)
    
    def show_log(self):
        """Show suggestion log"""
        if not self.suggestion_log:
            self.show_message("Log", "No suggestions yet!")
            return
        
        log_text = "\n\n".join([f"[{s['timestamp']}]\n{s['suggestion']}" 
                               for s in self.suggestion_log[-10:]])
        self.show_message("Suggestion Log (Last 10)", log_text)
    
    def show_settings(self):
        """Show settings dialog"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Settings")
        msg.setText("""Coding Pet Settings:

• Pet checks for coding activity every 60 seconds
• Click the pet to dismiss suggestions
• Right-click for menu options
• Suggestions are logged automatically

Using Google Gemini API

To use Gemini suggestions, set:
export GOOGLE_API_KEY="your-api-key"

Get your free API key at:
https://ai.google.dev/
""")
        msg.exec_()
    
    def show_message(self, title, text):
        """Show a message box"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.exec_()
    
    def closeEvent(self, event):
        """Clean up on close"""
        if self.suggestion_worker and self.suggestion_worker.isRunning():
            self.suggestion_worker.stop()
            self.suggestion_worker.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    pet = CodingPet()
    pet.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
