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
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPainter, QColor, QBrush, QPen, QImage
from PyQt5.QtCore import QObject
from PyQt5.QtSvg import QSvgRenderer

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")  # Set this as environment variable
SUGGESTION_INTERVAL = 60000  # Check every 60 seconds
CODING_KEYWORDS = ["code", "editor", "terminal", "git", "python", "javascript", 
                   "vscode", "pycharm", "sublime", "atom", "visual studio"]

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(SCRIPT_DIR, "claude-code.svg")

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
            # Try different model names in order
            try:
                model = genai.GenerativeModel('models/gemini-1.5-flash')
            except:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                except:
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
        
        # Movement variables
        self.move_direction = 1  # 1 for right, -1 for left
        self.move_speed = 2
        self.is_dragging = False
        self.drag_start_pos = None
        
        # Load SVG
        self.svg_renderer = self.load_svg()
        
        self.init_ui()
        self.setup_timers()
        
    def load_svg(self):
        """Load the SVG image"""
        if os.path.exists(SVG_PATH):
            return QSvgRenderer(SVG_PATH)
        else:
            print(f"Warning: SVG file not found at {SVG_PATH}")
            print(f"Make sure claude-code.svg is in the same directory as this script")
            return None
        
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Coding Pet")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main widget
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(main_widget)
        
        # Pet canvas
        self.pet_label = QLabel()
        self.pet_label.setFixedSize(80, 80)
        self.pet_label.setCursor(Qt.OpenHandCursor)
        self.pet_label.mousePressEvent = self.pet_clicked
        self.pet_label.mouseMoveEvent = self.pet_drag
        self.pet_label.mouseReleaseEvent = self.pet_drop
        
        # Suggestion label
        self.suggestion_label = QLabel()
        self.suggestion_label.setWordWrap(True)
        self.suggestion_label.setMaximumWidth(250)
        self.suggestion_label.setStyleSheet("""
            background-color: rgba(217, 119, 87, 220);
            color: white;
            padding: 8px;
            border-radius: 8px;
            font-size: 10px;
            font-weight: bold;
        """)
        self.suggestion_label.hide()
        
        layout = QVBoxLayout()
        layout.addWidget(self.pet_label)
        layout.addWidget(self.suggestion_label)
        layout.setContentsMargins(0, 0, 0, 0)
        main_widget.setLayout(layout)
        
        # Set initial window size
        self.setGeometry(100, 100, 80, 80)
        
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
        
        # Movement timer - pet moves around
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.move_pet)
        self.move_timer.start(50)  # Move every 50ms
    
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
    
    def move_pet(self):
        """Move the pet around the screen"""
        if self.is_dragging:
            return  # Don't auto-move while dragging
        
        # Move horizontally
        self.pet_x += self.move_speed * self.move_direction
        
        # Get screen size
        screen = QApplication.primaryScreen()
        screen_rect = screen.geometry()
        
        # Bounce at edges
        if self.pet_x <= 0:
            self.pet_x = 0
            self.move_direction = 1
        elif self.pet_x >= screen_rect.width() - 80:
            self.pet_x = screen_rect.width() - 80
            self.move_direction = -1
        
        # Update window position
        self.move(int(self.pet_x), int(self.pet_y))
    
    def pet_drag(self, event):
        """Handle pet dragging"""
        if event.buttons() == Qt.LeftButton and self.is_dragging:
            delta = event.globalPos() - self.drag_start_pos
            self.pet_x = self.x() + delta.x()
            self.pet_y = self.y() + delta.y()
            self.drag_start_pos = event.globalPos()
            self.move(int(self.pet_x), int(self.pet_y))
    
    def pet_drop(self, event):
        """Handle pet drop after dragging"""
        self.is_dragging = False
        self.pet_label.setCursor(Qt.OpenHandCursor)
    
    def pet_clicked(self, event):
        """Handle pet click"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.globalPos()
            self.pet_label.setCursor(Qt.ClosedHandCursor)
        
        if self.suggestion_visible:
            self.suggestion_label.hide()
            self.suggestion_visible = False
            self.pet_state = "happy"
        else:
            self.request_suggestion()
    
    def draw_pet(self):
        """Draw the pet character using SVG"""
        pixmap = QPixmap(80, 80)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.svg_renderer:
            self.svg_renderer.render(painter)
        
        if self.pet_state == "thinking":
            # Add thought bubble animation
            bubble_offset = self.animation_frame * 2
            painter.setBrush(QBrush(QColor(200, 200, 200, 150)))
            painter.drawEllipse(55 + bubble_offset, 5, 12, 12)
            painter.drawEllipse(60 + bubble_offset, 15, 8, 8)
            painter.drawEllipse(63 + bubble_offset, 23, 5, 5)
        
        elif self.pet_state == "sad":
            # Darken the image
            painter.fillRect(0, 0, 80, 80, QColor(255, 100, 100, 80))
        
        elif self.pet_state == "happy":
            # Add glow effect
            painter.setPen(QPen(QColor(217, 119, 87, 100), 2))
            painter.drawEllipse(5, 5, 70, 70)
        
        painter.end()
        self.pet_label.setPixmap(pixmap)
    
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
        msg.setText("""🐾 Coding Pet Settings:

MOVEMENT:
• Pet automatically moves left & right across screen
• Drag the pet to move it manually
• Pet bounces at screen edges

INTERACTION:
• Click the pet to get a suggestion
• Right-click for menu options
• Pet checks for coding every 60 seconds
• Suggestions are logged automatically

USING GOOGLE GEMINI API:
Get your API key at: https://ai.google.dev/

Files needed (same folder):
- coding_pet_google_with_image.py
- claude-code.svg
- requirements_google.txt
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
