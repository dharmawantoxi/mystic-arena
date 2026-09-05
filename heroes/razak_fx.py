# ============================================================================
# heroes/razak_fx.py
# ----------------------------------------------------------------------------
# RAZAK — COMBAT / GAME-FEEL ENGINE  (screen-space live layer)
#
# Badan Razak digambar lewat ``_NS_razak`` (bosses/level2.py) ke canvas
# yang DI-CACHE lalu di-scale oleh pipeline hero.  Artinya semua yang butuh
# gerak 60 fps sejati — trail machete api, partikel, napalm, impact,
# guncangan layar — TIDAK boleh hidup di dalam canvas itu: hasilnya ikut
# terkunci pada kuantisasi pose (2 frame per pose) dan menyusut bersama
# sprite.  Modul ini adalah lapisan hidup tersebut: digambar langsung ke
# layar pada skala 1:1 tiap frame, dengan delta-time nyata.
#
# Pembagian kerja (sengaja, supaya tidak ada efek yang digambar 2x):
#
#   RENDERER (canvas, ter-cache)      MODUL INI (layar, hidup)
#   -----------------------------     -----------------------------------
#   rig + selout + rim light          trail machete api (histori nyata)
#   bayangan kontak, aura, wisps     partikel (debu, asap, bara, ember)
#   TELEGRAPH cincin Q/W/E/R          PROYEKTIL Sticky Napalm (sistem nyata)
#   pose, wing-beat, napas            IMPACT FX + flash + hit-stop + shake
#   afterimage dash                   SkillFX Q/W/E/R + overlay DEBUG
#
# 100% PROSEDURAL. Tidak ada PNG / JPG / GIF / sprite-sheet / image.load.
# Semua bentuk dibuat dengan pygame.draw + pygame.Surface + pygame.transform.
#
# Isi modul
#   RAZAK_PALETTE      palette khusus karakter (kontrak 9 kunci + ramp)
#   Particle            partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem      pool + burst + cap, reusable
#   SwingTrail          weapon trail prosedural dari histori posisi bilah
#   ImpactFX            flash + shockwave + debris + slash fragment
#   RazakProjectile     proyektil modular (spawn->travel->hit->destroy)
#   ProjectileSystem    manajer proyektil
#   SkillFX             lifecycle FX skill (cast->charge->release->fade)
#   RazakFXDirector     satu instance per unit, mengikat semua di atas
#   draw_debug_overlay  hitbox/hurtbox/state/frame/FPS/particle/skill/timer
#   API modul           tick / reset_all / notify_* / draw_*_layer
# ============================================================================

import math
import random

import pygame
from pygame import Vector2

try:                                 # bus game-feel bersama (zephyr & gornak)
    from heroes import combat_feel as _feel
except Exception:                    # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual untuk karakter RAZAK: hitbox, hurtbox, jangkauan, state
#: animasi, frame, FPS, jumlah partikel, state skill, timer serangan.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
RAZAK_FX_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 170

#: Batas keras proyektil visual per director.
MAX_PROJECTILES = 12

#: Panjang histori trail senjata (jumlah sample posisi bilah).
TRAIL_SAMPLES = 14

#: Batas dampak aktif per director & skill sekaligus di layar.
MAX_IMPACTS = 8
MAX_SKILLS = 4

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Kecepatan molotov Sticky Napalm (px/detik, ruang layar/dunia boss).
NAPALM_SPEED = 330.0
NAPALM_ARC = 34.0

#: Radius EFEK di ruang dunia (sama dengan radius gameplay base_boss.py).
WORLD_RADIUS = {"q": 75.0, "w": 95.0, "e": 80.0, "r": 180.0}

#: Umur FX skill dalam DETIK. Sinkron dengan ``_NS_razak.SKILL_DUR``
#: (40/50/35/90 langkah simulasi = 0.67/0.83/0.58/1.50 s) plus sisa
#: after-glow supaya efek tidak "terpotong" saat pose skill selesai.
SKILL_TOTAL = {"q": 1.05, "w": 1.00, "e": 0.90, "r": 1.85}

#: Durasi pose per skill (frame) — dipakai untuk memetakan umur FX ke
#: fase yang sama dengan yang dibaca renderer.
SKILL_DUR = {"q": 40, "w": 50, "e": 35, "r": 90}


# ============================================================================
# 1.  PALETTE  —  dark-fantasy fire rider: hitam-bara + api + kuningan
# ============================================================================

RAZAK_PALETTE = {
    # ── kontrak palette karakter (9 kunci wajib) ────────────────────
    # Nilai literal = nilai renderer (satu sumber); _sync_palette()
    # menyalin ulang kalau renderer berubah.
    "outline":    (5,    3,   3),
    "shadow":     (55,  12,   5),
    "dark":       (135, 30,   8),
    "body":       (155,  62,  25),
    "mid":        (215,  80,  15),
    "light":      (255, 130,  30),
    "highlight":  (255, 180,  60),
    "weapon":     (160, 152, 165),
    "fx":         (255, 220, 130),

    # ── ramp api (napalm / trail / impact) ──────────────────────────
    "fire_darkest": (55,  12,   5),
    "fire_dark":    (135, 30,   8),
    "fire_mid":     (215, 80,  15),
    "fire_bright":  (255, 130,  30),
    "fire_hot":     (255, 180,  60),
    "fire_glow":    (255, 220, 130),
    "fire_white":   (255, 250, 210),

    # ── bat mount (ramp badan) ──────────────────────────────────────
    "bat_dark":     (92,  30,  24),
    "bat_mid":      (155,  62,  25),
    "bat_light":    (210,  95,  38),
    "bat_high":     (242, 142,  66),
    "bat_rim":      (255, 214, 150),

    # ── bahan fisik: kulit goblin, samak, kuningan, baja, asap ─────
    "skin":         (95, 145,  55),
    "leather":      (95,  62,  32),
    "brass":        (155, 108,  40),
    "brass_hot":    (250, 222, 138),
    "steel":        (95,  88,  98),
    "steel_hot":    (225, 220, 228),
    "smoke":        (76,  60,  56),
    "ash":          (38,  30,  30),
    "dust":         (150, 100,  55),

    # ── goggle biru (signature) ─────────────────────────────────────
    "blue":         (95, 165, 230),
    "blue_hot":     (176, 224, 255),
}

P = RAZAK_PALETTE

#: Kunci yang boleh disalin dari palet renderer supaya warna karakter
#: dan warna efek tidak pernah berbeda "satu derajat".
_PALETTE_SYNC = {
    "outline": "shadow_deep",
    "shadow": "fire_darkest",
    "dark": "fire_dark",
    "body": "bat_mid",
    "mid": "fire_mid",
    "light": "fire_bright",
    "highlight": "fire_hot",
    "weapon": "metal_light",
    "fx": "fire_glow",
    "fire_darkest": "fire_darkest",
    "fire_dark": "fire_dark",
    "fire_mid": "fire_mid",
    "fire_bright": "fire_bright",
    "fire_hot": "fire_hot",
    "fire_glow": "fire_glow",
    "fire_white": "fire_white",
    "bat_dark": "bat_dark",
    "bat_mid": "bat_mid",
    "bat_light": "bat_light",
    "bat_high": "bat_high",
    "bat_rim": "bat_rim",
    "skin": "gob_mid",
    "leather": "leather_mid",
    "brass": "brass_mid",
    "brass_hot": "brass_shine",
    "steel": "metal_mid",
    "steel_hot": "metal_shine",
    "smoke": "smoke_mid",
    "ash": "smoke_dark",
    "dust": "leather_light",
    "blue": "blue_light",
    "blue_hot": "blue_shine",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Salin warna tema dari ``_NS_razak.PALETTE`` sekali saja.

    Renderer adalah satu-satunya sumber kebenaran untuk material karakter;
    efek hidup tidak boleh punya salinan yang lalu melenceng.  Kalau
    renderer tidak tersedia (tooling minimal), nilai literal di atas dipakai.
    """
    global _PALETTE_SYNCED
    if _PALETTE_SYNCED:
        return
    _PALETTE_SYNCED = True
    G = _renderer()
    if G is None:
        return
    pal = getattr(G, "PALETTE", None)
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
    """``_NS_razak`` atau None. Diimpor malas: modul boss besar."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level2 import _NS_razak as G
            _RENDERER = G
        except Exception:                      # pragma: no cover
            _RENDERER = False
    return _RENDERER or None


def _fallback_pose(boss):
    """(action, phase, ap) tanpa renderer: baca atribut yang sudah ada."""
    skill = getattr(boss, "active_skill", None)
    moving = bool(getattr(boss, "_razak_moving", False))
    action = "dash" if skill == "e" else (
        "attack" if getattr(boss, "_razak_attack_active", False)
        else ("walk" if moving else "idle"))
    phase = float(getattr(boss, "pulse", 0.0) or 0.0)
    ap = 0.0
    if action == "attack":
        raw = float(getattr(boss, "_razak_attack_progress", 0.0) or 0.0)
        ap = min(1.0, max(0.0, raw))
    return action, phase, ap


def pose_of(boss):
    """(action, phase, ap) — pose yang SEDANG digambar badan."""
    G = _renderer()
    if G is None:
        return _fallback_pose(boss)
    try:
        return G._resolve_pose(boss, bool(getattr(boss, "_razak_moving",
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


def machete_points(boss, x, y):
    """(grip, tip)  machete dalam piksel layar (Vector2)."""
    G = _renderer()
    if G is not None:
        try:
            g = G._grip_screen(boss, x, y)
            t = G._tip_screen(boss, x, y)
            return Vector2(g), Vector2(t)
        except Exception:                      # pragma: no cover
            pass
    # fallback: geometri idle-belakang sederhana
    f = 1 if getattr(boss, "direction", 1) >= 0 else -1
    return Vector2(x - f * 20, y - 16), Vector2(x - f * 40, y - 25)


def gun_end(boss, x, y):
    """Moncong flamethrower dalam piksel layar (Vector2)."""
    G = _renderer()
    if G is not None:
        try:
            p = G._gun_end_screen(boss, x, y)
            return Vector2(p)
        except Exception:                      # pragma: no cover
            pass
    f = 1 if getattr(boss, "direction", 1) >= 0 else -1
    return Vector2(x + f * 30, y - 12)


# ============================================================================
# 3.  KUALITAS & PRIMITIF TER-CACHE
# ============================================================================

def _quality():
    """Faktor intensitas FX (preset kualitas x beban governor).

    Memakai ``Quality.particle_ratio`` supaya governor beban FX ikut
    menurunkan partikel saat combat ramai (mis. 6 hero sebangku), bukan
    hanya preset tinggi/sedang/rendah.
    """
    try:
        from mobile.perf import Quality as Q
        return float(getattr(Q, "particle_ratio", 1.0) or 1.0)
    except Exception:                          # pragma: no cover
        return 1.0


def particle_budget():
    """Anggaran partikel 0..1 (ikut preset kualitas)."""
    q = _quality()
    return max(0.15, min(1.0, q))


def glow_allowed():
    """Additive glow diizinkan? (diperlambat di perangkat murah)."""
    try:
        from mobile.perf import Quality as Q
        return bool(getattr(Q, "use_additive_glow", True))
    except Exception:                          # pragma: no cover
        return True


def shake_allowed():
    """Guncangan layar diizinkan? (preset kualitas)."""
    try:
        from mobile.perf import Quality as Q
        return bool(getattr(Q, "shake_allowed", True))
    except Exception:                          # pragma: no cover
        return True


def _clamp_color(color):
    r, g, b = (int(color[0]), int(color[1]), int(color[2]))
    return (max(0, min(255, r)), max(0, min(255, g)),
            max(0, min(255, b)))


def _mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def _hash01(seed):
    v = math.sin(float(seed) * 12.9898 + 78.233) * 43758.5453
    return v - math.floor(v)


# ── cache surface ─────────────────────────────────────────────────────────
_SURF_CACHE = {}
_SURF_ORDER = []
_SURF_MAX = 384


def _cache_put(key, surf):
    """Simpan surface; evict 25% tertua kalau penuh (anti bocor RAM)."""
    existing = _SURF_CACHE.get(key)
    if existing is not None:
        return existing
    if len(_SURF_CACHE) >= _SURF_MAX:
        drop = max(8, _SURF_MAX // 4)
        for _ in range(drop):
            if not _SURF_ORDER:
                break
            old = _SURF_ORDER.pop(0)
            _SURF_CACHE.pop(old, None)
    _SURF_CACHE[key] = surf
    _SURF_ORDER.append(key)
    return surf


#: Cache salinan-redup untuk blit additive (lihat `_fade_copy`).
_FADE_CACHE = {}
_FADE_ORDER = []


def clear_cache():
    _SURF_CACHE.clear()
    _SURF_ORDER.clear()
    _FADE_CACHE.clear()
    _FADE_ORDER.clear()


def cache_size():
    return len(_SURF_CACHE)


def glow_surface(radius, color, power=1.0):
    """Radial glow PREMULTIPLIED (quantized) — sekali bangun, dipakai ulang.

    ``BLEND_RGB_ADD`` MENGABAIKAN kanal alpha: kalau lingkaran digambar
    dengan RGB penuh + alpha menurun, hasil additive-nya menjadi CAKRAM
    warna solid — inilah yang membuat Razak tertelan cahaya putih-kuning
    saat Firestorm (R) / skill lain di-cast. Intensitas dikalikan ke RGB
    DAN disalin ke alpha, jadi surface yang sama benar untuk blit normal
    maupun additive (pola yang sama dipakai gornak/zephyr/kaizen).
    """
    radius = max(3, int(radius))
    power = max(0.05, min(2.0, round(power / 0.05) * 0.05))
    key = ("glow", radius, color, power)
    cached = _SURF_CACHE.get(key)
    if cached is not None:
        return cached
    size = radius * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    col = _clamp_color(color)
    steps = max(2, min(14, radius // 2))
    for i in range(steps, 0, -1):
        t = i / float(steps)
        rr = int(radius * t)
        k = 0.47 * power * (1.0 - t) ** 1.7
        if k <= 0.008:
            continue
        pygame.draw.circle(surf,
                           (int(col[0] * k), int(col[1] * k),
                            int(col[2] * k), min(255, int(255 * k))),
                           (radius + 1, radius + 1), rr)
    return _cache_put(key, surf)


def spark_surface(size, color):
    """Bintang 4 spike chunky (impact flash)."""
    size = max(3, int(size))
    key = ("spark", size, color)
    cached = _SURF_CACHE.get(key)
    if cached is not None:
        return cached
    s = size * 2 + 4
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    c = size + 2
    col = _clamp_color(color)
    for f, col2, w in ((1.0, col, max(1, size // 2)),
                       (0.6, _mix(col, (255, 255, 255), 0.5),
                        max(1, size // 4))):
        pts = [(c, c - int(size * f)), (c + int(size * 0.34 * f), c),
               (c, c + int(size * f)), (c - int(size * 0.34 * f), c)]
        pygame.draw.polygon(surf, (*col2, 255), pts)
        pts_h = [(c - int(size * f), c), (c, c - int(size * 0.34 * f)),
                 (c + int(size * f), c), (c, c + int(size * 0.34 * f))]
        pygame.draw.polygon(surf, (*col2, 255), pts_h)
    return _cache_put(key, surf)


def ring_surface(radius, thickness, color, alpha=255, dashed=0):
    """Cincin chunky; dashed = jumlah gap (0 = penuh)."""
    radius = max(3, int(radius))
    thickness = max(1, int(thickness))
    key = ("ring", radius, thickness, color, alpha, dashed)
    cached = _SURF_CACHE.get(key)
    if cached is not None:
        return cached
    size = (radius + thickness + 1) * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = radius + thickness + 1
    col = _clamp_color(color)
    if dashed <= 0:
        pygame.draw.circle(surf, (*col, alpha), (c, c), radius, thickness)
    else:
        step = math.tau / max(6, dashed)
        for i in range(max(6, dashed)):
            a0 = i * step
            a1 = a0 + step * 0.62
            pts = []
            n = 5
            for j in range(n + 1):
                a = a0 + (a1 - a0) * j / n
                pts.append((c + math.cos(a) * radius,
                            c + math.sin(a) * radius))
            if len(pts) >= 2:
                pygame.draw.lines(surf, (*col, alpha), False, pts,
                                  thickness)
    return _cache_put(key, surf)


def ellipse_ring_surface(rx, ry, thickness, color, angle_deg=0):
    """Cincin elips berarah (shockwave directional)."""
    rx = max(4, int(rx))
    ry = max(2, int(ry))
    thickness = max(1, int(thickness))
    key = ("ering", rx, ry, thickness, color, angle_deg)
    cached = _SURF_CACHE.get(key)
    if cached is not None:
        return cached
    pad = thickness + 4
    w = (rx + pad) * 2
    h = (ry + pad) * 2
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    c = (rx + pad, ry + pad)
    col = _clamp_color(color)
    # arc elips manual: sejumlah segmen garis (pixel snap)
    n = 24
    pts = []
    for i in range(n + 1):
        a = math.tau * i / n
        pts.append((c[0] + math.cos(a) * rx, c[1] + math.sin(a) * ry))
    pygame.draw.lines(surf, (*col, 255), True, pts, thickness)
    if abs(angle_deg % 360) > 0.5:
        surf = pygame.transform.rotate(surf, angle_deg)
    return _cache_put(key, surf)


def ground_glow_surface(radius, color, power=0.35):
    """Glow tanah (elips lebar) PREMULTIPLIED — dipakai untuk blit additive.

    Sama seperti `glow_surface`: alpha diabaikan oleh ``BLEND_RGB_ADD``,
    jadi intensitas harus masuk ke RGB supaya kabut tanah tidak menjadi
    piringan terang yang menelan bayangan & kaki Razak.
    """
    radius = max(8, int(radius))
    power = max(0.05, min(1.0, round(power / 0.05) * 0.05))
    key = ("gglow", radius, color, power)
    cached = _SURF_CACHE.get(key)
    if cached is not None:
        return cached
    w = radius * 2 + 4
    h = max(8, radius // 2) * 2 + 4
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    col = _clamp_color(color)
    steps = max(2, min(12, radius // 4))
    for i in range(steps, 0, -1):
        t = i / float(steps)
        rr = int(radius * t)
        rh = max(2, int((radius * 0.30) * t))
        k = 0.35 * power * (1.0 - t) ** 1.6
        if k <= 0.008:
            continue
        pygame.draw.ellipse(surf,
                            (int(col[0] * k), int(col[1] * k),
                             int(col[2] * k), min(255, int(255 * k))),
                            (w // 2 - rr, h // 2 - rh, rr * 2, rh * 2))
    return _cache_put(key, surf)


def _shard_poly(surface, cx, cy, ang, length, width, color, alpha=255,
                rot=0.0, seed=0):
    """Chip/serpihan pixel: segi empat menyamping dengan ujung runcing."""
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = -sa, ca
    l2 = length * 0.5
    w2 = width * 0.5
    pts = [(cx - ca * l2 + px * w2, cy - sa * l2 + py * w2),
           (cx - ca * l2 - px * w2, cy - sa * l2 - py * w2),
           (cx + ca * l2 - px * w2, cy + sa * l2 - py * w2),
           (cx + ca * l2 + px * w2, cy + sa * l2 + py * w2)]
    pygame.draw.polygon(surface, (*_clamp_color(color), alpha),
                        [(int(x), int(y)) for x, y in pts])


# ── scratch pool (nol alokasi permukaan per frame pada jalur stabil) ──────
_SCRATCH = {}
_SCRATCH_STAMP = {}


def _scratch(w, h):
    w = max(1, int(w))
    h = max(1, int(h))
    key = (w // 8 * 8, h // 8 * 8)
    surf = _SCRATCH.get(key)
    if surf is None:
        surf = pygame.Surface((key[0], key[1]), pygame.SRCALPHA)
        _SCRATCH[key] = surf
        _SCRATCH_STAMP[key] = 0
    _SCRATCH_STAMP[key] = _SCRATCH_STAMP.get(key, 0) + 1
    surf.fill((0, 0, 0, 0))
    return surf


def _fade_copy(surf, alpha):
    """Salinan surface dengan RGB *dan* alpha diredam (untuk blit additive).

    ``set_alpha`` tidak berpengaruh pada ``BLEND_RGB_ADD`` — tanpa langkah
    ini, glow yang "memudar" tetap ditambahkan dengan intensitas penuh dan
    menumpuk jadi bercak putih di atas badan Razak.
    """
    a = max(1, min(255, int(alpha))) // 8 * 8 or 8
    key = (id(surf), surf.get_size(), a)
    hit = _FADE_CACHE.get(key)
    if hit is not None:
        return hit[1]
    cp = surf.copy()
    cp.fill((a, a, a, a), special_flags=pygame.BLEND_RGBA_MULT)
    # Simpan JUGA sumbernya: menahan objek asli tetap hidup supaya id()
    # tidak didaur ulang oleh surface lain (kunci cache tetap valid).
    _FADE_CACHE[key] = (surf, cp)
    _FADE_ORDER.append(key)
    while len(_FADE_ORDER) > 256:
        _FADE_CACHE.pop(_FADE_ORDER.pop(0), None)
    return cp


def _blit_faded(surface, surf, cx, cy, alpha=255, additive=False):
    if alpha <= 2:
        return
    a = max(2, min(255, int(alpha)))
    if additive:
        if a < 250:
            surf = _fade_copy(surf, a)
        surface.blit(surf, (int(cx - surf.get_width() // 2),
                            int(cy - surf.get_height() // 2)),
                     special_flags=pygame.BLEND_RGB_ADD)
        return
    if a < 255:
        surf.set_alpha(a)
    surface.blit(surf, (int(cx - surf.get_width() // 2),
                        int(cy - surf.get_height() // 2)))
    surf.set_alpha(255)


# ============================================================================
# 4.  PARTIKEL  —  reusable, berbatas, pixel-snapped
# ============================================================================

class Particle:
    """Satu partikel: posisi, kecepatan, percepatan, gravitasi, rotasi,
    alpha, ukuran, warna + warna akhir, bentuk & lapisan."""

    SHAPES = ("pixel", "glow", "spark", "shard", "streak", "ember",
              "smoke", "fire")

    __slots__ = ("active", "x", "y", "vx", "vy", "ax", "ay", "life",
                 "max_life", "size", "rotation", "rotation_speed", "alpha",
                 "gravity", "color", "color_end", "drag", "fade_pow",
                 "shape", "layer", "additive", "seed")

    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.ax = 0.0
        self.ay = 0.0
        self.life = 0.0
        self.max_life = 0.0
        self.size = 1
        self.rotation = 0.0
        self.rotation_speed = 0.0
        self.alpha = 255
        self.gravity = 0.0
        self.color = (255, 255, 255)
        self.color_end = None
        self.drag = 0.0
        self.fade_pow = 1.0
        self.shape = "pixel"
        self.layer = "front"
        self.additive = False
        self.seed = 0

    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        self.active = True
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.ax = float(kw.get("ax", 0.0))
        self.ay = float(kw.get("ay", 0.0))
        self.life = self.max_life = max(0.02, float(life))
        self.size = max(1, int(size))
        self.rotation = float(kw.get("rotation", 0.0))
        self.rotation_speed = float(kw.get("rotation_speed", 0.0))
        self.alpha = int(kw.get("alpha", 255))
        self.gravity = float(kw.get("gravity", 0.0))
        self.color = _clamp_color(color)
        ce = kw.get("color_end")
        self.color_end = _clamp_color(ce) if ce else None
        self.drag = float(kw.get("drag", 0.0))
        self.fade_pow = float(kw.get("fade_pow", 1.0))
        self.shape = kw.get("shape", "pixel") if kw.get("shape") in \
            self.SHAPES else "pixel"
        self.layer = kw.get("layer", "front") if kw.get("layer") in \
            ("back", "front") else "front"
        self.additive = bool(kw.get("additive", False))
        self.seed = int(kw.get("seed", 0))

    @property
    def position(self):
        return Vector2(self.x, self.y)

    @property
    def velocity(self):
        return Vector2(self.vx, self.vy)

    @property
    def acceleration(self):
        return Vector2(self.ax, self.ay)

    def update(self, dt):
        if not self.active:
            return False
        self.life -= dt
        if self.life <= 0.0:
            self.active = False
            return False
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        self.vy += self.gravity * dt
        if self.drag > 0.0:
            k = max(0.0, 1.0 - self.drag * dt)
            self.vx *= k
            self.vy *= k
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rotation_speed * dt
        return True

    def _fade(self):
        t = self.life / self.max_life
        a = self.alpha * (t ** self.fade_pow)
        return int(max(0, min(255, a)))

    def draw(self, surface):
        if not self.active:
            return
        a = self._fade()
        if a <= 2:
            return
        x = int(round(self.x))
        y = int(round(self.y))
        col = self.color
        if self.color_end is not None:
            k = 1.0 - (self.life / self.max_life)
            col = _mix(self.color, self.color_end, k)
        col = _clamp_color(col)
        shape = self.shape
        if shape == "pixel":
            pygame.draw.rect(surface, (*col, a),
                             (x, y, self.size, self.size))
        elif shape == "ember":
            pygame.draw.circle(surface, (*_mix(col, (255, 255, 255), 0.4),
                                         a), (x, y), max(1, self.size // 2))
            if glow_allowed() and self.size >= 3:
                g = glow_surface(self.size * 3, col, 0.35)
                _blit_faded(surface, g, x, y, a // 3, additive=True)
        elif shape == "glow":
            g = glow_surface(max(3, self.size * 4), col,
                             0.5 + 0.5 * (self.life / self.max_life))
            _blit_faded(surface, g, x, y, a, additive=self.additive)
        elif shape == "spark":
            s = spark_surface(max(3, self.size * 2), col)
            _blit_faded(surface, s, x, y, a, additive=self.additive)
        elif shape == "shard":
            sh = _scratch(self.size * 4 + 8, self.size * 4 + 8)
            _shard_poly(sh, self.size * 2 + 4, self.size * 2 + 4,
                        self.rotation, self.size * 2.4, max(1, self.size),
                        col, a)
            surface.blit(sh, (x - self.size * 2 - 4, y - self.size * 2 - 4))
        elif shape == "streak":
            ln = max(2.0, (self.vx * self.vx + self.vy * self.vy) ** 0.5)
            k = min(1.0, (self.size * 6.0) / max(1.0, ln))
            ex = x - int(round(self.vx * 0.05 * k))
            ey = y - int(round(self.vy * 0.05 * k))
            pygame.draw.line(surface, (*_mix(col, (255, 255, 255), 0.3), a),
                             (x, y), (ex, ey), max(1, self.size // 2))
        elif shape == "smoke":
            r = max(1, self.size + int((1.0 - self.life / self.max_life)
                                       * self.size * 1.6))
            pygame.draw.circle(surface, (*col, a // 3), (x, y), r)
            pygame.draw.circle(surface, (*_mix(col, (30, 24, 24), 0.5),
                                         a // 4), (x, y), max(1, r - 1))
        else:  # fire: 3 lapis chunky (dark -> bright -> hot)
            r = max(1, self.size)
            pygame.draw.circle(surface, (*_mix(col, P["fire_dark"], 0.55),
                                         a), (x, y), r + 1)
            pygame.draw.circle(surface, (*col, a), (x, y), r)
            pygame.draw.circle(surface,
                               (*_mix(col, P["fire_white"], 0.65), a),
                               (x, y), max(1, r - 1))
            if glow_allowed() and r >= 2:
                g = glow_surface(r * 4, col, 0.5)
                _blit_faded(surface, g, x, y, a // 2, additive=True)


class ParticleSystem:
    """Pool reusable + cap keras. ``spawn``/``burst``/``stream``/update/draw."""

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = max(8, int(cap))
        self.pool = [Particle() for _ in range(self.cap)]
        self.dropped = 0

    def _acquire(self):
        for p in self.pool:
            if not p.active:
                return p
        self.dropped += 1
        return None

    def count(self):
        return sum(1 for p in self.pool if p.active)

    def alive(self):
        return self.count()

    def clear(self):
        for p in self.pool:
            p.active = False

    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        p = self._acquire()
        if p is None:
            return None
        p.spawn(x, y, vx, vy, life, size, color, **kw)
        return p

    def burst(self, x, y, count, speed=(60.0, 210.0), life=(0.22, 0.55),
              size=(1, 3), colors=((255, 255, 255),), spread=math.tau,
              direction=0.0, gravity=0.0, drag=0.0, shape="pixel",
              additive=False, layer="front", seed=0,
              rotation_speed=(0.0, 0.0), fade_pow=1.0):
        """Ledakan partikel ke segala arah (atau di sekitar ``direction``)."""
        n = max(1, int(count * particle_budget()))
        out = 0
        for i in range(n):
            if spread >= math.tau - 0.001:
                ang = direction + random.random() * math.tau
            else:
                ang = direction + (random.random() - 0.5) * spread
            spd = random.uniform(*speed)
            vy = math.sin(ang) * spd
            col = colors[i % len(colors)]
            p = self.spawn(x, y, math.cos(ang) * spd, vy,
                           random.uniform(*life), random.randint(*size),
                           col, gravity=gravity, drag=drag, shape=shape,
                           additive=additive, layer=layer,
                           seed=seed + i,
                           rotation=random.random() * math.tau,
                           rotation_speed=random.uniform(*rotation_speed),
                           fade_pow=fade_pow)
            if p is not None:
                out += 1
        return out

    def stream(self, x, y, tx, ty, count, life=(0.3, 0.6), size=(1, 3),
               colors=((255, 255, 255),), bow=10.0, additive=False,
               layer="front", gravity=0.0, drag=0.0, shape="pixel"):
        """Pancaran dari (x, y) ke (tx, ty) dengan lengkung ``bow``."""
        n = max(1, int(count * particle_budget()))
        for i in range(n):
            t = random.random()
            px = x + (tx - x) * t
            py = y + (ty - y) * t
            px -= math.sin(t * math.pi) * bow
            ex = (tx - x)
            ey = (ty - y)
            ln = max(1.0, math.hypot(ex, ey))
            spd = random.uniform(60.0, 160.0)
            col = colors[i % len(colors)]
            self.spawn(px, py, ex / ln * spd, ey / ln * spd,
                       random.uniform(*life), random.randint(*size), col,
                       additive=additive, layer=layer, gravity=gravity,
                       drag=drag, shape=shape, seed=i * 17)
        return n

    def update(self, dt):
        for p in self.pool:
            if p.active:
                p.update(dt)

    def draw(self, surface, layer="front"):
        for p in self.pool:
            if p.active and p.layer == layer:
                p.draw(surface)


# ============================================================================
# 5.  SWING TRAIL  —  machete api dari histori posisi bilah NYATA
# ============================================================================

class SwingTrail:
    """Pita api 4 band dari (grip, tip) historis.

    Data disimpan sebagai sampel: OLD ... CURRENT (TRAIL_SAMPLES).  Tiap
    pasang titik berumur sendiri, jadi ekor memudar & menyempit; pita
    mengikuti arah ayunan karena murni turunan dari lintasan bilah.
    """

    def __init__(self, samples=TRAIL_SAMPLES):
        self.samples = []
        self.max_samples = max(6, int(samples))
        self.lifetime = 0.26
        self.width_boost = 1.0
        self.last_grip = None
        self.last_tip = None
        #: sapuan total maksimum satu pita (lebih dari itu trail akan
        #: melingkari badan dan menjadi "tembok" transparan)
        self.MAX_SWEEP = 1.95
        #: langkah sudut maksimum sebelum busur dipecah jadi beberapa quad
        self.ARC_STEP = 0.16

    def reset(self):
        self.samples = []
        self.last_grip = None
        self.last_tip = None

    def push(self, grip, tip, grip_b=None, tip_b=None):
        """Tambahkan sampel bilah saat ini (grip/tip = Vector2 layar)."""
        self.samples.append({
            "g": Vector2(grip), "t": Vector2(tip),
            "age": 0.0, "seed": len(self.samples),
        })
        while len(self.samples) > self.max_samples:
            self.samples.pop(0)
        self.last_grip = Vector2(grip)
        self.last_tip = Vector2(tip)

    def update(self, dt):
        alive = []
        for s in self.samples:
            s["age"] += dt
            if s["age"] < self.lifetime:
                alive.append(s)
        self.samples = alive

    @staticmethod
    def _ang_delta(a_new, a_old):
        """Selisih sudut terdekat (-pi..pi); tanda = arah tebasan."""
        return (a_new - a_old + math.pi) % (2.0 * math.pi) - math.pi

    # ------------------------------------------------------------------
    def _ribbon(self, surface, lst, edge, core, tip_col, base_alpha):
        """Satu band API sebagai sector cincin yang disapu UJUNG bilah.

        Senjata yang BERPUTAR meninggalkan sector antara radius dalam dan
        radius ujung, dibatasi dua sudut — itulah yang benar-benar
        terlihat sebagai bekas tebasan (bukan lembaran raksasa yang
        menutupi badan).  Pita ramping di tepi luar + inti + glint; alpha
        naik kuadrat ke sampel terbaru, jadi akselerasi terasa walau
        frame sedikit.
        """
        n = len(lst)
        if n < 2:
            return
        # histori -> (poros, sudut, radius, umur)
        nodes = []
        for s in lst:
            blade = s["t"] - s["g"]
            r = blade.length()
            if r < 6.0:
                continue                      # bilah terlipat: tak ada busur
            nodes.append((s["g"], math.atan2(blade.y, blade.x), r,
                          s["age"]))
        if len(nodes) < 2:
            return

        # putus strip saat arah berbalik
        strips = []
        cur = [nodes[0]]
        prev_dir = 0.0
        for i in range(1, len(nodes)):
            da = self._ang_delta(nodes[i][1], cur[-1][1])
            if abs(da) < 0.035:
                continue                      # tidak ada sapuan -> tidak ada pita
            if prev_dir * da < 0.0:           # arah berbalik -> mulai baru
                if len(cur) > 1:
                    strips.append((cur, prev_dir))
                cur = [nodes[i - 1], nodes[i]]
                prev_dir = da
                continue
            prev_dir = da
            cur.append(nodes[i])
        if len(cur) > 1:
            strips.append((cur, prev_dir))

        for raw, _pd in strips:
            strip = raw
            sweep = 0.0
            keep = 0
            for j in range(len(strip) - 1, 0, -1):
                sweep += abs(self._ang_delta(strip[j][1], strip[j - 1][1]))
                if sweep > self.MAX_SWEEP:
                    keep = j
                    break
            if keep:
                strip = strip[keep:]
            m = len(strip)
            if m < 2:
                continue

            xs, ys = [], []
            for (gx, _a, r, _age) in strip:
                xs += [gx.x - r * 0.20, gx.x + r * 1.12]
                ys += [gx.y - r * 1.12, gx.y + r * 1.12]
            minx, maxx = int(min(xs)) - 2, int(max(xs)) + 2
            miny, maxy = int(min(ys)) - 2, int(max(ys)) + 2
            w, h = maxx - minx, maxy - miny
            if w <= 2 or h <= 2 or w > 1400 or h > 1400:
                continue
            buf = _scratch(w, h)

            # ── OPTIMASI (v31) ──
            # Dua pemborosan di loop ini terukur di profil (satu hero
            # Razak saja: 0.55 ms/frame, 506 panggilan fungsi/frame):
            #
            #  1. `polar()` adalah closure yang DIBUAT ULANG tiap strip
            #     dan dipanggil 5x per titik. Kelimanya memakai sudut
            #     `aa` yang sama, jadi cos/sin dihitung 5 kali untuk
            #     nilai identik. Sekarang cos/sin dihitung SEKALI per
            #     titik lalu dipakai ulang.
            #  2. `glint` diisi dengan `polar(g1.x, g1.y, aa, rr)` —
            #     argumen PERSIS sama dengan `outer`. Jadi isinya selalu
            #     identik dengan `outer` dan list-nya mubazir; digambar
            #     langsung dari `outer`.
            #
            # Urutan operasi dijaga sama (`int(cx + cos*rad) - minx`,
            # bukan `int(cx - minx + cos*rad)`) supaya pembulatan
            #     truncation tidak bergeser satu piksel pun.

            for j in range(m - 1):
                (g0, a0, r0, age0) = strip[j]
                (g1, a1, r1, _age1) = strip[j + 1]
                gx1 = g1.x
                gy1 = g1.y
                da = self._ang_delta(a1, a0)
                if abs(da) < 0.02:
                    continue
                fade = max(0.0, 1.0 - age0 / self.lifetime)
                rank = (j + 1) / float(m)
                spread = min(1.0, 0.34 / max(0.05, abs(da)))
                k = (rank ** 2) * fade * self.width_boost * spread
                if k <= 0.012:
                    continue
                thin = 0.05 + 0.075 * rank
                steps = max(1, min(8, int(abs(da) / self.ARC_STEP) + 1))
                outer, inner, cout, cin = [], [], [], []
                k_thin = 1.0 - thin
                k_core = 1.0 - thin * 0.40
                for q in range(steps + 1):
                    f = q / float(steps)
                    aa = a0 + da * f
                    rr = (r0 + (r1 - r0) * f) * 0.97
                    ca = math.cos(aa)
                    sa = math.sin(aa)
                    ri = rr * k_thin
                    rc = rr * k_core
                    ro = rr * 0.985
                    outer.append((int(gx1 + ca * rr) - minx,
                                  int(gy1 + sa * rr) - miny))
                    inner.append((int(gx1 + ca * ri) - minx,
                                  int(gy1 + sa * ri) - miny))
                    cout.append((int(gx1 + ca * ro) - minx,
                                 int(gy1 + sa * ro) - miny))
                    cin.append((int(gx1 + ca * rc) - minx,
                                int(gy1 + sa * rc) - miny))
                # wash lebar sengaja LEMAH supaya tidak menutupi badan
                a_edge = int(base_alpha * k * 0.62)
                if a_edge > 5:
                    pygame.draw.polygon(buf, (*edge, a_edge),
                                        outer + inner[::-1])
                a_core = int((base_alpha + 96) * k)
                if a_core > 8:
                    pygame.draw.polygon(buf, (*core, min(255, a_core)),
                                        cout + cin[::-1])
                a_tip = int(235 * k)
                if a_tip > 14:
                    # `glint` dulu salinan persis `outer` (lihat catatan
                    # di atas) -> dipakai langsung.
                    pygame.draw.lines(buf, (*tip_col, min(255, a_tip)),
                                      False, outer, 2 if k > 0.78 else 1)
            surface.blit(buf, (minx, miny))

    # ------------------------------------------------------------------
    def draw(self, surface):
        if len(self.samples) < 2:
            return
        for edge, core, tip_col, alpha in (
                (P["fire_dark"], P["fire_mid"], P["fire_bright"], 120),
                (P["fire_bright"], P["fire_hot"], P["fire_glow"], 150),
                (P["fire_hot"], P["fire_glow"], P["fire_white"], 180),
                (P["fire_glow"], P["fire_white"], P["fire_white"], 200)):
            self._ribbon(surface, self.samples, edge, core, tip_col,
                         alpha)
        # bara yang terlempar dari ujung bilah terbaru
        newest = self.samples[-1]
        k = 1.0 - newest["age"] / self.lifetime
        for i in range(3):
            ang = _hash01(newest["seed"] * 7 + i) * math.tau
            ex = newest["t"].x + math.cos(ang) * 6 * k
            ey = newest["t"].y + math.sin(ang) * 5 * k
            _blit_faded(surface,
                        glow_surface(4, P["fire_hot"], 0.5),
                        ex, ey, int(180 * k), additive=True)


# ============================================================================
# 6.  IMPACT FX  —  flash + shockwave + debris + slash fragment
# ============================================================================

class ImpactFX:
    """Paket benturan di satu titik; meluruh sendiri, tidak pernah abadi."""

    KINDS = ("slash", "napalm", "flame", "dash", "storm", "hurt")

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="slash", ground=0.0, seed=0):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = max(0.35, min(2.2, float(power)))
        self.crit = bool(crit)
        self.kind = kind if kind in self.KINDS else "slash"
        self.ground = float(ground)
        self.seed = int(seed)
        self.age = 0.0
        self.total = min(0.62, 0.30 + 0.12 * self.power)

    def _ramp(self):
        t = min(1.0, self.age / max(0.001, self.total))
        return t

    def update(self, dt):
        self.age += dt
        return self.age < self.total

    # ------------------------------------------------------------------
    def draw(self, surface):
        t = self._ramp()
        if t >= 1.0:
            return
        k = 1.0 - t
        x, y = int(self.x), int(self.y)
        kind = self.kind
        if kind == "slash":
            hot, bright = P["fire_hot"], P["fire_white"]
        elif kind == "napalm":
            hot, bright = P["fire_bright"], P["fire_glow"]
        elif kind == "flame":
            hot, bright = P["fire_hot"], P["fire_glow"]
        elif kind == "hurt":
            hot, bright = P["blue_hot"], P["fire_white"]
        elif kind == "dash":
            hot, bright = P["fire_bright"], P["fire_hot"]
        else:
            hot, bright = P["fire_glow"], P["fire_white"]

        # 1. FLASH — bintang 8 spike chunky + halo hangat KOMPAK
        # (ukuran paritas keluarga Gornak: glow 5+10*pw, bukan bola besar)
        s = spark_surface(int((10 + 12 * self.power) * (0.5 + 0.5 * k)),
                          bright)
        _blit_faded(surface, s, x, y, int(235 * k), additive=True)
        if glow_allowed():
            g = glow_surface(int((6 + 10 * self.power) * (0.5 + 0.5 * k)),
                             hot, 0.55 * k)
            _blit_faded(surface, g, x, y, int(150 * k), additive=True)

        # 2. SHOCKWAVE — satu elips berarah (bukan lingkaran generik)
        rr = int((10 + 26 * t) * (0.8 + 0.25 * self.power))
        if rr > 5:
            er = ellipse_ring_surface(rr, max(2, int(rr * 0.42)),
                                      max(1, int(4 * k)), hot, 0)
            er.set_alpha(int(200 * k * (1.0 - t * 0.4)))
            surface.blit(er, (x - er.get_width() // 2,
                              y - er.get_height() // 2 - 4))
            if kind in ("napalm", "storm", "dash"):
                # ring tanah kedua (elips lebar di ground)
                gr = int(rr * 1.25)
                er2 = ellipse_ring_surface(gr, max(2, int(gr * 0.22)),
                                           max(1, int(3 * k)), bright, 0)
                er2.set_alpha(int(150 * k))
                surface.blit(er2, (x - er2.get_width() // 2,
                                   int(y + self.ground) -
                                   er2.get_height() // 2))

        # 3. SLASH FRAGMENTS — 3 lengkung sabit mengikuti arah serang
        if kind in ("slash", "flame", "storm"):
            for i in range(3):
                ang = self.angle + (i - 1) * 0.55 * k
                ln = int((14 + 8 * i) * (0.6 + 0.4 * k))
                bx = x + math.cos(ang) * 6
                by = y + math.sin(ang) * 6
                pygame.draw.arc(
                    surface, (*_clamp_color(hot), int(210 * k)),
                    (int(bx - ln), int(by - ln), ln * 2, ln * 2),
                    ang - 0.35, ang + 0.35, max(1, int(3 * k)))
                if i % 2 == 0:
                    pygame.draw.line(surface,
                                     (*_clamp_color(P["fire_white"]),
                                      int(160 * k)),
                                     (int(x + math.cos(ang) * ln),
                                      int(y + math.sin(ang) * ln * 0.6)),
                                     (int(x + math.cos(ang) * (ln + 6)),
                                      int(y + math.sin(ang) * (ln + 6) * .6)),
                                     1)

        # 4. DEBRIS — serpihan bara radial (sudah di-spawn particle;
        #    di sini tambahan core dekat tanah supaya berat terasa)
        if kind in ("napalm", "dash", "storm") and t < 0.5:
            for i in range(4):
                a = _hash01(self.seed * 13 + i) * math.tau
                rr = int((8 + 10 * t) * (1.0 + 0.3 * (i % 3)))
                pygame.draw.circle(surface,
                                   (*P["fire_dark"], int(150 * k)),
                                   (x + int(math.cos(a) * rr),
                                    y + int(math.sin(a) * rr * 0.5) +
                                    int(self.ground)), max(1, 4 - i))
        # 5. crit: pilar pendek emas
        if self.crit:
            pygame.draw.rect(surface, (*P["brass_hot"], int(190 * k)),
                             (x - 2, y - int(18 * k), 4, int(18 * k)))


# ============================================================================
# 7.  PROYEKTIL  —  Sticky Napalm (molotov dengan lifecycle penuh)
# ============================================================================

class RazakProjectile:
    """Molotov napalm: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT -> DESTROY.

    Kontrak: position, velocity, speed, damage, lifetime, target, radius,
    rotation, trail, particles, active.  Visual-only: damage otoritatif
    tetap di bosses/base_boss.py._razak_q (paritas Gornak/Grimjaw).
    """

    STATE_SPAWN = "spawn"
    STATE_TRAVEL = "travel"
    STATE_TRAIL = "trail"
    STATE_HIT = "hit"
    STATE_IMPACT = "impact"
    STATE_DESTROY = "destroy"

    def __init__(self, x, y, tx, ty, speed=NAPALM_SPEED, damage=0,
                 lifetime=1.4, target=None, radius=8.0, arc_height=None,
                 kind="napalm", ground=0.0, particles=None,
                 on_impact=None):
        self.position = Vector2(x, y)
        self.velocity = Vector2()
        self.speed = float(speed)
        self.damage = int(damage)
        self.lifetime = float(lifetime)
        self.target = target
        self.radius = float(radius)
        self.rotation = 0.0
        self.trail = []
        self.particles = particles
        self.active = True
        self.state = self.STATE_SPAWN
        self.kind = kind
        self.ground = float(ground)
        self.on_impact = on_impact
        self._start = Vector2(x, y)
        self._end = Vector2(tx, ty)
        self._dist = max(1.0, self._start.distance_to(self._end))
        self._age = 0.0
        self._dur = max(0.20, min(0.95, self._dist / max(40.0, self.speed)))
        self._arc = float(arc_height if arc_height is not None
                          else NAPALM_ARC)
        self._hit_pos = Vector2(tx, ty)
        self._impacted = False
        self.seed = random.randint(0, 999999)

    # ------------------------------------------------------------------
    def kill(self, x=None, y=None):
        if x is not None:
            self._hit_pos = Vector2(x, y)
        if not self._impacted:
            self._impacted = True
            try:
                if self.on_impact is not None and \
                        callable(self.on_impact):
                    self.on_impact(self)
            except Exception:                    # pragma: no cover
                pass
        self.active = False
        self.state = self.STATE_DESTROY

    def update(self, dt):
        if not self.active:
            return False
        self._age += dt
        if self._age >= self._dur or self._age >= self.lifetime:
            self.position = Vector2(self._end)
            self._hit()
            return False
        t = self._age / self._dur
        self.position = self._start.lerp(self._end, t)
        self.position.y += -4.0 * self._arc * t * (1.0 - t)
        self.rotation += dt * (self.speed / max(1.0, self.radius)) * 0.6
        self.state = self.STATE_TRAVEL if t < 0.5 else self.STATE_TRAIL
        self.trail.append((float(self.position.x), float(self.position.y),
                           self._age))
        if len(self.trail) > 10:
            self.trail.pop(0)
        # ember kecil yang jatuh dari molotov
        if self.particles is not None and self._age * 20 % 3 < 1:
            self.particles.spawn(
                self.position.x, self.position.y,
                random.uniform(-24, 24), random.uniform(-10, 34),
                random.uniform(0.2, 0.42), 1,
                P["fire_bright"], color_end=P["fire_dark"],
                gravity=120.0, drag=1.2, shape="ember", additive=True,
                seed=self.seed)
        # tumbukan target hidup (radius vs radius)
        tgt = self.target
        if tgt is not None and getattr(tgt, "alive", True):
            tx = float(getattr(tgt, "x", self._end.x))
            ty = float(getattr(tgt, "y", self._end.y))
            tr = float(getattr(tgt, "radius", 12))
            if Vector2(self.position.x, self.position.y).distance_to(
                    (tx, ty)) <= self.radius + tr + 4.0:
                self._hit_pos = Vector2(tx, ty)
                self._hit()
                return False
        return True

    def _hit(self):
        self.state = self.STATE_HIT
        # impact terjadi SEKALI di titik akhir
        self.kill(self._hit_pos.x, self._hit_pos.y)

    # ------------------------------------------------------------------
    def draw(self, surface):
        if not self.active:
            return
        if self.state == self.STATE_DESTROY:
            return
        # trail: asap dingin -> api panas (mengikuti lengkung)
        n = len(self.trail)
        for i, (tx, ty, age) in enumerate(self.trail):
            k = i / max(1, n - 1)
            a = int(40 + k * 150)
            r = max(1, int(2 + k * 4))
            if k < 0.45:
                pygame.draw.circle(surface, (*P["smoke"], int(a * 0.7)),
                                   (int(tx), int(ty)), r + 1)
                pygame.draw.circle(surface, (*P["ash"], int(a * 0.5)),
                                   (int(tx), int(ty - 1)), r)
            else:
                pygame.draw.circle(surface, (*P["fire_dark"], a),
                                   (int(tx), int(ty)), r + 1)
                pygame.draw.circle(surface, (*P["fire_bright"], a),
                                   (int(tx), int(ty)), r)
                pygame.draw.circle(surface, (*P["fire_hot"], int(a * 0.8)),
                                   (int(tx), int(ty - 1)), max(1, r - 2))

        px, py = int(self.position.x), int(self.position.y)
        if glow_allowed():
            g = glow_surface(16, P["fire_mid"], 0.6)
            _blit_faded(surface, g, px, py, 130, additive=True)
        # badan molotov: botol kuningan berputar (ellipse sumbu spin)
        ca = abs(math.cos(self.rotation))
        bw = max(2, int(6 * ca) + 2)
        pygame.draw.ellipse(surface, (*P["outline"], 200),
                            (px - bw + 1, py - 5 + 1, bw * 2, 10))
        pygame.draw.ellipse(surface, P["brass"],
                            (px - bw, py - 5, bw * 2, 10))
        pygame.draw.ellipse(surface, P["brass"],
                            (px - bw + 1, py - 4, max(1, bw * 2 - 2), 8))
        pygame.draw.ellipse(surface, P["brass_hot"],
                            (px - bw + 1, py - 4,
                             max(1, bw * 2 - 3), 4))
        ga = self.rotation * 1.7
        gx = px + int(math.cos(ga) * max(0, bw - 1))
        gy = py - 2 + int(math.sin(ga) * 2)
        pygame.draw.circle(surface, P["brass_hot"], (gx, gy), 1)
        # sumbu menyala di ekor botol (arah berlawanan gerak)
        dxn = self._end.x - self._start.x
        dyn = self._end.y - self._start.y
        dd = math.hypot(dxn, dyn) or 1.0
        wx = px - int(dxn / dd * 8)
        wy = py - int(dyn / dd * 8) - 2
        pygame.draw.circle(surface, (*P["fire_bright"], 240), (wx, wy), 3)
        pygame.draw.circle(surface, (*P["fire_hot"], 255), (wx, wy), 2)
        pygame.draw.circle(surface, (*P["fire_white"], 255), (wx, wy - 1), 1)
        for i in range(3):
            angle = self.rotation + i * math.tau / 3
            fx = px + int(math.cos(angle) * 6)
            fy = py + int(math.sin(angle) * 4)
            pygame.draw.circle(surface, (*P["fire_bright"], 200),
                               (fx, fy), 2)
            pygame.draw.circle(surface, (*P["fire_hot"], 230),
                               (fx, fy - 1), 1)

    def draw_impact(self, surface):
        """Flash kecil pada frame HIT (impact penuh via on_impact)."""
        if not self.active and self.state != self.STATE_DESTROY:
            return
        x, y = int(self._hit_pos.x), int(self._hit_pos.y)
        s = spark_surface(10, P["fire_hot"])
        _blit_faded(surface, s, x, y, 220, additive=True)


class ProjectileSystem:
    """Manajer proyektil visual: cap keras + auto-cleanup."""

    def __init__(self, particles=None, cap=MAX_PROJECTILES):
        self.particles = particles
        self.cap = max(1, int(cap))
        self.projectiles = []

    def count(self):
        return len(self.projectiles)

    def list(self):
        return self.projectiles

    def clear(self):
        self.projectiles = []

    def spawn(self, x, y, tx, ty, **kw):
        if len(self.projectiles) >= self.cap:
            if self.projectiles:
                self.projectiles.pop(0)
        kw.setdefault("particles", self.particles)
        pr = RazakProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    def update(self, dt):
        if not self.projectiles:
            return
        alive = []
        for pr in self.projectiles:
            if pr.active:
                if pr.update(dt):
                    alive.append(pr)
        self.projectiles = alive

    def draw(self, surface):
        for pr in self.projectiles:
            pr.draw(surface)


# ============================================================================
# 8.  SKILL FX  —  Q/W/E/R dengan lifecycle bertahap
# ============================================================================

class SkillFX:
    """Efek skill Razak dengan lifecycle bertahap.

    CAST -> CHARGE -> RELEASE -> TRAVEL/AREA -> IMPACT -> AFTER -> FADE

    Yang digambar di sini adalah bagian yang TIDAK boleh ikut ter-cache.
    Cincin telegraph geometris (Q 75 / W 95 / E 80 / R 180 px dunia)
    tetap milik renderer, jadi tidak ada satu pun bentuk ganda.
    """

    #: (charge, release, area, impact, after) dalam DETIK
    TIMELINE = {
        "q": (0.16, 0.12, 0.26, 0.12, 0.30),
        "w": (0.14, 0.12, 0.30, 0.14, 0.30),
        "e": (0.20, 0.10, 0.30, 0.12, 0.18),
        "r": (0.40, 0.22, 0.52, 0.24, 0.47),
    }

    TINT = {
        "q": (P["fire_dark"], P["fire_hot"]),      # Sticky Napalm
        "w": (P["fire_dark"], P["fire_bright"]),   # Flamebreak
        "e": (P["fire_mid"], P["fire_hot"]),       # Firefly
        "r": (P["fire_dark"], P["fire_glow"]),     # Firestorm
    }

    RADIUS = WORLD_RADIUS

    def __init__(self, kind, x, y, particles=None, radius=None,
                 aim=(0.0, 0.0), ground=0.0, facing=1, scale=1.0):
        self.kind = kind if kind in self.TIMELINE else "q"
        self.x = float(x)
        self.y = float(y)
        self.particles = particles
        self.radius = float(radius if radius is not None
                            else self.RADIUS.get(self.kind, 60.0))
        self.aim = (float(aim[0]) - x, float(aim[1]) - y)
        self.ground = float(ground)
        self.facing = 1 if (facing or 1) >= 0 else -1
        self.scale = max(0.05, min(2.0, float(scale)))
        tl = self.TIMELINE[self.kind]
        self.t_charge = tl[0]
        self.t_release = self.t_charge + tl[1]
        self.t_area = self.t_release + tl[2]
        self.t_impact = self.t_area + tl[3]
        self.total = min(self.t_impact + tl[4],
                         float(SKILL_TOTAL.get(self.kind, 1.2)))
        self.age = 0.0
        self.active = True
        self.phase = "cast"
        self._released = False
        self._impacted = False
        self._emit = 0.0
        self.seed = random.randint(0, 999999)

    # ------------------------------------------------------------------
    @property
    def aim_angle(self):
        ax, ay = self.aim
        if abs(ax) < 0.01 and abs(ay) < 0.01:
            return 0.0
        return math.atan2(ay, ax)

    def impacted(self, x=None, y=None):
        """Tandai IMPACT (panggil dari gameplay/impact handler)."""
        if x is not None and y is not None:
            self.x = float(x)
            self.y = float(y)
        self._impacted = True
        if self.age > self.t_impact:
            self.age = self.t_impact

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
            return False
        ps = self.particles
        if ps is None:
            return True
        kind = self.kind
        R = self.radius
        ang = self.aim_angle
        dark, hot = self.TINT[kind]

        # CHARGE: bara tersedot ke titik ini (bukan berputar tanpa arah)
        if self.phase == "charge" and kind != "e":
            self._emit += dt
            gap = 0.05 if kind != "r" else 0.03
            while self._emit >= gap:
                self._emit -= gap
                a = random.random() * math.tau
                rr = R * random.uniform(0.5, 1.0)
                sx = self.x + math.cos(a) * rr
                sy = self.y + math.sin(a) * rr * 0.4 + self.ground * 0.55
                life = random.uniform(0.22, 0.4)
                ps.spawn(sx, sy,
                         (self.x - sx) / life * 0.8,
                         (self.y + self.ground * 0.4 - sy) / life * 0.7,
                         life, random.uniform(1.5, 3.0), hot,
                         color_end=dark, drag=0.4, shape="ember",
                         additive=True, fade_pow=0.8, layer="back")

        # RELEASE: semburan keluar / debu (satu kali)
        elif self.phase == "release" and not self._released:
            self._released = True
            if kind == "q":
                ps.burst(self.x, self.y, 10,
                         speed=(100, 300), life=(0.16, 0.36), size=(2, 4),
                         colors=(P["fire_white"], hot, P["fire_hot"]),
                         spread=1.2, direction=ang, drag=3.4,
                         shape="streak", additive=True)
            elif kind == "w":
                ps.burst(self.x + math.cos(ang) * 6,
                         self.y + math.sin(ang) * 6, 12,
                         speed=(160, 380), life=(0.18, 0.4), size=(2, 4),
                         colors=(P["fire_white"], hot, P["fire_glow"]),
                         spread=0.9, direction=ang, drag=3.0,
                         shape="streak", additive=True)
            else:
                ps.burst(self.x, self.y + self.ground * 0.5, 14,
                         speed=(110, 320), life=(0.24, 0.52), size=(2, 5),
                         colors=(hot, P["fire_bright"], P["dust"]),
                         spread=math.tau, gravity=200.0, drag=1.6,
                         shape="fire", layer="back")

        # AREA: bara naik di sepanjang ring (steady phase)
        elif self.phase in ("area", "impact") and kind != "e":
            self._emit += dt
            gap = 0.07 if kind != "r" else 0.028
            while self._emit >= gap:
                self._emit -= gap
                a = random.random() * math.tau
                rr = R * random.uniform(0.22, 1.0)
                ps.spawn(self.x + math.cos(a) * rr,
                         self.y + self.ground + math.sin(a) * rr * 0.3,
                         random.uniform(-18, 18), random.uniform(-60, -24),
                         random.uniform(0.4, 0.85), random.uniform(1, 3),
                         hot, color_end=P["smoke"], drag=0.5,
                         shape="ember", additive=True)
                if kind == "r" and _hash01(self.seed + int(a * 97)) > 0.6:
                    ps.spawn(self.x + math.cos(a) * rr,
                             self.y + self.ground,
                             random.uniform(-30, 30),
                             random.uniform(-90, -40),
                             random.uniform(0.4, 0.8), 2,
                             P["fire_white"], color_end=P["fire_dark"],
                             drag=0.3, shape="ember", additive=True)

        # IMPACT: serpihan jatuh + debu (satu kali)
        elif self.phase == "impact" and not self._impacted:
            self._impacted = True
            ps.burst(self.x, self.y + self.ground * 0.4, 10,
                     speed=(90, 250), life=(0.3, 0.6), size=(2, 5),
                     colors=(hot, P["brass"], P["dust"]),
                     gravity=430.0, drag=1.0, shape="shard",
                     rotation_speed=(-13.0, 13.0))
            ps.burst(self.x, self.y + self.ground, 8,
                     speed=(40, 140), life=(0.4, 0.9), size=(2, 6),
                     colors=(P["smoke"], P["ash"], dark),
                     gravity=-40.0, drag=1.4, shape="smoke", layer="back")
        return True

    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        """Lapisan BAWAH karakter: kabut tanah, gelombang tekan, retakan."""
        if not self.active:
            return
        dark, hot = self.TINT[self.kind]
        a = self.age
        R = self.radius
        x = int(self.x)
        gy = int(self.y + self.ground)

        # kabut cahaya di tanah — kedalaman, bukan garis saja
        t_all = min(1.0, a / max(0.05, self.total))
        haze = int(R * (0.8 + 0.2 * math.sin(a * 4.2))) // 8 * 8
        power = 0.32 * (1.0 - abs(t_all - 0.35) * 1.5)
        if power > 0.02 and haze >= 8 and glow_allowed():
            hs = ground_glow_surface(haze, dark, power)
            surface.blit(hs, (x - hs.get_width() // 2,
                              gy - hs.get_height() // 2),
                         special_flags=pygame.BLEND_RGB_ADD)

        # gelombang tekan yang merambat keluar sepanjang area/impact
        if self.phase in ("release", "area", "impact"):
            span = max(0.001, self.t_impact - self.t_release)
            t = min(1.0, (a - self.t_release) / span)
            rr = int(self.ground_ring_radius(t))
            al = int(190 * (1.0 - t))
            if rr > 6 and al > 6:
                er = ellipse_ring_surface(rr, max(2, int(rr * 0.26)),
                                          max(1, int(4 * (1 - t)) + 1),
                                          hot, 0)
                er.set_alpha(al)
                surface.blit(er, (x - er.get_width() // 2,
                                  gy - er.get_height() // 2))
                if self.kind in ("e", "r"):
                    self._ground_cracks(surface, x, gy, R, hot,
                                        int(180 * (1.0 - t)), t)
            if self.kind == "q" and self.phase in ("area", "impact"):
                # kolam napalm: globs lengket di tanah
                for i in range(5):
                    gg = _hash01(self.seed + i * 23)
                    ox = int((gg - 0.5) * R * 1.2)
                    oy = int((_hash01(self.seed + i * 41) - 0.5) * R * 0.34)
                    pr = max(3, int(6 * (1.0 - t * 0.4)))
                    pygame.draw.ellipse(surface, (*P["fire_dark"], 190),
                                        (x + ox - pr, gy + oy - pr // 2,
                                         pr * 2, pr))
                    pygame.draw.ellipse(surface, (*P["fire_hot"], 210),
                                        (x + ox - pr + 1, gy + oy - pr // 2,
                                         pr * 2 - 2, pr - 1))
                    pygame.draw.ellipse(
                        surface, (*P["fire_glow"], 220),
                        (x + ox - pr // 2, gy + oy - pr // 3,
                         pr, pr // 2))

    def ground_ring_radius(self, t):
        """Radius gelombang tekan (px layar relatif) untuk umur fraksi t."""
        base = self.radius
        if self.kind in ("e", "r"):
            return base * (0.3 + 0.8 * t)
        return base * 1.5 * (0.3 + 0.8 * t)

    def _ground_cracks(self, surface, cx, cy, R, color, alpha, t):
        if alpha <= 6:
            return
        n = 6
        for i in range(n):
            base = _hash01(self.seed + i * 31) * math.tau
            length = R * (0.42 + _hash01(self.seed + i * 77) * 0.4) \
                * (0.7 + t)
            px, py = cx, cy
            ang = base
            for seg in range(3):
                ang += (_hash01(self.seed + i * 17 + seg) - 0.5) * 0.85
                nx = px + math.cos(ang) * (length / 3.0)
                ny = py + math.sin(ang) * (length / 3.0) * 0.34
                pygame.draw.line(surface, (*_clamp_color(color), alpha),
                                 (int(px), int(py)), (int(nx), int(ny)),
                                 max(1, 3 - seg))
                px, py = nx, ny

    # ------------------------------------------------------------------
    def draw_front(self, surface):
        """Lapisan ATAS karakter: pilar, kerucut api, globs, wisp."""
        if not self.active:
            return
        kind = self.kind
        x, y = int(self.x), int(self.y)
        a = self.age
        if kind == "q":
            self._draw_q(surface, x, y, a)
        elif kind == "w":
            self._draw_w(surface, x, y, a)
        elif kind == "e":
            self._draw_e(surface, x, y, a)
        else:
            self._draw_r(surface, x, y, a)

    # -- Q  Sticky Napalm: bola-bola lengket menyala + bara berdenyut ──
    def _draw_q(self, surface, x, y, a):
        R = self.radius
        t = min(1.0, a / max(0.001, self.total))
        pulse = 0.5 + 0.5 * math.sin(a * 6.0)
        if self.phase in ("area", "impact", "fade"):
            k = 1.0 if self.phase == "area" else (1.0 - t * 0.6)
            for i in range(6):
                gg = _hash01(self.seed + i * 13)
                ox = int((gg - 0.5) * R * 1.1)
                oy = int((_hash01(self.seed + i * 29) - 0.5) * R * 0.5)
                r = max(2, int((5 + 3 * pulse) * k))
                col = P["fire_bright"] if i % 2 else P["fire_hot"]
                if glow_allowed():
                    g = glow_surface(r * 3, col, 0.45 * k)
                    _blit_faded(surface, g, x + ox, y + oy - 4,
                                int(120 * k), additive=True)
                pygame.draw.circle(surface, (*P["fire_dark"], 200),
                                   (x + ox, y + oy), r + 1)
                pygame.draw.circle(surface, (*col, 230),
                                   (x + ox, y + oy - 1), r)
                pygame.draw.circle(surface,
                                   (*P["fire_white"], 240),
                                   (x + ox, y + oy - 2), max(1, r - 1))
        elif self.phase == "charge":
            # bola api kecil menyala di tangan sebelum lempar (muzzle)
            r = int(6 + 4 * (a / max(0.001, self.t_charge)))
            if glow_allowed():
                g = glow_surface(r * 4, P["fire_hot"], 0.7)
                _blit_faded(surface, g, x, y - 4, 150, additive=True)
            pygame.draw.circle(surface, (*P["fire_mid"], 230), (x, y), r)
            pygame.draw.circle(surface, (*P["fire_hot"], 255),
                               (x, y), max(1, r - 1))
            pygame.draw.circle(surface, (*P["fire_white"], 255),
                               (x, y - 1), 1)

    # -- W  Flamebreak: kerucut api 3 band dari moncong ke target ─────
    def _draw_w(self, surface, x, y, a):
        ang = self.aim_angle
        R = self.radius
        if self.phase in ("charge", "release"):
            mint = min(1.0, a / max(0.001, self.t_release))
            length = int(R * 0.5 * mint if self.phase == "charge"
                         else R * (0.6 + 0.4 * (1.0 -
                                                (a - self.t_charge) /
                                                max(0.001,
                                                    self.t_release -
                                                    self.t_charge))))
            width = int(10 + 22 * mint)
            self._flame_cone(surface, x, y, ang, length, width,
                             int(230 * mint), a)
        elif self.phase in ("area", "impact"):
            fade = 1.0 if self.phase == "area" else (
                1.0 - (a - self.t_area) /
                max(0.001, self.t_impact - self.t_area))
            length = int(R * (0.95 + 0.25 * math.sin(a * 8)) * fade)
            width = int(26 + 14 * math.sin(a * 5))
            self._flame_cone(surface, x, y, ang, length, width,
                             int(210 * fade), a)
            # pusat ledakan di target — flash KOMPAK + percikan
            tx = float(self.x) + self.aim[0]
            ty = float(self.y) + self.aim[1]
            if glow_allowed():
                g = glow_surface(int(12 + 10 * fade), P["fire_hot"],
                                 0.5 * fade)
                _blit_faded(surface, g, int(tx), int(ty) - 4,
                            int(150 * fade), additive=True)
            pygame.draw.circle(surface, (*P["fire_white"], int(200 * fade)),
                               (int(tx), int(ty)), max(1, int(6 * fade)))
        else:
            self._flame_cone(surface, x, y, ang, int(R * 0.3),
                             int(8), int(120 * (1.0 - a / self.total)),
                             a)

    def _flame_cone(self, surface, x, y, ang, length, width, alpha, phase):
        if length <= 2 or alpha <= 4:
            return
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        for band, (col, k_len, k_w, k_al) in enumerate((
                (P["fire_dark"], 1.00, 1.00, 0.75),
                (P["fire_bright"], 0.82, 0.72, 0.95),
                (P["fire_hot"], 0.60, 0.48, 1.0),
                (P["fire_glow"], 0.34, 0.26, 1.0))):
            L = int(length * k_len)
            W = max(2, int(width * k_w))
            # lidah api: tepi bergerigi deterministik
            tips = []
            base = [(x + px * W, y + py * W),
                    (x + ca * L * 0.55 + px * W * 0.7,
                     y + sa * L * 0.55 + py * W * 0.7),
                    (x + ca * L + px * W * 0.2 + math.sin(phase * 9) * 2,
                     y + sa * L + py * W * 0.2),
                    (x + ca * L * 0.55 - px * W * 0.7,
                     y + sa * L * 0.55 - py * W * 0.7),
                    (x - px * W, y - py * W)]
            pts = [(int(a), int(b)) for a, b in tips] + \
                  [(int(a), int(b)) for a, b in base]
            col = _clamp_color(col)
            pygame.draw.polygon(surface, (*col, int(alpha * k_al)),
                                [(a, b) for a, b in pts])
            # ember sepanjang kerucut
            if band == 1:
                for i in range(3):
                    t = 0.2 + 0.25 * i
                    ex = x + ca * length * t + math.sin(phase * 7 + i) * 3
                    ey = y + sa * length * t + math.cos(phase * 6 + i) * 3
                    pygame.draw.circle(surface, (*P["fire_white"],
                                                 int(alpha * 0.8)),
                                       (int(ex), int(ey)), 1)

    # -- E  Firefly: cincin mendarat + jejak api yang memudar ─────────
    def _draw_e(self, surface, x, y, a):
        R = self.radius
        t = min(1.0, a / max(0.001, self.total))
        if self.phase in ("release", "area"):
            k = (1.0 if self.phase == "release"
                 else 1.0 - (a - self.t_release) /
                 max(0.001, self.t_area - self.t_release))
            # dashed ring berputar + ring konvergen
            for i in range(2):
                rr = int(R * (0.35 + 0.55 * (i + t)) * k)
                if rr > 6:
                    ring = ring_surface(rr, 2, P["fire_hot"], 255,
                                        dashed=8 + i * 5)
                    ring.set_alpha(int(200 * k))
                    surface.blit(ring, (x - ring.get_width() // 2,
                                        y + self.ground -
                                        ring.get_height() // 2))
            # jejak api memudar di sekitar caster
            for i in range(6):
                gg = _hash01(self.seed + i * 31)
                ox = int((gg - 0.5) * R * 1.2 * (1.2 - t))
                oy = int((_hash01(self.seed + i * 47) - 0.5) * 18)
                pygame.draw.circle(surface, (*P["fire_hot"], int(140 * k)),
                                   (x + ox, y + self.ground + oy), 2)
                pygame.draw.circle(surface,
                                   (*P["fire_white"], int(160 * k)),
                                   (x + ox, y + self.ground + oy - 1), 1)
        elif self.phase == "impact":
            # a dalam [t_area, t_impact): puncak di awal, pudar ke nol
            span = max(0.001, self.t_impact - self.t_area)
            k = min(1.0, max(0.0, 1.0 - (a - self.t_area) / span))
            if glow_allowed():
                g = glow_surface(int(14 * (0.5 + k)), P["fire_bright"],
                                 0.6 * k)
                _blit_faded(surface, g, x, y - 4, int(140 * k),
                            additive=True)
            pygame.draw.circle(surface, (*P["fire_white"],
                                         int(min(255, 200 * k))),
                               (x, y), max(1, int(6 * k)))

    # -- R  Firestorm: 8 pilar api mengorbit + wisp spiral ────────────
    def _draw_r(self, surface, x, y, a):
        R = self.radius
        pulse = 0.6 + 0.4 * math.sin(a * 7.0)
        if self.phase == "charge":
            # Pilar cahaya di pusat (diri Razak) DIBUANG: kolom 30-100 px
            # tepat di sumbu badan menutupi karakter saat R di-cast.
            return
        if self.phase in ("release", "area", "impact", "fade"):
            fade = max(0.0, 1.0 - (a - self.t_release) /
                       max(0.001, self.total - self.t_release))
            ring_r = R * 0.62
            # 8 pilar mengorbit di 0.62·R (sama dengan renderer v2).
            # Dipertahankan: posisinya di radius telegraph, BUKAN di atas
            # badan, jadi tidak menutupi karakter.
            for i in range(8):
                ang = a * 0.8 + i * math.tau / 8
                px = x + math.cos(ang) * ring_r
                py = y + self.ground + math.sin(ang) * ring_r * 0.4
                h = int((36 + 22 * pulse) * (0.7 + 0.3 * fade))
                self._pillar(surface, int(px), int(py), h,
                             max(3, int(10 + 4 * pulse)), fade)
            # Erupsi pusat DIBUANG (alasan sama dengan pilar charge):
            # kolom 60-90 px di (x, y-6) menelan badan Razak. Glow +
            # wisp spiral di bawah tetap hidup sebagai penanda erupsi.
            if glow_allowed():
                g = glow_surface(int(18 * fade + 8), P["fire_hot"],
                                 0.55 * fade)
                _blit_faded(surface, g, x, y - 8, int(150 * fade),
                            additive=True)
            # wisp spiral naik
            for i in range(4):
                ang = a * 1.4 + i * math.tau / 4
                wx = x + math.cos(ang) * (18 + 10 * ((a * 3) % 1))
                wy = y - 8 - int((a * 60) % 40)
                pygame.draw.circle(surface,
                                   (*P["fire_glow"], int(190 * fade)),
                                   (int(wx), int(wy)), 2)
                pygame.draw.circle(surface,
                                   (*P["fire_white"], int(200 * fade)),
                                   (int(wx), int(wy - 1)), 1)

    def _pillar(self, surface, cx, cy, height, width, alpha):
        """Pilar api ter-cache per bucket tinggi/lebar/alpha."""
        if height <= 2 or width <= 1 or alpha <= 0.03:
            return
        h = int(height // 6 * 6)
        w = max(2, int(width // 4 * 4))
        al = max(1, min(10, int(alpha * 10)))
        key = ("pillar", h, w, al)
        surf = _SURF_CACHE.get(key)
        if surf is None:
            size_h = h + 8
            size_w = w * 2 + 10
            surf = pygame.Surface((size_w, size_h), pygame.SRCALPHA)
            cx0, cy0 = size_w // 2, size_h - 4
            # lidah api 3 band: gelap lebar -> terang runcing
            for band, (col, k) in enumerate((
                    (P["fire_dark"], 1.0), (P["fire_bright"], 0.72),
                    (P["fire_hot"], 0.46), (P["fire_glow"], 0.22))):
                ww = max(1, int(w * k))
                pts = [(cx0 - ww, cy0), (cx0 - ww // 2, cy0 - h // 2),
                       (cx0, cy0 - h), (cx0 + ww // 2, cy0 - h // 2),
                       (cx0 + ww, cy0)]
                pygame.draw.polygon(surf,
                                    (*_clamp_color(col),
                                     int(210 * (1.0 - band * 0.12))), pts)
                # lidah sekunder bergerigi
                if band == 1:
                    pygame.draw.polygon(surf,
                                        (*_clamp_color(P["fire_white"]),
                                         160),
                                        [(cx0 - ww // 3, cy0 - h // 3),
                                         (cx0, cy0 - int(h * 0.62)),
                                         (cx0 + ww // 3, cy0 - h // 3)])
            surf = _cache_put(key, surf)
        surf.set_alpha(int(255 * max(0.05, min(1.0, alpha * 1.5))))
        surface.blit(surf, (cx - surf.get_width() // 2,
                            cy - surf.get_height() + 4))
        surf.set_alpha(255)


# ============================================================================
# 9.  CONTROLLER ANIMASI  —  fase bernama + prioritas state
# ============================================================================

#: Prioritas state (angka besar = lebih penting; DEATH mengunci).
ANIM_PRIORITY = {
    "IDLE": 10, "WALK": 20, "RUN": 25, "CHARGE": 40,
    "ATTACK": 45, "SWING": 50, "CAST": 55, "SKILL": 56,
    "SPECIAL": 60, "HIT": 62, "HURT": 65, "DEATH": 100,
}

#: Fase timeline serangan (fraksi 0..1) — disinkronkan dari renderer.
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.09),
    ("WINDUP",       0.09, 0.30),
    ("SWING",        0.30, 0.50),
    ("IMPACT",       0.50, 0.62),
    ("FOLLOW",       0.62, 0.80),
    ("RECOVERY",     0.80, 1.00),
)
ATTACK_SWING_END = 0.62


def attack_phase(progress):
    """Kembalikan nama fase serangan untuk progress 0..1."""
    p = max(0.0, min(1.0, float(progress)))
    for name, a, b in ATTACK_PHASES:
        if a <= p < b:
            return name
    return "RECOVERY"


def _resolve_timeline():
    """Tarik timeline fase dari renderer kalau tersedia."""
    global ATTACK_PHASES, ATTACK_SWING_END
    G = _renderer()
    if G is None:
        return
    phases = getattr(G, "ATTACK_PHASES", None)
    if isinstance(phases, tuple) and len(phases) == 6:
        ATTACK_PHASES = phases
    swing_end = getattr(G, "ATTACK_SWING_END", None)
    if swing_end is not None:
        try:
            ATTACK_SWING_END = float(swing_end)
        except (TypeError, ValueError):
            pass


_resolve_timeline()


# ============================================================================
# 10.  DIRECTOR  —  satu per unit Razak
# ============================================================================

class RazakFXDirector:
    """Mengikat particle + trail + proyektil + impact + skill FX untuk
    satu unit Razak (mini boss — kodenya sama untuk jalur hero)."""

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
        self._proj_window_seen = False
        self._skill_release = {}
        self._impact_dedupe = {}       # kind -> (x, y, time)
        self._dash_landed = False

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def _ground_dy(self):
        return _ground_dy(self.hero)

    def on_swing_start(self, x, y, facing):
        """Awal ayunan: trail reset + debu antisipasi di bawah bat."""
        self.trail.reset()
        self.trail.width_boost = 1.0
        self.swing_active = True
        gy = y + self._ground_dy()
        self.particles.burst(
            x + facing * 4, gy, 5,
            speed=(26, 86), life=(0.16, 0.36), size=(2, 4),
            colors=(P["dust"], P["ash"], P["smoke"]),
            spread=1.2, direction=math.pi if facing > 0 else 0.0,
            gravity=100.0, drag=2.6, shape="dust", layer="back")

    def on_swing_end(self):
        self.swing_active = False

    def on_swing_impact_frame(self, x, y, facing):
        """Sapu udara di frame IMPACT — feedback walau tidak kena apa-apa."""
        grip, tip = machete_points(self.hero, x, y)
        ang = math.atan2(tip.y - grip.y, tip.x - grip.x)
        self.particles.burst(
            tip.x, tip.y, 8,
            speed=(120, 280), life=(0.1, 0.26), size=(1, 3),
            colors=(P["fire_hot"], P["fire_white"], P["fire_glow"]),
            spread=1.6, direction=ang, drag=3.6, shape="streak",
            additive=True)
        self.particles.burst(
            tip.x, tip.y, 4,
            speed=(60, 160), life=(0.14, 0.3), size=(1, 2),
            colors=(P["fire_bright"], P["fire_hot"]),
            spread=math.tau, drag=2.4, shape="ember", additive=True)
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(tip.x, tip.y, ang, 0.6, False,
                                     kind="slash", seed=int(self.frames)))

    # ------------------------------------------------------------------
    def spawn_napalm(self, x, y, tx, ty):
        """Lempar molotov dari posisi layar (x, y) ke target (tx, ty)."""
        tgt = getattr(self.hero, "target", None)
        if tgt is None or not getattr(tgt, "alive", False):
            tgt = None
        return self.projectiles.spawn(
            x, y, tx, ty, speed=NAPALM_SPEED, damage=0, target=tgt,
            radius=8.0, arc_height=NAPALM_ARC, kind="napalm",
            ground=self._ground_dy(),
            on_impact=lambda p: self._on_napalm_land(p))

    def _on_napalm_land(self, pr):
        """Molotov mendarat: impact + kolam lengket + shake + hit-stop."""
        hx, hy = pr._hit_pos.x, pr._hit_pos.y
        self._skill_dedupe_impact("q", hx, hy, 0.18)
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        self.skills.append(SkillFX(
            "q", hx, hy, self.particles, radius=WORLD_RADIUS["q"],
            ground=self._ground_dy(),
            scale=_rscale(self.hero)))
        self.on_impact(hx, hy, -math.pi / 2, 1.25, False, kind="napalm")
        self.particles.burst(
            hx, hy + self._ground_dy() * 0.4, 14,
            speed=(80, 260), life=(0.3, 0.7), size=(2, 5),
            colors=(P["fire_bright"], P["fire_hot"], P["fire_dark"]),
            spread=math.tau, gravity=330.0, drag=1.2, shape="fire")
        self.particles.burst(
            hx, hy + self._ground_dy() * 0.6, 10,
            speed=(30, 120), life=(0.5, 1.0), size=(2, 6),
            colors=(P["smoke"], P["ash"]), spread=math.tau,
            gravity=-40.0, drag=1.4, shape="smoke", layer="back")

    def on_cast(self, x, y, skill):
        """Skill dilepas: SkillFX + guncangan + (Q) lempar napalm."""
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        gy = self._ground_dy()
        aim = None
        tgt = getattr(self.hero, "target", None)
        if tgt is not None and getattr(tgt, "alive", False):
            aim = (float(tgt.x), float(tgt.y))
        facing = 1 if getattr(self.hero, "direction", 1) >= 0 else -1
        if aim is None:
            aim = (x + facing * 120, y + gy * 0.5)
        gun = gun_end(self.hero, x, y)

        if skill == "q":
            # lempar molotov dari moncong flamethrower
            self.particles.burst(
                gun.x, gun.y, 8,
                speed=(80, 240), life=(0.1, 0.24), size=(1, 3),
                colors=(P["fire_white"], P["fire_hot"], P["fire_bright"]),
                spread=1.4, direction=math.atan2(
                    gun.y - y, gun.x - x), drag=3.0,
                shape="streak", additive=True)
            self.spawn_napalm(gun.x, gun.y, aim[0], aim[1])
        elif skill == "w":
            self.skills.append(SkillFX(
                "w", gun.x, gun.y, self.particles, aim=aim,
                ground=gy, facing=facing, scale=_rscale(self.hero)))
        elif skill == "e":
            # Firefly: efek menyala di titik asal sebelum dash
            self.skills.append(SkillFX(
                "e", x, y, self.particles, ground=gy,
                facing=facing, scale=_rscale(self.hero)))
        elif skill == "r":
            self.skills.append(SkillFX(
                "r", x, y, self.particles, ground=gy,
                facing=facing, scale=_rscale(self.hero)))

        if shake_allowed():
            _feel_shake(5.0 if skill != "r" else 12.0,
                        0.16 if skill != "r" else 0.38)
        self.particles.burst(
            x, y + gy * 0.35, 12,
            speed=(60, 200), life=(0.2, 0.5), size=(2, 4),
            colors=(P["fire_mid"], P["dust"], P["ash"]),
            spread=math.tau, gravity=150.0, drag=2.0,
            shape="fire", layer="back")
        if skill == "r":
            _feel_hit_stop(0.06)

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="slash"):
        """Benturan mengenai target: flash, spark, debris, shake, hit-stop."""
        if self._skill_dedupe_impact(kind, x, y, 0.16):
            return
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind=kind,
                                     ground=self._ground_dy(),
                                     seed=int(self.frames)))
        pw = min(2.0, max(0.35, float(power)))

        hot = P["fire_hot"] if kind != "hurt" else P["blue_hot"]
        bright = P["fire_white"] if kind != "hurt" else P["blue"]
        n = int(9 + 7 * pw) + (6 if crit else 0)
        self.particles.burst(
            x, y, n, speed=(120, 340 + 90 * pw), life=(0.14, 0.4),
            size=(2, 4), colors=(hot, bright, P["fire_bright"]),
            spread=2.4, direction=angle, drag=3.6, shape="streak")
        self.particles.burst(
            x, y, int(5 + 3 * pw) + (4 if crit else 0),
            speed=(70, 210), life=(0.28, 0.6), size=(2, 5),
            colors=(P["fire_bright"], P["ash"], P["brass"]),
            gravity=470.0, drag=1.1, shape="shard",
            rotation_speed=(-16.0, 16.0))
        self.particles.burst(
            x, y + self._ground_dy() * 0.4, 6,
            speed=(40, 140), life=(0.3, 0.66), size=(2, 6),
            colors=(P["smoke"], P["ash"]), spread=math.tau,
            gravity=-30.0, drag=1.4, shape="smoke", layer="back")
        if crit:
            self.particles.burst(
                x, y, 8, speed=(180, 380), life=(0.2, 0.5), size=(2, 4),
                colors=(P["brass_hot"], P["brass"], hot),
                spread=math.tau, gravity=120.0, drag=2.0, shape="spark",
                additive=True)

        if shake_allowed():
            _feel_shake(4.0 + 3.4 * pw + (3.0 if crit else 0.0),
                        0.17 + 0.08 * pw)
        _feel_hit_stop(0.036 + 0.019 * min(1.5, pw) +
                       (0.014 if crit else 0.0))

    def on_hurt(self, amount=1.0):
        """Razak terkena serangan: flash + percikan api + debu sayap."""
        self.hit_flash = 0.16
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        self.particles.burst(
            hx, hy - 8, 7, speed=(80, 210), life=(0.14, 0.3), size=(2, 4),
            colors=(P["blue_hot"], P["fire_hot"], P["leather"]),
            drag=3.0, shape="spark", additive=True)
        self.particles.burst(
            hx, hy + 6, 5, speed=(30, 100), life=(0.22, 0.5), size=(2, 6),
            colors=(P["bat_dark"], P["smoke"], P["leather"]),
            gravity=200.0, drag=2.0, shape="dust", layer="back")

    def on_dash_land(self, x, y):
        """Firefly mendarat: cincin + bara + debu (sekali per dash)."""
        if self._dash_landed:
            return
        self._dash_landed = True
        gy = self._ground_dy()
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        self.skills.append(SkillFX("e", x, y, self.particles, ground=gy,
                                   scale=_rscale(self.hero)))
        self.on_impact(x, y, 0.0, 1.1, False, kind="dash")
        self.particles.burst(
            x, y + gy * 0.55, 12,
            speed=(90, 250), life=(0.2, 0.5), size=(2, 5),
            colors=(P["fire_bright"], P["fire_hot"], P["dust"]),
            spread=math.tau, gravity=230.0, drag=1.8,
            shape="fire", layer="back")

    def on_death(self, x, y):
        """Kematian: api padam, asap & debu naik sekali."""
        if self._death_done:
            return
        self._death_done = True
        gy = self._ground_dy()
        self.trail.reset()
        self.particles.clear()
        self.impacts.append(ImpactFX(x, y + gy * 0.3, -math.pi / 2, 2.2,
                                     True, kind="storm", seed=7,
                                     ground=gy))
        self.particles.burst(x, y, 22, speed=(90, 330), life=(0.5, 1.1),
                             size=(2, 6),
                             colors=(P["fire_bright"], P["bat_mid"],
                                     P["brass"], P["leather"]),
                             spread=math.tau, gravity=430.0, drag=1.1,
                             shape="shard", rotation_speed=(-18.0, 18.0))
        self.particles.burst(x, y + gy, 18, speed=(40, 150),
                             life=(0.5, 1.0), size=(3, 7),
                             colors=(P["dust"], P["smoke"], P["ash"]),
                             spread=math.tau, gravity=-30.0, drag=1.5,
                             shape="smoke", layer="back")
        if shake_allowed():
            _feel_shake(9.0, 0.42)

    # ------------------------------------------------------------------
    def _skill_dedupe_impact(self, kind, x, y, window):
        """Hindari FX impact ganda untuk skill AOE/landing yang sama."""
        key = kind
        last = self._impact_dedupe.get(key)
        now = self.time
        if last is not None:
            (lx, ly, lt) = last
            if now - lt <= window and math.hypot(x - lx, y - ly) < 14.0:
                self._impact_dedupe[key] = (x, y, now)
                return True
        self._impact_dedupe[key] = (x, y, now)
        return False

    # ------------------------------------------------------------------
    def _watch_engine_events(self, x, y):
        """Reaksi terhadap state yang DITULIS engine, tanpa mengubahnya.

        Lapisan ini satu arah: hanya membaca field yang sudah ada di
        Boss (active_skill, active_skill_timer, _razak_proj_spawned, x/y)
        sehingga tidak ada jalur yang bisa merusak damage/cooldown.
        """
        h = self.hero
        skill = getattr(h, "active_skill", None)
        timer = int(getattr(h, "active_skill_timer", 0) or 0)

        # ── Q (basic attack): jendela lempar — renderer memicu timing,
        #    lapisan hidup yang melempar di koordinat layar (1:1).
        window = bool(getattr(h, "_razak_live_proj_window", False))
        if window and not self._proj_window_seen:
            self._proj_window_seen = True
            tgt = getattr(h, "target", None)
            if tgt is not None and getattr(tgt, "alive", False):
                # Lapisan hidup digambar 1:1 di layar: koordinat target
                # DUNIA sudah merupakan koordinat layar. Membagi dengan
                # `_render_scale` (formula canvas renderer) membuat molotov
                # melewati target -> FX terlihat mendarat acak di peta.
                tx = x + (float(tgt.x) - float(getattr(h, "x", x)))
                ty = y + (float(tgt.y) - float(getattr(h, "y", y)))
            else:
                fl = 1 if getattr(h, "direction", 1) >= 0 else -1
                tx, ty = x + fl * 140, y + 18
            # posisi lempar: moncong flamethrower (pose nyata)
            gx, gy = gun_end(h, x, y)
            self.spawn_napalm(gx, gy, float(tx), float(ty))
        elif not window:
            self._proj_window_seen = False
        h._razak_live_proj_window = False  # konsumsi (edge)

        # ── W: rilis kerucut api di 55% durasi (momen damage AOE) ───
        if skill == "w" and timer:
            dur = max(1, int(SKILL_DUR.get("w", 50)))
            release_at = int(dur * 0.55)
            prev = self._skill_release.get("w")
            if prev != release_at and timer <= release_at:
                self._skill_release["w"] = release_at
                d = self._skill_for("w")
                if d is not None:
                    d.impacted()
        elif skill != "w":
            self._skill_release.pop("w", None)

        # ── R: erupsi di 35% durasi ─────────────────────────────────
        if skill == "r" and timer:
            dur = max(1, int(SKILL_DUR.get("r", 90)))
            release_at = int(dur * 0.35)
            prev = self._skill_release.get("r")
            if prev != release_at and timer <= release_at:
                self._skill_release["r"] = release_at
                d = self._skill_for("r")
                if d is not None:
                    d.impacted()
        elif skill != "r":
            self._skill_release.pop("r", None)

        # ── E: lompatan dash > 24 px dalam satu frame → mendarat ────
        jump = math.hypot(x - self.last_x, y - self.last_y)
        if jump > 24.0 and skill == "e":
            self.on_dash_land(x, y)
        elif skill != "e":
            self._dash_landed = False

    def _skill_for(self, kind):
        for s in self.skills:
            if s.kind == kind and s.active and s.phase != "fade":
                return s
        return None

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------
    def _resolve_state(self):
        """State yang DIINGINKAN frame ini, dari controller renderer."""
        h = self.hero
        if not getattr(h, "alive", True):
            return "DEATH"
        if self.hit_flash > 0.0:
            return "HURT"
        skill = getattr(h, "active_skill", None)
        if skill:
            return "SPECIAL" if skill == "r" else "SKILL"
        action, _phase, ap = pose_of(h)
        if action == "attack":
            ph = attack_phase(ap)
            if ph in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            if ph in ("SWING", "IMPACT"):
                return "SWING"
            return "ATTACK"
        if action == "walk":
            return "RUN" if float(getattr(h, "speed", 1.0)) >= 2.2 else "WALK"
        return "IDLE"

    def _update_state(self, dt):
        want = self._resolve_state()
        if want != self.state:
            cur_p = ANIM_PRIORITY.get(self.state, 0)
            new_p = ANIM_PRIORITY.get(want, 0)
            if self.state != "DEATH" and (new_p >= cur_p
                                          or self.state_time > 0.05):
                self.prev_state = self.state
                self.state = want
                self.state_time = 0.0
        self.state_time += dt
        self.anim_phase = str(getattr(self.hero, "_razak_attack_phase",
                                      None) or "NONE")

    # ------------------------------------------------------------------
    def update(self, dt, x, y):
        """Satu langkah simulasi FX. ``x, y`` = posisi layar unit."""
        if dt <= 0.0:
            return
        self.time += dt
        self.frames += 1
        h = self.hero

        # ── damage masuk -> HURT ─────────────────────────────────────
        hp = getattr(h, "hp", None)
        if hp is not None:
            if self._last_hp is not None and hp < self._last_hp - 0.01:
                self.on_hurt((self._last_hp - hp)
                             / max(1.0, float(getattr(h, "max_hp", 1.0))))
            self._last_hp = hp
        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)

        self._update_state(dt)
        self._watch_engine_events(x, y)
        if self.state == "DEATH":
            self.on_death(x, y)

        # ── cast skill (edge-triggered) ──────────────────────────────
        skill = getattr(h, "active_skill", None)
        if skill != self._skill_seen:
            if skill:
                self.on_cast(x, y, skill)
            self._skill_seen = skill

        # ── ayunan: deteksi fase, rekam trail ────────────────────────
        facing = 1 if getattr(h, "direction", 1) >= 0 else -1
        action, _phase, ap = pose_of(h)
        attacking = action == "attack"
        ph = attack_phase(ap)
        swinging = attacking and ph in ("SWING", "IMPACT", "FOLLOW")
        if swinging and not self._swing_seen:
            self.on_swing_start(x, y, facing)
        elif not swinging and self._swing_seen:
            self.on_swing_end()
        self._swing_seen = swinging

        impact_frame = attacking and ph == "IMPACT"
        if impact_frame and not self._impact_frame_seen:
            self._impact_frame_seen = True
            self.on_swing_impact_frame(x, y, facing)
        elif not impact_frame:
            self._impact_frame_seen = False

        if swinging:
            grip, tip = machete_points(h, x, y)
            self.trail.push(grip, tip)

        self.last_x = x
        self.last_y = y

        self.trail.update(dt)
        self.particles.update(dt)
        self.projectiles.update(dt)
        if self.impacts:
            self.impacts = [i for i in self.impacts if i.update(dt)]
        if self.skills:
            self.skills = [s for s in self.skills if s.update(dt)]

    # ------------------------------------------------------------------
    # Draw
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
        """IMPACT FLASH: glow api kecil + kilat di dada — BUKAN white-out.

        Versi lama menambahkan cakram PUTIH radius ~76 px (fire_white,
        alpha 120 tapi di-blit ``BLEND_RGB_ADD`` yang mengabaikan alpha)
        tepat di atas badan: ~84% siluet Razak berubah jadi blob putih
        SETIAP kali kena damage, dan karena efeknya ter-retrigger tiap
        tick damah/DoT, Razak praktis "dibungkus cahaya" sepanjang baku
        hantam. Cakram itu dibuang; sinyal benturan tetap terbaca lewat
        glow hangat kecil + kilat bintang di dada.
        """
        k = max(0.0, min(1.0, self.hit_flash / 0.16))
        # Lane boss juga menggambar flash siluet sendiri (hurt_flash_timer
        # -> _flash_buf di bosses/level2.py); dua flash penuh di frame yang
        # sama terbaca sebagai white-out, jadi bagian ini diredam di sana.
        if int(getattr(self.hero, "hurt_flash_timer", 0) or 0) > 0:
            k *= 0.35
        if k <= 0.02:
            return
        r = int(16 + 14 * k)
        if glow_allowed():
            g = glow_surface(r, P["fire_hot"], 0.5 * k)
            _blit_faded(surface, g, int(x), int(y) - 8, int(220 * k),
                        additive=True)
        s = max(3, int(4 + 8 * k))
        star = spark_surface(s, P["fire_white"])
        star.set_alpha(int(165 * k))
        surface.blit(star, (int(x) - s, int(y) - 16 - s))
        star.set_alpha(255)

    # ------------------------------------------------------------------
    def clear(self):
        """Kosongkan semua state FX unit ini (anti efek abadi)."""
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
        self._proj_window_seen = False
        self._skill_release.clear()
        self._impact_dedupe.clear()
        self._dash_landed = False

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
            "trail": len(self.trail.samples),
            "cache": cache_size(),
        }


# ============================================================================
# 11.  ADAPTER FU  dan BUS GAME-FEEL
# ============================================================================

def _rscale(boss):
    """Skala render pipeline untuk FX world-space (jalur boss = 1.0)."""
    return render_scale(boss)


def _ground_dy(boss):
    """Jarak anchor -> garis tanah, dalam piksel layar."""
    G = _renderer()
    dy = getattr(G, "GROUND_DY", 52) if G is not None else 52
    return int(round(float(dy) * render_scale(boss)))


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
    """True kalau Game.update harus membekukan langkah simulasi."""
    if _feel is None:                          # pragma: no cover
        return False
    return _feel.should_freeze_frame()


def hit_stop(seconds=0.045):
    """Minta hit-stop global (dijepit 0.03-0.08 s oleh bus)."""
    _feel_hit_stop(seconds)


def shake(strength=5.0, duration=0.22):
    """Goyangkan layar lewat bus bersama (trauma decay + kamera resmi)."""
    _feel_shake(strength, duration)


# ============================================================================
# 12.  OVERLAY DEBUG
# ============================================================================

_DEBUG_FONT = None


def _debug_font():
    global _DEBUG_FONT
    if _DEBUG_FONT is None:
        try:
            _DEBUG_FONT = pygame.font.Font(None, 15)
        except Exception:                      # pragma: no cover
            _DEBUG_FONT = False
    return _DEBUG_FONT or None


def draw_debug_overlay(surface, director):
    """Hitbox, hurtbox, jangkauan, tumbukan proyektil, state, frame, FPS."""
    h = director.hero
    x = int(getattr(h, "x", 0))
    y = int(getattr(h, "y", 0))
    rad = int(getattr(h, "radius", 16))
    rng = int(getattr(h, "range", 60)) or 60

    # jangkauan serangan
    pygame.draw.circle(surface, (255, 180, 60), (x, y), rng, 1)
    # hurtbox
    pygame.draw.circle(surface, (90, 220, 255), (x, y), rad, 1)
    # hitbox ayunan (jendela hit aktif saja)
    G = _renderer()
    hitbox = None
    if G is not None:
        try:
            hitbox = G._swing_hitbox(h, x, y)
        except Exception:                      # pragma: no cover
            hitbox = None
    if hitbox is not None:
        pygame.draw.rect(surface, (255, 230, 90), hitbox, 1)
    # tumbukan proyektil
    for pr in director.projectiles.projectiles:
        pygame.draw.circle(surface, (255, 255, 120),
                           (int(pr.position.x), int(pr.position.y)),
                           int(pr.radius), 1)
        pygame.draw.line(surface, (255, 255, 120),
                         (int(pr.position.x), int(pr.position.y)),
                         (int(pr._hit_pos.x), int(pr._hit_pos.y)), 1)
    # jangkar bilah (sumber bentuk trail)
    grip, tip = machete_points(h, x, y)
    pygame.draw.line(surface, (120, 255, 200), (int(grip.x), int(grip.y)),
                     (int(tip.x), int(tip.y)), 1)

    font = _debug_font()
    if font is None:
        return
    try:
        fps = int(pygame.time.Clock().get_fps())
    except Exception:                          # pragma: no cover
        fps = 0
    st = director.stats()
    hs = _feel.HITSTOP if _feel is not None else None
    lines = [
        "RAZAK %s / %s" % (st["state"], st["phase"]),
        "frame %d  prog %.2f  atkT %d" % (
            int(getattr(h, "_razak_attack_frame", 0)),
            float(getattr(h, "_razak_attack_progress", 0.0) or 0.0),
            int(getattr(h, "timer", 0) or 0)),
        "skill %s t=%d" % (getattr(h, "active_skill", None),
                           int(getattr(h, "active_skill_timer", 0) or 0)),
        "part %d  proj %d  imp %d  sk %d" % (
            st["particles"], st["projectiles"], st["impacts"], st["skills"]),
        "shake %.1f  stop %d  fps %d  cache %d" % (
            (_feel.SHAKE.amount if _feel is not None else 0.0),
            (hs.frames if hs is not None else 0), fps, st["cache"]),
    ]
    for i, txt in enumerate(lines):
        img = font.render(txt, True, (255, 200, 130))
        surface.blit(img, (x - 78, y - 104 + i * 13))


# ============================================================================
# 13.  API MODUL — registry, tick, hook render & gameplay
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Razak."""
    _sync_palette()
    d = getattr(hero, "_razak_fx", None)
    if d is None:
        d = RazakFXDirector(hero)
        try:
            hero._razak_fx = d
        except Exception:                      # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:               # jangkar tua dibuang
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    """Lepas director dari registry DAN penanda milik-nya di unit."""
    try:
        if director.hero is not None:
            director.hero._razak_fx = None
            director.hero._razak_live_fx = False
    except Exception:                          # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit ini (dipanggil renderer/pipeline).

    Sekalian menandai unit supaya renderer TIDAK menggambar efek yang
    sekarang dimiliki lapisan hidup di canvas.  Return True kalau
    lapisan hidup jadi dipakai.
    """
    if not RAZAK_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                          # pragma: no cover
        return False
    try:
        hero._razak_live_fx = True
    except Exception:                          # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not getattr(hero, "_razak_live_fx", False):
        return False
    d = getattr(hero, "_razak_fx", None)
    return d is not None and d in _DIRECTORS


def tick(dt=None):
    """Majukan waktu FX satu frame nyata; aman dipanggil berkali-kali."""
    global _LAST_TICK_MS
    if dt is not None:
        step = max(0.0, min(1.0 / 20.0, float(dt)))
        _advance(step)
        return step
    # Guard frame-sama: draw_ground_layer() memanggil tick() untuk SETIAP
    # unit Razak, sedangkan _advance() melangkahkan SEMUA director. Tanpa
    # guard ini, 2 Razak di layar membuat FX maju 2x lebih cepat, 4 Razak
    # 4x lebih cepat (partikel & trail habis sebelum waktunya). Samakan
    # dengan pola sylara/kaizen/vex_fx.
    now = pygame.time.get_ticks()
    if now == _LAST_TICK_MS:
        return 0.0                             # frame yang sama: sudah maju
    if _feel is not None:
        _LAST_TICK_MS = now
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
    """Bersihkan seluruh state FX Razak (ganti level / keluar match)."""
    global _LAST_TICK_MS
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()
    _LAST_TICK_MS = None                       # jangan telan tick pertama
    if _feel is not None:
        try:
            _feel.reset()
        except Exception:                      # pragma: no cover
            pass


def total_particles():
    """Jumlah partikel Razak hidup di seluruh arena (dipakai HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def total_projectiles():
    """Jumlah proyektil visual Razak (dipakai test & HUD)."""
    return sum(d.projectiles.count() for d in _DIRECTORS)


# --- hook yang dipanggil renderer / heroes/__init__.py ---------------------

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: digambar SEBELUM sprite hero di-blit."""
    if not RAZAK_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_razak_fx", None)
    if d is not None:
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: digambar SESUDAH sprite hero di-blit."""
    if not RAZAK_FX_ENABLED:
        return
    d = director_for(hero)
    d.draw_front(surface, x, y)


# --- hook yang dipanggil _entity.py / bosses/base_boss.py ------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Machete Razak mendarat di target (basic attack melee)."""
    if not RAZAK_FX_ENABLED or hero is None or target is None:
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
    d.on_impact(tx, ty, ang, power, bool(crit), kind="slash")


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False,
                             kind="napalm"):
    """Proyektil / molotov mengenai target."""
    if not RAZAK_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    director_for(hero).on_impact(x, y, angle, power, bool(crit), kind=kind)


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """Skill Razak meledak di sebuah titik (Q/W/R AOE, E landing)."""
    if not RAZAK_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    r = float(radius if radius is not None
              else WORLD_RADIUS.get(skill, 60.0))
    if skill == "napalm" or skill == "q":
        # Q: pendaratan molotov (impact + kolam) — dedupe dengan
        # on_impact dari projectile supaya tidak dobel.
        d.on_impact(x, y, -math.pi / 2, 1.25, False, kind="napalm")
        if d._skill_for("q") is None and len(d.skills) < MAX_SKILLS:
            d.skills.append(SkillFX(
                "q", x, y, d.particles, radius=r,
                ground=_ground_dy(hero), scale=_rscale(hero)))
        return
    if skill in ("w", "e", "r"):
        # Jangan paksa phase: release/impact visual disinkronkan oleh
        # director via timer engine (_skill_release / dash landing),
        # jadi koninya tetap charge->release->fade seperti dirancang.
        if d._skill_for(skill) is None and len(d.skills) < MAX_SKILLS:
            d.skills.append(SkillFX(
                skill, x, y, d.particles, radius=r,
                ground=_ground_dy(hero), scale=_rscale(hero)))
    d.on_impact(x, y, 0.0,
                1.2 if skill != "r" else 2.0, skill == "r",
                kind={"w": "flame", "e": "dash",
                      "r": "storm"}.get(skill, "flame"))


def notify_skill_cast(hero, skill):
    """Dipanggil jalur gameplay saat skill dilepas (opsional)."""
    if not RAZAK_FX_ENABLED or hero is None or skill not in SKILL_DUR:
        return
    d = director_for(hero)
    d.on_cast(float(getattr(hero, "x", 0.0)),
              float(getattr(hero, "y", 0.0)), skill)


def notify_hurt(hero, amount=1.0):
    """Paksa HURT (alat uji / pemanggil eksternal)."""
    if not RAZAK_FX_ENABLED or hero is None:
        return
    director_for(hero).on_hurt(float(amount))


# --- hook yang dipanggil _NS_razak._spawn_napalm (fallback tengah) ---------

def spawn_napalm(hero, sx, sy, tx, ty):
    """API kompatibilitas: lempar molotov di koordinat layar."""
    if not RAZAK_FX_ENABLED or hero is None:
        return None
    d = director_for(hero)
    return d.spawn_napalm(sx, sy, tx, ty)
