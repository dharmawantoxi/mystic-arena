# ============================================================================
# heroes/kaizen_fx.py
# ----------------------------------------------------------------------------
# KAIZEN — COMBAT / GAME-FEEL ENGINE  (screen-space live layer)
#
# Badan Kaizen digambar lewat ``_NS_kaizen`` (heroes/_bundle.py) ke canvas
# yang DI-CACHE lalu di-scale oleh pipeline hero.  Artinya semua yang butuh
# gerak 60 fps sejati — smear katana, partikel, proyektil sabit angin,
# impact, guncangan layar — TIDAK boleh hidup di dalam canvas itu: hasilnya
# ikut terkunci pada kuantisasi pose (2 frame per pose) dan menyusut
# bersama sprite.  Modul ini adalah lapisan hidup tersebut: digambar
# langsung ke layar pada skala 1:1 tiap frame, dengan delta-time nyata.
#
# Pembagian kerja (sengaja, supaya tidak ada efek yang digambar 2x):
#
#   RENDERER (canvas, ter-cache)      MODUL INI (layar, hidup)
#   -----------------------------     -----------------------------------
#   rig + selout + rim light          smear katana dari histori tip nyata
#   bayangan kontak, platform angin   partikel (debu, daun, mote angin)
#   TELEGRAPH AOE E/R (100/150 px)    PROYEKTIL sabit angin (sistem nyata)
#   dinding W / funnel R / pilar E    IMPACT FX + flash + hit-stop + shake
#   pose, foot solver, napas          overlay DEBUG_CHARACTER
#
# 100% PROSEDURAL. Tidak ada PNG / JPG / GIF / sprite-sheet / loader gambar.
# Semua bentuk dibuat dengan pygame.draw + pygame.Surface + pygame.transform.
#
# Isi modul
#   KAIZEN_PALETTE      palette khusus karakter (kontrak 9 kunci + ramp)
#   Particle            partikel penuh (acc, gravity, rotasi, fade, drag)
#   ParticleSystem      pool + burst + stream + cap, reusable
#   SwingTrail          weapon trail prosedural dari histori posisi katana
#   ImpactFX            flash + shockwave + slash fragment + debris
#   KaizenProjectile    sabit angin modular (spawn->travel->hit->destroy)
#   ProjectileSystem    manajer proyektil
#   SkillFX             lifecycle FX skill (cast->charge->release->fade)
#   KaizenFXDirector    satu instance per unit, mengikat semua di atas
#   draw_debug_overlay  hitbox/hurtbox/state/frame/FPS/particle/skill/timer
#   API modul           tick / reset_all / notify_* / draw_*_layer
# ============================================================================

import math
import random

import pygame

try:                        # bus game-feel bersama (zephyr/gornak/grimjaw)
    from heroes import combat_feel as _feel
except Exception:           # pragma: no cover - build minimal
    _feel = None


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual untuk karakter KAIZEN: hitbox, hurtbox, jangkauan, state
#: animasi, frame, FPS, jumlah partikel, state skill, timer serangan.
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah (badan tetap jalan).
KAIZEN_FX_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 96

#: Batas keras proyektil visual per director.
MAX_PROJECTILES = 8

#: Panjang histori trail senjata (jumlah sample posisi bilah).
TRAIL_SAMPLES = 8

#: Batas dampak aktif per director & skill sekaligus di layar.
MAX_IMPACTS = 4
MAX_SKILLS = 2

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0

#: Kecepatan sabit angin (px/detik, ruang dunia).
SLASH_SPEED = 640.0

#: Radius EFEK di ruang dunia — E/R = radius gameplay sebenarnya
#: (hero_skills/kaizen_skills.py: E=100, R=150), Q/W = radius visual.
WORLD_RADIUS = {"q": 84.0, "w": 56.0, "e": 100.0, "r": 150.0}

#: Umur FX skill dalam DETIK.  Sinkron dengan
#: ``_NS_kaizen.SKILL_VISUAL_DURATION`` (60/90/60/100 langkah simulasi =
#: 1.00/1.50/1.00/1.67 s) plus sisa after-glow supaya efek tidak
#: "terpotong" saat pose skill selesai.
SKILL_TOTAL = {"q": 1.16, "w": 1.66, "e": 1.18, "r": 1.90}

#: Durasi pose per skill (frame) — dipakai untuk memetakan umur FX ke
#: fase yang sama dengan yang dibaca renderer.
SKILL_DUR = {"q": 60, "w": 90, "e": 60, "r": 100}


# ============================================================================
# 1.  PALETTE  —  wind-blade assassin: baja dingin + sian angin + delima saya
# ============================================================================

KAIZEN_PALETTE = {
    # ── kontrak palette karakter (9 kunci wajib) ────────────────────
    "outline":    (24,   26,  40),
    "shadow":     (16,   40,  82),
    "dark":       (30,   60, 110),
    "body":       (55,   80, 145),
    "mid":        (110, 175, 230),
    "light":      (175, 220, 250),
    "highlight":  (215, 240, 255),
    "weapon":     (210, 220, 235),
    "fx":         (245, 252, 255),

    # ── ramp angin (trail / sabit / impact) ─────────────────────────
    "fx_deepest": (10,   24,  56),
    "fx_deep":    (16,   40,  82),
    "fx_dark":    (30,   60, 110),
    "fx_mid":     (55,  110, 175),
    "fx_light":   (110, 175, 230),
    "fx_bright":  (175, 220, 250),
    "fx_pale":    (215, 240, 255),
    "fx_white":   (245, 252, 255),

    # ── baja katana (glint / serpihan bilah) ────────────────────────
    "steel_dark":  (90, 105, 125),
    "steel_mid":   (155, 170, 190),
    "steel_light": (210, 220, 235),
    "steel_shine": (245, 250, 255),

    # ── aksen delima (saya / ito) — kontras hangat satu-satunya ─────
    "saya":        (104,  27,  39),
    "saya_light":  (150,  46,  58),
    "cord":        (190,  55,  65),

    # ── materi lingkungan ───────────────────────────────────────────
    "dust":        (96,  92, 104),
    "dust_light":  (142, 138, 150),
    "smoke":       (52,  60,  86),
    "leaf":        (96,  150, 120),
    "leaf_dark":   (58,  104,  84),
    "white":       (255, 255, 255),
}

P = KAIZEN_PALETTE

#: Kunci palette live -> kunci palette renderer (_NS_kaizen.PALETTE).
_PALETTE_SYNC = {
    "fx_deepest": "wind_deep",
    "fx_deep":    "wind_deep",
    "fx_dark":    "wind_darkest",
    "fx_mid":     "wind_dark",
    "fx_light":   "wind_mid",
    "fx_bright":  "wind_light",
    "fx_pale":    "wind_bright",
    "fx_white":   "wind_white",
    "steel_dark":  "steel_dark",
    "steel_mid":   "steel_mid",
    "steel_light": "steel_light",
    "steel_shine": "steel_shine",
    "saya":        "saya_mid",
    "saya_light":  "saya_light",
    "cord":        "cord_mid",
    "outline":     "ink",
}

_RENDERER = None
_PALETTE_SYNCED = False


def _renderer():
    """Ambil namespace renderer Kaizen (lazy, sekali saja)."""
    global _RENDERER
    if _RENDERER is None:
        try:
            from heroes._bundle import _NS_kaizen as G
            _RENDERER = G
        except Exception:                  # pragma: no cover - tool minimal
            _RENDERER = False
    return _RENDERER or None


def _sync_palette():
    """Salin warna tema dari ``_NS_kaizen.PALETTE`` sekali saja.

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


def crescent_surface(radius, color, depth=0.62, filled=False):
    """Bulan sabit angin — bentuk khas tebasan Kaizen (BUKAN lingkaran).

    ``filled=True`` menghasilkan sabit terisi 3-band (badan proyektil);
    ``filled=False`` menghasilkan sabit garis (fragmen tebasan).
    Menghadap +x (arah terbang) sebelum dirotasi pemanggil.
    """
    radius = max(4, int(radius))
    color = _clamp_color(color)
    depth = max(0.2, min(1.4, float(depth)))
    key = ("crescent", radius, color, round(depth, 2), bool(filled))
    surf = _SURF_CACHE.get(key)
    if surf is not None:
        return surf

    size = radius * 2 + 6
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    if filled:
        # sabit terisi: lingkaran penuh MINUS lingkaran offset (mask).
        body = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(body, (*color, 235), (c, c), radius)
        off = int(radius * (1.0 - depth * 0.55))
        pygame.draw.circle(body, (0, 0, 0, 0), (c - off, c),
                           int(radius * 0.92))
        # band dalam yang lebih terang
        hi = _mix(color, P["fx_white"], 0.45)
        band = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(band, (*hi, 235), (c, c), int(radius * 0.72))
        pygame.draw.circle(band, (0, 0, 0, 0),
                           (c - int(off * 0.9), c), int(radius * 0.70))
        body.blit(band, (0, 0))
        surf.blit(body, (0, 0))
        # tepi luar putih tipis (hard edge pixel-art)
        try:
            rect = pygame.Rect(c - radius, c - radius,
                               radius * 2, radius * 2)
            pygame.draw.arc(surf, (*P["fx_white"], 245), rect,
                            -math.pi * 0.42, math.pi * 0.42, 2)
        except (ValueError, pygame.error):        # pragma: no cover
            pass
    else:
        outer = pygame.Rect(c - radius, c - radius, radius * 2, radius * 2)
        off = int(radius * (1.0 - depth))
        inner = pygame.Rect(c - radius + off, c - radius,
                            radius * 2, radius * 2)
        try:
            pygame.draw.arc(surf, (*color, 235), outer, math.pi * 0.5,
                            math.pi * 1.5, max(2, radius // 4))
            pygame.draw.arc(surf, (*color, 200), inner, math.pi * 0.62,
                            math.pi * 1.38, max(1, radius // 6))
        except (ValueError, pygame.error):        # pragma: no cover
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
      pixel / spark / shard / streak / leaf / smoke / glow / mote
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
        self.color = P["fx_bright"]
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
            # belok tegak-lurus kecepatan -> gerak spiral khas angin
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

        if self.shape == "shard":
            # serpihan baja tajam yang berputar (debris tebasan)
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

        if self.shape == "leaf":
            # daun terbawa angin: wajik pipih yang berkepak
            fl = 0.55 + 0.45 * math.sin(self.rotation * 3.0)
            hh = max(1, int(sz * fl))
            ww = max(1, sz)
            ca = math.cos(self.rotation * 0.7)
            sa = math.sin(self.rotation * 0.7)
            tmp = _scratch(ww * 2 + 6, ww * 2 + 6)
            ox = oy = ww + 3
            pts = []
            for dx, dy in ((ww, 0), (0, hh), (-ww, 0), (0, -hh)):
                pts.append((ox + int(dx * ca - dy * sa),
                            oy + int(dx * sa + dy * ca)))
            pygame.draw.polygon(tmp, (*col, a), pts)
            pygame.draw.line(tmp, (*_mix(col, P["fx_deepest"], 0.4),
                                   int(a * 0.8)),
                             pts[0], pts[2], 1)
            surface.blit(tmp, (x - ox, y - oy))
            return

        if self.shape == "mote":
            # mote angin: titik terang + ekor kecil, additive
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
            # puffs debu lembut di lapisan belakang
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

        Gerbang anggaran dipasang di sini supaya emisi kontinu (bukan
        hanya burst) ikut turun saat 5 hero starter berbarengan.
        """
        budget = particle_budget()
        if budget <= 0.0:
            return None
        # Burst/stream callers already quantize their requested count via
        # _budgeted().  An explicit single spawn must stay deterministic;
        # probabilistic dropping here made a lone particle randomly return
        # None in tooling/tests and produced uneven trails on mobile.
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
        belokan spiral khas angin.  Jumlah partikel otomatis mengikuti
        anggaran kualitas perangkat.
        """
        count = _budgeted(count)
        if count <= 0:
            return 0
        colors = colors or (P["fx_bright"], P["fx_light"], P["fx_pale"])
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
                    back=back, swirl=swirl)
        finally:
            self._in_burst -= 1
        return n

    # ------------------------------------------------------------------
    def stream(self, x, y, tx, ty, count, life=(0.3, 0.6), size=(1, 3),
               colors=None, drag=1.2, shape="mote"):
        """Aliran partikel dari (x,y) menuju (tx,ty) — charge / hisap."""
        count = _budgeted(count)
        if count <= 0:
            return 0
        colors = colors or (P["fx_light"], P["fx_bright"])
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
# 6.  SWING TRAIL  —  weapon trail prosedural dari histori posisi katana
# ============================================================================

class SwingTrail:
    """Jejak katana Kaizen berbasis histori posisi (OLD POS ... CURRENT).

    Menyimpan pasangan (pangkal, tip) beberapa frame terakhir lalu
    menyusunnya jadi pita poligon translucent 3-band sian yang memudar
    + garis tepi putih 1-2 px (hard edge pixel-art).  Trail OTOMATIS
    mengikuti arah serangan karena bentuknya murni turunan dari lintasan
    busur bilah (arc-based), bukan lerp linear.

    Dibanding Grimjaw (api berat), pita Kaizen lebih TIPIS, lebih CEPAT
    pudar, dan intinya nyaris putih — bahasa iai: presisi, bukan bobot.
    """

    def __init__(self, samples=TRAIL_SAMPLES,
                 color_edge=None, color_core=None):
        self.samples = int(samples)
        self.points = []            # [[pangkal, tip, umur], ...]
        self.color_edge = color_edge or P["fx_mid"]
        self.color_core = color_core or P["fx_pale"]
        self.life = 0.20            # detik sebelum sample dibuang
        self.width_boost = 1.0
        self.storm_mode = False     # True saat R (pita lebih panas)
        self.active = False

    # ------------------------------------------------------------------
    def reset(self):
        """Kosongkan trail (dipanggil saat swing baru dimulai)."""
        self.points.clear()
        self.active = False
        self.storm_mode = False

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
        minx, maxx = int(min(xs)) - 6, int(max(xs)) + 6
        miny, maxy = int(min(ys)) - 6, int(max(ys)) + 6
        w = maxx - minx
        h = maxy - miny
        if w <= 0 or h <= 0 or w > 1400 or h > 1400:
            return

        buf = _scratch(w, h)

        def loc(v):
            return (int(v.x) - minx, int(v.y) - miny)

        hot = 1.22 if self.storm_mode else 1.0

        # ── lapis 1: selubung angin dalam (lebar penuh, sian gelap) ──
        for i in range(n - 1):
            g0, t0, a0 = self.points[i]
            g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(120 * self._quad_alpha(i, n) * fade *
                        self.width_boost)
            if alpha <= 4:
                continue
            pygame.draw.polygon(
                buf, (*P["fx_deep"], alpha),
                [loc(g0), loc(t0), loc(t1), loc(g1)])

        # ── lapis 2: badan angin (setengah lebar, dekat ujung) ───────
        for i in range(n - 1):
            g0, t0, a0 = self.points[i]
            g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(205 * self._quad_alpha(i, n) * fade * hot)
            if alpha <= 6:
                continue
            m0 = g0.lerp(t0, 0.55)
            m1 = g1.lerp(t1, 0.55)
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
            pygame.draw.line(buf, (*P["fx_white"], min(255, alpha)),
                             loc(t0), loc(t1), 2)

        surface.blit(buf, (minx, miny))


# ============================================================================
# 7.  IMPACT FX
# ============================================================================

class ImpactFX:
    """Satu kejadian benturan: flash, shockwave, slash fragment, debris.

    Semua digambar prosedural dan berumur pendek; tidak ada state yang
    hidup tanpa batas.  ``kind`` memilih bahasa benturan:
      * "slash" — tebasan katana (sabit + serpihan sian)
      * "crit"  — critical strike (putih panas + aksen delima)
      * "gale"  — pop Wind Wall / sapuan E (cincin horizontal)
      * "storm" — tick Tornado R (silang angin + pilar pendek)
    """

    __slots__ = ("x", "y", "angle", "power", "age", "duration",
                 "crit", "active", "color", "kind")

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="slash"):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = max(0.35, float(power))
        self.age = 0.0
        self.duration = 0.30 + 0.10 * min(2.0, self.power)
        self.crit = bool(crit) or kind == "crit"
        self.active = True
        self.kind = kind
        if kind == "crit":
            self.color = P["fx_white"]
        elif kind == "storm":
            self.color = P["fx_bright"]
        elif kind == "gale":
            self.color = P["fx_light"]
        else:
            self.color = P["fx_pale"] if not crit else P["fx_white"]

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
        if t < 0.22:
            ft = 1.0 - t / 0.22
            gr = int((5 + 8 * pw) * (0.5 + 0.5 * ft)) // 2 * 2 + 2
            surface.blit(glow_surface(gr, self.color, 0.5 * ft),
                         (x - gr, y - gr),
                         special_flags=pygame.BLEND_RGB_ADD)
            ln = (14 + 30 * pw) * ft
            fl = _scratch(int(ln * 2 + 8), int(ln * 2 + 8))
            c = int(ln + 4)
            for k in range(6):
                a = self.angle + k * math.pi / 3
                L = ln if k % 2 == 0 else ln * 0.45
                pygame.draw.line(
                    fl, (*P["fx_white"], int(240 * ft)), (c, c),
                    (c + int(math.cos(a) * L),
                     c + int(math.sin(a) * L)),
                    3 if k % 2 == 0 else 1)
            surface.blit(fl, (x - c, y - c))

        # ── 2. SHOCKWAVE — elips berarah (bukan lingkaran polos) ────
        rr = int((8 + 42 * pw) * (0.25 + 1.05 * t)) // 3 * 3
        th = max(1, int(4 * inv * pw))
        a = int(205 * inv * inv)
        if a > 6 and rr > 4:
            er = ellipse_ring_surface(rr, max(3, int(rr * 0.6)), th,
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
        if t < 0.55:
            st = 1.0 - t / 0.55
            r0 = int((6 + 18 * pw) * (0.3 + 1.1 * t))
            for i in range(4):
                ang = self.angle + i * math.pi / 4 + 0.19
                L = (6 + 14 * pw) * st * (1.0 if i % 2 else 0.55)
                pygame.draw.line(
                    surface, _clamp_color(
                        _mix(P["fx_dark"], P["fx_bright"], st)),
                    (x + int(math.cos(ang) * r0),
                     y + int(math.sin(ang) * r0)),
                    (x + int(math.cos(ang) * (r0 + L)),
                     y + int(math.sin(ang) * (r0 + L))),
                    2 if i % 2 else 1)

        # ── 4. SLASH FRAGMENT — 3 busur pecah searah tebasan ────────
        if t < 0.5 and self.kind in ("slash", "crit"):
            st = 1.0 - t / 0.5
            span = 0.55 + 0.5 * pw
            base_r = int(11 + 28 * pw * (0.4 + t))
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
            # aksen delima crit: silang pendek merah di inti
            if self.crit and t < 0.3:
                ct = 1.0 - t / 0.3
                Lc = int(8 + 10 * pw * ct)
                for da in (0.6, -0.6):
                    pygame.draw.line(
                        surface, (*P["cord"], int(200 * ct)),
                        (x - int(math.cos(self.angle + da) * Lc),
                         y - int(math.sin(self.angle + da) * Lc)),
                        (x + int(math.cos(self.angle + da) * Lc),
                         y + int(math.sin(self.angle + da) * Lc)), 1)

        # ── 4b. STORM — silang angin + pilar cahaya pendek ───────────
        if self.kind == "storm" and t < 0.5:
            st = 1.0 - t / 0.5
            ln = int((20 + 30 * pw) * st)
            for da in (math.pi / 4, -math.pi / 4):
                x0 = x - int(math.cos(self.angle + da) * ln)
                y0 = y - int(math.sin(self.angle + da) * ln)
                x1 = x + int(math.cos(self.angle + da) * ln)
                y1 = y + int(math.sin(self.angle + da) * ln)
                pygame.draw.line(surface, (*P["fx_white"],
                                           int(235 * st)),
                                 (x0, y0), (x1, y1), 3)
                pygame.draw.line(surface, (*P["fx_bright"],
                                           int(180 * st)),
                                 (x0, y0 + 1), (x1, y1 + 1), 1)
            hgt = int(36 * st)
            if hgt > 4:
                pl = _scratch(14, hgt + 4)
                pygame.draw.polygon(
                    pl, (*P["fx_light"], int(150 * st)),
                    [(7, hgt + 2), (7 - 3, 2), (7 + 3, 2)])
                surface.blit(pl, (x - 7, y - hgt - 18))

        # ── 4c. GALE — lengkung sapuan horizontal di ketinggian badan─
        if self.kind == "gale" and t < 0.45:
            st = 1.0 - t / 0.45
            rr = int((16 + 38 * pw) * (0.55 + 0.85 * t))
            buf_r = rr + 6
            buf = _scratch(buf_r * 2, buf_r)
            c, cy = buf_r, buf_r // 2
            rect = pygame.Rect(c - rr, cy - rr // 2, rr * 2, rr)
            try:
                pygame.draw.arc(buf, (*P["fx_pale"], int(220 * st)),
                                rect, math.pi, math.tau, 3)
                pygame.draw.arc(buf, (*P["fx_white"], int(170 * st)),
                                rect.inflate(-8, -4), math.pi,
                                math.tau, 1)
            except (ValueError, pygame.error):
                pass
            surface.blit(buf, (x - c, y - cy - 12))

        # ── 5. INTI benturan ─────────────────────────────────────────
        if t < 0.4:
            st = 1.0 - t / 0.4
            sz = int((4 + 8 * pw) * (0.5 + 0.5 * st)) // 2 * 2 + 2
            s = spark_surface(sz, self.color)
            s.set_alpha(int(255 * st))
            surface.blit(s, (x - sz - int(ca * 2), y - sz - int(sa * 2)))


# ============================================================================
# 8.  PROJECTILE SYSTEM  —  sabit angin (wind slash)
# ============================================================================

class KaizenProjectile:
    """Sabit angin — modular, vektor, delta-time.

    Kontrak atribut: position, velocity, speed, damage, lifetime,
    target, radius, rotation, trail, particles, active.

    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY.

    Catatan desain: damage tetap 0 untuk sabit visual — damage gameplay
    Kaizen sudah diterapkan langsung oleh ``hero_skills`` / jalur melee.
    Sistem ini tetap punya deteksi tumbukan penuh (radius vs target)
    supaya siklus hidupnya utuh dan bisa dipakai gameplay lain (callback
    ``on_impact``) tanpa mengubah keseimbangan hero.
    """

    STATE_TRAVEL = "travel"
    STATE_IMPACT = "impact"
    STATE_DEAD = "dead"

    def __init__(self, x, y, tx, ty, speed=SLASH_SPEED, damage=0,
                 target=None, radius=8.0, homing=3.4, kind="slash",
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
        self.max_lifetime = 1.5
        self.target = target
        self.radius = float(radius)
        self.rotation = math.atan2(self.velocity.y, self.velocity.x)
        self.trail = []                  # [[Vector2, umur], ...]
        self.trail_life = 0.20
        self.particles = particles       # ParticleSystem bersama
        self.active = True
        self.state = self.STATE_TRAVEL
        self.kind = kind                 # "slash" | "gale"
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
            if self._emit_acc >= 0.07:
                self._emit_acc = 0.0
                ang = self.rotation + math.pi + (random.random() - .5) * 0.9
                spd = random.uniform(20, 70)
                self.particles.spawn(
                    self.position.x, self.position.y,
                    math.cos(ang) * spd, math.sin(ang) * spd - 14,
                    random.uniform(0.16, 0.34),
                    random.uniform(1.5, 3.0),
                    P["fx_bright"] if random.random() < .5
                    else P["fx_light"],
                    color_end=P["fx_dark"], drag=2.8, shape="mote",
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
        """Trail pita -> glow -> badan sabit berarah -> inti -> glint."""
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
                    buf, (*P["fx_deep"], 120),
                    [(int(px) - minx, int(py) - miny) for px, py in poly])
                pygame.draw.lines(
                    buf, (*P["fx_bright"], 170), False,
                    [(int(pv.x) - minx, int(pv.y) - miny)
                     for pv, _a in self.trail], 2)
                surface.blit(buf, (minx, miny))

        if self.state == self.STATE_IMPACT:
            return

        draw_wind_slash(surface, self.position.x, self.position.y,
                        self.rotation, age=int(self.lifetime * 60),
                        gale=self.kind != "slash", radius=self.radius)


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
        pr = KaizenProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    def update(self, dt):
        if not self.projectiles:
            return
        self.projectiles = [p for p in self.projectiles if p.update(dt)]

    def draw(self, surface):
        for p in self.projectiles:
            p.draw(surface)


def draw_wind_slash(surface, px, py, angle=0.0, age=0, gale=False,
                    radius=8.0):
    """Renderer bersama sabit angin (dipakai projectile + tooling).

    Badan = sabit TERISI 3-band yang berputar mengikuti arah terbang,
    plus glow premultiplied, tepi putih, glint berputar di ujung, dan
    speed line di belakang.  Digambar ke scratch/cached lalu di-blit —
    tidak ada alokasi Surface per frame.
    """
    x, y = int(px), int(py)
    rad = max(4, int(radius))
    deg = int(math.degrees(angle)) // 10 * 10      # kuantisasi rotasi

    # glow di belakang (premultiplied, additive) — memberi bobot cahaya
    if glow_allowed():
        g = glow_surface(rad * 2, P["fx_light"] if gale else P["fx_mid"],
                         0.5)
        surface.blit(g, (x - rad * 2, y - rad * 2),
                     special_flags=pygame.BLEND_RGB_ADD)

    # badan sabit terisi (hard edge), diputar lalu di-cache
    key = ("slash_body", rad, bool(gale), deg)
    body = _SURF_CACHE.get(key)
    if body is None:
        base = crescent_surface(
            rad, P["fx_bright"] if gale else P["fx_light"],
            depth=0.72, filled=True)
        body = pygame.transform.rotate(base, -deg) if deg else base
        body = _cache_put(key, body)
    surface.blit(body, (x - body.get_width() // 2,
                        y - body.get_height() // 2))

    # speed line di belakang kepala sabit (pixel-art, murah)
    bx = x - int(math.cos(angle) * (rad + 4))
    by = y - int(math.sin(angle) * (rad + 4))
    pygame.draw.line(surface, _clamp_color(P["fx_bright"]),
                     (bx, by),
                     (bx - int(math.cos(angle) * rad * 1.4),
                      by - int(math.sin(angle) * rad * 1.4)), 1)

    # glint berputar di ujung sabit — deterministik, hidup, murah
    for k in range(2):
        a = angle + age * 0.26 + k * math.pi
        gx = x + int(math.cos(a) * (rad + 2))
        gy = y + int(math.sin(a) * (rad + 2) * 0.5)
        s = spark_surface(2, P["fx_white"] if k == 0 else P["steel_shine"])
        surface.blit(s, (gx - 3, gy - 3))


# ============================================================================
# 9.  SKILL FX  —  lifecycle cast -> charge -> release -> area -> fade
# ============================================================================

class SkillFX:
    """Efek skill Kaizen dengan lifecycle bertahap.

    CAST -> CHARGE -> RELEASE -> TRAVEL/AREA -> IMPACT -> AFTER -> FADE

    Q Steel Wind : sabit ganda + speed streak + debu lintasan.
    W Wind Wall  : tirai mote naik + swirl + spark defleksi.
    E Sweep      : cincin sapuan 100 px + daun terangkat + pilar tick.
    R Tornado    : debu orbit 150 px + daun tersedot + silang badai.

    Bentuk BESAR (dinding 3 lapis, funnel 5 lapis, marker AOE) tetap
    milik renderer canvas — modul ini menambah lapisan HIDUP 60 fps di
    atasnya, bukan menggambar ulang bentuk yang sama.
    """

    #: (charge, release, area, impact, after) dalam detik
    TIMELINE = {
        "q": (0.14, 0.10, 0.52, 0.16, 0.24),
        "w": (0.20, 0.12, 1.02, 0.12, 0.20),
        "e": (0.22, 0.12, 0.52, 0.16, 0.16),
        "r": (0.30, 0.16, 1.04, 0.18, 0.22),
    }

    RADIUS = WORLD_RADIUS

    def __init__(self, kind, x, y, particles=None, radius=None,
                 facing=1):
        _sync_palette()
        self.kind = kind if kind in self.TIMELINE else "q"
        self.x = float(x)
        self.y = float(y)
        self.facing = 1 if facing >= 0 else -1
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
        self._emit = 0.0
        self.seed = random.randint(0, 9999)

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

        self._emit += dt
        if self._emit < 0.08:
            return True
        self._emit = 0.0

        k = self.kind
        if self.phase == "charge":
            # CHARGE: angin tersedot ke pusat (mote spiral masuk)
            ps.stream(self.x + random.uniform(-self.radius, self.radius),
                      self.y + random.uniform(-self.radius * 0.4,
                                              self.radius * 0.4),
                      self.x, self.y - 8, 2,
                      colors=(P["fx_light"], P["fx_bright"]))
        elif self.phase == "release":
            pass  # burst dilakukan di on_cast (sekali, bukan per frame)
        elif self.phase == "area":
            if k == "w":
                # tirai mote naik di garis dinding depan
                wx = self.x + self.facing * 34
                ps.spawn(wx + random.uniform(-8, 8),
                         self.y + random.uniform(-24, 30),
                         self.facing * random.uniform(-6, 6),
                         -random.uniform(30, 70),
                         random.uniform(0.35, 0.7),
                         random.uniform(1.5, 3.0),
                         P["fx_bright"], color_end=P["fx_dark"],
                         drag=1.0, shape="mote",
                         swirl=random.uniform(-2.5, 2.5))
            elif k == "e":
                # daun & debu terangkat di tepi cincin sapuan
                ang = random.random() * math.tau
                rx = self.x + math.cos(ang) * self.radius
                ry = self.y + 30 + math.sin(ang) * self.radius * 0.5
                ps.spawn(rx, ry,
                         math.cos(ang + 1.2) * 40,
                         -random.uniform(30, 90),
                         random.uniform(0.4, 0.8),
                         random.uniform(2.0, 3.5),
                         P["leaf"] if random.random() < 0.5
                         else P["dust_light"],
                         color_end=P["leaf_dark"], gravity=110.0,
                         drag=1.2, shape="leaf",
                         rotation_speed=random.uniform(-9, 9))
            elif k == "r":
                # debu + daun orbit tersedot funnel (renderer punya badan)
                ang = random.random() * math.tau
                rr = self.radius * random.uniform(0.5, 1.0)
                rx = self.x + math.cos(ang) * rr
                ry = self.y + 30 + math.sin(ang) * rr * 0.5
                tang = ang + math.pi / 2
                spd = random.uniform(90, 170)
                ps.spawn(rx, ry,
                         math.cos(tang) * spd,
                         math.sin(tang) * spd * 0.5 -
                         random.uniform(30, 80),
                         random.uniform(0.5, 0.9),
                         random.uniform(2.0, 4.0),
                         P["fx_light"] if random.random() < 0.5
                         else P["leaf"],
                         color_end=P["fx_deep"], drag=0.6,
                         shape="leaf" if random.random() < 0.4
                         else "streak",
                         swirl=3.4,
                         rotation_speed=random.uniform(-10, 10))
            elif k == "q":
                # speed streak di sepanjang lintasan tebasan
                ps.spawn(self.x + self.facing * random.uniform(0, 60),
                         self.y + random.uniform(-16, 10),
                         self.facing * random.uniform(160, 300),
                         random.uniform(-16, 16),
                         random.uniform(0.12, 0.24),
                         random.uniform(1.5, 2.5),
                         P["fx_pale"], drag=2.4, shape="streak")
        return True

    # ------------------------------------------------------------------
    # Draw — ground (di bawah karakter) & front (di atas karakter)
    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        if not self.active:
            return
        t = self.age / self.total
        x, y = int(self.x), int(self.y)
        k = self.kind

        # kabut cahaya tanah lembut selama fase aktif (semua skill)
        if self.phase in ("charge", "release", "area"):
            r = int(self.radius * (0.5 if k in ("q", "w") else 0.9))
            gg = ground_glow_surface(max(12, r), P["fx_mid"],
                                     0.22 * (1.0 - t))
            surface.blit(gg, (x - gg.get_width() // 2,
                              y + 30 - gg.get_height() // 2),
                         special_flags=pygame.BLEND_RGB_ADD)

        if k == "q" and self.phase in ("release", "area"):
            # goresan lintasan tebasan di tanah (memudar)
            st = max(0.0, 1.0 - (self.age - self.t_charge) / 0.6)
            if st > 0.03:
                f = self.facing
                for i in range(3):
                    off = 8 + i * 16
                    ln = 22 - i * 5
                    pygame.draw.line(
                        surface, (*P["fx_dark"], int(140 * st)),
                        (x + f * off, y + 40 + i * 2),
                        (x + f * (off + ln), y + 40 + i * 2), 2)

        if k == "r" and self.phase in ("area", "impact"):
            # cincin debu berputar di kaki tornado (dua busur berlawanan)
            st = 1.0 - t
            rot = self.age * 3.2
            rr = int(self.radius * 0.66)
            buf = _scratch(rr * 2 + 8, rr + 8)
            c, cy = rr + 4, (rr + 8) // 2
            rect = pygame.Rect(c - rr, cy - rr // 2, rr * 2, rr)
            for k2 in range(2):
                a0 = rot + k2 * math.pi
                try:
                    pygame.draw.arc(buf, (*P["dust_light"],
                                          int(150 * st)),
                                    rect, a0, a0 + 1.9, 3)
                except (ValueError, pygame.error):
                    pass
            surface.blit(buf, (x - c, y + 30 - cy))

    # ------------------------------------------------------------------
    def draw_front(self, surface):
        if not self.active:
            return
        x, y = int(self.x), int(self.y)
        k = self.kind

        # RELEASE: cincin kejut tunggal yang mengembang (semua skill)
        if self.t_charge <= self.age < self.t_area:
            rt = (self.age - self.t_charge) / max(
                0.05, self.t_area - self.t_charge)
            rr = int(10 + self.radius * 0.8 * rt) // 2 * 2
            a = int(190 * (1.0 - rt) ** 1.5)
            if a > 6 and rr > 6:
                er = ellipse_ring_surface(rr, max(4, int(rr * 0.42)),
                                          2, P["fx_bright"], 0)
                er.set_alpha(a)
                surface.blit(er, (x - er.get_width() // 2,
                                  y + 24 - er.get_height() // 2))

        if k == "q" and self.phase in ("release", "area"):
            # dua sabit susul-menyusul ke arah hadap
            st = max(0.0, 1.0 - (self.age - self.t_charge) / 0.5)
            if st > 0.03:
                f = self.facing
                adv = (self.age - self.t_charge) * 190.0
                for i, lag in enumerate((0.0, 14.0)):
                    cx = x + f * int(26 + adv - lag)
                    cy2 = y - 10 + i * 8
                    cr = crescent_surface(
                        13 - i * 3, P["fx_pale"] if i == 0
                        else P["fx_light"], 0.7, filled=True)
                    img = pygame.transform.rotate(
                        cr, 0 if f > 0 else 180)
                    img.set_alpha(int(230 * st))
                    surface.blit(img, (cx - img.get_width() // 2,
                                       cy2 - img.get_height() // 2))
                    img.set_alpha(255)

        if k == "w" and self.phase in ("release", "area"):
            # spark defleksi kecil yang menyusuri garis dinding
            st = 1.0 - self.age / self.total
            wx = x + self.facing * 34
            ph = self.age * 9.0
            for i in range(3):
                sy = y - 26 + int(
                    (math.sin(ph + i * 2.1) * 0.5 + 0.5) * 54)
                s = spark_surface(3, P["fx_white"])
                s.set_alpha(int(200 * st))
                surface.blit(s, (wx - 4 + int(math.sin(ph * 0.7 + i) * 5),
                                 sy - 4))

        if k == "e" and self.phase in ("area", "impact"):
            # tepi cincin sapuan yang menyala berputar (di atas marker)
            st = max(0.0, 1.0 - (self.age - self.t_release) / 0.8)
            if st > 0.03:
                rot = self.age * 4.6
                rr = int(self.radius)
                buf = _scratch(rr * 2 + 10, rr + 10)
                c, cy = rr + 5, (rr + 10) // 2
                rect = pygame.Rect(c - rr, cy - rr // 2, rr * 2, rr)
                for k2 in range(3):
                    a0 = rot + k2 * math.tau / 3
                    try:
                        pygame.draw.arc(
                            buf, (*P["fx_bright"], int(210 * st)),
                            rect, a0, a0 + 0.9, 3)
                        pygame.draw.arc(
                            buf, (*P["fx_white"], int(150 * st)),
                            rect.inflate(-6, -3), a0 + 0.2,
                            a0 + 0.7, 1)
                    except (ValueError, pygame.error):
                        pass
                surface.blit(buf, (x - c, y + 30 - cy))

        if k == "r" and self.phase in ("area", "impact"):
            # glint puncak funnel + mote yang lepas dari puncak
            st = 1.0 - self.age / self.total
            topy = y - 64
            s = spark_surface(4, P["fx_white"])
            s.set_alpha(int(190 * st *
                            (0.6 + 0.4 * math.sin(self.age * 11.0))))
            surface.blit(s, (x - 5, topy - 5))


# ============================================================================
# 10.  GAME FEEL  —  screen shake + hit stop (via bus bersama)
# ============================================================================
#
# STATE INI GLOBAL, jadi tidak boleh dimiliki satu karakter.  Hit-stop &
# shake hidup di ``heroes/combat_feel.py``; modul ini hanya memakainya
# lewat nama lama supaya semua pemanggil — ``_core.Game.update``,
# ``_entity``, tooling, dan tes regresi — tidak perlu diubah.

HIT_STOP_ENABLED = True

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

    Flag ``KAIZEN_FX_ENABLED`` TIDAK menahan freeze karakter lain — ia
    hanya mengatur apakah FX Kaizen sendiri ikut jalan.
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
#: konstanta renderer (ATTACK_WINDUP_END=0.28, ATTACK_SWING_END=0.72,
#: ATTACK_IMPACT=0.54) supaya rig, trail, dan FX SELALU sepakat kapan
#: tebasan mendarat.
#: ANTICIPATION -> WIND-UP -> SWING -> IMPACT -> FOLLOW THROUGH -> RECOVERY
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.14),
    ("WINDUP",       0.14, 0.28),
    ("SWING",        0.28, 0.48),
    ("IMPACT",       0.48, 0.62),
    ("FOLLOW",       0.62, 0.80),
    ("RECOVERY",     0.80, 1.00),
)

#: Titik pendaratan tebasan (progress) — dipakai untuk whoosh + hitbox.
ATTACK_IMPACT_POINT = 0.54
ATTACK_SWING_END = 0.72


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
        ("ANTICIPATION", 0.00, windup * 0.48),
        ("WINDUP",       windup * 0.48, windup),
        ("SWING",        windup, impact - 0.06),
        ("IMPACT",       impact - 0.06, impact + 0.08),
        ("FOLLOW",       impact + 0.08, swing_end),
        ("RECOVERY",     swing_end, 1.00),
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
                getattr(hero, "hero_type", "kaizen")))
        except Exception:                  # pragma: no cover
            scale = 1.0
    return scale


def katana_points(hero, x=None, y=None, progress=None):
    """Posisi layar (pangkal, tip) katana Kaizen dari pose renderer.

    Memakai geometri lokal renderer (``_attack_pose`` untuk tangan +
    ``_katana_tip_local`` untuk ujung) lalu dikonversi ke skala layar,
    sehingga trail menempel PERSIS di kissaki — bukan di perkiraan.
    Return ((bx, by), (tx, ty), action).
    """
    G = _renderer()
    h = hero
    px = float(getattr(h, "x", 0.0)) if x is None else float(x)
    py = float(getattr(h, "y", 0.0)) if y is None else float(y)
    f = 1.0 if getattr(h, "facing",
                       getattr(h, "direction", 1)) >= 0 else -1.0
    s = render_scale(h)
    phase = float(getattr(h, "pulse", 0.0))
    ap = float(getattr(h, "_kz_attack_progress", 0.0)) \
        if progress is None else float(progress)

    if getattr(h, "_kz_attack_active", False) or progress is not None:
        action = "attack"
    elif getattr(h, "_moving_cached", False):
        action = "walk"
    else:
        action = "idle"

    if G is not None:
        try:
            tip_l = G._katana_tip_local(phase, action, ap)
            if action == "attack":
                hand_l = G._attack_pose(ap)["hand"]
            elif action == "walk":
                hand_l = (36, -6 + int(math.sin(phase * 1.7) * 3))
            else:
                hand_l = (34, -2 + int(math.sin(phase * 0.72) * 1.2))
        except Exception:                  # pragma: no cover - tool minimal
            hand_l, tip_l = (34, -2), (92, 18)
    else:                                  # pragma: no cover
        hand_l, tip_l = (34, -2), (92, 18)

    base = (px + hand_l[0] * f * s, py + hand_l[1] * s)
    tip = (px + tip_l[0] * f * s, py + tip_l[1] * s)
    return base, tip, action


# ============================================================================
# 13.  DIRECTOR  —  satu per unit Kaizen
# ============================================================================

class KaizenFXDirector:
    """Mengikat semua subsistem FX untuk satu instance Kaizen.

    Director adalah animation controller + event bus FX:
      * state machine berprioritas (IDLE..DEATH) dengan delta-time,
      * progress serangan dihitung SENDIRI dari ``attack_timer`` 60 Hz
        (lebih halus daripada ``_kz_attack_progress`` yang hanya
        diperbarui saat cache sprite miss),
      * deteksi edge (attack / skill / dash / hurt / death),
      * trail dari posisi katana NYATA,
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
        self.attack_progress = 0.0
        self._attack_cd = 1
        self._attack_live = False
        self._prev_timer = -1
        self.swing_active = False
        self._swing_seen = False
        self._blade_landed = False
        self._proj_fired = False
        self._skill_seen = None
        self._dash_seen = False
        self._wall_seen = 0
        self._ulti_seen = 0
        self._wall_last = 0
        self._ulti_last = 0
        self._wall_stuck = 0.0
        self._ulti_stuck = 0.0
        self._last_hp = None
        self._was_alive = True
        self._last_x = None
        self._last_y = None
        self._moving = False
        self._emit_wall = 0.0
        self._emit_storm = 0.0
        self._step_acc = 0.0
        self.hit_flash = 0.0
        self.time = 0.0
        self.frames = 0

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def on_swing_start(self, x, y, facing):
        """Awal ayunan: reset trail + debu tapak antisipasi."""
        self.trail.reset()
        self.trail.storm_mode = \
            int(getattr(self.hero, "_ulti_timer", 0) or 0) > 0
        self.swing_active = True
        self._blade_landed = False
        self._proj_fired = False
        self.particles.burst(
            x - facing * 8, y + 38, 4,
            speed=(26, 80), life=(0.2, 0.4), size=(2, 4),
            colors=(P["dust"], P["dust_light"]),
            spread=1.1, direction=math.pi if facing > 0 else 0.0,
            gravity=90.0, drag=2.6, shape="pixel", back=True)

    def on_swing_end(self):
        self.swing_active = False

    def on_blade_land(self, x, y, facing, crit=False):
        """Katana MENDARAT (titik IMPACT iai) — whoosh pop walau meleset.

        Hit nyata punya paket lengkap lewat notify_melee_impact; whoosh
        ini menjaga supaya tebasan yang meleset tetap terasa tajam.
        """
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(
            x + facing * 30, y + 6, math.atan2(0.3, facing),
            0.5, crit=crit, kind="crit" if crit else "slash"))
        self.particles.burst(
            x + facing * 30, y + 6, 2,
            speed=(70, 180), life=(0.14, 0.3), size=(1, 3),
            colors=(P["fx_pale"], P["fx_bright"]),
            spread=1.3, direction=math.atan2(0.2, facing), drag=3.6,
            shape="streak")
        shake(1.2, 0.13)

    def on_cast(self, x, y, skill):
        """Skill dilepas: buat SkillFX + bahasa per-skill + shake."""
        if len(self.skills) >= MAX_SKILLS - 1:
            self.skills.pop(0)
        h = self.hero
        f = 1 if getattr(h, "facing", getattr(h, "direction", 1)) >= 0 \
            else -1
        radius = None
        if skill == "q":
            try:
                radius = float(getattr(h, "skill_range", 0)) or None
            except Exception:              # pragma: no cover
                radius = None
        fx = SkillFX(skill, x, y, self.particles, radius, facing=f)
        self.skills.append(fx)

        if skill == "q":
            # Q Steel Wind: sabit ganda + streak + 2 proyektil visual
            self.particles.burst(x + f * 18, y - 8, 5,
                                 speed=(140, 300), life=(0.16, 0.34),
                                 size=(1, 3),
                                 colors=(P["fx_pale"], P["fx_white"],
                                         P["fx_bright"]),
                                 spread=0.8,
                                 direction=0.0 if f > 0 else math.pi,
                                 drag=3.2, shape="streak")
            tgt = getattr(h, "target", None)
            for i, dy in enumerate((-8.0, 6.0)):
                dist = 120.0
                tx = x + f * dist
                ty = y + dy * 3.0
                self.projectiles.spawn(
                    x + f * 16, y - 8 + dy, tx, ty,
                    speed=SLASH_SPEED * 0.82 + i * 40.0, target=tgt,
                    radius=6.0 + (1 if i == 0 else 0), kind="slash",
                    on_impact=self._slash_impact)
            shake(2.2, 0.2)
            hit_stop(0.021)
        elif skill == "w":
            # W Wind Wall: spark pembentukan dinding + mote naik
            wx = x + f * 34
            self.particles.burst(wx, y - 4, 5,
                                 speed=(30, 110), life=(0.3, 0.6),
                                 size=(1, 3),
                                 colors=(P["fx_bright"], P["fx_light"],
                                         P["fx_white"]),
                                 spread=0.9,
                                 direction=-math.pi / 2, drag=1.4,
                                 shape="mote", swirl=2.2)
            shake(1.1, 0.14)
        elif skill == "e":
            # E Sweep: lompatan — debu lepas landas + cincin gale
            self.particles.burst(x, y + 36, 5,
                                 speed=(60, 160), life=(0.3, 0.6),
                                 size=(2, 4),
                                 colors=(P["dust"], P["dust_light"]),
                                 spread=2.6, direction=-math.pi / 2,
                                 gravity=240.0, drag=1.6, shape="pixel",
                                 back=True)
            if len(self.impacts) >= MAX_IMPACTS:
                self.impacts.pop(0)
            self.impacts.append(ImpactFX(x, y + 26, 0.0, 1.1,
                                         kind="gale"))
            shake(2.5, 0.22)
            hit_stop(0.024)
        elif skill == "r":
            # R Tornado: hisapan awal + daun meledak naik + badai
            self.particles.burst(x, y + 24, 7,
                                 speed=(90, 240), life=(0.4, 0.8),
                                 size=(2, 4),
                                 colors=(P["fx_bright"], P["fx_light"],
                                         P["leaf"]),
                                 spread=math.tau, drag=1.0,
                                 shape="streak", swirl=3.0)
            self.particles.burst(x, y + 10, 4,
                                 speed=(40, 130), life=(0.5, 0.9),
                                 size=(2, 4),
                                 colors=(P["leaf"], P["leaf_dark"]),
                                 spread=math.tau, gravity=-160.0,
                                 drag=0.8, shape="leaf", swirl=2.6,
                                 rotation_speed=(-10.0, 10.0))
            shake(4.5, 0.4)
            hit_stop(0.040)

    def _slash_impact(self, proj):
        """Callback projectile: paket impact di titik benturan."""
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(
            proj.hit_pos.x, proj.hit_pos.y, proj.rotation,
            0.7, kind="slash"))
        self.particles.burst(
            proj.hit_pos.x, proj.hit_pos.y, 3,
            speed=(100, 250), life=(0.16, 0.36), size=(1, 3),
            colors=(P["fx_white"], P["fx_pale"], P["fx_bright"]),
            spread=2.2, direction=proj.rotation, drag=3.4, shape="streak")

    def on_dash(self, x, y, facing):
        """Q2 Dash Strike: garis debu + afterimage streak + hit-stop."""
        self.particles.burst(
            x - facing * 10, y + 30, 5,
            speed=(120, 280), life=(0.2, 0.4), size=(2, 4),
            colors=(P["dust_light"], P["fx_light"], P["fx_pale"]),
            spread=0.6, direction=math.pi if facing > 0 else 0.0,
            drag=2.8, shape="streak", back=True)
        self.particles.burst(
            x, y - 6, 3,
            speed=(60, 150), life=(0.16, 0.3), size=(1, 3),
            colors=(P["fx_pale"], P["fx_white"]),
            spread=0.5, direction=math.pi if facing > 0 else 0.0,
            drag=2.2, shape="streak")
        shake(2.8, 0.2)
        hit_stop(0.027)

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False,
                  kind="slash"):
        """Benturan mengenai target: flash, spark, debris, shake, hit-stop."""
        if len(self.impacts) >= MAX_IMPACTS:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit, kind))

        n = int(8 + 6 * min(2.0, power)) + (5 if crit else 0)
        self.particles.burst(
            x, y, n, speed=(110, 320), life=(0.16, 0.4),
            size=(1, 3),
            colors=(P["fx_white"], P["fx_pale"], P["fx_bright"]),
            spread=2.4, direction=angle, drag=3.6, shape="streak")
        self.particles.burst(
            x, y, 5 + (3 if crit else 0),
            speed=(70, 180), life=(0.28, 0.6), size=(2, 4),
            colors=(P["steel_light"], P["steel_mid"], P["fx_light"]),
            gravity=460.0, drag=1.1, shape="shard",
            rotation_speed=(-16.0, 16.0))
        self.particles.burst(
            x, y + 6, 3,
            speed=(20, 60), life=(0.3, 0.55), size=(3, 5),
            colors=(P["smoke"], P["dust"]),
            gravity=-26.0, drag=1.6, shape="smoke", back=True)

        shake(3.6 + 3.2 * min(2.0, power) + (2.6 if crit else 0.0),
              0.16 + 0.08 * min(2.0, power))
        hit_stop(0.036 + 0.02 * min(1.5, power) + (0.014 if crit else 0.0))

    def on_hurt(self, amount=1.0):
        """Kaizen terkena serangan: hit flash + percikan angin."""
        self.hit_flash = 0.15
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        self.particles.burst(
            hx, hy - 10, 3, speed=(70, 190), life=(0.18, 0.36),
            size=(1, 3), colors=(P["fx_bright"], P["fx_light"]),
            drag=3.0, shape="streak")

    def on_death(self):
        """Kaizen tumbang: angin buyar + daun jatuh + debu besar."""
        h = self.hero
        x = float(getattr(h, "x", 0.0))
        y = float(getattr(h, "y", 0.0))
        self.particles.burst(
            x, y - 14, 7, speed=(50, 170), life=(0.5, 1.0),
            size=(2, 4),
            colors=(P["fx_light"], P["fx_mid"], P["fx_dark"]),
            spread=math.tau, drag=1.4, shape="mote", swirl=1.8,
            fade_pow=1.4)
        self.particles.burst(
            x, y - 8, 3, speed=(30, 100), life=(0.6, 1.2),
            size=(2, 4), colors=(P["leaf"], P["leaf_dark"]),
            spread=math.tau, gravity=130.0, drag=1.2, shape="leaf",
            rotation_speed=(-7.0, 7.0))
        self.particles.burst(
            x, y + 28, 4, speed=(30, 90), life=(0.5, 0.9),
            size=(3, 6), colors=(P["dust"], P["smoke"]),
            spread=2.6, direction=-math.pi / 2, gravity=-16.0,
            drag=1.5, shape="smoke", back=True)
        self.trail.reset()
        shake(2.0, 0.3)

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
        timer = int(getattr(h, "attack_timer", getattr(h, "timer", 0))
                    or 0)
        prev = self._prev_timer
        if prev >= 0 and timer > prev:
            # timer NAIK = serangan baru dimulai; nilai puncak = cooldown
            self._attack_cd = max(2, timer)
            self._attack_live = True
        elif prev < 0 and timer > 0:
            # director dibuat DI TENGAH ayunan (unit baru masuk layar):
            # pakai cooldown gameplay sebagai panjang timeline supaya
            # progress tidak melompat.
            self._attack_cd = max(2, timer,
                                  int(getattr(h, "attack_cooldown", timer)
                                      or timer))
            self._attack_live = True
        if self._attack_live:
            if timer <= 0:
                self._attack_live = False
                self.attack_progress = 0.0
            else:
                frame = max(0, self._attack_cd - timer)
                self.attack_progress = min(
                    1.0, frame / max(1.0, self._attack_cd - 1.0))
        self._prev_timer = timer

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

        wall = int(getattr(h, "_wind_wall_timer", 0) or 0)
        if wall > self._wall_seen and self._wall_seen == 0 and \
                skill != "w":
            self.on_cast(hx, hy, "w")
        self._wall_seen = wall

        ulti = int(getattr(h, "_ulti_timer", 0) or 0)
        if ulti > self._ulti_seen and self._ulti_seen == 0 and \
                skill != "r":
            self.on_cast(hx, hy, "r")
        self._ulti_seen = ulti

        # ── Q2 Dash Strike (edge _is_dashing) ─────────────────────────
        dashing = bool(getattr(h, "_is_dashing", False))
        if dashing and not self._dash_seen:
            self.on_dash(hx, hy, facing)
        self._dash_seen = dashing

        # ── swing detection (edge-triggered pada fase SWING) ──────────
        swinging = self._attack_live and \
            attack_phase(self.attack_progress) in ("SWING", "IMPACT",
                                                   "FOLLOW")
        if swinging and not self._swing_seen:
            self.on_swing_start(hx, hy, facing)
        elif not swinging and self._swing_seen:
            self.on_swing_end()
        self._swing_seen = swinging

        # ── pendaratan bilah (whoosh pop di titik IMPACT iai) ─────────
        ap = self.attack_progress
        if swinging and not self._blade_landed and \
                ap >= ATTACK_IMPACT_POINT:
            self._blade_landed = True
            self.on_blade_land(hx, hy, facing)

        # ── sabit angin serangan dasar ranged (jendela 0.45-0.55) ─────
        # Menggantikan jalur canvas (_spawn_wind_slash) yang ikut beku
        # di cache sprite: _skip_renderer_projectiles di-set saat attach.
        if self._attack_live and float(getattr(h, "range", 0)) > 80.0:
            if 0.45 < ap < 0.58 and not self._proj_fired:
                self._proj_fired = True
                tgt = getattr(h, "target", None)
                tx = float(getattr(tgt, "x", hx + facing * 160.0))
                ty = float(getattr(tgt, "y", hy))
                self.projectiles.spawn(
                    hx + facing * 22.0, hy - 8.0, tx, ty - 6.0,
                    speed=SLASH_SPEED, target=tgt, radius=8.0,
                    kind="slash", on_impact=self._slash_impact)
            elif ap < 0.2:
                self._proj_fired = False

        # ── rekam posisi bilah saat swing -> trail ────────────────────
        # Pagar anti-beku: timer gameplay SELALU berkurang tiap langkah
        # simulasi.  Kalau hero tewas di tengah skill, ``Hero.update``
        # berhenti jalan dan timer membeku > 0 — tanpa pagar ini, emisi
        # dinding/tornado akan hidup tanpa batas di mayat.  Setelah 15 s
        # tanpa penurunan (mustahil di gameplay sehat), emisi berhenti.
        if wall <= 0 or wall < self._wall_last:
            self._wall_stuck = 0.0
        else:
            self._wall_stuck += dt
        self._wall_last = wall
        wall_live = wall > 0 and alive and self._wall_stuck < 15.0

        if ulti <= 0 or ulti < self._ulti_last:
            self._ulti_stuck = 0.0
        else:
            self._ulti_stuck += dt
        self._ulti_last = ulti
        ulti_live = ulti > 0 and alive and self._ulti_stuck < 15.0

        if alive and swinging:
            base, tip, _action = katana_points(h, progress=ap)
            # pita hanya menempati sepertiga LUAR bilah (bahasa iai)
            inner = (base[0] + (tip[0] - base[0]) * 0.45,
                     base[1] + (tip[1] - base[1]) * 0.45)
            outer = (base[0] + (tip[0] - base[0]) * 1.12,
                     base[1] + (tip[1] - base[1]) * 1.12)
            self.trail.push(inner, outer)

        # ── emisi kontinu: dinding W & badai R ────────────────────────
        if wall_live:
            self._emit_wall += dt
            if self._emit_wall >= 0.12:
                self._emit_wall = 0.0
                wx = hx + facing * 34
                self.particles.spawn(
                    wx + random.uniform(-6, 6),
                    hy + random.uniform(-20, 34),
                    facing * random.uniform(-8, 8),
                    -random.uniform(26, 66),
                    random.uniform(0.35, 0.7), random.uniform(1.5, 3.0),
                    P["fx_bright"], color_end=P["fx_dark"], drag=1.0,
                    shape="mote", swirl=random.uniform(-2.5, 2.5))
        if ulti_live:
            self._emit_storm += dt
            if self._emit_storm >= 0.10:
                self._emit_storm = 0.0
                ang = random.random() * math.tau
                rr = random.uniform(30, 90)
                tang = ang + math.pi / 2
                spd = random.uniform(100, 190)
                self.particles.spawn(
                    hx + math.cos(ang) * rr,
                    hy + 26 + math.sin(ang) * rr * 0.5,
                    math.cos(tang) * spd,
                    math.sin(tang) * spd * 0.5 - random.uniform(40, 100),
                    random.uniform(0.4, 0.8), random.uniform(2.0, 3.5),
                    P["fx_light"] if random.random() < 0.6 else P["leaf"],
                    color_end=P["fx_deep"], drag=0.6,
                    shape="streak" if random.random() < 0.6 else "leaf",
                    swirl=3.4, rotation=random.random() * math.tau,
                    rotation_speed=random.uniform(-9, 9))

        # ── debu langkah saat bergerak (foot dust, rate-limited) ──────
        if alive and self._moving and not self._attack_live:
            self._step_acc += dt
            if self._step_acc >= 0.16:
                self._step_acc = 0.0
                self.particles.spawn(
                    hx - facing * 8 + random.uniform(-3, 3),
                    hy + 38, -facing * random.uniform(14, 34),
                    -random.uniform(4, 16),
                    random.uniform(0.22, 0.4), random.uniform(2, 3),
                    P["dust"], color_end=P["smoke"], gravity=60.0,
                    drag=2.4, shape="pixel", back=True)

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
        r = int(16 + 24 * (self.hit_flash / 0.15))
        g = glow_surface(r, P["fx_pale"], self.hit_flash / 0.15 * 0.65)
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
    rng = int(getattr(h, "range", 60))

    # attack range
    pygame.draw.circle(surface, (255, 140, 60), (x, y), rng, 1)
    # hurtbox
    pygame.draw.circle(surface, (90, 220, 255), (x, y), rad, 1)
    # hitbox serangan (kerucut depan saat swing)
    if director.anim_phase in ("SWING", "IMPACT"):
        f = 1 if getattr(h, "facing", getattr(h, "direction", 1)) >= 0 \
            else -1
        pygame.draw.rect(surface, (255, 230, 90),
                         pygame.Rect(x if f > 0 else x - rng,
                                     y - 30, rng, 58), 1)
    # radius AOE gameplay E/R saat aktif
    if getattr(h, "active_skill", None) == "e":
        pygame.draw.circle(surface, (120, 255, 160), (x, y + 30),
                           int(WORLD_RADIUS["e"]), 1)
    if int(getattr(h, "_ulti_timer", 0) or 0) > 0:
        pygame.draw.circle(surface, (255, 90, 60), (x, y + 30),
                           int(WORLD_RADIUS["r"]), 1)
    # dinding W
    if int(getattr(h, "_wind_wall_timer", 0) or 0) > 0:
        f = 1 if getattr(h, "facing", getattr(h, "direction", 1)) >= 0 \
            else -1
        pygame.draw.line(surface, (150, 220, 255),
                         (x + f * 34, y - 30), (x + f * 34, y + 36), 1)
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
        "KAIZEN  %s / %s" % (st["state"], st["phase"]),
        "atkT %.2f  skill %s" % (st["attack_t"],
                                 getattr(h, "active_skill", None)),
        "wall %d  ulti %d  dash %d  qstack %d" % (
            int(getattr(h, "_wind_wall_timer", 0) or 0),
            int(getattr(h, "_ulti_timer", 0) or 0),
            int(getattr(h, "_dash_timer", 0) or 0),
            int(getattr(h, "_q_stack", 0) or 0)),
        "part %d  proj %d  imp %d  trail %d" % (
            st["particles"], st["projectiles"], st["impacts"],
            st["trail"]),
        "shake %.1f  stop %d  fps %d" % (
            SHAKE.amount, HITSTOP.frames, fps),
    ]
    for i, txt in enumerate(lines):
        img = font.render(txt, True, (200, 235, 255))
        surface.blit(img, (x - 60, y - 96 + i * 13))


# ============================================================================
# 15.  API MODUL  —  registry, tick, hook render
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Kaizen."""
    _sync_palette()
    d = getattr(hero, "_kz_fx", None)
    if d is None:
        d = KaizenFXDirector(hero)
        try:
            hero._kz_fx = d
        except Exception:                  # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:           # jangkar tua dibuang
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    """Lepas director dari registry DAN penanda milik-nya di unit.

    Penting: kalau penanda ``_kz_live_fx`` ditinggal sementara director
    sudah tidak dipanggil lagi, renderer akan terus MELEWATI smear
    di-canvas padahal tidak ada yang menggantinya -> efek hilang total.
    """
    try:
        if director.hero is not None:
            director.hero._kz_fx = None
            director.hero._kz_live_fx = False
            director.hero._skip_renderer_projectiles = False
    except Exception:                      # pragma: no cover
        pass
    director.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit ini (dipanggil renderer / pipeline).

    Sekalian menandai unit supaya renderer TIDAK menggambar efek yang
    sekarang dimiliki lapisan hidup (smear ayunan + sabit angin
    di-canvas).  Return True kalau lapisan hidup jadi dipakai.
    """
    if not KAIZEN_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                      # pragma: no cover
        return False
    try:
        hero._kz_live_fx = True
        # Sabit angin serangan dasar sekarang milik lapisan hidup
        # (60 fps, layar 1:1) — jalur canvas dilewati agar tidak dobel.
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
    if not getattr(hero, "_kz_live_fx", False):
        return False
    d = getattr(hero, "_kz_fx", None)
    # Penanda saja tidak cukup: director-nya harus masih TERDAFTAR.
    return d is not None and d in _DIRECTORS


def tick(dt=None):
    """Majukan waktu FX satu frame nyata.  Aman dipanggil berkali-kali.

    Delta-time dihitung oleh bus ``combat_feel`` (dijepit supaya lonjakan
    frame saat loading / alt-tab tidak melempar partikel ke luar layar,
    dilambatkan saat hit-stop, dan shake-nya hanya dimundurkan SEKALI per
    frame walau beberapa karakter ikut bertempur).  Pemanggilan kedua
    dalam MILIDETIK yang sama (dua unit Kaizen di satu frame) tidak
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
    """Jumlah partikel Kaizen hidup di seluruh arena (untuk HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def total_projectiles():
    """Jumlah proyektil visual Kaizen hidup (untuk HUD perf)."""
    return sum(d.projectiles.count() for d in _DIRECTORS)


# --- hook yang dipanggil heroes/__init__.py --------------------------------

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: dipanggil SEBELUM sprite hero di-blit."""
    if not KAIZEN_FX_ENABLED:
        return
    attach(hero)
    tick()
    director_for(hero).draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: dipanggil SETELAH sprite hero di-blit."""
    if not KAIZEN_FX_ENABLED:
        return
    director_for(hero).draw_front(surface)


# --- hook yang dipanggil _entity.py ----------------------------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Serangan dasar melee Kaizen mengenai target (damage instan)."""
    if not KAIZEN_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except Exception:                      # pragma: no cover
        power = 1.0
    tx = float(getattr(target, "x", 0)) if target is not None else 0.0
    ty = float(getattr(target, "y", 0)) if target is not None else 0.0
    ang = math.atan2(float(getattr(hero, "y", 0.0)) - ty,
                     tx - float(getattr(hero, "x", 0.0)))
    director_for(hero).on_impact(tx, ty - 10, ang, power, crit, "slash")


def notify_skill_impact(hero, x, y, radius=None, skill="q"):
    """Skill Kaizen meledak di sebuah titik (dipakai tooling/audit)."""
    if not KAIZEN_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    if len(d.skills) >= MAX_SKILLS - 1:
        d.skills.pop(0)
    f = 1 if getattr(hero, "facing",
                     getattr(hero, "direction", 1)) >= 0 else -1
    d.skills.append(SkillFX(skill, x, y, d.particles, radius, facing=f))


def notify_skill_cast(hero, skill):
    """Skill Kaizen dilepas dari luar (auto-cast guard / tooling)."""
    if not KAIZEN_FX_ENABLED or hero is None:
        return
    director_for(hero).on_cast(float(getattr(hero, "x", 0.0)),
                               float(getattr(hero, "y", 0.0)),
                               skill)


def notify_hurt(hero, amount=1.0):
    """Kaizen terkena damage dari luar (tanpa menunggu watch hp)."""
    if not KAIZEN_FX_ENABLED or hero is None:
        return
    director_for(hero).on_hurt(amount)
