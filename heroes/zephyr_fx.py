# ============================================================================
# heroes/zephyr_fx.py
# ----------------------------------------------------------------------------
# ZEPHYR — COMBAT / GAME-FEEL ENGINE  (screen-space live layer)
#
# Renderer badan Zephyr (heroes/_bundle.py :: _NS_zephyr) menggambar ke
# canvas yang DI-CACHE lalu di-scale.  Artinya semua yang butuh gerak
# 60 fps sejati - trail senjata, partikel, projectile, impact, shake -
# TIDAK boleh hidup di dalam canvas itu.  Modul ini adalah lapisan hidup
# tersebut: digambar langsung ke layar pada skala 1:1 setiap frame,
# memakai delta-time nyata, dan tidak pernah ikut ter-cache.
#
# 100% PROSEDURAL.  Tidak ada PNG / JPG / GIF / sprite-sheet / image.load.
# Semua bentuk dibuat dengan pygame.draw + pygame.Surface + transform.
#
# Isi:
#   ZEPHYR_PALETTE     palette khusus karakter
#   Particle           partikel penuh (accel, gravity, rotation, fade)
#   ParticleSystem     pool + burst + cap, reusable
#   SwingTrail         weapon trail prosedural dari histori posisi
#   ImpactFX           flash + shockwave + debris + slash fragment
#   ZephyrProjectile   projectile modular (spawn->travel->hit->destroy)
#   ProjectileSystem   manajer projectile
#   SkillFX            lifecycle FX skill (cast->charge->release->fade)
#   ScreenShake        trauma-based, decay bertahap
#   HitStop            0.03 - 0.08 s freeze
#   ZephyrFXDirector   satu instance per hero, mengikat semua di atas
#   debug overlay      DEBUG_CHARACTER
# ============================================================================

import math
import random

import pygame


# ============================================================================
# 0.  KONFIGURASI
# ============================================================================

#: Debug visual untuk karakter Zephyr (hitbox, state, timer, FPS, dll).
DEBUG_CHARACTER = False

#: Master switch — kalau False, modul jadi no-op murah.
ZEPHYR_FX_ENABLED = True

#: Hit-stop global (dibaca _core.Game.update).
HIT_STOP_ENABLED = True

#: Batas keras jumlah partikel hidup per director (anti-kebocoran FPS).
MAX_PARTICLES = 160

#: Batas keras projectile visual per director.
MAX_PROJECTILES = 24

#: Panjang histori trail senjata (jumlah sample posisi lama).
TRAIL_SAMPLES = 12

#: Simulasi game berjalan pada langkah tetap 1/60 s.
FIXED_DT = 1.0 / 60.0


# ============================================================================
# 1.  PALETTE  —  dark-fantasy fey, limited palette, hard edges
# ============================================================================

ZEPHYR_PALETTE = {
    # kunci generik (kontrak palette karakter)
    "outline":    (12,   4,  20),
    "shadow":     (26,   8,  38),
    "dark":       (58,  16,  74),
    "body":       (104, 32, 108),
    "mid":        (162, 60, 146),
    "light":      (218, 108, 186),
    "highlight":  (255, 200, 236),
    "weapon":     (128, 86, 122),
    "fx":         (255, 136, 210),

    # ramp sihir (dipakai bolt / trail / impact)
    "fx_darkest": (40,   4,  40),
    "fx_dark":    (100, 12,  84),
    "fx_mid":     (178, 32, 138),
    "fx_light":   (232, 80, 178),
    "fx_bright":  (255, 136, 210),
    "fx_hot":     (255, 200, 236),
    "fx_white":   (255, 242, 252),

    # aksen
    "thorn":      (96,  32, 102),
    "thorn_lit":  (186, 76, 158),
    "gold":       (234, 192, 90),
    "ember":      (255, 154, 210),
    "smoke":      (46,  22,  58),
    "ash":        (74,  40,  86),
}

P = ZEPHYR_PALETTE


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


# ============================================================================
# 1b. ANGGARAN EFEK  (preset kualitas mobile x governor beban FX)
# ============================================================================

def _quality():
    try:
        from mobile.perf import Quality as Q
        return Q
    except Exception:                          # pragma: no cover
        return None


def particle_budget():
    """Faktor jumlah partikel 0..1 (0.0 = partikel dimatikan)."""
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


# ============================================================================
# 2.  SURFACE CACHE  —  glow / spark / ring dibuat sekali lalu dipakai ulang
# ============================================================================

_SURF_CACHE = {}
_SURF_CACHE_MAX = 384


def _cache_put(key, surf):
    # Buang 25% entri tertua saat penuh (dict Python menjaga urutan
    # sisip) — jauh lebih baik daripada mengosongkan seluruh cache dan
    # membangun ulang semuanya di frame berikutnya.
    if len(_SURF_CACHE) >= _SURF_CACHE_MAX:
        for k in list(_SURF_CACHE)[:_SURF_CACHE_MAX // 4]:
            del _SURF_CACHE[k]
    _SURF_CACHE[key] = surf
    return surf


def glow_surface(radius, color, power=1.0):
    """Bola cahaya radial prosedural, PREMULTIPLIED untuk additive blit.

    Penting: ``BLEND_RGB_ADD`` mengabaikan kanal alpha, jadi kalau
    lingkaran digambar dengan RGB penuh + alpha menurun, hasil blit
    additive-nya jadi CAKRAM keras berwarna solid.  Di sini intensitas
    sudah dikalikan ke kanal RGB (premultiplied) dan juga disalin ke
    alpha, sehingga surface yang sama tetap benar untuk blit normal
    maupun additive.
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
    """Cincin ELIPS (shockwave berarah) — cached + rotasi.

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


def clear_cache():
    """Bersihkan seluruh surface cache (dipanggil saat ganti resolusi)."""
    _SURF_CACHE.clear()


def cache_size():
    """Jumlah surface yang sedang di-cache (dipakai debug/HUD)."""
    return len(_SURF_CACHE)


# ============================================================================
# 3.  PARTICLE SYSTEM
# ============================================================================

class Particle:
    """Satu partikel prosedural.

    Atribut lengkap sesuai kontrak: position, velocity, acceleration,
    life, max_life, size, rotation, rotation_speed, alpha, gravity,
    color.  ``shape`` memilih bentuk gambar (pixel-art, hard edge).
    """

    __slots__ = ("pos", "vel", "acc", "life", "max_life", "size",
                 "rotation", "rotation_speed", "alpha", "gravity",
                 "color", "color_end", "shape", "drag", "additive",
                 "active", "fade_pow")

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
            g = glow_surface(sz * 2, col, round(0.9 * fade, 2))
            surface.blit(g, (x - sz * 2, y - sz * 2),
                         special_flags=pygame.BLEND_RGB_ADD)
            return

        if self.shape == "spark":
            # set_alpha diabaikan oleh BLEND_RGB_ADD -> pakai blit normal
            s = spark_surface(sz + 1, col)
            s.set_alpha(a)
            surface.blit(s, (x - sz - 1, y - sz - 1))
            return

        if self.shape == "shard":
            # serpihan tajam yang ikut berputar (debris / slash fragment)
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
            # garis tipis searah kecepatan — bagus untuk percikan cepat
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

        # default: kotak chunky (pixel-art)
        tmp = _scratch(sz * 2 + 2, sz * 2 + 2)
        pygame.draw.rect(tmp, (*col, a), (1, 1, sz, sz))
        if sz >= 3:
            pygame.draw.rect(tmp, (*P["fx_white"], min(255, a + 40)),
                             (1, 1, max(1, sz // 2), max(1, sz // 2)))
        surface.blit(tmp, (x - sz // 2, y - sz // 2),
                     special_flags=pygame.BLEND_RGB_ADD
                     if self.additive else 0)


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


class ParticleSystem:
    """Pool partikel reusable: spawn / burst / update / draw."""

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

    def clear(self):
        """Matikan semua partikel (kembalikan ke pool)."""
        for p in self._live:
            p.active = False
            self._pool.append(p)
        self._live.clear()

    # ------------------------------------------------------------------
    def spawn(self, x, y, vx, vy, life, size, color, **kw):
        """Spawn satu partikel.  Return partikel, atau None kalau penuh."""
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
              rotation_speed=(0.0, 0.0), fade_pow=1.0):
        """Semburan radial / berarah.

        ``direction`` + ``spread`` mengontrol kerucut sebaran; spread
        tau = melingkar penuh.
        """
        colors = colors or (P["fx_bright"], P["fx_light"], P["fx_hot"])
        budget = particle_budget()
        if budget <= 0.0:
            return 0
        room = self.cap - len(self._live)
        if room <= 0:
            return 0
        count = max(0, int(count))
        if budget < 1.0:
            if count > 1:
                count = max(1, int(count * budget))
            elif random.random() >= budget:
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
                                                  rotation_speed[1]))
        finally:
            self._in_burst -= 1
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
            if (p.shape == "glow") == want_back:
                p.draw(surface)


# ============================================================================
# 4.  SWING TRAIL  —  weapon trail prosedural dari histori posisi
# ============================================================================

class SwingTrail:
    """Jejak senjata berbasis histori posisi.

    Menyimpan pasangan (grip, tip) beberapa frame terakhir lalu
    menyusunnya jadi pita poligon translucent yang memudar.  Trail
    OTOMATIS mengikuti arah serangan karena bentuknya murni turunan
    dari lintasan senjata, bukan bentuk yang digambar manual.
    """

    def __init__(self, samples=TRAIL_SAMPLES,
                 color_edge=None, color_core=None):
        self.samples = int(samples)
        self.points = []            # [(grip, tip, umur)]
        self.color_edge = color_edge or P["fx_mid"]
        self.color_core = color_core or P["fx_hot"]
        self.life = 0.26            # detik sebelum sample dibuang
        self.width_boost = 1.0
        self.active = False

    # ------------------------------------------------------------------
    def reset(self):
        """Kosongkan trail (dipanggil saat swing baru dimulai)."""
        self.points.clear()
        self.active = False

    def push(self, grip, tip):
        """Catat satu posisi senjata (dipanggil tiap frame saat swing)."""
        self.points.append([pygame.Vector2(grip), pygame.Vector2(tip), 0.0])
        if len(self.points) > self.samples:
            self.points.pop(0)
        self.active = True

    # ------------------------------------------------------------------
    def update(self, dt):
        """Tuakan sample; buang yang lewat umur."""
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
        """Gambar pita trail: bayangan -> badan -> inti terang."""
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

        # ── lapis 1: badan pita (gelap, lebar penuh) ──────────────────
        for i in range(n - 1):
            g0, t0, a0 = self.points[i]
            g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(150 * self._quad_alpha(i, n) * fade *
                        self.width_boost)
            if alpha <= 4:
                continue
            pygame.draw.polygon(
                buf, (*self.color_edge, alpha),
                [loc(g0), loc(t0), loc(t1), loc(g1)])

        # ── lapis 2: inti terang (setengah lebar, dekat ujung) ────────
        for i in range(n - 1):
            g0, t0, a0 = self.points[i]
            g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(215 * self._quad_alpha(i, n) * fade)
            if alpha <= 6:
                continue
            m0 = g0.lerp(t0, 0.50)
            m1 = g1.lerp(t1, 0.50)
            pygame.draw.polygon(
                buf, (*self.color_core, alpha),
                [loc(m0), loc(t0), loc(t1), loc(m1)])

        # ── lapis 3: garis ujung 1 px (hard edge pixel-art) ───────────
        for i in range(n - 1):
            _g0, t0, a0 = self.points[i]
            _g1, t1, _a1 = self.points[i + 1]
            fade = max(0.0, 1.0 - a0 / self.life)
            alpha = int(235 * self._quad_alpha(i, n) * fade)
            if alpha <= 8:
                continue
            pygame.draw.line(buf, (*P["fx_white"], alpha),
                             loc(t0), loc(t1), 2)

        surface.blit(buf, (minx, miny))


# ============================================================================
# 5.  IMPACT FX
# ============================================================================

class ImpactFX:
    """Satu kejadian benturan: flash, shockwave, slash fragment, debris.

    Semua digambar prosedural dan berumur pendek; tidak ada state yang
    hidup tanpa batas.
    """

    __slots__ = ("x", "y", "angle", "power", "age", "duration",
                 "crit", "active", "color", "kind")

    def __init__(self, x, y, angle=0.0, power=1.0, crit=False,
                 kind="magic"):
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.power = max(0.35, float(power))
        self.age = 0.0
        self.duration = 0.34 + 0.10 * min(2.0, self.power)
        self.crit = bool(crit)
        self.active = True
        self.kind = kind
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

        # ── 1. IMPACT FLASH — flare bintang, bukan bola putih ────────
        if t < 0.22:
            ft = 1.0 - t / 0.22
            gr = int((5 + 9 * pw) * (0.5 + 0.5 * ft)) // 2 * 2 + 2
            surface.blit(glow_surface(gr, P["fx_hot"], 0.55 * ft),
                         (x - gr, y - gr),
                         special_flags=pygame.BLEND_RGB_ADD)
            ln = (16 + 34 * pw) * ft
            fl = _scratch(int(ln * 2 + 8), int(ln * 2 + 8))
            c = int(ln + 4)
            for k in range(8):
                a = self.angle + k * math.pi / 4
                L = ln if k % 2 == 0 else ln * 0.42
                pygame.draw.line(
                    fl, (*P["fx_white"], int(240 * ft)), (c, c),
                    (c + int(math.cos(a) * L), c + int(math.sin(a) * L)),
                    3 if k % 2 == 0 else 1)
            surface.blit(fl, (x - c, y - c))

        # ── 2. SHOCKWAVE — elips berarah (bukan lingkaran polos) ─────
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
            for k in range(8):
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

        # ── 4. SLASH FRAGMENT — 3 busur pecah searah pukulan ─────────
        if t < 0.55:
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

        # ── 5. INTI benturan ─────────────────────────────────────────
        if t < 0.42:
            st = 1.0 - t / 0.42
            sz = int((5 + 9 * pw) * (0.5 + 0.5 * st)) // 2 * 2 + 2
            s = spark_surface(sz, self.color)
            s.set_alpha(int(255 * st))
            surface.blit(s, (x - sz - int(ca * 2), y - sz - int(sa * 2)))


# ============================================================================
# 6.  PROJECTILE SYSTEM
# ============================================================================

class ZephyrProjectile:
    """Bolt sihir Zephyr — modular, vektor, delta-time.

    Kontrak atribut: position, velocity, speed, damage, lifetime,
    target, radius, rotation, trail, particles, active.

    Lifecycle: SPAWN -> TRAVEL -> TRAIL -> HIT -> IMPACT FX -> DESTROY
    """

    STATE_TRAVEL = "travel"
    STATE_IMPACT = "impact"
    STATE_DEAD = "dead"

    def __init__(self, x, y, tx, ty, speed=520.0, damage=0,
                 target=None, radius=6.0, homing=6.5, kind="bolt",
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
        self.max_lifetime = 2.6
        self.target = target
        self.radius = float(radius)
        self.rotation = math.atan2(self.velocity.y, self.velocity.x)
        self.trail = []                  # [(Vector2, umur)]
        self.trail_life = 0.20
        self.particles = particles       # ParticleSystem bersama
        self.active = True
        self.state = self.STATE_TRAVEL
        self.kind = kind
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
            self.on_impact(self)

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

        # ── homing halus ke target yang bergerak ──────────────────────
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
            if self._emit_acc >= 0.028:
                self._emit_acc = 0.0
                ang = self.rotation + math.pi + (random.random() - .5) * 1.1
                spd = random.uniform(20, 70)
                self.particles.spawn(
                    self.position.x, self.position.y,
                    math.cos(ang) * spd, math.sin(ang) * spd,
                    random.uniform(0.16, 0.34),
                    random.uniform(1.5, 3.0),
                    P["fx_bright"] if random.random() < .5 else P["ember"],
                    color_end=P["fx_dark"], drag=3.0, shape="pixel")

        # ── tumbukan sederhana dengan target ─────────────────────────
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
        """Trail -> glow -> badan berarah -> inti -> glint orbit."""
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
                pygame.draw.polygon(
                    buf, (*P["fx_mid"], 120),
                    [(int(px) - minx, int(py) - miny) for px, py in poly])
                pygame.draw.lines(
                    buf, (*P["fx_light"], 170), False,
                    [(int(pv.x) - minx, int(pv.y) - miny)
                     for pv, _a in self.trail], 2)
                surface.blit(buf, (minx, miny))

        if self.state == self.STATE_IMPACT:
            return

        # Badan bolt memakai renderer bersama draw_bolt() supaya
        # projectile renderer & projectile gameplay identik.
        draw_bolt(surface, self.position.x, self.position.y,
                  self.rotation, age=int(self.lifetime * 60),
                  crit=False, radius=self.radius)


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
        pr = ZephyrProjectile(x, y, tx, ty, **kw)
        self.projectiles.append(pr)
        return pr

    def update(self, dt):
        if not self.projectiles:
            return
        self.projectiles = [p for p in self.projectiles if p.update(dt)]

    def draw(self, surface):
        for p in self.projectiles:
            p.draw(surface)


# ============================================================================
# 7.  SKILL FX  —  lifecycle penuh per skill
# ============================================================================

class SkillFX:
    """Efek skill Zephyr dengan lifecycle bertahap.

    CAST -> CHARGE -> RELEASE -> TRAVEL/AREA -> IMPACT -> AFTER -> FADE

    Setiap fase punya bahasa visual berbeda supaya skill terbaca:
    pilar cahaya, cincin energi, retakan tanah, debu, bara, pecahan.
    """

    #: (charge, release, area, impact, after) dalam detik
    TIMELINE = {
        "q": (0.30, 0.14, 0.90, 0.18, 0.55),
        "w": (0.24, 0.12, 1.20, 0.14, 0.60),
        "e": (0.20, 0.12, 0.70, 0.22, 0.45),
        "r": (0.42, 0.18, 1.40, 0.26, 0.80),
    }

    TINT = {
        "q": ((150, 62, 130), (232, 118, 190)),   # Bramble Maze
        "w": ((96, 74, 190), (196, 190, 255)),    # Shadow Realm
        "e": ((178, 32, 138), (255, 200, 236)),   # Casket Curse
        "r": ((232, 80, 178), (255, 242, 252)),   # Bedlam
    }

    RADIUS = {"q": 60, "w": 100, "e": 70, "r": 84}

    def __init__(self, kind, x, y, particles=None, radius=None):
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

        # CHARGE: partikel tersedot masuk ke pusat
        if self.phase == "charge":
            self._emit += dt
            if self._emit >= 0.035:
                self._emit = 0.0
                a = random.random() * math.tau
                rr = self.radius * random.uniform(0.7, 1.15)
                sx = self.x + math.cos(a) * rr
                sy = self.y + math.sin(a) * rr * 0.45
                ps.spawn(sx, sy,
                         -math.cos(a) * rr * 1.6,
                         -math.sin(a) * rr * 0.75,
                         0.42, random.uniform(1.5, 3.0),
                         P["fx_bright"], color_end=P["fx_dark"],
                         shape="pixel", fade_pow=0.6)

        # RELEASE: ledakan keluar + bara
        elif self.phase == "release" and not self._released:
            self._released = True
            ps.burst(self.x, self.y, 16,
                     speed=(120, 320), life=(0.24, 0.55),
                     size=(2, 4), colors=(P["fx_white"], P["fx_hot"],
                                          P["fx_light"]),
                     drag=3.2, shape="streak")
            ps.burst(self.x, self.y + 6, 8,
                     speed=(50, 150), life=(0.4, 0.8), size=(2, 5),
                     colors=(P["ash"], P["smoke"]),
                     gravity=-40.0, drag=1.6, shape="pixel")

        # AREA: bara naik pelan dari tanah
        elif self.phase == "area":
            self._emit += dt
            if self._emit >= 0.06:
                self._emit = 0.0
                a = random.random() * math.tau
                rr = self.radius * random.uniform(0.2, 1.0)
                ps.spawn(self.x + math.cos(a) * rr,
                         self.y + math.sin(a) * rr * 0.42,
                         random.uniform(-14, 14), random.uniform(-46, -18),
                         random.uniform(0.5, 1.0), random.uniform(1.5, 3.0),
                         P["ember"], color_end=P["fx_dark"],
                         drag=0.6, shape="pixel")

        # IMPACT: pecahan + debu
        elif self.phase == "impact" and not self._impacted:
            self._impacted = True
            ps.burst(self.x, self.y, 14,
                     speed=(90, 260), life=(0.3, 0.62), size=(2, 5),
                     colors=(P["thorn_lit"], P["fx_light"], P["ash"]),
                     gravity=420.0, drag=1.0, shape="shard",
                     rotation_speed=(-14.0, 14.0))
        return True

    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        """Lapisan bawah karakter: kabut tanah, cincin, retakan."""
        if not self.active:
            return
        col_a, col_b = self.TINT[self.kind]
        a = self.age
        R = self.radius

        # kabut/glow tanah (additive) — memberi kedalaman, bukan garis saja.
        # Radius & daya DIKUANTISASI supaya jumlah entri cache kecil.
        t_all = min(1.0, a / self.total)
        haze = int(R * (0.9 + 0.25 * math.sin(a * 4.0))) // 8 * 8
        power = round(0.30 * (1.0 - abs(t_all - 0.35) * 1.4) / 0.05) * 0.05
        if power > 0.02 and haze >= 8:
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
            step = 2 if segs >= 10 else 1
            for i in range(segs):
                a0 = i * math.tau / segs + phase
                if i % 2 and step == 2 and detail >= 0.55:
                    continue
                x0 = cx + math.cos(a0) * radius
                y0 = cy + math.sin(a0) * radius * 0.42
                x1 = cx + math.cos(a0 + 0.26) * radius
                y1 = cy + math.sin(a0 + 0.26) * radius * 0.42
                pygame.draw.line(buf, (*color, alpha),
                                 (int(x0), int(y0)), (int(x1), int(y1)), 3)
        surface.blit(buf, (int(self.x) - cx, int(self.y) - cy))

    def _ground_cracks(self, surface, R, color, alpha):
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
        """Lapisan atas karakter: shockwave, kilat rilis."""
        if not self.active:
            return
        col_a, col_b = self.TINT[self.kind]
        a = self.age
        x, y = int(self.x), int(self.y)

        if self.phase == "charge":
            # Pilar cahaya charge DIBUANG: kolom 60-130 px yang berdiri
            # tepat di sumbu badan menutupi Zephyr selama skill di-cast.
            # Fase charge kini tidak menggambar lapisan depan apa pun.
            return

        if self.phase == "release":
            t = (a - self.t_charge) / max(0.001,
                                          self.t_release - self.t_charge)
            r = int(self.radius * (0.4 + 1.1 * t))
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
            # cincin energi berputar (dua arah berlawanan)
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

    def _rune_ring(self, surface, cx, cy, radius, color, alpha,
                   rot, marks):
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
# 8.  GAME FEEL  —  screen shake + hit stop (via bus bersama)
# ============================================================================
#
# STATE INI GLOBAL, jadi tidak boleh dimiliki satu karakter.  Sejak pass
# Gornak, hit-stop & shake hidup di ``heroes/combat_feel.py``; modul ini
# hanya memakainya lewat nama lama (``HITSTOP``, ``SHAKE``, ``hit_stop``,
# ``shake``, ``should_freeze_frame``) supaya semua pemanggil lama —
# ``_core.Game.update``, ``_entity``, tooling, dan tes regresi
# ``tools/test_zephyr_v3.py`` — tidak perlu diubah sama sekali.
#
# Manfaat ikut bus bersama:
#   * dua hero yang memukul di frame yang sama tidak menumpuk freeze;
#   * satu-satunya jalur shake ke kamera tetap ``EffectManager.shake_screen``;
#   * ``Game.update`` cukup bertanya ke satu tempat untuk SEMUA karakter.

try:                                     # build minimal: tanpa bus = no-op
    from heroes import combat_feel as _feel
except Exception:                          # pragma: no cover
    _feel = None

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

    Flag ``ZEPHYR_FX_ENABLED`` TIDAK menahan freeze karakter lain — ia
    hanya mengatur apakah FX Zephyr sendiri ikut jalan (lihat ``shake``).
    """
    if _feel is not None:
        return _feel.should_freeze_frame()
    if not HIT_STOP_ENABLED:               # pragma: no cover
        return False
    return HITSTOP.consume_frame()


def shake(strength=5.0, duration=0.22):
    """API publik: guncangkan layar (lokal + EffectManager game)."""
    if _feel is not None:
        _feel.shake(strength, duration)
        return
    SHAKE.add(strength, duration)          # pragma: no cover
    try:
        import __main__
        game = getattr(__main__, "game_instance", None)
        if game is not None and getattr(game, "effects", None) is not None:
            game.effects.shake_screen(strength)
    except Exception:
        pass


# ============================================================================
# 9.  ANIMATION STATE (mirror ringan dari renderer, untuk debug + FX)
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

#: Fase timeline serangan (fraksi 0..1 dari durasi serangan).
ATTACK_PHASES = (
    ("ANTICIPATION", 0.00, 0.16),
    ("WINDUP",       0.16, 0.34),
    ("SWING",        0.34, 0.52),
    ("IMPACT",       0.52, 0.60),
    ("FOLLOW",       0.60, 0.80),
    ("RECOVERY",     0.80, 1.00),
)


def attack_phase(progress):
    """Kembalikan nama fase serangan untuk progress 0..1."""
    p = max(0.0, min(1.0, float(progress)))
    for name, a, b in ATTACK_PHASES:
        if a <= p < b:
            return name
    return "RECOVERY"


# ============================================================================
# 10.  DIRECTOR  —  satu per hero Zephyr
# ============================================================================

class ZephyrFXDirector:
    """Mengikat semua subsistem FX untuk satu instance Zephyr."""

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
        self.anim_phase = "IDLE"
        self.swing_active = False
        self._swing_seen = False
        self._skill_seen = None
        self._last_hp = None
        self.hit_flash = 0.0
        self.time = 0.0
        self.frames = 0

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def on_swing_start(self, x, y, facing):
        """Awal ayunan: reset trail + debu antisipasi."""
        self.trail.reset()
        self.swing_active = True
        self.particles.burst(
            x + facing * 6, y + 42, 5,
            speed=(30, 90), life=(0.2, 0.4), size=(2, 4),
            colors=(P["ash"], P["smoke"]),
            spread=1.1, direction=math.pi if facing > 0 else 0.0,
            gravity=90.0, drag=2.6, shape="pixel")

    def on_swing_end(self):
        self.swing_active = False

    def on_cast(self, x, y, skill):
        """Skill dilepas: buat SkillFX + shake ringan."""
        if len(self.skills) >= 3:
            self.skills.pop(0)
        self.skills.append(SkillFX(skill, x, y, self.particles))
        shake(3.0 if skill != "r" else 7.0,
              0.18 if skill != "r" else 0.42)

    def on_impact(self, x, y, angle=0.0, power=1.0, crit=False):
        """Benturan mengenai target: flash, spark, debris, shake, hit-stop."""
        if len(self.impacts) >= 8:
            self.impacts.pop(0)
        self.impacts.append(ImpactFX(x, y, angle, power, crit))

        n = int(9 + 7 * min(2.0, power)) + (6 if crit else 0)
        self.particles.burst(
            x, y, n, speed=(120, 340), life=(0.18, 0.44),
            size=(2, 4),
            colors=(P["fx_white"], P["fx_hot"], P["fx_bright"]),
            spread=2.4, direction=angle, drag=3.6, shape="streak")
        self.particles.burst(
            x, y, 6 + (4 if crit else 0),
            speed=(70, 190), life=(0.3, 0.65), size=(2, 5),
            colors=(P["thorn_lit"], P["ash"], P["fx_light"]),
            gravity=480.0, drag=1.1, shape="shard",
            rotation_speed=(-16.0, 16.0))

        shake(4.0 + 3.5 * min(2.0, power) + (3.0 if crit else 0.0),
              0.18 + 0.08 * min(2.0, power))
        hit_stop(0.038 + 0.02 * min(1.5, power) + (0.015 if crit else 0.0))

    def on_hurt(self, amount=1.0):
        """Zephyr terkena serangan: hit flash + percikan."""
        self.hit_flash = 0.16
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        self.particles.burst(
            hx, hy - 8, 7, speed=(80, 210), life=(0.2, 0.4),
            size=(2, 4), colors=(P["fx_light"], P["highlight"]),
            drag=3.0, shape="streak")

    # ------------------------------------------------------------------
    # State machine (prioritas + transisi)
    # ------------------------------------------------------------------
    def _resolve_state(self):
        h = self.hero
        if not getattr(h, "alive", True):
            return "DEATH"
        if self.hit_flash > 0.0:
            return "HURT"
        skill = getattr(h, "active_skill", None)
        if skill:
            return "SPECIAL" if skill == "r" else "SKILL"
        if getattr(h, "_zp_attack_active", False):
            prog = float(getattr(h, "_zp_attack_progress", 0.0))
            ph = attack_phase(prog)
            if ph in ("ANTICIPATION", "WINDUP"):
                return "CHARGE"
            if ph in ("SWING", "IMPACT"):
                return "SWING"
            return "ATTACK"
        if getattr(h, "_moving_cached", False):
            spd = float(getattr(h, "speed", 1.0))
            return "RUN" if spd >= 2.2 else "WALK"
        return "IDLE"

    def _update_state(self, dt):
        want = self._resolve_state()
        if want != self.state:
            # transisi hanya kalau prioritas >= state sekarang, atau
            # state sekarang sudah selesai (bukan state yang mengunci)
            cur_p = ANIM_PRIORITY.get(self.state, 0)
            new_p = ANIM_PRIORITY.get(want, 0)
            locked = self.state in ("DEATH",)
            if not locked and (new_p >= cur_p or self.state_time > 0.05):
                self.prev_state = self.state
                self.state = want
                self.state_time = 0.0
        self.state_time += dt
        self.anim_phase = attack_phase(
            float(getattr(self.hero, "_zp_attack_progress", 0.0)))

    # ------------------------------------------------------------------
    # Update / draw
    # ------------------------------------------------------------------
    def update(self, dt):
        self.time += dt
        self.frames += 1
        h = self.hero

        # deteksi kena damage untuk HURT
        hp = getattr(h, "hp", None)
        if hp is not None:
            if self._last_hp is not None and hp < self._last_hp - 0.01:
                self.on_hurt((self._last_hp - hp) / max(1.0,
                                                        getattr(h, "max_hp",
                                                                1.0)))
            self._last_hp = hp

        if self.hit_flash > 0.0:
            self.hit_flash = max(0.0, self.hit_flash - dt)

        self._update_state(dt)

        # skill cast detection (edge-triggered)
        skill = getattr(h, "active_skill", None)
        if skill != self._skill_seen:
            if skill:
                self.on_cast(float(getattr(h, "x", 0.0)),
                             float(getattr(h, "y", 0.0)) + 18, skill)
            self._skill_seen = skill

        # swing detection (edge-triggered pada fase SWING)
        swinging = self.anim_phase in ("SWING", "IMPACT") and \
            getattr(h, "_zp_attack_active", False)
        if swinging and not self._swing_seen:
            self.on_swing_start(float(getattr(h, "x", 0.0)),
                                float(getattr(h, "y", 0.0)),
                                1 if getattr(h, "facing", 1) >= 0 else -1)
        elif not swinging and self._swing_seen:
            self.on_swing_end()
        self._swing_seen = swinging

        # rekam posisi tongkat saat swing -> trail
        if swinging:
            grip, tip = self._staff_points()
            self.trail.push(grip, tip)

        self.trail.update(dt)
        self.particles.update(dt)
        self.projectiles.update(dt)

        if self.impacts:
            self.impacts = [i for i in self.impacts if i.update(dt)]
        if self.skills:
            self.skills = [s for s in self.skills if s.update(dt)]

    # ------------------------------------------------------------------
    def _staff_points(self):
        """Posisi layar (grip, tip) tongkat, dari pose renderer.

        Memakai geometri lokal renderer lalu dikonversi ke skala layar
        (_render_scale) sehingga trail benar-benar menempel di tongkat.
        """
        h = self.hero
        x = float(getattr(h, "x", 0.0))
        y = float(getattr(h, "y", 0.0))
        f = 1.0 if getattr(h, "facing", 1) >= 0 else -1.0
        scale = float(getattr(h, "_render_scale", 0.0) or 0.0)
        if scale <= 0.02:
            # sprite cache belum pernah miss untuk hero ini -> ambil
            # skala normalisasi resmi dari pipeline hero.
            try:
                from heroes import _get_hero_scale
                scale = float(_get_hero_scale(
                    getattr(h, "hero_type", "zephyr")))
            except Exception:
                scale = 1.0
        phase = float(getattr(h, "pulse", 0.0))
        prog = float(getattr(h, "_zp_attack_progress", 0.0))

        try:
            from heroes._bundle import _NS_zephyr as Z
            tip_l = Z._staff_tip_local(phase, "attack", prog)
        except Exception:
            tip_l = (44, -22)

        bottom_l = (2, 28)
        tip_x = x + tip_l[0] * f * scale
        tip_y = y + tip_l[1] * scale
        grip_x = x + (bottom_l[0] * 0.46 + tip_l[0] * 0.54) * f * scale
        grip_y = y + (bottom_l[1] * 0.46 + tip_l[1] * 0.54) * scale

        # Pita hanya menempati sepertiga LUAR tongkat: crescent tipis di
        # jalur ujung (bukan kipas lebar dari tangan), dan ujungnya
        # dipanjangkan sedikit supaya tetap terbaca pada skala arena.
        inner = pygame.Vector2(grip_x + (tip_x - grip_x) * 0.40,
                               grip_y + (tip_y - grip_y) * 0.40)
        outer = pygame.Vector2(grip_x + (tip_x - grip_x) * 1.18,
                               grip_y + (tip_y - grip_y) * 1.18)
        return inner, outer

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
        g = glow_surface(r, P["highlight"], self.hit_flash / 0.16 * 0.7)
        surface.blit(g, (int(getattr(h, "x", 0)) - r,
                         int(getattr(h, "y", 0)) - r - 6),
                     special_flags=pygame.BLEND_RGB_ADD)

    # ------------------------------------------------------------------
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
# 11.  DEBUG OVERLAY
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
    """Hitbox, hurtbox, attack range, state, timer, FPS, particle count."""
    h = director.hero
    x = int(getattr(h, "x", 0))
    y = int(getattr(h, "y", 0))
    rad = int(getattr(h, "radius", 16))
    rng = int(getattr(h, "range", 130))

    # attack range
    pygame.draw.circle(surface, (255, 90, 190), (x, y), rng, 1)
    # hurtbox
    pygame.draw.circle(surface, (90, 220, 255), (x, y), rad, 1)
    # hitbox serangan (kerucut di depan saat swing)
    if director.anim_phase in ("SWING", "IMPACT"):
        f = 1 if getattr(h, "facing", 1) >= 0 else -1
        pygame.draw.rect(surface, (255, 230, 90),
                         pygame.Rect(x if f > 0 else x - rng,
                                     y - 26, rng, 52), 1)
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
    except Exception:
        fps = 0
    st = director.stats()
    lines = [
        "ZEPHYR  %s / %s" % (st["state"], st["phase"]),
        "atkT %.2f  skill %s" % (
            float(getattr(h, "_zp_attack_progress", 0.0)),
            getattr(h, "active_skill", None)),
        "part %d  proj %d  imp %d" % (
            st["particles"], st["projectiles"], st["impacts"]),
        "shake %.1f  stop %d  fps %d" % (
            SHAKE.amount, HITSTOP.frames, fps),
    ]
    for i, txt in enumerate(lines):
        img = font.render(txt, True, (255, 220, 250))
        surface.blit(img, (x - 60, y - 88 + i * 13))


# ============================================================================
# 12.  API MODUL  —  registry, tick, hook render
# ============================================================================

_DIRECTORS = []
_LAST_TICK_MS = None


def director_for(hero):
    """Ambil (atau buat) director untuk sebuah hero Zephyr."""
    d = getattr(hero, "_zephyr_fx", None)
    if d is None:
        d = ZephyrFXDirector(hero)
        try:
            hero._zephyr_fx = d
        except Exception:
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:
            _DIRECTORS.pop(0)
    return d


def tick():
    """Majukan waktu FX satu frame nyata.  Aman dipanggil berkali-kali.

    Delta-time dihitung oleh bus ``combat_feel`` (dijepit supaya lonjakan
    frame saat loading / alt-tab tidak melempar partikel ke luar layar,
    dilambatkan saat hit-stop, dan shake-nya hanya dimundurkan SEKALI per
    frame walau beberapa karakter ikut bertempur).
    """
    global _LAST_TICK_MS
    if _feel is not None:
        # Guard frame-sama: draw_ground_layer() memanggil tick() untuk
        # SETIAP unit, sedangkan loop di bawah melangkahkan SEMUA
        # director. Tanpa guard ini 4 Zephyr di layar membuat FX maju
        # ~4x lebih cepat.
        now = pygame.time.get_ticks()
        if now == _LAST_TICK_MS:
            return 0.0                     # frame yang sama: sudah maju
        dt = _feel.fx_dt()
        _LAST_TICK_MS = now
    else:                                  # pragma: no cover - fallback
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
            d.update(dt)
    return dt


def reset_all():
    """Bersihkan seluruh state FX (ganti level / keluar match)."""
    global _LAST_TICK_MS
    _LAST_TICK_MS = None                   # jangan telan tick pertama
    for d in _DIRECTORS:
        d.particles.clear()
        d.projectiles.clear()
        d.trail.reset()
        d.impacts.clear()
        d.skills.clear()
    _DIRECTORS.clear()
    if _feel is not None:
        _feel.reset()
    else:                                  # pragma: no cover
        HITSTOP.frames = 0
        SHAKE.shake_strength = 0.0
        SHAKE.shake_duration = 0.0


def total_particles():
    """Jumlah partikel Zephyr hidup di seluruh arena (untuk HUD perf)."""
    return sum(d.particles.count() for d in _DIRECTORS)


# --- hook yang dipanggil heroes/__init__.py --------------------------------

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: dipanggil SEBELUM sprite hero di-blit."""
    if not ZEPHYR_FX_ENABLED:
        return
    tick()
    d = director_for(hero)
    d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: dipanggil SETELAH sprite hero di-blit."""
    if not ZEPHYR_FX_ENABLED:
        return
    d = director_for(hero)
    d.draw_front(surface)


# --- hook yang dipanggil _entity.py ----------------------------------------

def notify_projectile_impact(hero, x, y, angle=0.0, damage=0,
                             crit=False):
    """Projectile gameplay Zephyr mengenai target."""
    if not ZEPHYR_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except Exception:
        power = 1.0
    director_for(hero).on_impact(x, y, angle, power, crit)


def notify_skill_impact(hero, x, y, radius=70, skill="q"):
    """Skill Zephyr meledak di sebuah titik."""
    if not ZEPHYR_FX_ENABLED or hero is None:
        return
    d = director_for(hero)
    if len(d.skills) >= 3:
        d.skills.pop(0)
    d.skills.append(SkillFX(skill, x, y, d.particles, radius))


def draw_bolt(surface, px, py, angle=0.0, age=0, crit=False,
              radius=6.0):
    """Gambar bolt gameplay Zephyr (dipakai _entity._draw_projectile).

    Prosedural penuh dan BERARAH — bukan lingkaran polos:

        ekor meruncing -> halo lembut -> outline gelap -> badan layang
        -> bilah dalam -> duri fey -> inti piksel -> glint orbit

    Halo sengaja pakai ramp gelap (``fx_dark``) dengan daya rendah agar
    siluet badan tetap terbaca di atasnya.
    """
    x, y = int(px), int(py)
    ca, sa = math.cos(angle), math.sin(angle)
    nx, ny = -sa, ca                      # normal
    r = float(radius) * (1.2 if crit else 1.0)

    if crit:
        halo_c = (110, 74, 12)
        dark_c = (92, 58, 8)
        body_c = P["gold"]
        edge_c = P["highlight"]
    else:
        halo_c = P["fx_dark"]
        dark_c = P["fx_darkest"]
        body_c = P["fx_mid"]
        edge_c = P["fx_light"]

    # ── EKOR: poligon meruncing (motion streak) ──────────────────────
    tail = r * 4.2
    tail_poly = [
        (x + nx * r * 0.8, y + ny * r * 0.8),
        (x - ca * tail, y - sa * tail),
        (x - nx * r * 0.8, y - ny * r * 0.8),
    ]
    tb = _scratch(int(tail * 2 + 12), int(tail * 2 + 12))
    ox = int(tail + 6)
    pygame.draw.polygon(tb, (*dark_c, 120),
                        [(int(tx) - x + ox, int(ty) - y + ox)
                         for tx, ty in tail_poly])
    pygame.draw.polygon(tb, (*body_c, 90), [
        (int(x + nx * r * .4) - x + ox, int(y + ny * r * .4) - y + ox),
        (int(x - ca * tail * .62) - x + ox,
         int(y - sa * tail * .62) - y + ox),
        (int(x - nx * r * .4) - x + ox, int(y - ny * r * .4) - y + ox)])
    surface.blit(tb, (x - ox, y - ox))

    # ── HALO lembut (additive, daya rendah supaya tidak jadi cakram) ─
    gr = int(r * 2.1)
    surface.blit(glow_surface(gr, halo_c, 0.42), (x - gr, y - gr),
                 special_flags=pygame.BLEND_RGB_ADD)

    # ── BADAN: layang-layang panjang searah gerak ────────────────────
    ln_f = r * 3.1                     # panjang ke depan
    ln_b = r * 1.5                     # panjang ke belakang
    wd = r * 0.78
    body = [(x + ca * ln_f, y + sa * ln_f),
            (x + nx * wd - ca * r * .2, y + ny * wd - sa * r * .2),
            (x - ca * ln_b, y - sa * ln_b),
            (x - nx * wd - ca * r * .2, y - ny * wd - sa * r * .2)]
    ipoly = [(int(bx), int(by)) for bx, by in body]
    pygame.draw.polygon(surface, P["outline"],
                        [(bx + int(ca) - int(nx), by + int(sa) - int(ny))
                         for bx, by in ipoly])
    pygame.draw.polygon(surface, P["outline"],
                        [(bx + 1, by + 1) for bx, by in ipoly])
    pygame.draw.polygon(surface, body_c, ipoly)

    # bilah dalam (highlight sisi cahaya, kiri-atas)
    pygame.draw.polygon(surface, edge_c, [
        (int(x + ca * ln_f * .78), int(y + sa * ln_f * .78)),
        (int(x + nx * wd * .46), int(y + ny * wd * .46)),
        (int(x - ca * ln_b * .5), int(y - sa * ln_b * .5)),
        (int(x - nx * wd * .16), int(y - ny * wd * .16))])

    # ── DURI fey di pangkal ──────────────────────────────────────────
    for side in (-1, 1):
        bx = x - ca * r * 0.35 + nx * side * wd * 0.9
        by = y - sa * r * 0.35 + ny * side * wd * 0.9
        pygame.draw.line(
            surface, P["thorn_lit"], (int(bx), int(by)),
            (int(bx + nx * side * r * 0.95 - ca * r * 1.15),
             int(by + ny * side * r * 0.95 - sa * r * 1.15)), 2)

    # ── INTI piksel (chunky, hard edge) ──────────────────────────────
    cx_ = x + int(ca * r * .35)
    cy_ = y + int(sa * r * .35)
    s_ = max(2, int(r * .6))
    pygame.draw.rect(surface, P["fx_hot"],
                     (cx_ - s_ // 2, cy_ - s_ // 2, s_, s_))
    pygame.draw.rect(surface, P["fx_white"], (cx_ - 1, cy_ - 1, 2, 2))
    # kilau ujung
    pygame.draw.rect(surface, P["fx_white"],
                     (int(x + ca * ln_f * .9) - 1,
                      int(y + sa * ln_f * .9) - 1, 2, 2))

    # ── GLINT orbit ──────────────────────────────────────────────────
    spin = age * 0.35
    for i in range(3):
        a = spin + i * math.tau / 3
        pygame.draw.rect(surface, P["fx_bright"],
                         (x + int(math.cos(a) * r * 1.9),
                          y + int(math.sin(a) * r * 1.9), 2, 2))
