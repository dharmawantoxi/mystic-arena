# ============================================================================
# heroes/sylara_fx.py
# ----------------------------------------------------------------------------
# SYLARA — COMBAT / GAME-FEEL ENGINE  (screen-space live layer)
#
# Badan Sylara digambar lewat ``_NS_sylara`` (heroes/_bundle.py) ke canvas yang
# DI-CACHE lalu di-scale oleh pipeline hero.  Semua yang butuh gerak 60 fps
# sejati — pita sapuan busur, partikel daun/angin, proyektil panah, impact,
# sulur Shackle, siklon Windrun, gale Powershot, screen shake, hit-stop —
# TIDAK boleh hidup di dalam canvas itu: hasilnya ikut beku pada kuantisasi
# pose dan menyusut bersama sprite.  Modul ini adalah lapisan hidup tersebut:
# digambar langsung ke layar pada skala 1:1 tiap frame, memakai delta-time
# nyata.
#
# Pembagian kerja (sengaja — supaya tidak ada efek yang digambar 2x):
#
#   RENDERER (canvas, ter-cache)        MODUL INI (layar, hidup)
#   -----------------------------       ----------------------------------
#   rig + selout + hood + cape          pita sapuan busur dari histori posisi
#   bayangan kontak, platform angin     partikel (daun, bulu, gust, debu)
#   TELEGRAPH AOE Q/W/E/R (besar)       PROYEKTIL panah angin (sistem nyata)
#   pose tarik tali / sapuan melee      IMPACT FX + flash + hit-stop + shake
#   napas, blink, kibaran rambut        siklon W / sulur E / gale R hidup
#                                       overlay DEBUG_CHARACTER
#
# 100% PROSEDURAL.  Tidak ada berkas gambar eksternal, tidak ada sprite-sheet,
# tidak ada loader tekstur.  Semua bentuk dibuat dengan pygame.draw +
# pygame.Surface + pygame.transform + pygame.Vector2.
#
# Isi modul
#   SYLARA_PALETTE      palette khusus karakter (kontrak 9 kunci + ramp)
#   Particle            partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem      pool + burst + stream + ring + cap, reusable
#   SwingTrail          weapon trail prosedural dari histori posisi busur
#   ImpactFX            flash + shockwave + serpihan + fragmen + debris
#   SylaraProjectile    proyektil modular (spawn->travel->hit->destroy)
#   ProjectileSystem    manajer proyektil
#   draw_wind_arrow     renderer panah bersama (dipakai _entity.py)
#   SkillFX             lifecycle FX skill (cast->charge->release->fade)
#   SylaraFXDirector    satu instance per unit, mengikat semua di atas
#   draw_debug_overlay  hitbox/hurtbox/state/frame/FPS/particle/skill/timer
#   API modul           tick / reset_all / notify_* / draw_*_layer
# ============================================================================

import math
import random

import pygame

try:                    # bus game-feel bersama (zephyr/gornak/grimjaw/...)
    from heroes import combat_feel as _feel
except Exception:       # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual SYLARA: hitbox, hurtbox, jangkauan, state animasi, frame, FPS,
#: jumlah partikel, state skill, timer serangan.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
SYLARA_FX_ENABLED = True

#: Hit-stop global (dibaca _core.Game.update lewat should_freeze_frame).
HIT_STOP_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 99

#: Batas keras proyektil visual per director.
MAX_PROJECTILES = 9

#: Panjang histori trail senjata (jumlah sample posisi busur).
TRAIL_SAMPLES = 7

#: Batas dampak aktif per director & skill sekaligus di layar.
MAX_IMPACTS = 4
MAX_SKILLS = 2

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Kecepatan proyektil visual (px/detik, ruang dunia).
ARROW_SPEED = 620.0
GALE_SPEED = 780.0
VINE_SPEED = 480.0

#: Radius EFEK di ruang dunia (px) — sinkron dengan
#: hero_skills/_bundle.py :: _NS_sylara_skills (Q line = skill_range 180,
#: W windrun aura 70, E shackle range 200, R cone 300).
WORLD_RADIUS = {"q": 180.0, "w": 70.0, "e": 200.0, "r": 300.0}

#: Umur FX skill dalam DETIK.  Sinkron dengan
#: ``_NS_sylara.SKILL_VISUAL_DURATION`` (180/180/150/60 langkah).
SKILL_TOTAL = {"q": 3.00, "w": 3.00, "e": 2.50, "r": 1.35}

#: Durasi pose per skill (frame) — memetakan umur FX ke fase yang sama
#: dengan yang dibaca renderer.
SKILL_DUR = {"q": 180, "w": 180, "e": 150, "r": 60}


# ============================================================================
# 1.  PALETTE  —  wind ranger: hijau angin + emas daun + kayu busur
# ============================================================================

SYLARA_PALETTE = {
    # ── kontrak palette karakter (9 kunci wajib) ────────────────────
    "outline":    (  9,  20,  12),
    "shadow":     (  4,  10,   6),
    "dark":       ( 20,  46,  24),
    "body":       ( 55,  98,  52),
    "mid":        ( 95, 150,  80),
    "light":      (140, 195, 115),
    "highlight":  (232, 255, 214),
    "weapon":     (130,  90,  50),
    "fx":         (110, 195,  90),

    # ── ramp angin (hijau — energi utama) ───────────────────────────
    "fx_deepest": ( 12,  38,  16),
    "fx_deep":    ( 20,  60,  25),
    "fx_dark":    ( 50, 120,  50),
    "fx_mid":     (110, 195,  90),
    "fx_light":   (170, 235, 135),
    "fx_bright":  (210, 255, 175),
    "fx_pale":    (232, 255, 210),
    "fx_white":   (240, 255, 220),

    # ── daun & rumput (aksen hangat satu-satunya) ───────────────────
    "leaf_dark":   ( 78,  96,  30),
    "leaf_mid":    (146, 168,  52),
    "leaf_gold":   (196, 214,  72),
    "leaf_ember":  (236, 168,  58),
    "leaf_pale":   (242, 240, 168),

    # ── emas hardware ───────────────────────────────────────────────
    "gold_dark":   ( 95,  70,  20),
    "gold":        (170, 130,  40),
    "gold_light":  (230, 195,  90),
    "gold_hot":    (255, 236, 150),

    # ── kayu busur ──────────────────────────────────────────────────
    "wood_dark":   ( 45,  25,  15),
    "wood_mid":    (130,  90,  50),
    "wood_light":  (170, 125,  75),
    "wood_shine":  (205, 165, 105),

    # ── anak panah ──────────────────────────────────────────────────
    "shaft":       (200, 175, 130),
    "shaft_dark":  (140, 110,  70),
    "head":        (180, 195, 210),
    "head_dark":   (100, 115, 135),
    "head_shine":  (235, 245, 255),
    "feather":     (140, 200,  95),
    "feather_dark":( 70, 120,  55),
    "string":      (220, 210, 180),

    # ── sulur Shackle (E) ───────────────────────────────────────────
    "vine_dark":   ( 24,  62,  30),
    "vine_mid":    ( 66, 124,  56),
    "vine_light":  (128, 190,  96),

    # ── materi lingkungan ───────────────────────────────────────────
    "dust":        (118, 110,  86),
    "dust_light":  (162, 154, 124),
    "smoke":       ( 44,  52,  40),
    "white":       (255, 255, 255),
}

P = SYLARA_PALETTE

#: Kunci palette live -> kunci palette renderer (_NS_sylara.PALETTE).
_PALETTE_SYNC = {
    "outline":      "shadow_deep",
    "dark":         "cloth_darkest",
    "body":         "cloth_mid",
    "mid":          "cloth_light",
    "light":        "cloth_high",
    "highlight":    "wind_white",
    "weapon":       "wood_mid",
    "fx":           "wind_mid",
    "fx_deepest":   "wind_darkest",
    "fx_deep":      "wind_darkest",
    "fx_dark":      "wind_dark",
    "fx_mid":       "wind_mid",
    "fx_light":     "wind_light",
    "fx_bright":    "wind_bright",
    "fx_pale":      "wind_white",
    "leaf_gold":    "leaf_gold",
    "leaf_ember":   "leaf_ember",
    "gold_dark":    "gold_dark",
    "gold":         "gold_mid",
    "gold_light":   "gold_light",
    "gold_hot":     "gold_shine",
    "wood_dark":    "wood_darkest",
    "wood_mid":     "wood_mid",
    "wood_light":   "wood_light",
    "wood_shine":   "wood_shine",
    "shaft":        "arrow_shaft",
    "shaft_dark":   "arrow_shaft_d",
    "head":         "arrow_head",
    "head_dark":    "arrow_head_d",
    "feather":      "arrow_feather",
    "feather_dark": "arrow_feather_d",
    "string":       "string",
}

_RENDERER = None
_PALETTE_SYNCED = False


def _renderer():
    """Ambil namespace renderer Sylara (lazy, sekali saja)."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from heroes._bundle import _NS_sylara as G
            _RENDERER = G
        except Exception:                  # pragma: no cover - tool minimal
            _RENDERER = False
    return _RENDERER or None


def _sync_palette():
    """Salin warna tema dari ``_NS_sylara.PALETTE`` sekali saja.

    Renderer adalah satu-satunya sumber kebenaran untuk material
    karakter; efek hidup tidak boleh punya salinan yang lalu melenceng.
    Kalau renderer tidak tersedia (tooling minimal), nilai literal di
    atas tetap dipakai.
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
# 2.  ANGGARAN EFEK  (menghormati preset kualitas mobile)
# ============================================================================

def _quality():
    try:
        from mobile.perf import Quality
        return Quality
    except Exception:                      # pragma: no cover
        return None


def particle_budget():
    """Faktor jumlah partikel (0.0 = partikel dimatikan total)."""
    Q = _quality()
    if Q is None:
        return 1.0
    if not getattr(Q, "particles", True):
        return 0.0
    return float(getattr(Q, "particle_ratio", 1.0))


def skill_detail():
    """Detail telegraf/skill 0..1 (turunan beban FX).

    Dipakai untuk mengurangi jumlah chevron, bilah rumput, dan irisan
    cincin saat banyak hero live-FX bertarung. Hanya intensitas yang
    dikurangi (bukan frame yang dilewati), sehingga skill tidak berkedip.
    """
    Q = _quality()
    if Q is None:
        return 1.0
    return max(0.35, float(getattr(Q, "particle_ratio", 1.0)))


def glow_allowed():
    Q = _quality()
    return True if Q is None else bool(getattr(Q, "glow", True))


def shake_allowed():
    """Apakah guncangan boleh dipakai untuk game feel (bukan hanya kamera)."""
    Q = _quality()
    return True if Q is None else bool(getattr(Q, "screen_shake", True))


# ============================================================================
# 3.  HELPER WARNA & DETERMINISME
# ============================================================================

def _clamp_color(color):
    """Jepit komponen warna ke 0-255 dan pastikan tuple int.

    Fast path: palette sudah int valid (99% panggilan). Menghindari
    genexpr + max/min per partikel, yang panas di profil 5 hero starter.
    """
    if isinstance(color, (tuple, list)):
        n = len(color)
        if n == 3:
            r, g, b = color[0], color[1], color[2]
            if (isinstance(r, int) and isinstance(g, int) and
                    isinstance(b, int) and
                    0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                return (r, g, b)
        elif n == 4:
            r, g, b, a = color
            if (isinstance(r, int) and isinstance(g, int) and
                    isinstance(b, int) and isinstance(a, int) and
                    0 <= r <= 255 and 0 <= g <= 255 and
                    0 <= b <= 255 and 0 <= a <= 255):
                return (r, g, b, a)
    if type(color) is tuple and len(color) == 3:
        _r, _g, _b = color
        if (type(_r) is int and type(_g) is int and type(_b) is int
                and 0 <= _r <= 255 and 0 <= _g <= 255 and 0 <= _b <= 255):
            return color
    return tuple(max(0, min(255, int(c))) for c in color)


def _mix(a, b, t):
    """Interpolasi linear dua warna RGB."""
    t = max(0.0, min(1.0, t))
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def _hash01(seed):
    """Pseudo-random deterministik [0,1) dari integer."""
    h = int(seed) * 2654435761 & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFF) / 65535.0


def _budgeted(count):
    """Skalakan jumlah partikel sesuai preset kualitas (min 0)."""
    b = particle_budget()
    if b <= 0.0:
        return 0
    return max(0, int(round(count * b)))


def _ease_out(t):
    t = max(0.0, min(1.0, float(t)))
    return 1.0 - (1.0 - t) * (1.0 - t)


def _ease_in(t):
    t = max(0.0, min(1.0, float(t)))
    return t * t


def _ease_in_out(t):
    t = max(0.0, min(1.0, float(t)))
    return t * t * (3.0 - 2.0 * t)


# ============================================================================
# 4.  SURFACE CACHE  —  glow / daun / bulu / ring dibuat sekali
# ============================================================================

_SURF_CACHE = {}
_SURF_CACHE_MAX = 320


def _cache_put(key, surf):
    # Buang 25% entri tertua saat penuh (dict Python menjaga urutan
    # sisip) — jauh lebih baik daripada mengosongkan seluruh cache.
    if len(_SURF_CACHE) >= _SURF_CACHE_MAX:
        for k in list(_SURF_CACHE)[:_SURF_CACHE_MAX // 4]:
            del _SURF_CACHE[k]
    _SURF_CACHE[key] = surf
    return surf


def glow_surface(radius, color, power=1.0):
    """Bola cahaya radial prosedural, PREMULTIPLIED untuk additive blit."""
    radius = max(2, int(radius))
    color = _clamp_color(color)
    key = ("glow", radius, color, round(power, 2))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    size = radius * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = radius + 1
    steps = max(4, min(radius, 14))
    for i in range(steps, 0, -1):
        t = i / float(steps)
        r = max(1, int(radius * t))
        k = power * (1.0 - t) ** 1.7
        if k <= 0.004:
            continue
        pygame.draw.circle(
            surf,
            (int(color[0] * k), int(color[1] * k), int(color[2] * k),
             min(255, int(255 * k))),
            (c, c), r)
    return _cache_put(key, surf)


def spark_surface(size, color):
    """Bintang 4 sudut (pixel-art spark) — cached."""
    size = max(3, int(size))
    color = _clamp_color(color)
    key = ("spark", size, color)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    s = size * 2 + 1
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    c = size
    pygame.draw.polygon(surf, (*color, 235), [
        (c, 0), (c + max(1, size // 3), c),
        (c, s - 1), (c - max(1, size // 3), c)])
    pygame.draw.polygon(surf, (*color, 190), [
        (0, c), (c, c - max(1, size // 4)),
        (s - 1, c), (c, c + max(1, size // 4))])
    pygame.draw.circle(surf, (255, 255, 255, 255), (c, c),
                       max(1, size // 4))
    return _cache_put(key, surf)


def leaf_surface(size, color, shine=None):
    """Daun bersudut menghadap +x (bahasa visual ranger) — cached.

    Bukan elips halus: dua segitiga tepi keras + tulang daun 1 px,
    supaya bentuknya selamat setelah downscale pipeline hero.
    """
    size = max(3, int(size))
    color = _clamp_color(color)
    shine = _clamp_color(shine or _mix(color, P["leaf_pale"], 0.55))
    key = ("leaf", size, color, shine)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    w = size * 2 + 3
    h = size + 3
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cy = h // 2
    pts = [(1, cy), (size, 1), (w - 2, cy), (size, h - 2)]
    pygame.draw.polygon(surf, (*color, 240), pts)
    pygame.draw.polygon(surf, (*shine, 220),
                        [(1, cy), (size, 1), (w - 2, cy)])
    pygame.draw.line(surf, (*P["outline"], 200), (1, cy), (w - 2, cy), 1)
    pygame.draw.polygon(surf, (*P["outline"], 190), pts, 1)
    return _cache_put(key, surf)


def feather_surface(size, color):
    """Bulu fletching (sirip runcing) menghadap +x — cached."""
    size = max(3, int(size))
    color = _clamp_color(color)
    key = ("feather", size, color)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    w = size * 2 + 3
    h = size + 3
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cy = h // 2
    pygame.draw.polygon(surf, (*color, 235),
                        [(1, cy), (w - 2, cy - size // 2),
                         (w - 2, cy + 1)])
    pygame.draw.line(surf, (*_mix(color, P["white"], 0.5), 210),
                     (1, cy), (w - 2, cy - size // 3), 1)
    return _cache_put(key, surf)


def arrowhead_surface(length, width, color, shine):
    """Mata panah baja bersudut menghadap +x — cached."""
    length = max(4, int(length))
    width = max(2, int(width))
    color = _clamp_color(color)
    shine = _clamp_color(shine)
    key = ("head", length, width, color, shine)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    surf = pygame.Surface((length + 4, width * 2 + 4), pygame.SRCALPHA)
    cy = width + 2
    pts = [(length + 2, cy), (2, cy - width), (max(4, length // 3), cy),
           (2, cy + width)]
    pygame.draw.polygon(surf, (*color, 240), pts)
    pygame.draw.polygon(surf, (*shine, 225),
                        [(length + 2, cy), (2, cy - width),
                         (max(4, length // 3), cy)])
    pygame.draw.polygon(surf, (*P["outline"], 210), pts, 1)
    return _cache_put(key, surf)


def ring_surface(radius, thickness, color, alpha=255):
    """Cincin energi tipis — cached."""
    radius = max(3, int(radius))
    thickness = max(1, int(thickness))
    color = _clamp_color(color)
    key = ("ring", radius, thickness, color, int(alpha))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    size = radius * 2 + thickness * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    pygame.draw.circle(surf, (*color, int(alpha)), (c, c), radius, thickness)
    return _cache_put(key, surf)


def ellipse_ring_surface(rx, ry, thickness, color, angle_deg=0):
    """Cincin ELIPS (shockwave berarah) — cached + rotasi terkuantisasi."""
    rx = max(3, int(rx))
    ry = max(2, int(ry))
    thickness = max(1, int(thickness))
    color = _clamp_color(color)
    step = int(angle_deg) // 10 * 10          # kuantisasi 10 derajat
    key = ("ering", rx, ry, thickness, color, step)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    pad = thickness + 2
    base = pygame.Surface((rx * 2 + pad * 2, ry * 2 + pad * 2),
                          pygame.SRCALPHA)
    pygame.draw.ellipse(base, (*color, 255),
                        (pad, pad, rx * 2, ry * 2), thickness)
    if step:
        base = pygame.transform.rotate(base, -step)
    return _cache_put(key, base)


def ground_glow_surface(radius, color, power=0.3):
    """Kabut cahaya di tanah (elips gepeng, premultiplied) — cached."""
    radius = max(4, int(radius))
    color = _clamp_color(color)
    key = ("gglow", radius, color, round(power, 2))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    w = radius * 2 + 4
    h = radius + 4
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    steps = max(4, min(radius // 2, 12))
    for i in range(steps, 0, -1):
        t = i / float(steps)
        rx = max(2, int(radius * t))
        ry = max(1, int(radius * t * 0.5))
        k = power * (1.0 - t) ** 1.5
        if k <= 0.004:
            continue
        pygame.draw.ellipse(
            surf,
            (int(color[0] * k), int(color[1] * k), int(color[2] * k),
             min(255, int(255 * k))),
            (w // 2 - rx, h // 2 - ry, rx * 2, ry * 2))
    return _cache_put(key, surf)


def gust_surface(radius, color, depth=0.58, thickness=3):
    """Sabit angin (pita laminar) menghadap +x — cached.

    Dua busur konsentris yang menyempit di ujung: bentuk khas hembusan
    angin, bukan lingkaran polos.
    """
    radius = max(4, int(radius))
    color = _clamp_color(color)
    thickness = max(1, int(thickness))
    key = ("gust", radius, color, round(depth, 2), thickness)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    size = radius * 2 + thickness * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    rect = pygame.Rect(c - radius, c - radius, radius * 2, radius * 2)
    span = 0.55 + depth * 0.75
    try:
        pygame.draw.arc(surf, (*color, 240), rect, -span, span, thickness)
        r2 = max(2, int(radius * 0.72))
        rect2 = pygame.Rect(c - r2, c - r2, r2 * 2, r2 * 2)
        pygame.draw.arc(surf, (*_mix(color, P["fx_pale"], 0.6), 200),
                        rect2, -span * 0.7, span * 0.7,
                        max(1, thickness - 1))
    except (ValueError, pygame.error):        # pragma: no cover
        pass
    return _cache_put(key, surf)


def chevron_surface(size, color, thick=2):
    """Panah penunjuk arah menghadap +x — cached."""
    size = max(4, int(size))
    thick = max(1, int(thick))
    color = _clamp_color(color)
    key = ("chev", size, color, thick)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    s = size * 2 + thick * 2 + 2
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    c = s // 2
    pygame.draw.lines(surf, (*color, 245), False,
                      [(c - size // 2, c - size),
                       (c + size // 2, c),
                       (c - size // 2, c + size)], thick)
    return _cache_put(key, surf)


def dashed_ring_surface(radius, thickness, color, segments=4, span=0.42,
                        rot_step=0):
    """Cincin putus-putus berputar (halo rumput / telegraph) — cached."""
    radius = max(4, int(radius))
    thickness = max(1, int(thickness))
    color = _clamp_color(color)
    segments = max(3, min(24, int(segments)))
    span = max(0.08, min(1.6, float(span)))
    step = int(rot_step) // 10 * 10
    key = ("dring", radius, thickness, color, segments, round(span, 2), step)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    size = radius * 2 + thickness * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    rect = pygame.Rect(c - radius, c - radius, radius * 2, radius * 2)
    off = math.radians(step)
    for i in range(segments):
        a0 = off + i * math.tau / segments
        try:
            pygame.draw.arc(surf, (*color, 255), rect, a0, a0 + span,
                            thickness)
        except (ValueError, pygame.error):    # pragma: no cover
            pass
    return _cache_put(key, surf)


def grass_halo_surface(radius, color, blades=18, squash=0.42):
    """Halo rumput tegak di tanah (AOE ranger) — cached."""
    radius = max(6, int(radius))
    color = _clamp_color(color)
    blades = max(6, min(48, int(blades)))
    key = ("grass", radius, color, blades, round(squash, 2))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    h = int(radius * squash * 2) + 22
    w = radius * 2 + 8
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    for i in range(blades):
        a = i * math.tau / blades
        bx = cx + math.cos(a) * radius
        by = cy + math.sin(a) * radius * squash
        ln = 5 + int(_hash01(i * 13 + radius) * 7)
        lean = (_hash01(i * 29) - 0.5) * 5.0
        pygame.draw.line(surf, (*color, 210),
                         (int(bx), int(by)),
                         (int(bx + lean), int(by - ln)), 1)
        pygame.draw.line(surf, (*_mix(color, P["leaf_gold"], 0.55), 190),
                         (int(bx), int(by)),
                         (int(bx + lean * 0.5), int(by - ln * 0.6)), 1)
    return _cache_put(key, surf)


def clear_cache():
    """Bersihkan seluruh surface cache (dipanggil saat ganti resolusi)."""
    _SURF_CACHE.clear()


def cache_size():
    """Jumlah surface yang sedang di-cache (dipakai debug/HUD)."""
    return len(_SURF_CACHE)


# --- scratch surface pool: hindari alokasi Surface tiap partikel ------------

_SCRATCH = {}


def _scratch(w, h):
    """Surface sementara transparan berukuran >= (w,h), dipakai ulang."""
    w = max(4, int(w))
    h = max(4, int(h))
    key = (1 << (w - 1).bit_length(), 1 << (h - 1).bit_length())
    s = _SCRATCH.get(key)
    if s is None:
        s = pygame.Surface(key, pygame.SRCALPHA)
        _SCRATCH[key] = s
    else:
        s.fill((0, 0, 0, 0))
    return s


def rotated_cached(key, surf, deg):
    """Hasil ``pygame.transform.rotate`` yang di-cache per (key, 15°).

    Rotasi adalah operasi per-piksel; dipanggil berkali-kali per frame
    untuk daun, bulu, dan mata panah.  Kuantisasi 15° membuat jumlah
    entri terbatas (24 bucket) sekaligus cukup halus pada ukuran sprite
    sekecil ini.
    """
    step = int(deg) // 15 * 15
    if step == 0:
        return surf
    ck = ("rot", key, step)
    out = _SURF_CACHE.get(ck)
    if out is None:
        out = pygame.transform.rotate(surf, step)
        _cache_put(ck, out)
    return out


def _blit_faded(surface, surf, cx, cy, alpha=255, additive=False):
    """Blit surface dengan alpha dinamis tanpa membuat salinan."""
    if alpha <= 4:
        return
    if alpha >= 250 and not additive:
        surface.blit(surf, (int(cx - surf.get_width() / 2),
                            int(cy - surf.get_height() / 2)))
        return
    surf.set_alpha(int(alpha))
    surface.blit(surf, (int(cx - surf.get_width() / 2),
                        int(cy - surf.get_height() / 2)),
                 special_flags=pygame.BLEND_RGB_ADD if additive else 0)
    surf.set_alpha(255)


# ============================================================================
# 5.  PARTICLE SYSTEM
# ============================================================================

class Particle:
    """Satu partikel prosedural.

    Kontrak atribut lengkap: position, velocity, acceleration, life,
    max_life, size, rotation, rotation_speed, alpha, gravity, color.
    ``shape`` memilih bentuk gambar (pixel-art, hard edge):
      pixel / spark / leaf / feather / streak / gust / splinter /
      smoke / glow / grass
    """

    __slots__ = ("pos", "vel", "acc", "life", "max_life", "size",
                 "rotation", "rotation_speed", "alpha", "gravity",
                 "color", "color_end", "shape", "drag", "additive",
                 "active", "fade_pow", "back", "swirl", "flutter")

    def __init__(self):
        self.pos = pygame.Vector2()
        self.vel = pygame.Vector2()
        self.acc = pygame.Vector2()
        self.life = 0.0
        self.max_life = 1.0
        self.size = 2.0
        self.rotation = 0.0
        self.rotation_speed = 0.0
        self.alpha = 255
        self.gravity = 0.0
        self.color = P["fx_light"]
        self.color_end = None
        self.shape = "pixel"
        self.drag = 0.0
        self.additive = False
        self.active = False
        self.fade_pow = 1.0
        self.back = False
        self.swirl = 0.0
        self.flutter = 0.0

    # ------------------------------------------------------------------
    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        """Aktifkan partikel ini (dipakai ulang dari pool)."""
        self.pos.update(x, y)
        self.vel.update(vx, vy)
        self.acc.update(kw.get("ax", 0.0), kw.get("ay", 0.0))
        self.life = self.max_life = max(0.02, float(life))
        self.size = float(size)
        self.color = color
        self.color_end = kw.get("color_end")
        self.gravity = float(kw.get("gravity", 0.0))
        self.drag = float(kw.get("drag", 0.0))
        self.rotation = float(kw.get("rotation", 0.0))
        self.rotation_speed = float(kw.get("rotation_speed", 0.0))
        self.alpha = int(kw.get("alpha", 255))
        self.shape = kw.get("shape", "pixel")
        self.additive = bool(kw.get("additive", False))
        self.fade_pow = float(kw.get("fade_pow", 1.0))
        self.back = bool(kw.get("back", False))
        self.swirl = float(kw.get("swirl", 0.0))
        self.flutter = float(kw.get("flutter", 0.0))
        self.active = True
        return self

    # ------------------------------------------------------------------
    def update(self, dt):
        """Integrasi gerak; return False kalau partikel sudah mati."""
        self.life -= dt
        if self.life <= 0.0:
            self.active = False
            return False
        self.vel.x += self.acc.x * dt
        self.vel.y += (self.acc.y + self.gravity) * dt
        if self.swirl:
            # belok tegak-lurus kecepatan -> gerak spiral khas angin
            vx, vy = self.vel.x, self.vel.y
            self.vel.x += -vy * self.swirl * dt
            self.vel.y += vx * self.swirl * dt
        if self.flutter:
            # daun tidak jatuh lurus: bergoyang menyamping (deterministik
            # dari umur, jadi tetap tenang saat frame drop)
            t = self.max_life - self.life
            self.vel.x += math.sin(t * 9.0 + self.rotation) \
                * self.flutter * dt * 60.0
        if self.drag:
            damp = max(0.0, 1.0 - self.drag * dt)
            self.vel.x *= damp
            self.vel.y *= damp
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt
        self.rotation += self.rotation_speed * dt
        return True

    # ------------------------------------------------------------------
    def draw(self, surface):
        """Gambar partikel — pixel-snapped, hard edge."""
        t = self.life / self.max_life                 # 1 -> 0
        fade = t ** self.fade_pow
        a = int(self.alpha * fade)
        if a <= 3:
            return
        col = self.color
        if self.color_end is not None:
            col = _mix(self.color_end, self.color, fade)
        x = int(self.pos.x)
        y = int(self.pos.y)
        sz = max(1, int(self.size * (0.35 + 0.65 * fade)))

        if self.shape == "glow":
            if not glow_allowed():
                sz = max(1, sz // 2)
            g = glow_surface(sz * 2, col, round(0.9 * fade, 2))
            surface.blit(g, (x - sz * 2, y - sz * 2),
                         special_flags=pygame.BLEND_RGB_ADD)
            return

        if self.shape == "spark":
            s = spark_surface(sz + 1, col)
            s.set_alpha(a)
            surface.blit(s, (x - sz - 1, y - sz - 1))
            return

        if self.shape == "leaf":
            base = leaf_surface(max(2, sz), col)
            if sz >= 2:
                base = rotated_cached(("pleaf", max(2, sz), col), base,
                                      -int(math.degrees(self.rotation)))
            base.set_alpha(a)
            surface.blit(base, (x - base.get_width() // 2,
                                y - base.get_height() // 2))
            return

        if self.shape == "feather":
            base = feather_surface(max(2, sz), col)
            if sz >= 2:
                base = rotated_cached(("pfeat", max(2, sz), col), base,
                                      -int(math.degrees(self.rotation)))
            base.set_alpha(a)
            surface.blit(base, (x - base.get_width() // 2,
                                y - base.get_height() // 2))
            return

        if self.shape == "splinter":
            # serpihan kayu/baja berputar (debris benturan)
            ca = math.cos(self.rotation)
            sa = math.sin(self.rotation)
            h = max(1, sz)
            w = max(1, sz // 2)
            pts = []
            for dx, dy in ((h, 0), (-w, w), (-h // 2, 0), (-w, -w)):
                pts.append((x + int(dx * ca - dy * sa),
                            y + int(dx * sa + dy * ca)))
            tmp = _scratch(sz * 4 + 4, sz * 4 + 4)
            off = sz * 2 + 2
            pygame.draw.polygon(
                tmp, (*col, a),
                [(px - x + off, py - y + off) for px, py in pts])
            surface.blit(tmp, (x - off, y - off))
            return

        if self.shape == "streak":
            # garis tipis searah kecepatan — percikan angin cepat
            v = self.vel
            n = v.length()
            if n < 0.01:
                return
            ux, uy = v.x / n, v.y / n
            ln = max(2, int(sz * 2 + n * 0.02))
            tmp = _scratch(ln * 2 + 6, ln * 2 + 6)
            off = ln + 3
            pygame.draw.line(tmp, (*col, a),
                             (off, off),
                             (off - int(ux * ln), off - int(uy * ln)),
                             max(1, sz // 2))
            surface.blit(tmp, (x - off, y - off))
            return

        if self.shape == "gust":
            # pita angin kecil melengkung searah gerak (additive)
            v = self.vel
            ang = math.atan2(v.y, v.x) if v.length_squared() > 0.01 \
                else self.rotation
            base = gust_surface(max(3, sz * 2), col, 0.55, max(1, sz // 2))
            base = rotated_cached(("pgust", max(3, sz * 2), col,
                                   max(1, sz // 2)),
                                  base, -int(math.degrees(ang)))
            base.set_alpha(a)
            surface.blit(base, (x - base.get_width() // 2,
                                y - base.get_height() // 2),
                         special_flags=pygame.BLEND_RGB_ADD)
            return

        if self.shape == "grass":
            # helai rumput/serpih daun tegak (efek tanah)
            ln = max(2, sz * 2)
            pygame.draw.line(surface, (*col, a), (x, y),
                             (x + int(math.cos(self.rotation) * ln * 0.4),
                              y - ln), 1)
            return

        if self.shape == "smoke":
            # gumpalan debu lembut di lapisan belakang
            r = max(2, sz)
            tmp = _scratch(r * 2 + 4, r * 2 + 4)
            off = r + 2
            pygame.draw.circle(tmp, (*col, int(a * 0.5)), (off, off), r)
            pygame.draw.circle(tmp, (*_mix(col, P["fx_pale"], 0.15),
                                     int(a * 0.25)),
                               (off - r // 3, off - r // 3),
                               max(1, r // 2))
            surface.blit(tmp, (x - off, y - off))
            return

        # default: kotak chunky (pixel-art) + sudut terang
        tmp = _scratch(sz * 2 + 2, sz * 2 + 2)
        pygame.draw.rect(tmp, (*col, a), (1, 1, sz, sz))
        if sz >= 3:
            pygame.draw.rect(tmp, (*P["fx_pale"], min(255, a + 40)),
                             (1, 1, max(1, sz // 2), max(1, sz // 2)))
        surface.blit(tmp, (x - sz // 2, y - sz // 2),
                     special_flags=pygame.BLEND_RGB_ADD
                     if self.additive else 0)


class ParticleSystem:
    """Pool partikel reusable: spawn / burst / stream / ring / update / draw."""

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = int(cap)
        self._pool = []
        self._live = []

    # ------------------------------------------------------------------
    def _acquire(self):
        if self._pool:
            return self._pool.pop()
        return Particle()

    def count(self):
        """Jumlah partikel yang sedang hidup."""
        return len(self._live)

    def alive(self):
        """True kalau masih ada partikel hidup."""
        return bool(self._live)

    def clear(self):
        """Matikan semua partikel (kembalikan ke pool)."""
        for p in self._live:
            p.active = False
            if len(self._pool) < self.cap:
                self._pool.append(p)
        self._live.clear()

    # ------------------------------------------------------------------
    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        """Spawn satu partikel.  Return partikel, atau None kalau penuh.

        Gerbang anggaran dipasang di sini supaya emisi kontinu (bukan
        hanya burst) ikut turun saat 5 hero starter berbarengan.
        """
        budget = particle_budget()
        if budget <= 0.0:
            return None
        if len(self._live) >= self.cap:
            return None
        p = self._acquire().spawn(x, y, vx, vy, life, size, color, **kw)
        self._live.append(p)
        return p

    # ------------------------------------------------------------------
    def burst(self, x, y, count, speed=(60.0, 200.0), life=(0.25, 0.6),
              size=(2, 4), colors=None, spread=math.tau, direction=0.0,
              gravity=0.0, drag=2.0, shape="pixel", additive=False,
              rotation_speed=(0.0, 0.0), fade_pow=1.0, back=False,
              swirl=0.0, flutter=0.0):
        """Semburan radial / berarah.

        ``direction`` + ``spread`` mengontrol kerucut sebaran; spread
        ``math.tau`` = melingkar penuh.  ``back=True`` mengirim partikel
        ke lapisan belakang karakter (debu/asap).  ``swirl`` memberi
        belokan spiral khas angin, ``flutter`` goyangan daun jatuh.
        Jumlah partikel otomatis mengikuti anggaran kualitas perangkat.
        """
        count = _budgeted(count)
        if count <= 0:
            return 0
        colors = colors or (P["fx_light"], P["fx_mid"], P["fx_bright"])
        room = self.cap - len(self._live)
        if room <= 0:
            return 0
        count = min(count, room)
        n = 0
        self._in_burst = getattr(self, "_in_burst", 0) + 1
        try:
            for i in range(int(count)):
                ang = direction + (random.random() - 0.5) * spread
                spd = random.uniform(speed[0], speed[1])
                rs = random.uniform(rotation_speed[0], rotation_speed[1]) \
                    if rotation_speed[1] != rotation_speed[0] else 0.0
                if self.spawn(x, y,
                              math.cos(ang) * spd, math.sin(ang) * spd,
                              random.uniform(life[0], life[1]),
                              random.uniform(size[0], size[1]),
                              colors[i % len(colors)],
                              gravity=gravity, drag=drag, shape=shape,
                              additive=additive, fade_pow=fade_pow,
                              back=back, swirl=swirl, flutter=flutter,
                              rotation=random.random() * math.tau,
                              rotation_speed=rs):
                    n += 1
        finally:
            self._in_burst -= 1
        return n

    # ------------------------------------------------------------------
    def stream(self, x, y, tx, ty, count, life=(0.3, 0.6), size=(1, 3),
               colors=None, drag=1.2, shape="streak"):
        """Aliran partikel dari (x,y) menuju (tx,ty) — koridor volley."""
        count = _budgeted(count)
        if count <= 0:
            return 0
        colors = colors or (P["fx_bright"], P["fx_light"], P["leaf_gold"])
        n = 0
        for i in range(int(count)):
            t = i / max(1, count)
            px = x + (tx - x) * t + random.uniform(-4, 4)
            py = y + (ty - y) * t + random.uniform(-3, 3)
            dx, dy = tx - px, ty - py
            dist = max(1.0, math.hypot(dx, dy))
            spd = random.uniform(120.0, 260.0)
            if self.spawn(px, py, dx / dist * spd, dy / dist * spd,
                          random.uniform(life[0], life[1]),
                          random.uniform(size[0], size[1]),
                          colors[i % len(colors)],
                          drag=drag, shape=shape,
                          color_end=P["fx_deepest"],
                          rotation=random.random() * math.tau,
                          rotation_speed=random.uniform(-6, 6)):
                n += 1
        return n

    # ------------------------------------------------------------------
    def ring(self, x, y, radius, count, life=(0.3, 0.7), size=(2, 4),
             colors=None, speed=(40.0, 110.0), squash=0.55, shape="leaf",
             inward=False, swirl=0.0, back=False):
        """Cincin partikel mengembang (atau menyusut kalau ``inward``).

        ``squash`` menggepengkan cincin ke perspektif tanah (0.45 = AOE
        di lantai arena, 1.0 = cincin vertikal penuh).
        """
        count = _budgeted(count)
        if count <= 0:
            return 0
        colors = colors or (P["fx_mid"], P["leaf_gold"], P["fx_light"])
        n = 0
        self._in_burst = getattr(self, "_in_burst", 0) + 1
        try:
            for i in range(int(count)):
                ang = (i / float(count)) * math.tau + random.uniform(-0.12, 0.12)
                spd = random.uniform(speed[0], speed[1])
                dx, dy = math.cos(ang) * spd, math.sin(ang) * spd * squash
                if inward:
                    px = x + math.cos(ang) * radius
                    py = y + math.sin(ang) * radius * squash
                    dx, dy = -dx, -dy
                else:
                    px = x + math.cos(ang) * radius * 0.35
                    py = y + math.sin(ang) * radius * squash * 0.35
                if self.spawn(px, py, dx, dy,
                              random.uniform(life[0], life[1]),
                              random.uniform(size[0], size[1]),
                              colors[i % len(colors)],
                              drag=1.8, shape=shape,
                              color_end=P["fx_deep"],
                              rotation=random.random() * math.tau,
                              rotation_speed=random.uniform(-7, 7),
                              swirl=swirl, back=back):
                    n += 1
        finally:
            self._in_burst -= 1
        return n

    # ------------------------------------------------------------------
    def update(self, dt):
        """Integrasi semua partikel; yang mati dikembalikan ke pool."""
        if not self._live:
            return
        keep = []
        pool = self._pool
        for p in self._live:
            if p.update(dt):
                keep.append(p)
            elif len(pool) < self.cap:
                pool.append(p)
        self._live = keep

    # ------------------------------------------------------------------
    def draw(self, surface, layer=None):
        """Gambar partikel.  ``layer`` opsional: 'back' / 'front'."""
        if layer is None:
            for p in self._live:
                p.draw(surface)
            return
        want_back = layer == "back"
        for p in self._live:
            if p.back == want_back:
                p.draw(surface)


# ============================================================================
# 6.  SWING TRAIL  —  pita sapuan busur dari histori posisi
# ============================================================================

class SwingTrail:
    """Jejak busur Sylara berbasis histori posisi (OLD POS ... CURRENT).

    Menyimpan pasangan (pangkal, ujung) beberapa frame terakhir lalu
    menyusunnya jadi pita poligon translucent 4-lapis yang memudar +
    garis tepi putih 1-2 px (hard edge pixel-art) dan kilau daun.  Trail
    OTOMATIS mengikuti arah serangan karena bentuknya murni turunan dari
    lintasan BUSUR limb (arc-based), bukan lerp linear.

    Bahasa visual ranger: pita LAMINAR (tipis, cepat, berlapis seperti
    aliran udara), bukan smear baja tebal ala Kaizen.
    """

    def __init__(self, samples=TRAIL_SAMPLES,
                 color_edge=None, color_core=None):
        self.samples = int(samples)
        self.points = []            # [[pangkal, ujung, umur], ...]
        self.color_edge = color_edge or P["fx_dark"]
        self.color_core = color_core or P["fx_bright"]
        self.life = 0.22            # detik sebelum sample dibuang
        self.width_boost = 1.0
        self.overcharged = False    # True saat skill aktif (pita lebih panas)
        self.active = False

    # ------------------------------------------------------------------
    def reset(self):
        """Kosongkan trail (dipanggil saat swing baru dimulai)."""
        self.points.clear()
        self.active = False
        self.overcharged = False

    def push(self, base, tip):
        """Catat satu posisi senjata (dipanggil tiap frame saat swing)."""
        self.points.append([pygame.Vector2(base), pygame.Vector2(tip), 0.0])
        if len(self.points) > self.samples:
            self.points.pop(0)
        self.active = True

    # ------------------------------------------------------------------
    def update(self, dt):
        """Tua-kan sample; buang yang lewat umur."""
        if not self.points:
            self.active = False
            return
        for s in self.points:
            s[2] += dt
        self.points = [s for s in self.points if s[2] < self.life]
        if not self.points:
            self.active = False

    # ------------------------------------------------------------------
    def _quad_alpha(self, idx, n):
        """Alpha per segmen: ujung terbaru paling terang."""
        t = (idx + 1) / float(n)
        return t * t

    def draw(self, surface):
        """Gambar pita: selubung -> badan -> inti -> garis ujung -> daun."""
        n = len(self.points)
        if n < 2:
            return

        xs = []
        ys = []
        for g, t, _a in self.points:
            xs.append(g.x)
            xs.append(t.x)
            ys.append(g.y)
            ys.append(t.y)
        minx, maxx = int(min(xs)) - 8, int(max(xs)) + 8
        miny, maxy = int(min(ys)) - 8, int(max(ys)) + 8
        w = maxx - minx
        h = maxy - miny
        if w <= 0 or h <= 0 or w > 1400 or h > 1400:
            return

        buf = _scratch(w, h)

        def loc(v):
            return (int(v.x) - minx, int(v.y) - miny)

        hot = 1.22 if self.overcharged else 1.0

        # ── lapis 1: selubung angin dalam (lebar penuh, hijau gelap) ─
        for i in range(n - 1):
            g0, t0, a0 = self.points[i]
            g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(105 * self._quad_alpha(i, n) * fade *
                        self.width_boost)
            if alpha <= 4:
                continue
            pygame.draw.polygon(
                buf, (*P["fx_deepest"], alpha),
                [loc(g0), loc(t0), loc(t1), loc(g1)])

        # ── lapis 2: badan pita (setengah lebar, dekat ujung) ────────
        for i in range(n - 1):
            g0, t0, a0 = self.points[i]
            g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(195 * self._quad_alpha(i, n) * fade * hot)
            if alpha <= 6:
                continue
            m0 = g0.lerp(t0, 0.46)
            m1 = g1.lerp(t1, 0.46)
            pygame.draw.polygon(
                buf, (*self.color_edge, min(255, alpha)),
                [loc(m0), loc(t0), loc(t1), loc(m1)])

        # ── lapis 3: inti nyaris putih (seperempat lebar terakhir) ───
        for i in range(n - 1):
            g0, t0, a0 = self.points[i]
            g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(235 * self._quad_alpha(i, n) * fade * hot)
            if alpha <= 8:
                continue
            m0 = g0.lerp(t0, 0.78)
            m1 = g1.lerp(t1, 0.78)
            pygame.draw.polygon(
                buf, (*self.color_core, min(255, alpha)),
                [loc(m0), loc(t0), loc(t1), loc(m1)])

        # ── lapis 4: garis ujung 1-2 px (hard edge pixel-art) ────────
        for i in range(n - 1):
            _g0, t0, a0 = self.points[i]
            _g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(245 * self._quad_alpha(i, n) * fade)
            if alpha <= 8:
                continue
            pygame.draw.line(buf, (*P["fx_pale"], min(255, alpha)),
                             loc(t0), loc(t1), 2)

        surface.blit(buf, (minx, miny))

        # ── lapis 5: kilau daun di sepanjang busur (butuh rotasi, jadi
        #    digambar di luar buffer) ──────────────────────────────────
        if n >= 4:
            for i in range(0, n - 1, 3):
                _g0, t0, a0 = self.points[i]
                fade = max(0.0, 1.0 - a0 / self.life)
                alpha = int(165 * self._quad_alpha(i, n) * fade)
                if alpha <= 10:
                    continue
                col = P["leaf_gold"] if not self.overcharged \
                    else P["gold_hot"]
                g = leaf_surface(3, col)
                g.set_alpha(alpha)
                surface.blit(g, (int(t0.x) - g.get_width() // 2,
                                 int(t0.y) - g.get_height() // 2))
                g.set_alpha(255)


# ============================================================================
# 7.  IMPACT FX
# ============================================================================

class ImpactFX:
    """Satu kejadian benturan: flash, shockwave, serpihan, fragmen, debris.

    Semua digambar prosedural dan berumur pendek; tidak ada state yang
    hidup tanpa batas.  ``kind`` memilih bahasa benturan:
      * "arrow" — panah menancap (hijau + kilat baja + serpihan kayu)
      * "gale"  — hembusan berat Powershot / Focus Fire (pita angin)
      * "vine"  — Shackle mengikat (sulur + daun mengerat)
      * "swing" — sapuan limb busur mendarat (sabit angin)
      * "crit"  — critical strike (putih panas + aksen emas)
    """

    __slots__ = ("x", "y", "angle", "power", "age", "duration",
                 "crit", "active", "color", "kind")

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="arrow"):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = max(0.35, float(power))
        self.age = 0.0
        self.duration = 0.28 + 0.12 * min(2.0, self.power)
        self.crit = bool(crit) or kind == "crit"
        self.active = True
        self.kind = kind
        if kind == "crit":
            self.color = P["fx_white"]
        elif kind == "gale":
            self.color = P["fx_pale"]
        elif kind == "vine":
            self.color = P["vine_light"]
        elif kind == "swing":
            self.color = P["fx_bright"]
        else:
            self.color = P["fx_bright"] if not crit else P["fx_white"]
        if kind == "gale":
            self.duration += 0.16
        elif kind == "vine":
            self.duration += 0.10

    # ------------------------------------------------------------------
    def update(self, dt):
        self.age += dt
        if self.age >= self.duration:
            self.active = False
        return self.active

    # ------------------------------------------------------------------
    def draw(self, surface):
        if not self.active:
            return
        t = self.age / self.duration              # 0 -> 1
        inv = 1.0 - t
        x, y = int(self.x), int(self.y)
        pw = self.power
        deg = math.degrees(self.angle)

        # ── 1. IMPACT FLASH — flare bintang, bukan bola ─────────────
        if t < 0.24:
            ft = 1.0 - t / 0.24
            gr = int((6 + 9 * pw) * (0.5 + 0.5 * ft)) // 2 * 2 + 2
            surface.blit(glow_surface(gr, self.color, 0.5 * ft),
                         (x - gr, y - gr),
                         special_flags=pygame.BLEND_RGB_ADD)
            ln = (14 + 30 * pw) * ft
            fl = _scratch(int(ln * 2 + 8), int(ln * 2 + 8))
            c = int(ln + 4)
            for k in range(6):
                a = self.angle + k * math.pi / 3
                L = ln if k % 2 == 0 else ln * 0.42
                pygame.draw.line(
                    fl, (*P["fx_pale"], int(240 * ft)), (c, c),
                    (c + int(math.cos(a) * L), c + int(math.sin(a) * L)),
                    3 if k % 2 == 0 else 1)
            surface.blit(fl, (x - c, y - c))

        # ── 2. SHOCKWAVE — elips berarah (bukan lingkaran polos) ────
        rr = int((8 + 40 * pw) * (0.25 + 1.05 * t)) // 3 * 3
        th = max(1, int(4 * inv * pw))
        a = int(200 * inv * inv)
        if a > 6 and rr > 4:
            col = self.color if self.kind != "arrow" else P["fx_mid"]
            er = ellipse_ring_surface(rr, max(3, int(rr * 0.58)), th,
                                      col, deg)
            er.set_alpha(a)
            surface.blit(er, (x - er.get_width() // 2,
                              y - er.get_height() // 2))
            er.set_alpha(255)
            rr2 = int(rr * 0.56)
            if rr2 > 4:
                er2 = ellipse_ring_surface(rr2, max(2, int(rr2 * 0.7)),
                                           max(1, th - 1), self.color, deg)
                er2.set_alpha(int(a * 0.75))
                surface.blit(er2, (x - er2.get_width() // 2,
                                   y - er2.get_height() // 2))
                er2.set_alpha(255)

        # ── 3. SPOKE DEBRIS — garis radial memanjang keluar ──────────
        if t < 0.55:
            st = 1.0 - t / 0.55
            r0 = int((6 + 18 * pw) * (0.3 + 1.1 * t))
            for i in range(4):
                ang = self.angle + i * math.pi / 4 + 0.19
                L = (6 + 14 * pw) * st * (1.0 if i % 2 else 0.55)
                pygame.draw.line(
                    surface,
                    _clamp_color(_mix(P["fx_deep"], P["fx_light"], st)),
                    (x + int(math.cos(ang) * r0),
                     y + int(math.sin(ang) * r0)),
                    (x + int(math.cos(ang) * (r0 + L)),
                     y + int(math.sin(ang) * (r0 + L))),
                    2 if i % 2 else 1)

        # ── 4. SABIT ANGIN — busur mengembang searah tumbukan ────────
        # Berbasis LINGKARAN BESAR (arc), BUKAN lerp linear: memberi
        # bobot & arah pada benturan.
        if t < 0.5 and self.kind in ("arrow", "swing", "crit", "gale"):
            st = 1.0 - t / 0.5
            span = 0.60 + 0.55 * pw
            base_r = int(12 + 30 * pw * (0.45 + t))
            buf_r = base_r + 12
            buf = _scratch(buf_r * 2, buf_r * 2)
            c = buf_r
            rect = pygame.Rect(c - base_r, c - base_r,
                               base_r * 2, base_r * 2)
            for col, wdt, al in (
                    (P["fx_dark"], max(3, int(8 * st)), 115),
                    (P["fx_mid"], max(2, int(5 * st)), 195),
                    (P["fx_bright"], max(1, int(3 * st)), 235)):
                try:
                    pygame.draw.arc(buf, (*col, int(al * st)), rect,
                                    -self.angle - span / 2,
                                    -self.angle + span / 2, wdt)
                except (ValueError, pygame.error):    # pragma: no cover
                    pass
            # 3 fragmen busur yang buyar keluar
            for k in (-1, 0, 1):
                ang0 = self.angle - span / 2 + k * 0.14
                ang1 = ang0 + span * 0.86
                rad = base_r + 5 + abs(k) * 6
                rect2 = pygame.Rect(c - rad, c - rad, rad * 2, rad * 2)
                col = P["fx_white"] if k == 0 else P["fx_pale"]
                try:
                    pygame.draw.arc(buf, (*col, int(205 * st)),
                                    rect2, -ang1, -ang0,
                                    2 if k == 0 else 1)
                except (ValueError, pygame.error):    # pragma: no cover
                    pass
            # chevron penunjuk arah di ujung sabit
            lead = base_r + 10
            lx = c + int(math.cos(self.angle) * lead)
            ly = c + int(math.sin(self.angle) * lead)
            for d in (-1, 0, 1):
                a2 = self.angle + d * 0.30
                pygame.draw.line(
                    buf, (*P["fx_pale"], int(200 * st)),
                    (lx - int(math.cos(a2) * 6),
                     ly - int(math.sin(a2) * 6)),
                    (lx + int(math.cos(a2) * 6),
                     ly + int(math.sin(a2) * 6)), 2 if d == 0 else 1)
            surface.blit(buf, (x - c, y - c))
            # aksen emas crit: silang pendek di inti
            if self.crit and t < 0.3:
                ct = 1.0 - t / 0.3
                Lc = int(9 + 11 * pw * ct)
                for da in (0.6, -0.6):
                    pygame.draw.line(
                        surface, (*P["gold_light"], int(205 * ct)),
                        (x - int(math.cos(self.angle + da) * Lc),
                         y - int(math.sin(self.angle + da) * Lc)),
                        (x + int(math.cos(self.angle + da) * Lc),
                         y + int(math.sin(self.angle + da) * Lc)), 1)

        # ── 4b. VINE — karangan sulur mengerat lalu putus ────────────
        if self.kind == "vine" and t < 0.62:
            st = 1.0 - t / 0.62
            rad = int((9 + 22 * pw) * (0.5 + 0.7 * t))
            buf_r = rad + 8
            buf = _scratch(buf_r * 2, buf_r * 2)
            c = buf_r
            for k in range(6):
                a0 = self.angle + k * math.tau / 6
                pts = []
                for j in range(5):
                    s = j / 4.0
                    aa = a0 + math.sin(s * 3.1 + t * 5.0) * 0.5
                    rr2 = rad * (0.25 + 0.75 * s)
                    pts.append((c + math.cos(aa) * rr2,
                                c + math.sin(aa) * rr2 * 0.82))
                pygame.draw.lines(buf, (*P["vine_mid"], int(210 * st)),
                                  False, pts, 2)
                lf = leaf_surface(3, P["vine_light"])
                lf.set_alpha(int(220 * st))
                buf.blit(lf, (int(pts[-1][0]) - lf.get_width() // 2,
                              int(pts[-1][1]) - lf.get_height() // 2))
                lf.set_alpha(255)
            surface.blit(buf, (x - c, y - c))

        # ── 4c. GALE — koridor angin terkompresi (Powershot) ─────────
        if self.kind == "gale" and t < 0.6:
            st = 1.0 - t / 0.6
            for k in range(3):
                rad = int((14 + 40 * pw) * (0.35 + 0.9 * t)) + k * 7
                gs = gust_surface(max(5, rad), P["fx_light"], 0.62,
                                  max(1, 3 - k))
                gs = rotated_cached(("igale", rad, k), gs, -int(deg))
                gs.set_alpha(int(190 * st / (1 + k)))
                surface.blit(gs, (x - gs.get_width() // 2,
                                  y - gs.get_height() // 2),
                             special_flags=pygame.BLEND_RGB_ADD)
                gs.set_alpha(255)

        # ── 5. DAUN TERLEMPAR (tanda tangan Sylara) ──────────────────
        if t < 0.45:
            st = 1.0 - t / 0.45
            for k in range(4):
                a2 = self.angle + (k - 1.5) * 0.42
                d = (10 + 34 * pw) * (0.3 + t)
                lf = leaf_surface(max(2, int(3 * st) + 1),
                                  P["leaf_gold"] if k % 2 else
                                  P["leaf_ember"])
                lf = rotated_cached(("ilf", k, int(st * 4)), lf,
                                    -int(math.degrees(a2)))
                lf.set_alpha(int(225 * st))
                surface.blit(lf, (x + int(math.cos(a2) * d)
                                  - lf.get_width() // 2,
                                  y + int(math.sin(a2) * d)
                                  - lf.get_height() // 2))
                lf.set_alpha(255)


# ============================================================================
# 8.  PROJECTILE  —  panah angin modular
# ============================================================================

class SylaraProjectile:
    """Proyektil visual Sylara dengan lifecycle penuh.

    SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY

    Atribut kontrak: position, velocity, speed, damage, lifetime, target,
    radius, rotation, trail, particles, active.  ``kind``:
      * "arrow" — panah angin serangan dasar
      * "gale"  — panah Powershot (lebih besar, inti putih)
      * "vine"  — panah Shackle (menyeret sulur)
    """

    STATE_TRAVEL = "TRAVEL"
    STATE_IMPACT = "IMPACT"
    STATE_DEAD = "DEAD"

    def __init__(self, x, y, tx, ty, speed=ARROW_SPEED, damage=0,
                 kind="arrow", target=None, particles=None,
                 lifetime=1.5, radius=6.0, homing=0.0, on_hit=None):
        self.position = pygame.Vector2(float(x), float(y))
        d = pygame.Vector2(float(tx) - float(x), float(ty) - float(y))
        if d.length_squared() < 1e-6:
            d = pygame.Vector2(1.0, 0.0)
        self.direction = d.normalize()
        self.speed = float(speed)
        self.velocity = self.direction * self.speed
        self.damage = float(damage)
        self.lifetime = float(lifetime)
        self.max_lifetime = float(lifetime)
        self.target = target
        self.radius = float(radius)
        self.rotation = math.atan2(self.direction.y, self.direction.x)
        self.trail = []                 # [[Vector2, umur], ...]
        self.trail_life = 0.20
        self.particles = particles
        self.active = True
        self.state = self.STATE_TRAVEL
        self.kind = kind
        self.homing = float(homing)
        self.on_hit = on_hit
        self.age = 0.0
        self._impact_t = 0.0
        self._emit = 0.0

    # ------------------------------------------------------------------
    def kill(self, x=None, y=None):
        """Masuk fase IMPACT (bukan langsung hilang) lalu mati."""
        if self.state != self.STATE_TRAVEL:
            return
        if x is not None:
            self.position.update(float(x), float(y))
        self.state = self.STATE_IMPACT
        self._impact_t = 0.0
        if self.on_hit is not None:
            try:
                self.on_hit(self)
            except Exception:              # pragma: no cover
                pass
        if self.particles is not None:
            ang = self.rotation
            self.particles.burst(
                self.position.x, self.position.y,
                3, speed=(90, 240), life=(0.14, 0.34), size=(1, 3),
                colors=(P["fx_pale"], P["fx_bright"], P["leaf_gold"]),
                spread=2.2, direction=ang + math.pi, drag=3.4,
                shape="streak")

    # ------------------------------------------------------------------
    def update(self, dt):
        """Integrasi; return False kalau proyektil harus dibuang."""
        if not self.active:
            return False

        if self.state == self.STATE_IMPACT:
            self._impact_t += dt
            self._age_trail(dt)
            if self._impact_t >= 0.16:
                self.state = self.STATE_DEAD
                self.active = False
                return False
            return True

        self.age += dt
        self.lifetime -= dt
        if self.lifetime <= 0.0:
            self.kill()
            return True

        # ── homing lembut ke target hidup ───────────────────────────
        tgt = self.target
        if self.homing > 0.0 and tgt is not None and \
                getattr(tgt, "alive", False):
            want = pygame.Vector2(float(tgt.x) - self.position.x,
                                  float(tgt.y) - self.position.y)
            if want.length_squared() > 1.0:
                want = want.normalize()
                self.direction += (want - self.direction) * \
                    min(1.0, self.homing * dt)
                if self.direction.length_squared() > 1e-6:
                    self.direction = self.direction.normalize()
                self.velocity = self.direction * self.speed
        self.rotation = math.atan2(self.direction.y, self.direction.x)

        self.position += self.velocity * dt

        # ── trail: rantai posisi (dipakai untuk pita menyempit) ─────
        self.trail.append([pygame.Vector2(self.position), 0.0])
        if len(self.trail) > 10:
            self.trail.pop(0)
        self._age_trail(dt)

        # ── partikel jejak (rate-limited supaya murah) ──────────────
        if self.particles is not None:
            self._emit += dt
            if self._emit >= 0.035:
                self._emit = 0.0
                ang = self.rotation + math.pi + random.uniform(-0.5, 0.5)
                spd = random.uniform(30.0, 90.0)
                tint = P["leaf_gold"] if self.kind != "vine" \
                    else P["vine_light"]
                self.particles.spawn(
                    self.position.x, self.position.y,
                    math.cos(ang) * spd, math.sin(ang) * spd - 8,
                    random.uniform(0.16, 0.34),
                    random.uniform(1.5, 2.8),
                    tint, color_end=P["fx_deepest"], drag=2.6,
                    shape="leaf" if self.kind != "gale" else "gust",
                    rotation=random.random() * math.tau,
                    rotation_speed=random.uniform(-9, 9))

        # ── tumbukan dengan target (radius + radius unit) ───────────
        if tgt is not None and getattr(tgt, "alive", False):
            hit_r = self.radius + float(getattr(tgt, "radius", 12))
            if self.position.distance_squared_to(
                    pygame.Vector2(float(tgt.x), float(tgt.y))) \
                    <= hit_r * hit_r:
                self.kill(tgt.x, tgt.y)
        return True

    def _age_trail(self, dt):
        for s in self.trail:
            s[1] += dt
        if self.trail:
            self.trail = [s for s in self.trail if s[1] < self.trail_life]

    # ------------------------------------------------------------------
    def draw(self, surface):
        """Trail pita -> glow -> shaft -> mata panah -> fletching."""
        n = len(self.trail)
        if n >= 2:
            ux = math.cos(self.rotation + math.pi / 2)
            uy = math.sin(self.rotation + math.pi / 2)
            pts_a = []
            pts_b = []
            for i, (pv, age) in enumerate(self.trail):
                f = (i + 1) / float(n)
                fade = max(0.0, 1.0 - age / self.trail_life)
                wdt = self.radius * 0.62 * f * fade
                pts_a.append((pv.x + ux * wdt, pv.y + uy * wdt))
                pts_b.append((pv.x - ux * wdt, pv.y - uy * wdt))
            poly = pts_a + list(reversed(pts_b))
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            minx, miny = int(min(xs)) - 3, int(min(ys)) - 3
            w = int(max(xs)) - minx + 6
            h = int(max(ys)) - miny + 6
            if 0 < w < 1200 and 0 < h < 1200:
                buf = _scratch(w, h)
                pygame.draw.polygon(
                    buf, (*P["fx_deep"], 120),
                    [(int(px) - minx, int(py) - miny) for px, py in poly])
                pygame.draw.lines(
                    buf, (*P["fx_light"], 175), False,
                    [(int(pv.x) - minx, int(pv.y) - miny)
                     for pv, _a in self.trail], 2)
                surface.blit(buf, (minx, miny))

        if self.state == self.STATE_IMPACT:
            return

        draw_wind_arrow(surface, self.position.x, self.position.y,
                        self.rotation, age=int(self.age * 60),
                        kind=self.kind, radius=self.radius)


class ProjectileSystem:
    """Manajer projectile: spawn, update, draw, auto-cleanup."""

    def __init__(self, particles=None, cap=MAX_PROJECTILES):
        self.projectiles = []
        self.particles = particles
        self.cap = int(cap)

    def count(self):
        return len(self.projectiles)

    def clear(self):
        self.projectiles.clear()

    def spawn(self, x, y, tx, ty, **kw):
        """Buat projectile baru; None kalau sudah mentok cap."""
        if len(self.projectiles) >= self.cap:
            return None
        kw.setdefault("particles", self.particles)
        pr = SylaraProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    def update(self, dt):
        if not self.projectiles:
            return
        self.projectiles = [p for p in self.projectiles if p.update(dt)]

    def draw(self, surface):
        for p in self.projectiles:
            p.draw(surface)


def draw_wind_arrow(surface, px, py, angle=0.0, age=0, kind="arrow",
                    radius=6.0):
    """Renderer panah angin bersama (dipakai juga proyektil ``_entity``).

    Badan panah dibangun berlapis: halo additive -> ekor pita angin ->
    batang kayu 2 nilai -> mata baja bersudut dengan kilau 1 px ->
    fletching hijau -> kilau daun orbit.  Ujung TEPAT di (px, py)
    sehingga tumbukan terasa pas.  Semua bentuk prosedural & di-cache.

    ``kind``: "arrow" (dasar) / "gale" (Powershot) / "vine" (Shackle).
    """
    x, y = int(px), int(py)
    rad = max(3, int(radius))
    ca, sa = math.cos(angle), math.sin(angle)
    deg = int(math.degrees(angle))
    hot = kind == "gale"
    vine = kind == "vine"

    body = P["fx_bright"] if hot else (P["vine_light"] if vine
                                       else P["fx_light"])

    # ── HALO additive di belakang badan ─────────────────────────────
    if glow_allowed():
        g = glow_surface(rad * 2, P["fx_deep"] if not hot else P["fx_dark"],
                         0.5)
        surface.blit(g, (x - rad * 2, y - rad * 2),
                     special_flags=pygame.BLEND_RGB_ADD)

    # ── EKOR: pita angin menyempit ke belakang ──────────────────────
    tail_len = rad * (5.0 if hot else 3.8)
    for i in range(4):
        f = 1.0 - (i + 1) / 5.0
        off = (i + 1) * tail_len / 4.0
        tx = x - ca * off
        ty = y - sa * off
        wob = math.sin(age * 0.32 + i * 1.1) * rad * 0.32
        tx += -sa * wob
        ty += ca * wob
        alpha = int(150 * f * f)
        if alpha <= 5:
            continue
        gs = gust_surface(max(3, int(rad * (0.6 + 0.7 * f))), body,
                          0.5, max(1, rad // 3))
        gs = rotated_cached(("atail", rad, i, kind), gs, -deg)
        gs.set_alpha(alpha)
        surface.blit(gs, (int(tx) - gs.get_width() // 2,
                          int(ty) - gs.get_height() // 2),
                     special_flags=pygame.BLEND_RGB_ADD)
        gs.set_alpha(255)

    # ── BATANG kayu (2 nilai, hard edge) ────────────────────────────
    shaft_len = rad * 2.6
    bx = x - ca * shaft_len
    by = y - sa * shaft_len
    pygame.draw.line(surface, P["shaft_dark"], (int(bx), int(by)), (x, y),
                     max(2, rad // 2))
    pygame.draw.line(surface, P["shaft"],
                     (int(bx - sa), int(by + ca)), (int(x - sa), int(y + ca)),
                     max(1, rad // 3))

    # ── MATA PANAH bersudut, ujung tepat di (px, py) ────────────────
    head = arrowhead_surface(max(5, int(rad * 1.9)), max(2, rad // 2),
                             P["head_dark"] if not hot else P["gold"],
                             P["head_shine"] if not hot else P["gold_hot"])
    head = rotated_cached(("ahead", rad, hot), head, -deg)
    hx = x - int(ca * rad * 0.9)
    hy = y - int(sa * rad * 0.9)
    surface.blit(head, (hx - head.get_width() // 2,
                        hy - head.get_height() // 2))

    # ── FLETCHING hijau di pangkal ──────────────────────────────────
    for side in (-1, 1):
        fs = feather_surface(max(2, rad - 1),
                             P["feather"] if side > 0 else P["feather_dark"])
        fs = rotated_cached(("afeat", rad, side), fs, -deg)
        fx = bx - sa * side * rad * 0.45
        fy = by + ca * side * rad * 0.45
        surface.blit(fs, (int(fx) - fs.get_width() // 2,
                          int(fy) - fs.get_height() // 2))

    # ── KILAU: daun orbit + inti putih ──────────────────────────────
    a = angle + age * 0.16
    lx = x + int(math.cos(a) * (rad + 3))
    ly = y + int(math.sin(a) * (rad + 3) * 0.6)
    lf = leaf_surface(2, P["leaf_gold"] if not vine else P["vine_light"])
    surface.blit(lf, (lx - lf.get_width() // 2, ly - lf.get_height() // 2))
    pygame.draw.rect(surface, P["white"], (x - 1, y - 1, 2, 2))


# ============================================================================
# 9.  SKILL FX  —  lifecycle cast -> charge -> release -> area -> fade
# ============================================================================

class SkillFX:
    """Efek skill Sylara dengan lifecycle bertahap.

    CAST -> CHARGE -> RELEASE -> TRAVEL/AREA -> IMPACT -> AFTER -> FADE

    Q Focus Fire : kipas pita angin dari nock -> halo rumput -> koridor
                   volley panah ke arah hadap (fletching berputar).
    W Windrun    : ledakan daun -> siklon daun 70 px -> lembar angin dash.
    E Shackle    : sulur berdaun dari busur ke target -> mengerat -> putus.
    R Powershot  : getar tali + daun menggulung -> gale tunnel -> sapuan.
    """

    def __init__(self, skill, x, y, particles, radius=None, facing=1,
                 target=None, projectiles=None):
        self.skill = skill
        self.x = float(x)
        self.y = float(y)
        self.particles = particles
        self.projectiles = projectiles
        self.facing = 1 if facing >= 0 else -1
        self.target = target
        self.radius = float(radius) if radius else WORLD_RADIUS.get(skill,
                                                                    90.0)
        self.total = SKILL_TOTAL.get(skill, 1.4)
        self.age = 0.0
        self.active = True
        self.phase = "CAST"
        self._emit = 0.0
        self._released = False
        self._impacted = False

    # ------------------------------------------------------------------
    def progress(self):
        return max(0.0, min(1.0, self.age / max(0.001, self.total)))

    def _set_phase(self):
        p = self.progress()
        if p < 0.12:
            self.phase = "CAST"
        elif p < 0.28:
            self.phase = "CHARGE"
        elif p < 0.42:
            self.phase = "RELEASE"
        elif p < 0.74:
            self.phase = "AREA"
        elif p < 0.88:
            self.phase = "AFTER"
        else:
            self.phase = "FADE"

    # ------------------------------------------------------------------
    def update(self, dt):
        self.age += dt
        if self.age >= self.total:
            self.active = False
            return False
        self._set_phase()
        p = self.progress()
        if self.skill == "q":
            self._update_q(dt, p)
        elif self.skill == "w":
            self._update_w(dt, p)
        elif self.skill == "e":
            self._update_e(dt, p)
        elif self.skill == "r":
            self._update_r(dt, p)
        return True

    # ── Q FOCUS FIRE ──────────────────────────────────────────────
    def _update_q(self, dt, p):
        f = self.facing
        self._emit += dt
        if self._emit < 0.09:
            return
        self._emit = 0.0
        nx = self.x + f * 22
        ny = self.y - 16
        if p < 0.3:
            # CHARGE: daun tersedot ke nock
            self.particles.burst(
                nx + f * random.uniform(20, 60),
                ny + random.uniform(-24, 24), 2,
                speed=(80, 170), life=(0.18, 0.34), size=(2, 3),
                colors=(P["leaf_gold"], P["fx_light"]),
                spread=0.5, direction=math.pi if f > 0 else 0.0,
                drag=1.4, shape="leaf", flutter=0.4)
        else:
            # AREA: koridor volley — fletching berputar maju
            tx = self.x + f * self.radius
            self.particles.stream(
                nx, ny, tx, ny + random.uniform(-10, 10), 3,
                life=(0.22, 0.42), size=(2, 3),
                colors=(P["fx_pale"], P["leaf_gold"], P["fx_bright"]),
                shape="feather")

    # ── W WINDRUN ─────────────────────────────────────────────────
    def _update_w(self, dt, p):
        self._emit += dt
        if self._emit < 0.07:
            return
        self._emit = 0.0
        # siklon daun mengencang seiring waktu
        rad = self.radius * (1.0 - 0.35 * p)
        ang = p * 12.0 + random.uniform(0, math.tau)
        px = self.x + math.cos(ang) * rad
        py = self.y + 18 + math.sin(ang) * rad * 0.42
        self.particles.spawn(
            px, py,
            -math.sin(ang) * 150.0, math.cos(ang) * 60.0 - 24.0,
            random.uniform(0.3, 0.6), random.uniform(2, 4),
            P["leaf_gold"] if random.random() < 0.6 else P["fx_light"],
            color_end=P["fx_deep"], drag=1.2, shape="leaf",
            swirl=2.6, flutter=0.5,
            rotation=random.random() * math.tau,
            rotation_speed=random.uniform(-10, 10))

    # ── E SHACKLE SHOT ────────────────────────────────────────────
    def _update_e(self, dt, p):
        self._emit += dt
        if self._emit < 0.1:
            return
        self._emit = 0.0
        tgt = self.target
        if tgt is None or not getattr(tgt, "alive", False):
            return
        tx = float(getattr(tgt, "x", self.x))
        ty = float(getattr(tgt, "y", self.y))
        # daun merambat sepanjang sulur
        t = random.random()
        px = self.x + (tx - self.x) * t
        py = (self.y - 14) + (ty - self.y + 14) * t
        self.particles.spawn(
            px, py, random.uniform(-24, 24), random.uniform(-34, -8),
            random.uniform(0.28, 0.55), random.uniform(2, 3),
            P["vine_light"], color_end=P["vine_dark"], drag=1.6,
            shape="leaf", flutter=0.6,
            rotation=random.random() * math.tau,
            rotation_speed=random.uniform(-7, 7))

    # ── R POWERSHOT ───────────────────────────────────────────────
    def _update_r(self, dt, p):
        f = self.facing
        nx = self.x + f * 20
        ny = self.y - 18
        if p < 0.55:
            # CHARGE: daun & angin menggulung ke nock, tali bergetar
            self._emit += dt
            if self._emit >= 0.05:
                self._emit = 0.0
                a = random.uniform(0, math.tau)
                d = random.uniform(30, 74)
                self.particles.spawn(
                    nx + math.cos(a) * d, ny + math.sin(a) * d * 0.7,
                    -math.cos(a) * 190.0, -math.sin(a) * 150.0,
                    random.uniform(0.16, 0.32), random.uniform(2, 4),
                    P["fx_bright"] if random.random() < 0.5
                    else P["leaf_gold"],
                    color_end=P["fx_deep"], drag=0.8, shape="gust",
                    swirl=1.5)
            return
        if not self._released:
            self._released = True
            self._release_gale(nx, ny)

    def _release_gale(self, nx, ny):
        """RELEASE: kerucut 5 panah gale + hembusan berat."""
        f = self.facing
        tgt = self.target
        if tgt is not None and getattr(tgt, "alive", False):
            base = math.atan2(float(tgt.y) - ny, float(tgt.x) - nx)
        else:
            base = 0.0 if f > 0 else math.pi
        if self.projectiles is not None:
            for i in range(5):
                ang = base + (i / 4.0 - 0.5) * (math.pi / 6.0)
                dist = self.radius
                self.projectiles.spawn(
                    nx, ny,
                    nx + math.cos(ang) * dist,
                    ny + math.sin(ang) * dist,
                    speed=GALE_SPEED, kind="gale", radius=7.0,
                    lifetime=dist / GALE_SPEED + 0.05,
                    target=tgt if i == 2 else None,
                    homing=2.0 if i == 2 else 0.0)
        self.particles.burst(
            nx, ny, 8, speed=(220, 460), life=(0.2, 0.44), size=(2, 4),
            colors=(P["fx_pale"], P["fx_bright"], P["leaf_gold"]),
            spread=math.pi / 5, direction=base, drag=2.2, shape="streak")
        self.particles.burst(
            nx, ny - 4, 4, speed=(60, 170), life=(0.4, 0.8), size=(2, 4),
            colors=(P["leaf_gold"], P["leaf_ember"]),
            spread=math.pi / 3, direction=base + math.pi, drag=1.4,
            shape="leaf", flutter=0.7)
        shake(4.5, 0.34)
        hit_stop(0.037)

    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        """Lapisan di BAWAH karakter (telegraph tanah, halo rumput)."""
        if not self.active:
            return
        p = self.progress()
        if self.skill == "q":
            self._draw_ground_q(surface, p)
        elif self.skill == "w":
            self._draw_ground_w(surface, p)
        elif self.skill == "e":
            self._draw_ground_e(surface, p)
        elif self.skill == "r":
            self._draw_ground_r(surface, p)

    def _draw_ground_q(self, surface, p):
        f = self.facing
        a = int(150 * (1.0 - abs(p - 0.4) * 1.4))
        if a <= 6:
            return
        gy = int(self.y + 30)
        # koridor tembak: dua garis pandu + chevron berjalan
        length = int(self.radius)
        detail = skill_detail()
        for side in (-1, 1):
            pygame.draw.line(
                surface, (*P["fx_dark"], a),
                (int(self.x), gy + side * 8),
                (int(self.x + f * length), gy + side * 4), 1)
        n_chev = max(3, int(round(5 * detail)))
        for i in range(n_chev):
            t = ((p * 1.6 + i / n_chev) % 1.0)
            cx = int(self.x + f * length * t)
            ch = chevron_surface(5, P["fx_light"], 2)
            if f < 0:
                ch = pygame.transform.flip(ch, True, False)
            ch.set_alpha(int(a * (1.0 - t * 0.5)))
            surface.blit(ch, (cx - ch.get_width() // 2,
                              gy - ch.get_height() // 2))
            ch.set_alpha(255)
        gl = ground_glow_surface(int(34), P["fx_deep"], 0.12)
        gl.set_alpha(a)
        surface.blit(gl, (int(self.x) - gl.get_width() // 2,
                          gy - gl.get_height() // 2))
        gl.set_alpha(255)

    def _draw_ground_w(self, surface, p):
        # halo rumput persis di radius dunia W (70 px)
        a = int(210 * (1.0 - p) ** 0.8)
        if a <= 6:
            return
        gy = int(self.y + 26)
        detail = skill_detail()
        blades = max(10, int(round(20 * detail)))
        halo = grass_halo_surface(int(self.radius), P["fx_mid"],
                                  blades=blades, squash=0.42)
        halo.set_alpha(a)
        surface.blit(halo, (int(self.x) - halo.get_width() // 2,
                            gy - halo.get_height() // 2))
        halo.set_alpha(255)
        segs = max(6, int(round(10 * detail)))
        dr = dashed_ring_surface(int(self.radius * 0.72), 2, P["fx_light"],
                                 segments=segs, span=0.34,
                                 rot_step=p * 400.0)
        dr.set_alpha(int(a * 0.8))
        surface.blit(dr, (int(self.x) - dr.get_width() // 2,
                          gy - int(dr.get_height() * 0.5 * 0.5)))
        dr.set_alpha(255)

    def _draw_ground_e(self, surface, p):
        tgt = self.target
        if tgt is None:
            return
        a = int(190 * (1.0 - p) ** 0.7)
        if a <= 6:
            return
        tx = int(getattr(tgt, "x", self.x))
        ty = int(getattr(tgt, "y", self.y)) + 22
        halo = grass_halo_surface(26, P["vine_mid"], blades=12, squash=0.4)
        halo.set_alpha(a)
        surface.blit(halo, (tx - halo.get_width() // 2,
                            ty - halo.get_height() // 2))
        halo.set_alpha(255)

    def _draw_ground_r(self, surface, p):
        a = int(170 * (1.0 - abs(p - 0.5) * 1.6))
        if a <= 6:
            return
        gy = int(self.y + 30)
        r = int(20 + 26 * min(1.0, p * 2.0))
        gl = ground_glow_surface(r, P["fx_dark"], 0.34)
        gl.set_alpha(a)
        surface.blit(gl, (int(self.x) - gl.get_width() // 2,
                          gy - gl.get_height() // 2))
        gl.set_alpha(255)
        segs = max(5, int(round(8 * skill_detail())))
        dr = dashed_ring_surface(r, 2, P["leaf_gold"], segments=segs,
                                 span=0.3, rot_step=-p * 520.0)
        dr.set_alpha(a)
        surface.blit(dr, (int(self.x) - dr.get_width() // 2,
                          gy - dr.get_height() // 2))
        dr.set_alpha(255)

    # ------------------------------------------------------------------
    def draw_front(self, surface):
        """Lapisan di ATAS karakter (pita angin, sulur, gale)."""
        if not self.active:
            return
        p = self.progress()
        if self.skill == "q":
            self._draw_front_q(surface, p)
        elif self.skill == "w":
            self._draw_front_w(surface, p)
        elif self.skill == "e":
            self._draw_front_e(surface, p)
        elif self.skill == "r":
            self._draw_front_r(surface, p)

    def _draw_front_q(self, surface, p):
        f = self.facing
        nx = int(self.x + f * 22)
        ny = int(self.y - 16)
        a = int(220 * (1.0 - p) ** 0.6)
        if a <= 6:
            return
        # kipas pita angin dari nock (detail ikut beban FX)
        detail = skill_detail()
        n_fans = max(2, int(round(4 * detail)))
        for i in range(n_fans):
            ang = (0.0 if f > 0 else math.pi) + (i - (n_fans - 1) * 0.5) * 0.16
            gs = gust_surface(16 + i * 5, P["fx_light"], 0.55, 2)
            gs = rotated_cached(("qfan", i), gs,
                                -int(math.degrees(ang)))
            gs.set_alpha(int(a * (0.55 + 0.15 * i)))
            surface.blit(gs, (nx - gs.get_width() // 2,
                              ny - gs.get_height() // 2),
                         special_flags=pygame.BLEND_RGB_ADD)
            gs.set_alpha(255)
        # spiral fletching mengorbit nock
        n_feats = max(2, int(round(3 * detail)))
        for i in range(n_feats):
            aa = p * 9.0 + i * math.tau / n_feats
            fx = nx + int(math.cos(aa) * 15)
            fy = ny + int(math.sin(aa) * 11)
            ft = feather_surface(4, P["leaf_gold"])
            ft = rotated_cached(("qfeat", i), ft, -int(math.degrees(aa)))
            ft.set_alpha(a)
            surface.blit(ft, (fx - ft.get_width() // 2,
                              fy - ft.get_height() // 2))
            ft.set_alpha(255)

    def _draw_front_w(self, surface, p):
        f = self.facing
        a = int(190 * (1.0 - p) ** 0.7)
        if a <= 6:
            return
        # lembar angin dash di belakang badan
        for i in range(4):
            off = i * 11 + int((p * 5.0 % 1.0) * 10)
            gs = gust_surface(11 + i * 3, P["fx_bright"], 0.6, 2)
            gs = rotated_cached(("wsheet", i), gs, 0 if f > 0 else 180)
            gs.set_alpha(int(a * (1.0 - i * 0.2)))
            surface.blit(gs, (int(self.x - f * (16 + off))
                              - gs.get_width() // 2,
                              int(self.y - 6 + i * 5)
                              - gs.get_height() // 2),
                         special_flags=pygame.BLEND_RGB_ADD)
            gs.set_alpha(255)

    def _draw_front_e(self, surface, p):
        tgt = self.target
        if tgt is None:
            return
        a = int(230 * (1.0 - p) ** 0.5)
        if a <= 6:
            return
        ax, ay = int(self.x + self.facing * 18), int(self.y - 16)
        bx, by = int(getattr(tgt, "x", ax)), int(getattr(tgt, "y", ay)) - 8
        # sulur hidup: dua untai berkelok + daun di sepanjangnya
        steps = 12
        pts_a = []
        pts_b = []
        for i in range(steps + 1):
            t = i / float(steps)
            px = ax + (bx - ax) * t
            py = ay + (by - ay) * t
            nx = -(by - ay)
            ny = (bx - ax)
            L = max(1.0, math.hypot(nx, ny))
            wob = math.sin(t * 7.0 + p * 14.0) * 7.0 * (1.0 - abs(t - 0.5))
            pts_a.append((px + nx / L * wob, py + ny / L * wob))
            pts_b.append((px - nx / L * wob, py - ny / L * wob))
        for pts, col in ((pts_a, P["vine_mid"]), (pts_b, P["vine_dark"])):
            pygame.draw.lines(surface, (*col, a), False,
                              [(int(q[0]), int(q[1])) for q in pts], 2)
        for i in range(2, steps, 3):
            lf = leaf_surface(3, P["vine_light"])
            lf.set_alpha(a)
            q = pts_a[i]
            surface.blit(lf, (int(q[0]) - lf.get_width() // 2,
                              int(q[1]) - lf.get_height() // 2))
            lf.set_alpha(255)

    def _draw_front_r(self, surface, p):
        f = self.facing
        nx = int(self.x + f * 20)
        ny = int(self.y - 18)
        if p < 0.55:
            # CHARGE: cincin tekanan mengecil + inti memutih
            k = p / 0.55
            r = int(34 * (1.0 - k) + 8)
            rs = ring_surface(r, 2, P["fx_light"])
            rs.set_alpha(int(80 + 150 * k))
            surface.blit(rs, (nx - rs.get_width() // 2,
                              ny - rs.get_height() // 2))
            rs.set_alpha(255)
            if glow_allowed():
                gr = int(6 + 12 * k)
                surface.blit(glow_surface(gr, P["fx_pale"], 0.5 + 0.4 * k),
                             (nx - gr, ny - gr),
                             special_flags=pygame.BLEND_RGB_ADD)
            return
        # RELEASE: gale tunnel terkompresi ke arah tembak
        k = (p - 0.55) / 0.45
        a = int(230 * (1.0 - k))
        if a <= 6:
            return
        for i in range(6):
            d = 26 + i * 30
            rr = int(20 - i * 2)
            if rr <= 2:
                break
            er = ellipse_ring_surface(max(3, rr // 2), rr, 2,
                                      P["fx_bright"], 0)
            er.set_alpha(int(a * (1.0 - i / 7.0)))
            surface.blit(er, (int(nx + f * d) - er.get_width() // 2,
                              ny - er.get_height() // 2),
                         special_flags=pygame.BLEND_RGB_ADD)
            er.set_alpha(255)


# ============================================================================
# 10.  GAME FEEL  —  hit-stop & shake lewat bus bersama combat_feel
# ============================================================================

if _feel is not None:
    HITSTOP = _feel.HITSTOP
    SHAKE = _feel.SHAKE
else:                                                  # pragma: no cover
    class HitStop:
        """Fallback mini (dipakai hanya kalau combat_feel tidak ada)."""

        MIN_SECONDS = 0.03
        MAX_SECONDS = 0.08
        MAX_FRAMES = 5

        def __init__(self):
            self.frames = 0
            self.total = 0

        def trigger(self, seconds=0.045):
            if not HIT_STOP_ENABLED:
                return
            try:
                seconds = float(seconds)
            except (TypeError, ValueError):
                return
            seconds = max(self.MIN_SECONDS, min(self.MAX_SECONDS, seconds))
            frames = max(2, int(round(seconds / FIXED_DT)))
            frames = min(self.MAX_FRAMES, frames)
            if frames > self.frames:
                self.frames = frames
                self.total = frames

        def consume_frame(self):
            if self.frames > 0:
                self.frames -= 1
                return True
            self.total = 0
            return False

        @property
        def active(self):
            return self.frames > 0

        def clear(self):
            self.frames = 0
            self.total = 0

    class ScreenShake:
        """Fallback mini (dipakai hanya kalau combat_feel tidak ada)."""

        def __init__(self):
            self.shake_strength = 0.0
            self.shake_duration = 0.0
            self._max_duration = 0.0001
            self.enabled = True

        def add(self, strength, duration=0.22):
            if not self.enabled:
                return
            strength = float(strength)
            duration = max(0.0, float(duration))
            if strength <= 0.0 or duration <= 0.0:
                return
            if strength <= self.shake_strength and \
                    duration <= self.shake_duration:
                return
            self.shake_strength = max(self.shake_strength, strength)
            self.shake_duration = max(self.shake_duration, duration)
            self._max_duration = max(self._max_duration, self.shake_duration)

        def update(self, dt):
            if self.shake_duration <= 0.0:
                self.shake_strength = 0.0
                return
            self.shake_duration -= dt
            if self.shake_duration <= 0.0:
                self.shake_duration = 0.0
                self.shake_strength = 0.0
                self._max_duration = 0.0001

        @property
        def amount(self):
            if self.shake_duration <= 0.0 or self.shake_strength <= 0.0:
                return 0.0
            return self.shake_strength * (
                self.shake_duration / max(0.0001, self._max_duration))

        def clear(self):
            self.shake_strength = 0.0
            self.shake_duration = 0.0
            self._max_duration = 0.0001

    HITSTOP = HitStop()
    SHAKE = ScreenShake()


def hit_stop(seconds=0.045):
    """API publik: minta hit-stop global (dijepit 0.03 - 0.08 s)."""
    if _feel is not None:
        _feel.hit_stop(seconds)
    else:                                              # pragma: no cover
        HITSTOP.trigger(seconds)


def should_freeze_frame():
    """Dipanggil ``Game.update``: True kalau frame simulasi dibekukan.

    Flag ``SYLARA_FX_ENABLED`` TIDAK menahan freeze karakter lain — ia
    hanya mengatur apakah FX Sylara sendiri ikut jalan.
    """
    if _feel is not None:
        return _feel.should_freeze_frame()
    if not HIT_STOP_ENABLED:                           # pragma: no cover
        return False
    return HITSTOP.consume_frame()


def shake(strength=5.0, duration=0.22):
    """API publik: guncangkan layar (bus bersama + EffectManager)."""
    if not shake_allowed():
        return
    if _feel is not None:
        _feel.shake(strength, duration)
        return
    SHAKE.add(strength, duration)                      # pragma: no cover
    try:
        import __main__
        game = getattr(__main__, "game_instance", None)
        if game is not None and getattr(game, "effects", None) is not None:
            game.effects.shake_screen(strength)
    except Exception:                                  # pragma: no cover
        pass


# ============================================================================
# 11.  ANIMATION STATE  (controller cermin renderer — prioritas + transisi)
# ============================================================================

#: Nama state animasi + prioritasnya (angka besar = lebih penting).
ANIM_PRIORITY = {
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

#: Fase timeline serangan (fraksi 0..1).
#: ANTICIPATION -> WIND-UP -> SWING -> IMPACT -> FOLLOW THROUGH -> RECOVERY
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.12),
    ("WINDUP",       0.12, 0.26),
    ("SWING",        0.26, 0.52),
    ("IMPACT",       0.52, 0.62),
    ("FOLLOW",       0.62, 0.80),
    ("RECOVERY",     0.80, 1.00),
)

#: Titik pendaratan (progress) — dipakai untuk release panah + hitbox.
ATTACK_IMPACT_POINT = 0.52
ATTACK_SWING_END = 0.58

#: Jendela perekaman trail senjata (ARC-BASED swing, bukan lerp linear).
SWING_START = 0.16
SWING_END = 0.88


def attack_phase(progress):
    """Kembalikan nama fase serangan untuk progress 0..1."""
    p = max(0.0, min(1.0, float(progress)))
    for name, a, b in ATTACK_PHASES:
        if a <= p < b:
            return name
    return "RECOVERY"


def _resolve_timeline():
    """Tarik konstanta timeline dari renderer kalau tersedia.

    Renderer adalah satu sumber kebenaran; kalau timeline-nya berubah,
    fase FX ikut berubah tanpa perlu menyentuh modul ini lagi.
    """
    global ATTACK_PHASES, ATTACK_SWING_END, ATTACK_IMPACT_POINT
    global SWING_START, SWING_END
    G = _renderer()
    if G is None:
        return
    try:
        anti = float(G.ATTACK_ANTICIPATION_END)
        windup = float(G.ATTACK_WINDUP_END)
        swing_end = float(G.ATTACK_SWING_END)
        impact_end = float(G.ATTACK_IMPACT_END)
        follow = float(G.ATTACK_FOLLOW_END)
        impact = float(G.ATTACK_IMPACT_FRAME)
        w0, w1 = G.SWING_WINDOW
    except Exception:                      # pragma: no cover
        return
    if not (0.0 < anti < windup < swing_end < impact_end < follow < 1.0):
        return
    ATTACK_SWING_END = swing_end
    ATTACK_IMPACT_POINT = impact
    SWING_START = float(w0)
    SWING_END = float(w1)
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, anti),
        ("WINDUP",       anti, windup),
        ("SWING",        windup, swing_end),
        ("IMPACT",       swing_end, impact_end),
        ("FOLLOW",       impact_end, follow),
        ("RECOVERY",     follow, 1.00),
    )


_resolve_timeline()


# ============================================================================
# 12.  GEOMETRI BUSUR  —  jembatan ke pose renderer (satu sumber kebenaran)
# ============================================================================

def render_scale(hero):
    """Skala canvas->layar untuk hero ini (fallback: skala pipeline)."""
    scale = float(getattr(hero, "_render_scale", 0.0) or 0.0)
    if scale <= 0.02:
        try:
            from heroes import _get_hero_scale
            scale = float(_get_hero_scale(
                getattr(hero, "hero_type", "sylara")))
        except Exception:                  # pragma: no cover
            scale = 1.0
    return scale


def bow_points(hero, x=None, y=None, progress=None, action=None):
    """Posisi LAYAR (grip, ujung limb atas, nock) busur Sylara.

    Memakai geometri lokal renderer (``_bow_geometry``) lalu dikonversi
    ke skala layar lewat ``RIG_SCALE`` x ``_render_scale``, sehingga
    trail menempel PERSIS di kayu busur — bukan di perkiraan.
    Return ((grip, tip, nock), action).
    """
    G = _renderer()
    h = hero
    px = float(getattr(h, "x", 0.0)) if x is None else float(x)
    py = float(getattr(h, "y", 0.0)) if y is None else float(y)
    f = 1.0 if getattr(h, "facing",
                       getattr(h, "direction", 1)) >= 0 else -1.0
    s = render_scale(h)
    phase = float(getattr(h, "pulse", 0.0))
    ap = float(getattr(h, "_sy_attack_progress", 0.0)) \
        if progress is None else float(progress)

    if action is None:
        if getattr(h, "_sy_attack_active", False) or progress is not None:
            action = "swing" if getattr(h, "_sy_swing_mode", False) \
                else "attack"
        elif getattr(h, "_moving_cached", False):
            action = "walk"
        else:
            action = "idle"

    if G is not None:
        try:
            geo = G._bow_geometry(phase, action, ap)
            grip_l = geo["grip"]
            tip_l = geo["tip_up"]
            nock_l = geo["nock"]
            rs = float(getattr(G, "RIG_SCALE", 1.52))
        except Exception:                  # pragma: no cover - tool minimal
            grip_l, tip_l, nock_l = (17, -5), (30, -25), (15, -8)
            rs = 1.52
    else:                                  # pragma: no cover
        grip_l, tip_l, nock_l = (17, -5), (30, -25), (15, -8)
        rs = 1.52

    def to_screen(p_):
        return (px + p_[0] * rs * f * s, py + p_[1] * rs * s)

    return (to_screen(grip_l), to_screen(tip_l), to_screen(nock_l)), action


def swing_hitbox(hero, x=None, y=None):
    """Hitbox sapuan Sylara (kotak depan) di ruang LAYAR.

    Jangkauan = ``_NS_sylara.SWING_RANGE`` (dunia) di depan karakter;
    tinggi mengikuti skala sprite supaya sejajar dengan badan.
    """
    G = _renderer()
    h = hero
    px = float(getattr(h, "x", 0.0)) if x is None else float(x)
    py = float(getattr(h, "y", 0.0)) if y is None else float(y)
    f = 1.0 if getattr(h, "facing",
                       getattr(h, "direction", 1)) >= 0 else -1.0
    reach = float(getattr(G, "SWING_RANGE", 64.0)) if G is not None else 64.0
    height = 66.0
    left = px if f > 0 else px - reach
    return pygame.Rect(int(left), int(py - height * 0.62),
                       int(reach), int(height))


# ============================================================================
# 13.  DIRECTOR  —  satu instance per unit Sylara
# ============================================================================

class SylaraFXDirector:
    """Pengikat seluruh subsistem FX untuk SATU unit Sylara.

    Bertanggung jawab atas: animation state machine, timeline serangan
    60 Hz, trail sapuan busur, pelepasan panah, partikel idle/langkah,
    skill FX Q/W/E/R, impact, hit flash, dan pembersihan.
    """

    def __init__(self, hero):
        self.hero = hero
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.projectiles = ProjectileSystem(self.particles, MAX_PROJECTILES)
        self.trail = SwingTrail()
        self.impacts = []
        self.skills = []

        self.time = 0.0
        self.frames = 0
        self.state = "IDLE"
        self.prev_state = "IDLE"
        self.state_time = 0.0
        self.anim_phase = "IDLE"
        self.attack_progress = 0.0
        self.hit_flash = 0.0

        self._attack_live = False
        self._attack_frame = 0
        self._prev_timer = -1
        self._arrow_released = False
        self._swing_seen = False
        self._skill_seen = None
        self._moving = False
        self._last_x = None
        self._last_y = None
        self._last_hp = None
        self._was_alive = True
        self._emit_idle = 0.0
        self._step_acc = 0.0
        self._last_ms = None

        # timer gameplay yang dipantau (edge-triggered)
        self._focus_seen = 0
        self._windrun_seen = 0
        self._shackle_seen = 0
        self._powershot_seen = 0

    # ------------------------------------------------------------------
    # Event
    # ------------------------------------------------------------------
    def on_swing_start(self, x, y, facing):
        """Ayunan/tarikan dimulai: bersihkan trail + debu kaki."""
        self.trail.reset()
        self.trail.overcharged = bool(getattr(self.hero, "active_skill",
                                              None))
        self.particles.burst(
            x + facing * 6, y + 34, 4, speed=(40, 110), life=(0.2, 0.4),
            size=(2, 3), colors=(P["dust"], P["dust_light"]),
            spread=1.6, direction=-math.pi / 2 - facing * 0.5,
            gravity=210.0, drag=2.0, shape="pixel", back=True)

    def on_swing_end(self):
        """Jendela ayunan selesai — trail dibiarkan memudar sendiri."""
        self.trail.active = False

    def on_arrow_release(self, x, y, facing):
        """Frame IMPACT: tali dilepas -> flash, panah, daun terhempas."""
        h = self.hero
        tgt = getattr(h, "target", None)
        (_grip, tip, nock), _act = bow_points(h, x, y,
                                              progress=self.attack_progress)
        if tgt is not None and getattr(tgt, "alive", False):
            ang = math.atan2(float(tgt.y) - nock[1], float(tgt.x) - nock[0])
        else:
            ang = 0.0 if facing > 0 else math.pi

        swing_mode = bool(getattr(h, "_sy_swing_mode", False))
        if swing_mode:
            # Sapuan melee: tidak melepas panah — hentakan angin di ujung
            # limb + hit-stop ringan supaya benturan terasa.
            self.impacts.append(ImpactFX(tip[0], tip[1], ang, 1.0,
                                         False, "swing"))
            if len(self.impacts) > MAX_IMPACTS:
                self.impacts.pop(0)
            self.particles.burst(
                tip[0], tip[1], 4, speed=(140, 320), life=(0.14, 0.34),
                size=(1, 3),
                colors=(P["fx_pale"], P["fx_bright"], P["leaf_gold"]),
                spread=1.5, direction=ang, drag=3.4, shape="streak")
            shake(2.0, 0.16)
            hit_stop(0.020)
            return

        # Tembakan: proyektil visual + kilat busur
        dist = 360.0
        if tgt is not None and getattr(tgt, "alive", False):
            dist = max(40.0, math.hypot(float(tgt.x) - nock[0],
                                        float(tgt.y) - nock[1]))
        powered = getattr(h, "active_skill", None) in ("q", "r")
        self.projectiles.spawn(
            nock[0], nock[1],
            nock[0] + math.cos(ang) * dist,
            nock[1] + math.sin(ang) * dist,
            speed=GALE_SPEED if powered else ARROW_SPEED,
            kind="gale" if powered else "arrow",
            radius=7.0 if powered else 5.5,
            target=tgt, homing=3.0,
            lifetime=min(1.4, dist / ARROW_SPEED + 0.35))
        self.particles.burst(
            nock[0], nock[1], 4, speed=(150, 340), life=(0.12, 0.3),
            size=(1, 3),
            colors=(P["fx_pale"], P["fx_bright"], P["string"]),
            spread=0.9, direction=ang, drag=3.8, shape="streak")
        self.particles.burst(
            nock[0], nock[1], 4, speed=(50, 150), life=(0.3, 0.65),
            size=(2, 4), colors=(P["leaf_gold"], P["leaf_ember"]),
            spread=2.0, direction=ang + math.pi, drag=1.4,
            shape="leaf", flutter=0.6)
        shake(1.3, 0.12)

    def on_cast(self, x, y, skill):
        """Skill dilepas: FX lifecycle + hentakan awal khas ranger."""
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        h = self.hero
        f = 1 if getattr(h, "facing", getattr(h, "direction", 1)) >= 0 \
            else -1
        target = None
        radius = None
        if skill == "q":
            radius = float(getattr(h, "skill_range", 0) or 0) or None
            target = getattr(h, "target", None)
        elif skill == "e":
            target = getattr(h, "_shackle_target", None) or \
                getattr(h, "target", None)
            radius = WORLD_RADIUS["e"]
        elif skill == "r":
            target = getattr(h, "target", None)
            radius = WORLD_RADIUS["r"]
        fx = SkillFX(skill, x, y, self.particles, radius, facing=f,
                     target=target, projectiles=self.projectiles)
        self.skills.append(fx)
        self.trail.overcharged = True

        if skill == "q":
            # Focus Fire: kipas angin dari nock + hentakan ringan
            self.particles.burst(
                x + f * 20, y - 16, 5, speed=(140, 300),
                life=(0.16, 0.36), size=(1, 3),
                colors=(P["fx_pale"], P["fx_bright"], P["leaf_gold"]),
                spread=0.8, direction=0.0 if f > 0 else math.pi,
                drag=3.0, shape="streak")
            shake(2.0, 0.18)
            hit_stop(0.020)
        elif skill == "w":
            # Windrun: ledakan daun melingkar + debu tanah
            self.particles.ring(
                x, y + 20, WORLD_RADIUS["w"] * 0.85, 14,
                life=(0.35, 0.7), size=(2, 4),
                colors=(P["leaf_gold"], P["fx_light"], P["leaf_ember"]),
                speed=(80, 190), squash=0.45, shape="leaf", swirl=2.2)
            self.particles.burst(
                x, y + 30, 4, speed=(50, 140), life=(0.3, 0.6),
                size=(2, 4), colors=(P["dust"], P["dust_light"]),
                spread=2.6, direction=-math.pi / 2, gravity=230.0,
                drag=1.6, shape="pixel", back=True)
            shake(2.5, 0.22)
        elif skill == "e":
            # Shackle: sulur meledak di target
            tgt = fx.target
            tx = float(getattr(tgt, "x", x + f * 90.0))
            ty = float(getattr(tgt, "y", y))
            self.particles.burst(
                tx, ty - 6, 5, speed=(60, 170), life=(0.25, 0.55),
                size=(2, 3),
                colors=(P["vine_light"], P["vine_mid"], P["leaf_gold"]),
                spread=math.tau, drag=2.0, shape="leaf", swirl=1.8,
                flutter=0.5)
            self.impacts.append(ImpactFX(tx, ty - 8, 0.0, 1.1, False,
                                         "vine"))
            shake(1.7, 0.18)
        elif skill == "r":
            # Powershot: tarikan tekanan (release-nya di SkillFX)
            self.particles.burst(
                x + f * 18, y - 18, 5, speed=(40, 120),
                life=(0.24, 0.5), size=(2, 4),
                colors=(P["fx_light"], P["leaf_gold"]),
                spread=math.tau, drag=0.9, shape="gust", swirl=2.0)
            shake(1.5, 0.2)

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="arrow"):
        """Benturan mengenai target: flash, spark, debris, shake, hit-stop."""
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind))

        n = int(8 + 6 * min(2.0, power)) + (5 if crit else 0)
        if kind == "vine":
            cols = (P["vine_light"], P["vine_mid"], P["leaf_gold"])
            shp = "leaf"
        elif kind == "gale":
            cols = (P["fx_pale"], P["fx_bright"], P["fx_light"])
            shp = "gust"
        else:
            cols = (P["fx_pale"], P["fx_bright"], P["leaf_gold"])
            shp = "streak"
        self.particles.burst(
            x, y, n, speed=(110, 330), life=(0.16, 0.42),
            size=(1, 3), colors=cols,
            spread=2.4, direction=angle, drag=3.6, shape=shp)
        # serpihan kayu/baja panah
        self.particles.burst(
            x, y, 5 + (3 if crit else 0),
            speed=(70, 190), life=(0.28, 0.62), size=(2, 4),
            colors=(P["wood_shine"], P["wood_mid"], P["head"]),
            gravity=460.0, drag=1.1, shape="splinter",
            rotation_speed=(-16.0, 16.0))
        # daun yang terlempar dari benturan
        self.particles.burst(
            x, y - 4, 4, speed=(40, 130), life=(0.35, 0.75), size=(2, 4),
            colors=(P["leaf_gold"], P["leaf_ember"]),
            spread=2.4, direction=angle, drag=1.3, shape="leaf",
            flutter=0.7)
        self.particles.burst(
            x, y + 6, 3, speed=(20, 60), life=(0.3, 0.55), size=(3, 5),
            colors=(P["smoke"], P["dust"]),
            gravity=-26.0, drag=1.6, shape="smoke", back=True)

        shake(3.2 + 3.0 * min(2.0, power) + (2.6 if crit else 0.0),
              0.16 + 0.08 * min(2.0, power))
        hit_stop(0.034 + 0.02 * min(1.5, power) + (0.014 if crit else 0.0))

    def on_hurt(self, amount=1.0):
        """Sylara terkena serangan: hit flash + daun buyar."""
        self.hit_flash = 0.15
        try:
            self.hero._sy_hurt_frames = 8
        except Exception:                  # pragma: no cover
            pass
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        self.particles.burst(
            hx, hy - 14, 3, speed=(70, 190), life=(0.18, 0.36),
            size=(1, 3), colors=(P["fx_bright"], P["leaf_gold"]),
            drag=3.0, shape="streak")

    def on_death(self):
        """Sylara tumbang: daun berhamburan + cape runtuh + debu."""
        h = self.hero
        x = float(getattr(h, "x", 0.0))
        y = float(getattr(h, "y", 0.0))
        self.particles.burst(
            x, y - 18, 7, speed=(50, 180), life=(0.5, 1.05), size=(2, 4),
            colors=(P["leaf_gold"], P["leaf_ember"], P["fx_light"]),
            spread=math.tau, drag=1.4, shape="leaf", swirl=1.6,
            flutter=0.8, fade_pow=1.4)
        self.particles.burst(
            x, y - 34, 4, speed=(40, 130), life=(0.5, 0.95), size=(2, 4),
            colors=(P["fx_light"], P["fx_dark"]),
            spread=math.tau, drag=1.6, shape="gust")
        self.particles.burst(
            x, y + 30, 4, speed=(30, 95), life=(0.5, 0.9), size=(3, 6),
            colors=(P["dust"], P["smoke"]),
            spread=2.6, direction=-math.pi / 2, gravity=-16.0,
            drag=1.5, shape="smoke", back=True)
        self.trail.reset()
        shake(2.2, 0.32)

    # ------------------------------------------------------------------
    # State machine (prioritas + transisi)
    # ------------------------------------------------------------------
    def _desired_state(self):
        h = self.hero
        if not getattr(h, "alive", True):
            return "DEATH"
        if self.hit_flash > 0.08:
            return "HURT"
        skill = getattr(h, "active_skill", None)
        if skill == "r" or getattr(h, "_powershot_charging", False):
            return "SPECIAL"
        if skill in ("q", "w", "e"):
            return "SKILL"
        if int(getattr(h, "_shackle_timer", 0) or 0) > 0 or \
                int(getattr(h, "_focus_fire_timer", 0) or 0) > 0:
            return "SKILL"
        if getattr(h, "_windrun_active", False):
            return "RUN"
        if self._attack_live:
            ph = attack_phase(self.attack_progress)
            if ph in ("SWING", "IMPACT"):
                return "SWING" if getattr(h, "_sy_swing_mode", False) \
                    else "ATTACK"
            if ph in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            return "ATTACK"
        if self._moving:
            return "WALK"
        return "IDLE"

    def _update_state(self, dt):
        want = self._desired_state()
        if want != self.state:
            cur_p = ANIM_PRIORITY.get(self.state, 0)
            new_p = ANIM_PRIORITY.get(want, 0)
            locked = self.state == "DEATH" and \
                not getattr(self.hero, "alive", True)
            if not locked and (new_p >= cur_p or self.state_time > 0.05):
                self.prev_state = self.state
                self.state = want
                self.state_time = 0.0
        self.state_time += dt
        self.anim_phase = attack_phase(self.attack_progress) \
            if self._attack_live else self.state

    # ------------------------------------------------------------------
    # Attack timeline 60 Hz  (sumber: attack_timer gameplay, BUKAN pose
    # ter-cache — progress tetap halus walau sprite dipakai ulang)
    # ------------------------------------------------------------------
    def _update_attack_timeline(self):
        h = self.hero
        cd = max(2, int(getattr(h, "attack_cooldown", 52)))
        timer = int(getattr(h, "attack_timer",
                            getattr(h, "timer", 0)) or 0)
        prev = self._prev_timer
        # Serangan baru = timer NAIK (tahan berapa pun langkah simulasi
        # yang terlewat antar-gambar).
        if prev < 0:
            # Pengamatan pertama.  Kalau timer sudah berjalan, director
            # dibuat SETELAH serangan dimulai — gabung di tengah saja
            # daripada membatalkan seluruh animasi.
            if timer > 0:
                self._attack_live = True
                self._arrow_released = False
        elif timer > prev:
            self._attack_live = True
            self._attack_frame = 0
            self._arrow_released = False
        if self._attack_live:
            self._attack_frame = max(0, cd - timer)
            self.attack_progress = min(1.0, self._attack_frame
                                       / max(1, cd - 1))
            if timer <= 0:
                self._attack_live = False
                self.attack_progress = 0.0
        else:
            self.attack_progress = 0.0
        self._prev_timer = timer

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt):
        """Satu langkah FX (dipanggil ``tick()`` dengan dt nyata)."""
        if dt <= 0.0:
            return
        h = self.hero
        self.time += dt
        self.frames += 1
        hx = float(getattr(h, "x", 0.0))
        hy = float(getattr(h, "y", 0.0))

        # ── deteksi gerak ───────────────────────────────────────────
        if self._last_x is None:
            self._last_x, self._last_y = hx, hy
            self._moving = False
        else:
            self._moving = (abs(hx - self._last_x)
                            + abs(hy - self._last_y)) > 0.3
            self._last_x, self._last_y = hx, hy
        try:
            h._moving_cached = self._moving
        except Exception:                      # pragma: no cover
            pass

        # ── deteksi damage (tanpa bergantung pada hook eksternal) ────
        hp = float(getattr(h, "hp", 0.0) or 0.0)
        if self._last_hp is not None and hp < self._last_hp - 0.01:
            self.on_hurt((self._last_hp - hp)
                         / max(1.0, float(getattr(h, "max_hp", 1.0))))
        self._last_hp = hp

        # ── deteksi kematian ────────────────────────────────────────
        alive = bool(getattr(h, "alive", True))
        if self._was_alive and not alive:
            self.on_death()
        self._was_alive = alive

        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)

        self._update_attack_timeline()
        self._update_state(dt)

        facing = 1 if getattr(h, "facing",
                              getattr(h, "direction", 1)) >= 0 else -1

        # ── skill cast detection (edge-triggered, dua sumber) ────────
        # active_skill = jendela visual pipeline; timer mentah = jendela
        # gameplay.  Edge pada salah satunya cukup untuk memicu cast.
        skill = getattr(h, "active_skill", None)
        if skill != self._skill_seen:
            if skill in ("q", "w", "e", "r"):
                self.on_cast(hx, hy, skill)
            self._skill_seen = skill

        foc = int(getattr(h, "_focus_fire_timer", 0) or 0)
        if foc > self._focus_seen and self._focus_seen == 0 and skill != "q":
            self.on_cast(hx, hy, "q")
        self._focus_seen = foc

        wr = int(getattr(h, "_windrun_timer", 0) or 0)
        if wr > self._windrun_seen and self._windrun_seen == 0 and \
                skill != "w":
            self.on_cast(hx, hy, "w")
        self._windrun_seen = wr

        sh = int(getattr(h, "_shackle_timer", 0) or 0)
        if sh > self._shackle_seen and self._shackle_seen == 0 and \
                skill != "e":
            self.on_cast(hx, hy, "e")
        self._shackle_seen = sh

        ps = int(getattr(h, "_powershot_timer", 0) or 0)
        if ps > self._powershot_seen and self._powershot_seen == 0 and \
                skill != "r":
            self.on_cast(hx, hy, "r")
        self._powershot_seen = ps

        # ── swing detection (edge-triggered pada jendela ayunan) ─────
        ap = self.attack_progress
        swinging = self._attack_live and SWING_START <= ap <= SWING_END
        if swinging and not self._swing_seen:
            self.on_swing_start(hx, hy, facing)
        elif not swinging and self._swing_seen:
            self.on_swing_end()
        self._swing_seen = swinging

        # ── pelepasan panah / benturan sapuan di titik IMPACT ────────
        if self._attack_live and not self._arrow_released and \
                ap >= ATTACK_IMPACT_POINT:
            self._arrow_released = True
            self.on_arrow_release(hx, hy, facing)

        # ── rekam posisi busur saat swing -> trail ───────────────────
        if alive and swinging:
            (grip, tip, _nock), _action = bow_points(h, progress=ap)
            # Pita menempati bagian LUAR limb (ujung + sedikit badan
            # busur) — bahasa ranger: udara terbelah oleh limb, bukan
            # bilah tebal.
            inner = (grip[0] + (tip[0] - grip[0]) * 0.30,
                     grip[1] + (tip[1] - grip[1]) * 0.30)
            outer = (grip[0] + (tip[0] - grip[0]) * 1.22,
                     grip[1] + (tip[1] - grip[1]) * 1.22)
            self.trail.push(inner, outer)

        # ── emisi idle: daun & serbuk angin melayang (rate-limited) ──
        if alive and not self._attack_live and not self.skills:
            self._emit_idle += dt
            if self._emit_idle >= 0.19:
                self._emit_idle = 0.0
                self.particles.spawn(
                    hx + random.uniform(-18, 18),
                    hy + random.uniform(20, 44),
                    random.uniform(-14, 14), -random.uniform(10, 28),
                    random.uniform(0.6, 1.2), random.uniform(1, 2),
                    P["leaf_gold"] if random.random() < 0.4
                    else P["fx_dark"],
                    color_end=P["fx_deepest"], drag=1.0,
                    shape="leaf", back=True, flutter=0.4,
                    rotation=random.random() * math.tau,
                    rotation_speed=random.uniform(-4, 4))

        # ── debu langkah saat bergerak (foot dust, rate-limited) ─────
        if alive and self._moving and not self._attack_live:
            self._step_acc += dt
            rate = 0.12 if getattr(h, "_windrun_active", False) else 0.18
            if self._step_acc >= rate:
                self._step_acc = 0.0
                self.particles.spawn(
                    hx - facing * 8 + random.uniform(-3, 3),
                    hy + 40, -facing * random.uniform(16, 40),
                    -random.uniform(4, 18),
                    random.uniform(0.22, 0.42), random.uniform(2, 3),
                    P["dust"], color_end=P["smoke"], gravity=60.0,
                    drag=2.4, shape="pixel", back=True)

        # ── pembersihan skill yang timer-nya MACET ───────────────────
        # Pagar anti-beku: timer gameplay SELALU berkurang tiap langkah
        # simulasi.  Kalau hero tewas di tengah skill, ``Hero.update``
        # berhenti jalan dan timer membeku > 0 — tanpa pagar ini, emisi
        # skill akan hidup tanpa batas di mayat.
        focus_stuck = self._guard_stuck("focus", foc, dt)
        wind_stuck = self._guard_stuck("wind", wr, dt)
        shack_stuck = self._guard_stuck("shack", sh, dt)
        if not alive or focus_stuck > 15.0 or wind_stuck > 15.0 or \
                shack_stuck > 15.0:
            for fx in self.skills:
                fx.active = False

        self.trail.update(dt)
        self.particles.update(dt)
        self.projectiles.update(dt)

        if self.impacts:
            self.impacts = [i for i in self.impacts if i.update(dt)]
        if self.skills:
            # ``update`` mengembalikan False saat umurnya habis; ``active``
            # bisa dimatikan lebih awal oleh pagar anti-beku di atas.
            self.skills = [s for s in self.skills if s.update(dt) and
                           s.active]
        if not self.skills:
            self.trail.overcharged = False

    def _guard_stuck(self, name, value, dt):
        """Versi instance dari pagar anti-beku (state per director)."""
        last = getattr(self, "_" + name + "_last", None)
        acc = getattr(self, "_" + name + "_acc", 0.0)
        if last is None or value < last:
            acc = 0.0
        else:
            acc += dt
        setattr(self, "_" + name + "_last", value)
        setattr(self, "_" + name + "_acc", acc)
        return acc

    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        """GROUND FX + BACK PARTICLES (di bawah karakter)."""
        for s in self.skills:
            s.draw_ground(surface)
        self.particles.draw(surface, layer="back")

    def draw_front(self, surface):
        """ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES -> SKILL/IMPACT."""
        self.trail.draw(surface)
        self.projectiles.draw(surface)
        self.particles.draw(surface, layer="front")
        for s in self.skills:
            s.draw_front(surface)
        for i in self.impacts:
            i.draw(surface)
        if self.hit_flash > 0.0:
            self._draw_hit_flash(surface)
        if DEBUG_CHARACTER:
            draw_debug_overlay(surface, self)

    def _draw_hit_flash(self, surface):
        h = self.hero
        r = int(16 + 26 * (self.hit_flash / 0.15))
        g = glow_surface(r, P["fx_bright"], self.hit_flash / 0.15 * 0.7)
        surface.blit(g, (int(getattr(h, "x", 0)) - r,
                         int(getattr(h, "y", 0)) - r - 6),
                     special_flags=pygame.BLEND_RGB_ADD)

    # ------------------------------------------------------------------
    def clear(self):
        """Kosongkan seluruh subsistem (dipanggil saat di-release)."""
        self.particles.clear()
        self.projectiles.clear()
        self.trail.reset()
        self.impacts.clear()
        self.skills.clear()

    def stats(self):
        """Ringkasan untuk debug/HUD."""
        return {
            "state": self.state,
            "phase": self.anim_phase,
            "attack_t": round(self.attack_progress, 3),
            "particles": self.particles.count(),
            "projectiles": self.projectiles.count(),
            "impacts": len(self.impacts),
            "skills": len(self.skills),
            "trail": len(self.trail.points),
        }


# ============================================================================
# 14.  DEBUG OVERLAY  (DEBUG_CHARACTER)
# ============================================================================

_DEBUG_FONT = None


def _debug_font():
    global _DEBUG_FONT
    if _DEBUG_FONT is None:
        try:
            _DEBUG_FONT = pygame.font.Font(None, 15)
        except Exception:                  # pragma: no cover
            _DEBUG_FONT = False
    return _DEBUG_FONT or None


def draw_debug_overlay(surface, director):
    """Hitbox, hurtbox, attack range, state, timer, FPS, particle count."""
    h = director.hero
    x = int(getattr(h, "x", 0))
    y = int(getattr(h, "y", 0))
    rad = int(getattr(h, "radius", 16))
    rng = int(getattr(h, "range", 130))

    # attack range + jangkauan sapuan melee
    pygame.draw.circle(surface, (255, 190, 90), (x, y), rng, 1)
    G = _renderer()
    swing_r = int(getattr(G, "SWING_RANGE", 64.0)) if G is not None else 64
    pygame.draw.circle(surface, (255, 120, 120), (x, y), swing_r, 1)
    # hurtbox
    pygame.draw.circle(surface, (90, 220, 255), (x, y), rad, 1)
    # hitbox serangan (kotak depan saat jendela aktif)
    if director.anim_phase in ("SWING", "IMPACT"):
        pygame.draw.rect(surface, (255, 230, 90), swing_hitbox(h), 1)
    # radius AOE gameplay saat aktif
    if int(getattr(h, "_windrun_timer", 0) or 0) > 0:
        pygame.draw.circle(surface, (150, 240, 150), (x, y + 22),
                           int(WORLD_RADIUS["w"]), 1)
    if int(getattr(h, "_focus_fire_timer", 0) or 0) > 0:
        f = 1 if getattr(h, "facing", getattr(h, "direction", 1)) >= 0 \
            else -1
        pygame.draw.line(surface, (210, 255, 175), (x, y),
                         (int(x + f * WORLD_RADIUS["q"]), y), 1)
    tgt = getattr(h, "_shackle_target", None)
    if tgt is not None and int(getattr(h, "_shackle_timer", 0) or 0) > 0:
        pygame.draw.line(surface, (128, 190, 96), (x, y - 14),
                         (int(getattr(tgt, "x", x)),
                          int(getattr(tgt, "y", y))), 1)
    # anchor busur (debug geometri trail)
    try:
        (grip, tip, nock), _act = bow_points(h)
        pygame.draw.line(surface, (120, 255, 150),
                         (int(grip[0]), int(grip[1])),
                         (int(tip[0]), int(tip[1])), 1)
        pygame.draw.rect(surface, (255, 255, 120),
                         (int(nock[0]) - 2, int(nock[1]) - 2, 4, 4), 1)
    except Exception:                      # pragma: no cover
        pass
    # projectile collision
    for pr in director.projectiles.projectiles:
        pygame.draw.circle(surface, (255, 255, 120),
                           (int(pr.position.x), int(pr.position.y)),
                           int(pr.radius), 1)

    font = _debug_font()
    if font is None:
        return
    try:
        fps = int(pygame.time.Clock().get_fps())
    except Exception:                      # pragma: no cover
        fps = 0
    st = director.stats()
    lines = [
        "SYLARA  %s / %s" % (st["state"], st["phase"]),
        "atkT %.2f  swing %s  skill %s" % (
            st["attack_t"], bool(getattr(h, "_sy_swing_mode", False)),
            getattr(h, "active_skill", None)),
        "foc %d  wind %d  shack %d  pow %d" % (
            int(getattr(h, "_focus_fire_timer", 0) or 0),
            int(getattr(h, "_windrun_timer", 0) or 0),
            int(getattr(h, "_shackle_timer", 0) or 0),
            int(getattr(h, "_powershot_timer", 0) or 0)),
        "part %d  proj %d  imp %d  trail %d" % (
            st["particles"], st["projectiles"], st["impacts"],
            st["trail"]),
        "shake %.1f  stop %d  fps %d" % (
            SHAKE.amount, HITSTOP.frames, fps),
    ]
    for i, txt in enumerate(lines):
        img = font.render(txt, True, (210, 255, 200))
        surface.blit(img, (x - 60, y - 108 + i * 13))


# ============================================================================
# 15.  API MODUL  —  registry, tick, hook render
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Sylara."""
    _sync_palette()
    d = getattr(hero, "_sy_fx", None)
    if d is None:
        d = SylaraFXDirector(hero)
        try:
            hero._sy_fx = d
        except Exception:                  # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:           # jangkar tua dibuang
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    """Lepas director dari registry DAN penanda milik-nya di unit.

    Penting: kalau penanda ``_sy_live_fx`` ditinggal sementara director
    sudah tidak dipanggil lagi, renderer akan terus MELEWATI trail
    di-canvas padahal tidak ada yang menggantinya -> efek hilang total.
    """
    try:
        if director.hero is not None:
            director.hero._sy_fx = None
            director.hero._sy_live_fx = False
    except Exception:                      # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit ini (dipanggil renderer / pipeline).

    Sekalian menandai unit supaya renderer TIDAK menggambar efek yang
    sekarang dimiliki lapisan hidup (trail sapuan di canvas).
    Return True kalau lapisan hidup jadi dipakai.
    """
    if not SYLARA_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                      # pragma: no cover
        return False
    try:
        hero._sy_live_fx = True
    except Exception:                      # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini.

    Dipakai renderer untuk memutuskan apakah trail ayunan di-canvas
    masih perlu digambar (fallback) atau tidak.  Unit tanpa director —
    potongan portrait, alat uji, renderer yang dipanggil langsung —
    tetap memakai jalur canvas lama, jadi tidak ada visual yang hilang
    kalau modul FX tidak tersedia.
    """
    if not getattr(hero, "_sy_live_fx", False):
        return False
    d = getattr(hero, "_sy_fx", None)
    # Penanda saja tidak cukup: director-nya harus masih TERDAFTAR.
    return d is not None and d in _DIRECTORS


def _advance(director):
    """Majukan SATU director sesuai waktu sejak langkah terakhirnya.

    Mengapa tidak sekadar memanggil ``tick()`` dari ``draw_ground_layer``?
    Karena ``tick()`` memajukan SEMUA director.  Kalau 8 Sylara dirender
    dalam satu frame, jalur itu berarti 8 x 8 = 64 pembaruan director per
    frame (O(n^2)) walau hasil akhirnya identik.  Dengan stempel waktu
    per director, tiap unit maju tepat sekali per frame gambar — O(n) —
    dan unit yang tidak dirender (di luar layar) tidak menghabiskan
    waktu sama sekali.
    """
    if not SYLARA_FX_ENABLED or director is None:
        return 0.0
    now = pygame.time.get_ticks()
    if _feel is not None:                  # sisi efek: clock + shake bus
        _feel.fx_dt()
    last = director._last_ms
    if last is not None and now == last:
        return 0.0                         # sudah maju pada ms ini
    director._last_ms = now
    if last is None:
        return 0.0
    dt_ms = now - last
    if dt_ms <= 0:
        return 0.0
    dt = max(1.0 / 240.0, min(1.0 / 20.0, dt_ms / 1000.0))
    if HITSTOP is not None and HITSTOP.active:
        dt *= 0.18                         # slow-motion saat hit-stop
    director.update(dt)
    return dt


def tick(dt=None):
    """Majukan waktu FX satu frame nyata.  Aman dipanggil berkali-kali.

    Delta-time dihitung oleh bus ``combat_feel`` (dijepit supaya lonjakan
    frame saat loading / alt-tab tidak melempar partikel ke luar layar,
    dilambatkan saat hit-stop, dan shake-nya hanya dimundurkan SEKALI per
    frame walau beberapa karakter ikut bertempur).
    """
    global _LAST_TICK_MS
    now = pygame.time.get_ticks()
    if dt is None:
        if _feel is not None:
            if now == _LAST_TICK_MS:
                return 0.0                 # frame yang sama: sudah maju
            dt = _feel.fx_dt()
            _LAST_TICK_MS = now
        else:                              # pragma: no cover - fallback
            if _LAST_TICK_MS is None:
                _LAST_TICK_MS = now
                return 0.0
            dt_ms = now - _LAST_TICK_MS
            if dt_ms <= 0:
                return 0.0
            _LAST_TICK_MS = now
            dt = max(1.0 / 240.0, min(1.0 / 20.0, dt_ms / 1000.0))
            if HITSTOP.active:
                dt *= 0.18
            SHAKE.update(dt)
    if dt > 0.0:
        for d in _DIRECTORS:
            try:
                d._last_ms = now           # sinkron dengan _advance()
                d.update(dt)
            except Exception:              # pragma: no cover - anti-gagal
                pass
    return dt


def reset_all():
    """Lepas & kosongkan SEMUA director (ganti level / keluar match)."""
    global _LAST_TICK_MS
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()
    _LAST_TICK_MS = None


def total_particles():
    """Jumlah partikel Sylara hidup di seluruh arena (untuk HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def total_projectiles():
    """Jumlah proyektil visual Sylara hidup (untuk HUD perf)."""
    return sum(d.projectiles.count() for d in _DIRECTORS)


# --- hook yang dipanggil heroes/__init__.py --------------------------------

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: dipanggil SEBELUM sprite hero di-blit."""
    if not SYLARA_FX_ENABLED:
        return
    attach(hero)
    d = director_for(hero)
    _advance(d)
    d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: dipanggil SETELAH sprite hero di-blit."""
    if not SYLARA_FX_ENABLED:
        return
    director_for(hero).draw_front(surface)


# --- hook yang dipanggil _entity.py ----------------------------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Serangan jarak dekat Sylara mendarat (sapuan limb busur).

    Sylara ranged (range 130), jadi jalur ini aktif saat sapuan melee
    dipakai atau item mengubahnya jadi melee; API tetap disediakan demi
    paritas dengan modul karakter lain.
    """
    if not SYLARA_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except Exception:                      # pragma: no cover
        power = 1.0
    tx = float(getattr(target, "x", 0)) if target is not None else 0.0
    ty = float(getattr(target, "y", 0)) if target is not None else 0.0
    ang = math.atan2(ty - float(getattr(hero, "y", 0.0)),
                     tx - float(getattr(hero, "x", 0.0)))
    director_for(hero).on_impact(tx, ty - 10, ang, power, crit, "swing")


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False):
    """Panah Sylara mendarat (jalur ranged generik ``_entity``)."""
    if not SYLARA_FX_ENABLED or hero is None:
        return
    try:
        power = 0.75 + min(1.7, float(damage) / 45.0)
    except Exception:                      # pragma: no cover
        power = 1.0
    director_for(hero).on_impact(float(x), float(y) - 10, float(angle),
                                 power, crit, "arrow")


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """Skill Sylara meledak di sebuah titik (dipakai tooling/audit)."""
    if not SYLARA_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    if len(d.skills) >= MAX_SKILLS - 1:
        d.skills.pop(0)
    f = 1 if getattr(hero, "facing",
                     getattr(hero, "direction", 1)) >= 0 else -1
    d.skills.append(SkillFX(skill, x, y, d.particles, radius, facing=f,
                            target=getattr(hero, "target", None),
                            projectiles=d.projectiles))


def notify_skill_cast(hero, skill):
    """Skill Sylara dilepas dari luar (auto-cast guard / tooling)."""
    if not SYLARA_FX_ENABLED or hero is None:
        return
    director_for(hero).on_cast(float(getattr(hero, "x", 0.0)),
                               float(getattr(hero, "y", 0.0)),
                               skill)


def notify_hurt(hero, amount=1.0):
    """Sylara terkena damage dari luar (tanpa menunggu watch hp)."""
    if not SYLARA_FX_ENABLED or hero is None:
        return
    director_for(hero).on_hurt(amount)
