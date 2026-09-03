# ============================================================================
# heroes/zharok_fx.py
# ----------------------------------------------------------------------------
# ZHAROK — THE EMBERBORN  ·  LAPISAN TEMPUR HIDUP (v3)
#
# Rangka kerja ini adalah pasangan dari renderer ``bosses/level4.py ::
# _NS_zharok``.  Pembagian tugasnya tegas:
#
#   renderer  -> SATU-SATUNYA pemilik geometri badan & busur (rig, palet,
#                pose, controller animasi, ARK ayunan, telegraph fallback)
#   modul ini -> SEMUA yang hidup di RUANG LAYAR skala 1:1 — swing trail,
#                particle system, proyektil (anak panah api & tengkorak
#                jiwa), skill FX q/w/e/r, impact FX, afterimage, overlay
#                debug
#   combat_feel -> bus global hit-stop & screen shake (dipakai bersama)
#
# Kenapa dipisah?  Di lane hero, sprite badan di-*cache* lalu
# ``smoothscale``-kan.  Efek apa pun yang digambar ke canvas badan ikut
# BEKU dan ikut MENYUSUT.  Dengan memisahkan lapisan hidup ke ruang layar,
# trail/partikel/proyektil selalu 60 fps sejati dan selalu setajam layar.
#
# Modul ini TIDAK pernah menghitung ulang pose.  Ia MEMBACA
# ``_NS_zharok.bow_geometry()`` / ``_bow_arc()`` / ``_zh_state`` lewat
# jembatan malas ``_renderer()``, jadi busur dan trail-nya mustahil
# berbeda satu frame pun.
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
ZHAROK_FX_ENABLED = True

#: Cap keras — tidak ada satu pun sistem yang boleh tumbuh tanpa batas.
MAX_PARTICLES = 200
MAX_PROJECTILES = 22
TRAIL_SAMPLES = 10
MAX_IMPACTS = 9
MAX_SKILLS = 5
MAX_AFTERIMAGES = 7

FIXED_DT = 1.0 / 60.0

#: Kecepatan proyektil (px dunia / detik).
ARROW_SPEED = 760.0          # anak panah serangan dasar
VOLLEY_SPEED = 840.0         # anak panah Strafe (Q) — lebih cepat, lebih tipis
SKULL_SPEED = 310.0          # tengkorak jiwa Burning Army (R)

#: Durasi pose skill dalam FRAME — HARUS sama dengan
#: ``base_boss._cast_zharok_*`` dan ``_NS_zharok.SKILL_DUR``.
SKILL_DUR = {"q": 50, "w": 40, "e": 60, "r": 80}

#: Durasi lifecycle FX (detik) — sedikit lebih panjang dari pose supaya
#: tahap AFTER (asap/bara sisa) sempat memudar dengan wajar.
SKILL_TOTAL = {"q": 1.20, "w": 1.05, "e": 1.45, "r": 1.95}

#: Radius efek di RUANG DUNIA — sama persis dengan radius damage AI
#: (``_cast_zharok_e`` 150, ``_cast_zharok_r`` 220) dan dengan
#: ``_NS_zharok.SKILL_RADIUS``.  Dikunci oleh tes regresi.
WORLD_RADIUS = {"q": 250.0, "w": 200.0, "e": 150.0, "r": 220.0}

#: Jumlah entitas yang dipanggil / dilepas skill.
ARMY_COUNT = 5               # R — Burning Army
VOLLEY_COUNT = 6             # Q — Strafe

#: Jarak dunia (px) di bawahnya Zharok berhenti menembak dan beralih ke
#: Ember Cleave — menebas dengan badan busur.  Satu sumber kebenaran:
#: ``_NS_zharok.MELEE_REACH`` dan hook benturan di ``base_boss`` sama-sama
#: memakai angka ini, jadi animasi tebasan dan damage tidak pernah beda
#: pendapat soal "ini serangan dekat atau jauh".
MELEE_REACH = 74.0

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

#: Jendela hit aktif + frame impact.  ``0.52`` sengaja dipertahankan dari
#: timeline archery v2 (``_attack_pose`` memuncak tepat di sana).
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


# ============================================================================
# 2.  PALETTE — Emberborn (disinkronkan dari renderer)
# ============================================================================

ZHAROK_PALETTE = {
    # Hellfire 8-band
    "fire_darkest":  (48,  10,   8),
    "fire_dark":     (128, 28,  12),
    "fire_mid":      (210, 68,  18),
    "fire_bright":   (255, 124, 32),
    "fire_hot":      (255, 182, 64),
    "fire_glow":     (255, 224, 128),
    "fire_white":    (255, 252, 220),
    "fire_seam":     (255, 240, 180),

    # Soulfire 4-band (inti jiwa / tengkorak)
    "soul_dark":     (160, 25,  10),
    "soul_mid":      (255, 95,  25),
    "soul_hot":      (255, 205, 80),
    "soul_glow":     (255, 245, 180),

    # Bone ivory
    "bone_dark":     (74,  54,  32),
    "bone_mid":      (142, 114, 68),
    "bone_light":    (208, 178, 118),
    "bone_high":     (242, 220, 164),
    "bone_shine":    (255, 246, 212),

    # Jubah obsidian / kain compang-camping
    "hood_dark":     (42,  16,  22),
    "hood_mid":      (88,  30,  36),
    "hood_light":    (148, 54,  52),
    "hood_trim":     (228, 140, 80),

    # Kayu stave busur
    "wood_dark":     (46,  26,  14),
    "wood_mid":      (90,  54,  28),
    "wood_light":    (144, 98,  52),

    # Logam & emas
    "metal_dark":    (44,  40,  52),
    "metal_mid":     (92,  86,  102),
    "metal_light":   (158, 152, 172),
    "metal_shine":   (214, 208, 226),
    "gold_dark":     (88,  58,  18),
    "gold_mid":      (168, 124, 38),
    "gold_light":    (232, 188, 78),
    "gold_shine":    (255, 232, 142),

    # Mata / soket menyala
    "eye_bright":    (255, 125, 35),
    "eye_hot":       (255, 205, 95),
    "eye_white":     (255, 245, 215),

    # Asap ungu-dingin (Skeleton Walk)
    "smoke_dark":    (18,  10,  28),
    "smoke_mid":     (54,  36,  84),
    "smoke_light":   (114, 84,  162),
    "smoke_glow":    (190, 150, 240),

    # Turunan FX
    "ember":         (255, 158, 52),
    "ash":           (96,  84,  84),
    "dust":          (128, 112, 96),
    "shadow_deep":   (4,   2,   4),
}

#: Alias kerja — sinkron dengan renderer saat modul dipakai pertama kali.
P = dict(ZHAROK_PALETTE)

#: Kunci FX -> kunci palet renderer.  Kalau renderer mengubah warna,
#: lapisan hidup ikut berubah TANPA edit ganda.
_PALETTE_SYNC = {
    "fire_darkest": "fire_darkest", "fire_dark": "fire_dark",
    "fire_mid": "fire_mid", "fire_bright": "fire_bright",
    "fire_hot": "fire_hot", "fire_glow": "fire_glow",
    "fire_white": "fire_white", "fire_seam": "fire_seam",
    "soul_dark": "soul_dark", "soul_mid": "soul_mid",
    "soul_hot": "soul_hot", "soul_glow": "soul_glow",
    "bone_dark": "bone_dark", "bone_mid": "bone_mid",
    "bone_light": "bone_light", "bone_high": "bone_high",
    "bone_shine": "bone_shine",
    "hood_dark": "hood_dark", "hood_mid": "hood_mid",
    "hood_light": "hood_light", "hood_trim": "hood_trim",
    "wood_dark": "wood_dark", "wood_mid": "wood_mid",
    "wood_light": "wood_light",
    "metal_dark": "metal_dark", "metal_mid": "metal_mid",
    "metal_light": "metal_light", "metal_shine": "metal_shine",
    "gold_dark": "gold_dark", "gold_mid": "gold_mid",
    "gold_light": "gold_light", "gold_shine": "gold_shine",
    "eye_bright": "eye_bright", "eye_hot": "eye_hot",
    "eye_white": "eye_white",
    "smoke_dark": "smoke_dark", "smoke_mid": "smoke_mid",
    "smoke_light": "smoke_light", "smoke_glow": "smoke_glow",
    "shadow_deep": "shadow_deep",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Tarik warna dari ``_NS_zharok.PALETTE`` sekali saja (idempotent)."""
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
        P["ash"] = _mix(P["hood_dark"], P["dust"], 0.55)
    _PALETTE_SYNCED = True


# ============================================================================
# 3.  JEMBATAN KE RENDERER — satu sumber geometri & pose
# ============================================================================

_RENDERER = None          # None = belum dicari, False = tidak ada


def _renderer():
    """``_NS_zharok`` atau None.  Diimpor malas: modul boss itu besar."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level4 import _NS_zharok as Z
            _RENDERER = Z
        except Exception:                        # pragma: no cover
            _RENDERER = False
    return _RENDERER or None


#: Tabel ARK cadangan — IDENTIK dengan ``_NS_zharok.BOW_ARC`` supaya modul
#: tetap hidup (dengan geometri yang sama) kalau renderer gagal diimpor.
_ARC_FALLBACK = (
    (0.00, 0.12,  2.30,  1.92, "out"),
    (0.12, 0.30,  1.92, -1.16, "io"),
    (0.30, 0.50, -1.16,  1.74, "oc"),
    (0.50, 0.62,  1.74,  2.06, "hold"),
    (0.62, 0.82,  2.06,  2.64, "io"),
    (0.82, 1.00,  2.64,  2.30, "io"),
)

#: Setengah panjang stave busur & offset grip (px LAYAR, render_scale 1).
_STAVE_FALLBACK = 17.5
_GRIP_FALLBACK = (14.9, -7.4)


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
    p = max(0.0, min(1.0, float(progress)))
    if p < 0.30:
        return _ease("out", p / 0.30)
    if p < 0.50:
        return 1.0 - _ease("oc", (p - 0.30) / 0.20) * 0.95
    if p < 0.82:
        return 0.05 + _ease("io", (p - 0.50) / 0.32) * 0.18
    return 0.23 * (1.0 - _ease("io", (p - 0.82) / 0.18))


def _fallback_arc(progress):
    p = max(0.0, min(1.0, float(progress)))
    for t0, t1, a0, a1, kind in _ARC_FALLBACK:
        if t0 <= p < t1 or (p >= 1.0 and t1 >= 1.0):
            e = _ease(kind, (p - t0) / max(0.0001, t1 - t0))
            return a0 + (a1 - a0) * e, _fallback_lift(p)
    return _ARC_FALLBACK[0][2], 0.0


def bow_arc(progress):
    """``(theta, lift)`` ARK ayunan stave busur — SATU sumber kebenaran.

    Membaca ``_NS_zharok._bow_arc`` (fungsi yang sama yang dipakai canvas
    untuk menggambar busur); kalau renderer tidak ada, memakai tabel
    fallback yang identik di atas.
    """
    R = _renderer()
    fn = getattr(R, "_bow_arc", None) if R is not None else None
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
    action = getattr(boss, "_zh_pose_action", None)
    if action is None:
        action = {"q": "strafe", "w": "smoke", "e": "e_cast",
                  "r": "r_cast"}.get(skill)
    if action is None:
        action = ("attack" if getattr(boss, "_zh_attack_active", False)
                  else "idle")
    phase = float(getattr(boss, "pulse", 0.0) or 0.0)
    ap = float(getattr(boss, "_zh_attack_progress", 0.0) or 0.0)
    return action, phase, ap


def pose_of(boss):
    """Pose badan yang dipakai renderer: ``(action, phase, ap)``."""
    action = getattr(boss, "_zh_pose_action", None)
    if action is None:
        return _fallback_pose(boss)
    phase = float(getattr(boss, "_zh_phase", getattr(boss, "pulse", 0.0)))
    ap = float(getattr(boss, "_zh_attack_progress", 0.0) or 0.0)
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


def bow_points(boss, x, y):
    """``(grip, tip_atas, tip_bawah)`` stave busur di RUANG LAYAR.

    Memakai ``_NS_zharok.bow_geometry`` — fungsi yang sama yang dipakai
    canvas untuk menggambar busur, jadi trail tidak mungkin melenceng
    dari senjatanya.
    """
    action, phase, ap = pose_of(boss)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)
    R = _renderer()
    fn = getattr(R, "bow_geometry", None) if R is not None else None
    if fn is not None:
        try:
            grip, hi, lo, _theta = fn(facing, action, phase, ap)
            return ((x + grip[0] * k, y + grip[1] * k),
                    (x + hi[0] * k, y + hi[1] * k),
                    (x + lo[0] * k, y + lo[1] * k))
        except Exception:                        # pragma: no cover
            pass
    # fallback: hitung sendiri dengan tabel identik
    if action in ("melee", "swing", "cleave"):
        theta, lift = bow_arc(ap)
    else:
        theta, lift = 0.12 * math.sin(phase * 0.8), 0.0
    gx = facing * (_GRIP_FALLBACK[0] + 4.0 * lift)
    gy = _GRIP_FALLBACK[1] - 9.0 * lift
    dx = facing * math.sin(theta) * _STAVE_FALLBACK
    dy = -math.cos(theta) * _STAVE_FALLBACK
    return ((x + gx * k, y + gy * k),
            (x + (gx + dx) * k, y + (gy + dy) * k),
            (x + (gx - dx) * k, y + (gy - dy) * k))


def bow_angle(boss, x, y):
    """Sudut stave busur (radian, ruang layar) dari tip bawah ke atas."""
    _grip, hi, lo = bow_points(boss, x, y)
    return math.atan2(hi[1] - lo[1], hi[0] - lo[0])


def nock_point(boss, x, y):
    """Titik lepas anak panah (ruang layar) — depan grip busur."""
    grip, hi, lo = bow_points(boss, x, y)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)
    # sedikit di depan grip, di tengah antara kedua limb
    mx = (hi[0] + lo[0]) * 0.5
    my = (hi[1] + lo[1]) * 0.5
    return (grip[0] * 0.35 + mx * 0.65 + facing * 6.0 * k,
            grip[1] * 0.35 + my * 0.65)


def target_point(boss, x, y):
    """Titik target serangan dasar di ruang LAYAR (untuk proyektil)."""
    tgt = getattr(boss, "target", None)
    if tgt is not None and getattr(tgt, "alive", False):
        k = render_scale(boss)
        bx = float(getattr(boss, "x", x))
        by = float(getattr(boss, "y", y))
        return (x + (float(getattr(tgt, "x", bx)) - bx) / k,
                y + (float(getattr(tgt, "y", by)) - by) / k - 6.0)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    return (x + facing * 180.0, y - 10.0)


def ring_radius(boss, world_px):
    """Radius dunia -> radius layar (kompensasi skala hero-lane)."""
    return float(world_px) / max(0.05, render_scale(boss))


def particle_budget():
    return MAX_PARTICLES


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
    tmp = surf.copy()
    tmp.set_alpha(int(alpha))
    surface.blit(tmp, rect.topleft)


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
    """Genangan tanah elips ber-falloff (bara / lava / darah jiwa)."""
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


# -- primitif langsung (tanpa cache, bentuknya selalu unik) ------------------

def shard_poly(surface, cx, cy, ang, length, width, color, alpha=255):
    """Serpihan tulang / obsidian: belah ketupat meruncing."""
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
    """Titik pentagram (dipakai Death Pact) — jelas BUKAN lingkaran."""
    out = []
    step = math.tau / points
    for i in range(points):
        a = rot + i * step * 2.0
        out.append((cx + math.cos(a) * radius,
                    cy + math.sin(a) * radius * squash))
    return out


def taper_lane(surface, x0, y0, x1, y1, w0, w1, color, alpha):
    """Pita/koridor meruncing (telegraph Strafe) — bukan kerucut bulat."""
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
              alpha=255, gravity=0.0, color=(255, 150, 40),
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
        elif shape == "bone":
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
        elif shape == "skullbit":
            # remah tengkorak: kotak chunky pixel-art
            c = max(1, int(s))
            pygame.draw.rect(surface, color, (x - c, y - c, c * 2, c * 2))
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
        return self._next().spawn(x, y, **kw)

    def burst(self, x, y, count, speed=(40, 140), life=(0.2, 0.5),
              size=(2, 5), colors=((255, 150, 40),), spread=math.tau,
              direction=0.0, gravity=0.0, drag=0.0, shape="ember",
              additive=True, layer="front", rotation_speed=(0.0, 0.0),
              scatter=0.0, lift=0.0):
        """Ledakan partikel terarah (sudut, sebaran, kecepatan, umur,
        ukuran, warna, gravitasi, drag, rotasi) dalam satu panggilan."""
        count = max(0, int(count))
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
# 7.  SWING TRAIL — pita sabetan dari histori posisi senjata
# ============================================================================

class SwingTrail:
    """Trail stave busur Zharok.

    Menyimpan beberapa posisi senjata terakhir::

        OLD POSITION -> OLD POSITION -> OLD POSITION -> CURRENT POSITION

    lalu menyusunnya menjadi poligon translucent yang memudar.  Setiap
    PASANGAN sample jadi quad-nya SENDIRI dengan alpha sendiri (baru =
    terang, lama = nyaris hilang) — itu yang membuat sabetan terbaca
    sebagai *gerak*, bukan sebagai pelat oranye.
    """

    def __init__(self, samples=TRAIL_SAMPLES, life=0.14):
        self.samples = max(4, int(samples))
        self.life = float(life)
        self.history = []            # [[pangkal, ujung, umur, panas]]
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
            # pita hanya menutup bagian TERLUAR stave supaya tidak
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
            pygame.draw.polygon(buf, (*P["fire_dark"], int(52 * f)),
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
      ``melee``  — sabetan stave busur (busur sabit + retakan tanah)
      ``arrow``  — anak panah api menancap (ledakan bergerigi + serpihan)
      ``skull``  — tengkorak jiwa meledak (cangkang jiwa + remah tulang)
      ``skill``  — dampak umum skill
    """

    LIFE = {"melee": 0.28, "arrow": 0.30, "skull": 0.38, "skill": 0.36}

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
        elif self.kind == "arrow":
            self._draw_burst(surface, t, inv)
        elif self.kind == "skull":
            self._draw_soul(surface, t, inv)

    # ------------------------------------------------------------------
    def _draw_slash(self, surface, t, inv):
        """Fragmen sabit: tiga busur tipis melintang arah pukulan."""
        span = 1.2
        for k, (sc, wd, col) in enumerate((
                (1.0, 2, P["fire_hot"]),
                (0.72, 2, P["fire_bright"]),
                (1.22, 1, P["fire_mid"]))):
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
                pygame.draw.lines(surface, (*P["fire_dark"], int(160 * inv)),
                                  False, pts, 2)

    def _draw_burst(self, surface, t, inv):
        """Ledakan anak panah: cangkang api bergerigi + pecahan mata panah."""
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

    def _draw_soul(self, surface, t, inv):
        """Tengkorak jiwa pecah: cangkang jiwa + remah tulang berputar."""
        r = self.radius * (0.26 + 0.85 * _ease("oc", t))
        rect = pygame.Rect(int(self.x - r), int(self.y - r * 0.9),
                           int(r * 2), int(r * 1.8))
        if rect.width > 3 and rect.height > 3:
            pygame.draw.ellipse(surface, (*P["soul_mid"], int(90 * inv)),
                                rect, max(1, int(3 * inv) + 1))
        for k in range(6):
            a = _hash01(self.seed + k * 17) * math.tau + t * 3.0
            d = r * (0.55 + _hash01(self.seed + k * 23) * 0.7)
            px = self.x + math.cos(a) * d
            py = self.y + math.sin(a) * d * 0.85
            c = max(1, int(3 * inv) + 1)
            pygame.draw.rect(surface, (*P["bone_light"], int(210 * inv)),
                             (int(px - c), int(py - c), c * 2, c * 2))


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

    def __init__(self, x, y, tx, ty, speed=ARROW_SPEED, damage=0.0,
                 lifetime=1.8, radius=10.0, target=None, owner=None):
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


class FireArrowProjectile(BaseProjectile):
    """Anak panah hellfire: shaft kayu + broadhead logam + selubung api
    + pita ekor + bara.  Berputar mengikuti arah gerak (bukan lingkaran).
    """

    kind = "arrow"

    def __init__(self, x, y, tx, ty, speed=ARROW_SPEED, damage=0.0,
                 lifetime=1.7, radius=10.0, target=None, owner=None,
                 scale=1.0, homing=0.0):
        super().__init__(x, y, tx, ty, speed, damage, lifetime, radius,
                         target, owner)
        self.scale = float(scale)
        self.homing = float(homing)
        self.trail_len = 11
        self.length = 22.0 * self.scale
        self._emit_acc = 0.0

    def travel(self, dt):
        if self.homing > 0.0:
            tgt = self.target
            if tgt is not None and getattr(tgt, "alive", False):
                want = pygame.Vector2(float(getattr(tgt, "x", 0.0)),
                                      float(getattr(tgt, "y", 0.0))) \
                    - self.position
                if want.length_squared() > 1e-6:
                    want = want.normalize()
                    self.direction = (self.direction
                                      + want * self.homing * dt * 6.0)
                    if self.direction.length_squared() > 1e-6:
                        self.direction = self.direction.normalize()
                        self.velocity = self.direction * self.speed
        self.position += self.velocity * dt
        self.rotation = math.atan2(self.direction.y, self.direction.x)

    def emit(self, dt, system):
        if system is None:
            return
        self._emit_acc += dt
        if self._emit_acc < 0.026:
            return
        self._emit_acc = 0.0
        ps = system.particles
        if ps.count() > ps.cap * 0.85:
            return
        back = -self.direction
        ps.spawn(self.position.x + back.x * 8.0,
                 self.position.y + back.y * 8.0,
                 vx=back.x * random.uniform(20, 70)
                 + random.uniform(-24, 24),
                 vy=back.y * random.uniform(20, 70)
                 + random.uniform(-24, 24),
                 life=random.uniform(0.16, 0.36),
                 size=random.uniform(1.2, 2.4) * self.scale,
                 color=random.choice((P["fire_bright"], P["fire_hot"],
                                      P["ember"])),
                 shape="ember", additive=True, drag=1.4)

    # -- gambar --------------------------------------------------------
    def draw(self, surface):
        if not self.active:
            return
        self._draw_ribbon(surface, 5.0 * self.scale, 1.2 * self.scale,
                          ((P["fire_dark"], 0.34, 1.6),
                           (P["fire_mid"], 0.55, 1.0),
                           (P["fire_glow"], 0.85, 0.45)))
        x, y = self.position.x, self.position.y
        ca, sa = math.cos(self.rotation), math.sin(self.rotation)
        px, py = -sa, ca
        L = self.length
        k = self.scale

        # glow selubung (lonjong searah gerak)
        halo = _scratch(int(L * 2.4) + 14, int(L * 1.2) + 14)
        hw, hh = halo.get_size()
        pygame.draw.ellipse(halo, (*P["fire_dark"], 90),
                            (2, hh // 2 - int(4 * k) - 2,
                             hw - 4, int(8 * k) + 4))
        blit_add(surface, halo, (int(x - hw / 2 + ca * L * 0.15),
                                 int(y - hh / 2 + sa * L * 0.15)))

        tipx, tipy = x + ca * L * 0.62, y + sa * L * 0.62
        tailx, taily = x - ca * L * 0.55, y - sa * L * 0.55

        # shaft kayu (dengan selout gelap)
        pygame.draw.line(surface, (*P["shadow_deep"], 200),
                         (tailx + 1, taily + 1), (tipx + 1, tipy + 1),
                         max(2, int(3 * k)))
        pygame.draw.line(surface, (*P["wood_dark"], 255), (tailx, taily),
                         (tipx, tipy), max(2, int(3 * k)))
        pygame.draw.line(surface, (*P["wood_light"], 255),
                         (tailx - py, taily + px), (tipx - py, tipy + px),
                         max(1, int(1 * k)))

        # broadhead: poligon 4 titik meruncing
        head = [(tipx + ca * 7 * k, tipy + sa * 7 * k),
                (tipx - ca * 2 * k + px * 3.4 * k,
                 tipy - sa * 2 * k + py * 3.4 * k),
                (tipx - ca * 5 * k, tipy - sa * 5 * k),
                (tipx - ca * 2 * k - px * 3.4 * k,
                 tipy - sa * 2 * k - py * 3.4 * k)]
        pygame.draw.polygon(surface, (*P["metal_dark"], 255), head)
        pygame.draw.polygon(surface, (*P["metal_shine"], 255), head[:3], 1)

        # fletching: dua segitiga di ekor
        for s in (1, -1):
            pygame.draw.polygon(surface, (*P["hood_mid"], 235), [
                (tailx, taily),
                (tailx - ca * 6 * k + px * 4.2 * k * s,
                 taily - sa * 6 * k + py * 4.2 * k * s),
                (tailx - ca * 2 * k, taily - sa * 2 * k)])

        # inti api di ujung + kilau putih
        _blit_faded(surface, glow_surface(int(7 * k) + 3, P["fire_bright"],
                                          1.0), tipx, tipy, 225,
                    additive=True)
        pygame.draw.circle(surface, (*P["fire_hot"], 255),
                           (int(tipx), int(tipy)), max(1, int(2.4 * k)))
        pygame.draw.circle(surface, (*P["fire_white"], 255),
                           (int(tipx), int(tipy)), max(1, int(1.2 * k)))


class SoulSkullProjectile(BaseProjectile):
    """Tengkorak jiwa Burning Army (R).

    Mengorbit caster sebentar (fase panggil), lalu MENGUNCI target dan
    menukik.  Bentuknya tengkorak chunky dengan soket mata menyala dan
    ekor api — bukan lingkaran.
    """

    kind = "skull"

    def __init__(self, x, y, tx, ty, speed=SKULL_SPEED, damage=0.0,
                 lifetime=2.6, radius=14.0, target=None, owner=None,
                 orbit_center=None, orbit_radius=58.0, orbit_phase=0.0,
                 orbit_time=0.55):
        super().__init__(x, y, tx, ty, speed, damage, lifetime, radius,
                         target, owner)
        self.trail_len = 9
        self.orbit_center = pygame.Vector2(orbit_center) \
            if orbit_center is not None else pygame.Vector2(x, y)
        self.orbit_radius = float(orbit_radius)
        self.orbit_phase = float(orbit_phase)
        self.orbit_time = float(orbit_time)
        self.orbiting = True
        self.bob = random.uniform(0.0, math.tau)
        self._emit_acc = 0.0

    def follow_center(self, x, y):
        self.orbit_center.update(float(x), float(y))

    def travel(self, dt):
        if self.orbiting:
            self.orbit_phase += dt * 3.2
            self.position.update(
                self.orbit_center.x
                + math.cos(self.orbit_phase) * self.orbit_radius,
                self.orbit_center.y
                + math.sin(self.orbit_phase) * self.orbit_radius * 0.42
                - 18.0 + math.sin(self.bob + self.age * 5.0) * 4.0)
            if self.age >= self.orbit_time:
                self.orbiting = False
                d = self.destination - self.position
                if d.length_squared() > 1e-6:
                    self.direction = d.normalize()
                self.velocity = self.direction * self.speed
            return
        tgt = self.target
        if tgt is not None and getattr(tgt, "alive", False):
            want = pygame.Vector2(float(getattr(tgt, "x", 0.0)),
                                  float(getattr(tgt, "y", 0.0))) \
                - self.position
            if want.length_squared() > 1e-6:
                self.direction = (self.direction
                                  + want.normalize() * dt * 3.0)
                if self.direction.length_squared() > 1e-6:
                    self.direction = self.direction.normalize()
        self.velocity = self.direction * self.speed
        self.position += self.velocity * dt
        self.rotation = math.atan2(self.direction.y, self.direction.x)

    def check_collision(self):
        if self.orbiting:
            return False
        return super().check_collision()

    def emit(self, dt, system):
        if system is None:
            return
        self._emit_acc += dt
        if self._emit_acc < 0.05:
            return
        self._emit_acc = 0.0
        ps = system.particles
        if ps.count() > ps.cap * 0.85:
            return
        ps.spawn(self.position.x + random.uniform(-4, 4),
                 self.position.y + random.uniform(-2, 6),
                 vx=random.uniform(-16, 16), vy=random.uniform(-46, -12),
                 life=random.uniform(0.24, 0.5),
                 size=random.uniform(1.4, 2.8),
                 color=random.choice((P["soul_mid"], P["fire_bright"],
                                      P["ember"])),
                 shape="ember", additive=True, drag=0.8)

    def draw(self, surface):
        if not self.active:
            return
        self._draw_ribbon(surface, 6.0, 1.5,
                          ((P["fire_dark"], 0.28, 1.7),
                           (P["soul_mid"], 0.5, 1.0),
                           (P["soul_hot"], 0.75, 0.5)), fade=0.2)
        x, y = int(self.position.x), int(self.position.y)
        _blit_faded(surface, glow_surface(15, P["fire_dark"], 0.7), x, y,
                    170, additive=True)

        # tempurung tengkorak (poligon chunky)
        s = 6
        skull = [(x - s, y - s), (x + s, y - s), (x + s + 1, y + 1),
                 (x + s - 2, y + s), (x - s + 2, y + s), (x - s - 1, y + 1)]
        pygame.draw.polygon(surface, (*P["shadow_deep"], 220),
                            [(px + 1, py + 1) for px, py in skull])
        pygame.draw.polygon(surface, (*P["bone_mid"], 255), skull)
        pygame.draw.polygon(surface, (*P["bone_light"], 255),
                            [(x - s + 1, y - s + 1), (x + 1, y - s + 1),
                             (x + 1, y - 1), (x - s + 1, y - 1)])
        # soket mata menyala
        for ex in (-3, 3):
            pygame.draw.rect(surface, (*P["fire_dark"], 255),
                             (x + ex - 2, y - 3, 4, 4))
            pygame.draw.rect(surface, (*P["eye_bright"], 255),
                             (x + ex - 1, y - 2, 2, 2))
        # rahang bergigi
        for jx in range(-3, 4, 2):
            pygame.draw.rect(surface, (*P["bone_high"], 255),
                             (x + jx, y + 3, 1, 3))
        # mahkota api
        tmp = _scratch(26, 26)
        flame_poly(tmp, 13, 22, 15.0, seed=self.seed,
                   alpha=205, phase=self.age * 6.0, w=6.0)
        blit_add(surface, tmp, (x - 13, y - 22))


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

    def spawn_arrow(self, x, y, tx, ty, **kw):
        self._make_room()
        pr = FireArrowProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    def spawn_skull(self, x, y, tx, ty, **kw):
        self._make_room()
        pr = SoulSkullProjectile(x, y, tx, ty, **kw)
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
        if projectile.kind == "skull":
            self._push_impact(ImpactFX(px, py, "skull", ang, 1.3,
                                       P["soul_hot"], 52.0))
            self.particles.burst(px, py, 14, speed=(90, 300),
                                 life=(0.28, 0.66), size=(2, 4.6),
                                 colors=(P["soul_mid"], P["fire_bright"],
                                         P["ember"]),
                                 gravity=260, drag=0.8, shape="ember")
            self.particles.burst(px, py, 6, speed=(60, 190),
                                 life=(0.3, 0.7), size=(1.6, 3.2),
                                 colors=(P["bone_light"], P["bone_high"]),
                                 gravity=520, shape="skullbit",
                                 rotation_speed=(-8, 8), additive=False)
            _feel_shake(6.0, 0.18)
            _feel_hit_stop(0.045)
        else:
            self._push_impact(ImpactFX(px, py, "arrow", ang, 1.0,
                                       P["fire_bright"], 34.0))
            self.particles.burst(px, py, 12, speed=(80, 250),
                                 life=(0.2, 0.48), size=(1.6, 3.8),
                                 colors=(P["fire_bright"], P["fire_hot"],
                                         P["ember"]),
                                 spread=2.4, direction=ang + math.pi,
                                 gravity=250, drag=1.0, shape="ember")
            self.particles.burst(px, py, 4, speed=(20, 70),
                                 life=(0.35, 0.75), size=(2.5, 5),
                                 colors=(P["ash"], P["dust"]),
                                 gravity=-50, shape="smoke", additive=False)
            _feel_shake(3.6, 0.12)
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
# 10.  AFTERIMAGE — siluet pose sebelumnya (Skeleton Walk & sabetan berat)
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
        self.tint = tint or P["fire_dark"]
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
    """Efek satu skill Zharok, dengan lifecycle enam fase::

        CAST -> CHARGE -> RELEASE -> AREA/TRAVEL -> IMPACT -> AFTER -> FADE

    Setiap skill punya BENTUK khasnya sendiri — koridor (Q), kabut &
    siluet (W), pentagram & tengkorak (E), retakan magma & pilar (R) —
    supaya tidak semuanya jadi lingkaran.
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
        self._volley = 0
        self._acc = 0.0
        self._cracks = None
        self._skulls = []

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
        """Radius dunia -> radius layar (kompensasi skala hero-lane)."""
        return self.radius * mul / max(0.05, self.scale)

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

    # -- Q: Strafe -----------------------------------------------------
    def _upd_q(self, dt, particles, projectiles):
        t = self.t
        ax, ay = self.aim()
        if t < 0.16 and self._once("cast"):
            particles.burst(self.x, self.y + 26, 10, speed=(50, 170),
                            life=(0.25, 0.5), size=(2, 4),
                            colors=(P["dust"], P["ash"]), spread=math.pi,
                            direction=-math.pi / 2, gravity=180,
                            shape="dust", additive=False, layer="back")
        # RELEASE + AREA: rentetan anak panah
        if 0.30 <= t < 0.78:
            self._acc += dt
            if self._acc >= 0.075 and self._volley < VOLLEY_COUNT:
                self._acc = 0.0
                self._volley += 1
                spread = (self._volley - VOLLEY_COUNT * 0.5) * 15.0
                nx = self.x + self.facing * 22.0
                ny = self.y - 14.0
                projectiles.spawn_arrow(
                    nx, ny, ax + spread, ay + spread * 0.25,
                    speed=VOLLEY_SPEED, radius=9.0,
                    target=self.target if self._volley % 2 else None,
                    scale=0.9)
                particles.burst(nx, ny, 6, speed=(90, 240),
                                life=(0.12, 0.3), size=(1.4, 3.0),
                                colors=(P["fire_glow"], P["fire_hot"]),
                                spread=1.1,
                                direction=math.atan2(ay - ny, ax - nx),
                                drag=1.6, shape="streak")
                _feel_shake(1.8, 0.08)
        if t >= 0.74 and self._once("impact"):
            particles.burst(ax, ay, 12, speed=(70, 240), life=(0.25, 0.55),
                            size=(1.8, 4.0),
                            colors=(P["fire_bright"], P["ember"]),
                            gravity=280, drag=0.9, shape="ember")

    # -- W: Skeleton Walk ----------------------------------------------
    def _upd_w(self, dt, particles, projectiles):
        t = self.t
        if t < 0.16 and self._once("cast"):
            particles.burst(self.x, self.y + 22, 18, speed=(80, 250),
                            life=(0.3, 0.75), size=(3, 6.5),
                            colors=(P["smoke_mid"], P["smoke_light"],
                                    P["ash"]),
                            spread=math.tau, gravity=-40, drag=0.9,
                            shape="smoke", additive=False, layer="back")
            particles.burst(self.x, self.y + 20, 8, speed=(60, 190),
                            life=(0.3, 0.6), size=(1.5, 3.0),
                            colors=(P["bone_light"], P["bone_mid"]),
                            spread=math.tau, gravity=420, shape="bone",
                            rotation_speed=(-9, 9), additive=False)
            _feel_shake(5.0, 0.16)
        if 0.20 <= t < 0.80:
            self._acc += dt
            if self._acc >= 0.06:
                self._acc = 0.0
                a = random.uniform(0, math.tau)
                r = random.uniform(14, 40)
                particles.spawn(self.x + math.cos(a) * r,
                                self.y + math.sin(a) * r * 0.5 - 6,
                                vx=-math.sin(a) * 34.0,
                                vy=math.cos(a) * 14.0 - 16.0,
                                life=random.uniform(0.35, 0.75),
                                size=random.uniform(2.0, 4.2),
                                color=random.choice((P["smoke_light"],
                                                     P["smoke_glow"])),
                                shape="smoke", additive=False,
                                layer="front", drag=0.7)
        if t >= 0.80 and self._once("emerge"):
            particles.burst(self.x, self.y + 18, 16, speed=(120, 320),
                            life=(0.2, 0.5), size=(1.6, 3.6),
                            colors=(P["fire_bright"], P["smoke_glow"],
                                    P["ember"]),
                            spread=math.tau, gravity=200, drag=1.0,
                            shape="spark")
            _feel_shake(7.0, 0.2)
            _feel_hit_stop(0.035)

    # -- E: Death Pact -------------------------------------------------
    def _upd_e(self, dt, particles, projectiles):
        t = self.t
        if t < 0.16 and self._once("cast"):
            particles.burst(self.x, self.y + 26, 12, speed=(30, 110),
                            life=(0.4, 0.9), size=(2, 4.5),
                            colors=(P["soul_dark"], P["fire_dark"]),
                            spread=math.tau, gravity=-30, shape="rune",
                            rotation_speed=(-4, 4), layer="back")
        if 0.16 <= t < 0.46:
            self._acc += dt
            if self._acc >= 0.045:
                self._acc = 0.0
                a = random.uniform(0, math.tau)
                r = self.r_screen(1.0)
                particles.spawn(self.x + math.cos(a) * r,
                                self.y + 22 + math.sin(a) * r * 0.42,
                                vx=-math.cos(a) * 165.0,
                                vy=-math.sin(a) * 70.0 - 30.0,
                                life=0.42, size=random.uniform(1.6, 3.2),
                                color=random.choice((P["soul_mid"],
                                                     P["fire_bright"])),
                                shape="ember", additive=True, drag=0.4)
        if t >= 0.74 and self._once("erupt"):
            particles.burst(self.x, self.y + 16, 24, speed=(140, 400),
                            life=(0.3, 0.75), size=(2, 5),
                            colors=(P["fire_bright"], P["soul_hot"],
                                    P["ember"]),
                            spread=math.tau, gravity=340, drag=0.7,
                            shape="ember")
            particles.burst(self.x, self.y + 20, 8, speed=(70, 210),
                            life=(0.4, 0.85), size=(2, 4.5),
                            colors=(P["bone_mid"], P["ash"]),
                            spread=math.tau, gravity=560, shape="bone",
                            rotation_speed=(-11, 11), additive=False)
            _feel_shake(11.0, 0.26)
            _feel_hit_stop(0.05)

    # -- R: Burning Army -----------------------------------------------
    def _upd_r(self, dt, particles, projectiles):
        t = self.t
        if t < 0.16 and self._once("cast"):
            particles.burst(self.x, self.y + 26, 14, speed=(60, 200),
                            life=(0.35, 0.8), size=(3, 6),
                            colors=(P["ash"], P["dust"], P["smoke_mid"]),
                            spread=math.tau, gravity=-30, shape="smoke",
                            additive=False, layer="back")
            _feel_shake(8.0, 0.24)
        if 0.30 <= t < 0.52 and self._once("summon"):
            tgt = self.target
            for i in range(ARMY_COUNT):
                a = i * math.tau / ARMY_COUNT
                dx = math.cos(a) * self.r_screen(0.9)
                dy = math.sin(a) * self.r_screen(0.9) * 0.42
                pr = projectiles.spawn_skull(
                    self.x + math.cos(a) * 20.0,
                    self.y - 16.0 + math.sin(a) * 8.0,
                    self.x + dx, self.y + 18.0 + dy,
                    speed=SKULL_SPEED, radius=13.0, target=tgt,
                    orbit_center=(self.x, self.y), orbit_radius=58.0,
                    orbit_phase=a, orbit_time=0.5 + i * 0.06,
                    lifetime=2.4)
                self._skulls.append(pr)
            particles.burst(self.x, self.y + 6, 20, speed=(100, 300),
                            life=(0.3, 0.7), size=(2, 4.6),
                            colors=(P["fire_bright"], P["soul_hot"]),
                            spread=math.tau, gravity=180, drag=0.8,
                            shape="ember")
            _feel_shake(13.0, 0.3)
            _feel_hit_stop(0.065)
        # tengkorak yang masih mengorbit tetap mengikuti caster
        if self._skulls and t < 0.6:
            for pr in self._skulls:
                if pr.active and getattr(pr, "orbiting", False):
                    pr.follow_center(self.x, self.y)
        if 0.16 <= t < 0.9:
            self._acc += dt
            if self._acc >= 0.05:
                self._acc = 0.0
                a = random.uniform(0, math.tau)
                r = random.uniform(0.3, 1.0) * self.r_screen(1.0)
                particles.spawn(self.x + math.cos(a) * r,
                                self.y + 22 + math.sin(a) * r * 0.4,
                                vx=random.uniform(-16, 16),
                                vy=random.uniform(-120, -50),
                                life=random.uniform(0.4, 0.9),
                                size=random.uniform(1.6, 3.4),
                                color=random.choice((P["fire_bright"],
                                                     P["fire_hot"],
                                                     P["ember"])),
                                shape="ember", additive=True, drag=0.5,
                                layer="back" if random.random() < 0.5
                                else "front")

    # ==================================================================
    # GAMBAR — lapisan TANAH (di bawah badan)
    # ==================================================================
    def draw_ground(self, surface):
        if not self.active:
            return
        fn = getattr(self, "_gnd_" + self.skill, None)
        if fn is not None:
            fn(surface, self.t)

    def _gnd_w(self, surface, t):
        """Cincin asap menyebar + kabut tanah + telegraph radius."""
        gy = self.y + 22
        fade = 1.0 if t < 0.82 else max(0.0, 1.0 - (t - 0.82) / 0.18)
        if fade <= 0.02:
            return
        grow = _ease("oc", min(1.0, t / 0.5))
        R = self._fit(surface, self.r_screen(1.0))
        r = max(4, int(R * (0.2 + 0.8 * grow)))
        _blit_faded(surface, ground_pool_surface(r, P["smoke_mid"], 0.30),
                    self.x, gy, int(150 * fade), additive=False)
        # W tidak punya radius damage, jadi TIDAK ada telegraph lingkaran
        # penuh di sini — cukup cincin tanah beperspektif supaya kolam
        # asapnya duduk di lantai dan tidak menelan siluet Zharok.
        _blit_faded(surface,
                    ellipse_ring_surface(r, max(2, int(r * 0.42)), 2,
                                         P["smoke_light"], 255),
                    self.x, gy, int(120 * fade), additive=True)
        _blit_faded(surface,
                    arc_ring_surface(max(4, int(r * 0.62)), 7, 0.5, 2,
                                     P["smoke_glow"], 255, squash=0.42,
                                     rot=t * 1.1),
                    self.x, gy, int(105 * fade), additive=True)

    def _gnd_q(self, surface, t):
        """Koridor bidik + jejak bakar (BUKAN lingkaran)."""
        ax, ay = self.aim()
        gy = self.y + 22
        appear = _ease("out", min(1.0, t / 0.22))
        fade = 1.0 if t < 0.78 else max(0.0, 1.0 - (t - 0.78) / 0.22)
        if fade <= 0.02:
            return
        L = min(self._fit(surface, self.r_screen(1.0)),
                math.hypot(ax - self.x, ay - gy) + 40.0)
        ang = math.atan2(ay - gy, ax - self.x)
        ex = self.x + math.cos(ang) * L * appear
        ey = gy + math.sin(ang) * L * appear * 0.5
        buf = _scratch(int(abs(ex - self.x)) + 90, int(abs(ey - gy)) + 90)
        bw, bh = buf.get_size()
        ox, oy = bw // 2, bh // 2
        taper_lane(buf, ox, oy, ox + (ex - self.x), oy + (ey - gy),
                   10.0, 26.0, P["fire_dark"], int(66 * fade))
        taper_lane(buf, ox, oy, ox + (ex - self.x), oy + (ey - gy),
                   3.0, 10.0, P["fire_mid"], int(96 * fade))
        blit_add(surface, buf, (int(self.x) - ox, int(gy) - oy))
        # chevron maju di sepanjang koridor
        for i in range(4):
            u = ((t * 1.5 + i * 0.25) % 1.0)
            cx = self.x + math.cos(ang) * L * u
            cy = gy + math.sin(ang) * L * u * 0.5
            chevron(surface, cx, cy, ang, 9.0, P["fire_hot"],
                    int(150 * fade * (1.0 - u * 0.6)), 2)
        # jangkauan tembak: cincin putus-putus di radius dunia Q (250 px)
        _blit_faded(surface,
                    ring_surface(self._fit(surface, self.r_screen(1.0)),
                                 2, P["fire_mid"], 255, dashed=14),
                    self.x, gy, int(110 * fade * appear), additive=True)
        # reticle target: kurung siku berputar (bukan cincin)
        rt = 16 + 4 * math.sin(t * 22.0)
        for k in range(4):
            a = t * 3.0 + k * math.pi / 2
            c1 = (ax + math.cos(a) * rt, ay + math.sin(a) * rt * 0.6)
            c2 = (ax + math.cos(a + 0.5) * rt,
                  ay + math.sin(a + 0.5) * rt * 0.6)
            pygame.draw.line(surface, (*P["fire_bright"], int(180 * fade)),
                             c1, c2, 2)

    def _gnd_e(self, surface, t):
        """Pentagram tanah berapi + cincin runik konvergen + telegraph AoE."""
        gy = self.y + 22
        fade = 1.0 if t < 0.84 else max(0.0, 1.0 - (t - 0.84) / 0.16)
        if fade <= 0.02:
            return
        appear = _ease("out", min(1.0, t / 0.28))
        R = self._fit(surface, self.r_screen(1.0))
        r = R * appear
        _blit_faded(surface,
                    ground_pool_surface(int(r * 0.9), P["soul_dark"], 0.34),
                    self.x, gy, int(170 * fade), additive=True)
        # pentagram (5 titik dihubungkan berselang) — jelas bukan lingkaran
        pts = star_poly_points(self.x, gy, r * 0.82, 5, rot=-math.pi / 2 + t)
        if len(pts) == 5:
            order = [pts[0], pts[2], pts[4], pts[1], pts[3], pts[0]]
            pygame.draw.lines(surface, (*P["fire_dark"], int(190 * fade)),
                              False, order, 4)
            pygame.draw.lines(surface, (*P["fire_bright"], int(215 * fade)),
                              False, order, 2)
            for px, py in pts:
                pygame.draw.circle(surface,
                                   (*P["fire_glow"], int(220 * fade)),
                                   (int(px), int(py)), 3)
        _blit_faded(surface,
                    arc_ring_surface(int(max(4, r * (1.15 - 0.3 * appear))),
                                     6, 0.46, 2, P["soul_mid"], 255,
                                     squash=0.42, rot=-t * 1.4),
                    self.x, gy, int(150 * fade), additive=True)
        # TELEGRAPH AoE: lingkaran tepat di radius damage dunia (150 px).
        # Radius ini WAJIB sama dengan `_cast_zharok_e`, jadi pemain bisa
        # membaca zona bahaya dengan benar.
        _blit_faded(surface,
                    ring_surface(R, max(2, int(3 * appear)), P["fire_mid"],
                                 255),
                    self.x, gy, int(185 * fade * appear), additive=True)
        _blit_faded(surface,
                    ellipse_ring_surface(int(r), max(2, int(r * 0.42)), 2,
                                         P["fire_dark"], 255),
                    self.x, gy, int(120 * fade), additive=True)
        # erupsi: shockwave cincin memuai sampai radius damage penuh
        if t >= 0.74:
            k = (t - 0.74) / 0.26
            rr = int(R * (0.5 + 0.6 * _ease("oc", k)))
            _blit_faded(surface,
                        ring_surface(self._fit(surface, rr),
                                     max(1, int(4 * (1 - k))),
                                     P["fire_hot"], 255),
                        self.x, gy, int(210 * (1 - k)), additive=True)

    def _gnd_r(self, surface, t):
        """Retakan magma bergerigi + cincin lava + zona hangus."""
        gy = self.y + 22
        fade = 1.0 if t < 0.86 else max(0.0, 1.0 - (t - 0.86) / 0.14)
        if fade <= 0.02:
            return
        R = self._fit(surface, self.r_screen(1.0))
        if self._cracks is None:
            self._cracks = []
            for k in range(6):
                a = _hash01(self.seed + k * 13) * math.tau
                ln = R * (0.6 + _hash01(self.seed + k * 29) * 0.45)
                self._cracks.append(crack_points(
                    self.x, gy, self.x + math.cos(a) * ln,
                    gy + math.sin(a) * ln * 0.42, 6, 9.0, self.seed + k * 7))
        grow = _ease("oc", min(1.0, t / 0.4))
        _blit_faded(surface,
                    ground_pool_surface(int(R * 0.88 * grow), P["fire_dark"],
                                        0.42),
                    self.x, gy, int(180 * fade), additive=True)
        for pts in self._cracks:
            n = max(2, int(len(pts) * grow))
            seg = pts[:n]
            if len(seg) > 1:
                pygame.draw.lines(surface, (*P["fire_mid"], int(210 * fade)),
                                  False, seg, 3)
                pygame.draw.lines(surface, (*P["fire_hot"], int(180 * fade)),
                                  False, seg, 1)
        # TELEGRAPH AoE: lingkaran tepat di radius damage dunia (220 px),
        # sama persis dengan `_cast_zharok_r`.
        _blit_faded(surface,
                    ring_surface(R, max(2, int(3 * grow)), P["fire_bright"],
                                 255),
                    self.x, gy, int(195 * fade * grow), additive=True)
        _blit_faded(surface,
                    ellipse_ring_surface(int(R * grow),
                                         max(2, int(R * grow * 0.42)), 2,
                                         P["fire_mid"], 255),
                    self.x, gy, int(120 * fade), additive=True)
        _blit_faded(surface,
                    arc_ring_surface(int(R * 0.7), 8, 0.42, 2,
                                     P["fire_glow"], 255, squash=0.42,
                                     rot=t * 0.8),
                    self.x, gy, int(120 * fade), additive=True)

    # ==================================================================
    # GAMBAR — lapisan DEPAN (di atas badan)
    # ==================================================================
    def draw_front(self, surface):
        if not self.active:
            return
        fn = getattr(self, "_frn_" + self.skill, None)
        if fn is not None:
            fn(surface, self.t)

    def _frn_q(self, surface, t):
        """Kilatan moncong berulang di busur + garis bidik."""
        if not (0.26 <= t < 0.80):
            return
        bx = self.x + self.facing * 22.0
        by = self.y - 14.0
        flick = (t * 14.0) % 1.0
        if flick < 0.4:
            f = 1.0 - flick / 0.4
            spark_star(surface, bx, by, 12 * f + 4, P["fire_hot"],
                       int(215 * f), spikes=8, rot=t * 6.0,
                       core=P["fire_white"])
            _blit_faded(surface, glow_surface(int(11 * f) + 4,
                                              P["fire_bright"], 1.0),
                        bx, by, int(210 * f), additive=True)
        ax, ay = self.aim()
        pygame.draw.line(surface, (*P["fire_mid"], 70), (bx, by), (ax, ay), 1)

    def _frn_w(self, surface, t):
        """Selubung asap berputar + siluet hantu tembus pandang."""
        fade = 1.0 if t < 0.8 else max(0.0, 1.0 - (t - 0.8) / 0.2)
        if fade <= 0.02:
            return
        cy = self.y - 16
        for k in range(3):
            rr = int((26 + k * 13) * (0.6 + 0.5 * _ease("out",
                                                        min(1.0, t / 0.4))))
            _blit_faded(surface,
                        arc_ring_surface(rr, 5 + k, 0.44, 3,
                                         P["smoke_light"] if k % 2
                                         else P["smoke_glow"], 255),
                        self.x, cy, int((120 - k * 26) * fade),
                        additive=True)
        # dua mata bara menembus kabut
        if 0.25 < t < 0.85:
            for ex in (-6, 6):
                pygame.draw.circle(surface, (*P["eye_bright"],
                                             int(200 * fade)),
                                   (int(self.x + ex), int(cy - 14)), 2)
        if t >= 0.80:
            k = (t - 0.80) / 0.20
            rr = int(60 * _ease("oc", k)) + 6
            _blit_faded(surface, ring_surface(rr, max(1, int(3 * (1 - k))),
                                              P["smoke_glow"], 255),
                        self.x, cy, int(200 * (1 - k)), additive=True)

    def _frn_e(self, surface, t):
        """Tengkorak raksasa melayang + sinar kanal jiwa."""
        if t < 0.18:
            return
        fade = 1.0 if t < 0.86 else max(0.0, 1.0 - (t - 0.86) / 0.14)
        if fade <= 0.02:
            return
        rise = _ease("out", min(1.0, (t - 0.18) / 0.3))
        cy = self.y - 58 - 20 * rise + math.sin(t * 9.0) * 3.0
        s = 20.0 * rise
        if s < 2:
            return
        a = int(215 * fade)
        # tempurung besar
        skull = [(self.x - s, cy - s * 0.9), (self.x + s, cy - s * 0.9),
                 (self.x + s * 1.08, cy + s * 0.2),
                 (self.x + s * 0.66, cy + s * 0.95),
                 (self.x - s * 0.66, cy + s * 0.95),
                 (self.x - s * 1.08, cy + s * 0.2)]
        pygame.draw.polygon(surface, (*P["shadow_deep"], int(a * 0.8)),
                            [(px + 2, py + 2) for px, py in skull])
        pygame.draw.polygon(surface, (*P["bone_mid"], a), skull)
        pygame.draw.polygon(surface, (*P["bone_light"], a),
                            [(self.x - s * 0.86, cy - s * 0.72),
                             (self.x + s * 0.1, cy - s * 0.72),
                             (self.x + s * 0.1, cy - s * 0.1),
                             (self.x - s * 0.86, cy - s * 0.1)])
        # soket mata menyembur api
        for ex in (-0.42, 0.42):
            px = self.x + ex * s
            pygame.draw.polygon(surface, (*P["fire_darkest"], a), [
                (px - s * 0.26, cy - s * 0.42),
                (px + s * 0.26, cy - s * 0.42),
                (px + s * 0.18, cy + s * 0.06),
                (px - s * 0.18, cy + s * 0.06)])
            _blit_faded(surface, glow_surface(int(s * 0.42) + 2,
                                              P["fire_bright"], 1.0),
                        px, cy - s * 0.18, int(220 * fade), additive=True)
            tmp = _scratch(int(s * 1.4) + 8, int(s * 1.8) + 8)
            flame_poly(tmp, tmp.get_width() // 2, tmp.get_height() - 2,
                       s * 1.1, seed=self.seed + int(ex * 10),
                       alpha=int(200 * fade), phase=t * 20.0, w=s * 0.3)
            blit_add(surface, tmp, (int(px - tmp.get_width() // 2),
                                    int(cy - s * 0.2 - tmp.get_height() + 4)))
        # gigi
        for k in range(-2, 3):
            pygame.draw.rect(surface, (*P["bone_high"], a),
                             (int(self.x + k * s * 0.28 - s * 0.08),
                              int(cy + s * 0.55), max(1, int(s * 0.16)),
                              max(1, int(s * 0.34))))
        # sinar kanal jiwa turun ke caster
        beam = _scratch(int(s * 2.2) + 8, int(self.y + 24 - cy) + 8)
        bw, bh = beam.get_size()
        taper_lane(beam, bw // 2, 4, bw // 2, bh - 4, s * 0.35, s * 0.9,
                   P["soul_mid"], int(72 * fade))
        taper_lane(beam, bw // 2, 4, bw // 2, bh - 4, s * 0.14, s * 0.34,
                   P["soul_glow"], int(120 * fade))
        blit_add(surface, beam, (int(self.x - bw // 2), int(cy)))

    def _frn_r(self, surface, t):
        """Pilar api vertikal mengorbit + kolom cahaya ultimate."""
        fade = 1.0 if t < 0.88 else max(0.0, 1.0 - (t - 0.88) / 0.12)
        if fade <= 0.02:
            return
        R = self.r_screen(1.0)
        gy = self.y + 22
        grow = _ease("out", min(1.0, t / 0.34))
        for i in range(ARMY_COUNT):
            a = i * math.tau / ARMY_COUNT + t * 1.4
            px = self.x + math.cos(a) * R * 0.62 * grow
            py = gy + math.sin(a) * R * 0.26 * grow
            hgt = (26 + 16 * math.sin(t * 8.0 + i)) * grow
            if hgt < 3:
                continue
            tmp = _scratch(int(hgt) + 14, int(hgt * 1.6) + 14)
            flame_poly(tmp, tmp.get_width() // 2, tmp.get_height() - 2,
                       hgt, seed=self.seed + i * 31,
                       alpha=int(215 * fade), phase=t * 16.0 + i,
                       w=hgt * 0.3)
            blit_add(surface, tmp, (int(px - tmp.get_width() // 2),
                                    int(py - tmp.get_height() + 3)))
        # kolom cahaya meruncing dari tanah ke atas (bukan kotak)
        if 0.2 <= t < 0.7:
            k = (t - 0.2) / 0.5
            hgt = 120 * _ease("out", min(1.0, k * 2.0))
            col = _scratch(90, int(hgt) + 10)
            cw, ch = col.get_size()
            taper_lane(col, cw // 2, ch - 4, cw // 2, 4, 26.0, 6.0,
                       P["fire_dark"], int(76 * fade * (1 - k * 0.6)))
            taper_lane(col, cw // 2, ch - 4, cw // 2, 4, 11.0, 2.5,
                       P["fire_glow"], int(120 * fade * (1 - k * 0.6)))
            blit_add(surface, col, (int(self.x - cw // 2), int(gy - ch + 4)))
        # cincin raungan
        if 0.3 <= t < 0.62:
            k = (t - 0.3) / 0.32
            rr = int(R * (0.3 + 0.75 * _ease("oc", k)))
            _blit_faded(surface,
                        ellipse_ring_surface(rr, max(2, int(rr * 0.4)),
                                             max(1, int(4 * (1 - k))),
                                             P["fire_hot"], 255),
                        self.x, gy, int(200 * (1 - k) * fade), additive=True)


# ============================================================================
# 12.  DIRECTOR — satu instance per unit
# ============================================================================

class ZharokFXDirector:
    """Mengikat trail, partikel, proyektil, skill, dampak, dan game feel
    untuk SATU Zharok (boss lane maupun hero lane)."""

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
        self.shot_done = False
        self.swing_count = 0
        self.shot_count = 0
        self.melee = False

        # pelacakan skill
        self.skill_key = None
        self.skill_prev = None
        self.skill_time = 0.0

        # lain-lain
        self.hurt_prev = 0
        self.ember_acc = 0.0
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
        st = getattr(boss, "_zh_state", None)
        if st is None:
            action, _phase, _ap = pose_of(boss)
            st = {"idle": "IDLE", "walk": "WALK", "run": "RUN",
                  "attack": "ATTACK", "melee": "SWING", "strafe": "SKILL",
                  "smoke": "SKILL", "e_cast": "SKILL", "r_cast": "SPECIAL",
                  "hurt": "HURT", "death": "DEATH"}.get(action, "IDLE")
        if st != self.state:
            self.state_prev = self.state
            self.state = st
            self.state_time = 0.0
            self.anim_frame = 0
        self.state_priority = ANIM_STATES.get(st, 0)

        # -- progres serangan -----------------------------------------
        self.attack_prev = self.attack_progress
        ap = float(getattr(boss, "_zh_attack_progress", 0.0) or 0.0)
        self.attack_progress = ap
        self.attack_phase = attack_phase(ap)
        lo, hi = ATTACK_ACTIVE_WINDOW
        self.attack_active = lo <= ap <= hi

        action, _phase, _ap = pose_of(boss)
        self.melee = bool(getattr(boss, "_zh_melee_swing", False)) \
            or action in ("melee", "swing", "cleave")
        swinging = action in ("attack", "melee", "swing", "cleave",
                              "strafe")

        # -- trail senjata: rekam posisi stave saat menyabet/menarik ---
        if swinging and 0.12 <= ap <= 0.94:
            _grip, hi_tip, lo_tip = bow_points(boss, x, y)
            self.trail.push(lo_tip, hi_tip,
                            heat=1.0 if self.attack_active else 0.5)
            if self.attack_active:
                self.trail.hot = 1.0
        elif not swinging:
            self.trail.hot = max(0.0, self.trail.hot - 0.1)

        # -- momen impact / pelepasan anak panah ----------------------
        if swinging:
            crossed = self.attack_prev < ATTACK_IMPACT_FRAME <= ap
            if crossed and not self.swing_done:
                self.swing_done = True
                if self.melee:
                    self.swing_count += 1
                    self._melee_impact(boss, x, y)
                elif not getattr(boss, "_zh_suppress_auto_shot", False):
                    self.shot_count += 1
                    self.spawn_projectile(boss, x, y)
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
        """Bara & abu sekitar: hidup tapi hemat (kuota per detik).

        Berhenti OTOMATIS kalau unit sudah 0.5 s tidak digambar (mati /
        keluar layar), jadi tidak ada efek berumur tak terbatas.
        """
        if not self.have_pos or self.draw_age > 0.5:
            return
        rate = 8.0
        if self.skill_key == "r":
            rate = 24.0
        elif self.skill_key == "e":
            rate = 15.0
        elif self.skill_key == "w":
            rate = 5.0
        elif self.state in ("WALK", "RUN"):
            rate = 13.0
        self.ember_acc += dt * rate
        while self.ember_acc >= 1.0:
            self.ember_acc -= 1.0
            if self.particles.count() > self.particles.cap * 0.8:
                break
            a = random.uniform(0, math.tau)
            r = random.uniform(6, 24)
            self.particles.spawn(
                self.x + math.cos(a) * r,
                self.y + 18 + math.sin(a) * r * 0.35,
                vx=random.uniform(-13, 13),
                vy=random.uniform(-68, -20),
                life=random.uniform(0.4, 1.0),
                size=random.uniform(1.1, 2.5),
                color=random.choice((P["ember"], P["fire_hot"],
                                     P["fire_bright"])),
                shape="ember", additive=True, drag=0.5,
                layer="back" if random.random() < 0.5 else "front")

        # afterimage saat stealth (W), ultimate (R), atau sabetan aktif
        if self.skill_key in ("w", "r") or self.attack_active:
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
        tint = P["smoke_light"] if self.skill_key == "w" else P["fire_dark"]
        self.afterimages.append(
            Afterimage(surf, self.x + off[0], self.y + off[1], 0.26, tint))

    def _melee_impact(self, boss, x, y):
        """Sabetan stave busur mendarat: flash + sabit + debu + game feel."""
        _grip, hi_tip, lo_tip = bow_points(boss, x, y)
        ang = math.atan2(hi_tip[1] - lo_tip[1], hi_tip[0] - lo_tip[0])
        px = hi_tip[0] - math.cos(ang) * 4.0
        py = hi_tip[1] - math.sin(ang) * 4.0
        self.last_impact_point = (px, py)
        self.add_impact(px, py, "melee", ang, 1.1, P["fire_bright"], 32.0)
        self.particles.burst(px, py, 13, speed=(120, 330),
                             life=(0.18, 0.44), size=(1.7, 4.2),
                             colors=(P["fire_bright"], P["fire_hot"],
                                     P["ember"]),
                             spread=1.5, direction=ang, gravity=310,
                             drag=1.1, shape="ember")
        self.particles.burst(px, py, 6, speed=(60, 180),
                             life=(0.25, 0.55), size=(1.6, 3.6),
                             colors=(P["bone_light"], P["bone_mid"],
                                     P["ash"]),
                             spread=2.0, direction=ang, gravity=520,
                             shape="bone", rotation_speed=(-10, 10),
                             additive=False)
        self.particles.burst(x, y + 26, 6, speed=(50, 150),
                             life=(0.3, 0.6), size=(2.6, 5.4),
                             colors=(P["dust"], P["ash"]), spread=1.0,
                             direction=0.0 if hi_tip[0] >= x else math.pi,
                             gravity=140, shape="smoke", additive=False)
        _feel_shake(6.5, 0.17)
        _feel_hit_stop(0.05)

    def start_skill(self, boss, key, x, y):
        """Mulai lifecycle FX untuk satu skill."""
        if key not in ("q", "w", "e", "r"):
            return None
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        fx = SkillFX(key, x, y, facing, getattr(boss, "target", None),
                     scale=body_scale(boss), director=self)
        tp = target_point(boss, x, y)
        fx.target_point = tp
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        self.skills.append(fx)
        return fx

    def spawn_projectile(self, boss, x, y, tx=None, ty=None):
        """Lepas anak panah hellfire dari busur (serangan dasar)."""
        nx, ny = nock_point(boss, x, y)
        if tx is None or ty is None:
            tx, ty = target_point(boss, x, y)
        pr = self.projectiles.spawn_arrow(
            nx, ny, tx, ty, speed=ARROW_SPEED, radius=10.0,
            target=getattr(boss, "target", None), owner=boss)
        ang = math.atan2(ty - ny, tx - nx)
        self.particles.burst(nx, ny, 9, speed=(70, 210), life=(0.12, 0.32),
                             size=(1.4, 3.2),
                             colors=(P["fire_glow"], P["fire_hot"],
                                     P["fire_bright"]),
                             spread=1.3, direction=ang, drag=1.5,
                             shape="streak")
        self.add_impact(nx, ny, "skill", ang, 0.45, P["fire_hot"], 16.0)
        _feel_shake(2.2, 0.09)
        return pr

    def spawn_hurt(self, boss, x, y):
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        self.particles.burst(x - facing * 7, y - 14, 10, speed=(90, 230),
                             life=(0.2, 0.45), size=(1.5, 3.4),
                             colors=(P["bone_light"], P["fire_bright"],
                                     P["ember"]),
                             spread=2.2,
                             direction=math.pi if facing > 0 else 0.0,
                             gravity=320, drag=1.0, shape="spark")
        self.add_impact(x - facing * 9, y - 14, "skill",
                        math.pi if facing > 0 else 0.0, 0.5,
                        P["bone_high"], 24.0)

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
        """Di BAWAH badan: telegraph skill, retakan, afterimage, partikel
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
            "shots": self.shot_count,
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
# 13.  REGISTRI DIRECTOR
#      Pola SAMA dengan heroes/ignis_drachorn_fx.py: director menempel di
#      unit (``_zharok_fx``), daftar global dipakai tick() + reset_all().
# ============================================================================

_DIRECTORS = []
MAX_DIRECTORS = 12


def director_for(unit):
    """Ambil (atau buat) director FX untuk satu unit Zharok."""
    _sync_palette()
    d = getattr(unit, "_zharok_fx", None)
    if d is None:
        d = ZharokFXDirector(unit)
        try:
            unit._zharok_fx = d
        except Exception:                        # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > MAX_DIRECTORS:
            _release(_DIRECTORS.pop(0))
    return d


def _release(director):
    try:
        if director.unit is not None:
            director.unit._zharok_fx = None
            director.unit._zh_live_fx = False
    except Exception:                            # pragma: no cover
        pass
    director.reset()


def attach(unit):
    """Pasang lapisan hidup pada unit (dipanggil pipeline render)."""
    if not ZHAROK_FX_ENABLED or unit is None:
        return False
    try:
        director_for(unit)
    except Exception:                            # pragma: no cover
        return False
    try:
        unit._zh_live_fx = True
    except Exception:                            # pragma: no cover
        return False
    return True


def owns(unit):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not ZHAROK_FX_ENABLED or unit is None:
        return False
    if not getattr(unit, "_zh_live_fx", False):
        return False
    d = getattr(unit, "_zharok_fx", None)
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
    d = getattr(unit, "_zharok_fx", None)
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
    if not ZHAROK_FX_ENABLED:
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
    """Bersihkan seluruh state FX Zharok (ganti level / keluar match)."""
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
    """Jumlah partikel Zharok yang hidup (HUD performa + tes)."""
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
    d = getattr(unit, "_zharok_fx", None)
    if d is None:
        return []
    return d.projectiles.projectiles


# ============================================================================
# 14.  API GAMBAR — dipanggil renderer bosses/level4.py
#      Urutan kanonik: GROUND -> (badan digambar renderer) -> LIVE.
# ============================================================================

def draw_ground_layer(surface, unit, x, y):
    """Lapisan BAWAH badan: telegraph skill, retakan, genangan,
    afterimage, partikel belakang.  Juga memajukan simulasi satu frame."""
    if not ZHAROK_FX_ENABLED or unit is None:
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
    if not ZHAROK_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if not d.have_pos or d.x != x or d.y != y:
        d.sync(unit, x, y)
    d.draw_front(surface)
    if DEBUG_CHARACTER:
        draw_debug_overlay(surface, d)


# ============================================================================
# 15.  NOTIFIKASI — dipanggil AI (bosses/base_boss.py) & renderer
# ============================================================================

def notify_melee_impact(unit, target=None, damage=0, crit=False,
                        x=None, y=None, angle=None):
    """Stave busur mendarat pada target (jarak sangat dekat)."""
    if not ZHAROK_FX_ENABLED or unit is None:
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
    d.add_impact(x, y, "melee", angle, power, P["fire_bright"], 32.0)
    d.particles.burst(x, y, 13, speed=(120, 330), life=(0.18, 0.44),
                      size=(1.7, 4.2),
                      colors=(P["fire_bright"], P["fire_hot"], P["ember"]),
                      spread=1.5, direction=angle, gravity=310, drag=1.1,
                      shape="ember")
    d.particles.burst(x, y, 6, speed=(60, 180), life=(0.25, 0.55),
                      size=(1.6, 3.6),
                      colors=(P["bone_light"], P["ash"], P["dust"]),
                      spread=2.0, direction=angle, gravity=520,
                      shape="bone", rotation_speed=(-10, 10),
                      additive=False)
    _feel_shake(6.5 * power, 0.17)
    _feel_hit_stop(0.05 if not crit else 0.07)


def notify_projectile_impact(unit, x, y, angle=0.0, damage=0, crit=False,
                             kind="arrow"):
    """Anak panah / tengkorak jiwa mengenai target: paket impact lengkap."""
    if not ZHAROK_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    try:
        power = 0.7 + min(1.6, float(damage) / 60.0)
    except (TypeError, ValueError):
        power = 1.0
    if crit:
        power *= 1.3
    is_skull = (kind == "skull")
    d.add_impact(x, y, "skull" if is_skull else "arrow", angle, power,
                 P["soul_hot"] if is_skull else P["fire_bright"],
                 52.0 if is_skull else 34.0)
    d.particles.burst(x, y, 12, speed=(80, 250), life=(0.2, 0.5),
                      size=(1.6, 4.0),
                      colors=(P["fire_bright"], P["fire_hot"], P["ember"]),
                      spread=2.4, direction=angle + math.pi, gravity=250,
                      drag=1.0, shape="ember")
    d.particles.burst(x, y, 4, speed=(20, 70), life=(0.35, 0.75),
                      size=(2.5, 5), colors=(P["ash"], P["dust"]),
                      gravity=-50, shape="smoke", additive=False)
    _feel_shake((6.0 if is_skull else 3.6) * power, 0.14)
    _feel_hit_stop(0.045 if is_skull else 0.032)


def notify_skill_cast(unit, skill, x=None, y=None):
    """Skill mulai di-cast: buat lifecycle FX + guncangan awal."""
    if not ZHAROK_FX_ENABLED or unit is None:
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
    if not ZHAROK_FX_ENABLED or unit is None:
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
    power = 1.4 if key != "r" else 2.1
    color = P["smoke_glow"] if key == "w" else P["fire_bright"]
    rr = float(radius) if radius else {"q": 70.0, "w": 90.0, "e": 60.0,
                                       "r": 150.0}.get(key, 70.0)
    d.add_impact(x, y, "skill", 0.0, power, color, rr)
    d.particles.burst(x, y, 12 if key != "r" else 20, speed=(90, 300),
                      life=(0.25, 0.6), size=(2, 5),
                      colors=(P["fire_bright"], P["fire_hot"], P["ember"]),
                      gravity=300, drag=0.8, shape="ember")
    _feel_shake({"q": 6.0, "w": 5.0, "e": 11.0,
                 "r": 14.0}.get(key, 6.0), 0.22)
    _feel_hit_stop({"q": 0.035, "w": 0.03, "e": 0.05,
                    "r": 0.07}.get(key, 0.04))


def notify_projectile_cast(unit, x, y, tx=None, ty=None):
    """Lepas anak panah hellfire dari busur (serangan jarak jauh).

    Renderer memanggil ini saat frame cast aktif dan lapisan hidup sudah
    mengambil alih proyektil; menggantikan ``_spawn_fire_arrow`` versi
    canvas.
    """
    if not ZHAROK_FX_ENABLED or unit is None:
        return None
    d = director_for(unit)
    d.sync(unit, x, y)
    return d.spawn_projectile(unit, x, y, tx, ty)


def notify_hurt(unit, amount=1.0, x=None, y=None):
    """Unit terkena damage: percikan bara-tulang + kilat kecil."""
    if not ZHAROK_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if x is None or y is None:
        if not d.have_pos:
            return
        x, y = d.x, d.y
    d.spawn_hurt(unit, x, y)


def notify_death(unit, x=None, y=None):
    """Kematian: tulang berhamburan + bara + asap + guncangan berat."""
    if not ZHAROK_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if x is None or y is None:
        if not d.have_pos:
            return
        x, y = d.x, d.y
    d.add_impact(x, y, "skull", 0.0, 1.6, P["soul_hot"], 110.0)
    d.particles.burst(x, y, 28, speed=(120, 420), life=(0.4, 1.0),
                      size=(2, 6),
                      colors=(P["fire_hot"], P["fire_bright"], P["ember"],
                              P["ash"]),
                      spread=math.tau, gravity=340, drag=0.7, shape="ember")
    d.particles.burst(x, y, 12, speed=(70, 260), life=(0.5, 1.1),
                      size=(1.8, 4.0),
                      colors=(P["bone_light"], P["bone_mid"],
                              P["bone_high"]),
                      spread=math.tau, gravity=620, shape="bone",
                      rotation_speed=(-12, 12), additive=False)
    d.particles.burst(x, y, 8, speed=(30, 120), life=(0.6, 1.2),
                      size=(4, 8), colors=(P["ash"], P["smoke_mid"]),
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
# 16.  OVERLAY DEBUG  (DEBUG_CHARACTER = True)
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
    """Hitbox, hurtbox, attack range, tabrakan proyektil, state animasi,
    frame, FPS, jumlah partikel, state skill, timer serangan."""
    d = director
    if d is None or not d.have_pos:
        return
    unit = d.unit
    x, y = d.x, d.y
    k = body_scale(unit) if unit is not None else 1.0

    # -- jangkauan serangan (elips tanah) -----------------------------
    rng = float(getattr(unit, "attack_range",
                        getattr(unit, "range", 180)) or 180)
    rng = rng / max(0.05, k)
    _blit_faded(surface, ellipse_ring_surface(int(rng), int(rng * 0.4), 1,
                                              (90, 200, 255), 255),
                x, y + 22, 130)

    # -- radius skill aktif -------------------------------------------
    if d.skill_key:
        rr = WORLD_RADIUS.get(d.skill_key, 150.0) / max(0.05, k)
        _blit_faded(surface, ellipse_ring_surface(int(rr), int(rr * 0.4), 1,
                                                  (255, 120, 120), 255),
                    x, y + 22, 120)

    # -- hurtbox (badan) ------------------------------------------------
    hw = int(26 * k)
    hh = int(66 * k)
    pygame.draw.rect(surface, (70, 240, 120),
                     pygame.Rect(int(x - hw), int(y - hh + 10), hw * 2,
                                 hh + 18), 1)

    # -- hitbox senjata pada jendela aktif ------------------------------
    lo, hi = ATTACK_ACTIVE_WINDOW
    active = lo <= d.attack_progress <= hi
    col = (255, 80, 80) if active else (150, 150, 160)
    if unit is not None:
        grip, tip_hi, tip_lo = bow_points(unit, x, y)
        pygame.draw.line(surface, col, (int(tip_lo[0]), int(tip_lo[1])),
                         (int(tip_hi[0]), int(tip_hi[1])),
                         2 if active else 1)
        pygame.draw.circle(surface, col, (int(tip_hi[0]), int(tip_hi[1])),
                           max(2, int(13 * k)), 1)
        pygame.draw.circle(surface, (240, 240, 90),
                           (int(grip[0]), int(grip[1])), 2, 1)
        nx, ny = nock_point(unit, x, y)
        pygame.draw.circle(surface, (255, 200, 60), (int(nx), int(ny)), 3, 1)

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
        "ZHAROK [debug]",
        "state %s <- %s (p%d)" % (st["state"], d.state_prev,
                                  d.state_priority),
        "frame %d  t %.2fs  dt %.4f" % (st["frame"], d.state_time, d.dt),
        "attack %.2f %s%s%s" % (st["attack_progress"], st["attack_phase"],
                                "  <HIT>" if active else "",
                                "  MELEE" if d.melee else "  BOW"),
        "atk timer %s  cd %s" % (getattr(unit, "timer", "-"),
                                 getattr(unit, "attack_cooldown", "-")),
        "skill %s/%s t%.2f  boss_timer %s" % (
            d.skill_key or "-", sk.phase if sk else "-", d.skill_time,
            getattr(unit, "active_skill_timer", "-")),
        "part %d/%d  proj %d  fx %d" % (st["particles"], d.particles.cap,
                                        st["projectiles"], st["impacts"]),
        "fps %.0f  cache %d  swing %d shot %d" % (fps, cache_size(),
                                                  st["swings"],
                                                  st["shots"]),
    ]
    pad = 4
    w = max(font.size(t)[0] for t in lines) + pad * 2
    h = len(lines) * 13 + pad * 2
    box = pygame.Surface((w, h), pygame.SRCALPHA)
    box.fill((10, 8, 12, 190))
    pygame.draw.rect(box, (255, 140, 60, 200), box.get_rect(), 1)
    for i, t in enumerate(lines):
        box.blit(font.render(t, True, (255, 224, 190)), (pad, pad + i * 13))
    surface.blit(box, (int(x) + 46, int(y) - 100))


# ============================================================================
# 17.  API PUBLIK
# ============================================================================

__all__ = [
    "DEBUG_CHARACTER", "ZHAROK_FX_ENABLED", "ZHAROK_PALETTE",
    "MAX_PARTICLES", "MAX_PROJECTILES", "TRAIL_SAMPLES", "MAX_IMPACTS",
    "MAX_SKILLS", "MAX_AFTERIMAGES",
    "ATTACK_PHASES", "ATTACK_ACTIVE_WINDOW", "ATTACK_IMPACT_FRAME",
    "ANIM_STATES", "SKILL_PHASES", "SKILL_DUR", "SKILL_TOTAL",
    "WORLD_RADIUS", "ARROW_SPEED", "VOLLEY_SPEED", "SKULL_SPEED",
    "ARMY_COUNT", "VOLLEY_COUNT", "MELEE_REACH",
    "Particle", "ParticleSystem", "SwingTrail", "ImpactFX", "Afterimage",
    "BaseProjectile", "FireArrowProjectile", "SoulSkullProjectile",
    "ProjectileSystem", "SkillFX", "ZharokFXDirector",
    "attach", "owns", "recently_drawn", "director_for", "projectiles_for",
    "tick", "reset_all", "total_particles", "stats",
    "draw_ground_layer", "draw_live_layer", "draw_debug_overlay",
    "notify_melee_impact", "notify_projectile_cast",
    "notify_projectile_impact", "notify_skill_cast",
    "notify_skill_impact", "notify_hurt", "notify_death",
    "bow_arc", "bow_points", "bow_angle", "nock_point", "attack_phase",
    "skill_phase", "pose_of", "render_scale", "body_scale", "screen_point",
    "target_point", "ring_radius", "particle_budget", "glow_allowed",
    "shake_allowed",
    "glow_surface", "ring_surface", "ellipse_ring_surface",
    "ground_pool_surface", "ember_surface", "arc_ring_surface",
    "shard_poly", "flame_poly", "spark_star", "chevron", "crack_points",
    "star_poly_points", "taper_lane", "blit_add",
    "clear_cache", "cache_size",
]
