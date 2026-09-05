"""
bosses/level3.py - Semua boss Level 3

Gabungan dari 4 file terpisah:
  - varkul               (mini boss)
  - xerathis             (mini boss)
  - nyzrak               (mini boss)
  - ancient_apparition   (TRUE BOSS)

Tiap boss dibungkus dalam kelas namespace `_NS_<nama>`
supaya PALETTE dan fungsi helper-nya TIDAK saling
menimpa - 91 simbol bentrok antar file boss, termasuk
PALETTE, _aacircle, _draw_shadow, _target_position.

Kode di dalam tiap namespace TIDAK diubah isinya;
hanya referensi antar-simbol yang diberi prefix.

Entry point publik ada di bagian paling bawah file.
"""

import math
import pygame

try:                     # pass cahaya bersama; opsional supaya file boss
    import lighting as _lighting          # tetap bisa di-load sendiri
except Exception:        # pragma: no cover
    _lighting = None

# Penanda: file ini berisi BANYAK boss (1 true + 3 mini).
# Dipakai heroes/__init__.py agar tidak menebak fungsi draw_*
# secara longgar, yang bisa mengembalikan boss yang salah.
_IS_LEVEL_BUNDLE = True


def _composite_boss_body(surface, ns, raw, cx, cy, facing, phase, action,
                         attack_progress=0, rim_add=(30, 26, 44), bsize=180):
    """Komposit ORIGINAL-MAX untuk boss level3.

    Badan dirender ke buffer tetap, di-crop rapat, diberi outline siluet
    gelap 1 px (4 arah) lalu pass pencahayaan rim/shade dari lighting.py.
    Anchor (cx, cy) tetap jatuh di titik yang sama dengan sebelumnya, jadi
    pose & posisi dunia tidak berubah.
    """
    if getattr(ns, "_body_buf", None) is None:
        ns._body_buf = pygame.Surface((bsize, bsize), pygame.SRCALPHA)
    buf = ns._body_buf
    buf.fill((0, 0, 0, 0))
    raw(buf, bsize // 2, bsize // 2, facing, phase, action, attack_progress)
    used = buf.get_bounding_rect(min_alpha=1)
    if used.width <= 2 or used.height <= 2:
        return
    used.inflate_ip(4, 4)
    used.clamp_ip(buf.get_rect())
    sub = buf.subsurface(used).copy()
    ox = int(cx) - (bsize // 2) + used.left
    oy = int(cy) - (bsize // 2) + used.top
    edge = sub.copy()
    edge.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
    for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        surface.blit(edge, (ox + ddx, oy + ddy))
    if _lighting is not None:
        # Boss sprite level3 sudah punya gradasi nilai di-author yang cukup;
        # matikan gradien global agar idle tetap < 2.2 ms (rim + terminator
        # 1px tetap terlihat, arah cahaya dari lighting.py).
        _lighting.apply_to_rig(sub, rim_add=rim_add, shade_mul=168,
                               gradient=False, two_band=False)
    surface.blit(sub, (ox, oy))


# ====================================================================
# VARKUL
# ====================================================================
class _NS_varkul:
    """Namespace varkul - isi asli tidak diubah."""

    # ── ORIGINAL-MAX cache (piksel-identik, dibangun lazy) ──────────
    # Buffer badan untuk outline+lighting, buffer hurt flash, dan catatan
    # rect shadow supaya flash tidak ikut menyalakan bayangan tanah.
    _body_buf = None
    _flash_buf = None
    _record_shadow = None
    _shadow_cache = None
    _aura_cache = None
    _ground_cache = None
    _mist_cache = None

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Lich inspired frost blue / undead purple
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin / bone (undead pale blue)
        "skin_darkest":   (30,  45,  70),
        "skin_dark":      (60,  85, 115),
        "skin_mid":       (110, 145, 175),
        "skin_light":     (165, 200, 225),
        "skin_high":      (210, 235, 250),

        # Bone / skull
        "bone_dark":      (85, 100, 120),
        "bone_mid":       (155, 175, 195),
        "bone_light":     (215, 230, 240),
        "bone_shine":     (245, 250, 255),

        # Robe – dark purple
        "robe_darkest":   (18,  12,  35),
        "robe_dark":      (38,  25,  68),
        "robe_mid":       (68,  45, 115),
        "robe_light":     (105, 78, 160),
        "robe_high":      (145, 115, 200),

        # Armor trim / shoulders (dark blue metal)
        "armor_darkest":  (15,  25,  55),
        "armor_dark":     (30,  55,  95),
        "armor_mid":      (55,  90, 140),
        "armor_light":    (110, 150, 195),
        "armor_shine":    (180, 210, 240),

        # Gold trim
        "gold_dark":      (95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),
        "gold_shine":     (255, 235, 165),

        # Frost / ice energy
        "ice_darkest":    (10,  30,  75),
        "ice_dark":       (25,  70, 145),
        "ice_mid":        (70, 140, 225),
        "ice_light":      (140, 200, 250),
        "ice_bright":     (195, 230, 255),
        "ice_hot":        (225, 245, 255),
        "ice_white":      (245, 252, 255),

        # Eye glow (bright blue)
        "eye_dark":       (20,  60, 140),
        "eye_mid":        (70, 140, 240),
        "eye_light":      (150, 210, 255),
        "eye_hot":        (220, 245, 255),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_varkul._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_varkul.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_varkul._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_varkul._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_varkul._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_varkul._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale. Hero di-render ke canvas
            # offscreen lalu di-scale saat blit (heroes/__init__.py),
            # jadi titik canvas harus = (delta dunia)/scale supaya
            # beam/proyektil mendarat TEPAT di target setelah blit.
            # Boss yang digambar langsung di layar tidak terpengaruh
            # (scale = 1).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Ice / frost visual helpers
    # ---------------------------------------------------------------------------
    def _draw_ice_shard(surface, cx, cy, size, angle, color_dark, color_mid,
                        color_light, color_hot):
        """Draw a single sharp ice crystal shard."""
        ca, sa = math.cos(angle), math.sin(angle)
        tip_x = cx + ca * size
        tip_y = cy + sa * size
        base_l_x = cx + math.cos(angle + 2.4) * size * 0.35
        base_l_y = cy + math.sin(angle + 2.4) * size * 0.35
        base_r_x = cx + math.cos(angle - 2.4) * size * 0.35
        base_r_y = cy + math.sin(angle - 2.4) * size * 0.35

        _NS_varkul._poly(surface, color_dark, [
            (tip_x, tip_y), (base_l_x, base_l_y), (base_r_x, base_r_y)
        ])
        # Inner highlight
        _NS_varkul._poly(surface, color_mid, [
            (tip_x, tip_y),
            ((base_l_x + cx) / 2, (base_l_y + cy) / 2),
            ((base_r_x + cx) / 2, (base_r_y + cy) / 2),
        ])
        _NS_varkul._aaline(surface, color_light, (cx, cy), (tip_x, tip_y), 1)
        _NS_varkul._aacircle(surface, color_hot, (int(tip_x), int(tip_y)), 1)


    def _draw_snowflake(surface, cx, cy, size, phase, color=None):
        """Small rotating snowflake."""
        if color is None:
            color = _NS_varkul.PALETTE["ice_bright"]
        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            x1 = cx + int(math.cos(angle) * size)
            y1 = cy + int(math.sin(angle) * size)
            _NS_varkul._aaline(surface, color, (cx, cy), (x1, y1), 1)
            # Small branches
            bx = cx + int(math.cos(angle) * size * 0.6)
            by = cy + int(math.sin(angle) * size * 0.6)
            for b in (-1, 1):
                ba = angle + b * 0.5
                ex = bx + int(math.cos(ba) * size * 0.3)
                ey = by + int(math.sin(ba) * size * 0.3)
                _NS_varkul._aaline(surface, color, (bx, by), (ex, ey), 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_hot"], (cx, cy), 1)


    def _draw_frost_particles(surface, cx, cy, phase, radius=25, count=8):
        """Frosty motes swirling around a point."""
        for i in range(count):
            angle = phase * 0.6 + i * math.pi * 2 / count
            r = radius + int(math.sin(phase + i * 0.9) * 6)
            px = cx + int(math.cos(angle) * r)
            py = cy + int(math.sin(angle) * r * 0.6)
            alpha = int(140 + math.sin(phase * 1.4 + i) * 80)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha), (px, py), 2)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_hot"], alpha), (px, py), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM – Frost Orb
    # ---------------------------------------------------------------------------
    class FrostProjectile:
        """Frost orb projectile that travels toward a target."""
        def __init__(self, sx, sy, tx, ty, speed=5.5):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []

        def update(self):
            if not self.alive:
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail - frost mist
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 12)
                r = max(1, 6 - (len(self.trail) - i))
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], alpha), (tx, ty), r + 2)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha // 2), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Outer frost aura
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 90), (px, py), 15)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 140), (px, py), 11)
                # Core orb
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (px, py), 7)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (px, py), 5)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (px - 1, py - 1), 3)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (px - 1, py - 1), 1)
                # Ice shards protruding
                for i in range(4):
                    angle = phase * 3 + i * math.pi / 2
                    _NS_varkul._draw_ice_shard(surface, px, py, 8, angle,
                                    _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                                    _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    # ---------------------------------------------------------------------------
    # Chain Frost bouncing orb
    # ---------------------------------------------------------------------------
    class ChainFrostOrb:
        """Chain frost that bounces around."""
        def __init__(self, sx, sy, tx, ty, bounces=3):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = 4.5
            self.alive = True
            self.age = 0
            self.bounces_left = bounces
            self.trail = []

        def update(self, boss):
            if not self.alive:
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 3:
                if self.bounces_left > 0:
                    self.bounces_left -= 1
                    # Random new target direction
                    angle = self.age * 0.7
                    self.tx = self.x + math.cos(angle) * 120
                    self.ty = self.y + math.sin(angle) * 60
                else:
                    self.alive = False
                    return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 20:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(30 + i * 10)
                r = max(1, 5 - (len(self.trail) - i) // 2)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha), (tx, ty), r + 1)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], alpha // 2), (tx, ty), r)
            if self.alive:
                px, py = int(self.x), int(self.y)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 120), (px, py), 13)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 180), (px, py), 9)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (px, py), 6)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (px, py), 4)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (px - 1, py - 1), 2)
                # Rotating shards
                for i in range(5):
                    angle = phase * 4 + i * math.pi * 2 / 5
                    _NS_varkul._draw_ice_shard(surface, px, py, 7, angle,
                                    _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                                    _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_vk_last_x"):
            boss._vk_last_x = boss.x
            boss._vk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._vk_last_x)
        dy = abs(boss.y - boss._vk_last_y)
        boss._vk_last_x = boss.x
        boss._vk_last_y = boss.y
        return dx + dy > 0.3

    # ===================================================================
    # V2 ANIMATION CONTROLLER + LIVE FX BRIDGE
    # ===================================================================

    #: Fase serangan (fraksi 0..1 dari durasi serangan).
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.14),
        ("WINDUP",       0.14, 0.32),
        ("SWING",        0.32, 0.52),
        ("IMPACT",       0.52, 0.64),
        ("FOLLOW",       0.64, 0.82),
        ("RECOVERY",     0.82, 1.00),
    )

    #: Jendela hit aktif (dipakai debug & game feel).
    ATTACK_ACTIVE_WINDOW = (0.38, 0.64)
    ATTACK_IMPACT_FRAME = 0.52

    #: Prioritas state. Angka besar menang; DEATH mengunci.
    ANIM_STATES = {
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

    #: Aktifkan hitbox/hurtbox/jangkauan/state di arena.
    DEBUG_CHARACTER = False

    #: Modul FX layar (diisi malas). False = percobaan gagal -> canvas.
    _LIVE_MOD = None

    #: Tabel ark staff — SATU sumber kebenaran pose ayunan. Dipakai
    #: renderer canvas (``_draw_attack_arms``) DAN modul hidup
    #: (``heroes/varkul_fx.staff_arc``). Format: (t0, t1, theta0, theta1,
    #: ease); theta dalam radian dari vertikal, positif = ke arah depan.
    STAFF_ARC = (
        (0.00, 0.14, 0.00,  0.22, "out"),      # ANTICIPATION: angkat
        (0.14, 0.32, 0.22, -1.13, "io"),       # WINDUP: putar ke belakang
        (0.32, 0.52, -1.13, 1.42, "oc"),       # SWING: sapu cepat ke depan
        (0.52, 0.64, 1.42,  1.42, "hold"),     # IMPACT: tahan + overshoot
        (0.64, 0.82, 1.42, -0.48, "io"),       # FOLLOW THROUGH
        (0.82, 1.00, -0.48, 0.00, "io"),       # RECOVERY
    )

    @staticmethod
    def _arc_ease(kind, t):
        if t <= 0.0:
            return 0.0
        if t >= 1.0:
            return 1.0
        if kind == "out":
            return 1.0 - (1.0 - t) * (1.0 - t)
        if kind == "oc":                        # out-cubic
            return 1.0 - (1.0 - t) ** 3
        if kind == "hold":
            return math.sin(t * math.pi)
        # in-out (smoothstep)
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def _staff_lift(progress):
        """Tinggi tangan staff relatif (0 = idle, positif = terangkat)."""
        p = max(0.0, min(1.0, float(progress)))
        if p < 0.32:
            return _NS_varkul._arc_ease("out", p / 0.32)
        if p < 0.52:
            return 1.0 - _NS_varkul._arc_ease("oc", (p - 0.32) / 0.20) * 0.85
        if p < 0.82:
            return 0.15 + _NS_varkul._arc_ease("io", (p - 0.52) / 0.30) * 0.25
        return 0.4 * (1.0 - _NS_varkul._arc_ease("io", (p - 0.82) / 0.18))

    @classmethod
    def _staff_arc(cls, progress):
        """(theta, lift) staff untuk progress serangan 0..1.

        Staff TIDAK pernah diteleportasi: sudutnya diinterpolasi lewat
        tabel ark di atas, jadi crystal menelusuri lengkungan mulus
        wind-up -> sapuan -> follow-through.
        """
        p = max(0.0, min(1.0, float(progress)))
        for t0, t1, a0, a1, kind in cls.STAFF_ARC:
            if t0 <= p < t1:
                e = cls._arc_ease(kind, (p - t0) / max(0.0001, t1 - t0))
                return a0 + (a1 - a0) * e, cls._staff_lift(p)
        return 0.0, 0.0

    def attack_phases_order():
        return tuple(name for name, _a, _b in _NS_varkul.ATTACK_PHASES)

    def attack_phase(progress):
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_varkul.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    def _live_module():
        """Muat ``heroes.varkul_fx`` sekali; None kalau tidak tersedia."""
        NS = _NS_varkul
        if NS._LIVE_MOD is None:
            try:
                from heroes import varkul_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "VARKUL_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    def live_fx_ready():
        return _NS_varkul._live_module() is not None

    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Lapisan hidup untuk unit ini.

        Return ``(mod, owned)``. ``want_draw`` True pada jalur BOSS (draw
        dipanggil tiap frame tanpa cache sprite).
        """
        NS = _NS_varkul
        if portrait:
            return None, False
        mod = NS._live_module()
        if mod is None:
            return None, False
        try:
            if want_draw:
                mod.draw_ground_layer(surface, boss, x, y)
            else:
                mod.attach(boss)
        except Exception:
            return None, False
        try:
            owned = bool(mod.owns(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    def _update_varkul_anim(boss, moving=False):
        """ANIMATION CONTROLLER Varkul - state, fase, timing, delta-time.

        Satu-satunya sumber kebenaran untuk SEMUA state karakter; lapisan
        hidup (heroes/varkul_fx) serta alat uji membacanya dari sini.
        """
        G = _NS_varkul

        # ── delta time nyata (dipakai FX & transisi state) ──────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                      # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_vk_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._vk_last_ms = now
        boss._vk_dt = dt

        # ── timeline serangan ───────────────────────────────────────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 42)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vk_previous_timer", 0))
        active = bool(getattr(boss, "_vk_attack_active", False))

        triggered = timer >= cooldown - 1 and previous <= 1
        if triggered:
            boss._vk_attack_active = True
            boss._vk_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._vk_attack_frame = int(getattr(boss, "_vk_attack_frame",
                                                0)) + 1
        elif timer <= 0 and active:
            # serangan manual (alat audit / probe): majukan sampai selesai
            boss._vk_attack_frame = int(getattr(boss, "_vk_attack_frame",
                                                0)) + 1
            if int(getattr(boss, "_vk_attack_frame", 0)) > cooldown:
                boss._vk_attack_active = False
                boss._vk_attack_frame = 0
                active = False

        boss._vk_previous_timer = timer
        if active:
            prog = min(1.0, int(getattr(boss, "_vk_attack_frame", 0))
                       / max(1, cooldown))
        else:
            prog = 0.0
        boss._vk_attack_progress = prog
        boss._vk_attack_raw = prog
        boss._vk_attack_phase = G.attack_phase(prog) if active else "NONE"
        boss._vk_hit_active = active and (G.ATTACK_ACTIVE_WINDOW[0] <= prog <
                                          G.ATTACK_ACTIVE_WINDOW[1])
        boss._vk_impact_frame = active and abs(prog - G.ATTACK_IMPACT_FRAME) \
            < 0.025

        # ── hurt / hit flash ────────────────────────────────────────
        hurt = int(getattr(boss, "_vk_hurt_frames", 0) or 0)
        if hurt > 0:
            hurt -= 1
        if int(getattr(boss, "hurt_flash_timer", 0) or 0) > 0:
            hurt = max(hurt, 7)
        boss._vk_hurt_frames = hurt

        # ── resolve state ───────────────────────────────────────────
        if not getattr(boss, "alive", True):
            state = "DEATH"
        elif hurt > 0:
            state = "HURT"
        elif getattr(boss, "active_skill", None) is not None:
            state = ("SPECIAL" if getattr(boss, "active_skill", None) == "r"
                     else "SKILL")
        elif active:
            ph = boss._vk_attack_phase
            if ph in ("ANTICIPATION", "WINDUP"):
                state = "CHARGE"
            elif ph in ("SWING", "IMPACT"):
                state = "SWING"
            else:
                state = "ATTACK"
        elif moving:
            state = ("RUN" if float(getattr(boss, "speed", 1.0)) >= 2.2
                     else "WALK")
        else:
            state = "IDLE"

        old = getattr(boss, "_vk_state", None)
        boss._vk_state_prev = old or state
        if old != state:
            boss._vk_state_time = 0.0
        else:
            boss._vk_state_time = (float(getattr(boss, "_vk_state_time", 0.0))
                                   + dt)
        boss._vk_state = state

    def _resolve_pose(boss, moving=False):
        """(action, phase, attack_progress) untuk renderer & FX."""
        skill = getattr(boss, "active_skill", None)
        active = bool(getattr(boss, "_vk_attack_active", False))
        if skill:
            action = "cast"
        elif active:
            action = "attack"
        elif moving:
            action = "walk"
        else:
            action = "idle"
        phase = float(getattr(boss, "pulse", 0.0) or 0.0)
        ap = (float(getattr(boss, "_vk_attack_progress", 0.0) or 0.0)
              if active else 0.0)
        return action, phase, ap

    def _staff_tip_screen(boss, x, y):
        """Titik crystal staff untuk FX (semua FX memakai modul hidup,
        yang membacanya dari ``_resolve_pose`` + ``_staff_arc``)."""
        action = getattr(boss, "_vk_pose_action", "idle")
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        if action == "attack":
            theta, lift = _NS_varkul._staff_arc(
                float(getattr(boss, "_vk_attack_progress", 0.0) or 0.0))
            hand_x = x - facing * (23 - 6 * lift)
            hand_y = y + 8 - 30 * lift
            return (hand_x + facing * math.sin(theta) * 50,
                    hand_y - math.cos(theta) * 50)
        if action == "cast":
            return (x - facing * 20, y - 66)
        return (x - facing * 21, y - 30)

    def _draw_varkul_debug(surface, boss, x, y):
        """Overlay DEBUG_CHARACTER: hitbox, state, frame, FPS."""
        NS = _NS_varkul
        r = max(6, int(getattr(boss, "radius", 16)))
        pygame.draw.rect(surface, (80, 170, 255, 150),
                         pygame.Rect(int(x) - r, int(y) - r - 8, r * 2,
                                     r * 2), 1)
        rng = max(10, int(getattr(boss, "range", 200) * 0.7))
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        pygame.draw.line(surface, (255, 210, 60, 150), (int(x), int(y)),
                         (int(x + rng * f), int(y)), 1)
        pygame.draw.rect(surface, (255, 210, 60, 110),
                         pygame.Rect(int(x + rng * f) - 5, int(y) - 7, 10,
                                     14), 1)
        hb = None
        if getattr(boss, "_vk_hit_active", False):
            reach = int(rng)
            top = int(y - 44)
            left = int(x) if f > 0 else int(x) - reach
            hb = pygame.Rect(left, top, max(8, reach), max(10, 80))
            pygame.draw.rect(surface, (255, 70, 70, 190), hb, 2)
            pygame.draw.rect(surface, (255, 70, 70, 60), hb)
        state = getattr(boss, "_vk_state", "IDLE")
        ph = getattr(boss, "_vk_attack_phase", "NONE")
        frames = int(getattr(boss, "_vk_attack_frame", 0))
        prog = float(getattr(boss, "_vk_attack_progress", 0.0))
        hurt = int(getattr(boss, "_vk_hurt_frames", 0))
        dtv = float(getattr(boss, "_vk_dt", 1.0 / 60.0))
        inst = 1.0 / dtv if dtv > 0 else 60.0
        fps = float(getattr(boss, "_vk_fps", 60.0))
        fps = fps + (inst - fps) * 0.1
        boss._vk_fps = fps
        mod = NS._live_module()
        n_part = n_proj = -1
        if mod is not None:
            try:
                n_part = mod.total_particles()
                n_proj = len(mod.projectiles_for(boss))
            except Exception:
                pass
        lines = [
            f"VARKUL {state} {ph}",
            f"frame {frames} t={prog:.2f} hurt={hurt}",
            f"hit={'Y' if hb else 'N'} fps={fps:.0f}",
            f"dt={dtv:.4f} proj={n_proj} part={n_part}",
        ]
        font = None
        try:
            from _render import get_font
            font = get_font(14)
        except Exception:
            pass
        if font is None:
            return
        px, py = int(x) - 80, int(y) + 36
        for i, line in enumerate(lines):
            s = font.render(line, True, (220, 255, 230))
            surface.blit(s, (px, py + i * 14))

    def _update_attack_anim(boss):
        """Backward-compatible alias ke controller V2."""
        return _NS_varkul._update_varkul_anim(
            boss, _NS_varkul._detect_moving(boss))

    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_vk_projectiles"):
            boss._vk_projectiles = []
        for proj in boss._vk_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._vk_projectiles = [p for p in boss._vk_projectiles if p.alive or p.age < 8]


    def _manage_chain_orbs(boss, surface, phase):
        if not hasattr(boss, "_vk_chain_orbs"):
            boss._vk_chain_orbs = []
        for orb in boss._vk_chain_orbs:
            orb.update(boss)
            orb.draw(surface, phase)
        boss._vk_chain_orbs = [o for o in boss._vk_chain_orbs if o.alive or o.age < 8]


    def _spawn_projectile(boss, x, y):
        if not hasattr(boss, "_vk_projectiles"):
            boss._vk_projectiles = []
        tx, ty = _NS_varkul._target_position(boss, x, y)
        # Lepaskan dari crystal staff pada ark (progress ~0.43, layar
        # 1:1; canvas fallback memakai skala 1)
        facing = getattr(boss, "direction", 1)
        try:
            scale = float(getattr(boss, "_render_scale", 1.0) or 1.0)
        except (TypeError, ValueError):
            scale = 1.0
        theta, lift = _NS_varkul._staff_arc(0.43)
        sx = x - facing * (23 - 6 * lift) * scale + \
            facing * math.sin(theta) * 50 * scale
        sy = y + (8 - 30 * lift - math.cos(theta) * 50) * scale
        boss._vk_projectiles.append(_NS_varkul.FrostProjectile(sx, sy, tx, ty, speed=5.5))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_varkul(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus jalur hero-lane.

        Urutan lapisan: GROUND -> GROUND FX -> SHADOW -> CHARACTER BODY
        (back robe -> lower robe -> torso -> armor -> head -> weapon) ->
        ATTACK TRAIL/PROJECTILE/PARTICLES/SKILL FX/IMPACT (lapisan hidup
        heroes/varkul_fx) -> DEBUG. Trail, proyektil, impact, hit-stop &
        shake hidup di modul layar 1:1; canvas hanya fallback.
        """
        NS = _NS_varkul
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = NS._detect_moving(boss)
        NS._update_varkul_anim(boss, moving)
        action, phase, ap = NS._resolve_pose(boss, moving)
        boss._vk_pose_action = action
        boss._vk_phase = phase
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")
        facing = getattr(boss, "direction", 1) or 1
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)

        # ── lapisan hidup (boss jalur 1:1; lane dipicu heroes/__init__)
        live, owned = NS._live_fx(boss, surface, x, y,
                                  not hero_lane, portrait)
        boss._vk_suppress_canvas_projectile = owned

        # ── GROUND LAYERS ──────────────────────────────────────────
        if not portrait:
            NS._draw_frost_aura(surface, x, y, pulse)
            NS._draw_ice_platform(surface, x, y + 40, pulse, active_skill)
            if not owned:
                if active_skill == "q":
                    NS._draw_frost_blast_ground(surface, boss, x, y,
                                                skill_timer, pulse)
                elif active_skill == "e":
                    NS._draw_sacrifice_circle(surface, boss, x, y,
                                              skill_timer, pulse)
                elif active_skill == "r":
                    NS._draw_chain_frost_ground(surface, boss, x, y,
                                                skill_timer, pulse)

        # ---------- Character body (dengan hurt-flash mask) ----------
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            if NS._flash_buf is None:
                NS._flash_buf = pygame.Surface((220, 240), pygame.SRCALPHA)
            NS._flash_buf.fill((0, 0, 0, 0))
            NS._record_shadow = []
            _tgt, _tx, _ty = NS._flash_buf, 110, 120

        if action == "attack":
            NS._draw_varkul_attack(_tgt, boss, _tx, _ty)
        elif action == "cast":
            NS._draw_varkul_cast(_tgt, boss, _tx, _ty)
        elif action in ("walk", "run"):
            NS._draw_varkul_walk(_tgt, boss, _tx, _ty)
        else:
            NS._draw_varkul_idle(_tgt, boss, _tx, _ty)

        if flash > 0:
            surface.blit(NS._flash_buf, (x - _tx, y - _ty))
            w = int(235 * min(1.0, flash / 8.0))
            m = pygame.mask.from_surface(NS._flash_buf, 50)
            wht = m.to_surface(setcolor=(w, int(w * 0.9), int(w * 0.8), 255),
                               unsetcolor=(0, 0, 0, 0))
            for rect in (NS._record_shadow or ()):
                wht.fill((0, 0, 0, 0), rect)
            surface.blit(wht, (x - _tx, y - _ty),
                         special_flags=pygame.BLEND_RGB_ADD)
            NS._record_shadow = None

        # ---------- Projectiles (fallback canvas) ----------
        if not owned:
            NS._manage_projectiles(boss, surface, pulse)
            NS._manage_chain_orbs(boss, surface, pulse)

        # ---------- Skill foreground effects (fallback canvas) ----------
        if not owned and active_skill:
            if active_skill == "q":
                NS._draw_frost_blast(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "w":
                NS._draw_frostbite(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                NS._draw_sacrifice_foreground(surface, boss, x, y,
                                              skill_timer, pulse)
            elif active_skill == "r":
                NS._draw_chain_frost(surface, boss, x, y, skill_timer, pulse)

        # ── LIVE TOP LAYER (trail / projectile / impact / particle) ─
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

        # ---------- DEBUG ----------
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_varkul_debug(surface, boss, x, y)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_varkul_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_varkul._draw_shadow(surface, x, y + 48)
        _NS_varkul._draw_floating_mist(surface, x, y + 35, boss.pulse)
        _NS_varkul._draw_varkul_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_varkul_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_varkul._draw_shadow(surface, x + sway, y + 48)
        _NS_varkul._draw_floating_mist(surface, x + sway, y + 35, phase, trail=True,
                            facing=boss.direction)
        _NS_varkul._draw_varkul_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_varkul_attack(surface, boss, x, y):
        progress = getattr(boss, "_vk_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Spawn projectile at the right moment (ark swing melewati vertikal)
        if 0.38 < progress < 0.48 and not getattr(boss, "_vk_proj_spawned", False):
            if not getattr(boss, "_vk_suppress_canvas_projectile", False):
                _NS_varkul._spawn_projectile(boss, x, y)
            else:
                try:
                    from heroes import varkul_fx as _vfx
                    _vfx.notify_projectile_cast(boss, x, y)
                except Exception:
                    pass
            boss._vk_proj_spawned = True
        if progress < 0.15 or progress > 0.9:
            boss._vk_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 2) * -boss.direction
        _NS_varkul._draw_shadow(surface, x + recoil, y + 48)
        _NS_varkul._draw_floating_mist(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_varkul._draw_varkul_body(surface, x + recoil, y, boss.direction, boss.pulse,
                          "attack", progress)
        _NS_varkul._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    def _draw_varkul_cast(surface, boss, x, y):
        """Pose CAST (skill q/w/e/r): staff terangkat, orb tangan menyala.

        Menggunakan tabel ark yang sama dengan serangan pada progress
        channel (staff lurus ke atas) supaya transisi attack<->cast mulus.
        """
        skill = getattr(boss, "active_skill", None)
        # channel: staff naik saat mulai, sedikit turun menjelang release
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        total = {"q": 50, "w": 60, "e": 50, "r": 80}.get(skill, 50)
        t = 1.0 - (skill_timer / float(total)) if total else 0.0
        progress = 0.20 + 0.03 * math.sin(boss.pulse * 2.5) - 0.10 * t

        recoil = int(math.sin(boss.pulse * 1.4) * 1) * -boss.direction
        _NS_varkul._draw_shadow(surface, x + recoil, y + 48)
        _NS_varkul._draw_floating_mist(surface, x + recoil, y + 35, boss.pulse,
                            intense=(skill in ("r", "e")))
        _NS_varkul._draw_varkul_body(surface, x + recoil, y, boss.direction,
                          boss.pulse, "cast", progress)
        _NS_varkul._draw_channel_glow(surface, x + recoil, y, boss.direction,
                                      t, skill)


    # ===================================================================
    # BODY RENDERING – HD detailed Lich
    # ===================================================================
    def _draw_varkul_body(surface, cx, cy, facing, phase, action,
                          attack_progress=0):
        """Komposit ORIGINAL-MAX: badak ke buffer tetap, outline siluet
        gelap 1 px + pass pencahayaan rim/shade, lalu blit ke posisi sama."""
        _composite_boss_body(
            surface, _NS_varkul, _NS_varkul._draw_varkul_body_raw,
            cx, cy, facing, phase, action, attack_progress,
            rim_add=(70, 120, 210), bsize=180)

    def _masterwork_finish(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """ORIGINAL-MAX detail pass: rim kiri-atas + pemisah bagian + detail
        wajah/emblem agar tetap terbaca saat downscale."""
        P = _NS_varkul.PALETTE
        pygame.draw.circle(surface, P["bone_shine"], (cx - 10, cy - 36), 1)
        pygame.draw.circle(surface, P["bone_light"], (cx - 9, cy - 34), 2)
        for side in (-1, 1):
            pygame.draw.circle(surface, P["bone_shine"], (cx + side * 8, cy - 44), 1)
            pygame.draw.circle(surface, P["ice_white"], (cx + side * 7, cy - 45), 1)
        pygame.draw.line(surface, P["shadow_deep"], (cx - 6, cy - 20), (cx + 6, cy - 20), 1)
        pygame.draw.line(surface, P["shadow_deep"], (cx - 10, cy - 1), (cx + 10, cy - 1), 1)
        pygame.draw.line(surface, P["robe_darkest"], (cx - 13, cy + 27), (cx + 13, cy + 27), 1)
        pygame.draw.circle(surface, P["bone_shine"], (cx - 1, cy - 8), 1)
        pygame.draw.line(surface, P["gold_light"], (cx - 10, cy - 14), (cx, cy - 9), 1)
        orb_x = cx - 20 * facing
        orb_y = cy - 20
        pygame.draw.circle(surface, P["ice_hot"], (orb_x - 1, orb_y - 2), 2)
        pygame.draw.circle(surface, P["ice_white"], (orb_x - 1, orb_y - 2), 1)


    def _draw_varkul_body_raw(surface, cx, cy, facing, phase, action,
                              attack_progress=0):
        # Cape / robe back
        _NS_varkul._draw_robe_back(surface, cx, cy, facing, phase, action)

        # Lower robes (floating)
        _NS_varkul._draw_lower_robes(surface, cx, cy + 5, phase)

        # Torso robes with skull
        _NS_varkul._draw_torso(surface, cx, cy - 8, phase)

        # Pauldrons
        _NS_varkul._draw_pauldrons(surface, cx, cy - 18, phase)

        # Arms – staff arm and casting arm
        if action in ("attack", "cast"):
            _NS_varkul._draw_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_varkul._draw_idle_arms(surface, cx, cy - 8, facing, phase, action)

        # Skull head with crown
        _NS_varkul._draw_skull_head(surface, cx, cy - 30, phase)

        # Floating frost particles
        _NS_varkul._draw_body_particles(surface, cx, cy, phase)

        # ORIGINAL-MAX detail pass (rim + separator + emblem)
        _NS_varkul._masterwork_finish(surface, cx, cy, facing, phase, action,
                                      attack_progress)


    def _draw_robe_back(surface, cx, cy, facing, phase, action):
        """Back of robe / cape."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.1 + 0.5) * 2

        # Outer cape
        cape_outer = [
            (cx - 15, cy - 12),
            (cx - 20, cy + 5),
            (cx - 26 - int(wave), cy + 28),
            (cx - 18 - int(wave2), cy + 42),
            (cx - 5, cy + 46),
            (cx + 5, cy + 46),
            (cx + 18 + int(wave2), cy + 42),
            (cx + 26 + int(wave), cy + 28),
            (cx + 20, cy + 5),
            (cx + 15, cy - 12),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_darkest"], cape_outer)

        cape_mid = [
            (cx - 13, cy - 10),
            (cx - 17, cy + 5),
            (cx - 22 - int(wave * 0.7), cy + 26),
            (cx - 14, cy + 38),
            (cx, cy + 40),
            (cx + 14, cy + 38),
            (cx + 22 + int(wave * 0.7), cy + 26),
            (cx + 17, cy + 5),
            (cx + 13, cy - 10),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_dark"], cape_mid)

        # Inner lining (lighter purple)
        cape_inner = [
            (cx - 10, cy - 6),
            (cx - 13, cy + 5),
            (cx - 16, cy + 22),
            (cx - 8, cy + 32),
            (cx + 8, cy + 32),
            (cx + 16, cy + 22),
            (cx + 13, cy + 5),
            (cx + 10, cy - 6),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_mid"], cape_inner)

        # Ice crystals on cape edges
        for i, (px, py) in enumerate([(cx - 24, cy + 24), (cx + 24, cy + 24),
                                        (cx - 18, cy + 38), (cx + 18, cy + 38)]):
            size = 4 + int(math.sin(phase + i) * 1)
            _NS_varkul._draw_ice_shard(surface, px, py, size, -math.pi / 2 + math.sin(phase) * 0.1,
                            _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                            _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    def _draw_lower_robes(surface, cx, cy, phase):
        """Floating lower body with tattered robes (no legs)."""
        sway = int(math.sin(phase * 0.6) * 2)
        # Outer robe
        robe_outer = [
            (cx - 17, cy),
            (cx + 17, cy),
            (cx + 21 + sway, cy + 14),
            (cx + 15, cy + 24),
            (cx + 8, cy + 30),
            (cx + 3, cy + 32),
            (cx - 3, cy + 32),
            (cx - 8, cy + 30),
            (cx - 15, cy + 24),
            (cx - 21 - sway, cy + 14),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in robe_outer])
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_darkest"], robe_outer)

        robe_mid = [
            (cx - 14, cy + 2),
            (cx + 14, cy + 2),
            (cx + 17 + sway, cy + 14),
            (cx + 11, cy + 22),
            (cx + 5, cy + 27),
            (cx - 5, cy + 27),
            (cx - 11, cy + 22),
            (cx - 17 - sway, cy + 14),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_dark"], robe_mid)

        robe_inner = [
            (cx - 10, cy + 4),
            (cx + 10, cy + 4),
            (cx + 13 + sway, cy + 14),
            (cx + 7, cy + 20),
            (cx - 7, cy + 20),
            (cx - 13 - sway, cy + 14),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_mid"], robe_inner)

        # Tattered bottom
        for i in range(7):
            tx = cx - 15 + i * 5
            ty = cy + 28 + int(math.sin(phase * 1.3 + i) * 3)
            _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_dark"], [
                (tx - 2, cy + 24), (tx + 2, cy + 24),
                (tx + 1, ty + 4), (tx - 1, ty + 4),
            ])

        # Gold belt
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["gold_dark"], (cx - 18, cy - 1, 36, 5))
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["gold_mid"], (cx - 16, cy, 32, 3))
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["gold_light"], (cx - 13, cy + 1, 26, 1))

        # Belt center gem – ice
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_darkest"], (cx, cy + 1), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_dark"], (cx, cy + 1), 3)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (cx - 1, cy), 2)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (cx - 1, cy), 1)


    def _draw_torso(surface, cx, cy, phase):
        """Torso with robes and a skull emblem."""
        # Shadow
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["shadow_deep"], [
            (cx - 13 + 2, cy - 10 + 2), (cx + 13 + 2, cy - 10 + 2),
            (cx + 11 + 2, cy + 14 + 2), (cx + 5 + 2, cy + 19 + 2),
            (cx - 5 + 2, cy + 19 + 2), (cx - 11 + 2, cy + 14 + 2),
        ])
        # Main torso
        torso = [
            (cx - 13, cy - 10), (cx + 13, cy - 10),
            (cx + 11, cy + 14), (cx + 5, cy + 19),
            (cx - 5, cy + 19), (cx - 11, cy + 14),
        ]
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_darkest"], torso)
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_dark"], [
            (cx - 11, cy - 8), (cx + 11, cy - 8),
            (cx + 9, cy + 12), (cx + 4, cy + 16),
            (cx - 4, cy + 16), (cx - 9, cy + 12),
        ])
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["robe_mid"], [
            (cx - 8, cy - 5), (cx + 8, cy - 5),
            (cx + 6, cy + 8), (cx + 3, cy + 12),
            (cx - 3, cy + 12), (cx - 6, cy + 8),
        ])

        # Center skull emblem (bone)
        sk_cx, sk_cy = cx, cy + 2
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_dark"], (sk_cx, sk_cy - 2), 5)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_mid"], (sk_cx, sk_cy - 2), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_light"], (sk_cx - 1, sk_cy - 3), 2)
        # Eye sockets on emblem
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow"], (sk_cx - 2, sk_cy - 3), 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow"], (sk_cx + 2, sk_cy - 3), 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_hot"], (sk_cx - 2, sk_cy - 3), 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_hot"], (sk_cx + 2, sk_cy - 3), 1)
        # Jaw
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["bone_dark"], (sk_cx - 2, sk_cy + 1, 4, 3))
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["bone_mid"], (sk_cx - 2, sk_cy + 1, 4, 2))

        # Gold V-neck trim
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["gold_dark"], (cx - 11, cy - 8), (cx, cy - 2), 2)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["gold_dark"], (cx + 11, cy - 8), (cx, cy - 2), 2)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["gold_mid"], (cx - 10, cy - 7), (cx, cy - 3), 1)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["gold_mid"], (cx + 10, cy - 7), (cx, cy - 3), 1)


    def _draw_pauldrons(surface, cx, cy, phase):
        """Ice-crowned shoulder pauldrons."""
        for side in (-1, 1):
            sx = cx + side * 15
            # Shadow
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow_deep"], (sx + 2, cy + 2), 10)
            # Metal pauldron base
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["armor_darkest"], (sx, cy), 9)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["armor_dark"], (sx - side, cy - 1), 7)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["armor_mid"], (sx - side * 2, cy - 2), 5)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["armor_light"], (sx - side * 2, cy - 3), 2)

            # Gold trim
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_dark"], (sx, cy), 9, 2)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_mid"], (sx, cy), 8, 1)

            # Ice crystal spikes on top of pauldron
            for i, off_a in enumerate([-0.4, 0.0, 0.4]):
                spike_angle = -math.pi / 2 + off_a
                size = 6 if i == 1 else 4
                _NS_varkul._draw_ice_shard(surface, sx, cy - 4, size,
                                spike_angle,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    def _draw_idle_arms(surface, cx, cy, facing, phase, action):
        """Arms - one holds staff, one has orb of frost."""
        sway = int(math.sin(phase * 0.7) * 1)

        # LEFT (staff arm - opposite of facing)
        staff_side = -facing
        ss_x = cx + staff_side * 13
        ss_y = cy + 2
        se_x = ss_x + staff_side * 6
        se_y = cy + 12 + sway
        sh_x = se_x + staff_side * 4
        sh_y = se_y + 10
        _NS_varkul._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_varkul._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Draw staff
        _NS_varkul._draw_staff(surface, sh_x, sh_y, phase, staff_side)

        # RIGHT (orb hand - facing direction)
        orb_side = facing
        os_x = cx + orb_side * 13
        os_y = cy + 2
        oe_x = os_x + orb_side * 8
        oe_y = cy + 10 + sway
        oh_x = oe_x + orb_side * 5
        oh_y = oe_y + 8
        _NS_varkul._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_varkul._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        # Skeletal hand
        _NS_varkul._draw_skeletal_hand(surface, oh_x, oh_y)
        # Frost orb in hand
        _NS_varkul._draw_hand_orb(surface, oh_x + orb_side * 4, oh_y + 2, phase, 5)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Attack pose — AYUNAN ARK staff (bukan translasi).

        Staff diputar mengelilingi tangan mengikuti tabel
        ``_NS_varkul.STAFF_ARC``:

            ANTICIPATION  angkat staff, badan mengecil (menyiapkan)
            WIND-UP       staff berputar ke belakang kepala
            SWING         sapuan cepat melewati vertikal (out-cubic)
            IMPACT        tahan di depan-bawah + overshoot kecil
            FOLLOW        rileks naik kembali
            RECOVERY      kembali ke pose idle

        Posisi tangan dan sudut staff dibaca dari SATU fungsi
        ``_staff_arc`` yang juga dipakai modul hidup, sehingga trail,
        proyektil, dan FX selalu lahir tepat di crystal staff.
        """
        NS = _NS_varkul
        staff_side = -facing
        theta, lift = NS._staff_arc(progress)

        # ---- STAFF arm: bahu -> siku -> tangan (mengikuti lift) ----
        ss_x = cx + staff_side * 13
        ss_y = cy + 2
        sh_x = cx + staff_side * (23 - 6 * lift)
        sh_y = cy + 16 - 30 * lift
        # siku sedikit keluar supaya lengan tidak kaku
        mid_x = (ss_x + sh_x) / 2 + staff_side * 3
        mid_y = (ss_y + sh_y) / 2 + 2
        NS._draw_arm_segment(surface, ss_x, ss_y, mid_x, mid_y)
        NS._draw_arm_segment(surface, mid_x, mid_y, sh_x, sh_y)

        # ---- STAFF berputar pada titik tangan ----
        NS._draw_staff_arc(surface, sh_x, sh_y, phase, staff_side, theta,
                           casting=True, progress=progress)

        # ---- ORB hand: tarik saat wind-up, dorong saat swing ----
        orb_side = facing
        os_x = cx + orb_side * 13
        os_y = cy + 2
        if progress < 0.32:
            t = progress / 0.32
            ext = -0.4 * t          # tarik ke belakang (anticipation)
        elif progress < 0.52:
            t = (progress - 0.32) / 0.20
            ext = -0.4 + 1.4 * t    # dorong kuat ke depan saat swing
        elif progress < 0.64:
            ext = 1.0
        else:
            t = (progress - 0.64) / 0.36
            ext = 1.0 - t * 0.85

        oe_x = os_x + orb_side * int(6 + ext * 6)
        oe_y = cy + int(10 - ext * 6)
        oh_x = oe_x + orb_side * int(5 + ext * 5)
        oh_y = oe_y + int(8 - ext * 6)

        NS._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        NS._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        NS._draw_skeletal_hand(surface, oh_x, oh_y)

        # Orb tangan membesar mendekati frame rilis (bobot + antisipasi)
        release_pulse = 0.0
        if 0.38 < progress < 0.55:
            release_pulse = math.sin((progress - 0.38) / 0.17 * math.pi)
        orb_size = 6 + int(math.sin(progress * math.pi) * 4
                           + release_pulse * 4)
        NS._draw_hand_orb(surface, oh_x + orb_side * 4, oh_y + 2, phase,
                          orb_size)

        # Frost trail dari tangan saat swing melewati vertikal
        if 0.36 < progress < 0.60:
            intensity = math.sin((progress - 0.36) / 0.24 * math.pi)
            for i in range(4):
                angle = phase * 3 + i * math.pi / 2
                ex = oh_x + int(math.cos(angle) * 12 * intensity) * facing
                ey = oh_y + int(math.sin(angle) * 10 * intensity)
                NS._aacircle(surface,
                             (*NS.PALETTE["ice_light"], 180),
                             (ex, ey), max(1, int(3 * intensity)))
                NS._aacircle(surface,
                             (*NS.PALETTE["ice_white"], 200),
                             (ex, ey), max(1, int(2 * intensity)))

    def _draw_staff_arc(surface, x, y, phase, side, theta, casting=False,
                        progress=0):
        """Staff yang SELURUHNYA berputar mengelilingi tangan.

        Mirip ``_draw_staff`` (pole gelap -> mid -> light, cincin emas,
        cakar metal + kristal es di kepala), tetapi pole digambar pada
        sudut ``theta`` dari vertikal — inilah yang membuat ayunan
        terasa berbobot: ujung crystal menempuh lengkungan sungguhan.
        """
        NS = _NS_varkul
        P = NS.PALETTE
        st = math.sin(theta)
        ct = math.cos(theta)
        top_x = x + st * 44
        top_y = y - ct * 44
        bot_x = x - st * 8
        bot_y = y + ct * 16

        # Shadow pole
        NS._aaline(surface, P["shadow_deep"],
                   (top_x + 2, top_y + 2), (bot_x + 2, bot_y + 2), 5)
        # Wood/metal staff (3 ramp)
        NS._aaline(surface, P["armor_darkest"], (top_x, top_y),
                   (bot_x, bot_y), 4)
        NS._aaline(surface, P["armor_dark"], (top_x, top_y),
                   (bot_x, bot_y), 3)
        NS._aaline(surface, P["armor_mid"], (top_x, top_y),
                   (bot_x, bot_y), 1)

        # Gold rings mengikuti pole
        for t in (0.3, 0.6, 0.85):
            rx = int(top_x + (bot_x - top_x) * t)
            ry = int(top_y + (bot_y - top_y) * t)
            NS._aacircle(surface, P["gold_dark"], (rx, ry), 3)
            NS._aacircle(surface, P["gold_mid"], (rx, ry), 2)
            NS._aacircle(surface, P["gold_light"], (rx - 1, ry - 1), 1)

        # Kepala staff: crystal cluster pada ujung pole (searah theta)
        head_x = int(top_x + st * 4)
        head_y = int(top_y - ct * 4)

        glow_size = 6
        if casting:
            glow_size = 6 + int(math.sin(progress * math.pi) * 7)

        NS._aacircle(surface, (*P["ice_dark"], 80), (head_x, head_y),
                     glow_size + 3)
        NS._aacircle(surface, (*P["ice_mid"], 130), (head_x, head_y),
                     glow_size)

        # Cakar metal memegang kristal (rotasi ikut theta)
        for offset_a in (-1.2, -0.4, 0.4, 1.2):
            ang = theta + math.pi / 2 + offset_a * 0.35
            cx1 = head_x + int(math.cos(ang) * 3)
            cy1 = head_y + int(math.sin(ang) * 3)
            cx2 = head_x + int(math.cos(ang) * 8)
            cy2 = head_y + int(math.sin(ang) * 8) - (2 if ct > 0.3 else 0)
            NS._aaline(surface, P["armor_darkest"], (cx1, cy1), (cx2, cy2), 3)
            NS._aaline(surface, P["armor_mid"], (cx1, cy1), (cx2, cy2), 1)

        # Kristal utama mengarah sejajar pole
        NS._draw_ice_shard(surface, head_x, head_y, 8,
                           theta - math.pi / 2,
                           P["ice_darkest"], P["ice_dark"],
                           P["ice_light"], P["ice_white"])
        # Center gem
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        NS._aacircle(surface, P["ice_dark"], (head_x, head_y - 2), 4)
        NS._aacircle(surface, P["ice_mid"], (head_x, head_y - 2),
                     int(3 * pulse) + 1)
        NS._aacircle(surface, P["ice_bright"], (head_x, head_y - 3), 2)
        NS._aacircle(surface, P["ice_white"], (head_x, head_y - 3), 1)

    def _draw_channel_glow(surface, x, y, facing, t, skill):
        """Cahaya channeling saat cast skill: kristal staff + orb tangan."""
        NS = _NS_varkul
        P = NS.PALETTE
        intensity = math.sin(min(1.0, max(0.0, t)) * math.pi)
        # kristal staff (sisi belakang, terangkat)
        head_x = x - facing * 20
        head_y = y - 66
        NS._aacircle(surface, (*P["ice_mid"], int(140 * intensity)),
                     (head_x, head_y), int(6 + intensity * 5))
        NS._aacircle(surface, (*P["ice_bright"], int(170 * intensity)),
                     (head_x, head_y), int(3 + intensity * 3))
        # orb tangan depan membesar mendekati rilis
        orb_x = x + facing * 22
        orb_y = y - 14
        r = int(4 + intensity * 6)
        NS._aacircle(surface, (*P["ice_dark"], int(120 * intensity)),
                     (orb_x, orb_y), r + 3)
        NS._aacircle(surface, (*P["ice_mid"], int(180 * intensity)),
                     (orb_x, orb_y), r + 1)
        NS._aacircle(surface, P["ice_light"], (orb_x, orb_y), r)
        NS._aacircle(surface, P["ice_white"], (orb_x, orb_y), 1)
        # rune kecil berputar di sekitar orb
        rot = t * 7.0
        for i in range(4):
            a = rot + i * math.pi / 2
            rx = orb_x + int(math.cos(a) * (r + 9))
            ry = orb_y + int(math.sin(a) * (r + 7))
            NS._rect(surface, (*P["ice_bright"], int(200 * intensity)),
                     (rx, ry, 2, 2))


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Draw a robed arm segment."""
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 8)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["robe_darkest"], (x1, y1), (x2, y2), 7)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["robe_dark"], (x1, y1), (x2, y2), 5)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["robe_mid"], (x1, y1), (x2, y2), 3)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["robe_light"], (x1, y1 - 1), (x2, y2 - 1), 1)
        # Gold cuff at joint
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_dark"], (mx, my), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_mid"], (mx, my), 3)


    def _draw_skeletal_hand(surface, x, y):
        """Small bony hand."""
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_dark"], (x, y), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_mid"], (x, y), 3)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_light"], (x - 1, y - 1), 1)


    def _draw_hand_orb(surface, x, y, phase, size=5):
        """Frost orb hovering in hand (chunky: core tegas + glint pixel)."""
        pulse = math.sin(phase * 1.8) * 0.3 + 0.7
        s = max(2, int(size * pulse))
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 70), (x, y), s + 3)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 120), (x, y), s + 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (x, y), s)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (x - 1, y - 1), max(1, s - 2))
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (x - 1, y - 1), 1)

        # Kilau chunky (rect pixel, bukan lingkaran lembut)
        for i in range(3):
            angle = phase * 2 + i * math.pi * 2 / 3
            sx = x + int(math.cos(angle) * (s + 4))
            sy = y + int(math.sin(angle) * (s + 4))
            _NS_varkul._rect(surface, _NS_varkul.PALETTE["ice_bright"], (sx, sy, 2, 2))


    def _draw_staff(surface, x, y, phase, side, casting=False, progress=0):
        """The frost staff with ice crystal head."""
        # Staff pole - long
        top_x = x + side * -2
        top_y = y - 40
        bot_x = x + side * 4
        bot_y = y + 20

        # Shadow
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["shadow_deep"],
                (top_x + 2, top_y + 2), (bot_x + 2, bot_y + 2), 5)
        # Wood/metal staff
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_darkest"], (top_x, top_y), (bot_x, bot_y), 4)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_dark"], (top_x, top_y), (bot_x, bot_y), 3)
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_mid"], (top_x, top_y), (bot_x, bot_y), 1)

        # Gold rings on staff
        for t in (0.3, 0.6, 0.85):
            rx = int(top_x + (bot_x - top_x) * t)
            ry = int(top_y + (bot_y - top_y) * t)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_dark"], (rx, ry), 3)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_mid"], (rx, ry), 2)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["gold_light"], (rx - 1, ry - 1), 1)

        # Staff head - crystal cluster
        head_x, head_y = top_x, top_y - 4

        # Cast glow
        glow_size = 8
        if casting:
            glow_size = 8 + int(math.sin(progress * math.pi) * 10)

        # Backing glow
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 100), (head_x, head_y), glow_size + 4)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 160), (head_x, head_y), glow_size)

        # Metal claws holding the crystal
        for offset_a in (-1.2, -0.4, 0.4, 1.2):
            cx1 = head_x + int(math.cos(math.pi / 2 + offset_a) * 3)
            cy1 = head_y + int(math.sin(math.pi / 2 + offset_a) * 3)
            cx2 = head_x + int(math.cos(math.pi / 2 + offset_a) * 8)
            cy2 = head_y + int(math.sin(math.pi / 2 + offset_a) * 8) - 4
            _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_darkest"], (cx1, cy1), (cx2, cy2), 3)
            _NS_varkul._aaline(surface, _NS_varkul.PALETTE["armor_mid"], (cx1, cy1), (cx2, cy2), 1)

        # Main ice crystal
        _NS_varkul._draw_ice_shard(surface, head_x, head_y, 8, -math.pi / 2,
                        _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                        _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])
        # Center gem
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_dark"], (head_x, head_y - 2), 4)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (head_x, head_y - 2), int(3 * pulse) + 1)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (head_x, head_y - 3), 2)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (head_x, head_y - 3), 1)


    def _draw_skull_head(surface, cx, cy, phase):
        """Lich skull head with horned crown."""
        # Shadow
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow_deep"], (cx + 2, cy + 2), 12)

        # Skull main
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_dark"], (cx, cy), 11)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_mid"], (cx - 1, cy - 1), 9)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_light"], (cx - 2, cy - 3), 5)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_shine"], (cx - 3, cy - 4), 2)

        # Skull cheekbones angular
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["bone_dark"], [
            (cx - 10, cy + 2), (cx - 7, cy + 8), (cx - 4, cy + 6)
        ])
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["bone_dark"], [
            (cx + 10, cy + 2), (cx + 7, cy + 8), (cx + 4, cy + 6)
        ])

        # Eye sockets
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow"], (cx - 4, cy - 1), 3)
        _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["shadow"], (cx + 4, cy - 1), 3)

        # Glowing blue eyes
        eye_pulse = math.sin(phase * 1.8) * 0.3 + 0.7
        er = max(1, int(2 * eye_pulse))
        for eox in (-4, 4):
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["eye_dark"], 200), (cx + eox, cy - 1), 3)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_mid"], (cx + eox, cy - 1), er + 1)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_light"], (cx + eox, cy - 1), er)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["eye_hot"], (cx + eox, cy - 1), max(1, er - 1))

        # Eye light streaks/aura
        for eox in (-4, 4):
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["eye_light"], int(80 * eye_pulse)),
                      (cx + eox, cy - 1), 5)

        # Nasal cavity
        _NS_varkul._poly(surface, _NS_varkul.PALETTE["shadow"], [
            (cx - 1, cy + 2), (cx + 1, cy + 2),
            (cx + 2, cy + 5), (cx - 2, cy + 5),
        ])

        # Teeth / jaw
        _NS_varkul._rect(surface, _NS_varkul.PALETTE["bone_dark"], (cx - 5, cy + 6, 10, 4))
        for i in range(5):
            tx = cx - 4 + i * 2
            _NS_varkul._rect(surface, _NS_varkul.PALETTE["bone_light"], (tx, cy + 6, 1, 3))
        # Jaw shadow line
        _NS_varkul._aaline(surface, _NS_varkul.PALETTE["shadow"], (cx - 5, cy + 6), (cx + 5, cy + 6), 1)

        # Horned crown - big antler-like horns
        for side in (-1, 1):
            # Main horn curving outward
            base_x = cx + side * 6
            base_y = cy - 8

            # Base of horn
            _NS_varkul._poly(surface, _NS_varkul.PALETTE["bone_dark"], [
                (base_x - 2, base_y),
                (base_x + 2, base_y),
                (base_x + side * 4, base_y - 4),
                (base_x + side * 2, base_y - 5),
            ])

            # Curving horn segments
            for i, (dx, dy, w) in enumerate([
                (side * 4, -6, 3),
                (side * 7, -10, 2),
                (side * 10, -14, 2),
            ]):
                hx = base_x + dx
                hy = base_y + dy
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_dark"], (hx, hy), w)
                _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["bone_mid"], (hx - 1, hy - 1), w - 1)

            # Horn tip
            tip_x = base_x + side * 12
            tip_y = base_y - 16
            _NS_varkul._poly(surface, _NS_varkul.PALETTE["bone_light"], [
                (base_x + side * 10, base_y - 13),
                (base_x + side * 12, base_y - 13),
                (tip_x, tip_y),
            ])

            # Ice crystal at horn base
            _NS_varkul._draw_ice_shard(surface, base_x + side * 3, base_y + 1, 4,
                            -math.pi / 2 + side * 0.3,
                            _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                            _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])

        # Central crown ice crystal
        _NS_varkul._draw_ice_shard(surface, cx, cy - 12, 6, -math.pi / 2,
                        _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                        _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])

        # Small side crystals on top
        _NS_varkul._draw_ice_shard(surface, cx - 3, cy - 10, 4, -math.pi / 2 - 0.3,
                        _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                        _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])
        _NS_varkul._draw_ice_shard(surface, cx + 3, cy - 10, 4, -math.pi / 2 + 0.3,
                        _NS_varkul.PALETTE["ice_dark"], _NS_varkul.PALETTE["ice_mid"],
                        _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])


    def _draw_body_particles(surface, cx, cy, phase):
        """Floating frost particles around body."""
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 28 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(120 + math.sin(phase + i * 0.7) * 60)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha), (px, py), 2)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], alpha), (px, py), 1)

        # Falling snowflakes
        for i in range(4):
            t = (phase * 0.3 + i * 0.25) % 1.0
            fx = cx - 30 + i * 20 + int(math.sin(phase + i) * 5)
            fy = cy - 40 + int(t * 90)
            alpha = int(200 * (1 - t))
            _NS_varkul._draw_snowflake(surface, fx, fy, 3,
                            phase + i, (*_NS_varkul.PALETTE["ice_bright"], alpha))


    # ===================================================================
    # FLOATING EFFECTS (replaces legs)
    # ===================================================================
    def _draw_floating_mist(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Frost mist beneath floating Lich."""
        NS = _NS_varkul
        if NS._mist_cache is None:
            mist = pygame.Surface((120, 40), pygame.SRCALPHA)
            for radius in range(30, 3, -4):
                alpha = int((30 - radius) * 2.8)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*NS.PALETTE["ice_dark"], min(255, alpha)),
                        (60 - radius * 2, 20 - radius // 3,
                         radius * 4, max(3, radius // 2)),
                    )
            NS._mist_cache = mist
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        spr = NS._mist_cache
        spr.set_alpha(int(255 * min(1.0, pulse * strength)))
        surface.blit(spr, (cx - 60, cy - 10))

        # Rising frost wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], alpha), (sx, sy), 5)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha), (sx, sy - 2), 3)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting frost crystals
        for i in range(4):
            angle = phase * 0.9 + i * math.pi * 2 / 4
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (sx, sy), 3)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (sx, sy), 2)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y, lift=0):
        """Ground shadow beneath floating entity (cache + reaktif saat lift)."""
        NS = _NS_varkul
        if NS._shadow_cache is None:
            shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
            for radius in range(10, 0, -1):
                alpha = max(0, (10 - radius) * 16)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
                )
            pygame.draw.ellipse(shadow, (*NS.PALETTE["ice_dark"], 40), (8, 4, 84, 10))
            NS._shadow_cache = shadow
        spr = NS._shadow_cache
        w, h = spr.get_size()
        if lift:
            k = max(0.12, 1.0 - lift * 0.05)
            w = max(6, int(w * k))
            h = max(2, int(h * k))
            spr = pygame.transform.smoothscale(spr, (w, h))
        bx = x - w // 2
        by = (y + 10) - h          # dasar tetap menapak di y+10
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))


    def _draw_frost_aura(surface, x, y, phase):
        """Large background frost aura (basis di-cache, denyut via alpha)."""
        NS = _NS_varkul
        if NS._aura_cache is None:
            aura = pygame.Surface((180, 160), pygame.SRCALPHA)
            for radius in range(70, 5, -4):
                alpha = int((70 - radius) * 1.2)
                if alpha > 0:
                    NS._aacircle(aura, (*NS.PALETTE["ice_darkest"], min(255, alpha)),
                                 (90, 80), radius)
            NS._aura_cache = aura
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        spr = NS._aura_cache
        spr.set_alpha(int(255 * max(0.2, min(1.0, pulse))))
        surface.blit(spr, (x - 90, y - 80))


    def _draw_ice_platform(surface, x, y, phase, skill):
        """Ice circle / snowflake pattern on the ground (basis di-cache)."""
        NS = _NS_varkul
        if NS._ground_cache is None:
            ring = pygame.Surface((130, 44), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_dark"], 150),
                                (5, 10, 120, 24), 3)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_mid"], 180),
                                (20, 14, 90, 16), 2)
            for i in range(8):
                angle = i * math.pi / 4
                x1 = 65 + int(math.cos(angle) * 20)
                y1 = 22 + int(math.sin(angle) * 4)
                x2 = 65 + int(math.cos(angle) * 55)
                y2 = 22 + int(math.sin(angle) * 10)
                pygame.draw.line(ring, (*NS.PALETTE["ice_light"], 170),
                                 (x1, y1), (x2, y2), 1)
            for angle_deg in (0, 90, 180, 270):
                angle = math.radians(angle_deg)
                sx = 65 + int(math.cos(angle) * 50)
                sy = 22 + int(math.sin(angle) * 9)
                pygame.draw.circle(ring, (*NS.PALETTE["ice_bright"], 200), (sx, sy), 2)
            NS._ground_cache = ring
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        surface.blit(NS._ground_cache, (x - 65, y - 22))
        if skill:
            pygame.draw.ellipse(surface, (*NS.PALETTE["ice_bright"], int(80 * pulse)),
                                (x - 50, y - 14, 100, 28), 1)


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash yang MENGIKUTI ark crystal staff saat swing."""
        if progress < 0.30 or progress > 0.62:
            return
        t = (progress - 0.30) / 0.32
        intensity = math.sin(t * math.pi)

        # Posisi crystal staff saat ini (ark yang sama dengan renderer)
        theta, lift = _NS_varkul._staff_arc(progress)
        hand_x = x - facing * (23 - 6 * lift)
        hand_y = y + 8 - 30 * lift
        flash_x = hand_x + facing * math.sin(theta) * 50
        flash_y = hand_y - math.cos(theta) * 50

        alpha = int(180 * intensity)
        radius = int(5 + intensity * 8)

        # flash: dua cincin tegas + bintang 4 arah (bukan bola lembut)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha // 2),
                  (int(flash_x), int(flash_y)), radius + 3)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha),
                  (int(flash_x), int(flash_y)), radius)
        star = radius + 4
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            _NS_varkul._aaline(surface,
                               (*_NS_varkul.PALETTE["ice_white"], min(255, alpha)),
                               (int(flash_x), int(flash_y)),
                               (int(flash_x + dx * star),
                                int(flash_y + dy * star)), 2)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], min(255, alpha)),
                  (int(flash_x), int(flash_y)), 2)

        # Snowflake burst mengikuti crystal
        for i in range(5):
            angle = progress * 6 + i * math.pi * 2 / 5
            ex = flash_x + int(math.cos(angle) * radius * 1.5)
            ey = flash_y + int(math.sin(angle) * radius * 1.5)
            _NS_varkul._draw_snowflake(surface, ex, ey, 3, progress,
                            (*_NS_varkul.PALETTE["ice_bright"], alpha))


    # ===================================================================
    # SKILL Q: FROST BLAST
    # ===================================================================
    def _draw_frost_blast_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_varkul._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 50))
        # Ground warning circle at impact
        radius = int(20 + progress * 40)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 100), (tx, ty), radius, 2)
        _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 80), (tx, ty), radius + 5, 1)


    def _draw_frost_blast(surface, boss, x, y, timer, phase):
        tx, ty = _NS_varkul._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 50))

        start_x = x - 20 * boss.direction
        start_y = y - 20

        if progress < 0.4:
            # Traveling beam of frost
            travel_t = progress / 0.4
            cur_x = start_x + (tx - start_x) * travel_t
            cur_y = start_y + (ty - start_y) * travel_t

            # Comet trail
            for i in range(8):
                t = travel_t - i * 0.05
                if t <= 0:
                    continue
                px = int(start_x + (tx - start_x) * t)
                py = int(start_y + (ty - start_y) * t)
                size = max(2, 10 - i)
                alpha = max(0, 200 - i * 25)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], alpha), (px, py), size + 4)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha), (px, py), size + 2)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], alpha), (px, py), size)
                _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], alpha), (px, py), max(1, size - 3))

            # Head of comet
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_dark"], (int(cur_x), int(cur_y)), 14)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (int(cur_x), int(cur_y)), 10)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (int(cur_x), int(cur_y)), 7)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (int(cur_x), int(cur_y)), 4)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (int(cur_x), int(cur_y)), 2)

            # Ice shards around comet
            for i in range(5):
                angle = phase * 4 + i * math.pi * 2 / 5
                _NS_varkul._draw_ice_shard(surface, int(cur_x), int(cur_y), 8, angle,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])
        else:
            # Impact explosion
            exp_t = (progress - 0.4) / 0.6
            exp_r = int(40 * exp_t)
            alpha = int(255 * (1 - exp_t))

            # Explosion rings
            for i in range(3):
                r = exp_r - i * 5
                if r > 0:
                    _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], alpha),
                              (tx, ty), r, 2)
                    _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha),
                              (tx, ty), max(1, r - 3), 1)

            # Radiating ice shards
            for i in range(12):
                angle = i * math.pi / 6
                dist = 15 + int(exp_r * 0.8)
                sx = tx + int(math.cos(angle) * dist)
                sy = ty + int(math.sin(angle) * dist * 0.7)
                _NS_varkul._draw_ice_shard(surface, sx, sy, 8 + int(math.sin(phase) * 2),
                                angle,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])

            # Central flash
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], alpha), (tx, ty), 10)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_bright"], alpha), (tx, ty), 15)


    # ===================================================================
    # SKILL W: FROSTBITE (encase target in ice)
    # ===================================================================
    def _draw_frostbite(surface, boss, x, y, timer, phase):
        tx, ty = _NS_varkul._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 60))

        if progress < 0.3:
            # Frost projectile flying to target
            t = progress / 0.3
            cur_x = x - 20 * boss.direction + (tx - (x - 20 * boss.direction)) * t
            cur_y = y - 20 + (ty - (y - 20)) * t

            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 150),
                      (int(cur_x), int(cur_y)), 10)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_mid"], (int(cur_x), int(cur_y)), 7)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (int(cur_x), int(cur_y)), 5)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (int(cur_x), int(cur_y)), 2)
        else:
            # Ice prison forming
            t = (progress - 0.3) / 0.7
            size = int(20 + t * 15)

            # Ice block base
            _NS_varkul._poly(surface, (*_NS_varkul.PALETTE["ice_dark"], 200), [
                (tx - size, ty + size),
                (tx - size + 5, ty - size),
                (tx + size - 5, ty - size),
                (tx + size, ty + size),
            ])
            _NS_varkul._poly(surface, (*_NS_varkul.PALETTE["ice_mid"], 220), [
                (tx - size + 3, ty + size - 3),
                (tx - size + 7, ty - size + 3),
                (tx + size - 7, ty - size + 3),
                (tx + size - 3, ty + size - 3),
            ])
            _NS_varkul._poly(surface, (*_NS_varkul.PALETTE["ice_light"], 180), [
                (tx - size + 6, ty + size - 6),
                (tx - size + 10, ty - size + 6),
                (tx + size - 10, ty - size + 6),
                (tx + size - 6, ty + size - 6),
            ])

            # Ice shards around
            for i in range(8):
                angle = phase * 0.5 + i * math.pi / 4
                sx = tx + int(math.cos(angle) * size)
                sy = ty + int(math.sin(angle) * size * 0.7) - 5
                _NS_varkul._draw_ice_shard(surface, sx, sy,
                                6 + int(math.sin(phase + i) * 2),
                                angle - math.pi / 2,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])

            # Shine on top
            _NS_varkul._aaline(surface, _NS_varkul.PALETTE["ice_hot"],
                    (tx - size + 8, ty - size + 4),
                    (tx - 2, ty - size + 4), 2)


    # ===================================================================
    # SKILL E: SACRIFICE (drain circle)
    # ===================================================================
    def _draw_sacrifice_circle(surface, boss, x, y, timer, phase):
        """Pentagram circle on ground."""
        progress = max(0.0, min(1.0, 1 - timer / 50))
        radius = int(35 + progress * 25)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        circle = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        # Pentagram base circle
        pygame.draw.ellipse(circle, (*_NS_varkul.PALETTE["ice_dark"], int(180 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(circle, (*_NS_varkul.PALETTE["ice_mid"], int(150 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        # Pentagram star
        star_points = []
        for i in range(5):
            a = -math.pi / 2 + i * math.pi * 2 / 5 + phase * 0.1
            px = cx + int(math.cos(a) * (radius - 8))
            py = cy + int(math.sin(a) * (radius // 2 - 4))
            star_points.append((px, py))
        for i in range(5):
            p1 = star_points[i]
            p2 = star_points[(i + 2) % 5]
            pygame.draw.line(circle, (*_NS_varkul.PALETTE["ice_light"], int(200 * pulse)),
                             p1, p2, 2)

        surface.blit(circle, (x - cx, y + 30 - cy))


    def _draw_sacrifice_foreground(surface, boss, x, y, timer, phase):
        """Rising soul energy from ground to Lich (lifecycle ikut timer AI)."""
        duration = 50
        # Guard lifecycle: jangan menggambar di luar durasi skill AI.
        if timer <= 0 or timer > duration:
            return
        # Rising skull energy
        for i in range(6):
            t = (phase * 0.4 + i * 0.15) % 1.0
            offset_x = math.sin(phase + i * 0.7) * 15
            rx = x + int(offset_x)
            ry = y + 35 - int(t * 55)
            alpha = int(200 * (1 - t))
            size = 4 + int(t * 3)

            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], alpha), (rx, ry), size + 2)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_light"], alpha), (rx, ry), size)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_white"], alpha), (rx, ry), max(1, size - 2))


    # ===================================================================
    # SKILL R: CHAIN FROST
    # ===================================================================
    def _draw_chain_frost_ground(surface, boss, x, y, timer, phase):
        """Warning glow before launch."""
        progress = max(0.0, min(1.0, 1 - timer / 80))
        if progress < 0.3:
            # Charge up
            radius = int(15 + progress * 30)
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], int(150 * pulse)),
                      (x, y - 20), radius, 2)


    def _draw_chain_frost(surface, boss, x, y, timer, phase):
        """Draw chain frost orb + charging."""
        progress = max(0.0, min(1.0, 1 - timer / 80))

        if progress < 0.35:
            # Charging in hand
            charge = progress / 0.35
            cx, cy = x + boss.direction * 18, y - 15
            r = int(6 + charge * 10)

            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_dark"], 150), (cx, cy), r + 6)
            _NS_varkul._aacircle(surface, (*_NS_varkul.PALETTE["ice_mid"], 200), (cx, cy), r + 2)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_light"], (cx, cy), r)
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_bright"], (cx, cy), max(1, r - 3))
            _NS_varkul._aacircle(surface, _NS_varkul.PALETTE["ice_white"], (cx, cy), max(1, r - 5))

            # Ice shards forming
            for i in range(6):
                angle = phase * 4 + i * math.pi / 3
                _NS_varkul._draw_ice_shard(surface, cx, cy, int(6 + charge * 4), angle,
                                _NS_varkul.PALETTE["ice_darkest"], _NS_varkul.PALETTE["ice_dark"],
                                _NS_varkul.PALETTE["ice_light"], _NS_varkul.PALETTE["ice_white"])
        elif progress < 0.45 and not getattr(boss, "_vk_chain_launched", False):
            # Launch
            tx, ty = _NS_varkul._target_position(boss, x, y)
            if not hasattr(boss, "_vk_chain_orbs"):
                boss._vk_chain_orbs = []
            boss._vk_chain_orbs.append(
                _NS_varkul.ChainFrostOrb(x + boss.direction * 18, y - 15, tx, ty, bounces=4)
            )
            boss._vk_chain_launched = True

        if progress > 0.9:
            boss._vk_chain_launched = False


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_varkul.draw_varkul(surface, boss, x, y)


# ====================================================================
# XERATHIS
# ====================================================================
class _NS_xerathis:
    """Namespace xerathis - isi asli tidak diubah."""

    # ── ORIGINAL-MAX cache (piksel-identik, dibangun lazy) ──────────
    _body_buf = None
    _flash_buf = None
    _record_shadow = None
    _shadow_cache = None
    _aura_cache = None
    _ground_cache = None
    _mist_cache = None

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Crystal Maiden inspired
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin
        "skin_darkest":   (150, 105,  85),
        "skin_dark":      (200, 150, 120),
        "skin_mid":       (235, 195, 165),
        "skin_light":     (250, 220, 195),
        "skin_high":      (255, 240, 220),

        # Hair (blonde)
        "hair_darkest":   (105,  75,  30),
        "hair_dark":      (165, 125,  55),
        "hair_mid":       (215, 175,  95),
        "hair_light":     (245, 215, 145),
        "hair_shine":     (255, 240, 195),

        # Robe – blue/purple
        "robe_darkest":   (18,  22,  58),
        "robe_dark":      (35,  50, 110),
        "robe_mid":       (65,  90, 175),
        "robe_light":     (110, 140, 220),
        "robe_high":      (160, 190, 245),

        # Cloak – deep purple
        "cloak_darkest":  (22,  15,  50),
        "cloak_dark":     (48,  32,  95),
        "cloak_mid":      (80,  55, 145),
        "cloak_light":    (125, 95, 195),

        # Fur trim (white)
        "fur_dark":       (155, 175, 200),
        "fur_mid":        (210, 225, 240),
        "fur_light":      (240, 248, 255),

        # Gold
        "gold_dark":      (95,  70,  20),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 195, 90),
        "gold_shine":     (255, 235, 165),

        # Ice / crystal
        "ice_darkest":    (10,  30,  75),
        "ice_dark":       (25,  70, 145),
        "ice_mid":        (70, 140, 225),
        "ice_light":      (140, 200, 250),
        "ice_bright":     (195, 230, 255),
        "ice_hot":        (225, 245, 255),
        "ice_white":      (245, 252, 255),

        # Eye
        "eye_white":      (240, 248, 255),
        "eye_iris":       (85, 145, 220),
        "eye_iris_light": (150, 200, 255),
        "eye_pupil":      (15,  30,  60),

        # Lips
        "lips_dark":      (170,  75,  85),
        "lips_mid":       (215, 115, 125),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (4,   6,   15),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_xerathis._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_xerathis.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_xerathis._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width
            min_y = min(sy, ey) - width
            w = abs(ex - sx) + width * 4 + 4
            h = abs(ey - sy) + width * 4 + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color,
                             (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_xerathis._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)


    def _ellipse(surface, color, rect, width=0):
        color = _NS_xerathis._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, rw, rh), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3], rect, width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_xerathis._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, rw, rh), border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3], rect, border_radius=border_radius)


    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # DENGAN kompensasi scale. Hero di-render ke canvas
            # offscreen lalu di-scale saat blit (heroes/__init__.py),
            # jadi titik canvas harus = (delta dunia)/scale supaya
            # beam/proyektil mendarat TEPAT di target setelah blit.
            # Boss yang digambar langsung di layar tidak terpengaruh
            # (scale = 1).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Ice / crystal visual helpers
    # ---------------------------------------------------------------------------
    def _draw_ice_shard(surface, cx, cy, size, angle, color_dark, color_mid,
                        color_light, color_hot):
        """Draw a single sharp ice crystal shard."""
        ca, sa = math.cos(angle), math.sin(angle)
        tip_x = cx + ca * size
        tip_y = cy + sa * size
        base_l_x = cx + math.cos(angle + 2.4) * size * 0.35
        base_l_y = cy + math.sin(angle + 2.4) * size * 0.35
        base_r_x = cx + math.cos(angle - 2.4) * size * 0.35
        base_r_y = cy + math.sin(angle - 2.4) * size * 0.35

        _NS_xerathis._poly(surface, color_dark, [
            (tip_x, tip_y), (base_l_x, base_l_y), (base_r_x, base_r_y)
        ])
        _NS_xerathis._poly(surface, color_mid, [
            (tip_x, tip_y),
            ((base_l_x + cx) / 2, (base_l_y + cy) / 2),
            ((base_r_x + cx) / 2, (base_r_y + cy) / 2),
        ])
        _NS_xerathis._aaline(surface, color_light, (cx, cy), (tip_x, tip_y), 1)
        _NS_xerathis._aacircle(surface, color_hot, (int(tip_x), int(tip_y)), 1)


    def _draw_snowflake(surface, cx, cy, size, phase, color=None):
        """Small rotating snowflake."""
        if color is None:
            color = _NS_xerathis.PALETTE["ice_bright"]
        for i in range(6):
            angle = phase * 0.5 + i * math.pi / 3
            x1 = cx + int(math.cos(angle) * size)
            y1 = cy + int(math.sin(angle) * size)
            _NS_xerathis._aaline(surface, color, (cx, cy), (x1, y1), 1)
            bx = cx + int(math.cos(angle) * size * 0.6)
            by = cy + int(math.sin(angle) * size * 0.6)
            for b in (-1, 1):
                ba = angle + b * 0.5
                ex = bx + int(math.cos(ba) * size * 0.3)
                ey = by + int(math.sin(ba) * size * 0.3)
                _NS_xerathis._aaline(surface, color, (bx, by), (ex, ey), 1)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_hot"], (cx, cy), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM - Ice Shard Arrow
    # ---------------------------------------------------------------------------
    class IceShardProjectile:
        """Ice shard arrow projectile."""
        def __init__(self, sx, sy, tx, ty, speed=6.5):
            self.x = float(sx)
            self.y = float(sy)
            self.tx = float(tx)
            self.ty = float(ty)
            self.speed = speed
            self.alive = True
            self.age = 0
            self.trail = []
            dx = tx - sx
            dy = ty - sy
            self.angle = math.atan2(dy, dx)

        def update(self):
            if not self.alive:
                return
            self.age += 1
            dx = self.tx - self.x
            dy = self.ty - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 10:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return
            # Trail - frost mist
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 15)
                r = max(1, 5 - (len(self.trail) - i))
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], alpha), (tx, ty), r + 2)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha // 2), (tx, ty), r)

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Glow
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], 100), (px, py), 12)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], 150), (px, py), 8)

                # Ice arrow body - shard shape
                ca, sa = math.cos(self.angle), math.sin(self.angle)
                length = 14
                width = 4
                tip_x = px + ca * length
                tip_y = py + sa * length
                tail_x = px - ca * length * 0.7
                tail_y = py - sa * length * 0.7
                # Perpendicular offsets
                perp_x = -sa * width
                perp_y = ca * width

                # Dark outline
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_darkest"], [
                    (tip_x, tip_y),
                    (px + perp_x, py + perp_y),
                    (tail_x, tail_y),
                    (px - perp_x, py - perp_y),
                ])
                # Mid layer
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_mid"], [
                    (tip_x - ca * 1, tip_y - sa * 1),
                    (px + perp_x * 0.7, py + perp_y * 0.7),
                    (tail_x + ca * 1, tail_y + sa * 1),
                    (px - perp_x * 0.7, py - perp_y * 0.7),
                ])
                # Light layer
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_light"], [
                    (tip_x - ca * 2, tip_y - sa * 2),
                    (px + perp_x * 0.4, py + perp_y * 0.4),
                    (tail_x + ca * 2, tail_y + sa * 2),
                    (px - perp_x * 0.4, py - perp_y * 0.4),
                ])
                # Bright core
                _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_bright"],
                        (px - ca * length * 0.5, py - sa * length * 0.5),
                        (tip_x, tip_y), 2)
                _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_white"],
                        (px, py), (tip_x - ca * 2, tip_y - sa * 2), 1)
                # Tip sparkle
                _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (int(tip_x), int(tip_y)), 2)


    # ---------------------------------------------------------------------------
    # State management helpers
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_xr_last_x"):
            boss._xr_last_x = boss.x
            boss._xr_last_y = boss.y
            return False
        dx = abs(boss.x - boss._xr_last_x)
        dy = abs(boss.y - boss._xr_last_y)
        boss._xr_last_x = boss.x
        boss._xr_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        """Backward-compatible alias ke controller V2."""
        return _NS_xerathis._update_xerathis_anim(
            boss, _NS_xerathis._detect_moving(boss))


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_xr_projectiles"):
            boss._xr_projectiles = []
        for proj in boss._xr_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._xr_projectiles = [p for p in boss._xr_projectiles if p.alive or p.age < 8]


    def _spawn_projectile(boss, x, y):
        if not hasattr(boss, "_xr_projectiles"):
            boss._xr_projectiles = []
        tx, ty = _NS_xerathis._target_position(boss, x, y)
        facing = getattr(boss, "direction", 1)
        # Staff tip position (front-facing side, raised up)
        sx = x + 26 * facing
        sy = y - 18
        boss._xr_projectiles.append(_NS_xerathis.IceShardProjectile(sx, sy, tx, ty, speed=6.5))


    # ===================================================================
    # V2 ANIMATION CONTROLLER + LIVE FX BRIDGE
    # ===================================================================

    #: Fase serangan (fraksi 0..1 dari durasi serangan).
    ATTACK_PHASES = (
        ("ANTICIPATION", 0.00, 0.16),
        ("WINDUP",       0.16, 0.32),
        ("SWING",        0.32, 0.50),
        ("IMPACT",       0.50, 0.64),
        ("FOLLOW",       0.64, 0.82),
        ("RECOVERY",     0.82, 1.00),
    )

    #: Jendela hit aktif (dipakai debug & game feel).
    ATTACK_ACTIVE_WINDOW = (0.38, 0.64)
    ATTACK_IMPACT_FRAME = 0.52

    #: Prioritas state. Angka besar menang; DEATH mengunci.
    ANIM_STATES = {
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

    #: Aktifkan hitbox/hurtbox/jangkauan/state di arena.
    DEBUG_CHARACTER = False

    #: Modul FX layar (diisi malas). False = percobaan gagal -> canvas.
    _LIVE_MOD = None

    def attack_phases_order():
        return tuple(name for name, _a, _b in _NS_xerathis.ATTACK_PHASES)

    def attack_phase(progress):
        p = max(0.0, min(1.0, float(progress)))
        for name, a, b in _NS_xerathis.ATTACK_PHASES:
            if a <= p < b:
                return name
        return "RECOVERY"

    def _live_module():
        """Muat ``heroes.xerathis_fx`` sekali; None kalau tidak tersedia."""
        NS = _NS_xerathis
        if NS._LIVE_MOD is None:
            try:
                from heroes import xerathis_fx as mod
                NS._LIVE_MOD = mod if getattr(mod, "XERATHIS_FX_ENABLED",
                                              True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    def live_fx_ready():
        return _NS_xerathis._live_module() is not None

    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Lapisan hidup untuk unit ini.

        Return ``(mod, owned)``. ``want_draw`` True pada jalur BOSS (draw
        dipanggil tiap frame tanpa cache sprite).
        """
        NS = _NS_xerathis
        if portrait:
            return None, False
        mod = NS._live_module()
        if mod is None:
            return None, False
        try:
            if want_draw:
                mod.draw_ground_layer(surface, boss, x, y)
            else:
                mod.attach(boss)
        except Exception:
            return None, False
        try:
            owned = bool(mod.owns(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    def _update_xerathis_anim(boss, moving=False):
        """ANIMATION CONTROLLER Xerathis - state, fase, timing, delta-time.

        Satu-satunya sumber kebenaran untuk SEMUA state karakter; lapisan
        hidup (heroes/xerathis_fx) serta alat uji membacanya dari sini.
        """
        G = _NS_xerathis

        # ── delta time nyata (dipakai FX & transisi state) ──────────
        try:
            now = pygame.time.get_ticks()
        except Exception:                      # pragma: no cover
            now = 0
        prev_ms = getattr(boss, "_xr_last_ms", None)
        if prev_ms is None:
            dt = 1.0 / 60.0
        else:
            dt = (now - prev_ms) / 1000.0
            if dt <= 0.0 or dt > 0.05:
                dt = 1.0 / 60.0
        boss._xr_last_ms = now
        boss._xr_dt = dt

        # ── timeline serangan ───────────────────────────────────────
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 59)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_xr_previous_timer", 0))
        active = bool(getattr(boss, "_xr_attack_active", False))

        triggered = timer >= cooldown - 1 and previous <= 1
        if triggered:
            boss._xr_attack_active = True
            boss._xr_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._xr_attack_frame = int(getattr(boss, "_xr_attack_frame",
                                                0)) + 1
        elif timer <= 0 and active:
            # serangan manual (alat audit / probe): majukan sampai selesai
            boss._xr_attack_frame = int(getattr(boss, "_xr_attack_frame",
                                                0)) + 1
            if int(getattr(boss, "_xr_attack_frame", 0)) > cooldown:
                boss._xr_attack_active = False
                boss._xr_attack_frame = 0
                active = False

        boss._xr_previous_timer = timer
        if active:
            prog = min(1.0, int(getattr(boss, "_xr_attack_frame", 0))
                       / max(1, cooldown))
        else:
            prog = 0.0
        boss._xr_attack_progress = prog
        boss._xr_attack_raw = prog
        boss._xr_attack_phase = G.attack_phase(prog) if active else "NONE"
        boss._xr_hit_active = active and (G.ATTACK_ACTIVE_WINDOW[0] <= prog <
                                          G.ATTACK_ACTIVE_WINDOW[1])
        boss._xr_impact_frame = active and abs(prog - G.ATTACK_IMPACT_FRAME) < 0.025

        # ── hurt / hit flash ────────────────────────────────────────
        hurt = int(getattr(boss, "_xr_hurt_frames", 0) or 0)
        if hurt > 0:
            hurt -= 1
        if int(getattr(boss, "hurt_flash_timer", 0) or 0) > 0:
            hurt = max(hurt, 7)
        boss._xr_hurt_frames = hurt

        # ── resolve state ───────────────────────────────────────────
        if not getattr(boss, "alive", True):
            state = "DEATH"
        elif hurt > 0:
            state = "HURT"
        elif getattr(boss, "active_skill", None) is not None:
            state = ("SPECIAL" if getattr(boss, "active_skill", None) == "r"
                     else "SKILL")
        elif active:
            ph = boss._xr_attack_phase
            if ph in ("ANTICIPATION", "WINDUP"):
                state = "CHARGE"
            elif ph in ("SWING", "IMPACT"):
                state = "SWING"
            else:
                state = "ATTACK"
        elif moving:
            state = ("RUN" if float(getattr(boss, "speed", 1.0)) >= 2.2
                     else "WALK")
        else:
            state = "IDLE"

        old = getattr(boss, "_xr_state", None)
        boss._xr_state_prev = old or state
        if old != state:
            boss._xr_state_time = 0.0
        else:
            boss._xr_state_time = (float(getattr(boss, "_xr_state_time", 0.0))
                                   + dt)
        boss._xr_state = state

    def _resolve_pose(boss, moving=False):
        """(action, phase, attack_progress) untuk renderer & FX."""
        skill = getattr(boss, "active_skill", None)
        active = bool(getattr(boss, "_xr_attack_active", False))
        if skill:
            action = "cast"
        elif active:
            action = "attack"
        elif moving:
            action = "walk"
        else:
            action = "idle"
        phase = float(getattr(boss, "pulse", 0.0) or 0.0)
        ap = (float(getattr(boss, "_xr_attack_progress", 0.0) or 0.0)
              if active else 0.0)
        return action, phase, ap

    def _staff_tip_screen(boss, x, y):
        """Titik kepala kristal staff untuk FX (semua FX memakai modul
        hidup, yang membacanya dari ``_resolve_pose``)."""
        action = getattr(boss, "_xr_pose_action", "idle")
        facing = 1 if getattr(boss, "direction", 1) >= 0 else -1
        if action == "attack":
            t = float(getattr(boss, "_xr_attack_progress", 0.0) or 0.0)
            ext = 1.0 if t < 0.5 else 0.55
            return (x + facing * (24 + ext * 10), y - 18)
        return (x + facing * 24, y - 54)

    def _draw_xerathis_debug(surface, boss, x, y):
        """Overlay DEBUG_CHARACTER: hitbox, state, frame, FPS."""
        NS = _NS_xerathis
        import pygame as _pg
        r = max(6, int(getattr(boss, "radius", 16)))
        _pg.draw.rect(surface, (80, 170, 255, 150),
                      _pg.Rect(int(x) - r, int(y) - r - 8, r * 2, r * 2), 1)
        rng = max(10, int(getattr(boss, "range", 200) * 0.7))
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        _pg.draw.line(surface, (255, 210, 60, 150), (int(x), int(y)),
                      (int(x + rng * f), int(y)), 1)
        _pg.draw.rect(surface, (255, 210, 60, 110),
                      _pg.Rect(int(x + rng * f) - 5, int(y) - 7, 10, 14), 1)
        hb = None
        if getattr(boss, "_xr_hit_active", False):
            reach = int(rng)
            top = int(y - 38)
            left = int(x) if f > 0 else int(x) - reach
            hb = _pg.Rect(left, top, max(8, reach), max(10, 72))
            _pg.draw.rect(surface, (255, 70, 70, 190), hb, 2)
            _pg.draw.rect(surface, (255, 70, 70, 60), hb)
        state = getattr(boss, "_xr_state", "IDLE")
        ph = getattr(boss, "_xr_attack_phase", "NONE")
        frames = int(getattr(boss, "_xr_attack_frame", 0))
        prog = float(getattr(boss, "_xr_attack_progress", 0.0))
        hurt = int(getattr(boss, "_xr_hurt_frames", 0))
        fps = getattr(boss, "_xr_fps", 60.0)
        dtv = float(getattr(boss, "_xr_dt", 1.0 / 60.0))
        inst = 1.0 / dtv if dtv > 0 else 60.0
        fps = fps + (inst - fps) * 0.1
        boss._xr_fps = fps
        lines = [
            f"XERATHIS {state} {ph}",
            f"frame {frames} t={prog:.2f} hurt={hurt}",
            f"hit={'Y' if hb else 'N'} fps={fps:.0f}",
            f"dt={dtv:.4f} proj={len(getattr(boss, '_xr_projectiles', []))}",
        ]
        font = None
        try:
            from _render import get_font
            font = get_font(14)
        except Exception:
            pass
        if font is None:
            return
        px, py = int(x) - 80, int(y) + 36
        for i, line in enumerate(lines):
            s = font.render(line, True, (220, 255, 230))
            surface.blit(s, (px, py + i * 14))

    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_xerathis(surface, boss, x, y):
        """Entry point Boss.draw() sekaligus jalur hero-lane.

        Urutan lapisan: GROUND -> SHADOW -> BODY/ARMOR/HEAD -> WEAPON ->
        ATTACK TRAIL -> PROJECTILE -> FRONT PARTICLES -> SKILL FX ->
        IMPACT FX -> DEBUG. Trail, proyektil, impact, hit-stop & shake
        hidup di ``heroes/xerathis_fx.py`` (lapisan layar 1:1).
        """
        NS = _NS_xerathis
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = NS._detect_moving(boss)
        NS._update_xerathis_anim(boss, moving)
        action, phase, ap = NS._resolve_pose(boss, moving)
        boss._xr_pose_action = action
        boss._xr_phase = phase
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = hasattr(boss, "_render_scale")
        facing = getattr(boss, "direction", 1) or 1
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)

        # ── lapisan hidup (boss jalur 1:1; lane dipicu heroes/__init__)
        live, owned = NS._live_fx(boss, surface, x, y,
                                  not hero_lane, portrait)
        boss._xr_suppress_canvas_projectile = owned

        # ── GROUND LAYERS ──────────────────────────────────────────
        if not portrait:
            NS._draw_frost_aura(surface, x, y, pulse)
            NS._draw_ice_platform(surface, x, y + 40, pulse, active_skill)
            if active_skill == "q":
                NS._draw_crystal_nova_ground(surface, boss, x, y,
                                             skill_timer, pulse)
            elif active_skill == "e":
                NS._draw_arcane_aura_ground(surface, boss, x, y,
                                            skill_timer, pulse)
            elif active_skill == "r":
                NS._draw_freezing_field_ground(surface, boss, x, y,
                                               skill_timer, pulse)

        # ── CHARACTER BODY (dengan hurt-flash mask) ────────────────
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            if NS._flash_buf is None:
                NS._flash_buf = pygame.Surface((220, 240), pygame.SRCALPHA)
            NS._flash_buf.fill((0, 0, 0, 0))
            NS._record_shadow = []
            _tgt, _tx, _ty = NS._flash_buf, 110, 120

        if action == "attack":
            NS._draw_xerathis_attack(_tgt, boss, _tx, _ty)
        elif action in ("walk", "run"):
            NS._draw_xerathis_walk(_tgt, boss, _tx, _ty)
        else:
            NS._draw_xerathis_idle(_tgt, boss, _tx, _ty)

        if flash > 0:
            surface.blit(NS._flash_buf, (x - _tx, y - _ty))
            w = int(235 * min(1.0, flash / 8.0))
            m = pygame.mask.from_surface(NS._flash_buf, 50)
            wht = m.to_surface(setcolor=(w, int(w * 0.9), int(w * 0.8), 255),
                               unsetcolor=(0, 0, 0, 0))
            for rect in (NS._record_shadow or ()):
                wht.fill((0, 0, 0, 0), rect)
            surface.blit(wht, (x - _tx, y - _ty),
                         special_flags=pygame.BLEND_RGB_ADD)
            NS._record_shadow = None

        # ── FOREGROUND SKILL FX (canvas fallback) ──────────────────
        if not portrait:
            if active_skill == "q":
                NS._draw_crystal_nova(surface, boss, x, y, skill_timer,
                                      pulse)
            elif active_skill == "w":
                NS._draw_frostbite(surface, boss, x, y, skill_timer, pulse)
            elif active_skill == "e":
                NS._draw_arcane_aura_foreground(surface, boss, x, y,
                                                skill_timer, pulse)
            elif active_skill == "r":
                NS._draw_freezing_field(surface, boss, x, y, skill_timer,
                                        pulse)

        # ── LIVE TOP LAYER (trail / projectile / impact / particle) ─
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass

        # ── DEBUG ──────────────────────────────────────────────────
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_xerathis_debug(surface, boss, x, y)

    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_xerathis_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 2)
        _NS_xerathis._draw_shadow(surface, x, y + 48)
        _NS_xerathis._draw_floating_mist(surface, x, y + 35, boss.pulse)
        _NS_xerathis._draw_xerathis_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_xerathis_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(abs(math.sin(phase * 1.2)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_xerathis._draw_shadow(surface, x + sway, y + 48)
        _NS_xerathis._draw_floating_mist(surface, x + sway, y + 35, phase, trail=True,
                            facing=boss.direction)
        _NS_xerathis._draw_xerathis_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_xerathis_attack(surface, boss, x, y):
        progress = getattr(boss, "_xr_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        if 0.32 < progress < 0.42 and not getattr(boss, "_xr_proj_spawned", False):
            if not getattr(boss, "_xr_suppress_canvas_projectile", False):
                _NS_xerathis._spawn_projectile(boss, x, y)
            else:
                try:
                    from heroes import xerathis_fx as _xfx
                    _xfx.notify_projectile_cast(boss, x, y)
                except Exception:
                    pass
            boss._xr_proj_spawned = True
        if progress < 0.15 or progress > 0.9:
            boss._xr_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 2) * -boss.direction
        _NS_xerathis._draw_shadow(surface, x + recoil, y + 48)
        _NS_xerathis._draw_floating_mist(surface, x + recoil, y + 35, boss.pulse, intense=True)
        _NS_xerathis._draw_xerathis_body(surface, x + recoil, y, boss.direction, boss.pulse,
                            "attack", progress)
        _NS_xerathis._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    # ===================================================================
    # BODY RENDERING – HD detailed Crystal Maiden
    # ===================================================================
    def _draw_xerathis_body(surface, cx, cy, facing, phase, action,
                            attack_progress=0):
        """Komposit ORIGINAL-MAX: buffer tetap + outline + lighting."""
        _composite_boss_body(
            surface, _NS_xerathis, _NS_xerathis._draw_xerathis_body_raw,
            cx, cy, facing, phase, action, attack_progress,
            rim_add=(110, 150, 240), bsize=180)

    def _masterwork_finish(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """ORIGINAL-MAX detail pass: wajah lebih terbaca + rim kiri-atas."""
        P = _NS_xerathis.PALETTE
        for ex in (-3, 3):
            pygame.draw.rect(surface, P["eye_white"], (cx + ex - 2, cy - 25, 4, 3))
            pygame.draw.rect(surface, P["eye_iris"], (cx + ex - 2, cy - 25, 3, 3))
            pygame.draw.rect(surface, P["eye_iris_light"], (cx + ex - 1, cy - 26, 1, 2))
            pygame.draw.line(surface, P["hair_darkest"], (cx + ex - 3, cy - 27), (cx + ex + 1, cy - 27), 1)
        pygame.draw.line(surface, P["hair_darkest"], (cx - 1, cy - 18), (cx + 1, cy - 18), 1)
        pygame.draw.rect(surface, P["lips_mid"], (cx - 2, cy - 16, 4, 2))
        pygame.draw.rect(surface, P["skin_light"], (cx - 1, cy - 16, 2, 1))
        for xo, yo in ((-9, -10), (-6, -14), (10, -8), (12, 2)):
            pygame.draw.circle(surface, P["fur_light"], (cx + xo, cy + yo), 2)
        pygame.draw.line(surface, P["fur_light"], (cx - 11, cy - 12), (cx - 13, cy + 6), 1)
        pygame.draw.line(surface, P["robe_high"], (cx - 9, cy - 12), (cx - 8, cy + 2), 1)
        pygame.draw.circle(surface, P["gold_shine"], (cx - 1, cy - 9), 1)
        st_x = cx + 24 * facing
        st_y = cy - 54
        pygame.draw.circle(surface, P["ice_hot"], (st_x - 1, st_y - 2), 2)
        pygame.draw.circle(surface, P["ice_white"], (st_x - 1, st_y - 2), 1)


    def _draw_xerathis_body_raw(surface, cx, cy, facing, phase, action,
                                attack_progress=0):
        # Cape/cloak behind
        _NS_xerathis._draw_cloak(surface, cx, cy, facing, phase, action)

        # Floating lower body (dress/skirt)
        _NS_xerathis._draw_dress(surface, cx, cy + 5, phase)

        # Torso
        _NS_xerathis._draw_torso(surface, cx, cy - 8, phase)

        # Arms
        if action == "attack":
            _NS_xerathis._draw_attack_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_xerathis._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        # Head with hood
        _NS_xerathis._draw_head_hood(surface, cx, cy - 28, facing, phase)

        # Body frost particles
        _NS_xerathis._draw_body_particles(surface, cx, cy, phase)

        # ORIGINAL-MAX detail pass (wajah + rim)
        _NS_xerathis._masterwork_finish(surface, cx, cy, facing, phase, action,
                                        attack_progress)


    def _draw_cloak(surface, cx, cy, facing, phase, action):
        """Flowing purple cloak behind."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.1 + 0.5) * 2

        # Outer cloak
        cloak_outer = [
            (cx - 16, cy - 14),
            (cx - 22, cy + 5),
            (cx - 28 - int(wave), cy + 30),
            (cx - 20 - int(wave2), cy + 44),
            (cx - 5, cy + 48),
            (cx + 5, cy + 48),
            (cx + 20 + int(wave2), cy + 44),
            (cx + 28 + int(wave), cy + 30),
            (cx + 22, cy + 5),
            (cx + 16, cy - 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_darkest"], cloak_outer)

        cloak_mid = [
            (cx - 14, cy - 12),
            (cx - 19, cy + 5),
            (cx - 24 - int(wave * 0.7), cy + 28),
            (cx - 15, cy + 40),
            (cx, cy + 42),
            (cx + 15, cy + 40),
            (cx + 24 + int(wave * 0.7), cy + 28),
            (cx + 19, cy + 5),
            (cx + 14, cy - 12),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_dark"], cloak_mid)

        # Inner (lighter)
        cloak_inner = [
            (cx - 11, cy - 8),
            (cx - 14, cy + 5),
            (cx - 18, cy + 24),
            (cx - 8, cy + 34),
            (cx + 8, cy + 34),
            (cx + 18, cy + 24),
            (cx + 14, cy + 5),
            (cx + 11, cy - 8),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_mid"], cloak_inner)

        # Fur trim on edges
        for i, (px, py) in enumerate([
            (cx - 22, cy - 8), (cx - 26, cy + 15), (cx - 22, cy + 38),
            (cx + 22, cy - 8), (cx + 26, cy + 15), (cx + 22, cy + 38),
        ]):
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_dark"], (px, py), 4)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_mid"], (px - 1, py - 1), 3)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_light"], (px - 1, py - 1), 2)


    def _draw_dress(surface, cx, cy, phase):
        """Floating lower dress (no legs)."""
        sway = int(math.sin(phase * 0.6) * 2)
        # Outer skirt
        skirt = [
            (cx - 16, cy),
            (cx + 16, cy),
            (cx + 20 + sway, cy + 14),
            (cx + 15, cy + 24),
            (cx + 7, cy + 30),
            (cx + 2, cy + 32),
            (cx - 2, cy + 32),
            (cx - 7, cy + 30),
            (cx - 15, cy + 24),
            (cx - 20 - sway, cy + 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in skirt])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_darkest"], skirt)

        skirt_mid = [
            (cx - 13, cy + 2),
            (cx + 13, cy + 2),
            (cx + 16 + sway, cy + 14),
            (cx + 10, cy + 22),
            (cx + 5, cy + 27),
            (cx - 5, cy + 27),
            (cx - 10, cy + 22),
            (cx - 16 - sway, cy + 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_dark"], skirt_mid)

        skirt_inner = [
            (cx - 9, cy + 4),
            (cx + 9, cy + 4),
            (cx + 12 + sway, cy + 14),
            (cx + 6, cy + 20),
            (cx - 6, cy + 20),
            (cx - 12 - sway, cy + 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_mid"], skirt_inner)

        # Skirt highlight lines
        for i in range(3):
            lx = cx - 8 + i * 8
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_light"],
                    (lx, cy + 5), (lx + int(sway * 0.3), cy + 25), 1)

        # Tattered bottom (dress fringe)
        for i in range(7):
            tx = cx - 14 + i * 5
            ty = cy + 28 + int(math.sin(phase * 1.3 + i) * 2)
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_darkest"], [
                (tx - 2, cy + 24), (tx + 2, cy + 24),
                (tx + 1, ty + 3), (tx - 1, ty + 3),
            ])

        # Gold belt with buckle
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["gold_dark"], (cx - 17, cy - 1, 34, 5))
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["gold_mid"], (cx - 15, cy, 30, 3))
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["gold_light"], (cx - 13, cy + 1, 26, 1))

        # Belt center gem
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_darkest"], (cx, cy + 1), 4)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_dark"], (cx, cy + 1), 3)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_light"], (cx - 1, cy), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_bright"], (cx - 1, cy), 1)


    def _draw_torso(surface, cx, cy, phase):
        """Blue corset/bodice."""
        # Shadow
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["shadow_deep"], [
            (cx - 11 + 2, cy - 8 + 2), (cx + 11 + 2, cy - 8 + 2),
            (cx + 10 + 2, cy + 14 + 2), (cx + 4 + 2, cy + 18 + 2),
            (cx - 4 + 2, cy + 18 + 2), (cx - 10 + 2, cy + 14 + 2),
        ])
        # Corset base
        torso = [
            (cx - 11, cy - 8), (cx + 11, cy - 8),
            (cx + 10, cy + 14), (cx + 4, cy + 18),
            (cx - 4, cy + 18), (cx - 10, cy + 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_darkest"], torso)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_dark"], [
            (cx - 10, cy - 7), (cx + 10, cy - 7),
            (cx + 8, cy + 12), (cx + 3, cy + 15),
            (cx - 3, cy + 15), (cx - 8, cy + 12),
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["robe_mid"], [
            (cx - 7, cy - 5), (cx + 7, cy - 5),
            (cx + 6, cy + 10), (cx + 2, cy + 12),
            (cx - 2, cy + 12), (cx - 6, cy + 10),
        ])

        # Chest/skin area (top of bodice)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_dark"], [
            (cx - 7, cy - 9), (cx + 7, cy - 9),
            (cx + 5, cy - 5), (cx - 5, cy - 5),
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_mid"], [
            (cx - 6, cy - 9), (cx + 6, cy - 9),
            (cx + 4, cy - 6), (cx - 4, cy - 6),
        ])
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["skin_light"],
                (cx - 4, cy - 8), (cx + 4, cy - 8), 1)

        # Corset lacing (X pattern)
        for i in range(3):
            y_off = cy - 3 + i * 5
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_mid"],
                    (cx - 3, y_off), (cx + 3, y_off + 3), 1)
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_mid"],
                    (cx + 3, y_off), (cx - 3, y_off + 3), 1)

        # Center gem on chest
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["gold_dark"], (cx, cy - 1), 3)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_mid"], (cx, cy - 1), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_bright"], (cx, cy - 2), 1)

        # Side highlights on corset
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_light"],
                (cx - 9, cy - 5), (cx - 8, cy + 12), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Idle arms - one holds staff, other rests."""
        sway = int(math.sin(phase * 0.7) * 1)

        # STAFF arm (facing side - holding staff up)
        staff_side = facing
        ss_x = cx + staff_side * 11
        ss_y = cy + 2
        se_x = ss_x + staff_side * 6
        se_y = cy - 4 + sway
        sh_x = se_x + staff_side * 4
        sh_y = se_y - 4
        _NS_xerathis._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_xerathis._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_xerathis._draw_hand(surface, sh_x, sh_y)
        # Staff
        _NS_xerathis._draw_staff(surface, sh_x, sh_y, phase, staff_side)

        # OTHER arm (opposite side - resting)
        other_side = -facing
        os_x = cx + other_side * 11
        os_y = cy + 2
        oe_x = os_x + other_side * 5
        oe_y = cy + 10 + sway
        oh_x = oe_x + other_side * 3
        oh_y = oe_y + 8
        _NS_xerathis._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_xerathis._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_xerathis._draw_hand(surface, oh_x, oh_y)


    def _draw_attack_arms(surface, cx, cy, facing, phase, progress):
        """Attack pose - staff aimed forward for casting."""
        sway = int(math.sin(phase * 0.7) * 1)

        # STAFF arm extends forward for aim/cast
        staff_side = facing
        ss_x = cx + staff_side * 11
        ss_y = cy + 2

        # Aim/thrust motion
        if progress < 0.3:
            t = progress / 0.3
            ext = t * 0.4  # slight windup
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            ext = 0.4 + t * 0.6  # thrust forward
        else:
            t = (progress - 0.5) / 0.5
            ext = 1.0 - t * 0.6

        # Aim angle - slight upward
        aim_angle = -0.15
        se_x = ss_x + int((6 + ext * 4) * math.cos(aim_angle)) * staff_side
        se_y = ss_y + int((6 + ext * 4) * math.sin(aim_angle)) - 2
        sh_x = se_x + int((6 + ext * 6) * math.cos(aim_angle)) * staff_side
        sh_y = se_y + int((6 + ext * 6) * math.sin(aim_angle)) - 4

        _NS_xerathis._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_xerathis._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
        _NS_xerathis._draw_hand(surface, sh_x, sh_y)
        _NS_xerathis._draw_staff(surface, sh_x, sh_y, phase, staff_side, casting=True,
                    progress=progress)

        # OTHER arm (steadying - held out slightly)
        other_side = -facing
        os_x = cx + other_side * 11
        os_y = cy + 2
        oe_x = os_x + other_side * 6
        oe_y = cy + 6 + sway
        oh_x = oe_x + other_side * 4
        oh_y = oe_y + 6
        _NS_xerathis._draw_arm_segment(surface, os_x, os_y, oe_x, oe_y)
        _NS_xerathis._draw_arm_segment(surface, oe_x, oe_y, oh_x, oh_y)
        _NS_xerathis._draw_hand(surface, oh_x, oh_y)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Draw a robed arm segment."""
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["shadow_deep"], (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), 7)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_darkest"], (x1, y1), (x2, y2), 6)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_dark"], (x1, y1), (x2, y2), 4)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_mid"], (x1, y1), (x2, y2), 2)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["robe_light"], (x1, y1 - 1), (x2, y2 - 1), 1)


    def _draw_hand(surface, x, y):
        """Small skin-colored hand."""
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_darkest"], (x, y), 3)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_mid"], (x, y), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_light"], (x - 1, y - 1), 1)


    def _draw_staff(surface, x, y, phase, side, casting=False, progress=0):
        """The crystal staff."""
        # Staff pole - long, from hand upward and behind
        top_x = x + side * 4
        top_y = y - 38
        bot_x = x - side * 2
        bot_y = y + 16

        # Shadow
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["shadow_deep"],
                (top_x + 2, top_y + 2), (bot_x + 2, bot_y + 2), 5)
        # Wooden staff (gold-colored)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_dark"], (top_x, top_y), (bot_x, bot_y), 4)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_mid"], (top_x, top_y), (bot_x, bot_y), 3)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_light"], (top_x, top_y), (bot_x, bot_y), 1)

        # Wraps/rings on staff
        for t in (0.35, 0.65, 0.85):
            rx = int(top_x + (bot_x - top_x) * t)
            ry = int(top_y + (bot_y - top_y) * t)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["cloak_dark"], (rx, ry), 3)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["cloak_mid"], (rx, ry), 2)

        # Staff head - crystal cluster
        head_x, head_y = top_x, top_y - 4

        glow_size = 8
        if casting:
            glow_size = 8 + int(math.sin(progress * math.pi) * 12)

        # Backing glow
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], 100), (head_x, head_y), glow_size + 4)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], 160), (head_x, head_y), glow_size)

        # Gold claws holding the crystal
        for offset_a in (-1.0, -0.3, 0.3, 1.0):
            cx1 = head_x + int(math.cos(math.pi / 2 + offset_a) * 3)
            cy1 = head_y + int(math.sin(math.pi / 2 + offset_a) * 3)
            cx2 = head_x + int(math.cos(math.pi / 2 + offset_a) * 8)
            cy2 = head_y + int(math.sin(math.pi / 2 + offset_a) * 8) - 3
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_dark"], (cx1, cy1), (cx2, cy2), 3)
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["gold_mid"], (cx1, cy1), (cx2, cy2), 1)

        # Large main ice crystal - vertical
        crystal_h = 10
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_darkest"], [
            (head_x - 4, head_y),
            (head_x + 4, head_y),
            (head_x + 3, head_y - crystal_h + 2),
            (head_x, head_y - crystal_h),
            (head_x - 3, head_y - crystal_h + 2),
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_dark"], [
            (head_x - 3, head_y - 1),
            (head_x + 3, head_y - 1),
            (head_x + 2, head_y - crystal_h + 3),
            (head_x, head_y - crystal_h + 1),
            (head_x - 2, head_y - crystal_h + 3),
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_mid"], [
            (head_x - 2, head_y - 2),
            (head_x + 2, head_y - 2),
            (head_x + 1, head_y - crystal_h + 4),
            (head_x, head_y - crystal_h + 2),
            (head_x - 1, head_y - crystal_h + 4),
        ])
        # Bright highlight
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_bright"],
                (head_x - 1, head_y - crystal_h + 3),
                (head_x - 1, head_y - 2), 1)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (head_x - 1, head_y - crystal_h + 4), 1)

        # Small side crystals
        _NS_xerathis._draw_ice_shard(surface, head_x - 3, head_y - 3, 4, -math.pi / 2 - 0.4,
                        _NS_xerathis.PALETTE["ice_dark"], _NS_xerathis.PALETTE["ice_mid"],
                        _NS_xerathis.PALETTE["ice_light"], _NS_xerathis.PALETTE["ice_white"])
        _NS_xerathis._draw_ice_shard(surface, head_x + 3, head_y - 3, 4, -math.pi / 2 + 0.4,
                        _NS_xerathis.PALETTE["ice_dark"], _NS_xerathis.PALETTE["ice_mid"],
                        _NS_xerathis.PALETTE["ice_light"], _NS_xerathis.PALETTE["ice_white"])

        # Pulsing glow
        pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], int(80 * pulse)),
                  (head_x, head_y - 4), int(6 * pulse))


    def _draw_head_hood(surface, cx, cy, facing, phase):
        """Crystal Maiden's face with hood and hair."""
        # Hood back (behind head)
        hood_back = [
            (cx - 12, cy - 6),
            (cx - 14, cy + 4),
            (cx - 12, cy + 12),
            (cx + 12, cy + 12),
            (cx + 14, cy + 4),
            (cx + 12, cy - 6),
            (cx + 8, cy - 14),
            (cx - 8, cy - 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in hood_back])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_darkest"], hood_back)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_dark"], [
            (cx - 11, cy - 5),
            (cx - 13, cy + 4),
            (cx - 11, cy + 11),
            (cx + 11, cy + 11),
            (cx + 13, cy + 4),
            (cx + 11, cy - 5),
            (cx + 7, cy - 13),
            (cx - 7, cy - 13),
        ])

        # Hair fringe (blonde, visible under hood)
        hair_points = [
            (cx - 8, cy - 6),
            (cx - 9, cy - 2),
            (cx - 7, cy + 1),
            (cx - 3, cy - 1),
            (cx, cy),
            (cx + 3, cy - 1),
            (cx + 7, cy + 1),
            (cx + 9, cy - 2),
            (cx + 8, cy - 6),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["hair_darkest"], hair_points)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["hair_dark"], [
            (cx - 7, cy - 5),
            (cx - 8, cy - 2),
            (cx - 6, cy),
            (cx - 2, cy - 1),
            (cx + 2, cy - 1),
            (cx + 6, cy),
            (cx + 8, cy - 2),
            (cx + 7, cy - 5),
        ])
        # Hair highlight
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_mid"],
                (cx - 5, cy - 4), (cx - 3, cy - 2), 1)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_light"],
                (cx + 3, cy - 4), (cx + 5, cy - 3), 1)

        # Face (skin)
        face_points = [
            (cx - 6, cy),
            (cx - 7, cy + 4),
            (cx - 5, cy + 8),
            (cx - 2, cy + 10),
            (cx + 2, cy + 10),
            (cx + 5, cy + 8),
            (cx + 7, cy + 4),
            (cx + 6, cy),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_darkest"],
              [(p[0] + 1, p[1] + 1) for p in face_points])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_dark"], face_points)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["skin_mid"], [
            (cx - 5, cy + 1),
            (cx - 6, cy + 4),
            (cx - 4, cy + 7),
            (cx - 2, cy + 9),
            (cx + 2, cy + 9),
            (cx + 4, cy + 7),
            (cx + 6, cy + 4),
            (cx + 5, cy + 1),
        ])
        # Cheek highlights
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_light"], (cx - 3, cy + 5), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_light"], (cx + 3, cy + 5), 2)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_high"], (cx - 3, cy + 5), 1)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_high"], (cx + 3, cy + 5), 1)

        # Eyes
        for eye_x in (-3, 3):
            # Eye white
            _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["eye_white"], (cx + eye_x - 1, cy + 3, 2, 2))
            # Iris
            _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["eye_iris"], (cx + eye_x - 1, cy + 3, 2, 2))
            # Bright center
            _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["eye_iris_light"], (cx + eye_x, cy + 3, 1, 1))

        # Eyelashes/brows
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_darkest"],
                (cx - 5, cy + 2), (cx - 1, cy + 2), 1)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_darkest"],
                (cx + 1, cy + 2), (cx + 5, cy + 2), 1)

        # Nose (subtle)
        _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["skin_darkest"], (cx, cy + 6), 1)

        # Lips
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["lips_dark"], (cx - 2, cy + 8, 4, 1))
        _NS_xerathis._rect(surface, _NS_xerathis.PALETTE["lips_mid"], (cx - 1, cy + 8, 2, 1))

        # Hood top (in front, framing the face)
        hood_top = [
            (cx - 11, cy - 5),
            (cx - 13, cy - 2),
            (cx - 10, cy + 2),
            (cx - 8, cy - 2),
            (cx - 6, cy - 8),
            (cx, cy - 12),
            (cx + 6, cy - 8),
            (cx + 8, cy - 2),
            (cx + 10, cy + 2),
            (cx + 13, cy - 2),
            (cx + 11, cy - 5),
            (cx + 8, cy - 14),
            (cx - 8, cy - 14),
        ]
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_darkest"], hood_top)
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_dark"], [
            (cx - 10, cy - 4),
            (cx - 11, cy - 2),
            (cx - 9, cy + 1),
            (cx - 8, cy - 3),
            (cx - 6, cy - 7),
            (cx, cy - 11),
            (cx + 6, cy - 7),
            (cx + 8, cy - 3),
            (cx + 9, cy + 1),
            (cx + 11, cy - 2),
            (cx + 10, cy - 4),
            (cx + 7, cy - 13),
            (cx - 7, cy - 13),
        ])
        # Hood mid highlight
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["cloak_mid"], [
            (cx - 8, cy - 6),
            (cx - 9, cy - 3),
            (cx - 7, cy - 1),
            (cx - 5, cy - 6),
            (cx, cy - 9),
            (cx + 5, cy - 6),
            (cx + 7, cy - 1),
            (cx + 9, cy - 3),
            (cx + 8, cy - 6),
            (cx + 6, cy - 11),
            (cx - 6, cy - 11),
        ])

        # White fur trim on hood
        for i in range(9):
            angle = -math.pi + i * math.pi / 8
            fx = cx + int(math.cos(angle) * 12)
            fy = cy - 4 + int(math.sin(angle) * 9)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_dark"], (fx, fy), 3)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_mid"], (fx - 1, fy - 1), 2)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["fur_light"], (fx - 1, fy - 1), 1)

        # Ice crystal on top of hood
        _NS_xerathis._draw_ice_shard(surface, cx, cy - 15, 5, -math.pi / 2,
                        _NS_xerathis.PALETTE["ice_darkest"], _NS_xerathis.PALETTE["ice_dark"],
                        _NS_xerathis.PALETTE["ice_light"], _NS_xerathis.PALETTE["ice_white"])

        # Small ear/hair strands on sides
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["hair_dark"], [
            (cx - 8, cy + 2), (cx - 10, cy + 6), (cx - 7, cy + 8)
        ])
        _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["hair_dark"], [
            (cx + 8, cy + 2), (cx + 10, cy + 6), (cx + 7, cy + 8)
        ])
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_mid"],
                (cx - 8, cy + 3), (cx - 9, cy + 6), 1)
        _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["hair_mid"],
                (cx + 8, cy + 3), (cx + 9, cy + 6), 1)


    def _draw_body_particles(surface, cx, cy, phase):
        """Floating frost particles around body."""
        for i in range(10):
            angle = phase * 0.4 + i * math.pi / 5
            radius = 28 + int(math.sin(phase * 0.7 + i) * 8)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(120 + math.sin(phase + i * 0.7) * 60)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha), (px, py), 2)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_white"], alpha), (px, py), 1)

        # Falling snowflakes
        for i in range(4):
            t = (phase * 0.3 + i * 0.25) % 1.0
            fx = cx - 30 + i * 20 + int(math.sin(phase + i) * 5)
            fy = cy - 40 + int(t * 90)
            alpha = int(200 * (1 - t))
            _NS_xerathis._draw_snowflake(surface, fx, fy, 3,
                            phase + i, (*_NS_xerathis.PALETTE["ice_bright"], alpha))


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_mist(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Frost mist beneath floating Xerathis."""
        NS = _NS_xerathis
        if NS._mist_cache is None:
            mist = pygame.Surface((120, 40), pygame.SRCALPHA)
            for radius in range(30, 3, -4):
                alpha = int((30 - radius) * 2.8)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*NS.PALETTE["ice_dark"], min(255, alpha)),
                        (60 - radius * 2, 20 - radius // 3,
                         radius * 4, max(3, radius // 2)),
                    )
            NS._mist_cache = mist
        strength = 1.5 if intense else 1.0
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        spr = NS._mist_cache
        spr.set_alpha(int(255 * min(1.0, pulse * strength)))
        surface.blit(spr, (cx - 60, cy - 10))

        # Rising frost wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], alpha), (sx, sy), 5)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha), (sx, sy - 2), 3)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting frost crystals
        for i in range(4):
            angle = phase * 0.9 + i * math.pi * 2 / 4
            r = 22 + int(math.sin(phase + i * 1.3) * 5)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_mid"], (sx, sy), 3)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_bright"], (sx, sy), 2)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 120 - i * 22)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y, lift=0):
        """Ground shadow (cache + reaktif saat lift)."""
        NS = _NS_xerathis
        if NS._shadow_cache is None:
            shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
            for radius in range(10, 0, -1):
                alpha = max(0, (10 - radius) * 16)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
                )
            pygame.draw.ellipse(shadow, (*NS.PALETTE["ice_dark"], 40), (8, 4, 84, 10))
            NS._shadow_cache = shadow
        spr = NS._shadow_cache
        w, h = spr.get_size()
        if lift:
            k = max(0.12, 1.0 - lift * 0.05)
            w = max(6, int(w * k))
            h = max(2, int(h * k))
            spr = pygame.transform.smoothscale(spr, (w, h))
        bx = x - w // 2
        by = (y + 10) - h          # dasar tetap menapak di y+10
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))


    def _draw_frost_aura(surface, x, y, phase):
        """Large background aura (basis di-cache, denyut via alpha)."""
        NS = _NS_xerathis
        if NS._aura_cache is None:
            aura = pygame.Surface((180, 160), pygame.SRCALPHA)
            for radius in range(70, 5, -4):
                alpha = int((70 - radius) * 1.2)
                if alpha > 0:
                    NS._aacircle(aura, (*NS.PALETTE["ice_darkest"], min(255, alpha)),
                                 (90, 80), radius)
            NS._aura_cache = aura
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        spr = NS._aura_cache
        spr.set_alpha(int(255 * max(0.2, min(1.0, pulse))))
        surface.blit(spr, (x - 90, y - 80))


    def _draw_ice_platform(surface, x, y, phase, skill):
        """Ice snowflake pattern on the ground (basis di-cache)."""
        NS = _NS_xerathis
        if NS._ground_cache is None:
            ring = pygame.Surface((130, 44), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_dark"], 150),
                                (5, 10, 120, 24), 3)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_mid"], 180),
                                (20, 14, 90, 16), 2)
            for i in range(8):
                angle = i * math.pi / 4
                x1 = 65 + int(math.cos(angle) * 20)
                y1 = 22 + int(math.sin(angle) * 4)
                x2 = 65 + int(math.cos(angle) * 55)
                y2 = 22 + int(math.sin(angle) * 10)
                pygame.draw.line(ring, (*NS.PALETTE["ice_light"], 170),
                                 (x1, y1), (x2, y2), 1)
            for angle_deg in (0, 90, 180, 270):
                angle = math.radians(angle_deg)
                sx = 65 + int(math.cos(angle) * 50)
                sy = 22 + int(math.sin(angle) * 9)
                pygame.draw.circle(ring, (*NS.PALETTE["ice_bright"], 200), (sx, sy), 2)
            NS._ground_cache = ring
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        surface.blit(NS._ground_cache, (x - 65, y - 22))
        if skill:
            pygame.draw.ellipse(surface, (*NS.PALETTE["ice_bright"], int(80 * pulse)),
                                (x - 50, y - 14, 100, 28), 1)


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash effect during ranged attack (at staff tip)."""
        if progress < 0.25 or progress > 0.6:
            return
        t = (progress - 0.25) / 0.35
        intensity = math.sin(t * math.pi)

        flash_x = x + 26 * facing
        flash_y = y - 18

        alpha = int(180 * intensity)
        radius = int(6 + intensity * 15)

        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha // 2),
                  (flash_x, flash_y), radius + 6)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha),
                  (flash_x, flash_y), radius)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_white"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 4))

        for i in range(5):
            angle = progress * 6 + i * math.pi * 2 / 5
            ex = flash_x + int(math.cos(angle) * radius * 1.4)
            ey = flash_y + int(math.sin(angle) * radius * 1.4)
            _NS_xerathis._draw_snowflake(surface, ex, ey, 3, progress,
                            (*_NS_xerathis.PALETTE["ice_bright"], alpha))


    # ===================================================================
    # SKILL Q: CRYSTAL NOVA (AoE ice explosion at target)
    # ===================================================================
    def _draw_crystal_nova_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_xerathis._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 60))
        # Warning circle
        radius = int(25 + progress * 45)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], 100), (tx, ty), radius, 2)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], 80), (tx, ty), radius + 6, 1)


    def _draw_crystal_nova(surface, boss, x, y, timer, phase):
        tx, ty = _NS_xerathis._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 60))

        if progress < 0.35:
            # Casting phase - energy gathering above target
            t = progress / 0.35
            # Rising energy above target
            for i in range(5):
                offset = i * 0.15
                it = min(1.0, t + offset)
                gy = ty - int(it * 30)
                alpha = int(180 * (1 - offset))
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha),
                          (tx, gy), max(1, 4 - i))
        else:
            # Nova explosion phase
            t = (progress - 0.35) / 0.65

            # Central burst
            burst_r = int(20 + t * 25)
            alpha = int(220 * (1 - t))

            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha), (tx, ty), burst_r + 4)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], alpha), (tx, ty), burst_r)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], alpha), (tx, ty), burst_r // 2)

            # Radial ice crystals rising from ground
            for i in range(10):
                angle = i * math.pi / 5 + phase * 0.05
                dist = int(15 + t * 30)
                sx = tx + int(math.cos(angle) * dist)
                sy = ty + int(math.sin(angle) * dist * 0.6)

                # Rising crystal
                grow = min(1.0, t * 2.0)
                size = int(12 * grow)

                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_darkest"], [
                    (sx - 4, sy + size // 2),
                    (sx + 4, sy + size // 2),
                    (sx + 2, sy - size),
                    (sx, sy - size - 2),
                    (sx - 2, sy - size),
                ])
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_dark"], [
                    (sx - 3, sy + size // 2 - 1),
                    (sx + 3, sy + size // 2 - 1),
                    (sx + 1, sy - size + 1),
                    (sx, sy - size - 1),
                    (sx - 1, sy - size + 1),
                ])
                _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_mid"], [
                    (sx - 2, sy + size // 2 - 2),
                    (sx + 2, sy + size // 2 - 2),
                    (sx + 1, sy - size + 2),
                    (sx - 1, sy - size + 2),
                ])
                _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_bright"],
                        (sx, sy + size // 2 - 2), (sx, sy - size + 2), 1)
                _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (sx, sy - size), 1)

            # Ring shockwave
            ring_r = int(40 + t * 30)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_light"], int(150 * (1 - t))),
                      (tx, ty), ring_r, 2)


    # ===================================================================
    # SKILL W: FROSTBITE
    # ===================================================================
    def _draw_frostbite(surface, boss, x, y, timer, phase):
        tx, ty = _NS_xerathis._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 50))

        start_x = x + 26 * boss.direction
        start_y = y - 18

        if progress < 0.35:
            # Frost bolt flying to target
            t = progress / 0.35
            cur_x = start_x + (tx - start_x) * t
            cur_y = start_y + (ty - start_y) * t

            # Trail
            for i in range(6):
                tt = t - i * 0.05
                if tt <= 0:
                    continue
                px = int(start_x + (tx - start_x) * tt)
                py = int(start_y + (ty - start_y) * tt)
                alpha = max(0, 200 - i * 30)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha), (px, py), 6 - i // 2)
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], alpha), (px, py), 3)

            # Bolt head
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_dark"], 200),
                      (int(cur_x), int(cur_y)), 12)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_light"], (int(cur_x), int(cur_y)), 7)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_bright"], (int(cur_x), int(cur_y)), 4)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (int(cur_x), int(cur_y)), 2)
        else:
            # Target is frozen - ice encasing
            t = (progress - 0.35) / 0.65
            size = int(18 + t * 8)

            # Ice block encasing target
            _NS_xerathis._poly(surface, (*_NS_xerathis.PALETTE["ice_dark"], 220), [
                (tx - size, ty + size),
                (tx - size + 4, ty - size),
                (tx + size - 4, ty - size),
                (tx + size, ty + size),
            ])
            _NS_xerathis._poly(surface, (*_NS_xerathis.PALETTE["ice_mid"], 200), [
                (tx - size + 3, ty + size - 3),
                (tx - size + 6, ty - size + 3),
                (tx + size - 6, ty - size + 3),
                (tx + size - 3, ty + size - 3),
            ])
            _NS_xerathis._poly(surface, (*_NS_xerathis.PALETTE["ice_light"], 160), [
                (tx - size + 6, ty + size - 6),
                (tx - size + 9, ty - size + 6),
                (tx + size - 9, ty - size + 6),
                (tx + size - 6, ty + size - 6),
            ])

            # Ice crystals sticking out
            for i in range(6):
                angle = phase * 0.5 + i * math.pi / 3
                sx = tx + int(math.cos(angle) * size)
                sy = ty + int(math.sin(angle) * size * 0.7) - 3
                _NS_xerathis._draw_ice_shard(surface, sx, sy,
                                5 + int(math.sin(phase + i) * 1),
                                angle - math.pi / 2,
                                _NS_xerathis.PALETTE["ice_darkest"], _NS_xerathis.PALETTE["ice_dark"],
                                _NS_xerathis.PALETTE["ice_light"], _NS_xerathis.PALETTE["ice_white"])

            # Shine highlight
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_hot"],
                    (tx - size + 8, ty - size + 4),
                    (tx - 2, ty - size + 4), 2)


    # ===================================================================
    # SKILL E: ARCANE AURA (buffs self)
    # ===================================================================
    def _draw_arcane_aura_ground(surface, boss, x, y, timer, phase):
        """Aura circle around Xerathis on ground."""
        progress = max(0.0, min(1.0, 1 - timer / 90))
        radius = int(45 + progress * 20)
        pulse = math.sin(phase * 1.5) * 0.2 + 0.8

        aura = pygame.Surface((radius * 2 + 20, radius + 20), pygame.SRCALPHA)
        cx, cy = radius + 10, (radius + 20) // 2

        # Ring
        pygame.draw.ellipse(aura, (*_NS_xerathis.PALETTE["ice_mid"], int(180 * pulse)),
                            (5, 5, radius * 2 + 10, radius + 10), 3)
        pygame.draw.ellipse(aura, (*_NS_xerathis.PALETTE["ice_bright"], int(150 * pulse)),
                            (15, 8, radius * 2 - 10, radius + 4), 2)

        # Runic marks around aura
        for i in range(8):
            a = phase * 0.3 + i * math.pi / 4
            px = cx + int(math.cos(a) * (radius - 5))
            py = cy + int(math.sin(a) * (radius // 2 - 4))
            pygame.draw.circle(aura, (*_NS_xerathis.PALETTE["ice_hot"], int(220 * pulse)),
                               (px, py), 3)
            pygame.draw.circle(aura, (*_NS_xerathis.PALETTE["ice_white"], int(220 * pulse)),
                               (px, py), 1)

        surface.blit(aura, (x - cx, y + 30 - cy))


    def _draw_arcane_aura_foreground(surface, boss, x, y, timer, phase):
        """Rising magical energy around Xerathis."""
        duration = 90
        # Guard lifecycle: jangan menggambar di luar durasi skill AI.
        if timer <= 0 or timer > duration:
            return
        # Rising energy particles all around body
        for i in range(10):
            t = (phase * 0.5 + i * 0.1) % 1.0
            angle = i * math.pi / 5 + phase * 0.3
            dist = 20 + int(math.sin(phase + i) * 5)
            sx = x + int(math.cos(angle) * dist)
            sy = y + 30 - int(t * 70)
            alpha = int(200 * (1 - t))
            size = 3 + int(t * 3)

            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_mid"], alpha), (sx, sy), size + 2)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], alpha), (sx, sy), size)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_white"], alpha), (sx, sy), max(1, size - 2))

        # Pulsing halo around body
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        halo_r = int(40 * pulse)
        _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], int(60 * pulse)),
                  (x, y - 10), halo_r, 2)


    # ===================================================================
    # SKILL R: FREEZING FIELD
    # ===================================================================
    def _draw_freezing_field_ground(surface, boss, x, y, timer, phase):
        """Large ice field around Xerathis."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        radius = int(60 + progress * 30)
        pulse = math.sin(phase * 1.2) * 0.2 + 0.8

        field = pygame.Surface((radius * 2 + 30, radius + 30), pygame.SRCALPHA)
        cx, cy = radius + 15, (radius + 30) // 2

        # Base ice ring
        pygame.draw.ellipse(field, (*_NS_xerathis.PALETTE["ice_dark"], int(180 * pulse)),
                            (5, 5, radius * 2 + 20, radius + 20), 4)
        pygame.draw.ellipse(field, (*_NS_xerathis.PALETTE["ice_mid"], int(140 * pulse)),
                            (20, 12, radius * 2 - 10, radius + 6), 2)

        # Frost pattern
        for i in range(12):
            a = phase * 0.2 + i * math.pi / 6
            x1 = cx + int(math.cos(a) * 15)
            y1 = cy + int(math.sin(a) * 5)
            x2 = cx + int(math.cos(a) * (radius - 5))
            y2 = cy + int(math.sin(a) * (radius // 2 - 2))
            pygame.draw.line(field, (*_NS_xerathis.PALETTE["ice_light"], int(150 * pulse)),
                             (x1, y1), (x2, y2), 1)

        surface.blit(field, (x - cx, y + 30 - cy))


    def _draw_freezing_field(surface, boss, x, y, timer, phase):
        """Randomly exploding ice crystals in the field."""
        duration = 100
        # Guard lifecycle: jangan menggambar di luar durasi skill AI.
        if timer <= 0 or timer > duration:
            return
        # Deterministic random positions using phase
        for i in range(8):
            # Each crystal has its own life cycle
            crystal_phase = (phase * 0.4 + i * 0.35) % 1.0
            angle = i * math.pi / 4 + i * 0.7
            dist_r = 40 + (i * 13) % 30
            px = x + int(math.cos(angle) * dist_r)
            py = y + 25 + int(math.sin(angle) * dist_r * 0.3)

            # Grow then shrink cycle
            if crystal_phase < 0.5:
                grow = crystal_phase / 0.5
            else:
                grow = 1.0 - (crystal_phase - 0.5) / 0.5

            size = int(14 * grow)
            if size < 2:
                continue

            # Ice crystal spike shooting up
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_darkest"], [
                (px - 5, py + size // 2),
                (px + 5, py + size // 2),
                (px + 3, py - size),
                (px, py - size - 3),
                (px - 3, py - size),
            ])
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_dark"], [
                (px - 4, py + size // 2 - 1),
                (px + 4, py + size // 2 - 1),
                (px + 2, py - size + 1),
                (px, py - size - 2),
                (px - 2, py - size + 1),
            ])
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_mid"], [
                (px - 3, py + size // 2 - 2),
                (px + 3, py + size // 2 - 2),
                (px + 1, py - size + 2),
                (px, py - size - 1),
                (px - 1, py - size + 2),
            ])
            _NS_xerathis._poly(surface, _NS_xerathis.PALETTE["ice_light"], [
                (px - 2, py + size // 2 - 3),
                (px + 2, py + size // 2 - 3),
                (px + 1, py - size + 3),
                (px - 1, py - size + 3),
            ])
            # Highlight
            _NS_xerathis._aaline(surface, _NS_xerathis.PALETTE["ice_bright"],
                    (px, py + size // 2 - 3), (px, py - size + 3), 1)
            _NS_xerathis._aacircle(surface, _NS_xerathis.PALETTE["ice_white"], (px, py - size), 1)

            # Impact glow at base
            if grow > 0.3:
                _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], int(150 * grow)),
                          (px, py + size // 2), int(size * 0.8))

        # Continuous swirling frost energy
        for i in range(8):
            angle = phase * 0.8 + i * math.pi / 4
            r = 55
            sx = x + int(math.cos(angle) * r)
            sy = y + 25 + int(math.sin(angle) * r * 0.35)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_bright"], 180), (sx, sy), 2)
            _NS_xerathis._aacircle(surface, (*_NS_xerathis.PALETTE["ice_white"], 220), (sx, sy), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_xerathis.draw_xerathis(surface, boss, x, y)


# ====================================================================
# NYZRAK  ->  renderer v4 hidup di bosses/nyzrak_v4.py
# ====================================================================
# Rewrite total (pixel-art buffer + animasi delta-time + pose solver)
# dipindah ke modul sendiri supaya setiap layer renderer dapat diedit
# independen tanpa menyentuh bundle 4-boss ini. Nama lama dipertahankan:
# ``_NS_nyzrak`` tetap resolve dari bosses.level3 untuk gameplay,
# heroes/nyzrak_fx (lazy import) dan tes regresi.
from bosses.nyzrak_v4 import _NS_nyzrak  # noqa: E402,F401



# ====================================================================
# ANCIENT_APPARITION
# ====================================================================
class _NS_ancient_apparition:
    """Namespace ancient_apparition — FULL REWRITE visual & animasi.

    TRUE BOSS Level 3: wraith es purba.  Seluruh visual prosedural
    (pygame.draw + Surface + transform), tanpa satu pun aset eksternal.

    Arsitektur render (layer, urutan kontrak proyek):

        GROUND FX (aura beku, platform, telegraph skill)
          -> SHADOW (reaktif, dasar menapak)
          -> BACK ARM + BACK ORBIT
          -> SKIRT (jubah shard)
          -> TORSO -> ARMOR (pauldron) -> HEAD -> CROWN
          -> FRONT ARM + CLAW (senjata) -> FRONT ORBIT
          -> HIGHLIGHTS (rim + glint)
          -> ATTACK FX (flash cakar, trail canvas fallback)
          -> SKILL FX / PROJECTILE (fallback canvas)
          -> LIVE FX LAYER (heroes/ancient_apparition_fx — layar 1:1)
          -> DEBUG OVERLAY

    GAYA PIXEL ART: rig digambar di buffer setengah resolusi lalu
    di-upscale 2x nearest-neighbor (PIXEL = 2) sehingga piksel chunky,
    tepi keras, palet terbatas, highlight/shadow per-piksel — bukan
    vektor halus.

    Kontrak API lama dipertahankan (dipakai tools/test_level3_masterwork,
    heroes/__init__, bosses/_boss_index): draw_apparition / draw_boss /
    draw_ancient_apparition, _draw_shadow(lift), _draw_aa_body[_raw],
    _update_attack_anim, _detect_moving, durasi FX == AI.
    """

    # ── switch debug (hitbox/hurtbox/range/state/FPS/partikel) ──
    DEBUG_CHARACTER = False

    # ── cache komposit (piksel-identik, dibangun lazy) ──
    _body_buf = None
    _flash_buf = None
    _record_shadow = None
    _shadow_cache = None
    _aura_cache = None
    _ground_cache = None
    _mist_cache = None
    _rig_lo = None          # buffer rig resolusi rendah (pixel art)
    _rig_px = None          # hasil upscale 2x (chunky)

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    #: Skala pixel art chunky (semua bagian badan digambar di 1/PIXEL).
    PIXEL = 2

    #: Geometri lengan (px penuh, relatif jangkar badan) — MIRROR dari
    #: heroes/ancient_apparition_fx (_SHOULDER/_UPPER/_FORE/_CLAW).
    #: Jangan ubah satu sisi saja: trail layar menempel pada angka ini.
    SHOULDER_OFF = (13.0, -6.0)
    UPPER_LEN = 10.0
    FORE_LEN = 11.0
    CLAW_LEN = 8.0

    #: Fase serangan (progress 0..1) — MIRROR heroes/ancient_apparition_fx.
    ATK_PHASES = {
        "anticipation": (0.00, 0.20),
        "windup":       (0.20, 0.38),
        "swing":        (0.38, 0.55),
        "follow":       (0.55, 0.75),
        "recovery":     (0.75, 1.00),
    }

    # ---------------------------------------------------------------------------
    # HD Ice Palette (dark fantasy, terbatas, kontras)
    # ---------------------------------------------------------------------------
    PALETTE = {
        # ── kontrak inti ──
        "outline":     (6, 10, 20),
        "shadow":      (2, 5, 12),
        "dark":        (18, 38, 78),
        "body":        (30, 62, 112),
        "mid":         (55, 110, 180),
        "light":       (115, 175, 230),
        "highlight":   (170, 215, 250),
        "weapon":      (170, 215, 250),
        "fx":          (150, 225, 255),

        # ── ramp es ──
        "ice_darkest": (8, 20, 55),
        "ice_dark":    (22, 55, 115),
        "ice_mid":     (55, 110, 180),
        "ice_light":   (115, 175, 230),
        "ice_bright":  (170, 215, 250),
        "ice_hot":     (220, 240, 255),
        "ice_pure":    (245, 252, 255),

        # ── aksen ──
        "cyan_dark":   (15, 75, 110),
        "cyan_mid":    (55, 155, 195),
        "shadow_ice":  (12, 25, 55),
        "face_dark":   (30, 70, 130),
        "face_mid":    (95, 175, 230),
        "face_bright": (180, 230, 255),
        "face_hot":    (230, 248, 255),
        "frost_dark":  (30, 75, 130),
        "frost_mid":   (95, 165, 220),
        "frost_light": (170, 220, 250),
        "shadow_deep": (2, 5, 12),
        "white":       (255, 255, 255),
    }

    # ===================================================================
    # UTIL GAMBAR
    # ===================================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_ancient_apparition._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4),
                                  pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2),
                               radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_ancient_apparition.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius,
                                     width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_ancient_apparition._clamp(color)
        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]), int(end[1])
        if len(color) == 4 and color[3] < 255:
            min_x = min(sx, ex) - width - 2
            min_y = min(sy, ey) - width - 2
            w = abs(ex - sx) + width * 4 + 8
            h = abs(ey - sy) + width * 4 + 8
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(temp, color, (sx - min_x, sy - min_y),
                             (ex - min_x, ey - min_y), max(1, width))
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey),
                         max(1, width))

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_ancient_apparition._clamp(color)
        if len(color) == 4 and color[3] < 255:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, min_y = min(xs) - 2, min(ys) - 2
            w = max(xs) - min_x + 4
            h = max(ys) - min_y + 4
            if w <= 0 or h <= 0:
                return
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            shifted = [(p[0] - min_x, p[1] - min_y) for p in points]
            pygame.draw.polygon(temp, color, shifted)
            surface.blit(temp, (min_x, min_y))
            return
        pygame.draw.polygon(surface, color[:3], points)

    def _ellipse(surface, color, rect, width=0):
        color = _NS_ancient_apparition._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4),
                                  pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, int(rw), int(rh)), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3],
                            (rect[0], rect[1], int(rect[2]), int(rect[3])),
                            width)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            # Konversi koordinat DUNIA target ke ruang jangkar (x, y)
            # dengan kompensasi scale pipeline hero (lihat catatan lama).
            scale = float(getattr(boss, "_render_scale", 1.0)) or 1.0
            tx = x + (target.x - getattr(boss, "x", x)) / scale
            ty = y + (target.y - getattr(boss, "y", y)) / scale
            return int(tx), int(ty)
        return int(x + 200 / float(getattr(boss, "_render_scale", 1.0)
                                   or 1.0)
                   * getattr(boss, "direction", 1)), int(y)

    def _hash01(seed):
        seed &= 0xFFFFFFFF
        seed = (seed * 2654435761) & 0xFFFFFFFF
        seed ^= seed >> 13
        seed = (seed * 1274126177) & 0xFFFFFFFF
        return ((seed ^ (seed >> 16)) & 0xFFFF) / 65535.0

    # ===================================================================
    # ANIMATION CONTROLLER
    # ===================================================================
    # State: IDLE / WALK / RUN / ATTACK / CAST / SKILL / HIT / HURT /
    #        DEATH / CHARGE / SPECIAL.
    # Sumber kebenaran state tetap atribut gameplay (timer, active_skill,
    # hurt_flash_timer) — renderer hanya menerjemahkan, tidak menyimpan.

    def _ease_in_out(t):
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        if t < 0.5:
            return 2.0 * t * t
        return 1.0 - 2.0 * (1.0 - t) * (1.0 - t)

    def _ease_in(t):
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        return t * t

    def _ease_out(t):
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        return 1.0 - (1.0 - t) * (1.0 - t)

    def _attack_phase(progress):
        p = 0.0 if progress <= 0.0 else (1.0 if progress >= 1.0
                                         else progress)
        for name in ("anticipation", "windup", "swing", "follow",
                     "recovery"):
            lo, hi = _NS_ancient_apparition.ATK_PHASES[name]
            if p < hi:
                return name
        return "recovery"

    def _detect_moving(boss):
        """Deteksi gerak + kecepatan (px/frame) untuk pemisahan WALK/RUN."""
        NS = _NS_ancient_apparition
        if not hasattr(boss, "_aa_last_x"):
            boss._aa_last_x = boss.x
            boss._aa_last_y = boss.y
            boss._aa_speed = 0.0
            return False
        dx = boss.x - boss._aa_last_x
        dy = boss.y - boss._aa_last_y
        boss._aa_last_x = boss.x
        boss._aa_last_y = boss.y
        boss._aa_speed = math.hypot(dx, dy)
        return dx + dy > 0.3 or dx + dy < -0.3

    def _update_attack_anim(boss):
        """Jendela serangan dari timer gameplay (pola lama, tetap)."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_aa_prev_timer", 0))
        active = bool(getattr(boss, "_aa_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._aa_attack_active = True
            boss._aa_attack_frame = 0
            active = True
        elif active:
            boss._aa_attack_frame = int(
                getattr(boss, "_aa_attack_frame", 0)) + 1
            if boss._aa_attack_frame > cooldown:
                boss._aa_attack_active = False
                boss._aa_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._aa_attack_active = False
            boss._aa_attack_frame = 0
            active = False

        boss._aa_prev_timer = timer
        boss._aa_attack_progress = (
            min(1.0, getattr(boss, "_aa_attack_frame", 0)
                / max(1, cooldown - 1))
            if active else 0.0)

    def _resolve_state(boss, moving):
        """Pilih state animasi (prioritas: hurt > skill > attack > gerak)."""
        NS = _NS_ancient_apparition
        if not getattr(boss, "alive", True):
            return "death"
        if int(getattr(boss, "hurt_flash_timer", 0) or 0) > 3:
            return "hurt"
        skill = getattr(boss, "active_skill", None)
        if skill in ("q", "w", "e", "r"):
            return "cast_" + skill
        if getattr(boss, "_aa_attack_active", False):
            return "attack"
        speed = float(getattr(boss, "_moving_speed", None)
                      or getattr(boss, "_aa_speed", 0.0))
        if moving and speed > 1.35:
            return "run"
        if moving:
            return "walk"
        return "idle"

    # ===================================================================
    # GEOMETRI LENGAN (dipakai renderer + lapisan FX — satu sumber)
    # ===================================================================
    def arc_angle(progress, action, phase):
        """Sudut lengan depan (radian; 0 = depan, positif = naik).

        ANTICIPATION -> WIND-UP -> SWING -> FOLLOW -> RECOVERY: ayunan
        berbasis arc penuh (tidak ada teleport posisi awal ke akhir).
        """
        NS = _NS_ancient_apparition
        p = 0.0 if progress <= 0.0 else (1.0 if progress >= 1.0
                                         else progress)
        if action == "attack":
            if p < 0.20:                       # ANTICIPATION — tarik mundur
                return 0.35 + (-0.55 - 0.35) * NS._ease_in_out(p / 0.20)
            if p < 0.38:                       # WIND-UP — angkat ke belakang
                return -0.55 + (-1.62 - -0.55) * \
                    NS._ease_in_out((p - 0.20) / 0.18)
            if p < 0.55:                       # SWING — sapuan cepat
                return -1.62 + (0.55 - -1.62) * \
                    NS._ease_in((p - 0.38) / 0.17)
            if p < 0.75:                       # FOLLOW THROUGH
                return 0.55 + (0.75 - 0.55) * (p - 0.55) / 0.20
            return 0.75 + (0.35 - 0.75) * \
                NS._ease_out((p - 0.75) / 0.25)     # RECOVERY
        if action == "cast_w":                 # dua tangan mendorong depan
            return 0.05 + math.sin(phase * 26.0) * 0.03
        if action == "cast_e":                 # gather di dada
            return -0.12
        if action == "cast_q":                 # menyalurkan vortex
            return 0.28
        if action == "cast_r":                 # ULT: kedua tangan terangkat
            return 1.85
        if action == "run":
            return 0.15 + math.sin(phase * 5.2) * 0.5
        if action == "walk":
            return 0.35 + math.sin(phase * 2.6) * 0.22
        return 0.35 + math.sin(phase * 0.7) * 0.08

    def arm_geometry(facing, action, phase, progress=0.0):
        """(bahu, siku, tangan, ujung cakar) — offset px dari jangkar.

        Dipakai _rig_front_arm (//PIXEL) DAN heroes/ancient_apparition_fx
        (layar 1:1) supaya trail & asal shard menempel di cakar.
        """
        NS = _NS_ancient_apparition
        ang = NS.arc_angle(progress, action, phase)
        sx = NS.SHOULDER_OFF[0] * facing
        sy = NS.SHOULDER_OFF[1]
        bend = 0.55 if action == "attack" else 0.42
        ex = sx + math.cos(ang - bend) * NS.UPPER_LEN * facing
        ey = sy - math.sin(ang - bend) * NS.UPPER_LEN
        hx = ex + math.cos(ang) * NS.FORE_LEN * facing
        hy = ey - math.sin(ang) * NS.FORE_LEN
        tx = hx + math.cos(ang) * NS.CLAW_LEN * facing
        ty = hy - math.sin(ang) * NS.CLAW_LEN
        return ((sx, sy), (ex, ey), (hx, hy), (tx, ty))

    # ===================================================================
    # RIG PIXEL ART (buffer setengah resolusi -> upscale 2x chunky)
    # ===================================================================
    RIG_W = 64
    RIG_H = 76
    RIG_AX = 32            # jangkar low-res
    RIG_AY = 34

    def _rig_buffers():
        NS = _NS_ancient_apparition
        if NS._rig_lo is None:
            NS._rig_lo = pygame.Surface((NS.RIG_W, NS.RIG_H),
                                        pygame.SRCALPHA)
            NS._rig_px = pygame.Surface((NS.RIG_W * NS.PIXEL,
                                         NS.RIG_H * NS.PIXEL),
                                        pygame.SRCALPHA)
        return NS._rig_lo, NS._rig_px

    # ----------------------------- SKIRT -----------------------------
    def _rig_skirt(buf, phase, action, lean):
        """Jubah shard mengambang: massa + 6 shard hem bergantian.

        WALK: shard hem kiri/kanan menendang bergantian (foot timing),
        hem bergoyang; RUN: amplitude lebih besar dan condong.
        """
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ax, ay = NS.RIG_AX, NS.RIG_AY
        f = 1.6 if action in ("run",) else (1.0 if action in ("walk",)
                                            else 0.6)
        sway = math.sin(phase * (2.6 if action != "idle" else 0.7)) * f

        # massa utama (panggul)
        pygame.draw.polygon(buf, P["shadow_ice"], [
            (ax - 11, ay + 2), (ax + 11, ay + 2),
            (ax + 9, ay + 13), (ax - 9, ay + 13)])
        pygame.draw.polygon(buf, P["ice_darkest"], [
            (ax - 10, ay + 2), (ax + 10, ay + 2),
            (ax + 8, ay + 12), (ax - 8, ay + 12)])
        pygame.draw.polygon(buf, P["ice_dark"], [
            (ax - 8, ay + 3), (ax + 8, ay + 3),
            (ax + 6, ay + 11), (ax - 6, ay + 11)])
        pygame.draw.polygon(buf, P["ice_mid"], [
            (ax - 5, ay + 4), (ax + 5, ay + 4),
            (ax + 4, ay + 9), (ax - 4, ay + 9)])
        # garis facet vertikal
        for lx in (-4, 0, 4):
            pygame.draw.line(buf, P["ice_light"],
                             (ax + lx, ay + 4), (ax + lx, ay + 9), 1)

        # shard hem bergantian (kiri & kanan berlawanan fase = langkah)
        hem = ((-10, 6, 0), (-6, 9, math.pi), (-2, 7, 0),
               (2, 10, math.pi), (6, 8, 0), (10, 6, math.pi))
        for off, hgt, ph_off in hem:
            kick = math.sin(phase * 2.6 + ph_off) * (2.0 * f)
            bx = ax + off + int(kick + sway * off * 0.12)
            top = ay + 11
            tipx = bx + int(kick * 0.6 + lean * 0.5)
            tipy = top + hgt + (1 if math.sin(phase * 2.6 + ph_off) > 0
                                else 0)
            pygame.draw.polygon(buf, P["shadow_deep"], [
                (bx - 2 + 1, top + 1), (bx + 2 + 1, top + 1),
                (tipx + 1, tipy + 1)])
            pygame.draw.polygon(buf, P["ice_darkest"], [
                (bx - 2, top), (bx + 2, top), (tipx, tipy)])
            pygame.draw.polygon(buf, P["ice_dark"], [
                (bx - 1, top), (bx + 1, top), (tipx, tipy - 1)])
            pygame.draw.line(buf, P["ice_bright"],
                             (bx, top + 1), (tipx, tipy - 1), 1)
            buf.set_at((int(tipx), int(tipy) - 1), P["ice_hot"])

    # ----------------------------- TORSO -----------------------------
    def _rig_torso(buf, phase, action, core_hot):
        """Dada kristal heksagonal + inti menyala + pauldron."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ax, ay = NS.RIG_AX, NS.RIG_AY
        # torso heksagonal
        pygame.draw.polygon(buf, P["shadow_ice"], [
            (ax - 9, ay - 9), (ax + 9, ay - 9), (ax + 11, ay - 1),
            (ax + 6, ay + 3), (ax - 6, ay + 3), (ax - 11, ay - 1)])
        pygame.draw.polygon(buf, P["ice_darkest"], [
            (ax - 8, ay - 8), (ax + 8, ay - 8), (ax + 10, ay - 1),
            (ax + 5, ay + 2), (ax - 5, ay + 2), (ax - 10, ay - 1)])
        pygame.draw.polygon(buf, P["ice_dark"], [
            (ax - 6, ay - 7), (ax + 6, ay - 7), (ax + 8, ay - 1),
            (ax + 4, ay + 1), (ax - 4, ay + 1), (ax - 8, ay - 1)])
        # inti dada (jantung es) — denyut
        pulse = 0.7 + 0.3 * math.sin(phase * 1.5)
        core = P["ice_bright"] if core_hot else P["ice_light"]
        pygame.draw.rect(buf, P["shadow_deep"], (ax - 2, ay - 4, 4, 4))
        pygame.draw.rect(buf, core, (ax - 2, ay - 4, 3, 3))
        buf.set_at((ax - 1, ay - 3), P["ice_hot"])
        if core_hot or pulse > 0.85:
            buf.set_at((ax, ay - 3), P["ice_pure"])
        # facet diagonal
        pygame.draw.line(buf, P["ice_mid"], (ax - 6, ay - 6),
                         (ax - 3, ay + 1), 1)
        pygame.draw.line(buf, P["ice_mid"], (ax + 6, ay - 6),
                         (ax + 3, ay + 1), 1)
        pygame.draw.line(buf, P["ice_bright"], (ax - 5, ay - 6),
                         (ax - 4, ay - 3), 1)

        # pauldron (armor bahu): 3 paku per sisi
        for side in (-1, 1):
            base = [(ax + side * 8, ay - 8), (ax + side * 12, ay - 9),
                    (ax + side * 10, ay - 5)]
            pygame.draw.polygon(buf, P["ice_darkest"], base)
            pygame.draw.polygon(buf, P["ice_dark"], [
                (ax + side * 8, ay - 8), (ax + side * 11, ay - 9),
                (ax + side * 9, ay - 6)])
            for i, (dx, dy, hgt) in enumerate(((9, -9, 4), (11, -8, 6),
                                               (10, -6, 3))):
                bx = ax + side * dx
                by = ay + dy
                pygame.draw.polygon(buf, P["ice_mid"], [
                    (bx - 1, by), (bx + 1, by), (bx, by - hgt)])
                buf.set_at((bx, by - hgt), P["ice_hot"])

    # ----------------------------- HEAD ------------------------------
    def _rig_head(buf, phase, tilt, facing, hurt):
        """Kepala berhood berongga: wajah glow, mata menyala, dagu shard."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ax = NS.RIG_AX + int(tilt)
        ay = NS.RIG_AY - 13 + (1 if math.sin(phase * 0.8) > 0.4 else 0)
        breath = 1 if math.sin(phase * 1.6) > 0.2 else 0

        # hood
        pygame.draw.polygon(buf, P["ice_darkest"], [
            (ax - 6, ay - 6), (ax + 6, ay - 6), (ax + 8, ay),
            (ax + 7, ay + 5), (ax - 7, ay + 5), (ax - 8, ay)])
        pygame.draw.polygon(buf, P["ice_dark"], [
            (ax - 5, ay - 5), (ax + 5, ay - 5), (ax + 7, ay),
            (ax + 6, ay + 4), (ax - 6, ay + 4), (ax - 7, ay)])
        # puncak hood melengkung (breathing)
        pygame.draw.polygon(buf, P["ice_mid"], [
            (ax - 3, ay - 5), (ax + 3, ay - 5), (ax, ay - 7 - breath)])
        # wajah berongga
        pygame.draw.rect(buf, P["shadow_deep"], (ax - 4, ay - 3, 8, 6))
        pygame.draw.rect(buf, P["face_dark"], (ax - 3, ay - 2, 6, 4))
        # mata menyala (pixel 1x2, flicker)
        flick = 0 if hurt else (1 if math.sin(phase * 7.0) > 0.93 else 0)
        for side in (-1, 1):
            ex = ax + side * 2
            buf.set_at((ex, ay - 1), P["face_hot"])
            buf.set_at((ex, ay), P["face_bright"] if not flick
                       else P["white"])
        # mulut berongga glow
        pygame.draw.rect(buf, P["face_mid"], (ax - 1, ay + 2, 2, 1))
        # duri hood samping
        for side in (-1, 1):
            pygame.draw.polygon(buf, P["ice_darkest"], [
                (ax + side * 7, ay - 3), (ax + side * 10, ay - 5),
                (ax + side * 8, ay - 1)])
            pygame.draw.line(buf, P["ice_bright"],
                             (ax + side * 7, ay - 3),
                             (ax + side * 9, ay - 4), 1)
        # dagu shard
        pygame.draw.polygon(buf, P["ice_dark"], [
            (ax - 1, ay + 5), (ax + 1, ay + 5), (ax, ay + 8)])
        buf.set_at((ax, ay + 7), P["ice_bright"])

    # ----------------------------- CROWN -----------------------------
    def _rig_crown(buf, phase, flare):
        """Mahkota es: 5 paku tinggi, ujung menyala, bergoyang halus."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ax = NS.RIG_AX
        ay = NS.RIG_AY - 19      # puncak hood
        sway = int(math.sin(phase * 0.9) * 1)
        spikes = ((0, 13), (-3, 10), (3, 10), (-6, 8), (6, 8))
        for off, hgt in spikes:
            bx = ax + off + (sway if abs(off) > 3 else sway // 2)
            tip = (bx + (1 if off > 0 else -1 if off < 0 else 0)
                   + sway // 2, ay - hgt)
            pygame.draw.polygon(buf, P["shadow_deep"], [
                (bx - 2 + 1, ay + 1), (bx + 2 + 1, ay + 1),
                (tip[0] + 1, tip[1] + 1)])
            pygame.draw.polygon(buf, P["ice_darkest"], [
                (bx - 2, ay), (bx + 2, ay), tip])
            pygame.draw.polygon(buf, P["ice_dark"], [
                (bx - 1, ay), (bx + 1, ay), (tip[0], tip[1] + 1)])
            pygame.draw.line(buf, P["ice_bright"], (bx, ay),
                             (tip[0], tip[1] + 1), 1)
            buf.set_at((int(tip[0]), int(tip[1])),
                       P["ice_pure"] if flare else P["ice_hot"])

    # ----------------------------- ARMS ------------------------------
    def _rig_arm(buf, facing, action, phase, progress, back):
        """Satu lengan kristal: lengan atas + bawah + cakar 3 jari."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ax, ay = NS.RIG_AX, NS.RIG_AY
        if back:
            facing = -facing
            phase = phase + math.pi          # fase berlawanan
            if action == "attack":
                action = "idle"              # lengan belakang santai
            elif action.startswith("cast_") and action != "cast_r":
                action = "idle"
            progress = 0.0
        (sx, sy), (ex, ey), (hx, hy), (tx, ty) = NS.arm_geometry(
            facing, action, phase, progress)
        dark = P["ice_darkest"] if back else P["ice_dark"]
        mid = P["ice_dark"] if back else P["ice_mid"]
        bri = P["ice_mid"] if back else P["ice_bright"]

        def seg(x1, y1, x2, y2, w):
            pygame.draw.line(buf, dark, (x1 // 2 + ax, y1 // 2 + ay),
                             (x2 // 2 + ax, y2 // 2 + ay), w)

        # lengan atas & bawah (lebar 3 px low-res = 6 px chunky)
        seg(sx, sy, ex, ey, 3)
        seg(ex, ey, hx, hy, 3)
        # highlight atas lengan
        pygame.draw.line(buf, mid,
                         (sx // 2 + ax, sy // 2 + ay - 1),
                         (ex // 2 + ax, ey // 2 + ay - 1), 1)
        pygame.draw.line(buf, mid,
                         (ex // 2 + ax, ey // 2 + ay - 1),
                         (hx // 2 + ax, hy // 2 + ay - 1), 1)
        # telapak
        px_, py_ = int(hx // 2 + ax), int(hy // 2 + ay)
        pygame.draw.rect(buf, dark, (px_ - 1, py_ - 1, 3, 3))
        buf.set_at((px_, py_), mid)
        # cakar 3 jari mengarah ujung
        ang = math.atan2(-(ty - hy), (tx - hx) * facing)
        for da in (-0.45, 0.0, 0.45):
            fx = px_ + int(math.cos(ang + da) * 3 * facing)
            fy = py_ - int(math.sin(ang + da) * 3)
            pygame.draw.line(buf, bri, (px_, py_), (fx, fy), 1)
            buf.set_at((fx, fy), P["ice_hot"] if not back
                       else P["ice_mid"])

    # --------------------------- ORBIT -------------------------------
    def _rig_orbit(buf, phase, action, progress, facing):
        """3 splinter es mengorbit — sumber visual shard basic attack."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ax, ay = NS.RIG_AX, NS.RIG_AY
        base_r = 21
        for i in range(3):
            spd = (1.1, -0.8, 1.6)[i]
            r = base_r + (3, -2, 5)[i] + int(math.sin(phase * 1.3 + i) * 2)
            ang = phase * spd + i * math.tau / 3.0
            oy = ay - 4 + (i - 1) * 5 + int(math.sin(phase + i * 2) * 2)
            ox = ax + int(math.cos(ang) * r)
            # saat menyerang, splinter depan menyusul tangan (maju)
            if action == "attack" and 0.3 < progress < 0.6 and i == 2:
                ox += int(6 * facing)
            ln = 4 + (i % 2) * 2
            dx_, dy_ = math.cos(ang + math.pi / 2), math.sin(ang
                                                             + math.pi / 2)
            pygame.draw.line(buf, P["ice_darkest"],
                             (ox - int(dx_ * ln), oy - int(dy_ * ln)),
                             (ox + int(dx_ * ln), oy + int(dy_ * ln)), 2)
            pygame.draw.line(buf, P["ice_light"],
                             (ox - int(dx_ * (ln - 1)),
                              oy - int(dy_ * (ln - 1))),
                             (ox + int(dx_ * (ln - 1)),
                              oy + int(dy_ * (ln - 1))), 1)
            buf.set_at((ox + int(dx_ * ln), oy + int(dy_ * ln)),
                       P["ice_hot"])

    # ------------------------ MASTERWORK (full-res) ------------------
    def _masterwork_finish(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """Pass detail full-res: halo mata, glow inti, glint mahkota."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        flick = 0.5 + 0.5 * math.sin(phase * 7.0)
        cast = action.startswith("cast_")
        hot = 1.35 if cast else 1.0
        # halo mata (dua titik glow kecil)
        for side in (-1, 1):
            ex = cx + int(tilt_head(phase)) + side * 4
            ey = cy - 27
            NS._aacircle(surface, (*P["face_dark"], int(110 * hot)),
                         (ex, ey), 4)
            NS._aacircle(surface, (*P["face_bright"], int(60 * hot * flick)),
                         (ex, ey), 6)
        # glow inti dada
        pulse = 0.7 + 0.3 * math.sin(phase * 1.5)
        NS._aacircle(surface, (*P["ice_light"], int(120 * pulse * hot)),
                     (cx, cy - 1), 7)
        NS._aacircle(surface, (*P["ice_hot"], int(70 * pulse * hot)),
                     (cx, cy - 1), 4)
        # glint ujung mahkota (2 titik berkedip)
        for off, k in ((0, 0), (-5, 2), (5, 3)):
            gx = cx + off
            gy = cy - 47 - (9 if off == 0 else 6)
            tw = 0.5 + 0.5 * math.sin(phase * 3.0 + k * 1.7)
            NS._aacircle(surface, (*P["ice_hot"], int(150 * tw)),
                         (gx, gy), 2)
        # rim kiri-atas: 3 piksel terang di tepi hood/torso
        pygame.draw.line(surface, P["ice_bright"],
                         (cx - 9, cy - 30), (cx - 8, cy - 27), 1)
        pygame.draw.line(surface, P["ice_bright"],
                         (cx - 12, cy - 12), (cx - 11, cy - 9), 1)
        del cast

    # ===================================================================
    # BODY RENDER (komposit: rig chunky + outline + lighting)
    # ===================================================================
    def _draw_aa_body(surface, cx, cy, facing, phase, action,
                      attack_progress=0):
        """Komposit ORIGINAL-MAX: buffer tetap + outline + lighting."""
        _composite_boss_body(
            surface, _NS_ancient_apparition,
            _NS_ancient_apparition._draw_aa_body_raw,
            cx, cy, facing, phase, action, attack_progress,
            rim_add=(150, 225, 255), bsize=200)

    def _draw_aa_body_raw(surface, cx, cy, facing, phase, action,
                          attack_progress=0):
        """Rig pixel art: low-res -> upscale 2x -> blit pada jangkar."""
        NS = _NS_ancient_apparition
        hurt = action == "hurt"
        ap = attack_progress if action == "attack" else 0.0
        ph = NS._attack_phase(ap) if ap > 0 else ""

        # ── bob & lean per state ──
        if action == "walk":
            bob = -abs(int(math.sin(phase * 2.6) * 2))
            lean = 1
        elif action == "run":
            bob = -abs(int(math.sin(phase * 5.2) * 3))
            lean = 3
        elif action == "attack":
            if ph == "anticipation":
                bob = -1
                lean = -2
            elif ph == "windup":
                bob = 1
                lean = -3
            elif ph == "swing":
                bob = -1
                lean = 5
            elif ph == "follow":
                bob = 0
                lean = 6
            else:
                bob = 0
                lean = 2
        elif action.startswith("cast_"):
            bob = -int(abs(math.sin(phase * 1.2)) * 2)
            lean = 2 if action != "cast_r" else 0
        else:
            bob = -int(abs(math.sin(phase * 0.8)) * 1)   # breathing
            lean = 0
        if hurt:
            lean = -2
            bob = 0

        lo, px = NS._rig_buffers()
        lo.fill((0, 0, 0, 0))
        core_hot = action.startswith("cast_") or \
            (ap > 0.35 and ap < 0.6)
        tilt = (2 if hurt else 0) + (1 if ph == "swing" else 0)

        # URUTAN LAYER RIG (back -> front)
        NS._rig_arm(lo, facing, action, phase, ap, back=True)
        NS._rig_orbit(lo, phase, action, ap, facing)
        NS._rig_skirt(lo, phase, action, lean)
        NS._rig_torso(lo, phase, action, core_hot)
        NS._rig_head(lo, phase, tilt, facing, hurt)
        NS._rig_crown(lo, phase, core_hot)
        NS._rig_arm(lo, facing, action, phase, ap, back=False)

        # upscale 2x nearest-neighbor -> piksel chunky keras
        pygame.transform.scale(lo, px.get_size(), px)
        ox = int(cx) - NS.RIG_AX * NS.PIXEL
        oy = int(cy) - NS.RIG_AY * NS.PIXEL + bob * NS.PIXEL
        surface.blit(px, (ox, oy))

        # pass detail full-res (glow/glint) pada posisi yang sama
        NS._masterwork_finish(surface, cx + lean, cy + bob, facing, phase,
                              action, attack_progress)

    # ===================================================================
    # CANVAS PROJECTILE SYSTEM (fallback tanpa lapisan hidup)
    # ===================================================================
    class IceShardProjectile:
        """Cold Touch kecil — cepat, homing ringan (canvas space).

        Bidang lengkap: position/velocity/speed/damage/lifetime/target/
        radius/rotation/trail/particles/active.
        """
        SPEED = 7.5

        def __init__(self, sx, sy, tx, ty, target=None):
            self.position = [float(sx), float(sy)]
            self.tx, self.ty = float(tx), float(ty)
            dx, dy = float(tx) - sx, float(ty) - sy
            d = max(1.0, math.hypot(dx, dy))
            self.velocity = [dx / d * self.SPEED, dy / d * self.SPEED]
            self.speed = float(self.SPEED)
            self.damage = 0
            self.lifetime = 90.0
            self.age = 0.0
            self.target = target
            self.radius = 4
            self.rotation = math.atan2(dy, dx)
            self.trail = []
            self.particles = True
            self.alive = True

        def update(self, dt=1.0 / 60.0):
            self.age += dt
            if self.age > self.lifetime:
                self.alive = False
                return
            # target tracking: titik tujuan mengikuti target hidup
            if self.target is not None and getattr(self.target, "alive",
                                                   True):
                tx = getattr(self.target, "x", None)
                ty = getattr(self.target, "y", None)
                if tx is not None and ty is not None:
                    self.tx, self.ty = float(tx), float(ty)
            dx = self.tx - self.position[0]
            dy = self.ty - self.position[1]
            dist = math.hypot(dx, dy)
            if dist < self.speed + 4:
                self.alive = False
                return
            self.trail.append((int(self.position[0]), int(self.position[1])))
            if len(self.trail) > 8:
                self.trail.pop(0)
            self.position[0] += dx / dist * self.speed
            self.position[1] += dy / dist * self.speed
            self.rotation = math.atan2(dy, dx)

        def draw(self, surface, phase):
            NS = _NS_ancient_apparition
            P = NS.PALETTE
            for i, (tx, ty) in enumerate(self.trail):
                a = int(60 + i * 14)
                r = max(1, 3 - (len(self.trail) - i))
                NS._aacircle(surface, (*P["ice_dark"], a), (tx, ty), r + 1)
                NS._aacircle(surface, (*P["ice_light"], a), (tx, ty),
                             max(1, r - 1))
            if not self.alive:
                return
            px, py = int(self.position[0]), int(self.position[1])
            dx, dy = math.cos(self.rotation), math.sin(self.rotation)
            pxp, pyp = -dy, dx
            shard = [(px + int(dx * 8), py + int(dy * 8)),
                     (px + int(pxp * 4), py + int(pyp * 4)),
                     (px - int(dx * 5), py - int(dy * 5)),
                     (px - int(pxp * 4), py - int(pyp * 4))]
            NS._poly(surface, P["ice_darkest"], shard)
            NS._poly(surface, P["ice_mid"], [
                (p[0] - dx * 2, p[1] - dy * 2) for p in shard[:3]])
            NS._aaline(surface, P["ice_pure"],
                       (px + int(dx * 6), py + int(dy * 6)),
                       (px - int(dx * 3), py - int(dy * 3)), 1)
            NS._aacircle(surface, (*P["ice_light"], 110), (px, py), 9)
            NS._aacircle(surface, (*P["ice_bright"], 70), (px, py), 5)

    class IceBoltProjectile:
        """Ice Blast (E) — bolt besar lambat + shard pengorbit."""
        SPEED = 5.0

        def __init__(self, sx, sy, tx, ty, target=None):
            self.position = [float(sx), float(sy)]
            self.tx, self.ty = float(tx), float(ty)
            dx, dy = float(tx) - sx, float(ty) - sy
            d = max(1.0, math.hypot(dx, dy))
            self.velocity = [dx / d * self.SPEED, dy / d * self.SPEED]
            self.speed = float(self.SPEED)
            self.damage = 0
            self.lifetime = 140.0
            self.age = 0.0
            self.target = target
            self.radius = 8
            self.rotation = math.atan2(dy, dx)
            self.trail = []
            self.particles = True
            self.alive = True

        def update(self, dt=1.0 / 60.0):
            self.age += dt
            if self.age > self.lifetime:
                self.alive = False
                return
            dx = self.tx - self.position[0]
            dy = self.ty - self.position[1]
            dist = math.hypot(dx, dy)
            if dist < self.speed + 6:
                self.alive = False
                return
            self.trail.append((int(self.position[0]), int(self.position[1])))
            if len(self.trail) > 12:
                self.trail.pop(0)
            self.position[0] += dx / dist * self.speed
            self.position[1] += dy / dist * self.speed

        def draw(self, surface, phase):
            NS = _NS_ancient_apparition
            P = NS.PALETTE
            for i, (tx, ty) in enumerate(self.trail):
                a = int(50 + i * 13)
                r = max(1, 5 - (len(self.trail) - i))
                NS._aacircle(surface, (*P["ice_dark"], a), (tx, ty), r + 2)
                NS._aacircle(surface, (*P["ice_mid"], a), (tx, ty), r)
            if not self.alive:
                return
            px, py = int(self.position[0]), int(self.position[1])
            dx, dy = math.cos(self.rotation), math.sin(self.rotation)
            pxp, pyp = -dy, dx
            shard = [(px + int(dx * 14), py + int(dy * 14)),
                     (px + int(pxp * 7), py + int(pyp * 7)),
                     (px - int(dx * 9), py - int(dy * 9)),
                     (px - int(pxp * 7), py - int(pyp * 7))]
            NS._poly(surface, P["shadow_deep"],
                     [(p[0] + 2, p[1] + 2) for p in shard])
            NS._poly(surface, P["ice_darkest"], shard)
            NS._poly(surface, P["ice_dark"], [
                (p[0] - dx * 2, p[1] - dy * 2) for p in shard])
            NS._poly(surface, P["ice_mid"], [
                (p[0] - dx * 5, p[1] - dy * 5) for p in shard[:3]])
            NS._aaline(surface, P["ice_pure"],
                       (px + int(dx * 12), py + int(dy * 12)),
                       (px - int(dx * 6), py - int(dy * 6)), 1)
            NS._aacircle(surface, (*P["ice_light"], 130), (px, py), 15)
            NS._aacircle(surface, (*P["ice_bright"], 90), (px, py), 9)
            for i in range(3):
                ang = phase * 3 + i * math.tau / 3.0
                ox = px + int(math.cos(ang) * 12)
                oy = py + int(math.sin(ang) * 12)
                NS._draw_snowflake(surface, ox, oy, 2, 190, rotate=phase)

    class FrostBeam:
        """Chilling Touch (W) — beam gerigi bergerak (canvas fallback)."""
        def __init__(self, sx, sy, tx, ty, life=45):
            self.sx, self.sy = int(sx), int(sy)
            self.tx, self.ty = int(tx), int(ty)
            self.life = life
            self.age = 0
            self.alive = True
            self.rotation = math.atan2(self.ty - self.sy,
                                       self.tx - self.sx)

        def update(self, dt=1.0 / 60.0):
            self.age += 1
            if self.age >= self.life:
                self.alive = False

        def draw(self, surface, phase):
            NS = _NS_ancient_apparition
            P = NS.PALETTE
            t = self.age / self.life
            a_scale = t / 0.15 if t < 0.15 else (
                1.0 - (t - 0.7) / 0.3 if t > 0.7 else 1.0)
            dx = self.tx - self.sx
            dy = self.ty - self.sy
            dist = math.hypot(dx, dy)
            if dist < 1 or a_scale <= 0:
                return
            dx /= dist
            dy /= dist
            pxp, pyp = -dy, dx
            steps = int(dist / 7)
            for i in range(steps):
                tp = i / max(1, steps - 1)
                bx = self.sx + dx * dist * tp
                by = self.sy + dy * dist * tp
                wave = math.sin(phase * 6 + tp * 14) * 3.5
                fx = int(bx + pxp * wave)
                fy = int(by + pyp * wave)
                a = int(200 * a_scale * (1.0 - tp * 0.35))
                w = int(4 + 2 * math.sin(math.pi * tp))
                NS._aacircle(surface, (*P["ice_dark"], a), (fx, fy), w + 2)
                NS._aacircle(surface, (*P["ice_mid"], a), (fx, fy), w)
                NS._aacircle(surface, (*P["ice_hot"], a), (fx, fy),
                             max(1, w - 2))
                if i % 2 == 0:
                    gx = int(fx + pxp * (w + 3))
                    gy = int(fy + pyp * (w + 3))
                    ex = int(gx + pxp * 4 + dx * (2 if i % 4 == 0 else -2))
                    ey = int(gy + pyp * 4 + dy * (2 if i % 4 == 0 else -2))
                    NS._aaline(surface, (*P["ice_bright"], a), (gx, gy),
                               (ex, ey), 1)
            for i in range(7):
                tp = (phase * 0.35 + i * 0.15) % 1.0
                sx = int(self.sx + dx * dist * tp)
                sy = int(self.sy + dy * dist * tp)
                NS._draw_snowflake(surface, sx + int(pxp * 7),
                                   sy + int(pyp * 7), 2,
                                   int(220 * a_scale),
                                   rotate=phase * 2 + i)

    # ===================================================================
    # STATE MANAGEMENT + SPAWN
    # ===================================================================
    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_aa_projectiles"):
            boss._aa_projectiles = []
        if not hasattr(boss, "_aa_beams"):
            boss._aa_beams = []
        for proj in boss._aa_projectiles:
            proj.update()
            proj.draw(surface, phase)
        boss._aa_projectiles = [p for p in boss._aa_projectiles
                                if p.alive or p.age < 0.08]
        for beam in boss._aa_beams:
            beam.update()
            beam.draw(surface, phase)
        boss._aa_beams = [b for b in boss._aa_beams if b.alive]

    def _spawn_ice_shard(boss, sx, sy, tx, ty):
        # Saat Ancient Apparition DIMAINKAN sebagai hero, basic attack
        # menembakkan homing shard dari sistem Hero — shard internal
        # canvas ini dimatikan supaya tidak dobel (lihat _entity.py).
        if getattr(boss, "_aa_hero_basic_shard", False):
            return
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_aa_projectiles"):
            boss._aa_projectiles = []
        boss._aa_projectiles.append(
            _NS_ancient_apparition.IceShardProjectile(
                sx, sy, tx, ty, target=getattr(boss, "target", None)))

    def _spawn_ice_bolt(boss, sx, sy, tx, ty):
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_aa_projectiles"):
            boss._aa_projectiles = []
        boss._aa_projectiles.append(
            _NS_ancient_apparition.IceBoltProjectile(
                sx, sy, tx, ty, target=getattr(boss, "target", None)))

    def _spawn_frost_beam(boss, sx, sy, tx, ty):
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        if not hasattr(boss, "_aa_beams"):
            boss._aa_beams = []
        boss._aa_beams.append(
            _NS_ancient_apparition.FrostBeam(sx, sy, tx, ty, life=45))

    # ===================================================================
    # GROUND FX + SHADOW
    # ===================================================================
    def _draw_shadow(surface, x, y, lift=0):
        """Bayangan reaktif: mengecil saat terangkat, dasar menapak."""
        NS = _NS_ancient_apparition
        if NS._shadow_cache is None:
            shadow = pygame.Surface((110, 22), pygame.SRCALPHA)
            for radius in range(11, 0, -1):
                alpha = max(0, (11 - radius) * 15)
                pygame.draw.ellipse(
                    shadow, (0, 0, 0, alpha),
                    (11 - radius, 11 - radius, 88 + radius * 2,
                     radius * 2))
            pygame.draw.ellipse(shadow,
                                (*NS.PALETTE["ice_dark"], 80),
                                (10, 5, 90, 12))
            NS._shadow_cache = shadow
        spr = NS._shadow_cache
        w, h = spr.get_size()
        if lift:
            k = max(0.12, 1.0 - lift * 0.05)
            w = max(6, int(w * k))
            h = max(2, int(h * k))
            spr = pygame.transform.smoothscale(spr, (w, h))
        bx = x - w // 2
        by = (y + 11) - h
        surface.blit(spr, (bx, by))
        if NS._record_shadow is not None:
            NS._record_shadow.append(pygame.Rect(bx, by, w, h))

    def _draw_frost_aura(surface, x, y, phase, active_skill):
        """Aura dingin halus di belakang badan (cached)."""
        NS = _NS_ancient_apparition
        if NS._aura_cache is None:
            aura = pygame.Surface((200, 180), pygame.SRCALPHA)
            for radius in range(80, 5, -4):
                alpha = int((80 - radius) * 1.15)
                if alpha > 0:
                    NS._aacircle(
                        aura,
                        (*NS.PALETTE["ice_darkest"], min(255, alpha)),
                        (100, 90), radius)
            NS._aura_cache = aura
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.4 if active_skill in ("q", "w", "e", "r") else 1.0
        spr = NS._aura_cache
        spr.set_alpha(int(255 * max(0.15, min(1.0, pulse * strength))))
        surface.blit(spr, (x - 100, y - 90))

    def _draw_ground_frost(surface, x, y, phase, active_skill):
        """Platform beku di bawah kaki (cached) + denyut skill."""
        NS = _NS_ancient_apparition
        if NS._ground_cache is None:
            ring = pygame.Surface((140, 46), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_dark"], 160),
                                (5, 10, 130, 26), 3)
            pygame.draw.ellipse(ring, (*NS.PALETTE["ice_mid"], 190),
                                (20, 14, 100, 18), 2)
            for i in range(10):
                angle = i * math.pi / 5
                x1 = 70 + int(math.cos(angle) * 32)
                y1 = 23 + int(math.sin(angle) * 7)
                x2 = 70 + int(math.cos(angle) * 60)
                y2 = 23 + int(math.sin(angle) * 11)
                pygame.draw.line(
                    ring, (*NS.PALETTE["ice_bright"], 180),
                    (x1, y1), (x2, y2), 1)
            NS._ground_cache = ring
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        surface.blit(NS._ground_cache, (x - 70, y - 23 + 30))
        if active_skill:
            NS._ellipse(surface,
                        (*NS.PALETTE["ice_hot"], int(80 * pulse)),
                        (x - 55, y - 15 + 30, 110, 30), 1)

    def _draw_ice_wisps(surface, cx, cy, phase, trail=False, facing=1,
                        intense=False):
        """Mist beku + salju melayang (versi ringan; partikel hidup ada
        di lapisan FX — fungsi ini fallback canvas)."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        if NS._mist_cache is None:
            mist = pygame.Surface((140, 42), pygame.SRCALPHA)
            for radius in range(34, 3, -4):
                alpha = int((34 - radius) * 2.2)
                if alpha > 0:
                    pygame.draw.ellipse(
                        mist, (*P["frost_dark"], min(255, alpha)),
                        (70 - radius * 2, 21 - radius // 3,
                         radius * 4, max(3, radius // 2)))
            NS._mist_cache = mist
        strength = 1.4 if intense else 1.0
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        spr = NS._mist_cache
        spr.set_alpha(int(255 * min(1.0, pulse * strength)))
        surface.blit(spr, (cx - 70, cy - 10))
        for i, offset in enumerate((-16, 0, 16)):
            t = (phase * 0.55 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 26)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha > 0:
                NS._aacircle(surface, (*P["frost_dark"], alpha),
                             (sx, sy), 4)
                NS._aacircle(surface, (*P["ice_hot"], alpha),
                             (sx, sy - 3), 1)
        for i in range(3):
            t = (phase * 0.4 + i * 0.2) % 1.0
            angle = phase * 0.5 + i * math.tau / 5.0
            r = 22 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 9) - int(t * 8)
            alpha = int(210 * (1 - t * 0.5) * strength)
            NS._draw_snowflake(surface, sx, sy, 2,
                               max(0, min(255, alpha)),
                               rotate=phase + i)
        if trail:
            for i in range(3):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 130 - i * 25)
                NS._aacircle(surface, (*P["frost_mid"], alpha),
                             (sx, sy), max(2, 4 - i))

    # ===================================================================
    # ICE / SNOWFLAKE HELPERS (dipakai skill fallback)
    # ===================================================================
    def _draw_snowflake(surface, cx, cy, size=3, alpha=255, rotate=0):
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        for i in range(6):
            angle = rotate + i * math.pi / 3
            ex = cx + int(math.cos(angle) * size)
            ey = cy + int(math.sin(angle) * size)
            NS._aaline(surface, (*P["ice_hot"], alpha), (cx, cy),
                       (ex, ey), 1)
            mx = cx + int(math.cos(angle) * (size - 1))
            my = cy + int(math.sin(angle) * (size - 1))
            t1 = angle + math.pi / 2
            t2 = angle - math.pi / 2
            NS._aaline(surface, (*P["ice_bright"], alpha), (mx, my),
                       (mx + int(math.cos(t1)), my + int(math.sin(t1))), 1)
            NS._aaline(surface, (*P["ice_bright"], alpha), (mx, my),
                       (mx + int(math.cos(t2)), my + int(math.sin(t2))), 1)
        NS._aacircle(surface, (*P["ice_pure"], alpha), (cx, cy), 1)

    def _draw_frost_crystal_spike(surface, cx, base_y, tip_y, width=4,
                                  alpha=255, phase=0):
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        height = base_y - tip_y
        if height <= 0:
            return
        NS._poly(surface, (*P["shadow_deep"], alpha), [
            (cx - width + 1, base_y + 1), (cx + width + 1, base_y + 1),
            (cx + 1, tip_y + 1)])
        NS._poly(surface, (*P["ice_darkest"], alpha), [
            (cx - width, base_y), (cx + width, base_y), (cx, tip_y)])
        for i, ck in enumerate(("ice_dark", "ice_mid", "ice_light",
                                "ice_bright")):
            shrink = (i + 1) * 0.15
            w = int(width * (1 - shrink))
            NS._poly(surface, (*P[ck], alpha), [
                (cx - w, base_y - 1), (cx + w, base_y - 1),
                (cx, tip_y + int(height * shrink * 0.2))])
        NS._aaline(surface, (*P["ice_hot"], alpha),
                   (cx, base_y - 2), (cx, tip_y + 2), 1)
        NS._aacircle(surface, (*P["ice_pure"], alpha), (cx, tip_y + 1), 1)

    # ===================================================================
    # SWING TRAIL (canvas fallback — histori posisi cakar)
    # ===================================================================
    def _draw_swing_trail(surface, boss, x, y, facing, progress):
        """Ribbon sapuan cakar dari histori posisi (fallback canvas)."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        ph = NS._attack_phase(progress)
        if ph not in ("swing", "follow"):
            if hasattr(boss, "_aa_trail"):
                boss._aa_trail.clear()
            return
        if not hasattr(boss, "_aa_trail"):
            boss._aa_trail = []
        (_, _, hand, tip) = NS.arm_geometry(facing, "attack",
                                            getattr(boss, "pulse", 0.0),
                                            progress)
        boss._aa_trail.append((x + hand[0], y + hand[1],
                               x + tip[0], y + tip[1]))
        if len(boss._aa_trail) > 10:
            boss._aa_trail.pop(0)
        n = len(boss._aa_trail)
        if n < 2:
            return
        for i in range(n - 1):
            bx0, by0, tx0, ty0 = boss._aa_trail[i]
            bx1, by1, tx1, ty1 = boss._aa_trail[i + 1]
            k = i / max(1, n - 1)
            a = int(120 * (0.3 + 0.7 * k))
            ix0 = bx0 + (tx0 - bx0) * 0.3
            iy0 = by0 + (ty0 - by0) * 0.3
            ix1 = bx1 + (tx1 - bx1) * 0.3
            iy1 = by1 + (ty1 - by1) * 0.3
            NS._poly(surface, (*P["ice_mid"], a),
                     [(ix0, iy0), (ix1, iy1), (tx1, ty1), (tx0, ty0)])
            NS._aaline(surface, (*P["ice_hot"], int(a * 0.9)),
                       (tx0, ty0), (tx1, ty1), 1)

    # ===================================================================
    # CAST FLASH (canvas fallback)
    # ===================================================================
    def _draw_cast_flash(surface, x, y, facing, progress):
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        if progress < 0.32 or progress > 0.62:
            return
        t = (progress - 0.32) / 0.30
        intensity = math.sin(t * math.pi)
        (_, _, hand, tip) = NS.arm_geometry(facing, "attack",
                                            0.0, progress)
        fx = x + tip[0]
        fy = y + tip[1]
        alpha = int(220 * intensity)
        radius = int(5 + intensity * 11)
        NS._aacircle(surface, (*P["ice_dark"], 140 * intensity // 1),
                     (fx, fy), radius + 4)
        NS._aacircle(surface, (*P["ice_mid"], alpha), (fx, fy), radius + 2)
        NS._aacircle(surface, (*P["ice_bright"], alpha), (fx, fy), radius)
        NS._aacircle(surface, (*P["ice_hot"], alpha), (fx, fy),
                     max(1, radius - 2))
        NS._aacircle(surface, (*P["ice_pure"], alpha), (fx, fy),
                     max(1, radius - 4))
        for i in range(5):
            ang = i * math.tau / 5 + progress * 6.0
            ex = fx + int(math.cos(ang) * radius * 1.5)
            ey = fy + int(math.sin(ang) * radius * 1.5)
            NS._draw_snowflake(surface, ex, ey, 2, alpha,
                               rotate=progress * 5)

    # ===================================================================
    # SKILL Q: ICE VORTEX (ground + foreground, canvas fallback)
    # ===================================================================
    def _draw_ice_vortex_ground(surface, boss, x, y, timer, phase):
        """Riak tanah di bawah vortex."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for i in range(4):
            r = int(15 + i * 12 + progress * 20
                    + math.sin(phase * 2 + i) * 3)
            NS._ellipse(surface, (*P["ice_dark"], int(150 * pulse)),
                        (tx - r, ty - r // 3, r * 2, r // 1.5), 2)
            NS._ellipse(surface, (*P["ice_mid"], int(100 * pulse)),
                        (tx - r + 3, ty - r // 3 + 2, r * 2 - 6,
                         r // 1.5 - 4), 1)

    def _draw_ice_vortex(surface, boss, x, y, timer, phase):
        """Tornado es berputar di target (fallback canvas)."""
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.15:
            return
        if progress < 0.5:
            height = int(60 * (progress - 0.15) / 0.35)
        else:
            height = int(60 * (1 - (progress - 0.85) / 0.15)) \
                if progress > 0.85 else 60
        if height <= 0:
            return
        max_width = 28
        ring_count = height // 3
        for i in range(ring_count):
            h_ratio = i / max(1, ring_count)
            y_offset = -int(h_ratio * height)
            width = int(max_width * (1 - h_ratio * 0.4))
            rotation = phase * 4 + h_ratio * 8
            for j in range(8):
                a1 = rotation + j * math.pi / 4
                a2 = a1 + 0.5
                x1 = tx + int(math.cos(a1) * width)
                y1 = ty + y_offset + int(math.sin(a1) * width * 0.3)
                x2 = tx + int(math.cos(a2) * width)
                y2 = ty + y_offset + int(math.sin(a2) * width * 0.3)
                alpha = int(200 * (1 - h_ratio * 0.3))
                NS._aaline(surface, (*P["ice_dark"], alpha),
                           (x1, y1), (x2, y2), 3)
                NS._aaline(surface, (*P["ice_bright"], alpha),
                           (x1, y1), (x2, y2), 1)
            for j in range(3):
                sa = rotation + j * math.tau / 3
                sx = tx + int(math.cos(sa) * width)
                sy = ty + y_offset + int(math.sin(sa) * width * 0.3)
                NS._aacircle(surface, (*P["ice_hot"], 220), (sx, sy), 3)
                NS._aacircle(surface, (*P["ice_pure"], 250), (sx, sy), 1)
        for i in range(6):
            angle = phase * 2 + i * math.pi / 3
            r = max_width - 3
            sx = tx + int(math.cos(angle) * r)
            sy = ty - height // 2 + int(math.sin(angle) * 15)
            NS._draw_snowflake(surface, sx, sy, 3, 230,
                               rotate=phase * 3)
        NS._ellipse(surface, (*P["ice_bright"], 180),
                    (tx - max_width, ty - max_width // 3,
                     max_width * 2, max_width // 1.5), 2)

    # ===================================================================
    # SKILL R: COLD FEET (ground telegraph + erupsi, canvas fallback)
    # ===================================================================
    def _draw_cold_feet_ground(surface, boss, x, y, timer, phase):
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        if progress < 0.4:
            radius = int(40 + progress * 20)
            NS._ellipse(surface, (*P["ice_dark"], int(200 * pulse)),
                        (tx - radius, ty - radius // 3, radius * 2,
                         radius // 1.5), 3)
            NS._ellipse(surface, (*P["ice_mid"], int(150 * pulse)),
                        (tx - radius + 4, ty - radius // 3 + 2,
                         radius * 2 - 8, radius // 1.5 - 4), 2)

    def _draw_cold_feet_spikes(surface, boss, x, y, timer, phase):
        NS = _NS_ancient_apparition
        P = NS.PALETTE
        tx, ty = NS._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            for i in range(8):
                angle = phase * 2 + i * math.pi / 4
                r = 60 * (1 - progress / 0.3)
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.5)
                NS._draw_snowflake(surface, sx, sy, 3, 200,
                                   rotate=phase * 4)
            return
        erupt_t = min(1.0, (progress - 0.3) / 0.3)
        num_spikes = 12
        ring_r = 50
        for i in range(num_spikes):
            angle = i * math.tau / num_spikes
            spike_x = tx + int(math.cos(angle) * ring_r)
            spike_y = ty + int(math.sin(angle) * ring_r * 0.5)
            spike_h = int(25 * erupt_t)
            NS._draw_frost_crystal_spike(surface, spike_x, spike_y,
                                         spike_y - spike_h, 3, 240, phase)
        center_h = int(35 * erupt_t)
        NS._draw_frost_crystal_spike(surface, tx, ty, ty - center_h, 5,
                                     250, phase)
        for i in range(num_spikes):
            angle = (i + 0.5) * math.tau / num_spikes
            spike_x = tx + int(math.cos(angle) * (ring_r * 0.6))
            spike_y = ty + int(math.sin(angle) * (ring_r * 0.6) * 0.5)
            spike_h = int(18 * erupt_t)
            NS._draw_frost_crystal_spike(surface, spike_x, spike_y,
                                         spike_y - spike_h, 2, 230, phase)
        for i in range(10):
            angle = i * math.pi / 5 + phase * 2
            r = ring_r + int(math.sin(phase * 3 + i) * 10)
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.5) - int(erupt_t * 15)
            NS._draw_snowflake(surface, sx, sy, 2, int(230 * erupt_t),
                               rotate=phase * 3 + i)
        for i in range(5):
            angle = phase * 0.5 + i * math.tau / 5
            r = ring_r + 5
            sx = tx + int(math.cos(angle) * r)
            sy = ty + int(math.sin(angle) * r * 0.5)
            NS._aacircle(surface, (*P["frost_light"], int(120 * erupt_t)),
                         (sx, sy), 8)

    # ===================================================================
    # SKILL PROJECTILE TRIGGER (durasi HARUS == AI: w=45, e=50)
    # ===================================================================
    def _handle_skill_projectiles(boss, x, y, active_skill, timer):
        """Spawn proyektil skill pada titik progress yang tepat."""
        NS = _NS_ancient_apparition
        if getattr(boss, "_skip_renderer_projectiles", False):
            return
        tx, ty = NS._target_position(boss, x, y)

        if active_skill == "e":
            duration = 50
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.35 < progress < 0.45 and not getattr(boss,
                                                      "_aa_e_spawned",
                                                      False):
                NS._spawn_ice_bolt(boss, x + 25 * boss.direction, y - 5,
                                   tx, ty)
                boss._aa_e_spawned = True
            if progress > 0.7:
                boss._aa_e_spawned = False

        elif active_skill == "w":
            duration = 45
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.3 < progress < 0.4 and not getattr(boss,
                                                    "_aa_w_spawned",
                                                    False):
                NS._spawn_frost_beam(boss, x + 25 * boss.direction, y - 5,
                                     tx, ty)
                boss._aa_w_spawned = True
            if progress > 0.7:
                boss._aa_w_spawned = False

    # ===================================================================
    # LAPISAN FX HIDUP (heroes/ancient_apparition_fx)
    # ===================================================================
    _LIVE_MOD = None

    def _live_module():
        """Muat heroes.ancient_apparition_fx sekali; None kalau gagal."""
        NS = _NS_ancient_apparition
        if NS._LIVE_MOD is None:
            try:
                from heroes import ancient_apparition_fx as mod
                NS._LIVE_MOD = mod if getattr(
                    mod, "APPARITION_FX_ENABLED", True) else False
            except Exception:
                NS._LIVE_MOD = False
        return NS._LIVE_MOD or None

    def live_fx_ready():
        """True kalau lapisan hidup bisa dipakai (dipakai tooling)."""
        return _NS_ancient_apparition._live_module() is not None

    def _live_fx(boss, surface, x, y, want_draw, portrait):
        """Return (mod, owned): mod None = tanpa lapisan hidup.

        want_draw True pada jalur BOSS (draw tiap frame, tanpa cache).
        Jalur HERO penggambaran dilakukan heroes/__init__.py; di sini
        hanya dipasang penanda agar renderer melewati salinan canvas.
        """
        NS = _NS_ancient_apparition
        if portrait:
            return None, False
        mod = NS._live_module()
        if mod is None:
            return None, False
        try:
            if want_draw:
                mod.draw_ground_layer(surface, boss, x, y)
            else:
                mod.attach(boss)
        except Exception:
            return None, False
        try:
            owned = bool(mod.owns(boss))
        except Exception:
            owned = False
        return (mod if want_draw else None), owned

    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_apparition(surface, boss, x, y):
        NS = _NS_ancient_apparition
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        # Deteksi gerak: preferensi cache direktur FX (diperbarui tiap
        # frame).  Fallback _detect_moving untuk jalur tanpa lapisan
        # hidup — jalur hero hanya memanggil renderer saat cache miss,
        # jadi sampling posisi di sini tidak beraturan.
        NS._detect_moving(boss)
        cached_moving = getattr(boss, "_moving_cached", None)
        moving = bool(cached_moving) if cached_moving is not None \
            else bool(getattr(boss, "_aa_speed", 0.0) > 0.3)
        NS._update_attack_anim(boss)

        attacking = (getattr(boss, "_aa_attack_active", False)
                     or getattr(boss, "timer", 0)
                     > getattr(boss, "attack_cooldown", 50) - 15)
        facing = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        portrait = bool(getattr(boss, "_portrait_hd", False))
        hero_lane = (hasattr(boss, "_render_scale") and not portrait)

        # ── lapisan FX hidup: BOSS digambar tiap frame -> draw di sini;
        #    HERO digambar heroes/__init__ (di luar cache sprite) ──
        live, owned = NS._live_fx(boss, surface, x, y,
                                  want_draw=not hero_lane, portrait=portrait)

        state = NS._resolve_state(boss, moving)
        action = state if state != "death" else "idle"
        ap = getattr(boss, "_aa_attack_progress", 0.0) \
            if attacking else 0.0

        # ═══ 1. GROUND FX (belakang segalanya) ═══
        if not portrait:
            NS._draw_frost_aura(surface, x, y, pulse, active_skill)
            NS._draw_ground_frost(surface, x, y + 22, pulse, active_skill)
            NS._draw_ice_wisps(surface, x, y + 34, pulse,
                               trail=(state in ("walk", "run")),
                               facing=facing,
                               intense=bool(active_skill) or attacking)
            if not owned:
                if active_skill == "q":
                    NS._draw_ice_vortex_ground(surface, boss, x, y,
                                               skill_timer, pulse)
                elif active_skill == "r":
                    NS._draw_cold_feet_ground(surface, boss, x, y,
                                              skill_timer, pulse)

        # ═══ 2. SHADOW (di luar flash buffer — kontrak) ═══
        hover = 2 if state.startswith("cast_r") else 0
        NS._draw_shadow(surface, x, y + 52, lift=hover)

        # ═══ 3. KARAKTER (ke flash buffer saat hurt) ═══
        flash = int(getattr(boss, "hurt_flash_timer", 0) or 0)
        _tgt, _tx, _ty = surface, x, y
        if flash > 0:
            if NS._flash_buf is None:
                NS._flash_buf = pygame.Surface((220, 240),
                                               pygame.SRCALPHA)
            NS._flash_buf.fill((0, 0, 0, 0))
            NS._record_shadow = []
            _tgt, _tx, _ty = NS._flash_buf, 110, 120

        NS._draw_aa_body(_tgt, _tx, _ty, facing, pulse, action, ap)

        if flash > 0:
            surface.blit(NS._flash_buf, (x - _tx, y - _ty))
            w = int(235 * min(1.0, flash / 8.0))
            m = pygame.mask.from_surface(NS._flash_buf, 50)
            wht = m.to_surface(
                setcolor=(w, int(w * 0.9), int(w * 0.8), 255),
                unsetcolor=(0, 0, 0, 0))
            for rect in (NS._record_shadow or ()):
                wht.fill((0, 0, 0, 0), rect)
            surface.blit(wht, (x - _tx, y - _ty),
                         special_flags=pygame.BLEND_RGB_ADD)
            NS._record_shadow = None

        # ═══ 4. ATTACK FX + SKILL FX + PROJECTILE (fallback canvas) ═══
        if not portrait and not owned:
            if attacking and not hero_lane:
                NS._draw_swing_trail(surface, boss, x, y, facing, ap)
                NS._draw_cast_flash(surface, x, y, facing, ap)
            NS._handle_skill_projectiles(boss, x, y, active_skill,
                                         skill_timer)
            NS._manage_projectiles(boss, surface, pulse)
            if active_skill == "q":
                NS._draw_ice_vortex(surface, boss, x, y, skill_timer,
                                    pulse)
            elif active_skill == "r":
                NS._draw_cold_feet_spikes(surface, boss, x, y,
                                          skill_timer, pulse)

        # ═══ 5. LAPISAN HIDUP (depan) + DEBUG ═══
        if live is not None:
            try:
                live.draw_live_layer(surface, boss, x, y)
            except Exception:
                pass
        if NS.DEBUG_CHARACTER and not portrait:
            NS._draw_aa_debug(surface, boss, x, y, action, owned)

    # ===================================================================
    # DEBUG OVERLAY  (DEBUG_CHARACTER = True)
    # ===================================================================
    def _draw_aa_debug(surface, boss, x, y, action, owned):
        """Hitbox, hurtbox, jangkauan, state, FPS — murni baca state."""
        NS = _NS_ancient_apparition
        # hurtbox = radius unit
        r = max(8, int(getattr(boss, "radius", 30)))
        pygame.draw.circle(surface, (80, 170, 255), (int(x), int(y)), r, 1)
        # jangkauan serangan
        rng = max(10, int(getattr(boss, "range", 150)))
        f = 1 if (getattr(boss, "direction", 1) or 1) >= 0 else -1
        pygame.draw.line(surface, (255, 210, 60), (int(x), int(y)),
                         (int(x) + rng * f, int(y)), 1)
        # hitbox ayunan (jendela aktif)
        ap = float(getattr(boss, "_aa_attack_progress", 0.0) or 0.0)
        if getattr(boss, "_aa_attack_active", False) and \
                NS.ATK_PHASES["swing"][0] <= ap <= 0.62:
            hb = pygame.Rect(int(x) + (14 if f > 0 else -58),
                             int(y) - 30, 44, 36)
            pygame.draw.rect(surface, (255, 70, 70), hb, 2)
        # tabrakan proyektil lapisan hidup
        if owned:
            try:
                mod = NS._LIVE_MOD
                for p in mod.projectiles_for(boss):
                    pr = max(3, int(p.hit_radius))
                    pygame.draw.circle(surface, (255, 120, 255),
                                       (int(p.position.x),
                                        int(p.position.y)), pr, 1)
            except Exception:
                pass
        try:
            font = pygame.font.Font(None, 15)
        except Exception:
            return
        try:
            fps = int(pygame.time.Clock().get_fps())
        except Exception:
            fps = 0
        lines = [
            "AA %s ap=%.2f" % (action, ap),
            "skill %s t=%d" % (getattr(boss, "active_skill", None),
                               int(getattr(boss, "active_skill_timer", 0))),
            "owned=%d fps=%d" % (1 if owned else 0, fps),
        ]
        for i, txt in enumerate(lines):
            img = font.render(txt, True, (200, 245, 255))
            surface.blit(img, (x - 56, y - 108 + i * 13))

    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_ancient_apparition.draw_apparition(surface, boss, x, y)

    def draw_ancient_apparition(surface, boss, x, y):
        """Entry point resmi untuk Ancient Apparition."""
        _NS_ancient_apparition.draw_apparition(surface, boss, x, y)


def tilt_head(phase):
    """Goyangan kepala ringan (dipakai _masterwork_finish)."""
    return math.sin(phase * 0.8) * 1.0


# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_varkul(surface, boss, x, y):
    """Entry point varkul."""
    return _NS_varkul.draw_varkul(surface, boss, x, y)

def draw_xerathis(surface, boss, x, y):
    """Entry point xerathis."""
    return _NS_xerathis.draw_xerathis(surface, boss, x, y)

def draw_nyzrak(surface, boss, x, y):
    """Entry point nyzrak."""
    return _NS_nyzrak.draw_nyzrak(surface, boss, x, y)

def draw_ancient_apparition(surface, boss, x, y):
    """Entry point ancient_apparition."""
    return _NS_ancient_apparition.draw_ancient_apparition(surface, boss, x, y)
