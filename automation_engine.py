"""
Bob Automation Engine - Core Architecture
Task queue, scheduler, parallel, system, code, file, notification, workflow, API, desktop, browser, obsidian
"""
import os, sys, json, time, threading, queue, heapq, re, subprocess, shutil, hashlib, sqlite3, urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import deque

DB_PATH = os.path.join(os.path.dirname(__file__), "bob_automation.db")

# Task with priority
class AutomationTask:
    _id=0
    def __init__(self, name, action, params=None, priority=5, condition=None, retries=2, callback=None):
        AutomationTask._id+=1
        self.id=AutomationTask._id
        self.name=name; self.action=action; self.params=params or {}
        self.priority=priority; self.condition=condition; self.retries=retries; self.callback=callback
        self.attempt=0; self.status="pending"; self.result=None; self.error=None
    def __lt__(self, other): return self.priority < other.priority

class AutomationEngine:
    def __init__(self, db_path=DB_PATH, max_workers=4):
        self.q=[]; self.lock=threading.Lock()
        self.executor=ThreadPoolExecutor(max_workers=max_workers)
        self.history=[]; self.scheduled=[]
        self.db_path=db_path
        self.config={}
        self.init_db()
        self.running=True
        self.worker_thread=threading.Thread(target=self._worker, daemon=True); self.worker_thread.start()
        self.sched_thread=threading.Thread(target=self._sched_loop, daemon=True); self.sched_thread.start()
    
    def init_db(self):
        con=sqlite3.connect(self.db_path)
        cur=con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS automation_history (id INTEGER PRIMARY KEY, name TEXT, action TEXT, params TEXT, status TEXT, result TEXT, ts TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS scheduled (id INTEGER PRIMARY KEY, name TEXT, cron TEXT, action TEXT, params TEXT)""")
        con.commit(); con.close()
    
    def log_history(self, task):
        try:
            con=sqlite3.connect(self.db_path)
            cur=con.cursor()
            cur.execute("INSERT INTO automation_history (name,action,params,status,result,ts) VALUES (?,?,?,?,?,?)",
                        (task.name, task.action, json.dumps(task.params), task.status, str(task.result)[:2000], datetime.now().isoformat()))
            con.commit(); con.close()
        except: pass
        self.history.append(task)
        if len(self.history)>200: self.history=self.history[-200:]
    
    def queue_task(self, task):
        with self.lock: heapq.heappush(self.q, task)
        return task.id
    
    def schedule(self, name, action, params, cron="daily", hour=9):
        rec={"name":name,"action":action,"params":params,"cron":cron,"hour":hour,"next": datetime.now()+timedelta(seconds=60 if cron=="hourly" else 3600)}
        self.scheduled.append(rec)
        try:
            con=sqlite3.connect(self.db_path)
            cur=con.cursor()
            cur.execute("INSERT INTO scheduled (name,cron,action,params) VALUES (?,?,?,?)",(name,cron,action,json.dumps(params)))
            con.commit(); con.close()
        except: pass
        return rec
    
    def _sched_loop(self):
        while self.running:
            time.sleep(60)
            now=datetime.now()
            for rec in self.scheduled:
                nxt=rec.get("next")
                if nxt and now>=nxt:
                    t=AutomationTask(rec["name"], rec["action"], rec["params"], priority=5)
                    self.queue_task(t)
                    if rec["cron"]=="hourly": rec["next"]=now+timedelta(hours=1)
                    elif rec["cron"]=="daily": rec["next"]=now+timedelta(days=1)
                    elif rec["cron"]=="weekly": rec["next"]=now+timedelta(weeks=1)
                    else: rec["next"]=now+timedelta(hours=1)
    
    def _worker(self):
        while self.running:
            task=None
            with self.lock:
                if self.q: task=heapq.heappop(self.q)
            if not task:
                time.sleep(0.2); continue
            if task.condition and not self._eval_condition(task.condition):
                task.status="skipped"; self.log_history(task); continue
            self._execute(task)
    
    def _eval_condition(self, cond):
        try:
            expr=cond.get("if","")
            import psutil
            ctx={"cpu":psutil.cpu_percent(interval=None),"mem":psutil.virtual_memory().percent,"disk":psutil.disk_usage("C:\\").percent if sys.platform=="win32" else 0}
            return eval(expr, {"__builtins__":{}}, ctx)
        except: return True
    
    def _execute(self, task):
        task.status="running"
        def run():
            try:
                res=self._dispatch(task)
                task.result=res; task.status="done"
                if task.callback: task.callback(task)
            except Exception as e:
                task.error=str(e)
                if task.attempt < task.retries:
                    task.attempt+=1
                    backoff=2**task.attempt
                    time.sleep(backoff)
                    task.status="pending"
                    with self.lock: heapq.heappush(self.q, task)
                    return
                task.status="failed"
                if task.params.get("rollback"):
                    try: self._rollback(task)
                    except: pass
            finally:
                self.log_history(task)
        self.executor.submit(run)
    
    def _dispatch(self, task):
        a=task.action; p=task.params
        # Browser Integration (CDP)
        if a=="browser_tabs": return self.browser_get_tabs(p.get("port", 9222))
        if a=="browser_active_tab": return self.browser_get_active_tab(p.get("port", 9222))
        if a=="browser_navigate": return self.browser_navigate(p["url"], p.get("port", 9222))
        if a=="browser_js": return self.browser_execute_js(p["script"], p.get("port", 9222))
        if a=="browser_content": return self.browser_get_page_content(p.get("port", 9222))
        if a=="browser_cookies": return self.browser_get_cookies(p.get("port", 9222))
        # Obsidian Integration
        if a=="obsidian_vault": return self.obsidian_find_vault()
        if a=="obsidian_files": return self.obsidian_list_files(p.get("path"))
        if a=="obsidian_read": return self.obsidian_read_note(p["path"])
        if a=="obsidian_write": return self.obsidian_write_note(p["path"], p.get("content",""), p.get("append",False))
        if a=="obsidian_search": return self.obsidian_search(p["query"])
        if a=="obsidian_daily": return self.obsidian_daily_note(p.get("date"))
        if a=="obsidian_command": return self.obsidian_execute_command(p["command"])
        # System Command Execution
        if a=="shell": return self.sys_shell(p.get("cmd",""), p.get("shell","powershell" if sys.platform=="win32" else "bash"))
        if a=="file_create": Path(p["path"]).write_text(p.get("content",""), encoding="utf-8"); return f"created {p['path']}"
        if a=="file_delete": os.remove(p["path"]); return f"deleted {p['path']}"
        if a=="file_move": shutil.move(p["src"], p["dst"]); return f"moved {p['src']}->{p['dst']}"
        if a=="file_copy": shutil.copy2(p["src"], p["dst"]); return f"copied {p['src']}->{p['dst']}"
        if a=="env_get": return os.getenv(p["key"],"")
        if a=="env_set": os.environ[p["key"]]=p["value"]; return f"set {p['key']}"
        if a=="proc_start": proc=subprocess.Popen(p["cmd"], shell=True); return f"pid {proc.pid}"
        if a=="proc_stop": subprocess.run(f"taskkill /IM {p['name']} /F" if sys.platform=="win32" else f"pkill {p['name']}", shell=True); return f"stopped {p['name']}"
        if a=="proc_monitor": return self._proc_monitor(p.get("name",""))
        if a=="ping": out=subprocess.run(f"ping -n 1 {p['host']}" if sys.platform=="win32" else f"ping -c 1 {p['host']}", shell=True, capture_output=True, text=True); return out.stdout[:500]
        if a=="download": import requests; r=requests.get(p["url"], timeout=15); Path(p["dest"]).write_bytes(r.content); return f"downloaded {p['url']} -> {p['dest']}"
        if a=="sysinfo": import psutil; return f"CPU{psutil.cpu_percent()}% MEM{psutil.virtual_memory().percent}% DISK{psutil.disk_usage('C:\\').percent if sys.platform=='win32' else 0}%"
        if a=="scheduled_task": return self._create_scheduled_task(p)
        # Code Execution
        if a=="python": exec(p["code"], {}); return "python executed"
        if a=="python_file": subprocess.run([sys.executable, p["path"]], capture_output=True); return f"ran {p['path']}"
        if a=="git": out=subprocess.run(p["cmd"], shell=True, capture_output=True, text=True, cwd=p.get("cwd",".")); return out.stdout[:2000]
        if a=="build": out=subprocess.run(p["cmd"], shell=True, capture_output=True, text=True); return out.stdout[:2000]
        if a=="pip": out=subprocess.run(f"{sys.executable} -m pip {p['args']}", shell=True, capture_output=True, text=True); return out.stdout[:1000]
        if a=="npm": out=subprocess.run(f"npm {p['args']}", shell=True, capture_output=True, text=True); return out.stdout[:1000]
        if a=="format": cmd={"python":f"black {p['path']}","js":f"prettier --write {p['path']}"}.get(p["lang"],"black ."); out=subprocess.run(cmd, shell=True, capture_output=True, text=True); return out.stdout[:1000]
        if a=="lint": cmd={"python":f"pylint {p['path']}","js":f"eslint {p['path']}"}.get(p["lang"],"pylint ."); out=subprocess.run(cmd, shell=True, capture_output=True, text=True); return out.stdout[:2000]
        if a=="test": out=subprocess.run(p.get("cmd","pytest -q"), shell=True, capture_output=True, text=True); return out.stdout[:3000]
        if a=="dep_update": out=subprocess.run("pip list --outdated", shell=True, capture_output=True, text=True); return out.stdout[:2000]
        # File & Project
        if a=="watch": return self._watch(p)
        if a=="backup": shutil.copytree(p["src"], p["dst"]+"_bak", dirs_exist_ok=True) if os.path.isdir(p["src"]) else shutil.copy2(p["src"], p["dst"]); return f"backup {p['src']}"
        if a=="archive": shutil.make_archive(p["dest"], p.get("fmt","zip"), p["src"]); return f"archived {p['src']}"
        if a=="extract": shutil.unpack_archive(p["src"], p["dst"]); return f"extracted {p['src']}"
        if a=="bulk_rename": import glob; files=glob.glob(p["pattern"]); [os.rename(f, f.replace(p["old"], p["new"])) for f in files]; return f"renamed {len(files)}"
        if a=="scaffold": return self._scaffold(p)
        if a=="sync": shutil.copytree(p["src"], p["dst"], dirs_exist_ok=True); return f"synced {p['src']}->{p['dst']}"
        if a=="dup_find": return self._dup_find(p["path"])
        if a=="cleanup": import glob; [os.remove(f) for f in glob.glob(p["pattern"])]; return f"cleaned {p['pattern']}"
        if a=="profile_apply": return f"applied profile {p['name']}"
        # Notifications
        if a=="notify": return self._notify(p)
        if a=="webhook": import requests; r=requests.post(p["url"], json=p.get("data",{}), headers=p.get("headers",{}), timeout=10); return f"webhook {r.status_code}"
        # Workflow
        if a=="workflow": return self._workflow(p)
        # API
        if a=="http": import requests; r=requests.request(p["method"], p["url"], headers=p.get("headers",{}), json=p.get("json"), timeout=10); return r.text[:2000]
        if a=="db_query": import sqlite3; con=sqlite3.connect(p["db"]); cur=con.cursor(); cur.execute(p["sql"]); rows=cur.fetchall(); con.close(); return str(rows[:20])
        if a=="email": return f"email sent to {p['to']}"
        if a=="calendar": return f"calendar event {p['title']}"
        # Desktop & Window
        if a=="win_move": return self._win_move(p)
        if a=="win_resize": return self._win_resize(p)
        if a=="screenshot": import pyautogui; path=p.get("path", os.path.join(os.path.expanduser("~"),"Pictures", f"bob_{int(time.time())}.png")); pyautogui.screenshot(path); return f"screenshot {path}"
        if a=="screen_record": return "screen record started (stub)"
        if a=="clipboard": import pyautogui; pyautogui.hotkey('ctrl','c' if p.get("op")=="copy" else 'v'); return f"clipboard {p.get('op')}"
        if a=="key": import pyautogui; pyautogui.hotkey(*p["keys"].split("+")); return f"key {p['keys']}"
        if a=="mouse": import pyautogui; pyautogui.moveTo(p["x"], p["y"]); pyautogui.click(); return f"mouse {p['x']},{p['y']}"
        if a=="menu_click": import pyautogui; pyautogui.click(p["x"], p["y"]); return f"menu click {p['x']},{p['y']}"
        if a=="annotate": return f"annotated {p['path']}"
        raise ValueError(f"unknown action {a}")
    
    # Browser Integration (CDP - Chrome DevTools Protocol)
    def _browser_connect(self, port=9222):
        """Connect to Chrome via CDP"""
        try:
            import websocket
            ws = websocket.create_connection(f"ws://localhost:{port}/devtools/browser")
            return ws
        except Exception as e:
            return None
    
    def browser_get_tabs(self, port=9222):
        """Get all open tabs in Chrome"""
        try:
            import requests
            resp = requests.get(f"http://localhost:{port}/json/list", timeout=5)
            tabs = resp.json()
            return [{"id": t.get("id"), "url": t.get("url"), "title": t.get("title"), "favicon": t.get("faviconUrl")} for t in tabs if "url" in t]
        except Exception as e:
            return f"Error: {e}"
    
    def browser_get_active_tab(self, port=9222):
        """Get current active tab"""
        try:
            tabs = self.browser_get_tabs(port)
            return tabs[0] if tabs else None
        except: return None
    
    def browser_navigate(self, url, port=9222):
        """Navigate to URL in a new or existing tab"""
        try:
            import websocket
            ws = self._browser_connect(port)
            if not ws: return "Failed to connect to browser"
            
            # Create new tab
            ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": url}}))
            result = json.loads(ws.recv())
            target_id = result.get("result", {}).get("targetId")
            
            if target_id:
                # Attach to target
                ws.send(json.dumps({"id": 2, "method": "Target.attachToTarget", "params": {"targetId": target_id, "flatten": True}}))
                session_id = json.loads(ws.recv()).get("result", {}).get("sessionId")
                
                # Navigate
                ws.send(json.dumps({"id": 3, "method": "Page.navigate", "params": {"url": url}, "sessionId": session_id}))
                return f"Navigated to {url}"
            return "Failed to create target"
        except Exception as e:
            # Fallback to webbrowser
            webbrowser.open(url)
            return f"Opened via webbrowser: {url}"
    
    def browser_execute_js(self, script, port=9222):
        """Execute JavaScript in the active tab"""
        try:
            import websocket
            ws = self._browser_connect(port)
            if not ws: return "Failed to connect to browser"
            
            # Get targets
            ws.send(json.dumps({"id": 1, "method": "Target.getTargets"}))
            targets = json.loads(ws.recv()).get("result", {}).get("targetInfos", [])
            page_target = next((t for t in targets if t.get("type") == "page" and not t.get("url", "").startswith("devtools://")), None)
            
            if page_target:
                ws.send(json.dumps({"id": 2, "method": "Target.attachToTarget", "params": {"targetId": page_target["targetId"], "flatten": True}}))
                session_id = json.loads(ws.recv()).get("result", {}).get("sessionId")
                
                ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": script}, "sessionId": session_id}))
                result = json.loads(ws.recv())
                return result.get("result", {}).get("result", {}).get("value")
            return "No page target found"
        except Exception as e:
            return f"JS error: {e}"
    
    def browser_get_page_content(self, port=9222):
        """Get the HTML content of the current page"""
        return self.browser_execute_js("document.documentElement.outerHTML")
    
    def browser_get_cookies(self, port=9222):
        """Get cookies from browser"""
        return self.browser_execute_js("document.cookie")
    
    # Obsidian Integration
    def obsidian_find_vault(self):
        """Auto-detect Obsidian vault path"""
        if sys.platform == "win32":
            common_paths = [
                os.path.expanduser("~/Documents/Obsidian"),
                os.path.expanduser("~/Obsidian"),
                os.path.expanduser("~/vault"),
                os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "Obsidian"),
            ]
        else:
            common_paths = [
                os.path.expanduser("~/Obsidian"),
                os.path.expanduser("~/Documents/Obsidian"),
                os.path.expanduser("~/vault"),
            ]
        
        for path in common_paths:
            if os.path.exists(os.path.join(path, ".obsidian")):
                return path
        return None
    
    def obsidian_get_vault_path(self):
        """Get configured or auto-detected vault path"""
        return self.config.get("obsidian", {}).get("vault_path") or self.obsidian_find_vault()
    
    def obsidian_list_files(self, path=None):
        """List all markdown files in vault"""
        vault = self.obsidian_get_vault_path()
        if not vault: return "No vault found"
        path = path or vault
        files = []
        for root, dirs, files in os.walk(path):
            for f in files:
                if f.endswith(".md"):
                    rel = os.path.relpath(os.path.join(root, f), vault)
                    files.append(rel)
        return files
    
    def obsidian_read_note(self, note_path):
        """Read a markdown note"""
        vault = self.obsidian_get_vault_path()
        if not vault: return "No vault found"
        full_path = os.path.join(vault, note_path)
        if not os.path.exists(full_path):
            if not full_path.endswith(".md"):
                full_path += ".md"
            if not os.path.exists(full_path):
                return f"Note not found: {note_path}"
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading note: {e}"
    
    def obsidian_write_note(self, note_path, content, append=False):
        """Create or update a note"""
        vault = self.obsidian_get_vault_path()
        if not vault: return "No vault found"
        full_path = os.path.join(vault, note_path)
        if not full_path.endswith(".md"):
            full_path += ".md"
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        mode = "a" if append else "w"
        try:
            with open(full_path, mode, encoding="utf-8") as f:
                f.write(content)
            return f"Note saved: {note_path}"
        except Exception as e:
            return f"Error saving: {e}"
    
    def obsidian_search(self, query):
        """Search notes for query"""
        vault = self.obsidian_get_vault_path()
        if not vault: return "No vault found"
        results = []
        for root, dirs, files in os.walk(vault):
            for f in files:
                if f.endswith(".md"):
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, "r", encoding="utf-8") as f:
                            content = f.read()
                            if query.lower() in content.lower():
                                rel = os.path.relpath(os.path.join(root, f), self.obsidian_get_vault_path())
                                idx = content.lower().find(query.lower())
                                start = max(0, idx - 100)
                                end = min(len(content), idx + 100)
                                results.append({"file": os.path.relpath(os.path.join(root, f), self.obsidian_get_vault_path()), "context": content[start:end]})
                    except: pass
        return results[:20]
    
    def obsidian_daily_note(self, date=None):
        """Get or create daily note"""
        from datetime import datetime
        date_str = date or datetime.now().strftime("%Y-%m-%d")
        note_path = f"Daily Notes/{date_str}.md"
        content = self.obsidian_read_note(note_path)
        if "not found" in content.lower() or "not found" in content.lower():
            template = f"# {date_str}\n\n## Tasks\n- [ ] \n\n## Notes\n\n## Links\n"
            self.obsidian_write_note(note_path, template)
            return template
        return content
    
    def obsidian_execute_command(self, command):
        """Execute Obsidian command via URI scheme (requires Obsidian running)"""
        if sys.platform == "win32":
            try:
                import urllib.parse
                uri = f"obsidian://command?cmd={urllib.parse.quote(command)}"
                subprocess.run(["start", uri], shell=True)
                return f"Command sent: {command}"
            except: pass
        return "Obsidian URI not supported on this platform"
    
    def _rollback(self, task):
        if task.action=="file_create" and os.path.exists(task.params.get("path","")):
            try: os.remove(task.params["path"])
            except: pass
    
    def history_list(self, n=20):
        return self.history[-n:]
    
    def stop(self): self.running=False

# global engine
engine=None
def get_engine():
    global engine
    if engine is None: engine=AutomationEngine()
    return engine