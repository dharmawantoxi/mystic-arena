# ============================================================================
# heroes/ignis_drachorn_fx.py
# ----------------------------------------------------------------------------
# IGNIS DRACHORN — THE MOLTEN SOVEREIGN  (screen-space live combat layer)
#
# Badan Ignis Drachorn digambar oleh ``_NS_ignis_drachorn``
# (bosses/level4.py) ke canvas yang di-CACHE lalu diberi outline siluet +
# pencahayaan. Seperti Gornak / Varkul / Xerathis, semua yang butuh gerak
# 60 fps sejati — sabetan greatsword, bara, proyektil bola api, meteor
# ultimate, impact, guncangan layar, hit-stop — TIDAK boleh hidup di
# dalam canvas itu (canvas dikuantisasi & di-smoothscale, jadi efeknya
# akan beku dan menyusut). Modul ini adalah lapisan hidup: digambar
# langsung ke layar pada skala 1:1 tiap frame dengan delta-time nyata
# (via heroes/combat_feel).
#
# Pembagian kerja (sengaja, supaya tidak ada efek digambar dua kali):
#
#   RENDERER (canvas, ter-cache)        MODUL INI (layar, hidup)
#   ---------------------------------   ------------------------------------
#   rig dragon knight + outline + rim   trail sabetan dari histori ujung bilah
#   bayangan, aura panas, bara tanah    particle system (ember/asap/debris)
#   pose idle/walk/run/attack/cast      proyektil Fire Orb + Meteor modular
#   ARK greatsword (SWORD_ARC)          IMPACT FX + flash + shockwave
#   hurt-flash (siluet badan)           SkillFX q/w/e/r lifecycle penuh
#   telegraph & fallback skill canvas   hit-stop 0.03-0.08 s + screen shake
#   elder dragon form (R)               overlay DEBUG_CHARACTER
#
# 100% PROSEDURAL. Tidak ada PNG / JPG / GIF / sprite-sheet / image.load.
# Semua bentuk dibuat dengan pygame.draw + pygame.Surface +
# pygame.transform + pygame.Vector2.
#
# Isi modul
#   IGNIS_PALETTE          palette karakter (kontrak 9 kunci + ramp api)
#   Particle               partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem         pool + burst + cap keras, reusable
#   SwingTrail             pita sabetan prosedural dari histori ujung bilah
#   ImpactFX               flash + shockwave + debris + fragmen sabit
#   FireOrbProjectile      proyektil modular (spawn->travel->hit->destroy)
#   MeteorProjectile       meteor jatuh (ultimate R) + kawah
#   ProjectileSystem       manajer proyektil
#   SkillFX                lifecycle FX skill (cast->charge->release->fade)
#   IgnisFXDirector        satu instance per unit, mengikat semua di atas
#   draw_debug_overlay     hitbox/hurtbox/range/state/frame/FPS/partikel
#   API modul              tick / reset_all / notify_* / draw_*_layer
# ============================================================================

import math
import random

import pygame

try:                                  # bus game-feel bersama (combat_feel)
    from heroes import combat_feel as _feel
except Exception:                     # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual karakter IGNIS DRACHORN: hitbox, hurtbox, jangkauan
#: serangan, tabrakan proyektil, state animasi, frame, FPS, jumlah
#: partikel, state skill, dan timer serangan.
DEBUG_CHARACTER = False

#: Master switch — kalau False modul jadi no-op murah (badan tetap jalan
#: lewat fallback canvas di renderer).
IGNIS_FX_ENABLED = True

#: Batas keras partikel hidup per director (anti kebocoran FPS).
MAX_PARTICLES = 210

#: Batas keras proyektil visual per director.
MAX_PROJECTILES = 20

#: Panjang histori trail senjata (sample posisi ujung greatsword).
TRAIL_SAMPLES = 9

#: Batas dampak & skill aktif bersamaan per director.
MAX_IMPACTS = 9
MAX_SKILLS = 5

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Kecepatan bola api dasar (px/detik, ruang dunia).
ORB_SPEED = 620.0

#: Kecepatan meteor ultimate (px/detik).
METEOR_SPEED = 780.0

#: Durasi pose skill (frame sim) — SINKRON dengan base_boss
#: (_cast_q/w/e/r_*) dan ``_NS_ignis_drachorn.SKILL_DUR``.
SKILL_DUR = {"q": 45, "w": 40, "e": 60, "r": 90}

#: Umur FX skill dalam DETIK (durasi pose + after-glow).
SKILL_TOTAL = {"q": 1.15, "w": 1.05, "e": 1.45, "r": 2.40}

#: Radius efek di ruang DUNIA (px) — sama dengan radius damage AI.
WORLD_RADIUS = {"q": 250.0, "w": 130.0, "e": 110.0, "r": 220.0}

#: Jumlah meteor yang dijatuhkan ultimate R.
METEOR_COUNT = 5

#: Fase serangan (fraksi 0..1 durasi serangan).
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.12),
    ("WINDUP",       0.12, 0.30),
    ("SWING",        0.30, 0.50),
    ("IMPACT",       0.50, 0.62),
    ("FOLLOW",       0.62, 0.82),
    ("RECOVERY",     0.82, 1.00),
)

#: Jendela hit aktif + frame impact (dibaca debug & game feel).
ATTACK_ACTIVE_WINDOW = (0.36, 0.62)
ATTACK_IMPACT_FRAME = 0.52

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
# 1.  PALETTE — molten sovereign: obsidian + magma + crimson + emas
# ============================================================================

IGNIS_PALETTE = {
    # ── kontrak palette karakter (9 kunci wajib) ────────────────────
    "outline":    (6,     3,   6),
    "shadow":     (10,    6,   8),
    "dark":       (28,   16,  20),
    "body":       (58,   36,  40),
    "mid":        (96,   62,  62),
    "light":      (150, 108, 100),
    "highlight":  (226, 200, 188),
    "weapon":     (255, 150,  46),
    "fx":         (255, 196,  78),

    # ── api (ramp 7 band) ───────────────────────────────────────────
    "fire_darkest": (60,  12,   4),
    "fire_dark":    (135, 35,   8),
    "fire_mid":     (215, 80,  15),
    "fire_light":   (250, 145, 30),
    "fire_bright":  (255, 200, 65),
    "fire_hot":     (255, 235, 140),
    "fire_white":   (255, 250, 220),

    # ── magma / seam ────────────────────────────────────────────────
    "magma_dark":   (96,  16,   6),
    "magma_mid":    (192, 56,  12),
    "magma_hot":    (255, 128, 28),
    "magma_bright": (255, 190, 76),

    # ── obsidian plate ──────────────────────────────────────────────
    "plate_dark":   (18,  12,  16),
    "plate_mid":    (48,  34,  42),
    "plate_light":  (96,  72,  80),

    # ── kain & sisik ────────────────────────────────────────────────
    "cloth":        (140, 30,  35),
    "cloth_light":  (200, 70,  62),
    "scale":        (105, 30,  32),
    "scale_light":  (170, 62,  54),

    # ── emas ────────────────────────────────────────────────────────
    "gold":         (170, 125, 35),
    "gold_hot":     (255, 235, 150),

    # ── asap, abu, debu ─────────────────────────────────────────────
    "smoke":        (54,  44,  48),
    "smoke_light":  (108, 92,  92),
    "ash":          (86,  70,  66),
    "dust":         (120, 96,  78),
    "ember":        (255, 120, 32),
}

P = dict(IGNIS_PALETTE)

#: Kunci renderer -> kunci palette modul ini (disinkronkan sekali supaya
#: warna efek tidak pernah melenceng dari material karakter).
_PALETTE_SYNC = {
    "fire_darkest": "fire_darkest",
    "fire_dark": "fire_dark",
    "fire_mid": "fire_mid",
    "fire_light": "fire_light",
    "fire_bright": "fire_bright",
    "fire_hot": "fire_hot",
    "fire_white": "fire_white",
    "magma_dark": "magma_dark",
    "magma_mid": "magma_mid",
    "magma_hot": "magma_hot",
    "magma_bright": "magma_bright",
    "plate_dark": "obsidian_darkest",
    "plate_mid": "obsidian_mid",
    "plate_light": "obsidian_light",
    "cloth": "red_mid",
    "cloth_light": "red_high",
    "scale": "dragon_mid",
    "scale_light": "dragon_high",
    "gold": "gold_mid",
    "gold_hot": "gold_shine",
    "smoke": "smoke_mid",
    "smoke_light": "smoke_light",
    "weapon": "blade_mid",
    "fx": "fire_bright",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Salin warna tema dari ``_NS_ignis_drachorn.PALETTE`` sekali saja.

    Renderer adalah satu-satunya sumber kebenaran untuk material
    karakter; lapisan efek tidak boleh punya salinan yang lalu berbeda.
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


#: Tabel ark cadangan — IDENTIK dengan ``_NS_ignis_drachorn.SWORD_ARC``
#: supaya modul tetap hidup kalau renderer gagal diimpor.
_ARC_FALLBACK = (
    (0.00, 0.12,  2.42,  2.00, "out"),
    (0.12, 0.30,  2.00, -1.30, "io"),
    (0.30, 0.50, -1.30,  1.80, "oc"),
    (0.50, 0.62,  1.80,  2.12, "hold"),
    (0.62, 0.82,  2.12,  2.72, "io"),
    (0.82, 1.00,  2.72,  2.42, "io"),
)

_BLADE_LEN_FALLBACK = 56.0
_GRIP_FALLBACK = (16.0, -6.0)


def _ease(kind, t):
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    if kind == "out":
        return 1.0 - (1.0 - t) * (1.0 - t)
    if kind == "oc":
        return 1.0 - (1.0 - t) ** 3
    if kind == "in":
        return t * t
    if kind == "hold":
        return math.sin(t * math.pi * 0.5)
    return t * t * (3.0 - 2.0 * t)


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


def sword_arc(progress):
    """(theta, lift) ark greatsword — SATU sumber kebenaran.

    Membaca ``_NS_ignis_drachorn._sword_arc`` (yang juga dipakai canvas);
    kalau renderer tidak ada, pakai tabel fallback identik di atas.
    """
    R = _renderer()
    fn = getattr(R, "_sword_arc", None) if R is not None else None
    if fn is not None:
        try:
            return fn(progress)
        except Exception:                      # pragma: no cover
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
    if action is None:
        action = {"q": "cast", "w": "cast", "e": "cast",
                  "r": "cast"}.get(skill)
    if action is None:
        action = ("melee" if getattr(boss, "_ign_attack_active", False)
                  else "idle")
    phase = float(getattr(boss, "pulse", 0.0) or 0.0)
    ap = float(getattr(boss, "_ign_attack_progress", 0.0) or 0.0)
    return action, phase, ap


def pose_of(boss):
    """Pose badan yang dipakai renderer (action, phase, attack_progress)."""
    action = getattr(boss, "_ign_pose_action", None)
    if action is None:
        return _fallback_pose(boss)
    phase = float(getattr(boss, "_ign_phase", getattr(boss, "pulse", 0.0)))
    ap = float(getattr(boss, "_ign_attack_progress", 0.0) or 0.0)
    return action, phase, ap


def render_scale(boss):
    """Skala hero-lane (canvas dikali saat blit). Boss di layar = 1."""
    try:
        s = float(getattr(boss, "_render_scale", 1.0) or 1.0)
    except (TypeError, ValueError):
        s = 1.0
    return s if s > 0.01 else 1.0


def body_scale(boss):
    """Skala badan relatif terhadap jangkar (dipakai titik FX)."""
    return render_scale(boss)


def screen_point(boss, x, y, local):
    """Titik layar dari koordinat lokal (offset dari jangkar badan)."""
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)
    return (x + local[0] * k * (1 if facing >= 0 else 1),
            y + local[1] * k)


def sword_points(boss, x, y):
    """(grip, tip) greatsword di ruang LAYAR untuk trail & proyektil.

    Memakai ``_NS_ignis_drachorn.sword_geometry`` — fungsi yang sama yang
    dipakai canvas untuk menggambar bilah, jadi trail tidak mungkin
    berbeda satu frame pun dari pedangnya.
    """
    action, phase, ap = pose_of(boss)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    k = body_scale(boss)
    R = _renderer()
    fn = getattr(R, "sword_geometry", None) if R is not None else None
    if fn is not None:
        try:
            grip, tip, _theta = fn(facing, action, phase, ap)
            return ((x + grip[0] * k, y + grip[1] * k),
                    (x + tip[0] * k, y + tip[1] * k))
        except Exception:                      # pragma: no cover
            pass
    # fallback: hitung sendiri dengan tabel identik
    theta, lift = sword_arc(ap) if action in ("melee", "swing", "attack") \
        else (2.42, 0.0)
    gx = facing * (_GRIP_FALLBACK[0] + 7.0 * lift)
    gy = _GRIP_FALLBACK[1] - 15.0 * lift
    tx = gx + facing * math.sin(theta) * _BLADE_LEN_FALLBACK
    ty = gy - math.cos(theta) * _BLADE_LEN_FALLBACK
    return ((x + gx * k, y + gy * k), (x + tx * k, y + ty * k))


def sword_angle(boss, x, y):
    """Sudut bilah (radian) di ruang layar, dari grip ke ujung."""
    grip, tip = sword_points(boss, x, y)
    return math.atan2(tip[1] - grip[1], tip[0] - grip[0])


def target_point(boss, x, y):
    """Titik target serangan dasar (ruang layar) untuk proyektil."""
    tgt = getattr(boss, "target", None)
    if tgt is not None and getattr(tgt, "alive", False):
        return (float(getattr(tgt, "x", x + 140.0)),
                float(getattr(tgt, "y", y)) - 6.0)
    facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
    return (x + facing * 160.0, y - 10.0)


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
_SCRATCH_POOL = []


def _clamp_color(color):
    return tuple(int(max(0, min(255, c))) for c in color)


def _mix(a, b, t):
    t = max(0.0, min(1.0, t))
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
        if len(_CACHE) > 220:                  # cap: hindari kebocoran
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
            s.fill((0, 0, 0, 0))
            return s.subsurface((0, 0, w, h))
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    if len(_SCRATCH_POOL) < 8:
        _SCRATCH_POOL.append(s)
    return s


_OPAQUE_POOL = []


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

    ``BLEND_RGB_ADD`` mengabaikan kanal alpha sepenuhnya, jadi surface
    ber-gradien kalau langsung di-ADD akan muncul sebagai bidang warna
    penuh (cakram/pelat keras). Di sini sumber di-"premultiply" dulu:
    di-blit normal ke atas hitam sehingga RGB ikut dikalikan alpha-nya,
    baru hasilnya ditambahkan. Itu yang bikin cahaya benar-benar
    meluruh ke gelap, bukan menempel sebagai stiker.
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
    cx, cy = int(cx), int(cy)
    rect = surf.get_rect(center=(cx, cy))
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


def glow_surface(radius, color, power=1.0):
    """Cahaya radial lembut ter-cache."""
    radius = max(3, int(radius))
    key = ("glow", radius, tuple(color[:3]), round(power, 2))
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
    c = radius + 1
    peak = int(max(0, min(255, 168 * power)))
    step = max(1, radius // 14)
    r = radius
    while r > step:
        t = r / float(radius)
        a = int(peak * (1.0 - t) ** 1.9)
        if a > 0:
            # ANNULUS, bukan lingkaran penuh: alpha tidak menumpuk jadi
            # cakram keras -> jatuh cahaya benar-benar mulus.
            pygame.draw.circle(surf, (*color[:3], a), (c, c), r, step + 1)
        r -= step
    pygame.draw.circle(surf, (*color[:3], peak), (c, c), max(1, step + 1))
    return _cache_put(key, surf)


def ring_surface(radius, thickness, color, alpha=255, dashed=0):
    """Cincin (opsional putus-putus) ter-cache."""
    radius = max(2, int(radius))
    thickness = max(1, int(thickness))
    key = ("ring", radius, thickness, tuple(color[:3]), int(alpha),
           int(dashed))
    if key in _CACHE:
        return _CACHE[key]
    size = radius * 2 + thickness * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    if dashed <= 0:
        pygame.draw.circle(surf, (*color[:3], int(alpha)), (c, c), radius,
                           thickness)
    else:
        for i in range(dashed):
            a0 = i * math.tau / dashed
            a1 = a0 + math.tau / dashed * 0.55
            pts = []
            steps = 5
            for k in range(steps + 1):
                a = a0 + (a1 - a0) * k / steps
                pts.append((c + math.cos(a) * radius,
                            c + math.sin(a) * radius))
            if len(pts) > 1:
                pygame.draw.lines(surf, (*color[:3], int(alpha)), False, pts,
                                  thickness)
    return _cache_put(key, surf)


def ellipse_ring_surface(rx, ry, thickness, color, alpha=255):
    """Cincin tanah pipih (perspektif) ter-cache."""
    rx = max(3, int(rx))
    ry = max(2, int(ry))
    thickness = max(1, int(thickness))
    key = ("ering", rx, ry, thickness, tuple(color[:3]), int(alpha))
    if key in _CACHE:
        return _CACHE[key]
    surf = pygame.Surface((rx * 2 + 6, ry * 2 + 6), pygame.SRCALPHA)
    for i in range(thickness, 0, -1):
        a = int(alpha * (i / float(thickness)) ** 0.7)
        pygame.draw.ellipse(surf, (*color[:3], a),
                            (3 + (thickness - i), 3 + (thickness - i),
                             (rx - (thickness - i)) * 2,
                             (ry - (thickness - i)) * 2), 1)
    return _cache_put(key, surf)


def ground_pool_surface(rx, color, power=0.35):
    """Genangan cahaya pipih di tanah (elips) ter-cache."""
    rx = max(4, int(rx))
    key = ("pool", rx, tuple(color[:3]), round(power, 2))
    if key in _CACHE:
        return _CACHE[key]
    ry = max(2, int(rx * 0.4))
    surf = pygame.Surface((rx * 2 + 4, ry * 2 + 4), pygame.SRCALPHA)
    peak = int(max(0, min(255, 190 * power)))
    step = max(1, rx // 12)
    r = rx
    while r > step:
        t = r / float(rx)
        a = int(peak * (1.0 - t) ** 1.5)
        if a > 0:
            rh = max(1, int(ry * t))
            pygame.draw.ellipse(surf, (*color[:3], a),
                                (2 + rx - r, 2 + ry - rh, r * 2, rh * 2),
                                step + 1)
        r -= step
    pygame.draw.ellipse(surf, (*color[:3], peak),
                        (2 + rx - step, 2 + ry - max(1, int(ry * 0.16)),
                         step * 2, max(2, int(ry * 0.32))))
    return _cache_put(key, surf)


def ember_surface(size, color):
    """Bara kecil (belah ketupat) ter-cache — bukan lingkaran."""
    size = max(2, int(size))
    key = ("ember", size, tuple(color[:3]))
    if key in _CACHE:
        return _CACHE[key]
    s = size * 2 + 2
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    c = s // 2
    pygame.draw.polygon(surf, (*color[:3], 235),
                        [(c, c - size), (c + size, c), (c, c + size),
                         (c - size, c)])
    pygame.draw.polygon(surf, (*P["fire_hot"], 255),
                        [(c, c - size // 2), (c + size // 2, c),
                         (c, c + size // 2), (c - size // 2, c)])
    return _cache_put(key, surf)


def shard_poly(surface, cx, cy, ang, length, width, color, alpha=255):
    """Serpihan runcing terarah (debris batuan/logam)."""
    ca, sa = math.cos(ang), math.sin(ang)
    tip = (cx + ca * length, cy + sa * length)
    tail = (cx - ca * length * 0.6, cy - sa * length * 0.6)
    perp = (-sa * width, ca * width)
    pygame.draw.polygon(surface, (*color[:3], int(alpha)),
                        [tip, (cx + perp[0], cy + perp[1]), tail,
                         (cx - perp[0], cy - perp[1])])


def flame_poly(surface, cx, cy, h, seed=0, alpha=255, phase=0.0, w=None):
    """Lidah api bergerigi (poligon) — bahasa bentuk utama karakter ini."""
    h = max(3.0, float(h))
    w = float(w if w is not None else h * 0.5)
    wob = math.sin(phase * 3.4 + seed) * (w * 0.35)
    wob2 = math.sin(phase * 5.1 + seed * 1.7) * (w * 0.2)
    pts = [
        (cx - w, cy),
        (cx - w * 0.55, cy - h * 0.32),
        (cx - w * 0.75 + wob2, cy - h * 0.6),
        (cx + wob, cy - h),
        (cx + w * 0.72 + wob2, cy - h * 0.58),
        (cx + w * 0.5, cy - h * 0.3),
        (cx + w, cy),
    ]
    a = int(alpha)
    pygame.draw.polygon(surface, (*P["fire_dark"], a), pts)
    pygame.draw.polygon(surface, (*P["fire_mid"], a),
                        [(cx + (px - cx) * 0.62, cy + (py - cy) * 0.72)
                         for px, py in pts])
    pygame.draw.polygon(surface, (*P["fire_bright"], a),
                        [(cx + (px - cx) * 0.34, cy + (py - cy) * 0.5)
                         for px, py in pts])


def _crack_points(x0, y0, x1, y1, segments=5, dev=6.0, seed=0):
    """Titik retakan bergerigi deterministik."""
    dx, dy = x1 - x0, y1 - y0
    dist = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / dist, dx / dist
    pts = [(x0, y0)]
    for k in range(1, segments):
        t = k / float(segments)
        h = _hash01(seed + k * 17) * 2.0 - 1.0
        d = h * dev * math.sin(t * math.pi)
        pts.append((x0 + dx * t + nx * d, y0 + dy * t + ny * d))
    pts.append((x1, y1))
    return pts


def spark_star(surface, cx, cy, size, color, alpha, spikes=8, rot=0.3,
               core=None):
    """Bintang percikan (flash impact) — bukan lingkaran."""
    alpha = int(max(0, min(255, alpha)))
    if alpha <= 0 or size <= 0:
        return
    for k in range(spikes):
        ang = rot + k * math.tau / spikes
        ln = size * (1.0 if k % 2 == 0 else 0.5)
        pygame.draw.line(surface, (*color[:3], alpha), (int(cx), int(cy)),
                         (int(cx + math.cos(ang) * ln),
                          int(cy + math.sin(ang) * ln * 0.9)),
                         2 if k % 2 == 0 else 1)
    if core:
        pygame.draw.circle(surface, (*core[:3], alpha), (int(cx), int(cy)),
                           max(1, int(size * 0.28)))


def chevron(surface, cx, cy, ang, size, color, alpha, width=3):
    """Chevron terarah untuk telegraph."""
    alpha = int(max(0, min(255, alpha)))
    if alpha <= 0 or size <= 0:
        return
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = -sa, ca
    tip = (cx + ca * size, cy + sa * size)
    for s in (-1, 1):
        pygame.draw.line(
            surface, (*color[:3], alpha),
            (int(cx + px * s * size * 0.55 - ca * size * 0.5),
             int(cy + py * s * size * 0.55 - sa * size * 0.5)),
            (int(tip[0]), int(tip[1])), width)


# ============================================================================
# 4.  PARTICLE
# ============================================================================

class Particle:
    """Partikel penuh: posisi, velocity, acceleration, life, max_life,
    size, rotation, rotation_speed, alpha, gravity, color (+ drag, shape,
    layer, additive)."""

    __slots__ = ("x", "y", "vx", "vy", "ax", "ay", "life", "max_life",
                 "size", "rotation", "rotation_speed", "alpha", "gravity",
                 "color", "shape", "drag", "additive", "layer", "active",
                 "scatter", "seed")

    def __init__(self):
        self.active = False

    def spawn(self, x, y, vx=0.0, vy=0.0, ax=0.0, ay=0.0,
              life=0.5, size=3.0, rotation=0.0, rotation_speed=0.0,
              alpha=255, gravity=0.0, color=(255, 150, 40),
              shape="ember", drag=0.0, additive=False, layer="front",
              scatter=0.0, seed=0):
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

    # -- draw ---------------------------------------------------------
    def draw(self, surface):
        if not self.active:
            return
        a = self._fade()
        if a <= 0:
            return
        color = (*self.color, a)
        x, y = int(self.x), int(self.y)
        s = max(1.0, self.size)
        shape = self.shape

        if shape == "streak":
            ang = math.atan2(self.vy, self.vx)
            ca, sa = math.cos(ang), math.sin(ang)
            pygame.draw.line(surface, color,
                             (x - ca * s * 2.0, y - sa * s * 2.0),
                             (x + ca * s * 1.2, y + sa * s * 1.2),
                             max(1, int(s * 0.6)))
        elif shape == "ember":
            t = self.life / max(0.001, self.max_life)
            col = _mix(P["fire_darkest"], self.color, t)
            _blit_faded(surface, ember_surface(max(1, int(s * 0.8)), col),
                        x, y, a, additive=True)
        elif shape == "flame":
            tmp = _scratch(int(s * 4) + 6, int(s * 5) + 6)
            flame_poly(tmp, tmp.get_width() // 2, tmp.get_height() - 2,
                       s * 2.2, seed=self.seed, alpha=a,
                       phase=self.rotation, w=s * 1.0)
            blit_add(surface, tmp, (x - tmp.get_width() // 2,
                                    y - tmp.get_height() + 2))
        elif shape == "smoke":
            r = max(2, int(s))
            _blit_faded(surface, glow_surface(r + 2, self.color, 0.32),
                        x, y, int(a * 0.7), additive=False)
        elif shape == "debris":
            shard_poly(surface, x, y, self.rotation, s * 1.8,
                       max(1.0, s * 0.6), self.color, a)
        elif shape == "dust":
            pygame.draw.circle(surface, color, (x, y), max(1, int(s * 0.55)))
        elif shape == "spark":
            c = max(1, int(s))
            pygame.draw.line(surface, color, (x - c, y), (x + c, y), 1)
            pygame.draw.line(surface, color, (x, y - c), (x, y + c), 1)
        elif shape == "ring":
            r = max(1, int(s))
            pygame.draw.circle(surface, color, (x, y), r, 1)
        elif shape == "scale":
            # serpihan sisik naga (segitiga membulat)
            ang = self.rotation
            pts = [(x + math.cos(ang + k * 2.09) * s * 1.5,
                    y + math.sin(ang + k * 2.09) * s * 1.5)
                   for k in range(3)]
            pygame.draw.polygon(surface, color, pts)
        else:
            pygame.draw.circle(surface, color, (x, y), max(1, int(s * 0.6)))


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

    def spawn(self, x, y, **kw):
        """Satu partikel dengan parameter penuh (mengikuti anggaran FX)."""
        budget = particle_budget()
        if budget <= 0.0:
            return None
        if budget < 1.0 and random.random() >= budget:
            return None
        return self._next().spawn(x, y, **kw)

    def burst(self, x, y, count, speed=(40, 140), life=(0.2, 0.5),
              size=(2, 5), colors=((255, 150, 40),), spread=math.tau,
              direction=0.0, gravity=0.0, drag=0.0, shape="ember",
              additive=True, layer="front", rotation_speed=(0.0, 0.0),
              scatter=0.0, lift=0.0):
        """Ledakan partikel terarah dengan sebaran acak."""
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
# 6.  SWING TRAIL — pita sabetan dari histori posisi senjata
# ============================================================================

class SwingTrail:
    """Trail sabetan greatsword.

    Menyimpan posisi (grip, tip) beberapa frame terakhir lalu menyusunnya
    jadi poligon translucent yang memudar — persis "slash trail dari
    posisi senjata sebelumnya" yang diminta. Digambar additive di ruang
    LAYAR, jadi tetap tajam berapa pun skala canvas.
    """

    def __init__(self, samples=TRAIL_SAMPLES):
        self.samples = max(4, int(samples))
        self.history = []            # [(grip, tip, umur, panas)]
        self.enabled = True
        self.age = 0.0
        self.hot = 0.0               # 0..1 seberapa "aktif" sabetan

    def reset(self):
        self.history.clear()
        self.age = 0.0
        self.hot = 0.0

    def push(self, grip, tip, heat=1.0):
        self.history.append([tuple(grip), tuple(tip), 0.0, float(heat)])
        if len(self.history) > self.samples:
            del self.history[0:len(self.history) - self.samples]

    def update(self, dt):
        self.age += dt
        dead = []
        for i, s in enumerate(self.history):
            s[2] += dt
            if s[2] > 0.13:
                dead.append(i)
        for i in reversed(dead):
            del self.history[i]
        self.hot = max(0.0, self.hot - dt * 3.0)

    def draw(self, surface):
        if not self.enabled or len(self.history) < 3:
            return
        n = len(self.history)

        # Setiap PASANGAN sample jadi satu quad sendiri dengan alpha
        # sendiri: yang paling baru terang, yang paling lama nyaris
        # hilang. Itu yang membuat sabetan terbaca sebagai gerak, bukan
        # sebagai pelat oranye.
        quads = []
        for i, (grip, tip, age, _heat) in enumerate(self.history):
            t = i / float(n - 1)
            fade = max(0.0, 1.0 - age / 0.13)
            gx, gy = grip
            tx, ty = tip
            k = 0.62 + 0.22 * (1.0 - t)      # ekor menyempit ke ujung bilah
            quads.append(((tx, ty),
                          (gx + (tx - gx) * k, gy + (ty - gy) * k),
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

        strength = max(0.0, min(1.0, 0.45 + self.hot * 0.55))
        for i in range(len(quads) - 1):
            (o0, i0_, f0) = quads[i]
            (o1, i1_, f1) = quads[i + 1]
            f = (f0 + f1) * 0.5 * strength
            if f <= 0.02:
                continue
            poly = [sh(o0), sh(o1), sh(i1_), sh(i0_)]
            pygame.draw.polygon(buf, (*P["fire_dark"], int(55 * f)), poly)
            mid = [sh(o0), sh(o1),
                   sh((i1_[0] + (o1[0] - i1_[0]) * 0.45,
                       i1_[1] + (o1[1] - i1_[1]) * 0.45)),
                   sh((i0_[0] + (o0[0] - i0_[0]) * 0.45,
                       i0_[1] + (o0[1] - i0_[1]) * 0.45))]
            pygame.draw.polygon(buf, (*P["fire_mid"], int(105 * f)), mid)
            pygame.draw.line(buf, (*P["fire_bright"], int(235 * f)),
                             sh(o0), sh(o1), 2)
            pygame.draw.line(buf, (*P["fire_hot"], int(210 * f)),
                             sh(o0), sh(o1), 1)
        blit_add(surface, buf, (x0, y0))

    def tip(self):
        return self.history[-1][1] if self.history else None


# ============================================================================
# 7.  IMPACT FX — flash, shockwave, retakan, fragmen sabit
# ============================================================================

class ImpactFX:
    """Satu kejadian dampak: kilat + gelombang kejut + serpihan.

    kind:
      ``melee``  — hantaman greatsword (sabit + retakan tanah)
      ``orb``    — bola api meledak
      ``meteor`` — meteor menghantam (kawah + cincin ganda)
      ``skill``  — dampak umum skill
    """

    def __init__(self, x, y, kind="melee", angle=0.0, power=1.0,
                 color=None, radius=48.0):
        self.x = float(x)
        self.y = float(y)
        self.kind = kind
        self.angle = float(angle)
        self.power = max(0.15, float(power))
        self.radius = float(radius)
        self.color = tuple(color[:3]) if color else P["fire_bright"]
        self.age = 0.0
        self.life = {"melee": 0.26, "orb": 0.30, "meteor": 0.52,
                     "skill": 0.36}.get(kind, 0.32)
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

        # -- kilat inti (2 frame pertama sangat terang) ---------------
        if t < 0.34:
            ft = 1.0 - t / 0.34
            spark_star(surface, x, y, (8 + 14 * pw) * (0.4 + 0.6 * ft),
                       P["fire_hot"], int(190 * ft), spikes=7,
                       rot=self.angle, core=P["fire_white"])
            _blit_faded(surface, glow_surface(int((10 + 16 * pw) * ft + 4),
                                              P["fire_bright"], 1.0),
                        x, y, int(240 * ft), additive=True)

        # -- gelombang kejut (cincin memuai + menipis) ----------------
        r = int(self.radius * (0.24 + 0.9 * _ease("oc", t)) * pw)
        if r > 2 and inv > 0.02:
            _blit_faded(surface,
                        ring_surface(r, max(1, int(2 * inv) + 1),
                                     self.color, 255),
                        x, y, int(200 * inv), additive=True)
            _blit_faded(surface,
                        ellipse_ring_surface(int(r * 1.1),
                                             max(2, int(r * 0.4)),
                                             2, P["magma_hot"], 255),
                        x, y + 4, int(120 * inv), additive=True)

        # -- bentuk khusus per jenis ----------------------------------
        if self.kind == "melee":
            self._draw_slash(surface, t, inv)
        elif self.kind == "meteor":
            self._draw_crater(surface, t, inv)
        elif self.kind == "orb":
            self._draw_burst(surface, t, inv)

    def _draw_slash(self, surface, t, inv):
        """Fragmen sabit: dua busur tipis melintang arah pukulan."""
        span = 1.15
        for k, (sc, wd, col) in enumerate((
                (1.0, 2, P["fire_hot"]),
                (0.74, 2, P["fire_bright"]),
                (1.2, 1, P["fire_mid"]))):
            r = self.radius * sc * (0.5 + 0.75 * _ease("out", t))
            pts = []
            for i in range(9):
                a = self.angle - span / 2 + span * i / 8.0
                pts.append((self.x + math.cos(a) * r,
                            self.y + math.sin(a) * r * 0.82))
            a255 = int((150 - k * 35) * inv)
            if a255 > 3 and len(pts) > 1:
                pygame.draw.lines(surface, (*col, a255), False, pts, wd)

    def _draw_crater(self, surface, t, inv):
        """Kawah meteor: retakan menyebar + genangan lava."""
        if self._cracks is None:
            self._cracks = []
            for k in range(6):
                a = _hash01(self.seed + k) * math.tau
                ln = self.radius * (0.55 + _hash01(self.seed + k * 3) * 0.7)
                self._cracks.append(_crack_points(
                    self.x, self.y, self.x + math.cos(a) * ln,
                    self.y + math.sin(a) * ln * 0.55, 4, 5.0,
                    self.seed + k * 11))
        grow = _ease("oc", min(1.0, t * 2.0))
        _blit_faded(surface,
                    ground_pool_surface(int(self.radius * 0.85 * grow),
                                        P["magma_hot"], 0.55),
                    self.x, self.y + 3, int(200 * inv + 40), additive=True)
        for pts in self._cracks:
            n = max(2, int(len(pts) * grow))
            seg = pts[:n]
            if len(seg) > 1:
                pygame.draw.lines(surface, (*P["magma_hot"],
                                            int(210 * inv)), False, seg, 2)
                pygame.draw.lines(surface, (*P["fire_hot"],
                                            int(150 * inv)), False, seg, 1)

    def _draw_burst(self, surface, t, inv):
        """Ledakan bola api: cangkang api bergerigi."""
        r = self.radius * (0.3 + 0.8 * _ease("oc", t))
        pts = []
        for i in range(12):
            a = i * math.tau / 12.0
            wob = 0.72 + _hash01(self.seed + i) * 0.5
            pts.append((self.x + math.cos(a) * r * wob,
                        self.y + math.sin(a) * r * wob * 0.9))
        if len(pts) > 2:
            pygame.draw.polygon(surface, (*P["fire_dark"], int(120 * inv)),
                                pts)
            pygame.draw.polygon(surface, (*P["fire_light"],
                                          int(170 * inv)), pts, 2)


# ============================================================================
# 8.  PROYEKTIL MODULAR
# ============================================================================

class BaseProjectile:
    """Kontrak proyektil bersama.

    Atribut wajib: position, velocity, speed, damage, lifetime, target,
    radius, rotation, trail, particles, active — semua dengan
    ``pygame.Vector2`` dan delta-time.
    """

    kind = "base"

    def __init__(self, x, y, tx, ty, speed=ORB_SPEED, damage=0.0,
                 lifetime=1.8, radius=13.0, target=None, owner=None):
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
        self.trail = []                       # [(Vector2, umur)]
        self.trail_len = 12
        self.particles = []                   # jejak partikel milik sendiri
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


class FireOrbProjectile(BaseProjectile):
    """Bola api Ignis: inti putih-panas, glow, ekor komet, cincin spin."""

    kind = "orb"

    def __init__(self, x, y, tx, ty, speed=ORB_SPEED, damage=0.0,
                 lifetime=1.9, radius=13.0, target=None, owner=None,
                 scale=1.0):
        super().__init__(x, y, tx, ty, speed, damage, lifetime, radius,
                         target, owner)
        self.scale = float(scale)
        self.rotation_speed = 7.5
        self.trail_len = 14
        self.wobble = random.uniform(0.0, math.tau)

    def emit(self, dt, system):
        if system is None:
            return
        if random.random() < min(1.0, dt * 46.0):
            ang = self.rotation + math.pi + random.uniform(-0.5, 0.5)
            system.particles.spawn(
                self.position.x, self.position.y,
                vx=math.cos(ang) * random.uniform(20, 70),
                vy=math.sin(ang) * random.uniform(20, 70) - 22,
                life=random.uniform(0.18, 0.42),
                size=random.uniform(1.6, 3.4),
                color=random.choice((P["fire_light"], P["fire_bright"],
                                     P["ember"])),
                shape="ember", additive=True, gravity=-40.0, drag=1.6,
                layer="front", seed=self.seed)

    def draw(self, surface):
        if not self.active:
            return
        x, y = int(self.position.x), int(self.position.y)
        r = self.radius * self.scale
        life_t = max(0.0, min(1.0, self.lifetime / self.max_lifetime))

        # -- ekor komet: pita meruncing dari histori posisi ------------
        n = len(self.trail)
        if n > 2:
            ang = self.rotation
            px, py = -math.sin(ang), math.cos(ang)
            for i in range(n - 1):
                t0 = i / float(n - 1)
                t1 = (i + 1) / float(n - 1)
                p0, a0 = self.trail[i]
                p1, a1 = self.trail[i + 1]
                f = max(0.0, 1.0 - a0 / 0.34) * t0
                if f <= 0.03:
                    continue
                w0 = r * 0.62 * t0
                w1 = r * 0.62 * t1
                quad = [(p0.x + px * w0, p0.y + py * w0),
                        (p1.x + px * w1, p1.y + py * w1),
                        (p1.x - px * w1, p1.y - py * w1),
                        (p0.x - px * w0, p0.y - py * w0)]
                pygame.draw.polygon(surface, (*P["fire_dark"],
                                              int(90 * f)), quad)
                pygame.draw.polygon(surface, (*P["fire_mid"],
                                              int(70 * f)), quad, 1)

        # -- glow luar (lembut) ----------------------------------------
        _blit_faded(surface, glow_surface(int(r * 2.2), P["fire_dark"], 0.7),
                    x, y, int(150 * life_t), additive=True)
        _blit_faded(surface, glow_surface(int(r * 1.3), P["fire_light"], 0.8),
                    x, y, int(160 * life_t), additive=True)

        # -- badan: cangkang api memanjang searah gerak ----------------
        ca, sa = math.cos(self.rotation), math.sin(self.rotation)
        pts = []
        for i in range(12):
            a = i * math.tau / 12.0
            # lonjong ke arah gerak + ekor meruncing di belakang
            stretch = 1.12 if math.cos(a) > 0 else 1.42
            wob = 1.0 + 0.12 * math.sin(a * 3.0 + self.wobble +
                                        self.age * 11.0)
            lx = math.cos(a) * r * stretch * wob * 0.92
            ly = math.sin(a) * r * 0.78 * wob
            pts.append((self.position.x + ca * lx - sa * ly,
                        self.position.y + sa * lx + ca * ly))
        pygame.draw.polygon(surface, (*P["fire_mid"], 215), pts)
        inner = [(self.position.x + (px - self.position.x) * 0.72,
                  self.position.y + (py - self.position.y) * 0.72)
                 for px, py in pts]
        pygame.draw.polygon(surface, (*P["fire_light"], 240), inner)
        pygame.draw.polygon(surface, (*P["fire_bright"], 210), pts, 1)

        # -- inti putih ------------------------------------------------
        core = (int(self.position.x + ca * r * 0.18),
                int(self.position.y + sa * r * 0.18))
        pygame.draw.circle(surface, (*P["fire_hot"], 255), core,
                           max(2, int(r * 0.48)))
        pygame.draw.circle(surface, (*P["fire_white"], 255), core,
                           max(1, int(r * 0.24)))

        # -- cincin orbit (memberi arah & rotasi) ----------------------
        rr = r * 1.55
        ca, sa = math.cos(self.rotation), math.sin(self.rotation)
        for s in (-1, 1):
            pygame.draw.line(
                surface, (*P["magma_bright"], 190),
                (int(x - ca * rr * 0.2 - sa * rr * s),
                 int(y - sa * rr * 0.2 + ca * rr * s)),
                (int(x + ca * rr * 0.75 - sa * rr * s * 0.35),
                 int(y + sa * rr * 0.75 + ca * rr * s * 0.35)), 2)


class MeteorProjectile(BaseProjectile):
    """Meteor ultimate: jatuh dari atas layar, kepala batu + selubung api."""

    kind = "meteor"

    def __init__(self, tx, ty, delay=0.0, speed=METEOR_SPEED, damage=0.0,
                 radius=22.0, owner=None, from_left=True):
        h = 340.0
        sx = tx - (150.0 if from_left else -150.0)
        sy = ty - h
        super().__init__(sx, sy, tx, ty, speed, damage,
                         lifetime=2.6, radius=radius, target=None,
                         owner=owner)
        self.delay = float(delay)
        self.rotation_speed = 5.0
        self.trail_len = 16
        self.impact_radius = radius * 3.0

    def update(self, dt, system=None):
        if not self.active:
            return
        if self.delay > 0.0:
            self.delay -= dt
            return
        super().update(dt, system)

    def check_collision(self):
        return self.position.y >= self.destination.y - 2.0

    def emit(self, dt, system):
        if system is None:
            return
        if random.random() < min(1.0, dt * 70.0):
            system.particles.spawn(
                self.position.x + random.uniform(-6, 6),
                self.position.y + random.uniform(-6, 6),
                vx=random.uniform(-40, 40), vy=random.uniform(-90, -30),
                life=random.uniform(0.25, 0.55),
                size=random.uniform(2.0, 4.6),
                color=random.choice((P["fire_light"], P["fire_mid"],
                                     P["smoke"])),
                shape="ember" if random.random() < 0.7 else "smoke",
                additive=True, drag=1.1, layer="front", seed=self.seed)

    def draw(self, surface):
        if not self.active or self.delay > 0.0:
            return
        x, y = int(self.position.x), int(self.position.y)
        r = self.radius

        # -- ekor api panjang -----------------------------------------
        n = len(self.trail)
        if n > 2:
            for i, (pos, age) in enumerate(self.trail):
                t = i / float(n - 1)
                a = int(150 * t * max(0.0, 1.0 - age / 0.5))
                if a <= 4:
                    continue
                _blit_faded(surface,
                            glow_surface(int(r * (0.35 + 0.75 * t)),
                                         P["fire_mid"], 0.9),
                            pos.x, pos.y, a, additive=True)

        _blit_faded(surface, glow_surface(int(r * 2.4), P["fire_dark"], 1.0),
                    x, y, 210, additive=True)

        # -- kepala batu (poligon tak beraturan) -----------------------
        pts = []
        for i in range(8):
            a = self.rotation + i * math.tau / 8.0
            wob = 0.78 + _hash01(self.seed + i) * 0.42
            pts.append((self.position.x + math.cos(a) * r * wob,
                        self.position.y + math.sin(a) * r * wob))
        pygame.draw.polygon(surface, (*P["plate_dark"], 255), pts)
        pygame.draw.polygon(surface, (*P["magma_hot"], 255), pts, 2)
        # urat magma di kepala
        for k in range(3):
            a = self.rotation + k * 2.1
            pygame.draw.line(
                surface, (*P["magma_bright"], 220),
                (int(x + math.cos(a) * r * 0.15),
                 int(y + math.sin(a) * r * 0.15)),
                (int(x + math.cos(a + 0.6) * r * 0.78),
                 int(y + math.sin(a + 0.6) * r * 0.78)), 2)
        pygame.draw.circle(surface, (*P["fire_hot"], 190), (x, y),
                           max(1, int(r * 0.3)))


class ProjectileSystem:
    """Manajer proyektil: spawn, update, cull, dampak, cap keras."""

    def __init__(self, particles, cap=MAX_PROJECTILES):
        self.projectiles = []
        self.particles = particles
        self.cap = max(4, int(cap))
        self.impacts = []
        self.on_impact_cb = None

    # -- spawn ---------------------------------------------------------
    def spawn_orb(self, x, y, tx, ty, **kw):
        if len(self.projectiles) >= self.cap:
            self.projectiles.pop(0)
        pr = FireOrbProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    def spawn_meteor(self, tx, ty, **kw):
        if len(self.projectiles) >= self.cap:
            self.projectiles.pop(0)
        pr = MeteorProjectile(tx, ty, **kw)
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
        if projectile.kind == "meteor":
            self._push_impact(ImpactFX(px, py, "meteor",
                                       angle=-math.pi / 2, power=1.5,
                                       color=P["fire_light"],
                                       radius=projectile.impact_radius))
            self.particles.burst(px, py, 16, speed=(90, 300),
                                 life=(0.3, 0.75), size=(2, 5),
                                 colors=(P["fire_light"], P["fire_bright"],
                                         P["ember"]),
                                 spread=math.pi * 1.1,
                                 direction=-math.pi / 2, gravity=520,
                                 drag=0.7, shape="ember")
            self.particles.burst(px, py, 8, speed=(50, 160),
                                 life=(0.4, 0.9), size=(3, 6),
                                 colors=(P["plate_mid"], P["ash"]),
                                 spread=math.pi, direction=-math.pi / 2,
                                 gravity=640, shape="debris",
                                 rotation_speed=(-9, 9), additive=False)
            if _feel is not None:
                _feel.shake(9.0, 0.22)
                _feel.hit_stop(0.05)
        else:
            self._push_impact(ImpactFX(px, py, "orb",
                                       angle=projectile.rotation,
                                       power=1.0, color=P["fire_bright"],
                                       radius=34.0))
            self.particles.burst(px, py, 14, speed=(80, 260),
                                 life=(0.22, 0.5), size=(1.8, 4.2),
                                 colors=(P["fire_bright"], P["fire_light"],
                                         P["ember"]),
                                 gravity=240, drag=1.0, shape="ember")
            self.particles.burst(px, py, 5, speed=(20, 70),
                                 life=(0.4, 0.8), size=(3, 6),
                                 colors=(P["smoke"], P["smoke_light"]),
                                 gravity=-60, shape="smoke",
                                 additive=False, layer="front")
            if _feel is not None:
                _feel.shake(4.5, 0.14)
                _feel.hit_stop(0.035)
        if self.on_impact_cb:
            try:
                self.on_impact_cb(projectile)
            except Exception:                  # pragma: no cover
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
# 9.  AFTERIMAGE — bayangan pose sebelumnya (ultimate & sabetan berat)
# ============================================================================

class Afterimage:
    """Salinan rig terakhir yang memudar (ghost trail).

    Memakai surface rig yang DISIMPAN renderer (``_last_rig``), jadi tidak
    perlu menggambar ulang badan dan pose ghost selalu benar.
    """

    __slots__ = ("surf", "x", "y", "age", "life", "tint", "active")

    def __init__(self, surf, x, y, life=0.30, tint=None):
        self.surf = surf
        self.x = float(x)
        self.y = float(y)
        self.age = 0.0
        self.life = float(life)
        self.tint = tint or P["fire_dark"]
        self.active = True

    def update(self, dt):
        self.age += dt
        if self.age >= self.life:
            self.active = False

    def draw(self, surface):
        if not self.active or self.surf is None:
            return
        t = 1.0 - self.age / self.life
        a = int(120 * t * t)
        if a <= 3:
            return
        ghost = self.surf.copy()
        ghost.fill((*self.tint, 255), special_flags=pygame.BLEND_RGB_MULT)
        blit_add(surface, ghost, (int(self.x), int(self.y)), a)


# ============================================================================
# 10.  SKILL FX — lifecycle penuh cast -> charge -> release -> area ->
#      impact -> after-effect -> fade
# ============================================================================

class SkillFX:
    """Satu instance efek skill.

    Fase (fraksi umur):
        CAST     0.00 - 0.16   telegraph, tarikan energi, rune
        CHARGE   0.16 - 0.34   penumpukan, getaran, partikel masuk
        RELEASE  0.34 - 0.46   letusan, flash, shockwave
        AREA     0.46 - 0.74   badan efek (kerucut / sapuan / pilar / erupsi)
        IMPACT   0.74 - 0.86   dampak sekunder, debu, retakan
        AFTER    0.86 - 1.00   sisa panas, asap, memudar
    """

    PHASES = (("CAST", 0.00, 0.16), ("CHARGE", 0.16, 0.34),
              ("RELEASE", 0.34, 0.46), ("AREA", 0.46, 0.74),
              ("IMPACT", 0.74, 0.86), ("AFTER", 0.86, 1.00))

    def __init__(self, skill, x, y, facing=1, target=None, scale=1.0,
                 director=None):
        self.skill = skill
        self.x = float(x)
        self.y = float(y)
        self.origin = pygame.Vector2(x, y)
        self.facing = 1 if facing >= 0 else -1
        self.target = target
        self.scale = float(scale)
        self.director = director
        self.age = 0.0
        self.life = SKILL_TOTAL.get(skill, 1.1)
        self.active = True
        self.seed = random.randint(0, 9999)
        self.radius = WORLD_RADIUS.get(skill, 120.0)
        self._released = False
        self._impacted = False
        self._meteors_sent = 0
        self._cracks = None
        tp = None
        if target is not None:
            tp = (float(getattr(target, "x", x + 140.0)),
                  float(getattr(target, "y", y)))
        self.target_point = tp or (x + self.facing * 140.0, y)

    # -- utilitas fase --------------------------------------------------
    @property
    def t(self):
        return max(0.0, min(1.0, self.age / self.life))

    def phase(self):
        p = self.t
        for name, a, b in self.PHASES:
            if a <= p < b:
                return name
        return "AFTER"

    def phase_t(self):
        p = self.t
        for _name, a, b in self.PHASES:
            if a <= p < b:
                return (p - a) / max(0.0001, b - a)
        return 1.0

    def follow(self, x, y):
        """Skill yang menempel di badan (E) ikut bergerak."""
        if self.skill in ("e",):
            self.x, self.y = float(x), float(y)

    # -- update ---------------------------------------------------------
    def update(self, dt, particles=None, projectiles=None):
        if not self.active:
            return
        prev = self.t
        self.age += dt
        if self.age >= self.life:
            self.active = False
        t = self.t
        if not self._released and prev < 0.34 <= t:
            self._released = True
            self._on_release(particles, projectiles)
        if not self._impacted and prev < 0.74 <= t:
            self._impacted = True
            self._on_impact(particles)
        self._emit(dt, t, particles, projectiles)

    # -- hook fase -------------------------------------------------------
    def _on_release(self, particles, projectiles):
        s = self.skill
        if particles is None:
            return
        if s == "q":
            particles.burst(self.x + self.facing * 26, self.y - 30, 16,
                            speed=(150, 420), life=(0.25, 0.6),
                            size=(2, 5),
                            colors=(P["fire_bright"], P["fire_light"],
                                    P["fire_hot"]),
                            spread=0.85, direction=0.0 if self.facing > 0
                            else math.pi, drag=0.6, shape="ember")
        elif s == "w":
            particles.burst(self.x, self.y + 34, 20, speed=(160, 400),
                            life=(0.3, 0.62), size=(2, 5),
                            colors=(P["dust"], P["ash"], P["fire_light"]),
                            spread=math.tau, gravity=460, drag=0.8,
                            shape="debris", rotation_speed=(-8, 8),
                            additive=False)
        elif s == "e":
            particles.burst(self.x, self.y + 20, 18, speed=(30, 110),
                            life=(0.45, 0.95), size=(2, 4.5),
                            colors=(P["cloth_light"], P["fire_mid"],
                                    P["magma_hot"]),
                            spread=0.9, direction=-math.pi / 2,
                            gravity=-140, drag=0.9, shape="ember")
        elif s == "r":
            particles.burst(self.x, self.y + 30, 26, speed=(180, 520),
                            life=(0.35, 0.8), size=(2.5, 6),
                            colors=(P["fire_bright"], P["fire_light"],
                                    P["magma_hot"], P["ash"]),
                            spread=math.tau, gravity=380, drag=0.6,
                            shape="ember")
            if projectiles is not None:
                for i in range(METEOR_COUNT):
                    off = (i - (METEOR_COUNT - 1) / 2.0) * (self.radius / 3.0)
                    projectiles.spawn_meteor(
                        self.x + off + random.uniform(-14, 14),
                        self.y + 32 + random.uniform(-6, 6),
                        delay=0.10 * i, damage=0.0,
                        radius=16 + random.random() * 8,
                        from_left=(i % 2 == 0))
                    self._meteors_sent += 1
        if _feel is not None and shake_allowed():
            _feel.shake({"q": 6.0, "w": 9.0, "e": 4.0,
                         "r": 15.0}.get(s, 6.0),
                        {"q": 0.20, "w": 0.26, "e": 0.16,
                         "r": 0.5}.get(s, 0.2))
            _feel.hit_stop({"q": 0.035, "w": 0.055, "e": 0.03,
                            "r": 0.075}.get(s, 0.04))

    def _on_impact(self, particles):
        if particles is None:
            return
        s = self.skill
        if s == "w":
            particles.burst(self.x, self.y + 34, 10, speed=(40, 130),
                            life=(0.4, 0.85), size=(3, 7),
                            colors=(P["smoke"], P["smoke_light"],
                                    P["dust"]),
                            spread=math.tau, gravity=-30, shape="smoke",
                            additive=False)
        elif s == "r":
            particles.burst(self.x, self.y + 20, 14, speed=(30, 120),
                            life=(0.6, 1.1), size=(4, 8),
                            colors=(P["smoke"], P["ash"]),
                            spread=math.tau, gravity=-50, shape="smoke",
                            additive=False)

    def _emit(self, dt, t, particles, projectiles):
        """Partikel berkelanjutan sepanjang hidup efek."""
        if particles is None:
            return
        s = self.skill
        ph = self.phase()
        if ph in ("CAST", "CHARGE"):
            # energi tersedot masuk ke titik cast
            if random.random() < dt * 34.0:
                a = random.uniform(0, math.tau)
                r = self.radius * random.uniform(0.45, 0.9)
                px = self.x + math.cos(a) * r
                py = self.y - 16 + math.sin(a) * r * 0.4
                sp = random.uniform(120, 260)
                particles.spawn(px, py,
                                vx=-math.cos(a) * sp,
                                vy=-math.sin(a) * sp * 0.4,
                                life=r / max(60.0, sp) + 0.06,
                                size=random.uniform(1.6, 3.2),
                                color=random.choice((P["fire_light"],
                                                     P["fire_bright"])),
                                shape="streak", additive=True,
                                layer="back")
        if s == "q" and ph in ("RELEASE", "AREA"):
            if random.random() < dt * 90.0:
                ang = (0.0 if self.facing > 0 else math.pi) + \
                    random.uniform(-0.34, 0.34)
                sp = random.uniform(240, 620)
                particles.spawn(self.x + self.facing * 26, self.y - 30,
                                vx=math.cos(ang) * sp,
                                vy=math.sin(ang) * sp - 30,
                                life=random.uniform(0.25, 0.55),
                                size=random.uniform(2.5, 6.0),
                                color=random.choice(
                                    (P["fire_light"], P["fire_bright"],
                                     P["fire_hot"], P["fire_mid"])),
                                shape="flame", additive=True, drag=1.3,
                                gravity=-90.0,
                                rotation_speed=random.uniform(3, 9),
                                seed=random.randint(0, 99))
        elif s == "e" and ph in ("AREA", "IMPACT", "RELEASE"):
            if random.random() < dt * 46.0:
                a = random.uniform(0, math.tau)
                r = random.uniform(10, 34)
                particles.spawn(self.x + math.cos(a) * r,
                                self.y + 30 + math.sin(a) * r * 0.35,
                                vx=random.uniform(-16, 16),
                                vy=random.uniform(-150, -70),
                                life=random.uniform(0.4, 0.8),
                                size=random.uniform(1.6, 3.4),
                                color=random.choice((P["cloth_light"],
                                                     P["magma_hot"],
                                                     P["fire_bright"])),
                                shape="ember", additive=True, drag=0.6)
        elif s == "r" and ph in ("AREA", "IMPACT", "AFTER"):
            if random.random() < dt * 40.0:
                a = random.uniform(0, math.tau)
                r = self.radius * random.uniform(0.2, 1.0)
                particles.spawn(self.x + math.cos(a) * r,
                                self.y + 34 + math.sin(a) * r * 0.35,
                                vx=random.uniform(-24, 24),
                                vy=random.uniform(-210, -90),
                                life=random.uniform(0.4, 0.95),
                                size=random.uniform(2.0, 4.6),
                                color=random.choice((P["fire_light"],
                                                     P["fire_bright"],
                                                     P["ember"])),
                                shape="ember", additive=True, drag=0.8)

    # ================= GAMBAR: LAPISAN TANAH (di bawah badan) =========
    def draw_ground(self, surface):
        if not self.active:
            return
        fn = getattr(self, "_ground_" + self.skill, None)
        if fn:
            fn(surface)

    # ================= GAMBAR: LAPISAN DEPAN (di atas badan) ==========
    def draw_front(self, surface):
        if not self.active:
            return
        fn = getattr(self, "_front_" + self.skill, None)
        if fn:
            fn(surface)

    # ------------------------------------------------------------------
    # Q — DRAGON BREATH: kerucut napas api
    # ------------------------------------------------------------------
    def _ground_q(self, surface):
        t = self.t
        ph = self.phase()
        f = self.facing
        reach = self.radius * 0.5
        base_x, base_y = self.x, self.y + 34

        if ph in ("CAST", "CHARGE"):
            # telegraph: kerucut garis putus + chevron maju
            k = self.phase_t()
            a = int(70 + 90 * k)
            spread = 0.52
            for s in (-1, 1):
                ang = s * spread
                pygame.draw.line(
                    surface, (*P["fire_mid"], a),
                    (int(base_x), int(base_y)),
                    (int(base_x + f * math.cos(ang) * reach),
                     int(base_y + math.sin(ang) * reach * 0.42)), 2)
            for i in range(3):
                d = reach * (0.35 + 0.25 * i) * (0.6 + 0.4 * k)
                chevron(surface, base_x + f * d,
                        base_y + math.sin(t * 6 + i) * 2,
                        0.0 if f > 0 else math.pi,
                        10 + 3 * i, P["fire_light"],
                        int(150 * k), 2)
            return

        # jejak bakar di tanah
        burn = _ease("oc", min(1.0, (t - 0.34) / 0.3))
        fade = 1.0 if t < 0.8 else max(0.0, 1.0 - (t - 0.8) / 0.2)
        for i in range(6):
            d = reach * (0.16 + 0.11 * i) * burn
            rw = int(10 + 4 * i)
            _blit_faded(surface,
                        ground_pool_surface(rw, P["magma_hot"], 0.5),
                        base_x + f * d,
                        base_y + math.sin(i * 1.7 + self.seed) * 3,
                        int(190 * fade), additive=True)

    def _front_q(self, surface):
        ph = self.phase()
        if ph in ("CAST", "CHARGE"):
            # bara terkumpul di mulut helm
            k = self.phase_t()
            mx = self.x + self.facing * 20
            my = self.y - 32
            _blit_faded(surface, glow_surface(int(6 + 10 * k),
                                              P["fire_light"], 0.7),
                        mx, my, int(120 * k), additive=True)
            spark_star(surface, mx, my, 5 + 7 * k, P["fire_hot"],
                       int(150 * k), spikes=6, rot=self.age * 5)
            return
        if ph == "AFTER":
            k = 1.0 - self.phase_t()
            _blit_faded(surface, glow_surface(20, P["fire_dark"], 0.8),
                        self.x + self.facing * 24, self.y - 30,
                        int(120 * k), additive=True)
            return

        # ---- badan kerucut napas api -------------------------------
        f = self.facing
        t = self.t
        grow = _ease("oc", min(1.0, (t - 0.34) / 0.16))
        fade = 1.0 if t < 0.72 else max(0.0, 1.0 - (t - 0.72) / 0.14)
        if fade <= 0.0:
            return
        mx = self.x + f * 22
        my = self.y - 30
        reach = self.radius * 0.56 * grow
        spread = 0.46

        pad = 24
        x0 = int(min(mx, mx + f * reach)) - pad
        y0 = int(my - reach * 0.6) - pad
        w = int(reach) + pad * 2 + 20
        h = int(reach * 1.2) + pad * 2
        if w < 4 or h < 4 or w > 1400 or h > 1400:
            return
        buf = _scratch(w, h)

        def sh(px, py):
            return (px - x0, py - y0)

        # tiga lapis kerucut bergerigi (gelap -> panas)
        for layer, (sc, col, alpha) in enumerate((
                (1.00, P["fire_darkest"], 105),
                (0.80, P["fire_dark"], 120),
                (0.58, P["fire_mid"], 135),
                (0.34, P["fire_light"], 150),
                (0.16, P["fire_hot"], 170))):
            pts = [sh(mx, my)]
            steps = 16
            for i in range(steps + 1):
                a = -spread * sc + (2 * spread * sc) * i / steps
                wob = (1.0 + 0.16 * math.sin(self.age * 15 + i * 1.6 +
                                             layer)
                       + 0.10 * math.sin(self.age * 27 + i * 3.7))
                rr = reach * sc * wob
                pts.append(sh(mx + f * math.cos(a) * rr,
                              my + math.sin(a) * rr))
            pygame.draw.polygon(buf, (*col, int(alpha * fade)), pts)

        # gumpalan api di ujung kerucut
        for i in range(5):
            a = -spread * 0.8 + (1.6 * spread) * i / 4.0
            rr = reach * (0.82 + 0.16 * math.sin(self.age * 9 + i))
            px = mx + f * math.cos(a) * rr
            py = my + math.sin(a) * rr
            flame_poly(buf, px - x0, py - y0, 13 + 6 * math.sin(
                self.age * 11 + i * 2.0), seed=i * 5,
                alpha=int(200 * fade), phase=self.age * 6.0, w=7)

        blit_add(surface, buf, (x0, y0))

    # ------------------------------------------------------------------
    # W — DRAGON TAIL: sapuan ekor + gelombang kejut melingkar
    # ------------------------------------------------------------------
    def _ground_w(self, surface):
        t = self.t
        ph = self.phase()
        cy = self.y + 34
        if ph in ("CAST", "CHARGE"):
            k = self.phase_t()
            _blit_faded(surface,
                        ellipse_ring_surface(int(self.radius * (1.25 - 0.3 * k)),
                                             int(self.radius * 0.44 *
                                                 (1.25 - 0.3 * k)),
                                             2, P["fire_mid"], 255),
                        self.x, cy, int(90 + 110 * k), additive=True)
            _blit_faded(surface,
                        ring_surface(int(self.radius * 0.5), 2,
                                     P["magma_hot"], 255, dashed=8),
                        self.x, cy, int(60 + 90 * k), additive=True)
            return
        grow = _ease("oc", min(1.0, (t - 0.34) / 0.26))
        fade = max(0.0, 1.0 - max(0.0, (t - 0.5)) / 0.5)
        r = self.radius * (0.25 + 1.05 * grow)
        _blit_faded(surface,
                    ellipse_ring_surface(int(r), int(r * 0.4),
                                         max(2, int(4 * fade)),
                                         P["fire_light"], 255),
                    self.x, cy, int(220 * fade), additive=True)
        _blit_faded(surface,
                    ellipse_ring_surface(int(r * 0.72), int(r * 0.29), 2,
                                         P["fire_mid"], 255),
                    self.x, cy, int(150 * fade), additive=True)
        _blit_faded(surface,
                    ground_pool_surface(int(r * 0.8), P["magma_dark"], 0.32),
                    self.x, cy, int(90 * fade), additive=True)
        # retakan tanah menyebar
        if self._cracks is None:
            self._cracks = []
            for k in range(7):
                a = _hash01(self.seed + k * 5) * math.tau
                ln = self.radius * (0.6 + _hash01(self.seed + k) * 0.55)
                self._cracks.append(_crack_points(
                    self.x, cy, self.x + math.cos(a) * ln,
                    cy + math.sin(a) * ln * 0.4, 4, 5.0, self.seed + k * 9))
        for pts in self._cracks:
            n = max(2, int(len(pts) * grow))
            pygame.draw.lines(surface, (*P["magma_hot"], int(210 * fade)),
                              False, pts[:n], 2)

    def _front_w(self, surface):
        ph = self.phase()
        t = self.t
        if ph in ("CAST", "CHARGE"):
            k = self.phase_t()
            _blit_faded(surface, glow_surface(int(14 + 16 * k),
                                              P["scale_light"], 0.9),
                        self.x - self.facing * 20, self.y + 6,
                        int(150 * k), additive=True)
            return
        if t > 0.8:
            return
        # ---- sapuan EKOR NAGA: pita busur menyapu tanah -------------
        swing = _ease("oc", min(1.0, (t - 0.34) / 0.30))
        fade = 1.0 if t < 0.62 else max(0.0, 1.0 - (t - 0.62) / 0.18)
        f = self.facing
        cx, cy = self.x, self.y + 18
        L = self.radius * 0.95
        a0, a1 = -2.55, 0.35                     # dari belakang-atas ke depan
        ang = a0 + (a1 - a0) * swing

        pad = 14
        x0 = int(cx - L) - pad
        y0 = int(cy - L * 0.9) - pad
        w = int(L * 2) + pad * 2
        h = int(L * 1.7) + pad * 2
        if w < 4 or h < 4 or w > 1400 or h > 1400:
            return
        buf = _scratch(w, h)

        upper, lower, spine = [], [], []
        segs = 10
        for i in range(segs + 1):
            u = i / float(segs)
            aa = ang - u * 0.85                  # ekor melengkung ke belakang
            rr = L * (0.18 + 0.82 * u)
            px = cx + f * math.cos(aa) * rr
            py = cy + math.sin(aa) * rr * 0.62
            thick = (9.5 * (1.0 - u) + 1.5)
            nx, ny = -math.sin(aa), math.cos(aa) * 0.62
            spine.append((px - x0, py - y0))
            upper.append((px + nx * thick - x0, py + ny * thick - y0))
            lower.append((px - nx * thick - x0, py - ny * thick - y0))

        body = upper + list(reversed(lower))
        if len(body) > 2:
            pygame.draw.polygon(buf, (*P["scale_light"], int(225 * fade)), body)
            pygame.draw.polygon(buf, (*P["magma_hot"], int(200 * fade)),
                                body, 2)
        # pelat sisik di sepanjang punggung ekor
        for i in range(1, segs, 2):
            ux, uy = upper[i]
            sx, sy = spine[i]
            pygame.draw.polygon(
                buf, (*P["plate_light"], int(230 * fade)),
                [(sx, sy), (ux + (ux - sx) * 0.4, uy + (uy - sy) * 0.4),
                 (ux + 5 * f, uy - 3)])
        # tepi panas mengikuti busur sapuan
        if len(spine) > 1:
            pygame.draw.lines(buf, (*P["fire_bright"], int(230 * fade)),
                              False, spine, 2)
        # gada api di ujung ekor
        tipx, tipy = spine[-1]
        _blit_faded(buf, glow_surface(15, P["fire_light"], 1.0), tipx, tipy,
                    int(230 * fade), additive=True)
        flame_poly(buf, tipx, tipy + 6, 20, seed=3, alpha=int(220 * fade),
                   phase=self.age * 9.0, w=9)
        blit_add(surface, buf, (x0, y0))

    # ------------------------------------------------------------------
    # E — DRAGON BLOOD: buff darah naga (rune + pilar + aura)
    # ------------------------------------------------------------------
    def _ground_e(self, surface):
        t = self.t
        cy = self.y + 34
        spin = self.age * 1.4
        pulse = 0.5 + 0.5 * math.sin(self.age * 6.0)
        fade = 1.0 if t < 0.78 else max(0.0, 1.0 - (t - 0.78) / 0.22)
        grow = _ease("out", min(1.0, t / 0.3))
        r = self.radius * 0.75 * grow

        _blit_faded(surface, ground_pool_surface(int(r), P["cloth"], 0.4),
                    self.x, cy, int(150 * fade), additive=True)
        _blit_faded(surface,
                    ellipse_ring_surface(int(r), int(r * 0.4), 3,
                                         P["cloth_light"], 255),
                    self.x, cy, int(200 * fade), additive=True)
        _blit_faded(surface,
                    ellipse_ring_surface(int(r * 0.62), int(r * 0.25), 2,
                                         P["magma_hot"], 255),
                    self.x, cy, int(160 * fade * (0.6 + 0.4 * pulse)),
                    additive=True)
        # rune: segi-lima berputar + goresan radial
        pts = []
        for i in range(5):
            a = spin + i * math.tau / 5.0
            pts.append((self.x + math.cos(a) * r * 0.78,
                        cy + math.sin(a) * r * 0.31))
        star = [pts[(i * 2) % 5] for i in range(6)]
        pygame.draw.lines(surface, (*P["magma_bright"], int(150 * fade)),
                          True, star, 2)
        for i in range(10):
            a = -spin * 0.7 + i * math.tau / 10.0
            pygame.draw.line(
                surface, (*P["cloth_light"], int(110 * fade)),
                (int(self.x + math.cos(a) * r * 0.86),
                 int(cy + math.sin(a) * r * 0.34)),
                (int(self.x + math.cos(a) * r * 1.0),
                 int(cy + math.sin(a) * r * 0.4)), 2)

    def _front_e(self, surface):
        t = self.t
        ph = self.phase()
        fade = 1.0 if t < 0.8 else max(0.0, 1.0 - (t - 0.8) / 0.2)
        # pilar api naik mengelilingi badan
        if ph in ("RELEASE", "AREA", "IMPACT"):
            k = _ease("oc", min(1.0, (t - 0.34) / 0.2))
            for i in range(5):
                a = self.age * 1.8 + i * math.tau / 5.0
                px = self.x + math.cos(a) * 30
                py = self.y + 30 + math.sin(a) * 9
                depth = math.sin(a)
                hgt = (34 + 16 * math.sin(self.age * 7 + i * 1.4)) * k
                if depth > 0:                    # pilar depan lebih terang
                    flame_poly(surface, px, py, hgt, seed=i * 3,
                               alpha=int(180 * fade), phase=self.age * 7.0,
                               w=8)
        # aura merah darah pada badan
        _blit_faded(surface, glow_surface(26, P["cloth"], 0.5),
                    self.x, self.y - 10,
                    int(46 * fade * (0.6 + 0.4 * math.sin(self.age * 5))),
                    additive=True)
        # kepala naga hantu muncul di atas (after-effect)
        if ph in ("AREA", "IMPACT", "AFTER"):
            k = min(1.0, (t - 0.46) / 0.22)
            self._ghost_dragon(surface, self.x, self.y - 76,
                               int(95 * k * fade))

    def _ghost_dragon(self, surface, cx, cy, alpha):
        """Kepala naga spektral (bentuk khas, bukan lingkaran)."""
        if alpha <= 4:
            return
        f = self.facing
        bob = math.sin(self.age * 3.4) * 3
        cy += bob
        pts = [
            (cx - f * 15, cy + 4), (cx - f * 10, cy - 6),
            (cx + f * 2, cy - 9), (cx + f * 14, cy - 4),
            (cx + f * 20, cy + 2), (cx + f * 12, cy + 5),
            (cx + f * 3, cy + 8), (cx - f * 9, cy + 9),
        ]
        pygame.draw.polygon(surface, (*P["cloth"], int(alpha * 0.42)), pts)
        pygame.draw.polygon(surface, (*P["fire_light"], alpha), pts, 1)
        # tanduk
        for s in (0, 1):
            bx = cx - f * (6 + s * 8)
            by = cy - (8 + s * 2)
            pygame.draw.line(surface, (*P["fire_bright"], alpha),
                             (int(bx), int(by)),
                             (int(bx - f * 12), int(by - 12 - s * 3)), 2)
        # mata menyala
        pygame.draw.circle(surface, (*P["fire_hot"], alpha),
                           (int(cx + f * 10), int(cy - 3)), 2)

    # ------------------------------------------------------------------
    # R — ELDER DRAGON FORM: erupsi + hujan meteor + raungan
    # ------------------------------------------------------------------
    def _ground_r(self, surface):
        t = self.t
        cy = self.y + 34
        ph = self.phase()
        if ph in ("CAST", "CHARGE"):
            k = self.phase_t()
            for i in range(3):
                rr = self.radius * (1.35 - 0.3 * k) * (0.55 + 0.22 * i)
                _blit_faded(surface,
                            ellipse_ring_surface(int(rr), int(rr * 0.4), 2,
                                                 P["fire_mid"], 255),
                            self.x, cy, int((60 + 90 * k) * (1 - i * 0.22)),
                            additive=True)
            _blit_faded(surface,
                        ring_surface(int(self.radius * 0.55), 3,
                                     P["magma_hot"], 255, dashed=12),
                        self.x, cy, int(70 + 110 * k), additive=True)
            return
        grow = _ease("oc", min(1.0, (t - 0.34) / 0.3))
        fade = max(0.0, 1.0 - max(0.0, t - 0.6) / 0.4)
        # danau lava
        _blit_faded(surface,
                    ground_pool_surface(int(self.radius * 0.9 * grow),
                                        P["magma_mid"], 0.5),
                    self.x, cy, int(210 * fade), additive=True)
        # cincin kejut ganda
        for i, sc in enumerate((1.0, 0.66)):
            r = self.radius * (0.2 + 1.1 * grow) * sc
            _blit_faded(surface,
                        ellipse_ring_surface(int(r), int(r * 0.4),
                                             max(2, int(5 * fade)),
                                             P["fire_light"] if i == 0
                                             else P["fire_hot"], 255),
                        self.x, cy, int((225 - i * 55) * fade),
                        additive=True)
        # retakan lava besar
        if self._cracks is None:
            self._cracks = []
            for k in range(10):
                a = _hash01(self.seed + k * 3) * math.tau
                ln = self.radius * (0.7 + _hash01(self.seed + k) * 0.6)
                self._cracks.append(_crack_points(
                    self.x, cy, self.x + math.cos(a) * ln,
                    cy + math.sin(a) * ln * 0.4, 5, 7.0,
                    self.seed + k * 13))
        for pts in self._cracks:
            n = max(2, int(len(pts) * grow))
            seg = pts[:n]
            pygame.draw.lines(surface, (*P["magma_dark"], int(200 * fade)),
                              False, seg, 4)
            pygame.draw.lines(surface, (*P["magma_hot"], int(220 * fade)),
                              False, seg, 2)
            pygame.draw.lines(surface, (*P["fire_hot"], int(140 * fade)),
                              False, seg, 1)

    def _front_r(self, surface):
        t = self.t
        ph = self.phase()
        if ph in ("CAST", "CHARGE"):
            k = self.phase_t()
            # energi berkumpul di dada
            _blit_faded(surface, glow_surface(int(10 + 16 * k),
                                              P["fire_light"], 0.7),
                        self.x, self.y - 14, int(105 * k), additive=True)
            spark_star(surface, self.x, self.y - 14, 8 + 12 * k,
                       P["fire_hot"], int(130 * k), spikes=8,
                       rot=self.age * 4)
            return
        # Kolom cahaya vertikal DIBUANG: berkas 200 px x ~68 px yang
        # berdiri tepat di sumbu badan menelan Ignis Drachorn selama
        # ultimate aktif. Cincin kejut + sayap api spektral di bawah
        # tetap hidup sebagai penanda ultimate.
        # raungan: 3 cincin kejut vertikal memuai dari kepala
        for i in range(3):
            rt = t - 0.34 - i * 0.09
            if rt <= 0 or rt > 0.5:
                continue
            k = rt / 0.5
            rr = int(30 + 190 * _ease("oc", k))
            _blit_faded(surface,
                        ring_surface(rr, max(1, int(3 * (1 - k))),
                                     P["fire_light"], 255),
                        self.x, self.y - 34, int(150 * (1 - k)),
                        additive=True)
        # sayap api spektral
        if 0.4 < t < 0.9:
            k = min(1.0, (t - 0.4) / 0.2) * max(0.0, 1.0 - (t - 0.7) / 0.2)
            self._fire_wings(surface, self.x, self.y - 26, k)

    def _fire_wings(self, surface, cx, cy, k):
        """Sepasang sayap api spektral (bentuk khas ultimate)."""
        if k <= 0.02:
            return
        alpha = int(165 * k)
        flap = math.sin(self.age * 5.0) * 8
        for s in (-1, 1):
            pts = [(cx, cy + 10)]
            for i in range(5):
                u = (i + 1) / 5.0
                a = -0.9 - u * 1.0
                rr = (46 + 52 * u) * k
                pts.append((cx + s * math.cos(a) * rr * 1.35,
                            cy + math.sin(a) * rr - flap * u))
            for i in range(4, -1, -1):
                u = (i + 1) / 5.0
                a = -0.75 - u * 0.75
                rr = (26 + 30 * u) * k
                pts.append((cx + s * math.cos(a) * rr * 1.2,
                            cy + math.sin(a) * rr * 0.7))
            if len(pts) > 2:
                pygame.draw.polygon(surface, (*P["fire_mid"],
                                              int(alpha * 0.42)), pts)
                pygame.draw.polygon(surface, (*P["fire_light"],
                                              min(255, int(alpha * 1.4))),
                                    pts, 2)


# ============================================================================
# 11.  DIRECTOR — satu instance per unit
# ============================================================================

class IgnisFXDirector:
    """Mengikat trail, partikel, proyektil, skill, dampak, dan game feel
    untuk SATU Ignis Drachorn (boss lane maupun hero lane)."""

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

        # pelacakan state
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

        # pelacakan skill
        self.skill_key = None
        self.skill_prev = None
        self.skill_time = 0.0

        # pelacakan lain
        self.hurt_prev = 0
        self.ember_acc = 0.0
        self.afterimage_acc = 0.0
        self.time = 0.0
        self.dt = FIXED_DT
        self.last_impact_point = None
        self.draw_age = 99.0          # detik sejak terakhir digambar

    # ==================================================================
    # SINKRONISASI (dipanggil tiap frame gambar, posisi layar diketahui)
    # ==================================================================
    def sync(self, boss, x, y):
        self.unit = boss
        self.x = float(x)
        self.y = float(y)
        self.have_pos = True
        self.draw_age = 0.0
        _sync_palette()

        # -- state animasi --------------------------------------------
        st = getattr(boss, "_ign_state", None)
        if st is None:
            action, _phase, _ap = pose_of(boss)
            st = {"idle": "IDLE", "walk": "WALK", "run": "RUN",
                  "melee": "ATTACK", "ranged": "CAST", "cast": "SKILL",
                  "hurt": "HURT", "death": "DEATH"}.get(action, "IDLE")
        if st != self.state:
            self.state_prev = self.state
            self.state = st
            self.state_time = 0.0
            self.anim_frame = 0
        self.state_priority = ANIM_STATES.get(st, 0)

        # -- progress serangan ----------------------------------------
        self.attack_prev = self.attack_progress
        ap = float(getattr(boss, "_ign_attack_progress", 0.0) or 0.0)
        self.attack_progress = ap
        self.attack_phase = attack_phase(ap)
        lo, hi = ATTACK_ACTIVE_WINDOW
        self.attack_active = lo <= ap <= hi

        action, _phase, _ap = pose_of(boss)
        swinging = action in ("melee", "attack", "swing")

        # -- trail senjata: rekam posisi bilah saat menyabet -----------
        if swinging and 0.14 <= ap <= 0.92:
            grip, tip = sword_points(boss, x, y)
            self.trail.push(grip, tip, heat=1.0 if self.attack_active
                            else 0.55)
            if self.attack_active:
                self.trail.hot = 1.0
        elif not swinging:
            self.trail.hot = max(0.0, self.trail.hot - 0.1)

        # -- dampak melee otomatis (kalau AI tidak memanggil notify) ---
        if swinging:
            if (self.attack_prev < ATTACK_IMPACT_FRAME <= ap
                    and not self.swing_done):
                self.swing_done = True
                self.swing_count += 1
                self._melee_impact(boss, x, y)
            if ap < 0.1:
                self.swing_done = False
        else:
            self.swing_done = False

        # -- skill: deteksi mulai / selesai ----------------------------
        key = getattr(boss, "active_skill", None)
        if key not in ("q", "w", "e", "r"):
            key = None
        if key != self.skill_key:
            self.skill_prev = self.skill_key
            self.skill_key = key
            self.skill_time = 0.0
            if key is not None:
                self.start_skill(boss, key, x, y)
        for sk in self.skills:
            sk.follow(x, y)

        # -- hurt flash -> percikan ------------------------------------
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
        """Bara sekitar: hidup, tapi hemat (kuota per detik).

        Berhenti otomatis kalau unit sudah tidak digambar (mati / keluar
        layar) sehingga tidak ada efek berumur tak terbatas.
        """
        if not self.have_pos or self.draw_age > 0.5:
            return
        rate = 9.0
        if self.skill_key == "r":
            rate = 26.0
        elif self.skill_key == "e":
            rate = 16.0
        elif self.state in ("WALK", "RUN"):
            rate = 14.0
        self.ember_acc += dt * rate
        while self.ember_acc >= 1.0:
            self.ember_acc -= 1.0
            if self.particles.count() > self.particles.cap * 0.8:
                break
            a = random.uniform(0, math.tau)
            r = random.uniform(6, 26)
            self.particles.spawn(
                self.x + math.cos(a) * r,
                self.y + 28 + math.sin(a) * r * 0.35,
                vx=random.uniform(-14, 14),
                vy=random.uniform(-70, -22),
                life=random.uniform(0.4, 1.0),
                size=random.uniform(1.2, 2.6),
                color=random.choice((P["ember"], P["fire_light"],
                                     P["fire_bright"])),
                shape="ember", additive=True, drag=0.5,
                layer="back" if random.random() < 0.5 else "front")

        # afterimage saat ultimate / sabetan aktif
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
        if len(self.afterimages) >= 6:
            self.afterimages.pop(0)
        self.afterimages.append(
            Afterimage(surf, self.x + off[0], self.y + off[1], 0.26,
                       P["fire_dark"]))

    def _melee_impact(self, boss, x, y):
        """Hantaman greatsword: flash + sabit + debu + hit-stop + shake."""
        grip, tip = sword_points(boss, x, y)
        ang = math.atan2(tip[1] - grip[1], tip[0] - grip[0])
        px = tip[0] - math.cos(ang) * 6.0
        py = tip[1] - math.sin(ang) * 6.0
        self.last_impact_point = (px, py)
        self.add_impact(px, py, "melee", ang, 1.15, P["fire_bright"], 34.0)
        self.particles.burst(px, py, 14, speed=(120, 340),
                             life=(0.18, 0.45), size=(1.8, 4.4),
                             colors=(P["fire_bright"], P["fire_hot"],
                                     P["ember"]),
                             spread=1.5, direction=ang, gravity=320,
                             drag=1.1, shape="ember")
        self.particles.burst(px, py, 6, speed=(60, 190),
                             life=(0.25, 0.55), size=(2, 4.5),
                             colors=(P["plate_mid"], P["ash"], P["dust"]),
                             spread=2.0, direction=ang, gravity=520,
                             shape="debris", rotation_speed=(-10, 10),
                             additive=False)
        self.particles.burst(x, y + 34, 6, speed=(50, 150),
                             life=(0.3, 0.6), size=(3, 6),
                             colors=(P["dust"], P["smoke_light"]),
                             spread=1.0,
                             direction=0.0 if tip[0] >= x else math.pi,
                             gravity=140, shape="smoke", additive=False)
        if _feel is not None:
            if shake_allowed():
                _feel.shake(7.0, 0.18)
            _feel.hit_stop(0.055)

    def start_skill(self, boss, key, x, y):
        """Mulai lifecycle FX untuk satu skill."""
        if key not in ("q", "w", "e", "r"):
            return None
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        fx = SkillFX(key, x, y, facing, getattr(boss, "target", None),
                     scale=body_scale(boss), director=self)
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        self.skills.append(fx)
        if key == "q":
            # napas api juga melempar bola api ke target
            grip, tip = sword_points(boss, x, y)
            tx, ty = target_point(boss, x, y)
            self.projectiles.spawn_orb(x + facing * 22, y - 30, tx, ty,
                                       speed=ORB_SPEED, radius=14.0,
                                       target=getattr(boss, "target", None),
                                       owner=boss, scale=1.25)
        return fx

    def spawn_projectile(self, boss, x, y, tx=None, ty=None):
        """Bola api serangan jarak jauh biasa (dipanggil renderer)."""
        grip, tip = sword_points(boss, x, y)
        if tx is None or ty is None:
            tx, ty = target_point(boss, x, y)
        pr = self.projectiles.spawn_orb(
            tip[0], tip[1], tx, ty, speed=ORB_SPEED, radius=12.0,
            target=getattr(boss, "target", None), owner=boss)
        self.particles.burst(tip[0], tip[1], 10, speed=(60, 200),
                             life=(0.16, 0.4), size=(1.6, 3.6),
                             colors=(P["fire_bright"], P["fire_light"]),
                             spread=1.6,
                             direction=math.atan2(ty - tip[1], tx - tip[0]),
                             drag=1.3, shape="ember")
        if _feel is not None:
            _feel.shake(2.5, 0.10)
        return pr

    def spawn_hurt(self, boss, x, y):
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        self.particles.burst(x - facing * 8, y - 16, 10, speed=(90, 240),
                             life=(0.2, 0.45), size=(1.6, 3.6),
                             colors=(P["cloth_light"], P["fire_light"],
                                     P["ember"]),
                             spread=2.2, direction=math.pi if facing > 0
                             else 0.0, gravity=320, drag=1.0,
                             shape="spark")
        self.add_impact(x - facing * 10, y - 16, "skill",
                        math.pi if facing > 0 else 0.0, 0.55,
                        P["cloth_light"], 26.0)

    def add_impact(self, x, y, kind="skill", angle=0.0, power=1.0,
                   color=None, radius=48.0):
        while len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        im = ImpactFX(x, y, kind, angle, power, color, radius)
        self.impacts.append(im)
        return im

    # ==================================================================
    # GAMBAR
    # ==================================================================
    def draw_ground(self, surface):
        """Di BAWAH badan: telegraph, retakan, genangan, partikel belakang."""
        for sk in self.skills:
            sk.draw_ground(surface)
        for af in self.afterimages:
            af.draw(surface)
        self.particles.draw(surface, layer="back")

    def draw_front(self, surface):
        """Di ATAS badan: trail, proyektil, partikel depan, skill, dampak."""
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
# 12.  REGISTRI DIRECTOR
#      Pola SAMA dengan heroes/varkul_fx.py: director menempel di unit
#      (``_ignis_fx``), daftar global dipakai tick() + reset_all().
# ============================================================================

_DIRECTORS = []
MAX_DIRECTORS = 12


def director_for(unit):
    """Ambil (atau buat) director FX untuk satu unit Ignis Drachorn."""
    _sync_palette()
    d = getattr(unit, "_ignis_fx", None)
    if d is None:
        d = IgnisFXDirector(unit)
        try:
            unit._ignis_fx = d
        except Exception:                        # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > MAX_DIRECTORS:
            _release(_DIRECTORS.pop(0))
    return d


def _release(director):
    try:
        if director.unit is not None:
            director.unit._ignis_fx = None
            director.unit._ign_live_fx = False
    except Exception:                            # pragma: no cover
        pass
    director.reset()


def attach(unit):
    """Pasang lapisan hidup pada unit (dipanggil pipeline render)."""
    if not IGNIS_FX_ENABLED or unit is None:
        return False
    try:
        director_for(unit)
    except Exception:                            # pragma: no cover
        return False
    try:
        unit._ign_live_fx = True
    except Exception:                            # pragma: no cover
        return False
    return True


def owns(unit):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not IGNIS_FX_ENABLED or unit is None:
        return False
    if not getattr(unit, "_ign_live_fx", False):
        return False
    d = getattr(unit, "_ignis_fx", None)
    return d is not None and d in _DIRECTORS


def tick(dt=None):
    """Majukan waktu FX satu frame nyata; aman dipanggil berkali-kali.

    Tanpa argumen, dt diambil dari bus game-feel (``fx_dt``) yang sudah
    memperhitungkan hit-stop; bus itu hanya menghasilkan dt > 0 sekali
    per frame nyata, jadi memanggil tick() dari beberapa unit dalam satu
    frame TIDAK mempercepat simulasi.
    """
    if not IGNIS_FX_ENABLED:
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
    """Bersihkan seluruh state FX Ignis (ganti level / keluar match)."""
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
    """Jumlah partikel Ignis hidup (dipakai HUD performa + tes)."""
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
    """Daftar proyektil milik unit (dipakai debug renderer & tes)."""
    d = getattr(unit, "_ignis_fx", None)
    if d is None:
        return []
    return d.projectiles.projectiles


# ============================================================================
# 13.  API GAMBAR — dipanggil renderer bosses/level4.py
#      Urutan kanonik: GROUND -> (badan digambar renderer) -> LIVE.
# ============================================================================

def draw_ground_layer(surface, unit, x, y):
    """Lapisan BAWAH badan: telegraph skill, retakan, genangan lava,
    afterimage, partikel belakang. Juga memajukan simulasi satu frame."""
    if not IGNIS_FX_ENABLED or unit is None:
        return
    if not attach(unit):
        return
    d = director_for(unit)
    d.sync(unit, x, y)
    tick()
    d.draw_ground(surface)


def draw_live_layer(surface, unit, x, y):
    """Lapisan ATAS badan: trail sabetan, proyektil, partikel depan,
    skill FX depan, dampak, lalu overlay debug. Dipanggil PALING AKHIR."""
    if not IGNIS_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if not d.have_pos or d.x != x or d.y != y:
        d.sync(unit, x, y)
    d.draw_front(surface)
    if DEBUG_CHARACTER:
        draw_debug_overlay(surface, d)


# ============================================================================
# 14.  NOTIFIKASI — dipanggil AI (bosses/base_boss.py) & renderer
# ============================================================================

def notify_melee_impact(unit, target=None, damage=0, crit=False,
                        x=None, y=None, angle=None):
    """Greatsword mendarat pada target."""
    if not IGNIS_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    try:
        power = 0.8 + min(1.6, float(damage) / 90.0)
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
    d.particles.burst(x, y, 14, speed=(120, 340), life=(0.18, 0.45),
                      size=(1.8, 4.4),
                      colors=(P["fire_bright"], P["fire_hot"], P["ember"]),
                      spread=1.5, direction=angle, gravity=320, drag=1.1,
                      shape="ember")
    d.particles.burst(x, y, 6, speed=(60, 190), life=(0.25, 0.55),
                      size=(2, 4.5),
                      colors=(P["plate_mid"], P["ash"], P["dust"]),
                      spread=2.0, direction=angle, gravity=520,
                      shape="debris", rotation_speed=(-10, 10),
                      additive=False)
    if _feel is not None:
        _feel_shake(7.0 * power, 0.18)
        _feel_hit_stop(0.055 if not crit else 0.075)


def notify_projectile_impact(unit, x, y, angle=0.0, damage=0, crit=False,
                             kind="orb"):
    """Bola api / meteor mengenai target: paket impact lengkap."""
    if not IGNIS_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    try:
        power = 0.7 + min(1.6, float(damage) / 60.0)
    except (TypeError, ValueError):
        power = 1.0
    if crit:
        power *= 1.3
    d.add_impact(x, y, "meteor" if kind == "meteor" else "orb", angle,
                 power, P["fire_bright"], 46.0 if kind != "meteor" else 70.0)
    d.particles.burst(x, y, 12, speed=(80, 260), life=(0.2, 0.5),
                      size=(1.8, 4.2),
                      colors=(P["fire_bright"], P["fire_light"],
                              P["ember"]),
                      gravity=240, drag=1.0, shape="ember")
    d.particles.burst(x, y, 4, speed=(20, 70), life=(0.4, 0.8),
                      size=(3, 6), colors=(P["smoke"], P["smoke_light"]),
                      gravity=-60, shape="smoke", additive=False)
    _feel_shake(4.0 * power, 0.14)
    _feel_hit_stop(0.035)


def notify_skill_impact(unit, x=None, y=None, radius=None, skill="q"):
    """Momen damage skill pada titik (x, y).

    AI memanggil ``notify_skill_cast`` lalu ``notify_skill_impact`` pada
    tick yang sama; SkillFX yang baru dibuat di-update di tempat (arah +
    radius final) supaya efek tidak digambar dobel.
    """
    if not IGNIS_FX_ENABLED or unit is None:
        return
    key = str(skill).lower()
    d = director_for(unit)
    if x is None or y is None:
        if not d.have_pos:
            return
        x, y = d.x, d.y + 30
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
    color = P["cloth_light"] if key == "e" else P["fire_bright"]
    rr = float(radius) if radius else {"q": 70.0, "w": 96.0, "e": 54.0,
                                       "r": 150.0}.get(key, 70.0)
    d.add_impact(x, y, "skill", 0.0, power, color, rr)
    d.particles.burst(x, y, 12 if key != "r" else 20, speed=(90, 300),
                      life=(0.25, 0.6), size=(2, 5),
                      colors=(P["fire_bright"], P["fire_light"],
                              P["ember"]),
                      gravity=300, drag=0.8, shape="ember")
    _feel_shake({"q": 6.0, "w": 9.0, "e": 4.0,
                 "r": 14.0}.get(key, 6.0), 0.22)
    _feel_hit_stop({"q": 0.035, "w": 0.05, "e": 0.03,
                    "r": 0.07}.get(key, 0.04))


def notify_skill_cast(unit, skill, x=None, y=None):
    """Skill mulai di-cast: buat lifecycle FX + guncangan awal."""
    if not IGNIS_FX_ENABLED or unit is None:
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


def notify_projectile_cast(unit, x, y, tx=None, ty=None):
    """Lepas bola api dari ujung greatsword (serangan jarak jauh).

    Renderer memanggil ini saat frame cast aktif dan lapisan hidup sudah
    mengambil alih proyektil; menggantikan ``_spawn_fire_projectile``
    versi canvas.
    """
    if not IGNIS_FX_ENABLED or unit is None:
        return None
    d = director_for(unit)
    d.sync(unit, x, y)
    return d.spawn_projectile(unit, x, y, tx, ty)


def notify_hurt(unit, amount=1.0, x=None, y=None):
    """Unit terkena damage: percikan darah-api + kilat kecil."""
    if not IGNIS_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if x is None or y is None:
        if not d.have_pos:
            return
        x, y = d.x, d.y
    d.spawn_hurt(unit, x, y)


def notify_death(unit, x=None, y=None):
    """Ledakan kematian: bara + asap + debris + guncangan berat."""
    if not IGNIS_FX_ENABLED or unit is None:
        return
    d = director_for(unit)
    if x is None or y is None:
        if not d.have_pos:
            return
        x, y = d.x, d.y
    d.add_impact(x, y, "skill", 0.0, 1.6, P["fire_light"], 120.0)
    d.particles.burst(x, y, 30, speed=(120, 420), life=(0.4, 1.0),
                      size=(2, 6),
                      colors=(P["fire_light"], P["fire_bright"],
                              P["ember"], P["ash"]),
                      spread=math.tau, gravity=340, drag=0.7,
                      shape="ember")
    d.particles.burst(x, y, 10, speed=(30, 120), life=(0.6, 1.2),
                      size=(4, 8), colors=(P["smoke"], P["smoke_light"]),
                      spread=math.tau, gravity=-40, shape="smoke",
                      additive=False)
    _feel_shake(16.0, 0.5)
    _feel_hit_stop(0.08)


def _feel_shake(strength, duration):
    if _feel is None or not shake_allowed():
        return
    try:
        _feel.shake(strength, duration)
    except Exception:                            # pragma: no cover
        pass


def _feel_hit_stop(seconds):
    if _feel is None:
        return
    try:
        _feel.hit_stop(max(0.03, min(0.08, float(seconds))))
    except Exception:                            # pragma: no cover
        pass


# ============================================================================
# 15.  OVERLAY DEBUG  (DEBUG_CHARACTER = True)
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
    """Hitbox, hurtbox, jangkauan serangan, tabrakan proyektil, state
    animasi, frame, FPS, jumlah partikel, state skill, timer serangan."""
    d = director
    if d is None or not d.have_pos:
        return
    unit = d.unit
    x, y = d.x, d.y
    k = body_scale(unit) if unit is not None else 1.0

    # -- jangkauan serangan (elips tanah) -----------------------------
    rng = float(getattr(unit, "attack_range", 55) or 55)
    _blit_faded(surface, ellipse_ring_surface(int(rng), int(rng * 0.4), 1,
                                              (90, 200, 255), 255),
                x, y + 34, 140)

    # -- radius skill aktif --------------------------------------------
    if d.skill_key:
        rr = WORLD_RADIUS.get(d.skill_key, 100.0) * k
        _blit_faded(surface, ellipse_ring_surface(int(rr), int(rr * 0.4), 1,
                                                  (255, 120, 120), 255),
                    x, y + 34, 120)

    # -- hurtbox (badan) ------------------------------------------------
    hw = int(34 * k)
    hh = int(78 * k)
    pygame.draw.rect(surface, (70, 240, 120),
                     pygame.Rect(int(x - hw), int(y - hh + 14), hw * 2,
                                 hh + 22), 1)

    # -- hitbox senjata pada jendela aktif -------------------------------
    lo, hi = ATTACK_ACTIVE_WINDOW
    active = lo <= d.attack_progress <= hi
    col = (255, 80, 80) if active else (150, 150, 160)
    if unit is not None:
        grip, tip = sword_points(unit, x, y)
        pygame.draw.line(surface, col, (int(grip[0]), int(grip[1])),
                         (int(tip[0]), int(tip[1])), 2 if active else 1)
        pygame.draw.circle(surface, col, (int(tip[0]), int(tip[1])),
                           int(16 * k), 1)

    # -- tabrakan proyektil ----------------------------------------------
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
    lines = [
        "IGNIS DRACHORN [debug]",
        "state %s <- %s (p%d)" % (st["state"], d.state_prev,
                                  d.state_priority),
        "frame %d  t %.2fs  dt %.4f" % (st["frame"], d.state_time, d.dt),
        "attack %.2f %s%s" % (st["attack_progress"], st["attack_phase"],
                              "  <HIT>" if active else ""),
        "atk timer %s  cd %s" % (getattr(unit, "timer", "-"),
                                 getattr(unit, "attack_cooldown", "-")),
        "skill %s t%.2f  boss_timer %s" % (
            d.skill_key or "-", d.skill_time,
            getattr(unit, "active_skill_timer", "-")),
        "part %d/%d  proj %d  fx %d" % (st["particles"], d.particles.cap,
                                        st["projectiles"], st["impacts"]),
        "fps %.0f  cache %d  swings %d" % (fps, cache_size(),
                                           st["swings"]),
    ]
    pad = 4
    w = max(font.size(t)[0] for t in lines) + pad * 2
    h = len(lines) * 13 + pad * 2
    box = pygame.Surface((w, h), pygame.SRCALPHA)
    box.fill((10, 8, 12, 190))
    pygame.draw.rect(box, (255, 140, 60, 200), box.get_rect(), 1)
    for i, t in enumerate(lines):
        box.blit(font.render(t, True, (255, 224, 190)), (pad, pad + i * 13))
    surface.blit(box, (int(x) + 46, int(y) - 108))


# ============================================================================
# 16.  API PUBLIK
# ============================================================================

__all__ = [
    "DEBUG_CHARACTER", "IGNIS_FX_ENABLED", "IGNIS_PALETTE",
    "MAX_PARTICLES", "MAX_PROJECTILES", "TRAIL_SAMPLES",
    "ATTACK_PHASES", "ATTACK_ACTIVE_WINDOW", "ATTACK_IMPACT_FRAME",
    "ANIM_STATES", "SKILL_DUR", "SKILL_TOTAL", "WORLD_RADIUS",
    "Particle", "ParticleSystem", "SwingTrail", "ImpactFX", "Afterimage",
    "BaseProjectile", "FireOrbProjectile", "MeteorProjectile",
    "ProjectileSystem", "SkillFX", "IgnisFXDirector",
    "attach", "owns", "director_for", "projectiles_for",
    "tick", "reset_all", "total_particles", "stats",
    "draw_ground_layer", "draw_live_layer", "draw_debug_overlay",
    "notify_melee_impact", "notify_projectile_cast",
    "notify_projectile_impact", "notify_skill_cast",
    "notify_skill_impact", "notify_hurt", "notify_death",
    "sword_arc", "sword_points", "sword_angle", "attack_phase",
    "pose_of", "render_scale", "body_scale", "screen_point",
    "target_point", "particle_budget", "glow_allowed", "shake_allowed",
    "glow_surface", "ring_surface", "ellipse_ring_surface",
    "ground_pool_surface", "ember_surface", "shard_poly", "flame_poly",
    "spark_star", "chevron", "clear_cache", "cache_size",
]
