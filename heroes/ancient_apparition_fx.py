# ============================================================================
# heroes/ancient_apparition_fx.py
# ----------------------------------------------------------------------------
# ANCIENT APPARITION — COMBAT / GAME-FEEL ENGINE  (lapisan layar, hidup 60 fps)
#
# Badan Ancient Apparition digambar lewat ``_NS_ancient_apparition``
# (bosses/level3.py) ke canvas yang DI-CACHE lalu di-scale oleh pipeline hero.
# Semua yang butuh gerak 60 fps sejati — arc ayunan cakar, trail, partikel
# salju/es, proyektil shard, vortex Q, beam W, ledakan E, erupsi R, impact
# flash, shockwave, debris, screen shake, hit-stop — HIDUP DI SINI: digambar
# langsung ke layar skala 1:1 tiap frame dengan delta-time nyata, tidak ikut
# beku saat pose sprite di-cache dan tidak menyusut oleh smoothscale.
#
# Pembagian kerja (sengaja — supaya tidak ada efek yang digambar 2x):
#
#   RENDERER (canvas, ter-cache)          MODUL INI (layar, hidup)
#   -----------------------------         --------------------------------
#   rig wraith es + crown + wajah         arc ayunan cakar dari histori posisi
#   skirt shard, orbit splinter           trail sapuan cakar (ribbon polygon)
#   bayangan kontak, platform beku        partikel (salju, mist, serpihan, debu)
#   TELEGRAPH ground Q/R (fallback)       PROYEKTIL shard/bolt (sistem nyata)
#   beam W / bolt E (fallback canvas)     VORTEX Q / BEAM W / BLAST E / R hidup
#   pose idle/walk/cast/attack            IMPACT FX + flash + hit-stop + shake
#                                         shatter kematian, overlay DEBUG
#
# 100% PROSEDURAL — tidak ada PNG/JPG/GIF, tidak ada sprite sheet, tidak ada
# tekstur unduhan.  Semua bentuk dibangun dengan pygame.draw + pygame.Surface
# + pygame.transform + pygame.Vector2.
#
# Isi modul
#   AA_PALETTE            palette khusus karakter (kontrak 9 kunci + ramp es)
#   Particle              partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem        pool + burst + stream + ring, reusable + cap keras
#   SlashTrail            trail senjata prosedural dari histori ujung cakar
#   ApparitionProjectile  proyektil modular (spawn->travel->hit->destroy)
#   ProjectileSystem      manajer proyektil
#   ImpactFX              flash + shockwave + serpihan + fragmen + debris
#   SkillFX               lifecycle FX skill (cast->charge->release->fade)
#   ApparitionFXDirector  satu instance per unit, mengikat semua di atas
#   draw_ice_shard        renderer shard bersama (dipakai _entity.py)
#   draw_debug_overlay    hitbox/hurtbox/state/frame/FPS/particle/timer
#   API modul             tick / reset_all / notify_* / draw_*_layer
# ============================================================================

import math
import random

import pygame

try:                        # bus game-feel bersama (zephyr/gornak/vex/...)
    from heroes import combat_feel as _feel
except Exception:           # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual ANCIENT APPARITION: hitbox, hurtbox, jangkauan serang, tabrakan
#: proyektil, state animasi, frame, FPS, jumlah partikel, state skill, timer.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
APPARITION_FX_ENABLED = True

#: Hit-stop global lewat bus combat_feel (dibaca Game.update).
HIT_STOP_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti bocor FPS).
MAX_PARTICLES = 170

#: Batas keras proyektil visual per director.
MAX_PROJECTILES = 16

#: Panjang histori trail cakar (jumlah sampel posisi).
TRAIL_SAMPLES = 12

#: Batas dampak & FX skill aktif per director (yang tertua dibuang).
MAX_IMPACTS = 8
MAX_SKILLS = 4

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Kecepatan proyektil visual (px/detik, ruang layar).
SHARD_SPEED = 560.0     # basic attack (Cold Touch kecil)
BOLT_SPEED = 300.0      # E - Ice Blast (berat, lambat)

#: Umur FX skill dalam DETIK — sinkron dengan jendela gameplay:
#: q = vortex_active_timer 180 langkah (3.0 s), w = 45 langkah (0.75 s),
#: e = 50 langkah (0.83 s) + ledakan, r = 90 langkah (1.5 s) + afterglow.
SKILL_TOTAL = {"q": 3.9, "w": 0.95, "e": 1.75, "r": 2.6}

#: Titik-titik fase ayunan (0..1 dari progress serangan) — MIRROR dari
#: bosses/level3.py :: _NS_ancient_apparition.ATK_PHASES.  Kedua sisi harus
#: tetap sama supaya trail layar menempel pada cakar yang digambar canvas.
ATK_PHASES = {
    "anticipation": (0.00, 0.20),
    "windup":       (0.20, 0.38),
    "swing":        (0.38, 0.55),
    "follow":       (0.55, 0.75),
    "recovery":     (0.75, 1.00),
}
SWING_START = 0.38
SWING_END = 0.62
ATTACK_IMPACT_POINT = 0.50

#: Prioritas state animasi (angka besar menang saat berebut).
ANIM_PRIORITY = {
    "DEATH": 100, "HURT": 90, "HIT": 80, "SPECIAL": 70, "SKILL": 60,
    "CAST": 50, "SWING": 45, "CHARGE": 40, "ATTACK": 30,
    "RUN": 20, "WALK": 10, "IDLE": 0,
}


def attack_phase(progress):
    """Nama fase serangan dari progress 0..1 (lihat ATK_PHASES)."""
    p = 0.0 if progress <= 0.0 else (1.0 if progress >= 1.0 else progress)
    for name in ("anticipation", "windup", "swing", "follow", "recovery"):
        lo, hi = ATK_PHASES[name]
        if p < hi:
            return name
    return "recovery"


def _ease_out(t):
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return 1.0 - (1.0 - t) * (1.0 - t)


def _ease_in(t):
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return t * t


def _ease_in_out(t):
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    if t < 0.5:
        return 2.0 * t * t
    return 1.0 - 2.0 * (1.0 - t) * (1.0 - t)


# ============================================================================
# 1.  PALETTE KARAKTER
# ============================================================================
# Kontrak 9 kunci (outline/shadow/dark/body/mid/light/highlight/weapon/fx)
# + ramp es yang dipakai bersama renderer.  Renderer adalah sumber kebenaran
# material: _sync_palette() menimpa nilai di bawah dari _NS_ancient_apparition
# saat modul itu tersedia, jadi FX & badan tidak pernah melenceng warna.

AA_PALETTE = {
    # ── kontrak inti ──
    "outline":    (6, 10, 20),
    "shadow":     (2, 5, 12),
    "dark":       (18, 38, 78),
    "body":       (30, 62, 112),
    "mid":        (55, 110, 180),
    "light":      (110, 170, 225),
    "highlight":  (185, 225, 250),
    "weapon":     (140, 205, 240),
    "fx":         (150, 225, 255),

    # ── ramp es (dipakai shard / spike / kristal) ──
    "ice_darkest": (8, 20, 55),
    "ice_dark":    (22, 55, 115),
    "ice_mid":     (55, 110, 180),
    "ice_light":   (115, 175, 230),
    "ice_bright":  (170, 215, 250),
    "ice_hot":     (220, 240, 255),
    "ice_pure":    (245, 252, 255),

    # ── aksen ──
    "face_hot":   (200, 245, 255),
    "frost_mid":  (95, 165, 220),
    "frost_light": (170, 220, 250),
    "white":      (255, 255, 255),
}

_PALETTE_SYNC = {
    "outline": "outline", "shadow": "shadow_deep", "dark": "ice_darkest",
    "body": "ice_dark", "mid": "ice_mid", "light": "ice_light",
    "highlight": "ice_bright", "weapon": "ice_bright", "fx": "face_hot",
    "ice_darkest": "ice_darkest", "ice_dark": "ice_dark",
    "ice_mid": "ice_mid", "ice_light": "ice_light",
    "ice_bright": "ice_bright", "ice_hot": "ice_hot",
    "ice_pure": "ice_pure", "face_hot": "face_hot",
    "frost_mid": "frost_mid", "frost_light": "frost_light",
}

_RENDERER = None
_PALETTE_SYNCED = False


def _renderer():
    """Ambil namespace renderer Ancient Apparition (lazy, sekali)."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level3 import _NS_ancient_apparition as G
            _RENDERER = G
        except Exception:                  # pragma: no cover - tool minimal
            _RENDERER = False
    return _RENDERER or None


def _sync_palette():
    """Samakan warna dengan renderer (sumber kebenaran material)."""
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
            AA_PALETTE[dst] = tuple(int(c) for c in col[:3])


def P(key):
    """Akses palette yang selalu sinkron."""
    _sync_palette()
    return AA_PALETTE.get(key, AA_PALETTE["fx"])


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
    """Faktor jumlah partikel (0.0 = partikel dimatikan)."""
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
    Q = _quality()
    return True if Q is None else bool(getattr(Q, "screen_shake", True))


# ============================================================================
# 3.  CACHE SURFACE PROSEDURAL
# ============================================================================
# Semua bentuk kecil (glow, shard, kristal salju, ring, spike, chevron,
# retakan) dibangun SEKALI per parameter lalu di-cache.  Rotasi dikuantisasi
# 16 arah supaya transform.rotate tidak jalan tiap frame.

_SURF_CACHE = {}
_SURF_CACHE_MAX = 260
_ROT_CACHE = {}
_ROT_CACHE_MAX = 160
_ADD = pygame.BLEND_RGB_ADD


def _cache_put(key, surf):
    if len(_SURF_CACHE) >= _SURF_CACHE_MAX:
        for k in list(_SURF_CACHE)[:40]:
            _SURF_CACHE.pop(k, None)
    _SURF_CACHE[key] = surf


def _clamp_color(color):
    return tuple(max(0, min(255, int(c))) for c in color[:3])


def _mix(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def _hash01(seed):
    """Deterministik 0..1 dari seed integer (angka stabil antar-frame)."""
    seed &= 0xFFFFFFFF
    seed = (seed * 2654435761) & 0xFFFFFFFF
    seed ^= seed >> 13
    seed = (seed * 1274126177) & 0xFFFFFFFF
    return ((seed ^ (seed >> 16)) & 0xFFFF) / 65535.0


def _range_val(v):
    """Skalar, atau rentang (a, b) -> nilai acak seragam di dalamnya.

    Dipakai parameter partikel seperti ``rotation_speed=(-6, 6)`` supaya
    pemanggil tidak perlu meng-acak manual di tiap spawn.
    """
    if isinstance(v, (tuple, list)):
        if len(v) == 0:
            return 0.0
        if len(v) == 1:
            return float(v[0])
        return random.uniform(float(v[0]), float(v[1]))
    return float(v)


def glow_surface(radius, color, power=1.0):
    """Halo radial halus PREMULTIPLIED — dibangun sekali, di-cache.

    ``BLEND_RGB_ADD`` MENGABAIKAN kanal alpha, jadi gradien yang hanya
    menurun di alpha berubah jadi CAKRAM warna solid saat di-blit
    additive — penyebab bola cahaya menutupi dada Ancient Apparition saat
    skill di-charge. Intensitas dikalikan ke RGB **dan** disalin ke alpha.
    """
    key = ("glow", int(radius), _clamp_color(color), round(power, 2))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    r = max(1, int(radius))
    size = r * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cr, cg, cb = _clamp_color(color)
    steps = max(3, r // 2)
    for i in range(steps):
        t = i / max(1, steps - 1)
        rr = int(r * (1.0 - t))
        k = 0.59 * power * (1.0 - t) ** 1.6
        if k <= 0.008:
            continue
        pygame.draw.circle(surf,
                           (int(cr * k), int(cg * k), int(cb * k),
                            min(255, int(255 * k))),
                           (r + 1, r + 1), max(0, rr))
    _cache_put(key, surf)
    return surf


def shard_surface(length, width, palette=None, alpha=255):
    """Shard es bersegi: outline -> gelap -> mid -> bright -> garis spekular.

    Arah +x.  BUKAN lingkaran: bentuk pentagon runcing dengan faset
    bertingkat khas pixel art es.
    """
    palette = palette or (P("ice_darkest"), P("ice_dark"), P("ice_mid"),
                          P("ice_light"), P("ice_bright"))
    key = ("shard", int(length), int(width), tuple(map(tuple, palette)),
           int(alpha))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    L = max(3, int(length))
    W = max(1, int(width))
    w, h = L + 4, W * 2 + 4
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = 2, h // 2
    pts = [(cx, cy - W), (cx + L, cy), (cx, cy + W), (cx - L // 3, cy)]
    pygame.draw.polygon(surf, (*P("shadow"), alpha),
                        [(x + 1, y + 1) for x, y in pts])
    for i, col in enumerate(palette):
        k = i * 0.16
        inner = [(cx + (x - cx) * (1 - k) - (0 if x > cx else k * 2),
                  cy + (y - cy) * (1 - k)) for x, y in pts]
        pygame.draw.polygon(surf, (*col, alpha), inner)
    pygame.draw.line(surf, (*P("ice_hot"), alpha),
                     (cx + L // 3, cy - 1), (cx + L - 2, cy), 1)
    pygame.draw.line(surf, (*P("ice_pure"), alpha),
                     (cx + L // 2, cy), (cx + L - 3, cy), 1)
    _cache_put(key, surf)
    return surf


def snowflake_surface(size, color=None, alpha=255):
    """Kristal salju 6 lengan dengan cabang — identitas Ancient Apparition."""
    color = color or P("ice_hot")
    key = ("snow", int(size), _clamp_color(color), int(alpha))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    s = max(3, int(size))
    dim = s * 2 + 3
    surf = pygame.Surface((dim, dim), pygame.SRCALPHA)
    c = dim // 2
    col = (*_clamp_color(color), alpha)
    dimc = (*_mix(color, (0, 0, 0), 0.45), alpha)
    for i in range(6):
        ang = i * math.pi / 3.0
        ex = c + int(math.cos(ang) * s)
        ey = c + int(math.sin(ang) * s)
        pygame.draw.line(surf, col, (c, c), (ex, ey), 1)
        for tb in (0.6, -0.6):
            bx = c + int(math.cos(ang) * s * 0.62)
            by = c + int(math.sin(ang) * s * 0.62)
            tx = bx + int(math.cos(ang + tb) * max(1, s // 2))
            ty = by + int(math.sin(ang + tb) * max(1, s // 2))
            pygame.draw.line(surf, dimc, (bx, by), (tx, ty), 1)
    pygame.draw.circle(surf, (*P("ice_pure"), alpha), (c, c), 1)
    _cache_put(key, surf)
    return surf


def ring_surface(radius, thickness, color, alpha=255):
    """Ring shockwave 1-warna (lingkaran — hanya untuk gelombang tekan)."""
    key = ("ring", int(radius), int(thickness), _clamp_color(color),
           int(alpha))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    r = max(2, int(radius))
    size = (r + thickness + 2) * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, (*_clamp_color(color), int(alpha)),
                       (size // 2, size // 2), r, max(1, int(thickness)))
    _cache_put(key, surf)
    return surf


def ellipse_ring_surface(rx, ry, thickness, color, alpha=255):
    """Ring elips (proyeksi shockwave ke tanah — perspektif arena top-down)."""
    key = ("ering", int(rx), int(ry), int(thickness), _clamp_color(color),
           int(alpha))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    rx = max(2, int(rx))
    ry = max(2, int(ry))
    w = (rx + thickness + 2) * 2
    h = (ry + thickness + 2) * 2
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (*_clamp_color(color), int(alpha)),
                        (thickness + 1, thickness + 1, rx * 2, ry * 2),
                        max(1, int(thickness)))
    _cache_put(key, surf)
    return surf


def spike_surface(bw, bh, alpha=255):
    """Paku es vertikal (erupsi R): dasar lebar, ujung runcing, faset es."""
    key = ("spike", int(bw), int(bh), int(alpha))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    bw = max(2, int(bw))
    bh = max(4, int(bh))
    w, h = bw * 2 + 4, bh + 4
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    base = h - 2
    cx = w // 2
    pts = [(cx - bw, base), (cx + bw, base), (cx, base - bh)]
    pygame.draw.polygon(surf, (*P("shadow"), int(alpha * 0.8)),
                        [(x + 1, y + 1) for x, y in pts])
    for i, name in enumerate(("ice_darkest", "ice_dark", "ice_mid",
                              "ice_light")):
        k = i * 0.15
        inner = [(cx - bw * (1 - k), base - i),
                 (cx + bw * (1 - k), base - i),
                 (cx, base - bh + int(bh * k * 0.4))]
        pygame.draw.polygon(surf, (*P(name), int(alpha)), inner)
    pygame.draw.line(surf, (*P("ice_hot"), int(alpha)),
                     (cx, base - 2), (cx, base - bh + 3), 1)
    pygame.draw.circle(surf, (*P("ice_pure"), int(alpha)), (cx, base - bh + 2), 1)
    _cache_put(key, surf)
    return surf


def chevron_surface(size, color, thick=2):
    """Chevron kecepatan (penunjuk arah) — dipakai telegraph W."""
    key = ("chev", int(size), _clamp_color(color), int(thick))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    s = max(4, int(size))
    surf = pygame.Surface((s + 4, s + 4), pygame.SRCALPHA)
    c = s // 2 + 2
    col = (*_clamp_color(color), 230)
    pygame.draw.line(surf, col, (2, 2), (c, c), thick)
    pygame.draw.line(surf, col, (c, c), (2, s + 2), thick)
    _cache_put(key, surf)
    return surf


def crack_surface(seed, length, color):
    """Retakan tanah bergerigi (setelah ledakan E / erupsi R)."""
    key = ("crack", int(seed), int(length), _clamp_color(color))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf
    L = max(10, int(length))
    w, h = L * 2 + 6, 14
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    col = (*_clamp_color(color), 210)
    dim = (*_mix(color, (0, 0, 0), 0.5), 210)
    x = 3
    y = h // 2
    steps = max(4, L // 4)
    for i in range(steps):
        nx = x + L // steps + int(_hash01(seed + i * 7) * 3)
        ny = h // 2 + int((_hash01(seed + i * 13) - 0.5) * 7)
        pygame.draw.line(surf, col, (x, y), (nx, ny), 1)
        if _hash01(seed + i * 31) > 0.55 and i < steps - 1:
            bx, by = nx, ny
            bnx = bx + int(_hash01(seed + i * 3) * 6) + 2
            bny = by + int((_hash01(seed + i * 5) - 0.5) * 8)
            pygame.draw.line(surf, dim, (bx, by), (bnx, bny), 1)
        x, y = nx, ny
    _cache_put(key, surf)
    return surf


def rotated_cached(key, surf, deg):
    """Rotasi dikuantisasi 16 arah (22.5 derajad) — murah, tetap mulus."""
    q = int(round(deg / 22.5)) * 22.5
    rk = (key, round(q, 1))
    got = _ROT_CACHE.get(rk)
    if got is not None:
        return got
    if len(_ROT_CACHE) >= _ROT_CACHE_MAX:
        for k in list(_ROT_CACHE)[:40]:
            _ROT_CACHE.pop(k, None)
    got = pygame.transform.rotate(surf, -q)
    _ROT_CACHE[rk] = got
    return got


def clear_cache():
    """Kosongkan seluruh cache surface (ganti tema / reset match)."""
    _SURF_CACHE.clear()
    _ROT_CACHE.clear()


def _blit_faded(surface, surf, cx, cy, alpha=255, additive=False):
    """Blit surface dengan alpha dinamis tanpa merusak cache aslinya."""
    if alpha <= 2:
        return
    alpha = min(255, int(alpha))
    if alpha >= 255 and not additive:
        surface.blit(surf, (int(cx - surf.get_width() / 2),
                            int(cy - surf.get_height() / 2)))
        return
    if additive:
        if getattr(surf, "_aa_add", 0) != alpha:
            surf.set_alpha(alpha)
            try:
                surf._aa_add = alpha
            except Exception:              # pragma: no cover
                pass
        surface.blit(surf, (int(cx - surf.get_width() / 2),
                            int(cy - surf.get_height() / 2)),
                     special_flags=_ADD)
    else:
        if getattr(surf, "_aa_alpha", 0) != alpha:
            surf.set_alpha(alpha)
            try:
                surf._aa_alpha = alpha
            except Exception:              # pragma: no cover
                pass
        surface.blit(surf, (int(cx - surf.get_width() / 2),
                            int(cy - surf.get_height() / 2)))


# ═════════════════════════════════════════════════════════════════════
# GAMBAR ALPHA-SAFE KE LAYAR XRGB
#
# Buffer render game dibuat TANPA kanal alpha (XRGB8888 — jalur cepat
# SDL, lihat mobile/platform_utils.py).  Di permukaan begitu,
# pygame.draw dengan warna RGBA mengabaikan alpha (jadi SOLID).
# Semua bentuk transparan modul ini melewati helper bawah: kalau target
# punya per-pixel alpha -> gambar langsung; kalau tidak -> render ke
# scratch SRCALPHA lalu blit (blend benar, alokasi dipakai ulang).
# ═════════════════════════════════════════════════════════════════════

_SCRATCH = {}
_SCRATCH_MAX = 28


def _scratch(w, h):
    """Surface SRCALPHA berukuran (w, h) dari pool (hemat alokasi)."""
    key = (int(w), int(h))
    s = _SCRATCH.get(key)
    if s is None:
        if len(_SCRATCH) >= _SCRATCH_MAX:
            for k in list(_SCRATCH)[:8]:
                _SCRATCH.pop(k, None)
        s = pygame.Surface(key, pygame.SRCALPHA)
        _SCRATCH[key] = s
    return s


def _px_alpha_target(surface):
    """True kalau target mendukung per-pixel alpha (gambar langsung)."""
    return bool(surface.get_flags() & pygame.SRCALPHA)


def _poly_a(surface, color, pts):
    """Polygon RGBA yang benar baik di SRCALPHA maupun layar XRGB."""
    if len(pts) < 3:
        return
    if _px_alpha_target(surface) or len(color) < 4 or color[3] >= 255:
        pygame.draw.polygon(surface, color, pts)
        return
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, y0 = min(xs), min(ys)
    w = int(max(xs) - x0) + 2
    h = int(max(ys) - y0) + 2
    if w <= 0 or h <= 0 or w > 1200 or h > 800:
        return
    tmp = _scratch(w, h)
    tmp.fill((0, 0, 0, 0))
    pygame.draw.polygon(tmp, color,
                        [(p[0] - x0 + 1, p[1] - y0 + 1) for p in pts])
    surface.blit(tmp, (int(x0) - 1, int(y0) - 1))


def _line_a(surface, color, start, end, width=1):
    """Garis RGBA yang benar baik di SRCALPHA maupun layar XRGB."""
    if _px_alpha_target(surface) or len(color) < 4 or color[3] >= 255:
        pygame.draw.line(surface, color, start, end, max(1, width))
        return
    sx, sy = int(start[0]), int(start[1])
    ex, ey = int(end[0]), int(end[1])
    pad = max(1, int(width)) + 2
    w = abs(ex - sx) + pad * 2
    h = abs(ey - sy) + pad * 2
    if w <= 0 or h <= 0 or w > 1200 or h > 800:
        return
    ox = pad - min(sx, ex)
    oy = pad - min(sy, ey)
    tmp = _scratch(w, h)
    tmp.fill((0, 0, 0, 0))
    pygame.draw.line(tmp, color, (sx + ox, sy + oy), (ex + ox, ey + oy),
                     max(1, width))
    surface.blit(tmp, (min(sx, ex) - pad, min(sy, ey) - pad))


def _circle_a(surface, color, center, radius, width=0):
    """Lingkaran RGBA yang benar baik di SRCALPHA maupun layar XRGB."""
    if _px_alpha_target(surface) or len(color) < 4 or color[3] >= 255:
        pygame.draw.circle(surface, color, (int(center[0]), int(center[1])),
                           max(0, int(radius)), max(0, int(width)))
        return
    r = max(1, int(radius))
    d = (r + max(1, int(width))) * 2 + 2
    tmp = _scratch(d, d)
    tmp.fill((0, 0, 0, 0))
    pygame.draw.circle(tmp, color, (d // 2, d // 2), r, max(1, int(width)))
    surface.blit(tmp, (int(center[0]) - d // 2, int(center[1]) - d // 2))


# ============================================================================
# 4.  PARTICLE SYSTEM  (reusable)
# ============================================================================

class Particle:
    """Satu partikel dengan seluruh atribut fisika yang dibutuhkan.

    position, velocity, acceleration, life, max_life, size, rotation,
    rotation_speed, alpha, gravity, color, drag, shrink, shape, layer.
    """

    __slots__ = ("x", "y", "vx", "vy", "ax", "ay", "life", "max_life",
                 "size", "rot", "rot_spd", "alpha", "gravity", "color",
                 "drag", "shrink", "shape", "back", "add", "seed")

    def __init__(self):
        self.reset()

    def reset(self):
        self.x = self.y = 0.0
        self.vx = self.vy = 0.0
        self.ax = self.ay = 0.0
        self.life = self.max_life = 0.0
        self.size = 1.0
        self.rot = 0.0
        self.rot_spd = 0.0
        self.alpha = 255
        self.gravity = 0.0
        self.color = P("fx")
        self.drag = 0.0
        self.shrink = 1.0
        self.shape = "pixel"
        self.back = False
        self.add = False
        self.seed = 0

    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = self.max_life = max(0.016, float(life))
        self.size = max(1.0, float(size))
        self.color = _clamp_color(color)
        self.alpha = float(kw.get("alpha", 255))
        self.ax = float(kw.get("ax", 0.0))
        self.ay = float(kw.get("ay", 0.0))
        self.gravity = _range_val(kw.get("gravity", 0.0))
        self.rot = _range_val(kw.get("rotation", 0.0))
        self.rot_spd = _range_val(kw.get("rotation_speed", 0.0))
        self.drag = _range_val(kw.get("drag", 0.0))
        self.shrink = _range_val(kw.get("shrink", 1.0))
        self.shape = kw.get("shape", "pixel")
        self.back = bool(kw.get("back", False))
        self.add = bool(kw.get("add", False))
        self.seed = int(kw.get("seed", random.randrange(65536)))

    @property
    def alive(self):
        return self.life > 0.0

    def update(self, dt):
        """Maju satu delta-time.  Return False kalau partikel mati."""
        if self.life <= 0.0:
            return False
        self.life -= dt
        if self.life <= 0.0:
            self.life = 0.0
            return False
        if self.drag > 0.0:
            f = max(0.0, 1.0 - self.drag * dt)
            self.vx *= f
            self.vy *= f
        self.vx += (self.ax + 0.0) * dt
        self.vy += (self.ay + self.gravity) * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.rot_spd:
            self.rot += self.rot_spd * dt
        return True

    def draw(self, surface):
        """Gambar partikel sesuai bentuknya (bukan semua lingkaran!)."""
        t = self.life / self.max_life
        alpha = self.alpha * (t if self.shape != "smoke"
                              else min(1.0, t * 1.8)) 
        if alpha <= 3:
            return
        size = max(1.0, self.size * (1.0 + (self.shrink - 1.0) * (1.0 - t)))
        s = int(round(size))
        x, y = int(self.x), int(self.y)
        col = self.color
        if self.add:
            col = _mix(col, P("ice_pure"), 0.25)

        if self.shape == "pixel":
            if s <= 1:
                if self.add:
                    _add_pixel(surface, x, y, col, alpha)
                else:
                    _set_pixel_alpha(surface, x, y, col, alpha)
                return
            if self.add:
                _add_pixel_rect(surface, x - s // 2, y - s // 2, s, col, alpha)
            else:
                _set_pixel_rect(surface, x - s // 2, y - s // 2, s, col, alpha)
            return

        if self.shape == "shard":
            surf = shard_surface(int(9 * size), max(1, int(2 * size)))
            img = rotated_cached(("pshard", int(size)), surf,
                                 math.degrees(self.rot))
            _blit_faded(surface, img, x, y, alpha, additive=self.add)
            return

        if self.shape == "snow":
            surf = snowflake_surface(max(2, int(size)))
            img = rotated_cached(("psnow", int(size)), surf,
                                 math.degrees(self.rot))
            _blit_faded(surface, img, x, y, alpha, additive=self.add)
            return

        if self.shape == "spark":
            dx = math.cos(self.rot)
            dy = math.sin(self.rot)
            ln = max(2, int(3 * size * t + 2))
            c = (*_mix(col, P("ice_pure"), 0.4), int(alpha))
            _line_a(surface, c,
                    (x - int(dx * ln), y - int(dy * ln)),
                    (x + int(dx * ln), y + int(dy * ln)), 1)
            return

        if self.shape == "smoke":
            r = max(2, int(size * (2.0 - t)))
            g = glow_surface(r, _mix(col, (10, 16, 30), 0.55), 0.35)
            _blit_faded(surface, g, x, y, alpha * 0.55)
            return

        if self.shape == "mist":
            r = max(3, int(size * (1.6 - t * 0.5)))
            g = glow_surface(r, col, 0.28)
            _blit_faded(surface, g, x, y, alpha * 0.5)
            return

        if self.shape == "star":
            s2 = max(2, int(size))
            c = (*col, int(alpha))
            _line_a(surface, c, (x - s2, y), (x + s2, y), 1)
            _line_a(surface, c, (x, y - s2), (x, y + s2), 1)
            _circle_a(surface, (*P("ice_pure"), int(alpha)), (x, y), 1)
            return

        # fallback: kotak pixel
        _set_pixel_rect(surface, x - s // 2, y - s // 2, s, col, alpha)


def _set_pixel_alpha(surface, x, y, color, alpha):
    """Tulis satu piksel dengan alpha (tanpa alokasi surface)."""
    if alpha > 235:
        try:
            surface.set_at((x, y), color)
        except Exception:                  # di luar klip / format beda
            pass
        return
    try:
        r, g, b, a = surface.get_at((x, y))
        t = alpha / 255.0
        surface.set_at((x, y),
                       (int(r * (1 - t) + color[0] * t),
                        int(g * (1 - t) + color[1] * t),
                        int(b * (1 - t) + color[2] * t), 255))
    except Exception:                      # pragma: no cover
        pass


def _set_pixel_rect(surface, x, y, s, color, alpha):
    """Kotak pixel padat dengan alpha (di-mix ke warna dasar es)."""
    if alpha > 235:
        pygame.draw.rect(surface, color, (x, y, s, s))
    else:
        t = alpha / 255.0
        col = _mix((8, 12, 22), color, t)
        pygame.draw.rect(surface, col, (x, y, s, s))


def _add_pixel(surface, x, y, color, alpha):
    """Satu piksel additive tanpa alokasi (set_at + math)."""
    try:
        r, g, b, a = surface.get_at((x, y))
        t = alpha / 255.0
        surface.set_at((x, y),
                       (min(255, int(r + color[0] * t)),
                        min(255, int(g + color[1] * t)),
                        min(255, int(b + color[2] * t)), 255))
    except Exception:                      # pragma: no cover
        pass


def _add_pixel_rect(surface, x, y, s, color, alpha):
    """Kotak pixel terang (aditif) — mix ke putih sesuai alpha."""
    if s <= 0:
        return
    if s == 1:
        _add_pixel(surface, x, y, color, alpha)
        return
    t = alpha / 255.0
    col = _mix((26, 40, 70), _mix(color, P("ice_pure"), 0.2),
               0.55 + 0.45 * t)
    pygame.draw.rect(surface, col, (x, y, s, s))


class ParticleSystem:
    """Pool partikel reusable dengan batas keras (anti bocor FPS)."""

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = int(cap)
        self._pool = [Particle() for _ in range(self.cap)]
        self._active = []

    def _acquire(self):
        if len(self._active) >= self.cap:
            return None
        p = self._pool.pop() if self._pool else Particle()
        self._active.append(p)
        return p

    def count(self):
        return len(self._active)

    def alive(self):
        return len(self._active)

    def clear(self):
        for p in self._active:
            p.reset()
            if len(self._pool) < self.cap:
                self._pool.append(p)
        self._active.clear()

    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        budget = particle_budget()
        if budget <= 0.05:
            return None
        if budget < 1.0 and random.random() > budget:
            return None
        p = self._acquire()
        if p is None:
            return None
        p.spawn(x, y, vx, vy, life, size, color, **kw)
        return p

    def burst(self, x, y, count, speed=(60.0, 220.0), life=(0.25, 0.6),
              size=(1, 3), colors=None, spread=math.tau, direction=0.0,
              **kw):
        """Ledakan partikel ke segala arah (atau kerucut ``direction``)."""
        colors = colors or (P("ice_light"), P("ice_bright"), P("ice_hot"))
        budget = particle_budget()
        n = int(count * budget)
        for i in range(n):
            ang = direction + (random.random() - 0.5) * spread
            spd = random.uniform(*speed)
            self.spawn(x, y,
                       math.cos(ang) * spd, math.sin(ang) * spd,
                       random.uniform(*life), random.randint(*size),
                       random.choice(colors), **kw)

    def stream(self, x, y, tx, ty, count, life=(0.3, 0.6), size=(1, 3),
               colors=None, **kw):
        """Aliran partikel dari (x,y) menuju (tx,ty) — gather/absorb."""
        colors = colors or (P("ice_bright"),)
        budget = particle_budget()
        for i in range(int(count * budget)):
            t = i / max(1, count - 1)
            px = x + (tx - x) * t + random.uniform(-6, 6)
            py = y + (ty - y) * t + random.uniform(-6, 6)
            dx, dy = tx - px, ty - py
            d = max(1.0, math.hypot(dx, dy))
            spd = d / random.uniform(*life)
            self.spawn(px, py, dx / d * spd, dy / d * spd,
                       random.uniform(*life), random.randint(*size),
                       random.choice(colors), shrink=0.4, **kw)

    def ring(self, x, y, radius, count, life=(0.3, 0.7), size=(2, 4),
             colors=None, inward=False, **kw):
        """Cincin partikel melebar (atau menguncup kalau inward)."""
        colors = colors or (P("ice_bright"), P("ice_hot"))
        budget = particle_budget()
        for i in range(int(count * budget)):
            ang = i * math.tau / max(1, count) + random.uniform(-0.1, 0.1)
            px = x + math.cos(ang) * radius
            py = y + math.sin(ang) * radius * 0.55
            spd = random.uniform(40, 110) * (-1.0 if inward else 1.0)
            self.spawn(px, py,
                       math.cos(ang) * spd, math.sin(ang) * spd * 0.55,
                       random.uniform(*life), random.randint(*size),
                       random.choice(colors), drag=1.5, **kw)

    def update(self, dt):
        if not self._active:
            return
        dead = []
        for p in self._active:
            if not p.update(dt):
                dead.append(p)
        if dead:
            for p in dead:
                self._active.remove(p)
                if len(self._pool) < self.cap:
                    p.reset()
                    self._pool.append(p)

    def draw(self, surface, layer=None):
        """layer None = semua; True = back; False = front."""
        for p in self._active:
            if layer is None or bool(p.back) == layer:
                p.draw(surface)


# ============================================================================
# 5.  SLASH TRAIL  (weapon trail dari histori posisi cakar)
# ============================================================================

class SlashTrail:
    """Pita sapuan cakar: simpan histori (base, tip), gambar ribbon polygon.

    Titik lama memudar; ribbon hanya menempati bagian LUAR lengan (cakar +
    sedikit pergelangan) sehingga terbaca sebagai sapuan senjata, bukan
    kabut yang menutupi badan.
    """

    def __init__(self, samples=TRAIL_SAMPLES):
        self.samples = int(samples)
        self.hist = []          # [(bx, by, tx, ty, age)]  terbaru terakhir
        self.age = 0.0
        self.overcharged = False

    def reset(self):
        self.hist.clear()

    def push(self, base, tip):
        self.hist.append((base[0], base[1], tip[0], tip[1], 0.0))
        if len(self.hist) > self.samples:
            self.hist.pop(0)

    def update(self, dt):
        self.age += dt
        for i, h in enumerate(self.hist):
            self.hist[i] = (h[0], h[1], h[2], h[3], h[4] + dt)

    def draw(self, surface, color=None):
        if len(self.hist) < 2:
            return
        color = color or (P("weapon") if not self.overcharged
                          else P("ice_pure"))
        n = len(self.hist)
        # Ribbon luar: dari titik grip ke ujung cakar tiap sampel.
        outer = []
        inner = []
        for i, (bx, by, tx, ty, age) in enumerate(self.hist):
            k = i / max(1, n - 1)                 # 0 lama -> 1 baru
            fade = max(0.0, 1.0 - age * 3.2) * (0.25 + 0.75 * k)
            if fade <= 0.03:
                continue
            # bagian dalam ribbon: 30% dari grip ke tip
            ix = bx + (tx - bx) * 0.30
            iy = by + (ty - by) * 0.30
            outer.append((tx, ty, fade))
            inner.append((ix, iy, fade))
        if len(outer) < 2:
            return
        # Bangun strip polygon per segmen (quad) supaya alpha per segmen
        # bisa berbeda — polygon tunggal tidak mendukung gradasi alpha.
        for i in range(len(outer) - 1):
            x0, y0, f0 = outer[i]
            x1, y1, f1 = outer[i + 1]
            ix0, iy0, _ = inner[i]
            ix1, iy1, _ = inner[i + 1]
            a = int(150 * min(f0, f1))
            if a <= 6:
                continue
            quad = [(ix0, iy0), (ix1, iy1), (x1, y1), (x0, y0)]
            c = (*_mix(color, P("ice_pure"), 0.3), a)
            _poly_a(surface, c, quad)
            # tepi terang tipis mengikuti arah ayunan
            c2 = (*P("ice_pure"), int(a * 0.8))
            _line_a(surface, c2, (x0, y0), (x1, y1), 1)


# ============================================================================
# 6.  PROJECTILE SYSTEM  (modular)
# ============================================================================

class ApparitionProjectile:
    """Proyektil visual Ancient Apparition.

    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY.
    kinds:
      * "shard"  — basic attack: shard kecil cepat, homing ringan
      * "bolt"   — E Ice Blast: bolt besar lambat + shard pengorbit
      * "reaver" — R: tracer es cepat (garis dingin)
    """

    def __init__(self, x, y, tx, ty, kind="shard", speed=None, damage=0,
                 target=None, lifetime=3.0, crit=False):
        self.position = pygame.Vector2(float(x), float(y))
        start_speed = speed if speed is not None else (
            SHARD_SPEED if kind == "shard" else
            (BOLT_SPEED if kind == "bolt" else 900.0))
        dx, dy = float(tx) - float(x), float(ty) - float(y)
        d = max(1.0, math.hypot(dx, dy))
        self.velocity = pygame.Vector2(dx / d * start_speed,
                                       dy / d * start_speed)
        self.speed = float(start_speed)
        self.damage = float(damage)
        self.lifetime = float(lifetime)
        self.age = 0.0
        self.target = target
        self.radius = 5.0 if kind == "shard" else (
            9.0 if kind == "bolt" else 3.0)
        self.hit_radius = self.radius + 2.0
        self.rotation = math.atan2(self.velocity.y, self.velocity.x)
        self.trail = []                       # [(x, y, age)]
        self.particles = True                 # emit partikel sendiri
        self.active = True
        self.kind = kind
        self.crit = crit
        self.tx, self.ty = float(tx), float(ty)
        self.homing = 3.6 if kind == "shard" else (
            1.2 if kind == "bolt" else 0.0)
        self._hit_done = False

    # ------------------------------------------------------------------
    def _steer(self, dt):
        """Target tracking: belok halus menuju target selagi hidup."""
        if self.homing <= 0.0 or self.target is None:
            return
        t = self.target
        tx = float(getattr(t, "x", self.tx))
        ty = float(getattr(t, "y", self.ty))
        want = pygame.Vector2(tx - self.position.x, ty - self.position.y)
        if want.length_squared() <= 1.0:
            return
        want.scale_to_length(self.speed)
        self.velocity = self.velocity.lerp(want, min(1.0, self.homing * dt))

    # ------------------------------------------------------------------
    def update(self, dt, psys=None):
        """SPAWN->TRAVEL->TRAIL->HIT.  Return True kalau impact terjadi."""
        if not self.active:
            return False
        self.age += dt
        if self.age >= self.lifetime:
            self.active = False
            return False

        self._steer(dt)
        if self.velocity.length_squared() > 0.001:
            self.rotation = math.atan2(self.velocity.y, self.velocity.x)

        # TRAIL — histori posisi (dipakai ribbon ekor)
        self.trail.append((self.position.x, self.position.y, 0.0))
        if len(self.trail) > (8 if self.kind == "shard" else 14):
            self.trail.pop(0)
        for i, (tx, ty, ta) in enumerate(self.trail):
            self.trail[i] = (tx, ty, ta + dt)

        # partikel dingin yang mengelupas dari proyektil
        if psys is not None and self.particles and \
                random.random() < (0.55 if self.kind != "shard" else 0.3):
            back = -self.velocity * 0.12
            psys.spawn(self.position.x, self.position.y,
                       back.x + random.uniform(-26, 26),
                       back.y + random.uniform(-26, 26),
                       random.uniform(0.18, 0.42), random.randint(1, 2),
                       random.choice((P("ice_bright"), P("ice_hot"))),
                       shape="pixel", add=True, shrink=0.5)

        self.position += self.velocity * dt

        # HIT — sampai tujuan (titik target tetap) atau menabrak target hidup
        dist = math.hypot(self.tx - self.position.x,
                          self.ty - self.position.y)
        hit_target = False
        if self.target is not None and getattr(self.target, "alive", True):
            tdist = math.hypot(getattr(self.target, "x", self.tx) -
                               self.position.x,
                               getattr(self.target, "y", self.ty) -
                               self.position.y)
            hit_target = tdist <= max(10.0, self.hit_radius + 12.0)
        if dist <= self.speed * dt + 6.0 or hit_target:
            self.position.x, self.position.y = self.tx, self.ty
            self.active = False
            self._hit_done = True
            return True
        return False

    # ------------------------------------------------------------------
    def draw(self, surface):
        """VISUAL: core + glow + bentuk berarah + rotasi + trail.

        Core shard bersegi (bukan lingkaran), halo radial, ekor facet
        memudar, dan Kristal salju kecil untuk bolt.
        """
        px, py = int(self.position.x), int(self.position.y)
        deg = math.degrees(self.rotation)

        # ── ekor: shard memudar mengikuti histori ──
        n = len(self.trail)
        if n >= 2:
            for i in range(n - 1):
                tx0, ty0, a0 = self.trail[i]
                t = i / max(1, n - 1)
                fade = max(0.0, 1.0 - a0 * 4.5) * (0.2 + 0.8 * t)
                if fade <= 0.05:
                    continue
                ln = int(self.radius * (0.6 + t))
                surf = shard_surface(ln, max(1, int(self.radius * 0.35)))
                img = rotated_cached(("ptr", ln, int(self.radius * 0.35)),
                                     surf, deg)
                _blit_faded(surface, img, tx0, ty0, 130 * fade,
                            additive=True)

        # ── halo ──
        if glow_allowed():
            g = glow_surface(int(self.radius * 2.4),
                             P("ice_light") if self.kind != "bolt"
                             else P("ice_mid"), 0.8)
            _blit_faded(surface, g, px, py, 150, additive=True)

        # ── badan berarah ──
        ln = int(self.radius * (2.4 if self.kind != "bolt" else 3.2))
        wd = max(2, int(self.radius * 0.55))
        surf = shard_surface(ln, wd)
        img = rotated_cached(("pbody", ln, wd), surf, deg)
        surface.blit(img, (px - img.get_width() // 2,
                           py - img.get_height() // 2))

        # ── inti panas ──
        hot = glow_surface(max(2, int(self.radius * 0.8)), P("ice_pure"), 1.0)
        _blit_faded(surface, hot, px, py, 220, additive=True)

        # ── pengorbit bolt (E): 3 shard kecil berputar ──
        if self.kind == "bolt":
            for i in range(3):
                ang = self.age * 7.0 + i * math.tau / 3.0
                ox = px + int(math.cos(ang) * (self.radius + 6))
                oy = py + int(math.sin(ang) * (self.radius + 6))
                s2 = shard_surface(7, 2)
                img2 = rotated_cached(("porb", 7, 2), s2,
                                       math.degrees(ang + math.pi / 2))
                _blit_faded(surface, img2, ox, oy, 200, additive=True)
        elif self.crit:
            sp = snowflake_surface(3)
            _blit_faded(surface, sp, px, py, 230, additive=True)


class ProjectileSystem:
    """Manajer proyektil: cap keras, spawn, update, draw."""

    def __init__(self, cap=MAX_PROJECTILES):
        self.cap = int(cap)
        self.items = []

    def count(self):
        return len(self.items)

    def clear(self):
        self.items.clear()

    def spawn(self, x, y, tx, ty, kind="shard", **kw):
        if len(self.items) >= self.cap:
            self.items.pop(0)
        p = ApparitionProjectile(x, y, tx, ty, kind=kind, **kw)
        self.items.append(p)
        return p

    def update(self, dt, psys=None, on_impact=None):
        """Update semua proyektil; panggil on_impact untuk yang mengenai."""
        hits = []
        for p in self.items:
            if p.update(dt, psys):
                hits.append(p)
        if hits and on_impact is not None:
            for p in hits:
                on_impact(p)
        self.items = [p for p in self.items if p.active]
        return hits

    def draw(self, surface):
        for p in self.items:
            p.draw(surface)


# ============================================================================
# 7.  IMPACT SYSTEM
# ============================================================================

class ImpactFX:
    """Paket feedback benturan: flash, spark, shockwave, debris, fragmen.

    kinds:
      * "hit"   — pukulan/shard biasa (ringan)
      * "blast" — ledakan E (berat: spike radial + retakan + nova)
      * "erupt" — erupsi R (cincin paku es + debu)
      * "frost" — freeze tick (kristal kecil)
    """

    LIFE = {"hit": 0.42, "blast": 0.85, "erupt": 0.7, "frost": 0.3}

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False, kind="hit",
                 psys=None):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = max(0.4, float(power))
        self.crit = bool(crit)
        self.kind = kind if kind in self.LIFE else "hit"
        self.life = self.LIFE[self.kind] * (1.0 + 0.15 * (self.power - 1.0))
        self.max_life = self.life
        self.alive = True
        self.seed = random.randrange(4096)

        # ── feedback game-feel SEKALI di spawn ──
        if _feel is not None:
            if self.kind == "blast":
                _feel.hit_stop(0.06)
                if shake_allowed():
                    _feel.shake(7.5 + self.power, 0.34)
            elif self.kind == "erupt":
                _feel.hit_stop(0.07)
                if shake_allowed():
                    _feel.shake(9.0 + self.power, 0.46)
            elif self.kind == "hit":
                _feel.hit_stop(0.038)
                if shake_allowed():
                    _feel.shake(3.2 + self.power * 1.6, 0.2)

        # ── burst partikel awal (arah menyebar dari sudut datang) ──
        if psys is not None:
            if self.kind == "hit":
                psys.burst(self.x, self.y, int(8 * self.power) + 4,
                           speed=(90, 300 * self.power),
                           life=(0.18, 0.45), size=(1, 2),
                           colors=(P("ice_hot"), P("ice_bright"), P("white")),
                           spread=2.4, direction=self.angle,
                           shape="spark", rotation_speed=0, add=True,
                           drag=2.2)
                psys.burst(self.x, self.y, 5, speed=(30, 90),
                           life=(0.3, 0.55), size=(2, 3),
                           colors=(P("ice_light"),), spread=math.tau,
                           shape="snow", rotation_speed=(-6, 6), back=True)
                if self.crit:
                    psys.burst(self.x, self.y, 8, speed=(60, 200),
                               life=(0.25, 0.5), size=(2, 3),
                               colors=(P("white"), P("fx")),
                               spread=math.tau, shape="star", add=True)
            elif self.kind == "blast":
                psys.burst(self.x, self.y, 22, speed=(120, 430),
                           life=(0.3, 0.75), size=(1, 3),
                           colors=(P("ice_hot"), P("ice_bright"), P("white")),
                           spread=math.tau, shape="spark", add=True, drag=1.8)
                psys.burst(self.x, self.y, 14, speed=(70, 260),
                           life=(0.4, 0.8), size=(2, 4),
                           colors=(P("ice_mid"), P("ice_light")),
                           spread=math.tau, shape="shard",
                           rotation_speed=(-9, 9), gravity=240, drag=1.2)
                psys.burst(self.x, self.y, 10, speed=(20, 70),
                           life=(0.6, 1.1), size=(4, 7),
                           colors=(P("frost_mid"),), spread=math.tau,
                           shape="smoke", back=True, gravity=-30)
            elif self.kind == "erupt":
                psys.ring(self.x, self.y, 26.0, 18, life=(0.35, 0.7),
                          size=(2, 4),
                          colors=(P("ice_bright"), P("ice_hot")),
                          shape="shard", rotation_speed=(-7, 7), add=True)
                psys.burst(self.x, self.y, 16, speed=(140, 420),
                           life=(0.3, 0.7), size=(1, 2),
                           colors=(P("white"), P("ice_hot")),
                           spread=math.pi, direction=-math.pi / 2,
                           shape="spark", add=True, gravity=420, drag=0.8)
                psys.burst(self.x, self.y, 10, speed=(15, 60),
                           life=(0.7, 1.2), size=(5, 8),
                           colors=(P("frost_mid"),), spread=math.tau,
                           shape="smoke", back=True, gravity=-24)
            else:  # frost
                psys.burst(self.x, self.y, 6, speed=(20, 90),
                           life=(0.25, 0.5), size=(1, 3),
                           colors=(P("ice_bright"),), spread=math.tau,
                           shape="snow", rotation_speed=(-6, 6))

    # ------------------------------------------------------------------
    def update(self, dt):
        self.life -= dt
        if self.life <= 0.0:
            self.alive = False

    # ------------------------------------------------------------------
    def draw(self, surface):
        t = 1.0 - self.life / self.max_life          # 0 -> 1
        fade = 1.0 - t
        if fade <= 0.02:
            return
        x, y = int(self.x), int(self.y)

        # ── IMPACT FLASH: bintang 4-arah menyala cepat lalu padam ──
        if t < 0.35 and self.kind in ("hit", "blast", "erupt"):
            ft = t / 0.35
            a = int(235 * (1.0 - ft))
            ln = int((16 if self.kind == "hit" else 34) *
                     (1.0 + ft * 1.6) * min(2.0, self.power))
            w = max(2, int(3 * (1.0 - ft) * min(2.0, self.power)))
            c = (*P("ice_pure"), a)
            _line_a(surface, c, (x - ln, y), (x + ln, y), w)
            _line_a(surface, c, (x, y - ln), (x, y + ln), w)
            for da in (0.7853982, -0.7853982, math.pi - 0.7853982,
                       math.pi + 0.7853982):
                x2 = x + int(math.cos(da) * ln * 0.55)
                y2 = y + int(math.sin(da) * ln * 0.55)
                _line_a(surface, (*P("ice_hot"), int(a * 0.8)),
                        (x, y), (x2, y2), max(1, w - 1))

        # ── SHOCKWAVE: ring elips melebar (proyeksi tanah) ──
        if self.kind in ("blast", "erupt", "hit"):
            maxr = (26 if self.kind == "hit" else
                    (58 if self.kind == "blast" else 46)) * \
                min(1.8, self.power)
            r = int(maxr * _ease_out(t))
            ry = max(2, int(r * 0.45))
            a = int(210 * fade)
            er = ellipse_ring_surface(r, ry, 2, P("ice_bright"), a)
            surface.blit(er, (x - er.get_width() // 2,
                              y - er.get_height() // 2))
            if self.kind != "hit":
                r2 = int(r * 0.6)
                er2 = ellipse_ring_surface(r2, max(2, int(r2 * 0.45)), 1,
                                           P("ice_pure"), int(a * 0.7))
                surface.blit(er2, (x - er2.get_width() // 2,
                                   y - er2.get_height() // 2))

        # ── SLASH FRAGMENTS: sabit goresan mengikuti sudut datang ──
        if self.kind == "hit" and t < 0.5:
            st = t / 0.5
            a = int(220 * (1.0 - st))
            arc_r = int(20 * min(2.0, self.power))
            cx0 = x - int(math.cos(self.angle) * arc_r * 0.4)
            cy0 = y - int(math.sin(self.angle) * arc_r * 0.4)
            pts = []
            for i in range(9):
                ang = self.angle - 0.9 + (1.8 * i / 8.0)
                rr = arc_r * (0.55 + 0.45 * math.sin(math.pi * i / 8.0))
                pts.append((cx0 + math.cos(ang) * rr,
                            cy0 + math.sin(ang) * rr))
            if len(pts) >= 3:
                for i in range(len(pts) - 1):
                    _line_a(surface, (*P("ice_hot"), a),
                            (int(pts[i][0]), int(pts[i][1])),
                            (int(pts[i + 1][0]), int(pts[i + 1][1])), 2)
                    _line_a(surface, (*P("ice_pure"), int(a * 0.7)),
                            (int(pts[i][0]) + 1, int(pts[i][1])),
                            (int(pts[i + 1][0]) + 1,
                             int(pts[i + 1][1])), 1)

        # ── BLAST: paku es radial + retakan tanah ──
        if self.kind == "blast":
            grow = min(1.0, t / 0.3)
            shrink = 1.0 - max(0.0, (t - 0.55) / 0.45) * 0.7
            n_spikes = 8
            for i in range(n_spikes):
                ang = i * math.tau / n_spikes + 0.2
                ln = int((22 + (i % 2) * 10) * grow * shrink *
                         min(1.6, self.power))
                sx = x + int(math.cos(ang) * (10 + 8 * grow))
                sy = y + int(math.sin(ang) * (10 + 8 * grow) * 0.55)
                sp = spike_surface(3, max(4, ln))
                sc = int(255 * shrink)
                _blit_faded(surface, sp, sx, sy - ln // 2, sc)
            if t > 0.35:
                ct = (t - 0.35) / 0.65
                for i in range(3):
                    ang = i * 2.1 + self.seed
                    cxp = x + int(math.cos(ang) * 26)
                    cyp = y + int(math.sin(ang) * 12)
                    crk = crack_surface(self.seed + i, int(20 * (1 - ct * 0.3)),
                                        P("ice_mid"))
                    img = rotated_cached(("crk", self.seed + i,
                                          int(20 * (1 - ct * 0.3))),
                                         crk, math.degrees(ang))
                    _blit_faded(surface, img, cxp, cyp, 190 * (1.0 - ct))

        # ── AFTER GLOW ──
        if glow_allowed() and t < 0.6:
            g = glow_surface(int(18 * min(2.0, self.power)) + 6,
                             P("ice_bright"), 0.7)
            _blit_faded(surface, g, x, y, 160 * (1.0 - t / 0.6),
                        additive=True)


# ============================================================================
# 8.  SKILL FX  (lifecycle: CAST -> CHARGE -> RELEASE -> AREA -> FADE)
# ============================================================================

class SkillFX:
    """Satu instance FX skill Q/W/E/R di layar.

    Q ICE VORTEX   : genangan berputar + shard orbit + mist naik + tick ring
    W CHILLING     : tarikan napas -> beam gerigi melebar + gelombang dingin
    E ICE BLAST    : bola bola gather -> bolt besar -> ledakan (via impact)
    R COLD FEET    : lingkar peringatan -> salju menguncup -> erupsi paku es
    """

    def __init__(self, skill, x, y, psys, radius=None, facing=1,
                 angle=0.0, projectiles=None):
        self.skill = skill if skill in ("q", "w", "e", "r") else "q"
        self.x = float(x)
        self.y = float(y)
        self.facing = 1 if facing >= 0 else -1
        self.angle = float(angle)
        self.psys = psys
        self.projectiles = projectiles
        self.radius = float(radius if radius else
                            {"q": 74.0, "w": 190.0, "e": 64.0,
                             "r": 96.0}[self.skill])
        self.t = 0.0
        self.total = SKILL_TOTAL[self.skill]
        self.alive = True
        self.seed = random.randrange(4096)
        self._released = False
        self._tick_count = 0

    # ------------------------------------------------------------------
    @property
    def phase(self):
        """Fase lifecycle: cast -> charge -> release -> area -> fade."""
        t = self.t / self.total
        if self.skill == "q":
            if t < 0.05:
                return "CAST"
            if t < 0.12:
                return "CHARGE"
            if t < 0.16:
                return "RELEASE"
            if t < 0.88:
                return "AREA"
            return "FADE"
        if self.skill == "w":
            if t < 0.22:
                return "CHARGE"
            if t < 0.32:
                return "RELEASE"
            if t < 0.78:
                return "AREA"
            return "FADE"
        if self.skill == "e":
            if t < 0.18:
                return "CHARGE"
            if t < 0.26:
                return "RELEASE"
            if t < 0.72:
                return "TRAVEL"
            return "FADE"
        # r
        if t < 0.10:
            return "CAST"
        if t < 0.34:
            return "CHARGE"
        if t < 0.42:
            return "RELEASE"
        if t < 0.82:
            return "AREA"
        return "FADE"

    # ------------------------------------------------------------------
    def update(self, dt):
        self.t += dt
        ph = self.phase
        ps = self.psys

        # ── emisi per fase ──
        if ps is not None:
            if self.skill == "q":
                if ph == "CHARGE":
                    ps.ring(self.x, self.y, self.radius, 10,
                            life=(0.25, 0.5), size=(1, 3),
                            colors=(P("ice_bright"),), inward=True,
                            shape="snow", rotation_speed=(-6, 6))
                elif ph == "RELEASE" and not self._released:
                    self._released = True
                    ps.burst(self.x, self.y, 14, speed=(80, 260),
                             life=(0.3, 0.6), size=(2, 4),
                             colors=(P("ice_light"), P("ice_bright")),
                             spread=math.tau, shape="shard",
                             rotation_speed=(-8, 8), gravity=140, drag=1.4)
                    if _feel is not None and shake_allowed():
                        _feel.shake(5.5, 0.3)
                elif ph == "AREA":
                    # salju menghisap ke dalam vortex (spiral dalam)
                    if random.random() < 0.5:
                        ang = random.random() * math.tau
                        rr = self.radius * random.uniform(0.7, 1.15)
                        sx = self.x + math.cos(ang) * rr
                        sy = self.y + math.sin(ang) * rr * 0.55
                        ps.spawn(sx, sy,
                                 (self.x - sx) * 1.6,
                                 (self.y - sy) * 1.6 - 30,
                                 random.uniform(0.4, 0.8), 2,
                                 random.choice((P("ice_bright"), P("frost_light"))),
                                 shape="snow", rotation_speed=(-7, 7),
                                 drag=0.6, add=True)
                    # mist naik dari genangan
                    if random.random() < 0.35:
                        ps.spawn(self.x + random.uniform(-self.radius * 0.8,
                                                         self.radius * 0.8),
                                 self.y + random.uniform(-8, 8),
                                 random.uniform(-8, 8), -random.uniform(24, 60),
                                 random.uniform(0.5, 0.9), random.randint(3, 6),
                                 P("frost_mid"), shape="mist", back=True)
                    # tick ring tiap 1/3 detik (mengikuti damage tick DOT)
                    self._tick_count += dt
                    if self._tick_count >= 0.333:
                        self._tick_count = 0.0
                        ps.ring(self.x, self.y, self.radius * 0.5, 8,
                                life=(0.2, 0.4), size=(1, 2),
                                colors=(P("ice_hot"),), shape="pixel",
                                add=True)
            elif self.skill == "w":
                if ph == "CHARGE" and random.random() < 0.6:
                    ps.spawn(self.x + random.uniform(-16, 16),
                             self.y + random.uniform(-14, 6),
                             random.uniform(-20, 20) + 30 * self.facing,
                             random.uniform(-24, 8),
                             random.uniform(0.2, 0.45), 2,
                             random.choice((P("ice_bright"), P("frost_light"))),
                             shape="snow", rotation_speed=(-6, 6), add=True)
                elif ph == "RELEASE" and not self._released:
                    self._released = True
                    if _feel is not None:
                        _feel.hit_stop(0.04)
                        if shake_allowed():
                            _feel.shake(4.0, 0.24)
            elif self.skill == "e":
                if ph == "CHARGE":
                    ps.stream(self.x + random.uniform(-70, 70),
                              self.y + random.uniform(-50, 30),
                              self.x, self.y, 2,
                              life=(0.2, 0.4), size=(1, 2),
                              colors=(P("ice_bright"), P("ice_hot")))
                elif ph == "RELEASE" and not self._released:
                    self._released = True
                    # bolt besar dilepas ke arah angle (target diserahkan
                    # lewat projectiles manager)
                    if self.projectiles is not None:
                        dist = 240.0
                        self.projectiles.spawn(
                            self.x, self.y,
                            self.x + math.cos(self.angle) * dist,
                            self.y + math.sin(self.angle) * dist,
                            kind="bolt", lifetime=1.1)
                    ps.burst(self.x, self.y, 10, speed=(60, 220),
                             life=(0.2, 0.5), size=(1, 3),
                             colors=(P("ice_hot"), P("white")),
                             spread=math.tau, shape="spark", add=True)
            elif self.skill == "r":
                if ph == "CHARGE":
                    ps.ring(self.x, self.y, self.radius * 1.2, 8,
                            life=(0.35, 0.6), size=(2, 3),
                            colors=(P("frost_light"), P("ice_bright")),
                            inward=True, shape="snow",
                            rotation_speed=(-6, 6))
                elif ph == "RELEASE" and not self._released:
                    self._released = True
                    if _feel is not None:
                        _feel.hit_stop(0.07)
                        if shake_allowed():
                            _feel.shake(9.0, 0.5)
                    ps.ring(self.x, self.y, 30.0, 20, life=(0.3, 0.6),
                            size=(2, 4),
                            colors=(P("ice_bright"), P("ice_hot")),
                            shape="shard", rotation_speed=(-8, 8), add=True)

        if self.t >= self.total:
            self.alive = False

    # ------------------------------------------------------------------
    def draw(self, surface):
        t = self.t / self.total
        ph = self.phase
        x, y = int(self.x), int(self.y)

        if self.skill == "q":
            self._draw_vortex(surface, x, y, t, ph)
        elif self.skill == "w":
            self._draw_beam(surface, x, y, t, ph)
        elif self.skill == "e":
            self._draw_blast_charge(surface, x, y, t, ph)
        elif self.skill == "r":
            self._draw_cold_feet(surface, x, y, t, ph)

    # ------------------------------------------------------------------
    def _draw_vortex(self, surface, x, y, t, ph):
        """Q — vortex: genangan elips + 6 shard orbit + pilar putar."""
        fade = 1.0 if ph != "FADE" else max(0.0, 1.0 - (t - 0.88) / 0.12)
        if fade <= 0.02:
            return
        grow = _ease_out(min(1.0, t / 0.16)) if ph != "CAST" else 0.0
        R = self.radius * grow
        if R <= 1:
            return
        spin = self.t * 3.4

        # genangan dasar (ground pool) — 3 elips
        for i, (rr, col, a) in enumerate((
                (R, P("ice_dark"), 120),
                (R * 0.72, P("ice_mid"), 140),
                (R * 0.45, P("ice_light"), 150))):
            er = ellipse_ring_surface(int(rr), max(2, int(rr * 0.42)), 2,
                                      col, int(a * fade))
            surface.blit(er, (x - er.get_width() // 2,
                              y - er.get_height() // 2))
        # gerigi genangan (bukan lingkaran mulus)
        for i in range(10):
            ang = spin * 0.4 + i * math.tau / 10
            r0, r1 = R * 0.95, R * 1.18
            _line_a(
                surface, (*P("ice_bright"), int(140 * fade)),
                (x + int(math.cos(ang) * r0),
                 y + int(math.sin(ang) * r0 * 0.42)),
                (x + int(math.cos(ang) * r1),
                 y + int(math.sin(ang) * r1 * 0.42)), 1)

        # shard orbit naik (tornado): 6 shard pada 3 ketinggian
        for lvl in range(3):
            h_ratio = lvl / 3.0
            yy = y - int((1.0 - h_ratio) * 46 * grow)
            rr = R * (0.32 + h_ratio * 0.5)
            for i in range(6):
                ang = spin * (1.0 + h_ratio * 0.8) + i * math.tau / 6
                sx = x + int(math.cos(ang) * rr)
                sy = yy + int(math.sin(ang) * rr * 0.3)
                ln = int(9 + (i % 2) * 4)
                sp = shard_surface(ln, 2)
                img = rotated_cached(("vort", ln, 2), sp,
                                     math.degrees(ang + math.pi / 2 + spin))
                _blit_faded(surface, img, sx, sy,
                            int((190 - lvl * 30) * fade), additive=True)

        # inti pusaran
        core = glow_surface(int(10 + 6 * grow), P("ice_pure"), 0.9)
        _blit_faded(surface, core, x, y - int(20 * grow),
                    int(200 * fade), additive=True)
        sf = snowflake_surface(5)
        img = rotated_cached(("vsnow", 5), sf, math.degrees(spin * 2))
        _blit_faded(surface, img, x, y - int(20 * grow),
                    int(230 * fade), additive=True)

    # ------------------------------------------------------------------
    def _draw_beam(self, surface, x, y, t, ph):
        """W — Chilling Touch: beam es gerigi dari tangan ke arah angle."""
        if ph == "CHARGE":
            a = int(200 * min(1.0, t / 0.22))
            g = glow_surface(14, P("ice_bright"), 0.9)
            _blit_faded(surface, g, x, y, a, additive=True)
            sf = snowflake_surface(4)
            _blit_faded(surface, sf, x, y, a, additive=True)
            # chevron arah: penunjuk telegraph sepanjang arah beam
            dx = math.cos(self.angle)
            dy = math.sin(self.angle)
            ch = chevron_surface(6, P("ice_bright"), 2)
            if self.facing < 0:
                ch = pygame.transform.flip(ch, True, False)
            for i in range(4):
                k = (i + 1) / 5.0 + 0.06 * math.sin(self.t * 9.0)
                cxp = x + dx * 150.0 * k
                cyp = y + dy * 150.0 * k
                _blit_faded(surface, ch, cxp, cyp,
                            int(a * (0.35 + 0.65 * k)))
            return
        tt = (t - 0.22) / 0.78 if ph != "CHARGE" else 0.0
        fade = 1.0 if ph != "FADE" else max(0.0, 1.0 - (t - 0.78) / 0.22)
        if fade <= 0.02:
            return
        reach = min(1.0, tt / 0.10) * (1.0 - 0.25 * max(0.0, tt - 0.8) * 5.0)
        ang = self.angle
        dx, dy = math.cos(ang), math.sin(ang)
        px, py = -dy, dx
        length = int(210 * reach)
        per = 5  # setengah lebar beam

        # ── beam gerigi: segmen quad dengan tepi bergerigi ──
        steps = max(6, length // 7)
        for i in range(steps):
            t0 = i / max(1, steps)
            t1 = (i + 1) / max(1, steps)
            wobble = math.sin(self.t * 22.0 + t0 * 16.0) * 2.2 * reach
            x0 = x + dx * length * t0 + px * wobble
            y0 = y + dy * length * t0 + py * wobble
            x1 = x + dx * length * t1 + px * wobble
            y1 = y + dy * length * t1 + py * wobble
            wid = per * (0.55 + 0.45 * math.sin(math.pi * (0.15 + t0 * 0.8)))
            a0 = int((160 - 90 * t0) * fade * reach)
            if a0 <= 4:
                continue
            # inti terang
            _poly_a(surface, (*P("ice_hot"), a0), [
                (x0 + px * wid, y0 + py * wid),
                (x1 + px * wid, y1 + py * wid),
                (x1 - px * wid, y1 - py * wid),
                (x0 - px * wid, y0 - py * wid)])
            # selubung luar lebih lebar & redup
            wid2 = wid + 3.2
            _poly_a(surface, (*P("ice_mid"), int(a0 * 0.5)), [
                (x0 + px * wid2, y0 + py * wid2),
                (x1 + px * wid2, y1 + py * wid2),
                (x1 - px * wid2, y1 - py * wid2),
                (x0 - px * wid2, y0 - py * wid2)])
            # gerigi es di sepanjang tepi (setiap 2 segmen)
            if i % 2 == 0:
                gx = x1 + px * (wid2 + 2.6)
                gy = y1 + py * (wid2 + 2.6)
                ex = gx + px * 4.0 + dx * (2.0 if i % 4 == 0 else -2.0)
                ey = gy + py * 4.0 + dy * (2.0 if i % 4 == 0 else -2.0)
                _line_a(surface, (*P("ice_bright"), int(a0 * 0.8)),
                        (gx, gy), (ex, ey), 1)

        # ── gelombang dingin berjalan sepanjang beam ──
        for k in range(3):
            wp = (tt * 2.2 + k * 0.33) % 1.0
            wx = x + dx * length * wp
            wy = y + dy * length * wp
            er = ellipse_ring_surface(6, 3, 1, P("ice_pure"),
                                      int(200 * fade))
            surface.blit(er, (int(wx - er.get_width() / 2),
                              int(wy - er.get_height() / 2)))

        # ── ujung beam: kristal menabrak ──
        tipx = x + dx * length
        tipy = y + dy * length
        g = glow_surface(12, P("ice_pure"), 1.0)
        _blit_faded(surface, g, tipx, tipy, int(210 * fade), additive=True)
        sf = snowflake_surface(5)
        img = rotated_cached(("wsnow", 5), sf,
                             math.degrees(self.t * 6.0
                                          + math.sin(self.t * 34.0)))
        _blit_faded(surface, img, tipx, tipy, int(235 * fade),
                    additive=True)

    # ------------------------------------------------------------------
    def _draw_blast_charge(self, surface, x, y, t, ph):
        """E — Ice Blast: bola gather di tangan (bolt & ledakan terpisah)."""
        if ph != "CHARGE":
            # setelah release, sisa aura tangan sebentar
            if ph == "RELEASE":
                g = glow_surface(18, P("ice_pure"), 1.0)
                _blit_faded(surface, g, x, y,
                            int(220 * (1.0 - (t - 0.18) / 0.08)),
                            additive=True)
            return
        tt = t / 0.18
        a = int(120 + 130 * tt)
        r = int(7 + 11 * tt)
        g = glow_surface(r + 6, P("ice_mid"), 0.8)
        _blit_faded(surface, g, x, y, int(a * 0.7), additive=True)
        # inti berputar: shard saling mengunci
        for i in range(4):
            ang = self.t * 9.0 + i * math.tau / 4.0
            rr = r * (1.25 - tt * 0.85)
            sx = x + math.cos(ang) * rr
            sy = y + math.sin(ang) * rr
            sp = shard_surface(10, 2)
            img = rotated_cached(("echg", 10, 2), sp, math.degrees(ang))
            _blit_faded(surface, img, sx, sy, a, additive=True)
        core = glow_surface(max(3, int(r * 0.5)), P("ice_pure"), 1.2)
        _blit_faded(surface, core, x, y, a, additive=True)

    # ------------------------------------------------------------------
    def _draw_cold_feet(self, surface, x, y, t, ph):
        """R — Cold Feet: telegraph -> gather -> erupsi paku es melingkar."""
        fade = 1.0 if ph != "FADE" else max(0.0, 1.0 - (t - 0.82) / 0.18)
        if fade <= 0.02:
            return
        R = self.radius

        if ph in ("CAST", "CHARGE"):
            # telegraph: lingkar ganda berdenyut + segitiga peringatan
            pulse = 0.5 + 0.5 * math.sin(self.t * 14.0)
            a = int((150 + 80 * pulse) * fade)
            er = ellipse_ring_surface(int(R), int(R * 0.45), 2,
                                      P("ice_bright"), a)
            surface.blit(er, (x - er.get_width() // 2,
                              y - er.get_height() // 2))
            er2 = ellipse_ring_surface(int(R * 0.62), int(R * 0.28), 1,
                                       P("frost_light"), int(a * 0.7))
            surface.blit(er2, (x - er2.get_width() // 2,
                               y - er2.get_height() // 2))
            # tanda silang tengah
            for da in (0.7853982, -0.7853982):
                _line_a(
                    surface, (*P("ice_mid"), int(a * 0.6)),
                    (x - int(math.cos(da) * R * 0.3),
                     y - int(math.sin(da) * R * 0.14)),
                    (x + int(math.cos(da) * R * 0.3),
                     y + int(math.sin(da) * R * 0.14)), 1)
            return

        # RELEASE / AREA / FADE — erupsi paku es
        et = (t - 0.34) / 0.66
        grow = _ease_out(min(1.0, et / 0.22))
        shrink = 1.0 - max(0.0, (et - 0.6) / 0.4) * 0.8

        # cincin paku luar (12) + cincin dalam (8) + menara tengah
        for ring_i, (count, base_r, hbase) in enumerate((
                (12, R * 0.92, 30), (8, R * 0.5, 20))):
            for i in range(count):
                ang = i * math.tau / count + ring_i * 0.26 + \
                    _hash01(self.seed + i) * 0.2
                sx = x + int(math.cos(ang) * base_r)
                sy = y + int(math.sin(ang) * base_r * 0.48)
                hh = int((hbase + (i % 3) * 8) * grow * shrink)
                sp = spike_surface(3 + (i % 2), hh)
                _blit_faded(surface, sp, sx, sy - hh // 2,
                            int(240 * min(1.0, shrink)))
        # menara tengah
        hh = int(46 * grow * shrink)
        sp = spike_surface(5, max(6, hh))
        _blit_faded(surface, sp, x, y - hh // 2, int(250 * min(1.0, shrink)))
        _circle_a(surface, (*P("ice_pure"), int(235 * shrink)),
                  (x, y - hh + 3), 2)

        # gelombang beku di tanah (ring melebar setelah erupsi)
        if et > 0.12:
            wt = (et - 0.12) / 0.88
            rr = int(R * _ease_out(wt))
            er = ellipse_ring_surface(max(3, rr), max(2, int(rr * 0.45)), 2,
                                      P("ice_hot"), int(190 * fade *
                                                        (1.0 - wt)))
            surface.blit(er, (x - er.get_width() // 2,
                              y - er.get_height() // 2))

        # retakan radial
        for i in range(5):
            ang = i * math.tau / 5 + self.seed * 0.13
            cxp = x + int(math.cos(ang) * R * 0.75)
            cyp = y + int(math.sin(ang) * R * 0.36)
            crk = crack_surface(self.seed + i, int(R * 0.5), P("ice_mid"))
            img = rotated_cached(("rcrk", self.seed + i, int(R * 0.5)),
                                 crk, math.degrees(ang))
            _blit_faded(surface, img, cxp, cyp, int(170 * fade * shrink))


# ============================================================================
# 9.  GEOMETRI LENGAN  (MIRROR renderer — jangan sampai melenceng)
# ============================================================================
# Rumus yang sama dengan _NS_ancient_apparition.arm_geometry() supaya trail
# & asal shard di layar MENEMPEL pada cakar yang digambar renderer.  Kalau
# renderer bisa diimpor, pakai rumis asli; kalau tidak (tool minimal),
# fallback lokal di bawah identik.

_SHOULDER = (13.0, -6.0)
_UPPER = 10.0
_FORE = 11.0
_CLAW = 8.0


def _local_arc_angle(progress, action, phase):
    p = 0.0 if progress <= 0.0 else (1.0 if progress >= 1.0 else progress)
    if action == "attack":
        if p < 0.20:                       # ANTICIPATION: tarik ke belakang
            return 0.35 + (-0.55 - 0.35) * _ease_in_out(p / 0.20)
        if p < 0.38:                       # WIND-UP: angkat ke belakang kepala
            return -0.55 + (-1.62 - -0.55) * _ease_in_out((p - 0.20) / 0.18)
        if p < 0.55:                       # SWING: sapuan cepat ke depan
            return -1.62 + (0.55 - -1.62) * _ease_in((p - 0.38) / 0.17)
        if p < 0.75:                       # FOLLOW THROUGH
            return 0.55 + (0.75 - 0.55) * (p - 0.55) / 0.20
        # RECOVERY
        return 0.75 + (0.35 - 0.75) * _ease_out((p - 0.75) / 0.25)
    if action in ("cast_w",):
        return 0.05 + math.sin(phase * 26.0) * 0.03
    if action in ("cast_e",):
        return -0.12
    if action in ("cast_q",):
        return 0.28
    if action in ("cast_r",):
        return 1.85
    if action == "walk":
        return 0.35 + math.sin(phase * 2.6) * 0.22
    return 0.35 + math.sin(phase * 0.7) * 0.08


def arm_points(hero, x, y, progress=None, action=None):
    """Posisi (bahu, siku, tangan, ujung cakar) LAYAR untuk lengan depan.

    Mencoba memakai geometri renderer dulu (satu sumber kebenaran), lalu
    fallback lokal yang identik.  Selalu mengembalikan koordinat ABSOLUT
    layar relatif jangkar (x, y).
    """
    G = _renderer()
    facing = 1 if (getattr(hero, "facing", None) or
                   getattr(hero, "direction", 1) or 1) >= 0 else -1
    phase = float(getattr(hero, "pulse", 0.0))
    if action is None:
        action = "attack" if progress is not None and progress > 0 else "idle"
    if G is not None and hasattr(G, "arm_geometry"):
        try:
            geo = G.arm_geometry(facing, action, phase, progress or 0.0)
            return tuple((x + g[0], y + g[1]) for g in geo)
        except Exception:                  # pragma: no cover
            pass
    ang = _local_arc_angle(progress or 0.0, action, phase)
    sx = x + _SHOULDER[0] * facing
    sy = y + _SHOULDER[1]
    ex = sx + math.cos(ang - 0.55) * _UPPER * facing
    ey = sy - math.sin(ang - 0.55) * _UPPER
    hx = ex + math.cos(ang) * _FORE * facing
    hy = ey - math.sin(ang) * _FORE
    tx = hx + math.cos(ang) * _CLAW * facing
    ty = hy - math.sin(ang) * _CLAW
    return ((sx, sy), (ex, ey), (hx, hy), (tx, ty))


def world_anchor(hero, x, y, wx, wy):
    """Peta koordinat DUNIA -> layar relatif terhadap jangkar (x, y)."""
    bx = float(getattr(hero, "x", wx))
    by = float(getattr(hero, "y", wy))
    return (x + (float(wx) - bx), y + (float(wy) - by))


def target_screen(hero, x, y):
    """Posisi layar target (atau titik 160px di depan kalau tak ada)."""
    t = getattr(hero, "target", None)
    if t is not None and getattr(t, "alive", True):
        return world_anchor(hero, x, y,
                            float(getattr(t, "x", 0.0)),
                            float(getattr(t, "y", 0.0)))
    f = 1 if (getattr(hero, "direction", 1) or 1) >= 0 else -1
    # Lapisan hidup 1:1: 160 px adalah 160 px DUNIA/Layar, bukan canvas
    # renderer (tanpa `_render_scale`).
    return (x + 160.0 * f, y - 6.0)


# ============================================================================
# 10.  DIRECTOR  (satu per unit — state machine + timeline + emisi)
# ============================================================================

class ApparitionFXDirector:
    """Mengikat semua sistem FX untuk SATU unit Ancient Apparition."""

    def __init__(self, hero):
        self.hero = hero
        self.time = 0.0
        self.frames = 0
        self._last_ms = None

        # ── sistem ──
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.projectiles = ProjectileSystem(MAX_PROJECTILES)
        self.trail = SlashTrail()
        self.impacts = []
        self.skills = []

        # ── state animasi ──
        self.state = "IDLE"
        self.prev_state = "IDLE"
        self.state_time = 0.0
        self.anim_phase = "IDLE"
        self.anim_frame = 0

        # ── timeline serangan (sumber: attack_timer gameplay) ──
        self.attack_progress = 0.0
        self._attack_live = False
        self._attack_frame = 0
        self._prev_timer = -1
        self._swing_seen = False
        self._shard_released = False
        self._atk_emit = 0.0

        # ── deteksi ──
        self._last_x = None
        self._last_y = None
        self._moving = False
        self._speed = 0.0
        self._last_hp = None
        self._was_alive = True
        self.hit_flash = 0.0
        self._skill_seen = None
        self._vortex_seen = 0
        self._fps = 60.0
        self._dt_avg = 1.0 / 60.0

    # ------------------------------------------------------------------
    def stats(self):
        return {
            "state": self.state,
            "phase": self.anim_phase,
            "attack_t": round(self.attack_progress, 2),
            "particles": self.particles.count(),
            "projectiles": self.projectiles.count(),
            "impacts": len(self.impacts),
            "trail": len(self.trail.hist),
            "skills": len(self.skills),
            "fps": int(self._fps),
        }

    def clear(self):
        self.particles.clear()
        self.projectiles.clear()
        self.trail.reset()
        self.impacts.clear()
        self.skills.clear()

    # ------------------------------------------------------------------
    # State machine (prioritas + transisi)
    # ------------------------------------------------------------------
    def _desired_state(self):
        h = self.hero
        if not getattr(h, "alive", True):
            return "DEATH"
        if self.hit_flash > 0.10:
            return "HURT"
        if self.hit_flash > 0.03:
            return "HIT"
        skill = getattr(h, "active_skill", None)
        if skill == "r":
            return "SPECIAL"
        if skill in ("q", "w", "e"):
            return "SKILL" if skill != "e" else "CAST"
        if self._attack_live:
            ph = attack_phase(self.attack_progress)
            if ph in ("swing",):
                return "SWING"
            if ph in ("anticipation", "windup"):
                return "CHARGE"
            return "ATTACK"
        if self._moving and self._speed > 1.35:
            return "RUN"
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
            if not locked and (new_p >= cur_p or self.state_time > 0.06):
                self.prev_state = self.state
                self.state = want
                self.state_time = 0.0
        self.state_time += dt
        self.anim_frame += 1
        self.anim_phase = attack_phase(self.attack_progress) \
            if self._attack_live else self.state

    # ------------------------------------------------------------------
    # Timeline serangan 60 Hz — progress halus walau sprite di-cache
    # ------------------------------------------------------------------
    def _update_attack_timeline(self):
        h = self.hero
        cd = max(2, int(getattr(h, "attack_cooldown", 46)))
        timer = int(getattr(h, "attack_timer",
                            getattr(h, "timer", 0)) or 0)
        prev = self._prev_timer
        if prev < 0:
            if timer > 0:
                self._attack_live = True
                self._shard_released = False
        elif timer > prev:
            self._attack_live = True
            self._attack_frame = 0
            self._shard_released = False
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
    # Callback gameplay -> FX
    # ------------------------------------------------------------------
    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False, kind="hit"):
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind,
                                     self.particles))

    def on_hurt(self, amount=1.0):
        self.hit_flash = max(self.hit_flash, 0.16 + 0.1 * min(2.0, amount))
        h = self.hero
        hx = float(getattr(h, "x", 0.0))
        hy = float(getattr(h, "y", 0.0))
        # serpihan es lepas dari badan
        self.particles.burst(hx, hy - 18, 8, speed=(50, 190),
                             life=(0.25, 0.55), size=(1, 3),
                             colors=(P("ice_light"), P("ice_bright")),
                             spread=math.tau, shape="shard",
                             rotation_speed=(-8, 8), gravity=210, drag=1.2)
        if _feel is not None and shake_allowed():
            _feel.shake(2.6, 0.16)

    def on_death(self):
        h = self.hero
        hx = float(getattr(h, "x", 0.0))
        hy = float(getattr(h, "y", 0.0))
        # SHATTER: badan es pecah — shard besar + salju + mist + nova
        self.particles.burst(hx, hy - 22, 26, speed=(60, 320),
                             life=(0.5, 1.0), size=(2, 5),
                             colors=(P("ice_mid"), P("ice_light"),
                                     P("ice_bright")),
                             spread=math.tau, shape="shard",
                             rotation_speed=(-10, 10), gravity=260, drag=1.0)
        self.particles.burst(hx, hy - 22, 16, speed=(30, 120),
                             life=(0.7, 1.3), size=(4, 8),
                             colors=(P("frost_mid"),), spread=math.tau,
                             shape="smoke", back=True, gravity=-20)
        self.particles.burst(hx, hy - 22, 14, speed=(40, 160),
                             life=(0.4, 0.8), size=(1, 3),
                             colors=(P("ice_hot"), P("white")),
                             spread=math.tau, shape="snow",
                             rotation_speed=(-8, 8))
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(hx, hy - 18, 0.0, 1.8, False, "blast",
                                     self.particles))
        self.clear_skill_fx()

    def clear_skill_fx(self):
        self.skills.clear()

    def on_cast(self, x, y, skill, angle=None):
        if skill not in ("q", "w", "e", "r"):
            return
        h = self.hero
        facing = 1 if (getattr(h, "facing",
                               getattr(h, "direction", 1)) or 1) >= 0 else -1
        if angle is None:
            tx, ty = target_screen(h, x, y)
            angle = math.atan2(ty - (y - 10), tx - x)
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        sx, sy = x, y
        if skill == "q":
            # vortex di lokasi target (koordinat dunia bila ada)
            vx = getattr(h, "vortex_x", None)
            vy = getattr(h, "vortex_y", None)
            if vx is not None and vy is not None:
                sx, sy = world_anchor(h, x, y, float(vx), float(vy))
            else:
                sx, sy = target_screen(h, x, y)
            radius = 74.0
            # baca radius gameplay bila ada (80 dunia)
            self.skills.append(SkillFX("q", sx, sy, self.particles,
                                       radius, facing=facing))
        elif skill == "w":
            wdx = getattr(h, "w_dir_x", None)
            wdy = getattr(h, "w_dir_y", None)
            if wdx is not None and wdy is not None:
                angle = math.atan2(float(wdy), float(wdx))
            self.skills.append(SkillFX("w", x + 18 * facing, y - 12,
                                       self.particles, 190.0,
                                       facing=facing, angle=angle))
        elif skill == "e":
            tx, ty = target_screen(h, x, y)
            ang = math.atan2(ty - (y - 14), tx - x)
            self.skills.append(SkillFX("e", x + 16 * facing, y - 14,
                                       self.particles, 64.0,
                                       facing=facing, angle=ang,
                                       projectiles=self.projectiles))
        elif skill == "r":
            # R menempel di TARGET (line AOE dari diri sendiri ke arah)
            rdx = getattr(h, "r_dir_x", None)
            rdy = getattr(h, "r_dir_y", None)
            if rdx is not None and rdy is not None:
                angle = math.atan2(float(rdy), float(rdx))
            tx, ty = target_screen(h, x, y)
            self.skills.append(SkillFX("r", tx, ty + 8, self.particles,
                                       96.0, facing=facing, angle=angle))
            # jejak beku sepanjang garis R
            for i in range(6):
                k = i / 6.0
                mx = x + (tx - x) * k
                my = (y - 6) + (ty - (y - 6)) * k
                self.particles.spawn(mx, my, random.uniform(-14, 14),
                                     random.uniform(-30, -6),
                                     random.uniform(0.4, 0.8),
                                     random.randint(2, 4), P("frost_mid"),
                                     shape="mist", back=True)

    # ------------------------------------------------------------------
    # Update utama (delta-time nyata, diperlambat saat hit-stop)
    # ------------------------------------------------------------------
    def update(self, dt):
        if dt <= 0.0:
            return
        h = self.hero
        self.time += dt
        self.frames += 1
        self._dt_avg = self._dt_avg * 0.9 + dt * 0.1
        if self._dt_avg > 0:
            self._fps = 1.0 / self._dt_avg
        hx = float(getattr(h, "x", 0.0))
        hy = float(getattr(h, "y", 0.0))

        # ── deteksi gerak & kecepatan (px per langkah update ~ per frame,
        #    sama satuan dengan _NS_ancient_apparition._detect_moving) ──
        if self._last_x is None:
            self._last_x, self._last_y = hx, hy
            self._moving = False
            self._speed = 0.0
        else:
            dxm = hx - self._last_x
            dym = hy - self._last_y
            self._speed = math.hypot(dxm, dym)
            self._moving = (abs(dxm) + abs(dym)) > 0.3
            self._last_x, self._last_y = hx, hy
        try:
            h._moving_cached = self._moving
            h._moving_speed = self._speed
        except Exception:                  # pragma: no cover
            pass

        # ── deteksi damage (watch HP — tanpa hook eksternal pun jalan) ──
        hp = float(getattr(h, "hp", 0.0) or 0.0)
        if self._last_hp is not None and hp < self._last_hp - 0.01:
            self.on_hurt((self._last_hp - hp)
                         / max(1.0, float(getattr(h, "max_hp", 1.0))))
        self._last_hp = hp

        # ── deteksi kematian ──
        alive = bool(getattr(h, "alive", True))
        if self._was_alive and not alive:
            self.on_death()
        self._was_alive = alive

        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)

        self._update_attack_timeline()
        self._update_state(dt)

        facing = 1 if (getattr(h, "facing",
                               getattr(h, "direction", 1)) or 1) >= 0 else -1

        # ── skill cast detection (edge-triggered) ──
        skill = getattr(h, "active_skill", None)
        if skill != self._skill_seen:
            if skill in ("q", "w", "e", "r"):
                self.on_cast(hx, hy, skill)
            self._skill_seen = skill

        # ── vortex Q aktif di dunia (DOT) — pastikan FX hidup di sana ──
        vt = int(getattr(h, "vortex_active_timer", 0) or 0)
        if vt > 0 and self._vortex_seen <= 0 and skill != "q":
            vx = getattr(h, "vortex_x", None)
            vy = getattr(h, "vortex_y", None)
            if vx is not None and vy is not None:
                sx, sy = world_anchor(h, hx, hy, float(vx), float(vy))
                if len(self.skills) >= MAX_SKILLS:
                    self.skills.pop(0)
                self.skills.append(SkillFX("q", sx, sy, self.particles,
                                           74.0, facing=facing))
        self._vortex_seen = vt

        # ── jendela ayunan: trail + emisi ──
        ap = self.attack_progress
        swinging = self._attack_live and SWING_START <= ap <= SWING_END
        if swinging and not self._swing_seen:
            self.trail.reset()
        elif not swinging and self._swing_seen:
            pass                            # ribbon dibiarkan memudar
        self._swing_seen = swinging

        if swinging:
            (_s, _e, hand, tip) = arm_points(h, hx, hy, progress=ap,
                                             action="attack")
            self.trail.push(hand, tip)
            # percikan salju dari cakar saat menyapu
            self._atk_emit += dt
            if self._atk_emit > 0.05:
                self._atk_emit = 0.0
                self.particles.spawn(tip[0], tip[1],
                                     random.uniform(-40, 40) - 60 * facing,
                                     random.uniform(-50, 10),
                                     random.uniform(0.2, 0.45), 2,
                                     random.choice((P("ice_bright"),
                                                    P("ice_hot"))),
                                     shape="pixel", add=True, shrink=0.5)

        # ── pelepasan shard di titik IMPACT ──
        if swinging and not self._shard_released and \
                ap >= ATTACK_IMPACT_POINT:
            self._shard_released = True
            tx, ty = target_screen(h, hx, hy)
            (_s, _e, _h, tip) = arm_points(h, hx, hy, progress=ap,
                                           action="attack")
            self.projectiles.spawn(tip[0], tip[1], tx, ty - 8,
                                   kind="shard", target=h.target,
                                   lifetime=1.4)
            # muzzle flash kecil di cakar
            self.particles.burst(tip[0], tip[1], 5, speed=(40, 160),
                                 life=(0.12, 0.3), size=(1, 2),
                                 colors=(P("ice_hot"), P("white")),
                                 spread=1.6,
                                 direction=math.atan2(ty - tip[1],
                                                      tx - tip[0]),
                                 shape="spark", add=True)

        # ── emisi ambient ──
        if alive and particle_budget() > 0.05:
            self._ambient(hx, hy, facing, dt, swinging)

        # ── majukan sistem ──
        self.trail.update(dt)
        self.particles.update(dt)

        def _proj_impact(p):
            kind = "blast" if p.kind == "bolt" else "hit"
            self.on_impact(p.position.x, p.position.y,
                           math.atan2(-p.velocity.y, -p.velocity.x),
                           1.3 if p.kind == "bolt" else 0.9,
                           p.crit, kind)

        self.projectiles.update(dt, self.particles, _proj_impact)
        for fx in self.impacts:
            fx.update(dt)
        self.impacts = [f for f in self.impacts if f.alive]
        for s in self.skills:
            s.update(dt)
        self.skills = [s for s in self.skills if s.alive]

    # ------------------------------------------------------------------
    def _ambient(self, hx, hy, facing, dt, swinging):
        """Emisi ambient: salju melayang, napas beku, debu langkah."""
        h = self.hero
        # salju halus mengorbit badan (identitas AA)
        if random.random() < 0.28:
            ang = random.random() * math.tau
            rr = random.uniform(14.0, 30.0)
            self.particles.spawn(hx + math.cos(ang) * rr,
                                 hy - 16 + math.sin(ang) * rr * 0.8,
                                 random.uniform(-12, 12),
                                 random.uniform(-26, -6),
                                 random.uniform(0.7, 1.4),
                                 random.randint(1, 2),
                                 random.choice((P("ice_bright"),
                                                P("frost_light"))),
                                 shape="pixel", shrink=0.4)
        # mist dingin dari skirt
        if random.random() < 0.22:
            self.particles.spawn(hx + random.uniform(-14, 14), hy + 26,
                                 random.uniform(-10, 10),
                                 random.uniform(-30, -12),
                                 random.uniform(0.6, 1.1), random.randint(3, 5),
                                 P("frost_mid"), shape="mist", back=True)
        # debu salju saat jalan (foot timing — dua langkah per siklus)
        if self._moving and not swinging and random.random() < 0.30:
            side = 1 if math.sin(float(getattr(h, "pulse", 0.0)) * 2.6) > 0 \
                else -1
            self.particles.spawn(hx - 6 * facing + 6 * side * facing,
                                 hy + 30, -facing * random.uniform(16, 44),
                                 -random.uniform(6, 26),
                                 random.uniform(0.3, 0.6), 2,
                                 P("frost_light"), shape="mist", back=True)

    # ------------------------------------------------------------------
    # Render layers
    # ------------------------------------------------------------------
    def draw_ground(self, surface, x, y):
        """GROUND FX + BACK PARTICLES (di bawah sprite)."""
        h = self.hero
        # genangan beku halus di bawah kaki
        if getattr(h, "alive", True):
            g = glow_surface(30, P("ice_dark"), 0.22)
            _blit_faded(surface, g, x, y + 34, 90)
        # vortex Q (area tanah di lokasi target) + telegraph R digambar
        # di bawah semua unit; erupsi R (paku) menyusul di depan.
        for s in self.skills:
            if s.skill == "q":
                s.draw(surface)
            elif s.skill == "r" and s.phase in ("CAST", "CHARGE"):
                s.draw(surface)
        self.particles.draw(surface, layer=True)

    def draw_front(self, surface, x, y):
        """TRAIL / PROJECTILE / FRONT PARTICLES / SKILL / IMPACT / DEBUG."""
        h = self.hero
        over = getattr(h, "active_skill", None) is not None
        self.trail.overcharged = over
        if len(self.trail.hist) >= 2:
            self.trail.draw(surface)
        self.projectiles.draw(surface)
        self.particles.draw(surface, layer=False)
        for s in self.skills:
            if s.skill == "r":
                if s.phase not in ("CAST", "CHARGE"):
                    s.draw(surface)       # erupsi paku es di atas tanah
            elif s.skill != "q":
                s.draw(surface)           # beam W / charge E
        for fx in self.impacts:
            fx.draw(surface)
        if DEBUG_CHARACTER:
            draw_debug_overlay(surface, self, x, y)


# ============================================================================
# 11.  DEBUG OVERLAY
# ============================================================================

def draw_debug_overlay(surface, director, x, y):
    """Hitbox, hurtbox, jangkauan, tabrakan proyektil, state, frame, FPS."""
    h = director.hero
    try:
        font = pygame.font.SysFont("consolas,monospace", 12)
    except Exception:                      # pragma: no cover
        return

    # hurtbox = radius unit
    r = max(8, int(getattr(h, "radius", 30)))
    pygame.draw.circle(surface, (80, 170, 255),
                       (int(x), int(y)), r, 1)

    # hitbox ayunan (aktif hanya di jendela swing)
    if director._attack_live and \
            SWING_START <= director.attack_progress <= SWING_END:
        facing = 1 if (getattr(h, "direction", 1) or 1) >= 0 else -1
        hb = pygame.Rect(int(x) + (10 if facing > 0 else -56), int(y) - 26,
                         46, 34)
        pygame.draw.rect(surface, (255, 70, 70), hb, 2)
        pygame.draw.rect(surface, (255, 70, 70), hb)

    # jangkauan serangan
    rng = max(10, int(getattr(h, "range", 150) * 0.5))
    pygame.draw.line(surface, (255, 210, 60), (int(x), int(y)),
                     (int(x) + rng * (1 if (getattr(h, "direction", 1) or 1)
                                      > 0 else -1), int(y)), 1)

    # tabrakan proyektil
    for p in director.projectiles.items:
        pygame.draw.circle(surface, (255, 120, 255),
                           (int(p.position.x), int(p.position.y)),
                           int(p.hit_radius), 1)

    st = director.stats()
    try:
        fps = int(pygame.time.Clock().get_fps())
    except Exception:                      # pragma: no cover
        fps = st["fps"]
    lines = [
        "AA    %s / %s" % (st["state"], st["phase"]),
        "atkT  %.2f  skill %s" % (st["attack_t"],
                                  getattr(h, "active_skill", None)),
        "part %d  proj %d  imp %d" % (st["particles"], st["projectiles"],
                                      st["impacts"]),
        "skillFX %d  trail %d" % (st["skills"], st["trail"]),
        "shake %.1f  stop %d  fps %d" % (
            (_feel.amount() if _feel is not None else 0.0),
            (_feel.stats().get("hitstop_frames", 0)
             if _feel is not None else 0), fps),
    ]
    for i, txt in enumerate(lines):
        img = font.render(txt, True, (200, 245, 255))
        surface.blit(img, (x - 64, y - 118 + i * 13))


# ============================================================================
# 12.  RENDERER SHARD BERSAMA  (dipakai _entity.py jalur hero)
# ============================================================================

def draw_ice_shard(surface, px, py, angle=0.0, age=0, crit=False,
                   radius=7.0):
    """Renderer proyektil es untuk jalur projectile generik Hero.

    Dipanggil _entity.Hero._draw_ice_shard_projectile supaya basic attack
    Ancient Apparition saat DIMAINKAN tampil identik dengan shard lapisan
    hidup: badan bersegi berarah, inti panas, halo, dan ekor memudar.
    """
    _sync_palette()
    px, py = int(px), int(py)
    deg = math.degrees(angle)

    # ekor facet dari histori singkat (posisi mundur searah)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    for i in range(3):
        off = (i + 1) * 6
        tx = px - int(cos_a * off)
        ty = py - int(sin_a * off)
        surf = shard_surface(10 - i * 2, 2)
        img = rotated_cached(("ent", 10 - i * 2, 2), surf, deg)
        _blit_faded(surface, img, tx, ty, 130 - i * 38, additive=True)

    if glow_allowed():
        g = glow_surface(int(radius * 2.2), P("ice_light"), 0.8)
        _blit_faded(surface, g, px, py, 140, additive=True)

    ln = int(radius * 2.4)
    wd = max(2, int(radius * 0.5))
    surf = shard_surface(ln, wd)
    img = rotated_cached(("entb", ln, wd), surf, deg)
    surface.blit(img, (px - img.get_width() // 2,
                       py - img.get_height() // 2))
    hot = glow_surface(max(2, int(radius * 0.7)), P("ice_pure"), 1.1)
    _blit_faded(surface, hot, px, py, 220, additive=True)
    if crit:
        sp = snowflake_surface(4)
        _blit_faded(surface, sp, px, py, 235, additive=True)


# ============================================================================
# 13.  API MODUL  —  registry, tick, hook render, notify
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit."""
    _sync_palette()
    d = getattr(hero, "_aa_fx", None)
    if d is None:
        d = ApparitionFXDirector(hero)
        try:
            hero._aa_fx = d
        except Exception:                  # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:           # jangkar tua dibuang
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    """Lepas director dari registry DAN penanda milik-nya di unit."""
    try:
        if director.hero is not None:
            director.hero._aa_fx = None
            director.hero._aa_live_fx = False
            director.hero._skip_renderer_projectiles = False
    except Exception:                      # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit (dipanggil pipeline render).

    Sekalian menandai unit supaya renderer TIDAK menggambar efek yang
    sekarang dimiliki lapisan hidup (shard canvas + skill FX canvas).
    """
    if not APPARITION_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                      # pragma: no cover
        return False
    try:
        hero._aa_live_fx = True
        hero._skip_renderer_projectiles = True
    except Exception:                      # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not getattr(hero, "_aa_live_fx", False):
        return False
    d = getattr(hero, "_aa_fx", None)
    return d is not None and d in _DIRECTORS


def _advance(director):
    """Majukan SATU director sesuai waktu sejak langkah terakhirnya (O(n)).

    Mengapa tidak sekadar memanggil ``tick()`` dari ``draw_ground_layer``?
    Karena ``tick()`` memajukan SEMUA director — kalau 8 Ancient Apparition
    dirender dalam satu frame, jalur itu berarti O(n^2).  Dengan stempel
    waktu per director, tiap unit maju tepat sekali per frame gambar.
    Bus game-feel tetap disentuh lewat ``combat_feel.fx_dt()`` supaya
    peluruhan shake tidak pernah tertinggal.
    """
    if not APPARITION_FX_ENABLED or director is None:
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
    director.update(dt)
    return dt


def tick(dt=None):
    """Majukan waktu FX satu frame nyata.  Aman dipanggil berkali-kali."""
    global _LAST_TICK_MS
    now = pygame.time.get_ticks()
    if dt is None:
        if _feel is not None:
            if now == _LAST_TICK_MS:
                return 0.0
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
    if dt > 0.0:
        for d in _DIRECTORS:
            try:
                d._last_ms = now
                d.update(dt)
            except Exception:              # pragma: no cover
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
    """Jumlah partikel AA hidup di seluruh arena (HUD perf / audit)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def total_projectiles():
    """Jumlah proyektil visual AA hidup (HUD perf / audit)."""
    return sum(d.projectiles.count() for d in _DIRECTORS)


def projectiles_for(hero):
    """Akses proyektil director unit (dipakai overlay debug renderer)."""
    d = getattr(hero, "_aa_fx", None)
    return d.projectiles.items if d is not None else []


# --- hook yang dipanggil heroes/__init__.py + bosses/level3.py -------------

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: GROUND FX + BACK PARTICLES, di bawah sprite."""
    if not APPARITION_FX_ENABLED:
        return
    if getattr(hero, "_portrait_hd", False):
        return
    attach(hero)
    d = director_for(hero)
    _advance(d)
    try:
        d.draw_ground(surface, x, y)
    except Exception:                      # pragma: no cover - anti gagal
        pass


def draw_live_layer(surface, hero, x, y):
    """Post-pass: TRAIL / PROJECTILE / SKILL / IMPACT / DEBUG."""
    if not APPARITION_FX_ENABLED:
        return
    if getattr(hero, "_portrait_hd", False):
        return
    try:
        director_for(hero).draw_front(surface, x, y)
    except Exception:                      # pragma: no cover
        pass


# --- hook yang dipanggil _entity.py ----------------------------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Serangan jarak dekat AA mengenai target (jalur melee paritas)."""
    if not APPARITION_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except Exception:                      # pragma: no cover
        power = 1.0
    tx = float(getattr(target, "x", 0)) if target is not None else 0.0
    ty = float(getattr(target, "y", 0)) if target is not None else 0.0
    ang = math.atan2(float(getattr(hero, "y", 0.0)) - ty,
                     tx - float(getattr(hero, "x", 0.0)))
    director_for(hero).on_impact(tx, ty - 10, ang, power, crit, "hit")


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False):
    """Shard basic attack mendarat (jalur ranged generik _entity)."""
    if not APPARITION_FX_ENABLED or hero is None:
        return
    try:
        power = 0.75 + min(1.7, float(damage) / 42.0)
    except Exception:                      # pragma: no cover
        power = 1.0
    director_for(hero).on_impact(float(x), float(y) - 10, float(angle),
                                 power, crit, "hit")


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """Skill AA meledak di sebuah titik (dipakai tooling/audit)."""
    if not APPARITION_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    if len(d.skills) >= MAX_SKILLS - 1:
        d.skills.pop(0)
    f = 1 if (getattr(hero, "facing",
                      getattr(hero, "direction", 1)) or 1) >= 0 else -1
    d.skills.append(SkillFX(skill, float(x), float(y), d.particles,
                            radius, facing=f))


def notify_skill_cast(hero, skill):
    """Skill AA dilepas dari luar (auto-cast guard / tooling)."""
    if not APPARITION_FX_ENABLED or hero is None:
        return
    director_for(hero).on_cast(float(getattr(hero, "x", 0.0)),
                               float(getattr(hero, "y", 0.0)), skill)


def notify_hurt(hero, amount=1.0):
    """AA terkena damage dari luar (tanpa menunggu watch hp)."""
    if not APPARITION_FX_ENABLED or hero is None:
        return
    director_for(hero).on_hurt(amount)
