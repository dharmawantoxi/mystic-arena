#!/usr/bin/env python3
"""SNAPSHOT renderer zharok v1 (sebelum upgrade Pixel Masterwork v2).

Dibuat otomatis sebelum rewrite `_NS_zharok` di bosses/level4.py.
Dipakai tools/_audit_zharok_v2.py untuk lembar before/after -
jangan diedit manual; kalau perlu regenerasi, ambil dari git history.
"""
import math
import pygame

try:
    import lighting as _lighting
except Exception:  # pragma: no cover
    _lighting = None

class _NS_zharok:
    """Namespace zharok - isi asli tidak diubah."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Palette - Bone yellow / fire orange / dark
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Bone (skeleton)
        "bone_darkest":   (35,  25,  10),
        "bone_dark":      (85,  65,  25),
        "bone_mid":       (155, 125, 55),
        "bone_light":     (215, 185, 100),
        "bone_high":      (245, 220, 145),
        "bone_shine":     (255, 240, 180),

        # Fire (orange/yellow)
        "fire_darkest":   (55,  12,   5),
        "fire_dark":      (140, 35,  10),
        "fire_mid":       (220, 80,  20),
        "fire_bright":    (255, 130, 40),
        "fire_hot":       (255, 180, 65),
        "fire_glow":      (255, 220, 130),
        "fire_white":     (255, 250, 210),

        # Hood/cloth (dark red)
        "hood_darkest":   (15,   8,  10),
        "hood_dark":      (50,  15,  18),
        "hood_mid":       (95,  30,  25),
        "hood_light":     (150, 55,  40),

        # Leather / armor straps
        "leather_darkest": (18, 12,  8),
        "leather_dark":   (45,  28,  18),
        "leather_mid":    (85,  55,  30),
        "leather_light":  (140, 95,  55),

        # Metal (arrows, plates)
        "metal_darkest":  (18,  15,  18),
        "metal_dark":     (48,  45,  55),
        "metal_mid":      (95,  90, 105),
        "metal_light":    (160, 155, 175),
        "metal_shine":    (215, 210, 225),

        # Gold accents (small)
        "gold_dark":      (90,  60,  15),
        "gold_mid":       (170, 130, 40),
        "gold_light":     (230, 190, 80),
        "gold_shine":     (255, 230, 140),

        # Eye sockets (glowing fire)
        "eye_dark":       (60,  15,   5),
        "eye_bright":     (255, 130, 40),
        "eye_hot":        (255, 200, 100),

        # Wood (bow)
        "wood_dark":      (50,  30,  15),
        "wood_mid":       (95,  60,  30),
        "wood_light":     (150, 105, 55),

        # Shadow smoke (purple)
        "smoke_dark":     (20,  10,  35),
        "smoke_mid":      (60,  40,  100),
        "smoke_light":    (120, 90, 175),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   2,   3),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zharok._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_zharok.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_zharok._clamp(color)
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
        pygame.draw.line(surface, color[:3], (sx, sy), (ex, ey), max(1, width))


    def _poly(surface, color, points):
        if len(points) < 3:
            return
        color = _NS_zharok._clamp(color)
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
        color = _NS_zharok._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(temp, color, (2, 2, int(rw), int(rh)), width)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.ellipse(surface, color[:3],
                            (rect[0], rect[1], int(rect[2]), int(rect[3])), width)


    def _rect(surface, color, rect, border_radius=0):
        color = _NS_zharok._clamp(color)
        if len(color) == 4 and color[3] < 255:
            rx, ry, rw, rh = rect
            if rw <= 0 or rh <= 0:
                return
            temp = pygame.Surface((int(rw) + 4, int(rh) + 4), pygame.SRCALPHA)
            pygame.draw.rect(temp, color, (2, 2, int(rw), int(rh)),
                             border_radius=border_radius)
            surface.blit(temp, (rx - 2, ry - 2))
            return
        pygame.draw.rect(surface, color[:3],
                         (rect[0], rect[1], int(rect[2]), int(rect[3])),
                         border_radius=border_radius)


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
        return int(x + 220 / float(getattr(boss, "_render_scale", 1.0) or 1.0) * getattr(boss, "direction", 1)), int(y)


    # ---------------------------------------------------------------------------
    # Fire helpers
    # ---------------------------------------------------------------------------
    def _draw_ember(surface, cx, cy, size=2, alpha=255):
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_dark"], alpha), (cx, cy), size + 1)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], alpha), (cx, cy), size)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_hot"], alpha), (cx, cy), max(1, size - 1))
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_glow"], min(255, alpha)), (cx, cy), 1)


    def _draw_flame(surface, cx, cy, size, phase, alpha=255):
        """Rising flame."""
        height = int(size * 2.2)
        for h in range(height):
            t = h / max(1, height)
            w = int(size * (1 - t * 0.7))
            fx = cx + int(math.sin(phase * 3 + t * 4) * 2)
            fy = cy - h
            a = int(alpha * (1 - t * 0.4))
            if t < 0.3:
                color = _NS_zharok.PALETTE["fire_darkest"]
            elif t < 0.55:
                color = _NS_zharok.PALETTE["fire_mid"]
            elif t < 0.8:
                color = _NS_zharok.PALETTE["fire_bright"]
            else:
                color = _NS_zharok.PALETTE["fire_hot"]
            _NS_zharok._aacircle(surface, (*color, a), (fx, fy), max(1, w))
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_glow"], alpha), (cx, cy - height // 3),
                  size // 2)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_white"], alpha),
                  (cx, cy - height // 4), max(1, size // 4))


    def _draw_flame_tuft(surface, cx, cy, size, phase, alpha=255):
        """Small crackling fire tuft (for bones)."""
        for i in range(3):
            angle = phase * 2 + i * math.pi * 2 / 3
            fx = cx + int(math.cos(angle) * (size // 2))
            fy = cy - size + int(math.sin(angle) * 1)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_darkest"], alpha), (fx, fy), size - 1)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], alpha), (fx, fy), size - 2)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_hot"], alpha), (fx, fy),
                      max(1, size - 3))
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_glow"], alpha), (cx, cy - size), 2)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_white"], alpha), (cx, cy - size), 1)


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class FireArrow:
        """Flame arrow projectile."""
        def __init__(self, sx, sy, tx, ty, speed=9.0):
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
            if len(self.trail) > 12:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            # Fire trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(50 + i * 15)
                r = max(1, 4 - (len(self.trail) - i))
                _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_darkest"], alpha), (tx, ty), r + 2)
                _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], alpha), (tx, ty), r)
                _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_hot"], alpha), (tx, ty), max(1, r - 1))
                _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_glow"], alpha // 2),
                          (tx, ty), max(1, r - 2))

            if self.alive:
                px, py = int(self.x), int(self.y)
                dx = math.cos(self.angle)
                dy = math.sin(self.angle)
                perp_x = -dy
                perp_y = dx

                # Arrow shaft (short line back)
                shaft_end_x = px - int(dx * 12)
                shaft_end_y = py - int(dy * 12)
                _NS_zharok._aaline(surface, _NS_zharok.PALETTE["shadow_deep"],
                        (shaft_end_x + 1, shaft_end_y + 1), (px + 1, py + 1), 3)
                _NS_zharok._aaline(surface, _NS_zharok.PALETTE["wood_dark"], (shaft_end_x, shaft_end_y),
                        (px, py), 2)
                _NS_zharok._aaline(surface, _NS_zharok.PALETTE["wood_mid"], (shaft_end_x, shaft_end_y),
                        (px, py), 1)

                # Arrow tip (triangle)
                tip_x = px + int(dx * 6)
                tip_y = py + int(dy * 6)
                arrow_pts = [
                    (tip_x, tip_y),
                    (px + int(perp_x * 3), py + int(perp_y * 3)),
                    (px - int(dx * 2), py - int(dy * 2)),
                    (px - int(perp_x * 3), py - int(perp_y * 3)),
                ]
                _NS_zharok._poly(surface, _NS_zharok.PALETTE["shadow_deep"],
                      [(p[0] + 1, p[1] + 1) for p in arrow_pts])
                _NS_zharok._poly(surface, _NS_zharok.PALETTE["metal_darkest"], arrow_pts)
                _NS_zharok._poly(surface, _NS_zharok.PALETTE["metal_dark"], [
                    (tip_x - int(dx), tip_y - int(dy)),
                    (px + int(perp_x * 2), py + int(perp_y * 2)),
                    (px, py),
                    (px - int(perp_x * 2), py - int(perp_y * 2)),
                ])
                _NS_zharok._poly(surface, _NS_zharok.PALETTE["metal_light"], [
                    (tip_x - int(dx * 2), tip_y - int(dy * 2)),
                    (px + int(perp_x), py + int(perp_y)),
                    (px - int(perp_x), py - int(perp_y)),
                ])
                _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["metal_shine"], (tip_x, tip_y), 1)

                # Feathers at back (fletching)
                for side_off in (-3, 3):
                    f_base_x = shaft_end_x
                    f_base_y = shaft_end_y
                    f_tip_x = shaft_end_x - int(dx * 4) + int(perp_x * side_off)
                    f_tip_y = shaft_end_y - int(dy * 4) + int(perp_y * side_off)
                    _NS_zharok._poly(surface, _NS_zharok.PALETTE["hood_dark"], [
                        (f_base_x, f_base_y),
                        (f_tip_x, f_tip_y),
                        (f_base_x - int(dx * 2), f_base_y - int(dy * 2)),
                    ])
                    _NS_zharok._poly(surface, _NS_zharok.PALETTE["hood_light"], [
                        (f_base_x, f_base_y),
                        (f_tip_x - int(dx), f_tip_y - int(dy)),
                        (f_base_x - int(dx), f_base_y - int(dy)),
                    ])

                # FIRE WRAPPING the arrow
                for i in range(5):
                    t = 0.1 + i * 0.18
                    fx = int(shaft_end_x + (px - shaft_end_x) * t)
                    fy = int(shaft_end_y + (py - shaft_end_y) * t)
                    flame_off = int(math.sin(phase * 4 + i) * 2)
                    fx += int(perp_x * flame_off)
                    fy += int(perp_y * flame_off)
                    _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_dark"], 200), (fx, fy), 3)
                    _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], 220), (fx, fy), 2)
                    _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_hot"], 240), (fx, fy), 1)

                # Bright glow at tip
                _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], 200), (tip_x, tip_y), 5)
                _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_hot"], 240), (tip_x, tip_y), 3)
                _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_glow"], 255), (tip_x, tip_y), 1)


    class BurningSkull:
        """R - Burning skull minion floating around."""
        def __init__(self, x, y, orbit_center_x, orbit_center_y, orbit_radius=50,
                     orbit_speed=0.05, orbit_offset=0, life=200):
            self.x = float(x)
            self.y = float(y)
            self.ocx = orbit_center_x
            self.ocy = orbit_center_y
            self.orbit_radius = orbit_radius
            self.orbit_speed = orbit_speed
            self.orbit_offset = orbit_offset
            self.life = life
            self.age = 0
            self.alive = True

        def update(self, boss_x=None, boss_y=None):
            self.age += 1
            if self.age >= self.life:
                self.alive = False
            if boss_x is not None:
                self.ocx = boss_x
                self.ocy = boss_y
            # Orbit around boss
            angle = self.age * self.orbit_speed + self.orbit_offset
            self.x = self.ocx + math.cos(angle) * self.orbit_radius
            self.y = self.ocy + math.sin(angle) * self.orbit_radius * 0.5 - 20

        def draw(self, surface, phase):
            t = self.age / self.life
            if t < 0.15:
                alpha = int(255 * (t / 0.15))
            elif t < 0.85:
                alpha = 255
            else:
                alpha = int(255 * (1 - (t - 0.85) / 0.15))

            px, py = int(self.x), int(self.y)

            # Flame trail behind
            for i in range(3):
                back_x = px + int(math.cos(self.orbit_offset + math.pi) * (i * 4))
                back_y = py + int(math.sin(self.orbit_offset + math.pi) * (i * 4))
                _NS_zharok._draw_ember(surface, back_x, back_y, max(1, 3 - i), alpha // (i + 1))

            # Skull
            _NS_zharok._draw_mini_skull(surface, px, py, phase, alpha)

            # Fire on top
            _NS_zharok._draw_flame_tuft(surface, px, py - 6, 3, phase, alpha)


    def _draw_mini_skull(surface, cx, cy, phase, alpha=255):
        """Small burning skull."""
        # Cranium
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["shadow_deep"], alpha), (cx + 1, cy + 1), 6)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["bone_darkest"], alpha), (cx, cy), 6)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["bone_dark"], alpha), (cx - 1, cy - 1), 5)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["bone_mid"], alpha), (cx - 1, cy - 2), 3)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["bone_light"], alpha), (cx - 2, cy - 3), 2)

        # Eye sockets (glowing)
        eye_pulse = math.sin(phase * 3) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy - 1
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["shadow_deep"], alpha), (ex, ey), 2)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], int(alpha * eye_pulse)),
                      (ex, ey), 1)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_hot"], int(alpha * eye_pulse)),
                      (ex, ey), 1)

        # Nose triangle
        _NS_zharok._poly(surface, (*_NS_zharok.PALETTE["shadow_deep"], alpha), [
            (cx, cy + 1),
            (cx - 1, cy + 3),
            (cx + 1, cy + 3),
        ])

        # Teeth
        _NS_zharok._rect(surface, (*_NS_zharok.PALETTE["shadow_deep"], alpha), (cx - 3, cy + 3, 6, 2))
        for tooth in (-2, -1, 1, 2):
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["bone_high"], alpha), (cx + tooth, cy + 4), 1)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_zh_last_x"):
            boss._zh_last_x = boss.x
            boss._zh_last_y = boss.y
            return False
        dx = abs(boss.x - boss._zh_last_x)
        dy = abs(boss.y - boss._zh_last_y)
        boss._zh_last_x = boss.x
        boss._zh_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_zh_prev_timer", 0))
        active = bool(getattr(boss, "_zh_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._zh_attack_active = True
            boss._zh_attack_frame = 0
            active = True
        elif active:
            boss._zh_attack_frame = int(getattr(boss, "_zh_attack_frame", 0)) + 1
            if boss._zh_attack_frame > cooldown:
                boss._zh_attack_active = False
                boss._zh_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._zh_attack_active = False
            boss._zh_attack_frame = 0
            active = False

        boss._zh_prev_timer = timer
        boss._zh_attack_progress = (
            min(1.0, getattr(boss, "_zh_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_zh_arrows"):
            boss._zh_arrows = []
        if not hasattr(boss, "_zh_skulls"):
            boss._zh_skulls = []

        for a in boss._zh_arrows:
            a.update()
            a.draw(surface, phase)
        boss._zh_arrows = [a for a in boss._zh_arrows if a.alive or a.age < 3]

        for s in boss._zh_skulls:
            s.update(boss_x=boss.x, boss_y=boss.y - 20)
            s.draw(surface, phase)
        boss._zh_skulls = [s for s in boss._zh_skulls if s.alive]


    def _spawn_fire_arrow(boss, sx, sy, tx, ty):
        if not hasattr(boss, "_zh_arrows"):
            boss._zh_arrows = []
        boss._zh_arrows.append(_NS_zharok.FireArrow(sx, sy, tx, ty))


    def _spawn_burning_skulls(boss, x, y, count=5):
        if not hasattr(boss, "_zh_skulls"):
            boss._zh_skulls = []
        for i in range(count):
            offset = i * math.pi * 2 / count
            boss._zh_skulls.append(_NS_zharok.BurningSkull(
                x, y, x, y, orbit_radius=45,
                orbit_speed=0.05, orbit_offset=offset, life=180
            ))


    # ===================================================================
    # MAIN ENTRY
    # ===================================================================
    def draw_zharok(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_zharok._detect_moving(boss)
        _NS_zharok._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_zh_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Background aura
        _NS_zharok._draw_fire_aura(surface, x, y, pulse, active_skill)
        _NS_zharok._draw_ground_runes(surface, x, y + 46, pulse, active_skill)

        # Ground skill effects
        if active_skill == "e":
            _NS_zharok._draw_death_pact_ground(surface, boss, x, y, skill_timer, pulse)

        # Skeleton walk (invisibility)
        is_invisible = (active_skill == "w")

        if is_invisible:
            _NS_zharok._draw_zh_smoke(surface, boss, x, y, skill_timer, pulse)
        else:
            # Character
            if attacking:
                _NS_zharok._draw_zh_attack(surface, boss, x, y)
            elif active_skill == "q":
                _NS_zharok._draw_zh_strafe(surface, boss, x, y, skill_timer)
            elif active_skill == "e":
                _NS_zharok._draw_zh_ecast(surface, boss, x, y, skill_timer)
            elif active_skill == "r":
                _NS_zharok._draw_zh_rcast(surface, boss, x, y, skill_timer)
            elif moving:
                _NS_zharok._draw_zh_walk(surface, boss, x, y)
            else:
                _NS_zharok._draw_zh_idle(surface, boss, x, y)

        # Skill triggers
        _NS_zharok._handle_skill_projectiles(boss, x, y, active_skill, skill_timer)

        # Projectiles
        _NS_zharok._manage_projectiles(boss, surface, pulse)

        # Foreground skill effects
        if active_skill == "e":
            _NS_zharok._draw_death_pact_foreground(surface, boss, x, y, skill_timer, pulse)


    def _handle_skill_projectiles(boss, x, y, active_skill, timer):
        tx, ty = _NS_zharok._target_position(boss, x, y)

        if active_skill == "q":
            # Q Strafe - fire multiple arrows over duration
            duration = 60
            progress = max(0.0, min(1.0, 1 - timer / duration))
            # Fire arrow every ~10 frames during 0.2-0.85 progress
            last_shot_frame = getattr(boss, "_zh_last_strafe_frame", -100)
            if 0.2 < progress < 0.85:
                frames_since = int(getattr(boss, "_zh_strafe_frame_count", 0))
                boss._zh_strafe_frame_count = frames_since + 1
                if frames_since % 8 == 0:
                    sx = x + 22 * boss.direction
                    sy = y - 10
                    # Slight spread
                    spread = ((frames_since // 8) - 2) * 15
                    _NS_zharok._spawn_fire_arrow(boss, sx, sy, tx + spread, ty)
            else:
                boss._zh_strafe_frame_count = 0

        elif active_skill == "r":
            # Summon burning skulls
            duration = 80
            progress = max(0.0, min(1.0, 1 - timer / duration))
            if 0.3 < progress < 0.4 and not getattr(boss, "_zh_r_spawned", False):
                _NS_zharok._spawn_burning_skulls(boss, x, y, count=5)
                boss._zh_r_spawned = True
            if progress > 0.6:
                boss._zh_r_spawned = False


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_zh_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_zharok._draw_shadow(surface, x, y + 55)
        _NS_zharok._draw_fire_wisps(surface, x, y + 40, boss.pulse)
        _NS_zharok._draw_zh_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_zh_walk(surface, boss, x, y):
        phase = boss.pulse * 2.3
        bob = int(math.sin(phase * 1.2) * 3)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_zharok._draw_shadow(surface, x + sway, y + 55)
        _NS_zharok._draw_fire_wisps(surface, x + sway, y + 40, phase, trail=True,
                         facing=boss.direction)
        _NS_zharok._draw_zh_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_zh_attack(surface, boss, x, y):
        progress = getattr(boss, "_zh_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Spawn arrow mid-attack
        if 0.35 < progress < 0.45 and not getattr(boss, "_zh_atk_spawned", False):
            tx, ty = _NS_zharok._target_position(boss, x, y)
            sx = x + 22 * boss.direction
            sy = y - 10
            _NS_zharok._spawn_fire_arrow(boss, sx, sy, tx, ty)
            boss._zh_atk_spawned = True
        if progress < 0.1 or progress > 0.9:
            boss._zh_atk_spawned = False

        recoil = int(math.sin(progress * math.pi) * 3) * -boss.direction
        _NS_zharok._draw_shadow(surface, x + recoil, y + 55)
        _NS_zharok._draw_fire_wisps(surface, x + recoil, y + 40, boss.pulse, intense=True)
        _NS_zharok._draw_zh_body(surface, x + recoil, y, boss.direction, boss.pulse,
                      "attack", progress)


    def _draw_zh_strafe(surface, boss, x, y, timer):
        """Q - Strafe rapid shots pose."""
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_zharok._draw_shadow(surface, x, y + 55)
        _NS_zharok._draw_fire_wisps(surface, x, y + 40, boss.pulse, intense=True)
        _NS_zharok._draw_zh_body(surface, x, y + bob, boss.direction, boss.pulse, "strafe")


    def _draw_zh_ecast(surface, boss, x, y, timer):
        """E - Death Pact pose."""
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_zharok._draw_shadow(surface, x, y + 55)
        _NS_zharok._draw_fire_wisps(surface, x, y + 40, boss.pulse, intense=True)
        _NS_zharok._draw_zh_body(surface, x, y + bob, boss.direction, boss.pulse, "e_cast")


    def _draw_zh_rcast(surface, boss, x, y, timer):
        """R - Burning Army pose."""
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_zharok._draw_shadow(surface, x, y + 55)
        _NS_zharok._draw_fire_wisps(surface, x, y + 40, boss.pulse, intense=True)
        _NS_zharok._draw_zh_body(surface, x, y + bob, boss.direction, boss.pulse, "r_cast")


    def _draw_zh_smoke(surface, boss, x, y, timer, phase):
        """W - Skeleton Walk (invisibility)."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        _NS_zharok._draw_shadow(surface, x, y + 55)

        # Fade in/out for character
        if progress < 0.3:
            alpha = int(255 * (1 - progress / 0.3))
        elif progress < 0.7:
            alpha = 0
        else:
            alpha = int(255 * ((progress - 0.7) / 0.3))

        if alpha > 0:
            # Ghost silhouette
            ghost = pygame.Surface((150, 180), pygame.SRCALPHA)
            _NS_zharok._draw_zh_body(ghost, 75, 90, boss.direction, phase, "idle")
            ghost.set_alpha(alpha)
            surface.blit(ghost, (x - 75, y - 90))

        # Purple smoke cloud
        for i in range(15):
            t = ((phase * 0.5 + i * 0.07) % 1.0)
            angle = phase * 0.6 + i * math.pi / 7.5
            r = 20 + int(t * 30)
            px = x + int(math.cos(angle) * r)
            py = y - 10 + int(math.sin(angle) * r * 0.5) - int(t * 15)
            smoke_alpha = int(200 * (1 - t))
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["smoke_dark"], smoke_alpha), (px, py), 8)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["smoke_mid"], smoke_alpha), (px, py), 6)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["smoke_light"], smoke_alpha // 2),
                      (px, py), 3)

        # Skull silhouette in smoke
        if 0.3 < progress < 0.7:
            skull_pulse = math.sin(phase * 2) * 0.3 + 0.7
            _NS_zharok._draw_mini_skull(surface, x, y - 30, phase, int(180 * skull_pulse))


    # ===================================================================
    # BODY RENDERING
    # ===================================================================
    def _draw_zh_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Skeleton archer body."""
        # Quiver on back
        _NS_zharok._draw_quiver(surface, cx - 8 * facing, cy - 14, facing, phase)

        # Cape/hood tattered back
        _NS_zharok._draw_hood_back(surface, cx, cy - 15, facing, phase)

        # Pelvis / lower bones
        _NS_zharok._draw_pelvis(surface, cx, cy + 8, phase)

        # Legs (skeleton)
        _NS_zharok._draw_skeleton_legs(surface, cx, cy + 15, facing, phase, action)

        # Ribcage torso
        _NS_zharok._draw_ribcage(surface, cx, cy - 5, phase)

        # Arms holding bow
        if action == "attack":
            _NS_zharok._draw_bow_attack_arms(surface, cx, cy - 5, facing, phase, attack_progress)
        elif action == "strafe":
            _NS_zharok._draw_bow_strafe_arms(surface, cx, cy - 5, facing, phase)
        elif action == "e_cast":
            _NS_zharok._draw_e_cast_arms(surface, cx, cy - 5, facing, phase)
        elif action == "r_cast":
            _NS_zharok._draw_r_cast_arms(surface, cx, cy - 5, facing, phase)
        else:
            _NS_zharok._draw_bow_idle_arms(surface, cx, cy - 5, facing, phase)

        # Head with hood
        _NS_zharok._draw_hooded_skull(surface, cx, cy - 22, facing, phase, action)


    def _draw_quiver(surface, cx, cy, facing, phase):
        """Quiver on back with arrows."""
        # Quiver body
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["shadow_deep"], (cx - 4 + 1, cy - 8 + 1, 8, 16),
              border_radius=1)
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["leather_darkest"], (cx - 4, cy - 8, 8, 16),
              border_radius=1)
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["leather_dark"], (cx - 3, cy - 7, 6, 14))
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["leather_mid"], (cx - 3, cy - 7, 3, 12))

        # Gold trim
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["gold_dark"], (cx - 4, cy - 8, 8, 2))
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["gold_mid"], (cx - 3, cy - 7, 6, 1))

        # Arrows sticking out
        for i, ox in enumerate((-2, 0, 2)):
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["wood_dark"], (cx + ox, cy - 8),
                    (cx + ox - i, cy - 16 - i), 2)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["wood_mid"], (cx + ox, cy - 8),
                    (cx + ox - i, cy - 16 - i), 1)
            # Feather fletching
            _NS_zharok._poly(surface, _NS_zharok.PALETTE["hood_dark"], [
                (cx + ox - i, cy - 16 - i),
                (cx + ox - i - 1, cy - 14 - i),
                (cx + ox - i + 1, cy - 15 - i),
            ])
            _NS_zharok._poly(surface, _NS_zharok.PALETTE["hood_light"], [
                (cx + ox - i, cy - 16 - i),
                (cx + ox - i - 1, cy - 15 - i),
                (cx + ox - i, cy - 14 - i),
            ])
            # Fire on arrow tips (some arrows lit)
            if i == 1:
                _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_bright"], (cx + ox - i, cy - 16 - i), 2)
                _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_hot"], (cx + ox - i, cy - 16 - i), 1)


    def _draw_hood_back(surface, cx, cy, facing, phase):
        """Tattered dark hood/cloth behind."""
        wave = math.sin(phase * 0.8) * 2

        hood_pts = [
            (cx - 8, cy),
            (cx - 12, cy + 8),
            (cx - 10 + int(wave), cy + 22),
            (cx - 3, cy + 28),
            (cx + 3, cy + 28),
            (cx + 10 - int(wave), cy + 22),
            (cx + 12, cy + 8),
            (cx + 8, cy),
        ]
        _NS_zharok._poly(surface, _NS_zharok.PALETTE["shadow_deep"], [(p[0] + 1, p[1] + 1) for p in hood_pts])
        _NS_zharok._poly(surface, _NS_zharok.PALETTE["hood_darkest"], hood_pts)
        _NS_zharok._poly(surface, _NS_zharok.PALETTE["hood_dark"], [
            (cx - 7, cy + 1),
            (cx - 10, cy + 8),
            (cx - 8 + int(wave), cy + 20),
            (cx - 2, cy + 25),
            (cx + 2, cy + 25),
            (cx + 8 - int(wave), cy + 20),
            (cx + 10, cy + 8),
            (cx + 7, cy + 1),
        ])
        _NS_zharok._poly(surface, _NS_zharok.PALETTE["hood_mid"], [
            (cx - 5, cy + 2),
            (cx - 7, cy + 8),
            (cx - 5 + int(wave), cy + 18),
            (cx, cy + 22),
            (cx + 5 - int(wave), cy + 18),
            (cx + 7, cy + 8),
            (cx + 5, cy + 2),
        ])

        # Tattered bottom
        for i in range(5):
            strip_x = cx - 8 + i * 4
            strip_y = cy + 25 + int(math.sin(phase + i) * 2)
            _NS_zharok._poly(surface, _NS_zharok.PALETTE["hood_darkest"], [
                (strip_x - 2, cy + 22),
                (strip_x + 2, cy + 22),
                (strip_x, strip_y + 3),
            ])


    def _draw_pelvis(surface, cx, cy, phase):
        """Skeletal pelvis/hip bones."""
        # Belt with pouches
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["shadow_deep"], (cx - 10 + 1, cy - 2 + 1, 20, 6),
              border_radius=1)
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["leather_darkest"], (cx - 10, cy - 2, 20, 6),
              border_radius=1)
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["leather_dark"], (cx - 9, cy - 1, 18, 4))
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["leather_mid"], (cx - 8, cy - 1, 16, 2))

        # Gold buckle
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["gold_dark"], (cx - 3, cy - 3, 6, 6), border_radius=1)
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["gold_mid"], (cx - 2, cy - 2, 4, 4))
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_bright"], (cx, cy), 1)

        # Pelvis bone below
        _NS_zharok._ellipse(surface, _NS_zharok.PALETTE["shadow_deep"], (cx - 8 + 1, cy + 4 + 1, 16, 6))
        _NS_zharok._ellipse(surface, _NS_zharok.PALETTE["bone_darkest"], (cx - 8, cy + 4, 16, 6))
        _NS_zharok._ellipse(surface, _NS_zharok.PALETTE["bone_dark"], (cx - 7, cy + 4, 14, 5))
        _NS_zharok._ellipse(surface, _NS_zharok.PALETTE["bone_mid"], (cx - 6, cy + 4, 12, 3))

        # Central dark hole
        _NS_zharok._ellipse(surface, _NS_zharok.PALETTE["shadow_deep"], (cx - 3, cy + 5, 6, 3))


    def _draw_skeleton_legs(surface, cx, cy, facing, phase, action):
        """Two skeletal legs."""
        walk_phase = phase * 3 if action == "walk" else 0

        for side_off, leg_x in ((-1, -4), (1, 4)):
            lift = int(math.sin(walk_phase + (0 if side_off == 1 else math.pi)) * 2) \
                if action == "walk" else 0

            lx = cx + leg_x
            # Thigh bone
            thigh_top = (lx, cy - lift)
            thigh_bot = (lx, cy + 8 - lift)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["shadow_deep"],
                    (thigh_top[0] + 1, thigh_top[1] + 1),
                    (thigh_bot[0] + 1, thigh_bot[1] + 1), 5)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_darkest"], thigh_top, thigh_bot, 4)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_dark"], thigh_top, thigh_bot, 3)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_mid"], thigh_top, thigh_bot, 2)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_light"], (thigh_top[0] - 1, thigh_top[1]),
                    (thigh_bot[0] - 1, thigh_bot[1]), 1)

            # Knee joint
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_darkest"], thigh_bot, 3)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_dark"], thigh_bot, 2)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_mid"], (thigh_bot[0] - 1, thigh_bot[1] - 1), 1)

            # Shin
            shin_top = (lx, cy + 9 - lift)
            shin_bot = (lx, cy + 18 - lift)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["shadow_deep"],
                    (shin_top[0] + 1, shin_top[1] + 1),
                    (shin_bot[0] + 1, shin_bot[1] + 1), 4)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_darkest"], shin_top, shin_bot, 3)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_dark"], shin_top, shin_bot, 2)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_mid"], shin_top, shin_bot, 1)

            # Foot
            _NS_zharok._rect(surface, _NS_zharok.PALETTE["leather_darkest"], (lx - 3, cy + 18 - lift, 6, 3),
                  border_radius=1)
            _NS_zharok._rect(surface, _NS_zharok.PALETTE["leather_dark"], (lx - 3, cy + 18 - lift, 6, 2))
            _NS_zharok._rect(surface, _NS_zharok.PALETTE["gold_dark"], (lx - 3, cy + 18 - lift, 6, 1))

            # Fire tuft on bone
            if action != "walk" or (walk_phase + side_off) % 2 < 1:
                _NS_zharok._draw_flame_tuft(surface, lx, cy + 3 - lift, 3, phase + side_off, 200)


    def _draw_ribcage(surface, cx, cy, phase):
        """Skeleton ribcage."""
        # Spine (background)
        _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_darkest"], (cx, cy - 8), (cx, cy + 10), 3)
        _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_dark"], (cx, cy - 8), (cx, cy + 10), 2)
        _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_mid"], (cx - 1, cy - 8), (cx - 1, cy + 10), 1)

        # Vertebrae
        for i in range(5):
            vy = cy - 6 + i * 4
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_darkest"], (cx, vy), 2)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_dark"], (cx, vy), 1)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_mid"], (cx - 1, vy - 1), 1)

        # Ribs (curved on both sides)
        for i, ry in enumerate((-6, -3, 0, 3, 6)):
            rib_width = 8 - abs(i - 2)
            # Left rib
            rib_pts_l = [
                (cx, cy + ry),
                (cx - rib_width, cy + ry + 1),
                (cx - rib_width - 1, cy + ry + 3),
                (cx - 2, cy + ry + 4),
            ]
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["shadow_deep"],
                    (cx + 1, cy + ry + 1), (cx - rib_width + 1, cy + ry + 2), 3)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_darkest"],
                    (cx, cy + ry), (cx - rib_width, cy + ry + 1), 2)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_dark"],
                    (cx, cy + ry), (cx - rib_width, cy + ry + 1), 1)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_mid"],
                    (cx, cy + ry - 1), (cx - rib_width, cy + ry), 1)

            # Right rib
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["shadow_deep"],
                    (cx + 1, cy + ry + 1), (cx + rib_width + 1, cy + ry + 2), 3)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_darkest"],
                    (cx, cy + ry), (cx + rib_width, cy + ry + 1), 2)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_dark"],
                    (cx, cy + ry), (cx + rib_width, cy + ry + 1), 1)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_mid"],
                    (cx, cy + ry - 1), (cx + rib_width, cy + ry), 1)

        # Shoulder bones (clavicles)
        for side in (-1, 1):
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_darkest"],
                    (cx, cy - 7), (cx + side * 9, cy - 5), 3)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_dark"],
                    (cx, cy - 7), (cx + side * 9, cy - 5), 2)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_mid"],
                    (cx, cy - 8), (cx + side * 9, cy - 6), 1)
            # Joint
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_darkest"], (cx + side * 9, cy - 5), 3)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_mid"], (cx + side * 9, cy - 5), 2)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_high"], (cx + side * 9 - 1, cy - 6), 1)

        # Small chest armor plate over ribs
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["shadow_deep"], (cx - 4 + 1, cy - 4 + 1, 8, 6), border_radius=1)
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["leather_dark"], (cx - 4, cy - 4, 8, 6), border_radius=1)
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["gold_dark"], (cx - 3, cy - 4, 6, 1))
        # Fire gem
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_bright"], (cx, cy - 1), 2)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_hot"], (cx, cy - 1), 1)


    def _draw_bow_idle_arms(surface, cx, cy, facing, phase):
        """Bow held ready, arrow nocked."""
        sway = math.sin(phase * 0.7) * 1

        # Bow arm (front, holding bow forward)
        bow_side = facing
        sh_x = cx + bow_side * 9
        sh_y = cy - 5
        elbow_x = sh_x + bow_side * 6
        elbow_y = cy + 2 + int(sway)
        hand_x = elbow_x + bow_side * 8
        hand_y = elbow_y - 2

        _NS_zharok._draw_bone_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_zharok._draw_bone_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        _NS_zharok._draw_skeleton_hand(surface, hand_x, hand_y, bow_side)

        # Draw bow at hand position
        _NS_zharok._draw_flaming_bow(surface, hand_x, hand_y, bow_side, "ready", phase)

        # String/draw arm (back)
        other_side = -facing
        sh_x2 = cx + other_side * 9
        sh_y2 = cy - 5
        elbow_x2 = sh_x2 + other_side * 3
        elbow_y2 = cy + 2 + int(sway)
        hand_x2 = elbow_x2 + other_side * 3
        hand_y2 = elbow_y2 + 2

        _NS_zharok._draw_bone_arm(surface, sh_x2, sh_y2, elbow_x2, elbow_y2)
        _NS_zharok._draw_bone_arm(surface, elbow_x2, elbow_y2, hand_x2, hand_y2)
        _NS_zharok._draw_skeleton_hand(surface, hand_x2, hand_y2, other_side)


    def _draw_bow_attack_arms(surface, cx, cy, facing, phase, progress):
        """Draw bow drawn back then release."""
        # Bow arm forward
        bow_side = facing
        sh_x = cx + bow_side * 9
        sh_y = cy - 5

        # Bow arm extends fully forward
        bow_hand_x = sh_x + bow_side * 15
        bow_hand_y = cy - 3
        bow_elbow_x = sh_x + bow_side * 8
        bow_elbow_y = cy - 4

        _NS_zharok._draw_bone_arm(surface, sh_x, sh_y, bow_elbow_x, bow_elbow_y)
        _NS_zharok._draw_bone_arm(surface, bow_elbow_x, bow_elbow_y, bow_hand_x, bow_hand_y)
        _NS_zharok._draw_skeleton_hand(surface, bow_hand_x, bow_hand_y, bow_side)

        # Draw arm - pulls back then releases
        if progress < 0.4:
            # Draw back (pull string)
            t = progress / 0.4
            pull = int(6 * t)
        elif progress < 0.5:
            # Held
            pull = 6
        else:
            # Released
            pull = 0

        string_hand_x = bow_hand_x - bow_side * (10 + pull)
        string_hand_y = bow_hand_y

        other_side = -facing
        sh_x2 = cx + other_side * 9
        sh_y2 = cy - 5
        # Elbow bends
        elbow_x2 = (sh_x2 + string_hand_x) // 2 + other_side * 2
        elbow_y2 = cy + 3

        _NS_zharok._draw_bone_arm(surface, sh_x2, sh_y2, elbow_x2, elbow_y2)
        _NS_zharok._draw_bone_arm(surface, elbow_x2, elbow_y2, string_hand_x, string_hand_y)
        _NS_zharok._draw_skeleton_hand(surface, string_hand_x, string_hand_y, other_side)

        # Bow (drawn state)
        if progress < 0.55:
            _NS_zharok._draw_flaming_bow(surface, bow_hand_x, bow_hand_y, bow_side, "drawn",
                              phase, pull=pull, arrow_x=string_hand_x,
                              arrow_y=string_hand_y)
        else:
            _NS_zharok._draw_flaming_bow(surface, bow_hand_x, bow_hand_y, bow_side, "ready", phase)


    def _draw_bow_strafe_arms(surface, cx, cy, facing, phase):
        """Strafe - continuous quick shooting."""
        # Similar to attack but continuous rapid pull
        pull_pattern = int(math.sin(phase * 8) * 4 + 4)  # oscillate 0-8

        bow_side = facing
        sh_x = cx + bow_side * 9
        sh_y = cy - 5
        bow_hand_x = sh_x + bow_side * 15
        bow_hand_y = cy - 3
        bow_elbow_x = sh_x + bow_side * 8
        bow_elbow_y = cy - 4

        _NS_zharok._draw_bone_arm(surface, sh_x, sh_y, bow_elbow_x, bow_elbow_y)
        _NS_zharok._draw_bone_arm(surface, bow_elbow_x, bow_elbow_y, bow_hand_x, bow_hand_y)
        _NS_zharok._draw_skeleton_hand(surface, bow_hand_x, bow_hand_y, bow_side)

        other_side = -facing
        sh_x2 = cx + other_side * 9
        sh_y2 = cy - 5
        string_hand_x = bow_hand_x - bow_side * (10 + pull_pattern)
        string_hand_y = bow_hand_y
        elbow_x2 = (sh_x2 + string_hand_x) // 2 + other_side * 2
        elbow_y2 = cy + 3

        _NS_zharok._draw_bone_arm(surface, sh_x2, sh_y2, elbow_x2, elbow_y2)
        _NS_zharok._draw_bone_arm(surface, elbow_x2, elbow_y2, string_hand_x, string_hand_y)
        _NS_zharok._draw_skeleton_hand(surface, string_hand_x, string_hand_y, other_side)

        _NS_zharok._draw_flaming_bow(surface, bow_hand_x, bow_hand_y, bow_side, "drawn",
                          phase, pull=pull_pattern, arrow_x=string_hand_x,
                          arrow_y=string_hand_y)


    def _draw_e_cast_arms(surface, cx, cy, facing, phase):
        """E - Death Pact, one arm raised with skull energy."""
        # Bow arm hanging
        bow_side = facing
        sh_x = cx + bow_side * 9
        sh_y = cy - 5
        elbow_x = sh_x + bow_side * 5
        elbow_y = cy + 4
        hand_x = elbow_x + bow_side * 4
        hand_y = elbow_y + 6

        _NS_zharok._draw_bone_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
        _NS_zharok._draw_bone_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
        _NS_zharok._draw_skeleton_hand(surface, hand_x, hand_y, bow_side)
        _NS_zharok._draw_flaming_bow(surface, hand_x, hand_y, bow_side, "down", phase)

        # Other arm raised up
        other_side = -facing
        sh_x2 = cx + other_side * 9
        sh_y2 = cy - 5
        elbow_x2 = sh_x2 + other_side * 5
        elbow_y2 = cy - 10
        hand_x2 = elbow_x2 + other_side * 3
        hand_y2 = cy - 18

        _NS_zharok._draw_bone_arm(surface, sh_x2, sh_y2, elbow_x2, elbow_y2)
        _NS_zharok._draw_bone_arm(surface, elbow_x2, elbow_y2, hand_x2, hand_y2)
        _NS_zharok._draw_skeleton_hand(surface, hand_x2, hand_y2, other_side)

        # Fire in raised hand
        pulse = math.sin(phase * 4) * 0.3 + 0.7
        r = int(6 * pulse)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_darkest"], 200), (hand_x2, hand_y2), r + 4)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_mid"], (hand_x2, hand_y2), r + 2)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_bright"], (hand_x2, hand_y2), r)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_hot"], (hand_x2, hand_y2), max(1, r - 2))
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_glow"], (hand_x2, hand_y2), max(1, r - 4))


    def _draw_r_cast_arms(surface, cx, cy, facing, phase):
        """R - Burning Army, both arms out summoning."""
        for side in (-1, 1):
            sh_x = cx + side * 9
            sh_y = cy - 5
            elbow_x = sh_x + side * 8
            elbow_y = cy - 4
            hand_x = elbow_x + side * 6
            hand_y = cy - 10

            _NS_zharok._draw_bone_arm(surface, sh_x, sh_y, elbow_x, elbow_y)
            _NS_zharok._draw_bone_arm(surface, elbow_x, elbow_y, hand_x, hand_y)
            _NS_zharok._draw_skeleton_hand(surface, hand_x, hand_y, side)

            # Fire in both hands
            pulse = math.sin(phase * 4 + side) * 0.3 + 0.7
            r = int(7 * pulse)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_darkest"], 200), (hand_x, hand_y), r + 4)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_mid"], (hand_x, hand_y), r + 2)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_bright"], (hand_x, hand_y), r)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_hot"], (hand_x, hand_y), max(1, r - 2))
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_glow"], (hand_x, hand_y), max(1, r - 4))


    def _draw_bone_arm(surface, x1, y1, x2, y2):
        """Skeletal arm segment."""
        _NS_zharok._aaline(surface, _NS_zharok.PALETTE["shadow_deep"], (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 4)
        _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_darkest"], (x1, y1), (x2, y2), 3)
        _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_dark"], (x1, y1), (x2, y2), 2)
        _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_mid"], (x1, y1), (x2, y2), 1)
        _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_light"], (x1 - 1, y1), (x2 - 1, y2), 1)

        # Joint at end
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_darkest"], (x2, y2), 2)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_dark"], (x2, y2), 1)


    def _draw_skeleton_hand(surface, x, y, facing):
        """Bony hand."""
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["shadow_deep"], (x + 1, y + 1), 3)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_darkest"], (x, y), 3)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_dark"], (x, y), 2)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_mid"], (x - 1, y - 1), 1)

        # 3 finger bones
        for i, off in enumerate((-1, 0, 1)):
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["bone_darkest"],
                    (x, y), (x + facing * 3, y + off * 2), 1)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_light"],
                      (x + facing * 3, y + off * 2), 1)


    def _draw_flaming_bow(surface, hx, hy, facing, pose, phase, pull=0,
                           arrow_x=None, arrow_y=None):
        """Curved bow that flames."""
        # Bow curve - vertical when ready
        bow_top_y = hy - 20
        bow_bot_y = hy + 20
        curve = 8 * facing  # bow curves outward

        # Bow shape as curved path
        bow_pts = []
        for t in range(11):
            u = t / 10
            y = bow_top_y + (bow_bot_y - bow_top_y) * u
            # Parabolic curve
            x = hx + int(curve * (1 - (u - 0.5) ** 2 * 4))
            bow_pts.append((x, y))

        # Draw bow curve
        for i in range(len(bow_pts) - 1):
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["shadow_deep"],
                    (bow_pts[i][0] + 1, bow_pts[i][1] + 1),
                    (bow_pts[i + 1][0] + 1, bow_pts[i + 1][1] + 1), 3)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["wood_dark"], bow_pts[i], bow_pts[i + 1], 3)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["wood_mid"], bow_pts[i], bow_pts[i + 1], 2)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["wood_light"], bow_pts[i], bow_pts[i + 1], 1)

        # Bow tips (curled)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["metal_dark"], bow_pts[0], 2)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["metal_light"], bow_pts[0], 1)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["metal_dark"], bow_pts[-1], 2)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["metal_light"], bow_pts[-1], 1)

        # Bowstring
        top_tip = bow_pts[0]
        bot_tip = bow_pts[-1]
        if pose == "drawn" and arrow_x is not None:
            # String pulled back forming V
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["shadow_deep"],
                    (top_tip[0] + 1, top_tip[1] + 1),
                    (arrow_x + 1, arrow_y + 1), 2)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["metal_mid"], top_tip, (arrow_x, arrow_y), 1)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["metal_light"], top_tip, (arrow_x, arrow_y), 1)

            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["shadow_deep"],
                    (bot_tip[0] + 1, bot_tip[1] + 1),
                    (arrow_x + 1, arrow_y + 1), 2)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["metal_mid"], bot_tip, (arrow_x, arrow_y), 1)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["metal_light"], bot_tip, (arrow_x, arrow_y), 1)

            # Nocked arrow (from string to bow front)
            arrow_tip_x = arrow_x + facing * (30 + pull)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["wood_dark"], (arrow_x, arrow_y),
                    (arrow_tip_x, arrow_y), 2)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["wood_mid"], (arrow_x, arrow_y),
                    (arrow_tip_x, arrow_y), 1)
            # Arrow head
            _NS_zharok._poly(surface, _NS_zharok.PALETTE["metal_darkest"], [
                (arrow_tip_x, arrow_y),
                (arrow_tip_x - facing * 4, arrow_y - 2),
                (arrow_tip_x - facing * 4, arrow_y + 2),
            ])
            _NS_zharok._poly(surface, _NS_zharok.PALETTE["metal_light"], [
                (arrow_tip_x - facing, arrow_y),
                (arrow_tip_x - facing * 3, arrow_y - 1),
                (arrow_tip_x - facing * 3, arrow_y + 1),
            ])
            # Fire on arrow head
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_bright"], (arrow_tip_x, arrow_y), 3)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_hot"], (arrow_tip_x, arrow_y), 2)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_glow"], (arrow_tip_x, arrow_y), 1)
        else:
            # String straight
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["metal_mid"], top_tip, bot_tip, 1)
            _NS_zharok._aaline(surface, _NS_zharok.PALETTE["metal_light"], top_tip, bot_tip, 1)

        # Fire wrapping the bow
        for i, t in enumerate([0.15, 0.35, 0.65, 0.85]):
            pt = bow_pts[int(t * 10)]
            flame_x = pt[0] + int(math.sin(phase * 3 + i) * 2)
            flame_y = pt[1]
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_dark"], 200), (flame_x, flame_y), 3)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], 220), (flame_x, flame_y), 2)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_hot"], 240), (flame_x, flame_y), 1)


    def _draw_hooded_skull(surface, cx, cy, facing, phase, action):
        """Hooded skull head."""
        # Hood
        hood = [
            (cx - 10, cy + 8),
            (cx - 11, cy - 2),
            (cx - 8, cy - 8),
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx + 8, cy - 8),
            (cx + 11, cy - 2),
            (cx + 10, cy + 8),
        ]
        _NS_zharok._poly(surface, _NS_zharok.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in hood])
        _NS_zharok._poly(surface, _NS_zharok.PALETTE["hood_darkest"], hood)
        _NS_zharok._poly(surface, _NS_zharok.PALETTE["hood_dark"], [
            (cx - 9, cy + 7),
            (cx - 10, cy - 2),
            (cx - 7, cy - 7),
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx + 7, cy - 7),
            (cx + 10, cy - 2),
            (cx + 9, cy + 7),
        ])
        _NS_zharok._poly(surface, _NS_zharok.PALETTE["hood_mid"], [
            (cx - 7, cy + 6),
            (cx - 8, cy - 2),
            (cx - 5, cy - 6),
            (cx, cy - 8),
            (cx + 5, cy - 6),
            (cx + 8, cy - 2),
            (cx + 7, cy + 6),
        ])

        # Hood inner dark shadow
        _NS_zharok._poly(surface, _NS_zharok.PALETTE["shadow_deep"], [
            (cx - 6, cy - 4),
            (cx + 6, cy - 4),
            (cx + 5, cy + 6),
            (cx, cy + 8),
            (cx - 5, cy + 6),
        ])

        # SKULL inside hood
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_darkest"], (cx, cy - 1), 6)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_dark"], (cx - 1, cy - 2), 5)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_mid"], (cx - 1, cy - 3), 3)
        _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["bone_light"], (cx - 2, cy - 4), 2)

        # Eye sockets (deep, glowing fire)
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side in (-1, 1):
            ex = cx + side * 2
            ey = cy - 2
            # Deep socket
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["shadow_deep"], (ex, ey), 3)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["eye_dark"], (ex, ey), 2)
            # Bright fire eye
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_bright"], (ex, ey),
                      max(1, int(2 * eye_pulse)))
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_hot"], (ex, ey), 1)
            _NS_zharok._aacircle(surface, _NS_zharok.PALETTE["fire_glow"], (ex, ey), 1)
            # Halo glow
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], int(120 * eye_pulse)),
                      (ex, ey), 4)

        # Nose triangle (dark hole)
        _NS_zharok._poly(surface, _NS_zharok.PALETTE["shadow_deep"], [
            (cx, cy + 1),
            (cx - 1, cy + 3),
            (cx + 1, cy + 3),
        ])

        # Teeth (jaw)
        _NS_zharok._rect(surface, _NS_zharok.PALETTE["shadow_deep"], (cx - 4, cy + 3, 8, 3))
        for tooth in (-3, -2, -1, 0, 1, 2, 3):
            _NS_zharok._rect(surface, _NS_zharok.PALETTE["bone_high"], (cx + tooth, cy + 3, 1, 2))

        # FLAME ON TOP OF SKULL (Clinkz signature)
        _NS_zharok._draw_flame(surface, cx, cy - 6, 5, phase, 240)
        # Extra big flame
        _NS_zharok._draw_flame(surface, cx - 3, cy - 4, 3, phase + 1, 220)
        _NS_zharok._draw_flame(surface, cx + 3, cy - 4, 3, phase + 2, 220)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_fire_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Fire wisps beneath skeleton."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 44), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(36, 3, -4):
            alpha = int((36 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_zharok.PALETTE["fire_darkest"], min(255, alpha)),
                    (75 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 75, cy - 11))

        # Rising flames
        for i, offset in enumerate((-22, -8, 8, 22)):
            t = (phase * 0.55 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 26)
            alpha = max(0, min(255, int(220 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_darkest"], alpha), (sx, sy), 5)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_dark"], alpha), (sx, sy - 1), 3)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], alpha), (sx, sy - 2), 2)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_hot"], alpha), (sx, sy - 3), 1)

        # Embers orbiting
        for i in range(7):
            angle = phase * 0.9 + i * math.pi * 2 / 7
            r = 25 + int(math.sin(phase + i * 1.3) * 6)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 9)
            _NS_zharok._draw_ember(surface, sx, sy, 2, 200)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 3)
                alpha = max(0, 140 - i * 25)
                _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_dark"], alpha),
                          (sx, sy), max(2, 5 - i))
                _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], alpha),
                          (sx, sy), max(1, 3 - i))


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((110, 22), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (11 - radius, 11 - radius, 88 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_zharok.PALETTE["fire_dark"], 80), (10, 5, 90, 12))
        surface.blit(shadow, (x - 55, y - 11))


    def _draw_fire_aura(surface, x, y, phase, active_skill):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        strength = 1.6 if active_skill else 1.0
        aura = pygame.Surface((220, 200), pygame.SRCALPHA)
        for radius in range(90, 5, -4):
            alpha = int((90 - radius) * 1.3 * pulse * strength)
            if alpha > 0:
                _NS_zharok._aacircle(aura, (*_NS_zharok.PALETTE["fire_darkest"], min(255, alpha)),
                          (110, 100), radius)
        surface.blit(aura, (x - 110, y - 100))


    def _draw_ground_runes(surface, x, y, phase, active_skill):
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((140, 46), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_zharok.PALETTE["fire_dark"], 160),
                            (5, 10, 130, 26), 3)
        pygame.draw.ellipse(ring, (*_NS_zharok.PALETTE["fire_mid"], 190),
                            (20, 14, 100, 18), 2)

        for i in range(10):
            angle = phase * 0.15 + i * math.pi / 5
            x1 = 70 + int(math.cos(angle) * 32)
            y1 = 23 + int(math.sin(angle) * 7)
            x2 = 70 + int(math.cos(angle) * 60)
            y2 = 23 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_zharok.PALETTE["fire_hot"], 180),
                             (x1, y1), (x2, y2), 1)

        if active_skill:
            pygame.draw.ellipse(ring, (*_NS_zharok.PALETTE["fire_glow"], int(80 * pulse)),
                                (15, 8, 110, 30), 1)

        surface.blit(ring, (x - 70, y - 23))


    # ===================================================================
    # SKILL E: DEATH PACT
    # ===================================================================
    def _draw_death_pact_ground(surface, boss, x, y, timer, phase):
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        # Runic circle with pentagram/skull
        radius = int(50 + progress * 15)
        _NS_zharok._ellipse(surface, (*_NS_zharok.PALETTE["fire_darkest"], int(200 * pulse)),
                 (x - radius, y + 45 - radius // 3, radius * 2, radius // 1.5), 3)
        _NS_zharok._ellipse(surface, (*_NS_zharok.PALETTE["fire_dark"], int(180 * pulse)),
                 (x - radius + 4, y + 45 - radius // 3 + 2,
                  radius * 2 - 8, radius // 1.5 - 4), 2)

        # Pentagram-like lines
        for i in range(5):
            angle = phase * 0.15 + i * math.pi * 2 / 5
            angle2 = angle + math.pi * 4 / 5
            x1 = x + int(math.cos(angle) * (radius - 5))
            y1 = y + 45 + int(math.sin(angle) * (radius - 5) * 0.5)
            x2 = x + int(math.cos(angle2) * (radius - 5))
            y2 = y + 45 + int(math.sin(angle2) * (radius - 5) * 0.5)
            _NS_zharok._aaline(surface, (*_NS_zharok.PALETTE["fire_bright"], int(200 * pulse)),
                    (x1, y1), (x2, y2), 1)


    def _draw_death_pact_foreground(surface, boss, x, y, timer, phase):
        """Big skull above boss + energy channels."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        pulse = math.sin(phase * 2) * 0.3 + 0.7

        if progress < 0.2:
            return

        form_t = min(1.0, (progress - 0.2) / 0.3)
        alpha = int(255 * form_t)

        # Big skull hovering above
        skull_y = y - 70 - int(math.sin(phase * 1.5) * 4)

        # Large skull
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["shadow_deep"], alpha), (x + 2, skull_y + 2), 15)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["bone_darkest"], alpha), (x, skull_y), 15)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["bone_dark"], alpha), (x - 1, skull_y - 2), 12)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["bone_mid"], alpha), (x - 2, skull_y - 4), 8)
        _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["bone_light"], alpha), (x - 3, skull_y - 6), 4)

        # Eye sockets (huge glowing)
        eye_pulse = math.sin(phase * 3) * 0.3 + 0.7
        for side in (-1, 1):
            ex = x + side * 5
            ey = skull_y - 3
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["shadow_deep"], alpha), (ex, ey), 5)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["eye_dark"], alpha), (ex, ey), 4)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], int(alpha * eye_pulse)),
                      (ex, ey), 3)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_hot"], int(alpha * eye_pulse)),
                      (ex, ey), 2)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_glow"], int(alpha * eye_pulse)),
                      (ex, ey), 1)
            # Halo
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], int(150 * eye_pulse)),
                      (ex, ey), 7)

        # Nose triangle
        _NS_zharok._poly(surface, (*_NS_zharok.PALETTE["shadow_deep"], alpha), [
            (x, skull_y + 2),
            (x - 3, skull_y + 6),
            (x + 3, skull_y + 6),
        ])

        # Big teeth/jaw
        _NS_zharok._rect(surface, (*_NS_zharok.PALETTE["shadow_deep"], alpha), (x - 8, skull_y + 6, 16, 5))
        for tooth in (-6, -4, -2, 0, 2, 4, 6):
            _NS_zharok._rect(surface, (*_NS_zharok.PALETTE["bone_high"], alpha),
                  (x + tooth, skull_y + 6, 2, 4))

        # Flames on top of skull
        _NS_zharok._draw_flame(surface, x, skull_y - 15, 6, phase, alpha)
        _NS_zharok._draw_flame(surface, x - 5, skull_y - 12, 4, phase + 1, alpha - 30)
        _NS_zharok._draw_flame(surface, x + 5, skull_y - 12, 4, phase + 2, alpha - 30)

        # Energy channels connecting skull to boss
        for i in range(3):
            t = (phase * 0.6 + i * 0.33) % 1.0
            cy = y - 20 + int((skull_y - y + 20) * t)
            cx = x + int(math.sin(t * math.pi) * 6 * (i - 1))
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_bright"], int(200 * alpha / 255)),
                      (cx, cy), 3)
            _NS_zharok._aacircle(surface, (*_NS_zharok.PALETTE["fire_hot"], int(230 * alpha / 255)),
                      (cx, cy), 2)


    # ===================================================================
    # Backward compatible alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_zharok.draw_zharok(surface, boss, x, y)

