# ============================================================================
# heroes/abaddon_fx.py
# ----------------------------------------------------------------------------
# LAPISAN FX HIDUP ABADDON (LORD OF AVERNUS) - boss Level 1 / boss-hero.
#
# Renderer utama (bosses/level1.py, _NS_abaddon v3) menggambar BADAN +
# ground FX ke canvas. Yang harus bergerak 60 fps sejati - trail tebasan,
# proyektil Mist Coil / Darkness Gale / Death Sever, partikel api, impact,
# afterimage, dan umpan balik game-feel (hit-stop + screen shake) - hidup
# di modul ini, di layar skala 1:1, di luar sprite cache.
#
# Aturan pakai (sama persis dengan gornak_fx / zephyr_fx):
#   * ``draw_ground_layer``  -> pre-pass  (di bawah sprite): scorch, gust
#   * ``draw_live_layer``    -> post-pass (di atas sprite):  trail, proc,
#                           partikel, impact, afterimage, debug
#   * ``attach`` / ``owns``  -> renderer boss memutuskan apakah efek
#     ayunan & proyektil di-canvas masih perlu digambar (fallback)
#   * benturan               -> hit_stop(0.03-0.08) + shake lewat bus
#     heroes/combat_feel (satu sumber kebenaran untuk freeze & kamera)
#
# 100% prosedural: tidak ada aset eksternal, tidak ada pygame.image /
# pygame.mixer di sini.
# ============================================================================

import math
import pygame

try:
    from heroes import combat_feel as _feel
except Exception:                              # pragma: no cover
    _feel = None

#: Master switch lapisan hidup Abaddon (False = renderer canvas fallback).
ABADDON_FX_ENABLED = True

# ----------------------------------------------------------------------------
# DURASI SKILL (frame) - HARUS sama dengan active_skill_timer yang diisi
# AI boss (bosses/base_boss.py) dan SKILL_DUR di _NS_abaddon (level1.py).
# ----------------------------------------------------------------------------
SKILL_DUR = {"q": 30, "w": 90, "e": 40, "r": 60}

# Frame (progress 0..1) saat proyektil dilepas dari pose cast.
_SKILL_RELEASE = {"q": 0.42, "e": 0.38, "r": 0.55}

# ----------------------------------------------------------------------------
# PALETTE - mirror kunci warna _NS_abaddon.PALETTE (satu bahasa warna).
# Dihapus ketergantungan import level1 di sini supaya modul tetap bisa
# di-load saat file boss belum siap; nilai di-sync dari renderer.
# ----------------------------------------------------------------------------
_PALETTE = {
    "outline": (6, 6, 14),
    "shadow_deep": (4, 5, 12),
    "flame_darkest": (6, 42, 54),
    "flame_dark": (16, 92, 114),
    "flame_mid": (44, 172, 190),
    "flame_light": (98, 232, 240),
    "flame_bright": (168, 252, 252),
    "flame_hot": (220, 255, 255),
    "flame_white": (244, 255, 255),
    "magic_darkest": (24, 8, 52),
    "magic_dark": (56, 26, 116),
    "magic_mid": (106, 62, 182),
    "magic_light": (166, 122, 226),
    "magic_bright": (212, 178, 250),
    "magic_hot": (242, 222, 255),
    "white": (255, 255, 255),
    "ash_dark": (70, 62, 84),
    "ash_light": (130, 118, 148),
}


def _sync_palette():
    """Ambil ulang palette dari renderer boss (kalau bisa)."""
    try:
        from bosses.level1 import _NS_abaddon as G
        for k in list(_PALETTE):
            if k in G.PALETTE:
                _PALETTE[k] = G.PALETTE[k]
        for k, v in G.PALETTE.items():
            if k not in _PALETTE:
                _PALETTE[k] = v
    except Exception:                          # pragma: no cover
        pass


def _clamp(c):
    return tuple(max(0, min(255, int(v))) for v in c)


def _a(v):
    return max(0, min(255, int(v)))


def _hash01(i):
    x = math.sin(i * 127.1 + 311.7) * 43758.5453
    return x - math.floor(x)


# ============================================================================
# PRIMITIF DRAW (chunky, tanpa temp surface per panggilan di alpha penuh)
# ============================================================================

def _rect4(surface, color, alpha, x, y, w, h):
    a = _a(alpha)
    if a <= 0 or w <= 0 or h <= 0:
        return
    c = _clamp(color)
    if a >= 250:
        pygame.draw.rect(surface, c, (int(x), int(y), int(w), int(h)))
    else:
        pygame.draw.rect(
            surface, (c[0], c[1], c[2], a), (int(x), int(y), int(w), int(h)))


def _disc(surface, color, alpha, x, y, r):
    a = _a(alpha)
    if a <= 0 or r <= 0:
        return
    c = _clamp(color)
    if a >= 250:
        pygame.draw.circle(surface, c, (int(x), int(y)), int(r))
    else:
        pygame.draw.circle(
            surface, (c[0], c[1], c[2], a), (int(x), int(y)), int(r))


def _seg(surface, color, alpha, x0, y0, x1, y1, w=1):
    a = _a(alpha)
    if a <= 0:
        return
    c = _clamp(color)
    if a >= 250:
        pygame.draw.line(surface, c, (int(x0), int(y0)), (int(x1), int(y1)),
                         max(1, int(w)))
    else:
        pygame.draw.line(
            surface, (c[0], c[1], c[2], a),
            (int(x0), int(y0)), (int(x1), int(y1)), max(1, int(w)))


def _star(surface, cx, cy, size, color, alpha, spikes=8, rot=0.0,
          core=None):
    """Bintang kilat chunky (spike panjang-pendang selang-seling)."""
    if alpha <= 0 or size <= 0:
        return
    for k in range(spikes):
        ang = rot + k * math.pi * 2 / spikes
        ln = size * (1.0 if k % 2 == 0 else 0.5)
        _seg(surface, color, alpha, cx, cy,
             cx + math.cos(ang) * ln, cy + math.sin(ang) * ln * 0.85,
             2 if k % 2 == 0 else 1)
    if core:
        _disc(surface, core, alpha, cx, cy, max(1, int(size * 0.3)))


def _shard(surface, cx, cy, ang, length, width, color, alpha, core=None):
    """Serpihan kristal: belah ketupat runcing searah ``ang``."""
    if alpha <= 0 or length <= 1:
        return
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    a = _a(alpha)
    c = _clamp(color)
    pts = [(cx + ca * length, cy + sa * length),
           (cx + nx * width, cy + ny * width),
           (cx - ca * length * 0.45, cy - sa * length * 0.45),
           (cx - nx * width, cy - ny * width)]
    if a >= 250:
        pygame.draw.polygon(surface, c,
                            [(int(px), int(py)) for px, py in pts])
    else:
        pygame.draw.polygon(surface, (c[0], c[1], c[2], a),
                            [(int(px), int(py)) for px, py in pts])
    if core:
        _seg(surface, core, alpha, cx - ca * length * 0.3,
             cy - sa * length * 0.3, cx + ca * length * 0.8,
             cy + sa * length * 0.8, 1)


def _dash_ring(surface, cx, cy, radius, color, alpha, phase,
               segments=12, thick=3, squash=0.5):
    """Cincin PUTUS-PUTUS chunky (bukan lingkaran vektor halus)."""
    if alpha <= 0 or radius <= 1:
        return
    for i in range(segments):
        a0 = phase + i * math.pi * 2 / segments
        a1 = a0 + math.pi * 2 / segments * 0.62
        _seg(surface, color, alpha,
             cx + math.cos(a0) * radius, cy + math.sin(a0) * radius * squash,
             cx + math.cos(a1) * radius, cy + math.sin(a1) * radius * squash,
             thick)


# ============================================================================
# 1. PARTICLE SYSTEM
# ============================================================================

MAX_PARTICLES = 96


class Particle(object):
    __slots__ = ("x", "y", "vx", "vy", "ax", "ay", "g", "life", "max_life",
                 "size", "color", "kind", "rot", "rot_spd", "add", "dead")

    def __init__(self, x, y, vx, vy, life, size, color, kind,
                 ax=0.0, ay=0.0, g=0.0, rot=0.0, rot_spd=0.0, add=False):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.ax = float(ax)
        self.ay = float(ay)
        self.g = float(g)
        self.life = float(life)
        self.max_life = float(life)
        self.size = float(size)
        self.color = color
        self.kind = kind            # "square" | "shard" | "puff" | "spark"
        self.rot = float(rot)
        self.rot_spd = float(rot_spd)
        self.add = bool(add)
        self.dead = False

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.dead = True
            return
        self.vx += (self.ax + 0.0) * dt
        self.vy += (self.ay + self.g) * dt
        self.x += self.vx * dt * 60.0
        self.y += self.vy * dt * 60.0
        self.rot += self.rot_spd * dt * 60.0

    def draw(self, surface):
        t = max(0.0, self.life / self.max_life)
        if self.kind == "puff":
            a = _a(150 * t)
            s = int(self.size * (1.6 - t * 0.8))
            _rect4(surface, self.color, a * 0.8,
                   self.x - s / 2, self.y - s / 2, s, s)
        elif self.kind == "shard":
            a = _a(235 * t)
            _shard(surface, self.x, self.y, self.rot,
                   self.size * (0.6 + 0.4 * t), max(1, self.size * 0.36),
                   self.color, a)
        elif self.kind == "spark":
            a = _a(255 * t)
            _seg(surface, self.color, a, self.x, self.y,
                 self.x - self.vx * 1.6, self.y - self.vy * 1.6, 1)
        else:  # square (chunky pixel)
            a = _a(235 * t)
            s = max(1, int(self.size * (0.5 + 0.5 * t)))
            if self.add:
                s = max(1, s - 1)
            _rect4(surface, self.color, a,
                   self.x - s / 2, self.y - s / 2, s, s)
            if self.add and t > 0.4:
                _disc(surface, _PALETTE["flame_white"], _a(a * 0.7),
                      self.x, self.y, max(1, s // 2))


class ParticleSystem(object):
    def __init__(self, cap=MAX_PARTICLES):
        self.items = []
        self.cap = cap

    def count(self):
        return len(self.items)

    def spawn(self, **kw):
        if len(self.items) >= self.cap:
            self.items.pop(0)
        self.items.append(Particle(**kw))

    def burst(self, x, y, n, speed=2.4, life=0.5, size=3, color=None,
              kind="square", g=0.4, spread=math.pi * 2,
              base_ang=0.0, add=False, rot_spd=1.8):
        for i in range(n):
            ang = base_ang + (0.5 - _hash01(i * 13 + 7)) * spread
            sp = speed * (0.45 + 0.75 * _hash01(i * 7 + 3))
            self.spawn(
                x=x, y=y,
                vx=math.cos(ang) * sp, vy=math.sin(ang) * sp,
                life=life * (0.6 + 0.6 * _hash01(i * 5 + 1)),
                size=size * (0.7 + 0.5 * _hash01(i * 11 + 2)),
                color=color or _PALETTE["flame_mid"],
                kind=kind, g=g, add=add,
                rot=ang, rot_spd=rot_spd * (0.5 + _hash01(i * 3)))

    def update(self, dt):
        for p in self.items:
            p.update(dt)
        if any(p.dead for p in self.items):
            self.items = [p for p in self.items if not p.dead]

    def draw(self, surface):
        for p in self.items:
            p.draw(surface)

    def clear(self):
        self.items = []


# ============================================================================
# 2. PROJECTILE (live, layar 1:1) - lifecycle: SPAWN->TRAVEL->HIT->IMPACT
# ============================================================================

MAX_PROJECTILES = 10


class AbaddonProjectile(object):
    """Proyektil Abaddon di ruang LAYAR (bukan canvas cache).

    kind:
      * "coil"  - Mist Coil (Q): bola kabut ke target + after-image kuantisasi
      * "gale"  - Darkness Gale (E): dinding angin gelap menjalar ke depan
      * "sever" - Death Sever (R): busur bulan sabit raksasa ungu
    """

    def __init__(self, kind, x, y, tx, ty, direction, speed, life,
                 radius, power=1.0):
        self.kind = kind
        self.x = float(x)
        self.y = float(y)
        self.tx = float(tx)
        self.ty = float(ty)
        self.direction = int(direction) or 1
        self.speed = float(speed)
        self.life = float(life)
        self.radius = int(radius)
        self.power = float(power)
        self.age = 0.0
        self.rot = 0.0
        self.active = True
        self.hit = False
        self.trail = []          # (x, y) - after-image kuantisasi
        self._stamp = 0
        dx, dy = tx - x, ty - y
        self.ang = math.atan2(dy, dx)

    # ------------------------------------------------------------------
    def update(self, dt, on_hit):
        if not self.active:
            return
        step = dt * 60.0
        self.age += dt
        # masa penundaan (lepas di frame release skill): diam & tak
        # digambar (draw_front memfilter age >= 0), setelah itu baru
        # terbang.
        if self.age < 0.0:
            self.rot += step * (3.2 if self.kind == "coil" else 1.6)
            return
        self.rot += step * (3.2 if self.kind == "coil" else 1.6)
        if self.kind == "coil":
            # kejar target (target tracking)
            dx, dy = self.tx - self.x, self.ty - self.y
            d = math.hypot(dx, dy)
            if d < self.speed * step + 5:
                self.x, self.y = self.tx, self.ty
                self._fire(on_hit)
                return
            self.x += dx / d * self.speed * step
            self.y += dy / d * self.speed * step
            self.ang = math.atan2(dy, dx)
        else:
            self.x += math.cos(self.ang) * self.speed * step
            self.y += math.sin(self.ang) * self.speed * step * 0.25
        # after-image kuantisasi (stamp tiap 2 langkah, hanya setelah lepas)
        self._stamp += 1
        if self.age < 0:
            return
        if self._stamp % 2 == 0:
            self.trail.append((int(self.x // 3) * 3, int(self.y // 3) * 3))
            if len(self.trail) > 8:
                self.trail.pop(0)
        if self.age >= self.life:
            self._fire(on_hit)

    def _fire(self, on_hit):
        if self.hit:
            return
        self.hit = True
        self.active = False
        if on_hit is not None:
            on_hit(self)

    # ------------------------------------------------------------------
    def draw(self, surface):
        px, py = int(self.x), int(self.y)
        fade = max(0.0, 1.0 - self.age / max(0.1, self.life))
        if self.kind == "coil":
            self._draw_coil(surface, px, py, fade)
        elif self.kind == "gale":
            self._draw_gale(surface, px, py, fade)
        else:
            self._draw_sever(surface, px, py, fade)

    # -- Q: bola kabut mist (chunky + arah + after-image) --------------
    def _draw_coil(self, surface, px, py, fade):
        P = _PALETTE
        # after-image: stamp persegi kuantisasi memudar (bukan garis halus)
        n = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            a = _a(120 * (i + 1) / max(1, n) * fade)
            if a <= 4:
                continue
            s = 3 + (n - i)
            _rect4(surface, P["magic_dark"], a, tx - s // 2, ty - s // 2, s, s)
            _disc(surface, P["magic_mid"], a, tx, ty, max(1, s // 3))
        # ekor spike arah gerak
        for off in (-4, 0, 4):
            nx, ny = -math.sin(self.ang), math.cos(self.ang)
            ox, oy = nx * off, ny * off
            _seg(surface, P["magic_light"], _a(170 * fade),
                 px - math.cos(self.ang) * 14 + ox,
                 py - math.sin(self.ang) * 14 + oy,
                 px - math.cos(self.ang) * 30 + ox,
                 py - math.sin(self.ang) * 30 + oy, 2)
        # inti berlapis (bukan satu lingkaran polos)
        _disc(surface, P["magic_darkest"], _a(200 * fade), px, py, 10)
        _disc(surface, P["magic_dark"], _a(225 * fade), px, py, 8)
        _disc(surface, P["magic_mid"], _a(240 * fade), px, py, 6)
        _disc(surface, P["flame_mid"], _a(240 * fade), px, py, 4)
        _disc(surface, P["flame_bright"], _a(250 * fade), px, py, 3)
        _disc(surface, P["flame_hot"], _a(255 * fade), px, py, 2)
        _rect4(surface, P["flame_white"], _a(255 * fade), px - 1, py - 1, 2, 2)
        # dua puing kabut mengorbit spiral
        for k in range(2):
            oa = self.rot * 1.4 + k * math.pi
            ox = px + math.cos(oa) * 9
            oy = py + math.sin(oa) * 9 * 0.8
            _disc(surface, P["magic_light"], _a(200 * fade), ox, oy, 2)
            _disc(surface, P["flame_hot"], _a(230 * fade), ox, oy, 1)

    # -- E: dinding angin gelap (crescent chunky + leading edge) -------
    def _draw_gale(self, surface, px, py, fade):
        P = _PALETTE
        d = self.direction
        # 9 balok vertikal membentuk busur melengkung, melengkung ke belakang
        for i in range(9):
            t = i / 8.0
            yy = py - 17 + t * 34
            bow = (1.0 - abs(t - 0.5) * 2) ** 1.6
            xx = px - d * int(6 + bow * 12)
            a = _a(235 * fade * (0.45 + 0.55 * bow))
            w = int(3 + bow * 3)
            _rect4(surface, P["magic_darkest"], _a(a * 0.85),
                   xx - w // 2, yy - 3, w, 7)
            _rect4(surface, P["magic_mid"], a, xx - w // 2 + 1, yy - 2,
                   max(1, w - 2), 5)
            if bow > 0.55:
                _rect4(surface, P["flame_light"], _a(a * 0.9),
                       xx - w // 2 + 1, yy - 1, max(1, w - 2), 2)
        # leading edge putih-panas di depan
        for i in range(7):
            t = i / 6.0
            yy = py - 14 + t * 28
            bow = (1.0 - abs(t - 0.5) * 2) ** 1.6
            xx = px + d * int(2 + bow * 2)
            _rect4(surface, P["flame_bright"], _a(235 * fade * bow),
                   xx - 1, yy - 1, 3, 3)
        # 3 streak horizontal ke belakang
        for i, off in enumerate((-8, 0, 8)):
            _seg(surface, P["magic_dark"], _a(190 * fade),
                 px - d * 18, py + off, px - d * 44, py + off + 2, 3)
            _seg(surface, P["magic_light"], _a(140 * fade),
                 px - d * 16, py + off, px - d * 38, py + off + 2, 1)
        # ujung depan menyala
        _star(surface, px + d * 5, py, int(7 * fade + 3),
              P["flame_light"], _a(220 * fade), spikes=4,
              rot=self.rot, core=P["flame_white"])

    # -- R: busur bulan sabit raksasa (pita berlapis + inti panas) -----
    def _draw_sever(self, surface, px, py, fade):
        P = _PALETTE
        d = self.direction
        R = 24
        a0 = self.rot * 0.5
        # pita: 3 lapis lebar (gelap->terang) + inti putih
        for w, col, am in ((15, P["magic_darkest"], 0.75),
                           (10, P["magic_mid"], 0.95),
                           (5, P["magic_bright"], 1.0),
                           (2, P["flame_hot"], 1.0)):
            a = _a(235 * fade * am)
            prev = None
            for i in range(13):
                t = i / 12.0
                ang = a0 + (t - 0.5) * 1.9
                ex = px + math.cos(ang) * R * 0.4 * d
                ey = py + math.sin(ang) * R
                q = (int(ex), int(ey))
                if prev is not None:
                    _seg(surface, col, a, prev[0], prev[1], q[0], q[1], w)
                prev = q
        # 6 serpihan ungu berputar di belakang busur
        for i in range(6):
            sa = a0 + 1.15 + _hash01(i * 5) * 0.5
            sr = R * (0.6 + 0.5 * _hash01(i * 9))
            sx = px + math.cos(sa) * sr * 0.4 * d
            sy = py + math.sin(sa) * sr
            _shard(surface, sx, sy, sa + math.pi / 2, 6, 2,
                   P["magic_light"], _a(210 * fade))
        # inti putih di pucuk busur
        for t in (0.0, 1.0):
            ang = a0 + (t - 0.5) * 1.9
            tx = px + math.cos(ang) * R * 0.4 * d
            ty = py + math.sin(ang) * R
            _disc(surface, P["flame_white"], _a(255 * fade), tx, ty, 2)


# ============================================================================
# 3. IMPACT FX - flash + cincin chunky + serpihan + shock + scorch
# ============================================================================

MAX_IMPACTS = 14


class ImpactFX(object):
    def __init__(self, x, y, ang, power, kind):
        self.x = float(x)
        self.y = float(y)
        self.ang = float(ang)
        self.power = float(power)
        self.kind = kind            # "blade" | "coil" | "gale" | "sever"
        self.age = 0.0
        self.life = 0.42 if kind != "sever" else 0.62
        P = _PALETTE
        self.c1 = P["magic_mid"] if kind in ("sever", "coil") else P["flame_mid"]
        self.c2 = (P["magic_bright"] if kind in ("sever", "coil")
                   else P["flame_bright"])
        self.c3 = P["flame_white"]
        self.done = False

    def update(self, dt):
        self.age += dt
        if self.age >= self.life:
            self.done = True

    def draw(self, surface):
        t = self.age / self.life
        k = 1.0 - t
        P = _PALETTE
        # flash bintang di frame awal
        if t < 0.35:
            s = int((14 + t * 26) * self.power * (1.0 - t / 0.35 * 0.4))
            _star(surface, self.x, self.y, s, self.c2,
                  _a(245 * (1 - t / 0.35)), spikes=8,
                  rot=self.ang + t * 4.0, core=P["white"])
        # cincin chunky mengembang (putus-putus, bukan lingkaran halus)
        r = int((10 + t * 46) * self.power)
        _dash_ring(surface, self.x, self.y, r, self.c1, _a(200 * k),
                   t * 3.0 + self.ang, segments=12,
                   thick=max(2, int(3 * self.power)), squash=0.55)
        _dash_ring(surface, self.x, self.y, int(r * 0.62), self.c2,
                   _a(150 * k), -t * 4.0, segments=8, thick=2,
                   squash=0.55)
        # serpihan beterbangan (deterministik dari seed per impact)
        for i in range(7):
            u = t * (0.55 + 0.75 * _hash01(i * 7 + 11))
            a = self.ang + (0.5 - _hash01(i * 13)) * 2.6
            d = u * 58 * self.power
            _shard(surface, self.x + math.cos(a) * d,
                   self.y + math.sin(a) * d * 0.8,
                   a + t * 5, 5 * (1 - t) + 2, 2,
                   self.c1 if i % 2 else self.c2, _a(225 * k))


class Scorch(object):
    """Jejak gosong di tanah yang memudar (ground decal)."""

    def __init__(self, x, y, radius, color):
        self.x = float(x)
        self.y = float(y)
        self.radius = int(radius)
        self.color = color
        self.age = 0.0
        self.life = 1.4
        self.done = False

    def update(self, dt):
        self.age += dt
        if self.age >= self.life:
            self.done = True

    def draw(self, surface):
        t = self.age / self.life
        a = _a(150 * (1 - t))
        r = self.radius
        _rect4(surface, _PALETTE["shadow_deep"], _a(a * 0.9),
               self.x - r // 2, self.y - r // 6, r, r // 3)
        _rect4(surface, self.color, _a(a * 0.5),
               self.x - r // 3, self.y - r // 8, r * 2 // 3, r // 4)


# ============================================================================
# 5. TRAIL TEBASAN (sampel ujung bilah -> pita berlapis)
# ============================================================================

class SwingTrail(object):
    """Pita trail dari SEMPEL posisi ujung bilah di waktu lampau.

    Renderer (level1) mengisi ``samples`` (list (x, y) dari lama ke baru)
    setiap frame selama jendela tebas. Modul ini menggambar pita 3 lapis +
    leading edge + speed line, lalu menghapusnya saat tebas selesai.
    """

    def __init__(self):
        self.samples = []
        self.visible = False

    def set(self, samples, visible):
        self.samples = samples
        self.visible = visible

    def clear(self):
        self.samples = []
        self.visible = False

    def draw(self, surface, hot=False):
        path = self.samples
        if not self.visible or len(path) < 3:
            return
        P = _PALETTE
        c_dark = P["magic_darkest"] if hot else P["flame_darkest"]
        c_mid = P["magic_mid"] if hot else P["flame_mid"]
        c_bright = P["magic_bright"] if hot else P["flame_bright"]
        c_hot = P["magic_hot"] if hot else P["flame_hot"]
        c_core = P["flame_white"]
        # lebar pita: tipis di ekor, tebal di pucuk
        n = len(path)
        for wmul, col, am in ((1.6, c_dark, 0.42), (1.0, c_mid, 0.92),
                              (0.4, c_bright, 1.0)):
            a = _a(235 * am)
            for i in range(n - 1):
                t = (i + 1) / n
                w = max(1, int(7.5 * t * t * wmul))
                _seg(surface, col, a, path[i][0], path[i][1],
                     path[i + 1][0], path[i + 1][1], w)
        # leading edge 1 px paling terang (arah gerak terbaca)
        for i in range(n - 3, n - 1):
            _seg(surface, c_core, _a(245), path[i][0], path[i][1],
                 path[i + 1][0], path[i + 1][1], 1)
        # speed line di dalam busur
        for k in range(2):
            i0 = 2 + k * 3
            i1 = min(n - 1, i0 + 4)
            if i0 < i1:
                _seg(surface, c_hot, _a(170), path[i0][0], path[i0][1],
                     path[i1][0], path[i1][1], 1)


# ============================================================================
# 6. DIRECTOR - state per unit (dipatok di objek boss/hero)
# ============================================================================

_DIRECTORS = []
_last_tick_ms = None


class AbaddonFXDirector(object):
    def __init__(self, hero):
        self.hero = hero
        self.particles = ParticleSystem()
        self.projectiles = []
        self.impacts = []
        self.scorch = []
        self.trail = SwingTrail()
        self.last_x = float(getattr(hero, "x", 0.0))
        self.last_y = float(getattr(hero, "y", 0.0))
        self._prev_skill = None
        self._prev_timer = None
        self._frame = 0
        self._swing_id = None
        self._swing_impact_done = False

    # ------------------------------------------------------------------
    def _target_pos(self):
        t = getattr(self.hero, "target", None)
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        if t is not None and getattr(t, "alive", True):
            return float(t.x), float(t.y)
        d = int(getattr(self.hero, "direction", 1)) or 1
        return hx + 160.0 * d, hy

    # ------------------------------------------------------------------
    def update(self, dt, hx, hy):
        self.last_x = hx
        self.last_y = hy
        self._frame += 1
        self.particles.update(dt)
        for p in self.projectiles:
            p.update(dt, self._on_projectile_hit)
        self.projectiles = [p for p in self.projectiles if not p.hit]
        for im in self.impacts:
            im.update(dt)
        self.impacts = [im for im in self.impacts if not im.done]
        for sc in self.scorch:
            sc.update(dt)
        self.scorch = [sc for sc in self.scorch if not sc.done]

        skill = getattr(self.hero, "active_skill", None)
        timer = int(getattr(self.hero, "active_skill_timer", 0) or 0)
        if skill and skill != self._prev_skill:
            self.on_cast(hx, hy, skill, timer)
        self._prev_skill = skill
        self._prev_timer = timer

        # partikel ambient: bara api naik dari tunggangan (murah, dibatasi)
        if (dt > 0 and self._frame % 3 == 0
                and len(self.particles.items) < 32):
            d = int(getattr(self.hero, "direction", 1)) or 1
            fx0 = _hash01(self._frame * 0.61 + 2)
            self.particles.spawn(
                x=hx + (d * 10 - 6) + (fx0 - 0.5) * 30,
                y=hy + 42,
                vx=(fx0 - 0.5) * 0.5,
                vy=-0.9 - fx0 * 0.9,
                life=0.5, size=3, color=_PALETTE["flame_mid"],
                kind="square", g=-0.4, add=True)

        # trail tebasan + impact basic attack (sumber pose: renderer boss)
        self._sync_swing(dt)

        # deketasi: partikel/proyektil tidak boleh hidup tanpa batas
        if len(self.particles.items) > MAX_PARTICLES:
            del self.particles.items[:len(self.particles.items) - MAX_PARTICLES]
        if len(self.impacts) > MAX_IMPACTS:
            del self.impacts[:len(self.impacts) - MAX_IMPACTS]
        if len(self.scorch) > 8:
            del self.scorch[:len(self.scorch) - 8]
        if len(self.projectiles) > MAX_PROJECTILES:
            del self.projectiles[:len(self.projectiles) - MAX_PROJECTILES]

    # ------------------------------------------------------------------
    def _sync_swing(self, dt):
        """Trail pita tebasan dari ujung bilah dunia (ruang layar 1:1).

        Pose dihitung oleh renderer boss (``_NS_abaddon._swing_tip``) -
        modul ini hanya merekam jejaknya di layar, jadi trail tidak
        pernah lepas dari bilah di lane mana pun (boss maupun hero).
        Impact basic attack dipicu SEKALI per ayunan saat frame impact
        dilewati (hit-stop + shake + flash di titik pendaratan).
        """
        try:
            from bosses.level1 import _NS_abaddon as G
            st = G._swing_tip(self.hero, float(self.hero.x), float(self.hero.y))
        except Exception:
            st = None
        trail = self.trail
        if st is None:
            trail.clear()
            self._swing_id = None
            return
        ap = st["ap"]
        active = bool(st["active"])
        if not active:
            trail.clear()
            self._swing_id = None
            self._swing_impact_done = False
            return
        if st.get("trailing"):
            trail.samples.append((int(st["tip_x"]), int(st["tip_y"])))
            if len(trail.samples) > 14:
                trail.samples.pop(0)
            trail.visible = True
        else:
            trail.clear()
        # impact sekali per ayunan
        sid = st.get("swing_id")
        if sid is not None and self._swing_id != sid:
            self._swing_id = sid
            self._swing_impact_done = False
        if not self._swing_impact_done and ap >= st["impact_frame"]:
            self._swing_impact_done = True
            ang = math.atan2(st["tip_y"] - self.last_y,
                             st["tip_x"] - self.last_x)
            power = 1.15 if st.get("hot") else 1.0
            self.on_swing_impact(st["tip_x"], st["tip_y"], ang, power=power)

    # ------------------------------------------------------------------
    def _on_projectile_hit(self, pr):
        tx, ty = pr.x, pr.y
        kind = pr.kind
        self.impacts.append(ImpactFX(tx, ty, pr.ang, pr.power, kind))
        self.scorch.append(Scorch(tx, ty + 14, 22,
                                  _PALETTE["magic_mid"] if kind in
                                  ("sever", "coil") else
                                  _PALETTE["flame_mid"]))
        self.particles.burst(tx, ty, 9, speed=3.0, life=0.5, size=4,
                             color=_PALETTE["magic_mid"] if kind in
                             ("sever", "coil") else _PALETTE["flame_mid"],
                             kind="shard", g=0.5)
        self.particles.burst(tx, ty, 6, speed=2.0, life=0.45, size=3,
                             color=_PALETTE["flame_bright"], kind="spark",
                             g=0.2, add=True)
        if kind == "sever":
            _feel_hit_stop(0.06)
            _feel_shake(9.0, 0.4)
        elif kind == "coil":
            _feel_hit_stop(0.036)
            _feel_shake(4.5, 0.18)
        else:
            _feel_hit_stop(0.035)
            _feel_shake(5.0, 0.2)

    # ------------------------------------------------------------------
    def on_cast(self, hx, hy, skill, timer):
        """Skill baru terdeteksi (edge active_skill)."""
        if skill not in SKILL_DUR:
            return
        tx, ty = self._target_pos()
        d = int(getattr(self.hero, "direction", 1)) or 1
        dur = SKILL_DUR[skill]

        rel = _SKILL_RELEASE.get(skill)
        if rel is not None:
            # proyektil dijadwalkan lepas di frame release.
            # dur = jumlah FRAME (SKILL_DUR) -> konversi ke DETIK supaya
            # sesuai dengan update() yang menambah ``dt`` dalam detik.
            spawn_at = (1.0 - rel) * float(dur) / 60.0
            if skill == "q":
                self._schedule("coil", spawn_at, hx + 30 * d, hy - 20,
                               tx, ty, d, speed=7.5, life=1.6, radius=9)
            elif skill == "e":
                self._schedule("gale", spawn_at, hx + 34 * d, hy - 8,
                               tx, ty, d, speed=13.0, life=0.9, radius=12)
            else:
                self._schedule("sever", spawn_at, hx + 34 * d, hy - 12,
                               tx, ty, d, speed=10.0, life=1.5, radius=16)
        if skill == "r":
            _feel_shake(6.0, 0.3)
        # kilat cast (tanda baca universal: skill baru saja keluar)
        self.particles.burst(hx, hy - 18, 5, speed=2.2, life=0.4,
                             size=3, color=_PALETTE["flame_light"],
                             kind="spark", g=-0.1, add=True)

    def _schedule(self, kind, delay_s, x, y, tx, ty, d, speed, life,
                  radius):
        p = AbaddonProjectile(kind, x, y, tx, ty, d, speed, life, radius)
        p.age = -delay_s          # mundur -> update() menunda gerak
        self.projectiles.append(p)

    # ------------------------------------------------------------------
    def on_swing_impact(self, x, y, ang, power=1.0, hot=False):
        """Tebasan basic attack mendarat (dipanggil saat frame impact)."""
        self.impacts.append(ImpactFX(x, y, ang, power, "blade"))
        self.particles.burst(x, y, 7, speed=2.8, life=0.45, size=4,
                             color=_PALETTE["flame_mid"], kind="shard",
                             g=0.6)
        self.particles.burst(x, y, 4, speed=1.8, life=0.5, size=5,
                             color=_PALETTE["ash_dark"], kind="puff",
                             g=-0.3)
        _feel_hit_stop(0.035 + 0.012 * min(1.5, power))
        _feel_shake(4.0 + 2.6 * power, 0.2)

    def on_impact(self, x, y, ang, power=1.0, crit=False, kind="blade"):
        """Benturan yang diberitahu gameplay (basic attack kena target)."""
        self.impacts.append(ImpactFX(x, y, ang, power * (1.25 if crit
                                                         else 1.0),
                                     kind))
        self.particles.burst(x, y, 8 if crit else 6,
                             speed=3.0 if crit else 2.4, life=0.5,
                             size=4, color=_PALETTE["flame_mid"],
                             kind="shard", g=0.5)
        self.particles.burst(x, y, 4, speed=2.0, life=0.4, size=3,
                             color=_PALETTE["flame_bright"], kind="spark",
                             g=0.2, add=True)
        _feel_hit_stop(0.036 + 0.018 * min(1.5, power) +
                       (0.014 if crit else 0.0))
        _feel_shake(4.0 + 3.2 * power + (3.0 if crit else 0.0), 0.22)

    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        for sc in self.scorch:
            sc.draw(surface)

    def draw_front(self, surface, x, y):
        # trail tebas
        self.trail.draw(surface,
                        hot=getattr(self.hero, "active_skill", None) == "r")
        # proyektil
        for pr in self.projectiles:
            if pr.age >= 0:
                pr.draw(surface)
        # partikel
        self.particles.draw(surface)
        # impact
        for im in self.impacts:
            im.draw(surface)


# ============================================================================
# 7. GAME-FEEL (lewat bus combat_feel - satu sumber kebenaran)
# ============================================================================

def _feel_shake(strength, duration):
    if _feel is not None:
        try:
            _feel.shake(strength, duration)
        except Exception:                      # pragma: no cover
            pass


def _feel_hit_stop(seconds):
    if _feel is not None:
        try:
            _feel.hit_stop(seconds)
        except Exception:                      # pragma: no cover
            pass


# nama lama tetap hidup (dipakai modul karakter & tooling)
def hit_stop(seconds=0.045):
    _feel_hit_stop(seconds)


def shake(strength=5.0, duration=0.22):
    _feel_shake(strength, duration)


# ============================================================================
# 8. API MODUL - registry, tick, hook render & gameplay
# ============================================================================

def director_for(hero):
    """Ambil (atau buat) director FX untuk satu unit Abaddon."""
    _sync_palette()
    d = getattr(hero, "_ab_fx", None)
    if d is None:
        d = AbaddonFXDirector(hero)
        try:
            hero._ab_fx = d
        except Exception:                      # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:               # jangkar tua dibuang
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    try:
        if director.hero is not None:
            director.hero._ab_fx = None
            director.hero._ab_live_fx = False
    except Exception:                          # pragma: no cover
        pass
    director.particles.clear()
    director.projectiles = []
    director.impacts = []
    director.scorch = []
    director.trail.clear()


def attach(hero):
    """Pasang lapisan hidup pada unit ini (dipanggil renderer / pipeline).

    Menandai unit supaya renderer TIDAK menggambar trail & proyektil
    di-canvas (lapisan hidup yang menggantikannya).
    """
    if not ABADDON_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                          # pragma: no cover
        return False
    try:
        hero._ab_live_fx = True
    except Exception:                          # pragma: no cover
        return False
    return True


def owns(hero):
    """True kalau lapisan hidup sudah mengambil alih efek unit ini.

    Dipakai renderer untuk memutuskan apakah trail tebas & proyektil
    di-canvas masih perlu digambar (fallback). Unit tanpa director
    (potongan portrait, alat uji) tetap memakai jalur canvas.
    """
    if not getattr(hero, "_ab_live_fx", False):
        return False
    d = getattr(hero, "_ab_fx", None)
    return d is not None and d in _DIRECTORS


def tick(dt=None):
    """Majukan waktu FX satu frame nyata; aman dipanggil berkali-kali.

    Delta-time dihitung bus ``combat_feel``: dijit, diperlambat saat
    hit-stop (slow-motion), shake hanya dimundurkan sekali per frame.
    """
    global _last_tick_ms
    if dt is not None:
        step = max(0.0, min(1.0 / 20.0, float(dt)))
        _advance(step)
        return step
    if _feel is not None:
        try:
            step = _feel.fx_dt()
        except Exception:                      # pragma: no cover
            step = 0.0
    else:                                      # pragma: no cover - fallback
        now = pygame.time.get_ticks()
        if _last_tick_ms is None:
            _last_tick_ms = now
            step = 0.0
        else:
            ms = now - _last_tick_ms
            _last_tick_ms = now
            step = max(1.0 / 240.0, min(1.0 / 20.0, ms / 1000.0))                 if ms > 0 else 0.0
    if step <= 0.0:
        # Frame pertama sejak boot (bus belum punya acuan): pakai langkah
        # default supaya skill/proyektil tetap terpasang pada frame ini.
        step = 1.0 / 60.0
    _advance(step)
    return step


def _advance(step):
    if step <= 0.0 or not _DIRECTORS:
        return
    for d in _DIRECTORS:
        h = d.hero
        d.update(step, float(getattr(h, "x", 0.0)),
                 float(getattr(h, "y", 0.0)))


def reset_all():
    """Bersihkan seluruh state FX Abaddon (ganti level / keluar match)."""
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()


def total_particles():
    """Jumlah partikel Abaddon hidup di seluruh arena (dipakai HUD)."""
    return sum(d.particles.count() for d in _DIRECTORS)


def projectiles_for(hero):
    """List proyektil milik unit (dipakai overlay debug)."""
    d = getattr(hero, "_ab_fx", None)
    if d is None:
        return []
    return list(d.projectiles)


def stats():
    st = {"particles": 0, "projectiles": 0, "impacts": 0}
    for d in _DIRECTORS:
        st["particles"] += d.particles.count()
        st["projectiles"] += len(d.projectiles)
        st["impacts"] += len(d.impacts)
    return st


# ----------------------------------------------------------------------------
# 9. HOOK RENDER (dipanggil heroes/__init__.py / renderer boss)
# ----------------------------------------------------------------------------

def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: digambar SEBELUM sprite di-blit."""
    if not ABADDON_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_ab_fx", None)
    if d is not None:
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: digambar SESUDAH sprite di-blit."""
    if not ABADDON_FX_ENABLED:
        return
    d = director_for(hero)
    d.draw_front(surface, x, y)


# ----------------------------------------------------------------------------
# 10. HOOK GAMEPLAY (dipanggil bosses/base_boss.py / _entity.py)
# ----------------------------------------------------------------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    """Bilah Abaddon mendarat di target (basic attack melee)."""
    if not ABADDON_FX_ENABLED or hero is None or target is None:
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
                                 kind="blade")


def notify_skill_cast(hero, skill):
    """Skill dilepas (opsional - director sudah mendeteksi tepi sendiri)."""
    if not ABADDON_FX_ENABLED or hero is None or skill not in SKILL_DUR:
        return
    d = director_for(hero)
    d.on_cast(float(getattr(hero, "x", 0.0)),
              float(getattr(hero, "y", 0.0)), skill,
              int(getattr(hero, "active_skill_timer", 0) or 0))


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False,
                             kind="coil"):
    """Proyektil Abaddon mengenai target (dipanggil gameplay bila ada)."""
    if not ABADDON_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    director_for(hero).on_impact(x, y, angle, power, bool(crit), kind=kind)
