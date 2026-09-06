# ============================================================================
# heroes/thalgryn_fx.py
# ----------------------------------------------------------------------------
# THALGRYN "THE SHAPE OF WATER" — LAPISAN FX HIDUP v4 (TOTAL REWRITE).
#
# Modul ini memegang SEMUA efek yang hidup di luar sprite cache:
#   * partikel air ber-POOL (droplet, percikan, busa, kabut, spark, shard)
#   * pita tebasan bilah (SwingTrail) dari histori UJUNG BILAH sungguhan
#   * proyektil Water Spear (core 3 lapis + trail + after-image + impact)
#   * ImpactFX (flash + shockwave ring + serpihan + droplet + kabut)
#   * SkillFX Q/W/E/R dengan sequence 4 fase:
#         PHASE 1 ANTICIPATION -> PHASE 2 CAST -> PHASE 3 IMPACT ->
#         PHASE 4 RECOVERY
#   * klon air (R) diambil dari silhouette renderer asli (bukan blob telur)
#   * hit-stop & screen shake lewat bus SHARED heroes/combat_feel.py
#
# 100% prosedural: tidak ada PNG / sprite sheet / image loader.
#
# ── PERFORMANCE ────────────────────────────────────────────────────────────
#   * partikel & proyektil & impact & skill semuanya POOLED (free-list),
#     tidak ada alokasi objek per frame;
#   * surface glow / ring / spark di-cache (LRU kecil) bukan dibuat ulang;
#   * partikel digambar sebagai kluster pixel integer (rect 1-3 px), bukan
#     lingkaran AA per partikel;
#   * semua cap dihormati (MAX_PARTICLES / MAX_PROJECTILES / MAX_IMPACTS /
#     MAX_SKILLS) sehingga combat ramai tidak menurunkan FPS.
#
# ── KONTRAK (dikunci tools/test_thalgryn_rewrite.py) ──────────────────────
#   attach / owns / tick / reset_all / total_particles / director_for /
#   draw_ground_layer / draw_live_layer / notify_melee_impact /
#   notify_projectile_impact / notify_skill_impact / notify_skill_cast /
#   draw_water_spear / draw_debug_overlay / hit_stop / shake.
#   SKILL_DUR & MELEE_REACH sinkron dengan renderer & AI boss.
# ============================================================================

import math
import random

import pygame

try:
    from heroes import combat_feel as _feel
except Exception:                                      # pragma: no cover
    _feel = None

#: Master switch lapisan FX Thalgryn.
THALGRYN_FX_ENABLED = True

#: overlay debug (hitbox / state / partikel)
DEBUG_CHARACTER = False

# ── anggaran & batas ───────────────────────────────────────────────────────
MAX_PARTICLES = 102
MAX_PROJECTILES = 9
TRAIL_SAMPLES = 9
MAX_IMPACTS = 4
MAX_SKILLS = 2

#: jarak (piksel dunia) tebasan bilah vs lemparan spear
MELEE_REACH = 78

#: durasi status skill (frame) — sinkron base_boss & hero_skills
SKILL_DUR = {"q": 60, "w": 50, "e": 60, "r": 80}

#: batas total timeline SkillFX (detik)
SKILL_TOTAL = {"q": 0.95, "w": 0.95, "e": 1.0, "r": 1.35}

#: radius efek skill (piksel dunia)
WORLD_RADIUS = {"q": 130, "w": 90, "e": 115, "r": 185}

ANIM_PRIORITY = {
    "IDLE": 0, "WALK": 10, "RUN": 15, "CHARGE": 30, "CAST": 35,
    "ATTACK": 40, "SWING": 45, "SKILL": 50, "SPECIAL": 55,
    "HIT": 60, "HURT": 65, "DEATH": 100,
}

# ============================================================================
# 1. PALETTE (disinkronkan dari renderer v4)
# ============================================================================
P = {
    "water_darkest": (10, 36, 54),
    "water_dark": (16, 62, 88),
    "water_mid": (28, 108, 138),
    "water_light": (58, 160, 186),
    "water_high": (112, 208, 222),
    "water_shine": (178, 240, 246),
    "water_white": (235, 255, 255),
    "core_dark": (22, 96, 128),
    "core_mid": (52, 176, 205),
    "core_light": (126, 232, 246),
    "core_hot": (210, 252, 255),
    "blade_dark": (18, 74, 102),
    "blade_mid": (40, 138, 168),
    "blade_light": (96, 202, 220),
    "blade_shine": (196, 246, 250),
    "eye_mid": (96, 214, 226),
    "eye_bright": (186, 248, 252),
    "eye_hot": (240, 255, 255),
    "gold_dark": (74, 48, 12),
    "gold_mid": (150, 104, 28),
    "gold_light": (216, 166, 54),
    "str_red": (200, 40, 40),
    "str_hot": (255, 100, 90),
    "agi_green": (60, 190, 70),
    "agi_hot": (140, 240, 120),
    "int_blue": (50, 130, 220),
    "int_hot": (140, 200, 255),
    "fx_dark": (10, 40, 60),
    "fx_mid": (40, 138, 168),
    "fx_bright": (112, 208, 222),
    "fx_light": (178, 240, 246),
    "fx_hot": (235, 255, 255),
    "white": (255, 255, 255),
}


def _sync_palette():
    """Salin nilai palette renderer v4 ke P (satu sumber kebenaran)."""
    try:
        from bosses.thalgryn_v4 import PALETTE as RP
    except Exception:                                      # pragma: no cover
        return
    for k in tuple(P.keys()):
        v = RP.get(k)
        if v is not None:
            P[k] = tuple(int(c) for c in v)


_sync_palette()


# ============================================================================
# 2. UTIL KECIL
# ============================================================================
def _renderer():
    try:
        from bosses.thalgryn_v4 import _NS_thalgryn as G
        return G
    except Exception:                                      # pragma: no cover
        return None


def _clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else (hi if v > hi else v)


def _mix(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def _hash01(seed):
    x = math.sin(seed * 127.1) * 43758.5453
    return x - math.floor(x)


def render_scale(boss):
    v = getattr(boss, "_render_scale", None)
    try:
        return float(v) if v else 1.0
    except (TypeError, ValueError):
        return 1.0


def pose_of(boss):
    G = _renderer()
    p = getattr(boss, "_th_pose", None)
    if p is None and G is not None:
        try:
            p = G.solve_pose(boss)
        except Exception:                                  # pragma: no cover
            p = None
    return p


def tip_screen(boss, x, y):
    G = _renderer()
    if G is None:
        return (x + 20, y - 30)
    try:
        return G._tip_screen(boss, x, y)
    except Exception:                                      # pragma: no cover
        return (x + 20, y - 30)


def grip_screen(boss, x, y):
    G = _renderer()
    if G is None:
        return (x + 7, y - 26)
    try:
        return G._grip_screen(boss, x, y)
    except Exception:                                      # pragma: no cover
        return (x + 7, y - 26)


def _quality():
    try:
        from mobile.perf import Quality as Q
        return Q
    except Exception:
        return None


def particle_budget():
    q = _quality()
    ratio = 1.0
    if q is not None:
        try:
            ratio = float(getattr(q, "particle_ratio", 1.0))
        except Exception:                                  # pragma: no cover
            ratio = 1.0
    return max(0.25, min(1.0, ratio))


def glow_allowed():
    q = _quality()
    if q is None:
        return True
    return not bool(getattr(q, "cheap_alpha", False))


# ============================================================================
# 3. CACHE SURFACE FX (glow / ring / spark) — LRU kecil, tanpa alokasi frame
# ============================================================================
_FX_CACHE = {}
_FX_CACHE_MAX = 96


def _cache_put(key, surf):
    if len(_FX_CACHE) >= _FX_CACHE_MAX:
        _FX_CACHE.clear()
    _FX_CACHE[key] = surf
    return surf


def clear_cache():
    _FX_CACHE.clear()


def cache_size():
    return len(_FX_CACHE)


def glow_surface(radius, color, power=1.0):
    """Radial glow lembut ter-cache (dipakai flash & aura)."""
    radius = max(2, int(radius))
    key = ("g", radius, tuple(color), round(power, 2))
    s = _FX_CACHE.get(key)
    if s is not None:
        return s
    d = radius * 2
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    cx = cy = radius
    steps = max(3, radius // 2)
    for i in range(steps, 0, -1):
        t = i / float(steps)
        a = int(150 * power * (1.0 - t) ** 1.8)
        if a <= 0:
            continue
        col = _mix(color, (255, 255, 255), (1.0 - t) * 0.55)
        pygame.draw.circle(s, col + (a,), (cx, cy), max(1, int(radius * t)))
    return _cache_put(key, s)


def spark_surface(size, color):
    """Bintang spark 4 arah (pixel crisp)."""
    size = max(2, int(size))
    key = ("s", size, tuple(color))
    s = _FX_CACHE.get(key)
    if s is not None:
        return s
    d = size * 2 + 1
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    c = size
    col = tuple(color) + (255,)
    pygame.draw.line(s, col, (c - size, c), (c + size, c), 1)
    pygame.draw.line(s, col, (c, c - size), (c, c + size), 1)
    if size >= 3:
        h = size // 2
        pygame.draw.line(s, col, (c - h, c - h), (c + h, c + h), 1)
        pygame.draw.line(s, col, (c - h, c + h), (c + h, c - h), 1)
    s.set_at((c, c), (255, 255, 255, 255))
    return _cache_put(key, s)


def ring_surface(radius, thickness, color, alpha=255):
    radius = max(2, int(radius))
    thickness = max(1, int(thickness))
    key = ("r", radius, thickness, tuple(color), alpha)
    s = _FX_CACHE.get(key)
    if s is not None:
        return s
    d = (radius + thickness) * 2
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    c = radius + thickness
    pygame.draw.circle(s, tuple(color) + (alpha,), (c, c), radius, thickness)
    return _cache_put(key, s)


def ellipse_ring_surface(rx, ry, thickness, color, alpha=200):
    rx = max(2, int(rx))
    ry = max(1, int(ry))
    key = ("e", rx, ry, thickness, tuple(color), alpha)
    s = _FX_CACHE.get(key)
    if s is not None:
        return s
    w = (rx + 2) * 2
    h = (ry + 2) * 2
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, tuple(color) + (alpha,), (2, 2, rx * 2, ry * 2),
                        max(1, thickness))
    return _cache_put(key, s)


def _blit_faded(surface, surf, cx, cy, alpha=255):
    if alpha >= 255:
        surface.blit(surf, (int(cx - surf.get_width() // 2),
                            int(cy - surf.get_height() // 2)))
        return
    if alpha <= 0:
        return
    tmp = surf.copy()
    tmp.set_alpha(int(alpha))
    surface.blit(tmp, (int(cx - surf.get_width() // 2),
                       int(cy - surf.get_height() // 2)))


# ============================================================================
# 4. PARTICLE SYSTEM (pooled)
# ============================================================================
K_DOT, K_SPARK, K_SHARD, K_DROP, K_SMOK, K_BUBB = 0, 1, 2, 3, 4, 5


class Particle(object):
    __slots__ = ("alive", "x", "y", "vx", "vy", "age", "life", "size",
                 "color", "kind", "grav", "drag", "spin", "ang", "fade")

    def __init__(self):
        self.alive = False
        self.x = self.y = self.vx = self.vy = 0.0
        self.age = self.life = 0.0
        self.size = 1
        self.color = (255, 255, 255)
        self.kind = K_DOT
        self.grav = 0.0
        self.drag = 0.0
        self.spin = 0.0
        self.ang = 0.0
        self.fade = 1.0


class ParticleSystem(object):
    """Pool partikel fixed-size: spawn memakai ulang slot mati."""

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = cap
        self.pool = [Particle() for _ in range(cap)]
        self._cursor = 0

    def count(self):
        n = 0
        for p in self.pool:
            if p.alive:
                n += 1
        return n

    def clear(self):
        for p in self.pool:
            p.alive = False

    def spawn(self, x, y, vx, vy, life, size, color, kind=K_DOT,
              grav=0.0, drag=0.0, spin=0.0, fade=1.0):
        p = None
        for _ in range(self.cap):
            cand = self.pool[self._cursor]
            self._cursor = (self._cursor + 1) % self.cap
            if not cand.alive:
                p = cand
                break
        if p is None:
            # pool penuh: ganti partikel tertua (umur terbesar)
            best = self.pool[0]
            br = -1.0
            for cand in self.pool:
                r = cand.age / max(0.001, cand.life)
                if r > br:
                    br = r
                    best = cand
            p = best
        p.alive = True
        p.x = float(x)
        p.y = float(y)
        p.vx = float(vx)
        p.vy = float(vy)
        p.age = 0.0
        p.life = max(0.05, float(life))
        p.size = max(1, int(size))
        p.color = tuple(int(c) for c in color)
        p.kind = kind
        p.grav = float(grav)
        p.drag = float(drag)
        p.spin = float(spin)
        p.ang = 0.0
        p.fade = float(fade)
        return p

    def burst(self, x, y, n, speed, color, kind=K_DOT, life=0.5, size=2,
              grav=0.0, spread=6.28318, base_ang=0.0, drag=2.0):
        n = max(1, int(n * particle_budget()))
        for i in range(n):
            a = base_ang + (random.random() - 0.5) * spread
            sp = speed * (0.45 + random.random() * 0.75)
            self.spawn(x, y, math.cos(a) * sp, math.sin(a) * sp,
                       life * (0.7 + random.random() * 0.6), size, color,
                       kind, grav=grav, drag=drag)

    def update(self, dt):
        for p in self.pool:
            if not p.alive:
                continue
            p.age += dt
            if p.age >= p.life:
                p.alive = False
                continue
            if p.drag:
                d = max(0.0, 1.0 - p.drag * dt)
                p.vx *= d
                p.vy *= d
            if p.grav:
                p.vy += p.grav * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            if p.spin:
                p.ang += p.spin * dt

    def draw(self, surface, ox=0.0, oy=0.0):
        for p in self.pool:
            if not p.alive:
                continue
            t = p.age / p.life
            a = (1.0 - t) ** p.fade
            x = int(p.x - ox)
            y = int(p.y - oy)
            if p.kind == K_DOT:
                s = p.size if t < 0.6 else max(1, p.size - 1)
                col = p.color + (int(235 * a),)
                surface.fill(col, (x - s // 2, y - s // 2, s, s))
            elif p.kind == K_SPARK:
                _blit_faded(surface, spark_surface(p.size + 1, p.color),
                            x, y, int(255 * a))
            elif p.kind == K_SHARD:
                s = max(1, p.size - int(t * 2))
                col = p.color + (int(230 * a),)
                surface.fill(col, (x - s // 2, y - s, s, s * 2))
                surface.fill(col, (x - s, y - s // 2, s * 2, s))
            elif p.kind == K_DROP:
                s = p.size
                col = p.color + (int(220 * a),)
                surface.fill(col, (x, y - s, 1, s * 2))
                surface.fill(p.color + (int(255 * a),),
                             (x - 1, y - 1, 3, 2))
            elif p.kind == K_SMOK:
                s = p.size + int(t * 3)
                col = p.color + (int(70 * a),)
                surface.fill(col, (x - s // 2, y - s // 2, s, s))
            else:  # K_BUBB
                s = p.size
                col = p.color + (int(160 * a),)
                pygame.draw.circle(surface, col, (x, y), s, 1)


# ============================================================================
# 5. SWING TRAIL — pita tebasan dari histori ujung bilah sungguhan
# ============================================================================
class SwingTrail(object):
    def __init__(self, samples=TRAIL_SAMPLES):
        self.samples = samples
        self.points = []          # [(x, y, age, power)]
        self._last_state = None

    def clear(self):
        del self.points[:]

    def sample(self, x, y, active, power=1.0, dt=1.0 / 60.0):
        if active:
            if not self.points or \
                    (abs(self.points[-1][0] - x) +
                     abs(self.points[-1][1] - y)) > 0.7:
                self.points.append([float(x), float(y), 0.0, float(power)])
                if len(self.points) > self.samples:
                    self.points.pop(0)
        for pt in self.points:
            pt[2] += dt
        while self.points and self.points[0][2] > 0.24:
            self.points.pop(0)

    def draw(self, surface, ox=0.0, oy=0.0):
        n = len(self.points)
        if n < 2:
            return
        for i in range(1, n):
            x0, y0, a0, p0 = self.points[i - 1]
            x1, y1, a1, p1 = self.points[i]
            t = i / float(n - 1)
            age = a1 / 0.24
            alpha = int(235 * (1.0 - age) ** 1.2 * t * p1)
            if alpha <= 8:
                continue
            w = max(2, int(2 + 4 * t * p1))
            col = _mix(P["blade_mid"], P["water_high"], t * 0.9)
            pygame.draw.line(surface, col + (alpha,),
                             (int(x0 - ox), int(y0 - oy)),
                             (int(x1 - ox), int(y1 - oy)), w)
            # mata pita: garis terang di tepi dalam (baca sebagai bilah)
            pygame.draw.line(surface, P["water_white"] +
                             (int(alpha * 0.85),),
                             (int(x0 - ox), int(y0 - oy) - w // 2),
                             (int(x1 - ox), int(y1 - oy) - w // 2), 1)
            # kabur air di tepi luar
            if t > 0.4:
                pygame.draw.line(surface, P["water_mid"] +
                                 (int(alpha * 0.5),),
                                 (int(x0 - ox), int(y0 - oy) + w // 2),
                                 (int(x1 - ox), int(y1 - oy) + w // 2), 1)


# ============================================================================
# 6. IMPACT FX (flash + ring + serpihan) — pooled
# ============================================================================
class ImpactFX(object):
    __slots__ = ("alive", "x", "y", "t", "dur", "power", "kind", "ang",
                 "crit")

    def __init__(self):
        self.alive = False
        self.x = self.y = 0.0
        self.t = self.dur = 0.0
        self.power = 1.0
        self.kind = "blade"
        self.ang = 0.0
        self.crit = False


class ImpactSystem(object):
    def __init__(self, cap=MAX_IMPACTS):
        self.cap = cap
        self.pool = [ImpactFX() for _ in range(cap)]
        self._cursor = 0

    def list(self):
        return [i for i in self.pool if i.alive]

    def __len__(self):
        return self.count()

    def __iter__(self):
        return iter(self.list())

    def count(self):
        return len(self.list())

    def clear(self):
        for i in self.pool:
            i.alive = False

    def spawn(self, x, y, power=1.0, kind="blade", ang=0.0, crit=False):
        fx = None
        for _ in range(self.cap):
            cand = self.pool[self._cursor]
            self._cursor = (self._cursor + 1) % self.cap
            if not cand.alive:
                fx = cand
                break
        if fx is None:
            fx = self.pool[0]
        fx.alive = True
        fx.x = float(x)
        fx.y = float(y)
        fx.t = 0.0
        fx.dur = 0.34 + 0.10 * min(2.0, power)
        fx.power = float(power)
        fx.kind = kind
        fx.ang = float(ang)
        fx.crit = bool(crit)
        return fx

    def update(self, dt):
        for fx in self.pool:
            if fx.alive:
                fx.t += dt
                if fx.t >= fx.dur:
                    fx.alive = False

    def draw(self, surface, ox=0.0, oy=0.0):
        for fx in self.pool:
            if not fx.alive:
                continue
            t = fx.t / fx.dur
            x = fx.x - ox
            y = fx.y - oy
            pw = fx.power
            # 1) flash putih panas (0..0.12)
            if t < 0.30:
                ft = t / 0.30
                r = (7 + 9 * pw) * (0.6 + 0.8 * ft)
                _blit_faded(surface, glow_surface(r, P["fx_hot"], 1.1),
                            x, y, int(255 * (1.0 - ft) ** 1.4))
            # 2) shockwave ring mengembang
            if 0.06 < t < 0.85:
                rt = (t - 0.06) / 0.79
                rr = int((6 + 26 * pw) * _ease_out(rt))
                al = int(210 * (1.0 - rt) ** 1.5)
                if rr > 1 and al > 6:
                    _blit_faded(surface,
                                ring_surface(rr, max(1, 2 - int(rt)),
                                             P["fx_bright"], 255),
                                x, y, al)
            # 3) ring dalam (air padat)
            if 0.10 < t < 0.6:
                rt = (t - 0.10) / 0.5
                rr = int((3 + 12 * pw) * _ease_out(rt))
                al = int(170 * (1.0 - rt))
                if rr > 1 and al > 6:
                    _blit_faded(surface,
                                ring_surface(rr, 1, P["water_high"], 255),
                                x, y, al)
            # 4) directional spark sepanjang arah benturan
            if t < 0.4:
                st = t / 0.4
                d = (4 + 16 * pw) * st
                for sgn in (1, -1):
                    sx = x + math.cos(fx.ang) * d * sgn
                    sy = y + math.sin(fx.ang) * d * sgn * 0.6
                    _blit_faded(surface,
                                spark_surface(2 + int(pw), P["fx_light"]),
                                sx, sy, int(220 * (1.0 - st)))


def _ease_out(t):
    t = _clamp(t, 0.0, 1.0)
    return 1.0 - (1.0 - t) * (1.0 - t)


def _ease_in(t):
    t = _clamp(t, 0.0, 1.0)
    return t * t


# ============================================================================
# 7. WATER SPEAR (proyektil) — pooled
# ============================================================================
class ThalgrynProjectile(object):
    STATE_DEAD, STATE_TRAVEL, STATE_IMPACT = 0, 1, 2

    __slots__ = ("state", "x", "y", "tx", "ty", "vx", "vy", "speed", "age",
                 "dur", "heavy", "angle", "trail_t", "crit")

    def __init__(self):
        self.state = ThalgrynProjectile.STATE_DEAD
        self.x = self.y = self.tx = self.ty = 0.0
        self.vx = self.vy = 0.0
        self.speed = 420.0
        self.age = 0.0
        self.dur = 1.4
        self.heavy = False
        self.angle = 0.0
        self.trail_t = 0.0
        self.crit = False


class ProjectileSystem(object):
    def __init__(self, cap=MAX_PROJECTILES, particles=None, director=None):
        self.cap = cap
        self.pool = [ThalgrynProjectile() for _ in range(cap)]
        self._cursor = 0
        self.particles = particles
        self.director = director

    def list(self):
        return [p for p in self.pool if p.state != p.STATE_DEAD]

    def count(self):
        return len(self.list())

    def clear(self):
        for p in self.pool:
            p.state = ThalgrynProjectile.STATE_DEAD

    def spawn(self, x, y, tx, ty, speed=420.0, heavy=False, crit=False):
        p = None
        for _ in range(self.cap):
            cand = self.pool[self._cursor]
            self._cursor = (self._cursor + 1) % self.cap
            if cand.state == cand.STATE_DEAD:
                p = cand
                break
        if p is None:
            p = self.pool[0]
        p.state = p.STATE_TRAVEL
        p.x = float(x)
        p.y = float(y)
        p.tx = float(tx)
        p.ty = float(ty)
        d = math.hypot(tx - x, ty - y) or 1.0
        p.speed = float(speed)
        p.vx = (tx - x) / d * p.speed
        p.vy = (ty - y) / d * p.speed
        p.angle = math.atan2(ty - y, tx - x)
        p.age = 0.0
        p.dur = max(0.18, d / p.speed + 0.05)
        p.heavy = bool(heavy)
        p.trail_t = 0.0
        p.crit = bool(crit)
        return p

    def update(self, dt):
        for p in self.pool:
            if p.state == p.STATE_DEAD:
                continue
            p.age += dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            # trail droplet di belakang spear
            p.trail_t += dt
            if p.trail_t > 0.02 and self.particles is not None:
                p.trail_t = 0.0
                self.particles.spawn(
                    p.x - math.cos(p.angle) * 6,
                    p.y - math.sin(p.angle) * 6,
                    -math.cos(p.angle) * 30 + random.uniform(-14, 14),
                    -math.sin(p.angle) * 30 + random.uniform(-14, 14),
                    0.28, 1, P["water_high"], K_DOT, drag=3.0)
            reached = math.hypot(p.tx - p.x, p.ty - p.y) < 10.0
            if reached or p.age >= p.dur:
                p.state = p.STATE_DEAD
                if self.director is not None:
                    self.director.on_impact(p.x, p.y, p.angle,
                                            1.5 if p.heavy else 1.0,
                                            p.crit, kind="spear")

    def draw(self, surface, ox=0.0, oy=0.0):
        for p in self.pool:
            if p.state == p.STATE_DEAD:
                continue
            draw_water_spear(surface, p.x - ox, p.y - oy, p.angle,
                             p.age, p.heavy or p.crit)


def draw_water_spear(surface, px, py, angle=0.0, age=0, crit=False,
                     scale=1.0):
    """Water Spear: kepala runcing 3 lapis + sirip belakang + kilau."""
    ca, sa = math.cos(angle), math.sin(angle)
    nx, ny = -sa, ca
    L = int(13 * scale)
    W = int(3 * scale)
    # after-image terkuantisasi (jejak gerak)
    for k, al in ((2, 110), (1, 170)):
        bx = px - ca * k * 4
        by = py - sa * k * 4
        col = P["water_high"] + (al,)
        pygame.draw.line(surface, col,
                         (int(bx - ca * L * 0.5), int(by - sa * L * 0.5)),
                         (int(bx + ca * L * 0.5), int(by + sa * L * 0.5)),
                         max(1, W - 1))
    # badan spear
    pygame.draw.line(surface, P["blade_dark"] + (255,),
                     (int(px - ca * L), int(py - sa * L)),
                     (int(px + ca * L * 0.4), int(py + sa * L * 0.4)), W)
    pygame.draw.line(surface, P["blade_mid"] + (255,),
                     (int(px - ca * L * 0.9), int(py - sa * L * 0.9)),
                     (int(px + ca * L * 0.5), int(py + sa * L * 0.5)),
                     max(1, W - 1))
    pygame.draw.line(surface, P["blade_light"] + (255,),
                     (int(px - ca * L * 0.7), int(py - sa * L * 0.7)),
                     (int(px + ca * L * 0.6), int(py + sa * L * 0.6)), 1)
    # kepala runcing
    hx, hy = px + ca * L * 0.6, py + sa * L * 0.6
    tipx, tipy = px + ca * (L * 0.6 + 7 * scale), py + sa * (L * 0.6 +
                                                             7 * scale)
    pygame.draw.polygon(surface, P["water_high"] + (255,),
                        [(int(hx + nx * W), int(hy + ny * W)),
                         (int(tipx), int(tipy)),
                         (int(hx - nx * W), int(hy - ny * W))])
    surface.set_at((int(tipx - ca), int(tipy - sa)),
                   P["water_white"] + (255,))
    # sirip belakang
    for sgn in (1, -1):
        fx = px - ca * L + nx * W * sgn
        fy = py - sa * L + ny * W * sgn
        pygame.draw.line(surface, P["water_light"] + (220,),
                         (int(fx), int(fy)),
                         (int(fx - ca * 4 + nx * 2 * sgn),
                          int(fy - sa * 4 + ny * 2 * sgn)), 1)
    if crit:
        _blit_faded(surface, glow_surface(8, P["fx_hot"], 0.8), px, py, 160)


# ============================================================================
# 8. SKILL FX — sequence 4 fase per skill
# ============================================================================
class SkillFX(object):
    """Timeline skill: ANTICIPATION -> CAST -> IMPACT -> RECOVERY.

    ``TIMELINE`` memetakan skill -> (t_ant, t_cast, t_imp, t_rec) dalam
    detik sejak cast. Dampak (flash/shockwave/hit-stop/shake) hanya
    dikeluarkan SEKALI saat memasuki fase IMPACT.
    """

    TIMELINE = {
        #        ant    cast   impact-window-start  total
        "q": (0.00, 0.14, 0.30, 0.95),
        "w": (0.00, 0.20, 0.42, 0.95),
        "e": (0.00, 0.22, 0.40, 1.00),
        "r": (0.00, 0.26, 0.50, 1.35),
    }

    __slots__ = ("skill", "x", "y", "t", "done_impact", "pending", "px",
                 "py", "radius", "seed", "cast_x", "cast_y", "spawned_proj",
                 "dead", "ix", "iy")

    def __init__(self, skill, x, y, radius=None):
        self.skill = skill
        self.x = float(x)
        self.y = float(y)
        self.cast_x = float(x)
        self.cast_y = float(y)
        self.t = 0.0
        self.done_impact = False
        self.pending = None          # (x, y) impact menunggu spear mendarat
        self.px = self.py = 0.0
        self.radius = float(radius or WORLD_RADIUS.get(skill, 110))
        self.seed = random.random() * 100.0
        self.spawned_proj = False
        self.dead = False
        self.ix = float(x)
        self.iy = float(y)

    # ------------------------------------------------------------------
    def phase(self):
        a, c, i, tot = self.TIMELINE[self.skill]
        if self.t < c:
            return "ANTICIPATION"
        if self.t < i:
            return "CAST"
        if self.t < tot - 0.18:
            return "IMPACT"
        return "RECOVERY"

    def progress(self):
        return _clamp(self.t / self.TIMELINE[self.skill][3])


# ============================================================================
# 9. DIRECTOR — satu per unit
# ============================================================================
class ThalgrynFXDirector(object):
    def __init__(self, hero):
        self.hero = hero
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.trail = SwingTrail(TRAIL_SAMPLES)
        self.impacts = ImpactSystem(MAX_IMPACTS)
        self.projectiles = ProjectileSystem(MAX_PROJECTILES,
                                            self.particles, self)
        self.skills = []
        self.x = float(getattr(hero, "x", 0.0))
        self.y = float(getattr(hero, "y", 0.0))
        self.prev_x = self.x
        self.prev_y = self.y
        self.alive = bool(getattr(hero, "alive", True))
        self.time = 0.0
        self._swing_was = False
        self._clone_t = 0.0
        self._clone_surf = None
        self._morph_t = 0.0

    # ------------------------------------------------------------------
    def clear(self):
        self.particles.clear()
        self.trail.clear()
        self.impacts.clear()
        self.projectiles.clear()
        del self.skills[:]
        self._clone_surf = None

    def stats(self):
        return {
            "particles": self.particles.count(),
            "projectiles": self.projectiles.count(),
            "impacts": self.impacts.count(),
            "skills": len(self.skills),
            "trail": len(self.trail.points),
        }

    # ------------------------------------------------------------------
    def update(self, dt, x, y):
        self.time += dt
        self.prev_x, self.prev_y = self.x, self.y
        self.x, self.y = float(x), float(y)
        boss = self.hero
        pose = pose_of(boss)
        scale = render_scale(boss)

        # ── trail dari ujung bilah sungguhan ──
        swinging = bool(getattr(boss, "_th_attack_active", False)) and \
            getattr(boss, "_th_attack_phase", "NONE") in (
                "SWING", "IMPACT", "FOLLOW")
        if pose is not None:
            tx, ty = tip_screen(boss, x, y)
            self.trail.sample(tx, ty, swinging, 1.0, dt)
            # whoosh droplet saat tebasan (tanpa impact FX: aturan proyek)
            if swinging and not self._swing_was:
                self.particles.burst(tx, ty, 2, 90 * scale,
                                     P["water_high"], K_DROP, life=0.3,
                                     size=2, grav=240, drag=1.5)
            self._swing_was = swinging

        # ── death burst (sekali) ──
        alive_now = bool(getattr(boss, "alive", True))
        if self.alive and not alive_now:
            self._death_burst(x, y, scale)
        self.alive = alive_now

        # ── systems ──
        self.particles.update(dt)
        self.projectiles.update(dt)
        self.impacts.update(dt)

        # ── skill timelines ──
        for fx in list(self.skills):
            self._update_skill(fx, dt, scale)
            fx.t += dt
            if fx.t >= fx.TIMELINE[fx.skill][3]:
                fx.dead = True
        self.skills = [s for s in self.skills if not s.dead]
        if self._clone_surf is not None:
            self._clone_t += dt
            if self._clone_t > 1.2:
                self._clone_surf = None

    # ------------------------------------------------------------------
    def _death_burst(self, x, y, scale):
        self.particles.burst(x, y - 18 * scale, 13, 150 * scale,
                             P["water_high"], K_DROP, life=0.7, size=2,
                             grav=320, drag=1.2)
        self.particles.burst(x, y - 14 * scale, 6, 90 * scale,
                             P["water_mid"], K_SMOK, life=0.9, size=3,
                             grav=-40, drag=1.6)
        self.impacts.spawn(x, y - 14 * scale, 1.4, kind="death")
        _shake(7.0, 0.30)
        _hit_stop(0.05)

    # ------------------------------------------------------------------
    # SKILL SEQUENCES
    # ------------------------------------------------------------------
    def on_cast(self, x, y, skill):
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        fx = SkillFX(skill, x, y)
        fx.cast_x, fx.cast_y = float(x), float(y)
        self.skills.append(fx)
        scale = render_scale(self.hero)
        if skill == "q":
            # surge: jejak dari posisi SEBELUM teleport (director masih
            # menyimpan posisi frame terakhir = posisi lama)
            ox_, oy_ = self.x, self.y
            nx_, ny_ = float(getattr(self.hero, "x", x)), \
                float(getattr(self.hero, "y", y))
            dx = nx_ - ox_
            dy = ny_ - oy_
            d = math.hypot(dx, dy)
            if d > 8.0:
                n = int(min(14, d / 9.0))
                for i in range(n):
                    t = i / float(max(1, n - 1))
                    px_ = ox_ + dx * t
                    py_ = oy_ + dy * t - 16 * scale
                    self.particles.spawn(px_, py_,
                                         random.uniform(-20, 20),
                                         random.uniform(-40, -10),
                                         0.4 + 0.2 * t, 2,
                                         P["water_high"], K_DROP,
                                         grav=200, drag=1.4)
                self.impacts.spawn(ox_, oy_ - 10 * scale, 0.8, kind="surge")
            fx.x, fx.y = nx_, ny_
            fx.cast_x, fx.cast_y = nx_, ny_
        elif skill == "r":
            G = _renderer()
            art = None
            if G is not None:
                try:
                    art = G.last_art(self.hero)
                except Exception:                          # pragma: no cover
                    art = None
            if art is not None:
                try:
                    self._clone_surf = art.copy()
                    # dorong RGB ke cyan air (silhouette "clone air")
                    self._clone_surf.fill((36, 148, 186, 255),
                                          special_flags=pygame.BLEND_RGB_MAX)
                    # turunkan alpha saja (RGB tetap) supaya translusen
                    self._clone_surf.fill((255, 255, 255, 140),
                                          special_flags=pygame.BLEND_RGBA_MIN)
                    self._clone_t = 0.0
                except Exception:                          # pragma: no cover
                    self._clone_surf = None

    # ------------------------------------------------------------------
    def _update_skill(self, fx, dt, scale):
        sk = fx.skill
        a, c, imp, tot = fx.TIMELINE[sk]
        t = fx.t
        x, y = fx.cast_x, fx.cast_y
        boss = self.hero
        facing = 1 if int(getattr(boss, "direction", 1) or 1) >= 0 else -1

        # ═══ PHASE 1 — ANTICIPATION ═══
        if t < c:
            k = t / max(0.001, c)
            if sk == "q":
                # air menyusut ke telapak: partikel konvergen
                if random.random() < 0.9:
                    aa = random.random() * 6.283
                    rr = (26 + 14 * (1 - k)) * scale
                    self.particles.spawn(
                        x + math.cos(aa) * rr, y - 14 * scale +
                        math.sin(aa) * rr * 0.5,
                        -math.cos(aa) * 70 * scale,
                        -math.sin(aa) * 36 * scale,
                        0.3, 2, P["water_light"], K_DOT, drag=0.0)
            elif sk == "w":
                # mote konvergen ke ujung bilah + charge ring
                tx, ty = tip_screen(boss, self.x, self.y)
                if random.random() < 0.95:
                    aa = random.random() * 6.283
                    rr = (14 + 10 * (1 - k)) * scale
                    self.particles.spawn(
                        tx + math.cos(aa) * rr, ty + math.sin(aa) * rr,
                        -math.cos(aa) * 90 * scale,
                        -math.sin(aa) * 90 * scale,
                        0.22, 2, P["core_light"], K_DOT, drag=0.0)
            elif sk == "e":
                # kolom air naik: bubble + mote spiral
                if random.random() < 0.95:
                    aa = t * 9.0 + random.random() * 2
                    rr = (10 + 6 * math.sin(t * 5)) * scale
                    self.particles.spawn(
                        x + math.cos(aa) * rr, y - 4 * scale,
                        math.cos(aa + 1.57) * 30, -120 * scale,
                        0.5, 2, P["water_high"], K_BUBB, drag=0.4)
            else:  # r
                # 3 puddle muncul + droplet naik
                if random.random() < 0.9:
                    i = random.randint(0, 2)
                    aa = (i * 2.094) + 0.6
                    rr = 34 * scale
                    self.particles.spawn(
                        x + math.cos(aa) * rr, y - 2 * scale,
                        0, -90 * scale, 0.4, 2, P["water_light"],
                        K_DROP, grav=180, drag=0.6)
            return

        # ═══ PHASE 2 — CAST ═══
        if t < imp:
            k = (t - c) / max(0.001, imp - c)
            if sk == "q":
                # jet air ke belakang + wedge depan
                if random.random() < 0.85:
                    self.particles.spawn(
                        x - facing * (8 + 10 * k) * scale,
                        y - 16 * scale + random.uniform(-6, 6),
                        -facing * (140 + 90 * k) * scale,
                        random.uniform(-30, 30),
                        0.3, 2, P["water_high"], K_DROP, drag=2.0)
            elif sk == "w":
                if not fx.spawned_proj:
                    fx.spawned_proj = True
                    gx, gy = tip_screen(boss, self.x, self.y)
                    tx, ty = self._target_world()
                    self.projectiles.spawn(gx, gy, tx, ty,
                                           speed=520.0 * max(0.6, scale),
                                           heavy=True)
                    # muzzle flash + recoil droplet
                    self.impacts.spawn(gx, gy, 0.55, kind="muzzle")
                    self.particles.burst(gx, gy, 4, 120 * scale,
                                         P["water_shine"], K_SPARK,
                                         life=0.25, size=2, drag=2.5)
                    _shake(3.0, 0.14)
            elif sk == "e":
                # kolom air naik makin cepat menjelang release
                if random.random() < 0.8:
                    aa = random.random() * 6.283
                    self.particles.spawn(
                        x + math.cos(aa) * 6 * scale,
                        y - (10 + 26 * k) * scale,
                        math.cos(aa) * 60 * scale, -60 * scale,
                        0.45, 2, P["core_light"], K_DOT, grav=-60,
                        drag=1.2)
            else:  # r
                # klon melesat keluar (visual di draw_front)
                if random.random() < 0.7:
                    i = random.randint(0, 2)
                    aa = i * 2.094 + 0.6
                    rr = (20 + 40 * k) * scale
                    self.particles.spawn(
                        x + math.cos(aa) * rr, y - 16 * scale,
                        math.cos(aa) * 60, -20, 0.35, 2,
                        P["water_high"], K_DROP, grav=160, drag=1.2)
            return

        # ═══ PHASE 3 — IMPACT (sekali) ═══
        if not fx.done_impact:
            fx.done_impact = True
            ix, iy = fx.pending or (x, y)
            fx.ix, fx.iy = ix, iy
            self._skill_impact(fx, ix, iy, scale)
            fx.pending = None
            return

        # ═══ PHASE 4 — RECOVERY ═══
        k = _clamp((t - imp) / max(0.001, tot - imp))
        ix, iy = fx.ix, fx.iy
        if random.random() < 0.35 * (1.0 - k):
            aa = random.random() * 6.283
            rr = fx.radius * 0.5 * (1.0 - k) * scale
            self.particles.spawn(
                ix + math.cos(aa) * rr, iy - 6 * scale +
                math.sin(aa) * rr * 0.4,
                math.cos(aa) * 20, -50 * (1 - k),
                0.5, 1, P["water_light"], K_DROP, grav=220, drag=1.0)

    # ------------------------------------------------------------------
    def _skill_impact(self, fx, ix, iy, scale):
        sk = fx.skill
        r = fx.radius * scale
        if sk == "q":
            self.impacts.spawn(ix, iy - 12 * scale, 1.5, kind="wave")
            self.particles.burst(ix, iy - 12 * scale, 10, 190 * scale,
                                 P["water_high"], K_DROP, life=0.55,
                                 size=2, grav=300, drag=1.2)
            self.particles.burst(ix, iy - 10 * scale, 4, 70 * scale,
                                 P["water_mid"], K_SMOK, life=0.7, size=3,
                                 grav=-50, drag=1.6)
            # geyser column
            for i in range(3):
                self.particles.spawn(ix + random.uniform(-6, 6) * scale,
                                     iy - 4 * scale,
                                     random.uniform(-15, 15),
                                     -random.uniform(140, 260) * scale,
                                     0.55, 2, P["water_shine"], K_DROP,
                                     grav=420, drag=0.4)
            _hit_stop(0.05)
            _shake(8.0, 0.28)
        elif sk == "w":
            self.impacts.spawn(ix, iy - 8 * scale, 1.7, kind="spear")
            self.particles.burst(ix, iy - 8 * scale, 9, 210 * scale,
                                 P["water_shine"], K_SHARD, life=0.5,
                                 size=2, grav=340, drag=1.1)
            self.particles.burst(ix, iy - 8 * scale, 5, 120 * scale,
                                 P["water_high"], K_DROP, life=0.6,
                                 size=2, grav=300, drag=1.2)
            _hit_stop(0.06)
            _shake(7.0, 0.26)
        elif sk == "e":
            self.impacts.spawn(ix, iy - 14 * scale, 1.2, kind="morph")
            cols = (P["str_hot"], P["agi_hot"], P["int_hot"])
            col = cols[int(getattr(self.hero, "morph_cycle", 0) or 0) % 3]
            self.particles.burst(ix, iy - 14 * scale, 8, 130 * scale,
                                 col, K_SPARK, life=0.6, size=2, grav=-60,
                                 drag=1.6)
            self.particles.burst(ix, iy - 10 * scale, 5, 60 * scale,
                                 P["core_light"], K_BUBB, life=0.8, size=2,
                                 grav=-120, drag=0.8)
            _hit_stop(0.04)
            _shake(5.0, 0.24)
        else:  # r
            self.impacts.spawn(ix, iy - 14 * scale, 2.1, kind="replicate")
            self.particles.burst(ix, iy - 14 * scale, 15, 240 * scale,
                                 P["water_high"], K_DROP, life=0.7,
                                 size=2, grav=320, drag=1.1)
            self.particles.burst(ix, iy - 12 * scale, 7, 110 * scale,
                                 P["water_mid"], K_SMOK, life=0.9, size=4,
                                 grav=-40, drag=1.5)
            for i in range(10):
                aa = i * 0.628
                self.particles.spawn(ix, iy - 6 * scale,
                                     math.cos(aa) * 200 * scale,
                                     math.sin(aa) * 90 * scale - 60,
                                     0.6, 2, P["water_shine"], K_SHARD,
                                     grav=380, drag=0.8)
            _hit_stop(0.07)
            _shake(10.0, 0.34)

    # ------------------------------------------------------------------
    def _target_world(self):
        boss = self.hero
        t = getattr(boss, "target", None)
        if t is not None and getattr(t, "alive", False):
            return float(getattr(t, "x", self.x)), \
                float(getattr(t, "y", self.y))
        f = 1 if int(getattr(boss, "direction", 1) or 1) >= 0 else -1
        return self.x + 170 * f, self.y

    # ------------------------------------------------------------------
    def on_impact(self, x, y, ang, power, crit, kind="blade"):
        """Benturan (melee / spear / skill). Impact FX + feel + reaksi."""
        scale = render_scale(self.hero)
        for s in self.skills:
            if s.pending is not None and s.skill == "w":
                s.pending = None
                s.done_impact = True
                s.ix, s.iy = float(x), float(y)
                self._skill_impact(s, float(x), float(y), scale)
                break
        self.impacts.spawn(x, y, power * scale, kind=kind, ang=ang,
                           crit=crit)
        n = int(6 + 6 * min(2.0, power))
        self.particles.burst(x, y, n, 130 * scale * min(1.6, power),
                             P["water_shine"], K_SPARK, life=0.3, size=2,
                             drag=2.6)
        self.particles.burst(x, y, int(n * 0.8), 90 * scale,
                             P["water_high"], K_DROP, life=0.45, size=2,
                             grav=300, drag=1.2)
        if kind in ("blade", "spear"):
            _hit_stop(0.045 if not crit else 0.06)
            _shake(4.0 if not crit else 6.0, 0.2)
        # reaksi musuh: flash + dorong kecil (kalau entity mendukung)
        tgt = getattr(self.hero, "target", None)
        if tgt is not None and kind == "blade":
            try:
                if math.hypot(getattr(tgt, "x", x) - x,
                              getattr(tgt, "y", y) - y) < 40:
                    tgt.hurt_flash_timer = max(
                        int(getattr(tgt, "hurt_flash_timer", 0) or 0), 6)
                    if not getattr(tgt, "is_boss", False):
                        tgt.x += math.cos(ang) * 3.0
                        tgt.y += math.sin(ang) * 1.5
            except Exception:                              # pragma: no cover
                pass

    # ------------------------------------------------------------------
    # DRAW: GROUND LAYER (di bawah sprite)
    # ------------------------------------------------------------------
    def draw_ground(self, surface, ox=0.0, oy=0.0):
        boss = self.hero
        scale = render_scale(boss)
        x = self.x - ox
        y = self.y - oy
        skill = getattr(boss, "active_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0) or 0)
        # puddle basah permanen (dither, murah: 8 pixel)
        gy = int(y) + 2
        for i in range(4):
            aa = i * 0.785 + self.time * 0.4
            rr = 20 * scale
            px_ = int(x + math.cos(aa) * rr)
            py_ = gy + int(math.sin(aa) * rr * 0.30)
            surface.fill(P["water_darkest"] + (90,), (px_, py_, 2, 1))
        if skill in SKILL_DUR and timer > 0:
            dur = SKILL_DUR[skill]
            prog = 1.0 - timer / float(dur)
            self._draw_telegraph(surface, x, y, skill, prog, scale)
        # klon air (R) di layer tanah/tinggi badan
        if self._clone_surf is not None and skill == "r":
            self._draw_clones(surface, ox, oy, prog if skill == "r"
                              else 0.0, scale)

    # ------------------------------------------------------------------
    def _draw_telegraph(self, surface, x, y, skill, prog, scale):
        r = WORLD_RADIUS.get(skill, 110) * scale
        gy = int(y) + 3
        if skill == "q":
            # garis arus ke arah hadap
            f = 1 if int(getattr(self.hero, "direction", 1) or 1) >= 0 \
                else -1
            ln = int(r * min(1.0, prog * 2.2))
            col = P["water_high"] + (int(140 * (1 - prog * 0.5)),)
            pygame.draw.line(surface, col, (int(x), gy),
                             (int(x + f * ln), gy), 2)
            for i in range(0, ln, 7):
                surface.fill(P["water_shine"] + (160,),
                             (int(x + f * i), gy - 2, 2, 1))
        elif skill == "e":
            # rune lingkaran atribut berputar
            cols = (P["str_hot"], P["agi_hot"], P["int_hot"])
            col = cols[int(getattr(self.hero, "morph_cycle", 0) or 0) % 3]
            rr = int(r * 0.55 * min(1.0, prog * 3))
            if rr > 3:
                _blit_faded(surface,
                            ellipse_ring_surface(rr, max(2, rr // 3), 1,
                                                 col, 200),
                            x, gy, 200)
                for i in range(6):
                    aa = self.time * 2.4 + i * 1.047
                    px_ = int(x + math.cos(aa) * rr)
                    py_ = gy + int(math.sin(aa) * rr * 0.34)
                    surface.fill(col + (220,), (px_, py_, 2, 2))
        elif skill == "r":
            # 3 puddle klon
            for i in range(3):
                aa = i * 2.094 + 0.6
                rr = 34 * scale * min(1.0, prog * 3)
                px_ = x + math.cos(aa) * rr
                py_ = gy + math.sin(aa) * rr * 0.34
                _blit_faded(surface,
                            ellipse_ring_surface(int(10 * scale),
                                                 int(4 * scale), 1,
                                                 P["water_high"], 200),
                            px_, py_, int(200 * min(1.0, prog * 4)))
        else:  # w
            tx, ty = self._target_world()
            dx, dy = tx - self.x, ty - self.y
            d = math.hypot(dx, dy) or 1.0
            k = min(1.0, prog * 2.0)
            cx, cy = x + dx / d * d * k * 0.98, gy + dy / d * d * k * 0.98
            _blit_faded(surface,
                        ellipse_ring_surface(int(14 * scale),
                                             int(6 * scale), 1,
                                             P["water_high"], 210),
                        cx, cy, int(220 * min(1.0, prog * 3)))

    # ------------------------------------------------------------------
    def _draw_clones(self, surface, ox, oy, prog, scale):
        G = _renderer()
        if G is None or self._clone_surf is None:
            return
        tint = self._clone_surf
        AWd, AHd = tint.get_size()
        px = G.PX
        k = _clamp(self._clone_t / 0.9)
        rise = _ease_out(min(1.0, self._clone_t / 0.35))
        fade = 1.0 - _ease_in(_clamp((self._clone_t - 0.6) / 0.5))
        if fade <= 0.02:
            self._clone_surf = None
            return
        big = pygame.transform.scale(tint, (AWd * px, AHd * px))
        tmp = big.copy()
        tmp.set_alpha(int(170 * fade))
        for i in range(3):
            aa = i * 2.094 + 0.6
            rr = (20 + 34 * _ease_out(min(1.0, self._clone_t / 0.6))) \
                * scale
            cx = self.x + math.cos(aa) * rr - ox
            cy = self.y + math.sin(aa) * rr * 0.34 - oy
            dx = int(cx - G.AX * px * scale)
            dy = int(cy - G.AY * px * scale + (1.0 - rise) * 30)
            # wave-distort: blit per strip horizontal dengan offset sinus
            strip = 6
            for sy in range(0, AHd * px, strip):
                off = int(math.sin(self.time * 7.0 + sy * 0.10 + i) *
                          2.4 * fade)
                surface.blit(tmp, (dx + off, dy + sy),
                             (0, sy, AWd * px, min(strip,
                                                   AHd * px - sy)))

    # ------------------------------------------------------------------
    # DRAW: LIVE LAYER (di atas sprite)
    # ------------------------------------------------------------------
    def draw_front(self, surface, ox=0.0, oy=0.0):
        boss = self.hero
        scale = render_scale(boss)
        # aura morph steady
        if getattr(boss, "morph_buff_active", False):
            cols = (P["str_hot"], P["agi_hot"], P["int_hot"])
            col = cols[int(getattr(boss, "morph_cycle", 0) or 0) % 3]
            pulse = 0.5 + 0.5 * math.sin(self.time * 5.0)
            _blit_faded(surface, glow_surface(int(20 * scale), col, 0.5),
                        self.x - ox, self.y - oy - 18 * scale,
                        int(50 + 40 * pulse))
        # charge glow W di ujung bilah
        for fx in self.skills:
            if fx.skill == "w" and fx.t < fx.TIMELINE["w"][1]:
                k = fx.t / max(0.001, fx.TIMELINE["w"][1])
                tx, ty = tip_screen(boss, self.x, self.y)
                _blit_faded(surface,
                            glow_surface(int((5 + 9 * k) * scale),
                                         P["core_hot"], 1.0),
                            tx - ox, ty - oy, int(120 + 120 * k))
            if fx.skill == "e" and fx.t < fx.TIMELINE["e"][2]:
                k = _clamp(fx.t / fx.TIMELINE["e"][2])
                hgt = int(52 * scale * (0.35 + 0.65 * k))
                cx0 = self.x - ox
                for yy in range(0, hgt, 2):
                    tt = yy / max(1, hgt)
                    w = max(2, int((9 - 6 * tt) * scale))
                    a = int(190 * (1 - tt * 0.75) * (0.5 + 0.5 * k))
                    wob = math.sin(self.time * 9 + yy * 0.35) * 2.2 * (1 - tt)
                    col = P["water_shine"] if yy % 6 < 2 else P["water_high"]
                    surface.fill(col + (a,),
                                 (int(cx0 - w // 2 + wob),
                                  int(self.y - oy - yy), w, 2))
                _blit_faded(surface,
                            glow_surface(int(10 * scale), P["core_hot"],
                                         0.9),
                            cx0, self.y - oy - hgt, int(150 * k))
        self.trail.draw(surface, ox, oy)
        self.projectiles.draw(surface, ox, oy)
        self.impacts.draw(surface, ox, oy)
        self.particles.draw(surface, ox, oy)


# ============================================================================
# 10. GAME-FEEL WRAPPERS (bus shared)
# ============================================================================
def _hit_stop(seconds=0.045):
    if _feel is not None:
        try:
            _feel.hit_stop(seconds)
        except Exception:                                  # pragma: no cover
            pass


def _shake(strength=5.0, duration=0.22):
    if _feel is not None:
        try:
            _feel.shake(strength, duration)
        except Exception:                                  # pragma: no cover
            pass


def hit_stop(seconds=0.045):
    _hit_stop(seconds)


def shake(strength=5.0, duration=0.22):
    _shake(strength, duration)


def should_freeze_frame():
    if _feel is None:                                      # pragma: no cover
        return False
    return _feel.should_freeze_frame()


# ============================================================================
# 11. REGISTRY DIRECTOR + API PUBLIK
# ============================================================================
_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    _sync_palette()
    d = getattr(hero, "_th_fx", None)
    if d is None:
        d = ThalgrynFXDirector(hero)
        try:
            hero._th_fx = d
        except Exception:                                  # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    try:
        if director.hero is not None:
            director.hero._th_fx = None
            director.hero._th_live_fx = False
    except Exception:                                      # pragma: no cover
        pass
    director.clear()


def attach(hero):
    if not THALGRYN_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                                      # pragma: no cover
        return False
    try:
        hero._th_live_fx = True
    except Exception:                                      # pragma: no cover
        return False
    return True


def owns(hero):
    if not getattr(hero, "_th_live_fx", False):
        return False
    d = getattr(hero, "_th_fx", None)
    return d is not None and d in _DIRECTORS


def tick(dt=None):
    global _LAST_TICK_MS
    if dt is not None:
        step = max(0.0, min(1.0 / 20.0, float(dt)))
        _advance(step)
        return step
    now = pygame.time.get_ticks()
    if now == _LAST_TICK_MS:
        return 0.0
    if _feel is not None:
        _LAST_TICK_MS = now
        try:
            step = _feel.fx_dt()
        except Exception:                                  # pragma: no cover
            step = 0.0
    else:                                                  # pragma: no cover
        ms = now - (_LAST_TICK_MS or now)
        _LAST_TICK_MS = now
        step = max(1.0 / 240.0, min(1.0 / 20.0, ms / 1000.0))
    _advance(step)
    return step


def _advance(step):
    if step <= 0.0 or not _DIRECTORS:
        return
    for d in _DIRECTORS:
        h = d.hero
        d.update(step, float(getattr(h, "x", 0.0)),
                 float(getattr(h, "y", 0.0)))


def reset_all():
    global _LAST_TICK_MS
    _LAST_TICK_MS = None
    for d in list(_DIRECTORS):
        _release(d)
    del _DIRECTORS[:]
    clear_cache()
    if _feel is not None:
        try:
            _feel.reset()
        except Exception:                                  # pragma: no cover
            pass


def total_particles():
    return sum(d.particles.count() for d in _DIRECTORS)


def projectiles_for(hero):
    d = getattr(hero, "_th_fx", None)
    if d is None:
        return ()
    return d.projectiles.list()


# ── hook renderer / heroes/__init__ ────────────────────────────────────────
def draw_ground_layer(surface, hero, x, y):
    if not THALGRYN_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_th_fx", None)
    if d is not None:
        d.x, d.y = float(x), float(y)
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    if not THALGRYN_FX_ENABLED:
        return
    d = director_for(hero)
    d.x, d.y = float(x), float(y)
    d.draw_front(surface)


# ── hook gameplay (base_boss / _entity) ────────────────────────────────────
def notify_melee_impact(hero, target, damage=0, crit=False):
    if not THALGRYN_FX_ENABLED or hero is None or target is None:
        return
    try:
        power = 0.75 + min(1.5, float(damage) / 70.0)
    except (TypeError, ValueError):
        power = 1.0
    tx = float(getattr(target, "x", getattr(hero, "x", 0.0)))
    ty = float(getattr(target, "y", getattr(hero, "y", 0.0))) - 6.0
    ang = math.atan2(ty - float(getattr(hero, "y", 0.0)),
                     tx - float(getattr(hero, "x", 0.0)))
    director_for(hero).on_impact(tx, ty, ang, power, bool(crit),
                                 kind="blade")


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False,
                             kind="spear"):
    if not THALGRYN_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    director_for(hero).on_impact(float(x), float(y), float(angle),
                                 power, bool(crit), kind=kind)


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    if not THALGRYN_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    x = float(x)
    y = float(y)
    fx = None
    for s in d.skills:
        if s.skill == skill and not s.done_impact:
            fx = s
            break
    if fx is None:
        if len(d.skills) >= MAX_SKILLS:
            d.skills.pop(0)
        fx = SkillFX(skill, x, y, radius)
        fx.done_impact = False
        fx.t = fx.TIMELINE[skill][2]      # mulai langsung dari IMPACT
        d.skills.append(fx)
    if skill == "w" and any(p.state == p.STATE_TRAVEL
                            for p in d.projectiles.pool):
        # spear masih terbang: impact menunggu mendarat (proyektil yang
        # memicu fase IMPACT lewat director.on_impact)
        fx.pending = (x, y)
        return
    # IMPACT sekarang juga: skill Q/E/R memang meledak saat AI/game
    # melaporkan benturan; menunda satu tick hanya membuat efek terasa
    # "telat" dari damage-nya.
    fx.pending = None
    fx.done_impact = True
    fx.ix, fx.iy = x, y
    if fx.t < fx.TIMELINE[skill][2]:
        fx.t = fx.TIMELINE[skill][2]
    d._skill_impact(fx, x, y, render_scale(hero))


def notify_skill_cast(hero, skill):
    if not THALGRYN_FX_ENABLED or hero is None or skill not in SKILL_DUR:
        return
    d = director_for(hero)
    d.on_cast(float(getattr(hero, "x", 0.0)),
              float(getattr(hero, "y", 0.0)), skill)


# ============================================================================
# 12. DEBUG OVERLAY
# ============================================================================
_DEBUG_FONT = None


def _debug_font():
    global _DEBUG_FONT
    if _DEBUG_FONT is None:
        try:
            _DEBUG_FONT = pygame.font.SysFont(None, 14)
        except Exception:                                  # pragma: no cover
            _DEBUG_FONT = False
    return _DEBUG_FONT or None


def draw_debug_overlay(surface, director):
    f = _debug_font()
    if f is None:
        return
    st = director.stats()
    lines = [
        "THALGRYN v4 fx",
        "part %d/%d" % (st["particles"], MAX_PARTICLES),
        "proj %d/%d" % (st["projectiles"], MAX_PROJECTILES),
        "imp %d/%d" % (st["impacts"], MAX_IMPACTS),
        "skill %d trail %d" % (st["skills"], st["trail"]),
    ]
    if _feel is not None:
        fs = _feel.stats()
        lines.append("hs %d shake %.1f" % (fs["hitstop_frames"],
                                           fs["shake"]))
    x, y = 8, 8
    for ln in lines:
        surf = f.render(ln, True, (140, 240, 255))
        surface.blit(surf, (x, y))
        y += 15
