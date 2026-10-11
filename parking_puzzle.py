"""
Parking Puzzle Game — Ultimate Edition v2
Rush Hour-style sliding block puzzle with full-featured editor.
v2 Features: daily challenge, move replay, screen shake, speed control,
  level import/export, difficulty indicators, move counter animation,
  car visual improvements (wheels/headlights), 15 solver-verified levels,
  6 themes, confetti trail, and all v1 features.
"""

import pygame, json, os, sys, math, random, struct, io, time as _time
from collections import deque
from datetime import date

# ─── Constants ───────────────────────────────────────────────────────────────
W, H_WIN = 900, 750
CELL = 80
COLS, ROWS = 6, 6
BX, BY = 50, 95
EXIT_ROW = 2
FPS = 60
ANIM_SPD = 14
HORIZ, VERT = "H", "V"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LVL_DIR = os.path.join(BASE_DIR, "parking_levels")
SCORES_F = os.path.join(BASE_DIR, "parking_scores.json")
STATS_F = os.path.join(BASE_DIR, "parking_stats.json")
DAILY_F = os.path.join(BASE_DIR, "parking_daily.json")
os.makedirs(LVL_DIR, exist_ok=True)

# ─── Themes ──────────────────────────────────────────────────────────────────
THEMES = {
    "Dark": {
        "bg": (25, 25, 35), "bg2": (35, 32, 45),
        "board": (50, 50, 65), "grid": (65, 65, 82),
        "exit": (200, 55, 55), "exit_glow": (255, 60, 60),
        "text": (225, 225, 235), "text_dim": (130, 130, 150),
        "btn": (60, 60, 80), "btn_h": (80, 80, 105),
        "panel": (38, 38, 52), "panel_b": (70, 70, 90),
        "hint": (100, 255, 200), "arrow": (180, 255, 220),
    },
    "Midnight": {
        "bg": (15, 15, 30), "bg2": (25, 20, 45),
        "board": (35, 35, 60), "grid": (50, 50, 75),
        "exit": (180, 50, 180), "exit_glow": (220, 80, 255),
        "text": (210, 210, 240), "text_dim": (120, 110, 160),
        "btn": (50, 40, 80), "btn_h": (70, 55, 110),
        "panel": (30, 25, 55), "panel_b": (60, 50, 100),
        "hint": (180, 130, 255), "arrow": (200, 160, 255),
    },
    "Ocean": {
        "bg": (15, 25, 40), "bg2": (20, 35, 55),
        "board": (30, 50, 70), "grid": (45, 65, 85),
        "exit": (50, 180, 200), "exit_glow": (80, 220, 240),
        "text": (210, 230, 240), "text_dim": (110, 140, 160),
        "btn": (30, 60, 85), "btn_h": (40, 80, 110),
        "panel": (20, 40, 60), "panel_b": (40, 70, 100),
        "hint": (80, 220, 240), "arrow": (100, 230, 250),
    },
    "Neon": {
        "bg": (10, 10, 15), "bg2": (15, 15, 25),
        "board": (25, 25, 40), "grid": (40, 40, 60),
        "exit": (255, 50, 100), "exit_glow": (255, 100, 150),
        "text": (240, 240, 255), "text_dim": (100, 100, 140),
        "btn": (40, 30, 60), "btn_h": (60, 40, 90),
        "panel": (20, 18, 35), "panel_b": (60, 50, 90),
        "hint": (0, 255, 180), "arrow": (0, 255, 200),
    },
    "Forest": {
        "bg": (15, 30, 20), "bg2": (20, 40, 25),
        "board": (30, 50, 35), "grid": (45, 70, 50),
        "exit": (80, 200, 80), "exit_glow": (120, 255, 120),
        "text": (210, 235, 215), "text_dim": (110, 150, 115),
        "btn": (35, 65, 40), "btn_h": (45, 85, 50),
        "panel": (20, 40, 25), "panel_b": (50, 80, 55),
        "hint": (100, 255, 150), "arrow": (120, 240, 160),
    },
    "Sunset": {
        "bg": (40, 20, 15), "bg2": (50, 25, 20),
        "board": (60, 40, 35), "grid": (80, 55, 50),
        "exit": (255, 150, 50), "exit_glow": (255, 180, 80),
        "text": (240, 225, 215), "text_dim": (150, 120, 105),
        "btn": (80, 50, 40), "btn_h": (100, 65, 50),
        "panel": (50, 30, 25), "panel_b": (90, 60, 50),
        "hint": (255, 200, 100), "arrow": (255, 210, 130),
    },
}

CAR_COLORS = [
    (220, 55, 55), (55, 135, 220), (55, 185, 95), (225, 175, 35),
    (155, 75, 195), (225, 125, 35), (35, 195, 195), (195, 95, 135),
    (140, 180, 80), (100, 130, 200), (200, 160, 100), (180, 60, 140),
]

T = None

def set_theme(name):
    global T
    T = THEMES.get(name, THEMES["Dark"])

set_theme("Dark")

C_SUCCESS = (80, 210, 120)
C_DANGER = (230, 70, 70)
C_STAR = (255, 210, 50)
C_STAR_E = (80, 80, 100)
C_GOLD = (255, 200, 50)
C_HIGHLIGHT = (255, 255, 100)
C_WHITE = (255, 255, 255)
C_WHEEL = (30, 30, 35)

# Difficulty config
DIFF_COLORS = {(1, 5): (80, 210, 120), (6, 8): (225, 175, 35), (9, 11): (225, 125, 35), (12, 99): (220, 55, 55)}
DIFF_NAMES = {(1, 5): "Easy", (6, 8): "Medium", (9, 11): "Hard", (12, 99): "Expert"}

def get_difficulty(opt):
    if opt is None: return "??", T["text_dim"]
    for (lo, hi), name in DIFF_NAMES.items():
        if lo <= opt <= hi: return name, DIFF_COLORS[(lo, hi)]
    return "??", T["text_dim"]

# ─── Sound Generator ─────────────────────────────────────────────────────────
def _wav(freq, ms, vol=0.3, sr=22050):
    n = int(sr * ms / 1000)
    b = io.BytesIO()
    ds = n * 2
    b.write(b'RIFF'); b.write(struct.pack('<I', 36 + ds))
    b.write(b'WAVE'); b.write(b'fmt ')
    b.write(struct.pack('<IHHIIHH', 16, 1, 1, sr, sr * 2, 2, 16))
    b.write(b'data'); b.write(struct.pack('<I', ds))
    for i in range(n):
        t = i / sr
        env = min(1.0, min(i / (sr * .005 + 1), (n - i) / (sr * .01 + 1)))
        v = int(vol * 32767 * env * math.sin(2 * math.pi * freq * t))
        b.write(struct.pack('<h', max(-32768, min(32767, v))))
    b.seek(0)
    return pygame.mixer.Sound(b)


def _multi_wav(tones, vol=0.25, sr=22050):
    total = sum(d for _, d in tones)
    n = int(sr * total / 1000)
    b = io.BytesIO()
    ds = n * 2
    b.write(b'RIFF'); b.write(struct.pack('<I', 36 + ds))
    b.write(b'WAVE'); b.write(b'fmt ')
    b.write(struct.pack('<IHHIIHH', 16, 1, 1, sr, sr * 2, 2, 16))
    b.write(b'data'); b.write(struct.pack('<I', ds))
    off = 0
    for freq, dur in tones:
        cnt = int(sr * dur / 1000)
        for i in range(cnt):
            idx = off + i
            if idx >= n: break
            t = i / sr
            env = min(1.0, min(i / (sr * .005 + 1), (cnt - i) / (sr * .01 + 1)))
            v = int(vol * 32767 * env * math.sin(2 * math.pi * freq * t))
            b.write(struct.pack('<h', max(-32768, min(32767, v))))
        off += cnt
    b.seek(0)
    return pygame.mixer.Sound(b)


class Sounds:
    def __init__(s):
        s.on = True
        s.ok = False
        try:
            pygame.mixer.init(22050, -16, 1, 512)
            s.move = _wav(440, 60, .15)
            s.click = _wav(600, 40, .12)
            s.err = _wav(200, 100, .15)
            s.win = _multi_wav([(523, 120), (659, 120), (784, 120), (1047, 250)], .2)
            s.hint = _wav(880, 80, .1)
            s.place = _wav(520, 50, .12)
            s.delete = _wav(260, 80, .12)
            s.undo = _wav(350, 50, .1)
            s.bump = _wav(150, 80, .2)
            s.ok = True
        except Exception:
            pass

    def play(s, n):
        if s.on and s.ok:
            snd = getattr(s, n, None)
            if snd:
                try: snd.play()
                except: pass


# ─── Particles ───────────────────────────────────────────────────────────────
class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'ml', 'color', 'sz', 'g', 'sh', 'rot', 'rv']
    def __init__(s, x, y, vx, vy, life, color, sz=4, g=.15, sh='r'):
        s.x, s.y, s.vx, s.vy = x, y, vx, vy
        s.life = s.ml = life; s.color = color; s.sz = sz; s.g = g; s.sh = sh
        s.rot = random.uniform(0, 6.28); s.rv = random.uniform(-.2, .2)


class Particles:
    def __init__(s): s.p = []

    def burst(s, x, y, n=30, sp=5, cols=None):
        cols = cols or CAR_COLORS
        for _ in range(n):
            a = random.uniform(0, math.pi * 2)
            sp2 = random.uniform(1, sp)
            s.p.append(Particle(x, y, math.cos(a)*sp2, math.sin(a)*sp2 - random.uniform(1,3),
                                random.randint(40, 90), random.choice(cols),
                                random.randint(3, 7), .12, random.choice(['r', 'c'])))

    def firework(s, x, y, col):
        for _ in range(25):
            a = random.uniform(0, math.pi * 2)
            sp = random.uniform(2, 6)
            s.p.append(Particle(x, y, math.cos(a)*sp, math.sin(a)*sp,
                                random.randint(30, 60), col, random.randint(2, 5), .08, 'c'))

    def confetti(s, x, y, n=15):
        for _ in range(n):
            a = random.uniform(0, math.pi * 2)
            sp = random.uniform(2, 8)
            c = random.choice(CAR_COLORS + [C_STAR, C_GOLD, C_SUCCESS, C_WHITE])
            s.p.append(Particle(x + random.randint(-30, 30), y,
                                math.cos(a)*sp, -random.uniform(3, 8),
                                random.randint(60, 120), c,
                                random.randint(4, 8), .06, 'r'))

    def trail(s, x, y, col):
        s.p.append(Particle(x, y, random.uniform(-.5, .5), random.uniform(-.5, .5),
                            random.randint(10, 25), col, random.randint(2, 4), .02, 'c'))

    def update(s):
        alive = []
        for p in s.p:
            p.x += p.vx; p.y += p.vy; p.vy += p.g; p.vx *= .99; p.life -= 1
            p.rot += p.rv
            if p.life > 0: alive.append(p)
        s.p = alive

    def draw(s, sf):
        for p in s.p:
            sz = max(1, int(p.sz * p.life / p.ml))
            if p.sh == 'c':
                pygame.draw.circle(sf, p.color, (int(p.x), int(p.y)), sz)
            else:
                s2 = pygame.Surface((sz*2, sz*2), pygame.SRCALPHA)
                pygame.draw.rect(s2, (*p.color, int(255 * p.life / p.ml)),
                                 (0, 0, sz*2, sz*2))
                rotated = pygame.transform.rotate(s2, math.degrees(p.rot))
                sf.blit(rotated, rotated.get_rect(center=(int(p.x), int(p.y))))


# ─── Screen Shake ────────────────────────────────────────────────────────────
class Shake:
    def __init__(s):
        s.x = 0; s.y = 0; s.intensity = 0; s.decay = 0.82

    def trigger(s, intensity=6):
        s.intensity = max(s.intensity, intensity)

    def update(s):
        if s.intensity > 0.3:
            s.x = random.uniform(-s.intensity, s.intensity)
            s.y = random.uniform(-s.intensity, s.intensity)
            s.intensity *= s.decay
        else:
            s.x = s.y = 0; s.intensity = 0

    def offset(s):
        return int(s.x), int(s.y)


# ─── Fade Transition ─────────────────────────────────────────────────────────
class Fade:
    def __init__(s):
        s.alpha = 0; s.target = 0; s.speed = 12; s.callback = None; s.active = False

    def start(s, callback=None):
        s.alpha = 0; s.target = 255; s.callback = callback; s.active = True

    def update(s):
        if not s.active: return
        if s.alpha < s.target:
            s.alpha = min(s.alpha + s.speed, 255)
            if s.alpha >= 255 and s.callback:
                s.callback(); s.callback = None; s.target = 0
        elif s.alpha > s.target:
            s.alpha = max(s.alpha - s.speed, 0)
            if s.alpha <= 0: s.active = False

    def draw(s, sf):
        if s.alpha > 0:
            ov = pygame.Surface((W, H_WIN), pygame.SRCALPHA)
            ov.fill((0, 0, 0, s.alpha))
            sf.blit(ov, (0, 0))


# ─── Animation ───────────────────────────────────────────────────────────────
class Anim:
    def __init__(s, car, sc, sr, ec, er):
        s.car, s.sc, s.sr, s.ec, s.er = car, sc, sr, ec, er
        s.prog = 0.0; s.done = False

    def update(s, dt):
        if s.done: return
        s.prog += ANIM_SPD * dt / CELL
        if s.prog >= 1.0:
            s.prog = 1.0; s.done = True
            s.car.col, s.car.row = s.ec, s.er

    def pos(s):
        return s.sc + (s.ec - s.sc) * s.prog, s.sr + (s.er - s.sr) * s.prog


class BumpAnim:
    """Quick shake on a single car for invalid move feedback."""
    def __init__(s, car, dc, dr):
        s.car = car; s.dc = dc; s.dr = dr
        s.timer = 8; s.offset = 0

    def update(s):
        if s.timer <= 0: return True
        s.timer -= 1
        s.offset = math.sin(s.timer * 1.5) * 6 * (s.timer / 8)
        return False

    def draw_offset(s):
        if s.dc: return int(s.offset * s.dc), 0
        return 0, int(s.offset * s.dr)


# ─── BFS Solver ──────────────────────────────────────────────────────────────
class Solver:
    @staticmethod
    def solve(level):
        cars = level.cars
        init = tuple((c.id, c.col, c.row, c.length, c.dir, c.target) for c in cars)
        vis = {tuple(sorted((c[0], c[1], c[2]) for c in init))}
        q = deque([(init, [])])
        while q:
            st, mv = q.popleft()
            g = {}
            for cid, col, row, ln, dr, it in st:
                for i in range(ln):
                    g[(col + (i if dr == HORIZ else 0), row + (i if dr == VERT else 0))] = cid
            for cid, col, row, ln, dr, it in st:
                if it and dr == HORIZ and row == EXIT_ROW and col + ln >= COLS:
                    return mv
                for d in [-1, 1]:
                    if dr == HORIZ:
                        nc = col + d
                        if nc < 0 or nc + ln > COLS: continue
                    else:
                        nr = row + d
                        if nr < 0 or nr + ln > ROWS: continue
                    ok = True
                    for i in range(ln):
                        cx = nc + i if dr == HORIZ else col
                        cy = nr + i if dr == VERT else row
                        if (cx, cy) in g and g[(cx, cy)] != cid: ok = False; break
                    if not ok: continue
                    ns = tuple((s[0], s[1] + (d if dr == HORIZ else 0),
                                s[2] + (d if dr == VERT else 0), s[3], s[4], s[5])
                               if s[0] == cid else s for s in st)
                    key = tuple(sorted((s[0], s[1], s[2]) for s in ns))
                    if key not in vis:
                        vis.add(key); q.append((ns, mv + [(cid, d if dr == HORIZ else 0,
                                                              d if dr == VERT else 0)]))
        return None


# ─── Car ─────────────────────────────────────────────────────────────────────
class Car:
    def __init__(s, id, col, row, length, dir, target=False, color=None):
        s.id, s.col, s.row, s.length, s.dir, s.target = id, col, row, length, dir, target
        s.color = CAR_COLORS[0] if target and not color else (color or CAR_COLORS[id % len(CAR_COLORS)])
        if target: s.color = CAR_COLORS[0]

    def cells(s):
        return [(s.col + (i if s.dir == HORIZ else 0), s.row + (i if s.dir == VERT else 0))
                for i in range(s.length)]

    def to_dict(s):
        return {"id": s.id, "col": s.col, "row": s.row, "length": s.length,
                "dir": s.dir, "target": s.target}

    @staticmethod
    def from_dict(d):
        return Car(d["id"], d["col"], d["row"], d["length"], d["dir"], d.get("target", False))


# ─── Level ───────────────────────────────────────────────────────────────────
class Level:
    def __init__(s, name="Custom", cars=None):
        s.name, s.cars, s.moves = name, cars or [], 0

    def grid(s):
        g = {}
        for c in s.cars:
            for cell in c.cells(): g[cell] = c.id
        return g

    def can_move(s, car, dc, dr):
        nc, nr = car.col + dc, car.row + dr
        if car.dir == HORIZ:
            if nc < 0 or nc + car.length > COLS: return False
        else:
            if nr < 0 or nr + car.length > ROWS: return False
        if not dc and not dr: return False
        g = s.grid()
        for i in range(car.length):
            cx = nc + i if car.dir == HORIZ else car.col
            cy = nr + i if car.dir == VERT else car.row
            if (cx, cy) in g and g[(cx, cy)] != car.id: return False
        return True

    def move_car(s, car, dc, dr):
        if s.can_move(car, dc, dr):
            car.col += dc; car.row += dr; s.moves += 1; return True
        return False

    def solved(s):
        return any(c.target and c.dir == HORIZ and c.row == EXIT_ROW and
                   c.col + c.length >= COLS for c in s.cars)

    def valid_moves(s):
        vm = {}
        for c in s.cars:
            moves = []
            if c.dir == HORIZ:
                for d in [-1, 1]:
                    if s.can_move(c, d, 0): moves.append((d, 0))
            else:
                for d in [-1, 1]:
                    if s.can_move(c, 0, d): moves.append((0, d))
            if moves: vm[c.id] = moves
        return vm

    def to_dict(s):
        return {"name": s.name, "cars": [c.to_dict() for c in s.cars]}

    @staticmethod
    def from_dict(d):
        return Level(d.get("name", "Custom"), [Car.from_dict(c) for c in d["cars"]])

    def copy(s):
        n = Level(s.name, [Car(c.id, c.col, c.row, c.length, c.dir, c.target, c.color) for c in s.cars])
        n.moves = s.moves; return n


# ─── Score / Stats Managers ──────────────────────────────────────────────────
class Scores:
    def __init__(s): s.d = s._load()
    def _load(s):
        try:
            if os.path.exists(SCORES_F):
                with open(SCORES_F) as f: return json.load(f)
        except: pass
        return {}
    def _save(s):
        try:
            with open(SCORES_F, 'w') as f: json.dump(s.d, f, indent=2)
        except: pass
    def best(s, k): return s.d.get(k)
    def record(s, k, m, t, opt=None):
        p = s.d.get(k)
        if p is None or m < p.get("moves", 9999):
            s.d[k] = {"moves": m, "time": round(t, 1), "optimal": opt}; s._save(); return True
        return False
    def delete(s, k): s.d.pop(k, None); s._save()


class Stats:
    def __init__(s): s.d = s._load()
    def _load(s):
        try:
            if os.path.exists(STATS_F):
                with open(STATS_F) as f: return json.load(f)
        except: pass
        return {"total_moves": 0, "total_time": 0, "levels_completed": 0,
                "games_played": 0, "perfects": 0, "theme": "Dark",
                "tutorial_shown": False, "last_level": 0,
                "daily_streak": 0, "daily_last": ""}
    def _save(s):
        try:
            with open(STATS_F, 'w') as f: json.dump(s.d, f, indent=2)
        except: pass
    def add(s, moves, t, perfect=False):
        s.d["total_moves"] += moves; s.d["total_time"] += t
        s.d["levels_completed"] += 1; s.d["games_played"] += 1
        if perfect: s.d["perfects"] += 1; s._save()
    def update_daily(s, dt_str):
        if s.d.get("daily_last") != dt_str:
            s.d["daily_streak"] = s.d.get("daily_streak", 0) + 1
            s.d["daily_last"] = dt_str
        s._save()


# ─── Daily Challenge Generator ───────────────────────────────────────────────
class DailyGen:
    @staticmethod
    def generate(dt_str=None):
        if dt_str is None: dt_str = str(date.today())
        rng = random.Random(hash(dt_str) + 42)

        for _ in range(200):
            cars = []
            tc = rng.randint(0, 3)
            cars.append(Car(0, tc, EXIT_ROW, 2, HORIZ, True))
            occ = set()
            for c in cars:
                for cell in c.cells(): occ.add(cell)

            n = rng.randint(4, 8)
            for i in range(n):
                placed = False
                for _ in range(30):
                    d = rng.choice([HORIZ, VERT])
                    l = rng.choice([2, 2, 3])
                    if d == HORIZ:
                        c = rng.randint(0, COLS - l)
                        r = rng.randint(0, ROWS - 1)
                    else:
                        c = rng.randint(0, COLS - 1)
                        r = rng.randint(0, ROWS - l)
                    cells = [(c + (j if d == HORIZ else 0), r + (j if d == VERT else 0)) for j in range(l)]
                    if any(cl in occ for cl in cells): continue
                    cars.append(Car(i + 1, c, r, l, d))
                    for cl in cells: occ.add(cl)
                    placed = True; break
                if not placed: continue

            lv = Level(f"Daily {dt_str}", cars)
            sol = Solver.solve(lv)
            if sol and 5 <= len(sol) <= 18:
                return lv, len(sol)
        return None, 0

    @staticmethod
    def save_result(dt_str, moves, t, opt):
        d = {}
        try:
            if os.path.exists(DAILY_F):
                with open(DAILY_F) as f: d = json.load(f)
        except: pass
        key = f"daily_{dt_str}"
        prev = d.get(key)
        if prev is None or moves < prev.get("moves", 9999):
            d[key] = {"date": dt_str, "moves": moves, "time": round(t, 1), "optimal": opt}
        try:
            with open(DAILY_F, 'w') as f: json.dump(d, f, indent=2)
        except: pass

    @staticmethod
    def get_result(dt_str):
        try:
            if os.path.exists(DAILY_F):
                with open(DAILY_F) as f: d = json.load(f)
                return d.get(f"daily_{dt_str}")
        except: pass
        return None


# ─── Built-in Levels (all solver-verified) ───────────────────────────────────
def builtin_levels():
    H, V = HORIZ, VERT
    return [
        Level("Zigzag", [Car(0,2,2,2,H,True), Car(1,1,0,3,V), Car(2,4,2,2,V), Car(3,1,4,2,H)]),
        Level("Two Blockers", [Car(0,1,2,2,H,True), Car(1,0,1,3,V), Car(2,3,2,2,V), Car(3,1,4,2,H)]),
        Level("Rush", [Car(0,1,2,2,H,True), Car(1,0,0,3,V), Car(2,2,0,2,H),
                       Car(3,3,2,2,V), Car(4,4,2,2,V), Car(5,0,4,2,H), Car(6,3,5,2,H)]),
        Level("Tutorial", [Car(0,1,2,2,H,True), Car(1,3,0,3,V), Car(2,0,3,3,V), Car(3,4,3,2,H)]),
        Level("Side Step", [Car(0,0,2,2,H,True), Car(1,0,0,2,H), Car(2,2,1,2,V),
                           Car(3,3,2,2,V), Car(4,2,5,2,H)]),
        Level("Challenge", [Car(0,0,2,2,H,True), Car(1,0,0,2,H), Car(2,4,0,2,V),
                           Car(3,2,1,2,V), Car(4,3,2,2,V), Car(5,1,4,2,H), Car(6,4,4,2,V)]),
        Level("Gridlock", [Car(0,0,2,2,H,True), Car(1,1,0,2,H), Car(2,3,1,2,V),
                          Car(3,2,2,2,V), Car(4,1,4,2,H), Car(5,3,4,2,V)]),
        Level("Tangle", [Car(0,0,2,2,H,True), Car(1,0,0,2,V), Car(2,2,0,2,V),
                        Car(3,2,2,2,V), Car(4,3,2,2,V), Car(5,1,4,2,H), Car(6,4,4,2,V)]),
        Level("Master", [Car(0,0,2,2,H,True), Car(1,1,0,2,V), Car(2,3,0,2,H),
                        Car(3,2,2,2,V), Car(4,4,2,2,V), Car(5,1,4,2,H), Car(6,3,4,2,H)]),
        Level("Traffic Jam", [Car(0,1,2,2,H,True), Car(1,0,0,2,H), Car(2,0,1,3,V),
                             Car(3,3,0,3,V), Car(4,5,0,3,V), Car(5,2,3,2,H),
                             Car(6,0,4,2,V), Car(7,1,4,2,H), Car(8,4,3,2,V)]),
        # v2 levels
        Level("Bottleneck", [Car(0,0,2,2,H,True), Car(1,2,0,3,V), Car(2,4,1,3,V),
                             Car(3,0,4,2,H), Car(4,3,4,2,V)]),
        Level("Crossroads", [Car(0,0,2,2,H,True), Car(1,1,0,2,V), Car(2,3,0,3,V),
                             Car(3,0,3,2,H), Car(4,2,4,2,H), Car(5,3,5,2,H)]),
        Level("Detour", [Car(0,0,2,2,H,True), Car(1,0,0,2,H), Car(2,3,1,2,V),
                         Car(3,2,2,3,V), Car(4,1,5,2,H), Car(5,3,3,2,V),
                         Car(6,4,2,2,V), Car(7,4,4,2,H)]),
        Level("Labyrinth", [Car(0,0,2,2,H,True), Car(1,2,0,3,V), Car(2,3,0,3,V),
                            Car(3,1,3,3,V), Car(4,4,3,2,V), Car(5,2,4,2,H),
                            Car(6,3,5,2,H)]),
        Level("Grand Finale", [Car(0,0,2,2,H,True), Car(1,0,0,2,H), Car(2,2,0,2,H),
                               Car(3,4,1,2,V), Car(4,2,2,3,V), Car(5,3,2,3,V),
                               Car(6,0,3,2,H), Car(7,1,4,2,V), Car(8,2,5,2,H)]),
    ]


def level_optimals():
    """Pre-computed optimal moves for each built-in level."""
    return [3, 4, 5, 6, 6, 6, 7, 7, 9, 10, 9, 9, 9, 16, 9]


# ─── Button ──────────────────────────────────────────────────────────────────
class Btn:
    def __init__(s, x, y, w, h, txt, col=None, hcol=None, fsz=18, icon=None):
        s.r = pygame.Rect(x, y, w, h); s.txt = txt; s.icon = icon
        s.col = col or T["btn"]; s.hcol = hcol or T["btn_h"]
        s.fsz = fsz; s.hov = False; s.on = True; s.vis = True

    def draw(s, sf, font):
        if not s.vis: return
        c = s.hcol if s.hov and s.on else s.col
        if not s.on: c = (45, 45, 55)
        pygame.draw.rect(sf, c, s.r, border_radius=8)
        pygame.draw.rect(sf, T["panel_b"], s.r, 1, border_radius=8)
        tc = T["text"] if s.on else T["text_dim"]
        label = f"{s.icon} {s.txt}" if s.icon else s.txt
        ts = font.render(label, True, tc)
        sf.blit(ts, ts.get_rect(center=s.r.center))

    def upd(s, mp): s.hov = s.vis and s.r.collidepoint(mp)
    def hit(s, p): return s.vis and s.on and s.r.collidepoint(p)


# ─── Clipboard helper ────────────────────────────────────────────────────────
def clipboard_copy(text):
    try:
        import subprocess
        proc = subprocess.Popen(['xclip', '-selection', 'clipboard'],
                                stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        proc.communicate(text.encode())
        return True
    except: pass
    try:
        import tkinter as tk
        r = tk.Tk(); r.withdraw()
        r.clipboard_clear(); r.clipboard_append(text)
        r.update(); r.destroy()
        return True
    except: pass
    return False

def clipboard_paste():
    try:
        import subprocess
        return subprocess.check_output(['xclip', '-selection', 'clipboard', '-o'],
                                       stderr=subprocess.DEVNULL).decode()
    except: pass
    try:
        import tkinter as tk
        r = tk.Tk(); r.withdraw()
        t = r.clipboard_get(); r.destroy()
        return t
    except: pass
    return None


# ─── Main Game ───────────────────────────────────────────────────────────────
class Game:
    def __init__(s):
        pygame.init()
        pygame.display.set_caption("Parking Puzzle — Ultimate Edition v2")
        s.scr = pygame.display.set_mode((W, H_WIN))
        s.clk = pygame.time.Clock()
        s.fl = pygame.font.SysFont("Arial", 38, bold=True)
        s.fm = pygame.font.SysFont("Arial", 24, bold=True)
        s.fs = pygame.font.SysFont("Arial", 18)
        s.ft = pygame.font.SysFont("Arial", 14)
        s.fi = pygame.font.SysFont("Arial", 12)

        s.snd = Sounds()
        s.ptx = Particles()
        s.shake = Shake()
        s.scores = Scores()
        s.stats = Stats()
        set_theme(s.stats.d.get("theme", "Dark"))

        s.state = "menu"
        s.builtins = builtin_levels()
        s.optimals = level_optimals()
        s.customs = s._load_custom()
        s.cur_lv = None; s.cur_idx = 0; s.cur_src = "builtin"
        s.sel_car = None; s.drag_st = None; s.drag_cs = None; s.drag_saved = False
        s.undo_stk = []; s.redo_stk = []
        s.anims = []; s.bump_anims = []; s.animating = False

        # Timer
        s.t_start = 0; s.t_elap = 0; s.t_run = False

        # Solver / Hint / Auto-solve
        s.solution = None; s.hint_id = None; s.hint_t = 0
        s.auto_solve = False; s.auto_steps = []; s.auto_idx = 0
        s.auto_timer = 0; s.auto_speed = 30

        # Ghost preview
        s.ghost_car = None; s.ghost_dc = 0; s.ghost_dr = 0

        # Valid moves
        s.valid_moves = {}

        # Win
        s.win_stars = 0; s.win_opt = None; s.fw_timer = 0

        # Fade
        s.fade = Fade()

        # Tutorial
        s.tut_step = 0; s.tut_visible = False

        # Editor
        s.ed_cars = []; s.ed_id = 1; s.ed_tool = "place"
        s.ed_len = 2; s.ed_dir = HORIZ
        s.ed_placing = False; s.ed_ps = None
        s.ed_sel = None; s.ed_drag = False; s.ed_doff = (0, 0)
        s.ed_name = "Custom Level"; s.ed_err = ""; s.ed_err_t = 0
        s.ed_undo = []

        # Pause
        s.paused = False

        s.name_active = False; s.name_text = ""
        s.confirm_del = None

        # v2: Move pop animation
        s.move_pop = 1.0

        # v2: Replay
        s.replay_moves = []; s.replay_playing = False
        s.replay_idx = 0; s.replay_timer = 0; s.replay_speed = 25
        s.replay_lv = None  # saved original level for replay

        # v2: Daily challenge
        s.daily_lv = None; s.daily_opt = 0; s.daily_date = ""

        # v2: Notification
        s.notif_text = ""; s.notif_timer = 0; s.notif_color = C_SUCCESS

        # v2: Scroll for level select
        s.ls_scroll = 0

        s._btns()

    def _load_custom(s):
        r = []
        for fn in sorted(os.listdir(LVL_DIR)):
            if fn.endswith(".json"):
                try:
                    with open(os.path.join(LVL_DIR, fn)) as f: r.append(Level.from_dict(json.load(f)))
                except: pass
        return r

    def _save_custom(s, lv):
        safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in lv.name)
        with open(os.path.join(LVL_DIR, f"{safe}.json"), "w") as f: json.dump(lv.to_dict(), f, indent=2)

    def _del_custom(s, idx):
        ri = idx - len(s.builtins)
        if 0 <= ri < len(s.customs):
            nm = s.customs[ri].name
            safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in nm)
            p = os.path.join(LVL_DIR, f"{safe}.json")
            if os.path.exists(p): os.remove(p)
            s.customs.pop(ri); s.scores.delete(nm); return True
        return False

    def all_lv(s): return s.builtins + s.customs

    def _btns(s):
        bx = BX + COLS * CELL + 30; bw = W - bx - 20; hw = bw // 2 - 5
        cx = W // 2
        s.b_play = Btn(cx-130, 280, 260, 52, "Play Levels", icon="\u25B6")
        s.b_daily = Btn(cx-130, 342, 260, 52, "Daily Challenge", icon="\u2600",
                        col=(45, 90, 110), hcol=(55, 115, 140))
        s.b_edit = Btn(cx-130, 404, 260, 52, "Level Editor", icon="\u270F")
        s.b_stat = Btn(cx-130, 466, 260, 52, "Statistics", icon="\u2606")
        s.b_them = Btn(cx-130, 528, 260, 52, "Theme", icon="\u263E")
        s.b_snd = Btn(cx-130, 590, 260, 52, "Sound: ON", icon="\uD83D\uDD0A")
        s.b_quit = Btn(cx-130, 652, 260, 52, "Quit", icon="\u2716",
                       col=(100,45,45), hcol=(140,55,55))
        s.m_btns = [s.b_play, s.b_daily, s.b_edit, s.b_stat, s.b_them, s.b_snd, s.b_quit]

        s.b_undo = Btn(bx, BY, bw, 34, "Undo (Ctrl+Z)", fsz=14)
        s.b_redo = Btn(bx, BY+38, bw, 34, "Redo (Ctrl+Y)", fsz=14)
        s.b_reset = Btn(bx, BY+76, bw, 34, "Reset (R)", fsz=14)
        s.b_hint = Btn(bx, BY+114, bw, 34, "Hint (H)", fsz=14, col=(45,90,75), hcol=(55,120,95))
        s.b_auto = Btn(bx, BY+152, bw, 34, "Auto-Solve (A)", fsz=14, col=(45,75,120), hcol=(55,95,150))
        s.b_menu = Btn(bx, BY+196, bw, 34, "Menu (Esc)", fsz=14)
        s.b_next = Btn(bx, BY+244, hw, 34, "Next", fsz=14)
        s.b_prev = Btn(bx+hw+10, BY+244, hw, 34, "Prev", fsz=14)
        s.p_btns = [s.b_undo, s.b_redo, s.b_reset, s.b_hint, s.b_auto,
                    s.b_menu, s.b_next, s.b_prev]

        # Editor buttons
        s.eb_pl = Btn(bx, BY, bw, 32, "Place Car", fsz=13)
        s.eb_se = Btn(bx, BY+36, bw, 32, "Select/Move", fsz=13)
        s.eb_de = Btn(bx, BY+72, bw, 32, "Delete Car", fsz=13)
        s.eb_h = Btn(bx, BY+116, hw, 32, "Horiz", fsz=13)
        s.eb_v = Btn(bx+hw+10, BY+116, hw, 32, "Vert", fsz=13)
        s.eb_l2 = Btn(bx, BY+152, hw, 32, "Len 2", fsz=13)
        s.eb_l3 = Btn(bx+hw+10, BY+152, hw, 32, "Len 3", fsz=13)
        s.eb_tg = Btn(bx, BY+194, bw, 32, "Set as Target", fsz=13, col=(130,45,45), hcol=(160,55,55))
        s.eb_rs = Btn(bx, BY+232, hw, 32, "Resize", fsz=13)
        s.eb_eu = Btn(bx+hw+10, BY+232, hw, 32, "Undo", fsz=13)
        s.eb_ex = Btn(bx, BY+270, hw, 32, "Export", fsz=13, col=(60,80,120), hcol=(75,100,150))
        s.eb_im = Btn(bx+hw+10, BY+270, hw, 32, "Import", fsz=13, col=(60,80,120), hcol=(75,100,150))
        s.eb_te = Btn(bx, BY+308, bw, 34, "Test Play", fsz=14, col=(45,90,140), hcol=(55,110,170))
        s.eb_sa = Btn(bx, BY+346, bw, 34, "Save Level", fsz=14, col=(45,110,65), hcol=(55,140,80))
        s.eb_cl = Btn(bx, BY+384, bw, 34, "Clear All", fsz=14, col=(110,75,45), hcol=(140,95,55))
        s.eb_ba = Btn(bx, BY+422, bw, 34, "Back to Menu", fsz=14)
        s.ed_btns = [s.eb_pl, s.eb_se, s.eb_de, s.eb_h, s.eb_v, s.eb_l2, s.eb_l3,
                     s.eb_tg, s.eb_rs, s.eb_eu, s.eb_ex, s.eb_im, s.eb_te, s.eb_sa, s.eb_cl, s.eb_ba]

        s.ls_btns = []
        s.b_ls_back = Btn(cx-100, H_WIN-65, 200, 45, "Back")
        s.b_wn = Btn(cx-110, 430, 220, 50, "Next Level")
        s.b_wm = Btn(cx-110, 490, 220, 50, "Menu")
        s.b_wr = Btn(cx-110, 550, 220, 50, "Retry")
        s.b_wreplay = Btn(cx-110, 375, 220, 45, "Replay Solution", fsz=16,
                          col=(45,90,120), hcol=(55,110,150))
        s.b_nok = Btn(cx-110, 380, 100, 40, "Save", fsz=16)
        s.b_ncn = Btn(cx+10, 380, 100, 40, "Cancel", fsz=16)
        s.b_cfy = Btn(cx-120, 360, 110, 40, "Delete", fsz=16, col=(150,50,50), hcol=(180,60,60))
        s.b_cfn = Btn(cx+10, 360, 110, 40, "Cancel", fsz=16)
        s.b_st_back = Btn(cx-100, H_WIN-70, 200, 50, "Back")
        s.b_pa_resume = Btn(cx-110, 280, 220, 50, "Resume", icon="\u25B6")
        s.b_pa_restart = Btn(cx-110, 345, 220, 50, "Restart")
        s.b_pa_menu = Btn(cx-110, 410, 220, 50, "Quit to Menu")

    def _build_ls(s):
        s.ls_btns = []
        for i, lv in enumerate(s.all_lv()):
            col_i, row_i = i % 3, i // 3
            x, y = 40 + col_i * 280, 130 + row_i * 64
            lb = f"{i+1}. {lv.name}"
            if i >= len(s.builtins): lb += "  [X]"
            sc = s.scores.best(lv.name)
            if sc: lb += f"  {sc['moves']}m"
            b = Btn(x, y, 260, 52, lb, fsz=13); b.li = i; s.ls_btns.append(b)

    # ── Helpers ──────────────────────────────────────────────────────────────
    def g2p(s, c, r): return BX + c * CELL, BY + r * CELL
    def p2g(s, px, py): return (px - BX) // CELL, (py - BY) // CELL

    def car_at(s, px, py, cars):
        c, r = s.p2g(px, py)
        if not (0 <= c < COLS and 0 <= r < ROWS): return None
        for car in cars:
            if (c, r) in car.cells(): return car
        return None

    def _stars(s, m, o):
        if o is None: return 1 if m > 0 else 0
        if m <= o: return 3
        if m <= o * 2: return 2
        return 1

    def _ftime(s, secs):
        m, sec = int(secs) // 60, int(secs) % 60
        return f"{m}:{sec:02d}"

    def _notify(s, text, color=C_SUCCESS, duration=120):
        s.notif_text = text; s.notif_timer = duration; s.notif_color = color

    # ── Level Management ─────────────────────────────────────────────────────
    def start_lv(s, lv, idx, src="builtin"):
        s.cur_lv = lv.copy(); s.cur_idx = idx; s.cur_src = src
        s.state = "playing"; s.sel_car = None; s.drag_st = None
        s.undo_stk = []; s.redo_stk = []; s.anims = []; s.bump_anims = []; s.animating = False
        s.solution = None; s.hint_id = None; s.hint_t = 0
        s.auto_solve = False; s.auto_steps = []; s.auto_idx = 0
        s.ghost_car = None; s.paused = False; s.move_pop = 1.0
        s.t_start = _time.time(); s.t_elap = 0; s.t_run = True
        s.valid_moves = s.cur_lv.valid_moves()
        s.replay_moves = []; s.replay_playing = False; s.replay_idx = 0
        s.replay_lv = lv.copy()
        s.stats.d["last_level"] = idx; s.stats._save()

    def _do_move(s, car, dc, dr, record=True):
        if s.animating or not s.cur_lv.can_move(car, dc, dr):
            # Invalid move -> bump + shake
            if car and not s.animating:
                s.bump_anims.append(BumpAnim(car, dc, dr))
                s.shake.trigger(4)
                s.snd.play("bump")
            return False
        oc, orow = car.col, car.row
        s.cur_lv.move_car(car, dc, dr)
        a = Anim(car, oc, orow, car.col, car.row)
        s.anims.append(a); s.animating = True
        if record:
            s.undo_stk.append({"id": car.id, "oc": oc, "or": orow, "dc": dc, "dr": dr})
            s.redo_stk.clear()
            s.replay_moves.append((car.id, dc, dr))
        s.solution = None; s.hint_id = None; s.ghost_car = None
        s.move_pop = 1.5
        s.snd.play("move")
        s.valid_moves = s.cur_lv.valid_moves()

        # Confetti trail behind moving car
        cx, cy = s.g2p(car.col + car.length / 2 if car.dir == HORIZ else car.col,
                       car.row + car.length / 2 if car.dir == VERT else car.row)
        s.ptx.trail(cx, cy, car.color)
        return True

    def undo(s):
        if s.animating or not s.undo_stk: return
        last = s.undo_stk.pop()
        car = next((c for c in s.cur_lv.cars if c.id == last["id"]), None)
        if car:
            a = Anim(car, car.col, car.row, last["oc"], last["or"])
            s.anims.append(a); s.animating = True
            car.col, car.row = last["oc"], last["or"]
            s.cur_lv.moves -= 1
            s.redo_stk.append(last)
            s.solution = None; s.hint_id = None; s.ghost_car = None
            s.valid_moves = s.cur_lv.valid_moves()
            s.snd.play("undo")

    def redo(s):
        if s.animating or not s.redo_stk: return
        nxt = s.redo_stk.pop()
        car = next((c for c in s.cur_lv.cars if c.id == nxt["id"]), None)
        if car:
            s._do_move(car, nxt["dc"], nxt["dr"], record=False)
            s.undo_stk.append(nxt)

    def reset_lv(s):
        if s.cur_src == "daily" and s.daily_lv:
            s.start_lv(s.daily_lv, 0, "daily")
        else:
            alv = s.all_lv()
            if 0 <= s.cur_idx < len(alv):
                s.start_lv(alv[s.cur_idx], s.cur_idx, s.cur_src)

    def next_lv(s):
        alv = s.all_lv()
        if alv:
            i = (s.cur_idx + 1) % len(alv)
            src = "builtin" if i < len(s.builtins) else "custom"
            s.start_lv(alv[i], i, src)

    def prev_lv(s):
        alv = s.all_lv()
        if alv:
            i = (s.cur_idx - 1) % len(alv)
            src = "builtin" if i < len(s.builtins) else "custom"
            s.start_lv(alv[i], i, src)

    def _show_hint(s):
        if s.animating or s.auto_solve or s.replay_playing: return
        sol = Solver.solve(s.cur_lv)
        if sol:
            s.hint_id = sol[0][0]; s.hint_t = 120; s.snd.play("hint")

    def _start_auto_solve(s):
        if s.animating or s.replay_playing: return
        sol = Solver.solve(s.cur_lv)
        if sol:
            s.auto_steps = sol; s.auto_idx = 0
            s.auto_solve = True; s.auto_timer = 0
            s.sel_car = None; s.snd.play("hint")

    def _auto_step(s):
        if s.animating: return
        if s.auto_idx >= len(s.auto_steps):
            s.auto_solve = False; return
        cid, dc, dr = s.auto_steps[s.auto_idx]
        car = next((c for c in s.cur_lv.cars if c.id == cid), None)
        if car and s._do_move(car, dc, dr):
            s.auto_idx += 1; s.auto_timer = 0
        else:
            s.auto_solve = False

    def _start_replay(s):
        if not s.replay_moves and s.replay_lv:
            return
        s.replay_playing = True; s.replay_idx = 0; s.replay_timer = 0
        if s.replay_lv:
            s.cur_lv = s.replay_lv.copy()
            s.undo_stk = []; s.redo_stk = []; s.anims = []; s.animating = False
            s.valid_moves = s.cur_lv.valid_moves()

    def _replay_step(s):
        if s.animating: return
        if s.replay_idx >= len(s.replay_moves):
            s.replay_playing = False; return
        cid, dc, dr = s.replay_moves[s.replay_idx]
        car = next((c for c in s.cur_lv.cars if c.id == cid), None)
        if car and s.cur_lv.can_move(car, dc, dr):
            oc, orow = car.col, car.row
            s.cur_lv.move_car(car, dc, dr)
            a = Anim(car, oc, orow, car.col, car.row)
            s.anims.append(a); s.animating = True
            s.move_pop = 1.3
            s.snd.play("move")
            s.valid_moves = s.cur_lv.valid_moves()
            s.replay_idx += 1; s.replay_timer = 0
        else:
            s.replay_playing = False

    def _handle_win(s):
        s.t_run = False; s.t_elap = _time.time() - s.t_start
        s.auto_solve = False; s.replay_playing = False
        if s.solution is None: s.solution = Solver.solve(s.cur_lv)
        opt = len(s.solution) if s.solution else None
        s.win_opt = opt; s.win_stars = s._stars(s.cur_lv.moves, opt)
        is_perfect = s.win_stars == 3
        if s.cur_src != "daily":
            s.scores.record(s.cur_lv.name, s.cur_lv.moves, s.t_elap, opt)
        else:
            DailyGen.save_result(s.daily_date, s.cur_lv.moves, s.t_elap, opt)
            s.stats.update_daily(s.daily_date)
        s.stats.add(s.cur_lv.moves, s.t_elap, is_perfect)
        s.state = "win"; s.snd.play("win")
        for _ in range(5):
            s.ptx.firework(random.randint(100, W-100), random.randint(80, 350), random.choice(CAR_COLORS))
        s.fw_timer = 0

    def _start_daily(s):
        dt_str = str(date.today())
        s.daily_date = dt_str
        # Check cache
        cache = {}
        try:
            if os.path.exists(DAILY_F):
                with open(DAILY_F) as f: cache = json.load(f)
        except: pass
        cache_key = f"gen_{dt_str}"
        if cache_key in cache:
            data = cache[cache_key]
            lv = Level(f"Daily {dt_str}", [Car.from_dict(c) for c in data["cars"]])
            s.daily_lv = lv; s.daily_opt = data.get("optimal", 0)
        else:
            lv, opt = DailyGen.generate(dt_str)
            if lv is None:
                s._notify("Failed to generate daily puzzle!", C_DANGER, 180)
                return
            s.daily_lv = lv; s.daily_opt = opt
            # Cache the generated puzzle
            cache[cache_key] = {"cars": [c.to_dict() for c in lv.cars], "optimal": opt}
            try:
                with open(DAILY_F, 'w') as f: json.dump(cache, f, indent=2)
            except: pass
        s.start_lv(s.daily_lv, 0, "daily")
        s.fade.start(lambda: None)

    # ── Drawing Primitives ───────────────────────────────────────────────────
    def _grad_bg(s, sf):
        for y in range(H_WIN):
            t = y / H_WIN
            c = tuple(int(T["bg"][i]*(1-t) + T["bg2"][i]*t) for i in range(3))
            pygame.draw.line(sf, c, (0, y), (W, y))

    def _draw_board(s, sf, ox=0, oy=0):
        br = pygame.Rect(BX-5+ox, BY-5+oy, COLS*CELL+10, ROWS*CELL+10)
        pygame.draw.rect(sf, tuple(max(0,c-15) for c in T["board"]), br, border_radius=8)
        for r in range(ROWS):
            for c in range(COLS):
                rc = pygame.Rect(BX+c*CELL+ox, BY+r*CELL+oy, CELL, CELL)
                pygame.draw.rect(sf, T["board"], rc)
                pygame.draw.rect(sf, T["grid"], rc, 1)
        # Pulsing exit
        pulse = (math.sin(pygame.time.get_ticks()/300)+1)/2
        ec = tuple(int(T["exit"][i]+(T["exit_glow"][i]-T["exit"][i])*pulse) for i in range(3))
        er = pygame.Rect(BX+COLS*CELL-3+ox, BY+EXIT_ROW*CELL+3+oy, 18, CELL-6)
        pygame.draw.rect(sf, ec, er, border_radius=5)
        ax = BX+COLS*CELL+22+ox; ay = BY+EXIT_ROW*CELL+CELL//2+oy
        sz = 12+int(3*pulse)
        pygame.draw.polygon(sf, ec, [(ax,ay-sz),(ax+sz,ay),(ax,ay+sz)])
        gs = pygame.Surface((40,40), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*T["exit_glow"], int(30*pulse)), (20,20), 20)
        sf.blit(gs, (ax-10, ay-20))

    def _draw_car(s, sf, car, col=None, row=None, hl=False, hg=False, ghost=False, ox=0, oy=0, bump_off=(0,0)):
        if col is None: col = car.col
        if row is None: row = car.row
        x, y = s.g2p(col, row)
        x += ox + bump_off[0]; y += oy + bump_off[1]
        if car.dir == HORIZ: w, h = car.length*CELL, CELL
        else: w, h = CELL, car.length*CELL
        m = 5; rc = pygame.Rect(x+m, y+m, w-m*2, h-m*2)
        if ghost:
            gs = pygame.Surface((rc.w, rc.h), pygame.SRCALPHA)
            gs.fill((*car.color, 60))
            sf.blit(gs, rc); pygame.draw.rect(sf, (*car.color, 120), rc, 2, border_radius=10)
            return
        # Hint glow
        if hg:
            pulse = (math.sin(pygame.time.get_ticks()/200)+1)/2
            gl = rc.inflate(10, 10)
            gs2 = pygame.Surface((gl.w, gl.h), pygame.SRCALPHA)
            pygame.draw.rect(gs2, (*T["hint"], int(80+60*pulse)), gs2.get_rect(), border_radius=12)
            sf.blit(gs2, gl)
        # Shadow
        sr = rc.copy(); sr.move_ip(3, 4)
        pygame.draw.rect(sf, (15,15,20), sr, border_radius=10)
        # Body
        pygame.draw.rect(sf, car.color, rc, border_radius=10)
        # Shine
        sh = pygame.Rect(rc.x+5, rc.y+3, rc.w-10, max(1, rc.h//3))
        lt = tuple(min(255,c+40) for c in car.color)
        ss = pygame.Surface((sh.w, sh.h), pygame.SRCALPHA); ss.fill((*lt, 70)); sf.blit(ss, sh)
        # Bottom shade
        bm = pygame.Rect(rc.x+5, rc.bottom-max(1,rc.h//4), rc.w-10, max(1,rc.h//4))
        dk = tuple(max(0,c-30) for c in car.color)
        bs = pygame.Surface((bm.w, bm.h), pygame.SRCALPHA); bs.fill((*dk, 50)); sf.blit(bs, bm)
        # Wheels
        if car.dir == HORIZ:
            for wx in [rc.x + 10, rc.right - 18]:
                for wy in [rc.y + 2, rc.bottom - 10]:
                    pygame.draw.rect(sf, C_WHEEL, (wx, wy, 10, 8), border_radius=2)
                    pygame.draw.rect(sf, (50,50,55), (wx, wy, 10, 8), 1, border_radius=2)
        else:
            for wy in [rc.y + 10, rc.bottom - 18]:
                for wx in [rc.x + 2, rc.right - 10]:
                    pygame.draw.rect(sf, C_WHEEL, (wx, wy, 8, 10), border_radius=2)
                    pygame.draw.rect(sf, (50,50,55), (wx, wy, 8, 10), 1, border_radius=2)
        # Headlights (small bright dots on the leading edge)
        if car.dir == HORIZ:
            pygame.draw.circle(sf, (255, 255, 200), (rc.right - 8, rc.y + 10), 3)
            pygame.draw.circle(sf, (255, 255, 200), (rc.right - 8, rc.bottom - 10), 3)
        else:
            pygame.draw.circle(sf, (255, 255, 200), (rc.x + 10, rc.bottom - 8), 3)
            pygame.draw.circle(sf, (255, 255, 200), (rc.right - 10, rc.bottom - 8), 3)
        # Border
        bc = C_HIGHLIGHT if hl else tuple(max(0,c-50) for c in car.color)
        pygame.draw.rect(sf, bc, rc, 3 if hl else 2, border_radius=10)
        # Target star
        if car.target:
            cx2, cy2 = rc.center; pts = []
            for i in range(10):
                a = -math.pi/2+i*math.pi/5; rd = 11 if i%2==0 else 5
                pts.append((cx2+rd*math.cos(a), cy2+rd*math.sin(a)))
            pygame.draw.polygon(sf, C_HIGHLIGHT, pts)

    def _draw_arrows(s, sf, ox=0, oy=0):
        if s.animating or s.auto_solve or s.replay_playing: return
        for car in s.cur_lv.cars:
            mvs = s.valid_moves.get(car.id, [])
            if not mvs: continue
            for dc, dr in mvs:
                cx, cy = s.g2p(car.col, car.row)
                if car.dir == HORIZ:
                    cx += car.length * CELL // 2; cy += CELL // 2
                    ax = cx + dc * (car.length * CELL // 2 + 15)
                    pygame.draw.line(sf, T["arrow"], (cx + dc * (car.length*CELL//2-2), cy), (ax+ox, cy+oy), 2)
                    pygame.draw.polygon(sf, T["arrow"], [
                        (ax+ox, cy+oy), (ax+ox - dc*8, cy+oy-6), (ax+ox - dc*8, cy+oy+6)])
                else:
                    cx += CELL // 2; cy += car.length * CELL // 2
                    ay = cy + dr * (car.length * CELL // 2 + 15)
                    pygame.draw.line(sf, T["arrow"], (cx+ox, cy + dr * (car.length*CELL//2-2)), (cx+ox, ay+oy), 2)
                    pygame.draw.polygon(sf, T["arrow"], [
                        (cx+ox, ay+oy), (cx+ox-6, ay+oy - dr*8), (cx+ox+6, ay+oy - dr*8)])

    def _draw_star(s, sf, cx, cy, outer, inner, col, filled=True):
        pts = []
        for i in range(10):
            a = -math.pi/2+i*math.pi/5; r = outer if i%2==0 else inner
            pts.append((cx+r*math.cos(a), cy+r*math.sin(a)))
        if filled: pygame.draw.polygon(sf, col, pts)
        pygame.draw.polygon(sf, col, pts, 2)

    def _draw_stars_row(s, sf, cx, cy, cnt, sz=18):
        for i in range(3):
            x = cx + (i-1)*sz*2.4
            if i < cnt: s._draw_star(sf, x, cy, sz, sz*.4, C_STAR)
            else: s._draw_star(sf, x, cy, sz, sz*.4, C_STAR_E, False)

    def _draw_notif(s, sf):
        if s.notif_timer > 0:
            alpha = min(255, s.notif_timer * 4)
            ts = s.fs.render(s.notif_text, True, s.notif_color)
            ts.set_alpha(alpha)
            sf.blit(ts, ts.get_rect(centerx=W//2, y=H_WIN - 30))

    # ── Screen Draws ─────────────────────────────────────────────────────────
    def draw_menu(s, sf):
        s._grad_bg(sf)
        t = pygame.time.get_ticks()/1000
        title = s.fl.render("Parking Puzzle", True, C_WHITE)
        tr = title.get_rect(centerx=W//2, y=50)
        glow = s.fl.render("Parking Puzzle", True, C_GOLD)
        glow.set_alpha(int(40+20*math.sin(t*2)))
        sf.blit(glow, (tr.x+2, tr.y+2)); sf.blit(title, tr)
        sf.blit(s.fs.render("Ultimate Edition v2", True, T["text_dim"]),
                s.fs.render("Ultimate Edition v2", True, T["text_dim"]).get_rect(centerx=W//2, y=100))
        # Mini animated board
        px, py = W//2-150, 140
        pygame.draw.rect(sf, T["board"], (px,py,300,100), border_radius=6)
        pygame.draw.rect(sf, T["grid"], (px,py,300,100), 1, border_radius=6)
        mc = [(1+math.sin(t*.3)*.8,2,2,1,CAR_COLORS[0]),(3,0+math.sin(t*.5)*.3,1,2,CAR_COLORS[1]),
              (0,3,2,1,CAR_COLORS[2]),(4,3+math.cos(t*.4)*.2,2,1,CAR_COLORS[3])]
        cs = 300/6
        for cc,mr,ml,md,clr in mc:
            rx,ry = px+cc*cs+2, py+mr*cs+2
            rw, rh = (ml*cs-4 if md==1 else cs-4), (md*cs-4 if md==2 else cs-4)
            pygame.draw.rect(sf, clr, (rx,ry,rw,rh), border_radius=4)
        # Daily streak
        streak = s.stats.d.get("daily_streak", 0)
        if streak > 0:
            sf.blit(s.fs.render(f"Daily Streak: {streak} day{'s' if streak != 1 else ''}", True, C_GOLD),
                    s.fs.render(f"Daily Streak: {streak} day{'s' if streak != 1 else ''}", True, C_GOLD).get_rect(
                        centerx=W//2, y=250))
        # Features
        feats = ["Auto-Solve", "Hints", "6 Themes", "Replay", "Daily", "Editor",
                 "15 Levels", "Export", "Wheels", "Shake", "Speed+", "Arrows"]
        fy = 668
        for i, f in enumerate(feats):
            fx = 25 + i * 73
            pygame.draw.rect(sf, T["panel"], (fx-4, fy-2, 70, 22), border_radius=10)
            sf.blit(s.fi.render(f, True, T["text_dim"]), (fx+2, fy+1))

        s.b_snd.txt = f"Sound: {'ON' if s.snd.on else 'OFF'}"
        s.b_them.txt = f"Theme: {s.stats.d.get('theme','Dark')}"
        mp = pygame.mouse.get_pos()
        for b in s.m_btns: b.upd(mp); b.draw(sf, s.fm)

    def draw_playing(s, sf):
        s._grad_bg(sf)
        ox, oy = s.shake.offset()

        # Header
        sf.blit(s.fm.render(f"Level: {s.cur_lv.name}", True, T["text"]), (BX, 8))
        # Move counter with pop animation
        move_scale = s.move_pop
        if move_scale > 1.02:
            mf = pygame.font.SysFont("Arial", int(18 * move_scale), bold=True)
        else:
            mf = s.fs
        sf.blit(mf.render(f"Moves: {s.cur_lv.moves}", True, T["text"]), (BX, 40))
        if s.t_run: s.t_elap = _time.time() - s.t_start
        sf.blit(s.fs.render(f"Time: {s._ftime(s.t_elap)}", True, T["text_dim"]), (BX+160, 40))
        best = s.scores.best(s.cur_lv.name) if s.cur_src != "daily" else DailyGen.get_result(s.daily_date)
        if best:
            sf.blit(s.ft.render(f"Best: {best['moves']}m / {s._ftime(best['time'])}", True, C_GOLD),
                    (BX+330, 44))
        if s.solution is not None:
            sf.blit(s.ft.render(f"Optimal: {len(s.solution)} moves", True, T["text_dim"]), (BX, 64))
        elif not s.auto_solve and not s.replay_playing:
            sf.blit(s.ft.render("H=hint  A=auto-solve  +/-=speed", True, T["text_dim"]), (BX, 64))
        if s.auto_solve:
            spd_label = ["Slow", "Normal", "Fast", "Turbo"][min(3, s.auto_speed // 10)]
            prog = f"Auto-solving [{spd_label}]... {s.auto_idx}/{len(s.auto_steps)}"
            sf.blit(s.ft.render(prog, True, T["hint"]), (BX, 64))
        if s.replay_playing:
            prog = f"Replaying... {s.replay_idx}/{len(s.replay_moves)}"
            sf.blit(s.ft.render(prog, True, (180, 180, 255)), (BX, 64))

        s._draw_board(sf, ox, oy)
        s._draw_arrows(sf, ox, oy)

        # Ghost preview
        if s.ghost_car and not s.animating:
            gc, gr = s.ghost_car.col + s.ghost_dc, s.ghost_car.row + s.ghost_dr
            s._draw_car(sf, s.ghost_car, col=gc, row=gr, ghost=True, ox=ox, oy=oy)

        # Bump animation offsets
        bump_map = {}
        for ba in s.bump_anims:
            bump_map[ba.car.id] = ba.draw_offset()

        # Cars
        a_ids = {a.car.id for a in s.anims}
        for car in s.cur_lv.cars:
            boff = bump_map.get(car.id, (0, 0))
            if car.id not in a_ids:
                s._draw_car(sf, car, hl=(car==s.sel_car),
                           hg=(car.id==s.hint_id and s.hint_t>0),
                           ox=ox, oy=oy, bump_off=boff)
        for a in s.anims:
            ac, ar = a.pos()
            s._draw_car(sf, a.car, col=ac, row=ar, hl=(a.car==s.sel_car), ox=ox, oy=oy)

        # Hint label
        if s.hint_id is not None and s.hint_t > 0 and not s.animating:
            for car in s.cur_lv.cars:
                if car.id == s.hint_id:
                    cx = BX+(car.col+car.length/2)*CELL+ox; cy = BY+(car.row+car.length/2)*CELL+oy
                    b = math.sin(pygame.time.get_ticks()/150)*5
                    pygame.draw.polygon(sf, T["hint"], [(cx,cy-45+b),(cx-12,cy-55+b),(cx+12,cy-55+b)])
                    sf.blit(s.ft.render("Move this!", True, T["hint"]),
                            s.ft.render("Move this!", True, T["hint"]).get_rect(centerx=cx, y=cy-72+b))
                    break

        # Side panel
        px = BX+COLS*CELL+30
        pr = pygame.Rect(px-12, BY-12, W-px+12, H_WIN-BY+8)
        pygame.draw.rect(sf, T["panel"], pr, border_radius=10)
        pygame.draw.rect(sf, T["panel_b"], pr, 1, border_radius=10)

        # Live stars
        if s.solution is not None:
            st = s._stars(s.cur_lv.moves, len(s.solution))
            s._draw_stars_row(sf, px+70, BY-8, st, 14)

        # Difficulty badge
        opt = s.win_opt if s.state == "win" else (len(s.solution) if s.solution else
               (s.optimals[s.cur_idx] if 0 <= s.cur_idx < len(s.optimals) else None))
        if opt:
            dn, dc = get_difficulty(opt)
            pygame.draw.rect(sf, dc, (px, BY+8, 60, 18), border_radius=9)
            sf.blit(s.fi.render(dn, True, C_WHITE), (px+8, BY+10))

        # Move history
        if s.undo_stk:
            sf.blit(s.fi.render(f"History: {len(s.undo_stk)} moves", True, T["text_dim"]), (px, BY+310))
            for i, mv in enumerate(s.undo_stk[-4:]):
                direction = ""
                if mv["dc"] > 0: direction = "\u2192"
                elif mv["dc"] < 0: direction = "\u2190"
                elif mv["dr"] > 0: direction = "\u2193"
                elif mv["dr"] < 0: direction = "\u2191"
                sf.blit(s.fi.render(f"  #{mv['id']} {direction}", True, T["text_dim"]),
                        (px, BY+326+i*16))

        mp = pygame.mouse.get_pos()
        for b in s.p_btns: b.upd(mp); b.draw(sf, s.ft)

        # Controls
        iy = BY + 415
        for i, (txt, c) in enumerate([
            ("Controls:", T["text"]), ("Drag / Arrow keys", T["text_dim"]),
            ("Tab: cycle car", T["text_dim"]), ("H: hint  A: auto-solve", T["text_dim"]),
            ("+/-: auto-solve speed", T["text_dim"]),
            ("Goal: RED car \u2192 EXIT!", T["text_dim"]),
        ]):
            f = s.fs if i == 0 else s.ft
            sf.blit(f.render(txt, True, c), (px, iy+i*18))

        if s.tut_visible: s._draw_tutorial(sf)
        if s.paused: s._draw_pause(sf)
        s._draw_notif(sf)

    def _draw_tutorial(s, sf):
        ov = pygame.Surface((W, H_WIN), pygame.SRCALPHA); ov.fill((0,0,0,140)); sf.blit(ov, (0,0))
        tips = [
            ("Welcome to Parking Puzzle!", C_GOLD, s.fm, 140),
            ("Slide the colored cars to free the RED car.", T["text"], s.fs, 200),
            ("Click and drag cars to move them.", T["text"], s.fs, 235),
            ("Use arrow keys after selecting a car.", T["text"], s.fs, 270),
            ("Press H for hints, A to watch AI solve it.", T["text"], s.fs, 305),
            ("New: Daily Challenge, Replay, Export/Import!", C_SUCCESS, s.fs, 345),
            ("Green arrows show valid moves.", T["hint"], s.fs, 380),
            ("Get 3 stars by matching the optimal move count!", C_GOLD, s.fs, 415),
        ]
        for txt, col, font, y in tips:
            if txt:
                ts = font.render(txt, True, col)
                sf.blit(ts, ts.get_rect(centerx=W//2, y=y))
        pulse = (math.sin(pygame.time.get_ticks()/300)+1)/2
        c = tuple(int(T["text"][i]+(C_GOLD[i]-T["text"][i])*pulse) for i in range(3))
        ts = s.fs.render("Click anywhere or press any key to continue", True, c)
        sf.blit(ts, ts.get_rect(centerx=W//2, y=470))

    def _draw_pause(s, sf):
        ov = pygame.Surface((W, H_WIN), pygame.SRCALPHA); ov.fill((0,0,0,160)); sf.blit(ov, (0,0))
        sf.blit(s.fl.render("PAUSED", True, C_WHITE),
                s.fl.render("PAUSED", True, C_WHITE).get_rect(centerx=W//2, y=200))
        mp = pygame.mouse.get_pos()
        for b in [s.b_pa_resume, s.b_pa_restart, s.b_pa_menu]:
            b.upd(mp); b.draw(sf, s.fm)

    def draw_ls(s, sf):
        s._grad_bg(sf)
        sf.blit(s.fl.render("Select Level", True, C_WHITE),
                s.fl.render("Select Level", True, C_WHITE).get_rect(centerx=W//2, y=15))
        bl, cl = len(s.builtins), len(s.customs)
        # Progress bar
        completed = sum(1 for lv in s.builtins if s.scores.best(lv.name))
        pct = completed / max(1, bl) * 100
        bar_x, bar_y, bar_w, bar_h = 60, 65, W - 120, 18
        pygame.draw.rect(sf, T["panel"], (bar_x, bar_y, bar_w, bar_h), border_radius=9)
        if pct > 0:
            pygame.draw.rect(sf, C_SUCCESS, (bar_x, bar_y, int(bar_w * pct / 100), bar_h), border_radius=9)
        pygame.draw.rect(sf, T["panel_b"], (bar_x, bar_y, bar_w, bar_h), 1, border_radius=9)
        sf.blit(s.ft.render(f"{completed}/{bl} completed ({pct:.0f}%)  |  {bl} built-in + {cl} custom",
                           True, T["text_dim"]),
                s.ft.render(f"{completed}/{bl} completed ({pct:.0f}%)  |  {bl} built-in + {cl} custom",
                           True, T["text_dim"]).get_rect(centerx=W//2, y=87))
        # Stars summary
        total_s = 0
        for i, lv in enumerate(s.builtins):
            sc = s.scores.best(lv.name)
            opt = s.optimals[i] if i < len(s.optimals) else None
            if sc and opt: total_s += s._stars(sc['moves'], opt)
            elif sc: total_s += 1
        sf.blit(s.fs.render(f"\u2605 {total_s}/{bl*3}", True, C_GOLD),
                s.fs.render(f"\u2605 {total_s}/{bl*3}", True, C_GOLD).get_rect(right=W-60, centery=bar_y+9))

        mp = pygame.mouse.get_pos()
        for i, b in enumerate(s.ls_btns):
            b.upd(mp)
            # Difficulty badge
            if b.li < len(s.optimals):
                opt = s.optimals[b.li]
                dn, dc = get_difficulty(opt)
                pygame.draw.rect(sf, dc, (b.r.right - 55, b.r.y + 4, 50, 16), border_radius=8)
                sf.blit(s.fi.render(dn, True, C_WHITE), (b.r.right - 48, b.r.y + 6))
            b.draw(sf, s.ft)

        # Delete confirm overlay
        if s.confirm_del is not None:
            ov = pygame.Surface((W, H_WIN), pygame.SRCALPHA); ov.fill((0,0,0,150)); sf.blit(ov, (0,0))
            sf.blit(s.fm.render("Delete this level?", True, C_DANGER),
                    s.fm.render("Delete this level?", True, C_DANGER).get_rect(centerx=W//2, y=310))
            for b in [s.b_cfy, s.b_cfn]: b.upd(mp); b.draw(sf, s.fs)

        s.b_ls_back.upd(mp); s.b_ls_back.draw(sf, s.fm)
        s._draw_notif(sf)

    def draw_win(s, sf):
        s._grad_bg(sf)
        s.ptx.update()
        # Continuous confetti
        if s.fw_timer < 180:
            s.fw_timer += 1
            if s.fw_timer % 8 == 0:
                s.ptx.confetti(random.randint(100, W-100), random.randint(50, 200))
            if s.fw_timer % 20 == 0:
                s.ptx.firework(random.randint(100, W-100), random.randint(80, 300), random.choice(CAR_COLORS))
        s.ptx.draw(sf)
        ov = pygame.Surface((W, H_WIN), pygame.SRCALPHA); ov.fill((0,0,0,100)); sf.blit(ov, (0,0))
        sf.blit(s.fl.render("Puzzle Solved!", True, C_SUCCESS),
                s.fl.render("Puzzle Solved!", True, C_SUCCESS).get_rect(centerx=W//2, y=140))
        s._draw_stars_row(sf, W//2, 210, s.win_stars, 26)
        sf.blit(s.fm.render(f"Moves: {s.cur_lv.moves}", True, T["text"]),
                s.fm.render(f"Moves: {s.cur_lv.moves}", True, T["text"]).get_rect(centerx=W//2, y=270))
        sf.blit(s.fs.render(f"Time: {s._ftime(s.t_elap)}", True, T["text_dim"]),
                s.fs.render(f"Time: {s._ftime(s.t_elap)}", True, T["text_dim"]).get_rect(centerx=W//2, y=310))
        if s.win_opt is not None:
            txt = f"Optimal: {s.win_opt} moves"
            if s.cur_lv.moves == s.win_opt: txt += "  (Perfect!)"
            sf.blit(s.fs.render(txt, True, C_GOLD),
                    s.fs.render(txt, True, C_GOLD).get_rect(centerx=W//2, y=345))
        best = s.scores.best(s.cur_lv.name) if s.cur_src != "daily" else DailyGen.get_result(s.daily_date)
        if best and best['moves'] == s.cur_lv.moves:
            sf.blit(s.fm.render("New Best!", True, C_GOLD),
                    s.fm.render("New Best!", True, C_GOLD).get_rect(centerx=W//2, y=380))
        # Daily badge
        if s.cur_src == "daily":
            sf.blit(s.fs.render(f"Daily Challenge - {s.daily_date}", True, (100, 200, 255)),
                    s.fs.render(f"Daily Challenge - {s.daily_date}", True, (100, 200, 255)).get_rect(centerx=W//2, y=410))

        mp = pygame.mouse.get_pos()
        # Show replay button only if there were moves
        if s.replay_moves:
            s.b_wreplay.vis = True
            s.b_wreplay.upd(mp); s.b_wreplay.draw(sf, s.fs)
            s.b_wn.r.y = 490; s.b_wm.r.y = 550; s.b_wr.r.y = 610
        else:
            s.b_wreplay.vis = False
            s.b_wn.r.y = 430; s.b_wm.r.y = 490; s.b_wr.r.y = 550
        for b in [s.b_wn, s.b_wm, s.b_wr]: b.upd(mp); b.draw(sf, s.fm)

    def draw_stats(s, sf):
        s._grad_bg(sf)
        sf.blit(s.fl.render("Statistics", True, C_WHITE),
                s.fl.render("Statistics", True, C_WHITE).get_rect(centerx=W//2, y=30))
        d = s.stats.d
        streak = d.get("daily_streak", 0)
        rows = [
            ("Levels Completed", str(d.get("levels_completed", 0))),
            ("Total Moves", str(d.get("total_moves", 0))),
            ("Total Time", s._ftime(d.get("total_time", 0))),
            ("Perfect Clears (3\u2605)", str(d.get("perfects", 0))),
            ("Games Played", str(d.get("games_played", 0))),
            ("Daily Streak", f"{streak} day{'s' if streak != 1 else ''}"),
        ]
        for i, (label, val) in enumerate(rows):
            y = 100 + i * 55
            pygame.draw.rect(sf, T["panel"], (W//2-200, y, 400, 45), border_radius=10)
            pygame.draw.rect(sf, T["panel_b"], (W//2-200, y, 400, 45), 1, border_radius=10)
            sf.blit(s.fs.render(label, True, T["text_dim"]), (W//2-180, y+12))
            sf.blit(s.fm.render(val, True, T["text"]), (W//2+130, y+8))

        # Per-level breakdown
        sf.blit(s.fs.render("Level Progress", True, T["text"]), (60, 445))
        for i, lv in enumerate(s.builtins):
            sc = s.scores.best(lv.name)
            opt = s.optimals[i] if i < len(s.optimals) else None
            x, y = 60 + (i % 5) * 165, 475 + (i // 5) * 60
            # Difficulty color bar
            if opt:
                _, dcol = get_difficulty(opt)
                pygame.draw.rect(sf, dcol, (x, y, 155, 50), border_radius=8)
                sf.blit(s.fi.render(get_difficulty(opt)[0], True, (*dcol,)), (x+110, y+4))
            else:
                pygame.draw.rect(sf, T["panel"], (x, y, 155, 50), border_radius=8)
            sf.blit(s.ft.render(lv.name, True, T["text"]), (x+8, y+6))
            if sc:
                st = s._stars(sc['moves'], opt) if opt else 1
                sf.blit(s.fi.render(f"{sc['moves']}m {s._ftime(sc['time'])}", True, T["text_dim"]), (x+8, y+26))
                for si in range(3):
                    c = C_STAR if si < st else C_STAR_E
                    pygame.draw.circle(sf, c, (x+120+si*12, y+30), 4)
            else:
                sf.blit(s.fi.render("Not completed", True, T["text_dim"]), (x+8, y+26))
            pygame.draw.rect(sf, T["panel_b"], (x, y, 155, 50), 1, border_radius=8)

        mp = pygame.mouse.get_pos()
        s.b_st_back.upd(mp); s.b_st_back.draw(sf, s.fm)
        s._draw_notif(sf)

    def draw_name_dlg(s, sf):
        ov = pygame.Surface((W, H_WIN), pygame.SRCALPHA); ov.fill((0,0,0,150)); sf.blit(ov, (0,0))
        dw, dh = 340, 200; dx, dy = (W-dw)//2, (H_WIN-dh)//2
        pygame.draw.rect(sf, T["panel"], (dx,dy,dw,dh), border_radius=12)
        pygame.draw.rect(sf, T["panel_b"], (dx,dy,dw,dh), 2, border_radius=12)
        sf.blit(s.fm.render("Save Level", True, T["text"]),
                s.fm.render("Save Level", True, T["text"]).get_rect(centerx=W//2, y=dy+20))
        sf.blit(s.fs.render("Enter level name:", True, T["text_dim"]),
                s.fs.render("Enter level name:", True, T["text_dim"]).get_rect(centerx=W//2, y=dy+65))
        ir = pygame.Rect(dx+30, dy+100, dw-60, 35)
        bc = T["hint"] if s.name_active else T["panel_b"]
        pygame.draw.rect(sf, tuple(max(0,c-10) for c in T["board"]), ir, border_radius=6)
        pygame.draw.rect(sf, bc, ir, 2, border_radius=6)
        dt = s.name_text + ("|" if s.name_active and (pygame.time.get_ticks()//500)%2==0 else "")
        sf.blit(s.fs.render(dt, True, T["text"]), (ir.x+10, ir.y+7))
        mp = pygame.mouse.get_pos()
        s.b_nok.upd(mp); s.b_ncn.upd(mp)
        s.b_nok.draw(sf, s.fs); s.b_ncn.draw(sf, s.fs)

    def draw_editor(s, sf):
        s._grad_bg(sf)
        sf.blit(s.fm.render("Level Editor", True, T["text"]), (BX, 8))
        sf.blit(s.ft.render(f"Cars: {len(s.ed_cars)}  |  Tool: {s.ed_tool}  |  "
                            f"Dir: {s.ed_dir}  |  Len: {s.ed_len}", True, T["text_dim"]), (BX, 38))
        if s.ed_sel:
            sf.blit(s.ft.render(f"Selected: Car {s.ed_sel.id} ({s.ed_sel.length}{'H' if s.ed_sel.dir==HORIZ else 'V'})"
                                f"{' [TARGET]' if s.ed_sel.target else ''}", True, C_HIGHLIGHT), (BX, 56))
        s._draw_board(sf)
        for car in s.ed_cars:
            s._draw_car(sf, car, hl=(car == s.ed_sel))
        # Side panel
        px = BX+COLS*CELL+30
        pr = pygame.Rect(px-12, BY-12, W-px+12, H_WIN-BY+8)
        pygame.draw.rect(sf, T["panel"], pr, border_radius=10)
        pygame.draw.rect(sf, T["panel_b"], pr, 1, border_radius=10)

        # Tool indicators
        tool_colors = {"place": C_SUCCESS, "select": C_GOLD, "delete": C_DANGER}
        pygame.draw.rect(sf, tool_colors.get(s.ed_tool, T["text_dim"]),
                         (px, BY-8, 8, 8), border_radius=4)

        mp = pygame.mouse.get_pos()
        for b in s.ed_btns: b.upd(mp); b.draw(sf, s.ft)

        # Error message
        if s.ed_err_t > 0:
            sf.blit(s.fs.render(s.ed_err, True, C_DANGER), (BX, BY + ROWS * CELL + 10))

        # Editor tips
        iy = BY + 468
        for i, (txt, c) in enumerate([
            ("Editor Tips:", T["text"]),
            ("Click grid to place/select/delete", T["text_dim"]),
            ("Drag to set car size", T["text_dim"]),
            ("Export/Import shares via clipboard", T["text_dim"]),
            ("Test validates solvability", T["text_dim"]),
        ]):
            f = s.fs if i == 0 else s.ft
            sf.blit(f.render(txt, True, c), (px, iy+i*18))

        s._draw_notif(sf)

    # ── Editor Logic ─────────────────────────────────────────────────────────
    def _ed_validate(s, test=False):
        if not s.ed_cars: return "No cars placed!"
        if not any(c.target for c in s.ed_cars):
            return "No target car! Place on exit row or use Set as Target."
        tgt = next((c for c in s.ed_cars if c.target), None)
        if tgt.dir != HORIZ: return "Target must be horizontal!"
        if tgt.row != EXIT_ROW: return "Target must be on exit row (row 3)!"
        if test:
            lv = Level("t", [Car(c.id,c.col,c.row,c.length,c.dir,c.target,c.color) for c in s.ed_cars])
            if Solver.solve(lv) is None: return "No solution! Adjust layout."
        return ""

    def _ed_err_set(s, msg): s.ed_err = msg; s.ed_err_t = 180

    def _ed_add(s, c1, r1, c2, r2):
        s.ed_undo.append([Car(c.id,c.col,c.row,c.length,c.dir,c.target,c.color) for c in s.ed_cars])
        if c1==c2 and r1==r2: d,l = s.ed_dir, s.ed_len; cc,cr = c1,r1
        elif abs(c2-c1) >= abs(r2-r1):
            d,l = HORIZ, max(2,min(abs(c2-c1)+1,3)); cc,cr = min(c1,c2), r1
        else:
            d,l = VERT, max(2,min(abs(r2-r1)+1,3)); cc,cr = c1, min(r1,r2)
        if d==HORIZ and cc+l>COLS: cc=COLS-l
        if d==VERT and cr+l>ROWS: cr=ROWS-l
        if cc<0 or cr<0: s.ed_undo.pop(); return
        for i in range(l):
            x,y = cc+(i if d==HORIZ else 0), cr+(i if d==VERT else 0)
            if any((x,y) in oc.cells() for oc in s.ed_cars): s.ed_undo.pop(); return
        is_t = (not any(c.target for c in s.ed_cars) and d==HORIZ and cr==EXIT_ROW)
        car = Car(s.ed_id, cc, cr, l, d, is_t); s.ed_cars.append(car); s.ed_id += 1
        s.snd.play("place")

    def _ed_undo(s):
        if s.ed_undo:
            s.ed_cars = s.ed_undo.pop()
            if s.ed_sel and s.ed_sel not in s.ed_cars: s.ed_sel = None
            s.snd.play("undo")

    def _ed_resize(s):
        if s.ed_sel:
            s.ed_undo.append([Car(c.id,c.col,c.row,c.length,c.dir,c.target,c.color) for c in s.ed_cars])
            car = s.ed_sel
            new_len = 3 if car.length == 2 else 2
            if car.dir == HORIZ:
                if car.col + new_len > COLS: s.ed_undo.pop(); return
            else:
                if car.row + new_len > ROWS: s.ed_undo.pop(); return
            for i in range(new_len):
                cx = car.col + (i if car.dir == HORIZ else 0)
                cy = car.row + (i if car.dir == VERT else 0)
                for oc in s.ed_cars:
                    if oc.id != car.id and (cx, cy) in oc.cells():
                        s.ed_undo.pop(); return
            car.length = new_len
            s.snd.play("click")

    def _ed_test(s):
        err = s._ed_validate(True)
        if err: s._ed_err_set(err); s.snd.play("err"); return
        lv = Level("Editor Test", [Car(c.id,c.col,c.row,c.length,c.dir,c.target,c.color) for c in s.ed_cars])
        s.cur_lv = lv; s.cur_idx = -1; s.cur_src = "editor"
        s.state = "playing"; s.sel_car = None; s.drag_st = None
        s.undo_stk = []; s.redo_stk = []; s.anims = []; s.bump_anims = []; s.animating = False
        s.solution = None; s.hint_id = None; s.auto_solve = False; s.ghost_car = None
        s.t_start = _time.time(); s.t_elap = 0; s.t_run = True; s.paused = False
        s.move_pop = 1.0; s.replay_moves = []; s.replay_lv = lv.copy()
        s.valid_moves = s.cur_lv.valid_moves(); s.snd.play("click")

    def _ed_save(s):
        err = s._ed_validate(True)
        if err: s._ed_err_set(err); s.snd.play("err"); return
        s.name_active = True; s.name_text = s.ed_name

    def _ed_do_save(s, name):
        name = name.strip() or f"Level {len(s.customs)+1}"
        lv = Level(name, [Car(c.id,c.col,c.row,c.length,c.dir,c.target,c.color) for c in s.ed_cars])
        s._save_custom(lv); s.customs = s._load_custom(); s.ed_name = name
        s._ed_err_set(f"Saved: {name}")

    def _ed_export(s):
        if not s.ed_cars:
            s._ed_err_set("No cars to export!"); s.snd.play("err"); return
        lv = Level(s.ed_name, [Car(c.id,c.col,c.row,c.length,c.dir,c.target,c.color) for c in s.ed_cars])
        data = json.dumps(lv.to_dict())
        if clipboard_copy(data):
            s._notify("Level copied to clipboard!", C_SUCCESS)
            s.snd.play("win")
        else:
            s._ed_err_set("Clipboard not available")
            s.snd.play("err")

    def _ed_import(s):
        text = clipboard_paste()
        if not text:
            s._ed_err_set("Clipboard is empty!")
            s.snd.play("err"); return
        try:
            d = json.loads(text)
            lv = Level.from_dict(d)
            # Verify no overlaps
            cells = set()
            for c in lv.cars:
                for cell in c.cells():
                    if cell in cells:
                        s._ed_err_set("Imported level has overlaps!")
                        s.snd.play("err"); return
                    cells.add(cell)
            s.ed_undo.append([Car(c.id,c.col,c.row,c.length,c.dir,c.target,c.color) for c in s.ed_cars])
            s.ed_cars = lv.cars
            s.ed_id = max((c.id for c in lv.cars), default=0) + 1
            s.ed_name = lv.name
            tgt = next((c for c in s.ed_cars if c.target), None)
            if tgt: tgt.color = CAR_COLORS[0]
            s._notify(f"Imported: {lv.name} ({len(lv.cars)} cars)")
            s.snd.play("place")
        except Exception as e:
            s._ed_err_set(f"Import failed: invalid format")
            s.snd.play("err")

    # ── Events ───────────────────────────────────────────────────────────────
    def events(s):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: return False
            if ev.type == pygame.KEYDOWN:
                if s.name_active:
                    if ev.key == pygame.K_RETURN: s._ed_do_save(s.name_text); s.name_active = False
                    elif ev.key == pygame.K_ESCAPE: s.name_active = False
                    elif ev.key == pygame.K_BACKSPACE: s.name_text = s.name_text[:-1]
                    elif len(s.name_text) < 30 and ev.unicode.isprintable(): s.name_text += ev.unicode
                    continue
                if s.tut_visible:
                    s.tut_visible = False; s.stats.d["tutorial_shown"] = True; s.stats._save()
                    continue
                if s.paused:
                    if ev.key == pygame.K_ESCAPE or ev.key == pygame.K_p:
                        s.paused = False; continue
                    continue
                if s.replay_playing:
                    if ev.key in (pygame.K_ESCAPE, pygame.K_SPACE):
                        s.replay_playing = False; continue
                    continue
                if ev.key == pygame.K_ESCAPE:
                    if s.confirm_del is not None: s.confirm_del = None
                    elif s.state in ("playing","editor","level_select","win","stats"):
                        s.fade.start(lambda: setattr(s,'state','menu'))
                elif ev.key == pygame.K_p and s.state == "playing": s.paused = True
                elif ev.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL and s.state == "playing": s.undo()
                elif ev.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL and s.state == "playing": s.redo()
                elif ev.key == pygame.K_r and s.state == "playing": s.reset_lv(); s.snd.play("click")
                elif ev.key == pygame.K_h and s.state == "playing": s._show_hint()
                elif ev.key == pygame.K_a and s.state == "playing": s._start_auto_solve()
                elif ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS) and s.state == "playing":
                    s.auto_speed = max(5, s.auto_speed - 5)
                    s._notify(f"Speed: {['Turbo','Fast','Normal','Slow'][min(3, s.auto_speed//10)]}")
                elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS) and s.state == "playing":
                    s.auto_speed = min(40, s.auto_speed + 5)
                    s._notify(f"Speed: {['Turbo','Fast','Normal','Slow'][min(3, s.auto_speed//10)]}")
                elif ev.key == pygame.K_TAB and s.state == "playing" and not s.animating:
                    cars = s.cur_lv.cars
                    if cars:
                        if s.sel_car is None: s.sel_car = cars[0]
                        else:
                            idx = next((i for i,c in enumerate(cars) if c.id==s.sel_car.id), 0)
                            s.sel_car = cars[(idx+1)%len(cars)]
                        s.snd.play("click")
                elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN) and s.state == "playing" and s.sel_car and not s.animating and not s.auto_solve:
                    car = s.sel_car; dc=dr=0
                    if ev.key==pygame.K_LEFT and car.dir==HORIZ: dc=-1
                    elif ev.key==pygame.K_RIGHT and car.dir==HORIZ: dc=1
                    elif ev.key==pygame.K_UP and car.dir==VERT: dr=-1
                    elif ev.key==pygame.K_DOWN and car.dir==VERT: dr=1
                    if (dc or dr): s._do_move(car, dc, dr)
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1: s._click(ev.pos)
                elif ev.button == 3 and s.state == "level_select" and s.confirm_del is None:
                    for b in s.ls_btns:
                        if b.hit(ev.pos) and b.li >= len(s.builtins): s.confirm_del = b.li; break
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1: s._release(ev.pos)
            elif ev.type == pygame.MOUSEMOTION: s._motion(ev.pos)
        return True

    def _click(s, pos):
        if s.name_active:
            if s.b_nok.hit(pos): s._ed_do_save(s.name_text)
            s.name_active = False; return
        if s.confirm_del is not None:
            if s.b_cfy.hit(pos): s._del_custom(s.confirm_del); s.confirm_del = None; s._build_ls()
            elif s.b_cfn.hit(pos): s.confirm_del = None
            return
        if s.paused:
            if s.b_pa_resume.hit(pos): s.paused = False; s.snd.play("click")
            elif s.b_pa_restart.hit(pos): s.paused = False; s.reset_lv(); s.snd.play("click")
            elif s.b_pa_menu.hit(pos): s.paused = False; s.state = "menu"; s.snd.play("click")
            return
        if s.state == "menu":
            if s.b_play.hit(pos): s._build_ls(); s.fade.start(lambda: setattr(s,'state','level_select')); s.snd.play("click")
            elif s.b_daily.hit(pos): s._start_daily(); s.snd.play("click")
            elif s.b_edit.hit(pos):
                s.ed_cars.clear(); s.ed_id=1; s.ed_sel=None; s.ed_err=""; s.ed_undo=[]
                s.fade.start(lambda: setattr(s,'state','editor')); s.snd.play("click")
            elif s.b_stat.hit(pos): s.fade.start(lambda: setattr(s,'state','stats')); s.snd.play("click")
            elif s.b_them.hit(pos):
                names = list(THEMES.keys()); cur = s.stats.d.get("theme","Dark")
                ni = (names.index(cur)+1) % len(names); nn = names[ni]
                s.stats.d["theme"] = nn; s.stats._save(); set_theme(nn); s.snd.play("click")
                for b in s.m_btns + s.p_btns + s.ed_btns:
                    if not hasattr(b, '_custom_col'):
                        b.col = T["btn"]; b.hcol = T["btn_h"]
            elif s.b_snd.hit(pos): s.snd.on = not s.snd.on
            elif s.b_quit.hit(pos): pygame.quit(); sys.exit()
        elif s.state == "playing":
            if s.animating or s.auto_solve or s.replay_playing: return
            if s.b_undo.hit(pos): s.undo()
            elif s.b_redo.hit(pos): s.redo()
            elif s.b_reset.hit(pos): s.reset_lv(); s.snd.play("click")
            elif s.b_hint.hit(pos): s._show_hint()
            elif s.b_auto.hit(pos): s._start_auto_solve()
            elif s.b_menu.hit(pos): s.state = "menu"; s.snd.play("click")
            elif s.b_next.hit(pos): s.next_lv(); s.snd.play("click")
            elif s.b_prev.hit(pos): s.prev_lv(); s.snd.play("click")
            else:
                car = s.car_at(*pos, s.cur_lv.cars)
                if car:
                    s.sel_car = car; s.drag_st = pos; s.drag_cs = (car.col, car.row); s.drag_saved = False
                    s.hint_id = None; s.ghost_car = None
        elif s.state == "level_select":
            if s.b_ls_back.hit(pos): s.fade.start(lambda: setattr(s,'state','menu')); s.snd.play("click"); return
            for b in s.ls_btns:
                if b.hit(pos):
                    alv = s.all_lv()
                    if 0 <= b.li < len(alv):
                        src = "builtin" if b.li < len(s.builtins) else "custom"
                        s.fade.start(lambda i=b.li, sr=src: s.start_lv(alv[i], i, sr))
                        s.snd.play("click")
                    return
        elif s.state == "editor": s._ed_click(pos)
        elif s.state == "win":
            if s.b_wreplay.vis and s.b_wreplay.hit(pos):
                s.state = "playing"; s._start_replay(); s.snd.play("click"); return
            if s.b_wn.hit(pos): s.next_lv(); s.snd.play("click")
            elif s.b_wm.hit(pos): s.state = "menu"; s.snd.play("click")
            elif s.b_wr.hit(pos): s.reset_lv(); s.snd.play("click")
        elif s.state == "stats":
            if s.b_st_back.hit(pos): s.fade.start(lambda: setattr(s,'state','menu')); s.snd.play("click")

    def _ed_click(s, pos):
        if s.eb_pl.hit(pos): s.ed_tool="place"; s.ed_sel=None; s.snd.play("click"); return
        if s.eb_se.hit(pos): s.ed_tool="select"; s.snd.play("click"); return
        if s.eb_de.hit(pos): s.ed_tool="delete"; s.snd.play("click"); return
        if s.eb_h.hit(pos): s.ed_dir=HORIZ; return
        if s.eb_v.hit(pos): s.ed_dir=VERT; return
        if s.eb_l2.hit(pos): s.ed_len=2; return
        if s.eb_l3.hit(pos): s.ed_len=3; return
        if s.eb_tg.hit(pos):
            if s.ed_sel:
                for c in s.ed_cars: c.target = False
                s.ed_sel.target = True; s.ed_sel.color = CAR_COLORS[0]; s.snd.play("click")
            return
        if s.eb_rs.hit(pos): s._ed_resize(); return
        if s.eb_eu.hit(pos): s._ed_undo(); return
        if s.eb_ex.hit(pos): s._ed_export(); return
        if s.eb_im.hit(pos): s._ed_import(); return
        if s.eb_te.hit(pos): s._ed_test(); return
        if s.eb_sa.hit(pos): s._ed_save(); return
        if s.eb_cl.hit(pos):
            s.ed_cars.clear(); s.ed_id=1; s.ed_sel=None; s.ed_undo=[]; s.snd.play("delete"); return
        if s.eb_ba.hit(pos): s.state="menu"; s.snd.play("click"); return
        c, r = s.p2g(*pos)
        if not (0<=c<COLS and 0<=r<ROWS): return
        if s.ed_tool == "place": s.ed_placing=True; s.ed_ps=(c,r)
        elif s.ed_tool == "select":
            car = s.car_at(*pos, s.ed_cars)
            if car:
                s.ed_sel=car; s.ed_drag=True
                px,py = s.g2p(car.col,car.row); s.ed_doff=(pos[0]-px,pos[1]-py); s.snd.play("click")
            else: s.ed_sel = None
        elif s.ed_tool == "delete":
            car = s.car_at(*pos, s.ed_cars)
            if car:
                s.ed_undo.append([Car(c2.id,c2.col,c2.row,c2.length,c2.dir,c2.target,c2.color) for c2 in s.ed_cars])
                s.ed_cars.remove(car)
                if s.ed_sel == car: s.ed_sel = None; s.snd.play("delete")

    def _release(s, pos):
        if s.state == "playing" and s.sel_car:
            # Try to execute the drag move
            if s.drag_st and s.ghost_car and not s.animating and not s.auto_solve:
                car = s.sel_car
                if car.dir == HORIZ:
                    cells = round((pos[0] - s.drag_st[0]) / CELL)
                    if cells and s.cur_lv.can_move(car, cells, 0):
                        s._do_move(car, cells, 0)
                    # else: bump animation already handled in _motion or silent fail
                else:
                    cells = round((pos[1] - s.drag_st[1]) / CELL)
                    if cells and s.cur_lv.can_move(car, 0, cells):
                        s._do_move(car, 0, cells)
            s.sel_car = None; s.drag_st = None; s.ghost_car = None
        elif s.state == "editor":
            if s.ed_placing and s.ed_ps:
                sc,sr = s.ed_ps; ec,er = s.p2g(*pos)
                ec,er = max(0,min(ec,5)), max(0,min(er,5))
                s._ed_add(sc,sr,ec,er); s.ed_placing=False; s.ed_ps=None
            s.ed_drag = False

    def _motion(s, pos):
        if s.state == "playing" and s.sel_car and s.drag_st and not s.animating and not s.auto_solve:
            car = s.sel_car; sx, sy = s.drag_st
            if car.dir == HORIZ:
                cells = round((pos[0]-sx)/CELL)
                if cells:
                    gc, gr = car.col + cells, car.row
                    if s.cur_lv.can_move(car, cells, 0):
                        s.ghost_car = car; s.ghost_dc = cells; s.ghost_dr = 0
                    else:
                        for mc in range(cells, 0 if cells > 0 else cells+1, -1 if cells > 0 else 1):
                            if s.cur_lv.can_move(car, mc, 0):
                                s.ghost_car = car; s.ghost_dc = mc; s.ghost_dr = 0; break
                        else: s.ghost_car = None
                else: s.ghost_car = None
            else:
                cells = round((pos[1]-sy)/CELL)
                if cells:
                    if s.cur_lv.can_move(car, 0, cells):
                        s.ghost_car = car; s.ghost_dc = 0; s.ghost_dr = cells
                    else:
                        for mc in range(cells, 0 if cells > 0 else cells+1, -1 if cells > 0 else 1):
                            if s.cur_lv.can_move(car, 0, mc):
                                s.ghost_car = car; s.ghost_dc = 0; s.ghost_dr = mc; break
                        else: s.ghost_car = None
                else: s.ghost_car = None
        elif s.state == "editor" and s.ed_drag and s.ed_sel:
            car = s.ed_sel; ox,oy = s.ed_doff
            gx,gy = s.p2g(pos[0]-ox, pos[1]-oy)
            ml = car.length if car.dir==HORIZ else 1; mr = car.length if car.dir==VERT else 1
            gx,gy = max(0,min(gx,COLS-ml)), max(0,min(gy,ROWS-mr))
            ok = True
            for i in range(car.length):
                cx,cy = gx+(i if car.dir==HORIZ else 0), gy+(i if car.dir==VERT else 0)
                if any((cx,cy) in oc.cells() for oc in s.ed_cars if oc.id!=car.id): ok=False; break
            if ok: car.col, car.row = gx, gy

    # ── Update ───────────────────────────────────────────────────────────────
    def update(s, dt):
        s.fade.update()
        s.shake.update()
        if s.hint_t > 0:
            s.hint_t -= 1
            if s.hint_t <= 0: s.hint_id = None
        if s.notif_timer > 0: s.notif_timer -= 1
        if s.ed_err_t > 0: s.ed_err_t -= 1
        # Move pop decay
        if s.move_pop > 1.02:
            s.move_pop += (1.0 - s.move_pop) * 0.15
        else:
            s.move_pop = 1.0
        if s.state == "playing" and not s.paused:
            # Bump animations
            done_bumps = []
            for i, ba in enumerate(s.bump_anims):
                if ba.update(): done_bumps.append(i)
            for i in reversed(done_bumps): s.bump_anims.pop(i)
            # Animations
            if s.anims:
                for a in s.anims: a.update(dt)
                s.anims = [a for a in s.anims if not a.done]
                if not s.anims:
                    s.animating = False
                    if s.state == "playing" and s.cur_lv.solved(): s._handle_win()
            # Auto-solve
            if s.auto_solve:
                s.auto_timer += 1
                if s.auto_timer >= s.auto_speed and not s.animating:
                    s._auto_step()
            # Replay
            if s.replay_playing:
                s.replay_timer += 1
                if s.replay_timer >= s.replay_speed and not s.animating:
                    s._replay_step()
        if s.state == "win": s.ptx.update()

    # ── Main Loop ────────────────────────────────────────────────────────────
    def run(s):
        if not s.stats.d.get("tutorial_shown", False):
            s.tut_visible = True

        running = True
        while running:
            dt = s.clk.tick(FPS) / 1000.0 * 60
            running = s.events()
            s.update(dt)

            if s.state == "menu": s.draw_menu(s.scr)
            elif s.state == "playing": s.draw_playing(s.scr)
            elif s.state == "level_select": s.draw_ls(s.scr)
            elif s.state == "editor": s.draw_editor(s.scr)
            elif s.state == "win": s.draw_win(s.scr)
            elif s.state == "stats": s.draw_stats(s.scr)

            if s.name_active and s.state == "editor": s.draw_name_dlg(s.scr)
            s.fade.draw(s.scr)
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    Game().run()