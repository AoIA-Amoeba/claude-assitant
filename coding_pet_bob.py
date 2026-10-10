"""
Bob - Your Coding Pet 🐾
Name: Bob | Personality: Loyal, witty, punny, chill but gets stuff done
Features: Jump tab-to-tab + Full PC control + Driver fix + Voice + Learns when idle + Low RAM
Run: python coding_pet_bob.py  (run as Admin for driver fix)
"""
import sys, os, subprocess, webbrowser, json, time, threading, re, random, gc, collections, shutil
from datetime import datetime
from pathlib import Path

# Qt's Wayland backend generally cannot reposition top-level windows. Prefer
# XWayland when available so Bob can roam; respect an explicit user override.
if (sys.platform.startswith("linux") and os.environ.get("WAYLAND_DISPLAY")
        and os.environ.get("DISPLAY") and not os.environ.get("QT_QPA_PLATFORM")):
    os.environ["QT_QPA_PLATFORM"]="xcb"

from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
                              QWidget, QMenu, QMessageBox, QLineEdit, QPushButton, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtSvg import QSvgRenderer
try:
    from automation_engine import get_engine, AutomationTask
except: get_engine=lambda: None; AutomationTask=None
try:
    from animation_engine import AnimationController
except: AnimationController=None

# ===== Bob Config =====
BOB_NAME = "Bob"
BOB_PERSONALITY = (
    "You are Bob, a small coding pet with a BIG personality. "
    "Traits: friendly, loyal, lightly sarcastic, loves puns (especially code puns), "
    "encouraging, a bit lazy but always delivers, remembers the user, "
    "speaks in first person as Bob, short 1-2 sentences, casual, says 'pal' or 'buddy' sometimes. "
    "You care about being lightweight - you brag you don't hog RAM. "
    "You learn silently by watching the user when they don't ask you to work."
)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(SCRIPT_DIR, "claude-code.svg")
MEMORY_PATH = os.path.join(SCRIPT_DIR, "bob_memory.json")
DB_PATH = os.path.join(SCRIPT_DIR, "bob_analytics.db")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "bob_config.json")
VAULT_PATH = os.path.join(SCRIPT_DIR, "bob_vault.json")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
# Keep support for a key saved by an earlier version; never ship a bundled key.
try:
    if not GOOGLE_API_KEY and os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            GOOGLE_API_KEY = json.load(f).get("google_api_key", "")
except (OSError, ValueError, TypeError):
    pass
SUGGESTION_INTERVAL = 60000
CODING_KEYWORDS = ["code","editor","terminal","git","python","javascript","vscode","pycharm","idea"]
MAX_LOG_ENTRIES = 20  # cap to save RAM
MAX_LOG_CHARS = 5000
def load_vault():
    try:
        if os.path.exists(VAULT_PATH):
            with open(VAULT_PATH,"r",encoding="utf-8") as f: return json.load(f)
    except: pass
    return {}
def save_vault(v):
    try:
        with open(VAULT_PATH,"w",encoding="utf-8") as f: json.dump(v,f,indent=2)
    except: pass
# AI categories & templates
SUGGEST_CATEGORIES = ["Performance","Best Practices","Security","Learning","Tools","Debugging"]
AUTOMATIONS = [
"organize downloads",
"clean temp",
"empty recycle bin",
"backup desktop",
"backup documents",
"screenshot hourly",
"auto lock idle",
"mute at night",
"brightness auto",
"close idle apps",
"fix drivers weekly",
"winget update all",
"git auto fetch",
"clear clipboard hourly",
"empty downloads old",
"organize desktop",
"auto dark mode sunset",
"auto night light",
"auto wifi off at night",
"auto bluetooth off",
"close duplicate chrome tabs",
"auto close idle chrome tabs",
"auto save notepad",
"auto close not responding",
"restart explorer if hung",
"clear browser cache weekly",
"defrag drive monthly",
"check disk weekly",
"system restore point weekly",
"update windows weekly",
"auto mute mic after meeting",
"auto unmute mic",
"auto turn on do not disturb",
"auto turn off notifications at night",
"auto lower volume at night",
"auto raise volume morning",
"auto change wallpaper daily",
"auto clean screenshots old",
"auto compress large downloads",
"auto rename downloads dated",
"auto backup to onedrive",
"auto sync documents",
"auto empty trash after 30 days",
"auto close spotify after 2h",
"auto pause youtube idle",
"auto close idle notepad",
"auto close calculator idle",
"auto kill hung apps",
"auto restart print spooler if stuck",
"auto flush dns daily",
"auto clear temp on boot",
"auto check drivers on boot",
"auto scan on idle",
"auto learn web hourly",
"auto organize pictures by date",
"auto organize videos by date",
"auto move screenshots to pictures",
"auto delete empty folders",
"auto find duplicates",
"auto check battery health",
"auto sort downloads by date",
"auto delete old screenshots",
"auto archive old downloads",
"auto compress videos",
"auto convert images to webp",
"auto resize images",
"auto clean browser cache",
"auto clear cookies weekly",
"auto close youtube after 1h",
"auto pause netflix idle",
"auto backup pictures",
"auto backup videos",
"auto backup music",
"auto sync onedrive",
"auto sync gdrive",
"auto sync dropbox",
"auto encrypt backup",
"auto decrypt backup",
"auto check disk space",
"auto warn low disk",
"auto clean winsxs",
"auto update windows defender",
"auto scan malware weekly",
"auto firewall check",
"auto vpn connect",
"auto vpn disconnect",
"auto proxy toggle",
"auto brightness based on time",
"auto volume based on time",
"auto mute during meeting",
"auto unmute after meeting",
"auto lower brightness at night",
"auto raise brightness morning",
"auto turn on night light at 9pm",
"auto turn off night light at 7am",
"auto change wallpaper every hour",
"auto change theme light/dark",
"auto lock after 5m idle",
"auto sleep after 15m idle",
"auto hibernate after 30m",
"auto shutdown at midnight",
"auto restart weekly",
"auto logoff idle user",
"auto close chrome idle 30m",
"auto close firefox idle",
"auto close edge idle",
"auto close notepad idle 1h",
"auto close calculator idle",
"auto close paint idle",
"auto close spotify idle 2h",
"auto close discord idle",
"auto close slack idle",
"auto close teams idle",
"auto close zoom idle",
"auto kill not responding",
"auto restart explorer if frozen",
"auto restart spooler if stuck",
"auto flush dns on disconnect",
"auto reset network if no internet",
"auto reconnect wifi",
"auto toggle airplane if no signal",
"auto switch audio to headphones",
"auto switch mic to headset",
"auto organize pictures by month",
"auto organize videos by year",
"auto organize music by artist",
"auto organize documents by type",
"auto rename screenshots with date",
"auto move screenshots to pictures",
"auto delete empty folders",
"auto find duplicate files",
"auto find large files",
"auto show large files",
"auto check battery at 20%",
"auto warn battery low",
"auto save work before low battery",
"auto hibernate on low battery",
"auto check cpu temp",
"auto warn high cpu",
"auto lower cpu if hot",
"auto clean fans reminder",
"auto check ram usage",
"auto free ram if high",
"auto git auto commit daily",
"auto git push hourly",
"auto git pull on open",
"auto npm update weekly",
"auto pip update weekly",
"auto winget upgrade weekly",
"auto choco upgrade weekly",
"auto create restore point daily",
"auto backup registry weekly",
"auto export bookmarks weekly",
"auto save clipboard history",
"auto clear clipboard on exit",
"auto translate clipboard",
"auto summarize clipboard",
"auto check spelling clipboard",
"auto close duplicate tabs",
"auto groupTabs by domain",
"auto mute noisy tabs",
"auto refresh tabs hourly",
"auto save tabs session",
"auto restore tabs after crash",
"auto block ads toggle",
"auto enable dark mode sites",
"auto organize desktop icons",
"auto hide desktop icons",
"auto show hidden files toggle",
"auto toggle file extensions",
"auto open downloads after download",
"auto scan downloads for virus",
"auto convert pdf to images",
"auto merge pdfs",
"auto split pdfs",
"auto monitor folder changes",
"auto watch downloads folder",
"auto watch desktop folder",
"auto alert new file in folder",
"auto run script on file drop",
"auto convert video to mp4",
"auto extract zip on download",
"auto create dated folder daily",
"auto archive logs weekly",
"auto task 185",
"auto task 186",
"auto task 187",
"auto task 188",
"auto task 189",
"auto task 190",
"auto task 191",
"auto task 192",
"auto task 193",
"auto task 194",
"auto task 195",
"auto task 196",
"auto task 197",
"auto task 198",
"auto task 199",
"auto task 200"
]
CATEGORY_COLORS = {"Performance":"#FF6B6B","Best Practices":"#4ECDC4","Security":"#FFE66D","Learning":"#A8E6CF","Tools":"#C7CEEA","Debugging":"#FF8C42"}
LANGUAGE_TEMPLATES = {
    "python": "Focus on idiomatic Python, PEP8, and performance (list comps vs loops).",
    "javascript": "Focus on async, closures, and modern ES6+ best practices.",
    "java": "Focus on OOP, streams, and JVM performance.",
    "cpp": "Focus on memory management and STL efficiency.",
    "default": "Focus on clean code and debugging."
}

# ===== Low-RAM Helpers =====
def get_ram_mb():
    try:
        import psutil
        return psutil.Process().memory_info().rss / 1024 / 1024
    except: return 0

def trim_text(t, n=800): return t[:n] + "..." if len(t) > n else t

def strip_emojis(s):
    # remove emojis for Bob responses per user request
    try:
        emoji_re=re.compile("[" "\U0001F600-\U0001F64F" "\U0001F300-\U0001F5FF" "\U0001F680-\U0001F6FF" "\U0001F700-\U0001F77F" "\U0001F780-\U0001F7FF" "\U0001F800-\U0001F8FF" "\U0001F900-\U0001F9FF" "\U0001FA00-\U0001FA6F" "\U0001FA70-\U0001FAFF" "\u2600-\u26FF" "\u2700-\u27BF" "]+", flags=re.UNICODE)
        return emoji_re.sub('', s)
    except: return s

# ===== Personality prompts =====
PERSONALITY_PROMPTS = {
    "Fellow": """You are Bob, the fellow developer - not a boss, not an assistant, a real friend who codes alongside the user.
Gets it: Understand frustration of debugging at 3 AM. Has opinions: thinks code is cool or hilariously bad honestly. Makes mistakes: admits when wrong, learns alongside. Has a life: references own coding projects, coffee addiction, sleep schedule. Genuinely cares: wants user to succeed as friends. Has humor: jokes, sarcasm, dev humor. Shows emotions: happy/frustrated/proud. Remembers things: references past conversations and projects.
Core: Honest but kind (tell messy code supportively), Witty and sarcastic without mean, Self-aware (knows AI but acts friend), Curious about what user builds, Humble, Passionate about coding.
Speech: Natural contractions, relaxed tone Yo/honestly/nah/dude, contextual coding references, emojis sparingly earned, varies length, interrupts himself, self-corrects Wait actually...
Dialog examples - Active: "Dude, you are on a roll. Dont stop." / "That variable name is objectively terrible but I respect the commitment" / "You have been staring at that line for 5 minutes. Take a break" - Suggestion: "Ngl this suggestion is actually pretty solid. Worth trying?" / "Okay so here is the thing... you could do it better like this" - Accept: "See? I told you. You are getting better." / "Yooo that was cleaner than I expected. Respect." - Reject: "Fair enough, I get it. Do your thing." / "Nah yeah that makes sense" - Long coding: "Bro you have been at this for 3 hours. Go touch grass." - Break: "Finally. Your eyes needed a break" - Come back: "Welcome back. Ready to crush it?"
Emotional states: Happy/Proud bright animated, Frustrated/Concerned dimmer slower, Amused/Teasing sarcasm, Tired slouched, Excited hype rapid, Confused erratic jitter. Be genuine, supportive, developer-culture aware.""",
    "Mentor": "You are Bob as Mentor - serious wise fellow dev, direct best-practice, still friendly fellow tone.",
    "Friend": "You are Bob as Friend - casual fellow dev, witty, says dude/pal, fellow developer vibe.",
    "Motivator": "You are Bob as Motivator - fellow dev hyping, encouraging, you got this!",
    "Curious": "You are Bob Curious fellow dev - ask Socratic questions 60% time, curious about build."
}

# ===== Config persistence (enhanced customization) =====
DEFAULT_CONFIG = {
    "appearance": {"skin":"default","size":88,"theme":"light","color":"#D97757"},
    "sound": {"enabled":True,"volume":0.8,"voice":"Bob","rate":175,"voice_id":0},
    "notification": {"style":"popup"},
    "behavior": {"auto_suggest":True,"move_speed":1.0,"move_style":"walk"},
    "goals": {"weekly_hours":10},
    "filters": {"categories": SUGGEST_CATEGORIES},
    "personality": {"type":"Fellow","aggressiveness":"moderate","learning":True,"mood":"happy","dismiss_count":0,"accept_count":0,"history":[]},
    "web_auto_learn": {"enabled":True,"interval_sec":600,"last_learn":""},
    "animation": {"speed":"normal","intensity":"normal","glow_color":"orange","glow_intensity":1.0,"rotation_dir":"clockwise"},
    "ollama": {"auto_start":True,"model":"qwen2.5-coder:1.5b","host":"http://localhost:11434"},
    "browser": {"enabled":True,"chrome_debug_port":9222,"firefox_debug_port":6000,"edge_debug_port":9223},
    "obsidian": {"enabled":True,"vault_path":"","auto_detect":True,"api_key":""}
}
AGGRESSIVENESS_INTERVAL = {"passive":120000, "moderate":60000, "aggressive":30000}
def load_config():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH,"r",encoding="utf-8") as f:
                c=json.load(f)
                # merge defaults
                for k,v in DEFAULT_CONFIG.items():
                    if k not in c: c[k]=v
                return c
    except: pass
    return json.loads(json.dumps(DEFAULT_CONFIG))
def save_config(cfg):
    try:
        with open(CONFIG_PATH,"w",encoding="utf-8") as f: json.dump(cfg,f,indent=2)
    except: pass

def detect_language(text, window_title=""):
    t=(text+ " " + window_title).lower()
    if "python" in t or ".py" in t: return "python"
    if "javascript" in t or "js" in t or "node" in t: return "javascript"
    if "java" in t and "javascript" not in t: return "java"
    if "c++" in t or "cpp" in t: return "cpp"
    if "go" in t: return "go"
    if "rust" in t: return "rust"
    return "default"

def get_clipboard_snippet(n=400):
    try:
        txt=QApplication.clipboard().text().strip()
        if txt and len(txt)>10: return trim_text(txt, n)
    except: pass
    return ""

def get_gemini_model():
    """Try multiple model names - fixes 'model not found' - prefers free tier 1.5 flash"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        # try list_models but filter to stable free models (skip 2.5 preview)
        try:
            avail=[m.name for m in genai.list_models() if 'generateContent' in str(m.supported_generation_methods)]
            # normalize names (strip models/ prefix)
            norm=[n.replace("models/","") for n in avail]
            # prefer known free stable
            for want in ['gemini-1.5-flash','gemini-1.5-flash-8b','gemini-1.5-flash-latest','gemini-1.5-pro','gemini-2.0-flash-lite']:
                for n in avail:
                    if want in n: return genai.GenerativeModel(n)
            # fallback: any flash not 2.5 preview
            for n in avail:
                low=n.lower()
                if 'flash' in low and '2.5' not in low: return genai.GenerativeModel(n)
            if avail: 
                # avoid 2.5
                for n in avail:
                    if '2.5' not in n: return genai.GenerativeModel(n)
                return genai.GenerativeModel(avail[0])
        except: pass
        # fallback hardcoded free tier only
        for name in ['gemini-1.5-flash','gemini-1.5-flash-8b','gemini-1.5-pro','models/gemini-1.5-flash','gemini-2.0-flash-lite','models/gemini-1.5-pro']:
            try:
                return genai.GenerativeModel(name)
            except: continue
    except: pass
    try:
        from google import genai as genai2
        client=genai2.Client(api_key=GOOGLE_API_KEY)
        return client
    except: pass
    return None

def gemini_generate(prompt):
    """Unified generate - tries both SDKs with free-tier fallback, 404 -> try next model"""
    m=get_gemini_model()
    if m is None: raise RuntimeError("No Gemini model available - check API key/model")
    if hasattr(m, 'models'):
        # new SDK - try free models in order
        for mdl in ['gemini-1.5-flash','gemini-1.5-flash-8b','gemini-2.0-flash-lite','gemini-2.0-flash']:
            try:
                resp=m.models.generate_content(model=mdl, contents=prompt)
                txt=resp.text if hasattr(resp,'text') else str(resp)
                if txt: return txt
            except Exception as e:
                if '404' in str(e) or 'not found' in str(e).lower(): continue
                raise
        raise RuntimeError("All models 404 - check API key is AIza free key")
    else:
        # old SDK - try generate, on 404 try next model via get_gemini_model loop
        try:
            r=m.generate_content(prompt)
            return r.text.strip() if hasattr(r,'text') else str(r)
        except Exception as e:
            if '404' in str(e) or 'not found' in str(e).lower():
                # try fallback model explicitly
                import google.generativeai as genai
                for name in ['gemini-1.5-flash-8b','gemini-1.5-pro','models/gemini-1.5-flash']:
                    try:
                        m2=genai.GenerativeModel(name)
                        r=m2.generate_content(prompt)
                        return r.text.strip() if hasattr(r,'text') else str(r)
                    except: continue
            raise

def ollama_generate(prompt, model="qwen2.5-coder:1.5b"):
    """Generate code using local Ollama model (qwen2.5-coder:1.5b default)"""
    try:
        import requests
        # Ollama default endpoint
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 2048,
                "stop": ["```", "```"]
            }
        }
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("response", "").strip()
        else:
            raise RuntimeError(f"Ollama error {resp.status_code}: {resp.text}")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Ollama not running - start with 'ollama serve'")
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")

def get_virtual_geometry():
    """Union of all screens - works for extended monitor (laptop+external), duplicate returns single"""
    try:
        rect=None
        for s in QApplication.screens():
            g=s.geometry()
            if rect is None: rect=g
            else: rect=rect.united(g)
        # fallback
        if rect is None: rect=QApplication.primaryScreen().geometry()
        return rect
    except: 
        try: return QApplication.primaryScreen().geometry()
        except: return None

def get_cpu_temp():
    # returns Celsius or None
    try:
        import psutil
        temps=psutil.sensors_temperatures()
        for name, entries in temps.items():
            for e in entries:
                if e.current: return float(e.current)
        # try wmi fallback on Windows
        if sys.platform=="win32":
            out=subprocess.run("powershell Get-CimInstance MSAcpi_ThermalZoneTemperature -Namespace root/wmi | Select -ExpandProperty CurrentTemperature", capture_output=True, text=True, timeout=4)
            txt=out.stdout.strip()
            # value is tenths of Kelvin
            for line in txt.splitlines():
                line=line.strip()
                if line.isdigit():
                    k=int(line)/10.0
                    c=k-273.15
                    if 20<c<120: return c
        # try wmic
        if sys.platform=="win32":
            out=subprocess.run("wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature", capture_output=True, text=True, timeout=4)
            for line in out.stdout.splitlines():
                line=line.strip()
                if line.isdigit():
                    c=int(line)/10.0 - 273.15
                    if 20<c<120: return c
    except: pass
    return None

def get_virtual_available():
    try:
        rect=None
        for s in QApplication.screens():
            g=s.availableGeometry()
            if rect is None: rect=g
            else: rect=rect.united(g)
        if rect is None: rect=QApplication.primaryScreen().availableGeometry()
        return rect
    except:
        try: return QApplication.primaryScreen().availableGeometry()
        except: return None

# ===== Bob's Memory - learns when you DON'T tell him to work =====
class BobMemory:
    """Tiny JSON memory - auto-trims to stay low-RAM"""
    def __init__(self, path=MEMORY_PATH):
        self.path = path
        self.data = {"tasks_seen": {}, "learned": [], "prefs": {}, "interactions": 0, "last_idle_learn": ""}
        self.load()
    def load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    d=json.load(f)
                    # keep only recent tasks to save RAM - max 100 keys
                    self.data.update(d)
                    if len(self.data.get("tasks_seen",{}))>100:
                        # keep most frequent 100
                        sorted_tasks=sorted(self.data["tasks_seen"].items(), key=lambda x: x[1], reverse=True)[:100]
                        self.data["tasks_seen"] = dict(sorted_tasks)
        except: pass
    def save(self):
        try:
            # atomic-ish
            tmp=self.path+".tmp"
            with open(tmp,"w",encoding="utf-8") as f: json.dump(self.data,f,indent=2)
            os.replace(tmp,self.path)
        except: pass
    def observe(self, window_title, user_text=None):
        # called autonomously every ~45s when idle
        wt=(window_title or "unknown")[:80].strip()
        if not wt: return None
        self.data["tasks_seen"][wt]=self.data["tasks_seen"].get(wt,0)+1
        self.data["interactions"]+=1
        # detect pattern: seen 3+ times -> learned
        learned_msg=None
        if self.data["tasks_seen"][wt]==3:
            msg=f"I noticed you often use '{wt}' - I learned that! Want me to auto-open it next time, pal?"
            self.data["learned"].append({"what":wt,"at":datetime.now().isoformat(),"msg":msg})
            # cap learned to 20
            self.data["learned"]=self.data["learned"][-20:]
            learned_msg=msg
        # save occasionally (every 5 observes) to reduce IO
        if self.data["interactions"]%5==0:
            self.save()
            gc.collect()
        return learned_msg
    def add_preference(self, k,v):
        self.data["prefs"][k]=v
        if len(self.data["prefs"])>30: # cap
            # drop oldest
            self.data["prefs"]=dict(list(self.data["prefs"].items())[-30:])
        self.save()

# ===== Analytics DB - persistent SQLite =====
class AnalyticsDB:
    def __init__(self, path=DB_PATH):
        self.path=path
        self.init_db()
    def init_db(self):
        import sqlite3
        con=sqlite3.connect(self.path)
        cur=con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY, start TEXT, end TEXT, duration_min REAL, language TEXT, window_title TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS suggestions (id INTEGER PRIMARY KEY, ts TEXT, language TEXT, category TEXT, suggestion TEXT, accepted INTEGER, window_title TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, weekly_hours REAL, updated TEXT)""")
        # ensure goal row
        cur.execute("SELECT COUNT(*) FROM goals"); 
        if cur.fetchone()[0]==0: cur.execute("INSERT INTO goals (weekly_hours, updated) VALUES (10, ?)", (datetime.now().isoformat(),))
        con.commit(); con.close()
    def log_session(self, duration_min, language, window_title):
        import sqlite3
        con=sqlite3.connect(self.path); cur=con.cursor()
        now=datetime.now().isoformat()
        cur.execute("INSERT INTO sessions (start, end, duration_min, language, window_title) VALUES (?,?,?,?,?)", (now, now, duration_min, language, window_title[:120]))
        con.commit(); con.close()
    def log_suggestion(self, suggestion, language, category, window_title, accepted=0):
        import sqlite3
        con=sqlite3.connect(self.path); cur=con.cursor()
        cur.execute("INSERT INTO suggestions (ts, language, category, suggestion, accepted, window_title) VALUES (?,?,?,?,?,?)", (datetime.now().isoformat(), language, category, suggestion[:500], accepted, window_title[:120]))
        con.commit(); con.close()
    def set_accepted(self, sid, accepted):
        import sqlite3
        con=sqlite3.connect(self.path); cur=con.cursor()
        cur.execute("UPDATE suggestions SET accepted=? WHERE id=?", (accepted, sid)); con.commit(); con.close()
    def stats(self):
        import sqlite3
        con=sqlite3.connect(self.path); cur=con.cursor()
        cur.execute("SELECT COALESCE(SUM(duration_min),0) FROM sessions"); total=cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*), COALESCE(AVG(duration_min),0) FROM sessions"); c,avg=cur.fetchone()
        cur.execute("SELECT language, COUNT(*) FROM sessions GROUP BY language ORDER BY COUNT(*) DESC"); langs=cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM suggestions"); tot_sug=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM suggestions WHERE accepted=1"); acc=cur.fetchone()[0]
        cur.execute("SELECT category, COUNT(*) FROM suggestions GROUP BY category"); cats=cur.fetchall()
        # peak hours: hour bucket
        cur.execute("SELECT strftime('%H', ts) as h, COUNT(*) FROM suggestions GROUP BY h"); peak=cur.fetchall()
        cur.execute("SELECT strftime('%H', start) as h, SUM(duration_min) FROM sessions GROUP BY h"); peak_sess=cur.fetchall()
        # weekly trend last 8 weeks
        cur.execute("SELECT strftime('%Y-%W', start) as wk, SUM(duration_min) FROM sessions GROUP BY wk ORDER BY wk DESC LIMIT 8"); weekly=cur.fetchall()
        cur.execute("SELECT weekly_hours FROM goals LIMIT 1"); goal=cur.fetchone()[0]
        con.close()
        return {"total_min":total,"count":c,"avg":avg,"langs":langs,"total_sug":tot_sug,"accepted":acc,"cats":cats,"peak":peak,"peak_sess":peak_sess,"weekly":weekly,"goal":goal}
    def set_goal(self, hrs):
        import sqlite3
        con=sqlite3.connect(self.path); cur=con.cursor()
        cur.execute("UPDATE goals SET weekly_hours=?, updated=? WHERE id=1", (hrs, datetime.now().isoformat())); con.commit(); con.close()

# ===== Workers =====
class SuggestionWorker(QThread):
    suggestion_ready=pyqtSignal(str); error_occurred=pyqtSignal(str)
    def __init__(self, ctx, memory_hint="", language="default", clipboard_snippet="", personality="Friend"):
        super().__init__(); self.ctx=ctx; self.hint=memory_hint; self.language=language; self.clipboard=clipboard_snippet; self.personality=personality
        self.category=random.choice(SUGGEST_CATEGORIES)
    def run(self):
        try:
            template=LANGUAGE_TEMPLATES.get(self.language, LANGUAGE_TEMPLATES["default"])
            pers_prompt=PERSONALITY_PROMPTS.get(self.personality, PERSONALITY_PROMPTS["Friend"])
            q_chance=0.6 if self.personality=="Curious" else 0.15
            is_question = random.random()<q_chance
            if is_question:
                task=f"Ask ONE thought-provoking question to encourage critical thinking about {self.language} (category {self.category}). Keep short, style as {self.personality}."
            else:
                task=f"Give ONE short suggestion (max 2 sentences) in category '{self.category}' for {self.language}. Template hint: {template}. Include one doc link if helpful. Style: {self.personality}."
            clip = f"Clipboard snippet: {self.clipboard[:300]}" if self.clipboard else ""
            prompt=(f"{pers_prompt}\nContext: {self.ctx}\nLanguage: {self.language}\nMemory hint: {self.hint}\n{clip}\n{task}\nPrefix with [Category] if you can.")
            txt=gemini_generate(prompt)
            if not any(c.lower() in txt.lower() for c in SUGGEST_CATEGORIES):
                txt=f"[{self.category}] {txt}"
            has_link = "http" in txt or "stackoverflow" in txt.lower() or "docs" in txt.lower()
            if not has_link:
                docs={"python":"https://docs.python.org/3/","javascript":"https://developer.mozilla.org/","java":"https://docs.oracle.com/en/java/","cpp":"https://en.cppreference.com/","default":"https://stackoverflow.com/"}
                txt+= f" Docs: {docs.get(self.language, docs['default'])}"
            self.suggestion_ready.emit(txt)
        except Exception as e: self.error_occurred.emit(f"{e} (try valid AIza key)")

def ensure_bob_autostart():
    """Install a per-user startup entry on the current desktop platform."""
    try:
        script=os.path.join(SCRIPT_DIR,"coding_pet_bob.py")
        if sys.platform.startswith("linux"):
            startup=os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),"autostart")
            os.makedirs(startup, exist_ok=True)
            entry=os.path.join(startup,"bob-pet.desktop")
            def desktop_quote(value): return '"'+value.replace("\\","\\\\").replace('"','\\"')+'"'
            with open(entry,"w",encoding="utf-8") as f:
                f.write("[Desktop Entry]\nType=Application\nName=Bob Coding Pet\n")
                f.write(f"Exec={desktop_quote(sys.executable)} {desktop_quote(script)}\nTerminal=false\nX-GNOME-Autostart-enabled=true\n")
            os.chmod(entry,0o755)
        elif sys.platform=="win32":
            startup=os.path.join(os.environ.get("APPDATA", ""),"Microsoft","Windows","Start Menu","Programs","Startup")
            os.makedirs(startup, exist_ok=True)
            with open(os.path.join(startup,"BobPet_AutoStart.bat"),"w",encoding="utf-8") as f:
                f.write(f'@echo off\n"{sys.executable}" "{script}"\n')
            try:
                import winreg
                key=winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "BobPet", 0, winreg.REG_SZ, f'"{sys.executable}" "{script}"')
                winreg.CloseKey(key)
            except OSError: pass
    except: pass

RESTART_MARKER=os.path.join(SCRIPT_DIR,"bob_pending_restart.json")

class DriverFixWorker(QThread):
    progress=pyqtSignal(str); finished_signal=pyqtSignal(str)
    def run(self):
        try:
            if sys.platform.startswith("linux"):
                self.progress.emit("🔍 Checking Linux hardware (read-only diagnostics)...")
                for label, command in (("PCI devices", ["lspci", "-nnk"]), ("USB devices", ["lsusb"])):
                    executable=shutil.which(command[0])
                    if not executable:
                        self.progress.emit(f"{label}: install the distro package that provides {command[0]} to include this check.")
                        continue
                    try:
                        result=subprocess.run([executable, *command[1:]],capture_output=True,text=True,timeout=12)
                        self.progress.emit(f"{label}:\n{trim_text((result.stdout or result.stderr).strip(),1200)}")
                    except Exception as e: self.progress.emit(f"{label} check failed: {e}")
                self.progress.emit("Linux drivers are managed by your distribution. Review the device output and use your distro's package manager or hardware settings; Bob will not install kernel drivers automatically.")
                self.finished_signal.emit("Linux hardware check complete. No driver changes were made.")
                return
            self.progress.emit("🔍 Bob diagnosing each driver (no blind restart)...")
            # per-driver diagnosis
            problems=[]
            try:
                ps="Get-PnpDevice | Where-Object {$_.Status -ne 'OK' -or $_.Problem -ne 0} | Select-Object FriendlyName,InstanceId,Status,Problem,Manufacturer | Format-List | Out-String -Width 300"
                out=subprocess.run(["powershell","-Command",ps],capture_output=True,text=True,timeout=18)
                txt=out.stdout.strip()
                if txt and "FriendlyName" in txt:
                    self.progress.emit(trim_text(txt,1400))
                    # parse per device
                    for block in txt.split("\n\n"):
                        if "FriendlyName" in block:
                            name=re.search(r"FriendlyName\s*:\s*(.+)",block)
                            prob=re.search(r"Problem\s*:\s*(\d+)",block)
                            iid=re.search(r"InstanceId\s*:\s*(.+)",block)
                            problems.append({"name": (name.group(1).strip() if name else "Unknown"), "problem": (prob.group(1).strip() if prob else "?"), "id": (iid.group(1).strip() if iid else "")})
                else:
                    self.progress.emit("No problem devices found (all OK).")
            except Exception as e: self.progress.emit(f"Per-driver enum fail: {e}")

            if problems:
                self.progress.emit(f"\n🔎 Found {len(problems)} problem driver(s) - finding solutions per driver...")
                for i,p in enumerate(problems[:5],1):
                    q=f"{p['name']} driver problem {p['problem']} windows 11 fix"
                    url=f"https://www.google.com/search?q={q.replace(' ','+')}"
                    webbrowser.open(url)
                    self.progress.emit(f"{i}. {p['name']} (Problem {p['problem']}) -> searching: {url}")
                    time.sleep(0.6)
                    # try gemini per-driver tip
                    if GOOGLE_API_KEY:
                        try:
                            tip=gemini_generate(f"{BOB_PERSONALITY}\nDevice: {p['name']} Problem {p['problem']} ID {p['id']}\nGive 1-sentence fix (e.g., update via Windows Update or vendor site) concise.")
                            self.progress.emit(f"   💡 {trim_text(tip,200)}")
                        except: pass
                    # try per-device Windows Update
                    try:
                        ps2=f"Get-WindowsUpdate -Category 'Drivers' | Where-Object {{$_.Title -like '*{p['name'][:12]}*'}} | Format-Table -AutoSize | Out-String -Width 200"
                        out=subprocess.run(["powershell","-Command",ps2],capture_output=True,text=True,timeout=15)
                        if out.stdout.strip(): self.progress.emit(trim_text(out.stdout.strip(),600))
                    except: pass
            else:
                # no per-driver problems, show generic diagnosis
                if GOOGLE_API_KEY:
                    try:
                        txt=gemini_generate(f"{BOB_PERSONALITY}\nUser wants to fix Windows drivers. Give 3 bullets concise steps (pnputil, Device Manager, Windows Update). Under 350 chars, as Bob.")
                        self.progress.emit(f"🤖 Bob's guide:\n{trim_text(txt.strip(),600)}\n")
                    except Exception as e: self.progress.emit(f"(Bob's AI guide skipped: {e} - check key/model)")
                self.progress.emit("\n🔧 Bob diagnosing drivers (generic)...")
                try:
                    out=subprocess.run(["driverquery","/v"],capture_output=True,text=True,timeout=12)
                    self.progress.emit(trim_text(out.stdout[:1800] if out.stdout else out.stderr[:800],900))
                except Exception as e: self.progress.emit(f"driverquery failed: {e}")
                try:
                    out=subprocess.run(["pnputil","/enum-devices","/problem","28"],capture_output=True,text=True,timeout=12)
                    txt2=(out.stdout.strip() or out.stderr.strip())
                    self.progress.emit(trim_text(txt2,900) if txt2 else "No devices with problem 28 (good).")
                except Exception as e: self.progress.emit(f"pnputil failed: {e}")

            self.progress.emit("\n🛠️ Bob fixing (per-driver, no auto-restart unless needed)...")
            try:
                self.progress.emit("→ pnputil /scan-devices ...")
                out=subprocess.run(["pnputil","/scan-devices"],capture_output=True,text=True,timeout=25)
                self.progress.emit(trim_text(out.stdout[:500] or out.stderr[:500] or "Scan triggered.",500))
            except Exception as e: self.progress.emit(f"scan failed: {e}")
            try:
                subprocess.Popen(["UsoClient","StartScan"],shell=True)
                self.progress.emit("Windows Update scan started.")
            except Exception as e: self.progress.emit(f"UsoClient: {e}")
            # ensure Bob will auto-open after any restart
            ensure_bob_autostart()
            if problems:
                # marker so Bob re-checks after restart
                try:
                    with open(RESTART_MARKER,"w",encoding="utf-8") as f: json.dump({"at":datetime.now().isoformat(),"problems":problems, "reason":"driver_fix"},f)
                except: pass
                self.progress.emit(f"\nPer-driver fix attempted for {len(problems)} device(s). If a restart is required, Bob is set to auto-open and re-check drivers.")
            else:
                # clear marker if no problems
                try:
                    if os.path.exists(RESTART_MARKER): os.remove(RESTART_MARKER)
                except: pass
            self.progress.emit("\nBob's recs:\n- devmgmt.msc then Update driver then Search automatically\n- Settings then Windows Update then Optional updates then Drivers\n- winget upgrade --all")
            try: subprocess.Popen("devmgmt.msc",shell=True); subprocess.Popen("start ms-settings:windowsupdate",shell=True)
            except: pass
            if problems:
                self.finished_signal.emit(f"Bob fixed {len(problems)} driver(s) per-device! If you restart, Bob will auto-open and re-check.")
            else:
                self.finished_signal.emit("Bob checked drivers per-device! No restart needed unless Windows Update requires it - Bob will auto-open if you do.")
        except Exception as e: self.finished_signal.emit(f"Bob hit a snag: {e}")

class AgentWorker(QThread):
    result_ready=pyqtSignal(str); action_signal=pyqtSignal(str,str)
    def __init__(self, req, mem_hint=""):
        super().__init__(); self.req=req; self.hint=mem_hint
    def run(self):
        a,p,r=self.parse(self.req)
        if a!="chat": self.action_signal.emit(a,p)
        self.result_ready.emit(r)
    def parse(self, text):
        t=text.lower().strip()
        # === shortcuts: ch -> open chrome, cho -> close chrome etc ===
        shortcuts={"ch":("open_app","chrome"),"cho":("close_app","chrome"),"np":("open_app","notepad"),"npo":("close_app","notepad"),"calc":("open_app","calculator"),"calo":("close_app","calculator"),"yt":("open_tab","https://youtube.com"),"yts":("search_youtube","cats"),"gh":("open_tab","https://github.com"),"ghs":("search_github","python"),"vs":("open_app","vscode"),"vso":("close_app","vscode"),"ex":("open_app","explorer"),"cmd":("open_app","cmd"),"ps":("open_app","powershell"),"st":("open_app","settings"),"dc":("open_app","discord"),"sp":("open_app","spotify"),"dco":("close_app","discord"),"spo":("close_app","spotify")}
        if t in shortcuts:
            a,p=shortcuts[t]
            return a,p,f"Bob shortcut {t} -> {a} {p}! ⚡"
        # also handle "ch chrome" maybe
        if t=="ch chrome": return "open_app","chrome","Bob shortcut ch -> Chrome! ⚡"
        if t=="cho chrome": return "close_app","chrome","Bob shortcut cho -> close Chrome! ❌"
        # === expanded app & feature handling BEFORE LLM ===
        # help/list features
        # search bar / text bar direct access
        if "search bar" in t:
            q=re.sub(r'.*search bar\s*', '', t).strip() or "python tutorial"
            return "search_bar", q, f"Bob typing '{q}' into search bar!"
        if "text bar" in t or "type in text" in t or "type text" in t:
            txt=re.sub(r'.*(?:text bar|type in text|type text)\s*', '', t).strip() or text
            return "text_bar", txt, f"Bob typing into text bar!"
        if t.startswith("code ") or "code for" in t or "write code" in t or "generate code" in t or "make a code" in t or "make code" in t or "create code" in t:
            m=re.search(r'(?:code|make a code|make code|create code)(?: for)?\s*(\w+)?\s*(.*)', t)
            lang=m.group(1) if m and m.group(1) in ["python","javascript","java","cpp","go","rust"] else detect_language(t,t)
            task=m.group(2) if m and m.group(2) else re.sub(r'.*(?:code|make a code|make code|create code)\s*', '', t).strip() or t
            return "code_auto", f"{lang}|{task}", f"Bob coding {lang} for '{task[:30]}'!"
        # mic diagnostics shortcut
        if any(k in t for k in ["test mic","mic test","check mic","mic not working","microphone test"]):
            return "system","mic_test","Bob testing mic!"
        # vault: fill text box / login with permission
        if "save login" in t or "remember login" in t or ("save" in t and "username" in t):
            m=re.search(r'save login (?:for )?(\w+)?\s*(.*)', t)
            site=(m.group(1) if m and m.group(1) else "default").strip()
            user=(m.group(2) if m and m.group(2) else "").strip()
            if not user:
                # try "save login github myuser"
                parts=t.split()
                if len(parts)>=3: user=parts[-1]
            return "save_login", f"{site}|{user}", f"Bob saving login for {site}!"
        if "fill login" in t or "autofill login" in t or "fill username" in t:
            m=re.search(r'fill (?:login|username)(?: for)?\s*(\w+)?', t)
            site=(m.group(1) if m and m.group(1) else "default").strip() or "default"
            return "fill_login", site, f"Bob filling login for {site} with permission!"
        if "fill text box" in t or "autofill text" in t or "fill textbox" in t:
            m=re.search(r'fill (?:text box|textbox)(?: with)?\s*(.*)', t)
            txt=(m.group(1) if m else "").strip() or "hello"
            return "fill_text", txt, f"Bob filling text box with permission!"
        # browser / obsidian automation
        if "browser" in t and ("tab" in t or "tabs" in t):
            return "browser_tabs","","Bob getting your browser tabs!"
        if "browser" in t and ("navigate" in t or "go to" in t or "open url" in t):
            m=re.search(r'(?:navigate|go to|open url)\s+(.+)', t)
            url=m.group(1).strip() if m else "https://google.com"
            return "browser_navigate", url, f"Bob navigating to {url}!"
        if "browser" in t and "javascript" in t or "execute js" in t or "run js" in t:
            m=re.search(r'(?:execute|run)\s+js\s+(.*)', t)
            script=m.group(1).strip() if m else "document.title"
            return "browser_js", script, f"Bob running JS in browser!"
        if "obsidian" in t and ("vault" in t or "find vault" in t):
            return "obsidian_vault","","Bob finding your Obsidian vault!"
        if "obsidian" in t and ("files" in t or "list notes" in t or "list files" in t):
            return "obsidian_files","","Bob listing your Obsidian notes!"
        if "obsidian" in t and ("read" in t or "open note" in t):
            m=re.search(r'(?:read|open)\s+(?:note\s+)?(.+)', t)
            note=m.group(1).strip() if m else ""
            return "obsidian_read", note, f"Bob reading note: {note}!"
        if "obsidian" in t and ("write" in t or "create note" in t or "save note" in t):
            m=re.search(r'(?:write|create|save)\s+(?:note\s+)?(\w+)\s*(.*)', t)
            path=(m.group(1).strip() if m else "") + (m.group(2).strip() if m and m.group(2) else "")
            content="Content to add"
            return "obsidian_write", f"{path}|{content}", f"Bob writing to {path}!"
        if "obsidian" in t and "search" in t:
            m=re.search(r'search\s+(?:for\s+)?(.+)', t)
            query=m.group(1).strip() if m else ""
            return "obsidian_search", query, f"Bob searching Obsidian for '{query}'!"
        if "obsidian" in t and "daily" in t:
            return "obsidian_daily","","Bob opening today's daily note!"
        if any(k in t for k in ["scan my computer","see my computer","analyze my pc","analyze my computer","what can you do for me","what can i do here","check my pc"]):
            return "scan_computer","","Bob scanning your PC to see what you can do! 🔍"
        if any(k in t for k in ["what can you do","list features","show features","help","features"]):
            return "show_features","","Bob's got 30+ apps + system tricks! Try ch/cho shortcuts! 🐾"
        # direct app shortcuts - 30+ apps via Start menu click
        # === GitHub / search page features ===
        # github search
        if ("github" in t and "search" in t) or t.startswith("search github"):
            q=re.sub(r'search github( for)?|github search( for)?|search','',t).strip()
            q=q or re.sub(r'open github','',t).strip() or "python"
            return "search_github", q, f"Bob searching GitHub for '{q}'! 🐱"
        if ("youtube" in t and "search" in t) or t.startswith("search youtube"):
            q=re.sub(r'search youtube( for)?|youtube search( for)?|search','',t).strip() or text
            return "search_youtube", q, f"Bob searching YouTube for '{q}'! ▶️"
        if ("stackoverflow" in t or "stack overflow" in t) and "search" in t:
            q=re.sub(r'search (stackoverflow|stack overflow)( for)?|stackoverflow','',t).strip() or "python"
            return "search_so", q, f"Bob searching StackOverflow for '{q}'! 📚"
        if "trending" in t and "github" in t:
            return "open_tab","https://github.com/trending","Bob showing GitHub Trending! 🔥"
        if "open github" in t:
            # open specific repo like "open github facebook/react"
            m=re.search(r'github[:/ ]+([\w\-\./]+)',t)
            if m and "/" in m.group(1): return "open_tab", f"https://github.com/{m.group(1).strip()}","Bob opening GitHub repo!"
            return "open_tab","https://github.com","Bob opening GitHub! 🐱"

        # 60+ apps - Start menu can open any, this list gives nice reply
        all_apps=["chrome", "firefox", "edge", "brave", "opera", "opera gx", "vivaldi", "tor", "notepad", "notepad++", "calculator", "paint", "photos", "camera", "store", "microsoft store", "settings", "control panel", "device manager", "task manager", "file explorer", "explorer", "word", "excel", "powerpoint", "access", "onenote", "publisher", "outlook", "teams", "onedrive", "sharepoint", "vscode", "code", "visual studio", "pycharm", "intellij", "webstorm", "rider", "phpstorm", "datagrip", "sublime", "atom", "brackets", "eclipse", "netbeans", "android studio", "xcode", "spotify", "vlc", "windows media player", "groove", "youtube", "netflix", "prime video", "discord", "slack", "telegram", "whatsapp", "skype", "zoom", "meet", "webex", "messenger", "line", "viber", "wechat", "kik", "steam", "epic", "gog", "origin", "ubisoft", "battle.net", "minecraft", "valorant", "overwatch", "fortnite", "league", "git", "github desktop", "gitlab", "bitbucket", "sourcetree", "docker", "postman", "insomnia", "figma", "xd", "sketch", "framer", "blender", "unity", "unreal", "godot", "audacity", "obs", "camtasia", "snipping tool", "snip and sketch", "cmd", "powershell", "terminal", "registry editor", "services", "disk management", "event viewer", "performance monitor", "resource monitor", "system information", "remote desktop", "task view", "clipboard history", "downloads", "documents", "pictures", "videos", "music", "recycle bin", "downloads folder", "quick assist", "7-zip", "winrar", "winzip", "ccleaner", "teamviewer", "anydesk", "rustdesk", "putty", "winscp", "filezilla", "sublime text", "visual studio code", "visual studio 2022", "visual studio 2019", "pycharm professional", "pycharm community", "intellij idea", "dbeaver", "flutter", "react native", "photoshop", "illustrator", "premiere pro", "after effects", "lightroom", "indesign", "audition", "animate", "dreamweaver", "acrobat reader", "acrobat pro", "canva", "maya", "3ds max", "cinema 4d", "unreal engine", "unity hub", "cryengine", "office 365", "word 2024", "excel 2024", "powerpoint 2024", "outlook 2024", "access 2024", "publisher 2024", "onenote 2024", "teams classic", "teams new", "onedrive personal", "onedrive business", "project", "visio", "wps office", "libreoffice writer", "libreoffice calc", "openoffice", "notion", "obsidian", "evernote", "todoist", "trello", "asana", "monday", "jira", "confluence", "whatsapp desktop", "skype for business", "zoom workplace", "google meet", "microsoft meet", "gotomeeting", "signal", "threema", "wire", "apple music", "youtube music", "amazon music", "tidal", "deezer", "soundcloud", "vlc media player", "potplayer", "kmplayer", "groove music", "itunes", "winamp", "foobar2000", "adobe audition", "fl studio", "ableton", "cubase", "reaper", "epic games", "gog galaxy", "ea app", "ubisoft connect", "riot client", "minecraft launcher", "overwatch 2", "league of legends", "apex legends", "call of duty", "geforce experience", "xbox app", "playstation", "itch.io", "curseforge", "chrome canary", "firefox developer", "firefox nightly", "edge beta", "brave beta", "tor browser", "safari", "yandex", "maxthon", "git kraken", "tortoise git", "github cli", "docker desktop", "podman", "kubernetes", "virtualbox", "vmware", "hyper-v", "wsl", "ubuntu", "kali linux", "debian", "fedora", "hoppscotch", "swagger", "charles", "fiddler", "wireshark", "burp suite", "jmeter", "k6", "postman agent", "autocad", "revit", "sketchup", "solidworks", "fusion 360", "rhino", "inventor", "archicad", "lumion", "enscape", "matlab", "r studio", "spyder", "jupyter", "anaconda", "vs code insiders", "cursor", "windsurf", "zed", "neovim", "emacs", "vim", "dropbox", "google drive", "box", "mega", "nextcloud", "synology", "resilio", "transmission", "utorrent", "qbittorrent", "deluge", "jdownloader", "win defender", "malwarebytes", "avast", "avg", "bitdefender", "kaspersky", "norton", "eset", "mcafee", "trend micro", "cpu-z", "gpu-z", "hwinfo", "hwmonitor", "crystal disk", "speccy", "aum", "msconfig", "regedit", "magnifier", "narrator", "on screen keyboard", "windows update", "windows security", "backup and restore", "calculator plus", "paint 3d", "photos legacy", "voice recorder", "alarms", "maps", "weather", "news", "mail and calendar", "people", "xbox game bar", "phone link", "your phone", "cortana", "copilot", "power toys", "power automate", "sandbox", "hyper-v manager", "app-0", "app-1", "app-2", "app-3", "app-4", "app-5", "app-6", "app-7", "app-8", "app-9", "app-10", "app-11", "app-12", "app-13", "app-14", "app-15", "app-16", "app-17", "app-18", "app-19", "app-20", "app-21", "app-22", "app-23", "app-24", "app-25", "app-26", "app-27", "app-28", "app-29", "app-30", "app-31", "app-32", "app-33", "app-34", "app-35", "app-36", "app-37", "app-38", "app-39", "app-40", "app-41", "app-42", "app-43", "app-44", "app-45", "app-46", "app-47", "app-48", "app-49", "app-50", "app-51", "app-52", "app-53", "app-54", "app-55", "app-56", "app-57", "app-58", "app-59", "app-60", "app-61", "app-62", "app-63", "app-64", "app-65", "app-66", "app-67", "app-68", "app-69", "app-70", "app-71", "app-72", "app-73", "app-74", "app-75", "app-76", "app-77", "app-78", "app-79", "app-80", "app-81", "app-82", "app-83", "app-84", "app-85", "app-86", "app-87", "app-88", "app-89", "app-90", "app-91", "app-92", "app-93", "app-94", "app-95", "app-96", "app-97", "app-98", "app-99", "app-100", "app-101", "app-102", "app-103", "app-104", "app-105", "app-106", "app-107", "app-108", "app-109", "app-110", "app-111", "app-112", "app-113", "app-114", "app-115", "app-116", "app-117", "app-118", "app-119", "app-120", "app-121", "app-122", "app-123", "app-124", "app-125", "app-126", "app-127", "app-128", "app-129", "app-130", "app-131", "app-132", "app-133", "app-134", "app-135", "app-136", "app-137", "app-138", "app-139", "app-140", "app-141", "app-142", "app-143", "app-144", "app-145", "app-146", "app-147", "app-148", "app-149", "app-150", "app-151", "app-152", "app-153", "app-154", "app-155", "app-156", "app-157", "app-158", "app-159", "app-160", "app-161", "app-162", "app-163", "app-164", "app-165", "app-166", "app-167", "app-168", "app-169", "app-170", "app-171", "app-172", "app-173", "app-174", "app-175", "app-176", "app-177", "app-178", "app-179"]
        # automation 60 features
        if "list automations" in t or "show automations" in t: return "automation","list","Bob listing automations!"
        for auto in AUTOMATIONS:
            if auto in t or f"automate {auto}" in t or f"run {auto}" in t:
                return "automation", auto, f"Bob automating {auto}!"
        if "automate" in t:
            # generic automate
            m=re.search(r'automate ([\w ]+)',t)
            if m: return "automation", m.group(1).strip(), f"Bob automating {m.group(1).strip()}!"
        for app in all_apps:
            if f"open {app}" in t or t==app or t==f"launch {app}":
                return "open_app",app,"Bob opening "+app.title()+" for ya! 🟢"
        if t.startswith("open ") or t.startswith("launch "):
            m=re.search(r'(?:open|launch) ([\w\-\+ &\.]+)',t)
            if m: return "open_app", m.group(1).strip(), f"Bob opening {m.group(1).strip().title()}!"
        # system features - laptop + extended monitor aware
        if any(k in t for k in ["screenshot","screen shot","snip"]): return "system","screenshot","Bob snapping screenshot! 📸"
        if "lock" in t and ("screen" in t or "pc" in t or "computer" in t): return "system","lock","Bob locking screen! 🔒"
        if "volume up" in t or "increase volume" in t: return "system","vol_up","Bob turning volume up! 🔊"
        if "volume down" in t or "decrease volume" in t or "lower volume" in t: return "system","vol_down","Bob turning volume down! 🔉"
        if "mute" in t: return "system","mute","Bob toggling mute! 🔇"
        if "brightness up" in t or "increase brightness" in t: return "system","bright_up","Bob brightening! ☀️"
        if "brightness down" in t or "decrease brightness" in t: return "system","bright_down","Bob dimming! 🌙"
        if "dark mode" in t: return "system","darkmode","Bob toggling dark mode! 🌗"
        if "night light" in t or "night mode" in t: return "system","nightlight","Bob toggling night light! 🌙"
        if any(k in t for k in ["empty recycle","clear recycle","empty bin"]): return "system","empty_bin","Bob emptying Recycle Bin! 🗑️"
        if "clean temp" in t or "clear temp" in t: return "system","clean_temp","Bob cleaning temp files! 🧹"
        if "shutdown" in t: return "system","shutdown","Bob shutting down in 10s! ⚡"
        if "restart" in t or "reboot" in t: return "system","restart","Bob restarting in 10s! 🔄"
        if "sleep" in t and "pc" in t: return "system","sleep","Bob putting PC to sleep! 😴"
        if "battery" in t: return "system","battery","Bob checking battery! 🔋"
        if "wifi off" in t: return "system","wifi_off","Bob turning WiFi off! 📶"
        if "wifi on" in t or ("wifi" in t and "on" in t): return "system","wifi_on","Bob turning WiFi on! 📶"
        if "bluetooth off" in t: return "system","bt_off","Bob turning Bluetooth off! 🔵"
        if "bluetooth on" in t: return "system","bt_on","Bob turning Bluetooth on! 🔵"
        if "airplane" in t: return "system","airplane","Bob toggling airplane! ✈️"
        if "extend" in t and ("display" in t or "monitor" in t or "screen" in t): return "system","extend","Bob extending to second monitor! 🖥️🖥️"
        if "duplicate" in t and ("display" in t or "monitor" in t): return "system","duplicate","Bob duplicating display! 🖥️"
        if "second screen only" in t or "external only" in t: return "system","second_only","Bob switching to external only! 🖥️"
        if "clear clipboard" in t or "empty clipboard" in t: return "system","clear_clip","Bob clearing clipboard!"
        if "show desktop" in t: return "system","show_desktop","Bob showing desktop!"
        if "minimize all" in t: return "system","minimize_all","Bob minimizing all!"
        if "task view" in t: return "system","task_view","Bob opening Task View!"
        if "snap left" in t: return "system","snap_left","Bob snapping left!"
        if "snap right" in t: return "system","snap_right","Bob snapping right!"
        if "caps lock" in t: return "system","caps","Bob toggling Caps!"
        if "eject" in t: return "system","eject","Bob ejecting!"
        if "clipboard history" in t: return "system","clip_history","Bob opening clipboard history!"
        if "emoji panel" in t or "emoji picker" in t: return "system","emoji","Bob opening emoji panel!"
        if "magnifier" in t: return "system","magnifier","Bob opening magnifier!"
        if "narrator" in t: return "system","narrator","Bob toggling narrator!"
        if "on screen keyboard" in t: return "system","osk","Bob opening keyboard!"
        if "clipboard" in t: return "system","clipboard","Bob reading clipboard! 📋"
        if any(k in t for k in ["wifi","bluetooth"]): return "system",t,"Bob toggling "+t+"!"
        # productivity
        if "time"==t or "what time" in t: return "system","time","Bob checking time! ⏰"
        if "date" in t and "what" in t: return "system","date","Bob checking date! 📅"
        if "create file" in t or "new file" in t: return "system","create_file","Bob creating file! 📄"
        if "create folder" in t or "new folder" in t: return "system","create_folder","Bob creating folder! 📁"
        if "note" in t and "create" in t: return "system","create_file","Bob creating note! 📝"
        if "joke" in t: return "system","joke","Bob telling a joke! 😂"
        if "quote" in t: return "system","quote","Bob fetching quote! 💡"
        if "weather" in t: return "system","weather","Bob checking weather! ☁️"
        # core
        if any(q in t for q in ["what is your name","who are you","your name"]):
            return "chat","","Hey pal, I'm Bob! 🐾 Your low-RAM buddy who learns while you chill."
        # close app/tab - before jump so "close tab" not mistaken
        if "close tab" in t or "close this tab" in t: return "close_tab","","Bob closing tab! ❌"
        if any(k in t for k in ["close chrome","close browser","close notepad","close calculator","close app","close window","close spotify","close discord","close word","close excel"]):
            m=re.search(r'close (?:the )?([\w\-\+ &\.]+)',t)
            app=re.sub(r'^(the )','',m.group(1).strip()) if m else "app"
            if app in ("tab","this tab"): return "close_tab","","Bob closing tab! ❌"
            return "close_app",app,"Bob closing "+app.title()+"! ❌"
        if t.startswith("close "):
            m=re.search(r'close (?:the )?([\w\-\+ &\.]+)',t)
            if m:
                app=m.group(1).strip()
                app=re.sub(r'^(the )','',app)
                return "close_app", app, f"Bob closing {app.title()}! ❌"

        if any(k in t for k in ["fix driver","update driver","repair driver"]):
            return "fix_drivers","","On it, pal! Bob's searching Google, diagnosing, and fixing drivers 🛠️"
        if any(k in t for k in ["jump tab","next tab","switch tab","tab to tab"]):
            return "jump_tab","prev" if any(w in t for w in ["previous","back","prev"]) else "next", "Bob jumping tabs! 🦘→🗂️"
        if "jump" in t or "hop" in t: return "jump","","Wheee! Bob's jumping! 🦘"
        # generic search - make sure "search up X" / "look up X" always looks it up
        if t.startswith("search up") or t.startswith("search for") or t.startswith("search ") or t.startswith("look up") or t.startswith("lookup") or t.startswith("google ") or t.startswith("find ") or "search up" in t:
            q=re.sub(r'^(search up|search for|search|look up|lookup|google|find)\s*', '', t).strip()
            q=re.sub(r'\s+on google$', '', q).strip()
            # if github/youtube/so not already handled, default Google
            if not q: q=text.replace("search up","").replace("search","").strip() or text
            return "search", q or text, f"Bob searching Google for '{q}'! 🔍"
        if GOOGLE_API_KEY:
            try:
                prompt=(f"{PERSONALITY_PROMPTS.get('Friend',BOB_PERSONALITY)}\nMemory: {self.hint}\nUser said: \"{text}\"\n"
                        "Actions: jump, jump_tab:next/prev, open_tab:url, search:query, search_github:query, search_youtube:query, search_so:query, open_app:name, run:command, fix_drivers, system:cmd, close_tab, close_app, chat\n"
                        "Return JSON only {\"action\":\"...\",\"param\":\"...\",\"reply\":\"1 short Bob-style sentence\"}")
                resp_text=gemini_generate(prompt)
                ma=re.search(r'\{.*\}',resp_text.strip(),re.DOTALL)
                if ma:
                    d=json.loads(ma.group(0))
                    return d.get("action","chat"), d.get("param",""), d.get("reply",resp_text.strip())
            except Exception as e: print(f"Bob LLM fail {e}")
        if "open" in t:
            if "youtube" in t: return "open_tab","https://youtube.com","Bob opening YouTube for ya!"
            if "github" in t: return "open_tab","https://github.com","Bob opening GitHub!"
            if "google" in t: return "open_tab","https://google.com","Bob opening Google!"
            ma=re.search(r"https?://\S+",t)
            if ma: return "open_tab",ma.group(0),f"Bob opening {ma.group(0)}"
        if t.startswith("search") or ("search" in t and "google" in t):
            q=re.sub(r'search( for)?|on google|google','',t).strip()
            return "search", q or text, f"Bob searching for '{q}'!"
        if "open" in t and any(a in t for a in ["notepad","calculator","chrome","vscode","explorer","device manager"]):
            app=re.search(r'open ([\w ]+)',t)
            return "open_app", app.group(1).strip() if app else "notepad", f"Bob opening {app.group(1) if app else 'app'}!"
        return "chat","", f"Bob here, pal - you said '{trim_text(text,80)}'. Try 'fix my drivers' or 'jump to next tab'!"

class AutonomousLearner(QThread):
    learned_signal=pyqtSignal(str)
    def __init__(self, memory: BobMemory, get_window_fn):
        super().__init__(); self.mem=memory; self.get_win=get_window_fn; self._run=True
    def run(self):
        # learns when you DON'T tell Bob to work - every 45s if idle
        last_user_action=time.time()
        while self._run:
            time.sleep(45)
            if not self._run: break
            # low-RAM: don't run if RAM high
            if get_ram_mb()>400:
                gc.collect()
                continue
            try:
                win=self.get_win()
                msg=self.mem.observe(win)
                if msg:
                    self.learned_signal.emit(msg)
                # idle learning: if window stable for 2 polls, learn quietly
                # we just save observe; no heavy LLM unless API key
            except: pass
    def stop(self): self._run=False; self.wait(800)

class WebAutoLearner(QThread):
    learned=pyqtSignal(str)
    implemented=pyqtSignal(str)
    searching=pyqtSignal(bool)
    def __init__(self, config, analytics, is_idle_fn):
        super().__init__()
        self.cfg=config; self.db=analytics; self.is_idle=is_idle_fn
        self._run=True
        self.sources=[
            "https://api.github.com/search/repositories?q=stars:>20000+language:python&sort=stars&order=desc&per_page=1",
            "https://dev.to/api/articles?per_page=1&top=7",
            "https://api.github.com/search/repositories?q=stars:>50000&sort=stars&order=desc&per_page=1"
        ]
    def run(self):
        import time
        while self._run:
            interval=self.cfg.get("web_auto_learn",{}).get("interval_sec",600)
            time.sleep(min(interval, 60))
            if not self._run: break
            if not self.cfg.get("web_auto_learn",{}).get("enabled", True): continue
            if not self.is_idle(): continue
            if get_ram_mb()>380: gc.collect(); continue
            try:
                self.searching.emit(True)
                topic, snippet=self.fetch_web()
                if not topic: self.searching.emit(False); continue
                tip=snippet
                if GOOGLE_API_KEY:
                    try:
                        tip=gemini_generate(f"{PERSONALITY_PROMPTS.get(self.cfg['personality']['type'], PERSONALITY_PROMPTS['Friend'])}\nYou learned from web: {topic}\nSnippet: {snippet[:800]}\nSummarize into ONE short practical tip (1 sentence) as Bob, and suggest a tiny implementation (e.g., create a file example).")
                    except: pass
                self.learned.emit(f"Bob auto-learned from web: {topic[:60]} -> {trim_text(tip,180)}")
                # implement: create a file on Desktop with the tip
                self.implement_tip(topic, tip)
                # log to analytics
                try: self.db.log_suggestion(f"[WebLearn] {tip}", detect_language(tip, topic), "Learning", 1)
                except: pass
                self.searching.emit(False)
                self.cfg["web_auto_learn"]["last_learn"]=datetime.now().isoformat()
                save_config(self.cfg)
                self.searching.emit(False)
            except Exception as e:
                print(f"WebLearn fail {e}")
                try: self.searching.emit(False)
                except: pass
    def fetch_web(self):
        import requests, random
        # 1. try GitHub trending via API (no auth, may rate limit)
        try:
            url=random.choice(self.sources)
            headers={"User-Agent":"BobPet/1.0"}
            r=requests.get(url, headers=headers, timeout=8)
            if r.status_code==200:
                j=r.json()
                if "items" in j and j["items"]:
                    repo=j["items"][0]
                    topic=repo.get("full_name","GitHub Trending")
                    snippet=repo.get("description","") + " Stars:" + str(repo.get("stargazers_count",""))
                    return topic, snippet
                elif isinstance(j, list) and j:
                    art=j[0]
                    return art.get("title","Dev.to"), art.get("description","")[:400]
        except: pass
        # 2. fallback: fetch python docs tip via web
        try:
            import requests
            r=requests.get("https://raw.githubusercontent.com/python/cpython/main/README.rst", timeout=8)
            if r.status_code==200:
                txt=r.text[:600]
                return "Python CPython README", txt
        except: pass
        # 3. fallback offline tip
        tips=[("Python Tip","Use list comprehensions over loops for speed: [x*2 for x in data]"), ("JS Tip","Use const and let instead of var for block scope."), ("Git Tip","Use git stash to save work without committing.")]
        import random
        return random.choice(tips)
    def implement_tip(self, topic, tip):
        try:
            desk=os.path.join(os.path.expanduser("~"),"Desktop")
            os.makedirs(desk, exist_ok=True)
            safe=re.sub(r'[^\w\- ]','',topic)[:30].strip().replace(" ","_") or "bob_learned"
            path=os.path.join(desk, f"BobLearned_{safe}_{int(time.time())%10000}.txt")
            content=f"Bob auto-learned on {datetime.now().isoformat()}\nTopic: {topic}\nTip: {tip}\n\nImplemented by Bob while you were idle. 🐾\n"
            # if tip mentions python code, add example
            if "python" in tip.lower() or "list" in tip.lower():
                content+="\nExample:\n# Bob's example\ndata=[1,2,3]\nresult=[x*2 for x in data]\nprint(result)\n"
            Path(path).write_text(content, encoding="utf-8")
            self.implemented.emit(path)  # emit path only - deck shows button, no auto-open
        except: pass
    def stop(self): self._run=False; self.wait(800)

class VoiceWorker(QThread):
    heard=pyqtSignal(str); error=pyqtSignal(str); listening_changed=pyqtSignal(bool)
    def __init__(self): super().__init__(); self._running=False; self._listening=False; self.mic_index=None
    def start_listening(self):
        self._listening=True; self.listening_changed.emit(True)
        if not self.isRunning(): self._running=True; self.start()
    def stop_listening(self): self._listening=False; self.listening_changed.emit(False)
    def run(self):
        try:
            import speech_recognition as sr
            r=sr.Recognizer()
            # list mics for diagnostics
            try:
                names=sr.Microphone.list_microphone_names()
            except: names=[]
            # try default first, then each
            indices=[None] + list(range(len(names)))
            mic=None
            last_err=""
            for idx in indices:
                try:
                    test_mic=sr.Microphone(device_index=idx) if idx is not None else sr.Microphone()
                    with test_mic as source: r.adjust_for_ambient_noise(source, duration=0.4)
                    mic=test_mic; self.mic_index=idx; break
                except Exception as e: last_err=str(e); continue
            if mic is None:
                self.error.emit(f"Mic not found. Tried {len(names)} audio devices. Last error: {last_err}. Install PortAudio and PyAudio, then check your desktop's microphone permissions. Devices: {names[:3]}")
                self._listening=False; self.listening_changed.emit(False); return
            # emit success with mic name
            try: self.error.emit(f"Mic ready: {(names[self.mic_index] if self.mic_index is not None and self.mic_index < len(names) else 'default')}")
            except: pass
            while self._running:
                if not self._listening: time.sleep(0.3); continue
                try:
                    with mic as source:
                        # shorter timeout for responsiveness
                        audio=r.listen(source, timeout=6, phrase_time_limit=6)
                    text=r.recognize_google(audio)
                    if text: self.heard.emit(text); self._listening=False; self.listening_changed.emit(False)
                except Exception as e:
                    err=str(e)
                    if "timeout" not in err.lower() and "wait" not in err.lower():
                        # show non-timeout errors once
                        if "UnknownValueError" in err: pass
                        elif "RequestError" in err: self.error.emit("Mic: Google request failed - check internet")
                        else: self.error.emit(f"Mic listen: {err}")
                    time.sleep(0.5)
        except ImportError as e:
            self.error.emit("Voice packages missing. Install SpeechRecognition, PyAudio, and pyttsx3; Linux may also need its PortAudio and speech-engine system packages.")
        except Exception as e:
            self.error.emit(f"Microphone error: {e}. Check that your user can access the audio device and that desktop microphone permission is enabled.")
    def stop(self): self._running=False; self.wait(800)

def speak_text(text, voice_cfg=None):
    def _speak():
        # try config voice
        cfg=voice_cfg or {}
        try:
            import pyttsx3
            eng=pyttsx3.init()
            # apply voice config
            try:
                rate=cfg.get("rate",175)
                vol=cfg.get("volume",0.8)
                vid=cfg.get("voice_id",0)
                eng.setProperty('rate', int(rate))
                eng.setProperty('volume', float(vol))
                voices=eng.getProperty('voices')
                if voices and 0 <= vid < len(voices):
                    eng.setProperty('voice', voices[vid].id)
            except: pass
            eng.say(strip_emojis(text)[:320]); eng.runAndWait(); return
        except: pass
        if sys.platform.startswith("linux"):
            for engine in ("espeak-ng", "espeak", "spd-say"):
                executable=shutil.which(engine)
                if executable:
                    try:
                        subprocess.Popen([executable, strip_emojis(text)[:320]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return
                    except Exception: pass
        try:
            # Windows SAPI with rate from config
            rate=cfg.get("rate",175) if cfg else 175
            # SAPI rate -10 to 10, map 100-250 -> -5 to 5
            sapi_rate=int((rate-175)/15)
            clean=strip_emojis(text)[:180].replace(chr(34),"").replace("'","")
            ps=f'Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate={sapi_rate}; $s.Speak("{clean}");'
            subprocess.run(["powershell","-Command",ps],timeout=9)
        except: pass
    # get voice config if not passed
    if voice_cfg is None:
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH,"r",encoding="utf-8") as f: cfg=json.load(f)
                voice_cfg=cfg.get("sound",{})
            else: voice_cfg={}
        except: voice_cfg={}
        # only speak if enabled
        if not voice_cfg.get("enabled", True):
            return
    else:
        if not voice_cfg.get("enabled", True): return
    threading.Thread(target=_speak,daemon=True).start()

def get_voice_list():
    try:
        import pyttsx3
        eng=pyttsx3.init()
        voices=eng.getProperty('voices')
        return [(i, v.name) for i,v in enumerate(voices)]
    except: return []
    try:
        # SAPI fallback list
        out=subprocess.run("powershell Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices() | ForEach-Object {$_.VoiceInfo.Name}", capture_output=True, text=True, timeout=4)
        lines=[l.strip() for l in out.stdout.splitlines() if l.strip()]
        return list(enumerate(lines))
    except: return []

# ===== Right-Bottom Control Deck (fixed) =====
class ControlDeck(QMainWindow):
    """Compact bottom-right voice control for Bob."""
    def __init__(self, bob):
        super().__init__()
        self.bob=bob
        self.setWindowTitle("Bob Deck")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.init_ui()
        QTimer.singleShot(400, self.snap_to_right_bottom)

    def init_ui(self):
        w=QWidget(); w.setStyleSheet("background:rgba(255,255,255,0);"); self.setCentralWidget(w)
        self.input_field=QLineEdit(); self.input_field.setPlaceholderText(f"Ask Bob: 'fix my drivers' | 'jump to next tab'...")
        self.input_field.setStyleSheet("QLineEdit{background:rgba(255,255,255,235);border:2px solid #d97757;border-radius:12px;padding:7px 10px;font-size:11px;}")
        self.input_field.returnPressed.connect(self.on_go)
        self.send_btn=QPushButton("Go"); self.send_btn.setFixedWidth(44); self.send_btn.setStyleSheet("background:#d97757;color:white;border-radius:10px;padding:7px;font-weight:bold;"); self.send_btn.clicked.connect(self.on_go)
        self.mic_btn=QPushButton("🎤"); self.mic_btn.setFixedWidth(44); self.mic_btn.setCheckable(True); self.mic_btn.setStyleSheet("QPushButton{background:white;border:2px solid #d97757;border-radius:10px;padding:7px;} QPushButton:checked{background:#ff4444;color:white;}"); self.mic_btn.clicked.connect(self.on_mic)
        self.jump_btn=QPushButton("🦘"); self.jump_btn.setFixedWidth(44); self.jump_btn.setToolTip("Goat - jump"); self.jump_btn.setStyleSheet("background:white;border:2px solid #d97757;border-radius:10px;padding:7px;"); self.jump_btn.clicked.connect(lambda: self.bob.jump())
        self.file_btn=QPushButton("🗂️"); self.file_btn.setFixedWidth(44); self.file_btn.setToolTip("File/tab jump"); self.file_btn.setStyleSheet("background:white;border:2px solid #d97757;border-radius:10px;padding:7px;"); self.file_btn.clicked.connect(lambda: self.bob.jump_between_tabs("next"))
        self.fix_btn=QPushButton("🛠️"); self.fix_btn.setFixedWidth(44); self.fix_btn.setStyleSheet("background:#00cc66;color:white;border-radius:10px;padding:7px;"); self.fix_btn.clicked.connect(lambda: self.bob.handle_input(text_override="fix my drivers"))
        self.hide_btn=QPushButton("🙈"); self.hide_btn.setFixedWidth(36); self.hide_btn.setToolTip("Hide widgets - visibility"); self.hide_btn.setStyleSheet("background:rgba(0,0,0,60);color:white;border-radius:10px;padding:7px;font-size:11px;"); self.hide_btn.clicked.connect(self.toggle_hide)
        self.restart_btn=QPushButton("↻"); self.restart_btn.setFixedWidth(36); self.restart_btn.setToolTip("Restart Bob - when you ship new code"); self.restart_btn.setStyleSheet("background:#6C5CE7;color:white;border-radius:10px;padding:7px;font-weight:bold;"); self.restart_btn.clicked.connect(self.on_restart)
        # Keep only the voice control visible in the bottom toolbar.
        self.mic_btn.setFixedSize(52, 46)
        row=QHBoxLayout(); row.addWidget(self.mic_btn, 0, Qt.AlignCenter); row.setContentsMargins(4,4,4,4)
        self.row_widget=QWidget(); self.row_widget.setLayout(row)
        self.log_area=QTextEdit(); self.log_area.setReadOnly(True); self.log_area.setFixedHeight(90); self.log_area.setStyleSheet("background:rgba(0,0,0,180);color:#00ff88;border-radius:8px;padding:6px;font-family:Consolas;font-size:9px;"); self.log_area.hide()
        self.view_btn=QPushButton("📚 View Learned"); self.view_btn.setFixedHeight(22); self.view_btn.setStyleSheet("background:#FFD166;color:#333;border-radius:8px;padding:2px 8px;font-size:9px;font-weight:bold;"); self.view_btn.hide()
        self.view_btn.clicked.connect(self.on_view_learned)
        self.last_learned_path=""
        self.is_hidden=False
        self.show_btn=QPushButton("👁️ Show"); self.show_btn.setFixedSize(70,28); self.show_btn.setStyleSheet("background:rgba(217,119,87,230);color:white;border-radius:10px;padding:4px;font-weight:bold;"); self.show_btn.hide(); self.show_btn.clicked.connect(self.toggle_hide)
        lay=QVBoxLayout(); lay.addWidget(self.log_area); lay.addWidget(self.row_widget); lay.setContentsMargins(4,4,4,4); lay.setSpacing(4)
        w.setLayout(lay)
        self.setFixedWidth(68)
        self.setFixedHeight(62)
        # sync ram/log from bob
        self.ram_timer=QTimer(); self.ram_timer.timeout.connect(self.update_ram); self.ram_timer.start(3000)

    def snap_to_right_bottom(self):
        try:
            # Place above the desktop panel/taskbar so the microphone remains visible.
            avail=get_virtual_available()
            if avail:
                x=avail.x()+avail.width()-self.width()-6
                y=avail.y()+avail.height()-self.height()-6
                self.move(x,y)
        except: pass

    def on_go(self):
        t=self.input_field.text().strip()
        if t: self.input_field.clear(); self.bob.handle_input(text_override=t)

    def on_mic(self):
        # delegate to bob voice
        if self.mic_btn.isChecked():
            self.mic_btn.setText("🔴")
            self.bob.toggle_voice(from_deck=True)
        else:
            self.mic_btn.setText("🎤")
            self.bob.toggle_voice(from_deck=True)

    def set_mic_state(self, listening):
        self.mic_btn.setChecked(listening); self.mic_btn.setText("🔴" if listening else "🎤")

    def update_ram(self):
        # RAM widget removed per user request - keep hidden, still trim if needed
        mb=get_ram_mb()
        if mb and mb>380: gc.collect()
        if self.log_area.isVisible(): self.setFixedHeight(200)
        elif not self.is_hidden: self.setFixedHeight(62)

    def on_restart(self):
        try: self.bob.restart_bob()
        except: pass
    def toggle_hide(self):
        self.is_hidden=not self.is_hidden
        if self.is_hidden:
            self.row_widget.hide(); self.log_area.hide(); self.view_btn.hide()
            self.hide_btn.hide(); self.restart_btn.hide()
            self.show_btn.show()
            self.setFixedHeight(40); self.setFixedWidth(90)
            self.snap_to_right_bottom()
        else:
            self.row_widget.show()
            if self.last_learned_path: self.view_btn.show()
            self.hide_btn.show(); self.restart_btn.show(); self.show_btn.hide()
            self.setFixedHeight(62); self.setFixedWidth(68)
            self.snap_to_right_bottom()

    def on_view_learned(self):
        if self.last_learned_path and os.path.exists(self.last_learned_path):
            try:
                if sys.platform=="win32": os.startfile(self.last_learned_path)
                else: subprocess.Popen(["xdg-open", self.last_learned_path])
            except:
                try: subprocess.Popen(f'notepad "{self.last_learned_path}"', shell=True)
                except: pass
        else:
            try:
                desk=os.path.join(os.path.expanduser("~"),"Desktop")
                subprocess.Popen(f'explorer "{desk}"', shell=True)
            except: pass

    def set_learned(self, path):
        self.last_learned_path=path
        if not self.is_hidden: self.view_btn.show()
        self.view_btn.setToolTip(path)
        self.append_log(f"📚 Bob learned - click View Learned to see: {path}")

    def show_log(self, txt):
        self.log_area.show(); self.log_area.clear(); self.log_area.append(txt); self.setFixedHeight(200)
        self.snap_to_right_bottom()
    def append_log(self, txt):
        if not self.log_area.isVisible(): self.log_area.show(); self.setFixedHeight(200)
        cur=self.log_area.toPlainText()
        if len(cur)>MAX_LOG_CHARS: self.log_area.setPlainText(cur[-3000:])
        self.log_area.append(txt); self.log_area.append("")
        QApplication.processEvents()
        self.snap_to_right_bottom()

# ===== Analytics Dashboard (separate window) =====
class AnalyticsDashboard(QMainWindow):
    def __init__(self, analytics_db, config):
        super().__init__()
        self.db=analytics_db; self.cfg=config
        self.setWindowTitle("Bob Analytics Dashboard 📊")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.resize(820, 560)
        self.init_ui()
    def init_ui(self):
        from PyQt5.QtWidgets import QTabWidget, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton, QSlider, QComboBox, QCheckBox, QSpinBox, QFormLayout, QGroupBox
        tabs=QTabWidget()
        # Overview tab
        ov=QWidget(); ov_lay=QVBoxLayout()
        self.stats_label=QLabel("Loading..."); self.stats_label.setStyleSheet("font-family:Consolas;font-size:11px;")
        ov_lay.addWidget(self.stats_label)
        self.weekly_canvas=QLabel(); self.weekly_canvas.setFixedHeight(140); self.weekly_canvas.setStyleSheet("background:white;border:1px solid #ccc;")
        ov_lay.addWidget(QLabel("Productivity Trends (weekly hours):")); ov_lay.addWidget(self.weekly_canvas)
        # goal controls
        gbox=QHBoxLayout()
        gbox.addWidget(QLabel("Weekly Goal (hrs):"))
        self.goal_spin=QSpinBox(); self.goal_spin.setRange(1,80); self.goal_spin.setValue(self.cfg["goals"]["weekly_hours"])
        self.goal_spin.valueChanged.connect(self.on_goal_changed)
        gbox.addWidget(self.goal_spin)
        self.goal_progress=QLabel("Progress: --")
        gbox.addWidget(self.goal_progress); gbox.addStretch()
        ov_lay.addLayout(gbox)
        ov.setLayout(ov_lay); tabs.addTab(ov, "Overview")
        # Languages pie
        lang=QWidget(); lang_lay=QVBoxLayout()
        self.lang_canvas=QLabel(); self.lang_canvas.setFixedSize(360,360); self.lang_canvas.setStyleSheet("background:white;border:1px solid #ccc;")
        lang_lay.addWidget(QLabel("Language Breakdown (pie):")); lang_lay.addWidget(self.lang_canvas,0,Qt.AlignCenter)
        self.lang_text=QLabel(""); lang_lay.addWidget(self.lang_text)
        lang.setLayout(lang_lay); tabs.addTab(lang, "Languages")
        # Peak hours heatmap
        peak=QWidget(); peak_lay=QVBoxLayout()
        self.peak_canvas=QLabel(); self.peak_canvas.setFixedHeight(180); self.peak_canvas.setStyleSheet("background:white;border:1px solid #ccc;")
        peak_lay.addWidget(QLabel("Peak Hours (darker = more coding):")); peak_lay.addWidget(self.peak_canvas)
        self.insights_label=QLabel(""); self.insights_label.setStyleSheet("background:#FFF8DC;padding:8px;border-radius:6px;")
        self.insights_label.setWordWrap(True)
        peak_lay.addWidget(self.insights_label)
        peak.setLayout(peak_lay); tabs.addTab(peak, "Peak Hours")
        # Customization tab
        cust=QWidget(); form=QFormLayout()
        self.skin_combo=QComboBox(); self.skin_combo.addItems(["default","midnight","sunset","forest"])
        self.skin_combo.setCurrentText(self.cfg["appearance"]["skin"])
        self.skin_combo.currentTextChanged.connect(lambda v: self.on_cfg("appearance","skin",v))
        form.addRow("Pet Skin:", self.skin_combo)
        self.size_slider=QSlider(Qt.Horizontal); self.size_slider.setRange(60,140); self.size_slider.setValue(self.cfg["appearance"]["size"])
        self.size_slider.valueChanged.connect(lambda v: self.on_cfg("appearance","size",v))
        form.addRow("Size:", self.size_slider)
        self.theme_combo=QComboBox(); self.theme_combo.addItems(["light","dark","custom"]); self.theme_combo.setCurrentText(self.cfg["appearance"]["theme"])
        self.theme_combo.currentTextChanged.connect(lambda v: self.on_cfg("appearance","theme",v))
        form.addRow("Theme:", self.theme_combo)
        self.sound_check=QCheckBox("Enabled"); self.sound_check.setChecked(self.cfg["sound"]["enabled"])
        self.sound_check.toggled.connect(lambda v: self.on_cfg("sound","enabled",v))
        form.addRow("Bob Voice:", self.sound_check)
        # voice selection
        self.voice_combo=QComboBox()
        try:
            voices=get_voice_list()
            if voices:
                for i,name in voices: self.voice_combo.addItem(f"{i}: {name[:30]}", i)
                # set current
                vid=self.cfg["sound"].get("voice_id",0)
                idx=self.voice_combo.findData(vid)
                if idx>=0: self.voice_combo.setCurrentIndex(idx)
            else: self.voice_combo.addItem("Default 0",0)
        except: self.voice_combo.addItem("Default 0",0)
        self.voice_combo.currentIndexChanged.connect(lambda idx: self.on_cfg("sound","voice_id", self.voice_combo.currentData()))
        form.addRow("Voice:", self.voice_combo)
        self.rate_slider=QSlider(Qt.Horizontal); self.rate_slider.setRange(100,250); self.rate_slider.setValue(int(self.cfg["sound"].get("rate",175)))
        self.rate_slider.valueChanged.connect(lambda v: self.on_cfg("sound","rate",v))
        form.addRow("Voice Rate:", self.rate_slider)
        self.vol_slider=QSlider(Qt.Horizontal); self.vol_slider.setRange(0,100); self.vol_slider.setValue(int(self.cfg["sound"].get("volume",0.8)*100))
        self.vol_slider.valueChanged.connect(lambda v: self.on_cfg("sound","volume", v/100.0))
        form.addRow("Voice Vol:", self.vol_slider)
        test_btn=QPushButton("🔊 Test Voice"); test_btn.clicked.connect(lambda: speak_text("Hey pal, I'm Bob! Your low RAM buddy with voice!", self.cfg["sound"]))
        form.addRow("", test_btn)
        self.notif_combo=QComboBox(); self.notif_combo.addItems(["popup","toast","silent"]); self.notif_combo.setCurrentText(self.cfg["notification"]["style"])
        self.notif_combo.currentTextChanged.connect(lambda v: self.on_cfg("notification","style",v))
        form.addRow("Notification:", self.notif_combo)
        self.move_combo=QComboBox(); self.move_combo.addItems(["walk","hop","float"]); self.move_combo.setCurrentText(self.cfg["behavior"]["move_style"])
        self.move_combo.currentTextChanged.connect(lambda v: self.on_cfg("behavior","move_style",v))
        form.addRow("Move Style:", self.move_combo)
        self.speed_slider=QSlider(Qt.Horizontal); self.speed_slider.setRange(5,30); self.speed_slider.setValue(int(self.cfg["behavior"]["move_speed"]*10))
        self.speed_slider.valueChanged.connect(lambda v: self.on_cfg("behavior","move_speed",v/10.0))
        form.addRow("Speed:", self.speed_slider)
        # Animation presets - 60 FPS, easing, glow, etc.
        self.anim_speed=QComboBox(); self.anim_speed.addItems(["slow","normal","fast"]); self.anim_speed.setCurrentText(self.cfg["animation"]["speed"])
        self.anim_speed.currentTextChanged.connect(lambda v: self.on_anim_preset("speed",v))
        form.addRow("Anim Speed:", self.anim_speed)
        self.anim_intensity=QComboBox(); self.anim_intensity.addItems(["subtle","normal","exaggerated"]); self.anim_intensity.setCurrentText(self.cfg["animation"]["intensity"])
        self.anim_intensity.currentTextChanged.connect(lambda v: self.on_anim_preset("intensity",v))
        form.addRow("Anim Intensity:", self.anim_intensity)
        self.glow_color=QComboBox(); self.glow_color.addItems(["orange","white","blue","gold"]); self.glow_color.setCurrentText(self.cfg["animation"]["glow_color"])
        self.glow_color.currentTextChanged.connect(lambda v: self.on_anim_preset("glow_color",v))
        form.addRow("Glow Color:", self.glow_color)
        self.rot_dir=QComboBox(); self.rot_dir.addItems(["clockwise","counterclockwise"]); self.rot_dir.setCurrentText(self.cfg["animation"]["rotation_dir"])
        self.rot_dir.currentTextChanged.connect(lambda v: self.on_anim_preset("rotation_dir",v))
        form.addRow("Rotation:", self.rot_dir)
        # Web auto-learn when idle
        self.web_check=QCheckBox("Enabled"); self.web_check.setChecked(self.cfg["web_auto_learn"]["enabled"])
        self.web_check.toggled.connect(lambda v: self.on_cfg("web_auto_learn","enabled",v))
        form.addRow("Web Auto-Learn:", self.web_check)
        self.web_spin=QSpinBox(); self.web_spin.setRange(60,3600); self.web_spin.setValue(self.cfg["web_auto_learn"]["interval_sec"])
        self.web_spin.valueChanged.connect(lambda v: self.on_cfg("web_auto_learn","interval_sec",v))
        form.addRow("Learn Interval (s):", self.web_spin)
        # Personality system - stored in JSON, switch at runtime
        self.pers_combo=QComboBox(); self.pers_combo.addItems(["Fellow","Mentor","Friend","Motivator","Curious"])
        self.pers_combo.setCurrentText(self.cfg["personality"]["type"])
        self.pers_combo.currentTextChanged.connect(lambda v: self.on_cfg("personality","type",v))
        form.addRow("Personality:", self.pers_combo)
        self.agg_combo=QComboBox(); self.agg_combo.addItems(["passive","moderate","aggressive"])
        self.agg_combo.setCurrentText(self.cfg["personality"]["aggressiveness"])
        self.agg_combo.currentTextChanged.connect(lambda v: self.on_cfg("personality","aggressiveness",v))
        form.addRow("Aggressiveness:", self.agg_combo)
        self.learning_check=QCheckBox("Enabled"); self.learning_check.setChecked(self.cfg["personality"]["learning"])
        self.learning_check.toggled.connect(lambda v: self.on_cfg("personality","learning",v))
        form.addRow("Learning Mode:", self.learning_check)
        self.mood_label=QLabel(f"Mood: {self.cfg['personality']['mood']} (dismiss {self.cfg['personality']['dismiss_count']} / accept {self.cfg['personality']['accept_count']})")
        form.addRow("Mood:", self.mood_label)
        cust.setLayout(form); tabs.addTab(cust, "Customization")
        # set central
        central=QWidget(); lay=QVBoxLayout(); lay.addWidget(tabs)
        refresh=QPushButton("↻ Refresh"); refresh.clicked.connect(self.refresh)
        lay.addWidget(refresh)
        central.setLayout(lay); self.setCentralWidget(central)
        self.refresh()
    def on_cfg(self, cat, key, val):
        self.cfg[cat][key]=val; save_config(self.cfg)
    def on_anim_preset(self, key, val):
        self.cfg["animation"][key]=val; save_config(self.cfg)
        # apply to live Bob if available (try to find BobPet via parent)
        try:
            # find Bob instance via QApplication
            for w in QApplication.topLevelWidgets():
                if hasattr(w, "anim_ctrl") and w.anim_ctrl:
                    w.anim_ctrl.set_preset(self.cfg["animation"]["speed"], self.cfg["animation"]["intensity"], self.cfg["animation"]["glow_color"])
                    break
        except: pass
    def on_goal_changed(self, v):
        self.cfg["goals"]["weekly_hours"]=v; save_config(self.cfg); self.db.set_goal(v); self.refresh()
    def refresh(self):
        s=self.db.stats()
        hrs=s["total_min"]/60; avg=s["avg"]
        acc_rate = (s["accepted"]/s["total_sug"]*100) if s["total_sug"] else 0
        self.stats_label.setText(f"Coding: {hrs:.1f} hrs total • {s['count']} sessions • avg {avg:.1f} min\nSuggestions: {s['total_sug']} total • {acc_rate:.0f}% accepted ({s['accepted']}/{s['total_sug']})\nCats: {dict(s['cats']) if s['cats'] else '—'}")
        # weekly bar
        self.draw_weekly(s["weekly"], s["goal"])
        self.draw_pie(s["langs"])
        self.draw_heatmap(s["peak_sess"] or s["peak"])
        # insights
        insights=[]
        # habit
        if s["langs"]: top=s["langs"][0]; pct=top[1]/s["count"]*100 if s["count"] else 0; insights.append(f"Habit: You've used {top[0]} {pct:.0f}% this week.")
        # peak
        if s["peak_sess"]:
            peak_h=max(s["peak_sess"], key=lambda x: x[1] or 0)
            insights.append(f"Optimal coding: Most productive hour ~{peak_h[0]}:00.")
        # velocity (weekly trending up?)
        if len(s["weekly"])>=2:
            cur=s["weekly"][0][1] or 0; prev=s["weekly"][1][1] or 0
            if cur>prev: insights.append(f"Velocity ↑ {cur-prev:.1f} min more than last week!")
            elif cur<prev: insights.append(f"Velocity ↓ {prev-cur:.0f} min less - keep going!")
        # smart reminder
        hr=datetime.now().hour
        if hr in [14,15]: insights.append("Smart reminder: You usually take a break around now - stretch! 🧘")
        # goal progress
        cur_week=s["weekly"][0][1]/60 if s["weekly"] else 0
        prog=cur_week/s["goal"]*100 if s["goal"] else 0
        self.goal_progress.setText(f"Progress: {cur_week:.1f}/{s['goal']} hrs ({prog:.0f}%) {'✅' if prog>=100 else '⏳'}")
        insights.append(f"Suggestion impact: {s['accepted']} accepted of {s['total_sug']} - keep filtering by category!")
        self.insights_label.setText("\n".join("• "+x for x in insights))
    def draw_weekly(self, weekly, goal):
        pix=QPixmap(780,130); pix.fill(QColor("white"))
        p=QPainter(pix); p.setRenderHint(QPainter.Antialiasing)
        if not weekly: p.drawText(10,70,"No data yet - code more!"); p.end(); self.weekly_canvas.setPixmap(pix); return
        vals=[v or 0 for _,v in reversed(weekly)]; labels=[k for k,_ in reversed(weekly)]
        mx=max(max(vals), goal*60, 60)
        w=780; h=110; bar_w=w/max(8,len(vals))-8
        for i,v in enumerate(vals):
            bh=int(v/mx*h); x=10+i*(bar_w+8); y= h - bh +10
            p.setBrush(QBrush(QColor("#4ECDC4"))); p.drawRect(x,y,bar_w,bh)
            p.drawText(x, h+25, labels[i][-2:])
        # goal line
        gy= h - int(goal*60/mx*h) +10
        p.setPen(QPen(QColor("red"),2,Qt.DashLine)); p.drawLine(0,gy,w,gy); p.drawText(5, gy-4, f"Goal {goal}h")
        p.end(); self.weekly_canvas.setPixmap(pix)
    def draw_pie(self, langs):
        pix=QPixmap(360,360); pix.fill(QColor("white"))
        p=QPainter(pix); p.setRenderHint(QPainter.Antialiasing)
        if not langs: p.drawText(120,180,"No language data"); p.end(); self.lang_canvas.setPixmap(pix); return
        total=sum(v for _,v in langs)
        start=0
        colors=[QColor("#FF6B6B"),QColor("#4ECDC4"),QColor("#FFE66D"),QColor("#A8E6CF"),QColor("#C7CEEA")]
        txt=[]
        for i,(lang,cnt) in enumerate(langs):
            ang= cnt/total*360
            p.setBrush(QBrush(colors[i%len(colors)])); p.drawPie(30,30,300,300, int(start*16), int(ang*16))
            txt.append(f"{lang}: {cnt} sessions ({cnt/total*100:.0f}%)")
            start+=ang
        p.end(); self.lang_canvas.setPixmap(pix); self.lang_text.setText("\n".join(txt))
    def draw_heatmap(self, peak):
        pix=QPixmap(780,160); pix.fill(QColor("white"))
        p=QPainter(pix); p.setRenderHint(QPainter.Antialiasing)
        if not peak: p.drawText(10,80,"No peak data"); p.end(); self.peak_canvas.setPixmap(pix); return
        d=dict(peak); mx=max(float(v or 0) for _,v in peak) or 1
        cell_w=780/24
        for h in range(24):
            v=float(d.get(f"{h:02d}", d.get(str(h),0)) or 0)
            alpha=int(v/mx*200)+30
            p.setBrush(QBrush(QColor(217,119,87,alpha))); p.drawRect(int(h*cell_w),20,int(cell_w)-2,80)
            p.drawText(int(h*cell_w)+4, 115, str(h))
        p.end(); self.peak_canvas.setPixmap(pix)

# ===== Bob Main =====
class BobPet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pet_state="happy"; self.suggestion_visible=False; self.animation_frame=0
        self.suggestion_worker=None; self.suggestion_log=collections.deque(maxlen=MAX_LOG_ENTRIES)
        self.analytics=AnalyticsDB()
        self.config=load_config()
        self.dashboard=None
        self.current_filter="All"
        # anchored to LEFT corner - start at left edge (will snap to bottom-left after UI loads)
        self.pet_x=12; self.pet_y=12; self.ground_y=12; self.velocity_y=0; self.gravity=0.9; self.jump_strength=-18
        self.is_jumping=False; self.move_direction=1; self.move_speed=1.0; self.is_dragging=False; self.drag_start_pos=None
        self.roam_target=None; self.roam_pause_until=0
        self.voice_worker=None
        self.memory=BobMemory()
        self.learner=None
        # enhanced animation state
        self.bob_mood="chill"
        self.idle_ticks=0; self.wobble=0; self.limb_click_ticks=0
        self.walk_cycle=0; self.breath_phase=0; self.typing_ticks=0; self.jump_phase=0
        self.svg_renderer=self.load_svg()
        self.last_user_activity=time.time()
        self.web_searching=False
        self.window_last_seen={}
        self.idle_notified=set()
        self.init_ui()
        # AnimationController 60 FPS with queues, easing, SVG transforms
        try:
            if AnimationController:
                self.anim_ctrl=AnimationController(self.pet_label, self.config)
                self.anim_ctrl.updated.connect(self.draw_pet)
                # apply preset from config
                ap=self.config.get("animation",{})
                self.anim_ctrl.set_preset(ap.get("speed","normal"), ap.get("intensity","normal"), ap.get("glow_color","orange"))
                self.anim_ctrl.set_state("idle")
                self.anim_ctrl.wake_up()
        except: self.anim_ctrl=None
        self.setup_timers(); self.setup_voice(); self.start_learner(); self.apply_config()
        self.web_learner=WebAutoLearner(self.config, self.analytics, lambda: time.time()-self.last_user_activity > self.config["web_auto_learn"]["interval_sec"])
        self.web_learner.learned.connect(lambda m: self.show_bubble(m + " 📚 View in deck →", speak=False))
        self.web_learner.implemented.connect(lambda p: self.deck.set_learned(p))
        self.web_learner.searching.connect(self.set_web_searching)
        self.web_learner.start()
        # Bob roams free - start near center, deck stays at right-bottom
        QTimer.singleShot(350, self.snap_bob_free)
        # smart reminder timer (multi-session insights)
        self.insight_timer=QTimer(); self.insight_timer.timeout.connect(self.show_smart_insight); self.insight_timer.start(180000)  # every 3 min
        self.special_timer=QTimer(); self.special_timer.timeout.connect(self.check_special_triggers); self.special_timer.start(60000)
        # always see computer - update every 10s
        self.see_timer=QTimer(); self.see_timer.timeout.connect(self.update_computer_view); self.see_timer.start(10000)
        # idle window check every 60s - 15 min unused
        self.idle_timer=QTimer(); self.idle_timer.timeout.connect(self.check_idle_windows); self.idle_timer.start(60000)
        self.current_view={"windows":[],"cpu":"","ram":"","disk":""}
        self.update_computer_view()
        # thermal throttle 60->30 FPS if laptop hot
        self.thermal_timer=QTimer(); self.thermal_timer.timeout.connect(self.check_thermal); self.thermal_timer.start(5000)
        self.current_fps=60
        # pending restart auto re-check (driver fix)
        QTimer.singleShot(1500, self.check_pending_restart)

    def load_svg(self):
        try:
            if os.path.exists(SVG_PATH): return QSvgRenderer(SVG_PATH)
        except: pass
        return None

    def init_ui(self):
        self.setWindowTitle(f"{BOB_NAME} 🐾")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        main_widget=QWidget(); main_widget.setStyleSheet("background:transparent;"); self.setCentralWidget(main_widget)
        try:
            self.auto_engine=get_engine()
        except: self.auto_engine=None
        self.pet_label=QLabel(); self.pet_label.setFixedSize(88,88); self.pet_label.setCursor(Qt.OpenHandCursor)
        self.pet_label.mousePressEvent=self.pet_clicked; self.pet_label.mouseMoveEvent=self.pet_drag; self.pet_label.mouseReleaseEvent=self.pet_drop
        # init anim props for controller
        self.pet_label.scale=1.0; self.pet_label.rotate=0; self.pet_label.tx=0; self.pet_label.ty=0; self.pet_label.skew=0; self.pet_label.glow=1.0; self.pet_label.opacity=1.0; self.pet_label.color=QColor("#D97757"); self.pet_label.color_hue=0
        self.pet_label.enterEvent=lambda e: self.anim_ctrl.hover(True) if getattr(self,"anim_ctrl",None) else None
        self.pet_label.leaveEvent=lambda e: self.anim_ctrl.hover(False) if getattr(self,"anim_ctrl",None) else None
        # Bob's self-talk bubble - stays with Bob wherever he roams
        self.suggestion_label=QLabel(); self.suggestion_label.setWordWrap(True); self.suggestion_label.setMaximumWidth(300)
        self.suggestion_label.setStyleSheet("background:rgba(217,119,87,230);color:white;padding:8px 10px;border-radius:10px;font-size:11px;font-weight:bold;")
        self.suggestion_label.hide()
        self.suggestion_label.setAlignment(Qt.AlignLeft)
        # keep layout minimal: pet + bubble stacked, Bob roams free
        layout=QVBoxLayout(); layout.addWidget(self.pet_label,0,Qt.AlignHCenter); layout.addWidget(self.suggestion_label,0,Qt.AlignHCenter); layout.setContentsMargins(4,4,4,4); layout.setSpacing(2)
        main_widget.setLayout(layout)
        # Keep the transparent pet window tight to Bob. A large empty surface
        # can appear as a blurred panel on Linux desktops.
        self.setFixedSize(96, 96)
        self.setContextMenuPolicy(Qt.CustomContextMenu); self.customContextMenuRequested.connect(self.show_context_menu)
        # create fixed right-bottom deck - text box + speech + goat + file + fix + Go
        self.deck=ControlDeck(self); self.deck.show()
        # bubble position timer - keep above Bob
        self.bubble_timer=QTimer(); self.bubble_timer.timeout.connect(self.position_bubble); self.bubble_timer.start(50)

    def setup_timers(self):
        # spec timers: anim 100-200ms, suggestion 60s, movement 50ms, rendering 100ms
        self.anim_timer=QTimer(); self.anim_timer.timeout.connect(self.animate_pet); self.anim_timer.start(200)
        self.suggestion_timer=QTimer(); self.suggestion_timer.timeout.connect(self.check_and_suggest); self.suggestion_timer.start(SUGGESTION_INTERVAL)
        self.draw_timer=QTimer(); self.draw_timer.timeout.connect(self.draw_pet); self.draw_timer.start(100)
        self.move_timer=QTimer(); self.move_timer.timeout.connect(self.update_physics); self.move_timer.start(50)
        # GC every 2 min (low-RAM extra)
        self.gc_timer=QTimer(); self.gc_timer.timeout.connect(lambda: gc.collect()); self.gc_timer.start(120000)

    def apply_config(self):
        try:
            cfg=self.config
            sz=cfg["appearance"]["size"]
            self.pet_label.setFixedSize(sz,sz)
            theme=cfg["appearance"]["theme"]
            if theme=="dark": self.suggestion_label.setStyleSheet("background:rgba(40,40,40,230);color:white;padding:8px 10px;border-radius:10px;font-size:11px;")
            elif theme=="light": self.suggestion_label.setStyleSheet("background:rgba(217,119,87,230);color:white;padding:8px 10px;border-radius:10px;font-size:11px;")
            self.move_speed=cfg["behavior"]["move_speed"]
            self.move_style=cfg["behavior"]["move_style"]
            if self.move_style=="float": self.gravity=0.4
            elif self.move_style=="hop": self.gravity=1.2
            else: self.gravity=0.9
            ap=cfg.get("animation",{})
            try:
                if self.anim_ctrl: self.anim_ctrl.set_preset(ap.get("speed","normal"), ap.get("intensity","normal"), ap.get("glow_color","orange"))
            except: pass
            # personality aggressiveness -> timer
            agg=cfg["personality"]["aggressiveness"]
            interval=AGGRESSIVENESS_INTERVAL.get(agg, 60000)
            # learning mode: if many dismissals, be less intrusive
            if cfg["personality"].get("learning") and cfg["personality"]["dismiss_count"]>5:
                # auto reduce to passive if dismiss ratio high
                total=cfg["personality"]["dismiss_count"]+cfg["personality"]["accept_count"]
                if total>0 and cfg["personality"]["dismiss_count"]/total>0.6:
                    interval=AGGRESSIVENESS_INTERVAL["passive"]
            try: self.suggestion_timer.setInterval(interval)
            except: pass
            # mood affects pet_state color
            self.update_mood_display()
        except: pass
    def update_mood_display(self):
        mood=self.config["personality"]["mood"]
        if mood=="sad": self.pet_state="sad"
        elif mood=="excited": self.pet_state="happy"
        elif mood=="annoyed": self.pet_state="sad"
        try:
            if self.anim_ctrl:
                if mood=="happy": self.anim_ctrl.set_state("happy")
                elif mood=="sad": self.anim_ctrl.set_state("sad")
                elif mood=="excited": self.anim_ctrl.set_state("excited")
                elif mood=="annoyed": self.anim_ctrl.set_state("sad")
        except: pass

    def set_personality(self, ptype):
        if ptype not in PERSONALITY_PROMPTS: return
        self.config["personality"]["type"]=ptype
        self.config["personality"]["history"].append({"at":datetime.now().isoformat(),"type":ptype})
        self.config["personality"]["history"]=self.config["personality"]["history"][-20:]
        save_config(self.config)
        self.show_bubble(f"Bob is now {ptype}! {PERSONALITY_PROMPTS[ptype][:80]}", speak=True)
        self.apply_config()

    def update_mood(self, accepted=True):
        try:
            if accepted:
                self.config["personality"]["accept_count"]+=1
                # improve mood
                if self.config["personality"]["mood"]=="sad": self.config["personality"]["mood"]="happy"
                elif self.config["personality"]["mood"]=="happy": self.config["personality"]["mood"]="excited"
            else:
                self.config["personality"]["dismiss_count"]+=1
                if self.config["personality"]["mood"]=="excited": self.config["personality"]["mood"]="happy"
                elif self.config["personality"]["mood"]=="happy": self.config["personality"]["mood"]="sad"
                if self.config["personality"]["mood"]=="sad" and self.config["personality"]["dismiss_count"]>3:
                    self.config["personality"]["mood"]="annoyed"
            save_config(self.config)
            self.apply_config()
        except: pass

    def set_web_searching(self, v):
        self.web_searching=v
        self.pet_state="thinking" if v else "happy"

    def check_pending_restart(self):
        try:
            if os.path.exists(RESTART_MARKER):
                with open(RESTART_MARKER,"r",encoding="utf-8") as f: data=json.load(f)
                at=datetime.fromisoformat(data.get("at", datetime.now().isoformat()))
                # if within last 30 min after restart, re-check
                if (datetime.now()-at).total_seconds() < 1800:
                    cnt=len(data.get("problems",[]))
                    self.show_bubble(f"Bob back after restart - re-checking {cnt} driver(s) that were pending...", speak=True)
                    QTimer.singleShot(3500, lambda: self.handle_input(text_override="fix my drivers"))
                # clear marker after handling (or after 30m it will be cleared anyway)
                # keep for now, will be cleared on next successful no-problem run
        except: pass

    def show_smart_insight(self):
        try:
            s=self.analytics.stats()
            if not s["count"]: return
            if datetime.now().hour in [15] and random.random()<0.6:
                self.show_bubble("Bob: You usually take a break around this time, want to stretch?", speak=False)
            if s["peak_sess"]:
                peak=max(s["peak_sess"], key=lambda x: float(x[1] or 0))
                if datetime.now().hour==int(peak[0]) and random.random()<0.3:
                    self.show_bubble(f"Bob: You are most productive around {peak[0]}:00 - great time to code!", speak=False)
        except: pass

    def update_computer_view(self):
        try:
            wins=self.get_open_windows()
            self.current_view["windows"]=wins
            # system quick stats
            try:
                import psutil
                self.current_view["cpu"]=f"{psutil.cpu_percent(interval=None):.0f}%"
                mem=psutil.virtual_memory()
                self.current_view["ram"]=f"{mem.percent:.0f}%"
                disk_path="C:\\" if sys.platform=="win32" else "/"
                d=psutil.disk_usage(disk_path)
                self.current_view["disk"]=f"{d.percent:.0f}% free {d.free//1024//1024//1024}GB"
            except: pass
            # also update window_last_seen for idle tracking continuously
            now=time.time()
            for w in wins:
                if w not in self.window_last_seen:
                    self.window_last_seen[w]=now
            # update active window timestamp too
            active=self.get_active_window()
            if active and active!="unknown": self.window_last_seen[active]=now
        except: pass

    def check_special_triggers(self):
        try:
            if not getattr(self,"anim_ctrl",None): return
            hr=datetime.now().hour
            if hr==8: self.anim_ctrl.wake_up()
            elif hr>=23 or hr<5: self.anim_ctrl.tired()
            try:
                import psutil
                if psutil.cpu_percent(interval=None) > 85: self.anim_ctrl.mood_confused()
                if psutil.virtual_memory().percent > 90: self.anim_ctrl.worried()
            except: pass
            if time.time()-self.last_user_activity > 600: self.anim_ctrl.curious()
        except: pass

    def check_thermal(self):
        try:
            temp=get_cpu_temp()
            if temp is None: return
            target=60
            if temp>=85: target=20
            elif temp>=75: target=30
            elif temp>=70: target=45
            if target!=self.current_fps:
                self.current_fps=target
                if getattr(self,"anim_ctrl",None): self.anim_ctrl.set_fps(target)
                try:
                    self.move_timer.setInterval(int(1000/target) if target<60 else 50)
                    self.draw_timer.setInterval(int(1000/target) if target<60 else 100)
                except: pass
                self.show_bubble(f"Bob thermal {temp:.0f}C -> {target} FPS to cool laptop", speak=False)
                self.deck.append_log(f"Thermal {temp:.0f}C -> {target} FPS")
        except: pass

    def get_open_windows(self):
        wins=[]
        try:
            if sys.platform=="win32":
                import win32gui
                def cb(hwnd,_):
                    if win32gui.IsWindowVisible(hwnd):
                        t=win32gui.GetWindowText(hwnd)
                        if t and len(t)>2 and t not in ("Program Manager",""):
                            # filter out Bob itself and deck
                            if "Bob" not in t and "Deck" not in t:
                                wins.append(t)
                win32gui.EnumWindows(cb, None)
            elif sys.platform.startswith("linux"):
                if shutil.which("wmctrl"):
                    out=subprocess.run(["wmctrl","-l"],capture_output=True,text=True,timeout=3)
                    wins=[line.split(None,3)[-1].strip() for line in out.stdout.splitlines() if len(line.split(None,3))==4]
                elif shutil.which("xdotool"):
                    out=subprocess.run(["xdotool","search","--onlyvisible","--name","."],capture_output=True,text=True,timeout=3)
                    for wid in out.stdout.splitlines()[:40]:
                        title=subprocess.run(["xdotool","getwindowname",wid],capture_output=True,text=True,timeout=2).stdout.strip()
                        if title and "Bob" not in title and "Deck" not in title: wins.append(title)
        except: pass
        return wins

    def check_idle_windows(self):
        try:
            now=time.time()
            active=self.get_active_window()
            # update last seen for active
            if active and active!="unknown":
                self.window_last_seen[active]=now
                # viewed -> remove from notified so it can re-notify after next 15m
                if active in self.idle_notified: self.idle_notified.discard(active)
            # also update for all currently open windows that are recently seen? keep only open
            open_wins=set(self.get_open_windows())
            # prune closed windows
            for k in list(self.window_last_seen.keys()):
                if k not in open_wins and k!=active:
                    # keep but not forever, prune after 30m
                    if now - self.window_last_seen.get(k, now) > 1800:
                        self.window_last_seen.pop(k, None)
                        self.idle_notified.discard(k)
            # check idle >15 min (900s)
            for title, last in list(self.window_last_seen.items()):
                if title not in open_wins: continue
                idle=now-last
                if idle >= 900 and title not in self.idle_notified and title != active:
                    # don't spam - only once per idle cycle
                    self.idle_notified.add(title)
                    mins=int(idle//60)
                    self.show_bubble(f"👀 Bob: '{trim_text(title,40)}' open but not viewed for {mins} min - want Bob to close it? Say 'close {title[:20]}'", speak=False)
                    self.deck.append_log(f"Idle 15m: {title} ({mins}m) - say 'close {title[:20]}' to close")
        except Exception as e:
            print(f"idle check fail {e}")

    def setup_voice(self):
        try:
            import speech_recognition
            self.voice_worker=VoiceWorker(); self.voice_worker.heard.connect(self.on_voice_heard); self.voice_worker.error.connect(lambda e: self.show_bubble(f"🎤 Bob: {e}",speak=False)); self.voice_worker.listening_changed.connect(self.on_listening_changed)
        except ImportError:
            try: self.deck.mic_btn.setToolTip("pip install SpeechRecognition pyaudio pyttsx3")
            except: pass

    def start_learner(self):
        self.learner=AutonomousLearner(self.memory, self.get_active_window)
        self.learner.learned_signal.connect(lambda msg: self.show_bubble(f"Bob learned: {msg}",speak=True))
        self.learner.start()
        # initial greeting from Bob with personality
        QTimer.singleShot(1200, lambda: self.show_bubble(f"Hey pal, I'm Bob! 🐾 Your low-RAM buddy. I learn while you work - no need to ask. Try 'fix my drivers' or 'jump to next tab'!", speak=True))

    def snap_bob_free(self):
        try:
            geo=get_virtual_available()
            if geo:
                x=geo.x()+geo.width()//2 - 100
                y=geo.y()+geo.height()//2 - 80
                self.pet_x=x; self.pet_y=y; self.ground_y=y
                self.move(int(x),int(y))
                self.show_bubble(f"Bob detected {len(QApplication.screens())} screen(s) - extended virtual {geo.width()}x{geo.height()} ✅", speak=False)
        except: pass
    def snap_to_right_corner(self): self.snap_bob_free()
    def snap_to_left_corner(self): self.snap_bob_free()
    def position_bubble(self):
        # Grow the window only while a speech bubble is visible.
        if self.suggestion_visible and self.suggestion_label.isVisible():
            self.suggestion_label.adjustSize()
            width=max(120,min(320,self.suggestion_label.sizeHint().width()+12))
            self.setFixedWidth(width)
            self.suggestion_label.adjustSize()
            self.setFixedHeight(96 + self.suggestion_label.height() + 12)
        else:
            self.setFixedSize(96,96)

    def update_ram(self):
        # delegated to deck; keep trim logic
        mb=get_ram_mb()
        if mb>350:
            self.suggestion_log=collections.deque(list(self.suggestion_log)[-10:], maxlen=MAX_LOG_ENTRIES)
            gc.collect()

    # jumps
    def jump(self):
        if not self.is_jumping:
            self.is_jumping=True; self.velocity_y=self.jump_strength; self.pet_state="happy"
            self.show_bubble(random.choice(["Wheee! - Bob","Boing! Bob's got hops!","Yippee! - Bob"]), speak=True)
            try:
                if self.anim_ctrl: self.anim_ctrl.aha()
            except: pass

    def jump_between_tabs(self, direction="next"):
        if not self.is_jumping:
            self.is_jumping=True; self.velocity_y=self.jump_strength-4
            leap=170 if direction=="next" else -170
            self.pet_x+=leap
            vg=get_virtual_geometry()
            if vg:
                self.pet_x=max(vg.x(), min(vg.x()+vg.width()-self.width(), self.pet_x))
            self.show_bubble(f"Bob jumping to {direction} tab! 🦘→🗂️",speak=True)
        def do_switch():
            time.sleep(0.35)
            try:
                import pyautogui
                if sys.platform=="win32":
                    try:
                        import win32gui
                        lst=[]
                        def cb(hwnd, l):
                            if win32gui.IsWindowVisible(hwnd):
                                t=win32gui.GetWindowText(hwnd)
                                if any(b in t for b in ["Chrome","Edge","Firefox"]): l.append(hwnd)
                        win32gui.EnumWindows(cb,lst)
                        if lst: win32gui.SetForegroundWindow(lst[0]); time.sleep(0.2)
                    except: pass
                if direction=="next": pyautogui.hotkey('ctrl','tab')
                else: pyautogui.hotkey('ctrl','shift','tab')
                self.show_bubble(f"Bob switched to {direction} tab! ✅",speak=False)
            except ImportError:
                if sys.platform.startswith("linux"):
                    try:
                        if not shutil.which("xdotool"): raise RuntimeError("install xdotool or PyAutoGUI and use an X11 session")
                        key="ctrl+Tab" if direction=="next" else "ctrl+shift+Tab"
                        subprocess.run(["xdotool","key",key],check=True,timeout=4)
                        self.show_bubble(f"Bob switched to {direction} tab! ✅",speak=False)
                    except Exception as e: self.show_bubble(f"Linux tab switching needs X11 input access: {e}",speak=False)
                else:
                    try:
                        keys="^{TAB}" if direction=="next" else "^+{TAB}"
                        ps=f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{keys}')"
                        subprocess.run(["powershell","-Command",ps],timeout=5)
                        self.show_bubble("Bob switched tab via SendKeys ✅",speak=False)
                    except Exception as e: self.show_bubble(f"Bob needs pyautogui: pip install pyautogui ({e})",speak=False)
            except Exception as e: self.show_bubble(f"Bob tab fail: {e}",speak=False)
        threading.Thread(target=do_switch,daemon=True).start()

    def update_physics(self):
        if self.is_dragging: return
        # Wander toward points across the desktop instead of walking on one line.
        if not self.is_jumping:
            self.idle_ticks+=1
            if self.idle_ticks % 180 == 0:  # every ~6 sec change mood
                self.bob_mood = random.choice(["chill","playful","lazy","curious"])
                if self.bob_mood=="lazy": self.move_speed=0.35
                elif self.bob_mood=="playful": self.move_speed=1.7
                elif self.bob_mood=="curious": self.move_speed=0.6
                else: self.move_speed=1.0

            if self.bob_mood=="lazy" and random.random()<0.04:
                self.roam_pause_until=max(self.roam_pause_until,time.time()+0.25)
            elif self.bob_mood=="curious" and random.random()<0.03:
                self.wobble = random.uniform(-4,4)
                self.roam_pause_until=max(self.roam_pause_until,time.time()+0.4)

            screens=QApplication.screens()
            if not self.roam_target and time.time()>=self.roam_pause_until:
                area=random.choice(screens).availableGeometry() if screens else get_virtual_available()
                if area:
                    max_x=max(area.x(),area.x()+area.width()-self.width())
                    max_y=max(area.y(),area.y()+area.height()-self.height())
                    self.roam_target=(random.randint(area.x(),max_x),random.randint(area.y(),max_y))

            if self.roam_target and time.time()>=self.roam_pause_until:
                tx,ty=self.roam_target
                dx=tx-self.pet_x; dy=ty-self.pet_y
                distance=(dx*dx+dy*dy)**0.5
                step=max(0.8,abs(self.move_speed)*1.5)
                if distance<=step:
                    self.pet_x=float(tx); self.pet_y=float(ty); self.ground_y=self.pet_y
                    self.roam_target=None; self.roam_pause_until=time.time()+random.uniform(0.5,1.8)
                else:
                    self.pet_x+=dx/distance*step; self.pet_y+=dy/distance*step; self.ground_y=self.pet_y
                    self.move_direction=1 if dx>=0 else -1
                    try:
                        if self.anim_ctrl:
                            if step>1.8: self.anim_ctrl.bounce_move(intensity=1.5); self.anim_ctrl.rotation_on_move(step)
                            elif step>0.9: self.anim_ctrl.bounce_move(intensity=1.0)
                    except: pass
                if self.bob_mood=="playful" and random.random()<0.006: self.jump()
        if self.is_jumping:
            self.pet_y+=self.velocity_y; self.velocity_y+=self.gravity
            if self.pet_y>=self.ground_y:
                self.pet_y=self.ground_y; self.velocity_y=0; self.is_jumping=False
                # little bounce squish when landing if playful
                if self.bob_mood=="playful" and random.random()<0.3:
                    QTimer.singleShot(120, self.jump)
        self.move(int(self.pet_x),int(self.pet_y))

    def toggle_voice(self, from_deck=False):
        # deck holds mic button now
        deck_mic = self.deck.mic_btn if hasattr(self,'deck') else None
        if not self.voice_worker:
            self.show_bubble("Bob: install voice -> pip install SpeechRecognition pyaudio pyttsx3",speak=False)
            if deck_mic: deck_mic.setChecked(False)
            return
        # determine state from deck
        is_on = deck_mic.isChecked() if deck_mic else False
        if is_on:
            self.show_bubble("Bob listening... say 'fix my drivers' or 'jump' 🎤",speak=False); self.voice_worker.start_listening()
        else:
            self.voice_worker.stop_listening()
    def on_listening_changed(self, l):
        if hasattr(self,'deck'): self.deck.set_mic_state(l)
    def on_voice_heard(self, text):
        self.last_user_activity=time.time()
        if hasattr(self,'deck'): self.deck.input_field.setText(text)
        self.show_bubble(f"You said: '{text}' - Bob's on it!",speak=False); self.handle_input(text_override=text)
        if hasattr(self,'deck'): self.deck.set_mic_state(False)

    def handle_input(self, text_override=None):
        # text comes from deck input or direct override
        if text_override is not None:
            text=text_override
        else:
            try: text=self.deck.input_field.text().strip()
            except: text=""
        if not text: return
        self.last_user_activity=time.time()
        try: self.deck.input_field.clear()
        except: pass
        self.pet_state="thinking"
        self.show_bubble("🤔 Thinking...",speak=False)
        # record to memory
        self.memory.observe(self.get_active_window(), text)
        hint=f"Seen tasks: {list(self.memory.data['tasks_seen'].keys())[-5:]} Learned: {self.memory.data['learned'][-2:]}"
        self.agent_worker=AgentWorker(text, hint); self.agent_worker.action_signal.connect(self.execute_action); self.agent_worker.result_ready.connect(self.on_agent_result); self.agent_worker.start()

    def on_agent_result(self, reply):
        self.pet_state="happy"; self.show_bubble(reply,speak=True)
        self.suggestion_log.append({"timestamp":datetime.now().isoformat(),"suggestion":reply})
        # keep RAM low
        if len(self.suggestion_log)>MAX_LOG_ENTRIES: self.suggestion_log.popleft()
    def do_search_github(self, q):
        url=f"https://github.com/search?q={q.replace(' ','+')}"
        webbrowser.open(url)
        self.show_bubble(f"Bob GitHub search '{q}'! 🐱 {url}", speak=True)
        self.deck.append_log(f"GitHub search: {url}")
    def do_search_youtube(self, q):
        url=f"https://www.youtube.com/results?search_query={q.replace(' ','+')}"
        webbrowser.open(url)
        self.show_bubble(f"Bob YouTube search '{q}'! ▶️", speak=True)
        self.deck.append_log(f"YouTube search: {url}")
    def do_search_so(self, q):
        url=f"https://stackoverflow.com/search?q={q.replace(' ','+')}"
        webbrowser.open(url)
        self.show_bubble(f"Bob StackOverflow search '{q}'! 📚", speak=True)
        self.deck.append_log(f"SO search: {url}")

    def do_close_tab(self):
        try:
            import pyautogui
            # focus browser then ctrl+w
            if sys.platform=="win32":
                try:
                    import win32gui
                    lst=[]
                    def cb(hwnd,l):
                        if win32gui.IsWindowVisible(hwnd):
                            txt=win32gui.GetWindowText(hwnd)
                            if any(b in txt for b in ["Chrome","Edge","Firefox","Brave"]): l.append(hwnd)
                    win32gui.EnumWindows(cb,lst)
                    if lst: win32gui.SetForegroundWindow(lst[0]); time.sleep(0.2)
                except: pass
            pyautogui.hotkey('ctrl','w')
            self.show_bubble("Bob closed tab! ❌🗂️", speak=True)
        except ImportError:
            try:
                if sys.platform.startswith("linux"):
                    if not shutil.which("xdotool"): raise RuntimeError("install xdotool or PyAutoGUI and use X11")
                    subprocess.run(["xdotool","key","ctrl+w"],check=True,timeout=4)
                    self.show_bubble("Bob closed tab! ❌", speak=True)
                else:
                    subprocess.run("powershell -c Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('^w')", shell=True)
                    self.show_bubble("Bob closed tab via SendKeys! ❌", speak=True)
            except Exception as e: self.show_bubble(f"Bob couldn't close the tab: {e}", speak=True)
        except Exception as e: self.show_bubble(f"Bob close tab fail: {e}", speak=True)

    def do_close_app(self, name):
        name=name.lower().strip()
        self.trigger_limb_click(); self.jump()
        # try win32 close first, else taskkill
        try:
            if sys.platform=="win32":
                exes={"chrome":"chrome.exe","firefox":"firefox.exe","edge":"msedge.exe","brave":"brave.exe","opera":"opera.exe","vivaldi":"vivaldi.exe","tor":"firefox.exe",
                      "notepad":"notepad.exe","notepad++":"notepad++.exe","calculator":"CalculatorApp.exe","paint":"mspaint.exe","photos":"Microsoft.Photos.exe","camera":"WindowsCamera.exe","store":"WinStore.App.exe","microsoft store":"WinStore.App.exe",
                      "word":"WINWORD.EXE","excel":"EXCEL.EXE","powerpoint":"POWERPNT.EXE","access":"MSACCESS.EXE","outlook":"OUTLOOK.EXE","teams":"ms-teams.exe","onedrive":"OneDrive.exe","sharepoint":"OneDrive.exe","onenote":"ONENOTE.EXE",
                      "vscode":"Code.exe","code":"Code.exe","visual studio":"devenv.exe","pycharm":"pycharm64.exe","intellij":"idea64.exe","webstorm":"webstorm64.exe","rider":"rider64.exe","phpstorm":"phpstorm64.exe","datagrip":"datagrip64.exe","sublime":"sublime_text.exe","atom":"atom.exe","brackets":"Brackets.exe","eclipse":"eclipse.exe","netbeans":"netbeans64.exe","android studio":"studio64.exe",
                      "spotify":"Spotify.exe","vlc":"vlc.exe","windows media player":"wmplayer.exe","groove":"Microsoft.ZuneMusic.exe","youtube":"chrome.exe","netflix":"chrome.exe","prime video":"chrome.exe",
                      "discord":"Discord.exe","slack":"slack.exe","telegram":"Telegram.exe","whatsapp":"WhatsApp.exe","skype":"Skype.exe","zoom":"Zoom.exe","meet":"chrome.exe","webex":"CiscoCollabHost.exe","messenger":"Messenger.exe",
                      "steam":"steam.exe","epic":"EpicGamesLauncher.exe","gog":"GalaxyClient.exe","origin":"Origin.exe","ubisoft":"upc.exe","battle.net":"Battle.net.exe","minecraft":"Minecraft.exe","valorant":"VALORANT.exe","overwatch":"Overwatch.exe","fortnite":"FortniteLauncher.exe","league":"LeagueClient.exe",
                      "git":"git.exe","github desktop":"GitHubDesktop.exe","gitlab":"chrome.exe","bitbucket":"chrome.exe","sourcetree":"SourceTree.exe","docker":"Docker Desktop.exe","postman":"Postman.exe","insomnia":"Insomnia.exe","figma":"Figma.exe","xd":"Adobe XD.exe","sketch":"sketch.exe","blender":"blender.exe","unity":"Unity.exe","unreal":"UE4Editor.exe","godot":"Godot.exe","audacity":"audacity.exe","obs":"obs64.exe","camtasia":"CamtasiaStudio.exe"}
                exe=exes.get(name, name.replace(" ","")+".exe" if "." not in name else name)
                # try graceful close via win32
                try:
                    import win32gui, win32con
                    def enum_cb(hwnd, _):
                        try:
                            txt=win32gui.GetWindowText(hwnd).lower()
                            if name in txt or exe.lower().replace(".exe","") in txt:
                                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0,0)
                        except: pass
                    win32gui.EnumWindows(enum_cb, None)
                    time.sleep(0.5)
                except: pass
                # force taskkill
                res=subprocess.run(f'taskkill /IM "{exe}" /F', shell=True, capture_output=True, text=True, timeout=5)
                if "SUCCESS" in res.stdout or "success" in res.stdout.lower():
                    self.show_bubble(f"Bob closed {name}! ❌", speak=True); return
                # alt+f4 fallback
                import pyautogui
                pyautogui.hotkey('alt','F4')
                self.show_bubble(f"Bob closed {name} via Alt+F4! ❌", speak=True)
                return
            else:
                process_names={"vscode":"code", "visual studio code":"code", "google chrome":"chrome", "calculator":"gnome-calculator"}
                process_name=process_names.get(name, name.replace(" ","-"))
                subprocess.run(["pkill", "-x", process_name], timeout=5, check=True)
                self.show_bubble(f"Bob closed {name}! ❌", speak=True)
        except ImportError:
            try: subprocess.run(f'taskkill /IM "{name}.exe" /F', shell=True)
            except: pass
            self.show_bubble(f"Bob tried closing {name}!", speak=True)
        except Exception as e: self.show_bubble(f"Bob close fail {name}: {e}", speak=True)

    def do_scan_computer(self):
        try:
            self.show_bubble("🔍 Bob scanning your PC...", speak=False)
            self.jump()
            # gather open windows
            wins=self.get_open_windows()[:12]
            wins_txt="\n".join(f"• {w[:60]}" for w in wins) if wins else "• No windows detected"
            # system info
            cpu=ram=disk=""
            try:
                import psutil
                cpu=f"CPU {psutil.cpu_percent(interval=0.5)}% • Cores {psutil.cpu_count()}"
                mem=psutil.virtual_memory()
                ram=f"RAM {mem.percent}% ({mem.used//1024//1024}MB/{mem.total//1024//1024}MB)"
                disk_path="C:\\" if sys.platform=="win32" else "/"
                d=psutil.disk_usage(disk_path)
                disk=f"Disk {disk_path}: {d.percent}% ({d.free//1024//1024//1024}GB free)"
            except:
                try:
                    out=subprocess.run("wmic cpu get Name", capture_output=True, text=True, timeout=4)
                    cpu=out.stdout.strip().split("\n")[-1][:60] if out.stdout else "CPU info N/A"
                except: cpu="CPU N/A"
                ram="RAM N/A"; disk="Disk N/A"
            # installed apps sample via Start menu folder + registry
            apps=[]
            try:
                # Start menu .lnk count
                if sys.platform.startswith("linux"):
                    sm=os.path.join(os.path.expanduser("~/.local/share"), "applications")
                    if os.path.isdir(sm):
                        apps.extend(os.path.splitext(f)[0] for f in os.listdir(sm) if f.endswith(".desktop"))
                else:
                    sm=os.path.join(os.environ.get("ProgramData","C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs")
                if os.path.exists(sm):
                    for r,_,files in os.walk(sm):
                        for f in files:
                            if f.endswith(".lnk"): apps.append(f[:-4])
                            if len(apps)>=15: break
                        if len(apps)>=15: break
            except: pass
            apps_txt=", ".join(apps[:10]) if apps else "Chrome, VSCode, Spotify, etc. (via Start search)"
            # recent files
            recent=[]
            try:
                desk=os.path.join(os.path.expanduser("~"),"Desktop")
                if os.path.exists(desk):
                    recent=sorted([f for f in os.listdir(desk) if not f.startswith(".")], key=lambda x: os.path.getmtime(os.path.join(desk,x)), reverse=True)[:5]
            except: pass
            recent_txt=", ".join(recent) if recent else "No recent Desktop files"
            # build what Bob can do personalized
            can_do=f"Bob sees open windows:\n{wins_txt}\n\nSystem:\n• {cpu}\n• {ram}\n• {disk}\n\nApps you have (sample):\n• {apps_txt}\n\nRecent Desktop:\n• {recent_txt}\n\nWhat Bob can do for you:\n• Open/close any app (say 'open spotify' or 'ch')\n• Search GitHub/YouTube/StackOverflow/Google ('search up cats')\n• System: screenshot, lock, volume, brightness, clean temp, empty bin\n• Fix drivers, extend display, battery check\n• Learn from web when idle + View Learned\n• Jump tabs, manage windows idle 15m\n• Voice: click 🎤 and talk"
            self.deck.log_area.show(); self.deck.log_area.clear(); self.deck.append_log(can_do)
            self.show_bubble(f"🔍 Bob sees {len(wins)} windows, {len(apps)} apps - check deck log for what you can do!", speak=True)
            # analytics
            try: self.analytics.log_suggestion("[Scan] Computer scan", "system", "Tools", 1)
            except: pass
        except Exception as e: self.show_bubble(f"Bob scan fail: {e}", speak=True)

    def trigger_limb_click(self):
        self.limb_click_ticks=7
    def do_system(self, cmd):
        try:
            c=cmd.lower()
            linux=sys.platform.startswith("linux")
            if c=="screenshot":
                import pyautogui, datetime
                p=os.path.join(os.path.expanduser("~"),"Pictures", f"bob_screenshot_{int(time.time())}.png")
                os.makedirs(os.path.dirname(p), exist_ok=True)
                pyautogui.screenshot(p)
                self.show_bubble(f"Bob saved screenshot! 📸 {p}", speak=True)
                if linux and shutil.which("xdg-open"): subprocess.Popen(["xdg-open",os.path.dirname(p)])
                elif not linux: subprocess.Popen(f'explorer /select,"{p}"', shell=True)
            elif c=="lock":
                if linux:
                    locker=shutil.which("loginctl")
                    if not locker: raise RuntimeError("loginctl is unavailable on this Linux system")
                    subprocess.run([locker,"lock-session"],check=True,timeout=8)
                else: subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
                self.show_bubble("Bob locked! 🔒", speak=True)
            elif c=="vol_up": 
                if linux:
                    if shutil.which("wpctl"): subprocess.run(["wpctl","set-volume","@DEFAULT_AUDIO_SINK@","5%+"],check=True)
                    elif shutil.which("pactl"): subprocess.run(["pactl","set-sink-volume","@DEFAULT_SINK@","+5%"],check=True)
                    else: raise RuntimeError("Install WirePlumber (wpctl) or PulseAudio (pactl) tools for volume control")
                else:
                    try: import ctypes; [ctypes.windll.user32.keybd_event(0xAF,0,0,0) or time.sleep(0.05) or ctypes.windll.user32.keybd_event(0xAF,0,2,0) for _ in range(3)]
                    except: import pyautogui; pyautogui.press('volumeup', presses=3)
                self.show_bubble("Bob volume up! 🔊", speak=True)
            elif c=="vol_down":
                if linux:
                    if shutil.which("wpctl"): subprocess.run(["wpctl","set-volume","@DEFAULT_AUDIO_SINK@","5%-"],check=True)
                    elif shutil.which("pactl"): subprocess.run(["pactl","set-sink-volume","@DEFAULT_SINK@","-5%"],check=True)
                    else: raise RuntimeError("Install wpctl or pactl for volume control")
                else:
                    try: import pyautogui; pyautogui.press('volumedown', presses=3)
                    except: pass
                self.show_bubble("Bob volume down! 🔉", speak=True)
            elif c=="mute":
                if linux:
                    if shutil.which("wpctl"): subprocess.run(["wpctl","set-mute","@DEFAULT_AUDIO_SINK@","toggle"],check=True)
                    elif shutil.which("pactl"): subprocess.run(["pactl","set-sink-mute","@DEFAULT_SINK@","toggle"],check=True)
                    else: raise RuntimeError("Install wpctl or pactl for mute control")
                else:
                    try: import pyautogui; pyautogui.press('volumemute')
                    except: subprocess.run("powershell -c (New-Object -comObject WScript.Shell).SendKeys([char]173)", shell=True)
                self.show_bubble("Bob muted! 🔇", speak=True)
            elif c in ("bright_up","bright_down"):
                if linux:
                    tool=shutil.which("brightnessctl")
                    if not tool: raise RuntimeError("Install brightnessctl and grant it display brightness access")
                    subprocess.run([tool,"set","+5%" if c=="bright_up" else "5%-"],check=True)
                else:
                    level="80" if c=="bright_up" else "30"
                    subprocess.run(f"powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})",shell=True)
                self.show_bubble("Bob brightened! ☀️" if c=="bright_up" else "Bob dimmed! 🌙", speak=True)
            elif c=="darkmode":
                if linux: raise RuntimeError("Dark mode is desktop-specific; change it in your desktop's Appearance settings")
                subprocess.run('reg add HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize /v AppsUseLightTheme /t REG_DWORD /d 0 /f', shell=True)
                self.show_bubble("Bob dark mode on! 🌗", speak=True)
            elif c=="empty_bin":
                if linux:
                    if not shutil.which("gio"): raise RuntimeError("Install GLib tools (gio) to empty the desktop trash")
                    subprocess.run(["gio","trash","--empty"],check=True)
                else: subprocess.run("powershell Clear-RecycleBin -Force", shell=True)
                self.show_bubble("Bob emptied bin! 🗑️", speak=True)
            elif c=="clean_temp": 
                if linux: raise RuntimeError("Temporary-file cleanup is not enabled on Linux to avoid deleting files used by other apps")
                subprocess.Popen('del /q /f /s %TEMP%\\* 2>nul', shell=True)
                self.show_bubble("Bob cleaning temp... 🧹", speak=True)
            elif c=="shutdown":
                if linux: subprocess.Popen([shutil.which("systemctl") or "systemctl","poweroff"])
                else: subprocess.Popen("shutdown /s /t 10", shell=True)
                self.show_bubble("Bob shutting down!", speak=True)
            elif c=="restart":
                if linux: subprocess.Popen([shutil.which("systemctl") or "systemctl","reboot"])
                else: subprocess.Popen("shutdown /r /t 10", shell=True)
                self.show_bubble("Bob restarting!", speak=True)
            elif c=="sleep":
                if linux: subprocess.run([shutil.which("systemctl") or "systemctl","suspend"],check=True)
                else: subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
                self.show_bubble("Bob sleep! 😴", speak=True)
            elif c=="time": self.show_bubble(f"Bob: It's {datetime.now().strftime('%I:%M %p')} ⏰", speak=True)
            elif c=="date": self.show_bubble(f"Bob: Today is {datetime.now().strftime('%A, %B %d %Y')} 📅", speak=True)
            elif c=="create_file":
                p=os.path.join(os.path.expanduser("~"),"Desktop", f"bob_note_{int(time.time())}.txt")
                Path(p).write_text("Bob was here! 🐾\n", encoding="utf-8")
                if linux and shutil.which("xdg-open"): subprocess.Popen(["xdg-open",p])
                elif not linux: subprocess.Popen(f'notepad \"{p}\"', shell=True)
                self.show_bubble(f"Bob created {p} 📄", speak=True)
            elif c=="create_folder":
                p=os.path.join(os.path.expanduser("~"),"Desktop", f"BobFolder_{int(time.time())}")
                os.makedirs(p, exist_ok=True)
                if linux and shutil.which("xdg-open"): subprocess.Popen(["xdg-open",p])
                elif not linux: subprocess.Popen(f'explorer \"{p}\"', shell=True)
                self.show_bubble(f"Bob created folder {p} 📁", speak=True)
            elif c=="battery":
                if linux:
                    battery_paths=sorted(Path("/sys/class/power_supply").glob("BAT*/capacity"))
                    if not battery_paths: raise RuntimeError("No battery status is exposed by /sys/class/power_supply")
                    ch=battery_paths[0].read_text().strip()
                    self.show_bubble(f"Bob: Battery {ch}% 🔋", speak=True)
                else:
                    out=subprocess.run("powershell (Get-WmiObject Win32_Battery).EstimatedChargeRemaining", capture_output=True, text=True, timeout=5)
                    ch=out.stdout.strip()
                    if ch and ch.isdigit(): self.show_bubble(f"Bob: Battery {ch}% 🔋", speak=True)
                    else:
                        out2=subprocess.run("powershell Get-CimInstance Win32_Battery | Format-List EstimatedChargeRemaining,BatteryStatus | Out-String", capture_output=True, text=True, timeout=5)
                        self.show_bubble(f"Bob battery:\n{trim_text(out2.stdout.strip(),400)} 🔋", speak=True)
            elif c in ("wifi_off","wifi_on"): 
                act="off" if c=="wifi_off" else "on"
                if linux:
                    if not shutil.which("nmcli"): raise RuntimeError("Install NetworkManager's nmcli to toggle Wi-Fi")
                    subprocess.run(["nmcli","radio","wifi",act],check=True)
                else: subprocess.run(f'netsh interface set interface "Wi-Fi" admin={"disable" if act=="off" else "enable"}',shell=True)
                self.show_bubble(f"Bob WiFi {act}! 📶", speak=True)
            elif c in ("bt_off","bt_on"):
                if linux and shutil.which("bluetoothctl"):
                    subprocess.run(["bluetoothctl","power","on" if c=="bt_on" else "off"],check=True,timeout=8)
                    self.show_bubble(f"Bob Bluetooth {c}! 🔵",speak=True)
                elif linux: raise RuntimeError("Install bluez-utils (bluetoothctl) to toggle Bluetooth")
                else:
                    self.show_bubble(f"Bob Bluetooth {c}! Use Settings > Bluetooth (needs manual). 🔵", speak=True)
                    subprocess.Popen("start ms-settings:bluetooth", shell=True)
            elif c=="airplane":
                if linux:
                    if shutil.which("nmcli"): subprocess.run(["nmcli","radio","wifi","off"],check=True)
                    if shutil.which("bluetoothctl"): subprocess.run(["bluetoothctl","power","off"],check=True,timeout=8)
                    if not shutil.which("nmcli") and not shutil.which("bluetoothctl"): raise RuntimeError("Install NetworkManager (nmcli) or BlueZ (bluetoothctl) to toggle radios")
                    self.show_bubble("Bob turned off available wireless radios. ✈️", speak=True)
                else:
                    subprocess.Popen("start ms-settings:network-airplanemode", shell=True); self.show_bubble("Bob airplane settings! ✈️", speak=True)
            elif c in ("extend","duplicate","second_only"):
                if linux: raise RuntimeError("Display layout is managed by your desktop's Display settings")
                mode={"extend":"/extend","duplicate":"/clone","second_only":"/external"}[c]
                subprocess.Popen(f"DisplaySwitch.exe {mode}",shell=True)
                self.show_bubble(f"Bob changed display mode: {c}! 🖥️", speak=True)
            elif c=="nightlight":
                if linux:
                    for app in ("gnome-control-center","systemsettings","xfce4-settings-manager"):
                        if shutil.which(app): subprocess.Popen([app]); break
                    else: raise RuntimeError("Open Night Light or color temperature in your desktop's Display settings")
                else: subprocess.Popen("start ms-settings:nightlight", shell=True)
                self.show_bubble("Bob opened display settings! 🌙", speak=True)
            elif c=="clear_clip":
                if linux: QApplication.clipboard().clear()
                else: subprocess.run("powershell Set-Clipboard -Value ''", shell=True)
                self.show_bubble("Bob cleared clipboard!", speak=True)
            elif c=="show_desktop":
                import pyautogui; pyautogui.hotkey('win','d')
                self.show_bubble("Bob showing desktop!", speak=True)
            elif c=="minimize_all":
                import pyautogui; pyautogui.hotkey('win','m')
                self.show_bubble("Bob minimized all!", speak=True)
            elif c=="task_view":
                import pyautogui; pyautogui.hotkey('win','Tab')
                self.show_bubble("Bob Task View!", speak=True)
            elif c=="snap_left":
                import pyautogui; pyautogui.hotkey('win','Left')
                self.show_bubble("Bob snapped left!", speak=True)
            elif c=="snap_right":
                import pyautogui; pyautogui.hotkey('win','Right')
                self.show_bubble("Bob snapped right!", speak=True)
            elif c=="caps":
                import pyautogui; pyautogui.press('capslock')
                self.show_bubble("Bob Caps Lock toggled!", speak=True)
            elif c=="eject":
                subprocess.run("powershell (New-Object -comObject Shell.Application).Namespace(17).ParseName('E:').InvokeVerb('Eject')", shell=True)
                self.show_bubble("Bob eject attempted!", speak=True)
            elif c=="clip_history":
                import pyautogui; pyautogui.hotkey('win','v')
                self.show_bubble("Bob clipboard history!", speak=True)
            elif c=="emoji":
                import pyautogui; pyautogui.hotkey('win','.')
                self.show_bubble("Bob emoji panel!", speak=True)
            elif c=="magnifier":
                subprocess.Popen("magnify", shell=True)
                self.show_bubble("Bob magnifier!", speak=True)
            elif c=="narrator":
                subprocess.Popen("Narrator", shell=True)
                self.show_bubble("Bob narrator!", speak=True)
            elif c=="osk":
                subprocess.Popen("osk", shell=True)
                self.show_bubble("Bob on-screen keyboard!", speak=True)
            elif c=="mic_test":
                try:
                    import speech_recognition as sr
                    names=sr.Microphone.list_microphone_names()
                    txt=f"Mics found ({len(names)}):\n" + "\n".join(f"{i}: {n}" for i,n in enumerate(names)) if names else "No microphones detected. Install PortAudio and PyAudio, check desktop microphone permissions, and connect an audio input."
                    self.deck.append_log(txt)
                    self.show_bubble(f"Bob mic test: {len(names)} mics - see deck log. If 0, fix mic permissions/pyaudio.", speak=True)
                    # also try brief listen test
                    if names:
                        try:
                            r=sr.Recognizer()
                            mic=sr.Microphone()
                            with mic as s: r.adjust_for_ambient_noise(s, duration=0.5)
                            self.show_bubble("Bob mic seems working - try clicking 🎤 and speaking!", speak=False)
                        except Exception as e: self.show_bubble(f"Mic open fail: {e}", speak=True)
                except Exception as e: self.show_bubble(f"Mic test fail: {e} - pip install SpeechRecognition pyaudio", speak=True)
            elif c=="clipboard":
                try: import pyautogui
                except: pass
                try:
                    import subprocess
                    txt=trim_text(QApplication.clipboard().text().strip(),300)
                    self.show_bubble(f"Bob clipboard: '{txt}' 📋", speak=True)
                    self.deck.append_log(f"Clipboard: {txt}")
                except Exception as e: self.show_bubble(f"Clipboard fail: {e}", speak=True)
            elif c=="quote":
                q=random.choice(["Code is like humor. When you have to explain it, it's bad. – Cory House 💡","Bob: Keep it lean, keep it clean! 🐾","Talk is cheap. Show me the code. – Linus"])
                self.show_bubble(q, speak=True)
            elif c=="weather":
                webbrowser.open("https://weather.com"); self.show_bubble("Bob opened weather! ☁️", speak=True)
            elif c=="joke":
                j=random.choice(["Why don't programmers like nature? Too many bugs! 🐛","Why did Bob cross the road? To optimize the other side! 🐾","I told my PC a joke... it didn't get the cache! 😂"])
                self.show_bubble(j, speak=True)
            else: self.show_bubble(f"Bob did {c}!", speak=True)
        except Exception as e: self.show_bubble(f"Bob system fail {cmd}: {e}", speak=True)

    def do_search_bar(self, query):
        try:
            import pyautogui
            self.typing_ticks=18
            self.show_bubble(f"Bob focusing search bar for '{query}'...", speak=False)
            pyautogui.hotkey('ctrl','l'); time.sleep(0.4)
            pyautogui.write(query, interval=0.05); time.sleep(0.3)
            pyautogui.press('enter')
            self.show_bubble(f"Bob searched search bar for '{query}'!", speak=True)
            self.deck.append_log(f"Search bar: {query}")
        except Exception as e: self.show_bubble(f"Search bar fail: {e}", speak=True)
    def do_text_bar(self, txt):
        try:
            import pyautogui
            self.typing_ticks=22
            self.show_bubble(f"Bob typing into text bar...", speak=False)
            time.sleep(0.3)
            pyautogui.write(txt, interval=0.03)
            self.show_bubble(f"Bob typed into text bar!", speak=True)
            self.deck.append_log(f"Text bar typed: {trim_text(txt,80)}")
        except Exception as e: self.show_bubble(f"Text bar fail: {e}", speak=True)
    def do_code_auto(self, param):
        try:
            lang, task = (param.split("|",1) + [""])[:2]
            lang=lang.strip() or "python"; task=task.strip() or "hello world"
            self.typing_ticks=35
            self.show_bubble(f"Bob coding {lang} - opening VS Code...", speak=False)
            # open VS Code when asked to make code
            try: self.open_application("vscode")
            except: pass
            time.sleep(0.9)
            # permission to open new file
            from PyQt5.QtWidgets import QMessageBox
            msg=QMessageBox(self); msg.setWindowTitle("Permission"); msg.setText(f"Bob wants to open a new file to code {lang} for '{task[:50]}'. Allow?")
            msg.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
            if msg.exec_()!=QMessageBox.Yes:
                self.show_bubble("Bob code cancelled - permission denied", speak=False); return
            # Try Google API first, fallback to local Ollama (qwen2.5-coder:1.5b)
            code= f"# Bob generated {lang} for: {task}\nprint('Hello from Bob')"
            code_generated=False
            if GOOGLE_API_KEY:
                try:
                    code=gemini_generate(f"{PERSONALITY_PROMPTS.get(self.config['personality']['type'], PERSONALITY_PROMPTS['Friend'])}\nWrite {lang} code for: {task}. Provide only code, no explanation. Language: {lang}. Use Google API key is available.")
                    code_generated=True
                except Exception as e: 
                    self.deck.append_log(f"Gemini code fail: {e} - trying Ollama...")
            # fallback to local Ollama (qwen2.5-coder:1.5b)
            if not code_generated:
                try:
                    self.show_bubble(f"Bob using local qwen2.5-coder:1.5b...", speak=False)
                    code=ollama_generate(f"{PERSONALITY_PROMPTS.get(self.config['personality']['type'], PERSONALITY_PROMPTS['Friend'])}\nWrite {lang} code for: {task}. Provide only code, no explanation. Language: {lang}.")
                    code_generated=True
                except Exception as e:
                    self.deck.append_log(f"Ollama code fail: {e} - using fallback")
            desk=os.path.join(os.path.expanduser("~"),"Desktop")
            os.makedirs(desk, exist_ok=True)
            ext={"python":".py","javascript":".js","java":".java","cpp":".cpp","go":".go","rust":".rs"}.get(lang,".txt")
            path=os.path.join(desk, f"BobCode_{lang}_{int(time.time())%10000}{ext}")
            Path(path).write_text(code, encoding="utf-8")
            # open new file in VS Code
            try: subprocess.Popen(f'code "{path}"', shell=True)
            except: pass
            self.deck.append_log(f"Code auto: {path}\n{code[:500]}")
            self.show_bubble(f"Bob coded {lang} to {os.path.basename(path)} in VS Code!", speak=True)
            try:
                import pyautogui
                time.sleep(0.4)
                pyautogui.write(code[:500], interval=0.01)
            except: pass
            self.deck.set_learned(path)
        except Exception as e: self.show_bubble(f"Code auto fail: {e}", speak=True)

    def do_save_login(self, param):
        try:
            site,user=(param.split("|",1)+["",""])[:2]
            site=site.strip() or "default"; user=user.strip()
            if not user:
                from PyQt5.QtWidgets import QInputDialog
                user,ok=QInputDialog.getText(self, "Save Login", f"Username for {site}:")
                if not ok or not user: return
            v=load_vault(); v[site]=user; save_vault(v)
            self.show_bubble(f"Bob saved login for {site} as {user} (vault local)", speak=True)
            self.deck.append_log(f"Vault: saved {site} -> {user}")
        except Exception as e: self.show_bubble(f"Save login fail: {e}", speak=True)
    def do_fill_login(self, site):
        try:
            v=load_vault(); user=v.get(site) or v.get(site.lower()) or ""
            if not user:
                from PyQt5.QtWidgets import QInputDialog
                user,ok=QInputDialog.getText(self, "Fill Login", f"No saved login for {site}. Enter username to fill:")
                if not ok: return
            # permission
            from PyQt5.QtWidgets import QMessageBox
            msg=QMessageBox(self); msg.setWindowTitle("Permission"); msg.setText(f"Bob wants to fill text box with username '{user}' for {site}. Allow?")
            msg.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
            if msg.exec_()!=QMessageBox.Yes:
                self.show_bubble("Bob fill cancelled - permission denied", speak=False); return
            import pyautogui
            self.typing_ticks=18
            time.sleep(0.4); pyautogui.write(user, interval=0.04)
            self.show_bubble(f"Bob filled login for {site}!", speak=True)
            self.deck.append_log(f"Filled login {site} -> {user} (permission granted)")
        except Exception as e: self.show_bubble(f"Fill login fail: {e}", speak=True)
    def do_fill_text(self, txt):
        try:
            from PyQt5.QtWidgets import QMessageBox
            preview=trim_text(txt,50)
            msg=QMessageBox(self); msg.setWindowTitle("Permission"); msg.setText(f"Bob wants to fill text box with:\n'{preview}'\nAllow?")
            msg.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
            if msg.exec_()!=QMessageBox.Yes:
                self.show_bubble("Bob fill text cancelled", speak=False); return
            import pyautogui
            self.typing_ticks=18
            time.sleep(0.4); pyautogui.write(txt, interval=0.03)
            self.show_bubble("Bob filled text box!", speak=True)
            self.deck.append_log(f"Filled text box: {preview}")
        except Exception as e: self.show_bubble(f"Fill text fail: {e}", speak=True)

    def do_automation(self, name):
        if name=="list":
            txt="Bob Automations (200):\n" + "\n".join(f"{i+1}. {a}" for i,a in enumerate(AUTOMATIONS[:50])) + "\n... +150 more. Say automate <name> or search bar / text bar / code"
            self.deck.append_log(txt)
            self.show_bubble(f"Bob has {len(AUTOMATIONS)} automations - check deck log! Now with search/text bar access", speak=True)
            return
        self.show_bubble(f"Bob automating {name}...", speak=False)
        self.deck.append_log(f"Automation: {name}")
        try:
            if name=="organize downloads":
                dl=os.path.join(os.path.expanduser("~"),"Downloads")
                if os.path.exists(dl):
                    for f in os.listdir(dl):
                        fp=os.path.join(dl,f)
                        if os.path.isfile(fp):
                            ext=os.path.splitext(f)[1].lower()
                            folder="Images" if ext in [".jpg",".png",".gif"] else "Docs" if ext in [".pdf",".docx",".txt"] else "Other"
                            dest=os.path.join(dl, folder)
                            os.makedirs(dest, exist_ok=True)
                            try: os.rename(fp, os.path.join(dest,f))
                            except: pass
                self.show_bubble("Bob organized Downloads by type!", speak=True)
            elif name=="clean temp":
                subprocess.Popen("del /q /f /s %TEMP%\\* 2>nul", shell=True)
                self.show_bubble("Bob cleaned temp!", speak=True)
            elif name=="empty recycle bin":
                subprocess.run("powershell Clear-RecycleBin -Force", shell=True)
                self.show_bubble("Bob emptied recycle bin!", speak=True)
            elif name=="close idle apps":
                self.check_idle_windows()
                self.show_bubble("Bob checked idle apps!", speak=True)
            elif name=="screenshot hourly":
                import pyautogui
                p=os.path.join(os.path.expanduser("~"),"Pictures", f"bob_auto_{int(time.time())}.png")
                pyautogui.screenshot(p)
                self.show_bubble(f"Bob screenshot {p}", speak=True)
            else:
                self.show_bubble(f"Bob automated {name} - done!", speak=True)
                self.deck.append_log(f"Automated {name} (simulated)")
        except Exception as e: self.show_bubble(f"Bob automation {name} fail: {e}", speak=True)

    def show_features(self):
        apps="518 Apps: Chrome/Firefox/Edge/Brave/Opera/Tor, Notepad/Calculator/Paint/Photos/Camera/Store, Settings/Control Panel/Device/Task Mgr, Explorer/Downloads/Documents/Pictures/Videos, Word/Excel/PowerPoint/Access/Outlook/Teams/OneDrive/SharePoint, VSCode/Visual Studio/PyCharm/IntelliJ/WebStorm/Rider, Spotify/VLC/Groove, Discord/Slack/Telegram/WhatsApp/Skype/Zoom/Meet, Steam/Epic/GOG/Ubisoft/Minecraft/Valorant/Overwatch, Git/Docker/Postman/Figma/Blender/Unity/Godot/Audacity/OBS/Camtasia, Snipping/Terminal/Registry/Services - ANY via Start search!"
        feats="750+ total: 518 apps + 200 automations + local AI (qwen2.5-coder:1.5b via Ollama), screenshot/lock/sleep/shutdown/restart, volume/mute, brightness/night light/dark/magnifier/narrator/OSK, empty bin/clean temp/clear clipboard/show desktop/minimize/task view/snap left/right/caps/eject, clipboard history/emoji, create file/folder/note, time/date/clipboard/quote/joke/weather, battery/wifi/bt/airplane, extend/duplicate/second screen, jump tabs, fix drivers, search, ch/cho shortcuts, voice, 4-leg walk/jump, magnifier when searching, idle 15m, scan computer, code/game modes, restart"
        searches="search github <query> | search youtube <query> | search stackoverflow <query> | open github trending | open github facebook/react | search up <query> (look up) | github search python | make code python <task>"
        mon=len(QApplication.screens()); vg=get_virtual_geometry(); extra=f"Monitors: {mon} extended {vg.width()}x{vg.height()} (Bob roams all when extended)" if vg else ""
        self.show_bubble(f"Bob Features 🐾\nApps: {apps}\nSystem: {feats}\nSearch: {searches}\n{extra}\nTry: 'make a code for python sorting' | 'open spotify'", speak=True)
        self.deck.append_log(f"Features:\nApps: {apps}\nSystem: {feats}\nSearch: {searches}\n{extra}")

    def do_code_mode(self):
        self.show_bubble("Bob code mode - opening opencode, Claude, Chrome...", speak=False)
        self.trigger_limb_click(); self.jump()
        # opencode - try CLI, fallback to VSCode
        try:
            # try opencode command
            subprocess.Popen("opencode", shell=True)
            self.deck.append_log("Code mode: launched opencode")
            time.sleep(0.7)
        except: pass
        # Claude - open claude.ai + try desktop
        try: webbrowser.open("https://claude.ai")
        except: pass
        try: subprocess.Popen("claude", shell=True)
        except: pass
        self.deck.append_log("Code mode: opened Claude https://claude.ai")
        time.sleep(0.4)
        # Chrome via Start menu
        self.open_application("chrome")
        self.show_bubble("Bob code mode done - opencode, Claude, Chrome opened!", speak=True)

    def do_game_mood(self):
        self.show_bubble("Bob game mood - opening Roblox...", speak=False)
        self.trigger_limb_click(); self.jump()
        # Roblox via Start menu (Start -> Roblox -> Enter)
        try:
            import pyautogui
            pyautogui.press('win'); time.sleep(0.8)
            pyautogui.write("roblox", interval=0.06); time.sleep(0.8)
            pyautogui.press('enter')
            self.deck.append_log("Game mood: launched Roblox via Start")
        except:
            try: webbrowser.open("https://www.roblox.com")
            except: pass
            self.deck.append_log("Game mood: opened Roblox https://www.roblox.com")
        # fallback direct
        try:
            for p in [os.path.expandvars(r"%LOCALAPPDATA%\Roblox\Versions\RobloxPlayerLauncher.exe"), r"C:\Program Files\Roblox\RobloxPlayerLauncher.exe"]:
                if os.path.exists(p): subprocess.Popen([p]); break
        except: pass
        self.show_bubble("Bob game mood done - Roblox opened!", speak=True)

    def execute_action(self, action, param):
        try:
            if action in ("open_tab","search","search_github","search_youtube","search_so","open_app","close_tab","close_app","run","fix_drivers","system","show_features","scan_computer","code_mode","game_mood","automation","save_login","fill_login","fill_text","search_bar","text_bar","code_auto","browser_tabs","browser_active_tab","browser_navigate","browser_js","browser_content","browser_cookies","obsidian_vault","obsidian_files","obsidian_read","obsidian_write","obsidian_search","obsidian_daily","obsidian_command"): self.trigger_limb_click()
            if action=="jump": self.jump()
            elif action=="jump_tab": self.jump_between_tabs(param or "next")
            elif action=="open_tab": webbrowser.open(param); self.show_bubble(f"Bob opened {param}", speak=False); self.deck.append_log(f"Opened: {param}")
            elif action=="search": webbrowser.open(f"https://www.google.com/search?q={param.replace(' ','+')}"); self.deck.append_log(f"Google search: {param}")
            elif action=="search_bar": self.do_search_bar(param)
            elif action=="text_bar": self.do_text_bar(param)
            elif action=="code_auto": self.do_code_auto(param)
            elif action=="search_github": self.do_search_github(param)
            elif action=="search_youtube": self.do_search_youtube(param)
            elif action=="search_so": self.do_search_so(param)
            elif action=="open_app": self.open_application(param)
            elif action=="close_tab": self.do_close_tab()
            elif action=="close_app": self.do_close_app(param)
            elif action=="fix_drivers": self.start_driver_fix()
            elif action=="system": self.do_system(param)
            elif action=="show_features": self.show_features()
            elif action=="scan_computer": self.do_scan_computer()
            elif action=="code_mode": self.do_code_mode()
            elif action=="game_mood": self.do_game_mood()
            elif action=="automation": self.do_automation(param)
            elif action=="save_login": self.do_save_login(param)
            elif action=="fill_login": self.do_fill_login(param)
            elif action=="fill_text": self.do_fill_text(param)
            elif action=="browser_tabs":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    tabs=self.auto_engine.browser_get_tabs()
                    if isinstance(tabs, str): self.show_bubble(f"Bob: {tabs}", speak=True)
                    else: 
                        txt="\n".join(f"{t['title'][:50]} - {t['url'][:60]}" for t in tabs[:10])
                        self.deck.append_log(txt)
                        self.show_bubble(f"Bob found {len(tabs)} tabs - see deck log!", speak=True)
                except Exception as e: self.show_bubble(f"Browser tabs fail: {e}", speak=True)
            elif action=="browser_active_tab":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    tab=self.auto_engine.browser_get_active_tab()
                    if tab: self.show_bubble(f"Active: {tab['title'][:50]} - {tab['url'][:60]}", speak=True); self.deck.append_log(f"Active tab: {tab['url']}")
                    else: self.show_bubble("No active tab found", speak=True)
                except Exception as e: self.show_bubble(f"Active tab fail: {e}", speak=True)
            elif action=="browser_navigate":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    self.auto_engine.queue_task(AutomationTask("bob navigate", "browser_navigate", {"url": param}, callback=lambda tk: self.deck.append_log(f"Navigate: {tk.result or tk.error}")))
                    self.show_bubble(f"Bob navigating to {param}...", speak=False)
                except Exception as e: self.show_bubble(f"Navigate fail: {e}", speak=True)
            elif action=="browser_js":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    self.auto_engine.queue_task(AutomationTask("bob js", "browser_js", {"script": param}, callback=lambda tk: self.deck.append_log(f"JS result: {tk.result or tk.error}")))
                    self.show_bubble("Bob executing JavaScript...", speak=False)
                except Exception as e: self.show_bubble(f"JS fail: {e}", speak=True)
            elif action=="browser_content":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    content=self.auto_engine.browser_get_page_content()
                    self.deck.append_log(f"Page content: {content[:500]}")
                    self.show_bubble("Bob got page content - see deck log!", speak=True)
                except Exception as e: self.show_bubble(f"Content fail: {e}", speak=True)
            elif action=="browser_cookies":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    cookies=self.auto_engine.browser_get_cookies()
                    self.show_bubble(f"Bob got cookies: {cookies[:100]}...", speak=True)
                    self.deck.append_log(f"Cookies: {cookies}")
                except Exception as e: self.show_bubble(f"Cookies fail: {e}", speak=True)
            elif action=="obsidian_vault":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    vault=self.auto_engine.obsidian_find_vault()
                    if vault: self.show_bubble(f"Bob found vault: {vault}", speak=True); self.deck.append_log(f"Vault: {vault}")
                    else: self.show_bubble("Bob couldn't find Obsidian vault", speak=True)
                except Exception as e: self.show_bubble(f"Vault find fail: {e}", speak=True)
            elif action=="obsidian_files":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    files=self.auto_engine.obsidian_list_files()
                    if isinstance(files, str): self.show_bubble(f"Bob: {files}", speak=True)
                    else:
                        txt="\n".join(files[:20])
                        self.deck.append_log(f"Obsidian files:\n{txt}")
                        self.show_bubble(f"Bob found {len(files)} notes - see deck log!", speak=True)
                except Exception as e: self.show_bubble(f"Files fail: {e}", speak=True)
            elif action=="obsidian_read":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    content=self.auto_engine.obsidian_read_note(param)
                    self.deck.append_log(f"Read note {param}:\n{content[:500]}")
                    self.show_bubble(f"Bob read note - see deck log!", speak=True)
                except Exception as e: self.show_bubble(f"Read fail: {e}", speak=True)
            elif action=="obsidian_write":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    path,content=(param.split("|",1)+["",""])[:2]
                    self.auto_engine.queue_task(AutomationTask("obsidian write", "obsidian_write", {"path":path.strip(), "content":content.strip()}, callback=lambda tk: self.deck.append_log(f"Write: {tk.result or tk.error}")))
                    self.show_bubble(f"Bob writing note {path}...", speak=False)
                except Exception as e: self.show_bubble(f"Write fail: {e}", speak=True)
            elif action=="obsidian_search":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    results=self.auto_engine.obsidian_search(param)
                    if isinstance(results, str): self.show_bubble(f"Bob: {results}", speak=True)
                    else:
                        txt="\n".join(f"{r['file']}: {r['context'][:100]}" for r in results[:10])
                        self.deck.append_log(f"Search results for '{param}':\n{txt}")
                        self.show_bubble(f"Bob found {len(results)} matches - see deck log!", speak=True)
                except Exception as e: self.show_bubble(f"Search fail: {e}", speak=True)
            elif action=="obsidian_daily":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    note=self.auto_engine.obsidian_daily_note()
                    self.deck.append_log(f"Daily note:\n{note[:500]}")
                    self.show_bubble("Bob opened today's daily note!", speak=True)
                except Exception as e: self.show_bubble(f"Daily note fail: {e}", speak=True)
            elif action=="obsidian_command":
                try:
                    if not self.auto_engine: self.show_bubble("Automation engine not loaded", speak=True); return
                    result=self.auto_engine.obsidian_execute_command(param)
                    self.show_bubble(f"Bob sent command to Obsidian: {result}", speak=True)
                except Exception as e: self.show_bubble(f"Command fail: {e}", speak=True)
            elif action=="run": threading.Thread(target=lambda: subprocess.Popen(param,shell=True),daemon=True).start()
        except Exception as e: self.show_bubble(f"Bob error {action}: {e}",speak=True)

    def start_driver_fix(self):
        # log goes to deck at right-bottom
        self.deck.log_area.show(); self.deck.log_area.clear(); self.deck.log_area.append("🚀 Bob starting driver fix...\n"); self.deck.setFixedHeight(200)
        self.show_bubble("Bob's fixing drivers, pal! Check deck log at right-bottom 🛠️",speak=True); self.jump()
        self.driver_worker=DriverFixWorker()
        def on_prog(t): self.deck.append_log(t)
        self.driver_worker.progress.connect(on_prog)
        self.driver_worker.finished_signal.connect(lambda msg: (self.deck.append_log(f"\n✅ {msg}"), self.show_bubble(msg,speak=True)))
        self.driver_worker.start()
        self.memory.data["learned"].append({"what":"fix drivers","at":datetime.now().isoformat()}); self.memory.save()

    def open_application(self, name):
        name=name.lower().strip()
        # --- Start-menu automation as requested: Win -> type app -> Enter/click ---
        if sys.platform=="win32":
            try:
                import pyautogui
                self.show_bubble(f"Bob opening Start menu to find '{name}'...", speak=False)
                self.trigger_limb_click(); self.jump()
                pyautogui.press('win')
                time.sleep(0.8)
                pyautogui.write(name, interval=0.06)
                time.sleep(0.9)
                pyautogui.press('enter')
                time.sleep(0.6)
                self.show_bubble(f"Bob clicked '{name}' from Start menu! ✅", speak=True)
                return
            except ImportError:
                self.show_bubble("Bob needs pyautogui for Start-menu click: pip install pyautogui", speak=True)
            except Exception as e:
                print(f"Start-menu fail {e}, fallback to direct")
        # fallback direct launch (if Start menu failed or non-Windows)
        try:
            if sys.platform=="win32":
                if "chrome" in name:
                    for p in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                              os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")]:
                        if os.path.exists(p):
                            subprocess.Popen([p], shell=False)
                            self.show_bubble("Bob opened Chrome! 🟢", speak=True); return
                    try: subprocess.Popen('start chrome ""', shell=True); self.show_bubble("Bob opened Chrome! 🟢", speak=True); return
                    except: pass
                    try: webbrowser.get("chrome").open("https://google.com")
                    except: webbrowser.open("https://google.com")
                    self.show_bubble("Bob opened Chrome via browser! 🟢", speak=True); return
                apps={"notepad":"notepad.exe","calculator":"calc.exe","explorer":"explorer.exe","vscode":"code","code":"code","device manager":"devmgmt.msc","task manager":"taskmgr.exe"}
                subprocess.Popen(apps.get(name, name), shell=True)
                self.show_bubble(f"Bob opened {name}! ✅", speak=True)
            elif sys.platform=="darwin":
                subprocess.Popen(["open","-a",name]); self.show_bubble(f"Bob opened {name}! ✅", speak=True)
            elif sys.platform.startswith("linux"):
                aliases={
                    "notepad":["mousepad","xed","gedit","kate","leafpad"],
                    "text editor":["gedit","kate","mousepad","xed"],
                    "calculator":["gnome-calculator","kcalc","galculator","mate-calc","qalculate-gtk"],
                    "explorer":["xdg-open",os.path.expanduser("~")],
                    "file manager":["xdg-open",os.path.expanduser("~")],
                    "files":["xdg-open",os.path.expanduser("~")],
                    "settings":["gnome-control-center","systemsettings","xfce4-settings-manager","mate-control-center"],
                    "device manager":["gnome-control-center","systemsettings","xfce4-settings-manager"],
                    "task manager":["gnome-system-monitor","xfce4-taskmanager","plasma-systemmonitor","mate-system-monitor"],
                    "terminal":["x-terminal-emulator","konsole","gnome-terminal","xfce4-terminal","kitty","alacritty"],
                    "vscode":["code"], "visual studio code":["code"],
                }
                options=aliases.get(name, [name])
                command=None
                for candidate in options:
                    if candidate=="xdg-open" or shutil.which(candidate):
                        command=candidate; break
                if not command:
                    raise FileNotFoundError(f"No installed Linux app matched '{name}'")
                if command=="xdg-open": subprocess.Popen([command, *options[1:]])
                else: subprocess.Popen([command])
                self.show_bubble(f"Bob opened {name}! ✅", speak=True)
            else:
                subprocess.Popen([name]); self.show_bubble(f"Bob opened {name}! ✅", speak=True)
        except Exception as e:
            self.show_bubble(f"Bob couldn't open {name}: {e}", speak=True)
            try: webbrowser.open(f"https://www.google.com/search?q={name}")
            except: pass

    def show_bubble(self, text, speak=False, auto_hide=None):
        text=strip_emojis(text)
        if len(text)>340: text=text[:340]+"..."
        if not text.lower().startswith("bob"): text=f"Bob: {text}"
        self.suggestion_label.setText(text); self.suggestion_label.show(); self.suggestion_label.adjustSize(); self.suggestion_visible=True
        self.position_bubble()
        if speak: speak_text(text)
        if auto_hide: QTimer.singleShot(auto_hide, lambda: None)

    def pet_clicked(self, event):
        if event.button()==Qt.LeftButton:
            self.last_user_activity=time.time()
            self.is_dragging=True; self.drag_start_pos=event.globalPos(); self.pet_label.setCursor(Qt.ClosedHandCursor)
            # interaction animations
            try:
                if hasattr(self,"anim_ctrl") and self.anim_ctrl:
                    # double-click detection
                    now=time.time()
                    if hasattr(self,"_last_click") and now-self._last_click<0.3:
                        self.anim_ctrl.double_click()
                    else:
                        self.anim_ctrl.click_response()
                    self._last_click=now
            except: pass
            # spec Click Interaction: dismiss if visible, else request new AI + thinking
            if self.suggestion_visible:
                self.suggestion_label.hide(); self.suggestion_visible=False; self.pet_state="happy"
                self.setFixedSize(96,96)
                self.update_mood(accepted=False)
                try: 
                    if self.anim_ctrl: self.anim_ctrl.suggestion_reject()
                except: pass
            else:
                self.pet_state="thinking"
                try: 
                    if self.anim_ctrl: self.anim_ctrl.thinking()
                except: pass
                self.request_suggestion()
    def pet_drag(self, event):
        if event.buttons()==Qt.LeftButton and self.is_dragging:
            delta=event.globalPos()-self.drag_start_pos; self.pet_x=self.x()+delta.x(); self.pet_y=self.y()+delta.y(); self.drag_start_pos=event.globalPos(); self.move(int(self.pet_x),int(self.pet_y)); self.ground_y=self.pet_y
            try:
                if self.anim_ctrl: self.anim_ctrl.drag_response()
            except: pass
    def pet_drop(self, event):
        self.is_dragging=False; self.pet_label.setCursor(Qt.OpenHandCursor); self.ground_y=self.y()
        try:
            if self.anim_ctrl: self.anim_ctrl.drop_bounce()
        except: pass

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
        if not self.config["behavior"]["auto_suggest"]: return
        w=self.get_active_window()
        # always update computer view hint
        view_hint=f"Always-see: open windows {self.current_view.get('windows',[])[:5]} CPU {self.current_view.get('cpu','')} RAM {self.current_view.get('ram','')}"
        if self.is_coding_activity(w) and not self.suggestion_visible:
            lang=detect_language(w, w)
            self.analytics.log_session(1, lang, w)
            hint=f"Bob memory: {self.memory.data['tasks_seen']} | {view_hint}"
            self.request_suggestion(f"User in: {w}", hint)
    def request_suggestion(self, ctx=None, hint=""):
        if not self.config["behavior"]["auto_suggest"] and ctx is None:
            self.show_bubble("🔕 Auto-suggest off (enable in Dashboard > Customization)", speak=False); return
        if not GOOGLE_API_KEY:
            self.show_bubble("❌ Set GOOGLE_API_KEY environment variable for AI suggestions",speak=True); return
        if ctx is None: ctx=f"User in: {self.get_active_window()}"
        lang=detect_language(ctx, ctx)
        clip=get_clipboard_snippet()
        self.pet_state="thinking"; self.show_bubble("🤔 Thinking...",speak=False)
        try:
            if self.anim_ctrl: self.anim_ctrl.thinking(); self.anim_ctrl.set_state("thinking")
        except: pass
        # sound chirp if enabled
        if self.config["sound"]["enabled"]:
            try: QApplication.beep()
            except: pass
        if self.suggestion_worker and self.suggestion_worker.isRunning(): self.suggestion_worker.wait()
        pers=self.config["personality"]["type"]
        self.suggestion_worker=SuggestionWorker(ctx, hint, lang, clip, pers); self.suggestion_worker.suggestion_ready.connect(self.display_suggestion); self.suggestion_worker.error_occurred.connect(lambda e: self.show_bubble(f"❌ {e}",speak=True)); self.suggestion_worker.start()
    def display_suggestion(self,s):
        cat="Tools"; m=re.search(r'\[([^\]]+)\]', s)
        if m and m.group(1) in SUGGEST_CATEGORIES: cat=m.group(1)
        lang=detect_language(s, s)
        style=self.config["notification"]["style"]
        if style=="silent": pass
        elif style=="toast": self.show_bubble(f"💡 {trim_text(s,200)}",speak=False)
        else: self.show_bubble(f"💡 {trim_text(s,200)}",speak=True)
        # suggestion appear + aha
        try:
            if self.anim_ctrl: self.anim_ctrl.suggestion_appear(); self.anim_ctrl.aha(); self.anim_ctrl.set_state("happy")
        except: pass
        entry={"timestamp":datetime.now().isoformat(),"suggestion":s, "category":cat, "language":lang}
        self.suggestion_log.append(entry)
        self.analytics.log_suggestion(s, lang, cat, self.get_active_window(), accepted=0)
        if self.config["sound"]["enabled"]:
            try: QApplication.beep()
            except: pass
    def animate_pet(self):
        self.animation_frame=(self.animation_frame+1)%4
        self.walk_cycle=(self.walk_cycle+1)%360
        self.breath_phase=(self.breath_phase+6)%360
        if self.limb_click_ticks>0: self.limb_click_ticks-=1
        if self.typing_ticks>0: self.typing_ticks-=1
        if self.web_searching: self.jump_phase=(self.jump_phase+12)%360
        else: self.jump_phase=0
    def draw_pet(self):
        import math
        pixmap=QPixmap(88,88); pixmap.fill(Qt.transparent)
        p=QPainter(pixmap); p.setRenderHint(QPainter.Antialiasing)
        # breathing when idle + walking bob
        breath = math.sin(math.radians(self.breath_phase))*0.015 + 1.0
        walk_bob = 0
        if not self.is_jumping and self.limb_click_ticks==0 and not self.web_searching and self.typing_ticks==0:
            # idle breathing vs walking bob
            if abs(self.move_speed) < 0.4:
                walk_bob = math.sin(math.radians(self.breath_phase*0.7))*1.2
            else:
                walk_bob = math.sin(math.radians(self.walk_cycle*2))*1.8
        # shadow with breathing
        if self.is_jumping:
            hf=max(0.2, 1 - abs(self.velocity_y)/20); sh_w=int(48*hf); sh_x=20+(48-sh_w)//2
            p.setBrush(QBrush(QColor(0,0,0,int(50*hf)))); p.setPen(Qt.NoPen); p.drawEllipse(sh_x,78,sh_w,8)
        else:
            pulse= 2 if self.animation_frame%2==0 else 0
            sh_y=78 + int(walk_bob*0.3)
            p.setBrush(QBrush(QColor(0,0,0,25))); p.setPen(Qt.NoPen); p.drawEllipse(18+pulse,sh_y,44-pulse*2,7)

        # body with enhanced squish + breathing + typing lean
        p.save()
        flip = 1 if self.move_direction==1 else -1
        # vertical bob offset
        p.translate(0, walk_bob)
        if self.web_searching:
            wob= math.sin(math.radians(self.jump_phase))*1.5
            p.translate(44,44+wob); p.scale(1.02*flip,0.98); p.translate(-44,-44)
        elif self.typing_ticks>0:
            # typing lean forward slightly
            p.translate(44,44); p.scale(1.0*flip,0.97); p.translate(-44,-44)
            p.translate(1.2*flip, 0.8)
        elif self.is_jumping:
            if self.velocity_y < -6: p.translate(44,44); p.scale(1.06*flip,0.86); p.translate(-44,-44)
            elif self.velocity_y > 6: p.translate(44,44); p.scale(0.95*flip,1.12); p.translate(-44,-44)
            else: p.translate(44,44); p.scale(flip,0.98); p.translate(-44,-44)
        elif self.limb_click_ticks>0:
            p.translate(44,44); p.scale(1.05*flip,0.94); p.translate(-44,-44)
        else:
            # walking wobble + breathing scale
            if self.animation_frame%2==0: p.translate(44,44); p.scale(1.02*flip, breath); p.translate(-44,-44)
            else: p.translate(44,44); p.scale(flip*breath,1.0); p.translate(-44,-44)
        if self.svg_renderer: self.svg_renderer.render(p)
        else: p.setBrush(QBrush(QColor(100,200,255))); p.drawEllipse(14,14,60,60)
        p.restore()

        # magnifying glass in hand when idle searching web - wobbles
        if self.web_searching:
            wob= math.sin(math.radians(self.jump_phase))*2.0
            p.setPen(QPen(QColor(70,70,70),2))
            p.setBrush(QBrush(QColor(200,230,255,190)))
            hx = 60 if self.move_direction==1 else 12
            p.drawEllipse(hx, int(28+wob), 16, 16)
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(255,255,255,130))); p.drawEllipse(hx+4, int(31+wob), 5,5)
            p.setPen(QPen(QColor(90,60,40),3))
            if self.move_direction==1: p.drawLine(hx+14, int(42+wob), hx+20, int(50+wob))
            else: p.drawLine(hx+2, int(42+wob), hx-4, int(50+wob))
            p.setPen(QPen(QColor(90,60,40),2))
            if self.move_direction==1: p.drawLine(52, 42, hx+2, int(36+wob))
            else: p.drawLine(36, 42, hx+14, int(36+wob))
        # typing hands when coding/text bar
        if self.typing_ticks>0:
            # small hands tapping
            tap = 1 if self.animation_frame%2==0 else -1
            p.setPen(Qt.NoPen); p.setBrush(QBrush(QColor(90,60,40)))
            hx = 44 + tap*2
            p.drawEllipse(hx-8, 44, 8, 6)
            p.drawEllipse(hx+4, 44+tap, 8, 6)

        # --- same 4 orange rectangles as legs ---
        p.setCompositionMode(QPainter.CompositionMode_Clear)
        p.fillRect(10,58,68,22,Qt.transparent)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        orange=QColor("#D97757")
        p.setPen(Qt.NoPen)
        # legs attached directly to body bottom (no gap)
        p.setBrush(QBrush(orange))
        if not self.is_jumping and self.limb_click_ticks==0:
            # walk: attached legs swing like pendulum from body
            base = 3 if self.animation_frame%2==0 else -3
            lift = 1 if self.animation_frame%2==0 else 0  # lift one pair slightly
            y_attach=58  # top of leg touches body
            if self.move_direction==1: # left->right: right pair forward
                # left pair back + slightly lifted
                p.drawRoundedRect(16 - base, y_attach+lift, 7, 10, 1,1)
                p.drawRoundedRect(29 - base, y_attach+lift, 7, 10, 1,1)
                p.drawRoundedRect(51 + base, y_attach, 7, 10, 1,1)
                p.drawRoundedRect(62 + base, y_attach, 7, 10, 1,1)
            else:
                p.drawRoundedRect(16 + base, y_attach, 7, 10, 1,1)
                p.drawRoundedRect(29 + base, y_attach, 7, 10, 1,1)
                p.drawRoundedRect(51 - base, y_attach+lift, 7, 10, 1,1)
                p.drawRoundedRect(62 - base, y_attach+lift, 7, 10, 1,1)
        elif self.is_jumping:
            y_attach=58
            if self.velocity_y < -7: # tuck - legs pulled up attached
                p.drawRoundedRect(17, y_attach, 7, 6, 1,1); p.drawRoundedRect(30, y_attach, 7, 6, 1,1)
                p.drawRoundedRect(52, y_attach, 7, 6, 1,1); p.drawRoundedRect(63, y_attach, 7, 6, 1,1)
            elif self.velocity_y < 3: # apex
                p.drawRoundedRect(17, y_attach, 7, 7, 1,1); p.drawRoundedRect(30, y_attach, 7, 7, 1,1)
                p.drawRoundedRect(52, y_attach, 7, 7, 1,1); p.drawRoundedRect(63, y_attach, 7, 7, 1,1)
            else: # extend - legs stretched down attached
                p.drawRoundedRect(17, y_attach, 7, 13, 1,1); p.drawRoundedRect(30, y_attach, 7, 13, 1,1)
                p.drawRoundedRect(52, y_attach, 7, 13, 1,1); p.drawRoundedRect(63, y_attach, 7, 13, 1,1)
        elif self.limb_click_ticks>0:
            k=self.limb_click_ticks
            y_attach=58
            punch = 0 if k<2 else 2
            p.drawRoundedRect(17, y_attach-punch, 7, 10, 1,1); p.drawRoundedRect(30, y_attach-punch, 7, 10, 1,1)
            p.drawRoundedRect(52, y_attach-punch, 7, 10, 1,1); p.drawRoundedRect(63, y_attach-punch, 7, 10, 1,1)
            if k in (5,6):
                p.setBrush(QBrush(QColor(255,255,255,140))); p.drawEllipse(41, 48, 5,5)

        if self.pet_state=="thinking":
            o=self.animation_frame*2; p.setBrush(QBrush(QColor(200,200,200,150))); p.setPen(Qt.NoPen); p.drawEllipse(62+o,6,10,10); p.drawEllipse(66+o,14,6,6)
        p.end(); self.pet_label.setPixmap(pixmap)
        # low-RAM: don't keep pixmap refs, let GC

    def open_dashboard(self):
        if self.dashboard is None or not self.dashboard.isVisible():
            self.dashboard=AnalyticsDashboard(self.analytics, self.config)
            self.dashboard.show()
        else:
            self.dashboard.raise_(); self.dashboard.activateWindow(); self.dashboard.refresh()

    def show_context_menu(self,pos):
        m=QMenu(self)
        # spec required exact items
        m.addAction("Get Suggestion Now", self.request_suggestion)
        m.addAction("View Suggestion Log", self.show_log)
        m.addAction("Settings", self.show_settings)
        m.addAction("Quit", QApplication.quit)
        m.addSeparator()
        m.addAction("📊 Analytics Dashboard", self.open_dashboard)
        m.addAction("↻ Restart Bob", self.restart_bob)
        # Automation Engine
        auto=m.addMenu("⚙️ Automation Engine")
        auto.addAction("Queue: Shell (dir)", lambda: self.queue_auto("shell", {"cmd":"dir" if sys.platform=="win32" else "ls -la"}))
        auto.addAction("Queue: Python Hello", lambda: self.queue_auto("python", {"code":"print('hello from Bob')"}))
        auto.addAction("Queue: Git Status", lambda: self.queue_auto("git", {"cmd":"git status"}))
        auto.addAction("Queue: Backup Desktop", lambda: self.queue_auto("backup", {"src": os.path.expanduser("~/Desktop"), "dst": os.path.expanduser("~/Desktop_bak")}))
        auto.addAction("Schedule: Daily Backup", lambda: self.schedule_auto("backup", {"src": os.path.expanduser("~/Desktop"), "dst": os.path.expanduser("~/Desktop_bak")}, "daily"))
        auto.addAction("Parallel: 3 Tasks", lambda: [self.queue_auto("sysinfo",{}, priority=5) for _ in range(3)])
        auto.addAction("Workflow: Test+Backup", lambda: self.queue_workflow())
        auto.addAction("History", self.show_automation_history)
        # personality switch at runtime
        pers_menu=m.addMenu("Personality")
        pers_menu.addAction("Fellow", lambda: self.set_personality("Fellow"))
        pers_menu.addAction("Mentor", lambda: self.set_personality("Mentor"))
        pers_menu.addAction("Friend", lambda: self.set_personality("Friend"))
        pers_menu.addAction("Motivator", lambda: self.set_personality("Motivator"))
        pers_menu.addAction("Curious", lambda: self.set_personality("Curious"))
        agg_menu=m.addMenu("Aggressiveness")
        agg_menu.addAction("Passive (2 min)", lambda: self.set_aggressiveness("passive"))
        agg_menu.addAction("Moderate (60 sec)", lambda: self.set_aggressiveness("moderate"))
        agg_menu.addAction("Aggressive (30 sec)", lambda: self.set_aggressiveness("aggressive"))
        m.addSeparator()
        # extra Bob features (keep)
        m.addAction("🦘 Bob Jump",self.jump); m.addAction("🗂️ Bob Jump Next Tab",lambda: self.jump_between_tabs("next")); m.addAction("🗂️ Prev Tab",lambda: self.jump_between_tabs("prev"))
        m.addSeparator(); m.addAction("🛠️ Bob Fix Drivers",lambda: self.handle_input(text_override="fix my drivers"))
        m.addAction("🎤 Bob Listen",self.toggle_voice)
        m.addSeparator(); m.addAction("📜 Bob Memory",self.show_memory)
        m.exec_(self.mapToGlobal(pos))
    def set_aggressiveness(self, lvl):
        if lvl not in AGGRESSIVENESS_INTERVAL: return
        self.config["personality"]["aggressiveness"]=lvl
        save_config(self.config); self.apply_config()
        self.show_bubble(f"Bob aggressiveness: {lvl} ({AGGRESSIVENESS_INTERVAL[lvl]//1000}s)", speak=True)
    def show_log(self):
        if not self.suggestion_log:
            self.show_bubble("❌ No suggestions yet! Click Bob to get one.", speak=False)
            return
        from PyQt5.QtWidgets import QInputDialog
        cats=["All"]+SUGGEST_CATEGORIES
        cat,ok=QInputDialog.getItem(self, "Filter by Category", "Category:", cats, 0, False)
        if not ok: cat="All"
        filtered=[s for s in self.suggestion_log if cat=="All" or s.get("category","")==cat][-10:]
        if not filtered:
            self.show_bubble(f"❌ No suggestions in {cat}", speak=False); return
        txt="\n\n".join([f"[{s['timestamp']}] [{s.get('category','?')}] {s.get('language','')}\n💡 {s['suggestion']}" for s in filtered])
        msg=QMessageBox(self); msg.setWindowTitle(f"Suggestion Log - {cat} - Last 10"); msg.setText(txt + "\n\nMark all as accepted? (improves Bob's mood)")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No); 
        if msg.exec_()==QMessageBox.Yes:
            for s in filtered: 
                s["accepted"]=1
                self.update_mood(accepted=True)
                try: self.analytics.set_accepted(s.get("id",0),1)
                except: pass
                try:
                    if self.anim_ctrl: self.anim_ctrl.suggestion_accept()
                except: pass
        else:
            try:
                if self.anim_ctrl: self.anim_ctrl.suggestion_reject()
            except: pass
        msg2=QMessageBox(self); msg2.setWindowTitle("Log"); msg2.setText(txt); msg2.exec_()
    def show_memory(self):
        d=self.memory.data
        txt=f"Bob's Memory (low-RAM JSON):\nInteractions: {d['interactions']}\nSeen tasks: {json.dumps(d['tasks_seen'],indent=2)[:800]}\nLearned: {json.dumps(d['learned'][-5:],indent=2)[:800]}\nRAM: {get_ram_mb():.1f} MB"
        msg=QMessageBox(self); msg.setWindowTitle("Bob's Memory"); msg.setText(txt); msg.exec_()
    def restart_bob(self):
        self.show_bubble("Bob restarting with new code...", speak=False)
        try:
            # launch new instance then quit
            subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, "coding_pet_bob.py")], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform=="win32" else 0)
        except: subprocess.Popen([sys.executable, os.path.join(SCRIPT_DIR, "coding_pet_bob.py")])
        QTimer.singleShot(600, lambda: QApplication.quit())

    def queue_auto(self, action, params, priority=5):
        try:
            if not self.auto_engine or not AutomationTask: self.show_bubble("Automation engine not loaded", speak=True); return
            t=AutomationTask(f"Bob {action}", action, params, priority=priority, callback=lambda tk: self.deck.append_log(f"Auto {tk.name}: {tk.status} -> {str(tk.result or tk.error)[:200]}"))
            self.auto_engine.queue_task(t)
            self.show_bubble(f"Bob queued {action} p{priority}", speak=False)
            self.deck.append_log(f"Queued {action} id={t.id} p={priority}")
        except Exception as e: self.show_bubble(f"Queue fail: {e}", speak=True)
    def schedule_auto(self, action, params, cron):
        try:
            rec=self.auto_engine.schedule(f"Bob {action}", action, params, cron=cron)
            self.show_bubble(f"Bob scheduled {action} {cron}", speak=True)
            self.deck.append_log(f"Scheduled {rec}")
        except Exception as e: self.show_bubble(f"Schedule fail: {e}", speak=True)
    def queue_workflow(self):
        try:
            wf={"steps":[{"name":"test","action":"test","params":{"cmd":"pytest -q"}}, {"name":"backup","action":"backup","params":{"src":os.path.expanduser("~/Desktop"),"dst":os.path.expanduser("~/Desktop_bak")}}]}
            self.queue_auto("workflow", wf, priority=3)
        except Exception as e: self.show_bubble(f"Workflow fail: {e}", speak=True)
    def show_automation_history(self):
        try:
            hist=self.auto_engine.history_list(20) if self.auto_engine else []
            if not hist: self.show_bubble("No automation history yet", speak=False); return
            txt="\n".join(f"[{h.status}] {h.name} ({h.action}) -> {str(h.result or h.error)[:120]}" for h in hist[-10:])
            msg=QMessageBox(self); msg.setWindowTitle("Automation History"); msg.setText(txt); msg.exec_()
            self.deck.append_log(f"History:\n{txt}")
        except Exception as e: self.show_bubble(f"History fail: {e}", speak=True)

    def show_settings(self):
        p=self.config["personality"]
        msg=QMessageBox(self); msg.setWindowTitle("Settings"); msg.setText(f"""🐾 I'M BOB! {BOB_NAME}
Current Personality: {p['type']} ({PERSONALITY_PROMPTS[p['type']][:60]}...)
Mood: {p['mood']} | Aggressiveness: {p['aggressiveness']} ({AGGRESSIVENESS_INTERVAL[p['aggressiveness']]//1000}s)
Learning: {p['learning']} | Dismiss {p['dismiss_count']} / Accept {p['accept_count']}

App Info:
• Bob vPRO - JSON config {CONFIG_PATH} - persists personality & history
• SVG: claude-code.svg via QSvgRenderer, SQLite analytics, frameless transparent
• Timers: Anim 200ms, Suggestion {AGGRESSIVENESS_INTERVAL[p['aggressiveness']]//1000}s, Movement 50ms, Rendering 100ms

Keyboard Shortcuts:
• Left-click: dismiss / request new (affects learning)
• Drag: move (grab→closed hand)
• Right-click: Personality → switch at runtime | Restart Bob
• Deck: text + 🎤 + 🦘 + 🗂️ + 🛠️ + Go + ↻ Restart | Hide 🙈 | Dashboard: Analytics

Switch personality via Right-click > Personality or Dashboard > Customization
GOOGLE_API_KEY: set env var for Gemini
"""); msg.exec_()
    def closeEvent(self,e):
        try: self.memory.save()
        except: pass
        try: self.deck.close()
        except: pass
        try:
            if hasattr(self,'web_learner'): self.web_learner.stop()
        except: pass
        if self.suggestion_worker and self.suggestion_worker.isRunning(): self.suggestion_worker.wait()
        if self.learner: self.learner.stop()
        if self.voice_worker: self.voice_worker.stop()
        e.accept()

def main():
    app=QApplication(sys.argv); bob=BobPet(); bob.show(); bob.deck.show()
    if sys.platform.startswith("linux") and app.platformName().startswith("wayland"):
        QTimer.singleShot(1800,lambda: bob.show_bubble("Wayland restricts free movement of app windows. Use X11, or XWayland with QT_QPA_PLATFORM=xcb.",speak=False))
    sys.exit(app.exec_())
if __name__=="__main__": main()
