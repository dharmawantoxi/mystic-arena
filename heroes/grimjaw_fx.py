# ============================================================================
# heroes/grimjaw_fx.py
# ----------------------------------------------------------------------------
# GRIMJAW — COMBAT / GAME-FEEL ENGINE  (screen-space live layer)
#
# Badan Grimjaw digambar lewat ``_NS_grimjaw`` (heroes/_bundle.py) ke canvas
# yang DI-CACHE lalu di-scale oleh pipeline hero.  Artinya semua yang butuh
# gerak 60 fps sejati — trail pedang dari posisi NYATA, partikel, proyektil
# gelombang bilah, impact, guncangan layar — TIDAK boleh hidup di dalam
# canvas itu: hasilnya ikut terkunci pada kuantisasi pose (2 frame per pose)
# dan menyusut bersama sprite.  Modul ini adalah lapisan hidup tersebut:
# digambar langsung ke layar pada skala 1:1 tiap frame, dengan delta-time
# nyata, dan tidak pernah ikut ter-cache.
#
# Pembagian kerja (sengaja, supaya tidak ada efek yang digambar 2x):
#
#   RENDERER (canvas, ter-cache)       MODUL INI (layar, hidup)
#   -----------------------------     -----------------------------------
#   rig + selout + rim light          trail pedang dari histori posisi nyata
#   bayangan kontak, marker tanah     partikel (debu, bara, serpihan, asap)
#   TELEGRAPH tanah Q/W/E/R           proyektil gelombang bilah (visual)
#   pose, foot solver, napas          IMPACT FX + flash + hit-stop + shake
#   afterimage omnislash              overlay DEBUG_CHARACTER
#
# 100% PROSEDURAL. Tidak ada PNG / JPG / GIF / sprite-sheet / image.load.
# Semua bentuk dibuat dengan pygame.draw + pygame.Surface +
# pygame.transform + pygame.Vector2.
#
# Isi modul
#   GRIMJAW_PALETTE     palette khusus karakter (kontrak 9 kunci + ramp api)
#   Particle            partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem      pool + burst + stream + cap, reusable
#   SwingTrail          weapon trail prosedural dari histori posisi bilah
#   ImpactFX            flash + shockwave + debris + slash fragment
#   GrimjawProjectile   proyektil modular (spawn->travel->hit->destroy)
#   ProjectileSystem    manajer proyektil
#   SkillFX             lifecycle FX skill (cast->charge->release->fade)
#   GrimjawFXDirector   satu instance per unit, mengikat semua di atas
#   draw_debug_overlay  hitbox/hurtbox/state/frame/FPS/particle/skill/timer
#   API modul           tick / reset_all / notify_* / draw_*_layer
#
# Game-feel (hit-stop 0.03–0.08 s + screen-shake trauma) TIDAK dimiliki
# modul ini: semuanya lewat bus bersama ``heroes/combat_feel.py`` yang
# sudah dipakai Zephyr & Gornak, jadi tiga karakter memukul di frame yang
# sama tidak menumpuk freeze.
# ============================================================================

import math
import random

import pygame

try:                                 # bus game-feel bersama (zephyr & gornak)
    from heroes import combat_feel as _feel
except Exception:                    # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual untuk karakter GRIMJAW: hitbox, hurtbox, jangkauan, state
#: animasi, frame, FPS, jumlah partikel, state skill, timer serangan.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
GRIMJAW_FX_ENABLED = True

#: Hit-stop global (dibaca _core.Game.update lewat should_freeze_frame).
HIT_STOP_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 108

#: Batas keras projectile visual per director.
MAX_PROJECTILES = 12

#: Panjang histori trail senjata (jumlah sample posisi lama).
TRAIL_SAMPLES = 7

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0


# ============================================================================
# 1.  PALETTE  —  dark-fantasy juggernaut: api + darah + baja + emas
# ============================================================================

GRIMJAW_PALETTE = {
    # ── kontrak palette karakter (9 kunci wajib) ────────────────────
    "outline":    (34,  20,  13),
    "shadow":     (18,  10,   8),
    "dark":       (70,  22,  12),
    "body":       (112,  66,  37),
    "mid":        (200,  96,  34),
    "light":      (238, 152,  58),
    "highlight":  (255, 198,  96),
    "weapon":     (160, 102,  58),
    "fx":         (255, 226, 140),

    # ── ramp api (trail / gelombang bilah / impact) ─────────────────
    "fx_darkest": (34,  20,  13),
    "fx_dark":    (70,  22,  12),
    "fx_mid":     (200,  96,  34),
    "fx_light":   (238, 152,  58),
    "fx_bright":  (255, 198,  96),
    "fx_hot":     (255, 226, 140),
    "fx_white":   (255, 255, 250),

    # ── darah & emas (crit strike) ──────────────────────────────────
    "blood":      (204,  40,  44),
    "blood_hot":  (255, 118, 118),
    "gold":       (234, 192,  90),
    "gold_hot":   (255, 234,  160),

    # ── rage / omnislash (merah pekat) ──────────────────────────────
    "rage_dark":  (96,  10,  14),
    "rage_mid":   (168,  24,  26),
    "rage_light": (224,  52,  48),
    "rage_bright": (255, 118,  96),

    # ── penyembuhan (ward) ──────────────────────────────────────────
    "heal_dark":  (24,  84,  52),
    "heal_mid":   (66, 168, 104),
    "heal_light": (140, 224, 160),
    "heal_core":  (210, 255, 220),

    # ── sisa pembakaran (debu / asap / arang / bara) ────────────────
    "smoke":      (26,  18,  14),
    "ash":        (74,  52,  40),
    "dust":       (128, 104,  82),
    "ember":      (255, 170,  80),
}

P = GRIMJAW_PALETTE

#: Kunci yang boleh disalin dari palet renderer supaya warna karakter dan
#: warna efek tidak pernah melenceng satu derajat pun (konvensi gornak_fx).
_PALETTE_SYNC = {
    "outline":     "armor_darkest",
    "shadow":      "shadow_deep",
    "dark":        "fire_dark",
    "body":        "armor_mid",
    "mid":         "fire_mid",
    "light":       "fire_light",
    "highlight":   "fire_hot",
    "weapon":      "metal_light",
    "fx":          "fire_core",
    "fx_darkest":  "fire_darkest",
    "fx_dark":     "fire_dark",
    "fx_mid":      "fire_mid",
    "fx_light":    "fire_light",
    "fx_bright":   "fire_hot",
    "fx_hot":      "fire_core",
    "fx_white":    "white",
    "blood":       "blood_mid",
    "blood_hot":   "blood_bright",
    "gold":        "gold_light",
    "gold_hot":    "gold_shine",
    "rage_dark":   "rage_dark",
    "rage_mid":    "rage_mid",
    "rage_light":  "rage_light",
    "rage_bright": "rage_bright",
    "heal_dark":   "heal_dark",
    "heal_mid":    "heal_mid",
    "heal_light":  "heal_light",
    "heal_core":   "heal_core",
    "ember":       "ember",
    "smoke":       "shadow_deep",
    "ash":         "armor_dark",
}

_PALETTE_SYNCED = False

#: Literal fallback untuk palet renderer (dipakai kalau bundle tak ada).
_RENDERER = None            # None = belum dicari, False = tidak ada


def _renderer():
    """Ambil namespace renderer Grimjaw (lazy, sekali saja)."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from heroes._bundle import _NS_grimjaw as G
            _RENDERER = G
        except Exception:                  # pragma: no cover - tool minimal
            _RENDERER = False
    return _RENDERER or None


def _sync_palette():
    """Salin warna tema dari ``_NS_grimjaw.PALETTE`` sekali saja.

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


def skill_detail():
    """Detail telegraf/skill 0..1 (turunan beban FX).

    Dipakai untuk mengurangi jumlah retakan, rune, dan segmen cincin
    saat banyak hero live-FX bertarung. Hanya intensitas yang dikurangi
    (bukan frame yang dilewati), sehingga skill tidak berkedip.
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
        elif n >= 4:
            r, g, b = color[0], color[1], color[2]
            if (isinstance(r, int) and isinstance(g, int) and
                    isinstance(b, int) and
                    0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                return color if isinstance(color, tuple) else (r, g, b)
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


# ============================================================================
# 4.  SURFACE CACHE  —  glow / spark / ring / crescent dibuat sekali
# ============================================================================

_SURF_CACHE = {}
_SURF_CACHE_MAX = 384


def _cache_put(key, surf):
    # Buang 25% entri tertua saat penuh (dict Python menjaga urutan
    # sisip) — jauh lebih baik daripada mengosongkan seluruh cache.
    if len(_SURF_CACHE) >= _SURF_CACHE_MAX:
        for k in list(_SURF_CACHE)[:_SURF_CACHE_MAX // 4]:
            del _SURF_CACHE[k]
    _SURF_CACHE[key] = surf
    return surf


def glow_surface(radius, color, power=1.0):
    """Bola cahaya radial prosedural, PREMULTIPLIED untuk additive blit.

    ``BLEND_RGB_ADD`` mengabaikan kanal alpha, jadi intensitas sudah
    dikalikan ke kanal RGB (premultiplied) — surface yang sama tetap
    benar untuk blit normal maupun additive.
    """
    radius = max(2, int(radius))
    color = _clamp_color(color)
    key = ("glow", radius, color, round(power, 2))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    size = radius * 2 + 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = radius + 1
    # Posterized ala spidol: 4 band cahaya TEGAS (bukan gradien halus)
    # supaya konsisten dengan renderer doodle. Pusat tiap band
    # digeser 1 px secara deterministik - blob "ditekan tangan".
    for bi, f in enumerate((0.22, 0.45, 0.70, 1.0)):
        k = power * f
        if k <= 0.004:
            continue
        r = max(1, int(radius * (1.05 - 0.75 * f)))
        dx = dy = 0
        if radius >= 7:
            dx = int(round((_hash01(radius * 31 + bi * 7) - 0.5) * 2))
            dy = int(round((_hash01(radius * 57 + bi * 13) - 0.5) * 2))
        pygame.draw.circle(
            surf,
            (int(color[0] * k), int(color[1] * k), int(color[2] * k),
             min(255, int(255 * k))),
            (c + dx, c + dy), r)
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
    # Asterisk 5 jarum dengan sudut & panjang tidak rata (coretan
    # tangan), deterministik dari size supaya cache konsisten.
    for k in range(5):
        a = k * math.tau / 5 + _hash01(size * 31 + k) * 0.6
        L = size * (0.65 + 0.35 * _hash01(size * 17 + k * 7))
        pygame.draw.line(
            surf, (*color, 235), (c, c),
            (c + int(math.cos(a) * L), c + int(math.sin(a) * L)),
            2 if k % 2 == 0 else 1)
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

    size = radius * 2 + thickness * 2 + 6
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    # Cincin coret-tangan: radius tiap vertex di-jitter deterministik,
    # lalu pass kedua lebih tipis & bergeser (garis rangkap doodle).
    n = max(10, min(22, radius // 3))
    pts = []
    for i in range(n):
        a = i * math.tau / n
        wob = 1.0 + (_hash01(radius * 13 + i * 7) - 0.5) *             min(0.09, 3.0 / max(4, radius))
        pts.append((int(c + math.cos(a) * radius * wob + 0.5),
                    int(c + math.sin(a) * radius * wob + 0.5)))
    pygame.draw.lines(surf, (*color, int(alpha)), True, pts,
                      max(1, int(thickness * 0.8)))
    if radius >= 8:
        pts2 = [(px + (1 if i % 2 else -1), py)
                for i, (px, py) in enumerate(pts)]
        pygame.draw.lines(surf, (*color, int(alpha * 0.5)), True, pts2, 1)
    return _cache_put(key, surf)


def ellipse_ring_surface(rx, ry, thickness, color, angle_deg=0):
    """Cincin ELIPS (shockwave berarah) — cached + rotasi terkuantisasi.

    Shockwave yang gepeng tegak lurus arah pukulan jauh lebih terbaca
    daripada lingkaran sempurna: arah benturan langsung terlihat.
    """
    rx = max(3, int(rx))
    ry = max(2, int(ry))
    thickness = max(1, int(thickness))
    color = _clamp_color(color)
    step = int(angle_deg) // 10 * 10          # kuantisasi 10 derajat
    key = ("ering", rx, ry, thickness, color, step)
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    pad = thickness + 5
    base = pygame.Surface((rx * 2 + pad * 2, ry * 2 + pad * 2),
                          pygame.SRCALPHA)
    cx = rx + pad
    cy = ry + pad
    # Elips coret-tangan: vertex parametrik di-jitter radial.
    n = max(10, min(24, (rx + ry) // 4))
    pts = []
    for i in range(n):
        a = i * math.tau / n
        wob = 1.0 + (_hash01(rx * 13 + ry * 7 + i * 11) - 0.5) *             min(0.09, 3.0 / max(4, (rx + ry) // 2))
        pts.append((int(cx + math.cos(a) * rx * wob + 0.5),
                    int(cy + math.sin(a) * ry * wob + 0.5)))
    pygame.draw.lines(base, (*color, 255), True, pts,
                      max(1, int(thickness * 0.85)))
    if rx >= 8:
        pts2 = [(px + (1 if i % 2 else -1), py)
                for i, (px, py) in enumerate(pts)]
        pygame.draw.lines(base, (*color, 120), True, pts2, 1)
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
    # 3 band tegas (posterized) + coretan horizontal di band tengah:
    # kabut dibaca sebagai arsiran spidol, bukan blur.
    for bi, f in enumerate((0.30, 0.58, 1.0)):
        k = power * f
        if k <= 0.004:
            continue
        rx = max(2, int(radius * f))
        ry = max(1, int(radius * f * 0.5))
        dy = int(round((_hash01(radius * 23 + bi * 5) - 0.5) * 2))
        pygame.draw.ellipse(
            surf,
            (int(color[0] * k), int(color[1] * k), int(color[2] * k),
             min(255, int(255 * k))),
            (w // 2 - rx, h // 2 - ry + dy, rx * 2, ry * 2))
    for k in range(3):
        sx = int(w * (0.30 + 0.20 * k))
        ln = int(radius * (0.22 + 0.10 * _hash01(radius * 7 + k)))
        yy = h // 2 + int((_hash01(radius * 11 + k * 3) - 0.5) *
                          radius * 0.6)
        pygame.draw.line(
            surf, (int(color[0] * power), int(color[1] * power),
                   int(color[2] * power), min(255, int(190 * power))),
            (sx, yy), (sx + ln, yy + 1), 1)
    return _cache_put(key, surf)


def crescent_surface(radius, color, depth=0.62):
    """Bulan sabit API (dua busur) — bentuk khas gelombang bilah Grimjaw.

    Bukan lingkaran: shape dibentuk busur luar minus busur dalam yang
    digeser, lalu ditebalkan 3 band supaya terbaca sebagai tebasan.
    """
    radius = max(4, int(radius))
    color = _clamp_color(color)
    depth = max(0.2, min(1.4, float(depth)))
    key = ("crescent", radius, color, round(depth, 2))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    size = radius * 2 + 6
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2

    def _arc_pts(r, a0, a1, salt, wob):
        n = max(7, min(18, int(r)))
        pts = []
        for i in range(n + 1):
            t = i / n
            a = a0 + (a1 - a0) * t
            wv = 1.0 + (_hash01(radius * 29 + salt + i * 11) - 0.5) * wob
            pts.append((int(c + math.cos(a) * r * wv + 0.5),
                        int(c + math.sin(a) * r * wv + 0.5)))
        return pts

    # busur luar tebal (coretan utama) + busur dalam ramping;
    # jitter radial kecil supaya terlihat digambar tangan.
    pygame.draw.lines(surf, (*color, 235), False,
                      _arc_pts(radius, math.pi * 0.50, math.pi * 1.50,
                               0, 0.07),
                      max(2, radius // 4))
    off = radius * (1.0 - depth)
    pygame.draw.lines(surf, (*color, 200), False,
                      _arc_pts(radius - off, math.pi * 0.62,
                               math.pi * 1.38, 40, 0.09),
                      max(1, radius // 6))
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
    ``shape`` memilih bentuk gambar (pixel-art, hard edge).
    """

    __slots__ = ("pos", "vel", "acc", "life", "max_life", "size",
                 "rotation", "rotation_speed", "alpha", "gravity",
                 "color", "color_end", "shape", "drag", "additive",
                 "active", "fade_pow", "back")

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
        self.color = P["fx_bright"]
        self.color_end = None
        self.shape = "pixel"
        self.drag = 0.0
        self.additive = False
        self.active = False
        self.fade_pow = 1.0
        self.back = False

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
            # surface glow sudah premultiplied -> selalu additive
            if not glow_allowed():
                sz = max(1, sz // 2)
            g = glow_surface(sz * 2, col, round(0.9 * fade, 2))
            surface.blit(g, (x - sz * 2, y - sz * 2),
                         special_flags=pygame.BLEND_RGB_ADD)
            return

        if self.shape == "spark":
            # set_alpha diabaikan BLEND_RGB_ADD -> pakai blit normal
            s = spark_surface(sz + 1, col)
            s.set_alpha(a)
            surface.blit(s, (x - sz - 1, y - sz - 1))
            return

        if self.shape == "shard":
            # serpihan tajam yang berputar (debris / pecahan bilah)
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
            # garis tipis searah kecepatan — percikan cepat
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

        if self.shape == "ember":
            # bara api: wajik yang berkedip, 2 band (inti + selubung)
            fl = 0.72 + 0.28 * math.sin(self.rotation * 6.0)
            hh = max(1, int(sz * fl))
            ww = max(1, int(sz * 0.6))
            tmp = _scratch(ww * 2 + 4, hh * 2 + 4)
            ox, oy = ww + 1, hh + 1
            pygame.draw.polygon(tmp, (*_mix(col, P["fx_darkest"], 0.4),
                                      int(a * 0.8)),
                                [(ox, oy - hh), (ox + ww, oy),
                                 (ox, oy + hh), (ox - ww, oy)])
            pygame.draw.polygon(tmp, (*col, a),
                                [(ox, oy - hh // 2), (ox + ww // 2, oy),
                                 (ox, oy + hh // 2), (ox - ww // 2, oy)])
            surface.blit(tmp, (x - ox, y - oy),
                         special_flags=pygame.BLEND_RGB_ADD
                         if self.additive else 0)
            return

        if self.shape == "smoke":
            # puffs lembut di lapisan belakang — memberi bobot pada tebasan
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
    """Pool partikel reusable: spawn / burst / stream / update / draw."""

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
        """Spawn satu partikel.  Return partikel, atau None kalau penuh.

        Gerbang anggaran juga dipasang di sini karena banyak emisi
        kontinu (skill steady-state) tidak lewat ``burst()``. Tanpa ini
        governor Q.particle_ratio hanya memangkas burst, sehingga paket
        partikel 5 hero starter nyaris tidak berkurang.
        """
        budget = particle_budget()
        if budget <= 0.0:
            return None
        if (budget < 1.0 and not getattr(self, "_in_burst", 0)
                and random.random() >= budget):
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
              rotation_speed=(0.0, 0.0), fade_pow=1.0, back=False):
        """Semburan radial / berarah.

        ``direction`` + ``spread`` mengontrol kerucut sebaran; spread
        ``math.tau`` = melingkar penuh.  ``back=True`` mengirim partikel
        ke lapisan belakang karakter (asap/debu).  Jumlah partikel
        otomatis mengikuti anggaran kualitas perangkat.
        """
        count = _budgeted(count)
        if count <= 0:
            return 0
        colors = colors or (P["fx_bright"], P["fx_light"], P["fx_hot"])
        room = self.cap - len(self._live)
        if room <= 0:
            return 0
        n = min(int(count), room)
        self._in_burst = getattr(self, "_in_burst", 0) + 1
        try:
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
                    back=back)
        finally:
            self._in_burst -= 1
        return n

    # ------------------------------------------------------------------
    def stream(self, x, y, tx, ty, count, life=(0.3, 0.6), size=(1, 3),
               colors=None, drag=1.2, shape="ember"):
        """Aliran partikel dari (x,y) menuju (tx,ty) — charge / hisap."""
        count = _budgeted(count)
        if count <= 0:
            return 0
        colors = colors or (P["fx_light"], P["ember"])
        n = 0
        for i in range(int(count)):
            t = i / max(1, count)
            px = x + (tx - x) * t + random.uniform(-4, 4)
            py = y + (ty - y) * t + random.uniform(-3, 3)
            dx, dy = tx - px, ty - py
            dist = max(1.0, math.hypot(dx, dy))
            spd = random.uniform(90.0, 200.0)
            if self.spawn(px, py, dx / dist * spd, dy / dist * spd,
                          random.uniform(life[0], life[1]),
                          random.uniform(size[0], size[1]),
                          colors[i % len(colors)],
                          drag=drag, shape=shape,
                          color_end=P["fx_dark"],
                          rotation=random.random() * math.tau,
                          rotation_speed=random.uniform(-6, 6)):
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
# 6.  SWING TRAIL  —  weapon trail prosedural dari histori posisi bilah
# ============================================================================

class SwingTrail:
    """Jejak pedang Grimjaw berbasis histori posisi (OLD POS ... CURRENT).

    Menyimpan pasangan (grip, tip) beberapa frame terakhir lalu
    menyusunnya jadi pita poligon translucent 3-band yang memudar.
    Trail OTOMATIS mengikuti arah serangan karena bentuknya murni
    turunan dari lintasan busur bilah (arc-based), bukan lerp linear.
    """

    def __init__(self, samples=TRAIL_SAMPLES,
                 color_edge=None, color_core=None):
        self.samples = int(samples)
        self.points = []            # [[grip, tip, umur], ...]
        self.color_edge = color_edge or P["fx_dark"]
        self.color_core = color_core or P["fx_hot"]
        self.life = 0.26            # detik sebelum sample dibuang
        self.width_boost = 1.0
        self.spin_mode = False      # True saat Blade Fury (pita lebih panas)
        self.active = False
        self.seed = 13              # seed wobble kontur tinta (deterministik)

    # ------------------------------------------------------------------
    def reset(self):
        """Kosongkan trail (dipanggil saat swing baru dimulai)."""
        self.points.clear()
        self.active = False
        self.spin_mode = False

    def push(self, grip, tip):
        """Catat satu posisi senjata (dipanggil tiap frame saat swing)."""
        self.points.append([pygame.Vector2(grip), pygame.Vector2(tip), 0.0])
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
        minx, maxx = int(min(xs)) - 6, int(max(xs)) + 6
        miny, maxy = int(min(ys)) - 6, int(max(ys)) + 6
        w = maxx - minx
        h = maxy - miny
        if w <= 0 or h <= 0 or w > 1400 or h > 1400:
            return

        buf = _scratch(w, h)

        def loc(v):
            return (int(v.x) - minx, int(v.y) - miny)

        hot = 1.25 if self.spin_mode else 1.0

        # ── lapis 0: kontur tinta di tepi luar (ujung bilah) ─────────
        # garis rangkap doodle: tepi trail digambar tinta gelap dulu
        # supaya band api di atasnya terbaca sebagai coretan spidol.
        ink_pts = []
        for i, (_g, t, a) in enumerate(self.points):
            fade = max(0.0, 1.0 - a / self.life)
            if fade <= 0.05:
                continue
            jx = int(round((_hash01(self.seed * 13 + i * 7) - 0.5) * 2))
            jy = int(round((_hash01(self.seed * 29 + i * 11) - 0.5) * 2))
            ink_pts.append((loc(t)[0] + jx, loc(t)[1] + jy))
        if len(ink_pts) >= 2:
            pygame.draw.lines(
                buf, (*P["fx_darkest"], 120), False, ink_pts, 2)
            pygame.draw.lines(
                buf, (*P["fx_darkest"], 70), False,
                [(px + 1, py - 1) for px, py in ink_pts], 1)

        # ── lapis 1: selubung gelap (lebar penuh, api paling gelap) ──
        for i in range(n - 1):
            g0, t0, a0 = self.points[i]
            g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(150 * self._quad_alpha(i, n) * fade *
                        self.width_boost)
            if alpha <= 4:
                continue
            pygame.draw.polygon(
                buf, (*P["fx_darkest"], alpha),
                [loc(g0), loc(t0), loc(t1), loc(g1)])

        # ── lapis 2: badan api (setengah lebar, dekat ujung) ─────────
        for i in range(n - 1):
            g0, t0, a0 = self.points[i]
            g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(215 * self._quad_alpha(i, n) * fade * hot)
            if alpha <= 6:
                continue
            m0 = g0.lerp(t0, 0.55)
            m1 = g1.lerp(t1, 0.55)
            pygame.draw.polygon(
                buf, (*self.color_edge, min(255, alpha)),
                [loc(m0), loc(t0), loc(t1), loc(m1)])

        # ── lapis 3: inti membara ( seperempat lebar terakhir ) ──────
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

        # ── lapis 4: garis inti ujung (coretan putih, wobble 1 px) ──
        core_pts = []
        for i, (_g, t, a) in enumerate(self.points):
            fade = max(0.0, 1.0 - a / self.life)
            alpha = int(245 * self._quad_alpha(i, n) * fade)
            if alpha <= 8:
                continue
            jx = int(round((_hash01(self.seed * 7 + i * 5) - 0.5) * 2))
            jy = int(round((_hash01(self.seed * 19 + i * 3) - 0.5) * 2))
            core_pts.append((loc(t)[0] + jx, loc(t)[1] + jy))
        if len(core_pts) >= 2:
            pygame.draw.lines(buf, (*P["fx_white"], 235), False,
                              core_pts, 2)

        surface.blit(buf, (minx, miny))


# ============================================================================
# 7.  IMPACT FX
# ============================================================================

class ImpactFX:
    """Satu kejadian benturan: flash, shockwave, slash fragment, debris.

    Semua digambar prosedural dan berumur pendek; tidak ada state yang
    hidup tanpa batas.  ``kind`` memilih bahasa benturan:
      * "blade" — tebasan pedang (busur + serpihan)
      * "crit"  — critical strike (emas + lebih besar)
      * "spin"  — tick Blade Fury (cincin horizontal)
      * "omni"  — tebasan Omnislash (silang + pilar pendek)
    """

    __slots__ = ("x", "y", "angle", "power", "age", "duration",
                 "crit", "active", "color", "kind")

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="blade"):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = max(0.35, float(power))
        self.age = 0.0
        self.duration = 0.34 + 0.10 * min(2.0, self.power)
        self.crit = bool(crit) or kind == "crit"
        self.active = True
        self.kind = kind
        if kind == "crit":
            self.color = P["gold"]
        elif kind == "omni":
            self.color = P["rage_bright"]
        elif kind == "spin":
            self.color = P["fx_light"]
        else:
            self.color = P["fx_hot"] if not crit else P["gold"]

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

        # ── 1. IMPACT FLASH — flare bintang 8 arah, bukan bola ──────
        if t < 0.22:
            ft = 1.0 - t / 0.22
            gr = int((5 + 9 * pw) * (0.5 + 0.5 * ft)) // 2 * 2 + 2
            surface.blit(glow_surface(gr, self.color, 0.55 * ft),
                         (x - gr, y - gr),
                         special_flags=pygame.BLEND_RGB_ADD)
            ln = (16 + 34 * pw) * ft
            fl = _scratch(int(ln * 2 + 8), int(ln * 2 + 8))
            c = int(ln + 4)
            for i in range(4):
                a = self.angle + k * math.pi / 4
                L = ln if k % 2 == 0 else ln * 0.42
                pygame.draw.line(
                    fl, (*P["fx_white"], int(240 * ft)), (c, c),
                    (c + int(math.cos(a) * L),
                     c + int(math.sin(a) * L)),
                    3 if k % 2 == 0 else 1)
            surface.blit(fl, (x - c, y - c))

        # ── 2. SHOCKWAVE — elips berarah (bukan lingkaran polos) ────
        rr = int((8 + 46 * pw) * (0.25 + 1.05 * t)) // 3 * 3
        th = max(1, int(4 * inv * pw))
        a = int(215 * inv * inv)
        if a > 6 and rr > 4:
            er = ellipse_ring_surface(rr, max(3, int(rr * 0.62)), th,
                                      P["fx_light"], deg)
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
        if t < 0.6:
            st = 1.0 - t / 0.6
            r0 = int((6 + 20 * pw) * (0.3 + 1.1 * t))
            for i in range(4):
                ang = self.angle + k * math.pi / 4 + 0.19
                L = (7 + 15 * pw) * st * (1.0 if k % 2 else 0.55)
                pygame.draw.line(
                    surface, _clamp_color(
                        _mix(P["fx_dark"], P["fx_bright"], st)),
                    (x + int(math.cos(ang) * r0),
                     y + int(math.sin(ang) * r0)),
                    (x + int(math.cos(ang) * (r0 + L)),
                     y + int(math.sin(ang) * (r0 + L))),
                    2 if k % 2 else 1)

        # ── 4. SLASH FRAGMENT — 3 busur pecah searah tebasan ────────
        if t < 0.55 and self.kind in ("blade", "crit"):
            st = 1.0 - t / 0.55
            span = 0.55 + 0.5 * pw
            base_r = int(12 + 30 * pw * (0.4 + t))
            buf_r = base_r + 8
            buf = _scratch(buf_r * 2, buf_r * 2)
            c = buf_r
            for k in (-1, 0, 1):
                ang0 = self.angle - span / 2 + k * 0.12
                ang1 = ang0 + span
                rad = base_r - abs(k) * 5
                rect = pygame.Rect(c - rad, c - rad, rad * 2, rad * 2)
                col = P["fx_white"] if k == 0 else P["fx_bright"]
                try:
                    pygame.draw.arc(buf, (*col, int(225 * st)),
                                    rect, -ang1, -ang0,
                                    3 if k == 0 else 2)
                except (ValueError, pygame.error):
                    pass
            surface.blit(buf, (x - c, y - c))

        # ── 4b. OMNI — silang tebasan + pilar cahaya pendek ──────────
        if self.kind == "omni" and t < 0.5:
            st = 1.0 - t / 0.5
            ln = int((22 + 34 * pw) * st)
            for da in (math.pi / 4, -math.pi / 4):
                x0 = x - int(math.cos(self.angle + da) * ln)
                y0 = y - int(math.sin(self.angle + da) * ln)
                x1 = x + int(math.cos(self.angle + da) * ln)
                y1 = y + int(math.sin(self.angle + da) * ln)
                pygame.draw.line(surface, (*P["fx_white"],
                                           int(235 * st)),
                                 (x0, y0), (x1, y1), 3)
                pygame.draw.line(surface, (*P["rage_bright"],
                                           int(180 * st)),
                                 (x0, y0 + 1), (x1, y1 + 1), 1)
            hgt = int(40 * st)
            if hgt > 4:
                pl = _scratch(14, hgt + 4)
                pygame.draw.polygon(
                    pl, (*P["rage_light"], int(150 * st)),
                    [(7, hgt + 2), (7 - 3, 2), (7 + 3, 2)])
                surface.blit(pl, (x - 7, y - hgt - 20))

        # ── 4c. SPIN — lengkung sapuan horizontal di ketinggian badan─
        if self.kind == "spin" and t < 0.45:
            st = 1.0 - t / 0.45
            rr = int((18 + 42 * pw) * (0.55 + 0.85 * t))
            buf_r = rr + 6
            buf = _scratch(buf_r * 2, buf_r)
            c, cy = buf_r, buf_r // 2
            rect = pygame.Rect(c - rr, cy - rr // 2, rr * 2, rr)
            try:
                pygame.draw.arc(buf, (*P["fx_hot"], int(220 * st)),
                                rect, math.pi, math.tau, 3)
                pygame.draw.arc(buf, (*P["fx_white"], int(170 * st)),
                                rect.inflate(-8, -4), math.pi,
                                math.tau, 1)
            except (ValueError, pygame.error):
                pass
            surface.blit(buf, (x - c, y - cy - 14))

        # ── 5. INTI benturan ─────────────────────────────────────────
        if t < 0.42:
            st = 1.0 - t / 0.42
            sz = int((5 + 9 * pw) * (0.5 + 0.5 * st)) // 2 * 2 + 2
            s = spark_surface(sz, self.color)
            s.set_alpha(int(255 * st))
            surface.blit(s, (x - sz - int(ca * 2), y - sz - int(sa * 2)))


# ============================================================================
# 8.  PROJECTILE SYSTEM  —  gelombang bilah api (blade wave)
# ============================================================================

class GrimjawProjectile:
    """Gelombang bilah api — modular, vektor, delta-time.

    Kontrak atribut: position, velocity, speed, damage, lifetime,
    target, radius, rotation, trail, particles, active.

    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY.

    Catatan desain: damage tetap 0 untuk gelombang visual — damage
    gameplay Q/E/R sudah diterapkan langsung oleh ``hero_skills``.
    Sistem ini tetap punya deteksi tumbukan penuh (radius vs target)
    supaya siklus hidupnya utuh dan bisa dipakai gameplay lain (callback
    ``on_impact``) tanpa mengubah keseimbangan hero.
    """

    STATE_TRAVEL = "travel"
    STATE_IMPACT = "impact"
    STATE_DEAD = "dead"

    def __init__(self, x, y, tx, ty, speed=430.0, damage=0,
                 target=None, radius=8.0, homing=3.2, kind="wave",
                 particles=None, on_impact=None):
        self.position = pygame.Vector2(x, y)
        self.spawn_pos = pygame.Vector2(x, y)
        d = pygame.Vector2(tx - x, ty - y)
        if d.length_squared() < 1e-6:
            d = pygame.Vector2(1.0, 0.0)
        self.velocity = d.normalize() * speed
        self.speed = float(speed)
        self.damage = damage
        self.lifetime = 0.0
        self.max_lifetime = 1.6
        self.target = target
        self.radius = float(radius)
        self.rotation = math.atan2(self.velocity.y, self.velocity.x)
        self.trail = []                  # [[Vector2, umur], ...]
        self.trail_life = 0.22
        self.particles = particles       # ParticleSystem bersama
        self.active = True
        self.state = self.STATE_TRAVEL
        self.kind = kind                 # "wave" | "ember_bolt"
        self.homing = float(homing)
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
            if self._impact_age > 0.28 and not self.trail:
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

        self.rotation = math.atan2(self.velocity.y, self.velocity.x)

        # ── catat trail lalu maju ────────────────────────────────────
        self.trail.append([pygame.Vector2(self.position), 0.0])
        if len(self.trail) > 16:
            self.trail.pop(0)
        self._age_trail(dt)

        self.position += self.velocity * dt

        # ── emisi partikel ekor (rate-limited) ───────────────────────
        if self.particles is not None:
            self._emit_acc += dt
            if self._emit_acc >= 0.03:
                self._emit_acc = 0.0
                ang = self.rotation + math.pi + (random.random() - .5) * 0.9
                spd = random.uniform(20, 80)
                self.particles.spawn(
                    self.position.x, self.position.y,
                    math.cos(ang) * spd, math.sin(ang) * spd - 26,
                    random.uniform(0.18, 0.38),
                    random.uniform(1.5, 3.0),
                    P["fx_light"] if random.random() < .5 else P["ember"],
                    color_end=P["fx_dark"], drag=2.6, shape="ember",
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
        """Trail -> glow -> badan sabit berarah -> inti -> kilau orbit."""
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
                wdt = self.radius * 0.8 * f * fade
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
                    buf, (*P["fx_dark"], 130),
                    [(int(px) - minx, int(py) - miny) for px, py in poly])
                pygame.draw.lines(
                    buf, (*P["fx_light"], 170), False,
                    [(int(pv.x) - minx, int(pv.y) - miny)
                     for pv, _a in self.trail], 2)
                surface.blit(buf, (minx, miny))

        if self.state == self.STATE_IMPACT:
            return

        draw_blade_wave(surface, self.position.x, self.position.y,
                        self.rotation, age=int(self.lifetime * 60),
                        crit=self.kind != "wave", radius=self.radius)


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
        pr = GrimjawProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    def update(self, dt):
        if not self.projectiles:
            return
        self.projectiles = [p for p in self.projectiles if p.update(dt)]

    def draw(self, surface):
        for p in self.projectiles:
            p.draw(surface)


def draw_blade_wave(surface, px, py, angle=0.0, age=0, crit=False,
                    radius=8.0):
    """Renderer bersama gelombang bilah api (dipakai projectile + tools).

    Badan = bulan sabit 2 busur yang berputar mengikuti arah terbang,
    plus glow premultiplied, inti putih, dan kilau orbit deterministik.
    Digambar ke scratch lalu di-blit sekali — tidak ada alokasi Surface
    per frame.
    """
    x, y = int(px), int(py)
    rad = max(4, int(radius))
    deg = int(math.degrees(angle)) // 10 * 10      # kuantisasi rotasi

    # glow di belakang (premultiplied, additive) — memberi bobot cahaya
    if glow_allowed():
        g = glow_surface(rad * 2, P["gold_hot"] if crit else P["fx_mid"],
                         0.55)
        surface.blit(g, (x - rad * 2, y - rad * 2),
                     special_flags=pygame.BLEND_RGB_ADD)

    # badan sabit di scratch (hard edge), lalu diputar
    key = ("wave_body", rad, bool(crit), deg)
    body = _SURF_CACHE.get(key)
    if body is None:
        s = rad * 2 + 6
        body = pygame.Surface((s, s), pygame.SRCALPHA)
        c = s // 2

        def _warc(r, a0, a1, salt):
            # busur coret-tangan: polyline dengan jitter radial kecil
            n = max(6, min(16, rad))
            pts = []
            for i in range(n + 1):
                t = i / n
                a = a0 + (a1 - a0) * t
                wv = 1.0 + (_hash01(rad * 37 + salt + i * 13) - 0.5) * 0.08
                pts.append((int(c + math.cos(a) * r * wv + 0.5),
                            int(c + math.sin(a) * r * wv + 0.5)))
            return pts

        # sabit menghadap +x (arah terbang), busur kiri-atas ke kiri-bawah
        pygame.draw.lines(body, (*P["fx_mid"], 235), False,
                          _warc(rad, math.pi * 0.55, math.pi * 1.45, 0),
                          max(2, rad // 3))
        pygame.draw.lines(body, (*P["fx_light"], 235), False,
                          _warc(rad - rad // 3, math.pi * 0.65,
                                math.pi * 1.35, 50),
                          max(1, rad // 5))
        pygame.draw.lines(body, (*P["fx_hot"], 220), False,
                          _warc(rad - rad // 3 - rad // 4, math.pi * 0.75,
                                math.pi * 1.25, 90), 1)
        # inti depan (kepala sabit)
        pygame.draw.circle(body, (*P["fx_white"], 255),
                           (c + rad - 2, c), max(1, rad // 4))
        if deg:
            body = pygame.transform.rotate(body, -deg)
        body = _cache_put(key, body)
    surface.blit(body, (x - body.get_width() // 2,
                        y - body.get_height() // 2))

    # kilau orbit deterministik (berputar mengikuti umur) — hidup, murah
    for k in range(3):
        a = angle + age * 0.22 + k * math.tau / 3
        gx = x + int(math.cos(a) * (rad + 3))
        gy = y + int(math.sin(a) * (rad + 3) * 0.5)
        s = spark_surface(2, P["fx_hot"])
        surface.blit(s, (gx - 3, gy - 3))


# ============================================================================
# 9.  SKILL FX  —  lifecycle cast -> charge -> release -> area -> fade
# ============================================================================

class SkillFX:
    """Efek skill Grimjaw dengan lifecycle bertahap.

    CAST -> CHARGE -> RELEASE -> TRAVEL/AREA -> IMPACT -> AFTER -> FADE

    Q Blade Fury   : vortex api + scorch + tick radial.
    W Healing Ward : kabut penyembuh + mote hijau naik + rune diamond.
    E Crit Strike  : suatan cahaya bilah + chevron kerucut ke depan.
    R Omnislash    : pilar rage + nova + silang tebasan + shard orbit.
    """

    #: (charge, release, area, impact, after) dalam detik
    TIMELINE = {
        "q": (0.34, 0.16, 0.95, 0.20, 0.55),
        "w": (0.26, 0.12, 1.10, 0.16, 0.60),
        "e": (0.22, 0.12, 0.70, 0.22, 0.45),
        "r": (0.40, 0.18, 1.30, 0.28, 0.80),
    }

    TINT = {
        "q": (None, None),      # diisi dari palet live (fire ramp)
        "w": (None, None),
        "e": (None, None),
        "r": (None, None),
    }

    RADIUS = {"q": 76, "w": 100, "e": 60, "r": 86}

    def __init__(self, kind, x, y, particles=None, radius=None):
        _sync_palette()
        self.kind = kind if kind in self.TIMELINE else "q"
        self.x = float(x)
        self.y = float(y)
        self.particles = particles
        self.radius = float(radius or self.RADIUS[self.kind])
        self.age = 0.0
        tl = self.TIMELINE[self.kind]
        self.t_charge = tl[0]
        self.t_release = tl[0] + tl[1]
        self.t_area = self.t_release + tl[2]
        self.t_impact = self.t_area + tl[3]
        self.total = self.t_impact + tl[4]
        self.active = True
        self.phase = "cast"
        self._released = False
        self._impacted = False
        self._emit = 0.0
        self.seed = random.randint(0, 9999)
        if self.kind == "q":
            self.col_a, self.col_b = P["fx_dark"], P["fx_hot"]
        elif self.kind == "w":
            self.col_a, self.col_b = P["heal_dark"], P["heal_core"]
        elif self.kind == "e":
            self.col_a, self.col_b = P["gold"], P["gold_hot"]
        else:
            self.col_a, self.col_b = P["rage_dark"], P["rage_bright"]

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

        if self.phase == "charge":
            # CHARGE: bara/debu tersedot masuk ke pusat
            self._emit += dt
            if self._emit >= 0.034:
                self._emit = 0.0
                a = random.random() * math.tau
                rr = self.radius * random.uniform(0.7, 1.15)
                sx = self.x + math.cos(a) * rr
                sy = self.y + math.sin(a) * rr * 0.45
                ps.spawn(sx, sy,
                         -math.cos(a) * rr * 1.7,
                         -math.sin(a) * rr * 0.8,
                         0.42, random.uniform(1.5, 3.0),
                         self.col_b if self.kind != "w" else P["heal_light"],
                         color_end=self.col_a,
                         shape="ember" if self.kind != "w" else "pixel",
                         fade_pow=0.6,
                         rotation=random.random() * math.tau,
                         rotation_speed=random.uniform(-8, 8))

        elif self.phase == "release" and not self._released:
            self._released = True
            if self.kind == "w":
                # ward: kelopak lembut, bukan ledakan
                ps.burst(self.x, self.y, 5,
                         speed=(40, 120), life=(0.4, 0.8), size=(2, 4),
                         colors=(P["heal_mid"], P["heal_light"],
                                 P["heal_core"]),
                         drag=2.2, shape="pixel", gravity=-30.0)
            else:
                ps.burst(self.x, self.y, 8,
                         speed=(130, 330), life=(0.24, 0.55),
                         size=(2, 4),
                         colors=(P["fx_white"], self.col_b, P["fx_light"]),
                         drag=3.2, shape="streak",
                         direction=0.0, spread=math.tau)
                ps.burst(self.x, self.y + 6, 4,
                         speed=(50, 150), life=(0.4, 0.8), size=(2, 5),
                         colors=(P["ash"], P["smoke"]),
                         gravity=-40.0, drag=1.6, shape="smoke", back=True)

        elif self.phase == "area":
            self._emit += dt
            if self.kind == "q":
                # AREA Q: bara spiral naik dari tanah (vortex)
                if self._emit >= 0.05:
                    self._emit = 0.0
                    a = random.random() * math.tau
                    rr = self.radius * random.uniform(0.3, 1.0)
                    ps.spawn(self.x + math.cos(a) * rr,
                             self.y + math.sin(a) * rr * 0.42,
                             -math.sin(a) * 60, -random.uniform(40, 110),
                             random.uniform(0.5, 1.0),
                             random.uniform(1.5, 3.0),
                             P["ember"], color_end=P["fx_dark"],
                             drag=0.6, shape="ember",
                             rotation=random.random() * math.tau,
                             rotation_speed=random.uniform(-10, 10))
            elif self.kind == "w":
                # AREA W: mote hijau naik pelan
                if self._emit >= 0.07:
                    self._emit = 0.0
                    a = random.random() * math.tau
                    rr = self.radius * random.uniform(0.2, 0.95)
                    ps.spawn(self.x + math.cos(a) * rr,
                             self.y + math.sin(a) * rr * 0.4,
                             random.uniform(-8, 8), -random.uniform(24, 52),
                             random.uniform(0.6, 1.2),
                             random.uniform(1.5, 3.0),
                             P["heal_light"], color_end=P["heal_dark"],
                             drag=0.4, shape="pixel")
            elif self.kind == "e":
                # AREA E: bara emas mengalir ke depan (kerucut)
                if self._emit >= 0.05:
                    self._emit = 0.0
                    f = random.uniform(-1.0, 1.0)
                    ps.spawn(self.x + f * 10,
                             self.y - random.uniform(2, 20),
                             f * random.uniform(60, 190),
                             -random.uniform(10, 60),
                             random.uniform(0.3, 0.6),
                             random.uniform(1.5, 3.0),
                             P["gold_hot"], color_end=P["blood"],
                             drag=2.0, shape="ember",
                             rotation=random.random() * math.tau,
                             rotation_speed=random.uniform(-9, 9))
            else:
                # AREA R: shard rage mengorbit lalu lepas
                if self._emit >= 0.06:
                    self._emit = 0.0
                    a = random.random() * math.tau
                    rr = self.radius * random.uniform(0.4, 0.9)
                    ps.spawn(self.x + math.cos(a) * rr,
                             self.y + math.sin(a) * rr * 0.5 - 10,
                             math.cos(a + 1.57) * random.uniform(90, 190),
                             math.sin(a + 1.57) * random.uniform(60, 120)
                             - 40,
                             random.uniform(0.4, 0.8),
                             random.uniform(2, 4),
                             P["rage_light"], color_end=P["rage_dark"],
                             drag=1.6, shape="shard",
                             rotation=a, rotation_speed=(-14.0, 14.0)[
                                 random.randint(0, 1)])

        elif self.phase == "impact" and not self._impacted:
            self._impacted = True
            if self.kind != "w":
                ps.burst(self.x, self.y, 7,
                         speed=(90, 260), life=(0.3, 0.62), size=(2, 5),
                         colors=(self.col_b, P["fx_light"], P["ash"]),
                         gravity=420.0, drag=1.0, shape="shard",
                         rotation_speed=(-14.0, 14.0))
        return True

    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        """Lapisan bawah karakter: kabut tanah, cincin, retakan, scorch."""
        if not self.active:
            return
        col_a, col_b = self.col_a, self.col_b
        a = self.age
        R = self.radius

        # kabut/glow tanah (additive) — radius & daya DIKUANTISASI supaya
        # jumlah entri cache tetap kecil.
        t_all = min(1.0, a / self.total)
        haze = int(R * (0.9 + 0.25 * math.sin(a * 4.0))) // 8 * 8
        power = round(0.30 * (1.0 - abs(t_all - 0.35) * 1.4) / 0.05) * 0.05
        if power > 0.02 and haze >= 8 and glow_allowed():
            hs = ground_glow_surface(haze, col_a, power)
            surface.blit(hs, (int(self.x) - hs.get_width() // 2,
                              int(self.y) - hs.get_height() // 2),
                         special_flags=pygame.BLEND_RGB_ADD)

        if self.phase == "charge":
            t = a / self.t_charge
            rr = int(R * (1.25 - 0.25 * t))
            self._ground_ring(surface, rr, col_a, int(120 + 90 * t),
                              dashed=True, phase=t * 6.0)
        elif self.phase in ("release", "area"):
            t = min(1.0, (a - self.t_charge) /
                    max(0.001, self.t_area - self.t_charge))
            self._ground_ring(surface, int(R), col_a,
                              int(200 - 90 * t), dashed=False)
            self._ground_ring(surface, int(R * 0.66), col_b,
                              int(160 - 70 * t), dashed=True,
                              phase=-t * 5.0)
            if self.kind != "w":
                self._ground_cracks(surface, R, col_b,
                                    int(170 * (1.0 - t)))
        else:
            t = min(1.0, (a - self.t_area) /
                    max(0.001, self.total - self.t_area))
            self._ground_ring(surface, int(R * (1.0 + 0.35 * t)), col_b,
                              int(150 * (1.0 - t)), dashed=False)

    def _ground_ring(self, surface, radius, color, alpha,
                     dashed=False, phase=0.0):
        if alpha <= 5 or radius <= 3:
            return
        w = radius * 2 + 8
        h = int(radius * 0.9) + 8
        buf = _scratch(w, h)
        cx, cy = w // 2, h // 2
        rect = pygame.Rect(cx - radius, cy - int(radius * 0.42),
                           radius * 2, int(radius * 0.84))
        if not dashed:
            pygame.draw.ellipse(buf, (*color, alpha), rect, 3)
            pygame.draw.ellipse(buf, (*P["fx_white"], alpha // 3),
                                rect.inflate(-6, -3), 1)
        else:
            detail = skill_detail()
            segs = max(8, min(16, int(16 * detail)))
            for i in range(segs):
                a0 = i * math.tau / segs + phase
                if i % 2 and detail >= 0.55:
                    continue
                x0 = cx + math.cos(a0) * radius
                y0 = cy + math.sin(a0) * radius * 0.42
                x1 = cx + math.cos(a0 + 0.26) * radius
                y1 = cy + math.sin(a0 + 0.26) * radius * 0.42
                pygame.draw.line(buf, (*color, alpha),
                                 (int(x0), int(y0)), (int(x1), int(y1)), 3)
        surface.blit(buf, (int(self.x) - cx, int(self.y) - cy))

    def _ground_cracks(self, surface, R, color, alpha):
        """Retakan tanah bergaris (bukan lingkaran) — deterministik."""
        if alpha <= 6:
            return
        detail = skill_detail()
        n_cracks = max(2, min(5, int(round(5 * detail))))
        for i in range(n_cracks):
            base = _hash01(self.seed + i * 31) * math.tau
            length = R * (0.55 + _hash01(self.seed + i * 77) * 0.5)
            px, py = self.x, self.y
            ang = base
            segs = max(2, min(4, int(round(4 * detail))))
            for seg in range(segs):
                ang += (_hash01(self.seed + i * 13 + seg) - 0.5) * 0.9
                nx = px + math.cos(ang) * (length / segs)
                ny = py + math.sin(ang) * (length / segs) * 0.42
                pygame.draw.line(surface, _clamp_color(color),
                                 (int(px), int(py)), (int(nx), int(ny)),
                                 max(1, 3 - seg))
                px, py = nx, ny

    # ------------------------------------------------------------------
    def draw_front(self, surface):
        """Lapisan atas karakter: nova, chevron, rune diamond."""
        if not self.active:
            return
        col_a, col_b = self.col_a, self.col_b
        a = self.age
        x, y = int(self.x), int(self.y)

        if self.phase == "charge":
            # Pilar cahaya charge DIBUANG: kolom 60-134 px yang berdiri
            # tepat di sumbu badan menutupi Grimjaw selama skill di-cast.
            # Fase charge kini tidak menggambar lapisan depan apa pun.
            return

        if self.phase == "release":
            t = (a - self.t_charge) / max(0.001,
                                          self.t_release - self.t_charge)
            r = int(self.radius * (0.4 + 1.1 * t))
            if glow_allowed():
                g = glow_surface(r // 3 * 3, P["fx_white"],
                                 round(0.8 * (1.0 - t), 2))
                surface.blit(g, (x - r, y - r),
                             special_flags=pygame.BLEND_RGB_ADD)
            ring = ring_surface(r, max(1, int(5 * (1 - t))), col_b, 255)
            ring.set_alpha(int(230 * (1 - t)))
            surface.blit(ring, (x - ring.get_width() // 2,
                                y - ring.get_height() // 2))

        elif self.phase == "area":
            t = (a - self.t_release) / max(0.001,
                                           self.t_area - self.t_release)
            if self.kind == "e":
                # E: chevron api berbaris ke depan (kerucut crit)
                self._chevrons(surface, t)
            else:
                # cincin rune berputar (dua arah berlawanan)
                for k, spd in ((0, 2.3), (1, -1.6)):
                    rr = int(self.radius * (0.55 + 0.22 * k))
                    self._rune_ring(surface, x, y - 6, rr,
                                    col_b if k else col_a,
                                    int(150 - 60 * t), a * spd, 8 + k * 4)

        elif self.phase == "impact":
            t = (a - self.t_area) / max(0.001, self.t_impact - self.t_area)
            r = int(self.radius * (0.6 + 0.9 * t))
            ring = ring_surface(r, max(1, int(6 * (1 - t))),
                                P["fx_white"], 255)
            ring.set_alpha(int(220 * (1 - t)))
            surface.blit(ring, (x - ring.get_width() // 2,
                                y - ring.get_height() // 2))

    # ------------------------------------------------------------------
    def _chevrons(self, surface, t):
        """Deretan chevron yang meluncur ke depan (telegraph cone E)."""
        f = 1.0 if getattr(self, "_facing", 0) >= 0 else -1
        col = self.col_b
        detail = skill_detail()
        n_chev = max(2, min(4, int(round(4 * detail))))
        for i in range(n_chev):
            prog = (t * 1.6 + i * 0.25) % 1.0
            dx = int(f * (14 + prog * self.radius))
            dy = -8 - int((1.0 - prog) * 10)
            al = int(210 * (1.0 - prog) * (0.4 + 0.6 * t))
            if al <= 6:
                continue
            cx = int(self.x) + dx
            cy = int(self.y) + dy
            w = 6 + i
            pts = [(cx + f * 7, cy), (cx - f * 3, cy - w),
                   (cx - f * 1, cy), (cx - f * 3, cy + w)]
            pygame.draw.polygon(surface, (*col, al), pts, 2)

    def _rune_ring(self, surface, cx, cy, radius, color, alpha,
                   rot, marks):
        """Rune diamond mengorbit — bukan lingkaran kontinu."""
        if alpha <= 5:
            return
        detail = skill_detail()
        marks = max(3, int(round(marks * (0.4 + 0.6 * detail))))
        for i in range(marks):
            ang = rot + i * math.tau / marks
            px = cx + math.cos(ang) * radius
            py = cy + math.sin(ang) * radius * 0.55
            sz = 3 if i % 2 else 2
            s = _scratch(sz * 2 + 4, sz * 2 + 4)
            pygame.draw.polygon(s, (*color, alpha),
                                [(sz + 2, 0), (sz * 2 + 3, sz + 2),
                                 (sz + 2, sz * 2 + 3), (1, sz + 2)])
            surface.blit(s, (int(px) - sz - 2, int(py) - sz - 2))


# ============================================================================
# 10.  GAME FEEL  —  screen shake + hit stop (via bus bersama)
# ============================================================================
#
# STATE INI GLOBAL, jadi tidak boleh dimiliki satu karakter.  Hit-stop &
# shake hidup di ``heroes/combat_feel.py``; modul ini hanya memakainya
# lewat nama lama supaya semua pemanggil — ``_core.Game.update``,
# ``_entity``, tooling, dan tes regresi — tidak perlu diubah.

if _feel is not None:
    ScreenShake = _feel.ScreenShake
    HitStop = _feel.HitStop
    HITSTOP = _feel.HITSTOP
    SHAKE = _feel.SHAKE
    FIXED_DT = _feel.FIXED_DT
else:                                      # pragma: no cover - fallback
    class ScreenShake:                     # noqa: F811
        """Shake lokal (bus tidak tersedia) — API identik dengan bus."""

        def __init__(self):
            self.shake_strength = 0.0
            self.shake_duration = 0.0
            self._max_duration = 0.0001
            self.enabled = True

        def add(self, strength, duration=0.22):
            if strength <= self.shake_strength and \
                    duration <= self.shake_duration:
                return
            self.shake_strength = max(self.shake_strength, float(strength))
            self.shake_duration = max(self.shake_duration, float(duration))
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
            if self.shake_duration <= 0.0:
                return 0.0
            return self.shake_strength * (self.shake_duration
                                          / self._max_duration)

        def offset(self):
            amt = self.amount
            if amt <= 0.4:
                return (0, 0)
            return (random.uniform(-amt, amt), random.uniform(-amt, amt))

    class HitStop:                         # noqa: F811
        MIN_SECONDS = 0.03
        MAX_SECONDS = 0.08

        def __init__(self):
            self.frames = 0
            self.total = 0

        def trigger(self, seconds=0.045):
            if not HIT_STOP_ENABLED:
                return
            seconds = max(self.MIN_SECONDS,
                          min(self.MAX_SECONDS, float(seconds)))
            frames = max(1, int(round(seconds / FIXED_DT)))
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

    HITSTOP = HitStop()
    SHAKE = ScreenShake()


def hit_stop(seconds=0.045):
    """API publik: minta hit-stop global (dijepit 0.03 - 0.08 s)."""
    if _feel is not None:
        _feel.hit_stop(seconds)
    else:                                  # pragma: no cover
        HITSTOP.trigger(seconds)


def should_freeze_frame():
    """Dipanggil ``Game.update``: True kalau frame simulasi dibekukan.

    Flag ``GRIMJAW_FX_ENABLED`` TIDAK menahan freeze karakter lain — ia
    hanya mengatur apakah FX Grimjaw sendiri ikut jalan.
    """
    if _feel is not None:
        return _feel.should_freeze_frame()
    if not HIT_STOP_ENABLED:               # pragma: no cover
        return False
    return HITSTOP.consume_frame()


def shake(strength=5.0, duration=0.22):
    """API publik: guncangkan layar (bus bersama + EffectManager)."""
    if not shake_allowed():
        return
    if _feel is not None:
        _feel.shake(strength, duration)
        return
    SHAKE.add(strength, duration)          # pragma: no cover
    try:
        import __main__
        game = getattr(__main__, "game_instance", None)
        if game is not None and getattr(game, "effects", None) is not None:
            game.effects.shake_screen(strength)
    except Exception:                      # pragma: no cover
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

#: Fase timeline serangan (fraksi 0..1).  Batang-batang ini diambil dari
#: konstanta renderer (ATTACK_WINDUP_END=0.25, ATTACK_SWING_END=0.62)
#: supaya rig, trail, dan FX SELALU sepakat kapan tebasan mendarat.
#: ANTICIPATION -> WIND-UP -> SWING -> IMPACT -> FOLLOW THROUGH -> RECOVERY
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.12),
    ("WINDUP",       0.12, 0.25),
    ("SWING",        0.25, 0.55),
    ("IMPACT",       0.55, 0.68),
    ("FOLLOW",       0.68, 0.84),
    ("RECOVERY",     0.84, 1.00),
)

#: Titik pendaratan tebasan (progress) — dipakai untuk whoosh + hitbox.
ATTACK_SWING_END = 0.62


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
    global ATTACK_PHASES, ATTACK_SWING_END
    G = _renderer()
    if G is None:
        return
    try:
        windup = float(G.ATTACK_WINDUP_END)
        swing_end = float(G.ATTACK_SWING_END)
    except Exception:                      # pragma: no cover
        return
    if not (0.05 < windup < swing_end < 1.0):
        return
    ATTACK_SWING_END = swing_end
    mid_swing = windup + (swing_end - windup) * 0.75
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, windup * 0.48),
        ("WINDUP",       windup * 0.48, windup),
        ("SWING",        windup, mid_swing),
        ("IMPACT",       mid_swing, swing_end + 0.06),
        ("FOLLOW",       swing_end + 0.06, swing_end + 0.22),
        ("RECOVERY",     swing_end + 0.22, 1.00),
    )


_resolve_timeline()


# ============================================================================
# 12.  GEOMETRI BILAH  —  jembatan ke pose renderer (satu sumber kebenaran)
# ============================================================================

def render_scale(hero):
    """Skala canvas->layar untuk hero ini (fallback: skala pipeline)."""
    scale = float(getattr(hero, "_render_scale", 0.0) or 0.0)
    if scale <= 0.02:
        try:
            from heroes import _get_hero_scale
            scale = float(_get_hero_scale(
                getattr(hero, "hero_type", "grimjaw")))
        except Exception:                  # pragma: no cover
            scale = 1.0
    return scale


def blade_points(hero, x=None, y=None):
    """Posisi layar (grip, tip) bilah Grimjaw dari pose renderer.

    Memakai geometri lokal renderer lalu dikonversi ke skala layar,
    sehingga trail menempel PERSIS di pedang — bukan di perkiraan.
    Return ((gx, gy), (tx, ty), action).
    """
    G = _renderer()
    h = hero
    px = float(getattr(h, "x", 0.0)) if x is None else float(x)
    py = float(getattr(h, "y", 0.0)) if y is None else float(y)
    f = 1.0 if getattr(h, "facing", 1) >= 0 else -1.0
    s = render_scale(h)
    phase = float(getattr(h, "pulse", 0.0))
    ap = float(getattr(h, "_gj_attack_progress", 0.0))
    spin = float(getattr(h, "pulse", 0.0)) * 6.0

    if getattr(h, "_blade_fury_timer", 0) > 0:
        action = "spin"
        ap = 0.0
    elif getattr(h, "_gj_attack_active", False):
        action = "attack"
        spin = 0.0
    elif getattr(h, "_moving_cached", False):
        action = "walk"
    else:
        action = "idle"

    if G is not None:
        try:
            grip_l = G._blade_grip_local(action, ap, phase)
            tip_l = G._blade_tip_local(phase, action, ap, spin)
        except Exception:                  # pragma: no cover - tool minimal
            grip_l, tip_l = (17, 3), (17, -49)
    else:                                  # pragma: no cover
        grip_l, tip_l = (17, 3), (17, -49)

    grip = (px + grip_l[0] * f * s, py + grip_l[1] * s)
    tip = (px + tip_l[0] * f * s, py + tip_l[1] * s)
    return grip, tip, action


# ============================================================================
# 13.  DIRECTOR  —  satu per unit Grimjaw
# ============================================================================

class GrimjawFXDirector:
    """Mengikat semua subsistem FX untuk satu instance Grimjaw.

    Director adalah animation controller + event bus FX:
      * state machine berprioritas (IDLE..DEATH) dengan delta-time,
      * deteksi edge (attack / skill / hurt / death) dari atribut hero,
      * trail dari posisi bilah NYATA,
      * partikel, proyektil, impact, SkillFX, shake, hit-stop.
    """

    def __init__(self, hero):
        _sync_palette()
        self.hero = hero
        self.particles = ParticleSystem(MAX_PARTICLES)
        self.projectiles = ProjectileSystem(self.particles)
        self.trail = SwingTrail()
        self.impacts = []
        self.skills = []
        self.state = "IDLE"
        self.prev_state = "IDLE"
        self.state_time = 0.0
        self.anim_phase = "IDLE"
        self.swing_active = False
        self._swing_seen = False
        self._blade_landed = False
        self._skill_seen = None
        self._fury_seen = 0
        self._ward_seen = 0
        self._crit_seen = 0
        self._omni_seen = 0
        self._fury_prev = 0
        self._omni_prev = 0
        self._fury_tick_count = 0
        self._omni_tick_count = 0
        self._fury_last = 0
        self._crit_last = 0
        self._fury_stuck = 0.0
        self._crit_stuck = 0.0
        self._last_hp = None
        self._was_alive = True
        self._last_x = None
        self._last_y = None
        self._moving = False
        self._emit_acc = 0.0
        self._emit_ward = 0.0
        self._emit_crit = 0.0
        self.hit_flash = 0.0
        self.time = 0.0
        self.frames = 0

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def on_swing_start(self, x, y, facing):
        """Awal ayunan: reset trail + debu antisipasi + smoke belakang."""
        self.trail.reset()
        self.trail.spin_mode = False
        self.swing_active = True
        self._blade_landed = False
        self.particles.burst(
            x - facing * 6, y + 40, 2,
            speed=(30, 90), life=(0.2, 0.4), size=(2, 4),
            colors=(P["dust"], P["ash"]),
            spread=1.1, direction=math.pi if facing > 0 else 0.0,
            gravity=90.0, drag=2.6, shape="pixel", back=True)
        self.particles.burst(
            x, y + 34, 4,
            speed=(18, 52), life=(0.35, 0.6), size=(3, 6),
            colors=(P["smoke"], P["ash"]),
            spread=1.6, direction=0.0, gravity=-24.0, drag=1.8,
            shape="smoke", back=True)

    def on_swing_end(self):
        self.swing_active = False
        self.trail.spin_mode = False

    def on_blade_land(self, x, y, facing, crit=False):
        """Pedang MENDARAT (ujung ayunan) — whoosh pop walau tidak kena.

        Hit nyata punya paket lengkap lewat notify_melee_impact; whoosh
        ini menjaga supaya serangan yang meleset tetap terasa berbobot.
        """
        if len(self.impacts) >= 8:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(
            x + facing * 30, y + 16, math.atan2(0.35, facing),
            0.55, crit=crit, kind="crit" if crit else "blade"))
        self.particles.burst(
            x + facing * 30, y + 18, 3,
            speed=(60, 170), life=(0.16, 0.34), size=(1, 3),
            colors=(P["fx_light"], P["ember"]),
            spread=1.5, direction=math.atan2(0.2, facing), drag=3.4,
            shape="streak")
        shake(1.3, 0.14)

    def on_cast(self, x, y, skill):
        """Skill dilepas: buat SkillFX + bahasa per-skill + shake."""
        if len(self.skills) >= 3:
            self.skills.pop(0)
        radius = None
        if skill == "q":
            try:
                radius = float(getattr(self.hero, "skill_range", 0)) or None
            except Exception:              # pragma: no cover
                radius = None
        fx = SkillFX(skill, x, y, self.particles, radius)
        self.skills.append(fx)

        if skill == "q":
            # Q Blade Fury: ledakan bara awal + recoil dust
            self.particles.burst(x, y - 6, 7,
                                 speed=(120, 300), life=(0.25, 0.5),
                                 size=(2, 4),
                                 colors=(P["fx_light"], P["fx_hot"],
                                         P["fx_white"]),
                                 drag=3.0, shape="streak")
            self.particles.burst(x, y + 8, 4,
                                 speed=(40, 120), life=(0.4, 0.8),
                                 size=(3, 6), colors=(P["smoke"], P["ash"]),
                                 gravity=-30.0, drag=1.6, shape="smoke",
                                 back=True)
            self.trail.reset()
            self.trail.spin_mode = True
            shake(3.0, 0.26)
            hit_stop(0.027)
        elif skill == "w":
            # W Healing Ward: kelopak hijau lembut dari titik ward
            shake(1.0, 0.14)
        elif skill == "e":
            # E Critical Strike: suatan emas + 3 gelombang bilah ke depan
            f = 1.0 if getattr(self.hero, "facing", 1) >= 0 else -1.0
            self.particles.burst(x, y - 14, 6,
                                 speed=(150, 330), life=(0.2, 0.42),
                                 size=(2, 4),
                                 colors=(P["gold_hot"], P["gold"],
                                         P["fx_white"]),
                                 spread=0.9, direction=0.0 if f > 0
                                 else math.pi, drag=3.2, shape="streak")
            tgt = getattr(self.hero, "target", None)
            for i, spread_i in enumerate((-0.34, 0.0, 0.34)):
                base_a = (0.0 if f > 0 else math.pi) + spread_i
                dist = 150.0
                tx = x + math.cos(base_a) * dist
                ty = y + math.sin(base_a) * dist * 0.5
                self.projectiles.spawn(
                    x + f * 14, y - 14, tx, ty,
                    speed=430.0 + i * 26.0, target=tgt,
                    radius=7.0 + (1 if i == 1 else 0),
                    kind="wave",
                    on_impact=self._wave_impact)
            shake(2.0, 0.18)
            hit_stop(0.024)
        elif skill == "r":
            # R Omnislash: pilar rage + nova + shard + gelombang pembuka
            self.particles.burst(x, y - 10, 9,
                                 speed=(140, 360), life=(0.25, 0.55),
                                 size=(2, 5),
                                 colors=(P["rage_bright"], P["rage_light"],
                                         P["fx_white"]),
                                 drag=2.8, shape="streak")
            self.particles.burst(x, y - 10, 5,
                                 speed=(60, 180), life=(0.4, 0.8),
                                 size=(2, 5),
                                 colors=(P["rage_light"], P["rage_dark"]),
                                 gravity=380.0, drag=1.0, shape="shard",
                                 rotation_speed=(-16.0, 16.0))
            tgt = getattr(self.hero, "target", None)
            if tgt is not None and getattr(tgt, "alive", False):
                self.projectiles.spawn(
                    x, y - 16, float(tgt.x), float(tgt.y) - 10,
                    speed=520.0, target=tgt, radius=9.0, kind="bolt",
                    on_impact=self._wave_impact)
            shake(4.0, 0.42)
            hit_stop(0.040)

    def _wave_impact(self, proj):
        """Callback projectile: paket impact di titik benturan."""
        if len(self.impacts) >= 8:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(
            proj.hit_pos.x, proj.hit_pos.y, proj.rotation,
            0.8, crit=proj.kind != "wave",
            kind="crit" if proj.kind != "wave" else "blade"))
        self.particles.burst(
            proj.hit_pos.x, proj.hit_pos.y, 4,
            speed=(110, 280), life=(0.18, 0.4), size=(2, 4),
            colors=(P["fx_white"], P["fx_hot"], P["fx_light"]),
            spread=2.2, direction=proj.rotation, drag=3.4, shape="streak")

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="blade"):
        """Benturan mengenai target: flash, spark, debris, shake, hit-stop."""
        if len(self.impacts) >= 8:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind))

        n = int(9 + 7 * min(2.0, power)) + (6 if crit else 0)
        self.particles.burst(
            x, y, n, speed=(120, 340), life=(0.18, 0.44),
            size=(2, 4),
            colors=(P["fx_white"], P["fx_hot"], P["fx_bright"]),
            spread=2.4, direction=angle, drag=3.6, shape="streak")
        self.particles.burst(
            x, y, 6 + (4 if crit else 0),
            speed=(70, 190), life=(0.3, 0.65), size=(2, 5),
            colors=(P["fx_light"], P["ash"], P["gold_hot"]),
            gravity=480.0, drag=1.1, shape="shard",
            rotation_speed=(-16.0, 16.0))
        self.particles.burst(
            x, y, 4,
            speed=(24, 70), life=(0.35, 0.6), size=(3, 6),
            colors=(P["smoke"], P["ash"]),
            gravity=-30.0, drag=1.6, shape="smoke", back=True)

        shake(4.0 + 3.5 * min(2.0, power) + (3.0 if crit else 0.0),
              0.18 + 0.08 * min(2.0, power))
        hit_stop(0.038 + 0.02 * min(1.5, power) + (0.015 if crit else 0.0))

    def on_fury_tick(self, x, y):
        """Satu tick damage Blade Fury: cincin sapuan + bara radial."""
        self._fury_tick_count += 1
        if len(self.impacts) >= 8:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(
            x, y - 14, random.random() * math.tau, 0.8,
            kind="spin"))
        self.particles.burst(
            x, y - 12, 5,
            speed=(150, 320), life=(0.2, 0.45), size=(2, 4),
            colors=(P["fx_light"], P["fx_hot"], P["ember"]),
            spread=math.tau, drag=2.8, shape="ember",
            rotation_speed=(-10.0, 10.0))
        shake(1.2, 0.14)
        # hit-stop hanya tiap tick ke-3: 12 tick × 0.03 s akan membuat
        # game patah-patah; tick biasa cukup shake.
        if self._fury_tick_count % 3 == 0:
            hit_stop(0.020)

    def on_omni_strike(self, x, y):
        """Satu tebasan Omnislash mengenai target yang terkunci."""
        self._omni_tick_count += 1
        if len(self.impacts) >= 10:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(
            x, y - 12, random.uniform(-2.6, -0.6), 1.2,
            kind="omni"))
        self.particles.burst(
            x, y - 12, 4,
            speed=(140, 330), life=(0.16, 0.36), size=(2, 4),
            colors=(P["rage_bright"], P["fx_white"], P["rage_light"]),
            spread=2.6, drag=3.4, shape="streak")
        shake(2.5, 0.16)
        hit_stop(0.020)

    def on_hurt(self, amount=1.0):
        """Grimjaw terkena serangan: hit flash + percikan bara."""
        self.hit_flash = 0.16
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        self.particles.burst(
            hx, hy - 10, 3, speed=(80, 210), life=(0.2, 0.4),
            size=(2, 4), colors=(P["fx_light"], P["ember"]),
            drag=3.0, shape="streak")

    def on_death(self):
        """Grimjaw tumbang: bara padam + asap + debu besar."""
        h = self.hero
        x = float(getattr(h, "x", 0.0))
        y = float(getattr(h, "y", 0.0))
        self.particles.burst(
            x, y - 12, 8, speed=(60, 220), life=(0.4, 0.9),
            size=(2, 5), colors=(P["ember"], P["fx_light"]),
            gravity=240.0, drag=1.4, shape="ember",
            rotation_speed=(-9.0, 9.0))
        self.particles.burst(
            x, y, 5, speed=(30, 90), life=(0.6, 1.1), size=(4, 8),
            colors=(P["smoke"], P["ash"]), gravity=-36.0, drag=1.2,
            shape="smoke", back=True)
        shake(3.0, 0.3)

    # ------------------------------------------------------------------
    # State machine (prioritas + transisi)
    # ------------------------------------------------------------------
    def _resolve_state(self):
        h = self.hero
        if not getattr(h, "alive", True):
            return "DEATH"
        if self.hit_flash > 0.0:
            return "HURT"
        if getattr(h, "_omnislash_timer", 0) > 0 or \
                getattr(h, "active_skill", None) == "r":
            return "SPECIAL"
        if getattr(h, "_blade_fury_timer", 0) > 0 or \
                getattr(h, "_heal_ward_timer", 0) > 0 or \
                getattr(h, "active_skill", None) in ("q", "w", "e"):
            return "SKILL"
        if getattr(h, "_crit_buff_timer", 0) > 0 and self.swing_active:
            return "CAST"
        if getattr(h, "_gj_attack_active", False):
            prog = float(getattr(h, "_gj_attack_progress", 0.0))
            ph = attack_phase(prog)
            if ph in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            if ph in ("SWING", "IMPACT"):
                return "SWING"
            return "ATTACK"
        if self._moving:
            spd = float(getattr(h, "speed", 1.0))
            return "RUN" if spd >= 2.2 else "WALK"
        return "IDLE"

    def _update_state(self, dt):
        want = self._resolve_state()
        if want != self.state:
            # transisi hanya kalau prioritas >= state sekarang, atau
            # state sekarang sudah tidak lagi mengunci (bukan DEATH).
            cur_p = ANIM_PRIORITY.get(self.state, 0)
            new_p = ANIM_PRIORITY.get(want, 0)
            locked = self.state in ("DEATH",)
            if not locked and (new_p >= cur_p or self.state_time > 0.05):
                self.prev_state = self.state
                self.state = want
                self.state_time = 0.0
        self.state_time += dt
        self.anim_phase = attack_phase(
            float(getattr(self.hero, "_gj_attack_progress", 0.0)))

    # ------------------------------------------------------------------
    # Update / draw
    # ------------------------------------------------------------------
    def update(self, dt):
        self.time += dt
        self.frames += 1
        h = self.hero

        # ── deteksi gerak sendiri (lebih akurat daripada _moving_cached
        #    yang hanya diperbarui saat cache sprite miss) ─────────────
        hx = float(getattr(h, "x", 0.0))
        hy = float(getattr(h, "y", 0.0))
        if self._last_x is not None:
            self._moving = (abs(hx - self._last_x) +
                            abs(hy - self._last_y)) > 0.3
        self._last_x = hx
        self._last_y = hy

        # ── deteksi kena damage untuk HURT ────────────────────────────
        hp = getattr(h, "hp", None)
        if hp is not None:
            if self._last_hp is not None and hp < self._last_hp - 0.01:
                self.on_hurt((self._last_hp - hp) /
                             max(1.0, getattr(h, "max_hp", 1.0)))
            self._last_hp = hp

        # ── deteksi kematian ──────────────────────────────────────────
        alive = bool(getattr(h, "alive", True))
        if self._was_alive and not alive:
            self.on_death()
        self._was_alive = alive

        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)

        self._update_state(dt)

        # ── skill cast detection (edge-triggered, dua sumber) ─────────
        # active_skill = jendela visual pipeline; timer mentah = jendela
        # gameplay.  Edge pada salah satunya cukup untuk memicu cast.
        skill = getattr(h, "active_skill", None)
        if skill != self._skill_seen:
            if skill:
                self.on_cast(hx, hy + 16, skill)
            self._skill_seen = skill

        fury = int(getattr(h, "_blade_fury_timer", 0) or 0)
        if fury > self._fury_seen and self._fury_seen == 0:
            self.on_cast(hx, hy + 16, "q")
        self._fury_seen = fury

        ward = int(getattr(h, "_heal_ward_timer", 0) or 0)
        if ward > self._ward_seen and self._ward_seen == 0:
            wx, wy = getattr(h, "_heal_ward_pos", (hx, hy))
            self.on_cast(float(wx), float(wy) + 12, "w")
        self._ward_seen = ward

        crit_t = int(getattr(h, "_crit_buff_timer", 0) or 0)
        if crit_t > self._crit_seen and self._crit_seen == 0:
            self.on_cast(hx, hy + 16, "e")
        self._crit_seen = crit_t

        omni = int(getattr(h, "_omnislash_timer", 0) or 0)
        if omni > self._omni_seen and self._omni_seen == 0:
            self.on_cast(hx, hy + 16, "r")
        self._omni_seen = omni

        # ── tick damage skill (persilangan kelipatan timer) ───────────
        # Gameplay men-trigger damage saat timer % 15 == 0 (Q) dan
        # timer % 8 == 0 (R).  FX menggambar impact di tick yang sama.
        if fury > 0 and self._fury_prev is not None and fury < self._fury_prev:
            for t in range(fury + 1, self._fury_prev + 1):
                if t % 15 == 0:
                    self.on_fury_tick(hx, hy)
                    break
        self._fury_prev = fury

        if omni > 0 and self._omni_prev is not None and \
                omni < self._omni_prev:
            for t in range(omni + 1, self._omni_prev + 1):
                if t % 8 == 0:
                    tgt = getattr(h, "_omnislash_target", None)
                    tx = float(getattr(tgt, "x", hx))
                    ty = float(getattr(tgt, "y", hy))
                    self.on_omni_strike(tx, ty)
                    break
        self._omni_prev = omni

        # ── swing detection (edge-triggered pada fase SWING) ──────────
        swinging = getattr(h, "_gj_attack_active", False) and \
            self.anim_phase in ("SWING", "IMPACT", "FOLLOW")
        if swinging and not self._swing_seen:
            self.on_swing_start(hx, hy,
                                1 if getattr(h, "facing", 1) >= 0 else -1)
        elif not swinging and self._swing_seen:
            self.on_swing_end()
        self._swing_seen = swinging

        # ── pendaratan bilah (whoosh pop) ─────────────────────────────
        ap = float(getattr(h, "_gj_attack_progress", 0.0))
        if swinging and not self._blade_landed and ap >= ATTACK_SWING_END:
            self._blade_landed = True
            self.on_blade_land(hx, hy,
                               1 if getattr(h, "facing", 1) >= 0 else -1,
                               crit=bool(getattr(h, "_gj_crit_active",
                                                 False)))

        # ── rekam posisi bilah saat swing/spin -> trail ───────────────
        # Pagar anti-beku: timer gameplay SELALU berkurang tiap langkah
        # simulasi.  Kalau hero tewas di tengah skill, ``Hero.update``
        # berhenti jalan dan timer membeku > 0 — tanpa pagar ini, emisi
        # bara/trail akan hidup tanpa batas di mayat.  Setelah 15 s tanpa
        # penurunan (mustahil di gameplay sehat), emisi dihentikan.
        alive_ok = bool(getattr(h, "alive", True))
        if fury <= 0 or fury < self._fury_last:
            self._fury_stuck = 0.0
        else:
            self._fury_stuck += dt
        self._fury_last = fury
        fury_live = fury > 0 and alive_ok and self._fury_stuck < 15.0
        if crit_t <= 0 or crit_t < self._crit_last:
            self._crit_stuck = 0.0
        else:
            self._crit_stuck += dt
        self._crit_last = crit_t
        crit_live = crit_t > 0 and alive_ok and self._crit_stuck < 15.0

        tracing = alive_ok and (swinging or fury_live or omni > 0)
        if tracing:
            grip, tip, action = blade_points(h)
            # pita hanya menempati sepertiga LUAR bilah
            inner = (grip[0] + (tip[0] - grip[0]) * 0.42,
                     grip[1] + (tip[1] - grip[1]) * 0.42)
            outer = (grip[0] + (tip[0] - grip[0]) * 1.14,
                     grip[1] + (tip[1] - grip[1]) * 1.14)
            self.trail.push(inner, outer)

        # ── emisi kontinu: bara mane saat fury, emas saat crit buff ───
        if fury_live:
            self._emit_acc += dt
            if self._emit_acc >= 0.05:
                self._emit_acc = 0.0
                self.particles.spawn(
                    hx + random.uniform(-10, 10),
                    hy - random.uniform(8, 40),
                    random.uniform(-24, 24), -random.uniform(30, 80),
                    random.uniform(0.4, 0.8), random.uniform(1.5, 3.0),
                    P["ember"], color_end=P["fx_dark"], drag=0.8,
                    shape="ember", rotation=random.random() * math.tau,
                    rotation_speed=random.uniform(-8, 8))
        if crit_live:
            self._emit_crit += dt
            if self._emit_crit >= 0.09:
                self._emit_crit = 0.0
                g2, t2, _a = blade_points(h)
                self.particles.spawn(
                    t2[0], t2[1],
                    random.uniform(-30, 30), -random.uniform(20, 70),
                    random.uniform(0.3, 0.6), random.uniform(1.5, 2.5),
                    P["gold_hot"], color_end=P["blood"], drag=1.4,
                    shape="ember", rotation=random.random() * math.tau,
                    rotation_speed=random.uniform(-8, 8))

        self.trail.update(dt)
        self.particles.update(dt)
        self.projectiles.update(dt)

        if self.impacts:
            self.impacts = [i for i in self.impacts if i.update(dt)]
        if self.skills:
            self.skills = [s for s in self.skills if s.update(dt)]

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
        r = int(18 + 26 * (self.hit_flash / 0.16))
        g = glow_surface(r, P["fx_hot"], self.hit_flash / 0.16 * 0.7)
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
    rng = int(getattr(h, "range", 60))

    # attack range
    pygame.draw.circle(surface, (255, 140, 60), (x, y), rng, 1)
    # hurtbox
    pygame.draw.circle(surface, (90, 220, 255), (x, y), rad, 1)
    # hitbox serangan (kerucut depan saat swing)
    if director.anim_phase in ("SWING", "IMPACT"):
        f = 1 if getattr(h, "facing", 1) >= 0 else -1
        pygame.draw.rect(surface, (255, 230, 90),
                         pygame.Rect(x if f > 0 else x - rng,
                                     y - 30, rng, 58), 1)
    # radius Blade Fury
    if int(getattr(h, "_blade_fury_timer", 0) or 0) > 0:
        try:
            fr = int(getattr(h, "skill_range", 0) or 70)
        except Exception:                  # pragma: no cover
            fr = 70
        pygame.draw.circle(surface, (255, 90, 60), (x, y), fr, 1)
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
        "GRIMJAW  %s / %s" % (st["state"], st["phase"]),
        "atkT %.2f  skill %s" % (
            float(getattr(h, "_gj_attack_progress", 0.0)),
            getattr(h, "active_skill", None)),
        "fury %d  ward %d  crit %d  omni %d" % (
            int(getattr(h, "_blade_fury_timer", 0) or 0),
            int(getattr(h, "_heal_ward_timer", 0) or 0),
            int(getattr(h, "_crit_buff_timer", 0) or 0),
            int(getattr(h, "_omnislash_timer", 0) or 0)),
        "part %d  proj %d  imp %d" % (
            st["particles"], st["projectiles"], st["impacts"]),
        "shake %.1f  stop %d  fps %d" % (
            SHAKE.amount, HITSTOP.frames, fps),
    ]
    for i, txt in enumerate(lines):
        img = font.render(txt, True, (255, 220, 180))
        surface.blit(img, (x - 60, y - 96 + i * 13))


# ============================================================================
# 15.  API MODUL  —  registry, tick, hook render
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Grimjaw."""
    _sync_palette()
    d = getattr(hero, "_gj_fx", None)
    if d is None:
        d = GrimjawFXDirector(hero)
        try:
            hero._gj_fx = d
        except Exception:                  # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:           # jangkar tua dibuang
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    """Lepas director dari registry DAN penanda milik-nya di unit.

    Penting: kalau penanda ``_gj_live_fx`` ditinggal sementara director
    sudah tidak dipanggil lagi, renderer akan terus MELEWATI smear api
    di-canvas padahal tidak ada yang menggantinya -> efek hilang total.
    """
    try:
        if director.hero is not None:
            director.hero._gj_fx = None
            director.hero._gj_live_fx = False
    except Exception:                      # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit ini (dipanggil renderer / pipeline).

    Sekalian menandai unit supaya renderer TIDAK menggambar efek yang
    sekarang dimiliki lapisan hidup (smear ayunan di-canvas).  Return
    True kalau lapisan hidup jadi dipakai.
    """
    if not GRIMJAW_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                      # pragma: no cover
        return False
    try:
        hero._gj_live_fx = True
    except Exception:                      # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini.

    Dipakai renderer untuk memutuskan apakah smear ayunan di-canvas masih
    perlu digambar (fallback) atau tidak.  Unit tanpa director — potongan
    portrait, alat uji, renderer yang dipanggil langsung — tetap memakai
    jalur canvas lama, jadi tidak ada visual yang hilang kalau modul FX
    tidak tersedia.
    """
    if not getattr(hero, "_gj_live_fx", False):
        return False
    d = getattr(hero, "_gj_fx", None)
    # Penanda saja tidak cukup: director-nya harus masih TERDAFTAR.
    return d is not None and d in _DIRECTORS


def tick(dt=None):
    """Majukan waktu FX satu frame nyata.  Aman dipanggil berkali-kali.

    Delta-time dihitung oleh bus ``combat_feel`` (dijepit supaya lonjakan
    frame saat loading / alt-tab tidak melempar partikel ke luar layar,
    dilambatkan saat hit-stop, dan shake-nya hanya dimundurkan SEKALI per
    frame walau beberapa karakter ikut bertempur).
    """
    global _LAST_TICK_MS
    if dt is None:
        if _feel is not None:
            # Guard frame-sama: draw_ground_layer() memanggil tick() untuk
            # SETIAP unit, sedangkan loop di bawah melangkahkan SEMUA
            # director. Tanpa guard ini 4 Grimjaw di layar membuat FX maju
            # ~4x lebih cepat.
            now = pygame.time.get_ticks()
            if now == _LAST_TICK_MS:
                return 0.0                 # frame yang sama: sudah maju
            dt = _feel.fx_dt()
            _LAST_TICK_MS = now
        else:                              # pragma: no cover - fallback
            now = pygame.time.get_ticks()
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
                d.update(dt)
            except Exception:              # pragma: no cover - anti-gagal
                pass
    return dt


def reset_all():
    """Lepas & kosongkan SEMUA director (ganti level / keluar match)."""
    # BUG: tanpa `global`, baris `_LAST_TICK_MS = None` di bawah hanya
    # membuat variabel LOKAL yang langsung dibuang - jam frame modul
    # tidak pernah benar-benar direset. Akibatnya frame pertama match
    # berikutnya memakai selisih waktu dari match LAMA (bisa puluhan
    # detik), lalu trail & partikel Grimjaw melompat jauh di frame
    # pembuka. Pola yang benar sudah dipakai kaizen/sylara/vex_fx.
    global _LAST_TICK_MS
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()
    _LAST_TICK_MS = None


def total_particles():
    """Jumlah partikel Grimjaw hidup di seluruh arena (untuk HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def total_projectiles():
    """Jumlah proyektil visual Grimjaw hidup (untuk HUD perf)."""
    return sum(d.projectiles.count() for d in _DIRECTORS)


# --- hook yang dipanggil heroes/__init__.py --------------------------------

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: dipanggil SEBELUM sprite hero di-blit."""
    if not GRIMJAW_FX_ENABLED:
        return
    tick()
    director_for(hero).draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: dipanggil SETELAH sprite hero di-blit."""
    if not GRIMJAW_FX_ENABLED:
        return
    director_for(hero).draw_front(surface)


# --- hook yang dipanggil _entity.py ----------------------------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Serangan dasar melee Grimjaw mengenai target (damage instan)."""
    if not GRIMJAW_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except Exception:                      # pragma: no cover
        power = 1.0
    tx = float(getattr(target, "x", 0)) if target is not None else 0.0
    ty = float(getattr(target, "y", 0)) if target is not None else 0.0
    ang = math.atan2(float(getattr(hero, "y", 0.0)) - ty,
                     tx - float(getattr(hero, "x", 0.0)))
    director_for(hero).on_impact(tx, ty - 10, ang, power, crit, "blade")


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """Skill Grimjaw meledak di sebuah titik (dipakai tooling/audit)."""
    if not GRIMJAW_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    if len(d.skills) >= 3:
        d.skills.pop(0)
    d.skills.append(SkillFX(skill, x, y, d.particles, radius))


def notify_skill_cast(hero, skill):
    """Skill Grimjaw dilepas dari luar (auto-cast guard / tooling)."""
    if not GRIMJAW_FX_ENABLED or hero is None:
        return
    director_for(hero).on_cast(float(getattr(hero, "x", 0.0)),
                               float(getattr(hero, "y", 0.0)) + 16,
                               skill)


def notify_hurt(hero, amount=1.0):
    """Grimjaw terkena damage dari luar (tanpa menunggu watch hp)."""
    if not GRIMJAW_FX_ENABLED or hero is None:
        return
    director_for(hero).on_hurt(amount)
