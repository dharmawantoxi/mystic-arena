# ============================================================================
# heroes/xerathis_fx.py
# ----------------------------------------------------------------------------
# XERATHIS — CRYSTAL SORCERESS  (screen-space live layer)
#
# Badan Xerathis digambar lewat ``_NS_xerathis`` (bosses/level3.py) ke canvas
# yang di-CACHE lalu di-scale oleh pipeline hero. Seperti Gornak/Zephyr,
# semua yang butuh gerak 60 fps sejati — pita sapuan staff, partikel es,
# proyektil frost shard, impact, guncangan layar, hit-stop — TIDAK boleh
# hidup di dalam canvas itu. Modul ini adalah lapisan hidup: digambar
# langsung ke layar pada skala 1:1 tiap frame, dengan delta-time nyata.
#
# Pembagian kerja (sengaja, supaya tidak ada efek yang digambar 2x):
#
#   RENDERER (canvas, ter-cache)      MODUL INI (layar, hidup)
#   -----------------------------     -----------------------------------
#   rig sorceress + selout + rim      trail staff dari histori posisi nyata
#   bayangan kontak, aura es          partikel (es, salju, debu kristal)
#   pose, bob napas, gelombang        proyektil Ice Shard (sistem nyata)
#   flash cast, skill ground canvas   IMPACT FX + flash + shockwave
#   after-image blink                 overlay DEBUG_CHARACTER
#
# 100% PROSEDURAL. Tidak ada PNG / JPG / GIF / sprite-sheet / image.load.
# Semua bentuk dibuat dengan pygame.draw + pygame.Surface + pygame.transform.
#
# Isi modul
#   XERATHIS_PALETTE      palette khusus karakter (kontrak 9 kunci + ramp)
#   Particle              partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem        pool + burst + cap, reusable
#   SwingTrail            staff/ice trail prosedural dari histori posisi
#   ImpactFX              flash + shockwave + debris + slash fragment
#   XerathisProjectile    proyektil modular (spawn->travel->hit->destroy)
#   ProjectileSystem      manajer proyektil
#   SkillFX               lifecycle FX skill (cast->charge->release->fade)
#   XerathisFXDirector    satu instance per unit, mengikat semua di atas
#   draw_debug_overlay    hitbox/hurtbox/state/frame/FPS/particle/skill/timer
#   API modul             tick / reset_all / notify_* / draw_*_layer
# ============================================================================

import math
import random

import pygame

try:                                 # bus game-feel bersama (combat_feel)
    from heroes import combat_feel as _feel
except Exception:                    # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual untuk karakter XERATHIS: hitbox, hurtbox, jangkauan, state
#: animasi, frame, FPS, jumlah partikel, state skill, timer serangan.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
XERATHIS_FX_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 190

#: Batas keras proyektil visual per director.
MAX_PROJECTILES = 18

#: Panjang histori trail senjata (jumlah sample posisi bilah).
TRAIL_SAMPLES = 16

#: Batas dampak aktif per director & skill sekaligus di layar.
MAX_IMPACTS = 8
MAX_SKILLS = 5

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Kecepatan shard Crystal Nova (px/detik, ruang dunia).
SHARD_SPEED = 820.0

#: Umur FX skill dalam DETIK. Sinkron dengan ``_NS_xerathis`` +
#: ``active_skill_timer`` AI (60/50/90/100 langkah sim = 1.00/0.83/1.50/1.67s)
#: plus sisa after-glow supaya efek tidak "terpotong".
SKILL_TOTAL = {"q": 1.16, "w": 0.92, "e": 1.68, "r": 1.92}

#: Durasi pose per skill (frame) — dipakai untuk memetakan umur FX ke
#: fase yang sama dengan yang dibaca renderer.
SKILL_DUR = {"q": 60, "w": 50, "e": 90, "r": 100}

#: Radius EFEK di ruang dunia. q/w = skill point; e/r = area buff/ultimate.
WORLD_RADIUS = {"q": 48.0, "w": 30.0, "e": 90.0, "r": 110.0}

#: Fase serangan (dirujuk overlay debug & trail).
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.16),
    ("WINDUP",       0.16, 0.32),
    ("SWING",        0.32, 0.50),
    ("IMPACT",       0.50, 0.64),
    ("FOLLOW",       0.64, 0.82),
    ("RECOVERY",     0.82, 1.00),
)

#: Prioritas state. Angka besar menang; DEATH mengunci.
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


# ============================================================================
# 1.  PALETTE  —  crystal sorceress: es biru + ungu dingin + salju
# ============================================================================

XERATHIS_PALETTE = {
    # ── kontrak palette karakter (kontrak 9 kunci wajib) ───────────
    "outline":    (8,    10,  22),
    "shadow":     (14,   20,  44),
    "dark":       (28,   44,  92),
    "body":       (70,   98,  168),
    "mid":        (108,  148, 218),
    "light":      (158,  202, 248),
    "highlight":  (196,  232, 255),
    "weapon":     (218,  240, 255),
    "fx":         (235,  250, 255),

    # ── ramp es / kristal ──────────────────────────────────────────
    "fx_darkest": (8,    14,  38),
    "fx_dark":    (22,   38,  86),
    "fx_mid":     (70,   118, 190),
    "fx_light":   (130,  184, 235),
    "fx_bright":  (180,  218, 252),
    "fx_hot":     (226,  246, 255),
    "fx_white":   (248,  254, 255),

    # ── material fisik ─────────────────────────────────────────────
    "skin":       (235,  195, 168),
    "hair":       (220,  178, 100),
    "robe":       (62,   82,  154),
    "cloak":      (56,   36,  118),
    "gold":       (198,  152, 62),
    "gold_hot":   (255,  236, 165),

    # ── bahan es (spark & serpihan) ────────────────────────────────
    "ice_dark":   (16,   30,  72),
    "ice_mid":    (60,   118, 208),
    "ice_light":  (132,  190, 245),
    "ice_edge":   (196,  232, 255),
    "ice_hot":    (236,  252, 255),

    # ── sisa pembakaran (debu / asap / debu kristal) ───────────────
    "smoke":      (26,   36,  66),
    "ash":        (96,   72,  92),
    "dust":       (120,  150, 172),
}

P = XERATHIS_PALETTE

#: Kunci yang boleh disalin dari palet renderer supaya warna karakter
#: dan warna efek tidak pernah berbeda "satu derajat".
_PALETTE_SYNC = {
    "outline": "shadow_deep",
    "shadow": "robe_darkest",
    "dark": "robe_dark",
    "body": "robe_mid",
    "mid": "robe_light",
    "light": "robe_high",
    "highlight": "ice_bright",
    "weapon": "ice_hot",
    "fx": "ice_white",
    "fx_darkest": "ice_darkest",
    "fx_dark": "ice_dark",
    "fx_mid": "ice_mid",
    "fx_light": "ice_light",
    "fx_bright": "ice_bright",
    "fx_hot": "ice_hot",
    "fx_white": "ice_white",
    "ice_dark": "ice_darkest",
    "ice_mid": "ice_mid",
    "ice_light": "ice_light",
    "ice_edge": "ice_bright",
    "ice_hot": "ice_hot",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Salin warna tema dari ``_NS_xerathis.PALETTE`` sekali saja.

    Renderer adalah satu-satunya sumber kebenaran untuk material karakter;
    efek hidup tidak boleh punya salinan yang lalu melenceng.
    """
    global _PALETTE_SYNCED
    if _PALETTE_SYNCED:
        return
    _PALETTE_SYNCED = True
    R = _renderer()
    if R is None:
        return
    pal = getattr(R, "PALETTE", None)
    if not isinstance(pal, dict):
        return
    for dst, src in _PALETTE_SYNC.items():
        col = pal.get(src)
        if col is not None:
            P[dst] = tuple(int(c) for c in col[:3]) if len(col) >= 3 \
                else tuple(int(c) for c in col[:3] + (255,))


# ============================================================================
# 2.  JEMBATAN KE RENDERER  (satu sumber geometri & pose)
# ============================================================================

_RENDERER = None          # None = belum dicari, False = tidak ada


def _renderer():
    """``_NS_xerathis`` atau None. Diimpor malas: modul boss besar."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level3 import _NS_xerathis as G
            _RENDERER = G
        except Exception:                      # pragma: no cover
            _RENDERER = False
    return _RENDERER or None


def _fallback_pose(boss):
    """(action, phase, ap) tanpa renderer: baca atribut yang sudah ada."""
    skill = getattr(boss, "active_skill", None)
    action = getattr(boss, "_xr_pose_action", None)
    if action is None:
        action = {"q": "cast", "w": "cast", "e": "cast",
                  "r": "cast"}.get(skill)
    if action is None:
        action = ("attack" if getattr(boss, "_xr_attack_active", False)
                  else "idle")
    phase = float(getattr(boss, "pulse", 0.0) or 0.0)
    ap = 0.0
    if action == "attack":
        ap = float(getattr(boss, "_xr_attack_progress", 0.0) or 0.0)
    return action, phase, ap


def pose_of(boss):
    """Pose badan yang dipakai renderer (action, phase, attack_progress)."""
    R = _renderer()
    if R is None:
        return _fallback_pose(boss)
    try:
        action = getattr(boss, "_xr_pose_action", None)
        if action is None:
            return _fallback_pose(boss)
        phase = float(getattr(boss, "_xr_phase", getattr(boss, "pulse", 0.0)))
        ap = float(getattr(boss, "_xr_attack_progress", 0.0) or 0.0)
        return action, phase, ap
    except Exception:                          # pragma: no cover
        return _fallback_pose(boss)


def render_scale(boss):
    """Skala hero-lane (canvas dikali saat blit). Boss di layar = 1."""
    try:
        s = float(getattr(boss, "_render_scale", 1.0) or 1.0)
    except (TypeError, ValueError):
        s = 1.0
    return s if s > 0.01 else 1.0


def body_scale(boss):
    """Skala badan relatif terhadap anchor (digunakan FX tip)."""
    return render_scale(boss)


def screen_point(boss, x, y, local, action=None, phase=None, ap=None):
    """Titik koordinat layar dari koordinat lokal (offset dari anchor)."""
    if action is None or phase is None or ap is None:
        action, phase, ap = pose_of(boss)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)
    return (x + local[0] * k * facing + (0 if facing >= 0 else 0),
            y + local[1] * k)


def staff_points(boss, x, y, back=False):
    """(grip, tip) staff dalam ruang layar untuk trail & proyektil.

    Renderer menggambar staff dengan kristal di ``top`` ~ y-42 dan ujung
    runcing ~ y-52; saat menyerang staff mengarah ke depan.  Semua fungsi
    di modul ini memakai angka yang sama supaya proyektil lahir tepat di
    kepala kristal, bukan di tengah badan.
    """
    action, phase, ap = pose_of(boss)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)

    if action == "attack":
        t = max(0.0, min(1.0, ap or 0.0))
        # thrust -> swing -> thrust kembali (arc)
        if t < 0.30:
            ext = t / 0.30 * 0.45
            lift = 0.20 - t * 0.35
        elif t < 0.50:
            tt = (t - 0.30) / 0.20
            ext = 0.45 + tt * 0.85
            lift = (0.20 - 0.35) - tt * 0.10
        else:
            tt = (t - 0.50) / 0.50
            ext = 1.30 - tt * 0.90
            lift = -0.25 + tt * 0.45
        base_x = x + facing * (17 + ext * 10) * k
        base_y = y - (42 + max(0.0, lift) * 26) * k
        tip_x = base_x + facing * (8 + ext * 10) * k
        tip_y = base_y - (18 + ext * 4) * k
        grip_x = x + facing * 12 * k
        grip_y = y - 4 * k
    elif action == "cast":
        base_x = x + facing * 22 * k
        base_y = y - 40 * k
        tip_x = base_x + facing * 8 * k
        tip_y = base_y - 18 * k
        grip_x = x + facing * 13 * k
        grip_y = y - 2 * k
    else:
        sway = math.sin(phase * 0.7) * 2.0
        base_x = x + facing * 16 * k
        base_y = y - (44 + sway) * k
        tip_x = base_x + facing * 8 * k
        tip_y = base_y - 16 * k
        grip_x = x + facing * 12 * k
        grip_y = y - 2 * k

    if back:
        base_x = x - facing * 10 * k
        base_y = y - (38 + sway if action == "idle" else 34) * k
        tip_x = base_x - facing * 7 * k
        tip_y = base_y - 14 * k
        grip_x = x - facing * 9 * k
        grip_y = y + 2 * k
    return (grip_x, grip_y), (tip_x, tip_y)


def _quality():
    """Kualitas render mobile (objek Quality) — fallback aman."""
    try:
        from mobile.perf import Quality as Q
        return Q
    except Exception:                          # pragma: no cover
        return None


def particle_budget():
    """Faktor jumlah partikel 0..1 (preset kualitas x governor beban FX)."""
    Q = _quality()
    if Q is None:
        return 1.0
    if not getattr(Q, "particles", True):
        return 0.0
    return float(getattr(Q, "particle_ratio", 1.0))


def glow_allowed():
    return True


def shake_allowed():
    return True


# ============================================================================
# 3.  KECIL-CEPAT  (draw helpers + cache surface)
# ============================================================================

_HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

_CACHE = {}


def _clamp_color(color):
    color = tuple(int(max(0, min(255, c))) for c in color)
    return color


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(min(len(a), len(b))))


def _hash01(seed):
    """Hash deterministik kecil -> [0,1)."""
    v = (seed * 747796405 + 2891336453) & 0xFFFFFFFF
    v = ((v >> ((v >> 28) + 4)) ^ v) * 277803737
    v = (v >> 22) ^ v
    return (v & 0x3FFFFFF) / float(0x3FFFFFF)


def _cache_put(key, surf):
    if key not in _CACHE:
        _CACHE[key] = surf
    return _CACHE[key]


def clear_cache():
    _CACHE.clear()


def cache_size():
    return len(_CACHE)


def glow_surface(radius, color, power=1.0):
    """Cached soft radial glow (dipakai glow projectile/burst)."""
    radius = max(3, int(radius))
    key = ("glow", radius, color, round(power, 2))
    if key in _CACHE:
        return _CACHE[key]
    size = radius * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    steps = max(3, radius // 2)
    for i in range(steps, -1, -1):
        r = int(radius * i / steps)
        a = int((1.0 - i / steps) * 255 * power)
        a = max(0, min(255, a))
        if r > 0 and a > 0:
            color_a = (*color[:3], a)
            if _HAS_AACIRCLE:
                try:
                    pygame.draw.aacircle(surf, color_a, (radius + 2, radius + 2),
                                         r)
                except Exception:
                    pygame.draw.circle(surf, color_a,
                                       (radius + 2, radius + 2), r)
            else:
                pygame.draw.circle(surf, color_a, (radius + 2, radius + 2), r)
    return _cache_put(key, surf)


def spark_surface(size, color):
    """Cached 4-point sparkle (salt-and-pepper chunky pixel)."""
    size = max(3, int(size))
    key = ("spark", size, color)
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    c = size
    pygame.draw.line(surf, color, (c, 1), (c, size * 2 - 1), max(1, size // 3))
    pygame.draw.line(surf, color, (1, c), (size * 2 - 1, c), max(1, size // 3))
    pygame.draw.line(surf, color, (c, 1), (c, size * 2 - 1), 1)
    pygame.draw.line(surf, color, (1, c), (size * 2 - 1, c), 1)
    return _cache_put(key, surf)


def ring_surface(radius, thickness, color, alpha=255, dashed=0):
    """Cached ring (atau ring putus-putus jika dashed>0)."""
    radius = max(4, int(radius))
    thickness = max(1, int(thickness))
    key = ("ring", radius, thickness, color, alpha, dashed)
    if key in _CACHE:
        return _CACHE[key]
    size = radius * 2 + thickness * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (size // 2, size // 2)
    color_a = (*color[:3], alpha)
    if dashed <= 0:
        pygame.draw.circle(surf, color_a, center, radius, thickness)
    else:
        step = (math.tau / dashed)
        for i in range(dashed):
            a0 = i * step
            a1 = a0 + step * 0.58
            pts = [(center[0] + math.cos(a) * radius,
                    center[1] + math.sin(a) * radius)
                   for a in (a0, a1)]
            for a in [a0 + (a1 - a0) * t for t in (0.0, 0.5, 1.0)]:
                px = int(center[0] + math.cos(a) * radius)
                py = int(center[1] + math.sin(a) * radius)
                pygame.draw.circle(surf, color_a, (px, py), thickness)
    return _cache_put(key, surf)


def ellipse_ring_surface(rx, ry, thickness, color, angle_deg=0):
    """Cached chunky ellipse ring."""
    rx, ry = max(4, int(rx)), max(3, int(ry))
    thickness = max(1, int(thickness))
    key = ("ering", rx, ry, thickness, color, int(angle_deg))
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((rx * 2 + thickness * 2 + 10,
                           ry * 2 + thickness * 2 + 10), pygame.SRCALPHA)
    rect = (thickness + 5, thickness + 5, rx * 2, ry * 2)
    pygame.draw.ellipse(surf, color, rect, thickness)
    if angle_deg:
        surf = pygame.transform.rotate(surf, -angle_deg)
    return _cache_put(key, surf)


def ground_glow_surface(radius, color, power=0.3):
    """Cached flat ground ellipse glow."""
    radius = max(4, int(radius))
    key = ("gglow", radius, color, power)
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((radius * 2 + 8, radius + 10), pygame.SRCALPHA)
    steps = max(3, radius // 3)
    for i in range(steps, -1, -1):
        r = max(1, int(radius * i / steps))
        a = int((1.0 - i / steps) * 40 * power)
        if a <= 0:
            continue
        pygame.draw.ellipse(surf, (*color[:3], a),
                            (radius + 4 - r, 5 - r // 5,
                             r * 2, max(2, r // 2)))
    return _cache_put(key, surf)


def _shard_poly(surface, cx, cy, ang, length, width, color, alpha=255,
                outline=False):
    """Gambar shard es tajam (polygon directional)."""
    ca, sa = math.cos(ang), math.sin(ang)
    tip = (cx + ca * length, cy + sa * length)
    left = (cx + math.cos(ang + 2.4) * width * 0.45,
            cy + math.sin(ang + 2.4) * width * 0.45)
    right = (cx + math.cos(ang - 2.4) * width * 0.45,
             cy + math.sin(ang - 2.4) * width * 0.45)
    pts = [tip, left, right]
    color_a = (*color[:3], alpha)
    if outline:
        pygame.draw.polygon(surface, color_a, pts)
    else:
        if _HAS_AACIRCLE:
            pygame.draw.polygon(surface, color_a, pts)
        else:
            pygame.draw.polygon(surface, color_a, pts)
    return tip


def _scratch(w, h):
    return pygame.Surface((max(1, int(w)), max(1, int(h))), pygame.SRCALPHA)


def _blit_faded(surface, surf, cx, cy, alpha=255, additive=False):
    if surf is None:
        return
    if alpha < 2:
        return
    cx, cy = int(cx), int(cy)
    rect = surf.get_rect(center=(cx, cy))
    if alpha >= 255:
        flags = pygame.BLEND_RGB_ADD if additive else 0
        surface.blit(surf, rect.topleft, special_flags=flags)
        return
    # Non-additif: set_alpha langsung, tanpa salinan per partikel.
    if additive:
        tmp = _scratch(rect.width, rect.height)
        tmp.blit(surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        tmp.set_alpha(alpha)
        surface.blit(tmp, rect.topleft,
                     special_flags=pygame.BLEND_RGB_ADD)
        return
    surf.set_alpha(int(alpha))
    surface.blit(surf, rect.topleft)
    surf.set_alpha(255)


# ============================================================================
# 4.  PARTICLE
# ============================================================================

class Particle:
    """Particle penuh: posisi, vel, acc, rotasi, fade, drag, gravity."""

    __slots__ = ("x", "y", "vx", "vy", "ax", "ay", "life", "max_life",
                 "size", "rotation", "rotation_speed", "alpha", "gravity",
                 "color", "shape", "drag", "additive", "layer", "active",
                 "scatter")

    def __init__(self):
        self.active = False

    def spawn(self, x, y, vx=0.0, vy=0.0, ax=0.0, ay=0.0,
              life=0.5, size=3.0, rotation=0.0, rotation_speed=0.0,
              alpha=255, gravity=0.0, color=(180, 220, 255),
              shape="spark", drag=0.0, additive=False, layer="front",
              scatter=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.ax = float(ax)
        self.ay = float(ay)
        self.life = float(max(0.01, life))
        self.max_life = float(life)
        self.size = float(size)
        self.rotation = float(rotation)
        self.rotation_speed = float(rotation_speed)
        self.alpha = float(max(0, min(255, alpha)))
        self.gravity = float(gravity)
        self.color = tuple(int(c) for c in color[:3])
        self.shape = shape
        self.drag = float(drag)
        self.additive = bool(additive)
        self.layer = layer
        self.scatter = float(scatter)
        self.active = True
        return self

    def update(self, dt):
        if not self.active:
            return
        self.life -= dt
        if self.life <= 0.0:
            self.active = False
            return
        # drag / scatter
        if self.drag > 0.0:
            d = max(0.0, 1.0 - self.drag * dt)
            self.vx *= d
            self.vy *= d
        if self.scatter > 0.0:
            self.vx += random.uniform(-self.scatter, self.scatter) * dt
            self.vy += random.uniform(-self.scatter, self.scatter) * dt
        self.vx += self.ax * dt
        self.vy += (self.ay + self.gravity) * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rotation_speed * dt

    def _fade(self):
        t = self.life / max(0.001, self.max_life)
        return int(max(0.0, min(1.0, t)) * self.alpha)

    def draw(self, surface):
        if not self.active:
            return
        a = self._fade()
        if a <= 0:
            return
        color = (*self.color, a)
        x, y = int(self.x), int(self.y)
        s = max(1.0, self.size)
        if self.shape == "streak":
            ang = math.atan2(self.vy, self.vx)
            ca, sa = math.cos(ang), math.sin(ang)
            px, py = -sa * s * 0.35, ca * s * 0.35
            pygame.draw.line(surface, color,
                             (x - ca * s * 1.6 - px, y - sa * s * 1.6 - py),
                             (x + ca * s * 1.6 + px, y + sa * s * 1.6 + py),
                             max(1, int(s * 0.55)))
        elif self.shape == "shard":
            v = max(1.0, abs(self.vx) + abs(self.vy) + 1.0)
            ang = math.atan2(self.vy, self.vx)
            tip = (x + math.cos(ang) * s * 1.8, y + math.sin(ang) * s * 1.8)
            lx = x + math.cos(ang + 2.4) * s * 0.6
            ly = y + math.sin(ang + 2.4) * s * 0.6
            rx = x + math.cos(ang - 2.4) * s * 0.6
            ry = y + math.sin(ang - 2.4) * s * 0.6
            pygame.draw.polygon(surface, color, [tip, (lx, ly), (rx, ry)])
        elif self.shape == "dust":
            pygame.draw.circle(surface, color, (x, y), max(1, int(s * 0.5)))
        elif self.shape == "spark":
            c = int(s)
            pygame.draw.line(surface, color, (x - c, y), (x + c, y), 1)
            pygame.draw.line(surface, color, (x, y - c), (x, y + c), 1)
        elif self.shape == "ring":
            r = int(s)
            pygame.draw.circle(surface, color, (x, y), r)
            pygame.draw.circle(surface, color, (x, y), r + 1, 1)
        elif self.shape == "crystal":
            size = s * 2.2
            ang = self.rotation
            tip = (x + math.cos(ang) * size, y + math.sin(ang) * size)
            pygame.draw.line(surface, color,
                             (x - math.cos(ang) * size,
                              y - math.sin(ang) * size), tip,
                             max(1, int(s * 0.7)))
            pygame.draw.line(surface, color, tip,
                             (x - math.sin(ang) * s * 0.6,
                              y + math.cos(ang) * s * 0.6), 1)
            pygame.draw.line(surface, color, tip,
                             (x + math.sin(ang) * s * 0.6,
                              y - math.cos(ang) * s * 0.6), 1)
        else:
            pygame.draw.circle(surface, color, (x, y), max(1, int(s * 0.6)))


# ============================================================================
# 5.  PARTICLE SYSTEM
# ============================================================================

class ParticleSystem:
    """Pool reusable, burst terarah, cap keras."""

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = max(8, int(cap))
        self.particles = [Particle() for _ in range(self.cap)]
        self._cursor = 0

    def _next(self):
        p = self.particles[self._cursor]
        self._cursor = (self._cursor + 1) % self.cap
        return p

    def burst(self, x, y, count, speed=(30, 120), life=(0.2, 0.5),
              size=(2, 5), colors=((200, 220, 255),), spread=math.tau,
              direction=0.0, gravity=0.0, drag=0.0, shape="spark",
              additive=False, layer="front", rotation_speed=(0, 0),
              scatter=0.0):
        budget = particle_budget()
        if budget <= 0.0:
            return 0
        count = max(0, int(count))
        if budget < 1.0:
            if count > 1:
                count = max(1, int(count * budget))
            elif random.random() >= budget:
                return 0
        for _ in range(count):
            p = self._next()
            ang = direction + random.uniform(-spread / 2.0, spread / 2.0)
            speed_now = random.uniform(speed[0], speed[1])
            life_now = random.uniform(life[0], life[1])
            size_now = random.uniform(size[0], size[1])
            color = colors[int(random.random() * len(colors))]
            rot = random.uniform(-math.pi, math.pi)
            rot_spd = random.uniform(rotation_speed[0], rotation_speed[1])
            az = random.uniform(-30.0, 30.0)
            vy = random.uniform(-45.0, 45.0)
            if scatter:
                az += random.uniform(-scatter, scatter)
            p.spawn(x, y, math.cos(ang) * speed_now,
                    math.sin(ang) * speed_now - vy,
                    az, az * 0.4, life_now, size_now, rot, rot_spd,
                    255, gravity, color, shape, drag, additive, layer,
                    scatter)

    def update(self, dt):
        for p in self.particles:
            p.update(dt)

    def draw(self, surface, layer="front"):
        if layer == "front":
            for p in self.particles:
                if p.active and p.layer == "front":
                    p.draw(surface)
        else:
            for p in self.particles:
                if p.active and p.layer == "back":
                    p.draw(surface)

    def count(self):
        return sum(1 for p in self.particles if p.active)

    def clear(self):
        for p in self.particles:
            p.active = False


# ============================================================================
# 6.  SWING TRAIL  —  staff/ice slash dari histori posisi
# ============================================================================

class SwingTrail:
    """Pita sapuan staff prosedural dari histori posisi ujung staff.

    Sample minimal 3-4 posisi lama + posisi sekarang; poligon transparan
    di-build dari sisi depan (leading edge) dan belakang (trailing edge)
    sehingga trail terlihat mengikuti arah ayunan, bukan garis statis.
    """

    def __init__(self, samples=TRAIL_SAMPLES):
        self.samples = int(samples)
        self.points = []
        self.width_boost = 1.0
        self.active = False

    def reset(self):
        self.points.clear()
        self.active = False
        self.width_boost = 1.0

    def push(self, x, y, facing=1):
        self.points.append((float(x), float(y)))
        if len(self.points) > self.samples:
            self.points.pop(0)
        self.active = len(self.points) >= 3

    def _poly(self, scale=1.0, width=9.0):
        if len(self.points) < 3:
            return None
        pts = self.points
        out = []
        # leading edge
        for i, (x, y) in enumerate(pts):
            nx = pts[min(i + 1, len(pts) - 1)]
            px = pts[max(i - 1, 0)]
            dx, dy = nx[0] - px[0], nx[1] - px[1]
            L = math.hypot(dx, dy)
            if L < 0.001:
                dx, dy = 1.0, 0.0
                L = 1.0
            nx_, ny_ = -dy / L, dx / L
            w = width * self.width_boost
            # taper tip lama
            t = i / max(1.0, len(pts) - 1)
            w *= (0.3 + 0.7 * t)
            out.append((x + nx_ * w * scale, y + ny_ * w * scale))
        for i in range(len(pts) - 1, -1, -1):
            x, y = pts[i]
            nx = pts[min(i + 1, len(pts) - 1)]
            px = pts[max(i - 1, 0)]
            dx, dy = nx[0] - px[0], nx[1] - px[1]
            L = math.hypot(dx, dy)
            if L < 0.001:
                dx, dy = 1.0, 0.0
                L = 1.0
            nx_, ny_ = -dy / L, dx / L
            w = width * self.width_boost
            t = i / max(1.0, len(pts) - 1)
            w *= (0.3 + 0.7 * t)
            out.append((x - nx_ * w * scale, y - ny_ * w * scale))
        return out

    def draw(self, surface, color, alpha, additive=True):
        if not self.active or len(self.points) < 3:
            return
        poly = self._poly(1.0, 8.5)
        if poly is None:
            return
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        min_x, min_y = int(min(xs)) - 4, int(min(ys)) - 4
        w = int(max(xs) - min_x + 8)
        h = int(max(ys) - min_y + 8)
        if w <= 0 or h <= 0:
            return
        tmp = _scratch(w, h)
        shifted = [(p[0] - min_x, p[1] - min_y) for p in poly]
        pygame.draw.polygon(tmp, (*color[:3], int(alpha)), shifted)
        surface.blit(tmp, (min_x, min_y),
                     special_flags=pygame.BLEND_RGB_ADD if additive else 0)


# ============================================================================
# 7.  IMPACT FX
# ============================================================================

class ImpactFX:
    """Flash + ring + shard fragments + slash fragment tunggal."""

    _COUNT = 0

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="ice", seed=0):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = float(power)
        self.crit = bool(crit)
        self.kind = kind
        self.age = 0.0
        self.life = 0.34 + 0.12 * min(2.0, max(0.2, power))
        self.seed = int(seed)
        ImpactFX._COUNT += 1

    def update(self, dt):
        self.age += dt

    def _t(self):
        return min(1.0, self.age / max(0.001, self.life))

    def draw(self, surface):
        t = self._t()
        if t >= 1.0:
            return
        fade = 1.0 - t
        p = min(2.2, self.power)

        # central flash
        r = int((7 + 20 * p) * (0.3 + 0.7 * t))
        glow = glow_surface(max(6, r), P.get("fx_high", P["fx_hot"]), 0.85)
        _blit_faded(surface, glow, self.x, self.y, int(160 * fade),
                    additive=True)

        # ring shockwave
        rr = int((22 + 16 * p) * (0.2 + 0.85 * t))
        ring = ring_surface(rr, max(1, int(3 * p)), P["fx_bright"], 200 * fade)
        _blit_faded(surface, ring, self.x, self.y, int(220 * fade),
                    additive=True)

        # slash fragment (arc)
        arc_pts = []
        start = self.angle - 0.9
        end = self.angle + 0.9
        for i in range(7):
            a = start + (end - start) * i / 6.0
            rr2 = (20 + 8 * p) * (0.4 + 0.8 * t)
            arc_pts.append((self.x + math.cos(a) * rr2,
                            self.y + math.sin(a) * rr2 - 4 * t))
            arc_pts.append((self.x + math.cos(a) * (rr2 - 5.0),
                            self.y + math.sin(a) * (rr2 - 5.0) - 4 * t))
        if len(arc_pts) >= 3:
            tmp = _scratch(90, 90)
            pygame.draw.lines(tmp, (*P["ice_edge"], int(200 * fade)), False,
                              [(px - self.x + 45, py - self.y + 45)
                               for px, py in arc_pts], max(1, int(3 * p)))
            surface.blit(tmp, (int(self.x) - 45, int(self.y) - 45),
                         special_flags=pygame.BLEND_RGB_ADD)


# ============================================================================
# 8.  PROJECTILE  —  Ice Shard (directional crystal)
# ============================================================================

class XerathisProjectile:
    """Proyektil frost shard modular.

    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY.
    """

    __slots__ = ("x", "y", "velocity", "speed", "damage", "lifetime",
                 "target", "radius", "rotation", "trail", "particles",
                 "active", "sx", "sy", "hit_radius", "kind", "age",
                 "hit_pos", "on_impact", "homing", "hit_target",
                 "trail_len")

    def __init__(self, sx, sy, tx, ty, speed=SHARD_SPEED, damage=0,
                 target=None, radius=7.0, kind="ice", trail_len=12,
                 particles=None, on_impact=None):
        self.x = float(sx)
        self.y = float(sy)
        self.sx = float(sx)
        self.sy = float(sy)
        self.speed = float(speed)
        self.damage = damage
        self.target = target
        self.radius = float(radius)
        self.hit_radius = float(radius)
        self.kind = kind
        self.age = 0.0
        self.lifetime = (3.2 if kind != "bolt" else 2.4)
        self.particles = particles
        self.on_impact = on_impact
        self.active = True
        self.hit_pos = None
        self.rotation = 0.0
        self.homing = 0.45
        self.hit_target = False
        dx = tx - sx
        dy = ty - sy
        L = math.hypot(dx, dy) or 1.0
        self.velocity = pygame.Vector2(dx / L, dy / L)
        self.trail = []
        self.trail_len = int(trail_len)

    @property
    def pos(self):
        return self.x, self.y

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age >= self.lifetime:
            self.active = False
            return

        # target tracking lembut
        if self.target is not None and getattr(self.target, "alive", False):
            tx = float(getattr(self.target, "x", self.x + 100))
            ty = float(getattr(self.target, "y", self.y)) - 6.0
            dx = tx - self.x
            dy = ty - self.y
            L = math.hypot(dx, dy) or 1.0
            desired = pygame.Vector2(dx / L, dy / L)
            self.velocity = self.velocity.lerp(desired, self.homing * dt)
            self.velocity = self.velocity.normalize() if self.velocity \
                else desired

        self.x += self.velocity.x * self.speed * dt
        self.y += self.velocity.y * self.speed * dt
        self.rotation = (self.rotation + math.atan2(self.velocity.y,
                                                    self.velocity.x) * dt * 4.0)

        self.trail.append((self.x, self.y, self.age))
        if len(self.trail) > self.trail_len:
            self.trail.pop(0)

        # hit target
        if self.target is not None and getattr(self.target, "alive", False):
            tx = float(getattr(self.target, "x", self.x))
            ty = float(getattr(self.target, "y", self.y))
            hr = max(10.0, self.radius + float(
                getattr(self.target, "radius", 10.0)) * 0.55)
            if math.hypot(tx - self.x, ty - self.y) <= hr:
                self._hit(self.target.x, self.target.y)
                return

        if self.particles is not None and len(self.trail) % 2 == 0:
            self.particles.burst(self.x, self.y, 1,
                                 speed=(10, 45), life=(0.12, 0.3),
                                 size=(1, 2),
                                 colors=(P["ice_light"], P["ice_edge"]),
                                 spread=1.4, direction=self.rotation + math.pi,
                                 drag=1.4, shape="spark", additive=True)

    def _hit(self, x, y):
        if not self.active:
            return
        self.hit_pos = pygame.Vector2(x, y)
        self.active = False
        if self.on_impact:
            try:
                self.on_impact(self)
            except Exception:
                pass

    def draw(self, surface):
        if not self.active:
            return
        # trail (fading)
        n = len(self.trail)
        for i, (tx, ty, a) in enumerate(self.trail):
            t = (i + 1) / max(1, n)
            alpha = int(35 + 110 * t * (1.0 - self.age / self.lifetime))
            r = max(1, int(2.0 + 3.5 * t))
            _blit_faded(surface, glow_surface(max(6, r), P["ice_dark"], 0.5),
                        tx, ty, alpha, additive=True)
        # glow
        _blit_faded(surface, glow_surface(16, P["ice_mid"], 0.7),
                    self.x, self.y, 150, additive=True)
        # directional shard body
        ca, sa = math.cos(self.rotation), math.sin(self.rotation)
        px, py = self.x, self.y
        length = 15.0
        width = 5.0
        self._draw_shard(surface, px, py, self.rotation, length, width)

    def _draw_shard(self, surface, px, py, ang, length, width):
        ca, sa = math.cos(ang), math.sin(ang)
        tip = (px + ca * length, py + sa * length)
        tail = (px - ca * length * 0.75, py - sa * length * 0.75)
        perp = (-sa, ca)
        pygame.draw.polygon(surface, P["ice_dark"],
                            [tip,
                             (px + perp[0] * width, py + perp[1] * width),
                             tail,
                             (px - perp[0] * width, py - perp[1] * width)])
        pygame.draw.polygon(surface, P["ice_mid"],
                            [(px + ca * 2, py + sa * 2),
                             (px + perp[0] * width * 0.65,
                              py + perp[1] * width * 0.65),
                             (tail[0] + ca * 2, tail[1] + sa * 2),
                             (px - perp[0] * width * 0.65,
                              py - perp[1] * width * 0.65)])
        pygame.draw.polygon(surface, P["ice_light"],
                            [(px + ca * 4, py + sa * 4),
                             (px + perp[0] * width * 0.35,
                              py + perp[1] * width * 0.35),
                             (tail[0] + ca * 4, tail[1] + sa * 4),
                             (px - perp[0] * width * 0.35,
                              py - perp[1] * width * 0.35)])
        pygame.draw.line(surface, P["ice_edge"],
                         (px - ca * 7, py - sa * 7), tip, 1)
        pygame.draw.circle(surface, P["ice_hot"], (int(tip[0]), int(tip[1])), 1)


# ============================================================================
# 9.  PROJECTILE SYSTEM
# ============================================================================

class ProjectileSystem:
    """Manajer proyektil dengan pool maksimal."""

    def __init__(self, particles=None):
        self.particles = particles
        self.items = []

    def spawn(self, sx, sy, tx, ty, speed=SHARD_SPEED, damage=0,
              target=None, radius=7.0, kind="ice", trail_len=12,
              on_impact=None):
        if len(self.items) >= MAX_PROJECTILES:
            self.items.pop(0)
        pr = XerathisProjectile(
            sx, sy, tx, ty, speed, damage, target, radius, kind,
            trail_len, self.particles, on_impact)
        self.items.append(pr)
        return pr

    def update(self, dt):
        for pr in self.items:
            pr.update(dt)
        self.items = [pr for pr in self.items if pr.active]

    def draw(self, surface):
        for pr in self.items:
            pr.draw(surface)

    def draw_debug(self, surface):
        for pr in self.items:
            pygame.draw.circle(surface, (255, 80, 220, 180),
                               (int(pr.x), int(pr.y)), int(pr.hit_radius), 1)

    def count(self):
        return len(self.items)

    def clear(self):
        self.items.clear()


# ============================================================================
# 10.  SKILL FX  (Q Crystal Nova, W Frostbite, E Arcane Aura, R Freezing Field)
# ============================================================================

class SkillFX:
    """Satu skill aktif + lifecycle (cast -> charge -> release -> fade)."""

    TINT = {
        "q": P["fx_bright"],
        "w": P["fx_light"],
        "e": P["fx_bright"],
        "r": P["fx_hot"],
    }

    def __init__(self, skill, x, y, particles=None, aim=None, radius=None):
        self.skill = skill
        self.x = float(x)
        self.y = float(y)
        self.aim = aim or (x, y)
        self.radius = float(radius or WORLD_RADIUS.get(skill, 60))
        self.particles = particles
        self.age = 0.0
        self.life = float(SKILL_TOTAL.get(skill, 1.0))
        self.done = False
        self._released = False
        self._impact_emitted = False
        self._after = False

    def update(self, dt):
        if self.done:
            return
        self.age += dt
        dur = float(SKILL_DUR.get(self.skill, 60)) / 60.0
        if self.age >= dur and not self._released:
            self._released = True
            self._emit_release()
        if self.age >= dur + 0.34 and not self._after:
            self._after = True
            self._emit_after()
        if self.age >= self.life:
            self.done = True

    def _t(self):
        dur = float(SKILL_DUR.get(self.skill, 60)) / 60.0
        return max(0.0, min(1.0, self.age / max(0.001, dur)))

    def _fade(self):
        if self.age <= 0.0:
            return 0.0
        # total life berakhir -> fade out
        dt = self.age / max(0.001, self.life)
        if dt > 0.72:
            return 1.0 - (dt - 0.72) / 0.28
        return 1.0

    def _emit_release(self):
        if self.particles is None:
            return
        x, y = self.aim[0], self.aim[1]
        if self.skill == "q":
            self.particles.burst(x, y, 22, speed=(80, 260),
                                 life=(0.18, 0.7), size=(2, 5),
                                 colors=(P["ice_hot"], P["ice_edge"],
                                         P["ice_light"]),
                                 spread=math.tau, gravity=90.0,
                                 shape="shard", additive=True,
                                 rotation_speed=(-18, 18))
            self.particles.burst(x, y, 12, speed=(20, 110),
                                 life=(0.3, 0.8), size=(1, 3),
                                 colors=(P["ice_light"], P["ice_mid"]),
                                 spread=math.tau, gravity=30.0,
                                 shape="spark", additive=True)
        elif self.skill == "w":
            self.particles.burst(x, y, 16, speed=(30, 160),
                                 life=(0.2, 0.6), size=(2, 4),
                                 colors=(P["ice_hot"], P["fx_bright"]),
                                 spread=math.tau, gravity=120.0,
                                 shape="shard", additive=True,
                                 rotation_speed=(-14, 14))
            self.particles.burst(x, y, 8, speed=(10, 80),
                                 life=(0.4, 0.9), size=(1, 3),
                                 colors=(P["ice_mid"], P["ice_dark"]),
                                 spread=math.tau, shape="crystal",
                                 rotation_speed=(-6, 6))
        elif self.skill == "e":
            self.particles.burst(x, y, 18, speed=(40, 150),
                                 life=(0.4, 1.0), size=(2, 4),
                                 colors=(P["fx_bright"], P["fx_hot"]),
                                 spread=math.tau, gravity=-50.0,
                                 shape="spark", additive=True)
            self.particles.burst(x, y, 10, speed=(15, 80),
                                 life=(0.5, 1.2), size=(2, 5),
                                 colors=(P["ice_light"], P["fx_light"]),
                                 spread=math.tau, gravity=-30.0,
                                 shape="dust", layer="back")
        elif self.skill == "r":
            self.particles.burst(x, y, 30, speed=(100, 320),
                                 life=(0.2, 0.9), size=(2, 6),
                                 colors=(P["fx_white"], P["ice_edge"],
                                         P["ice_light"]),
                                 spread=math.tau, gravity=-20.0,
                                 shape="shard", additive=True,
                                 rotation_speed=(-22, 22))
            self.particles.burst(x, y, 16, speed=(30, 150),
                                 life=(0.5, 1.2), size=(2, 5),
                                 colors=(P["fx_bright"], P["ice_mid"]),
                                 spread=math.tau, gravity=40.0,
                                 shape="crystal", rotation_speed=(-8, 8))

    def _emit_after(self):
        if self.particles is None:
            return
        x, y = self.aim[0], self.aim[1]
        self.particles.burst(x, y, 8, speed=(20, 80), life=(0.2, 0.6),
                             size=(2, 4),
                             colors=(P["fx_dark"], P["fx_light"]),
                             spread=math.tau, gravity=80.0,
                             shape="dust", layer="back")

    def draw_ground(self, surface):
        fade = self._fade()
        if fade <= 0.0:
            return
        t = self._t()
        x, y = self.aim[0], self.aim[1]
        if self.skill == "q":
            r = int((18 + self.radius * t) * (0.3 + 0.7 * t))
            glow = ground_glow_surface(r, P["ice_dark"], 0.5)
            _blit_faded(surface, glow, x, y + 14, int(220 * fade),
                        additive=True)
            ring = ellipse_ring_surface(r, int(r * 0.45), 3,
                                        (*P["ice_dark"], 220))
            _blit_faded(surface, ring, x, y + 12, int(180 * fade),
                        additive=True)
        elif self.skill == "e":
            r = int(self.radius * (0.7 + 0.3 * math.sin(t * 12)))
            ring = ellipse_ring_surface(r, int(r * 0.45), 3,
                                        (*P["fx_bright"], 170))
            _blit_faded(surface, ring, x, y + 10, int(180 * fade),
                        additive=True)
            for i in range(8):
                a = t * 2.5 + i * math.pi / 4
                px = x + math.cos(a) * r * 0.9
                py = y + 12 + math.sin(a) * r * 0.38
                pygame.draw.circle(surface, (*P["fx_hot"], int(220 * fade)),
                                   (int(px), int(py)), 2)
        elif self.skill == "r":
            r = int(self.radius * (0.6 + 0.5 * t))
            ring = ellipse_ring_surface(r, int(r * 0.42), 5,
                                        (*P["fx_bright"], 200))
            _blit_faded(surface, ring, x, y + 10, int(180 * fade),
                        additive=True)
            for i in range(12):
                a = t * 4.0 + i * math.pi / 6
                px = x + math.cos(a) * r * 0.85
                py = y + 12 + math.sin(a) * r * 0.36
                pygame.draw.circle(surface, (*P["ice_hot"], int(220 * fade)),
                                   (int(px), int(py)), 2)

    def draw_front(self, surface):
        fade = self._fade()
        if fade <= 0.0:
            return
        t = self._t()
        x, y = self.aim[0], self.aim[1]
        if self.skill == "q":
            # rising crystal spikes + nova
            if t < 0.35:
                tt = t / 0.35
                for i in range(7):
                    a = i * math.tau / 7 + t * 2.0
                    px = x + math.cos(a) * 18 * (0.4 + 0.6 * tt)
                    py = y - 8 - int(tt * 26)
                    c = P["ice_dark"]
                    pygame.draw.polygon(surface,
                                        (*c, int(200 * fade)),
                                        [(px - 3, py + 7), (px + 3, py + 7),
                                         (px, py - 12)])
                    pygame.draw.line(surface, (*P["ice_edge"],
                                               int(230 * fade)),
                                     (px, py + 7), (px, py - 12), 1)
            else:
                tt = (t - 0.35) / 0.65
                r = int((16 + 34 * tt) * (1.0 - tt * 0.2))
                glow = glow_surface(max(6, r), P["ice_mid"], 0.8)
                _blit_faded(surface, glow, x, y, int(220 * fade),
                            additive=True)
                ring = ring_surface(int(r * 1.1), 3, P["fx_bright"], 210)
                _blit_faded(surface, ring, x, y, int(220 * (1.0 - tt)),
                            additive=True)
        elif self.skill == "w":
            # frost beam to target + encasing crystal
            sx, sy = self.x, self.y
            ex, ey = self.aim[0], self.aim[1]
            tt = max(0.0, min(1.0, t * 2.4))
            cur_x = sx + (ex - sx) * tt
            cur_y = sy - 10 + (ey - sy + 10) * tt
            pygame.draw.line(surface, (*P["ice_light"], int(150 * fade)),
                             (int(sx + 24), int(sy - 18)),
                             (int(cur_x), int(cur_y)), 2)
            pygame.draw.circle(surface, (*P["ice_hot"], int(240 * fade)),
                               (int(cur_x), int(cur_y)), 5)
            _blit_faded(surface, glow_surface(16, P["fx_bright"], 0.9),
                        cur_x, cur_y, int(200 * fade), additive=True)
            if t > 0.35:
                size = 14 + 8 * (t - 0.35) / 0.65
                pygame.draw.polygon(surface, (*P["ice_dark"], 220),
                                    [(ex - size, ey + size),
                                     (ex - size + 5, ey - size),
                                     (ex + size - 5, ey - size),
                                     (ex + size, ey + size)])
                for i in range(6):
                    a = i * math.pi / 3
                    pygame.draw.line(surface, (*P["ice_edge"],
                                               int(220 * fade)),
                                     (ex + math.cos(a) * size * 0.7,
                                      ey + math.sin(a) * size * 0.7),
                                     (ex + math.cos(a) * size * 1.1,
                                      ey + math.sin(a) * size * 1.1), 2)
                    pygame.draw.circle(surface, (*P["ice_hot"],
                                                 int(230 * fade)),
                                       (int(ex + math.cos(a) * size * 1.1),
                                        int(ey + math.sin(a) * size * 1.1)), 1)
        elif self.skill == "e":
            # rising energy from body
            for i in range(8):
                ss = (t * 1.6 + i * 0.12) % 1.0
                a = i * math.pi / 4 + t * 2.0
                px = x + math.cos(a) * (16 + 12 * ss)
                py = y + 16 - ss * 62
                alpha = int((1.0 - ss) * 200 * fade)
                pygame.draw.circle(surface, (*P["fx_light"], alpha),
                                   (int(px), int(py)), 2 + int(ss * 3))
                pygame.draw.circle(surface, (*P["fx_hot"], alpha),
                                   (int(px), int(py)), 1)
            # halo pulsing
            r = int(42 * (0.85 + 0.15 * math.sin(t * 8.0)))
            ring = ring_surface(r, 2, P["fx_bright"], 140)
            _blit_faded(surface, ring, x, y - 8, int(160 * fade),
                        additive=True)
        elif self.skill == "r":
            # switching ice crystals + swirling storm
            for i in range(8):
                cp = (t * 2.2 + i * 0.35) % 1.0
                grow = math.sin(cp * math.pi)
                a = i * math.pi / 4 + i * 0.6 + t * 1.8
                dist = 38 + (i * 11) % 22
                px = x + math.cos(a) * dist
                py = y + 18 + math.sin(a) * dist * 0.3
                size = int(10 + 12 * grow)
                if size > 1:
                    pygame.draw.polygon(surface, (*P["ice_dark"],
                                                  int(220 * fade)),
                                        [(px - 5, py + size // 2),
                                         (px + 5, py + size // 2),
                                         (px + 3, py - size),
                                         (px, py - size - 3),
                                         (px - 3, py - size)])
                    pygame.draw.line(surface, (*P["ice_edge"],
                                               int(240 * fade)),
                                     (px, py + 2), (px, py - size), 1)
            for i in range(10):
                a = t * 4.0 + i * math.pi / 5
                r = 58
                px = x + math.cos(a) * r
                py = y + 14 + math.sin(a) * r * 0.32
                pygame.draw.circle(surface, (*P["ice_light"], int(170 * fade)),
                                   (int(px), int(py)), 2)
                pygame.draw.circle(surface, (*P["ice_hot"], int(230 * fade)),
                                   (int(px), int(py)), 1)


# ============================================================================
# 11.  DIRECTOR — satu per unit Xerathis
# ============================================================================

class XerathisFXDirector:
    """Mengikat particle + trail + proyektil + impact + skill FX untuk
    satu unit Xerathis (hero MAUPUN mini boss — kode sama, hanya sumber
    transformasinya yang beda)."""

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
        self._cast_seen = False

    # ------------------------------------------------------------------
    def on_swing_start(self, x, y, facing):
        """Awal ayunan / cast: trail reset + debu es di kaki."""
        self.trail.reset()
        self.trail.width_boost = 1.0
        self.swing_active = True
        gy = y + 36
        self.particles.burst(
            x + facing * 7, gy, 6,
            speed=(25, 90), life=(0.18, 0.4), size=(2, 4),
            colors=(P["dust"], P["ice_mid"], P["fx_dark"]),
            spread=1.2, direction=math.pi if facing > 0 else 0.0,
            gravity=90.0, drag=2.4, shape="dust", layer="back")

    def on_swing_end(self):
        self.swing_active = False

    def on_swing_impact_frame(self, x, y, facing):
        """Sapu udara di frame IMPACT — feedback walau tidak kena apa-apa."""
        _g, tip = staff_points(self.hero, x, y, False)
        ang = math.atan2(tip[1] - _g[1], tip[0] - _g[0])
        self.particles.burst(
            tip[0], tip[1], 8,
            speed=(100, 240), life=(0.1, 0.26), size=(1, 3),
            colors=(P["ice_hot"], P["ice_edge"], P["ice_light"]),
            spread=1.6, direction=ang - math.pi / 2, drag=3.5,
            shape="streak", additive=True)
        self.particles.burst(
            tip[0], tip[1], 5,
            speed=(60, 160), life=(0.14, 0.34), size=(2, 4),
            colors=(P["ice_light"], P["ice_mid"]),
            spread=1.5, direction=ang + math.pi, drag=3.0,
            shape="shard", rotation_speed=(-12, 12), additive=True)
        self.impacts.append(ImpactFX(tip[0], tip[1], ang, 0.55, False,
                                     kind="ice", seed=int(self.frames)))

    def on_cast(self, x, y, skill, aim=None):
        """Skill dilepas: SkillFX + guncangan + (Q) proyektil."""
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        gy = 36
        if aim is None:
            tgt = getattr(self.hero, "target", None)
            if tgt is not None and getattr(tgt, "alive", False):
                aim = (float(tgt.x), float(tgt.y))
            else:
                facing = 1 if getattr(self.hero, "direction", 1) >= 0 else -1
                aim = (x + facing * 120, y - 8)
        self.skills.append(SkillFX(skill, x, y, self.particles,
                                   aim=aim, radius=WORLD_RADIUS.get(skill)))
        heavy = skill == "r"
        if shake_allowed():
            _feel_shake(6.0 if not heavy else 14.0,
                        0.16 if not heavy else 0.42)
        if heavy:
            _feel_hit_stop(0.06)
        self.particles.burst(x, y + gy * 0.35, 10,
                             speed=(60, 170), life=(0.2, 0.5), size=(2, 4),
                             colors=(P["fx_mid"], P["fx_dark"], P["dust"]),
                             spread=math.tau, gravity=140.0, drag=2.0,
                             shape="dust", layer="back")

    def spawn_ice_shard(self, x, y, aim):
        """Lepaskan shard dari ujung staff ke target."""
        _g, tip = staff_points(self.hero, x, y, False)
        tgt = getattr(self.hero, "target", None)
        if tgt is None or not getattr(tgt, "alive", False):
            tgt = None
        return self.projectiles.spawn(
            tip[0], tip[1], aim[0], aim[1],
            speed=SHARD_SPEED, damage=0, target=tgt, radius=7.0,
            kind="ice",
            on_impact=lambda p: self.on_impact(p.hit_pos.x, p.hit_pos.y,
                                               p.rotation, 1.15, False,
                                               kind="ice"))

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="ice"):
        """Benturan mengenai target: flash, spark, debris, shake, hit-stop."""
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind=kind))
        pw = min(2.0, max(0.35, float(power)))

        if kind == "ice":
            spark, edge, hot = P["ice_hot"], P["ice_light"], P["ice_edge"]
        else:
            spark, edge, hot = P["fx_hot"], P["fx_bright"], P["fx_white"]

        n = int(10 + 8 * pw) + (6 if crit else 0)
        self.particles.burst(
            x, y, n, speed=(120, 320 + 100 * pw), life=(0.16, 0.44),
            size=(2, 5), colors=(spark, hot, edge),
            spread=2.4, direction=angle, drag=3.5, shape="streak",
            additive=True)
        self.particles.burst(
            x, y, int(6 + 3 * pw) + (4 if crit else 0),
            speed=(70, 220), life=(0.28, 0.7), size=(2, 5),
            colors=(edge, P["ice_light"], P["ice_mid"]),
            gravity=460.0, drag=1.1, shape="shard", additive=True,
            rotation_speed=(-16, 16))
        if crit:
            self.particles.burst(
                x, y, 9, speed=(180, 380), life=(0.22, 0.5), size=(2, 4),
                colors=(P["gold_hot"], P["gold"], spark),
                spread=math.tau, gravity=120.0, drag=2.0,
                shape="spark", additive=True)

        if shake_allowed():
            _feel_shake(4.5 + 3.4 * pw + (3.0 if crit else 0.0),
                        0.17 + 0.08 * pw)
        _feel_hit_stop(0.036 + 0.019 * min(1.5, pw) +
                       (0.014 if crit else 0.0))

    def on_hurt(self, amount=1.0):
        """Xerathis terkena serangan: flash + percikan es + debu jubah."""
        self.hit_flash = 0.16
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        self.particles.burst(
            hx, hy - 8, 7, speed=(80, 210), life=(0.16, 0.34), size=(2, 4),
            colors=(P["ice_edge"], P["gold_hot"], P["ice_light"]),
            drag=3.0, shape="streak", additive=True)
        self.particles.burst(
            hx, hy + 6, 4, speed=(30, 90), life=(0.24, 0.5), size=(2, 5),
            colors=(P["robe"], P["smoke"]), gravity=200.0, drag=2.0,
            shape="dust", layer="back")

    def _watch_engine_events(self, x, y):
        """Sinkronkan state debug dari ``active_skill`` engine.

        FX skill di-trigger lewat ``notify_skill_cast`` / 
        ``notify_skill_impact`` (jalur AI/gameplay) supaya tidak pernah
        dobel saat ``active_skill`` juga dibaca di sini.
        """
        skill = getattr(self.hero, "active_skill", None)
        if skill:
            self.state = "SPECIAL" if skill == "r" else "SKILL"
        else:
            self.state = getattr(self.hero, "_xr_state", "IDLE")

    def update(self, dt, x, y):
        self.time += dt
        self.frames += 1
        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)
        self.particles.update(dt)
        for i in self.impacts:
            i.update(dt)
        for sk in self.skills:
            sk.update(dt)
        self.projectiles.update(dt)

        self._watch_engine_events(x, y)

        # -- swing / cast trail sampling
        action, phase, ap = pose_of(self.hero)
        facing = 1 if getattr(self.hero, "direction", 1) >= 0 else -1
        if action in ("attack", "cast", "skill"):
            if not self._swing_seen:
                self._swing_seen = True
                self.on_swing_start(x, y, facing)
            _g, tip = staff_points(self.hero, x, y, False)
            self.trail.push(tip[0], tip[1], facing)
            if action == "attack":
                if ap and (0.30 <= ap <= 0.34) and not self._impact_frame_seen:
                    self._impact_frame_seen = True
                    self.on_swing_impact_frame(x, y, facing)
                elif self._impact_frame_seen and ap > 0.62:
                    self._impact_frame_seen = False
        else:
            if self._swing_seen:
                self._swing_seen = False
                self.on_swing_end()
            self.trail.reset()

        self.impacts = [i for i in self.impacts if i.age < i.life]
        self.skills = [s for s in self.skills if not s.done]

    def draw_ground(self, surface):
        self.particles.draw(surface, "back")
        for sk in self.skills:
            sk.draw_ground(surface)
        # ground glow running during skill cast
        if getattr(self.hero, "active_skill", None):
            skill = getattr(self.hero, "active_skill", None)
            gy = 36
            pulse = math.sin(self.time * 6.0) * 0.25 + 0.75
            r = int(WORLD_RADIUS.get(skill, 40) * pulse)
            ring = ellipse_ring_surface(r, int(r * 0.4), 2,
                                        (*P["fx_bright"], 120))
            _blit_faded(surface, ring, float(getattr(self.hero, "x", 0)),
                        float(getattr(self.hero, "y", 0)) + gy,
                        int(130 * pulse), additive=True)

    def draw_front(self, surface, x, y):
        self.trail.draw(surface, P["ice_edge"], 150, additive=True)
        for i, imp in enumerate(self.impacts):
            imp.draw(surface)
        self.projectiles.draw(surface)
        self.particles.draw(surface, "front")
        for sk in self.skills:
            sk.draw_front(surface)

    def clear(self):
        self.particles.clear()
        self.projectiles.clear()
        self.trail.reset()
        self.impacts.clear()
        self.skills.clear()


# ============================================================================
# 12.  DEBUG OVERLAY
# ============================================================================

def _debug_font():
    try:
        from _render import get_font
        return get_font(14)
    except Exception:
        return None


def draw_debug_overlay(surface, director):
    """Pos debug: hitbox, hurtbox, attack range, projectile collision,
    anim state/frame, FPS, particle count, skill state, attack timer."""
    h = director.hero
    x = float(getattr(h, "x", 0.0))
    y = float(getattr(h, "y", 0.0))
    f = 1 if getattr(h, "direction", 1) >= 0 else -1
    r = max(8, int(getattr(h, "radius", 14)))
    pygame.draw.rect(surface, (80, 170, 255, 150),
                     pygame.Rect(int(x) - r, int(y) - r - 8, r * 2, r * 2), 1)
    rng = max(20, int(getattr(h, "range", 200) * 0.7))
    pygame.draw.line(surface, (255, 210, 60, 150), (int(x), int(y)),
                     (int(x + rng * f), int(y)), 1)
    pygame.draw.rect(surface, (255, 210, 60, 110),
                     pygame.Rect(int(x + rng * f) - 5, int(y) - 7, 10, 14), 1)
    # projectile collision
    for pr in director.projectiles.items:
        pygame.draw.circle(surface, (255, 120, 255, 170),
                           (int(pr.x), int(pr.y)), int(pr.hit_radius), 1)
    fps = director._fps = getattr(director, "_fps", 60.0)
    state = director.state
    phase = director.anim_phase
    lines = [
        f"XERATHIS {state} {phase}",
        f"frame {director.frames} t={director.time:.2f}",
        f"particles={director.particles.count()} proj={director.projectiles.count()}",
        f"skills={len(director.skills)} impacts={len(director.impacts)}",
    ]
    font = _debug_font()
    if font is None:
        return
    px, py = int(x) - 80, int(y) + 36
    for i, line in enumerate(lines):
        s = font.render(line, True, (220, 255, 230))
        surface.blit(s, (px, py + i * 14))


# ============================================================================
# 13.  BUTUH POSE & STATIC
# ============================================================================

def attack_phase(progress):
    """Nama fase serangan untuk progress 0..1."""
    p = max(0.0, min(1.0, float(progress)))
    for name, a, b in ATTACK_PHASES:
        if a <= p < b:
            return name
    return "RECOVERY"


# ============================================================================
# 14.  REGISTRY + API MODUL
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Xerathis."""
    _sync_palette()
    d = getattr(hero, "_xr_fx", None)
    if d is None:
        d = XerathisFXDirector(hero)
        try:
            hero._xr_fx = d
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
            director.hero._xr_fx = None
            director.hero._xr_live_fx = False
    except Exception:                          # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit (rendering pipeline)."""
    if not XERATHIS_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                          # pragma: no cover
        return False
    try:
        hero._xr_live_fx = True
    except Exception:                          # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not getattr(hero, "_xr_live_fx", False):
        return False
    d = getattr(hero, "_xr_fx", None)
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
        return 0.0
    if _feel is not None:
        _LAST_TICK_MS = now
        try:
            step = _feel.fx_dt()
        except Exception:                      # pragma: no cover
            step = 0.0
    else:                                      # pragma: no cover
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
    if step <= 0.0 or not _DIRECTORS:
        return
    for d in _DIRECTORS:
        h = d.hero
        d.update(step, float(getattr(h, "x", 0.0)),
                 float(getattr(h, "y", 0.0)))


def reset_all():
    """Bersihkan seluruh state FX Xerathis."""
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
    """Jumlah partikel Xerathis hidup (dipakai HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def stats():
    try:
        return _feel.stats()
    except Exception:                          # pragma: no cover
        return {"hitstop_frames": 0, "hitstop_total": 0, "shake": 0.0}


def projectiles_for(hero):
    """Daftar proyektil milik unit (diluar renderer debug)."""
    d = getattr(hero, "_xr_fx", None)
    if d is None:
        return []
    return d.projectiles.items


# --- hook yang dipanggil heroes/__init__.py --------------------------------

def draw_ground_layer(surface, hero, x, y):
    if not XERATHIS_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_xr_fx", None)
    if d is not None:
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    if not XERATHIS_FX_ENABLED:
        return
    d = director_for(hero)
    d.draw_front(surface, x, y)


# --- hook yang dipanggil _entity.py / bosses/base_boss.py ------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    if not XERATHIS_FX_ENABLED or hero is None or target is None:
        return
    try:
        power = 0.75 + min(1.5, float(damage) / 70.0)
    except (TypeError, ValueError):
        power = 1.0
    tx = float(getattr(target, "x", getattr(hero, "x", 0.0)))
    ty = float(getattr(target, "y", getattr(hero, "y", 0.0))) - 6.0
    ang = math.atan2(ty - float(getattr(hero, "y", 0.0)),
                     tx - float(getattr(hero, "x", 0.0)))
    director_for(hero).on_impact(tx, ty, ang, power, bool(crit), kind="ice")


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False,
                             kind="ice"):
    if not XERATHIS_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    director_for(hero).on_impact(x, y, angle, power, bool(crit), kind="ice")


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    if not XERATHIS_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    if len(d.skills) >= MAX_SKILLS:
        d.skills.pop(0)
    fx = SkillFX(skill, float(getattr(hero, "x", 0.0)),
                 float(getattr(hero, "y", 0.0)), d.particles,
                 aim=(x, y), radius=radius or WORLD_RADIUS.get(skill))
    d.skills.append(fx)
    d.on_impact(x, y, 0.0,
                1.4 if skill != "r" else 2.1,
                skill == "r", kind="ice")


def notify_skill_cast(hero, skill):
    if not XERATHIS_FX_ENABLED or hero is None or skill not in SKILL_DUR:
        return
    d = director_for(hero)
    d.on_cast(float(getattr(hero, "x", 0.0)),
              float(getattr(hero, "y", 0.0)), skill)


def notify_projectile_cast(hero, x, y):
    """Spawn frost-shard proyektil dari staff ke target (basic attack).

    Renderer memanggil ini saat frame cast aktif dan lapisan hidup sudah
    mengambil alih proyektil; menggantikan ``_spawn_projectile`` canvas.
    """
    if not XERATHIS_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    tgt = getattr(hero, "target", None)
    if tgt is not None and getattr(tgt, "alive", False):
        aim = (float(tgt.x), float(tgt.y))
    else:
        facing = 1 if getattr(hero, "direction", 1) >= 0 else -1
        aim = (x + facing * 130.0, y - 10.0)
    d.spawn_ice_shard(x, y, aim)


def notify_hurt(hero, amount=1.0):
    if not XERATHIS_FX_ENABLED or hero is None:
        return
    director_for(hero).on_hurt(amount)


def _feel_shake(strength, duration):
    try:
        _feel.shake(strength, duration)
    except Exception:
        pass


def _feel_hit_stop(seconds):
    try:
        _feel.hit_stop(seconds)
    except Exception:
        pass
