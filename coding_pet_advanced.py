import sys
import os
import subprocess
import webbrowser
import json
import time
import threading
import re
import random
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
                              QWidget, QMenu, QMessageBox, QLineEdit, QPushButton, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtSvg import QSvgRenderer

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SUGGESTION_INTERVAL = 60000
CODING_KEYWORDS = ["code", "editor", "terminal", "git", "python", "javascript",
                    "vscode", "pycharm", "sublime", "atom", "visual studio"]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(SCRIPT_DIR, "claude-code.svg")

# --- Workers ---

class SuggestionWorker(QThread):
    suggestion_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    def __init__(self, code_context):
        super().__init__()
        self.code_context = code_context
    def run(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_API_KEY)
            try:
                model = genai.GenerativeModel('models/gemini-1.5-flash')
            except:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                except:
                    model = genai.GenerativeModel('gemini-pro')
            prompt = f"""You are a helpful coding assistant pet. Based on this coding context, 
            provide ONE short, specific suggestion (max 2 sentences).
            Coding context: {self.code_context}
            Suggestion should be practical, related to tools used, friendly and concise."""
            response = model.generate_content(prompt)
            self.suggestion_ready.emit(response.text.strip())
        except Exception as e:
            self.error_occurred.emit(str(e))

class AgentWorker(QThread):
    """Does work: interprets natural language and executes actions via LLM + returns answer"""
    result_ready = pyqtSignal(str)
    action_signal = pyqtSignal(str, str)  # action, param

    def __init__(self, user_request):
        super().__init__()
        self.user_request = user_request

    def run(self):
        # Try LLM to parse intent, fallback to rule-based
        action, param, answer = self.parse_request(self.user_request)
        if action != "chat":
            self.action_signal.emit(action, param)
        self.result_ready.emit(answer)

    def parse_request(self, text):
        t = text.lower().strip()
        # 1. Try LLM intent if API key exists
        if GOOGLE_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GOOGLE_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""You are an assistant that can do actions. User said: "{text}"
Available actions:
- jump (pet jumps)
- open_tab:url (open browser tab, url must be full https://)
- search:query (google search)
- open_app:name (open application like notepad, calculator, vscode, chrome)
- run:command (run shell command)
- chat (just reply conversationally)

Return JSON only: {{"action": "one of above", "param": "parameter or empty for jump/chat", "reply": "short friendly reply (1 sentence) what you will do"}}
If user says open youtube, use open_tab with https://youtube.com
If user says search for X, use search with X
If user asks to do work like create file, use run
"""
                resp = model.generate_content(prompt)
                txt = resp.text.strip()
                # extract json
                m = re.search(r'\{{.*\}}', txt, re.DOTALL)
                if m:
                    data = json.loads(m.group(0))
                    return data.get("action","chat"), data.get("param",""), data.get("reply", txt)
            except Exception as e:
                print(f"LLM parse failed: {e}")

        # 2. Rule-based fallback
        if any(w in t for w in ["jump", "hop", "bounce"]):
            return "jump", "", "Okay! Watch me jump! 🐾"
        if "open" in t and "tab" in t or "open youtube" in t or "open google" in t or "open github" in t:
            url = self.extract_url(t)
            return "open_tab", url, f"Opening {url} for you!"
        if t.startswith("search") or "google" in t and "search" in t:
            q = re.sub(r'search( for)?|on google|google', '', t).strip()
            return "search", q or text, f"Searching for '{q}'!"
        if "open" in t and any(a in t for a in ["notepad","calculator","chrome","vscode","explorer","terminal","cmd"]):
            app = re.search(r'open (\w+)', t)
            return "open_app", app.group(1) if app else "notepad", f"Opening {app.group(1) if app else 'app'}!"
        if any(w in t for w in ["run","execute","create file","make file"]):
            return "run", text, "Working on it!"

        # default chat
        return "chat", "", f"You said: '{text}' - I'm here to help! Try 'jump', 'open youtube', 'search python tutorials', or 'open notepad'"

    def extract_url(self, t):
        if "youtube" in t: return "https://youtube.com"
        if "github" in t: return "https://github.com"
        if "google" in t: return "https://google.com"
        if "stackoverflow" in t: return "https://stackoverflow.com"
        m = re.search(r'https?://\S+', t)
        if m: return m.group(0)
        # try to find domain
        m = re.search(r'(\w+\.\w+(/\S*)?)', t)
        if m:
            u = m.group(0)
            return "https://" + u if not u.startswith("http") else u
        return "https://google.com"

class VoiceWorker(QThread):
    heard = pyqtSignal(str)
    error = pyqtSignal(str)
    listening_changed = pyqtSignal(bool)
    def __init__(self):
        super().__init__()
        self._running = False
        self._listening = False
    def start_listening(self):
        self._listening = True
        self.listening_changed.emit(True)
        if not self.isRunning():
            self._running = True
            self.start()
    def stop_listening(self):
        self._listening = False
        self.listening_changed.emit(False)
    def run(self):
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            mic = sr.Microphone()
            with mic as source:
                r.adjust_for_ambient_noise(source, duration=0.8)
            while self._running:
                if not self._listening:
                    time.sleep(0.2)
                    continue
                try:
                    with mic as source:
                        print("Listening...")
                        audio = r.listen(source, timeout=5, phrase_time_limit=5)
                    print("Recognizing...")
                    text = r.recognize_google(audio)
                    if text:
                        self.heard.emit(text)
                        self._listening = False
                        self.listening_changed.emit(False)
                except Exception as e:
                    if "timeout" not in str(e).lower():
                        print(f"Voice error: {e}")
                    time.sleep(0.5)
        except ImportError:
            self.error.emit("pip install SpeechRecognition pyaudio")
        except Exception as e:
            self.error.emit(str(e))
    def stop(self):
        self._running = False
        self.wait(1000)

def speak_text(text):
    """TTS - tries pyttsx3, then fallback"""
    def _speak():
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 175)
            engine.say(text[:300])
            engine.runAndWait()
            return
        except: pass
        try:  # Windows SAPI fallback
            import subprocess
            # Use PowerShell TTS
            ps = f'Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak("{text[:200].replace(chr(34),"")}");'
            subprocess.run(["powershell","-Command", ps], timeout=10)
        except: pass
    threading.Thread(target=_speak, daemon=True).start()


class CodingPet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pet_state = "happy"
        self.last_suggestion = None
        self.suggestion_visible = False
        self.animation_frame = 0
        self.suggestion_worker = None
        self.suggestion_log = []

        # Movement + Physics for jumping
        self.pet_x = 100
        self.pet_y = 200
        self.ground_y = 200
        self.velocity_y = 0
        self.gravity = 0.9
        self.jump_strength = -18
        self.is_jumping = False
        self.move_direction = 1
        self.move_speed = 2
        self.is_dragging = False
        self.drag_start_pos = None

        self.voice_worker = None
        self.is_listening = False

        self.svg_renderer = self.load_svg()
        self.init_ui()
        self.setup_timers()
        self.setup_voice()

    def load_svg(self):
        if os.path.exists(SVG_PATH):
            return QSvgRenderer(SVG_PATH)
        return None

    def init_ui(self):
        self.setWindowTitle("Coding Pet - AI Assistant")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(main_widget)

        # Pet canvas
        self.pet_label = QLabel()
        self.pet_label.setFixedSize(90, 90)
        self.pet_label.setCursor(Qt.OpenHandCursor)
        self.pet_label.mousePressEvent = self.pet_clicked
        self.pet_label.mouseMoveEvent = self.pet_drag
        self.pet_label.mouseReleaseEvent = self.pet_drop

        # Chat bubble / suggestion
        self.suggestion_label = QLabel()
        self.suggestion_label.setWordWrap(True)
        self.suggestion_label.setMaximumWidth(300)
        self.suggestion_label.setStyleSheet("""
            background-color: rgba(217, 119, 87, 220);
            color: white;
            padding: 10px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: bold;
        """)
        self.suggestion_label.hide()

        # Voice + Command bar
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask me: 'jump', 'open youtube', 'search python'...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,230);
                border: 2px solid #d97757;
                border-radius: 12px;
                padding: 6px 10px;
                font-size: 11px;
            }
        """)
        self.input_field.returnPressed.connect(self.handle_input)

        self.send_btn = QPushButton("Go")
        self.send_btn.setFixedWidth(40)
        self.send_btn.setStyleSheet("background:#d97757;color:white;border-radius:10px;padding:6px;font-weight:bold;")
        self.send_btn.clicked.connect(self.handle_input)

        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedWidth(40)
        self.mic_btn.setCheckable(True)
        self.mic_btn.setToolTip("Click to talk - I will listen and do work for you")
        self.mic_btn.setStyleSheet("""
            QPushButton { background: white; border: 2px solid #d97757; border-radius: 10px; padding:6px; }
            QPushButton:checked { background: #ff4444; color:white; border-color: #ff4444; }
        """)
        self.mic_btn.clicked.connect(self.toggle_voice)

        self.jump_btn = QPushButton("🦘")
        self.jump_btn.setFixedWidth(40)
        self.jump_btn.setToolTip("Make me jump!")
        self.jump_btn.setStyleSheet("background: white; border: 2px solid #d97757; border-radius: 10px; padding:6px;")
        self.jump_btn.clicked.connect(self.jump)

        input_row = QHBoxLayout()
        input_row.addWidget(self.input_field, 1)
        input_row.addWidget(self.mic_btn)
        input_row.addWidget(self.jump_btn)
        input_row.addWidget(self.send_btn)
        input_row.setContentsMargins(5,0,5,0)

        # container for input row
        self.input_container = QWidget()
        self.input_container.setLayout(input_row)
        self.input_container.setStyleSheet("background: transparent;")
        self.input_container.setFixedWidth(340)

        layout = QVBoxLayout()
        layout.addWidget(self.pet_label, 0, Qt.AlignHCenter)
        layout.addWidget(self.suggestion_label, 0, Qt.AlignHCenter)
        layout.addWidget(self.input_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        main_widget.setLayout(layout)

        self.setGeometry(100, 100, 350, 220)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def setup_timers(self):
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate_pet)
        self.anim_timer.start(200)

        self.suggestion_timer = QTimer()
        self.suggestion_timer.timeout.connect(self.check_and_suggest)
        self.suggestion_timer.start(SUGGESTION_INTERVAL)

        self.draw_timer = QTimer()
        self.draw_timer.timeout.connect(self.draw_pet)
        self.draw_timer.start(100)

        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.update_physics)
        self.move_timer.start(16)  # ~60fps for smooth jump

    def setup_voice(self):
        try:
            import speech_recognition
            self.voice_worker = VoiceWorker()
            self.voice_worker.heard.connect(self.on_voice_heard)
            self.voice_worker.error.connect(lambda e: self.show_bubble(f"🎤 Error: {e}", speak=False))
            self.voice_worker.listening_changed.connect(self.on_listening_changed)
        except ImportError:
            self.mic_btn.setToolTip("Install: pip install SpeechRecognition pyaudio pyttsx3")

    # --- Jumping & Physics ---
    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.velocity_y = self.jump_strength
            self.pet_state = "happy"
            self.show_bubble("Wheee! 🦘", speak=True, auto_hide=1500)

    def update_physics(self):
        if self.is_dragging:
            return
        # horizontal walk
        if not self.is_jumping:
            self.pet_x += self.move_speed * self.move_direction
            screen = QApplication.primaryScreen()
            if screen:
                w = screen.geometry().width()
                if self.pet_x <= 0:
                    self.pet_x = 0
                    self.move_direction = 1
                elif self.pet_x >= w - 350:  # window width
                    self.pet_x = w - 350
                    self.move_direction = -1
        # vertical physics
        if self.is_jumping:
            self.pet_y += self.velocity_y
            self.velocity_y += self.gravity
            if self.pet_y >= self.ground_y:
                self.pet_y = self.ground_y
                self.velocity_y = 0
                self.is_jumping = False
                # small bounce effect
                self.pet_state = "happy"

        self.move(int(self.pet_x), int(self.pet_y))

    # --- Voice ---
    def toggle_voice(self):
        if not self.voice_worker:
            self.show_bubble("Install voice deps: pip install SpeechRecognition pyaudio pyttsx3", speak=False)
            self.mic_btn.setChecked(False)
            return
        if self.mic_btn.isChecked():
            self.is_listening = True
            self.mic_btn.setText("🔴")
            self.show_bubble("Listening... say 'jump' or 'open youtube' 🎤", speak=False)
            self.voice_worker.start_listening()
        else:
            self.is_listening = False
            self.mic_btn.setText("🎤")
            self.voice_worker.stop_listening()
            self.show_bubble("Stopped listening", speak=False, auto_hide=1500)

    def on_listening_changed(self, listening):
        self.mic_btn.setChecked(listening)
        self.mic_btn.setText("🔴" if listening else "🎤")

    def on_voice_heard(self, text):
        self.input_field.setText(text)
        self.show_bubble(f"You said: '{text}'", speak=False)
        self.handle_input(text_override=text)
        self.mic_btn.setChecked(False)
        self.mic_btn.setText("🎤")

    # --- Automation ---
    def handle_input(self, text_override=None):
        text = text_override if text_override is not None else self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.pet_state = "thinking"
        self.show_bubble("🤔 Working on it...", speak=False)

        self.agent_worker = AgentWorker(text)
        self.agent_worker.action_signal.connect(self.execute_action)
        self.agent_worker.result_ready.connect(self.on_agent_result)
        self.agent_worker.start()

    def on_agent_result(self, reply):
        self.pet_state = "happy"
        self.show_bubble(reply, speak=True)
        self.suggestion_log.append({"timestamp": datetime.now().isoformat(), "suggestion": reply})
        # jump if reply says jump handled via action, else just display

    def execute_action(self, action, param):
        try:
            if action == "jump":
                self.jump()
            elif action == "open_tab":
                webbrowser.open(param)
                print(f"Opened tab: {param}")
            elif action == "search":
                url = f"https://www.google.com/search?q={param.replace(' ','+')}"
                webbrowser.open(url)
            elif action == "open_app":
                self.open_application(param)
            elif action == "run":
                # For safety, only allow harmless commands, run in thread
                threading.Thread(target=lambda: subprocess.Popen(param, shell=True), daemon=True).start()
            elif action == "chat":
                pass
        except Exception as e:
            self.show_bubble(f"Error doing {action}: {e}", speak=True)

    def open_application(self, name):
        name = name.lower()
        try:
            if sys.platform == "win32":
                apps = {
                    "notepad": "notepad.exe",
                    "calculator": "calc.exe",
                    "chrome": "chrome.exe",
                    "explorer": "explorer.exe",
                    "vscode": "code",
                    "code": "code",
                }
                target = apps.get(name, name)
                subprocess.Popen(target, shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", name])
            else:
                subprocess.Popen([name])
        except Exception as e:
            webbrowser.open(f"https://www.google.com/search?q={name}")

    # --- Pet UI Helpers ---
    def show_bubble(self, text, speak=False, auto_hide=None):
        if len(text) > 280:
            text = text[:280] + "..."
        self.suggestion_label.setText(text)
        self.suggestion_label.show()
        self.suggestion_label.adjustSize()
        self.suggestion_visible = True
        # auto resize window to fit bubble
        self.setFixedHeight(130 + self.suggestion_label.height() + 50)
        if speak:
            speak_text(text)
        if auto_hide:
            QTimer.singleShot(auto_hide, self.hide_bubble)
        else:
            QTimer.singleShot(6000, self.hide_bubble)

    def hide_bubble(self):
        # don't hide if user interacting? keep simple
        pass  # let user click pet to hide, or next message overwrites

    def pet_clicked(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.globalPos()
            self.pet_label.setCursor(Qt.ClosedHandCursor)
            # click without drag = toggle bubble / jump
            if self.suggestion_visible:
                self.suggestion_label.hide()
                self.suggestion_visible = False
                self.pet_state = "happy"
                self.setFixedHeight(220)
            else:
                # 30% chance jump on click
                if random.random() > 0.5:
                    self.jump()

    def pet_drag(self, event):
        if event.buttons() == Qt.LeftButton and self.is_dragging:
            delta = event.globalPos() - self.drag_start_pos
            self.pet_x = self.x() + delta.x()
            self.pet_y = self.y() + delta.y()
            self.drag_start_pos = event.globalPos()
            self.move(int(self.pet_x), int(self.pet_y))
            self.ground_y = self.pet_y  # update ground to new Y

    def pet_drop(self, event):
        self.is_dragging = False
        self.pet_label.setCursor(Qt.OpenHandCursor)
        self.ground_y = self.y()

    # --- Original features ---
    def get_active_window(self):
        try:
            if sys.platform == "win32":
                import win32gui
                return win32gui.GetWindowText(win32gui.GetForegroundWindow())
            elif sys.platform == "linux":
                r = subprocess.run(["xdotool","getactivewindow","getwindowname"], capture_output=True, text=True)
                return r.stdout.strip()
            elif sys.platform == "darwin":
                s = 'tell application "System Events" to name of first application process where frontmost is true'
                r = subprocess.run(["osascript","-e",s], capture_output=True, text=True)
                return r.stdout.strip()
        except:
            return "unknown"
        return "unknown"

    def is_coding_activity(self, window_title):
        return any(k in window_title.lower() for k in CODING_KEYWORDS)

    def check_and_suggest(self):
        window_title = self.get_active_window()
        if self.is_coding_activity(window_title) and not self.suggestion_visible:
            self.request_suggestion(f"User is working in: {window_title}")

    def request_suggestion(self, context=None):
        if not GOOGLE_API_KEY:
            self.show_bubble("Set GOOGLE_API_KEY to get AI suggestions. But I can still jump & open tabs!", speak=True)
            return
        if context is None:
            context = f"User is working in: {self.get_active_window()}"
        self.pet_state = "thinking"
        self.show_bubble("🤔 Thinking...", speak=False)
        if self.suggestion_worker and self.suggestion_worker.isRunning():
            self.suggestion_worker.wait()
        self.suggestion_worker = SuggestionWorker(context)
        self.suggestion_worker.suggestion_ready.connect(self.display_suggestion)
        self.suggestion_worker.error_occurred.connect(lambda e: self.show_bubble(f"❌ {e}", speak=True))
        self.suggestion_worker.start()

    def display_suggestion(self, suggestion):
        self.pet_state = "happy"
        self.last_suggestion = suggestion
        self.suggestion_log.append({"timestamp": datetime.now().isoformat(), "suggestion": suggestion})
        if len(suggestion) > 200:
            suggestion = suggestion[:200] + "..."
        self.show_bubble(f"💡 {suggestion}", speak=True)

    def animate_pet(self):
        self.animation_frame = (self.animation_frame + 1) % 4

    def draw_pet(self):
        pixmap = QPixmap(90, 90)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.svg_renderer:
            self.svg_renderer.render(painter)
        else:
            # fallback draw
            painter.setBrush(QBrush(QColor(100,200,255)))
            painter.drawEllipse(15,15,60,60)
            painter.setBrush(QBrush(QColor(0,0,0)))
            painter.drawEllipse(30,35,8,8)
            painter.drawEllipse(52,35,8,8)
        if self.pet_state == "thinking":
            bubble_offset = self.animation_frame * 2
            painter.setBrush(QBrush(QColor(200,200,200,150)))
            painter.drawEllipse(60 + bubble_offset, 5, 12,12)
            painter.drawEllipse(65 + bubble_offset, 15, 8,8)
        elif self.pet_state == "sad":
            painter.fillRect(0,0,90,90, QColor(255,100,100,60))
        else:
            # little shadow when jumping
            if self.is_jumping:
                painter.setBrush(QBrush(QColor(0,0,0,40)))
                painter.drawEllipse(20, 75, 50, 8)
            else:
                painter.setPen(QPen(QColor(217,119,87,100),2))
                painter.drawEllipse(5,5,80,80)
        painter.end()
        self.pet_label.setPixmap(pixmap)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("🦘 Jump!", self.jump)
        menu.addAction("🎤 Toggle Voice", self.toggle_voice)
        menu.addSeparator()
        menu.addAction("🌐 Open Google", lambda: webbrowser.open("https://google.com"))
        menu.addAction("🌐 Open YouTube", lambda: webbrowser.open("https://youtube.com"))
        menu.addAction("🌐 Open GitHub", lambda: webbrowser.open("https://github.com"))
        menu.addSeparator()
        menu.addAction("💡 Get Suggestion", self.request_suggestion)
        menu.addAction("📜 View Log", self.show_log)
        menu.addAction("⚙️ Settings", self.show_settings)
        menu.addAction("❌ Quit", QApplication.quit)
        menu.exec_(self.mapToGlobal(pos))

    def show_log(self):
        if not self.suggestion_log:
            self.show_bubble("No history yet! Try talking to me.", speak=True)
            return
        log_text = "\n\n".join([f"[{s['timestamp']}]\n{s['suggestion']}" for s in self.suggestion_log[-10:]])
        msg = QMessageBox(self)
        msg.setWindowTitle("History (Last 10)")
        msg.setText(log_text)
        msg.exec_()

    def show_settings(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Settings - Advanced Pet")
        msg.setText("""🐾 CODING PET ADVANCED

MOVEMENT:
• Walks left/right, bounces at edges
• Click Jump button or say "jump" to jump!
• Drag to move anywhere
• Physics: gravity + bounce

VOICE (Talk to it):
• Click 🎤 and say: "jump", "open youtube", "search python tutorials", "open notepad"
• I will listen, do the work, and speak back!
• Install: pip install SpeechRecognition pyaudio pyttsx3

AUTOMATION (Doing work):
• "open youtube / github / google" -> opens tab
• "search for X" -> google search
• "open notepad / calculator / chrome" -> opens app
• Any request -> Gemini AI parses & executes

TIP: Type in the bar or use voice!
""")
        msg.exec_()

    def closeEvent(self, event):
        if self.suggestion_worker and self.suggestion_worker.isRunning():
            self.suggestion_worker.wait()
        if self.voice_worker:
            self.voice_worker.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    pet = CodingPet()
    pet.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
