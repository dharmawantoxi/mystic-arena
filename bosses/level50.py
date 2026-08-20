"""
bosses/level50.py - Semua boss Level 50

Berisi:
  - kaelthys  (mini boss - MELEE stillwater blade, water hashira style)
  - kaoruken  (mini boss - MELEE palmseer, Hyuga-style chakra prodigy)
  - vaelkorr  (mini boss - RANGED threadbinder immortal, Kakuzu-style)
  - akirakumo (TRUE BOSS - RANGED moonfang prince, demon prince swordsman)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True


# ====================================================================================================
# KAELTHYS - MINI BOSS
# ====================================================================================================

class _NS_kaelthys:
    """Namespace kaelthys - HD rendering untuk mini boss Kaelthys."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Haori (jubah) — dark side (kiri, hitam-merah)
        "haori_dark_darkest": (25, 8, 12),
        "haori_dark_dark": (55, 20, 25),
        "haori_dark_mid": (95, 35, 40),
        "haori_dark_light": (140, 60, 65),

        # Haori — pattern side (kanan, kuning-hijau geometrik)
        "haori_pat_darkest": (55, 45, 15),
        "haori_pat_dark": (110, 90, 30),
        "haori_pat_mid": (180, 155, 55),
        "haori_pat_light": (230, 210, 110),
        "haori_pat_accent": (60, 90, 40),   # hijau untuk pola
        "haori_pat_accent_light": (120, 165, 70),

        # Inner kimono/uniform (dark)
        "uniform_darkest": (8, 8, 12),
        "uniform_dark": (22, 22, 28),
        "uniform_mid": (48, 48, 58),
        "uniform_light": (85, 85, 100),

        # Skin (pale)
        "skin_dark": (155, 120, 100),
        "skin_mid": (210, 175, 145),
        "skin_light": (245, 215, 185),
        "skin_shine": (255, 240, 220),

        # Hair (black-dark blue)
        "hair_darkest": (5, 5, 15),
        "hair_dark": (18, 18, 30),
        "hair_mid": (40, 40, 55),
        "hair_light": (75, 75, 95),
        "hair_shine": (140, 140, 170),

        # Eyes (piercing blue)
        "eye_dark": (10, 30, 70),
        "eye_mid": (60, 120, 200),
        "eye_light": (150, 210, 255),
        "eye_shine": (230, 245, 255),

        # Katana blade (silver + slight blue)
        "blade_dark": (60, 70, 90),
        "blade_mid": (140, 155, 175),
        "blade_light": (210, 220, 235),
        "blade_shine": (250, 255, 255),
        "blade_edge": (255, 255, 255),

        # Hilt (dark blue/gold)
        "hilt_dark": (20, 20, 30),
        "hilt_mid": (55, 55, 75),
        "hilt_wrap": (30, 40, 80),
        "guard_dark": (60, 50, 20),
        "guard_mid": (140, 115, 55),
        "guard_light": (220, 190, 110),

        # Belt (white/gray)
        "belt_dark": (100, 95, 90),
        "belt_mid": (180, 175, 170),
        "belt_light": (230, 225, 220),

        # WATER effects (signature)
        "water_darkest": (5, 20, 55),
        "water_dark": (15, 55, 120),
        "water_mid": (55, 130, 210),
        "water_light": (130, 200, 250),
        "water_shine": (210, 240, 255),
        "water_foam": (245, 250, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    # ============================================================
    # UTILITIES
    # ============================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaelthys._clamp(color)
        if _NS_kaelthys.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaelthys._clamp(color)
        if _NS_kaelthys.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kaelthys._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 100 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kaelthys(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kaelthys._detect_moving(boss)
        _NS_kaelthys._update_attack_anim(boss)
        attacking = getattr(boss, "_kt_attack_active", False)

        # Ambient
        _NS_kaelthys._draw_shadow(surface, x, y + 52)
        _NS_kaelthys._draw_water_aura(surface, x, y, pulse)
        _NS_kaelthys._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX (behind body)
        if active_skill == "e":
            _NS_kaelthys._draw_waterfall_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaelthys._draw_whirlpool_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_kaelthys._draw_body_attack(surface, boss, x, y)
        elif moving:
            _NS_kaelthys._draw_body_walk(surface, boss, x, y)
        else:
            _NS_kaelthys._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX
        if active_skill == "q":
            _NS_kaelthys._draw_tide_slash_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaelthys._draw_whirlpool_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaelthys._draw_waterfall_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaelthys._draw_rapid_tides_fx(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_kt_attack_active", False))

        if not active:
            if timer >= cooldown - 20:
                boss._kt_attack_active = True
                boss._kt_attack_frame = 0
                active = True

        if active:
            boss._kt_attack_frame = int(getattr(boss, "_kt_attack_frame", 0)) + 1
            attack_duration = 25
            if boss._kt_attack_frame >= attack_duration:
                boss._kt_attack_active = False
                boss._kt_attack_frame = 0
                active = False

        attack_duration = 25
        boss._kt_attack_progress = (
            min(1.0, getattr(boss, "_kt_attack_frame", 0) / attack_duration)
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_kt_last_x"):
            boss._kt_last_x = boss.x
            boss._kt_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kt_last_x)
        dy = abs(boss.y - boss._kt_last_y)
        boss._kt_last_x = boss.x
        boss._kt_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_kaelthys._draw_full_body(surface, x, y + bob,
                                     boss.direction, boss.pulse, "idle", 0)

    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_kaelthys._draw_full_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "walk", 0)

    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_kt_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Melee swing: WIND-UP → SWING → RECOVERY
        if progress < 0.35:
            # Wind-up: step back + raise sword
            t = progress / 0.35
            lunge = -int(t * 5) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            # SWING: lunge forward while swinging
            t = (progress - 0.35) / 0.25
            ease = 1 - (1 - t) ** 2
            lunge = int((-5 + ease * 18)) * boss.direction
            lift = int(3 - ease * 5)
        else:
            # Recovery
            t = (progress - 0.6) / 0.4
            lunge = int(13 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)

        _NS_kaelthys._draw_full_body(surface, x + lunge, y - lift,
                                     boss.direction, boss.pulse, "attack", progress)
        # Water slash arc during swing
        _NS_kaelthys._draw_basic_water_slash(surface, boss, x + lunge,
                                              y - lift, progress)

    # ============================================================
    # FULL BODY (humanoid with katana)
    # ============================================================
    def _draw_full_body(surface, cx, cy, facing, phase, action, atk_prog):
        # 1. Back leg (behind)
        _NS_kaelthys._draw_legs(surface, cx, cy, facing, phase, action)
        # 2. Haori lower/robe
        _NS_kaelthys._draw_haori_lower(surface, cx, cy, facing, phase, action)
        # 3. Back arm (di belakang torso)
        _NS_kaelthys._draw_back_arm(surface, cx, cy, facing, phase, action, atk_prog)
        # 4. Torso + haori upper
        _NS_kaelthys._draw_torso(surface, cx, cy, facing, phase)
        # 5. Head + hair
        _NS_kaelthys._draw_head(surface, cx, cy - 22, facing, phase)
        # 6. Front arm + KATANA (di depan semua)
        _NS_kaelthys._draw_front_arm_with_katana(surface, cx, cy, facing,
                                                  phase, action, atk_prog)

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Two legs in hakama (samurai pants)."""
        leg_sway = 0
        if action == "walk":
            leg_sway = math.sin(phase) * 3

        # Back leg
        back_x = cx - 4
        back_y_top = cy + 8
        back_y_bot = cy + 40 + int(-leg_sway)

        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                             (back_x + 1, back_y_top + 1),
                             (back_x + 1, back_y_bot + 1), 8)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["uniform_darkest"],
                             (back_x, back_y_top), (back_x, back_y_bot), 7)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["uniform_dark"],
                             (back_x, back_y_top), (back_x, back_y_bot), 5)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["uniform_mid"],
                             (back_x - 1, back_y_top), (back_x - 1, back_y_bot), 2)

        # Front leg
        front_x = cx + 4
        front_y_top = cy + 8
        front_y_bot = cy + 40 + int(leg_sway)

        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                             (front_x + 1, front_y_top + 1),
                             (front_x + 1, front_y_bot + 1), 8)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["uniform_darkest"],
                             (front_x, front_y_top), (front_x, front_y_bot), 7)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["uniform_dark"],
                             (front_x, front_y_top), (front_x, front_y_bot), 5)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["uniform_mid"],
                             (front_x - 1, front_y_top), (front_x - 1, front_y_bot), 2)

        # Feet (small dark shape)
        for foot_x, foot_y in ((back_x, back_y_bot), (front_x, front_y_bot)):
            pygame.draw.ellipse(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                                (foot_x - 4, foot_y - 1, 10, 5))
            pygame.draw.ellipse(surface, _NS_kaelthys.PALETTE["uniform_dark"],
                                (foot_x - 3, foot_y, 8, 3))

    def _draw_haori_lower(surface, cx, cy, facing, phase, action):
        """Long flowing haori bottom half - split colors (dark left, patterned right)."""
        sway = math.sin(phase * 0.8) * 2

        # DARK SIDE (Kaelthys left / -facing side)
        dark_side = -facing
        dark_pts = [
            (cx, cy + 8),
            (cx + dark_side * 3, cy + 14),
            (cx + dark_side * 6, cy + 22),
            (cx + dark_side * 9, cy + 32),
            (cx + dark_side * 12 + int(sway * dark_side), cy + 40),
            (cx + dark_side * 10, cy + 42),
            (cx, cy + 40),
        ]
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in dark_pts])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_dark_darkest"], dark_pts)
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_dark_dark"], [
            (cx, cy + 10),
            (cx + dark_side * 2, cy + 16),
            (cx + dark_side * 5, cy + 24),
            (cx + dark_side * 8, cy + 32),
            (cx + dark_side * 10, cy + 38),
            (cx, cy + 38),
        ])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_dark_mid"], [
            (cx, cy + 12),
            (cx + dark_side * 4, cy + 22),
            (cx + dark_side * 6, cy + 32),
            (cx, cy + 34),
        ])

        # PATTERNED SIDE (right side)
        pat_side = facing
        pat_pts = [
            (cx, cy + 8),
            (cx + pat_side * 3, cy + 14),
            (cx + pat_side * 6, cy + 22),
            (cx + pat_side * 9, cy + 32),
            (cx + pat_side * 12 - int(sway * pat_side), cy + 40),
            (cx + pat_side * 10, cy + 42),
            (cx, cy + 40),
        ]
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in pat_pts])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_pat_darkest"], pat_pts)
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_pat_dark"], [
            (cx, cy + 10),
            (cx + pat_side * 2, cy + 16),
            (cx + pat_side * 5, cy + 24),
            (cx + pat_side * 8, cy + 32),
            (cx + pat_side * 10, cy + 38),
            (cx, cy + 38),
        ])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_pat_mid"], [
            (cx, cy + 12),
            (cx + pat_side * 4, cy + 20),
            (cx + pat_side * 7, cy + 30),
            (cx + pat_side * 8, cy + 36),
            (cx, cy + 34),
        ])

        # Geometric pattern (diamonds) on patterned side
        for i, (dx, dy) in enumerate([
            (3, 16), (6, 22), (2, 24), (5, 30), (8, 28), (3, 34),
        ]):
            px = cx + pat_side * dx
            py = cy + dy
            # Diamond shape
            _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_pat_accent"], [
                (px, py - 2), (px + 2, py), (px, py + 2), (px - 2, py),
            ])
            _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_pat_accent_light"], [
                (px, py - 1), (px + 1, py), (px, py + 1), (px - 1, py),
            ])
            pygame.draw.rect(surface, _NS_kaelthys.PALETTE["haori_pat_light"],
                             (px, py, 1, 1))

        # BELT (white sash)
        pygame.draw.rect(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                         (cx - 13, cy + 7, 26, 5))
        pygame.draw.rect(surface, _NS_kaelthys.PALETTE["belt_dark"],
                         (cx - 12, cy + 8, 24, 4))
        pygame.draw.rect(surface, _NS_kaelthys.PALETTE["belt_mid"],
                         (cx - 12, cy + 8, 24, 2))
        pygame.draw.rect(surface, _NS_kaelthys.PALETTE["belt_light"],
                         (cx - 10, cy + 8, 20, 1))
        # Small belt knot
        pygame.draw.rect(surface, _NS_kaelthys.PALETTE["belt_dark"],
                         (cx - 2, cy + 8, 4, 5))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Upper body with haori collar."""
        breath = math.sin(phase * 0.7) * 1

        # Base torso (dark uniform)
        torso_pts = [
            (cx - 11, cy - 8),
            (cx - 13, cy - 2),
            (cx - 12, cy + 6),
            (cx - 8, cy + 9),
            (cx + 8, cy + 9),
            (cx + 12, cy + 6),
            (cx + 13, cy - 2),
            (cx + 11, cy - 8),
            (cx + 5, cy - 12),
            (cx - 5, cy - 12),
        ]
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in torso_pts])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["uniform_darkest"], torso_pts)
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["uniform_dark"], [
            (cx - 10, cy - 6),
            (cx - 11, cy + 2),
            (cx - 6, cy + 7),
            (cx + 6, cy + 7),
            (cx + 11, cy + 2),
            (cx + 10, cy - 6),
            (cx + 4, cy - 10),
            (cx - 4, cy - 10),
        ])

        # HAORI upper (split colors)
        # Dark shoulder (left side from viewer = -facing)
        dark_side = -facing
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_dark_darkest"], [
            (cx, cy - 10),
            (cx + dark_side * 4, cy - 12),
            (cx + dark_side * 12, cy - 8),
            (cx + dark_side * 14, cy - 2),
            (cx + dark_side * 13, cy + 5),
            (cx + dark_side * 8, cy + 9),
            (cx, cy + 8),
        ])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_dark_dark"], [
            (cx, cy - 9),
            (cx + dark_side * 4, cy - 11),
            (cx + dark_side * 11, cy - 7),
            (cx + dark_side * 13, cy - 2),
            (cx + dark_side * 12, cy + 4),
            (cx + dark_side * 7, cy + 8),
            (cx, cy + 7),
        ])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_dark_mid"], [
            (cx, cy - 6),
            (cx + dark_side * 8, cy - 6),
            (cx + dark_side * 10, cy - 2),
            (cx + dark_side * 8, cy + 4),
            (cx, cy + 4),
        ])

        # Patterned shoulder (right)
        pat_side = facing
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_pat_darkest"], [
            (cx, cy - 10),
            (cx + pat_side * 4, cy - 12),
            (cx + pat_side * 12, cy - 8),
            (cx + pat_side * 14, cy - 2),
            (cx + pat_side * 13, cy + 5),
            (cx + pat_side * 8, cy + 9),
            (cx, cy + 8),
        ])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_pat_dark"], [
            (cx, cy - 9),
            (cx + pat_side * 4, cy - 11),
            (cx + pat_side * 11, cy - 7),
            (cx + pat_side * 13, cy - 2),
            (cx + pat_side * 12, cy + 4),
            (cx + pat_side * 7, cy + 8),
            (cx, cy + 7),
        ])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_pat_mid"], [
            (cx, cy - 6),
            (cx + pat_side * 8, cy - 6),
            (cx + pat_side * 10, cy - 2),
            (cx + pat_side * 8, cy + 4),
            (cx, cy + 4),
        ])

        # Diamond pattern on patterned shoulder
        for dx, dy in [(4, -6), (8, -3), (5, 0), (9, 2), (3, 4), (7, 6)]:
            px = cx + pat_side * dx
            py = cy + dy
            _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["haori_pat_accent"], [
                (px, py - 1), (px + 1, py), (px, py + 1), (px - 1, py),
            ])
            pygame.draw.rect(surface, _NS_kaelthys.PALETTE["haori_pat_light"],
                             (px, py, 1, 1))

        # Center opening (V-shape showing dark uniform)
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["uniform_darkest"], [
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx + 1, cy + 4),
            (cx - 1, cy + 4),
        ])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["uniform_dark"], [
            (cx - 2, cy - 9),
            (cx + 2, cy - 9),
            (cx + 1, cy + 2),
            (cx - 1, cy + 2),
        ])

    def _draw_head(surface, cx, cy, facing, phase):
        """Head with long black hair and blue eyes."""
        # HAIR BACK (behind head, long flowing)
        hair_back_pts = [
            (cx - 8, cy + 8),
            (cx - 11, cy + 4),
            (cx - 12, cy - 4),
            (cx - 10, cy - 10),
            (cx - 6, cy - 13),
            (cx + 6, cy - 13),
            (cx + 10, cy - 10),
            (cx + 12, cy - 4),
            (cx + 11, cy + 4),
            (cx + 8, cy + 8),
            (cx + 10, cy + 14),
            (cx + 8, cy + 18),
            (cx + 5, cy + 20),
            (cx - 5, cy + 20),
            (cx - 8, cy + 18),
            (cx - 10, cy + 14),
        ]
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in hair_back_pts])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["hair_darkest"], hair_back_pts)
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["hair_dark"], [
            (cx - 7, cy + 7),
            (cx - 10, cy + 3),
            (cx - 11, cy - 4),
            (cx - 9, cy - 9),
            (cx - 5, cy - 12),
            (cx + 5, cy - 12),
            (cx + 9, cy - 9),
            (cx + 11, cy - 4),
            (cx + 10, cy + 3),
            (cx + 7, cy + 7),
            (cx + 9, cy + 14),
            (cx + 4, cy + 18),
            (cx - 4, cy + 18),
            (cx - 9, cy + 14),
        ])
        # Hair highlights
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["hair_mid"], [
            (cx - 6, cy - 8),
            (cx - 4, cy - 11),
            (cx + 4, cy - 11),
            (cx + 6, cy - 8),
            (cx + 5, cy - 4),
            (cx - 5, cy - 4),
        ])
        pygame.draw.rect(surface, _NS_kaelthys.PALETTE["hair_light"],
                         (cx - 2, cy - 10, 4, 1))
        pygame.draw.rect(surface, _NS_kaelthys.PALETTE["hair_shine"],
                         (cx - 1, cy - 10, 2, 1))

        # FACE
        face_pts = [
            (cx - 5, cy + 5),
            (cx - 6, cy - 2),
            (cx - 4, cy - 6),
            (cx + 4, cy - 6),
            (cx + 6, cy - 2),
            (cx + 5, cy + 5),
        ]
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["skin_dark"], face_pts)
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["skin_mid"], [
            (cx - 4, cy + 4),
            (cx - 5, cy - 2),
            (cx - 3, cy - 5),
            (cx + 3, cy - 5),
            (cx + 5, cy - 2),
            (cx + 4, cy + 4),
        ])
        # Skin highlight
        pygame.draw.line(surface, _NS_kaelthys.PALETTE["skin_light"],
                         (cx - 2, cy - 4), (cx + 2, cy - 4), 1)
        pygame.draw.rect(surface, _NS_kaelthys.PALETTE["skin_shine"],
                         (cx - 1, cy - 4, 2, 1))

        # HAIR BANGS (front, cover forehead)
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["hair_darkest"], [
            (cx - 6, cy - 6),
            (cx - 5, cy - 8),
            (cx - 3, cy - 5),
            (cx, cy - 7),
            (cx + 3, cy - 5),
            (cx + 5, cy - 8),
            (cx + 6, cy - 6),
            (cx + 5, cy - 3),
            (cx - 5, cy - 3),
        ])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["hair_dark"], [
            (cx - 5, cy - 5),
            (cx - 3, cy - 4),
            (cx, cy - 6),
            (cx + 3, cy - 4),
            (cx + 5, cy - 5),
            (cx + 4, cy - 3),
            (cx - 4, cy - 3),
        ])

        # EYES (piercing blue)
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        for eye_x_off in (-2, 2):
            ex = cx + eye_x_off * facing
            ey = cy - 2
            # Eye white
            pygame.draw.rect(surface, _NS_kaelthys.PALETTE["skin_shine"],
                             (ex - 1, ey, 2, 1))
            # Iris (blue)
            pygame.draw.rect(surface, _NS_kaelthys.PALETTE["eye_dark"],
                             (ex, ey, 1, 1))
            # Glow
            for r in range(3, 0, -1):
                alpha = _NS_kaelthys._alpha(70 * (3 - r) / 3 * eye_pulse)
                _NS_kaelthys._aacircle(surface,
                                       (*_NS_kaelthys.PALETTE["eye_mid"], alpha),
                                       (ex, ey), r)
            # Bright pupil highlight
            pygame.draw.rect(surface, _NS_kaelthys.PALETTE["eye_light"],
                             (ex, ey, 1, 1))

        # Mouth (thin line, serious)
        pygame.draw.line(surface, _NS_kaelthys.PALETTE["skin_dark"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)

    def _draw_back_arm(surface, cx, cy, facing, phase, action, atk_prog):
        """Back arm — hidden behind body, holds nothing."""
        sway = math.sin(phase * 0.9) * 2
        back_shoulder_x = cx - facing * 10
        back_shoulder_y = cy - 6
        back_hand_x = back_shoulder_x - facing * 3 + int(sway)
        back_hand_y = cy + 8

        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                             (back_shoulder_x + 1, back_shoulder_y + 1),
                             (back_hand_x + 1, back_hand_y + 1), 6)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["haori_dark_darkest"],
                             (back_shoulder_x, back_shoulder_y),
                             (back_hand_x, back_hand_y), 5)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["haori_dark_dark"],
                             (back_shoulder_x, back_shoulder_y),
                             (back_hand_x, back_hand_y), 3)
        # Back hand
        _NS_kaelthys._aacircle(surface, _NS_kaelthys.PALETTE["skin_dark"],
                               (back_hand_x, back_hand_y), 3)
        _NS_kaelthys._aacircle(surface, _NS_kaelthys.PALETTE["skin_mid"],
                               (back_hand_x, back_hand_y), 2)

    def _draw_front_arm_with_katana(surface, cx, cy, facing, phase, action, atk_prog):
        """Front arm holding katana — the main visual element."""
        sway = math.sin(phase * 0.9) * 2
        front_shoulder_x = cx + facing * 10
        front_shoulder_y = cy - 6

        # Sword position based on action
        # Sword angle in radians. 0 = pointing right (facing direction)
        # Positive angle = swinging down toward ground
        if action == "attack":
            if atk_prog < 0.35:
                # WIND-UP: sword raised HIGH above head (angle up-back)
                t = atk_prog / 0.35
                # Rotate from horizontal (0) to raised (-135deg from facing)
                sword_angle = -math.pi * 0.25 - t * math.pi * 0.75
                hand_offset_x = facing * int(-6 - t * 2)
                hand_offset_y = int(-6 - t * 8)
            elif atk_prog < 0.6:
                # SWING: fast downward slash
                t = (atk_prog - 0.35) / 0.25
                ease = 1 - (1 - t) ** 2
                # Rotate from raised to fully extended forward-down
                sword_angle = -math.pi * 1.0 + ease * math.pi * 1.15
                hand_offset_x = facing * int(-8 + ease * 22)
                hand_offset_y = int(-14 + ease * 18)
            else:
                # Recovery
                t = (atk_prog - 0.6) / 0.4
                sword_angle = math.pi * 0.15 - t * math.pi * 0.15
                hand_offset_x = facing * int(14 - t * 10)
                hand_offset_y = int(4 - t * 4)
        elif action == "walk":
            # Sword held ready
            sword_angle = -math.pi * 0.15 + math.sin(phase) * 0.05
            hand_offset_x = facing * 8
            hand_offset_y = int(4 + sway)
        else:
            # Idle: sword held at side, tip up-forward
            sword_angle = -math.pi * 0.2 + math.sin(phase * 0.5) * 0.03
            hand_offset_x = facing * 8
            hand_offset_y = int(4 - sway)

        front_hand_x = front_shoulder_x + hand_offset_x
        front_hand_y = front_shoulder_y + hand_offset_y

        # Elbow (curved arm)
        elbow_x = int((front_shoulder_x + front_hand_x) / 2) + facing * 3
        elbow_y = int((front_shoulder_y + front_hand_y) / 2) + 1

        # ARM (upper + forearm)
        # Upper arm
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                             (front_shoulder_x + 1, front_shoulder_y + 1),
                             (elbow_x + 1, elbow_y + 1), 6)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["haori_pat_darkest"],
                             (front_shoulder_x, front_shoulder_y),
                             (elbow_x, elbow_y), 5)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["haori_pat_dark"],
                             (front_shoulder_x, front_shoulder_y),
                             (elbow_x, elbow_y), 3)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["haori_pat_mid"],
                             (front_shoulder_x - 1, front_shoulder_y - 1),
                             (elbow_x - 1, elbow_y - 1), 1)
        # Forearm (uniform sleeve)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 1),
                             (front_hand_x + 1, front_hand_y + 1), 5)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["uniform_darkest"],
                             (elbow_x, elbow_y),
                             (front_hand_x, front_hand_y), 4)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["uniform_dark"],
                             (elbow_x, elbow_y),
                             (front_hand_x, front_hand_y), 2)

        # HAND (holding hilt)
        _NS_kaelthys._aacircle(surface, _NS_kaelthys.PALETTE["skin_dark"],
                               (front_hand_x, front_hand_y), 4)
        _NS_kaelthys._aacircle(surface, _NS_kaelthys.PALETTE["skin_mid"],
                               (front_hand_x, front_hand_y), 3)
        pygame.draw.rect(surface, _NS_kaelthys.PALETTE["skin_light"],
                         (front_hand_x - 1, front_hand_y - 1, 1, 1))

        # KATANA
        _NS_kaelthys._draw_katana(surface, front_hand_x, front_hand_y,
                                    sword_angle, facing)

    def _draw_katana(surface, hand_x, hand_y, angle, facing):
        """Katana blade rendered at given angle from hand position."""
        # Katana components (from hand):
        # - Guard (tsuba) — small perpendicular disc
        # - Blade — long curved single-edge
        # - Handle actually extends BACKWARD from hand slightly

        # If facing left, invert angle horizontally
        actual_angle = angle if facing > 0 else math.pi - angle

        blade_length = 32
        # Blade tip position
        tip_x = hand_x + int(math.cos(actual_angle) * blade_length)
        tip_y = hand_y + int(math.sin(actual_angle) * blade_length)

        # Guard position (right next to hand, perpendicular)
        perp_x = -math.sin(actual_angle)
        perp_y = math.cos(actual_angle)
        guard_a = (hand_x + int(perp_x * 4), hand_y + int(perp_y * 4))
        guard_b = (hand_x - int(perp_x * 4), hand_y - int(perp_y * 4))

        # BLADE (shadow first)
        blade_side_x = -math.sin(actual_angle) * 2
        blade_side_y = math.cos(actual_angle) * 2

        # Full blade polygon (elongated)
        blade_pts = [
            (hand_x + int(blade_side_x), hand_y + int(blade_side_y)),
            (tip_x + int(blade_side_x * 0.3), tip_y + int(blade_side_y * 0.3)),
            (tip_x, tip_y),
            (hand_x - int(blade_side_x), hand_y - int(blade_side_y)),
        ]
        # Shadow
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in blade_pts])
        # Blade body
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["blade_dark"], blade_pts)
        # Bright side (top/back of blade)
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["blade_mid"], [
            (hand_x + int(blade_side_x * 0.5), hand_y + int(blade_side_y * 0.5)),
            (tip_x + int(blade_side_x * 0.2), tip_y + int(blade_side_y * 0.2)),
            (tip_x, tip_y),
            (hand_x, hand_y),
        ])
        _NS_kaelthys._poly(surface, _NS_kaelthys.PALETTE["blade_light"], [
            (hand_x, hand_y),
            (tip_x, tip_y),
            (int((hand_x + tip_x) / 2), int((hand_y + tip_y) / 2)),
        ])
        # Bright edge line
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["blade_shine"],
                             (hand_x, hand_y), (tip_x, tip_y), 1)
        # Tip highlight
        pygame.draw.rect(surface, _NS_kaelthys.PALETTE["blade_edge"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_kaelthys.PALETTE["white"],
                         (tip_x, tip_y, 1, 1))

        # GUARD (tsuba)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["guard_dark"],
                             guard_a, guard_b, 3)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["guard_mid"],
                             guard_a, guard_b, 1)
        pygame.draw.rect(surface, _NS_kaelthys.PALETTE["guard_light"],
                         (hand_x, hand_y, 1, 1))

        # HILT (extending backward from hand, small)
        back_x = hand_x - int(math.cos(actual_angle) * 6)
        back_y = hand_y - int(math.sin(actual_angle) * 6)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["hilt_dark"],
                             (hand_x, hand_y), (back_x, back_y), 4)
        _NS_kaelthys._aaline(surface, _NS_kaelthys.PALETTE["hilt_wrap"],
                             (hand_x, hand_y), (back_x, back_y), 2)

    # ============================================================
    # BASIC MELEE ATTACK — WATER SLASH ARC
    # ============================================================
    def _draw_basic_water_slash(surface, boss, x, y, progress):
        """Water crescent arc appears during swing phase."""
        # Only show during swing phase (0.35 - 0.6)
        if progress < 0.35 or progress > 0.75:
            return

        facing = boss.direction
        # Slash intensity peaks in middle of swing
        if progress < 0.6:
            t = (progress - 0.35) / 0.25
        else:
            t = 1 - (progress - 0.6) / 0.15
        intensity = math.sin(t * math.pi)

        # Slash arc center (in front of boss)
        cx = x + facing * 20
        cy = y - 4

        # Draw crescent water arc
        arc_radius = int(28 + t * 8)
        arc_thickness = 4

        # Arc goes from top-back to bottom-front (downward slash)
        start_angle = -math.pi * 0.9 * facing  # depend on facing
        end_angle = math.pi * 0.1 * facing
        if facing < 0:
            start_angle, end_angle = end_angle, start_angle

        # Draw arc as multiple curved line segments
        segments = 20
        prev_x, prev_y = None, None
        for i in range(segments + 1):
            t_seg = i / segments
            # Interpolate angle based on swing progress (only draw portion visible)
            angle_range = math.pi * 1.0
            base_angle = -math.pi * 0.6 * facing
            seg_angle = base_angle + t_seg * angle_range * facing

            sx = cx + int(math.cos(seg_angle) * arc_radius)
            sy = cy + int(math.sin(seg_angle) * arc_radius)

            if prev_x is not None:
                # Only render the "swept" portion
                sweep_progress = t * 1.2
                if t_seg <= sweep_progress:
                    fade = 1.0 - max(0, (sweep_progress - t_seg) * 2)

                    # Multi-layer water arc
                    alpha_outer = _NS_kaelthys._alpha(180 * intensity * fade)
                    alpha_mid = _NS_kaelthys._alpha(220 * intensity * fade)
                    alpha_core = _NS_kaelthys._alpha(255 * intensity * fade)

                    pygame.draw.line(surface,
                                     (*_NS_kaelthys.PALETTE["water_dark"], alpha_outer),
                                     (prev_x, prev_y), (sx, sy), 6)
                    pygame.draw.line(surface,
                                     (*_NS_kaelthys.PALETTE["water_mid"], alpha_mid),
                                     (prev_x, prev_y), (sx, sy), 4)
                    pygame.draw.line(surface,
                                     (*_NS_kaelthys.PALETTE["water_light"], alpha_core),
                                     (prev_x, prev_y), (sx, sy), 2)
                    pygame.draw.line(surface,
                                     (*_NS_kaelthys.PALETTE["water_shine"], alpha_core),
                                     (prev_x, prev_y), (sx, sy), 1)

                    # Water droplets flying off
                    if i % 3 == 0 and fade > 0.5:
                        for drop_i in range(2):
                            drop_off_x = int(math.cos(seg_angle) * (drop_i + 2) * 2)
                            drop_off_y = int(math.sin(seg_angle) * (drop_i + 2) * 2)
                            pygame.draw.rect(surface,
                                             _NS_kaelthys.PALETTE["water_light"],
                                             (sx + drop_off_x, sy + drop_off_y, 2, 2))
                            pygame.draw.rect(surface,
                                             _NS_kaelthys.PALETTE["water_foam"],
                                             (sx + drop_off_x, sy + drop_off_y, 1, 1))

            prev_x, prev_y = sx, sy

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 13 - radius,
                                 100 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, 170), (5, 7, 110, 12))
        surface.blit(shadow, (x - 60, y - 13))

    def _draw_water_aura(surface, x, y, phase):
        """Subtle water aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((180, 150), pygame.SRCALPHA)
        for radius in range(70, 5, -5):
            alpha = _NS_kaelthys._alpha((70 - radius) * 0.8 * pulse)
            if alpha > 0:
                _NS_kaelthys._aacircle(aura,
                                       (*_NS_kaelthys.PALETTE["water_dark"], alpha),
                                       (90, 75), radius)
        for radius in range(40, 5, -4):
            alpha = _NS_kaelthys._alpha((40 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_kaelthys._aacircle(aura,
                                       (*_NS_kaelthys.PALETTE["water_mid"], alpha),
                                       (90, 75), radius)
        surface.blit(aura, (x - 90, y - 75))

        # Floating water droplets
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            radius = 32 + int(math.sin(phase + i) * 8)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_kaelthys.PALETTE["water_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kaelthys.PALETTE["water_light"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring — subtle water ripples."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kaelthys.PALETTE["water_darkest"], 180),
                            (5, 15, 140, 22), 3)
        pygame.draw.ellipse(ring, (*_NS_kaelthys.PALETTE["water_dark"], 200),
                            (14, 17, 122, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_kaelthys.PALETTE["water_mid"], 180),
                            (25, 19, 100, 14), 1)

        # Ripple lines
        for i in range(3):
            r_off = int((phase * 20 + i * 30) % 60)
            alpha = _NS_kaelthys._alpha(150 * (1 - r_off / 60))
            pygame.draw.ellipse(ring, (*_NS_kaelthys.PALETTE["water_light"], alpha),
                                (25 - r_off // 4, 19 - r_off // 8,
                                 100 + r_off // 2, 14 + r_off // 4), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_kaelthys.PALETTE["water_shine"],
                                 _NS_kaelthys._alpha(150 * pulse)),
                                (15, 10, 120, 32), 1)
        surface.blit(ring, (x - 75, y - 23))

    # ============================================================
    # SKILL Q — TIDE SLASH (large horizontal wave)
    # ============================================================
    def _draw_tide_slash_fx(surface, boss, x, y, timer, phase):
        """Large horizontal water wave traveling forward."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Wave travels forward
        travel_dist = int(220 * progress)
        wave_center_x = x + facing * (30 + travel_dist)
        wave_center_y = y - 4

        # Wave dimensions
        wave_w = 60
        wave_h = 40

        # Fade out as it travels
        fade = 1.0 - progress * 0.5

        # Main crescent wave
        arc_points = []
        segments = 24
        for i in range(segments + 1):
            t = i / segments
            # Crescent from top to bottom
            angle = -math.pi * 0.5 + t * math.pi
            ax = wave_center_x + int(math.cos(angle) * wave_w * 0.5) * facing
            ay = wave_center_y + int(math.sin(angle) * wave_h * 0.6)
            arc_points.append((ax, ay))

        # Draw thick water crescent
        for i in range(len(arc_points) - 1):
            alpha = _NS_kaelthys._alpha(230 * fade)
            # Outer glow
            pygame.draw.line(surface,
                             (*_NS_kaelthys.PALETTE["water_dark"], alpha),
                             arc_points[i], arc_points[i + 1], 10)
            pygame.draw.line(surface,
                             (*_NS_kaelthys.PALETTE["water_mid"], alpha),
                             arc_points[i], arc_points[i + 1], 6)
            pygame.draw.line(surface,
                             (*_NS_kaelthys.PALETTE["water_light"], alpha),
                             arc_points[i], arc_points[i + 1], 3)
            pygame.draw.line(surface,
                             (*_NS_kaelthys.PALETTE["water_shine"], alpha),
                             arc_points[i], arc_points[i + 1], 1)

        # Water droplets trailing
        for i in range(20):
            drop_angle = phase * 2 + i * math.pi / 10
            drop_r = 20 + int(math.sin(phase * 3 + i) * 10)
            dx = wave_center_x + int(math.cos(drop_angle) * drop_r) * facing
            dy = wave_center_y + int(math.sin(drop_angle) * drop_r * 0.6)
            alpha = _NS_kaelthys._alpha(200 * fade)
            pygame.draw.rect(surface,
                             (*_NS_kaelthys.PALETTE["water_light"], alpha),
                             (dx, dy, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_kaelthys.PALETTE["water_foam"], alpha),
                             (dx, dy, 1, 1))

        # Trail behind (fading arc echoes)
        for echo_i in range(4):
            echo_dist = travel_dist - (echo_i + 1) * 20
            if echo_dist < 0:
                break
            echo_x = x + facing * (30 + echo_dist)
            echo_alpha = _NS_kaelthys._alpha(120 * fade * (1 - echo_i * 0.25))
            for i in range(0, segments, 2):
                t = i / segments
                angle = -math.pi * 0.5 + t * math.pi
                ax = echo_x + int(math.cos(angle) * wave_w * 0.4) * facing
                ay = wave_center_y + int(math.sin(angle) * wave_h * 0.5)
                pygame.draw.rect(surface,
                                 (*_NS_kaelthys.PALETTE["water_light"], echo_alpha),
                                 (ax, ay, 2, 2))

    # ============================================================
    # SKILL W — WHIRLPOOL (spinning vortex)
    # ============================================================
    def _draw_whirlpool_ground(surface, boss, x, y, timer, phase):
        """Water pool on ground."""
        tx, ty = _NS_kaelthys._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(45 * min(1.0, progress * 3))

        if r > 3:
            # Base water pool
            pygame.draw.ellipse(surface, (*_NS_kaelthys.PALETTE["water_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_kaelthys.PALETTE["water_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_kaelthys.PALETTE["water_mid"], 150),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_whirlpool_fx(surface, boss, x, y, timer, phase):
        """Spinning spiral vortex above ground pool."""
        tx, ty = _NS_kaelthys._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        max_r = int(45 * min(1.0, progress * 3))

        if max_r < 5:
            return

        # Draw spiral arms
        spiral_speed = phase * 3
        num_arms = 4
        for arm_i in range(num_arms):
            arm_offset = arm_i * math.pi * 2 / num_arms
            prev = None
            for step in range(30):
                t = step / 30
                spiral_angle = spiral_speed + arm_offset + t * math.pi * 3
                r = int(max_r * (1 - t) * 0.9 + 3)
                sx = tx + int(math.cos(spiral_angle) * r)
                sy = ty + int(math.sin(spiral_angle) * r * 0.4)
                alpha = _NS_kaelthys._alpha(230 * (1 - t * 0.5))

                if prev is not None:
                    pygame.draw.line(surface,
                                     (*_NS_kaelthys.PALETTE["water_dark"], alpha),
                                     prev, (sx, sy), 4)
                    pygame.draw.line(surface,
                                     (*_NS_kaelthys.PALETTE["water_mid"], alpha),
                                     prev, (sx, sy), 2)
                    pygame.draw.line(surface,
                                     (*_NS_kaelthys.PALETTE["water_light"], alpha),
                                     prev, (sx, sy), 1)

                # Water sparkle at tip
                if step % 4 == 0:
                    pygame.draw.rect(surface,
                                     (*_NS_kaelthys.PALETTE["water_foam"], alpha),
                                     (sx, sy, 2, 2))
                prev = (sx, sy)

        # Central vortex hole (dark)
        _NS_kaelthys._aacircle(surface, _NS_kaelthys.PALETTE["water_darkest"],
                               (tx, ty), 5)
        _NS_kaelthys._aacircle(surface, _NS_kaelthys.PALETTE["shadow_deep"],
                               (tx, ty), 3)

        # Water droplets flying inward
        for i in range(10):
            in_angle = phase * 2 + i * math.pi / 5
            in_dist = max_r + int(math.sin(phase * 4 + i) * 8)
            dx = tx + int(math.cos(in_angle) * in_dist)
            dy = ty + int(math.sin(in_angle) * in_dist * 0.4)
            pygame.draw.rect(surface, _NS_kaelthys.PALETTE["water_light"], (dx, dy, 2, 2))
            pygame.draw.rect(surface, _NS_kaelthys.PALETTE["water_foam"], (dx, dy, 1, 1))

    # ============================================================
    # SKILL E — WATERFALL COLUMN (vertical strike)
    # ============================================================
    def _draw_waterfall_ground(surface, boss, x, y, timer, phase):
        """Impact splash on ground."""
        tx, ty = _NS_kaelthys._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = int(35 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_kaelthys.PALETTE["water_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_kaelthys.PALETTE["water_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_kaelthys.PALETTE["water_mid"], 150),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_waterfall_fx(surface, boss, x, y, timer, phase):
        """Vertical column of falling water crashing down."""
        tx, ty = _NS_kaelthys._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Column dimensions
        col_top_y = max(0, ty - 180)
        col_width = 24

        # Falling water animation
        if progress < 0.15:
            # Wind-up: only warning glow
            t = progress / 0.15
            warn_alpha = _NS_kaelthys._alpha(120 * t)
            pygame.draw.rect(surface,
                             (*_NS_kaelthys.PALETTE["water_light"], warn_alpha),
                             (tx - col_width // 2, ty - 3, col_width, 3))
        else:
            t = (progress - 0.15) / 0.85
            intensity = math.sin(min(1.0, t * 2) * math.pi * 0.5)

            # Main column (multi-layer)
            layers = [
                (col_width, 100),
                (col_width - 6, 180),
                (col_width - 12, 220),
                (col_width - 18, 255),
            ]
            colors = [
                _NS_kaelthys.PALETTE["water_dark"],
                _NS_kaelthys.PALETTE["water_mid"],
                _NS_kaelthys.PALETTE["water_light"],
                _NS_kaelthys.PALETTE["water_shine"],
            ]
            for (w, base_a), color in zip(layers, colors):
                actual_alpha = _NS_kaelthys._alpha(base_a * intensity)
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (tx - w // 2, col_top_y, w, ty - col_top_y))

            # Rushing water motion lines
            for i in range(15):
                line_t = (phase * 3 + i * 0.12) % 1.0
                line_y = col_top_y + int(line_t * (ty - col_top_y))
                line_x = tx + int(math.sin(phase * 4 + i) * 4)
                pygame.draw.rect(surface, _NS_kaelthys.PALETTE["water_foam"],
                                 (line_x - 4, line_y, 8, 1))
                pygame.draw.rect(surface, _NS_kaelthys.PALETTE["white"],
                                 (line_x, line_y, 2, 1))

            # Splash at bottom
            for i in range(12):
                spl_angle = i * math.pi / 6
                spl_r = int(15 + math.sin(phase * 5 + i) * 8)
                sx = tx + int(math.cos(spl_angle) * spl_r)
                sy = ty + int(math.sin(spl_angle) * spl_r * 0.4)
                alpha = _NS_kaelthys._alpha(220 * intensity)
                pygame.draw.rect(surface,
                                 (*_NS_kaelthys.PALETTE["water_light"], alpha),
                                 (sx, sy, 3, 3))
                pygame.draw.rect(surface,
                                 (*_NS_kaelthys.PALETTE["water_foam"], alpha),
                                 (sx, sy, 2, 2))

            # Upward splash particles
            for i in range(10):
                part_t = (phase * 1.5 + i * 0.1) % 1.0
                px = tx + int(math.sin(phase * 3 + i) * 20) - 10
                py = ty - int(part_t * 40)
                alpha = _NS_kaelthys._alpha(200 * (1 - part_t) * intensity)
                _NS_kaelthys._aacircle(surface,
                                       (*_NS_kaelthys.PALETTE["water_mid"], alpha),
                                       (px, py), 2)
                pygame.draw.rect(surface,
                                 (*_NS_kaelthys.PALETTE["water_light"], alpha),
                                 (px, py, 1, 1))

    # ============================================================
    # SKILL R — RAPID TIDES (multi-slash)
    # ============================================================
    def _draw_rapid_tides_fx(surface, boss, x, y, timer, phase):
        """Multiple slash arcs in rapid succession."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # 5 slashes at different times and angles
        num_slashes = 5
        for slash_i in range(num_slashes):
            slash_start = slash_i * 0.12
            slash_end = slash_start + 0.35
            if progress < slash_start or progress > slash_end:
                continue

            slash_t = (progress - slash_start) / (slash_end - slash_start)
            slash_intensity = math.sin(slash_t * math.pi)

            # Vary slash position and angle
            offset_x = (slash_i - 2) * 15
            offset_y = (slash_i % 2) * 10 - 5

            cx = x + facing * (25 + offset_x)
            cy = y - 4 + offset_y

            arc_radius = 24
            arc_thickness = 3

            # Draw curved slash
            segments = 15
            prev = None
            for i in range(segments + 1):
                t = i / segments
                base_angle = -math.pi * 0.5 * facing + (slash_i % 2) * 0.3
                seg_angle = base_angle + t * math.pi * facing
                sx = cx + int(math.cos(seg_angle) * arc_radius)
                sy = cy + int(math.sin(seg_angle) * arc_radius * 0.7)

                if prev is not None and t <= slash_t * 1.2:
                    fade = 1.0 - max(0, (slash_t * 1.2 - t) * 1.5)
                    alpha = _NS_kaelthys._alpha(230 * slash_intensity * fade)

                    pygame.draw.line(surface,
                                     (*_NS_kaelthys.PALETTE["water_dark"], alpha),
                                     prev, (sx, sy), 5)
                    pygame.draw.line(surface,
                                     (*_NS_kaelthys.PALETTE["water_mid"], alpha),
                                     prev, (sx, sy), 3)
                    pygame.draw.line(surface,
                                     (*_NS_kaelthys.PALETTE["water_light"], alpha),
                                     prev, (sx, sy), 1)

                    # Droplets
                    if i % 3 == 0:
                        pygame.draw.rect(surface,
                                         (*_NS_kaelthys.PALETTE["water_foam"], alpha),
                                         (sx, sy, 2, 2))

                prev = (sx, sy)


# ====================================================================
# ALIAS untuk convenience
# ====================================================================
draw_kaelthys = _NS_kaelthys.draw_kaelthys


# ====================================================================================================
# KAORUKEN - MINI BOSS
# ====================================================================================================

class _NS_kaoruken:
    """Namespace kaoruken - Hyuga-style chakra prodigy boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Skin (fair, natural)
        "skin_darkest": (75, 55, 45),
        "skin_dark": (150, 110, 90),
        "skin_mid": (215, 175, 145),
        "skin_light": (240, 210, 180),
        "skin_shine": (255, 235, 210),

        # Hair (long dark brown-black)
        "hair_darkest": (15, 10, 12),
        "hair_dark": (35, 22, 25),
        "hair_mid": (70, 50, 55),
        "hair_light": (115, 90, 95),
        "hair_shine": (170, 140, 145),

        # Robe (cream/beige gi)
        "robe_darkest": (85, 75, 55),
        "robe_dark": (155, 140, 105),
        "robe_mid": (210, 195, 155),
        "robe_light": (240, 228, 195),
        "robe_shine": (255, 250, 225),

        # Dark pants (grey-brown)
        "pants_darkest": (18, 15, 20),
        "pants_dark": (45, 40, 48),
        "pants_mid": (85, 78, 92),
        "pants_light": (130, 120, 140),

        # Wrappings (tan bandages)
        "wrap_dark": (95, 75, 45),
        "wrap_mid": (170, 140, 90),
        "wrap_light": (220, 195, 150),

        # Byakugan eyes (pale white-lavender)
        "eye_socket": (40, 45, 55),
        "eye_dark": (140, 145, 155),
        "eye_mid": (215, 218, 230),
        "eye_light": (245, 248, 255),
        "eye_glow": (255, 255, 255),
        "eye_vein": (140, 90, 155),

        # Chakra cyan-teal (signature Gentle Fist)
        "chakra_darkest": (5, 40, 45),
        "chakra_dark": (15, 100, 115),
        "chakra_mid": (60, 200, 220),
        "chakra_light": (150, 240, 250),
        "chakra_hot": (210, 250, 255),
        "chakra_shine": (245, 255, 255),

        # Headband metal
        "metal_dark": (30, 30, 38),
        "metal_mid": (95, 95, 110),
        "metal_light": (170, 170, 185),
        "metal_shine": (225, 225, 240),

        # Gold accents
        "gold_dark": (95, 65, 15),
        "gold_mid": (200, 155, 50),
        "gold_light": (245, 210, 100),
        "gold_shine": (255, 240, 165),

        # Lion (bright chakra creature)
        "lion_dark": (25, 90, 100),
        "lion_mid": (85, 200, 215),
        "lion_light": (180, 245, 250),
        "lion_hot": (230, 255, 255),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    # ── helpers ──────────────────────────────────────────────
    def _clamp(c):
        return tuple(max(0, min(255, int(v))) for v in c)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kaoruken._clamp(color)
        if _NS_kaoruken.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaoruken._clamp(color)
        if _NS_kaoruken.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_kaoruken._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 250 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kaoruken(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kaoruken._detect_moving(boss)
        _NS_kaoruken._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kao_attack_active", False)
            or getattr(boss, "timer", 0)
            > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient
        _NS_kaoruken._draw_chakra_aura(surface, x, y, pulse)
        _NS_kaoruken._draw_ground_ring(surface, x, y + 50, pulse, active_skill)

        # Skill ground FX
        if active_skill == "e":
            _NS_kaoruken._draw_rotation_ground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "w":
            _NS_kaoruken._draw_64palms_ground(
                surface, boss, x, y, skill_timer, pulse
            )

        # Body pose
        if attacking:
            _NS_kaoruken._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_kaoruken._draw_walk_pose(surface, boss, x, y)
        else:
            _NS_kaoruken._draw_idle_pose(surface, boss, x, y)

        # Overlays on body
        if active_skill == "e":
            _NS_kaoruken._draw_rotation_overlay(
                surface, boss, x, y, skill_timer, pulse
            )

        # Foreground FX
        if active_skill == "q":
            _NS_kaoruken._draw_gentle_fist(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "w":
            _NS_kaoruken._draw_64palms(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "r":
            _NS_kaoruken._draw_lion_fist(
                surface, boss, x, y, skill_timer, pulse
            )

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cd = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))
        prev = int(getattr(boss, "_kao_prev_timer", 0))
        active = bool(getattr(boss, "_kao_attack_active", False))
        if timer >= cd - 1 and prev <= 1:
            boss._kao_attack_active = True
            boss._kao_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kao_attack_frame = int(
                getattr(boss, "_kao_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._kao_attack_active = False
            boss._kao_attack_frame = 0
            active = False
        boss._kao_prev_timer = timer
        boss._kao_attack_progress = (
            min(1.0, getattr(boss, "_kao_attack_frame", 0) / max(1, cd - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_kao_last_x"):
            boss._kao_last_x = boss.x
            boss._kao_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kao_last_x)
        dy = abs(boss.y - boss._kao_last_y)
        boss._kao_last_x = boss.x
        boss._kao_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 5)
        _NS_kaoruken._draw_shadow(surface, x, y + 50)
        _NS_kaoruken._draw_float_wisps(surface, x, y + 46, boss.pulse)
        _NS_kaoruken._draw_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle"
        )

    def _draw_walk_pose(surface, boss, x, y):
        ph = boss.pulse * 1.4
        bob = int(math.sin(ph * 1.1) * 6)
        sway = int(math.sin(ph * 0.7) * 3)
        _NS_kaoruken._draw_shadow(surface, x + sway, y + 50)
        _NS_kaoruken._draw_float_wisps(
            surface, x + sway, y + 46, ph, trail=True, facing=boss.direction
        )
        _NS_kaoruken._draw_body(
            surface, x + sway, y + bob, boss.direction, ph, "walk"
        )

    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_kao_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Palm strike: pull back → thrust forward → recover
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 3)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            lunge = int((-4 + t * 18)) * boss.direction
            lift = int(3 - t * 5)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(14 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.6) * 2)
        _NS_kaoruken._draw_shadow(surface, x + lunge, y + 50)
        _NS_kaoruken._draw_float_wisps(
            surface, x + lunge, y + 46, boss.pulse, intense=True
        )
        _NS_kaoruken._draw_palm_thrust_trail(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )
        _NS_kaoruken._draw_body(
            surface, x + lunge, y - lift + bob, boss.direction,
            boss.pulse, "attack", progress,
        )
        _NS_kaoruken._draw_palm_hit_impact(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )

    # ============================================================
    # BODY COMPOSITION
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, progress=0,
                   alpha=255):
        if alpha < 255:
            temp = pygame.Surface((180, 180), pygame.SRCALPHA)
            _NS_kaoruken._draw_body_parts(
                temp, 90, 90, facing, phase, action, progress
            )
            temp.set_alpha(alpha)
            surface.blit(temp, (cx - 90, cy - 90))
        else:
            _NS_kaoruken._draw_body_parts(
                surface, cx, cy, facing, phase, action, progress
            )

    def _draw_body_parts(surface, cx, cy, facing, phase, action, progress):
        # Order: long hair back -> back arm -> legs ->
        # robe body -> waist wrap -> head -> hair front ->
        # headband -> front arm+palm
        _NS_kaoruken._draw_hair_back(surface, cx, cy, facing, phase)
        _NS_kaoruken._draw_back_arm(surface, cx, cy, facing, phase, action, progress)
        _NS_kaoruken._draw_legs(surface, cx, cy, facing, phase, action)
        _NS_kaoruken._draw_torso(surface, cx, cy, facing, phase)
        _NS_kaoruken._draw_head(surface, cx, cy, facing, phase)
        _NS_kaoruken._draw_hair_front(surface, cx, cy, facing, phase)
        _NS_kaoruken._draw_headband(surface, cx, cy, facing, phase)
        _NS_kaoruken._draw_front_arm_palm(
            surface, cx, cy, facing, phase, action, progress
        )

    # ── LEGS (dark pants + wrapped calves) ───────────────────
    def _draw_legs(surface, cx, cy, facing, phase, action):
        sway = (
            math.sin(phase * 1.4) * 3
            if action == "walk"
            else math.sin(phase * 0.5) * 1.5
        )
        for side in (-1, 1):
            lx = cx + side * 5
            ly = cy + 14
            sw = int(sway * (1 if side > 0 else -1))
            # Thigh (dark pants — shorts to knee)
            thigh = [
                (lx - 3, ly - 1), (lx + 3, ly - 1),
                (lx + 4 + sw, ly + 6), (lx - 4 + sw, ly + 6),
            ]
            _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["shadow_deep"],
                               [(p[0] + 1, p[1] + 2) for p in thigh])
            _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["pants_darkest"], thigh)
            _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["pants_dark"], [
                (lx - 2, ly), (lx + 2, ly),
                (lx + 3 + sw, ly + 5), (lx - 3 + sw, ly + 5),
            ])
            _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["pants_mid"], [
                (lx - 1, ly + 1), (lx + 1, ly + 1),
                (lx + 1 + sw, ly + 4), (lx - 1 + sw, ly + 4),
            ])
            # Hem line at knee
            pygame.draw.line(surface, _NS_kaoruken.PALETTE["pants_light"],
                             (lx - 4 + sw, ly + 6),
                             (lx + 4 + sw, ly + 6), 1)
            # Wrapped calves (bandages)
            wrap_pts = [
                (lx - 3 + sw, ly + 6), (lx + 3 + sw, ly + 6),
                (lx + 3 + sw, ly + 14), (lx - 3 + sw, ly + 14),
            ]
            _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["wrap_dark"], wrap_pts)
            _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["wrap_mid"], [
                (lx - 2 + sw, ly + 7), (lx + 2 + sw, ly + 7),
                (lx + 2 + sw, ly + 13), (lx - 2 + sw, ly + 13),
            ])
            # Wrap bands (horizontal lines)
            for wy in (ly + 8, ly + 10, ly + 12):
                pygame.draw.line(surface, _NS_kaoruken.PALETTE["wrap_light"],
                                 (lx - 3 + sw, wy),
                                 (lx + 3 + sw, wy), 1)
            # Sandals (ninja tabi)
            _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["pants_darkest"], [
                (lx - 3 + sw, ly + 13), (lx + 3 + sw, ly + 13),
                (lx + 4 + sw + facing, ly + 16),
                (lx - 2 + sw + facing, ly + 16),
            ])
            _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["pants_dark"], [
                (lx - 2 + sw, ly + 14), (lx + 2 + sw, ly + 14),
                (lx + 3 + sw + facing, ly + 15),
            ])
            pygame.draw.rect(surface, _NS_kaoruken.PALETTE["pants_light"],
                             (lx + sw, ly + 14, 1, 1))

    # ── TORSO (cream robe) ───────────────────────────────────
    def _draw_torso(surface, cx, cy, facing, phase):
        body = [
            (cx - 10, cy - 10), (cx - 6, cy - 13),
            (cx + 6, cy - 13), (cx + 10, cy - 10),
            (cx + 11, cy), (cx + 10, cy + 10),
            (cx + 6, cy + 14), (cx - 6, cy + 14),
            (cx - 10, cy + 10), (cx - 11, cy),
        ]
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["shadow_deep"],
                           [(p[0] + 2, p[1] + 2) for p in body])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["robe_darkest"], body)
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["robe_dark"], [
            (cx - 9, cy - 9), (cx - 5, cy - 12),
            (cx + 5, cy - 12), (cx + 9, cy - 9),
            (cx + 10, cy), (cx + 9, cy + 9),
            (cx + 5, cy + 13), (cx - 5, cy + 13),
            (cx - 9, cy + 9), (cx - 10, cy),
        ])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["robe_mid"], [
            (cx - 7, cy - 7), (cx - 3, cy - 10),
            (cx + 3, cy - 10), (cx + 7, cy - 7),
            (cx + 8, cy), (cx + 7, cy + 6),
            (cx + 3, cy + 10), (cx - 3, cy + 10),
            (cx - 7, cy + 6), (cx - 8, cy),
        ])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["robe_light"], [
            (cx - 5, cy - 5), (cx - 2, cy - 8),
            (cx + 2, cy - 8), (cx + 5, cy - 5),
            (cx + 6, cy), (cx + 5, cy + 4),
            (cx + 2, cy + 8), (cx - 2, cy + 8),
            (cx - 5, cy + 4), (cx - 6, cy),
        ])
        # Shine highlight
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["robe_shine"],
                         (cx - 2, cy - 6, 3, 2))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["robe_shine"],
                         (cx - 3, cy - 3, 2, 1))
        # V-collar (crossed opening, darker inside)
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["robe_darkest"], [
            (cx - 4, cy - 12), (cx, cy - 6),
            (cx + 4, cy - 12), (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["robe_dark"], [
            (cx - 3, cy - 11), (cx, cy - 6),
            (cx + 3, cy - 11), (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        # Collar edge (darker line)
        pygame.draw.line(surface, _NS_kaoruken.PALETTE["robe_darkest"],
                         (cx - 4, cy - 12), (cx, cy - 6), 1)
        pygame.draw.line(surface, _NS_kaoruken.PALETTE["robe_darkest"],
                         (cx + 4, cy - 12), (cx, cy - 6), 1)
        # Waist wrap (dark cloth/sash)
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["pants_darkest"],
                         (cx - 11, cy + 9, 22, 5))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["pants_dark"],
                         (cx - 10, cy + 10, 20, 3))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["pants_mid"],
                         (cx - 10, cy + 10, 20, 1))
        # Sash knot (small)
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["pants_darkest"],
                         (cx - 2, cy + 9, 4, 6))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["pants_dark"],
                         (cx - 1, cy + 10, 2, 4))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["pants_light"],
                         (cx - 1, cy + 10, 1, 1))
        # Hyuga clan symbol (small circle/triangle emblem on chest)
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["chakra_darkest"],
                         (cx - 1, cy, 3, 3))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["chakra_dark"],
                         (cx, cy, 2, 2))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["chakra_mid"],
                         (cx, cy, 1, 1))

    # ── BACK ARM ─────────────────────────────────────────────
    def _draw_back_arm(surface, cx, cy, facing, phase, action, progress):
        back = -facing
        sx = cx + back * 9
        sy = cy - 8
        sway = math.sin(phase * 0.7) * 2
        # In Neji's pose the back arm is often pulled back/coiled
        # Back arm slightly bent
        ex = sx + back * 3
        ey = sy + 8 + int(sway)
        hx = ex + int(math.cos(-math.pi / 3) * 6) * back
        hy = ey + int(math.sin(-math.pi / 3) * 6)
        # Upper arm (robe sleeve)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["shadow_deep"],
                             (sx + 1, sy + 2), (ex + 1, ey + 2), 8)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["robe_darkest"],
                             (sx, sy), (ex, ey), 7)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["robe_dark"],
                             (sx, sy), (ex, ey), 5)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["robe_mid"],
                             (sx, sy - 1), (ex, ey - 1), 3)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["robe_light"],
                             (sx, sy - 2), (ex, ey - 2), 1)
        # Sleeve end line
        pygame.draw.line(surface, _NS_kaoruken.PALETTE["robe_darkest"],
                         (ex - 3, ey + 1), (ex + 3, ey + 1), 1)
        # Forearm (wrapped bandages)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["shadow_deep"],
                             (ex + 1, ey + 2), (hx + 1, hy + 2), 6)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["wrap_dark"],
                             (ex, ey), (hx, hy), 5)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["wrap_mid"],
                             (ex, ey), (hx, hy), 3)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["wrap_light"],
                             (ex, ey - 1), (hx, hy - 1), 1)
        # Wrap bands
        for i in range(3):
            t = (i + 1) / 4
            bx = int(ex + (hx - ex) * t)
            by = int(ey + (hy - ey) * t)
            pygame.draw.line(surface, _NS_kaoruken.PALETTE["wrap_dark"],
                             (bx - 2, by), (bx + 2, by), 1)
        # Fist (back hand)
        _NS_kaoruken._aacircle(surface, _NS_kaoruken.PALETTE["shadow_deep"],
                               (hx + 1, hy + 1), 4)
        _NS_kaoruken._aacircle(surface, _NS_kaoruken.PALETTE["skin_darkest"],
                               (hx, hy), 4)
        _NS_kaoruken._aacircle(surface, _NS_kaoruken.PALETTE["skin_dark"],
                               (hx, hy), 3)
        _NS_kaoruken._aacircle(surface, _NS_kaoruken.PALETTE["skin_mid"],
                               (hx - 1, hy - 1), 2)
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["skin_light"],
                         (hx - 1, hy - 1, 1, 1))
        # Chakra glow on knuckles (subtle)
        for r in range(4, 0, -1):
            a = _NS_kaoruken._alpha(80 * (4 - r) / 4)
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_mid"], a),
                                   (hx, hy), r)

    # ── FRONT ARM + OPEN PALM ────────────────────────────────
    def _draw_front_arm_palm(surface, cx, cy, facing, phase, action, progress):
        # Front arm is extended forward for palm strike
        base_angle = 0  # horizontal palm strike
        if action == "attack":
            if progress < 0.3:
                t = progress / 0.3
                # Pull back
                base_angle = -math.pi / 4 - t * math.pi / 6
            elif progress < 0.55:
                t = (progress - 0.3) / 0.25
                # Thrust forward
                base_angle = -math.pi / 4 - math.pi / 6 + t * math.pi / 3
            else:
                t = (progress - 0.55) / 0.45
                # Recovery
                base_angle = -math.pi / 12 + (1 - t) * 0.15
        else:
            base_angle = -math.pi / 12 + math.sin(phase * 0.5) * 0.08

        sx = cx + facing * 10
        sy = cy - 8
        arm_len = 20
        # Extended hand position
        hx = sx + int(math.cos(base_angle) * arm_len) * facing
        hy = sy + int(math.sin(base_angle) * arm_len)
        ex = sx + int(math.cos(base_angle) * arm_len * 0.5) * facing
        ey = sy + int(math.sin(base_angle) * arm_len * 0.5) + 2

        # Upper arm (robe sleeve — WIDE)
        sleeve_end_perp = base_angle + math.pi / 2
        sleeve_a_x = ex + int(math.cos(sleeve_end_perp) * 5)
        sleeve_a_y = ey + int(math.sin(sleeve_end_perp) * 5)
        sleeve_b_x = ex - int(math.cos(sleeve_end_perp) * 5)
        sleeve_b_y = ey - int(math.sin(sleeve_end_perp) * 5)
        sleeve_pts = [
            (sx - 3, sy), (sx + 3, sy),
            (sleeve_a_x, sleeve_a_y),
            (sleeve_b_x, sleeve_b_y),
        ]
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in sleeve_pts])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["robe_darkest"], sleeve_pts)
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["robe_dark"], [
            (sx - 2, sy + 1), (sx + 2, sy + 1),
            (int((sleeve_a_x + ex) / 2), int((sleeve_a_y + ey) / 2)),
            (int((sleeve_b_x + ex) / 2), int((sleeve_b_y + ey) / 2)),
        ])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["robe_mid"], [
            (sx - 1, sy + 2), (sx + 1, sy + 2),
            (ex, ey - 1), (ex, ey + 1),
        ])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["robe_light"], [
            (sx, sy + 3), (sx, sy + 3),
            (ex, ey), (ex, ey),
        ])
        # Sleeve edge (darker line)
        pygame.draw.line(surface, _NS_kaoruken.PALETTE["robe_darkest"],
                         (sleeve_a_x, sleeve_a_y),
                         (sleeve_b_x, sleeve_b_y), 1)
        # Forearm (skin + wraps)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["shadow_deep"],
                             (ex + 1, ey + 2), (hx + 1, hy + 2), 6)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["skin_darkest"],
                             (ex, ey), (hx, hy), 5)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["skin_dark"],
                             (ex, ey), (hx, hy), 4)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["skin_mid"],
                             (ex, ey - 1), (hx, hy - 1), 2)
        _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["skin_light"],
                             (ex, ey - 2), (hx, hy - 2), 1)
        # Wrist wrap
        wrist_off_x = int(math.cos(base_angle) * -3) * facing
        wrist_off_y = int(math.sin(base_angle) * -3)
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["wrap_dark"],
                         (hx + wrist_off_x - 2, hy + wrist_off_y - 2, 5, 4))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["wrap_mid"],
                         (hx + wrist_off_x - 2, hy + wrist_off_y - 1, 5, 2))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["wrap_light"],
                         (hx + wrist_off_x - 2, hy + wrist_off_y - 1, 5, 1))

        # OPEN PALM (5 fingers)
        _NS_kaoruken._draw_open_palm(surface, hx, hy, facing, phase,
                                      base_angle, action)

    def _draw_open_palm(surface, hx, hy, facing, phase, arm_angle, action):
        """Open palm with fingers spread — Gentle Fist signature."""
        # Palm base (rectangle-ish shape extending from wrist)
        palm_dx = int(math.cos(arm_angle) * 4) * facing
        palm_dy = int(math.sin(arm_angle) * 4)
        palm_cx = hx + palm_dx
        palm_cy = hy + palm_dy

        # Palm poly
        perp = arm_angle + math.pi / 2
        palm_w = 3
        p1_x = palm_cx + int(math.cos(perp) * palm_w)
        p1_y = palm_cy + int(math.sin(perp) * palm_w)
        p2_x = palm_cx - int(math.cos(perp) * palm_w)
        p2_y = palm_cy - int(math.sin(perp) * palm_w)
        # Palm shape (from wrist to base of fingers)
        palm_pts = [
            (hx + int(math.cos(perp) * (palm_w - 1)),
             hy + int(math.sin(perp) * (palm_w - 1))),
            (p1_x, p1_y),
            (p2_x, p2_y),
            (hx - int(math.cos(perp) * (palm_w - 1)),
             hy - int(math.sin(perp) * (palm_w - 1))),
        ]
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 1) for p in palm_pts])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["skin_darkest"], palm_pts)
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["skin_dark"], [
            (hx + int(math.cos(perp) * (palm_w - 1)),
             hy + int(math.sin(perp) * (palm_w - 1))),
            (int((p1_x + palm_cx) / 2), int((p1_y + palm_cy) / 2)),
            (int((p2_x + palm_cx) / 2), int((p2_y + palm_cy) / 2)),
            (hx - int(math.cos(perp) * (palm_w - 1)),
             hy - int(math.sin(perp) * (palm_w - 1))),
        ])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["skin_mid"], [
            (hx, hy),
            (palm_cx, palm_cy),
        ])
        # Palm shine
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["skin_light"],
                         (palm_cx - 1, palm_cy - 1, 1, 1))

        # 5 FINGERS (spread out from palm base)
        finger_spread = math.pi / 5  # angle between fingers
        finger_base_ang = arm_angle
        finger_len = 4
        for f_i in range(5):
            f_ang_off = (f_i - 2) * (finger_spread / 5)
            # Thumb (index 0) is shorter and at wider angle
            if f_i == 0:
                f_ang = finger_base_ang - math.pi / 4 * facing
                f_len = 3
            elif f_i == 4:
                f_ang = finger_base_ang + math.pi / 5 * facing
                f_len = 3
            else:
                f_ang = finger_base_ang + f_ang_off * facing
                f_len = finger_len + (f_i == 2)  # middle finger longest
            f_tip_x = palm_cx + int(math.cos(f_ang) * f_len) * facing
            f_tip_y = palm_cy + int(math.sin(f_ang) * f_len)
            # Finger line
            _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["shadow_deep"],
                                 (palm_cx + 1, palm_cy + 1),
                                 (f_tip_x + 1, f_tip_y + 1), 2)
            _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["skin_darkest"],
                                 (palm_cx, palm_cy), (f_tip_x, f_tip_y), 2)
            _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["skin_dark"],
                                 (palm_cx, palm_cy), (f_tip_x, f_tip_y), 1)
            pygame.draw.rect(surface, _NS_kaoruken.PALETTE["skin_mid"],
                             (f_tip_x, f_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_kaoruken.PALETTE["skin_light"],
                             (f_tip_x, f_tip_y, 1, 1))

        # CHAKRA GLOW on palm (signature Gentle Fist)
        pulse_intensity = math.sin(phase * 2) * 0.4 + 0.6
        if action == "attack":
            pulse_intensity = 1.0
        for r in range(7, 0, -1):
            a = _NS_kaoruken._alpha(160 * (7 - r) / 7 * pulse_intensity)
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_mid"], a),
                                   (palm_cx, palm_cy), r)
        _NS_kaoruken._aacircle(surface,
                               _NS_kaoruken.PALETTE["chakra_hot"],
                               (palm_cx, palm_cy), 2)
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["chakra_shine"],
                         (palm_cx, palm_cy, 1, 1))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["white"],
                         (palm_cx, palm_cy, 1, 1))

    # ── HEAD ─────────────────────────────────────────────────
    def _draw_head(surface, cx, cy, facing, phase):
        hx = cx + facing * 2
        hy = cy - 20
        head_pts = [
            (hx - 7, hy + 5), (hx - 8, hy - 1), (hx - 6, hy - 7),
            (hx - 1, hy - 9), (hx + 4, hy - 9), (hx + 7, hy - 6),
            (hx + 8, hy), (hx + 7, hy + 5), (hx + 4, hy + 7),
            (hx - 1, hy + 7), (hx - 5, hy + 6),
        ]
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["shadow_deep"],
                           [(p[0] + 1, p[1] + 2) for p in head_pts])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["skin_darkest"], head_pts)
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["skin_dark"], [
            (hx - 6, hy + 4), (hx - 7, hy), (hx - 5, hy - 6),
            (hx, hy - 8), (hx + 3, hy - 8), (hx + 6, hy - 5),
            (hx + 7, hy), (hx + 6, hy + 4), (hx + 3, hy + 6),
            (hx, hy + 6), (hx - 4, hy + 5),
        ])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["skin_mid"], [
            (hx - 5, hy - 3), (hx - 3, hy - 6),
            (hx + 2, hy - 6), (hx + 5, hy - 3),
            (hx + 6, hy), (hx + 4, hy + 3),
            (hx - 1, hy + 3), (hx - 5, hy),
        ])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["skin_light"], [
            (hx - 2, hy - 5), (hx + 2, hy - 5),
            (hx + 3, hy - 3), (hx - 3, hy - 3),
        ])
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["skin_shine"],
                         (hx, hy - 5, 2, 1))
        # Nose (small)
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["skin_darkest"],
                         (hx + facing * 1, hy - 1, 1, 3))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["skin_dark"],
                         (hx + facing * 2, hy + 1, 1, 1))
        # Mouth (serious line)
        pygame.draw.line(surface, _NS_kaoruken.PALETTE["skin_darkest"],
                         (hx + facing * 1, hy + 4),
                         (hx + facing * 4, hy + 4), 1)
        # Ear
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["skin_darkest"],
                         (hx - facing * 7, hy, 2, 3))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["skin_dark"],
                         (hx - facing * 7, hy + 1, 1, 2))

        # BYAKUGAN EYES (pale white-lavender, no visible pupil, veins around)
        _NS_kaoruken._draw_byakugan_eye(surface, hx + facing * 3, hy - 2,
                                         facing, phase)
        _NS_kaoruken._draw_byakugan_eye(surface, hx - facing * 2, hy - 1,
                                         facing, phase, small=True)

    def _draw_byakugan_eye(surface, ex, ey, facing, phase, small=False):
        """Pale white byakugan eye with faint lavender vein around."""
        pulse = math.sin(phase * 2) * 0.15 + 0.85
        w = 3 if small else 4
        h = 2 if small else 3
        # Socket (darker outline)
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["shadow_deep"],
                         (ex - w // 2, ey - 1, w, h))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["eye_socket"],
                         (ex - w // 2 + 1, ey - 1, w - 1, h))
        # Byakugan pale glow
        for r in range(4 if not small else 3, 0, -1):
            a = _NS_kaoruken._alpha(90 * (4 - r) / 4 * pulse)
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["eye_mid"], a),
                                   (ex, ey), r)
        # Iris — pale white with no visible pupil
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["eye_dark"],
                         (ex - w // 2 + 1, ey - 1, w - 1, h))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["eye_mid"],
                         (ex - w // 2 + 1, ey, w - 1, 1))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["eye_light"],
                         (ex, ey, w - 2, 1))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["eye_glow"],
                         (ex + 1, ey, 1, 1))
        # No visible pupil — just faint hint
        # Vein marks around eye (only for main eye, subtle)
        if not small:
            # Small vein lines outward
            for v_i in range(3):
                v_ang = (v_i - 1) * 0.6 + math.pi
                vx1 = ex + int(math.cos(v_ang) * (w // 2 + 1))
                vy1 = ey + int(math.sin(v_ang) * 2)
                vx2 = ex + int(math.cos(v_ang) * (w // 2 + 3))
                vy2 = ey + int(math.sin(v_ang) * 3)
                pygame.draw.line(surface, _NS_kaoruken.PALETTE["eye_vein"],
                                 (vx1, vy1), (vx2, vy2), 1)

    # ── HAIR (long straight dark) ────────────────────────────
    def _draw_hair_back(surface, cx, cy, facing, phase):
        """Long straight dark hair flowing down back."""
        hx = cx + facing * 2
        hy = cy - 20
        # Neji's hair is long and mostly straight, tied loose at top
        strands = [
            (-5, -6, 0.0, 32, 5),
            (-3, -8, 0.3, 36, 6),
            (-1, -9, 0.6, 38, 6),
            (1, -9, 0.9, 37, 6),
            (3, -8, 1.2, 34, 5),
            (5, -6, 1.5, 30, 4),
            (-6, -3, 0.4, 28, 4),
            (6, -3, 1.6, 26, 4),
            (-4, -1, 0.8, 32, 5),
            (4, -1, 1.8, 30, 4),
        ]
        for (ox, oy, ph_off, length, base_w) in strands:
            pts = []
            seg = 9
            for j in range(seg + 1):
                t = j / seg
                sx = hx + ox - int(facing * t * length * 0.3)
                sy = hy + oy + int(t * length * 0.9)
                # Subtle wave
                wave = math.sin(phase * 0.8 + ph_off + t * math.pi * 1.4)
                sx += int(wave * (1 + t * 4)) * (-facing)
                sy += int(math.sin(phase * 0.5 + ph_off + t) * 1)
                pts.append((sx, sy))
            for j in range(len(pts) - 1):
                thick = max(1, base_w - j // 2)
                _NS_kaoruken._aaline(surface,
                                     _NS_kaoruken.PALETTE["shadow_deep"],
                                     (pts[j][0] + 1, pts[j][1] + 1),
                                     (pts[j + 1][0] + 1, pts[j + 1][1] + 1),
                                     thick + 1)
                _NS_kaoruken._aaline(surface,
                                     _NS_kaoruken.PALETTE["hair_darkest"],
                                     pts[j], pts[j + 1], thick)
                _NS_kaoruken._aaline(surface,
                                     _NS_kaoruken.PALETTE["hair_dark"],
                                     pts[j], pts[j + 1], max(1, thick - 1))
                if thick > 2:
                    _NS_kaoruken._aaline(surface,
                                         _NS_kaoruken.PALETTE["hair_mid"],
                                         (pts[j][0], pts[j][1] - 1),
                                         (pts[j + 1][0], pts[j + 1][1] - 1),
                                         max(1, thick - 3))
                if thick > 4:
                    _NS_kaoruken._aaline(surface,
                                         _NS_kaoruken.PALETTE["hair_light"],
                                         (pts[j][0], pts[j][1] - 2),
                                         (pts[j + 1][0], pts[j + 1][1] - 2),
                                         1)

    def _draw_hair_front(surface, cx, cy, facing, phase):
        """Front bangs — parted center."""
        hx = cx + facing * 2
        hy = cy - 20
        bangs = [
            (-4, -7, 0.0, 6),
            (-2, -8, 0.3, 7),
            (2, -8, 0.6, 7),
            (4, -7, 0.9, 6),
            (-6, -5, 1.2, 5),
            (6, -5, 1.5, 5),
        ]
        for (ox, oy, ph_off, length) in bangs:
            bx = hx + ox
            by = hy + oy
            sway = math.sin(phase * 0.6 + ph_off) * 0.8
            tip_x = bx + int(sway)
            tip_y = by + length
            _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["hair_darkest"],
                                 (bx, by), (tip_x, tip_y), 3)
            _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["hair_dark"],
                                 (bx, by), (tip_x, tip_y), 2)
            _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["hair_mid"],
                                 (bx, by - 1), (tip_x, tip_y - 1), 1)
            pygame.draw.rect(surface, _NS_kaoruken.PALETTE["hair_light"],
                             (tip_x, tip_y, 1, 1))

    # ── HEADBAND ─────────────────────────────────────────────
    def _draw_headband(surface, cx, cy, facing, phase):
        hx = cx + facing * 2
        hy = cy - 20
        band_y = hy - 5
        # Cloth wrap
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["pants_darkest"],
                         (hx - 7, band_y, 15, 3))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["pants_dark"],
                         (hx - 7, band_y + 1, 15, 1))
        # Metal plate (center forehead)
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["metal_dark"],
                         (hx - 3, band_y, 6, 3))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["metal_mid"],
                         (hx - 3, band_y, 6, 2))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["metal_light"],
                         (hx - 3, band_y, 6, 1))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["metal_shine"],
                         (hx - 2, band_y, 3, 1))
        # Chakra circle symbol
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["chakra_darkest"],
                         (hx - 1, band_y + 1, 3, 1))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["chakra_mid"],
                         (hx, band_y + 1, 1, 1))
        # Headband ties trailing back
        back = -facing
        for tie_i in range(2):
            tie_y_off = tie_i * 2
            tie_start_x = hx + back * 7
            tie_start_y = band_y + 1 + tie_y_off
            tie_end_x = tie_start_x + back * (5 + tie_i * 2)
            tie_end_y = tie_start_y + 3 + tie_i * 2 \
                        + int(math.sin(phase * 0.8 + tie_i) * 2)
            _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["pants_darkest"],
                                 (tie_start_x, tie_start_y),
                                 (tie_end_x, tie_end_y), 2)
            _NS_kaoruken._aaline(surface, _NS_kaoruken.PALETTE["pants_dark"],
                                 (tie_start_x, tie_start_y),
                                 (tie_end_x, tie_end_y), 1)

    # ============================================================
    # BASIC ATTACK — PALM THRUST TRAIL + IMPACT
    # ============================================================
    def _get_palm_position(cx, cy, facing, progress):
        """Position of open palm at given attack progress."""
        if progress < 0.3:
            t = progress / 0.3
            angle = -math.pi / 4 - t * math.pi / 6
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            angle = -math.pi / 4 - math.pi / 6 + t * math.pi / 3
        else:
            t = (progress - 0.55) / 0.45
            angle = -math.pi / 12 + (1 - t) * 0.15
        sx = cx + facing * 10
        sy = cy - 8
        arm_len = 20
        hx = sx + int(math.cos(angle) * arm_len) * facing
        hy = sy + int(math.sin(angle) * arm_len)
        # Palm slightly forward of hand
        palm_x = hx + int(math.cos(angle) * 4) * facing
        palm_y = hy + int(math.sin(angle) * 4)
        return palm_x, palm_y, angle

    def _draw_palm_thrust_trail(surface, boss, cx, cy, facing, progress):
        """Straight chakra thrust trail (not swinging arc — punching thrust)."""
        if progress < 0.28 or progress > 0.7:
            return
        if progress < 0.32:
            intensity = (progress - 0.28) / 0.04
        elif progress < 0.55:
            intensity = 1.0
        else:
            intensity = max(0, 1 - (progress - 0.55) / 0.15)
        intensity = max(0.0, min(1.0, intensity))
        if intensity <= 0:
            return
        # Sample past positions of palm
        num = 10
        trail = []
        for i in range(num):
            sp = progress - (i / num) * 0.2
            if sp < 0.28:
                continue
            px, py, ang = _NS_kaoruken._get_palm_position(cx, cy, facing, sp)
            trail.append((px, py, ang, i))
        if len(trail) < 2:
            return
        trail.reverse()
        ts = pygame.Surface((300, 200), pygame.SRCALPHA)
        ox = cx - 150
        oy = cy - 100
        # Chakra streak lines (parallel, thrust style)
        layers = [
            (_NS_kaoruken.PALETTE["chakra_darkest"], 10, 100),
            (_NS_kaoruken.PALETTE["chakra_dark"], 7, 150),
            (_NS_kaoruken.PALETTE["chakra_mid"], 4, 210),
            (_NS_kaoruken.PALETTE["chakra_light"], 2, 240),
            (_NS_kaoruken.PALETTE["chakra_shine"], 1, 255),
        ]
        for color, max_w, max_a in layers:
            for i in range(len(trail) - 1):
                p1, p2 = trail[i], trail[i + 1]
                fade = 1.0 - (p1[3] / num)
                a = _NS_kaoruken._alpha(max_a * fade * intensity)
                w = max(1, int(max_w * fade))
                if a > 0:
                    pygame.draw.line(
                        ts, (*color, a),
                        (p1[0] - ox, p1[1] - oy),
                        (p2[0] - ox, p2[1] - oy), w,
                    )
        # Streaking chakra lines emanating forward (Gentle Fist "pressure waves")
        if trail:
            lead = trail[0]
            for line_i in range(5):
                line_off = (line_i - 2) * 4
                perp = lead[2] + math.pi / 2
                start_x = lead[0] + int(math.cos(perp) * line_off) - ox
                start_y = lead[1] + int(math.sin(perp) * line_off) - oy
                end_x = start_x + int(math.cos(lead[2]) * 20) * facing
                end_y = start_y + int(math.sin(lead[2]) * 20)
                for w, color, wa in [
                    (2, _NS_kaoruken.PALETTE["chakra_dark"], 180),
                    (1, _NS_kaoruken.PALETTE["chakra_light"], 240),
                ]:
                    la = _NS_kaoruken._alpha(wa * intensity)
                    pygame.draw.line(ts, (*color, la),
                                     (start_x, start_y), (end_x, end_y), w)
                pygame.draw.rect(ts,
                                 (*_NS_kaoruken.PALETTE["chakra_hot"],
                                  _NS_kaoruken._alpha(255 * intensity)),
                                 (end_x, end_y, 2, 2))
        surface.blit(ts, (ox, oy))
        # Leading edge glow
        if trail:
            lead = trail[0]
            for r in range(12, 2, -2):
                a = _NS_kaoruken._alpha(180 * (12 - r) / 12 * intensity)
                _NS_kaoruken._aacircle(
                    surface, (*_NS_kaoruken.PALETTE["chakra_mid"], a),
                    (lead[0], lead[1]), r,
                )
            _NS_kaoruken._aacircle(surface, _NS_kaoruken.PALETTE["chakra_hot"],
                                   (lead[0], lead[1]), 4)
            _NS_kaoruken._aacircle(surface, _NS_kaoruken.PALETTE["chakra_shine"],
                                   (lead[0], lead[1]), 2)
            pygame.draw.rect(surface, _NS_kaoruken.PALETTE["white"],
                             (lead[0], lead[1], 1, 1))

    def _draw_palm_hit_impact(surface, boss, cx, cy, facing, progress):
        if progress < 0.5 or progress > 0.7:
            return
        t = (progress - 0.5) / 0.2
        inten = math.sin(t * math.pi)
        px, py, ang = _NS_kaoruken._get_palm_position(cx, cy, facing, progress)
        ix = px + facing * 8
        iy = py
        r = int(6 + t * 14)
        a = _NS_kaoruken._alpha(255 * inten)
        # Central chakra burst
        for rr in range(r + 4, 0, -2):
            ra = _NS_kaoruken._alpha(a * (r + 4 - rr) / (r + 4))
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_darkest"], ra),
                                   (ix, iy), rr)
        _NS_kaoruken._aacircle(surface,
                               (*_NS_kaoruken.PALETTE["chakra_dark"], a),
                               (ix, iy), max(2, r - 3))
        _NS_kaoruken._aacircle(surface,
                               (*_NS_kaoruken.PALETTE["chakra_mid"], a),
                               (ix, iy), max(1, r - 6))
        _NS_kaoruken._aacircle(surface,
                               (*_NS_kaoruken.PALETTE["chakra_light"], a),
                               (ix, iy), max(1, r - 9))
        _NS_kaoruken._aacircle(surface,
                               (*_NS_kaoruken.PALETTE["chakra_hot"], a),
                               (ix, iy), max(1, r - 12))
        pygame.draw.rect(surface, (*_NS_kaoruken.PALETTE["white"], a),
                         (ix, iy, 1, 1))
        # Chakra shockwave rings
        wave_r = int(r * (1.3 + t * 0.5))
        wave_a = _NS_kaoruken._alpha(200 * (1 - t))
        _NS_kaoruken._aacircle(surface,
                               (*_NS_kaoruken.PALETTE["chakra_light"], wave_a),
                               (ix, iy), wave_r, 2)
        _NS_kaoruken._aacircle(surface,
                               (*_NS_kaoruken.PALETTE["chakra_hot"], wave_a),
                               (ix, iy), max(1, wave_r - 1), 1)
        # Radial chakra spikes (star)
        for i in range(8):
            sang = i * math.pi / 4 + progress * 2
            spike_len = int(r * 1.5)
            ex = ix + int(math.cos(sang) * spike_len)
            ey = iy + int(math.sin(sang) * spike_len)
            for w, color, wa in [
                (3, _NS_kaoruken.PALETTE["chakra_dark"], 200),
                (2, _NS_kaoruken.PALETTE["chakra_mid"], 240),
                (1, _NS_kaoruken.PALETTE["chakra_hot"], 255),
            ]:
                la = _NS_kaoruken._alpha(wa * inten)
                pygame.draw.line(surface, (*color, la),
                                 (ix, iy), (ex, ey), w)
            pygame.draw.rect(surface,
                             (*_NS_kaoruken.PALETTE["white"], a),
                             (ex, ey, 2, 2))
        # Sparks flying outward
        for i in range(10):
            sang = i * math.pi / 5 + progress * 3
            dist = int(r * 1.3)
            ex = ix + int(math.cos(sang) * dist)
            ey = iy + int(math.sin(sang) * dist)
            pygame.draw.rect(surface,
                             (*_NS_kaoruken.PALETTE["chakra_hot"], a),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_kaoruken.PALETTE["white"], a),
                             (ex, ey, 1, 1))

    # ============================================================
    # AMBIENT / FLOATING FX
    # ============================================================
    def _draw_shadow(surface, x, y):
        sh = pygame.Surface((130, 26), pygame.SRCALPHA)
        for r in range(13, 0, -1):
            a = max(0, (13 - r) * 17)
            pygame.draw.ellipse(sh, (0, 0, 0, a),
                                (10 - r, 13 - r, 110 + r * 2, r * 2))
        pygame.draw.ellipse(sh, (5, 10, 15, 170), (8, 7, 114, 12))
        surface.blit(sh, (x - 65, y - 13))

    def _draw_chakra_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for r in range(85, 5, -5):
            a = _NS_kaoruken._alpha((85 - r) * 1.0 * pulse)
            if a > 0:
                _NS_kaoruken._aacircle(aura,
                                       (*_NS_kaoruken.PALETTE["chakra_darkest"], a),
                                       (110, 90), r)
        for r in range(50, 5, -3):
            a = _NS_kaoruken._alpha((50 - r) * 1.3 * pulse)
            if a > 0:
                _NS_kaoruken._aacircle(aura,
                                       (*_NS_kaoruken.PALETTE["chakra_dark"], a),
                                       (110, 90), r)
        surface.blit(aura, (x - 110, y - 90))
        # Floating chakra sparks
        for i in range(10):
            ang = phase * 0.3 + i * math.pi / 5
            rd = 40 + int(math.sin(phase + i) * 12)
            sx = x + int(math.cos(ang) * rd)
            sy = y - 5 + int(math.sin(ang) * rd * 0.45)
            pygame.draw.rect(surface, _NS_kaoruken.PALETTE["chakra_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kaoruken.PALETTE["chakra_hot"],
                             (sx, sy, 1, 1))

    def _draw_float_wisps(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((140, 34), pygame.SRCALPHA)
        p = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(22, 3, -2):
            a = _NS_kaoruken._alpha((22 - r) * 3 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kaoruken.PALETTE["chakra_darkest"], a),
                    (70 - r * 2, 17 - r // 3, r * 4, max(3, r // 2)),
                )
        for r in range(14, 3, -2):
            a = _NS_kaoruken._alpha((14 - r) * 4 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kaoruken.PALETTE["chakra_dark"], a),
                    (70 - r, 17 - r // 4, r * 2, max(2, r // 3)),
                )
        surface.blit(mist, (cx - 70, cy - 10))
        for i in range(6):
            t = (phase * 0.5 + i * 0.16) % 1.0
            sx = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            sy = cy - int(t * 18)
            a = _NS_kaoruken._alpha(200 * (1 - t) * strength)
            if a > 0:
                _NS_kaoruken._aacircle(surface,
                                       (*_NS_kaoruken.PALETTE["chakra_dark"], a),
                                       (sx, sy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_kaoruken.PALETTE["chakra_mid"], a),
                                 (sx, sy, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_kaoruken.PALETTE["chakra_hot"], a),
                                 (sx, sy, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 10 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                a = _NS_kaoruken._alpha(140 - i * 25)
                if a > 0:
                    _NS_kaoruken._aacircle(
                        surface, (*_NS_kaoruken.PALETTE["chakra_dark"], a),
                        (sx, sy), max(2, 5 - i),
                    )

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((170, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kaoruken.PALETTE["chakra_darkest"], 180),
                            (5, 14, 160, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_kaoruken.PALETTE["chakra_dark"], 210),
                            (15, 16, 140, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_kaoruken.PALETTE["chakra_mid"], 190),
                            (25, 18, 120, 16), 1)
        for i in range(8):
            ang = phase * 0.3 + i * math.pi / 4
            x1 = 85 + int(math.cos(ang) * 45)
            y1 = 25 + int(math.sin(ang) * 8)
            x2 = 85 + int(math.cos(ang) * 72)
            y2 = 25 + int(math.sin(ang) * 12)
            pygame.draw.line(ring, (*_NS_kaoruken.PALETTE["chakra_light"], 200),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(
                ring, (*_NS_kaoruken.PALETTE["chakra_hot"],
                       _NS_kaoruken._alpha(150 * pulse)),
                (10, 8, 150, 32), 1,
            )
        surface.blit(ring, (x - 85, y - 23))

    # ============================================================
    # SKILL Q — GENTLE FIST: 8 TRIGRAMS PALMS (series of thrusts)
    # ============================================================
    def _draw_gentle_fist(surface, boss, x, y, timer, phase):
        """Rapid series of chakra thrust strikes toward target."""
        facing = boss.direction
        duration = 55
        progress = 1 - timer / duration
        progress = max(0.0, min(1.0, progress))
        tx, ty = _NS_kaoruken._target_position(boss, x, y)
        if progress < 0.1:
            return
        t = (progress - 0.1) / 0.9
        # 8 rapid strikes (like 2, 4, 8, 16, 32 palms sequence)
        num_strikes = 8
        start_x = x + facing * 30
        start_y = y - 5
        for st_i in range(num_strikes):
            st_seed = st_i * 0.12
            st_t = t - st_seed
            if st_t < 0 or st_t > 0.3:
                continue
            fade = math.sin(st_t / 0.3 * math.pi)
            # Position of each thrust — spaced along line to target
            travel_t = st_i / max(1, num_strikes - 1)
            px = int(start_x + (tx - start_x) * travel_t)
            py = int(start_y + (ty - start_y) * travel_t) \
                 + int((st_i % 2 - 0.5) * 8)
            # Strike burst
            r = int(6 + fade * 8)
            a = _NS_kaoruken._alpha(255 * fade)
            for rr in range(r + 3, 0, -1):
                ra = _NS_kaoruken._alpha(a * (r + 3 - rr) / (r + 3))
                _NS_kaoruken._aacircle(surface,
                                       (*_NS_kaoruken.PALETTE["chakra_dark"], ra),
                                       (px, py), rr)
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_mid"], a),
                                   (px, py), max(1, r - 3))
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_hot"], a),
                                   (px, py), max(1, r - 5))
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_shine"], a),
                                   (px, py), max(1, r - 7))
            pygame.draw.rect(surface, (*_NS_kaoruken.PALETTE["white"], a),
                             (px, py, 1, 1))
            # Palm print silhouette (5 dots as fingers)
            for f_i in range(5):
                f_ang = -math.pi / 3 + f_i * math.pi / 6
                fx = px + int(math.cos(f_ang) * r * 0.8) * facing
                fy = py + int(math.sin(f_ang) * r * 0.8)
                pygame.draw.rect(surface,
                                 (*_NS_kaoruken.PALETTE["chakra_hot"], a),
                                 (fx, fy, 1, 1))
                pygame.draw.rect(surface,
                                 (*_NS_kaoruken.PALETTE["white"], a),
                                 (fx, fy, 1, 1))
            # Radial spikes
            for sp_i in range(4):
                sp_ang = sp_i * math.pi / 2 + st_i * 0.3
                ex = px + int(math.cos(sp_ang) * r)
                ey = py + int(math.sin(sp_ang) * r)
                pygame.draw.line(surface,
                                 (*_NS_kaoruken.PALETTE["chakra_light"], a),
                                 (px, py), (ex, ey), 2)

    # ============================================================
    # SKILL W — 8 TRIGRAMS 64 PALMS (AoE around boss)
    # ============================================================
    def _draw_64palms_ground(surface, boss, x, y, timer, phase):
        """Trigram circle on ground under boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 2))
        if r < 5:
            return
        # Trigram octagonal pattern on ground
        for ring_i in range(3):
            ring_r = r - ring_i * 8
            if ring_r < 5:
                continue
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_dark"], 200),
                                   (x, y + 45), ring_r, 2)
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_mid"], 220),
                                   (x, y + 45), ring_r - 1, 1)
        # 8 trigram markers on outer ring
        for i in range(8):
            tang = i * math.pi / 4
            tx1 = x + int(math.cos(tang) * r)
            ty1 = y + 45 + int(math.sin(tang) * r * 0.5)
            # Trigram bars (3 short lines)
            for bar_i in range(3):
                bar_off = (bar_i - 1) * 3
                bar_perp = tang + math.pi / 2
                bx1 = tx1 + int(math.cos(bar_perp) * bar_off)
                by1 = ty1 + int(math.sin(bar_perp) * bar_off * 0.5)
                bx2 = bx1 + int(math.cos(tang) * 5)
                by2 = by1 + int(math.sin(tang) * 5 * 0.5)
                pygame.draw.line(surface,
                                 _NS_kaoruken.PALETTE["chakra_hot"],
                                 (bx1, by1), (bx2, by2), 2)

    def _draw_64palms(surface, boss, x, y, timer, phase):
        """Radial palm strikes in all 8 directions × multiple rings."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r_max = int(70 * min(1.0, progress * 1.5))
        if r_max < 10:
            return
        t = progress
        # Rings of palm strikes expanding outward
        for ring_i in range(4):
            ring_delay = ring_i * 0.12
            ring_t = t - ring_delay
            if ring_t < 0 or ring_t > 0.5:
                continue
            ring_fade = math.sin(ring_t / 0.5 * math.pi)
            ring_r = int(15 + ring_i * 15)
            num_palms = 8 + ring_i * 4
            for p_i in range(num_palms):
                p_ang = p_i * math.pi * 2 / num_palms + ring_i * 0.2
                px = x + int(math.cos(p_ang) * ring_r)
                py = y + int(math.sin(p_ang) * ring_r * 0.75)
                # Palm strike burst
                pr = int(4 + ring_fade * 4)
                a = _NS_kaoruken._alpha(240 * ring_fade)
                for rr in range(pr + 2, 0, -1):
                    ra = _NS_kaoruken._alpha(a * (pr + 2 - rr) / (pr + 2))
                    _NS_kaoruken._aacircle(surface,
                                           (*_NS_kaoruken.PALETTE["chakra_dark"], ra),
                                           (px, py), rr)
                _NS_kaoruken._aacircle(surface,
                                       (*_NS_kaoruken.PALETTE["chakra_mid"], a),
                                       (px, py), max(1, pr - 2))
                _NS_kaoruken._aacircle(surface,
                                       (*_NS_kaoruken.PALETTE["chakra_hot"], a),
                                       (px, py), max(1, pr - 3))
                pygame.draw.rect(surface,
                                 (*_NS_kaoruken.PALETTE["white"], a),
                                 (px, py, 1, 1))
                # Directional line from center
                pygame.draw.line(surface,
                                 (*_NS_kaoruken.PALETTE["chakra_light"], a),
                                 (x + int(math.cos(p_ang) * 10),
                                  y + int(math.sin(p_ang) * 10 * 0.75)),
                                 (px, py), 1)
        # Central chakra pillar
        cp_a = _NS_kaoruken._alpha(200 + math.sin(phase * 4) * 55)
        for r in range(15, 0, -2):
            a = _NS_kaoruken._alpha(cp_a * (15 - r) / 15)
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_mid"], a),
                                   (x, y), r)
        _NS_kaoruken._aacircle(surface,
                               _NS_kaoruken.PALETTE["chakra_hot"],
                               (x, y), 4)
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["white"],
                         (x, y, 1, 1))

    # ============================================================
    # SKILL E — 8 TRIGRAMS PALMS ROTATION (chakra dome around boss)
    # ============================================================
    def _draw_rotation_ground(surface, boss, x, y, timer, phase):
        """Rotating chakra swirl on ground."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 + math.sin(phase * 3) * 5)
        # Multiple rotating rings
        for ring_i in range(3):
            ring_r = r - ring_i * 8
            a = _NS_kaoruken._alpha(200 - ring_i * 40)
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_dark"], a),
                                   (x, y + 45), ring_r, 2)
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_mid"], a),
                                   (x, y + 45), ring_r - 1, 1)
        # Spiral swirl markers
        for i in range(12):
            sang = phase * 3 + i * math.pi / 6
            sx = x + int(math.cos(sang) * r * 0.9)
            sy = y + 45 + int(math.sin(sang) * r * 0.45)
            pygame.draw.rect(surface, _NS_kaoruken.PALETTE["chakra_hot"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kaoruken.PALETTE["white"],
                             (sx, sy, 1, 1))

    def _draw_rotation_overlay(surface, boss, x, y, timer, phase):
        """Spinning chakra dome around boss."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = 55 + int(math.sin(phase * 3) * 3)
        # Dome bubble (ellipse taller than wide)
        dome = pygame.Surface((r * 2 + 20, r * 2 + 30), pygame.SRCALPHA)
        center = (r + 10, r + 15)
        # Multiple orbit lines (like spinning chakra shell)
        for orbit_i in range(4):
            orbit_ang = phase * 4 + orbit_i * math.pi / 4
            # Draw ellipse rotated (approximate)
            for pt_i in range(24):
                p_ang = pt_i * math.pi / 12
                # Ellipse point
                rx = int(math.cos(p_ang) * r)
                ry = int(math.sin(p_ang) * r * 1.1)
                # Rotate by orbit_ang (2D squash for tilt effect)
                cos_o = math.cos(orbit_ang)
                sin_o = math.sin(orbit_ang)
                px = int(rx * cos_o - ry * sin_o * 0.3) + center[0]
                py = int(rx * sin_o * 0.3 + ry * cos_o) + center[1]
                a = _NS_kaoruken._alpha(200)
                pygame.draw.rect(dome,
                                 (*_NS_kaoruken.PALETTE["chakra_mid"], a),
                                 (px, py, 1, 1))
                if pt_i % 3 == 0:
                    pygame.draw.rect(dome,
                                     (*_NS_kaoruken.PALETTE["chakra_hot"], a),
                                     (px, py, 2, 2))
        # Big outer sphere outline
        for i, (thick, av) in enumerate([(3, 80), (2, 130), (1, 200)]):
            pygame.draw.ellipse(dome,
                                (*_NS_kaoruken.PALETTE["chakra_dark"], av),
                                (center[0] - r - i, center[1] - r - i - 5,
                                 r * 2 + i * 2, r * 2 + 10 + i * 2), thick)
            pygame.draw.ellipse(dome,
                                (*_NS_kaoruken.PALETTE["chakra_mid"], av),
                                (center[0] - r - i + 1, center[1] - r - i - 4,
                                 r * 2 + i * 2 - 2, r * 2 + 8 + i * 2), 1)
        # Rotating sparkles on outer edge
        for i in range(16):
            sang = phase * 5 + i * math.pi / 8
            sx = center[0] + int(math.cos(sang) * r)
            sy = center[1] + int(math.sin(sang) * r * 1.1)
            pygame.draw.rect(dome, _NS_kaoruken.PALETTE["chakra_shine"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(dome, _NS_kaoruken.PALETTE["white"],
                             (sx, sy, 1, 1))
        surface.blit(dome, (x - r - 10, y - r - 15))

    # ============================================================
    # SKILL R — LION FIST (chakra lion spirit charging)
    # ============================================================
    def _draw_lion_fist(surface, boss, x, y, timer, phase):
        """Big chakra lion spirit flying toward target."""
        facing = boss.direction
        duration = 90
        progress = 1 - timer / duration
        progress = max(0.0, min(1.0, progress))
        tx, ty = _NS_kaoruken._target_position(boss, x, y)
        if progress < 0.15:
            # Charge phase
            t = progress / 0.15
            cx_c = x + facing * 25
            cy_c = y - 5
            for r in range(int(15 * t) + 5, 0, -1):
                a = _NS_kaoruken._alpha(220 * (15 * t + 5 - r) / (15 * t + 5))
                _NS_kaoruken._aacircle(surface,
                                       (*_NS_kaoruken.PALETTE["chakra_dark"], a),
                                       (cx_c, cy_c), r)
            _NS_kaoruken._aacircle(surface,
                                   _NS_kaoruken.PALETTE["chakra_hot"],
                                   (cx_c, cy_c), max(1, int(6 * t)))
            return
        t = (progress - 0.15) / 0.7
        t = min(1.0, t)
        start_x = x + facing * 30
        start_y = y - 5
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail (chakra energy stream)
        for i in range(10):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            a = _NS_kaoruken._alpha(200 - i * 20)
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_darkest"], a),
                                   (px, py), max(2, 10 - i))
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_dark"], a),
                                   (px, py), max(1, 7 - i))
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_mid"], a),
                                   (px, py), max(1, 5 - i))
        # LION SPIRIT (big shape)
        _NS_kaoruken._draw_chakra_lion(surface, bx, by, facing, phase)
        # Impact
        if t > 0.85:
            st = (t - 0.85) / 0.15
            r = int(25 + st * 25)
            a = _NS_kaoruken._alpha(255 * (1 - st))
            for rr in range(r + 4, 0, -3):
                ra = _NS_kaoruken._alpha(a * (r + 4 - rr) / (r + 4))
                _NS_kaoruken._aacircle(surface,
                                       (*_NS_kaoruken.PALETTE["chakra_dark"], ra),
                                       (tx, ty), rr)
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_mid"], a),
                                   (tx, ty), max(2, r - 5))
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_hot"], a),
                                   (tx, ty), max(1, r - 12))
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["white"], a),
                                   (tx, ty), max(1, r - 18))
            # Radial sparks
            for i in range(12):
                sang = i * math.pi / 6 + st * 3
                dist = int(r * 1.3)
                ex = tx + int(math.cos(sang) * dist)
                ey = ty + int(math.sin(sang) * dist)
                pygame.draw.rect(surface,
                                 (*_NS_kaoruken.PALETTE["chakra_hot"], a),
                                 (ex, ey, 3, 3))
                pygame.draw.rect(surface,
                                 (*_NS_kaoruken.PALETTE["white"], a),
                                 (ex, ey, 1, 1))

    def _draw_chakra_lion(surface, lx, ly, facing, phase):
        """Big chakra lion silhouette (roaring)."""
        # Body — big oval
        body_pts = [
            (lx - 22 * facing, ly - 2),
            (lx - 20 * facing, ly - 10),
            (lx - 10 * facing, ly - 15),
            (lx + 5 * facing, ly - 14),
            (lx + 15 * facing, ly - 10),
            (lx + 20 * facing, ly - 3),
            (lx + 18 * facing, ly + 8),
            (lx + 5 * facing, ly + 12),
            (lx - 10 * facing, ly + 10),
            (lx - 20 * facing, ly + 5),
        ]
        # Multi-layer glow (from darkest outer to brightest inner)
        for layer_i, (offset, color, a) in enumerate([
            (3, _NS_kaoruken.PALETTE["chakra_darkest"], 100),
            (2, _NS_kaoruken.PALETTE["chakra_dark"], 150),
            (1, _NS_kaoruken.PALETTE["chakra_mid"], 200),
            (0, _NS_kaoruken.PALETTE["lion_mid"], 240),
        ]):
            expanded = [
                (p[0] + offset * (1 if p[0] > lx else -1),
                 p[1] + offset * (1 if p[1] > ly else -1))
                for p in body_pts
            ]
            _NS_kaoruken._poly(surface, (*color, a), expanded)
        # Highlight core
        core_pts = [
            (lx - 15 * facing, ly - 2),
            (lx - 10 * facing, ly - 10),
            (lx + 5 * facing, ly - 10),
            (lx + 13 * facing, ly - 5),
            (lx + 12 * facing, ly + 5),
            (lx + 2 * facing, ly + 8),
            (lx - 10 * facing, ly + 6),
        ]
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["lion_light"], core_pts)
        # LION HEAD (front)
        head_x = lx + 18 * facing
        head_y = ly - 8
        # Head shape
        head_pts = [
            (head_x - 5 * facing, head_y - 3),
            (head_x - 3 * facing, head_y - 7),
            (head_x + 4 * facing, head_y - 8),
            (head_x + 10 * facing, head_y - 5),
            (head_x + 12 * facing, head_y),
            (head_x + 10 * facing, head_y + 5),
            (head_x + 3 * facing, head_y + 7),
            (head_x - 3 * facing, head_y + 5),
        ]
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["chakra_dark"], head_pts)
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["chakra_mid"], [
            (head_x - 3 * facing, head_y - 2),
            (head_x - 2 * facing, head_y - 5),
            (head_x + 4 * facing, head_y - 6),
            (head_x + 9 * facing, head_y - 4),
            (head_x + 10 * facing, head_y),
            (head_x + 9 * facing, head_y + 4),
            (head_x + 3 * facing, head_y + 6),
            (head_x - 2 * facing, head_y + 4),
        ])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["lion_mid"], [
            (head_x - 1, head_y - 3),
            (head_x + 3 * facing, head_y - 4),
            (head_x + 7 * facing, head_y - 2),
            (head_x + 8 * facing, head_y + 2),
            (head_x + 3 * facing, head_y + 4),
            (head_x - 1, head_y + 3),
        ])
        # Mane (radiating spikes around head)
        for i in range(10):
            m_ang = i * math.pi / 5
            m_base_x = head_x + int(math.cos(m_ang) * 6) * facing
            m_base_y = head_y + int(math.sin(m_ang) * 6)
            m_tip_x = head_x + int(math.cos(m_ang) * 12) * facing
            m_tip_y = head_y + int(math.sin(m_ang) * 12)
            perp = m_ang + math.pi / 2
            pa_x = m_base_x + int(math.cos(perp) * 2)
            pa_y = m_base_y + int(math.sin(perp) * 2)
            pb_x = m_base_x - int(math.cos(perp) * 2)
            pb_y = m_base_y - int(math.sin(perp) * 2)
            _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["chakra_dark"],
                               [(m_tip_x, m_tip_y), (pa_x, pa_y), (pb_x, pb_y)])
            _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["chakra_mid"], [
                (m_tip_x, m_tip_y),
                (int((m_tip_x + m_base_x) / 2),
                 int((m_tip_y + m_base_y) / 2)),
                (m_base_x, m_base_y),
            ])
            pygame.draw.rect(surface, _NS_kaoruken.PALETTE["lion_hot"],
                             (m_tip_x, m_tip_y, 1, 1))
        # Roaring MOUTH (open jaw)
        mouth_x = head_x + 8 * facing
        mouth_y = head_y + 2
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["shadow_deep"], [
            (mouth_x - 2 * facing, mouth_y - 1),
            (mouth_x + 4 * facing, mouth_y - 2),
            (mouth_x + 4 * facing, mouth_y + 4),
            (mouth_x - 1 * facing, mouth_y + 3),
        ])
        _NS_kaoruken._poly(surface, _NS_kaoruken.PALETTE["chakra_darkest"], [
            (mouth_x - 1 * facing, mouth_y),
            (mouth_x + 3 * facing, mouth_y - 1),
            (mouth_x + 3 * facing, mouth_y + 3),
            (mouth_x, mouth_y + 2),
        ])
        # Teeth (small triangles)
        for tooth_i in range(3):
            tth_x = mouth_x + tooth_i * facing
            pygame.draw.rect(surface, _NS_kaoruken.PALETTE["white"],
                             (tth_x, mouth_y, 1, 1))
            pygame.draw.rect(surface, _NS_kaoruken.PALETTE["white"],
                             (tth_x, mouth_y + 2, 1, 1))
        # EYE (fierce)
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["shadow_deep"],
                         (head_x + 3 * facing, head_y - 1, 2, 2))
        pygame.draw.rect(surface, _NS_kaoruken.PALETTE["white"],
                         (head_x + 3 * facing, head_y - 1, 1, 1))
        # Eye glow
        for r in range(3, 0, -1):
            a = _NS_kaoruken._alpha(120 * (3 - r) / 3)
            _NS_kaoruken._aacircle(surface,
                                   (*_NS_kaoruken.PALETTE["chakra_hot"], a),
                                   (head_x + 3 * facing, head_y), r)
        # Overall bright outline
        for i in range(len(body_pts) - 1):
            pygame.draw.line(surface,
                             _NS_kaoruken.PALETTE["lion_hot"],
                             body_pts[i], body_pts[i + 1], 1)
        pygame.draw.line(surface, _NS_kaoruken.PALETTE["lion_hot"],
                         body_pts[-1], body_pts[0], 1)


# ====================================================================================================
# VAELKORR - MINI BOSS
# ====================================================================================================

class _NS_vaelkorr:
    """Namespace vaelkorr - HD rendering untuk mini boss Vaelkorr."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Robe/cloak (dark akatsuki-like)
        "robe_darkest": (8, 6, 10),
        "robe_dark": (25, 20, 30),
        "robe_mid": (48, 40, 55),
        "robe_light": (78, 68, 88),
        "robe_edge": (110, 95, 120),

        # Red cloud pattern (crimson)
        "cloud_dark": (85, 15, 20),
        "cloud_mid": (165, 35, 40),
        "cloud_light": (220, 70, 65),
        "cloud_shine": (255, 140, 120),

        # Skin (pale gray-green)
        "skin_dark": (55, 65, 55),
        "skin_mid": (110, 120, 100),
        "skin_light": (170, 180, 155),

        # Hair (dark)
        "hair_dark": (10, 10, 15),
        "hair_mid": (35, 30, 40),
        "hair_light": (70, 60, 75),

        # Mask base (bone/ceramic)
        "mask_bone_dark": (60, 50, 35),
        "mask_bone_mid": (150, 130, 90),
        "mask_bone_light": (220, 200, 155),
        "mask_bone_shine": (250, 235, 195),

        # Element: WIND (green)
        "wind_dark": (20, 60, 25),
        "wind_mid": (70, 160, 70),
        "wind_light": (150, 230, 130),
        "wind_shine": (220, 255, 190),

        # Element: WATER (blue)
        "water_dark": (10, 40, 90),
        "water_mid": (40, 120, 210),
        "water_light": (120, 200, 250),
        "water_shine": (200, 240, 255),

        # Element: EARTH (brown/orange)
        "earth_dark": (60, 30, 15),
        "earth_mid": (155, 90, 40),
        "earth_light": (220, 150, 80),
        "earth_shine": (250, 210, 140),

        # Element: LIGHTNING (white-purple)
        "light_dark": (60, 60, 90),
        "light_mid": (170, 170, 210),
        "light_light": (230, 230, 255),
        "light_shine": (255, 255, 255),

        # Element: FIRE (red-orange)
        "fire_dark": (90, 25, 10),
        "fire_mid": (220, 90, 30),
        "fire_light": (255, 170, 60),
        "fire_shine": (255, 230, 150),

        # Thread (glowing green cord — signature)
        "thread_dark": (15, 55, 20),
        "thread_mid": (55, 165, 60),
        "thread_light": (140, 240, 130),
        "thread_shine": (220, 255, 200),

        # Heart extraction (purple)
        "heart_dark": (35, 10, 55),
        "heart_mid": (110, 40, 170),
        "heart_light": (200, 130, 240),
        "heart_shine": (250, 210, 255),

        # Eyes (yellow/green glow)
        "eye_dark": (40, 60, 10),
        "eye_mid": (160, 220, 40),
        "eye_light": (230, 255, 130),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    ELEMENT_MAP = {
        0: "wind",
        1: "water",
        2: "earth",
        3: "light",   # lightning
        4: "fire",
    }

    # ============================================================
    # UTILITIES
    # ============================================================
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_vaelkorr._clamp(color)
        if _NS_vaelkorr.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_vaelkorr._clamp(color)
        if _NS_vaelkorr.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_vaelkorr._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)

    def _element_colors(elem):
        """Return (dark, mid, light, shine) for current element."""
        return (
            _NS_vaelkorr.PALETTE[f"{elem}_dark"],
            _NS_vaelkorr.PALETTE[f"{elem}_mid"],
            _NS_vaelkorr.PALETTE[f"{elem}_light"],
            _NS_vaelkorr.PALETTE[f"{elem}_shine"],
        )

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_vaelkorr(surface, boss, x, y):
        """Entry point untuk Boss.draw()."""
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_vaelkorr._detect_moving(boss)
        _NS_vaelkorr._update_attack_anim(boss)
        # Attacking = SEDANG dalam animasi attack
        attacking = getattr(boss, "_vk_attack_active", False)

        # Current element (0=wind default)
        current_elem = _NS_vaelkorr.ELEMENT_MAP.get(
            getattr(boss, "current_element", 0) % 5, "wind"
        )

        # Ambient
        _NS_vaelkorr._draw_shadow(surface, x, y + 52)
        _NS_vaelkorr._draw_akatsuki_aura(surface, x, y, pulse, current_elem)
        _NS_vaelkorr._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX
        if active_skill == "e":
            _NS_vaelkorr._draw_earth_grudge_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vaelkorr._draw_heart_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_vaelkorr._draw_body_attack(surface, boss, x, y, current_elem)
        elif moving:
            _NS_vaelkorr._draw_body_walk(surface, boss, x, y, current_elem)
        else:
            _NS_vaelkorr._draw_body_idle(surface, boss, x, y, current_elem)

        # Floating masks around boss
        _NS_vaelkorr._draw_floating_masks(surface, boss, x, y, pulse, current_elem)

        # Foreground skill FX
        if active_skill == "q":
            _NS_vaelkorr._draw_thread_spear_skill(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_vaelkorr._draw_mask_switch_fx(surface, boss, x, y, skill_timer, pulse, current_elem)
        elif active_skill == "e":
            _NS_vaelkorr._draw_earth_grudge_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_vaelkorr._draw_heart_extraction_fg(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        """Deteksi kapan attack dimulai dan track progress."""
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_vk_previous_timer", cooldown))
        active = bool(getattr(boss, "_vk_attack_active", False))

        # Attack dimulai saat timer reset dari tinggi ke rendah (cycle baru)
        # ATAU saat timer dekat cooldown
        if not active:
            # Trigger attack ketika timer mendekati cooldown
            if timer >= cooldown - 20:
                boss._vk_attack_active = True
                boss._vk_attack_frame = 0
                active = True

        if active:
            boss._vk_attack_frame = int(getattr(boss, "_vk_attack_frame", 0)) + 1
            attack_duration = 30  # frame animasi attack
            if boss._vk_attack_frame >= attack_duration:
                boss._vk_attack_active = False
                boss._vk_attack_frame = 0
                active = False

        boss._vk_previous_timer = timer
        attack_duration = 30
        boss._vk_attack_progress = (
            min(1.0, getattr(boss, "_vk_attack_frame", 0) / attack_duration)
            if active else 0.0
        )

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

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y, elem):
        bob = int(math.sin(boss.pulse * 0.6) * 3)
        _NS_vaelkorr._draw_full_body(surface, x, y + bob,
                                     boss.direction, boss.pulse, "idle", 0, elem)

    def _draw_body_walk(surface, boss, x, y, elem):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_vaelkorr._draw_full_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "walk", 0, elem)

    def _draw_body_attack(surface, boss, x, y, elem):
        progress = getattr(boss, "_vk_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # 3-phase animation:
        # 0.0-0.3: WIND-UP (tarik mundur, angkat lengan)
        # 0.3-0.55: THRUST (dorong maju cepat + release projectile)
        # 0.55-1.0: RECOVERY (kembali ke idle)
        if progress < 0.3:
            t = progress / 0.3
            # Ease-in: tarik mundur
            lunge = -int(t * t * 6) * boss.direction
            lift = int(t * 4)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            # Ease-out: dorong maju
            lunge = int((-6 + t * 20)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.55) / 0.45
            # Kembali ke idle
            lunge = int(14 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)

        _NS_vaelkorr._draw_full_body(surface, x + lunge, y - lift,
                                     boss.direction, boss.pulse, "attack",
                                     progress, elem)
        _NS_vaelkorr._draw_basic_thread_projectile(surface, boss, x + lunge,
                                                    y - lift, progress, elem)
    # ============================================================
    # FULL BODY (humanoid: legs, robe, torso, arms, head, hood)
    # ============================================================
    def _draw_full_body(surface, cx, cy, facing, phase, action, atk_prog, elem):
        # 1. Robe/lower body (paling belakang)
        _NS_vaelkorr._draw_robe_lower(surface, cx, cy, facing, phase, action)
        # 2. BACK arm dulu (di belakang torso)
        _NS_vaelkorr._draw_back_arm(surface, cx, cy, facing, phase, action)
        # 3. Torso + red clouds
        _NS_vaelkorr._draw_torso(surface, cx, cy, facing, phase, action)
        # 4. Head + hood
        _NS_vaelkorr._draw_head(surface, cx, cy - 22, facing, phase, elem)
        # 5. FRONT arm (di depan torso, di depan head base)
        _NS_vaelkorr._draw_front_arm(surface, cx, cy, facing, phase, action,
                                     atk_prog, elem)

    def _draw_robe_lower(surface, cx, cy, facing, phase, action):
        """Long flowing robe from hip to ground."""
        sway = math.sin(phase * 0.8) * 2 if action == "idle" else math.sin(phase) * 3

        # Bottom edge tattered
        robe_pts = [
            (cx - 14, cy + 8),
            (cx - 16, cy + 18),
            (cx - 18, cy + 28),
            (cx - 15 + int(sway), cy + 40),
            (cx - 8 + int(sway * 0.5), cy + 44),
            (cx - 2, cy + 46),
            (cx + 5, cy + 44),
            (cx + 12 - int(sway * 0.5), cy + 42),
            (cx + 17 - int(sway), cy + 32),
            (cx + 16, cy + 20),
            (cx + 14, cy + 8),
        ]
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in robe_pts])
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["robe_darkest"], robe_pts)

        # Layered highlights
        inner_pts = [
            (cx - 12, cy + 10),
            (cx - 14, cy + 20),
            (cx - 15, cy + 30),
            (cx - 10 + int(sway), cy + 38),
            (cx + 10 - int(sway), cy + 38),
            (cx + 13, cy + 30),
            (cx + 14, cy + 20),
            (cx + 12, cy + 10),
        ]
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["robe_dark"], inner_pts)

        # Vertical fold shadows
        for x_off in (-8, -3, 3, 8):
            pygame.draw.line(surface, _NS_vaelkorr.PALETTE["robe_darkest"],
                             (cx + x_off, cy + 12),
                             (cx + x_off + int(sway * 0.3), cy + 40), 1)

        # Red cloud pattern on robe
        for i, (rx, ry, rs) in enumerate([
            (-8, 20, 3), (6, 26, 3), (-4, 34, 2), (10, 16, 2),
        ]):
            cx2 = cx + rx
            cy2 = cy + ry
            _NS_vaelkorr._draw_red_cloud(surface, cx2, cy2, rs)

    def _draw_red_cloud(surface, cx, cy, size):
        """Small red cloud symbol (Akatsuki-style)."""
        # Outer dark cloud shape
        pts = [
            (cx - size * 2, cy),
            (cx - size, cy - size),
            (cx, cy - size),
            (cx + size, cy - size),
            (cx + size * 2, cy),
            (cx + size, cy + size // 2),
            (cx - size, cy + size // 2),
        ]
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["cloud_dark"], pts)
        # Mid red
        inner_pts = [
            (cx - size, cy),
            (cx, cy - size + 1),
            (cx + size, cy),
            (cx, cy + 1),
        ]
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["cloud_mid"], inner_pts)
        # Bright highlight
        pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["cloud_light"],
                         (cx - 1, cy - 1, 2, 1))

    def _draw_torso(surface, cx, cy, facing, phase, action):
        """Upper body (chest/shoulders under robe)."""
        breath = math.sin(phase * 0.7) * 1

        torso_pts = [
            (cx - 12, cy - 8),
            (cx - 14, cy - 2),
            (cx - 13, cy + 6),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 13, cy + 6),
            (cx + 14, cy - 2),
            (cx + 12, cy - 8),
            (cx + 6, cy - 12),
            (cx - 6, cy - 12),
        ]
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in torso_pts])
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["robe_darkest"], torso_pts)
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["robe_dark"], [
            (cx - 11, cy - 6),
            (cx - 12, cy + 2),
            (cx - 6, cy + 8),
            (cx + 6, cy + 8),
            (cx + 12, cy + 2),
            (cx + 11, cy - 6),
            (cx + 4, cy - 10),
            (cx - 4, cy - 10),
        ])
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["robe_mid"], [
            (cx - 8, cy - 4),
            (cx - 9, cy + 2),
            (cx - 4, cy + 6),
            (cx + 4, cy + 6),
            (cx + 9, cy + 2),
            (cx + 8, cy - 4),
            (cx + 2, cy - 8),
            (cx - 2, cy - 8),
        ])

        # Central V-collar opening (red inside)
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["cloud_dark"], [
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx, cy - 3),
        ])
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["cloud_mid"], [
            (cx - 2, cy - 9),
            (cx + 2, cy - 9),
            (cx, cy - 4),
        ])

        # Red clouds on torso
        _NS_vaelkorr._draw_red_cloud(surface, cx - 7, cy - 2, 2)
        _NS_vaelkorr._draw_red_cloud(surface, cx + 7, cy + 4, 2)

        # Belt line
        pygame.draw.line(surface, _NS_vaelkorr.PALETTE["robe_darkest"],
                         (cx - 12, cy + 9), (cx + 12, cy + 9), 2)
        pygame.draw.line(surface, _NS_vaelkorr.PALETTE["cloud_dark"],
                         (cx - 12, cy + 10), (cx + 12, cy + 10), 1)

    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        """Back arm (di belakang torso)."""
        sway = math.sin(phase * 0.9) * 2

        back_shoulder_x = cx - facing * 10
        back_shoulder_y = cy - 6
        back_hand_x = back_shoulder_x - facing * 4 + int(sway)
        back_hand_y = cy + 8

        _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["shadow_deep"],
                             (back_shoulder_x + 1, back_shoulder_y + 1),
                             (back_hand_x + 1, back_hand_y + 1), 6)
        _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["robe_darkest"],
                             (back_shoulder_x, back_shoulder_y),
                             (back_hand_x, back_hand_y), 5)
        _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["robe_dark"],
                             (back_shoulder_x, back_shoulder_y),
                             (back_hand_x, back_hand_y), 3)
        # Back hand
        _NS_vaelkorr._aacircle(surface, _NS_vaelkorr.PALETTE["skin_dark"],
                               (back_hand_x, back_hand_y), 3)
        _NS_vaelkorr._aacircle(surface, _NS_vaelkorr.PALETTE["skin_mid"],
                               (back_hand_x, back_hand_y), 2)


    def _draw_front_arm(surface, cx, cy, facing, phase, action, atk_prog, elem):
        """Front arm dengan animasi attack yang jelas."""
        sway = math.sin(phase * 0.9) * 2

        front_shoulder_x = cx + facing * 10
        front_shoulder_y = cy - 6

        if action == "attack":
            # ANIMASI JELAS: wind-up → thrust → recovery
            if atk_prog < 0.3:
                # WIND-UP: tarik tangan ke belakang, angkat ke atas
                t = atk_prog / 0.3
                hand_offset_x = facing * int(-t * 12)  # tarik mundur
                hand_offset_y = int(-8 - t * 6)  # angkat tinggi
            elif atk_prog < 0.55:
                # THRUST: dorong ke depan cepat!
                t = (atk_prog - 0.3) / 0.25
                # Ease-out cubic untuk snap yang keras
                ease = 1 - (1 - t) ** 3
                hand_offset_x = facing * int(-12 + ease * 32)  # maju jauh
                hand_offset_y = int(-14 + ease * 16)  # turun ke horizontal
            else:
                # RECOVERY: kembali ke posisi normal
                t = (atk_prog - 0.55) / 0.45
                hand_offset_x = facing * int(20 - t * 16)
                hand_offset_y = int(2 + t * 4)

            front_hand_x = front_shoulder_x + hand_offset_x
            front_hand_y = front_shoulder_y + hand_offset_y
        else:
            front_hand_x = front_shoulder_x + facing * 4 - int(sway)
            front_hand_y = cy + 6

        # Elbow midpoint (curved arm)
        elbow_x = int((front_shoulder_x + front_hand_x) / 2) + facing * 2
        elbow_y = int((front_shoulder_y + front_hand_y) / 2) + 2

        # Saat attack di fase thrust, siku lebih tegang
        if action == "attack" and 0.3 < atk_prog < 0.55:
            elbow_x = int((front_shoulder_x + front_hand_x) / 2) + facing * 4
            elbow_y = int((front_shoulder_y + front_hand_y) / 2) - 2

        # Upper arm
        _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["shadow_deep"],
                             (front_shoulder_x + 1, front_shoulder_y + 1),
                             (elbow_x + 1, elbow_y + 1), 6)
        _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["robe_darkest"],
                             (front_shoulder_x, front_shoulder_y),
                             (elbow_x, elbow_y), 5)
        _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["robe_dark"],
                             (front_shoulder_x, front_shoulder_y),
                             (elbow_x, elbow_y), 3)
        _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["robe_mid"],
                             (front_shoulder_x, front_shoulder_y - 1),
                             (elbow_x, elbow_y - 1), 1)
        # Forearm
        _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 1),
                             (front_hand_x + 1, front_hand_y + 1), 5)
        _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["robe_darkest"],
                             (elbow_x, elbow_y),
                             (front_hand_x, front_hand_y), 4)
        _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["robe_dark"],
                             (elbow_x, elbow_y),
                             (front_hand_x, front_hand_y), 2)

        # Front hand
        _NS_vaelkorr._aacircle(surface, _NS_vaelkorr.PALETTE["skin_dark"],
                               (front_hand_x, front_hand_y), 4)
        _NS_vaelkorr._aacircle(surface, _NS_vaelkorr.PALETTE["skin_mid"],
                               (front_hand_x, front_hand_y), 3)
        _NS_vaelkorr._aacircle(surface, _NS_vaelkorr.PALETTE["skin_light"],
                               (front_hand_x - 1, front_hand_y - 1), 1)

        # Thread energy channeling di tangan saat attack
        ec = _NS_vaelkorr._element_colors(elem)
        if action == "attack":
            # Charge intensity berdasarkan fase
            if atk_prog < 0.3:
                # Wind-up: energy menumpuk (getting brighter)
                intensity = atk_prog / 0.3
            elif atk_prog < 0.55:
                # Thrust: energy release (peak then fade)
                intensity = 1.0 - (atk_prog - 0.3) / 0.25 * 0.5
            else:
                intensity = 0.3 * (1 - (atk_prog - 0.55) / 0.45)

            for r in range(int(8 * intensity) + 2, 0, -1):
                alpha = _NS_vaelkorr._alpha(100 * intensity * (10 - r) / 10)
                _NS_vaelkorr._aacircle(surface,
                                       (*_NS_vaelkorr.PALETTE["thread_mid"], alpha),
                                       (front_hand_x, front_hand_y), r)
            # Bright core
            if intensity > 0.5:
                _NS_vaelkorr._aacircle(surface,
                                       _NS_vaelkorr.PALETTE["thread_light"],
                                       (front_hand_x, front_hand_y),
                                       max(1, int(intensity * 3)))
                pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["thread_shine"],
                                 (front_hand_x, front_hand_y, 1, 1))

        # Simpan posisi hand untuk projectile origin
        boss_ref = getattr(surface, "_current_boss", None)

    def _draw_head(surface, cx, cy, facing, phase, elem):
        """Head with hood, forehead protector, mask-style face."""
        # Hood (dark)
        hood_pts = [
            (cx - 10, cy + 6),
            (cx - 11, cy - 2),
            (cx - 9, cy - 9),
            (cx - 4, cy - 12),
            (cx + 4, cy - 12),
            (cx + 9, cy - 9),
            (cx + 11, cy - 2),
            (cx + 10, cy + 6),
            (cx + 8, cy + 8),
            (cx - 8, cy + 8),
        ]
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in hood_pts])
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["robe_darkest"], hood_pts)
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["robe_dark"], [
            (cx - 9, cy + 5),
            (cx - 10, cy - 1),
            (cx - 8, cy - 8),
            (cx - 3, cy - 11),
            (cx + 3, cy - 11),
            (cx + 8, cy - 8),
            (cx + 10, cy - 1),
            (cx + 9, cy + 5),
        ])

        # Face (mask-like, wrapped in cloth)
        face_pts = [
            (cx - 6, cy + 4),
            (cx - 7, cy - 2),
            (cx - 5, cy - 7),
            (cx + 5, cy - 7),
            (cx + 7, cy - 2),
            (cx + 6, cy + 4),
        ]
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["skin_dark"], face_pts)
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["skin_mid"], [
            (cx - 5, cy + 2),
            (cx - 6, cy - 2),
            (cx - 4, cy - 6),
            (cx + 4, cy - 6),
            (cx + 6, cy - 2),
            (cx + 5, cy + 2),
        ])

        # Forehead protector band (metal)
        pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["robe_darkest"],
                         (cx - 6, cy - 6, 12, 3))
        pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["mask_bone_dark"],
                         (cx - 6, cy - 6, 12, 2))
        pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["mask_bone_mid"],
                         (cx - 6, cy - 5, 12, 1))
        # Emblem (small horizontal line)
        pygame.draw.line(surface, _NS_vaelkorr.PALETTE["mask_bone_light"],
                         (cx - 2, cy - 5), (cx + 2, cy - 5), 1)

        # Face wrap (cloth mask lower part)
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["robe_darkest"], [
            (cx - 6, cy + 4),
            (cx - 5, cy - 1),
            (cx + 5, cy - 1),
            (cx + 6, cy + 4),
            (cx + 4, cy + 6),
            (cx - 4, cy + 6),
        ])
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["robe_dark"], [
            (cx - 5, cy + 3),
            (cx - 4, cy),
            (cx + 4, cy),
            (cx + 5, cy + 3),
            (cx + 3, cy + 5),
            (cx - 3, cy + 5),
        ])

        # EYES (glowing element color)
        ec = _NS_vaelkorr._element_colors(elem)
        eye_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_x_off in (-3, 3):
            ex = cx + eye_x_off * facing
            ey = cy - 3
            # Socket
            pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["shadow_deep"],
                             (ex - 1, ey, 2, 2))
            # Glow halo
            for r in range(4, 0, -1):
                alpha = _NS_vaelkorr._alpha(80 * (4 - r) / 4 * eye_pulse)
                _NS_vaelkorr._aacircle(surface, (*ec[1], alpha), (ex, ey), r)
            # Bright core
            pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["white"],
                             (ex, ey, 1, 1))

    # ============================================================
    # FLOATING MASKS AROUND BOSS
    # ============================================================
    def _draw_floating_masks(surface, boss, cx, cy, phase, current_elem):
        """4 masks orbiting around boss (like Kakuzu's hearts)."""
        mask_configs = [
            ("wind", -40, -10, 0),
            ("water", 40, -15, math.pi * 0.5),
            ("earth", -35, 20, math.pi),
            ("fire", 35, 25, math.pi * 1.5),
        ]

        for elem, base_x, base_y, angle_off in mask_configs:
            # Slight floating motion
            float_y = math.sin(phase * 0.8 + angle_off) * 3
            float_x = math.cos(phase * 0.5 + angle_off) * 2
            mx = cx + base_x + int(float_x)
            my = cy + base_y + int(float_y)

            # Draw connecting thread to boss (subtle)
            _NS_vaelkorr._aaline(surface,
                                 (*_NS_vaelkorr.PALETTE["thread_dark"], 100),
                                 (cx, cy), (mx, my), 1)

            _NS_vaelkorr._draw_element_mask(surface, mx, my, elem,
                                            highlight=(elem == current_elem))

    def _draw_element_mask(surface, cx, cy, elem, highlight=False):
        """Small bone mask with element color."""
        ec = _NS_vaelkorr._element_colors(elem)

        # Shadow
        pygame.draw.ellipse(surface, _NS_vaelkorr.PALETTE["shadow_deep"],
                            (cx - 5, cy - 4, 11, 10))

        # Mask base (bone)
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["mask_bone_dark"], [
            (cx - 5, cy - 3),
            (cx - 4, cy - 5),
            (cx, cy - 6),
            (cx + 4, cy - 5),
            (cx + 5, cy - 3),
            (cx + 4, cy + 3),
            (cx, cy + 5),
            (cx - 4, cy + 3),
        ])
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["mask_bone_mid"], [
            (cx - 4, cy - 2),
            (cx - 3, cy - 4),
            (cx, cy - 5),
            (cx + 3, cy - 4),
            (cx + 4, cy - 2),
            (cx + 3, cy + 2),
            (cx, cy + 4),
            (cx - 3, cy + 2),
        ])
        # Highlight (top)
        pygame.draw.line(surface, _NS_vaelkorr.PALETTE["mask_bone_light"],
                         (cx - 2, cy - 4), (cx + 2, cy - 4), 1)

        # Element eyes (glowing)
        pygame.draw.rect(surface, ec[1], (cx - 2, cy - 2, 1, 1))
        pygame.draw.rect(surface, ec[1], (cx + 2, cy - 2, 1, 1))
        pygame.draw.rect(surface, ec[2], (cx - 2, cy - 2, 1, 1))
        pygame.draw.rect(surface, ec[2], (cx + 2, cy - 2, 1, 1))

        # Mouth line
        pygame.draw.line(surface, _NS_vaelkorr.PALETTE["shadow_deep"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
        pygame.draw.rect(surface, ec[1], (cx, cy + 2, 1, 1))

        # If active/highlighted, add glow
        if highlight:
            for r in range(9, 4, -1):
                alpha = _NS_vaelkorr._alpha(80 * (9 - r) / 5)
                _NS_vaelkorr._aacircle(surface, (*ec[2], alpha), (cx, cy), r)

    # ============================================================
    # BASIC RANGED ATTACK — THREAD PROJECTILE
    # ============================================================
    def _draw_basic_thread_projectile(surface, boss, x, y, progress, elem):
        # Projectile keluar SAAT thrust (setelah wind-up) sampai selesai
        if progress < 0.45:
            return
        facing = boss.direction
        tx, ty = _NS_vaelkorr._target_position(boss, x, y)
        ec = _NS_vaelkorr._element_colors(elem)

        # Origin dari posisi tangan saat thrust
        start_x = x + facing * 30
        start_y = y - 4

        # Normalisasi t: dari 0.45 sampai 1.0
        t = (progress - 0.45) / 0.55
        t = min(1.0, t)
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)

        # Thread trail
        for i in range(7):
            trail_t = max(0.0, t - i * 0.08)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            alpha = _NS_vaelkorr._alpha(220 - i * 30)
            size = max(1, 5 - i)
            _NS_vaelkorr._aacircle(surface, (*_NS_vaelkorr.PALETTE["thread_dark"], alpha),
                                   (px, py), size)
            _NS_vaelkorr._aacircle(surface, (*_NS_vaelkorr.PALETTE["thread_mid"], alpha),
                                   (px, py), max(1, size - 1))
            _NS_vaelkorr._aacircle(surface, (*_NS_vaelkorr.PALETTE["thread_light"], alpha),
                                   (px, py), max(1, size - 2))

        # Spear tip (elongated diamond)
        angle = math.atan2(ty - start_y, tx - start_x)
        tip_len = 8
        tip_x = bx + int(math.cos(angle) * tip_len)
        tip_y = by + int(math.sin(angle) * tip_len)
        back_x = bx - int(math.cos(angle) * 4)
        back_y = by - int(math.sin(angle) * 4)
        side_x = -math.sin(angle) * 3
        side_y = math.cos(angle) * 3

        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["thread_dark"], [
            (tip_x, tip_y),
            (bx + int(side_x), by + int(side_y)),
            (back_x, back_y),
            (bx - int(side_x), by - int(side_y)),
        ])
        _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["thread_mid"], [
            (tip_x, tip_y),
            (bx + int(side_x * 0.6), by + int(side_y * 0.6)),
            (back_x, back_y),
            (bx - int(side_x * 0.6), by - int(side_y * 0.6)),
        ])
        _NS_vaelkorr._aacircle(surface, _NS_vaelkorr.PALETTE["thread_light"], (bx, by), 2)
        pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["thread_shine"], (bx, by, 1, 1))
    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((120, 26), pygame.SRCALPHA)
        for radius in range(12, 0, -1):
            alpha = max(0, (12 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 13 - radius,
                                 100 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, 170), (5, 7, 110, 12))
        surface.blit(shadow, (x - 60, y - 13))

    def _draw_akatsuki_aura(surface, x, y, phase, elem):
        """Subtle dark aura + element color tint."""
        ec = _NS_vaelkorr._element_colors(elem)
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((180, 150), pygame.SRCALPHA)
        for radius in range(75, 5, -5):
            alpha = _NS_vaelkorr._alpha((75 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_vaelkorr._aacircle(aura,
                                       (*_NS_vaelkorr.PALETTE["robe_darkest"], alpha),
                                       (90, 75), radius)
        # Element tint
        for radius in range(45, 5, -4):
            alpha = _NS_vaelkorr._alpha((45 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_vaelkorr._aacircle(aura, (*ec[0], alpha), (90, 75), radius)
        surface.blit(aura, (x - 90, y - 75))

        # Floating embers (element color)
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 32 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, ec[1], (sx, sy, 2, 2))
            pygame.draw.rect(surface, ec[2], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring with runes."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((150, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_vaelkorr.PALETTE["robe_darkest"], 200),
                            (5, 15, 140, 22), 3)
        pygame.draw.ellipse(ring, (*_NS_vaelkorr.PALETTE["cloud_dark"], 210),
                            (14, 17, 122, 18), 2)
        pygame.draw.ellipse(ring, (*_NS_vaelkorr.PALETTE["thread_dark"], 200),
                            (25, 19, 100, 14), 1)

        # Runes
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 75 + int(math.cos(angle) * 40)
            y1 = 26 + int(math.sin(angle) * 6)
            x2 = 75 + int(math.cos(angle) * 64)
            y2 = 26 + int(math.sin(angle) * 10)
            pygame.draw.line(ring, (*_NS_vaelkorr.PALETTE["thread_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring, (*_NS_vaelkorr.PALETTE["thread_light"],
                                       _NS_vaelkorr._alpha(150 * pulse)),
                                (15, 10, 120, 32), 1)
        surface.blit(ring, (x - 75, y - 23))

    # ============================================================
    # SKILL Q — THREAD SPEAR (barrage)
    # ============================================================
    def _draw_thread_spear_skill(surface, boss, x, y, timer, phase):
        """Multiple thread spears in barrage."""
        facing = boss.direction
        duration = 50
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_vaelkorr._target_position(boss, x, y)

        start_x = x + facing * 22
        start_y = y - 6

        # 5 spears in fan/barrage
        spread_count = 5
        for spear_i in range(spread_count):
            offset = (spear_i - 2) * 8
            delay = spear_i * 0.08
            t = max(0.0, min(1.0, (progress - delay) / max(0.05, 1.0 - delay)))
            if t <= 0:
                continue

            end_x = tx
            end_y = ty + offset

            bx = int(start_x + (end_x - start_x) * t)
            by = int(start_y + (end_y - start_y) * t)

            # Trail
            for i in range(8):
                trail_t = max(0.0, t - i * 0.06)
                px = int(start_x + (end_x - start_x) * trail_t)
                py = int(start_y + (end_y - start_y) * trail_t)
                alpha = _NS_vaelkorr._alpha(230 - i * 26)
                size = max(1, 6 - i)
                _NS_vaelkorr._aacircle(surface, (*_NS_vaelkorr.PALETTE["thread_dark"], alpha),
                                       (px, py), size)
                _NS_vaelkorr._aacircle(surface, (*_NS_vaelkorr.PALETTE["thread_mid"], alpha),
                                       (px, py), max(1, size - 1))
                _NS_vaelkorr._aacircle(surface, (*_NS_vaelkorr.PALETTE["thread_light"], alpha),
                                       (px, py), max(1, size - 2))

            # Spear tip
            angle = math.atan2(end_y - start_y, end_x - start_x)
            tip_len = 10
            tip_x = bx + int(math.cos(angle) * tip_len)
            tip_y = by + int(math.sin(angle) * tip_len)
            back_x = bx - int(math.cos(angle) * 5)
            back_y = by - int(math.sin(angle) * 5)
            side_x = -math.sin(angle) * 4
            side_y = math.cos(angle) * 4

            _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["thread_dark"], [
                (tip_x, tip_y),
                (bx + int(side_x), by + int(side_y)),
                (back_x, back_y),
                (bx - int(side_x), by - int(side_y)),
            ])
            _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["thread_mid"], [
                (tip_x, tip_y),
                (bx + int(side_x * 0.6), by + int(side_y * 0.6)),
                (back_x, back_y),
                (bx - int(side_x * 0.6), by - int(side_y * 0.6)),
            ])
            _NS_vaelkorr._aacircle(surface, _NS_vaelkorr.PALETTE["thread_light"], (bx, by), 2)
            pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["thread_shine"], (tip_x, tip_y, 1, 1))

            # Impact burst
            if t > 0.9:
                st = (t - 0.9) / 0.1
                r = int(6 + st * 12)
                alpha = _NS_vaelkorr._alpha(230 * (1 - st))
                _NS_vaelkorr._aacircle(surface, (*_NS_vaelkorr.PALETTE["thread_mid"], alpha),
                                       (end_x, end_y), r, 2)
                for i in range(6):
                    a = i * math.pi / 3
                    ex = end_x + int(math.cos(a) * r)
                    ey = end_y + int(math.sin(a) * r)
                    pygame.draw.rect(surface, (*_NS_vaelkorr.PALETTE["thread_light"], alpha),
                                     (ex, ey, 2, 2))

    # ============================================================
    # SKILL W — MASK SWITCH FX
    # ============================================================
    def _draw_mask_switch_fx(surface, boss, x, y, timer, phase, current_elem):
        """Swirling element energy around boss as it swaps masks."""
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        ec = _NS_vaelkorr._element_colors(current_elem)

        # Spiraling particles around boss
        for i in range(20):
            spiral_t = (progress + i * 0.05) % 1.0
            angle = phase * 3 + i * math.pi / 5 + spiral_t * math.pi * 2
            radius = int(50 - spiral_t * 40)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 10 + int(math.sin(angle) * radius * 0.7)
            alpha = _NS_vaelkorr._alpha(240 * (1 - spiral_t))
            size = max(1, int(3 - spiral_t * 2))

            _NS_vaelkorr._aacircle(surface, (*ec[0], alpha), (sx, sy), size + 1)
            _NS_vaelkorr._aacircle(surface, (*ec[1], alpha), (sx, sy), size)
            pygame.draw.rect(surface, (*ec[2], alpha), (sx, sy, 1, 1))

        # Central bright flash
        flash_intensity = math.sin(progress * math.pi)
        for r in range(20, 3, -2):
            alpha = _NS_vaelkorr._alpha(120 * flash_intensity * (20 - r) / 20)
            _NS_vaelkorr._aacircle(surface, (*ec[1], alpha), (x, y - 10), r)

    # ============================================================
    # SKILL E — EARTH GRUDGE FEAR
    # ============================================================
    def _draw_earth_grudge_ground(surface, boss, x, y, timer, phase):
        """Ground cracks/shockwave in cone from boss."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Cone shockwave
        max_dist = 180
        current_dist = int(max_dist * min(1.0, progress * 2))

        # Cracks in cone
        for i in range(8):
            angle_off = (i - 3.5) * 0.12
            end_x = x + facing * int(math.cos(angle_off) * current_dist)
            end_y = y + 45 + int(math.sin(angle_off) * current_dist * 0.4)

            # Multiple crack segments
            prev_x = x + facing * 20
            prev_y = y + 45
            steps = 5
            for step in range(1, steps + 1):
                t = step / steps
                seg_x = prev_x + facing * int((end_x - prev_x) / steps * (0.8 + math.sin(phase + i) * 0.3))
                seg_y = prev_y + int((end_y - prev_y) / steps)
                pygame.draw.line(surface, _NS_vaelkorr.PALETTE["earth_dark"],
                                 (prev_x, prev_y), (seg_x, seg_y), 3)
                pygame.draw.line(surface, _NS_vaelkorr.PALETTE["earth_mid"],
                                 (prev_x, prev_y), (seg_x, seg_y), 1)
                prev_x, prev_y = seg_x, seg_y

    def _draw_earth_grudge_fg(surface, boss, x, y, timer, phase):
        """Rising earth spikes + grudge tentacles."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        max_dist = 180
        current_dist = int(max_dist * min(1.0, progress * 2))

        # Earth spikes rising in cone
        for i in range(10):
            angle_off = (i - 4.5) * 0.1
            dist = 30 + i * 15
            if dist > current_dist:
                break
            sx = x + facing * int(math.cos(angle_off) * dist)
            sy_base = y + 45 + int(math.sin(angle_off) * dist * 0.4)

            # Spike rise animation
            rise_t = min(1.0, (current_dist - dist) / 30)
            spike_h = int(20 * rise_t + math.sin(phase * 2 + i) * 2)

            # Spike shape
            _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["shadow_deep"], [
                (sx + 1, sy_base - spike_h + 1),
                (sx - 4, sy_base + 1),
                (sx + 4, sy_base + 1),
            ])
            _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["earth_dark"], [
                (sx, sy_base - spike_h),
                (sx - 4, sy_base),
                (sx + 4, sy_base),
            ])
            _NS_vaelkorr._poly(surface, _NS_vaelkorr.PALETTE["earth_mid"], [
                (sx, sy_base - spike_h),
                (sx - 2, sy_base),
                (sx + 2, sy_base),
            ])
            pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["earth_light"],
                             (sx, sy_base - spike_h, 1, 1))
            pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["earth_shine"],
                             (sx, sy_base - spike_h, 1, 1))

            # Grudge tendril curling around spike
            if rise_t > 0.5:
                for t_step in range(3):
                    tt = t_step / 3
                    tendril_x = sx + int(math.sin(phase * 2 + i + tt * 3) * 3)
                    tendril_y = sy_base - int(spike_h * tt) - 3
                    _NS_vaelkorr._aacircle(surface, _NS_vaelkorr.PALETTE["cloud_dark"],
                                           (tendril_x, tendril_y), 2)
                    pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["cloud_mid"],
                                     (tendril_x, tendril_y, 1, 1))

    # ============================================================
    # SKILL R — HEART EXTRACTION
    # ============================================================
    def _draw_heart_ground(surface, boss, x, y, timer, phase):
        """Dark purple ritual circle."""
        tx, ty = _NS_vaelkorr._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(35 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_vaelkorr.PALETTE["heart_dark"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_vaelkorr.PALETTE["heart_mid"], 150),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            # Runes
            for i in range(6):
                angle = phase * 0.5 + i * math.pi / 3
                rx = tx + int(math.cos(angle) * r * 0.8)
                ry = ty + int(math.sin(angle) * r * 0.3)
                pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["heart_light"],
                                 (rx, ry, 2, 2))

    def _draw_heart_extraction_fg(surface, boss, x, y, timer, phase):
        """Thread from boss to target pulling heart."""
        facing = boss.direction
        tx, ty = _NS_vaelkorr._target_position(boss, x, y)
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        start_x = x + facing * 22
        start_y = y - 6

        if progress < 0.3:
            # Extending thread
            t = progress / 0.3
            end_x = int(start_x + (tx - start_x) * t)
            end_y = int(start_y + (ty - start_y) * t)
            # Wavy thread
            steps = 10
            prev = (start_x, start_y)
            for step in range(1, steps + 1):
                tt = step / steps
                sx = int(start_x + (end_x - start_x) * tt)
                sy = int(start_y + (end_y - start_y) * tt)
                perp_wave = math.sin(phase * 3 + tt * math.pi * 2) * 3
                sx += int(perp_wave * 0.3)
                sy += int(perp_wave)
                _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["heart_dark"],
                                     prev, (sx, sy), 3)
                _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["heart_mid"],
                                     prev, (sx, sy), 2)
                _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["heart_light"],
                                     prev, (sx, sy), 1)
                prev = (sx, sy)
        elif progress < 0.7:
            # Heart pulled — beam back to boss
            t = (progress - 0.3) / 0.4
            # Heart position (starts at target, moves toward boss)
            heart_x = int(tx + (start_x - tx) * t)
            heart_y = int(ty + (start_y - ty) * t)

            # Connecting beam
            steps = 12
            prev = (start_x, start_y)
            for step in range(1, steps + 1):
                tt = step / steps
                sx = int(start_x + (heart_x - start_x) * tt)
                sy = int(start_y + (heart_y - start_y) * tt)
                perp_wave = math.sin(phase * 4 + tt * math.pi * 3) * 2
                sx += int(perp_wave * 0.3)
                sy += int(perp_wave)
                _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["heart_dark"],
                                     prev, (sx, sy), 3)
                _NS_vaelkorr._aaline(surface, _NS_vaelkorr.PALETTE["heart_mid"],
                                     prev, (sx, sy), 2)
                prev = (sx, sy)

            # Heart shape (pulsing)
            heart_pulse = math.sin(phase * 5) * 0.2 + 1.0
            hr = int(6 * heart_pulse)
            for r in range(hr + 4, 0, -1):
                alpha = _NS_vaelkorr._alpha(200 * (hr + 4 - r) / (hr + 4))
                _NS_vaelkorr._aacircle(surface, (*_NS_vaelkorr.PALETTE["heart_dark"], alpha),
                                       (heart_x, heart_y), r)
            _NS_vaelkorr._aacircle(surface, _NS_vaelkorr.PALETTE["heart_mid"],
                                   (heart_x, heart_y), hr - 1)
            _NS_vaelkorr._aacircle(surface, _NS_vaelkorr.PALETTE["heart_light"],
                                   (heart_x, heart_y), max(1, hr - 3))
            pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["heart_shine"],
                             (heart_x, heart_y, 2, 2))
            pygame.draw.rect(surface, _NS_vaelkorr.PALETTE["white"],
                             (heart_x, heart_y, 1, 1))
        else:
            # Absorption flash
            t = (progress - 0.7) / 0.3
            for r in range(int(25 * (1 - t)), 3, -2):
                alpha = _NS_vaelkorr._alpha(200 * (1 - t))
                _NS_vaelkorr._aacircle(surface, (*_NS_vaelkorr.PALETTE["heart_mid"], alpha),
                                       (start_x, start_y), r)
            _NS_vaelkorr._aacircle(surface, _NS_vaelkorr.PALETTE["heart_shine"],
                                   (start_x, start_y), int(6 * (1 - t)))


# ====================================================================
# ALIAS untuk convenience
# ====================================================================
draw_vaelkorr = _NS_vaelkorr.draw_vaelkorr


# ====================================================================================================
# AKIRAKUMO - TRUE BOSS
# ====================================================================================================

class _NS_akirakumo:
    """Namespace akirakumo - demon prince swordsman boss."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Pale demon skin (cool bluish-white)
        "skin_darkest": (65, 60, 75),
        "skin_dark": (135, 125, 145),
        "skin_mid": (195, 185, 205),
        "skin_light": (230, 220, 240),
        "skin_shine": (250, 245, 252),

        # Silver-white hair (long flowing)
        "hair_darkest": (85, 90, 110),
        "hair_dark": (145, 150, 170),
        "hair_mid": (200, 205, 220),
        "hair_light": (235, 238, 245),
        "hair_shine": (255, 255, 255),

        # White kimono (pure white with faint cool shadows)
        "kimono_darkest": (95, 95, 115),
        "kimono_dark": (160, 160, 180),
        "kimono_mid": (215, 215, 230),
        "kimono_light": (245, 245, 250),
        "kimono_shine": (255, 255, 255),

        # Red pattern (blood flowers/hexagons on kimono)
        "red_dark": (85, 15, 20),
        "red_mid": (185, 35, 40),
        "red_light": (240, 75, 75),
        "red_shine": (255, 140, 135),

        # Purple sash/obi
        "sash_dark": (35, 20, 65),
        "sash_mid": (85, 55, 145),
        "sash_light": (150, 115, 210),
        "sash_shine": (210, 185, 245),

        # Gold accents (rope belt, armor trim)
        "gold_dark": (95, 70, 15),
        "gold_mid": (200, 155, 45),
        "gold_light": (245, 210, 95),
        "gold_shine": (255, 240, 165),

        # Silver armor (shoulder guards)
        "armor_dark": (55, 60, 78),
        "armor_mid": (120, 128, 148),
        "armor_light": (200, 205, 220),
        "armor_shine": (245, 245, 255),

        # Fluffy mokomoko (white fur pelt over shoulder)
        "fur_darkest": (150, 155, 170),
        "fur_dark": (200, 205, 218),
        "fur_mid": (235, 238, 245),
        "fur_light": (250, 252, 255),
        "fur_shine": (255, 255, 255),

        # Katana blade (silvery)
        "blade_darkest": (25, 28, 38),
        "blade_dark": (75, 82, 100),
        "blade_mid": (155, 165, 190),
        "blade_light": (220, 225, 240),
        "blade_shine": (250, 250, 255),

        # Blue spiritual energy (Bakusaiga daggers)
        "spirit_darkest": (5, 15, 55),
        "spirit_dark": (25, 60, 145),
        "spirit_mid": (75, 150, 240),
        "spirit_light": (170, 215, 255),
        "spirit_hot": (220, 240, 255),
        "spirit_shine": (250, 253, 255),

        # Purple demon energy (Sokan, Meido)
        "demon_darkest": (15, 5, 40),
        "demon_dark": (60, 25, 115),
        "demon_mid": (140, 70, 220),
        "demon_light": (200, 145, 255),
        "demon_hot": (235, 195, 255),
        "demon_shine": (250, 235, 255),

        # Red demonic aura (Toukijin)
        "aura_darkest": (55, 5, 10),
        "aura_dark": (130, 20, 25),
        "aura_mid": (215, 45, 50),
        "aura_light": (255, 110, 100),
        "aura_hot": (255, 175, 165),

        # Golden eyes (demon prince)
        "eye_socket": (10, 8, 3),
        "eye_dark": (100, 70, 15),
        "eye_mid": (215, 165, 40),
        "eye_light": (250, 220, 95),
        "eye_glow": (255, 245, 175),
        "eye_pupil": (2, 2, 4),

        # Crescent moon mark (forehead)
        "moon_dark": (50, 15, 65),
        "moon_mid": (130, 55, 180),
        "moon_light": (200, 140, 245),

        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 4),
        "white": (255, 255, 255),
    }

    # ── helpers ──────────────────────────────────────────────
    def _clamp(c):
        return tuple(max(0, min(255, int(v))) for v in c)

    def _alpha(v):
        return max(0, min(255, int(v)))

    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_akirakumo._clamp(color)
        if _NS_akirakumo.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_akirakumo._clamp(color)
        if _NS_akirakumo.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_akirakumo._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 260 * getattr(boss, "direction", 1)), int(y)

    def _draw_crescent(surface, cx, cy, radius, thickness, color, alpha,
                       angle=0.0, arc_span=math.pi):
        if radius < 3:
            return
        seg = max(8, int(radius * 0.6))
        pts = []
        for i in range(seg + 1):
            t = i / seg
            a = angle - arc_span / 2 + t * arc_span
            pts.append((cx + int(math.cos(a) * radius),
                        cy + int(math.sin(a) * radius)))
        for i in range(len(pts) - 1):
            pygame.draw.line(surface,
                             (*color, _NS_akirakumo._alpha(alpha)),
                             pts[i], pts[i + 1], thickness)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_akirakumo(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_akirakumo._detect_moving(boss)
        _NS_akirakumo._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_akr_attack_active", False)
            or getattr(boss, "timer", 0)
            > getattr(boss, "attack_cooldown", 40) - 15
        )

        # Ambient behind
        _NS_akirakumo._draw_demon_aura(surface, x, y, pulse)
        _NS_akirakumo._draw_ground_ring(surface, x, y + 50, pulse, active_skill)

        # Skill ground FX
        if active_skill == "e":
            _NS_akirakumo._draw_toukijin_ground(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "r":
            _NS_akirakumo._draw_meido_ground(
                surface, boss, x, y, skill_timer, pulse
            )

        # Body
        if attacking:
            _NS_akirakumo._draw_attack_pose(surface, boss, x, y)
        elif moving:
            _NS_akirakumo._draw_walk_pose(surface, boss, x, y)
        else:
            _NS_akirakumo._draw_idle_pose(surface, boss, x, y)

        # Overlays on body
        if active_skill == "e":
            _NS_akirakumo._draw_toukijin_overlay(
                surface, boss, x, y, skill_timer, pulse
            )

        # Foreground skill FX
        if active_skill == "q":
            _NS_akirakumo._draw_sokan(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "w":
            _NS_akirakumo._draw_bakusaiga(
                surface, boss, x, y, skill_timer, pulse
            )
        elif active_skill == "r":
            _NS_akirakumo._draw_meido(
                surface, boss, x, y, skill_timer, pulse
            )

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cd = max(2, int(getattr(boss, "attack_cooldown", 40)))
        timer = int(getattr(boss, "timer", 0))
        prev = int(getattr(boss, "_akr_prev_timer", 0))
        active = bool(getattr(boss, "_akr_attack_active", False))
        if timer >= cd - 1 and prev <= 1:
            boss._akr_attack_active = True
            boss._akr_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._akr_attack_frame = int(
                getattr(boss, "_akr_attack_frame", 0)
            ) + 1
        elif timer <= 0:
            boss._akr_attack_active = False
            boss._akr_attack_frame = 0
            active = False
        boss._akr_prev_timer = timer
        boss._akr_attack_progress = (
            min(1.0, getattr(boss, "_akr_attack_frame", 0) / max(1, cd - 1))
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_akr_last_x"):
            boss._akr_last_x = boss.x
            boss._akr_last_y = boss.y
            return False
        dx = abs(boss.x - boss._akr_last_x)
        dy = abs(boss.y - boss._akr_last_y)
        boss._akr_last_x = boss.x
        boss._akr_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS (floating)
    # ============================================================
    def _draw_idle_pose(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.6) * 5)
        _NS_akirakumo._draw_shadow(surface, x, y + 52)
        _NS_akirakumo._draw_float_wisps(surface, x, y + 46, boss.pulse)
        _NS_akirakumo._draw_body(
            surface, x, y + bob, boss.direction, boss.pulse, "idle"
        )

    def _draw_walk_pose(surface, boss, x, y):
        ph = boss.pulse * 1.3
        bob = int(math.sin(ph * 1.0) * 6)
        sway = int(math.sin(ph * 0.7) * 3)
        _NS_akirakumo._draw_shadow(surface, x + sway, y + 52)
        _NS_akirakumo._draw_float_wisps(
            surface, x + sway, y + 46, ph, trail=True, facing=boss.direction
        )
        _NS_akirakumo._draw_body(
            surface, x + sway, y + bob, boss.direction, ph, "walk"
        )

    def _draw_attack_pose(surface, boss, x, y):
        progress = getattr(boss, "_akr_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 4)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            lunge = int((-4 + t * 18)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(14 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.6) * 2)
        _NS_akirakumo._draw_shadow(surface, x + lunge, y + 52)
        _NS_akirakumo._draw_float_wisps(
            surface, x + lunge, y + 46, boss.pulse, intense=True
        )
        _NS_akirakumo._draw_slash_trail(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )
        _NS_akirakumo._draw_body(
            surface, x + lunge, y - lift + bob, boss.direction,
            boss.pulse, "attack", progress,
        )
        _NS_akirakumo._draw_slash_impact(
            surface, boss, x + lunge, y - lift + bob, boss.direction, progress
        )

    # ============================================================
    # BODY COMPOSITION
    # ============================================================
    def _draw_body(surface, cx, cy, facing, phase, action, progress=0,
                   alpha=255):
        if alpha < 255:
            temp = pygame.Surface((220, 200), pygame.SRCALPHA)
            _NS_akirakumo._draw_body_parts(
                temp, 110, 110, facing, phase, action, progress
            )
            temp.set_alpha(alpha)
            surface.blit(temp, (cx - 110, cy - 110))
        else:
            _NS_akirakumo._draw_body_parts(
                surface, cx, cy, facing, phase, action, progress
            )

    def _draw_body_parts(surface, cx, cy, facing, phase, action, progress):
        # Order: long hair back -> back kimono trail -> back arm -> legs ->
        # kimono body -> mokomoko fur pelt -> sash -> head -> hair front ->
        # shoulder armor -> front arm+katana
        _NS_akirakumo._draw_hair_back(surface, cx, cy, facing, phase)
        _NS_akirakumo._draw_kimono_trail(surface, cx, cy, facing, phase, action)
        _NS_akirakumo._draw_back_arm(surface, cx, cy, facing, phase, action)
        _NS_akirakumo._draw_legs(surface, cx, cy, facing, phase, action)
        _NS_akirakumo._draw_kimono_body(surface, cx, cy, facing, phase)
        _NS_akirakumo._draw_kimono_pattern(surface, cx, cy, facing, phase)
        _NS_akirakumo._draw_sash(surface, cx, cy, facing, phase)
        _NS_akirakumo._draw_mokomoko(surface, cx, cy, facing, phase)
        _NS_akirakumo._draw_shoulder_armor(surface, cx, cy, facing, phase)
        _NS_akirakumo._draw_head(surface, cx, cy, facing, phase)
        _NS_akirakumo._draw_hair_front(surface, cx, cy, facing, phase)
        _NS_akirakumo._draw_front_arm_katana(
            surface, cx, cy, facing, phase, action, progress
        )

    # ── LEGS (kimono hakama) ─────────────────────────────────
    def _draw_legs(surface, cx, cy, facing, phase, action):
        sway = (
            math.sin(phase * 1.3) * 3
            if action == "walk"
            else math.sin(phase * 0.5) * 1.5
        )
        # Wide flowing kimono legs (mostly white with purple sash center)
        for side in (-1, 1):
            lx = cx + side * 6
            ly = cy + 14
            sw = int(sway * (1 if side > 0 else -1))
            hak = [
                (lx - 5, ly - 1), (lx + 5, ly - 1),
                (lx + 7 + sw, ly + 8),
                (lx + 8 + sw, ly + 14),
                (lx - 8 + sw, ly + 14),
                (lx - 7 + sw, ly + 8),
            ]
            _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 2) for p in hak])
            _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_darkest"], hak)
            _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_dark"], [
                (lx - 4, ly), (lx + 4, ly),
                (lx + 6 + sw, ly + 8), (lx + 7 + sw, ly + 13),
                (lx - 7 + sw, ly + 13), (lx - 6 + sw, ly + 8),
            ])
            _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_mid"], [
                (lx - 3, ly + 1), (lx + 3, ly + 1),
                (lx + 4 + sw, ly + 7), (lx + 5 + sw, ly + 12),
                (lx - 5 + sw, ly + 12), (lx - 4 + sw, ly + 7),
            ])
            _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_light"], [
                (lx - 2, ly + 2), (lx + 2, ly + 2),
                (lx + 2 + sw, ly + 10), (lx - 2 + sw, ly + 10),
            ])
            # Pleats
            for pleat_x in (-3, 0, 3):
                pygame.draw.line(surface,
                                 _NS_akirakumo.PALETTE["kimono_darkest"],
                                 (lx + pleat_x, ly + 1),
                                 (lx + pleat_x + sw, ly + 13), 1)
            # Bottom hem (light edge)
            pygame.draw.line(surface, _NS_akirakumo.PALETTE["kimono_shine"],
                             (lx - 7 + sw, ly + 13),
                             (lx + 7 + sw, ly + 13), 1)
            # White tabi socks
            _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_mid"], [
                (lx - 4 + sw, ly + 14), (lx + 4 + sw, ly + 14),
                (lx + 5 + sw + facing, ly + 17),
                (lx - 3 + sw + facing, ly + 17),
            ])
            _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_light"], [
                (lx - 3 + sw, ly + 15), (lx + 3 + sw, ly + 15),
                (lx + 4 + sw + facing, ly + 16),
            ])
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["kimono_shine"],
                             (lx + sw, ly + 15, 1, 1))

    # ── KIMONO BODY (white outer robe) ──────────────────────
    def _draw_kimono_body(surface, cx, cy, facing, phase):
        body = [
            (cx - 12, cy - 10), (cx - 7, cy - 13),
            (cx + 7, cy - 13), (cx + 12, cy - 10),
            (cx + 13, cy), (cx + 12, cy + 10),
            (cx + 7, cy + 14), (cx - 7, cy + 14),
            (cx - 12, cy + 10), (cx - 13, cy),
        ]
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in body])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_darkest"], body)
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_dark"], [
            (cx - 11, cy - 9), (cx - 6, cy - 12),
            (cx + 6, cy - 12), (cx + 11, cy - 9),
            (cx + 12, cy), (cx + 11, cy + 9),
            (cx + 6, cy + 13), (cx - 6, cy + 13),
            (cx - 11, cy + 9), (cx - 12, cy),
        ])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_mid"], [
            (cx - 9, cy - 7), (cx - 5, cy - 10),
            (cx + 5, cy - 10), (cx + 9, cy - 7),
            (cx + 10, cy), (cx + 9, cy + 6),
            (cx + 5, cy + 10), (cx - 5, cy + 10),
            (cx - 9, cy + 6), (cx - 10, cy),
        ])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_light"], [
            (cx - 6, cy - 5), (cx - 3, cy - 8),
            (cx + 3, cy - 8), (cx + 6, cy - 5),
            (cx + 7, cy), (cx + 6, cy + 4),
            (cx + 3, cy + 8), (cx - 3, cy + 8),
            (cx - 6, cy + 4), (cx - 7, cy),
        ])
        # Shiny highlight
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["kimono_shine"],
                         (cx - 2, cy - 6, 3, 2))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["kimono_shine"],
                         (cx - 4, cy - 3, 2, 1))
        # V-collar (crossed opening — inner darker)
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_darkest"], [
            (cx - 4, cy - 12), (cx, cy - 6),
            (cx + 4, cy - 12), (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_dark"], [
            (cx - 3, cy - 11), (cx, cy - 6),
            (cx + 3, cy - 11), (cx + 2, cy - 3),
            (cx - 2, cy - 3),
        ])
        # Red border trim on inner collar
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["red_dark"],
                         (cx - 4, cy - 12), (cx, cy - 6), 1)
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["red_dark"],
                         (cx + 4, cy - 12), (cx, cy - 6), 1)
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["red_mid"],
                         (cx - 3, cy - 11), (cx, cy - 6), 1)
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["red_mid"],
                         (cx + 3, cy - 11), (cx, cy - 6), 1)

    def _draw_kimono_pattern(surface, cx, cy, facing, phase):
        """Red flower/hexagon patterns on kimono."""
        # Flower motifs at hem and shoulders (like Sesshomaru's kimono)
        # Simplified as red dots/rosettes
        pattern_positions = [
            (facing * 6, -8),
            (facing * 8, -4),
            (facing * 9, 3),
            (facing * 7, 10),
            (facing * 4, 12),
            (-facing * 5, 11),
            (-facing * 8, 6),
            (-facing * 9, -1),
        ]
        for (dx, dy) in pattern_positions:
            fx = cx + dx
            fy = cy + dy
            # Small rosette (red flower)
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["red_dark"],
                             (fx - 1, fy - 1, 3, 3))
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["red_mid"],
                             (fx - 1, fy, 3, 1))
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["red_mid"],
                             (fx, fy - 1, 1, 3))
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["red_light"],
                             (fx, fy, 1, 1))

    def _draw_kimono_trail(surface, cx, cy, facing, phase, action):
        """Long white kimono trail flowing behind."""
        back = -facing
        base_x = cx + back * 7
        base_y = cy - 4
        seg = 8
        pts_t = []
        pts_b = []
        for i in range(seg + 1):
            t = i / seg
            sx = base_x - int(facing * t * 32)
            sy = base_y + int(t * 28) - int(t * t * 5)
            wave = math.sin(phase * 1.2 + t * math.pi * 1.4) * (3 + t * 5)
            sy += int(wave)
            w = int(6 * (1 - t * 0.35))
            pts_t.append((sx, sy - w))
            pts_b.append((sx, sy + w))
        full = pts_t + list(reversed(pts_b))
        if len(full) >= 3:
            _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                                [(p[0] + 1, p[1] + 2) for p in full])
            _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_darkest"], full)
            inner = pts_t[:-1] + list(reversed(pts_b[:-1]))
            if len(inner) >= 3:
                _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_dark"], inner)
            inner2 = pts_t[:-2] + list(reversed(pts_b[:-2]))
            if len(inner2) >= 3:
                _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_mid"], inner2)
        # Red trim edge
        for i in range(len(pts_t) - 1):
            a = _NS_akirakumo._alpha(220 * (1 - i / len(pts_t)))
            pygame.draw.line(surface,
                             (*_NS_akirakumo.PALETTE["red_dark"], a),
                             pts_b[i], pts_b[i + 1], 1)
        # Red flower on tail
        if len(pts_t) > 4:
            mid = pts_t[4]
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["red_dark"],
                             (mid[0] - 1, mid[1] + 3, 3, 3))
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["red_mid"],
                             (mid[0], mid[1] + 3, 1, 3))
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["red_mid"],
                             (mid[0] - 1, mid[1] + 4, 3, 1))
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["red_light"],
                             (mid[0], mid[1] + 4, 1, 1))

    # ── SASH / OBI (purple with gold rope) ───────────────────
    def _draw_sash(surface, cx, cy, facing, phase):
        # Wide purple sash
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                         (cx - 13, cy + 8, 26, 7))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["sash_dark"],
                         (cx - 13, cy + 8, 26, 6))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["sash_mid"],
                         (cx - 12, cy + 9, 24, 4))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["sash_light"],
                         (cx - 12, cy + 9, 24, 2))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["sash_shine"],
                         (cx - 10, cy + 9, 20, 1))
        # Gold rope belt over sash
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_dark"],
                         (cx - 13, cy + 11, 26, 2))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_mid"],
                         (cx - 12, cy + 11, 24, 1))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_light"],
                         (cx - 10, cy + 11, 20, 1))
        # Rope knot with tassels at front
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_dark"],
                         (cx - 3, cy + 8, 6, 8))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_mid"],
                         (cx - 2, cy + 9, 4, 6))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_light"],
                         (cx - 2, cy + 9, 4, 3))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_shine"],
                         (cx - 1, cy + 9, 2, 1))
        # Hanging tassels
        for side in (-1, 1):
            tsx = cx + side * 2
            for ty_off in (16, 19, 22):
                pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_mid"],
                                 (tsx, cy + ty_off, 1, 3))
                pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_light"],
                                 (tsx, cy + ty_off, 1, 1))

    # ── MOKOMOKO (fluffy fur pelt over right shoulder) ───────
    def _draw_mokomoko(surface, cx, cy, facing, phase):
        """Big fluffy white fur pelt/scarf around shoulder."""
        back = -facing
        base_x = cx + back * 5
        base_y = cy - 6
        # The mokomoko wraps over shoulder and drapes down back
        # Draw as big fluffy blob with multiple lumps
        breath = math.sin(phase * 0.5) * 1
        # Main body of fur (over shoulder)
        fur_pts = [
            (base_x - 8, base_y - 6),
            (base_x - 10, base_y - 2),
            (base_x - 9, base_y + 4),
            (base_x - 6, base_y + 9),
            (base_x - 2, base_y + 12 + int(breath)),
            (base_x + 3, base_y + 10),
            (base_x + 5, base_y + 4),
            (base_x + 4, base_y - 2),
            (base_x + 1, base_y - 6),
        ]
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in fur_pts])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["fur_darkest"], fur_pts)
        # Multi-lump fluffy texture
        fluff_lumps = [
            (base_x - 6, base_y - 4, 4),
            (base_x - 4, base_y + 1, 5),
            (base_x - 2, base_y + 6, 4),
            (base_x + 1, base_y + 3, 4),
            (base_x + 2, base_y - 3, 3),
            (base_x - 7, base_y + 2, 3),
            (base_x - 3, base_y + 10, 3),
        ]
        for (lx, ly, lr) in fluff_lumps:
            _NS_akirakumo._aacircle(surface,
                                    _NS_akirakumo.PALETTE["fur_dark"],
                                    (lx, ly), lr)
        for (lx, ly, lr) in fluff_lumps:
            _NS_akirakumo._aacircle(surface,
                                    _NS_akirakumo.PALETTE["fur_mid"],
                                    (lx - 1, ly - 1), max(1, lr - 1))
        # Highlights on top lumps
        for (lx, ly, lr) in fluff_lumps[:3]:
            _NS_akirakumo._aacircle(surface,
                                    _NS_akirakumo.PALETTE["fur_light"],
                                    (lx - 1, ly - 1), max(1, lr - 2))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["fur_shine"],
                         (base_x - 5, base_y - 3, 2, 1))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["fur_shine"],
                         (base_x - 3, base_y, 2, 1))
        # Small fluff detail (radial lines showing fur texture)
        for i in range(8):
            ang = i * math.pi / 4 + phase * 0.2
            lx = base_x - 4 + int(math.cos(ang) * 8)
            ly = base_y + 2 + int(math.sin(ang) * 6)
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["fur_dark"],
                             (lx, ly, 1, 1))

    # ── SHOULDER ARMOR (silver pauldron) ─────────────────────
    def _draw_shoulder_armor(surface, cx, cy, facing, phase):
        # Big armored shoulder pauldron on front side
        sx = cx + facing * 11
        sy = cy - 9
        # Curved armor plate
        armor_pts = [
            (sx - 5, sy + 5),
            (sx - 5, sy - 2),
            (sx - 2, sy - 5),
            (sx + 3, sy - 5),
            (sx + 6, sy - 2),
            (sx + 6, sy + 4),
        ]
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in armor_pts])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["armor_dark"], armor_pts)
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["armor_mid"], [
            (sx - 4, sy + 4),
            (sx - 4, sy - 1),
            (sx - 1, sy - 4),
            (sx + 2, sy - 4),
            (sx + 5, sy - 1),
            (sx + 5, sy + 3),
        ])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["armor_light"], [
            (sx - 3, sy + 2),
            (sx - 3, sy),
            (sx, sy - 3),
            (sx + 1, sy - 3),
            (sx + 4, sy),
            (sx + 4, sy + 2),
        ])
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["armor_shine"],
                         (sx - 1, sy - 2, 2, 1))
        # Gold trim on top edge
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["gold_dark"],
                         (sx - 2, sy - 5), (sx + 3, sy - 5), 1)
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["gold_mid"],
                         (sx - 1, sy - 5), (sx + 2, sy - 5), 1)
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_shine"],
                         (sx + 1, sy - 5, 1, 1))
        # Rivets
        for rvx in (-3, 3):
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_mid"],
                             (sx + rvx, sy + 2, 1, 1))
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_shine"],
                             (sx + rvx, sy + 2, 1, 1))

    # ── BACK ARM ─────────────────────────────────────────────
    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        back = -facing
        sx = cx + back * 11
        sy = cy - 8
        sway = math.sin(phase * 0.7) * 2
        ex = sx + back * 6
        ey = sy + 12 + int(sway)
        hx = ex + back * 3
        hy = ey + 8
        # Wide flowing white kimono sleeve
        sleeve_pts = [
            (sx - 4, sy), (sx + 4, sy),
            (ex + 5, ey), (ex + 6, ey + 6),
            (ex - 6, ey + 6), (ex - 5, ey),
        ]
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in sleeve_pts])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_darkest"], sleeve_pts)
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_dark"], [
            (sx - 3, sy + 1), (sx + 3, sy + 1),
            (ex + 4, ey), (ex + 5, ey + 5),
            (ex - 5, ey + 5), (ex - 4, ey),
        ])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_mid"], [
            (sx - 2, sy + 2), (sx + 2, sy + 2),
            (ex + 3, ey), (ex + 3, ey + 4),
            (ex - 3, ey + 4), (ex - 3, ey),
        ])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_light"], [
            (sx - 1, sy + 3), (sx + 1, sy + 3),
            (ex + 1, ey), (ex + 1, ey + 3),
            (ex - 1, ey + 3), (ex - 1, ey),
        ])
        # Sleeve edge (red trim)
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["red_dark"],
                         (ex - 6, ey + 6), (ex + 6, ey + 6), 1)
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["red_mid"],
                         (ex - 5, ey + 6), (ex + 5, ey + 6), 1)
        # Forearm (pale skin)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                              (ex + 1, ey + 7), (hx + 1, hy + 2), 5)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["skin_darkest"],
                              (ex, ey + 6), (hx, hy), 4)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["skin_dark"],
                              (ex, ey + 6), (hx, hy), 3)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["skin_mid"],
                              (ex, ey + 5), (hx, hy - 1), 1)
        # Fist
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                                (hx + 1, hy + 1), 3)
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["skin_darkest"],
                                (hx, hy), 3)
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["skin_dark"],
                                (hx, hy), 2)
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["skin_light"],
                         (hx - 1, hy - 1, 1, 1))

    # ── FRONT ARM + KATANA ───────────────────────────────────
    def _draw_front_arm_katana(surface, cx, cy, facing, phase, action, progress):
        base_angle = -math.pi / 6
        if action == "attack":
            if progress < 0.3:
                t = progress / 0.3
                base_angle = -math.pi / 6 - t * math.pi / 2.2
            elif progress < 0.55:
                t = (progress - 0.3) / 0.25
                base_angle = -math.pi / 6 - math.pi / 2.2 + t * (math.pi * 1.15)
            else:
                t = (progress - 0.55) / 0.45
                base_angle = -math.pi / 6 + (math.pi * 0.7 * (1 - t))
        else:
            base_angle += math.sin(phase * 0.5) * 0.08

        sx = cx + facing * 11
        sy = cy - 8
        arm_len = 18
        hx = sx + int(math.cos(base_angle) * arm_len) * facing
        hy = sy + int(math.sin(base_angle) * arm_len)
        ex = sx + int(math.cos(base_angle) * arm_len * 0.5) * facing
        ey = sy + int(math.sin(base_angle) * arm_len * 0.5) + 2

        # Wide kimono sleeve for upper arm
        sleeve_end_perp = base_angle + math.pi / 2
        sleeve_a_x = ex + int(math.cos(sleeve_end_perp) * 5)
        sleeve_a_y = ey + int(math.sin(sleeve_end_perp) * 5)
        sleeve_b_x = ex - int(math.cos(sleeve_end_perp) * 5)
        sleeve_b_y = ey - int(math.sin(sleeve_end_perp) * 5)
        sleeve_pts = [
            (sx - 4, sy), (sx + 4, sy),
            (sleeve_a_x, sleeve_a_y),
            (sleeve_b_x, sleeve_b_y),
        ]
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in sleeve_pts])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_darkest"], sleeve_pts)
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_dark"], [
            (sx - 3, sy + 1), (sx + 3, sy + 1),
            (int((sleeve_a_x + ex) / 2), int((sleeve_a_y + ey) / 2)),
            (int((sleeve_b_x + ex) / 2), int((sleeve_b_y + ey) / 2)),
        ])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_mid"], [
            (sx - 2, sy + 2), (sx + 2, sy + 2),
            (ex, ey - 1), (ex, ey + 1),
        ])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["kimono_light"], [
            (sx - 1, sy + 3), (sx + 1, sy + 3),
            (ex, ey), (ex, ey),
        ])
        # Red trim edge
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["red_dark"],
                         (sleeve_a_x, sleeve_a_y),
                         (sleeve_b_x, sleeve_b_y), 1)
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["red_mid"],
                         (sleeve_a_x, sleeve_a_y),
                         (sleeve_b_x, sleeve_b_y), 1)

        # Forearm (pale skin)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                              (ex + 1, ey + 2), (hx + 1, hy + 2), 6)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["skin_darkest"],
                              (ex, ey), (hx, hy), 5)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["skin_dark"],
                              (ex, ey), (hx, hy), 4)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["skin_mid"],
                              (ex, ey - 1), (hx, hy - 1), 2)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["skin_light"],
                              (ex, ey - 2), (hx, hy - 2), 1)

        # HAND
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                                (hx + 1, hy + 1), 4)
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["skin_darkest"],
                                (hx, hy), 4)
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["skin_dark"],
                                (hx, hy), 3)
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["skin_mid"],
                                (hx - 1, hy - 1), 2)
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["skin_light"],
                         (hx - 1, hy - 1, 1, 1))

        # Sharp demon claws on fingers
        for c_i, c_off in enumerate((-2, 0, 2)):
            cl_x = hx + int(math.cos(base_angle) * 3) * facing + c_off
            cl_y = hy + int(math.sin(base_angle) * 3) + c_i
            cl_tip_x = cl_x + int(math.cos(base_angle) * 2) * facing
            cl_tip_y = cl_y + int(math.sin(base_angle) * 2)
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["armor_light"],
                             (cl_tip_x, cl_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["armor_shine"],
                             (cl_tip_x, cl_tip_y, 1, 1))

        # KATANA (Tenseiga-style)
        _NS_akirakumo._draw_katana(surface, hx, hy, facing, phase, base_angle,
                                    action)

    def _draw_katana(surface, hx, hy, facing, phase, arm_angle, action):
        """Long silvery katana."""
        # Handle
        tsuka_len = 7
        tsuka_end_x = hx - int(math.cos(arm_angle) * tsuka_len) * facing
        tsuka_end_y = hy - int(math.sin(arm_angle) * tsuka_len)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                              (hx + 1, hy + 1),
                              (tsuka_end_x + 1, tsuka_end_y + 1), 4)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["sash_dark"],
                              (hx, hy), (tsuka_end_x, tsuka_end_y), 3)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["sash_mid"],
                              (hx, hy), (tsuka_end_x, tsuka_end_y), 2)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["sash_light"],
                              (hx, hy - 1), (tsuka_end_x, tsuka_end_y - 1), 1)
        # Handle wrap
        for i in range(1, tsuka_len):
            t = i / tsuka_len
            wx = int(hx + (tsuka_end_x - hx) * t)
            wy = int(hy + (tsuka_end_y - hy) * t)
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_dark"],
                             (wx, wy, 1, 2))
        # Pommel
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["gold_dark"],
                                (tsuka_end_x, tsuka_end_y), 2)
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["gold_mid"],
                                (tsuka_end_x, tsuka_end_y), 1)
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_shine"],
                         (tsuka_end_x, tsuka_end_y, 1, 1))

        # Tsuba
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                                (hx + 1, hy + 1), 4)
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["gold_dark"],
                                (hx, hy), 4)
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["gold_mid"],
                                (hx, hy), 3)
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["gold_light"],
                                (hx - 1, hy - 1), 2)
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["gold_shine"],
                         (hx - 1, hy - 1, 1, 1))

        # BLADE (silvery, long)
        blade_len = 32
        blade_tip_x = hx + int(math.cos(arm_angle) * blade_len) * facing
        blade_tip_y = hy + int(math.sin(arm_angle) * blade_len)
        blade_base_x = hx + int(math.cos(arm_angle) * 4) * facing
        blade_base_y = hy + int(math.sin(arm_angle) * 4)
        perp = arm_angle + math.pi / 2
        bw = 2
        bp1_x = blade_base_x + int(math.cos(perp) * bw)
        bp1_y = blade_base_y + int(math.sin(perp) * bw)
        bp2_x = blade_base_x - int(math.cos(perp) * bw)
        bp2_y = blade_base_y - int(math.sin(perp) * bw)
        blade_pts = [(blade_tip_x, blade_tip_y), (bp1_x, bp1_y),
                     (bp2_x, bp2_y)]
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in blade_pts])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["blade_darkest"], blade_pts)
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["blade_dark"], [
            (blade_tip_x, blade_tip_y),
            (int((bp1_x + blade_base_x) / 2),
             int((bp1_y + blade_base_y) / 2)),
            (blade_base_x, blade_base_y),
        ])
        # Bright edge
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["blade_mid"],
                              (blade_base_x, blade_base_y),
                              (blade_tip_x, blade_tip_y), 2)
        _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["blade_light"],
                              (blade_base_x, blade_base_y),
                              (blade_tip_x, blade_tip_y), 1)
        # Bright tip
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["blade_shine"],
                         (blade_tip_x, blade_tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["white"],
                         (blade_tip_x, blade_tip_y, 1, 1))
        # Spiritual glow at tip
        for r in range(4, 0, -1):
            a = _NS_akirakumo._alpha(120 * (4 - r) / 4)
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["spirit_mid"], a),
                                    (blade_tip_x, blade_tip_y), r)

    # ── HEAD ─────────────────────────────────────────────────
    def _draw_head(surface, cx, cy, facing, phase):
        hx = cx + facing * 2
        hy = cy - 20
        head_pts = [
            (hx - 7, hy + 5), (hx - 8, hy - 1), (hx - 6, hy - 7),
            (hx - 1, hy - 9), (hx + 4, hy - 9), (hx + 7, hy - 6),
            (hx + 8, hy), (hx + 7, hy + 5), (hx + 4, hy + 7),
            (hx - 1, hy + 7), (hx - 5, hy + 6),
        ]
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 2) for p in head_pts])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["skin_darkest"], head_pts)
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["skin_dark"], [
            (hx - 6, hy + 4), (hx - 7, hy), (hx - 5, hy - 6),
            (hx, hy - 8), (hx + 3, hy - 8), (hx + 6, hy - 5),
            (hx + 7, hy), (hx + 6, hy + 4), (hx + 3, hy + 6),
            (hx, hy + 6), (hx - 4, hy + 5),
        ])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["skin_mid"], [
            (hx - 5, hy - 3), (hx - 3, hy - 6),
            (hx + 2, hy - 6), (hx + 5, hy - 3),
            (hx + 6, hy), (hx + 4, hy + 3),
            (hx - 1, hy + 3), (hx - 5, hy),
        ])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["skin_light"], [
            (hx - 2, hy - 5), (hx + 2, hy - 5),
            (hx + 3, hy - 3), (hx - 3, hy - 3),
        ])
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["skin_shine"],
                         (hx, hy - 5, 2, 1))

        # DEMON FACE MARKS (magenta/purple stripes on cheeks — 2 per side)
        for side in (-1, 1):
            for stripe_i in range(2):
                sx1 = hx + side * (3 + stripe_i)
                sy1 = hy + 1
                sx2 = hx + side * (5 + stripe_i)
                sy2 = hy + 4
                pygame.draw.line(surface,
                                 _NS_akirakumo.PALETTE["moon_dark"],
                                 (sx1, sy1), (sx2, sy2), 1)
                pygame.draw.line(surface,
                                 _NS_akirakumo.PALETTE["moon_mid"],
                                 (sx1, sy1 + 1), (sx2, sy2 + 1), 1)

        # CRESCENT MOON MARK on forehead (blue-purple)
        # Small crescent centered
        moon_x = hx
        moon_y = hy - 6
        _NS_akirakumo._draw_crescent(
            surface, moon_x, moon_y, 3, 1,
            _NS_akirakumo.PALETTE["moon_dark"], 255,
            angle=-math.pi / 2, arc_span=math.pi * 0.9,
        )
        _NS_akirakumo._draw_crescent(
            surface, moon_x, moon_y, 3, 1,
            _NS_akirakumo.PALETTE["moon_mid"], 255,
            angle=-math.pi / 2, arc_span=math.pi * 0.8,
        )
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["moon_light"],
                         (moon_x - 2, moon_y - 1, 1, 1))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["moon_light"],
                         (moon_x + 1, moon_y - 1, 1, 1))

        # Nose
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["skin_darkest"],
                         (hx + facing * 1, hy - 1, 1, 3))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["skin_dark"],
                         (hx + facing * 2, hy + 1, 1, 1))
        # Mouth (serious)
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["skin_darkest"],
                         (hx + facing * 1, hy + 4),
                         (hx + facing * 4, hy + 4), 1)
        # Pointed demon ears
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["skin_darkest"], [
            (hx - facing * 7, hy - 2),
            (hx - facing * 10, hy - 4),
            (hx - facing * 8, hy),
        ])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["skin_dark"], [
            (hx - facing * 7, hy - 1),
            (hx - facing * 9, hy - 3),
            (hx - facing * 7, hy + 1),
        ])
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["skin_mid"],
                         (hx - facing * 8, hy - 2, 1, 1))

        # GOLDEN EYES
        _NS_akirakumo._draw_gold_eye(surface, hx + facing * 3, hy - 2,
                                      facing, phase)
        _NS_akirakumo._draw_gold_eye(surface, hx - facing * 2, hy - 1,
                                      facing, phase, small=True)

    def _draw_gold_eye(surface, ex, ey, facing, phase, small=False):
        """Golden demon eye with vertical slit pupil."""
        pulse = math.sin(phase * 2.5) * 0.25 + 0.75
        w = 3 if small else 4
        h = 2 if small else 3
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                         (ex - w // 2, ey - 1, w, h))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["eye_socket"],
                         (ex - w // 2 + 1, ey - 1, w - 1, h))
        for r in range(4, 0, -1):
            a = _NS_akirakumo._alpha(80 * (4 - r) / 4 * pulse)
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["eye_mid"], a),
                                    (ex, ey), r)
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["eye_dark"],
                         (ex - w // 2 + 1, ey - 1, w - 1, h))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["eye_mid"],
                         (ex, ey - 1, w - 2, h))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["eye_light"],
                         (ex + 1, ey, w - 3, 1))
        # Vertical slit pupil
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["eye_pupil"],
                         (ex, ey - 1), (ex, ey + h - 2), 1)
        # Hot spot
        if not small:
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["eye_glow"],
                             (ex + 1, ey - 1, 1, 1))

    # ── HAIR (silver-white long flowing) ─────────────────────
    def _draw_hair_back(surface, cx, cy, facing, phase):
        hx = cx + facing * 2
        hy = cy - 20
        strands = [
            (-5, -6, 0.0, 38, 6),
            (-3, -8, 0.3, 42, 7),
            (-1, -9, 0.6, 44, 7),
            (1, -9, 0.9, 43, 7),
            (3, -8, 1.2, 40, 6),
            (5, -6, 1.5, 36, 5),
            (-6, -3, 0.4, 32, 5),
            (6, -3, 1.6, 30, 4),
            (-4, -1, 0.8, 36, 5),
            (4, -1, 1.8, 34, 4),
            (-2, 2, 0.2, 40, 5),
            (2, 2, 1.4, 38, 5),
        ]
        for (ox, oy, ph_off, length, base_w) in strands:
            pts = []
            seg = 9
            for j in range(seg + 1):
                t = j / seg
                sx = hx + ox - int(facing * t * length * 0.4)
                sy = hy + oy + int(t * length * 0.85)
                wave = math.sin(phase * 1.0 + ph_off + t * math.pi * 1.6)
                sx += int(wave * (2 + t * 6)) * (-facing)
                sy += int(math.sin(phase * 0.7 + ph_off + t) * 2)
                pts.append((sx, sy))
            for j in range(len(pts) - 1):
                thick = max(1, base_w - j // 2)
                _NS_akirakumo._aaline(surface,
                                      _NS_akirakumo.PALETTE["shadow_deep"],
                                      (pts[j][0] + 1, pts[j][1] + 1),
                                      (pts[j + 1][0] + 1, pts[j + 1][1] + 1),
                                      thick + 1)
                _NS_akirakumo._aaline(surface,
                                      _NS_akirakumo.PALETTE["hair_darkest"],
                                      pts[j], pts[j + 1], thick)
                _NS_akirakumo._aaline(surface,
                                      _NS_akirakumo.PALETTE["hair_dark"],
                                      pts[j], pts[j + 1], max(1, thick - 1))
                if thick > 2:
                    _NS_akirakumo._aaline(surface,
                                          _NS_akirakumo.PALETTE["hair_mid"],
                                          (pts[j][0], pts[j][1] - 1),
                                          (pts[j + 1][0], pts[j + 1][1] - 1),
                                          max(1, thick - 3))
                if thick > 4:
                    _NS_akirakumo._aaline(surface,
                                          _NS_akirakumo.PALETTE["hair_light"],
                                          (pts[j][0], pts[j][1] - 2),
                                          (pts[j + 1][0], pts[j + 1][1] - 2),
                                          1)
                if thick > 5:
                    pygame.draw.rect(surface, _NS_akirakumo.PALETTE["hair_shine"],
                                     (pts[j][0], pts[j][1] - 3, 1, 1))

    def _draw_hair_front(surface, cx, cy, facing, phase):
        hx = cx + facing * 2
        hy = cy - 20
        bangs = [
            (-4, -7, 0.0, 7),
            (-1, -8, 0.3, 9),
            (2, -8, 0.6, 9),
            (5, -6, 0.9, 7),
            (-6, -5, 1.2, 6),
        ]
        for (ox, oy, ph_off, length) in bangs:
            bx = hx + ox
            by = hy + oy
            sway = math.sin(phase * 0.7 + ph_off) * 1
            tip_x = bx + int((facing * 1) + sway)
            tip_y = by + length
            _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["hair_darkest"],
                                  (bx, by), (tip_x, tip_y), 3)
            _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["hair_dark"],
                                  (bx, by), (tip_x, tip_y), 2)
            _NS_akirakumo._aaline(surface, _NS_akirakumo.PALETTE["hair_mid"],
                                  (bx, by - 1), (tip_x, tip_y - 1), 1)
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["hair_light"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["hair_shine"],
                             (tip_x, tip_y, 1, 1))

    # ============================================================
    # BASIC ATTACK — SLASH TRAIL + IMPACT
    # ============================================================
    def _get_katana_tip(cx, cy, facing, progress):
        if progress < 0.3:
            t = progress / 0.3
            angle = -math.pi / 6 - t * math.pi / 2.2
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            angle = -math.pi / 6 - math.pi / 2.2 + t * (math.pi * 1.15)
        else:
            t = (progress - 0.55) / 0.45
            angle = -math.pi / 6 + (math.pi * 0.7 * (1 - t))
        sx = cx + facing * 11
        sy = cy - 8
        arm_len = 18
        hx = sx + int(math.cos(angle) * arm_len) * facing
        hy = sy + int(math.sin(angle) * arm_len)
        blade_len = 32
        tip_x = hx + int(math.cos(angle) * blade_len) * facing
        tip_y = hy + int(math.sin(angle) * blade_len)
        return tip_x, tip_y, angle

    def _draw_slash_trail(surface, boss, cx, cy, facing, progress):
        """White-blue spiritual slash trail."""
        if progress < 0.28 or progress > 0.7:
            return
        if progress < 0.32:
            intensity = (progress - 0.28) / 0.04
        elif progress < 0.55:
            intensity = 1.0
        else:
            intensity = max(0, 1 - (progress - 0.55) / 0.15)
        intensity = max(0.0, min(1.0, intensity))
        if intensity <= 0:
            return
        num = 14
        trail = []
        for i in range(num):
            sp = progress - (i / num) * 0.22
            if sp < 0.28:
                continue
            tx, ty, ang = _NS_akirakumo._get_katana_tip(cx, cy, facing, sp)
            trail.append((tx, ty, ang, i))
        if len(trail) < 2:
            return
        trail.reverse()
        ts = pygame.Surface((320, 320), pygame.SRCALPHA)
        ox = cx - 160
        oy = cy - 160
        layers = [
            (_NS_akirakumo.PALETTE["spirit_darkest"], 14, 100),
            (_NS_akirakumo.PALETTE["spirit_dark"], 10, 150),
            (_NS_akirakumo.PALETTE["spirit_mid"], 6, 200),
            (_NS_akirakumo.PALETTE["spirit_light"], 3, 240),
            (_NS_akirakumo.PALETTE["spirit_shine"], 1, 255),
        ]
        for color, max_w, max_a in layers:
            for i in range(len(trail) - 1):
                p1, p2 = trail[i], trail[i + 1]
                fade = 1.0 - (p1[3] / num)
                a = _NS_akirakumo._alpha(max_a * fade * intensity)
                w = max(1, int(max_w * fade))
                if a > 0:
                    pygame.draw.line(
                        ts, (*color, a),
                        (p1[0] - ox, p1[1] - oy),
                        (p2[0] - ox, p2[1] - oy), w,
                    )
        # Sparkles
        for i, (tx, ty, ang, idx) in enumerate(trail):
            fade = 1.0 - (idx / num)
            a = _NS_akirakumo._alpha(230 * fade * intensity)
            if a <= 0 or i % 2 == 0:
                continue
            perp = ang + math.pi / 2
            for s in range(2):
                d = 4 + s * 3
                sign = 1 if s == 0 else -1
                spx = tx - ox + int(math.cos(perp) * d * sign)
                spy = ty - oy + int(math.sin(perp) * d * sign)
                pygame.draw.rect(ts, (*_NS_akirakumo.PALETTE["spirit_hot"], a),
                                 (spx, spy, 2, 2))
                pygame.draw.rect(ts, (*_NS_akirakumo.PALETTE["white"], a),
                                 (spx, spy, 1, 1))
        surface.blit(ts, (ox, oy))
        if trail:
            lead = trail[0]
            for r in range(10, 2, -2):
                a = _NS_akirakumo._alpha(160 * (10 - r) / 10 * intensity)
                _NS_akirakumo._aacircle(
                    surface, (*_NS_akirakumo.PALETTE["spirit_mid"], a),
                    (lead[0], lead[1]), r,
                )
            _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["spirit_hot"],
                                    (lead[0], lead[1]), 3)
            _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["white"],
                                    (lead[0], lead[1]), 1)

    def _draw_slash_impact(surface, boss, cx, cy, facing, progress):
        if progress < 0.5 or progress > 0.7:
            return
        t = (progress - 0.5) / 0.2
        inten = math.sin(t * math.pi)
        tx, ty, ang = _NS_akirakumo._get_katana_tip(cx, cy, facing, progress)
        ix = tx + facing * 4
        iy = ty
        r = int(6 + t * 15)
        a = _NS_akirakumo._alpha(255 * inten)
        for rr in range(r + 4, 0, -2):
            ra = _NS_akirakumo._alpha(a * (r + 4 - rr) / (r + 4))
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["spirit_darkest"], ra),
                                    (ix, iy), rr)
        _NS_akirakumo._aacircle(surface,
                                (*_NS_akirakumo.PALETTE["spirit_dark"], a),
                                (ix, iy), max(2, r - 3))
        _NS_akirakumo._aacircle(surface,
                                (*_NS_akirakumo.PALETTE["spirit_mid"], a),
                                (ix, iy), max(1, r - 7))
        _NS_akirakumo._aacircle(surface,
                                (*_NS_akirakumo.PALETTE["spirit_light"], a),
                                (ix, iy), max(1, r - 10))
        _NS_akirakumo._aacircle(surface,
                                (*_NS_akirakumo.PALETTE["spirit_hot"], a),
                                (ix, iy), max(1, r - 13))
        pygame.draw.rect(surface, (*_NS_akirakumo.PALETTE["white"], a),
                         (ix, iy, 1, 1))
        # Radial slash lines
        for i in range(6):
            slash_ang = ang + (i - 2.5) * 0.2
            sx1 = ix - int(math.cos(slash_ang) * r * 0.5) * facing
            sy1 = iy - int(math.sin(slash_ang) * r * 0.5)
            sx2 = ix + int(math.cos(slash_ang) * r) * facing
            sy2 = iy + int(math.sin(slash_ang) * r)
            for w, color, wa in [
                (3, _NS_akirakumo.PALETTE["spirit_dark"], 200),
                (2, _NS_akirakumo.PALETTE["spirit_mid"], 240),
                (1, _NS_akirakumo.PALETTE["white"], 255),
            ]:
                la = _NS_akirakumo._alpha(wa * inten)
                pygame.draw.line(surface, (*color, la),
                                 (sx1, sy1), (sx2, sy2), w)
        # Sparks
        for i in range(10):
            sa = i * math.pi / 5 + progress * 4
            dist = int(r * 1.3)
            ex = ix + int(math.cos(sa) * dist)
            ey = iy + int(math.sin(sa) * dist)
            pygame.draw.rect(surface,
                             (*_NS_akirakumo.PALETTE["spirit_hot"], a),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_akirakumo.PALETTE["white"], a),
                             (ex, ey, 1, 1))

    # ============================================================
    # AMBIENT / FLOATING FX
    # ============================================================
    def _draw_shadow(surface, x, y):
        sh = pygame.Surface((150, 28), pygame.SRCALPHA)
        for r in range(14, 0, -1):
            a = max(0, (14 - r) * 16)
            pygame.draw.ellipse(sh, (0, 0, 0, a),
                                (10 - r, 14 - r, 130 + r * 2, r * 2))
        pygame.draw.ellipse(sh, (10, 8, 15, 170), (8, 8, 134, 12))
        surface.blit(sh, (x - 75, y - 14))

    def _draw_demon_aura(surface, x, y, phase):
        pulse = math.sin(phase * 0.4) * 0.25 + 0.75
        aura = pygame.Surface((240, 200), pygame.SRCALPHA)
        for r in range(90, 5, -5):
            a = _NS_akirakumo._alpha((90 - r) * 0.9 * pulse)
            if a > 0:
                _NS_akirakumo._aacircle(aura,
                                        (*_NS_akirakumo.PALETTE["sash_dark"], a),
                                        (120, 100), r)
        for r in range(50, 5, -3):
            a = _NS_akirakumo._alpha((50 - r) * 1.1 * pulse)
            if a > 0:
                _NS_akirakumo._aacircle(aura,
                                        (*_NS_akirakumo.PALETTE["demon_dark"], a),
                                        (120, 100), r)
        surface.blit(aura, (x - 120, y - 100))
        # Floating cherry blossoms (sakura petals — pink)
        for i in range(8):
            ang = phase * 0.3 + i * math.pi / 4
            rd = 45 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(ang) * rd)
            sy = y - 5 + int(math.sin(ang) * rd * 0.45)
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["red_mid"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["red_light"],
                             (sx, sy, 1, 1))
        # White light motes
        for i in range(8):
            ang = phase * 0.5 + i * math.pi / 4 + 1.0
            rd = 40 + int(math.sin(phase * 1.5 + i) * 10)
            sx = x + int(math.cos(ang) * rd)
            sy = y - 5 + int(math.sin(ang) * rd * 0.4)
            pygame.draw.rect(surface, _NS_akirakumo.PALETTE["kimono_shine"],
                             (sx, sy, 1, 1))

    def _draw_float_wisps(surface, cx, cy, phase, trail=False, facing=1,
                          intense=False):
        strength = 1.4 if intense else 1.0
        mist = pygame.Surface((140, 34), pygame.SRCALPHA)
        p = math.sin(phase * 1.2) * 0.25 + 0.75
        for r in range(22, 3, -2):
            a = _NS_akirakumo._alpha((22 - r) * 3 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_akirakumo.PALETTE["sash_dark"], a),
                    (70 - r * 2, 17 - r // 3, r * 4, max(3, r // 2)),
                )
        for r in range(14, 3, -2):
            a = _NS_akirakumo._alpha((14 - r) * 4 * p * strength)
            if a > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_akirakumo.PALETTE["demon_dark"], a),
                    (70 - r, 17 - r // 4, r * 2, max(2, r // 3)),
                )
        surface.blit(mist, (cx - 70, cy - 10))
        # Rising motes
        for i in range(6):
            t = (phase * 0.5 + i * 0.16) % 1.0
            sx = cx - 18 + i * 7 + int(math.sin(phase + i) * 3)
            sy = cy - int(t * 18)
            a = _NS_akirakumo._alpha(200 * (1 - t) * strength)
            if a > 0:
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["sash_mid"], a),
                                        (sx, sy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_akirakumo.PALETTE["sash_light"], a),
                                 (sx, sy, 1, 1))
        # Cherry blossoms falling
        for i in range(4):
            t = (phase * 0.4 + i * 0.25) % 1.0
            sx = cx - 20 + i * 12 + int(math.sin(phase * 1.5 + i) * 4)
            sy = cy - 5 - int(t * 25)
            a = _NS_akirakumo._alpha(220 * (1 - t) * strength)
            if a > 0:
                pygame.draw.rect(surface,
                                 (*_NS_akirakumo.PALETTE["red_mid"], a),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_akirakumo.PALETTE["red_light"], a),
                                 (sx, sy, 1, 1))
        if trail:
            for i in range(5):
                sx = cx - (i + 1) * 10 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                a = _NS_akirakumo._alpha(140 - i * 25)
                if a > 0:
                    _NS_akirakumo._aacircle(
                        surface, (*_NS_akirakumo.PALETTE["kimono_dark"], a),
                        (sx, sy), max(2, 5 - i),
                    )

    def _draw_ground_ring(surface, x, y, phase, skill):
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 46), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_akirakumo.PALETTE["sash_dark"], 180),
                            (5, 14, 170, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_akirakumo.PALETTE["demon_dark"], 210),
                            (15, 16, 150, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_akirakumo.PALETTE["sash_mid"], 190),
                            (25, 18, 130, 16), 1)
        for i in range(10):
            ang = phase * 0.3 + i * math.pi / 5
            x1 = 90 + int(math.cos(ang) * 48)
            y1 = 25 + int(math.sin(ang) * 8)
            x2 = 90 + int(math.cos(ang) * 74)
            y2 = 25 + int(math.sin(ang) * 12)
            pygame.draw.line(ring, (*_NS_akirakumo.PALETTE["demon_light"], 200),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(
                ring, (*_NS_akirakumo.PALETTE["demon_hot"],
                       _NS_akirakumo._alpha(150 * pulse)),
                (10, 8, 160, 32), 1,
            )
        surface.blit(ring, (x - 90, y - 23))

    # ============================================================
    # SKILL Q — SOKAN (crescent energy wave)
    # ============================================================
    def _draw_sokan(surface, boss, x, y, timer, phase):
        """Purple crescent wave flying toward target."""
        facing = boss.direction
        duration = 45
        progress = 1 - timer / duration
        progress = max(0.0, min(1.0, progress))
        tx, ty = _NS_akirakumo._target_position(boss, x, y)
        if progress < 0.15:
            t = progress / 0.15
            cx_c = x + facing * 25
            cy_c = y - 5
            for r in range(int(8 * t) + 3, 0, -1):
                a = _NS_akirakumo._alpha(200 * (8 * t + 3 - r) / (8 * t + 3))
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["demon_dark"], a),
                                        (cx_c, cy_c), r)
            return
        t = (progress - 0.15) / 0.85
        t = min(1.0, t)
        start_x = x + facing * 30
        start_y = y - 5
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Trail
        for i in range(8):
            trail_t = max(0.0, t - i * 0.06)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            a = _NS_akirakumo._alpha(200 - i * 22)
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["demon_darkest"], a),
                                    (px, py), max(2, 8 - i))
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["demon_dark"], a),
                                    (px, py), max(1, 6 - i))
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["demon_mid"], a),
                                    (px, py), max(1, 4 - i))
        # Big crescent projectile
        cr_r = 15
        for cr_layer, (w, color, wa) in enumerate([
            (5, _NS_akirakumo.PALETTE["demon_darkest"], 120),
            (3, _NS_akirakumo.PALETTE["demon_dark"], 180),
            (2, _NS_akirakumo.PALETTE["demon_mid"], 220),
            (1, _NS_akirakumo.PALETTE["demon_hot"], 255),
        ]):
            _NS_akirakumo._draw_crescent(
                surface, bx, by, cr_r, w, color, wa,
                angle=0 if facing > 0 else math.pi,
                arc_span=math.pi * 1.2,
            )
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["demon_hot"],
                                (bx, by), 3)
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["white"],
                                (bx, by), 1)
        # Impact
        if t > 0.88:
            st = (t - 0.88) / 0.12
            r = int(15 + st * 20)
            a = _NS_akirakumo._alpha(255 * (1 - st))
            for rr in range(r + 3, 0, -2):
                ra = _NS_akirakumo._alpha(a * (r + 3 - rr) / (r + 3))
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["demon_dark"], ra),
                                        (tx, ty), rr)
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["demon_mid"], a),
                                    (tx, ty), max(1, r - 5))
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["demon_hot"], a),
                                    (tx, ty), max(1, r - 10))
            for i in range(6):
                ang = i * math.pi / 3 + st * 3
                cx_i = tx + int(math.cos(ang) * r * 1.2)
                cy_i = ty + int(math.sin(ang) * r * 1.2)
                _NS_akirakumo._draw_crescent(
                    surface, cx_i, cy_i, 4, 1,
                    _NS_akirakumo.PALETTE["demon_hot"], a,
                    angle=ang,
                )

    # ============================================================
    # SKILL W — BAKUSAIGA (multiple spirit daggers)
    # ============================================================
    def _draw_bakusaiga(surface, boss, x, y, timer, phase):
        """Many blue spiritual daggers flying at target."""
        facing = boss.direction
        duration = 55
        progress = 1 - timer / duration
        progress = max(0.0, min(1.0, progress))
        tx, ty = _NS_akirakumo._target_position(boss, x, y)
        if progress < 0.15:
            return
        t = (progress - 0.15) / 0.85
        t = min(1.0, t)
        num = 10
        start_x = x + facing * 30
        start_y = y - 5
        base_dist = math.hypot(tx - start_x, ty - start_y)
        base_ang = math.atan2(ty - start_y, tx - start_x)
        spread = math.pi / 5
        for d_i in range(num):
            ang_off = (d_i - (num - 1) / 2) * (spread / num)
            d_ang = base_ang + ang_off
            d_start = d_i * 0.03
            d_t = max(0.0, min(1.0, (t - d_start) / max(0.01, 1 - d_start)))
            if d_t <= 0:
                continue
            travel = base_dist * 1.1
            dx = int(start_x + math.cos(d_ang) * travel * d_t)
            dy = int(start_y + math.sin(d_ang) * travel * d_t)
            # Trail
            for ti in range(5):
                tt = max(0.0, d_t - ti * 0.06)
                px = int(start_x + math.cos(d_ang) * travel * tt)
                py = int(start_y + math.sin(d_ang) * travel * tt)
                a = _NS_akirakumo._alpha(200 - ti * 30)
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["spirit_dark"], a),
                                        (px, py), max(1, 4 - ti))
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["spirit_mid"], a),
                                        (px, py), max(1, 3 - ti))
            # Dagger shape (elongated diamond)
            _NS_akirakumo._draw_spirit_dagger(surface, dx, dy, d_ang)
            # Aura
            for r in range(6, 2, -1):
                a = _NS_akirakumo._alpha(100 * (6 - r) / 6)
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["spirit_mid"], a),
                                        (dx, dy), r)
            # Impact per dagger
            if d_t > 0.9:
                impact_x = tx + int((d_i - 4.5) * 8)
                impact_y = ty + int((d_i % 3 - 1) * 5)
                st = (d_t - 0.9) / 0.1
                r = int(6 + st * 10)
                a = _NS_akirakumo._alpha(220 * (1 - st))
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["spirit_dark"], a),
                                        (impact_x, impact_y), r, 2)
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["spirit_mid"], a),
                                        (impact_x, impact_y), max(1, r - 3))
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["spirit_hot"], a),
                                        (impact_x, impact_y), max(1, r - 5))
                pygame.draw.rect(surface,
                                 (*_NS_akirakumo.PALETTE["white"], a),
                                 (impact_x, impact_y, 1, 1))

    def _draw_spirit_dagger(surface, dx, dy, angle):
        """Elongated diamond/dagger shape."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        length = 10
        width = 2
        tip_x = dx + int(cos_a * length * 0.6)
        tip_y = dy + int(sin_a * length * 0.6)
        back_x = dx - int(cos_a * length * 0.4)
        back_y = dy - int(sin_a * length * 0.4)
        perp_x = -sin_a
        perp_y = cos_a
        pts = [
            (tip_x, tip_y),
            (dx + int(perp_x * width), dy + int(perp_y * width)),
            (back_x, back_y),
            (dx - int(perp_x * width), dy - int(perp_y * width)),
        ]
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["shadow_deep"],
                            [(p[0] + 1, p[1] + 1) for p in pts])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["spirit_darkest"], pts)
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["spirit_dark"], [
            (tip_x, tip_y),
            (int((dx + tip_x) / 2 + perp_x), int((dy + tip_y) / 2 + perp_y)),
            (back_x, back_y),
            (int((dx + tip_x) / 2 - perp_x), int((dy + tip_y) / 2 - perp_y)),
        ])
        _NS_akirakumo._poly(surface, _NS_akirakumo.PALETTE["spirit_mid"], [
            (tip_x, tip_y), (dx, dy), (back_x, back_y),
        ])
        # Bright core
        pygame.draw.line(surface, _NS_akirakumo.PALETTE["spirit_light"],
                         (back_x, back_y), (tip_x, tip_y), 1)
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["spirit_shine"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_akirakumo.PALETTE["white"],
                         (tip_x, tip_y, 1, 1))

    # ============================================================
    # SKILL E — TOUKIJIN (red demonic aura buff)
    # ============================================================
    def _draw_toukijin_ground(surface, boss, x, y, timer, phase):
        """Red flame rings under boss."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(35 + i * 8 + math.sin(phase * 2) * 3)
            a = _NS_akirakumo._alpha(200 - i * 60)
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["aura_dark"], a),
                                    (x, y + 45), r, 2)
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["aura_mid"], a),
                                    (x, y + 45), r, 1)

    def _draw_toukijin_overlay(surface, boss, x, y, timer, phase):
        """Red flame aura around body."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        breath = math.sin(phase * 2) * 3
        r = 50 + int(breath)
        aura = pygame.Surface((r * 2 + 30, r * 2 + 30), pygame.SRCALPHA)
        center = (r + 15, r + 15)
        # Flame-shaped aura (multiple layers)
        for i, (thick, av) in enumerate([(3, 100), (2, 160), (1, 220)]):
            _NS_akirakumo._aacircle(aura,
                                    (*_NS_akirakumo.PALETTE["aura_darkest"], av),
                                    center, r - i, thick)
            _NS_akirakumo._aacircle(aura,
                                    (*_NS_akirakumo.PALETTE["aura_dark"], av),
                                    center, r - i - 1, 1)
        # Rising flame tongues (like Toukijin visual)
        for i in range(16):
            fl_ang = phase * 1.5 + i * math.pi / 8
            fl_len = int(8 + math.sin(phase * 3 + i) * 4)
            fl_base_x = center[0] + int(math.cos(fl_ang) * r)
            fl_base_y = center[1] + int(math.sin(fl_ang) * r)
            fl_tip_x = center[0] + int(math.cos(fl_ang) * (r + fl_len))
            fl_tip_y = center[1] + int(math.sin(fl_ang) * (r + fl_len))
            # Flame layers
            for w, color, wa in [
                (3, _NS_akirakumo.PALETTE["aura_dark"], 180),
                (2, _NS_akirakumo.PALETTE["aura_mid"], 220),
                (1, _NS_akirakumo.PALETTE["aura_light"], 255),
            ]:
                pygame.draw.line(aura, (*color, wa),
                                 (fl_base_x, fl_base_y),
                                 (fl_tip_x, fl_tip_y), w)
            pygame.draw.rect(aura,
                             (*_NS_akirakumo.PALETTE["aura_hot"], 255),
                             (fl_tip_x, fl_tip_y, 2, 2))
            pygame.draw.rect(aura,
                             (*_NS_akirakumo.PALETTE["white"], 255),
                             (fl_tip_x, fl_tip_y, 1, 1))
        surface.blit(aura, (x - r - 15, y - r - 15))
        # Extra rising flame particles
        for i in range(10):
            f_t = (phase * 0.7 + i * 0.1) % 1.0
            fx = x + int(math.sin(phase + i) * 20)
            fy = y - int(f_t * 40)
            fa = _NS_akirakumo._alpha(220 * (1 - f_t))
            if fa > 0:
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["aura_dark"], fa),
                                        (fx, fy), 3)
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["aura_mid"], fa),
                                        (fx, fy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_akirakumo.PALETTE["aura_hot"], fa),
                                 (fx, fy, 1, 1))

    # ============================================================
    # SKILL R — MEIDO ZANGETSU (massive crescent slash)
    # ============================================================
    def _draw_meido_ground(surface, boss, x, y, timer, phase):
        tx, ty = _NS_akirakumo._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.4:
            return
        t = (progress - 0.4) / 0.6
        r = int(60 + t * 30)
        a = _NS_akirakumo._alpha(200 * (1 - t * 0.3))
        pygame.draw.ellipse(surface,
                            (*_NS_akirakumo.PALETTE["demon_darkest"], a),
                            (tx - r, ty + 40 - r // 3, r * 2, r * 2 // 3))
        pygame.draw.ellipse(surface,
                            (*_NS_akirakumo.PALETTE["demon_dark"], a),
                            (tx - r + 5, ty + 40 - r // 3 + 2,
                             r * 2 - 10, r * 2 // 3 - 4))

    def _draw_meido(surface, boss, x, y, timer, phase):
        """Massive purple crescent slash that arcs from origin to target."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_akirakumo._target_position(boss, x, y)
        if progress < 0.2:
            # Charge phase — big glow at hand
            t = progress / 0.2
            cx_c = x + facing * 25
            cy_c = y - 5
            for r in range(int(12 * t) + 5, 0, -1):
                a = _NS_akirakumo._alpha(200 * (12 * t + 5 - r) / (12 * t + 5))
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["demon_dark"], a),
                                        (cx_c, cy_c), r)
            _NS_akirakumo._aacircle(surface,
                                    _NS_akirakumo.PALETTE["demon_hot"],
                                    (cx_c, cy_c), max(1, int(6 * t)))
            return
        # Casting: MASSIVE crescent moves from origin toward target
        t = (progress - 0.2) / 0.7
        t = min(1.0, t)
        start_x = x + facing * 30
        start_y = y - 5
        bx = int(start_x + (tx - start_x) * t)
        by = int(start_y + (ty - start_y) * t)
        # Long trail
        for i in range(12):
            trail_t = max(0.0, t - i * 0.05)
            px = int(start_x + (tx - start_x) * trail_t)
            py = int(start_y + (ty - start_y) * trail_t)
            a = _NS_akirakumo._alpha(220 - i * 18)
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["demon_darkest"], a),
                                    (px, py), max(2, 12 - i))
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["demon_dark"], a),
                                    (px, py), max(1, 9 - i))
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["demon_mid"], a),
                                    (px, py), max(1, 6 - i))
            if i < 5:
                # Small crescents along trail
                cr_ang = phase * 2 + i * 0.5
                _NS_akirakumo._draw_crescent(
                    surface, px, py, 5 + i, 1,
                    _NS_akirakumo.PALETTE["demon_hot"], a,
                    angle=cr_ang,
                )
        # MASSIVE crescent projectile
        cr_r = 25
        for cr_layer, (w, color, wa) in enumerate([
            (7, _NS_akirakumo.PALETTE["demon_darkest"], 120),
            (5, _NS_akirakumo.PALETTE["demon_dark"], 180),
            (3, _NS_akirakumo.PALETTE["demon_mid"], 220),
            (2, _NS_akirakumo.PALETTE["demon_light"], 240),
            (1, _NS_akirakumo.PALETTE["demon_hot"], 255),
        ]):
            _NS_akirakumo._draw_crescent(
                surface, bx, by, cr_r, w, color, wa,
                angle=0 if facing > 0 else math.pi,
                arc_span=math.pi * 1.3,
            )
        # Center glow
        for r in range(10, 0, -2):
            a = _NS_akirakumo._alpha(150 * (10 - r) / 10)
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["demon_hot"], a),
                                    (bx, by), r)
        _NS_akirakumo._aacircle(surface, _NS_akirakumo.PALETTE["white"],
                                (bx, by), 2)
        # Sparkles around the crescent
        for i in range(12):
            sp_ang = phase * 2 + i * math.pi / 6
            sp_dist = int(cr_r * 1.1)
            spx = bx + int(math.cos(sp_ang) * sp_dist)
            spy = by + int(math.sin(sp_ang) * sp_dist)
            pygame.draw.rect(surface,
                             _NS_akirakumo.PALETTE["demon_hot"],
                             (spx, spy, 2, 2))
            pygame.draw.rect(surface,
                             _NS_akirakumo.PALETTE["white"],
                             (spx, spy, 1, 1))
        # Impact
        if t > 0.85:
            st = (t - 0.85) / 0.15
            r = int(30 + st * 30)
            a = _NS_akirakumo._alpha(255 * (1 - st))
            for rr in range(r + 5, 0, -3):
                ra = _NS_akirakumo._alpha(a * (r + 5 - rr) / (r + 5))
                _NS_akirakumo._aacircle(surface,
                                        (*_NS_akirakumo.PALETTE["demon_darkest"], ra),
                                        (tx, ty), rr)
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["demon_dark"], a),
                                    (tx, ty), max(1, r - 5))
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["demon_mid"], a),
                                    (tx, ty), max(1, r - 12))
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["demon_hot"], a),
                                    (tx, ty), max(1, r - 20))
            _NS_akirakumo._aacircle(surface,
                                    (*_NS_akirakumo.PALETTE["white"], a),
                                    (tx, ty), max(1, r - 25))
            # Radial crescents flying outward
            for i in range(8):
                ang = i * math.pi / 4 + st * 3
                dist = int(r * 1.2)
                cxi = tx + int(math.cos(ang) * dist)
                cyi = ty + int(math.sin(ang) * dist)
                _NS_akirakumo._draw_crescent(
                    surface, cxi, cyi, 8, 2,
                    _NS_akirakumo.PALETTE["demon_hot"], a,
                    angle=ang,
                )


# ====================================================================================================
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ====================================================================================================
def draw_kaelthys(surface, boss, x, y):
    """Entry point kaelthys."""
    return _NS_kaelthys.draw_kaelthys(surface, boss, x, y)

def draw_kaoruken(surface, boss, x, y):
    """Entry point kaoruken."""
    return _NS_kaoruken.draw_kaoruken(surface, boss, x, y)

def draw_vaelkorr(surface, boss, x, y):
    """Entry point vaelkorr."""
    return _NS_vaelkorr.draw_vaelkorr(surface, boss, x, y)

def draw_akirakumo(surface, boss, x, y):
    """Entry point akirakumo."""
    return _NS_akirakumo.draw_akirakumo(surface, boss, x, y)
