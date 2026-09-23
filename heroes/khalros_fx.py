# ============================================================================
# heroes/khalros_fx.py
# ----------------------------------------------------------------------------
# LAPISAN FX HIDUP KHALROS "THE BEASTLORD" (boss Level 2 / boss-hero).
#
# V2: BADAN TIDAK LAGI DIGAMBAR DI SINI. Rig pixel masterwork hidup di
# ``bosses/level2.py::_NS_khalros`` (satu sumber kebenaran untuk jalur boss,
# lane hero, dan portrait) - lihat docs/AUDIT_ULANG_DARI_AWAL.md. Modul ini
# tinggal lapisan HIDUP yang tidak mungkin di-cache: trail ayunan, partikel,
# proyektil, FX skill, impact, dan game feel. ``KhalrosRenderer`` dipertahankan
# hanya sebagai penentu state + geometri senjata (dipakai trail & debug), dan
# ``draw_character`` menjadi jembatan tipis ke rig boss.
#
#   1. STATE         - KhalrosRenderer.state_for + geometry kapak (rig boss)
#   2. ANIMATION     - AnimationController (IDLE/WALK/RUN/ATTACK/SWING/
#                      CAST/SKILL/HIT/HURT/DEATH/CHARGE/SPECIAL, dt-based)
#   3. SWING ATTACK  - ayunan kapak arc-based + window aktif + hitbox
#   4. SWING TRAIL   - pita dari sampel ujung bilah (translucent + fading)
#   5. PROJECTILE    - KhalrosProjectile (kapak / hawk / ember), lifecycle
#   6. SKILL FX      - KhalrosSkillFX (Q/W/E/R) CAST->CHARGE->RELEASE->
#                      TRAVEL/AREA->IMPACT->AFTER->FADE
#   7. PARTICLE      - Particle / ParticleSystem (reusable, berbatas)
#   8. IMPACT        - ImpactFX (flash + shock + debris + hit-stop + shake)
#   9. GAME FEEL     - ScreenShake (trauma) + hit-stop (lewat combat_feel)
#  10. DEBUG         - DEBUG_CHARACTER overlay (hitbox/hurtbox/range/state)
#
# Aturan pakai (sama dengan abaddon_fx / razak_fx):
#   * ``draw_ground_layer`` -> pre-pass  (di bawah sprite)
#   * ``draw_live_layer``   -> post-pass (di atas sprite)
#   * ``render_khalros``    -> entry all-in-one (ground + badan via rig boss
#                              + live FX); BUKAN renderer badan
#   * ``attach`` / ``owns`` -> boss memutuskan apakah efek diambil alih
#   * benturan               -> hit_stop(0.03-0.08) + shake via combat_feel
#
# 100% prosedural: tidak ada aset eksternal, tidak ada pygame.image /
# pygame.mixer di sini.
# ============================================================================

import math
import pygame

try:
    from heroes import combat_feel as _feel
except Exception:                      # pragma: no cover
    _feel = None

#: Master switch lapisan hidup KHALROS (False = jalur inline level2 fallback).
KHALROS_FX_ENABLED = True

#: Master switch overlay debug per-karakter.
DEBUG_CHARACTER = False

# ----------------------------------------------------------------------------
# DURASI SKILL (frame) - HARUS sama dengan active_skill_timer yang diisi
# AI boss (bosses/base_boss.py _khalros_*) dan durasi tebang di level2.
# ----------------------------------------------------------------------------
SKILL_DUR = {"q": 50, "w": 60, "e": 45, "r": 70}

# Progress 0..1 saat FX skill "dilepas" (release) dari pose cast.
_SKILL_RELEASE = {"q": 0.42, "w": 0.40, "e": 0.30, "r": 0.55}

# ----------------------------------------------------------------------------
# PALETTE KONSEPTUAL (kunci yang diminta prompt) - satu bahasa warna.
# ----------------------------------------------------------------------------
CHARACTER_PALETTE = {
    "outline":   (10, 7, 5),
    "shadow":    (8, 6, 10),
    "dark":      (52, 33, 18),
    "body":      (150, 96, 56),
    "mid":       (185, 122, 70),
    "light":     (220, 162, 110),
    "highlight": (248, 212, 160),
    "weapon":    (150, 146, 158),
    "fx":        (255, 150, 48),
}

# Palette detail (warna sebenarnya dipakai renderer & FX).
PALETTE = {
    # Siluet / bayangan
    "outline":      (10, 7, 5),
    "shadow_deep":  (6, 5, 9),
    "shadow":       (28, 20, 14),

    # Kulit kasar (barbar)
    "skin_darkest": (44, 24, 16),
    "skin_dark":    (96, 56, 36),
    "skin_mid":     (150, 96, 60),
    "skin_light":   (200, 146, 96),
    "skin_high":    (235, 190, 140),

    # Rambut / janggut gelap
    "hair_darkest": (16, 11, 7),
    "hair_dark":    (40, 26, 16),
    "hair_mid":     (74, 48, 28),
    "hair_high":    (120, 82, 48),

    # Kulit binatang / loincloth (cokelat)
    "leather_darkest": (25, 15, 9),
    "leather_dark":    (55, 32, 16),
    "leather_mid":     (95, 62, 32),
    "leather_light":   (150, 100, 55),
    "leather_high":    (205, 150, 90),

    # Logam kapak / gesper
    "metal_darkest": (16, 14, 18),
    "metal_dark":    (52, 48, 56),
    "metal_mid":     (105, 100, 112),
    "metal_light":   (170, 166, 178),
    "metal_shine":   (228, 224, 232),
    "metal_edge":    (250, 247, 252),

    # Emas (gesper kepala binatang)
    "gold_dark":  (120, 78, 22),
    "gold_mid":   (190, 132, 44),
    "gold_light": (230, 182, 86),
    "gold_shine": (255, 226, 150),

    # Api primal / aura (oranye-amber)
    "fire_darkest": (120, 38, 6),
    "fire_dark":    (196, 74, 10),
    "fire_mid":     (255, 138, 28),
    "fire_light":   (255, 186, 78),
    "fire_bright":  (255, 224, 138),
    "fire_hot":     (255, 248, 200),
    "fire_white":   (255, 255, 235),

    # Hawk / binatang (cokelat kebiruan)
    "hawk_darkest": (28, 22, 30),
    "hawk_dark":    (60, 48, 52),
    "hawk_mid":     (104, 86, 84),
    "hawk_light":   (160, 138, 128),
    "hawk_beak":    (210, 150, 60),

    # Debu / tanah
    "dust_dark":   (86, 66, 44),
    "dust_mid":    (138, 110, 76),
    "dust_light":  (196, 168, 128),

    # Dampak / darah
    "impact_dark": (120, 30, 16),
    "impact_mid":  (205, 60, 30),
    "impact_light":(255, 140, 70),

    "white":       (255, 255, 255),
    "ash_dark":    (70, 58, 48),
    "ash_light":   (150, 128, 110),
}


def _sync_palette():
    """Ambil ulang palette dari renderer boss bila tersedia (satu bahasa)."""
    try:
        from bosses.level2 import _NS_khalros as G
        for k, v in G.PALETTE.items():
            if k not in PALETTE:
                PALETTE[k] = v
    except Exception:                      # pragma: no cover
        pass


def _clamp(c):
    if type(c) is tuple and len(c) == 3:
        _r, _g, _b = c
        if (type(_r) is int and type(_g) is int and type(_b) is int
                and 0 <= _r <= 255 and 0 <= _g <= 255 and 0 <= _b <= 255):
            return c
    return tuple(max(0, min(255, int(v))) for v in c)


def _a(v):
    return max(0, min(255, int(v)))


def _hash01(i):
    x = math.sin(i * 127.1 + 311.7) * 43758.5453
    return x - math.floor(x)


def _lerp(a, b, t):
    return a + (b - a) * t


def _ease_in(t):
    return t * t


def _ease_out(t):
    return 1.0 - (1.0 - t) * (1.0 - t)


def _ease_in_out(t):
    return t * t * (3.0 - 2.0 * t)


def _aacircle(surf, color, pos, r):
    """Lingkaran chunky (aacircle bila ada, else fallback)."""
    x, y = pos
    c = _clamp(color)
    if len(c) == 4:
        try:
            pygame.draw.aacircle(surf, c, (int(x), int(y)), int(r))
            return
        except Exception:
            pass
        pygame.draw.circle(surf, c, (int(x), int(y)), int(r))
        return
    try:
        pygame.draw.aacircle(surf, c[:3], (int(x), int(y)), int(r))
    except Exception:
        pygame.draw.circle(surf, c[:3], (int(x), int(y)), int(r))


# ============================================================================
# PRIMITIF DRAW (chunky, tanpa temp surface per panggilan saat alpha penuh)
# ============================================================================

def _rect4(surface, color, alpha, x, y, w, h):
    a = _a(alpha)
    if a <= 0 or w <= 0 or h <= 0:
        return
    c = _clamp(color)
    if a >= 250:
        pygame.draw.rect(surface, c[:3], (int(x), int(y), int(w), int(h)))
    else:
        pygame.draw.rect(surface, (c[0], c[1], c[2], a),
                         (int(x), int(y), int(w), int(h)))


def _disc(surface, color, alpha, x, y, r):
    a = _a(alpha)
    if a <= 0 or r <= 0:
        return
    c = _clamp(color)
    if a >= 250:
        pygame.draw.circle(surface, c[:3], (int(x), int(y)), int(r))
    else:
        pygame.draw.circle(surface, (c[0], c[1], c[2], a),
                           (int(x), int(y)), int(r))


def _seg(surface, color, alpha, x0, y0, x1, y1, w=1):
    a = _a(alpha)
    if a <= 0:
        return
    c = _clamp(color)
    if a >= 250:
        pygame.draw.line(surface, c[:3], (int(x0), int(y0)),
                         (int(x1), int(y1)), max(1, int(w)))
    else:
        pygame.draw.line(surface, (c[0], c[1], c[2], a),
                         (int(x0), int(y0)), (int(x1), int(y1)),
                         max(1, int(w)))


def _poly(surface, color, pts, alpha=255):
    a = _a(alpha)
    if a <= 0 or len(pts) < 3:
        return
    c = _clamp(color)
    ip = [(int(px), int(py)) for px, py in pts]
    if a >= 250:
        pygame.draw.polygon(surface, c[:3], ip)
    else:
        pygame.draw.polygon(surface, (c[0], c[1], c[2], a), ip)


def _star(surface, cx, cy, size, color, alpha, spikes=4, rot=0.0, core=None):
    """Bintang kilat chunky (spike panjang-pendek selang-seling)."""
    if alpha <= 0 or size <= 0:
        return
    for k in range(spikes):
        ang = rot + k * math.pi * 2.0 / spikes
        ln = size * (1.0 if k % 2 == 0 else 0.5)
        _seg(surface, color, alpha, cx, cy,
             cx + math.cos(ang) * ln, cy + math.sin(ang) * ln * 0.85,
             2 if k % 2 == 0 else 1)
    if core:
        _disc(surface, core, alpha, cx, cy, max(1, int(size * 0.3)))


def _shard(surface, cx, cy, ang, length, width, color, alpha, core=None):
    """Serpihan kristal: belah ketupat runcing searah ang."""
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
        pygame.draw.polygon(surface, c[:3],
                            [(int(px), int(py)) for px, py in pts])
    else:
        pygame.draw.polygon(surface, (c[0], c[1], c[2], a),
                            [(int(px), int(py)) for px, py in pts])
    if core:
        _seg(surface, core, alpha, cx - ca * length * 0.3,
             cy - sa * length * 0.3, cx + ca * length * 0.8,
             cy + sa * length * 0.8, 1)


def _dash_ring(surface, cx, cy, radius, color, alpha, phase,
               segments=6, thick=3, squash=0.5):
    """Cincin PUTUS-PUTUS chunky (bukan lingkaran vektor halus)."""
    if alpha <= 0 or radius <= 1:
        return
    for i in range(segments):
        a0 = phase + i * math.pi * 2.0 / segments
        a1 = a0 + math.pi * 2.0 / segments * 0.62
        _seg(surface, color, alpha,
             cx + math.cos(a0) * radius, cy + math.sin(a0) * radius * squash,
             cx + math.cos(a1) * radius, cy + math.sin(a1) * radius * squash,
             thick)


def _filled_crescent(surface, cx, cy, r, ang, sweep, color, alpha):
    """Sabit chunky terisi (busur tebasan)."""
    if alpha <= 0 or r <= 1:
        return
    c = _clamp(color)
    a = _a(alpha)
    steps = max(3, int(sweep * 26))
    outer = []
    for i in range(steps + 1):
        t = i / float(steps)
        a0 = ang - sweep / 2.0 + sweep * t
        outer.append((int(cx + math.cos(a0) * r),
                      int(cy + math.sin(a0) * r)))
    inner = []
    for i in range(steps + 1):
        t = i / float(steps)
        a0 = ang - sweep / 2.0 + sweep * t
        inner.append((int(cx + math.cos(a0) * r * 0.55),
                      int(cy + math.sin(a0) * r * 0.55)))
    pts = outer + inner[::-1]
    if a >= 250:
        pygame.draw.polygon(surface, c[:3], pts)
    else:
        pygame.draw.polygon(surface, (c[0], c[1], c[2], a), pts)


# ============================================================================
# 1. PARTICLE SYSTEM (reusable, berbatas)
# ============================================================================

MAX_PARTICLES = 72


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
                _disc(surface, PALETTE["fire_white"], _a(a * 0.7),
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
                color=color or PALETTE["fire_mid"],
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
# 2. PROJECTILE (modular, lifecycle SPAWN->TRAVEL->HIT->IMPACT->DESTROY)
# ============================================================================

MAX_PROJECTILES = 7


class KhalrosProjectile(object):
    """Proyektil KHALROS di ruang LAYAR (bukan cache sprite).

    kind:
      * "axe"   - Wild Axe (Q): kapak berputar mengejar target + trail
      * "hawk"  - Hawk Storm (R): elang spiral turun + feather trail
      * "ember" - bara primal (dekorasi / skill W)
    """

    def __init__(self, kind, x, y, tx, ty, speed, life, radius, power=1.0,
                 direction=1):
        self.kind = kind
        self.x = float(x)
        self.y = float(y)
        self.tx = float(tx)
        self.ty = float(ty)
        self.speed = float(speed)
        self.life = float(life)
        self.radius = int(radius)
        self.power = float(power)
        self.direction = int(direction) or 1
        self.age = 0.0
        self.rot = 0.0
        self.active = True
        self.hit = False
        self.trail = []          # (x, y) - after-image
        self._stamp = 0
        dx, dy = tx - x, ty - y
        self.ang = math.atan2(dy, dx)

    def update(self, dt, on_hit):
        if not self.active:
            return
        step = dt * 60.0
        self.age += dt
        self.rot += step * (5.0 if self.kind == "axe" else 3.4)

        if self.kind == "axe":
            # kejar target (target tracking)
            dx, dy = self.tx - self.x, self.ty - self.y
            d = math.hypot(dx, dy)
            if d < self.speed * step + 6:
                self.x, self.y = self.tx, self.ty
                self._fire(on_hit)
                return
            self.x += dx / d * self.speed * step
            self.y += dy / d * self.speed * step
            self.ang = math.atan2(dy, dx)
        elif self.kind == "hawk":
            self.x += math.cos(self.rot * 0.6) * self.speed * step * 0.4
            # turun menjulang ke target
            dy = self.ty - self.y
            self.y += max(-1.0, min(1.0, dy / 40.0)) * self.speed * step
            if abs(dy) < 8 and self.age > self.life * 0.6:
                self._fire(on_hit)
                return
        else:  # ember - lurus
            self.x += math.cos(self.ang) * self.speed * step
            self.y += math.sin(self.ang) * self.speed * step * 0.5

        # after-image kuantisasi
        self._stamp += 1
        if self._stamp % 2 == 0:
            self.trail.append((int(self.x // 3) * 3, int(self.y // 3) * 3))
            if len(self.trail) > 9:
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

    def draw(self, surface):
        px, py = int(self.x), int(self.y)
        fade = max(0.0, 1.0 - self.age / max(0.1, self.life))
        if self.kind == "axe":
            self._draw_axe(surface, px, py, fade)
        elif self.kind == "hawk":
            self._draw_hawk(surface, px, py, fade)
        else:
            self._draw_ember(surface, px, py, fade)

    def _draw_axe(self, surface, px, py, fade):
        P = PALETTE
        # after-image
        n = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            a = _a(110 * (i + 1) / max(1, n) * fade)
            if a <= 4:
                continue
            _rect4(surface, P["fire_dark"], a, tx - 3, ty - 3, 6, 6)
            _disc(surface, P["fire_mid"], a, tx, ty, 3)
        # pegangan
        hx = px - math.cos(self.rot) * 8
        hy = py - math.sin(self.rot) * 8
        _seg(surface, P["leather_darkest"], _a(240 * fade), hx, hy, px, py, 4)
        _seg(surface, P["leather_mid"], _a(240 * fade), hx, hy, px, py, 2)
        # kepala kapak (segitiga tajam)
        ca, sa = math.cos(self.rot), math.sin(self.rot)
        nx, ny = -sa, ca
        tip = (px + ca * 12, py + sa * 12)
        back = (px - ca * 2, py - sa * 2)
        w1 = (px + nx * 9, py + ny * 9)
        w2 = (px - nx * 9, py - ny * 9)
        _poly(surface, P["metal_darkest"], [back, w1, tip, w2])
        _poly(surface, P["metal_mid"],
              [(px + ca * 2, py + sa * 2), w1, tip, w2], alpha=235)
        _poly(surface, P["metal_edge"], [tip, w1, (px + ca * 6, py + sa * 6)],
              alpha=200)
        # api primal di tepi
        _disc(surface, P["fire_mid"], _a(220 * fade), tip[0], tip[1], 3)
        _disc(surface, P["fire_hot"], _a(230 * fade), tip[0], tip[1], 1)

    def _draw_hawk(self, surface, px, py, fade):
        P = PALETTE
        d = self.direction
        # sayap
        wing = math.sin(self.rot * 1.3) * 6
        _poly(surface, P["hawk_darkest"],
              [(px, py), (px - 16 * d, py - 6 + wing), (px - 6 * d, py + 2)])
        _poly(surface, P["hawk_dark"],
              [(px, py), (px - 14 * d, py - 5 + wing), (px - 5 * d, py + 1)],
              alpha=235)
        _poly(surface, P["hawk_mid"],
              [(px, py), (px + 2 * d, py - 2), (px - 4 * d, py + 1)],
              alpha=220)
        # badan
        _disc(surface, P["hawk_dark"], _a(240 * fade), px, py, 6)
        _disc(surface, P["hawk_mid"], _a(230 * fade), px, py + 1, 4)
        # paruh + mata
        _poly(surface, P["hawk_beak"],
              [(px + 6 * d, py - 1), (px + 12 * d, py), (px + 6 * d, py + 2)])
        _disc(surface, P["fire_mid"], _a(240 * fade), px + 3 * d, py - 2, 1)
        # feather trail
        for k in range(3):
            oy = py + 4 + k * 3
            _seg(surface, P["hawk_light"], _a(160 * fade),
                 px - 6 * d, oy, px - 16 * d, oy + 3, 2)

    def _draw_ember(self, surface, px, py, fade):
        P = PALETTE
        _disc(surface, P["fire_dark"], _a(210 * fade), px, py, 4)
        _disc(surface, P["fire_mid"], _a(230 * fade), px, py, 3)
        _disc(surface, P["fire_hot"], _a(240 * fade), px, py, 1)


# ============================================================================
# 3. IMPACT FX - flash + cincin chunky + serpihan + shock + scorch
# ============================================================================

MAX_IMPACTS = 9


class ImpactFX(object):
    def __init__(self, x, y, ang, power, kind):
        self.x = float(x)
        self.y = float(y)
        self.ang = float(ang)
        self.power = float(power)
        self.kind = kind            # "blade" | "axe" | "hawk" | "roar" | "charge"
        self.age = 0.0
        self.life = 0.42 if kind != "hawk" else 0.62
        P = PALETTE
        self.c1 = P["fire_mid"] if kind in ("axe", "hawk", "roar") else \
            P["impact_mid"]
        self.c2 = P["fire_bright"] if kind in ("axe", "hawk", "roar") else \
            P["impact_light"]
        self.c3 = P["fire_white"]
        self.done = False

    def update(self, dt):
        self.age += dt
        if self.age >= self.life:
            self.done = True

    def draw(self, surface):
        t = self.age / self.life
        k = 1.0 - t
        P = PALETTE
        # flash bintang di frame awal
        if t < 0.35:
            s = int((12 + t * 24) * self.power * (1.0 - t / 0.35 * 0.4))
            _star(surface, self.x, self.y, s, self.c2,
                  _a(245 * (1 - t / 0.35)), spikes=4,
                  rot=self.ang + t * 4.0, core=P["white"])
        # cincin chunky mengembang
        r = int((9 + t * 44) * self.power)
        _dash_ring(surface, self.x, self.y, r, self.c1, _a(200 * k),
                   t * 3.0 + self.ang, segments=6,
                   thick=max(2, int(3 * self.power)), squash=0.55)
        _dash_ring(surface, self.x, self.y, int(r * 0.62), self.c2,
                   _a(150 * k), -t * 4.0, segments=4, thick=2, squash=0.55)
        # serpihan beterbangan
        for i in range(3):
            u = t * (0.55 + 0.75 * _hash01(i * 7 + 11))
            a = self.ang + (0.5 - _hash01(i * 13)) * 2.6
            d = u * 54 * self.power
            _shard(surface, self.x + math.cos(a) * d,
                   self.y + math.sin(a) * d * 0.8,
                   a + t * 5, 5 * (1 - t) + 2, 2,
                   self.c1 if i % 2 else self.c2, _a(225 * k))


class Scorch(object):
    """Jejak gosong / tanah di bawah (ground decal), memudar."""

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
        _rect4(surface, PALETTE["shadow_deep"], _a(a * 0.9),
               self.x - r // 2, self.y - r // 6, r, r // 3)
        _rect4(surface, self.color, _a(a * 0.5),
               self.x - r // 3, self.y - r // 8, r * 2 // 3, r // 4)


# ============================================================================
# 4. SWING TRAIL (pita dari SEMPEL ujung bilah di waktu lampau)
# ============================================================================

class SwingTrail(object):
    """Pita trail dari SEMPEL posisi ujung bilah (lama -> baru).

    Renderer mengisi ``samples`` tiap frame saat jendela tebas aktif.
    Modul menggambar pita 3 lapis + leading edge + speed line.
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
        P = PALETTE
        c_dark = P["fire_darkest"] if hot else P["metal_darkest"]
        c_mid = P["fire_mid"] if hot else P["metal_mid"]
        c_bright = P["fire_bright"] if hot else P["metal_light"]
        c_hot = P["fire_hot"] if hot else P["metal_shine"]
        c_core = P["fire_white"]
        n = len(path)
        for wmul, col, am in ((1.6, c_dark, 0.42), (1.0, c_mid, 0.92),
                              (0.4, c_bright, 1.0)):
            a = _a(235 * am)
            for i in range(n - 1):
                t = (i + 1) / n
                w = max(1, int(8.0 * t * t * wmul))
                _seg(surface, col, a, path[i][0], path[i][1],
                     path[i + 1][0], path[i + 1][1], w)
        # leading edge 1 px paling terang
        for i in range(n - 3, n - 1):
            _seg(surface, c_core, _a(245), path[i][0], path[i][1],
                 path[i + 1][0], path[i + 1][1], 1)
        # speed line di dalam busur
        for kk in range(2):
            i0 = 2 + kk * 3
            i1 = min(n - 1, i0 + 4)
            if i0 < i1:
                _seg(surface, c_hot, _a(170), path[i0][0], path[i0][1],
                     path[i1][0], path[i1][1], 1)


# ============================================================================
# 5. SKILL FX (KHALROS Q/W/E/R) - lifecycle lengkap
#    CAST -> CHARGE -> RELEASE -> TRAVEL/AREA -> IMPACT -> AFTER -> FADE
# ============================================================================

class KhalrosSkillFX(object):
    """Satu instans skill FX untuk KHALROS.

    kind: "q" (Wild Axes), "w" (Call of the Wild), "e" (Boar Charge),
          "r" (Hawk Storm).
    """

    def __init__(self, kind, x, y, tx, ty, direction, power=1.0):
        self.kind = kind
        self.x = float(x)
        self.y = float(y)
        self.tx = float(tx)
        self.ty = float(ty)
        self.direction = int(direction) or 1
        self.power = float(power)
        self.age = 0.0
        self.total = float(SKILL_DUR.get(kind, 50)) / 60.0
        self.release = _SKILL_RELEASE.get(kind, 0.4)
        self.impacted = False
        self.done = False
        # sub-elemen per skill
        self._spin = 0.0
        self._charge = 0.0
        self._trail = []       # untuk boar charge / hawk
        d = self.direction
        self._boar_x = x + d * 10
        self._boar_y = y

    # ------------------------------------------------------------------
    def update(self, dt, on_impact):
        self.age += dt
        self._spin += dt * 10.0
        self._charge = min(1.0, self.age / (self.total * self.release))
        t = self.age / self.total
        if t >= 1.0:
            self.done = True
        # impact sekali saat lewat release
        if not self.impacted and t >= self.release:
            self.impacted = True
            if on_impact is not None:
                on_impact(self)

    # ------------------------------------------------------------------
    def draw(self, surface, particles):
        t = self.age / self.total
        if self.kind == "q":
            self._draw_q(surface, t)
        elif self.kind == "w":
            self._draw_w(surface, t)
        elif self.kind == "e":
            self._draw_e(surface, t)
        else:
            self._draw_r(surface, t, particles)

    # ---- Q: Wild Axes (kapak melayang + tebas ke bawah + ring) --------
    def _draw_q(self, surface, t):
        P = PALETTE
        # dua kapak berputar di atas target, lalu menebas ke bawah
        for k in range(2):
            off = (k - 0.5) * 26
            spin = self._spin * (1.0 if k == 0 else -1.0) + k * 1.3
            if t < self.release:
                # melayang & berputar di atas target
                ay = self.ty - 70 + math.sin(spin) * 6
                ax = self.tx + off
                self._mini_axe(surface, ax, ay, spin, 1.0)
            else:
                # menebas ke arah target
                p = (t - self.release) / (1.0 - self.release)
                ax = self.tx + off * (1.0 - p)
                ay = self.ty - 70 + 70 * _ease_in(p)
                self._mini_axe(surface, ax, ay, spin + p * 6.0, 1.0 - p * 0.3)
        # ring tebasan saat impact
        if t >= self.release:
            rt = (t - self.release) / (1.0 - self.release)
            r = int((6 + rt * 60) * self.power)
            _dash_ring(surface, self.tx, self.ty, r, P["fire_mid"],
                       _a(200 * (1 - rt)), self._spin, segments=6,
                       thick=max(2, int(3 * self.power)), squash=0.5)
            _dash_ring(surface, self.tx, self.ty, int(r * 0.6),
                       P["fire_bright"], _a(150 * (1 - rt)), -self._spin,
                       segments=4, thick=2, squash=0.5)
            if rt < 0.4:
                _star(surface, self.tx, self.ty,
                      int((10 + rt * 30) * self.power), P["fire_bright"],
                      _a(240 * (1 - rt / 0.4)), spikes=4,
                      rot=self._spin, core=P["white"])

    def _mini_axe(self, surface, ax, ay, spin, fade):
        P = PALETTE
        hx = ax - math.cos(spin) * 7
        hy = ay - math.sin(spin) * 7
        _seg(surface, P["leather_darkest"], _a(240 * fade), hx, hy, ax, ay, 4)
        ca, sa = math.cos(spin), math.sin(spin)
        nx, ny = -sa, ca
        tip = (ax + ca * 11, ay + sa * 11)
        w1 = (ax + nx * 8, ay + ny * 8)
        w2 = (ax - nx * 8, ay - ny * 8)
        _poly(surface, P["metal_darkest"], [(ax - ca * 2, ay - sa * 2), w1,
                                            tip, w2])
        _poly(surface, P["metal_mid"], [(ax, ay), w1, tip, w2], alpha=235)
        _disc(surface, P["fire_mid"], _a(220 * fade), tip[0], tip[1], 3)
        _disc(surface, P["fire_hot"], _a(230 * fade), tip[0], tip[1], 1)

    # ---- W: Call of the Wild (roar + pack emerge + shockwave) ----------
    def _draw_w(self, surface, t):
        P = PALETTE
        # ground crack + shockwave radial
        r = int((8 + t * 130) * self.power)
        _dash_ring(surface, self.x, self.y + 6, r, P["fire_dark"],
                   _a(200 * (1 - t)), self._spin, segments=6,
                   thick=max(3, int(5 * self.power)), squash=0.4)
        _dash_ring(surface, self.x, self.y + 6, int(r * 0.7),
                   P["fire_mid"], _a(170 * (1 - t)), -self._spin,
                   segments=6, thick=3, squash=0.4)
        # pak binatang (boar/wolf) menjulang dari tanah
        for k in range(4):
            a = k * math.pi * 2.0 / 4 + 0.4
            bx = self.x + math.cos(a) * (30 + 10 * math.sin(self._spin + k))
            by = self.y + 6 + math.sin(a) * 12
            emerge = max(0.0, min(1.0, (t - self.release * 0.5) * 2.0 - k * 0.12))
            if emerge <= 0:
                continue
            hh = int(26 * emerge)
            _poly(surface, P["leather_darkest"],
                  [(bx - 9, by), (bx - 5, by - hh), (bx + 5, by - hh),
                   (bx + 9, by)])
            _poly(surface, P["leather_mid"],
                  [(bx - 7, by - 1), (bx - 4, by - hh + 4), (bx + 4, by - hh + 4),
                   (bx + 7, by - 1)], alpha=235)
            # mata menyala
            _disc(surface, P["fire_mid"], _a(230 * emerge), bx - 2, by - hh + 6, 1)
            _disc(surface, P["fire_mid"], _a(230 * emerge), bx + 2, by - hh + 6, 1)
        # roar flash di awal
        if t < 0.3:
            _star(surface, self.x, self.y - 30,
                  int((14 + t * 20) * self.power), P["fire_bright"],
                  _a(230 * (1 - t / 0.3)), spikes=10, rot=self._spin,
                  core=P["white"])

    # ---- E: Boar Charge (dust line + boar lunge + dirt burst) ----------
    def _draw_e(self, surface, t):
        P = PALETTE
        d = self.direction
        # garis debu dari start ke target
        ex = self.x + d * 70 * _ease_out(min(1.0, t / self.release))
        for i in range(10):
            f = i / 9.0
            dx = _lerp(self.x, ex, f)
            dy = self.y + 6 + math.sin(f * 8 + self._spin) * 4
            a = _a(180 * (1 - abs(f - 0.5)) * (1 - t))
            _disc(surface, P["dust_mid"], a, dx, dy, int(4 + 3 * (1 - f)))
        # boar yang meluncur
        bx = _lerp(self.x + d * 8, ex, _ease_out(min(1.0, t / self.release)))
        by = self.y + 2
        self._boar(surface, bx, by, d, 1.0)
        # ledakan tanah di ujung
        if t >= self.release:
            rt = (t - self.release) / (1.0 - self.release)
            r = int((6 + rt * 46) * self.power)
            _dash_ring(surface, ex, self.y + 6, r, P["dust_dark"],
                       _a(200 * (1 - rt)), self._spin, segments=6,
                       thick=3, squash=0.45)
            _dash_ring(surface, ex, self.y + 6, int(r * 0.6),
                       P["dust_light"], _a(160 * (1 - rt)), -self._spin,
                       segments=4, thick=2, squash=0.45)
            if rt < 0.4:
                _star(surface, ex, self.y, int((10 + rt * 26) * self.power),
                      P["fire_bright"], _a(230 * (1 - rt / 0.4)), spikes=4,
                      rot=self._spin, core=P["white"])

    def _boar(self, surface, bx, by, d, fade):
        P = PALETTE
        _poly(surface, P["leather_darkest"],
              [(bx - 12 * d, by - 6), (bx + 10 * d, by - 6),
               (bx + 14 * d, by), (bx - 12 * d, by + 2)])
        _poly(surface, P["leather_mid"],
              [(bx - 10 * d, by - 5), (bx + 8 * d, by - 5),
               (bx + 12 * d, by - 1), (bx - 9 * d, by + 1)], alpha=235)
        # kepala + taring
        _poly(surface, P["leather_dark"],
              [(bx + 10 * d, by - 7), (bx + 18 * d, by - 4),
               (bx + 12 * d, by + 1)])
        _disc(surface, P["fire_mid"], _a(220 * fade), bx + 13 * d, by - 4, 1)
        # kaki
        for k in range(2):
            _rect4(surface, P["leather_darkest"], _a(230 * fade),
                   bx - 8 * d + k * 10, by + 1, 3, 6)

    # ---- R: Hawk Storm (hawk turun + feather storm + shockwave) -------
    def _draw_r(self, surface, t, particles):
        P = PALETTE
        d = self.direction
        # langit menggelap + kilat
        if t < 0.4:
            _star(surface, self.x, self.y - 60, int(20 + t * 30),
                  P["fire_bright"], _a(180 * (1 - t / 0.4)), spikes=12,
                  rot=self._spin, core=P["white"])
        # elang turun dari atas ke titik
        hy = _lerp(self.y - 90, self.y - 20, _ease_in(min(1.0, t / self.release)))
        wing = math.sin(self._spin * 2.0) * 10
        self._hawk_big(surface, self.x, hy, d, wing, 1.0)
        # storm bulu + shockwave saat mendarat
        if t >= self.release:
            rt = (t - self.release) / (1.0 - self.release)
            r = int((10 + rt * 160) * self.power)
            _dash_ring(surface, self.x, self.y + 6, r, P["hawk_dark"],
                       _a(200 * (1 - rt)), self._spin, segments=18,
                       thick=max(3, int(6 * self.power)), squash=0.38)
            _dash_ring(surface, self.x, self.y + 6, int(r * 0.66),
                       P["fire_mid"], _a(170 * (1 - rt)), -self._spin,
                       segments=6, thick=3, squash=0.38)
            if rt < 0.5 and particles is not None:
                if len(particles.items) < MAX_PARTICLES - 6:
                    particles.burst(self.x, self.y, 3, speed=4.0, life=0.6,
                                    size=4, color=P["hawk_light"], kind="shard",
                                    g=0.3)
                    particles.burst(self.x, self.y, 4, speed=2.5, life=0.5,
                                    size=4, color=P["fire_mid"], kind="spark",
                                    add=True)

    def _hawk_big(self, surface, px, py, d, wing, fade):
        P = PALETTE
        # sayap besar
        _poly(surface, P["hawk_darkest"],
              [(px, py), (px - 34 * d, py - 10 + wing), (px - 10 * d, py + 4)])
        _poly(surface, P["hawk_dark"],
              [(px, py), (px - 30 * d, py - 8 + wing), (px - 8 * d, py + 2)],
              alpha=235)
        _poly(surface, P["hawk_mid"],
              [(px, py), (px - 14 * d, py - 4), (px - 4 * d, py + 1)],
              alpha=220)
        # tubuh + ekor
        _disc(surface, P["hawk_dark"], _a(240 * fade), px, py + 2, 9)
        _disc(surface, P["hawk_mid"], _a(230 * fade), px, py + 3, 6)
        _poly(surface, P["hawk_darkest"],
              [(px - 4 * d, py + 8), (px - 14 * d, py + 14), (px - 2 * d, py + 8)])
        # kepala + paruh + mata
        _disc(surface, P["hawk_mid"], _a(235 * fade), px + 8 * d, py - 4, 5)
        _poly(surface, P["hawk_beak"],
              [(px + 11 * d, py - 5), (px + 20 * d, py - 3), (px + 11 * d, py - 1)])
        _disc(surface, P["fire_bright"], _a(245 * fade), px + 9 * d, py - 5, 1)


# ============================================================================
# 6. RENDERER BADAN (layered, silhouette kuat, prodedural)
# ============================================================================

# Pose anchor: kaki di (x, y). Tubuh menjulang ke atas.
FEET_DY = 0
SHOULDER_DX = 9
SHOULDER_DY = 50          # bahu di y - 50
HEAD_DY = 84              # kepala di y - 84 (pusat)
WEAPON_LEN = 46          # panjang kapak (grip -> ujung)


class KhalrosRenderer(object):
    """Renderer prosedural KHALROS - layered, animation controller."""

    def __init__(self):
        self.pose_cache = {}

    # ------------------------------------------------------------------
    # Tentukan anim state dari atribut boss.
    def state_for(self, boss):
        if not getattr(boss, "alive", True):
            return "DEATH"
        if getattr(boss, "hurt_flash_timer", 0) and \
                int(getattr(boss, "hurt_flash_timer", 0)) > 0:
            return "HURT"
        skill = getattr(boss, "active_skill", None)
        if skill == "e":
            return "CHARGE"
        if skill == "r":
            return "SPECIAL"
        if skill in ("q", "w"):
            return "SKILL"
        if getattr(boss, "_khal_attack_active", False) or \
                int(getattr(boss, "timer", 0)) > \
                int(getattr(boss, "attack_cooldown", 45)) - 15:
            return "ATTACK"
        moving = bool(getattr(boss, "_khal_moving", False))
        if moving:
            spd = float(getattr(boss, "speed", 1.0) or 1.0)
            return "RUN" if spd >= 1.4 else "WALK"
        return "IDLE"

    # ------------------------------------------------------------------
    # Geometri kapak dalam ruang LAYAR. V2: angka diambil dari rig boss
    # (`_NS_khalros._axe_grip_screen` / `_axe_tip_screen`) supaya trail,
    # hitbox, dan bilah yang digambar tidak pernah berbeda satu piksel pun
    # dengan kapak di sprite. ``SHOULDER_DX``/``WEAPON_LEN`` di bawah ini
    # tetap ada sebagai fallback kalau rig belum bisa diimpor.
    def _rig(self):
        try:
            from bosses.level2 import _NS_khalros as G
            return G
        except Exception:                 # pragma: no cover
            return None

    def weapon_grip(self, x, y, facing, boss=None):
        G = self._rig()
        if G is not None and boss is not None:
            try:
                return G._axe_grip_screen(boss, x, y)
            except Exception:             # pragma: no cover
                pass
        return (x + facing * SHOULDER_DX, y - 20)

    def weapon_angle(self, boss, facing):
        """Sudut kapak (radian, ruang layar) dari keyframe rig."""
        G = self._rig()
        state = self.state_for(boss)
        prog = float(getattr(boss, "_khal_attack_progress", 0.0))
        if G is not None and state in ("ATTACK", "CHARGE", "SKILL",
                                       "SPECIAL", "IDLE", "WALK", "RUN"):
            try:
                act = {"ATTACK": "attack", "CHARGE": "charge",
                       "SKILL": "cast", "SPECIAL": "cast",
                       "RUN": "walk", "WALK": "walk"}.get(state, "idle")
                pose = G._attack_pose(prog) if act == "attack" else None
                if pose is not None:
                    return pose["arm_a"] + 0.72
                return -1.25 + math.sin(float(getattr(boss, "pulse", 0.0))
                                         * 0.7) * 0.06
            except Exception:             # pragma: no cover
                pass
        if state == "ATTACK":
            if prog < 0.25:
                return _lerp(-1.7, -2.4, _ease_in(prog / 0.25))
            if prog < 0.6:
                return _lerp(-2.4, 0.7, _ease_in_out((prog - 0.25) / 0.35))
            return _lerp(0.7, -0.4, _ease_out((prog - 0.6) / 0.4))
        if state in ("SKILL", "SPECIAL", "CHARGE"):
            return -1.9 + math.sin(getattr(boss, "pulse", 0.0)) * 0.05
        return -0.5 + math.sin(getattr(boss, "pulse", 0.0) * 0.7) * 0.06

    def swing_tip(self, boss, x, y):
        """[dipanggil director] grip + ujung bilah + window aktif.

        Dua sumber kebenaran itu bahaya: trail bisa muncul beberapa piksel
        dari bilah yang kelihatan. Karena itu angka diambil dari rig, dan
        ``WEAPON_LEN`` lama hanya dipakai bila rig tidak tersedia.
        """
        facing = int(getattr(boss, "direction", 1)) or 1
        active = bool(getattr(boss, "_khal_attack_active", False))
        prog = float(getattr(boss, "_khal_attack_progress", 0.0))
        G = self._rig()
        if G is not None:
            try:
                gx, gy = G._axe_grip_screen(boss, x, y)
                tx, ty = G._axe_tip_screen(boss, x, y)
                ang = math.atan2(ty - gy, (tx - gx) * (1.0 if facing >= 0
                                                        else -1.0))
                if not active:
                    return {"active": False, "tip_x": tx, "tip_y": ty,
                            "grip_x": gx, "grip_y": gy, "ang": ang,
                            "trailing": False, "swing_id": None,
                            "impact_frame": G.ATTACK_IMPACT}
                trailing = 0.2 <= prog <= 0.85
                sid = int(getattr(boss, "_khal_attack_frame", 0) // 4)
                return {"active": True, "tip_x": tx, "tip_y": ty,
                        "grip_x": gx, "grip_y": gy, "ang": ang,
                        "trailing": trailing, "swing_id": sid,
                        "impact_frame": G.ATTACK_IMPACT, "ap": prog}
            except Exception:             # pragma: no cover
                pass
        gx, gy = self.weapon_grip(x, y, facing, boss)
        ang = self.weapon_angle(boss, facing)
        tip_x = gx + math.cos(ang) * WEAPON_LEN * facing
        tip_y = gy + math.sin(ang) * WEAPON_LEN
        if not active:
            return {"active": False, "tip_x": tip_x, "tip_y": tip_y,
                    "grip_x": gx, "grip_y": gy, "ang": ang,
                    "trailing": False, "swing_id": None, "impact_frame": 0.5}
        trailing = 0.2 <= prog <= 0.85
        sid = int(getattr(boss, "_khal_attack_frame", 0) // 4)
        return {"active": True, "tip_x": tip_x, "tip_y": tip_y,
                "grip_x": gx, "grip_y": gy, "ang": ang,
                "trailing": trailing, "swing_id": sid, "impact_frame": 0.5,
                "ap": prog}

    # ------------------------------------------------------------------
    # Draw badan lengkap (layered).
    # ------------------------------------------------------------------
    # V2: TIDAK ADA RIG BADAN DI SINI.
    #
    # Dulu kelas ini menggambar kepala/badan/lengan sendiri (kotak-kotak
    # kasar) dan hasilnya menimpa renderer boss. Sekarang satu-satunya
    # sumber bentuk adalah `_NS_khalros` di bosses/level2.py; `draw` &
    # `draw_body` tinggal jembatan supaya pemanggil lama (director,
    # demo __main__, jalur portrait/cache) tetap dapat sprite yang SAMA.
    def draw(self, surface, boss, x, y, fx=None, progress=0.0):
        self.draw_body(surface, boss, x, y)

    def draw_body(self, surface, boss, x, y):
        """Delegasi ke renderer boss; diam kalau modul boss tak tersedia.

        Tidak ada fallback ke "rig lama" - kalau rig boss gagal dimuat,
        lebih baik tidak menggambar apa pun daripada menampilkan dua
        Khalros dengan bahasa visual berbeda.
        """
        try:
            from bosses.level2 import _NS_khalros as G
        except Exception:                 # pragma: no cover
            return
        boss = boss or getattr(self, "hero", None)
        if boss is None:
            return
        try:
            action, _phase, _ap = G._resolve_pose(
                boss, bool(getattr(boss, "_khal_moving", False)))
        except Exception:                 # pragma: no cover
            action = "idle"
        rage = getattr(boss, "active_skill", None) in ("w", "r")
        hunting = getattr(boss, "active_skill", None) in ("q", "e")
        timer = int(getattr(boss, "active_skill_timer", 0) or 0)
        try:
            if action == "charge":
                G._draw_khalros_charge(surface, boss, x, y, timer, rage)
            elif action == "cast":
                G._draw_khalros_cast(surface, boss, x, y,
                                     getattr(boss, "active_skill", None),
                                     timer, rage)
            elif action == "attack":
                G._draw_khalros_attack(surface, boss, x, y, rage, hunting)
            elif action == "walk":
                G._draw_khalros_walk(surface, boss, x, y, rage, hunting)
            else:
                G._draw_khalros_idle(surface, boss, x, y, rage, hunting)
        except Exception:                 # pragma: no cover
            pass



def _ellipse_shadow(surface, x, y, rx, ry):
    P = PALETTE
    _disc(surface, P["shadow_deep"], 150, x, y, rx)
    pygame.draw.ellipse(surface, (8, 6, 10, 150),
                        (int(x - rx), int(y - ry), int(rx * 2), int(ry * 2)))


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


# layar shake lokal (dipakai demo mandiri bila combat_feel tak ada)
class _LocalShake:
    def __init__(self):
        self.shake_strength = 0.0
        self.shake_duration = 0.0

    def add(self, strength, duration=0.22):
        if strength <= self.shake_strength and \
                duration <= self.shake_duration:
            return
        self.shake_strength = max(self.shake_strength, float(strength))
        self.shake_duration = max(self.shake_duration, float(duration))

    def update(self, dt):
        if self.shake_duration > 0:
            self.shake_duration -= dt
            self.shake_strength *= 0.86
            if self.shake_duration <= 0:
                self.shake_strength = 0.0

    def offset(self):
        if self.shake_strength <= 0:
            return 0, 0
        a = self.shake_strength
        return int(math.sin(self.shake_duration * 90.0) * a), \
            int(math.cos(self.shake_duration * 73.0) * a)


_LOCAL_SHAKE = _LocalShake()


def hit_stop(seconds=0.045):
    _feel_hit_stop(seconds)


def shake(strength=5.0, duration=0.22):
    _feel_shake(strength, duration)
    _LOCAL_SHAKE.add(strength, duration)


# ============================================================================
# 8. DIRECTOR - state per unit (dipatok di objek boss/hero)
# ============================================================================

_DIRECTORS = []
_last_tick_ms = None

# Anim state constants (dipakai debug + tools).
ANIM_STATES = ("IDLE", "WALK", "RUN", "ATTACK", "SWING", "CAST", "SKILL",
               "HIT", "HURT", "DEATH", "CHARGE", "SPECIAL")


class KhalrosFXDirector(object):
    def __init__(self, hero):
        self.hero = hero
        self.particles = ParticleSystem()
        self.projectiles = []
        self.impacts = []
        self.scorch = []
        self.skills = []
        self.trail = SwingTrail()
        self.renderer = KhalrosRenderer()
        self.last_x = float(getattr(hero, "x", 0.0))
        self.last_y = float(getattr(hero, "y", 0.0))
        self._prev_skill = None
        self._prev_timer = None
        self._frame = 0
        self._swing_id = None
        self._swing_impact_done = False
        self.anim_state = "IDLE"
        self.attack_timer = 0.0

    # ------------------------------------------------------------------
    def _target_pos(self):
        t = getattr(self.hero, "target", None)
        hx = float(getattr(self.hero, "x", 0.0))
        hy = float(getattr(self.hero, "y", 0.0))
        if t is not None and getattr(t, "alive", True):
            return float(t.x), float(t.y)
        d = int(getattr(self.hero, "direction", 1)) or 1
        return hx + 150.0 * d, hy

    # ------------------------------------------------------------------
    def update(self, dt, hx, hy):
        self.last_x = hx
        self.last_y = hy
        self._frame += 1
        self.anim_state = self.renderer.state_for(self.hero)
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
        for sk in self.skills:
            sk.update(dt, self._on_skill_impact)
        self.skills = [sk for sk in self.skills if not sk.done]

        skill = getattr(self.hero, "active_skill", None)
        timer = int(getattr(self.hero, "active_skill_timer", 0) or 0)
        if skill and skill != self._prev_skill:
            self.on_cast(hx, hy, skill, timer)
        self._prev_skill = skill
        self._prev_timer = timer

        # partikel ambient: bara primal naik (murah, dibatasi)
        if (dt > 0 and self._frame % 4 == 0
                and len(self.particles.items) < 40):
            d = int(getattr(self.hero, "direction", 1)) or 1
            fx0 = _hash01(self._frame * 0.61 + 2)
            self.particles.spawn(
                x=hx + (d * 12 - 6) + (fx0 - 0.5) * 26,
                y=hy + 30,
                vx=(fx0 - 0.5) * 0.4,
                vy=-0.6 - fx0 * 0.8,
                life=0.5, size=3, color=PALETTE["fire_mid"],
                kind="square", g=-0.3, add=True)

        # swing trail + impact basic attack
        self._sync_swing(dt)

        # batas saja: tidak ada partikel/proyektil hidup tanpa batas
        if len(self.particles.items) > MAX_PARTICLES:
            del self.particles.items[:len(self.particles.items) - MAX_PARTICLES]
        if len(self.impacts) > MAX_IMPACTS:
            del self.impacts[:len(self.impacts) - MAX_IMPACTS]
        if len(self.scorch) > 8:
            del self.scorch[:len(self.scorch) - 8]
        if len(self.projectiles) > MAX_PROJECTILES:
            del self.projectiles[:len(self.projectiles) - MAX_PROJECTILES]
        if len(self.skills) > 6:
            del self.skills[:len(self.skills) - 6]

    # ------------------------------------------------------------------
    def _sync_swing(self, dt):
        # lunge ikut pose serangan supaya trail sejajar dengan kapak gambar
        prog = float(getattr(self.hero, "_khal_attack_progress", 0.0))
        facing = int(getattr(self.hero, "direction", 1)) or 1
        lunge = int(math.sin(prog * math.pi) * 5) * facing
        st = self.renderer.swing_tip(self.hero, self.last_x + lunge,
                                     self.last_y)
        trail = self.trail
        if not st.get("active", False):
            trail.clear()
            self._swing_id = None
            self._swing_impact_done = False
            return
        if st.get("trailing"):
            trail.samples.append((int(st["tip_x"]), int(st["tip_y"])))
            if len(trail.samples) > 16:
                trail.samples.pop(0)
            trail.visible = True
        else:
            trail.clear()
        sid = st.get("swing_id")
        if sid is not None and self._swing_id != sid:
            self._swing_id = sid
            self._swing_impact_done = False
        if not self._swing_impact_done and st.get("ap", 0) >= \
                st.get("impact_frame", 0.5):
            self._swing_impact_done = True
            ang = math.atan2(st["tip_y"] - self.last_y,
                             st["tip_x"] - self.last_x)
            self.on_swing_impact(st["tip_x"], st["tip_y"], ang, power=1.1)

    # ------------------------------------------------------------------
    def _on_projectile_hit(self, pr):
        tx, ty = pr.x, pr.y
        kind = pr.kind
        self.impacts.append(ImpactFX(tx, ty, pr.ang, pr.power,
                                     "axe" if kind == "axe" else "hawk"))
        self.scorch.append(Scorch(tx, ty + 14, 22,
                                  PALETTE["fire_mid"] if kind == "axe"
                                  else PALETTE["hawk_mid"]))
        self.particles.burst(tx, ty, 4, speed=3.0, life=0.5, size=4,
                             color=PALETTE["fire_mid"] if kind == "axe"
                             else PALETTE["hawk_mid"], kind="shard", g=0.5)
        self.particles.burst(tx, ty, 3, speed=2.0, life=0.45, size=3,
                             color=PALETTE["fire_bright"], kind="spark",
                             g=0.2, add=True)
        if kind == "hawk":
            _feel_hit_stop(0.036)
            _feel_shake(4.5, 0.4)
        else:
            _feel_hit_stop(0.022)
            _feel_shake(2.2, 0.18)

    def _on_skill_impact(self, sk):
        x, y = sk.x, sk.y
        if sk.kind == "q":
            x, y = sk.tx, sk.ty
        kind = {"q": "axe", "w": "roar", "e": "charge", "r": "hawk"}[sk.kind]
        self.impacts.append(ImpactFX(x, y, 0.0, sk.power, kind))
        self.scorch.append(Scorch(x, y + 14, 26, PALETTE["fire_dark"]))
        self.particles.burst(x, y, 5, speed=3.4, life=0.55, size=4,
                             color=PALETTE["fire_mid"], kind="shard", g=0.5)
        self.particles.burst(x, y, 3, speed=2.4, life=0.45, size=3,
                             color=PALETTE["fire_bright"], kind="spark",
                             g=0.2, add=True)
        if sk.kind == "r":
            _feel_hit_stop(0.040)
            _feel_shake(7.0, 0.5)
        elif sk.kind == "e":
            _feel_hit_stop(0.027)
            _feel_shake(4.5, 0.32)
        elif sk.kind == "w":
            _feel_hit_stop(0.024)
            _feel_shake(4.0, 0.3)
        else:
            _feel_hit_stop(0.024)
            _feel_shake(3.0, 0.24)

    # ------------------------------------------------------------------
    def on_cast(self, hx, hy, skill, timer):
        if skill not in SKILL_DUR:
            return
        tx, ty = self._target_pos()
        d = int(getattr(self.hero, "direction", 1)) or 1
        self.skills.append(KhalrosSkillFX(skill, hx, hy, tx, ty, d, 1.0))
        # kilat cast
        self.particles.burst(hx, hy - 18, 2, speed=2.2, life=0.4,
                             size=3, color=PALETTE["fire_light"],
                             kind="spark", g=-0.1, add=True)

    def on_swing_impact(self, x, y, ang, power=1.0, hot=False):
        self.impacts.append(ImpactFX(x, y, ang, power, "blade"))
        self.particles.burst(x, y, 3, speed=2.8, life=0.45, size=4,
                             color=PALETTE["fire_mid"], kind="shard", g=0.6)
        self.particles.burst(x, y, 4, speed=1.8, life=0.5, size=5,
                             color=PALETTE["ash_dark"], kind="puff", g=-0.3)
        _feel_hit_stop(0.035 + 0.012 * min(1.5, power))
        _feel_shake(4.0 + 2.6 * power, 0.2)

    def on_impact(self, x, y, ang, power=1.0, crit=False, kind="blade"):
        self.impacts.append(ImpactFX(x, y, ang, power * (1.25 if crit
                                                         else 1.0), kind))
        self.particles.burst(x, y, 8 if crit else 6,
                             speed=3.0 if crit else 2.4, life=0.5,
                             size=4, color=PALETTE["fire_mid"], kind="shard",
                             g=0.5)
        self.particles.burst(x, y, 4, speed=2.0, life=0.4, size=3,
                             color=PALETTE["fire_bright"], kind="spark",
                             g=0.2, add=True)
        _feel_hit_stop(0.036 + 0.018 * min(1.5, power) +
                       (0.014 if crit else 0.0))
        _feel_shake(4.0 + 3.2 * power + (3.0 if crit else 0.0), 0.22)

    # ------------------------------------------------------------------
    def draw_ground(self, surface):
        for sc in self.scorch:
            sc.draw(surface)

    def draw_front(self, surface, x=None, y=None):
        self.trail.draw(surface,
                        hot=getattr(self.hero, "active_skill", None) == "r")
        for pr in self.projectiles:
            if pr.age >= 0:
                pr.draw(surface)
        self.particles.draw(surface)
        for sk in self.skills:
            sk.draw(surface, self.particles)
        for im in self.impacts:
            im.draw(surface)

    def draw_character(self, surface, x, y):
        prog = float(getattr(self.hero, "_khal_attack_progress", 0.0))
        self.renderer.draw(surface, self.hero, x, y, self, prog)

    def draw_debug(self, surface, x, y):
        if not DEBUG_CHARACTER:
            return
        hx = x
        hy = y
        # hitbox (badan)
        _rect4(surface, (255, 60, 60), 200, hx - 20, hy - 100, 40, 100)
        # hurtbox (lingkaran radius)
        r = int(getattr(self.hero, "radius", 36))
        pygame.draw.circle(surface, (60, 200, 255), (int(hx), int(hy - 30)),
                           r, 1)
        # attack range
        d = int(getattr(self.hero, "direction", 1)) or 1
        ar = int(getattr(self.hero, "range", 70))
        _seg(surface, (255, 230, 60), 200, hx, hy - 30, hx + d * ar, hy - 30, 1)
        # state + frame + particle count
        try:
            import pygame as _pg
            font = _pg.font.SysFont("monospace", 12)
            txt = "%s f%d P%d" % (self.anim_state, self._frame,
                                  self.particles.count())
            surf = font.render(txt, True, (255, 255, 255))
            surface.blit(surf, (int(hx - 30), int(hy - 130)))
        except Exception:
            pass


# ============================================================================
# 9. API MODUL - registry, tick, hook render & gameplay
# ============================================================================

def director_for(hero):
    _sync_palette()
    d = getattr(hero, "_khal_fx", None)
    if d is None:
        d = KhalrosFXDirector(hero)
        try:
            hero._khal_fx = d
        except Exception:                      # pragma: no cover
            return d
        _DIRECTORS.append(d)
        if len(_DIRECTORS) > 12:
            old = _DIRECTORS.pop(0)
            _release(old)
    return d


def _release(director):
    try:
        if director.hero is not None:
            director.hero._khal_fx = None
            director.hero._khal_live_fx = False
    except Exception:                          # pragma: no cover
        pass
    director.particles.clear()
    director.projectiles = []
    director.impacts = []
    director.scorch = []
    director.skills = []
    director.trail.clear()


def attach(hero):
    if not KHALROS_FX_ENABLED or hero is None:
        return False
    try:
        director_for(hero)
    except Exception:                          # pragma: no cover
        return False
    try:
        hero._khal_live_fx = True
    except Exception:                          # pragma: no cover
        return False
    return True


def owns(hero):
    if not getattr(hero, "_khal_live_fx", False):
        return False
    d = getattr(hero, "_khal_fx", None)
    return d is not None and d in _DIRECTORS


def tick(dt=None):
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
            step = max(1.0 / 240.0, min(1.0 / 20.0, ms / 1000.0)) \
                if ms > 0 else 0.0
    if step <= 0.0:
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
    for d in list(_DIRECTORS):
        _release(d)
    _DIRECTORS.clear()


def total_particles():
    return sum(d.particles.count() for d in _DIRECTORS)


def projectiles_for(hero):
    d = getattr(hero, "_khal_fx", None)
    if d is None:
        return []
    return list(d.projectiles)


def stats():
    st = {"particles": 0, "projectiles": 0, "impacts": 0, "skills": 0}
    for d in _DIRECTORS:
        st["particles"] += d.particles.count()
        st["projectiles"] += len(d.projectiles)
        st["impacts"] += len(d.impacts)
        st["skills"] += len(d.skills)
    return st


# ----------------------------------------------------------------------------
# 10. RENDER ENTRY (all-in-one) - dipakai bosses/level2.draw_khalros
# ----------------------------------------------------------------------------

def render_khalros(surface, boss, x, y):
    """Render KHALROS utuh (ground + badan + FX) di ruang layar 1:1.

    Return True bila modul mengambil alih (jalur boss / live).
    Return False bila sebaiknya pakai renderer inline level2 (portrait
    / cache / modul dimatikan).
    """
    if not KHALROS_FX_ENABLED:
        return False

    portrait = bool(getattr(boss, "_portrait_hd", False))
    cached = bool(getattr(boss, "_skip_renderer_projectiles", False))

    if not attach(boss):
        return False
    d = getattr(boss, "_khal_fx", None)
    if d is None:
        return False

    # portrait / cache -> gambar badan STATIS saja (tanpa tick FX agar
    # sprite cache tidak "beku" pada pose beranimasi).
    if portrait or cached:
        d.draw_character(surface, x, y)
        return True

    tick()

    # update proyektil gameplay milik boss (damage tetap jalan)
    projs = getattr(boss, "_khal_projectiles", None)
    if projs is not None:
        for pr in projs:
            try:
                pr.update()
                pr.draw(surface, getattr(boss, "pulse", 0.0))
            except Exception:
                pass

    # ground accents + badan + FX
    d.draw_ground(surface)
    d.draw_character(surface, x, y)
    d.draw_front(surface, x, y)
    if DEBUG_CHARACTER:
        d.draw_debug(surface, x, y)
    return True


def draw_ground_layer(surface, hero, x, y):
    """Pre-pass: di bawah sprite (scorch, dust)."""
    if not KHALROS_FX_ENABLED:
        return
    if not attach(hero):
        return
    tick()
    d = getattr(hero, "_khal_fx", None)
    if d is not None:
        d.draw_ground(surface)


def draw_live_layer(surface, hero, x, y):
    """Post-pass: di atas sprite (trail, projectile, FX, impact)."""
    if not KHALROS_FX_ENABLED:
        return
    d = director_for(hero)
    if d is not None:
        d.draw_front(surface, x, y)
        if DEBUG_CHARACTER:
            d.draw_debug(surface, x, y)


# ----------------------------------------------------------------------------
# 11. HOOK GAMEPLAY (dipanggil bosses/base_boss.py / _entity.py)
# ----------------------------------------------------------------------------

def notify_melee_impact(hero, target, damage=0, crit=False):
    if not KHALROS_FX_ENABLED or hero is None or target is None:
        return
    try:
        power = 0.75 + min(1.5, float(damage) / 70.0)
    except (TypeError, ValueError):
        power = 1.0
    tx = float(getattr(target, "x", getattr(hero, "x", 0.0)))
    ty = float(getattr(target, "y", getattr(hero, "y", 0.0))) - 6.0
    ang = math.atan2(ty - float(getattr(hero, "y", 0.0)),
                     tx - float(getattr(hero, "x", 0.0)))
    director_for(hero).on_impact(tx, ty, ang, power, bool(crit), kind="blade")


def notify_skill_cast(hero, skill):
    if not KHALROS_FX_ENABLED or hero is None or skill not in SKILL_DUR:
        return
    d = director_for(hero)
    d.on_cast(float(getattr(hero, "x", 0.0)),
              float(getattr(hero, "y", 0.0)), skill,
              int(getattr(hero, "active_skill_timer", 0) or 0))


def notify_projectile_impact(hero, x, y, angle=0.0, damage=0, crit=False,
                             kind="axe"):
    if not KHALROS_FX_ENABLED or hero is None:
        return
    try:
        power = 0.7 + min(1.6, float(damage) / 45.0)
    except (TypeError, ValueError):
        power = 1.0
    director_for(hero).on_impact(x, y, angle, power, bool(crit), kind=kind)


# ============================================================================
# 12. DEMO MANDIRI (pygame) - untuk pengujian tanpa game utuh
# ============================================================================

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    pygame.init()
    W, H = 720, 520
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("KHALROS - Procedural FX Demo")
    clock = pygame.time.Clock()
    print("[khalros_fx] demo mulai - SPACE attack, 1/2/3/4 skills, "
          "M move, D debug, klik=aim")
    font = pygame.font.SysFont("monospace", 14)

    class FakeBoss:
        def __init__(self):
            self.x = W // 2
            self.y = H // 2 + 40
            self.direction = 1
            self.pulse = 0.0
            self.active_skill = None
            self.active_skill_timer = 0
            self.timer = 0
            self.attack_cooldown = 42
            self.speed = 1.0
            self.range = 70
            self.radius = 36
            self.target = None
            self.alive = True
            self.hurt_flash_timer = 0
            self._khal_attack_active = False
            self._khal_attack_progress = 0.0
            self._khal_attack_frame = 0
            self._khal_prev_timer = 0
            self._khal_last_x = self.x
            self._khal_last_y = self.y
            self._khal_moving = False
            self._khal_projectiles = []
            self._khal_fx = None
            self._khal_live_fx = False

    boss = FakeBoss()
    DEBUG_CHARACTER = True
    attack_cd = 0
    moving = False

    def do_attack():
        boss._khal_attack_active = True
        boss._khal_attack_frame = 0
        boss._khal_attack_progress = 0.0

    def do_skill(k):
        boss.active_skill = k
        boss.active_skill_timer = SKILL_DUR[k]
        notify_skill_cast(boss, k)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    do_attack()
                elif ev.key == pygame.K_1:
                    do_skill("q")
                elif ev.key == pygame.K_2:
                    do_skill("w")
                elif ev.key == pygame.K_3:
                    do_skill("e")
                elif ev.key == pygame.K_4:
                    do_skill("r")
                elif ev.key == pygame.K_d:
                    DEBUG_CHARACTER = not DEBUG_CHARACTER
                elif ev.key == pygame.K_m:
                    moving = not moving
                elif ev.key == pygame.K_LEFT:
                    boss.direction = -1
                elif ev.key == pygame.K_RIGHT:
                    boss.direction = 1

        # mouse = target aim
        mx, my = pygame.mouse.get_pos()
        boss.target = type("T", (), {"x": mx, "y": my, "alive": True})()

        boss.pulse += dt * 3.0

        # update attack progress
        if boss._khal_attack_active:
            attack_cd += 1
            boss._khal_attack_frame += 1
            cooldown = max(2, int(boss.attack_cooldown))
            boss._khal_attack_progress = min(
                1.0, boss._khal_attack_frame / max(1, cooldown - 1))
            if boss._khal_attack_frame > cooldown:
                boss._khal_attack_active = False
                boss._khal_attack_frame = 0
                boss._khal_attack_progress = 0.0

        # skill timer decay
        if boss.active_skill_timer > 0:
            boss.active_skill_timer -= 1
            if boss.active_skill_timer <= 0:
                boss.active_skill = None

        # movement simulation
        if moving:
            boss.x += boss.direction * 1.5
            if boss.x > W - 60:
                boss.direction = -1
            if boss.x < 60:
                boss.direction = 1
            boss._khal_moving = True
        else:
            boss._khal_moving = False

        # update gameplay projectiles (demo spawns saat skill q/r)
        for pr in boss._khal_projectiles:
            pr.update()
            pr.draw(screen, boss.pulse)
        boss._khal_projectiles = [p for p in boss._khal_projectiles
                                  if p.alive or p.age < 5]

        # ---- draw ----
        screen.fill((18, 16, 26))
        # lantai
        pygame.draw.rect(screen, (30, 26, 38), (0, H // 2 + 70, W, H))
        _LOCAL_SHAKE.update(dt)
        ox, oy = _LOCAL_SHAKE.offset()
        sub = pygame.Surface((W, H), pygame.SRCALPHA)
        render_khalros(sub, boss, boss.x, boss.y)
        screen.blit(sub, (ox, oy))

        # HUD
        fps = clock.get_fps()
        lines = [
            "KHALROS - procedural FX  (SPACE attack, 1/2/3/4 skills, "
            "M move, D debug)",
            "FPS %.0f   particles %d   projectiles %d   impacts %d   skills %d"
            % (fps, total_particles(), len(projectiles_for(boss)),
               stats()["impacts"], stats()["skills"]),
            "state %s   skill %s" % (director_for(boss).anim_state,
                                     boss.active_skill),
        ]
        for i, ln in enumerate(lines):
            screen.blit(font.render(ln, True, (230, 220, 200)),
                        (10, 10 + i * 18))
        pygame.display.flip()

    print("[khalros_fx] demo selesai bersih")
    pygame.quit()
