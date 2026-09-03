# ============================================================================
# heroes/vhalzun_fx.py
# ----------------------------------------------------------------------------
# VHALZUN — THE REAPER OF SOULS  ·  LAPISAN TEMPUR HIDUP (v2)
#
# Pasangan dari renderer ``bosses/level5.py :: _NS_vhalzun``.  Pembagian
# tugasnya tegas:
#
#   renderer  -> SATU-SATUNYA pemilik geometri badan & sabit (rig, palet,
#                pose, controller animasi, ARC ayunan, telegraph fallback)
#   modul ini-> SEMUA yang hidup di RUANG LAYAR skala 1:1 — swing trail,
#                particle system, proyektil (death pulse & reaper scythe),
#                skill FX q/w/e/r, impact FX, afterimage, overlay debug
#   combat_feel -> bus global hit-stop & screen shake (dipakai bersama)
#
# Kenapa dipisah?  Di lane hero, sprite badan di-*cache* lalu
# ``smoothscale``-kan.  Efek apa pun yang digambar ke canvas badan ikut
# BEKU dan ikut MENYUSUT.  Dengan memisahkan lapisan hidup ke ruang layar,
# trail/partikel/proyektil selalu 60 fps sejati dan selalu setajam layar.
#
# Modul ini TIDAK pernah menghitung ulang pose.  Ia MEMBACA
# ``_NS_vhalzun.pose_of()`` / ``scythe_points()`` lewat jembatan malas
# ``_renderer()``, jadi sabit dan trail-nya mustahil berbeda satu frame
# pun.
#
# 100% PROSEDURAL: tidak ada PNG / JPG / GIF / sprite-sheet / aset
# eksternal dan tidak ada ``pygame.image.load`` di mana pun.
# ============================================================================

import math
import random

import pygame

try:
    from heroes import combat_feel as _feel
except Exception:                                # pragma: no cover
    try:
        import combat_feel as _feel              # type: ignore
    except Exception:
        _feel = None


# ============================================================================
# 1.  KONSTANTA & KONTRAK
# ============================================================================

#: Nama karakter yang dikerjakan (satu sumber kebenaran).
CHARACTER_NAME = "vhalzun"

#: Overlay debug (hitbox, hurtbox, state, FPS, jumlah partikel, ...).
DEBUG_CHARACTER = False

#: Master switch lapisan hidup.  False -> renderer memakai fallback canvas.
VHALZUN_FX_ENABLED = True

#: Cap keras — tidak ada satu pun sistem yang boleh tumbuh tanpa batas.
MAX_PARTICLES = 220
MAX_PROJECTILES = 10
TRAIL_SAMPLES = 12
MAX_IMPACTS = 8
MAX_SKILLS = 4
MAX_AFTERIMAGES = 8

FIXED_DT = 1.0 / 60.0

#: Kecepatan proyektil (px dunia / detik).
ORB_SPEED = 330.0            # death pulse (serangan dasar jarak jauh)
SCYTHE_WAVE_SPEED = 540.0    # reaper's scythe (skill E)

#: Durasi pose skill dalam FRAME — HARUS sama dengan
#: ``bosses/level5._NS_vhalzun.SKILL_DUR`` dan timer AI di base_boss.
SKILL_DUR = {"q": 60, "w": 80, "e": 60, "r": 100}

#: Radius efek di RUANG DUNIA — sama dengan radius damage AI
#: (``_smart_ai_vhalzun``: q <= 130, w <= 150, e target tunggal,
#: r wraith radius 150).  Dikunci oleh tes regresi.
WORLD_RADIUS = {"q": 130.0, "w": 150.0, "e": 60.0, "r": 150.0}

#: Jarak dunia (px) di bawahnya Vhalzun menebas dengan sabit.
#: Satu sumber kebenaran bersama renderer + hook base_boss.
MELEE_REACH = 96.0

#: Fase serangan (fraksi 0..1) — identik dengan renderer.
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.12),
    ("WINDUP",       0.12, 0.30),
    ("SWING",        0.30, 0.50),
    ("IMPACT",       0.50, 0.62),
    ("FOLLOW",       0.62, 0.82),
    ("RECOVERY",     0.82, 1.00),
)

#: Jendela hit aktif + frame benturan/rilis.
ATTACK_ACTIVE_WINDOW = (0.30, 0.55)
ATTACK_IMPACT_FRAME = 0.42
ATTACK_RELEASE_FRAME = 0.32
ATK_IMPACT = ATTACK_IMPACT_FRAME
ATK_RELEASE = ATTACK_RELEASE_FRAME

#: Prioritas state animasi — angka besar menang, DEATH mengunci.
ANIM_STATES = {
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

#: Lifecycle skill: CAST -> CHARGE -> RELEASE -> AREA -> IMPACT -> AFTER.
SKILL_PHASES = (
    ("CAST",    0.00, 0.16),
    ("CHARGE",  0.16, 0.34),
    ("RELEASE", 0.34, 0.46),
    ("AREA",    0.46, 0.74),
    ("IMPACT",  0.74, 0.86),
    ("AFTER",   0.86, 1.00),
)


def attack_phase(progress):
    """Nama fase serangan untuk progress 0..1 (identik renderer)."""
    p = max(0.0, min(1.0, float(progress)))
    for name, a, b in ATTACK_PHASES:
        if a <= p < b:
            return name
    return "RECOVERY"


def skill_phase(t):
    """Nama fase skill untuk t 0..1."""
    p = max(0.0, min(1.0, float(t)))
    for name, a, b in SKILL_PHASES:
        if a <= p < b:
            return name
    return "AFTER"


# ============================================================================
# 2.  PALETTE — Reaper of Souls (disinkronkan dari renderer)
# ============================================================================

#: Palet fallback — langsung tersedia saat modul diimpor.  Saat renderer
#: ditemukan, ``_sync_palette()`` MUTASI dict ini in-place (bukan
#: mengikat ulang nama) supaya semua referensi ``_P`` ikut terbarui.
VHALZUN_PALETTE = {
    "outline": (3, 8, 7), "robe_darkest": (8, 20, 18),
    "robe_dark": (18, 42, 36), "robe_mid": (35, 72, 58),
    "robe_light": (58, 110, 88), "robe_high": (95, 155, 125),
    "robe_shine": (150, 200, 175),
    "inner_darkest": (5, 12, 10), "inner_dark": (12, 25, 20),
    "inner_mid": (22, 45, 35),
    "bone_dark": (60, 75, 55), "bone_mid": (110, 130, 100),
    "bone_light": (170, 185, 155), "bone_shine": (215, 225, 200),
    "necro_darkest": (5, 30, 10), "necro_dark": (18, 75, 25),
    "necro_mid": (40, 155, 55), "necro_light": (90, 220, 95),
    "necro_bright": (150, 250, 140), "necro_hot": (200, 255, 180),
    "necro_white": (235, 255, 220), "blade_dark": (35, 60, 40),
    "blade_mid": (75, 130, 80), "blade_light": (130, 200, 130),
    "blade_shine": (200, 245, 200), "gold_dark": (85, 60, 15),
    "gold_mid": (155, 115, 35), "gold_light": (215, 180, 70),
    "gold_shine": (250, 225, 145), "wood_dark": (40, 25, 15),
    "wood_mid": (70, 45, 25), "wood_light": (110, 78, 45),
    "eye_dark": (25, 75, 20), "eye_mid": (80, 200, 60),
    "eye_bright": (170, 255, 130), "eye_hot": (230, 255, 200),
    "purple_dark": (35, 15, 55), "purple_mid": (75, 40, 115),
    "shadow": (0, 0, 0), "shadow_deep": (3, 6, 4),
    "white": (255, 255, 255),
}

_P = VHALZUN_PALETTE
_PALETTE_SYNCED = False


def _sync_palette():
    """Salin palet dari renderer sekali (mutasi in-place, aman dipanggil
    berkali-kali — termasuk sebelum ``_renderer`` didefinisikan)."""
    global _PALETTE_SYNCED
    if _PALETTE_SYNCED:
        return
    try:
        G = _renderer()
    except Exception:
        G = None
    if G is not None:
        base = getattr(G, "PALETTE", None)
        if isinstance(base, dict) and base:
            _P.update(base)
    _PALETTE_SYNCED = True


# ============================================================================
# 3.  GERBANG KUALITAS & UTILITAS GAMBAR PROSEDURAL
# ============================================================================

def _quality():
    try:
        from mobile.perf import Quality
        return Quality
    except Exception:                          # pragma: no cover
        return None


def particle_budget():
    """Faktor jumlah partikel (0.0 = partikel dimatikan total)."""
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
    if _feel is not None:
        try:
            return bool(getattr(_feel, "SHAKE", None) is not None)
        except Exception:
            pass
    return True


# ── jembatan renderer (lazy) ─────────────────────────────────────────
_RENDERER = None          # None = belum dicari, False = tidak ada


def _renderer():
    """Muat ``_NS_vhalzun`` dari bosses.level5 sekali; None kalau gagal."""
    global _RENDERER
    if _RENDERER is False:
        return None
    if _RENDERER is None:
        try:
            from bosses import level5 as _L
            _RENDERER = getattr(_L, "_NS_vhalzun", None) or False
        except Exception:                      # pragma: no cover
            _RENDERER = False
    return _RENDERER or None


def pose_of(boss):
    """(action, phase, ap) dari renderer — sinkron dengan yang digambar."""
    G = _renderer()
    if G is not None:
        try:
            return G.pose_of(boss)
        except Exception:
            pass
    skill = getattr(boss, "active_skill", None)
    if skill:
        return ("cast_" + str(skill), float(getattr(boss, "pulse", 0.0)), 0.0)
    if getattr(boss, "_vhz_attack_active", False):
        return ("attack", float(getattr(boss, "pulse", 0.0)),
                float(getattr(boss, "_vhz_attack_progress", 0.0) or 0.0))
    return ("idle", float(getattr(boss, "pulse", 0.0)), 0.0)


def scythe_points(boss, x, y):
    """(pivot, tip) pygame.Vector2 ruang LAYAR dari renderer."""
    G = _renderer()
    if G is not None:
        try:
            return G.scythe_points(boss, x, y)
        except Exception:
            pass
    f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
    sc = body_scale(boss)
    pivot = pygame.Vector2(x + 12 * f * sc, y - 32 * sc)
    tip = pygame.Vector2(x + 58 * f * sc, y - 4 * sc)
    return (pivot, tip)


def body_scale(boss):
    sc = getattr(boss, "_render_scale", 1.0)
    try:
        sc = float(sc)
    except (TypeError, ValueError):
        sc = 1.0
    return sc if sc > 0.01 else 1.0


def ground_dy(boss):
    """Offset garis tanah dari titik jangkar (px layar)."""
    G = _renderer()
    base = float(getattr(G, "GROUND_DY", 48)) if G is not None else 48.0
    return base * body_scale(boss)


def screen_point(boss, x, y, lx, ly):
    """Peta offset lokal rig -> ruang layar (mirror + skala)."""
    f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
    sc = body_scale(boss)
    return (x + lx * f * sc, y + ly * sc)


# ── cache surface prosedural ─────────────────────────────────────────
_CACHE = {}
_CACHE_MAX = 160


def _cache_put(key, surf):
    if len(_CACHE) >= _CACHE_MAX:
        _CACHE.pop(next(iter(_CACHE)))
    _CACHE[key] = surf
    return surf


def clear_cache():
    _CACHE.clear()


def cache_size():
    return len(_CACHE)


def glow_surface(radius, color, power=1.0):
    """Glow radial lembut (cache per radius+warna)."""
    radius = max(2, int(radius))
    key = ("glow", radius, tuple(color[:3]), round(power, 2))
    s = _CACHE.get(key)
    if s is None:
        size = radius * 2 + 2
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = size // 2
        for r in range(radius, 0, -1):
            t = 1.0 - r / float(radius)
            a = int(255 * (t ** (1.6 + power)))
            if a > 0:
                pygame.draw.circle(s, (*color[:3], min(255, a)), (cx, cx), r)
        s = _cache_put(key, s)
    return s


def ring_surface(radius, thickness, color, alpha=255, teeth=0):
    """Cincin chunky; ``teeth`` > 0 -> cincin bergerigi (bukan lingkaran
    polos) — dipakai nova Death Pulse & shockwave."""
    radius = max(2, int(radius))
    key = ("ring", radius, int(thickness), tuple(color[:3]), int(alpha),
           int(teeth))
    s = _CACHE.get(key)
    if s is None:
        size = radius * 2 + 6
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        col = (*color[:3], max(0, min(255, int(alpha))))
        if teeth > 0:
            pts_o, pts_i = [], []
            n = max(8, teeth * 2)
            for i in range(n):
                ang = i * math.tau / n
                rr = radius if i % 2 == 0 else radius - thickness
                pts_o.append((c + math.cos(ang) * rr, c + math.sin(ang) * rr))
                pts_i.append((c + math.cos(ang + math.tau / n) * (radius - thickness * 2),
                              c + math.sin(ang + math.tau / n) * (radius - thickness * 2)))
            pygame.draw.polygon(s, col, pts_o + pts_i[::-1])
        else:
            pygame.draw.circle(s, col, (c, c), radius, max(1, int(thickness)))
        s = _cache_put(key, s)
    return s


def ellipse_ring_surface(rx, ry, thickness, color, alpha=255):
    """Cincin ellipse (proyeksi tanah) — cache per ukuran."""
    rx, ry = max(2, int(rx)), max(1, int(ry))
    key = ("ering", rx, ry, int(thickness), tuple(color[:3]), int(alpha))
    s = _CACHE.get(key)
    if s is None:
        w, h = rx * 2 + 6, ry * 2 + 6
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        col = (*color[:3], max(0, min(255, int(alpha))))
        pygame.draw.ellipse(s, col, (3, 3, rx * 2, ry * 2),
                            max(1, int(thickness)))
        s = _cache_put(key, s)
    return s


def skull_decal(size, alpha=255):
    """Tengkorak pixel-art kecil (cache) — orbit Heartstopper, nova Q."""
    size = max(4, int(size))
    key = ("skull", size, int(alpha))
    s = _CACHE.get(key)
    if s is None:
        w = h = size * 2 + 4
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        a = max(0, min(255, int(alpha)))
        bone = (*_P["bone_mid"], a)
        bone_hi = (*_P["bone_light"], a)
        dark = (*_P["shadow_deep"], a)
        eye = (*_P["eye_bright"], a)
        # dome
        pygame.draw.circle(s, bone, (cx, cy - 1), size)
        pygame.draw.rect(s, bone, (cx - size + 2, cy - 1, (size - 2) * 2, 3))
        # highlight kiri-atas
        pygame.draw.rect(s, bone_hi, (cx - size // 2, cy - size - 1, 2, 2))
        # mata
        pygame.draw.rect(s, dark, (cx - size // 2 - 1, cy - 2, 3, 3))
        pygame.draw.rect(s, dark, (cx + size // 2 - 1, cy - 2, 3, 3))
        pygame.draw.rect(s, eye, (cx - size // 2 - 1, cy - 1, 2, 2))
        pygame.draw.rect(s, eye, (cx + size // 2 - 1, cy - 1, 2, 2))
        # hidung + gigi
        pygame.draw.rect(s, dark, (cx - 1, cy + 1, 2, 2))
        for i in range(3):
            pygame.draw.rect(s, dark, (cx - 2 + i * 2, cy + 3, 1, 2))
        s = _cache_put(key, s)
    return s


def wraith_sprite(size, tint=None, alpha=210):
    """Siluet wraith (hantu) pixel-art — Ghost Shroud & death FX."""
    size = max(6, int(size))
    key = ("wraith", size, tuple(tint or _P["necro_light"]), int(alpha))
    s = _CACHE.get(key)
    if s is None:
        w = size * 2 + 6
        h = size * 3 + 6
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        cx = w // 2
        col = (*(tint or _P["necro_light"])[:3], max(0, min(255, alpha)))
        dark = (*_P["necro_dark"], max(0, min(255, int(alpha * 0.7))))
        # kepala + badan meruncing (polygon)
        pts = [
            (cx, 3),
            (cx + size // 2 + 1, 3 + size // 2),
            (cx + size, 3 + size + size // 2),
            (cx + size - 1, 3 + size * 2),
            (cx + size // 2, h - 3),
            (cx, 3 + size * 2 + 2),
            (cx - size // 2, h - 6),
            (cx - size + 1, 3 + size * 2),
            (cx - size, 3 + size + size // 2),
            (cx - size // 2 - 1, 3 + size // 2),
        ]
        pygame.draw.polygon(s, dark, pts)
        pygame.draw.polygon(s, col, [(px - 1, py - 1) if i % 2 else (px, py)
                                     for i, (px, py) in enumerate(pts)])
        # mata gelap
        pygame.draw.rect(s, (*_P["shadow_deep"], alpha),
                         (cx - size // 2 - 1, 3 + size // 2, 2, 3))
        pygame.draw.rect(s, (*_P["shadow_deep"], alpha),
                         (cx + size // 2 - 1, 3 + size // 2, 2, 3))
        s = _cache_put(key, s)
    return s


def scythe_blade_decal(size, alpha=255):
    """Siluet bilah sabit (untuk proyektil Reaper's Scythe)."""
    size = max(8, int(size))
    key = ("blade", size, int(alpha))
    s = _CACHE.get(key)
    if s is None:
        w = h = size * 2 + 4
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        c = w // 2
        a = max(0, min(255, int(alpha)))
        th0, th1 = -0.35, 1.15
        n = 12
        outer = [(c + size * math.cos(th0 + (th1 - th0) * i / n),
                  c + size * math.sin(th0 + (th1 - th0) * i / n))
                 for i in range(n + 1)]
        inner = [(c + (size * 0.42) * math.cos(th1 - (th1 - th0) * i / n),
                  c + (size * 0.42) * math.sin(th1 - (th1 - th0) * i / n))
                 for i in range(n + 1)]
        pygame.draw.polygon(s, (*_P["blade_dark"], a), outer + inner[::-1])
        mid = [(c + (size * 0.75) * math.cos(th0 + (th1 - th0) * i / n),
                c + (size * 0.75) * math.sin(th0 + (th1 - th0) * i / n))
               for i in range(n + 1)]
        pygame.draw.polygon(s, (*_P["blade_mid"], a), outer + mid[::-1])
        pygame.draw.lines(s, (*_P["blade_shine"], a), False, outer, 1)
        s = _cache_put(key, s)
    return s


def _blit_faded(surface, surf, cx, cy, alpha=255.0, additive=False):
    """Blit surface dengan alpha dinamis (jalur murah: set_alpha)."""
    alpha = max(0, min(255, int(alpha)))
    if alpha <= 2 or surf is None:
        return
    cx, cy = int(cx), int(cy)
    if additive and glow_allowed():
        prev = surf.get_alpha()
        surf.set_alpha(alpha)
        surface.blit(surf, (cx - surf.get_width() // 2,
                            cy - surf.get_height() // 2),
                     special_flags=pygame.BLEND_RGB_ADD)
        surf.set_alpha(prev)
        return
    prev = surf.get_alpha()
    surf.set_alpha(alpha)
    surface.blit(surf, (cx - surf.get_width() // 2,
                        cy - surf.get_height() // 2))
    surf.set_alpha(prev)


def blit_add(surface, src, pos, alpha=255):
    """Blit aditif (BLEND_RGB_ADD) — untuk core glow panas."""
    alpha = max(0, min(255, int(alpha)))
    if alpha <= 2:
        return
    prev = src.get_alpha()
    src.set_alpha(alpha)
    surface.blit(src, (int(pos[0]), int(pos[1])),
                 special_flags=pygame.BLEND_RGB_ADD)
    src.set_alpha(prev)


def shard_poly(surface, cx, cy, ang, length, width, color, alpha=255):
    """Serpihan tajam (polygon) menghadap arah ``ang``."""
    cx, cy = int(cx), int(cy)
    dx, dy = math.cos(ang), math.sin(ang)
    px, py = -dy, dx
    L, W = length, width
    pts = [
        (cx + dx * L, cy + dy * L),
        (cx + px * W, cy + py * W),
        (cx - dx * L * 0.6, cy - dy * L * 0.6),
        (cx - px * W, cy - py * W),
    ]
    pygame.draw.polygon(surface, (*color[:3], max(0, min(255, int(alpha)))),
                        pts)


def spark_star(surface, cx, cy, size, color, alpha, spikes=8, rot=0.3):
    """Bintang kilat benturan (polygon berduri — bukan lingkaran)."""
    cx, cy = int(cx), int(cy)
    pts = []
    for i in range(spikes * 2):
        ang = rot + i * math.pi / spikes
        r = size if i % 2 == 0 else size * 0.38
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    pygame.draw.polygon(surface, (*color[:3], max(0, min(255, int(alpha)))),
                        pts)


def taper_lane(surface, x0, y0, x1, y1, w0, w1, color, alpha):
    """Pita meruncing (dipakai arus jiwa / leech stream)."""
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / d, dx / d
    pts = [
        (x0 + nx * w0, y0 + ny * w0),
        (x1 + nx * w1, y1 + ny * w1),
        (x1 - nx * w1, y1 - ny * w1),
        (x0 - nx * w0, y0 - ny * w0),
    ]
    pygame.draw.polygon(surface, (*color[:3], max(0, min(255, int(alpha)))),
                        pts)


def _clamp_color(color):
    return tuple(max(0, min(255, int(c))) for c in color)


def darken(color, k):
    return _clamp_color((color[0] * k, color[1] * k, color[2] * k))


# ============================================================================
# 4.  PARTICLE SYSTEM  (reusable: posisi, kecepatan, akselerasi, umur,
#     rotasi, alpha, gravity, arah, spread, burst)
# ============================================================================

class Particle:
    """Satu partikel dengan atribut lengkap + fade + gravity + drag."""

    __slots__ = ("x", "y", "vx", "vy", "ax", "ay", "life", "max_life",
                 "size", "rotation", "rotation_speed", "alpha", "gravity",
                 "color", "shape", "drag", "additive", "layer", "seed")

    def __init__(self, x, y, vx, vy, life, size, color, shape="orb",
                 gravity=0.0, rotation=0.0, rotation_speed=0.0,
                 drag=0.0, additive=False, layer="front", seed=0.0,
                 ax=0.0, ay=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.ax = float(ax)
        self.ay = float(ay)
        self.life = float(life)
        self.max_life = float(life)
        self.size = float(size)
        self.rotation = float(rotation)
        self.rotation_speed = float(rotation_speed)
        self.alpha = 255
        self.gravity = float(gravity)
        self.color = tuple(color[:3])
        self.shape = shape
        self.drag = float(drag)
        self.additive = bool(additive)
        self.layer = layer
        self.seed = float(seed)

    def update(self, dt):
        if self.drag > 0.0:
            k = math.exp(-self.drag * dt)
            self.vx *= k
            self.vy *= k
        self.vx += self.ax * dt
        self.vy += (self.ay + self.gravity) * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rotation_speed * dt
        self.life -= dt
        t = self.life / self.max_life if self.max_life > 0 else 0.0
        # fade-out di 40% terakhir umur
        self.alpha = int(255 * min(1.0, t / 0.4))

    @property
    def alive(self):
        return self.life > 0.0

    def draw(self, surface):
        if self.alpha <= 4:
            return
        x, y = int(self.x), int(self.y)
        c = self.color
        a = self.alpha
        s = self.size
        sh = self.shape
        if sh == "orb":
            if glow_allowed() and s >= 2.5:
                _blit_faded(surface, glow_surface(int(s * 2.2), c, 0.7),
                            x, y, a * 0.75, additive=self.additive)
            pygame.draw.circle(surface, (*c, a), (x, y), max(1, int(s * 0.7)))
        elif sh == "spark":
            if glow_allowed():
                _blit_faded(surface, glow_surface(int(s * 2.0), c, 0.8),
                            x, y, a * 0.8, additive=True)
            pygame.draw.circle(surface, (255, 255, 255, a), (x, y),
                               max(1, int(s * 0.5)))
        elif sh == "streak":
            ln = max(2, int(s * 2.2))
            sp = math.hypot(self.vx, self.vy) or 1.0
            dx, dy = self.vx / sp, self.vy / sp
            pygame.draw.line(surface, (*c, a), (x, y),
                             (x - int(dx * ln), y - int(dy * ln)),
                             max(1, int(s * 0.6)))
            pygame.draw.circle(surface, (255, 255, 255, a), (x, y),
                               max(1, int(s * 0.4)))
        elif sh == "shard":
            ang = self.rotation
            if ang == 0.0:
                ang = math.atan2(self.vy, self.vx)
            shard_poly(surface, x, y, ang,
                       max(2.0, s * 1.6), max(1.0, s * 0.55), c, a)
        elif sh == "bone":
            # serpihan tulang chunky yang berputar
            r = max(2, int(s))
            dx, dy = math.cos(self.rotation), math.sin(self.rotation)
            pygame.draw.line(surface, (*c, a),
                             (x - int(dx * r), y - int(dy * r)),
                             (x + int(dx * r), y + int(dy * r)),
                             max(2, int(s * 0.8)))
            pygame.draw.circle(surface, (*_P["bone_light"], a),
                               (x - int(dx * r), y - int(dy * r)), 1)
            pygame.draw.circle(surface, (*_P["bone_light"], a),
                               (x + int(dx * r), y + int(dy * r)), 1)
        elif sh == "soul":
            # wisp jiwa: kepala bulat + ekor mengecil ke bawah
            r = max(1, int(s * 0.8))
            pygame.draw.circle(surface, (*c, a), (x, y), r)
            pygame.draw.circle(surface, (*c, a // 2), (x, y - r - 1),
                               max(1, r - 1))
            pygame.draw.circle(surface, (255, 255, 255, a), (x, y - 1), 1)
        elif sh == "ember":
            pygame.draw.rect(surface, (*c, a), (x, y, max(1, int(s)),
                                                max(1, int(s))))
            if a > 120:
                pygame.draw.rect(surface, (255, 255, 255, a // 2),
                                 (x, y, 1, 1))
        elif sh == "dust":
            pygame.draw.circle(surface, (*c, max(8, a // 2)), (x, y),
                               max(1, int(s)))
        else:  # pragma: no cover - jaga-jaga
            pygame.draw.circle(surface, (*c, a), (x, y), max(1, int(s)))


class ParticleSystem:
    """Pool partikel reusable dengan cap keras + spawn/burst/directional."""

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = int(cap)
        self.parts = []

    def count(self):
        return len(self.parts)

    def spawn(self, x, y, vx, vy, life, size, color, shape="orb",
              gravity=0.0, rotation=0.0, rotation_speed=0.0, drag=0.0,
              additive=False, layer="front", seed=0.0, ax=0.0, ay=0.0):
        if len(self.parts) >= self.cap:
            self.parts.pop(0)
        self.parts.append(Particle(x, y, vx, vy, life, size, color, shape,
                                   gravity=gravity, rotation=rotation,
                                   rotation_speed=rotation_speed, drag=drag,
                                   additive=additive, layer=layer, seed=seed,
                                   ax=ax, ay=ay))

    def burst(self, x, y, n, speed=(60.0, 220.0), life=(0.2, 0.5),
              size=(1.5, 3.5), colors=((40, 155, 55),), spread=math.tau,
              direction=None, gravity=0.0, drag=1.0, shape="orb",
              additive=False, layer="front", rotation_speed=None,
              accel=(0.0, 0.0)):
        """Ledakan n partikel dengan spread acak di sekitar direction."""
        n = max(0, int(n * particle_budget()))
        if n <= 0:
            return
        for _ in range(n):
            if direction is None:
                ang = random.uniform(0.0, math.tau)
            else:
                ang = direction + random.uniform(-spread / 2, spread / 2)
            sp = random.uniform(*speed)
            lf = random.uniform(*life)
            sz = random.uniform(*size)
            color = random.choice(colors)
            rs = 0.0
            if rotation_speed is not None:
                rs = random.uniform(*rotation_speed)
            self.spawn(x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                       lf, sz, color, shape=shape, gravity=gravity,
                       drag=drag, rotation=random.uniform(0.0, math.tau),
                       rotation_speed=rs, additive=additive, layer=layer,
                       seed=random.uniform(0.0, 10.0),
                       ax=accel[0], ay=accel[1])

    def stream_toward(self, x, y, tx, ty, n, speed=(80.0, 160.0),
                      life=(0.3, 0.6), size=(1.5, 3.0),
                      colors=((90, 220, 95),), shape="soul", drag=0.0,
                      layer="front", accel=(0.0, 0.0)):
        """Partikel yang bergerak MENUJU titik (vakum jiwa / leech)."""
        n = max(0, int(n * particle_budget()))
        if n <= 0:
            return
        dx, dy = tx - x, ty - y
        d = math.hypot(dx, dy) or 1.0
        for _ in range(n):
            off = random.uniform(6.0, max(7.0, d * 0.25))
            sx = x + dx / d * off + random.uniform(-10, 10)
            sy = y + dy / d * off + random.uniform(-10, 10)
            sp = random.uniform(*speed)
            self.spawn(sx, sy, dx / d * sp, dy / d * sp,
                       random.uniform(*life), random.uniform(*size),
                       random.choice(colors), shape=shape, drag=drag,
                       layer=layer, rotation=random.uniform(0, math.tau),
                       seed=random.uniform(0, 10),
                       ax=accel[0], ay=accel[1])

    def update(self, dt):
        if not self.parts:
            return
        keep = []
        for p in self.parts:
            p.update(dt)
            if p.alive:
                keep.append(p)
        self.parts = keep

    def draw(self, surface, layer="front"):
        for p in self.parts:
            if p.layer == layer:
                p.draw(surface)

    def draw_all(self, surface, skip_layer=None):
        for p in self.parts:
            if p.layer != skip_layer:
                p.draw(surface)

    def clear(self):
        self.parts.clear()


# ============================================================================
# 5.  SWING TRAIL  (ribbon sabit dari histori posisi ujung bilah)
# ============================================================================

class SwingTrail:
    """Ribbon translusen yang mengikuti jejak ujung bilah sabit.

    Menyimpan sampel posisi (OLD ... CURRENT) selama bilah bergerak
    cepat; digambar sebagai polygon sabit memudar + partikel pixel di
    tepi.  Trail otomatis mengikuti ARAH serangan karena ia mengambil
    posisi nyata ujung bilah tiap frame.
    """

    __slots__ = ("samples", "life", "cap")

    def __init__(self, cap=TRAIL_SAMPLES, life=0.16):
        self.cap = int(cap)
        self.life = float(life)
        self.samples = []          # [Vector2, umur]

    def reset(self):
        self.samples.clear()

    def push(self, tip_x, tip_y, heat=1.0):
        """Tambah sampel CURRENT; heat 0 -> jejak memudar cepat."""
        if heat <= 0.01:
            for s in self.samples:
                s[1] -= self.life * 0.8
            return
        self.samples.append([pygame.Vector2(tip_x, tip_y),
                             self.life * heat])
        while len(self.samples) > self.cap:
            self.samples.pop(0)

    def update(self, dt):
        if not self.samples:
            return
        for s in self.samples:
            s[1] -= dt
        cutoff = 0
        for i, s in enumerate(self.samples):
            if s[1] <= 0.0:
                cutoff = i + 1
            else:
                break
        if cutoff:
            del self.samples[:cutoff]

    @property
    def tip(self):
        return self.samples[-1][0] if self.samples else None

    def draw(self, surface):
        n = len(self.samples)
        if n < 2:
            return
        pts = [s[0] for s in self.samples]
        ages = [s[1] for s in self.samples]
        max_age = self.life
        # ── ribbon utama: polygon antara garis luar & dalam ────────
        # lebar menyusut ke arah sampel lama (bentuk sabit)
        for i in range(n - 1):
            t0 = ages[i] / max_age
            t1 = ages[i + 1] / max_age
            if t1 <= 0.0:
                continue
            a0, a1 = int(200 * t0), int(210 * t1)
            if a0 <= 4 and a1 <= 4:
                continue
            p0, p1 = pts[i], pts[i + 1]
            d = p1 - p0
            ln = d.length()
            if ln < 0.5:
                continue
            nvec = pygame.Vector2(-d.y, d.x) / ln
            w0 = max(1.0, 9.0 * t0)
            w1 = max(1.0, 9.0 * t1)
            quad = [
                (p0.x + nvec.x * w0, p0.y + nvec.y * w0),
                (p1.x + nvec.x * w1, p1.y + nvec.y * w1),
                (p1.x - nvec.x * w1, p1.y - nvec.y * w1),
                (p0.x - nvec.x * w0, p0.y - nvec.y * w0),
            ]
            if glow_allowed():
                pygame.draw.polygon(
                    surface, (*_P["necro_dark"], min(255, (a0 + a1) // 3)),
                    quad)
            pygame.draw.polygon(
                surface, (*_P["necro_mid"], min(255, (a0 + a1) // 2)), quad)
            pygame.draw.polygon(
                surface, (*_P["necro_bright"], min(255, (a0 + a1) // 2)), quad, 1)
        # ── inti terang: garis tebal dari sampel lama ke CURRENT ───
        if glow_allowed():
            core = [(p.x, p.y) for p, a in zip(pts, ages) if a > 0.0]
            if len(core) >= 2:
                pygame.draw.lines(surface, (*_P["necro_light"], 150),
                                  False, core, 2)
                pygame.draw.lines(surface, (*_P["necro_hot"], 200),
                                  False, core, 1)
        # ── percikan pixel di sepanjang tepi (chunky) ──────────────
        for i in range(0, n, 2):
            t = ages[i] / max_age
            if t <= 0.15:
                continue
            p = pts[i]
            pygame.draw.rect(surface, (*_P["necro_bright"],
                                       int(230 * t)),
                             (int(p.x) - 1, int(p.y) - 1, 2, 2))


# ============================================================================
# 6.  IMPACT FX  (hit flash + sparks + shockwave + debris + slash)
# ============================================================================

class ImpactFX:
    """Satu kejadian benturan: flash bintang, shockwave bergerigi,
    serpihan, slash fragment.  Hook hit-stop & shake dipanggil saat
    spawn (lewat combat_feel)."""

    __slots__ = ("x", "y", "kind", "angle", "power", "crit", "t", "dur",
                 "alive")

    def __init__(self, x, y, kind="soul", angle=0.0, power=1.0,
                 crit=False, dur=0.34):
        self.x = float(x)
        self.y = float(y)
        self.kind = str(kind)
        self.angle = float(angle)
        self.power = max(0.4, float(power))
        self.crit = bool(crit)
        self.t = 0.0
        self.dur = float(dur) * (1.25 if crit else 1.0)
        self.alive = True

    def update(self, dt):
        self.t += dt
        if self.t >= self.dur:
            self.alive = False

    def draw(self, surface):
        t01 = self.t / self.dur
        inv = 1.0 - t01
        k = self.power
        if self.kind == "scythe":
            self._draw_slash(surface, t01, inv, k)
        elif self.kind == "skill":
            self._draw_skill(surface, t01, inv, k)
        else:
            self._draw_soul(surface, t01, inv, k)

    # ── benturan sabit: slash arc + debris + shockwave ─────────────
    def _draw_slash(self, surface, t, inv, k):
        c = _P
        ang = self.angle
        # slash arc (dua kurva polygon meruncing, arah serangan)
        if t < 0.55:
            fade = 1.0 - t / 0.55
            span = 1.9
            r0, r1 = 16.0 * k, 40.0 * k
            rot = ang + 0.9 - t * 2.6
            n = 10
            outer, inner = [], []
            for i in range(n + 1):
                a = rot - span / 2 + span * i / n
                rr = r0 + (r1 - r0) * (i / n)
                outer.append((self.x + math.cos(a) * rr,
                              self.y + math.sin(a) * rr * 0.8))
                inner.append((self.x + math.cos(a) * (rr - 9.0 * fade * k),
                              self.y + math.sin(a) * (rr - 9.0 * fade * k) * 0.8))
            poly = outer + inner[::-1]
            pygame.draw.polygon(surface, (*c["necro_mid"],
                                          int(190 * fade)), poly)
            pygame.draw.polygon(surface, (*c["necro_light"],
                                          int(230 * fade)), poly, 2)
        # shockwave bergerigi
        if t < 0.5:
            rr = (12.0 + t * 90.0) * k
            a = int(210 * (1.0 - t / 0.5))
            _blit_faded(surface, ring_surface(int(rr), 3,
                                              c["necro_light"], a, teeth=7),
                        self.x, self.y, a)
        # flash bintang singkat
        if t < 0.18:
            s = (10.0 + 26.0 * k) * (1.0 - t / 0.18)
            spark_star(surface, self.x, self.y, s, c["necro_white"],
                       int(235 * (1.0 - t / 0.18)), spikes=6,
                       rot=ang + 0.4)

    # ── benturan death pulse (soul) ────────────────────────────────
    def _draw_soul(self, surface, t, inv, k):
        c = _P
        # flash bintang jiwa
        if t < 0.22:
            s = (9.0 + 18.0 * k) * inv
            spark_star(surface, self.x, self.y, s, c["necro_white"],
                       int(235 * inv), spikes=5, rot=self.angle)
        # nova bergerigi kecil
        if t < 0.6:
            rr = (8.0 + t * 60.0) * k
            a = int(200 * (1.0 - t / 0.6))
            _blit_faded(surface, ring_surface(int(rr), 2,
                                              c["necro_bright"], a, teeth=5),
                        self.x, self.y, a)
        # tengkorak kilat (khas reaper)
        if t < 0.30 and k >= 0.9:
            sk = skull_decal(int(5 + 3 * inv))
            _blit_faded(surface, sk, self.x, self.y - 2,
                        200 * (1.0 - t / 0.30))

    # ── benturan skill ─────────────────────────────────────────────
    def _draw_skill(self, surface, t, inv, k):
        c = _P
        if t < 0.3:
            s = (14.0 + 30.0 * k) * inv
            spark_star(surface, self.x, self.y, s, c["necro_white"],
                       int(240 * inv), spikes=8, rot=self.angle + 0.2)
        rr = (14.0 + t * 110.0) * k
        a = int(190 * inv)
        _blit_faded(surface, ring_surface(int(rr), 3, c["necro_light"], a,
                                          teeth=9),
                    self.x, self.y, a)


# ============================================================================
# 7.  PROJECTILE SYSTEM  (modular: lifecycle penuh, Vector2, dt-based)
# ============================================================================

class BaseProjectile:
    """Dasar proyektil: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX
    -> DESTROY.  Subclass mengoverride travel()/emit()/draw()."""

    __slots__ = ("pos", "vel", "speed", "damage", "lifetime", "target",
                 "radius", "rotation", "active", "age", "trail",
                 "on_impact", "ground", "hit_pos", "kind", "_total_dist")

    def __init__(self, x, y, tx, ty, speed=ORB_SPEED, damage=0.0,
                 target=None, radius=8.0, lifetime=3.0, on_impact=None,
                 ground=48.0, kind="soul"):
        self.pos = pygame.Vector2(float(x), float(y))
        d = pygame.Vector2(float(tx) - float(x), float(ty) - float(y))
        if d.length_squared() < 1.0:
            d = pygame.Vector2(1.0, 0.0)
        self.vel = d.normalize() * float(speed)
        self.speed = float(speed)
        self.damage = float(damage)
        self.lifetime = float(lifetime)
        self.target = target
        self.radius = float(radius)
        self.rotation = math.atan2(self.vel.y, self.vel.x)
        self.active = True
        self.age = 0.0
        self.trail = []                 # [(Vector2, umur)]
        self.on_impact = on_impact
        self.ground = float(ground)
        self.hit_pos = None
        self.kind = str(kind)
        self._total_dist = self.pos.distance_to(
            pygame.Vector2(float(tx), float(ty)))

    # -- lifecycle -----------------------------------------------------
    def update(self, dt, system=None):
        if not self.active:
            self._decay_trail(dt)
            return
        self.age += dt
        if self.age >= self.lifetime:
            self.destroy(system, impact=False)
            return
        self.travel(dt)
        self.update_trail(dt)
        if system is not None:
            self.emit(dt, system)
        if self.check_collision():
            self.destroy(system, impact=True)

    def travel(self, dt):
        self.pos += self.vel * dt
        self.rotation = math.atan2(self.vel.y, self.vel.x)

    def update_trail(self, dt):
        self.trail.append([pygame.Vector2(self.pos), 0.16])
        if len(self.trail) > 14:
            self.trail.pop(0)
        for s in self.trail:
            s[1] -= dt

    def _decay_trail(self, dt):
        for s in self.trail:
            s[1] -= dt
        self.trail = [s for s in self.trail if s[1] > 0.0]

    def emit(self, dt, system):
        """Partikel pasif di sepanjang jalur (override)."""
        return

    def check_collision(self):
        """Benturan vs target / titik tujuan.  Override bila perlu."""
        if self.target is not None and getattr(self.target, "alive", True):
            tx = float(getattr(self.target, "x", self.pos.x))
            ty = float(getattr(self.target, "y", self.pos.y))
            r = float(getattr(self.target, "radius", 14)) + self.radius
            if (self.pos.x - tx) ** 2 + (self.pos.y - ty) ** 2 <= r * r:
                self.hit_pos = pygame.Vector2(tx, ty - 4)
                return True
        # capai ujung jarak (titik tujuan diam)
        if self.vel.length() > 0.0:
            travelled = self.age * self.speed
            if travelled >= self._total_dist - 4.0:
                self.hit_pos = pygame.Vector2(self.pos)
                return True
        return False

    def destroy(self, system=None, impact=True):
        if not self.active:
            return
        self.active = False
        self.hit_pos = self.hit_pos or pygame.Vector2(self.pos)
        if impact:
            if self.on_impact is not None:
                try:
                    self.on_impact(self)
                except Exception:
                    pass
            elif system is not None:
                system.push_impact(
                    ImpactFX(self.hit_pos.x, self.hit_pos.y,
                             kind="soul", angle=self.rotation,
                             power=0.9))

    def draw(self, surface):
        self._draw_ribbon(surface)
        if self.active:
            self._draw_body(surface)

    def _draw_ribbon(self, surface):
        c = _P
        n = len(self.trail)
        for i in range(n - 1):
            (p0, a0), (p1, a1) = self.trail[i], self.trail[i + 1]
            if a1 <= 0.0:
                continue
            w0 = max(1.0, self.radius * 0.8 * (a0 / 0.16))
            w1 = max(1.0, self.radius * 0.8 * (a1 / 0.16))
            d = p1 - p0
            ln = d.length()
            if ln < 0.3:
                continue
            nv = pygame.Vector2(-d.y, d.x) / ln
            quad = [
                (p0.x + nv.x * w0, p0.y + nv.y * w0),
                (p1.x + nv.x * w1, p1.y + nv.y * w1),
                (p1.x - nv.x * w1, p1.y - nv.y * w1),
                (p0.x - nv.x * w0, p0.y - nv.y * w0),
            ]
            pygame.draw.polygon(
                surface, (*c["necro_dark"], int(140 * a1 / 0.16)), quad)

    def _draw_body(self, surface):
        pygame.draw.circle(surface, (*_P["necro_mid"], 255),
                           (int(self.pos.x), int(self.pos.y)),
                           int(self.radius))


class SoulOrbProjectile(BaseProjectile):
    """Death Pulse orb — inti + glow + bentuk directional (tear) yang
    berotasi mengikuti arah + trail jiwa + partikel."""

    def __init__(self, x, y, tx, ty, speed=ORB_SPEED, damage=0.0,
                 target=None, on_impact=None, ground=48.0):
        super().__init__(x, y, tx, ty, speed=speed, damage=damage,
                         target=target, radius=8.0, lifetime=3.0,
                         on_impact=on_impact, ground=ground, kind="soul")
        self._home = 2.4          # kekuatan homing ringan

    def travel(self, dt):
        # homing ringan ke target (mengikuti kalau target bergeser)
        if self.target is not None and getattr(self.target, "alive", True):
            tx = float(getattr(self.target, "x", self.pos.x))
            ty = float(getattr(self.target, "y", self.pos.y))
            want = pygame.Vector2(tx - self.pos.x, ty - self.pos.y)
            if want.length_squared() > 1.0:
                want = want.normalize() * self.speed
                steer = min(1.0, self._home * dt)
                self.vel = self.vel.lerp(want, steer)
                if self.vel.length_squared() > 1.0:
                    self.vel = self.vel.normalize() * self.speed
        self.pos += self.vel * dt
        self.rotation = math.atan2(self.vel.y, self.vel.x)

    def emit(self, dt, system):
        if random.random() < dt * 42.0 * particle_budget():
            system.particles.spawn(
                self.pos.x + random.uniform(-3, 3),
                self.pos.y + random.uniform(-3, 3),
                random.uniform(-18, 18), random.uniform(-30, -6),
                random.uniform(0.18, 0.4), random.uniform(1.5, 2.8),
                random.choice((_P["necro_light"], _P["necro_bright"])),
                shape="soul", drag=1.2, additive=True)

    def _draw_body(self, surface):
        c = _P
        x, y = int(self.pos.x), int(self.pos.y)
        ang = self.rotation
        # glow besar (additif)
        if glow_allowed():
            _blit_faded(surface, glow_surface(16, c["necro_mid"], 0.8),
                        x, y, 190, additive=True)
        # bentuk directional: tear (kepala lancip ke arah gerak)
        dx, dy = math.cos(ang), math.sin(ang)
        px, py = -dy, dx
        pts = [
            (x + dx * 11, y + dy * 11),
            (x + px * 6, y + py * 6),
            (x - dx * 5, y - dy * 5),
            (x - px * 6, y - py * 6),
        ]
        pygame.draw.polygon(surface, (*c["necro_dark"], 255), pts)
        pygame.draw.polygon(surface, (*c["necro_mid"], 255),
                            [(qx - dx * 1, qy - dy * 1) for qx, qy in pts])
        # inti panas
        pygame.draw.circle(surface, (*c["necro_bright"], 255), (x, y), 4)
        pygame.draw.circle(surface, (*c["necro_hot"], 255), (x - 1, y - 1), 2)
        pygame.draw.circle(surface, (*c["necro_white"], 255), (x - 1, y - 2), 1)
        # percikan orbit
        for i in range(3):
            a = self.age * 9.0 + i * math.tau / 3
            sx = x + int(math.cos(a) * 11)
            sy = y + int(math.sin(a) * 11)
            pygame.draw.rect(surface, (*c["necro_bright"], 230),
                             (sx - 1, sy - 1, 2, 2))


class ReaperScytheProjectile(BaseProjectile):
    """Gelombang sabit (skill E) — siluet bilah berputar + afterimage +
    partikel jiwa; merambat lurus dengan osilasi vertikal ringan."""

    def __init__(self, x, y, tx, ty, speed=SCYTHE_WAVE_SPEED, damage=0.0,
                 target=None, on_impact=None, ground=48.0):
        super().__init__(x, y, tx, ty, speed=speed, damage=damage,
                         target=target, radius=15.0, lifetime=2.2,
                         on_impact=on_impact, ground=ground, kind="scythe")
        self._base_y = float(y)
        self._spin = 0.0
        self._aft = []               # afterimage [(pos, spin, umur)]

    def travel(self, dt):
        self._spin += dt * 14.0
        self.pos += self.vel * dt
        self.pos.y = self._base_y + math.sin(self.age * 7.0) * 5.0
        self.rotation = math.atan2(self.vel.y, self.vel.x)
        # afterimage
        self._aft.append([pygame.Vector2(self.pos), self._spin, 0.14])
        if len(self._aft) > 8:
            self._aft.pop(0)
        for a in self._aft:
            a[2] -= dt
        self._aft = [a for a in self._aft if a[2] > 0.0]

    def emit(self, dt, system):
        if random.random() < dt * 30.0 * particle_budget():
            system.particles.spawn(
                self.pos.x + random.uniform(-8, 8),
                self.pos.y + random.uniform(-10, 10),
                random.uniform(-24, 24), random.uniform(-40, -8),
                random.uniform(0.15, 0.35), random.uniform(1.5, 3.0),
                random.choice((_P["necro_bright"], _P["blade_light"])),
                shape="spark", drag=1.6, additive=True)

    def check_collision(self):
        if self.target is not None and getattr(self.target, "alive", True):
            tx = float(getattr(self.target, "x", self.pos.x))
            ty = float(getattr(self.target, "y", self.pos.y))
            r = float(getattr(self.target, "radius", 14)) + self.radius
            if (self.pos.x - tx) ** 2 + (self.pos.y - ty) ** 2 <= r * r:
                self.hit_pos = pygame.Vector2(tx, ty - 4)
                return True
        travelled = self.age * self.speed
        if travelled >= self._total_dist - 6.0:
            self.hit_pos = pygame.Vector2(self.pos)
            return True
        return False

    def _draw_body(self, surface):
        c = _P
        x, y = int(self.pos.x), int(self.pos.y)
        # afterimage bilah (memudar)
        for apos, aspin, aage in self._aft:
            k = aage / 0.14
            bl = scythe_blade_decal(16)
            rot = pygame.transform.rotate(bl, -math.degrees(aspin))
            _blit_faded(surface, rot, apos.x, apos.y, 90 * k)
        # bilah utama berputar
        bl = scythe_blade_decal(16)
        rot = pygame.transform.rotate(bl, -math.degrees(self._spin))
        if glow_allowed():
            _blit_faded(surface, glow_surface(26, c["necro_mid"], 0.7),
                        x, y, 150, additive=True)
        surface.blit(rot, (x - rot.get_width() // 2, y - rot.get_height() // 2))
        # inti jiwa di pusat
        pygame.draw.circle(surface, (*c["necro_bright"], 255), (x, y), 4)
        pygame.draw.circle(surface, (*c["necro_white"], 255), (x, y), 2)


class ProjectileSystem:
    """Kumpulan proyektil dengan cap + manajemen impact FX."""

    def __init__(self, particles, cap=MAX_PROJECTILES):
        self.particles = particles
        self.cap = int(cap)
        self.projectiles = []
        self.impacts = []

    def _make_room(self):
        while len(self.projectiles) >= self.cap:
            self.projectiles.pop(0)

    def spawn_orb(self, x, y, tx, ty, **kw):
        self._make_room()
        p = SoulOrbProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(p)
        return p

    def spawn_scythe_wave(self, x, y, tx, ty, **kw):
        self._make_room()
        p = ReaperScytheProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(p)
        return p

    def push_impact(self, fx):
        self.impacts.append(fx)
        while len(self.impacts) > MAX_IMPACTS:
            self.impacts.pop(0)

    def on_impact(self, proj):
        """Callback default: impact FX + burst partikel + game feel."""
        hp = proj.hit_pos or proj.pos
        kind = "scythe" if proj.kind == "scythe" else "soul"
        power = 1.25 if proj.kind == "scythe" else 0.95
        self.push_impact(ImpactFX(hp.x, hp.y, kind=kind,
                                  angle=proj.rotation, power=power))
        c = _P
        if kind == "scythe":
            self.particles.burst(
                hp.x, hp.y, 16, speed=(90, 320), life=(0.2, 0.5),
                size=(1.5, 3.5),
                colors=(c["necro_bright"], c["blade_light"], c["necro_hot"]),
                shape="spark", drag=2.2, additive=True)
            self.particles.burst(
                hp.x, hp.y, 7, speed=(50, 150), life=(0.4, 0.8),
                size=(1.5, 2.5), colors=(c["bone_mid"], c["bone_light"]),
                shape="bone", gravity=340.0, drag=0.6, layer="front",
                rotation_speed=(-9.0, 9.0))
            if _feel is not None:
                _feel.hit_stop(0.06)
                if shake_allowed():
                    _feel.shake(7.0, 0.26)
        else:
            self.particles.burst(
                hp.x, hp.y, 12, speed=(60, 240), life=(0.2, 0.45),
                size=(1.5, 3.0),
                colors=(c["necro_light"], c["necro_bright"], c["necro_white"]),
                shape="soul", drag=2.4, additive=True)
            if _feel is not None:
                _feel.hit_stop(0.04)
                if shake_allowed():
                    _feel.shake(4.5, 0.2)

    def update(self, dt):
        for p in self.projectiles:
            p.update(dt, system=self)
        self.projectiles = [p for p in self.projectiles
                            if p.active or p.trail]
        for im in self.impacts:
            im.update(dt)
        self.impacts = [im for im in self.impacts if im.alive]

    def draw(self, surface):
        for p in self.projectiles:
            p.draw(surface)

    def draw_impacts(self, surface):
        for im in self.impacts:
            im.draw(surface)

    def count(self):
        return len(self.projectiles)

    def clear(self):
        self.projectiles.clear()
        self.impacts.clear()


# ============================================================================
# 8.  SKILL FX  — lifecycle CAST -> CHARGE -> RELEASE -> AREA -> IMPACT
#     -> AFTER -> FADE.  Semua q/w/e/r dimajukan setiap frame (anti-
#     kebocoran) dan dibuang setelah selesai.
# ============================================================================

class SkillFX:
    """Satu kejadian skill.  ``t01`` bisa disinkronkan dari timer state
    boss (set_engine_progress) supaya visual dan gameplay seirama."""

    __slots__ = ("skill", "x", "y", "facing", "scale", "t01", "elapsed",
                 "total", "done", "_fired", "target", "_cracks")

    def __init__(self, skill, x, y, facing=1, target=None, scale=1.0,
                 total=None):
        self.skill = str(skill)
        self.x = float(x)
        self.y = float(y)
        self.facing = 1 if facing >= 0 else -1
        self.target = target
        self.scale = float(scale)
        self.t01 = 0.0
        self.elapsed = 0.0
        self.total = float(total if total is not None else
                           SKILL_DUR.get(self.skill, 60) * FIXED_DT * 1.35)
        self.done = False
        self._fired = set()

    def set_engine_progress(self, value):
        """Sinkronkan progres dari timer boss (0..1)."""
        v = max(0.0, min(1.0, float(value)))
        if v >= self.t01:
            self.t01 = v
            self.elapsed = v * self.total

    def follow(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def _once(self, key):
        if key in self._fired:
            return False
        self._fired.add(key)
        return True

    def update(self, dt, particles):
        self.elapsed += dt
        if self.elapsed >= self.total:
            self.done = True
        # jangan biarkan t01 mundur
        nat = min(1.0, self.elapsed / self.total)
        if nat > self.t01:
            self.t01 = nat
        fn = getattr(self, "_upd_" + self.skill, None)
        if fn is not None:
            fn(self.t01, dt, particles)

    # ------------------------------------------------------------------
    # draw ground (di bawah sprite)
    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        fn = getattr(self, "_gnd_" + self.skill, None)
        if fn is not None:
            fn(surface, self.t01)

    # ------------------------------------------------------------------
    # draw front (di atas sprite)
    # ------------------------------------------------------------------
    def draw_front(self, surface):
        fn = getattr(self, "_frn_" + self.skill, None)
        if fn is not None:
            fn(surface, self.t01)

    # ==================================================================
    # Q — DEATH PULSE: nova jiwa bergerigi + tengkorak + retakan tanah
    # ==================================================================
    def _upd_q(self, t, dt, particles):
        c = _P
        ph = skill_phase(t)
        # CAST+CHARGE: jiwa dari sekeliling tersedot masuk
        if ph in ("CAST", "CHARGE"):
            if self._once("q_in"):
                particles.burst(
                    self.x, self.y - 12, 10, speed=(150, 260),
                    life=(0.25, 0.4), size=(1.5, 3.0),
                    colors=(c["necro_light"], c["necro_bright"]),
                    shape="soul", drag=0.0, additive=True)
        # RELEASE: ledakan keluar + shockwave + tengkorak
        if ph == "RELEASE" and self._once("q_burst"):
            particles.burst(
                self.x, self.y - 12, 26, speed=(120, 420),
                life=(0.25, 0.6), size=(1.5, 4.0),
                colors=(c["necro_light"], c["necro_bright"], c["necro_hot"],
                        c["necro_white"]),
                shape="shard", drag=2.6, additive=True,
                rotation_speed=(-8, 8))
            particles.burst(
                self.x, self.y - 12, 10, speed=(40, 120),
                life=(0.5, 0.9), size=(2.0, 3.5),
                colors=(c["bone_mid"], c["bone_light"]),
                shape="bone", gravity=300.0, drag=0.8,
                rotation_speed=(-9, 9))
            if _feel is not None:
                _feel.hit_stop(0.05)
                if shake_allowed():
                    _feel.shake(6.0, 0.24)
        # AREA: bara naik dari tanah
        if ph in ("AREA", "IMPACT") and random.random() < dt * 30.0:
            rr = WORLD_RADIUS["q"] * self.scale * random.uniform(0.2, 0.9)
            ang = random.uniform(0.0, math.tau)
            particles.spawn(
                self.x + math.cos(ang) * rr,
                self.y + 34 * self.scale,
                random.uniform(-8, 8), random.uniform(-70, -30),
                random.uniform(0.4, 0.8), random.uniform(1.5, 3.0),
                random.choice((c["necro_light"], c["necro_mid"])),
                shape="ember", additive=True)

    def _gnd_q(self, surface, t):
        """Tanah: cincin bergerigi melebar + retakan."""
        c = _P
        ph = skill_phase(t)
        r_world = WORLD_RADIUS["q"] * self.scale
        if ph in ("CAST", "CHARGE"):
            # ring menguncup (telegraph)
            k = 1.0 - (t / 0.34)
            rr = int(r_world * (0.35 + 0.65 * k))
            _blit_faded(surface,
                        ellipse_ring_surface(rr, max(3, rr // 3), 2,
                                             c["necro_mid"], 200),
                        self.x, self.y + 34 * self.scale, 200)
            return
        prog = (t - 0.34) / max(0.001, 1.0 - 0.34)
        rr = int(r_world * min(1.0, prog * 1.15))
        a = int(220 * max(0.0, 1.0 - prog))
        _blit_faded(surface,
                    ellipse_ring_surface(rr, max(3, rr // 3), 3,
                                         c["necro_bright"], a),
                    self.x, self.y + 34 * self.scale, a)
        # retakan tanah (garis zigzag dari pusat)
        if self._cracks is not None:
            for (x0, y0, x1, y1) in self._cracks:
                pygame.draw.line(surface, (*c["necro_dark"], a),
                                 (x0, y0), (x1, y1), 2)

    def _frn_q(self, surface, t):
        """Depan: nova bergerigi ganda + tengkorak mengorbit."""
        c = _P
        ph = skill_phase(t)
        if ph in ("CAST", "CHARGE"):
            k = t / 0.34
            rr = 30.0 * (1.0 - k) + 6.0
            _blit_faded(surface,
                        ring_surface(int(rr), 2, c["necro_light"], 220,
                                     teeth=6),
                        self.x, self.y - 12, 220)
            return
        prog = min(1.0, (t - 0.34) / 0.5)
        if prog >= 1.0:
            return
        fade = 1.0 - prog
        # dua gelombang nova bergerigi (offset)
        for wave in (0.0, 0.12):
            wp = min(1.0, max(0.0, prog - wave))
            if wp <= 0.0:
                continue
            rr = 14.0 + wp * (WORLD_RADIUS["q"] * self.scale)
            a = int(235 * (1.0 - wp))
            _blit_faded(surface,
                        ring_surface(int(rr), 3, c["necro_light"], a,
                                     teeth=10),
                        self.x, self.y - 10, a)
            _blit_faded(surface,
                        ring_surface(int(rr * 0.55), 2, c["necro_bright"],
                                     a, teeth=6),
                        self.x, self.y - 10, a)
        # tengkorak terlempar mengorbit keluar
        if prog < 0.5:
            for i in range(4):
                ang = self.elapsed * 3.0 + i * math.tau / 4
                rr = 20.0 + prog * 90.0 * self.scale
                sx = self.x + math.cos(ang) * rr
                sy = self.y - 10 + math.sin(ang) * rr * 0.7
                _blit_faded(surface, skull_decal(5),
                            sx, sy, int(220 * (1.0 - prog * 2.0)))
        # kilatan pusat
        if prog < 0.2:
            spark_star(surface, self.x, self.y - 12,
                       (16 + 30 * (1.0 - prog / 0.2)) * self.scale,
                       c["necro_white"], int(240 * (1.0 - prog / 0.2)),
                       spikes=8)

    # ==================================================================
    # W — HEARTSTOPPER AURA: sigil heks, tengkorak orbit, aliran hisap
    # ==================================================================
    def _upd_w(self, t, dt, particles):
        c = _P
        ph = skill_phase(t)
        # sepanjang hidup: jiwa tersedot ke Vhalzun (leech stream)
        if ph in ("CHARGE", "RELEASE", "AREA"):
            if random.random() < dt * 26.0:
                rr = WORLD_RADIUS["w"] * self.scale * random.uniform(0.7, 1.0)
                ang = random.uniform(0.0, math.tau)
                particles.spawn(
                    self.x + math.cos(ang) * rr,
                    self.y - 8 + math.sin(ang) * rr * 0.5,
                    0.0, 0.0, random.uniform(0.5, 0.9),
                    random.uniform(1.5, 3.0),
                    random.choice((c["necro_light"], c["necro_bright"])),
                    shape="soul", drag=0.0, additive=True,
                    ax=-math.cos(ang) * 150.0,
                    ay=-math.sin(ang) * 90.0)
        if ph == "RELEASE" and self._once("w_pulse"):
            particles.burst(
                self.x, self.y - 12, 14, speed=(70, 200),
                life=(0.2, 0.45), size=(1.5, 3.0),
                colors=(c["necro_bright"], c["necro_hot"]),
                shape="spark", drag=2.0, additive=True)
            if _feel is not None and shake_allowed():
                _feel.shake(3.5, 0.18)

    def _gnd_w(self, surface, t):
        """Tanah: sigil heksagonal berputar (bukan lingkaran)."""
        c = _P
        a0 = int(120 + 60 * math.sin(self.elapsed * 5.0))
        r = int(WORLD_RADIUS["w"] * self.scale)
        gy = self.y + 34 * self.scale
        # sigil: 2 heksagon saling silang
        for rot in (self.elapsed * 0.8, -self.elapsed * 0.6 + math.pi / 6):
            pts = [(self.x + math.cos(rot + i * math.tau / 6) * r,
                    gy + math.sin(rot + i * math.tau / 6) * (r // 2.4))
                   for i in range(6)]
            pygame.draw.polygon(surface, (*c["necro_dark"], a0), pts, 2)
            pygame.draw.polygon(surface, (*c["necro_mid"], a0 // 2), pts, 1)
        # sambungan sudut-ke-sudut (web)
        pts2 = [(self.x + math.cos(-self.elapsed * 0.6 + i * math.tau / 6) * r,
                 gy + math.sin(-self.elapsed * 0.6 + i * math.tau / 6) * (r // 2.4))
                for i in range(6)]
        for i in range(6):
            pygame.draw.line(surface, (*c["necro_bright"], a0 // 2),
                             pts2[i], pts2[(i + 2) % 6], 1)

    def _frn_w(self, surface, t):
        """Depan: tengkorak orbit + jantung nekrotik terkoyak."""
        c = _P
        ph = skill_phase(t)
        fade = 1.0 if ph != "AFTER" else max(0.0, 1.0 - (t - 0.86) / 0.14)
        # 6 tengkorak mengorbit dengan bob
        for i in range(6):
            ang = self.elapsed * 1.6 + i * math.tau / 6
            rx = 58.0 * self.scale
            ry = 22.0 * self.scale
            sx = self.x + math.cos(ang) * rx
            sy = self.y + 4 + math.sin(ang) * ry + \
                math.sin(self.elapsed * 3.0 + i) * 3
            _blit_faded(surface, skull_decal(5), sx, sy,
                        int(235 * fade))
        # jantung nekrotik naik (jiwa yang dihentikan)
        for i in range(3):
            tt = ((self.elapsed * 0.8 + i * 0.33) % 1.0)
            hx = self.x + (i - 1) * 22 * self.scale
            hy = self.y - 26 - tt * 34.0
            a = int(200 * (1.0 - tt) * fade)
            if a <= 4:
                continue
            # bentuk jantung chunky (2 kotak + poligon)
            pygame.draw.rect(surface, (*c["necro_light"], a),
                             (hx - 3, hy, 3, 3))
            pygame.draw.rect(surface, (*c["necro_light"], a),
                             (hx, hy, 3, 3))
            pygame.draw.polygon(surface, (*c["necro_bright"], a),
                                [(hx - 3, hy + 3), (hx + 3, hy + 3), (hx, hy + 6)])

    # ==================================================================
    # E — REAPER'S SCYTHE: spin-up -> lempar gelombang sabit besar
    # ==================================================================
    def _upd_e(self, t, dt, particles):
        c = _P
        ph = skill_phase(t)
        if ph in ("CAST", "CHARGE"):
            # percikan terkumpul di bilah
            if random.random() < dt * 40.0:
                ang = random.uniform(0.0, math.tau)
                rr = random.uniform(24.0, 44.0)
                particles.spawn(
                    self.x + math.cos(ang) * rr,
                    self.y - 18 + math.sin(ang) * rr,
                    -math.cos(ang) * 120.0, -math.sin(ang) * 120.0,
                    random.uniform(0.15, 0.3), random.uniform(1.5, 2.5),
                    random.choice((c["necro_bright"], c["blade_shine"])),
                    shape="spark", drag=0.0, additive=True)
        if ph == "RELEASE" and self._once("e_throw"):
            if _feel is not None:
                _feel.hit_stop(0.045)
                if shake_allowed():
                    _feel.shake(5.0, 0.22)

    def _gnd_e(self, surface, t):
        """Tanah: koridor sapuan (telegraph arah lempar)."""
        c = _P
        ph = skill_phase(t)
        if ph in ("CAST", "CHARGE"):
            k = t / 0.34
            ln = int(70 + 120 * k)
            w = int(16 + 10 * k)
            f = self.facing
            x0 = self.x + 20 * f * self.scale
            y0 = self.y - 16 * self.scale
            x1 = x0 + ln * f
            a = int(150 * k + 60)
            taper_lane(surface, x0, y0, x1, y0, w, w // 2,
                       c["necro_dark"], a)
            pygame.draw.line(surface, (*c["necro_bright"], a),
                             (x0, y0), (x1, y0), 1)

    def _frn_e(self, surface, t):
        """Depan: kilat bilah saat spin (bilah sungguhan ada di rig)."""
        c = _P
        ph = skill_phase(t)
        if ph in ("CAST", "CHARGE"):
            # lingkar spin blur di sekitar badan
            rr = 40.0 * self.scale
            a = int(120 + 80 * math.sin(self.elapsed * 18.0))
            for i in range(3):
                ang = self.elapsed * 16.0 + i * math.tau / 3
                px = self.x + math.cos(ang) * rr
                py = self.y - 18 + math.sin(ang) * rr * 0.6
                shard_poly(surface, px, py, ang, 10.0 * self.scale,
                           3.0, c["necro_bright"], a)
        if ph == "RELEASE" and t < 0.46:
            prog = (t - 0.34) / 0.12
            f = self.facing
            x0 = self.x + 20 * f
            y0 = self.y - 16
            ln = 200.0 * self.scale * prog
            taper_lane(surface, x0, y0, x0 + ln * f, y0, 10, 2,
                       c["necro_light"], int(190 * (1.0 - prog)))

    # ==================================================================
    # R — GHOST SHROUD: wraith naik + cangkang spektral + vakum jiwa
    # ==================================================================
    def _upd_r(self, t, dt, particles):
        c = _P
        ph = skill_phase(t)
        if ph == "RELEASE" and self._once("r_burst"):
            particles.burst(
                self.x, self.y - 14, 22, speed=(80, 300),
                life=(0.3, 0.7), size=(1.5, 3.5),
                colors=(c["necro_bright"], c["necro_white"], c["purple_mid"]),
                shape="soul", drag=1.8, additive=True)
            if _feel is not None:
                _feel.hit_stop(0.06)
                if shake_allowed():
                    _feel.shake(8.0, 0.3)
        # wraith terus naik selama AREA
        if ph in ("RELEASE", "AREA", "IMPACT"):
            if random.random() < dt * 16.0:
                ang = random.uniform(0.0, math.tau)
                rr = WORLD_RADIUS["r"] * self.scale * random.uniform(0.4, 1.0)
                particles.spawn(
                    self.x + math.cos(ang) * rr,
                    self.y + 30 * self.scale,
                    random.uniform(-6, 6), random.uniform(-90, -50),
                    random.uniform(0.6, 1.1), random.uniform(2.0, 3.5),
                    random.choice((c["necro_light"], c["necro_bright"])),
                    shape="soul", additive=True)
        # motes penyembuhan (hijau lembut naik)
        if ph in ("AREA", "AFTER") and random.random() < dt * 12.0:
            particles.spawn(
                self.x + random.uniform(-26, 26) * self.scale,
                self.y + 20 * self.scale,
                random.uniform(-4, 4), random.uniform(-50, -26),
                random.uniform(0.5, 0.9), random.uniform(1.5, 2.5),
                c["necro_hot"], shape="ember", additive=True)

    def _gnd_r(self, surface, t):
        """Tanah: lingkar kubur + rune naik."""
        c = _P
        ph = skill_phase(t)
        r = int(WORLD_RADIUS["r"] * self.scale)
        gy = self.y + 34 * self.scale
        if ph in ("CAST", "CHARGE"):
            k = t / 0.34
            rr = int(r * (0.3 + 0.7 * k))
            _blit_faded(surface,
                        ellipse_ring_surface(rr, max(3, rr // 3), 2,
                                             c["necro_mid"], 190),
                        self.x, gy, 190)
        else:
            fade = 1.0 if ph != "AFTER" else max(0.0, 1.0 - (t - 0.86) / 0.14)
            a = int(190 * fade)
            _blit_faded(surface,
                        ellipse_ring_surface(r, max(3, r // 3), 3,
                                             c["necro_bright"], a),
                        self.x, gy, a)
            # rune tick naik-turun di sepanjang lingkar
            for i in range(8):
                ang = self.elapsed * 1.2 + i * math.tau / 8
                px = self.x + math.cos(ang) * r
                py = gy + math.sin(ang) * (r // 2.6)
                h = 3 + int(3 * math.sin(self.elapsed * 6.0 + i))
                pygame.draw.line(surface, (*c["necro_hot"], a),
                                 (px, py - h), (px, py + h), 1)

    def _frn_r(self, surface, t):
        """Depan: wraith siluet mengelilingi + cangkang facet spektral."""
        c = _P
        ph = skill_phase(t)
        fade = 1.0 if ph != "AFTER" else max(0.0, 1.0 - (t - 0.86) / 0.14)
        if fade <= 0.02:
            return
        # wraith (siluet hantu) mengorbit + naik
        for i in range(5):
            ang = self.elapsed * 0.9 + i * math.tau / 5
            rx = 52.0 * self.scale
            rise = ((self.elapsed * 0.6 + i * 0.2) % 1.0) * 26.0
            wx = self.x + math.cos(ang) * rx
            wy = self.y + 26 - rise + math.sin(self.elapsed * 2.0 + i) * 3
            wr = wraith_sprite(9)
            _blit_faded(surface, wr, wx, wy, int(200 * fade))
        # cangkang spektral: poligon facet di sekeliling badan
        if ph in ("CHARGE", "RELEASE", "AREA"):
            pulse = 0.75 + 0.25 * math.sin(self.elapsed * 6.0)
            rr = 46.0 * self.scale * pulse
            n = 8
            pts = []
            for i in range(n):
                ang = i * math.tau / n - self.elapsed * 0.7
                pts.append((self.x + math.cos(ang) * rr,
                            self.y - 12 + math.sin(ang) * rr * 1.15))
            pygame.draw.polygon(surface, (*c["necro_light"],
                                          int(52 * fade)), pts, 2)
            pygame.draw.polygon(surface, (*c["necro_bright"],
                                          int(90 * fade)), pts, 1)


# atribut late untuk retakan tanah Q (di-generate sekali per FX)
def _skillfx_postinit(fx):
    """Buat retakan tanah deterministik untuk skill Q (sekali)."""
    if fx.skill == "q":
        rng = random.Random(int(fx.x * 7 + fx.y * 13))
        cracks = []
        for i in range(6):
            ang = i * math.tau / 6 + rng.uniform(-0.2, 0.2)
            x0 = fx.x
            y0 = fx.y + 34 * fx.scale
            x1 = x0 + math.cos(ang) * 30
            y1 = y0 + math.sin(ang) * 12
            x2 = x1 + math.cos(ang + rng.uniform(-0.5, 0.5)) * 26
            y2 = y1 + math.sin(ang + rng.uniform(-0.5, 0.5)) * 10
            cracks.append((x0, y0, x1, y1))
            cracks.append((x1, y1, x2, y2))
        fx._cracks = cracks
    else:
        fx._cracks = None


# ============================================================================
# 9.  DIRECTOR — mengikat semua sistem untuk SATU unit Vhalzun
# ============================================================================

class VhalzunFXDirector:
    """Mengikat trail, partikel, proyektil, skill, dampak, dan game feel
    untuk satu Vhalzun (boss lane maupun hero lane)."""

    def __init__(self, unit=None):
        self.unit = unit
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.projectiles = ProjectileSystem(self.particles, MAX_PROJECTILES)
        self.trail = SwingTrail(TRAIL_SAMPLES)
        self.skills = []
        self.impacts = []
        self.afterimages = []

        # posisi layar terakhir
        self.x = 0.0
        self.y = 0.0
        self.have_pos = False
        self.draw_age = 99.0

        # pelacakan state animasi
        self.state = "IDLE"
        self.state_prev = "IDLE"
        self.state_time = 0.0
        self.anim_frame = 0

        # pelacakan serangan
        self.attack_progress = 0.0
        self.attack_prev = -1.0
        self.attack_kind = "pulse"
        self.swing_done = False
        self.shot_done = False
        self._pending_impact = None

        # pelacakan skill
        self.skill_key = None
        self.skill_prev = None
        self._skill_total = 1
        self._scythe_wave_done = False

        # lain-lain
        self.hurt_prev = 0
        self.ember_acc = 0.0
        self.time = 0.0
        self.dt = FIXED_DT
        self._fps_acc = 0.0
        self._fps_n = 0
        self.fps = 60.0
        self._was_alive = True

    # ==================================================================
    # SYNC — dipanggil tiap frame gambar (posisi layar diketahui)
    # ==================================================================
    def sync(self, boss, x, y):
        self.unit = boss
        self.x = float(x)
        self.y = float(y)
        self.have_pos = True
        self.draw_age = 0.0
        _sync_palette()

        # -- state animasi dari renderer --------------------------------
        st = getattr(boss, "_vhz_state", None)
        if st is None:
            action, _phase, _ap = pose_of(boss)
            st = {"idle": "IDLE", "walk": "WALK", "attack": "ATTACK",
                  "swing": "SWING", "cast_q": "SKILL", "cast_w": "SKILL",
                  "cast_e": "SPECIAL", "cast_r": "SPECIAL",
                  "hurt": "HURT", "death": "DEATH"}.get(action, "IDLE")
        if st != self.state:
            self.state_prev = self.state
            self.state = st
            self.state_time = 0.0
            self.anim_frame = 0

        # -- serangan ----------------------------------------------------
        self.attack_kind = getattr(boss, "_vhz_attack_kind",
                                   self.attack_kind) or "pulse"
        ap = float(getattr(boss, "_vhz_attack_progress", 0.0) or 0.0)
        active = bool(getattr(boss, "_vhz_attack_active", False))
        if not active:
            self.attack_progress = 0.0
            self.attack_prev = -1.0
        else:
            # reset flag saat cycle baru (progress mundur drastis)
            if self.attack_prev >= 0.0 and ap < self.attack_prev - 0.5:
                self.swing_done = False
                self.shot_done = False
                self._pending_impact = None
            self.attack_progress = ap
        self.attack_prev = self.attack_progress if active else -1.0

        # -- skill --------------------------------------------------------
        skill = getattr(boss, "_vhz_skill", None)
        timer = int(getattr(boss, "active_skill_timer", 0) or 0) \
            if skill is not None else 0
        if skill is not None and skill != self.skill_prev:
            if not any(fx.skill == skill for fx in self.skills):
                self.on_cast(self.x, self.y, skill)
        if skill is not None:
            self._skill_total = max(self._skill_total, timer, 1)
            for fx in self.skills:
                if fx.skill == skill:
                    fx.set_engine_progress(
                        1.0 - timer / float(max(1, self._skill_total)))
        if skill != self.skill_key:
            self.skill_key = skill
            self._skill_total = max(1, timer) if skill is not None else 1
        self.skill_prev = skill

    # ==================================================================
    # UPDATE — dimajukan lewat tick() (dt dari bus game-feel)
    # ==================================================================
    def update(self, dt):
        self.time += dt
        self.state_time += dt
        self.anim_frame += 1
        self.draw_age += dt

        # FPS meter
        self._fps_acc += dt
        self._fps_n += 1
        if self._fps_acc >= 0.5:
            self.fps = self._fps_n / max(0.0001, self._fps_acc)
            self._fps_acc = 0.0
            self._fps_n = 0

        u = self.unit
        x, y = self.x, self.y

        # ── HURT: edge naik dari hurt_flash_timer ────────────────────
        if u is not None:
            hurt = int(getattr(u, "hurt_flash_timer", 0) or 0)
            if hurt >= 5 and hurt > self.hurt_prev:
                self.on_hurt(x, y)
            self.hurt_prev = hurt

            # ── DEATH: ledakan jiwa sekali ────────────────────────────
            alive = bool(getattr(u, "alive", True))
            if self._was_alive and not alive:
                self.on_death(x, y)
            self._was_alive = alive

        # ── SERANGAN: event per fase ──────────────────────────────────
        # Baca state TERBARU langsung dari unit (bukan salinan sync) —
        # hook gameplay (notify_*) bisa jalan sebelum frame gambar
        # pertama, jadi tick() harus tetap melihat progress baru.
        if u is not None:
            kind_now = getattr(u, "_vhz_attack_kind", None)
            if kind_now:
                self.attack_kind = kind_now
            if getattr(u, "_vhz_attack_active", False):
                self.attack_progress = max(0.0, min(1.0, float(
                    getattr(u, "_vhz_attack_progress", 0.0) or 0.0)))
        active = u is not None and bool(getattr(u, "_vhz_attack_active",
                                                False))
        if not active and self._pending_impact is not None:
            # serangan berakhir sebelum frame benturan (interupsi) ->
            # lepas impact yang tertahan agar tidak menggantung selamanya
            self._release_pending()
        if active:
            ap = self.attack_progress
            kind = self.attack_kind
            tp = self._target_point()

            # spawn proyektil pada frame rilis (HANYA jalur boss;
            # jalur hero memakai proyektil generik gameplay)
            if kind == "pulse" and not self.shot_done \
                    and ap >= ATK_RELEASE:
                self.shot_done = True
                if getattr(u, "_render_scale", None) is None:
                    self._spawn_attack_orb(tp)
            # impact swing pada frame benturan bilah
            if kind == "swing" and not self.swing_done \
                    and ap >= ATK_IMPACT:
                self.swing_done = True
                self._on_swing_impact_frame(x, y, tp)

            # trail: sampel ujung bilah selama jendela cepat
            _pivot, tip = scythe_points(u, x, y)
            fast = 0.24 <= ap <= 0.62 and kind == "swing"
            self.trail.push(tip.x, tip.y, 1.0 if fast else
                            (0.6 if kind == "attack" else 0.0))
        else:
            self.trail.push(0, 0, 0.0)

        # ── AFTERIMAGE sabit saat spin skill E ───────────────────────
        if u is not None:
            action, _ph, ap = pose_of(u)
            if action == "cast_e" and ap < 0.55:
                self.push_afterimage()
            # skill E: lepaskan gelombang sabit pada fase RELEASE
            # (ambang 0.42 sama dengan fallback canvas renderer).
            if action == "cast_e" and ap >= 0.42 \
                    and not self._scythe_wave_done:
                self._scythe_wave_done = True
                if getattr(u, "_render_scale", None) is None:
                    self._spawn_scythe_wave()
            elif action != "cast_e":
                self._scythe_wave_done = False

        # ── AMBIENT: bara jiwa & mist (rate-limited) ──────────────────
        self._ambient(dt)

        # ── sistem ────────────────────────────────────────────────────
        self.trail.update(dt)
        self.projectiles.update(dt)
        self.particles.update(dt)
        for im in self.impacts:
            im.update(dt)
        self.impacts = [im for im in self.impacts if im.alive]
        for ai in self.afterimages:
            ai["life"] -= dt
        self.afterimages = [ai for ai in self.afterimages
                            if ai["life"] > 0.0]
        for fx in self.skills:
            fx.update(dt, self.particles)
        self.skills = [fx for fx in self.skills if not fx.done]

    # ------------------------------------------------------------------
    # event helpers
    # ------------------------------------------------------------------
    def _target_point(self):
        u = self.unit
        tgt = getattr(u, "target", None) if u is not None else None
        if tgt is not None and getattr(tgt, "alive", True):
            return (float(getattr(tgt, "x", self.x)),
                    float(getattr(tgt, "y", self.y)) - 6.0, tgt)
        return None

    def _spawn_attack_orb(self, tp):
        u = self.unit
        _pivot, tip = scythe_points(u, self.x, self.y)
        if tp is None:
            f = 1 if (getattr(u, "direction", 1) or 1) >= 0 else -1
            aim = (self.x + f * 140.0, self.y - 10.0)
            tgt = None
        else:
            aim, tgt = (tp[0], tp[1]), tp[2]
        self.projectiles.spawn_orb(
            tip.x, tip.y, aim[0], aim[1], speed=ORB_SPEED, damage=0.0,
            target=tgt, ground=ground_dy(u),
            on_impact=lambda b: self._on_orb_hit(b))
        self.particles.burst(
            tip.x, tip.y, 7, speed=(90, 220), life=(0.12, 0.3),
            size=(1.5, 3.0),
            colors=(_P["necro_bright"], _P["necro_white"]),
            spread=1.9, drag=3.0, shape="spark", additive=True)

    def _on_orb_hit(self, bolt):
        hp = bolt.hit_pos
        self.projectiles.push_impact(
            ImpactFX(hp.x, hp.y, kind="soul", angle=bolt.rotation,
                     power=0.95))
        self.particles.burst(
            hp.x, hp.y, 12, speed=(60, 240), life=(0.2, 0.45),
            size=(1.5, 3.0),
            colors=(_P["necro_light"], _P["necro_bright"], _P["necro_white"]),
            shape="soul", drag=2.4, additive=True)
        if _feel is not None:
            _feel.hit_stop(0.04)
            if shake_allowed():
                _feel.shake(4.5, 0.2)

    def _spawn_scythe_wave(self):
        """Skill E: gelombang sabit besar melesat ke target."""
        u = self.unit
        _pivot, tip = scythe_points(u, self.x, self.y)
        tp = self._target_point()
        if tp is None:
            f = 1 if (getattr(u, "direction", 1) or 1) >= 0 else -1
            aim, tgt = (self.x + f * 240.0, self.y - 10.0), None
        else:
            aim, tgt = (tp[0], tp[1]), tp[2]
        self.projectiles.spawn_scythe_wave(
            tip.x, tip.y, aim[0], aim[1], speed=SCYTHE_WAVE_SPEED,
            damage=0.0, target=tgt, ground=ground_dy(u),
            on_impact=lambda b: self._on_orb_hit(b))
        self.particles.burst(
            tip.x, tip.y, 10, speed=(80, 240), life=(0.15, 0.35),
            size=(1.5, 3.0),
            colors=(_P["blade_shine"], _P["necro_bright"], _P["necro_white"]),
            shape="spark", drag=2.6, additive=True)
        if _feel is not None and shake_allowed():
            _feel.shake(4.0, 0.18)

    def _on_swing_impact_frame(self, x, y, tp):
        """Frame bilah menyentuh: full impact kalau target di dalam busur."""
        u = self.unit
        _pivot, tip = scythe_points(u, x, y)
        f = 1 if (getattr(u, "direction", 1) or 1) >= 0 else -1
        if tp is not None:
            tx, ty = tp[0], tp[1]
            dist = math.hypot(tx - x, ty - y)
            front = (tx - x) * f
            if dist <= MELEE_REACH + 20.0 and front > -18.0:
                self.on_impact(tx, ty,
                               math.atan2(ty - (y - 10), tx - x),
                               1.2, False, kind="scythe")
        # percikan tanah walau meleset (feel sapuan)
        self.particles.burst(
            tip.x, tip.y + 20, 5, speed=(30, 110), life=(0.15, 0.35),
            size=(1.0, 2.2), colors=(_P["necro_dark"], _P["necro_mid"]),
            shape="dust", drag=2.0, layer="back")
        self._release_pending()

    def _release_pending(self):
        if self._pending_impact is not None:
            tx, ty, ang, power, crit, kind = self._pending_impact
            self.on_impact(tx, ty, ang, power, crit, kind=kind)
            self._pending_impact = None

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="soul"):
        """Impact penuh + partikel + game feel."""
        self.impacts.append(ImpactFX(x, y, kind=kind, angle=angle,
                                     power=power, crit=crit))
        while len(self.impacts) > MAX_IMPACTS:
            self.impacts.pop(0)
        c = _P
        if kind == "scythe":
            self.particles.burst(
                x, y, 15, speed=(100, 340), life=(0.18, 0.45),
                size=(1.5, 3.5),
                colors=(c["necro_bright"], c["blade_shine"], c["necro_hot"]),
                shape="spark", drag=2.4, additive=True)
            self.particles.burst(
                x, y, 6, speed=(50, 160), life=(0.35, 0.7),
                size=(1.5, 2.5), colors=(c["bone_mid"], c["bone_light"]),
                shape="bone", gravity=320.0, drag=0.7,
                rotation_speed=(-9, 9))
            if _feel is not None:
                _feel.hit_stop(0.055)
                if shake_allowed():
                    _feel.shake(6.5, 0.24)
        else:
            self.particles.burst(
                x, y, 11, speed=(60, 240), life=(0.18, 0.4),
                size=(1.5, 3.0),
                colors=(c["necro_light"], c["necro_bright"]),
                shape="soul", drag=2.6, additive=True)
            if _feel is not None:
                _feel.hit_stop(0.038)
                if shake_allowed():
                    _feel.shake(4.0, 0.18)

    def on_hurt(self, x, y):
        """Kena pukul: serpihan jiwa + recoil kecil."""
        self.particles.burst(
            x, y - 16, 9, speed=(50, 190), life=(0.15, 0.35),
            size=(1.5, 3.0),
            colors=(_P["necro_light"], _P["robe_light"]),
            shape="soul", drag=2.2, additive=True)

    def on_death(self, x, y):
        """Mati: jiwa meledak keluar + wraith naik (FX global via bus)."""
        c = _P
        self.particles.burst(
            x, y - 16, 30, speed=(60, 320), life=(0.4, 0.9),
            size=(1.5, 4.0),
            colors=(c["necro_light"], c["necro_bright"], c["bone_light"],
                    c["necro_white"]),
            shape="soul", drag=1.4, additive=True)
        self.particles.burst(
            x, y - 16, 8, speed=(40, 130), life=(0.6, 1.1),
            size=(2.0, 3.5), colors=(c["bone_mid"], c["bone_light"]),
            shape="bone", gravity=260.0, drag=0.5,
            rotation_speed=(-9, 9))
        if _feel is not None:
            _feel.hit_stop(0.08)
            if shake_allowed():
                _feel.shake(10.0, 0.34)

    def on_cast(self, x, y, skill):
        fx = SkillFX(skill, x, y,
                     facing=(getattr(self.unit, "direction", 1) or 1),
                     target=getattr(self.unit, "target", None),
                     scale=body_scale(self.unit))
        _skillfx_postinit(fx)
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        self.skills.append(fx)
        return fx

    def push_afterimage(self):
        u = self.unit
        _pivot, tip = scythe_points(u, self.x, self.y)
        self.afterimages.append({"x": tip.x, "y": tip.y, "life": 0.16,
                                 "max": 0.16})
        while len(self.afterimages) > MAX_AFTERIMAGES:
            self.afterimages.pop(0)

    def _ambient(self, dt):
        """Bara jiwa pelan di sekitar badan (rate-limited + budget)."""
        if not self.have_pos or particle_budget() <= 0.0:
            return
        self.ember_acc += dt * 9.0
        while self.ember_acc >= 1.0:
            self.ember_acc -= 1.0
            self.particles.spawn(
                self.x + random.uniform(-20, 20),
                self.y + random.uniform(6, 34),
                random.uniform(-4, 4), random.uniform(-26, -10),
                random.uniform(0.5, 1.0), random.uniform(1.5, 2.5),
                random.choice((_P["necro_mid"], _P["necro_dark"])),
                shape="ember", layer="back", additive=True)

    # ------------------------------------------------------------------
    # draw layers
    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        for fx in self.skills:
            fx.follow(self.x, self.y)
            fx.draw_ground(surface)
        self.particles.draw(surface, "back")

    def draw_front(self, surface):
        # afterimage sabit (di bawah trail utama)
        for ai in self.afterimages:
            k = ai["life"] / ai["max"]
            bl = scythe_blade_decal(13)
            _blit_faded(surface, bl, ai["x"], ai["y"], 110 * k)
        # trail sabetan
        self.trail.draw(surface)
        # proyektil + impact
        self.projectiles.draw(surface)
        self.projectiles.draw_impacts(surface)
        for im in self.impacts:
            im.draw(surface)
        # partikel depan
        self.particles.draw(surface, "front")
        # skill front (di atas partikel supaya terbaca)
        for fx in self.skills:
            fx.draw_front(surface)

    # ------------------------------------------------------------------
    def stats(self):
        return {
            "state": self.state,
            "state_prev": self.state_prev,
            "state_time": round(self.state_time, 3),
            "anim_frame": self.anim_frame,
            "attack_kind": self.attack_kind,
            "attack_progress": round(self.attack_progress, 3),
            "attack_phase": attack_phase(self.attack_progress)
            if self.attack_progress > 0.0 else "-",
            "skill": self.skill_key,
            "particles": self.particles.count(),
            "projectiles": self.projectiles.count(),
            "skills": len(self.skills),
            "impacts": len(self.impacts),
            "afterimages": len(self.afterimages),
            "fps": round(self.fps, 1),
        }

    def reset(self):
        self.particles.clear()
        self.projectiles.clear()
        self.trail.reset()
        self.skills.clear()
        self.impacts.clear()
        self.afterimages.clear()
        self.swing_done = False
        self.shot_done = False
        self.skill_key = None
        self._pending_impact = None
        self.have_pos = False


# ============================================================================
# 10. REGISTRI DIRECTOR  (pola identik heroes/krobellus_fx.py)
# ============================================================================

_DIRECTORS = []
MAX_DIRECTORS = 12


def director_for(unit):
    """Ambil (atau buat) director FX untuk satu unit Vhalzun."""
    _sync_palette()
    d = getattr(unit, "_vhalzun_fx", None)
    if d is None:
        d = VhalzunFXDirector(unit)
        try:
            unit._vhalzun_fx = d
        except Exception:                        # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > MAX_DIRECTORS:
            _release(_DIRECTORS.pop(0))
    return d


def _release(director):
    try:
        if director.unit is not None:
            director.unit._vhalzun_fx = None
            director.unit._vhz_live_fx = False
    except Exception:                            # pragma: no cover
        pass
    director.reset()


def attach(unit):
    """Pasang lapisan hidup pada unit (dipanggil pipeline render)."""
    if not VHALZUN_FX_ENABLED or unit is None:
        return False
    try:
        director_for(unit)
    except Exception:                            # pragma: no cover
        return False
    try:
        unit._vhz_live_fx = True
    except Exception:                            # pragma: no cover
        return False
    return True


def owns(unit):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not VHALZUN_FX_ENABLED or unit is None:
        return False
    if not getattr(unit, "_vhz_live_fx", False):
        return False
    d = getattr(unit, "_vhalzun_fx", None)
    return d is not None and d in _DIRECTORS


def recently_drawn(unit, max_age=0.35):
    """True kalau lapisan hidup unit ini BENAR-BENAR digambar belakangan."""
    d = getattr(unit, "_vhalzun_fx", None)
    if d is None:
        return False
    return bool(d.have_pos) and d.draw_age <= float(max_age)


def tick(dt=None):
    """Majukan waktu FX satu frame nyata; aman dipanggil berkali-kali."""
    if not VHALZUN_FX_ENABLED:
        return 0.0
    if dt is not None:
        step = max(0.0, min(1.0 / 20.0, float(dt)))
        _advance(step)
        return step
    if _feel is not None:
        try:
            step = float(_feel.fx_dt())
        except Exception:                        # pragma: no cover
            step = 0.0
    else:                                        # pragma: no cover
        step = FIXED_DT
    _advance(step)
    return step


def _advance(step):
    if step <= 0.0 or not _DIRECTORS:
        return
    step = max(0.0, min(1.0 / 20.0, step))
    for d in _DIRECTORS:
        d.update(step)


def reset_all():
    """Bersihkan seluruh state FX Vhalzun (ganti level / keluar match)."""
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()
    clear_cache()


def total_particles():
    """Jumlah partikel Vhalzun yang hidup (HUD performa + tes)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def stats():
    """Ringkasan global untuk overlay debug / profiling."""
    out = {"directors": len(_DIRECTORS), "particles": 0, "projectiles": 0,
           "skills": 0, "impacts": 0, "cache": cache_size()}
    for d in _DIRECTORS:
        s = d.stats()
        out["particles"] += s["particles"]
        out["projectiles"] += s["projectiles"]
        out["skills"] += s["skills"]
        out["impacts"] += s["impacts"]
    return out


# ============================================================================
# 11.  API PUBLIK — dipanggil pipeline render & hook gameplay
# ============================================================================

def draw_ground_layer(surface, unit, x, y):
    """Pre-pass: digambar SEBELUM sprite di-blit (ground FX, back)."""
    if not VHALZUN_FX_ENABLED:
        return
    if not attach(unit):
        return
    tick()
    d = getattr(unit, "_vhalzun_fx", None)
    if d is not None:
        d.sync(unit, x, y)
        d.draw_ground(surface)


def draw_live_layer(surface, unit, x, y):
    """Post-pass: digambar SESUDAH sprite di-blit (trail, proj, impact)."""
    if not VHALZUN_FX_ENABLED:
        return
    d = director_for(unit)
    d.draw_front(surface)
    if DEBUG_CHARACTER:
        try:
            debug_overlay(surface, unit, x, y)
        except Exception:
            pass


# ── hook gameplay ────────────────────────────────────────────────────

def notify_melee_impact(unit, target, damage=0, crit=False):
    """Sabit Vhalzun mendarat di target (basic attack swing).

    Kalau ayunan masih di awal cycle (damage hook lebih dulu dari frame
    visual benturan), impact DITAHAN sampai frame bilah menyentuh —
    jadi flash & hit-stop sinkron dengan mata pedang.
    """
    if not VHALZUN_FX_ENABLED or unit is None or target is None:
        return
    try:
        power = 0.75 + min(1.5, float(damage) / 70.0)
    except (TypeError, ValueError):
        power = 1.0
    tx = float(getattr(target, "x", getattr(unit, "x", 0.0)))
    ty = float(getattr(target, "y", getattr(unit, "y", 0.0))) - 6.0
    ang = math.atan2(ty - float(getattr(unit, "y", 0.0)),
                     tx - float(getattr(unit, "x", 0.0)))
    d = director_for(unit)
    active = bool(getattr(unit, "_vhz_attack_active", False))
    ap = float(getattr(unit, "_vhz_attack_progress", 0.0) or 0.0)
    kind = getattr(unit, "_vhz_attack_kind", "swing") or "swing"
    if active and kind == "swing" and ap < ATK_IMPACT:
        d._pending_impact = (tx, ty, ang, power, bool(crit), "scythe")
        return
    d.on_impact(tx, ty, ang, power, bool(crit), kind="scythe")
    d._pending_impact = None


def notify_projectile_impact(unit, x, y, angle=0.0, damage=0, crit=False,
                             kind="soul"):
    """Death pulse mengenai target (basic attack jarak jauh)."""
    if not VHALZUN_FX_ENABLED or unit is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    d = director_for(unit)
    active = bool(getattr(unit, "_vhz_attack_active", False))
    ap = float(getattr(unit, "_vhz_attack_progress", 0.0) or 0.0)
    atk_kind = getattr(unit, "_vhz_attack_kind", "pulse") or "pulse"
    hero_lane = getattr(unit, "_render_scale", None) is not None
    if not hero_lane and active and atk_kind == "pulse" \
            and ap < ATK_RELEASE + 0.1:
        # jalur BOSS: damage instan, impact visual ditahan sampai orb
        # prosedural mendarat.
        d._pending_impact = (float(x), float(y), float(angle), power,
                             bool(crit), kind)
        return
    if hero_lane and active and atk_kind == "swing":
        d._pending_impact = (float(x), float(y), float(angle), power,
                             bool(crit), "scythe")
        return
    d.on_impact(float(x), float(y), float(angle), power, bool(crit),
                kind=kind)
    d._pending_impact = None


def notify_skill_cast(unit, skill, x=None, y=None):
    """Skill dilepaskan (Q/W/E/R) — buat SkillFX lifecycle penuh."""
    if not VHALZUN_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    skill = str(skill)
    if any(fx.skill == skill for fx in d.skills):
        return
    px = float(x) if x is not None else float(getattr(unit, "x", 0.0))
    py = float(y) if y is not None else float(getattr(unit, "y", 0.0))
    d.on_cast(px, py, skill)


def notify_skill_impact(unit, x, y, radius=None, skill="q"):
    """Skill meledak di sebuah titik (AOE) — impact + shockwave."""
    if not VHALZUN_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if not any(fx.skill == skill for fx in d.skills):
        d.on_cast(float(getattr(unit, "x", x)),
                  float(getattr(unit, "y", y)), skill)
    d.on_impact(float(x), float(y), angle=0.0,
                power=1.2 if skill in ("q", "r") else 0.9,
                crit=False, kind="skill")
    if radius:
        c = _P
        d.particles.burst(
            float(x), float(y), 14, speed=(80, 260), life=(0.2, 0.5),
            size=(1.5, 3.5),
            colors=(c["necro_light"], c["necro_bright"], c["necro_hot"]),
            shape="shard", drag=2.2, additive=True,
            rotation_speed=(-6, 6))


def notify_death(unit):
    """Unit mati — dipanggil hook base_boss.take_damage saat hp <= 0."""
    if not VHALZUN_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    d.on_death(float(getattr(unit, "x", 0.0)),
               float(getattr(unit, "y", 0.0)))


# ============================================================================
# 12.  OVERLAY DEBUG (DEBUG_CHARACTER = True)
# ============================================================================

_DBG_FONT = None


def _dbg_font(size=12):
    global _DBG_FONT
    if _DBG_FONT is None:
        try:
            _DBG_FONT = pygame.font.Font(None, size + 4)
        except Exception:                        # pragma: no cover
            _DBG_FONT = pygame.font.Font(None, 16)
    return _DBG_FONT


def debug_overlay(surface, unit, x, y):
    """Hitbox, hurtbox, range, state, frame, FPS, partikel, skill."""
    d = getattr(unit, "_vhalzun_fx", None)
    if d is None:
        return
    sc = body_scale(unit)
    gy = y + ground_dy(unit)
    # attack range (melee) & hurtbox
    pygame.draw.circle(surface, (255, 200, 60), (int(x), int(y)),
                       int(MELEE_REACH * sc), 1)
    hurt = pygame.Rect(int(x - 23 * sc), int(y - 52 * sc),
                       int(46 * sc), int(74 * sc))
    pygame.draw.rect(surface, (80, 160, 255), hurt, 1)
    # hitbox swing saat jendela aktif
    active = bool(getattr(unit, "_vhz_hit_active", False))
    if active:
        f = 1 if (getattr(unit, "direction", 1) or 1) >= 0 else -1
        reach = int(MELEE_REACH * 0.9 * sc)
        top = int(y - 44 * sc)
        h = int(76 * sc)
        left = int(x) if f > 0 else int(x) - reach
        pygame.draw.rect(surface, (255, 80, 80),
                         (left, top, max(8, reach), max(10, h)), 1)
    # garis pivot->tip sabit
    pv, tip = scythe_points(unit, x, y)
    pygame.draw.line(surface, (90, 255, 90),
                     (int(pv.x), int(pv.y)), (int(tip.x), int(tip.y)), 1)
    pygame.draw.circle(surface, (90, 255, 90), (int(tip.x), int(tip.y)), 3, 1)
    # teks state
    s = d.stats()
    lines = [
        f"VHALZUN[{CHARACTER_NAME}] state={s['state']}"
        f"<{s['state_prev']}> t={s['state_time']:.2f}",
        f"pose={pose_of(unit)[0]} kind={s['attack_kind']} "
        f"phase={s['attack_phase']} ap={s['attack_progress']:.2f}",
        f"skill={s['skill']} frame={s['anim_frame']}",
        f"partikel={s['particles']} proj={s['projectiles']} "
        f"impact={s['impacts']} fps={s['fps']:.0f}",
    ]
    font = _dbg_font()
    yy = int(y - 100 * sc)
    for ln in lines:
        img = font.render(ln, True, (180, 255, 180))
        surface.blit(img, (int(x - 100), yy))
        yy += 13
