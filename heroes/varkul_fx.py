# ============================================================================
# heroes/varkul_fx.py
# ----------------------------------------------------------------------------
# VARKUL — THE FROSTFANG / FROST SORCERER  (screen-space live layer)
#
# Badan Varkul digambar lewat ``_NS_varkul`` (bosses/level3.py) ke canvas
# yang di-CACHE lalu diberi outline siluet + pencahayaan. Seperti
# Xerathis/Nyzrak/Gornak, semua yang butuh gerak 60 fps sejati — sapuan
# ark staff, partikel es, proyektil frost bolt, orb chain frost, impact,
# guncangan layar, hit-stop — TIDAK boleh hidup di dalam canvas itu.
# Modul ini adalah lapisan hidup: digambar langsung ke layar pada skala
# 1:1 tiap frame, dengan delta-time nyata (via heroes/combat_feel).
#
# Pembagian kerja (sengaja, supaya tidak ada efek yang digambar 2x):
#
#   RENDERER (canvas, ter-cache)      MODUL INI (layar, hidup)
#   -----------------------------     -----------------------------------
#   rig lich + outline + rim light    trail sapuan staff dari histori nyata
#   bayangan, aura es, platform es    partikel (es, salju, debu, mist)
#   pose idle/walk/attack/cast        proyektil Frost Bolt (sistem nyata)
#   ayunan ARK staff (rotasi theta)   orb Chain Frost + lightning arcs
#   hurt-flash (siluet badan)         IMPACT FX + flash + shockwave
#   fallback skill canvas q/w/e/r     SkillFX lifecycle cast->release->fade
#                                     overlay DEBUG_CHARACTER
#
# 100% PROSEDURAL. Tidak ada PNG / JPG / GIF / sprite-sheet / image.load.
# Semua bentuk dibuat dengan pygame.draw + pygame.Surface + pygame.transform.
#
# Isi modul
#   VARKUL_PALETTE        palette khusus karakter (kontrak 9 kunci + ramp)
#   Particle              partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem        pool + burst + cap, reusable
#   SwingTrail            trail sapuan staff prosedural dari histori posisi
#   ImpactFX              flash + shockwave + debris es + fragmen slash
#   FrostBoltProjectile   proyektil modular (spawn->travel->hit->destroy)
#   ChainFrostOrbProjectile  orb R yang memantul + arc lightning
#   ProjectileSystem      manajer proyektil
#   SkillFX               lifecycle FX skill (cast->charge->release->fade)
#   VarkulFXDirector      satu instance per unit, mengikat semua di atas
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

#: Debug visual untuk karakter VARKUL: hitbox, hurtbox, jangkauan, state
#: animasi, frame, FPS, jumlah partikel, state skill, timer serangan.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
VARKUL_FX_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 190

#: Batas keras proyektil visual per director.
MAX_PROJECTILES = 18

#: Panjang histori trail senjata (jumlah sample posisi crystal staff).
TRAIL_SAMPLES = 16

#: Batas dampak aktif per director & skill sekaligus di layar.
MAX_IMPACTS = 8
MAX_SKILLS = 5

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Kecepatan Frost Bolt (px/detik, ruang dunia).
BOLT_SPEED = 760.0

#: Kecepatan orb Chain Frost (px/detik).
CHAIN_SPEED = 540.0

#: Umur FX skill dalam DETIK. Sinkron dengan ``_NS_varkul`` +
#: ``active_skill_timer`` AI (50/60/50/80 langkah sim = 0.83/1.00/0.83/1.33s)
#: plus sisa after-glow supaya efek tidak "terpotong".
SKILL_TOTAL = {"q": 1.10, "w": 1.38, "e": 1.12, "r": 2.30}

#: Durasi pose per skill (frame) — dipakai untuk memetakan umur FX ke
#: fase yang sama dengan yang dibaca renderer.
SKILL_DUR = {"q": 50, "w": 60, "e": 50, "r": 80}

#: Jumlah pantulan maksimal orb Chain Frost.
CHAIN_BOUNCES = 4

#: Radius EFEK di ruang dunia. q/w = skill point; e/r = area.
WORLD_RADIUS = {"q": 54.0, "w": 34.0, "e": 95.0, "r": 120.0}

#: Fase serangan (fraksi 0..1 dari durasi serangan).
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.14),
    ("WINDUP",       0.14, 0.32),
    ("SWING",        0.32, 0.52),
    ("IMPACT",       0.52, 0.64),
    ("FOLLOW",       0.64, 0.82),
    ("RECOVERY",     0.82, 1.00),
)

#: Jendela hit aktif (dipakai debug & game feel).
ATTACK_ACTIVE_WINDOW = (0.38, 0.64)
ATTACK_IMPACT_FRAME = 0.52

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
# 1.  PALETTE  —  frost sorcerer: es biru + ungu lich + emas kuno
# ============================================================================

VARKUL_PALETTE = {
    # ── kontrak palette karakter (kontrak 9 kunci wajib) ───────────
    "outline":    (4,     6,  15),
    "shadow":     (18,   12,  35),
    "dark":       (38,   25,  68),
    "body":       (68,   45, 115),
    "mid":        (105,  78, 160),
    "light":      (145, 115, 200),
    "highlight":  (195, 230, 255),
    "weapon":     (110, 150, 195),
    "fx":         (245, 252, 255),

    # ── ramp es / frost ────────────────────────────────────────────
    "fx_darkest": (10,   30,  75),
    "fx_dark":    (25,   70, 145),
    "fx_mid":     (70,  140, 225),
    "fx_light":   (140, 200, 250),
    "fx_bright":  (195, 230, 255),
    "fx_hot":     (225, 245, 255),
    "fx_white":   (245, 252, 255),

    # ── material fisik ─────────────────────────────────────────────
    "bone":       (155, 175, 195),
    "bone_light": (215, 230, 240),
    "bone_shine": (245, 250, 255),
    "robe":       (68,   45, 115),
    "robe_deep":  (18,   12,  35),
    "armor":      (30,   55,  95),
    "armor_mid":  (55,   90, 140),
    "gold":       (170, 130,  40),
    "gold_hot":   (255, 235, 165),

    # ── bahan es (spark & serpihan) ────────────────────────────────
    "ice_dark":   (10,   30,  75),
    "ice_mid":    (70,  140, 225),
    "ice_light":  (140, 200, 250),
    "ice_bright": (195, 230, 255),
    "ice_edge":   (195, 230, 255),
    "ice_hot":    (225, 245, 255),
    "ice_white":  (245, 252, 255),

    # ── mata lich ──────────────────────────────────────────────────
    "eye":        (70,  140, 240),
    "eye_hot":    (220, 245, 255),

    # ── sisa destinasi (debu / asap / kabut kubur) ────────────────
    "smoke":      (26,   36,  66),
    "ash":        (74,   64,  96),
    "dust":       (120, 150, 172),
}

P = VARKUL_PALETTE

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
    "weapon": "armor_light",
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
    "ice_bright": "ice_bright",
    "ice_edge": "ice_bright",
    "ice_hot": "ice_hot",
    "ice_white": "ice_white",
    "bone": "bone_mid",
    "bone_light": "bone_light",
    "bone_shine": "bone_shine",
    "robe": "robe_mid",
    "robe_deep": "robe_darkest",
    "armor": "armor_dark",
    "armor_mid": "armor_mid",
    "gold": "gold_mid",
    "gold_hot": "gold_shine",
    "eye": "eye_mid",
    "eye_hot": "eye_hot",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Salin warna tema dari ``_NS_varkul.PALETTE`` sekali saja.

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
            P[dst] = tuple(int(c) for c in col[:3])


# ============================================================================
# 2.  JEMBATAN KE RENDERER  (satu sumber geometri & pose)
# ============================================================================

_RENDERER = None          # None = belum dicari, False = tidak ada


def _renderer():
    """``_NS_varkul`` atau None. Diimpor malas: modul boss besar."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level3 import _NS_varkul as G
            _RENDERER = G
        except Exception:                      # pragma: no cover
            _RENDERER = False
    return _RENDERER or None


#: geometri cadangan — identik dengan ``_NS_varkul._staff_arc`` supaya
#: modul tetap hidup kalau renderer tidak bisa diimpor.
_ARC_FALLBACK = (
    # (t0, t1, th0, th1, ease) — theta dalam radian dari vertikal;
    # positif = mengayun ke arah depan (facing).
    (0.00, 0.14, 0.00,  0.22, "out"),      # ANTICIPATION: angkat
    (0.14, 0.32, 0.22, -1.13, "io"),       # WINDUP: putar ke belakang
    (0.32, 0.52, -1.13, 1.42, "oc"),       # SWING: sapu cepat ke depan
    (0.52, 0.64, 1.42,  1.42, "hold"),     # IMPACT: tahan + overshoot
    (0.64, 0.82, 1.42, -0.48, "io"),       # FOLLOW THROUGH
    (0.82, 1.00, -0.48, 0.00, "io"),       # RECOVERY
)


def _ease(kind, t):
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    if kind == "out":
        return 1.0 - (1.0 - t) * (1.0 - t)
    if kind == "oc":                        # out-cubic
        return 1.0 - (1.0 - t) ** 3
    if kind == "hold":
        return math.sin(t * math.pi)
    # in-out
    return t * t * (3.0 - 2.0 * t)


def _fallback_arc(progress):
    """(theta, lift) staff untuk progress 0..1 tanpa renderer."""
    p = max(0.0, min(1.0, float(progress)))
    for t0, t1, a0, a1, kind in _ARC_FALLBACK:
        if t0 <= p < t1 or (p >= 1.0 and t1 >= 1.0):
            e = _ease(kind, (p - t0) / max(0.0001, t1 - t0))
            theta = a0 + (a1 - a0) * e
            return theta, _hand_lift(p)
    return 0.0, 0.0


def _hand_lift(progress):
    """Tinggi tangan staff relatif (0 = idle, positif = terangkat).

    Harus identik dengan ``_NS_varkul._staff_lift`` — keduanya dibaca
    renderer canvas dan modul hidup supaya trail/proyektil lahir tepat
    di crystal staff.
    """
    p = max(0.0, min(1.0, float(progress)))
    if p < 0.32:
        return _ease("out", p / 0.32) * 1.0
    if p < 0.52:
        return 1.0 - _ease("oc", (p - 0.32) / 0.20) * 0.85
    if p < 0.82:
        return 0.15 + _ease("io", (p - 0.52) / 0.30) * 0.25
    return 0.4 * (1.0 - _ease("io", (p - 0.82) / 0.18))


def staff_arc(progress):
    """(theta, lift) pose ark staff — SATU sumber kebenaran.

    Membaca ``_NS_varkul._staff_arc`` (dipakai renderer canvas juga);
    kalau renderer tidak ada, pakai tabel fallback identik di atas.
    """
    R = _renderer()
    fn = getattr(R, "_staff_arc", None) if R is not None else None
    if fn is not None:
        try:
            return fn(progress)
        except Exception:                    # pragma: no cover
            pass
    return _fallback_arc(progress)


def _fallback_pose(boss):
    """(action, phase, ap) tanpa renderer: baca atribut yang sudah ada."""
    skill = getattr(boss, "active_skill", None)
    action = getattr(boss, "_vk_pose_action", None)
    if action is None:
        action = {"q": "cast", "w": "cast", "e": "cast",
                  "r": "cast"}.get(skill)
    if action is None:
        action = ("attack" if getattr(boss, "_vk_attack_active", False)
                  else "idle")
    phase = float(getattr(boss, "pulse", 0.0) or 0.0)
    ap = 0.0
    if action == "attack":
        ap = float(getattr(boss, "_vk_attack_progress", 0.0) or 0.0)
    return action, phase, ap


def pose_of(boss):
    """Pose badan yang dipakai renderer (action, phase, attack_progress)."""
    R = _renderer()
    if R is None:
        return _fallback_pose(boss)
    try:
        action = getattr(boss, "_vk_pose_action", None)
        if action is None:
            return _fallback_pose(boss)
        phase = float(getattr(boss, "_vk_phase", getattr(boss, "pulse", 0.0)))
        ap = float(getattr(boss, "_vk_attack_progress", 0.0) or 0.0)
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
    return (x + local[0] * k * facing, y + local[1] * k)


def staff_points(boss, x, y, back=False):
    """(grip, tip) staff dalam ruang layar untuk trail & proyektil.

    Renderer menggambar staff dengan tangan di sisi BELAKANG
    (``staff_side = -facing``) dan kristal es di kepala staff.  Saat
    menyerang, seluruh staff berputar mengikuti ark ``staff_arc`` —
    crystal tip menelusuri LENGKUNGAN, dan di titik inilah trail plus
    proyektil lahir, sehingga semuanya konsisten dengan canvas.
    """
    action, phase, ap = pose_of(boss)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)

    if back:
        grip = (x - facing * 23.0 * k, y + 14.0 * k)
        tip = (x - facing * 21.0 * k, y - 30.0 * k)
        return grip, tip

    if action == "attack":
        theta, lift = staff_arc(ap)
        hand_x = x - facing * (23.0 - 6.0 * lift) * k
        hand_y = y + (8.0 - 30.0 * lift) * k
        L = 44.0 * k
        top_x = hand_x + facing * math.sin(theta) * L
        top_y = hand_y - math.cos(theta) * L
        # crystal head sedikit di atas ujung pole, searah ark
        head_x = top_x + facing * math.sin(theta) * 6.0 * k
        head_y = top_y - math.cos(theta) * 6.0 * k
        return (hand_x, hand_y), (head_x, head_y)

    if action == "cast":
        pulse = math.sin(phase * 2.4) * 2.0 * k
        hand_x = x - facing * 17.0 * k
        hand_y = y - 22.0 * k + pulse * 0.2
        top_x = hand_x - facing * 3.2 * k
        top_y = hand_y - 43.9 * k
        return (hand_x, hand_y), (top_x, top_y - 4.0 * k)

    # idle / walk: sway halus
    sway = math.sin(phase * 0.7) * 1.0 * k
    hand_x = x - facing * 23.0 * k
    hand_y = y + (14.0 + sway * 0.4) * k
    top_x = hand_x - facing * 2.0 * k
    top_y = hand_y - (40.0 + sway) * k
    return (hand_x, hand_y), (top_x, top_y - 4.0 * k)


def orb_points(boss, x, y):
    """(pusat orb tangan) dalam ruang layar — sumber proyektil skill W."""
    action, phase, ap = pose_of(boss)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)
    if action == "attack":
        ext = 1.0 if ap < 0.55 else max(0.3, 1.0 - (ap - 0.55) * 1.6)
        oh_x = x + facing * (18.0 + ext * 10.0) * k
        oh_y = y - (8.0 + ext * 12.0) * k
        return (oh_x + facing * 4.0 * k, oh_y + 2.0 * k)
    if action == "cast":
        return (x + facing * 22.0 * k, y - 14.0 * k)
    return (x + facing * 18.0 * k, y + 2.0 * k)


def target_point(boss, x, y):
    """Titik target serangan dasar (layar) untuk proyektil."""
    tgt = getattr(boss, "target", None)
    if tgt is not None and getattr(tgt, "alive", False):
        return (float(getattr(tgt, "x", x + 120.0)),
                float(getattr(tgt, "y", y)) - 6.0)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    return (x + facing * 150.0, y - 10.0)


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
    if type(color) is tuple and len(color) == 3:
        _r, _g, _b = color
        if (type(_r) is int and type(_g) is int and type(_b) is int
                and 0 <= _r <= 255 and 0 <= _g <= 255 and 0 <= _b <= 255):
            return color
    return tuple(int(max(0, min(255, c))) for c in color)


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
    """Cached soft radial glow (dipakai glow proyektil/burst)."""
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
                    pygame.draw.aacircle(surf, color_a, (radius + 2, radius + 2), r)
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
            for a in [a0 + (a1 - a0) * t for t in (0.0, 0.25, 0.5, 0.75, 1.0)]:
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


def snowflake_surface(size, color):
    """Cached kepingan salju 6 lengan (chunky pixel)."""
    size = max(2, int(size))
    key = ("snow", size, color)
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((size * 2 + 3, size * 2 + 3), pygame.SRCALPHA)
    c = size + 1
    for i in range(6):
        a = i * math.pi / 3
        x1 = c + math.cos(a) * size
        y1 = c + math.sin(a) * size
        pygame.draw.line(surf, color, (c, c), (x1, y1), 1)
        if size >= 3:
            bx = c + math.cos(a) * size * 0.55
            by = c + math.sin(a) * size * 0.55
            for s in (-1, 1):
                ba = a + s * 0.6
                pygame.draw.line(surf, color, (bx, by),
                                 (bx + math.cos(ba) * size * 0.35,
                                  by + math.sin(ba) * size * 0.35), 1)
    pygame.draw.circle(surf, color, (c, c), 1)
    return _cache_put(key, surf)


def shard_poly(surface, cx, cy, ang, length, width, color, alpha=255):
    """Gambar shard es tajam (polygon directional)."""
    ca, sa = math.cos(ang), math.sin(ang)
    tip = (cx + ca * length, cy + sa * length)
    left = (cx + math.cos(ang + 2.4) * width * 0.45,
            cy + math.sin(ang + 2.4) * width * 0.45)
    right = (cx + math.cos(ang - 2.4) * width * 0.45,
             cy + math.sin(ang - 2.4) * width * 0.45)
    color_a = (*color[:3], alpha)
    pygame.draw.polygon(surface, color_a, [tip, left, right])
    return tip


def _lightning_points(a, b, segs, jag, seed=0):
    """Titik-titik petir bergerigi dari a ke b (deterministik via seed)."""
    pts = []
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    for i in range(segs + 1):
        t = i / float(segs)
        off = 0.0
        if 0 < i < segs:
            off = (_hash01(seed + i * 131) - 0.5) * 2.0 * jag
        pts.append((a[0] + dx * t + nx * off, a[1] + dy * t + ny * off))
    return pts


_SCRATCH_POOL = []


def _scratch(w, h):
    for s in _SCRATCH_POOL:
        if s.get_width() >= w and s.get_height() >= h:
            s.fill((0, 0, 0, 0))
            return s
    s = pygame.Surface((max(1, int(w)), max(1, int(h))), pygame.SRCALPHA)
    if len(_SCRATCH_POOL) < 8:
        _SCRATCH_POOL.append(s)
    return s


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
    # Non-additif: set_alpha langsung pada surface cache (tanpa copy).
    # Jalur aditif tetap lewat _scratch supaya premultiply alpha dipertahankan.
    if additive:
        tmp = _scratch(rect.width, rect.height)
        tmp.blit(surf, (0, 0))
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
            ang = math.atan2(self.vy, self.vx)
            tip = (x + math.cos(ang) * s * 1.8, y + math.sin(ang) * s * 1.8)
            lx = x + math.cos(ang + 2.4) * s * 0.6
            ly = y + math.sin(ang + 2.4) * s * 0.6
            rx = x + math.cos(ang - 2.4) * s * 0.6
            ry = y + math.sin(ang - 2.4) * s * 0.6
            pygame.draw.polygon(surface, color, [tip, (lx, ly), (rx, ry)])
        elif self.shape == "dust":
            pygame.draw.circle(surface, color, (x, y), max(1, int(s * 0.5)))
        elif self.shape == "mist":
            r = max(1, int(s))
            g = glow_surface(r + 2, self.color, 0.35)
            _blit_faded(surface, g, x, y, int(a * 0.6), additive=True)
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
        elif self.shape == "snow":
            flake = snowflake_surface(int(s) + 2, self.color)
            _blit_faded(surface, flake, x, y, a)
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
# 6.  SWING TRAIL  —  sabit es dari histori posisi crystal staff
# ============================================================================

class SwingTrail:
    """Pita sapuan staff prosedural dari histori posisi crystal staff.

    Sample minimal 3-4 posisi lama + posisi sekarang; poligon transparan
    di-build dari sisi depan (leading edge) dan belakang (trailing edge)
    sehingga trail terlihat mengikuti ARK ayunan — staff berputar, maka
    trail membentuk sabit, bukan garis statis.
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
        poly = self._poly(1.0, 7.0)
        if poly is None:
            return
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        min_x, min_y = int(min(xs)) - 2, int(min(ys)) - 2
        w = int(max(xs)) - min_x + 4
        h = int(max(ys)) - min_y + 4
        if w <= 0 or h <= 0 or w > 640 or h > 640:
            return
        tmp = _scratch(w, h)
        shifted = [(px - min_x, py - min_y) for px, py in poly]
        pygame.draw.polygon(tmp, (*color[:3], int(alpha * 0.45)), shifted)
        # leading edge terang
        pts = self.points
        for i in range(1, len(pts)):
            pygame.draw.line(tmp, (*color[:3], int(alpha * 0.8)),
                             (pts[i - 1][0] - min_x, pts[i - 1][1] - min_y),
                             (pts[i][0] - min_x, pts[i][1] - min_y), 2)
        surface.blit(tmp, (min_x, min_y),
                     special_flags=pygame.BLEND_RGB_ADD if additive else 0)


# ============================================================================
# 7.  IMPACT FX  —  flash + shockwave + serpihan es + fragmen sabit
# ============================================================================

class ImpactFX:
    """Flash + ring shockwave + shard es + fragmen sabit tunggal."""

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
        r = int((6 + 14 * p) * (0.3 + 0.7 * t))
        glow = glow_surface(max(6, r), P["fx_hot"], 0.7)
        _blit_faded(surface, glow, self.x, self.y, int(130 * fade),
                    additive=True)

        # ring shockwave (chunky, dua lapis)
        rr = int((22 + 16 * p) * (0.2 + 0.85 * t))
        ring = ring_surface(rr, max(1, int(3 * p)), P["fx_bright"],
                            int(200 * fade))
        _blit_faded(surface, ring, self.x, self.y, int(220 * fade),
                    additive=True)
        ring2 = ring_surface(max(4, rr - 6), 1, P["ice_light"],
                             int(140 * fade), dashed=10)
        _blit_faded(surface, ring2, self.x, self.y, int(160 * fade),
                    additive=True)

        # fragmen sabit (arc) di sekitar sudut benturan
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
# 8.  PROJECTILE  —  Frost Bolt (kristal directional) + Chain Frost Orb
# ============================================================================

class FrostBoltProjectile:
    """Proyektil frost bolt modular.

    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY.
    Punya position, velocity, speed, damage, lifetime, target, radius,
    rotation, trail, particles, active — semua atribut wajib.
    """

    __slots__ = ("x", "y", "velocity", "speed", "damage", "lifetime",
                 "target", "radius", "rotation", "trail", "particles",
                 "active", "sx", "sy", "hit_radius", "kind", "age",
                 "hit_pos", "on_impact", "homing", "hit_target",
                 "trail_len", "spin")

    def __init__(self, sx, sy, tx, ty, speed=BOLT_SPEED, damage=0,
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
        self.lifetime = 3.2 if kind != "bolt" else 2.4
        self.particles = particles
        self.on_impact = on_impact
        self.active = True
        self.hit_pos = None
        self.rotation = 0.0
        self.spin = 5.0
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

        # target tracking lembut (homing)
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
                                                    self.velocity.x)
                         * dt * 4.0 + self.spin * dt)

        self.trail.append((self.x, self.y, self.age))
        if len(self.trail) > self.trail_len:
            self.trail.pop(0)

        # deteksi tabrak target
        if self.target is not None and getattr(self.target, "alive", False):
            tx = float(getattr(self.target, "x", self.x))
            ty = float(getattr(self.target, "y", self.y))
            hr = max(10.0, self.radius + float(
                getattr(self.target, "radius", 10.0)) * 0.55)
            if math.hypot(tx - self.x, ty - self.y) <= hr:
                self._hit(tx, ty - 4.0)
                return

        # partikel jejak frost mist
        if self.particles is not None and len(self.trail) % 2 == 0:
            self.particles.burst(self.x, self.y, 1,
                                 speed=(10, 45), life=(0.12, 0.3),
                                 size=(1, 2),
                                 colors=(P["ice_light"], P["ice_edge"]),
                                 spread=1.4,
                                 direction=math.atan2(self.velocity.y,
                                                      self.velocity.x)
                                 + math.pi,
                                 drag=1.4, shape="spark", additive=True)

    def _hit(self, x, y):
        if not self.active:
            return
        self.hit_pos = pygame.Vector2(x, y)
        self.hit_target = True
        self.active = False
        if self.on_impact:
            try:
                self.on_impact(self)
            except Exception:
                pass

    def draw(self, surface):
        if not self.active:
            return
        # trail (fading frost mist)
        n = len(self.trail)
        for i, (tx, ty, a) in enumerate(self.trail):
            t = (i + 1) / max(1, n)
            alpha = int(35 + 110 * t * (1.0 - self.age / self.lifetime))
            r = max(1, int(2.0 + 3.5 * t))
            _blit_faded(surface, glow_surface(max(6, r), P["ice_dark"], 0.5),
                        tx, ty, alpha, additive=True)
        # glow (ketat, bukan bola lembut)
        _blit_faded(surface, glow_surface(11, P["ice_mid"], 0.5),
                    self.x, self.y, 120, additive=True)
        # directional shard body
        self._draw_shard(surface, self.x, self.y, self.rotation, 15.0, 5.0)

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
        pygame.draw.circle(surface, P["ice_hot"],
                           (int(tip[0]), int(tip[1])), 1)
        # halo shard berputar (bukan lingkaran polos)
        for i in range(3):
            a = self.rotation * 2.0 + i * math.tau / 3
            sx = px + math.cos(a) * 11.0
            sy = py + math.sin(a) * 11.0
            shard_poly(surface, sx, sy, a + math.pi / 2, 4.0, 2.0,
                       P["ice_light"], 200)


class ChainFrostOrbProjectile:
    """Orb Chain Frost (R): terbang ke target, memantul ke titik berikutnya.

    Setiap pantulan memicu nova kecil + arc lightning ke titik lama,
    lalu orb menerus. Visual: core + glow + cincin shard berputar;
    JEJAK berupa bola kabut es yang memudar.
    """

    __slots__ = ("x", "y", "velocity", "speed", "damage", "lifetime",
                 "target", "radius", "rotation", "trail", "particles",
                 "active", "age", "hit_radius", "bounces_left", "waypoint",
                 "on_bounce", "on_expire", "seed")

    def __init__(self, sx, sy, first_waypoint, particles=None,
                 speed=CHAIN_SPEED, bounces=CHAIN_BOUNCES,
                 on_bounce=None, on_expire=None, seed=0):
        self.x = float(sx)
        self.y = float(sy)
        self.speed = float(speed)
        self.damage = 0
        self.target = None
        self.radius = 9.0
        self.hit_radius = 12.0
        self.age = 0.0
        self.lifetime = 2.8
        self.particles = particles
        self.active = True
        self.rotation = 0.0
        self.bounces_left = int(bounces)
        self.waypoint = (float(first_waypoint[0]), float(first_waypoint[1]))
        self.trail = []
        self.on_bounce = on_bounce
        self.on_expire = on_expire
        self.seed = int(seed)
        dx = self.waypoint[0] - self.x
        dy = self.waypoint[1] - self.y
        L = math.hypot(dx, dy) or 1.0
        self.velocity = pygame.Vector2(dx / L, dy / L)

    def _pick_next_waypoint(self):
        """Pantulan berikutnya: condong ke arah acak terarah (bukan acak
        murni supaya tetap berada di area musuh)."""
        ang = self.age * 0.9 + _hash01(self.seed + self.bounces_left * 17) \
            * math.tau
        dist = 90.0 + _hash01(self.seed * 7 + self.bounces_left) * 70.0
        self.waypoint = (self.x + math.cos(ang) * dist,
                         self.y + math.sin(ang) * dist * 0.6)

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age >= self.lifetime:
            self._expire()
            return
        dx = self.waypoint[0] - self.x
        dy = self.waypoint[1] - self.y
        dist = math.hypot(dx, dy)
        if dist < max(6.0, self.speed * dt):
            # sampai waypoint -> bounce atau mati
            if self.bounces_left > 0:
                self.bounces_left -= 1
                if self.on_bounce:
                    try:
                        self.on_bounce(self)
                    except Exception:
                        pass
                self._pick_next_waypoint()
                ndx = self.waypoint[0] - self.x
                ndy = self.waypoint[1] - self.y
                L = math.hypot(ndx, ndy) or 1.0
                self.velocity = pygame.Vector2(ndx / L, ndy / L)
            else:
                self._expire()
                return
        else:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
        self.rotation += dt * 7.0
        self.trail.append((self.x, self.y))
        if len(self.trail) > 20:
            self.trail.pop(0)
        if self.particles is not None and len(self.trail) % 3 == 0:
            self.particles.burst(self.x, self.y, 1,
                                 speed=(8, 40), life=(0.2, 0.5),
                                 size=(2, 4),
                                 colors=(P["ice_mid"], P["ice_light"]),
                                 spread=math.tau, drag=1.6,
                                 shape="mist", additive=True, layer="back")

    def _expire(self):
        self.active = False
        if self.on_expire:
            try:
                self.on_expire(self)
            except Exception:
                pass

    def draw(self, surface):
        # trail bola kabut memudar
        n = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            t = (i + 1) / max(1, n)
            r = 3 + int(5.0 * t)
            _blit_faded(surface,
                        glow_surface(r + 3, P["ice_dark"], 0.42),
                        tx, ty, int(30 + 90 * t), additive=True)
        # glow + core
        _blit_faded(surface, glow_surface(20, P["ice_mid"], 0.75),
                    self.x, self.y, 170, additive=True)
        px, py = int(self.x), int(self.y)
        pygame.draw.circle(surface, P["ice_dark"], (px, py), 9)
        pygame.draw.circle(surface, P["ice_mid"], (px, py), 7)
        pygame.draw.circle(surface, P["ice_light"], (px - 1, py - 1), 5)
        pygame.draw.circle(surface, P["ice_bright"], (px - 1, py - 1), 3)
        pygame.draw.circle(surface, P["ice_white"], (px - 1, py - 2), 1)
        # cincin shard berputar (directional shape)
        for i in range(5):
            a = self.rotation + i * math.tau / 5
            sx = px + math.cos(a) * 13
            sy = py + math.sin(a) * 13
            shard_poly(surface, sx, sy, a + math.pi / 2, 6.0, 3.0,
                       P["ice_light"], 220)
        # arc lightning ke trail lama
        if n >= 8:
            a = self.trail[-8]
            pts = _lightning_points((self.x, self.y), a, 5, 5.0,
                                    self.seed + int(self.age * 20))
            pygame.draw.lines(surface, (*P["ice_light"], 130), False,
                              [(int(px2), int(py2)) for px2, py2 in pts], 1)


# ============================================================================
# 9.  PROJECTILE SYSTEM
# ============================================================================

class ProjectileSystem:
    """Manajer proyektil dengan pool maksimal."""

    def __init__(self, particles=None):
        self.particles = particles
        self.items = []

    def spawn(self, sx, sy, tx, ty, speed=BOLT_SPEED, damage=0,
              target=None, radius=7.0, kind="ice", trail_len=12,
              on_impact=None):
        if len(self.items) >= MAX_PROJECTILES:
            self.items.pop(0)
        pr = FrostBoltProjectile(
            sx, sy, tx, ty, speed, damage, target, radius, kind,
            trail_len, self.particles, on_impact)
        self.items.append(pr)
        return pr

    def spawn_chain_orb(self, sx, sy, waypoint, speed=CHAIN_SPEED,
                        bounces=CHAIN_BOUNCES, on_bounce=None,
                        on_expire=None, seed=0):
        if len(self.items) >= MAX_PROJECTILES:
            self.items.pop(0)
        orb = ChainFrostOrbProjectile(
            sx, sy, waypoint, self.particles, speed, bounces,
            on_bounce, on_expire, seed)
        self.items.append(orb)
        return orb

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
# 10.  SKILL FX  (Q Frost Blast, W Frostbite, E Sacrifice, R Chain Frost)
# ============================================================================

class SkillFX:
    """Satu skill aktif + lifecycle (cast -> charge -> release -> fade).

    Tiap fase punya visualnya sendiri dan TIDAK semuanya lingkaran:
    telegraph cincin putus, komets dengan halo shard, kurungan es
    poligonal, pentagram rune, dan petir es bergerigi.
    """

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
        if self.age >= dur + 0.30 and not self._after:
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
        dt = self.age / max(0.001, self.life)
        if dt > 0.72:
            return max(0.0, 1.0 - (dt - 0.72) / 0.28)
        return 1.0

    def _emit_release(self):
        """Partikel saat skill dilepas (impact frame AI)."""
        if self.particles is None:
            return
        x, y = self.aim[0], self.aim[1]
        if self.skill == "q":
            # ledakan frost: serpihan shard + spark
            self.particles.burst(x, y, 20, speed=(90, 280),
                                 life=(0.18, 0.65), size=(2, 5),
                                 colors=(P["ice_hot"], P["ice_edge"],
                                         P["ice_light"]),
                                 spread=math.tau, gravity=110.0,
                                 shape="shard", additive=True,
                                 rotation_speed=(-18, 18))
            self.particles.burst(x, y, 10, speed=(30, 120),
                                 life=(0.3, 0.8), size=(1, 3),
                                 colors=(P["ice_light"], P["ice_mid"]),
                                 spread=math.tau, gravity=40.0,
                                 shape="snow", rotation_speed=(-3, 3))
        elif self.skill == "w":
            # kurungan es terbentuk: serpihan naik + kabut dingin
            self.particles.burst(x, y, 14, speed=(30, 150),
                                 life=(0.25, 0.7), size=(2, 4),
                                 colors=(P["ice_hot"], P["fx_bright"]),
                                 spread=math.tau, gravity=-60.0,
                                 shape="shard", additive=True,
                                 rotation_speed=(-14, 14))
            self.particles.burst(x, y, 10, speed=(6, 40),
                                 life=(0.5, 1.1), size=(3, 6),
                                 colors=(P["ice_mid"], P["ice_dark"]),
                                 spread=math.tau, shape="mist",
                                 additive=True, layer="back")
        elif self.skill == "e":
            # jiwa terbangun dari lingkaran pengorbanan
            self.particles.burst(x, y + 10, 16, speed=(18, 70),
                                 life=(0.5, 1.2), size=(2, 4),
                                 colors=(P["fx_bright"], P["fx_hot"],
                                         P["ice_light"]),
                                 spread=0.7, direction=-math.pi / 2,
                                 gravity=-70.0, drag=1.2,
                                 shape="spark", additive=True)
            self.particles.burst(x, y + 14, 8, speed=(10, 50),
                                 life=(0.6, 1.3), size=(3, 6),
                                 colors=(P["ice_mid"], P["smoke"]),
                                 spread=math.tau, gravity=-25.0,
                                 shape="mist", additive=True, layer="back")
        elif self.skill == "r":
            # lepas orb: burst ledakan kecil + salju
            self.particles.burst(self.x, self.y - 20, 18, speed=(80, 240),
                                 life=(0.2, 0.6), size=(2, 5),
                                 colors=(P["fx_white"], P["ice_edge"],
                                         P["ice_light"]),
                                 spread=math.tau, gravity=-20.0,
                                 shape="shard", additive=True,
                                 rotation_speed=(-22, 22))

    def _emit_after(self):
        """After-effect: patch es / kabut sisa."""
        if self.particles is None:
            return
        x, y = self.aim[0], self.aim[1]
        if self.skill in ("q", "w"):
            self.particles.burst(x, y + 8, 7, speed=(14, 60),
                                 life=(0.3, 0.8), size=(2, 5),
                                 colors=(P["fx_dark"], P["ice_mid"]),
                                 spread=math.tau, gravity=90.0,
                                 shape="dust", layer="back")
        elif self.skill == "r":
            self.particles.burst(x, y, 6, speed=(12, 50),
                                 life=(0.4, 0.9), size=(2, 4),
                                 colors=(P["ice_mid"], P["ice_dark"]),
                                 spread=math.tau, shape="snow",
                                 rotation_speed=(-2, 2))

    # ------------------------------------------------------------------
    # GROUND LAYERS
    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        fade = self._fade()
        if fade <= 0.0:
            return
        t = self._t()
        x, y = self.aim[0], self.aim[1]
        if self.skill == "q":
            # TELEGRAPH: cincin putus elips + mark berputar
            r = int(self.radius * (0.55 + 0.45 * min(1.0, t * 2.0)))
            ring = ellipse_ring_surface(r, int(r * 0.45), 2,
                                        (*P["ice_dark"], 210))
            _blit_faded(surface, ring, x, y + 12, int(170 * fade),
                        additive=True)
            dashes = ring_surface(max(6, r - 6), 1, P["ice_mid"],
                                  int(150 * fade), dashed=12)
            _blit_faded(surface, dashes, x, y + 12,
                        int(150 * fade * (0.6 + 0.4 * math.sin(t * 14.0))),
                        additive=True)
        elif self.skill == "e":
            # PENTAGRAM: dua elips rune + bintang lima + glints orbit
            self._draw_pentagram(surface, self.x, self.y, t, fade)
        elif self.skill == "r":
            # area ultimate: cincin ganda + mark salju
            r = int(self.radius * (0.55 + 0.45 * t))
            ring = ellipse_ring_surface(r, int(r * 0.42), 4,
                                        (*P["fx_bright"], 190))
            _blit_faded(surface, ring, x, y + 10, int(170 * fade),
                        additive=True)
            dashes = ring_surface(max(6, r - 8), 1, P["ice_light"],
                                  int(150 * fade), dashed=16)
            _blit_faded(surface, dashes, x, y + 10, int(140 * fade),
                        additive=True)
            for i in range(10):
                a = t * 3.0 + i * math.tau / 10
                px = x + math.cos(a) * r * 0.86
                py = y + 12 + math.sin(a) * r * 0.36
                flake = snowflake_surface(3, (*P["ice_hot"],))
                _blit_faded(surface, flake, px, py, int(200 * fade))

    def _draw_pentagram(self, surface, cx, cy, t, fade):
        """Lingkaran pengorbanan: pentagram rune di tanah."""
        r = int(self.radius * (0.7 + 0.3 * min(1.0, t * 1.6)))
        pulse = 0.75 + 0.25 * math.sin(t * 14.0)
        cx_i, cy_i = int(cx), int(cy + 14)
        rx, ry = r, max(6, int(r * 0.45))
        # dua cincin elips
        ring = ellipse_ring_surface(rx, ry, 2, (*P["ice_dark"], 220))
        _blit_faded(surface, ring, cx_i, cy_i, int(190 * fade * pulse),
                    additive=True)
        ring2 = ellipse_ring_surface(max(4, rx - 7), max(4, ry - 3), 1,
                                     (*P["ice_mid"], 200))
        _blit_faded(surface, ring2, cx_i, cy_i, int(160 * fade * pulse),
                    additive=True)
        # bintang lima (pentagram) — garis lurus antar sudut
        pts = []
        rot = t * 0.5
        for i in range(5):
            a = -math.pi / 2 + i * math.tau / 5 + rot
            pts.append((cx + math.cos(a) * (rx - 8),
                        cy_i + math.sin(a) * (ry - 3)))
        tmp = _scratch(rx * 2 + 12, ry * 2 + 12)
        ox, oy = rx + 6, ry + 6
        for i in range(5):
            p1 = pts[i]
            p2 = pts[(i + 2) % 5]
            pygame.draw.line(tmp, (*P["ice_light"], int(210 * fade * pulse)),
                             (p1[0] - cx + ox, p1[1] - cy_i + oy),
                             (p2[0] - cx + ox, p2[1] - cy_i + oy), 2)
        surface.blit(tmp, (int(cx) - ox, int(cy_i) - oy),
                     special_flags=pygame.BLEND_RGB_ADD)
        # glints orbit
        for i in range(6):
            a = rot * 2.0 + i * math.tau / 6
            px = cx + math.cos(a) * rx * 0.92
            py = cy_i + math.sin(a) * ry * 0.92
            pygame.draw.circle(surface,
                               (*P["ice_hot"], int(220 * fade)),
                               (int(px), int(py)), 2)

    # ------------------------------------------------------------------
    # FRONT LAYERS
    # ------------------------------------------------------------------
    def draw_front(self, surface):
        fade = self._fade()
        if fade <= 0.0:
            return
        t = self._t()
        x, y = self.aim[0], self.aim[1]
        if self.skill == "q":
            self._front_frost_blast(surface, t, fade)
        elif self.skill == "w":
            self._front_frostbite(surface, t, fade)
        elif self.skill == "e":
            self._front_sacrifice(surface, t, fade)
        elif self.skill == "r":
            self._front_chain_charge(surface, t, fade)

    # -- Q -------------------------------------------------------------
    def _front_frost_blast(self, surface, t, fade):
        sx, sy = self.x, self.y
        ex, ey = self.aim[0], self.aim[1]
        if t < 0.42:
            # COMET: bola es dengan ekor + halo shard, menuju aim
            tt = t / 0.42
            cur_x = sx + (ex - sx) * tt
            cur_y = sy - 18 + (ey - sy + 18) * tt
            for i in range(7):
                bt = max(0.0, tt - i * 0.07)
                px = sx + (ex - sx) * bt
                py = (sy - 18) + (ey - sy + 18) * bt
                s = max(2, 9 - i)
                _blit_faded(surface,
                            glow_surface(s + 3, P["ice_dark"], 0.5),
                            px, py, int(160 - i * 20), additive=True)
            _blit_faded(surface, glow_surface(14, P["ice_mid"], 0.85),
                        cur_x, cur_y, int(230 * fade), additive=True)
            pygame.draw.circle(surface, P["ice_light"],
                               (int(cur_x), int(cur_y)), 8)
            pygame.draw.circle(surface, P["ice_bright"],
                               (int(cur_x), int(cur_y)), 5)
            pygame.draw.circle(surface, P["ice_white"],
                               (int(cur_x), int(cur_y)), 2)
            for i in range(5):
                a = t * 9.0 + i * math.tau / 5
                shard_poly(surface,
                           cur_x + math.cos(a) * 13, cur_y + math.sin(a) * 13,
                           a + math.pi / 2, 7.0, 3.0, P["ice_light"], int(220 * fade))
        else:
            # IMPACT: nova petals + spike ring es + flash
            tt = (t - 0.42) / 0.58
            r = int((20 + self.radius * tt) * (1.0 - tt * 0.25))
            glow = glow_surface(max(6, int(r * 0.8)), P["ice_mid"], 0.8)
            _blit_faded(surface, glow, ex, ey, int(210 * (1.0 - tt)),
                        additive=True)
            # ring shockwave
            ring = ring_surface(int(r * 1.08), 3, P["fx_bright"], 200)
            _blit_faded(surface, ring, ex, ey, int(220 * (1.0 - tt)),
                        additive=True)
            # duri es keliling (polygon, bukan lingkaran)
            n = 10
            for i in range(n):
                a = i * math.tau / n + t * 1.2
                spike_h = 9 + 6 * math.sin(i * 2.7 + t * 9.0)
                base = r * 0.55
                px = ex + math.cos(a) * base
                py = ey + math.sin(a) * base * 0.6
                shard_poly(surface, px, py, a,
                           spike_h * (0.6 + 0.6 * (1.0 - tt)), 4.0,
                           P["ice_mid"], int(210 * (1.0 - tt * 0.7)))
                shard_poly(surface, px, py, a,
                           spike_h * 0.5 * (1.0 - tt), 2.5,
                           P["ice_edge"], int(230 * (1.0 - tt)))
            # central flash
            if tt < 0.4:
                pygame.draw.circle(surface,
                                   (*P["ice_white"], int(220 * (1 - tt * 2.5))),
                                   (int(ex), int(ey)), 6)

    # -- W -------------------------------------------------------------
    def _front_frostbite(self, surface, t, fade):
        sx, sy = self.x, self.y
        ex, ey = self.aim[0], self.aim[1]
        if t < 0.30:
            # bolt cepat dari caster ke target
            tt = t / 0.30
            cur_x = sx + (ex - sx) * tt
            cur_y = sy - 14 + (ey - sy + 14) * tt
            pygame.draw.line(surface, (*P["ice_light"], int(150 * fade)),
                             (int(sx), int(sy - 14)),
                             (int(cur_x), int(cur_y)), 2)
            _blit_faded(surface, glow_surface(12, P["fx_bright"], 0.8),
                        cur_x, cur_y, int(210 * fade), additive=True)
            pygame.draw.circle(surface, P["ice_hot"],
                               (int(cur_x), int(cur_y)), 4)
        else:
            # ICE PRISON: kurungan kristal poligonal (BUKAN lingkaran)
            self._draw_ice_prison(surface, ex, ey,
                                  (t - 0.30) / 0.70, fade)

    def _draw_ice_prison(self, surface, cx, cy, tt, fade):
        """Kurungan es: blok kristal chunky dengan facet + duri puncak."""
        size = 16 + 12 * min(1.0, tt * 1.4)
        c = cx, cy
        # siluet gelap
        pygame.draw.polygon(surface, (*P["ice_dark"], int(200 * fade)), [
            (c[0] - size, c[1] + size * 0.9),
            (c[0] - size * 0.8, c[1] - size * 0.55),
            (c[0] - size * 0.3, c[1] - size),
            (c[0] + size * 0.35, c[1] - size * 0.9),
            (c[0] + size, c[1] - size * 0.4),
            (c[0] + size * 0.9, c[1] + size * 0.9),
        ])
        # facet terang
        pygame.draw.polygon(surface, (*P["ice_mid"], int(190 * fade)), [
            (c[0] - size * 0.7, c[1] + size * 0.7),
            (c[0] - size * 0.55, c[1] - size * 0.4),
            (c[0] - size * 0.15, c[1] - size * 0.75),
            (c[0] + size * 0.5, c[1] - size * 0.3),
            (c[0] + size * 0.68, c[1] + size * 0.7),
        ])
        # kilau facet kiri-atas (key light)
        pygame.draw.polygon(surface, (*P["ice_light"], int(170 * fade)), [
            (c[0] - size * 0.5, c[1] + size * 0.5),
            (c[0] - size * 0.4, c[1] - size * 0.28),
            (c[0] - size * 0.1, c[1] - size * 0.5),
            (c[0] + size * 0.2, c[1] - size * 0.05),
            (c[0] + size * 0.05, c[1] + size * 0.55),
        ])
        # garis facet
        pygame.draw.line(surface, (*P["ice_edge"], int(220 * fade)),
                         (c[0] - size * 0.15, c[1] - size * 0.75),
                         (c[0] - size * 0.2, c[1] + size * 0.8), 1)
        pygame.draw.line(surface, (*P["ice_edge"], int(180 * fade)),
                         (c[0] - size * 0.55, c[1] - size * 0.4),
                         (c[0] + size * 0.5, c[1] - size * 0.3), 1)
        # duri puncak
        for i, (dx, h) in enumerate(((-size * 0.45, 10), (0.0, 14),
                                     (size * 0.45, 9))):
            shard_poly(surface, c[0] + dx, c[1] - size * 0.92,
                       -math.pi / 2 + dx * 0.02, h * (0.6 + 0.4 * tt), 4.0,
                       P["ice_mid"], int(220 * fade))
        # glints
        gphase = tt * 8.0
        for i in range(3):
            gx = c[0] - size * 0.3 + i * size * 0.3
            gy = c[1] - size * 0.2 + math.sin(gphase + i * 2.1) * size * 0.3
            pygame.draw.circle(surface,
                               (*P["ice_white"], int(200 * fade)),
                               (int(gx), int(gy)), 1)
        # shimmer saat mulai retak
        if tt > 0.8:
            shake = (tt - 0.8) * 12.0
            for i in range(4):
                a = i * math.tau / 4 + gphase
                px = c[0] + math.cos(a) * size * 1.1
                py = c[1] + math.sin(a) * size * 0.8
                spark = spark_surface(2, (*P["ice_hot"], int(200 * fade)))
                surface.blit(spark, (int(px + math.sin(shake + i) * 2),
                                     int(py)), special_flags=0)

    # -- E -------------------------------------------------------------
    def _front_sacrifice(self, surface, t, fade):
        cx, cy = self.x, self.y
        # soul wisps naik dari lingkaran ke badan caster
        for i in range(6):
            tt = (t * 1.5 + i * 0.16) % 1.0
            ox = math.sin(t * 5.0 + i * 1.9) * 14.0
            rx = cx + ox
            ry = cy + 24 - tt * 66
            alpha = int((1.0 - tt) * 210 * fade)
            pygame.draw.circle(surface, (*P["ice_light"], alpha),
                               (int(rx), int(ry)), 2 + int(tt * 3))
            pygame.draw.circle(surface, (*P["ice_white"], alpha),
                               (int(rx), int(ry)), 1)
        # halo pulsa heal
        r = int(40 * (0.85 + 0.15 * math.sin(t * 9.0)))
        ring = ring_surface(r, 2, P["fx_bright"], 150)
        _blit_faded(surface, ring, cx, cy - 6, int(170 * fade),
                    additive=True)
        # shard kecil mengorbit badan
        for i in range(5):
            a = t * 3.2 + i * math.tau / 5
            px = cx + math.cos(a) * (20 + 6 * math.sin(t * 4.0))
            py = cy - 10 + math.sin(a) * 12
            shard_poly(surface, px, py, a + math.pi / 2, 5.0, 2.5,
                       P["ice_light"], int(210 * fade))

    # -- R -------------------------------------------------------------
    def _front_chain_charge(self, surface, t, fade):
        cx, cy = self.x, self.y
        hand = (cx - 20.0, cy - 18.0)
        if t < 0.45:
            # CHARGE: shard spiral masuk ke orb tangan
            charge = t / 0.45
            for i in range(7):
                a = t * 10.0 - i * 0.8
                rr = (1.0 - charge) * 30 + 8 + i * 2.2
                px = hand[0] + math.cos(a) * rr
                py = hand[1] + math.sin(a) * rr * 0.7
                shard_poly(surface, px, py, a + math.pi / 2,
                           4.0 + 3.0 * charge, 2.5, P["ice_light"],
                           int(200 * fade))
            r = int(5 + charge * 11)
            _blit_faded(surface, glow_surface(16, P["ice_mid"], 0.8),
                        hand[0], hand[1], int(200 * fade), additive=True)
            pygame.draw.circle(surface, P["ice_light"],
                               (int(hand[0]), int(hand[1])), r)
            pygame.draw.circle(surface, P["ice_white"],
                               (int(hand[0]) - 1, int(hand[1]) - 1),
                               max(1, r - 4))
            # rune ring dashed berputar
            ring = ring_surface(26, 2, P["fx_bright"],
                                int(140 * fade), dashed=10)
            _blit_faded(surface, ring, hand[0], hand[1],
                        int(150 * fade * charge), additive=True)
        else:
            # setelah lepas: recoil flash kecil di tangan
            tt = (t - 0.45) / 0.55
            _blit_faded(surface, glow_surface(12, P["fx_bright"], 0.6),
                        hand[0], hand[1], int(150 * (1.0 - tt)),
                        additive=True)


# ============================================================================
# 11.  DIRECTOR — satu per unit Varkul
# ============================================================================

class VarkulFXDirector:
    """Mengikat particle + trail + proyektil + impact + skill FX untuk
    satu unit Varkul (mini boss MAUPUN hero hasil unlock — kode sama,
    hanya sumber transformasinya yang beda)."""

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
    # SWING (ark staff)
    # ------------------------------------------------------------------
    def on_swing_start(self, x, y, facing):
        """Awal ayunan: trail reset + debu es di kaki."""
        self.trail.reset()
        self.trail.width_boost = 1.0
        self.swing_active = True
        gy = 36
        self.particles.burst(
            x - facing * 7, y + gy, 6,
            speed=(25, 90), life=(0.18, 0.4), size=(2, 4),
            colors=(P["dust"], P["ice_mid"], P["fx_dark"]),
            spread=1.2, direction=0.0 if facing > 0 else math.pi,
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
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(tip[0], tip[1], ang, 0.55, False,
                                     kind="ice", seed=int(self.frames)))
        if shake_allowed():
            _feel_shake(3.2, 0.12)

    # ------------------------------------------------------------------
    # SKILL
    # ------------------------------------------------------------------
    def on_cast(self, x, y, skill, aim=None):
        """Skill dilepas: SkillFX + guncangan + (R) orb Chain Frost."""
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        if aim is None:
            tgt = getattr(self.hero, "target", None)
            if tgt is not None and getattr(tgt, "alive", False):
                aim = (float(tgt.x), float(tgt.y))
            else:
                facing = 1 if getattr(self.hero, "direction", 1) >= 0 else -1
                aim = (x + facing * 130, y - 8)
        self.skills.append(SkillFX(skill, x, y, self.particles,
                                   aim=aim, radius=WORLD_RADIUS.get(skill)))
        heavy = skill == "r"
        if shake_allowed():
            _feel_shake(6.0 if not heavy else 13.0,
                        0.16 if not heavy else 0.34)
        if heavy:
            _feel_hit_stop(0.055)
        self.particles.burst(x, y + 14, 10,
                             speed=(60, 170), life=(0.2, 0.5), size=(2, 4),
                             colors=(P["fx_mid"], P["fx_dark"], P["dust"]),
                             spread=math.tau, gravity=140.0, drag=2.0,
                             shape="dust", layer="back")

    def release_chain_frost(self, x, y, aim=None):
        """Lepaskan orb Chain Frost dari tangan ke area musuh."""
        tgt = getattr(self.hero, "target", None)
        if aim is None:
            if tgt is not None and getattr(tgt, "alive", False):
                aim = (float(tgt.x), float(tgt.y))
            else:
                facing = 1 if getattr(self.hero, "direction", 1) >= 0 else -1
                aim = (x + facing * 150.0, y - 10.0)
        orb = self.projectiles.spawn_chain_orb(
            x - 18.0, y - 20.0, aim,
            speed=CHAIN_SPEED, bounces=CHAIN_BOUNCES,
            on_bounce=lambda o: self.on_chain_bounce(o),
            on_expire=lambda o: self.on_impact(o.x, o.y, 0.0, 1.2, False,
                                               kind="ice"),
            seed=int(self.frames))
        if shake_allowed():
            _feel_shake(7.0, 0.2)
        return orb

    def on_chain_bounce(self, orb):
        """Nova kecil + arc lightning + serpihan di tiap pantulan."""
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(orb.x, orb.y, -math.pi / 2, 0.9,
                                     False, kind="ice",
                                     seed=int(self.frames) + 3))
        self.particles.burst(orb.x, orb.y, 10, speed=(70, 200),
                             life=(0.15, 0.4), size=(2, 4),
                             colors=(P["ice_hot"], P["ice_edge"],
                                     P["ice_light"]),
                             spread=math.tau, gravity=60.0,
                             shape="shard", additive=True,
                             rotation_speed=(-14, 14))
        self.particles.burst(orb.x, orb.y, 5, speed=(10, 60),
                             life=(0.3, 0.8), size=(2, 5),
                             colors=(P["ice_mid"], P["ice_dark"]),
                             spread=math.tau, shape="mist",
                             additive=True, layer="back")
        if shake_allowed():
            _feel_shake(3.5, 0.14)

    # ------------------------------------------------------------------
    # BASIC ATTACK PROYECTILE
    # ------------------------------------------------------------------
    def spawn_frost_bolt(self, x, y, aim):
        """Lepaskan frost bolt dari crystal staff ke target."""
        _g, tip = staff_points(self.hero, x, y, False)
        tgt = getattr(self.hero, "target", None)
        if tgt is None or not getattr(tgt, "alive", False):
            tgt = None
        return self.projectiles.spawn(
            tip[0], tip[1], aim[0], aim[1],
            speed=BOLT_SPEED, damage=0, target=tgt, radius=7.0,
            kind="ice",
            on_impact=lambda p: self.on_impact(p.hit_pos.x, p.hit_pos.y,
                                               p.rotation, 1.15, False,
                                               kind="ice"))

    # ------------------------------------------------------------------
    # IMPACT / HURT
    # ------------------------------------------------------------------
    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="ice"):
        """Benturan mengenai target: flash, spark, debris, shake, hit-stop."""
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind=kind))
        pw = min(2.0, max(0.35, float(power)))

        spark, edge, hot = P["ice_hot"], P["ice_light"], P["ice_edge"]

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
        self.particles.burst(
            x, y + 4, 4, speed=(20, 80), life=(0.3, 0.8), size=(3, 6),
            colors=(P["ice_dark"], P["smoke"]),
            gravity=-30.0, drag=1.5, shape="mist", additive=True,
            layer="back")
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
        """Varkul terkena serangan: flash + percikan es + kabut jubah."""
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

    def _death_shatter(self, x, y):
        """Kematian: badan pecah jadi serpihan kristal + kabut."""
        self.particles.burst(x, y - 10, 26, speed=(60, 260),
                             life=(0.4, 1.1), size=(2, 6),
                             colors=(P["ice_light"], P["ice_edge"],
                                     P["bone_light"]),
                             spread=math.tau, gravity=420.0, drag=0.8,
                             shape="shard", rotation_speed=(-20, 20),
                             additive=True)
        self.particles.burst(x, y - 6, 10, speed=(15, 80),
                             life=(0.6, 1.4), size=(4, 8),
                             colors=(P["ice_mid"], P["smoke"]),
                             spread=math.tau, gravity=-45.0, drag=1.0,
                             shape="mist", additive=True, layer="back")
        if shake_allowed():
            _feel_shake(10.0, 0.3)
        _feel_hit_stop(0.05)

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def _watch_engine_events(self, x, y):
        """Sinkronkan state debug + deteksi hurt/death dari engine."""
        skill = getattr(self.hero, "active_skill", None)
        if skill:
            self.state = "SPECIAL" if skill == "r" else "SKILL"
        else:
            self.state = getattr(self.hero, "_vk_state", "IDLE")
        self.anim_phase = getattr(self.hero, "_vk_attack_phase", "NONE")

        # hurt lewat penurunan HP (engine tidak selalu memanggil notify)
        hp = getattr(self.hero, "hp", None)
        if hp is not None:
            if self._last_hp is not None and hp < self._last_hp:
                self.on_hurt(0.8)
            self._last_hp = hp

        # death sekali
        if not getattr(self.hero, "alive", True) and not self._death_done:
            self._death_done = True
            self._death_shatter(x, y)

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
                if ap and (0.50 <= ap <= 0.54) and not self._impact_frame_seen:
                    self._impact_frame_seen = True
                    self.on_swing_impact_frame(x, y, facing)
                elif self._impact_frame_seen and ap > 0.66:
                    self._impact_frame_seen = False
        else:
            if self._swing_seen:
                self._swing_seen = False
                self.on_swing_end()
            self.trail.reset()

        # cast charge: shard spiral halus di orb tangan
        if action == "cast":
            op = orb_points(self.hero, x, y)
            if self.frames % 4 == 0:
                a = self.time * 7.0
                self.particles.burst(
                    op[0] + math.cos(a) * 10, op[1] + math.sin(a) * 7, 1,
                    speed=(8, 30), life=(0.2, 0.4), size=(1, 2),
                    colors=(P["ice_light"], P["ice_edge"]),
                    direction=-a, spread=0.8, drag=2.2,
                    shape="spark", additive=True)

        self.impacts = [i for i in self.impacts if i.age < i.life]
        self.skills = [s for s in self.skills if not s.done]

    # ------------------------------------------------------------------
    # DRAW
    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        self.particles.draw(surface, "back")
        for sk in self.skills:
            sk.draw_ground(surface)
        # ground glow ringan saat cast
        if getattr(self.hero, "active_skill", None):
            skill = getattr(self.hero, "active_skill", None)
            pulse = math.sin(self.time * 6.0) * 0.25 + 0.75
            r = int(WORLD_RADIUS.get(skill, 40) * pulse * 0.7)
            ring = ellipse_ring_surface(r, int(r * 0.4), 2,
                                        (*P["fx_bright"], 120))
            _blit_faded(surface, ring,
                        float(getattr(self.hero, "x", 0)),
                        float(getattr(self.hero, "y", 0)) + 36,
                        int(120 * pulse), additive=True)

    def draw_front(self, surface, x, y):
        # urutan master prompt: TRAIL -> PROJECTILE -> PARTICLES ->
        # SKILL FX -> IMPACT FX
        self.trail.draw(surface, P["ice_edge"], 150, additive=True)
        self.projectiles.draw(surface)
        self.particles.draw(surface, "front")
        for sk in self.skills:
            sk.draw_front(surface)
        for imp in self.impacts:
            imp.draw(surface)

    def clear(self):
        self.particles.clear()
        self.projectiles.clear()
        self.trail.reset()
        self.impacts.clear()
        self.skills.clear()
        self._death_done = False
        self._last_hp = None


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
    # jendela hit aktif
    if getattr(h, "_vk_hit_active", False):
        reach = int(rng)
        top = int(y - 44)
        left = int(x) if f > 0 else int(x) - reach
        hb = pygame.Rect(left, top, max(8, reach), max(10, 80))
        pygame.draw.rect(surface, (255, 70, 70, 190), hb, 2)
        pygame.draw.rect(surface, (255, 70, 70, 60), hb)
    # projectile collision
    for pr in director.projectiles.items:
        pygame.draw.circle(surface, (255, 120, 255, 170),
                           (int(pr.x), int(pr.y)), int(pr.hit_radius), 1)
    fps = director._fps = getattr(director, "_fps", 60.0)
    dtv = float(getattr(h, "_vk_dt", 1.0 / 60.0) or 1.0 / 60.0)
    inst = 1.0 / dtv if dtv > 0 else 60.0
    fps = fps + (inst - fps) * 0.1
    director._fps = fps
    state = director.state
    phase = director.anim_phase
    lines = [
        f"VARKUL {state} {phase}",
        f"frame {director.frames} t={director.time:.2f}",
        f"particles={director.particles.count()} "
        f"proj={director.projectiles.count()}",
        f"skills={len(director.skills)} impacts={len(director.impacts)} "
        f"fps={fps:.0f}",
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


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Varkul."""
    _sync_palette()
    d = getattr(hero, "_vk_fx", None)
    if d is None:
        d = VarkulFXDirector(hero)
        try:
            hero._vk_fx = d
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
            director.hero._vk_fx = None
            director.hero._vk_live_fx = False
    except Exception:                          # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit (rendering pipeline)."""
    if not VARKUL_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                          # pragma: no cover
        return False
    try:
        hero._vk_live_fx = True
    except Exception:                          # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not getattr(hero, "_vk_live_fx", False):
        return False
    d = getattr(hero, "_vk_fx", None)
    return d is not None and d in _DIRECTORS


def tick(dt=None):
    """Majukan waktu FX satu frame nyata; aman dipanggil berkali-kali."""
    if dt is not None:
        step = max(0.0, min(1.0 / 20.0, float(dt)))
        _advance(step)
        return step
    if _feel is not None:
        try:
            step = _feel.fx_dt()
        except Exception:                      # pragma: no cover
            step = 0.0
    else:                                      # pragma: no cover
        step = FIXED_DT
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
    """Bersihkan seluruh state FX Varkul (ganti level / keluar match)."""
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()
    if _feel is not None:
        try:
            _feel.reset()
        except Exception:                      # pragma: no cover
            pass


def total_particles():
    """Jumlah partikel Varkul hidup (dipakai HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def stats():
    try:
        return _feel.stats()
    except Exception:                          # pragma: no cover
        return {"hitstop_frames": 0, "hitstop_total": 0, "shake": 0.0}


def projectiles_for(hero):
    """Daftar proyektil milik unit (untuk debug renderer)."""
    d = getattr(hero, "_vk_fx", None)
    if d is None:
        return []
    return d.projectiles.items


# --- hook yang dipanggil heroes/__init__.py --------------------------------

def draw_ground_layer(surface, hero, x, y):
    if not VARKUL_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_vk_fx", None)
    if d is not None:
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    if not VARKUL_FX_ENABLED:
        return
    d = director_for(hero)
    d.draw_front(surface, x, y)
    if DEBUG_CHARACTER:
        draw_debug_overlay(surface, d)


# --- hook yang dipanggil bosses/base_boss.py -------------------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Hook serangan jarak dekat (dipakai bila varkul dipakai melee)."""
    if not VARKUL_FX_ENABLED or hero is None or target is None:
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
    """Frost bolt / skill mengenai target: paket impact lengkap."""
    if not VARKUL_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    director_for(hero).on_impact(float(x), float(y), angle, power,
                                 bool(crit), kind=kind)


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """FX area skill pada titik (x, y): SkillFX + paket impact.

    AI memanggil ``notify_skill_cast`` lalu ``notify_skill_impact`` pada
    tick yang sama; SkillFX yang barusan dibuat cast di-update di tempat
    (aim/radius final) supaya efek tidak digambar dobel.
    """
    if not VARKUL_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    fx = None
    for s in d.skills:
        if s.skill == skill and s.age <= 0.05:
            fx = s
            break
    if fx is None:
        if len(d.skills) >= MAX_SKILLS:
            d.skills.pop(0)
        fx = SkillFX(skill, float(getattr(hero, "x", 0.0)),
                     float(getattr(hero, "y", 0.0)), d.particles,
                     aim=(float(x), float(y)),
                     radius=radius or WORLD_RADIUS.get(skill))
        d.skills.append(fx)
    else:
        fx.aim = (float(x), float(y))
        if radius:
            fx.radius = float(radius)
    d.on_impact(float(x), float(y), 0.0,
                1.4 if skill != "r" else 2.1,
                skill == "r", kind="ice")


def notify_skill_cast(hero, skill):
    """Skill mulai di-cast: SkillFX + guncangan (dan R: orb langsung)."""
    if not VARKUL_FX_ENABLED or hero is None or skill not in SKILL_DUR:
        return
    d = director_for(hero)
    d.on_cast(float(getattr(hero, "x", 0.0)),
              float(getattr(hero, "y", 0.0)), skill)
    if skill == "r":
        # orb dilepas saat mulai supaya AI + FX sinkron
        d.release_chain_frost(float(getattr(hero, "x", 0.0)),
                              float(getattr(hero, "y", 0.0)))


def notify_projectile_cast(hero, x, y):
    """Spawn frost bolt dari crystal staff ke target (basic attack).

    Renderer memanggil ini saat frame cast aktif dan lapisan hidup sudah
    mengambil alih proyektil; menggantikan ``_spawn_projectile`` canvas.
    """
    if not VARKUL_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    tgt = getattr(hero, "target", None)
    if tgt is not None and getattr(tgt, "alive", False):
        aim = (float(tgt.x), float(tgt.y))
    else:
        facing = 1 if getattr(hero, "direction", 1) >= 0 else -1
        aim = (x + facing * 150.0, y - 10.0)
    d.spawn_frost_bolt(x, y, aim)


def notify_hurt(hero, amount=1.0):
    if not VARKUL_FX_ENABLED or hero is None:
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
