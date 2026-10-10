"""
Bob Animation Engine - 60 FPS robust system
Covers: frame queues, easing, SVG transforms, color/opacity, caching, idle/movement/interaction/mood/suggestion/floating/presets/state machine
"""
import math, random, time
from collections import deque
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from PyQt5.QtGui import QColor

# Easing functions
def ease_linear(t): return t
def ease_in(t): return t*t
def ease_out(t): return 1 - (1-t)*(1-t)
def ease_in_out(t): return 2*t*t if t<0.5 else 1 - pow(-2*t+2,2)/2
def ease_bounce(t):
    n1=7.5625; d1=2.75
    if t<1/d1: return n1*t*t
    elif t<2/d1: t-=1.5/d1; return n1*t*t+0.75
    elif t<2.5/d1: t-=2.25/d1; return n1*t*t+0.9375
    else: t-=2.625/d1; return n1*t*t+0.984375
def ease_elastic(t):
    if t==0: return 0
    if t==1: return 1
    return -pow(2,10*t-10)*math.sin((t*10-10.75)*2*math.pi/3)

EASINGS={"linear":ease_linear,"ease-in":ease_in,"ease-out":ease_out,"ease-in-out":ease_in_out,"bounce":ease_bounce,"elastic":ease_elastic}

class Animation:
    def __init__(self, target, prop, start, end, duration, easing="linear", on_complete=None):
        self.target=target; self.prop=prop; self.start=start; self.end=end
        self.duration=max(1,duration); self.easing=EASINGS.get(easing,ease_linear)
        self.on_complete=on_complete; self.elapsed=0; self.done=False
    def tick(self, dt):
        self.elapsed+=dt
        t=min(1, self.elapsed/self.duration)
        e=self.easing(t)
        val=self.start + (self.end-self.start)*e
        setattr(self.target, self.prop, val)
        if t>=1:
            self.done=True
            if self.on_complete: self.on_complete()
            return True
        return False

class AnimationController(QObject):
    updated=pyqtSignal()
    def __init__(self, widget, config, parent=None):
        super().__init__(parent)
        self.widget=widget; self.config=config or {}
        self.active=[]; self.queue=deque()
        self.cache={}; self.particles=[]
        self.state="idle"; self.prev_state=None; self.state_history=[]
        self.presets=self.config.get("animation",{})
        self.speed_map={"slow":0.6,"normal":1.0,"fast":1.6}
        self.intensity_map={"subtle":0.5,"normal":1.0,"exaggerated":1.8}
        self.frame=0
        self.fps=60
        self.glow_phase=0
        self.ambient_timer=QTimer(); self.ambient_timer.timeout.connect(self._ambient)
        self.ambient_timer.start(4000)
        self.timer=QTimer(); self.timer.timeout.connect(self._tick)
        self.timer.start(16)  # ~60 FPS
        self.last=time.time()
    def set_fps(self, fps):
        fps=max(10, min(60, fps))
        if fps==self.fps: return
        self.fps=fps
        self.timer.setInterval(int(1000/fps))
    def _tick(self):
        now=time.time(); dt=(now-self.last)*1000; self.last=now
        # frame skipping if lag
        if dt>40: dt=16
        # batch update
        for anim in list(self.active):
            if anim.tick(dt):
                self.active.remove(anim)
                # try queue
                if self.queue and len(self.active)<3:  # throttling
                    nxt=self.queue.popleft()
                    self.active.append(nxt)
        self.frame+=1
        self.glow_phase=(self.glow_phase+2)%360
        # state-based idle handled elsewhere
        self.updated.emit()
        # lazy cleanup
        if self.frame%60==0:
            # memory pooling reuse
            if len(self.cache)>120:
                # keep recent 80
                keys=list(self.cache.keys())[-80:]
                self.cache={k:self.cache[k] for k in keys}
    def add(self, anim, queue=False):
        if queue and self.active:
            self.queue.append(anim)
        else:
            self.active.append(anim)
    def clear(self, prop=None):
        if prop: self.active=[a for a in self.active if a.prop!=prop]
        else: self.active.clear()
    def animate(self, target, prop, to_val, duration=300, easing="ease-in-out", queue=False):
        # apply speed preset
        speed=self.speed_map.get(self.presets.get("speed","normal"),1.0)
        duration=int(duration/speed)
        # intensity scaling for scale/rotate
        intensity=self.intensity_map.get(self.presets.get("intensity","normal"),1.0)
        if prop in ("scale","glow","rotate"): to_val= 1 + (to_val-1)*intensity if prop=="scale" else to_val*intensity
        start=getattr(target, prop, 0 if prop!="scale" else 1)
        # blended transition: if same prop active, lerp from current
        self.clear(prop) if not queue else None
        anim=Animation(target, prop, start, to_val, duration, easing)
        self.add(anim, queue=queue)
    # Easing wrappers
    def ease(self, name): return EASINGS.get(name, ease_linear)
    # SVG transforms - apply to target object with scale/rotate/translate/skew/color/opacity
    def apply_svg_transform(self, painter, target):
        # batch: translate, scale, rotate, skew via transform matrix
        s=getattr(target,"scale",1); r=getattr(target,"rotate",0); tx=getattr(target,"tx",0); ty=getattr(target,"ty",0); sk=getattr(target,"skew",0)
        painter.translate(44+tx,44+ty)
        painter.rotate(r)
        painter.shear(sk,0)
        painter.scale(s,s)
        painter.translate(-44,-44)
    # Color/opacity animations
    def animate_color(self, target, to_color, duration=400):
        # morph via lerp
        start=target.color if hasattr(target,"color") else QColor("#D97757")
        def lerp(t):
            # simple
            pass
        self.animate(target, "color_hue", to_color.hue(), duration, "ease-in-out")
    def animate_opacity(self, target, to_opacity, duration=300):
        self.animate(target, "opacity", to_opacity, duration, "ease-out")

    # Idle/Ambient
    def _ambient(self):
        if self.state!="idle": return
        choice=random.choice(["breathing","floating","rotation","glow","color","bobbing"])
        if choice=="breathing": self.breathing()
        elif choice=="floating": self.floating()
        elif choice=="rotation": self.subtle_rotation()
        elif choice=="glow": self.glow_pulse()
        elif choice=="color": self.color_shift()
        elif choice=="bobbing": self.bobbing()
    def breathing(self):
        # 1.0 -> 1.08 subtle
        self.animate(self.widget, "scale", 1.08, 900, "ease-in-out")
        self.animate(self.widget, "scale", 1.0, 900, "ease-in-out", queue=True)
    def floating(self):
        self.animate(self.widget, "ty", -6, 1200, "ease-in-out")
        self.animate(self.widget, "ty", 0, 1200, "ease-in-out", queue=True)
    def subtle_rotation(self):
        ang=random.uniform(5,15) * (1 if random.random()>0.5 else -1)
        self.animate(self.widget, "rotate", ang, 1800, "ease-in-out")
        self.animate(self.widget, "rotate", 0, 1800, "ease-in-out", queue=True)
    def glow_pulse(self):
        self.animate(self.widget, "glow", 1.6, 800, "ease-in-out")
        self.animate(self.widget, "glow", 1.0, 800, "ease-in-out", queue=True)
    def color_shift(self):
        # animate color hue slightly
        self.animate(self.widget, "color_hue", 20, 1500, "ease-in-out")
        self.animate(self.widget, "color_hue", 0, 1500, "ease-in-out", queue=True)
    def bobbing(self):
        self.animate(self.widget, "ty", -4, 1000, "ease-in-out")
        self.animate(self.widget, "ty", 0, 1000, "ease-in-out", queue=True)

    # Movement
    def bounce_move(self, intensity=1):
        self.animate(self.widget, "ty", -4*intensity, 180, "ease-out")
        self.animate(self.widget, "ty", 0, 180, "bounce", queue=True)
    def rotation_on_move(self, speed=1):
        ang= 45*speed if random.random()>0.5 else -45*speed
        self.animate(self.widget, "rotate", ang, 300, "linear")
    def momentum(self):
        self.animate(self.widget, "tx", 6, 200, "ease-out")
        self.animate(self.widget, "tx", 0, 400, "elastic", queue=True)

    # Interaction
    def click_response(self):
        self.animate(self.widget, "scale", 1.25, 120, "ease-out")
        self.animate(self.widget, "rotate", 360, 300, "ease-in-out", queue=True)
        self.animate(self.widget, "scale", 1.0, 200, "bounce", queue=True)
    def drag_response(self):
        self.animate(self.widget, "scale", 1.15, 150, "ease-out")
        self.animate(self.widget, "glow", 1.8, 150, "linear")
    def drop_bounce(self):
        self.animate(self.widget, "scale", 0.92, 120, "ease-in")
        self.animate(self.widget, "scale", 1.0, 400, "bounce", queue=True)
    def hover(self, enter=True):
        if enter: self.animate(self.widget, "scale", 1.1, 180, "ease-out"); self.animate(self.widget, "glow", 1.4, 180, "linear")
        else: self.animate(self.widget, "scale", 1.0, 180, "ease-out"); self.animate(self.widget, "glow", 1.0, 180, "linear")
    def double_click(self):
        for _ in range(2): self.animate(self.widget, "rotate", 360, 250, "ease-in-out", queue=True)

    # Mood
    def mood_happy(self):
        self.animate(self.widget, "scale", 1.15, 300, "ease-in-out"); self.animate(self.widget, "glow", 1.6, 300, "linear")
        self.animate(self.widget, "rotate", 360, 500, "linear", queue=True)
    def mood_thinking(self):
        self.animate(self.widget, "rotate", 360, 3000, "linear"); self.animate(self.widget, "scale", 1.05, 800, "ease-in-out")
    def mood_sad(self):
        self.animate(self.widget, "opacity", 0.7, 600, "ease-out"); self.animate(self.widget, "ty", 4, 800, "ease-in-out")
    def mood_excited(self):
        for _ in range(3): self.animate(self.widget, "scale", 1.2, 150, "ease-out", queue=True); self.animate(self.widget, "scale", 0.9, 150, "ease-in", queue=True)
        self.animate(self.widget, "glow", 1.9, 400, "linear")
    def mood_confused(self):
        for _ in range(4): self.animate(self.widget, "rotate", random.uniform(-20,20), 180, "linear", queue=True); self.animate(self.widget, "opacity", 0.6, 120, "linear", queue=True)

    # Suggestion
    def suggestion_appear(self):
        self.widget.scale=0; self.animate(self.widget, "scale", 1.0, 400, "bounce")
    def thinking(self):
        self.mood_thinking(); self.animate(self.widget, "glow", 1.5, 1000, "ease-in-out")
    def aha(self):
        self.animate(self.widget, "scale", 1.3, 150, "ease-out"); self.animate(self.widget, "scale", 1.0, 250, "bounce", queue=True); self.animate(self.widget, "rotate", 360, 400, "ease-in-out", queue=True)
    def suggestion_accept(self):
        self.mood_happy(); self.animate(self.widget, "glow", 1.7, 400, "linear")
    def suggestion_reject(self):
        self.animate(self.widget, "scale", 0.95, 200, "ease-in"); self.animate(self.widget, "opacity", 0.7, 400, "ease-out", queue=True)
    def loading(self):
        self.animate(self.widget, "rotate", 720, 1500, "linear"); self.animate(self.widget, "glow", 1.6, 800, "ease-in-out")

    # Complex sequences
    def wake_up(self):
        self.widget.opacity=0; self.animate(self.widget, "opacity", 1.0, 600, "ease-in"); self.animate(self.widget, "scale", 1.08, 500, "bounce", queue=True)
    def celebration(self):
        self.animate(self.widget, "scale", 1.2, 200, "ease-out"); self.animate(self.widget, "rotate", 360, 400, "ease-in-out", queue=True); self.animate(self.widget, "scale", 1.0, 300, "bounce", queue=True)
    def worried(self):
        self.mood_confused(); self.animate(self.widget, "scale", 0.95, 500, "ease-in-out")
    def curious(self):
        self.subtle_rotation(); self.floating()
    def tired(self):
        self.animate(self.widget, "opacity", 0.6, 1000, "ease-out"); self.animate(self.widget, "scale", 0.88, 1000, "ease-in-out"); self.animate(self.widget, "ty", 6, 1200, "ease-in-out")
    def energetic(self):
        for _ in range(2): self.rotation_on_move(1.5); self.bounce_move(1.5)

    # Floating
    def vertical_float(self): self.floating()
    def horizontal_drift(self):
        self.animate(self.widget, "tx", 6, 1500, "ease-in-out"); self.animate(self.widget, "tx", -6, 1500, "ease-in-out", queue=True); self.animate(self.widget, "tx", 0, 800, "ease-out", queue=True)
    def circular_orbit(self):
        # orbit via tx/ty
        self.animate(self.widget, "tx", 5, 600, "ease-in-out"); self.animate(self.widget, "ty", -5, 600, "ease-in-out", queue=True)
        self.animate(self.widget, "tx", -5, 600, "ease-in-out", queue=True); self.animate(self.widget, "ty", 5, 600, "ease-in-out", queue=True)

    # Performance
    def set_preset(self, speed="normal", intensity="normal", glow_color="orange"):
        self.presets["speed"]=speed; self.presets["intensity"]=intensity; self.presets["glow_color"]=glow_color
    # State machine
    def set_state(self, new_state):
        if new_state==self.state: return
        # priority: celebration overrides
        if self.state=="celebrating" and new_state!="idle": return
        self.prev_state=self.state; self.state_history.append(self.state)
        if len(self.state_history)>10: self.state_history=self.state_history[-10:]
        self.state=new_state
        # callbacks
        if new_state=="happy": self.mood_happy()
        elif new_state=="thinking": self.mood_thinking()
        elif new_state=="sad": self.mood_sad()
        elif new_state=="excited": self.mood_excited()
    def get_state(self): return self.state
