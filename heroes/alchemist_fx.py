# ============================================================================
# heroes/alchemist_fx.py
# ----------------------------------------------------------------------------
# ALCHEMIST — COMBAT / GAME-FEEL ENGINE  (screen-space live layer)
#
# Badan Alchemist digambar lewat ``_NS_alchemist`` (bosses/level2.py) ke
# canvas yang DI-CACHE lalu di-scale oleh pipeline hero.  Artinya semua
# yang butuh gerak 60 fps sejati — trail cleaver, partikel asap/asam,
# botol Unstable Concoction, impact, hit-stop — TIDAK boleh hidup di
# dalam canvas itu.  Modul ini adalah lapisan hidup tersebut: digambar
# langsung ke layar pada skala 1:1 tiap frame, dengan delta-time nyata.
#
# Pembagian kerja (tidak ada efek yang digambar 2x):
#
#   RENDERER (canvas, ter-cache)      MODUL INI (layar, hidup)
#   -----------------------------     -----------------------------------
#   rig + selout + rim light          trail cleaver (histori busur nyata)
#   bayangan kontak, aura, wisps      partikel (asap, debu, percikan, koin)
#   TELEGRAPH decal Q/W/E/R           PROYEKTIL botol asam (sistem nyata)
#   pose, napas, siklus jalan         semburan droplet Acid Spray (Q)
#   FX canvas fallback                IMPACT FX + flash + hit-stop + shake
#                                     SkillFX Q/W/E/R + overlay DEBUG
#
# 100% PROSEDURAL. Tidak ada PNG / JPG / GIF / sprite-sheet / pemuatan
# aset eksternal. Semua bentuk dibuat dengan pygame.draw + pygame.Surface
# + pygame.transform + pygame.Vector2.
#
# Isi modul
#   ALCHEMIST_PALETTE   palette khusus karakter (kontrak 9 kunci + ramp)
#   Particle            partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem      pool + burst + stream + cap, reusable
#   SwingTrail          weapon trail prosedural dari histori posisi bilah
#   ImpactFX            flash + shockwave + debris + slash fragment
#   AlchemistProjectile proyektil modular (spawn->travel->hit->destroy)
#   ProjectileSystem    manajer proyektil
#   SkillFX             lifecycle FX skill (cast->charge->release->fade)
#   AlchemistFXDirector satu instance per unit, mengikat semua di atas
#   draw_debug_overlay  hitbox/hurtbox/state/frame/FPS/particle/timer
#   API modul           tick / reset_all / notify_* / draw_*_layer
# ============================================================================

import math
import random

import pygame
from pygame import Vector2

try:                                 # bus game-feel bersama (satu sumber
    from heroes import combat_feel as _feel   # kebenaran hit-stop & shake)
except Exception:                    # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual untuk karakter ALCHEMIST: hitbox, hurtbox, jangkauan,
#: state animasi, frame, FPS, jumlah partikel, state skill, timer serang.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
ALCHEMIST_FX_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 170

#: Batas keras proyektil hidup per director.
MAX_PROJECTILES = 14

#: Panjang histori trail senjata (jumlah sample posisi bilah).
TRAIL_SAMPLES = 14

#: Batas dampak aktif per director & skill sekaligus di layar.
MAX_IMPACTS = 8
MAX_SKILLS = 4

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Kecepatan botol Unstable Concoction (px/detik, ruang layar boss).
BOTTLE_SPEED = 330.0
BOTTLE_ARC = 46.0

#: Radius EFEK di ruang dunia (harus sama dengan gameplay base_boss.py /
#: hero_skills/_bundle.py: W AOE 100 di target, R AOE 200 di sekitar diri,
#: Q genangan ~100 visual, E buff denyut ~90).
WORLD_RADIUS = {"q": 100.0, "w": 100.0, "e": 90.0, "r": 200.0}

#: Umur FX skill dalam DETIK — sinkron dengan ``_NS_alchemist.SKILL_DUR``
#: (40/60/60/90 langkah = 0.67/1.00/1.00/1.50 s) + after-glow.
SKILL_TOTAL = {"q": 1.05, "w": 1.30, "e": 1.15, "r": 2.05}

#: Durasi pose per skill (frame) — dipakai memetakan umur FX ke fase
#: yang sama dengan yang dibaca renderer.
SKILL_DUR = {"q": 40, "w": 60, "e": 60, "r": 90}


# ============================================================================
# 1.  PALETTE — dark-fantasy ogre chemist: asam hijau + emas serakah
# ============================================================================

#: Kontrak palette karakter: 9 kunci wajib + ramp khusus.
ALCHEMIST_PALETTE = {
    # ── 9 kunci kontrak (nilai literal = fallback; _sync_palette
    #    menyalin ulang dari renderer supaya satu sumber kebenaran) ──
    "outline":    (12,  36,   8),
    "shadow":     (18,  11,   6),
    "dark":       (40,  88,  16),
    "body":       (96, 158,  36),
    "mid":        (150, 222, 46),
    "light":      (198, 246, 84),
    "highlight":  (232, 255, 150),
    "weapon":     (148, 104, 36),
    "fx":         (198, 246, 84),

    # ── ramp asam (spray / botol / genangan / trail) ───────────────
    "acid_darkest": (12,  36,   8),
    "acid_dark":    (40,  88,  16),
    "acid_mid":     (96, 158,  36),
    "acid_bright":  (150, 222, 46),
    "acid_hot":     (198, 246, 84),
    "acid_glow":    (232, 255, 150),
    "acid_white":   (246, 255, 214),

    # ── ramp emas (Greevil's Greed) ────────────────────────────────
    "gold_darkest": (48,  30,   8),
    "gold_dark":    (116,  76,  12),
    "gold_mid":     (196, 150,  34),
    "gold_light":   (244, 208,  78),
    "gold_shine":   (255, 242, 160),

    # ── ogre / kulit / logam (mengikuti renderer) ──────────────────
    "ogre_dark":    (96,  52,  16),
    "ogre_mid":     (158, 98,  32),
    "ogre_light":   (205, 143, 52),
    "leather":      (86,  57,  29),
    "leather_dark": (44,  28,  15),
    "brass":        (148, 104, 36),
    "brass_hot":    (246, 218, 132),
    "metal":        (142, 140, 156),

    # ── partikel lingkungan ────────────────────────────────────────
    "dust":      (108,  96,  76),
    "dust_dark": (66,   58,  46),
    "smoke":     (74,  84,  66),
    "smoke_dark":(44,  52,  40),
    "ash":       (58,  66,  52),
    "vapor":     (150, 200, 120),

    # ── hurt (unit biru kena pukul) ────────────────────────────────
    "blue":      (110, 190, 255),
    "blue_hot":  (190, 235, 255),
}

P = ALCHEMIST_PALETTE

#: Pemetaan sinkronisasi: kunci modul <- kunci renderer.
_PALETTE_SYNC = {
    "outline":      "acid_darkest",
    "shadow":       "leather_darkest",
    "dark":         "acid_dark",
    "body":         "acid_mid",
    "mid":          "acid_bright",
    "light":        "acid_hot",
    "highlight":    "acid_glow",
    "weapon":       "brass_mid",
    "fx":           "acid_hot",
    "acid_darkest": "acid_darkest",
    "acid_dark":    "acid_dark",
    "acid_mid":     "acid_mid",
    "acid_bright":  "acid_bright",
    "acid_hot":     "acid_hot",
    "acid_glow":    "acid_glow",
    "acid_white":   "acid_white",
    "gold_darkest": "gold_darkest",
    "gold_dark":    "gold_dark",
    "gold_mid":     "gold_mid",
    "gold_light":   "gold_light",
    "gold_shine":   "gold_shine",
    "ogre_dark":    "ogre_dark",
    "ogre_mid":     "ogre_mid",
    "ogre_light":   "ogre_light",
    "leather":      "leather_mid",
    "leather_dark": "leather_dark",
    "brass":        "brass_mid",
    "brass_hot":    "brass_shine",
    "metal":        "metal_light",
}

_PALETTE_SYNCED = False


def _sync_palette():
    """Salin warna tema dari ``_NS_alchemist.PALETTE`` sekali saja."""
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
    """``_NS_alchemist`` atau None. Diimpor malas: modul boss besar."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from bosses.level2 import _NS_alchemist as G
            _RENDERER = G
        except Exception:                      # pragma: no cover
            _RENDERER = False
    return _RENDERER or None


def _fallback_pose(boss):
    """(action, phase, ap) tanpa renderer: baca atribut yang sudah ada."""
    skill = getattr(boss, "active_skill", None)
    moving = bool(getattr(boss, "_alch_moving", False))
    if getattr(boss, "_alch_attack_active", False):
        action = "attack"
    elif skill == "q":
        action = "q_cast"
    elif skill == "w":
        action = "w_cast"
    elif skill == "e":
        action = "e_cast"
    elif skill == "r":
        action = "r_cast"
    else:
        action = "walk" if moving else "idle"
    phase = float(getattr(boss, "pulse", 0.0) or 0.0)
    ap = 0.0
    if action == "attack":
        raw = float(getattr(boss, "_alch_attack_progress", 0.0) or 0.0)
        G = _renderer()
        ap = G._attack_curve(min(1.0, max(0.0, raw))) if G is not None \
            else min(1.0, max(0.0, raw))
    return action, phase, ap


def pose_of(boss):
    """(action, phase, ap) — pose yang SEDANG digambar badan."""
    G = _renderer()
    if G is None:
        return _fallback_pose(boss)
    try:
        return G._resolve_pose(
            boss, bool(getattr(boss, "_alch_moving", False)))
    except Exception:                          # pragma: no cover
        return _fallback_pose(boss)


def attack_phase_of(boss):
    """Nama fase serangan (ANTICIPATION..RECOVERY / NONE)."""
    return str(getattr(boss, "_alch_attack_phase", "NONE") or "NONE")


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
    """Skala rig -> piksel layar (SCALE renderer * normalisasi hero)."""
    G = _renderer()
    k = getattr(G, "SCALE", 1.0) if G is not None else 1.0
    return float(k) * render_scale(boss)


def _ground_dy(boss):
    """Jarak jangkar -> garis tanah (px layar)."""
    G = _renderer()
    if G is not None:
        try:
            return int(getattr(G, "GROUND_DY", 58))
        except Exception:                      # pragma: no cover
            pass
    return 58


def _rscale(boss):
    return render_scale(boss)


def cleaver_points(boss, x, y, back=False):
    """(grip, tip) cleaver dalam piksel layar (Vector2)."""
    G = _renderer()
    if G is not None:
        try:
            g = G._grip_screen(boss, x, y, back=back)
            t = G._tip_screen(boss, x, y, back=back)
            return Vector2(g), Vector2(t)
        except Exception:                      # pragma: no cover
            pass
    f = 1 if getattr(boss, "direction", 1) >= 0 else -1
    if back:
        return (Vector2(x - f * 22, y + 4),
                Vector2(x - f * 48, y + 14))
    return Vector2(x + f * 22, y + 4), Vector2(x + f * 46, y + 26)


def gun_end(boss, x, y):
    """Moncong acid gun goblin dalam piksel layar (Vector2)."""
    G = _renderer()
    if G is not None:
        try:
            return Vector2(G._gun_end_screen(boss, x, y))
        except Exception:                      # pragma: no cover
            pass
    f = 1 if getattr(boss, "direction", 1) >= 0 else -1
    return Vector2(x + f * 12, y - 46)


def bottle_hand(boss, x, y):
    """Tangan botol goblin (pose W) dalam piksel layar (Vector2)."""
    G = _renderer()
    if G is not None:
        try:
            return Vector2(G._bottle_hand_screen(boss, x, y))
        except Exception:                      # pragma: no cover
            pass
    f = 1 if getattr(boss, "direction", 1) >= 0 else -1
    return Vector2(x - f * 11, y - 74)


def target_screen(boss, x, y):
    """Posisi target (dunia) -> px layar pada jangkar unit."""
    # Renderer._target_position adalah konversi CANVAS: saat dipanggil di
    # jalur HERO dengan _render_scale, x/y masih koordinat DUNIA yang
    # dibagi skala -> titik mendarat molotov meleset. Gunakan jalurnya
    # hanya untuk boss (tanpa _render_scale); hero langsung 1:1.
    if getattr(boss, "_render_scale", None) is None:
        G = _renderer()
        if G is not None:
            try:
                return Vector2(G._target_position(boss, x, y))
            except Exception:                  # pragma: no cover
                pass
    tgt = getattr(boss, "target", None)
    f = 1 if getattr(boss, "direction", 1) >= 0 else -1
    if tgt is not None and getattr(tgt, "alive", False):
        # Lapisan hidup digambar di LAYAR 1:1; posisi target dunia sudah
        # merupakan koordinat layar. Jangan dikalikan / dibagi `_render_scale`
        # (itu hanya untuk konversi canvas renderer) — kalau dibagi skala,
        # titik mendarat molotov Q "nyasar" di luar target (FX terlihat
        # muncul acak di peta).
        return Vector2(x + (float(tgt.x) - float(getattr(boss, "x", x))),
                       y + (float(tgt.y) - float(getattr(boss, "y", y))))
    return Vector2(x + f * 150, y + 10)


# ============================================================================
# 3.  KUALITAS & PRIMITIF TER-CACHE
# ============================================================================

def _quality():
    """Faktor intensitas FX (preset kualitas x beban governor).

    Memakai ``Quality.particle_ratio`` (bukan ``Quality.quality``) supaya
    governor beban FX (set_fx_load / fx_load) ikut menurunkan partikel saat
    banyak hero live-FX bertarung, bukan hanya preset tinggi/sedang/rendah.
    """
    try:
        from mobile.perf import Quality as Q
        return float(getattr(Q, "particle_ratio", 1.0) or 1.0)
    except Exception:                          # pragma: no cover
        return 1.0


def particle_budget():
    """Anggaran partikel 0..1 (ikut preset kualitas)."""
    return max(0.15, min(1.0, _quality()))


def glow_allowed():
    """Additive glow diizinkan? (diperlambat di perangkat murah)."""
    try:
        from mobile.perf import Quality as Q
        return bool(getattr(Q, "use_additive_glow", True))
    except Exception:                          # pragma: no cover
        return True


def shake_allowed():
    """Guncangan layar diizinkan? (preset kualitas + setting game)."""
    try:
        from mobile.perf import Quality as Q
        return bool(getattr(Q, "shake_allowed", True))
    except Exception:                          # pragma: no cover
        return True


def _clamp_color(color):
    return tuple(max(0, min(255, int(c))) for c in color[:3])


def _mix(a, b, t):
    t = max(0.0, min(1.0, float(t)))
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def _hash01(seed):
    """Deterministik 0..1 dari seed int (tanpa state global random)."""
    h = (seed * 374761393 + 668265263) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFFFF) / 4294967295.0


_SURF_CACHE = {}
_SURF_ORDER = []
_SURF_CACHE_MAX = 96


def _cache_put(key, surf):
    _SURF_CACHE[key] = surf
    _SURF_ORDER.append(key)
    while len(_SURF_ORDER) > _SURF_CACHE_MAX:
        old = _SURF_ORDER.pop(0)
        _SURF_CACHE.pop(old, None)
    return surf


def clear_cache():
    """Kosongkan seluruh cache primitive (dipakai test / ganti tema)."""
    _SURF_CACHE.clear()
    del _SURF_ORDER[:]
    _FADE_CACHE.clear()
    del _FADE_ORDER[:]


def cache_size():
    return len(_SURF_CACHE)


def glow_surface(radius, color, power=1.0):
    """Lingkaran glow ber-gradien PREMULTIPLIED, ter-cache.

    ``BLEND_RGB_ADD`` MENGABAIKAN kanal alpha: gradien yang hanya menurun
    di alpha berubah jadi CAKRAM warna solid saat di-blit additive —
    penyebab Alchemist tertutup bola putih/kuning saat kena damage dan
    saat ultimate. Intensitas dikalikan ke RGB **dan** disalin ke alpha,
    jadi surface yang sama benar untuk blit normal maupun additive.
    """
    radius = max(2, int(radius))
    power = max(0.2, min(3.0, float(power)))
    key = ("glow", radius, _clamp_color(color), round(power, 2))
    surf = _SURF_CACHE.get(key)
    if surf is None:
        d = radius * 2
        surf = pygame.Surface((d, d), pygame.SRCALPHA)
        col = _clamp_color(color)
        steps = max(3, radius)
        for i in range(steps):
            t = i / float(steps)
            r = int(radius * (1.0 - t))
            k = (1.0 - t) ** power
            if k > 0.004 and r > 0:
                pygame.draw.circle(surf,
                                   (int(col[0] * k), int(col[1] * k),
                                    int(col[2] * k), min(255, int(255 * k))),
                                   (radius, radius), r)
        surf = _cache_put(key, surf)
    return surf


def spark_surface(size, color):
    """Bintang kilat 4-arah kecil (untuk impact), ter-cache."""
    size = max(3, int(size))
    key = ("spark", size, _clamp_color(color))
    surf = _SURF_CACHE.get(key)
    if surf is None:
        d = size * 2 + 2
        surf = pygame.Surface((d, d), pygame.SRCALPHA)
        c = size - 1
        col = _clamp_color(color)
        pygame.draw.line(surf, (*col, 255), (1, c), (d - 2, c), 1)
        pygame.draw.line(surf, (*col, 255), (c, 1), (c, d - 2), 1)
        pygame.draw.line(surf, (*col, 160),
                         (c - size // 2, c - size // 2),
                         (c + size // 2, c + size // 2), 1)
        pygame.draw.line(surf, (*col, 160),
                         (c - size // 2, c + size // 2),
                         (c + size // 2, c - size // 2), 1)
        surf = _cache_put(key, surf)
    return surf


def ring_surface(radius, thickness, color, alpha=255, dashed=0):
    """Cincin (opsional putus-putus), ter-cache."""
    radius = max(2, int(radius))
    thickness = max(1, int(thickness))
    key = ("ring", radius, thickness, _clamp_color(color),
           int(alpha), int(dashed))
    surf = _SURF_CACHE.get(key)
    if surf is None:
        d = (radius + thickness) * 2 + 2
        surf = pygame.Surface((d, d), pygame.SRCALPHA)
        c = radius + thickness
        col = (*_clamp_color(color), int(alpha))
        if dashed > 0:
            for i in range(int(dashed)):
                a0 = i * math.tau / dashed
                a1 = a0 + math.tau / dashed * 0.55
                p0 = (c + math.cos(a0) * radius,
                      c + math.sin(a0) * radius)
                p1 = (c + math.cos(a1) * radius,
                      c + math.sin(a1) * radius)
                pygame.draw.line(surf, col,
                                 (int(p0[0]), int(p0[1])),
                                 (int(p1[0]), int(p1[1])), thickness)
        else:
            pygame.draw.circle(surf, col, (c, c), radius, thickness)
        surf = _cache_put(key, surf)
    return surf


def ground_glow_surface(radius, color, power=0.35):
    """Glow elips tanah PREMULTIPLIED (falloff cepat), ter-cache.

    Alasan premultiply sama dengan `glow_surface`: alpha diabaikan oleh
    ``BLEND_RGB_ADD``, jadi intensitas harus masuk ke RGB supaya kabut
    tanah tidak jadi piringan terang yang menelan kaki Alchemist.
    """
    radius = max(3, int(radius))
    key = ("gglow", radius, _clamp_color(color), round(power, 2))
    surf = _SURF_CACHE.get(key)
    if surf is None:
        w = radius * 2
        h = radius
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        col = _clamp_color(color)
        steps = max(3, radius // 2)
        for i in range(steps):
            t = i / float(steps)
            rw = int(radius * (1.0 - t))
            rh = max(1, int(radius // 2 * (1.0 - t)))
            k = (1.0 - t) ** (1.0 / max(0.1, power))
            if k > 0.004:
                pygame.draw.ellipse(surf,
                                    (int(col[0] * k), int(col[1] * k),
                                     int(col[2] * k),
                                     min(255, int(255 * k))),
                                    (radius - rw, radius // 2 - rh,
                                     rw * 2, rh * 2))
        surf = _cache_put(key, surf)
    return surf


def _shard_poly(surface, cx, cy, ang, length, width, color, alpha=255,
                additive=False):
    """Pecahan poligon runcing menghadap ``ang`` (debris / slash)."""
    alpha = max(0, min(255, int(alpha)))
    if alpha <= 2 or length < 1:
        return
    ca, sa = math.cos(ang), math.sin(ang)
    px, py = -sa, ca
    pts = [(cx + ca * length, cy + sa * length),
           (cx + px * width, cy + py * width),
           (cx - ca * length * 0.4, cy - sa * length * 0.4),
           (cx - px * width, cy - py * width)]
    pts = [(int(p[0]), int(p[1])) for p in pts]
    col = (*_clamp_color(color), alpha)
    if additive:
        tmp = pygame.Surface((max(2, int(length * 2 + width * 2)),
                              max(2, int(length * 2 + width * 2))),
                             pygame.SRCALPHA)
        off = tmp.get_width() // 2
        pygame.draw.polygon(
            tmp, col,
            [(p[0] - cx + off, p[1] - cy + off) for p in pts])
        surface.blit(tmp, (int(cx - off), int(cy - off)),
                     special_flags=pygame.BLEND_RGBA_ADD)
    else:
        pygame.draw.polygon(surface, col, pts)


_FADE_CACHE = {}
_FADE_ORDER = []


def _fade_copy(surf, alpha):
    """Salinan surface dengan RGB *dan* alpha diredam (blit additive)."""
    a = max(1, min(255, int(alpha))) // 8 * 8 or 8
    key = (id(surf), surf.get_size(), a)
    hit = _FADE_CACHE.get(key)
    if hit is not None:
        return hit[1]
    cp = surf.copy()
    cp.fill((a, a, a, a), special_flags=pygame.BLEND_RGBA_MULT)
    _FADE_CACHE[key] = (surf, cp)          # tahan sumber: id() tetap unik
    _FADE_ORDER.append(key)
    while len(_FADE_ORDER) > 256:
        _FADE_CACHE.pop(_FADE_ORDER.pop(0), None)
    return cp


def _blit_faded(surface, surf, cx, cy, alpha=255, additive=False):
    """Blit surf di (cx, cy) dengan alpha/blend global murah."""
    if alpha <= 2:
        return
    x = int(cx - surf.get_width() / 2)
    y = int(cy - surf.get_height() / 2)
    if alpha >= 250 and not additive:
        surface.blit(surf, (x, y))
        return
    if additive:
        # RGB harus ikut diredam: BLEND_RGBA_ADD menambah kanal warna apa
        # adanya, jadi meredam alpha saja membuat glow yang "memudar"
        # tetap ditambahkan penuh dan menumpuk jadi bercak putih.
        a = max(1, min(255, int(alpha)))
        tmp = _fade_copy(surf, a)
        surface.blit(tmp, (x, y), special_flags=pygame.BLEND_RGBA_ADD)
        return
    # Non-additif: set_alpha langsung pada surface cache (tanpa copy).
    surf.set_alpha(int(alpha))
    surface.blit(surf, (x, y))
    surf.set_alpha(255)


# ============================================================================
# 4.  PARTICLE SYSTEM  (reusable: pool + burst + stream + cap)
# ============================================================================

class Particle:
    """Satu partikel penuh: position, velocity, acceleration, life,
    max_life, size, rotation, rotation_speed, alpha, gravity, color,
    drag, color_end, shape, layer — semuanya simulasi delta-time."""
    __slots__ = ("x", "y", "vx", "vy", "ax", "ay", "life", "max_life",
                 "size", "rot", "rot_speed", "alpha", "gravity",
                 "color", "color_end", "drag", "shape", "layer",
                 "additive", "fade_pow", "grow", "alive", "seed")

    SHAPES = ("dot", "ember", "streak", "dust", "smoke", "shard",
              "bubble", "drop", "coin", "spark")

    def __init__(self):
        self.reset()

    def reset(self):
        self.x = self.y = 0.0
        self.vx = self.vy = 0.0
        self.ax = self.ay = 0.0
        self.life = self.max_life = 0.25
        self.size = 2.0
        self.rot = 0.0
        self.rot_speed = 0.0
        self.alpha = 255
        self.gravity = 0.0
        self.color = P["acid_bright"]
        self.color_end = None
        self.drag = 0.0
        self.shape = "dot"
        self.layer = "front"
        self.additive = False
        self.fade_pow = 1.0
        self.grow = 0.0
        self.alive = False
        self.seed = 0

    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = self.max_life = max(0.02, float(life))
        self.size = max(0.5, float(size))
        self.color = _clamp_color(color)
        self.color_end = _clamp_color(kw["color_end"]) if \
            kw.get("color_end") else None
        self.ax = float(kw.get("ax", 0.0))
        self.ay = float(kw.get("ay", 0.0))
        self.rot = float(kw.get("rotation", 0.0))
        self.rot_speed = float(kw.get("rotation_speed", 0.0))
        self.alpha = max(0, min(255, int(kw.get("alpha", 255))))
        self.gravity = float(kw.get("gravity", 0.0))
        self.drag = float(kw.get("drag", 0.0))
        self.shape = kw.get("shape", "dot")
        if self.shape not in Particle.SHAPES:
            self.shape = "dot"
        self.layer = kw.get("layer", "front")
        self.additive = bool(kw.get("additive", False))
        self.fade_pow = float(kw.get("fade_pow", 1.0))
        self.grow = float(kw.get("grow", 0.0))
        self.alive = True
        self.seed = int(kw.get("seed", random.randint(0, 1 << 30)))

    @property
    def position(self):
        return Vector2(self.x, self.y)

    @property
    def velocity(self):
        return Vector2(self.vx, self.vy)

    @property
    def acceleration(self):
        return Vector2(self.ax, self.ay)

    def _fade(self):
        t = self.life / self.max_life                # 1 -> 0
        return max(0.0, t) ** self.fade_pow

    def update(self, dt):
        if not self.alive:
            return
        self.life -= dt
        if self.life <= 0.0:
            self.alive = False
            return
        # integrasi semi-implisit + drag eksponensial
        self.vy += (self.ay + self.gravity) * dt
        self.vx += self.ax * dt
        if self.drag > 0.0:
            k = max(0.0, 1.0 - self.drag * dt)
            self.vx *= k
            self.vy *= k
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.rot_speed:
            self.rot = (self.rot + self.rot_speed * dt) % math.tau
        if self.grow:
            self.size = max(0.5, self.size + self.grow * dt)

    def draw(self, surface):
        if not self.alive:
            return
        f = self._fade()
        a = int(self.alpha * f)
        if a <= 3:
            return
        col = self.color if self.color_end is None else \
            _mix(self.color_end, self.color, f)
        x, y = int(self.x), int(self.y)
        s = self.size
        shape = self.shape
        if shape == "dot":
            r = max(1, int(s))
            pygame.draw.circle(surface, (*col, a), (x, y), r)
        elif shape == "ember":
            r = max(1, int(s))
            if self.additive and glow_allowed():
                _blit_faded(surface, glow_surface(r + 2, col, 1.4),
                            x, y, a, additive=True)
            pygame.draw.circle(surface, (*col, a), (x, y), r)
            if s > 1.6:
                pygame.draw.circle(
                    surface, (*_mix(col, P["acid_white"], 0.6), a),
                    (x, y), max(1, r // 2))
        elif shape == "spark":
            _blit_faded(surface, spark_surface(max(2, int(s)), col),
                        x, y, a, additive=self.additive and glow_allowed())
        elif shape == "streak":
            ang = math.atan2(self.vy, self.vx) if \
                (self.vx or self.vy) else self.rot
            ln = max(2.0, s * 2.4)
            _shard_poly(surface, x, y, ang, ln, max(1.0, s * 0.55),
                        col, a)
        elif shape == "dust":
            r = max(1, int(s))
            pygame.draw.circle(surface, (*col, a // 2), (x, y), r)
            pygame.draw.circle(surface, (*col, a), (x, y),
                               max(1, r - 1))
        elif shape == "smoke":
            r = max(2, int(s))
            pygame.draw.circle(surface, (*col, int(a * 0.8)),
                               (x, y), r)
            pygame.draw.circle(
                surface, (*_mix(col, (0, 0, 0), 0.25), int(a * 0.6)),
                (x, y + r // 2), max(1, r // 2))
        elif shape == "shard":
            _shard_poly(surface, x, y, self.rot or math.pi / 4,
                        max(2.0, s * 1.8), max(1.0, s * 0.5), col, a)
        elif shape == "bubble":
            r = max(1, int(s))
            pygame.draw.circle(surface, (*col, a), (x, y), r, 1)
            pygame.draw.circle(surface, (*col, a // 3),
                               (x, y), max(1, r - 1))
            if r > 1:
                pygame.draw.circle(
                    surface, (*P["acid_glow"], a), (x - r // 2,
                                                    y - r // 2), 1)
        elif shape == "drop":
            # tetes asam: segitiga arah gerak + badan bulat
            ang = math.atan2(self.vy, self.vx) if \
                (self.vx or self.vy) else math.pi / 2
            r = max(1, int(s))
            _shard_poly(surface, x, y, ang, r + 2, max(1, r * 0.7),
                        col, a)
            pygame.draw.circle(surface, (*col, a), (x, y), r)
        elif shape == "coin":
            r = max(1, int(s))
            w = max(1, int(abs(math.cos(self.rot)) * r) + 1)
            pygame.draw.ellipse(surface, (*P["gold_dark"], a),
                                (x - w - 1, y - r, w * 2 + 2, r * 2))
            pygame.draw.ellipse(surface, (*col, a),
                                (x - w, y - r + 1, w * 2, r * 2 - 2))
            if w > 1:
                pygame.draw.circle(
                    surface, (*P["gold_shine"], a),
                    (x - w // 2, y - r // 2), 1)


class ParticleSystem:
    """Pool partikel dengan batas keras + burst + stream."""

    def __init__(self, cap=MAX_PARTICLES):
        self.cap = int(cap)
        self._pool = [Particle() for _ in range(min(64, self.cap))]
        self._active = []

    def _acquire(self):
        if self._active and len(self._active) >= self.cap:
            return None
        if self._pool:
            p = self._pool.pop()
        else:
            p = Particle()
        self._active.append(p)
        return p

    def count(self):
        return len(self._active)

    def alive(self):
        return bool(self._active)

    def clear(self):
        for p in self._active:
            p.reset()
            self._pool.append(p)
        self._active = []

    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        p = self._acquire()
        if p is None:
            return None
        p.spawn(x, y, vx, vy, life, size, color, **kw)
        return p

    def burst(self, x, y, count, speed=(60.0, 210.0),
              life=(0.22, 0.55), size=(1, 3), colors=None,
              spread=math.tau, direction=0.0, gravity=0.0, drag=0.0,
              shape="dot", additive=False, layer="front",
              rotation_speed=None, color_end=None, fade_pow=1.0):
        """Ledakan partikel ke segala arah / kerucut arah."""
        count = int(count)
        if count <= 0 or not colors:
            return
        budget = particle_budget()
        count = int(count * budget) if budget < 1.0 else count
        for _ in range(count):
            ang = direction + (random.random() - 0.5) * spread
            spd = random.uniform(*speed)
            sz = random.uniform(*size)
            lf = random.uniform(*life)
            kw = dict(gravity=gravity, drag=drag, shape=shape,
                      additive=additive, layer=layer, fade_pow=fade_pow,
                      rotation=random.uniform(0.0, math.tau))
            if rotation_speed is not None:
                kw["rotation_speed"] = random.uniform(*rotation_speed)
            if color_end is not None:
                kw["color_end"] = color_end
            self.spawn(x, y,
                       math.cos(ang) * spd, math.sin(ang) * spd,
                       lf, sz, random.choice(colors), **kw)

    def stream(self, x, y, tx, ty, count, life=(0.3, 0.6),
               size=(1, 3), colors=None, layer="front",
               additive=False, shape="dot", color_end=None):
        """Partikel tersedot dari (x, y) menuju (tx, ty) (charge FX)."""
        count = int(count)
        if count <= 0 or not colors:
            return
        budget = particle_budget()
        count = int(count * budget) if budget < 1.0 else count
        for _ in range(count):
            px = x + random.uniform(-14, 14)
            py = y + random.uniform(-10, 10)
            lf = random.uniform(*life)
            kw = dict(shape=shape, additive=additive, layer=layer)
            if color_end is not None:
                kw["color_end"] = color_end
            self.spawn(px, py,
                       (tx - px) / lf * 0.9, (ty - py) / lf * 0.9,
                       lf, random.uniform(*size),
                       random.choice(colors), **kw)

    def update(self, dt):
        if not self._active:
            return
        alive = []
        for p in self._active:
            p.update(dt)
            if p.alive:
                alive.append(p)
            else:
                p.reset()
                self._pool.append(p)
        self._active = alive

    def draw(self, surface, layer="front"):
        for p in self._active:
            if p.layer == layer:
                p.draw(surface)


# ============================================================================
# 5.  SWING TRAIL  (histori posisi bilah -> pita busur memudar)
# ============================================================================

class SwingTrail:
    """Trail senjata prosedural dari histori grip/tip cleaver.

    Menyimpan TRAIL_SAMPLES posisi (grip, tip) terakhir; pita
    digambar sebagai poligon translusen berlapis (edge / core / tip)
    yang melebar mengikuti kecepatan bilah lalu memudar — selalu
    mengikuti ARAH ayunan, bukan dua pose snap.
    """

    def __init__(self, samples=TRAIL_SAMPLES):
        self.samples = []                 # [(gx, gy, tx, ty, age)]
        self.max_samples = int(samples)
        self.width_boost = 1.0
        self.age = 0.0

    def reset(self):
        self.samples = []

    def push(self, grip, tip):
        self.samples.append((float(grip[0]), float(grip[1]),
                             float(tip[0]), float(tip[1]), 0.0))
        while len(self.samples) > self.max_samples:
            self.samples.pop(0)

    def update(self, dt):
        self.age += dt
        for i, s in enumerate(self.samples):
            self.samples[i] = (s[0], s[1], s[2], s[3],
                               s[4] + dt)
        # sample mati kalau terlalu tua (anti daftar abadi)
        max_age = 0.16
        self.samples = [s for s in self.samples if s[4] <= max_age]

    @staticmethod
    def _ang_delta(a_new, a_old):
        d = (a_new - a_old) % math.tau
        return d if d <= math.pi else d - math.tau

    def _ribbon(self, surface, lst, edge, core, tip_col, base_alpha,
                width_scale):
        n = len(lst)
        if n < 2:
            return
        # kecepatan sudut rata-rata -> lebar pita
        angs = [math.atan2(s[3] - s[1], s[2] - s[0]) for s in lst]
        speed = 0.0
        for i in range(1, n):
            speed += abs(SwingTrail._ang_delta(angs[i], angs[i - 1]))
        speed /= max(1, n - 1)
        width = max(1.5, min(7.0, 1.5 + speed * 22.0)) * width_scale
        for i in range(1, n):
            s0, s1 = lst[i - 1], lst[i]
            t = i / float(n - 1)              # 0 tua -> 1 baru
            a = int(base_alpha * t ** 1.4)
            if a <= 4:
                continue
            for k, (col, wmul) in enumerate(((edge, 1.0),
                                             (core, 0.62),
                                             (tip_col, 0.30))):
                wa = int(a * (1.0, 0.85, 0.7)[k])
                if wa <= 4:
                    continue
                w = max(1.0, width * wmul * (0.35 + 0.65 * t))
                # perp arah bilah tiap ujung
                a0 = math.atan2(s0[3] - s0[1], s0[2] - s0[0])
                a1 = math.atan2(s1[3] - s1[1], s1[2] - s1[0])
                p0 = (s0[2] - math.sin(a0) * w,
                      s0[3] + math.cos(a0) * w)
                p1 = (s1[2] - math.sin(a1) * w,
                      s1[3] + math.cos(a1) * w)
                p2 = (s1[2] + math.sin(a1) * w,
                      s1[3] - math.cos(a1) * w)
                p3 = (s0[2] + math.sin(a0) * w,
                      s0[3] - math.cos(a0) * w)
                pts = [(int(p[0]), int(p[1]))
                       for p in (p0, p1, p2, p3)]
                pygame.draw.polygon(surface, (*col, wa), pts)

    def draw(self, surface):
        if len(self.samples) < 2 or not glow_allowed():
            return
        wb = self.width_boost
        self._ribbon(surface, self.samples,
                     P["acid_dark"], P["acid_bright"], P["acid_hot"],
                     150, wb)


# ============================================================================
# 6.  IMPACT FX  (hit flash + shockwave + debris + slash fragment)
# ============================================================================

class ImpactFX:
    """Satu benturan: bintang kilat, cincin kejut, serpihan, debu.

    kind: slash (cleaver), acid (droplet), conc (botol W), rage,
    greed (ultimate), hurt (unit kena pukul), dash.
    """
    TOTAL = {"slash": 0.34, "acid": 0.36, "conc": 0.52,
             "rage": 0.55, "greed": 0.85, "hurt": 0.28,
             "dash": 0.38}
    TINT = {
        "slash": (P["acid_hot"], P["acid_white"]),
        "acid":  (P["acid_bright"], P["acid_glow"]),
        "conc":  (P["acid_mid"], P["acid_hot"]),
        "rage":  (P["acid_hot"], P["acid_white"]),
        "greed": (P["gold_mid"], P["gold_shine"]),
        "hurt":  (P["blue"], P["blue_hot"]),
        "dash":  (P["acid_mid"], P["acid_bright"]),
    }

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="slash", ground=0.0, seed=0):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = max(0.2, min(2.5, float(power)))
        self.crit = bool(crit)
        self.kind = kind if kind in self.TOTAL else "slash"
        self.ground = float(ground)
        self.seed = int(seed) or random.randint(0, 999999)
        self.age = 0.0
        self.total = self.TOTAL[self.kind] * (1.0 + 0.22 *
                                              (self.power - 1.0))
        self.active = True

    def _ramp(self):
        return max(0.0, 1.0 - self.age / self.total)

    def update(self, dt):
        self.age += dt
        if self.age >= self.total:
            self.active = False
            return False
        return True

    def draw(self, surface):
        if not self.active:
            return
        t = self._ramp()
        inv = 1.0 - t
        hot, white = self.TINT[self.kind]
        pw = self.power
        x, y = int(self.x), int(self.y)
        ang = self.angle

        # flash inti + bintang kilat (kiri: cepat menyusut)
        if t > 0.55:
            fs = (1.0 - inv / 0.45)
            core_r = max(2, int((4 + 7 * pw) * (1.0 - fs)))
            if glow_allowed():
                _blit_faded(surface, glow_surface(core_r + 4, white),
                            x, y, int(220 * t), additive=True)
            pygame.draw.circle(surface, (*white, int(235 * t)),
                               (x, y), max(1, core_r // 2))
            star = spark_surface(max(4, int(6 + 8 * pw)), white)
            _blit_faded(surface, star, x, y, int(250 * t),
                        additive=True)
            if self.crit:
                star2 = spark_surface(max(6, int(10 + 10 * pw)), hot)
                _blit_faded(surface, star2, x, y,
                            int(200 * t), additive=True)

        # cincin kejut mengembang
        rr = int(4 + inv * (18 + 34 * pw))
        ra = int(200 * t)
        if ra > 6:
            _blit_faded(surface,
                        ring_surface(rr, 2, hot, min(255, ra)),
                        x, y)
        # fragment slash (kiri arah serangan)
        if self.kind in ("slash", "conc", "greed") and t > 0.3:
            frag = max(2, int(3 + 4 * pw))
            for i in range(frag):
                h1 = _hash01(self.seed + i * 7)
                h2 = _hash01(self.seed + i * 13 + 5)
                fa = ang + (h1 - 0.5) * 1.9
                fr = 6 + h2 * (16 + 20 * pw)
                fx = self.x + math.cos(fa) * fr
                fy = self.y + math.sin(fa) * fr
                _shard_poly(surface, int(fx), int(fy), fa,
                            3 + h1 * (5 + 5 * pw), 1.6,
                            hot, int(190 * t), additive=False)

        # shockwave tanah (elips pipih di garis tanah)
        if self.ground and t > 0.25:
            gw = int(6 + inv * (26 + 40 * pw))
            gh = max(2, gw // 3)
            ga = int(140 * t)
            if ga > 6:
                pygame.draw.ellipse(
                    surface, (*hot, ga),
                    (x - gw, int(self.y + self.ground * 0.5) - gh,
                     gw * 2, gh * 2), 2)
        # percikan dekoratif deterministik (crit lebih ramai)
        n = (7 if not self.crit else 12)
        for i in range(n):
            h1 = _hash01(self.seed * 3 + i * 31)
            h2 = _hash01(self.seed * 5 + i * 17 + 3)
            sa = ang + (h1 - 0.5) * 2.6
            sr = inv * (10 + h2 * (26 + 26 * pw))
            sx = int(self.x + math.cos(sa) * sr)
            sy = int(self.y + math.sin(sa) * sr * 0.8)
            col = white if h2 > 0.6 else hot
            pygame.draw.circle(surface, (*col, int(170 * t)),
                               (sx, sy), 1)


# ============================================================================
# 7.  PROJECTILE SYSTEM  (modular, delta-time, lifecycle penuh)
# ============================================================================

class AlchemistProjectile:
    """Proyektil modular: botol asam (busur + sumbu), droplet spray,
    dan koin visual.

    Lifecycle: SPAWN -> TRAVEL (+TRAIL) -> HIT -> IMPACT FX -> DESTROY.
    Bidang lengkap: position, velocity, speed, damage, lifetime,
    target, radius (hit), rotation, trail, particles, active.
    """
    __slots__ = ("x", "y", "vx", "vy", "speed", "damage", "lifetime",
                 "target", "radius", "hit_radius", "rotation",
                 "rot_speed", "trail", "particles", "active", "kind",
                 "tx", "ty", "sx", "sy", "arc_height", "age", "alive",
                 "_hit_pos", "on_impact", "spin", "ground", "flight")

    def __init__(self, x, y, tx, ty, speed=BOTTLE_SPEED, damage=0,
                 target=None, radius=7.0, kind="bottle",
                 arc_height=BOTTLE_ARC, lifetime=2.4, ground=0.0,
                 on_impact=None, rot_speed=7.0):
        # SPAWN
        self.x = float(x)
        self.y = float(y)
        self.sx, self.sy = float(x), float(y)
        self.tx, self.ty = float(tx), float(ty)
        self.speed = float(speed)
        self.damage = float(damage)
        self.target = target
        self.radius = float(radius)
        self.hit_radius = float(radius)
        self.kind = kind
        self.arc_height = float(arc_height)
        self.lifetime = max(0.05, float(lifetime))
        self.ground = float(ground)
        self.on_impact = on_impact
        self.age = 0.0
        self.alive = True
        self.active = True
        self.rotation = 0.0
        self.rot_speed = float(rot_speed)
        self.spin = random.uniform(0.0, math.tau)
        self.trail = []
        self.particles = True
        self._hit_pos = Vector2(x, y)
        # kecepatan awal (TRAVEL lurus untuk droplet; busur dihitung
        # parametrik untuk botol supaya mendarat TEPAT di target)
        dx, dy = self.tx - self.x, self.ty - self.y
        dist = max(1.0, math.hypot(dx, dy))
        self.vx = dx / dist * self.speed
        self.vy = dy / dist * self.speed
        if kind == "bottle":
            self.flight = max(0.12, dist / max(1.0, self.speed))
        else:
            self.flight = max(0.05, dist / max(1.0, self.speed))

    # ------------------------------------------------------------------
    def kill(self, x=None, y=None):
        """HIT + IMPACT FX + DESTROY (dipanggil sistem / gameplay)."""
        if not self.alive:
            return
        self.alive = False
        hx = self.x if x is None else float(x)
        hy = self.y if y is None else float(y)
        self._hit_pos = Vector2(hx, hy)
        self.x, self.y = hx, hy
        if self.on_impact is not None:
            try:
                self.on_impact(self)
            except Exception:
                pass

    # ------------------------------------------------------------------
    def update(self, dt, particles=None):
        """TRAVEL + TRAIL; return False saat DESTROY."""
        if not self.alive:
            return False
        self.age += dt
        if self.kind == "bottle":
            # busur parametrik: selalu mendarat persis di target
            t = min(1.0, self.age / self.flight)
            self.x = self.sx + (self.tx - self.sx) * t
            arc = -4.0 * self.arc_height * t * (1.0 - t)
            self.y = self.sy + (self.ty - self.sy) * t + arc
            self.rotation += self.rot_speed * dt
            if particles is not None and self.particles:
                if random.random() < 0.55:
                    particles.spawn(
                        self.x, self.y,
                        random.uniform(-16, 16), random.uniform(-8, 26),
                        random.uniform(0.16, 0.34),
                        random.uniform(1.0, 2.4),
                        random.choice((P["acid_bright"], P["acid_hot"],
                                       P["acid_glow"])),
                        gravity=210.0, drag=1.4, shape="drop",
                        additive=False, layer="front")
            self.trail.append((self.x, self.y))
            if len(self.trail) > 9:
                self.trail.pop(0)
            if t >= 1.0:
                self.kill(self.tx, self.ty)
                return False
        else:
            # droplet / coin: balistik penuh
            self.vy += (340.0 if self.kind == "droplet"
                        else 520.0) * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.rotation += self.rot_speed * dt
            if self.kind == "coin":
                self.rot_speed *= (1.0 - 0.6 * dt)
            self.trail.append((self.x, self.y))
            if len(self.trail) > 5:
                self.trail.pop(0)
        # umur maksimum (anti proyektil abadi)
        if self.age >= self.lifetime:
            self.kill()
            return False
        return True

    # ------------------------------------------------------------------
    def _draw_bottle(self, surface, x, y):
        """Botol ramuan berputar: body + cork + asam menyala + glow."""
        ang = self.rotation
        ca, sa = math.cos(ang), math.sin(ang)
        px, py = -sa, ca
        bh, bw = 8, 5
        pts = [(x + ca * d + px * w, y + sa * d + py * w)
               for d, w in ((bh, bw), (bh, -bw), (-bh, -bw),
                            (-bh, bw))]
        pts = [(int(p[0]), int(p[1])) for p in pts]
        pygame.draw.polygon(surface, (*P["shadow"], 190),
                            [(p[0] + 1, p[1] + 1) for p in pts])
        pygame.draw.polygon(surface, P["acid_darkest"], pts)
        inner = [(x + ca * (bh - 1) + px * (bw - 1),
                  y + sa * (bh - 1) + py * (bw - 1)),
                 (x + ca * (bh - 1) - px * (bw - 1),
                  y + sa * (bh - 1) - py * (bw - 1)),
                 (x - ca * (bh - 1) - px * (bw - 2),
                  y - sa * (bh - 1) - py * (bw - 2)),
                 (x - ca * (bh - 1) + px * (bw - 2),
                  y - sa * (bh - 1) + py * (bw - 2))]
        pygame.draw.polygon(surface, P["acid_mid"],
                            [(int(p[0]), int(p[1])) for p in inner])
        cork = (int(x + ca * (bh + 3)), int(y + sa * (bh + 3)))
        pygame.draw.circle(surface, P["leather_dark"], cork, 3)
        pygame.draw.circle(surface, P["leather"], cork, 2)
        pygame.draw.circle(surface, P["acid_bright"], (int(x), int(y)),
                           3)
        pygame.draw.circle(surface, P["acid_hot"], (int(x), int(y)), 2)
        pygame.draw.circle(surface, P["acid_glow"],
                           (int(x) - 1, int(y) - 1), 1)
        # sumbu berpijar (bom tidak stabil)
        fuse = (int(x - ca * (bh + 5)), int(y - sa * (bh + 5)))
        fl = 0.5 + 0.5 * math.sin(self.spin + self.age * 22.0)
        pygame.draw.circle(surface,
                           (*P["acid_white"], int(160 + 90 * fl)),
                           fuse, 2)
        if glow_allowed():
            _blit_faded(surface, glow_surface(10, P["acid_bright"]),
                        x, y, int(120 + 70 * fl), additive=True)
        # coretan sumbu
        pygame.draw.line(surface, (*P["gold_light"], 190),
                         (int(x - ca * (bh + 3)), int(y - sa * (bh + 3))),
                         fuse, 1)

    def draw(self, surface):
        """TRAIL + badan proyektil (core / glow / bentuk arah)."""
        if not self.alive:
            return
        # trail memudar
        n = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            t = i / float(max(1, n - 1))
            if self.kind == "bottle":
                r = max(1, int(1 + t * 3))
                pygame.draw.circle(
                    surface, (*P["acid_bright"], int(60 + t * 90)),
                    (int(tx), int(ty)), r)
            elif self.kind == "coin":
                r = max(1, int(1 + t * 2))
                pygame.draw.circle(
                    surface, (*P["gold_mid"], int(50 + t * 70)),
                    (int(tx), int(ty)), r)
        x, y = int(self.x), int(self.y)
        if self.kind == "bottle":
            self._draw_bottle(surface, x, y)
        elif self.kind == "droplet":
            ang = math.atan2(self.vy, self.vx)
            _shard_poly(surface, x, y, ang, 4, 2, P["acid_hot"], 220)
            pygame.draw.circle(surface, P["acid_bright"], (x, y), 2)
            pygame.draw.circle(surface, P["acid_glow"], (x, y), 1)
        elif self.kind == "coin":
            r = 3
            w = max(1, int(abs(math.cos(self.rotation)) * r) + 1)
            pygame.draw.ellipse(surface, P["gold_dark"],
                                (x - w - 1, y - r, w * 2 + 2, r * 2))
            pygame.draw.ellipse(surface, P["gold_light"],
                                (x - w, y - r + 1, w * 2, r * 2 - 2))

    def draw_impact(self, surface):
        """IMPACT FX singkat tepat setelah destroy (sketsa cipratan)."""
        if self.alive:
            return
        x, y = int(self._hit_pos.x), int(self._hit_pos.y)
        pygame.draw.circle(surface, (*P["acid_white"], 140),
                           (x, y), 5)
        pygame.draw.circle(surface, (*P["acid_hot"], 120),
                           (x, y), 8)


class ProjectileSystem:
    """Manajer proyektil: spawn / update / draw / cap."""

    def __init__(self, particles=None, cap=MAX_PROJECTILES):
        self.particles = particles
        self.cap = int(cap)
        self._list = []

    def count(self):
        return len(self._list)

    def list(self):
        return list(self._list)

    def clear(self):
        self._list = []

    def spawn(self, x, y, tx, ty, **kw):
        if len(self._list) >= self.cap:
            self._list.pop(0)
        pr = AlchemistProjectile(x, y, tx, ty, **kw)
        self._list.append(pr)
        return pr

    def update(self, dt):
        if not self._list:
            return
        alive = []
        for pr in self._list:
            ok = pr.update(dt, self.particles)
            if ok:
                alive.append(pr)
            else:
                # DESTROY: cipratan singkat lewat partikel
                if self.particles is not None and pr.particles:
                    self._landing_burst(pr)
        self._list = alive

    def _landing_burst(self, pr):
        ps = self.particles
        if pr.kind == "bottle":
            ps.burst(pr.x, pr.y, 14,
                     speed=(70, 300), life=(0.2, 0.5), size=(2, 4),
                     colors=(P["acid_white"], P["acid_hot"],
                             P["acid_bright"]),
                     spread=math.tau, gravity=380.0, drag=1.2,
                     shape="drop")
            ps.burst(pr.x, pr.y, 8,
                     speed=(30, 110), life=(0.4, 0.8), size=(3, 7),
                     colors=(P["smoke"], P["ash"]),
                     spread=math.tau, gravity=-46.0, drag=1.6,
                     shape="smoke", layer="back")
        elif pr.kind == "droplet":
            ps.burst(pr.x, pr.y, 5,
                     speed=(30, 130), life=(0.14, 0.3), size=(1, 2),
                     colors=(P["acid_bright"], P["acid_hot"]),
                     spread=math.tau, gravity=260.0, drag=1.4,
                     shape="drop")
        elif pr.kind == "coin":
            ps.burst(pr.x, pr.y, 3,
                     speed=(20, 80), life=(0.2, 0.4), size=(1, 2),
                     colors=(P["gold_light"], P["gold_shine"]),
                     spread=math.tau, gravity=300.0, drag=1.0,
                     shape="spark", additive=True)

    def draw(self, surface):
        for pr in self._list:
            pr.draw(surface)


# ============================================================================
# 8.  SKILL FX  (lifecycle CAST->CHARGE->RELEASE->AREA->IMPACT->FADE)
# ============================================================================

class SkillFX:
    """Efek skill Alchemist dengan lifecycle bertahap.

    Q Acid Spray       — cone droplet + genangan di target
    W Unstable Conc.   — ledakan AOE + gelombang cincin di target
    E Chemical Rage    — denyut buff di badan + uap naik
    R Greevil's Greed  — badai koin + lingkaran emas radius 200

    Yang digambar di sini bagian yang TIDAK boleh ikut ter-cache;
    telegraph geometris tetap milik renderer (tidak ada bentuk ganda).
    """

    #: (charge, release, area, impact, after) dalam DETIK
    TIMELINE = {
        "q": (0.14, 0.10, 0.30, 0.12, 0.34),
        "w": (0.20, 0.12, 0.34, 0.16, 0.44),
        "e": (0.16, 0.12, 0.34, 0.14, 0.36),
        "r": (0.34, 0.20, 0.56, 0.26, 0.66),
    }

    TINT = {
        "q": (P["acid_dark"], P["acid_hot"]),
        "w": (P["acid_dark"], P["acid_bright"]),
        "e": (P["acid_mid"], P["acid_hot"]),
        "r": (P["gold_dark"], P["gold_light"]),
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

    @property
    def aim_angle(self):
        ax, ay = self.aim
        if abs(ax) < 0.01 and abs(ay) < 0.01:
            return 0.0
        return math.atan2(ay, ax)

    def impacted(self, x=None, y=None):
        """Tandai IMPACT (dipanggil gameplay / watcher timer)."""
        if x is not None and y is not None:
            self.x = float(x)
            self.y = float(y)
        self._impacted = True
        if self.age > self.t_impact:
            self.age = self.t_impact

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
        R = self.radius * self.scale
        ang = self.aim_angle
        dark, hot = self.TINT[kind]

        # CHARGE: energi tersedot ke titik lepas (bukan orbit kosong)
        if self.phase == "charge":
            self._emit += dt
            gap = 0.05 if kind != "r" else 0.03
            while self._emit >= gap:
                self._emit -= gap
                a = random.random() * math.tau
                rr = R * random.uniform(0.4, 0.9)
                sx = self.x + math.cos(a) * rr
                sy = self.y + math.sin(a) * rr * 0.5 + \
                    self.ground * 0.5
                life = random.uniform(0.2, 0.4)
                ps.spawn(sx, sy,
                         (self.x - sx) / life * 0.8,
                         (self.y + self.ground * 0.3 - sy) / life * 0.7,
                         life, random.uniform(1.5, 3.0),
                         hot if kind != "r" else P["gold_light"],
                         color_end=dark, drag=0.4,
                         shape="ember", additive=True, fade_pow=0.8,
                         layer="back")

        # RELEASE: semburan sekali ke arah aim / ke segala arah
        elif self.phase == "release" and not self._released:
            self._released = True
            if kind == "q":
                ps.burst(self.x, self.y, 12,
                         speed=(120, 330), life=(0.16, 0.36),
                         size=(2, 4),
                         colors=(P["acid_white"], hot,
                                 P["acid_glow"]),
                         spread=1.1, direction=ang, drag=3.2,
                         shape="drop", additive=True)
            elif kind == "w":
                ps.burst(self.x, self.y, 14,
                         speed=(90, 260), life=(0.2, 0.42),
                         size=(2, 4),
                         colors=(P["acid_white"], hot,
                                 P["acid_bright"]),
                         spread=math.tau, drag=2.6, shape="drop")
            elif kind == "e":
                ps.burst(self.x, self.y + self.ground * 0.4, 12,
                         speed=(80, 220), life=(0.24, 0.5),
                         size=(2, 5),
                         colors=(hot, P["acid_bright"], P["vapor"]),
                         spread=math.tau, gravity=-160.0, drag=1.8,
                         shape="smoke", layer="back")
            else:
                ps.burst(self.x, self.y, 18,
                         speed=(140, 400), life=(0.2, 0.55),
                         size=(2, 4),
                         colors=(P["gold_shine"], P["gold_light"],
                                 P["gold_mid"]),
                         spread=math.tau, gravity=340.0, drag=1.0,
                         shape="coin", layer="front")

        # AREA: emisi berkelanjutan sesuai kepribadian skill
        elif self.phase in ("area", "impact"):
            self._emit += dt
            gap = {"q": 0.04, "w": 0.05, "e": 0.04, "r": 0.03}[kind]
            while self._emit >= gap:
                self._emit -= gap
                a = random.random() * math.tau
                rr = R * random.uniform(0.15, 0.95)
                sx = self.x + math.cos(a) * rr
                sy = self.y + math.sin(a) * rr * 0.55 + \
                    self.ground * 0.4
                if kind in ("q", "w"):
                    ps.spawn(sx, sy, 0.0, random.uniform(-30, -12),
                             random.uniform(0.3, 0.7),
                             random.uniform(2, 4), P["acid_mid"],
                             color_end=P["acid_dark"], shape="bubble",
                             layer="back")
                elif kind == "e":
                    ps.spawn(sx, sy,
                             random.uniform(-14, 14),
                             random.uniform(-90, -40),
                             random.uniform(0.3, 0.6),
                             random.uniform(2, 4), P["vapor"],
                             color_end=P["smoke"], shape="smoke",
                             layer="back")
                else:
                    ps.spawn(sx, sy - self.ground * 0.4,
                             random.uniform(-40, 40),
                             random.uniform(-190, -90),
                             random.uniform(0.4, 0.8),
                             random.uniform(2, 3), P["gold_light"],
                             gravity=420.0, shape="coin",
                             rotation_speed=random.uniform(-9.0, 9.0))
        return True

    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        """GROUND FX: genangan / zona / cincin — di bawah sprite."""
        if not self.active:
            return
        t = self.age / self.total
        R = self.radius * self.scale
        gy = self.y + self.ground * 0.55
        if self.kind == "q":
            if self.phase in ("area", "impact", "fade"):
                a = int(150 * (1.0 - max(0.0, t - 0.55) / 0.45))
                if a > 6:
                    _blit_faded(surface,
                                ground_glow_surface(
                                    int(R * 0.6), P["acid_mid"], 0.4),
                                self.x, gy, a)
        elif self.kind == "w":
            if self.phase in ("impact", "fade"):
                a = int(190 * (1.0 - max(0.0, t - 0.6) / 0.4))
                if a > 6:
                    _blit_faded(surface,
                                ground_glow_surface(
                                    int(R * 0.8), P["acid_bright"], 0.5),
                                self.x, gy, a)
                    _blit_faded(surface,
                                ring_surface(int(R), 2,
                                             P["acid_hot"], a),
                                self.x, gy)
        elif self.kind == "e":
            if self.phase not in ("cast", "charge"):
                pul = 0.5 + 0.5 * math.sin(self.age * 9.0)
                a = int(120 * (1.0 - t) * (0.6 + 0.4 * pul))
                if a > 6:
                    _blit_faded(surface,
                                ground_glow_surface(
                                    int(R * 0.5), P["acid_hot"], 0.4),
                                self.x, gy, a)
        elif self.kind == "r":
            if self.phase in ("area", "impact", "fade"):
                a = int(160 * (1.0 - max(0.0, t - 0.5) / 0.5))
                if a > 6:
                    _blit_faded(surface,
                                ground_glow_surface(
                                    int(R * 0.55), P["gold_mid"], 0.5),
                                self.x, gy, a)
                    _blit_faded(surface,
                                ring_surface(int(R), 3,
                                             P["gold_light"], a),
                                self.x, gy)

    def draw_front(self, surface):
        """FRONT FX: cone Q / shockwave W / uap E / badai koin R."""
        if not self.active:
            return
        t = self.age / self.total
        inv = 1.0 - t
        R = self.radius * self.scale
        ang = self.aim_angle
        dark, hot = self.TINT[self.kind]
        x, y = int(self.x), int(self.y)

        if self.kind == "q":
            # kerucut semburan: garis droplet memudar
            if self.phase in ("release", "area"):
                reach = R * min(1.0, (self.age - self.t_charge) /
                                max(0.01, self.t_area - self.t_charge))
                for i in range(10):
                    tt = i / 9.0
                    d = reach * tt
                    w = 3 + tt * (R * 0.26)
                    px = int(self.x + math.cos(ang) * d +
                             math.sin(ang) * w * 0.3)
                    py = int(self.y + math.sin(ang) * d -
                             math.cos(ang) * w * 0.3)
                    a = int(190 * (1.0 - tt * 0.5) *
                            (1.0 if self.phase == "area" else 0.7))
                    pygame.draw.circle(
                        surface, (*P["acid_bright"], a), (px, py),
                        max(1, int(2 + tt * 3)))
        elif self.kind == "w":
            if self.phase in ("impact", "fade"):
                rr = int(R * (0.3 + 0.7 * (1.0 - inv)))
                a = int(210 * inv)
                if a > 6:
                    _blit_faded(surface,
                                ring_surface(rr, 3, P["acid_hot"], a),
                                x, y)
                    _blit_faded(surface,
                                ring_surface(max(3, rr - 8), 2,
                                             P["acid_glow"], a // 2),
                                x, y)
        elif self.kind == "e":
            if self.phase in ("release", "area"):
                pul = 0.5 + 0.5 * math.sin(self.age * 11.0)
                for k in range(3):
                    rr = int(10 + k * 9 + pul * 5)
                    a = int(150 * inv * (1.0 - k * 0.25))
                    if a > 6:
                        _blit_faded(surface,
                                    ring_surface(rr, 2, P["acid_hot"],
                                                 a),
                                    x, y - 6)
        elif self.kind == "r":
            if self.phase in ("release", "area", "impact"):
                pul = 0.5 + 0.5 * math.sin(self.age * 8.0)
                a = int(200 * (0.5 + 0.5 * pul) *
                        max(0.0, 1.0 - t * 0.7))
                if a > 6:
                    _blit_faded(surface,
                                glow_surface(int(16 + 10 * pul),
                                             P["gold_shine"]),
                                x, y - 8, a, additive=glow_allowed())
                # kilau bintang
                _blit_faded(surface,
                            spark_surface(9, P["gold_shine"]),
                            x, y - 8, int(160 * pul),
                            additive=glow_allowed())


# ============================================================================
# 9.  DIRECTOR  (satu instance per unit — mengikat semua sistem)
# ============================================================================

class AlchemistFXDirector:
    """Mengikat particle + trail + proyektil + impact + skill FX untuk
    satu unit Alchemist (true boss / hero lane memakai kode yang sama).

    Lapisan ini SATU ARAH: hanya MEMBACA field yang sudah ditulis
    engine (active_skill, active_skill_timer, w_target_*, rage_active,
    _alch_attack_phase, hp, x/y) — tidak pernah mengubah gameplay.
    """

    def __init__(self, hero):
        self.hero = hero
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.projectiles = ProjectileSystem(self.particles,
                                            MAX_PROJECTILES)
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
        self._rage_emit = 0.0

    # ------------------------------------------------------------------
    # util
    # ------------------------------------------------------------------
    def _ground_dy(self):
        return _ground_dy(self.hero)

    def clear(self):
        self.particles.clear()
        self.projectiles.clear()
        self.trail.reset()
        self.impacts = []
        self.skills = []

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def on_swing_start(self, x, y, facing):
        """Awal ayunan: trail reset + debu antisipasi di kaki."""
        self.trail.reset()
        self.trail.width_boost = 1.0
        self.swing_active = True
        gy = y + self._ground_dy()
        self.particles.burst(
            x + facing * 4, gy, 6,
            speed=(26, 92), life=(0.16, 0.38), size=(2, 4),
            colors=(P["dust"], P["ash"], P["smoke"]),
            spread=1.2, direction=math.pi if facing > 0 else 0.0,
            gravity=110.0, drag=2.6, shape="dust", layer="back")

    def on_swing_end(self):
        self.swing_active = False

    def on_swing_impact_frame(self, x, y, facing):
        """Sapuan di frame IMPACT — feedback walau tidak kena target."""
        grip, tip = cleaver_points(self.hero, x, y)
        ang = math.atan2(tip.y - grip.y, tip.x - grip.x)
        self.particles.burst(
            tip.x, tip.y, 9,
            speed=(130, 300), life=(0.1, 0.26), size=(1, 3),
            colors=(P["acid_hot"], P["acid_white"], P["acid_glow"]),
            spread=1.6, direction=ang, drag=3.6, shape="streak",
            additive=True)
        self.particles.burst(
            tip.x, tip.y, 4,
            speed=(60, 170), life=(0.14, 0.3), size=(1, 2),
            colors=(P["acid_bright"], P["acid_hot"]),
            spread=math.tau, drag=2.4, shape="bubble", additive=True)
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(
            tip.x, tip.y, ang, 0.6, False, kind="slash",
            ground=self._ground_dy(), seed=int(self.frames)))

    # ------------------------------------------------------------------
    def spawn_bottle(self, x, y, tx, ty):
        """Lempar botol Unstable Concoction (koordinat layar)."""
        tgt = getattr(self.hero, "target", None)
        if tgt is None or not getattr(tgt, "alive", False):
            tgt = None
        return self.projectiles.spawn(
            x, y, tx, ty, speed=BOTTLE_SPEED, damage=0, target=tgt,
            radius=8.0, kind="bottle", arc_height=BOTTLE_ARC,
            ground=self._ground_dy(),
            on_impact=lambda p: self._on_bottle_land(p))

    def _on_bottle_land(self, pr):
        """Botol mendarat: impact AOE + genangan + shake + hit-stop."""
        hx, hy = pr._hit_pos.x, pr._hit_pos.y
        if self._skill_dedupe_impact("w", hx, hy, 0.18):
            return
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        self.skills.append(SkillFX(
            "w", hx, hy, self.particles,
            radius=WORLD_RADIUS["w"], ground=self._ground_dy(),
            scale=_rscale(self.hero)))
        self.on_impact(hx, hy, -math.pi / 2, 1.35, False, kind="conc")
        self.particles.burst(
            hx, hy + self._ground_dy() * 0.4, 16,
            speed=(80, 300), life=(0.3, 0.7), size=(2, 5),
            colors=(P["acid_bright"], P["acid_hot"], P["acid_dark"]),
            spread=math.tau, gravity=360.0, drag=1.2, shape="drop")
        self.particles.burst(
            hx, hy + self._ground_dy() * 0.6, 10,
            speed=(30, 120), life=(0.5, 1.0), size=(3, 7),
            colors=(P["smoke"], P["ash"]),
            spread=math.tau, gravity=-40.0, drag=1.4, shape="smoke",
            layer="back")

    def _spray_q(self, x, y):
        """Q Acid Spray: semburan droplet dari moncong gun + SkillFX."""
        gx, gy = gun_end(self.hero, x, y)
        aim = target_screen(self.hero, x, y)
        ang = math.atan2(aim.y - gy, aim.x - gx)
        self.particles.burst(
            gx, gy, 10,
            speed=(80, 240), life=(0.1, 0.24), size=(1, 3),
            colors=(P["acid_white"], P["acid_hot"], P["acid_bright"]),
            spread=1.3, direction=ang, drag=3.0, shape="streak",
            additive=True)
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        self.skills.append(SkillFX(
            "q", gx, gy, self.particles, aim=(aim.x, aim.y),
            radius=WORLD_RADIUS["q"], ground=self._ground_dy(),
            facing=1 if getattr(self.hero, "direction", 1) >= 0 else -1,
            scale=_rscale(self.hero)))
        # droplet balistik mendarat di sepanjang kerucut
        for i in range(7):
            a = ang + (random.random() - 0.5) * 0.5
            dist = random.uniform(60.0, 150.0) * _rscale(self.hero)
            tx = gx + math.cos(a) * dist
            ty = gy + math.sin(a) * dist + 30
            self.projectiles.spawn(
                gx, gy, tx, ty, speed=random.uniform(260, 380),
                kind="droplet", radius=3.0, arc_height=0.0,
                lifetime=0.9, ground=self._ground_dy(),
                rot_speed=6.0)

    def _rage_burst(self, x, y):
        """E Chemical Rage: denyut buff + uap + heal glow."""
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        self.skills.append(SkillFX(
            "e", x, y, self.particles, radius=WORLD_RADIUS["e"],
            ground=self._ground_dy(),
            facing=1 if getattr(self.hero, "direction", 1) >= 0 else -1,
            scale=_rscale(self.hero)))
        self.on_impact(x, y - 6, 0.0, 1.15, False, kind="rage")
        self.particles.burst(
            x, y + self._ground_dy() * 0.4, 14,
            speed=(60, 200), life=(0.3, 0.7), size=(2, 5),
            colors=(P["acid_hot"], P["vapor"], P["acid_bright"]),
            spread=math.tau, gravity=-140.0, drag=1.6, shape="smoke")

    def _greed_storm(self, x, y):
        """R Greevil's Greed: badai koin AOE 200 + shockwave emas."""
        if len(self.skills) >= MAX_SKILLS:
            self.skills.pop(0)
        self.skills.append(SkillFX(
            "r", x, y, self.particles, radius=WORLD_RADIUS["r"],
            ground=self._ground_dy(),
            facing=1 if getattr(self.hero, "direction", 1) >= 0 else -1,
            scale=_rscale(self.hero)))
        self.on_impact(x, y - 8, 0.0, 2.0, True, kind="greed")
        # voli koin visual ke segala arah
        for i in range(10):
            a = random.uniform(0.0, math.tau)
            dist = random.uniform(90.0, 210.0) * _rscale(self.hero)
            self.projectiles.spawn(
                x, y - 10,
                x + math.cos(a) * dist,
                y + math.sin(a) * dist * 0.5 + 8,
                speed=random.uniform(240, 400), kind="coin",
                radius=3.0, arc_height=0.0, lifetime=1.1,
                ground=self._ground_dy(), rot_speed=10.0)

    def on_cast(self, x, y, skill):
        """Skill dilepas: SkillFX + guncangan + proyektil."""
        gy = self._ground_dy()
        if skill == "q":
            self._spray_q(x, y)
        elif skill == "w":
            hand = bottle_hand(self.hero, x, y)
            tgt = target_screen(self.hero, x, y)
            wt = getattr(self.hero, "w_target_x", None)
            if wt is not None:
                s = render_scale(self.hero)
                tgt = Vector2(
                    x + (float(wt) - float(getattr(self.hero, "x",
                                                   x))) / s,
                    y + (float(getattr(self.hero, "w_target_y", 0.0))
                         - float(getattr(self.hero, "y", y))) / s)
            self.particles.burst(
                hand.x, hand.y, 8,
                speed=(60, 180), life=(0.12, 0.28), size=(1, 3),
                colors=(P["acid_white"], P["acid_hot"]),
                spread=math.tau, drag=2.8, shape="bubble",
                additive=True)
            self.spawn_bottle(hand.x, hand.y, tgt.x, tgt.y)
        elif skill == "e":
            self._rage_burst(x, y)
        elif skill == "r":
            self._greed_storm(x, y)
        if shake_allowed():
            _feel_shake(5.0 if skill != "r" else 12.0,
                        0.16 if skill != "r" else 0.38)
        self.particles.burst(
            x, y + gy * 0.35, 12,
            speed=(60, 200), life=(0.2, 0.5), size=(2, 4),
            colors=(P["acid_mid"], P["dust"], P["ash"]),
            spread=math.tau, gravity=150.0, drag=2.0, shape="dust",
            layer="back")
        if skill == "r":
            _feel_hit_stop(0.06)

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="slash"):
        """Benturan mengenai target: flash, spark, debris, shake, stop."""
        if self._skill_dedupe_impact(kind, x, y, 0.16):
            return
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(
            x, y, angle, power, crit, kind=kind,
            ground=self._ground_dy(), seed=int(self.frames)))
        pw = min(2.0, max(0.35, float(power)))
        hot = P["acid_hot"]
        bright = P["acid_white"]
        if kind == "greed":
            hot, bright = P["gold_light"], P["gold_shine"]
        elif kind == "hurt":
            hot, bright = P["blue_hot"], P["blue"]
        n = int(9 + 7 * pw) + (6 if crit else 0)
        self.particles.burst(
            x, y, n, speed=(120, 340 + 90 * pw), life=(0.14, 0.4),
            size=(2, 4),
            colors=(hot, bright, P["acid_bright"] if kind != "greed"
                    else P["gold_mid"]),
            spread=2.4, direction=angle, drag=3.6, shape="streak")
        self.particles.burst(
            x, y, int(5 + 3 * pw) + (4 if crit else 0),
            speed=(70, 210), life=(0.28, 0.6), size=(2, 5),
            colors=(P["acid_bright"] if kind != "greed"
                    else P["gold_mid"], P["ash"], P["brass"]),
            gravity=470.0, drag=1.1, shape="shard",
            rotation_speed=(-16.0, 16.0))
        self.particles.burst(
            x, y + self._ground_dy() * 0.4, 6,
            speed=(40, 140), life=(0.3, 0.66), size=(2, 6),
            colors=(P["smoke"], P["ash"]), spread=math.tau,
            gravity=-30.0, drag=1.4, shape="smoke", layer="back")
        if crit:
            self.particles.burst(
                x, y, 8, speed=(180, 380), life=(0.2, 0.5),
                size=(2, 4),
                colors=(P["brass_hot"], P["brass"], hot),
                spread=math.tau, gravity=120.0, drag=2.0,
                shape="spark", additive=True)
        if shake_allowed():
            _feel_shake(4.0 + 3.4 * pw + (3.0 if crit else 0.0),
                        0.17 + 0.08 * pw)
        _feel_hit_stop(0.036 + 0.019 * min(1.5, pw) +
                       (0.014 if crit else 0.0))

    def on_hurt(self, amount=1.0):
        """Alchemist terkena serangan: flash + percikan + debu."""
        self.hit_flash = 0.16
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        self.particles.burst(
            hx, hy - 10, 7, speed=(80, 210), life=(0.14, 0.3),
            size=(2, 4),
            colors=(P["blue_hot"], P["acid_hot"], P["leather"]),
            drag=3.0, shape="spark", additive=True)
        self.particles.burst(
            hx, hy + 6, 5, speed=(30, 100), life=(0.22, 0.5),
            size=(2, 6),
            colors=(P["ogre_dark"], P["smoke"], P["leather"]),
            gravity=200.0, drag=2.0, shape="dust", layer="back")

    def on_death(self, x, y):
        """Kematian: ledakan asam + asap + serpihan sekali saja."""
        if self._death_done:
            return
        self._death_done = True
        gy = self._ground_dy()
        self.trail.reset()
        self.particles.clear()
        self.impacts.append(ImpactFX(x, y + gy * 0.3, -math.pi / 2,
                                     2.2, True, kind="conc", seed=7,
                                     ground=gy))
        self.particles.burst(
            x, y, 24, speed=(90, 340), life=(0.5, 1.1), size=(2, 6),
            colors=(P["acid_bright"], P["ogre_mid"], P["brass"],
                    P["leather"]),
            spread=math.tau, gravity=430.0, drag=1.1, shape="shard",
            rotation_speed=(-18.0, 18.0))
        self.particles.burst(
            x, y, 14, speed=(140, 320), life=(0.3, 0.6), size=(2, 4),
            colors=(P["acid_hot"], P["acid_glow"], P["acid_white"]),
            spread=math.tau, gravity=260.0, drag=1.4, shape="drop")
        self.particles.burst(
            x, y + gy, 18, speed=(40, 150), life=(0.5, 1.0),
            size=(3, 7), colors=(P["dust"], P["smoke"], P["ash"]),
            spread=math.tau, gravity=-30.0, drag=1.5, shape="smoke",
            layer="back")
        if shake_allowed():
            _feel_shake(9.0, 0.42)

    # ------------------------------------------------------------------
    def _skill_dedupe_impact(self, kind, x, y, window):
        """Hindari FX impact ganda untuk ledakan yang sama."""
        last = self._impact_dedupe.get(kind)
        now = self.time
        if last is not None:
            lx, ly, lt = last
            if now - lt <= window and math.hypot(x - lx, y - ly) < 14.0:
                self._impact_dedupe[kind] = (x, y, now)
                return True
        self._impact_dedupe[kind] = (x, y, now)
        return False

    def _skill_for(self, kind):
        for s in self.skills:
            if s.kind == kind and s.active and s.phase != "fade":
                return s
        return None

    # ------------------------------------------------------------------
    # Engine watchers (satu arah — hanya baca)
    # ------------------------------------------------------------------
    def _watch_engine_events(self, x, y):
        h = self.hero
        skill = getattr(h, "active_skill", None)
        timer = int(getattr(h, "active_skill_timer", 0) or 0)

        # ── W: jendela lempar dari renderer (edge) ─────────────────
        window = bool(getattr(h, "_alch_live_proj_window", False))
        if window and not self._proj_window_seen:
            self._proj_window_seen = True
        elif not window:
            self._proj_window_seen = False
        h._alch_live_proj_window = False     # konsumsi (edge)

        # ── Q: semburan mendarat di ~30% durasi ────────────────────
        if skill == "q" and timer:
            dur = max(1, int(SKILL_DUR.get("q", 40)))
            release_at = int(dur * 0.30)
            prev = self._skill_release.get("q")
            if prev != release_at and timer <= release_at:
                self._skill_release["q"] = release_at
                d = self._skill_for("q")
                if d is not None:
                    aim = target_screen(h, x, y)
                    d.impacted(aim.x, aim.y)
                    self.on_impact(aim.x, aim.y, 0.0, 1.0, False,
                                   kind="acid")
        elif skill != "q":
            self._skill_release.pop("q", None)

        # ── R: erupsi di 35% durasi ────────────────────────────────
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

        # ── RAGE buff aktif: bara + uap terus-menerus (hemat) ──────
        if getattr(h, "rage_active", False):
            self._rage_emit += getattr(h, "_alch_dt", FIXED_DT)
            if self._rage_emit >= 0.09:
                self._rage_emit = 0.0
                gy = self._ground_dy()
                self.particles.burst(
                    x + random.uniform(-14, 14),
                    y + gy * random.uniform(0.1, 0.5), 2,
                    speed=(14, 70), life=(0.3, 0.6), size=(2, 4),
                    colors=(P["acid_hot"], P["vapor"]),
                    direction=-math.pi / 2, spread=0.8,
                    gravity=-120.0, drag=1.2, shape="smoke",
                    layer="back")

    # ------------------------------------------------------------------
    # State machine (cermin prioritas renderer)
    # ------------------------------------------------------------------
    def _resolve_state(self):
        h = self.hero
        if not getattr(h, "alive", True):
            return "DEATH"
        if self.hit_flash > 0.0:
            return "HURT"
        skill = getattr(h, "active_skill", None)
        if skill:
            return "SPECIAL" if skill == "r" else (
                "SKILL" if skill == "e" else "CAST")
        action, _phase, ap = pose_of(h)
        if action == "attack":
            ph = attack_phase_of(h)
            if ph in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            if ph in ("SWING", "IMPACT"):
                return "SWING"
            return "ATTACK"
        if action == "walk":
            return "RUN" if float(getattr(h, "speed", 1.0) or
                                  1.0) >= 1.1 else "WALK"
        return "IDLE"

    def _update_state(self, dt):
        want = self._resolve_state()
        if want != self.state:
            cur_p = _ANIM_PRIORITY.get(self.state, 0)
            new_p = _ANIM_PRIORITY.get(want, 0)
            if self.state != "DEATH" and (new_p >= cur_p or
                                          self.state_time > 0.05):
                self.prev_state = self.state
                self.state = want
                self.state_time = 0.0
        self.state_time += dt
        self.anim_phase = attack_phase_of(self.hero)

    # ------------------------------------------------------------------
    def update(self, dt, x, y):
        """Satu langkah simulasi FX. ``x, y`` = posisi layar unit."""
        if dt <= 0.0:
            return
        self.time += dt
        self.frames += 1
        h = self.hero

        # damage masuk -> HURT
        hp = getattr(h, "hp", None)
        if hp is not None:
            if self._last_hp is not None and hp < self._last_hp - 0.01:
                self.on_hurt(
                    (self._last_hp - hp)
                    / max(1.0, float(getattr(h, "max_hp", 1.0))))
            self._last_hp = hp
        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)

        self._update_state(dt)
        self._watch_engine_events(x, y)
        if self.state == "DEATH":
            self.on_death(x, y)

        # cast skill (edge-triggered)
        skill = getattr(h, "active_skill", None)
        if skill != self._skill_seen:
            if skill:
                self.on_cast(x, y, skill)
            self._skill_seen = skill

        # ayunan: fase trail + frame impact
        facing = 1 if getattr(h, "direction", 1) >= 0 else -1
        action, _phase, ap = pose_of(h)
        ph = attack_phase_of(h)
        attacking = action == "attack"
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
            grip, tip = cleaver_points(h, x, y)
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
        """TRAIL -> PROJECTILE -> FRONT PARTICLES -> SKILL -> IMPACT."""
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
        """IMPACT FLASH: glow kecil + kilat dada — bukan cakram di badan."""
        k = max(0.0, min(1.0, self.hit_flash / 0.16))
        # Lane boss punya flash siluetnya sendiri (hurt_flash_timer); dua
        # flash penuh di frame yang sama terbaca sebagai white-out.
        if int(getattr(self.hero, "hurt_flash_timer", 0) or 0) > 0:
            k *= 0.35
        if k <= 0.02:
            return
        r = max(8, int(14 + 8 * k))
        if glow_allowed():
            # power 2.2 = falloff tajam: inti kecil, tepi cepat habis,
            # jadi glow membaca sebagai "kena pukul" tanpa membanjiri
            # badan Alchemist yang lebar.
            glow = glow_surface(r, P["blue_hot"], 2.2)
            _blit_faded(surface, glow, x, y - 12, int(150 * k),
                        additive=True)
        s = max(3, int(3 + 5 * k))
        star = spark_surface(s, P["acid_white"])
        star.set_alpha(int(150 * k))
        surface.blit(star, (int(x) - star.get_width() // 2,
                            int(y) - 18 - star.get_height() // 2))
        star.set_alpha(255)


# ============================================================================
# 10.  DEBUG OVERLAY  (DEBUG_CHARACTER = True)
# ============================================================================

_DEBUG_FONT = None


def _debug_font():
    global _DEBUG_FONT
    if _DEBUG_FONT is None:
        try:
            _DEBUG_FONT = pygame.font.Font(None, 15)
        except Exception:
            _DEBUG_FONT = False
    return _DEBUG_FONT or None


def draw_debug_overlay(surface, director):
    """Hitbox ayunan, hurtbox, jangkauan, tabrakan proyektil, state
    animasi + frame, FPS, jumlah partikel, state skill, timer serang."""
    h = director.hero
    x = int(getattr(h, "x", 0.0))
    y = int(getattr(h, "y", 0.0))
    G = _renderer()

    # hurtbox
    r = max(6, int(getattr(h, "radius", 30) * 0.9 *
                   (body_scale(h) if G is None else 1.0)))
    pygame.draw.rect(surface, (80, 170, 255, 150),
                     pygame.Rect(x - r, y - r - 10, r * 2, r * 2 + 18),
                     1)
    # jangkauan serangan
    rng = max(10, int(getattr(h, "range", 50) * 0.9))
    f = 1 if getattr(h, "direction", 1) >= 0 else -1
    pygame.draw.line(surface, (255, 210, 60, 150), (x, y),
                     (x + int(rng * f), y), 1)
    pygame.draw.rect(surface, (255, 210, 60, 110),
                     pygame.Rect(x + int(rng * f) - 5, y - 7, 10, 14),
                     1)
    # hitbox ayunan (hanya saat jendela hit aktif)
    if G is not None:
        try:
            hb = G._swing_hitbox(h, x, y)
        except Exception:
            hb = None
        if hb is not None:
            pygame.draw.rect(surface, (255, 70, 70, 190), hb, 2)
            pygame.draw.rect(surface, (255, 70, 70, 60), hb)
    # tabrakan proyektil hidup
    for p in director.projectiles.list():
        rr = max(3, int(p.hit_radius))
        pygame.draw.circle(surface, (255, 120, 255, 170),
                           (int(p.x), int(p.y)), rr, 1)
    # trail sample (histori bilah)
    for s in director.trail.samples:
        pygame.draw.circle(surface, (120, 255, 140, 120),
                           (int(s[2]), int(s[3])), 1)
    # teks state
    fps = director.frames / max(0.001, director.time)
    lines = [
        "ALCHEMIST live-FX",
        "state=%s->%s t=%.2fs" % (director.prev_state,
                                  director.state,
                                  director.state_time),
        "phase=%s animframe=%d" % (director.anim_phase,
                                   director.frames),
        "fps~%.0f particles=%d/%d" % (
            fps, director.particles.count(), MAX_PARTICLES),
        "proj=%d impacts=%d skills=%d" % (
            director.projectiles.count(), len(director.impacts),
            len(director.skills)),
        "atk=%s t=%.2f hitwin=%s" % (
            director.anim_phase,
            float(getattr(h, "_alch_attack_progress", 0.0)),
            "Y" if getattr(h, "_alch_hit_active", False) else "-"),
        "skill=%s timer=%d rage=%s" % (
            getattr(h, "active_skill", None),
            int(getattr(h, "active_skill_timer", 0)),
            bool(getattr(h, "rage_active", False))),
    ]
    font = _debug_font()
    if font is not None:
        for i, txt in enumerate(lines):
            surface.blit(font.render(txt, True, (235, 240, 220)),
                         (x - 64, y - 130 + i * 11))


# ============================================================================
# 11.  GAME-FEEL BUS  (hit-stop 0.03-0.08 s + shake lewat satu jalur)
# ============================================================================

def _feel_hit_stop(seconds):
    """Hit-stop dikunci 0.03-0.08 s (di luar dibuang)."""
    if _feel is None:
        return
    try:
        s = max(_feel.HIT_STOP_MIN, min(_feel.HIT_STOP_MAX,
                                        float(seconds)))
        _feel.hit_stop(s)
    except Exception:                          # pragma: no cover
        pass


def _feel_shake(strength, duration):
    """Screen shake lewat bus bersama (kamera digoyang satu kali)."""
    if _feel is None:
        return
    try:
        _feel.shake(float(strength), float(duration))
    except Exception:                          # pragma: no cover
        pass


#: Prioritas state (cermin _NS_alchemist.ANIM_PRIORITY).
_ANIM_PRIORITY = {
    "IDLE": 10, "WALK": 20, "RUN": 25, "CHARGE": 40,
    "ATTACK": 45, "SWING": 50, "CAST": 55, "SKILL": 56,
    "SPECIAL": 60, "HIT": 62, "HURT": 65, "DEATH": 100,
}


# ============================================================================
# 12.  API MODUL  (dipanggil renderer / base_boss / heroes/__init__)
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Alchemist."""
    _sync_palette()
    d = getattr(hero, "_alch_fx", None)
    if d is None:
        d = AlchemistFXDirector(hero)
        try:
            hero._alch_fx = d
        except Exception:                      # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:               # jangkar tua dibuang
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    """Lepas director dari registry DAN penanda miliknya di unit."""
    try:
        if director.hero is not None:
            director.hero._alch_fx = None
            director.hero._alch_live_fx = False
    except Exception:                          # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit ini (dipanggil renderer/pipeline).

    Sekalian menandai unit supaya renderer TIDAK menggambar efek yang
    sekarang dimiliki lapisan hidup di canvas. Return True kalau
    lapisan hidup jadi dipakai.
    """
    if not ALCHEMIST_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                          # pragma: no cover
        return False
    try:
        hero._alch_live_fx = True
    except Exception:                          # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini."""
    if not getattr(hero, "_alch_live_fx", False):
        return False
    d = getattr(hero, "_alch_fx", None)
    return d is not None and d in _DIRECTORS


def tick(dt=None):
    """Majukan waktu FX satu frame nyata; aman dipanggil berkali-kali."""
    global _LAST_TICK_MS
    if dt is not None:
        step = max(0.0, min(1.0 / 20.0, float(dt)))
        _advance(step)
        return step
    # Guard frame-sama: draw_ground_layer() memanggil tick() untuk SETIAP
    # unit, sedangkan _advance() melangkahkan SEMUA director. Tanpa guard
    # ini 4 unit sejenis di layar membuat FX maju ~4x lebih cepat.
    now = pygame.time.get_ticks()
    if now == _LAST_TICK_MS:
        return 0.0                             # frame yang sama: sudah maju
    if _feel is not None:
        _LAST_TICK_MS = now
        try:
            step = _feel.fx_dt()
        except Exception:                      # pragma: no cover
            step = 0.0
    else:                                      # pragma: no cover
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
    """Langkahkan seluruh director dengan dt yang sama."""
    if step <= 0.0 or not _DIRECTORS:
        return
    for d in _DIRECTORS:
        h = d.hero
        d.update(step, float(getattr(h, "x", 0.0)),
                 float(getattr(h, "y", 0.0)))


def reset_all():
    """Bersihkan seluruh state FX (ganti level / keluar match)."""
    global _LAST_TICK_MS
    _LAST_TICK_MS = None                       # jangan telan tick pertama
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()


def total_particles():
    """Jumlah partikel Alchemist hidup di seluruh arena."""
    return sum(d.particles.count() for d in _DIRECTORS)


def total_projectiles():
    """Jumlah proyektil visual Alchemist (dipakai test & HUD)."""
    return sum(d.projectiles.count() for d in _DIRECTORS)


def projectiles_for(hero):
    """Daftar proyektil hidup milik satu unit (dipakai debug)."""
    d = getattr(hero, "_alch_fx", None)
    return d.projectiles.list() if d is not None else []


# --- hook yang dipanggil renderer / heroes/__init__.py ---------------------

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: digambar SEBELUM sprite di-blit."""
    if not ALCHEMIST_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_alch_fx", None)
    if d is not None:
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: digambar SESUDAH sprite di-blit."""
    if not ALCHEMIST_FX_ENABLED:
        return
    d = director_for(hero)
    d.draw_front(surface, x, y)


# --- hook yang dipanggil _entity.py / bosses/base_boss.py ------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Cleaver Alchemist mendarat di target (basic attack melee)."""
    if not ALCHEMIST_FX_ENABLED or hero is None or target is None:
        return
    try:
        power = 0.75 + min(1.5, float(damage) / 70.0)
    except (TypeError, ValueError):
        power = 1.0
    tx = float(getattr(target, "x", getattr(hero, "x", 0.0)))
    ty = float(getattr(target, "y", getattr(hero, "y", 0.0))) - 6.0
    ang = math.atan2(ty - float(getattr(hero, "y", 0.0)),
                     tx - float(getattr(hero, "x", 0.0)))
    director_for(hero).on_impact(tx, ty, ang, power, bool(crit),
                                 kind="slash")


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0,
                             crit=False, kind="acid"):
    """Proyektil (botol / droplet) mengenai target."""
    if not ALCHEMIST_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    director_for(hero).on_impact(x, y, angle, power, bool(crit),
                                 kind=kind)


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """Skill Alchemist meledak di sebuah titik (Q/W/E/R AOE)."""
    if not ALCHEMIST_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    r = float(radius if radius is not None
              else WORLD_RADIUS.get(skill, 60.0))
    if skill == "w":
        d.on_impact(x, y, -math.pi / 2, 1.35, False, kind="conc")
        if d._skill_for("w") is None and len(d.skills) < MAX_SKILLS:
            d.skills.append(SkillFX(
                "w", x, y, d.particles, radius=r,
                ground=_ground_dy(hero), scale=_rscale(hero)))
        return
    if skill in ("q", "e", "r"):
        if d._skill_for(skill) is None and len(d.skills) < MAX_SKILLS:
            d.skills.append(SkillFX(
                skill, x, y, d.particles, radius=r,
                ground=_ground_dy(hero), scale=_rscale(hero)))
        d.on_impact(x, y, 0.0,
                    1.2 if skill != "r" else 2.0, skill == "r",
                    kind={"q": "acid", "e": "rage",
                          "r": "greed"}.get(skill, "acid"))


def notify_skill_cast(hero, skill):
    """Dipanggil jalur gameplay saat skill dilepas (opsional)."""
    if not ALCHEMIST_FX_ENABLED or hero is None or skill not in \
            SKILL_DUR:
        return
    director_for(hero).on_cast(
        float(getattr(hero, "x", 0.0)),
        float(getattr(hero, "y", 0.0)), skill)


def notify_hurt(hero, amount=1.0):
    """Paksa HURT (alat uji / pemanggil eksternal)."""
    if not ALCHEMIST_FX_ENABLED or hero is None:
        return
    director_for(hero).on_hurt(float(amount))


# --- hook yang dipanggil _NS_alchemist._spawn_acid_bottle (fallback) -------

def spawn_bottle(hero, sx, sy, tx, ty):
    """API kompatibilitas: lempar botol di koordinat layar."""
    if not ALCHEMIST_FX_ENABLED or hero is None:
        return None
    return director_for(hero).spawn_bottle(sx, sy, float(tx),
                                           float(ty))
