# ============================================================================
# heroes/thalgryn_fx.py
# ----------------------------------------------------------------------------
# Lapisan FX HIDUP untuk Thalgryn "The Shape of Water" (mini boss level 6).
#
# Modul ini memegang SEMUA efek yang tidak boleh ikut ter-cache / ter-skala:
#   * partikel air (percikan, droplet, gelembung, busa)
#   * pita tebasan bilah air (SwingTrail, dari histori posisi sungguhan)
#   * proyektil "Water Spear" (core + glow + trail + impact)
#   * impact flash / shockwave / serpihan air / retakan
#   * skill FX Q/W/E/R dengan lifecycle CAST -> CHARGE -> RELEASE ->
#     TRAVEL/AREA -> IMPACT -> AFTER -> FADE
#   * hit-stop & screen shake (lewat bus heroes/combat_feel.py)
#
# 100% prosedural: tidak ada PNG / sprite sheet / image.load.
#
# Arsitektur mengikuti heroes/gornak_fx.py (rumah gaya V3 yang sama):
#   * satu director per unit (hero MAUPUN mini boss)
#   * modul ini TIDAK menggambar apa pun sampai dipanggil renderer lewat
#     draw_ground_layer() / draw_live_layer(), atau jalur hero lewat
#     heroes/__init__.py (_LIVE_FX_HEROES)
#   * semua geometry/pose dibaca dari bosses/level6._NS_thalgryn supaya
#     efek tidak pernah lepas dari badan (satu sumber kebenaran)
# ============================================================================

import math
import random

import pygame

#: Master switch lapisan FX Thalgryn.
THALGRYN_FX_ENABLED = True

#: Aktifkan overlay debug (hitbox / hurtbox / state / partikel).
DEBUG_CHARACTER = False

# ── Anggaran & batas ───────────────────────────────────────────────────────
MAX_PARTICLES = 170
MAX_PROJECTILES = 16
TRAIL_SAMPLES = 14
MAX_IMPACTS = 8
MAX_SKILLS = 4

#: Jarak (piksel dunia) di bawah ini serangan dasar Thalgryn dibaca sebagai
#: tebasan bilah air (melee swing); di atasnya dibaca sebagai lemparan
#: Water Spear (ranged). Sama seperti konvensi MELEE_REACH hero V3 lain.
MELEE_REACH = 78

#: Durasi status skill (frame) - HARUS sinkron dengan bosses/base_boss.py
#: (_thalgryn_q/w/e/r) dan hero_skills/_bundle.py.
SKILL_DUR = {"q": 60, "w": 50, "e": 60, "r": 80}

#: Batas total timeline SkillFX per skill (detik) - mencegah efek hidup
#: lebih lama dari statusnya sendiri.
SKILL_TOTAL = {"q": 0.9, "w": 0.8, "e": 0.95, "r": 1.2}

#: Radius efek skill dalam piksel dunia (telegraph renderer memakai angka
#: yang sama lewat _fx_scale).
WORLD_RADIUS = {"q": 130, "w": 90, "e": 115, "r": 185}

#: Prioritas state animasi (angka besar menang; DEATH mengunci).
ANIM_PRIORITY = {
    "IDLE": 0,
    "WALK": 10,
    "RUN": 15,
    "CHARGE": 30,
    "CAST": 35,
    "ATTACK": 40,
    "SWING": 45,
    "SKILL": 50,
    "SPECIAL": 55,
    "HIT": 60,
    "HURT": 65,
    "DEATH": 100,
}

# ============================================================================
# 1.  PALETTE  (nilai cadangan; disinkronkan dari _NS_thalgryn.PALETTE)
# ============================================================================

P = {
    # ── Badan air ─────────────────────────────────────────────────────
    "water_darkest": (5, 30, 45),
    "water_dark": (18, 70, 100),
    "water_mid": (40, 130, 165),
    "water_light": (85, 190, 210),
    "water_high": (140, 225, 235),
    "water_shine": (200, 245, 250),
    "water_white": (240, 255, 255),

    # ── Inti dalam ────────────────────────────────────────────────────
    "core_dark": (25, 85, 110),
    "core_mid": (55, 145, 170),
    "core_light": (110, 205, 220),

    # ── Bilah air (weapon) ────────────────────────────────────────────
    "blade_dark": (18, 70, 100),
    "blade_mid": (55, 145, 170),
    "blade_light": (110, 205, 220),
    "blade_shine": (200, 245, 250),

    # ── Mata menyala ──────────────────────────────────────────────────
    "eye_mid": (100, 210, 220),
    "eye_bright": (180, 245, 250),
    "eye_hot": (230, 255, 255),

    # ── Ramp FX generik ───────────────────────────────────────────────
    "fx_dark": (10, 40, 60),
    "fx_mid": (60, 150, 180),
    "fx_bright": (130, 215, 230),
    "fx_light": (200, 245, 250),
    "fx_hot": (235, 255, 255),
    "fx_white": (250, 255, 255),

    # ── Atribut morph ─────────────────────────────────────────────────
    "str_red": (200, 40, 40),
    "str_hot": (255, 100, 90),
    "agi_green": (60, 190, 70),
    "agi_hot": (140, 240, 120),
    "int_blue": (50, 130, 220),
    "int_hot": (140, 200, 255),

    # ── Trim emas / tanah / kabut ─────────────────────────────────────
    "gold_dark": (95, 62, 15),
    "gold_mid": (165, 125, 35),
    "gold_light": (225, 185, 70),
    "dust": (120, 150, 150),
    "ash": (70, 90, 100),
    "smoke": (40, 55, 65),
    "shadow": (0, 0, 0),
}

# Pemetaan kunci FX -> kunci PALETTE renderer (disalin sekali saat sync).
_PALETTE_SYNC = {
    "water_darkest": "water_darkest",
    "water_dark": "water_dark",
    "water_mid": "water_mid",
    "water_light": "water_light",
    "water_high": "water_high",
    "water_shine": "water_shine",
    "water_white": "water_white",
    "core_dark": "core_dark",
    "core_mid": "core_mid",
    "core_light": "core_light",
    "blade_dark": "blade_dark",
    "blade_mid": "blade_mid",
    "blade_light": "blade_light",
    "blade_shine": "blade_shine",
    "eye_mid": "eye_mid",
    "eye_bright": "eye_bright",
    "eye_hot": "eye_hot",
    "str_red": "str_red",
    "str_hot": "str_hot",
    "agi_green": "agi_green",
    "agi_hot": "agi_hot",
    "int_blue": "int_blue",
    "int_hot": "int_hot",
    "gold_dark": "gold_dark",
    "gold_mid": "gold_mid",
    "gold_light": "gold_light",
    "shadow": "shadow",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Salin warna tema dari ``_NS_thalgryn.PALETTE`` sekali saja."""
    global _PALETTE_SYNCED
    if _PALETTE_SYNCED:
        return
    _PALETTE_SYNCED = True
    G = _renderer()
    if G is None:
        return
    pal = getattr(G, "PALETTE", None)
    if not isinstance(pal, dict):
        return
    for dst, src in _PALETTE_SYNC.items():
        col = pal.get(src)
        if col is not None:
            P[dst] = tuple(int(c) for c in col[:3])


# ============================================================================
# 2.  JEMBATAN KE RENDERER  (satu sumber geometri & pose)
# ============================================================================

_RENDERER = None          # None = belum dicari, False = tidak ada


def _renderer():
    """``_NS_thalgryn`` atau None. Diimpor malas (modul boss besar)."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level6 import _NS_thalgryn as G
            _RENDERER = G
        except Exception:                      # pragma: no cover
            _RENDERER = False
    return _RENDERER or None


def _fallback_pose(boss):
    """(action, phase, ap) tanpa renderer: baca atribut yang sudah ada."""
    skill = getattr(boss, "active_skill", None)
    action = getattr(boss, "_th_pose_action", None)
    if action is None:
        action = {"q": "waveform", "w": "adaptive", "e": "morph",
                  "r": "replicate"}.get(skill)
    if action is None:
        action = ("attack" if getattr(boss, "_th_attack_active", False)
                  else "idle")
    phase = float(getattr(boss, "pulse", 0.0) or 0.0)
    ap = 0.0
    if action == "attack":
        raw = float(getattr(boss, "_th_attack_progress", 0.0) or 0.0)
        ap = min(1.0, max(0.0, raw))
    return action, phase, ap


def pose_of(boss):
    """(action, phase, ap) — pose yang SEDANG digambar badan."""
    G = _renderer()
    if G is None:
        return _fallback_pose(boss)
    try:
        return G._resolve_pose(boss, bool(getattr(boss, "_moving_cached",
                                                  False)))
    except Exception:                          # pragma: no cover
        return _fallback_pose(boss)


def render_scale(boss):
    """Faktor normalisasi pipeline hero. Jalur boss = 1.0."""
    v = getattr(boss, "_render_scale", None)
    if v is None:
        return 1.0
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 1.0
    if v <= 0.02:
        return 1.0
    return max(0.05, min(1.6, v))


def body_scale(boss):
    """Skala rig -> piksel layar (SCALE renderer dikali normalisasi hero)."""
    G = _renderer()
    k = getattr(G, "SCALE", 1.0) if G is not None else 1.0
    return float(k) * render_scale(boss)


def screen_point(boss, x, y, local, action=None, phase=None, ap=None):
    """Ruang lokal rig -> piksel layar (sama dengan _NS_thalgryn._local)."""
    G = _renderer()
    facing = getattr(boss, "direction", None)
    if facing is None:
        facing = getattr(boss, "facing", 1)
    f = 1 if (facing or 1) >= 0 else -1
    if action is None or phase is None or ap is None:
        action, phase, ap = pose_of(boss)
    lean = root_y = 0
    lift = 0.0
    k = body_scale(boss)
    if G is not None:
        try:
            lean, root_y = G._rig_shift(action, phase, ap)
        except Exception:                      # pragma: no cover
            lean = root_y = 0
        lift = float(getattr(G, "LIFT", 0))
    return (int(round(x + (local[0] * f + lean * f) * k)),
            int(round(y - lift * render_scale(boss)
                      + (local[1] + root_y) * k)))


def blade_points(boss, x, y):
    """(grip, tip) bilah air dalam piksel layar — sumber bentuk trail."""
    G = _renderer()
    action, phase, ap = pose_of(boss)
    if G is None:
        grip_l = (14, 2)
        tip_l = (42, -16)
    else:
        try:
            grip_l = G._front_grip_local(action, ap, phase)
            tip_l = G._tip_local(action, phase, ap)
        except Exception:                      # pragma: no cover
            grip_l, tip_l = (14, 2), (42, -16)
    grip = screen_point(boss, x, y, grip_l, action, phase, ap)
    tip = screen_point(boss, x, y, tip_l, action, phase, ap)
    return pygame.Vector2(grip), pygame.Vector2(tip)


# ============================================================================
# 3.  ANGGARAN EFEK  (menghormati preset kualitas mobile)
# ============================================================================

def _quality():
    try:
        from mobile.perf import Quality
        return Quality
    except Exception:                          # pragma: no cover
        return None


def particle_budget():
    Q = _quality()
    if Q is None:
        return 1.0
    if not getattr(Q, "particles", True):
        return 0.0
    return float(getattr(Q, "particle_ratio", 1.0))


def glow_allowed():
    Q = _quality()
    return True if Q is None else bool(getattr(Q, "glow", True))


def shake_allowed():
    Q = _quality()
    return True if Q is None else bool(getattr(Q, "screen_shake", True))


# ============================================================================
# 4.  HELPER WARNA & CACHING
# ============================================================================

def _clamp_color(color):
    return tuple(max(0, min(255, int(c))) for c in color[:3])


def _mix(a, b, t):
    t = max(0.0, min(1.0, float(t)))
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def _hash01(seed):
    h = int(seed) * 2654435761 & 0xFFFFFFFF
    h ^= h >> 16
    h = (h * 2246822519) & 0xFFFFFFFF
    return (h & 0xFFFF) / 65535.0


_SURF_CACHE = {}
_SURF_CACHE_MAX = 384


def _cache_put(key, surf):
    if len(_SURF_CACHE) >= _SURF_CACHE_MAX:
        for k in list(_SURF_CACHE)[:_SURF_CACHE_MAX // 4]:
            del _SURF_CACHE[k]
    _SURF_CACHE[key] = surf
    return surf


def clear_cache():
    _SURF_CACHE.clear()


def cache_size():
    return len(_SURF_CACHE)


def glow_surface(radius, color, power=1.0):
    """Bola cahaya radial PREMULTIPLIED (benar untuk blit additive)."""
    radius = max(2, int(radius)) // 2 * 2
    color = _clamp_color(color)
    power = round(float(power), 2)
    key = ("glow", radius, color, power)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    size = radius * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = radius + 1
    steps = max(4, min(radius, 12))
    for i in range(steps, 0, -1):
        t = i / float(steps)
        r = max(1, int(radius * t))
        k = power * (1.0 - t) ** 1.75
        if k <= 0.004:
            continue
        pygame.draw.circle(
            surf,
            (int(color[0] * k), int(color[1] * k), int(color[2] * k),
             min(255, int(255 * k))), (c, c), r)
    return _cache_put(key, surf)


def spark_surface(size, color):
    """Bintang 4 sudut pixel-art (hard edge, tanpa gradien)."""
    size = max(3, int(size))
    color = _clamp_color(color)
    key = ("spark", size, color)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    s = size * 2 + 1
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    c = size
    arm = max(1, size // 3)
    pygame.draw.polygon(surf, (*color, 235),
                        [(c, 0), (c + arm, c), (c, s - 1), (c - arm, c)])
    pygame.draw.polygon(surf, (*color, 185),
                        [(0, c), (c, c - max(1, size // 4)),
                         (s - 1, c), (c, c + max(1, size // 4))])
    pygame.draw.rect(surf, (*P["fx_white"], 255), (c - 1, c - 1, 3, 3))
    return _cache_put(key, surf)


def ring_surface(radius, thickness, color, alpha=255, dashed=0):
    """Cincin energi (opsional terputus)."""
    radius = max(3, int(radius)) // 3 * 3
    thickness = max(1, int(thickness))
    color = _clamp_color(color)
    dashed = int(dashed)
    alpha = int(alpha) // 16 * 16
    key = ("ring", radius, thickness, color, alpha, dashed)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    size = radius * 2 + thickness * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    if dashed <= 0:
        pygame.draw.circle(surf, (*color, int(alpha)), (c, c), radius,
                           thickness)
    else:
        step = math.tau / dashed
        span = step * 0.56
        for i in range(dashed):
            a0 = i * step
            pts = []
            for j in range(5):
                a = a0 + span * j / 4.0
                pts.append((c + math.cos(a) * radius,
                            c + math.sin(a) * radius))
            for j in range(len(pts) - 1):
                pygame.draw.line(surf, (*color, int(alpha)),
                                 (int(pts[j][0]), int(pts[j][1])),
                                 (int(pts[j + 1][0]), int(pts[j + 1][1])),
                                 thickness)
    return _cache_put(key, surf)


def ellipse_ring_surface(rx, ry, thickness, color, angle_deg=0):
    """Cincin elips berarah — shockwave gepeng, bukan lingkaran polos."""
    rx = max(3, int(rx)) // 3 * 3
    ry = max(2, int(ry)) // 2 * 2
    thickness = max(1, int(thickness))
    color = _clamp_color(color)
    step = int(angle_deg) // 15 * 15
    key = ("ering", rx, ry, thickness, color, step)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    pad = thickness + 2
    base = pygame.Surface((rx * 2 + pad * 2, ry * 2 + pad * 2),
                          pygame.SRCALPHA)
    pygame.draw.ellipse(base, (*color, 255), (pad, pad, rx * 2, ry * 2),
                        thickness)
    if step:
        base = pygame.transform.rotate(base, -step)
    return _cache_put(key, base)


def ground_glow_surface(radius, color, power=0.3):
    """Kabut cahaya di tanah (elips gepeng, premultiplied)."""
    radius = max(4, int(radius))
    color = _clamp_color(color)
    power = round(float(power), 2)
    key = ("gglow", radius, color, power)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    w = radius * 2 + 4
    h = radius + 4
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    steps = max(4, min(radius // 2, 12))
    for i in range(steps, 0, -1):
        t = i / float(steps)
        rx = max(2, int(radius * t))
        ry = max(1, int(radius * t * 0.42))
        k = power * (1.0 - t) ** 1.5
        if k <= 0.004:
            continue
        pygame.draw.ellipse(
            surf,
            (int(color[0] * k), int(color[1] * k), int(color[2] * k),
             min(255, int(255 * k))),
            (w // 2 - rx, h // 2 - ry, rx * 2, ry * 2))
    return _cache_put(key, surf)


def _shard_poly(surface, cx, cy, ang, length, width, color, alpha=255,
                core=None):
    """Serpihan tajam berorientasi (pecahan bilah / tetes air)."""
    alpha = int(alpha)
    if alpha <= 5:
        return
    ln = max(2, int(length))
    wd = max(1, int(width))
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for dx, dy in ((ln, 0), (-ln // 3, wd), (-ln, 0), (-ln // 3, -wd)):
        pts.append((int(cx) + int(dx * ca - dy * sa),
                    int(cy) + int(dx * sa + dy * ca)))
    pygame.draw.polygon(surface, (*_clamp_color(color), min(255, alpha)), pts)
    if core is not None and ln >= 6:
        pygame.draw.polygon(
            surface, (*_clamp_color(core), min(255, alpha + 20)),
            [(int(cx) + int(ln * .6 * ca), int(cy) + int(ln * .6 * sa)),
             (int(cx) - wd // 2, int(cy) - max(1, wd // 2)),
             (int(cx) - int(ln * .4), int(cy))])


# ── scratch surface pool ──────────────────────────────────────────────────
_SCRATCH = {}


def _scratch(w, h):
    """Surface sementara transparan >= (w,h), dipakai ulang (tanpa alokasi)."""
    w = max(4, int(w))
    h = max(4, int(h))
    key = (1 << (w - 1).bit_length(), 1 << (h - 1).bit_length())
    s = _SCRATCH.get(key)
    if s is None:
        s = pygame.Surface(key, pygame.SRCALPHA)
        _SCRATCH[key] = s
    else:
        s.fill((0, 0, 0, 0))
    return s


def _blit_faded(surface, surf, cx, cy, alpha=255, additive=False):
    alpha = int(alpha)
    if alpha <= 5:
        return
    if additive:
        surface.blit(surf, (int(cx) - surf.get_width() // 2,
                            int(cy) - surf.get_height() // 2),
                     special_flags=pygame.BLEND_RGB_ADD)
        return
    surf.set_alpha(min(255, alpha))
    surface.blit(surf, (int(cx) - surf.get_width() // 2,
                        int(cy) - surf.get_height() // 2))


# ============================================================================
# 5.  PARTICLE SYSTEM
# ============================================================================

class Particle:
    """Satu partikel prosedural (pool reuse)."""

    __slots__ = ("pos", "vel", "acc", "life", "max_life", "size",
                 "rotation", "rotation_speed", "alpha", "gravity",
                 "color", "color_end", "shape", "drag", "additive",
                 "active", "fade_pow", "layer", "seed")

    def __init__(self):
        self.pos = pygame.Vector2()
        self.vel = pygame.Vector2()
        self.acc = pygame.Vector2()
        self.life = 0.0
        self.max_life = 1.0
        self.size = 2.0
        self.rotation = 0.0
        self.rotation_speed = 0.0
        self.alpha = 255
        self.gravity = 0.0
        self.color = P["fx_bright"]
        self.color_end = None
        self.shape = "pixel"
        self.drag = 0.0
        self.additive = False
        self.active = False
        self.fade_pow = 1.0
        self.layer = "front"
        self.seed = 0

    @property
    def position(self):
        return self.pos

    @property
    def velocity(self):
        return self.vel

    @property
    def acceleration(self):
        return self.acc

    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        self.pos.update(x, y)
        self.vel.update(vx, vy)
        self.acc.update(float(kw.get("ax", 0.0)), float(kw.get("ay", 0.0)))
        self.life = self.max_life = max(0.02, float(life))
        self.size = float(size)
        self.color = color
        self.color_end = kw.get("color_end")
        self.gravity = float(kw.get("gravity", 0.0))
        self.drag = float(kw.get("drag", 0.0))
        self.rotation = float(kw.get("rotation", 0.0))
        self.rotation_speed = float(kw.get("rotation_speed", 0.0))
        self.alpha = int(kw.get("alpha", 255))
        self.shape = kw.get("shape", "pixel")
        self.additive = bool(kw.get("additive", False))
        self.fade_pow = float(kw.get("fade_pow", 1.0))
        self.layer = kw.get("layer", "front")
        self.seed = int(kw.get("seed", 0))
        self.active = True
        return self

    def update(self, dt):
        self.life -= dt
        if self.life <= 0.0:
            self.active = False
            return False
        self.vel.x += self.acc.x * dt
        self.vel.y += (self.acc.y + self.gravity) * dt
        if self.drag:
            damp = max(0.0, 1.0 - self.drag * dt)
            self.vel.x *= damp
            self.vel.y *= damp
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt
        self.rotation += self.rotation_speed * dt
        return True

    def draw(self, surface):
        t = self.life / self.max_life
        fade = t ** self.fade_pow
        a = int(self.alpha * fade)
        if a <= 4:
            return
        col = self.color if self.color_end is None \
            else _mix(self.color_end, self.color, fade)
        x = int(self.pos.x)
        y = int(self.pos.y)
        sz = max(1, int(self.size * (0.35 + 0.65 * fade)))
        shape = self.shape

        if shape == "glow":
            if not glow_allowed():
                return
            g = glow_surface(sz * 2, col, round(0.85 * fade, 2))
            surface.blit(g, (x - sz * 2, y - sz * 2),
                         special_flags=pygame.BLEND_RGB_ADD)
            return

        if shape == "spark":
            s = spark_surface(sz + 1, col)
            s.set_alpha(a)
            surface.blit(s, (x - sz - 1, y - sz - 1))
            return

        if shape == "shard":
            _shard_poly(surface, x, y, self.rotation, sz * 2,
                        max(1, sz // 2 + 1), col, a, P["fx_white"])
            return

        if shape == "streak":
            v = self.vel
            n = v.length()
            if n < 0.01:
                return
            ux, uy = v.x / n, v.y / n
            ln = max(2, int(sz * 2 + n * 0.022))
            buf = _scratch(ln * 2 + 6, ln * 2 + 6)
            off = ln + 3
            pygame.draw.line(buf, (*col, a), (off, off),
                             (off - int(ux * ln), off - int(uy * ln)),
                             max(1, sz // 2 + 1))
            surface.blit(buf, (x - off, y - off))
            return

        if shape == "dust":
            r = sz + 1
            buf = _scratch(r * 2 + 2, r * 2 + 2)
            pygame.draw.rect(buf, (*col, a), (2, 2, sz, sz))
            pygame.draw.rect(buf, (*col, max(0, a // 2)),
                             (1, 3, max(1, sz // 2), max(1, sz // 2)))
            surface.blit(buf, (x - r, y - r))
            return

        # default: kotak chunky (inti terang kalau cukup besar)
        buf = _scratch(sz * 2 + 2, sz * 2 + 2)
        if self.additive:
            k = max(0.0, min(1.0, a / 255.0))
            col = _clamp_color((col[0] * k, col[1] * k, col[2] * k))
            wc = _clamp_color((P["fx_white"][0] * k,
                               P["fx_white"][1] * k,
                               P["fx_white"][2] * k))
            pygame.draw.rect(buf, (*col, 255), (1, 1, sz, sz))
            if sz >= 3:
                pygame.draw.rect(buf, (*wc, 255),
                                 (1, 1, max(1, sz // 2), max(1, sz // 2)))
            surface.blit(buf, (x - sz // 2, y - sz // 2),
                         special_flags=pygame.BLEND_RGB_ADD)
            return
        pygame.draw.rect(buf, (*col, a), (1, 1, sz, sz))
        if sz >= 3:
            pygame.draw.rect(buf, (*P["fx_white"], min(255, a + 40)),
                             (1, 1, max(1, sz // 2), max(1, sz // 2)))
        surface.blit(buf, (x - sz // 2, y - sz // 2))


class ParticleSystem:
    """Pool partikel reusable: spawn / burst / stream / update / draw."""

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = int(cap)
        self._pool = []
        self._live = []
        self.dropped = 0

    def _acquire(self):
        if self._pool:
            return self._pool.pop()
        return Particle()

    def count(self):
        return len(self._live)

    def clear(self):
        for p in self._live:
            p.active = False
            self._pool.append(p)
        self._live.clear()

    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        budget = particle_budget()
        if budget <= 0.0:
            self.dropped += 1
            return None
        room = int(self.cap * budget) - len(self._live)
        if room <= 0:
            self.dropped += 1
            return None
        p = self._acquire().spawn(x, y, vx, vy, life, size, color, **kw)
        self._live.append(p)
        return p

    def burst(self, x, y, count, speed=(60.0, 210.0), life=(0.22, 0.55),
              size=(2, 4), colors=None, spread=math.tau, direction=0.0,
              gravity=0.0, drag=2.2, shape="pixel", additive=False,
              rotation_speed=(0.0, 0.0), fade_pow=1.0, layer="front"):
        colors = colors or (P["fx_bright"], P["fx_light"], P["fx_hot"])
        budget = particle_budget()
        if budget <= 0.0:
            return 0
        room = int(self.cap * budget) - len(self._live)
        if room <= 0:
            self.dropped += int(count)
            return 0
        n = min(int(count * budget) if budget < 1.0 else int(count), room)
        for i in range(n):
            ang = direction + (random.random() - 0.5) * spread
            spd = random.uniform(speed[0], speed[1])
            self.spawn(
                x, y,
                math.cos(ang) * spd, math.sin(ang) * spd,
                random.uniform(life[0], life[1]),
                random.uniform(size[0], size[1]),
                colors[i % len(colors)],
                gravity=gravity, drag=drag, shape=shape,
                additive=additive, fade_pow=fade_pow, layer=layer,
                rotation=random.random() * math.tau,
                rotation_speed=random.uniform(rotation_speed[0],
                                               rotation_speed[1]),
                seed=i)
        return n

    def stream(self, x, y, tx, ty, count, life=(0.3, 0.6), size=(1, 3),
               colors=None, bow=18.0, layer="back"):
        colors = colors or (P["fx_light"], P["fx_bright"], P["fx_mid"])
        d = math.hypot(tx - x, ty - y)
        if d < 1.0:
            return 0
        ux, uy = (tx - x) / d, (ty - y) / d
        px, py = -uy, ux
        budget = particle_budget()
        if budget <= 0.0:
            return 0
        made = 0
        for i in range(min(int(count), 24)):
            side = random.choice((-1.0, 1.0)) * random.uniform(0.35, 1.0)
            sx = x + px * bow * side
            sy = y + py * bow * side * 0.55
            p = self.spawn(sx, sy, (tx - sx) / max(0.05, life[1]) * 0.9,
                           (ty - sy) / max(0.05, life[1]) * 0.9,
                           random.uniform(*life), random.uniform(*size),
                           colors[i % len(colors)],
                           drag=0.35, shape="pixel", additive=True,
                           layer=layer,
                           rotation=math.atan2(uy, ux),
                           rotation_speed=side * 2.2)
            if p is None:
                break
            made += 1
        return made

    def update(self, dt):
        if not self._live:
            return
        live = self._live
        keep = []
        pool = self._pool
        for p in live:
            if p.update(dt):
                keep.append(p)
            elif len(pool) < self.cap:
                pool.append(p)
        self._live = keep

    def draw(self, surface, layer="front"):
        if not self._live:
            return
        want_back = layer == "back"
        for p in self._live:
            if (p.layer == "back") == want_back:
                p.draw(surface)


# ============================================================================
# 6.  SWING TRAIL  —  jejak bilah air dari histori posisi sungguhan
# ============================================================================

class SwingTrail:
    """Pita tebasan bilah air berbasis histori (grip, tip) per frame.

    Bentuknya turunan lintasan senjata (sector cincin di sekitar grip),
    jadi tidak pernah lepas dari bilah. Warna = gradasi air (dark -> shine).
    """

    MAX_TURN_DOT = 0.15
    ARC_STEP = 0.16
    MAX_SWEEP = 1.95

    def __init__(self, samples=TRAIL_SAMPLES):
        self.samples = int(samples)
        self.points = []          # [[grip, tip, umur], ...]
        self.life = 0.24
        self.width_boost = 1.0
        self.active = False
        self.color_edge = P["water_light"]
        self.color_core = P["water_high"]
        self.color_tip = P["fx_white"]

    def reset(self):
        self.points.clear()
        self.active = False

    def push(self, grip, tip):
        self.points.append([pygame.Vector2(grip), pygame.Vector2(tip), 0.0])
        if len(self.points) > self.samples:
            self.points.pop(0)
        self.active = True

    def update(self, dt):
        if not self.points:
            self.active = False
            return
        for s in self.points:
            s[2] += dt
        self.points = [s for s in self.points if s[2] < self.life]
        if not self.points:
            self.active = False

    @staticmethod
    def _ang_delta(a_new, a_old):
        return (a_new - a_old + math.pi) % (2.0 * math.pi) - math.pi

    def _ribbon(self, surface, lst, edge, core, tip_col, base_alpha):
        n = len(lst)
        if n < 2:
            return
        nodes = []
        for g, t, age in lst:
            blade = t - g
            r = blade.length()
            if r < 6.0:
                continue
            nodes.append((g, math.atan2(blade.y, blade.x), r, age))
        if len(nodes) < 2:
            return

        strips = []
        cur = [nodes[0]]
        prev_dir = 0.0
        for i in range(1, len(nodes)):
            da = self._ang_delta(nodes[i][1], cur[-1][1])
            if abs(da) < 0.035:
                continue
            if prev_dir * da < 0.0:
                if len(cur) > 1:
                    strips.append((cur, prev_dir))
                cur = [nodes[i - 1], nodes[i]]
                prev_dir = da
                continue
            prev_dir = da
            cur.append(nodes[i])
        if len(cur) > 1:
            strips.append((cur, prev_dir))

        for raw, _pd in strips:
            strip = raw
            sweep = 0.0
            keep = 0
            for j in range(len(strip) - 1, 0, -1):
                sweep += abs(self._ang_delta(strip[j][1], strip[j - 1][1]))
                if sweep > self.MAX_SWEEP:
                    keep = j
                    break
            if keep:
                strip = strip[keep:]
            m = len(strip)
            if m < 2:
                continue

            xs, ys = [], []
            for (gx, _a, r, _age) in strip:
                xs += [gx.x - r * 0.20, gx.x + r * 1.12]
                ys += [gx.y - r * 1.12, gx.y + r * 1.12]
            minx, maxx = int(min(xs)) - 2, int(max(xs)) + 2
            miny, maxy = int(min(ys)) - 2, int(max(ys)) + 2
            w, h = maxx - minx, maxy - miny
            if w <= 2 or h <= 2 or w > 1400 or h > 1400:
                continue
            buf = _scratch(w, h)

            def polar(cx, cy, ang, rad):
                return (int(cx + math.cos(ang) * rad) - minx,
                        int(cy + math.sin(ang) * rad) - miny)

            for j in range(m - 1):
                (g0, a0, r0, age0) = strip[j]
                (g1, a1, r1, _age1) = strip[j + 1]
                da = self._ang_delta(a1, a0)
                if abs(da) < 0.02:
                    continue
                fade = max(0.0, 1.0 - age0 / self.life)
                rank = (j + 1) / float(m)
                spread = min(1.0, 0.34 / max(0.05, abs(da)))
                k = (rank ** 2) * fade * self.width_boost * spread
                if k <= 0.012:
                    continue
                thin = 0.05 + 0.075 * rank
                steps = max(1, min(8, int(abs(da) / self.ARC_STEP) + 1))
                outer, inner, cout, cin, glint = [], [], [], [], []
                for q in range(steps + 1):
                    f = q / float(steps)
                    aa = a0 + da * f
                    rr = (r0 + (r1 - r0) * f) * 0.97
                    ri = rr * (1.0 - thin)
                    rc = rr * (1.0 - thin * 0.40)
                    outer.append(polar(g1.x, g1.y, aa, rr))
                    inner.append(polar(g1.x, g1.y, aa, ri))
                    cout.append(polar(g1.x, g1.y, aa, rr * 0.985))
                    cin.append(polar(g1.x, g1.y, aa, rc))
                    glint.append(polar(g1.x, g1.y, aa, rr))
                a_edge = int(base_alpha * k * 0.62)
                if a_edge > 5:
                    pygame.draw.polygon(buf, (*edge, a_edge),
                                        outer + inner[::-1])
                a_core = int((base_alpha + 96) * k)
                if a_core > 8:
                    pygame.draw.polygon(buf, (*core, min(255, a_core)),
                                        cout + cin[::-1])
                a_tip = int(235 * k)
                if a_tip > 14:
                    pygame.draw.lines(buf, (*tip_col, min(255, a_tip)),
                                      False, glint, 2 if k > 0.78 else 1)
            surface.blit(buf, (minx, miny))

    def draw(self, surface):
        if self.points:
            self._ribbon(surface, self.points, self.color_edge,
                         self.color_core, self.color_tip, 88)


# ============================================================================
# 7.  IMPACT FX
# ============================================================================

class ImpactFX:
    """Satu kejadian benturan air: flash, shockwave, percikan, serpihan.

    ``kind`` memilih bahasa visual:
        ``blade``      — tebasan bilah air (crescent + percikan)
        ``spear``      — Water Spear (retakan zigzag + busa)
        ``wave``       — Waveform dash (semburan horizontal)
        ``morph``      — Morph (mote atribut + cincin)
        ``replicate``  — Replicate (cincin ganda + pilar kecil)
    """

    KINDS = ("blade", "spear", "wave", "morph", "replicate")

    __slots__ = ("x", "y", "angle", "power", "age", "duration", "crit",
                 "active", "kind", "seed", "ground")

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="blade", ground=0.0, seed=None):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = max(0.35, min(2.6, float(power)))
        self.age = 0.0
        self.duration = 0.30 + 0.11 * min(2.0, self.power)
        self.crit = bool(crit)
        self.active = True
        self.kind = kind if kind in self.KINDS else "blade"
        self.ground = float(ground)
        self.seed = random.randint(0, 9999) if seed is None else int(seed)

    def update(self, dt):
        self.age += dt
        if self.age >= self.duration:
            self.active = False
        return self.active

    def _ramp(self):
        if self.kind == "blade":
            return P["water_dark"], P["water_light"], P["water_shine"]
        if self.kind == "wave":
            return P["water_dark"], P["water_mid"], P["water_light"]
        if self.kind == "morph":
            return P["core_dark"], P["core_light"], P["water_high"]
        if self.kind == "replicate":
            return P["water_dark"], P["water_light"], P["fx_white"]
        return P["fx_dark"], P["water_light"], P["fx_white"]

    def draw(self, surface):
        if not self.active:
            return
        t = min(1.0, self.age / self.duration)
        inv = 1.0 - t
        x, y = int(self.x), int(self.y)
        pw = self.power
        deg = math.degrees(self.angle)
        dark, mid, hot = self._ramp()

        # 1. FLASH: bintang 8 sisi, bukan bola putih
        if t < 0.24:
            ft = 1.0 - t / 0.24
            gr = int((5 + 10 * pw) * (0.5 + 0.5 * ft)) // 2 * 2 + 2
            if glow_allowed():
                surface.blit(glow_surface(gr, hot, 0.55 * ft),
                             (x - gr, y - gr),
                             special_flags=pygame.BLEND_RGB_ADD)
            ln = (10 + 21 * pw) * ft
            buf = _scratch(int(ln * 2 + 8), int(ln * 2 + 8))
            c = int(ln + 4)
            for k in range(8):
                a = self.angle + k * math.pi / 4
                L = ln if k % 2 == 0 else ln * 0.40
                pygame.draw.line(buf, (*P["fx_white"], int(232 * ft)),
                                 (c, c),
                                 (c + int(math.cos(a) * L),
                                  c + int(math.sin(a) * L)),
                                 2 if k % 2 == 0 else 1)
            surface.blit(buf, (x - c, y - c))

        # 2. SHOCKWAVE: elips gepeng (melebar seiring waktu)
        rr = int((8 + 44 * pw) * (0.25 + 1.0 * t)) // 3 * 3
        th = max(1, int(4 * inv * pw))
        a = int(210 * inv * inv)
        if a > 6 and rr > 4:
            if self.kind == "blade":
                er = ellipse_ring_surface(rr, max(3, int(rr * 0.55)), th,
                                          mid, deg)
            elif self.kind in ("wave", "replicate"):
                er = ellipse_ring_surface(rr, max(3, int(rr * 0.72)), th,
                                          mid, 0)
            else:
                er = ring_surface(rr, th, mid, 255, dashed=0)
            er.set_alpha(a)
            surface.blit(er, (x - er.get_width() // 2,
                              y - er.get_height() // 2))
            rr2 = int(rr * 0.56)
            if rr2 > 4:
                er2 = ring_surface(rr2, max(1, th - 1), hot, 255,
                                   dashed=8 if self.kind != "blade" else 0)
                er2.set_alpha(int(a * 0.8))
                surface.blit(er2, (x - er2.get_width() // 2,
                                   y - er2.get_height() // 2))

        # 3. SPOKE DEBRIS: garis radial memanjang keluar
        if t < 0.58:
            st = 1.0 - t / 0.58
            r0 = int((6 + 19 * pw) * (0.3 + 1.05 * t))
            for k in range(8):
                ang = self.angle + k * math.pi / 4 + 0.19
                L = (7 + 14 * pw) * st * (1.0 if k % 2 else 0.55)
                pygame.draw.line(
                    surface, _clamp_color(_mix(dark, mid, st)),
                    (x + int(math.cos(ang) * r0),
                     y + int(math.sin(ang) * r0)),
                    (x + int(math.cos(ang) * (r0 + L)),
                     y + int(math.sin(ang) * (r0 + L))),
                    2 if k % 2 else 1)

        # 4. SLASH FRAGMENT: busur pecah searah pukulan (blade / spear)
        if t < 0.52 and self.kind in ("blade", "spear"):
            st = 1.0 - t / 0.52
            span = 0.5 + 0.5 * pw
            base_r = int(11 + 28 * pw * (0.4 + t))
            buf = _scratch(base_r * 2 + 16, base_r * 2 + 16)
            c = base_r + 8
            for k in (-1, 0, 1):
                ang0 = self.angle - span / 2 + k * 0.13
                ang1 = ang0 + span
                rad = base_r - abs(k) * 5
                rect = pygame.Rect(c - rad, c - rad, rad * 2, rad * 2)
                col = P["fx_white"] if k == 0 else mid
                try:
                    pygame.draw.arc(buf, (*col, int(225 * st)), rect,
                                    -ang1, -ang0, 3 if k == 0 else 2)
                except (ValueError, pygame.error):
                    pass
            surface.blit(buf, (x - c, y - c))

        # 5. RETAKAN ZIGZAG (spear / replicate)
        if t < 0.62 and self.kind in ("spear", "replicate"):
            st = 1.0 - t / 0.62
            n = 5 if self.kind == "spear" else 7
            for i in range(n):
                base = (self.seed * 0.37) + i * math.tau / n
                length = (16 + 20 * pw) * (0.6 + 0.55 * t)
                px, py = x, y
                ang = base
                for seg in range(3):
                    ang += (_hash01(self.seed + i * 13 + seg) - .5) * 1.1
                    nx = px + math.cos(ang) * (length / 3.0)
                    ny = py + math.sin(ang) * (length / 3.0)
                    pygame.draw.line(
                        surface,
                        _clamp_color(_mix(dark, hot, 1 - seg * .3)),
                        (int(px), int(py)), (int(nx), int(ny)),
                        max(1, 3 - seg))
                    px, py = nx, ny

        # 6. TETES AIR (morph / replicate): titik-titik naik lalu jatuh
        if self.kind in ("morph", "replicate") and t < 0.7:
            st = 1.0 - t / 0.7
            for i in range(6):
                a0 = self.seed * 0.17 + i * math.tau / 6
                rr = (10 + 20 * pw) * (0.3 + 0.8 * t)
                dx = int(x + math.cos(a0) * rr)
                dy = int(y + math.sin(a0) * rr * 0.55)
                pygame.draw.circle(surface, (*hot, int(200 * st)),
                                   (dx, dy), max(1, int(2.4 * st)))

        # 7. INTI benturan
        if t < 0.40:
            st = 1.0 - t / 0.40
            sz = int((5 + 9 * pw) * (0.5 + 0.5 * st)) // 2 * 2 + 2
            s = spark_surface(sz, hot)
            s.set_alpha(int(255 * st))
            surface.blit(s, (x - sz - 1, y - sz - 1))


# ============================================================================
# 8.  PROJECTILE SYSTEM  —  WATER SPEAR
# ============================================================================

class ThalgrynProjectile:
    """Water Spear — modular, vektor, delta-time.

    Kontrak atribut: ``position, velocity, speed, damage, lifetime,
    target, radius, rotation, trail, particles, active``.
    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY.

    Proyektil di lapisan FX bersifat VISUAL (damage=0 default): damage
    tetap dihitung gameplay (base_boss / skill), jadi tidak ada perubahan
    angka keseimbangan - hanya pembawaannya yang jadi nyata.
    """

    STATE_TRAVEL = "travel"
    STATE_IMPACT = "impact"
    STATE_DEAD = "dead"

    def __init__(self, x, y, tx, ty, speed=520.0, damage=0,
                 target=None, radius=7.0, homing=6.5, kind="spear",
                 particles=None, on_impact=None, ground=0.0):
        self.position = pygame.Vector2(x, y)
        self.spawn_pos = pygame.Vector2(x, y)
        d = pygame.Vector2(tx - x, ty - y)
        if d.length_squared() < 1e-6:
            d = pygame.Vector2(1.0, 0.0)
        self.velocity = d.normalize() * float(speed)
        self.speed = float(speed)
        self.damage = damage
        self.lifetime = 0.0
        self.max_lifetime = 1.9
        self.target = target
        self.radius = float(radius)
        self.rotation = math.atan2(self.velocity.y, self.velocity.x)
        self.trail = []
        self.trail_life = 0.19
        self.particles = particles
        self.active = True
        self.state = self.STATE_TRAVEL
        self.kind = kind
        self.homing = float(homing)
        self.on_impact = on_impact
        self.ground = float(ground)
        self._impact_age = 0.0
        self._emit_acc = 0.0
        self.hit_pos = pygame.Vector2(tx, ty)
        self.seed = random.randint(0, 9999)

    def kill(self, x=None, y=None):
        if self.state != self.STATE_TRAVEL:
            return
        self.state = self.STATE_IMPACT
        self.hit_pos.update(self.position if x is None
                            else pygame.Vector2(x, y))
        self._impact_age = 0.0
        if self.on_impact:
            try:
                self.on_impact(self)
            except Exception:                # pragma: no cover
                pass

    def update(self, dt):
        if self.state == self.STATE_DEAD:
            return False

        if self.state == self.STATE_IMPACT:
            self._impact_age += dt
            self._age_trail(dt)
            if self._impact_age > 0.26 and not self.trail:
                self.state = self.STATE_DEAD
                self.active = False
                return False
            return True

        self.lifetime += dt
        if self.lifetime > self.max_lifetime:
            self.kill()
            return True

        tgt = self.target
        if tgt is not None and getattr(tgt, "alive", False):
            to = pygame.Vector2(float(tgt.x), float(tgt.y)) - self.position
            if to.length_squared() > 1.0:
                desired = to.normalize() * self.speed
                self.velocity += (desired - self.velocity) \
                    * min(1.0, self.homing * dt)
                if self.velocity.length_squared() > 1e-6:
                    self.velocity.scale_to_length(self.speed)
        self.rotation = math.atan2(self.velocity.y, self.velocity.x)

        self.trail.append([pygame.Vector2(self.position), 0.0])
        if len(self.trail) > 14:
            self.trail.pop(0)
        self._age_trail(dt)
        self.position += self.velocity * dt

        ps = self.particles
        if ps is not None:
            self._emit_acc += dt
            if self._emit_acc >= 0.03:
                self._emit_acc = 0.0
                ang = self.rotation + math.pi + (random.random() - .5) * 1.2
                spd = random.uniform(24, 78)
                ps.spawn(self.position.x, self.position.y,
                         math.cos(ang) * spd, math.sin(ang) * spd,
                         random.uniform(0.14, 0.3), random.uniform(1.5, 3.2),
                         P["water_light"] if random.random() < .5
                         else P["water_high"],
                         color_end=P["water_dark"], drag=3.0, shape="pixel",
                         additive=True)

        if tgt is not None and getattr(tgt, "alive", False):
            hit_r = self.radius + float(getattr(tgt, "radius", 12)) + 4.0
            if self.position.distance_squared_to(
                    pygame.Vector2(float(tgt.x), float(tgt.y))) \
                    <= hit_r * hit_r:
                self.kill(tgt.x, tgt.y)
        return True

    def _age_trail(self, dt):
        for s in self.trail:
            s[1] += dt
        if self.trail:
            self.trail = [s for s in self.trail if s[1] < self.trail_life]

    def draw(self, surface):
        n = len(self.trail)
        if n >= 2:
            step = 9.0
            ux, uy = math.cos(self.rotation), math.sin(self.rotation)
            for i in range(n - 1, -1, -1):
                pv, age = self.trail[i]
                fade = max(0.0, 1.0 - age / self.trail_life)
                d = self.spawn_pos.distance_to(pv)
                if (int(d / step) % 2) or fade <= 0.05:
                    continue
                a = int(150 * fade)
                ln = max(2, int(self.radius * (1.3 - 0.6 * fade)))
                _shard_poly(surface, pv.x, pv.y, self.rotation, ln,
                            max(1, int(self.radius * .45)),
                            P["water_dark"], a)
                pygame.draw.line(surface, _clamp_color(P["water_mid"]),
                                 (int(pv.x - ux * ln), int(pv.y - uy * ln)),
                                 (int(pv.x + ux * ln * .4),
                                  int(pv.y + uy * ln * .4)),
                                 max(1, int(self.radius * .5)))

        if self.state == self.STATE_IMPACT:
            return

        draw_water_spear(surface, self.position.x, self.position.y,
                         self.rotation, age=int(self.lifetime * 60),
                         radius=self.radius, seed=self.seed)

    def draw_impact(self, surface):
        if self.state != self.STATE_IMPACT:
            return
        t = min(1.0, self._impact_age / 0.26)
        a = int(220 * (1.0 - t))
        if a <= 5:
            return
        x, y = int(self.hit_pos.x), int(self.hit_pos.y)
        r = int(9 + 22 * t)
        ring = ring_surface(r, max(1, int(3 * (1 - t))), P["water_light"],
                            255, dashed=9)
        ring.set_alpha(a)
        surface.blit(ring, (x - ring.get_width() // 2,
                            y - ring.get_height() // 2))
        glint = spark_surface(max(3, int(9 * (1 - t))), P["fx_white"])
        glint.set_alpha(a)
        surface.blit(glint, (x - glint.get_width() // 2,
                             y - glint.get_height() // 2))


class ProjectileSystem:
    """Manajer proyektil: spawn / update / draw / auto-cleanup."""

    def __init__(self, particles=None, cap=MAX_PROJECTILES):
        self.projectiles = []
        self.particles = particles
        self.cap = int(cap)

    def count(self):
        return len(self.projectiles)

    def list(self):
        return tuple(self.projectiles)

    def clear(self):
        self.projectiles.clear()

    def spawn(self, x, y, tx, ty, **kw):
        if len(self.projectiles) >= self.cap:
            return None
        kw.setdefault("particles", self.particles)
        pr = ThalgrynProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    def update(self, dt):
        if not self.projectiles:
            return
        self.projectiles = [p for p in self.projectiles if p.update(dt)]

    def draw(self, surface):
        for p in self.projectiles:
            p.draw(surface)
            p.draw_impact(surface)


# ============================================================================
# 9.  SKILL FX  —  lifecycle Q / W / E / R
# ============================================================================

class SkillFX:
    """Efek skill Thalgryn dengan lifecycle bertahap.

    CAST -> CHARGE -> RELEASE -> TRAVEL/AREA -> IMPACT -> AFTER -> FADE.
    Yang digambar di sini adalah bagian yang TIDAK boleh ikut ter-cache:
    mote air tersedot, shockwave, retakan, pilar air, busa, tetes atribut.
    """

    TIMELINE = {
        "q": (0.20, 0.10, 0.20, 0.12, 0.16),
        "w": (0.16, 0.08, 0.16, 0.10, 0.10),
        "e": (0.30, 0.12, 0.30, 0.14, 0.20),
        "r": (0.40, 0.18, 0.30, 0.16, 0.24),
    }

    TINT = {
        "q": ((12, 62, 86), (150, 226, 238)),     # Waveform: arus air
        "w": ((16, 74, 100), (210, 248, 252)),    # Adaptive: spear terang
        "e": ((52, 96, 120), (190, 235, 244)),    # Morph: atribut pucat
        "r": ((10, 52, 76), (235, 252, 255)),     # Replicate: putih air
    }

    RADIUS = WORLD_RADIUS

    def __init__(self, kind, x, y, particles=None, radius=None,
                 aim=(0.0, 0.0), ground=0.0, facing=1):
        self.kind = kind if kind in self.TIMELINE else "q"
        self.x = float(x)
        self.y = float(y)
        self.particles = particles
        self.radius = float(radius if radius is not None
                            else self.RADIUS.get(self.kind, 60.0))
        self.aim = (float(aim[0]) - x, float(aim[1]) - y)
        self.ground = float(ground)
        self.facing = 1 if (facing or 1) >= 0 else -1
        tl = self.TIMELINE[self.kind]
        self.t_charge = tl[0]
        self.t_release = self.t_charge + tl[1]
        self.t_area = self.t_release + tl[2]
        self.t_impact = self.t_area + tl[3]
        self.total = min(self.t_impact + tl[4],
                         float(SKILL_TOTAL.get(self.kind, 1.0)))
        self.age = 0.0
        self.active = True
        self.phase = "cast"
        self._released = False
        self._impacted = False
        self._emit = 0.0
        self.seed = random.randint(0, 9999)

    @property
    def aim_angle(self):
        ax, ay = self.aim
        if abs(ax) < 0.01 and abs(ay) < 0.01:
            return 0.0
        return math.atan2(ay, ax)

    def _set_phase(self):
        a = self.age
        if a < self.t_charge:
            self.phase = "charge"
        elif a < self.t_release:
            self.phase = "release"
        elif a < self.t_area:
            self.phase = "area"
        elif a < self.t_impact:
            self.phase = "impact"
        else:
            self.phase = "fade"

    def update(self, dt):
        self.age += dt
        self._set_phase()
        if self.age >= self.total:
            self.active = False
            return False
        ps = self.particles
        if ps is None:
            return True
        kind = self.kind
        R = self.radius
        ang = self.aim_angle
        tint_d, tint_l = self.TINT[kind]

        if self.phase == "charge":
            self._emit += dt
            gap = 0.05 if kind != "r" else 0.028
            while self._emit >= gap:
                self._emit -= gap
                a = random.random() * math.tau
                rr = R * random.uniform(0.55, 1.05)
                sx = self.x + math.cos(a) * rr
                sy = self.y + math.sin(a) * rr * 0.5 + self.ground * 0.55
                life = random.uniform(0.24, 0.44)
                ps.spawn(sx, sy,
                         (self.x - sx) / life * 0.85,
                         (self.y + self.ground * 0.4 - sy) / life * 0.7,
                         life, random.uniform(1.5, 3.2),
                         tint_l, color_end=tint_d,
                         drag=0.4, shape="pixel", additive=True,
                         fade_pow=0.6, layer="back")
            if kind == "e":
                # E: kolom air naik di sekitar badan
                ps.burst(self.x, self.y + self.ground, 4,
                         speed=(30, 90), life=(0.3, 0.6), size=(2, 4),
                         colors=(P["water_light"], P["water_mid"],
                                 tint_d),
                         gravity=-140.0, drag=1.2, shape="dust",
                         layer="back")
            elif kind == "r":
                ps.burst(self.x, self.y + self.ground, 4,
                         speed=(20, 70), life=(0.3, 0.6), size=(2, 4),
                         colors=(P["ash"], P["smoke"], tint_d),
                         gravity=-40.0, drag=1.4, shape="dust",
                         layer="back")

        elif self.phase == "release" and not self._released:
            self._released = True
            if kind == "q":
                ps.burst(self.x + math.cos(ang) * 6,
                         self.y + math.sin(ang) * 6, 12,
                         speed=(140, 340), life=(0.16, 0.34), size=(2, 4),
                         colors=(P["fx_white"], tint_l, P["water_light"]),
                         spread=1.15, direction=ang, drag=3.4,
                         shape="streak", additive=True)
            elif kind == "w":
                ps.burst(self.x + math.cos(ang) * 10,
                         self.y + math.sin(ang) * 10, 14,
                         speed=(160, 380), life=(0.16, 0.36), size=(2, 4),
                         colors=(P["fx_white"], tint_l, P["water_light"]),
                         spread=0.9, direction=ang, drag=3.2,
                         shape="streak", additive=True)
            else:
                ps.burst(self.x, self.y + self.ground * 0.35, 16,
                         speed=(120, 320), life=(0.2, 0.5), size=(2, 5),
                         colors=(tint_l, P["water_light"], P["fx_white"]),
                         spread=math.tau, gravity=120.0, drag=1.8,
                         shape="shard", rotation_speed=(-15.0, 15.0))

        elif self.phase == "area":
            self._emit += dt
            gap = 0.075 if kind != "r" else 0.035
            while self._emit >= gap:
                self._emit -= gap
                a = random.random() * math.tau
                rr = R * random.uniform(0.25, 1.0)
                ps.spawn(self.x + math.cos(a) * rr,
                         self.y + self.ground + math.sin(a) * rr * 0.36,
                         random.uniform(-16, 16), random.uniform(-52, -20),
                         random.uniform(0.4, 0.9), random.uniform(1.5, 3.2),
                         tint_l, color_end=tint_d,
                         drag=0.5, shape="pixel", additive=True)
            if kind == "e":
                # mote atribut mengorbit (STR/AGI/INT)
                for i in range(3):
                    a0 = self.age * 2.1 + i * math.tau / 3
                    rr = R * 0.55
                    attr_col = (P["str_hot"], P["agi_hot"], P["int_hot"])[i]
                    ps.spawn(self.x + math.cos(a0) * rr,
                             self.y - 6 + math.sin(a0) * rr * 0.5,
                             math.cos(a0 + math.pi / 2) * 30,
                             math.sin(a0 + math.pi / 2) * 18,
                             0.3, 2.0, attr_col,
                             drag=0.2, shape="pixel", additive=True)
            elif kind == "r":
                ps.stream(self.x + math.cos(ang) * R * 0.8,
                          self.y + self.ground * 0.4 + math.sin(ang) * R * .3,
                          self.x, self.y - 6, 6,
                          life=(0.3, 0.5), size=(2, 3),
                          colors=(tint_l, P["water_light"], tint_d),
                          bow=22.0)

        elif self.phase == "impact" and not self._impacted:
            self._impacted = True
            ps.burst(self.x, self.y + self.ground * 0.2, 12,
                     speed=(90, 240), life=(0.28, 0.6), size=(2, 5),
                     colors=(tint_l, P["water_light"], P["ash"]),
                     gravity=430.0, drag=1.0, shape="shard",
                     rotation_speed=(-13.0, 13.0))
        return True

    def draw_ground(self, surface):
        if not self.active:
            return
        dark, hot = self.TINT[self.kind]
        a = self.age
        R = self.radius
        gy = int(self.y + self.ground)
        x = int(self.x)

        t_all = min(1.0, a / max(0.05, self.total))
        haze = int(R * (0.85 + 0.2 * math.sin(a * 4.2))) // 8 * 8
        power = round(0.32 * (1.0 - abs(t_all - 0.35) * 1.5) / 0.05) * 0.05
        if power > 0.02 and haze >= 8 and glow_allowed():
            hs = ground_glow_surface(haze, dark, power)
            surface.blit(hs, (x - hs.get_width() // 2,
                              gy - hs.get_height() // 2),
                         special_flags=pygame.BLEND_RGB_ADD)

        if self.phase in ("release", "area", "impact"):
            spread = min(1.0, a / max(0.05, self.t_area))
            rr = int(R * (0.4 + 0.75 * spread)) // 6 * 6
            alpha = int(200 * (1.0 - spread * 0.5))
            if rr > 8 and alpha > 10:
                ring = ring_surface(rr, max(1, int(4 * (1 - spread)) + 1),
                                    dark, alpha,
                                    dashed=10 if self.kind != "q" else 0)
                surface.blit(ring, (x - ring.get_width() // 2,
                                    gy - ring.get_height() // 2))
            rr2 = int(rr * 0.6)
            if rr2 > 6:
                ring2 = ring_surface(rr2, 1, hot, int(alpha * 0.7))
                surface.blit(ring2, (x - ring2.get_width() // 2,
                                     gy - ring2.get_height() // 2))

    def draw_front(self, surface):
        if not self.active:
            return
        hot = self.TINT[self.kind][1]
        a = self.age
        x, y = int(self.x), int(self.y)
        R = self.radius

        # kolom / pilar air naik saat release..impact (e / r)
        if self.kind in ("e", "r") and self.phase in ("release", "area",
                                                       "impact"):
            k = min(1.0, (a - self.t_release) / max(0.05, self.t_impact))
            hgt = int(R * 0.9 * (0.5 + 0.5 * math.sin(k * math.pi)))
            for i in range(0, hgt, 3):
                tt = i / max(1, hgt)
                w = int((1.0 - tt * 0.5) * 10) + 2
                yy = y - i
                alpha = int(200 * (1.0 - tt) * (1.0 - k * 0.5))
                if alpha <= 0:
                    continue
                pygame.draw.ellipse(
                    surface, (*P["water_mid"], alpha),
                    (x - w, yy, w * 2, 4))
                pygame.draw.ellipse(
                    surface, (*hot, min(255, alpha + 40)),
                    (x - w // 2, yy, w, 2))

        # tetes atribut mengorbit (e)
        if self.kind == "e" and self.phase in ("area", "impact"):
            for i in range(3):
                a0 = a * 2.1 + i * math.tau / 3
                rr = R * 0.55
                attr = (P["str_hot"], P["agi_hot"], P["int_hot"])[i]
                dx = int(x + math.cos(a0) * rr)
                dy = int(y - 6 + math.sin(a0) * rr * 0.5)
                pygame.draw.circle(surface, (*attr, 220), (dx, dy), 3)
                pygame.draw.circle(surface, P["fx_white"], (dx, dy), 1)

        # semburan horizontal (q)
        if self.kind == "q" and self.phase in ("release", "area"):
            ang = self.aim_angle
            f = self.facing
            L = int(R * 1.3 * min(1.0, (a - self.t_release)
                                  / max(0.05, self.t_area)))
            for i in range(3):
                off = (i - 1) * 7
                sx = x + math.cos(ang) * (L * 0.4)
                sy = y + math.sin(ang) * (L * 0.4) + off
                ex = x + math.cos(ang) * L
                ey = y + math.sin(ang) * L + off
                pygame.draw.line(surface, (*P["water_light"], 170),
                                 (int(sx), int(sy)), (int(ex), int(ey)),
                                 3 if i == 1 else 2)
            # kepala gelombang
            hx = x + math.cos(ang) * L
            hy = y + math.sin(ang) * L
            pygame.draw.circle(surface, (*hot, 230), (int(hx), int(hy)), 5)
            pygame.draw.circle(surface, P["fx_white"], (int(hx), int(hy)), 2)
            _ = f


# ============================================================================
# 10. DIRECTOR — mengikat semua sistem FX untuk satu unit Thalgryn
# ============================================================================

def attack_phase(progress):
    """Nama fase serangan untuk progress 0..1 (None di luar serangan)."""
    if progress is None:
        return "NONE"
    G = _renderer()
    if G is not None:
        try:
            return G.attack_phase(progress)
        except Exception:                      # pragma: no cover
            pass
    p = max(0.0, min(1.0, float(progress)))
    for name, a, b in (("ANTICIPATION", 0.0, 0.14), ("WINDUP", 0.14, 0.30),
                       ("SWING", 0.30, 0.48), ("IMPACT", 0.48, 0.62),
                       ("FOLLOW", 0.62, 0.82), ("RECOVERY", 0.82, 1.0)):
        if a <= p < b:
            return name
    return "RECOVERY"


class ThalgrynFXDirector:
    """Mengikat particle + trail + proyektil + impact + skill FX untuk
    satu unit Thalgryn (mini boss; kodenama sama untuk jalur hero)."""

    def __init__(self, hero):
        self.hero = hero
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.projectiles = ProjectileSystem(self.particles)
        self.trail = SwingTrail()
        self.impacts = []
        self.skills = []
        self.state = "IDLE"
        self.prev_state = "IDLE"
        self.state_time = 0.0
        self.anim_phase = "NONE"
        self.swing_active = False
        self.hit_flash = 0.0
        self.time = 0.0
        self.frames = 0
        self.last_x = float(getattr(hero, "x", 0.0))
        self.last_y = float(getattr(hero, "y", 0.0))
        self._swing_seen = False
        self._impact_frame_seen = False
        self._skill_seen = None
        self._last_hp = None
        self._death_done = False
        self._dash_seen = False

    # ── Events ────────────────────────────────────────────────────────
    def on_swing_start(self, x, y, facing):
        self.trail.reset()
        self.trail.width_boost = 1.0
        self.swing_active = True
        gy = y + _ground_dy(self.hero)
        self.particles.burst(
            x + facing * 7, gy, 5,
            speed=(28, 92), life=(0.18, 0.4), size=(2, 4),
            colors=(P["dust"], P["ash"], P["smoke"]),
            spread=1.2, direction=math.pi if facing > 0 else 0.0,
            gravity=95.0, drag=2.6, shape="dust", layer="back")

    def on_swing_end(self):
        self.swing_active = False

    def on_swing_impact_frame(self, x, y, facing):
        """Sapu udara di frame IMPACT (atau connect melee bila dekat)."""
        _g, tip = blade_points(self.hero, x, y)
        ang = math.atan2(tip.y - _g.y, tip.x - _g.x) - math.pi / 2
        # bila target di jangkauan bilah -> connect DI target, bukan di tip
        tgt = getattr(self.hero, "target", None)
        tx, ty = tip.x, tip.y
        melee = False
        if tgt is not None and getattr(tgt, "alive", False):
            d = math.hypot(float(tgt.x) - float(getattr(self.hero, "x", x)),
                           float(tgt.y) - float(getattr(self.hero, "y", y)))
            if d <= MELEE_REACH:
                tx, ty = float(tgt.x), float(tgt.y)
                melee = True
        if melee:
            self.on_impact(tx, ty, ang, 1.0, False, kind="blade")
        else:
            # lempar Water Spear dari ujung bilah ke target
            self.spawn_spear(x, y, tip, ang, heavy=False)
        # sapuan percikan air di ujung bilah (feedback walau meleset)
        self.particles.burst(
            tip.x, tip.y, 7,
            speed=(110, 250), life=(0.1, 0.24), size=(1, 3),
            colors=(P["water_shine"], P["fx_bright"], P["water_light"]),
            spread=1.5, direction=ang, drag=3.6, shape="streak",
            additive=True)
        if not melee:
            self.impacts.append(ImpactFX(tip.x, tip.y, ang, 0.5, False,
                                         kind="blade", ground=0.0,
                                         seed=int(self.frames)))

    def spawn_spear(self, x, y, tip, ang, heavy=False, aim=None):
        """Lepaskan Water Spear dari ujung bilah ke target."""
        tgt = getattr(self.hero, "target", None)
        if (tgt is None or not getattr(tgt, "alive", False)) and aim is None:
            facing = 1 if getattr(self.hero, "direction", 1) >= 0 else -1
            aim = (x + facing * 140, y - 6)
        if aim is None:
            aim = (float(tgt.x), float(tgt.y))
        speed = 520.0 if not heavy else 620.0
        radius = 7.0 if not heavy else 9.5
        power = 1.1 if not heavy else 1.5
        pr = self.projectiles.spawn(
            tip.x, tip.y, aim[0], aim[1],
            speed=speed, damage=0, target=tgt, radius=radius,
            kind="spear", ground=_ground_dy(self.hero),
            on_impact=lambda p: self.on_impact(p.hit_pos.x, p.hit_pos.y,
                                               p.rotation, power, False,
                                               kind="spear"))
        if pr is not None:
            self.particles.burst(tip.x, tip.y, 6,
                                 speed=(90, 220), life=(0.12, 0.3),
                                 size=(1, 3),
                                 colors=(P["fx_white"], P["water_shine"]),
                                 spread=1.9, direction=pr.rotation,
                                 drag=3.2, shape="spark", additive=True)
        return pr

    def on_cast(self, x, y, skill, aim=None):
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        gy = _ground_dy(self.hero)
        if aim is None:
            tgt = getattr(self.hero, "target", None)
            if tgt is not None and getattr(tgt, "alive", False):
                aim = (float(tgt.x), float(tgt.y))
            else:
                facing = 1 if getattr(self.hero, "direction", 1) >= 0 else -1
                aim = (x + facing * 140, y - 6)
        self.skills.append(SkillFX(skill, x, y, self.particles,
                                   aim=aim, ground=gy))
        heavy = skill in ("w", "r")
        if shake_allowed():
            _feel_shake(5.0 if not heavy else 12.0,
                        0.16 if not heavy else 0.38)
        if skill == "w":
            # spear adaptif dari ujung bilah
            _g, tip = blade_points(self.hero, x, y)
            self.spawn_spear(x, y, tip, 0.0, heavy=True, aim=aim)
        elif skill == "r":
            _feel_hit_stop(0.055)
        self.particles.burst(x, y + gy * 0.4, 10,
                             speed=(60, 190), life=(0.2, 0.5), size=(2, 4),
                             colors=(SkillFX.TINT.get(skill, P["fx_dark"])[0],
                                     P["ash"], P["dust"]),
                             spread=math.tau, gravity=150.0, drag=2.0,
                             shape="dust", layer="back")

    def on_dash(self, x, y, ox, oy):
        """Waveform: badan pindah -> jejak arus dari titik asal."""
        gy = _ground_dy(self.hero)
        self.particles.burst(ox, oy + gy, 10,
                             speed=(50, 150), life=(0.3, 0.6), size=(2, 5),
                             colors=(P["water_light"], P["water_mid"],
                                     P["dust"]),
                             gravity=-60.0, drag=1.4, shape="dust",
                             layer="back")
        self.particles.stream(ox, oy, x, y, 12, life=(0.2, 0.4),
                              size=(2, 3),
                              colors=(P["water_light"], P["water_high"],
                                      P["water_mid"]), bow=14.0)
        if shake_allowed():
            _feel_shake(3.4, 0.12)

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="spear"):
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind=kind))
        pw = min(2.0, max(0.35, float(power)))

        spark, edge, hot = (P["water_shine"], P["water_light"],
                            P["fx_white"])
        n = int(9 + 7 * pw) + (6 if crit else 0)
        self.particles.burst(
            x, y, n, speed=(120, 330 + 90 * pw), life=(0.16, 0.42),
            size=(2, 4), colors=(spark, hot, edge),
            spread=2.4, direction=angle, drag=3.6, shape="streak")
        self.particles.burst(
            x, y, int(5 + 3 * pw) + (4 if crit else 0),
            speed=(70, 200), life=(0.3, 0.66), size=(2, 5),
            colors=(edge, P["ash"], P["water_mid"]),
            gravity=470.0, drag=1.1, shape="shard",
            rotation_speed=(-16.0, 16.0))
        if crit:
            self.particles.burst(
                x, y, 8, speed=(180, 380), life=(0.22, 0.5), size=(2, 4),
                colors=(P["gold_light"], P["gold_mid"], spark),
                spread=math.tau, gravity=120.0, drag=2.0, shape="spark",
                additive=True)
        if shake_allowed():
            _feel_shake(4.0 + 3.4 * pw + (3.0 if crit else 0.0),
                        0.17 + 0.08 * pw)
        _feel_hit_stop(0.036 + 0.019 * min(1.5, pw)
                       + (0.014 if crit else 0.0))

    def on_hurt(self, amount=1.0):
        self.hit_flash = 0.16
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        self.particles.burst(
            hx, hy - 8, 7, speed=(80, 210), life=(0.16, 0.34), size=(2, 4),
            colors=(P["water_light"], P["water_shine"], P["fx_white"]),
            drag=3.0, shape="streak", additive=True)
        self.particles.burst(
            hx, hy + 6, 4, speed=(30, 90), life=(0.24, 0.5), size=(2, 5),
            colors=(P["water_mid"], P["smoke"]), gravity=200.0, drag=2.0,
            shape="dust", layer="back")

    def on_death(self, x, y):
        if self._death_done:
            return
        self._death_done = True
        gy = _ground_dy(self.hero)
        self.trail.reset()
        self.particles.clear()
        self.impacts.append(ImpactFX(x, y + gy * 0.35, -math.pi / 2, 2.2,
                                     True, kind="replicate", seed=7))
        self.particles.burst(x, y, 22, speed=(90, 320), life=(0.5, 1.1),
                             size=(2, 6),
                             colors=(P["water_light"], P["water_mid"],
                                     P["water_high"], P["gold_mid"]),
                             spread=math.tau, gravity=430.0, drag=1.1,
                             shape="shard", rotation_speed=(-18.0, 18.0))
        self.particles.burst(x, y + gy, 16, speed=(40, 150),
                             life=(0.5, 1.0), size=(3, 7),
                             colors=(P["dust"], P["smoke"], P["ash"]),
                             spread=math.tau, gravity=-30.0, drag=1.5,
                             shape="dust", layer="back")
        if shake_allowed():
            _feel_shake(9.0, 0.42)

    # ── State machine ─────────────────────────────────────────────────
    def _resolve_state(self):
        h = self.hero
        if not getattr(h, "alive", True):
            return "DEATH"
        if self.hit_flash > 0.0:
            return "HURT"
        skill = getattr(h, "active_skill", None)
        if skill:
            return "SPECIAL" if skill == "r" else "SKILL"
        if getattr(h, "_th_attack_active", False):
            ph = attack_phase(float(getattr(h, "_th_attack_progress", 0.0)))
            if ph in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            if ph in ("SWING", "IMPACT"):
                return "SWING"
            return "ATTACK"
        if getattr(h, "_moving_cached", False):
            return "RUN" if float(getattr(h, "speed", 1.0)) >= 2.2 \
                else "WALK"
        st = getattr(h, "_th_state", None)
        if st in ANIM_PRIORITY:
            return st
        return "IDLE"

    def _update_state(self, dt):
        want = self._resolve_state()
        if want != self.state:
            cur_p = ANIM_PRIORITY.get(self.state, 0)
            new_p = ANIM_PRIORITY.get(want, 0)
            if self.state != "DEATH" and (new_p >= cur_p
                                          or self.state_time > 0.05):
                self.prev_state = self.state
                self.state = want
                self.state_time = 0.0
        self.state_time += dt
        self.anim_phase = str(getattr(self.hero, "_th_attack_phase", None)
                              or "NONE")

    # ── Update / draw ─────────────────────────────────────────────────
    def update(self, dt, x, y):
        if dt <= 0.0:
            return
        self.time += dt
        self.frames += 1
        h = self.hero

        hp = getattr(h, "hp", None)
        if hp is not None:
            if self._last_hp is not None and hp < self._last_hp - 0.01:
                self.on_hurt((self._last_hp - hp)
                             / max(1.0, float(getattr(h, "max_hp", 1.0))))
            self._last_hp = hp
        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)

        self._update_state(dt)

        if self.state == "DEATH":
            self.on_death(x, y)

        # ── cast skill (edge-triggered) ───────────────────────────────
        skill = getattr(h, "active_skill", None)
        if skill != self._skill_seen:
            if skill:
                self.on_cast(x, y, skill)
            self._skill_seen = skill

        # ── dash Q: lompatan posisi besar saat skill q ────────────────
        jump = math.hypot(x - self.last_x, y - self.last_y)
        if jump > 24.0 and skill == "q" and not self._dash_seen:
            self._dash_seen = True
            self.on_dash(x, y, self.last_x, self.last_y)
        elif skill != "q":
            self._dash_seen = False

        # ── ayunan: deteksi fase, rekam trail ─────────────────────────
        facing = 1 if getattr(h, "direction", 1) >= 0 else -1
        attacking = bool(getattr(h, "_th_attack_active", False))
        swinging = attacking and self.anim_phase in ("SWING", "IMPACT",
                                                      "FOLLOW")
        if swinging and not self._swing_seen:
            self.on_swing_start(x, y, facing)
        elif not swinging and self._swing_seen:
            self.on_swing_end()
        self._swing_seen = swinging

        impact_frame = attacking and self.anim_phase == "IMPACT"
        if impact_frame and not self._impact_frame_seen:
            self._impact_frame_seen = True
            self.on_swing_impact_frame(x, y, facing)
        elif not impact_frame:
            self._impact_frame_seen = False

        if swinging:
            grip, tip = blade_points(h, x, y)
            self.trail.push(grip, tip)

        self.last_x = x
        self.last_y = y

        self.trail.update(dt)
        self.particles.update(dt)
        self.projectiles.update(dt)
        if self.impacts:
            self.impacts = [i for i in self.impacts if i.update(dt)]
        if self.skills:
            self.skills = [s for s in self.skills if s.update(dt)]

    def draw_ground(self, surface):
        for s in self.skills:
            s.draw_ground(surface)
        self.particles.draw(surface, layer="back")

    def draw_front(self, surface, x, y):
        self.trail.draw(surface)
        self.projectiles.draw(surface)
        self.particles.draw(surface, layer="front")
        for s in self.skills:
            s.draw_front(surface)
        for i in self.impacts:
            i.draw(surface)
        if self.hit_flash > 0.0:
            self._draw_hit_flash(surface, x, y)
        if DEBUG_CHARACTER:
            draw_debug_overlay(surface, self)

    def _draw_hit_flash(self, surface, x, y):
        k = max(0.0, min(1.0, self.hit_flash / 0.16))
        if int(getattr(self.hero, "hurt_flash_timer", 0) or 0) > 0:
            k *= 0.35
        r = int(18 + 14 * k)
        if glow_allowed():
            g = glow_surface(r, P["water_shine"], 0.55 * k)
            surface.blit(g, (int(x) - r, int(y) - r - 8),
                         special_flags=pygame.BLEND_RGB_ADD)
        s = max(3, int(4 + 8 * k))
        star = spark_surface(s, P["fx_white"])
        star.set_alpha(int(170 * k))
        surface.blit(star, (int(x) - s, int(y) - 16 - s))

    def clear(self):
        self.particles.clear()
        self.projectiles.clear()
        self.trail.reset()
        self.impacts.clear()
        self.skills.clear()
        self.hit_flash = 0.0
        self.swing_active = False
        self._swing_seen = False
        self._impact_frame_seen = False
        self._skill_seen = None
        self._dash_seen = False
        self._last_hp = None
        self._death_done = False

    def stats(self):
        return {
            "state": self.state,
            "prev": self.prev_state,
            "phase": self.anim_phase,
            "particles": self.particles.count(),
            "dropped": self.particles.dropped,
            "projectiles": self.projectiles.count(),
            "impacts": len(self.impacts),
            "skills": len(self.skills),
            "trail": len(self.trail.points),
            "cache": cache_size(),
        }


def _ground_dy(boss):
    G = _renderer()
    dy = getattr(G, "GROUND_DY", 40) if G is not None else 40
    return int(round(float(dy) * render_scale(boss)))


# ============================================================================
# 11.  BUS ADAPTER  (hit-stop & shake lewat combat_feel)
# ============================================================================

try:
    from heroes import combat_feel as _feel
except Exception:                              # pragma: no cover
    _feel = None


def _feel_shake(strength, duration):
    if _feel is None:
        return
    try:
        _feel.shake(strength, duration)
    except Exception:                          # pragma: no cover
        pass


def _feel_hit_stop(seconds):
    if _feel is None:
        return
    try:
        _feel.hit_stop(seconds)
    except Exception:                          # pragma: no cover
        pass


def should_freeze_frame():
    if not THALGRYN_FX_ENABLED or _feel is None:
        return False
    return _feel.should_freeze_frame()


def hit_stop(seconds=0.045):
    _feel_hit_stop(seconds)


def shake(strength=5.0, duration=0.22):
    if not shake_allowed():
        return
    _feel_shake(strength, duration)


# ============================================================================
# 12.  WATER SPEAR RENDERER BERSAMA
# ============================================================================

def draw_water_spear(surface, px, py, angle=0.0, age=0, crit=False,
                     radius=7.0, seed=0):
    """Tombak air: core + glow + bentuk terarah + sparkle orbit + trail.

    Digambar langsung (tanpa transform.rotate) - hemat alokasi.
    """
    px, py = int(px), int(py)
    r = max(3.0, float(radius))
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    px_ = -sin_a
    py_ = cos_a

    # ── glow inti ────────────────────────────────────────────────────
    if glow_allowed():
        g = glow_surface(int(r * 2.4), P["water_light"], 0.5)
        surface.blit(g, (px - int(r * 2.4), py - int(r * 2.4)),
                     special_flags=pygame.BLEND_RGB_ADD)

    # ── bentuk tombak memanjang ──────────────────────────────────────
    tip_len = r * 2.0
    back_len = r * 0.9
    half = r * 0.72
    tip = (px + int(cos_a * tip_len), py + int(sin_a * tip_len))
    back = (px - int(cos_a * back_len), py - int(sin_a * back_len))
    s1 = (px + int(px_ * half), py + int(py_ * half))
    s2 = (px - int(px_ * half), py - int(py_ * half))

    pygame.draw.polygon(surface, (*P["water_darkest"], 200),
                        [tip, s1, back, s2])
    pygame.draw.polygon(surface, (*P["water_dark"], 220),
                        [tip,
                         (px + int(px_ * half * 0.7),
                          py + int(py_ * half * 0.7)),
                         back,
                         (px - int(px_ * half * 0.7),
                          py - int(py_ * half * 0.7))])
    pygame.draw.polygon(surface, (*P["water_mid"], 240),
                        [tip,
                         (px + int(px_ * half * 0.4),
                          py + int(py_ * half * 0.4)),
                         back,
                         (px - int(px_ * half * 0.4),
                          py - int(py_ * half * 0.4))])
    pygame.draw.polygon(surface, (*P["water_light"], 250),
                        [tip,
                         (px + int(px_ * half * 0.2),
                          py + int(py_ * half * 0.2)),
                         back,
                         (px - int(px_ * half * 0.2),
                          py - int(py_ * half * 0.2))])

    # ── garis inti terang ────────────────────────────────────────────
    pygame.draw.line(surface, P["water_high"],
                     back, tip, max(1, int(r * 0.5)))
    pygame.draw.line(surface, P["fx_white"],
                     (back[0] + int(cos_a * 2), back[1] + int(sin_a * 2)),
                     tip, 1)

    # ── ujung terang ─────────────────────────────────────────────────
    pygame.draw.circle(surface, P["water_shine"], tip, max(2, int(r * 0.5)))
    pygame.draw.circle(surface, P["fx_white"], tip, max(1, int(r * 0.3)))

    # ── sparkle orbit ────────────────────────────────────────────────
    spin = (seed * 0.13 + age * 0.28) % math.tau
    for i in range(3):
        a = spin + i * math.tau / 3
        sx = px + int(math.cos(a) * (r + 4))
        sy = py + int(math.sin(a) * (r + 4))
        pygame.draw.circle(surface, P["water_shine"], (sx, sy), 1)


# ============================================================================
# 13.  DEBUG OVERLAY
# ============================================================================

def _debug_font():
    try:
        from _render import get_font
        return get_font(14, "body")
    except Exception:                          # pragma: no cover
        return pygame.font.Font(None, 16)


def draw_debug_overlay(surface, director):
    """Overlay debug direktur: hitbox, state, partikel, phase."""
    try:
        h = director.hero
        x = int(getattr(h, "x", 0))
        y = int(getattr(h, "y", 0))
        r = max(6, int(getattr(h, "radius", 16) * 0.9))
        pygame.draw.rect(surface, (80, 170, 255, 150),
                         pygame.Rect(x - r, y - r - 8, r * 2, r * 2), 1)
        rng = max(10, int(getattr(h, "range", 160) * 0.9))
        f = 1 if (getattr(h, "direction", 1) or 1) >= 0 else -1
        pygame.draw.line(surface, (255, 210, 60, 150), (x, y),
                         (x + int(rng * f), y), 1)
        for p in director.projectiles.list():
            rr = max(3, int(p.radius))
            pygame.draw.circle(surface, (255, 120, 255, 170),
                               (int(p.position.x), int(p.position.y)),
                               rr, 1)
        st = director.stats()
        font = _debug_font()
        lines = [
            "state %s (%s)" % (st["state"], st["phase"]),
            "p %d  d %d  pr %d  im %d  sk %d" % (
                st["particles"], st["dropped"], st["projectiles"],
                st["impacts"], st["skills"]),
        ]
        for i, ln in enumerate(lines):
            img = font.render(ln, True, (190, 255, 235))
            surface.blit(img, (x - 40, y - 120 + i * 14))
    except Exception:                          # pragma: no cover
        pass


# ============================================================================
# 14.  REGISTRY DIRECTOR + API PUBLIK
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Thalgryn."""
    _sync_palette()
    d = getattr(hero, "_th_fx", None)
    if d is None:
        d = ThalgrynFXDirector(hero)
        try:
            hero._th_fx = d
        except Exception:                      # pragma: no cover
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
    except Exception:                          # pragma: no cover
        pass
    director.clear()


def attach(hero):
    if not THALGRYN_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                          # pragma: no cover
        return False
    try:
        hero._th_live_fx = True
    except Exception:                          # pragma: no cover
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
        except Exception:                      # pragma: no cover
            step = 0.0
    else:                                      # pragma: no cover
        now = pygame.time.get_ticks()
        if _LAST_TICK_MS is None:
            _LAST_TICK_MS = now
            return 0.0
        ms = now - _LAST_TICK_MS
        _LAST_TICK_MS = now
        if ms <= 0:
            return 0.0
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
    _DIRECTORS.clear()
    if _feel is not None:
        try:
            _feel.reset()
        except Exception:                      # pragma: no cover
            pass


def total_particles():
    return sum(d.particles.count() for d in _DIRECTORS)


def projectiles_for(hero):
    d = getattr(hero, "_th_fx", None)
    if d is None:
        return ()
    return d.projectiles.list()


# ── hook yang dipanggil renderer / heroes/__init__.py ──────────────────────

def draw_ground_layer(surface, hero, x, y):
    if not THALGRYN_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_th_fx", None)
    if d is not None:
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    if not THALGRYN_FX_ENABLED:
        return
    d = director_for(hero)
    d.draw_front(surface, x, y)


# ── hook yang dipanggil _entity.py / bosses/base_boss.py ───────────────────

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Bilah air Thalgryn mendarat di target (basic attack melee)."""
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
    """Water Spear / proc mengenai target."""
    if not THALGRYN_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    director_for(hero).on_impact(x, y, angle, power, bool(crit), kind=kind)


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """Skill Thalgryn meledak di sebuah titik (Q/E/R AOE)."""
    if not THALGRYN_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    if len(d.skills) >= MAX_SKILLS:
        d.skills.pop(0)
    fx = SkillFX(skill, x, y, d.particles, radius)
    d.skills.append(fx)
    kind = {"q": "wave", "w": "spear", "e": "morph",
            "r": "replicate"}.get(skill, "spear")
    d.on_impact(x, y, 0.0, 1.3 if skill != "r" else 2.0, skill == "r",
                kind=kind)


def notify_skill_cast(hero, skill):
    if not THALGRYN_FX_ENABLED or hero is None or skill not in SKILL_DUR:
        return
    d = director_for(hero)
    d.on_cast(float(getattr(hero, "x", 0.0)),
              float(getattr(hero, "y", 0.0)), skill)
