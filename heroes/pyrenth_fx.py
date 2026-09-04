# ============================================================================
# heroes/pyrenth_fx.py
# ----------------------------------------------------------------------------
# PYRENTH — THE DEVOURER  ·  LAPISAN TEMPUR HIDUP (v3)
#
# Rangka kerja ini adalah pasangan dari renderer ``bosses/level4.py ::
# _NS_pyrenth``.  Pembagian tugasnya tegas:
#
#   renderer  -> SATU-SATUNYA pemilik geometri badan & pedang api (rig
#                demon lord bersayap, palet, pose, controller animasi,
#                ARK bilah, telegraph fallback)
#   modul ini -> SEMUA yang hidup di RUANG LAYAR skala 1:1 — swing trail,
#                particle system, proyektil (Doom Bolt & Soul Ember),
#                skill FX q/w/e/r, impact FX, afterimage, overlay debug
#   combat_feel -> bus global hit-stop & screen shake (dipakai bersama)
#
# Kenapa dipisah?  Di lane hero, sprite badan di-*cache* lalu
# ``smoothscale``-kan.  Efek apa pun yang digambar ke canvas badan ikut
# BEKU dan ikut MENYUSUT.  Dengan memisahkan lapisan hidup ke ruang layar,
# trail/partikel/proyektil selalu 60 fps sejati dan selalu setajam layar.
#
# Modul ini TIDAK pernah menghitung ulang pose.  Ia MEMBACA
# ``_NS_pyrenth.blade_geometry()`` / ``_blade_arc()`` / ``_pyr_state``
# lewat jembatan malas ``_renderer()``, jadi bilah dan trail-nya
# mustahil berbeda satu frame pun.
#
# Kosakata skill Pyrenth (dikontrakkan dengan ``base_boss._cast_pyrenth_*``):
#
#   Q  DOOM            rantai api mengunci satu target       (320 dmg)
#   W  DEVOUR          sedot jiwa + heal 8% max HP           (self)
#   E  SCORCHED EARTH  erupsi duri api radius 180            (380 dmg)
#   R  INFERNAL BLADE  tebasan ultimate radius 220           (550 dmg)
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
PYRENTH_FX_ENABLED = True

#: Cap keras — tidak ada satu pun sistem yang boleh tumbuh tanpa batas.
MAX_PARTICLES = 200
MAX_PROJECTILES = 22
TRAIL_SAMPLES = 10
MAX_IMPACTS = 9
MAX_SKILLS = 5
MAX_AFTERIMAGES = 7

FIXED_DT = 1.0 / 60.0

#: Kecepatan proyektil (px dunia / detik).
DOOM_SPEED = 760.0           # Q — Doom Bolt (rantai api mengunci target)
EMBER_SPEED = 250.0          # W — Soul Ember (jiwa tersedot ke Pyrenth)

#: Durasi pose skill dalam FRAME — HARUS sama dengan
#: ``base_boss._cast_pyrenth_*`` (active_skill_timer) dan
#: ``_NS_pyrenth.SKILL_DUR``.
SKILL_DUR = {"q": 50, "w": 40, "e": 60, "r": 70}

#: Durasi lifecycle FX (detik) — sedikit lebih panjang dari pose supaya
#: tahap AFTER (asap/bara sisa) sempat memudar dengan wajar.
SKILL_TOTAL = {"q": 1.25, "w": 1.10, "e": 1.60, "r": 1.90}

#: Radius efek di RUANG DUNIA — sama persis dengan radius damage AI di
#: ``bosses/base_boss.py``: ``_cast_pyrenth_e`` 180, ``_cast_pyrenth_r``
#: 220, Q jangkauan bidik 200, W jangkauan sedot jiwa 200.  Dikunci oleh
#: tes regresi ``tools/test_pyrenth_v3_combat.py``.
WORLD_RADIUS = {"q": 200.0, "w": 200.0, "e": 180.0, "r": 220.0}

#: Jumlah jiwa yang dicabut W (Devour) dan disedot ke inti Pyrenth.
SPIRIT_COUNT = 3

#: Jarak dunia (px) di bawahnya tebasan pedang api dianggap melee.
#: Pyrenth murni melee (range 55 di boss_data) — angka ini dipakai
#: ``_NS_pyrenth`` dan hook benturan ``base_boss`` agar animasi dan
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
#: ayunan BLADE_ARC) DAN lapisan hidup (momen impact) — satu angka.
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

#: ARK bilah api — IDENTIK dengan ``_NS_pyrenth.BLADE_ARC`` (tabel cadangan
#: kalau renderer gagal diimpor; tes mengunci keduanya sama).
#:
#: ``(t0, t1, phi0, phi1, ease)`` — ``phi`` = sudut pedang dari sumbu
#: DEPAN (+x arah facing, orientasi matematis y-atas).  Loop tertutup:
#: phi(0) == phi(1) dan langkah maksimum < 0.30 rad per 1/200 progres,
#: jadi bilah tidak pernah teleport.
BLADE_ARC = (
    (0.00, 0.12,  0.96,  2.18, "out"),    # ANGKAT: jagaan -> atas-belakang
    (0.12, 0.30,  2.18,  2.88, "io"),     # WIND-UP: horizontal belakang
    (0.30, 0.50,  2.88, -1.31, "oc"),     # SWING: sapuan overhead ke depan
    (0.50, 0.62, -1.31, -1.05, "hold"),   # IMPACT: pendaran + recoil
    (0.62, 0.82, -1.05, -0.44, "io"),     # FOLLOW THROUGH
    (0.82, 1.00, -0.44,  0.96, "io"),     # RECOVERY: kembali ke jagaan
)

#: Setengah panjang bilah & offset grip (px LAYAR, render_scale 1) —
#: cadangan dari rig renderer (rig 48 px x SCALE 0.62).
_BLADE_HALF_FALLBACK = 29.8
_GRIP_FALLBACK = (26.0, -8.7)


# ============================================================================
# 2.  PALETTE — Demon Lord api (disinkronkan dari renderer)
# ============================================================================
#
# Palet Pyrenth memakai 9 kunci kontrak (outline / shadow / dark / body /
# mid / light / highlight / weapon / fx) DI ATAS band-band tematik:
# kulit iblis merah-magma, retakan molten, api 7 band, membran sayap,
# tanduk tulang, baja hitam, dan jiwa ungu (khusus DEVOUR).

PYRENTH_PALETTE = {
    # Kulit iblis 6-band (merah gelap -> magma)
    "skin_darkest":    (25,   8,   8),
    "skin_dark":       (75,  22,  18),
    "skin_mid":        (135, 45,  25),
    "skin_light":      (195, 85,  35),
    "skin_high":       (235, 135, 55),
    "skin_shine":      (255, 190, 100),

    # Retakan molten 6-band (urat magma yang menyala di kulit & bilah)
    "molten_darkest":  (60,  15,   5),
    "molten_dark":     (155, 45,  10),
    "molten_mid":      (230, 90,  15),
    "molten_bright":   (255, 145, 40),
    "molten_hot":      (255, 200, 80),
    "molten_glow":     (255, 235, 145),

    # Api 7-band (bilah, semburan, erupsi)
    "fire_darkest":    (60,  15,   5),
    "fire_dark":       (140, 35,  10),
    "fire_mid":        (220, 75,  20),
    "fire_bright":     (255, 125, 35),
    "fire_hot":        (255, 180, 65),
    "fire_glow":       (255, 220, 130),
    "fire_white":      (255, 250, 210),

    # Kain cawat / ikat pinggang (gelap)
    "cape_darkest":    (15,   8,   8),
    "cape_dark":       (45,  22,  18),
    "cape_mid":        (85,  40,  25),
    "cape_light":      (125, 58,  34),

    # Membran sayap kelelawar 5-band
    "horse_darkest":   (18,   8,  10),
    "horse_dark":      (55,  20,  22),
    "horse_mid":       (100, 40,  35),
    "horse_light":     (155, 70,  50),
    "horse_high":      (196, 104, 72),

    # Tanduk / tulang 5-band
    "mane_darkest":    (25,  18,  15),
    "mane_dark":       (55,  42,  35),
    "mane_mid":        (95,  78,  62),
    "mane_bright":     (150, 130, 100),
    "mane_hot":        (210, 195, 165),

    # Baja hitam & emas
    "arm_darkest":     (8,    8,  12),
    "arm_dark":        (28,  25,  32),
    "arm_mid":         (60,  55,  65),
    "arm_light":       (110, 105, 118),
    "arm_high":        (150, 145, 158),
    "arm_shine":       (170, 165, 178),
    "metal_darkest":   (18,  15,  18),
    "metal_dark":      (48,  45,  55),
    "metal_mid":       (100, 95, 110),
    "metal_edge":      (250, 250, 255),
    "metal_light":     (170, 165, 180),
    "metal_shine":     (225, 220, 235),
    "gold_dark":       (95,  62,  15),
    "gold_mid":        (180, 130, 40),
    "gold_light":      (235, 190, 80),

    # Mata menyala oranye
    "eye_dark":        (75,  20,   5),
    "eye_bright":      (255, 140, 40),
    "eye_hot":         (255, 220, 130),

    # JIWA — hijau-toska pucat, khusus W (DEVOUR).  Sengaja BUKAN oranye
    # supaya sedotan jiwa langsung terbaca berbeda dari api biasa.
    "soul_dark":       (6,   30,  28),
    "soul_mid":        (26,  92,  84),
    "soul_light":      (96,  200, 178),
    "soul_glow":       (188, 255, 236),

    # Turunan FX
    "ember":           (255, 152,  50),
    "ash":             (92,   72,  66),
    "dust":            (124, 100,  84),
    "shadow_deep":     (3,    2,   3),

    # 9 KUNCI KONTRAK
    "outline":         (12,   5,   5),
    "shadow":          (3,    2,   3),
    "dark":            (75,  22,  18),
    "body":            (135, 45,  25),
    "mid":             (195, 85,  35),
    "light":           (235, 135, 55),
    "highlight":       (255, 190, 100),
    "weapon":          (255, 125, 35),
    "fx":              (255, 145, 40),
}

#: Alias kerja — sinkron dengan renderer saat modul dipakai pertama kali.
P = dict(PYRENTH_PALETTE)

#: Kunci FX -> kunci palet renderer (``_NS_pyrenth.PALETTE``).  Kalau
#: renderer mengubah warna, lapisan hidup ikut berubah TANPA edit ganda.
#: ``horse_*`` di lapisan ini adalah MEMBRAN SAYAP (``wing_*``) dan
#: ``mane_*`` adalah TANDUK/TULANG (``horn_*``) — nama generiknya
#: dipertahankan supaya struktur kode paritas dengan modul FX lain.
_PALETTE_SYNC = {
    "skin_darkest": "skin_darkest", "skin_dark": "skin_dark",
    "skin_mid": "skin_mid", "skin_light": "skin_light",
    "skin_high": "skin_high", "skin_shine": "skin_shine",
    "molten_darkest": "fire_darkest", "molten_dark": "molten_dark",
    "molten_mid": "molten_mid", "molten_bright": "molten_bright",
    "molten_hot": "molten_hot", "molten_glow": "molten_glow",
    "fire_darkest": "fire_darkest", "fire_dark": "fire_dark",
    "fire_mid": "fire_mid", "fire_bright": "fire_bright",
    "fire_hot": "fire_hot", "fire_glow": "fire_glow",
    "fire_white": "fire_white",
    "cape_darkest": "cloth_darkest", "cape_dark": "cloth_dark",
    "cape_mid": "cloth_mid",
    "horse_darkest": "wing_darkest", "horse_dark": "wing_dark",
    "horse_mid": "wing_mid", "horse_light": "wing_light",
    "mane_darkest": "horn_darkest", "mane_dark": "horn_dark",
    "mane_mid": "horn_mid", "mane_bright": "horn_light",
    "mane_hot": "horn_shine",
    "arm_darkest": "arm_darkest", "arm_dark": "arm_dark",
    "arm_mid": "arm_mid", "arm_light": "arm_light",
    "arm_shine": "arm_shine",
    "metal_darkest": "metal_darkest", "metal_dark": "metal_dark",
    "metal_mid": "metal_mid", "metal_edge": "metal_edge",
    "metal_light": "metal_light", "metal_shine": "metal_shine",
    "gold_dark": "gold_dark", "gold_mid": "gold_mid",
    "gold_light": "gold_light",
    "eye_dark": "eye_dark", "eye_bright": "eye_bright",
    "eye_hot": "eye_hot",
    "shadow_deep": "shadow_deep",
    # 9 kunci kontrak (dipetakan ke warna asli renderer)
    "outline": "skin_darkest", "shadow": "shadow_deep",
    "dark": "skin_dark", "body": "skin_mid", "mid": "skin_light",
    "light": "skin_high", "highlight": "skin_shine",
    "weapon": "fire_bright", "fx": "molten_bright",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Tarik warna dari ``_NS_pyrenth.PALETTE`` sekali saja (idempotent)."""
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
        P["arm_high"] = _mix(P["arm_light"], P["arm_shine"], 0.5)
        P["cape_light"] = _mix(P["cape_mid"], P["skin_light"], 0.4)
        P["horse_high"] = _mix(P["horse_light"], P["skin_high"], 0.4)
    _PALETTE_SYNCED = True


# ============================================================================
# 3.  JEMBATAN KE RENDERER — satu sumber geometri & pose
# ============================================================================

_RENDERER = None          # None = belum dicari, False = tidak ada


def _renderer():
    """``_NS_pyrenth`` atau None.  Diimpor malas: modul boss itu besar."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level4 import _NS_pyrenth as V
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
    """Kenaikan grip (0..1) — IDENTIK dengan ``_NS_pyrenth._sword_lift``."""
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
    for t0, t1, a0, a1, kind in BLADE_ARC:
        if t0 <= p < t1 or (p >= 1.0 and t1 >= 1.0):
            e = _ease(kind, (p - t0) / max(0.0001, t1 - t0))
            return a0 + (a1 - a0) * e, _fallback_lift(p)
    return BLADE_ARC[0][2], 0.0


def blade_arc(progress):
    """``(phi, lift)`` ARK pedang — SATU sumber kebenaran.

    Membaca ``_NS_pyrenth._blade_arc`` (fungsi yang sama yang dipakai
    canvas untuk menggambar pedang); kalau renderer tidak ada, memakai
    tabel fallback yang identik di atas.
    """
    R = _renderer()
    fn = getattr(R, "_blade_arc", None) if R is not None else None
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
    action = getattr(boss, "_pyr_pose_action", None)
    if action is None:
        action = {"q": "q_cast", "w": "w_cast", "e": "e_cast",
                  "r": "r_cast"}.get(skill)
    if action is None:
        action = ("swing" if getattr(boss, "_pyr_attack_active", False)
                  else "idle")
    phase = float(getattr(boss, "pulse", 0.0) or 0.0)
    ap = float(getattr(boss, "_pyr_attack_progress", 0.0) or 0.0)
    return action, phase, ap


def pose_of(boss):
    """Pose badan yang dipakai renderer: ``(action, phase, ap)``."""
    action = getattr(boss, "_pyr_pose_action", None)
    if action is None:
        return _fallback_pose(boss)
    phase = float(getattr(boss, "_pyr_phase",
                          getattr(boss, "pulse", 0.0)))
    ap = float(getattr(boss, "_pyr_attack_progress", 0.0) or 0.0)
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


def blade_points(boss, x, y):
    """``(grip, tip_atas, ujung_belakang)`` pedang di RUANG LAYAR.

    Memakai ``_NS_pyrenth.blade_geometry`` — fungsi yang sama yang
    dipakai canvas untuk menggambar pedang, jadi trail tidak mungkin
    melenceng dari bilahnya.
    """
    action, phase, ap = pose_of(boss)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)
    R = _renderer()
    fn = getattr(R, "blade_geometry", None) if R is not None else None
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
        phi, lift = blade_arc(ap)
    else:
        phi, lift = 0.96 + 0.06 * math.sin(phase * 0.8), 0.0
    gx = facing * (_GRIP_FALLBACK[0] + 5.0 * lift)
    gy = _GRIP_FALLBACK[1] - 9.0 * lift
    dx = facing * math.cos(phi) * _BLADE_HALF_FALLBACK
    dy = -math.sin(phi) * _BLADE_HALF_FALLBACK
    return ((x + gx * k, y + gy * k),
            (x + (gx + dx) * k, y + (gy + dy) * k),
            (x + (gx - dx * 0.35) * k, y + (gy - dy * 0.35) * k))


def blade_tip(boss, x, y):
    """Titik ujung bilah (ruang layar) — untuk trail & titik lahir bolt."""
    _grip, hi, _lo = blade_points(boss, x, y)
    return hi


def blade_angle(boss, x, y):
    """Sudut bilah (radian, ruang layar) dari grip ke ujung."""
    grip, hi, _lo = blade_points(boss, x, y)
    return math.atan2(hi[1] - grip[1], hi[0] - grip[0])


def launch_point(boss, x, y):
    """Titik lepas Doom Bolt (ruang layar) — sedikit di depan ujung
    bilah ke arah target."""
    _grip, hi, _lo = blade_points(boss, x, y)
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
    """Genangan tanah elips ber-falloff (bara / jiwa)."""
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
    """Cincin duri bergerigi (Scorched Earth) — jelas BUKAN lingkaran
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


def spark_star(surface, cx, cy, size, color, alpha, spikes=8, rot=0.3,
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
    """Titik bintang n-titik (dipakai telegraph R — 8 titik) — jelas BUKAN
    lingkaran."""
    out = []
    step = math.tau / points
    for i in range(points):
        a = rot + i * step * 2.0
        out.append((cx + math.cos(a) * radius,
                    cy + math.sin(a) * radius * squash))
    return out


def molten_star_points(cx, cy, radius, spikes=8, rot=0.0, squash=0.42,
                      inner=0.45):
    """Bintang api bersudut tajam (sigil infernal Pyrenth)."""
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
        elif shape == "soul":
            # serpih jiwa DEVOUR: cangkang toska + inti pucat
            r = max(1, int(s * 0.7))
            _blit_faded(surface, glow_surface(r + 2, P["soul_light"], 0.9),
                        x, y, a, additive=True)
            pygame.draw.rect(surface, (*self.color, a),
                             (x - r, y - r, r * 2, r * 2), 1)
            pygame.draw.circle(surface, (*P["soul_glow"], a), (x, y), r)
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
    """Trail pedang api Pyrenth.

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
            pygame.draw.polygon(buf, (*P["molten_dark"], int(52 * f)),
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
      ``melee``  — tebasan pedang api (sabit api + retakan tanah)
      ``bolt``   — Doom Bolt mendarat (ledakan gerigi + serpihan)
      ``ember``  — Soul Ember tertelan (implosi jiwa, BUKAN ledakan)
      ``quake``  — erupsi Scorched Earth mendarat (kejut tanah + debu)
      ``skill``  — dampak umum skill
    """

    LIFE = {"melee": 0.28, "bolt": 0.32, "ember": 0.40, "quake": 0.36,
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
                       P["fire_hot"], int(195 * ft), spikes=8,
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
        elif self.kind == "ember":
            self._draw_ember_burst(surface, t, inv)
        elif self.kind == "quake":
            self._draw_quake(surface, t, inv)

    # ------------------------------------------------------------------
    def _draw_slash(self, surface, t, inv):
        """Fragmen sabit: tiga busur tipis melintang arah tebasan."""
        span = 1.2
        for k, (sc, wd, col) in enumerate((
                (1.0, 2, P["fire_hot"]),
                (0.72, 2, P["fire_bright"]),
                (1.22, 1, P["molten_bright"]))):
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
                pygame.draw.lines(surface, (*P["molten_dark"], int(160 * inv)),
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

    def _draw_ember_burst(self, surface, t, inv):
        """Soul Ember tertelan: cangkang jiwa yang MENGKERUT ke dalam.

        Berbeda dari impact lain, radiusnya MENGECIL seiring umur —
        jiwa tersedot habis, bukan meledak keluar.
        """
        r = self.radius * (1.05 - 0.75 * _ease("oc", t))
        rect = pygame.Rect(int(self.x - r), int(self.y - r * 0.9),
                           int(r * 2), int(r * 1.8))
        if rect.width > 3 and rect.height > 3:
            pygame.draw.ellipse(surface, (*P["soul_mid"], int(110 * inv)),
                                rect, max(1, int(3 * inv) + 1))
        for k in range(6):
            a = _hash01(self.seed + k * 17) * math.tau - t * 3.4
            d = r * (0.55 + _hash01(self.seed + k * 23) * 0.7)
            px = self.x + math.cos(a) * d
            py = self.y + math.sin(a) * d * 0.85
            c = max(1, int(3 * inv) + 1)
            pygame.draw.rect(surface, (*P["soul_glow"], int(215 * inv)),
                             (int(px - c), int(py - c), c * 2, c * 2))

    def _draw_quake(self, surface, t, inv):
        """Erupsi mendarat: kejut elips tanah + kepulan debu + retakan."""
        r = self.radius * (0.3 + 0.9 * _ease("oc", t))
        for k, (m, col) in enumerate(((1.0, P["molten_bright"]),
                                      (0.72, P["fire_hot"]))):
            rect = pygame.Rect(int(self.x - r * m),
                               int(self.y + 6 - r * m * 0.36),
                               int(r * m * 2), int(r * m * 0.72))
            if rect.width > 3:
                pygame.draw.ellipse(surface, (*col, int(150 * inv * (1 - k * 0.4))),
                                    rect, max(1, int(3 * inv)))
        # kepulan debu (bukan lingkaran: tiga gumpalan bergeser)
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

    def __init__(self, x, y, tx, ty, speed=DOOM_SPEED, damage=0.0,
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


class DoomBoltProjectile(BaseProjectile):
    """Q — DOOM BOLT: mata tombak api memanjang (bukan lingkaran polos).

    Bentuk: mata tombak obsidian berinti magma — kepala runcing, sirip
    ganda, ekor memudar, rotasi mengikuti arah terbang, glow beranulus,
    jejak bara, dan tiga gelang rantai yang berputar mengelilingi badan
    proyektil (ikatan DOOM).
    """

    kind = "bolt"

    def __init__(self, x, y, tx, ty, speed=DOOM_SPEED, damage=0.0,
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
            color=random.choice((P["molten_bright"], P["fire_bright"],
                                 P["fire_hot"])),
            shape="ember", additive=True, drag=1.2)

    def draw(self, surface):
        px, py = self.position.x, self.position.y
        s = self.scale
        ca, sa = math.cos(self.rotation), math.sin(self.rotation)
        ex, ey = -sa, ca                     # sumbu tegak

        # jejak panjang (ribbon meruncing)
        self._draw_ribbon(surface, 1.2 * s, 4.2 * s,
                          ((P["molten_dark"], 0.55, 1.0),
                           (P["molten_bright"], 0.85, 0.55),
                           (P["fire_hot"], 1.0, 0.2)), fade=0.16)

        # glow beranulus (di bawah bentuk)
        _blit_faded(surface, glow_surface(int(13 * s), P["molten_bright"], 1.0),
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
        pygame.draw.polygon(surface, P["molten_darkest"],
                            [tail1, tail2, back])
        pygame.draw.polygon(surface, P["molten_dark"],
                            [tip, sh1, mid1, mid2, sh2])
        pygame.draw.polygon(surface, P["molten_mid"],
                            [(tip[0] + (back[0] - tip[0]) * 0.15,
                              tip[1] + (back[1] - tip[1]) * 0.15),
                             (sh1[0] + (back[0] - sh1[0]) * 0.5,
                              sh1[1] + (back[1] - sh1[1]) * 0.5),
                             (back[0], back[1]),
                             (sh2[0] + (back[0] - sh2[0]) * 0.5,
                              sh2[1] + (back[1] - sh2[1]) * 0.5)])
        pygame.draw.polygon(surface, P["molten_bright"],
                            [tip,
                             (px + ex * 1.6 * s, py + ey * 1.6 * s),
                             (px - ca * 4 * s, py - sa * 4 * s),
                             (px - ex * 1.6 * s, py - ey * 1.6 * s)])
        # garis inti menyala
        pygame.draw.line(surface, P["molten_hot"],
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

        # GELANG RANTAI: tiga cincin obsidian yang berputar melingkari
        # badan proyektil — ini yang membuat DOOM terbaca sebagai ikatan
        # berapi, bukan sekadar peluru api.
        spin = self.age * 9.0
        for i in range(3):
            off = (i - 1) * 6.0 * s
            bx = px - ca * off
            by = py - sa * off
            ph = spin + i * 1.05
            rw = abs(math.cos(ph)) * 5.2 * s + 1.0    # cincin miring
            rh = 5.2 * s
            ring = []
            for k in range(10):
                aa = k * math.tau / 10.0
                lx = math.cos(aa) * rw
                ly = math.sin(aa) * rh
                ring.append((bx + lx * ca - ly * sa,
                             by + lx * sa + ly * ca))
            pygame.draw.polygon(surface, P["arm_darkest"], ring, 2)
            pygame.draw.polygon(surface, P["molten_hot"], ring, 1)


class SoulEmberProjectile(BaseProjectile):
    """W — SOUL EMBER: jiwa yang DISEDOT masuk ke inti Pyrenth.

    Bedanya dengan proyektil biasa: ini terbang KE ARAH Pyrenth, bukan
    menjauh — itu bahasa visual DEVOUR.  Bentuknya bukan bola: cangkang
    jiwa runcing seperti tetesan terbalik dengan wajah kosong, inti
    toska berdenyut, ekor pita jiwa, dan sedikit ayunan gelisah.
    Warnanya sengaja toska pucat, BUKAN oranye, supaya langsung terbaca
    berbeda dari seluruh api Pyrenth.
    """

    kind = "ember"
    WOBBLE = 0.06           # amplitudo ayunan (fraksi kecepatan)

    def __init__(self, x, y, tx, ty, speed=EMBER_SPEED, damage=0.0,
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
            vx=random.uniform(-16, 16), vy=random.uniform(-26, -4),
            life=random.uniform(0.25, 0.6),
            size=random.uniform(1.2, 2.6) * self.scale,
            color=random.choice((P["soul_light"], P["soul_glow"],
                                 P["soul_mid"])),
            shape="streak", additive=True, drag=1.0)

    def draw(self, surface):
        px, py = self.position.x, self.position.y
        s = self.scale
        pulse = 0.75 + 0.25 * math.sin(self.wobble_phase * 0.8)
        ca, sa = math.cos(self.rotation), math.sin(self.rotation)
        ex, ey = -sa, ca

        # pita jiwa yang tertinggal
        self._draw_ribbon(surface, 1.6 * s, 5.0 * s,
                          ((P["soul_dark"], 0.55, 1.0),
                           (P["soul_mid"], 0.8, 0.55),
                           (P["soul_glow"], 1.0, 0.22)), fade=0.24)

        # halo jiwa
        _blit_faded(surface, glow_surface(int(14 * s * pulse + 4),
                                          P["soul_light"], 1.0),
                    px, py, 135, additive=True)

        # cangkang: tetesan terbalik (kepala bulat, ekor meruncing)
        head = (px + ca * 7.5 * s, py + sa * 7.5 * s)
        tail = (px - ca * 11.0 * s, py - sa * 11.0 * s)
        w = 5.4 * s * pulse
        shell = [head,
                 (px + ex * w, py + ey * w),
                 (px - ca * 4.0 * s + ex * w * 0.6,
                  py - sa * 4.0 * s + ey * w * 0.6),
                 tail,
                 (px - ca * 4.0 * s - ex * w * 0.6,
                  py - sa * 4.0 * s - ey * w * 0.6),
                 (px - ex * w, py - ey * w)]
        pygame.draw.polygon(surface, P["soul_dark"], shell)
        inner = [(px + (sx - px) * 0.6, py + (sy - py) * 0.6)
                 for sx, sy in shell]
        pygame.draw.polygon(surface, P["soul_mid"], inner)

        # WAJAH KOSONG: dua rongga mata pucat — jiwa, bukan bola energi
        for sgn in (-1, 1):
            exx = px + ex * 2.1 * s * sgn + ca * 2.0 * s
            eyy = py + ey * 2.1 * s * sgn + sa * 2.0 * s
            pygame.draw.circle(surface, P["soul_glow"],
                               (int(exx), int(eyy)),
                               max(1, int(1.2 * s)))

        # inti berdenyut
        pygame.draw.circle(surface, P["soul_light"], (int(px), int(py)),
                           max(1, int(2.4 * s * pulse)))
        pygame.draw.circle(surface, P["soul_glow"], (int(px), int(py)),
                           max(1, int(1.2 * s * pulse)))


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

    def spawn_doom(self, x, y, tx, ty, **kw):
        self._make_room()
        pr = DoomBoltProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    def spawn_ember(self, x, y, tx, ty, **kw):
        self._make_room()
        pr = SoulEmberProjectile(x, y, tx, ty, **kw)
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
        if projectile.kind == "ember":
            # Soul Ember sampai di inti Pyrenth: jiwa TERTELAN.
            # Partikelnya sedikit dan hidupnya pendek — implosi, bukan
            # ledakan; shake-nya pun jauh lebih halus daripada benturan
            # api, karena tidak ada yang dihantam.
            self._push_impact(ImpactFX(px, py, "ember", ang, 1.2,
                                       P["soul_light"], 46.0))
            self.particles.burst(px, py, 12, speed=(40, 150),
                                 life=(0.2, 0.5), size=(1.5, 3.4),
                                 colors=(P["soul_light"], P["soul_glow"],
                                         P["soul_mid"]),
                                 gravity=-90, drag=1.6, shape="soul")
            self.particles.burst(px, py, 5, speed=(30, 110),
                                 life=(0.3, 0.7), size=(1.6, 3.2),
                                 colors=(P["soul_glow"], P["fire_glow"]),
                                 gravity=-140, drag=1.2, shape="streak")
            _feel_shake(3.2, 0.12)
            _feel_hit_stop(0.03)
        else:
            self._push_impact(ImpactFX(px, py, "bolt", ang, 1.0,
                                       P["molten_bright"], 36.0))
            self.particles.burst(px, py, 12, speed=(80, 250),
                                 life=(0.2, 0.48), size=(1.6, 3.8),
                                 colors=(P["molten_bright"], P["fire_bright"],
                                         P["fire_hot"], P["ember"]),
                                 spread=2.4, direction=ang + math.pi,
                                 gravity=250, drag=1.0, shape="ember")
            self.particles.burst(px, py, 4, speed=(20, 70),
                                 life=(0.35, 0.75), size=(2.5, 5),
                                 colors=(P["ash"], P["dust"]),
                                 gravity=-50, shape="smoke", additive=False)
            _feel_shake(3.8, 0.12)
            _feel_hit_stop(0.032)
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
        self.tint = tint or P["molten_dark"]
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
    """Efek satu skill Pyrenth, dengan lifecycle enam fase::

        CAST -> CHARGE -> RELEASE -> AREA/TRAVEL -> IMPACT -> AFTER -> FADE

    Setiap skill punya BENTUK khasnya sendiri supaya tidak semuanya jadi
    lingkaran::

        Q  DOOM            koridor bidik meruncing + MATA RANTAI api
        W  DEVOUR          spiral sedot ke dalam + rahang jiwa + heal
        E  SCORCHED EARTH  cincin duri api + retakan magma + shockwave
        R  INFERNAL BLADE  sabit api menyapu + baji rekahan + pilar api
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
        self._souls = []              # jiwa yang dicabut W
        self._lunge_x0 = float(x)     # titik mulai terjangan (R)
        self._cracks_e = None         # retakan magma E (dibuat sekali)
        self._chain_born = None       # kapan rantai Q lahir
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

    # ==================================================================
    # Q — DOOM  (rantai api mengunci satu target, 320 dmg)
    # ==================================================================
    def _upd_q(self, dt, particles, projectiles):
        t = self.t
        ax, ay = self.aim()
        # CAST: debu terangkat + bara merangkak di kaki
        if t < 0.16 and self._once("cast"):
            particles.burst(self.x, self.y + 26, 10, speed=(50, 170),
                            life=(0.25, 0.5), size=(2, 4),
                            colors=(P["dust"], P["ash"]), spread=math.pi,
                            direction=-math.pi / 2, gravity=180,
                            shape="dust", additive=False, layer="back")
        # CHARGE: energi terkumpul ke cakar/bilah depan
        if 0.10 <= t < 0.40:
            self._acc += dt
            if self._acc >= 0.03 and self.director is not None:
                self._acc = 0.0
                lp = self._launch()
                ang = math.atan2(ay - lp[1], ax - lp[0])
                rr = random.uniform(16, 26)
                particles.spawn(
                    lp[0] + math.cos(ang + math.pi) * rr,
                    lp[1] + math.sin(ang + math.pi) * rr,
                    vx=-math.cos(ang + math.pi) * 90.0,
                    vy=-math.sin(ang + math.pi) * 90.0,
                    life=0.16, size=random.uniform(1.4, 2.6),
                    color=random.choice((P["molten_bright"],
                                         P["molten_hot"], P["fire_hot"])),
                    shape="streak", additive=True)
        # RELEASE: Doom Bolt lepas + MATA RANTAI api tercetak sepanjang
        # jalur (inilah yang membuat Q terbaca sebagai "rantai", bukan
        # sekadar peluru).
        if 0.34 <= t < 0.46 and self._once("release") and \
                self.director is not None:
            lp = self._launch()
            ang = math.atan2(ay - lp[1], ax - lp[0])
            self.director.projectiles.spawn_doom(
                lp[0], lp[1], ax, ay, speed=DOOM_SPEED, radius=10.0,
                target=self.target, owner=self.director.unit,
                scale=self.scale)
            self._chain_born = self.age
            particles.burst(lp[0], lp[1], 9, speed=(90, 260),
                            life=(0.12, 0.3), size=(1.4, 3.0),
                            colors=(P["molten_hot"], P["fire_hot"],
                                    P["fire_bright"]),
                            spread=1.1, direction=ang, drag=1.6,
                            shape="streak")
            _feel_shake(2.6, 0.10)
        # IMPACT: gema di titik terkunci
        if t >= 0.74 and self._once("impact"):
            particles.burst(ax, ay, 12, speed=(70, 240), life=(0.25, 0.55),
                            size=(1.8, 4.0),
                            colors=(P["molten_bright"], P["fire_bright"],
                                    P["ember"]),
                            gravity=280, drag=0.9, shape="ember")
            particles.burst(ax, ay, 5, speed=(40, 120), life=(0.3, 0.7),
                            size=(1.6, 3.4),
                            colors=(P["metal_light"], P["ash"]),
                            gravity=480, shape="shard",
                            rotation_speed=(-9, 9), additive=False)

    def _launch(self):
        """Titik lepas proyektil (ujung bilah/cakar) di ruang layar."""
        lp = (self.x + self.facing * 20.0 * self.scale,
              self.y - 8.0)
        if self.director is not None and self.director.unit is not None:
            try:
                lp = launch_point(self.director.unit, self.x, self.y)
            except Exception:                        # pragma: no cover
                lp = lp
        return lp

    # ==================================================================
    # W — DEVOUR  (sedot jiwa dari sekitar + heal 8% max HP)
    # ==================================================================
    def _upd_w(self, dt, particles, projectiles):
        t = self.t
        # CAST: cakar terbuka, tanah menghitam, asap jiwa merembes
        if t < 0.12 and self._once("cast"):
            particles.burst(self.x, self.y + 20, 14, speed=(40, 150),
                            life=(0.4, 0.9), size=(2.5, 5.5),
                            colors=(P["soul_dark"], P["soul_mid"],
                                    P["ash"]),
                            spread=math.tau, gravity=-45, drag=0.9,
                            shape="smoke", additive=False, layer="back")
            _feel_shake(4.0, 0.14)
        # CHARGE + AREA: jiwa DISEDOT MASUK — partikel lahir di pinggir
        # radius lalu terbang KE DALAM menuju dada Pyrenth.  Arah gerak
        # yang terbalik inilah tanda baca "devour", bukan "ledakan".
        if 0.08 <= t < 0.80:
            self._acc += dt
            while self._acc >= 0.022:
                self._acc -= 0.022
                if particles.count() > particles.cap * 0.85:
                    break
                a = random.uniform(0.0, math.tau)
                rr = self.r_screen(random.uniform(0.45, 1.0))
                sx = self.x + math.cos(a) * rr
                sy = self.y - 6 + math.sin(a) * rr * 0.45
                # kecepatan mengarah ke inti (dada), makin dekat makin cepat
                dx = (self.x - sx)
                dy = (self.y - 16 - sy)
                L = math.hypot(dx, dy) or 1.0
                sp = random.uniform(150.0, 320.0)
                particles.spawn(
                    sx, sy, vx=dx / L * sp, vy=dy / L * sp,
                    life=max(0.12, min(0.9, L / sp)),
                    size=random.uniform(1.4, 3.2),
                    color=random.choice((P["soul_light"], P["soul_glow"],
                                         P["soul_mid"])),
                    shape="streak", additive=True,
                    layer="back" if random.random() < 0.4 else "front")
        # RELEASE: SPIRIT_COUNT jiwa besar terjun ke Pyrenth (proyektil
        # nyata — arahnya dari luar KE dalam, kebalikan proyektil biasa)
        if t >= 0.20 and self._once("souls") and self.director is not None:
            for i in range(SPIRIT_COUNT):
                a = (i / float(SPIRIT_COUNT)) * math.tau + \
                    _hash01(self.seed + i) * 0.8
                rr = self.r_screen(0.85)
                sx = self.x + math.cos(a) * rr
                sy = self.y - 10 + math.sin(a) * rr * 0.45
                self.director.projectiles.spawn_ember(
                    sx, sy, self.x, self.y - 16, speed=EMBER_SPEED,
                    radius=12.0, owner=self.director.unit,
                    scale=self.scale)
            _feel_shake(5.5, 0.18)
            _feel_hit_stop(0.04)
        # IMPACT: jiwa tertelan — kilat penyembuhan di dada
        if t >= 0.62 and self._once("heal"):
            particles.burst(self.x, self.y - 16, 16, speed=(50, 190),
                            life=(0.3, 0.7), size=(1.6, 3.6),
                            colors=(P["soul_glow"], P["soul_light"],
                                    P["fire_glow"]),
                            spread=math.tau, gravity=-120, drag=1.1,
                            shape="ember")
            if self.director is not None:
                self.director.add_impact(self.x, self.y - 16, "skill", 0.0,
                                         1.1, P["soul_glow"], 42.0)
            _feel_shake(6.0, 0.20)
            _feel_hit_stop(0.045)

    # ==================================================================
    # E — SCORCHED EARTH  (erupsi duri api radius 180, 380 dmg)
    # ==================================================================
    def _upd_e(self, dt, particles, projectiles):
        t = self.t
        # CAST: kedua cakar terangkat, tanah retak, debu meletup
        if t < 0.12 and self._once("cast"):
            particles.burst(self.x, self.y + 22, 16, speed=(80, 250),
                            life=(0.3, 0.75), size=(2.5, 6),
                            colors=(P["dust"], P["ash"], P["cape_dark"]),
                            spread=math.tau, gravity=-30, drag=0.9,
                            shape="dust", additive=False, layer="back")
            _feel_shake(5.0, 0.16)
        # CHARGE: bara merayap keluar mengikuti cincin erupsi
        if 0.10 <= t < 0.36:
            self._acc += dt
            if self._acc >= 0.04:
                self._acc = 0.0
                a = random.uniform(0, math.tau)
                rr = self.r_screen(random.uniform(0.4, 0.95))
                particles.spawn(
                    self.x + math.cos(a) * rr,
                    self.y + 10 + math.sin(a) * rr * 0.42,
                    vx=0.0, vy=random.uniform(-80, -34),
                    life=random.uniform(0.3, 0.65),
                    size=random.uniform(1.6, 3.4),
                    color=random.choice((P["molten_bright"],
                                         P["fire_bright"], P["fire_hot"])),
                    shape="ember", additive=True)
        # RELEASE: DURI API MELEDAK dari tanah (damage jatuh saat cast,
        # jadi erupsi visual harus datang di awal jendela)
        if t >= 0.16 and self._once("erupt"):
            n = 16
            for i in range(n):
                a = i * math.tau / n + _hash01(self.seed + i) * 0.3
                rr = self.r_screen(0.94)
                sx = self.x + math.cos(a) * rr
                sy = self.y + 10 + math.sin(a) * rr * 0.42
                particles.burst(sx, sy, 3, speed=(140, 380),
                                life=(0.3, 0.75), size=(1.8, 4.4),
                                colors=(P["molten_bright"],
                                        P["fire_bright"], P["fire_hot"]),
                                spread=0.9, direction=-math.pi / 2,
                                gravity=430, drag=0.6, shape="flame")
            particles.burst(self.x, self.y + 8, 22, speed=(200, 480),
                            life=(0.3, 0.85), size=(1.8, 4.8),
                            colors=(P["molten_bright"], P["fire_bright"],
                                    P["ember"]),
                            spread=math.tau, gravity=320, drag=0.7,
                            shape="ember")
            particles.burst(self.x, self.y + 12, 8, speed=(90, 280),
                            life=(0.4, 0.9), size=(2.0, 4.4),
                            colors=(P["arm_mid"], P["metal_dark"],
                                    P["ash"]),
                            spread=math.tau, gravity=620, shape="debris",
                            rotation_speed=(-11, 11), additive=False)
            self._scorched = True
            _feel_shake(9.5, 0.26)
            _feel_hit_stop(0.05)
        # AFTER: tanah hangus mengepul
        if t > 0.5:
            self._acc += dt
            if self._acc >= 0.06:
                self._acc = 0.0
                a = random.uniform(0, math.tau)
                rr = random.uniform(0.3, 0.95) * self.r_screen(1.0)
                particles.spawn(
                    self.x + math.cos(a) * rr,
                    self.y + 8 + math.sin(a) * rr * 0.42,
                    vx=random.uniform(-12, 12), vy=random.uniform(-48, -18),
                    life=random.uniform(0.5, 1.0),
                    size=random.uniform(2.4, 5.2),
                    color=random.choice((P["ash"], P["dust"])),
                    shape="smoke", additive=False, layer="front")

    # ==================================================================
    # R — INFERNAL BLADE  (tebasan ultimate + terjangan, radius 220)
    # ==================================================================
    def _upd_r(self, dt, particles, projectiles):
        t = self.t
        # CAST: bilah diangkat, api tersedot ke atas kepala
        if t < 0.12 and self._once("cast"):
            particles.burst(self.x, self.y - 20, 18, speed=(60, 200),
                            life=(0.35, 0.8), size=(1.8, 4.2),
                            colors=(P["fire_bright"], P["molten_bright"],
                                    P["ember"]),
                            spread=math.tau, gravity=-180, drag=0.9,
                            shape="streak", additive=True, layer="back")
            _feel_shake(6.0, 0.18)
        # CHARGE: bara terkumpul di sepanjang bilah
        if 0.08 <= t < 0.40:
            self._acc += dt
            if self._acc >= 0.025:
                self._acc = 0.0
                lp = self._launch()
                particles.spawn(
                    lp[0] + random.uniform(-14, 14),
                    lp[1] + random.uniform(-18, 8),
                    vx=random.uniform(-20, 20), vy=random.uniform(-40, 10),
                    life=random.uniform(0.15, 0.35),
                    size=random.uniform(1.4, 3.0),
                    color=random.choice((P["fire_hot"], P["fire_glow"],
                                         P["molten_hot"])),
                    shape="ember", additive=True)
        # RELEASE: TEBASAN — sabit api raksasa dilepas ke depan
        if t >= 0.30 and self._once("slash"):
            ang = 0.0 if self.facing > 0 else math.pi
            particles.burst(self.x + self.facing * 30, self.y - 6, 26,
                            speed=(220, 560), life=(0.25, 0.7),
                            size=(2.0, 5.2),
                            colors=(P["fire_bright"], P["fire_hot"],
                                    P["fire_glow"], P["ember"]),
                            spread=1.5, direction=ang, gravity=180,
                            drag=0.7, shape="streak")
            particles.burst(self.x + self.facing * 24, self.y + 14, 12,
                            speed=(120, 340), life=(0.3, 0.8),
                            size=(2.2, 5.0),
                            colors=(P["dust"], P["ash"]),
                            spread=1.2, direction=ang, gravity=260,
                            shape="dust", additive=False, layer="back")
            if self.director is not None:
                self.director.add_impact(
                    self.x + self.facing * 40, self.y - 4, "melee", ang,
                    2.2, P["fire_glow"], max(40.0, self.r_screen(0.42)))
            _feel_shake(15.0, 0.34)
            _feel_hit_stop(0.075)
        # AREA: pilar api menyusuri retakan yang ditinggalkan tebasan
        if 0.34 <= t < 0.82:
            self._acc += dt
            if self._acc >= 0.035:
                self._acc = 0.0
                d = random.uniform(0.2, 1.0) * self.r_screen(0.9)
                particles.spawn(
                    self.x + self.facing * d + random.uniform(-8, 8),
                    self.y + 12 + random.uniform(-4, 6),
                    vx=random.uniform(-16, 16),
                    vy=random.uniform(-130, -60),
                    life=random.uniform(0.3, 0.65),
                    size=random.uniform(2.0, 4.6),
                    color=random.choice((P["fire_bright"], P["fire_hot"],
                                         P["molten_bright"])),
                    shape="flame", additive=True)
        # AFTER: bara jatuh + asap tebal
        if t > 0.70:
            self._acc += dt
            if self._acc >= 0.07:
                self._acc = 0.0
                particles.spawn(
                    self.x + self.facing * random.uniform(0, 1) *
                    self.r_screen(0.8),
                    self.y - random.uniform(0, 40),
                    vx=random.uniform(-10, 10), vy=random.uniform(20, 70),
                    life=random.uniform(0.4, 0.9),
                    size=random.uniform(1.4, 3.0),
                    color=random.choice((P["ember"], P["ash"])),
                    shape="ember", additive=True, gravity=90)

    # ------------------------------------------------------------------
    # GAMBAR — BAWAH badan
    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        fn = getattr(self, "_gnd_" + self.skill, None)
        if fn is not None:
            fn(surface)

    def _gnd_q(self, surface):
        """Telegraph DOOM: koridor bidik meruncing + reticle kurung siku."""
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
                   P["molten_mid"], a255)
        # reticle kurung siku di target (bukan lingkaran penuh)
        s = 10.0 + 4.0 * math.sin(self.age * 9.0)
        c = int(95 * grow * (1.0 - max(0.0, (t - 0.5) / 0.3)))
        if c > 3:
            col = (*P["molten_bright"], c)
            for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                pygame.draw.lines(surface, col, False, [
                    (ax + dx * s, ay + dy * s * 0.5 - dy * s * 0.2),
                    (ax + dx * s, ay + dy * s * 0.5 + dy * s * 0.28),
                    (ax + dx * s * 0.55, ay + dy * s * 0.5 + dy * s * 0.28)],
                    2)

    def _gnd_w(self, surface):
        """Telegraph DEVOUR: cincin PENUH radius dunia + genangan jiwa.

        Radius 200 dunia = jangkauan sedot jiwa di AI; tes regresi
        menguncinya.
        """
        t = self.t
        if t > 0.96:
            return
        grow = min(1.0, t / 0.20)
        r = self._fit(surface, self.r_screen(1.0) * grow)
        a255 = int(140 * grow * (1.0 - max(0.0, (t - 0.66) / 0.32)))
        if a255 < 4 or r < 6:
            return
        cy = self.y + 10
        # 1) cincin PENUH — batas sedot jiwa
        _blit_faded(surface, ring_surface(r, 2, P["soul_light"], 255),
                    self.x, cy, a255, additive=True)
        # 2) potongan busur runik yang berputar BERLAWANAN arah — sedotan
        _blit_faded(surface,
                    arc_ring_surface(int(r * 0.72), 9, 0.5, 2,
                                     P["soul_glow"], 255, squash=0.42,
                                     rot=-self.age * 1.4),
                    self.x, cy, int(a255 * 0.9), additive=True)
        # 3) garis tarik: 10 jari-jari yang memendek ke pusat
        pull = (self.age * 1.6) % 1.0
        for i in range(10):
            a = i * math.tau / 10.0 + self.age * 0.4
            r0 = r * (0.95 - pull * 0.5)
            r1 = r0 - r * 0.22
            if r1 < 2:
                continue
            pygame.draw.line(surface, (*P["soul_light"], int(a255 * 0.8)),
                             (self.x + math.cos(a) * r0,
                              cy + math.sin(a) * r0 * 0.42),
                             (self.x + math.cos(a) * r1,
                              cy + math.sin(a) * r1 * 0.42), 2)
        # 4) genangan jiwa
        _blit_faded(surface, ground_pool_surface(r, P["soul_dark"], 0.5),
                    self.x, cy, int(a255 * 0.9))

    def _gnd_e(self, surface):
        """Telegraph SCORCHED EARTH: cincin PENUH radius 180 dunia +
        cincin duri bergerigi + retakan magma yang menjalar keluar."""
        t = self.t
        if t > 0.98:
            return
        grow = min(1.0, t / 0.20)
        r = self._fit(surface, self.r_screen(1.0) * grow)
        a255 = int(155 * grow * (1.0 - max(0.0, (t - 0.70) / 0.28)))
        if a255 < 4 or r < 6:
            return
        cy = self.y + 10
        # 1) cincin PENUH — radius damage (tes mengunci)
        _blit_faded(surface, ring_surface(r, 2, P["molten_bright"], 255),
                    self.x, cy, a255, additive=True)
        # 2) cincin duri (jelas bukan lingkaran polos)
        _blit_faded(surface,
                    spike_ring_surface(int(r * 0.82), 14,
                                       max(3, int(r * 0.18)),
                                       P["fire_dark"], 255, squash=0.42,
                                       rot=self.age * 0.25),
                    self.x, cy, int(a255 * 0.75), additive=True)
        # 3) retakan magma menjalar keluar
        if self._cracks_e is None:
            self._cracks_e = []
            for k in range(7):
                a = k * math.tau / 7.0 + _hash01(self.seed + k) * 0.5
                self._cracks_e.append((a, 0.55 + _hash01(self.seed + k * 3)
                                       * 0.45))
        for a, m in self._cracks_e:
            rr = r * m * grow
            pts = crack_points(self.x, cy, self.x + math.cos(a) * rr,
                               cy + math.sin(a) * rr * 0.42, 5, 5.0,
                               self.seed + int(a * 100))
            if len(pts) > 1:
                pygame.draw.lines(surface, (*P["molten_dark"], a255), False,
                                  pts, 3)
                pygame.draw.lines(surface, (*P["fire_hot"],
                                            int(a255 * 0.8)), False, pts, 1)
        # 4) genangan bara
        _blit_faded(surface, ground_pool_surface(r, P["fire_darkest"], 0.5),
                    self.x, cy, int(a255 * 0.9))

    def _gnd_r(self, surface):
        """Telegraph INFERNAL BLADE: cincin PENUH radius 220 dunia +
        rekahan tanah berbentuk BAJI ke arah tebasan."""
        t = self.t
        if t > 0.98:
            return
        grow = min(1.0, t / 0.20)
        r = self._fit(surface, self.r_screen(1.0) * grow)
        a255 = int(150 * grow * (1.0 - max(0.0, (t - 0.75) / 0.23)))
        if a255 < 4 or r < 6:
            return
        cy = self.y + 10
        # 1) cincin PENUH — radius damage (tes mengunci)
        _blit_faded(surface, ring_surface(r, 3, P["fire_bright"], 255),
                    self.x, cy, a255, additive=True)
        # 2) baji rekahan ke arah hadap — arah tebasan terbaca
        wedge = []
        span = 0.85
        base = 0.0 if self.facing > 0 else math.pi
        for i in range(9):
            a = base - span / 2 + span * i / 8.0
            wedge.append((self.x + math.cos(a) * r * 0.98,
                          cy + math.sin(a) * r * 0.42 * 0.98))
        wedge.append((self.x, cy))
        pygame.draw.polygon(surface, (*P["fire_darkest"],
                                      int(a255 * 0.55)), wedge)
        pygame.draw.lines(surface, (*P["fire_glow"], a255), True, wedge, 2)
        # 3) bintang api 8 titik yang berputar pelan
        pts = molten_star_points(self.x, cy, r * 0.6, spikes=8,
                                 rot=self.age * 0.5, squash=0.42,
                                 inner=0.42)
        if len(pts) > 2:
            pygame.draw.lines(surface, (*P["molten_hot"],
                                        int(a255 * 0.85)), True, pts, 2)
        # 4) genangan magma
        _blit_faded(surface, ground_pool_surface(r, P["molten_darkest"],
                                                 0.5),
                    self.x, cy, int(a255 * 0.9))

    # ------------------------------------------------------------------
    # GAMBAR — DEPAN badan
    # ------------------------------------------------------------------
    def draw_front(self, surface):
        fn = getattr(self, "_fnt_" + self.skill, None)
        if fn is not None:
            fn(surface)

    def _fnt_q(self, surface):
        """Orb DOOM di ujung bilah, lalu MATA RANTAI api sepanjang jalur."""
        t = self.t
        lp = self._launch()
        # muatan sebelum lepas
        if t < 0.46:
            grow = min(1.0, max(0.0, (t - 0.08) / 0.26))
            pulse = 0.8 + 0.2 * math.sin(self.age * 14.0)
            rr = int((6 + 10 * grow) * pulse)
            if rr >= 2:
                _blit_faded(surface,
                            glow_surface(rr + 3, P["molten_bright"], 1.0),
                            lp[0], lp[1], int(200 * grow), additive=True)
                _blit_faded(surface,
                            glow_surface(max(2, rr // 2), P["fire_hot"],
                                         1.0),
                            lp[0], lp[1], int(230 * grow), additive=True)
                pygame.draw.circle(surface, P["fire_white"],
                                   (int(lp[0]), int(lp[1])),
                                   max(1, int(2 * grow)))
            return
        # RANTAI: mata rantai elips yang menyala berurutan dari Pyrenth
        # ke target — hanya hidup di jendela setelah RELEASE.
        if t > 0.92:
            return
        ax, ay = self.aim()
        fade = 1.0 - max(0.0, (t - 0.62) / 0.30)
        if fade <= 0.03:
            return
        dx, dy = ax - lp[0], ay - lp[1]
        dist = math.hypot(dx, dy)
        if dist < 8.0:
            return
        ux, uy = dx / dist, dy / dist
        step = 13.0
        n = int(min(26, dist / step))
        ang = math.atan2(dy, dx)
        for i in range(n):
            f = (i + 0.5) / float(max(1, n))
            px = lp[0] + ux * dist * f
            py = lp[1] + uy * dist * f
            # kilau berjalan sepanjang rantai
            travel = ((self.age * 2.6) - f) % 1.0
            heat = max(0.0, 1.0 - travel * 3.0)
            a = int(215 * fade * (0.45 + 0.55 * heat))
            if a < 5:
                continue
            rx = 6.0 if i % 2 == 0 else 4.0
            ry = 4.0 if i % 2 == 0 else 6.0
            rot = ang + (0.0 if i % 2 == 0 else math.pi / 2)
            link = []
            for k in range(10):
                aa = k * math.tau / 10.0
                lx = math.cos(aa) * rx
                ly = math.sin(aa) * ry
                link.append((px + lx * math.cos(rot) - ly * math.sin(rot),
                             py + lx * math.sin(rot) + ly * math.cos(rot)))
            pygame.draw.polygon(surface, (*P["arm_darkest"], a), link, 3)
            pygame.draw.polygon(surface,
                                (*(P["fire_glow"] if heat > 0.5
                                   else P["molten_bright"]), a), link, 1)
            if heat > 0.55:
                _blit_faded(surface, ember_surface(2, P["fire_hot"]),
                            px, py, int(a * heat), additive=True)

    def _fnt_w(self, surface):
        """DEVOUR: pusaran jiwa + berkas sedot ke dada + kilau heal."""
        t = self.t
        if t < 0.06 or t > 0.94:
            return
        fade = min(1.0, t / 0.14) * (1.0 - max(0.0, (t - 0.70) / 0.30))
        if fade <= 0.03:
            return
        cx, cy = self.x, self.y - 16.0
        # 1) berkas sedot: garis melengkung dari pinggir ke inti
        r = self.r_screen(0.9)
        for i in range(7):
            a = i * math.tau / 7.0 - self.age * 2.2
            pts = []
            for k in range(5):
                kk = k / 4.0
                rr = r * (1.0 - kk)
                aa = a + kk * 1.1          # melengkung (spiral)
                pts.append((cx + math.cos(aa) * rr,
                            cy + 16 + math.sin(aa) * rr * 0.45 - kk * 16))
            a255 = int(165 * fade)
            if a255 > 4 and len(pts) > 1:
                pygame.draw.lines(surface, (*P["soul_mid"], a255), False,
                                  pts, 3)
                pygame.draw.lines(surface, (*P["soul_glow"],
                                            int(a255 * 0.85)), False, pts, 1)
        # 2) inti jiwa berdenyut di dada
        pulse = 0.75 + 0.25 * math.sin(self.age * 11.0)
        core = int((8 + 9 * min(1.0, t / 0.5)) * pulse)
        _blit_faded(surface, glow_surface(core + 4, P["soul_light"], 1.0),
                    cx, cy, int(210 * fade), additive=True)
        _blit_faded(surface, glow_surface(max(2, core // 2), P["soul_glow"],
                                          1.0),
                    cx, cy, int(235 * fade), additive=True)
        # 3) simbol devour: rahang segitiga yang menutup
        bite = 1.0 - min(1.0, max(0.0, (t - 0.30) / 0.34))
        gap = 3.0 + 9.0 * bite
        col = (*P["soul_glow"], int(220 * fade))
        for sgn in (-1, 1):
            pygame.draw.polygon(surface, col, [
                (cx - core, cy + sgn * gap),
                (cx + core, cy + sgn * gap),
                (cx, cy + sgn * (gap + core * 0.75))])
        # 4) kilau heal saat jiwa tertelan
        if t >= 0.62:
            ht = 1.0 - min(1.0, (t - 0.62) / 0.30)
            spark_star(surface, cx, cy, 12 + 16 * ht, P["soul_glow"],
                       int(200 * ht), spikes=6, rot=self.age,
                       core=P["fire_white"])

    def _fnt_e(self, surface):
        """SCORCHED EARTH: duri api MENJULUR dari tanah + shockwave ganda."""
        t = self.t
        if t < 0.14:
            return
        r = self.r_screen(0.94)
        if t < 0.66:
            st = (t - 0.14) / 0.52
            n = 16
            h = int(self.r_screen(0.36) * _ease("oc", min(1.0, st * 1.4)))
            inv = int(240 * (1.0 - max(0.0, (t - 0.5) / 0.32)))
            if h > 3 and inv > 3:
                for i in range(n):
                    a = i * math.tau / n + _hash01(self.seed + i) * 0.3
                    sx = self.x + math.cos(a) * r
                    sy = self.y + 10 + math.sin(a) * r * 0.42
                    tipy = sy - h * (0.7 + _hash01(self.seed + i * 7) * 0.6)
                    tipx = sx + math.cos(a) * h * 0.3
                    # duri: bayangan -> inti gelap -> lidah api
                    pygame.draw.polygon(surface, (*P["fire_darkest"], inv),
                                        [(sx - 4, sy + 2), (sx + 4, sy + 2),
                                         (tipx, tipy)])
                    pygame.draw.polygon(surface, (*P["fire_mid"], inv),
                                        [(sx - 2.5, sy), (sx + 2.5, sy),
                                         (tipx, tipy + 3)])
                    pygame.draw.polygon(surface, (*P["fire_hot"], inv),
                                        [(sx - 1, sy - 2), (sx + 1, sy - 2),
                                         (tipx, tipy + 6)])
                    _blit_faded(surface, ember_surface(3, P["fire_glow"]),
                                tipx, tipy, inv, additive=True)
            # duri dalam (cincin kedua, lebih pendek)
            if h > 3 and inv > 3:
                r2 = self.r_screen(0.58)
                for i in range(10):
                    a = (i + 0.5) * math.tau / 10.0
                    sx = self.x + math.cos(a) * r2
                    sy = self.y + 10 + math.sin(a) * r2 * 0.42
                    h2 = int(h * 0.68)
                    pygame.draw.polygon(surface,
                                        (*P["fire_dark"], int(inv * 0.9)),
                                        [(sx - 3, sy + 2), (sx + 3, sy + 2),
                                         (sx, sy - h2)])
                    pygame.draw.polygon(surface,
                                        (*P["fire_bright"], int(inv * 0.9)),
                                        [(sx - 1.4, sy), (sx + 1.4, sy),
                                         (sx, sy - h2 + 4)])
        # shockwave ganda
        if t < 0.48:
            sw = (t - 0.14) / 0.34
            rr = int(r * (0.4 + 0.9 * _ease("oc", min(1.0, sw))))
            inv = int(195 * (1.0 - sw))
            if rr > 4 and inv > 3:
                _blit_faded(surface,
                            ellipse_ring_surface(rr, int(rr * 0.42),
                                                 max(1, int(3 * (1 - sw))
                                                     + 1),
                                                 P["molten_bright"], 255),
                            self.x, self.y + 10, inv, additive=True)
                _blit_faded(surface,
                            ellipse_ring_surface(int(rr * 0.66),
                                                 int(rr * 0.28),
                                                 max(1, int(2 * (1 - sw))
                                                     + 1),
                                                 P["fire_hot"], 255),
                            self.x, self.y + 10, int(inv * 0.8),
                            additive=True)

    def _fnt_r(self, surface):
        """INFERNAL BLADE: sabit api raksasa yang menyapu + pilar rekahan."""
        t = self.t
        if t < 0.24 or t > 0.92:
            return
        base = 0.0 if self.facing > 0 else math.pi
        # 1) SABIT: tiga busur meruncing yang menyapu turun (bukan cincin)
        st = max(0.0, min(1.0, (t - 0.24) / 0.34))
        inv = 1.0 - max(0.0, (t - 0.52) / 0.40)
        if inv > 0.03:
            sweep = -1.15 + 2.30 * _ease("oc", st)   # atas -> bawah
            span = 1.35
            for k, (sc, wd, col) in enumerate((
                    (1.00, 5, P["fire_dark"]),
                    (0.94, 3, P["fire_bright"]),
                    (0.88, 2, P["fire_glow"]))):
                rr = self.r_screen(0.42) * sc
                pts = []
                for i in range(13):
                    a = base + sweep - span / 2 + span * i / 12.0
                    pts.append((self.x + math.cos(a) * rr * self.facing
                                * (1 if self.facing > 0 else 1),
                                self.y - 6 + math.sin(a) * rr * 0.9))
                a255 = int((210 - k * 30) * inv)
                if a255 > 4 and len(pts) > 1:
                    pygame.draw.lines(surface, (*col, a255), False, pts, wd)
            # kilat di puncak sabit
            tipa = base + sweep
            spark_star(surface,
                       self.x + math.cos(tipa) * self.r_screen(0.42),
                       self.y - 6 + math.sin(tipa) * self.r_screen(0.42)
                       * 0.9,
                       10 + 12 * inv, P["fire_glow"], int(220 * inv),
                       spikes=6, rot=tipa, core=P["fire_white"])
        # 2) PILAR api dari rekahan sepanjang arah tebasan
        if t >= 0.34:
            pt = min(1.0, (t - 0.34) / 0.30)
            pfade = 1.0 - max(0.0, (t - 0.66) / 0.26)
            if pfade > 0.03:
                for i in range(6):
                    f = (i + 1) / 6.0
                    if f > pt:
                        break
                    px = self.x + self.facing * self.r_screen(0.9) * f
                    py = self.y + 12
                    hh = self.r_screen(0.22) * (1.1 - f * 0.45) * \
                        _ease("out", min(1.0, (pt - f) * 3.0 + 0.3))
                    if hh < 4:
                        continue
                    flame_poly(surface, px, py, hh,
                               seed=self.seed + i * 11,
                               alpha=int(230 * pfade),
                               phase=self.age * 3.0 + i,
                               w=hh * 0.34)

    # ------------------------------------------------------------------
    @staticmethod
    def _draw_ghost_procedural(surface, px, py, side, a):
        """Siluet iblis sederhana (fallback afterimage tanpa rig)."""
        col = (*P["molten_dark"], a)
        pygame.draw.ellipse(surface, col,
                            (int(px - 16), int(py - 6), 32, 26))
        pygame.draw.ellipse(surface, col,
                            (int(px + side * 6), int(py - 20), 15, 15))
        pygame.draw.polygon(surface, col,
                            [(px - 15, py + 16), (px + 15, py + 16),
                             (px + 9, py + 30), (px - 9, py + 30)])
        pygame.draw.line(surface, (*P["fire_bright"], a),
                         (int(px + side * 13), int(py - 12)),
                         (int(px + side * 26), int(py - 22)), 3)


# ============================================================================
# 12.  TERJANGAN R — offset gerakan Infernal Blade (SATU sumber angka)
# ============================================================================

def _lunge_offset_fallback(t):
    """Offset terjangan R (px dunia, arah facing) untuk fraksi umur FX."""
    # pose R = 70 frame; puncak (engine progress 0.30-0.58) = jarak penuh
    if t < 0.26:
        return 46.0 * _ease("oc", t / 0.26)
    if t < 0.50:
        return 46.0
    if t < 0.86:
        return 46.0 * (1.0 - _ease("io", (t - 0.50) / 0.36))
    return 0.0


def lunge_offset(skill_fx, t):
    """Offset terjangan skill R (px dunia; facing ditambahkan di caller).

    ``t`` adalah fraksi umur FX (0..1 termasuk ekor AFTER).  Renderer
    menghitung dalam PROGRESS ENGINE (0..1 sepanjang SKILL_DUR), jadi
    ``t`` dikonversi dulu: ``engine = t / ENGINE_SPAN``.  Fallback lokal
    memakai tabel dalam fraksi umur FX sehingga hasilnya identik.
    """
    R = _renderer()
    fn = getattr(R, "_lunge_offset", None) if R is not None else None
    if fn is not None:
        try:
            eng = max(0.0, min(1.0, float(t) / SkillFX.ENGINE_SPAN))
            return float(fn(eng))
        except Exception:                        # pragma: no cover
            pass
    return _lunge_offset_fallback(max(0.0, min(1.0, float(t))))


#: Alias kompatibilitas: modul FX lain (dan alat uji lama) memanggil
#: ``dash_offset``.  Pyrenth tidak melakukan dash kuda seperti Vokrahn —
#: gerakan majunya adalah TERJANGAN tebasan R — tapi kontrak namanya
#: dipertahankan supaya kode pemanggil tidak perlu bercabang.
dash_offset = lunge_offset


# ============================================================================
# 13.  FX DIRECTOR
# ============================================================================

class PyrenthFXDirector:
    """Mengikat trail, partikel, proyektil, skill, dampak, dan game feel
    untuk SATU Pyrenth (boss lane maupun hero lane)."""

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
        self.melee = True          # Pyrenth selalu melee

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
        st = getattr(boss, "_pyr_state", None)
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
        ap = float(getattr(boss, "_pyr_attack_progress", 0.0) or 0.0)
        self.attack_progress = ap
        self.attack_phase = attack_phase(ap)
        lo, hi = ATTACK_ACTIVE_WINDOW
        self.attack_active = lo <= ap <= hi

        action, _phase, _ap = pose_of(boss)
        self.melee = action in ("swing", "attack", "melee")
        swinging = action in ("swing", "attack", "melee")

        # -- trail senjata: rekam posisi bilah saat menyabet -----------
        if swinging and 0.12 <= ap <= 0.94:
            grip, hi_tip, _lo = blade_points(boss, x, y)
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
        """Bara dari bilah/kulit & debu dari kaki: hidup tapi hemat.

        Berhenti OTOMATIS kalau unit sudah 0.5 s tidak digambar (mati /
        keluar layar), jadi tidak ada efek berumur tak terbatas.
        """
        if not self.have_pos or self.draw_age > 0.5:
            return
        rate = 7.0
        if self.skill_key == "r":
            rate = 18.0                 # INFERNAL BLADE: bilah mengamuk
        elif self.skill_key == "e":
            rate = 15.0                 # SCORCHED EARTH: tanah membara
        elif self.skill_key == "w":
            rate = 4.0                  # DEVOUR: api MEREDUP, jiwa naik
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
                                     P["molten_bright"])),
                shape="ember", additive=True, drag=0.5,
                layer="back" if random.random() < 0.5 else "front")
        # DEVOUR: wisp jiwa naik dari tanah selama sedotan berlangsung
        if self.skill_key == "w":
            self.dust_acc += dt * 14.0
            while self.dust_acc >= 1.0:
                self.dust_acc -= 1.0
                if self.particles.count() > self.particles.cap * 0.85:
                    break
                a = random.uniform(0, math.tau)
                r = random.uniform(30, 90)
                self.particles.spawn(
                    self.x + math.cos(a) * r,
                    self.y + 22 + math.sin(a) * r * 0.35,
                    vx=random.uniform(-8, 8), vy=random.uniform(-60, -24),
                    life=random.uniform(0.4, 0.9),
                    size=random.uniform(1.4, 3.2),
                    color=random.choice((P["soul_mid"], P["soul_light"])),
                    shape="streak", additive=True, drag=0.7,
                    layer="back")

        # debu kaki saat bergerak
        if self.state in ("WALK", "RUN"):
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

        # afterimage: terjangan ultimate (R) atau sabetan aktif
        if self.skill_key == "r" or self.attack_active:
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
        tint = P["soul_light"] if self.skill_key == "w" \
            else P["molten_dark"]
        extra = 0.0
        if self.skill_key == "r":
            # terjangan R: posisi LOGIS unit tidak ikut bergeser — ghost
            # harus digeser manual ke jalur terjangan supaya berekor.
            for s in self.skills:
                if s.skill == "r":
                    extra = s.facing * lunge_offset(s, s.t)
                    break
        self.afterimages.append(Afterimage(
            surf, self.x + off[0] + extra, self.y + off[1], 0.26, tint))

    def _melee_impact(self, boss, x, y):
        """Tebasan pedang api mendarat: flash + sabit + serpihan + feel."""
        grip, hi_tip, _lo = blade_points(boss, x, y)
        ang = math.atan2(hi_tip[1] - grip[1], hi_tip[0] - grip[0])
        px = hi_tip[0] + math.cos(ang) * 4.0
        py = hi_tip[1] + math.sin(ang) * 4.0
        self.last_impact_point = (px, py)
        self.add_impact(px, py, "melee", ang, 1.1, P["fire_bright"], 34.0)
        self.particles.burst(px, py, 13, speed=(120, 330),
                             life=(0.18, 0.44), size=(1.7, 4.2),
                             colors=(P["fire_bright"], P["fire_hot"],
                                     P["ember"]),
                             spread=1.5, direction=ang, gravity=310,
                             drag=1.1, shape="ember")
        self.particles.burst(px, py, 6, speed=(60, 180),
                             life=(0.25, 0.55), size=(1.6, 3.6),
                             colors=(P["metal_light"], P["arm_light"],
                                     P["ash"]),
                             spread=2.0, direction=ang, gravity=520,
                             shape="shard", rotation_speed=(-10, 10),
                             additive=False)
        self.particles.burst(x, y + 26, 6, speed=(50, 150),
                             life=(0.3, 0.6), size=(2.6, 5.4),
                             colors=(P["dust"], P["ash"]), spread=1.0,
                             direction=0.0 if hi_tip[0] >= x else math.pi,
                             gravity=140, shape="dust", additive=False)
        _feel_shake(6.5, 0.18)
        _feel_hit_stop(0.05)

    def start_skill(self, boss, key, x, y):
        """Mulai lifecycle FX untuk satu skill."""
        if key not in ("q", "w", "e", "r"):
            return None
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        k = body_scale(boss)
        fx = SkillFX(key, x, y, facing, getattr(boss, "target", None),
                     scale=k, director=self)
        if key in ("e", "w"):
            # SCORCHED EARTH & DEVOUR berpusat pada Pyrenth sendiri —
            # AI menjatuhkan damage/heal-nya dalam radius di sekitar
            # boss, jadi titik "bidik" FX = kaki boss, bukan target.
            fx.target_point = (x, y + 10.0)
        elif key == "r":
            # INFERNAL BLADE: tebasan ultimate sambil menerjang maju;
            # titik bidik = ujung terjangan supaya sabit, baji rekahan,
            # dan pilar api mendarat di tempat yang sama dengan sprite.
            fx._lunge_x0 = x
            fx.target_point = (x + facing * 46.0, y + 8.0)
        else:
            fx.target_point = target_point(boss, x, y)
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        self.skills.append(fx)
        return fx

    def spawn_souls(self, boss, x, y, count=SPIRIT_COUNT):
        """W — cabut ``count`` jiwa dari sekitar, tarik ke inti Pyrenth.

        Proyektilnya terbang MASUK (dari pinggir radius menuju dada),
        kebalikan proyektil biasa — itu bahasa visual DEVOUR.
        """
        k = body_scale(boss)
        r = WORLD_RADIUS["w"] * 0.85 / max(0.05, k)
        out = []
        for i in range(max(1, int(count))):
            a = (i / float(max(1, int(count)))) * math.tau + \
                random.uniform(-0.4, 0.4)
            sx = x + math.cos(a) * r
            sy = y - 10 + math.sin(a) * r * 0.45
            out.append(self.projectiles.spawn_ember(
                sx, sy, x, y - 16, speed=EMBER_SPEED, radius=12.0,
                owner=boss, scale=k))
            self.particles.burst(sx, sy, 5, speed=(30, 120),
                                 life=(0.2, 0.5), size=(1.4, 3.0),
                                 colors=(P["soul_mid"], P["soul_light"]),
                                 spread=math.tau, drag=1.4, shape="streak")
        return out

    def spawn_doom(self, boss, x, y, tx=None, ty=None):
        """Lepas Doom Bolt dari ujung bilah (skill Q)."""
        lp = launch_point(boss, x, y)
        if tx is None or ty is None:
            tx, ty = target_point(boss, x, y)
        pr = self.projectiles.spawn_doom(
            lp[0], lp[1], tx, ty, speed=DOOM_SPEED, radius=10.0,
            target=getattr(boss, "target", None), owner=boss,
            scale=body_scale(boss))
        ang = math.atan2(ty - lp[1], tx - lp[0])
        self.particles.burst(lp[0], lp[1], 9, speed=(70, 210),
                             life=(0.12, 0.32), size=(1.4, 3.2),
                             colors=(P["molten_hot"], P["fire_hot"],
                                     P["fire_bright"]),
                             spread=1.3, direction=ang, drag=1.5,
                             shape="streak")
        self.add_impact(lp[0], lp[1], "skill", ang, 0.45, P["molten_hot"],
                        16.0)
        _feel_shake(2.2, 0.09)
        return pr

    def spawn_hurt(self, boss, x, y):
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        self.particles.burst(x - facing * 7, y - 14, 10, speed=(90, 230),
                             life=(0.2, 0.45), size=(1.5, 3.4),
                             colors=(P["metal_light"], P["fire_bright"],
                                     P["molten_bright"]),
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
#      (``_pyrenth_fx``), daftar global dipakai tick() + reset_all().
# ============================================================================

_DIRECTORS = []
MAX_DIRECTORS = 12


def director_for(unit):
    """Ambil (atau buat) director FX untuk satu unit Pyrenth."""
    _sync_palette()
    d = getattr(unit, "_pyrenth_fx", None)
    if d is None:
        d = PyrenthFXDirector(unit)
        try:
            unit._pyrenth_fx = d
        except Exception:                        # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > MAX_DIRECTORS:
            _release(_DIRECTORS.pop(0))
    return d


def _release(director):
    try:
        if director.unit is not None:
            director.unit._pyrenth_fx = None
            director.unit._pyr_live_fx = False
    except Exception:                            # pragma: no cover
        pass
    director.reset()


def attach(unit):
    """Pasang lapisan hidup pada unit (dipanggil pipeline render)."""
    if not PYRENTH_FX_ENABLED or unit is None:
        return False
    try:
        director_for(unit)
    except Exception:                            # pragma: no cover
        return False
    try:
        unit._pyr_live_fx = True
    except Exception:                            # pragma: no cover
        return False
    return True


def owns(unit):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not PYRENTH_FX_ENABLED or unit is None:
        return False
    if not getattr(unit, "_pyr_live_fx", False):
        return False
    d = getattr(unit, "_pyrenth_fx", None)
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
    d = getattr(unit, "_pyrenth_fx", None)
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
    if not PYRENTH_FX_ENABLED:
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
    """Bersihkan seluruh state FX Pyrenth (ganti level / keluar match)."""
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
    """Jumlah partikel Pyrenth yang hidup (HUD performa + tes)."""
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
    d = getattr(unit, "_pyrenth_fx", None)
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
    if not PYRENTH_FX_ENABLED or unit is None:
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
    if not PYRENTH_FX_ENABLED or unit is None:
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
    if not PYRENTH_FX_ENABLED or unit is None:
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
    d.particles.burst(x, y, 13, speed=(120, 330), life=(0.18, 0.44),
                      size=(1.7, 4.2),
                      colors=(P["fire_bright"], P["fire_hot"], P["ember"]),
                      spread=1.5, direction=angle, gravity=310, drag=1.1,
                      shape="ember")
    d.particles.burst(x, y, 6, speed=(60, 180), life=(0.25, 0.55),
                      size=(1.6, 3.6),
                      colors=(P["metal_light"], P["ash"], P["dust"]),
                      spread=2.0, direction=angle, gravity=520,
                      shape="shard", rotation_speed=(-10, 10),
                      additive=False)
    _feel_shake(6.5 * power, 0.18)
    _feel_hit_stop(0.05 if not crit else 0.07)


def notify_projectile_impact(unit, x, y, angle=0.0, damage=0, crit=False,
                             kind="bolt"):
    """Doom Bolt / Soul Ember sampai di target: paket impact lengkap."""
    if not PYRENTH_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    try:
        power = 0.7 + min(1.6, float(damage) / 60.0)
    except (TypeError, ValueError):
        power = 1.0
    if crit:
        power *= 1.3
    is_soul = (kind == "ember")
    if is_soul:
        d.add_impact(x, y, "ember", angle, power, P["soul_light"], 46.0)
        d.particles.burst(x, y, 12, speed=(40, 150), life=(0.2, 0.5),
                          size=(1.5, 3.4),
                          colors=(P["soul_light"], P["soul_glow"],
                                  P["soul_mid"]),
                          gravity=-90, drag=1.6, shape="soul")
        _feel_shake(3.2 * power, 0.12)
        _feel_hit_stop(0.03)
        return
    d.add_impact(x, y, "bolt", angle, power, P["molten_bright"], 36.0)
    d.particles.burst(x, y, 12, speed=(80, 250), life=(0.2, 0.5),
                      size=(1.6, 4.0),
                      colors=(P["molten_bright"], P["fire_bright"],
                              P["fire_hot"], P["ember"]),
                      spread=2.4, direction=angle + math.pi, gravity=250,
                      drag=1.0, shape="ember")
    d.particles.burst(x, y, 4, speed=(20, 70), life=(0.35, 0.75),
                      size=(2.5, 5), colors=(P["ash"], P["dust"]),
                      gravity=-50, shape="smoke", additive=False)
    _feel_shake(3.8 * power, 0.14)
    _feel_hit_stop(0.032)


def notify_skill_cast(unit, skill, x=None, y=None):
    """Skill mulai di-cast: buat lifecycle FX + guncangan awal."""
    if not PYRENTH_FX_ENABLED or unit is None:
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
    if not PYRENTH_FX_ENABLED or unit is None:
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
    color = P["soul_glow"] if key == "r" else P["molten_bright"]
    rr = float(radius) if radius else {"q": 70.0, "w": 90.0, "e": 60.0,
                                       "r": 150.0}.get(key, 70.0)
    d.add_impact(x, y, "skill", 0.0, power, color, rr)
    d.particles.burst(x, y, 12 if key != "r" else 20, speed=(90, 300),
                      life=(0.25, 0.6), size=(2, 5),
                      colors=(P["molten_bright"], P["fire_bright"],
                              P["ember"]),
                      gravity=300, drag=0.8, shape="ember")
    _feel_shake({"q": 5.0, "w": 8.0, "e": 10.0,
                 "r": 14.0}.get(key, 6.0), 0.22)
    _feel_hit_stop({"q": 0.035, "w": 0.045, "e": 0.055,
                    "r": 0.07}.get(key, 0.04))


def notify_projectile_cast(unit, x, y, tx=None, ty=None):
    """Lepas Doom Bolt dari ujung bilah (skill Q).

    Renderer memanggil ini saat frame cast aktif dan lapisan hidup sudah
    mengambil alih proyektil; menggantikan ``_spawn_molten_bolt`` versi
    canvas.
    """
    if not PYRENTH_FX_ENABLED or unit is None:
        return None
    d = director_for(unit)
    d.sync(unit, x, y)
    return d.spawn_doom(unit, x, y, tx, ty)


def notify_hurt(unit, amount=1.0, x=None, y=None):
    """Unit terkena damage: percikan serpihan + kilat kecil."""
    if not PYRENTH_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if x is None or y is None:
        if not d.have_pos:
            return
        x, y = d.x, d.y
    d.spawn_hurt(unit, x, y)


def notify_death(unit, x=None, y=None):
    """Kematian: bara + serpihan + asap + jiwa lepas + guncangan."""
    if not PYRENTH_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if x is None or y is None:
        if not d.have_pos:
            return
        x, y = d.x, d.y
    d.add_impact(x, y, "quake", 0.0, 1.8, P["molten_hot"], 120.0)
    d.particles.burst(x, y, 28, speed=(120, 420), life=(0.4, 1.0),
                      size=(2, 6),
                      colors=(P["fire_hot"], P["fire_bright"], P["ember"],
                              P["molten_bright"]),
                      spread=math.tau, gravity=340, drag=0.7, shape="ember")
    d.particles.burst(x, y, 14, speed=(70, 260), life=(0.5, 1.1),
                      size=(1.8, 4.0),
                      colors=(P["metal_light"], P["arm_mid"],
                              P["arm_high"]),
                      spread=math.tau, gravity=620, shape="shard",
                      rotation_speed=(-12, 12), additive=False)
    d.particles.burst(x, y, 8, speed=(30, 120), life=(0.6, 1.2),
                      size=(4, 8), colors=(P["ash"], P["soul_mid"]),
                      spread=math.tau, gravity=-40, shape="smoke",
                      additive=False)
    _feel_shake(15.0, 0.48)
    _feel_hit_stop(0.08)


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
        grip, tip_hi, tip_lo = blade_points(unit, x, y)
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
        "PYRENTH [debug]",
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
    "DEBUG_CHARACTER", "PYRENTH_FX_ENABLED", "PYRENTH_PALETTE",
    "MAX_PARTICLES", "MAX_PROJECTILES", "TRAIL_SAMPLES", "MAX_IMPACTS",
    "MAX_SKILLS", "MAX_AFTERIMAGES",
    "ATTACK_PHASES", "ATTACK_ACTIVE_WINDOW", "ATTACK_IMPACT_FRAME",
    "ANIM_STATES", "SKILL_PHASES", "SKILL_DUR", "SKILL_TOTAL",
    "WORLD_RADIUS", "DOOM_SPEED", "EMBER_SPEED", "SPIRIT_COUNT",
    "MELEE_REACH", "BLADE_ARC",
    "Particle", "ParticleSystem", "SwingTrail", "ImpactFX", "Afterimage",
    "BaseProjectile", "DoomBoltProjectile", "SoulEmberProjectile",
    "ProjectileSystem", "SkillFX", "PyrenthFXDirector",
    "attach", "owns", "recently_drawn", "director_for", "projectiles_for",
    "tick", "reset_all", "total_particles", "stats",
    "draw_ground_layer", "draw_live_layer", "draw_debug_overlay",
    "notify_melee_impact", "notify_projectile_cast",
    "notify_projectile_impact", "notify_skill_cast",
    "notify_skill_impact", "notify_hurt", "notify_death",
    "blade_arc", "blade_points", "blade_tip", "blade_angle",
    "launch_point", "attack_phase", "skill_phase", "pose_of",
    "render_scale", "body_scale", "screen_point", "target_point",
    "ring_radius", "lunge_offset", "dash_offset",
    "particle_budget", "glow_allowed", "shake_allowed",
    "glow_surface", "ring_surface", "ellipse_ring_surface",
    "ground_pool_surface", "ember_surface", "arc_ring_surface",
    "spike_ring_surface", "shard_poly", "flame_poly", "spark_star",
    "chevron", "crack_points", "star_poly_points", "molten_star_points",
    "taper_lane", "blit_add",
    "clear_cache", "cache_size",
]
