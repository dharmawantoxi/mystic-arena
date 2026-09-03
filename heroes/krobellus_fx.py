# ============================================================================
# heroes/krobellus_fx.py
# ----------------------------------------------------------------------------
# KROBELLUS — THE DEATH PROPHET — COMBAT / GAME-FEEL ENGINE
# (lapisan live ruang layar 1:1)
#
# Badan Krobellus (rig pixel-art nabi hantu + sabit spectral) digambar lewat
# ``_NS_krobellus`` (bosses/level5.py). Semua yang butuh gerak 60 fps sejati —
# trail sabit, partikel jiwa, proyektil soul bolt, FX skill Q/W/E/R, impact,
# guncangan layar, hit-stop — hidup di modul ini dan digambar LANGSUNG ke
# layar pada skala 1:1 tiap frame (tidak pernah masuk canvas sprite yang
# di-cache).
#
# Pembagian kerja (tidak ada efek yang digambar dua kali):
#
#   RENDERER (canvas, ter-cache)          MODUL INI (layar, hidup)
#   -----------------------------         ----------------------------------
#   rig pixel-art + selout + rim          trail sabit dari histori posisi bilah
#   bayangan, mist tanah, rune circle     partikel jiwa/serpihan/debu (pool)
#   pose, napas, jubah, sabit             PROYEKTIL soul bolt (sistem nyata)
#   telegraph tanah skill                 SKILL Q/W/E/R (lifecycle penuh)
#   fallback FX canvas (tanpa modul)      IMPACT FX + flash + hit-stop + shake
#                                         overlay DEBUG_CHARACTER
#
# Sinkronisasi timing dengan renderer (satu sumber kebenaran pose):
#   * serangan basic  : ``boss._krb_attack_progress`` / ``_krb_attack_kind``
#   * skill           : ``boss.active_skill`` / ``active_skill_timer``
#                       (jalur boss generik: ``ability_active`` -> 'q')
#   * kena damage     : ``boss.hurt_flash_timer``
#
# 100% PROSEDURAL. Tidak ada PNG / JPG / GIF / sprite-sheet / image.load.
#
# Isi modul
#   KROBELLS_PALETTE   palette karakter + FX (default; disinkron dari renderer)
#   Particle           partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem     pool + burst + cap, reusable
#   SwingTrail         ribbon sabit prosedural dari histori posisi bilah
#   ImpactFX           flash bintang + ring chunky
#   SoulBolt           proyektil modular (spawn->travel->trail->hit->destroy)
#   ProjectileSystem   manajer proyektil
#   SkillFX            lifecycle FX skill (cast->charge->release->area->fade)
#   KrobellusFXDirector  satu instance per unit, mengikat semua di atas
#   draw_debug_overlay hitbox/hurtbox/range/state/frame/FPS/particle/skill
#   API modul          tick / reset_all / notify_* / draw_*_layer
# ============================================================================

import math
import random

import pygame

try:                                 # bus game-feel bersama (semua karakter)
    from heroes import combat_feel as _feel
except Exception:                    # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual untuk karakter KROBELLS: hitbox, hurtbox, jangkauan, state
#: animasi, frame, FPS, jumlah partikel, state skill, timer serangan.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
KROBELLS_FX_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 220

#: Batas keras proyektil visual per director.
MAX_PROJECTILES = 6

#: Batas skill FX simultan per director.
MAX_SKILLS = 3

#: Batas dampak aktif per director.
MAX_IMPACTS = 8

#: Jumlah sample posisi bilah untuk ribbon trail.
TRAIL_SAMPLES = 10

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

# --- Geometri & timing (Wajib selaras dengan _NS_krobellus) ---------------
#: Kecepatan soul bolt (px/detik, ruang layar).
BOLT_SPEED = 340.0
#: Umur maksimum soul bolt (detik) — tidak ada proyektil hidup tanpa batas.
BOLT_LIFE = 2.2
#: Radius tabrakan visual soul bolt.
BOLT_RADIUS = 7.0

#: Jangkauan dunia (px) sabit: target di dalamnya -> SWING, di luar -> BOLT.
MELEE_REACH = 110.0

#: Durasi skill (frame @60fps) — acuan; renderer memakai timer aktual.
SKILL_DUR = {'q': 60, 'w': 60, 'e': 50, 'r': 90}

#: Fraksi progress skill di mana RELEASE terjadi (FX area/ledakan).
SKILL_RELEASE = {'q': 0.55, 'w': 0.45, 'e': 0.0, 'r': 0.35}

#: Frame pelepasan soul bolt pada serangan basic jenis 'bolt'.
ATK_RELEASE = 0.52

#: Frame benturan bilah pada serangan basic jenis 'swing'.
ATK_IMPACT = 0.46

# --- Game feel (detik) ------------------------------------------------------
HITSTOP_MELEE = 0.042
HITSTOP_BOLT = 0.034
HITSTOP_SKILL = 0.050
HITSTOP_R = 0.060


# ============================================================================
# 1.  PALETTE
# ============================================================================

#: Palette KROBELLS (dark fantasy: jubah ungu gelap, cahaya jiwa teal,
#: void ungu, trim emas, mata api merah). Renderer menyinkronkan paletnya
#: dari sini agar warna badan & efek tidak pernah melenceng.
KROBELLS_PALETTE = {
    # Outline & bayangan
    "outline":      (10,   6,  18),
    "shadow_deep":  (18,   8,  30),
    "shadow":       (30,  15,  48),

    # Jubah (ungu gelap)
    "robe_dark":    (44,  24,  70),
    "robe_mid":     (70,  40, 106),
    "robe_light":   (106, 66, 152),
    "robe_shine":   (148, 106, 196),
    "robe_fade":    (24,  12,  40),

    # Korset / pelat
    "armor_dark":   (26,  13,  44),
    "armor_mid":    (56,  32,  86),
    "armor_light":  (92,  58, 130),

    # Kulit (pucat, spectral)
    "skin_dark":    (140, 148, 148),
    "skin_mid":     (188, 202, 198),
    "skin_light":   (226, 238, 232),
    "skin_shine":   (244, 252, 248),

    # Jiwa teal (FX utama)
    "soul_dark":    (18,  72,  68),
    "soul_mid":     (46, 148, 134),
    "soul_light":   (96, 216, 194),
    "soul_bright":  (168, 250, 232),
    "soul_hot":     (228, 255, 248),
    "soul_white":   (250, 255, 252),

    # Void ungu (FX sekunder: silence/crypt)
    "void_dark":    (40,  14,  74),
    "void_mid":     (86,  34, 148),
    "void_light":   (142, 74, 208),
    "void_bright":  (196, 130, 244),
    "void_hot":     (236, 192, 255),

    # Trim emas
    "gold_dark":    (98,  64,  20),
    "gold_mid":     (178, 132, 40),
    "gold_light":   (238, 196,  84),
    "gold_shine":   (255, 236, 156),

    # Mata (api jiwa merah)
    "eye_dark":     (96,  18,  28),
    "eye_mid":      (190, 44,  54),
    "eye_bright":   (240, 96,  86),
    "eye_hot":      (255, 168, 150),

    # Sabit
    "scythe_dark":  (36,  30,  48),
    "scythe_mid":   (92,  84, 116),
    "scythe_light": (168, 160, 196),

    # FX putih netral
    "fx_white":     (245, 250, 252),
}

_P = KROBELLS_PALETTE

#: Kunci yang disalin dari palet renderer (kalau sudah dimuat) supaya warna
#: badan dan warna efek selalu identik.
_PALETTE_SYNC = {
    "outline": "outline",
    "shadow_deep": "shadow_deep",
    "shadow": "shadow",
    "robe_dark": "robe_dark",
    "robe_mid": "robe_mid",
    "robe_light": "robe_light",
    "robe_shine": "robe_shine",
    "robe_fade": "robe_fade",
    "armor_dark": "armor_dark",
    "armor_mid": "armor_mid",
    "armor_light": "armor_light",
    "skin_dark": "skin_dark",
    "skin_mid": "skin_mid",
    "skin_light": "skin_light",
    "skin_shine": "skin_shine",
    "soul_dark": "soul_dark",
    "soul_mid": "soul_mid",
    "soul_light": "soul_light",
    "soul_bright": "soul_bright",
    "soul_hot": "soul_hot",
    "soul_white": "soul_white",
    "void_dark": "void_dark",
    "void_mid": "void_mid",
    "void_light": "void_light",
    "void_bright": "void_bright",
    "void_hot": "void_hot",
    "gold_dark": "gold_dark",
    "gold_mid": "gold_mid",
    "gold_light": "gold_light",
    "gold_shine": "gold_shine",
    "eye_dark": "eye_dark",
    "eye_mid": "eye_mid",
    "eye_bright": "eye_bright",
    "eye_hot": "eye_hot",
    "scythe_dark": "scythe_dark",
    "scythe_mid": "scythe_mid",
    "scythe_light": "scythe_light",
    "fx_white": "fx_white",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Salin palet dari renderer (satu sumber kebenaran warna)."""
    global _PALETTE_SYNCED
    if _PALETTE_SYNCED:
        return
    G = _renderer()
    if G is None:
        return
    src = getattr(G, "PALETTE", None)
    if isinstance(src, dict):
        for dst, key in _PALETTE_SYNC.items():
            val = src.get(key)
            if isinstance(val, (tuple, list)) and len(val) >= 3:
                _PALETTE_SYNC[dst] = tuple(int(c) for c in val[:3])
    _PALETTE_SYNCED = True


# ============================================================================
# 2.  QUALITY GATE
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


# ============================================================================
# 3.  RENDERER (lazy) — satu sumber kebenaran pose & geometri sabit
# ============================================================================

_RENDERER = None          # None = belum dicari, False = tidak ada


def _renderer():
    """Muat ``_NS_krobellus`` dari bosses.level5 sekali; None kalau gagal."""
    global _RENDERER
    if _RENDERER is False:
        return None
    if _RENDERER is None:
        try:
            from bosses import level5 as _L
            _RENDERER = getattr(_L, "_NS_krobellus", None) or False
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
        return ("skill", float(getattr(boss, "pulse", 0.0)), 0.0)
    if getattr(boss, "_krb_attack_active", False):
        return ("attack", float(getattr(boss, "pulse", 0.0)),
                float(getattr(boss, "_krb_attack_progress", 0.0) or 0.0))
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
    sc = getattr(boss, "_render_scale", 1.0) or 1.0
    pivot = pygame.Vector2(x + 11 * f * sc, y - 20 * sc)
    tip = pygame.Vector2(x + 58 * f * sc, y + 18 * sc)
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
    return 48.0 * body_scale(boss)


# ============================================================================
# 4.  CACHE SURFACE PROSEDURAL  (dibangun sekali, dipakai semua unit)
# ============================================================================

_CACHE = {}
_CACHE_MAX = 160


def _cache_put(key, surf):
    if len(_CACHE) >= _CACHE_MAX:
        try:
            _CACHE.pop(next(iter(_CACHE)))
        except Exception:                      # pragma: no cover
            pass
    _CACHE[key] = surf
    return surf


def clear_cache():
    """Kosongkan cache surface prosedural (ganti level / keluar match)."""
    _CACHE.clear()


def cache_size():
    return len(_CACHE)


def glow_surface(radius, color, power=1.0):
    """Halo radial lembut (cached) — orb, impact, heal glow."""
    key = ("glow", int(radius), tuple(color[:3]), round(power, 1))
    s = _CACHE.get(key)
    if s is not None:
        return s
    r = max(1, int(radius))
    size = r * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cr, cg, cb = color[:3]
    steps = max(2, int(r / 1.5))
    for i in range(steps, 0, -1):
        rr = int(r * i / steps)
        a = int(110 * power * (1 - i / (steps + 1)) ** 1.5) + 8
        if a <= 0:
            continue
        pygame.draw.circle(surf, (cr, cg, cb, min(255, a)), (r + 1, r + 1), rr)
    return _cache_put(key, surf)


def flash_star(radius, color):
    """Bintang 8 lengan chunky (cached) — inti impact flash."""
    key = ("star", int(radius), tuple(color[:3]))
    s = _CACHE.get(key)
    if s is not None:
        return s
    n = max(4, int(radius))
    size = n * 2 + 3
    c0 = size // 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = color[:3]
    for i in range(8):
        a = i * math.pi / 4
        ln = n if i % 2 == 0 else int(n * 0.62)
        ex = c0 + math.cos(a) * ln
        ey = c0 + math.sin(a) * ln
        pygame.draw.line(surf, (*c, 255), (c0, c0), (ex, ey), 2)
    pygame.draw.circle(surf, (*c, 255), (c0, c0), max(2, n // 4))
    pygame.draw.circle(surf, (255, 255, 255, 255), (c0, c0), max(1, n // 7))
    return _cache_put(key, surf)


def ghost_sprite(size, tint=None):
    """Kepala hantu mini (cached) — ghost wave skill R & jiwa melayang."""
    key = ("ghost", int(size), tuple(tint[:3]) if tint else None)
    s = _CACHE.get(key)
    if s is not None:
        return s
    n = max(4, int(size))
    w = n * 2 + 4
    h = n * 2 + 6
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2
    body = tint if tint else (110, 220, 200)
    dark = (24, 90, 84)
    hot = (228, 255, 248)
    # badan hantu (airdrop chunky)
    pts = [
        (cx - n, cx), (cx - n + 2, cx - n + 3), (cx, cx - n + 1),
        (cx + n - 2, cx - n + 3), (cx + n, cx),
        (cx + n - 1, cx + n - 4), (cx + n // 3, cx + n - 2),
        (cx - n // 3, cx + n - 2), (cx - n + 1, cx + n - 4),
    ]
    pygame.draw.polygon(surf, (*dark, 255), pts)
    inner = [
        (cx - n + 3, cx), (cx - n + 4, cx - n + 5), (cx, cx - n + 3),
        (cx + n - 4, cx - n + 5), (cx + n - 3, cx),
        (cx + n - 4, cx + n - 6), (cx, cx + n - 5), (cx - n + 4, cx + n - 6),
    ]
    pygame.draw.polygon(surf, (*body, 255), inner)
    # rongga mata
    off = max(2, n // 3)
    pygame.draw.circle(surf, (*dark, 255), (cx - off, cx - 1), max(1, n // 4))
    pygame.draw.circle(surf, (*dark, 255), (cx + off, cx - 1), max(1, n // 4))
    pygame.draw.circle(surf, (*hot, 255), (cx - off, cx - 1), max(1, n // 6))
    pygame.draw.circle(surf, (*hot, 255), (cx + off, cx - 1), max(1, n // 6))
    return _cache_put(key, surf)


def _blit_faded(surface, surf, cx, cy, alpha=255.0, additive=False):
    """Blit dengan alpha dinamis tanpa mengotori surface cache."""
    alpha = max(0.0, min(255.0, alpha))
    if alpha <= 1.0:
        return
    if alpha >= 254.0 and not additive:
        surface.blit(surf, (int(cx - surf.get_width() / 2),
                            int(cy - surf.get_height() / 2)))
        return
    tmp = surf.copy()
    tmp.set_alpha(int(alpha))
    flags = pygame.BLEND_RGB_ADD if additive else 0
    surface.blit(tmp, (int(cx - surf.get_width() / 2),
                       int(cy - surf.get_height() / 2)),
                 special_flags=flags)


# ============================================================================
# 5.  PARTICLE SYSTEM  (pool + burst + cap)
# ============================================================================

class Particle:
    """Satu partikel: posisi, kecepatan, akselerasi, umur, rotasi, fade."""

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
        if self.shape == "orb":
            if glow_allowed() and s >= 2.5:
                _blit_faded(surface, glow_surface(int(s * 2.2), c, 0.7),
                            x, y, a * 0.75, additive=self.additive)
            pygame.draw.circle(surface, (*c, a), (x, y), max(1, int(s * 0.7)))
        elif self.shape == "spark":
            if glow_allowed():
                _blit_faded(surface, glow_surface(int(s * 2.0), c, 0.8),
                            x, y, a * 0.8, additive=True)
            pygame.draw.circle(surface, (255, 255, 255, a), (x, y),
                               max(1, int(s * 0.5)))
        elif self.shape == "streak":
            ln = max(2, int(s * 2.2))
            sp = math.hypot(self.vx, self.vy) or 1.0
            dx, dy = self.vx / sp, self.vy / sp
            pygame.draw.line(surface, (*c, a), (x, y),
                             (x - int(dx * ln), y - int(dy * ln)), max(1, int(s * 0.6)))
            pygame.draw.circle(surface, (255, 255, 255, a), (x, y),
                               max(1, int(s * 0.4)))
        elif self.shape == "shard":
            r = s
            pts = [
                (x + r, y),
                (x - r * 0.5, y - r * 0.6),
                (x - r, y),
                (x - r * 0.5, y + r * 0.6),
            ]
            pygame.draw.polygon(surface, (*c, a), pts)
        elif self.shape == "dust":
            pygame.draw.circle(surface, (*c, max(8, a // 2)), (x, y),
                               max(1, int(s)))
        elif self.shape == "soul":
            pygame.draw.circle(surface, (*c, a), (x, y), max(1, int(s * 0.8)))
            pygame.draw.circle(surface, (*c, a // 2), (x, y - 2),
                               max(1, int(s * 0.5)))
            pygame.draw.circle(surface, (255, 255, 255, a), (x, y - 1), 1)
        else:  # pragma: no cover - jaga-jaga
            pygame.draw.circle(surface, (*c, a), (x, y), max(1, int(s)))


class ParticleSystem:
    """Pool partikel reusable dengan cap keras + spawn/burst."""

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = int(cap)
        self.parts = []

    def count(self):
        return len(self.parts)

    def spawn(self, x, y, vx, vy, life, size, color, shape="orb",
              gravity=0.0, rotation=0.0, rotation_speed=0.0, drag=0.0,
              additive=False, layer="front", seed=0.0):
        if len(self.parts) >= self.cap:
            self.parts.pop(0)
        self.parts.append(Particle(x, y, vx, vy, life, size, color, shape,
                                   gravity=gravity, rotation=rotation,
                                   rotation_speed=rotation_speed, drag=drag,
                                   additive=additive, layer=layer, seed=seed))

    def burst(self, x, y, n, speed=(60.0, 220.0), life=(0.2, 0.5),
              size=(1.5, 3.5), colors=((96, 216, 194),), spread=math.tau,
              direction=None, gravity=0.0, drag=1.0, shape="orb",
              additive=False, layer="front", rotation_speed=None):
        """Ledakan n partikel dengan spread acak di sekitar direction."""
        n = max(0, int(n * particle_budget()))
        if n <= 0:
            return
        # CATATAN: variabel sampel TIDAK BOLEH menaungi parameter tuple
        # (life/size) — bug lama: iterasi ke-2 memecah *life yang sudah
        # jadi float.
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
                       seed=random.uniform(0.0, 10.0))

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
# 6.  SWING TRAIL  (ribbon sabit dari histori posisi bilah)
# ============================================================================

class SwingTrail:
    """Ribbon translusen yang mengikuti jejak ujung bilah.

    Menyimpan sampel posisi (OLD ... CURRENT) selama bilah dalam
    kecepatan tinggi; digambar sebagai polygon sabit yang memudar +
    serpihan pixel di tepi.
    """

    def __init__(self, samples=TRAIL_SAMPLES):
        self.samples = max(4, int(samples))
        self.pts = []          # [(x, y, speed), ...] terbaru di akhir
        self.active = False
        self.energy = 0.0      # 0..1 intensitas ribbon
        self.seed = 0

    def add_sample(self, x, y, speed, active):
        self.active = active
        if not active:
            # biarkan ribbon memudar, jangan menambah sampel
            return
        if self.pts:
            px, py, _ = self.pts[-1]
            d = math.hypot(x - px, y - py)
            if d < 1.5:
                self.pts[-1] = (x, y, speed)
                return
        self.pts.append((x, y, max(0.0, float(speed))))
        if len(self.pts) > self.samples:
            self.pts.pop(0)
        self.energy = min(1.0, 0.35 + 0.65 * min(1.0, speed / 900.0))

    def update(self, dt):
        # bilah melambat di luar jendela aktif -> sampel basi dibuang pelan
        if not self.active and self.pts:
            for _ in range(2):
                if self.pts:
                    self.pts.pop(0)
        self.energy = max(0.0, self.energy - dt * 4.5)

    def clear(self):
        self.pts.clear()
        self.active = False
        self.energy = 0.0

    def draw(self, surface):
        n = len(self.pts)
        if n < 3 or self.energy <= 0.01:
            return
        e = self.energy
        # Ribbon: dua tepi di sepanjang jejak, lebar membesar ke ujung baru.
        left, right = [], []
        for i in range(n):
            x, y, sp = self.pts[i]
            t = i / (n - 1)
            if i > 0:
                px, py, _ = self.pts[i - 1]
                dx, dy = x - px, y - py
                d = math.hypot(dx, dy) or 1.0
            else:
                dx, dy = 1.0, 0.0
            nx, ny = -dy / d, dx / d
            w = (1.5 + t * 7.0 * e) * (0.5 + 0.5 * min(1.0, sp / 700.0))
            left.append((x + nx * w, y + ny * w))
            right.append((x - nx * w, y - ny * w))
        poly = left + list(reversed(right))
        for i in range(2, n):
            t = i / (n - 1)
            seg = [(poly[2 * (i - 1)], poly[2 * (i - 1) + 1],
                    poly[2 * i + 1], poly[2 * i])]
            a = int(95 * e * (t ** 1.4))
            if a < 6:
                continue
            pygame.draw.polygon(surface, (*_P["soul_mid"], a), seg)
        # Tepi dalam terang
        for i in range(1, n):
            t = i / (n - 1)
            a = int(150 * e * (t ** 1.6))
            if a < 8:
                continue
            pygame.draw.line(surface, (*_P["soul_bright"], a),
                             left[i - 1], left[i], max(1, int(1 + 2 * e * t)))
            pygame.draw.line(surface, (*_P["soul_bright"], a // 2),
                             right[i - 1], right[i], max(1, int(1 + e * t)))
        # Inti putih di ujung terbaru
        hx, hy, _ = self.pts[-1]
        a = int(200 * e)
        if a > 10:
            pygame.draw.circle(surface, (*_P["soul_hot"], a), (int(hx), int(hy)),
                               max(1, int(2 + 2 * e)))
        # Serpihan pixel di tepi ribbon
        if glow_allowed() and n >= 4:
            for i in range(1, n, 2):
                x, y, _ = self.pts[i]
                a = int(120 * e * (i / (n - 1)))
                if a < 10:
                    continue
                pygame.draw.rect(surface, (*_P["soul_light"], a),
                                 (int(x) + (i % 3) - 1, int(y) + (i % 2), 1, 1))


# ============================================================================
# 7.  IMPACT FX  (flash bintang + ring chunky; partikel lewat sistem)
# ============================================================================

class ImpactFX:
    """Flash benturan: bintang chunky memudar + cincin ekspansi."""

    def __init__(self, x, y, angle, power=1.0, crit=False, kind="soul",
                 ground=0.0, seed=0.0):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = max(0.3, min(2.2, float(power)))
        self.crit = bool(crit)
        self.kind = kind
        self.ground = float(ground)
        self.age = 0.0
        self.dur = 0.26 if not crit else 0.32
        self.seed = float(seed)

    @property
    def alive(self):
        return self.age < self.dur

    def t(self):
        return min(1.0, self.age / self.dur)

    def update(self, dt):
        self.age += dt

    def draw(self, surface):
        t = self.t()
        if t >= 1.0:
            return
        pw = self.power
        if self.kind == "void":
            base, hot = _P["void_bright"], _P["void_hot"]
        elif self.kind == "gold":
            base, hot = _P["gold_light"], _P["gold_shine"]
        else:
            base, hot = _P["soul_bright"], _P["soul_hot"]
        # Bintang flash (besar -> kecil cepat)
        if t < 0.45:
            k = 1.0 - t / 0.45
            r = int((8 + 14 * pw) * (0.5 + 0.5 * k))
            a = int(255 * k * (0.7 + 0.3 * min(1.0, pw)))
            if self.crit:
                _blit_faded(surface, flash_star(r + 8, hot), self.x, self.y,
                            a * 0.9, additive=True)
            _blit_faded(surface, flash_star(r, base), self.x, self.y, a,
                        additive=True)
            pygame.draw.circle(surface, (255, 255, 255, min(255, a)),
                               (int(self.x), int(self.y)),
                               max(1, int(2 + 3 * pw * k)))
        # Cincin chunky ekspansi
        if 0.10 < t < 0.9:
            rt = (t - 0.10) / 0.8
            r = int((10 + 26 * pw) * (0.35 + 0.65 * (1 - (1 - rt) ** 2)))
            a = int(200 * (1 - rt))
            if a > 8:
                segs = 10
                for i in range(segs):
                    a0 = self.seed + i * math.tau / segs
                    a1 = a0 + math.tau / segs * 0.6
                    p0 = (self.x + math.cos(a0) * r, self.y + math.sin(a0) * r)
                    p1 = (self.x + math.cos(a1) * r, self.y + math.sin(a1) * r)
                    pygame.draw.line(surface, (*base, a), p0, p1,
                                     max(2, int(3 * pw * (1 - rt * 0.5))))
        # Kilat mendatar di garis benturan
        if t < 0.3:
            a = int(220 * (1 - t / 0.3))
            ln = int((14 + 20 * pw) * (1 - t / 0.3 * 0.4))
            dx = math.cos(self.angle)
            dy = math.sin(self.angle)
            pygame.draw.line(surface, (255, 255, 255, a),
                             (self.x - dx * ln, self.y - dy * ln),
                             (self.x + dx * ln, self.y + dy * ln), 2)


# ============================================================================
# 8.  PROJECTILE  (soul bolt modular)
# ============================================================================

class SoulBolt:
    """Proyektil jiwa: inti + glow + bentuk directional + trail + partikel.

    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT (callback) ->
    DESTROY.  Mengejar target hidup (re-target) kalau ada.
    """

    def __init__(self, x, y, tx, ty, speed=BOLT_SPEED, damage=0,
                 target=None, radius=BOLT_RADIUS, kind="soul",
                 ground=0.0, on_impact=None):
        self.x = float(x)
        self.y = float(y)
        self.tx = float(tx)
        self.ty = float(ty)
        self.speed = float(speed)
        self.damage = float(damage)
        self.target = target
        self.radius = float(radius)
        self.kind = kind
        self.ground = float(ground)
        self.on_impact = on_impact
        self.age = 0.0
        self.lifetime = BOLT_LIFE
        self.wobble = random.uniform(0.0, math.tau)
        self.rotation = 0.0
        self.trail = []
        self.active = True
        self.hit_pos = None

    # ------------------------------------------------------------------
    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        # re-target: kejar target hidup
        tgt = self.target
        if tgt is not None and getattr(tgt, "alive", True):
            self.tx = float(getattr(tgt, "x", self.tx))
            self.ty = float(getattr(tgt, "y", self.ty) - 6.0)
        dx = self.tx - self.x
        dy = self.ty - self.y
        dist = math.hypot(dx, dy)
        if self.age > self.lifetime or dist < self.speed * dt + 4.0:
            self.x = self.tx
            self.y = self.ty
            self.active = False
            self.hit_pos = pygame.Vector2(self.tx, self.ty)
            if self.on_impact is not None:
                try:
                    self.on_impact(self)
                except Exception:              # pragma: no cover
                    pass
            return
        nx, ny = dx / dist, dy / dist
        self.rotation = math.atan2(dy, dx)
        self.wobble += dt * 9.0
        wob = math.sin(self.wobble) * 26.0 * dt
        self.x += nx * self.speed * dt - ny * wob
        self.y += ny * self.speed * dt + nx * wob
        # trail (sampel posisi, lama = memudar)
        self.trail.append((self.x, self.y, self.rotation))
        if len(self.trail) > 12:
            self.trail.pop(0)

    # ------------------------------------------------------------------
    def draw(self, surface):
        # Trail: jejak pita memudar + titik jiwa
        n = len(self.trail)
        for i in range(n):
            tx, ty, _ = self.trail[i]
            t = i / max(1, n - 1)
            a = int(70 * t ** 1.5)
            if a < 6:
                continue
            r = max(1, int(self.radius * 0.55 * t))
            pygame.draw.circle(surface, (*_P["soul_mid"], a), (int(tx), int(ty)), r)
            if glow_allowed() and i % 2 == 0:
                pygame.draw.circle(surface, (*_P["soul_bright"], a // 2),
                                   (int(tx), int(ty) - 1), max(1, r - 1))
        if not self.active:
            return
        px, py = int(self.x), int(self.y)
        ang = self.rotation
        # ekor (arah lawan gerak)
        bx = px - int(math.cos(ang) * 10)
        by = py - int(math.sin(ang) * 10)
        bx2 = px - int(math.cos(ang) * 17)
        by2 = py - int(math.sin(ang) * 17)
        if glow_allowed():
            _blit_faded(surface, glow_surface(14, _P["soul_mid"], 0.9),
                        px, py, 200, additive=True)
        pygame.draw.line(surface, (*_P["soul_dark"], 220), (px, py), (bx, by), 5)
        pygame.draw.line(surface, (*_P["soul_mid"], 235), (bx, by), (bx2, by2), 3)
        pygame.draw.line(surface, (*_P["soul_bright"], 200), (px, py), (bx, by), 3)
        # inti kepala-hantu (bentuk directional, bukan lingkaran polos)
        tipx = px + int(math.cos(ang) * 6)
        tipy = py + int(math.sin(ang) * 6)
        head_pts = [
            (tipx, tipy),
            (px + 2, py - 4), (px - 5, py - 4),
            (px - 6, py), (px - 5, py + 4), (px + 2, py + 4),
        ]
        pygame.draw.polygon(surface, (*_P["soul_light"], 255), head_pts)
        pygame.draw.polygon(surface, (*_P["soul_bright"], 255),
                            [(tipx, tipy), (px, py - 2), (px, py + 2)])
        # rongga mata + cahaya
        pygame.draw.circle(surface, (*_P["soul_dark"], 255),
                           (px + 1, py - 1), 1)
        pygame.draw.circle(surface, (*_P["soul_hot"], 255),
                           (px + 2, py - 1), 1)
        if glow_allowed():
            _blit_faded(surface, glow_surface(6, _P["soul_hot"], 1.0),
                        tipx, tipy, 160, additive=True)


class ProjectileSystem:
    """Manajer proyektil dengan cap keras."""

    def __init__(self, cap=MAX_PROJECTILES):
        self.cap = int(cap)
        self.bolts = []

    def count(self):
        return len(self.bolts)

    def spawn(self, x, y, tx, ty, speed=BOLT_SPEED, damage=0, target=None,
              radius=BOLT_RADIUS, kind="soul", ground=0.0, on_impact=None):
        if len(self.bolts) >= self.cap:
            self.bolts.pop(0)
        b = SoulBolt(x, y, tx, ty, speed=speed, damage=damage, target=target,
                     radius=radius, kind=kind, ground=ground,
                     on_impact=on_impact)
        self.bolts.append(b)
        return b

    def update(self, dt):
        if not self.bolts:
            return
        for b in self.bolts:
            b.update(dt)
        self.bolts = [b for b in self.bolts
                      if b.active or b.age < 0.25]

    def draw(self, surface):
        for b in self.bolts:
            b.draw(surface)

    def clear(self):
        self.bolts.clear()


# ============================================================================
# 9.  SKILL FX  (lifecycle: cast -> charge -> release -> area -> fade)
# ============================================================================

class SkillFX:
    """FX satu skill Krobellus.

    ``t01`` = progress 0..1 dari durasi skill; ``released`` ditandai saat
    fraksi release dilewati (spawn event sekali saja).
    """

    TINT = {
        'q': (_P["soul_bright"], _P["soul_mid"], _P["soul_hot"]),
        'w': (_P["void_bright"], _P["void_mid"], _P["void_hot"]),
        'e': (_P["soul_bright"], _P["soul_mid"], _P["soul_hot"]),
        'r': (_P["void_bright"], _P["void_mid"], _P["soul_hot"]),
    }

    def __init__(self, skill, x, y, particles, aim=None, ground=0.0,
                 projectiles=None, director=None, target=None):
        self.skill = skill
        self.x = float(x)
        self.y = float(y)
        self.particles = particles
        self.aim = aim
        self.ground = float(ground)
        self.projectiles = projectiles
        self.director = director
        self.target = target
        self.t01 = 0.0
        self.released = False
        self.age = 0.0
        self.dur = float(SKILL_DUR.get(skill, 60)) / 60.0
        self.tail = 0.55                      # detik sisa efek setelah durasi
        self._stream_acc = 0.0
        self._ghosts = []                     # ghost wave R: (cos, sin, delay, size)

    # ------------------------------------------------------------------
    def update(self, dt, boss_x, boss_y):
        self.age += dt
        self.x = float(boss_x)
        self.y = float(boss_y)
        # re-target (skill yang mengejar: w/e)
        if self.skill in ('w', 'e'):
            tgt = self.director._target_point() if self.director else None
            if tgt is not None and self.aim is not None:
                # W: bolt mengejar; E: titik tetap saat cast (desain siphon)
                if self.skill == 'w':
                    self.aim = (tgt[0], tgt[1])
        if not self.released:
            rel = SKILL_RELEASE.get(self.skill, 0.5)
            if self.t01 >= rel:
                self._release()
        # spawn kontinu (hanya selama skill masih berjalan)
        if self.skill == 'e' and self.t01 < 1.0 and self.aim is not None:
            self._stream_acc += dt * 26.0
            while self._stream_acc >= 1.0:
                self._stream_acc -= 1.0
                self._spawn_siphon_particle()
        if self.skill == 'q' and self.released:
            k = self.t01 - SKILL_RELEASE['q']
            if 0.0 <= k < 0.30 and random.random() < 0.5:
                a = random.uniform(0.0, math.tau)
                self.particles.burst(
                    self.x + math.cos(a) * 26, self.y - 8 + math.sin(a) * 10,
                    1, speed=(40, 120), life=(0.3, 0.6), size=(1.5, 3),
                    colors=(_P["soul_bright"], _P["soul_hot"]),
                    direction=a, spread=0.5, drag=1.5, shape="soul")

    # ------------------------------------------------------------------
    def _release(self):
        self.released = True
        if self.skill == 'q':
            # Ledakan cincin jiwa: blade-burst radial + guncangan
            if shake_allowed():
                _feel_shake(6.0, 0.18)
            _feel_hit_stop(HITSTOP_SKILL)
            n = int(14 * particle_budget())
            for i in range(max(1, n)):
                a = i * math.tau / max(1, n) + random.uniform(-0.1, 0.1)
                self.particles.spawn(
                    self.x + math.cos(a) * 18, self.y - 10 + math.sin(a) * 7,
                    math.cos(a) * 300, math.sin(a) * 130, 0.4, 3.2,
                    random.choice((_P["soul_bright"], _P["soul_hot"],
                                   _P["soul_white"])),
                    shape="streak", drag=3.4, additive=True)
            self.particles.burst(self.x, self.y - 8, int(10 * particle_budget()),
                                 speed=(120, 330), life=(0.25, 0.55),
                                 size=(1.5, 3.5),
                                 colors=(_P["soul_bright"], _P["soul_mid"],
                                         _P["soul_hot"]),
                                 spread=math.tau, drag=2.4, shape="soul")
            self.particles.burst(self.x, self.y + self.ground * 0.8,
                                 int(8 * particle_budget()),
                                 speed=(50, 160), life=(0.4, 0.8),
                                 size=(2, 5), colors=(_P["robe_mid"],
                                                      _P["soul_dark"]),
                                 spread=math.tau, gravity=160.0, drag=1.6,
                                 shape="dust", layer="back")
        elif self.skill == 'w':
            if self.projectiles is not None and self.aim is not None:
                tgt = self.director._target_point() if self.director else None
                tgt = tgt[2] if tgt else self.target
                self.projectiles.spawn(
                    self.x + 14, self.y - 18, self.aim[0], self.aim[1],
                    speed=BOLT_SPEED * 1.05, damage=0, target=tgt,
                    kind="void", ground=self.ground,
                    on_impact=lambda b: self.director._on_bolt_hit(
                        b, kind="void") if self.director is not None
                    else _bolt_impact(b, kind="void"))
            if shake_allowed():
                _feel_shake(4.5, 0.14)
        elif self.skill == 'r':
            # Erupsi crypt: gelombang hantu + puing + debu
            self._ghosts = []
            for i in range(12):
                a = i * math.tau / 12 + random.uniform(-0.15, 0.15)
                self._ghosts.append((math.cos(a), math.sin(a),
                                     random.uniform(0.0, 0.22),
                                     random.randint(5, 8)))
            self.particles.burst(self.x, self.y + self.ground * 0.85,
                                 int(16 * particle_budget()),
                                 speed=(90, 300), life=(0.3, 0.7),
                                 size=(2, 5),
                                 colors=(_P["void_mid"], _P["void_dark"],
                                         _P["shadow_deep"]),
                                 spread=math.tau, gravity=260.0, drag=1.2,
                                 shape="shard", rotation_speed=(-14, 14))
            self.particles.burst(self.x, self.y + self.ground * 0.85,
                                 int(14 * particle_budget()),
                                 speed=(40, 140), life=(0.5, 1.0),
                                 size=(3, 7), colors=(_P["void_dark"],
                                                      _P["shadow_deep"]),
                                 spread=math.tau, gravity=60.0, drag=1.4,
                                 shape="dust", layer="back")
            _feel_shake(13.0, 0.40)
            _feel_hit_stop(HITSTOP_R)
        elif self.skill == 'e':
            self.particles.burst(self.x + 16, self.y - 18,
                                 int(8 * particle_budget()),
                                 speed=(60, 180), life=(0.25, 0.5),
                                 size=(1.5, 3),
                                 colors=(_P["soul_bright"], _P["soul_hot"]),
                                 spread=math.tau, drag=2.0, shape="soul")

    # ------------------------------------------------------------------
    def _spawn_siphon_particle(self):
        """Partikel jiwa mengalir DARI target KE Krobellus."""
        if self.aim is None:
            return
        tx, ty = self.aim
        hx, hy = self.x + 16, self.y - 18
        t = random.uniform(0.75, 1.0)      # mulai dekat Krobellus
        px = tx + (hx - tx) * t
        py = ty + (hy - ty) * t
        dx, dy = hx - tx, hy - ty
        d = math.hypot(dx, dy) or 1.0
        sp = 240.0
        self.particles.spawn(px, py, dx / d * sp + random.uniform(-24, 24),
                             dy / d * sp + random.uniform(-24, 24),
                             0.45, 2.6,
                             random.choice((_P["soul_light"],
                                            _P["soul_bright"],
                                            _P["soul_hot"])),
                             shape="soul", drag=0.4)

    # ------------------------------------------------------------------
    @property
    def done(self):
        return self.age > self.dur + self.tail

    # ------------------------------------------------------------------
    def draw(self, surface):
        t = self.t01
        bright, mid, hot = self.TINT.get(self.skill, self.TINT['q'])
        if self.skill == 'q':
            self._draw_q(surface, t, bright, mid, hot)
        elif self.skill == 'w':
            self._draw_w(surface, t, bright, mid, hot)
        elif self.skill == 'e':
            self._draw_e(surface, t, bright, mid, hot)
        elif self.skill == 'r':
            self._draw_r(surface, t, bright, mid, hot)

    # --- Q: EXORCISM -----------------------------------------------------
    def _draw_q(self, s, t, bright, mid, hot):
        rel = SKILL_RELEASE['q']
        if t < rel:
            # charge: spiral jiwa menyatu ke sabit
            k = t / rel
            for i in range(7):
                a = self.age * 5.0 + i * math.tau / 7
                r = 46 * (1 - k) + 12
                px = self.x + math.cos(a) * r
                py = self.y - 12 + math.sin(a) * r * 0.5
                a2 = int(220 * (0.4 + 0.6 * k))
                pygame.draw.circle(s, (*mid, a2), (int(px), int(py)), 2)
                pygame.draw.circle(s, (*hot, a2), (int(px), int(py) - 1), 1)
        else:
            # area: gelombang cincin memudar
            k = min(1.0, (t - rel) / 0.45)
            r = int(20 + 90 * (1 - (1 - k) ** 2))
            a = int(200 * (1 - k))
            if a > 6:
                segs = 14
                for i in range(segs):
                    a0 = i * math.tau / segs
                    a1 = a0 + math.tau / segs * 0.55
                    p0 = (self.x + math.cos(a0) * r,
                          self.y - 10 + math.sin(a0) * r * 0.45)
                    p1 = (self.x + math.cos(a1) * r,
                          self.y - 10 + math.sin(a1) * r * 0.45)
                    pygame.draw.line(s, (*bright, a), p0, p1,
                                     max(2, int(4 * (1 - k))))
            a2 = int(120 * (1 - k))
            if a2 > 6:
                pygame.draw.ellipse(s, (*mid, a2),
                                    (int(self.x - r), int(self.y + 6),
                                     int(r * 2), int(r * 0.5)))

    # --- W: SILENCE -------------------------------------------------------
    def _draw_w(self, s, t, bright, mid, hot):
        rel = SKILL_RELEASE['w']
        hx, hy = self.x + 14, self.y - 18
        if t < rel:
            # orb ungu membesar di tangan
            k = t / rel
            r = int(3 + 9 * k)
            pulse = 0.75 + 0.25 * math.sin(self.age * 14.0)
            if glow_allowed():
                _blit_faded(s, glow_surface(r + 8, mid, 0.9), hx, hy,
                            int(190 * k * pulse), additive=True)
            pygame.draw.circle(s, (*darken(mid, 0.6), 235), (int(hx), int(hy)), r)
            pygame.draw.circle(s, (*bright, 255), (int(hx), int(hy)), max(1, r - 3))
            pygame.draw.circle(s, (*hot, 255), (int(hx) - 1, int(hy) - 1),
                               max(1, r - 5))
            # percikan konvergensi
            for i in range(5):
                a = self.age * 6.0 + i * math.tau / 5
                rr = (26 - 20 * k)
                px = hx + math.cos(a) * rr
                py = hy + math.sin(a) * rr
                pygame.draw.circle(s, (*bright, int(200 * k)), (int(px), int(py)), 1)
        elif self.aim is not None:
            # zona hening di titik target (setelah bolt mendarat ditangani
            # impact; di sini telegraph hex memudar)
            tx, ty = self.aim
            k = min(1.0, (t - rel) / 0.5)
            a = int(150 * (1 - k))
            if a > 6:
                for i in range(6):
                    a0 = self.age * 0.8 + i * math.tau / 6
                    a1 = a0 + math.tau / 6 * 0.6
                    r = 16 + 10 * k
                    p0 = (tx + math.cos(a0) * r, ty + math.sin(a0) * r * 0.5)
                    p1 = (tx + math.cos(a1) * r, ty + math.sin(a1) * r * 0.5)
                    pygame.draw.line(s, (*bright, a), p0, p1, 2)
                pygame.draw.ellipse(s, (*mid, a // 2),
                                    (int(tx - 22), int(ty - 9), 44, 18))

    # --- E: SPIRIT SIPHON ---------------------------------------------------
    def _draw_e(self, s, t, bright, mid, hot):
        if self.aim is None:
            return
        tx, ty = self.aim
        hx, hy = self.x + 16, self.y - 18
        # garis arus halus (2 lapis, bergelombang)
        dx, dy = hx - tx, hy - ty
        dist = math.hypot(dx, dy) or 1.0
        segs = max(4, int(dist / 12))
        for layer in range(2):
            for i in range(segs + 1):
                tt = i / segs
                wave = math.sin(tt * math.pi * 3.0 + self.age * (5.0 + layer * 2.0))
                off = (6.0 - layer * 5.0)
                px = tx + dx * tt + (-dy / dist) * wave * off
                py = ty + dy * tt + (dx / dist) * wave * off
                a = int(120 + 60 * math.sin(tt * math.tau + self.age * 8.0))
                ccol = mid if layer else bright
                pygame.draw.circle(s, (*ccol, max(40, a)),
                                   (int(px), int(py)), max(1, 2 - layer))
        # vortex pengisap di target
        pulse = 0.7 + 0.3 * math.sin(self.age * 6.0)
        for i in range(3):
            r = int((5 + i * 6) * pulse)
            a = int(170 - i * 45)
            ccol = bright if i == 0 else mid
            segs = 8
            for j in range(segs):
                a0 = self.age * (2.0 + i) + j * math.tau / segs
                a1 = a0 + math.tau / segs * 0.5
                p0 = (tx + math.cos(a0) * r, ty + math.sin(a0) * r * 0.7)
                p1 = (tx + math.cos(a1) * r, ty + math.sin(a1) * r * 0.7)
                pygame.draw.line(s, (*ccol, a), p0, p1, max(1, 3 - i))
        # heal glow di sisi Krobellus
        if glow_allowed():
            _blit_faded(s, glow_surface(16, mid, 0.8), hx, hy,
                        int(150 * pulse), additive=True)
        pygame.draw.circle(s, (*bright, int(200 * pulse)), (int(hx), int(hy)), 3)
        pygame.draw.circle(s, (*hot, 235), (int(hx), int(hy)), 1)

    # --- R: CRYPT SWARM ------------------------------------------------------
    def _draw_r(self, s, t, bright, mid, hot):
        rel = SKILL_RELEASE['r']
        gy = self.y + self.ground * 0.85
        if t < rel:
            # charge: celah tanah menyala + abu terangkat
            k = t / rel
            for i in range(6):
                a = i * math.tau / 6 + self.age
                r = 34
                px = self.x + math.cos(a) * r * (0.4 + 0.6 * k)
                py = gy + math.sin(a) * r * 0.32 * (0.4 + 0.6 * k)
                a2 = int(200 * k)
                pygame.draw.line(s, (*mid, a2),
                                 (int(self.x + math.cos(a) * r * 0.45),
                                  int(gy + math.sin(a) * r * 0.15)),
                                 (int(px), int(py)), 2)
            if glow_allowed():
                _blit_faded(s, glow_surface(int(30 + 14 * k), mid, 0.7),
                            self.x, gy, int(120 * k), additive=True)
        else:
            k = min(1.0, (t - rel) / 0.55)
            # ring erupsi ganda
            for i, frac in enumerate((0.0, 0.28)):
                rk = max(0.0, min(1.0, (k - frac) / 0.55))
                if rk <= 0.0 or rk >= 1.0:
                    continue
                r = int((16 + 64 * i) * (0.3 + 0.7 * (1 - (1 - rk) ** 2)))
                a = int(190 * (1 - rk))
                if a > 6:
                    ccol = bright if i == 0 else mid
                    segs = 12
                    for j in range(segs):
                        a0 = j * math.tau / segs + i * 0.26
                        a1 = a0 + math.tau / segs * 0.6
                        p0 = (self.x + math.cos(a0) * r,
                              gy + math.sin(a0) * r * 0.4)
                        p1 = (self.x + math.cos(a1) * r,
                              gy + math.sin(a1) * r * 0.4)
                        pygame.draw.line(s, (*ccol, a), p0, p1,
                                         max(2, int(4 * (1 - rk))))
            # gelombang hantu naik
            for cos_a, sin_a, delay, size in self._ghosts:
                if k < delay:
                    continue
                gk = min(1.0, (k - delay) / (1.0 - delay))
                rise = gk * 44.0
                gx = self.x + cos_a * (30 + 26 * gk)
                gy2 = gy - rise + math.sin(self.age * 3.0 + cos_a * 6.0) * 2.5
                a = int(230 * min(1.0, gk * 3.0) * (1.0 - 0.35 * k))
                if a < 8:
                    continue
                spr = ghost_sprite(size)
                _blit_faded(s, spr, gx, gy2, a)
            # pita kegelapan naik
            if glow_allowed():
                _blit_faded(s, glow_surface(46, mid, 0.55), self.x, gy,
                            int(140 * (1 - k)), additive=True)


def darken(color, k):
    return (max(0, int(color[0] * k)), max(0, int(color[1] * k)),
            max(0, int(color[2] * k)))


def _bolt_impact(bolt, kind="void"):
    """Fallback mendaratnya soul bolt saat tidak ada director (test ringan).

    Impact penuh lewat registry; kalau memang tidak ada satu pun director
    (modul dipanggil langsung dari alat uji), beri shake + hit-stop kecil.
    """
    x = bolt.hit_pos.x if bolt.hit_pos else bolt.x
    y = bolt.hit_pos.y if bolt.hit_pos else bolt.y
    for d in _DIRECTORS:
        if any(b is bolt for b in d.projectiles.bolts):
            d.on_impact(x, y, bolt.rotation, 1.15, False, kind=kind)
            return
    if shake_allowed():
        _feel_shake(4.0, 0.15)
    _feel_hit_stop(HITSTOP_BOLT)


# ============================================================================
# 10. DIRECTOR  (satu instance per unit)
# ============================================================================

class KrobellusFXDirector:
    """Ikatan semua sistem FX untuk satu unit Krobellus."""

    def __init__(self, hero):
        self.hero = hero
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.trail = SwingTrail()
        self.projectiles = ProjectileSystem()
        self.skills = []
        self.impacts = []
        self.hit_flash = 0.0
        # tracking serangan
        self._cycle = 0
        self._prev_progress = -1.0
        self._bolt_spawned = False
        self._impact_done = False
        self._air_done = False
        self._pending_impact = None      # (tx, ty, angle, power, crit, kind)
        # tracking skill
        self._cur_skill = None
        self._prev_skill = None
        self._prev_skill_timer = -1
        self._prev_hurt = 0
        self._fps_acc = 0.0
        self._fps_n = 0
        self.fps = 60.0

    # ------------------------------------------------------------------
    def _attack_state(self):
        h = self.hero
        active = bool(getattr(h, "_krb_attack_active", False))
        progress = float(getattr(h, "_krb_attack_progress", 0.0) or 0.0)
        kind = getattr(h, "_krb_attack_kind", "swing") or "swing"
        return active, max(0.0, min(1.0, progress)), kind

    def _target_point(self):
        h = self.hero
        tgt = getattr(h, "target", None)
        if tgt is not None and getattr(tgt, "alive", True):
            return (float(getattr(tgt, "x", 0.0)),
                    float(getattr(tgt, "y", 0.0) - 6.0), tgt)
        return None

    # ------------------------------------------------------------------
    def update(self, dt, x, y):
        h = self.hero
        # FPS
        self._fps_acc += dt
        self._fps_n += 1
        if self._fps_acc >= 0.5:
            self.fps = self._fps_n / self._fps_acc
            self._fps_acc = 0.0
            self._fps_n = 0

        # HURT
        hurt = int(getattr(h, "hurt_flash_timer", 0) or 0)
        if hurt >= 5 and hurt > self._prev_hurt:
            self.on_hurt(1.0)
        self._prev_hurt = hurt
        self.hit_flash = max(0.0, self.hit_flash - dt * 6.5)

        # SERANGAN
        active, progress, kind = self._attack_state()
        if active and self._prev_progress >= 0.0 and \
                progress < self._prev_progress - 0.5:
            # wrap cycle baru
            self._cycle += 1
            self._bolt_spawned = False
            self._impact_done = False
            self._air_done = False
            self._pending_impact = None
        self._prev_progress = progress if active else -1.0

        if active:
            tp = self._target_point()
            if kind == "bolt" and not self._bolt_spawned and \
                    progress >= ATK_RELEASE:
                self._bolt_spawned = True
                # LANE GATE: di jalur hero (punya _render_scale) proyektil
                # generik gameplay SUDAH terbang sebagai visual — soul bolt
                # prosedural ini hanya untuk jalur boss yang tidak punya
                # proyektil generik (dampak ganda bila dua-duanya digambar).
                if getattr(h, "_render_scale", None) is None:
                    self._spawn_attack_bolt(x, y, tp)
            if kind == "swing" and not self._impact_done and \
                    progress >= ATK_IMPACT:
                self._impact_done = True
                self._on_swing_impact_frame(x, y, tp)
            # trail: sampel posisi bilah selama jendela cepat
            pivot, tip = scythe_points(h, x, y)
            fast = 0.26 <= progress <= 0.62
            if fast:
                speed = 900.0 * (1.0 if kind == "swing" else 0.5)
            else:
                speed = 120.0
            self.trail.add_sample(tip.x, tip.y, speed, fast)
        else:
            self.trail.add_sample(0, 0, 0.0, False)

        # SKILL (deteksi edge dari state boss)
        skill = getattr(h, "active_skill", None)
        if skill is None and getattr(h, "ability_active", False) and \
                int(getattr(h, "ability_active_timer", 0) or 0) > 0:
            skill = 'q'      # jalur boss generik
        timer = 0
        if skill:
            timer = int(getattr(h, "active_skill_timer", 0) or 0)
            if timer <= 0 and skill == 'q' and \
                    getattr(h, "active_skill", None) is None:
                timer = int(getattr(h, "ability_active_timer", 0) or 0)
        if skill != self._prev_skill:
            if skill is not None and not any(
                    fx.skill == skill for fx in self.skills):
                # DE-DUPE: notify_skill_cast (jalur hero/boss) biasanya
                # sudah membuat SkillFX; jangan buat yang kedua.
                self.on_cast(x, y, skill)
            self._cur_skill = skill
            if skill is not None and timer > 0:
                self._skill_total = max(1, timer)
        elif skill is not None:
            self._skill_total = max(getattr(self, "_skill_total", 1), timer)
        self._prev_skill = skill
        self._prev_skill_timer = timer

        # update progress + event skill (SEMUA fx dimajukan supaya yang
        # sudah selesai tetap memudar & dibuang — anti-kebocoran)
        for fx in self.skills:
            if fx.skill == self._cur_skill and self._cur_skill is not None:
                total = getattr(self, "_skill_total",
                                SKILL_DUR.get(fx.skill, 60))
                fx.t01 = max(0.0, min(1.0,
                                      1.0 - timer / float(max(1, total))))
            else:
                fx.t01 = 1.0
            fx.update(dt, x, y)

        # system
        self.trail.update(dt)
        self.projectiles.update(dt)
        self.particles.update(dt)
        for im in self.impacts:
            im.update(dt)
        self.impacts = [im for im in self.impacts if im.alive]
        self.skills = [fx for fx in self.skills if not fx.done]

    # ------------------------------------------------------------------
    def _spawn_attack_bolt(self, x, y, tp):
        h = self.hero
        _pivot, tip = scythe_points(h, x, y)
        if tp is None:
            f = 1 if (getattr(h, "direction", 1) or 1) >= 0 else -1
            aim = (x + f * 130.0, y - 8.0)
            tgt = None
        else:
            aim = (tp[0], tp[1])
            tgt = tp[2]
        self.projectiles.spawn(
            tip.x, tip.y, aim[0], aim[1], speed=BOLT_SPEED, damage=0,
            target=tgt, kind="soul", ground=ground_dy(h),
            on_impact=lambda b: self._on_bolt_hit(b))
        self.particles.burst(tip.x, tip.y, 6, speed=(90, 220),
                             life=(0.12, 0.3), size=(1.5, 3),
                             colors=(_P["soul_white"], _P["soul_bright"]),
                             spread=1.9, drag=3.2, shape="spark",
                             additive=True)

    def _on_bolt_hit(self, bolt, kind="soul"):
        """Soul bolt mendarat: impact penuh + lepas pending notify."""
        hp = bolt.hit_pos
        self.on_impact(hp.x, hp.y, bolt.rotation, 1.1, False, kind=kind)
        self._impact_done = True
        self._pending_impact = None

    def _on_swing_impact_frame(self, x, y, tp):
        """Frame bilah menyentuh: full impact kalau target di dalam busur."""
        h = self.hero
        _pivot, tip = scythe_points(h, x, y)
        f = 1 if (getattr(h, "direction", 1) or 1) >= 0 else -1
        hit = False
        if tp is not None:
            tx, ty = tp[0], tp[1]
            dist = math.hypot(tx - x, ty - y)
            # harus di depan badan (cone)
            front = (tx - x) * f
            if dist <= MELEE_REACH + 18.0 and front > -18.0:
                self.on_impact(tx, ty, math.atan2(ty - (y - 10), tx - x),
                               1.2, False, kind="soul")
                hit = True
        if not hit:
            # sapuan udara di ujung bilah (feedback ringan, tanpa freeze)
            if not self._air_done:
                self._air_done = True
                ang = math.atan2(tip.y - y, tip.x - x)
                self.particles.burst(
                    tip.x, tip.y, 6, speed=(110, 240), life=(0.1, 0.24),
                    size=(1.5, 3),
                    colors=(_P["soul_bright"], _P["soul_hot"]),
                    spread=1.5, direction=ang, drag=3.4, shape="streak",
                    additive=True)
                if len(self.impacts) < MAX_IMPACTS:
                    self.impacts.append(ImpactFX(tip.x, tip.y, ang, 0.5,
                                                 False, kind="soul"))
        # pending notify (dari damage hook) dilepas di sini — sinkron visual
        if self._pending_impact is not None:
            self._pending_impact = None

    # ------------------------------------------------------------------
    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="soul"):
        """Benturan penuh: flash + ring + percikan + serpihan + shake +
        hit-stop (dijepit 0.03-0.08 s oleh bus)."""
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind=kind))
        pw = min(2.0, max(0.35, float(power)))
        if kind == "void":
            spark, edge, hot = _P["void_bright"], _P["void_mid"], _P["void_hot"]
        elif kind == "gold":
            spark, edge, hot = _P["gold_light"], _P["gold_mid"], _P["gold_shine"]
        else:
            spark, edge, hot = _P["soul_bright"], _P["soul_mid"], _P["soul_hot"]
        n = int(9 + 7 * pw) + (6 if crit else 0)
        self.particles.burst(
            x, y, n, speed=(120, 330 + 90 * pw), life=(0.16, 0.42),
            size=(2, 4), colors=(spark, hot, edge),
            spread=2.4, direction=angle, drag=3.6, shape="streak",
            additive=True)
        self.particles.burst(
            x, y, int(5 + 3 * pw) + (4 if crit else 0),
            speed=(70, 200), life=(0.3, 0.66), size=(2, 5),
            colors=(edge, _P["soul_dark"], _P["robe_mid"]),
            gravity=470.0, drag=1.1, shape="shard",
            rotation_speed=(-16.0, 16.0))
        self.particles.burst(
            x, y, int(4 + 3 * pw), speed=(40, 140), life=(0.4, 0.8),
            size=(1.5, 3.5), colors=(spark, _P["soul_light"]),
            spread=math.tau, gravity=-60.0, drag=1.6, shape="soul")
        if crit:
            self.particles.burst(
                x, y, 8, speed=(180, 380), life=(0.22, 0.5), size=(2, 4),
                colors=(spark, hot), spread=math.tau, gravity=120.0,
                drag=2.0, shape="spark", additive=True)
        if shake_allowed():
            _feel_shake(4.0 + 3.4 * pw + (3.0 if crit else 0.0),
                        0.17 + 0.08 * pw)
        if kind == "void":
            _feel_hit_stop(HITSTOP_SKILL)
        elif crit:
            _feel_hit_stop(min(0.08, 0.045 + 0.019 * min(1.5, pw) + 0.014))
        else:
            _feel_hit_stop(min(0.08, 0.036 + 0.019 * min(1.5, pw)))

    def on_hurt(self, amount=1.0):
        """Krobellus terkena: flash + serpihan jiwa terlempar."""
        h = self.hero
        x = float(getattr(h, "x", 0.0))
        y = float(getattr(h, "y", 0.0))
        f = 1 if (getattr(h, "direction", 1) or 1) >= 0 else -1
        self.hit_flash = 0.16
        self.particles.burst(
            x, y - 14, int(8 * particle_budget()),
            speed=(90, 240), life=(0.2, 0.5), size=(1.5, 3),
            colors=(_P["soul_bright"], _P["soul_light"], _P["eye_bright"]),
            spread=2.2, direction=math.pi * (0.5 if f > 0 else -0.5),
            drag=2.4, shape="soul")
        self.particles.burst(
            x, y + 10, int(5 * particle_budget()),
            speed=(40, 120), life=(0.35, 0.7), size=(2, 4),
            colors=(_P["robe_mid"], _P["shadow"]),
            gravity=220.0, drag=1.2, shape="shard",
            rotation_speed=(-10, 10))

    def on_cast(self, x, y, skill, aim=None):
        """Skill mulai: buat SkillFX + guncangan + (R) beat freeze."""
        if skill not in SKILL_DUR:
            return
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        h = self.hero
        if aim is None:
            tgt = self._target_point()
            if tgt is not None:
                aim = (tgt[0], tgt[1])
            else:
                f = 1 if (getattr(h, "direction", 1) or 1) >= 0 else -1
                aim = (x + f * 120.0, y - 8.0)
        tp = self._target_point()
        fx = SkillFX(skill, x, y, self.particles, aim=aim,
                     ground=ground_dy(h), projectiles=self.projectiles,
                     director=self, target=tp[2] if tp else None)
        # E: target dikunci saat cast (stream mengarah ke titik awal)
        if skill == 'e' and tp is not None:
            fx.aim = (tp[0], tp[1])
        self.skills.append(fx)
        heavy = skill == 'r'
        if shake_allowed():
            _feel_shake(6.0 if not heavy else 10.0,
                        0.16 if not heavy else 0.30)
        if heavy:
            _feel_hit_stop(HITSTOP_R)
        self.particles.burst(
            x, y + ground_dy(h) * 0.4, 10,
            speed=(60, 190), life=(0.2, 0.5), size=(2, 4),
            colors=(_P["soul_dark"], _P["robe_fade"], _P["shadow"]),
            spread=math.tau, gravity=150.0, drag=2.0, shape="dust",
            layer="back")

    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        """Pre-pass: telegraph tanah + partikel layer belakang."""
        h = self.hero
        x = float(getattr(h, "x", 0.0))
        y = float(getattr(h, "y", 0.0))
        skill = self._cur_skill
        if skill in ('q', 'r') and self._prev_skill_timer > 0:
            timer = self._prev_skill_timer
            total = getattr(self, "_skill_total", SKILL_DUR.get(skill, 60))
            t = 1.0 - timer / float(max(1, total))
            gy = y + ground_dy(h) * 0.85
            if skill == 'q':
                r = int(24 + 60 * min(1.0, t / SKILL_RELEASE['q']))
                a = int(110 * (0.4 + 0.6 * min(1.0, t / SKILL_RELEASE['q'])))
                pygame.draw.ellipse(surface, (*_P["soul_mid"], a),
                                    (int(x - r), int(gy - r * 0.22),
                                     int(r * 2), int(r * 0.44)), 2)
                pygame.draw.ellipse(surface, (*_P["soul_dark"], a // 2),
                                    (int(x - r * 0.7), int(gy - r * 0.15),
                                     int(r * 1.4), int(r * 0.3)))
            else:
                r = int(30 + 46 * min(1.0, t / SKILL_RELEASE['r']))
                a = int(130 * min(1.0, t / SKILL_RELEASE['r']))
                pygame.draw.ellipse(surface, (*_P["void_dark"], a),
                                    (int(x - r), int(gy - r * 0.3),
                                     int(r * 2), int(r * 0.6)), 3)
                pygame.draw.ellipse(surface, (*_P["void_mid"], a // 2),
                                    (int(x - r * 0.65), int(gy - r * 0.2),
                                     int(r * 1.3), int(r * 0.4)))
        self.particles.draw(surface, layer="back")

    def draw_front(self, surface, x, y):
        """Post-pass: trail, proyektil, skill, impact, partikel depan."""
        # trail bilah
        self.trail.draw(surface)
        # proyektil
        self.projectiles.draw(surface)
        # skill FX
        for fx in self.skills:
            fx.draw(surface)
        # impact
        for im in self.impacts:
            im.draw(surface)
        # partikel depan
        self.particles.draw(surface, layer="front")
        # flash kena damage (ring putih di badan)
        if self.hit_flash > 0.01:
            a = int(140 * min(1.0, self.hit_flash / 0.16))
            if a > 4:
                h = self.hero
                r = int((20 + 8 * body_scale(h)) * 1.2)
                pygame.draw.ellipse(surface, (255, 255, 255, a),
                                    (int(x - r * 0.8), int(y - 46),
                                     int(r * 1.6), int(r * 2.2)), 2)
        # debug
        if DEBUG_CHARACTER:
            draw_debug_overlay(surface, self, x, y)

    # ------------------------------------------------------------------
    def clear(self):
        self.particles.clear()
        self.trail.clear()
        self.projectiles.clear()
        self.skills.clear()
        self.impacts.clear()
        self.hit_flash = 0.0
        self._pending_impact = None


# ============================================================================
# 11. REGISTRY & TICK
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Krobellus."""
    _sync_palette()
    d = getattr(hero, "_krb_fx", None)
    if d is None:
        d = KrobellusFXDirector(hero)
        try:
            hero._krb_fx = d
        except Exception:                      # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:               # jangkar tua dibuang
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    try:
        if director.hero is not None:
            director.hero._krb_fx = None
            director.hero._krb_live_fx = False
    except Exception:                          # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit ini. Return True kalau aktif."""
    if not KROBELLS_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                          # pragma: no cover
        return False
    try:
        hero._krb_live_fx = True
    except Exception:                          # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not getattr(hero, "_krb_live_fx", False):
        return False
    d = getattr(hero, "_krb_fx", None)
    return d is not None and d in _DIRECTORS


def tick(dt=None):
    """Majukan waktu FX satu frame nyata; aman dipanggil berkali-kali."""
    global _LAST_TICK_MS
    if dt is not None:
        step = max(0.0, min(1.0 / 20.0, float(dt)))
        _advance(step)
        return step
    now = pygame.time.get_ticks()
    if now == _LAST_TICK_MS:
        return 0.0                             # frame sama: sudah maju
    if _feel is not None:
        _LAST_TICK_MS = now
        try:
            step = _feel.fx_dt()
        except Exception:                      # pragma: no cover
            step = 0.0
    else:                                      # pragma: no cover - fallback
        if _LAST_TICK_MS is None:
            _LAST_TICK_MS = now
            return 0.0
        ms = now - _LAST_TICK_MS
        _LAST_TICK_MS = now
        if ms <= 0:
            return 0.0
        step = max(1.0 / 240.0, min(1.0 / 20.0, ms / 1000.0))
        if _feel is not None and getattr(_feel, "HITSTOP", None) is not None:
            step *= 0.18
    _advance(step)
    return step


def _advance(step):
    if step <= 0.0 or not _DIRECTORS:
        return
    for d in list(_DIRECTORS):
        h = d.hero
        if h is None:
            continue
        d.update(step, float(getattr(h, "x", 0.0)),
                 float(getattr(h, "y", 0.0)))


def reset_all():
    """Bersihkan seluruh state FX Krobellus (ganti level / keluar match)."""
    global _LAST_TICK_MS
    _LAST_TICK_MS = None
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()


def total_particles():
    """Jumlah partikel Krobellus hidup di seluruh arena (HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


# ============================================================================
# 12. HOOK LAYAR (dipanggil heroes/__init__.py + bosses/level5.py)
# ============================================================================

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: digambar SEBELUM sprite di-blit."""
    if not KROBELLS_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_krb_fx", None)
    if d is not None:
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: digambar SESUDAH sprite di-blit."""
    if not KROBELLS_FX_ENABLED:
        return
    d = director_for(hero)
    d.draw_front(surface, int(x), int(y))


# ============================================================================
# 13. HOOK GAMEPLAY (_entity.py / bosses/base_boss.py / hero_skills)
# ============================================================================

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Sabit Krobellus mendarat di target (basic attack swing).

    Kalau ayunan masih di awal cycle (damage hook lebih dulu dari frame
    visual benturan), impact DITAHAN sampai frame bilah menyentuh —
    jadi flash & hit-stop sinkron dengan mata pedang.
    """
    if not KROBELLS_FX_ENABLED or hero is None or target is None:
        return
    try:
        power = 0.75 + min(1.5, float(damage) / 70.0)
    except (TypeError, ValueError):
        power = 1.0
    tx = float(getattr(target, "x", getattr(hero, "x", 0.0)))
    ty = float(getattr(target, "y", getattr(hero, "y", 0.0))) - 6.0
    ang = math.atan2(ty - float(getattr(hero, "y", 0.0)),
                     tx - float(getattr(hero, "x", 0.0)))
    d = director_for(hero)
    active, progress, kind = d._attack_state()
    if active and kind == "swing" and progress < ATK_IMPACT:
        d._pending_impact = (tx, ty, ang, power, bool(crit), "soul")
        return
    d.on_impact(tx, ty, ang, power, bool(crit), kind="soul")
    d._pending_impact = None


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False,
                             kind="soul"):
    """Soul bolt mengenai target (basic attack jarak jauh)."""
    if not KROBELLS_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    d = director_for(hero)
    active, progress, atk_kind = d._attack_state()
    hero_lane = getattr(hero, "_render_scale", None) is not None
    if not hero_lane and active and atk_kind == "bolt" \
            and progress < ATK_RELEASE + 0.1:
        # Jalur BOSS: damage instan, impact visual ditahan sampai soul
        # bolt prosedural mendarat.
        d._pending_impact = (float(x), float(y), float(angle), power,
                             bool(crit), kind)
        return
    if hero_lane and active and atk_kind == "swing":
        # Jalur HERO (swing mode): damage lewat proyektil generik yang
        # mendarat SEBELUM frame benturan bilah. Tunda sampai frame
        # benturan (dilepas _on_swing_impact_frame, yang juga memicu
        # impact penuh) supaya tidak ada impact ganda / impact maju.
        d._pending_impact = (float(x), float(y), float(angle), power,
                             bool(crit), kind)
        return
    # Jalur hero (bolt mode) / kasus lain: proyektil generik mendarat
    # SEKARANG = benturan visual; impact langsung.
    d.on_impact(float(x), float(y), float(angle), power, bool(crit),
                kind=kind)
    d._pending_impact = None


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """Skill Krobellus meledak di sebuah titik (Q/W/E AOE)."""
    if not KROBELLS_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    # pastikan SkillFX ada (jalur state boss biasanya sudah membuatnya)
    if not any(fx.skill == skill for fx in d.skills):
        d.on_cast(float(getattr(hero, "x", x)),
                  float(getattr(hero, "y", y)), skill,
                  aim=(float(x), float(y)))
    kind = "void" if skill in ('w', 'r') else "soul"
    d.on_impact(float(x), float(y), 0.0,
                1.4 if skill != 'r' else 1.8, skill == 'r', kind=kind)


def notify_skill_cast(hero, skill):
    """Dipanggil jalur gameplay saat skill dilepas (opsional)."""
    if not KROBELLS_FX_ENABLED or hero is None or skill not in SKILL_DUR:
        return
    d = director_for(hero)
    if any(fx.skill == skill for fx in d.skills):
        return
    d.on_cast(float(getattr(hero, "x", 0.0)),
              float(getattr(hero, "y", 0.0)), skill)


# ============================================================================
# 14. GAME FEEL (meneruskan ke bus global)
# ============================================================================

def _feel_shake(strength, duration):
    if _feel is not None:
        try:
            _feel.shake(strength, duration)
            return
        except Exception:                      # pragma: no cover
            pass
    try:
        import __main__
        game = getattr(__main__, "game_instance", None)
        if game is not None and getattr(game, "effects", None) is not None:
            game.effects.shake_screen(int(strength))
    except Exception:                          # pragma: no cover
        pass


def _feel_hit_stop(seconds):
    if _feel is not None:
        try:
            _feel.hit_stop(seconds)
            return
        except Exception:                      # pragma: no cover
            pass


def should_freeze_frame():
    if _feel is not None:
        try:
            return bool(_feel.should_freeze_frame())
        except Exception:                      # pragma: no cover
            return False
    return False


def hit_stop(seconds=0.045):
    _feel_hit_stop(seconds)


def shake(strength=5.0, duration=0.22):
    _feel_shake(strength, duration)


# ============================================================================
# 15. DEBUG OVERLAY
# ============================================================================

_DEBUG_FONT = None


def _debug_font():
    global _DEBUG_FONT
    if _DEBUG_FONT is None:
        try:
            _DEBUG_FONT = pygame.font.SysFont("monospace", 11)
        except Exception:                      # pragma: no cover
            _DEBUG_FONT = None
    return _DEBUG_FONT


def draw_debug_overlay(surface, director, x, y):
    """Hitbox/hurtbox/jangkauan/state/frame/FPS/partikel/skill/timer."""
    fnt = _debug_font()
    if fnt is None:
        return
    h = director.hero
    x = int(x)
    y = int(y)
    sc = body_scale(h)
    r = int(22 * sc)
    f = 1 if (getattr(h, "direction", 1) or 1) >= 0 else -1
    # hurtbox
    pygame.draw.rect(surface, (255, 80, 80),
                     (x - r, y - r - 20, r * 2, r * 2 + 20), 1)
    # jangkauan basic
    reach = int(MELEE_REACH * 1.0)
    pygame.draw.circle(surface, (80, 200, 255), (x, y), reach, 1)
    pygame.draw.circle(surface, (80, 200, 255), (x, y), 4, 1)
    # hitbox ayunan saat jendela aktif
    active, progress, kind = director._attack_state()
    if active and kind == "swing" and 0.30 <= progress < 0.62:
        hb = pygame.Rect(0, 0, int(reach * 0.95), int(70 * sc))
        if f >= 0:
            hb.midleft = (x + 12, y - 8)
        else:
            hb.midright = (x - 12, y - 8)
        pygame.draw.rect(surface, (255, 220, 60), hb, 1)
    # proyektil
    for b in director.projectiles.bolts:
        pygame.draw.circle(surface, (120, 255, 120),
                           (int(b.x), int(b.y)), int(b.radius) + 2, 1)
    # teks
    G = _renderer()
    state = "IDLE"
    phase_name = "-"
    if G is not None:
        try:
            state = G.anim_state(h)
        except Exception:
            pass
        try:
            phase_name = G.attack_phase(progress) if active else "-"
        except Exception:
            pass
    skill = getattr(h, "active_skill", None) or (
        'q' if getattr(h, "ability_active", False) else None)
    lines = [
        "KROBELLS  state=%s  phase=%s" % (state, phase_name),
        "atk %s p=%.2f  skill=%s t=%d" % (
            kind if active else "-", progress, skill,
            int(getattr(h, "active_skill_timer", 0) or 0)),
        "timer=%d cd=%d  hurt=%d" % (
            int(getattr(h, "timer", 0) or 0),
            int(getattr(h, "attack_cooldown", 0) or 0),
            int(getattr(h, "hurt_flash_timer", 0) or 0)),
        "fps=%.0f  parts=%d  bolts=%d  skills=%d" % (
            director.fps, director.particles.count(),
            director.projectiles.count(), len(director.skills)),
    ]
    yy = y - 92
    for ln in lines:
        t = fnt.render(ln, True, (220, 255, 240))
        bg = t.copy()
        bg.fill((0, 0, 0, 180))
        surface.blit(bg, (x - 8, yy - 1))
        surface.blit(t, (x - 7, yy))
        yy += 13
