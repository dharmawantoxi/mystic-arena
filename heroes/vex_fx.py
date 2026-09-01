# ============================================================================
# heroes/vex_fx.py
# ----------------------------------------------------------------------------
# VEX — COMBAT / GAME-FEEL ENGINE  (screen-space live layer)
#
# Badan Vex digambar lewat ``_NS_vex`` (heroes/_bundle.py) ke canvas yang
# DI-CACHE lalu di-scale oleh pipeline hero.  Semua yang butuh gerak 60 fps
# sejati — arc ayunan staff, partikel, proyektil void, impact, crystal spike,
# gelembung astral, screen shake, hit-stop — TIDAK boleh hidup di dalam
# canvas itu: hasilnya ikut beku pada kuantisasi pose dan menyusut bersama
# sprite.  Modul ini adalah lapisan hidup tersebut: digambar langsung ke
# layar pada skala 1:1 tiap frame, memakai delta-time nyata.
#
# Pembagian kerja (sengaja — supaya tidak ada efek yang digambar 2x):
#
#   RENDERER (canvas, ter-cache)        MODUL INI (layar, hidup)
#   -----------------------------       ----------------------------------
#   rig + selout + crown + hood         arc ayunan staff dari histori posisi
#   bayangan kontak, platform void      partikel (mote, debu, kristal, rune)
#   TELEGRAPH AOE Q/W/E/R (besar)       PROYEKTIL void shard (sistem nyata)
#   conduit beam, portal collapse       IMPACT FX + flash + hit-stop + shake
#   pose, napas, jubah mengambang       spike W / gelembung E / flux R hidup
#                                       overlay DEBUG_CHARACTER
#
# 100% PROSEDURAL.  Tidak ada berkas gambar eksternal, tidak ada
# sprite-sheet, tidak ada loader tekstur.  Semua bentuk dibuat dengan
# pygame.draw + pygame.Surface + pygame.transform.
#
# Isi modul
#   VEX_PALETTE        palette khusus karakter (kontrak 9 kunci + ramp)
#   Particle           partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem     pool + burst + stream + ring + cap, reusable
#   SwingTrail         weapon trail prosedural dari histori posisi staff
#   ImpactFX           flash + shockwave + serpihan + fragmen + debris
#   VexProjectile      proyektil modular (spawn->travel->hit->destroy)
#   ProjectileSystem   manajer proyektil
#   draw_arcane_orb    renderer orb bersama (dipakai _entity.py)
#   SkillFX            lifecycle FX skill (cast->charge->release->fade)
#   VexFXDirector      satu instance per unit, mengikat semua di atas
#   draw_debug_overlay hitbox/hurtbox/state/frame/FPS/particle/skill/timer
#   API modul          tick / reset_all / notify_* / draw_*_layer
# ============================================================================

import math
import random

import pygame

try:                        # bus game-feel bersama (zephyr/gornak/grimjaw/kaizen)
    from heroes import combat_feel as _feel
except Exception:           # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual VEX: hitbox, hurtbox, jangkauan, state animasi, frame, FPS,
#: jumlah partikel, state skill, timer serangan.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
VEX_FX_ENABLED = True

#: Hit-stop global (dibaca _core.Game.update lewat should_freeze_frame).
HIT_STOP_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 170

#: Batas keras proyektil visual per director.
MAX_PROJECTILES = 18

#: Panjang histori trail senjata (jumlah sample posisi staff).
TRAIL_SAMPLES = 12

#: Batas dampak aktif per director & skill sekaligus di layar.
MAX_IMPACTS = 8
MAX_SKILLS = 4

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Kecepatan proyektil visual void (px/detik, ruang dunia).
ORB_SPEED = 620.0
#: Kecepatan serpihan void / kristal (R / W).
SHARD_SPEED = 300.0

#: Radius EFEK di ruang dunia (px) — sinkron dengan
#: hero_skills/_bundle.py :: _NS_vex_skills (W ring 55, W burst 60,
#: E prison range 200, R AOE 180) dan HERO_TYPES["vex"]["skill_range"]=250.
WORLD_RADIUS = {"q": 250.0, "w": 60.0, "e": 200.0, "r": 180.0}

#: Umur FX skill dalam DETIK.  Sinkron dengan
#: ``_NS_vex.SKILL_VISUAL_DURATION`` (40/100/60/80 langkah) UNTUK POSE,
#: lalu diperpanjang supaya efek hidup mengikuti status gameplay yang
#: sebenarnya (W = 180 langkah = 3.0 s, E = 150 = 2.5 s, R = 60 = 1.0 s).
SKILL_TOTAL = {"q": 0.95, "w": 3.25, "e": 2.85, "r": 1.65}

#: Durasi pose per skill (frame) — dipakai memetakan umur FX ke fase yang
#: sama dengan yang dibaca renderer.
SKILL_DUR = {"q": 40, "w": 100, "e": 60, "r": 80}


# ============================================================================
# 1.  PALETTE  —  void harbinger: teal void + ungu astral + emas rune
# ============================================================================

VEX_PALETTE = {
    # ── kontrak palette karakter (9 kunci wajib) ────────────────────
    "outline":    (  8,  10,  20),
    "shadow":     (  4,   6,  15),
    "dark":       ( 10,   8,  25),
    "body":       ( 45,  35,  75),
    "mid":        ( 75,  60, 115),
    "light":      (110,  90, 155),
    "highlight":  (170, 190, 220),
    "weapon":     ( 40,  45,  60),
    "fx":         ( 95, 225, 220),

    # ── ramp void (teal/cyan — energi utama) ────────────────────────
    "fx_deepest": (  8,  40,  50),
    "fx_deep":    ( 20,  85, 100),
    "fx_dark":    ( 45, 165, 175),
    "fx_mid":     ( 95, 225, 220),
    "fx_light":   (155, 245, 235),
    "fx_bright":  (200, 255, 245),
    "fx_pale":    (235, 255, 250),
    "fx_white":   (255, 255, 255),

    # ── ramp astral (ungu — E Astral Imprisonment) ──────────────────
    "astral_deepest": ( 25,   8,  50),
    "astral_deep":    ( 60,  25, 110),
    "astral_mid":     (115,  55, 190),
    "astral_light":   (175, 110, 235),
    "astral_bright":  (215, 165, 250),
    "astral_hot":     (240, 220, 255),

    # ── rune emas (kontras hangat satu-satunya) ─────────────────────
    "rune_dark":   ( 30,  75,  85),
    "rune_mid":    ( 60, 155, 165),
    "rune_light":  (140, 235, 230),
    "gold":        (232, 210, 118),
    "gold_hot":    (255, 240, 196),

    # ── material staff ──────────────────────────────────────────────
    "staff_dark":  ( 15,  20,  30),
    "staff_mid":   ( 40,  45,  60),
    "staff_light": ( 75,  85, 105),
    "staff_shine": (125, 145, 170),

    # ── kristal (W Sanity's Eclipse) ────────────────────────────────
    "crystal_dark":   ( 24,  70, 120),
    "crystal_mid":    ( 70, 150, 205),
    "crystal_light":  (150, 240, 255),
    "crystal_shine":  (225, 252, 255),

    # ── materi lingkungan ───────────────────────────────────────────
    "dust":        ( 92,  88, 112),
    "dust_light":  (138, 134, 158),
    "smoke":       ( 38,  42,  68),
    "white":       (255, 255, 255),
}

P = VEX_PALETTE

#: Kunci palette live -> kunci palette renderer (_NS_vex.PALETTE).
_PALETTE_SYNC = {
    "outline":        "armor_darkest",
    "shadow":         "shadow_deep",
    "dark":           "robe_darkest",
    "body":           "robe_mid",
    "mid":            "robe_light",
    "light":          "robe_high",
    "highlight":      "armor_shine",
    "weapon":         "staff_mid",
    "fx":             "void_light",
    "fx_deepest":     "void_darkest",
    "fx_deep":        "void_dark",
    "fx_dark":        "void_mid",
    "fx_mid":         "void_light",
    "fx_light":       "void_bright",
    "fx_bright":      "void_hot",
    "fx_pale":        "void_white",
    "fx_white":       "white",
    "astral_deepest": "astral_darkest",
    "astral_deep":    "astral_dark",
    "astral_mid":     "astral_mid",
    "astral_light":   "astral_light",
    "astral_bright":  "astral_bright",
    "astral_hot":     "astral_hot",
    "rune_dark":      "rune_dark",
    "rune_mid":       "rune_mid",
    "rune_light":     "rune_light",
    "gold":           "void_gold",
    "gold_hot":       "void_gold_hot",
    "staff_dark":     "staff_dark",
    "staff_mid":      "staff_mid",
    "staff_light":    "staff_light",
    "staff_shine":    "staff_shine",
}

_RENDERER = None
_PALETTE_SYNCED = False


def _renderer():
    """Ambil namespace renderer Vex (lazy, sekali saja)."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from heroes._bundle import _NS_vex as G
            _RENDERER = G
        except Exception:                  # pragma: no cover - tool minimal
            _RENDERER = False
    return _RENDERER or None


def _sync_palette():
    """Salin warna tema dari ``_NS_vex.PALETTE`` sekali saja.

    Renderer adalah satu-satunya sumber kebenaran untuk material karakter;
    efek hidup tidak boleh punya salinan yang lalu melenceng.  Kalau
    renderer tidak tersedia (tooling minimal), nilai literal di atas
    tetap dipakai.
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
    """Jepit komponen warna ke 0-255 dan pastikan tuple int."""
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
# 4.  SURFACE CACHE  —  glow / spark / ring / orb / kristal dibuat sekali
# ============================================================================

_SURF_CACHE = {}
_SURF_CACHE_MAX = 340


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


def faceted_orb_surface(radius, core, mid, edge, spec, rot_step=0,
                        sides=8):
    """Orb void BERSEGI (bukan lingkaran polos) — cached.

    Oktagon chunky dengan dua faset (atas terang / bawah gelap), pita
    specular sabit di kiri-atas, outline keras, dan 3 piksil kilau.
    ``rot_step`` dikuantisasi 15° supaya cache tidak meledak.
    """
    radius = max(3, int(radius))
    core = _clamp_color(core)
    mid = _clamp_color(mid)
    edge = _clamp_color(edge)
    spec = _clamp_color(spec)
    sides = max(5, min(12, int(sides)))
    step = int(rot_step) // 15 * 15
    key = ("forb", radius, core, mid, edge, spec, step, sides)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    size = radius * 2 + 6
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    ang0 = math.radians(step)
    pts = []
    for i in range(sides):
        a = ang0 + (i + 0.5) * math.tau / sides
        pts.append((c + math.cos(a) * radius, c + math.sin(a) * radius))

    pygame.draw.polygon(surf, (*mid, 238), pts)

    # ── dua faset: bawah gelap, atas terang (tepi keras, tanpa AA) ──
    low = sorted([q for q in pts if q[1] > c], key=lambda q: q[0])
    high = sorted([q for q in pts if q[1] <= c], key=lambda q: q[0])
    if len(low) >= 2:
        pygame.draw.polygon(surf, (*_mix(mid, P["outline"], 0.55), 235),
                            [(c - radius, c)] + low + [(c + radius, c)])
    if len(high) >= 2:
        pygame.draw.polygon(surf, (*_mix(mid, core, 0.42), 235),
                            [(c - radius, c)] + high + [(c + radius, c)])

    # ── sabit specular kiri-atas ────────────────────────────────────
    rect = pygame.Rect(c - radius, c - radius, radius * 2, radius * 2)
    try:
        pygame.draw.arc(surf, (*spec, 240), rect,
                        math.pi * 1.08, math.pi * 1.78,
                        max(1, radius // 4))
    except (ValueError, pygame.error):        # pragma: no cover
        pass

    # ── outline keras + kilau piksel ────────────────────────────────
    pygame.draw.polygon(surf, (*edge, 235), pts, 1)
    pygame.draw.rect(surf, (*P["white"], 255),
                     (c - radius // 2 - 1, c - radius // 2 - 1, 2, 2))
    pygame.draw.rect(surf, (*core, 230),
                     (c - 1, c - 1, 2, 2))
    return _cache_put(key, surf)


def rune_surface(size, color, seed=0):
    """Glif rune bersudut (BUKAN lingkaran) — cached per (size, seed)."""
    size = max(3, int(size))
    color = _clamp_color(color)
    seed = int(seed) % 6
    key = ("rune", size, color, seed)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    s = size * 2 + 3
    surf = pygame.Surface((s, s), pygame.SRCALPHA)
    c = size + 1
    h = int(size * _hash01(seed * 7 + 1) * 0.4)
    # batang vertikal + 2-3 cabang bersudut (deterministik per seed)
    pygame.draw.line(surf, (*color, 240), (c, c - size), (c, c + size), 1)
    for k in range(3):
        if _hash01(seed * 31 + k * 5) < 0.34:
            continue
        y = c - size + int((k + 0.5) * (size * 2) / 3.0)
        d = 1 if _hash01(seed * 17 + k) < 0.5 else -1
        pygame.draw.line(surf, (*color, 225), (c, y),
                         (c + d * size, y - h), 1)
    return _cache_put(key, surf)


def crystal_shard_surface(length, width, color, shine):
    """Spike kristal bersudut menghadap +x (BUKAN elips) — cached."""
    length = max(4, int(length))
    width = max(2, int(width))
    color = _clamp_color(color)
    shine = _clamp_color(shine)
    key = ("shard", length, width, color, shine)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    surf = pygame.Surface((length + 4, width * 2 + 4), pygame.SRCALPHA)
    cy = width + 2
    pts = [(2, cy), (int(length * 0.55), cy - width),
           (length + 2, cy - max(1, width // 4)),
           (int(length * 0.55), cy + width)]
    pygame.draw.polygon(surf, (*color, 240), pts)
    # faset terang (sisi atas) — hard edge pixel-art
    pygame.draw.polygon(surf, (*shine, 225),
                        [(2, cy), (int(length * 0.55), cy - width),
                         (length + 2, cy - max(1, width // 4)),
                         (int(length * 0.5), cy - max(1, width // 5))])
    pygame.draw.polygon(surf, (*P["outline"], 220), pts, 1)
    return _cache_put(key, surf)


def chevron_surface(size, color, thick=2):
    """Panah runic menghadap +x (penanda arah skill) — cached."""
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


def dashed_ring_surface(radius, thickness, color, segments=8, span=0.42,
                        rot_step=0):
    """Cincin putus-putus berputar (rune halo) — cached."""
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
    untuk partikel bersudut, proyektil, dan spike kristal.  Kuantisasi
    15° membuat jumlah entri terbatas (24 bucket) sekaligus cukup halus
    untuk ukuran sprite sekecil ini.
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
      pixel / spark / shard / streak / mote / smoke / glow / rune / crystal
    """

    __slots__ = ("pos", "vel", "acc", "life", "max_life", "size",
                 "rotation", "rotation_speed", "alpha", "gravity",
                 "color", "color_end", "shape", "drag", "additive",
                 "active", "fade_pow", "back", "swirl")

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
        self.active = True
        return self

    # ------------------------------------------------------------------
    def update(self, dt):
        """Integrasi gerak; return False kalau partikel sudah mati."""
        self.life -= dt
        if self.life <= 0.0:
            self.active = False
            return False
        self.vel.x += (self.acc.x) * dt
        self.vel.y += (self.acc.y + self.gravity) * dt
        if self.swirl:
            # belok tegak-lurus kecepatan -> gerak spiral khas void
            vx, vy = self.vel.x, self.vel.y
            self.vel.x += -vy * self.swirl * dt
            self.vel.y += vx * self.swirl * dt
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

        if self.shape == "rune":
            # glif rune berputar — bahasa visual Vex, bukan titik bundar
            base = rune_surface(max(2, sz), col, int(self.rotation * 2) & 5)
            if sz >= 3:
                base = rotated_cached(("prune", max(2, sz), col,
                                       int(self.rotation * 2) & 5),
                                      base,
                                      int(math.degrees(self.rotation)))
            base.set_alpha(a)
            surface.blit(base, (x - base.get_width() // 2,
                                y - base.get_height() // 2))
            return

        if self.shape == "crystal":
            # serpihan kristal bersudut (W / R)
            base = crystal_shard_surface(max(3, int(sz * 2.2)),
                                         max(2, int(sz * 0.8)),
                                         col, _mix(col, P["white"], 0.5))
            if sz >= 3:
                base = rotated_cached(
                    ("pcrys", max(3, int(sz * 2.2)), max(2, int(sz * 0.8)),
                     col),
                    base, -int(math.degrees(self.rotation)))
            base.set_alpha(a)
            surface.blit(base, (x - base.get_width() // 2,
                                y - base.get_height() // 2))
            return

        if self.shape == "shard":
            # pecahan rune berputar (debris benturan)
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
            # garis tipis searah kecepatan — percikan void cepat
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

        if self.shape == "mote":
            # mote void: titik terang + ekor kecil, additive
            tmp = _scratch(sz * 4 + 4, sz * 4 + 4)
            off = sz * 2 + 2
            pygame.draw.circle(tmp, (*col, int(a * 0.55)),
                               (off, off), max(1, sz))
            pygame.draw.circle(tmp, (*_mix(col, P["fx_white"], 0.5), a),
                               (off, off), max(1, sz // 2))
            surface.blit(tmp, (x - off, y - off),
                         special_flags=pygame.BLEND_RGB_ADD)
            return

        if self.shape == "smoke":
            # gumpalan debu lembut di lapisan belakang
            r = max(2, sz)
            tmp = _scratch(r * 2 + 4, r * 2 + 4)
            off = r + 2
            pygame.draw.circle(tmp, (*col, int(a * 0.5)),
                               (off, off), r)
            pygame.draw.circle(tmp, (*_mix(col, P["fx_white"], 0.15),
                                     int(a * 0.25)),
                               (off - r // 3, off - r // 3),
                               max(1, r // 2))
            surface.blit(tmp, (x - off, y - off))
            return

        # default: kotak chunky (pixel-art) + sudut terang
        tmp = _scratch(sz * 2 + 2, sz * 2 + 2)
        pygame.draw.rect(tmp, (*col, a), (1, 1, sz, sz))
        if sz >= 3:
            pygame.draw.rect(tmp, (*P["fx_white"], min(255, a + 40)),
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
            self._pool.append(p)
        self._live.clear()

    # ------------------------------------------------------------------
    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        """Spawn satu partikel.  Return partikel, atau None kalau penuh."""
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
              swirl=0.0):
        """Semburan radial / berarah.

        ``direction`` + ``spread`` mengontrol kerucut sebaran; spread
        ``math.tau`` = melingkar penuh.  ``back=True`` mengirim partikel
        ke lapisan belakang karakter (debu/asap).  ``swirl`` memberi
        belokan spiral khas void.  Jumlah partikel otomatis mengikuti
        anggaran kualitas perangkat.
        """
        count = _budgeted(count)
        if count <= 0:
            return 0
        colors = colors or (P["fx_light"], P["fx_mid"], P["fx_bright"])
        room = self.cap - len(self._live)
        if room <= 0:
            return 0
        n = min(int(count), room)
        for i in range(n):
            ang = direction + (random.random() - 0.5) * spread
            spd = random.uniform(speed[0], speed[1])
            self.spawn(
                x, y,
                math.cos(ang) * spd, math.sin(ang) * spd,
                random.uniform(life[0], life[1]),
                random.uniform(size[0], size[1]),
                colors[i % len(colors)],
                gravity=gravity, drag=drag, shape=shape,
                additive=additive, fade_pow=fade_pow,
                rotation=random.random() * math.tau,
                rotation_speed=random.uniform(rotation_speed[0],
                                              rotation_speed[1]),
                back=back, swirl=swirl)
        return n

    # ------------------------------------------------------------------
    def stream(self, x, y, tx, ty, count, life=(0.3, 0.6), size=(1, 3),
               colors=None, drag=1.2, shape="mote"):
        """Aliran partikel dari (x,y) menuju (tx,ty) — charge / hisap."""
        count = _budgeted(count)
        if count <= 0:
            return 0
        colors = colors or (P["fx_mid"], P["fx_light"])
        n = 0
        for i in range(int(count)):
            t = i / max(1, count)
            px = x + (tx - x) * t + random.uniform(-4, 4)
            py = y + (ty - y) * t + random.uniform(-3, 3)
            dx, dy = tx - px, ty - py
            dist = max(1.0, math.hypot(dx, dy))
            spd = random.uniform(90.0, 210.0)
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
             colors=None, speed=(40.0, 110.0), squash=0.55, shape="mote",
             inward=False, swirl=0.0, back=False):
        """Cincin partikel mengembang (atau menyusut kalau ``inward``).

        ``squash`` menggepengkan cincin ke perspektif tanah (0.55 = AOE
        di lantai arena, 1.0 = cincin vertikal penuh).
        """
        count = _budgeted(count)
        if count <= 0:
            return 0
        colors = colors or (P["fx_mid"], P["fx_light"], P["fx_bright"])
        n = 0
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
        return n

    # ------------------------------------------------------------------
    def update(self, dt):
        """Integrasi semua partikel; yang mati dikembalikan ke pool."""
        if not self._live:
            return
        live = self._live
        keep = []
        pool = self._pool
        for p in live:
            if p.update(dt):
                keep.append(p)
            else:
                if len(pool) < self.cap:
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
# 6.  SWING TRAIL  —  arc staff prosedural dari histori posisi
# ============================================================================

class SwingTrail:
    """Jejak staff Vex berbasis histori posisi (OLD POS ... CURRENT).

    Menyimpan pasangan (pangkal, ujung) beberapa frame terakhir lalu
    menyusunnya jadi pita poligon translucent 4-band teal yang memudar
    + garis tepi putih 1-2 px (hard edge pixel-art).  Trail OTOMATIS
    mengikuti arah serangan karena bentuknya murni turunan dari lintasan
    busur orb staff (arc-based), bukan lerp linear.

    Dibanding Kaizen (pita iai tipis & cepat), pita Vex lebih LEBAR,
    lebih LAMA pudar, dan dihiasi rune glif — bahasa void: berat,
    mengambang, dan berenergi, bukan presisi baja.
    """

    def __init__(self, samples=TRAIL_SAMPLES,
                 color_edge=None, color_core=None):
        self.samples = int(samples)
        self.points = []            # [[pangkal, ujung, umur], ...]
        self.color_edge = color_edge or P["fx_dark"]
        self.color_core = color_core or P["fx_bright"]
        self.life = 0.26            # detik sebelum sample dibuang
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
        """Gambar pita trail: selubung -> badan -> inti -> garis ujung."""
        n = len(self.points)
        if n < 2:
            return

        # bounding box supaya scratch surface sekecil mungkin
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

        hot = 1.20 if self.overcharged else 1.0

        # ── lapis 1: selubung void dalam (lebar penuh, teal gelap) ───
        for i in range(n - 1):
            g0, t0, a0 = self.points[i]
            g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(115 * self._quad_alpha(i, n) * fade *
                        self.width_boost)
            if alpha <= 4:
                continue
            pygame.draw.polygon(
                buf, (*P["fx_deepest"], alpha),
                [loc(g0), loc(t0), loc(t1), loc(g1)])

        # ── lapis 2: badan void (setengah lebar, dekat ujung) ────────
        for i in range(n - 1):
            g0, t0, a0 = self.points[i]
            g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(200 * self._quad_alpha(i, n) * fade * hot)
            if alpha <= 6:
                continue
            m0 = g0.lerp(t0, 0.48)
            m1 = g1.lerp(t1, 0.48)
            pygame.draw.polygon(
                buf, (*self.color_edge, min(255, alpha)),
                [loc(m0), loc(t0), loc(t1), loc(m1)])

        # ── lapis 3: inti nyaris putih (seperempat lebar terakhir) ───
        for i in range(n - 1):
            g0, t0, a0 = self.points[i]
            g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(230 * self._quad_alpha(i, n) * fade * hot)
            if alpha <= 8:
                continue
            m0 = g0.lerp(t0, 0.76)
            m1 = g1.lerp(t1, 0.76)
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

        # ── lapis 5: rune glif melayang di sepanjang arc (di luar buf
        #    karena butuh rotasi per-sample) ──────────────────────────
        if n >= 4:
            for i in range(0, n - 1, 3):
                _g0, t0, a0 = self.points[i]
                fade = max(0.0, 1.0 - a0 / self.life)
                alpha = int(150 * self._quad_alpha(i, n) * fade)
                if alpha <= 10:
                    continue
                g = rune_surface(3, P["rune_light"] if not self.overcharged
                                 else P["gold_hot"], i & 5)
                g.set_alpha(alpha)
                surface.blit(g, (int(t0.x) - g.get_width() // 2,
                                 int(t0.y) - g.get_height() // 2))


# ============================================================================
# 7.  IMPACT FX
# ============================================================================

class ImpactFX:
    """Satu kejadian benturan: flash, shockwave, serpihan, fragmen, debris.

    Semua digambar prosedural dan berumur pendek; tidak ada state yang
    hidup tanpa batas.  ``kind`` memilih bahasa benturan:
      * "orb"    — Arcane Orb mendarat (teal, bintang 6 + pecahan rune)
      * "astral" — Astral Imprisonment mengurung / pecah (ungu, kurungan)
      * "spike"  — crystal spike Sanity's Eclipse (biru kristal, tajam)
      * "flux"   — ledakan Essence Flux (teal + emas, paling berat)
      * "crit"   — critical strike (putih panas + aksen emas)
    """

    __slots__ = ("x", "y", "angle", "power", "age", "duration",
                 "crit", "active", "color", "kind")

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="orb"):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = max(0.35, float(power))
        self.age = 0.0
        self.duration = 0.30 + 0.12 * min(2.0, self.power)
        self.crit = bool(crit) or kind == "crit"
        self.active = True
        self.kind = kind
        if kind == "crit":
            self.color = P["fx_white"]
        elif kind == "flux":
            self.color = P["gold_hot"]
        elif kind == "astral":
            self.color = P["astral_bright"]
        elif kind == "spike":
            self.color = P["crystal_light"]
        else:
            self.color = P["fx_bright"] if not crit else P["fx_white"]
        if kind == "flux":
            self.duration += 0.16
        elif kind == "astral":
            self.duration += 0.08

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
        ca, sa = math.cos(self.angle), math.sin(self.angle)
        deg = math.degrees(self.angle)

        # ── 1. IMPACT FLASH — flare bintang 6 arah, bukan bola ──────
        if t < 0.24:
            ft = 1.0 - t / 0.24
            gr = int((6 + 9 * pw) * (0.5 + 0.5 * ft)) // 2 * 2 + 2
            surface.blit(glow_surface(gr, self.color, 0.5 * ft),
                         (x - gr, y - gr),
                         special_flags=pygame.BLEND_RGB_ADD)
            ln = (15 + 32 * pw) * ft
            fl = _scratch(int(ln * 2 + 8), int(ln * 2 + 8))
            c = int(ln + 4)
            for k in range(6):
                a = self.angle + k * math.pi / 3
                L = ln if k % 2 == 0 else ln * 0.45
                pygame.draw.line(
                    fl, (*P["fx_pale"], int(240 * ft)), (c, c),
                    (c + int(math.cos(a) * L),
                     c + int(math.sin(a) * L)),
                    3 if k % 2 == 0 else 1)
            surface.blit(fl, (x - c, y - c))

        # ── 2. SHOCKWAVE — elips berarah (bukan lingkaran polos) ────
        rr = int((9 + 44 * pw) * (0.25 + 1.05 * t)) // 3 * 3
        th = max(1, int(4 * inv * pw))
        a = int(205 * inv * inv)
        if a > 6 and rr > 4:
            col = self.color if self.kind != "orb" else P["fx_mid"]
            er = ellipse_ring_surface(rr, max(3, int(rr * 0.6)), th,
                                      col, deg)
            er.set_alpha(a)
            surface.blit(er, (x - er.get_width() // 2,
                              y - er.get_height() // 2))
            rr2 = int(rr * 0.58)
            if rr2 > 4:
                er2 = ellipse_ring_surface(rr2, max(2, int(rr2 * 0.7)),
                                           max(1, th - 1), self.color, deg)
                er2.set_alpha(int(a * 0.75))
                surface.blit(er2, (x - er2.get_width() // 2,
                                   y - er2.get_height() // 2))

        # ── 3. SPOKE DEBRIS — garis radial memanjang keluar ──────────
        if t < 0.55:
            st = 1.0 - t / 0.55
            r0 = int((7 + 19 * pw) * (0.3 + 1.1 * t))
            for k in range(8):
                ang = self.angle + k * math.pi / 4 + 0.19
                L = (6 + 15 * pw) * st * (1.0 if k % 2 else 0.55)
                pygame.draw.line(
                    surface, _clamp_color(
                        _mix(P["fx_deep"], P["fx_light"], st)),
                    (x + int(math.cos(ang) * r0),
                     y + int(math.sin(ang) * r0)),
                    (x + int(math.cos(ang) * (r0 + L)),
                     y + int(math.sin(ang) * (r0 + L))),
                    2 if k % 2 else 1)

        # ── 4. SLASH FRAGMENT — sabit tebal + busur pecah + chevron ──
        # Busurnya BERBASIS LINGKARAN BESAR (arc) yang mengembang searah
        # ayunan, BUKAN lerp linear: memberi bobot & arah pada tebasan.
        if t < 0.5 and self.kind in ("orb", "crit"):
            st = 1.0 - t / 0.5
            span = 0.62 + 0.55 * pw
            base_r = int(13 + 32 * pw * (0.45 + t))
            buf_r = base_r + 12
            buf = _scratch(buf_r * 2, buf_r * 2)
            c = buf_r
            # ── sabit utama: selubung gelap -> badan -> tepi terang ──
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
                except (ValueError, pygame.error):        # pragma: no cover
                    pass
            # ── 3 fragmen busur yang buyar keluar ───────────────────
            for k in (-1, 0, 1):
                ang0 = self.angle - span / 2 + k * 0.14
                ang1 = ang0 + span * 0.86
                rad = base_r + 5 + abs(k) * 6
                rect2 = pygame.Rect(c - rad, c - rad, rad * 2, rad * 2)
                col = P["fx_white"] if k == 0 else P["fx_pale"]
                try:
                    pygame.draw.arc(buf, (*col, int(210 * st)),
                                    rect2, -ang1, -ang0,
                                    2 if k == 0 else 1)
                except (ValueError, pygame.error):        # pragma: no cover
                    pass
            # ── chevron penunjuk arah di ujung sabit ────────────────
            lead = base_r + 10
            lx = c + int(math.cos(self.angle) * lead)
            ly = c + int(math.sin(self.angle) * lead)
            for d in (-1, 0, 1):
                a2 = self.angle + d * 0.30
                pygame.draw.line(
                    buf, (*P["fx_pale"], int(205 * st)),
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
                        surface, (*P["gold"], int(205 * ct)),
                        (x - int(math.cos(self.angle + da) * Lc),
                         y - int(math.sin(self.angle + da) * Lc)),
                        (x + int(math.cos(self.angle + da) * Lc),
                         y + int(math.sin(self.angle + da) * Lc)), 1)

        # ── 4b. ASTRAL — kurungan rune pecah (segi, bukan lingkaran) ─
        if self.kind == "astral" and t < 0.55:
            st = 1.0 - t / 0.55
            rad = int((10 + 26 * pw) * (0.45 + 0.9 * t))
            sides = 6
            buf_r = rad + 6
            buf = _scratch(buf_r * 2, buf_r * 2)
            c = buf_r
            pts = []
            for i in range(sides):
                ang = self.angle + (i + 0.5) * math.tau / sides
                pts.append((c + math.cos(ang) * rad,
                            c + math.sin(ang) * rad))
            pygame.draw.polygon(buf, (*P["astral_light"], int(120 * st)),
                                pts)
            pygame.draw.polygon(buf, (*P["astral_bright"], int(225 * st)),
                                pts, 2)
            for px_, py_ in pts:
                pygame.draw.line(buf, (*P["astral_hot"], int(200 * st)),
                                 (c, c), (int(px_), int(py_)), 1)
            surface.blit(buf, (x - c, y - c))

        # ── 4c. SPIKE — pecahan kristal tajam menyembur ──────────────
        if self.kind == "spike" and t < 0.5:
            st = 1.0 - t / 0.5
            for k in range(4):
                ang = self.angle + k * math.pi / 2 + 0.35
                ln = int((9 + 16 * pw) * st)
                sh = rotated_cached(
                    ("ispk", ln),
                    crystal_shard_surface(max(4, ln), max(2, ln // 4),
                                          P["crystal_mid"],
                                          P["crystal_shine"]),
                    -int(math.degrees(ang)))
                sh.set_alpha(int(230 * st))
                surface.blit(sh, (x - sh.get_width() // 2,
                                  y - sh.get_height() // 2))

        # ── 4d. FLUX — ledakan void: cincin emas + silang rune ───────
        if self.kind == "flux":
            if t < 0.6:
                st = 1.0 - t / 0.6
                rad = int((16 + 60 * pw) * (0.35 + 0.95 * t))
                surface.blit(dashed_ring_surface(
                    max(5, rad), max(2, int(3 * st) + 1), P["gold"],
                    segments=10, span=0.38,
                    rot_step=math.degrees(self.angle) + t * 90.0),
                    (x - rad - 8, y - rad - 8))
                ln = int((22 + 34 * pw) * st)
                for da in (math.pi / 4, -math.pi / 4):
                    x0 = x - int(math.cos(self.angle + da) * ln)
                    y0 = y - int(math.sin(self.angle + da) * ln)
                    x1 = x + int(math.cos(self.angle + da) * ln)
                    y1 = y + int(math.sin(self.angle + da) * ln)
                    pygame.draw.line(surface, (*P["gold_hot"],
                                               int(235 * st)),
                                     (x0, y0), (x1, y1), 3)
                    pygame.draw.line(surface, (*P["fx_pale"],
                                               int(180 * st)),
                                     (x0, y0 + 1), (x1, y1 + 1), 1)
            # pilar cahaya pendek (ledakan vertikal, bukan bola)
            if t < 0.45:
                st = 1.0 - t / 0.45
                hgt = int(42 * st)
                if hgt > 4:
                    pl = _scratch(16, hgt + 4)
                    pygame.draw.polygon(
                        pl, (*P["fx_light"], int(155 * st)),
                        [(8, hgt + 2), (8 - 4, 2), (8 + 4, 2)])
                    surface.blit(pl, (x - 8, y - hgt - 16))

        # ── 5. INTI benturan ─────────────────────────────────────────
        if t < 0.4:
            st = 1.0 - t / 0.4
            sz = int((4 + 8 * pw) * (0.5 + 0.5 * st)) // 2 * 2 + 2
            s = spark_surface(sz, self.color)
            s.set_alpha(int(255 * st))
            surface.blit(s, (x - sz - int(ca * 2), y - sz - int(sa * 2)))


# ============================================================================
# 8.  PROJECTILE SYSTEM  —  serpihan void / kristal (spawn->travel->hit)
# ============================================================================

class VexProjectile:
    """Proyektil void Vex — modular, vektor, delta-time.

    Kontrak atribut: position, velocity, speed, damage, lifetime,
    target, radius, rotation, trail, particles, active.

    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY.

    Catatan desain: ``damage`` tetap 0 — proyektil ini MURNI VISUAL.
    Damage gameplay Vex sudah diterapkan langsung oleh ``hero_skills``
    dan jalur proyektil generik ``_entity.py``.  Sistem ini tetap punya
    deteksi tumbukan penuh (radius vs target) supaya siklus hidupnya
    utuh dan bisa dipakai gameplay lain lewat callback ``on_impact``
    tanpa mengubah keseimbangan hero.
    """

    STATE_TRAVEL = "travel"
    STATE_IMPACT = "impact"
    STATE_DEAD = "dead"

    def __init__(self, x, y, tx, ty, speed=ORB_SPEED, damage=0,
                 target=None, radius=7.0, homing=3.2, kind="shard",
                 particles=None, on_impact=None, gravity=0.0,
                 max_lifetime=1.4):
        self.position = pygame.Vector2(x, y)
        self.spawn_pos = pygame.Vector2(x, y)
        d = pygame.Vector2(tx - x, ty - y)
        if d.length_squared() < 1e-6:
            d = pygame.Vector2(1.0, 0.0)
        self.velocity = d.normalize() * speed
        self.speed = float(speed)
        self.damage = damage
        self.lifetime = 0.0
        self.max_lifetime = float(max_lifetime)
        self.target = target
        self.radius = float(radius)
        self.rotation = math.atan2(self.velocity.y, self.velocity.x)
        self.trail = []                  # [[Vector2, umur], ...]
        self.trail_life = 0.22
        self.particles = particles       # ParticleSystem bersama
        self.active = True
        self.state = self.STATE_TRAVEL
        self.kind = kind                 # "shard" | "orb" | "crystal"
        self.homing = float(homing)
        self.gravity = float(gravity)
        self.on_impact = on_impact
        self._impact_age = 0.0
        self._emit_acc = 0.0
        self.hit_pos = pygame.Vector2(tx, ty)

    # ------------------------------------------------------------------
    def kill(self, x=None, y=None):
        """Paksa masuk fase impact di posisi tertentu."""
        if self.state != self.STATE_TRAVEL:
            return
        self.state = self.STATE_IMPACT
        self.hit_pos.update(self.position if x is None
                            else pygame.Vector2(x, y))
        self._impact_age = 0.0
        if self.on_impact:
            try:
                self.on_impact(self)
            except Exception:            # pragma: no cover - aman gameplay
                pass

    # ------------------------------------------------------------------
    def update(self, dt):
        """Kembalikan False kalau projectile harus dibuang."""
        if self.state == self.STATE_DEAD:
            return False

        if self.state == self.STATE_IMPACT:
            self._impact_age += dt
            self._age_trail(dt)
            if self._impact_age > 0.26 and not self.trail:
                self.state = self.STATE_DEAD
                self.active = False
                return False
            return True

        self.lifetime += dt
        if self.lifetime > self.max_lifetime:
            self.kill()
            return True

        # ── homing halus ke target yang bergerak ─────────────────────
        tgt = self.target
        if tgt is not None and getattr(tgt, "alive", False):
            to = pygame.Vector2(float(tgt.x), float(tgt.y)) - self.position
            if to.length_squared() > 1.0:
                desired = to.normalize() * self.speed
                k = min(1.0, self.homing * dt)
                self.velocity += (desired - self.velocity) * k
                if self.velocity.length_squared() > 1e-6:
                    self.velocity.scale_to_length(self.speed)

        if self.gravity:
            self.velocity.y += self.gravity * dt

        self.rotation = math.atan2(self.velocity.y, self.velocity.x)

        # ── catat trail lalu maju ────────────────────────────────────
        self.trail.append([pygame.Vector2(self.position), 0.0])
        if len(self.trail) > 14:
            self.trail.pop(0)
        self._age_trail(dt)

        self.position += self.velocity * dt

        # ── emisi partikel ekor (rate-limited) ───────────────────────
        if self.particles is not None:
            self._emit_acc += dt
            if self._emit_acc >= 0.04:
                self._emit_acc = 0.0
                ang = self.rotation + math.pi + (random.random() - .5) * 0.8
                spd = random.uniform(18, 62)
                tint = (P["fx_light"] if self.kind != "crystal"
                        else P["crystal_mid"])
                self.particles.spawn(
                    self.position.x, self.position.y,
                    math.cos(ang) * spd, math.sin(ang) * spd - 12,
                    random.uniform(0.16, 0.34),
                    random.uniform(1.5, 3.0),
                    tint, color_end=P["fx_deepest"], drag=2.8,
                    shape="mote",
                    rotation=random.random() * math.tau,
                    rotation_speed=random.uniform(-8, 8))

        # ── tumbukan dengan target (radius + radius unit) ────────────
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
        """Trail pita -> glow -> badan berarah -> inti -> glint."""
        # ── TRAIL: pita menyempit, bukan rantai lingkaran ────────────
        n = len(self.trail)
        if n >= 2:
            ux = math.cos(self.rotation + math.pi / 2)
            uy = math.sin(self.rotation + math.pi / 2)
            pts_a = []
            pts_b = []
            for i, (pv, age) in enumerate(self.trail):
                f = (i + 1) / float(n)
                fade = max(0.0, 1.0 - age / self.trail_life)
                wdt = self.radius * 0.85 * f * fade
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
                dark = (P["fx_deepest"] if self.kind != "crystal"
                        else P["crystal_dark"])
                pygame.draw.polygon(
                    buf, (*dark, 120),
                    [(int(px) - minx, int(py) - miny) for px, py in poly])
                bright = (P["fx_light"] if self.kind != "crystal"
                          else P["crystal_light"])
                pygame.draw.lines(
                    buf, (*bright, 170), False,
                    [(int(pv.x) - minx, int(pv.y) - miny)
                     for pv, _a in self.trail], 2)
                surface.blit(buf, (minx, miny))

        if self.state == self.STATE_IMPACT:
            return

        if self.kind == "orb":
            draw_arcane_orb(surface, self.position.x, self.position.y,
                            self.rotation, age=int(self.lifetime * 60),
                            radius=self.radius, kind="attack")
            return

        # ── badan: shard / crystal bersudut berputar searah gerak ────
        ln = max(4, int(self.radius * 2.6))
        wd = max(2, int(self.radius * 0.9))
        if self.kind == "crystal":
            base = crystal_shard_surface(ln, wd, P["crystal_mid"],
                                         P["crystal_shine"])
        else:
            base = crystal_shard_surface(ln, wd, P["fx_dark"],
                                         P["fx_bright"])
        deg = -int(math.degrees(self.rotation)) // 10 * 10
        body = rotated_cached(("pbody", ln, wd, self.kind), base, deg)
        surface.blit(body, (int(self.position.x) - body.get_width() // 2,
                            int(self.position.y) - body.get_height() // 2))

        # halo additive (premultiplied, daya rendah)
        if glow_allowed():
            g = glow_surface(ln, P["fx_deep"] if self.kind != "crystal"
                             else P["crystal_dark"], 0.42)
            surface.blit(g, (int(self.position.x) - ln,
                             int(self.position.y) - ln),
                         special_flags=pygame.BLEND_RGB_ADD)

        # glint berputar — deterministik, hidup, murah
        for k in range(2):
            a = self.rotation + self.lifetime * 9.0 + k * math.pi
            gx = int(self.position.x + math.cos(a) * (self.radius + 3))
            gy = int(self.position.y + math.sin(a) * (self.radius + 3) * 0.6)
            s = spark_surface(2, P["fx_pale"] if k == 0
                              else P["crystal_shine"])
            surface.blit(s, (gx - 3, gy - 3))


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
        pr = VexProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    def update(self, dt):
        if not self.projectiles:
            return
        self.projectiles = [p for p in self.projectiles if p.update(dt)]

    def draw(self, surface):
        for p in self.projectiles:
            p.draw(surface)


def draw_arcane_orb(surface, px, py, angle=0.0, age=0, kind="attack",
                    radius=8.0):
    """Renderer bersama orb Vex (dipakai proyektil generik ``_entity``).

    Badan = orb BERSEGI (oktagon faset, BUKAN lingkaran polos) dengan
    sabit specular, halo additive, halo rune putus-putus kontra-rotasi,
    glif orbit, core putih, dan ekor facet memudar.  Semua bentuk
    prosedural, di-cache per (radius, rotasi terkuantisasi) sehingga
    tidak ada alokasi Surface per frame.

    ``kind``:
      * "attack" — serangan dasar / Arcane Orb (teal)
      * "skill"  — proyektil skill (lebih panas, ada aksen emas)
    """
    x, y = int(px), int(py)
    rad = max(4, int(radius))
    deg = int(math.degrees(angle)) // 15 * 15      # kuantisasi rotasi
    hot = kind == "skill"

    # ── HALO additive (premultiplied) di belakang badan ──────────────
    if glow_allowed():
        g = glow_surface(rad * 2, P["fx_deep"] if not hot else P["rune_dark"],
                         0.55)
        surface.blit(g, (x - rad * 2, y - rad * 2),
                     special_flags=pygame.BLEND_RGB_ADD)

    # ── TRAIL: deret facet memudar ke belakang ───────────────────────
    ca, sa = math.cos(angle), math.sin(angle)
    for i in range(5):
        f = 1.0 - (i + 1) / 6.0
        tx = x - int(ca * (i + 1) * rad * 0.62)
        ty = y - int(sa * (i + 1) * rad * 0.62)
        # goyangan deterministik dari age -> ekor "bernapas", tidak acak
        off = int(math.sin(age * 0.35 + i * 1.1) * rad * 0.28)
        tx += int(-sa * off)
        ty += int(ca * off)
        alpha = int(150 * f * f)
        if alpha <= 5:
            continue
        sub = faceted_orb_surface(max(2, int(rad * (0.30 + 0.55 * f))),
                                  P["fx_pale"] if hot else P["fx_bright"],
                                  P["fx_mid"], P["fx_deep"],
                                  P["fx_pale"], rot_step=deg + i * 18,
                                  sides=6)
        sub.set_alpha(alpha)
        surface.blit(sub, (tx - sub.get_width() // 2,
                           ty - sub.get_height() // 2))

    # ── BADAN orb bersegi ────────────────────────────────────────────
    body = faceted_orb_surface(
        rad,
        P["gold_hot"] if hot else P["fx_white"],
        P["fx_mid"] if not hot else P["fx_light"],
        P["fx_light"] if not hot else P["gold"],
        P["fx_pale"],
        rot_step=deg)
    surface.blit(body, (x - body.get_width() // 2,
                        y - body.get_height() // 2))

    # ── HALO RUNE: cincin putus-putus kontra-rotasi ──────────────────
    surface.blit(
        dashed_ring_surface(rad + 5, 2, P["fx_light"] if not hot
                            else P["rune_light"],
                            segments=8, span=0.40,
                            rot_step=math.degrees(-angle) + age * 5.0),
        (x - rad - 9, y - rad - 9))
    surface.blit(
        dashed_ring_surface(rad + 11, 1, P["fx_deep"],
                            segments=10, span=0.26,
                            rot_step=math.degrees(angle) - age * 3.0),
        (x - rad - 15, y - rad - 15))

    # ── GLIF ORBIT (bentuk bersudut, bukan titik) ────────────────────
    for i in range(2):
        a = angle + age * 0.09 + i * math.pi
        rr = rad + 7 + int(math.sin(age * 0.2 + i) * 2)
        gl = rune_surface(3, P["rune_light"] if not hot else P["gold_hot"],
                          i + (int(age * 0.1) & 3))
        surface.blit(gl, (int(x + math.cos(a) * rr) - gl.get_width() // 2,
                          int(y + math.sin(a) * rr) - gl.get_height() // 2))

    # ── CORE putih + kilau depan ─────────────────────────────────────
    pygame.draw.rect(surface, P["white"], (x - 1, y - 1, 2, 2))
    fx = x + int(ca * (rad + 3))
    fy = y + int(sa * (rad + 3))
    s = spark_surface(3, P["fx_pale"] if not hot else P["gold_hot"])
    surface.blit(s, (fx - 4, fy - 4))


# ============================================================================
# 9.  SKILL FX  —  lifecycle cast -> charge -> release -> area -> fade
# ============================================================================

class SkillFX:
    """Efek skill Vex dengan lifecycle bertahap.

    CAST -> CHARGE -> RELEASE -> TRAVEL/AREA -> IMPACT -> AFTER -> FADE

    Q Arcane Orb        : aperture iris + conduit chevron + packet stream.
    W Sanity's Eclipse  : cincin retak + crystal spike naik + tick 20 frame.
    E Astral Imprisonment: kurungan bersegi + jeruji rune + shatter.
    R Essence Flux      : implosi -> ledakan void + serpihan radial.

    Bentuk BESAR (telegraph AOE, conduit, portal collapse) tetap milik
    renderer canvas — modul ini menambah lapisan HIDUP 60 fps di atasnya,
    bukan menggambar ulang bentuk yang sama.
    """

    #: Fraksi umur tiap fase (dipakai bersama oleh keempat skill).
    P_CAST = 0.12
    P_CHARGE = 0.30
    P_RELEASE = 0.42

    def __init__(self, skill, x, y, particles, radius=None, facing=1,
                 target=None, projectiles=None):
        self.skill = skill
        self.x = float(x)
        self.y = float(y)
        self.facing = 1 if facing >= 0 else -1
        self.particles = particles
        self.projectiles = projectiles
        self.target = target
        self.radius = float(radius) if radius else WORLD_RADIUS.get(
            skill, 80.0)
        self.age = 0.0
        self.duration = float(SKILL_TOTAL.get(skill, 1.0))
        self.active = True
        self.impacted = False
        self._emit = 0.0
        self._tick_acc = 0.0
        self._tick_count = 0
        self._spikes = None
        self._seed = int(abs(hash((skill, int(x), int(y)))) % 9973)
        self.origin = (self.x, self.y)

    # ------------------------------------------------------------------
    @property
    def progress(self):
        return max(0.0, min(1.0, self.age / max(0.0001, self.duration)))

    def phase(self):
        p = self.progress
        if p < self.P_CAST:
            return "CAST"
        if p < self.P_CHARGE:
            return "CHARGE"
        if p < self.P_RELEASE:
            return "RELEASE"
        if p < 0.80:
            return "AREA"
        return "FADE"

    # ------------------------------------------------------------------
    def update(self, dt):
        """Majukan lifecycle; return False kalau sudah selesai."""
        if not self.active:
            return False
        self.age += dt
        p = self.progress

        # posisi mengikuti target (E = kurungan menempel di target)
        if self.skill == "e" and self.target is not None:
            if getattr(self.target, "alive", False):
                self.x = float(self.target.x)
                self.y = float(self.target.y)

        fn = {
            "q": self._update_q,
            "w": self._update_w,
            "e": self._update_e,
            "r": self._update_r,
        }.get(self.skill)
        if fn is not None:
            fn(dt, p)

        if self.age >= self.duration:
            self.active = False
            return False
        return True

    # ------------------------------------------------------------------
    # Q — ARCANE ORB
    # ------------------------------------------------------------------
    def _update_q(self, dt, p):
        if p < self.P_CAST and not self.impacted:
            self.particles.burst(
                self.x + self.facing * 14, self.y - 34, 8,
                speed=(40, 130), life=(0.2, 0.42), size=(1, 3),
                colors=(P["fx_pale"], P["fx_light"], P["fx_bright"]),
                spread=math.tau, drag=2.4, shape="mote")
        if self.P_CAST <= p < self.P_CHARGE:
            self._emit += dt
            if self._emit >= 0.045:
                self._emit = 0.0
                ang = random.random() * math.tau
                rr = random.uniform(16, 34)
                spd = random.uniform(70, 150)
                self.particles.spawn(
                    self.x + self.facing * 14 + math.cos(ang) * rr,
                    self.y - 34 + math.sin(ang) * rr * 0.8,
                    -math.cos(ang) * spd, -math.sin(ang) * spd * 0.8,
                    random.uniform(0.2, 0.4), random.uniform(1.5, 3.0),
                    P["fx_light"], color_end=P["fx_deep"], drag=1.6,
                    shape="mote", rotation=random.random() * math.tau,
                    rotation_speed=random.uniform(-8, 8))
        if not self.impacted and p >= self.P_RELEASE:
            self.impacted = True
            tx = self.x + self.facing * self.radius * 0.6
            self.particles.burst(
                self.x + self.facing * 18, self.y - 34, 9,
                speed=(150, 320), life=(0.16, 0.34), size=(1, 3),
                colors=(P["fx_pale"], P["fx_bright"], P["rune_light"]),
                spread=0.7, direction=0.0 if self.facing > 0 else math.pi,
                drag=3.0, shape="streak")
            self.particles.stream(
                self.x + self.facing * 18, self.y - 34, tx, self.y - 40,
                6, life=(0.18, 0.34), size=(1, 3),
                colors=(P["fx_light"], P["fx_pale"]))

    # ------------------------------------------------------------------
    # W — SANITY'S ECLIPSE
    # ------------------------------------------------------------------
    def _update_w(self, dt, p):
        if self._spikes is None:
            n = 9
            self._spikes = []
            for i in range(n):
                a = (i / float(n)) * math.tau + _hash01(self._seed + i) * 0.3
                self._spikes.append({
                    "a": a,
                    "r": self.radius * (0.42 + 0.58 *
                                        _hash01(self._seed + i * 13)),
                    "h": 0.55 + 0.75 * _hash01(self._seed + i * 29),
                    "w": 0.7 + 0.6 * _hash01(self._seed + i * 31),
                })
        # damage tick: hero_skills menembak tiap 20 frame simulasi
        self._tick_acc += dt
        if self._tick_acc >= 20.0 / 60.0 and p < 0.92:
            self._tick_acc = 0.0
            self._tick_count += 1
            self._eclipse_tick()

        # debu mengambang di dalam cincin
        self._emit += dt
        if self._emit >= 0.09 and p < 0.88:
            self._emit = 0.0
            ang = random.random() * math.tau
            rr = random.uniform(self.radius * 0.2, self.radius * 0.95)
            self.particles.spawn(
                self.x + math.cos(ang) * rr,
                self.y + 26 + math.sin(ang) * rr * 0.5,
                random.uniform(-10, 10), -random.uniform(18, 52),
                random.uniform(0.4, 0.8), random.uniform(1.5, 3.0),
                P["crystal_mid"] if random.random() < 0.5 else P["fx_deep"],
                color_end=P["fx_deepest"], drag=1.2, shape="mote",
                rotation=random.random() * math.tau,
                rotation_speed=random.uniform(-5, 5))

    def _eclipse_tick(self):
        """Satu tick damage: spike berdenyut + pecahan kristal."""
        self.particles.ring(
            self.x, self.y + 26, self.radius * 0.9, 8,
            life=(0.25, 0.5), size=(2, 4),
            colors=(P["crystal_light"], P["crystal_mid"]),
            speed=(45, 120), squash=0.55, shape="crystal")
        self.particles.burst(
            self.x, self.y + 26, 4,
            speed=(40, 120), life=(0.2, 0.45), size=(2, 4),
            colors=(P["fx_dark"], P["fx_mid"]),
            spread=math.tau, drag=2.0, shape="mote")

    # ------------------------------------------------------------------
    # E — ASTRAL IMPRISONMENT
    # ------------------------------------------------------------------
    def _update_e(self, dt, p):
        self._emit += dt
        if self._emit >= 0.07:
            self._emit = 0.0
            ang = random.random() * math.tau
            rr = random.uniform(18, 30)
            self.particles.spawn(
                self.x + math.cos(ang) * rr,
                self.y - 6 + math.sin(ang) * rr * 1.15,
                -math.cos(ang) * random.uniform(20, 55),
                -math.sin(ang) * random.uniform(20, 55)
                - random.uniform(4, 18),
                random.uniform(0.35, 0.7), random.uniform(1.5, 3.0),
                P["astral_light"] if random.random() < 0.6
                else P["astral_bright"],
                color_end=P["astral_deep"], drag=1.4, shape="mote",
                rotation=random.random() * math.tau,
                rotation_speed=random.uniform(-6, 6))
        # shatter di akhir kurungan
        if not self.impacted and p >= 0.86:
            self.impacted = True
            self._astral_shatter()

    def _astral_shatter(self):
        self.particles.burst(
            self.x, self.y - 6, 12,
            speed=(90, 240), life=(0.24, 0.5), size=(2, 4),
            colors=(P["astral_bright"], P["astral_light"],
                    P["astral_hot"]),
            spread=math.tau, drag=2.2, shape="shard",
            rotation_speed=(-14.0, 14.0))
        if self.projectiles is not None:
            for i in range(4):
                a = (i / 4.0) * math.tau + 0.4
                self.projectiles.spawn(
                    self.x, self.y - 6,
                    self.x + math.cos(a) * 70.0,
                    self.y - 6 + math.sin(a) * 70.0,
                    speed=SHARD_SPEED * 0.8, radius=4.0,
                    kind="shard", gravity=180.0, max_lifetime=0.5,
                    on_impact=None)

    # ------------------------------------------------------------------
    # R — ESSENCE FLUX
    # ------------------------------------------------------------------
    def _update_r(self, dt, p):
        if p < self.P_RELEASE:
            # IMPLOSI: partikel tersedot ke dalam
            self._emit += dt
            if self._emit >= 0.035:
                self._emit = 0.0
                ang = random.random() * math.tau
                rr = random.uniform(self.radius * 0.4, self.radius * 0.9)
                spd = random.uniform(120, 230)
                self.particles.spawn(
                    self.x + math.cos(ang) * rr,
                    self.y + 12 + math.sin(ang) * rr * 0.6,
                    -math.cos(ang) * spd, -math.sin(ang) * spd * 0.6,
                    random.uniform(0.25, 0.45), random.uniform(1.5, 3.5),
                    P["fx_light"] if random.random() < 0.7 else P["gold"],
                    color_end=P["fx_deep"], drag=0.4, shape="streak",
                    rotation=random.random() * math.tau,
                    rotation_speed=random.uniform(-9, 9))
        elif not self.impacted:
            self.impacted = True
            self._flux_burst()

        if self.impacted and p < 0.72:
            self._emit += dt
            if self._emit >= 0.05:
                self._emit = 0.0
                ang = random.random() * math.tau
                rr = random.uniform(self.radius * 0.3, self.radius * 0.8)
                self.particles.spawn(
                    self.x + math.cos(ang) * rr,
                    self.y + 18 + math.sin(ang) * rr * 0.55,
                    math.cos(ang) * random.uniform(30, 90),
                    math.sin(ang) * random.uniform(20, 60)
                    - random.uniform(20, 70),
                    random.uniform(0.5, 0.95), random.uniform(3, 6),
                    P["smoke"], color_end=P["dust"], drag=1.1,
                    shape="smoke", back=True, fade_pow=1.4)

    def _flux_burst(self):
        """Ledakan: cincin ganda + serpihan radial (proyektil sungguhan)."""
        self.particles.ring(
            self.x, self.y + 14, self.radius * 0.35, 18,
            life=(0.35, 0.75), size=(2, 5),
            colors=(P["fx_bright"], P["fx_light"], P["gold"]),
            speed=(150, 330), squash=0.65, shape="streak", swirl=1.2)
        self.particles.ring(
            self.x, self.y + 22, self.radius * 0.5, 12,
            life=(0.5, 1.0), size=(3, 6),
            colors=(P["dust"], P["smoke"]),
            speed=(60, 150), squash=0.6, shape="smoke", back=True)
        if self.projectiles is not None:
            n = 8
            for i in range(n):
                a = (i / float(n)) * math.tau + 0.22
                tx = self.x + math.cos(a) * self.radius * 0.75
                ty = self.y + 14 + math.sin(a) * self.radius * 0.75 * 0.6
                self.projectiles.spawn(
                    self.x, self.y + 12, tx, ty,
                    speed=SHARD_SPEED * random.uniform(0.85, 1.25),
                    radius=5.0, kind="shard", gravity=120.0,
                    max_lifetime=0.55,
                    on_impact=self._shard_impact)

    def _shard_impact(self, proj):
        """Callback serpihan R: percikan kecil di ujung lintasan."""
        self.particles.burst(
            proj.hit_pos.x, proj.hit_pos.y, 4,
            speed=(60, 170), life=(0.14, 0.3), size=(1, 3),
            colors=(P["fx_pale"], P["fx_light"]),
            spread=math.tau, drag=3.2, shape="streak")

    # ------------------------------------------------------------------
    # DRAW — lapisan tanah (di bawah karakter)
    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        if not self.active:
            return
        fn = {
            "q": self._draw_ground_q,
            "w": self._draw_ground_w,
            "e": self._draw_ground_e,
            "r": self._draw_ground_r,
        }.get(self.skill)
        if fn is not None:
            fn(surface)

    def _draw_ground_q(self, surface):
        p = self.progress
        if p >= 0.62:
            return
        a = int(150 * (1.0 - p / 0.62))
        if a <= 4:
            return
        # jejak conduit di tanah: deret chevron (bukan garis polos)
        steps = 7
        for i in range(steps):
            t = (i + 1) / float(steps)
            gx = self.x + self.facing * self.radius * 0.62 * t
            gy = self.y + 30 - int(6 * t)
            ch = chevron_surface(5, P["fx_mid"], 2)
            if self.facing < 0:
                ch = _SURF_CACHE.get("chev5f") or _cache_put(
                    "chev5f", pygame.transform.flip(ch, True, False))
            ch.set_alpha(int(a * (0.35 + 0.65 * t)))
            surface.blit(ch, (int(gx) - ch.get_width() // 2,
                              int(gy) - ch.get_height() // 2))

    def _draw_ground_w(self, surface):
        p = self.progress
        if p >= 0.94:
            return
        fade = 1.0 - p / 0.94
        rr = int(self.radius)
        # kolam void gepeng
        g = ground_glow_surface(max(8, rr), P["fx_deep"], 0.34)
        g.set_alpha(int(255 * min(1.0, fade * 1.4)))
        surface.blit(g, (int(self.x) - g.get_width() // 2,
                         int(self.y) + 26 - g.get_height() // 2))
        # cincin retak bersegi (poligon tajam, bukan lingkaran mulus)
        sides = 11
        pts = []
        for i in range(sides):
            a = (i / float(sides)) * math.tau
            wob = 1.0 + 0.10 * math.sin(i * 2.7 + self._seed)
            pts.append((self.x + math.cos(a) * rr * wob,
                        self.y + 26 + math.sin(a) * rr * 0.55 * wob))
        buf = _scratch(int(rr * 2.4) + 8, int(rr * 1.6) + 8)
        ox = int(rr * 1.2) + 4
        oy = int(rr * 0.8) + 4
        sh = [(px - self.x + ox, py - self.y - 26 + oy) for px, py in pts]
        pygame.draw.polygon(buf, (*P["fx_deepest"], int(90 * fade)), sh)
        pygame.draw.polygon(buf, (*P["crystal_dark"], int(190 * fade)),
                            sh, 2)
        # retakan radial pendek
        for i, (px, py) in enumerate(pts):
            if i % 2:
                continue
            dx = px - self.x
            dy = py - (self.y + 26)
            n = max(1.0, math.hypot(dx, dy))
            L = 6 + 8 * _hash01(self._seed + i * 7)
            pygame.draw.line(
                buf, (*P["crystal_mid"], int(150 * fade)),
                (px - self.x + ox, py - self.y - 26 + oy),
                (px - self.x + ox + dx / n * L,
                 py - self.y - 26 + oy + dy / n * L), 1)
        surface.blit(buf, (int(self.x) - ox, int(self.y) + 26 - oy))

    def _draw_ground_e(self, surface):
        p = self.progress
        if p >= 0.9:
            return
        fade = 1.0 - p / 0.9
        rr = 26
        g = ground_glow_surface(rr, P["astral_deep"], 0.30)
        g.set_alpha(int(255 * min(1.0, fade * 1.3)))
        surface.blit(g, (int(self.x) - g.get_width() // 2,
                         int(self.y) + 26 - g.get_height() // 2))
        surface.blit(
            dashed_ring_surface(20, 2, P["astral_light"], segments=6,
                                span=0.5,
                                rot_step=self.age * 60.0),
            (int(self.x) - 26, int(self.y) + 26 - 26))

    def _draw_ground_r(self, surface):
        p = self.progress
        if p < 0.18:
            # lingkaran hisapan menyusut (implosi)
            t = p / 0.18
            rr = int(self.radius * (1.0 - 0.72 * t))
            surface.blit(
                dashed_ring_surface(max(5, rr), max(2, int(3 * (1 - t)) + 1),
                                    P["fx_mid"], segments=12, span=0.34,
                                    rot_step=-self.age * 140.0),
                (int(self.x) - rr - 8, int(self.y) + 20 - rr - 8))
            return
        if p >= 0.96:
            return
        t = (p - 0.18) / 0.78
        # cincin ledakan mengembang + hangus (dither dots, bukan bola)
        rr = int(self.radius * (0.25 + 1.0 * _ease_out(t)))
        a = int(215 * (1.0 - t) ** 1.4)
        if a > 5:
            er = ellipse_ring_surface(rr, max(3, int(rr * 0.58)),
                                      max(1, int(4 * (1 - t)) + 1),
                                      P["fx_mid"], 0)
            er.set_alpha(a)
            surface.blit(er, (int(self.x) - er.get_width() // 2,
                              int(self.y) + 20 - er.get_height() // 2))
        # kolam after-glow
        g = ground_glow_surface(max(10, int(self.radius * 0.75)),
                                P["fx_deep"], 0.30)
        g.set_alpha(int(210 * (1.0 - t)))
        surface.blit(g, (int(self.x) - g.get_width() // 2,
                         int(self.y) + 20 - g.get_height() // 2))
        # titik-titik hangus deterministik
        for i in range(14):
            a2 = _hash01(self._seed + i * 11) * math.tau
            rad = self.radius * (0.35 + 0.6 * _hash01(self._seed + i * 23))
            sx = int(self.x + math.cos(a2) * rad)
            sy = int(self.y + 20 + math.sin(a2) * rad * 0.55)
            pygame.draw.rect(surface, (*P["shadow"], int(150 * (1 - t))),
                             (sx, sy, 2, 2))

    # ------------------------------------------------------------------
    # DRAW — lapisan depan (di atas karakter)
    # ------------------------------------------------------------------
    def draw_front(self, surface):
        if not self.active:
            return
        fn = {
            "q": self._draw_front_q,
            "w": self._draw_front_w,
            "e": self._draw_front_e,
            "r": self._draw_front_r,
        }.get(self.skill)
        if fn is not None:
            fn(surface)

    def _draw_front_q(self, surface):
        p = self.progress
        fx = self.x + self.facing * 16
        fy = self.y - 34
        if p < self.P_CHARGE:
            # aperture iris: cincin putus-putus menyusut + glif
            t = p / self.P_CHARGE
            rr = int(6 + 30 * (1.0 - t))
            surface.blit(
                dashed_ring_surface(max(5, rr), 2, P["fx_light"],
                                    segments=8, span=0.42,
                                    rot_step=self.age * 220.0),
                (int(fx) - rr - 8, int(fy) - rr - 8))
            if p > self.P_CAST:
                gl = rune_surface(6, P["rune_light"], 2)
                gl.set_alpha(int(230 * (1 - t)))
                surface.blit(gl, (int(fx) - gl.get_width() // 2,
                                  int(fy) - gl.get_height() // 2))
        elif p < 0.66:
            # paket energi mengalir sepanjang conduit
            t = (p - self.P_CHARGE) / (0.66 - self.P_CHARGE)
            span = self.radius * 0.62
            for i in range(4):
                ft = (t * 1.6 + i * 0.25) % 1.0
                gx = fx + self.facing * span * ft
                gy = fy - 6 * ft
                a = int(235 * (1.0 - abs(ft - 0.5) * 1.2))
                if a <= 6:
                    continue
                ch = chevron_surface(6, P["fx_bright"], 2)
                if self.facing < 0:
                    ch = _SURF_CACHE.get("chev6f") or _cache_put(
                        "chev6f", pygame.transform.flip(ch, True, False))
                ch.set_alpha(a)
                surface.blit(ch, (int(gx) - ch.get_width() // 2,
                                  int(gy) - ch.get_height() // 2))
            # iris di ujung staff
            surface.blit(
                dashed_ring_surface(11, 2, P["fx_bright"], segments=6,
                                    span=0.5, rot_step=-self.age * 180.0),
                (int(fx) - 19, int(fy) - 19))

    def _draw_front_w(self, surface):
        p = self.progress
        if p >= 0.96 or self._spikes is None:
            return
        # spike tumbuh cepat, berdiri, lalu runtuh
        if p < 0.16:
            grow = _ease_out(p / 0.16)
        elif p < 0.80:
            grow = 1.0
        else:
            grow = max(0.0, 1.0 - (p - 0.80) / 0.16)
        if grow <= 0.02:
            return
        # denyut sinkron dengan tick damage (3x/detik)
        pulse = 0.82 + 0.18 * math.sin(self.age * 9.4)
        for i, sp in enumerate(self._spikes):
            sx = self.x + math.cos(sp["a"]) * sp["r"]
            sy = self.y + 26 + math.sin(sp["a"]) * sp["r"] * 0.55
            hgt = int(sp["h"] * 34 * grow * pulse)
            if hgt < 3:
                continue
            wdt = max(2, int(sp["w"] * 7 * grow))
            shard = rotated_cached(
                ("wspike", wdt, P["crystal_mid"], P["crystal_light"],
                 i % 2),
                crystal_shard_surface(wdt * 2, wdt, P["crystal_mid"],
                                      P["crystal_light"]),
                90)
            if i % 2:
                shard = _SURF_CACHE.get(("wspikeF", wdt)) or _cache_put(
                    ("wspikeF", wdt),
                    pygame.transform.flip(shard, True, False))
            shard.set_alpha(int(240 * min(1.0, grow * 1.2)))
            surface.blit(shard, (int(sx) - shard.get_width() // 2,
                                 int(sy) - hgt))
            # ujung menyala
            pygame.draw.rect(surface, (*P["crystal_shine"], 220),
                             (int(sx) - 1, int(sy) - hgt - 2, 3, 3))
        # cincin dalam berputar
        rr = int(self.radius * 0.55)
        surface.blit(
            dashed_ring_surface(rr, 2, P["crystal_light"], segments=9,
                                span=0.30, rot_step=self.age * 90.0),
            (int(self.x) - rr - 8, int(self.y) + 26 - rr - 8))

    def _draw_front_e(self, surface):
        p = self.progress
        if p >= 0.9:
            return
        grow = _ease_out(min(1.0, p / 0.14))
        fall = 1.0 if p < 0.80 else max(0.0, 1.0 - (p - 0.80) / 0.10)
        k = min(grow, fall)
        if k <= 0.02:
            return
        rx = int(30 * (0.7 + 0.3 * k))
        ry = int(38 * (0.7 + 0.3 * k))
        cy = self.y - 6
        buf = _scratch(rx * 2 + 16, ry * 2 + 16)
        cx = rx + 8
        cyb = ry + 8
        sides = 9
        pts = []
        for i in range(sides):
            a = (i / float(sides)) * math.tau + self.age * 0.9
            pts.append((cx + math.cos(a) * rx, cyb + math.sin(a) * ry))
        pygame.draw.polygon(buf, (*P["astral_deep"], int(85 * k)), pts)
        pygame.draw.polygon(buf, (*P["astral_light"], int(205 * k)), pts, 2)
        # jeruji kurungan (garis vertikal + sabuk horizontal)
        for i in range(sides):
            if i % 2 == 0:
                pygame.draw.line(buf, (*P["astral_mid"], int(150 * k)),
                                 (cx, cyb - ry), pts[i], 1)
        pygame.draw.line(buf, (*P["astral_bright"], int(170 * k)),
                         (cx - rx, cyb), (cx + rx, cyb), 1)
        # glif rune di sabuk
        for i in range(3):
            a = self.age * 1.6 + i * math.tau / 3
            gx = cx + math.cos(a) * rx * 0.82
            gy = cyb + math.sin(a) * ry * 0.82
            gl = rune_surface(3, P["astral_hot"], i)
            buf.blit(gl, (int(gx) - gl.get_width() // 2,
                          int(gy) - gl.get_height() // 2))
        surface.blit(buf, (int(self.x) - cx, int(cy) - cyb))

    def _draw_front_r(self, surface):
        p = self.progress
        if p < self.P_RELEASE:
            # IMPLOSI: chevron tersedot ke dalam
            t = p / self.P_RELEASE
            for i in range(6):
                a = (i / 6.0) * math.tau + self.age * 2.2
                rr = self.radius * (0.85 - 0.6 * _ease_in(t))
                gx = self.x + math.cos(a) * rr
                gy = self.y + 6 + math.sin(a) * rr * 0.6
                ch = rotated_cached(("chev7", P["fx_bright"], 2),
                                    chevron_surface(7, P["fx_bright"], 2),
                                    -int(math.degrees(a)) - 90)
                ch.set_alpha(int(230 * (1.0 - abs(t - 0.5) * 1.1)))
                surface.blit(ch, (int(gx) - ch.get_width() // 2,
                                  int(gy) - ch.get_height() // 2))
            return
        # LEDAKAN: cincin emas mengembang + glide rune
        t = (p - self.P_RELEASE) / (1.0 - self.P_RELEASE)
        if t < 0.7:
            st = 1.0 - t / 0.7
            rr = int(self.radius * (0.2 + 1.05 * _ease_out(t)))
            surface.blit(
                dashed_ring_surface(max(6, rr), max(2, int(4 * st) + 1),
                                    P["gold"], segments=10, span=0.36,
                                    rot_step=self.age * 200.0),
                (int(self.x) - rr - 8, int(self.y) + 8 - rr - 8))
            # glif rune melayang keluar
            for i in range(6):
                a = (i / 6.0) * math.tau + 0.3
                rad = self.radius * (0.3 + 0.7 * t)
                gx = self.x + math.cos(a) * rad
                gy = self.y + 8 + math.sin(a) * rad * 0.55
                gl = rune_surface(5, P["gold_hot"], i)
                gl.set_alpha(int(230 * st))
                surface.blit(gl, (int(gx) - gl.get_width() // 2,
                                  int(gy) - gl.get_height() // 2))
        # after-glow: pilar tipis memudar
        if 0.35 < t < 1.0:
            st = 1.0 - (t - 0.35) / 0.65
            hgt = int(60 * st)
            if hgt > 4:
                pl = _scratch(18, hgt + 4)
                pygame.draw.polygon(
                    pl, (*P["fx_mid"], int(140 * st)),
                    [(9, hgt + 2), (9 - 5, 2), (9 + 5, 2)])
                surface.blit(pl, (int(self.x) - 9, int(self.y) - hgt - 18))


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
            self._max_duration = max(self._max_duration,
                                     self.shake_duration)

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

    Flag ``VEX_FX_ENABLED`` TIDAK menahan freeze karakter lain — ia
    hanya mengatur apakah FX Vex sendiri ikut jalan.
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
    ("ANTICIPATION", 0.00, 0.13),
    ("WINDUP",       0.13, 0.28),
    ("SWING",        0.28, 0.50),
    ("IMPACT",       0.50, 0.64),
    ("FOLLOW",       0.64, 0.80),
    ("RECOVERY",     0.80, 1.00),
)

#: Titik pendaratan (progress) — dipakai untuk release orb + hitbox.
ATTACK_IMPACT_POINT = 0.56
ATTACK_SWING_END = 0.66

#: Jendela aktif senjata (ARC-BASED swing, bukan lerp linear).
SWING_START = 0.26
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

    Renderer adalah satu sumber kebenaran; kalau renderer berubah, fase
    FX ikut berubah tanpa perlu menyentuh modul ini lagi.
    """
    global ATTACK_PHASES, ATTACK_SWING_END, ATTACK_IMPACT_POINT
    G = _renderer()
    if G is None:
        return
    try:
        windup = float(G.ATTACK_WINDUP_END)
        swing_end = float(G.ATTACK_SWING_END)
        impact = float(G.ATTACK_IMPACT)
    except Exception:                      # pragma: no cover
        return
    if not (0.05 < windup < impact < swing_end < 1.0):
        return
    ATTACK_SWING_END = swing_end
    ATTACK_IMPACT_POINT = impact
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, windup * 0.46),
        ("WINDUP",       windup * 0.46, windup),
        ("SWING",        windup, impact - 0.06),
        ("IMPACT",       impact - 0.06, impact + 0.08),
        ("FOLLOW",       impact + 0.08, max(impact + 0.10, swing_end)),
        ("RECOVERY",     max(impact + 0.10, swing_end), 1.00),
    )


_resolve_timeline()


# ============================================================================
# 12.  GEOMETRI STAFF  —  jembatan ke pose renderer (satu sumber kebenaran)
# ============================================================================

def render_scale(hero):
    """Skala canvas->layar untuk hero ini (fallback: skala pipeline)."""
    scale = float(getattr(hero, "_render_scale", 0.0) or 0.0)
    if scale <= 0.02:
        try:
            from heroes import _get_hero_scale
            scale = float(_get_hero_scale(
                getattr(hero, "hero_type", "vex")))
        except Exception:                  # pragma: no cover
            scale = 1.0
    return scale


def staff_points(hero, x=None, y=None, progress=None):
    """Posisi layar (pangkal, gagang, orb) staff Vex dari pose renderer.

    Memakai geometri lokal renderer (``_orb_tip_local`` untuk orb,
    ``_staff_grip_local`` untuk gagang, ``_staff_butt_local`` untuk
    pangkal) lalu dikonversi ke skala layar lewat ``RIG_SCALE`` x
    ``_render_scale``, sehingga trail menempel PERSIS di orb staff —
    bukan di perkiraan.
    Return ((butt, grip, orb), action).
    """
    G = _renderer()
    h = hero
    px = float(getattr(h, "x", 0.0)) if x is None else float(x)
    py = float(getattr(h, "y", 0.0)) if y is None else float(y)
    f = 1.0 if getattr(h, "facing",
                       getattr(h, "direction", 1)) >= 0 else -1.0
    s = render_scale(h)
    phase = float(getattr(h, "pulse", 0.0))
    ap = float(getattr(h, "_vx_attack_progress", 0.0)) \
        if progress is None else float(progress)

    action = "idle"
    if getattr(h, "_vx_attack_active", False) or progress is not None:
        action = "attack"
    elif getattr(h, "_moving_cached", False):
        action = "walk"

    if G is not None:
        try:
            orb_l = G._orb_tip_local(phase, action, ap)
            grip_l = G._staff_grip_local(phase, action, ap)
            butt_l = G._staff_butt_local(phase, action, ap)
            rs = float(getattr(G, "RIG_SCALE", 1.52))
        except Exception:                  # pragma: no cover - tool minimal
            orb_l, grip_l, butt_l = (32, -44), (17, -24), (2, -4)
            rs = 1.52
    else:                                  # pragma: no cover
        orb_l, grip_l, butt_l = (32, -44), (17, -24), (2, -4)
        rs = 1.52

    def to_screen(lx, ly):
        return (px + lx * rs * f * s, py + ly * rs * s)

    return (to_screen(*butt_l), to_screen(*grip_l),
            to_screen(*orb_l)), action


def swing_hitbox(hero, x=None, y=None, progress=None):
    """Hitbox ayunan Vex (kerucut depan) — dipakai overlay debug.

    Jangkauan = ``hero.range`` (dunia) di depan karakter; tinggi
    mengikuti skala sprite supaya sejajar dengan badan.
    """
    h = hero
    px = float(getattr(h, "x", 0.0)) if x is None else float(x)
    py = float(getattr(h, "y", 0.0)) if y is None else float(y)
    f = 1.0 if getattr(h, "facing",
                       getattr(h, "direction", 1)) >= 0 else -1.0
    rng = float(getattr(h, "range", 130) or 130)
    s = max(0.5, render_scale(h))
    top = -46 * s
    height = 74 * s
    return pygame.Rect(px if f > 0 else px - rng, py + top, rng, height)


# ============================================================================
# 13.  DIRECTOR  —  satu per unit Vex
# ============================================================================

class VexFXDirector:
    """Mengikat semua subsistem FX untuk satu instance Vex.

    Director adalah animation controller + event bus FX:
      * state machine berprioritas (IDLE..DEATH) dengan delta-time,
      * progress serangan dihitung SENDIRI dari ``attack_timer`` 60 Hz
        (lebih halus daripada ``_vx_attack_progress`` yang hanya
        diperbarui saat cache sprite miss),
      * deteksi edge (attack / skill / prison / eclipse / flux / hurt /
        death),
      * trail dari posisi staff NYATA,
      * partikel, proyektil, impact, SkillFX, shake, hit-stop.
    """

    def __init__(self, hero):
        _sync_palette()
        self.hero = hero
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.projectiles = ProjectileSystem(self.particles, MAX_PROJECTILES)
        self.trail = SwingTrail()
        self.impacts = []
        self.skills = []
        self.state = "IDLE"
        self.prev_state = "IDLE"
        self.state_time = 0.0
        self.anim_phase = "IDLE"
        self.attack_progress = 0.0
        self._attack_live = False
        self._attack_frame = 0
        self._prev_timer = -1
        self.swing_active = False
        self._swing_seen = False
        self._orb_released = False
        self._skill_seen = None
        self._prison_seen = 0
        self._eclipse_seen = 0
        self._flux_seen = 0
        self._prison_stuck = 0.0
        self._eclipse_stuck = 0.0
        self._flux_stuck = 0.0
        self._last_hp = None
        self._was_alive = True
        self._last_x = None
        self._last_y = None
        self._moving = False
        self._emit_idle = 0.0
        self._step_acc = 0.0
        self.hit_flash = 0.0
        self.time = 0.0
        self.frames = 0
        #: stempel waktu (ms) langkah terakhir director ini — dipakai
        #: ``_advance`` supaya tiap unit maju TEPAK SATU KALI per frame
        #: gambar, berapa pun jumlah Vex yang ikut bertempur.
        self._last_ms = None

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def on_swing_start(self, x, y, facing):
        """Awal ayunan: reset trail + debu antisipasi + rune menyala."""
        self.trail.reset()
        self.trail.overcharged = bool(getattr(self.hero, "active_skill",
                                              None))
        self.swing_active = True
        self._orb_released = False
        self.particles.burst(
            x - facing * 6, y + 40, 4,
            speed=(24, 76), life=(0.2, 0.42), size=(2, 4),
            colors=(P["dust"], P["dust_light"]),
            spread=1.1, direction=math.pi if facing > 0 else 0.0,
            gravity=90.0, drag=2.6, shape="pixel", back=True)
        self.particles.burst(
            x, y - 44, 5,
            speed=(30, 90), life=(0.18, 0.38), size=(1, 3),
            colors=(P["fx_light"], P["fx_mid"]),
            spread=math.tau, drag=2.4, shape="mote", swirl=2.0)

    def on_swing_end(self):
        self.swing_active = False

    def on_orb_release(self, x, y, facing):
        """Titik IMPACT ayunan: orb dilepas dari ujung staff.

        Proyektil yang benar-benar membawa damage adalah milik
        ``_entity`` (jalur ranged generik); yang ini adalah PAKET
        VISUAL pelepasan supaya setiap tebasan terasa "keluar" dari
        staff walau targetnya meleset.
        """
        (_butt, _grip, orb), _action = staff_points(
            self.hero, progress=self.attack_progress)
        ox, oy = orb
        ang = math.atan2(-0.18, facing)
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(ox, oy, ang, 0.45, kind="orb"))
        self.particles.burst(
            ox, oy, 6,
            speed=(90, 210), life=(0.14, 0.32), size=(1, 3),
            colors=(P["fx_pale"], P["fx_bright"], P["rune_light"]),
            spread=1.2, direction=ang, drag=3.4, shape="streak")
        self.particles.ring(
            ox, oy, 8, 7, life=(0.16, 0.32), size=(1, 3),
            colors=(P["fx_light"], P["fx_mid"], P["fx_bright"]),
            speed=(40, 100), squash=0.9, shape="mote", swirl=1.6)
        shake(2.6, 0.14)

    def on_cast(self, x, y, skill):
        """Skill dilepas: buat SkillFX + bahasa per-skill + shake."""
        if len(self.skills) >= MAX_SKILLS - 1:
            self.skills.pop(0)
        h = self.hero
        f = 1 if getattr(h, "facing", getattr(h, "direction", 1)) >= 0 \
            else -1
        radius = None
        target = None
        if skill == "q":
            try:
                radius = float(getattr(h, "skill_range", 0)) or None
            except Exception:                  # pragma: no cover
                radius = None
        elif skill == "e":
            target = getattr(h, "_astral_prison_target", None)
            radius = WORLD_RADIUS["e"]
        fx = SkillFX(skill, x, y, self.particles, radius, facing=f,
                     target=target, projectiles=self.projectiles)
        self.skills.append(fx)
        self.trail.overcharged = True

        if skill == "q":
            # Q Arcane Orb: aperture + stream + conduit
            self.particles.burst(
                x + f * 16, y - 34, 10, speed=(120, 280),
                life=(0.16, 0.36), size=(1, 3),
                colors=(P["fx_pale"], P["fx_bright"], P["rune_light"]),
                spread=0.9, direction=0.0 if f > 0 else math.pi,
                drag=3.0, shape="streak")
            shake(4.2, 0.20)
            hit_stop(0.035)
        elif skill == "w":
            # W Sanity's Eclipse: cincin kristal + debu tanah
            self.particles.ring(
                x, y + 26, WORLD_RADIUS["w"] * 0.9, 12,
                life=(0.3, 0.65), size=(2, 4),
                colors=(P["crystal_light"], P["crystal_mid"]),
                speed=(60, 150), squash=0.55, shape="crystal")
            self.particles.burst(
                x, y + 30, 8, speed=(50, 140), life=(0.3, 0.6),
                size=(2, 4), colors=(P["dust"], P["dust_light"]),
                spread=2.6, direction=-math.pi / 2, gravity=240.0,
                drag=1.6, shape="pixel", back=True)
            shake(5.5, 0.24)
            hit_stop(0.042)
        elif skill == "e":
            # E Astral Imprisonment: kurungan ungu + rune
            tx = float(getattr(target, "x", x + f * 90.0))
            ty = float(getattr(target, "y", y))
            self.particles.burst(
                tx, ty - 6, 10, speed=(60, 170), life=(0.25, 0.55),
                size=(1, 3),
                colors=(P["astral_bright"], P["astral_light"],
                        P["astral_hot"]),
                spread=math.tau, drag=2.0, shape="mote", swirl=2.4)
            shake(3.4, 0.18)
        elif skill == "r":
            # R Essence Flux: hisapan + ledakan (lihat SkillFX._flux_burst)
            self.particles.burst(
                x, y + 12, 12, speed=(120, 260), life=(0.2, 0.45),
                size=(2, 4),
                colors=(P["fx_bright"], P["fx_light"], P["gold"]),
                spread=math.tau, drag=1.0, shape="streak", swirl=2.2)
            self.particles.burst(
                x, y + 30, 10, speed=(40, 130), life=(0.4, 0.85),
                size=(3, 6), colors=(P["dust"], P["smoke"]),
                spread=2.6, direction=-math.pi / 2, gravity=-18.0,
                drag=1.5, shape="smoke", back=True)
            shake(11.0, 0.42)
            hit_stop(0.075)

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="orb"):
        """Benturan mengenai target: flash, spark, debris, shake, hit-stop."""
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind))

        n = int(8 + 6 * min(2.0, power)) + (5 if crit else 0)
        if kind == "astral":
            cols = (P["astral_hot"], P["astral_bright"], P["astral_light"])
            shp = "shard"
        elif kind == "spike":
            cols = (P["crystal_shine"], P["crystal_light"],
                    P["crystal_mid"])
            shp = "crystal"
        elif kind == "flux":
            cols = (P["gold_hot"], P["fx_pale"], P["fx_bright"])
            shp = "streak"
        else:
            cols = (P["fx_pale"], P["fx_bright"], P["rune_light"])
            shp = "streak"
        self.particles.burst(
            x, y, n, speed=(110, 330), life=(0.16, 0.42),
            size=(1, 3), colors=cols,
            spread=2.4, direction=angle, drag=3.6, shape=shp)
        self.particles.burst(
            x, y, 5 + (3 if crit else 0),
            speed=(70, 190), life=(0.28, 0.62), size=(2, 4),
            colors=(P["staff_shine"], P["staff_light"], P["fx_dark"]),
            gravity=460.0, drag=1.1, shape="shard",
            rotation_speed=(-16.0, 16.0))
        self.particles.burst(
            x, y + 6, 3,
            speed=(20, 60), life=(0.3, 0.55), size=(3, 5),
            colors=(P["smoke"], P["dust"]),
            gravity=-26.0, drag=1.6, shape="smoke", back=True)

        shake(3.4 + 3.2 * min(2.0, power) + (2.6 if crit else 0.0),
              0.16 + 0.08 * min(2.0, power))
        hit_stop(0.036 + 0.02 * min(1.5, power) + (0.014 if crit else 0.0))

    def on_hurt(self, amount=1.0):
        """Vex terkena serangan: hit flash + percikan void buyar."""
        self.hit_flash = 0.15
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        self.particles.burst(
            hx, hy - 14, 6, speed=(70, 190), life=(0.18, 0.36),
            size=(1, 3), colors=(P["fx_bright"], P["fx_light"]),
            drag=3.0, shape="streak")

    def on_death(self):
        """Vex tumbang: void buyar + jubah runtuh + debu besar."""
        h = self.hero
        x = float(getattr(h, "x", 0.0))
        y = float(getattr(h, "y", 0.0))
        self.particles.burst(
            x, y - 18, 14, speed=(50, 180), life=(0.5, 1.05),
            size=(2, 4),
            colors=(P["fx_light"], P["fx_dark"], P["fx_deep"]),
            spread=math.tau, drag=1.4, shape="mote", swirl=1.6,
            fade_pow=1.4)
        self.particles.burst(
            x, y - 40, 8, speed=(40, 130), life=(0.5, 0.95),
            size=(2, 4),
            colors=(P["astral_light"], P["astral_mid"]),
            spread=math.tau, drag=1.6, shape="rune",
            rotation_speed=(-8.0, 8.0))
        self.particles.burst(
            x, y + 32, 8, speed=(30, 95), life=(0.5, 0.9),
            size=(3, 6), colors=(P["dust"], P["smoke"]),
            spread=2.6, direction=-math.pi / 2, gravity=-16.0,
            drag=1.5, shape="smoke", back=True)
        self.trail.reset()
        shake(4.5, 0.32)

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
        if skill == "r":
            return "SPECIAL"
        if skill in ("q", "w", "e"):
            return "SKILL"
        if int(getattr(h, "_essence_flux_timer", 0) or 0) > 0:
            return "SPECIAL"
        if int(getattr(h, "_sanity_eclipse_timer", 0) or 0) > 0 or \
                int(getattr(h, "_astral_prison_timer", 0) or 0) > 0:
            return "SKILL"
        if getattr(h, "_is_dashing", False):
            return "RUN"
        if self._attack_live:
            ph = attack_phase(self.attack_progress)
            if ph in ("SWING", "IMPACT"):
                return "SWING"
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
            locked = self.state in ("DEATH",) and \
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
        cd = max(2, int(getattr(h, "attack_cooldown", 46)))
        timer = int(getattr(h, "attack_timer",
                            getattr(h, "timer", 0)) or 0)
        prev = self._prev_timer
        # Serangan baru = timer NAIK (tahan berapa pun langkah simulasi
        # yang terlewat antar-gambar).
        if prev < 0:
            # Pengamatan pertama.  Kalau timer sudah berjalan, director
            # dibuat SETELAH ayunan dimulai (mis. unit baru muncul di
            # tengah pertarungan) — gabung di tengah saja daripada
            # membatalkan seluruh animasi.
            if timer > 0:
                self._attack_live = True
                self._orb_released = False
        elif timer > prev:
            self._attack_live = True
            self._attack_frame = 0
            self._orb_released = False
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

        # ── deteksi kematian ─────────────────────────────────────────
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

        # ── skill cast detection (edge-triggered, dua sumber) ─────────
        # active_skill = jendela visual pipeline; timer mentah = jendela
        # gameplay.  Edge pada salah satunya cukup untuk memicu cast.
        skill = getattr(h, "active_skill", None)
        if skill != self._skill_seen:
            if skill in ("q", "w", "e", "r"):
                self.on_cast(hx, hy, skill)
            self._skill_seen = skill

        # ── W: Sanity's Eclipse (180 langkah = 3.0 s) ─────────────────
        ecl = int(getattr(h, "_sanity_eclipse_timer", 0) or 0)
        if ecl > self._eclipse_seen and self._eclipse_seen == 0 and \
                skill != "w":
            self.on_cast(hx, hy, "w")
        self._eclipse_seen = ecl

        # ── E: Astral Imprisonment (150 langkah = 2.5 s) ──────────────
        pri = int(getattr(h, "_astral_prison_timer", 0) or 0)
        if pri > self._prison_seen and self._prison_seen == 0 and \
                skill != "e":
            self.on_cast(hx, hy, "e")
        self._prison_seen = pri

        # ── R: Essence Flux (60 langkah = 1.0 s visual) ───────────────
        flx = int(getattr(h, "_essence_flux_timer", 0) or 0)
        if flx > self._flux_seen and self._flux_seen == 0 and \
                skill != "r":
            self.on_cast(hx, hy, "r")
        self._flux_seen = flx

        # ── swing detection (edge-triggered pada jendela ayunan) ──────
        ap = self.attack_progress
        swinging = self._attack_live and SWING_START <= ap <= SWING_END
        if swinging and not self._swing_seen:
            self.on_swing_start(hx, hy, facing)
        elif not swinging and self._swing_seen:
            self.on_swing_end()
        self._swing_seen = swinging

        # ── pelepasan orb di titik IMPACT ─────────────────────────────
        if swinging and not self._orb_released and \
                ap >= ATTACK_IMPACT_POINT:
            self._orb_released = True
            self.on_orb_release(hx, hy, facing)

        # ── rekam posisi staff saat swing -> trail ────────────────────
        if alive and swinging:
            (_butt, grip, orb), _action = staff_points(h, progress=ap)
            # pita hanya menempati bagian LUAR staff (orb + sedikit
            # batang) — bahasa caster: energi keluar dari orb.
            inner = (grip[0] + (orb[0] - grip[0]) * 0.34,
                     grip[1] + (orb[1] - grip[1]) * 0.34)
            outer = (grip[0] + (orb[0] - grip[0]) * 1.30,
                     grip[1] + (orb[1] - grip[1]) * 1.30)
            self.trail.push(inner, outer)

        # ── emisi idle: mote void mengambang (rate-limited) ───────────
        if alive and not self._attack_live and not self.skills:
            self._emit_idle += dt
            if self._emit_idle >= 0.16:
                self._emit_idle = 0.0
                self.particles.spawn(
                    hx + random.uniform(-16, 16),
                    hy + random.uniform(24, 46),
                    random.uniform(-8, 8), -random.uniform(10, 30),
                    random.uniform(0.6, 1.2), random.uniform(1, 2),
                    P["fx_dark"], color_end=P["fx_deepest"], drag=1.0,
                    shape="mote", back=True,
                    rotation=random.random() * math.tau,
                    rotation_speed=random.uniform(-4, 4))

        # ── debu langkah saat bergerak (foot dust, rate-limited) ──────
        if alive and self._moving and not self._attack_live:
            self._step_acc += dt
            if self._step_acc >= 0.18:
                self._step_acc = 0.0
                self.particles.spawn(
                    hx - facing * 8 + random.uniform(-3, 3),
                    hy + 42, -facing * random.uniform(14, 34),
                    -random.uniform(4, 16),
                    random.uniform(0.22, 0.4), random.uniform(2, 3),
                    P["dust"], color_end=P["smoke"], gravity=60.0,
                    drag=2.4, shape="pixel", back=True)

        # ── pembersihan skill yang timer-nya MACET ────────────────────
        # Pagar anti-beku: timer gameplay SELALU berkurang tiap langkah
        # simulasi.  Kalau hero tewas di tengah skill, ``Hero.update``
        # berhenti jalan dan timer membeku > 0 — tanpa pagar ini, emisi
        # skill akan hidup tanpa batas di mayat.
        prison_stuck = self._guard_stuck("prison", pri, dt)
        eclipse_stuck = self._guard_stuck("eclipse", ecl, dt)
        flux_stuck = self._guard_stuck("flux", flx, dt)
        if not alive or prison_stuck > 15.0 or eclipse_stuck > 15.0 or \
                flux_stuck > 15.0:
            for fx in self.skills:
                if fx.skill in ("w", "e", "r"):
                    fx.active = False

        self.trail.update(dt)
        self.particles.update(dt)
        self.projectiles.update(dt)

        if self.impacts:
            self.impacts = [i for i in self.impacts if i.update(dt)]
        if self.skills:
            self.skills = [s for s in self.skills if s.update(dt)]

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
        g = glow_surface(r, P["astral_bright"], self.hit_flash / 0.15 * 0.7)
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

    # attack range
    pygame.draw.circle(surface, (255, 140, 60), (x, y), rng, 1)
    # hurtbox
    pygame.draw.circle(surface, (90, 220, 255), (x, y), rad, 1)
    # hitbox serangan (kerucut depan saat swing)
    if director.anim_phase in ("SWING", "IMPACT"):
        pygame.draw.rect(surface, (255, 230, 90), swing_hitbox(h), 1)
    # radius AOE gameplay W/R saat aktif
    if int(getattr(h, "_sanity_eclipse_timer", 0) or 0) > 0:
        pygame.draw.circle(surface, (140, 240, 255), (x, y + 26),
                           int(WORLD_RADIUS["w"]), 1)
    if int(getattr(h, "_essence_flux_timer", 0) or 0) > 0:
        pygame.draw.circle(surface, (255, 210, 90), (x, y + 20),
                           int(WORLD_RADIUS["r"]), 1)
    # kurungan E
    if int(getattr(h, "_astral_prison_timer", 0) or 0) > 0:
        tgt = getattr(h, "_astral_prison_target", None)
        if tgt is not None:
            pygame.draw.circle(surface, (200, 130, 255),
                               (int(getattr(tgt, "x", x)),
                                int(getattr(tgt, "y", y))), 30, 1)
    # staff anchor (debug geometri trail)
    try:
        (_butt, grip, orb), _action = staff_points(h)
        pygame.draw.line(surface, (120, 255, 220),
                         (int(grip[0]), int(grip[1])),
                         (int(orb[0]), int(orb[1])), 1)
        pygame.draw.rect(surface, (255, 255, 120),
                         (int(orb[0]) - 2, int(orb[1]) - 2, 4, 4), 1)
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
        "VEX  %s / %s" % (st["state"], st["phase"]),
        "atkT %.2f  skill %s" % (st["attack_t"],
                                 getattr(h, "active_skill", None)),
        "ecl %d  prison %d  flux %d" % (
            int(getattr(h, "_sanity_eclipse_timer", 0) or 0),
            int(getattr(h, "_astral_prison_timer", 0) or 0),
            int(getattr(h, "_essence_flux_timer", 0) or 0)),
        "part %d  proj %d  imp %d  trail %d" % (
            st["particles"], st["projectiles"], st["impacts"],
            st["trail"]),
        "shake %.1f  stop %d  fps %d" % (
            SHAKE.amount, HITSTOP.frames, fps),
    ]
    for i, txt in enumerate(lines):
        img = font.render(txt, True, (200, 245, 255))
        surface.blit(img, (x - 60, y - 104 + i * 13))


# ============================================================================
# 15.  API MODUL  —  registry, tick, hook render
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Vex."""
    _sync_palette()
    d = getattr(hero, "_vx_fx", None)
    if d is None:
        d = VexFXDirector(hero)
        try:
            hero._vx_fx = d
        except Exception:                  # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:           # jangkar tua dibuang
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    """Lepas director dari registry DAN penanda milik-nya di unit.

    Penting: kalau penanda ``_vx_live_fx`` ditinggal sementara director
    sudah tidak dipanggil lagi, renderer akan terus MELEWATI smear
    di-canvas padahal tidak ada yang menggantinya -> efek hilang total.
    """
    try:
        if director.hero is not None:
            director.hero._vx_fx = None
            director.hero._vx_live_fx = False
            director.hero._skip_renderer_projectiles = False
    except Exception:                      # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit ini (dipanggil renderer / pipeline).

    Sekalian menandai unit supaya renderer TIDAK menggambar efek yang
    sekarang dimiliki lapisan hidup (smear ayunan + orb canvas).
    Return True kalau lapisan hidup jadi dipakai.
    """
    if not VEX_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                      # pragma: no cover
        return False
    try:
        hero._vx_live_fx = True
        # Orb serangan skill sekarang milik lapisan hidup (60 fps,
        # layar 1:1) — jalur canvas dilewati agar tidak dobel.
        hero._skip_renderer_projectiles = True
    except Exception:                      # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini.

    Dipakai renderer untuk memutuskan apakah smear ayunan di-canvas
    masih perlu digambar (fallback) atau tidak.  Unit tanpa director —
    potongan portrait, alat uji, renderer yang dipanggil langsung, jalur
    BOSS lane — tetap memakai jalur canvas lama, jadi tidak ada visual
    yang hilang kalau modul FX tidak tersedia.
    """
    if not getattr(hero, "_vx_live_fx", False):
        return False
    d = getattr(hero, "_vx_fx", None)
    # Penanda saja tidak cukup: director-nya harus masih TERDAFTAR.
    return d is not None and d in _DIRECTORS


def _advance(director):
    """Majukan SATU director sesuai waktu sejak langkah terakhirnya.

    Mengapa tidak sekadar memanggil ``tick()`` dari ``draw_ground_layer``?
    Karena ``tick()`` memajukan SEMUA director.  Kalau 8 Vex dirender
    dalam satu frame, jalur itu berarti 8 x 8 = 64 pembaruan director per
    frame (O(n^2)) walau hasil akhirnya identik.  Dengan stempel waktu
    per director, tiap unit maju tepat sekali per frame gambar — O(n) —
    dan unit yang tidak dirender (di luar layar) tidak menghabiskan
    waktu sama sekali.

    Bus game-feel (clock + peluruhan shake) TETAP disentuh lewat
    ``combat_feel.fx_dt()`` supaya guncangan layar tidak pernah
    tertinggal, apa pun jumlah karakter yang bertempur.
    """
    if not VEX_FX_ENABLED or director is None:
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
    frame walau beberapa karakter ikut bertempur).  Pemanggilan kedua
    dalam MILIDETIK yang sama (dua unit Vex di satu frame) tidak
    memajukan director dua kali.
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
    """Jumlah partikel Vex hidup di seluruh arena (untuk HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def total_projectiles():
    """Jumlah proyektil visual Vex hidup (untuk HUD perf)."""
    return sum(d.projectiles.count() for d in _DIRECTORS)


# --- hook yang dipanggil heroes/__init__.py --------------------------------

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: dipanggil SEBELUM sprite hero di-blit."""
    if not VEX_FX_ENABLED:
        return
    attach(hero)
    d = director_for(hero)
    _advance(d)
    d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: dipanggil SETELAH sprite hero di-blit."""
    if not VEX_FX_ENABLED:
        return
    director_for(hero).draw_front(surface)


# --- hook yang dipanggil _entity.py ----------------------------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Serangan jarak dekat Vex mengenai target (damage instan).

    Vex ranged (range 130) jadi jalur ini hanya aktif kalau ia dipakai
    di jalur BOSS / item mengubahnya jadi melee; API tetap disediakan
    demi paritas dengan modul karakter lain.
    """
    if not VEX_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except Exception:                      # pragma: no cover
        power = 1.0
    tx = float(getattr(target, "x", 0)) if target is not None else 0.0
    ty = float(getattr(target, "y", 0)) if target is not None else 0.0
    ang = math.atan2(float(getattr(hero, "y", 0.0)) - ty,
                     tx - float(getattr(hero, "x", 0.0)))
    director_for(hero).on_impact(tx, ty - 10, ang, power, crit, "orb")


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False):
    """Proyektil Vex mendarat (jalur ranged generik ``_entity``)."""
    if not VEX_FX_ENABLED or hero is None:
        return
    try:
        power = 0.75 + min(1.7, float(damage) / 42.0)
    except Exception:                      # pragma: no cover
        power = 1.0
    director_for(hero).on_impact(float(x), float(y) - 10, float(angle),
                                 power, crit, "orb")


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """Skill Vex meledak di sebuah titik (dipakai tooling/audit)."""
    if not VEX_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    if len(d.skills) >= MAX_SKILLS - 1:
        d.skills.pop(0)
    f = 1 if getattr(hero, "facing",
                     getattr(hero, "direction", 1)) >= 0 else -1
    d.skills.append(SkillFX(skill, x, y, d.particles, radius, facing=f,
                            projectiles=d.projectiles))


def notify_skill_cast(hero, skill):
    """Skill Vex dilepas dari luar (auto-cast guard / tooling)."""
    if not VEX_FX_ENABLED or hero is None:
        return
    director_for(hero).on_cast(float(getattr(hero, "x", 0.0)),
                               float(getattr(hero, "y", 0.0)),
                               skill)


def notify_hurt(hero, amount=1.0):
    """Vex terkena damage dari luar (tanpa menunggu watch hp)."""
    if not VEX_FX_ENABLED or hero is None:
        return
    director_for(hero).on_hurt(amount)
