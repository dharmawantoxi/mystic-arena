"""
bosses/level6.py - Semua boss Level 6

Gabungan dari 4 file terpisah:
  - gravewake            (mini boss)
  - syrentha             (mini boss)
  - thalgryn             (mini boss)
  - kunkka               (TRUE BOSS)

Tiap boss dibungkus dalam kelas namespace `_NS_<nama>`
supaya PALETTE dan fungsi helper-nya TIDAK saling
menimpa - 91 simbol bentrok antar file boss, termasuk
PALETTE, _aacircle, _draw_shadow, _target_position.

Kode di dalam tiap namespace TIDAK diubah isinya;
hanya referensi antar-simbol yang diberi prefix.

Entry point publik ada di bagian paling bawah file.
"""

import math
import random
import pygame

# Penanda: file ini berisi BANYAK boss (1 true + 3 mini).
# Dipakai heroes/__init__.py agar tidak menebak fungsi draw_*
# secara longgar, yang bisa mengembalikan boss yang salah.
_IS_LEVEL_BUNDLE = True



# ====================================================================
# GRAVEWAKE
# ====================================================================
class _NS_gravewake:
    """Namespace gravewake - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Tidehunter inspired teal/green sea monster
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - deep sea green/teal
        "skin_darkest":   (12,  30,  28),
        "skin_dark":      (28,  55,  50),
        "skin_mid":       (55,  95,  80),
        "skin_light":     (95, 145, 115),
        "skin_high":      (145, 190, 155),
        "skin_shine":     (195, 225, 195),

        # Belly - lighter
        "belly_dark":     (60,  80,  62),
        "belly_mid":      (110, 130, 100),
        "belly_light":    (165, 180, 145),

        # Spikes / horns - bone
        "bone_dark":      (85,  90,  60),
        "bone_mid":       (150, 155, 110),
        "bone_light":     (210, 210, 170),
        "bone_shine":     (245, 245, 220),

        # Armor / harness - dark leather
        "leather_darkest":(15,  10,   8),
        "leather_dark":   (35,  22,  15),
        "leather_mid":    (65,  42,  22),
        "leather_light":  (100, 70,  40),

        # Anchor - rusted steel
        "anchor_darkest": (25,  30,  35),
        "anchor_dark":    (55,  62,  70),
        "anchor_mid":     (95, 105, 115),
        "anchor_light":   (145, 155, 165),
        "anchor_shine":   (200, 208, 215),
        "anchor_rust":    (110, 65,  35),

        # Water - cyan/tidal
        "water_darkest":  (5,   35,  50),
        "water_dark":     (15,  85, 105),
        "water_mid":      (45, 160, 175),
        "water_light":    (110, 220, 220),
        "water_bright":   (170, 245, 240),
        "water_hot":      (215, 255, 250),
        "water_white":    (240, 255, 253),

        # Gold trim
        "gold_dark":      (95,  62,  15),
        "gold_mid":       (165, 125, 35),
        "gold_light":     (225, 185, 70),

        # Teeth (white)
        "teeth_dark":     (180, 175, 160),
        "teeth_mid":      (220, 218, 200),
        "teeth_light":    (245, 245, 232),

        # Eyes
        "eye_dark":       (95,  15,  15),
        "eye_mid":        (195, 45,  40),
        "eye_bright":     (240, 130, 80),
        "eye_hot":        (255, 220, 180),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   6,   5),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_gravewake._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_gravewake.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_gravewake._clamp(color)
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
        color = _NS_gravewake._clamp(color)
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
        color = _NS_gravewake._clamp(color)
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
        color = _NS_gravewake._clamp(color)
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
    # Water helpers
    # ---------------------------------------------------------------------------
    def _draw_water_splash(surface, x, y, size, phase, alpha=255):
        """Water splash particle."""
        flick = math.sin(phase * 3) * 0.15 + 1.0
        s = int(size * flick)
        if s < 1:
            return
        _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_darkest"], alpha // 3), (x, y), s + 3)
        _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha // 2), (x, y), s + 1)
        _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha), (x, y), s)
        _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_light"], alpha), (x, y - 1),
                  max(1, s - 2))
        _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_bright"], min(255, alpha)),
                  (x, y - 2), max(1, s - 4))


    def _draw_water_column(surface, cx, cy, height, width, phase, alpha=220):
        """Vertical water column with wave motion."""
        for i in range(height):
            t = i / max(1, height)
            wave = math.sin(phase * 3 + t * 6) * 3
            w_here = int(width * (1 - t * 0.4))
            layer_y = cy - i
            layer_x = cx + int(wave)
            _NS_gravewake._rect(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha),
                  (layer_x - w_here, layer_y, w_here * 2, 2))
            _NS_gravewake._rect(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha),
                  (layer_x - w_here + 1, layer_y, w_here * 2 - 2, 2))
            _NS_gravewake._rect(surface, (*_NS_gravewake.PALETTE["water_light"], alpha),
                  (layer_x - w_here // 2, layer_y, w_here, 2))
            _NS_gravewake._rect(surface, (*_NS_gravewake.PALETTE["water_hot"], alpha),
                  (layer_x - w_here // 4, layer_y, max(1, w_here // 2), 2))


    # ---------------------------------------------------------------------------
    # EFFECT SYSTEM
    # ---------------------------------------------------------------------------
    class AnchorSwing:
        """Q anchor swing crescent effect."""
        def __init__(self, cx, cy, direction):
            self.cx = cx
            self.cy = cy
            self.direction = direction
            self.alive = True
            self.age = 0
            self.max_age = 20

        def update(self):
            self.age += 1
            if self.age >= self.max_age:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive:
                return
            t = self.age / self.max_age
            alpha = int(255 * (1 - t * 0.6))

            # Big crescent wave slash
            for i in range(-14, 15):
                curve = math.cos(i * 0.2) * 8
                vy = self.cy + i * 2
                vx = self.cx + int(curve) * self.direction + int(t * 40) * self.direction

                w_alpha = int(alpha * (1 - abs(i) / 15))
                if w_alpha <= 0:
                    continue

                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_dark"], w_alpha), (vx, vy), 5)
                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_mid"], w_alpha), (vx, vy), 4)
                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_light"], w_alpha), (vx, vy), 3)
                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_bright"], w_alpha), (vx, vy), 2)
                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_hot"], w_alpha), (vx, vy), 1)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_gw_last_x"):
            boss._gw_last_x = boss.x
            boss._gw_last_y = boss.y
            return False
        dx = abs(boss.x - boss._gw_last_x)
        dy = abs(boss.y - boss._gw_last_y)
        boss._gw_last_x = boss.x
        boss._gw_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_gw_prev_timer", 0))
        active = bool(getattr(boss, "_gw_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._gw_attack_active = True
            boss._gw_attack_frame = 0
            active = True
        elif active:
            boss._gw_attack_frame = int(getattr(boss, "_gw_attack_frame", 0)) + 1
            if boss._gw_attack_frame > cooldown:
                boss._gw_attack_active = False
                boss._gw_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._gw_attack_active = False
            boss._gw_attack_frame = 0
            active = False

        boss._gw_prev_timer = timer
        boss._gw_attack_progress = (
            min(1.0, getattr(boss, "_gw_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_effects(boss, surface, phase):
        if not hasattr(boss, "_gw_effects"):
            boss._gw_effects = []
        for e in boss._gw_effects:
            e.update()
            e.draw(surface, phase)
        boss._gw_effects = [e for e in boss._gw_effects if e.alive]


    def _spawn_anchor_swing(boss, x, y):
        if not hasattr(boss, "_gw_effects"):
            boss._gw_effects = []
        sx = x + 25 * boss.direction
        sy = y
        boss._gw_effects.append(_NS_gravewake.AnchorSwing(sx, sy, boss.direction))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_gravewake(surface, boss, x, y):
        """Entry point."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_gravewake._detect_moving(boss)
        _NS_gravewake._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_gw_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_gravewake._draw_water_aura(surface, x, y, pulse)
        _NS_gravewake._draw_ground_runes(surface, x, y + 42, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "w":
            _NS_gravewake._draw_tidebringer_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_gravewake._draw_ravage_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if active_skill == "q":
            _NS_gravewake._draw_gravewake_anchor_smash(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_gravewake._draw_gravewake_melee_attack(surface, boss, x, y)
        elif moving:
            _NS_gravewake._draw_gravewake_walk(surface, boss, x, y)
        else:
            _NS_gravewake._draw_gravewake_idle(surface, boss, x, y)

        # Kraken Shell overlaps body
        if active_skill == "e":
            _NS_gravewake._draw_kraken_shell(surface, boss, x, y, skill_timer, pulse)

        # ---------- Effects (anchor swings, etc) ----------
        _NS_gravewake._manage_effects(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "w":
            _NS_gravewake._draw_tidebringer_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_gravewake._draw_ravage_foreground(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_gravewake_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_gravewake._draw_shadow(surface, x, y + 52)
        _NS_gravewake._draw_floating_water(surface, x, y + 40, boss.pulse)
        _NS_gravewake._draw_gravewake_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_gravewake_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_gravewake._draw_shadow(surface, x + sway, y + 52)
        _NS_gravewake._draw_floating_water(surface, x + sway, y + 40, phase, trail=True,
                            facing=boss.direction)
        _NS_gravewake._draw_gravewake_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_gravewake_melee_attack(surface, boss, x, y):
        """Anchor swing basic attack."""
        progress = getattr(boss, "_gw_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        lunge = int(math.sin(progress * math.pi) * 5) * boss.direction
        _NS_gravewake._draw_shadow(surface, x + lunge, y + 52)
        _NS_gravewake._draw_floating_water(surface, x + lunge, y + 40, boss.pulse, intense=True)
        _NS_gravewake._draw_gravewake_body(surface, x + lunge, y, boss.direction, boss.pulse,
                            "melee", progress)
        _NS_gravewake._draw_anchor_swing_trail(surface, x + lunge, y, boss.direction, progress)


    def _draw_gravewake_anchor_smash(surface, boss, x, y, timer, phase):
        """Q - Anchor smash."""
        cast_duration = 40
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        # Spawn swing effect near mid-swing
        if 0.35 < progress < 0.45 and not getattr(boss, "_gw_swing_spawned", False):
            _NS_gravewake._spawn_anchor_swing(boss, x, y)
            boss._gw_swing_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._gw_swing_spawned = False

        lunge = int(math.sin(progress * math.pi) * 7) * boss.direction
        _NS_gravewake._draw_shadow(surface, x + lunge, y + 52)
        _NS_gravewake._draw_floating_water(surface, x + lunge, y + 40, phase, intense=True)
        _NS_gravewake._draw_gravewake_body(surface, x + lunge, y, boss.direction, phase,
                           "melee", progress)
        _NS_gravewake._draw_anchor_water_trail(surface, x + lunge, y, boss.direction, progress, phase)


    # ===================================================================
    # BODY RENDERING – HD detailed Tidehunter
    # ===================================================================
    def _draw_gravewake_body(surface, cx, cy, facing, phase, action,
                            attack_progress=0):
        """Main body composition - massive hulking sea monster."""
        # Anchor (drawn behind body when idle, arm animation for melee)
        if action != "melee" or attack_progress < 0.25:
            _NS_gravewake._draw_anchor(surface, cx + facing * 22, cy + 20, facing, phase, angle=0.5)

        # Lower body / hip harness (short - most of body is torso)
        _NS_gravewake._draw_lower_body(surface, cx, cy + 20, phase)

        # Massive torso / chest
        _NS_gravewake._draw_torso(surface, cx, cy - 5, phase)

        # Back spikes (large row of bone spikes)
        _NS_gravewake._draw_back_spikes(surface, cx, cy - 15, facing, phase)

        # Arms (long, muscular)
        if action == "melee":
            _NS_gravewake._draw_melee_arms(surface, cx, cy - 5, facing, phase, attack_progress)
        else:
            _NS_gravewake._draw_idle_arms(surface, cx, cy - 5, facing, phase)

        # Head with fanged mouth and small eyes
        _NS_gravewake._draw_head(surface, cx, cy - 30, facing, phase)

        # Water droplets around body
        _NS_gravewake._draw_body_water_particles(surface, cx, cy, phase)


    def _draw_lower_body(surface, cx, cy, phase):
        """Lower hip area with belt/loincloth."""
        # Hip base (wide)
        hip_pts = [
            (cx - 22, cy - 5),
            (cx + 22, cy - 5),
            (cx + 26, cy + 8),
            (cx + 20, cy + 18),
            (cx + 10, cy + 24),
            (cx - 10, cy + 24),
            (cx - 20, cy + 18),
            (cx - 26, cy + 8),
        ]
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in hip_pts])
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["skin_darkest"], hip_pts)
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["skin_dark"], [
            (cx - 20, cy - 4),
            (cx + 20, cy - 4),
            (cx + 24, cy + 7),
            (cx + 18, cy + 17),
            (cx + 8, cy + 22),
            (cx - 8, cy + 22),
            (cx - 18, cy + 17),
            (cx - 24, cy + 7),
        ])
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["skin_mid"], [
            (cx - 17, cy - 2),
            (cx + 17, cy - 2),
            (cx + 20, cy + 6),
            (cx + 14, cy + 14),
            (cx + 5, cy + 18),
            (cx - 5, cy + 18),
            (cx - 14, cy + 14),
            (cx - 20, cy + 6),
        ])

        # Belt / harness (leather)
        _NS_gravewake._rect(surface, _NS_gravewake.PALETTE["leather_darkest"], (cx - 24, cy - 6, 48, 8))
        _NS_gravewake._rect(surface, _NS_gravewake.PALETTE["leather_dark"], (cx - 22, cy - 5, 44, 6))
        _NS_gravewake._rect(surface, _NS_gravewake.PALETTE["leather_mid"], (cx - 20, cy - 4, 40, 3))

        # Belt studs / bolts
        for i in range(-2, 3):
            bx = cx + i * 9
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["anchor_dark"], (bx, cy - 2), 2)
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["anchor_mid"], (bx, cy - 2), 1)

        # Central anchor emblem on belt
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["gold_dark"], (cx, cy - 1), 5)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["gold_mid"], (cx, cy - 1), 4)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["gold_light"], (cx - 1, cy - 2), 2)
        # Small anchor shape
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["leather_darkest"],
                (cx, cy - 3), (cx, cy + 2), 1)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["leather_darkest"],
                (cx - 2, cy - 1), (cx + 2, cy - 1), 1)

        # Loincloth hanging down (tattered)
        for i, off in enumerate((-8, -3, 3, 8)):
            wave = int(math.sin(phase * 0.8 + i) * 2)
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["leather_dark"], [
                (cx + off - 3, cy + 2),
                (cx + off + 3, cy + 2),
                (cx + off + 2 + wave, cy + 18),
                (cx + off - 2 + wave, cy + 18),
            ])
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["leather_mid"], [
                (cx + off - 2, cy + 3),
                (cx + off + 2, cy + 3),
                (cx + off + 1 + wave, cy + 15),
                (cx + off - 1 + wave, cy + 15),
            ])

        # Small spike/detail on hip
        for side in (-1, 1):
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["bone_dark"], [
                (cx + side * 22, cy - 4),
                (cx + side * 26, cy - 8),
                (cx + side * 24, cy + 2),
            ])
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["bone_mid"], [
                (cx + side * 22, cy - 4),
                (cx + side * 25, cy - 7),
                (cx + side * 23, cy + 1),
            ])


    def _draw_torso(surface, cx, cy, phase):
        """Massive muscular torso with belly."""
        # Shadow
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["shadow_deep"], [
            (cx - 24 + 3, cy - 12 + 3),
            (cx + 24 + 3, cy - 12 + 3),
            (cx + 27 + 3, cy + 5 + 3),
            (cx + 22 + 3, cy + 22 + 3),
            (cx - 22 + 3, cy + 22 + 3),
            (cx - 27 + 3, cy + 5 + 3),
        ])

        # Main torso shape (huge, muscular)
        torso_pts = [
            (cx - 24, cy - 12),
            (cx + 24, cy - 12),
            (cx + 27, cy + 5),
            (cx + 22, cy + 22),
            (cx - 22, cy + 22),
            (cx - 27, cy + 5),
        ]
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["skin_darkest"], torso_pts)
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["skin_dark"], [
            (cx - 22, cy - 10),
            (cx + 22, cy - 10),
            (cx + 25, cy + 5),
            (cx + 20, cy + 20),
            (cx - 20, cy + 20),
            (cx - 25, cy + 5),
        ])
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["skin_mid"], [
            (cx - 20, cy - 8),
            (cx + 20, cy - 8),
            (cx + 22, cy + 4),
            (cx + 17, cy + 17),
            (cx - 17, cy + 17),
            (cx - 22, cy + 4),
        ])

        # Highlight on chest muscles
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["skin_light"], (cx - 8, cy - 3), 4)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["skin_light"], (cx + 8, cy - 3), 4)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["skin_high"], (cx - 9, cy - 5), 2)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["skin_high"], (cx + 9, cy - 5), 2)

        # Belly (lighter color - central oval)
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["belly_dark"], [
            (cx - 12, cy + 2),
            (cx + 12, cy + 2),
            (cx + 14, cy + 10),
            (cx + 10, cy + 18),
            (cx - 10, cy + 18),
            (cx - 14, cy + 10),
        ])
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["belly_mid"], [
            (cx - 10, cy + 3),
            (cx + 10, cy + 3),
            (cx + 12, cy + 10),
            (cx + 8, cy + 16),
            (cx - 8, cy + 16),
            (cx - 12, cy + 10),
        ])

        # Belly scale texture
        for row in range(3):
            for col in range(-1, 2):
                sx = cx + col * 6 + (row % 2) * 3
                sy = cy + 6 + row * 4
                _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["belly_dark"], (sx, sy), 2)
                _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["belly_mid"], (sx, sy - 1), 1)
                _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["belly_light"], (sx, sy - 1), 1)

        # Scale texture on torso (dark spots)
        for i in range(8):
            angle = phase * 0.1 + i * math.pi / 4
            r = 15
            sx = cx + int(math.cos(angle) * r)
            sy = cy - 3 + int(math.sin(angle) * 8)
            if abs(sx - cx) > 12 or sy < cy - 5:  # Only outer torso, not belly
                _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["skin_darkest"], (sx, sy), 2)
                _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["skin_dark"], (sx, sy - 1), 1)

        # Pectoral divide line
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["skin_darkest"],
                (cx, cy - 10), (cx, cy + 2), 1)


    def _draw_back_spikes(surface, cx, cy, facing, phase):
        """Row of bone spikes on the back/shoulders."""
        # Large center spike
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["bone_dark"], [
            (cx - 4, cy),
            (cx + 4, cy),
            (cx, cy - 15),
        ])
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["bone_mid"], [
            (cx - 3, cy),
            (cx + 3, cy),
            (cx, cy - 13),
        ])
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["bone_light"], [
            (cx - 1, cy - 2),
            (cx + 1, cy - 2),
            (cx, cy - 12),
        ])

        # Side spikes going out
        for side_off, height in [(-8, 12), (8, 12), (-14, 10), (14, 10),
                                   (-19, 8), (19, 8)]:
            sx = cx + side_off
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["bone_dark"], [
                (sx - 3, cy + 2),
                (sx + 3, cy + 2),
                (sx + (2 if side_off > 0 else -2), cy - height),
            ])
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["bone_mid"], [
                (sx - 2, cy + 2),
                (sx + 2, cy + 2),
                (sx + (1 if side_off > 0 else -1), cy - height + 1),
            ])
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["bone_light"], [
                (sx, cy - 2),
                (sx + 1, cy - 2),
                (sx + (1 if side_off > 0 else -1), cy - height + 2),
            ])
            # Tip highlight
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["bone_shine"],
                      (sx + (2 if side_off > 0 else -2), cy - height), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Massive arms - one holding anchor, one at side."""
        sway = math.sin(phase * 0.7) * 2

        # Anchor arm (facing side) - holds anchor
        aa_x = cx + facing * 22
        aa_y = cy + 5
        ae_x = aa_x + facing * 8
        ae_y = cy + 18 + int(sway)
        ah_x = ae_x + facing * 3  # hand on anchor
        ah_y = cy + 25

        _NS_gravewake._draw_arm_segment(surface, aa_x, aa_y, ae_x, ae_y, thickness=9)
        _NS_gravewake._draw_arm_segment(surface, ae_x, ae_y, ah_x, ah_y, thickness=7)
        _NS_gravewake._draw_monster_hand(surface, ah_x, ah_y, phase)

        # Free arm (opposite side) - hangs at side, clawed
        fa_x = cx + (-facing) * 22
        fa_y = cy + 5
        fe_x = fa_x + (-facing) * 7
        fe_y = cy + 18
        fh_x = fe_x + (-facing) * 4
        fh_y = fe_y + 12

        _NS_gravewake._draw_arm_segment(surface, fa_x, fa_y, fe_x, fe_y, thickness=9)
        _NS_gravewake._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y, thickness=7)
        _NS_gravewake._draw_monster_hand(surface, fh_x, fh_y, phase)


    def _draw_melee_arms(surface, cx, cy, facing, phase, progress):
        """Anchor swing animation."""
        # Free arm stable
        fa_x = cx + (-facing) * 22
        fa_y = cy + 5
        fe_x = fa_x + (-facing) * 7
        fe_y = cy + 18
        fh_x = fe_x + (-facing) * 4
        fh_y = fe_y + 12
        _NS_gravewake._draw_arm_segment(surface, fa_x, fa_y, fe_x, fe_y, thickness=9)
        _NS_gravewake._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y, thickness=7)
        _NS_gravewake._draw_monster_hand(surface, fh_x, fh_y, phase)

        # Anchor arm - overhead swing
        aa_x = cx + facing * 22
        aa_y = cy + 5

        if progress < 0.3:
            # Wind up (raise anchor high)
            t = progress / 0.3
            arm_angle = -0.5 + (-1.3) * t  # from -0.5 to -1.8
        elif progress < 0.6:
            # Swing down and forward
            t = (progress - 0.3) / 0.3
            arm_angle = -1.8 + 2.8 * t  # from -1.8 to 1.0
        else:
            # Recovery
            t = (progress - 0.6) / 0.4
            arm_angle = 1.0 - 1.5 * t  # from 1.0 to -0.5

        ae_x = aa_x + int(math.cos(arm_angle) * 15) * facing
        ae_y = aa_y + int(math.sin(arm_angle) * 15)
        ah_x = ae_x + int(math.cos(arm_angle) * 12) * facing
        ah_y = ae_y + int(math.sin(arm_angle) * 12)

        _NS_gravewake._draw_arm_segment(surface, aa_x, aa_y, ae_x, ae_y, thickness=9)
        _NS_gravewake._draw_arm_segment(surface, ae_x, ae_y, ah_x, ah_y, thickness=7)

        # Anchor at hand position with rotation
        anchor_angle = arm_angle + 0.5
        _NS_gravewake._draw_anchor(surface, ah_x, ah_y, facing, phase, angle=anchor_angle,
                    intense=(0.3 < progress < 0.7))


    def _draw_arm_segment(surface, x1, y1, x2, y2, thickness=8):
        """Thick muscular arm segment."""
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["shadow_deep"],
                (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), thickness + 1)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["skin_darkest"], (x1, y1), (x2, y2), thickness)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["skin_dark"], (x1, y1), (x2, y2), thickness - 2)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["skin_mid"], (x1, y1), (x2, y2),
                max(1, thickness - 4))
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["skin_light"], (x1 - 1, y1 - 1),
                (x2 - 1, y2 - 1), 1)


    def _draw_monster_hand(surface, x, y, phase):
        """Clawed monster hand."""
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["shadow_deep"], (x + 1, y + 1), 5)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["skin_darkest"], (x, y), 5)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["skin_dark"], (x - 1, y - 1), 4)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["skin_mid"], (x - 1, y - 2), 3)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["skin_light"], (x - 2, y - 2), 1)

        # Claws
        for i in range(-1, 2):
            claw_angle = math.pi * 0.5 + i * 0.4
            cx1 = x + int(math.cos(claw_angle) * 4)
            cy1 = y + int(math.sin(claw_angle) * 4)
            cx2 = x + int(math.cos(claw_angle) * 8)
            cy2 = y + int(math.sin(claw_angle) * 8)
            _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["bone_dark"], (cx1, cy1), (cx2, cy2), 2)
            _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["bone_mid"], (cx1, cy1), (cx2, cy2), 1)
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["bone_light"], (cx2, cy2), 1)


    def _draw_anchor(surface, hx, hy, facing, phase, angle=0, intense=False):
        """Large rusted anchor weapon."""
        # Anchor pole/shaft
        pole_length = 35
        pole_end_x = hx - int(math.cos(angle) * pole_length) * facing
        pole_end_y = hy - int(math.sin(angle) * pole_length)

        # Pole shadow
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["shadow_deep"],
                (hx + 2, hy + 2), (pole_end_x + 2, pole_end_y + 2), 5)
        # Pole
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["anchor_darkest"],
                (hx, hy), (pole_end_x, pole_end_y), 4)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["anchor_dark"],
                (hx, hy), (pole_end_x, pole_end_y), 3)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["anchor_mid"],
                (hx, hy), (pole_end_x, pole_end_y), 2)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["anchor_light"],
                (hx - 1, hy - 1), (pole_end_x - 1, pole_end_y - 1), 1)

        # Anchor top ring (where rope goes)
        ring_x = pole_end_x
        ring_y = pole_end_y
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["anchor_darkest"], (ring_x, ring_y), 5)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["anchor_dark"], (ring_x, ring_y), 4, 2)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["anchor_mid"], (ring_x, ring_y), 3, 1)

        # Anchor arms/flukes at bottom (T-crossbar)
        # Perpendicular direction to angle
        perp = angle + math.pi / 2
        perp_x = math.cos(perp) * facing
        perp_y = math.sin(perp)

        # Cross-bar at bottom
        bar_len = 20
        bar_x1 = hx + int(perp_x * bar_len)
        bar_y1 = hy + int(perp_y * bar_len)
        bar_x2 = hx - int(perp_x * bar_len)
        bar_y2 = hy - int(perp_y * bar_len)

        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["shadow_deep"],
                (bar_x1 + 2, bar_y1 + 2), (bar_x2 + 2, bar_y2 + 2), 6)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["anchor_darkest"],
                (bar_x1, bar_y1), (bar_x2, bar_y2), 5)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["anchor_dark"],
                (bar_x1, bar_y1), (bar_x2, bar_y2), 4)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["anchor_mid"],
                (bar_x1, bar_y1), (bar_x2, bar_y2), 2)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["anchor_light"],
                (bar_x1 - 1, bar_y1 - 1), (bar_x2 - 1, bar_y2 - 1), 1)

        # Hook flukes at each end (curved barbs)
        for side_dir, endx, endy in [(1, bar_x1, bar_y1), (-1, bar_x2, bar_y2)]:
            # Fluke tip curves back toward the pole
            curve_dir_x = -math.cos(angle) * facing * side_dir
            curve_dir_y = -math.sin(angle) * side_dir
            hook_x = endx + int(math.cos(angle) * 8) * facing + int(curve_dir_x * 5)
            hook_y = endy + int(math.sin(angle) * 8) + int(curve_dir_y * 5)

            # Triangular fluke shape
            fluke_pts = [
                (endx - int(perp_x * 3 * side_dir), endy - int(perp_y * 3 * side_dir)),
                (endx + int(perp_x * 3 * side_dir), endy + int(perp_y * 3 * side_dir)),
                (hook_x, hook_y),
            ]
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["shadow_deep"],
                  [(p[0] + 2, p[1] + 2) for p in fluke_pts])
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["anchor_darkest"], fluke_pts)
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["anchor_dark"], [
                (endx - int(perp_x * 2 * side_dir),
                 endy - int(perp_y * 2 * side_dir)),
                (endx + int(perp_x * 2 * side_dir),
                 endy + int(perp_y * 2 * side_dir)),
                (hook_x, hook_y),
            ])
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["anchor_mid"], [
                (endx - int(perp_x * 1 * side_dir),
                 endy - int(perp_y * 1 * side_dir)),
                (endx + int(perp_x * 1 * side_dir),
                 endy + int(perp_y * 1 * side_dir)),
                (hook_x, hook_y),
            ])
            # Sharp tip
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["anchor_shine"], (hook_x, hook_y), 1)

        # Rust patches
        for i in range(3):
            angle_offset = i * math.pi * 2 / 3 + phase * 0.2
            rx = hx + int(math.cos(angle_offset) * 4)
            ry = hy + int(math.sin(angle_offset) * 4)
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["anchor_rust"], (rx, ry), 2)

        # Water dripping from anchor if intense
        if intense:
            for i in range(5):
                t = ((phase * 2 + i * 0.3) % 1.0)
                drip_x = hx + int(math.cos(angle - math.pi / 2) * 8) * facing
                drip_y = hy + int(math.sin(angle - math.pi / 2) * 8) + int(t * 30)
                alpha = int(220 * (1 - t))
                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha),
                          (drip_x, drip_y), 2)
                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_bright"], alpha),
                          (drip_x, drip_y), 1)


    def _draw_head(surface, cx, cy, facing, phase):
        """Large head with fanged mouth, small eyes, spikes."""
        # Neck (short and thick)
        _NS_gravewake._rect(surface, _NS_gravewake.PALETTE["skin_darkest"], (cx - 8, cy + 10, 16, 8))
        _NS_gravewake._rect(surface, _NS_gravewake.PALETTE["skin_dark"], (cx - 7, cy + 10, 14, 7))
        _NS_gravewake._rect(surface, _NS_gravewake.PALETTE["skin_mid"], (cx - 6, cy + 11, 12, 5))

        # Head shape (wide/blocky monster head)
        head_pts = [
            (cx - 15, cy - 5),
            (cx - 14, cy - 10),
            (cx - 8, cy - 13),
            (cx + 8, cy - 13),
            (cx + 14, cy - 10),
            (cx + 15, cy - 5),
            (cx + 15, cy + 6),
            (cx + 10, cy + 12),
            (cx - 10, cy + 12),
            (cx - 15, cy + 6),
        ]
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["shadow_deep"], [(p[0] + 3, p[1] + 3) for p in head_pts])
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["skin_darkest"], head_pts)
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["skin_dark"], [
            (cx - 14, cy - 4),
            (cx - 13, cy - 9),
            (cx - 7, cy - 12),
            (cx + 7, cy - 12),
            (cx + 13, cy - 9),
            (cx + 14, cy - 4),
            (cx + 14, cy + 5),
            (cx + 9, cy + 11),
            (cx - 9, cy + 11),
            (cx - 14, cy + 5),
        ])
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["skin_mid"], [
            (cx - 11, cy - 2),
            (cx - 10, cy - 7),
            (cx - 5, cy - 10),
            (cx + 5, cy - 10),
            (cx + 10, cy - 7),
            (cx + 11, cy - 2),
            (cx + 11, cy + 3),
            (cx + 7, cy + 8),
            (cx - 7, cy + 8),
            (cx - 11, cy + 3),
        ])

        # Head highlight
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["skin_light"], (cx - 5, cy - 6), 3)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["skin_high"], (cx - 6, cy - 7), 1)

        # ===== Head spikes (small ones around head) =====
        for spike_off, sy_off in [(-12, -8), (-6, -12), (0, -14),
                                    (6, -12), (12, -8)]:
            sx = cx + spike_off
            sy = cy + sy_off
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["bone_dark"], [
                (sx - 2, sy + 2),
                (sx + 2, sy + 2),
                (sx, sy - 4),
            ])
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["bone_mid"], [
                (sx - 1, sy + 2),
                (sx + 1, sy + 2),
                (sx, sy - 3),
            ])
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["bone_light"], (sx, sy - 3), 1)

        # ===== EYES (small, glowing red/orange) =====
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        # Eye ridges (dark shadow above)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["skin_darkest"],
                (cx - 8, cy - 5), (cx - 4, cy - 5), 2)
        _NS_gravewake._aaline(surface, _NS_gravewake.PALETTE["skin_darkest"],
                (cx + 4, cy - 5), (cx + 8, cy - 5), 2)

        # Eye sockets
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["shadow_deep"], (cx - 6, cy - 3), 2)
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["shadow_deep"], (cx + 6, cy - 3), 2)

        # Glowing eyes
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["eye_dark"], (cx - 6, cy - 3),
                  max(1, int(2 * eye_pulse)))
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["eye_mid"], (cx - 6, cy - 3),
                  max(1, int(1 * eye_pulse)))
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["eye_bright"], (cx - 6, cy - 3), 1)

        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["eye_dark"], (cx + 6, cy - 3),
                  max(1, int(2 * eye_pulse)))
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["eye_mid"], (cx + 6, cy - 3),
                  max(1, int(1 * eye_pulse)))
        _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["eye_bright"], (cx + 6, cy - 3), 1)

        # ===== HUGE FANGED MOUTH =====
        # Mouth opens wide
        mouth_open = 2 + int(math.sin(phase * 1.2) * 1)
        mouth_pts = [
            (cx - 10, cy + 2),
            (cx + 10, cy + 2),
            (cx + 8, cy + 8 + mouth_open),
            (cx + 4, cy + 10 + mouth_open),
            (cx - 4, cy + 10 + mouth_open),
            (cx - 8, cy + 8 + mouth_open),
        ]
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["shadow_deep"], mouth_pts)

        # Inner mouth (dark red)
        _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["eye_dark"], [
            (cx - 8, cy + 3),
            (cx + 8, cy + 3),
            (cx + 6, cy + 7 + mouth_open),
            (cx + 3, cy + 9 + mouth_open),
            (cx - 3, cy + 9 + mouth_open),
            (cx - 6, cy + 7 + mouth_open),
        ])

        # Upper teeth (row of fangs)
        for i in range(5):
            tx = cx - 7 + i * 3.5
            # Different sizes for varied fangs
            tooth_h = 3 + (1 if i in (1, 3) else 0)
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["teeth_dark"], [
                (int(tx - 1), cy + 2),
                (int(tx + 1), cy + 2),
                (int(tx), cy + 2 + tooth_h),
            ])
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["teeth_mid"], [
                (int(tx - 1), cy + 2),
                (int(tx + 1), cy + 2),
                (int(tx), cy + 1 + tooth_h),
            ])
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["teeth_light"], [
                (int(tx), cy + 2),
                (int(tx + 1), cy + 2),
                (int(tx), cy + 1 + tooth_h),
            ])

        # Lower teeth (smaller row)
        for i in range(4):
            tx = cx - 5 + i * 3.5
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["teeth_dark"], [
                (int(tx - 1), cy + 10 + mouth_open),
                (int(tx + 1), cy + 10 + mouth_open),
                (int(tx), cy + 10 + mouth_open - 3),
            ])
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["teeth_mid"], [
                (int(tx - 1), cy + 10 + mouth_open),
                (int(tx + 1), cy + 10 + mouth_open),
                (int(tx), cy + 10 + mouth_open - 2),
            ])

        # Extra large corner fangs
        for side in (-1, 1):
            cx1 = cx + side * 8
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["teeth_dark"], [
                (cx1 - 1, cy + 2),
                (cx1 + 1, cy + 2),
                (cx1 + side, cy + 8),
            ])
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["teeth_mid"], [
                (cx1 - 1, cy + 2),
                (cx1 + 1, cy + 2),
                (cx1 + side, cy + 7),
            ])
            _NS_gravewake._poly(surface, _NS_gravewake.PALETTE["teeth_light"], [
                (cx1, cy + 2),
                (cx1 + 1, cy + 2),
                (cx1 + side, cy + 6),
            ])


    def _draw_body_water_particles(surface, cx, cy, phase):
        """Water droplets around body."""
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            radius = 32 + int(math.sin(phase * 0.7 + i) * 6)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(140 + math.sin(phase + i * 0.7) * 60)
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha), (px, py), 2)
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_bright"], alpha // 2), (px, py), 1)

        # Rising water drops
        for i in range(4):
            t = ((phase * 0.4 + i * 0.25) % 1.0)
            px = cx + int(math.sin(phase + i) * 20) + (i - 1) * 4
            py = cy + 20 - int(t * 55)
            alpha = int(200 * (1 - t))
            if alpha > 0:
                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_light"], alpha), (px, py), 1)
                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_hot"], alpha), (px, py - 1), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_water(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Water mist below floating Gravewake."""
        strength = 1.5 if intense else 1.0

        # Base water mist
        mist = pygame.Surface((140, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(38, 3, -4):
            alpha = int((38 - radius) * 2.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_gravewake.PALETTE["water_darkest"], min(255, alpha)),
                    (70 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 70, cy - 12))

        # Rising water wisps
        for i, offset in enumerate((-25, -12, 0, 12, 25)):
            t = (phase * 0.5 + i * 0.2) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 25)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha), (sx, sy), 5)
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha), (sx, sy - 2), 3)
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting water droplets
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 26 + int(math.sin(phase + i * 1.3) * 4)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7)
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["water_mid"], (sx, sy), 3)
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["water_light"], (sx, sy), 2)
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["water_hot"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 130 - i * 22)
                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        """Large shadow (Gravewake is big)."""
        shadow = pygame.Surface((120, 25), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (12 - radius, 12 - radius, 96 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_gravewake.PALETTE["water_darkest"], 60),
                           (10, 5, 100, 12))
        surface.blit(shadow, (x - 60, y - 12))


    def _draw_water_aura(surface, x, y, phase):
        """Background water aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(80, 5, -4):
            alpha = int((80 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_gravewake._aacircle(aura, (*_NS_gravewake.PALETTE["water_darkest"], min(255, alpha)),
                          (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))


    def _draw_ground_runes(surface, x, y, phase, skill):
        """Water runes on ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((150, 50), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_gravewake.PALETTE["water_dark"], 140),
                            (5, 10, 140, 30), 3)
        pygame.draw.ellipse(ring, (*_NS_gravewake.PALETTE["water_mid"], 170),
                            (25, 15, 100, 20), 2)

        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 75 + int(math.cos(angle) * 35)
            y1 = 25 + int(math.sin(angle) * 8)
            x2 = 75 + int(math.cos(angle) * 65)
            y2 = 25 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_gravewake.PALETTE["water_bright"], 160),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_gravewake.PALETTE["water_hot"], int(80 * pulse)),
                                (15, 8, 120, 34), 1)

        surface.blit(ring, (x - 75, y - 25))


    def _draw_anchor_swing_trail(surface, x, y, facing, progress):
        """Trail during basic anchor swing."""
        if progress < 0.3 or progress > 0.7:
            return
        t = (progress - 0.3) / 0.4
        center_x = x + facing * 5
        center_y = y - 5
        radius = 50

        start_angle = -math.pi / 2 - 0.5
        end_angle = math.pi / 4
        current_angle = start_angle + (end_angle - start_angle) * t

        trail_length = 1.5
        segments = 12
        for i in range(segments):
            seg_t = i / segments
            angle = current_angle - trail_length * seg_t
            if angle < start_angle:
                continue

            ax = center_x + int(math.cos(angle) * radius) * facing
            ay = center_y + int(math.sin(angle) * radius)

            alpha_seg = int(220 * (1 - seg_t))
            size = int(5 * (1 - seg_t * 0.4))
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha_seg),
                      (ax, ay), size + 2)
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha_seg),
                      (ax, ay), size + 1)
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_light"], alpha_seg),
                      (ax, ay), size)


    def _draw_anchor_water_trail(surface, x, y, facing, progress, phase):
        """Enhanced water trail during Anchor Smash."""
        if progress < 0.15 or progress > 0.75:
            return

        t = (progress - 0.15) / 0.6
        center_x = x + facing * 5
        center_y = y - 5
        radius = 55

        start_angle = -math.pi / 2 - 0.5
        end_angle = math.pi / 4
        current_angle = start_angle + (end_angle - start_angle) * t

        trail_length = 2.0
        segments = 16
        for i in range(segments):
            seg_t = i / segments
            angle = current_angle - trail_length * seg_t
            if angle < start_angle:
                continue

            ax = center_x + int(math.cos(angle) * radius) * facing
            ay = center_y + int(math.sin(angle) * radius)

            alpha_seg = int(240 * (1 - seg_t))
            size = int(6 * (1 - seg_t * 0.3))

            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_darkest"], alpha_seg),
                      (ax, ay), size + 3)
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha_seg),
                      (ax, ay), size + 2)
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha_seg),
                      (ax, ay), size + 1)
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_light"], alpha_seg),
                      (ax, ay), size)
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_bright"], alpha_seg),
                      (ax, ay), max(1, size - 2))
            _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_hot"], alpha_seg),
                      (ax, ay), max(1, size - 3))


    # ===================================================================
    # SKILL W: TIDEBRINGER - Anchor pillars summoned from ground
    # ===================================================================
    def _draw_tidebringer_ground(surface, boss, x, y, timer, phase):
        """Ground indicator for anchor spawns."""
        progress = max(0.0, min(1.0, 1 - timer / 120))
        facing = boss.direction

        # Multiple anchor spawn points in front of Gravewake
        for i in range(3):
            offset = 40 + i * 40
            ax = x + facing * offset
            ay = y + 40

            pulse = math.sin(phase * 2 + i * 0.5) * 0.2 + 0.8
            radius = int(15 + progress * 8)

            # Water circle on ground
            _NS_gravewake._ellipse(surface, (*_NS_gravewake.PALETTE["water_dark"], int(180 * pulse)),
                     (ax - radius, ay - radius // 3,
                      radius * 2, radius * 2 // 3), 2)
            _NS_gravewake._ellipse(surface, (*_NS_gravewake.PALETTE["water_mid"], int(150 * pulse)),
                     (ax - radius + 3, ay - radius // 3 + 2,
                      radius * 2 - 6, radius * 2 // 3 - 4), 1)


    def _draw_tidebringer_foreground(surface, boss, x, y, timer, phase):
        """Water anchor pillars rising from ground."""
        progress = max(0.0, min(1.0, 1 - timer / 120))
        facing = boss.direction

        # 3 anchors in a line in front
        for i in range(3):
            # Each anchor rises with slight delay
            delay = i * 0.15
            anchor_progress = max(0.0, min(1.0, (progress - delay) / max(0.1, 1 - delay)))

            if anchor_progress <= 0:
                continue

            offset = 40 + i * 40
            ax = x + facing * offset
            ay = y + 20

            # Rising water column beneath anchor
            column_h = int(30 * anchor_progress)
            for h in range(column_h):
                t = h / max(1, column_h)
                wave = math.sin(phase * 4 + t * 6 + i) * 3
                w_here = int(8 * (1 - t * 0.5))
                layer_y = ay + 20 - h
                layer_x = ax + int(wave)
                alpha = int(220 * (1 - t * 0.3))
                _NS_gravewake._rect(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha),
                      (layer_x - w_here, layer_y, w_here * 2, 2))
                _NS_gravewake._rect(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha),
                      (layer_x - w_here + 1, layer_y, w_here * 2 - 2, 2))
                _NS_gravewake._rect(surface, (*_NS_gravewake.PALETTE["water_light"], alpha),
                      (layer_x - w_here // 2, layer_y, w_here, 2))

            # Draw ethereal water anchor at top of column
            if anchor_progress > 0.3:
                anchor_y = ay - 5 + int(math.sin(phase * 2 + i) * 2)
                anchor_alpha = int(255 * min(1.0, (anchor_progress - 0.3) / 0.7))
                _NS_gravewake._draw_water_anchor(surface, ax, anchor_y, phase + i, anchor_alpha)

            # Splashes around base
            for j in range(4):
                angle = phase * 2 + j * math.pi / 2 + i
                r = 12
                sx = ax + int(math.cos(angle) * r)
                sy = ay + 18 + int(math.sin(angle) * 4)
                _NS_gravewake._draw_water_splash(surface, sx, sy, 3, phase + i + j, 200)


    def _draw_water_anchor(surface, cx, cy, phase, alpha=255):
        """Ethereal water anchor floating."""
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Glow around
        _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_dark"], int(120 * pulse)),
                  (cx, cy), 20)
        _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_mid"], int(100 * pulse)),
                  (cx, cy), 15)

        # Anchor pole (vertical)
        _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha),
                (cx, cy - 15), (cx, cy + 10), 4)
        _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha),
                (cx, cy - 15), (cx, cy + 10), 3)
        _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_bright"], alpha),
                (cx, cy - 15), (cx, cy + 10), 2)
        _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_hot"], alpha),
                (cx, cy - 15), (cx, cy + 10), 1)

        # Top ring
        _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha), (cx, cy - 15), 4)
        _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha), (cx, cy - 15), 4, 2)
        _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_bright"], alpha), (cx, cy - 15), 3, 1)

        # Cross bar at bottom
        _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha),
                (cx - 10, cy + 8), (cx + 10, cy + 8), 4)
        _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha),
                (cx - 10, cy + 8), (cx + 10, cy + 8), 3)
        _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_bright"], alpha),
                (cx - 10, cy + 8), (cx + 10, cy + 8), 2)
        _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_hot"], alpha),
                (cx - 10, cy + 8), (cx + 10, cy + 8), 1)

        # Hook flukes on either side
        for side in (-1, 1):
            # Curved fluke
            _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha),
                    (cx + side * 10, cy + 8), (cx + side * 12, cy + 3), 3)
            _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha),
                    (cx + side * 10, cy + 8), (cx + side * 12, cy + 3), 2)
            _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_bright"], alpha),
                    (cx + side * 10, cy + 8), (cx + side * 12, cy + 3), 1)


    # ===================================================================
    # SKILL E: KRAKEN SHELL - Defense buff
    # ===================================================================
    def _draw_kraken_shell(surface, boss, x, y, timer, phase):
        """Water shell around Gravewake."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Multi-layer water shell
        shell_layers = [
            (55, _NS_gravewake.PALETTE["water_darkest"], 100),
            (48, _NS_gravewake.PALETTE["water_dark"], 130),
            (42, _NS_gravewake.PALETTE["water_mid"], 100),
            (36, _NS_gravewake.PALETTE["water_light"], 80),
        ]

        for radius, color, alpha in shell_layers:
            a = int(alpha * pulse * progress)
            _NS_gravewake._aacircle(surface, (*color, a), (x, y - 5), radius, 3)

        # Spiky water shell shape (like kraken shell) - draw radiating spikes
        for i in range(12):
            angle = phase * 0.8 + i * math.pi / 6
            inner_r = 40
            outer_r = 55 + int(math.sin(phase * 3 + i) * 4)

            ix = x + int(math.cos(angle) * inner_r)
            iy = y - 5 + int(math.sin(angle) * inner_r * 0.9)
            ox = x + int(math.cos(angle) * outer_r)
            oy = y - 5 + int(math.sin(angle) * outer_r * 0.9)

            # Water spike
            _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_dark"], 220),
                    (ix, iy), (ox, oy), 4)
            _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_mid"], 240),
                    (ix, iy), (ox, oy), 3)
            _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_light"], 250),
                    (ix, iy), (ox, oy), 2)
            _NS_gravewake._aaline(surface, (*_NS_gravewake.PALETTE["water_bright"], 255),
                    (ix, iy), (ox, oy), 1)
            # Tip
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["water_hot"], (ox, oy), 2)
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["water_white"], (ox, oy), 1)

        # Small circulating orbs
        for i in range(6):
            angle = phase * 1.5 + i * math.pi / 3
            r = 48
            px = x + int(math.cos(angle) * r)
            py = y - 5 + int(math.sin(angle) * r * 0.9)
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["water_bright"], (px, py), 3)
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["water_hot"], (px, py), 2)
            _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["water_white"], (px, py), 1)


    # ===================================================================
    # SKILL R: RAVAGE - Huge tidal wave/tentacles
    # ===================================================================
    def _draw_ravage_ground(surface, boss, x, y, timer, phase):
        """Large expanding water shockwave on ground."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Massive expanding rings
        for ring_i in range(3):
            ring_progress = progress - ring_i * 0.1
            if ring_progress <= 0 or ring_progress > 1:
                continue
            radius = int(20 + ring_progress * 130)
            alpha = int(220 * (1 - ring_progress))

            _NS_gravewake._ellipse(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha),
                     (x - radius, y + 40 - radius // 3,
                      radius * 2, radius * 2 // 3), 4)
            _NS_gravewake._ellipse(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha),
                     (x - radius + 4, y + 40 - radius // 3 + 2,
                      radius * 2 - 8, radius * 2 // 3 - 4), 3)
            _NS_gravewake._ellipse(surface, (*_NS_gravewake.PALETTE["water_bright"], alpha),
                     (x - radius + 8, y + 40 - radius // 3 + 4,
                      radius * 2 - 16, radius * 2 // 3 - 8), 2)


    def _draw_ravage_foreground(surface, boss, x, y, timer, phase):
        """Multiple water spikes/tentacles erupting outward."""
        progress = max(0.0, min(1.0, 1 - timer / 100))

        # Number of spikes around Gravewake, in concentric rings
        spike_rings = [
            # (radius, count, delay)
            (40, 8, 0.0),
            (75, 12, 0.15),
            (110, 16, 0.3),
            (140, 20, 0.45),
        ]

        for ring_r, count, delay in spike_rings:
            if progress < delay:
                continue

            spike_progress = min(1.0, (progress - delay) / max(0.15, 1 - delay))

            for i in range(count):
                angle = i * math.pi * 2 / count + phase * 0.3
                spike_x = x + int(math.cos(angle) * ring_r)
                spike_y = y + 40 + int(math.sin(angle) * ring_r * 0.4)

                # Skip spikes too far below character shadow
                if abs(spike_y - (y + 40)) < 5 and abs(spike_x - x) < 30:
                    continue

                # Rising water spike
                spike_height = int(50 * spike_progress * (1 - min(1.0, (progress - delay) / 0.5)))
                if spike_height < 5:
                    continue

                spike_width = 6
                for h in range(spike_height):
                    t = h / max(1, spike_height)
                    wave = math.sin(phase * 4 + t * 6 + i) * 2
                    w_here = int(spike_width * (1 - t * 0.7))
                    if w_here < 1:
                        break
                    layer_y = spike_y - h
                    layer_x = spike_x + int(wave)
                    alpha = int(230 * (1 - t * 0.3))

                    _NS_gravewake._rect(surface, (*_NS_gravewake.PALETTE["water_dark"], alpha),
                          (layer_x - w_here, layer_y, w_here * 2, 2))
                    _NS_gravewake._rect(surface, (*_NS_gravewake.PALETTE["water_mid"], alpha),
                          (layer_x - w_here + 1, layer_y, w_here * 2 - 2, 2))
                    _NS_gravewake._rect(surface, (*_NS_gravewake.PALETTE["water_light"], alpha),
                          (layer_x - w_here // 2, layer_y, w_here, 2))
                    _NS_gravewake._rect(surface, (*_NS_gravewake.PALETTE["water_hot"], alpha),
                          (layer_x - 1, layer_y, 2, 2))

                # Spike tip splash
                tip_y = spike_y - spike_height
                tip_x = spike_x + int(math.sin(phase * 4 + spike_height * 0.05 + i) * 2)
                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_mid"], 220), (tip_x, tip_y), 5)
                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_bright"], 240), (tip_x, tip_y), 3)
                _NS_gravewake._aacircle(surface, (*_NS_gravewake.PALETTE["water_hot"], 250), (tip_x, tip_y), 2)
                _NS_gravewake._aacircle(surface, _NS_gravewake.PALETTE["water_white"], (tip_x, tip_y), 1)

        # Additional splashes around Gravewake
        for i in range(10):
            angle = phase * 1.2 + i * math.pi / 5
            r = 60 + int(math.sin(phase * 2 + i) * 15)
            sx = x + int(math.cos(angle) * r)
            sy = y + 40 + int(math.sin(angle) * r * 0.4)
            _NS_gravewake._draw_water_splash(surface, sx, sy, 4, phase + i, 220)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_gravewake.draw_gravewake(surface, boss, x, y)


# ====================================================================
# SYRENTHA
# ====================================================================
class _NS_syrentha:
    """Namespace syrentha - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Naga Siren inspired teal/green/gold
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Skin - pale teal/blue-green
        "skin_darkest":   (35,  70,  75),
        "skin_dark":      (75, 120, 120),
        "skin_mid":       (125, 175, 165),
        "skin_light":     (175, 215, 200),
        "skin_shine":     (215, 240, 225),

        # Scales - deep teal/green (tail)
        "scale_darkest":  (10,  35,  40),
        "scale_dark":     (25,  70,  75),
        "scale_mid":      (50, 120, 115),
        "scale_light":    (95, 175, 160),
        "scale_high":     (150, 215, 195),
        "scale_shine":    (200, 240, 220),

        # Hair/fins - orange/gold
        "hair_darkest":   (85,  35,  10),
        "hair_dark":      (145, 70,  20),
        "hair_mid":       (215, 130, 40),
        "hair_light":     (255, 180, 75),
        "hair_shine":     (255, 220, 130),

        # Gold armor / trim
        "gold_darkest":   (75,  50,  10),
        "gold_dark":      (125, 90,  20),
        "gold_mid":       (185, 145, 40),
        "gold_light":     (235, 195, 80),
        "gold_shine":     (255, 235, 150),

        # Water - cyan/teal
        "water_darkest":  (5,   40,  50),
        "water_dark":     (15,  95, 110),
        "water_mid":      (45, 175, 175),
        "water_light":    (110, 225, 215),
        "water_bright":   (170, 245, 235),
        "water_hot":      (215, 255, 250),
        "water_white":    (240, 255, 253),

        # Spear blade
        "blade_darkest":  (30,  45,  55),
        "blade_dark":     (75,  95, 110),
        "blade_mid":      (130, 155, 175),
        "blade_light":    (185, 205, 220),
        "blade_shine":    (230, 240, 250),

        # Mirror image (translucent blue)
        "mirror_dark":    (30,  90, 130),
        "mirror_mid":     (65, 155, 190),
        "mirror_light":   (130, 210, 235),
        "mirror_hot":     (200, 240, 250),

        # Eyes
        "eye_dark":       (40,  90,  95),
        "eye_mid":        (100, 190, 180),
        "eye_bright":     (170, 235, 220),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   6,   8),
        "white":          (255, 255, 255),
        "star_yellow":    (255, 230, 90),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_syrentha._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_syrentha.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_syrentha._clamp(color)
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
        color = _NS_syrentha._clamp(color)
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
        color = _NS_syrentha._clamp(color)
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
        color = _NS_syrentha._clamp(color)
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
    # Water helpers
    # ---------------------------------------------------------------------------
    def _draw_water_splash(surface, x, y, size, phase, alpha=255):
        """Water splash particle."""
        flick = math.sin(phase * 3) * 0.15 + 1.0
        s = int(size * flick)
        if s < 1:
            return
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_darkest"], alpha // 3), (x, y), s + 3)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_dark"], alpha // 2), (x, y), s + 1)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_mid"], alpha), (x, y), s)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_light"], alpha), (x, y - 1),
                  max(1, s - 2))
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_bright"], min(255, alpha)),
                  (x, y - 2), max(1, s - 4))


    def _draw_music_note(surface, cx, cy, phase, alpha=220, size=1.0):
        """Draw a musical note."""
        # Note head (oval)
        head_r = int(3 * size)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_dark"], alpha), (cx, cy), head_r + 1)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_mid"], alpha), (cx, cy), head_r)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_light"], alpha),
                  (cx - 1, cy - 1), max(1, head_r - 1))
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_bright"], min(255, alpha)),
                  (cx - 1, cy - 1), max(1, head_r - 2))

        # Stem going up
        stem_h = int(10 * size)
        _NS_syrentha._aaline(surface, (*_NS_syrentha.PALETTE["water_dark"], alpha),
                (cx + head_r, cy), (cx + head_r, cy - stem_h), 2)
        _NS_syrentha._aaline(surface, (*_NS_syrentha.PALETTE["water_mid"], alpha),
                (cx + head_r, cy), (cx + head_r, cy - stem_h), 1)

        # Flag on top
        flag_pts = [
            (cx + head_r, cy - stem_h),
            (cx + head_r + int(4 * size), cy - stem_h + int(3 * size)),
            (cx + head_r + int(3 * size), cy - stem_h + int(6 * size)),
            (cx + head_r, cy - stem_h + int(4 * size)),
        ]
        _NS_syrentha._poly(surface, (*_NS_syrentha.PALETTE["water_mid"], alpha), flag_pts)
        _NS_syrentha._poly(surface, (*_NS_syrentha.PALETTE["water_light"], alpha), [
            (cx + head_r, cy - stem_h + 1),
            (cx + head_r + int(3 * size), cy - stem_h + int(3 * size)),
            (cx + head_r + int(2 * size), cy - stem_h + int(5 * size)),
            (cx + head_r, cy - stem_h + int(3 * size)),
        ])


    # ---------------------------------------------------------------------------
    # EFFECT SYSTEM
    # ---------------------------------------------------------------------------
    class RiptideWave:
        """Q - Water wave crescent that travels forward."""
        def __init__(self, sx, sy, direction, max_dist=180):
            self.x = float(sx)
            self.y = float(sy)
            self.start_x = float(sx)
            self.direction = direction
            self.max_dist = max_dist
            self.speed = 8.0
            self.alive = True
            self.age = 0
            self.max_age = 24

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.x += self.speed * self.direction
            if self.age >= self.max_age:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive:
                return
            t = self.age / self.max_age
            alpha = int(255 * (1 - t * 0.5))
            px, py = int(self.x), int(self.y)

            # Crescent wave
            for i in range(-13, 14):
                curve = math.cos(i * 0.22) * 7
                vy = py + i * 2
                vx = px + int(curve) * self.direction

                w_alpha = int(alpha * (1 - abs(i) / 14))
                if w_alpha <= 0:
                    continue

                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_dark"], w_alpha), (vx, vy), 4)
                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_mid"], w_alpha), (vx, vy), 3)
                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_light"], w_alpha), (vx, vy), 2)
                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_bright"], w_alpha), (vx, vy), 1)

            # Bright core arc
            for i in range(-11, 12):
                curve = math.cos(i * 0.22) * 7
                vy = py + i * 2
                vx = px + int(curve) * self.direction

                core_alpha = int(alpha * (1 - abs(i) / 12))
                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_hot"], core_alpha),
                          (vx, vy), 2)
                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_white"], core_alpha),
                          (vx, vy), 1)

            # Trailing splashes
            for i in range(5):
                angle = phase * 2 + i * math.pi / 2.5
                r = 12 + int(math.sin(phase + i) * 4)
                sx = px + int(math.cos(angle) * r) * self.direction
                sy = py + int(math.sin(angle) * r)
                _NS_syrentha._draw_water_splash(surface, sx, sy, 3, phase, alpha)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_sy_last_x"):
            boss._sy_last_x = boss.x
            boss._sy_last_y = boss.y
            return False
        dx = abs(boss.x - boss._sy_last_x)
        dy = abs(boss.y - boss._sy_last_y)
        boss._sy_last_x = boss.x
        boss._sy_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_sy_prev_timer", 0))
        active = bool(getattr(boss, "_sy_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._sy_attack_active = True
            boss._sy_attack_frame = 0
            active = True
        elif active:
            boss._sy_attack_frame = int(getattr(boss, "_sy_attack_frame", 0)) + 1
            if boss._sy_attack_frame > cooldown:
                boss._sy_attack_active = False
                boss._sy_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._sy_attack_active = False
            boss._sy_attack_frame = 0
            active = False

        boss._sy_prev_timer = timer
        boss._sy_attack_progress = (
            min(1.0, getattr(boss, "_sy_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_effects(boss, surface, phase):
        if not hasattr(boss, "_sy_effects"):
            boss._sy_effects = []
        for e in boss._sy_effects:
            e.update()
            e.draw(surface, phase)
        boss._sy_effects = [e for e in boss._sy_effects if e.alive]


    def _spawn_riptide(boss, x, y):
        if not hasattr(boss, "_sy_effects"):
            boss._sy_effects = []
        sx = x + 30 * boss.direction
        sy = y - 5
        boss._sy_effects.append(_NS_syrentha.RiptideWave(sx, sy, boss.direction))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_syrentha(surface, boss, x, y):
        """Entry point."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_syrentha._detect_moving(boss)
        _NS_syrentha._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_sy_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_syrentha._draw_water_aura(surface, x, y, pulse)
        _NS_syrentha._draw_ground_runes(surface, x, y + 45, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "w":
            _NS_syrentha._draw_enchanting_song_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_syrentha._draw_song_of_siren_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Mirror images (drawn before boss so boss appears on top) ----
        if active_skill == "e":
            _NS_syrentha._draw_mirror_images(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if active_skill == "q":
            _NS_syrentha._draw_syrentha_riptide_cast(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_syrentha._draw_syrentha_singing(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_syrentha._draw_syrentha_singing(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_syrentha._draw_syrentha_melee_attack(surface, boss, x, y)
        elif moving:
            _NS_syrentha._draw_syrentha_walk(surface, boss, x, y)
        else:
            _NS_syrentha._draw_syrentha_idle(surface, boss, x, y)

        # ---------- Effects (wave, etc) ----------
        _NS_syrentha._manage_effects(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "w":
            _NS_syrentha._draw_enchanting_song_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_syrentha._draw_song_of_siren_foreground(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_syrentha_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_syrentha._draw_shadow(surface, x, y + 55)
        _NS_syrentha._draw_floating_water(surface, x, y + 42, boss.pulse)
        _NS_syrentha._draw_syrentha_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_syrentha_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_syrentha._draw_shadow(surface, x + sway, y + 55)
        _NS_syrentha._draw_floating_water(surface, x + sway, y + 42, phase, trail=True,
                            facing=boss.direction)
        _NS_syrentha._draw_syrentha_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_syrentha_melee_attack(surface, boss, x, y):
        """Spear thrust animation."""
        progress = getattr(boss, "_sy_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        lunge = int(math.sin(progress * math.pi) * 6) * boss.direction
        _NS_syrentha._draw_shadow(surface, x + lunge, y + 55)
        _NS_syrentha._draw_floating_water(surface, x + lunge, y + 42, boss.pulse, intense=True)
        _NS_syrentha._draw_syrentha_body(surface, x + lunge, y, boss.direction, boss.pulse,
                           "melee", progress)
        _NS_syrentha._draw_spear_thrust_trail(surface, x + lunge, y, boss.direction, progress)


    def _draw_syrentha_riptide_cast(surface, boss, x, y, timer, phase):
        """Q - Riptide cast."""
        cast_duration = 40
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        if 0.35 < progress < 0.45 and not getattr(boss, "_sy_riptide_spawned", False):
            _NS_syrentha._spawn_riptide(boss, x, y)
            boss._sy_riptide_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._sy_riptide_spawned = False

        lunge = int(math.sin(progress * math.pi) * 6) * boss.direction
        _NS_syrentha._draw_shadow(surface, x + lunge, y + 55)
        _NS_syrentha._draw_floating_water(surface, x + lunge, y + 42, phase, intense=True)
        _NS_syrentha._draw_syrentha_body(surface, x + lunge, y, boss.direction, phase,
                           "melee", progress)
        _NS_syrentha._draw_spear_water_trail(surface, x + lunge, y, boss.direction, progress, phase)


    def _draw_syrentha_singing(surface, boss, x, y, timer, phase):
        """Both arms raised, singing pose (for W and R)."""
        bob = int(math.sin(phase * 1.0) * 2)
        _NS_syrentha._draw_shadow(surface, x, y + 55)
        _NS_syrentha._draw_floating_water(surface, x, y + 42, phase, intense=True)
        _NS_syrentha._draw_syrentha_body(surface, x, y + bob, boss.direction, phase, "singing")


    # ===================================================================
    # BODY RENDERING – HD detailed Naga Siren
    # ===================================================================
    def _draw_syrentha_body(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """Main body composition - upper humanoid + mermaid tail."""
        # Mermaid tail (drawn first, behind body)
        _NS_syrentha._draw_mermaid_tail(surface, cx, cy + 25, facing, phase)

        # Torso/chest with gold bra armor
        _NS_syrentha._draw_torso(surface, cx, cy - 5, phase)

        # Arms
        if action == "melee":
            _NS_syrentha._draw_melee_arms(surface, cx, cy - 5, facing, phase, attack_progress)
        elif action == "singing":
            _NS_syrentha._draw_singing_arms(surface, cx, cy - 5, facing, phase)
        else:
            _NS_syrentha._draw_idle_arms(surface, cx, cy - 5, facing, phase)

        # Head with big orange hair/fins
        _NS_syrentha._draw_head(surface, cx, cy - 25, facing, phase)

        # Big flowing fin-hair around head
        _NS_syrentha._draw_fin_hair(surface, cx, cy - 25, facing, phase)

        # Water particles around body
        _NS_syrentha._draw_body_water_particles(surface, cx, cy, phase)


    def _draw_mermaid_tail(surface, cx, cy, facing, phase):
        """Long scaled mermaid tail curving down."""
        sway = math.sin(phase * 0.6) * 4
        sway2 = math.sin(phase * 0.9 + 0.5) * 3

        # Tail curves - draw as multi-segment
        # Base (widest at hips)
        tail_base = [
            (cx - 15, cy - 8),
            (cx + 15, cy - 8),
            (cx + 18, cy + 2),
            (cx + 16, cy + 15),
            (cx + 13, cy + 25),
            (cx - 13, cy + 25),
            (cx - 16, cy + 15),
            (cx - 18, cy + 2),
        ]
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in tail_base])
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_darkest"], tail_base)
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_dark"], [
            (cx - 13, cy - 6),
            (cx + 13, cy - 6),
            (cx + 16, cy + 2),
            (cx + 14, cy + 14),
            (cx + 11, cy + 23),
            (cx - 11, cy + 23),
            (cx - 14, cy + 14),
            (cx - 16, cy + 2),
        ])
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_mid"], [
            (cx - 10, cy - 4),
            (cx + 10, cy - 4),
            (cx + 13, cy + 2),
            (cx + 11, cy + 12),
            (cx + 8, cy + 20),
            (cx - 8, cy + 20),
            (cx - 11, cy + 12),
            (cx - 13, cy + 2),
        ])

        # Highlight
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["scale_high"],
                (cx - 6, cy - 2), (cx - 4, cy + 18), 1)

        # Middle tail section (thinner)
        mid_x = cx + int(sway)
        mid_tail = [
            (cx - 13, cy + 24),
            (cx + 13, cy + 24),
            (mid_x + 11, cy + 34),
            (mid_x + 8, cy + 42),
            (mid_x - 8, cy + 42),
            (mid_x - 11, cy + 34),
        ]
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_darkest"], mid_tail)
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_dark"], [
            (cx - 11, cy + 25),
            (cx + 11, cy + 25),
            (mid_x + 9, cy + 33),
            (mid_x + 7, cy + 40),
            (mid_x - 7, cy + 40),
            (mid_x - 9, cy + 33),
        ])
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_mid"], [
            (cx - 8, cy + 26),
            (cx + 8, cy + 26),
            (mid_x + 6, cy + 32),
            (mid_x + 5, cy + 38),
            (mid_x - 5, cy + 38),
            (mid_x - 6, cy + 32),
        ])

        # Bottom tail with fin
        bot_x = mid_x + int(sway2)
        bot_tail = [
            (mid_x - 8, cy + 41),
            (mid_x + 8, cy + 41),
            (bot_x + 5, cy + 50),
            (bot_x - 5, cy + 50),
        ]
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_darkest"], bot_tail)
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_dark"], [
            (mid_x - 7, cy + 42),
            (mid_x + 7, cy + 42),
            (bot_x + 4, cy + 49),
            (bot_x - 4, cy + 49),
        ])

        # ===== Tail fin at bottom =====
        fin_x = bot_x
        fin_y = cy + 50
        # Fan-shaped fin
        fin_pts = [
            (fin_x - 4, fin_y),
            (fin_x + 4, fin_y),
            (fin_x + 15 + int(sway2), fin_y + 10),
            (fin_x + 10 + int(sway), fin_y + 15),
            (fin_x, fin_y + 12),
            (fin_x - 10 - int(sway), fin_y + 15),
            (fin_x - 15 - int(sway2), fin_y + 10),
        ]
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in fin_pts])
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_darkest"], fin_pts)
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_dark"], [
            (fin_x - 3, fin_y + 1),
            (fin_x + 3, fin_y + 1),
            (fin_x + 12 + int(sway2), fin_y + 9),
            (fin_x + 8 + int(sway), fin_y + 13),
            (fin_x, fin_y + 10),
            (fin_x - 8 - int(sway), fin_y + 13),
            (fin_x - 12 - int(sway2), fin_y + 9),
        ])
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_mid"], [
            (fin_x - 2, fin_y + 2),
            (fin_x + 2, fin_y + 2),
            (fin_x + 8, fin_y + 8),
            (fin_x + 5, fin_y + 11),
            (fin_x, fin_y + 8),
            (fin_x - 5, fin_y + 11),
            (fin_x - 8, fin_y + 8),
        ])
        # Fin ridges
        for i in range(-2, 3):
            rx1 = fin_x
            ry1 = fin_y + 2
            rx2 = fin_x + i * 4 + int(sway2 if i > 0 else -sway2)
            ry2 = fin_y + 12 - abs(i)
            _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["scale_high"], (rx1, ry1), (rx2, ry2), 1)

        # ===== Scale pattern on tail =====
        for row in range(6):
            for col in range(-2, 3):
                sx = cx + col * 5 + (row % 2) * 2
                sy = cy - 2 + row * 5
                if 0 < sy - cy < 40:
                    # Draw scale (small teardrop shape)
                    _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["scale_darkest"], (sx, sy), 3)
                    _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["scale_dark"], (sx, sy - 1), 2)
                    _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["scale_mid"], (sx, sy - 1), 1)
                    _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["scale_high"], (sx, sy - 1), 1)

        # ===== Side fins (small) =====
        for side in (-1, 1):
            fin_side_x = cx + side * 16
            fin_side_y = cy + 8
            side_fin_pts = [
                (fin_side_x, fin_side_y - 3),
                (fin_side_x + side * 8, fin_side_y - 2),
                (fin_side_x + side * 10, fin_side_y + 4),
                (fin_side_x + side * 6, fin_side_y + 8),
                (fin_side_x, fin_side_y + 5),
            ]
            _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_darkest"], side_fin_pts)
            _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["scale_dark"], [
                (fin_side_x + side * 1, fin_side_y - 2),
                (fin_side_x + side * 7, fin_side_y - 1),
                (fin_side_x + side * 8, fin_side_y + 3),
                (fin_side_x + side * 5, fin_side_y + 6),
                (fin_side_x + side * 1, fin_side_y + 4),
            ])
            _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["scale_high"],
                    (fin_side_x + side * 2, fin_side_y),
                    (fin_side_x + side * 8, fin_side_y + 4), 1)


    def _draw_torso(surface, cx, cy, phase):
        """Upper body with gold bra armor and pale skin."""
        # Torso shape (feminine curves)
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["shadow_deep"], [
            (cx - 12 + 2, cy - 10 + 2), (cx + 12 + 2, cy - 10 + 2),
            (cx + 10 + 2, cy + 12 + 2), (cx - 10 + 2, cy + 12 + 2),
        ])

        torso_pts = [
            (cx - 12, cy - 10),
            (cx - 13, cy - 5),
            (cx - 11, cy + 5),
            (cx - 10, cy + 12),
            (cx + 10, cy + 12),
            (cx + 11, cy + 5),
            (cx + 13, cy - 5),
            (cx + 12, cy - 10),
        ]
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["skin_darkest"], torso_pts)
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["skin_dark"], [
            (cx - 11, cy - 9),
            (cx - 12, cy - 4),
            (cx - 10, cy + 4),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 10, cy + 4),
            (cx + 12, cy - 4),
            (cx + 11, cy - 9),
        ])
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["skin_mid"], [
            (cx - 9, cy - 7),
            (cx - 10, cy - 3),
            (cx - 8, cy + 3),
            (cx - 6, cy + 8),
            (cx + 6, cy + 8),
            (cx + 8, cy + 3),
            (cx + 10, cy - 3),
            (cx + 9, cy - 7),
        ])

        # Highlight (shoulders/chest)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_light"], (cx - 5, cy - 4), 2)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_light"], (cx + 5, cy - 4), 2)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_shine"], (cx - 5, cy - 5), 1)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_shine"], (cx + 5, cy - 5), 1)

        # ===== Gold bra / chest armor =====
        # Two cups
        for side in (-1, 1):
            cup_x = cx + side * 5
            cup_y = cy - 2
            # Cup shape
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_darkest"], (cup_x, cup_y), 5)
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_dark"], (cup_x, cup_y), 4)
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_mid"], (cup_x - 1, cup_y - 1), 3)
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_light"], (cup_x - 1, cup_y - 2), 2)
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_shine"], (cup_x - 2, cup_y - 3), 1)

        # Center connector between cups (gold gem)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_dark"], (cx, cy), 2)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["water_mid"], (cx, cy), 1)

        # Waist/hip transition with gold trim
        _NS_syrentha._rect(surface, _NS_syrentha.PALETTE["gold_darkest"], (cx - 12, cy + 10, 24, 4))
        _NS_syrentha._rect(surface, _NS_syrentha.PALETTE["gold_dark"], (cx - 11, cy + 10, 22, 3))
        _NS_syrentha._rect(surface, _NS_syrentha.PALETTE["gold_mid"], (cx - 10, cy + 11, 20, 2))
        _NS_syrentha._rect(surface, _NS_syrentha.PALETTE["gold_light"], (cx - 8, cy + 11, 16, 1))

        # Belt gem (water/teal)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_darkest"], (cx, cy + 12), 3)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["water_dark"], (cx, cy + 12), 2)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["water_bright"], (cx, cy + 12), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Idle - spear in one hand."""
        sway = math.sin(phase * 0.7) * 2

        # Spear arm (facing side)
        sa_x = cx + facing * 11
        sa_y = cy + 2
        se_x = sa_x + facing * 8
        se_y = cy + 8 + int(sway)
        sh_x = se_x + facing * 4
        sh_y = se_y + 8
        _NS_syrentha._draw_arm_segment(surface, sa_x, sa_y, se_x, se_y)
        _NS_syrentha._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Spear
        _NS_syrentha._draw_spear(surface, sh_x, sh_y, facing, phase, angle=0.3)

        # Free arm (opposite)
        fa_x = cx + (-facing) * 11
        fa_y = cy + 2
        fe_x = fa_x + (-facing) * 6
        fe_y = cy + 8
        fh_x = fe_x + (-facing) * 3
        fh_y = fe_y + 6
        _NS_syrentha._draw_arm_segment(surface, fa_x, fa_y, fe_x, fe_y)
        _NS_syrentha._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_syrentha._draw_naga_hand(surface, fh_x, fh_y)


    def _draw_melee_arms(surface, cx, cy, facing, phase, progress):
        """Spear thrust animation."""
        # Free arm stable
        fa_x = cx + (-facing) * 11
        fa_y = cy + 2
        fe_x = fa_x + (-facing) * 6
        fe_y = cy + 8
        fh_x = fe_x + (-facing) * 3
        fh_y = fe_y + 6
        _NS_syrentha._draw_arm_segment(surface, fa_x, fa_y, fe_x, fe_y)
        _NS_syrentha._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_syrentha._draw_naga_hand(surface, fh_x, fh_y)

        # Spear arm - thrust forward
        sa_x = cx + facing * 11
        sa_y = cy + 2

        if progress < 0.3:
            # Wind up (pull back)
            t = progress / 0.3
            thrust = -6 * t
        elif progress < 0.6:
            # Thrust forward
            t = (progress - 0.3) / 0.3
            thrust = -6 + 24 * t
        else:
            # Recovery
            t = (progress - 0.6) / 0.4
            thrust = 18 - 18 * t

        se_x = sa_x + facing * (8 + int(thrust * 0.5))
        se_y = cy + 8
        sh_x = se_x + facing * (5 + int(thrust * 0.5))
        sh_y = se_y + 4

        _NS_syrentha._draw_arm_segment(surface, sa_x, sa_y, se_x, se_y)
        _NS_syrentha._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Spear pointing forward
        spear_angle = 0.1 if progress < 0.6 else 0.3
        _NS_syrentha._draw_spear(surface, sh_x, sh_y, facing, phase, angle=spear_angle,
                   intense=(0.3 < progress < 0.7))


    def _draw_singing_arms(surface, cx, cy, facing, phase):
        """Both arms raised up in singing pose."""
        sway = math.sin(phase * 1.5) * 2

        for side in (-1, 1):
            sa_x = cx + side * 11
            sa_y = cy + 2
            # Elbow raised
            se_x = sa_x + side * 8
            se_y = cy - 5 + int(sway)
            # Hand raised high
            sh_x = se_x + side * 4
            sh_y = se_y - 12 + int(sway)

            _NS_syrentha._draw_arm_segment(surface, sa_x, sa_y, se_x, se_y)
            _NS_syrentha._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)
            _NS_syrentha._draw_singing_hand(surface, sh_x, sh_y, phase)


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Skin arm segment (bare)."""
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["shadow_deep"],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 6)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["skin_darkest"], (x1, y1), (x2, y2), 5)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["skin_dark"], (x1, y1), (x2, y2), 4)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["skin_mid"], (x1, y1), (x2, y2), 2)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["skin_light"], (x1 - 1, y1 - 1), (x2 - 1, y2 - 1), 1)


    def _draw_naga_hand(surface, x, y):
        """Naga hand with slight claws."""
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["shadow_deep"], (x + 1, y + 1), 4)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_darkest"], (x, y), 3)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_dark"], (x, y - 1), 3)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_mid"], (x - 1, y - 1), 2)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_light"], (x - 1, y - 2), 1)


    def _draw_singing_hand(surface, x, y, phase):
        """Hand raised while singing - with water sparkles."""
        _NS_syrentha._draw_naga_hand(surface, x, y)
        # Glow around hand
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_dark"], int(150 * pulse)), (x, y), 8)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_mid"], int(180 * pulse)), (x, y), 6)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_light"], int(200 * pulse)), (x, y), 4)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_hot"], int(230 * pulse)), (x, y), 2)

        # Small sparkles
        for i in range(4):
            angle = phase * 2 + i * math.pi / 2
            sx = x + int(math.cos(angle) * 8)
            sy = y + int(math.sin(angle) * 8)
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["water_white"], (sx, sy), 1)


    def _draw_spear(surface, hx, hy, facing, phase, angle=0, intense=False):
        """Naga spear with curved blade."""
        length = 40
        tip_x = hx + int(math.cos(angle) * length) * facing
        tip_y = hy + int(math.sin(angle) * length)

        # Shaft
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["shadow_deep"],
                (hx + 2, hy + 2), (tip_x + 2, tip_y + 2), 4)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["gold_darkest"], (hx, hy), (tip_x, tip_y), 3)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["gold_dark"], (hx, hy), (tip_x, tip_y), 2)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["gold_mid"], (hx - 1, hy - 1), (tip_x - 1, tip_y - 1), 1)

        # Gold decorative rings on shaft
        for i in range(3):
            t = 0.25 + i * 0.25
            rx = int(hx + (tip_x - hx) * t)
            ry = int(hy + (tip_y - hy) * t)
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_darkest"], (rx, ry), 3)
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_mid"], (rx, ry), 2)
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_light"], (rx - 1, ry - 1), 1)

        # Spear blade at tip (curved leaf-shape)
        perp_angle = angle + math.pi / 2
        px = math.cos(perp_angle) * facing
        py = math.sin(perp_angle)

        blade_len = 14
        blade_tip_x = tip_x + int(math.cos(angle) * blade_len) * facing
        blade_tip_y = tip_y + int(math.sin(angle) * blade_len)

        # Blade curve mid points
        mid_x = tip_x + int(math.cos(angle) * blade_len * 0.5) * facing
        mid_y = tip_y + int(math.sin(angle) * blade_len * 0.5)

        blade_pts = [
            (tip_x + int(px * 1), tip_y + int(py * 1)),
            (mid_x + int(px * 4), mid_y + int(py * 4)),
            (blade_tip_x, blade_tip_y),
            (mid_x - int(px * 4), mid_y - int(py * 4)),
            (tip_x - int(px * 1), tip_y - int(py * 1)),
        ]
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in blade_pts])
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["blade_darkest"], blade_pts)
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["blade_dark"], [
            (tip_x, tip_y),
            (mid_x + int(px * 3), mid_y + int(py * 3)),
            (blade_tip_x, blade_tip_y),
            (mid_x - int(px * 3), mid_y - int(py * 3)),
        ])
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["blade_mid"], [
            (tip_x, tip_y),
            (mid_x + int(px * 2), mid_y + int(py * 2)),
            (blade_tip_x, blade_tip_y),
            (mid_x - int(px * 2), mid_y - int(py * 2)),
        ])
        # Blade highlight
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["blade_light"],
                (tip_x, tip_y), (blade_tip_x, blade_tip_y), 1)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["blade_shine"],
                (tip_x, tip_y), (blade_tip_x, blade_tip_y), 1)

        # Water aura on blade
        if intense:
            for i in range(4):
                t = i / 4
                bx = int(tip_x + (blade_tip_x - tip_x) * t)
                by = int(tip_y + (blade_tip_y - tip_y) * t)
                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_mid"], 200), (bx, by), 3)
                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_light"], 220), (bx, by), 2)
                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_hot"], 240), (bx, by), 1)

        # Small back-hook at base of blade (naga style)
        hook_x = tip_x - int(math.cos(angle) * 3) * facing
        hook_y = tip_y - int(math.sin(angle) * 3)
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["gold_dark"], [
            (hook_x, hook_y),
            (hook_x - int(px * 5), hook_y - int(py * 5)),
            (hook_x + int(math.cos(angle - 0.5) * 6) * facing,
             hook_y + int(math.sin(angle - 0.5) * 6)),
        ])
        _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["gold_mid"], [
            (hook_x, hook_y),
            (hook_x - int(px * 4), hook_y - int(py * 4)),
            (hook_x + int(math.cos(angle - 0.5) * 5) * facing,
             hook_y + int(math.sin(angle - 0.5) * 5)),
        ])

        # Pommel (butt of spear)
        pommel_x = hx - int(math.cos(angle) * 3) * facing
        pommel_y = hy - int(math.sin(angle) * 3)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_darkest"], (pommel_x, pommel_y), 3)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_mid"], (pommel_x, pommel_y), 2)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_shine"], (pommel_x - 1, pommel_y - 1), 1)


    def _draw_head(surface, cx, cy, facing, phase):
        """Naga head - pale skin, glowing eyes."""
        # Neck
        _NS_syrentha._rect(surface, _NS_syrentha.PALETTE["skin_dark"], (cx - 3, cy + 8, 6, 6))
        _NS_syrentha._rect(surface, _NS_syrentha.PALETTE["skin_mid"], (cx - 2, cy + 8, 4, 5))

        # Head shape
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["shadow_deep"], (cx + 2, cy + 2), 10)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_darkest"], (cx, cy), 9)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_dark"], (cx - 1, cy - 1), 8)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_mid"], (cx - 2, cy - 2), 6)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_light"], (cx - 3, cy - 3), 3)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["skin_shine"], (cx - 3, cy - 4), 1)

        # Cheek shading
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["scale_dark"], 60), (cx - 4, cy + 3), 2)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["scale_dark"], 60), (cx + 4, cy + 3), 2)

        # Eye ridges (small dark line above eyes)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["skin_darkest"],
                (cx - 5, cy - 3), (cx - 2, cy - 3), 1)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["skin_darkest"],
                (cx + 2, cy - 3), (cx + 5, cy - 3), 1)

        # Eyes - glowing teal
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["shadow_deep"], (cx - 3, cy - 1), 2)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["shadow_deep"], (cx + 3, cy - 1), 2)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["eye_dark"], (cx - 3, cy - 1),
                  max(1, int(2 * eye_pulse)))
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["eye_mid"], (cx - 3, cy - 1),
                  max(1, int(1 * eye_pulse)))
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["eye_bright"], (cx - 3, cy - 1), 1)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["eye_dark"], (cx + 3, cy - 1),
                  max(1, int(2 * eye_pulse)))
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["eye_mid"], (cx + 3, cy - 1),
                  max(1, int(1 * eye_pulse)))
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["eye_bright"], (cx + 3, cy - 1), 1)

        # Nose (small)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["skin_dark"], (cx, cy), (cx, cy + 2), 1)

        # Lips (small, singing shape)
        _NS_syrentha._rect(surface, _NS_syrentha.PALETTE["hair_darkest"], (cx - 2, cy + 4, 4, 2))
        _NS_syrentha._rect(surface, _NS_syrentha.PALETTE["hair_dark"], (cx - 2, cy + 4, 4, 1))

        # Small gold forehead gem
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["gold_dark"], (cx, cy - 6), 2)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["water_mid"], (cx, cy - 6), 1)
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["water_bright"], (cx, cy - 6), 1)

        # Gill lines on neck/cheek
        for i in range(2):
            _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["scale_darkest"],
                    (cx - 7, cy + 3 + i * 2), (cx - 5, cy + 3 + i * 2), 1)
            _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["scale_darkest"],
                    (cx + 5, cy + 3 + i * 2), (cx + 7, cy + 3 + i * 2), 1)


    def _draw_fin_hair(surface, cx, cy, facing, phase):
        """Big orange spiky fin-hair around head like a crown."""
        wave = math.sin(phase * 0.7) * 3
        wave2 = math.sin(phase * 1.0 + 0.5) * 2

        # Draw multiple spike fins radiating outward from top of head
        # Center top - large
        center_spikes = [
            (0, -25, 5),      # (x_offset, y_offset, base_width)
            (-6, -22, 4),
            (6, -22, 4),
            (-12, -18, 4),
            (12, -18, 4),
            (-16, -12, 3),
            (16, -12, 3),
        ]

        for x_off, y_off, base_w in center_spikes:
            tip_x = cx + x_off + int(wave * (x_off / 15))
            tip_y = cy + y_off - int(abs(wave2))
            # Base position on head
            base_x = cx + int(x_off * 0.4)
            base_y = cy - 6

            # Spike/fin shape
            spike_pts = [
                (base_x - base_w, base_y),
                (base_x + base_w, base_y),
                (tip_x, tip_y),
            ]
            _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["hair_darkest"], spike_pts)
            _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["hair_dark"], [
                (base_x - base_w + 1, base_y - 1),
                (base_x + base_w - 1, base_y - 1),
                (tip_x, tip_y + 1),
            ])
            _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["hair_mid"], [
                (base_x - base_w + 2, base_y - 2),
                (base_x + base_w - 2, base_y - 2),
                (tip_x, tip_y + 2),
            ])
            # Highlight streak
            _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["hair_light"],
                    (base_x, base_y - 3), (tip_x, tip_y + 3), 1)
            # Bright tip
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["hair_shine"], (tip_x, tip_y), 1)

        # Side hair - long flowing back
        for side in (-1, 1):
            hair_pts = [
                (cx + side * 8, cy - 3),
                (cx + side * 14 + int(wave * 0.5), cy + 4),
                (cx + side * 18 + int(wave), cy + 12),
                (cx + side * 16 + int(wave2), cy + 22),
                (cx + side * 12, cy + 20),
                (cx + side * 8, cy + 12),
                (cx + side * 6, cy + 3),
            ]
            _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["hair_darkest"], hair_pts)
            _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["hair_dark"], [
                (cx + side * 8, cy - 2),
                (cx + side * 13, cy + 4),
                (cx + side * 16, cy + 12),
                (cx + side * 14, cy + 20),
                (cx + side * 10, cy + 18),
                (cx + side * 7, cy + 10),
            ])
            _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["hair_mid"], [
                (cx + side * 8, cy - 1),
                (cx + side * 11, cy + 4),
                (cx + side * 13, cy + 10),
                (cx + side * 11, cy + 16),
                (cx + side * 8, cy + 8),
            ])
            # Hair streaks
            _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["hair_light"],
                    (cx + side * 9, cy + 1), (cx + side * 12, cy + 14), 1)

        # Gold crown/circlet on forehead
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["gold_dark"],
                (cx - 8, cy - 6), (cx + 8, cy - 6), 3)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["gold_mid"],
                (cx - 8, cy - 6), (cx + 8, cy - 6), 2)
        _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["gold_light"],
                (cx - 8, cy - 7), (cx + 8, cy - 7), 1)

        # Small crown points
        for i in (-6, -2, 2, 6):
            _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["gold_dark"], [
                (cx + i - 1, cy - 6),
                (cx + i + 1, cy - 6),
                (cx + i, cy - 9),
            ])
            _NS_syrentha._poly(surface, _NS_syrentha.PALETTE["gold_mid"], [
                (cx + i, cy - 6),
                (cx + i + 1, cy - 6),
                (cx + i, cy - 8),
            ])


    def _draw_body_water_particles(surface, cx, cy, phase):
        """Water droplets around body."""
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            radius = 32 + int(math.sin(phase * 0.7 + i) * 6)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(140 + math.sin(phase + i * 0.7) * 60)
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_dark"], alpha), (px, py), 2)
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_bright"], alpha // 2), (px, py), 1)

        # Rising water drops
        for i in range(5):
            t = ((phase * 0.4 + i * 0.2) % 1.0)
            px = cx + int(math.sin(phase + i) * 18) + (i - 2) * 4
            py = cy + 30 - int(t * 60)
            alpha = int(200 * (1 - t))
            if alpha > 0:
                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_light"], alpha), (px, py), 1)
                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_hot"], alpha), (px, py - 1), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_water(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Water mist below floating Syrentha."""
        strength = 1.5 if intense else 1.0

        mist = pygame.Surface((140, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(38, 3, -4):
            alpha = int((38 - radius) * 2.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_syrentha.PALETTE["water_darkest"], min(255, alpha)),
                    (70 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 70, cy - 12))

        # Rising water wisps
        for i, offset in enumerate((-25, -12, 0, 12, 25)):
            t = (phase * 0.5 + i * 0.2) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 25)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_dark"], alpha), (sx, sy), 5)
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_mid"], alpha), (sx, sy - 2), 3)
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting water orbs
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 26 + int(math.sin(phase + i * 1.3) * 4)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7)
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["water_mid"], (sx, sy), 3)
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["water_light"], (sx, sy), 2)
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["water_hot"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 130 - i * 22)
                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((110, 22), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (11 - radius, 11 - radius, 88 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_syrentha.PALETTE["water_darkest"], 60),
                           (10, 5, 90, 11))
        surface.blit(shadow, (x - 55, y - 11))


    def _draw_water_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(80, 5, -4):
            alpha = int((80 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_syrentha._aacircle(aura, (*_NS_syrentha.PALETTE["water_darkest"], min(255, alpha)),
                          (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))


    def _draw_ground_runes(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((140, 48), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_syrentha.PALETTE["water_dark"], 140),
                            (5, 10, 130, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_syrentha.PALETTE["water_mid"], 170),
                            (22, 14, 96, 20), 2)

        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 70 + int(math.cos(angle) * 32)
            y1 = 24 + int(math.sin(angle) * 8)
            x2 = 70 + int(math.cos(angle) * 60)
            y2 = 24 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_syrentha.PALETTE["water_bright"], 160),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_syrentha.PALETTE["water_hot"], int(80 * pulse)),
                                (15, 8, 110, 32), 1)

        surface.blit(ring, (x - 70, y - 24))


    def _draw_spear_thrust_trail(surface, x, y, facing, progress):
        """Trail during basic spear thrust."""
        if progress < 0.3 or progress > 0.7:
            return
        t = (progress - 0.3) / 0.4
        trail_x = x + facing * (25 + int(t * 25))
        trail_y = y - 3

        # Line trail
        for i in range(6):
            seg_t = i / 6
            ax = trail_x - facing * int(seg_t * 20)
            ay = trail_y
            alpha_seg = int(220 * (1 - seg_t))
            size = int(4 * (1 - seg_t * 0.4))
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_mid"], alpha_seg), (ax, ay), size + 1)
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_light"], alpha_seg), (ax, ay), size)
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_hot"], alpha_seg),
                      (ax, ay), max(1, size - 1))


    def _draw_spear_water_trail(surface, x, y, facing, progress, phase):
        """Enhanced water trail during Riptide cast."""
        if progress < 0.15 or progress > 0.75:
            return

        t = (progress - 0.15) / 0.6
        trail_x = x + facing * (25 + int(t * 30))
        trail_y = y - 3

        for i in range(8):
            seg_t = i / 8
            ax = trail_x - facing * int(seg_t * 25)
            ay = trail_y + int(math.sin(seg_t * math.pi + phase) * 3)
            alpha_seg = int(240 * (1 - seg_t))
            size = int(5 * (1 - seg_t * 0.3))
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_dark"], alpha_seg),
                      (ax, ay), size + 2)
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_mid"], alpha_seg),
                      (ax, ay), size + 1)
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_light"], alpha_seg),
                      (ax, ay), size)
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_bright"], alpha_seg),
                      (ax, ay), max(1, size - 1))
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_hot"], alpha_seg),
                      (ax, ay), max(1, size - 2))


    # ===================================================================
    # SKILL W: ENCHANTING SONG
    # ===================================================================
    def _draw_enchanting_song_ground(surface, boss, x, y, timer, phase):
        """Ground effect - concentric water rings."""
        progress = max(0.0, min(1.0, 1 - timer / 100))
        pulse = math.sin(phase * 2) * 0.2 + 0.8
        radius = int(50 + progress * 30)

        _NS_syrentha._ellipse(surface, (*_NS_syrentha.PALETTE["water_darkest"], int(150 * pulse)),
                 (x - radius, y + 40 - radius // 3, radius * 2, radius * 2 // 3), 4)
        _NS_syrentha._ellipse(surface, (*_NS_syrentha.PALETTE["water_dark"], int(180 * pulse)),
                 (x - radius + 5, y + 42 - radius // 3,
                  radius * 2 - 10, radius * 2 // 3 - 6), 3)
        _NS_syrentha._ellipse(surface, (*_NS_syrentha.PALETTE["water_mid"], int(150 * pulse)),
                 (x - radius + 10, y + 44 - radius // 3,
                  radius * 2 - 20, radius * 2 // 3 - 12), 2)


    def _draw_enchanting_song_foreground(surface, boss, x, y, timer, pulse):
        """Music notes rising and swirling."""
        progress = max(0.0, min(1.0, 1 - timer / 100))

        # Music notes swirling around
        note_count = 10
        for i in range(note_count):
            # Notes orbit outward
            base_angle = pulse * 0.8 + i * math.pi * 2 / note_count
            base_r = 30 + int(math.sin(pulse * 1.2 + i) * 5)
            rise = ((pulse * 0.4 + i * 0.1) % 1.0)

            # Position
            note_x = x + int(math.cos(base_angle) * base_r)
            note_y = y - 5 - int(rise * 40) + int(math.sin(base_angle) * base_r * 0.4)

            alpha = int(230 * (1 - rise * 0.5))
            size = 0.8 + math.sin(pulse * 2 + i) * 0.2
            _NS_syrentha._draw_music_note(surface, note_x, note_y, pulse + i, alpha, size)

        # Sparkles
        for i in range(8):
            angle = pulse * 1.5 + i * math.pi / 4
            r = 45 + int(math.sin(pulse * 2 + i) * 6)
            sx = x + int(math.cos(angle) * r)
            sy = y + int(math.sin(angle) * r * 0.4)
            alpha = int(200 * (math.sin(pulse * 3 + i) * 0.3 + 0.7))
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_hot"], alpha), (sx, sy), 2)
            _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["water_white"], (sx, sy), 1)

        # Sleep "Z" letters floating (if progress advanced)
        if progress > 0.5:
            for i in range(3):
                zx = x + (i - 1) * 25 + int(math.sin(pulse + i) * 4)
                zy = y - 60 - int(((pulse * 0.3 + i * 0.2) % 1.0) * 20)
                z_size = 6
                # Z shape
                _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["water_light"],
                        (zx - z_size, zy - z_size),
                        (zx + z_size, zy - z_size), 2)
                _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["water_light"],
                        (zx + z_size, zy - z_size),
                        (zx - z_size, zy + z_size), 2)
                _NS_syrentha._aaline(surface, _NS_syrentha.PALETTE["water_light"],
                        (zx - z_size, zy + z_size),
                        (zx + z_size, zy + z_size), 2)


    # ===================================================================
    # SKILL E: MIRROR IMAGE
    # ===================================================================
    def _draw_mirror_images(surface, boss, x, y, timer, phase):
        """Draw 2-3 mirror image copies around Syrentha."""
        progress = max(0.0, min(1.0, 1 - timer / 150))

        # Position of mirror images
        mirror_positions = [
            (-70, 15),
            (70, 15),
            (-40, -20),
        ]

        for i, (ox, oy) in enumerate(mirror_positions):
            # Delay per image
            delay = i * 0.1
            if progress < delay:
                continue

            img_progress = min(1.0, (progress - delay) / max(0.1, 1 - delay))

            # Position (with slight offset animation)
            mx = x + ox + int(math.sin(phase + i) * 3)
            my = y + oy + int(math.sin(phase * 1.2 + i) * 3)

            # Fade in
            alpha = int(180 * min(1.0, img_progress * 2))

            _NS_syrentha._draw_mirror_silhouette(surface, mx, my, boss.direction, phase + i, alpha)


    def _draw_mirror_silhouette(surface, cx, cy, facing, phase, alpha=180):
        """Simplified translucent water silhouette of Syrentha."""
        # Draw an ethereal water version - simplified body

        # Aura glow
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["mirror_dark"], alpha // 3), (cx, cy), 35)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["mirror_dark"], alpha // 2), (cx, cy), 25)

        # Tail (simplified)
        tail_pts = [
            (cx - 12, cy - 5),
            (cx + 12, cy - 5),
            (cx + 14, cy + 5),
            (cx + 10, cy + 20),
            (cx + 5, cy + 30),
            (cx - 5, cy + 30),
            (cx - 10, cy + 20),
            (cx - 14, cy + 5),
        ]
        _NS_syrentha._poly(surface, (*_NS_syrentha.PALETTE["mirror_dark"], alpha), tail_pts)
        _NS_syrentha._poly(surface, (*_NS_syrentha.PALETTE["mirror_mid"], alpha), [
            (cx - 10, cy - 4),
            (cx + 10, cy - 4),
            (cx + 12, cy + 5),
            (cx + 8, cy + 18),
            (cx + 4, cy + 27),
            (cx - 4, cy + 27),
            (cx - 8, cy + 18),
            (cx - 12, cy + 5),
        ])

        # Fin at bottom
        _NS_syrentha._poly(surface, (*_NS_syrentha.PALETTE["mirror_mid"], alpha), [
            (cx - 4, cy + 30),
            (cx + 4, cy + 30),
            (cx + 10, cy + 38),
            (cx + 5, cy + 42),
            (cx, cy + 38),
            (cx - 5, cy + 42),
            (cx - 10, cy + 38),
        ])

        # Torso
        _NS_syrentha._poly(surface, (*_NS_syrentha.PALETTE["mirror_dark"], alpha), [
            (cx - 10, cy - 15),
            (cx + 10, cy - 15),
            (cx + 12, cy - 5),
            (cx - 12, cy - 5),
        ])
        _NS_syrentha._poly(surface, (*_NS_syrentha.PALETTE["mirror_mid"], alpha), [
            (cx - 8, cy - 14),
            (cx + 8, cy - 14),
            (cx + 10, cy - 6),
            (cx - 10, cy - 6),
        ])

        # Head
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["mirror_dark"], alpha), (cx, cy - 22), 8)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["mirror_mid"], alpha), (cx - 1, cy - 23), 7)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["mirror_light"], alpha), (cx - 2, cy - 24), 4)

        # Hair spikes
        for x_off, y_off in [(0, -35), (-5, -32), (5, -32), (-10, -28), (10, -28)]:
            _NS_syrentha._poly(surface, (*_NS_syrentha.PALETTE["mirror_mid"], alpha), [
                (cx + int(x_off * 0.5) - 3, cy - 27),
                (cx + int(x_off * 0.5) + 3, cy - 27),
                (cx + x_off, cy + y_off),
            ])

        # Eyes (bright dots)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["mirror_hot"], min(255, alpha)),
                  (cx - 3, cy - 22), 1)
        _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["mirror_hot"], min(255, alpha)),
                  (cx + 3, cy - 22), 1)

        # Arms (simplified)
        for side in (-1, 1):
            _NS_syrentha._aaline(surface, (*_NS_syrentha.PALETTE["mirror_dark"], alpha),
                    (cx + side * 10, cy - 12), (cx + side * 14, cy), 5)
            _NS_syrentha._aaline(surface, (*_NS_syrentha.PALETTE["mirror_mid"], alpha),
                    (cx + side * 10, cy - 12), (cx + side * 14, cy), 3)

        # Water particles around image
        for i in range(4):
            angle = phase * 2 + i * math.pi / 2
            r = 20
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * r * 0.6)
            _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["mirror_hot"], alpha), (sx, sy), 1)


    # ===================================================================
    # SKILL R: SONG OF THE SIREN
    # ===================================================================
    def _draw_song_of_siren_ground(surface, boss, x, y, timer, phase):
        """Massive spiral water pattern on ground."""
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Spiral effect
        for i in range(4):
            r = 30 + i * 22
            alpha = int(150 * pulse) - i * 20
            if alpha > 0:
                _NS_syrentha._ellipse(surface, (*_NS_syrentha.PALETTE["water_dark"], alpha),
                         (x - r, y + 42 - r // 3,
                          r * 2, r * 2 // 3), 3)
                _NS_syrentha._ellipse(surface, (*_NS_syrentha.PALETTE["water_mid"], alpha),
                         (x - r + 3, y + 44 - r // 3,
                          r * 2 - 6, r * 2 // 3 - 4), 2)


    def _draw_song_of_siren_foreground(surface, boss, x, y, timer, pulse):
        """Huge spiral of music notes and stars - stunning waves."""
        progress = max(0.0, min(1.0, 1 - timer / 120))

        # Concentric expanding water rings
        for ring_i in range(4):
            ring_phase = pulse - ring_i * 0.3
            ring_r = int(40 + (ring_phase % 2) * 60)
            alpha = int(180 * (1 - (ring_phase % 2) / 2))

            _NS_syrentha._ellipse(surface, (*_NS_syrentha.PALETTE["water_dark"], alpha),
                     (x - ring_r, y - ring_r // 3,
                      ring_r * 2, ring_r * 2 // 3), 3)
            _NS_syrentha._ellipse(surface, (*_NS_syrentha.PALETTE["water_mid"], alpha),
                     (x - ring_r + 3, y - ring_r // 3 + 2,
                      ring_r * 2 - 6, ring_r * 2 // 3 - 4), 2)
            _NS_syrentha._ellipse(surface, (*_NS_syrentha.PALETTE["water_bright"], alpha),
                     (x - ring_r + 6, y - ring_r // 3 + 4,
                      ring_r * 2 - 12, ring_r * 2 // 3 - 8), 1)

        # Spiral music notes
        for i in range(15):
            # Spiral outward
            angle = pulse * 1.2 + i * 0.5
            r = 20 + i * 8
            note_x = x + int(math.cos(angle) * r)
            note_y = y - 5 + int(math.sin(angle) * r * 0.5)

            alpha = int(230 * (1 - i / 15 * 0.3))
            size = 1.0 - i * 0.03
            if size > 0.5:
                _NS_syrentha._draw_music_note(surface, note_x, note_y, pulse + i, alpha, size)

        # Stars (stun indicator)
        for i in range(8):
            angle = pulse * 0.8 + i * math.pi / 4
            r = 70 + int(math.sin(pulse * 2 + i) * 8)
            sx = x + int(math.cos(angle) * r)
            sy = y - 20 + int(math.sin(angle) * r * 0.5)
            _NS_syrentha._draw_star(surface, sx, sy, size=4,
                      color=_NS_syrentha.PALETTE["star_yellow"])

        # Rising particles from center
        for i in range(10):
            t = ((pulse * 0.5 + i * 0.1) % 1.0)
            angle = i * math.pi / 5
            px = x + int(math.cos(angle) * 30 * (1 - t))
            py = y - int(t * 60)
            alpha = int(220 * (1 - t))
            if alpha > 0:
                _NS_syrentha._aacircle(surface, (*_NS_syrentha.PALETTE["water_bright"], alpha), (px, py), 2)
                _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["water_white"], (px, py), 1)


    def _draw_star(surface, cx, cy, size=4, color=None):
        """Draw a 4-pointed star (stun indicator)."""
        if color is None:
            color = _NS_syrentha.PALETTE["star_yellow"]
        # Vertical spike
        _NS_syrentha._aaline(surface, color, (cx, cy - size), (cx, cy + size), 2)
        # Horizontal spike
        _NS_syrentha._aaline(surface, color, (cx - size, cy), (cx + size, cy), 2)
        # Diagonal (smaller)
        _NS_syrentha._aaline(surface, color, (cx - size // 2, cy - size // 2),
                (cx + size // 2, cy + size // 2), 1)
        _NS_syrentha._aaline(surface, color, (cx - size // 2, cy + size // 2),
                (cx + size // 2, cy - size // 2), 1)
        # Bright center
        _NS_syrentha._aacircle(surface, _NS_syrentha.PALETTE["white"], (cx, cy), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_syrentha.draw_syrentha(surface, boss, x, y)


# ====================================================================
# THALGRYN
# ====================================================================
class _NS_thalgryn:
    """Namespace thalgryn - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Morphling inspired water elemental (cyan/teal/blue)
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Water body - translucent teal/cyan
        "water_darkest":  (5,   30,  45),
        "water_dark":     (18,  70, 100),
        "water_mid":      (40, 130, 165),
        "water_light":    (85, 190, 210),
        "water_high":     (140, 225, 235),
        "water_shine":    (200, 245, 250),
        "water_white":    (240, 255, 255),

        # Deeper body core
        "core_darkest":   (8,   40,  55),
        "core_dark":      (25,  85, 110),
        "core_mid":       (55, 145, 170),
        "core_light":     (110, 205, 220),

        # Bright water highlights (surface reflections)
        "reflect_dark":   (95, 200, 220),
        "reflect_mid":    (150, 230, 240),
        "reflect_light":  (210, 250, 253),
        "reflect_hot":    (245, 255, 255),

        # Eyes - glowing cyan
        "eye_dark":       (30, 120, 145),
        "eye_mid":        (100, 210, 220),
        "eye_bright":     (180, 245, 250),
        "eye_hot":        (230, 255, 255),

        # Attribute icons colors
        "str_red":        (200, 40, 40),
        "str_hot":        (255, 100, 90),
        "agi_green":      (60, 190, 70),
        "agi_hot":        (140, 240, 120),
        "int_blue":       (50, 130, 220),
        "int_hot":        (140, 200, 255),

        # Ground / misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   6,   8),
        "white":          (255, 255, 255),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_thalgryn._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_thalgryn.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_thalgryn._clamp(color)
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
        color = _NS_thalgryn._clamp(color)
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
        color = _NS_thalgryn._clamp(color)
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
        color = _NS_thalgryn._clamp(color)
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
    # Water helpers
    # ---------------------------------------------------------------------------
    def _draw_water_droplet(surface, x, y, size, phase, alpha=255):
        """Small water droplet."""
        flick = math.sin(phase * 3) * 0.15 + 1.0
        s = int(size * flick)
        if s < 1:
            return
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_darkest"], alpha // 3), (x, y), s + 3)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_dark"], alpha // 2), (x, y), s + 1)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha), (x, y), s)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_light"], alpha), (x, y - 1),
                  max(1, s - 2))
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_high"], min(255, alpha)),
                  (x, y - 2), max(1, s - 4))


    def _draw_water_splash(surface, x, y, size, phase, alpha=255):
        """Water splash particle upward."""
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_darkest"], alpha // 3), (x, y), size + 3)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_dark"], alpha // 2), (x, y), size + 1)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha), (x, y), size)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_light"], alpha), (x, y - 1),
                  max(1, size - 2))
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_high"], min(255, alpha)),
                  (x, y - 2), max(1, size - 4))
        if size > 3:
            _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_shine"], min(255, alpha)),
                      (x, y - 2), max(1, size - 6))


    # ---------------------------------------------------------------------------
    # PROJECTILE SYSTEM
    # ---------------------------------------------------------------------------
    class AdaptiveStrikeProjectile:
        """W - Water spike projectile (like an icicle/spear of water)."""
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
            if len(self.trail) > 14:
                self.trail.pop(0)
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        def draw(self, surface, phase):
            if not self.alive and self.age < 3:
                return

            # Long trail
            for i, (tx, ty) in enumerate(self.trail):
                alpha = int(40 + i * 15)
                r = max(1, 5 - (len(self.trail) - i) // 2)
                _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_dark"], alpha), (tx, ty), r + 2)
                _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha), (tx, ty), r + 1)
                _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_light"], alpha), (tx, ty), r)
                _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_high"], alpha // 2),
                          (tx, ty), max(1, r - 1))

            if self.alive:
                px, py = int(self.x), int(self.y)
                # Elongated spear/icicle shape
                perp = self.angle + math.pi / 2
                tip_x = px + int(math.cos(self.angle) * 14)
                tip_y = py + int(math.sin(self.angle) * 14)
                back_x = px - int(math.cos(self.angle) * 6)
                back_y = py - int(math.sin(self.angle) * 6)
                side1_x = px + int(math.cos(perp) * 4)
                side1_y = py + int(math.sin(perp) * 4)
                side2_x = px - int(math.cos(perp) * 4)
                side2_y = py - int(math.sin(perp) * 4)

                # Layered spear
                _NS_thalgryn._poly(surface, (*_NS_thalgryn.PALETTE["water_darkest"], 200), [
                    (tip_x, tip_y),
                    (side1_x, side1_y),
                    (back_x, back_y),
                    (side2_x, side2_y)
                ])
                _NS_thalgryn._poly(surface, (*_NS_thalgryn.PALETTE["water_dark"], 220), [
                    (tip_x, tip_y),
                    (px + int(math.cos(perp) * 3), py + int(math.sin(perp) * 3)),
                    (back_x, back_y),
                    (px - int(math.cos(perp) * 3), py - int(math.sin(perp) * 3))
                ])
                _NS_thalgryn._poly(surface, (*_NS_thalgryn.PALETTE["water_mid"], 240), [
                    (tip_x, tip_y),
                    (px + int(math.cos(perp) * 2), py + int(math.sin(perp) * 2)),
                    (back_x, back_y),
                    (px - int(math.cos(perp) * 2), py - int(math.sin(perp) * 2))
                ])
                _NS_thalgryn._poly(surface, (*_NS_thalgryn.PALETTE["water_light"], 250), [
                    (tip_x, tip_y),
                    (px + int(math.cos(perp) * 1), py + int(math.sin(perp) * 1)),
                    (back_x, back_y),
                    (px - int(math.cos(perp) * 1), py - int(math.sin(perp) * 1))
                ])

                # Bright core line
                _NS_thalgryn._aaline(surface, _NS_thalgryn.PALETTE["water_high"],
                        (back_x, back_y), (tip_x, tip_y), 2)
                _NS_thalgryn._aaline(surface, _NS_thalgryn.PALETTE["water_shine"],
                        (back_x, back_y), (tip_x, tip_y), 1)

                # Bright tip
                _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_shine"], (tip_x, tip_y), 3)
                _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_white"], (tip_x, tip_y), 2)

                # Radiating sparkles
                for i in range(4):
                    spark_angle = phase * 4 + i * math.pi / 2
                    sx = px + int(math.cos(spark_angle) * 10)
                    sy = py + int(math.sin(spark_angle) * 10)
                    _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_shine"], (sx, sy), 1)


    class WaveformDash:
        """Q - Waveform effect - Thalgryn becomes a wave."""
        def __init__(self, sx, sy, direction, max_dist=200):
            self.start_x = sx
            self.start_y = sy
            self.x = float(sx)
            self.y = float(sy)
            self.direction = direction
            self.speed = 12.0
            self.alive = True
            self.age = 0
            self.max_age = 20

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.x += self.speed * self.direction
            if self.age >= self.max_age:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive:
                return
            t = self.age / self.max_age

            # Trail of dashes
            for trail_i in range(6):
                trail_t = trail_i / 6
                trail_x = self.x - self.speed * trail_i * 2 * self.direction
                alpha = int(240 * (1 - trail_t) * (1 - t * 0.5))

                # Wave/water shape blob
                for j in range(-8, 9):
                    curve = math.cos(j * 0.2) * 4
                    vy = self.y + j * 2
                    vx = int(trail_x) + int(curve) * self.direction

                    w_alpha = int(alpha * (1 - abs(j) / 9))
                    if w_alpha <= 0:
                        continue

                    _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_darkest"], w_alpha),
                              (vx, vy), 5)
                    _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_dark"], w_alpha),
                              (vx, vy), 4)
                    _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_mid"], w_alpha),
                              (vx, vy), 3)
                    _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_light"], w_alpha),
                              (vx, vy), 2)
                    _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_high"], w_alpha),
                              (vx, vy), 1)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_th_last_x"):
            boss._th_last_x = boss.x
            boss._th_last_y = boss.y
            return False
        dx = abs(boss.x - boss._th_last_x)
        dy = abs(boss.y - boss._th_last_y)
        boss._th_last_x = boss.x
        boss._th_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_th_prev_timer", 0))
        active = bool(getattr(boss, "_th_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._th_attack_active = True
            boss._th_attack_frame = 0
            active = True
        elif active:
            boss._th_attack_frame = int(getattr(boss, "_th_attack_frame", 0)) + 1
            if boss._th_attack_frame > cooldown:
                boss._th_attack_active = False
                boss._th_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._th_attack_active = False
            boss._th_attack_frame = 0
            active = False

        boss._th_prev_timer = timer
        boss._th_attack_progress = (
            min(1.0, getattr(boss, "_th_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_projectiles(boss, surface, phase):
        if not hasattr(boss, "_th_projectiles"):
            boss._th_projectiles = []
        for p in boss._th_projectiles:
            p.update()
            p.draw(surface, phase)
        boss._th_projectiles = [p for p in boss._th_projectiles
                               if p.alive or p.age < 8]


    def _spawn_basic_projectile(boss, x, y):
        if not hasattr(boss, "_th_projectiles"):
            boss._th_projectiles = []
        tx, ty = _NS_thalgryn._target_position(boss, x, y)
        sx = x + 22 * boss.direction
        sy = y - 10
        boss._th_projectiles.append(_NS_thalgryn.AdaptiveStrikeProjectile(sx, sy, tx, ty, speed=7.0))


    def _spawn_adaptive_strike(boss, x, y):
        if not hasattr(boss, "_th_projectiles"):
            boss._th_projectiles = []
        tx, ty = _NS_thalgryn._target_position(boss, x, y)
        sx = x + 22 * boss.direction
        sy = y - 10
        boss._th_projectiles.append(_NS_thalgryn.AdaptiveStrikeProjectile(sx, sy, tx, ty, speed=10.0))


    def _manage_effects(boss, surface, phase):
        if not hasattr(boss, "_th_effects"):
            boss._th_effects = []
        for e in boss._th_effects:
            e.update()
            e.draw(surface, phase)
        boss._th_effects = [e for e in boss._th_effects if e.alive]


    def _spawn_waveform(boss, x, y):
        if not hasattr(boss, "_th_effects"):
            boss._th_effects = []
        boss._th_effects.append(_NS_thalgryn.WaveformDash(x, y - 10, boss.direction))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_thalgryn(surface, boss, x, y):
        """Entry point."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_thalgryn._detect_moving(boss)
        _NS_thalgryn._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_th_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_thalgryn._draw_water_aura(surface, x, y, pulse)
        _NS_thalgryn._draw_ground_runes(surface, x, y + 45, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "e":
            _NS_thalgryn._draw_morph_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thalgryn._draw_replicate_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Replicate copies drawn behind main ----------
        if active_skill == "r":
            _NS_thalgryn._draw_replicates(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if active_skill == "q":
            _NS_thalgryn._draw_thalgryn_waveform(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thalgryn._draw_thalgryn_morph(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_thalgryn._draw_thalgryn_attack(surface, boss, x, y)
        elif moving:
            _NS_thalgryn._draw_thalgryn_walk(surface, boss, x, y)
        else:
            _NS_thalgryn._draw_thalgryn_idle(surface, boss, x, y)

        # ---------- Projectiles ----------
        _NS_thalgryn._manage_projectiles(boss, surface, pulse)

        # ---------- Effects ----------
        _NS_thalgryn._manage_effects(boss, surface, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_thalgryn_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 3)
        _NS_thalgryn._draw_shadow(surface, x, y + 55)
        _NS_thalgryn._draw_water_base(surface, x, y + 42, boss.pulse)
        _NS_thalgryn._draw_thalgryn_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_thalgryn_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 4)
        sway = int(math.sin(phase) * 2)
        _NS_thalgryn._draw_shadow(surface, x + sway, y + 55)
        _NS_thalgryn._draw_water_base(surface, x + sway, y + 42, phase, trail=True,
                        facing=boss.direction)
        _NS_thalgryn._draw_thalgryn_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_thalgryn_attack(surface, boss, x, y):
        progress = getattr(boss, "_th_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        if 0.28 < progress < 0.35 and not getattr(boss, "_th_proj_spawned", False):
            _NS_thalgryn._spawn_basic_projectile(boss, x, y)
            boss._th_proj_spawned = True
        if progress < 0.1 or progress > 0.9:
            boss._th_proj_spawned = False

        recoil = int(math.sin(progress * math.pi) * 3) * -boss.direction
        _NS_thalgryn._draw_shadow(surface, x + recoil, y + 55)
        _NS_thalgryn._draw_water_base(surface, x + recoil, y + 42, boss.pulse, intense=True)
        _NS_thalgryn._draw_thalgryn_body(surface, x + recoil, y, boss.direction, boss.pulse,
                           "attack", progress)
        _NS_thalgryn._draw_cast_flash(surface, x + recoil, y, boss.direction, progress)


    def _draw_thalgryn_waveform(surface, boss, x, y, timer, phase):
        """Q - Waveform - transforms to wave."""
        cast_duration = 40
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        if 0.3 < progress < 0.4 and not getattr(boss, "_th_wave_spawned", False):
            _NS_thalgryn._spawn_waveform(boss, x, y)
            boss._th_wave_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._th_wave_spawned = False

        # Body dissolves into wave then reforms
        if 0.25 < progress < 0.65:
            # Dissolved - draw sparse water splashes at position
            _NS_thalgryn._draw_shadow(surface, x, y + 55)
            for i in range(15):
                angle = phase * 3 + i * math.pi / 7
                r = 20 + int(math.sin(phase * 4 + i) * 8)
                sx = x + int(math.cos(angle) * r)
                sy = y - 10 + int(math.sin(angle) * r * 0.6)
                alpha = int(180 * math.sin(phase * 3 + i))
                if alpha > 0:
                    _NS_thalgryn._draw_water_splash(surface, sx, sy, 3, phase + i, alpha)
        else:
            # Normal body
            bob = int(math.sin(phase * 1.5) * 2)
            _NS_thalgryn._draw_shadow(surface, x, y + 55)
            _NS_thalgryn._draw_water_base(surface, x, y + 42, phase, intense=True)
            _NS_thalgryn._draw_thalgryn_body(surface, x, y + bob, boss.direction, phase, "idle")


    def _draw_thalgryn_morph(surface, boss, x, y, timer, phase):
        """E - Morph - body shifts colors based on attribute selected."""
        bob = int(math.sin(phase * 1.5) * 2)
        _NS_thalgryn._draw_shadow(surface, x, y + 55)
        _NS_thalgryn._draw_water_base(surface, x, y + 42, phase, intense=True)

        # Draw with morph glow color overlay
        # Cycle through STR/AGI/INT
        morph_cycle = int(phase * 2) % 3
        morph_color = [_NS_thalgryn.PALETTE["str_red"], _NS_thalgryn.PALETTE["agi_green"],
                       _NS_thalgryn.PALETTE["int_blue"]][morph_cycle]
        hot_color = [_NS_thalgryn.PALETTE["str_hot"], _NS_thalgryn.PALETTE["agi_hot"],
                    _NS_thalgryn.PALETTE["int_hot"]][morph_cycle]

        _NS_thalgryn._draw_thalgryn_body(surface, x, y + bob, boss.direction, phase, "morph")

        # Overlay morph aura
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        _NS_thalgryn._aacircle(surface, (*morph_color, int(120 * pulse)), (x, y - 5), 45)
        _NS_thalgryn._aacircle(surface, (*morph_color, int(80 * pulse)), (x, y - 5), 55)
        _NS_thalgryn._aacircle(surface, (*hot_color, int(100 * pulse)), (x, y - 5), 35)

        # Attribute icon floating above
        _NS_thalgryn._draw_attribute_icon(surface, x, y - 55 + int(math.sin(phase * 2) * 3),
                             morph_cycle, phase)


    # ===================================================================
    # BODY RENDERING – HD Water Elemental
    # ===================================================================
    def _draw_thalgryn_body(surface, cx, cy, facing, phase, action,
                           attack_progress=0):
        """Main body composition - water elemental."""
        # Body wobble/undulation (water is fluid)
        wobble = math.sin(phase * 2) * 2

        # Lower body (dissolves into water)
        _NS_thalgryn._draw_lower_water_body(surface, cx, cy + 15, phase, wobble)

        # Torso (fluid water shape)
        _NS_thalgryn._draw_water_torso(surface, cx, cy - 5, phase, wobble)

        # Arms (fluid)
        if action == "attack" or action == "morph":
            _NS_thalgryn._draw_casting_arms(surface, cx, cy - 5, facing, phase, attack_progress)
        else:
            _NS_thalgryn._draw_idle_arms(surface, cx, cy - 5, facing, phase)

        # Head (glossy water head)
        _NS_thalgryn._draw_water_head(surface, cx, cy - 28, facing, phase)

        # Water reflections and shine on body
        _NS_thalgryn._draw_body_reflections(surface, cx, cy, phase)


    def _draw_lower_water_body(surface, cx, cy, phase, wobble):
        """Lower body dissolves into water column."""
        sway = math.sin(phase * 0.7) * 3
        sway2 = math.sin(phase * 1.0 + 0.5) * 2

        # Wide flowing bottom (dissolves)
        lower_pts = [
            (cx - 18 + int(wobble), cy - 5),
            (cx + 18 - int(wobble), cy - 5),
            (cx + 22 + int(sway), cy + 5),
            (cx + 20 + int(sway2), cy + 18),
            (cx + 14, cy + 28),
            (cx + 6, cy + 35 + int(sway2)),
            (cx - 6, cy + 35 - int(sway2)),
            (cx - 14, cy + 28),
            (cx - 20 - int(sway2), cy + 18),
            (cx - 22 - int(sway), cy + 5),
        ]

        # Shadow
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in lower_pts])

        # Layered water body
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_darkest"], lower_pts)
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_dark"], [
            (cx - 16 + int(wobble), cy - 4),
            (cx + 16 - int(wobble), cy - 4),
            (cx + 20 + int(sway), cy + 5),
            (cx + 18 + int(sway2), cy + 17),
            (cx + 12, cy + 26),
            (cx + 5, cy + 32),
            (cx - 5, cy + 32),
            (cx - 12, cy + 26),
            (cx - 18 - int(sway2), cy + 17),
            (cx - 20 - int(sway), cy + 5),
        ])
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_mid"], [
            (cx - 13, cy - 2),
            (cx + 13, cy - 2),
            (cx + 16, cy + 6),
            (cx + 14, cy + 16),
            (cx + 10, cy + 24),
            (cx + 3, cy + 28),
            (cx - 3, cy + 28),
            (cx - 10, cy + 24),
            (cx - 14, cy + 16),
            (cx - 16, cy + 6),
        ])
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_light"], [
            (cx - 10, cy),
            (cx + 10, cy),
            (cx + 12, cy + 6),
            (cx + 10, cy + 15),
            (cx + 7, cy + 22),
            (cx - 7, cy + 22),
            (cx - 10, cy + 15),
            (cx - 12, cy + 6),
        ])

        # Bottom tapering wisps (water drips)
        for i, off in enumerate((-8, -4, 0, 4, 8)):
            wave = int(math.sin(phase * 2 + i) * 2)
            drop_h = 5 + i % 3
            _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_mid"], [
                (cx + off - 3, cy + 30),
                (cx + off + 3, cy + 30),
                (cx + off + wave + 1, cy + 30 + drop_h),
                (cx + off + wave - 1, cy + 30 + drop_h),
            ])
            _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_light"],
                      (cx + off + wave, cy + 30 + drop_h), 1)

        # Inner core glow (bright water heart)
        core_pulse = math.sin(phase * 1.5) * 0.2 + 0.8
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_high"], int(180 * core_pulse)),
                  (cx, cy + 8), 6)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_shine"], int(220 * core_pulse)),
                  (cx, cy + 8), 3)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_white"], int(240 * core_pulse)),
                  (cx, cy + 8), 1)


    def _draw_water_torso(surface, cx, cy, phase, wobble):
        """Fluid water torso."""
        # Torso shape - broad shoulders narrowing to waist
        torso_pts = [
            (cx - 14, cy - 10),
            (cx + 14, cy - 10),
            (cx + 16 + int(wobble), cy - 2),
            (cx + 14, cy + 8),
            (cx + 10, cy + 15),
            (cx - 10, cy + 15),
            (cx - 14, cy + 8),
            (cx - 16 - int(wobble), cy - 2),
        ]

        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in torso_pts])
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_darkest"], torso_pts)
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_dark"], [
            (cx - 12, cy - 9),
            (cx + 12, cy - 9),
            (cx + 14 + int(wobble), cy - 2),
            (cx + 12, cy + 7),
            (cx + 8, cy + 13),
            (cx - 8, cy + 13),
            (cx - 12, cy + 7),
            (cx - 14 - int(wobble), cy - 2),
        ])
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_mid"], [
            (cx - 10, cy - 7),
            (cx + 10, cy - 7),
            (cx + 11, cy - 2),
            (cx + 9, cy + 5),
            (cx + 5, cy + 11),
            (cx - 5, cy + 11),
            (cx - 9, cy + 5),
            (cx - 11, cy - 2),
        ])
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_light"], [
            (cx - 7, cy - 4),
            (cx + 7, cy - 4),
            (cx + 8, cy),
            (cx + 5, cy + 7),
            (cx - 5, cy + 7),
            (cx - 8, cy),
        ])

        # Chest highlight (light hits the water surface)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_high"], (cx - 4, cy - 3), 2)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_shine"], (cx - 5, cy - 4), 1)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["reflect_hot"], (cx - 5, cy - 5), 1)

        # Right side highlight
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_high"], (cx + 4, cy - 3), 2)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_shine"], (cx + 5, cy - 4), 1)

        # Deeper core spot (like a heart of water)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["core_dark"], (cx, cy + 2), 4)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["core_mid"], (cx, cy + 2), 3)
        core_pulse = math.sin(phase * 1.5) * 0.3 + 0.7
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_high"], int(220 * core_pulse)),
                  (cx, cy + 2), max(1, int(2 * core_pulse)))
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_shine"], int(240 * core_pulse)),
                  (cx, cy + 2), 1)

        # Water surface ripple lines
        for i in range(3):
            yoff = cy - 5 + i * 4
            _NS_thalgryn._aaline(surface, (*_NS_thalgryn.PALETTE["water_light"], 120),
                    (cx - 8 + int(math.sin(phase + i) * 2), yoff),
                    (cx + 8 - int(math.sin(phase + i) * 2), yoff), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Fluid water arms hanging at sides."""
        sway = math.sin(phase * 0.7) * 3
        sway2 = math.sin(phase * 0.9 + 0.5) * 2

        for side in (-1, 1):
            # Shoulder
            sh_x = cx + side * 14
            sh_y = cy - 2
            # Elbow (slightly out)
            el_x = sh_x + side * 8 + int(sway if side > 0 else -sway) // 2
            el_y = cy + 8
            # Hand
            hd_x = el_x + side * 4 + int(sway2 if side > 0 else -sway2)
            hd_y = el_y + 12

            _NS_thalgryn._draw_water_arm_segment(surface, sh_x, sh_y, el_x, el_y, phase, thickness=7)
            _NS_thalgryn._draw_water_arm_segment(surface, el_x, el_y, hd_x, hd_y, phase, thickness=6)
            _NS_thalgryn._draw_water_hand(surface, hd_x, hd_y, phase)


    def _draw_casting_arms(surface, cx, cy, facing, phase, progress):
        """One arm raised forward for casting."""
        sway = math.sin(phase * 0.7) * 2

        # Back arm
        back_side = -facing
        bs_x = cx + back_side * 14
        bs_y = cy - 2
        be_x = bs_x + back_side * 7
        be_y = cy + 8
        bh_x = be_x + back_side * 4
        bh_y = be_y + 10
        _NS_thalgryn._draw_water_arm_segment(surface, bs_x, bs_y, be_x, be_y, phase, thickness=7)
        _NS_thalgryn._draw_water_arm_segment(surface, be_x, be_y, bh_x, bh_y, phase, thickness=6)
        _NS_thalgryn._draw_water_hand(surface, bh_x, bh_y, phase)

        # Front casting arm - extends forward
        fs_x = cx + facing * 14
        fs_y = cy - 2

        if progress < 0.3:
            t = progress / 0.3
            arm_angle = -0.5 * t
        elif progress < 0.5:
            t = (progress - 0.3) / 0.2
            arm_angle = -0.5 + 1.3 * t
        else:
            t = (progress - 0.5) / 0.5
            arm_angle = 0.8 - 0.6 * t

        fe_x = fs_x + int(math.cos(arm_angle) * 12) * facing
        fe_y = fs_y + int(math.sin(arm_angle) * 12)
        fh_x = fe_x + int(math.cos(arm_angle) * 10) * facing
        fh_y = fe_y + int(math.sin(arm_angle) * 10)

        _NS_thalgryn._draw_water_arm_segment(surface, fs_x, fs_y, fe_x, fe_y, phase, thickness=7)
        _NS_thalgryn._draw_water_arm_segment(surface, fe_x, fe_y, fh_x, fh_y, phase, thickness=6)

        # Charging orb on hand
        glow_size = 6 + int(math.sin(progress * math.pi) * 6)
        _NS_thalgryn._draw_water_hand_glow(surface, fh_x, fh_y, phase, glow_size)


    def _draw_water_arm_segment(surface, x1, y1, x2, y2, phase, thickness=7):
        """Fluid water arm segment."""
        # Shadow
        _NS_thalgryn._aaline(surface, _NS_thalgryn.PALETTE["shadow_deep"],
                (x1 + 2, y1 + 2), (x2 + 2, y2 + 2), thickness + 1)
        # Layered
        _NS_thalgryn._aaline(surface, _NS_thalgryn.PALETTE["water_darkest"], (x1, y1), (x2, y2), thickness)
        _NS_thalgryn._aaline(surface, _NS_thalgryn.PALETTE["water_dark"], (x1, y1), (x2, y2), thickness - 1)
        _NS_thalgryn._aaline(surface, _NS_thalgryn.PALETTE["water_mid"], (x1, y1), (x2, y2),
                max(1, thickness - 3))
        _NS_thalgryn._aaline(surface, _NS_thalgryn.PALETTE["water_light"], (x1, y1), (x2, y2),
                max(1, thickness - 5))
        _NS_thalgryn._aaline(surface, _NS_thalgryn.PALETTE["water_high"], (x1 - 1, y1 - 1),
                (x2 - 1, y2 - 1), 1)


    def _draw_water_hand(surface, x, y, phase):
        """Water hand with glow."""
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["shadow_deep"], (x + 1, y + 1), 5)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_darkest"], (x, y), 5)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_dark"], (x, y), 4)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_mid"], (x - 1, y - 1), 3)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_light"], (x - 1, y - 2), 2)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_high"], (x - 2, y - 2), 1)

        # Small water drips
        drip_t = ((phase * 2) % 1.0)
        if drip_t < 0.5:
            drip_y = y + 6 + int(drip_t * 10)
            _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_mid"], 220), (x, drip_y), 1)


    def _draw_water_hand_glow(surface, x, y, phase, size=6):
        """Water hand with charging glow."""
        _NS_thalgryn._draw_water_hand(surface, x, y, phase)

        pulse = math.sin(phase * 2) * 0.3 + 0.7
        s = int(size * pulse)

        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_dark"], 130), (x, y), s + 6)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_mid"], 180), (x, y), s + 3)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_light"], 220), (x, y), s)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_high"], 240), (x, y), max(1, s - 2))
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_shine"], 250), (x, y), max(1, s - 4))
        if s > 4:
            _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_white"], (x, y), max(1, s - 6))

        # Sparkles
        for i in range(4):
            angle = phase * 3 + i * math.pi / 2
            sx = x + int(math.cos(angle) * (s + 4))
            sy = y + int(math.sin(angle) * (s + 4))
            _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_shine"], (sx, sy), 1)


    def _draw_water_head(surface, cx, cy, facing, phase):
        """Glossy water head with glowing eyes."""
        # Neck (fluid connection)
        _NS_thalgryn._rect(surface, _NS_thalgryn.PALETTE["water_darkest"], (cx - 4, cy + 8, 8, 6))
        _NS_thalgryn._rect(surface, _NS_thalgryn.PALETTE["water_dark"], (cx - 3, cy + 8, 6, 5))
        _NS_thalgryn._rect(surface, _NS_thalgryn.PALETTE["water_mid"], (cx - 2, cy + 9, 4, 4))

        # Head shape (rounded blob)
        # Shadow
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["shadow_deep"], (cx + 2, cy + 2), 11)

        # Layers of water
        head_pts = [
            (cx - 10, cy - 3),
            (cx - 9, cy - 8),
            (cx - 5, cy - 11),
            (cx + 5, cy - 11),
            (cx + 9, cy - 8),
            (cx + 10, cy - 3),
            (cx + 10, cy + 5),
            (cx + 7, cy + 10),
            (cx - 7, cy + 10),
            (cx - 10, cy + 5),
        ]
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_darkest"], head_pts)
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_dark"], [
            (cx - 9, cy - 2),
            (cx - 8, cy - 7),
            (cx - 4, cy - 10),
            (cx + 4, cy - 10),
            (cx + 8, cy - 7),
            (cx + 9, cy - 2),
            (cx + 9, cy + 4),
            (cx + 6, cy + 9),
            (cx - 6, cy + 9),
            (cx - 9, cy + 4),
        ])
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_mid"], [
            (cx - 7, cy),
            (cx - 6, cy - 5),
            (cx - 3, cy - 8),
            (cx + 3, cy - 8),
            (cx + 6, cy - 5),
            (cx + 7, cy),
            (cx + 6, cy + 5),
            (cx + 4, cy + 7),
            (cx - 4, cy + 7),
            (cx - 6, cy + 5),
        ])
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_light"], [
            (cx - 4, cy - 2),
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 4, cy - 2),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
        ])

        # Head shine (like reflection on water)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_high"], (cx - 4, cy - 5), 2)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_shine"], (cx - 4, cy - 6), 1)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["reflect_hot"], (cx - 4, cy - 6), 1)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_white"], (cx - 5, cy - 7), 1)

        # ===== EYES - glowing bright cyan =====
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Eyes are simple bright dots (like Morphling)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["shadow_deep"], (cx - 3, cy - 2), 2)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["shadow_deep"], (cx + 3, cy - 2), 2)

        # Glowing eyes
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["eye_dark"], (cx - 3, cy - 2),
                  max(1, int(2 * eye_pulse)))
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["eye_mid"], (cx - 3, cy - 2),
                  max(1, int(2 * eye_pulse)))
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["eye_bright"], (cx - 3, cy - 2),
                  max(1, int(1 * eye_pulse)))
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["eye_hot"], (cx - 3, cy - 2), 1)

        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["eye_dark"], (cx + 3, cy - 2),
                  max(1, int(2 * eye_pulse)))
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["eye_mid"], (cx + 3, cy - 2),
                  max(1, int(2 * eye_pulse)))
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["eye_bright"], (cx + 3, cy - 2),
                  max(1, int(1 * eye_pulse)))
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["eye_hot"], (cx + 3, cy - 2), 1)

        # Eye glow aura
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["eye_bright"], int(80 * eye_pulse)),
                  (cx - 3, cy - 2), 4)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["eye_bright"], int(80 * eye_pulse)),
                  (cx + 3, cy - 2), 4)

        # Water crown / top droplet
        top_bob = int(math.sin(phase * 1.5) * 1)
        # Small pointed top on head
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_dark"], [
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx, cy - 14 + top_bob),
        ])
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_mid"], [
            (cx - 2, cy - 9),
            (cx + 2, cy - 9),
            (cx, cy - 13 + top_bob),
        ])
        _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["water_high"], [
            (cx - 1, cy - 10),
            (cx + 1, cy - 10),
            (cx, cy - 13 + top_bob),
        ])
        # Top droplet
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_light"], (cx, cy - 14 + top_bob), 2)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_shine"], (cx, cy - 14 + top_bob), 1)

        # Small droplets floating around head
        for i in range(3):
            drop_angle = phase + i * math.pi * 2 / 3
            dr = 14 + int(math.sin(phase * 2 + i) * 2)
            dx = cx + int(math.cos(drop_angle) * dr)
            dy = cy - 5 + int(math.sin(drop_angle) * dr * 0.6)
            _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_mid"], (dx, dy), 1)
            _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_high"], (dx, dy), 1)


    def _draw_body_reflections(surface, cx, cy, phase):
        """Bright water reflections and shines on body."""
        # Long vertical highlights on left side of body
        for i in range(4):
            yoff = cy - 15 + i * 8
            wave = int(math.sin(phase + i) * 2)
            _NS_thalgryn._aaline(surface, _NS_thalgryn.PALETTE["water_high"],
                    (cx - 8 + wave, yoff), (cx - 6 + wave, yoff + 5), 1)
            _NS_thalgryn._aaline(surface, _NS_thalgryn.PALETTE["water_shine"],
                    (cx - 7 + wave, yoff + 1), (cx - 6 + wave, yoff + 3), 1)

        # Small droplets floating around body
        for i in range(6):
            angle = phase * 0.4 + i * math.pi / 3
            radius = 30 + int(math.sin(phase * 0.7 + i) * 6)
            px = cx + int(math.cos(angle) * radius)
            py = cy + int(math.sin(angle) * radius * 0.5)
            alpha = int(180 + math.sin(phase + i) * 60)
            _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_dark"], alpha), (px, py), 2)
            _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_high"], alpha // 2), (px, py), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_water_base(surface, cx, cy, phase, trail=False,
                        facing=1, intense=False):
        """Water base beneath floating Thalgryn."""
        strength = 1.5 if intense else 1.0

        # Base water pool
        mist = pygame.Surface((140, 45), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(38, 3, -4):
            alpha = int((38 - radius) * 2.2 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_thalgryn.PALETTE["water_darkest"], min(255, alpha)),
                    (70 - radius * 2, 22 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 70, cy - 12))

        # Rising water wisps
        for i, offset in enumerate((-25, -12, 0, 12, 25)):
            t = (phase * 0.5 + i * 0.2) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 25)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_dark"], alpha), (sx, sy), 5)
            _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha), (sx, sy - 2), 3)
            _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_high"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting water orbs
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 26 + int(math.sin(phase + i * 1.3) * 4)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 7)
            _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_mid"], (sx, sy), 3)
            _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_light"], (sx, sy), 2)
            _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_high"], (sx, sy), 1)

        # Splashes at base
        for i in range(4):
            splash_angle = phase * 2 + i * math.pi / 2
            r = 18
            sx = cx + int(math.cos(splash_angle) * r)
            sy = cy + 2 + int(math.sin(splash_angle) * 3)
            _NS_thalgryn._draw_water_splash(surface, sx, sy, 2, phase + i, 180)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 12 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 130 - i * 22)
                _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((110, 22), pygame.SRCALPHA)
        for radius in range(11, 0, -1):
            alpha = max(0, (11 - radius) * 15)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (11 - radius, 11 - radius, 88 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_thalgryn.PALETTE["water_darkest"], 60),
                           (10, 5, 90, 11))
        surface.blit(shadow, (x - 55, y - 11))


    def _draw_water_aura(surface, x, y, phase):
        """Background water aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((200, 180), pygame.SRCALPHA)
        for radius in range(80, 5, -4):
            alpha = int((80 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_thalgryn._aacircle(aura, (*_NS_thalgryn.PALETTE["water_darkest"], min(255, alpha)),
                          (100, 90), radius)
        surface.blit(aura, (x - 100, y - 90))


    def _draw_ground_runes(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((140, 48), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_thalgryn.PALETTE["water_dark"], 140),
                            (5, 10, 130, 28), 3)
        pygame.draw.ellipse(ring, (*_NS_thalgryn.PALETTE["water_mid"], 170),
                            (22, 14, 96, 20), 2)

        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 70 + int(math.cos(angle) * 32)
            y1 = 24 + int(math.sin(angle) * 8)
            x2 = 70 + int(math.cos(angle) * 60)
            y2 = 24 + int(math.sin(angle) * 12)
            pygame.draw.line(ring, (*_NS_thalgryn.PALETTE["water_high"], 160),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_thalgryn.PALETTE["water_shine"], int(80 * pulse)),
                                (15, 8, 110, 32), 1)

        surface.blit(ring, (x - 70, y - 24))


    def _draw_cast_flash(surface, x, y, facing, progress):
        """Flash effect during ranged attack."""
        if progress < 0.2 or progress > 0.65:
            return
        t = (progress - 0.2) / 0.45
        intensity = math.sin(t * math.pi)

        flash_x = x + facing * 24
        flash_y = y - 5

        alpha = int(200 * intensity)
        radius = int(8 + intensity * 15)

        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_dark"], alpha // 2),
                  (flash_x, flash_y), radius + 8)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha),
                  (flash_x, flash_y), radius)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_light"], alpha),
                  (flash_x, flash_y), radius // 2)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_shine"], min(255, alpha)),
                  (flash_x, flash_y), max(1, radius // 4))
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["water_white"],
                  (flash_x, flash_y), max(1, radius // 6))


    # ===================================================================
    # SKILL E: MORPH - Attribute icons
    # ===================================================================
    def _draw_morph_ground(surface, boss, x, y, timer, phase):
        """Ground swirl effect for morph."""
        pulse = math.sin(phase * 3) * 0.2 + 0.8
        radius = 40

        # Spiral ground effect
        for i in range(3):
            r = radius - i * 8
            alpha = int(150 * pulse) - i * 20
            if alpha > 0:
                _NS_thalgryn._ellipse(surface, (*_NS_thalgryn.PALETTE["water_dark"], alpha),
                         (x - r, y + 42 - r // 3,
                          r * 2, r * 2 // 3), 3)
                _NS_thalgryn._ellipse(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha),
                         (x - r + 3, y + 44 - r // 3,
                          r * 2 - 6, r * 2 // 3 - 4), 2)


    def _draw_attribute_icon(surface, cx, cy, attr_index, phase):
        """Draw floating attribute icon (STR/AGI/INT)."""
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        if attr_index == 0:
            # STRENGTH - Red shield/star shape
            color = _NS_thalgryn.PALETTE["str_red"]
            hot = _NS_thalgryn.PALETTE["str_hot"]
            _NS_thalgryn._aacircle(surface, (*color, int(150 * pulse)), (cx, cy), 12)
            _NS_thalgryn._aacircle(surface, (*color, 220), (cx, cy), 9)
            _NS_thalgryn._aacircle(surface, (*hot, 240), (cx, cy), 6)
            # Cross/spike shape
            for angle_deg in (0, 60, 120, 180, 240, 300):
                rad = math.radians(angle_deg)
                ex = cx + int(math.cos(rad) * 8)
                ey = cy + int(math.sin(rad) * 8)
                _NS_thalgryn._aaline(surface, _NS_thalgryn.PALETTE["white"], (cx, cy), (ex, ey), 2)
        elif attr_index == 1:
            # AGILITY - Green triangle/leaf
            color = _NS_thalgryn.PALETTE["agi_green"]
            hot = _NS_thalgryn.PALETTE["agi_hot"]
            _NS_thalgryn._aacircle(surface, (*color, int(150 * pulse)), (cx, cy), 12)
            _NS_thalgryn._aacircle(surface, (*color, 220), (cx, cy), 9)
            _NS_thalgryn._poly(surface, (*hot, 240), [
                (cx, cy - 6),
                (cx + 5, cy + 4),
                (cx - 5, cy + 4),
            ])
            _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["white"], [
                (cx, cy - 4),
                (cx + 3, cy + 2),
                (cx - 3, cy + 2),
            ])
        else:
            # INTELLIGENCE - Blue crystal/diamond
            color = _NS_thalgryn.PALETTE["int_blue"]
            hot = _NS_thalgryn.PALETTE["int_hot"]
            _NS_thalgryn._aacircle(surface, (*color, int(150 * pulse)), (cx, cy), 12)
            _NS_thalgryn._aacircle(surface, (*color, 220), (cx, cy), 9)
            _NS_thalgryn._poly(surface, (*hot, 240), [
                (cx, cy - 6),
                (cx + 5, cy),
                (cx, cy + 6),
                (cx - 5, cy),
            ])
            _NS_thalgryn._poly(surface, _NS_thalgryn.PALETTE["white"], [
                (cx, cy - 3),
                (cx + 2, cy),
                (cx, cy + 3),
                (cx - 2, cy),
            ])


    # ===================================================================
    # SKILL R: REPLICATE
    # ===================================================================
    def _draw_replicate_ground(surface, boss, x, y, timer, phase):
        """Ground rings for each replicate position."""
        progress = max(0.0, min(1.0, 1 - timer / 150))

        positions = [(-70, 15), (70, 15), (-40, -20)]
        for i, (ox, oy) in enumerate(positions):
            rx = x + ox
            ry = y + oy + 42

            pulse = math.sin(phase * 2 + i * 0.5) * 0.2 + 0.8
            radius = int(15 + progress * 8)

            _NS_thalgryn._ellipse(surface, (*_NS_thalgryn.PALETTE["water_dark"], int(180 * pulse)),
                     (rx - radius, ry - radius // 3,
                      radius * 2, radius * 2 // 3), 2)
            _NS_thalgryn._ellipse(surface, (*_NS_thalgryn.PALETTE["water_mid"], int(150 * pulse)),
                     (rx - radius + 3, ry - radius // 3 + 2,
                      radius * 2 - 6, radius * 2 // 3 - 4), 1)


    def _draw_replicates(surface, boss, x, y, timer, phase):
        """Draw water replicate copies."""
        progress = max(0.0, min(1.0, 1 - timer / 150))

        positions = [(-70, 15), (70, 15), (-40, -20)]
        for i, (ox, oy) in enumerate(positions):
            delay = i * 0.1
            if progress < delay:
                continue
            img_progress = min(1.0, (progress - delay) / max(0.1, 1 - delay))

            rx = x + ox + int(math.sin(phase + i) * 3)
            ry = y + oy + int(math.sin(phase * 1.2 + i) * 3)

            alpha = int(200 * min(1.0, img_progress * 2))
            _NS_thalgryn._draw_water_replicate(surface, rx, ry, boss.direction, phase + i, alpha)


    def _draw_water_replicate(surface, cx, cy, facing, phase, alpha=200):
        """Simplified water clone."""
        wobble = math.sin(phase * 2) * 1

        # Body glow
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_darkest"], alpha // 3),
                  (cx, cy), 35)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_dark"], alpha // 2),
                  (cx, cy - 5), 25)

        # Lower body (simplified)
        lower_pts = [
            (cx - 14, cy),
            (cx + 14, cy),
            (cx + 16, cy + 10),
            (cx + 12, cy + 22),
            (cx + 5, cy + 28),
            (cx - 5, cy + 28),
            (cx - 12, cy + 22),
            (cx - 16, cy + 10),
        ]
        _NS_thalgryn._poly(surface, (*_NS_thalgryn.PALETTE["water_dark"], alpha), lower_pts)
        _NS_thalgryn._poly(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha), [
            (cx - 12, cy + 1),
            (cx + 12, cy + 1),
            (cx + 14, cy + 10),
            (cx + 10, cy + 20),
            (cx + 4, cy + 25),
            (cx - 4, cy + 25),
            (cx - 10, cy + 20),
            (cx - 14, cy + 10),
        ])

        # Torso (simplified)
        _NS_thalgryn._poly(surface, (*_NS_thalgryn.PALETTE["water_dark"], alpha), [
            (cx - 11, cy - 10),
            (cx + 11, cy - 10),
            (cx + 13 + int(wobble), cy),
            (cx + 8, cy + 5),
            (cx - 8, cy + 5),
            (cx - 13 - int(wobble), cy),
        ])
        _NS_thalgryn._poly(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha), [
            (cx - 9, cy - 8),
            (cx + 9, cy - 8),
            (cx + 10, cy - 1),
            (cx + 6, cy + 3),
            (cx - 6, cy + 3),
            (cx - 10, cy - 1),
        ])

        # Head
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_dark"], alpha), (cx, cy - 20), 9)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha), (cx - 1, cy - 21), 8)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_light"], alpha), (cx - 2, cy - 22), 5)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_high"], alpha), (cx - 3, cy - 23), 2)

        # Eyes
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["shadow_deep"], (cx - 3, cy - 20), 2)
        _NS_thalgryn._aacircle(surface, _NS_thalgryn.PALETTE["shadow_deep"], (cx + 3, cy - 20), 2)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["eye_bright"], min(255, alpha)),
                  (cx - 3, cy - 20), 1)
        _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["eye_bright"], min(255, alpha)),
                  (cx + 3, cy - 20), 1)

        # Top droplet
        _NS_thalgryn._poly(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha), [
            (cx - 2, cy - 27),
            (cx + 2, cy - 27),
            (cx, cy - 32),
        ])

        # Arms (simple)
        for side in (-1, 1):
            _NS_thalgryn._aaline(surface, (*_NS_thalgryn.PALETTE["water_dark"], alpha),
                    (cx + side * 11, cy - 8), (cx + side * 15, cy + 5), 5)
            _NS_thalgryn._aaline(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha),
                    (cx + side * 11, cy - 8), (cx + side * 15, cy + 5), 3)
            _NS_thalgryn._aaline(surface, (*_NS_thalgryn.PALETTE["water_light"], alpha),
                    (cx + side * 11, cy - 8), (cx + side * 15, cy + 5), 1)

        # Water base
        _NS_thalgryn._ellipse(surface, (*_NS_thalgryn.PALETTE["water_mid"], alpha // 2),
                 (cx - 18, cy + 26, 36, 8))

        # Sparkles around replicate
        for i in range(4):
            angle = phase * 2 + i * math.pi / 2
            r = 25
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * r * 0.6)
            _NS_thalgryn._aacircle(surface, (*_NS_thalgryn.PALETTE["water_shine"], alpha), (sx, sy), 1)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_thalgryn.draw_thalgryn(surface, boss, x, y)


# ====================================================================
# KUNKKA
# ====================================================================
class _NS_kunkka:
    """Namespace kunkka - isi asli tidak diubah."""

    # ---------------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------------
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")

    # ---------------------------------------------------------------------------
    # HD Color Palette - Kunkka inspired navy blue / gold / water
    # ---------------------------------------------------------------------------
    PALETTE = {
        # Coat - navy blue
        "coat_darkest":   (8,   15,  30),
        "coat_dark":      (20,  32,  60),
        "coat_mid":       (38,  58, 100),
        "coat_light":     (65,  95, 145),
        "coat_high":      (105, 140, 190),
        "coat_shine":     (155, 185, 225),

        # Vest inner
        "vest_darkest":   (25,  15,   8),
        "vest_dark":      (55,  32,  15),
        "vest_mid":       (95,  62,  30),
        "vest_light":     (140, 100, 55),

        # Gold trim / buttons
        "gold_darkest":   (75,  50,  10),
        "gold_dark":      (125, 90,  20),
        "gold_mid":       (185, 145, 40),
        "gold_light":     (235, 195, 80),
        "gold_shine":     (255, 235, 150),

        # Skin - tan/weathered
        "skin_dark":      (100, 70,  50),
        "skin_mid":       (155, 115, 85),
        "skin_light":     (205, 170, 135),
        "skin_shine":     (235, 210, 180),

        # Beard/hair - dark brown
        "hair_darkest":   (18,  12,  10),
        "hair_dark":      (38,  25,  18),
        "hair_mid":       (65,  45,  30),
        "hair_light":     (100, 75,  55),

        # Water - cyan/blue
        "water_darkest":  (5,   25,  55),
        "water_dark":     (15,  65, 115),
        "water_mid":      (40, 130, 200),
        "water_light":    (95, 195, 240),
        "water_bright":   (160, 230, 255),
        "water_hot":      (210, 245, 255),
        "water_white":    (240, 252, 255),

        # Cutlass blade - steel
        "blade_darkest":  (40,  50,  65),
        "blade_dark":     (85,  100, 120),
        "blade_mid":      (140, 155, 175),
        "blade_light":    (190, 205, 225),
        "blade_shine":    (230, 240, 250),

        # Sash - cyan/blue
        "sash_dark":      (35,  60,  95),
        "sash_mid":       (65, 110, 155),
        "sash_light":     (110, 160, 205),

        # Ghost ship - ethereal blue-white
        "ghost_dark":     (60, 110, 155),
        "ghost_mid":      (130, 180, 220),
        "ghost_light":    (190, 225, 245),
        "ghost_hot":      (230, 245, 255),

        # Misc
        "shadow":         (0,   0,   0),
        "shadow_deep":    (3,   6,   10),
        "white":          (255, 255, 255),
        "red_x":          (200, 50, 40),
        "red_hot":        (255, 100, 80),
    }


    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)


    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kunkka._clamp(color)
        cx, cy = int(center[0]), int(center[1])
        radius = max(0, int(radius))
        if radius == 0:
            return
        if len(color) == 4 and color[3] < 255:
            temp = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(temp, color, (radius + 2, radius + 2), radius, width)
            surface.blit(temp, (cx - radius - 2, cy - radius - 2))
            return
        if _NS_kunkka.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color[:3], (cx, cy), radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color[:3], (cx, cy), radius, width)


    def _aaline(surface, color, start, end, width=1):
        color = _NS_kunkka._clamp(color)
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
        color = _NS_kunkka._clamp(color)
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
        color = _NS_kunkka._clamp(color)
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
        color = _NS_kunkka._clamp(color)
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
    # Water splash helpers
    # ---------------------------------------------------------------------------
    def _draw_water_splash(surface, x, y, size, phase, alpha=255):
        """Draw a water splash particle."""
        flick = math.sin(phase * 3) * 0.15 + 1.0
        s = int(size * flick)
        if s < 1:
            return
        _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_darkest"], alpha // 3), (x, y), s + 3)
        _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_dark"], alpha // 2), (x, y), s + 1)
        _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_mid"], alpha), (x, y), s)
        _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_light"], alpha), (x, y - 1),
                  max(1, s - 2))
        _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_bright"], min(255, alpha)),
                  (x, y - 2), max(1, s - 4))
        if s > 3:
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_hot"], min(255, alpha)),
                      (x, y - 2), max(1, s - 6))


    def _draw_water_wave(surface, x1, y1, x2, y2, phase, thickness=4,
                        alpha=220):
        """Draw a curved water wave between two points."""
        dx = x2 - x1
        dy = y2 - y1
        dist = math.sqrt(dx * dx + dy * dy) or 1
        steps = max(6, int(dist / 6))

        for i in range(steps):
            t = i / steps
            # Curve using sine wave perpendicular
            wave = math.sin(t * math.pi * 2 + phase * 2) * 4
            perp_x = -dy / dist * wave
            perp_y = dx / dist * wave
            px = int(x1 + dx * t + perp_x)
            py = int(y1 + dy * t + perp_y)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_dark"], alpha), (px, py),
                      thickness + 1)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_mid"], alpha),
                      (px, py), thickness)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_light"], alpha),
                      (px, py), max(1, thickness - 1))
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_bright"], alpha),
                      (px, py), max(1, thickness - 2))


    # ---------------------------------------------------------------------------
    # PROJECTILE / EFFECT SYSTEM
    # ---------------------------------------------------------------------------
    class TideBringerWave:
        """The Q tide wave - crescent slash forward."""
        def __init__(self, sx, sy, direction, max_dist=180):
            self.x = float(sx)
            self.y = float(sy)
            self.start_x = float(sx)
            self.start_y = float(sy)
            self.direction = direction
            self.max_dist = max_dist
            self.speed = 9.0
            self.alive = True
            self.age = 0
            self.max_age = 25

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.x += self.speed * self.direction
            if self.age >= self.max_age:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive and self.age < 2:
                return

            t = self.age / self.max_age
            alpha = int(255 * (1 - t * 0.5))
            px, py = int(self.x), int(self.y)

            # Crescent wave shape - large curved arc
            # Draw multiple curves for wave effect
            for wave_off in range(-2, 3):
                for i in range(-14, 15):
                    # Vertical position with curve
                    curve = math.cos(i * 0.2) * 6
                    vy = py + i * 2
                    vx = px + int(curve) * self.direction + wave_off * 2

                    w_alpha = int(alpha * (1 - abs(i) / 15))
                    if w_alpha <= 0:
                        continue

                    _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_dark"], w_alpha),
                              (vx, vy), 4)
                    _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_mid"], w_alpha),
                              (vx, vy), 3)
                    _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_light"], w_alpha),
                              (vx, vy), 2)
                    _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_bright"], w_alpha),
                              (vx, vy), 1)

            # Bright core arc
            for i in range(-12, 13):
                curve = math.cos(i * 0.2) * 6
                vy = py + i * 2
                vx = px + int(curve) * self.direction

                core_alpha = int(alpha * (1 - abs(i) / 13))
                _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_hot"], core_alpha),
                          (vx, vy), 2)
                _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_white"], core_alpha),
                          (vx, vy), 1)

            # Splashes trailing
            for i in range(6):
                spark_angle = phase * 2 + i * math.pi / 3
                r = 15 + int(math.sin(phase + i) * 5)
                sx = px + int(math.cos(spark_angle) * r) * self.direction
                sy = py + int(math.sin(spark_angle) * r)
                _NS_kunkka._draw_water_splash(surface, sx, sy, 3, phase, alpha)


    class GhostShip:
        """The R ghost ship - sails forward."""
        def __init__(self, sx, sy, direction, max_dist=350):
            self.x = float(sx)
            self.y = float(sy)
            self.start_x = float(sx)
            self.direction = direction
            self.max_dist = max_dist
            self.speed = 4.0
            self.alive = True
            self.age = 0
            self.sway_phase = 0

        def update(self):
            if not self.alive:
                return
            self.age += 1
            self.sway_phase += 0.15
            self.x += self.speed * self.direction
            if abs(self.x - self.start_x) >= self.max_dist:
                self.alive = False

        def draw(self, surface, phase):
            if not self.alive:
                return
            _NS_kunkka._draw_ghost_ship_shape(surface, int(self.x), int(self.y),
                                  self.direction, phase + self.sway_phase)


    def _draw_ghost_ship_shape(surface, cx, cy, facing, phase):
        """Draw large ethereal ghost ship."""
        sway = int(math.sin(phase * 0.8) * 3)
        ship_h = 60
        ship_w = 80

        # ---- Water disturbance at base ----
        for i in range(10):
            angle = i * math.pi / 5
            wx = cx + int(math.cos(angle) * ship_w * 0.6)
            wy = cy + 20 + int(math.sin(angle) * 8)
            alpha = 150
            _NS_kunkka._draw_water_splash(surface, wx, wy, 4, phase + i, alpha)

        # Base water spray under ship
        _NS_kunkka._ellipse(surface, (*_NS_kunkka.PALETTE["water_dark"], 180),
                 (cx - ship_w // 2 - 10, cy + 15, ship_w + 20, 15))
        _NS_kunkka._ellipse(surface, (*_NS_kunkka.PALETTE["water_mid"], 150),
                 (cx - ship_w // 2, cy + 18, ship_w, 10))

        # ---- Ship hull ----
        hull_alpha = 220
        hull_pts = [
            (cx - ship_w // 2, cy - 5),
            (cx - ship_w // 2 + 5, cy + 15),
            (cx + facing * (ship_w // 2 - 5), cy + 20),
            (cx + facing * (ship_w // 2 + 8), cy + 8),
            (cx + facing * (ship_w // 2 + 5), cy - 3),
            (cx + ship_w // 2 - 5, cy - 5),
        ]
        _NS_kunkka._poly(surface, (*_NS_kunkka.PALETTE["ghost_dark"], hull_alpha), hull_pts)

        # Inner hull
        hull_inner = [
            (cx - ship_w // 2 + 4, cy - 3),
            (cx - ship_w // 2 + 8, cy + 12),
            (cx + facing * (ship_w // 2 - 8), cy + 17),
            (cx + facing * (ship_w // 2 + 5), cy + 6),
            (cx + facing * (ship_w // 2 + 2), cy - 2),
            (cx + ship_w // 2 - 8, cy - 3),
        ]
        _NS_kunkka._poly(surface, (*_NS_kunkka.PALETTE["ghost_mid"], hull_alpha), hull_inner)

        # Hull planks (horizontal lines)
        for i in range(3):
            y_off = cy - 2 + i * 5
            _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["ghost_dark"], 200),
                    (cx - ship_w // 2 + 6, y_off),
                    (cx + facing * (ship_w // 2 - 6), y_off), 1)

        # Hull outline
        for i in range(len(hull_pts)):
            p1 = hull_pts[i]
            p2 = hull_pts[(i + 1) % len(hull_pts)]
            _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["ghost_light"], 220), p1, p2, 1)

        # ---- Masts ----
        mast_positions = [(-15, 45), (10, 55), (30, 40)]  # x_offset, height
        for mast_x, mast_h in mast_positions:
            mx = cx + mast_x * facing
            my_bottom = cy - 3
            my_top = my_bottom - mast_h
            # Mast pole
            _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["ghost_dark"], 220),
                    (mx, my_top), (mx, my_bottom), 2)
            _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["ghost_mid"], 240),
                    (mx, my_top), (mx, my_bottom), 1)

            # Sail
            sail_w = 12 + int(sway)
            sail_pts = [
                (mx, my_top + 5),
                (mx + sail_w, my_top + 8),
                (mx + sail_w - 2, my_bottom - 10),
                (mx, my_bottom - 15),
            ]
            _NS_kunkka._poly(surface, (*_NS_kunkka.PALETTE["ghost_mid"], 180), sail_pts)
            _NS_kunkka._poly(surface, (*_NS_kunkka.PALETTE["ghost_light"], 200), [
                (mx, my_top + 6),
                (mx + sail_w - 2, my_top + 9),
                (mx + sail_w - 3, my_bottom - 11),
                (mx, my_bottom - 16),
            ])
            # Sail highlight
            _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["ghost_hot"], 220),
                    (mx + 2, my_top + 8),
                    (mx + 2, my_bottom - 12), 1)

        # ---- Bowsprit (front pole) ----
        bs_x1 = cx + facing * (ship_w // 2 + 5)
        bs_y1 = cy
        bs_x2 = cx + facing * (ship_w // 2 + 18)
        bs_y2 = cy - 8
        _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["ghost_dark"], 220), (bs_x1, bs_y1), (bs_x2, bs_y2), 2)
        _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["ghost_mid"], 240), (bs_x1, bs_y1), (bs_x2, bs_y2), 1)

        # ---- Ghost glow around ship ----
        for i in range(3):
            r = 30 + i * 10
            alpha = 60 - i * 15
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_mid"], alpha), (cx, cy), r)

        # ---- Water sprays around ship ----
        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            r = ship_w // 2 + 15
            wx = cx + int(math.cos(angle) * r)
            wy = cy + int(math.sin(angle) * r * 0.4) + 5
            _NS_kunkka._draw_water_splash(surface, wx, wy, 4, phase + i, 200)


    # ---------------------------------------------------------------------------
    # State management
    # ---------------------------------------------------------------------------
    def _detect_moving(boss):
        if not hasattr(boss, "_kk_last_x"):
            boss._kk_last_x = boss.x
            boss._kk_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kk_last_x)
        dy = abs(boss.y - boss._kk_last_y)
        boss._kk_last_x = boss.x
        boss._kk_last_y = boss.y
        return dx + dy > 0.3


    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 50)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kk_prev_timer", 0))
        active = bool(getattr(boss, "_kk_attack_active", False))

        if timer >= cooldown - 1 and previous <= 1:
            boss._kk_attack_active = True
            boss._kk_attack_frame = 0
            active = True
        elif active:
            boss._kk_attack_frame = int(getattr(boss, "_kk_attack_frame", 0)) + 1
            if boss._kk_attack_frame > cooldown:
                boss._kk_attack_active = False
                boss._kk_attack_frame = 0
                active = False
        elif timer <= 0:
            boss._kk_attack_active = False
            boss._kk_attack_frame = 0
            active = False

        boss._kk_prev_timer = timer
        boss._kk_attack_progress = (
            min(1.0, getattr(boss, "_kk_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )


    def _manage_effects(boss, surface, phase):
        if not hasattr(boss, "_kk_effects"):
            boss._kk_effects = []
        for e in boss._kk_effects:
            e.update()
            e.draw(surface, phase)
        boss._kk_effects = [e for e in boss._kk_effects if e.alive or e.age < 5]


    def _spawn_tide_wave(boss, x, y):
        if not hasattr(boss, "_kk_effects"):
            boss._kk_effects = []
        sx = x + 30 * boss.direction
        sy = y - 5
        boss._kk_effects.append(_NS_kunkka.TideBringerWave(sx, sy, boss.direction))


    def _spawn_ghost_ship(boss, x, y):
        if not hasattr(boss, "_kk_effects"):
            boss._kk_effects = []
        sx = x - 100 * boss.direction  # Ships come from behind
        sy = y + 5
        boss._kk_effects.append(_NS_kunkka.GhostShip(sx, sy, boss.direction))


    # ===================================================================
    # MAIN DRAW ENTRY POINT
    # ===================================================================
    def draw_kunkka(surface, boss, x, y):
        """Entry point."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kunkka._detect_moving(boss)
        _NS_kunkka._update_attack_anim(boss)

        attacking = (
            getattr(boss, "_kk_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 50) - 15
        )

        # ---------- Background layers ----------
        _NS_kunkka._draw_water_aura(surface, x, y, pulse)
        _NS_kunkka._draw_ground_runes(surface, x, y + 38, pulse, active_skill)

        # ---------- Skill ground effects ----------
        if active_skill == "w":
            _NS_kunkka._draw_x_marks_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kunkka._draw_torrent_ground(surface, boss, x, y, skill_timer, pulse)

        # ---------- Character body ----------
        if active_skill == "q":
            _NS_kunkka._draw_kunkka_tide_cast(surface, boss, x, y, skill_timer, pulse)
        elif attacking:
            _NS_kunkka._draw_kunkka_melee_attack(surface, boss, x, y)
        elif moving:
            _NS_kunkka._draw_kunkka_walk(surface, boss, x, y)
        else:
            _NS_kunkka._draw_kunkka_idle(surface, boss, x, y)

        # ---------- Effects (waves, ships etc) ----------
        _NS_kunkka._manage_effects(boss, surface, pulse)

        # ---------- Skill foreground effects ----------
        if active_skill == "w":
            _NS_kunkka._draw_x_marks_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kunkka._draw_ghost_ship_cast(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kunkka._draw_torrent_foreground(surface, boss, x, y, skill_timer, pulse)


    # ===================================================================
    # POSE MODES
    # ===================================================================
    def _draw_kunkka_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.8) * 2)
        _NS_kunkka._draw_shadow(surface, x, y + 48)
        _NS_kunkka._draw_floating_water(surface, x, y + 35, boss.pulse)
        _NS_kunkka._draw_kunkka_body(surface, x, y + bob, boss.direction, boss.pulse, "idle")


    def _draw_kunkka_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(abs(math.sin(phase * 1.3)) * 3)
        sway = int(math.sin(phase) * 2)
        _NS_kunkka._draw_shadow(surface, x + sway, y + 48)
        _NS_kunkka._draw_floating_water(surface, x + sway, y + 35, phase, trail=True,
                             facing=boss.direction)
        _NS_kunkka._draw_kunkka_body(surface, x + sway, y - bob, boss.direction, phase, "walk")


    def _draw_kunkka_melee_attack(surface, boss, x, y):
        """Sword swing animation."""
        progress = getattr(boss, "_kk_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        lunge = int(math.sin(progress * math.pi) * 5) * boss.direction
        _NS_kunkka._draw_shadow(surface, x + lunge, y + 48)
        _NS_kunkka._draw_floating_water(surface, x + lunge, y + 35, boss.pulse, intense=True)
        _NS_kunkka._draw_kunkka_body(surface, x + lunge, y, boss.direction, boss.pulse,
                         "melee", progress)
        _NS_kunkka._draw_sword_swing_trail(surface, x + lunge, y, boss.direction, progress)


    def _draw_kunkka_tide_cast(surface, boss, x, y, timer, phase):
        """Q casting - swings cutlass releasing wave."""
        # Determine cast progress
        cast_duration = 40
        elapsed = cast_duration - timer
        progress = max(0.0, min(1.0, elapsed / cast_duration))

        # Spawn wave near mid-swing
        if 0.35 < progress < 0.42 and not getattr(boss, "_kk_wave_spawned", False):
            _NS_kunkka._spawn_tide_wave(boss, x, y)
            boss._kk_wave_spawned = True
        if progress < 0.2 or progress > 0.9:
            boss._kk_wave_spawned = False

        lunge = int(math.sin(progress * math.pi) * 6) * boss.direction
        _NS_kunkka._draw_shadow(surface, x + lunge, y + 48)
        _NS_kunkka._draw_floating_water(surface, x + lunge, y + 35, phase, intense=True)
        _NS_kunkka._draw_kunkka_body(surface, x + lunge, y, boss.direction, phase,
                         "melee", progress)
        _NS_kunkka._draw_sword_water_trail(surface, x + lunge, y, boss.direction, progress, phase)


    # ===================================================================
    # BODY RENDERING – HD detailed Admiral
    # ===================================================================
    def _draw_kunkka_body(surface, cx, cy, facing, phase, action,
                         attack_progress=0):
        """Main body composition."""
        # Coat tails (behind body)
        _NS_kunkka._draw_coat_tails(surface, cx, cy + 5, facing, phase, action)

        # Legs (dark pants)
        _NS_kunkka._draw_legs(surface, cx, cy + 15, phase)

        # Torso coat
        _NS_kunkka._draw_torso_coat(surface, cx, cy - 8, phase)

        # Shoulders / epaulets
        _NS_kunkka._draw_epaulets(surface, cx, cy - 16, phase)

        # Arms
        if action == "melee":
            _NS_kunkka._draw_melee_arms(surface, cx, cy - 8, facing, phase, attack_progress)
        else:
            _NS_kunkka._draw_idle_arms(surface, cx, cy - 8, facing, phase)

        # Head with hair + beard + hat/hair
        _NS_kunkka._draw_head(surface, cx, cy - 28, facing, phase)

        # Sword (in hand) - drawn based on action
        # Water particles around body
        _NS_kunkka._draw_body_water_particles(surface, cx, cy, phase)


    def _draw_coat_tails(surface, cx, cy, facing, phase, action):
        """Long navy coat tails."""
        wave = math.sin(phase * 0.8) * 3
        wave2 = math.sin(phase * 1.2 + 0.5) * 2

        # Coat tail shape (long behind)
        tail_pts = [
            (cx - 16, cy - 10),
            (cx - 22, cy + 5),
            (cx - 24 - int(wave), cy + 25),
            (cx - 20 - int(wave2), cy + 40),
            (cx - 8, cy + 42),
            (cx + 8, cy + 42),
            (cx + 20 + int(wave2), cy + 40),
            (cx + 24 + int(wave), cy + 25),
            (cx + 22, cy + 5),
            (cx + 16, cy - 10),
        ]
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["shadow_deep"], [(p[0] + 2, p[1] + 2) for p in tail_pts])
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["coat_darkest"], tail_pts)

        tail_mid = [
            (cx - 14, cy - 8),
            (cx - 20, cy + 5),
            (cx - 22 - int(wave), cy + 22),
            (cx - 18 - int(wave2), cy + 36),
            (cx - 6, cy + 38),
            (cx + 6, cy + 38),
            (cx + 18 + int(wave2), cy + 36),
            (cx + 22 + int(wave), cy + 22),
            (cx + 20, cy + 5),
            (cx + 14, cy - 8),
        ]
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["coat_dark"], tail_mid)

        # Inner tail
        tail_inner = [
            (cx - 11, cy - 5),
            (cx - 15, cy + 5),
            (cx - 17, cy + 20),
            (cx - 6, cy + 32),
            (cx + 6, cy + 32),
            (cx + 17, cy + 20),
            (cx + 15, cy + 5),
            (cx + 11, cy - 5),
        ]
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["coat_mid"], tail_inner)

        # Coat highlights
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["coat_light"],
                (cx - 9, cy - 3), (cx - 12, cy + 25), 1)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["coat_light"],
                (cx + 9, cy - 3), (cx + 12, cy + 25), 1)

        # Gold trim on coat edges
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["gold_dark"],
                (cx - 22 - int(wave), cy + 22),
                (cx - 20 - int(wave2), cy + 36), 2)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["gold_mid"],
                (cx - 22 - int(wave), cy + 22),
                (cx - 20 - int(wave2), cy + 36), 1)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["gold_dark"],
                (cx + 22 + int(wave), cy + 22),
                (cx + 20 + int(wave2), cy + 36), 2)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["gold_mid"],
                (cx + 22 + int(wave), cy + 22),
                (cx + 20 + int(wave2), cy + 36), 1)

        # Gold buttons down the middle
        for i in range(3):
            by = cy + 5 + i * 8
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_dark"], (cx, by), 2)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_mid"], (cx, by), 1)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_shine"], (cx - 1, by - 1), 1)


    def _draw_legs(surface, cx, cy, phase):
        """Dark pants with boots."""
        sway = int(math.sin(phase * 0.5) * 1)

        for side in (-1, 1):
            leg_x = cx + side * 5
            leg_top_y = cy
            leg_bot_y = cy + 22

            # Leg/pants
            _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["shadow_deep"],
                    (leg_x + 1, leg_top_y + 1),
                    (leg_x + sway + 1, leg_bot_y + 1), 8)
            _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["coat_darkest"],
                    (leg_x, leg_top_y),
                    (leg_x + sway, leg_bot_y), 7)
            _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["coat_dark"],
                    (leg_x, leg_top_y),
                    (leg_x + sway, leg_bot_y), 5)
            _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["coat_mid"],
                    (leg_x - 1, leg_top_y),
                    (leg_x + sway - 1, leg_bot_y), 2)

            # Boot
            boot_x = leg_x + sway
            _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["shadow_deep"],
                  (boot_x - 5, leg_bot_y - 2, 10, 8))
            _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["hair_darkest"],
                  (boot_x - 4, leg_bot_y - 2, 9, 7))
            _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["hair_dark"],
                  (boot_x - 4, leg_bot_y - 2, 9, 5))
            _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["hair_mid"],
                  (boot_x - 3, leg_bot_y - 1, 6, 2))

            # Gold boot buckle
            _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["gold_dark"], (boot_x - 2, leg_bot_y + 1, 4, 2))
            _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["gold_mid"], (boot_x - 1, leg_bot_y + 1, 2, 1))


    def _draw_torso_coat(surface, cx, cy, phase):
        """Main coat torso."""
        # Shadow
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["shadow_deep"], [
            (cx - 15 + 2, cy - 10 + 2), (cx + 15 + 2, cy - 10 + 2),
            (cx + 13 + 2, cy + 15 + 2), (cx + 5 + 2, cy + 20 + 2),
            (cx - 5 + 2, cy + 20 + 2), (cx - 13 + 2, cy + 15 + 2),
        ])

        coat = [
            (cx - 15, cy - 10), (cx + 15, cy - 10),
            (cx + 13, cy + 15), (cx + 5, cy + 20),
            (cx - 5, cy + 20), (cx - 13, cy + 15),
        ]
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["coat_darkest"], coat)
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["coat_dark"], [
            (cx - 13, cy - 8), (cx + 13, cy - 8),
            (cx + 11, cy + 13), (cx + 4, cy + 17),
            (cx - 4, cy + 17), (cx - 11, cy + 13),
        ])
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["coat_mid"], [
            (cx - 10, cy - 5), (cx + 10, cy - 5),
            (cx + 8, cy + 10), (cx + 3, cy + 14),
            (cx - 3, cy + 14), (cx - 8, cy + 10),
        ])

        # Highlight
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["coat_light"],
                (cx - 8, cy - 4), (cx - 6, cy + 12), 1)

        # Gold buttons (two rows)
        for i in range(4):
            by = cy - 6 + i * 6
            # Left row
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_dark"], (cx - 5, by), 2)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_mid"], (cx - 5, by), 1)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_shine"], (cx - 6, by - 1), 1)
            # Right row
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_dark"], (cx + 5, by), 2)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_mid"], (cx + 5, by), 1)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_shine"], (cx + 4, by - 1), 1)

        # Cyan sash (from shoulder to waist)
        sash_pts = [
            (cx - 14, cy - 8),
            (cx - 8, cy - 6),
            (cx + 8, cy + 12),
            (cx + 4, cy + 16),
            (cx - 12, cy - 2),
        ]
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["sash_dark"], sash_pts)
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["sash_mid"], [
            (cx - 13, cy - 7),
            (cx - 8, cy - 5),
            (cx + 7, cy + 11),
            (cx + 4, cy + 15),
            (cx - 11, cy - 1),
        ])
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["sash_light"],
                (cx - 12, cy - 5), (cx + 5, cy + 13), 1)

        # Belt at waist (leather with gold buckle)
        _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["vest_darkest"], (cx - 15, cy + 15, 30, 5))
        _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["vest_dark"], (cx - 14, cy + 15, 28, 3))
        _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["vest_mid"], (cx - 13, cy + 16, 26, 1))

        # Gold belt buckle
        _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["gold_dark"], (cx - 4, cy + 15, 8, 5))
        _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["gold_mid"], (cx - 3, cy + 15, 6, 4))
        _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["gold_light"], (cx - 2, cy + 16, 4, 2))
        # Anchor emblem on buckle
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["vest_darkest"],
                (cx, cy + 15), (cx, cy + 19), 1)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["vest_darkest"],
                (cx - 2, cy + 17), (cx + 2, cy + 17), 1)


    def _draw_epaulets(surface, cx, cy, phase):
        """Gold fringed epaulets on shoulders."""
        for side in (-1, 1):
            sx = cx + side * 15
            # Shoulder base (coat)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["shadow_deep"], (sx + 2, cy + 2), 10)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["coat_darkest"], (sx, cy), 9)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["coat_dark"], (sx - side, cy - 1), 7)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["coat_mid"], (sx - side * 2, cy - 2), 5)

            # Gold epaulet on top
            _NS_kunkka._ellipse(surface, _NS_kunkka.PALETTE["gold_darkest"],
                     (sx - 7, cy - 5, 14, 6))
            _NS_kunkka._ellipse(surface, _NS_kunkka.PALETTE["gold_dark"],
                     (sx - 6, cy - 5, 12, 5))
            _NS_kunkka._ellipse(surface, _NS_kunkka.PALETTE["gold_mid"],
                     (sx - 5, cy - 4, 10, 3))
            _NS_kunkka._ellipse(surface, _NS_kunkka.PALETTE["gold_light"],
                     (sx - 4, cy - 4, 8, 2))
            _NS_kunkka._ellipse(surface, _NS_kunkka.PALETTE["gold_shine"],
                     (sx - 3, cy - 4, 4, 1))

            # Gold fringe hanging down
            for i in range(-3, 4):
                fx = sx + i * 2
                fringe_len = 4 + abs(i)
                _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["gold_dark"],
                        (fx, cy - 1), (fx, cy + fringe_len), 1)
                _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["gold_mid"],
                        (fx, cy - 1), (fx, cy + fringe_len - 1), 1)
                # Fringe tip
                _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_light"],
                          (fx, cy + fringe_len), 1)


    def _draw_idle_arms(surface, cx, cy, facing, phase):
        """Idle - one arm holding cutlass, one at side."""
        sway = math.sin(phase * 0.7) * 2

        # Sword arm (facing side)
        ss_x = cx + facing * 13
        ss_y = cy + 2
        se_x = ss_x + facing * 7
        se_y = cy + 12 + int(sway)
        sh_x = se_x + facing * 4
        sh_y = se_y + 10
        _NS_kunkka._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_kunkka._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Draw cutlass pointing down/forward
        _NS_kunkka._draw_cutlass(surface, sh_x, sh_y, facing, phase, angle=-0.2)

        # Free arm (opposite side)
        fs_x = cx + (-facing) * 13
        fs_y = cy + 2
        fe_x = fs_x + (-facing) * 6
        fe_y = cy + 12
        fh_x = fe_x + (-facing) * 3
        fh_y = fe_y + 8
        _NS_kunkka._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_kunkka._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_kunkka._draw_gloved_hand(surface, fh_x, fh_y)


    def _draw_melee_arms(surface, cx, cy, facing, phase, progress):
        """Sword swing animation."""
        # Free arm stable
        fs_x = cx + (-facing) * 13
        fs_y = cy + 2
        fe_x = fs_x + (-facing) * 6
        fe_y = cy + 12
        fh_x = fe_x + (-facing) * 3
        fh_y = fe_y + 8
        _NS_kunkka._draw_arm_segment(surface, fs_x, fs_y, fe_x, fe_y)
        _NS_kunkka._draw_arm_segment(surface, fe_x, fe_y, fh_x, fh_y)
        _NS_kunkka._draw_gloved_hand(surface, fh_x, fh_y)

        # Sword arm - swing motion
        ss_x = cx + facing * 13
        ss_y = cy + 2

        if progress < 0.3:
            # Wind up (raise back)
            t = progress / 0.3
            arm_angle = -1.2 + (-0.8) * t  # -1.2 to -2.0
        elif progress < 0.6:
            # Swing forward
            t = (progress - 0.3) / 0.3
            arm_angle = -2.0 + 3.0 * t
        else:
            # Recovery
            t = (progress - 0.6) / 0.4
            arm_angle = 1.0 - 1.2 * t

        se_x = ss_x + int(math.cos(arm_angle) * 12) * facing
        se_y = ss_y + int(math.sin(arm_angle) * 12)
        sh_x = se_x + int(math.cos(arm_angle) * 10) * facing
        sh_y = se_y + int(math.sin(arm_angle) * 10)

        _NS_kunkka._draw_arm_segment(surface, ss_x, ss_y, se_x, se_y)
        _NS_kunkka._draw_arm_segment(surface, se_x, se_y, sh_x, sh_y)

        # Cutlass with rotation
        sword_angle = arm_angle + (0.3 if facing > 0 else -0.3)
        _NS_kunkka._draw_cutlass(surface, sh_x, sh_y, facing, phase, angle=sword_angle,
                     intense=(0.3 < progress < 0.7))


    def _draw_arm_segment(surface, x1, y1, x2, y2):
        """Coat sleeve arm segment with gold cuff."""
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["shadow_deep"],
                (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), 7)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["coat_darkest"], (x1, y1), (x2, y2), 6)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["coat_dark"], (x1, y1), (x2, y2), 4)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["coat_mid"], (x1, y1), (x2, y2), 2)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["coat_light"], (x1 - 1, y1), (x2 - 1, y2), 1)

        # Gold cuff at end
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_dark"], (x2, y2), 4)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_mid"], (x2, y2), 3)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_light"], (x2 - 1, y2 - 1), 1)


    def _draw_gloved_hand(surface, x, y):
        """Leather glove."""
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["shadow_deep"], (x + 1, y + 1), 4)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["hair_darkest"], (x, y), 3)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["hair_dark"], (x, y - 1), 2)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["hair_mid"], (x - 1, y - 1), 1)


    def _draw_cutlass(surface, hx, hy, facing, phase, angle=0, intense=False):
        """Kunkka's cutlass - curved sword blade."""
        length = 32
        tip_x = hx + int(math.cos(angle) * length) * facing
        tip_y = hy + int(math.sin(angle) * length)

        # Perpendicular for blade width
        perp_angle = angle + math.pi / 2
        px = math.cos(perp_angle) * facing
        py = math.sin(perp_angle)

        # Curved blade shape (cutlass curve)
        curve_offset = 6
        mid_x = hx + int(math.cos(angle) * length * 0.6) * facing
        mid_y = hy + int(math.sin(angle) * length * 0.6)
        curve_mid_x = mid_x + int(math.cos(angle - 0.5) * curve_offset) * facing
        curve_mid_y = mid_y + int(math.sin(angle - 0.5) * curve_offset)

        # Blade shadow
        blade_pts = [
            (hx + int(px * 3), hy + int(py * 3)),
            (hx - int(px * 2), hy - int(py * 2)),
            (curve_mid_x - int(px * 1), curve_mid_y - int(py * 1)),
            (tip_x, tip_y),
            (curve_mid_x + int(px * 3), curve_mid_y + int(py * 3)),
        ]
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["shadow_deep"],
              [(p[0] + 2, p[1] + 2) for p in blade_pts])

        # Blade base (dark steel)
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["blade_darkest"], blade_pts)

        # Blade inner
        blade_inner = [
            (hx + int(px * 2), hy + int(py * 2)),
            (hx - int(px * 1), hy - int(py * 1)),
            (curve_mid_x, curve_mid_y),
            (tip_x, tip_y),
            (curve_mid_x + int(px * 2), curve_mid_y + int(py * 2)),
        ]
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["blade_dark"], blade_inner)

        # Mid blade
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["blade_mid"], [
            (hx + int(px * 1), hy + int(py * 1)),
            (hx, hy),
            (curve_mid_x + int(px * 0.5), curve_mid_y + int(py * 0.5)),
            (tip_x, tip_y),
        ])

        # Blade shine (edge)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["blade_light"],
                (hx + int(px * 1), hy + int(py * 1)),
                (tip_x, tip_y), 1)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["blade_shine"],
                (hx + int(px * 0.5), hy + int(py * 0.5)),
                (tip_x, tip_y), 1)

        # Guard (crossguard - gold)
        guard_perp_x = int(px * 7)
        guard_perp_y = int(py * 7)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["gold_darkest"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 4)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["gold_dark"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 3)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["gold_mid"],
                (hx + guard_perp_x, hy + guard_perp_y),
                (hx - guard_perp_x, hy - guard_perp_y), 2)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["gold_light"],
                (hx + int(guard_perp_x * 0.7), hy + int(guard_perp_y * 0.7)),
                (hx - int(guard_perp_x * 0.7), hy - int(guard_perp_y * 0.7)), 1)

        # Curved knuckle guard (from top of guard curving down to pommel)
        knuckle_x1 = hx + guard_perp_x
        knuckle_y1 = hy + guard_perp_y
        knuckle_x2 = hx - int(math.cos(angle) * 8) * facing
        knuckle_y2 = hy - int(math.sin(angle) * 8)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["gold_dark"], (knuckle_x1, knuckle_y1),
                (knuckle_x2, knuckle_y2), 2)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["gold_mid"], (knuckle_x1, knuckle_y1),
                (knuckle_x2, knuckle_y2), 1)

        # Pommel
        pommel_x = hx - int(math.cos(angle) * 6) * facing
        pommel_y = hy - int(math.sin(angle) * 6)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_darkest"], (pommel_x, pommel_y), 3)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_dark"], (pommel_x, pommel_y), 2)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["gold_shine"], (pommel_x - 1, pommel_y - 1), 1)

        # Water aura on blade when intense
        if intense:
            for i in range(5):
                t = i / 5
                bx = int(hx + (tip_x - hx) * t)
                by = int(hy + (tip_y - hy) * t)
                _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_mid"], 180), (bx, by), 3)
                _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_light"], 200), (bx, by), 2)
                _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_hot"], 220), (bx, by), 1)


    def _draw_head(surface, cx, cy, facing, phase):
        """Kunkka's head - dark hair, beard, weathered face."""
        # Neck
        _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["skin_dark"], (cx - 3, cy + 8, 6, 5))
        _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["skin_mid"], (cx - 2, cy + 8, 4, 4))

        # Head shape
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["shadow_deep"], (cx + 2, cy + 2), 11)

        # Skin base
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["skin_dark"], (cx, cy), 10)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["skin_mid"], (cx - 1, cy - 1), 8)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["skin_light"], (cx - 2, cy - 3), 5)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["skin_shine"], (cx - 3, cy - 4), 2)

        # Hair - dark long flowing hair
        hair_wave = math.sin(phase * 0.5) * 2
        hair_pts = [
            (cx - 10, cy - 4),
            (cx - 11, cy - 8),
            (cx - 8, cy - 12),
            (cx - 3, cy - 14),
            (cx + 3, cy - 14),
            (cx + 8, cy - 12),
            (cx + 11, cy - 8),
            (cx + 10, cy - 4),
            (cx + 13 + int(hair_wave), cy + 4),
            (cx + 12, cy + 8),
            (cx - 12, cy + 8),
            (cx - 13 - int(hair_wave), cy + 4),
        ]
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["hair_darkest"], hair_pts)
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["hair_dark"], [
            (cx - 9, cy - 3),
            (cx - 10, cy - 7),
            (cx - 7, cy - 11),
            (cx - 3, cy - 13),
            (cx + 3, cy - 13),
            (cx + 7, cy - 11),
            (cx + 10, cy - 7),
            (cx + 9, cy - 3),
            (cx + 11, cy + 3),
            (cx + 10, cy + 7),
            (cx - 10, cy + 7),
            (cx - 11, cy + 3),
        ])

        # Hair highlights (mid tones)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["hair_mid"],
                (cx - 6, cy - 10), (cx - 4, cy - 12), 1)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["hair_mid"],
                (cx + 6, cy - 10), (cx + 4, cy - 12), 1)

        # Face area (open - hair frames it)
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["skin_dark"], [
            (cx - 6, cy - 5),
            (cx - 5, cy - 8),
            (cx + 5, cy - 8),
            (cx + 6, cy - 5),
            (cx + 5, cy + 2),
            (cx - 5, cy + 2),
        ])
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["skin_mid"], [
            (cx - 5, cy - 4),
            (cx - 4, cy - 7),
            (cx + 4, cy - 7),
            (cx + 5, cy - 4),
            (cx + 4, cy + 1),
            (cx - 4, cy + 1),
        ])
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["skin_light"], [
            (cx - 3, cy - 3),
            (cx - 2, cy - 5),
            (cx + 2, cy - 5),
            (cx + 3, cy - 3),
            (cx + 2, cy),
            (cx - 2, cy),
        ])

        # Eyes - dark and intense
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["shadow_deep"], (cx - 2, cy - 3), 2)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["shadow_deep"], (cx + 2, cy - 3), 2)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["hair_darkest"], (cx - 2, cy - 3), 1)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["hair_darkest"], (cx + 2, cy - 3), 1)
        # Slight blue tint (sea eyes)
        _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["water_mid"], (cx - 2, cy - 3, 1, 1))
        _NS_kunkka._rect(surface, _NS_kunkka.PALETTE["water_mid"], (cx + 2, cy - 3, 1, 1))

        # Nose
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["skin_dark"], (cx, cy - 1), (cx, cy + 2), 1)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["skin_light"], (cx, cy), 1)

        # Beard/mustache - dark brown
        beard_pts = [
            (cx - 6, cy + 2),
            (cx - 7, cy + 6),
            (cx - 5, cy + 10),
            (cx - 3, cy + 12),
            (cx, cy + 13),
            (cx + 3, cy + 12),
            (cx + 5, cy + 10),
            (cx + 7, cy + 6),
            (cx + 6, cy + 2),
            (cx + 3, cy + 3),
            (cx, cy + 4),
            (cx - 3, cy + 3),
        ]
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["hair_darkest"], beard_pts)
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["hair_dark"], [
            (cx - 5, cy + 3),
            (cx - 6, cy + 6),
            (cx - 4, cy + 9),
            (cx - 2, cy + 11),
            (cx, cy + 12),
            (cx + 2, cy + 11),
            (cx + 4, cy + 9),
            (cx + 6, cy + 6),
            (cx + 5, cy + 3),
            (cx + 2, cy + 4),
            (cx - 2, cy + 4),
        ])
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["hair_mid"],
                (cx - 4, cy + 5), (cx - 3, cy + 10), 1)
        _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["hair_mid"],
                (cx + 4, cy + 5), (cx + 3, cy + 10), 1)

        # Mustache (top of beard)
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["hair_darkest"], [
            (cx - 5, cy + 2), (cx - 3, cy + 3), (cx - 5, cy + 4)
        ])
        _NS_kunkka._poly(surface, _NS_kunkka.PALETTE["hair_darkest"], [
            (cx + 5, cy + 2), (cx + 3, cy + 3), (cx + 5, cy + 4)
        ])


    def _draw_body_water_particles(surface, cx, cy, phase):
        """Water droplets around body."""
        for i in range(8):
            angle = phase * 0.4 + i * math.pi / 4
            radius = 28 + int(math.sin(phase * 0.7 + i) * 6)
            px = cx + int(math.cos(angle) * radius)
            py = cy - 5 + int(math.sin(angle) * radius * 0.5)
            alpha = int(140 + math.sin(phase + i * 0.7) * 60)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_dark"], alpha), (px, py), 2)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_bright"], alpha // 2), (px, py), 1)

        # Rising water splashes
        for i in range(4):
            t = ((phase * 0.4 + i * 0.25) % 1.0)
            px = cx + int(math.sin(phase + i) * 18) + (i - 1) * 4
            py = cy + 20 - int(t * 50)
            alpha = int(200 * (1 - t))
            if alpha > 0:
                _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_light"], alpha), (px, py), 1)
                _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_hot"], alpha), (px, py - 1), 1)


    # ===================================================================
    # FLOATING EFFECTS
    # ===================================================================
    def _draw_floating_water(surface, cx, cy, phase, trail=False,
                            facing=1, intense=False):
        """Water mist below floating Kunkka."""
        strength = 1.5 if intense else 1.0

        # Base water mist
        mist = pygame.Surface((120, 40), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        for radius in range(32, 3, -4):
            alpha = int((32 - radius) * 2.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kunkka.PALETTE["water_darkest"], min(255, alpha)),
                    (60 - radius * 2, 20 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        surface.blit(mist, (cx - 60, cy - 10))

        # Rising water wisps
        for i, offset in enumerate((-20, -8, 8, 20)):
            t = (phase * 0.5 + i * 0.25) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 5 - int(t * 24)
            alpha = max(0, min(255, int(200 * (1 - t) * strength)))
            if alpha <= 0:
                continue
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_dark"], alpha), (sx, sy), 5)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_mid"], alpha), (sx, sy - 2), 3)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_bright"], min(255, alpha)),
                      (sx, sy - 3), 1)

        # Orbiting water droplets
        for i in range(5):
            angle = phase * 0.9 + i * math.pi * 2 / 5
            r = 22 + int(math.sin(phase + i * 1.3) * 4)
            sx = cx + int(math.cos(angle) * r)
            sy = cy + int(math.sin(angle) * 6)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["water_mid"], (sx, sy), 3)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["water_light"], (sx, sy), 2)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["water_hot"], (sx, sy), 1)

        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 11 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = max(0, 130 - i * 22)
                _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_mid"], alpha),
                          (sx, sy), max(2, 5 - i))


    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((100, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            alpha = max(0, (10 - radius) * 16)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 10 - radius, 80 + radius * 2, radius * 2),
            )
        pygame.draw.ellipse(shadow, (*_NS_kunkka.PALETTE["water_darkest"], 60), (8, 4, 84, 10))
        surface.blit(shadow, (x - 50, y - 10))


    def _draw_water_aura(surface, x, y, phase):
        """Background water aura."""
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((180, 160), pygame.SRCALPHA)
        for radius in range(72, 5, -4):
            alpha = int((72 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_kunkka._aacircle(aura, (*_NS_kunkka.PALETTE["water_darkest"], min(255, alpha)),
                          (90, 80), radius)
        surface.blit(aura, (x - 90, y - 80))


    def _draw_ground_runes(surface, x, y, phase, skill):
        """Water runes on ground."""
        pulse = math.sin(phase * 1.0) * 0.25 + 0.75
        ring = pygame.Surface((130, 44), pygame.SRCALPHA)

        pygame.draw.ellipse(ring, (*_NS_kunkka.PALETTE["water_dark"], 140),
                            (5, 10, 120, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_kunkka.PALETTE["water_mid"], 170),
                            (20, 14, 90, 16), 2)

        for i in range(10):
            angle = phase * 0.2 + i * math.pi / 5
            x1 = 65 + int(math.cos(angle) * 30)
            y1 = 22 + int(math.sin(angle) * 6)
            x2 = 65 + int(math.cos(angle) * 55)
            y2 = 22 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_kunkka.PALETTE["water_bright"], 160),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_kunkka.PALETTE["water_hot"], int(80 * pulse)),
                                (15, 8, 100, 28), 1)

        surface.blit(ring, (x - 65, y - 22))


    def _draw_sword_swing_trail(surface, x, y, facing, progress):
        """Arc trail during normal sword swing."""
        if progress < 0.3 or progress > 0.7:
            return

        t = (progress - 0.3) / 0.4
        center_x = x + facing * 5
        center_y = y - 8
        radius = 40

        start_angle = -math.pi / 2 - 0.5
        end_angle = math.pi / 4
        current_angle = start_angle + (end_angle - start_angle) * t

        trail_length = 1.5
        segments = 12
        for i in range(segments):
            seg_t = i / segments
            angle = current_angle - trail_length * seg_t
            if angle < start_angle:
                continue

            ax = center_x + int(math.cos(angle) * radius) * facing
            ay = center_y + int(math.sin(angle) * radius)

            alpha_seg = int(200 * (1 - seg_t))
            size = int(4 * (1 - seg_t * 0.5))
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["blade_light"], alpha_seg),
                      (ax, ay), size + 1)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["blade_shine"], alpha_seg),
                      (ax, ay), size)


    def _draw_sword_water_trail(surface, x, y, facing, progress, phase):
        """Water trail during Tide Bringer cast."""
        if progress < 0.15 or progress > 0.7:
            return

        t = (progress - 0.15) / 0.55
        center_x = x + facing * 5
        center_y = y - 8
        radius = 40

        start_angle = -math.pi / 2 - 0.5
        end_angle = math.pi / 4
        current_angle = start_angle + (end_angle - start_angle) * t

        trail_length = 1.8
        segments = 14
        for i in range(segments):
            seg_t = i / segments
            angle = current_angle - trail_length * seg_t
            if angle < start_angle:
                continue

            ax = center_x + int(math.cos(angle) * radius) * facing
            ay = center_y + int(math.sin(angle) * radius)

            alpha_seg = int(230 * (1 - seg_t))
            size = int(5 * (1 - seg_t * 0.4))

            # Water trail
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_dark"], alpha_seg),
                      (ax, ay), size + 2)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_mid"], alpha_seg),
                      (ax, ay), size + 1)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_light"], alpha_seg),
                      (ax, ay), size)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_bright"], alpha_seg),
                      (ax, ay), max(1, size - 2))
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_hot"], alpha_seg),
                      (ax, ay), max(1, size - 3))


    # ===================================================================
    # SKILL W: X MARKS THE SPOT
    # ===================================================================
    def _draw_x_marks_ground(surface, boss, x, y, timer, phase):
        """Ground X mark at target location."""
        tx, ty = _NS_kunkka._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 100))
        pulse = math.sin(phase * 3) * 0.3 + 0.7

        # Ground circle
        radius = int(30 + progress * 10)
        _NS_kunkka._ellipse(surface, (*_NS_kunkka.PALETTE["water_dark"], int(180 * pulse)),
                 (tx - radius, ty - radius // 3,
                  radius * 2, radius * 2 // 3), 3)
        _NS_kunkka._ellipse(surface, (*_NS_kunkka.PALETTE["water_mid"], int(140 * pulse)),
                 (tx - radius + 4, ty - radius // 3 + 3,
                  radius * 2 - 8, radius * 2 // 3 - 6), 2)


    def _draw_x_marks_foreground(surface, boss, x, y, timer, pulse):
        """X mark foreground - the actual X."""
        tx, ty = _NS_kunkka._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 100))

        # Rising water splashes around
        splash_pulse = math.sin(pulse * 3) * 0.3 + 0.7

        # The X (two crossed lines)
        x_size = int(20 + progress * 5)
        thickness = 4

        # First diagonal (top-left to bottom-right)
        _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["water_dark"], 220),
                (tx - x_size, ty - x_size), (tx + x_size, ty + x_size),
                thickness + 2)
        _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["water_mid"], 240),
                (tx - x_size, ty - x_size), (tx + x_size, ty + x_size),
                thickness)
        _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["water_light"], 250),
                (tx - x_size, ty - x_size), (tx + x_size, ty + x_size),
                thickness - 1)
        _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["water_hot"], 255),
                (tx - x_size, ty - x_size), (tx + x_size, ty + x_size),
                1)

        # Second diagonal (top-right to bottom-left)
        _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["water_dark"], 220),
                (tx + x_size, ty - x_size), (tx - x_size, ty + x_size),
                thickness + 2)
        _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["water_mid"], 240),
                (tx + x_size, ty - x_size), (tx - x_size, ty + x_size),
                thickness)
        _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["water_light"], 250),
                (tx + x_size, ty - x_size), (tx - x_size, ty + x_size),
                thickness - 1)
        _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["water_hot"], 255),
                (tx + x_size, ty - x_size), (tx - x_size, ty + x_size),
                1)

        # Red X marker on top (if fully placed)
        if progress > 0.5:
            red_size = 6
            _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["red_x"],
                    (tx - red_size, ty - red_size - 20),
                    (tx + red_size, ty + red_size - 20), 3)
            _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["red_x"],
                    (tx + red_size, ty - red_size - 20),
                    (tx - red_size, ty + red_size - 20), 3)
            _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["red_hot"],
                    (tx - red_size, ty - red_size - 20),
                    (tx + red_size, ty + red_size - 20), 1)
            _NS_kunkka._aaline(surface, _NS_kunkka.PALETTE["red_hot"],
                    (tx + red_size, ty - red_size - 20),
                    (tx - red_size, ty + red_size - 20), 1)

        # Water splashes rising from X
        for i in range(6):
            angle = pulse * 1.5 + i * math.pi / 3
            r = 20 + int(math.sin(pulse * 2 + i) * 5)
            sx = tx + int(math.cos(angle) * r)
            sy = ty - int(abs(math.sin(pulse * 3 + i)) * 15)
            _NS_kunkka._draw_water_splash(surface, sx, sy, 4, pulse + i,
                              int(200 * splash_pulse))

        # Central bright splash
        _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_bright"], int(180 * splash_pulse)),
                  (tx, ty), 6)
        _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_hot"], int(220 * splash_pulse)),
                  (tx, ty), 3)
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["water_white"], (tx, ty), 1)


    # ===================================================================
    # SKILL E: GHOST SHIP
    # ===================================================================
    def _draw_ghost_ship_cast(surface, boss, x, y, timer, phase):
        """Summon the ghost ship."""
        if not getattr(boss, "_kk_ship_spawned", False):
            _NS_kunkka._spawn_ghost_ship(boss, x, y)
            boss._kk_ship_spawned = True

        if timer <= 5:
            boss._kk_ship_spawned = False

        # Casting flash at Kunkka
        hand_x = x + boss.direction * 15
        hand_y = y - 5
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_dark"], 150),
                  (hand_x, hand_y), int(15 * pulse))
        _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_mid"], 200),
                  (hand_x, hand_y), int(10 * pulse))
        _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_bright"], 230),
                  (hand_x, hand_y), int(6 * pulse))
        _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["water_hot"],
                  (hand_x, hand_y), max(1, int(3 * pulse)))


    # ===================================================================
    # SKILL R: TORRENT
    # ===================================================================
    def _draw_torrent_ground(surface, boss, x, y, timer, phase):
        """Ground water swirl at target."""
        tx, ty = _NS_kunkka._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 80))
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Growing swirl on ground
        radius = int(15 + progress * 30)
        for i in range(3):
            r = radius - i * 6
            alpha = int((150 - i * 30) * pulse)
            if r > 0:
                _NS_kunkka._ellipse(surface, (*_NS_kunkka.PALETTE["water_dark"], alpha),
                         (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)

        # Swirling water lines
        for i in range(6):
            angle = phase * 3 + i * math.pi / 3
            x1 = tx + int(math.cos(angle) * (radius - 5))
            y1 = ty + int(math.sin(angle) * (radius // 3 - 2))
            x2 = tx + int(math.cos(angle + 0.5) * radius)
            y2 = ty + int(math.sin(angle + 0.5) * radius // 3)
            _NS_kunkka._aaline(surface, (*_NS_kunkka.PALETTE["water_bright"], int(200 * pulse)),
                    (x1, y1), (x2, y2), 2)


    def _draw_torrent_foreground(surface, boss, x, y, timer, phase):
        """Water spout erupting at target."""
        tx, ty = _NS_kunkka._target_position(boss, x, y)
        progress = max(0.0, min(1.0, 1 - timer / 80))

        # Growing water column
        if progress > 0.3:
            column_progress = (progress - 0.3) / 0.7
            column_height = int(70 * column_progress)
            column_width = int(20 + column_progress * 15)

            # Draw water column with wave
            for i in range(column_height):
                t = i / max(1, column_height)
                wave = math.sin(phase * 4 + t * 8) * 4
                width_here = int(column_width * (1 - t * 0.3))
                alpha = int(220 * (1 - t * 0.4))

                layer_y = ty - i
                layer_x = tx + int(wave)

                # Water column layers
                for w in range(4):
                    w_alpha = alpha - w * 30
                    if w_alpha > 0:
                        _NS_kunkka._rect(surface,
                              (*_NS_kunkka.PALETTE["water_dark"], w_alpha),
                              (layer_x - width_here + w * 2, layer_y,
                               width_here * 2 - w * 4, 2))

                # Bright core
                _NS_kunkka._rect(surface, (*_NS_kunkka.PALETTE["water_light"], alpha),
                      (layer_x - width_here // 2, layer_y, width_here, 2))
                _NS_kunkka._rect(surface, (*_NS_kunkka.PALETTE["water_hot"], alpha),
                      (layer_x - width_here // 4, layer_y, width_here // 2, 2))
                _NS_kunkka._rect(surface, (*_NS_kunkka.PALETTE["water_white"], alpha),
                      (layer_x - 1, layer_y, 2, 2))

            # Water splashes around top
            top_x = tx + int(math.sin(phase * 4 + column_height * 0.05) * 4)
            top_y = ty - column_height
            for i in range(8):
                angle = phase * 2 + i * math.pi / 4
                spread = 20 + int(math.sin(phase * 3 + i) * 8)
                sx = top_x + int(math.cos(angle) * spread)
                sy = top_y + int(math.sin(angle) * spread * 0.5)
                _NS_kunkka._draw_water_splash(surface, sx, sy, 5, phase + i, 220)

            # Big splash at top
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_dark"], 150),
                      (top_x, top_y), 15)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_mid"], 200),
                      (top_x, top_y), 10)
            _NS_kunkka._aacircle(surface, (*_NS_kunkka.PALETTE["water_bright"], 230),
                      (top_x, top_y), 6)
            _NS_kunkka._aacircle(surface, _NS_kunkka.PALETTE["water_hot"], (top_x, top_y), 3)

        # Base water swirl expanding
        base_r = int(30 + progress * 20)
        swirl_pulse = math.sin(phase * 4) * 0.3 + 0.7
        for i in range(3):
            r = base_r - i * 6
            alpha = int(180 * swirl_pulse) - i * 30
            if r > 0 and alpha > 0:
                _NS_kunkka._ellipse(surface, (*_NS_kunkka.PALETTE["water_mid"], alpha),
                         (tx - r, ty - r // 3, r * 2, r * 2 // 3), 2)


    # ===================================================================
    # Backward-compatible entry point alias
    # ===================================================================
    def draw_boss(surface, boss, x, y):
        _NS_kunkka.draw_kunkka(surface, boss, x, y)


# ====================================================================
# ENTRY POINT PUBLIK (dipanggil base_boss.Boss.draw)
# ====================================================================

def draw_gravewake(surface, boss, x, y):
    """Entry point gravewake."""
    return _NS_gravewake.draw_gravewake(surface, boss, x, y)

def draw_syrentha(surface, boss, x, y):
    """Entry point syrentha."""
    return _NS_syrentha.draw_syrentha(surface, boss, x, y)

def draw_thalgryn(surface, boss, x, y):
    """Entry point thalgryn."""
    return _NS_thalgryn.draw_thalgryn(surface, boss, x, y)

def draw_kunkka(surface, boss, x, y):
    """Entry point kunkka."""
    return _NS_kunkka.draw_kunkka(surface, boss, x, y)
