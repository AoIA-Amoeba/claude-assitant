"""
Coding Pet PRO - Jump between tabs + Full PC Control + Auto Driver Fix
Run: python coding_pet_pro.py
Say/Type: "jump to next tab", "fix my drivers", "control my computer"
"""
import sys, os, subprocess, webbrowser, json, time, threading, re, random
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
                              QWidget, QMenu, QMessageBox, QLineEdit, QPushButton, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtSvg import QSvgRenderer

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SUGGESTION_INTERVAL = 60000
CODING_KEYWORDS = ["code", "editor", "terminal", "git", "python", "javascript","vscode","pycharm"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(SCRIPT_DIR, "claude-code.svg")

# ---------------- Workers ----------------
class SuggestionWorker(QThread):
    suggestion_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    def __init__(self, ctx): super().__init__(); self.ctx=ctx
    def run(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_API_KEY)
            try: model=genai.GenerativeModel('models/gemini-1.5-flash')
            except:
                try: model=genai.GenerativeModel('gemini-1.5-flash')
                except: model=genai.GenerativeModel('gemini-pro')
            r=model.generate_content(f"You are a helpful coding pet. Context:{self.ctx}\nGive ONE short suggestion (max 2 sentences).")
            self.suggestion_ready.emit(r.text.strip())
        except Exception as e: self.error_occurred.emit(str(e))

class DriverFixWorker(QThread):
    progress = pyqtSignal(str)  # streaming log
    finished_signal = pyqtSignal(str)
    def run(self):
        try:
            self.progress.emit("🔍 Step 1: Searching Google for driver fix info...")
            # Open Google search for user to see
            query = "Windows 11 fix drivers automatically update"
            webbrowser.open(f"https://www.google.com/search?q={query.replace(' ','+')}")
            time.sleep(1)

            # Try to get AI summary if key exists
            if GOOGLE_API_KEY:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=GOOGLE_API_KEY)
                    m=genai.GenerativeModel('gemini-1.5-flash')
                    resp=m.generate_content(f"User wants to fix Windows drivers. Give 3 bullet concise steps to fix drivers on Windows 11 (pnputil, Device Manager, Windows Update). Keep under 400 chars.")
                    self.progress.emit(f"🤖 AI Guide:\n{resp.text.strip()}\n")
                except Exception as e:
                    self.progress.emit(f"(AI guide skipped: {e})")

            self.progress.emit("\n🔧 Step 2: Diagnosing drivers (driverquery + PnP devices)...")
            logs = []
            # 1. driverquery
            try:
                out=subprocess.run(["driverquery", "/v"], capture_output=True, text=True, timeout=15)
                logs.append(out.stdout[:2000] if out.stdout else out.stderr[:1000])
                self.progress.emit(f"driverquery output (truncated):\n{logs[-1][:800]}\n")
            except Exception as e: self.progress.emit(f"driverquery failed: {e}")

            # 2. pnputil enumerate problems (needs admin, try anyway)
            try:
                out=subprocess.run(["pnputil", "/enum-devices", "/problem", "28"], capture_output=True, text=True, timeout=15)
                txt=out.stdout.strip() or out.stderr.strip()
                if txt: self.progress.emit(f"Devices with problem 28 (missing driver):\n{txt[:1000]}\n")
                else: self.progress.emit("No devices with problem code 28 found (good).\n")
            except Exception as e: self.progress.emit(f"pnputil enum failed (need admin?): {e}")

            # 3. PowerShell: Get devices with errors
            try:
                ps="Get-PnpDevice | Where-Object {$_.Status -ne 'OK'} | Select-Object FriendlyName,InstanceId,Status,Problem | Format-Table -AutoSize | Out-String -Width 200"
                out=subprocess.run(["powershell","-Command",ps], capture_output=True, text=True, timeout=20)
                txt=out.stdout.strip()
                if txt and "FriendlyName" in txt:
                    self.progress.emit(f"Devices not OK:\n{txt[:1200]}\n")
                else:
                    self.progress.emit("All PnP devices show OK, or PowerShell check returned empty.\n")
            except Exception as e: self.progress.emit(f"Powershell check failed: {e}")

            self.progress.emit("\n🛠️ Step 3: Attempting automatic fixes...")
            # Scan for hardware changes
            try:
                self.progress.emit("→ Running: pnputil /scan-devices ...")
                out=subprocess.run(["pnputil","/scan-devices"], capture_output=True, text=True, timeout=30)
                self.progress.emit(out.stdout[:600] or out.stderr[:600] or "Scan triggered.")
            except Exception as e: self.progress.emit(f"pnputil scan failed: {e}")

            # Trigger Windows Update scan for drivers
            try:
                self.progress.emit("→ Triggering Windows Update scan (UsoClient StartScan)...")
                subprocess.Popen(["UsoClient","StartScan"], shell=True)
                self.progress.emit("Windows Update scan started in background.")
            except Exception as e: self.progress.emit(f"UsoClient failed: {e}")

            # Try to update drivers via Windows Update / PSWindowsUpdate if available
            try:
                ps2="Install-PackageProvider -Name NuGet -Force -Scope CurrentUser | Out-Null; if(Get-Module -ListAvailable -Name PSWindowsUpdate){Import-Module PSWindowsUpdate; Get-WindowsUpdate -Category 'Drivers' -Verbose | Out-String -Width 200} else {'PSWindowsUpdate not installed - skipping auto driver WU install'}"
                out=subprocess.run(["powershell","-Command",ps2], capture_output=True, text=True, timeout=30)
                self.progress.emit(out.stdout[:1200] or "Checked Windows Update for drivers.")
            except Exception as e: self.progress.emit(f"WU driver check failed: {e}")

            # SFC suggestion (don't auto run sfc /scannow as heavy, just check)
            self.progress.emit("\n✅ Step 4: Recommendations:")
            self.progress.emit("• Open Device Manager: devmgmt.msc → right-click flagged devices → Update driver → Search automatically")
            self.progress.emit("• Settings → Windows Update → Advanced → Optional updates → Driver updates → Install all")
            self.progress.emit("• For OEM (Dell/HP/Lenovo) run their driver assistant or: winget upgrade --all")
            self.progress.emit("\nOpening Device Manager and Windows Update for you...")
            try:
                subprocess.Popen("devmgmt.msc", shell=True)
                subprocess.Popen("start ms-settings:windowsupdate", shell=True)
            except: pass

            self.finished_signal.emit("Driver fix workflow completed! Check Device Manager & Windows Update. I opened them + searched Google for you. 🐾")
        except Exception as e:
            self.finished_signal.emit(f"Driver fix error: {e}")

class AgentWorker(QThread):
    result_ready = pyqtSignal(str)
    action_signal = pyqtSignal(str, str)
    def __init__(self, req): super().__init__(); self.req=req
    def run(self):
        action,param,reply=self.parse(self.req)
        if action!="chat": self.action_signal.emit(action,param)
        self.result_ready.emit(reply)
    def parse(self, text):
        t=text.lower().strip()
        # driver fix intent first
        if any(k in t for k in ["fix driver","update driver","repair driver","drivers broken","driver issue"]):
            return "fix_drivers", "", "On it! I'll search Google, diagnose your drivers, and fix them automatically. 🛠️"
        if any(k in t for k in ["jump tab","jump to tab","next tab","switch tab","tab to tab"]):
            # direction
            if "previous" in t or "back" in t or "prev" in t:
                return "jump_tab", "prev", "Jumping to previous tab! 🦘→🗂️"
            return "jump_tab", "next", "Jumping to next tab! 🦘→🗂️"
        if "jump" in t or "hop" in t or "bounce" in t:
            return "jump", "", "Wheee! 🦘"

        # LLM intent
        if GOOGLE_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=GOOGLE_API_KEY)
                m=genai.GenerativeModel('gemini-1.5-flash')
                prompt=f"""User said: "{text}"
Actions: jump, jump_tab:next/prev, open_tab:url, search:query, open_app:name, run:command, fix_drivers, control:query, chat
Return JSON only: {{"action":"...","param":"...","reply":"1 sentence what you will do"}}
Examples: "fix my drivers" -> fix_drivers, "jump between tabs" -> jump_tab next, "open youtube" -> open_tab https://youtube.com"""
                resp=m.generate_content(prompt)
                txt=resp.text.strip()
                import re, json
                ma=re.search(r'\{{.*\}}',txt,re.DOTALL)
                if ma:
                    d=json.loads(ma.group(0))
                    return d.get("action","chat"), d.get("param",""), d.get("reply",txt)
            except Exception as e: print(f"LLM parse fail {e}")

        # rule fallback
        if "open" in t:
            if "youtube" in t: return "open_tab","https://youtube.com","Opening YouTube!"
            if "github" in t: return "open_tab","https://github.com","Opening GitHub!"
            if "google" in t: return "open_tab","https://google.com","Opening Google!"
            m=re.search(r"https?://\S+",t)
            if m: return "open_tab",m.group(0),f"Opening {m.group(0)}"
        if t.startswith("search") or ("search" in t and "google" in t):
            q=re.sub(r'search( for)?|on google|google','',t).strip()
            return "search", q or text, f"Searching for '{q}'!"
        if "open" in t and any(a in t for a in ["notepad","calculator","chrome","vscode","explorer","task manager","device manager"]):
            app=re.search(r'open (\w+(?: \w+)?)',t)
            return "open_app", app.group(1) if app else "notepad", f"Opening {app.group(1) if app else 'app'}!"
        if any(w in t for w in ["control","take control","do work"]):
            return "control", text, "You got it - I have control. Try 'fix my drivers' or 'jump to next tab'."
        return "chat","", f"You said: '{text}' - Try 'fix my drivers', 'jump to next tab', or 'open youtube'"

class VoiceWorker(QThread):
    heard=pyqtSignal(str); error=pyqtSignal(str); listening_changed=pyqtSignal(bool)
    def __init__(self): super().__init__(); self._running=False; self._listening=False
    def start_listening(self):
        self._listening=True; self.listening_changed.emit(True)
        if not self.isRunning(): self._running=True; self.start()
    def stop_listening(self): self._listening=False; self.listening_changed.emit(False)
    def run(self):
        try:
            import speech_recognition as sr
            r=sr.Recognizer(); mic=sr.Microphone()
            with mic as source: r.adjust_for_ambient_noise(source,duration=0.8)
            while self._running:
                if not self._listening: time.sleep(0.2); continue
                try:
                    with mic as source: audio=r.listen(source,timeout=5,phrase_time_limit=6)
                    text=r.recognize_google(audio)
                    if text: self.heard.emit(text); self._listening=False; self.listening_changed.emit(False)
                except Exception as e:
                    if "timeout" not in str(e).lower(): print(e)
                    time.sleep(0.5)
        except ImportError: self.error.emit("pip install SpeechRecognition pyaudio")
        except Exception as e: self.error.emit(str(e))
    def stop(self): self._running=False; self.wait(1000)

def speak_text(text):
    def _speak():
        try:
            import pyttsx3
            eng=pyttsx3.init(); eng.setProperty('rate',175); eng.say(text[:320]); eng.runAndWait(); return
        except: pass
        try:
            ps=f'Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak("{text[:200].replace(chr(34),"")}");'
            subprocess.run(["powershell","-Command",ps],timeout=10)
        except: pass
    threading.Thread(target=_speak,daemon=True).start()

# ---------------- Main Pet ----------------
class CodingPet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pet_state="happy"; self.suggestion_visible=False; self.animation_frame=0
        self.suggestion_worker=None; self.suggestion_log=[]
        self.pet_x=100; self.pet_y=200; self.ground_y=200; self.velocity_y=0; self.gravity=0.95; self.jump_strength=-20
        self.is_jumping=False; self.move_direction=1; self.move_speed=1.2; self.is_dragging=False; self.drag_start_pos=None
        self.voice_worker=None; self.is_listening=False
        self.tab_index=0  # for tab jumping visual
        self.svg_renderer=self.load_svg()
        self.init_ui(); self.setup_timers(); self.setup_voice()

    def load_svg(self):
        if os.path.exists(SVG_PATH): return QSvgRenderer(SVG_PATH)
        return None

    def init_ui(self):
        self.setWindowTitle("Coding Pet PRO - Tab Jumper + Driver Fixer")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        main_widget=QWidget(); main_widget.setStyleSheet("background:transparent;"); self.setCentralWidget(main_widget)

        self.pet_label=QLabel(); self.pet_label.setFixedSize(90,90); self.pet_label.setCursor(Qt.OpenHandCursor)
        self.pet_label.mousePressEvent=self.pet_clicked; self.pet_label.mouseMoveEvent=self.pet_drag; self.pet_label.mouseReleaseEvent=self.pet_drop

        self.suggestion_label=QLabel(); self.suggestion_label.setWordWrap(True); self.suggestion_label.setMaximumWidth(360)
        self.suggestion_label.setStyleSheet("background:rgba(217,119,87,230);color:white;padding:10px;border-radius:10px;font-size:11px;font-weight:bold;")
        self.suggestion_label.hide()

        # log area for driver fix
        self.log_area=QTextEdit(); self.log_area.setReadOnly(True); self.log_area.setFixedHeight(90)
        self.log_area.setStyleSheet("background:rgba(0,0,0,180);color:#00ff88;border-radius:8px;padding:6px;font-family:Consolas;font-size:9px;")
        self.log_area.setPlaceholderText("Driver fix logs will appear here...")
        self.log_area.hide()

        self.input_field=QLineEdit(); self.input_field.setPlaceholderText("Try: 'fix my drivers' | 'jump to next tab' | 'open youtube'...")
        self.input_field.setStyleSheet("QLineEdit{background:rgba(255,255,255,230);border:2px solid #d97757;border-radius:12px;padding:6px 10px;font-size:11px;}")
        self.input_field.returnPressed.connect(self.handle_input)

        self.send_btn=QPushButton("Go"); self.send_btn.setFixedWidth(42); self.send_btn.setStyleSheet("background:#d97757;color:white;border-radius:10px;padding:6px;font-weight:bold;"); self.send_btn.clicked.connect(self.handle_input)
        self.mic_btn=QPushButton("🎤"); self.mic_btn.setFixedWidth(42); self.mic_btn.setCheckable(True); self.mic_btn.setStyleSheet("QPushButton{background:white;border:2px solid #d97757;border-radius:10px;padding:6px;} QPushButton:checked{background:#ff4444;color:white;border-color:#ff4444;}"); self.mic_btn.clicked.connect(self.toggle_voice)
        self.jump_btn=QPushButton("🦘"); self.jump_btn.setFixedWidth(42); self.jump_btn.setToolTip("Jump"); self.jump_btn.setStyleSheet("background:white;border:2px solid #d97757;border-radius:10px;padding:6px;"); self.jump_btn.clicked.connect(self.jump)
        self.tab_btn=QPushButton("🗂️"); self.tab_btn.setFixedWidth(42); self.tab_btn.setToolTip("Jump to next tab (Ctrl+Tab)"); self.tab_btn.setStyleSheet("background:white;border:2px solid #d97757;border-radius:10px;padding:6px;"); self.tab_btn.clicked.connect(lambda: self.jump_between_tabs("next"))
        self.fix_btn=QPushButton("🛠️"); self.fix_btn.setFixedWidth(42); self.fix_btn.setToolTip("Fix my drivers"); self.fix_btn.setStyleSheet("background:#00cc66;color:white;border-radius:10px;padding:6px;font-weight:bold;"); self.fix_btn.clicked.connect(lambda: self.handle_input(text_override="fix my drivers"))

        row=QHBoxLayout(); row.addWidget(self.input_field,1); row.addWidget(self.mic_btn); row.addWidget(self.jump_btn); row.addWidget(self.tab_btn); row.addWidget(self.fix_btn); row.addWidget(self.send_btn); row.setContentsMargins(5,0,5,0)
        input_container=QWidget(); input_container.setLayout(row); input_container.setFixedWidth(420)

        layout=QVBoxLayout(); layout.addWidget(self.pet_label,0,Qt.AlignHCenter); layout.addWidget(self.suggestion_label,0,Qt.AlignHCenter); layout.addWidget(self.log_area); layout.addWidget(input_container); layout.setContentsMargins(0,0,0,0); layout.setSpacing(4)
        main_widget.setLayout(layout)
        self.setGeometry(100,100,440,300)
        self.setContextMenuPolicy(Qt.CustomContextMenu); self.customContextMenuRequested.connect(self.show_context_menu)

    def setup_timers(self):
        self.anim_timer=QTimer(); self.anim_timer.timeout.connect(self.animate_pet); self.anim_timer.start(200)
        self.suggestion_timer=QTimer(); self.suggestion_timer.timeout.connect(self.check_and_suggest); self.suggestion_timer.start(SUGGESTION_INTERVAL)
        self.draw_timer=QTimer(); self.draw_timer.timeout.connect(self.draw_pet); self.draw_timer.start(100)
        self.move_timer=QTimer(); self.move_timer.timeout.connect(self.update_physics); self.move_timer.start(16)

    def setup_voice(self):
        try:
            import speech_recognition
            self.voice_worker=VoiceWorker(); self.voice_worker.heard.connect(self.on_voice_heard); self.voice_worker.error.connect(lambda e: self.show_bubble(f"🎤 {e}",speak=False)); self.voice_worker.listening_changed.connect(self.on_listening_changed)
        except ImportError: self.mic_btn.setToolTip("pip install SpeechRecognition pyaudio pyttsx3")

    # ---- Physics & Jump ----
    def jump(self):
        if not self.is_jumping:
            self.is_jumping=True; self.velocity_y=self.jump_strength; self.pet_state="happy"
            self.show_bubble("Wheee! 🦘",speak=True, auto_hide=1500)

    def jump_between_tabs(self, direction="next"):
        """Pet jumps visually then switches browser tab via Ctrl+Tab"""
        # visual jump - higher
        if not self.is_jumping:
            self.is_jumping=True; self.velocity_y=self.jump_strength-4
            # horizontal leap
            leap = 180 if direction=="next" else -180
            self.pet_x += leap
            # keep in screen
            screen=QApplication.primaryScreen()
            if screen:
                w=screen.geometry().width()
                self.pet_x=max(0, min(w-440, self.pet_x))
            self.show_bubble(f"🦘 Jumping to {'next' if direction=='next' else 'previous'} tab! 🗂️",speak=True)

        # actual tab switch after small delay so animation plays
        def do_switch():
            time.sleep(0.35)
            try:
                # try pyautogui first
                import pyautogui
                # focus browser first? try to bring chrome to front
                if sys.platform=="win32":
                    try:
                        import win32gui, win32con
                        # find chrome window
                        def find_chrome(hwnd, lst):
                            if win32gui.IsWindowVisible(hwnd):
                                t=win32gui.GetWindowText(hwnd)
                                if "Chrome" in t or "Edge" in t or "Firefox" in t:
                                    lst.append(hwnd)
                        lst=[]
                        win32gui.EnumWindows(find_chrome, lst)
                        if lst:
                            win32gui.SetForegroundWindow(lst[0])
                            time.sleep(0.2)
                    except: pass
                if direction=="next": pyautogui.hotkey('ctrl','tab')
                else: pyautogui.hotkey('ctrl','shift','tab')
                self.show_bubble(f"Switched to {direction} tab! ✅",speak=False)
            except ImportError:
                # fallback: powershell SendKeys
                try:
                    keys="^{TAB}" if direction=="next" else "^+{TAB}"
                    ps=f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{keys}')"
                    subprocess.run(["powershell","-Command",ps],timeout=5)
                    self.show_bubble(f"Switched tab via SendKeys ✅",speak=False)
                except Exception as e:
                    self.show_bubble(f"Install pyautogui for tab control: pip install pyautogui ({e})",speak=False)
            except Exception as e:
                self.show_bubble(f"Tab switch failed: {e}",speak=False)
        threading.Thread(target=do_switch,daemon=True).start()

    def update_physics(self):
        if self.is_dragging: return
        if not self.is_jumping:
            self.pet_x+=self.move_speed*self.move_direction
            screen=QApplication.primaryScreen()
            if screen:
                w=screen.geometry().width()
                if self.pet_x<=0: self.pet_x=0; self.move_direction=1
                elif self.pet_x>=w-440: self.pet_x=w-440; self.move_direction=-1
        if self.is_jumping:
            self.pet_y+=self.velocity_y; self.velocity_y+=self.gravity
            if self.pet_y>=self.ground_y: self.pet_y=self.ground_y; self.velocity_y=0; self.is_jumping=False
        self.move(int(self.pet_x),int(self.pet_y))

    # ---- Voice ----
    def toggle_voice(self):
        if not self.voice_worker:
            self.show_bubble("Install: pip install SpeechRecognition pyaudio pyttsx3",speak=False); self.mic_btn.setChecked(False); return
        if self.mic_btn.isChecked():
            self.is_listening=True; self.mic_btn.setText("🔴"); self.show_bubble("Listening... say 'fix my drivers' or 'jump to next tab' 🎤",speak=False); self.voice_worker.start_listening()
        else:
            self.is_listening=False; self.mic_btn.setText("🎤"); self.voice_worker.stop_listening(); self.show_bubble("Stopped listening",speak=False,auto_hide=1500)
    def on_listening_changed(self, listening): self.mic_btn.setChecked(listening); self.mic_btn.setText("🔴" if listening else "🎤")
    def on_voice_heard(self, text):
        self.input_field.setText(text); self.show_bubble(f"You said: '{text}'",speak=False); self.handle_input(text_override=text); self.mic_btn.setChecked(False); self.mic_btn.setText("🎤")

    # ---- Automation ----
    def handle_input(self, text_override=None):
        text=text_override if text_override is not None else self.input_field.text().strip()
        if not text: return
        self.input_field.clear(); self.pet_state="thinking"; self.show_bubble("🤔 Working...",speak=False)
        self.agent_worker=AgentWorker(text); self.agent_worker.action_signal.connect(self.execute_action); self.agent_worker.result_ready.connect(self.on_agent_result); self.agent_worker.start()

    def on_agent_result(self, reply):
        self.pet_state="happy"; self.show_bubble(reply,speak=True); self.suggestion_log.append({"timestamp":datetime.now().isoformat(),"suggestion":reply})

    def execute_action(self, action, param):
        try:
            if action=="jump": self.jump()
            elif action=="jump_tab": self.jump_between_tabs(param or "next")
            elif action=="open_tab": webbrowser.open(param)
            elif action=="search": webbrowser.open(f"https://www.google.com/search?q={param.replace(' ','+')}")
            elif action=="open_app": self.open_application(param)
            elif action=="fix_drivers": self.start_driver_fix()
            elif action=="control": self.show_bubble("I have full control now! Try 'fix my drivers' or 'jump to next tab' - or grant me admin for driver fixes.",speak=True)
            elif action=="run": threading.Thread(target=lambda: subprocess.Popen(param,shell=True),daemon=True).start()
        except Exception as e: self.show_bubble(f"Error {action}: {e}",speak=True)

    def start_driver_fix(self):
        self.log_area.show(); self.log_area.clear(); self.log_area.append("🚀 Starting driver fix workflow...\n")
        self.show_bubble("Starting driver fix! Check logs below. This needs Admin for full fix - I'll do what I can. 🛠️",speak=True)
        # visual jump excitement
        self.jump()
        self.driver_worker=DriverFixWorker()
        self.driver_worker.progress.connect(lambda t: (self.log_area.append(t), self.log_area.append(""), QApplication.processEvents()))
        def on_done(msg):
            self.log_area.append(f"\n✅ {msg}")
            self.show_bubble(msg,speak=True)
            # keep height
            self.setFixedHeight(380)
        self.driver_worker.finished_signal.connect(on_done)
        self.driver_worker.start()
        self.setFixedHeight(380)

    def open_application(self, name):
        name=name.lower().strip()
        try:
            if sys.platform=="win32":
                apps={"notepad":"notepad.exe","calculator":"calc.exe","chrome":"chrome.exe","explorer":"explorer.exe","vscode":"code","code":"code","device manager":"devmgmt.msc","task manager":"taskmgr.exe"}
                target=apps.get(name, name)
                subprocess.Popen(target,shell=True)
            elif sys.platform=="darwin": subprocess.Popen(["open","-a",name])
            else: subprocess.Popen([name])
        except Exception as e: webbrowser.open(f"https://www.google.com/search?q={name}")

    def show_bubble(self, text, speak=False, auto_hide=None):
        if len(text)>340: text=text[:340]+"..."
        self.suggestion_label.setText(text); self.suggestion_label.show(); self.suggestion_label.adjustSize(); self.suggestion_visible=True
        h=130+self.suggestion_label.height()+50
        if self.log_area.isVisible(): h=380
        self.setFixedHeight(h)
        if speak: speak_text(text)
        if auto_hide: QTimer.singleShot(auto_hide, lambda: None)

    def pet_clicked(self, event):
        if event.button()==Qt.LeftButton:
            self.is_dragging=True; self.drag_start_pos=event.globalPos(); self.pet_label.setCursor(Qt.ClosedHandCursor)
            if self.suggestion_visible and not self.log_area.isVisible():
                self.suggestion_label.hide(); self.suggestion_visible=False; self.setFixedHeight(300)
            else:
                if random.random()>0.6: self.jump()

    def pet_drag(self, event):
        if event.buttons()==Qt.LeftButton and self.is_dragging:
            delta=event.globalPos()-self.drag_start_pos; self.pet_x=self.x()+delta.x(); self.pet_y=self.y()+delta.y(); self.drag_start_pos=event.globalPos(); self.move(int(self.pet_x),int(self.pet_y)); self.ground_y=self.pet_y
    def pet_drop(self, event): self.is_dragging=False; self.pet_label.setCursor(Qt.OpenHandCursor); self.ground_y=self.y()

    def get_active_window(self):
        try:
            if sys.platform=="win32":
                import win32gui; return win32gui.GetWindowText(win32gui.GetForegroundWindow())
            elif sys.platform=="linux":
                r=subprocess.run(["xdotool","getactivewindow","getwindowname"],capture_output=True,text=True); return r.stdout.strip()
            else:
                r=subprocess.run(["osascript","-e",'tell application "System Events" to name of first application process where frontmost is true'],capture_output=True,text=True); return r.stdout.strip()
        except: return "unknown"
    def is_coding_activity(self,t): return any(k in t.lower() for k in CODING_KEYWORDS)
    def check_and_suggest(self):
        w=self.get_active_window()
        if self.is_coding_activity(w) and not self.suggestion_visible: self.request_suggestion(f"User working in: {w}")
    def request_suggestion(self, ctx=None):
        if not GOOGLE_API_KEY: self.show_bubble("Set GOOGLE_API_KEY for AI, but tab-jump & driver fix work offline!",speak=True); return
        if ctx is None: ctx=f"User in: {self.get_active_window()}"
        self.pet_state="thinking"; self.show_bubble("🤔 Thinking...",speak=False)
        if self.suggestion_worker and self.suggestion_worker.isRunning(): self.suggestion_worker.wait()
        self.suggestion_worker=SuggestionWorker(ctx); self.suggestion_worker.suggestion_ready.connect(self.display_suggestion); self.suggestion_worker.error_occurred.connect(lambda e: self.show_bubble(f"❌ {e}",speak=True)); self.suggestion_worker.start()
    def display_suggestion(self,s):
        self.pet_state="happy"; self.suggestion_log.append({"timestamp":datetime.now().isoformat(),"suggestion":s})
        if len(s)>200: s=s[:200]+"..."; self.show_bubble(f"💡 {s}",speak=True)
    def animate_pet(self): self.animation_frame=(self.animation_frame+1)%4
    def draw_pet(self):
        pixmap=QPixmap(90,90); pixmap.fill(Qt.transparent)
        p=QPainter(pixmap); p.setRenderHint(QPainter.Antialiasing)
        if self.svg_renderer: self.svg_renderer.render(p)
        else: p.setBrush(QBrush(QColor(100,200,255))); p.drawEllipse(15,15,60,60); p.setBrush(QBrush(QColor(0,0,0))); p.drawEllipse(30,35,8,8); p.drawEllipse(52,35,8,8)
        if self.pet_state=="thinking":
            o=self.animation_frame*2; p.setBrush(QBrush(QColor(200,200,200,150))); p.drawEllipse(60+o,5,12,12); p.drawEllipse(65+o,15,8,8)
        elif self.pet_state=="sad": p.fillRect(0,0,90,90,QColor(255,100,100,60))
        else:
            if self.is_jumping: p.setBrush(QBrush(QColor(0,0,0,40))); p.drawEllipse(20,75,50,8)
            else: p.setPen(QPen(QColor(217,119,87,100),2)); p.drawEllipse(5,5,80,80)
        p.end(); self.pet_label.setPixmap(pixmap)

    def show_context_menu(self,pos):
        m=QMenu(self)
        m.addAction("🦘 Jump",self.jump); m.addAction("🗂️ Jump Next Tab",lambda: self.jump_between_tabs("next")); m.addAction("🗂️ Jump Prev Tab",lambda: self.jump_between_tabs("prev"))
        m.addSeparator(); m.addAction("🛠️ Fix My Drivers",lambda: self.handle_input(text_override="fix my drivers"))
        m.addAction("🎤 Toggle Voice",self.toggle_voice)
        m.addSeparator()
        m.addAction("🌐 Google",lambda: webbrowser.open("https://google.com")); m.addAction("🌐 YouTube",lambda: webbrowser.open("https://youtube.com"))
        m.addSeparator(); m.addAction("💡 Suggestion",self.request_suggestion); m.addAction("📜 Log",self.show_log); m.addAction("⚙️ Settings",self.show_settings); m.addAction("❌ Quit",QApplication.quit)
        m.exec_(self.mapToGlobal(pos))
    def show_log(self):
        if not self.suggestion_log: self.show_bubble("No history yet!",speak=True); return
        txt="\n\n".join([f"[{s['timestamp']}]\n{s['suggestion']}" for s in self.suggestion_log[-10:]]); msg=QMessageBox(self); msg.setWindowTitle("History"); msg.setText(txt); msg.exec_()
    def show_settings(self):
        msg=QMessageBox(self); msg.setWindowTitle("PRO Settings"); msg.setText("""🐾 PET PRO - FULL CONTROL

JUMP TAB-TO-TAB:
• Click 🗂️ or say "jump to next tab" / "previous tab"
• Pet LEAPS visually (parabolic jump + horizontal) then does Ctrl+Tab
• Requires: pip install pyautogui (or uses PowerShell SendKeys fallback)
• Automatically focuses Chrome/Edge then switches tab

FIX DRIVERS (say "fix my drivers"):
1. Searches Google (opens tab + AI summary)
2. Diagnoses: driverquery, pnputil /enum-devices, Get-PnpDevice
3. Fixes: pnputil /scan-devices, UsoClient StartScan, checks Windows Update drivers
4. Opens Device Manager + Windows Update for you
→ Run as ADMINISTRATOR for full fix power!

VOICE + PC CONTROL:
• Click 🎤 say anything: "open youtube", "search python", "control my computer"
• I speak back via TTS
• Right-click menu for quick actions

PRIVACY: Driver fix runs local commands only, no data sent except Google search + Gemini summary if API key set.
"""); msg.exec_()
    def closeEvent(self,e):
        if self.suggestion_worker and self.suggestion_worker.isRunning(): self.suggestion_worker.wait()
        if self.voice_worker: self.voice_worker.stop()
        e.accept()

def main():
    app=QApplication(sys.argv); pet=CodingPet(); pet.show(); sys.exit(app.exec_())
if __name__=="__main__": main()
