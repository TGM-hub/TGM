"""
Orbital Observatory — N-Body Chaos
====================================
Layout : [ CATALOGUE | SIMULATION | OBJECTS + EVENTS ]

Click any catalogue item to add it to the simulation.
Each object gets a circular orbit at its default distance,
perturbed by all other bodies — watch the chaos unfold.

Collisions → realistic momentum-conserving merger.
The survivor inherits combined mass, volume-averaged radius,
and mixed colour. Name shows what merged.

Controls:
  Click catalogue   → add object at default AU (circular orbit)
  Right-click body  → remove it
  Click body        → select (shows vars in panel)
  S                 → reset star to Sun
  R                 → full reset
  V / F             → velocity / force vectors
  SPACE             → pause / resume
  + / -             → time multiplier
  H                 → toggle HZ ring
  C                 → clear all guests
  ESC               → quit
"""

import pygame
import numpy as np
import sys
import math
import time as _time

from catalogue import CATALOGUE, CATEGORIES, AU, get_by_category

# ─────────────────────────────────────────────────────────────────
#  PHYSICAL CONSTANTS & MUTABLE STAR
# ─────────────────────────────────────────────────────────────────
G               = 6.674e-11
SUN_MASS_REAL   = 1.989e30
SUN_RADIUS_REAL = 6.957e8
AU_M            = 1.496e11
YEAR_S          = 365.25 * 86400
HZ_INNER_REAL   = 0.95
HZ_OUTER_REAL   = 1.37

star = {"mass": SUN_MASS_REAL, "radius": SUN_RADIUS_REAL, "density": 1408.0}

PHYS_RADII = {
    "Sun":6.957e8,"Mercury":2.440e6,"Venus":6.052e6,"Earth":6.371e6,
    "Moon":1.737e6,"Mars":3.390e6,"Jupiter":6.991e7,"Saturn":5.823e7,
    "Uranus":2.536e7,"Neptune":2.462e7,"Pluto":1.188e6,
    "Ganymede":2.634e6,"Titan":2.576e6,"Europa":1.561e6,"Io":1.822e6,
    "Ceres":4.730e5,"Vesta":2.625e5,"Halley's Comet":5.5e3,
    "Apophis":185.0,"67P/Churyumov":2000.0,
    "TRAPPIST-1e":5.797e6,"Kepler-442b":9.556e6,
    "Hot Jupiter (51 Peg b)":8.28e7,"Proxima b":7.0e6,
    "GJ 1214 b":1.35e7,"HD 209458 b":9.9e7,
    "WASP-12b":1.29e8,"Kepler-16b":5.0e7,
}
DEFAULT_PHYS_R = 1e6

# ─────────────────────────────────────────────────────────────────
#  ORBITAL MECHANICS
# ─────────────────────────────────────────────────────────────────
def v_circ(r):        return math.sqrt(G * star["mass"] / r)
def v_esc(r):         return math.sqrt(2 * G * star["mass"] / r)
def period(r):        return 2*math.pi*math.sqrt(r**3 / (G*star["mass"]))
def grav_force(m, r): return G * star["mass"] * m / r**2
def orb_energy(r):    return -G * star["mass"] / (2*r)
def ang_mom(m, r):    return m * v_circ(r) * r
def hill(m, r):       return r * (m / (3*star["mass"]))**(1/3)
def surf_g(m, R):     return G*m/R**2 if R > 0 else 0
def obj_density(m,R): return m / (4/3*math.pi*R**3) if R > 0 else 0

def roche(obj_R, obj_rho):
    if obj_rho <= 0 or star["density"] <= 0: return 0
    return 2.44 * star["radius"] * (star["density"] / obj_rho)**(1/3)

def hz_bounds():
    lum = (star["mass"] / SUN_MASS_REAL)**3.5
    s   = math.sqrt(lum)
    return HZ_INNER_REAL*s, HZ_OUTER_REAL*s

def lum_ratio():
    return (star["mass"] / SUN_MASS_REAL)**3.5

def star_type():
    m = star["mass"] / SUN_MASS_REAL
    if m < 0.08:  return "Brown Dwarf",          (110,  70,  35)
    if m < 0.45:  return "M — Red dwarf",         (210,  75,  45)
    if m < 0.80:  return "K — Orange dwarf",      (210, 145,  60)
    if m < 1.04:  return "G — Yellow (Sun)",      (255, 215,  75)
    if m < 1.40:  return "F — Yellow-white",      (240, 240, 155)
    if m < 2.10:  return "A — White",             (195, 210, 255)
    if m < 16.0:  return "B — Blue-white giant",  (145, 175, 255)
    return              "O — Blue supergiant",    ( 75, 115, 255)

def specific_energy(b, sun):
    """Specific orbital energy of body b w.r.t. star. <0 = bound."""
    r  = b.dist_to(sun)
    v2 = float(np.dot(b.vel - sun.vel, b.vel - sun.vel))
    if r < 1: return 0
    return 0.5*v2 - G*sun.mass/r

def compute_vars(b, sun):
    """Compute orbital variables for a live body."""
    r_m    = b.dist_to(sun)
    if r_m < 1e6: return {}
    r_au   = r_m / AU_M
    phys_r = b.phys_r
    rho    = obj_density(b.mass, phys_r)
    roche_m= roche(phys_r, rho)
    T_s    = period(r_m)
    T_e    = period(AU_M)
    vc     = v_circ(r_m)
    ve     = v_circ(AU_M)
    hz_in, hz_out = hz_bounds()
    E_spec = specific_energy(b, sun)
    bound  = E_spec < 0
    return {
        "r_au":        r_au,
        "v_actual":    float(np.linalg.norm(b.vel - sun.vel)) / 1e3,
        "v_circ":      vc / 1e3,
        "v_esc":       v_esc(r_m) / 1e3,
        "T_yr":        T_s / YEAR_S,
        "T_days":      T_s / 86400,
        "F_grav":      grav_force(b.mass, r_m),
        "E_spec":      E_spec / 1e6,
        "bound":       bound,
        "g_surf":      surf_g(b.mass, phys_r),
        "density":     rho,
        "hill_au":     hill(b.mass, r_m) / AU_M,
        "roche_au":    roche_m / AU_M,
        "roche_m":     roche_m,
        "above_roche": r_m > roche_m,
        "hz_in":       hz_in,
        "hz_out":      hz_out,
        "in_hz":       hz_in <= r_au <= hz_out,
        "vs_v":        float(np.linalg.norm(b.vel - sun.vel)) / (ve if ve else 1),
        "vs_T":        (T_s/YEAR_S) / (T_e/YEAR_S),
    }

# ─────────────────────────────────────────────────────────────────
#  LAYOUT
# ─────────────────────────────────────────────────────────────────
CAT_W  = 210
VAR_W  = 290
SIM_W  = 760
HEIGHT = 720
WIDTH  = CAT_W + SIM_W + VAR_W
FPS    = 60

CAT_X  = 0
SIM_X  = CAT_W
VAR_X  = CAT_W + SIM_W
SIM_CX = SIM_W // 2
SIM_CY = HEIGHT // 2
SIM_ORIGIN = np.array([SIM_CX, SIM_CY])

C_BG      = (4,   5,  14)
C_PANEL   = (7,  11,  22)
C_SEP     = (22,  34,  60)
C_ACCENT  = (80, 160, 255)
C_GREEN   = (60, 200, 110)
C_ORANGE  = (255, 155,  45)
C_RED     = (215,  55,  55)
C_YELLOW  = (255, 215,  60)
C_DIM     = (70,  95, 140)
C_TEXT    = (185, 205, 235)
C_LABEL   = (90, 120, 165)
C_HZ      = (50, 170,  80)
C_ROCHE   = (190,  50,  50)
C_STAR_SL = (255, 200,  70)
C_MERGE   = (255, 200, 100)   # collision flash colour

SCALE    = 2.0e9
DT_BASE  = 3600 * 8
TRAIL    = 400
MAX_EVENTS = 12    # max collision log entries shown

ITEM_H = 32
CAT_H  = 20
PAD    = 8

DEFAULT_PLANETS = ["Mercury","Venus","Earth","Mars","Jupiter","Saturn","Uranus","Neptune"]

# ─────────────────────────────────────────────────────────────────
#  BODY
# ─────────────────────────────────────────────────────────────────
class Body:
    _id = 0
    def __init__(self, name, mass, pos, vel, r_px, color, phys_r=None, desc=""):
        self.id      = Body._id; Body._id += 1
        self.name    = name
        self.mass    = float(mass)
        self.pos     = np.array(pos,  dtype=float)
        self.vel     = np.array(vel,  dtype=float)
        self.acc     = np.zeros(2)
        self.radius  = r_px
        self.phys_r  = phys_r or PHYS_RADII.get(name, DEFAULT_PHYS_R)
        self.color   = color
        self.desc    = desc
        self.trail   = []
        self.is_sun  = False
        self.is_bg   = False   # True = default solar system planet
        self.flash   = 0       # merge flash timer (frames)

    def px(self):
        rel = self.pos / SCALE
        return (int(SIM_ORIGIN[0] + rel[0]), int(SIM_ORIGIN[1] + rel[1]))

    def dist_to(self, other):
        return float(np.linalg.norm(self.pos - other.pos))

# ─────────────────────────────────────────────────────────────────
#  PHYSICS
# ─────────────────────────────────────────────────────────────────
def accs(bodies):
    A = [np.zeros(2) for _ in bodies]
    for i, a in enumerate(bodies):
        for j, b in enumerate(bodies):
            if i == j: continue
            d   = b.pos - a.pos
            mag = float(np.linalg.norm(d))
            if mag < 1e-3: continue          # guard: bodies at same position
            r   = max(mag, a.phys_r + b.phys_r, 1e6)
            A[i] += G * b.mass / r**2 * (d / mag)
    return A

def step_verlet(bodies, dt):
    if not bodies: return
    old = [b.acc.copy() for b in bodies]
    for b, a in zip(bodies, old):
        b.pos += b.vel*dt + 0.5*a*dt**2
    new = accs(bodies)
    for b, ao, an in zip(bodies, old, new):
        b.vel += 0.5*(ao + an)*dt
        b.acc  = an

def init_acc(bodies):
    A = accs(bodies)
    for b, a in zip(bodies, A): b.acc = a

def merge_pair(winner, loser, sun):
    """
    Momentum-conserving inelastic collision.
    After merge, if the resulting body is unbound (E > 0),
    we bleed off excess kinetic energy by rotating the velocity
    toward circular — physically this represents tidal dissipation
    and is the standard approach in N-body codes.
    Returns event string.
    """
    m_tot = winner.mass + loser.mass

    # Momentum conservation
    v_merged = (winner.mass*winner.vel + loser.mass*loser.vel) / m_tot

    # Volume-additive physical radius
    new_phys_r = (winner.phys_r**3 + loser.phys_r**3)**(1/3)
    new_r_px   = min(int((winner.radius**3 + loser.radius**3)**(1/3)), 40)

    # Blend colour by mass fraction
    f = loser.mass / m_tot
    new_color = tuple(int(winner.color[i]*(1-f) + loser.color[i]*f) for i in range(3))

    winner.mass   = m_tot
    winner.phys_r = new_phys_r
    winner.radius = max(winner.radius, new_r_px)
    winner.color  = new_color
    winner.flash  = 25

    # Post-collision energy check
    r = winner.dist_to(sun)
    if r < 1e6 or winner.is_sun:
        winner.vel = v_merged
    else:
        v_e   = v_esc(r)
        speed = float(np.linalg.norm(v_merged))
        if speed > v_e:
            # Cap at 92% v_esc, tangential direction
            pos_mag = float(np.linalg.norm(winner.pos))
            if pos_mag > 1e-3:
                tang   = np.array([-winner.pos[1], winner.pos[0]]) / pos_mag
            else:
                tang   = np.array([0.0, 1.0])
            winner.vel = tang * (v_e * 0.92)
        else:
            winner.vel = v_merged

    # Merge name
    if loser.name not in winner.name:
        merged_name = f"{winner.name}+{loser.name}"
        winner.name = merged_name[:17] + "…" if len(merged_name) > 18 else merged_name

    # Build readable event string
    dist_au = r / AU_M
    if winner.is_sun:
        return f"★ absorbed {loser.name} at {dist_au:.2f} AU"
    return f"{winner.name} ← {loser.name}  [{dist_au:.2f} AU]"


def process_collisions(bodies, event_log):
    """
    Detect and resolve all collisions, then log ejections.
    We loop until no new collisions are found to handle chain reactions
    in a single frame safely.
    """
    sun = bodies[0]
    any_merged = False

    for _ in range(10):   # max 10 chain reactions per frame
        merged = set()
        for i in range(len(bodies)):
            for j in range(i+1, len(bodies)):
                if i in merged or j in merged: continue
                bi, bj = bodies[i], bodies[j]
                try:
                    dist = bi.dist_to(bj)
                except Exception:
                    continue
                if dist < bi.phys_r + bj.phys_r:
                    if bi.is_sun or (not bj.is_sun and bi.mass >= bj.mass):
                        winner, loser, lose_idx = bi, bj, j
                    else:
                        winner, loser, lose_idx = bj, bi, i
                    try:
                        evt = merge_pair(winner, loser, sun)
                        event_log.insert(0, evt)
                        if len(event_log) > MAX_EVENTS: event_log.pop()
                    except Exception as e:
                        event_log.insert(0, f"collision error: {e}")
                    merged.add(lose_idx)

        if not merged:
            break
        bodies[:] = [b for i, b in enumerate(bodies) if i not in merged]
        any_merged = True

    if any_merged:
        init_acc(bodies)

    # Log and remove ejected bodies (> 150 AU)
    ejected = [b for b in bodies if not b.is_sun and b.dist_to(sun)/AU_M > 150]
    for b in ejected:
        bodies.remove(b)
        event_log.insert(0, f"↗ {b.name} ejected at {b.dist_to(sun)/AU_M:.0f} AU")
        if len(event_log) > MAX_EVENTS: event_log.pop()
    if ejected:
        init_acc(bodies)

# ─────────────────────────────────────────────────────────────────
#  SYSTEM BUILDER
# ─────────────────────────────────────────────────────────────────
def build_system():
    Body._id = 0
    stype, scol = star_type()
    sun = Body("Star", star["mass"], [0,0], [0,0], 18, scol,
               phys_r=star["radius"], desc=stype)
    sun.is_sun = True
    bodies = [sun]
    for name in DEFAULT_PLANETS:
        d   = CATALOGUE[name]
        r_m = d["default_dist_au"] * AU_M
        b   = Body(name, d["mass"], [r_m, 0], [0, v_circ(r_m)],
                   d["radius_px"], d["color"], desc=d["description"])
        b.is_bg = True
        bodies.append(b)
    init_acc(bodies)
    return bodies

def rebuild_star(bodies):
    stype, scol = star_type()
    bodies[0].mass   = star["mass"]
    bodies[0].phys_r = star["radius"]
    bodies[0].color  = scol
    bodies[0].radius = max(8, min(40, int(18*(star["radius"]/SUN_RADIUS_REAL)**0.35)))
    bodies[0].desc   = stype

def reorbit_all(bodies):
    for b in bodies:
        if b.is_sun: continue
        r = float(np.linalg.norm(b.pos))
        if r < 1e6: continue
        tangent = np.array([-b.pos[1], b.pos[0]]) / r
        b.vel   = tangent * v_circ(r)
    init_acc(bodies)

def add_object(bodies, name, data, angle_offset=0):
    """
    Add a catalogue object at its default distance with circular velocity.
    Slightly randomise angle so multiple copies don't stack.
    """
    r_m   = data["default_dist_au"] * AU_M
    angle = math.radians(angle_offset)
    pos   = np.array([math.cos(angle)*r_m, math.sin(angle)*r_m])
    tang  = np.array([-math.sin(angle), math.cos(angle)])
    vel   = tang * v_circ(r_m)
    b = Body(name, data["mass"], pos, vel,
             data["radius_px"], data["color"], desc=data.get("description",""))
    bodies.append(b)
    init_acc(bodies)
    return b

# ─────────────────────────────────────────────────────────────────
#  CATALOGUE LAYOUT
# ─────────────────────────────────────────────────────────────────
def build_cat_layout():
    items, y = [], 0
    for cat in CATEGORIES:
        items.append({"type":"cat","label":cat,
                      "rect":pygame.Rect(CAT_X, y, CAT_W, CAT_H)})
        y += CAT_H + 1
        for name, data in get_by_category(cat).items():
            items.append({"type":"item","name":name,"data":data,
                          "rect":pygame.Rect(CAT_X+4, y, CAT_W-8, ITEM_H)})
            y += ITEM_H + 2
        y += 4
    return items, y

# ─────────────────────────────────────────────────────────────────
#  SLIDER
# ─────────────────────────────────────────────────────────────────
class Slider:
    H = 7
    def __init__(self, x, y, w, vmin, vmax, val, label, fmt, log=False, color=C_ACCENT):
        self.rect  = pygame.Rect(x, y, w, self.H)
        self.vmin, self.vmax, self.value = vmin, vmax, val
        self.label, self.fmt, self.log, self.color = label, fmt, log, color
        self.drag  = False

    @property
    def frac(self):
        if self.log:
            return (math.log10(self.value) - math.log10(self.vmin)) / \
                   (math.log10(self.vmax) - math.log10(self.vmin))
        return (self.value - self.vmin) / (self.vmax - self.vmin)

    def hx(self): return int(self.rect.x + self.frac * self.rect.w)

    def hit(self, mx, my):
        return abs(mx - self.hx()) < 10 and abs(my - (self.rect.y + self.H//2)) < 12

    def track_hit(self, mx, my):
        return self.rect.inflate(0, 14).collidepoint(mx, my)

    def update(self, mx):
        f = float(np.clip((mx - self.rect.x) / self.rect.w, 0, 1))
        if self.log:
            self.value = 10**(math.log10(self.vmin) +
                              f * (math.log10(self.vmax) - math.log10(self.vmin)))
        else:
            self.value = self.vmin + f * (self.vmax - self.vmin)

    def draw(self, surf, fs, ft):
        pygame.draw.rect(surf, (20,30,55), self.rect, border_radius=3)
        fw = int(self.frac * self.rect.w)
        if fw > 0:
            pygame.draw.rect(surf, self.color,
                             pygame.Rect(self.rect.x, self.rect.y, fw, self.H),
                             border_radius=3)
        pygame.draw.circle(surf, (210,225,255), (self.hx(), self.rect.y+self.H//2), 6)
        pygame.draw.circle(surf, self.color,    (self.hx(), self.rect.y+self.H//2), 4)
        surf.blit(fs.render(self.label, True, C_LABEL), (self.rect.x, self.rect.y-15))
        surf.blit(ft.render(self.fmt.format(self.value), True, (200,218,250)),
                  (self.rect.right-62, self.rect.y-14))

# ─────────────────────────────────────────────────────────────────
#  DRAWING
# ─────────────────────────────────────────────────────────────────
_STARS = None
def starfield():
    global _STARS
    if _STARS is None:
        rng  = np.random.default_rng(7)
        pos  = rng.integers(0, [SIM_W, HEIGHT], size=(220,2))
        brit = rng.integers(25, 140, size=220)
        _STARS = list(zip(pos.tolist(), brit.tolist()))
    return _STARS

def draw_trail(surf, trail, color):
    if len(trail) < 2: return
    for i in range(1, len(trail)):
        a = int(200 * i / len(trail))
        c = tuple(max(0, min(255, int(ch*a/255))) for ch in color)
        pygame.draw.line(surf, c, trail[i-1], trail[i], 1)

def draw_glow(surf, p, r, color):
    for gr in range(r+14, r, -3):
        s = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
        a = max(0, int(50*(gr-r)/14))
        pygame.draw.circle(s, (*color, a), (gr, gr), gr)
        surf.blit(s, (p[0]-gr, p[1]-gr))

def draw_hz(surf):
    hi, ho = hz_bounds()
    ri, ro = int(hi*AU_M/SCALE), int(ho*AU_M/SCALE)
    cx, cy = SIM_CX, SIM_CY
    s = pygame.Surface((SIM_W, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(s, (45,155,70,18), (cx,cy), ro)
    pygame.draw.circle(s, (0,0,0,0),      (cx,cy), ri)
    surf.blit(s, (0,0))
    pygame.draw.circle(surf, (35,120,55), (cx,cy), ro, 1)
    pygame.draw.circle(surf, (35,120,55), (cx,cy), ri, 1)

def draw_vec(surf, o, v, col, label, font, sf):
    m = float(np.linalg.norm(v))
    if m < 1e-10: return
    d = v/m; L = min(60, max(10, m*sf))
    e = (int(o[0]+d[0]*L), int(o[1]+d[1]*L))
    pygame.draw.line(surf, col, o, e, 2)
    p = np.array([-d[1], d[0]])
    t = np.array(e, float)
    pygame.draw.polygon(surf, col,
                        [e, (t-d*6+p*4).astype(int).tolist(),
                            (t-d*6-p*4).astype(int).tolist()])
    surf.blit(font.render(label, True, col), (e[0]+3, e[1]-6))

def fmt_val(v):
    if v != v or v == float('inf'): return "∞"
    a = abs(v)
    if a >= 1e12: return f"{v/1e12:.2f}T"
    if a >= 1e9:  return f"{v/1e9:.2f}G"
    if a >= 1e6:  return f"{v/1e6:.2f}M"
    if a >= 1e3:  return f"{v/1e3:.2f}k"
    if a >= 0.01: return f"{v:.4g}"
    return f"{v:.2e}"

# ─────────────────────────────────────────────────────────────────
#  LEFT PANEL — CATALOGUE
# ─────────────────────────────────────────────────────────────────
def draw_catalogue(screen, layout, scroll_y, hover_name, fb, fs, ft):
    pygame.draw.rect(screen, C_PANEL, (CAT_X, 0, CAT_W, HEIGHT))
    pygame.draw.line(screen, C_SEP, (CAT_W, 0), (CAT_W, HEIGHT), 2)
    screen.blit(fb.render("CATALOGUE", True, C_ACCENT), (CAT_X+PAD, 8))
    screen.blit(ft.render("click to add", True, C_DIM), (CAT_X+PAD, 22))
    pygame.draw.line(screen, C_SEP, (CAT_X, 32), (CAT_W, 32), 1)

    clip = pygame.Rect(CAT_X, 34, CAT_W, HEIGHT-34)
    screen.set_clip(clip)
    for item in layout:
        r = item["rect"].move(0, 34-scroll_y)
        if r.bottom < 34 or r.top > HEIGHT: continue
        if item["type"] == "cat":
            pygame.draw.rect(screen, (10,16,32), r)
            screen.blit(ft.render(item["label"].upper(), True, (55,85,140)),
                        (r.x+PAD, r.y+4))
        else:
            nm, dat = item["name"], item["data"]
            hov = nm == hover_name
            bg  = (22, 33, 58) if hov else (11, 16, 32)
            pygame.draw.rect(screen, bg, r, border_radius=3)
            if hov:
                pygame.draw.rect(screen, C_ACCENT, r, 1, border_radius=3)
            pygame.draw.circle(screen, dat["color"], (r.x+10, r.y+ITEM_H//2), 5)
            screen.blit(fs.render(nm, True, C_TEXT),  (r.x+20, r.y+3))
            screen.blit(ft.render(f"{dat['mass']:.1e}kg", True, C_LABEL), (r.x+20, r.y+17))
    screen.set_clip(None)

# ─────────────────────────────────────────────────────────────────
#  RIGHT PANEL — OBJECTS IN ORBIT + EVENTS
# ─────────────────────────────────────────────────────────────────
def draw_right_panel(screen, bodies, selected, vd,
                     star_mass_sl, star_rad_sl,
                     event_log, paused, dt_mult,
                     fb, fs, ft):

    x0 = VAR_X
    pygame.draw.rect(screen, C_PANEL, (x0, 0, VAR_W, HEIGHT))
    pygame.draw.line(screen, C_SEP, (x0, 0), (x0, HEIGHT), 2)
    W = VAR_W - PAD*2
    y = 8

    # ── STAR ────────────────────────────────────────────────────
    stype, scol = star_type()
    screen.blit(fb.render("STAR", True, C_ACCENT), (x0+PAD, y)); y += 16
    pygame.draw.circle(screen, scol, (x0+PAD+6, y+6), 6)
    screen.blit(fs.render(stype, True, scol), (x0+PAD+18, y)); y += 15
    lum = lum_ratio()
    m_r = star["mass"]/SUN_MASS_REAL
    screen.blit(ft.render(f"M={m_r:.3f}M☉  L={lum:.3f}L☉", True, C_LABEL), (x0+PAD, y)); y += 13
    star_mass_sl.draw(screen, fs, ft); y = star_mass_sl.rect.y + 22
    star_rad_sl.draw(screen, fs, ft);  y = star_rad_sl.rect.y  + 16
    screen.blit(ft.render("S — reset star", True, (50,75,115)), (x0+PAD, y)); y += 14

    pygame.draw.line(screen, C_SEP, (x0+4, y), (x0+VAR_W-4, y)); y += 7

    # ── SELECTED OBJECT VARS ───────────────────────────────────
    screen.blit(fb.render("SELECTED OBJECT", True, C_ACCENT), (x0+PAD, y)); y += 15

    if selected and vd:
        c = selected.color
        pygame.draw.circle(screen, c, (x0+PAD+6, y+6), 6)
        screen.blit(fs.render(selected.name, True, c), (x0+PAD+18, y)); y += 14
        screen.blit(ft.render(f"mass={selected.mass:.2e}kg", True, C_LABEL), (x0+PAD, y)); y += 12

        def row(label, val, unit, hi=False, warn=False, dim=False):
            nonlocal y
            cv = C_ORANGE if warn else (C_GREEN if hi else (C_DIM if dim else C_TEXT))
            screen.blit(ft.render(label, True, C_LABEL),         (x0+PAD, y))
            screen.blit(fs.render(fmt_val(val), True, cv),        (x0+138, y))
            screen.blit(ft.render(unit, True, C_DIM),             (x0+210, y))
            y += 13

        row("Distance",     vd["r_au"],     "AU",     hi=True)
        row("Speed",        vd["v_actual"], "km/s",   hi=True)
        row("v_circular",   vd["v_circ"],   "km/s",   dim=True)
        row("v_escape",     vd["v_esc"],    "km/s",   dim=True)
        row("Period",       vd["T_yr"],     "years")
        row("Grav. force",  vd["F_grav"],   "N")
        row("Orbital E",    vd["E_spec"],   "MJ/kg",
            warn=(not vd["bound"]), hi=vd["bound"])

        # Bound/unbound badge
        if vd["bound"]:
            pygame.draw.rect(screen,(15,55,28),(x0+PAD,y,80,15),border_radius=3)
            pygame.draw.rect(screen,C_GREEN,(x0+PAD,y,80,15),1,border_radius=3)
            screen.blit(ft.render("⬤ BOUND",True,C_GREEN),(x0+PAD+4,y+2))
        else:
            pygame.draw.rect(screen,(60,15,15),(x0+PAD,y,90,15),border_radius=3)
            pygame.draw.rect(screen,C_RED,(x0+PAD,y,90,15),1,border_radius=3)
            screen.blit(ft.render("↗ ESCAPING",True,C_RED),(x0+PAD+4,y+2))
        bx = x0+PAD + (86 if vd["bound"] else 96)
        if vd.get("in_hz"):
            pygame.draw.rect(screen,(15,55,28),(bx,y,85,15),border_radius=3)
            pygame.draw.rect(screen,C_HZ,(bx,y,85,15),1,border_radius=3)
            screen.blit(ft.render("🌿 HZ",True,C_HZ),(bx+4,y+2))
        if not vd.get("above_roche",True):
            bx2 = bx + (91 if vd.get("in_hz") else 0)
            pygame.draw.rect(screen,(60,12,12),(bx2,y,82,15),border_radius=3)
            pygame.draw.rect(screen,C_RED,(bx2,y,82,15),1,border_radius=3)
            screen.blit(ft.render("☠ ROCHE",True,C_RED),(bx2+4,y+2))
        y += 20

        row("Surface g",    vd["g_surf"],   "m/s²")
        row("Hill sphere",  vd["hill_au"],  "AU")
        row("vs 1-AU v",    vd["vs_v"],     "×",      dim=True)
    else:
        screen.blit(ft.render("click a body in sim", True, C_DIM), (x0+PAD, y)); y += 13

    pygame.draw.line(screen, C_SEP, (x0+4, y+2), (x0+VAR_W-4, y+2)); y += 9

    # ── BODIES IN SIMULATION ────────────────────────────────────
    guests = [b for b in bodies if not b.is_sun and not b.is_bg]
    screen.blit(fb.render(f"IN ORBIT ({len(guests)} added)", True, C_ACCENT),
                (x0+PAD, y)); y += 15

    for b in guests[:8]:   # show up to 8
        pygame.draw.circle(screen, b.color, (x0+PAD+6, y+5), 5)
        label = b.name[:20]
        r_au  = b.dist_to(bodies[0]) / AU_M
        E     = specific_energy(b, bodies[0])
        status_col = C_GREEN if E < 0 else C_RED
        screen.blit(ft.render(label, True, b.color), (x0+PAD+16, y))
        screen.blit(ft.render(f"{r_au:.2f}AU", True, status_col), (x0+200, y))
        y += 12
    if len(guests) > 8:
        screen.blit(ft.render(f"  … +{len(guests)-8} more", True, C_DIM), (x0+PAD, y))
        y += 12

    pygame.draw.line(screen, C_SEP, (x0+4, y+2), (x0+VAR_W-4, y+2)); y += 9

    # ── COLLISION LOG ───────────────────────────────────────────
    screen.blit(fb.render("COLLISION LOG", True, C_MERGE), (x0+PAD, y)); y += 15
    if event_log:
        for evt in event_log[:6]:
            screen.blit(ft.render(f"⚡ {evt}", True, C_MERGE), (x0+PAD, y))
            y += 12
    else:
        screen.blit(ft.render("no collisions yet", True, C_DIM), (x0+PAD, y))
        y += 12

    pygame.draw.line(screen, C_SEP, (x0+4, y+2), (x0+VAR_W-4, y+2)); y += 9

    # ── CONTROLS ────────────────────────────────────────────────
    ctrl = [
        (f"{'⏸ PAUSED' if paused else '▶ RUNNING'}",
         (255,170,50) if paused else (50,205,105)),
        (f"Time ×{dt_mult:.2f}   Bodies:{len(bodies)}", (90,130,180)),
        ("", None),
        ("Click cat. → add object",     C_DIM),
        ("Right-click body → remove",   C_DIM),
        ("Click body → inspect",        C_DIM),
        ("C → clear added objects",     C_DIM),
        ("V vel  F force  H HZ",        C_DIM),
        ("SPC pause  +/- speed",        C_DIM),
        ("S star reset  R full reset",  C_DIM),
    ]
    for txt, col in ctrl:
        if col: screen.blit(ft.render(txt, True, col), (x0+PAD, y))
        y += 13

# ─────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Orbital Observatory — N-Body Chaos")
    clock  = pygame.time.Clock()

    fb = pygame.font.SysFont("monospace", 12, bold=True)
    fs = pygame.font.SysFont("monospace", 12)
    ft = pygame.font.SysFont("monospace", 10)

    bodies    = build_system()
    cat_layout, cat_total = build_cat_layout()
    event_log = []

    SL_X = VAR_X + PAD
    SL_W = VAR_W - PAD*2
    star_mass_sl = Slider(SL_X, 88,  SL_W, 0.08, 50.0, 1.0,
                          "Star mass (M☉)",   "{:.3f} M☉", log=True, color=C_STAR_SL)
    star_rad_sl  = Slider(SL_X, 132, SL_W, 0.05,100.0, 1.0,
                          "Star radius (R☉)", "{:.3f} R☉", log=True, color=(255,130,55))
    all_sl = [star_mass_sl, star_rad_sl]

    # Track how many times each name has been added (for angle offset)
    add_count   = {}
    selected    = None
    vd          = {}
    scroll_y    = 0
    hover_name  = None
    show_vel    = False
    show_force  = False
    paused      = False
    dt_mult     = 1.0
    show_hz     = True

    def apply_star():
        star["mass"]    = star_mass_sl.value * SUN_MASS_REAL
        star["radius"]  = star_rad_sl.value  * SUN_RADIUS_REAL
        star["density"] = obj_density(star["mass"], star["radius"])
        rebuild_star(bodies)
        reorbit_all(bodies)

    def reset_star():
        star["mass"]   = SUN_MASS_REAL
        star["radius"] = SUN_RADIUS_REAL
        star["density"]= 1408.0
        star_mass_sl.value = 1.0
        star_rad_sl.value  = 1.0
        apply_star()

    running = True
    while running:
        mx, my = pygame.mouse.get_pos()

        hover_name = None
        if mx < CAT_W and my > 34:
            for item in cat_layout:
                r = item["rect"].move(0, 34-scroll_y)
                if item["type"] == "item" and r.collidepoint(mx, my):
                    hover_name = item["name"]

        # ── Events ──────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                k = event.key
                if   k == pygame.K_ESCAPE: running = False
                elif k == pygame.K_v:      show_vel   = not show_vel
                elif k == pygame.K_f:      show_force = not show_force
                elif k == pygame.K_SPACE:  paused     = not paused
                elif k == pygame.K_h:      show_hz    = not show_hz
                elif k == pygame.K_s:      reset_star()
                elif k == pygame.K_c:
                    # Clear all added (non-bg, non-sun) bodies
                    bodies[:] = [b for b in bodies if b.is_sun or b.is_bg]
                    init_acc(bodies)
                    selected = None; vd = {}
                    add_count.clear()
                elif k == pygame.K_r:
                    star["mass"]=SUN_MASS_REAL; star["radius"]=SUN_RADIUS_REAL
                    star["density"]=1408.0
                    star_mass_sl.value=1.0; star_rad_sl.value=1.0
                    bodies.clear(); bodies.extend(build_system())
                    event_log.clear(); selected=None; vd={}; add_count.clear()
                elif k in (pygame.K_EQUALS, pygame.K_PLUS):
                    dt_mult = min(dt_mult*2, 64.0)
                elif k == pygame.K_MINUS:
                    dt_mult = max(dt_mult/2, 0.125)

            elif event.type == pygame.MOUSEWHEEL:
                if mx < CAT_W:
                    scroll_y = max(0, min(scroll_y - event.y*18,
                                         max(0, cat_total - HEIGHT + 34)))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Catalogue click → add object
                if event.button == 1 and mx < CAT_W and my > 34:
                    for item in cat_layout:
                        r = item["rect"].move(0, 34-scroll_y)
                        if item["type"] == "item" and r.collidepoint(mx, my):
                            nm  = item["name"]
                            cnt = add_count.get(nm, 0)
                            add_count[nm] = cnt + 1
                            # Spread multiple copies evenly around orbit
                            angle = cnt * 37 + 15   # 37° offset per copy
                            b = add_object(bodies, nm, item["data"], angle)
                            selected = b
                            break

                # Click in sim → select body
                elif event.button == 1 and SIM_X <= mx < SIM_X+SIM_W:
                    sim_mx = mx - SIM_X
                    selected = None; vd = {}
                    for b in bodies:
                        p = b.px()
                        if math.hypot(p[0]-sim_mx, p[1]-my) <= max(b.radius+5, 9):
                            selected = b
                            break

                # Right-click in sim → remove body
                elif event.button == 3 and SIM_X <= mx < SIM_X+SIM_W:
                    sim_mx = mx - SIM_X
                    for b in bodies[:]:
                        if b.is_sun: continue
                        p = b.px()
                        if math.hypot(p[0]-sim_mx, p[1]-my) <= max(b.radius+6, 10):
                            bodies.remove(b)
                            init_acc(bodies)
                            if selected and selected is b:
                                selected = None; vd = {}
                            break

                # Star sliders
                elif event.button == 1 and mx >= VAR_X:
                    for sl in all_sl:
                        if sl.hit(mx, my) or sl.track_hit(mx, my):
                            sl.drag = True; sl.update(mx)

            elif event.type == pygame.MOUSEBUTTONUP:
                for sl in all_sl: sl.drag = False

            elif event.type == pygame.MOUSEMOTION:
                changed = False
                for sl in all_sl:
                    if sl.drag:
                        sl.update(mx); changed = True
                if changed: apply_star()

        # Update selected vars every frame
        if selected and selected in bodies:
            vd = compute_vars(selected, bodies[0])
        elif selected not in bodies:
            selected = None; vd = {}

        # ── Physics ─────────────────────────────────────────────
        if not paused:
            step_verlet(bodies, DT_BASE * dt_mult)

            for b in bodies:
                b.flash = max(0, b.flash - 1)
                p = b.px()
                b.trail.append(p)
                if len(b.trail) > TRAIL: b.trail.pop(0)

            process_collisions(bodies, event_log)

            # Selected body removed by collision/ejection
            if selected and selected not in bodies:
                selected = None; vd = {}

        # ── Draw simulation ──────────────────────────────────────
        sim = screen.subsurface(pygame.Rect(SIM_X, 0, SIM_W, HEIGHT))
        sim.fill(C_BG)

        for (sx,sy), b in starfield():
            sim.set_at((sx,sy), (b,b,b))

        if show_hz:
            draw_hz(sim)
            hi, ho = hz_bounds()
            sim.blit(ft.render(f"🌿 HZ {hi:.2f}–{ho:.2f} AU",
                                True, (35,115,50)), (6, HEIGHT-16))

        for b in bodies:
            draw_trail(sim, b.trail, b.color)

        for b in bodies:
            p = b.px()
            if not (0 <= p[0] < SIM_W and 0 <= p[1] < HEIGHT): continue

            if b.is_sun:
                draw_glow(sim, p, b.radius, b.color)

            # Merge flash — bright white ring
            if b.flash > 0:
                alpha = int(255 * b.flash / 20)
                s = pygame.Surface((b.radius*4, b.radius*4), pygame.SRCALPHA)
                pygame.draw.circle(s, (*C_MERGE, alpha),
                                   (b.radius*2, b.radius*2), b.radius*2, 3)
                sim.blit(s, (p[0]-b.radius*2, p[1]-b.radius*2))

            # Selected highlight
            if b is selected:
                pygame.draw.circle(sim, (255,255,255), p, b.radius+5, 1)

            pygame.draw.circle(sim, b.color, p, b.radius)

            if show_vel and not b.is_sun:
                draw_vec(sim, p, b.vel, (80,220,120), "v", ft, 1.8e-3)
            if show_force and not b.is_sun:
                draw_vec(sim, p, b.mass*b.acc, (220,80,80), "F", ft, 3e-22)

            if b.radius >= 5 or b is selected:
                sim.blit(fs.render(b.name, True, b.color),
                         (p[0]+b.radius+3, p[1]-6))

        # ── Draw panels ──────────────────────────────────────────
        draw_catalogue(screen, cat_layout, scroll_y, hover_name, fb, fs, ft)
        draw_right_panel(screen, bodies, selected, vd,
                         star_mass_sl, star_rad_sl,
                         event_log, paused, dt_mult, fb, fs, ft)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()