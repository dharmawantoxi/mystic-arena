# ============================================================================
# heroes/gravefang_fx.py
# ----------------------------------------------------------------------------
# GRAVEFANG — THE BONE DEVOURER  ·  LAPISAN TEMPUR HIDUP (v2)
#
# Pasangan dari renderer ``bosses/level5.py :: _NS_gravefang``.  Pembagian
# tugasnya tegas:
#
#   renderer   -> SATU-SATUNYA pemilik geometri badan & gada (rig, palet,
#                 pose, controller animasi, ARC ayunan, telegraph fallback)
#   modul ini  -> SEMUA yang hidup di RUANG LAYAR skala 1:1 — swing trail,
#                 particle system, proyektil (pecahan tulang & boulder),
#                 skill FX q/w/e/r, impact FX, afterimage, overlay debug
#   combat_feel-> bus global hit-stop & screen shake (dipakai bersama)
#
# Kenapa dipisah?  Di lane hero, sprite badan di-*cache* lalu
# ``smoothscale``-kan.  Efek apa pun yang digambar ke canvas badan ikut
# BEKU dan ikut MENYUSUT.  Dengan memisahkan lapisan hidup ke ruang layar,
# trail/partikel/proyektil selalu 60 fps sejati dan selalu setajam layar.
#
# Modul ini TIDAK pernah menghitung ulang pose.  Ia MEMBACA
# ``_NS_gravefang.pose_of()`` / ``club_points()`` lewat jembatan malas
# ``_renderer()``, jadi gada dan trail-nya mustahil berbeda satu frame pun.
#
# 100% PROSEDURAL: tidak ada PNG / JPG / GIF / sprite-sheet / aset
# eksternal dan tidak ada pemuatan gambar di mana pun.
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
CHARACTER_NAME = "gravefang"

#: Overlay debug (hitbox, hurtbox, state, FPS, jumlah partikel, ...).
DEBUG_CHARACTER = False

#: Master switch lapisan hidup.  False -> renderer memakai fallback canvas.
GRAVEFANG_FX_ENABLED = True

#: Cap keras — tidak ada satu pun sistem yang boleh tumbuh tanpa batas.
MAX_PARTICLES = 240
MAX_PROJECTILES = 10
TRAIL_SAMPLES = 12
MAX_IMPACTS = 8
MAX_SKILLS = 4
MAX_AFTERIMAGES = 8

FIXED_DT = 1.0 / 60.0

#: Kecepatan proyektil (px/detik ruang layar).
SHARD_SPEED = 300.0          # pecahan tulang (serangan dasar jarak jauh)
BOULDER_SPEED = 360.0        # rolling boulder (skill W)

#: Durasi skill dalam FRAME — HARUS sama dengan renderer & AI
#: (_smart_ai_gravefang: q 60, w 70, e 70, r 100).
SKILL_DUR = {"q": 60, "w": 70, "e": 70, "r": 100}

#: Radius efek di RUANG DUNIA — sama dengan radius damage AI.
WORLD_RADIUS = {"q": 120.0, "w": 150.0, "e": 100.0, "r": 180.0}

#: Jarak dunia (px) — di bawahnya Gravefang menghantam dengan gada.
#: Nilai HARUS sama dengan _NS_gravefang.MELEE_REACH.
MELEE_REACH = 78.0

#: Fase serangan — identik dengan renderer.
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.14),
    ("WINDUP",       0.14, 0.32),
    ("SWING",        0.32, 0.52),
    ("IMPACT",       0.52, 0.64),
    ("FOLLOW",       0.64, 0.84),
    ("RECOVERY",     0.84, 1.00),
)

ATTACK_ACTIVE_WINDOW = (0.32, 0.58)
ATTACK_IMPACT_FRAME = 0.46
ATTACK_RELEASE_FRAME = 0.34
ATK_IMPACT = ATTACK_IMPACT_FRAME
ATK_RELEASE = ATTACK_RELEASE_FRAME

#: Prioritas state animasi — identik dengan renderer.
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

SKILL_PHASES = (
    ("CAST",    0.00, 0.16),
    ("CHARGE",  0.16, 0.34),
    ("RELEASE", 0.34, 0.46),
    ("AREA",    0.46, 0.74),
    ("IMPACT",  0.74, 0.86),
    ("AFTER",   0.86, 1.00),
)


def attack_phase(progress):
    """Nama fase serangan untuk progress 0..1."""
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
# 2.  PALETTE  (disalin dari renderer saat pertama dipakai)
# ============================================================================

GRAVEFANG_PALETTE = {
    "outline":        (7,   9,   6),
    "bone_darkest":   (48,  52,  38),
    "bone_dark":      (86,  92,  66),
    "bone_mid":       (140, 148, 108),
    "bone_light":     (192, 198, 156),
    "bone_high":      (224, 230, 194),
    "bone_shine":     (245, 248, 228),
    "hide_darkest":   (14,  24,  12),
    "hide_dark":      (30,  48,  22),
    "hide_mid":       (54,  80,  34),
    "hide_light":     (86,  120, 50),
    "hide_high":      (124, 164, 70),
    "rock_darkest":   (20,  22,  24),
    "rock_dark":      (42,  46,  50),
    "rock_mid":       (72,  78,  82),
    "rock_light":     (108, 116, 120),
    "rock_high":      (150, 158, 162),
    "grave_darkest":  (18,  40,  8),
    "grave_dark":     (54,  100, 16),
    "grave_mid":      (104, 168, 28),
    "grave_light":    (150, 220, 55),
    "grave_bright":   (190, 245, 100),
    "grave_hot":      (222, 255, 165),
    "grave_white":    (245, 255, 215),
    "iron_dark":      (34,  28,  24),
    "iron_mid":       (68,  58,  48),
    "iron_light":     (110, 96,  78),
    "iron_shine":     (158, 142, 116),
    "gore_dark":      (52,  14,  14),
    "gore_mid":       (96,  26,  24),
    "gore_light":     (146, 48,  38),
    "eye_dark":       (40,  84,  6),
    "eye_mid":        (120, 200, 20),
    "eye_bright":     (185, 245, 80),
    "eye_hot":        (235, 255, 180),
    "shadow":         (0,   0,   0),
    "shadow_deep":    (3,   6,   3),
    "white":          (255, 255, 255),
}

_P = GRAVEFANG_PALETTE
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
    """Muat ``_NS_gravefang`` dari bosses.level5 sekali; None kalau gagal."""
    global _RENDERER
    if _RENDERER is False:
        return None
    if _RENDERER is None:
        try:
            from bosses import level5 as _L
            _RENDERER = getattr(_L, "_NS_gravefang", None) or False
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
    if getattr(boss, "_gf_attack_active", False):
        return ("attack", float(getattr(boss, "pulse", 0.0)),
                float(getattr(boss, "_gf_attack_progress", 0.0) or 0.0))
    return ("idle", float(getattr(boss, "pulse", 0.0)), 0.0)


def club_points(boss, x, y):
    """(pivot, head) pygame.Vector2 ruang LAYAR dari renderer."""
    G = _renderer()
    if G is not None:
        try:
            return G.club_points(boss, x, y)
        except Exception:
            pass
    f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
    sc = body_scale(boss)
    pivot = pygame.Vector2(x + 12 * f * sc, y - 20 * sc)
    tip = pygame.Vector2(x + 24 * f * sc, y - 58 * sc)
    return (pivot, tip)


#: Alias kompatibilitas (beberapa alat memakai nama generik).
def weapon_points(boss, x, y):
    return club_points(boss, x, y)


def staff_points(boss, x, y):
    return club_points(boss, x, y)


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
    base = float(getattr(G, "GROUND_DY", 52)) if G is not None else 52.0
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
    """Bola glow radial (cache per radius+warna+power)."""
    radius = max(2, int(radius))
    key = ("glow", radius, tuple(color[:3]), round(float(power), 2))
    s = _CACHE.get(key)
    if s is None:
        size = radius * 2 + 2
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        for r in range(radius, 0, -1):
            a = int(150 * power * (1.0 - r / float(radius)) ** 1.7)
            if a > 0:
                pygame.draw.circle(s, (*color[:3], min(255, a)), (c, c), r)
        s = _cache_put(key, s)
    return s


def ring_surface(radius, thickness, color, alpha=255, teeth=0):
    """Cincin chunky; ``teeth`` > 0 -> cincin bergerigi (bukan lingkaran
    polos) — dipakai shockwave Boulder Smash & Magnetize."""
    radius = max(2, int(radius))
    key = ("ring", radius, int(thickness), tuple(color[:3]), int(alpha),
           int(teeth))
    s = _CACHE.get(key)
    if s is None:
        size = radius * 2 + 6
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        col = (*color[:3], max(0, min(255, int(alpha))))
        if teeth <= 0:
            pygame.draw.circle(s, col, (c, c), radius,
                               max(1, int(thickness)))
        else:
            pts_o, pts_i = [], []
            n = teeth * 2
            for i in range(n):
                ang = i * math.tau / n
                rr = radius if i % 2 == 0 else radius * 0.80
                ri = rr - max(1, int(thickness))
                pts_o.append((c + math.cos(ang) * rr,
                              c + math.sin(ang) * rr))
                pts_i.append((c + math.cos(ang) * ri,
                              c + math.sin(ang) * ri))
            pygame.draw.polygon(s, col, pts_o + pts_i[::-1])
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


def rock_decal(size, alpha=255, seed=0):
    """Bongkahan batu pixel-art (cache) — boulder W, debris, Magnetize."""
    size = max(4, int(size))
    key = ("rock", size, int(alpha), int(seed) % 4)
    s = _CACHE.get(key)
    if s is None:
        w = h = size * 2 + 4
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        a = max(0, min(255, int(alpha)))
        rng = random.Random(1000 + int(seed) % 4)
        pts = []
        n = 7
        for i in range(n):
            ang = i * math.tau / n + rng.uniform(-0.15, 0.15)
            rr = size * rng.uniform(0.78, 1.0)
            pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
        pygame.draw.polygon(s, (*_P["outline"], a),
                            [(px, py + 1) for px, py in pts])
        pygame.draw.polygon(s, (*_P["rock_dark"], a), pts)
        # bidang tercahaya (kiri-atas), bukan poligon konsentris
        lit = [(cx, cy)]
        for px, py in pts:
            if (px - cx) * -0.7 + (py - cy) * -0.7 > 0:
                lit.append((cx + (px - cx) * 0.9, cy + (py - cy) * 0.9))
        if len(lit) >= 3:
            pygame.draw.polygon(s, (*_P["rock_mid"], a), lit)
        pygame.draw.circle(s, (*_P["rock_light"], a),
                           (int(cx - size * 0.3), int(cy - size * 0.3)),
                           max(1, size // 3))
        # urat energi kubur di celah batu
        pygame.draw.line(s, (*_P["grave_mid"], a),
                         (cx - size // 2, cy + size // 4),
                         (cx + size // 3, cy - size // 5), 2)
        s = _cache_put(key, s)
    return s


def skull_decal(size, alpha=255):
    """Tengkorak pixel-art kecil (cache) — totem E, orbit R, impact."""
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
        pygame.draw.circle(s, bone, (cx, cy - 1), size)
        pygame.draw.rect(s, bone, (cx - size + 2, cy - 1, (size - 2) * 2, 3))
        pygame.draw.rect(s, bone_hi, (cx - size // 2, cy - size - 1, 2, 2))
        pygame.draw.rect(s, dark, (cx - size // 2 - 1, cy - 2, 3, 3))
        pygame.draw.rect(s, dark, (cx + size // 2 - 1, cy - 2, 3, 3))
        pygame.draw.rect(s, eye, (cx - size // 2 - 1, cy - 1, 2, 2))
        pygame.draw.rect(s, eye, (cx + size // 2 - 1, cy - 1, 2, 2))
        pygame.draw.rect(s, dark, (cx - 1, cy + 1, 2, 2))
        for i in range(3):
            pygame.draw.rect(s, dark, (cx - 2 + i * 2, cy + 3, 1, 2))
        s = _cache_put(key, s)
    return s


def totem_sprite(size, alpha=230):
    """Geomagnetic Grip: pasak tulang tertancap (skill E)."""
    size = max(6, int(size))
    key = ("totem", size, int(alpha))
    s = _CACHE.get(key)
    if s is None:
        w = size * 2 + 8
        h = size * 3 + 10
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        cx = w // 2
        a = max(0, min(255, int(alpha)))
        # pasak tulang tertancap ke tanah
        pygame.draw.polygon(s, (*_P["outline"], a), [
            (cx - 4, size), (cx + 4, size),
            (cx + 3, h - 4), (cx - 3, h - 4)])
        pygame.draw.polygon(s, (*_P["bone_dark"], a), [
            (cx - 3, size), (cx + 3, size),
            (cx + 2, h - 5), (cx - 2, h - 5)])
        pygame.draw.line(s, (*_P["bone_light"], a),
                         (cx - 1, size + 1), (cx - 1, h - 6), 1)
        # bonggol tulang di puncak
        pygame.draw.circle(s, (*_P["outline"], a), (cx, size), size // 2 + 1)
        pygame.draw.circle(s, (*_P["bone_dark"], a), (cx, size), size // 2)
        pygame.draw.circle(s, (*_P["bone_mid"], a), (cx - 1, size - 1),
                           max(1, size // 2 - 1))
        # duri samping
        for k in (-1, 1):
            pygame.draw.polygon(s, (*_P["bone_light"], a), [
                (cx + k * (size // 2), size - size // 3),
                (cx + k * (size // 2 + 3), size - size),
                (cx + k * (size // 3), size - size // 2)])
        # mata energi kubur
        pygame.draw.rect(s, (*_P["grave_bright"], a),
                         (cx - size // 3 - 1, size - 1, 2, 2))
        pygame.draw.rect(s, (*_P["grave_bright"], a),
                         (cx + size // 3 - 1, size - 1, 2, 2))
        s = _cache_put(key, s)
    return s


def _blit_faded(surface, surf, cx, cy, alpha=255.0, additive=False):
    """Blit surface dengan alpha dinamis (jalur murah: set_alpha)."""
    alpha = max(0, min(255, int(alpha)))
    if alpha <= 2 or surf is None:
        return
    cx, cy = int(cx), int(cy)
    prev = surf.get_alpha()
    surf.set_alpha(alpha)
    if additive and glow_allowed():
        surface.blit(surf, (cx - surf.get_width() // 2,
                            cy - surf.get_height() // 2),
                     special_flags=pygame.BLEND_RGB_ADD)
    else:
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
    """Pita meruncing (dipakai tarikan Geomagnetic Grip / Magnetize)."""
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


def ground_crack(surface, x0, y0, ang, length, color, alpha, seed=0):
    """Retakan tanah zig-zag prosedural (identitas earth-bruiser)."""
    rng = random.Random(int(seed))
    pts = [(x0, y0)]
    n = 5
    for i in range(1, n + 1):
        u = i / n
        wob = rng.uniform(-0.35, 0.35)
        px = x0 + math.cos(ang + wob) * length * u
        py = y0 + math.sin(ang + wob) * length * u * 0.42
        pts.append((px, py))
    col = (*color[:3], max(0, min(255, int(alpha))))
    if len(pts) >= 2:
        pygame.draw.lines(surface, col, False,
                          [(int(px), int(py)) for px, py in pts], 2)


def _clamp_color(color):
    return tuple(max(0, min(255, int(c))) for c in color)


def darken(color, k):
    return _clamp_color((color[0] * k, color[1] * k, color[2] * k))


# ============================================================================
# 4.  PARTICLE SYSTEM  (reusable: posisi, kecepatan, akselerasi, umur,
#     ukuran, rotasi, alpha, gravity, drag, bentuk)
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
        elif sh == "rubble":
            # pecahan batu bersudut yang berputar (khas earth-bruiser)
            r = max(2.0, s * 1.3)
            pts = []
            for i in range(5):
                ang = self.rotation + i * math.tau / 5
                rr = r if i % 2 == 0 else r * 0.6
                pts.append((x + math.cos(ang) * rr, y + math.sin(ang) * rr))
            pygame.draw.polygon(surface, (*c, a), pts)
            pygame.draw.polygon(surface, (*_P["rock_high"], min(255, a)),
                                pts, 1)
        elif sh == "wisp":
            # wisp kubur: kepala bulat + ekor mengecil ke atas
            r = max(1, int(s * 0.8))
            pygame.draw.circle(surface, (*c, a), (x, y), r)
            pygame.draw.circle(surface, (*c, a // 2), (x, y - r - 1),
                               max(1, r - 1))
            pygame.draw.circle(surface, (255, 255, 255, a), (x, y - 1), 1)
        elif sh == "ember":
            pygame.draw.rect(surface, (*c, a),
                             (x, y, max(1, int(s)), max(1, int(s))))
            if a > 120:
                pygame.draw.rect(surface, (255, 255, 255, a // 2), (x, y, 1, 1))
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
              size=(1.5, 3.5), colors=((104, 168, 28),), spread=math.tau,
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
                      colors=((150, 220, 55),), shape="wisp", drag=0.0,
                      layer="front", accel=(0.0, 0.0)):
        """Partikel yang bergerak MENUJU titik (tarikan Magnetize)."""
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
# 5.  SWING TRAIL  (ribbon dari histori posisi kepala gada)
# ============================================================================

class SwingTrail:
    """Ribbon translusen yang mengikuti jejak kepala gada.

    Menyimpan sampel posisi (OLD ... CURRENT) selama gada bergerak
    cepat; digambar sebagai polygon memudar + partikel pixel di tepi.
    Trail otomatis mengikuti ARAH serangan karena ia mengambil posisi
    nyata kepala gada tiap frame.
    """

    __slots__ = ("samples", "life", "cap")

    def __init__(self, cap=TRAIL_SAMPLES, life=0.18):
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
        for i in range(n - 1):
            t0 = ages[i] / max_age
            t1 = ages[i + 1] / max_age
            if t1 <= 0.0:
                continue
            a0, a1 = int(200 * t0), int(210 * t1)
            p0, p1 = pts[i], pts[i + 1]
            d = p1 - p0
            ln = d.length()
            if ln < 0.3:
                continue
            nvec = pygame.Vector2(-d.y, d.x) / ln
            # gada jauh lebih berat dari tongkat -> pita lebih tebal
            w0 = max(1.0, 12.0 * t0)
            w1 = max(1.0, 12.0 * t1)
            quad = [
                (p0.x + nvec.x * w0, p0.y + nvec.y * w0),
                (p1.x + nvec.x * w1, p1.y + nvec.y * w1),
                (p1.x - nvec.x * w1, p1.y - nvec.y * w1),
                (p0.x - nvec.x * w0, p0.y - nvec.y * w0),
            ]
            if glow_allowed():
                pygame.draw.polygon(
                    surface, (*_P["grave_dark"], min(255, (a0 + a1) // 3)),
                    quad)
            pygame.draw.polygon(
                surface, (*_P["grave_mid"], min(255, (a0 + a1) // 2)), quad)
            pygame.draw.polygon(
                surface, (*_P["grave_bright"], min(255, (a0 + a1) // 2)),
                quad, 1)
        # ── inti terang: garis tebal dari sampel lama ke CURRENT ───
        if glow_allowed():
            core = [(p.x, p.y) for p, a in zip(pts, ages) if a > 0.0]
            if len(core) >= 2:
                pygame.draw.lines(surface, (*_P["grave_light"], 150),
                                  False, core, 2)
                pygame.draw.lines(surface, (*_P["grave_hot"], 200),
                                  False, core, 1)
        # ── percikan pixel di sepanjang tepi (chunky) ──────────────
        for i in range(0, n, 2):
            t = ages[i] / max_age
            if t <= 0.15:
                continue
            p = pts[i]
            pygame.draw.rect(surface,
                             (*_P["grave_bright"], int(230 * t)),
                             (int(p.x) - 1, int(p.y) - 1, 2, 2))


# ============================================================================
# 6.  IMPACT FX  (hit flash + sparks + shockwave + debris + slash)
# ============================================================================

class ImpactFX:
    """Satu kejadian benturan: flash bintang, shockwave bergerigi,
    serpihan batu, retakan tanah.  Hook hit-stop & shake dipanggil saat
    spawn (lewat combat_feel)."""

    __slots__ = ("x", "y", "kind", "angle", "power", "crit", "t", "dur",
                 "alive", "_seed")

    def __init__(self, x, y, kind="grave", angle=0.0, power=1.0,
                 crit=False, dur=0.36):
        self.x = float(x)
        self.y = float(y)
        self.kind = str(kind)
        self.angle = float(angle)
        self.power = max(0.4, float(power))
        self.crit = bool(crit)
        self.t = 0.0
        self.dur = float(dur) * (1.25 if crit else 1.0)
        self.alive = True
        self._seed = random.randint(0, 9999)

    def update(self, dt):
        self.t += dt
        if self.t >= self.dur:
            self.alive = False

    def draw(self, surface):
        t01 = self.t / self.dur
        inv = 1.0 - t01
        k = self.power
        if self.kind == "club":
            self._draw_slam(surface, t01, inv, k)
        elif self.kind == "skill":
            self._draw_skill(surface, t01, inv, k)
        else:
            self._draw_grave(surface, t01, inv, k)

    # ── benturan gada: shockwave tanah + retakan + debris ───────────
    def _draw_slam(self, surface, t, inv, k):
        c = _P
        ang = self.angle
        # busur hantaman (sapuan berat, lebih lebar dari sabetan)
        if t < 0.55:
            fade = 1.0 - t / 0.55
            span = 2.1
            r0, r1 = 18.0 * k, 46.0 * k
            rot = ang + 0.9 - t * 2.4
            n = 10
            outer, inner = [], []
            for i in range(n + 1):
                a = rot - span / 2 + span * i / n
                rr = r0 + (r1 - r0) * (i / n)
                outer.append((self.x + math.cos(a) * rr,
                              self.y + math.sin(a) * rr * 0.8))
                inner.append((self.x + math.cos(a) * (rr - 11.0 * fade * k),
                              self.y + math.sin(a) * (rr - 11.0 * fade * k) * 0.8))
            poly = outer + inner[::-1]
            pygame.draw.polygon(surface,
                                (*c["grave_mid"], int(190 * fade)), poly)
            pygame.draw.polygon(surface,
                                (*c["grave_light"], int(230 * fade)), poly, 2)
        # shockwave bergerigi di tanah
        if t < 0.5:
            rr = (14.0 + t * 100.0) * k
            a = int(210 * (1.0 - t / 0.5))
            _blit_faded(surface, ring_surface(int(rr), 3, c["grave_light"],
                                              a, teeth=8),
                        self.x, self.y, a)
        # retakan tanah menyebar dari titik benturan
        if t < 0.62:
            a = int(200 * (1.0 - t / 0.62))
            for i in range(5):
                ca = ang - 1.2 + i * 0.6
                ground_crack(surface, self.x, self.y, ca,
                             (26.0 + t * 40.0) * k, c["grave_dark"], a,
                             seed=self._seed + i)
        # flash bintang di frame awal
        if t < 0.18:
            s = (12.0 + 30.0 * k) * (1.0 - t / 0.18)
            spark_star(surface, self.x, self.y, s, c["grave_white"],
                       int(235 * (1.0 - t / 0.18)), spikes=6, rot=ang + 0.4)

    # ── benturan pecahan tulang ────────────────────────────────────
    def _draw_grave(self, surface, t, inv, k):
        c = _P
        if t < 0.22:
            s = (9.0 + 18.0 * k) * inv
            spark_star(surface, self.x, self.y, s, c["grave_white"],
                       int(235 * inv), spikes=5, rot=self.angle)
        if t < 0.6:
            rr = (8.0 + t * 62.0) * k
            a = int(200 * (1.0 - t / 0.6))
            _blit_faded(surface, ring_surface(int(rr), 2, c["grave_bright"],
                                              a, teeth=5),
                        self.x, self.y, a)
        # tengkorak kilat (khas Bone Devourer)
        if t < 0.30 and k >= 0.9:
            sk = skull_decal(int(5 + 3 * inv))
            _blit_faded(surface, sk, self.x, self.y - 2,
                        200 * (1.0 - t / 0.30))

    # ── benturan skill ─────────────────────────────────────────────
    def _draw_skill(self, surface, t, inv, k):
        c = _P
        if t < 0.3:
            s = (16.0 + 32.0 * k) * inv
            spark_star(surface, self.x, self.y, s, c["grave_white"],
                       int(240 * inv), spikes=8, rot=self.angle + 0.2)
        rr = (16.0 + t * 120.0) * k
        a = int(190 * inv)
        _blit_faded(surface, ring_surface(int(rr), 3, c["grave_light"], a,
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

    def __init__(self, x, y, tx, ty, speed=SHARD_SPEED, damage=0.0,
                 target=None, radius=8.0, lifetime=3.0, on_impact=None,
                 ground=52.0, kind="grave"):
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
                             kind="grave", angle=self.rotation, power=0.9))

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
                surface, (*c["grave_dark"], int(140 * a1 / 0.16)), quad)

    def _draw_body(self, surface):
        pygame.draw.circle(surface, (*_P["grave_mid"], 255),
                           (int(self.pos.x), int(self.pos.y)),
                           int(self.radius))


class BoneShardProjectile(BaseProjectile):
    """Pecahan tulang — bilah bergerigi yang BERPUTAR mengikuti arah
    lempar, dengan trail debu dan percikan tulang kecil."""

    def __init__(self, x, y, tx, ty, speed=SHARD_SPEED, damage=0.0,
                 target=None, on_impact=None, ground=52.0):
        super().__init__(x, y, tx, ty, speed=speed, damage=damage,
                         target=target, radius=8.0, lifetime=3.0,
                         on_impact=on_impact, ground=ground, kind="grave")
        self._home = 2.0          # kekuatan homing ringan
        self._spin = 0.0

    def travel(self, dt):
        self._spin += dt * 14.0
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
        if random.random() < dt * 38.0 * particle_budget():
            system.particles.spawn(
                self.pos.x + random.uniform(-3, 3),
                self.pos.y + random.uniform(-3, 3),
                random.uniform(-18, 18), random.uniform(-26, -4),
                random.uniform(0.18, 0.4), random.uniform(1.5, 2.6),
                random.choice((_P["bone_light"], _P["grave_light"])),
                shape="dust", drag=1.4)

    def _draw_body(self, surface):
        c = _P
        x, y = int(self.pos.x), int(self.pos.y)
        if glow_allowed():
            _blit_faded(surface, glow_surface(13, c["grave_mid"], 0.7),
                        x, y, 165, additive=True)
        # bilah tulang bergerigi (poligon runcing, BUKAN lingkaran)
        ang = self._spin
        pts = []
        for i in range(6):
            a = ang + i * math.tau / 6
            rr = 10.0 if i % 2 == 0 else 5.0
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        pygame.draw.polygon(surface, (*c["outline"], 255),
                            [(px, py + 1) for px, py in pts])
        pygame.draw.polygon(surface, (*c["bone_dark"], 255), pts)
        # bidang tercahaya (directional, bukan konsentris)
        lit = [(x, y)]
        for px, py in pts:
            if (px - x) * -0.7 + (py - y) * -0.7 > 0:
                lit.append((x + (px - x) * 0.9, y + (py - y) * 0.9))
        if len(lit) >= 3:
            pygame.draw.polygon(surface, (*c["bone_light"], 255), lit)
        pygame.draw.circle(surface, (*c["grave_hot"], 255), (x, y), 2)
        # percikan orbit
        for i in range(3):
            a = self.age * 9.0 + i * math.tau / 3
            sx = x + int(math.cos(a) * 11)
            sy = y + int(math.sin(a) * 11)
            pygame.draw.rect(surface, (*c["grave_bright"], 230),
                             (sx - 1, sy - 1, 2, 2))


class BoulderProjectile(BaseProjectile):
    """Rolling Boulder (skill W) — bongkahan batu besar yang MENGGELINDING
    di tanah: rotasi searah gerak, debu tergilas, afterimage, dan
    retakan tanah di belakangnya."""

    def __init__(self, x, y, tx, ty, speed=BOULDER_SPEED, damage=0.0,
                 target=None, on_impact=None, ground=52.0):
        super().__init__(x, y, tx, ty, speed=speed, damage=damage,
                         target=target, radius=15.0, lifetime=2.4,
                         on_impact=on_impact, ground=ground, kind="boulder")
        self._roll = 0.0
        self._aft = []               # afterimage [(pos, roll, umur)]

    def travel(self, dt):
        # menggelinding: rotasi proporsional jarak tempuh / radius
        self._roll += (self.speed * dt) / max(4.0, self.radius)
        self.pos += self.vel * dt
        self.rotation = math.atan2(self.vel.y, self.vel.x)
        self._aft.append([pygame.Vector2(self.pos), self._roll, 0.14])
        if len(self._aft) > 8:
            self._aft.pop(0)
        for a in self._aft:
            a[2] -= dt
        self._aft = [a for a in self._aft if a[2] > 0.0]

    def emit(self, dt, system):
        # debu tergilas di bawah boulder
        if random.random() < dt * 46.0 * particle_budget():
            system.particles.spawn(
                self.pos.x + random.uniform(-10, 10),
                self.pos.y + random.uniform(4, 12),
                random.uniform(-40, 40), random.uniform(-46, -12),
                random.uniform(0.22, 0.5), random.uniform(2.0, 4.0),
                random.choice((_P["rock_mid"], _P["rock_light"],
                               _P["grave_dark"])),
                shape="dust", drag=1.8, layer="back")
        # pecahan batu kecil terlempar
        if random.random() < dt * 14.0 * particle_budget():
            system.particles.spawn(
                self.pos.x + random.uniform(-8, 8),
                self.pos.y + random.uniform(-4, 8),
                random.uniform(-70, 70), random.uniform(-120, -40),
                random.uniform(0.3, 0.6), random.uniform(1.5, 2.8),
                random.choice((_P["rock_light"], _P["bone_mid"])),
                shape="rubble", gravity=320.0, drag=0.5,
                rotation_speed=random.uniform(-8, 8))

    def _draw_body(self, surface):
        c = _P
        x, y = int(self.pos.x), int(self.pos.y)
        # afterimage (memudar) — kesan kecepatan
        for apos, aroll, aage in self._aft:
            k = aage / 0.14
            _blit_faded(surface, rock_decal(12, 150, seed=1),
                        apos.x, apos.y, 90 * k)
        if glow_allowed():
            _blit_faded(surface, glow_surface(24, c["grave_dark"], 0.7),
                        x, y, 150, additive=True)
        # bongkahan batu yang BERGULIR (rotasi nyata)
        rock = rock_decal(15, 255, seed=0)
        rot = pygame.transform.rotate(rock, -math.degrees(self._roll))
        surface.blit(rot, (x - rot.get_width() // 2,
                           y - rot.get_height() // 2))
        # urat energi kubur berdenyut di permukaan batu
        pulse = 0.5 + 0.5 * math.sin(self.age * 14.0)
        for i in range(3):
            a = self._roll + i * math.tau / 3
            vx = x + int(math.cos(a) * 9)
            vy = y + int(math.sin(a) * 9)
            pygame.draw.rect(surface,
                             (*c["grave_bright"], int(160 + 80 * pulse)),
                             (vx - 1, vy - 1, 3, 3))


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

    def spawn_shard(self, x, y, tx, ty, **kw):
        self._make_room()
        p = BoneShardProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(p)
        return p

    def spawn_boulder(self, x, y, tx, ty, **kw):
        self._make_room()
        p = BoulderProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(p)
        return p

    def push_impact(self, fx):
        self.impacts.append(fx)
        while len(self.impacts) > MAX_IMPACTS:
            self.impacts.pop(0)

    def on_impact(self, proj):
        """Callback default: impact FX + burst partikel + game feel."""
        hp = proj.hit_pos or proj.pos
        kind = "skill" if proj.kind == "boulder" else "grave"
        power = 1.35 if proj.kind == "boulder" else 0.95
        self.push_impact(ImpactFX(hp.x, hp.y, kind=kind,
                                  angle=proj.rotation, power=power))
        c = _P
        if proj.kind == "boulder":
            self.particles.burst(
                hp.x, hp.y, 20, speed=(90, 360), life=(0.22, 0.55),
                size=(1.8, 4.0),
                colors=(c["rock_light"], c["rock_mid"], c["bone_light"]),
                shape="rubble", drag=1.8, gravity=300.0,
                rotation_speed=(-9, 9))
            self.particles.burst(
                hp.x, hp.y, 10, speed=(60, 200), life=(0.2, 0.5),
                size=(2.0, 4.5),
                colors=(c["grave_dark"], c["rock_dark"]),
                shape="dust", drag=2.2, layer="back")
            if _feel is not None:
                _feel.hit_stop(0.065)
                if shake_allowed():
                    _feel.shake(8.0, 0.28)
        else:
            self.particles.burst(
                hp.x, hp.y, 12, speed=(60, 250), life=(0.2, 0.45),
                size=(1.5, 3.0),
                colors=(c["bone_light"], c["grave_bright"],
                        c["grave_white"]),
                shape="shard", drag=2.4, rotation_speed=(-7, 7))
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
                 "total", "done", "_fired", "target", "_cracks", "_totems",
                 "_rocks")

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
        self._cracks = None
        self._totems = None
        self._rocks = None

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

    def _target_xy(self):
        t = self.target
        if t is not None and getattr(t, "alive", True):
            return (float(getattr(t, "x", self.x)),
                    float(getattr(t, "y", self.y)) - 8.0)
        return (self.x + self.facing * 150.0, self.y - 8.0)

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

    def draw_ground(self, surface):
        fn = getattr(self, "_gnd_" + self.skill, None)
        if fn is not None:
            fn(surface, self.t01)

    def draw_front(self, surface):
        fn = getattr(self, "_frn_" + self.skill, None)
        if fn is not None:
            fn(surface, self.t01)

    # ==================================================================
    # Q — BOULDER SMASH: gada dihantam ke tanah, batu mencuat + nova
    # ==================================================================
    def _upd_q(self, t, dt, particles):
        c = _P
        ph = skill_phase(t)
        # CAST+CHARGE: kerikil tersedot naik ke gada
        if ph in ("CAST", "CHARGE"):
            if random.random() < dt * 30.0:
                ang = random.uniform(0.0, math.tau)
                rr = random.uniform(40.0, 90.0) * self.scale
                particles.stream_toward(
                    self.x + math.cos(ang) * rr,
                    self.y + 30 + math.sin(ang) * rr * 0.4,
                    self.x, self.y - 18, 1,
                    speed=(120, 220), life=(0.2, 0.4), size=(1.5, 3.0),
                    colors=(c["rock_light"], c["bone_mid"]),
                    shape="rubble")
        # RELEASE: hantaman -> debu + pecahan batu + game feel
        if ph == "RELEASE" and self._once("q_burst"):
            gy = self.y + 34 * self.scale
            particles.burst(
                self.x, gy, 24, speed=(120, 380), life=(0.25, 0.6),
                size=(2.0, 4.5),
                colors=(c["rock_light"], c["rock_mid"], c["bone_light"]),
                shape="rubble", drag=1.6, gravity=340.0,
                rotation_speed=(-10, 10))
            particles.burst(
                self.x, gy, 14, speed=(60, 220), life=(0.3, 0.7),
                size=(2.5, 5.0),
                colors=(c["grave_dark"], c["rock_dark"]),
                shape="dust", drag=2.2, layer="back")
            if _feel is not None:
                _feel.hit_stop(0.06)
                if shake_allowed():
                    _feel.shake(8.5, 0.30)
        # AREA: bara kubur naik dari retakan
        if ph in ("AREA", "IMPACT"):
            if random.random() < dt * 26.0:
                rr = random.uniform(20.0, WORLD_RADIUS["q"] * 0.7) * self.scale
                ang = random.uniform(0.0, math.tau)
                particles.spawn(
                    self.x + math.cos(ang) * rr,
                    self.y + 34 * self.scale + math.sin(ang) * rr * 0.35,
                    random.uniform(-6, 6), random.uniform(-70, -30),
                    random.uniform(0.35, 0.7), random.uniform(1.5, 2.8),
                    random.choice((c["grave_light"], c["grave_bright"])),
                    shape="ember", additive=True)

    def _gnd_q(self, surface, t):
        """Tanah: retakan menyebar + nova bergerigi ganda."""
        c = _P
        ph = skill_phase(t)
        gy = self.y + 34 * self.scale
        if ph in ("CAST", "CHARGE"):
            # telegraph: lingkaran mengecil (peringatan area)
            k = t / 0.34
            rr = int(WORLD_RADIUS["q"] * self.scale * (1.25 - 0.25 * k))
            _blit_faded(surface,
                        ellipse_ring_surface(rr, max(3, rr // 3), 2,
                                             c["grave_dark"], 150),
                        self.x, gy, 150)
            return
        prog = min(1.0, (t - 0.34) / 0.52)
        if prog >= 1.0:
            return
        # retakan tanah radial (deterministik per cast)
        if self._cracks:
            a = int(220 * (1.0 - prog))
            for ang, ln, seed in self._cracks:
                ground_crack(surface, self.x, gy, ang,
                             ln * self.scale * min(1.0, prog * 2.2),
                             c["grave_bright"], a, seed=seed)
        # nova bergerigi ganda yang mengembang
        for wave in (0.0, 0.14):
            wp = min(1.0, max(0.0, prog - wave))
            if wp <= 0.0:
                continue
            rr = int(WORLD_RADIUS["q"] * self.scale * wp)
            a = int(210 * (1.0 - wp))
            if a <= 4:
                continue
            _blit_faded(surface,
                        ring_surface(rr, 4, c["grave_light"], 255, teeth=9),
                        self.x, gy, a)

    def _frn_q(self, surface, t):
        """Depan: pilar batu mencuat dari tanah saat hantaman."""
        c = _P
        ph = skill_phase(t)
        if ph in ("CAST", "CHARGE"):
            return
        prog = min(1.0, (t - 0.34) / 0.52)
        if prog >= 1.0 or not self._rocks:
            return
        gy = self.y + 34 * self.scale
        for ang, dist, hgt, seed in self._rocks:
            # pilar naik cepat lalu turun perlahan
            k = min(1.0, prog * 3.0)
            fall = max(0.0, (prog - 0.55) / 0.45)
            up = hgt * self.scale * k * (1.0 - fall * 0.85)
            if up <= 1.0:
                continue
            px = self.x + math.cos(ang) * dist * self.scale
            py = gy + math.sin(ang) * dist * self.scale * 0.35
            a = int(255 * (1.0 - fall))
            # pilar: trapesium batu bersudut
            w = 7 * self.scale
            pts = [(px - w, py), (px + w, py),
                   (px + w * 0.55, py - up), (px - w * 0.65, py - up)]
            pygame.draw.polygon(surface, (*c["outline"], a),
                                [(qx + 1, qy + 1) for qx, qy in pts])
            pygame.draw.polygon(surface, (*c["rock_dark"], a), pts)
            pygame.draw.polygon(surface, (*c["rock_mid"], a), [
                (px - w * 0.8, py), (px - w * 0.1, py),
                (px - w * 0.2, py - up), (px - w * 0.6, py - up)])
            pygame.draw.line(surface, (*c["rock_high"], a),
                             (px - w * 0.6, py - up + 2),
                             (px - w * 0.7, py - 2), 1)
            # ujung bersinar energi kubur
            pygame.draw.rect(surface, (*c["grave_bright"], a),
                             (int(px - 2), int(py - up), 4, 3))

    # ==================================================================
    # W — ROLLING BOULDER: batu bergulir + jalur debu
    # ==================================================================
    def _upd_w(self, t, dt, particles):
        c = _P
        ph = skill_phase(t)
        if ph in ("CAST", "CHARGE") and self._once("w_cast"):
            particles.burst(
                self.x, self.y + 20, 12, speed=(50, 170), life=(0.25, 0.5),
                size=(2.0, 4.0),
                colors=(c["rock_mid"], c["rock_light"]),
                shape="rubble", drag=1.8, gravity=240.0,
                rotation_speed=(-6, 6))
        if ph == "RELEASE" and self._once("w_rel"):
            if _feel is not None:
                _feel.hit_stop(0.05)
                if shake_allowed():
                    _feel.shake(6.0, 0.26)
        # AREA: debu sepanjang lintasan boulder
        if ph in ("RELEASE", "AREA", "IMPACT"):
            tx, ty = self._target_xy()
            u = min(1.0, max(0.0, (t - 0.34) / 0.4))
            px = self.x + (tx - self.x) * u
            py = self.y + (ty - self.y) * u
            if random.random() < dt * 40.0:
                particles.spawn(
                    px + random.uniform(-12, 12),
                    py + random.uniform(10, 26),
                    random.uniform(-50, 50), random.uniform(-40, -10),
                    random.uniform(0.25, 0.55), random.uniform(2.0, 4.0),
                    random.choice((c["rock_mid"], c["grave_dark"])),
                    shape="dust", drag=1.8, layer="back")

    def _gnd_w(self, surface, t):
        """Tanah: jalur bekas gilasan boulder."""
        c = _P
        ph = skill_phase(t)
        if ph in ("CAST", "CHARGE"):
            return
        tx, ty = self._target_xy()
        u = min(1.0, max(0.0, (t - 0.34) / 0.4))
        fade = 1.0 if t < 0.80 else max(0.0, 1.0 - (t - 0.80) / 0.20)
        gy = self.y + 34 * self.scale
        gty = ty + 34 * self.scale
        # pita jalur yang menggelap
        taper_lane(surface, self.x, gy,
                   self.x + (tx - self.x) * u, gy + (gty - gy) * u,
                   9.0 * self.scale, 7.0 * self.scale,
                   c["grave_darkest"], int(150 * fade))
        # retakan kecil di sepanjang jalur
        n = 5
        for i in range(1, n + 1):
            v = i / n
            if v > u:
                break
            cx = self.x + (tx - self.x) * v
            cy = gy + (gty - gy) * v
            ground_crack(surface, cx, cy, 0.4 + i, 16.0 * self.scale,
                         c["grave_dark"], int(170 * fade), seed=i * 13)

    def _frn_w(self, surface, t):
        """Depan: boulder bergulir (visual fallback bila proyektil
        modular tidak dipakai, mis. lane hero)."""
        c = _P
        ph = skill_phase(t)
        if ph in ("CAST", "CHARGE"):
            # batu terangkat di atas kepala
            k = t / 0.34
            rr = int((7 + 8 * k) * self.scale)
            _blit_faded(surface, rock_decal(rr, 255, seed=2),
                        self.x, self.y - 34 - 8 * k, 255)
            return
        u = min(1.0, max(0.0, (t - 0.34) / 0.4))
        if u >= 1.0:
            return
        tx, ty = self._target_xy()
        px = self.x + (tx - self.x) * u
        py = self.y + (ty - self.y) * u
        roll = u * 14.0
        rock = rock_decal(int(15 * self.scale), 255, seed=0)
        rot = pygame.transform.rotate(rock, -math.degrees(roll))
        surface.blit(rot, (int(px) - rot.get_width() // 2,
                           int(py) - rot.get_height() // 2))
        if glow_allowed():
            _blit_faded(surface, glow_surface(20, c["grave_dark"], 0.6),
                        px, py, 130, additive=True)

    # ==================================================================
    # E — GEOMAGNETIC GRIP: pasak tulang mencengkeram target
    # ==================================================================
    def _upd_e(self, t, dt, particles):
        c = _P
        ph = skill_phase(t)
        if ph == "RELEASE" and self._once("e_slam"):
            gy = self.y + 34 * self.scale
            particles.burst(
                self.x, gy, 16, speed=(90, 280), life=(0.25, 0.55),
                size=(1.8, 3.8),
                colors=(c["bone_light"], c["rock_light"]),
                shape="rubble", drag=1.8, gravity=320.0,
                rotation_speed=(-9, 9))
            if _feel is not None:
                _feel.hit_stop(0.05)
                if shake_allowed():
                    _feel.shake(6.0, 0.24)
        # AREA: energi merambat dari pasak ke target
        if ph in ("AREA", "IMPACT"):
            tx, ty = self._target_xy()
            if random.random() < dt * 30.0:
                particles.stream_toward(
                    self.x, self.y + 20, tx, ty, 1,
                    speed=(150, 260), life=(0.25, 0.5), size=(1.5, 3.0),
                    colors=(c["grave_light"], c["grave_bright"]),
                    shape="wisp")

    def _gnd_e(self, surface, t):
        c = _P
        ph = skill_phase(t)
        gy = self.y + 34 * self.scale
        pulse = 0.5 + 0.5 * math.sin(self.elapsed * 8.0)
        rr = int(WORLD_RADIUS["e"] * self.scale * (0.55 + 0.15 * pulse))
        a = int(170 * (1.0 - t * 0.5))
        _blit_faded(surface,
                    ellipse_ring_surface(rr, max(3, rr // 3), 3,
                                         c["grave_light"], a),
                    self.x, gy, a)
        # retakan mengarah ke target
        if ph in ("AREA", "IMPACT", "AFTER"):
            tx, _ty = self._target_xy()
            ang = 0.0 if tx >= self.x else math.pi
            ground_crack(surface, self.x, gy, ang, 60.0 * self.scale,
                         c["grave_dark"], int(190 * (1.0 - t)), seed=71)

    def _frn_e(self, surface, t):
        """Depan: 5 pasak tulang mencuat + rantai energi ke target."""
        c = _P
        ph = skill_phase(t)
        if ph == "CAST":
            return
        fade = 1.0 if t < 0.84 else max(0.0, 1.0 - (t - 0.84) / 0.16)
        gy = self.y + 34 * self.scale
        if self._totems:
            for i, (dx, dy, size) in enumerate(self._totems):
                # pasak naik berurutan (stagger)
                k = min(1.0, max(0.0, (t - 0.16 - i * 0.05) / 0.22))
                if k <= 0.0:
                    continue
                px = self.x + dx * self.scale
                py = gy + dy * self.scale
                spr = totem_sprite(int(size * self.scale),
                                   int(235 * fade))
                # muncul dari tanah: geser ke atas seiring k
                oy = (1.0 - k) * spr.get_height() * 0.7
                surface.blit(spr, (int(px) - spr.get_width() // 2,
                                   int(py - spr.get_height() + oy)))
        # rantai energi dari Gravefang ke target (cengkeraman)
        if ph in ("AREA", "IMPACT"):
            tx, ty = self._target_xy()
            sx, sy = self.x, self.y - 12
            n = 8
            prev = None
            for i in range(n + 1):
                u = i / n
                wob = math.sin(u * 7.0 - self.elapsed * 12.0) * 7.0 * self.scale
                px = sx + (tx - sx) * u
                py = sy + (ty - sy) * u + wob
                if prev is not None:
                    pygame.draw.line(surface,
                                     (*c["grave_mid"], int(215 * fade)),
                                     (int(prev[0]), int(prev[1])),
                                     (int(px), int(py)), 3)
                    pygame.draw.line(surface,
                                     (*c["grave_hot"], int(165 * fade)),
                                     (int(prev[0]), int(prev[1])),
                                     (int(px), int(py)), 1)
                prev = (px, py)

    # ==================================================================
    # R — MAGNETIZE: tarikan medan + orbit batu + nova besar
    # ==================================================================
    def _upd_r(self, t, dt, particles):
        c = _P
        ph = skill_phase(t)
        if ph in ("CAST", "CHARGE") and self._once("r_cast"):
            particles.burst(
                self.x, self.y - 24, 16, speed=(50, 180), life=(0.3, 0.6),
                size=(1.8, 3.8),
                colors=(c["grave_light"], c["grave_bright"]),
                shape="wisp", drag=2.0, additive=True)
            if _feel is not None and shake_allowed():
                _feel.shake(4.5, 0.22)
        if ph == "RELEASE" and self._once("r_rel"):
            particles.burst(
                self.x, self.y, 26, speed=(140, 420), life=(0.3, 0.7),
                size=(2.0, 4.5),
                colors=(c["rock_light"], c["bone_light"], c["grave_bright"]),
                shape="rubble", drag=1.6, gravity=280.0,
                rotation_speed=(-11, 11))
            if _feel is not None:
                _feel.hit_stop(0.075)
                if shake_allowed():
                    _feel.shake(10.0, 0.34)
        # AREA: puing tersedot MASUK ke Gravefang (arah penting)
        if ph in ("RELEASE", "AREA", "IMPACT"):
            if random.random() < dt * 52.0:
                ang = random.uniform(0.0, math.tau)
                rr = WORLD_RADIUS["r"] * self.scale
                particles.stream_toward(
                    self.x + math.cos(ang) * rr,
                    self.y + math.sin(ang) * rr * 0.45,
                    self.x, self.y - 10, 1,
                    speed=(220, 380), life=(0.3, 0.55), size=(1.8, 3.5),
                    colors=(c["rock_light"], c["bone_mid"],
                            c["grave_bright"]),
                    shape="rubble")

    def _gnd_r(self, surface, t):
        c = _P
        gy = self.y + 34 * self.scale
        pulse = 0.5 + 0.5 * math.sin(self.elapsed * 7.0)
        rr = int(WORLD_RADIUS["r"] * self.scale * (0.5 + 0.2 * pulse))
        a = int(160 * (1.0 - t * 0.5))
        _blit_faded(surface,
                    ellipse_ring_surface(rr, max(3, rr // 3), 3,
                                         c["grave_light"], a),
                    self.x, gy, a)
        # cincin tarikan kedua (lebih rapat, berlawanan fase)
        rr2 = int(WORLD_RADIUS["r"] * self.scale * (0.68 - 0.18 * pulse))
        _blit_faded(surface,
                    ellipse_ring_surface(rr2, max(2, rr2 // 3), 2,
                                         c["grave_bright"], a),
                    self.x, gy, int(a * 0.8))

    def _frn_r(self, surface, t):
        """Depan: batu mengorbit + aura cincin denyut (siluet tetap
        terbaca — TIDAK memakai bola glow pekat yang menutupi rig)."""
        c = _P
        ph = skill_phase(t)
        if ph == "CAST":
            return
        fade = 1.0 if t < 0.86 else max(0.0, 1.0 - (t - 0.86) / 0.14)
        cy = self.y - 12
        # batu mengorbit Gravefang (3 buah, radius menyusut)
        shrink = 1.0 - min(0.55, max(0.0, (t - 0.34)) * 0.9)
        for i in range(3):
            a = self.elapsed * 3.4 + i * math.tau / 3
            orx = 46.0 * self.scale * shrink
            ory = 17.0 * self.scale * shrink
            px = self.x + math.cos(a) * orx
            py = cy + math.sin(a) * ory
            sz = int((7 + 2 * math.sin(a * 2.0)) * self.scale)
            _blit_faded(surface, rock_decal(max(4, sz), 255, seed=i),
                        px, py, 240 * fade)
        # cincin denyut tipis (bukan bola pekat)
        if glow_allowed():
            for k in (0.0, 0.5):
                u = ((self.elapsed * 1.5 + k) % 1.0)
                rr = int((12.0 + 20.0 * u) * self.scale)
                aa = int(150 * fade * (1.0 - u))
                if aa > 4:
                    _blit_faded(surface,
                                ring_surface(rr, 2, c["grave_light"], 255,
                                             teeth=6),
                                self.x, cy, aa, additive=True)


def _skillfx_postinit(fx):
    """Geometri deterministik per skill (dibuat sekali saat cast)."""
    rng = random.Random(int(fx.x * 7 + fx.y * 13))
    if fx.skill == "q":
        cracks = []
        for i in range(7):
            ang = i * math.tau / 7 + rng.uniform(-0.18, 0.18)
            cracks.append((ang, rng.uniform(48.0, 76.0),
                           rng.randint(0, 9999)))
        fx._cracks = cracks
        rocks = []
        for i in range(5):
            ang = i * math.tau / 5 + rng.uniform(-0.25, 0.25)
            rocks.append((ang, rng.uniform(34.0, 62.0),
                          rng.uniform(16.0, 28.0), rng.randint(0, 9999)))
        fx._rocks = rocks
    elif fx.skill == "e":
        totems = []
        for i in range(5):
            ang = math.pi * (0.15 + 0.7 * (i / 4.0))
            dist = rng.uniform(30.0, 52.0)
            totems.append((math.cos(ang) * dist * fx.facing,
                           math.sin(ang) * dist * 0.34,
                           rng.uniform(7.0, 10.0)))
        fx._totems = totems


# ============================================================================
# 9.  DIRECTOR  — satu per unit; menjahit semua sistem jadi satu lapisan
# ============================================================================

class GravefangFXDirector:
    """Pemilik seluruh state FX hidup untuk SATU unit Gravefang."""

    def __init__(self, unit):
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
        self.attack_kind = "shard"
        self.swing_done = False
        self.shot_done = False
        self._pending_impact = None

        # pelacakan skill
        self.skill_key = None
        self.skill_prev = None
        self._skill_total = 1
        self._boulder_done = False

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
        st = getattr(boss, "_gf_state", None)
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
        self.attack_kind = getattr(boss, "_gf_attack_kind",
                                   self.attack_kind) or "shard"
        ap = float(getattr(boss, "_gf_attack_progress", 0.0) or 0.0)
        active = bool(getattr(boss, "_gf_attack_active", False))
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
        skill = getattr(boss, "_gf_skill", None)
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

            # ── DEATH: ledakan tulang sekali ──────────────────────────
            alive = bool(getattr(u, "alive", True))
            if self._was_alive and not alive:
                self.on_death(x, y)
            self._was_alive = alive

        # ── SERANGAN: event per fase ──────────────────────────────────
        # Baca state TERBARU langsung dari unit (bukan salinan sync) —
        # hook gameplay (notify_*) bisa jalan sebelum frame gambar
        # pertama, jadi tick() harus tetap melihat progress baru.
        if u is not None:
            kind_now = getattr(u, "_gf_attack_kind", None)
            if kind_now:
                self.attack_kind = kind_now
            if getattr(u, "_gf_attack_active", False):
                self.attack_progress = max(0.0, min(1.0, float(
                    getattr(u, "_gf_attack_progress", 0.0) or 0.0)))
        active = u is not None and bool(getattr(u, "_gf_attack_active",
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
            if kind == "shard" and not self.shot_done and ap >= ATK_RELEASE:
                self.shot_done = True
                if getattr(u, "_render_scale", None) is None:
                    self._spawn_attack_shard(tp)
            # impact hantaman pada frame gada menyentuh
            if kind == "slam" and not self.swing_done and ap >= ATK_IMPACT:
                self.swing_done = True
                self._on_slam_impact_frame(x, y, tp)

            # trail: sampel kepala gada selama jendela cepat
            _pivot, tip = club_points(u, x, y)
            fast = 0.26 <= ap <= 0.66 and kind == "slam"
            self.trail.push(tip.x, tip.y, 1.0 if fast else
                            (0.6 if kind == "attack" else 0.0))
        else:
            self.trail.push(0, 0, 0.0)

        # ── AFTERIMAGE gada saat spin skill E ────────────────────────
        if u is not None:
            action, _ph, ap = pose_of(u)
            if action == "cast_e" and ap < 0.55:
                self.push_afterimage()
            # skill W: lepaskan Rolling Boulder pada fase RELEASE
            # (ambang 0.42 sama dengan fallback canvas renderer).
            if action == "cast_w" and ap >= 0.42 and not self._boulder_done:
                self._boulder_done = True
                if getattr(u, "_render_scale", None) is None:
                    self._spawn_boulder()
            elif action != "cast_w":
                self._boulder_done = False

        # ── AMBIENT: bara kubur & debu (rate-limited) ────────────────
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
        self.afterimages = [ai for ai in self.afterimages if ai["life"] > 0.0]
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

    def _spawn_attack_shard(self, tp):
        u = self.unit
        _pivot, tip = club_points(u, self.x, self.y)
        if tp is None:
            f = 1 if (getattr(u, "direction", 1) or 1) >= 0 else -1
            aim = (self.x + f * 140.0, self.y - 10.0)
            tgt = None
        else:
            aim, tgt = (tp[0], tp[1]), tp[2]
        self.projectiles.spawn_shard(
            tip.x, tip.y, aim[0], aim[1], speed=SHARD_SPEED, damage=0.0,
            target=tgt, ground=ground_dy(u),
            on_impact=lambda b: self._on_proj_hit(b))
        self.particles.burst(
            tip.x, tip.y, 7, speed=(90, 220), life=(0.12, 0.3),
            size=(1.5, 3.0),
            colors=(_P["bone_light"], _P["grave_bright"]),
            shape="shard", drag=2.6, rotation_speed=(-8, 8))

    def _spawn_boulder(self):
        """Skill W: Rolling Boulder melesat ke target."""
        u = self.unit
        tp = self._target_point()
        gy = self.y + 20.0
        if tp is None:
            f = 1 if (getattr(u, "direction", 1) or 1) >= 0 else -1
            aim, tgt = (self.x + f * 240.0, gy), None
        else:
            aim, tgt = (tp[0], tp[1] + 14.0), tp[2]
        f = 1 if (getattr(u, "direction", 1) or 1) >= 0 else -1
        self.projectiles.spawn_boulder(
            self.x + f * 26.0, gy, aim[0], aim[1], speed=BOULDER_SPEED,
            damage=0.0, target=tgt, ground=ground_dy(u),
            on_impact=lambda b: self._on_proj_hit(b))
        self.particles.burst(
            self.x + f * 26.0, gy, 12, speed=(70, 230), life=(0.2, 0.45),
            size=(2.0, 4.0),
            colors=(_P["rock_light"], _P["rock_mid"], _P["grave_dark"]),
            shape="rubble", drag=2.0, gravity=280.0,
            rotation_speed=(-9, 9))
        if _feel is not None and shake_allowed():
            _feel.shake(4.5, 0.2)

    def _on_proj_hit(self, proj):
        self.projectiles.on_impact(proj)
        self._release_pending()

    def _on_slam_impact_frame(self, x, y, tp):
        """Frame gada menyentuh: full impact kalau target di busur."""
        u = self.unit
        _pivot, tip = club_points(u, x, y)
        f = 1 if (getattr(u, "direction", 1) or 1) >= 0 else -1
        if tp is not None:
            tx, ty = tp[0], tp[1]
            dist = math.hypot(tx - x, ty - y)
            front = (tx - x) * f
            if dist <= MELEE_REACH + 20.0 and front > -18.0:
                self.on_impact(tx, ty,
                               math.atan2(ty - (y - 10), tx - x),
                               1.25, False, kind="club")
        # debu tanah walau meleset (feel hantaman berat)
        self.particles.burst(
            tip.x, tip.y + 18, 8, speed=(40, 140), life=(0.18, 0.4),
            size=(1.5, 3.2), colors=(_P["rock_dark"], _P["grave_dark"]),
            shape="dust", drag=2.0, layer="back")
        self._release_pending()

    def _release_pending(self):
        if self._pending_impact is not None:
            tx, ty, ang, power, crit, kind = self._pending_impact
            self.on_impact(tx, ty, ang, power, crit, kind=kind)
            self._pending_impact = None

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="grave"):
        """Impact penuh + partikel + game feel."""
        self.impacts.append(ImpactFX(x, y, kind=kind, angle=angle,
                                     power=power, crit=crit))
        while len(self.impacts) > MAX_IMPACTS:
            self.impacts.pop(0)
        c = _P
        if kind == "club":
            self.particles.burst(
                x, y, 16, speed=(110, 360), life=(0.2, 0.5),
                size=(1.8, 4.0),
                colors=(c["rock_light"], c["bone_light"],
                        c["grave_bright"]),
                shape="rubble", drag=2.0, gravity=300.0,
                rotation_speed=(-10, 10))
            self.particles.burst(
                x, y, 7, speed=(50, 170), life=(0.35, 0.7),
                size=(1.5, 2.5), colors=(c["bone_mid"], c["bone_light"]),
                shape="bone", gravity=320.0, drag=0.7,
                rotation_speed=(-9, 9))
            if _feel is not None:
                _feel.hit_stop(0.062)
                if shake_allowed():
                    _feel.shake(7.5, 0.26)
        else:
            self.particles.burst(
                x, y, 11, speed=(60, 240), life=(0.18, 0.4),
                size=(1.5, 3.0),
                colors=(c["bone_light"], c["grave_bright"]),
                shape="shard", drag=2.6, rotation_speed=(-7, 7))
            if _feel is not None:
                _feel.hit_stop(0.038)
                if shake_allowed():
                    _feel.shake(4.0, 0.18)

    def on_hurt(self, x, y):
        """Kena pukul: serpihan tulang + recoil kecil."""
        self.particles.burst(
            x, y - 16, 9, speed=(50, 190), life=(0.15, 0.35),
            size=(1.5, 3.0),
            colors=(_P["bone_light"], _P["hide_light"]),
            shape="bone", drag=2.2, gravity=200.0,
            rotation_speed=(-8, 8))

    def on_death(self, x, y):
        """Mati: kerangka berhamburan (FX global via bus)."""
        c = _P
        self.particles.burst(
            x, y - 16, 30, speed=(60, 330), life=(0.4, 0.9),
            size=(1.8, 4.2),
            colors=(c["bone_light"], c["bone_mid"], c["rock_light"],
                    c["grave_bright"]),
            shape="bone", drag=1.4, gravity=280.0,
            rotation_speed=(-11, 11))
        self.particles.burst(
            x, y - 16, 12, speed=(40, 150), life=(0.5, 1.0),
            size=(2.5, 5.0), colors=(c["grave_dark"], c["rock_dark"]),
            shape="dust", drag=1.8, layer="back")
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
        _pivot, tip = club_points(u, self.x, self.y)
        self.afterimages.append({"x": tip.x, "y": tip.y, "life": 0.16,
                                 "max": 0.16})
        while len(self.afterimages) > MAX_AFTERIMAGES:
            self.afterimages.pop(0)

    def _ambient(self, dt):
        """Bara kubur pelan di sekitar badan (rate-limited + budget)."""
        if not self.have_pos or particle_budget() <= 0.0:
            return
        self.ember_acc += dt * 9.0
        while self.ember_acc >= 1.0:
            self.ember_acc -= 1.0
            self.particles.spawn(
                self.x + random.uniform(-22, 22),
                self.y + random.uniform(8, 38),
                random.uniform(-4, 4), random.uniform(-26, -10),
                random.uniform(0.5, 1.0), random.uniform(1.5, 2.5),
                random.choice((_P["grave_mid"], _P["grave_dark"])),
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
        # afterimage kepala gada (di bawah trail utama)
        for ai in self.afterimages:
            k = ai["life"] / ai["max"]
            _blit_faded(surface,
                        ring_surface(9, 2, _P["grave_mid"], 180, teeth=5),
                        ai["x"], ai["y"], 110 * k)
        # trail ayunan
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
# 10. REGISTRI DIRECTOR  (pola identik heroes/nyxara_fx.py)
# ============================================================================

_DIRECTORS = []
MAX_DIRECTORS = 12


def director_for(unit):
    """Ambil (atau buat) director FX untuk satu unit Gravefang."""
    _sync_palette()
    d = getattr(unit, "_gravefang_fx", None)
    if d is None:
        d = GravefangFXDirector(unit)
        try:
            unit._gravefang_fx = d
        except Exception:                        # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > MAX_DIRECTORS:
            _release(_DIRECTORS.pop(0))
    return d


def _release(director):
    try:
        if director.unit is not None:
            director.unit._gravefang_fx = None
            director.unit._gf_live_fx = False
    except Exception:                            # pragma: no cover
        pass
    director.reset()


def attach(unit):
    """Pasang lapisan hidup pada unit (dipanggil pipeline render)."""
    if not GRAVEFANG_FX_ENABLED or unit is None:
        return False
    try:
        director_for(unit)
    except Exception:                            # pragma: no cover
        return False
    try:
        unit._gf_live_fx = True
    except Exception:                            # pragma: no cover
        return False
    return True


def owns(unit):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not GRAVEFANG_FX_ENABLED or unit is None:
        return False
    if not getattr(unit, "_gf_live_fx", False):
        return False
    d = getattr(unit, "_gravefang_fx", None)
    return d is not None and d in _DIRECTORS


def recently_drawn(unit, max_age=0.35):
    """True kalau lapisan hidup unit ini BENAR-BENAR digambar belakangan."""
    d = getattr(unit, "_gravefang_fx", None)
    if d is None:
        return False
    return bool(d.have_pos) and d.draw_age <= float(max_age)


def tick(dt=None):
    """Majukan waktu FX satu frame nyata; aman dipanggil berkali-kali."""
    if not GRAVEFANG_FX_ENABLED:
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
    """Bersihkan seluruh state FX Gravefang (ganti level / keluar match)."""
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()
    clear_cache()


def total_particles():
    """Jumlah partikel Gravefang yang hidup (HUD performa + tes)."""
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
    if not GRAVEFANG_FX_ENABLED:
        return
    if not attach(unit):
        return
    tick()
    d = getattr(unit, "_gravefang_fx", None)
    if d is not None:
        d.sync(unit, x, y)
        d.draw_ground(surface)


def draw_live_layer(surface, unit, x, y):
    """Post-pass: digambar SESUDAH sprite di-blit (trail, proj, impact)."""
    if not GRAVEFANG_FX_ENABLED:
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
    """Gada Gravefang mendarat di target (basic attack slam).

    Kalau ayunan masih di awal cycle (damage hook lebih dulu dari frame
    visual benturan), impact DITAHAN sampai frame gada menyentuh —
    jadi flash & hit-stop sinkron dengan kepala gada.
    """
    if not GRAVEFANG_FX_ENABLED or unit is None or target is None:
        return
    try:
        power = 0.8 + min(1.5, float(damage) / 70.0)
    except (TypeError, ValueError):
        power = 1.0
    tx = float(getattr(target, "x", getattr(unit, "x", 0.0)))
    ty = float(getattr(target, "y", getattr(unit, "y", 0.0))) - 6.0
    ang = math.atan2(ty - float(getattr(unit, "y", 0.0)),
                     tx - float(getattr(unit, "x", 0.0)))
    d = director_for(unit)
    active = bool(getattr(unit, "_gf_attack_active", False))
    ap = float(getattr(unit, "_gf_attack_progress", 0.0) or 0.0)
    kind = getattr(unit, "_gf_attack_kind", "slam") or "slam"
    if active and kind == "slam" and ap < ATK_IMPACT:
        d._pending_impact = (tx, ty, ang, power, bool(crit), "club")
        return
    d.on_impact(tx, ty, ang, power, bool(crit), kind="club")
    d._pending_impact = None


def notify_projectile_impact(unit, x, y, angle=0.0, damage=0, crit=False,
                             kind="grave"):
    """Pecahan tulang mengenai target (basic attack jarak jauh)."""
    if not GRAVEFANG_FX_ENABLED or unit is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    d = director_for(unit)
    active = bool(getattr(unit, "_gf_attack_active", False))
    ap = float(getattr(unit, "_gf_attack_progress", 0.0) or 0.0)
    atk_kind = getattr(unit, "_gf_attack_kind", "shard") or "shard"
    hero_lane = getattr(unit, "_render_scale", None) is not None
    if not hero_lane and active and atk_kind == "shard" \
            and ap < ATK_RELEASE + 0.1:
        # jalur BOSS: damage instan, impact visual ditahan sampai
        # pecahan prosedural mendarat.
        d._pending_impact = (float(x), float(y), float(angle), power,
                             bool(crit), kind)
        return
    if hero_lane and active and atk_kind == "slam":
        d._pending_impact = (float(x), float(y), float(angle), power,
                             bool(crit), "club")
        return
    d.on_impact(float(x), float(y), float(angle), power, bool(crit),
                kind=kind)
    d._pending_impact = None


def notify_skill_cast(unit, skill, x=None, y=None):
    """Skill dilepaskan (Q/W/E/R) — buat SkillFX lifecycle penuh."""
    if not GRAVEFANG_FX_ENABLED or unit is None:
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
    if not GRAVEFANG_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if not any(fx.skill == skill for fx in d.skills):
        d.on_cast(float(getattr(unit, "x", x)),
                  float(getattr(unit, "y", y)), skill)
    d.on_impact(float(x), float(y), angle=0.0,
                power=1.3 if skill in ("q", "r") else 0.9,
                crit=False, kind="skill")
    if radius:
        c = _P
        d.particles.burst(
            float(x), float(y), 16, speed=(80, 280), life=(0.2, 0.55),
            size=(1.8, 4.0),
            colors=(c["rock_light"], c["bone_light"], c["grave_bright"]),
            shape="rubble", drag=2.0, gravity=300.0,
            rotation_speed=(-9, 9))


def notify_death(unit):
    """Unit mati — dipanggil hook base_boss.take_damage saat hp <= 0."""
    if not GRAVEFANG_FX_ENABLED or unit is None:
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
    d = getattr(unit, "_gravefang_fx", None)
    if d is None:
        return
    sc = body_scale(unit)
    # attack range (melee) & hurtbox
    pygame.draw.circle(surface, (255, 200, 60), (int(x), int(y)),
                       int(MELEE_REACH * sc), 1)
    hurt = pygame.Rect(int(x - 25 * sc), int(y - 52 * sc),
                       int(50 * sc), int(74 * sc))
    pygame.draw.rect(surface, (80, 160, 255), hurt, 1)
    # hitbox hantaman saat jendela aktif
    if bool(getattr(unit, "_gf_hit_active", False)):
        f = 1 if (getattr(unit, "direction", 1) or 1) >= 0 else -1
        reach = int(MELEE_REACH * 0.95 * sc)
        top = int(y - 40 * sc)
        h = int(80 * sc)
        left = int(x) if f > 0 else int(x) - reach
        pygame.draw.rect(surface, (255, 80, 80),
                         (left, top, max(8, reach), max(10, h)), 1)
    # garis pivot->kepala gada
    pv, tip = club_points(unit, x, y)
    pygame.draw.line(surface, (150, 220, 55),
                     (int(pv.x), int(pv.y)), (int(tip.x), int(tip.y)), 1)
    pygame.draw.circle(surface, (150, 220, 55), (int(tip.x), int(tip.y)), 3, 1)
    # teks state
    s = d.stats()
    lines = [
        f"GRAVEFANG[{CHARACTER_NAME}] state={s['state']}"
        f"<{s['state_prev']}> t={s['state_time']:.2f}",
        f"pose={pose_of(unit)[0]} kind={s['attack_kind']} "
        f"phase={s['attack_phase']} ap={s['attack_progress']:.2f}",
        f"skill={s['skill']} frame={s['anim_frame']}",
        f"partikel={s['particles']} proj={s['projectiles']} "
        f"impact={s['impacts']} fps={s['fps']:.0f}",
    ]
    font = _dbg_font()
    yy = int(y - 104 * sc)
    for ln in lines:
        img = font.render(ln, True, (190, 245, 100))
        surface.blit(img, (int(x - 105), yy))
        yy += 13
