# ============================================================================
# heroes/gorath_fx.py
# ----------------------------------------------------------------------------
# GORATH v3 — COMBAT FX & GAME FEEL (lapisan hidup 100% prosedural)
#
# Rewrite penuh sistem tempur GORATH (mini boss level 2, sekaligus hero yang
# bisa di-unlock): ayunan berbasis busur + trail sabit, proyektil darah
# modular, particle system reusable, skill FX 4 skill dengan lifecycle
# CAST -> CHARGE -> RELEASE -> AREA -> IMPACT -> AFTER -> FADE, impact FX,
# hit-stop 0.03-0.08 s, dan screen shake — semua lewat `pygame.Surface`,
# `pygame.draw`, `pygame.transform`, `Rect`, dan `Vector2`. Tidak ada PNG /
# sprite-sheet / asset eksternal.
#
# Lapisan ini digambar LANGSUNG ke layar pada skala 1:1 DI LUAR sprite cache
# (lihat heroes/__init__.py `_LIVE_FX_HEROES` dan `_NS_gorath.draw_gorath`),
# jadi trail/partikel/proyektil tetap bergerak 60 fps sejati walau pose
# sprite sedang dipakai ulang oleh cache. Untuk geometri badan & disiplin
# pixel-art renderer, lihat docs/GORATH_V2_RENDERER.md; sistem tempurnya
# dijelaskan di docs/GORATH_V3_COMBAT_FX.md.
#
# Kontrak modul (dipakai renderer & pipeline):
#   attach / owns / tick / reset_all / total_particles / projectiles_for /
#   draw_ground_layer / draw_live_layer / notify_melee_impact /
#   notify_projectile_impact / notify_skill_impact / notify_skill_cast /
#   notify_skill_start / notify_skill_end / draw_blood_bolt / stats /
#   DEBUG_CHARACTER
# ============================================================================

import math
import random

import pygame

try:                                 # bus game-feel bersama (hit-stop/shake)
    from heroes import combat_feel as _feel
except Exception:                    # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual: hitbox, hurtbox, jangkauan, state animasi, frame, FPS,
#: jumlah partikel, state skill, timer serangan.
DEBUG_CHARACTER = False

#: Master switch lapisan hidup Gorath (renderer kembali ke jalur canvas).
GORATH_FX_ENABLED = True

#: Anggaran partikel per unit (cap dihormati, tidak pernah grow tak hingga).
MAX_PARTICLES = 170
#: Cap proyektil hidup per unit.
MAX_PROJECTILES = 16
#: Panjang histori trail ayunan.
TRAIL_SAMPLES = 14
#: Cap effect impact serentak.
MAX_IMPACTS = 8
#: Cap skill FX serentak.
MAX_SKILLS = 4

#: Langkah simulasi game (frame tetap 1/60 s).
FIXED_DT = 1.0 / 60.0

#: Kecepatan bolt darah (px/detik).
BOLT_SPEED = 640.0

#: Radius skill dalam PX DUNIA (sama dengan gameplay base_boss.py dan
#: telegraph renderer — jangan diubah tanpa menyentuh keduanya).
WORLD_RADIUS = {"q": 90.0, "w": 150.0, "e": 85.0, "r": 190.0}

#: Total durasi lapisan hidup per skill (detik) ~ durasi engine (frame/60).
SKILL_TOTAL = {"q": 1.50, "w": 1.00, "e": 0.60, "r": 1.50}

#: Durasi engine skill (frame) — disinkronkan dari renderer `_NS_gorath`.
SKILL_DUR = {"q": 90, "w": 60, "e": 35, "r": 90}

#: Batas fase ayunan — harus sama dengan `_NS_gorath.ATTACK_PHASES`.
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.16),
    ("WINDUP",       0.16, 0.30),
    ("SWING",        0.30, 0.46),
    ("IMPACT",       0.46, 0.60),
    ("FOLLOW",       0.60, 0.80),
    ("RECOVERY",     0.80, 1.00),
)


# ============================================================================
# 1.  PALETTE  (darah / demon flesh / tulang / baja — sinkron dari renderer)
# ============================================================================

GORATH_PALETTE = {
    # darah — bahasa visual utama Gorath
    "blood_darkest": (24, 3, 6),
    "blood_dark":    (72, 6, 12),
    "blood_mid":     (136, 15, 22),
    "blood_bright":  (196, 26, 32),
    "blood_hot":     (236, 56, 50),
    "blood_glow":    (255, 102, 86),
    "blood_light":   (255, 166, 142),
    "blood_seam":    (255, 214, 190),

    # kulit demon (serpihan, guratan)
    "skin_dark":     (76, 22, 28),
    "skin_mid":      (126, 46, 40),
    "skin_light":    (176, 80, 58),
    "skin_high":     (216, 132, 92),

    # logam kukri
    "metal_dark":    (48, 43, 52),
    "metal_mid":     (96, 89, 99),
    "metal_light":   (156, 149, 160),
    "metal_shine":   (218, 213, 222),

    # tulang / fragment
    "bone_dark":     (114, 100, 80),
    "bone_mid":      (176, 161, 132),
    "bone_light":    (221, 211, 182),

    # FX tambahan lapisan hidup
    "fx_dark":       (30, 6, 10),
    "fx_mid":        (120, 20, 26),
    "fx_bright":     (214, 40, 40),
    "fx_hot":        (255, 110, 90),
    "fx_light":      (255, 176, 148),
    "fx_white":      (255, 236, 218),
    "smoke":         (38, 16, 26),
    "dust":          (66, 40, 30),
    "ember":         (255, 138, 96),
    "white":         (255, 248, 240),
}

P = GORATH_PALETTE

_PALETTE_SYNC = {
    "blood_darkest": "blood_darkest",
    "blood_dark":    "blood_dark",
    "blood_mid":     "blood_mid",
    "blood_bright":  "blood_bright",
    "blood_hot":     "blood_hot",
    "blood_glow":    "blood_glow",
    "blood_light":   "blood_light",
    "blood_seam":    "blood_seam",
    "skin_dark":     "skin_dark",
    "skin_mid":      "skin_mid",
    "skin_light":    "skin_light",
    "skin_high":     "skin_high",
    "metal_dark":    "metal_dark",
    "metal_mid":     "metal_mid",
    "metal_light":   "metal_light",
    "metal_shine":   "metal_shine",
    "bone_dark":     "bone_dark",
    "bone_mid":      "bone_mid",
    "bone_light":    "bone_light",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Tarik nilai palet dari renderer supaya FX dan badan satu bahasa."""
    global _PALETTE_SYNCED
    if _PALETTE_SYNCED:
        return
    G = _renderer()
    if G is not None:
        try:
            src = getattr(G, "PALETTE", {}) or {}
            for k, sk in _PALETTE_SYNC.items():
                if sk in src:
                    GORATH_PALETTE[k] = tuple(src[sk][:3])
        except Exception:                      # pragma: no cover
            pass
    _PALETTE_SYNCED = True


# ============================================================================
# 2.  JEMBATAN RENDERER  (badan & anchor efek tidak pernah beda frame)
# ============================================================================

_RENDERER = None          # None = belum dicari, False = tidak ada


def _renderer():
    """``_NS_gorath`` atau None. Diimpor malas: modul boss besar."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level2 import _NS_gorath as G
            _RENDERER = G
        except Exception:                      # pragma: no cover
            _RENDERER = False
    return _RENDERER or None


def _fallback_pose(boss):
    """(action, phase, ap) tanpa renderer: baca atribut yang sudah ada."""
    skill = getattr(boss, "active_skill", None)
    action = getattr(boss, "_gor_pose_action", None)
    if action is None:
        action = ("attack" if getattr(boss, "_gor_attack_active", False)
                  else "idle")
    phase = float(getattr(boss, "pulse", 0.0) or 0.0)
    ap = 0.0
    if action == "attack":
        raw = float(getattr(boss, "_gor_attack_progress", 0.0) or 0.0)
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
    k = getattr(G, "SCALE", 0.62) if G is not None else 0.62
    return float(k) * render_scale(boss)


def screen_point(boss, x, y, local, action=None, phase=None, ap=None):
    """Ruang lokal rig -> piksel layar.

    Sama persis dengan ``_NS_gorath._local``, tapi memakai skala normalisasi
    hero supaya efek hidup menempel di badan pada KEDUA jalur (arena 1:1
    dan lane hero yang sprite-nya di-kecilkan).
    """
    G = _renderer()
    facing = getattr(boss, "direction", None)
    if facing is None:
        facing = getattr(boss, "facing", 1)
    f = 1 if (facing or 1) >= 0 else -1
    if action is None or phase is None or ap is None:
        action, phase, ap = pose_of(boss)
    lean = root_y = 0
    k = body_scale(boss)
    if G is not None:
        try:
            lean, root_y = G._rig_shift(action, phase, ap)
        except Exception:                      # pragma: no cover
            lean = root_y = 0
    return (int(round(x + (local[0] * f + lean * f) * k)),
            int(round(y + (local[1] + root_y) * k)))


def blade_points(boss, x, y, back=False):
    """(grip, tip) bilah dalam piksel layar — sumber bentuk trail."""
    G = _renderer()
    action, phase, ap = pose_of(boss)
    if G is None:
        grip_l = (20, 2)
        tip_l = (50, -16) if not back else (-12, 10)
    else:
        try:
            grip = (G._back_grip_local(action, ap, phase) if back
                    else G._front_grip_local(action, ap, phase))
            tip_l = G._tip_local(action, phase, ap, back)
            grip_l = (int(grip[0]), int(grip[1]))
        except Exception:                      # pragma: no cover
            grip_l, tip_l = (20, 2), (46, -4)
    grip = screen_point(boss, x, y, grip_l, action, phase, ap)
    tip = screen_point(boss, x, y, tip_l, action, phase, ap)
    return pygame.Vector2(grip), pygame.Vector2(tip)


def _ground_dy(boss):
    """Jarak anchor -> garis tanah, dalam piksel layar."""
    G = _renderer()
    dy = getattr(G, "GROUND_DY", 32) if G is not None else 32
    return int(round(float(dy) * render_scale(boss)))


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
    """Jumlah partikel yang diizinkan (preset rendah bisa 0 = mati total)."""
    Q = _quality()
    if Q is None:
        return MAX_PARTICLES
    try:
        ratio = float(getattr(Q, "particle_ratio", 1.0) or 1.0)
    except (TypeError, ValueError):
        ratio = 1.0
    return max(0, int(MAX_PARTICLES * max(0.0, min(1.0, ratio))))


def glow_allowed():
    """True kalau halo additive diizinkan (glow low/off memangkasnya)."""
    Q = _quality()
    if Q is None:
        return True
    try:
        return bool(getattr(Q, "glow", True))
    except Exception:                          # pragma: no cover
        return True


def shake_allowed():
    """True kalau screen shake diizinkan preset kualitas."""
    Q = _quality()
    if Q is None:
        return True
    try:
        return bool(getattr(Q, "screen_shake", True))
    except Exception:                          # pragma: no cover
        return True


# ============================================================================
# 4.  UTIL WARNA
# ============================================================================

def _clamp_color(color):
    c = tuple(max(0, min(255, int(v))) for v in color[:3])
    return c


def _mix(a, b, t):
    t = max(0.0, min(1.0, float(t)))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _hash01(seed):
    """Hash deterministik 0..1 (untuk retakan / serpihan)."""
    s = (seed * 2654435761) & 0xFFFFFFFF
    s ^= s >> 13
    s = (s * 2246822519) & 0xFFFFFFFF
    s ^= s >> 16
    return (s & 0xFFFFFF) / 16777215.0


# ============================================================================
# 5.  SURFACE CACHE  (glow / spark / ring / ellipse / ground glow)
# ============================================================================

_SURF_CACHE = {}
_SURF_ORDER = []
_SURF_CACHE_MAX = 384


def _cache_put(key, surf):
    """Simpan surface cache dengan evict LRU (terlama 25% saat penuh)."""
    if key in _SURF_CACHE:
        _SURF_ORDER.remove(key)
    _SURF_CACHE[key] = surf
    _SURF_ORDER.append(key)
    if len(_SURF_ORDER) > _SURF_CACHE_MAX:
        cut = max(1, _SURF_CACHE_MAX // 4)
        for old in _SURF_ORDER[:cut]:
            _SURF_CACHE.pop(old, None)
        del _SURF_ORDER[:cut]


def clear_cache():
    """Kosongkan seluruh cache surface (ganti level / reset)."""
    _SURF_CACHE.clear()
    _SURF_ORDER.clear()


def cache_size():
    return len(_SURF_ORDER)


def glow_surface(radius, color, power=1.0):
    """Halo radial lembut (additive). Radius & alpha di-kuantisasi supaya
    animasi yang terus membesar tidak meledakkan cache."""
    r = max(3, int(radius))
    if r % 2 == 0:
        r += 1
    a = max(16, min(255, int(255 * max(0.0, min(1.0, power)))))
    key = ("glow", r, _clamp_color(color), (a // 16) * 16)
    hit = _SURF_CACHE.get(key)
    if hit is not None:
        return hit
    surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    c = _clamp_color(color)
    try:
        for i in range(r, 1, -1):
            t = i / float(r)
            al = int(a * (1.0 - t) ** 2)
            if al <= 0:
                continue
            pygame.draw.circle(surf, (*c, al), (r, r), i)
    except Exception:                          # pragma: no cover
        pygame.draw.circle(surf, (*c, a), (r, r), r)
    _cache_put(key, surf)
    return surf


def spark_surface(size, color):
    """Bintang percik 4-sisi chunky (bukan cross-hair vektor)."""
    s = max(4, int(size))
    if s % 2 == 0:
        s += 1
    key = ("spark", s, _clamp_color(color))
    hit = _SURF_CACHE.get(key)
    if hit is not None:
        return hit
    surf = pygame.Surface((s * 2 + 2, s * 2 + 2), pygame.SRCALPHA)
    c = s + 1
    pts = [(c, c - s), (c + s // 3, c - s // 3), (c + s, c),
           (c + s // 3, c + s // 3), (c, c + s), (c - s // 3, c + s // 3),
           (c - s, c), (c - s // 3, c - s // 3)]
    try:
        pygame.draw.polygon(surf, (*_clamp_color(color), 235), pts)
        pygame.draw.polygon(surf, (255, 255, 255, 200),
                            [pts[0], (c, c), pts[2], (c, c), pts[4],
                             (c, c), pts[6], (c, c)])
    except Exception:                          # pragma: no cover
        pygame.draw.circle(surf, (*_clamp_color(color), 235), (c, c), s)
    _cache_put(key, surf)
    return surf


def ring_surface(radius, thickness, color, alpha=255, dashed=0):
    """Cincin stroke (dashed bila > 0) — untuk shockwave & marker."""
    r = max(3, int(radius))
    th = max(1, int(thickness))
    key = ("ring", r, th, _clamp_color(color), (alpha // 8) * 8, dashed)
    hit = _SURF_CACHE.get(key)
    if hit is not None:
        return hit
    surf = pygame.Surface((r * 2 + th * 2 + 2, r * 2 + th * 2 + 2),
                          pygame.SRCALPHA)
    c = r + th + 1
    rect = pygame.Rect(c - r, c - r, r * 2, r * 2)
    col = (*_clamp_color(color), max(0, min(255, int(alpha))))
    if dashed > 0:
        steps = max(6, dashed * 4)
        for i in range(steps):
            a0 = i * math.tau / steps
            a1 = (i + 0.5) * math.tau / steps
            try:
                pygame.draw.arc(surf, col, rect, a0, a1, th)
            except (ValueError, pygame.error):
                pass
    else:
        try:
            pygame.draw.circle(surf, col, (c, c), r, th)
        except (ValueError, pygame.error):
            pass
    _cache_put(key, surf)
    return surf


def ellipse_ring_surface(rx, ry, thickness, color, angle_deg=0):
    """Elips stroke — shockwave gepeng tegak lurus arah tebasan."""
    rx = max(3, int(rx))
    ry = max(3, int(ry))
    th = max(1, int(thickness))
    key = ("ering", rx, ry, th, _clamp_color(color), int(angle_deg) // 5 * 5)
    hit = _SURF_CACHE.get(key)
    if hit is not None:
        return hit
    w, h = rx * 2 + th * 2 + 2, ry * 2 + th * 2 + 2
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    c = (rx + th + 1, ry + th + 1)
    rect = pygame.Rect(c[0] - rx, c[1] - ry, rx * 2, ry * 2)
    col = (*_clamp_color(color), 255)
    steps = max(12, int((rx + ry) * 0.35))
    pts = []
    for i in range(steps + 1):
        a = i * math.tau / steps
        pts.append((c[0] + math.cos(a) * rx, c[1] + math.sin(a) * ry))
    for i in range(steps):
        try:
            pygame.draw.line(surf, col, pts[i], pts[i + 1], th)
        except (ValueError, pygame.error):
            pass
    if angle_deg:
        surf = pygame.transform.rotate(surf, float(angle_deg))
    _cache_put(key, surf)
    return surf


def ground_glow_surface(radius, color, power=0.3):
    """Cahaya tanah ber-falloff (decal, additive) — kolam darah dll."""
    r = max(4, int(radius))
    if r % 2 == 0:
        r += 1
    a = max(16, min(255, int(255 * max(0.0, min(1.0, power)))))
    key = ("gglow", r, _clamp_color(color), (a // 16) * 16)
    hit = _SURF_CACHE.get(key)
    if hit is not None:
        return hit
    surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    c = _clamp_color(color)
    for i in range(r, 1, -1):
        t = i / float(r)
        al = int(a * (1.0 - t) ** 1.6)
        if al <= 0:
            continue
        pygame.draw.ellipse(surf, (*c, al),
                            (r - i, int((r - i) * 0.62), i * 2,
                             max(2, int(i * 1.24))))
    _cache_put(key, surf)
    return surf


# ============================================================================
# 6.  SCRATCH BUFFER + BLIT
# ============================================================================

_SCRATCH = {}


def _scratch(w, h):
    """Buffer transparan kecil yang dipakai ulang (tanpa alokasi per frame)."""
    key = (max(8, int(w)), max(8, int(h)))
    s = _SCRATCH.get(key)
    if s is None:
        s = pygame.Surface(key, pygame.SRCALPHA)
        _SCRATCH[key] = s
    else:
        s.fill((0, 0, 0, 0))
    return s


def _blit_faded(surface, surf, cx, cy, alpha=255, additive=False):
    """Blit surface di tengah (cx, cy) dengan alpha; additive bila diminta."""
    if alpha <= 0:
        return
    a = max(0, min(255, int(alpha)))
    if a >= 255:
        surf.set_alpha(255)
    else:
        surf.set_alpha(a)
    w, h = surf.get_size()
    if additive:
        surface.blit(surf, (int(cx) - w // 2, int(cy) - h // 2),
                     special_flags=pygame.BLEND_RGB_ADD)
    else:
        surface.blit(surf, (int(cx) - w // 2, int(cy) - h // 2))


def _shard_poly(surface, cx, cy, ang, length, width, color, alpha=255):
    """Serpihan berbentuk belah ketupat memanjang (tanpa rotate surface)."""
    if alpha <= 0:
        return
    c = _clamp_color(color)
    dx, dy = math.cos(ang), math.sin(ang)
    px, py = -dy, dx
    hw = width * 0.5
    pts = [
        (cx + dx * length, cy + dy * length),
        (cx + px * hw, cy + py * hw),
        (cx - dx * length * 0.45, cy - dy * length * 0.45),
        (cx - px * hw, cy - py * hw),
    ]
    try:
        pygame.draw.polygon(surface, (*c, max(0, min(255, int(alpha)))), pts)
    except (ValueError, pygame.error):
        pass


# ============================================================================
# 7.  PARTICLE SYSTEM
# ============================================================================

class Particle:
    """Partikel tunggal — kontrak master prompt:

    ``position / velocity / acceleration`` (dengan alias ``pos/vel/acc``),
    ``life / max_life``, ``size``, ``rotation / rotation_speed``, ``alpha``,
    ``gravity``, ``color / color_end``. Ditambah ``drag``, ``fade_pow``,
    ``shape`` (pixel/spark/streak/shard/dust/glow/wisp/smoke), ``additive``,
    ``layer``.
    """

    __slots__ = ("x", "y", "vx", "vy", "ax", "ay", "life", "max_life",
                 "size", "rotation", "rotation_speed", "gravity", "color",
                 "color_end", "drag", "fade_pow", "shape", "additive",
                 "layer", "active", "seed")

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.ax = 0.0
        self.ay = 0.0
        self.life = 0.0
        self.max_life = 1.0
        self.size = 2.0
        self.rotation = 0.0
        self.rotation_speed = 0.0
        self.gravity = 0.0
        self.color = (200, 40, 40)
        self.color_end = None
        self.drag = 0.0
        self.fade_pow = 1.0
        self.shape = "pixel"
        self.additive = False
        self.layer = "front"
        self.active = False
        self.seed = 0

    # alias kontrak master prompt --------------------------------------
    @property
    def position(self):
        return pygame.Vector2(self.x, self.y)

    @property
    def velocity(self):
        return pygame.Vector2(self.vx, self.vy)

    @property
    def acceleration(self):
        return pygame.Vector2(self.ax, self.ay)

    # ------------------------------------------------------------------
    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.ax = float(kw.get("ax", 0.0))
        self.ay = float(kw.get("ay", 0.0))
        self.life = 0.0
        self.max_life = max(0.02, float(life))
        self.size = max(0.5, float(size))
        self.rotation = float(kw.get("rotation", 0.0))
        self.rotation_speed = float(kw.get("rotation_speed", 0.0))
        self.gravity = float(kw.get("gravity", 0.0))
        self.color = tuple(int(v) for v in color[:3])
        ce = kw.get("color_end")
        self.color_end = tuple(int(v) for v in ce[:3]) if ce else None
        self.drag = float(kw.get("drag", 0.0))
        self.fade_pow = float(kw.get("fade_pow", 1.0))
        self.shape = kw.get("shape", "pixel")
        self.additive = bool(kw.get("additive", False))
        self.layer = kw.get("layer", "front")
        self.seed = int(kw.get("seed", 0)) or random.randint(0, 9999)
        self.active = True
        return self

    # ------------------------------------------------------------------
    @property
    def progress(self):
        if self.max_life <= 0:
            return 1.0
        return max(0.0, min(1.0, self.life / self.max_life))

    def alpha(self):
        t = self.progress
        base = (1.0 - t) ** max(0.2, self.fade_pow)
        return max(0, min(255, int(255 * base)))

    # ------------------------------------------------------------------
    def update(self, dt):
        if not self.active:
            return False
        self.life += dt
        if self.life >= self.max_life:
            self.active = False
            return False
        self.vy += self.gravity * dt
        if self.drag > 0:
            f = max(0.0, 1.0 - self.drag * dt)
            self.vx *= f
            self.vy *= f
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rotation_speed * dt
        return True

    # ------------------------------------------------------------------
    def draw(self, surface):
        if not self.active:
            return
        t = self.progress
        a = self.alpha()
        if a <= 2:
            return
        x, y = int(self.x), int(self.y)
        size = max(1.0, self.size)
        col = self.color
        if self.color_end is not None:
            col = _mix(self.color, self.color_end, t)
        shape = self.shape

        if shape == "pixel":
            s = max(1, int(round(size)))
            pygame.draw.rect(surface, (*col, a), (x - s // 2, y - s // 2, s, s))
        elif shape == "spark":
            # garis pendek searah kecepatan (atau rotasi)
            ang = self.rotation
            ln = max(2.0, size * 2.6)
            dx, dy = math.cos(ang) * ln, math.sin(ang) * ln
            pygame.draw.line(surface, (*col, a), (x, y),
                             (x + int(dx), y + int(dy)), max(1, int(size * 0.6)))
        elif shape == "streak":
            ang = self.rotation
            _shard_poly(surface, x, y, ang, size * 2.2, size * 0.55, col, a)
        elif shape == "shard":
            ang = self.rotation
            _shard_poly(surface, x, y, ang, size * 1.8, size * 0.7, col, a)
            pygame.draw.circle(surface, (*_mix(col, P["fx_white"], 0.5), a),
                               (x, y), max(1, int(size * 0.35)))
        elif shape == "dust":
            r = int(size * (0.6 + 0.8 * t))
            buf = _scratch(r * 2 + 2, r * 2 + 2)
            cc = r + 1
            for i in range(3):
                rr = max(1, r - i)
                if rr <= 0:
                    break
                pygame.draw.circle(buf, (*_mix(col, P["smoke"], i * 0.28),
                                         int(a * (1.0 - i * 0.22))),
                                   (cc, cc), rr)
            surface.blit(buf, (x - cc, y - cc))
        elif shape == "glow":
            if glow_allowed():
                g = glow_surface(int(size * 2), col, a / 255.0)
                surface.blit(g, (x - g.get_width() // 2,
                                 y - g.get_height() // 2),
                             special_flags=pygame.BLEND_RGB_ADD)
            else:
                r = max(1, int(size))
                pygame.draw.circle(surface, (*col, a), (x, y), r)
        elif shape == "wisp":
            # ekor pendek bergelombang (spiral tipis)
            ang = self.rotation
            buf = _scratch(18, 18)
            cc = 9
            for i in range(5):
                aa = ang + i * 0.5
                rr = i * 1.4
                px = cc + int(math.cos(aa) * rr * 2.2)
                py = cc + int(math.sin(aa) * rr)
                pygame.draw.circle(buf, (*col, int(a * (1 - i / 5.5))),
                                   (px, py), max(1, int(size * (1 - i / 6))))
            surface.blit(buf, (x - cc, y - cc))
        elif shape == "smoke":
            r = int(size * (0.5 + 1.1 * t))
            col_smoke = _mix(col, P["smoke"], min(1.0, t * 1.4))
            pygame.draw.circle(surface, (*col_smoke, int(a * 0.5)), (x, y), r)
            pygame.draw.circle(surface, (*col_smoke, int(a * 0.3)),
                               (x + 1, y - 1), max(1, r - 1))
        else:                                   # pixel default
            s = max(1, int(round(size)))
            pygame.draw.rect(surface, (*col, a), (x - s // 2, y - s // 2, s, s))


class ParticleSystem:
    """Pool partikel reusable dengan cap.

    ``spawn / burst / stream / update / draw / clear / count / alive``.
    Permintaan melebihi cap dicatat di ``dropped`` (tidak pernah grow).
    """

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = int(cap)
        self._pool = [Particle() for _ in range(self.cap)]
        self._next = 0
        self.dropped = 0

    def count(self):
        return sum(1 for p in self._pool if p.active)

    def alive(self):
        return self.count()

    def clear(self):
        for p in self._pool:
            p.active = False
        self._next = 0
        self.dropped = 0

    def _acquire(self):
        for _ in range(self.cap):
            p = self._pool[self._next]
            self._next = (self._next + 1) % self.cap
            if not p.active:
                return p
        self.dropped += 1
        return None

    # ------------------------------------------------------------------
    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        p = self._acquire()
        if p is None:
            return None
        p.spawn(x, y, vx, vy, life, size, color, **kw)
        return p

    def burst(self, x, y, count, speed=(60.0, 210.0), life=(0.22, 0.55),
              size=(1, 3), colors=(P["blood_bright"], P["blood_hot"]),
              spread=math.tau, direction=0.0, gravity=0.0, drag=0.0,
              shape="pixel", additive=False, layer="front",
              color_end=None, rotation_speed=(0.0, 0.0)):
        """Ledakan partikel ke segala arah (atau kerucut ``spread``)."""
        n = max(0, int(count))
        for _ in range(n):
            ang = direction + random.uniform(-spread * 0.5, spread * 0.5)
            sp = random.uniform(speed[0], speed[1])
            life_v = random.uniform(life[0], life[1])
            sz = random.uniform(size[0], size[1])
            col = colors[random.randrange(len(colors))]
            self.spawn(x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                       life_v, sz, col, gravity=gravity, drag=drag,
                       shape=shape, additive=additive, layer=layer,
                       rotation=ang, rotation_speed=random.uniform(
                           rotation_speed[0], rotation_speed[1]),
                       color_end=color_end)

    def stream(self, x, y, tx, ty, count, life=(0.3, 0.6), size=(1, 3),
               colors=(P["blood_bright"], P["blood_hot"]), spread=0.35,
               speed=(40.0, 120.0), gravity=0.0, drag=0.0, shape="pixel",
               additive=False, layer="front"):
        """Aliran partikel dari (x,y) menuju (tx,ty)."""
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy) or 1.0
        base = math.atan2(dy, dx)
        n = max(0, int(count))
        for _ in range(n):
            ang = base + random.uniform(-spread, spread)
            sp = random.uniform(speed[0], speed[1])
            self.spawn(x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                       random.uniform(life[0], life[1]),
                       random.uniform(size[0], size[1]),
                       colors[random.randrange(len(colors))],
                       gravity=gravity, drag=drag, shape=shape,
                       additive=additive, layer=layer, rotation=ang,
                       color_end=P["smoke"] if shape == "smoke" else None)

    # ------------------------------------------------------------------
    def update(self, dt):
        for p in self._pool:
            if p.active:
                p.update(dt)

    def draw(self, surface, layer="front"):
        for p in self._pool:
            if p.active and p.layer == layer:
                if p.additive:
                    # partikel additive digambar lewat buffer agar tidak
                    # menimbulkan kotak additive pada sprite
                    p.draw(surface)
                else:
                    p.draw(surface)


# ============================================================================
# 8.  SWING TRAIL  — sabit darah dari histori ujung kukri yang sebenarnya
# ============================================================================

class SwingTrail:
    """Trail ayunan berbasis ARC (bukan lerp lurus).

    Histori menyimpan ``(pivot grip, sudut, radius, umur)`` untuk DUA bilah
    (kukri depan + belakang). Tiap pasangan sampel digambar sebagai sektor
    cincin tipis di sekitar poros grip — sabit mengikuti arah serangan,
    bukan lembaran raksasa. Arah yang berbalik MEMUTUS strip (recovery
    tidak menyapu badan); sapuan total dipangkas ke ``MAX_SWEEP``.
    """

    MAX_SWEEP = 1.95          # rad (≈112°) — potong dari ekor
    MAX_TURN_DOT = 0.15       # dot product arah < ini = arah berbalik
    ARC_STEP = 0.16           # rad per segmen busur (tepi mulus)

    def __init__(self, samples=TRAIL_SAMPLES):
        self.samples = max(4, int(samples))
        self.points = []          # list dict: grip, ang, radius, age, back
        self.width_boost = 1.0
        self.active = False

    def reset(self):
        self.points.clear()
        self.width_boost = 1.0

    def push(self, grip, tip, grip_b=None, tip_b=None):
        """Tambah sampel kedua bilah. ``grip/tip`` = Vector2 layar."""
        for (g, t, back) in ((grip, tip, False),
                             (grip_b, tip_b, True)):
            if g is None or t is None:
                continue
            dx = t.x - g.x
            dy = t.y - g.y
            radius = math.hypot(dx, dy)
            if radius < 3.0:
                continue
            ang = math.atan2(dy, dx)
            if self.points:
                last = self.points[-1]
                if last["back"] == back:
                    d = math.cos(ang - last["ang"])
                    if d < self.MAX_TURN_DOT:
                        # arah berbalik -> strip terputus (satu tebasan)
                        self.points = [p for p in self.points
                                       if p["back"] != back]
            self.points.append({"grip": (float(g.x), float(g.y)),
                                "ang": ang, "radius": radius, "age": 0.0,
                                "back": back})
        # pangkas ke panjang histori + sapuan maksimum
        if len(self.points) > self.samples * 2:
            self.points = self.points[-self.samples * 2:]
        sweep = 0.0
        last_ang = {}
        for p in self.points:
            b = p["back"]
            if b in last_ang:
                sweep += abs(p["ang"] - last_ang[b])
            last_ang[b] = p["ang"]
        while sweep > self.MAX_SWEEP and len(self.points) > 2:
            self.points.pop(0)
            sweep = 0.0
            last_ang = {}
            for p in self.points:
                b = p["back"]
                if b in last_ang:
                    sweep += abs(p["ang"] - last_ang[b])
                last_ang[b] = p["ang"]

    def update(self, dt):
        for p in self.points:
            p["age"] += dt
        self.points = [p for p in self.points if p["age"] < 0.22]

    def _ribbon(self, surface, lst, col, base_alpha, width):
        """Sektor cincin dari daftar sampel yang sudah urut."""
        n = len(lst)
        for i in range(1, n):
            p0, p1 = lst[i - 1], lst[i]
            a0, a1 = p0["ang"], p1["ang"]
            if a1 < a0:
                a0, a1 = a1, a0
            if a1 - a0 < 0.012:
                continue
            rank = i / float(n)
            alpha = int(base_alpha * rank * rank)
            if alpha <= 4:
                continue
            gx, gy = p1["grip"]
            r_out = max(4.0, p1["radius"] * 0.97)
            r_in = max(2.0, r_out - width * p1["radius"] * 0.22
                       * (0.5 + rank))
            steps = max(2, int((a1 - a0) / self.ARC_STEP) + 1)
            outer = [(gx + math.cos(a0 + (a1 - a0) * k / steps) * r_out,
                      gy + math.sin(a0 + (a1 - a0) * k / steps) * r_out)
                     for k in range(steps + 1)]
            inner = [(gx + math.cos(a1 - (a1 - a0) * k / steps) * r_in,
                      gy + math.sin(a1 - (a1 - a0) * k / steps) * r_in)
                     for k in range(steps + 1)]
            try:
                pygame.draw.polygon(surface, (*col, alpha), outer + inner)
            except (ValueError, pygame.error):
                pass

    def draw(self, surface):
        if not self.points:
            return
        front = [p for p in self.points if not p["back"]]
        back = [p for p in self.points if p["back"]]
        w = 0.16 * self.width_boost
        # 3 lapis: wash lebar gelap -> inti darah -> glint ujung
        self._ribbon(surface, front, P["blood_darkest"], 150, w * 1.5)
        self._ribbon(surface, back, P["blood_darkest"], 130, w * 1.5)
        self._ribbon(surface, front, P["blood_mid"], 200, w)
        self._ribbon(surface, back, P["blood_mid"], 170, w)
        self._ribbon(surface, front, P["blood_bright"], 235, w * 0.45)
        self._ribbon(surface, back, P["blood_bright"], 200, w * 0.45)
        # glint di lintasan ujung (titik terjauh sektor)
        for p in front[-3:]:
            gx, gy = p["grip"]
            alpha = int(200 * (p["age"] / 0.22))
            pygame.draw.circle(surface, (*P["blood_light"], alpha),
                               (int(gx + math.cos(p["ang"]) * p["radius"]),
                                int(gy + math.sin(p["ang"]) * p["radius"])),
                               max(1, int(2.2 * self.width_boost)))


# ============================================================================
# 9.  IMPACT FX  — paket lengkap saat benturan mendarat
# ============================================================================

class ImpactFX:
    """Flash bintang, shockwave elips, cincin, spoke debris, serpihan,
    cipratan darah — bukan bola putih. ``kind`` memilih bahasa visual:
    ``blade`` (kukri), ``blood`` (proyektil), ``rupture`` (R / ledakan
    besar)."""

    KINDS = ("blade", "blood", "rupture")

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

    # ------------------------------------------------------------------
    def update(self, dt):
        self.age += dt
        if self.age >= self.duration:
            self.active = False
        return self.active

    # ------------------------------------------------------------------
    def _ramp(self):
        if self.kind == "blade":
            return P["blood_darkest"], P["blood_mid"], P["blood_glow"]
        if self.kind == "rupture":
            return P["fx_dark"], P["blood_bright"], P["blood_hot"]
        return P["blood_dark"], P["blood_bright"], P["blood_light"]

    # ------------------------------------------------------------------
    def draw(self, surface):
        if not self.active:
            return
        t = min(1.0, self.age / self.duration)
        inv = 1.0 - t
        x, y = int(self.x), int(self.y)
        pw = self.power
        deg = math.degrees(self.angle)
        dark, mid, hot = self._ramp()

        # ── 1. FLASH: bintang 8 sisi, pendek & tebal ─────────────────
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

        # ── 2. SHOCKWAVE: elips gepeng TEGAK LURUS arah tebasan ──────
        rr = int((8 + 44 * pw) * (0.25 + 1.0 * t)) // 3 * 3
        th = max(1, int(4 * inv * pw))
        a = int(210 * inv * inv)
        if a > 6 and rr > 4:
            er = ellipse_ring_surface(rr, max(3, int(rr * 0.55)), th,
                                      mid, deg)
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

        # ── 3. SPOKE DEBRIS: garis radial memanjang keluar ──────────
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

        # ── 4. SLASH FRAGMENT: 3 busur pecah searah pukulan ─────────
        if t < 0.52 and self.kind in ("blade", "blood"):
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

        # ── 5. CIPRATAN DARAH (blade / blood) ───────────────────────
        if t < 0.55 and self.kind in ("blade", "blood"):
            st = 1.0 - t / 0.55
            n = 6 if self.kind == "blade" else 9
            for i in range(n):
                ang = self.angle + i * math.tau / n + 0.35 * st
                L = (10 + 16 * pw) * st * (0.6 + 0.5 * _hash01(
                    self.seed + i))
                ex = x + int(math.cos(ang) * L)
                ey = y + int(math.sin(ang) * L * 0.8)
                pygame.draw.line(surface,
                                 (*_mix(mid, hot, 0.5), int(190 * st)),
                                 (x, y), (ex, ey), 2)
                pygame.draw.circle(surface,
                                   (*hot, int(230 * st)),
                                   (ex, ey), max(1, int(2 * st)))

        # ── 6. RETAKAN ZIGZAG (rupture — ledakan besar) ─────────────
        if t < 0.62 and self.kind == "rupture":
            st = 1.0 - t / 0.62
            a2 = int(200 * st)
            n = 7
            for i in range(n):
                base = (self.seed * 0.37) + i * math.tau / n
                length = (16 + 20 * pw) * (0.6 + 0.55 * t)
                px, py = x, y
                ang = base
                for seg in range(3):
                    ang += (_hash01(self.seed + i * 13 + seg) - .5) * 1.1
                    nx = px + math.cos(ang) * (length / 3.0)
                    ny = py + math.sin(ang) * (length / 3.0)
                    pygame.draw.line(surface,
                                     _clamp_color(_mix(dark, hot,
                                                       1 - seg * .3)),
                                     (int(px), int(py)), (int(nx), int(ny)),
                                     max(1, 3 - seg))
                    px, py = nx, ny

        # ── 7. INTI benturan ────────────────────────────────────────
        if t < 0.40:
            st = 1.0 - t / 0.40
            sz = int((5 + 9 * pw) * (0.5 + 0.5 * st)) // 2 * 2 + 2
            s = spark_surface(sz, hot if not self.crit else P["fx_white"])
            s.set_alpha(int(255 * st))
            surface.blit(s, (x - sz - 1, y - sz - 1))


# ============================================================================
# 10.  PROJECTILE SYSTEM  —  BOLT DARAH
# ============================================================================

class GorathProjectile:
    """Bolt darah — modular, vektor, delta-time.

    Kontrak atribut: ``position, velocity, speed, damage, lifetime,
    target, radius, rotation, trail, particles, active`` (plus ``homing``,
    ``state``, ``kind`` untuk lifecycle-nya).

    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY

    Proyektil di lapisan FX bersifat VISUAL (``damage=0`` default): damage
    skill tetap dihitung sistem gameplay (base_boss), jadi tidak ada
    perubahan angka keseimbangan — hanya pembawaannya yang jadi nyata.
    """

    STATE_TRAVEL = "travel"
    STATE_IMPACT = "impact"
    STATE_DEAD = "dead"

    def __init__(self, x, y, tx, ty, speed=BOLT_SPEED, damage=0,
                 lifetime=1.9, target=None, radius=7.0, kind="blood",
                 ground=0.0, particles=None, on_impact=None):
        self.spawn_pos = pygame.Vector2(float(x), float(y))
        self.position = pygame.Vector2(float(x), float(y))
        self.tx = float(tx)
        self.ty = float(ty)
        self.speed = float(speed)
        self.damage = float(damage)
        self.lifetime = 0.0
        self.max_lifetime = float(lifetime)
        self.target = target
        self.radius = float(radius)
        self.hit_radius = max(3.0, float(radius) * 0.85)
        self.rotation = 0.0
        self.trail = []               # [Vector2, umur]
        self.trail_life = 0.24
        self.particles = particles
        self.active = True
        self.state = self.STATE_TRAVEL
        self.kind = kind
        self.homing = True
        self.hit_pos = None
        self.ground = float(ground)
        self.on_impact = on_impact
        self.seed = random.randint(0, 9999)
        self._impact_age = 0.0
        self._emit_acc = 0.0
        dx, dy = self.tx - self.x, self.ty - self.y
        dist = math.hypot(dx, dy) or 1.0
        self.velocity = pygame.Vector2((dx / dist) * self.speed,
                                       (dy / dist) * self.speed)
        self.rotation = math.atan2(dy, dx)

    # kontrak master prompt ---------------------------------------------
    @property
    def x(self):
        return self.position.x

    @property
    def y(self):
        return self.position.y

    @x.setter
    def x(self, v):
        self.position.x = float(v)

    @y.setter
    def y(self, v):
        self.position.y = float(v)

    @property
    def sx(self):
        return int(self.position.x)

    @property
    def sy(self):
        return int(self.position.y)

    # ------------------------------------------------------------------
    def kill(self, x=None, y=None):
        if self.state == self.STATE_DEAD:
            return
        self.hit_pos = pygame.Vector2(self.position.x if x is None else x,
                                      self.position.y if y is None else y)
        self.state = self.STATE_IMPACT
        self._impact_age = 0.0
        if self.on_impact is not None:
            try:
                self.on_impact(self)
            except Exception:                      # pragma: no cover
                pass
        self.active = False

    # ------------------------------------------------------------------
    def update(self, dt):
        """Kembalikan False kalau proyektil harus dibuang."""
        if self.state == self.STATE_DEAD:
            return False

        if self.state == self.STATE_IMPACT:
            self._impact_age += dt
            self._age_trail(dt)
            if self._impact_age > 0.26 and not self.trail:
                self.state = self.STATE_DEAD
                return False
            return True

        self.lifetime += dt
        if self.lifetime > self.max_lifetime:
            self.kill()
            return True                      # satu frame untuk pop-nya

        # ── homing halus ke target yang masih hidup ──────────────────
        tgt = self.target
        if tgt is not None and getattr(tgt, "alive", False):
            to = pygame.Vector2(float(tgt.x), float(tgt.y)) - self.position
            if to.length_squared() > 1.0:
                desired = to.normalize() * self.speed
                self.velocity += (desired - self.velocity) \
                    * min(1.0, self.homing * dt * 6.0)
                if self.velocity.length_squared() > 1e-6:
                    self.velocity.scale_to_length(self.speed)
        self.rotation = math.atan2(self.velocity.y, self.velocity.x)

        # ── catat trail, lalu maju ───────────────────────────────────
        self.trail.append([pygame.Vector2(self.position), 0.0])
        if len(self.trail) > 12:
            self.trail.pop(0)
        self._age_trail(dt)
        self.position += self.velocity * dt

        # ── emisi partikel ekor (rate-limited, jangan tiap frame) ───
        ps = self.particles
        if ps is not None:
            self._emit_acc += dt
            if self._emit_acc >= 0.035:
                self._emit_acc = 0.0
                ang = self.rotation + math.pi + (random.random() - .5) * 1.1
                spd = random.uniform(22, 70)
                ps.spawn(self.position.x, self.position.y,
                         math.cos(ang) * spd, math.sin(ang) * spd,
                         random.uniform(0.14, 0.3), random.uniform(1.5, 3.0),
                         P["blood_bright"] if random.random() < .5
                         else P["blood_glow"],
                         color_end=P["blood_darkest"], drag=3.0,
                         shape="pixel", additive=True)

        # ── tumbukan dengan target ───────────────────────────────────
        if tgt is not None and getattr(tgt, "alive", False):
            hit_r = self.hit_radius + float(getattr(tgt, "radius", 12)) + 4.0
            if self.position.distance_squared_to(
                    pygame.Vector2(float(tgt.x), float(tgt.y))) \
                    <= hit_r * hit_r:
                self.kill(tgt.x, tgt.y)
        elif tgt is None and self.position.distance_squared_to(
                pygame.Vector2(self.tx, self.ty)) <                 (self.speed * dt + 6.0) ** 2:
            self.kill(self.tx, self.ty)
        return True

    def _age_trail(self, dt):
        for s in self.trail:
            s[1] += dt
        if self.trail:
            self.trail = [s for s in self.trail if s[1] < self.trail_life]

    # ------------------------------------------------------------------
    def draw(self, surface):
        """Trail berlapis -> body bolt (IMPACT state tidak menggambar
        body — gantinya pop via draw_impact)."""
        draw_blood_bolt(surface, self.position.x, self.position.y,
                        self.rotation, age=min(1.0, self.lifetime * 60),
                        radius=self.radius, spin_seed=self.seed,
                        trail=self.trail)

    def draw_impact(self, surface):
        """Sisa cahaya sesaat setelah bolt pecah (fase IMPACT)."""
        if self.state != self.STATE_IMPACT:
            return
        t = min(1.0, self._impact_age / 0.26)
        a = int(220 * (1.0 - t))
        if a <= 5:
            return
        x, y = int(self.hit_pos.x), int(self.hit_pos.y)
        r = int(9 + 22 * t)
        ring = ring_surface(r, max(1, int(3 * (1 - t))), P["blood_light"],
                            255, dashed=9)
        ring.set_alpha(a)
        surface.blit(ring, (x - ring.get_width() // 2,
                            y - ring.get_height() // 2))
        glint = spark_surface(max(3, int(9 * (1 - t))), P["fx_white"])
        glint.set_alpha(a)
        surface.blit(glint, (x - glint.get_width() // 2,
                             y - glint.get_height() // 2))
        pygame.draw.circle(surface, (*P["blood_hot"], int(a * 0.8)),
                           (x, y), max(1, int(5 * (1 - t))))


class ProjectileSystem:
    """Pengelola proyektil Gorath (cap + auto-cleanup)."""

    def __init__(self, particles=None, cap=MAX_PROJECTILES):
        self.projectiles = []
        self.particles = particles
        self.cap = int(cap)

    def count(self):
        return len(self.projectiles)

    def list(self):
        """Proyektil aktif (read-only) — dipakai debug overlay & tes."""
        return tuple(self.projectiles)

    def clear(self):
        self.projectiles.clear()

    def spawn(self, x, y, tx, ty, **kw):
        """Buat proyektil baru; None kalau sudah mentok cap."""
        if len(self.projectiles) >= self.cap:
            return None
        kw.setdefault("particles", self.particles)
        pr = GorathProjectile(x, y, tx, ty, **kw)
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
# 10b.  RENDERER BOLT DARAH  (dipakai lapisan hidup & panggilan berdiri
# sendiri) — bukan lingkaran: ekor meruncing -> halo -> outline gelap ->
# kepala panah 3 lapis -> fuller -> 2 serpihan orbit -> glint ujung.
# ============================================================================

def draw_blood_bolt(surface, px, py, angle=0.0, age=0, crit=False,
                    radius=7.0, spin_seed=0, trail=None, impact=False):
    """Gambar bolt darah di (px, py) menghadap ``angle`` (rad)."""
    x, y = int(px), int(py)
    r = max(3.0, float(radius))
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy, dx

    # ── trail berlapis (meruncing ke ekor) ──────────────────────────
    if trail:
        n = len(trail)
        for i, entry in enumerate(trail):
            # entry bisa [Vector2, umur] (proyektil) atau (x, y, sudut)
            if isinstance(entry, (list, tuple)) and len(entry) >= 2 \
                    and hasattr(entry[0], "x"):
                tx, ty = entry[0].x, entry[0].y
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                tx, ty = entry[0], entry[1]
            else:
                continue
            t = (i + 1) / float(n)
            al = int(36 + 150 * t)
            rr = max(1, int(r * (0.35 + 0.75 * t)))
            pygame.draw.circle(surface, (*P["blood_dark"], int(al * 0.55)),
                               (int(tx), int(ty)), rr + 2)
            pygame.draw.circle(surface, (*P["blood_bright"], al),
                               (int(tx), int(ty)), rr)
            if i % 3 == 0:
                pygame.draw.circle(surface, (*P["blood_hot"], al),
                                   (int(tx), int(ty) - 1), max(1, rr - 2))

    # ── halo + outline gelap (badan bolt, bukan lingkaran polos) ────
    tail = (x - int(dx * r * 4.2), y - int(dy * r * 4.2))
    if glow_allowed():
        g = glow_surface(int(r * 2.6), P["blood_glow"], 0.5)
        surface.blit(g, (x - g.get_width() // 2, y - g.get_height() // 2),
                     special_flags=pygame.BLEND_RGB_ADD)
    for wd, col in ((6, P["blood_darkest"]), (4, P["blood_mid"])):
        pygame.draw.line(surface, col, tail, (x, y), wd)

    # ── kepala panah 3 lapis (crescent fang) ────────────────────────
    tip = (x + int(dx * r * 1.9), y + int(dy * r * 1.9))
    base = (x - int(dx * r * 0.6), y - int(dy * r * 0.6))
    w1 = int(r * 0.85)
    w2 = int(r * 0.45)
    for wd, col in ((w1, P["blood_darkest"]), (w2, P["blood_bright"])):
        pygame.draw.polygon(surface, col, [
            tip,
            (base[0] + int(nx * wd), base[1] + int(ny * wd)),
            (base[0] - int(nx * wd), base[1] - int(ny * wd)),
        ])
    pygame.draw.polygon(surface, P["blood_hot"], [
        tip,
        (base[0] + int(nx * w2 * 0.5), base[1] + int(ny * w2 * 0.5)),
        (base[0] - int(nx * w2 * 0.5), base[1] - int(ny * w2 * 0.5)),
    ])
    # fuller gelap (alur tengah)
    pygame.draw.line(surface, P["blood_darkest"],
                     (base[0] - int(dx * r * 0.4), base[1] - int(dy * r * 0.4)),
                     (tip[0] - int(dx * r * 0.3), tip[1] - int(dy * r * 0.3)),
                     2)

    # ── 2 serpihan orbit spiral ─────────────────────────────────────
    for k in range(2):
        a = angle + k * math.pi + age * 5.2 + spin_seed * 0.01
        ox = x + int(math.cos(a) * r * 1.7)
        oy = y + int(math.sin(a) * r * 1.7)
        pygame.draw.circle(surface, (*P["blood_dark"], 170), (ox, oy), 2)
        pygame.draw.circle(surface, (*P["blood_glow"], 235), (ox, oy), 1)

    # ── inti + glint ujung ──────────────────────────────────────────
    pygame.draw.circle(surface, (*P["blood_dark"], 120), (x, y), int(r * 0.9))
    pygame.draw.circle(surface, (*P["blood_hot"], 245), (x, y),
                       max(1, int(r * 0.55)))
    pygame.draw.circle(surface, (*P["fx_white"], 255),
                       (x - int(nx * r * 0.3), y - int(ny * r * 0.3)),
                       max(1, int(r * 0.22)))
    pygame.draw.circle(surface, (*P["fx_white"], 230),
                       (tip[0], tip[1]), max(1, int(r * 0.28)))

    if impact:
        pygame.draw.circle(surface, (*P["blood_glow"], 190),
                           (x, y), int(r * 1.6))
        pygame.draw.circle(surface, (*P["fx_white"], 235),
                           (x, y), max(1, int(r * 0.7)))


# ============================================================================
# 11.  SKILL FX  —  Q BLOODRAGE / W BLOODRITE / E THIRST / R RUPTURE
# ============================================================================

class SkillFX:
    """FX skill lapisan hidup — lifecycle master prompt:

    CAST -> CHARGE -> RELEASE -> TRAVEL/AREA -> IMPACT -> AFTER -> FADE

    Timeline per skill (detik) + bahasa visual per skill: BUKAN tumpukan
    lingkaran. Q = pilar + mahkota api darah + bara; W = muzzle star +
    voli bolt + splat marker; E = jejak lompat + afterimage + ledakan
    pendaratan; R = rantai darah + wisp spiral + ledakan + duri.
    """

    # (charge, release, area, impact, fade) — total = SKILL_TOTAL
    TIMELINE = {
        "q": (0.12, 0.18, 0.55, 0.35, 0.30),
        "w": (0.10, 0.15, 0.30, 0.20, 0.25),
        "e": (0.08, 0.12, 0.15, 0.12, 0.13),
        "r": (0.15, 0.25, 0.50, 0.30, 0.30),
    }
    RADIUS = WORLD_RADIUS
    TINT = {
        "q": P["blood_hot"],
        "w": P["blood_bright"],
        "e": P["blood_glow"],
        "r": P["blood_light"],
    }

    def __init__(self, kind, x, y, particles=None, radius=None,
                 aim=(0.0, 0.0), ground=0.0, facing=1, leap_from=None):
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
        # E: titik tolak lompat (jejak afterimage digambar dari sini)
        self.leap_from = leap_from
        self._leap_emitted = False

    # ------------------------------------------------------------------
    @property
    def aim_angle(self):
        ax, ay = self.aim
        if abs(ax) < 0.01 and abs(ay) < 0.01:
            return 0.0
        return math.atan2(ay, ax)

    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    def update(self, dt):
        self.age += dt
        self._set_phase()
        if self.age >= self.total:
            self.active = False
        if self.particles is not None and self.kind in ("q", "r"):
            self._emit_embers(dt)
        return self.active

    # ------------------------------------------------------------------
    def _emit_embers(self, dt):
        """Bara naik selama fase steady (q/r) — hemat, selalu berujung."""
        if self.phase not in ("release", "area", "impact"):
            return
        self._emit += dt
        budget = particle_budget()
        if budget <= 0:
            return
        if self._emit < 0.045:
            return
        self._emit = 0.0
        if self.particles.count() >= budget:
            return
        kind = self.kind
        if kind == "q":
            self.particles.spawn(
                self.x + random.uniform(-10, 10), self.y - 14,
                random.uniform(-8, 8), random.uniform(-85, -40),
                random.uniform(0.35, 0.7), random.uniform(1.5, 3.0),
                P["ember"] if random.random() < 0.5 else P["blood_glow"],
                gravity=-30.0, drag=0.4, shape="wisp", additive=True,
                layer="front")
        else:
            self.particles.spawn(
                self.x + random.uniform(-18, 18),
                self.y + self.ground,
                random.uniform(-40, 40), random.uniform(-70, -20),
                random.uniform(0.4, 0.8), random.uniform(2, 4),
                P["blood_hot"] if random.random() < 0.5 else P["smoke"],
                gravity=-20.0, drag=1.2, shape="smoke", layer="back")

    # ==================================================================
    # GROUND PASS  (di bawah sprite — decal & back particles)
    # ==================================================================
    def draw_ground(self, surface):
        t = min(1.0, self.age / max(0.01, self.total))
        inv = 1.0 - t
        x, y = int(self.x), int(self.y)
        gy = y + int(self.ground)
        k = self.radius / 60.0

        if self.kind == "q":
            # denyut kolam darah di tanah (falloff, bukan stroke)
            if self.phase in ("release", "area", "impact"):
                pulse = 0.6 + 0.4 * math.sin(self.age * 7.0)
                rr = int((16 + 30 * pulse) * k)
                if glow_allowed():
                    g = ground_glow_surface(rr, P["blood_dark"], 0.4 * inv)
                    surface.blit(g, (x - g.get_width() // 2,
                                     y - g.get_height() // 2 + int(
                                         self.ground * 0.6)))
                pygame.draw.ellipse(surface, (*P["blood_darkest"],
                                              int(120 * inv * pulse)),
                                    (x - rr, gy - rr // 3, rr * 2,
                                     max(4, rr // 2)))
                pygame.draw.ellipse(surface, (*P["blood_bright"],
                                              int(80 * inv * pulse)),
                                    (x - rr // 2, gy - rr // 6, rr,
                                     max(3, rr // 3)))

        elif self.kind == "w":
            # splat marker 2 cincin + retakan pendek di zona target
            if self.phase in ("area", "impact", "fade"):
                rr = int(self.radius * 0.42 * (0.5 + 0.5 * inv))
                st = inv if self.phase != "fade" else 1.0 - t
                a = int(150 * st)
                if rr > 6:
                    r1 = ring_surface(rr, 2, P["blood_mid"], a, dashed=6)
                    surface.blit(r1, (x - r1.get_width() // 2,
                                      y - r1.get_height() // 2
                                      + int(self.ground * 0.5)))
                    r2 = ring_surface(max(4, int(rr * 0.55)), 3,
                                      P["blood_hot"], int(a * 0.8))
                    surface.blit(r2, (x - r2.get_width() // 2,
                                      y - r2.get_height() // 2
                                      + int(self.ground * 0.5)))
                for i in range(4):
                    ang = self.seed + i * math.tau / 4 + 0.4
                    L = int((10 + 14 * inv) * k)
                    px, py = x, gy
                    for seg in range(2):
                        ang += (_hash01(self.seed + i * 7 + seg) - .5) * 1.0
                        nx = px + math.cos(ang) * L * 0.6
                        ny = py + math.sin(ang) * L * 0.3
                        pygame.draw.line(surface,
                                         (*P["blood_dark"], int(160 * st)),
                                         (int(px), int(py)),
                                         (int(nx), int(ny)), 2)
                        px, py = nx, ny

        elif self.kind == "e":
            # retakan pendaratan + gelombang tanah saat impact
            if self.phase in ("impact", "fade"):
                st = inv if self.phase == "impact" else 1.0 - t
                rr = int(self.radius * (0.3 + 0.6 * (1.0 - st)))
                if rr > 6:
                    er = ellipse_ring_surface(rr, max(3, int(rr * 0.5)),
                                              3, P["blood_bright"],
                                              int((self.age * 140) % 360))
                    er.set_alpha(int(190 * st))
                    surface.blit(er, (x - er.get_width() // 2,
                                      y - er.get_height() // 2
                                      + int(self.ground * 0.5)))
                for i in range(5):
                    ang = self.seed + i * math.tau / 5
                    L = int((8 + 20 * st) * k)
                    px, py = x, gy
                    for seg in range(3):
                        ang += (_hash01(self.seed + i * 11 + seg) - .5) * 0.9
                        nx = px + math.cos(ang) * L / 3
                        ny = py + math.sin(ang) * L * 0.4 / 3
                        pygame.draw.line(surface,
                                         (*P["blood_dark"], int(170 * st)),
                                         (int(px), int(py)),
                                         (int(nx), int(ny)),
                                         max(1, 3 - seg))
                        px, py = nx, ny

        elif self.kind == "r":
            # zona ledakan: cincin ganda mengembang + retakan magma
            if self.phase in ("impact", "fade"):
                st = inv if self.phase == "impact" else 1.0 - t
                rr = int(self.radius * (0.25 + 0.65 * (1.0 - st)))
                if rr > 8:
                    r1 = ring_surface(rr, 3, P["blood_mid"], 200, dashed=10)
                    surface.blit(r1, (x - r1.get_width() // 2,
                                      y - r1.get_height() // 2
                                      + int(self.ground * 0.5)))
                    r2 = ring_surface(max(5, int(rr * 0.6)), 2,
                                      P["blood_hot"], int(160 * st))
                    surface.blit(r2, (x - r2.get_width() // 2,
                                      y - r2.get_height() // 2
                                      + int(self.ground * 0.5)))
                if glow_allowed():
                    g = ground_glow_surface(int(rr * 0.9), P["blood_glow"],
                                            0.5 * st)
                    surface.blit(g, (x - g.get_width() // 2,
                                     y - g.get_height() // 2
                                     + int(self.ground * 0.6)))
                for i in range(6):
                    ang = self.seed * 0.3 + i * math.tau / 6
                    L = int((14 + 26 * st) * k)
                    px, py = x, gy
                    for seg in range(3):
                        ang += (_hash01(self.seed + i * 13 + seg) - .5) * 0.8
                        nx = px + math.cos(ang) * L / 3
                        ny = py + math.sin(ang) * L * 0.35 / 3
                        pygame.draw.line(surface,
                                         (*_mix(P["blood_darkest"],
                                                P["blood_hot"], seg * .4),
                                          int(200 * st)),
                                         (int(px), int(py)),
                                         (int(nx), int(ny)),
                                         max(2, 4 - seg))
                        px, py = nx, ny

    # ==================================================================
    # FRONT PASS  (di atas sprite)
    # ==================================================================
    def draw_front(self, surface):
        if not self.active:
            return
        t = min(1.0, self.age / max(0.01, self.total))
        inv = 1.0 - t
        x, y = int(self.x), int(self.y)
        phase = self.phase

        if self.kind == "q":
            self._draw_q_front(surface, x, y, t, inv, phase)
        elif self.kind == "w":
            self._draw_w_front(surface, x, y, t, inv, phase)
        elif self.kind == "e":
            self._draw_e_front(surface, x, y, t, inv, phase)
        else:
            self._draw_r_front(surface, x, y, t, inv, phase)

    # ------------------------------------------------------------------
    def _draw_q_front(self, surface, x, y, t, inv, phase):
        """BLOODRAGE: pilar aktivasi 4 lapis + mahkota api darah 2 ring +
        bintang 8 spike + glint orbit."""
        c = P["blood_hot"]
        # ── AKTIVASI: pilar darah 4 lapis ──
        if phase in ("cast", "charge"):
            pt = min(1.0, self.age / max(0.01, self.t_release))
            top = y - int((70 + 46 * (1 - pt)) * (self.radius / 90.0))
            for wd, col, al in ((30, P["blood_darkest"], 110),
                                (20, P["blood_dark"], 150),
                                (10, P["blood_bright"], 195),
                                (4, P["blood_hot"], 230)):
                pygame.draw.line(surface, (*col, int(al * (1 - pt * 0.3))),
                                 (x, top), (x, y), wd)
            pygame.draw.line(surface, (*P["fx_white"], int(200 * (1 - pt))),
                             (x, top), (x, y), 2)
            if glow_allowed():
                g = glow_surface(int(26 * (1 + pt)), P["blood_glow"],
                                 0.6 * (1 - pt * 0.4))
                surface.blit(g, (x - g.get_width() // 2,
                                 y - g.get_height() // 2 - 30),
                             special_flags=pygame.BLEND_RGB_ADD)
        # ── STEADY: mahkota api darah 2 ring + bintang + glint orbit ──
        if phase in ("release", "area"):
            pulse = 0.7 + 0.3 * math.sin(self.age * 6.5)
            for k, (rr, col, wd) in enumerate((
                    (int(30 * (self.radius / 90.0)), P["blood_mid"], 4),
                    (int(20 * (self.radius / 90.0)), P["blood_bright"], 3))):
                ang0 = self.age * (2.4 if k == 0 else -1.7)
                buf = _scratch(rr * 2 + 8, rr * 2 + 8)
                cc = rr + 4
                for i in range(14):
                    a = ang0 + i * math.tau / 14
                    px = cc + int(math.cos(a) * rr * pulse)
                    py = cc + int(math.sin(a) * rr * 0.62 * pulse)
                    ln = 4 if i % 2 else 7
                    pygame.draw.line(
                        surface,
                        (*col, int(160 + 60 * _hash01(self.seed + i))),
                        (x + int(math.cos(a) * rr * pulse * 0.8),
                         y - 8 + int(math.sin(a) * rr * 0.5 * pulse * 0.8)),
                        (x + int(math.cos(a) * (rr * pulse + ln)),
                         y - 8 + int(math.sin(a) * rr * 0.5 * pulse + ln * 0.4)),
                        2 if i % 2 else 1)
            self._star(surface, x, y - 10, int(26 * (self.radius / 90.0)),
                       P["blood_glow"], int(190 * pulse), spikes=8,
                       rot=self.age * 1.4, core=P["fx_white"])
            for k in range(3):
                a = self.age * 2.1 + k * math.tau / 3
                rr = int((26 + 8 * math.sin(self.age * 3 + k)) *
                         (self.radius / 90.0))
                gx = x + int(math.cos(a) * rr)
                gy = y - 12 + int(math.sin(a) * rr * 0.5)
                pygame.draw.circle(surface, (*P["ember"], 200), (gx, gy), 2)
                pygame.draw.circle(surface, (*P["fx_white"], 240), (gx, gy), 1)
        # ── RELEASE: cipratan radial ──
        if phase == "release":
            st = 1.0 - (self.age - self.t_release) / max(
                0.01, self.t_area - self.t_release)
            for i in range(10):
                a = self.seed * 0.3 + i * math.tau / 10
                L = int((14 + 26 * st) * (self.radius / 90.0))
                pygame.draw.line(surface, (*P["blood_hot"], int(170 * st)),
                                 (x, y - 6),
                                 (x + int(math.cos(a) * L),
                                  y - 6 + int(math.sin(a) * L * 0.6)), 2)

    # ------------------------------------------------------------------
    def _draw_w_front(self, surface, x, y, t, inv, phase):
        """BLOODRITE: muzzle star + aliran darah ke target + denyut inti."""
        # ── muzzle star di kedua kukri ──
        if phase in ("cast", "charge"):
            pt = min(1.0, self.age / max(0.01, self.t_release))
            for side in (-1, 1):
                sx = x + side * 26 * self.facing
                sy = y - 10
                self._star(surface, sx, sy, int(12 + 10 * pt),
                           P["blood_glow"], int(220 * (1 - pt * 0.5)),
                           spikes=4, rot=self.age * 3 + side, core=P["fx_white"])
        # ── aliran darah ke arah aim (3 pita) ──
        if phase in ("release", "area"):
            aa = self.aim_angle
            pulse = 0.75 + 0.25 * math.sin(self.age * 9)
            for k in range(3):
                off = (k - 1) * 0.22
                a = aa + off
                L = int((34 + 26 * (1 - k * 0.25)) * pulse)
                col = P["blood_bright"] if k < 2 else P["blood_glow"]
                pygame.draw.line(
                    surface, (*col, int(200 - k * 30)),
                    (x, y - 8),
                    (x + int(math.cos(a) * L),
                     y - 8 + int(math.sin(a) * L)), 3 - k)
            # denyut inti
            pygame.draw.circle(surface, (*P["blood_dark"], 150),
                               (x, y - 6), int(12 * pulse))
            pygame.draw.circle(surface, (*P["blood_hot"], 240),
                               (x, y - 6), int(6 * pulse))
        # ── fade: sisa kilau ──
        if phase == "fade":
            pygame.draw.circle(surface, (*P["blood_glow"], int(120 * inv)),
                               (x, y - 6), int(10 * inv))

    # ------------------------------------------------------------------
    def _draw_e_front(self, surface, x, y, t, inv, phase):
        """THIRST: jejak afterimage dari titik tolak + ledakan pendaratan."""
        # ── jejak lompat (dari leap_from ke posisi sekarang) ──
        if self.leap_from is not None:
            x0, y0 = int(self.leap_from[0]), int(self.leap_from[1])
            dx, dy = x - x0, y - y0
            dist = math.hypot(dx, dy)
            if dist > 8:
                n = min(7, int(dist / 9))
                for i in range(1, n + 1):
                    fr = i / float(n)
                    px = x0 + dx * fr
                    py = y0 + dy * fr
                    al = int(200 * (1 - fr) * inv)
                    pygame.draw.circle(surface, (*P["blood_dark"], al),
                                       (int(px), int(py)), 7)
                    pygame.draw.circle(surface, (*P["blood_glow"], al),
                                       (int(px), int(py)), 4)
                    if fr > 0.5:
                        pygame.draw.circle(surface, (*P["fx_white"], al),
                                           (int(px), int(py)), 2)
        # ── ledakan pendaratan (AOE 85 di titik mendarat) ──
        if phase in ("impact", "fade"):
            st = inv if phase == "impact" else 1.0 - t
            rr = int(self.radius * (0.35 + 0.5 * st))
            if glow_allowed():
                g = glow_surface(int(rr * 1.4), P["blood_glow"], 0.5 * st)
                surface.blit(g, (x - g.get_width() // 2,
                                 y - g.get_height() // 2),
                             special_flags=pygame.BLEND_RGB_ADD)
            self._star(surface, x, y, int(rr * 1.05), P["blood_hot"],
                       int(230 * st), spikes=8, rot=self.age * 2.2,
                       core=P["fx_white"])
            for i in range(8):
                a = self.seed * 0.4 + i * math.tau / 8
                L = int(rr * (0.8 + 0.5 * _hash01(self.seed + i)))
                pygame.draw.line(surface, (*P["blood_bright"], int(200 * st)),
                                 (x, y),
                                 (x + int(math.cos(a) * L),
                                  y + int(math.sin(a) * L * 0.7)), 2)
            # duri menyembur (bukan lingkaran)
            for i in range(6):
                a = self.seed + i * math.tau / 6 + 0.35
                L = int(rr * (0.5 + 0.8 * st))
                wdt = 3 if i % 2 else 2
                pygame.draw.polygon(surface, (*P["blood_darkest"],
                                              int(220 * st)),
                                    [(x + int(math.cos(a) * rr * 0.25),
                                      y + int(math.sin(a) * rr * 0.2)),
                                     (x + int(math.cos(a + 0.16) * L),
                                      y + int(math.sin(a + 0.16) * L * 0.8)),
                                     (x + int(math.cos(a - 0.16) * L),
                                      y + int(math.sin(a - 0.16) * L * 0.8))])

    # ------------------------------------------------------------------
    def _draw_r_front(self, surface, x, y, t, inv, phase):
        """RUPTURE: rantai darah bergelombang + wisp spiral 2 lengan +
        ledakan + duri + pilar caster."""
        # ── pilar aktivasi di caster ──
        if phase in ("cast", "charge"):
            pt = min(1.0, self.age / max(0.01, self.t_release))
            top = y - int((90 + 40 * (1 - pt)) * (self.radius / 190.0))
            for wd, col, al in ((36, P["blood_darkest"], 110),
                                (24, P["blood_dark"], 150),
                                (13, P["blood_bright"], 195),
                                (5, P["blood_hot"], 230)):
                pygame.draw.line(surface, (*col, int(al * (1 - pt * 0.25))),
                                 (x, top), (x, y), wd)
            pygame.draw.line(surface, (*P["fx_white"], int(200 * (1 - pt))),
                             (x, top), (x, y), 2)
        # ── rantai darah bergelombang ke arah aim ──
        if phase in ("release", "area", "impact"):
            aa = self.aim_angle
            dist = math.hypot(self.aim[0], self.aim[1])
            if dist > 20:
                segs = 9
                prev = (x, y - 6)
                for i in range(1, segs + 1):
                    fr = i / segs
                    mx = x + math.cos(aa) * dist * fr
                    my = y - 6 + math.sin(aa) * dist * fr
                    wig = math.sin(self.age * 5 + i * 1.3) * 4 * (1 - fr * 0.5)
                    mx += math.cos(aa + math.pi / 2) * wig
                    my += math.sin(aa + math.pi / 2) * wig
                    curr = (int(mx), int(my))
                    pygame.draw.line(surface, P["blood_darkest"],
                                     prev, curr, 5)
                    pygame.draw.line(surface, P["blood_mid"], prev, curr, 3)
                    pygame.draw.line(surface, P["blood_bright"], prev, curr,
                                     1)
                    if i % 3 == 0:
                        pygame.draw.circle(surface, (*P["blood_hot"], 230),
                                           curr, 2)
                    prev = curr
        # ── wisp spiral 2 lengan di sekitar caster ──
        if phase in ("release", "area"):
            for arm in range(2):
                for j in range(6):
                    a = self.age * 3.2 + arm * math.pi + j * 0.55
                    rr = (12 + j * 8) * (self.radius / 190.0)
                    px = x + int(math.cos(a) * rr)
                    py = y - 10 + int(math.sin(a) * rr * 0.5)
                    pygame.draw.circle(surface,
                                       (*P["blood_glow"],
                                        int(150 * (1 - j / 6))), (px, py), 2)
        # ── ledakan besar + duri (di caster — AOE 190) ──
        if phase in ("impact", "fade"):
            st = inv if phase == "impact" else 1.0 - t
            rr = int(self.radius * (0.3 + 0.55 * st))
            if glow_allowed():
                g = glow_surface(int(rr * 1.3), P["blood_hot"], 0.55 * st)
                surface.blit(g, (x - g.get_width() // 2,
                                 y - g.get_height() // 2),
                             special_flags=pygame.BLEND_RGB_ADD)
            self._star(surface, x, y, int(rr * 1.1), P["blood_glow"],
                       int(235 * st), spikes=10, rot=self.age * 1.6,
                       core=P["fx_white"])
            for i in range(12):
                a = self.seed * 0.3 + i * math.tau / 12
                L = int(rr * (0.9 + 0.6 * _hash01(self.seed + i)))
                pygame.draw.line(surface, (*P["blood_bright"], int(210 * st)),
                                 (x, y),
                                 (x + int(math.cos(a) * L),
                                  y + int(math.sin(a) * L * 0.8)), 2)
            for i in range(8):
                a = self.seed + i * math.tau / 8 + 0.3
                L = int(rr * (0.6 + 1.0 * st))
                pygame.draw.polygon(surface, (*P["blood_darkest"],
                                              int(225 * st)),
                                    [(x + int(math.cos(a) * rr * 0.2),
                                      y + int(math.sin(a) * rr * 0.16)),
                                     (x + int(math.cos(a + 0.14) * L),
                                      y + int(math.sin(a + 0.14) * L * 0.8)),
                                     (x + int(math.cos(a - 0.14) * L),
                                      y + int(math.sin(a - 0.14) * L * 0.8))])

    # ------------------------------------------------------------------
    def _star(self, surface, x, y, radius, color, alpha, spikes=8, rot=0.0,
              core=None):
        """Bintang tajam ber-spike (bukan lingkaran)."""
        if radius <= 2 or alpha <= 4:
            return
        pts = []
        for i in range(spikes * 2):
            a = rot + i * math.pi / spikes
            rr = radius if i % 2 == 0 else radius * 0.42
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        try:
            pygame.draw.polygon(surface, (*_clamp_color(color),
                                          int(alpha)), pts)
        except (ValueError, pygame.error):
            return
        if core is not None:
            pygame.draw.circle(surface, (*_clamp_color(core), int(alpha)),
                               (x, y), max(1, int(radius * 0.22)))


# ============================================================================
# 12.  DIRECTOR — satu per unit Gorath
# ============================================================================

def attack_phase(progress):
    """Nama fase serangan untuk progress 0..1."""
    p = max(0.0, min(1.0, float(progress)))
    for name, a, b in ATTACK_PHASES:
        if a <= p < b:
            return name
    return "RECOVERY"


class GorathFXDirector:
    """Mengikat particle + trail + proyektil + impact + skill FX untuk
    satu unit Gorath (hero MAUPUN mini boss — kodenya sama, hanya sumber
    transformasinya yang beda)."""

    def __init__(self, hero):
        self.hero = hero
        budget = particle_budget()
        self.particles = ParticleSystem(budget)
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
        # peristiwa engine yang sudah dikonsumsi (edge trigger)
        self._leap_seen = False
        self._leap_from = None
        self._e_fx = None

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def on_swing_start(self, x, y, facing):
        """Awal ayunan: trail di-reset + debu antisipasi di tanah."""
        self.trail.reset()
        self.trail.width_boost = 1.0
        self.swing_active = True
        self._impact_frame_seen = False
        gy = y + _ground_dy(self.hero)
        budget = particle_budget()
        if budget > 0:
            self.particles.burst(
                x + facing * 8, gy, 5,
                speed=(26, 80), life=(0.18, 0.4), size=(2, 4),
                colors=(P["dust"], P["blood_dark"], P["smoke"]),
                spread=1.2, direction=math.pi if facing > 0 else 0.0,
                gravity=95.0, drag=2.6, shape="dust", layer="back")

    def on_swing_end(self):
        self.swing_active = False

    def on_swing_impact_frame(self, x, y, facing):
        """Sapu udara di frame IMPACT — feedback walau tidak kena apa-apa."""
        budget = particle_budget()
        if budget <= 0:
            return
        try:
            _g, tip = blade_points(self.hero, x, y, False)
            _gb, tip_b = blade_points(self.hero, x, y, True)
        except Exception:                      # pragma: no cover
            return
        ang = math.atan2(tip.y - y, tip.x - x)
        self.particles.burst(
            tip.x, tip.y, 7,
            speed=(110, 250), life=(0.1, 0.24), size=(1, 3),
            colors=(P["blood_hot"], P["blood_glow"], P["fx_white"]),
            spread=1.5, direction=ang, drag=3.6, shape="streak",
            additive=True)
        self.particles.burst(
            tip_b.x, tip_b.y, 4,
            speed=(70, 170), life=(0.09, 0.2), size=(1, 3),
            colors=(P["blood_bright"], P["fx_white"]),
            spread=1.4, direction=ang + math.pi, drag=3.4, shape="streak",
            additive=True)
        if len(self.impacts) < MAX_IMPACTS:
            self.impacts.append(ImpactFX(tip.x, tip.y, ang, 0.5, False,
                                         kind="blade", ground=0.0,
                                         seed=int(self.frames)))

    def on_cast(self, x, y, skill, aim=None):
        """Skill dilepas: SkillFX + guncangan + (W) voli proyektil."""
        if skill not in SKILL_DUR:
            return
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        gy = _ground_dy(self.hero)
        G = _renderer()
        if aim is None:
            tgt = getattr(self.hero, "target", None)
            if tgt is not None and getattr(tgt, "alive", False):
                aim = (float(tgt.x), float(tgt.y))
            else:
                facing = 1 if getattr(self.hero, "direction", 1) >= 0 else -1
                aim = (x + facing * 90, y - 6)
        leap_from = None
        if skill == "e":
            self._leap_from = (float(self.hero.x), float(self.hero.y))
            leap_from = self._leap_from
        fx = SkillFX(skill, x, y, self.particles, aim=aim, ground=gy,
                     facing=getattr(self.hero, "direction", 1),
                     leap_from=leap_from)
        if skill == "e":
            self._e_fx = fx
        self.skills.append(fx)
        heavy = skill == "r"
        if shake_allowed():
            _feel_shake(6.0 if not heavy else 13.0,
                        0.16 if not heavy else 0.40)
        if skill == "w":
            self.spawn_blood_volley(x, y, aim)
        elif heavy and G is not None:
            # R: ledakan besar -> satu beat freeze
            _feel_hit_stop(0.06)
        self.particles.burst(x, y + gy * 0.4, 10,
                             speed=(60, 190), life=(0.2, 0.5), size=(2, 4),
                             colors=(P["blood_dark"], P["smoke"],
                                     P["dust"]),
                             spread=math.tau, gravity=150.0, drag=2.0,
                             shape="dust", layer="back")
        # gelombang kejut aktivasi di tanah (pengganti _draw_shockwave
        # di-canvas yang dilewati renderer saat owned)
        if len(self.impacts) < MAX_IMPACTS:
            self.impacts.append(ImpactFX(
                x, y + gy * 0.45, 0.0,
                1.7 if heavy else 1.15, False,
                kind="rupture" if heavy else "blood", ground=gy))

    def spawn_blood_volley(self, x, y, aim):
        """W: voli 3 bolt darah dari ujung kukri ke arah target."""
        try:
            _g, tip = blade_points(self.hero, x, y, False)
        except Exception:                      # pragma: no cover
            tip = pygame.Vector2(x + 30, y - 10)
        tgt = getattr(self.hero, "target", None)
        if tgt is None or not getattr(tgt, "alive", False):
            tgt = None
        base_ang = math.atan2(aim[1] - y, aim[0] - x)
        for k in (-1, 0, 1):
            a = base_ang + k * 0.14
            tx = tip.x + math.cos(a) * 420
            ty = tip.y + math.sin(a) * 420
            pr = self.projectiles.spawn(
                tip.x, tip.y, tx, ty,
                speed=BOLT_SPEED * (1.0 - abs(k) * 0.12), damage=0,
                target=tgt, radius=7.0, kind="blood",
                ground=_ground_dy(self.hero),
                on_impact=lambda p: self.on_impact(
                    p.hit_pos.x, p.hit_pos.y, p.rotation, 1.05, False,
                    kind="blood"))
            if pr is not None:
                pr.rotation = a
                pr.vx = math.cos(a) * pr.speed
                pr.vy = math.sin(a) * pr.speed
                self.particles.burst(tip.x, tip.y, 4,
                                     speed=(90, 200), life=(0.12, 0.28),
                                     size=(1, 3),
                                     colors=(P["fx_white"],
                                             P["blood_glow"]),
                                     spread=1.6, direction=a, drag=3.2,
                                     shape="spark", additive=True)
        return True

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="blade"):
        """Benturan mengenai target: flash, spark, debris, shake, hit-stop."""
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind=kind))
        self.hit_flash = 0.16
        pw = min(2.0, max(0.35, float(power)))
        budget = particle_budget()
        if budget <= 0:
            return

        if kind == "blade":
            spark, edge, hot = P["blood_hot"], P["blood_bright"], \
                P["fx_white"]
        elif kind == "rupture":
            spark, edge, hot = P["blood_glow"], P["blood_bright"], \
                P["blood_light"]
        else:
            spark, edge, hot = P["blood_glow"], P["blood_light"], \
                P["fx_white"]

        n = int(9 + 7 * pw) + (6 if crit else 0)
        self.particles.burst(
            x, y, n, speed=(120, 330 + 90 * pw), life=(0.16, 0.42),
            size=(2, 4), colors=(spark, hot, edge),
            spread=2.4, direction=angle, drag=3.6, shape="streak")
        self.particles.burst(
            x, y, int(5 + 3 * pw) + (4 if crit else 0),
            speed=(70, 200), life=(0.3, 0.66), size=(2, 5),
            colors=(edge, P["blood_dark"], P["bone_mid"]),
            gravity=470.0, drag=1.1, shape="shard",
            rotation_speed=(-16.0, 16.0))
        self.particles.burst(
            x, y, int(6 + 4 * pw), speed=(60, 190), life=(0.25, 0.5),
            size=(2, 4), colors=(P["blood_bright"], P["blood_hot"]),
            spread=math.tau, gravity=420.0, drag=1.4, shape="pixel",
            color_end=P["blood_darkest"])

        if shake_allowed():
            _feel_shake(4.5 + 3.5 * pw, 0.14 + 0.08 * pw)
        _feel_hit_stop(0.045 if not crit else 0.06)

    def on_hurt(self, amount=1.0):
        """Kena damage: cipratan darah pendek dari badan."""
        budget = particle_budget()
        if budget <= 0 or self.hero is None:
            return
        x = float(getattr(self.hero, "x", 0.0))
        y = float(getattr(self.hero, "y", 0.0))
        self.particles.burst(
            x, y - 12, int(6 + min(8, amount * 2)),
            speed=(50, 150), life=(0.2, 0.45), size=(2, 4),
            colors=(P["blood_bright"], P["blood_hot"], P["blood_dark"]),
            spread=2.6, direction=random.uniform(0, math.tau),
            gravity=430.0, drag=1.0, shape="pixel",
            color_end=P["blood_darkest"])

    def on_death(self, x, y):
        """Mati: ledakan darah besar + serpihan + guncangan keras."""
        self._death_done = True
        budget = particle_budget()
        if budget > 0:
            self.particles.burst(
                x, y - 10, 26, speed=(90, 300), life=(0.4, 0.9),
                size=(2, 5), colors=(P["blood_bright"], P["blood_hot"],
                                     P["blood_glow"]),
                spread=math.tau, gravity=260.0, drag=1.2, shape="streak")
            self.particles.burst(
                x, y - 10, 14, speed=(60, 200), life=(0.5, 1.1),
                size=(2, 5), colors=(P["bone_mid"], P["blood_dark"],
                                     P["metal_mid"]),
                spread=math.tau, gravity=520.0, drag=0.8, shape="shard",
                rotation_speed=(-18.0, 18.0))
            self.particles.burst(
                x, y - 6, 12, speed=(30, 120), life=(0.6, 1.3),
                size=(3, 6), colors=(P["smoke"], P["blood_darkest"]),
                spread=math.tau, gravity=-60.0, drag=1.8, shape="smoke",
                layer="back")
        if len(self.impacts) < MAX_IMPACTS:
            self.impacts.append(ImpactFX(x, y - 10, 0.0, 2.0, True,
                                         kind="rupture"))
        if shake_allowed():
            _feel_shake(16.0, 0.5)
        _feel_hit_stop(0.07)

    # ------------------------------------------------------------------
    # Watcher engine (edge trigger — tidak menyentuh gameplay)
    # ------------------------------------------------------------------
    def _watch_engine_events(self, x, y):
        """Baca state yang sudah ditulis engine/renderer; picu FX saat
        TEPI (transisi), bukan tiap frame."""
        hero = self.hero
        if hero is None:
            return
        # skill cast (tepi active_skill)
        skill = getattr(hero, "active_skill", None)
        if skill in SKILL_DUR and self._skill_seen != skill:
            if self._skill_seen is None or self._skill_seen == "":
                self.on_cast(x, y, skill)
            self._skill_seen = skill
        elif skill not in SKILL_DUR and self._skill_seen:
            self._skill_seen = None
            self._e_fx = None

        # kematian
        alive = getattr(hero, "alive", True)
        if not alive and not self._death_done:
            self.on_death(x, y)

        # kena damage (hp turun)
        hp = getattr(hero, "hp", None)
        if hp is not None:
            if self._last_hp is None:
                self._last_hp = hp
            elif hp < self._last_hp - 0.5:
                flash = int(getattr(hero, "hurt_flash_timer", 0) or 0)
                if flash >= 8:
                    self.on_hurt(self._last_hp - hp)
            self._last_hp = hp

        # lompatan posisi (E Thirst dash) — jejak di titik tolak
        if not self._leap_seen:
            dx = abs(x - self.last_x)
            dy = abs(y - self.last_y)
            if dx + dy > 46 and skill == "e":
                self._leap_seen = True
                self._leap_from = (self.last_x, self.last_y)
                budget = particle_budget()
                if budget > 0:
                    self.particles.burst(
                        self.last_x, self.last_y + 4, 8,
                        speed=(40, 130), life=(0.2, 0.45), size=(2, 4),
                        colors=(P["blood_bright"], P["dust"]),
                        spread=math.tau, gravity=180.0, drag=2.0,
                        shape="dust", layer="back")
        else:
            self._leap_seen = False

    # ------------------------------------------------------------------
    def _resolve_state(self):
        """State animasi dari renderer controller (atau fallback)."""
        hero = self.hero
        st = getattr(hero, "_gor_state", None)
        if st is None:
            if not getattr(hero, "alive", True):
                return "DEATH"
            if getattr(hero, "_gor_attack_active", False):
                return "SWING"
            if getattr(hero, "active_skill", None):
                return "SKILL"
            return "WALK" if getattr(hero, "_moving_cached", False) \
                else "IDLE"
        return st

    # ------------------------------------------------------------------
    def _update_state(self, dt):
        want = self._resolve_state()
        if want != self.state:
            self.prev_state = self.state
            self.state = want
            self.state_time = 0.0
        else:
            self.state_time += dt

    # ------------------------------------------------------------------
    def update(self, dt, x, y):
        """Majukan seluruh sistem FX unit ini satu langkah."""
        self.time += dt
        self.frames += 1
        self._watch_engine_events(x, y)
        self._update_state(dt)

        # ── deteksi ayunan dari controller renderer ──
        active = bool(getattr(self.hero, "_gor_attack_active", False))
        raw = float(getattr(self.hero, "_gor_attack_raw", 0.0) or 0.0)
        phase = getattr(self.hero, "_gor_attack_phase", "NONE") or "NONE"
        facing = 1 if (getattr(self.hero, "direction", 1) or 1) >= 0 else -1

        if active and not self._swing_seen:
            self._swing_seen = True
            self.on_swing_start(x, y, facing)
        elif not active and self._swing_seen:
            self._swing_seen = False
            self.on_swing_end()

        # trail: dorong posisi bilah SETIAP frame saat ayunan hidup
        if active:
            try:
                grip, tip = blade_points(self.hero, x, y, False)
                grip_b, tip_b = blade_points(self.hero, x, y, True)
                self.trail.push(grip, tip, grip_b, tip_b)
            except Exception:                      # pragma: no cover
                pass
        else:
            self.trail.update(dt)

        # frame IMPACT -> sapu udara (sekali per ayunan)
        if active and phase == "IMPACT" and not self._impact_frame_seen:
            self._impact_frame_seen = True
            self.on_swing_impact_frame(x, y, facing)

        # E: skill fx mengikuti posisi lompatan
        if self._e_fx is not None and self._e_fx.active:
            self._e_fx.x = float(x)
            self._e_fx.y = float(y)

        # majukan sistem
        self.trail.update(dt)
        self.particles.update(dt)
        self.projectiles.update(dt)
        for fx in self.impacts:
            fx.update(dt)
        self.impacts = [fx for fx in self.impacts if fx.active]
        for fx in self.skills:
            fx.update(dt)
        self.skills = [fx for fx in self.skills if fx.active]
        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)

        self.last_x = float(x)
        self.last_y = float(y)

    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        """GROUND FX + BACK PARTICLES (di bawah sprite)."""
        for s in self.skills:
            s.draw_ground(surface)
        self.particles.draw(surface, layer="back")

    def draw_front(self, surface, x, y):
        """ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES -> SKILL -> IMPACT."""
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
        """IMPACT FLASH: Surface transparan di atas badan (bukan tint RGB)."""
        k = max(0.0, min(1.0, self.hit_flash / 0.16))
        r = int(20 + 26 * k)
        if glow_allowed():
            g = glow_surface(r, P["blood_hot"], 0.7 * k)
            surface.blit(g, (int(x) - r, int(y) - r - 6),
                         special_flags=pygame.BLEND_RGB_ADD)
        size = int(30 + 46 * k)
        buf = _scratch(size * 2, size * 2)
        pygame.draw.circle(buf, (*P["fx_white"], int(120 * k)),
                           (size, size), int(size * 0.72))
        surface.blit(buf, (int(x) - size, int(y) - size - 8),
                     special_flags=pygame.BLEND_RGB_ADD)

    # ------------------------------------------------------------------
    def clear(self):
        """Kosongkan semua state FX unit ini."""
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
        self._last_hp = None
        self._death_done = False
        self._leap_seen = False
        self._leap_from = None
        self._e_fx = None

    def stats(self):
        """Ringkasan untuk debug / HUD."""
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


# ============================================================================
# 13.  BUS ADAPTER  (hit-stop & shake lewat combat_feel)
# ============================================================================

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
    """Dipanggil ``Game.update``: True kalau langkah simulasi dibekukan."""
    if not GORATH_FX_ENABLED or _feel is None:
        return False
    return _feel.should_freeze_frame()


def hit_stop(seconds=0.045):
    """API publik: minta hit-stop global."""
    _feel_hit_stop(seconds)


def shake(strength=5.0, duration=0.22):
    """API publik: guncangkan layar."""
    if not shake_allowed():
        return
    _feel_shake(strength, duration)


# ============================================================================
# 14.  REGISTRY DIRECTOR + HOOK RENDER
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Gorath."""
    _sync_palette()
    d = getattr(hero, "_gor_fx", None)
    if d is None:
        d = GorathFXDirector(hero)
        try:
            hero._gor_fx = d
        except Exception:                      # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:               # jangkar tua dibuang
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    """Lepas director dari registry DAN penanda milik-nya di unit.

    Penting: kalau penanda ``_gor_live_fx`` ditinggal sementara director
    sudah tidak dipanggil lagi, renderer akan terus MELEWATKAN efek
    di-canvas padahal tidak ada yang menggantinya -> efek hilang total.
    """
    try:
        if director.hero is not None:
            director.hero._gor_fx = None
            director.hero._gor_live_fx = False
    except Exception:                          # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit ini (dipanggil renderer / pipeline).

    Sekalian menandai unit supaya renderer TIDAK menggambar efek yang
    sekarang dimiliki lapisan hidup (FX skill foreground di canvas).
    Return True kalau lapisan hidup jadi dipakai.
    """
    if not GORATH_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                          # pragma: no cover
        return False
    try:
        hero._gor_live_fx = True
    except Exception:                          # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini.

    Dipakai renderer untuk memutuskan apakah FX skill foreground di-canvas
    masih perlu digambar (fallback) atau tidak. Unit tanpa director —
    potongan portrait, alat uji, renderer yang dipanggil langsung — tetap
    memakai jalur canvas lama, jadi tidak ada visual yang hilang kalau
    modul FX tidak tersedia.
    """
    if not getattr(hero, "_gor_live_fx", False):
        return False
    d = getattr(hero, "_gor_fx", None)
    return d is not None and d in _DIRECTORS


def tick(dt=None):
    """Majukan waktu FX satu frame nyata; aman dipanggil berkali-kali.

    Delta-time dihitung oleh bus ``combat_feel``: dijit agar lonjakan frame
    tidak melempar partikel ke luar layar, diperlambat saat hit-stop, dan
    shake hanya dimundurkan sekali walau beberapa karakter sama-sama punya
    lapisan hidup.

    ``dt`` boleh diisi (alat uji / audit) supaya simulasi FX bisa dijalankan
    dengan langkah tetap tanpa bergantung pada jam SDL.
    """
    global _LAST_TICK_MS
    if dt is not None:
        step = max(0.0, min(1.0 / 20.0, float(dt)))
        _advance(step)
        return step
    if _feel is not None:
        try:
            step = _feel.fx_dt()
        except Exception:                      # pragma: no cover
            step = 0.0
    else:                                      # pragma: no cover - fallback
        now = pygame.time.get_ticks()
        if _LAST_TICK_MS is None:
            _LAST_TICK_MS = now
            return 0.0
        ms = now - _LAST_TICK_MS
        _LAST_TICK_MS = now
        if ms <= 0:
            return 0.0
        step = max(1.0 / 240.0, min(1.0 / 20.0, ms / 1000.0))
        if _feel is not None and _feel.HITSTOP.active:
            step *= 0.18
    _advance(step)
    return step


def _advance(step):
    """Langkahkan seluruh director dengan dt yang sama (langkah FX)."""
    if step <= 0.0 or not _DIRECTORS:
        return
    for d in _DIRECTORS:
        h = d.hero
        d.update(step, float(getattr(h, "x", 0.0)),
                 float(getattr(h, "y", 0.0)))


def reset_all():
    """Bersihkan seluruh state FX Gorath (ganti level / keluar match).

    Sekalian melepas penanda "diambil alih" di setiap unit, supaya
    ``owns()`` dan ``draw_gorath`` kembali ke jalur canvas.
    """
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()
    clear_cache()
    if _feel is not None:
        try:
            _feel.reset()
        except Exception:                      # pragma: no cover
            pass


def total_particles():
    """Jumlah partikel Gorath hidup di seluruh arena (dipakai HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def projectiles_for(hero):
    """List proyektil milik unit (dipakai overlay debug)."""
    d = getattr(hero, "_gor_fx", None)
    if d is None:
        return []
    return list(d.projectiles.projectiles)


def stats():
    st = {"particles": 0, "projectiles": 0, "impacts": 0, "skills": 0}
    for d in _DIRECTORS:
        st["particles"] += d.particles.count()
        st["projectiles"] += d.projectiles.count()
        st["impacts"] += len(d.impacts)
        st["skills"] += len(d.skills)
    return st


# --- hook yang dipanggil heroes/__init__.py --------------------------------

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: digambar SEBELUM sprite hero di-blit."""
    if not GORATH_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_gor_fx", None)
    if d is not None:
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: digambar SESUDAH sprite hero di-blit."""
    if not GORATH_FX_ENABLED:
        return
    d = director_for(hero)
    d.draw_front(surface, x, y)


# --- hook yang dipanggil _entity.py / bosses/base_boss.py ------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Kukri Gorath mendarat di target (basic attack melee)."""
    if not GORATH_FX_ENABLED or hero is None or target is None:
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
                             kind="blood"):
    """Proyektil darah mengenai target."""
    if not GORATH_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    director_for(hero).on_impact(x, y, angle, power, bool(crit), kind=kind)


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """Skill Gorath meledak di sebuah titik (E pendaratan / R AOE)."""
    if not GORATH_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    if len(d.skills) >= MAX_SKILLS:
        d.skills.pop(0)
    gy = _ground_dy(hero)
    fx = SkillFX(skill, x, y, d.particles, radius, ground=gy,
                 facing=getattr(hero, "direction", 1))
    d.skills.append(fx)
    kind = "rupture" if skill == "r" else "blood"
    d.on_impact(x, y, 0.0, 1.3 if skill != "r" else 2.0,
                skill == "r", kind=kind)


def notify_skill_cast(hero, skill):
    """Dipanggil jalur gameplay saat skill dilepas (opsional).

    Director sudah mendeteksi tepi ``active_skill`` sendiri, jadi fungsi
    ini hanya berguna untuk alat uji / pemanggil yang ingin memaksa FX.
    """
    if not GORATH_FX_ENABLED or hero is None or skill not in SKILL_DUR:
        return
    d = director_for(hero)
    d.on_cast(float(getattr(hero, "x", 0.0)),
              float(getattr(hero, "y", 0.0)), skill)


def notify_skill_start(hero, skill):
    """Alias konservatif: sama dengan notify_skill_cast (dipakai audit)."""
    notify_skill_cast(hero, skill)


def notify_skill_end(hero, skill=None):
    """Selesaikan skill FX lebih awal (dipakai audit / reset state)."""
    if not GORATH_FX_ENABLED or hero is None:
        return
    d = getattr(hero, "_gor_fx", None)
    if d is None:
        return
    if skill is None:
        d.skills.clear()
    else:
        d.skills = [fx for fx in d.skills if fx.kind != skill]


# ============================================================================
# 15.  DEBUG OVERLAY  (DEBUG_CHARACTER = True)
# ============================================================================

def _debug_font():
    try:
        return pygame.font.SysFont("consolas", 13, bold=True)
    except Exception:                          # pragma: no cover
        return pygame.font.Font(None, 18)


def draw_debug_overlay(surface, director):
    """Overlay per-director di lapisan hidup (lane hero, sprite di-cache)."""
    try:
        font = _debug_font()
    except Exception:                          # pragma: no cover
        return
    st = director.stats()
    feel = None
    if _feel is not None:
        try:
            feel = _feel.stats()
        except Exception:
            feel = None
    hero = director.hero
    x = float(getattr(hero, "x", 0.0))
    y = float(getattr(hero, "y", 0.0))
    lines = [
        f"GORATH FX  {st['state']} {director.state_time:.2f}s",
        f"anim       {director.anim_phase}  swing {int(director.swing_active)}",
        f"particles  {st['particles']} (drop {st['dropped']})  cap"
        f" {director.particles.cap}",
        f"proj {st['projectiles']}  impact {st['impacts']}  skill"
        f" {st['skills']}  cache {st['cache']}",
    ]
    if feel is not None:
        lines.append(
            f"hitstop {feel.get('hitstop_frames', 0)}  "
            f"shake {feel.get('shake', 0.0):.1f}")
    xx = int(x) + 30
    yy = int(y) - 120
    for i, ln in enumerate(lines):
        img = font.render(ln, True, (255, 240, 120))
        pygame.draw.rect(surface, (10, 8, 12, 170),
                         (xx - 4, yy + i * 15 - 2,
                          img.get_width() + 8, 15))
        surface.blit(img, (xx, yy + i * 15))
