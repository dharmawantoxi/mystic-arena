# ============================================================================
# heroes/vokrahn_fx.py
# ----------------------------------------------------------------------------
# VOKRAHN — THE HARBINGER OF CHAOS  ·  LAPISAN TEMPUR HIDUP (v3)
#
# Rangka kerja ini adalah pasangan dari renderer ``bosses/level4.py ::
# _NS_vokrahn``.  Pembagian tugasnya tegas:
#
#   renderer  -> SATU-SATUNYA pemilik geometri badan & pedang (rig kuda +
#                ksatria, palet, pose, controller animasi, ARK pedang,
#                telegraph fallback)
#   modul ini -> SEMUA yang hidup di RUANG LAYAR skala 1:1 — swing trail,
#                particle system, proyektil (Chaos Bolt & Chaos Brand),
#                skill FX q/w/e/r, impact FX, afterimage, overlay debug
#   combat_feel -> bus global hit-stop & screen shake (dipakai bersama)
#
# Kenapa dipisah?  Di lane hero, sprite badan di-*cache* lalu
# ``smoothscale``-kan.  Efek apa pun yang digambar ke canvas badan ikut
# BEKU dan ikut MENYUSUT.  Dengan memisahkan lapisan hidup ke ruang layar,
# trail/partikel/proyektil selalu 60 fps sejati dan selalu setajam layar.
#
# Modul ini TIDAK pernah menghitung ulang pose.  Ia MEMBACA
# ``_NS_vokrahn.sword_geometry()`` / ``_sword_arc()`` / ``_vok_state``
# lewat jembatan malas ``_renderer()``, jadi pedang dan trail-nya
# mustahil berbeda satu frame pun.
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

#: Overlay debug (hitbox, hurtbox, state, FPS, jumlah partikel, ...).
DEBUG_CHARACTER = False

#: Master switch lapisan hidup.  False -> renderer memakai fallback canvas.
VOKRAHN_FX_ENABLED = True

#: Cap keras — tidak ada satu pun sistem yang boleh tumbuh tanpa batas.
MAX_PARTICLES = 120
MAX_PROJECTILES = 13
TRAIL_SAMPLES = 6
MAX_IMPACTS = 5
MAX_SKILLS = 3
MAX_AFTERIMAGES = 7

FIXED_DT = 1.0 / 60.0

#: Kecepatan proyektil (px dunia / detik).
BOLT_SPEED = 780.0           # Q — Chaos Bolt (cepuk kekacauan meluncur)
BRAND_SPEED = 270.0          # R — Chaos Brand (bara berat Phantasm)

#: Durasi pose skill dalam FRAME — HARUS sama dengan
#: ``base_boss._cast_vokrahn_*`` (active_skill_timer) dan
#: ``_NS_vokrahn.SKILL_DUR``.
SKILL_DUR = {"q": 50, "w": 60, "e": 50, "r": 80}

#: Durasi lifecycle FX (detik) — sedikit lebih panjang dari pose supaya
#: tahap AFTER (asap/bara sisa) sempat memudar dengan wajar.
SKILL_TOTAL = {"q": 1.25, "w": 1.55, "e": 1.35, "r": 2.10}

#: Radius efek di RUANG DUNIA — sama persis dengan radius damage AI:
#: ``_cast_vokrahn_w`` 220, ``_cast_vokrahn_r`` 220, Q bidikan 250,
#: E zona benturan dash 150.  Dikunci oleh tes regresi.
WORLD_RADIUS = {"q": 250.0, "w": 220.0, "e": 150.0, "r": 220.0}

#: Jumlah entitas yang dipanggil skill.
PHANTOM_COUNT = 2            # R — Phantasm (ilusi ksatria kekacauan)

#: Jarak dunia (px) di bawahnya tebasan greatsword dianggap melee.
#: Vokrahn murni melee (range 55 di boss_data) — angka ini dipakai
#: ``_NS_vokrahn`` dan hook benturan ``base_boss`` agar animasi dan
#: damage tidak pernah beda pendapat.
MELEE_REACH = 96.0

#: Fase serangan (fraksi 0..1 dari durasi serangan).  Nama fase ini
#: dipakai renderer, lapisan hidup, dan overlay debug — satu kosakata.
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.12),
    ("WINDUP",       0.12, 0.30),
    ("SWING",        0.30, 0.50),
    ("IMPACT",       0.50, 0.62),
    ("FOLLOW",       0.62, 0.82),
    ("RECOVERY",     0.82, 1.00),
)

#: Jendela hit aktif + frame impact.  ``0.52`` dipakai renderer (puncak
#: ayunan SWORD_ARC) DAN lapisan hidup (momen impact) — satu angka.
ATTACK_ACTIVE_WINDOW = (0.38, 0.62)
ATTACK_IMPACT_FRAME = 0.52

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

#: ARK pedang — IDENTIK dengan ``_NS_vokrahn.SWORD_ARC`` (tabel cadangan
#: kalau renderer gagal diimpor; tes mengunci keduanya sama).
#:
#: ``(t0, t1, phi0, phi1, ease)`` — ``phi`` = sudut pedang dari sumbu
#: DEPAN (+x arah facing, orientasi matematis y-atas).  Loop tertutup:
#: phi(0) == phi(1) dan langkah maksimum < 0.30 rad per 1/200 progres,
#: jadi bilah tidak pernah teleport.
SWORD_ARC = (
    (0.00, 0.12,  0.96,  2.18, "out"),    # ANGKAT: jagaan -> atas-belakang
    (0.12, 0.30,  2.18,  2.88, "io"),     # WIND-UP: horizontal belakang
    (0.30, 0.50,  2.88, -1.31, "oc"),     # SWING: sapuan overhead ke depan
    (0.50, 0.62, -1.31, -1.05, "hold"),   # IMPACT: pendaran + recoil
    (0.62, 0.82, -1.05, -0.44, "io"),     # FOLLOW THROUGH
    (0.82, 1.00, -0.44,  0.96, "io"),     # RECOVERY: kembali ke jagaan
)

#: Setengah panjang bilah & offset grip (px LAYAR, render_scale 1) —
#: cadangan dari rig renderer (rig 48 px x SCALE 0.62).
_SWORD_HALF_FALLBACK = 29.8
_GRIP_FALLBACK = (26.0, -8.7)


# ============================================================================
# 2.  PALETTE — Chaos Knight (disinkronkan dari renderer)
# ============================================================================

VOKRAHN_PALETTE = {
    # Besi hitam 6-band (armor ksatria)
    "arm_darkest":     (8,   5,  10),
    "arm_dark":        (26,  18,  26),
    "arm_mid":         (54,  38,  46),
    "arm_light":       (92,  68,  76),
    "arm_high":        (148, 116, 122),
    "arm_shine":       (205, 178, 178),

    # Crimson kekacauan 6-band (trim / rune / energi)
    "chaos_darkest":   (30,   6,   8),
    "chaos_dark":      (85,  14,  14),
    "chaos_mid":       (160,  24,  20),
    "chaos_bright":    (225,  50,  34),
    "chaos_hot":       (255,  95,  55),
    "chaos_glow":      (255, 150, 105),

    # Api 7-band (bilah pedang / efek)
    "fire_darkest":    (60,  12,   6),
    "fire_dark":       (140, 28,  10),
    "fire_mid":        (220,  70,  16),
    "fire_bright":     (255, 125,  32),
    "fire_hot":        (255, 178,  62),
    "fire_glow":       (255, 222, 132),
    "fire_white":      (255, 250, 212),

    # Jubah compang-camping (kain merah gelap)
    "cape_darkest":    (20,   6,   9),
    "cape_dark":       (54,  13,  16),
    "cape_mid":        (100,  24,  27),
    "cape_light":      (155,  44,  38),

    # Kuda jelaga 5-band
    "horse_darkest":   (6,   6,   9),
    "horse_dark":      (22,  20,  24),
    "horse_mid":       (48,  43,  48),
    "horse_light":     (84,  76,  80),
    "horse_high":      (128, 118, 118),

    # surai / ekor api 5-band
    "mane_darkest":    (32,   6,   4),
    "mane_dark":       (90,  16,  10),
    "mane_mid":        (160,  32,  16),
    "mane_bright":     (225,  58,  26),
    "mane_hot":        (255, 115,  52),

    # Logam & emas
    "metal_darkest":   (14,  12,  17),
    "metal_dark":      (38,  35,  44),
    "metal_mid":       (78,  75,  88),
    "metal_edge":      (104, 100, 116),
    "metal_light":     (134, 132, 148),
    "metal_shine":     (190, 188, 205),
    "gold_dark":       (88,  57,  16),
    "gold_mid":        (168, 122,  36),
    "gold_light":      (228, 182,  76),

    # Mata menyala
    "eye_dark":        (64,   6,   6),
    "eye_bright":      (255,  64,  32),
    "eye_hot":         (255, 182, 132),

    # Asap ungu-dingin (Phantasm)
    "smoke_dark":      (20,  10,  26),
    "smoke_mid":       (58,  34,  80),
    "smoke_light":     (118,  84, 158),
    "smoke_glow":      (192, 152, 240),

    # Turunan FX
    "ember":           (255, 160,  55),
    "ash":             (100,  88,  88),
    "dust":            (130, 114,  98),
    "shadow_deep":     (3,   2,   4),

    # Kunci kontrak 9 (dipakai tes regresi)
    "outline":         (8,   5,  10),
    "shadow":          (3,   2,   4),
    "dark":            (26,  18,  26),
    "body":            (54,  38,  46),
    "mid":             (92,  68,  76),
    "light":           (148, 116, 122),
    "highlight":       (205, 178, 178),
    "weapon":          (255, 125,  32),
    "fx":              (225,  50,  34),
}

#: Alias kerja — sinkron dengan renderer saat modul dipakai pertama kali.
P = dict(VOKRAHN_PALETTE)

#: Kunci FX -> kunci palet renderer.  Kalau renderer mengubah warna,
#: lapisan hidup ikut berubah TANPA edit ganda.
#: PALET RENDERER memakai nama ``red_*`` untuk keluarga crimson kekacauan;
#: lapisan hidup memakainya sebagai ``chaos_*`` — dipetakan di sini supaya
#: satu perubahan warna di renderer otomatis ikut ke seluruh FX.
_PALETTE_SYNC = {
    "arm_darkest": "arm_darkest", "arm_dark": "arm_dark",
    "arm_mid": "arm_mid", "arm_light": "arm_light",
    "arm_high": "arm_high", "arm_shine": "arm_shine",
    "chaos_darkest": "red_darkest", "chaos_dark": "red_dark",
    "chaos_mid": "red_mid", "chaos_bright": "red_bright",
    "chaos_hot": "red_hot", "chaos_glow": "red_glow",
    "fire_darkest": "fire_darkest", "fire_dark": "fire_dark",
    "fire_mid": "fire_mid", "fire_bright": "fire_bright",
    "fire_hot": "fire_hot", "fire_glow": "fire_glow",
    "fire_white": "fire_white",
    "cape_darkest": "cape_darkest", "cape_dark": "cape_dark",
    "cape_mid": "cape_mid", "cape_light": "cape_light",
    "horse_darkest": "horse_darkest", "horse_dark": "horse_dark",
    "horse_mid": "horse_mid", "horse_light": "horse_light",
    "horse_high": "horse_high",
    "mane_darkest": "mane_darkest", "mane_dark": "mane_dark",
    "mane_mid": "mane_mid", "mane_bright": "mane_bright",
    "mane_hot": "mane_hot",
    "metal_darkest": "metal_darkest", "metal_dark": "metal_dark",
    "metal_mid": "metal_mid", "metal_edge": "metal_edge",
    "metal_light": "metal_light", "metal_shine": "metal_shine",
    "gold_dark": "gold_dark", "gold_mid": "gold_mid",
    "gold_light": "gold_light",
    "eye_dark": "eye_dark", "eye_bright": "eye_bright",
    "eye_hot": "eye_hot",
    "shadow_deep": "shadow_deep",
    # kunci kontrak 9 (dipetakan ke warna asli renderer)
    "outline": "arm_darkest", "shadow": "shadow_deep",
    "dark": "arm_dark", "body": "arm_mid", "mid": "arm_light",
    "light": "arm_high", "highlight": "arm_shine",
    "weapon": "fire_bright", "fx": "red_bright",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Tarik warna dari ``_NS_vokrahn.PALETTE`` sekali saja (idempotent)."""
    global _PALETTE_SYNCED
    if _PALETTE_SYNCED:
        return
    R = _renderer()
    if R is None:
        _PALETTE_SYNCED = True
        return
    src = getattr(R, "PALETTE", None)
    if isinstance(src, dict):
        for dst_key, src_key in _PALETTE_SYNC.items():
            col = src.get(src_key)
            if col and len(col) >= 3:
                P[dst_key] = (int(col[0]), int(col[1]), int(col[2]))
        # turunan
        P["ember"] = _mix(P["fire_bright"], P["fire_hot"], 0.45)
        P["ash"] = _mix(P["cape_dark"], P["dust"], 0.55)
    _PALETTE_SYNCED = True


# ============================================================================
# 3.  JEMBATAN KE RENDERER — satu sumber geometri & pose
# ============================================================================

_RENDERER = None          # None = belum dicari, False = tidak ada


def _renderer():
    """``_NS_vokrahn`` atau None.  Diimpor malas: modul boss itu besar."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level4 import _NS_vokrahn as V
            _RENDERER = V
        except Exception:                        # pragma: no cover
            _RENDERER = False
    return _RENDERER or None


def _ease(kind, t):
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    if kind == "out":
        return 1.0 - (1.0 - t) * (1.0 - t)
    if kind == "oc":                             # out-cubic (cepat di awal)
        return 1.0 - (1.0 - t) ** 3
    if kind == "in":
        return t * t
    if kind == "hold":
        return math.sin(t * math.pi * 0.5)
    return t * t * (3.0 - 2.0 * t)               # in-out (smoothstep)


def _fallback_lift(progress):
    """Kenaikan grip (0..1) — IDENTIK dengan ``_NS_vokrahn._sword_lift``."""
    p = max(0.0, min(1.0, float(progress)))
    E = _ease
    if p < 0.12:
        return 0.5 * E("out", p / 0.12)
    if p < 0.30:
        return 0.5 + 0.4 * E("io", (p - 0.12) / 0.18)
    if p < 0.50:
        return 0.9 - 0.9 * E("oc", (p - 0.30) / 0.20)
    if p < 0.62:
        return -0.12 * E("hold", (p - 0.50) / 0.12)
    if p < 0.82:
        return -0.12 + 0.17 * E("io", (p - 0.62) / 0.20)
    return 0.05 * (1.0 - E("io", (p - 0.82) / 0.18))


def _fallback_arc(progress):
    p = max(0.0, min(1.0, float(progress)))
    for t0, t1, a0, a1, kind in SWORD_ARC:
        if t0 <= p < t1 or (p >= 1.0 and t1 >= 1.0):
            e = _ease(kind, (p - t0) / max(0.0001, t1 - t0))
            return a0 + (a1 - a0) * e, _fallback_lift(p)
    return SWORD_ARC[0][2], 0.0


def sword_arc(progress):
    """``(phi, lift)`` ARK pedang — SATU sumber kebenaran.

    Membaca ``_NS_vokrahn._sword_arc`` (fungsi yang sama yang dipakai
    canvas untuk menggambar pedang); kalau renderer tidak ada, memakai
    tabel fallback yang identik di atas.
    """
    R = _renderer()
    fn = getattr(R, "_sword_arc", None) if R is not None else None
    if fn is not None:
        try:
            return fn(progress)
        except Exception:                        # pragma: no cover
            pass
    return _fallback_arc(progress)


def attack_phase(progress):
    """Nama fase serangan untuk ``progress`` 0..1."""
    p = max(0.0, min(1.0, float(progress)))
    for name, a, b in ATTACK_PHASES:
        if a <= p < b:
            return name
    return "RECOVERY"


def skill_phase(t):
    """Nama fase lifecycle skill untuk fraksi umur ``t`` 0..1."""
    t = max(0.0, min(1.0, float(t)))
    for name, a, b in SKILL_PHASES:
        if a <= t < b:
            return name
    return "AFTER"


def _fallback_pose(boss):
    """``(action, phase, ap)`` tanpa renderer: baca atribut yang ada."""
    skill = getattr(boss, "active_skill", None)
    action = getattr(boss, "_vok_pose_action", None)
    if action is None:
        action = {"q": "q_cast", "w": "w_cast", "e": "e_cast",
                  "r": "r_cast"}.get(skill)
    if action is None:
        action = ("swing" if getattr(boss, "_vok_attack_active", False)
                  else "idle")
    phase = float(getattr(boss, "pulse", 0.0) or 0.0)
    ap = float(getattr(boss, "_vok_attack_progress", 0.0) or 0.0)
    return action, phase, ap


def pose_of(boss):
    """Pose badan yang dipakai renderer: ``(action, phase, ap)``."""
    action = getattr(boss, "_vok_pose_action", None)
    if action is None:
        return _fallback_pose(boss)
    phase = float(getattr(boss, "_vok_phase",
                          getattr(boss, "pulse", 0.0)))
    ap = float(getattr(boss, "_vok_attack_progress", 0.0) or 0.0)
    return action, phase, ap


def render_scale(boss):
    """Skala hero-lane (canvas dikali saat blit).  Boss di layar = 1."""
    try:
        s = float(getattr(boss, "_render_scale", 1.0) or 1.0)
    except (TypeError, ValueError):
        s = 1.0
    return s if s > 0.01 else 1.0


def body_scale(boss):
    """Skala badan relatif jangkar — dipakai semua titik FX."""
    return render_scale(boss)


def screen_point(boss, x, y, local):
    """Titik layar dari offset lokal (sudah termasuk skala hero-lane)."""
    k = body_scale(boss)
    return (x + local[0] * k, y + local[1] * k)


def sword_points(boss, x, y):
    """``(grip, tip_atas, ujung_belakang)`` pedang di RUANG LAYAR.

    Memakai ``_NS_vokrahn.sword_geometry`` — fungsi yang sama yang
    dipakai canvas untuk menggambar pedang, jadi trail tidak mungkin
    melenceng dari bilahnya.
    """
    action, phase, ap = pose_of(boss)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)
    R = _renderer()
    fn = getattr(R, "sword_geometry", None) if R is not None else None
    if fn is not None:
        try:
            grip, hi, lo, _phi = fn(facing, action, phase, ap)
            return ((x + grip[0] * k, y + grip[1] * k),
                    (x + hi[0] * k, y + hi[1] * k),
                    (x + lo[0] * k, y + lo[1] * k))
        except Exception:                        # pragma: no cover
            pass
    # fallback: hitung sendiri dengan tabel identik
    if action in ("swing", "attack", "melee"):
        phi, lift = sword_arc(ap)
    else:
        phi, lift = 0.96 + 0.06 * math.sin(phase * 0.8), 0.0
    gx = facing * (_GRIP_FALLBACK[0] + 5.0 * lift)
    gy = _GRIP_FALLBACK[1] - 9.0 * lift
    dx = facing * math.cos(phi) * _SWORD_HALF_FALLBACK
    dy = -math.sin(phi) * _SWORD_HALF_FALLBACK
    return ((x + gx * k, y + gy * k),
            (x + (gx + dx) * k, y + (gy + dy) * k),
            (x + (gx - dx * 0.35) * k, y + (gy - dy * 0.35) * k))


def sword_tip(boss, x, y):
    """Titik ujung bilah (ruang layar) — untuk trail & titik lahir bolt."""
    _grip, hi, _lo = sword_points(boss, x, y)
    return hi


def sword_angle(boss, x, y):
    """Sudut bilah (radian, ruang layar) dari grip ke ujung."""
    grip, hi, _lo = sword_points(boss, x, y)
    return math.atan2(hi[1] - grip[1], hi[0] - grip[0])


def launch_point(boss, x, y):
    """Titik lepas Chaos Bolt (ruang layar) — sedikit di depan ujung
    bilah ke arah target."""
    _grip, hi, _lo = sword_points(boss, x, y)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)
    return (hi[0] + facing * 4.0 * k, hi[1])


def target_point(boss, x, y):
    """Titik target serangan dasar di ruang LAYAR (untuk proyektil).

    Lapisan hidup digambar 1:1 di layar, sedangkan posisi unit/target
    sudah berupa koordinat dunia = koordinat layar. Target TIDAK boleh
    dibagi-``_render_scale``: konversi canvas itu hanya berlaku di
    jalur renderer sprite yang di-scale saat di-blit. Tanpa koreksi ini
    proyektil mendarat jauh DI BELAKANG target (FX terlihat nyasar ke
    titik acak di peta).
    """
    tgt = getattr(boss, "target", None)
    if tgt is not None and getattr(tgt, "alive", False):
        bx = float(getattr(boss, "x", x))
        by = float(getattr(boss, "y", y))
        return (x + (float(getattr(tgt, "x", bx)) - bx),
                y + (float(getattr(tgt, "y", by)) - by) - 6.0)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    return (x + facing * 180.0, y - 10.0)


def ring_radius(boss, world_px):
    """Radius dunia -> radius layar (lapisan hidup 1:1)."""
    return float(world_px)


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
# 4.  HELPER GAMBAR + CACHE SURFACE
# ============================================================================

_CACHE = {}
_SCRATCH_POOL = []
_OPAQUE_POOL = []

#: cap entri cache; dibersihkan total kalau lewat.
_CACHE_CAP = 210


def _clamp_color(color):
    if type(color) is tuple and len(color) >= 3:
        _r, _g, _b = color[0], color[1], color[2]
        if (type(_r) is int and type(_g) is int and type(_b) is int
                and 0 <= _r <= 255 and 0 <= _g <= 255 and 0 <= _b <= 255):
            return (_r, _g, _b)
    return tuple(int(max(0, min(255, c))) for c in color[:3])


def _mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _hash01(seed):
    """Hash deterministik kecil -> [0, 1)."""
    v = (int(seed) * 747796405 + 2891336453) & 0xFFFFFFFF
    v = ((v >> ((v >> 28) + 4)) ^ v) * 277803737
    v = (v >> 22) ^ v
    return (v & 0x3FFFFFF) / float(0x3FFFFFF)


def _cache_put(key, surf):
    if key not in _CACHE:
        if len(_CACHE) > _CACHE_CAP:
            _CACHE.clear()
        _CACHE[key] = surf
    return _CACHE[key]


def clear_cache():
    _CACHE.clear()


def cache_size():
    return len(_CACHE)


def _scratch(w, h):
    """Surface sementara dari pool (hindari alokasi tiap frame)."""
    w = max(1, int(w))
    h = max(1, int(h))
    for s in _SCRATCH_POOL:
        if s.get_width() >= w and s.get_height() >= h:
            sub = s.subsurface((0, 0, w, h))
            sub.fill((0, 0, 0, 0))
            return sub
    s = pygame.Surface((max(w, 256), max(h, 256)), pygame.SRCALPHA)
    if len(_SCRATCH_POOL) < 8:
        _SCRATCH_POOL.append(s)
    return s.subsurface((0, 0, w, h))


def _opaque(w, h):
    """Surface HITAM buram dari pool (untuk premultiply alpha)."""
    w = max(1, int(w))
    h = max(1, int(h))
    for s in _OPAQUE_POOL:
        if s.get_width() >= w and s.get_height() >= h:
            sub = s.subsurface((0, 0, w, h))
            sub.fill((0, 0, 0))
            return sub
    s = pygame.Surface((max(w, 256), max(h, 256)))
    if len(_OPAQUE_POOL) < 6:
        _OPAQUE_POOL.append(s)
    return s.subsurface((0, 0, w, h))


def blit_add(surface, src, pos, alpha=255):
    """Blit ADDITIF yang MENGHORMATI alpha per-piksel.

    ``BLEND_RGB_ADD`` mengabaikan kanal alpha sepenuhnya: surface
    ber-gradien yang langsung di-ADD muncul sebagai bidang warna penuh
    bertepi keras (stiker).  Di sini sumber di-*premultiply* dulu —
    di-blit normal ke atas hitam sehingga RGB ikut dikalikan alpha-nya —
    baru hasilnya ditambahkan.  Itu yang membuat cahaya benar-benar
    meluruh ke gelap.
    """
    if src is None:
        return
    w, h = src.get_size()
    if w < 1 or h < 1:
        return
    tmp = _opaque(w, h)
    tmp.blit(src, (0, 0))
    if alpha < 255:
        a = int(max(0, min(255, alpha)))
        tmp.fill((a, a, a, 255), special_flags=pygame.BLEND_RGB_MULT)
    surface.blit(tmp, pos, special_flags=pygame.BLEND_RGB_ADD)


def _blit_faded(surface, surf, cx, cy, alpha=255, additive=False):
    if surf is None or alpha < 2:
        return
    rect = surf.get_rect(center=(int(cx), int(cy)))
    if additive:
        blit_add(surface, surf, rect.topleft, alpha)
        return
    if alpha >= 255:
        surface.blit(surf, rect.topleft)
        return
    # Non-additif: set_alpha langsung, tanpa salinan per partikel.
    surf.set_alpha(int(alpha))
    surface.blit(surf, rect.topleft)
    surf.set_alpha(255)


# -- primitif ber-cache -----------------------------------------------------

def glow_surface(radius, color, power=1.0):
    """Cahaya radial lembut.  Dibangun dari ANNULUS (cincin ber-width),
    bukan tumpukan lingkaran penuh — tumpukan lingkaran membuat alpha
    menumpuk di tengah dan menghasilkan cakram bertepi keras."""
    r = max(2, int(radius))
    col = _clamp_color(color)
    key = ("glow", r, col, round(float(power), 2))
    got = _CACHE.get(key)
    if got is not None:
        return got
    size = r * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    steps = max(4, min(r, 22))
    for i in range(steps, 0, -1):
        t = i / float(steps)
        rr = max(1, int(r * t))
        a = int(255 * ((1.0 - t) ** 1.9) * power)
        if a <= 1:
            continue
        width = max(1, int(r / steps) + 1)
        pygame.draw.circle(surf, (*col, a), (c, c), rr, width)
    pygame.draw.circle(surf, (*col, int(min(255, 235 * power))), (c, c),
                       max(1, int(r * 0.16)))
    return _cache_put(key, surf)


def ring_surface(radius, thickness, color, alpha=255, dashed=0):
    """Cincin (opsional putus-putus) — dipakai shockwave & telegraph."""
    r = max(2, int(radius))
    th = max(1, int(thickness))
    col = _clamp_color(color)
    key = ("ring", r, th, col, int(alpha), int(dashed))
    got = _CACHE.get(key)
    if got is not None:
        return got
    size = r * 2 + th * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    if dashed > 0:
        seg = math.tau / (dashed * 2)
        rect = pygame.Rect(c - r, c - r, r * 2, r * 2)
        for i in range(dashed):
            a0 = i * seg * 2
            pygame.draw.arc(surf, (*col, int(alpha)), rect, a0, a0 + seg, th)
    else:
        pygame.draw.circle(surf, (*col, int(alpha)), (c, c), r, th)
    return _cache_put(key, surf)


def ellipse_ring_surface(rx, ry, thickness, color, alpha=255):
    """Cincin elips (perspektif tanah)."""
    rx = max(2, int(rx))
    ry = max(1, int(ry))
    th = max(1, int(thickness))
    col = _clamp_color(color)
    key = ("ering", rx, ry, th, col, int(alpha))
    got = _CACHE.get(key)
    if got is not None:
        return got
    surf = pygame.Surface((rx * 2 + th * 2 + 4, ry * 2 + th * 2 + 4),
                          pygame.SRCALPHA)
    rect = pygame.Rect(th + 2, th + 2, rx * 2, ry * 2)
    pygame.draw.ellipse(surf, (*col, int(alpha)), rect, th)
    return _cache_put(key, surf)


def ground_pool_surface(rx, color, power=0.35):
    """Genangan tanah elips ber-falloff (bara / kekacauan)."""
    rx = max(3, int(rx))
    col = _clamp_color(color)
    key = ("pool", rx, col, round(float(power), 2))
    got = _CACHE.get(key)
    if got is not None:
        return got
    ry = max(2, int(rx * 0.42))
    surf = pygame.Surface((rx * 2 + 4, ry * 2 + 4), pygame.SRCALPHA)
    steps = max(4, min(rx // 2, 16))
    for i in range(steps, 0, -1):
        t = i / float(steps)
        a = int(210 * ((1.0 - t) ** 1.4) * power) + 6
        rect = pygame.Rect(2 + rx - int(rx * t), 2 + ry - int(ry * t),
                           int(rx * t * 2), int(ry * t * 2))
        if rect.width > 1 and rect.height > 1:
            pygame.draw.ellipse(surf, (*col, min(255, a)), rect)
    return _cache_put(key, surf)


def ember_surface(size, color):
    """Bara kecil chunky (pixel-art): inti keras + halo 1 px."""
    s = max(1, int(size))
    col = _clamp_color(color)
    key = ("ember", s, col)
    got = _CACHE.get(key)
    if got is not None:
        return got
    d = s * 2 + 4
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    c = d // 2
    pygame.draw.circle(surf, (*col, 70), (c, c), s + 2)
    pygame.draw.circle(surf, (*col, 175), (c, c), max(1, s))
    pygame.draw.circle(surf, (*_mix(col, (255, 255, 235), 0.55), 245),
                       (c, c), max(1, s - 1) if s > 1 else 1)
    return _cache_put(key, surf)


def arc_ring_surface(radius, segments, span, thickness, color, alpha=255,
                     squash=1.0, rot=0.0):
    """Cincin runik: potongan busur meruncing (bukan cincin utuh).

    ``squash`` < 1 memipihkan cincin secara vertikal sehingga potongannya
    duduk di BIDANG TANAH alih-alih melayang sebagai lempengan lepas di
    udara — itu bedanya antara "arc rune yang berputar di tanah" dan
    "papan warna yang menempel di layar".  ``rot`` memutar polanya.
    """
    r = max(3, int(radius))
    th = max(1, int(thickness))
    sq = max(0.05, min(1.0, float(squash)))
    ry = max(2, int(r * sq))
    col = _clamp_color(color)
    key = ("arcring", r, ry, int(segments), round(float(span), 2), th, col,
           int(alpha), round(float(rot), 2))
    got = _CACHE.get(key)
    if got is not None:
        return got
    w = r * 2 + th * 2 + 6
    h = ry * 2 + th * 2 + 6
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    rect = pygame.Rect(cx - r, cy - ry, r * 2, ry * 2)
    step = math.tau / max(1, int(segments))
    for i in range(int(segments)):
        a0 = rot + i * step
        pygame.draw.arc(surf, (*col, int(alpha)), rect, a0, a0 + span * step,
                        th)
        pygame.draw.arc(surf, (*_mix(col, (255, 255, 255), 0.4),
                               int(alpha * 0.7)),
                        rect.inflate(-th * 2, -th * 2), a0,
                        a0 + span * step * 0.7, max(1, th - 1))
    return _cache_put(key, surf)


def spike_ring_surface(radius, count, length, color, alpha=255,
                       squash=1.0, rot=0.0):
    """Cincin duri bergerigi (Realm of Chaos) — jelas BUKAN lingkaran
    polos: tiap duri segitiga tajam dengan panjang bervariasi."""
    r = max(4, int(radius))
    ln = max(2, int(length))
    n = max(3, int(count))
    sq = max(0.05, min(1.0, float(squash)))
    ry = max(2, int(r * sq))
    col = _clamp_color(color)
    key = ("spiker", r, ry, ln, n, col, int(alpha), round(float(rot), 2))
    got = _CACHE.get(key)
    if got is not None:
        return got
    w = (r + ln) * 2 + 8
    h = (ry + ln) * 2 + 8
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    for i in range(n):
        a0 = rot + i * math.tau / n
        a1 = a0 + math.tau / n * 0.55
        am = (a0 + a1) * 0.5
        l = ln * (0.7 + _hash01(i * 17 + n) * 0.6)
        p0 = (cx + math.cos(a0) * r, cy + math.sin(a0) * ry)
        p1 = (cx + math.cos(a1) * r, cy + math.sin(a1) * ry)
        pt = (cx + math.cos(am) * (r + l),
              cy + math.sin(am) * (ry + l * sq))
        pygame.draw.polygon(surf, (*col, int(alpha)), [p0, pt, p1])
        pygame.draw.polygon(surf, (*_mix(col, (255, 255, 255), 0.35),
                                   int(alpha * 0.8)),
                            [(p0[0] + (pt[0] - p0[0]) * 0.25,
                              p0[1] + (pt[1] - p0[1]) * 0.25),
                             pt,
                             (p1[0] + (pt[0] - p1[0]) * 0.25,
                              p1[1] + (pt[1] - p1[1]) * 0.25)])
    pygame.draw.circle(surf, (*col, int(alpha * 0.8)), (cx, cy), r, 2)
    return _cache_put(key, surf)


# -- primitif langsung (tanpa cache, bentuknya selalu unik) ------------------

def shard_poly(surface, cx, cy, ang, length, width, color, alpha=255):
    """Serpihan obsidian / baja: belah ketupat meruncing."""
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = -sa, ca
    pts = [(cx + ca * length, cy + sa * length),
           (cx + px * width, cy + py * width),
           (cx - ca * length * 0.7, cy - sa * length * 0.7),
           (cx - px * width, cy - py * width)]
    pygame.draw.polygon(surface, (*_clamp_color(color), int(alpha)), pts)


def flame_poly(surface, cx, cy, h, seed=0, alpha=255, phase=0.0, w=None):
    """Lidah api bergerigi (poligon), bukan lingkaran."""
    h = max(3.0, float(h))
    w = float(w) if w else h * 0.42
    pts = [(cx - w, cy)]
    steps = 6
    for i in range(steps + 1):
        t = i / float(steps)
        wob = (_hash01(seed + i * 13) - 0.5) * w * 0.7
        flick = math.sin(phase * 5.0 + i * 1.3) * w * 0.22
        pts.append((cx - w * (1.0 - t) + wob + flick,
                    cy - h * t * (0.55 + 0.45 * t)))
    for i in range(steps, -1, -1):
        t = i / float(steps)
        wob = (_hash01(seed + 400 + i * 7) - 0.5) * w * 0.7
        flick = math.sin(phase * 5.0 + i * 1.1 + 2.0) * w * 0.22
        pts.append((cx + w * (1.0 - t) + wob + flick,
                    cy - h * t * (0.55 + 0.45 * t)))
    pts.append((cx + w, cy))
    if len(pts) < 3:
        return
    a = int(alpha)
    pygame.draw.polygon(surface, (*P["fire_dark"], int(a * 0.75)), pts)
    inner = [(cx + (px - cx) * 0.62, cy + (py - cy) * 0.72) for px, py in pts]
    pygame.draw.polygon(surface, (*P["fire_bright"], int(a * 0.9)), inner)
    core = [(cx + (px - cx) * 0.3, cy + (py - cy) * 0.5) for px, py in pts]
    pygame.draw.polygon(surface, (*P["fire_glow"], a), core)


def spark_star(surface, cx, cy, size, color, alpha, spikes=4, rot=0.3,
               core=None):
    """Kilat bintang berujung tajam (impact flash)."""
    if size <= 0 or alpha <= 2:
        return
    pts = []
    for i in range(spikes * 2):
        a = rot + i * math.pi / spikes
        r = size if i % 2 == 0 else size * 0.34
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    if len(pts) > 2:
        pygame.draw.polygon(surface, (*_clamp_color(color), int(alpha)), pts)
    if core:
        pygame.draw.circle(surface, (*_clamp_color(core), int(alpha)),
                           (int(cx), int(cy)), max(1, int(size * 0.24)))


def chevron(surface, cx, cy, ang, size, color, alpha, width=3):
    """Tanda panah ">" untuk telegraph arah."""
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = -sa, ca
    tip = (cx + ca * size, cy + sa * size)
    a = (cx - ca * size * 0.35 + px * size * 0.8,
         cy - sa * size * 0.35 + py * size * 0.8)
    b = (cx - ca * size * 0.35 - px * size * 0.8,
         cy - sa * size * 0.35 - py * size * 0.8)
    col = (*_clamp_color(color), int(alpha))
    pygame.draw.lines(surface, col, False, [a, tip, b], max(1, int(width)))


def crack_points(x0, y0, x1, y1, segments=5, dev=6.0, seed=0):
    """Garis retak bergerigi deterministik."""
    pts = [(x0, y0)]
    for i in range(1, segments):
        t = i / float(segments)
        mx = x0 + (x1 - x0) * t
        my = y0 + (y1 - y0) * t
        nx = -(y1 - y0)
        ny = (x1 - x0)
        L = math.hypot(nx, ny) or 1.0
        off = (_hash01(seed * 31 + i) - 0.5) * 2.0 * dev
        pts.append((mx + nx / L * off, my + ny / L * off))
    pts.append((x1, y1))
    return pts


def star_poly_points(cx, cy, radius, points=5, rot=0.0, squash=0.42):
    """Titik bintang n-titik (dipakai Phantasm — 8 titik) — jelas BUKAN
    lingkaran."""
    out = []
    step = math.tau / points
    for i in range(points):
        a = rot + i * step * 2.0
        out.append((cx + math.cos(a) * radius,
                    cy + math.sin(a) * radius * squash))
    return out


def chaos_star_points(cx, cy, radius, spikes=4, rot=0.0, squash=0.42,
                      inner=0.45):
    """Bintang kekacauan bersudut tajam (simbol chaos Vokrahn)."""
    out = []
    n = max(3, int(spikes))
    step = math.tau / n
    for i in range(n * 2):
        a = rot + i * step * 0.5
        r = radius if i % 2 == 0 else radius * inner
        out.append((cx + math.cos(a) * r,
                    cy + math.sin(a) * r * squash))
    return out


def taper_lane(surface, x0, y0, x1, y1, w0, w1, color, alpha):
    """Pita/koridor meruncing (telegraph bidik) — bukan kerucut bulat."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    px, py = -dy / L, dx / L
    pts = [(x0 + px * w0, y0 + py * w0), (x1 + px * w1, y1 + py * w1),
           (x1 - px * w1, y1 - py * w1), (x0 - px * w0, y0 - py * w0)]
    pygame.draw.polygon(surface, (*_clamp_color(color), int(alpha)), pts)


# ============================================================================
# 5.  PARTICLE
# ============================================================================

class Particle:
    """Partikel penuh: position, velocity, acceleration, life, max_life,
    size, rotation, rotation_speed, alpha, gravity, color (+ drag, shape,
    layer, additive, scatter)."""

    __slots__ = ("x", "y", "vx", "vy", "ax", "ay", "life", "max_life",
                 "size", "rotation", "rotation_speed", "alpha", "gravity",
                 "color", "shape", "drag", "additive", "layer", "active",
                 "scatter", "seed")

    def __init__(self):
        self.active = False

    def spawn(self, x, y, vx=0.0, vy=0.0, ax=0.0, ay=0.0,
              life=0.5, size=3.0, rotation=0.0, rotation_speed=0.0,
              alpha=255, gravity=0.0, color=(255, 125, 32),
              shape="ember", drag=0.0, additive=True, layer="front",
              scatter=0.0, seed=0):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.ax = float(ax)
        self.ay = float(ay)
        self.life = float(max(0.01, life))
        self.max_life = self.life
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
        self.seed = int(seed)
        self.active = True
        return self

    # -- update -------------------------------------------------------
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

    def draw_alpha(self):
        """Alpha efektif frame ini (setelah peluruhan umur)."""
        return self._fade()

    # -- tampilan vektor (kontrak API) --------------------------------
    # Penyimpanan internal sengaja SKALAR: pool 200 partikel ber-__slots__
    # jauh lebih murah daripada membuat ratusan objek Vector2 tiap frame
    # di jalur update yang panas. Properti di bawah memberi tampilan
    # ``position`` / ``velocity`` / ``acceleration`` sesuai kontrak untuk
    # kode pemanggil, debug overlay, dan tes — tanpa membebani update.
    @property
    def position(self):
        return pygame.Vector2(self.x, self.y)

    @position.setter
    def position(self, v):
        self.x = float(v[0])
        self.y = float(v[1])

    @property
    def velocity(self):
        return pygame.Vector2(self.vx, self.vy)

    @velocity.setter
    def velocity(self, v):
        self.vx = float(v[0])
        self.vy = float(v[1])

    @property
    def acceleration(self):
        return pygame.Vector2(self.ax, self.ay + self.gravity)

    @acceleration.setter
    def acceleration(self, v):
        self.ax = float(v[0])
        self.ay = float(v[1])

    @property
    def alive(self):
        return self.active

    # -- draw ---------------------------------------------------------
    def draw(self, surface):
        if not self.active:
            return
        a = self._fade()
        if a <= 1:
            return
        color = (*self.color, a)
        x, y = int(self.x), int(self.y)
        s = max(1.0, self.size)
        shape = self.shape

        if shape == "ember":
            t = self.life / max(0.001, self.max_life)
            col = _mix(P["fire_darkest"], self.color, 0.25 + 0.75 * t)
            _blit_faded(surface, ember_surface(max(1, int(s * 0.8)), col),
                        x, y, a, additive=True)
        elif shape == "streak":
            ang = math.atan2(self.vy, self.vx)
            ca, sa = math.cos(ang), math.sin(ang)
            pygame.draw.line(surface, color,
                             (x - ca * s * 2.4, y - sa * s * 2.4),
                             (x + ca * s * 1.1, y + sa * s * 1.1),
                             max(1, int(s * 0.6)))
        elif shape == "flame":
            w = int(s * 4) + 8
            h = int(s * 6) + 8
            tmp = _scratch(w, h)
            flame_poly(tmp, w // 2, h - 2, s * 2.4, seed=self.seed,
                       alpha=a, phase=self.rotation, w=s * 1.05)
            blit_add(surface, tmp, (x - w // 2, y - h + 2))
        elif shape == "smoke":
            r = max(2, int(s))
            _blit_faded(surface, glow_surface(r + 2, self.color, 0.30),
                        x, y, int(a * 0.72), additive=False)
        elif shape == "shard":
            shard_poly(surface, x, y, self.rotation, s * 2.0,
                       max(1.0, s * 0.5), self.color, a)
        elif shape == "debris":
            shard_poly(surface, x, y, self.rotation, s * 1.7,
                       max(1.0, s * 0.62), self.color, a)
        elif shape == "dust":
            pygame.draw.circle(surface, color, (x, y), max(1, int(s * 0.55)))
        elif shape == "spark":
            c = max(1, int(s))
            pygame.draw.line(surface, color, (x - c, y), (x + c, y), 1)
            pygame.draw.line(surface, color, (x, y - c), (x, y + c), 1)
        elif shape == "ring":
            pygame.draw.circle(surface, color, (x, y), max(1, int(s)), 1)
        elif shape == "rune":
            # goresan runik pendek yang berputar
            ang = self.rotation
            r = max(2, int(s * 1.6))
            for k in range(3):
                aa = ang + k * 2.094
                pygame.draw.line(surface, color,
                                 (x + math.cos(aa) * r * 0.4,
                                  y + math.sin(aa) * r * 0.4),
                                 (x + math.cos(aa) * r,
                                  y + math.sin(aa) * r), 1)
        elif shape == "brand":
            # bara berat Phantasm: inti pekat + cangkang membara
            r = max(1, int(s * 0.7))
            _blit_faded(surface, glow_surface(r + 2, P["chaos_bright"], 0.9),
                        x, y, a, additive=True)
            pygame.draw.rect(surface, (*self.color, a),
                             (x - r, y - r, r * 2, r * 2), 1)
            pygame.draw.circle(surface, (*P["fire_hot"], a), (x, y), r)
        else:
            pygame.draw.circle(surface, color, (x, y), max(1, int(s * 0.6)))


# ============================================================================
# 6.  PARTICLE SYSTEM — pool tetap dengan kursor melingkar
# ============================================================================

class ParticleSystem:
    """Pool reusable, burst terarah, cap keras (tidak pernah tumbuh).

    Karena pool-nya tetap dan kursornya melingkar, runtime TIDAK PERNAH
    mengalokasi partikel baru: yang tertua otomatis dipakai ulang.
    """

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = max(8, int(cap))
        self.particles = [Particle() for _ in range(self.cap)]
        self._cursor = 0

    def _next(self):
        p = self.particles[self._cursor]
        self._cursor = (self._cursor + 1) % self.cap
        return p

    def spawn(self, x, y, **kw):
        budget = particle_budget()
        if budget <= 0.0:
            return None
        if budget < 1.0 and random.random() >= budget:
            return None
        return self._next().spawn(x, y, **kw)

    def burst(self, x, y, count, speed=(40, 140), life=(0.2, 0.5),
              size=(2, 5), colors=((255, 125, 32),), spread=math.tau,
              direction=0.0, gravity=0.0, drag=0.0, shape="ember",
              additive=True, layer="front", rotation_speed=(0.0, 0.0),
              scatter=0.0, lift=0.0):
        """Ledakan partikel terarah (sudut, sebaran, kecepatan, umur,
        ukuran, warna, gravitasi, drag, rotasi) dalam satu panggilan."""
        budget = particle_budget()
        if budget <= 0.0:
            return 0
        count = max(0, int(count))
        if budget < 1.0:
            if count > 1:
                count = max(1, int(count * budget))
            elif random.random() >= budget:
                return 0
        for i in range(count):
            p = self._next()
            ang = direction + random.uniform(-spread / 2.0, spread / 2.0)
            sp = random.uniform(speed[0], speed[1])
            lf = random.uniform(life[0], life[1])
            sz = random.uniform(size[0], size[1])
            color = colors[int(random.random() * len(colors))]
            rot = random.uniform(-math.pi, math.pi)
            rspd = random.uniform(rotation_speed[0], rotation_speed[1])
            p.spawn(x, y,
                    math.cos(ang) * sp,
                    math.sin(ang) * sp - lift,
                    0.0, 0.0, lf, sz, rot, rspd, 255, gravity, color,
                    shape, drag, additive, layer, scatter,
                    seed=int(x) + i * 7)

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
# 7.  SWING TRAIL — pita sabetan dari histori posisi pedang
# ============================================================================

class SwingTrail:
    """Trail greatsword Vokrahn.

    Menyimpan beberapa posisi senjata terakhir::

        OLD POSITION -> OLD POSITION -> OLD POSITION -> CURRENT POSITION

    lalu menyusunnya menjadi poligon translucent yang memudar.  Setiap
    PASANGAN sample jadi quad-nya SENDIRI dengan alpha sendiri (baru =
    terang, lama = nyaris hilang) — itu yang membuat sabetan terbaca
    sebagai *gerak*, bukan sebagai pelat merah.
    """

    def __init__(self, samples=TRAIL_SAMPLES, life=0.16):
        self.samples = max(4, int(samples))
        self.life = float(life)
        self.history = []            # [[grip, ujung, umur, panas]]
        self.enabled = True
        self.age = 0.0
        self.hot = 0.0               # 0..1 seberapa "aktif" sabetan

    def reset(self):
        self.history.clear()
        self.age = 0.0
        self.hot = 0.0

    def push(self, root, tip, heat=1.0):
        self.history.append([tuple(root), tuple(tip), 0.0, float(heat)])
        if len(self.history) > self.samples:
            del self.history[0:len(self.history) - self.samples]

    def update(self, dt):
        self.age += dt
        if self.history:
            keep = []
            for s in self.history:
                s[2] += dt
                if s[2] <= self.life:
                    keep.append(s)
            self.history = keep
        self.hot = max(0.0, self.hot - dt * 3.0)

    def draw(self, surface):
        if not self.enabled or len(self.history) < 3:
            return
        n = len(self.history)
        quads = []
        for i, (root, tip, age, _heat) in enumerate(self.history):
            t = i / float(n - 1)
            fade = max(0.0, 1.0 - age / self.life)
            rx, ry = root
            tx, ty = tip
            # pita hanya menutup bagian TERLUAR bilah supaya tidak
            # menelan siluet karakter
            k = 0.55 + 0.25 * (1.0 - t)
            quads.append(((tx, ty),
                          (rx + (tx - rx) * k, ry + (ty - ry) * k),
                          t * t * fade))

        xs = [q[0][0] for q in quads] + [q[1][0] for q in quads]
        ys = [q[0][1] for q in quads] + [q[1][1] for q in quads]
        pad = 10
        x0, y0 = int(min(xs)) - pad, int(min(ys)) - pad
        w = int(max(xs) - min(xs)) + pad * 2
        h = int(max(ys) - min(ys)) + pad * 2
        if w <= 2 or h <= 2 or w > 900 or h > 900:
            return
        buf = _scratch(w, h)

        def sh(pt):
            return (pt[0] - x0, pt[1] - y0)

        strength = max(0.0, min(1.0, 0.42 + self.hot * 0.58))
        for i in range(len(quads) - 1):
            (o0, i0_, f0) = quads[i]
            (o1, i1_, f1) = quads[i + 1]
            f = (f0 + f1) * 0.5 * strength
            if f <= 0.02:
                continue
            pygame.draw.polygon(buf, (*P["chaos_dark"], int(52 * f)),
                                [sh(o0), sh(o1), sh(i1_), sh(i0_)])
            mid = [sh(o0), sh(o1),
                   sh((i1_[0] + (o1[0] - i1_[0]) * 0.45,
                      i1_[1] + (o1[1] - i1_[1]) * 0.45)),
                   sh((i0_[0] + (o0[0] - i0_[0]) * 0.45,
                      i0_[1] + (o0[1] - i0_[1]) * 0.45))]
            pygame.draw.polygon(buf, (*P["fire_mid"], int(102 * f)), mid)
            pygame.draw.line(buf, (*P["fire_bright"], int(230 * f)),
                             sh(o0), sh(o1), 2)
            pygame.draw.line(buf, (*P["fire_glow"], int(205 * f)),
                             sh(o0), sh(o1), 1)
        blit_add(surface, buf, (x0, y0))

    def tip(self):
        return self.history[-1][1] if self.history else None


# ============================================================================
# 8.  IMPACT FX — flash, shockwave, sabit, serpihan
# ============================================================================

class ImpactFX:
    """Satu kejadian dampak.

    ``kind``:
      ``melee``  — tebasan greatsword (sabit api + retakan tanah)
      ``bolt``   — Chaos Bolt mendarat (ledakan gerigi + serpihan)
      ``brand``  — Chaos Brand Phantasm meledak (cangkang chaos + bara)
      ``dash``   — Chaos Strike mendarat (shockwave kuda + debu)
      ``skill``  — dampak umum skill
    """

    LIFE = {"melee": 0.28, "bolt": 0.32, "brand": 0.40, "dash": 0.36,
            "skill": 0.36}

    def __init__(self, x, y, kind="melee", angle=0.0, power=1.0,
                 color=None, radius=44.0):
        self.x = float(x)
        self.y = float(y)
        self.kind = kind
        self.angle = float(angle)
        self.power = max(0.15, float(power))
        self.radius = float(radius)
        self.color = tuple(color[:3]) if color else P["fire_bright"]
        self.age = 0.0
        self.life = self.LIFE.get(kind, 0.32)
        self.active = True
        self.seed = random.randint(0, 9999)
        self._cracks = None

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age >= self.life:
            self.active = False

    # ------------------------------------------------------------------
    def draw(self, surface):
        if not self.active:
            return
        t = max(0.0, min(1.0, self.age / self.life))
        inv = 1.0 - t
        x, y = int(self.x), int(self.y)
        pw = self.power

        # -- kilat inti (impact flash) --------------------------------
        if t < 0.34:
            ft = 1.0 - t / 0.34
            spark_star(surface, x, y, (8 + 14 * pw) * (0.4 + 0.6 * ft),
                       P["fire_hot"], int(195 * ft), spikes=4,
                       rot=self.angle, core=P["fire_white"])
            _blit_faded(surface,
                        glow_surface(int((10 + 16 * pw) * ft + 4),
                                     P["fire_bright"], 1.0),
                        x, y, int(238 * ft), additive=True)

        # -- gelombang kejut (memuai + menipis) -----------------------
        r = int(self.radius * (0.24 + 0.9 * _ease("oc", t)) * pw)
        if r > 2 and inv > 0.02:
            _blit_faded(surface,
                        ring_surface(r, max(1, int(2 * inv) + 1),
                                     self.color, 255),
                        x, y, int(200 * inv), additive=True)
            _blit_faded(surface,
                        ellipse_ring_surface(int(r * 1.08),
                                             max(2, int(r * 0.4)), 2,
                                             P["fire_hot"], 255),
                        x, y + 4, int(112 * inv), additive=True)

        if self.kind == "melee":
            self._draw_slash(surface, t, inv)
        elif self.kind == "bolt":
            self._draw_bolt(surface, t, inv)
        elif self.kind == "brand":
            self._draw_brand(surface, t, inv)
        elif self.kind == "dash":
            self._draw_dash(surface, t, inv)

    # ------------------------------------------------------------------
    def _draw_slash(self, surface, t, inv):
        """Fragmen sabit: tiga busur tipis melintang arah tebasan."""
        span = 1.2
        for k, (sc, wd, col) in enumerate((
                (1.0, 2, P["fire_hot"]),
                (0.72, 2, P["fire_bright"]),
                (1.22, 1, P["chaos_bright"]))):
            r = self.radius * sc * (0.5 + 0.75 * _ease("out", t))
            pts = []
            for i in range(9):
                a = self.angle - span / 2 + span * i / 8.0
                pts.append((self.x + math.cos(a) * r,
                            self.y + math.sin(a) * r * 0.82))
            a255 = int((150 - k * 34) * inv)
            if a255 > 3:
                pygame.draw.lines(surface, (*col, a255), False, pts, wd)
        # retakan tanah pendek
        if self._cracks is None:
            self._cracks = []
            for k in range(3):
                a = self.angle + (_hash01(self.seed + k) - 0.5) * 1.6
                ln = self.radius * (0.5 + _hash01(self.seed + k * 5) * 0.6)
                self._cracks.append(crack_points(
                    self.x, self.y + 10, self.x + math.cos(a) * ln,
                    self.y + 10 + math.sin(a) * ln * 0.4, 4, 4.0,
                    self.seed + k * 9))
        for pts in self._cracks:
            if len(pts) > 1:
                pygame.draw.lines(surface, (*P["chaos_dark"], int(160 * inv)),
                                  False, pts, 2)

    def _draw_bolt(self, surface, t, inv):
        """Ledakan Chaos Bolt: cangkang api bergerigi + pecahan."""
        r = self.radius * (0.3 + 0.8 * _ease("oc", t))
        pts = []
        for i in range(11):
            a = i * math.tau / 11.0
            wob = 0.70 + _hash01(self.seed + i) * 0.55
            pts.append((self.x + math.cos(a) * r * wob,
                        self.y + math.sin(a) * r * wob * 0.9))
        if len(pts) > 2:
            pygame.draw.polygon(surface, (*P["fire_dark"], int(115 * inv)),
                                pts)
            pygame.draw.polygon(surface, (*P["fire_glow"], int(168 * inv)),
                                pts, 2)
        for k in range(4):
            a = self.angle + math.pi + (_hash01(self.seed + k * 3) - 0.5) * 2.2
            d = r * (0.7 + _hash01(self.seed + k * 7) * 0.6)
            shard_poly(surface, self.x + math.cos(a) * d,
                       self.y + math.sin(a) * d, a, 5.0, 1.6,
                       P["metal_light"], int(190 * inv))

    def _draw_brand(self, surface, t, inv):
        """Chaos Brand meledak: cangkang chaos + bara berputar."""
        r = self.radius * (0.26 + 0.85 * _ease("oc", t))
        rect = pygame.Rect(int(self.x - r), int(self.y - r * 0.9),
                           int(r * 2), int(r * 1.8))
        if rect.width > 3 and rect.height > 3:
            pygame.draw.ellipse(surface, (*P["chaos_mid"], int(90 * inv)),
                                rect, max(1, int(3 * inv) + 1))
        for k in range(6):
            a = _hash01(self.seed + k * 17) * math.tau + t * 3.0
            d = r * (0.55 + _hash01(self.seed + k * 23) * 0.7)
            px = self.x + math.cos(a) * d
            py = self.y + math.sin(a) * d * 0.85
            c = max(1, int(3 * inv) + 1)
            pygame.draw.rect(surface, (*P["fire_hot"], int(210 * inv)),
                             (int(px - c), int(py - c), c * 2, c * 2))

    def _draw_dash(self, surface, t, inv):
        """Chaos Strike mendarat: kejut elips tanah + kepulan debu."""
        r = self.radius * (0.3 + 0.9 * _ease("oc", t))
        for k, (m, col) in enumerate(((1.0, P["chaos_bright"]),
                                      (0.72, P["fire_hot"]))):
            rect = pygame.Rect(int(self.x - r * m),
                               int(self.y + 6 - r * m * 0.36),
                               int(r * m * 2), int(r * m * 0.72))
            if rect.width > 3:
                pygame.draw.ellipse(surface, (*col, int(150 * inv * (1 - k * 0.4))),
                                    rect, max(1, int(3 * inv)))
        # kepulan debu kuda (bukan lingkaran: tiga gumpalan bergeser)
        for k in range(3):
            a = self.angle + math.pi + (k - 1) * 0.7
            d = r * (0.6 + 0.4 * k * 0.3)
            _blit_faded(surface, glow_surface(int(6 + 5 * k), P["dust"], 0.35),
                        self.x + math.cos(a) * d,
                        self.y + 10 + math.sin(a) * d * 0.4,
                        int(120 * inv), additive=False)


# ============================================================================
# 9.  PROYEKTIL MODULAR
# ============================================================================

class BaseProjectile:
    """Kontrak proyektil bersama.

    Atribut wajib LENGKAP dan semuanya dipakai: ``position``, ``velocity``,
    ``speed``, ``damage``, ``lifetime``, ``target``, ``radius``,
    ``rotation``, ``trail``, ``particles``, ``active`` — semuanya dengan
    ``pygame.Vector2`` dan delta-time.

    Lifecycle::

        SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY
    """

    kind = "base"

    def __init__(self, x, y, tx, ty, speed=BOLT_SPEED, damage=0.0,
                 lifetime=1.6, radius=10.0, target=None, owner=None):
        self.position = pygame.Vector2(float(x), float(y))
        self.spawn_position = pygame.Vector2(self.position)
        d = pygame.Vector2(float(tx) - float(x), float(ty) - float(y))
        if d.length_squared() < 1e-6:
            d = pygame.Vector2(1.0, 0.0)
        self.direction = d.normalize()
        self.speed = float(speed)
        self.velocity = self.direction * self.speed
        self.damage = float(damage)
        self.lifetime = float(lifetime)
        self.max_lifetime = float(lifetime)
        self.radius = float(radius)
        self.rotation = math.atan2(self.direction.y, self.direction.x)
        self.rotation_speed = 0.0
        self.target = target
        self.owner = owner
        self.trail = []                      # [[Vector2, umur]]
        self.trail_len = 12
        self.particles = []                  # jejak partikel milik sendiri
        self.active = True
        self.hit = False
        self.age = 0.0
        self.seed = random.randint(0, 9999)
        self.destination = pygame.Vector2(float(tx), float(ty))

    # -- siklus hidup --------------------------------------------------
    def update(self, dt, system=None):
        if not self.active:
            return
        self.age += dt
        self.lifetime -= dt
        if self.lifetime <= 0.0:
            self.destroy(system, impact=False)
            return
        self.travel(dt)
        self.update_trail(dt)
        self.emit(dt, system)
        if self.check_collision():
            self.destroy(system, impact=True)

    def travel(self, dt):
        self.position += self.velocity * dt
        self.rotation += self.rotation_speed * dt

    def update_trail(self, dt):
        self.trail.append([pygame.Vector2(self.position), 0.0])
        if len(self.trail) > self.trail_len:
            del self.trail[0:len(self.trail) - self.trail_len]
        for t in self.trail:
            t[1] += dt

    def emit(self, dt, system):
        pass

    def check_collision(self):
        tgt = self.target
        if tgt is not None and getattr(tgt, "alive", False):
            tx = float(getattr(tgt, "x", 0.0))
            ty = float(getattr(tgt, "y", 0.0))
            hit_r = self.radius + float(getattr(tgt, "radius", 12.0))
            if (self.position - pygame.Vector2(tx, ty)).length() <= hit_r:
                return True
        if (self.position - self.destination).length() <= self.radius * 0.9:
            return True
        return False

    def destroy(self, system=None, impact=True):
        if not self.active:
            return
        self.active = False
        self.hit = bool(impact)
        if system is not None and impact:
            system.on_impact(self)

    def draw(self, surface):
        pass

    # -- helper trail --------------------------------------------------
    def _draw_ribbon(self, surface, w0, w1, colors, fade=0.13):
        """Pita meruncing dari histori posisi (bukan garis lurus)."""
        n = len(self.trail)
        if n < 3:
            return
        pts = []
        for i, (pos, age) in enumerate(self.trail):
            t = i / float(n - 1)
            a = max(0.0, 1.0 - age / max(0.01, fade))
            pts.append((pos.x, pos.y, t * a))
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        pad = int(max(w0, w1)) + 6
        x0, y0 = int(min(xs)) - pad, int(min(ys)) - pad
        w = int(max(xs) - min(xs)) + pad * 2
        h = int(max(ys) - min(ys)) + pad * 2
        if w <= 2 or h <= 2 or w > 900 or h > 900:
            return
        buf = _scratch(w, h)
        for i in range(len(pts) - 1):
            ax, ay, af = pts[i]
            bx, by, bf = pts[i + 1]
            f = (af + bf) * 0.5
            if f <= 0.03:
                continue
            t = i / float(max(1, len(pts) - 2))
            wd = w0 + (w1 - w0) * t
            for col, mul, gr in colors:
                pygame.draw.line(buf, (*col, int(255 * f * mul)),
                                 (ax - x0, ay - y0), (bx - x0, by - y0),
                                 max(1, int(wd * gr)))
        blit_add(surface, buf, (x0, y0))


class ChaosBoltProjectile(BaseProjectile):
    """Q — Chaos Bolt: cepuk kekacauan memanjang (bukan lingkaran polos).

    Bentuk: panah gelap berinti crimson — kepala runcing, badan
    bersayap, ekor memudar, rotasi mengikuti arah terbang, glow
    beranulus, jejak bara.
    """

    kind = "bolt"

    def __init__(self, x, y, tx, ty, speed=BOLT_SPEED, damage=0.0,
                 lifetime=1.6, radius=10.0, target=None, owner=None,
                 scale=1.0):
        super().__init__(x, y, tx, ty, speed=speed, damage=damage,
                         lifetime=lifetime, radius=radius, target=target,
                         owner=owner)
        self.scale = max(0.3, float(scale))

    def emit(self, dt, system):
        if system is None:
            return
        if self.age < 0.05 or random.random() < 0.45:
            return
        system.particles.spawn(
            self.position.x - self.direction.x * 12.0 * self.scale,
            self.position.y - self.direction.y * 12.0 * self.scale,
            vx=random.uniform(-14, 14), vy=random.uniform(-14, 14)
            - self.velocity.y * 0.05,
            life=random.uniform(0.15, 0.35),
            size=random.uniform(1.2, 2.4) * self.scale,
            color=random.choice((P["chaos_bright"], P["fire_bright"],
                                 P["fire_hot"])),
            shape="ember", additive=True, drag=1.2)

    def draw(self, surface):
        px, py = self.position.x, self.position.y
        s = self.scale
        ca, sa = math.cos(self.rotation), math.sin(self.rotation)
        ex, ey = -sa, ca                     # sumbu tegak

        # jejak panjang (ribbon meruncing)
        self._draw_ribbon(surface, 1.2 * s, 4.2 * s,
                          ((P["chaos_dark"], 0.55, 1.0),
                           (P["chaos_bright"], 0.85, 0.55),
                           (P["fire_hot"], 1.0, 0.2)), fade=0.16)

        # glow beranulus (di bawah bentuk)
        _blit_faded(surface, glow_surface(int(13 * s), P["chaos_bright"], 1.0),
                    px, py, 120, additive=True)
        _blit_faded(surface, glow_surface(int(7 * s), P["fire_hot"], 1.0),
                    px, py, 150, additive=True)

        # badan panah: kepala runcing + sayap ekor (poligon, bukan lingkaran)
        tip = (px + ca * 15 * s, py + sa * 15 * s)
        sh1 = (px + ex * 3.6 * s, py + ey * 3.6 * s)
        sh2 = (px - ex * 3.6 * s, py - ey * 3.6 * s)
        mid1 = (px - ca * 5 * s + ex * 2.2 * s,
                py - sa * 5 * s + ey * 2.2 * s)
        mid2 = (px - ca * 5 * s - ex * 2.2 * s,
                py - sa * 5 * s - ey * 2.2 * s)
        tail1 = (px - ca * 9 * s + ex * 4.2 * s,
                 py - sa * 9 * s + ey * 4.2 * s)
        tail2 = (px - ca * 9 * s - ex * 4.2 * s,
                 py - sa * 9 * s - ey * 4.2 * s)
        back = (px - ca * 12 * s, py - sa * 12 * s)
        pygame.draw.polygon(surface, P["chaos_darkest"],
                            [tail1, tail2, back])
        pygame.draw.polygon(surface, P["chaos_dark"],
                            [tip, sh1, mid1, mid2, sh2])
        pygame.draw.polygon(surface, P["chaos_mid"],
                            [(tip[0] + (back[0] - tip[0]) * 0.15,
                              tip[1] + (back[1] - tip[1]) * 0.15),
                             (sh1[0] + (back[0] - sh1[0]) * 0.5,
                              sh1[1] + (back[1] - sh1[1]) * 0.5),
                             (back[0], back[1]),
                             (sh2[0] + (back[0] - sh2[0]) * 0.5,
                              sh2[1] + (back[1] - sh2[1]) * 0.5)])
        pygame.draw.polygon(surface, P["chaos_bright"],
                            [tip,
                             (px + ex * 1.6 * s, py + ey * 1.6 * s),
                             (px - ca * 4 * s, py - sa * 4 * s),
                             (px - ex * 1.6 * s, py - ey * 1.6 * s)])
        # garis inti menyala
        pygame.draw.line(surface, P["chaos_hot"],
                         (px + ca * 13 * s, py + sa * 13 * s),
                         (px - ca * 5 * s, py - sa * 5 * s),
                         max(1, int(1.6 * s)))
        pygame.draw.line(surface, P["fire_glow"],
                         (px + ca * 11 * s, py + sa * 11 * s),
                         (px - ca * 2 * s, py - sa * 2 * s),
                         max(1, int(0.8 * s)))
        # kepala
        pygame.draw.circle(surface, P["fire_white"],
                           (int(px + ca * 14 * s), int(py + sa * 14 * s)),
                           max(1, int(1.6 * s)))


class ChaosBrandProjectile(BaseProjectile):
    """R — Chaos Brand: bara berat yang meluncur lambat (Phantasm).

    Bentuk: gumpalan chaos chunky — cangkang gelap retak bercahaya
    crimson, inti membara berdenyut, ekor bara, sedikit mengayun.
    """

    kind = "brand"
    WOBBLE = 0.06           # amplitudo ayunan (fraksi kecepatan)

    def __init__(self, x, y, tx, ty, speed=BRAND_SPEED, damage=0.0,
                 lifetime=2.2, radius=14.0, target=None, owner=None,
                 scale=1.0):
        super().__init__(x, y, tx, ty, speed=speed, damage=damage,
                         lifetime=lifetime, radius=radius, target=target,
                         owner=owner)
        self.scale = max(0.3, float(scale))
        self.wobble_phase = random.uniform(0.0, math.tau)

    def travel(self, dt):
        # ayun halus tegak lurus arah terbang (bara berat bergoyang)
        self.position += self.velocity * dt
        self.wobble_phase += dt * 9.0
        amp = self.WOBBLE * self.speed * dt
        ex, ey = -self.direction.y, self.direction.x
        self.position.x += ex * math.sin(self.wobble_phase) * amp
        self.position.y += ey * math.sin(self.wobble_phase) * amp
        self.rotation += self.rotation_speed * dt

    def emit(self, dt, system):
        if system is None or random.random() < 0.35:
            return
        system.particles.spawn(
            self.position.x + random.uniform(-4, 4),
            self.position.y + random.uniform(-4, 4),
            vx=random.uniform(-20, 20), vy=random.uniform(-30, -6),
            life=random.uniform(0.3, 0.7),
            size=random.uniform(1.4, 3.0) * self.scale,
            color=random.choice((P["chaos_bright"], P["fire_bright"],
                                 P["ash"])),
            shape="ember", additive=True, drag=0.8, gravity=60.0)

    def draw(self, surface):
        px, py = self.position.x, self.position.y
        s = self.scale
        pulse = 0.75 + 0.25 * math.sin(self.wobble_phase * 0.5)

        # jejak asap-bar
        self._draw_ribbon(surface, 2.0 * s, 5.5 * s,
                          ((P["chaos_dark"], 0.5, 1.0),
                           (P["fire_dark"], 0.75, 0.55),
                           (P["chaos_bright"], 0.9, 0.22)), fade=0.22)

        # glow
        _blit_faded(surface, glow_surface(int(16 * s * pulse + 4),
                                          P["chaos_bright"], 1.0),
                    px, py, 130, additive=True)

        # cangkang chunky (kotak berputar + retakan cahaya)
        rot = self.rotation
        ca, sa = math.cos(rot), math.sin(rot)
        ex, ey = -sa, ca
        r = 7.0 * s
        corners = []
        for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            wob = 0.82 + 0.18 * _hash01(self.seed + int((dx + 1) + (dy + 1) * 2) * 7)
            corners.append((px + (ca * dx * r - sa * dy * r) * wob,
                            py + (sa * dx * r + ca * dy * r) * wob))
        pygame.draw.polygon(surface, P["arm_darkest"], corners)
        inner = [(px + (cx - px) * 0.62, py + (cy - py) * 0.62)
                 for cx, cy in corners]
        pygame.draw.polygon(surface, P["chaos_dark"], inner)
        # retakan membara
        pygame.draw.line(surface, P["fire_bright"],
                         corners[0], corners[2], max(1, int(1.4 * s)))
        pygame.draw.line(surface, P["chaos_hot"],
                         corners[1], corners[3], max(1, int(1.2 * s)))
        # inti membara
        pygame.draw.circle(surface, P["fire_hot"], (int(px), int(py)),
                           max(1, int(2.6 * s * pulse)))
        pygame.draw.circle(surface, P["fire_glow"], (int(px), int(py)),
                           max(1, int(1.3 * s * pulse)))


class ProjectileSystem:
    """Manajer proyektil: spawn, update, cull, dampak, cap keras."""

    def __init__(self, particles, cap=MAX_PROJECTILES):
        self.projectiles = []
        self.particles = particles
        self.cap = max(4, int(cap))
        self.impacts = []
        self.on_impact_cb = None

    # -- spawn ---------------------------------------------------------
    def _make_room(self):
        if len(self.projectiles) >= self.cap:
            self.projectiles.pop(0)          # yang tertua dibuang

    def spawn_bolt(self, x, y, tx, ty, **kw):
        self._make_room()
        pr = ChaosBoltProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    def spawn_brand(self, x, y, tx, ty, **kw):
        self._make_room()
        pr = ChaosBrandProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    # -- lifecycle -----------------------------------------------------
    def update(self, dt):
        for pr in self.projectiles:
            pr.update(dt, self)
        if self.projectiles:
            self.projectiles = [p for p in self.projectiles if p.active]

    def _push_impact(self, fx):
        while len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(fx)

    def on_impact(self, projectile):
        """Dipanggil proyektil saat menabrak: FX + partikel + game feel."""
        px, py = projectile.position.x, projectile.position.y
        ang = projectile.rotation
        if projectile.kind == "brand":
            self._push_impact(ImpactFX(px, py, "brand", ang, 1.4,
                                       P["chaos_hot"], 56.0))
            self.particles.burst(px, py, 8, speed=(90, 300),
                                 life=(0.3, 0.7), size=(2, 4.6),
                                 colors=(P["chaos_mid"], P["chaos_bright"],
                                         P["fire_bright"], P["ember"]),
                                 gravity=260, drag=0.8, shape="ember")
            self.particles.burst(px, py, 3, speed=(60, 190),
                                 life=(0.3, 0.7), size=(1.6, 3.2),
                                 colors=(P["arm_mid"], P["metal_light"]),
                                 gravity=520, shape="shard",
                                 rotation_speed=(-8, 8), additive=False)
            _feel_shake(3.2, 0.18)
            _feel_hit_stop(0.030)
        else:
            self._push_impact(ImpactFX(px, py, "bolt", ang, 1.0,
                                       P["chaos_bright"], 36.0))
            self.particles.burst(px, py, 6, speed=(80, 250),
                                 life=(0.2, 0.48), size=(1.6, 3.8),
                                 colors=(P["chaos_bright"], P["fire_bright"],
                                         P["fire_hot"], P["ember"]),
                                 spread=2.4, direction=ang + math.pi,
                                 gravity=250, drag=1.0, shape="ember")
            self.particles.burst(px, py, 4, speed=(20, 70),
                                 life=(0.35, 0.75), size=(2.5, 5),
                                 colors=(P["ash"], P["dust"]),
                                 gravity=-50, shape="smoke", additive=False)
            _feel_shake(1.9, 0.12)
            _feel_hit_stop(0.020)
        if self.on_impact_cb:
            try:
                self.on_impact_cb(projectile)
            except Exception:                # pragma: no cover
                pass

    def update_impacts(self, dt):
        for im in self.impacts:
            im.update(dt)
        if self.impacts:
            self.impacts = [i for i in self.impacts if i.active]
            if len(self.impacts) > MAX_IMPACTS:
                del self.impacts[0:len(self.impacts) - MAX_IMPACTS]

    def draw(self, surface):
        for pr in self.projectiles:
            pr.draw(surface)

    def draw_impacts(self, surface):
        for im in self.impacts:
            im.draw(surface)

    def count(self):
        return len(self.projectiles)

    def clear(self):
        self.projectiles.clear()
        self.impacts.clear()


# ============================================================================
# 10.  AFTERIMAGE — siluet pose sebelumnya (dash & sabetan berat)
# ============================================================================

class Afterimage:
    """Salinan rig terakhir yang memudar (ghost trail).

    Memakai surface rig yang DISIMPAN renderer (``_last_rig``), jadi pose
    ghost selalu benar tanpa menggambar ulang badan.
    """

    __slots__ = ("surf", "x", "y", "age", "life", "tint", "active")

    def __init__(self, surf, x, y, life=0.30, tint=None):
        self.surf = surf
        self.x = float(x)
        self.y = float(y)
        self.age = 0.0
        self.life = float(max(0.05, life))
        self.tint = tint or P["chaos_dark"]
        self.active = True

    def update(self, dt):
        if not self.active:
            return
        self.age += dt
        if self.age >= self.life:
            self.active = False

    def draw(self, surface):
        if not self.active or self.surf is None:
            return
        t = 1.0 - self.age / self.life
        a = int(120 * t * t)
        if a < 4:
            return
        try:
            ghost = self.surf.copy()
            ghost.fill((*self.tint, 255), special_flags=pygame.BLEND_RGB_MULT)
            ghost.set_alpha(a)
            surface.blit(ghost, (int(self.x), int(self.y)))
        except Exception:                    # pragma: no cover
            pass


# ============================================================================
# 11.  SKILL FX — lifecycle penuh per skill
# ============================================================================

class SkillFX:
    """Efek satu skill Vokrahn, dengan lifecycle enam fase::

        CAST -> CHARGE -> RELEASE -> AREA/TRAVEL -> IMPACT -> AFTER -> FADE

    Setiap skill punya BENTUK khasnya sendiri — koridor bidik (Q), duri
    kekacauan (W), dash & kejut (E), bintang chaos & hantu (R) — supaya
    tidak semuanya jadi lingkaran.
    """

    def __init__(self, skill, x, y, facing=1, target=None, scale=1.0,
                 director=None):
        self.skill = str(skill).lower()
        self.x = float(x)
        self.y = float(y)
        self.facing = 1 if facing >= 0 else -1
        self.target = target
        self.scale = float(scale) if scale else 1.0
        self.director = director
        self.age = 0.0
        self.total = SKILL_TOTAL.get(self.skill, 1.2)
        self.active = True
        self.seed = random.randint(0, 9999)
        self.radius = WORLD_RADIUS.get(self.skill, 150.0)
        self.target_point = None
        self.phase = "CAST"
        self.engine_t = None
        self._did = set()
        self._acc = 0.0
        self._phantoms = []
        self._dash_x0 = float(x)      # titik mulai dash (E)
        self._scorched = False

    # ------------------------------------------------------------------
    @property
    def t(self):
        return max(0.0, min(1.0, self.age / max(0.01, self.total)))

    #: fraksi umur yang dikendalikan engine (sisanya = ekor AFTER/FADE).
    ENGINE_SPAN = 0.86

    def set_engine_progress(self, value):
        """Selaraskan lifecycle FX dengan ``active_skill_timer`` engine.

        Efek skill HARUS satu detak dengan AI-nya: kalau engine baru 50 %
        menuju damage, telegraph juga harus 50 %.  Umur di-*bump* (tidak
        pernah mundur) sehingga fase, `_once`, dan pertumbuhan radius
        tetap monoton walau frame di-render lompat-lompat.
        """
        try:
            v = max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return
        self.engine_t = v
        want = v * self.total * self.ENGINE_SPAN
        if want > self.age:
            self.age = want
            self.phase = skill_phase(self.t)

    def r_screen(self, mul=1.0):
        """Radius dunia -> radius layar (lapisan hidup 1:1, tanpa skala)."""
        return self.radius * mul

    @staticmethod
    def _fit(surface, r):
        """Jepit radius ke dalam canvas supaya decal tidak meledak."""
        margin = min(surface.get_width(), surface.get_height()) // 2 - 10
        return int(max(4, min(float(r), max(4, margin))))

    def follow(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def aim(self):
        """Titik bidik di ruang layar."""
        if self.target_point is not None:
            return self.target_point
        tgt = self.target
        if tgt is not None and getattr(tgt, "alive", False):
            return (self.x + self.facing * self.r_screen(0.55), self.y - 8.0)
        return (self.x + self.facing * self.r_screen(0.55), self.y - 8.0)

    # ------------------------------------------------------------------
    def update(self, dt, particles, projectiles):
        if not self.active:
            return
        self.age += dt
        self.phase = skill_phase(self.t)
        if self.age >= self.total:
            self.active = False
            return
        fn = getattr(self, "_upd_" + self.skill, None)
        if fn is not None:
            fn(dt, particles, projectiles)

    def _once(self, key):
        if key in self._did:
            return False
        self._did.add(key)
        return True

    # -- Q: Chaos Bolt -------------------------------------------------
    def _upd_q(self, dt, particles, projectiles):
        t = self.t
        ax, ay = self.aim()
        if t < 0.16 and self._once("cast"):
            particles.burst(self.x, self.y + 26, 5, speed=(50, 170),
                            life=(0.25, 0.5), size=(2, 4),
                            colors=(P["dust"], P["ash"]), spread=math.pi,
                            direction=-math.pi / 2, gravity=180,
                            shape="dust", additive=False, layer="back")
        # CHARGE: energi chaos berkumpul ke ujung bilah
        if 0.10 <= t < 0.40:
            self._acc += dt
            if self._acc >= 0.03 and self.director is not None:
                self._acc = 0.0
                lp = (self.x + self.facing * 20.0 * self.scale, self.y - 8.0)
                if self.director.unit is not None:
                    try:
                        lp = launch_point(self.director.unit, self.x, self.y)
                    except Exception:                    # pragma: no cover
                        pass
                ang = math.atan2(ay - lp[1], ax - lp[0])
                rr = random.uniform(16, 26)
                particles.spawn(
                    lp[0] + math.cos(ang + math.pi) * rr,
                    lp[1] + math.sin(ang + math.pi) * rr,
                    vx=-math.cos(ang + math.pi) * 90.0,
                    vy=-math.sin(ang + math.pi) * 90.0,
                    life=0.16, size=random.uniform(1.4, 2.6),
                    color=random.choice((P["chaos_bright"],
                                         P["chaos_hot"], P["fire_hot"])),
                    shape="streak", additive=True)
        # RELEASE: lepaskan bolt dari ujung bilah
        if 0.34 <= t < 0.46 and self._once("release") and \
                self.director is not None:
            lp = (self.x + self.facing * 20.0 * self.scale, self.y - 8.0)
            if self.director.unit is not None:
                try:
                    lp = launch_point(self.director.unit, self.x, self.y)
                except Exception:                    # pragma: no cover
                    pass
            self.director.projectiles.spawn_bolt(
                lp[0], lp[1], ax, ay, speed=BOLT_SPEED, radius=10.0,
                target=self.target, owner=self.director.unit,
                scale=self.scale)
            particles.burst(lp[0], lp[1], 4, speed=(90, 260),
                            life=(0.12, 0.3), size=(1.4, 3.0),
                            colors=(P["chaos_hot"], P["fire_hot"],
                                    P["fire_bright"]),
                            spread=1.1, direction=math.atan2(ay - lp[1],
                                                             ax - lp[0]),
                            drag=1.6, shape="streak")
            _feel_shake(1.3, 0.10)
        # IMPACT visual (bolt-nya membawa impact-nya sendiri saat
        # menabrak; ini menambah gema di titik bidik)
        if t >= 0.74 and self._once("impact"):
            particles.burst(ax, ay, 5, speed=(70, 240), life=(0.25, 0.55),
                            size=(1.8, 4.0),
                            colors=(P["chaos_bright"], P["ember"]),
                            gravity=280, drag=0.9, shape="ember")

    # -- W: Realm of Chaos ---------------------------------------------
    def _upd_w(self, dt, particles, projectiles):
        t = self.t
        if t < 0.10 and self._once("cast"):
            particles.burst(self.x, self.y + 22, 8, speed=(80, 250),
                            life=(0.3, 0.75), size=(2.5, 6),
                            colors=(P["dust"], P["ash"], P["chaos_dark"]),
                            spread=math.tau, gravity=-30, drag=0.9,
                            shape="dust", additive=False, layer="back")
            _feel_shake(2.2, 0.15)
        # CHARGE: bara merayap di sepanjang cincin
        if 0.10 <= t < 0.40:
            self._acc += dt
            if self._acc >= 0.05:
                self._acc = 0.0
                a = random.uniform(0, math.tau)
                rr = self.r_screen(0.9)
                particles.spawn(
                    self.x + math.cos(a) * rr,
                    self.y + 10 + math.sin(a) * rr * 0.42,
                    vx=0.0, vy=random.uniform(-70, -30),
                    life=random.uniform(0.3, 0.6),
                    size=random.uniform(1.6, 3.2),
                    color=random.choice((P["chaos_bright"], P["fire_bright"],
                                         P["fire_hot"])),
                    shape="ember", additive=True)
        # RELEASE: duri kekacauan MELEDAK dari tanah (damage jatuh saat
        # cast, jadi ledakan visual harus datang di awal jendela)
        if t >= 0.16 and self._once("release"):
            n = 14
            for i in range(n):
                a = i * math.tau / n + _hash01(self.seed + i) * 0.3
                rr = self.r_screen(0.94)
                sx = self.x + math.cos(a) * rr
                sy = self.y + 10 + math.sin(a) * rr * 0.42
                particles.burst(sx, sy, 3, speed=(120, 340),
                                life=(0.3, 0.7), size=(1.8, 4.2),
                                colors=(P["chaos_bright"], P["fire_bright"],
                                        P["fire_hot"]),
                                spread=0.9, direction=-math.pi / 2 + a * 0.2,
                                gravity=420, drag=0.6, shape="flame")
            particles.burst(self.x, self.y + 8, 10, speed=(200, 460),
                            life=(0.3, 0.8), size=(1.8, 4.6),
                            colors=(P["chaos_bright"], P["fire_bright"],
                                    P["ember"]),
                            spread=math.tau, gravity=300, drag=0.7,
                            shape="ember")
            self._scorched = True
            _feel_shake(4.0, 0.24)
            _feel_hit_stop(0.027)
        # AFTER: asap & bara sisa
        if t > 0.5:
            self._acc += dt
            if self._acc >= 0.07:
                self._acc = 0.0
                a = random.uniform(0, math.tau)
                rr = random.uniform(0.3, 0.9) * self.r_screen(1.0)
                particles.spawn(
                    self.x + math.cos(a) * rr,
                    self.y + 8 + math.sin(a) * rr * 0.42,
                    vx=random.uniform(-12, 12), vy=random.uniform(-46, -16),
                    life=random.uniform(0.5, 1.0),
                    size=random.uniform(2.4, 5.0),
                    color=random.choice((P["ash"], P["smoke_mid"])),
                    shape="smoke", additive=False, layer="front")

    # -- E: Chaos Strike ------------------------------------------------
    def _upd_e(self, dt, particles, projectiles):
        t = self.t
        # ekor api sepanjang jalur dash
        if 0.05 <= t < 0.62:
            self._acc += dt
            if self._acc >= 0.02:
                self._acc = 0.0
                off = dash_offset(self, t)
                bx = self.x + off
                by = self.y + 16
                particles.spawn(bx + random.uniform(-8, 8),
                                by + random.uniform(-4, 6),
                                vx=-self.facing * random.uniform(60, 160),
                                vy=random.uniform(-24, -6),
                                life=random.uniform(0.2, 0.45),
                                size=random.uniform(1.8, 4.0),
                                color=random.choice((P["fire_bright"],
                                                     P["fire_hot"],
                                                     P["chaos_bright"])),
                                shape="flame", additive=True,
                                layer="back")
        # mendarat di titik bidik (puncak dash: engine 0.30 = fx t 0.26)
        if t >= 0.28 and self._once("impact"):
            ax, ay = self.aim()
            self._dash_impact(ax, ay, particles)

    def _dash_impact(self, ax, ay, particles):
        particles.burst(ax, ay, 7, speed=(120, 360), life=(0.25, 0.6),
                        size=(2, 4.6),
                        colors=(P["chaos_bright"], P["fire_bright"],
                                P["ember"]),
                        spread=math.tau, gravity=300, drag=0.8,
                        shape="ember")
        particles.burst(ax, ay + 8, 5, speed=(80, 220), life=(0.3, 0.7),
                        size=(2.5, 5.5),
                        colors=(P["dust"], P["ash"]),
                        spread=1.4, direction=self.facing * math.pi / 2,
                        gravity=200, shape="dust", additive=False)
        if self.director is not None:
            self.director.add_impact(ax, ay, "dash",
                                     0.0 if self.facing > 0 else math.pi,
                                     1.5, P["chaos_bright"],
                                     max(30.0, self.r_screen(0.5)))
        _feel_shake(4.5, 0.24)
        _feel_hit_stop(0.033)

    # -- R: Phantasm ----------------------------------------------------
    def _upd_r(self, dt, particles, projectiles):
        t = self.t
        if t < 0.10 and self._once("cast"):
            particles.burst(self.x, self.y + 20, 9, speed=(80, 250),
                            life=(0.4, 0.9), size=(3, 6.5),
                            colors=(P["smoke_mid"], P["smoke_light"],
                                    P["ash"]),
                            spread=math.tau, gravity=-40, drag=0.9,
                            shape="smoke", additive=False, layer="back")
            _feel_shake(2.5, 0.16)
        # RELEASE: hantu-materialize (momentum damage)
        if t >= 0.16 and self._once("release"):
            for i in range(PHANTOM_COUNT):
                side = 1 if i == 0 else -1
                self._phantoms.append({
                    "side": side * self.facing,
                    "seed": self.seed + i * 31,
                    "born": self.age,
                })
            particles.burst(self.x, self.y - 6, 9, speed=(90, 280),
                            life=(0.35, 0.8), size=(1.8, 4.0),
                            colors=(P["smoke_light"], P["smoke_glow"],
                                    P["chaos_bright"]),
                            spread=math.tau, gravity=-30, drag=0.8,
                            shape="streak", additive=True)
            if self.director is not None:
                self.director.add_impact(self.x, self.y, "skill", 0.0, 1.2,
                                         P["smoke_glow"], 60.0)
            _feel_shake(3.0, 0.20)
        # AREA: hantu melayang + bara ungu
        if 0.16 <= t < 0.85:
            self._acc += dt
            if self._acc >= 0.06:
                self._acc = 0.0
                ph = random.choice(self._phantoms) if self._phantoms else \
                    {"side": self.facing, "seed": self.seed}
                px = self.x + ph["side"] * 26.0
                py = self.y - 10 + math.sin(self.age * 6.0 + ph["seed"]) * 4
                particles.spawn(px + random.uniform(-10, 10),
                                py + random.uniform(-10, 10),
                                vx=random.uniform(-16, 16),
                                vy=random.uniform(-40, -10),
                                life=random.uniform(0.4, 0.8),
                                size=random.uniform(1.6, 3.4),
                                color=random.choice((P["smoke_light"],
                                                     P["smoke_glow"],
                                                     P["chaos_hot"])),
                                shape="streak", additive=True)
        # hantu melayang kecil ke titik bidik (visual — damage dari AI)
        if t >= 0.30 and self._once("brands") and self.director is not None:
            for i in range(2):
                ax, ay = self.aim()
                sx = self.x + (1 if i == 0 else -1) * 26.0
                sy = self.y - 14.0
                self.director.projectiles.spawn_brand(
                    sx, sy, ax + random.uniform(-24, 24),
                    ay + random.uniform(-12, 12),
                    speed=BRAND_SPEED, radius=13.0,
                    target=self.target if i == 0 else None,
                    owner=self.director.unit, scale=self.scale)

    # ------------------------------------------------------------------
    # GAMBAR — BAWAH badan
    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        fn = getattr(self, "_gnd_" + self.skill, None)
        if fn is not None:
            fn(surface)

    def _gnd_q(self, surface):
        """Telegraph bidik: koridor meruncing + reticle kurung siku."""
        t = self.t
        if t > 0.85:
            return
        ax, ay = self.aim()
        # damage Q jatuh saat cast, jadi koridor harus penuh hampir segera
        grow = min(1.0, t / 0.22)
        a255 = int(120 * grow * (1.0 - max(0.0, (t - 0.45) / 0.4)))
        if a255 < 4:
            return
        taper_lane(surface, self.x + self.facing * 14.0 * self.scale,
                   self.y - 6.0, ax, ay, 2.0 * grow, 14.0 * grow,
                   P["chaos_mid"], a255)
        # reticle kurung siku di target (bukan lingkaran penuh)
        s = 10.0 + 4.0 * math.sin(self.age * 9.0)
        c = int(95 * grow * (1.0 - max(0.0, (t - 0.5) / 0.3)))
        if c > 3:
            col = (*P["chaos_bright"], c)
            for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                pygame.draw.lines(surface, col, False, [
                    (ax + dx * s, ay + dy * s * 0.5 - dy * s * 0.2),
                    (ax + dx * s, ay + dy * s * 0.5 + dy * s * 0.28),
                    (ax + dx * s * 0.55, ay + dy * s * 0.5 + dy * s * 0.28)],
                    2)

    def _gnd_w(self, surface):
        """Telegraph AoE: LINGKARAN PENUH radius dunia (kontrak) + duri.

        AI menjatuhkan damage W saat cast, jadi lingkaran radius 220
        dunia harus TEPAT pada 20 % pertama jendela skill — tes
        regresi menguncinya.
        """
        t = self.t
        if t > 0.98:
            return
        grow = min(1.0, t / 0.20)
        r = self._fit(surface, self.r_screen(1.0) * grow)
        a255 = int(150 * grow * (1.0 - max(0.0, (t - 0.70) / 0.28)))
        if a255 < 4 or r < 6:
            return
        cy = self.y + 10
        # 1) cincin PENUH — radius damage (harus lingkaran, tes mengunci)
        _blit_faded(surface, ring_surface(r, 2, P["chaos_bright"], 255),
                    self.x, cy, a255, additive=True)
        # 2) cincin duri bergerigi (dekorasi, bukan lingkaran polos)
        _blit_faded(surface,
                    spike_ring_surface(r, 12, int(r * 0.16), P["chaos_dark"],
                                       255, squash=0.42, rot=self.age * 0.4),
                    self.x, cy, int(a255 * 0.9), additive=True)
        # 3) rune runik berputar
        _blit_faded(surface,
                    arc_ring_surface(int(r * 0.7), 8, 0.55, 2,
                                     P["fire_hot"], 255, squash=0.42,
                                     rot=-self.age * 0.9),
                    self.x, cy, int(a255 * 0.8))
        # 4) genangan scorched setelah meledak
        if self._scorched:
            fade = max(0.0, 1.0 - (t - 0.16) / 0.75)
            if fade > 0.02:
                _blit_faded(surface, ground_pool_surface(r, P["chaos_dark"],
                                                         0.5),
                            self.x, cy, int(170 * fade))

    def _gnd_e(self, surface):
        """Jalur dash: pita memudar dari titik awal ke posisi sekarang."""
        t = self.t
        if t < 0.05 or t > 0.75:
            return
        off = dash_offset(self, t)
        bx = self.x + off
        grow = min(1.0, t / 0.2)
        a255 = int(130 * grow * (1.0 - max(0.0, (t - 0.4) / 0.35)))
        if a255 < 4:
            return
        taper_lane(surface, self._dash_x0, self.y + 14.0, bx,
                   self.y + 14.0, 3.0, 9.0, P["fire_dark"], a255)
        _blit_faded(surface, ground_pool_surface(int(26 * grow),
                                                 P["chaos_dark"], 0.4),
                    self.x, self.y + 14, int(a255 * 0.8))

    def _gnd_r(self, surface):
        """Telegraph: LINGKARAN PENUH radius dunia + bintang chaos 8 titik.

        Sama seperti W: damage jatuh saat cast, jadi lingkaran 220 dunia
        harus tepat pada 20 % pertama jendela skill.
        """
        t = self.t
        if t > 0.98:
            return
        grow = min(1.0, t / 0.20)
        r = self._fit(surface, self.r_screen(1.0) * grow)
        a255 = int(150 * grow * (1.0 - max(0.0, (t - 0.75) / 0.23)))
        if a255 < 4 or r < 6:
            return
        cy = self.y + 10
        # 1) cincin PENUH — radius damage (harus lingkaran, tes mengunci)
        _blit_faded(surface, ring_surface(r, 2, P["smoke_light"], 255),
                    self.x, cy, a255, additive=True)
        # 2) bintang chaos 8 titik (bukan lingkaran)
        pts = chaos_star_points(self.x, cy, r * 0.8, spikes=4,
                                rot=self.age * 0.5, squash=0.42, inner=0.45)
        if len(pts) > 2:
            pygame.draw.polygon(surface,
                                (*P["smoke_dark"], int(a255 * 0.55)), pts)
            pygame.draw.lines(surface, (*P["smoke_glow"], a255), True, pts, 2)
        # 3) tick runik di pinggir
        for i in range(12):
            a = i * math.tau / 12.0 + self.age * 0.3
            x0 = self.x + math.cos(a) * r * 0.9
            y0 = cy + math.sin(a) * r * 0.42 * 0.9
            pygame.draw.line(surface, (*P["smoke_light"], a255),
                             (x0, y0),
                             (self.x + math.cos(a) * r * 0.97,
                              cy + math.sin(a) * r * 0.42 * 0.97), 2)
        # 4) genangan asap ungu
        _blit_faded(surface, ground_pool_surface(r, P["smoke_dark"], 0.45),
                    self.x, cy, int(a255 * 0.9))

    # ------------------------------------------------------------------
    # GAMBAR — DEPAN badan
    # ------------------------------------------------------------------
    def draw_front(self, surface):
        fn = getattr(self, "_fnt_" + self.skill, None)
        if fn is not None:
            fn(surface)

    def _fnt_q(self, surface):
        """Orb pengisian di ujung bilah sampai RELEASE."""
        t = self.t
        if t >= 0.46:
            return
        lp = (self.x + self.facing * 20.0 * self.scale, self.y - 8.0)
        if self.director is not None and self.director.unit is not None:
            try:
                lp = launch_point(self.director.unit, self.x, self.y)
            except Exception:                        # pragma: no cover
                pass
        grow = min(1.0, max(0.0, (t - 0.08) / 0.26))
        pulse = 0.8 + 0.2 * math.sin(self.age * 14.0)
        rr = int((6 + 10 * grow) * pulse)
        if rr < 2:
            return
        _blit_faded(surface, glow_surface(rr + 3, P["chaos_bright"], 1.0),
                    lp[0], lp[1], int(200 * grow), additive=True)
        _blit_faded(surface, glow_surface(max(2, rr // 2), P["fire_hot"], 1.0),
                    lp[0], lp[1], int(230 * grow), additive=True)
        pygame.draw.circle(surface, P["fire_white"], (int(lp[0]), int(lp[1])),
                           max(1, int(2 * grow)))

    def _fnt_w(self, surface):
        """Duri kekacauan yang MENJULUR dari tanah + kejut saat meledak."""
        t = self.t
        if t < 0.16:
            return
        r = self.r_screen(0.94)
        if t < 0.62:
            st = (t - 0.16) / 0.46
            n = 14
            h = int(self.r_screen(0.34) * _ease("oc", min(1.0, st * 1.4)))
            inv = int(235 * (1.0 - max(0.0, (t - 0.5) / 0.3)))
            if h > 3 and inv > 3:
                for i in range(n):
                    a = i * math.tau / n + _hash01(self.seed + i) * 0.3
                    sx = self.x + math.cos(a) * r
                    sy = self.y + 10 + math.sin(a) * r * 0.42
                    tipx = sx + math.cos(a) * h * 0.35
                    tipy = sy - h * (0.7 + _hash01(self.seed + i * 7) * 0.5)
                    wdt = max(1, int(2.5 * (1 - st * 0.5)))
                    pygame.draw.polygon(surface,
                                        (*P["chaos_darkest"], inv),
                                        [(sx - 3, sy + 2), (sx + 3, sy + 2),
                                         (tipx, tipy)])
                    pygame.draw.polygon(surface,
                                        (*P["chaos_bright"], inv),
                                        [(sx - 2, sy), (sx + 1, sy),
                                         (tipx, tipy + 2)])
                    _blit_faded(surface, ember_surface(3, P["fire_hot"]),
                                tipx, tipy, inv, additive=True)
        # shockwave ganda
        if t < 0.45:
            sw = (t - 0.16) / 0.29
            rr = int(r * (0.4 + 0.9 * _ease("oc", min(1.0, sw))))
            inv = int(190 * (1.0 - sw))
            if rr > 4 and inv > 3:
                _blit_faded(surface,
                            ellipse_ring_surface(rr, int(rr * 0.42),
                                                 max(1, int(3 * (1 - sw)) + 1),
                                                 P["chaos_bright"], 255),
                            self.x, self.y + 10, inv, additive=True)

    def _fnt_e(self, surface):
        """Kilat kejut saat dash mendarat + pita api di belakang."""
        t = self.t
        if 0.08 <= t < 0.60:
            off = dash_offset(self, t)
            k = body_scale(self.director.unit) if self.director is not None \
                and self.director.unit is not None else self.scale
            for i in range(4):
                back = off - self.facing * (i + 1) * 16.0 * k
                a = int(110 - i * 24)
                if a < 8:
                    continue
                _blit_faded(surface,
                            glow_surface(int(14 - i * 2), P["fire_bright"],
                                         0.5),
                            self.x + back, self.y + 4, a, additive=True)

    def _fnt_r(self, surface):
        """Hantu Phantasm: salinan rig (atau siluet prosedural) bergetar."""
        t = self.t
        if t < 0.16 or not self._phantoms:
            return
        fade = max(0.0, min(1.0, (1.0 - t) / 0.4))
        if fade <= 0.02:
            return
        R = _renderer()
        rig = getattr(R, "_last_rig", None) if R is not None else None
        rig_off = getattr(R, "_last_rig_off", (0, 0)) if R is not None \
            else (0, 0)
        for i, ph in enumerate(self._phantoms):
            side = ph["side"]
            bob = math.sin(self.age * 5.0 + ph["seed"]) * 4.0
            px = self.x + side * 26.0
            py = self.y - 8.0 + bob
            flick = 0.7 + 0.3 * math.sin(self.age * 21.0 + ph["seed"] * 3)
            a = int(120 * fade * flick)
            if a < 4:
                continue
            if rig is not None:
                try:
                    ghost = rig.copy()
                    ghost.fill((*P["smoke_light"], 255),
                               special_flags=pygame.BLEND_RGB_MULT)
                    ghost.set_alpha(a)
                    surface.blit(ghost, (int(px + rig_off[0] - side * 6),
                                         int(py + rig_off[1])))
                except Exception:                # pragma: no cover
                    pass
            else:
                self._draw_ghost_procedural(surface, px, py, side, a)
            # mata menyala
            pygame.draw.circle(surface, (*P["eye_bright"], min(255, a + 60)),
                               (int(px + side * 6), int(py - 26)), 2)
            _blit_faded(surface, glow_surface(7, P["eye_bright"], 0.8),
                        px + side * 6, py - 26, min(255, a), additive=True)

    @staticmethod
    def _draw_ghost_procedural(surface, px, py, side, a):
        """Siluet hantu sederhana (fallback tanpa rig renderer)."""
        col = (*P["smoke_mid"], a)
        pygame.draw.ellipse(surface, col,
                            (int(px - 18), int(py - 4), 36, 22))
        pygame.draw.ellipse(surface, col,
                            (int(px + side * 8), int(py - 14), 14, 14))
        pygame.draw.polygon(surface, col,
                            [(px - 16, py + 16), (px + 16, py + 16),
                             (px + 10, py + 30), (px - 10, py + 30)])
        pygame.draw.line(surface, (*P["chaos_bright"], a),
                         (int(px + side * 14), int(py - 10)),
                         (int(px + side * 26), int(py - 18)), 2)


# ============================================================================
# 12.  DASH — offset gerakan Chaos Strike (SATU sumber angka)
# ============================================================================

def _dash_offset_fallback(t):
    """Offset dash (px dunia, arah facing) untuk fraksi umur FX ``t``."""
    # pose E = 50 frame; puncak (engine progress 0.3-0.6) = jarak penuh
    if t < 0.26:
        return 80.0 * _ease("oc", t / 0.26)
    if t < 0.52:
        return 80.0
    if t < 0.86:
        return 80.0 * (1.0 - _ease("io", (t - 0.52) / 0.34))
    return 0.0


def dash_offset(skill_fx, t):
    """Offset dash skill E (px dunia, arah facing ditambahkan di caller).

    ``t`` adalah fraksi umur FX (0..1 spans total termasuk ekor AFTER).
    Renderer menghitung dalam PROGRESS ENGINE (0..1 spans SKILL_DUR),
    jadi ``t`` dikonversi dulu: ``engine = t / ENGINE_SPAN``. Fallback
    lokal memakai tabel dalam fraksi umur FX sehingga hasilnya identik.
    """
    R = _renderer()
    fn = getattr(R, "_dash_offset", None) if R is not None else None
    if fn is not None:
        try:
            eng = max(0.0, min(1.0, float(t) / SkillFX.ENGINE_SPAN))
            return float(fn(eng))
        except Exception:                        # pragma: no cover
            pass
    return _dash_offset_fallback(max(0.0, min(1.0, float(t))))


# ============================================================================
# 13.  FX DIRECTOR
# ============================================================================

class VokrahnFXDirector:
    """Mengikat trail, partikel, proyektil, skill, dampak, dan game feel
    untuk SATU Vokrahn (boss lane maupun hero lane)."""

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

        # pelacakan state animasi
        self.state = "IDLE"
        self.state_prev = "IDLE"
        self.state_time = 0.0
        self.state_priority = 0
        self.anim_frame = 0
        self.anim_time = 0.0

        # pelacakan serangan
        self.attack_progress = 0.0
        self.attack_prev = 0.0
        self.attack_phase = "RECOVERY"
        self.attack_active = False
        self.swing_done = False
        self.swing_count = 0
        self.melee = True          # Vokrahn selalu melee

        # pelacakan skill
        self.skill_key = None
        self.skill_prev = None
        self.skill_time = 0.0

        # lain-lain
        self.hurt_prev = 0
        self.ember_acc = 0.0
        self.dust_acc = 0.0
        self.afterimage_acc = 0.0
        self.time = 0.0
        self.dt = FIXED_DT
        self.last_impact_point = None
        self.draw_age = 99.0          # detik sejak terakhir digambar

    # ==================================================================
    # SINKRONISASI (dipanggil tiap frame gambar; posisi layar diketahui)
    # ==================================================================
    def sync(self, boss, x, y):
        self.unit = boss
        self.x = float(x)
        self.y = float(y)
        self.have_pos = True
        self.draw_age = 0.0
        _sync_palette()

        # -- state animasi --------------------------------------------
        st = getattr(boss, "_vok_state", None)
        if st is None:
            action, _phase, _ap = pose_of(boss)
            st = {"idle": "IDLE", "walk": "WALK", "run": "RUN",
                  "swing": "SWING", "attack": "ATTACK",
                  "q_cast": "SKILL", "w_cast": "SKILL",
                  "e_cast": "SKILL", "r_cast": "SPECIAL",
                  "hurt": "HURT", "death": "DEATH"}.get(action, "IDLE")
        if st != self.state:
            self.state_prev = self.state
            self.state = st
            self.state_time = 0.0
            self.anim_frame = 0
        self.state_priority = ANIM_STATES.get(st, 0)

        # -- progres serangan -----------------------------------------
        self.attack_prev = self.attack_progress
        ap = float(getattr(boss, "_vok_attack_progress", 0.0) or 0.0)
        self.attack_progress = ap
        self.attack_phase = attack_phase(ap)
        lo, hi = ATTACK_ACTIVE_WINDOW
        self.attack_active = lo <= ap <= hi

        action, _phase, _ap = pose_of(boss)
        self.melee = action in ("swing", "attack", "melee")
        swinging = action in ("swing", "attack", "melee")

        # -- trail senjata: rekam posisi bilah saat menyabet -----------
        if swinging and 0.12 <= ap <= 0.94:
            grip, hi_tip, _lo = sword_points(boss, x, y)
            self.trail.push(grip, hi_tip,
                            heat=1.0 if self.attack_active else 0.5)
            if self.attack_active:
                self.trail.hot = 1.0
        elif not swinging:
            self.trail.hot = max(0.0, self.trail.hot - 0.1)

        # -- momen impact tebasan --------------------------------------
        if swinging:
            crossed = self.attack_prev < ATTACK_IMPACT_FRAME <= ap
            if crossed and not self.swing_done:
                self.swing_done = True
                self.swing_count += 1
                self._melee_impact(boss, x, y)
            if ap < 0.1:
                self.swing_done = False
        else:
            self.swing_done = False

        # -- skill: deteksi mulai / selesai ---------------------------
        key = getattr(boss, "active_skill", None)
        if key not in ("q", "w", "e", "r"):
            key = None
        if key != self.skill_key:
            self.skill_prev = self.skill_key
            self.skill_key = key
            self.skill_time = 0.0
            if key is not None:
                self.start_skill(boss, key, x, y)
        # lifecycle FX dikunci ke timer skill engine (satu detak dgn AI)
        if key is not None:
            dur = float(SKILL_DUR.get(key, 50))
            timer = float(getattr(boss, "active_skill_timer", 0) or 0)
            prog = max(0.0, min(1.0, 1.0 - timer / max(1.0, dur)))
            for sk in self.skills:
                if sk.skill == key:
                    sk.set_engine_progress(prog)
        for sk in self.skills:
            sk.follow(x, y)

        # -- hurt flash -> percikan -----------------------------------
        hf = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        if hf > self.hurt_prev and hf > 0:
            self.spawn_hurt(boss, x, y)
        self.hurt_prev = hf

    # ==================================================================
    # UPDATE
    # ==================================================================
    def update(self, dt):
        dt = max(0.0, min(0.05, float(dt)))
        self.dt = dt
        self.time += dt
        self.state_time += dt
        self.anim_time += dt
        if self.anim_time >= 0.12:               # frame animasi nominal
            self.anim_time -= 0.12
            self.anim_frame += 1
        if self.skill_key:
            self.skill_time += dt

        self.draw_age += dt
        self.trail.update(dt)
        self.particles.update(dt)
        self.projectiles.update(dt)
        self.projectiles.update_impacts(dt)

        for sk in self.skills:
            sk.update(dt, self.particles, self.projectiles)
        if self.skills:
            self.skills = [s for s in self.skills if s.active]
            if len(self.skills) > MAX_SKILLS:
                del self.skills[0:len(self.skills) - MAX_SKILLS]

        for im in self.impacts:
            im.update(dt)
        if self.impacts:
            self.impacts = [i for i in self.impacts if i.active]
            if len(self.impacts) > MAX_IMPACTS:
                del self.impacts[0:len(self.impacts) - MAX_IMPACTS]

        for af in self.afterimages:
            af.update(dt)
        if self.afterimages:
            self.afterimages = [a for a in self.afterimages if a.active]

        self._ambient(dt)

    def _ambient(self, dt):
        """Bara dari bilah & debu dari kaki kuda: hidup tapi hemat.

        Berhenti OTOMATIS kalau unit sudah 0.5 s tidak digambar (mati /
        keluar layar), jadi tidak ada efek berumur tak terbatas.
        """
        if not self.have_pos or self.draw_age > 0.5:
            return
        rate = 7.0
        if self.skill_key == "r":
            rate = 16.0
        elif self.skill_key == "w":
            rate = 14.0
        elif self.state in ("WALK", "RUN"):
            rate = 10.0
        self.ember_acc += dt * rate
        while self.ember_acc >= 1.0:
            self.ember_acc -= 1.0
            if self.particles.count() > self.particles.cap * 0.8:
                break
            a = random.uniform(0, math.tau)
            r = random.uniform(6, 24)
            self.particles.spawn(
                self.x + math.cos(a) * r,
                self.y + 16 + math.sin(a) * r * 0.35,
                vx=random.uniform(-13, 13),
                vy=random.uniform(-70, -22),
                life=random.uniform(0.4, 1.0),
                size=random.uniform(1.1, 2.5),
                color=random.choice((P["ember"], P["fire_hot"],
                                     P["chaos_bright"])),
                shape="ember", additive=True, drag=0.5,
                layer="back" if random.random() < 0.5 else "front")
        # debu kaki kuda saat bergerak
        if self.state in ("WALK", "RUN") or self.skill_key == "e":
            self.dust_acc += dt * (16.0 if self.state == "RUN" else 8.0)
            while self.dust_acc >= 1.0:
                self.dust_acc -= 1.0
                if self.particles.count() > self.particles.cap * 0.85:
                    break
                self.particles.spawn(
                    self.x + random.uniform(-16, 16),
                    self.y + 30 + random.uniform(-3, 5),
                    vx=random.uniform(-24, 24), vy=random.uniform(-16, -4),
                    life=random.uniform(0.3, 0.6),
                    size=random.uniform(1.8, 3.6),
                    color=random.choice((P["dust"], P["ash"])),
                    shape="dust", additive=False, layer="back")

        # afterimage: dash (E), ultimate (R), atau sabetan aktif
        if self.skill_key in ("e", "r") or self.attack_active:
            self.afterimage_acc += dt
            if self.afterimage_acc >= 0.055:
                self.afterimage_acc = 0.0
                self.push_afterimage()

    # ==================================================================
    # KEJADIAN
    # ==================================================================
    def push_afterimage(self):
        R = _renderer()
        surf = getattr(R, "_last_rig", None) if R is not None else None
        if surf is None:
            return
        off = getattr(R, "_last_rig_off", (0, 0))
        if len(self.afterimages) >= MAX_AFTERIMAGES:
            self.afterimages.pop(0)
        tint = P["smoke_light"] if self.skill_key in ("e", "r") \
            else P["chaos_dark"]
        extra = 0.0
        if self.skill_key == "e":
            # dash: posisi LOGIS unit tidak ikut bergeser — ghost harus
            # digeser manual ke jalur dash supaya berekor mengikuti.
            for s in self.skills:
                if s.skill == "e":
                    extra = s.facing * dash_offset(s, s.t)
                    break
        self.afterimages.append(Afterimage(
            surf, self.x + off[0] + extra, self.y + off[1], 0.26, tint))

    def _melee_impact(self, boss, x, y):
        """Tebasan greatsword mendarat: flash + sabit + serpihan + feel."""
        grip, hi_tip, _lo = sword_points(boss, x, y)
        ang = math.atan2(hi_tip[1] - grip[1], hi_tip[0] - grip[0])
        px = hi_tip[0] + math.cos(ang) * 4.0
        py = hi_tip[1] + math.sin(ang) * 4.0
        self.last_impact_point = (px, py)
        self.add_impact(px, py, "melee", ang, 1.1, P["fire_bright"], 34.0)
        self.particles.burst(px, py, 6, speed=(120, 330),
                             life=(0.18, 0.44), size=(1.7, 4.2),
                             colors=(P["fire_bright"], P["fire_hot"],
                                     P["ember"]),
                             spread=1.5, direction=ang, gravity=310,
                             drag=1.1, shape="ember")
        self.particles.burst(px, py, 3, speed=(60, 180),
                             life=(0.25, 0.55), size=(1.6, 3.6),
                             colors=(P["metal_light"], P["arm_light"],
                                     P["ash"]),
                             spread=2.0, direction=ang, gravity=520,
                             shape="shard", rotation_speed=(-10, 10),
                             additive=False)
        self.particles.burst(x, y + 26, 3, speed=(50, 150),
                             life=(0.3, 0.6), size=(2.6, 5.4),
                             colors=(P["dust"], P["ash"]), spread=1.0,
                             direction=0.0 if hi_tip[0] >= x else math.pi,
                             gravity=140, shape="dust", additive=False)
        _feel_shake(3.2, 0.18)
        _feel_hit_stop(0.030)

    def start_skill(self, boss, key, x, y):
        """Mulai lifecycle FX untuk satu skill."""
        if key not in ("q", "w", "e", "r"):
            return None
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        k = body_scale(boss)
        fx = SkillFX(key, x, y, facing, getattr(boss, "target", None),
                     scale=k, director=self)
        if key == "e":
            # Chaos Strike: damage jatuh saat cast, visual = boss menggeser
            # 80 px ke depan. Titik "bidik" FX = titik pendaratan dash,
            # supaya lane telegraph, jalur, dan kejut mendarat di satu
            # tempat yang sama dengan sprite.
            fx.target_point = (x + facing * 80.0, y + 10.0)
        else:
            fx.target_point = target_point(boss, x, y)
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        self.skills.append(fx)
        return fx

    def spawn_bolt(self, boss, x, y, tx=None, ty=None):
        """Lepas Chaos Bolt dari ujung bilah (skill Q)."""
        lp = launch_point(boss, x, y)
        if tx is None or ty is None:
            tx, ty = target_point(boss, x, y)
        pr = self.projectiles.spawn_bolt(
            lp[0], lp[1], tx, ty, speed=BOLT_SPEED, radius=10.0,
            target=getattr(boss, "target", None), owner=boss,
            scale=body_scale(boss))
        ang = math.atan2(ty - lp[1], tx - lp[0])
        self.particles.burst(lp[0], lp[1], 4, speed=(70, 210),
                             life=(0.12, 0.32), size=(1.4, 3.2),
                             colors=(P["chaos_hot"], P["fire_hot"],
                                     P["fire_bright"]),
                             spread=1.3, direction=ang, drag=1.5,
                             shape="streak")
        self.add_impact(lp[0], lp[1], "skill", ang, 0.45, P["chaos_hot"],
                        16.0)
        _feel_shake(1.1, 0.09)
        return pr

    def spawn_hurt(self, boss, x, y):
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        self.particles.burst(x - facing * 7, y - 14, 5, speed=(90, 230),
                             life=(0.2, 0.45), size=(1.5, 3.4),
                             colors=(P["metal_light"], P["fire_bright"],
                                     P["chaos_bright"]),
                             spread=2.2,
                             direction=math.pi if facing > 0 else 0.0,
                             gravity=320, drag=1.0, shape="spark")
        self.add_impact(x - facing * 9, y - 14, "skill",
                        math.pi if facing > 0 else 0.0, 0.5,
                        P["arm_high"], 24.0)

    def add_impact(self, x, y, kind="skill", angle=0.0, power=1.0,
                   color=None, radius=44.0):
        while len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        im = ImpactFX(x, y, kind, angle, power, color, radius)
        self.impacts.append(im)
        return im

    # ==================================================================
    # GAMBAR
    # ==================================================================
    def draw_ground(self, surface):
        """Di BAWAH badan: telegraph skill, jalur, afterimage, partikel
        belakang."""
        for sk in self.skills:
            sk.draw_ground(surface)
        for af in self.afterimages:
            af.draw(surface)
        self.particles.draw(surface, layer="back")

    def draw_front(self, surface):
        """Di ATAS badan: trail, proyektil, partikel depan, skill FX depan,
        dampak."""
        self.trail.draw(surface)
        self.projectiles.draw(surface)
        self.particles.draw(surface, layer="front")
        for sk in self.skills:
            sk.draw_front(surface)
        self.projectiles.draw_impacts(surface)
        for im in self.impacts:
            im.draw(surface)

    # ==================================================================
    # INFO
    # ==================================================================
    def count_particles(self):
        return self.particles.count()

    def stats(self):
        return {
            "particles": self.particles.count(),
            "projectiles": self.projectiles.count(),
            "skills": len(self.skills),
            "impacts": len(self.impacts) + len(self.projectiles.impacts),
            "afterimages": len(self.afterimages),
            "trail": len(self.trail.history),
            "state": self.state,
            "frame": self.anim_frame,
            "attack_progress": round(self.attack_progress, 3),
            "attack_phase": self.attack_phase,
            "swings": self.swing_count,
        }

    def reset(self):
        self.particles.clear()
        self.projectiles.clear()
        self.trail.reset()
        self.skills.clear()
        self.impacts.clear()
        self.afterimages.clear()
        self.swing_done = False
        self.skill_key = None
        self.have_pos = False


# ============================================================================
# 14.  REGISTRI DIRECTOR
#      Pola SAMA dengan heroes/zharok_fx.py: director menempel di unit
#      (``_vokrahn_fx``), daftar global dipakai tick() + reset_all().
# ============================================================================

_DIRECTORS = []
MAX_DIRECTORS = 12


def director_for(unit):
    """Ambil (atau buat) director FX untuk satu unit Vokrahn."""
    _sync_palette()
    d = getattr(unit, "_vokrahn_fx", None)
    if d is None:
        d = VokrahnFXDirector(unit)
        try:
            unit._vokrahn_fx = d
        except Exception:                        # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > MAX_DIRECTORS:
            _release(_DIRECTORS.pop(0))
    return d


def _release(director):
    try:
        if director.unit is not None:
            director.unit._vokrahn_fx = None
            director.unit._vok_live_fx = False
    except Exception:                            # pragma: no cover
        pass
    director.reset()


def attach(unit):
    """Pasang lapisan hidup pada unit (dipanggil pipeline render)."""
    if not VOKRAHN_FX_ENABLED or unit is None:
        return False
    try:
        director_for(unit)
    except Exception:                            # pragma: no cover
        return False
    try:
        unit._vok_live_fx = True
    except Exception:                            # pragma: no cover
        return False
    return True


def owns(unit):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not VOKRAHN_FX_ENABLED or unit is None:
        return False
    if not getattr(unit, "_vok_live_fx", False):
        return False
    d = getattr(unit, "_vokrahn_fx", None)
    return d is not None and d in _DIRECTORS


def recently_drawn(unit, max_age=0.35):
    """True kalau lapisan hidup unit ini BENAR-BENAR digambar belakangan.

    Dipakai renderer sebagai pengaman: di lane hero, yang memanggil
    ``draw_ground_layer`` / ``draw_live_layer`` adalah pipeline
    ``heroes/__init__``, bukan renderer.  Kalau ternyata tidak ada yang
    menggambarnya (mis. renderer dipanggil langsung oleh alat uji atau
    integrasi lain), renderer TIDAK boleh mematikan fallback canvas —
    kalau tidak, karakter kehilangan seluruh FX-nya diam-diam.
    """
    d = getattr(unit, "_vokrahn_fx", None)
    if d is None:
        return False
    return bool(d.have_pos) and d.draw_age <= float(max_age)


def tick(dt=None):
    """Majukan waktu FX satu frame nyata; aman dipanggil berkali-kali.

    Tanpa argumen, dt diambil dari bus game-feel (``fx_dt``) yang sudah
    memperhitungkan hit-stop; bus itu hanya menghasilkan dt > 0 sekali per
    frame nyata, jadi memanggil tick() dari beberapa unit dalam satu frame
    TIDAK mempercepat simulasi.
    """
    if not VOKRAHN_FX_ENABLED:
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
    """Bersihkan seluruh state FX Vokrahn (ganti level / keluar match)."""
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()
    clear_cache()
    if _feel is not None:
        try:
            _feel.reset()
        except Exception:                        # pragma: no cover
            pass


def total_particles():
    """Jumlah partikel Vokrahn yang hidup (HUD performa + tes)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def stats():
    """Ringkasan global untuk overlay debug / profiling."""
    out = {"directors": len(_DIRECTORS), "particles": 0, "projectiles": 0,
           "skills": 0, "impacts": 0, "afterimages": 0,
           "cache": cache_size()}
    for d in _DIRECTORS:
        s = d.stats()
        out["particles"] += s["particles"]
        out["projectiles"] += s["projectiles"]
        out["skills"] += s["skills"]
        out["impacts"] += s["impacts"]
        out["afterimages"] += s["afterimages"]
    if _feel is not None:
        try:
            out.update(_feel.stats())
        except Exception:                        # pragma: no cover
            pass
    return out


def projectiles_for(unit):
    """Daftar proyektil milik unit (dipakai overlay debug & tes)."""
    d = getattr(unit, "_vokrahn_fx", None)
    if d is None:
        return []
    return d.projectiles.projectiles


# ============================================================================
# 15.  API GAMBAR — dipanggil renderer bosses/level4.py
#      Urutan kanonik: GROUND -> (badan digambar renderer) -> LIVE.
# ============================================================================

def draw_ground_layer(surface, unit, x, y):
    """Lapisan BAWAH badan: telegraph skill, jalur, afterimage, partikel
    belakang.  Juga memajukan simulasi satu frame."""
    if not VOKRAHN_FX_ENABLED or unit is None:
        return
    if not attach(unit):
        return
    d = director_for(unit)
    d.sync(unit, x, y)
    tick()
    d.draw_ground(surface)


def draw_live_layer(surface, unit, x, y):
    """Lapisan ATAS badan: trail sabetan, proyektil, partikel depan,
    skill FX depan, dampak, lalu overlay debug.  Dipanggil PALING AKHIR."""
    if not VOKRAHN_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if not d.have_pos or d.x != x or d.y != y:
        d.sync(unit, x, y)
    d.draw_front(surface)
    if DEBUG_CHARACTER:
        draw_debug_overlay(surface, d)


# ============================================================================
# 16.  NOTIFIKASI — dipanggil AI (bosses/base_boss.py) & renderer
# ============================================================================

def notify_melee_impact(unit, target=None, damage=0, crit=False,
                        x=None, y=None, angle=None):
    """Greatsword mendarat pada target (serangan dasar — selalu melee)."""
    if not VOKRAHN_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    try:
        power = 0.8 + min(1.6, float(damage) / 85.0)
    except (TypeError, ValueError):
        power = 1.0
    if crit:
        power *= 1.35
    if x is None or y is None:
        if target is not None:
            x = float(getattr(target, "x", d.x))
            y = float(getattr(target, "y", d.y)) - 6.0
        elif d.have_pos:
            d._melee_impact(unit, d.x, d.y)
            return
        else:
            return
    if angle is None:
        angle = math.atan2(float(y) - d.y, float(x) - d.x)
    d.add_impact(x, y, "melee", angle, power, P["fire_bright"], 34.0)
    d.particles.burst(x, y, 6, speed=(120, 330), life=(0.18, 0.44),
                      size=(1.7, 4.2),
                      colors=(P["fire_bright"], P["fire_hot"], P["ember"]),
                      spread=1.5, direction=angle, gravity=310, drag=1.1,
                      shape="ember")
    d.particles.burst(x, y, 3, speed=(60, 180), life=(0.25, 0.55),
                      size=(1.6, 3.6),
                      colors=(P["metal_light"], P["ash"], P["dust"]),
                      spread=2.0, direction=angle, gravity=520,
                      shape="shard", rotation_speed=(-10, 10),
                      additive=False)
    _feel_shake(6.5 * power, 0.18)
    _feel_hit_stop(0.05 if not crit else 0.07)


def notify_projectile_impact(unit, x, y, angle=0.0, damage=0, crit=False,
                             kind="bolt"):
    """Chaos Bolt / Chaos Brand mengenai target: paket impact lengkap."""
    if not VOKRAHN_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    try:
        power = 0.7 + min(1.6, float(damage) / 60.0)
    except (TypeError, ValueError):
        power = 1.0
    if crit:
        power *= 1.3
    is_brand = (kind == "brand")
    d.add_impact(x, y, "brand" if is_brand else "bolt", angle, power,
                 P["chaos_hot"] if is_brand else P["chaos_bright"],
                 52.0 if is_brand else 36.0)
    d.particles.burst(x, y, 6, speed=(80, 250), life=(0.2, 0.5),
                      size=(1.6, 4.0),
                      colors=(P["chaos_bright"], P["fire_bright"],
                              P["fire_hot"], P["ember"]),
                      spread=2.4, direction=angle + math.pi, gravity=250,
                      drag=1.0, shape="ember")
    d.particles.burst(x, y, 4, speed=(20, 70), life=(0.35, 0.75),
                      size=(2.5, 5), colors=(P["ash"], P["dust"]),
                      gravity=-50, shape="smoke", additive=False)
    _feel_shake((6.0 if is_brand else 3.8) * power, 0.14)
    _feel_hit_stop(0.045 if is_brand else 0.032)


def notify_skill_cast(unit, skill, x=None, y=None):
    """Skill mulai di-cast: buat lifecycle FX + guncangan awal."""
    if not VOKRAHN_FX_ENABLED or unit is None:
        return None
    key = str(skill).lower()
    if key not in SKILL_DUR:
        return None
    d = director_for(unit)
    if x is None or y is None:
        if d.have_pos:
            x, y = d.x, d.y
        else:
            # posisi layar belum diketahui: biarkan sync() yang memulai
            d.skill_key = None
            return None
    if d.skill_key == key and d.skills and d.skills[-1].age <= 0.06:
        return d.skills[-1]
    d.skill_key = key
    d.skill_time = 0.0
    return d.start_skill(unit, key, float(x), float(y))


def notify_skill_impact(unit, x=None, y=None, radius=None, skill="q"):
    """Momen damage skill pada titik (x, y).

    AI memanggil ``notify_skill_cast`` lalu ``notify_skill_impact`` pada
    tick yang sama; SkillFX yang baru dibuat di-update DI TEMPAT (arah +
    radius final) supaya efeknya tidak digambar dobel.
    """
    if not VOKRAHN_FX_ENABLED or unit is None:
        return
    key = str(skill).lower()
    d = director_for(unit)
    if x is None or y is None:
        if not d.have_pos:
            return
        x, y = d.x, d.y + 22
    fx = None
    for s in d.skills:
        if s.skill == key and s.age <= 0.06:
            fx = s
            break
    if fx is None:
        fx = d.start_skill(unit, key, d.x if d.have_pos else float(x),
                           d.y if d.have_pos else float(y))
    if fx is not None:
        fx.target_point = (float(x), float(y))
        if radius:
            fx.radius = float(radius)
    power = 2.1 if key == "r" else 1.4
    color = P["smoke_glow"] if key == "r" else P["chaos_bright"]
    rr = float(radius) if radius else {"q": 70.0, "w": 90.0, "e": 60.0,
                                       "r": 150.0}.get(key, 70.0)
    d.add_impact(x, y, "skill", 0.0, power, color, rr)
    d.particles.burst(x, y, 12 if key != "r" else 20, speed=(90, 300),
                      life=(0.25, 0.6), size=(2, 5),
                      colors=(P["chaos_bright"], P["fire_bright"],
                              P["ember"]),
                      gravity=300, drag=0.8, shape="ember")
    _feel_shake({"q": 5.0, "w": 8.0, "e": 10.0,
                 "r": 14.0}.get(key, 6.0), 0.22)
    _feel_hit_stop({"q": 0.035, "w": 0.045, "e": 0.055,
                    "r": 0.07}.get(key, 0.04))


def notify_projectile_cast(unit, x, y, tx=None, ty=None):
    """Lepas Chaos Bolt dari ujung bilah (skill Q).

    Renderer memanggil ini saat frame cast aktif dan lapisan hidup sudah
    mengambil alih proyektil; menggantikan ``_spawn_chaos_bolt`` versi
    canvas.
    """
    if not VOKRAHN_FX_ENABLED or unit is None:
        return None
    d = director_for(unit)
    d.sync(unit, x, y)
    return d.spawn_bolt(unit, x, y, tx, ty)


def notify_hurt(unit, amount=1.0, x=None, y=None):
    """Unit terkena damage: percikan serpihan + kilat kecil."""
    if not VOKRAHN_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if x is None or y is None:
        if not d.have_pos:
            return
        x, y = d.x, d.y
    d.spawn_hurt(unit, x, y)


def notify_death(unit, x=None, y=None):
    """Kematian: bara + serpihan + asap + bintang chaos + guncangan."""
    if not VOKRAHN_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if x is None or y is None:
        if not d.have_pos:
            return
        x, y = d.x, d.y
    d.add_impact(x, y, "brand", 0.0, 1.8, P["chaos_hot"], 120.0)
    d.particles.burst(x, y, 14, speed=(120, 420), life=(0.4, 1.0),
                      size=(2, 6),
                      colors=(P["fire_hot"], P["fire_bright"], P["ember"],
                              P["chaos_bright"]),
                      spread=math.tau, gravity=340, drag=0.7, shape="ember")
    d.particles.burst(x, y, 7, speed=(70, 260), life=(0.5, 1.1),
                      size=(1.8, 4.0),
                      colors=(P["metal_light"], P["arm_mid"],
                              P["arm_high"]),
                      spread=math.tau, gravity=620, shape="shard",
                      rotation_speed=(-12, 12), additive=False)
    d.particles.burst(x, y, 4, speed=(30, 120), life=(0.6, 1.2),
                      size=(4, 8), colors=(P["ash"], P["smoke_mid"]),
                      spread=math.tau, gravity=-40, shape="smoke",
                      additive=False)
    _feel_shake(7.5, 0.48)
    _feel_hit_stop(0.040)


def _feel_shake(strength, duration):
    if _feel is None or not shake_allowed():
        return
    try:
        _feel.shake(strength, duration)
    except Exception:                            # pragma: no cover
        pass


def _feel_hit_stop(seconds):
    """Hit-stop SELALU dijepit ke jendela yang diminta: 0.03 - 0.08 s."""
    if _feel is None:
        return
    try:
        _feel.hit_stop(max(0.03, min(0.08, float(seconds))))
    except Exception:                            # pragma: no cover
        pass


# ============================================================================
# 17.  OVERLAY DEBUG  (DEBUG_CHARACTER = True)
# ============================================================================

_DBG_FONT = [None]


def _dbg_font():
    if _DBG_FONT[0] is None:
        try:
            if not pygame.font.get_init():
                pygame.font.init()
            _DBG_FONT[0] = pygame.font.SysFont("consolas,monospace", 11)
        except Exception:                        # pragma: no cover
            _DBG_FONT[0] = False
    return _DBG_FONT[0] or None


def draw_debug_overlay(surface, director):
    """Hitbox pedang, hurtbox, attack range + MELEE_REACH, tabrakan
    proyektil, state animasi, frame, FPS, jumlah partikel, state skill,
    timer serangan."""
    d = director
    if d is None or not d.have_pos:
        return
    unit = d.unit
    x, y = d.x, d.y
    k = body_scale(unit) if unit is not None else 1.0

    # -- jangkauan serangan (elips tanah) -----------------------------
    rng = float(getattr(unit, "attack_range",
                        getattr(unit, "range", 55)) or 55)
    rng = rng / max(0.05, k)
    _blit_faded(surface, ellipse_ring_surface(int(rng), int(rng * 0.4), 1,
                                              (90, 200, 255), 255),
                x, y + 30, 130)

    # -- jangkauan tebasan ---------------------------------------------
    mr = MELEE_REACH / max(0.05, k)
    _blit_faded(surface, ellipse_ring_surface(int(mr), int(mr * 0.4), 1,
                                              (255, 160, 80), 255),
                x, y + 30, 120)

    # -- radius skill aktif -------------------------------------------
    if d.skill_key:
        rr = WORLD_RADIUS.get(d.skill_key, 150.0) / max(0.05, k)
        _blit_faded(surface, ellipse_ring_surface(int(rr), int(rr * 0.4), 1,
                                                  (255, 120, 120), 255),
                    x, y + 30, 120)

    # -- hurtbox (badan) ------------------------------------------------
    hw = int(26 * k)
    hh = int(66 * k)
    pygame.draw.rect(surface, (70, 240, 120),
                     pygame.Rect(int(x - hw), int(y - hh + 10), hw * 2,
                                 hh + 18), 1)

    # -- hitbox pedang pada jendela aktif ------------------------------
    lo, hi = ATTACK_ACTIVE_WINDOW
    active = lo <= d.attack_progress <= hi
    col = (255, 80, 80) if active else (150, 150, 160)
    if unit is not None:
        grip, tip_hi, tip_lo = sword_points(unit, x, y)
        pygame.draw.line(surface, col, (int(tip_lo[0]), int(tip_lo[1])),
                         (int(tip_hi[0]), int(tip_hi[1])),
                         2 if active else 1)
        pygame.draw.circle(surface, col, (int(tip_hi[0]), int(tip_hi[1])),
                           max(2, int(13 * k)), 1)
        pygame.draw.circle(surface, (240, 240, 90),
                           (int(grip[0]), int(grip[1])), 2, 1)

    # -- tabrakan proyektil ---------------------------------------------
    for pr in d.projectiles.projectiles:
        pygame.draw.circle(surface, (255, 220, 90),
                           (int(pr.position.x), int(pr.position.y)),
                           max(1, int(pr.radius)), 1)
        pygame.draw.line(surface, (255, 220, 90),
                         (int(pr.position.x), int(pr.position.y)),
                         (int(pr.destination.x), int(pr.destination.y)), 1)

    # -- jangkar + sumbu --------------------------------------------------
    pygame.draw.line(surface, (255, 255, 255), (int(x) - 6, int(y)),
                     (int(x) + 6, int(y)), 1)
    pygame.draw.line(surface, (255, 255, 255), (int(x), int(y) - 6),
                     (int(x), int(y) + 6), 1)

    # -- teks --------------------------------------------------------------
    font = _dbg_font()
    if font is None:
        return
    fps = 1.0 / max(0.0001, d.dt)
    st = d.stats()
    sk = d.skills[-1] if d.skills else None
    lines = [
        "VOKRAHN [debug]",
        "state %s <- %s (p%d)" % (st["state"], d.state_prev,
                                  d.state_priority),
        "frame %d  t %.2fs  dt %.4f" % (st["frame"], d.state_time, d.dt),
        "attack %.2f %s%s" % (st["attack_progress"], st["attack_phase"],
                              "  <HIT>" if active else ""),
        "atk timer %s  cd %s" % (getattr(unit, "timer", "-"),
                                 getattr(unit, "attack_cooldown", "-")),
        "skill %s/%s t%.2f  boss_timer %s" % (
            d.skill_key or "-", sk.phase if sk else "-", d.skill_time,
            getattr(unit, "active_skill_timer", "-")),
        "part %d/%d  proj %d  fx %d" % (st["particles"], d.particles.cap,
                                        st["projectiles"], st["impacts"]),
        "fps %.0f  cache %d  swing %d" % (fps, cache_size(),
                                          st["swings"]),
    ]
    pad = 4
    w = max(font.size(t)[0] for t in lines) + pad * 2
    h = len(lines) * 13 + pad * 2
    box = pygame.Surface((w, h), pygame.SRCALPHA)
    box.fill((10, 8, 12, 190))
    pygame.draw.rect(box, (255, 120, 160, 200), box.get_rect(), 1)
    for i, t in enumerate(lines):
        box.blit(font.render(t, True, (255, 224, 190)), (pad, pad + i * 13))
    surface.blit(box, (int(x) + 46, int(y) - 100))


# ============================================================================
# 18.  API PUBLIK
# ============================================================================

__all__ = [
    "DEBUG_CHARACTER", "VOKRAHN_FX_ENABLED", "VOKRAHN_PALETTE",
    "MAX_PARTICLES", "MAX_PROJECTILES", "TRAIL_SAMPLES", "MAX_IMPACTS",
    "MAX_SKILLS", "MAX_AFTERIMAGES",
    "ATTACK_PHASES", "ATTACK_ACTIVE_WINDOW", "ATTACK_IMPACT_FRAME",
    "ANIM_STATES", "SKILL_PHASES", "SKILL_DUR", "SKILL_TOTAL",
    "WORLD_RADIUS", "BOLT_SPEED", "BRAND_SPEED", "PHANTOM_COUNT",
    "MELEE_REACH", "SWORD_ARC",
    "Particle", "ParticleSystem", "SwingTrail", "ImpactFX", "Afterimage",
    "BaseProjectile", "ChaosBoltProjectile", "ChaosBrandProjectile",
    "ProjectileSystem", "SkillFX", "VokrahnFXDirector",
    "attach", "owns", "recently_drawn", "director_for", "projectiles_for",
    "tick", "reset_all", "total_particles", "stats",
    "draw_ground_layer", "draw_live_layer", "draw_debug_overlay",
    "notify_melee_impact", "notify_projectile_cast",
    "notify_projectile_impact", "notify_skill_cast",
    "notify_skill_impact", "notify_hurt", "notify_death",
    "sword_arc", "sword_points", "sword_tip", "sword_angle",
    "launch_point", "attack_phase", "skill_phase", "pose_of",
    "render_scale", "body_scale", "screen_point", "target_point",
    "ring_radius", "dash_offset",
    "particle_budget", "glow_allowed", "shake_allowed",
    "glow_surface", "ring_surface", "ellipse_ring_surface",
    "ground_pool_surface", "ember_surface", "arc_ring_surface",
    "spike_ring_surface", "shard_poly", "flame_poly", "spark_star",
    "chevron", "crack_points", "star_poly_points", "chaos_star_points",
    "taper_lane", "blit_add",
    "clear_cache", "cache_size",
]
