# ============================================================================
# heroes/ignis_drachorn_fx.py
# ----------------------------------------------------------------------------
# IGNIS DRACHORN — THE MOLTEN SOVEREIGN  (screen-space live combat layer)
#
# Badan Ignis Drachorn digambar oleh ``_NS_ignis_drachorn`` (bosses/level4.py)
# ke canvas yang DI-CACHE pada jalur hero (heroes/__init__.py: render_hero).
# Semua yang harus bergerak 60 fps sejati — sabit ayunan greatsword, partikel
# bara, proyektil bola api, impact, guncangan layar, hit-stop — TIDAK boleh
# hidup di dalam canvas itu: hasilnya ikut beku selama pose yang sama dipakai
# ulang, dan ikut menyusut saat canvas di-smoothscale.
#
# Modul ini adalah LAPISAN HIDUP: digambar langsung ke layar pada skala 1:1
# setiap frame dengan delta-time nyata (via heroes/combat_feel).
#
# Pembagian kerja (sengaja, supaya tidak ada efek yang digambar dua kali):
#
#   RENDERER (canvas, ter-cache)        MODUL INI (layar, hidup)
#   ---------------------------------   ------------------------------------
#   rig dragon knight + palet           trail sabit api dari histori ujung
#   bayangan, aura panas, ground rune   partikel (bara, asap, debu, serpihan)
#   pose idle/walk/attack/cast          proyektil Fire Orb (lifecycle penuh)
#   ARC ayunan pedang (theta)           komet Cataclysm R + meteor
#   hurt-flash (siluet badan)           IMPACT FX + flash + shockwave
#   fallback skill canvas q/w/e/r       SkillFX lifecycle cast->release->fade
#                                       overlay DEBUG_CHARACTER
#
# 100% PROSEDURAL. Tidak ada gambar/sprite-sheet/tekstur eksternal apa pun.
# Semua bentuk dibangun dari pygame.Surface + pygame.draw + pygame.transform
# + pygame.Vector2 + pygame.Rect.
#
# Isi modul
#   IGNIS_PALETTE          palette khusus karakter (kontrak 9 kunci + ramp)
#   Particle               partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem         pool + burst terarah + cap keras, reusable
#   SwingTrail             pita sabit api prosedural dari histori ujung bilah
#   ImpactFX               flash + shockwave + debris + fragmen slash
#   FireOrbProjectile      proyektil modular (spawn->travel->hit->destroy)
#   MeteorProjectile       meteor R yang jatuh dari langit + ledakan
#   ProjectileSystem       manajer proyektil
#   SkillFX                lifecycle FX skill (cast->charge->release->fade)
#   IgnisFXDirector        satu instance per unit, mengikat semua di atas
#   draw_debug_overlay     hitbox/hurtbox/range/state/frame/FPS/particle/timer
#   API modul              tick / reset_all / notify_* / draw_*_layer
# ============================================================================

import math
import random
import weakref

import pygame

try:                                 # bus game-feel bersama (combat_feel)
    from heroes import combat_feel as _feel
except Exception:                    # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual untuk karakter IGNIS DRACHORN: hitbox, hurtbox, jangkauan,
#: state animasi, frame, FPS, jumlah partikel, state skill, timer serangan.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
IGNIS_FX_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 210

#: Batas keras proyektil visual per director.
MAX_PROJECTILES = 20

#: Panjang histori trail senjata (jumlah sample posisi ujung bilah).
TRAIL_SAMPLES = 18

#: Batas dampak aktif & skill sekaligus di layar per director.
MAX_IMPACTS = 9
MAX_SKILLS = 5

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Kecepatan bola api serangan dasar (px/detik, ruang layar).
ORB_SPEED = 690.0

#: Kecepatan meteor Cataclysm (px/detik).
METEOR_SPEED = 900.0

#: Jumlah meteor yang dijatuhkan skill R.
METEOR_COUNT = 5

#: Umur FX skill dalam DETIK. Sinkron dengan ``_NS_ignis_drachorn`` +
#: ``active_skill_timer`` AI (45/40/60/90 langkah sim = 0.75/0.67/1.00/1.50 s)
#: plus sisa after-glow supaya efek tidak "terpotong".
SKILL_TOTAL = {"q": 1.35, "w": 1.15, "e": 1.55, "r": 2.60}

#: Durasi pose per skill (frame simulasi) — memetakan umur FX ke fase yang
#: sama dengan yang dibaca renderer canvas.
SKILL_DUR = {"q": 45, "w": 40, "e": 60, "r": 90}

#: Radius EFEK di ruang dunia (sinkron dengan base_boss._smart_ai_*).
#: q = panjang cone breath, w = sapuan ekor, e = aura darah, r = area erupsi.
WORLD_RADIUS = {"q": 250.0, "w": 130.0, "e": 105.0, "r": 220.0}

#: Setengah lebar cone Dragon Breath (radian) di ujung jangkauan.
BREATH_CONE = 0.42

#: Fase serangan (fraksi 0..1 dari durasi serangan). Batasnya sengaja jatuh
#: PERSIS di patahan tabel ``SWORD_ARC`` renderer, jadi nama fase dan sudut
#: bilah tidak pernah berbeda satu frame.
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.14),
    ("WINDUP",       0.14, 0.30),
    ("SWING",        0.30, 0.48),
    ("IMPACT",       0.48, 0.60),
    ("FOLLOW",       0.60, 0.80),
    ("RECOVERY",     0.80, 1.00),
)

#: Jendela hit aktif (dipakai debug & game feel).
ATTACK_ACTIVE_WINDOW = (0.36, 0.60)
ATTACK_IMPACT_FRAME = 0.48

#: Prioritas state animasi. Angka besar menang; DEATH mengunci.
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
# 1.  PALETTE  —  dragon knight: baja gelap + merah darah + emas + api
# ============================================================================

IGNIS_PALETTE = {
    # ── kontrak palette karakter (9 kunci wajib) ────────────────────
    "outline":    (8,     4,   6),
    "shadow":     (18,   12,  14),
    "dark":       (42,   28,  30),
    "body":       (75,   52,  55),
    "mid":        (120,  90,  90),
    "light":      (170, 140, 138),
    "highlight":  (215, 195, 190),
    "weapon":     (200, 130,  55),
    "fx":         (255, 250, 220),

    # ── ramp api (dipakai trail, proyektil, skill, impact) ─────────
    "fx_darkest": (60,   12,   4),
    "fx_dark":    (135,  35,   8),
    "fx_mid":     (215,  80,  15),
    "fx_light":   (250, 145,  30),
    "fx_bright":  (255, 200,  65),
    "fx_hot":     (255, 235, 140),
    "fx_white":   (255, 250, 220),

    # ── alias api (nama pendek supaya kode FX terbaca) ─────────────
    "fire_darkest": (60,  12,   4),
    "fire_dark":    (135, 35,   8),
    "fire_mid":     (215, 80,  15),
    "fire_light":   (250, 145, 30),
    "fire_bright":  (255, 200, 65),
    "fire_hot":     (255, 235, 140),
    "fire_white":   (255, 250, 220),
    "fire_edge":    (255, 200, 65),

    # ── material fisik ─────────────────────────────────────────────
    "armor":      (42,   28,  30),
    "armor_mid":  (75,   52,  55),
    "armor_light": (170, 140, 138),
    "red":        (140,  30,  35),
    "red_deep":   (45,    8,  10),
    "red_light":  (220,  90,  80),
    "gold":       (170, 125,  35),
    "gold_hot":   (255, 235, 150),
    "blade":      (200, 130,  55),
    "blade_hot":  (255, 235, 170),
    "scale":      (105,  30,  32),
    "scale_light": (200, 100, 80),

    # ── mata naga ──────────────────────────────────────────────────
    "eye":        (220,  90,  15),
    "eye_hot":    (255, 240, 180),

    # ── sisa destinasi (debu / asap / abu / bara) ─────────────────
    "smoke":      (52,   38,  36),
    "ash":        (96,   80,  74),
    "dust":       (126, 104,  88),
    "ember":      (255, 140,  40),
    "magma":      (255,  90,  20),
}

P = IGNIS_PALETTE

#: Kunci yang boleh disalin dari palet renderer supaya warna karakter dan
#: warna efek tidak pernah berbeda "satu derajat".
_PALETTE_SYNC = {
    "outline": "shadow_deep",
    "shadow": "armor_darkest",
    "dark": "armor_dark",
    "body": "armor_mid",
    "mid": "armor_light",
    "light": "armor_high",
    "highlight": "armor_shine",
    "weapon": "blade_mid",
    "fx": "fire_white",
    "fx_darkest": "fire_darkest",
    "fx_dark": "fire_dark",
    "fx_mid": "fire_mid",
    "fx_light": "fire_light",
    "fx_bright": "fire_bright",
    "fx_hot": "fire_hot",
    "fx_white": "fire_white",
    "fire_darkest": "fire_darkest",
    "fire_dark": "fire_dark",
    "fire_mid": "fire_mid",
    "fire_light": "fire_light",
    "fire_bright": "fire_bright",
    "fire_hot": "fire_hot",
    "fire_white": "fire_white",
    "fire_edge": "fire_bright",
    "armor": "armor_dark",
    "armor_mid": "armor_mid",
    "armor_light": "armor_light",
    "red": "red_mid",
    "red_deep": "red_darkest",
    "red_light": "red_high",
    "gold": "gold_mid",
    "gold_hot": "gold_shine",
    "blade": "blade_mid",
    "blade_hot": "blade_hot",
    "scale": "dragon_mid",
    "scale_light": "dragon_high",
    "eye": "eye_mid",
    "eye_hot": "eye_hot",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Salin warna tema dari ``_NS_ignis_drachorn.PALETTE`` sekali saja.

    Renderer adalah satu-satunya sumber kebenaran untuk material karakter;
    lapisan efek tidak boleh punya salinan yang lalu melenceng.
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
    """``_NS_ignis_drachorn`` atau None. Diimpor malas: modul boss besar."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level4 import _NS_ignis_drachorn as G
            _RENDERER = G
        except Exception:                      # pragma: no cover
            _RENDERER = False
    return _RENDERER or None


#: Geometri cadangan — identik dengan ``_NS_ignis_drachorn.SWORD_ARC`` supaya
#: modul tetap hidup kalau renderer tidak bisa diimpor.
#: (t0, t1, theta0, theta1, ease); theta radian dari vertikal, positif =
#: mengayun ke arah depan (facing).
_ARC_FALLBACK = (
    (0.00, 0.14,  0.38,  0.05, "out"),     # ANTICIPATION: turunkan, tarik nafas
    (0.14, 0.30,  0.05, -1.42, "io"),      # WINDUP: angkat jauh ke belakang
    (0.30, 0.48, -1.42,  1.58, "oc"),      # SWING: tebasan cepat ke depan
    (0.48, 0.60,  1.58,  1.58, "hold"),    # IMPACT: tahan (hit-stop visual)
    (0.60, 0.80,  1.58,  0.72, "io"),      # FOLLOW THROUGH
    (0.80, 1.00,  0.72,  0.38, "io"),      # RECOVERY
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
    return t * t * (3.0 - 2.0 * t)          # in-out (smoothstep)


def _hand_lift(progress):
    """Tinggi tangan pedang relatif (0 = idle, positif = terangkat).

    Harus identik dengan ``_NS_ignis_drachorn._sword_lift`` — keduanya
    dibaca renderer canvas dan modul hidup supaya trail plus proyektil
    lahir tepat di ujung bilah.
    """
    p = max(0.0, min(1.0, float(progress)))
    if p < 0.30:
        return _ease("out", p / 0.30) * 1.0
    if p < 0.48:
        return 1.0 - _ease("oc", (p - 0.30) / 0.18) * 0.88
    if p < 0.80:
        return 0.12 + _ease("io", (p - 0.48) / 0.32) * 0.22
    return 0.34 * (1.0 - _ease("io", (p - 0.80) / 0.20))


def _fallback_arc(progress):
    """(theta, lift) pedang untuk progress 0..1 tanpa renderer."""
    p = max(0.0, min(1.0, float(progress)))
    for t0, t1, a0, a1, kind in _ARC_FALLBACK:
        if t0 <= p < t1 or (p >= 1.0 and t1 >= 1.0):
            e = _ease(kind, (p - t0) / max(0.0001, t1 - t0))
            return a0 + (a1 - a0) * e, _hand_lift(p)
    return 0.38, 0.0


def sword_arc(progress):
    """(theta, lift) pose ARK pedang — SATU sumber kebenaran.

    Membaca ``_NS_ignis_drachorn._sword_arc`` (dipakai renderer canvas
    juga); kalau renderer tidak ada, pakai tabel fallback identik.
    """
    R = _renderer()
    fn = getattr(R, "_sword_arc", None) if R is not None else None
    if fn is not None:
        try:
            return fn(progress)
        except Exception:                    # pragma: no cover
            pass
    return _fallback_arc(progress)


def attack_phase(progress):
    """Nama fase serangan untuk progress 0..1."""
    p = max(0.0, min(1.0, float(progress)))
    for name, a, b in ATTACK_PHASES:
        if a <= p < b:
            return name
    return "RECOVERY"


def _fallback_pose(boss):
    """(action, phase, ap) tanpa renderer: baca atribut yang sudah ada."""
    skill = getattr(boss, "active_skill", None)
    action = getattr(boss, "_ign_pose_action", None)
    if action is None and skill:
        action = "cast"
    if action is None:
        action = ("attack" if getattr(boss, "_ign_attack_active", False)
                  else "idle")
    phase = float(getattr(boss, "pulse", 0.0) or 0.0)
    ap = 0.0
    if action == "attack":
        ap = float(getattr(boss, "_ign_attack_progress", 0.0) or 0.0)
    return action, phase, ap


def pose_of(boss):
    """Pose badan yang dipakai renderer (action, phase, attack_progress)."""
    R = _renderer()
    if R is None:
        return _fallback_pose(boss)
    try:
        action = getattr(boss, "_ign_pose_action", None)
        if action is None:
            return _fallback_pose(boss)
        phase = float(getattr(boss, "_ign_phase",
                              getattr(boss, "pulse", 0.0)))
        ap = float(getattr(boss, "_ign_attack_progress", 0.0) or 0.0)
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
    """Skala badan relatif terhadap anchor (dipakai FX tip)."""
    return render_scale(boss)


def screen_point(boss, x, y, local):
    """Titik layar dari koordinat lokal (offset dari anchor kaki)."""
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)
    return (x + local[0] * k * facing, y + local[1] * k)


def sword_points(boss, x, y):
    """(grip, tip) greatsword dalam ruang layar untuk trail & proyektil.

    Renderer memegang pedang di tangan sisi DEPAN (``facing``). Saat
    menyerang seluruh bilah berputar mengikuti ark ``sword_arc`` — ujung
    bilah menelusuri LENGKUNGAN, dan di titik itulah trail plus proyektil
    lahir, sehingga semuanya konsisten dengan canvas.
    """
    action, phase, ap = pose_of(boss)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)

    if action == "attack":
        theta, lift = sword_arc(ap)
        hand_x = x + facing * (17.0 + 7.0 * lift) * k
        hand_y = y + (2.0 - 22.0 * lift) * k
        L = 40.0 * k
        tip_x = hand_x + facing * math.sin(theta) * L
        tip_y = hand_y - math.cos(theta) * L
        return (hand_x, hand_y), (tip_x, tip_y)

    if action == "cast":
        pulse = math.sin(phase * 2.4) * 2.0 * k
        hand_x = x + facing * 20.0 * k
        hand_y = y - (26.0 + pulse * 0.4) * k
        tip_x = hand_x + facing * 6.0 * k
        tip_y = hand_y - 38.0 * k
        return (hand_x, hand_y), (tip_x, tip_y)

    # idle / walk: pedang menggantung ke depan-bawah, sway halus
    sway = math.sin(phase * 0.7) * 1.4 * k
    hand_x = x + facing * 20.0 * k
    hand_y = y + (12.0 + sway * 0.5) * k
    tip_x = hand_x + facing * 30.0 * k
    tip_y = hand_y - (12.0 + sway) * k
    return (hand_x, hand_y), (tip_x, tip_y)


def maw_point(boss, x, y):
    """Mulut helm naga (sumber Dragon Breath & muzzle flash)."""
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)
    return (x + facing * 12.0 * k, y - 30.0 * k)


def target_point(boss, x, y):
    """Titik target serangan dasar (layar) untuk proyektil."""
    tgt = getattr(boss, "target", None)
    if tgt is not None and getattr(tgt, "alive", False):
        return (float(getattr(tgt, "x", x + 120.0)),
                float(getattr(tgt, "y", y)) - 6.0)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    return (x + facing * 160.0, y - 10.0)


def particle_budget():
    """Jumlah partikel total yang diizinkan per director."""
    return MAX_PARTICLES


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
    return tuple(int(max(0, min(255, c))) for c in color)


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t)
                 for i in range(min(len(a), len(b))))


def _hash01(seed):
    """Hash deterministik kecil -> [0,1)."""
    v = (int(seed) * 747796405 + 2891336453) & 0xFFFFFFFF
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
    key = ("glow", radius, tuple(color[:3]), round(power, 2))
    if key in _CACHE:
        return _CACHE[key]
    size = radius * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    steps = max(3, radius // 2)
    for i in range(steps, -1, -1):
        r = int(radius * i / steps)
        a = max(0, min(255, int((1.0 - i / steps) * 255 * power)))
        if r > 0 and a > 0:
            pygame.draw.circle(surf, (*color[:3], a),
                               (radius + 2, radius + 2), r)
    return _cache_put(key, surf)


def ember_surface(size, color):
    """Cached bara chunky: serpihan bersudut + inti panas.

    Sengaja BUKAN kotak penuh: kotak besar terbaca sebagai blok warna
    nyasar, bukan bara. Bentuknya segi-enam pipih dengan sisi keras
    (pixel-art) plus inti 1-2 px yang lebih panas dari warna dasar,
    jadi tetap "chunky" tapi terbaca sebagai percikan api.
    """
    size = max(1, min(6, int(size)))
    key = ("ember", size, tuple(color[:3]))
    if key in _CACHE:
        return _CACHE[key]
    s = size * 2 + 3
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    c = s // 2
    r = size
    pts = [(c + r, c), (c + r // 2, c - r), (c - r // 2, c - r),
           (c - r, c), (c - r // 2, c + r), (c + r // 2, c + r)]
    pygame.draw.polygon(surf, (*color[:3], 230), pts)
    if size >= 2:
        inner = [(c + r - 1, c), (c, c - r + 1),
                 (c - r + 1, c), (c, c + r - 1)]
        pygame.draw.polygon(surf, (*P["fire_hot"], 255), inner)
    pygame.draw.rect(surf, (*P["fire_white"], 255), (c, c - 1, 1, 1))
    return _cache_put(key, surf)


def spark_surface(size, color):
    """Cached percikan 4 arah (chunky pixel, hard edge)."""
    size = max(3, int(size))
    key = ("spark", size, tuple(color[:3]))
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    c = size
    pygame.draw.line(surf, color, (c, 1), (c, size * 2 - 1),
                     max(1, size // 3))
    pygame.draw.line(surf, color, (1, c), (size * 2 - 1, c),
                     max(1, size // 3))
    return _cache_put(key, surf)


def ring_surface(radius, thickness, color, alpha=255, dashed=0):
    """Cached ring (atau ring putus-putus jika dashed > 0)."""
    radius = max(4, int(radius))
    thickness = max(1, int(thickness))
    key = ("ring", radius, thickness, tuple(color[:3]), int(alpha), dashed)
    if key in _CACHE:
        return _CACHE[key]
    size = radius * 2 + thickness * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (size // 2, size // 2)
    color_a = (*color[:3], int(alpha))
    if dashed <= 0:
        pygame.draw.circle(surf, color_a, center, radius, thickness)
    else:
        step = math.tau / dashed
        for i in range(dashed):
            a0 = i * step
            a1 = a0 + step * 0.55
            for t in (0.0, 0.25, 0.5, 0.75, 1.0):
                a = a0 + (a1 - a0) * t
                px = int(center[0] + math.cos(a) * radius)
                py = int(center[1] + math.sin(a) * radius)
                pygame.draw.circle(surf, color_a, (px, py), thickness)
    return _cache_put(key, surf)


def ellipse_ring_surface(rx, ry, thickness, color, angle_deg=0):
    """Cached chunky ellipse ring (ground telegraph)."""
    rx, ry = max(4, int(rx)), max(3, int(ry))
    thickness = max(1, int(thickness))
    key = ("ering", rx, ry, thickness, tuple(color), int(angle_deg))
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
    """Cached flat ground ellipse glow (bara di tanah)."""
    radius = max(4, int(radius))
    key = ("gglow", radius, tuple(color[:3]), round(power, 2))
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((radius * 2 + 8, radius + 12), pygame.SRCALPHA)
    steps = max(3, radius // 3)
    for i in range(steps, -1, -1):
        r = max(1, int(radius * i / steps))
        a = int((1.0 - i / steps) * 52 * power)
        if a <= 0:
            continue
        pygame.draw.ellipse(surf, (*color[:3], a),
                            (radius + 4 - r, 6 - r // 5,
                             r * 2, max(2, r // 2)))
    return _cache_put(key, surf)


def rune_surface(size, color, teeth=8):
    """Cached rune naga: cincin bergerigi (bukan lingkaran polos)."""
    size = max(6, int(size))
    key = ("rune", size, tuple(color[:3]), teeth)
    if key in _CACHE:
        return _CACHE[key]
    s = size * 2 + 6
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    c = s // 2
    pts_out = []
    pts_in = []
    for i in range(teeth * 2):
        a = i * math.pi / teeth
        r = size if i % 2 == 0 else size * 0.72
        pts_out.append((c + math.cos(a) * r, c + math.sin(a) * r))
        pts_in.append((c + math.cos(a) * r * 0.62,
                       c + math.sin(a) * r * 0.62))
    pygame.draw.polygon(surf, (*color[:3], 130), pts_out, 2)
    pygame.draw.polygon(surf, (*color[:3], 90), pts_in, 1)
    return _cache_put(key, surf)


def _blend_polygon(surface, color, points, alpha=255, additive=False,
                   width=0):
    """Gambar poligon SEMI-TRANSPARAN dengan blending yang benar.

    PENTING: pygame.draw.* pada Surface SRCALPHA MENIMPA pixel tujuan
    (termasuk kanal alpha) alih-alih mem-blend. Menggambar warna terang
    ber-alpha langsung ke layer FX karena itu menghasilkan blok warna
    solid, bukan nyala api transparan. Jadi kita gambar ke scratch
    opaque-color lalu blit dengan alpha/additive.
    """
    alpha = int(max(0, min(255, alpha)))
    if alpha < 2 or len(points) < 3:
        return
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    pad = int(width) + 2
    min_x, min_y = int(min(xs)) - pad, int(min(ys)) - pad
    w = int(max(xs)) - min_x + pad * 2
    h = int(max(ys)) - min_y + pad * 2
    if w <= 0 or h <= 0 or w > 1200 or h > 1200:
        return
    with _scratch_slot(w, h) as tmp:
        pygame.draw.polygon(tmp, (*color[:3], 255),
                            [(px - min_x, py - min_y) for px, py in points],
                            int(width))
        if additive:
            if alpha < 255:
                tmp.fill((alpha, alpha, alpha, 255),
                         special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(tmp, (min_x, min_y),
                         special_flags=pygame.BLEND_RGB_ADD)
        else:
            tmp.set_alpha(alpha)
            surface.blit(tmp, (min_x, min_y))
            tmp.set_alpha(255)


def _blend_line(surface, color, a, b, alpha=255, width=1, additive=False):
    """Garis semi-transparan dengan blending benar (lihat _blend_polygon)."""
    alpha = int(max(0, min(255, alpha)))
    if alpha < 2:
        return
    width = max(1, int(width))
    pad = width + 2
    min_x = int(min(a[0], b[0])) - pad
    min_y = int(min(a[1], b[1])) - pad
    w = int(max(a[0], b[0])) - min_x + pad * 2
    h = int(max(a[1], b[1])) - min_y + pad * 2
    if w <= 0 or h <= 0 or w > 1200 or h > 1200:
        return
    with _scratch_slot(w, h) as tmp:
        pygame.draw.line(tmp, (*color[:3], 255),
                         (a[0] - min_x, a[1] - min_y),
                         (b[0] - min_x, b[1] - min_y), width)
        if additive:
            if alpha < 255:
                tmp.fill((alpha, alpha, alpha, 255),
                         special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(tmp, (min_x, min_y),
                         special_flags=pygame.BLEND_RGB_ADD)
        else:
            tmp.set_alpha(alpha)
            surface.blit(tmp, (min_x, min_y))
            tmp.set_alpha(255)


def _blend_circle(surface, color, cx, cy, radius, alpha=255, width=0,
                  additive=False):
    """Lingkaran semi-transparan dengan blending benar."""
    radius = max(1, int(radius))
    alpha = int(max(0, min(255, alpha)))
    if alpha < 2:
        return
    s = radius * 2 + 3
    with _scratch_slot(s, s) as tmp:
        pygame.draw.circle(tmp, (*color[:3], 255),
                           (radius + 1, radius + 1), radius, int(width))
        if additive:
            if alpha < 255:
                tmp.fill((alpha, alpha, alpha, 255),
                         special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(tmp, (int(cx) - radius - 1, int(cy) - radius - 1),
                         special_flags=pygame.BLEND_RGB_ADD)
        else:
            tmp.set_alpha(alpha)
            surface.blit(tmp, (int(cx) - radius - 1, int(cy) - radius - 1))
            tmp.set_alpha(255)


def flame_poly(surface, cx, cy, ang, length, width, color, alpha=255):
    """Lidah api directional (polygon tajam, bukan lingkaran)."""
    ca, sa = math.cos(ang), math.sin(ang)
    tip = (cx + ca * length, cy + sa * length)
    left = (cx + math.cos(ang + 2.3) * width * 0.5,
            cy + math.sin(ang + 2.3) * width * 0.5)
    right = (cx + math.cos(ang - 2.3) * width * 0.5,
             cy + math.sin(ang - 2.3) * width * 0.5)
    mid_l = (cx + ca * length * 0.45 + math.cos(ang + 1.57) * width * 0.34,
             cy + sa * length * 0.45 + math.sin(ang + 1.57) * width * 0.34)
    mid_r = (cx + ca * length * 0.45 + math.cos(ang - 1.57) * width * 0.34,
             cy + sa * length * 0.45 + math.sin(ang - 1.57) * width * 0.34)
    _blend_polygon(surface, color, [tip, mid_l, left, right, mid_r],
                   int(alpha), additive=True)
    return tip


def _crack_points(a, b, segs, jag, seed=0):
    """Titik retakan magma bergerigi dari a ke b (deterministik)."""
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


# Surface sementara dipakai untuk menggambar poligon transparan lalu
# di-blit sekali. Dua aturan penting:
#
#  1. UKURAN PERSIS. Surface di-cache per ukuran EKSAK, bukan dibulatkan.
#     Kalau dibulatkan, `blit` ikut menyalin sisi kosong di luar gambar —
#     dan karena surface dipakai ulang, sisa frame lain muncul sebagai
#     kotak nyasar di layar.
#  2. SLOT PER KEDALAMAN. `_blit_faded` sering dipanggil DI DALAM kode
#     yang sedang memegang scratch lain; kalau keduanya berbagi satu
#     surface, gambar yang belum sempat di-blit ikut terhapus.
_SCRATCH_CACHE = {}
_SCRATCH_DEPTH = [0]
_SCRATCH_MAX = 64


def _scratch(w, h):
    """Surface sementara berukuran PERSIS (w, h), bersih, anti-tabrakan."""
    w, h = max(1, int(w)), max(1, int(h))
    key = (w, h, _SCRATCH_DEPTH[0] % 4)
    s = _SCRATCH_CACHE.get(key)
    if s is None:
        if len(_SCRATCH_CACHE) >= _SCRATCH_MAX:
            _SCRATCH_CACHE.clear()
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        _SCRATCH_CACHE[key] = s
    else:
        s.fill((0, 0, 0, 0))
    s.set_alpha(255)
    return s


class _scratch_slot:
    """Context manager: pinjam scratch pada kedalaman berikutnya.

    Dipakai oleh kode yang menggambar poligon lalu memanggil helper lain
    (yang juga butuh scratch) sebelum sempat mem-blit hasilnya.
    """

    __slots__ = ("w", "h", "surf")

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.surf = None

    def __enter__(self):
        _SCRATCH_DEPTH[0] += 1
        self.surf = _scratch(self.w, self.h)
        return self.surf

    def __exit__(self, *_exc):
        _SCRATCH_DEPTH[0] -= 1
        return False


_PREMUL_CACHE = weakref.WeakKeyDictionary()


def _premultiplied(surf):
    """Versi premultiplied-alpha dari `surf`, di-cache per-surface.

    BLEND_RGB_ADD mengabaikan per-pixel alpha: pixel "transparan tapi
    berwarna" (mis. sisa gradien pada glow tanah) tetap ditambahkan,
    sehingga seluruh kotak surface terlihat sebagai blok pucat.
    Dengan mengalikan RGB dengan alpha lebih dulu, pixel alpha=0
    menjadi hitam (0,0,0) yang netral terhadap penjumlahan.
    """
    out = _PREMUL_CACHE.get(surf)
    if out is not None:
        return out
    out = surf.copy()
    try:
        out = out.premul_alpha()
    except Exception:
        # Fallback manual bila build pygame tidak punya premul_alpha().
        w, h = out.get_size()
        for px in range(w):
            for py in range(h):
                r, g, b, a = out.get_at((px, py))
                if a >= 255:
                    continue
                k = a / 255.0
                out.set_at((px, py),
                           (int(r * k), int(g * k), int(b * k), a))
    try:
        _PREMUL_CACHE[surf] = out
    except TypeError:
        pass
    return out


def _blit_faded(surface, surf, cx, cy, alpha=255, additive=False):
    if surf is None or alpha < 2:
        return
    cx, cy = int(cx), int(cy)
    rect = surf.get_rect(center=(cx, cy))
    if not additive:
        if alpha >= 255:
            surface.blit(surf, rect.topleft)
            return
        with _scratch_slot(rect.width, rect.height) as tmp:
            tmp.blit(surf, (0, 0))
            tmp.set_alpha(int(alpha))
            surface.blit(tmp, rect.topleft)
            tmp.set_alpha(255)
        return
    src = _premultiplied(surf)
    if alpha >= 255:
        surface.blit(src, rect.topleft, special_flags=pygame.BLEND_RGB_ADD)
        return
    # set_alpha diabaikan oleh BLEND_RGB_ADD, jadi skalakan RGB manual.
    k = max(0, min(255, int(alpha)))
    with _scratch_slot(rect.width, rect.height) as tmp:
        tmp.blit(src, (0, 0))
        tmp.fill((k, k, k, 255), special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(tmp, rect.topleft, special_flags=pygame.BLEND_RGB_ADD)


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
              alpha=255, gravity=0.0, color=(255, 150, 40),
              shape="ember", drag=0.0, additive=False, layer="front",
              scatter=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.ax = float(ax)
        self.ay = float(ay)
        self.life = float(max(0.01, life))
        self.max_life = float(max(0.01, life))
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
        x, y = int(self.x), int(self.y)
        s = max(1.0, self.size)

        if self.shape == "streak":
            ang = math.atan2(self.vy, self.vx)
            ca, sa = math.cos(ang), math.sin(ang)
            _blend_line(surface, self.color,
                        (x - ca * s * 1.8, y - sa * s * 1.8),
                        (x + ca * s * 1.8, y + sa * s * 1.8),
                        a, max(1, int(s * 0.6)), additive=self.additive)
        elif self.shape == "flame":
            ang = math.atan2(self.vy, self.vx)
            flame_poly(surface, x, y, ang, s * 2.4, s * 1.5,
                       self.color, a)
        elif self.shape == "ember":
            e = ember_surface(max(1, int(s)), self.color)
            _blit_faded(surface, e, x, y, a, additive=self.additive)
        elif self.shape == "debris":
            ang = self.rotation
            pts = [(x + math.cos(ang + i * 2.09) * s * (1.0 + 0.3 * (i % 2)),
                    y + math.sin(ang + i * 2.09) * s * (1.0 + 0.3 * (i % 2)))
                   for i in range(3)]
            _blend_polygon(surface, self.color, pts, a,
                           additive=self.additive)
        elif self.shape == "shard":
            ang = math.atan2(self.vy, self.vx)
            tip = (x + math.cos(ang) * s * 1.9, y + math.sin(ang) * s * 1.9)
            lx = x + math.cos(ang + 2.4) * s * 0.6
            ly = y + math.sin(ang + 2.4) * s * 0.6
            rx = x + math.cos(ang - 2.4) * s * 0.6
            ry = y + math.sin(ang - 2.4) * s * 0.6
            _blend_polygon(surface, self.color, [tip, (lx, ly), (rx, ry)],
                           a, additive=self.additive)
        elif self.shape == "dust":
            _blend_circle(surface, self.color, x, y, max(1, int(s * 0.55)),
                          a, additive=self.additive)
        elif self.shape == "smoke":
            g = glow_surface(max(3, int(s)) + 2, self.color, 0.32)
            _blit_faded(surface, g, x, y, int(a * 0.62), additive=False)
        elif self.shape == "spark":
            c = max(1, int(s))
            _blend_line(surface, self.color, (x - c, y), (x + c, y), a, 1,
                        additive=self.additive)
            _blend_line(surface, self.color, (x, y - c), (x, y + c), a, 1,
                        additive=self.additive)
        elif self.shape == "ring":
            _blend_circle(surface, self.color, x, y, max(1, int(s)), a,
                          width=1, additive=self.additive)
        else:
            _blend_circle(surface, self.color, x, y, max(1, int(s * 0.6)),
                          a, additive=self.additive)


# ============================================================================
# 5.  PARTICLE SYSTEM
# ============================================================================

class ParticleSystem:
    """Pool reusable, burst terarah, cap keras (tidak pernah tumbuh)."""

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = max(8, int(cap))
        self.particles = [Particle() for _ in range(self.cap)]
        self._cursor = 0

    def _next(self):
        p = self.particles[self._cursor]
        self._cursor = (self._cursor + 1) % self.cap
        return p

    def burst(self, x, y, count, speed=(30, 120), life=(0.2, 0.5),
              size=(2, 5), colors=((255, 150, 40),), spread=math.tau,
              direction=0.0, gravity=0.0, drag=0.0, shape="ember",
              additive=False, layer="front", rotation_speed=(0, 0),
              scatter=0.0, alpha=255):
        count = max(0, int(count))
        for _ in range(count):
            p = self._next()
            ang = direction + random.uniform(-spread / 2.0, spread / 2.0)
            spd = random.uniform(speed[0], speed[1])
            life_now = random.uniform(life[0], life[1])
            size_now = random.uniform(size[0], size[1])
            color = colors[int(random.random() * len(colors))]
            rot = random.uniform(-math.pi, math.pi)
            rot_spd = random.uniform(rotation_speed[0], rotation_speed[1])
            p.spawn(x, y, math.cos(ang) * spd, math.sin(ang) * spd,
                    0.0, 0.0, life_now, size_now, rot, rot_spd,
                    alpha, gravity, color, shape, drag, additive, layer,
                    scatter)

    def update(self, dt):
        for p in self.particles:
            if p.active:
                p.update(dt)

    def draw(self, surface, layer="front"):
        for p in self.particles:
            if p.active and p.layer == layer:
                p.draw(surface)

    def count(self):
        return sum(1 for p in self.particles if p.active)

    def clear(self):
        for p in self.particles:
            p.active = False


# ============================================================================
# 6.  SWING TRAIL  —  sabit api dari histori posisi ujung bilah
# ============================================================================

class SwingTrail:
    """Pita sapuan pedang prosedural dari histori posisi ujung bilah.

    Menyimpan beberapa posisi lama + posisi sekarang; poligon transparan
    dibangun dari sisi depan (leading edge) dan belakang (trailing edge)
    sehingga trail mengikuti ARK ayunan — bilah berputar, maka trail
    membentuk sabit, bukan garis statis.
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

    def _poly(self, width=9.0):
        pts = self.points
        if len(pts) < 3:
            return None
        out = []
        back = []
        n = len(pts)
        for i, (x, y) in enumerate(pts):
            nxt = pts[min(i + 1, n - 1)]
            prv = pts[max(i - 1, 0)]
            dx, dy = nxt[0] - prv[0], nxt[1] - prv[1]
            L = math.hypot(dx, dy)
            if L < 0.001:
                dx, dy, L = 1.0, 0.0, 1.0
            nx_, ny_ = -dy / L, dx / L
            t = i / max(1.0, n - 1)
            w = width * self.width_boost * (0.25 + 0.75 * t)
            out.append((x + nx_ * w, y + ny_ * w))
            back.append((x - nx_ * w, y - ny_ * w))
        back.reverse()
        return out + back

    def draw(self, surface, alpha=170, additive=True):
        if not self.active or len(self.points) < 3:
            return
        poly = self._poly(8.0)
        if poly is None:
            return
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        min_x, min_y = int(min(xs)) - 3, int(min(ys)) - 3
        w = int(max(xs)) - min_x + 6
        h = int(max(ys)) - min_y + 6
        if w <= 0 or h <= 0 or w > 900 or h > 900:
            return
        with _scratch_slot(w, h) as tmp:
            shifted = [(px - min_x, py - min_y) for px, py in poly]
            # 3 lapis: gelap luar -> mid -> inti terang (ramp, hard edge)
            pygame.draw.polygon(tmp, (*P["fire_dark"], int(alpha * 0.38)),
                                shifted)
            inner = self._poly(4.6)
            if inner:
                pygame.draw.polygon(
                    tmp, (*P["fire_mid"], int(alpha * 0.55)),
                    [(px - min_x, py - min_y) for px, py in inner])
            pts = self.points
            for i in range(1, len(pts)):
                t = i / max(1.0, len(pts) - 1)
                pygame.draw.line(
                    tmp, (*P["fire_bright"], int(alpha * t)),
                    (pts[i - 1][0] - min_x, pts[i - 1][1] - min_y),
                    (pts[i][0] - min_x, pts[i][1] - min_y),
                    max(1, int(3 * t) + 1))
            for i in range(max(1, len(pts) - 5), len(pts)):
                t = i / max(1.0, len(pts) - 1)
                pygame.draw.line(
                    tmp, (*P["fire_white"], int(alpha * t * 0.9)),
                    (pts[i - 1][0] - min_x, pts[i - 1][1] - min_y),
                    (pts[i][0] - min_x, pts[i][1] - min_y), 1)
            surface.blit(
                tmp, (min_x, min_y),
                special_flags=pygame.BLEND_RGB_ADD if additive else 0)


# ============================================================================
# 7.  IMPACT FX  —  flash + shockwave + debris + fragmen sabit
# ============================================================================

class ImpactFX:
    """Flash + ring shockwave + serpihan bara + fragmen sabit tunggal."""

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="fire", seed=0):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = float(power)
        self.crit = bool(crit)
        self.kind = kind
        self.age = 0.0
        self.life = 0.32 + 0.14 * min(2.0, max(0.2, power))
        self.seed = int(seed)

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

        # central flash (Surface transparan additive)
        r = int((7 + 15 * p) * (0.35 + 0.65 * t))
        _blit_faded(surface, glow_surface(max(6, r), P["fire_hot"], 0.75),
                    self.x, self.y, int(150 * fade), additive=True)

        # ring shockwave (chunky, dua lapis)
        rr = int((20 + 18 * p) * (0.25 + 0.85 * t))
        _blit_faded(surface,
                    ring_surface(rr, max(1, int(3 * p)), P["fire_bright"],
                                 int(210 * fade)),
                    self.x, self.y, int(225 * fade), additive=True)
        _blit_faded(surface,
                    ring_surface(max(4, rr - 7), 1, P["fire_light"],
                                 int(140 * fade), dashed=9),
                    self.x, self.y, int(160 * fade), additive=True)

        # fragmen sabit di sekitar sudut benturan (bukan lingkaran)
        span = 0.95
        pts = []
        for i in range(7):
            a = self.angle - span + (span * 2) * i / 6.0
            rr2 = (18 + 10 * p) * (0.45 + 0.8 * t)
            pts.append((self.x + math.cos(a) * rr2,
                        self.y + math.sin(a) * rr2 - 4 * t))
        if len(pts) >= 3:
            size = 110
            half = size // 2
            with _scratch_slot(size, size) as tmp:
                pygame.draw.lines(
                    tmp, (*P["fire_edge"], int(200 * fade)), False,
                    [(px - self.x + half, py - self.y + half)
                     for px, py in pts], max(1, int(3 * p)))
                surface.blit(tmp, (int(self.x) - half, int(self.y) - half),
                             special_flags=pygame.BLEND_RGB_ADD)

        # lidah api pecahan yang menyembur searah pukulan
        for i in range(3):
            a = self.angle + (i - 1) * 0.5
            d = (10 + 26 * p) * t
            flame_poly(surface, self.x + math.cos(a) * d,
                       self.y + math.sin(a) * d, a,
                       12 * p * fade, 7 * p * fade,
                       P["fire_light"] if i % 2 else P["fire_bright"],
                       int(190 * fade))


# ============================================================================
# 8.  PROJECTILE  —  Fire Orb (basic) + Meteor (skill R)
# ============================================================================

class FireOrbProjectile:
    """Bola api modular dari ujung greatsword.

    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY.
    Punya position, velocity, speed, damage, lifetime, target, radius,
    rotation, trail, particles, active — semua atribut wajib.
    """

    __slots__ = ("x", "y", "velocity", "speed", "damage", "lifetime",
                 "target", "radius", "rotation", "trail", "particles",
                 "active", "sx", "sy", "hit_radius", "kind", "age",
                 "hit_pos", "on_impact", "homing", "hit_target",
                 "trail_len", "spin", "seed")

    def __init__(self, sx, sy, tx, ty, speed=ORB_SPEED, damage=0,
                 target=None, radius=8.0, kind="fire", trail_len=14,
                 particles=None, on_impact=None, seed=0):
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
        self.lifetime = 3.0
        self.particles = particles
        self.on_impact = on_impact
        self.active = True
        self.hit_pos = None
        self.rotation = 0.0
        self.spin = 6.5
        self.homing = 0.55
        self.hit_target = False
        self.seed = int(seed)
        dx, dy = tx - sx, ty - sy
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

        # target tracking lembut (homing) — vector math murni
        if self.target is not None and getattr(self.target, "alive", False):
            tx = float(getattr(self.target, "x", self.x + 100))
            ty = float(getattr(self.target, "y", self.y)) - 6.0
            dx, dy = tx - self.x, ty - self.y
            L = math.hypot(dx, dy) or 1.0
            desired = pygame.Vector2(dx / L, dy / L)
            self.velocity = self.velocity.lerp(desired, self.homing * dt)
            if self.velocity.length_squared() > 0.0001:
                self.velocity = self.velocity.normalize()
            else:                              # pragma: no cover
                self.velocity = desired

        self.x += self.velocity.x * self.speed * dt
        self.y += self.velocity.y * self.speed * dt
        self.rotation += self.spin * dt

        self.trail.append((self.x, self.y, self.age))
        if len(self.trail) > self.trail_len:
            self.trail.pop(0)

        # collision detection
        if self.target is not None and getattr(self.target, "alive", False):
            tx = float(getattr(self.target, "x", self.x))
            ty = float(getattr(self.target, "y", self.y))
            hr = max(11.0, self.radius + float(
                getattr(self.target, "radius", 10.0)) * 0.55)
            if math.hypot(tx - self.x, ty - self.y) <= hr:
                self._hit(tx, ty - 4.0)
                return

        # partikel jejak bara
        if self.particles is not None and len(self.trail) % 2 == 0:
            back = math.atan2(self.velocity.y, self.velocity.x) + math.pi
            self.particles.burst(self.x, self.y, 1,
                                 speed=(15, 60), life=(0.14, 0.36),
                                 size=(1, 3),
                                 colors=(P["fire_light"], P["fire_bright"]),
                                 spread=1.3, direction=back,
                                 drag=1.6, shape="ember", additive=True)

    def _hit(self, x, y):
        if not self.active:
            return
        self.hit_pos = pygame.Vector2(x, y)
        self.hit_target = True
        self.active = False
        if self.on_impact:
            try:
                self.on_impact(self)
            except Exception:                  # pragma: no cover
                pass

    def draw(self, surface):
        if not self.active:
            return
        # TRAIL: bola bara memudar (bukan garis polos)
        n = len(self.trail)
        for i, (tx, ty, _a) in enumerate(self.trail):
            t = (i + 1) / max(1, n)
            alpha = int(30 + 120 * t * (1.0 - self.age / self.lifetime))
            r = max(2, int(2.0 + 4.5 * t))
            _blit_faded(surface, glow_surface(r + 3, P["fire_dark"], 0.55),
                        tx, ty, alpha, additive=True)
        ang = math.atan2(self.velocity.y, self.velocity.x)
        # GLOW ketat
        _blit_faded(surface, glow_surface(13, P["fire_mid"], 0.6),
                    self.x, self.y, 140, additive=True)
        # DIRECTIONAL SHAPE: komet berekor (core + cangkang)
        self._draw_comet(surface, self.x, self.y, ang)
        # halo lidah api berputar
        for i in range(3):
            a = self.rotation * 1.6 + i * math.tau / 3
            fx = self.x + math.cos(a) * 11.0
            fy = self.y + math.sin(a) * 11.0
            flame_poly(surface, fx, fy, a, 7.0, 4.0, P["fire_light"], 200)

    def _draw_comet(self, surface, px, py, ang):
        ca, sa = math.cos(ang), math.sin(ang)
        perp = (-sa, ca)
        head = (px + ca * 9.0, py + sa * 9.0)
        tail = (px - ca * 15.0, py - sa * 15.0)
        w = 6.5
        pygame.draw.polygon(surface, P["fire_darkest"],
                            [head,
                             (px + perp[0] * w, py + perp[1] * w),
                             tail,
                             (px - perp[0] * w, py - perp[1] * w)])
        pygame.draw.polygon(surface, P["fire_mid"],
                            [(head[0] - ca, head[1] - sa),
                             (px + perp[0] * w * 0.66,
                              py + perp[1] * w * 0.66),
                             (tail[0] + ca * 3, tail[1] + sa * 3),
                             (px - perp[0] * w * 0.66,
                              py - perp[1] * w * 0.66)])
        pygame.draw.polygon(surface, P["fire_light"],
                            [(head[0] - ca * 2, head[1] - sa * 2),
                             (px + perp[0] * w * 0.36,
                              py + perp[1] * w * 0.36),
                             (tail[0] + ca * 6, tail[1] + sa * 6),
                             (px - perp[0] * w * 0.36,
                              py - perp[1] * w * 0.36)])
        pygame.draw.circle(surface, P["fire_hot"],
                           (int(px + ca * 2), int(py + sa * 2)), 3)
        pygame.draw.circle(surface, P["fire_white"],
                           (int(px + ca * 3), int(py + sa * 3)), 1)


class MeteorProjectile:
    """Meteor Cataclysm (R): jatuh dari luar layar ke titik dampak.

    Visual: inti magma + cangkang batu + ekor asap; saat mendarat memicu
    ledakan lewat ``on_impact`` (director yang membuat ImpactFX + debris).
    """

    __slots__ = ("x", "y", "velocity", "speed", "damage", "lifetime",
                 "target", "radius", "rotation", "trail", "particles",
                 "active", "age", "hit_radius", "impact", "on_impact",
                 "seed", "delay")

    def __init__(self, ix, iy, particles=None, speed=METEOR_SPEED,
                 delay=0.0, on_impact=None, seed=0, from_left=True):
        self.impact = (float(ix), float(iy))
        self.speed = float(speed)
        self.damage = 0
        self.target = None
        self.radius = 12.0
        self.hit_radius = 16.0
        self.age = 0.0
        self.delay = float(delay)
        self.lifetime = self.delay + 1.8
        self.particles = particles
        self.on_impact = on_impact
        self.active = True
        self.rotation = 0.0
        self.seed = int(seed)
        side = -1.0 if from_left else 1.0
        self.x = self.impact[0] + side * 210.0
        self.y = self.impact[1] - 320.0
        dx = self.impact[0] - self.x
        dy = self.impact[1] - self.y
        L = math.hypot(dx, dy) or 1.0
        self.velocity = pygame.Vector2(dx / L, dy / L)
        self.trail = []

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age < self.delay:
            return
        if self.age >= self.lifetime:
            self._land()
            return
        self.x += self.velocity.x * self.speed * dt
        self.y += self.velocity.y * self.speed * dt
        self.rotation += dt * 5.0
        self.trail.append((self.x, self.y))
        if len(self.trail) > 16:
            self.trail.pop(0)
        if self.particles is not None and len(self.trail) % 2 == 0:
            self.particles.burst(self.x, self.y, 1, speed=(20, 70),
                                 life=(0.25, 0.6), size=(3, 6),
                                 colors=(P["smoke"], P["ash"]),
                                 spread=1.6,
                                 direction=-math.pi / 2, drag=1.2,
                                 shape="smoke", layer="back")
        # mendarat
        dx = self.impact[0] - self.x
        dy = self.impact[1] - self.y
        if dy >= -2.0 or math.hypot(dx, dy) < self.speed * dt:
            self._land()

    def _land(self):
        if not self.active:
            return
        self.active = False
        if self.on_impact:
            try:
                self.on_impact(self)
            except Exception:                  # pragma: no cover
                pass

    def draw(self, surface):
        if not self.active or self.age < self.delay:
            return
        n = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            t = (i + 1) / max(1, n)
            _blit_faded(surface,
                        glow_surface(int(4 + 9 * t), P["fire_dark"], 0.5),
                        tx, ty, int(28 + 110 * t), additive=True)
        px, py = int(self.x), int(self.y)
        _blit_faded(surface, glow_surface(24, P["fire_mid"], 0.7),
                    px, py, 175, additive=True)
        # cangkang batu (poligon kasar, bukan lingkaran)
        pts = []
        for i in range(7):
            a = self.rotation + i * math.tau / 7
            r = 11.0 + _hash01(self.seed + i) * 4.0
            pts.append((px + math.cos(a) * r, py + math.sin(a) * r))
        pygame.draw.polygon(surface, P["smoke"], pts)
        pygame.draw.polygon(surface, P["fire_darkest"], pts, 2)
        # retakan magma di badan meteor
        for i in range(3):
            a = self.rotation * 1.4 + i * 2.1
            pygame.draw.line(surface, P["magma"],
                             (px - math.cos(a) * 7, py - math.sin(a) * 7),
                             (px + math.cos(a) * 7, py + math.sin(a) * 7), 2)
        pygame.draw.circle(surface, P["fire_bright"], (px, py), 4)
        pygame.draw.circle(surface, P["fire_white"], (px - 1, py - 1), 2)
        # ekor api searah gerak
        ang = math.atan2(self.velocity.y, self.velocity.x) + math.pi
        flame_poly(surface, px, py, ang, 30.0, 15.0, P["fire_light"], 190)
        flame_poly(surface, px, py, ang, 20.0, 8.0, P["fire_hot"], 220)


# ============================================================================
# 9.  PROJECTILE SYSTEM
# ============================================================================

class ProjectileSystem:
    """Manajer proyektil dengan pool maksimal (tidak pernah bocor)."""

    def __init__(self, particles=None):
        self.particles = particles
        self.items = []

    def spawn(self, sx, sy, tx, ty, speed=ORB_SPEED, damage=0,
              target=None, radius=8.0, kind="fire", trail_len=14,
              on_impact=None, seed=0):
        if len(self.items) >= MAX_PROJECTILES:
            self.items.pop(0)
        pr = FireOrbProjectile(sx, sy, tx, ty, speed, damage, target,
                               radius, kind, trail_len, self.particles,
                               on_impact, seed)
        self.items.append(pr)
        return pr

    def spawn_meteor(self, ix, iy, delay=0.0, speed=METEOR_SPEED,
                     on_impact=None, seed=0, from_left=True):
        if len(self.items) >= MAX_PROJECTILES:
            self.items.pop(0)
        m = MeteorProjectile(ix, iy, self.particles, speed, delay,
                             on_impact, seed, from_left)
        self.items.append(m)
        return m

    def update(self, dt):
        for pr in self.items:
            pr.update(dt)
        self.items = [pr for pr in self.items if pr.active]

    def draw(self, surface):
        for pr in self.items:
            pr.draw(surface)

    def draw_debug(self, surface):
        for pr in self.items:
            pygame.draw.circle(surface, (255, 80, 220),
                               (int(pr.x), int(pr.y)),
                               int(pr.hit_radius), 1)

    def count(self):
        return len(self.items)

    def clear(self):
        self.items.clear()


# ============================================================================
# 10.  SKILL FX  (Q Dragon Breath, W Dragon Tail, E Dragon Blood,
#                 R Elder Dragon Form)
# ============================================================================

class SkillFX:
    """Satu skill aktif + lifecycle CAST -> CHARGE -> RELEASE -> TRAVEL/AREA
    -> IMPACT -> AFTER EFFECT -> FADE.

    Tiap fase punya visualnya sendiri dan TIDAK semuanya lingkaran:
    cone bergerigi, sabit ekor, rune naga bergigi, retakan magma,
    pilar api, dan siluet sayap.
    """

    def __init__(self, skill, x, y, particles, aim=None, radius=None):
        self.skill = skill if skill in SKILL_TOTAL else "q"
        self.x = float(x)
        self.y = float(y)
        self.particles = particles
        self.age = 0.0
        self.life = SKILL_TOTAL[self.skill]
        self.radius = float(radius if radius else
                            WORLD_RADIUS.get(self.skill, 100.0))
        facing = 1.0
        if aim is None:
            aim = (self.x + 140.0, self.y - 8.0)
        self.aim = (float(aim[0]), float(aim[1]))
        self.angle = math.atan2(self.aim[1] - self.y, self.aim[0] - self.x)
        self.facing = 1 if self.aim[0] >= self.x else -1
        self.seed = random.randint(0, 1 << 20)
        self.done = False
        self._released = False
        self._impacted = False

    # ---------------------------------------------------------------
    @property
    def phase(self):
        """Nama fase lifecycle sekarang."""
        t = self.age / max(0.001, self.life)
        if t < 0.16:
            return "CAST"
        if t < 0.32:
            return "CHARGE"
        if t < 0.44:
            return "RELEASE"
        if t < 0.70:
            return "AREA"
        if t < 0.84:
            return "IMPACT"
        return "FADE"

    def _t(self):
        return min(1.0, self.age / max(0.001, self.life))

    def update(self, dt):
        if self.done:
            return
        self.age += dt
        t = self._t()
        if t >= 1.0:
            self.done = True
            return
        ph = self.phase
        if ph in ("CAST", "CHARGE") and self.particles is not None:
            if random.random() < 0.55:
                a = random.uniform(0, math.tau)
                r = 26 + random.random() * 16
                self.particles.burst(
                    self.x + math.cos(a) * r, self.y - 14 + math.sin(a) * 10,
                    1, speed=(20, 70), life=(0.2, 0.45), size=(1, 3),
                    colors=(P["fire_light"], P["fire_bright"]),
                    direction=math.atan2(self.y - 14 - (self.y - 14 +
                                                        math.sin(a) * 10),
                                         self.x - (self.x +
                                                   math.cos(a) * r)),
                    spread=1.0, drag=1.5, shape="ember", additive=True)
        if ph == "RELEASE" and not self._released:
            self._released = True
            self._on_release()
        if ph == "IMPACT" and not self._impacted:
            self._impacted = True
            self._on_impact_burst()

    def _on_release(self):
        if self.particles is None:
            return
        if self.skill == "q":
            self.particles.burst(
                self.x + self.facing * 14, self.y - 30, 16,
                speed=(180, 420), life=(0.18, 0.5), size=(2, 5),
                colors=(P["fire_bright"], P["fire_light"], P["fire_hot"]),
                spread=BREATH_CONE * 2.0, direction=self.angle,
                drag=1.6, shape="flame", additive=True)
        elif self.skill == "w":
            self.particles.burst(
                self.x, self.y + 6, 20, speed=(140, 330),
                life=(0.2, 0.55), size=(2, 6),
                colors=(P["fire_mid"], P["fire_light"], P["dust"]),
                spread=math.tau, gravity=260.0, drag=1.4,
                shape="debris", rotation_speed=(-14, 14))
        elif self.skill == "e":
            self.particles.burst(
                self.x, self.y - 12, 18, speed=(40, 150),
                life=(0.35, 0.9), size=(2, 5),
                colors=(P["red_light"], P["fire_mid"], P["fire_bright"]),
                spread=math.tau, gravity=-70.0, drag=1.1,
                shape="ember", additive=True)
        else:  # r
            self.particles.burst(
                self.x, self.y, 26, speed=(160, 430),
                life=(0.28, 0.85), size=(3, 7),
                colors=(P["fire_light"], P["fire_bright"], P["magma"]),
                spread=math.tau, gravity=180.0, drag=1.0,
                shape="ember", additive=True)
            self.particles.burst(
                self.x, self.y + 8, 12, speed=(30, 120),
                life=(0.5, 1.2), size=(5, 10),
                colors=(P["smoke"], P["ash"]),
                spread=math.tau, gravity=-40.0, drag=1.3,
                shape="smoke", layer="back")

    def _on_impact_burst(self):
        if self.particles is None:
            return
        ax, ay = self.aim
        self.particles.burst(
            ax, ay, 12, speed=(90, 260), life=(0.18, 0.5), size=(2, 5),
            colors=(P["fire_hot"], P["fire_bright"], P["fire_light"]),
            spread=math.tau, gravity=240.0, drag=1.6,
            shape="streak", additive=True)

    # ---------------------------------------------------------------
    def draw_ground(self, surface):
        """Lapisan tanah (di bawah karakter): telegraph, rune, bara."""
        if self.done:
            return
        t = self._t()
        fade = 1.0 - max(0.0, (t - 0.72) / 0.28)
        fade = max(0.0, min(1.0, fade))
        if fade <= 0.0:
            return
        if self.skill == "q":
            self._ground_cone(surface, t, fade)
        elif self.skill == "w":
            self._ground_sweep(surface, t, fade)
        elif self.skill == "e":
            self._ground_rune(surface, t, fade)
        else:
            self._ground_erupt(surface, t, fade)

    def _ground_cone(self, surface, t, fade):
        """Jalur hangus cone Dragon Breath (poligon, bukan lingkaran)."""
        reach = self.radius * min(1.0, t / 0.5)
        a = self.angle
        half = BREATH_CONE
        base = (self.x + math.cos(a) * 12, self.y + 18)
        pts = [base]
        for i in range(7):
            aa = a - half + (half * 2) * i / 6.0
            pts.append((self.x + math.cos(aa) * reach,
                        self.y + 18 + math.sin(aa) * reach * 0.32))
        if len(pts) < 3:
            return
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        min_x, min_y = int(min(xs)) - 4, int(min(ys)) - 4
        w = int(max(xs)) - min_x + 8
        h = int(max(ys)) - min_y + 8
        if w <= 0 or h <= 0 or w > 900 or h > 900:
            return
        with _scratch_slot(w, h) as tmp:
            sh = [(px - min_x, py - min_y) for px, py in pts]
            pygame.draw.polygon(tmp, (*P["fire_darkest"], int(120 * fade)),
                                sh)
            pygame.draw.polygon(tmp, (*P["fire_dark"], int(90 * fade)),
                                sh, 3)
            surface.blit(tmp, (min_x, min_y))
        # retakan magma memancar
        for i in range(4):
            aa = a - half * 0.7 + half * 1.4 * i / 3.0
            end = (self.x + math.cos(aa) * reach * 0.9,
                   self.y + 18 + math.sin(aa) * reach * 0.3)
            cp = _crack_points((self.x, self.y + 18), end, 5, 7.0,
                               self.seed + i * 31)
            pygame.draw.lines(surface, P["magma"], False,
                              [(int(px), int(py)) for px, py in cp], 2)

    def _ground_sweep(self, surface, t, fade):
        """Cincin retak sapuan ekor + debu."""
        r = int(self.radius * (0.35 + 0.75 * min(1.0, t / 0.55)))
        _blit_faded(surface, ellipse_ring_surface(
            r, int(r * 0.38), 3, (*P["fire_mid"], int(190 * fade))),
            self.x, self.y + 20, int(220 * fade), additive=True)
        _blit_faded(surface, ellipse_ring_surface(
            max(6, r - 12), int(r * 0.3), 2,
            (*P["fire_dark"], int(150 * fade))),
            self.x, self.y + 20, int(180 * fade), additive=True)
        for i in range(8):
            a = self.seed * 0.001 + i * math.tau / 8
            end = (self.x + math.cos(a) * r,
                   self.y + 20 + math.sin(a) * r * 0.36)
            cp = _crack_points((self.x, self.y + 20), end, 4, 5.0,
                               self.seed + i * 17)
            pygame.draw.lines(surface, P["fire_dark"], False,
                              [(int(px), int(py)) for px, py in cp], 2)

    def _ground_rune(self, surface, t, fade):
        """Rune naga berputar (Dragon Blood)."""
        r = int(self.radius * 0.62)
        spin = math.degrees(t * 2.4)
        rune = rune_surface(r, P["red_light"], teeth=9)
        rot = pygame.transform.rotate(rune, spin)
        _blit_faded(surface, rot, self.x, self.y + 22, int(190 * fade),
                    additive=True)
        _blit_faded(surface, ground_glow_surface(r, P["fire_dark"], 0.9),
                    self.x, self.y + 24, int(200 * fade), additive=True)
        _blit_faded(surface, ellipse_ring_surface(
            r, int(r * 0.36), 2, (*P["gold"], int(170 * fade))),
            self.x, self.y + 22, int(200 * fade), additive=True)

    def _ground_erupt(self, surface, t, fade):
        """Kawah magma Elder Dragon Form: cincin + retakan besar."""
        r = int(self.radius * (0.3 + 0.8 * min(1.0, t / 0.6)))
        _blit_faded(surface, ground_glow_surface(r, P["magma"], 1.0),
                    self.x, self.y + 22, int(220 * fade), additive=True)
        _blit_faded(surface, ellipse_ring_surface(
            r, int(r * 0.36), 4, (*P["fire_bright"], int(200 * fade))),
            self.x, self.y + 22, int(230 * fade), additive=True)
        _blit_faded(surface, ellipse_ring_surface(
            max(8, int(r * 0.62)), int(r * 0.24), 2,
            (*P["fire_light"], int(160 * fade))),
            self.x, self.y + 22, int(190 * fade), additive=True)
        for i in range(10):
            a = i * math.tau / 10 + self.seed * 0.0007
            end = (self.x + math.cos(a) * r * 1.05,
                   self.y + 22 + math.sin(a) * r * 0.4)
            cp = _crack_points((self.x, self.y + 22), end, 5, 8.0,
                               self.seed + i * 53)
            pygame.draw.lines(surface, P["magma"], False,
                              [(int(px), int(py)) for px, py in cp],
                              2 if i % 2 else 3)

    # ---------------------------------------------------------------
    def draw_front(self, surface):
        """Lapisan depan (di atas karakter): api, sabit, pilar, sayap."""
        if self.done:
            return
        t = self._t()
        if self.skill == "q":
            self._front_breath(surface, t)
        elif self.skill == "w":
            self._front_tail(surface, t)
        elif self.skill == "e":
            self._front_blood(surface, t)
        else:
            self._front_elder(surface, t)

    def _front_breath(self, surface, t):
        """Semburan cone api dari mulut helm naga."""
        if t < 0.18:
            # CHARGE: bola api mengumpul di mulut
            k = t / 0.18
            mx = self.x + self.facing * 14
            my = self.y - 30
            _blit_faded(surface,
                        glow_surface(int(6 + 16 * k), P["fire_bright"], 0.8),
                        mx, my, int(200 * k), additive=True)
            for i in range(4):
                a = t * 12 + i * math.tau / 4
                flame_poly(surface, mx + math.cos(a) * (16 - 12 * k),
                           my + math.sin(a) * (12 - 9 * k),
                           a + math.pi / 2, 8 * k + 3, 5, P["fire_light"],
                           int(220 * k))
            return
        if t > 0.80:
            return
        k = min(1.0, (t - 0.18) / 0.22)
        decay = 1.0 if t < 0.62 else max(0.0, 1.0 - (t - 0.62) / 0.18)
        reach = self.radius * k
        a = self.angle
        half = BREATH_CONE
        mx = self.x + self.facing * 14
        my = self.y - 30
        # lapis luar -> dalam (ramp api, hard edge)
        layers = ((1.00, P["fire_dark"], 110), (0.82, P["fire_mid"], 150),
                  (0.60, P["fire_light"], 190), (0.36, P["fire_bright"], 220),
                  (0.18, P["fire_hot"], 240))
        for scale, color, alpha in layers:
            pts = [(mx, my)]
            n = 9
            for i in range(n):
                aa = a - half * scale + (half * 2 * scale) * i / (n - 1)
                wobble = math.sin(t * 26 + i * 1.7) * 6.0 * scale
                rr = reach * scale + wobble
                pts.append((mx + math.cos(aa) * rr, my + math.sin(aa) * rr))
            if len(pts) < 3:
                continue
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            min_x, min_y = int(min(xs)) - 4, int(min(ys)) - 4
            w = int(max(xs)) - min_x + 8
            h = int(max(ys)) - min_y + 8
            if w <= 0 or h <= 0 or w > 900 or h > 900:
                continue
            with _scratch_slot(w, h) as tmp:
                pygame.draw.polygon(
                    tmp, (*color, int(alpha * decay)),
                    [(px - min_x, py - min_y) for px, py in pts])
                surface.blit(tmp, (min_x, min_y),
                             special_flags=pygame.BLEND_RGB_ADD)
        # lidah api besar di ujung cone
        for i in range(5):
            aa = a - half * 0.8 + half * 1.6 * i / 4.0
            d = reach * (0.7 + 0.25 * math.sin(t * 18 + i))
            flame_poly(surface, mx + math.cos(aa) * d,
                       my + math.sin(aa) * d, aa, 26 * decay, 16 * decay,
                       P["fire_bright"] if i % 2 else P["fire_hot"],
                       int(210 * decay))

    def _front_tail(self, surface, t):
        """Sabit ekor naga menyapu 360 derajat."""
        if t > 0.78:
            return
        k = min(1.0, t / 0.5)
        fade = 1.0 if t < 0.55 else max(0.0, 1.0 - (t - 0.55) / 0.23)
        r = self.radius * (0.4 + 0.7 * k)
        sweep_end = -math.pi / 2 + math.tau * k * 1.15
        seg = 16
        span = 2.3
        pts_out, pts_in = [], []
        for i in range(seg + 1):
            a = sweep_end - span * i / seg
            wob = math.sin(t * 14 + i * 0.6) * 4.0
            pts_out.append((self.x + math.cos(a) * (r + 12 + wob),
                            self.y + 8 + math.sin(a) * (r + 12 + wob) * 0.42))
            pts_in.append((self.x + math.cos(a) * (r - 14),
                           self.y + 8 + math.sin(a) * (r - 14) * 0.42))
        poly = pts_out + list(reversed(pts_in))
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        min_x, min_y = int(min(xs)) - 4, int(min(ys)) - 4
        w = int(max(xs)) - min_x + 8
        h = int(max(ys)) - min_y + 8
        if 0 < w <= 900 and 0 < h <= 900:
            with _scratch_slot(w, h) as tmp:
                pygame.draw.polygon(
                    tmp, (*P["fire_mid"], int(150 * fade)),
                    [(px - min_x, py - min_y) for px, py in poly])
                pygame.draw.lines(
                    tmp, (*P["fire_bright"], int(220 * fade)), False,
                    [(px - min_x, py - min_y) for px, py in pts_out], 3)
                surface.blit(tmp, (min_x, min_y),
                             special_flags=pygame.BLEND_RGB_ADD)
        # ujung ekor bersisik (segitiga chunky)
        tipa = sweep_end
        tx = self.x + math.cos(tipa) * (r + 16)
        ty = self.y + 8 + math.sin(tipa) * (r + 16) * 0.42
        for i in range(4):
            d = 1.0 - i * 0.2
            flame_poly(surface, tx, ty, tipa + math.pi / 2,
                       22 * d * fade, 13 * d * fade,
                       P["scale_light"] if i % 2 else P["fire_light"],
                       int(220 * fade))

    def _front_blood(self, surface, t):
        """Aura darah naga: pilar bara naik + cincin energi."""
        fade = 1.0 if t < 0.7 else max(0.0, 1.0 - (t - 0.7) / 0.3)
        k = min(1.0, t / 0.35)
        for i in range(7):
            a = i * math.tau / 7 + t * 2.2
            r = 30 + 8 * math.sin(t * 5 + i)
            px = self.x + math.cos(a) * r
            base_y = self.y + 16
            h = 46 * k * (0.65 + 0.35 * math.sin(t * 7 + i * 1.3))
            for j in range(4):
                jt = j / 3.0
                flame_poly(surface, px, base_y - h * jt, -math.pi / 2,
                           16 * (1.0 - jt * 0.5), 9 * (1.0 - jt * 0.4),
                           (P["fire_light"], P["fire_bright"], P["red_light"],
                            P["fire_hot"])[j],
                           int(180 * fade * (1.0 - jt * 0.35)))
        rr = int(34 + 16 * math.sin(t * 6.0))
        _blit_faded(surface, ring_surface(rr, 2, P["red_light"],
                                          int(150 * fade), dashed=12),
                    self.x, self.y - 12, int(190 * fade), additive=True)
        _blit_faded(surface, glow_surface(30, P["fire_dark"], 0.5),
                    self.x, self.y - 14, int(120 * fade), additive=True)

    def _front_elder(self, surface, t):
        """Elder Dragon Form: kolom api + siluet sayap + shockwave."""
        fade = 1.0 if t < 0.72 else max(0.0, 1.0 - (t - 0.72) / 0.28)
        k = min(1.0, t / 0.3)
        # pilar api utama (poligon meruncing, bukan lingkaran)
        h = 170 * k
        w = 40 + 12 * math.sin(t * 9)
        base = self.y + 18
        for scale, color, alpha in ((1.0, P["fire_dark"], 120),
                                    (0.72, P["fire_mid"], 160),
                                    (0.46, P["fire_light"], 200),
                                    (0.24, P["fire_hot"], 230)):
            pts = [(self.x - w * scale, base),
                   (self.x - w * scale * 0.55, base - h * 0.45),
                   (self.x - w * scale * 0.22 +
                    math.sin(t * 11) * 6, base - h * 0.82),
                   (self.x, base - h),
                   (self.x + w * scale * 0.22 +
                    math.sin(t * 11 + 1.2) * 6, base - h * 0.82),
                   (self.x + w * scale * 0.55, base - h * 0.45),
                   (self.x + w * scale, base)]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            min_x, min_y = int(min(xs)) - 4, int(min(ys)) - 4
            ww = int(max(xs)) - min_x + 8
            hh = int(max(ys)) - min_y + 8
            if not (0 < ww <= 900 and 0 < hh <= 900):
                continue
            with _scratch_slot(ww, hh) as tmp:
                pygame.draw.polygon(
                    tmp, (*color, int(alpha * fade)),
                    [(px - min_x, py - min_y) for px, py in pts])
                surface.blit(tmp, (min_x, min_y),
                             special_flags=pygame.BLEND_RGB_ADD)
        # siluet sayap naga terbentang (dua poligon bergerigi)
        spread = min(1.0, t / 0.42)
        for side in (-1, 1):
            wpts = [(self.x + side * 8, self.y - 44)]
            for i in range(4):
                ang = -0.85 + i * 0.42
                rr = (52 + i * 16) * spread
                wpts.append((self.x + side * math.cos(ang) * rr,
                             self.y - 46 + math.sin(ang) * rr * 0.72))
                wpts.append((self.x + side * math.cos(ang + 0.2) * rr * 0.72,
                             self.y - 40 + math.sin(ang + 0.2) * rr * 0.6))
            wpts.append((self.x + side * 6, self.y - 8))
            xs = [p[0] for p in wpts]
            ys = [p[1] for p in wpts]
            min_x, min_y = int(min(xs)) - 4, int(min(ys)) - 4
            ww = int(max(xs)) - min_x + 8
            hh = int(max(ys)) - min_y + 8
            if not (0 < ww <= 900 and 0 < hh <= 900):
                continue
            with _scratch_slot(ww, hh) as tmp:
                sh = [(px - min_x, py - min_y) for px, py in wpts]
                pygame.draw.polygon(tmp, (*P["red_deep"], int(150 * fade)),
                                    sh)
                pygame.draw.polygon(tmp, (*P["fire_mid"], int(200 * fade)),
                                    sh, 2)
                surface.blit(tmp, (min_x, min_y))
        # shockwave cincin yang mengembang
        rr = int(30 + 200 * min(1.0, t / 0.55))
        _blit_faded(surface, ring_surface(rr, 3, P["fire_bright"],
                                          int(170 * (1.0 - t))),
                    self.x, self.y + 12, int(200 * fade), additive=True)


# ============================================================================
# 11.  DIRECTOR  —  satu instance per unit
# ============================================================================

class IgnisFXDirector:
    """Mengikat particle + trail + proyektil + impact + skill FX untuk satu
    unit Ignis Drachorn (true boss MAUPUN hero hasil unlock — kode sama,
    hanya sumber transformasinya yang berbeda)."""

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
        self._last_hp = None
        self._death_done = False
        self._ember_clock = 0.0
        #: sisa waktu "unit ini sedang tampil di layar" (detik). Diisi
        #: ulang tiap kali draw dipanggil; emitter ambient hanya jalan
        #: selama nilainya positif, jadi unit yang tidak digambar (mati,
        #: off-screen, match selesai) tidak pernah membocorkan partikel.
        self._visible = 0.0

    # ------------------------------------------------------------------
    # SWING (ark greatsword)
    # ------------------------------------------------------------------
    def on_swing_start(self, x, y, facing):
        """Awal ayunan: trail reset + debu bara di kaki (anticipation)."""
        self.trail.reset()
        self.trail.width_boost = 1.0
        self.swing_active = True
        self.particles.burst(
            x - facing * 8, y + 34, 7,
            speed=(30, 110), life=(0.18, 0.45), size=(2, 5),
            colors=(P["dust"], P["ash"], P["fire_dark"]),
            spread=1.3, direction=math.pi if facing > 0 else 0.0,
            gravity=140.0, drag=2.6, shape="dust", layer="back")

    def on_swing_end(self):
        self.swing_active = False

    def on_swing_impact_frame(self, x, y, facing):
        """Sapu udara di frame IMPACT — feedback walau tidak kena apa pun."""
        grip, tip = sword_points(self.hero, x, y)
        ang = math.atan2(tip[1] - grip[1], tip[0] - grip[0])
        self.trail.width_boost = 1.55
        self.particles.burst(
            tip[0], tip[1], 10,
            speed=(140, 300), life=(0.1, 0.28), size=(2, 4),
            colors=(P["fire_hot"], P["fire_bright"], P["fire_light"]),
            spread=1.5, direction=ang + math.pi / 2, drag=3.6,
            shape="streak", additive=True)
        self.particles.burst(
            tip[0], tip[1], 6,
            speed=(70, 190), life=(0.16, 0.4), size=(2, 5),
            colors=(P["fire_light"], P["fire_mid"], P["ember"]),
            spread=1.6, direction=ang - math.pi / 2, drag=3.0,
            shape="ember", additive=True, rotation_speed=(-12, 12))
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(tip[0], tip[1], ang, 0.6, False,
                                     kind="fire", seed=int(self.frames)))
        if shake_allowed():
            _feel_shake(3.6, 0.13)

    # ------------------------------------------------------------------
    # SKILL
    # ------------------------------------------------------------------
    def on_cast(self, x, y, skill, aim=None):
        """Skill dilepas: SkillFX + guncangan + (R) hujan meteor."""
        if skill not in SKILL_TOTAL:
            return None
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        if aim is None:
            tgt = getattr(self.hero, "target", None)
            if tgt is not None and getattr(tgt, "alive", False):
                aim = (float(tgt.x), float(tgt.y))
            else:
                facing = 1 if getattr(self.hero, "direction", 1) >= 0 else -1
                aim = (x + facing * 150, y - 8)
        fx = SkillFX(skill, x, y, self.particles, aim=aim,
                     radius=WORLD_RADIUS.get(skill))
        self.skills.append(fx)
        heavy = skill == "r"
        if shake_allowed():
            _feel_shake(14.0 if heavy else 6.5, 0.36 if heavy else 0.18)
        if heavy:
            _feel_hit_stop(0.06)
            self.release_meteors(x, y)
        self.particles.burst(x, y + 16, 12,
                             speed=(70, 200), life=(0.22, 0.55), size=(2, 5),
                             colors=(P["dust"], P["ash"], P["fire_dark"]),
                             spread=math.tau, gravity=200.0, drag=2.0,
                             shape="dust", layer="back")
        return fx

    def release_meteors(self, x, y, count=METEOR_COUNT):
        """Hujan meteor Cataclysm di sekitar unit (skill R)."""
        out = []
        for i in range(int(count)):
            a = _hash01(self.frames + i * 71) * math.tau
            d = 40.0 + _hash01(self.frames * 3 + i) * WORLD_RADIUS["r"] * 0.65
            ix = x + math.cos(a) * d
            iy = y + math.sin(a) * d * 0.42 + 14
            m = self.projectiles.spawn_meteor(
                ix, iy, delay=0.12 + i * 0.13, seed=self.frames + i * 13,
                from_left=(i % 2 == 0),
                on_impact=lambda mm: self.on_meteor_land(mm))
            out.append(m)
        return out

    def on_meteor_land(self, meteor):
        """Meteor mendarat: kawah, debris, api, shake, hit-stop kecil."""
        mx, my = meteor.impact
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(mx, my, -math.pi / 2, 1.5, False,
                                     kind="fire", seed=meteor.seed))
        self.particles.burst(mx, my, 16, speed=(120, 330),
                             life=(0.2, 0.6), size=(2, 6),
                             colors=(P["fire_bright"], P["fire_light"],
                                     P["magma"]),
                             spread=math.pi, direction=-math.pi / 2,
                             gravity=520.0, drag=1.1,
                             shape="ember", additive=True)
        self.particles.burst(mx, my, 8, speed=(70, 220),
                             life=(0.3, 0.8), size=(3, 6),
                             colors=(P["smoke"], P["ash"], P["dust"]),
                             spread=math.pi, direction=-math.pi / 2,
                             gravity=380.0, drag=1.4,
                             shape="debris", rotation_speed=(-16, 16),
                             layer="back")
        if shake_allowed():
            _feel_shake(7.5, 0.2)
        _feel_hit_stop(0.035)

    # ------------------------------------------------------------------
    # BASIC ATTACK PROJECTILE
    # ------------------------------------------------------------------
    def spawn_fire_orb(self, x, y, aim=None):
        """Lepaskan bola api dari ujung greatsword ke target."""
        grip, tip = sword_points(self.hero, x, y)
        tgt = getattr(self.hero, "target", None)
        if tgt is None or not getattr(tgt, "alive", False):
            tgt = None
        if aim is None:
            aim = target_point(self.hero, x, y)
        self.particles.burst(
            tip[0], tip[1], 8, speed=(80, 220), life=(0.14, 0.36),
            size=(2, 4), colors=(P["fire_hot"], P["fire_bright"]),
            spread=1.5,
            direction=math.atan2(aim[1] - tip[1], aim[0] - tip[0]),
            drag=3.0, shape="ember", additive=True)
        return self.projectiles.spawn(
            tip[0], tip[1], aim[0], aim[1],
            speed=ORB_SPEED, damage=0, target=tgt, radius=8.0,
            kind="fire", seed=int(self.frames),
            on_impact=lambda p: self.on_impact(
                p.hit_pos.x if p.hit_pos else p.x,
                p.hit_pos.y if p.hit_pos else p.y,
                math.atan2(p.velocity.y, p.velocity.x), 1.2, False))

    # ------------------------------------------------------------------
    # IMPACT / HURT / DEATH
    # ------------------------------------------------------------------
    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="fire"):
        """Benturan mengenai target: flash, spark, debris, shake, hit-stop."""
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind=kind))
        pw = min(2.0, max(0.35, float(power)))

        n = int(11 + 9 * pw) + (6 if crit else 0)
        self.particles.burst(
            x, y, n, speed=(130, 340 + 110 * pw), life=(0.14, 0.42),
            size=(2, 5), colors=(P["fire_hot"], P["fire_bright"],
                                 P["fire_light"]),
            spread=2.3, direction=angle, drag=3.6, shape="streak",
            additive=True)
        self.particles.burst(
            x, y, int(6 + 4 * pw) + (4 if crit else 0),
            speed=(70, 230), life=(0.28, 0.72), size=(2, 5),
            colors=(P["ember"], P["fire_mid"], P["magma"]),
            gravity=520.0, drag=1.1, shape="ember", additive=True,
            rotation_speed=(-16, 16))
        self.particles.burst(
            x, y + 4, 5, speed=(20, 90), life=(0.3, 0.85), size=(3, 7),
            colors=(P["smoke"], P["ash"]),
            gravity=-40.0, drag=1.5, shape="smoke", layer="back")
        if crit:
            self.particles.burst(
                x, y, 9, speed=(190, 390), life=(0.22, 0.5), size=(2, 4),
                colors=(P["gold_hot"], P["gold"], P["fire_hot"]),
                spread=math.tau, gravity=140.0, drag=2.0,
                shape="spark", additive=True)

        if shake_allowed():
            _feel_shake(4.8 + 3.6 * pw + (3.0 if crit else 0.0),
                        0.17 + 0.08 * pw)
        # HIT STOP dalam jendela 0.03-0.08 detik
        _feel_hit_stop(0.038 + 0.02 * min(1.5, pw) + (0.015 if crit else 0.0))

    def on_hurt(self, amount=1.0):
        """Ignis terkena serangan: flash + percikan bara + asap armor."""
        self.hit_flash = 0.16
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        self.particles.burst(
            hx, hy - 10, 8, speed=(90, 220), life=(0.14, 0.34), size=(2, 4),
            colors=(P["fire_bright"], P["gold_hot"], P["fire_light"]),
            drag=3.0, shape="streak", additive=True)
        self.particles.burst(
            hx, hy + 6, 5, speed=(30, 100), life=(0.24, 0.55), size=(2, 5),
            colors=(P["smoke"], P["ash"]), gravity=220.0, drag=2.0,
            shape="dust", layer="back")

    def _death_burst(self, x, y):
        """Kematian: armor pecah + kolom asap + bara padam."""
        self.particles.burst(x, y - 12, 26, speed=(70, 280),
                             life=(0.4, 1.1), size=(2, 6),
                             colors=(P["armor_light"], P["fire_mid"],
                                     P["ember"]),
                             spread=math.tau, gravity=460.0, drag=0.9,
                             shape="debris", rotation_speed=(-20, 20))
        self.particles.burst(x, y - 8, 12, speed=(20, 90),
                             life=(0.7, 1.5), size=(5, 10),
                             colors=(P["smoke"], P["ash"]),
                             spread=math.tau, gravity=-55.0, drag=1.0,
                             shape="smoke", layer="back")
        if shake_allowed():
            _feel_shake(11.0, 0.32)
        _feel_hit_stop(0.055)

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def _watch_engine_events(self, x, y):
        """Sinkronkan state debug + deteksi hurt/death dari engine."""
        skill = getattr(self.hero, "active_skill", None)
        if skill:
            self.state = "SPECIAL" if skill == "r" else "SKILL"
        else:
            self.state = getattr(self.hero, "_ign_state", "IDLE")
        self.anim_phase = getattr(self.hero, "_ign_attack_phase", "NONE")

        hp = getattr(self.hero, "hp", None)
        if hp is not None:
            if self._last_hp is not None and hp < self._last_hp:
                self.on_hurt(0.8)
            self._last_hp = hp

        if not getattr(self.hero, "alive", True) and not self._death_done:
            self._death_done = True
            self._death_burst(x, y)

    def update(self, dt, x, y):
        self.time += dt
        self.frames += 1
        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)
        self.particles.update(dt)
        for imp in self.impacts:
            imp.update(dt)
        for sk in self.skills:
            sk.update(dt)
        self.projectiles.update(dt)

        self._watch_engine_events(x, y)

        action, phase, ap = pose_of(self.hero)
        facing = 1 if getattr(self.hero, "direction", 1) >= 0 else -1

        # -- swing trail sampling dari posisi ujung bilah yang SEBENARNYA
        if action in ("attack", "cast", "skill"):
            if not self._swing_seen:
                self._swing_seen = True
                self.on_swing_start(x, y, facing)
            grip, tip = sword_points(self.hero, x, y)
            self.trail.push(tip[0], tip[1], facing)
            if action == "attack":
                if ap and (ATTACK_IMPACT_FRAME <= ap <=
                           ATTACK_IMPACT_FRAME + 0.05) \
                        and not self._impact_frame_seen:
                    self._impact_frame_seen = True
                    self.on_swing_impact_frame(x, y, facing)
                elif self._impact_frame_seen and ap > 0.70:
                    self._impact_frame_seen = False
            if self.trail.width_boost > 1.0:
                self.trail.width_boost = max(
                    1.0, self.trail.width_boost - dt * 2.2)
        else:
            if self._swing_seen:
                self._swing_seen = False
                self.on_swing_end()
            self.trail.reset()

        # Bara ambient di sekitar armor (dibatasi ketat, hemat FPS).
        # Hanya selama unit HIDUP: begitu mati emitter berhenti sehingga
        # tidak ada satu pun efek yang hidup tanpa batas.
        self._visible = max(0.0, self._visible - dt)
        self._ember_clock += dt
        if (self._visible > 0.0 and getattr(self.hero, "alive", True)
                and self._ember_clock >= 0.09):
            self._ember_clock = 0.0
            a = random.uniform(0, math.tau)
            r = 14 + random.random() * 14
            self.particles.burst(
                x + math.cos(a) * r, y - 6 + math.sin(a) * 12, 1,
                speed=(6, 26), life=(0.35, 0.8), size=(1, 2),
                colors=(P["ember"], P["fire_light"], P["fire_bright"]),
                spread=0.9, direction=-math.pi / 2, gravity=-45.0,
                drag=1.1, shape="ember", additive=True)

        # cast charge: spiral bara di mulut helm
        if action == "cast":
            mp = maw_point(self.hero, x, y)
            if self.frames % 3 == 0:
                a = self.time * 8.0
                self.particles.burst(
                    mp[0] + math.cos(a) * 12, mp[1] + math.sin(a) * 8, 1,
                    speed=(10, 34), life=(0.18, 0.4), size=(1, 3),
                    colors=(P["fire_bright"], P["fire_hot"]),
                    direction=a + math.pi, spread=0.8, drag=2.2,
                    shape="ember", additive=True)

        self.impacts = [i for i in self.impacts if i.age < i.life]
        self.skills = [s for s in self.skills if not s.done]

    # ------------------------------------------------------------------
    # DRAW
    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        """GROUND FX + BACK PARTICLES (di bawah sprite)."""
        self._visible = 0.25
        self.particles.draw(surface, "back")
        for sk in self.skills:
            sk.draw_ground(surface)
        skill = getattr(self.hero, "active_skill", None)
        if skill:
            pulse = math.sin(self.time * 6.0) * 0.25 + 0.75
            r = int(WORLD_RADIUS.get(skill, 60) * pulse * 0.45)
            _blit_faded(surface,
                        ellipse_ring_surface(r, int(r * 0.4), 2,
                                             (*P["fire_bright"], 120)),
                        float(getattr(self.hero, "x", 0)),
                        float(getattr(self.hero, "y", 0)) + 34,
                        int(120 * pulse), additive=True)

    def draw_front(self, surface, x, y):
        """ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES -> SKILL -> IMPACT."""
        self.trail.draw(surface, 175, additive=True)
        self.projectiles.draw(surface)
        self.particles.draw(surface, "front")
        for sk in self.skills:
            sk.draw_front(surface)
        for imp in self.impacts:
            imp.draw(surface)
        if self.hit_flash > 0.0:
            k = self.hit_flash / 0.16
            _blit_faded(surface, glow_surface(34, P["fire_white"], 0.35),
                        x, y - 16, int(90 * k), additive=True)

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
    except Exception:                          # pragma: no cover
        return None


def draw_debug_overlay(surface, director):
    """Overlay debug: hitbox, hurtbox, attack range, projectile collision,
    animation state/frame, FPS, particle count, skill state, attack timer."""
    h = director.hero
    x = float(getattr(h, "x", 0.0))
    y = float(getattr(h, "y", 0.0))
    f = 1 if getattr(h, "direction", 1) >= 0 else -1
    r = max(8, int(getattr(h, "radius", 16)))

    # hurtbox
    pygame.draw.rect(surface, (80, 170, 255),
                     pygame.Rect(int(x) - r, int(y) - r - 10, r * 2, r * 2), 1)
    # attack range
    rng = max(20, int(getattr(h, "range", 200) * 0.7))
    pygame.draw.line(surface, (255, 210, 60), (int(x), int(y)),
                     (int(x + rng * f), int(y)), 1)
    pygame.draw.rect(surface, (255, 210, 60),
                     pygame.Rect(int(x + rng * f) - 5, int(y) - 7, 10, 14), 1)
    # hitbox saat jendela hit aktif
    if getattr(h, "_ign_hit_active", False):
        reach = int(rng)
        top = int(y - 48)
        left = int(x) if f > 0 else int(x) - reach
        hb = pygame.Rect(left, top, max(8, reach), max(10, 86))
        pygame.draw.rect(surface, (255, 70, 70), hb, 2)
    # projectile collision
    director.projectiles.draw_debug(surface)

    dtv = float(getattr(h, "_ign_dt", 1.0 / 60.0) or 1.0 / 60.0)
    inst = 1.0 / dtv if dtv > 0 else 60.0
    fps = getattr(director, "_fps", 60.0)
    fps = fps + (inst - fps) * 0.1
    director._fps = fps
    lines = [
        f"IGNIS {director.state} {director.anim_phase}",
        f"frame {director.frames} t={director.time:.2f} "
        f"atk={float(getattr(h, '_ign_attack_progress', 0.0)):.2f}",
        f"particles={director.particles.count()} "
        f"proj={director.projectiles.count()}",
        f"skills={len(director.skills)} impacts={len(director.impacts)} "
        f"fps={fps:.0f}",
    ]
    font = _debug_font()
    if font is None:
        return
    px, py = int(x) - 84, int(y) + 38
    for i, line in enumerate(lines):
        surface.blit(font.render(line, True, (255, 226, 190)),
                     (px, py + i * 14))


# ============================================================================
# 13.  REGISTRY + API MODUL
# ============================================================================

_DIRECTORS = []


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Ignis Drachorn."""
    _sync_palette()
    d = getattr(hero, "_ign_fx", None)
    if d is None:
        d = IgnisFXDirector(hero)
        try:
            hero._ign_fx = d
        except Exception:                      # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:
            _release(_DIRECTORS.pop(0))
    return d


def _release(director):
    try:
        if director.hero is not None:
            director.hero._ign_fx = None
            director.hero._ign_live_fx = False
    except Exception:                          # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit (rendering pipeline)."""
    if not IGNIS_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
        hero._ign_live_fx = True
    except Exception:                          # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not getattr(hero, "_ign_live_fx", False):
        return False
    d = getattr(hero, "_ign_fx", None)
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
    """Bersihkan seluruh state FX Ignis (ganti level / keluar match)."""
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()
    if _feel is not None:
        try:
            _feel.reset()
        except Exception:                      # pragma: no cover
            pass


def total_particles():
    """Jumlah partikel Ignis yang hidup (dipakai HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def total_projectiles():
    return sum(d.projectiles.count() for d in _DIRECTORS)


def stats():
    try:
        return _feel.stats()
    except Exception:                          # pragma: no cover
        return {"hitstop_frames": 0, "hitstop_total": 0, "shake": 0.0}


def projectiles_for(hero):
    """Daftar proyektil milik unit (untuk debug renderer)."""
    d = getattr(hero, "_ign_fx", None)
    if d is None:
        return []
    return d.projectiles.items


# --- hook yang dipanggil heroes/__init__.py --------------------------------

def draw_ground_layer(surface, hero, x, y):
    if not IGNIS_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_ign_fx", None)
    if d is not None:
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    if not IGNIS_FX_ENABLED:
        return
    d = director_for(hero)
    d.draw_front(surface, x, y)
    if DEBUG_CHARACTER:
        draw_debug_overlay(surface, d)


# --- hook yang dipanggil bosses/base_boss.py -------------------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Greatsword mendarat: paket impact + shake + hit-stop lengkap."""
    if not IGNIS_FX_ENABLED or hero is None or target is None:
        return
    try:
        power = 0.9 + min(1.6, float(damage) / 90.0)
    except (TypeError, ValueError):
        power = 1.0
    tx = float(getattr(target, "x", getattr(hero, "x", 0.0)))
    ty = float(getattr(target, "y", getattr(hero, "y", 0.0))) - 6.0
    ang = math.atan2(ty - float(getattr(hero, "y", 0.0)),
                     tx - float(getattr(hero, "x", 0.0)))
    director_for(hero).on_impact(tx, ty, ang, power, bool(crit))


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False,
                             kind="fire"):
    """Bola api / skill mengenai target: paket impact lengkap."""
    if not IGNIS_FX_ENABLED or hero is None:
        return
    try:
        power = 0.8 + min(1.6, float(damage) / 50.0)
    except (TypeError, ValueError):
        power = 1.0
    director_for(hero).on_impact(float(x), float(y), angle, power,
                                 bool(crit), kind=kind)


def notify_skill_cast(hero, skill):
    """Skill mulai di-cast: SkillFX + guncangan (dan R: hujan meteor)."""
    if not IGNIS_FX_ENABLED or hero is None or skill not in SKILL_TOTAL:
        return
    director_for(hero).on_cast(float(getattr(hero, "x", 0.0)),
                               float(getattr(hero, "y", 0.0)), skill)


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """FX area skill pada titik (x, y): SkillFX + paket impact.

    AI memanggil ``notify_skill_cast`` lalu ``notify_skill_impact`` pada
    tick yang sama; SkillFX yang barusan dibuat cast di-update di tempat
    (aim/radius final) supaya efek tidak digambar dobel.
    """
    if not IGNIS_FX_ENABLED or hero is None:
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
        fx.angle = math.atan2(fx.aim[1] - fx.y, fx.aim[0] - fx.x)
        fx.facing = 1 if fx.aim[0] >= fx.x else -1
        if radius:
            fx.radius = float(radius)
    d.on_impact(float(x), float(y), 0.0,
                2.1 if skill == "r" else 1.4, skill == "r")


def notify_projectile_cast(hero, x, y):
    """Spawn bola api dari ujung greatsword ke target (basic attack).

    Renderer memanggil ini saat frame cast aktif dan lapisan hidup sudah
    mengambil alih proyektil; menggantikan ``_spawn_fire_projectile``.
    """
    if not IGNIS_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    d.spawn_fire_orb(x, y, target_point(hero, x, y))


def notify_hurt(hero, amount=1.0):
    if not IGNIS_FX_ENABLED or hero is None:
        return
    director_for(hero).on_hurt(amount)


def _feel_shake(strength, duration):
    try:
        _feel.shake(strength, duration)
    except Exception:                          # pragma: no cover
        pass


def _feel_hit_stop(seconds):
    try:
        _feel.hit_stop(seconds)
    except Exception:                          # pragma: no cover
        pass
