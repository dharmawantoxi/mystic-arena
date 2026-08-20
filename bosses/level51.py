"""
bosses/level51.py - Semua boss Level 51

Berisi:
  - aurelian (mini boss - MELEE goldspear sovereign, fighter-tank)
  - morvath  (mini boss - MELEE deepmaw leviathan, strength)
  - pyrhaan  (mini boss - MELEE cinderborn adept, agility)
  - kaithros (TRUE BOSS - MELEE emberlion ronin, flame swordsmanship)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True


# ====================================================================================================
# AURELIAN - MINI BOSS
# ====================================================================================================

class _NS_aurelian:
    """Namespace aurelian - HD rendering untuk mini boss Aurelian."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Golden armor (main body)
        "gold_darkest": (55, 35, 8),
        "gold_dark": (110, 75, 15),
        "gold_mid": (180, 140, 40),
        "gold_light": (240, 200, 90),
        "gold_shine": (255, 240, 170),
        "gold_glow": (255, 255, 220),

        # Deep gold shadow (armor cavities)
        "gold_shadow": (35, 22, 5),

        # Blue cape/cloth
        "cape_darkest": (5, 10, 30),
        "cape_dark": (15, 30, 70),
        "cape_mid": (35, 65, 130),
        "cape_light": (75, 120, 195),
        "cape_edge": (140, 180, 230),

        # Skin (tanned)
        "skin_dark": (95, 65, 45),
        "skin_mid": (170, 130, 95),
        "skin_light": (225, 190, 150),
        "skin_shine": (250, 225, 195),

        # Hair (dark)
        "hair_dark": (20, 15, 25),
        "hair_mid": (55, 45, 60),
        "hair_light": (95, 80, 100),

        # Eyes (piercing blue-white)
        "eye_dark": (10, 30, 60),
        "eye_mid": (80, 140, 220),
        "eye_light": (200, 235, 255),

        # Spear blade (silver-steel with gold)
        "steel_dark": (55, 60, 75),
        "steel_mid": (135, 145, 165),
        "steel_light": (215, 225, 240),
        "steel_shine": (250, 253, 255),

        # Spear shaft (dark wood-metal)
        "shaft_dark": (25, 20, 15),
        "shaft_mid": (55, 45, 30),
        "shaft_light": (100, 85, 60),

        # Crystal (cataclysm)
        "crystal_darkest": (60, 45, 5),
        "crystal_dark": (140, 105, 20),
        "crystal_mid": (220, 175, 50),
        "crystal_light": (250, 220, 130),
        "crystal_shine": (255, 250, 200),

        # Banner (Demacian style)
        "banner_dark": (20, 40, 90),
        "banner_mid": (50, 90, 170),
        "banner_light": (130, 180, 240),

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
        color = _NS_aurelian._clamp(color)
        if _NS_aurelian.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_aurelian._clamp(color)
        if _NS_aurelian.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_aurelian._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 120 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_aurelian(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_aurelian._detect_moving(boss)
        _NS_aurelian._update_attack_anim(boss)
        attacking = getattr(boss, "_au_attack_active", False)

        # Ambient
        _NS_aurelian._draw_shadow(surface, x, y + 52)
        _NS_aurelian._draw_gold_aura(surface, x, y, pulse)
        _NS_aurelian._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX (behind body)
        if active_skill == "e":
            _NS_aurelian._draw_standard_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aurelian._draw_cataclysm_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_aurelian._draw_aegis_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_aurelian._draw_body_attack(surface, boss, x, y)
        elif moving:
            _NS_aurelian._draw_body_walk(surface, boss, x, y)
        else:
            _NS_aurelian._draw_body_idle(surface, boss, x, y)

        # Aegis bubble overlay (on top of body)
        if active_skill == "w":
            _NS_aurelian._draw_aegis_bubble(surface, boss, x, y, skill_timer, pulse)

        # Foreground skill FX
        if active_skill == "q":
            _NS_aurelian._draw_dragon_thrust_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_aurelian._draw_standard_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_aurelian._draw_cataclysm_fg(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 45)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_au_attack_active", False))

        if not active:
            if timer >= cooldown - 22:
                boss._au_attack_active = True
                boss._au_attack_frame = 0
                active = True

        if active:
            boss._au_attack_frame = int(getattr(boss, "_au_attack_frame", 0)) + 1
            attack_duration = 28
            if boss._au_attack_frame >= attack_duration:
                boss._au_attack_active = False
                boss._au_attack_frame = 0
                active = False

        attack_duration = 28
        boss._au_attack_progress = (
            min(1.0, getattr(boss, "_au_attack_frame", 0) / attack_duration)
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_au_last_x"):
            boss._au_last_x = boss.x
            boss._au_last_y = boss.y
            return False
        dx = abs(boss.x - boss._au_last_x)
        dy = abs(boss.y - boss._au_last_y)
        boss._au_last_x = boss.x
        boss._au_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_aurelian._draw_full_body(surface, x, y + bob,
                                     boss.direction, boss.pulse, "idle", 0)

    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 3)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_aurelian._draw_full_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "walk", 0)

    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_au_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 4) * boss.direction
            lift = int(t * 2)
        elif progress < 0.6:
            t = (progress - 0.3) / 0.3
            ease = 1 - (1 - t) ** 3
            lunge = int((-4 + ease * 22)) * boss.direction
            lift = int(2 - ease * 4)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(18 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)

        _NS_aurelian._draw_full_body(surface, x + lunge, y - lift,
                                     boss.direction, boss.pulse, "attack", progress)
        # Blue spear energy trail on thrust
        _NS_aurelian._draw_basic_spear_trail(surface, boss, x + lunge,
                                              y - lift, progress)

    # ============================================================
    # FULL BODY (heavy knight)
    # ============================================================
    def _draw_full_body(surface, cx, cy, facing, phase, action, atk_prog):
        # 1. Cape (paling belakang, meliuk)
        _NS_aurelian._draw_cape(surface, cx, cy, facing, phase)
        # 2. Legs (behind torso)
        _NS_aurelian._draw_legs(surface, cx, cy, facing, phase, action)
        # 3. Back arm (rear)
        _NS_aurelian._draw_back_arm(surface, cx, cy, facing, phase, action)
        # 4. Torso armor
        _NS_aurelian._draw_torso(surface, cx, cy, facing, phase)
        # 5. Head + crown
        _NS_aurelian._draw_head(surface, cx, cy - 24, facing, phase)
        # 6. Front arm + SPEAR
        _NS_aurelian._draw_front_arm_with_spear(surface, cx, cy, facing,
                                                 phase, action, atk_prog)

    def _draw_cape(surface, cx, cy, facing, phase):
        """Blue cape flowing behind."""
        sway = math.sin(phase * 0.4) * 3
        back_dir = -facing

        cape_pts = [
            (cx + back_dir * 4, cy - 10),
            (cx + back_dir * 10, cy - 8),
            (cx + back_dir * 14, cy - 2),
            (cx + back_dir * 18 + int(sway * back_dir), cy + 10),
            (cx + back_dir * 20 + int(sway * back_dir * 1.5), cy + 22),
            (cx + back_dir * 18 + int(sway * back_dir * 2), cy + 36),
            (cx + back_dir * 12 + int(sway * back_dir), cy + 44),
            (cx + back_dir * 4, cy + 42),
            (cx, cy + 30),
            (cx + back_dir * 2, cy + 10),
            (cx + back_dir * 3, cy - 4),
        ]
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["shadow_deep"],
                           [(px + 2, py + 3) for px, py in cape_pts])
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["cape_darkest"], cape_pts)
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["cape_dark"], [
            (cx + back_dir * 3, cy - 9),
            (cx + back_dir * 9, cy - 7),
            (cx + back_dir * 13, cy - 1),
            (cx + back_dir * 16 + int(sway * back_dir), cy + 10),
            (cx + back_dir * 18 + int(sway * back_dir * 1.5), cy + 22),
            (cx + back_dir * 15 + int(sway * back_dir * 1.5), cy + 34),
            (cx + back_dir * 10, cy + 42),
            (cx + back_dir * 2, cy + 40),
            (cx, cy + 28),
        ])
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["cape_mid"], [
            (cx + back_dir * 5, cy - 4),
            (cx + back_dir * 11, cy + 4),
            (cx + back_dir * 13 + int(sway * back_dir), cy + 18),
            (cx + back_dir * 10, cy + 30),
            (cx + back_dir * 4, cy + 32),
            (cx + back_dir * 3, cy + 8),
        ])
        # Cape highlight
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["cape_light"],
                             (cx + back_dir * 5, cy - 2),
                             (cx + back_dir * 8, cy + 15), 1)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["cape_edge"],
                             (cx + back_dir * 6, cy),
                             (cx + back_dir * 7, cy + 10), 1)

        # Golden trim on cape edge
        pygame.draw.line(surface, _NS_aurelian.PALETTE["gold_dark"],
                         (cx + back_dir * 20 + int(sway * back_dir * 1.5), cy + 22),
                         (cx + back_dir * 12 + int(sway * back_dir), cy + 44), 2)
        pygame.draw.line(surface, _NS_aurelian.PALETTE["gold_mid"],
                         (cx + back_dir * 20 + int(sway * back_dir * 1.5), cy + 22),
                         (cx + back_dir * 12 + int(sway * back_dir), cy + 44), 1)

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Armored legs (greaves)."""
        leg_sway = 0
        if action == "walk":
            leg_sway = math.sin(phase) * 3

        # Back leg
        back_x = cx - 4
        back_y_top = cy + 8
        back_y_knee = cy + 24
        back_y_bot = cy + 42 + int(-leg_sway)

        # Thigh (dark)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shadow_deep"],
                             (back_x + 1, back_y_top + 1),
                             (back_x + 1, back_y_knee + 1), 8)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_shadow"],
                             (back_x, back_y_top), (back_x, back_y_knee), 7)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_dark"],
                             (back_x, back_y_top), (back_x, back_y_knee), 5)
        # Greave (calf armor)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shadow_deep"],
                             (back_x + 1, back_y_knee + 1),
                             (back_x + 1, back_y_bot + 1), 8)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_darkest"],
                             (back_x, back_y_knee), (back_x, back_y_bot), 7)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_dark"],
                             (back_x, back_y_knee), (back_x, back_y_bot), 5)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_mid"],
                             (back_x - 1, back_y_knee), (back_x - 1, back_y_bot), 2)
        # Knee cap (round golden disc)
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_darkest"],
                               (back_x, back_y_knee), 4)
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_dark"],
                               (back_x, back_y_knee), 3)
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_mid"],
                               (back_x, back_y_knee), 2)
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_light"],
                         (back_x, back_y_knee - 1, 1, 1))

        # Front leg
        front_x = cx + 4
        front_y_top = cy + 8
        front_y_knee = cy + 24
        front_y_bot = cy + 42 + int(leg_sway)

        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shadow_deep"],
                             (front_x + 1, front_y_top + 1),
                             (front_x + 1, front_y_knee + 1), 8)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_shadow"],
                             (front_x, front_y_top), (front_x, front_y_knee), 7)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_dark"],
                             (front_x, front_y_top), (front_x, front_y_knee), 5)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_mid"],
                             (front_x - 1, front_y_top), (front_x - 1, front_y_knee), 2)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shadow_deep"],
                             (front_x + 1, front_y_knee + 1),
                             (front_x + 1, front_y_bot + 1), 8)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_darkest"],
                             (front_x, front_y_knee), (front_x, front_y_bot), 7)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_dark"],
                             (front_x, front_y_knee), (front_x, front_y_bot), 5)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_mid"],
                             (front_x - 1, front_y_knee), (front_x - 1, front_y_bot), 2)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_light"],
                             (front_x - 2, front_y_knee + 2),
                             (front_x - 2, front_y_bot - 2), 1)
        # Front knee cap
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_darkest"],
                               (front_x, front_y_knee), 4)
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_dark"],
                               (front_x, front_y_knee), 3)
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_mid"],
                               (front_x, front_y_knee), 2)
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_shine"],
                         (front_x, front_y_knee - 1, 1, 1))

        # Armored boots (sabatons)
        for foot_x, foot_y in ((back_x, back_y_bot), (front_x, front_y_bot)):
            pygame.draw.ellipse(surface, _NS_aurelian.PALETTE["shadow_deep"],
                                (foot_x - 5, foot_y - 1, 12, 6))
            pygame.draw.ellipse(surface, _NS_aurelian.PALETTE["gold_darkest"],
                                (foot_x - 4, foot_y, 10, 4))
            pygame.draw.ellipse(surface, _NS_aurelian.PALETTE["gold_dark"],
                                (foot_x - 4, foot_y, 10, 3))
            pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_mid"],
                             (foot_x - 2, foot_y, 5, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Golden chestplate with intricate detail."""
        # Main chestplate shape
        torso_pts = [
            (cx - 13, cy - 8),
            (cx - 15, cy - 2),
            (cx - 14, cy + 6),
            (cx - 9, cy + 10),
            (cx + 9, cy + 10),
            (cx + 14, cy + 6),
            (cx + 15, cy - 2),
            (cx + 13, cy - 8),
            (cx + 6, cy - 13),
            (cx - 6, cy - 13),
        ]
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in torso_pts])
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_darkest"], torso_pts)
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_dark"], [
            (cx - 12, cy - 6),
            (cx - 14, cy - 1),
            (cx - 13, cy + 5),
            (cx - 8, cy + 9),
            (cx + 8, cy + 9),
            (cx + 13, cy + 5),
            (cx + 14, cy - 1),
            (cx + 12, cy - 6),
            (cx + 5, cy - 11),
            (cx - 5, cy - 11),
        ])
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_mid"], [
            (cx - 10, cy - 4),
            (cx - 11, cy + 2),
            (cx - 7, cy + 7),
            (cx + 7, cy + 7),
            (cx + 11, cy + 2),
            (cx + 10, cy - 4),
            (cx + 4, cy - 9),
            (cx - 4, cy - 9),
        ])
        # Central highlight
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_light"], [
            (cx - 4, cy - 6),
            (cx + 4, cy - 6),
            (cx + 5, cy),
            (cx - 5, cy),
        ])

        # Center chest emblem (diamond/crown shape)
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_shadow"], [
            (cx, cy - 5),
            (cx + 3, cy - 1),
            (cx, cy + 3),
            (cx - 3, cy - 1),
        ])
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["cape_dark"], [
            (cx, cy - 4),
            (cx + 2, cy - 1),
            (cx, cy + 2),
            (cx - 2, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["cape_light"],
                         (cx, cy - 2, 1, 2))

        # Shoulder pauldrons (large golden discs)
        for shoulder_x_off, shoulder_side in [(-13, -1), (13, 1)]:
            sx = cx + shoulder_x_off
            sy = cy - 8
            # Shadow
            pygame.draw.ellipse(surface, _NS_aurelian.PALETTE["shadow_deep"],
                                (sx - 5, sy - 4, 12, 10))
            # Base
            pygame.draw.ellipse(surface, _NS_aurelian.PALETTE["gold_darkest"],
                                (sx - 5, sy - 4, 11, 10))
            pygame.draw.ellipse(surface, _NS_aurelian.PALETTE["gold_dark"],
                                (sx - 4, sy - 3, 9, 8))
            pygame.draw.ellipse(surface, _NS_aurelian.PALETTE["gold_mid"],
                                (sx - 3, sy - 2, 7, 6))
            # Spike on top
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_darkest"], [
                (sx + shoulder_side * 2, sy - 4),
                (sx + shoulder_side * 4, sy - 10),
                (sx + shoulder_side * 5, sy - 4),
            ])
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_dark"], [
                (sx + shoulder_side * 3, sy - 4),
                (sx + shoulder_side * 4, sy - 9),
                (sx + shoulder_side * 5, sy - 4),
            ])
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_mid"], [
                (sx + shoulder_side * 3, sy - 4),
                (sx + shoulder_side * 4, sy - 8),
                (sx + shoulder_side * 4, sy - 4),
            ])
            pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_shine"],
                             (sx + shoulder_side * 4, sy - 8, 1, 1))
            # Pauldron highlight
            pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_light"],
                             (sx - 1, sy - 2, 2, 1))
            pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_shine"],
                             (sx, sy - 2, 1, 1))

        # Waist belt (dark with gold buckle)
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["shadow_deep"],
                         (cx - 13, cy + 7, 27, 5))
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_shadow"],
                         (cx - 12, cy + 8, 25, 4))
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_dark"],
                         (cx - 12, cy + 8, 25, 2))
        # Central buckle
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_darkest"], [
            (cx - 3, cy + 7),
            (cx + 3, cy + 7),
            (cx + 4, cy + 12),
            (cx - 4, cy + 12),
        ])
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_dark"], [
            (cx - 2, cy + 8),
            (cx + 2, cy + 8),
            (cx + 3, cy + 11),
            (cx - 3, cy + 11),
        ])
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_shine"],
                         (cx, cy + 9, 1, 1))

    def _draw_head(surface, cx, cy, facing, phase):
        """Head with hair and golden crown."""
        # Hair back
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["shadow_deep"], [
            (cx - 7, cy + 7),
            (cx - 9, cy - 2),
            (cx - 7, cy - 9),
            (cx - 3, cy - 12),
            (cx + 3, cy - 12),
            (cx + 7, cy - 9),
            (cx + 9, cy - 2),
            (cx + 7, cy + 7),
        ])
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["hair_dark"], [
            (cx - 6, cy + 6),
            (cx - 8, cy - 2),
            (cx - 6, cy - 9),
            (cx - 3, cy - 11),
            (cx + 3, cy - 11),
            (cx + 6, cy - 9),
            (cx + 8, cy - 2),
            (cx + 6, cy + 6),
        ])

        # FACE
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["skin_dark"], [
            (cx - 5, cy + 5),
            (cx - 6, cy - 2),
            (cx - 4, cy - 7),
            (cx + 4, cy - 7),
            (cx + 6, cy - 2),
            (cx + 5, cy + 5),
        ])
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["skin_mid"], [
            (cx - 4, cy + 4),
            (cx - 5, cy - 2),
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 5, cy - 2),
            (cx + 4, cy + 4),
        ])
        # Skin highlight (cheekbone)
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["skin_light"],
                         (cx - 3, cy - 1, 6, 1))
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["skin_shine"],
                         (cx - 1, cy - 1, 2, 1))

        # Hair bangs covering forehead
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["hair_dark"], [
            (cx - 5, cy - 6),
            (cx - 4, cy - 8),
            (cx - 1, cy - 6),
            (cx + 1, cy - 8),
            (cx + 4, cy - 6),
            (cx + 5, cy - 4),
            (cx - 5, cy - 4),
        ])

        # CROWN (large golden with 5 spikes)
        # Base band
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["shadow_deep"],
                         (cx - 8, cy - 10, 16, 4))
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_darkest"],
                         (cx - 8, cy - 10, 16, 4))
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_dark"],
                         (cx - 8, cy - 10, 16, 3))
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_mid"],
                         (cx - 8, cy - 10, 16, 2))
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_light"],
                         (cx - 8, cy - 10, 16, 1))

        # 5 spikes on crown (large center, smaller sides)
        crown_spikes = [(-7, 3), (-4, 5), (0, 7), (4, 5), (7, 3)]
        for spike_x, spike_h in crown_spikes:
            sx = cx + spike_x
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["shadow_deep"], [
                (sx + 1, cy - 10 - spike_h + 1),
                (sx - 1, cy - 10 + 1),
                (sx + 2, cy - 10 + 1),
            ])
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_darkest"], [
                (sx, cy - 10 - spike_h),
                (sx - 1, cy - 10),
                (sx + 2, cy - 10),
            ])
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_dark"], [
                (sx, cy - 10 - spike_h),
                (sx, cy - 10),
                (sx + 1, cy - 10),
            ])
            pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_shine"],
                             (sx, cy - 10 - spike_h, 1, 1))

        # Central emblem on crown (small blue gem)
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["cape_dark"],
                         (cx - 1, cy - 9, 2, 2))
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["cape_light"],
                         (cx, cy - 9, 1, 1))

        # EYES (piercing blue)
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        for eye_x_off in (-2, 2):
            ex = cx + eye_x_off * facing
            ey = cy - 3
            # Eye white
            pygame.draw.rect(surface, _NS_aurelian.PALETTE["skin_shine"],
                             (ex - 1, ey, 2, 1))
            # Glow
            for r in range(3, 0, -1):
                alpha = _NS_aurelian._alpha(80 * (3 - r) / 3 * eye_pulse)
                _NS_aurelian._aacircle(surface,
                                       (*_NS_aurelian.PALETTE["eye_mid"], alpha),
                                       (ex, ey), r)
            pygame.draw.rect(surface, _NS_aurelian.PALETTE["eye_light"],
                             (ex, ey, 1, 1))

        # Mouth (stern)
        pygame.draw.line(surface, _NS_aurelian.PALETTE["skin_dark"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)

        # Small beard/chin shadow
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["hair_mid"],
                         (cx - 2, cy + 4, 4, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        """Back arm (hidden mostly)."""
        sway = math.sin(phase * 0.9) * 1
        back_shoulder_x = cx - facing * 12
        back_shoulder_y = cy - 6
        back_hand_x = back_shoulder_x - facing * 2 + int(sway)
        back_hand_y = cy + 10

        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shadow_deep"],
                             (back_shoulder_x + 1, back_shoulder_y + 1),
                             (back_hand_x + 1, back_hand_y + 1), 6)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_darkest"],
                             (back_shoulder_x, back_shoulder_y),
                             (back_hand_x, back_hand_y), 5)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_dark"],
                             (back_shoulder_x, back_shoulder_y),
                             (back_hand_x, back_hand_y), 3)
        # Gauntlet
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_darkest"],
                               (back_hand_x, back_hand_y), 3)
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_dark"],
                               (back_hand_x, back_hand_y), 2)

    def _draw_front_arm_with_spear(surface, cx, cy, facing, phase, action, atk_prog):
        """Front arm holding spear."""
        sway = math.sin(phase * 0.9) * 2
        front_shoulder_x = cx + facing * 12
        front_shoulder_y = cy - 6

        # Determine spear angle and hand position
        if action == "attack":
            if atk_prog < 0.3:
                # WIND-UP: pull spear back
                t = atk_prog / 0.3
                spear_angle = -math.pi * 0.15 - t * math.pi * 0.35
                hand_offset_x = facing * int(-8 - t * 6)
                hand_offset_y = int(-4 - t * 2)
            elif atk_prog < 0.6:
                # THRUST: forward stab (spear horizontal)
                t = (atk_prog - 0.3) / 0.3
                ease = 1 - (1 - t) ** 3
                spear_angle = -math.pi * 0.5 + ease * math.pi * 0.5
                hand_offset_x = facing * int(-14 + ease * 30)
                hand_offset_y = int(-6 + ease * 10)
            else:
                # Recovery
                t = (atk_prog - 0.6) / 0.4
                spear_angle = -t * math.pi * 0.15
                hand_offset_x = facing * int(16 - t * 12)
                hand_offset_y = int(4 - t * 4)
        elif action == "walk":
            spear_angle = -math.pi * 0.5 + math.sin(phase) * 0.05
            hand_offset_x = facing * 6
            hand_offset_y = int(2 + sway)
        else:
            # IDLE: spear vertical (pointing up)
            spear_angle = -math.pi * 0.5 + math.sin(phase * 0.5) * 0.02
            hand_offset_x = facing * 6
            hand_offset_y = int(2 - sway)

        front_hand_x = front_shoulder_x + hand_offset_x
        front_hand_y = front_shoulder_y + hand_offset_y

        # Elbow
        elbow_x = int((front_shoulder_x + front_hand_x) / 2) + facing * 2
        elbow_y = int((front_shoulder_y + front_hand_y) / 2) + 1

        # Upper arm (armored)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shadow_deep"],
                             (front_shoulder_x + 1, front_shoulder_y + 1),
                             (elbow_x + 1, elbow_y + 1), 6)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_darkest"],
                             (front_shoulder_x, front_shoulder_y),
                             (elbow_x, elbow_y), 5)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_dark"],
                             (front_shoulder_x, front_shoulder_y),
                             (elbow_x, elbow_y), 3)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_mid"],
                             (front_shoulder_x - 1, front_shoulder_y - 1),
                             (elbow_x - 1, elbow_y - 1), 1)

        # Elbow armor
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_darkest"],
                               (elbow_x, elbow_y), 3)
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_dark"],
                               (elbow_x, elbow_y), 2)

        # Forearm
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 1),
                             (front_hand_x + 1, front_hand_y + 1), 5)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_darkest"],
                             (elbow_x, elbow_y),
                             (front_hand_x, front_hand_y), 4)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_dark"],
                             (elbow_x, elbow_y),
                             (front_hand_x, front_hand_y), 2)

        # Gauntlet (hand)
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_darkest"],
                               (front_hand_x, front_hand_y), 4)
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_dark"],
                               (front_hand_x, front_hand_y), 3)
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_mid"],
                               (front_hand_x, front_hand_y), 2)
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_shine"],
                         (front_hand_x - 1, front_hand_y - 1, 1, 1))

        # SPEAR
        _NS_aurelian._draw_spear(surface, front_hand_x, front_hand_y,
                                  spear_angle, facing)

    def _draw_spear(surface, hand_x, hand_y, angle, facing):
        """Long polearm with steel/gold blade tip."""
        actual_angle = angle if facing > 0 else math.pi - angle

        # Shaft dimensions
        shaft_length_forward = 26
        shaft_length_backward = 18

        # Tip position (blade point)
        tip_x = hand_x + int(math.cos(actual_angle) * (shaft_length_forward + 12))
        tip_y = hand_y + int(math.sin(actual_angle) * (shaft_length_forward + 12))

        # Blade base position
        blade_base_x = hand_x + int(math.cos(actual_angle) * shaft_length_forward)
        blade_base_y = hand_y + int(math.sin(actual_angle) * shaft_length_forward)

        # Butt end (behind hand)
        butt_x = hand_x - int(math.cos(actual_angle) * shaft_length_backward)
        butt_y = hand_y - int(math.sin(actual_angle) * shaft_length_backward)

        # SHAFT (wooden pole)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shadow_deep"],
                             (butt_x + 2, butt_y + 2),
                             (blade_base_x + 2, blade_base_y + 2), 4)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shaft_dark"],
                             (butt_x, butt_y),
                             (blade_base_x, blade_base_y), 4)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shaft_mid"],
                             (butt_x, butt_y),
                             (blade_base_x, blade_base_y), 2)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shaft_light"],
                             (butt_x, butt_y - 1),
                             (blade_base_x, blade_base_y - 1), 1)

        # Gold rings on shaft (2 decoration bands)
        for ring_t in (0.3, 0.7):
            rx = int(butt_x + (blade_base_x - butt_x) * ring_t)
            ry = int(butt_y + (blade_base_y - butt_y) * ring_t)
            perp_x = -math.sin(actual_angle)
            perp_y = math.cos(actual_angle)
            _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_darkest"],
                                 (rx + int(perp_x * 3), ry + int(perp_y * 3)),
                                 (rx - int(perp_x * 3), ry - int(perp_y * 3)), 3)
            _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["gold_mid"],
                                 (rx + int(perp_x * 3), ry + int(perp_y * 3)),
                                 (rx - int(perp_x * 3), ry - int(perp_y * 3)), 1)

        # BLADE (spear tip - elongated leaf shape)
        perp_x = -math.sin(actual_angle)
        perp_y = math.cos(actual_angle)
        # Widest point at 30% from base
        widest_x = blade_base_x + int(math.cos(actual_angle) * 4)
        widest_y = blade_base_y + int(math.sin(actual_angle) * 4)

        blade_pts = [
            (tip_x, tip_y),
            (widest_x + int(perp_x * 3), widest_y + int(perp_y * 3)),
            (blade_base_x + int(perp_x * 2), blade_base_y + int(perp_y * 2)),
            (blade_base_x - int(perp_x * 2), blade_base_y - int(perp_y * 2)),
            (widest_x - int(perp_x * 3), widest_y - int(perp_y * 3)),
        ]
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in blade_pts])
        _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["steel_dark"], blade_pts)

        # Bright center line (fuller)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["steel_mid"],
                             (blade_base_x, blade_base_y), (tip_x, tip_y), 3)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["steel_light"],
                             (blade_base_x, blade_base_y), (tip_x, tip_y), 1)
        # Sharp edge highlight
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["steel_shine"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["white"],
                         (tip_x, tip_y, 1, 1))

        # Golden guard between shaft and blade
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_darkest"],
                               (blade_base_x, blade_base_y), 3)
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_dark"],
                               (blade_base_x, blade_base_y), 2)
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_light"],
                         (blade_base_x, blade_base_y, 1, 1))

        # Butt cap (small gold cap)
        _NS_aurelian._aacircle(surface, _NS_aurelian.PALETTE["gold_dark"],
                               (butt_x, butt_y), 2)
        pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_light"],
                         (butt_x, butt_y, 1, 1))

    # ============================================================
    # BASIC ATTACK — SPEAR THRUST TRAIL (blue energy)
    # ============================================================
    def _draw_basic_spear_trail(surface, boss, x, y, progress):
        """Blue energy trail when spear thrusts forward."""
        if progress < 0.35 or progress > 0.75:
            return

        facing = boss.direction
        if progress < 0.6:
            t = (progress - 0.35) / 0.25
        else:
            t = 1 - (progress - 0.6) / 0.15
        intensity = math.sin(t * math.pi)

        # Trail extends from thrust position forward
        base_x = x + facing * 18
        base_y = y - 4
        tip_x = x + facing * (32 + int(t * 20))
        tip_y = y - 4

        # Multi-layer trail
        alpha_outer = _NS_aurelian._alpha(180 * intensity)
        alpha_mid = _NS_aurelian._alpha(220 * intensity)
        alpha_core = _NS_aurelian._alpha(255 * intensity)

        pygame.draw.line(surface,
                         (*_NS_aurelian.PALETTE["cape_dark"], alpha_outer),
                         (base_x, base_y), (tip_x, tip_y), 8)
        pygame.draw.line(surface,
                         (*_NS_aurelian.PALETTE["cape_mid"], alpha_mid),
                         (base_x, base_y), (tip_x, tip_y), 5)
        pygame.draw.line(surface,
                         (*_NS_aurelian.PALETTE["cape_light"], alpha_core),
                         (base_x, base_y), (tip_x, tip_y), 3)
        pygame.draw.line(surface,
                         (*_NS_aurelian.PALETTE["cape_edge"], alpha_core),
                         (base_x, base_y), (tip_x, tip_y), 1)

        # Sparks flying off tip
        for i in range(6):
            spark_angle = math.sin(t * 8 + i) * 0.5
            spark_r = int(6 + math.sin(t * 4 + i) * 4)
            sx = tip_x + int(math.cos(spark_angle) * spark_r) * facing
            sy = tip_y + int(math.sin(spark_angle) * spark_r)
            pygame.draw.rect(surface,
                             (*_NS_aurelian.PALETTE["cape_edge"], alpha_core),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_aurelian.PALETTE["white"], alpha_core),
                             (sx, sy, 1, 1))

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

    def _draw_gold_aura(surface, x, y, phase):
        """Golden regal aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((200, 160), pygame.SRCALPHA)
        for radius in range(80, 5, -5):
            alpha = _NS_aurelian._alpha((80 - radius) * 0.8 * pulse)
            if alpha > 0:
                _NS_aurelian._aacircle(aura,
                                       (*_NS_aurelian.PALETTE["gold_darkest"], alpha),
                                       (100, 80), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_aurelian._alpha((50 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_aurelian._aacircle(aura,
                                       (*_NS_aurelian.PALETTE["gold_dark"], alpha),
                                       (100, 80), radius)
        surface.blit(aura, (x - 100, y - 80))

        # Floating gold particles
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 34 + int(math.sin(phase + i) * 8)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_shine"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Ground ring — golden regal."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_aurelian.PALETTE["gold_darkest"], 200),
                            (5, 17, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_aurelian.PALETTE["gold_dark"], 220),
                            (14, 19, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_aurelian.PALETTE["gold_mid"], 200),
                            (25, 21, 110, 16), 1)

        # Golden runes
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 28 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 28 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_aurelian.PALETTE["gold_light"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_aurelian.PALETTE["gold_shine"],
                                 _NS_aurelian._alpha(180 * pulse)),
                                (15, 10, 130, 34), 1)
        surface.blit(ring, (x - 80, y - 25))

    # ============================================================
    # SKILL Q — DRAGON THRUST (blue crescent forward)
    # ============================================================
    def _draw_dragon_thrust_fx(surface, boss, x, y, timer, phase):
        """Big blue crescent slash forward."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Wave travels forward
        travel_dist = int(180 * progress)
        wave_center_x = x + facing * (30 + travel_dist)
        wave_center_y = y - 4

        wave_w = 55
        wave_h = 45
        fade = 1.0 - progress * 0.4

        # Crescent (blue energy)
        arc_points = []
        segments = 20
        for i in range(segments + 1):
            t = i / segments
            angle = -math.pi * 0.5 + t * math.pi
            ax = wave_center_x + int(math.cos(angle) * wave_w * 0.5) * facing
            ay = wave_center_y + int(math.sin(angle) * wave_h * 0.6)
            arc_points.append((ax, ay))

        for i in range(len(arc_points) - 1):
            alpha = _NS_aurelian._alpha(230 * fade)
            pygame.draw.line(surface, (*_NS_aurelian.PALETTE["cape_darkest"], alpha),
                             arc_points[i], arc_points[i + 1], 10)
            pygame.draw.line(surface, (*_NS_aurelian.PALETTE["cape_dark"], alpha),
                             arc_points[i], arc_points[i + 1], 7)
            pygame.draw.line(surface, (*_NS_aurelian.PALETTE["cape_mid"], alpha),
                             arc_points[i], arc_points[i + 1], 4)
            pygame.draw.line(surface, (*_NS_aurelian.PALETTE["cape_light"], alpha),
                             arc_points[i], arc_points[i + 1], 2)
            pygame.draw.line(surface, (*_NS_aurelian.PALETTE["cape_edge"], alpha),
                             arc_points[i], arc_points[i + 1], 1)

        # Sparks around wave
        for i in range(15):
            sp_angle = phase * 2 + i * math.pi / 7
            sp_r = 25 + int(math.sin(phase * 3 + i) * 8)
            dx = wave_center_x + int(math.cos(sp_angle) * sp_r) * facing
            dy = wave_center_y + int(math.sin(sp_angle) * sp_r * 0.6)
            alpha = _NS_aurelian._alpha(200 * fade)
            pygame.draw.rect(surface, (*_NS_aurelian.PALETTE["cape_edge"], alpha),
                             (dx, dy, 2, 2))
            pygame.draw.rect(surface, (*_NS_aurelian.PALETTE["white"], alpha),
                             (dx, dy, 1, 1))

    # ============================================================
    # SKILL W — GOLDEN AEGIS (shield bubble)
    # ============================================================
    def _draw_aegis_ground(surface, boss, x, y, timer, pulse):
        """Golden ring on ground under boss."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        for i in range(2):
            r = int(38 + i * 8 + math.sin(pulse * 2) * 3)
            alpha = _NS_aurelian._alpha(220 - i * 60)
            _NS_aurelian._aacircle(surface,
                                   (*_NS_aurelian.PALETTE["gold_mid"], alpha),
                                   (x, y + 45), r, 2)
            _NS_aurelian._aacircle(surface,
                                   (*_NS_aurelian.PALETTE["gold_light"], alpha),
                                   (x, y + 45), r, 1)

    def _draw_aegis_bubble(surface, boss, x, y, timer, phase):
        """Golden shield bubble around boss."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        breath = math.sin(phase * 2) * 3
        r = 55 + int(breath)

        bubble = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        # Layered rings
        for i, (thickness, alpha_val) in enumerate([
            (3, 130), (2, 170), (1, 210),
        ]):
            _NS_aurelian._aacircle(bubble,
                                   (*_NS_aurelian.PALETTE["gold_dark"], alpha_val),
                                   center, r - i, thickness)
            _NS_aurelian._aacircle(bubble,
                                   (*_NS_aurelian.PALETTE["gold_mid"], alpha_val),
                                   center, r - i - 1, 1)

        # Rotating sparkles
        for i in range(20):
            angle = phase * 1.5 + i * math.pi / 10
            sx = center[0] + int(math.cos(angle) * r)
            sy = center[1] + int(math.sin(angle) * r)
            pygame.draw.rect(bubble, _NS_aurelian.PALETTE["gold_light"], (sx, sy, 2, 2))
            pygame.draw.rect(bubble, _NS_aurelian.PALETTE["gold_shine"], (sx, sy, 1, 1))

        # Shield emblem sparkles inside (near edge)
        for i in range(8):
            angle = phase * 0.5 + i * math.pi / 4
            inner_r = r - 10
            bx = center[0] + int(math.cos(angle) * inner_r)
            by = center[1] + int(math.sin(angle) * inner_r)
            alpha = _NS_aurelian._alpha(180)
            _NS_aurelian._aacircle(bubble,
                                   (*_NS_aurelian.PALETTE["gold_dark"], alpha),
                                   (bx, by), 3)
            _NS_aurelian._aacircle(bubble,
                                   (*_NS_aurelian.PALETTE["gold_mid"], alpha),
                                   (bx, by), 2)
            pygame.draw.rect(bubble, _NS_aurelian.PALETTE["gold_shine"], (bx, by, 1, 1))

        surface.blit(bubble, (x - r - 10, y - r - 10))

        # Cross emblem effect on shield (front)
        emblem_x = x + boss.direction * 8
        emblem_y = y - 10
        for r_e in range(12, 3, -1):
            alpha = _NS_aurelian._alpha(70 * (12 - r_e) / 9)
            _NS_aurelian._aacircle(surface,
                                   (*_NS_aurelian.PALETTE["gold_shine"], alpha),
                                   (emblem_x, emblem_y), r_e)

    # ============================================================
    # SKILL E — SOVEREIGN STANDARD (planted banner)
    # ============================================================
    def _draw_standard_ground(surface, boss, x, y, timer, phase):
        """AoE ring on ground at target."""
        tx, ty = _NS_aurelian._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(48 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_aurelian.PALETTE["gold_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_aurelian.PALETTE["gold_dark"], 200),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
            pygame.draw.ellipse(surface, (*_NS_aurelian.PALETTE["gold_mid"], 180),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8), 1)

    def _draw_standard_fg(surface, boss, x, y, timer, phase):
        """Blue banner planted at target with billowing flag."""
        tx, ty = _NS_aurelian._target_position(boss, x, y)
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Pole rises from ground
        pole_top_y = ty - int(80 * min(1.0, progress * 3))
        pole_bot_y = ty

        # Pole (dark shaft with gold top)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shadow_deep"],
                             (tx + 1, pole_top_y + 1), (tx + 1, pole_bot_y + 1), 4)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shaft_dark"],
                             (tx, pole_top_y), (tx, pole_bot_y), 4)
        _NS_aurelian._aaline(surface, _NS_aurelian.PALETTE["shaft_mid"],
                             (tx, pole_top_y), (tx, pole_bot_y), 2)

        # Gold tip on pole (spike)
        if pole_top_y < ty - 20:
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_darkest"], [
                (tx, pole_top_y - 6),
                (tx - 2, pole_top_y),
                (tx + 2, pole_top_y),
            ])
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_mid"], [
                (tx, pole_top_y - 5),
                (tx - 1, pole_top_y),
                (tx + 1, pole_top_y),
            ])
            pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_shine"],
                             (tx, pole_top_y - 5, 1, 1))

        # BANNER (blue flag billowing)
        if pole_top_y < ty - 20:
            billow = math.sin(phase * 2) * 3
            banner_pts = [
                (tx, pole_top_y + 5),
                (tx + 20, pole_top_y + 8 + int(billow)),
                (tx + 22, pole_top_y + 20 + int(billow * 0.5)),
                (tx + 18, pole_top_y + 30),
                (tx + 12, pole_top_y + 26),
                (tx + 6, pole_top_y + 30),
                (tx, pole_top_y + 28),
            ]
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["shadow_deep"],
                               [(px + 2, py + 2) for px, py in banner_pts])
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["banner_dark"], banner_pts)
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["banner_mid"], [
                (tx + 2, pole_top_y + 7),
                (tx + 18, pole_top_y + 10 + int(billow)),
                (tx + 19, pole_top_y + 20 + int(billow * 0.5)),
                (tx + 15, pole_top_y + 26),
                (tx + 10, pole_top_y + 24),
                (tx + 4, pole_top_y + 26),
                (tx + 2, pole_top_y + 24),
            ])
            # Emblem on banner (gold diamond)
            emblem_cx = tx + 11
            emblem_cy = pole_top_y + 16
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_darkest"], [
                (emblem_cx, emblem_cy - 4),
                (emblem_cx + 3, emblem_cy),
                (emblem_cx, emblem_cy + 4),
                (emblem_cx - 3, emblem_cy),
            ])
            _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["gold_mid"], [
                (emblem_cx, emblem_cy - 3),
                (emblem_cx + 2, emblem_cy),
                (emblem_cx, emblem_cy + 3),
                (emblem_cx - 2, emblem_cy),
            ])
            pygame.draw.rect(surface, _NS_aurelian.PALETTE["gold_shine"],
                             (emblem_cx, emblem_cy, 1, 1))

            # Gold trim on banner edge
            pygame.draw.line(surface, _NS_aurelian.PALETTE["gold_dark"],
                             (tx + 20, pole_top_y + 8 + int(billow)),
                             (tx + 18, pole_top_y + 30), 1)
            pygame.draw.line(surface, _NS_aurelian.PALETTE["gold_mid"],
                             (tx + 20, pole_top_y + 8 + int(billow)),
                             (tx + 18, pole_top_y + 30), 1)

        # Rising gold particles from base (buff effect)
        for i in range(10):
            part_t = (phase * 1.2 + i * 0.1) % 1.0
            angle = i * math.pi / 5 + phase * 0.3
            px = tx + int(math.cos(angle) * 30) - 0
            py = ty - int(part_t * 60)
            alpha = _NS_aurelian._alpha(220 * (1 - part_t))
            pygame.draw.rect(surface, (*_NS_aurelian.PALETTE["gold_mid"], alpha),
                             (px, py, 2, 2))
            pygame.draw.rect(surface, (*_NS_aurelian.PALETTE["gold_shine"], alpha),
                             (px, py, 1, 1))

    # ============================================================
    # SKILL R — CATACLYSM (ring of golden crystal spikes)
    # ============================================================
    def _draw_cataclysm_ground(surface, boss, x, y, timer, phase):
        """Ground crack circle where crystals will emerge."""
        tx, ty = _NS_aurelian._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = 70
        if progress < 0.3:
            # Wind-up: warning circle
            t = progress / 0.3
            alpha = _NS_aurelian._alpha(180 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_aurelian.PALETTE["gold_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_aurelian.PALETTE["gold_mid"], alpha),
                                (tx - r + 5, ty - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6), 2)
        else:
            # Ring is active
            alpha = _NS_aurelian._alpha(220)
            pygame.draw.ellipse(surface,
                                (*_NS_aurelian.PALETTE["crystal_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_aurelian.PALETTE["crystal_dark"], alpha),
                                (tx - r + 5, ty - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6), 2)

    def _draw_cataclysm_fg(surface, boss, x, y, timer, phase):
        """Ring of golden crystal spikes rising up."""
        tx, ty = _NS_aurelian._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = 70
        num_spikes = 14

        if progress < 0.3:
            # Wind-up: only warning glow at spike positions
            t = progress / 0.3
            for i in range(num_spikes):
                angle = i * math.pi * 2 / num_spikes
                sx = tx + int(math.cos(angle) * r)
                sy = ty + int(math.sin(angle) * r * 0.35)
                alpha = _NS_aurelian._alpha(180 * t)
                pygame.draw.rect(surface, (*_NS_aurelian.PALETTE["gold_light"], alpha),
                                 (sx - 1, sy - 1, 2, 2))
        else:
            # Spikes rising
            rise_t = min(1.0, (progress - 0.3) / 0.3)
            for i in range(num_spikes):
                angle = i * math.pi * 2 / num_spikes
                sx = tx + int(math.cos(angle) * r)
                sy_base = ty + int(math.sin(angle) * r * 0.35)

                # Height depends on rise animation
                spike_h = int(35 * rise_t + math.sin(phase * 2 + i) * 2)
                spike_w = 6

                # Crystal spike shape (tall pointed)
                _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["shadow_deep"], [
                    (sx + 2, sy_base - spike_h + 2),
                    (sx - spike_w + 2, sy_base + 2),
                    (sx + spike_w + 2, sy_base + 2),
                ])
                _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["crystal_darkest"], [
                    (sx, sy_base - spike_h),
                    (sx - spike_w, sy_base),
                    (sx + spike_w, sy_base),
                ])
                _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["crystal_dark"], [
                    (sx, sy_base - spike_h),
                    (sx - spike_w + 1, sy_base),
                    (sx + spike_w - 1, sy_base),
                ])
                # Left face (dark)
                _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["crystal_darkest"], [
                    (sx, sy_base - spike_h),
                    (sx - spike_w + 1, sy_base),
                    (sx - 1, sy_base),
                    (sx, sy_base - spike_h + 2),
                ])
                # Right face (bright)
                _NS_aurelian._poly(surface, _NS_aurelian.PALETTE["crystal_mid"], [
                    (sx, sy_base - spike_h),
                    (sx + spike_w - 1, sy_base),
                    (sx + 1, sy_base),
                    (sx, sy_base - spike_h + 2),
                ])
                # Bright edge (center ridge)
                pygame.draw.line(surface, _NS_aurelian.PALETTE["crystal_light"],
                                 (sx, sy_base - spike_h),
                                 (sx, sy_base), 1)
                # Tip glow
                pygame.draw.rect(surface, _NS_aurelian.PALETTE["crystal_shine"],
                                 (sx, sy_base - spike_h, 1, 1))
                pygame.draw.rect(surface, _NS_aurelian.PALETTE["white"],
                                 (sx, sy_base - spike_h, 1, 1))

                # Glowing base (energy)
                for glow_r in range(4, 0, -1):
                    alpha = _NS_aurelian._alpha(120 * (4 - glow_r) / 4)
                    _NS_aurelian._aacircle(surface,
                                           (*_NS_aurelian.PALETTE["gold_light"], alpha),
                                           (sx, sy_base), glow_r)

            # Golden particles floating up inside ring
            if rise_t > 0.5:
                for i in range(15):
                    part_t = (phase * 0.8 + i * 0.08) % 1.0
                    p_angle = i * math.pi * 2 / 15 + phase * 0.2
                    p_r = int(r * 0.6 * (1 - part_t * 0.3))
                    px = tx + int(math.cos(p_angle) * p_r)
                    py = ty + int(math.sin(p_angle) * p_r * 0.35) - int(part_t * 30)
                    alpha = _NS_aurelian._alpha(200 * (1 - part_t))
                    pygame.draw.rect(surface,
                                     (*_NS_aurelian.PALETTE["crystal_light"], alpha),
                                     (px, py, 2, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_aurelian.PALETTE["crystal_shine"], alpha),
                                     (px, py, 1, 1))


# ====================================================================
# ALIAS untuk convenience
# ====================================================================
draw_aurelian = _NS_aurelian.draw_aurelian


# ====================================================================================================
# MORVATH - MINI BOSS
# ====================================================================================================

class _NS_morvath:
    """Namespace morvath - HD rendering untuk mini boss Morvath."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Shark-blue skin
        "skin_darkest": (15, 30, 50),
        "skin_dark": (35, 60, 90),
        "skin_mid": (65, 105, 145),
        "skin_light": (110, 160, 200),
        "skin_shine": (170, 210, 240),

        # Cloak (dark Akatsuki-style)
        "cloak_darkest": (5, 5, 10),
        "cloak_dark": (18, 18, 25),
        "cloak_mid": (40, 40, 50),
        "cloak_light": (75, 75, 90),
        "cloak_edge": (110, 110, 130),

        # Red clouds (Akatsuki pattern)
        "cloud_dark": (75, 15, 20),
        "cloud_mid": (155, 35, 40),
        "cloud_light": (215, 70, 65),

        # Hair (dark blue-gray)
        "hair_dark": (25, 30, 45),
        "hair_mid": (55, 65, 85),
        "hair_light": (95, 110, 135),

        # Eyes (small piercing, pale yellow-white)
        "eye_dark": (30, 40, 15),
        "eye_mid": (150, 155, 60),
        "eye_light": (230, 235, 160),

        # Sword bandages (dirty white/tan)
        "bandage_dark": (85, 75, 55),
        "bandage_mid": (155, 140, 105),
        "bandage_light": (215, 200, 160),
        "bandage_shine": (245, 235, 200),

        # Sword scales (revealed shark skin) — grey-blue
        "sword_darkest": (25, 30, 40),
        "sword_dark": (55, 65, 80),
        "sword_mid": (110, 125, 145),
        "sword_light": (170, 185, 200),

        # WATER effects
        "water_darkest": (5, 20, 55),
        "water_dark": (15, 55, 110),
        "water_mid": (55, 130, 200),
        "water_light": (130, 195, 245),
        "water_shine": (210, 240, 255),
        "water_foam": (245, 250, 255),

        # Shark teeth
        "tooth_dark": (140, 130, 100),
        "tooth_mid": (215, 205, 175),
        "tooth_light": (250, 245, 220),

        # Forehead protector (metal)
        "metal_dark": (35, 35, 40),
        "metal_mid": (95, 95, 105),
        "metal_light": (170, 170, 180),
        "metal_shine": (230, 230, 240),

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
        color = _NS_morvath._clamp(color)
        if _NS_morvath.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_morvath._clamp(color)
        if _NS_morvath.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_morvath._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 130 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_morvath(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_morvath._detect_moving(boss)
        _NS_morvath._update_attack_anim(boss)
        attacking = getattr(boss, "_mv_attack_active", False)

        # Ambient
        _NS_morvath._draw_shadow(surface, x, y + 52)
        _NS_morvath._draw_water_aura(surface, x, y, pulse)
        _NS_morvath._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX (behind body)
        if active_skill == "w":
            _NS_morvath._draw_water_prison_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvath._draw_great_shark_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_morvath._draw_body_attack(surface, boss, x, y)
        elif moving:
            _NS_morvath._draw_body_walk(surface, boss, x, y)
        else:
            _NS_morvath._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX
        if active_skill == "q":
            _NS_morvath._draw_shark_bomb_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_morvath._draw_water_prison_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_morvath._draw_shark_bullets_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_morvath._draw_great_shark_fg(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 55)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_mv_attack_active", False))

        if not active:
            if timer >= cooldown - 30:
                boss._mv_attack_active = True
                boss._mv_attack_frame = 0
                active = True

        if active:
            boss._mv_attack_frame = int(getattr(boss, "_mv_attack_frame", 0)) + 1
            attack_duration = 35  # slower for heavy sword
            if boss._mv_attack_frame >= attack_duration:
                boss._mv_attack_active = False
                boss._mv_attack_frame = 0
                active = False

        attack_duration = 35
        boss._mv_attack_progress = (
            min(1.0, getattr(boss, "_mv_attack_frame", 0) / attack_duration)
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_mv_last_x"):
            boss._mv_last_x = boss.x
            boss._mv_last_y = boss.y
            return False
        dx = abs(boss.x - boss._mv_last_x)
        dy = abs(boss.y - boss._mv_last_y)
        boss._mv_last_x = boss.x
        boss._mv_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 2)
        _NS_morvath._draw_full_body(surface, x, y + bob,
                                    boss.direction, boss.pulse, "idle", 0)

    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 3)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_morvath._draw_full_body(surface, x + sway, y + bob,
                                    boss.direction, phase, "walk", 0)

    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_mv_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # HEAVY SWING (slower, more impact)
        if progress < 0.4:
            # Wind-up: LONG (swing back massive sword)
            t = progress / 0.4
            lunge = -int(t * 6) * boss.direction
            lift = int(t * 4)
        elif progress < 0.65:
            # SWING: heavy downward with lunge
            t = (progress - 0.4) / 0.25
            ease = 1 - (1 - t) ** 2
            lunge = int((-6 + ease * 24)) * boss.direction
            lift = int(4 - ease * 6)
        else:
            # Recovery
            t = (progress - 0.65) / 0.35
            lunge = int(18 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)

        _NS_morvath._draw_full_body(surface, x + lunge, y - lift,
                                    boss.direction, boss.pulse, "attack", progress)
        # Water swing trail
        _NS_morvath._draw_sword_water_slash(surface, boss, x + lunge,
                                             y - lift, progress)

    # ============================================================
    # FULL BODY
    # ============================================================
    def _draw_full_body(surface, cx, cy, facing, phase, action, atk_prog):
        # 1. Sword on back (if not attacking, otherwise held)
        # For simplicity: always draw sword either on back (idle) or in hand (attack)
        if action != "attack":
            _NS_morvath._draw_sword_on_back(surface, cx, cy, facing, phase)

        # 2. Cloak lower (long back)
        _NS_morvath._draw_cloak_lower(surface, cx, cy, facing, phase)

        # 3. Legs
        _NS_morvath._draw_legs(surface, cx, cy, facing, phase, action)

        # 4. Back arm
        _NS_morvath._draw_back_arm(surface, cx, cy, facing, phase, action, atk_prog)

        # 5. Torso (cloak upper)
        _NS_morvath._draw_torso(surface, cx, cy, facing, phase)

        # 6. Head + hair
        _NS_morvath._draw_head(surface, cx, cy - 24, facing, phase)

        # 7. Front arm + sword (if attacking)
        _NS_morvath._draw_front_arm(surface, cx, cy, facing, phase, action, atk_prog)

    def _draw_sword_on_back(surface, cx, cy, facing, phase):
        """Giant bandaged sword (Samehada style) — mounted on back."""
        # Position: diagonal on back, tip up-back
        back_dir = -facing
        # Base near hip, tip far up-back
        base_x = cx + back_dir * 6
        base_y = cy + 8
        tip_x = cx + back_dir * 14
        tip_y = cy - 34

        angle = math.atan2(tip_y - base_y, tip_x - base_x)
        sword_length = math.hypot(tip_x - base_x, tip_y - base_y)
        perp_x = -math.sin(angle)
        perp_y = math.cos(angle)

        # Sword width (very thick — massive)
        base_width = 9
        tip_width = 7

        # Sword body (bandaged wrap)
        bw_base_a = (base_x + int(perp_x * base_width),
                     base_y + int(perp_y * base_width))
        bw_base_b = (base_x - int(perp_x * base_width),
                     base_y - int(perp_y * base_width))
        bw_tip_a = (tip_x + int(perp_x * tip_width),
                    tip_y + int(perp_y * tip_width))
        bw_tip_b = (tip_x - int(perp_x * tip_width),
                    tip_y - int(perp_y * tip_width))

        sword_pts = [bw_base_a, bw_tip_a, bw_tip_b, bw_base_b]
        # Shadow
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["shadow_deep"],
                          [(px + 3, py + 3) for px, py in sword_pts])
        # Base bandage
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["bandage_dark"], sword_pts)

        # Inner bandage (highlight)
        inner_offset = 2
        inner_pts = [
            (base_x + int(perp_x * (base_width - inner_offset)),
             base_y + int(perp_y * (base_width - inner_offset))),
            (tip_x + int(perp_x * (tip_width - inner_offset)),
             tip_y + int(perp_y * (tip_width - inner_offset))),
            (tip_x - int(perp_x * (tip_width - inner_offset)),
             tip_y - int(perp_y * (tip_width - inner_offset))),
            (base_x - int(perp_x * (base_width - inner_offset)),
             base_y - int(perp_y * (base_width - inner_offset))),
        ]
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["bandage_mid"], inner_pts)

        # Bandage wrap lines (diagonal stripes across the sword)
        num_wraps = 8
        for i in range(num_wraps):
            wrap_t = (i + 0.5) / num_wraps
            wx = int(base_x + (tip_x - base_x) * wrap_t)
            wy = int(base_y + (tip_y - base_y) * wrap_t)
            w = base_width + (tip_width - base_width) * wrap_t
            wa = (wx + int(perp_x * w), wy + int(perp_y * w))
            wb = (wx - int(perp_x * w), wy - int(perp_y * w))
            # Wrap line (dark)
            _NS_morvath._aaline(surface, _NS_morvath.PALETTE["bandage_dark"],
                                wa, wb, 1)

        # Bright bandage highlight along one side
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["bandage_light"],
                            (base_x + int(perp_x * (base_width - 1)),
                             base_y + int(perp_y * (base_width - 1))),
                            (tip_x + int(perp_x * (tip_width - 1)),
                             tip_y + int(perp_y * (tip_width - 1))), 1)

        # POMMEL (rounded end near base)
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["shadow_deep"],
                              (base_x, base_y), base_width + 2)
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["bandage_dark"],
                              (base_x, base_y), base_width + 1)
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["bandage_mid"],
                              (base_x, base_y), base_width)

        # Small hilt handle sticking below (bandaged)
        handle_len = 12
        handle_end_x = base_x - int(math.cos(angle) * handle_len)
        handle_end_y = base_y - int(math.sin(angle) * handle_len)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["shadow_deep"],
                            (base_x + 1, base_y + 1),
                            (handle_end_x + 1, handle_end_y + 1), 5)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["bandage_dark"],
                            (base_x, base_y), (handle_end_x, handle_end_y), 4)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["bandage_mid"],
                            (base_x, base_y), (handle_end_x, handle_end_y), 2)

        # Rounded tip cap (bandage wraps over top)
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["bandage_dark"],
                              (tip_x, tip_y), tip_width - 1)
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["bandage_mid"],
                              (tip_x, tip_y), tip_width - 2)
        pygame.draw.rect(surface, _NS_morvath.PALETTE["bandage_light"],
                         (tip_x, tip_y, 1, 1))

    def _draw_cloak_lower(surface, cx, cy, facing, phase):
        """Long dark Akatsuki cloak flowing down."""
        sway = math.sin(phase * 0.6) * 2

        cloak_pts = [
            (cx - 15, cy + 8),
            (cx - 17, cy + 18),
            (cx - 19, cy + 30),
            (cx - 17 + int(sway), cy + 42),
            (cx - 10, cy + 46),
            (cx, cy + 47),
            (cx + 10, cy + 46),
            (cx + 17 - int(sway), cy + 42),
            (cx + 19, cy + 30),
            (cx + 17, cy + 18),
            (cx + 15, cy + 8),
        ]
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in cloak_pts])
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["cloak_darkest"], cloak_pts)
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["cloak_dark"], [
            (cx - 14, cy + 10),
            (cx - 16, cy + 20),
            (cx - 16 + int(sway), cy + 40),
            (cx - 8, cy + 43),
            (cx + 8, cy + 43),
            (cx + 16 - int(sway), cy + 40),
            (cx + 16, cy + 20),
            (cx + 14, cy + 10),
        ])
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["cloak_mid"], [
            (cx - 12, cy + 12),
            (cx - 14, cy + 22),
            (cx - 12 + int(sway * 0.5), cy + 36),
            (cx, cy + 40),
            (cx + 12 - int(sway * 0.5), cy + 36),
            (cx + 14, cy + 22),
            (cx + 12, cy + 12),
        ])

        # Vertical fold shadows
        for x_off in (-9, -3, 3, 9):
            pygame.draw.line(surface, _NS_morvath.PALETTE["cloak_darkest"],
                             (cx + x_off, cy + 14),
                             (cx + x_off + int(sway * 0.3), cy + 42), 1)

        # Red cloud patterns on cloak
        _NS_morvath._draw_red_cloud(surface, cx - 9, cy + 20, 3)
        _NS_morvath._draw_red_cloud(surface, cx + 7, cy + 26, 3)
        _NS_morvath._draw_red_cloud(surface, cx - 4, cy + 36, 2)
        _NS_morvath._draw_red_cloud(surface, cx + 10, cy + 38, 2)

    def _draw_red_cloud(surface, cx, cy, size):
        """Akatsuki red cloud symbol."""
        pts = [
            (cx - size * 2, cy),
            (cx - size, cy - size),
            (cx, cy - size),
            (cx + size, cy - size),
            (cx + size * 2, cy),
            (cx + size, cy + size // 2),
            (cx - size, cy + size // 2),
        ]
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["cloud_dark"], pts)
        inner_pts = [
            (cx - size, cy),
            (cx, cy - size + 1),
            (cx + size, cy),
            (cx, cy + 1),
        ]
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["cloud_mid"], inner_pts)
        pygame.draw.rect(surface, _NS_morvath.PALETTE["cloud_light"],
                         (cx - 1, cy - 1, 2, 1))

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Legs in dark pants."""
        leg_sway = 0
        if action == "walk":
            leg_sway = math.sin(phase) * 3

        # Back leg
        back_x = cx - 4
        back_y_top = cy + 8
        back_y_bot = cy + 42 + int(-leg_sway)

        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["shadow_deep"],
                            (back_x + 1, back_y_top + 1),
                            (back_x + 1, back_y_bot + 1), 8)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["cloak_darkest"],
                            (back_x, back_y_top), (back_x, back_y_bot), 7)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["cloak_dark"],
                            (back_x, back_y_top), (back_x, back_y_bot), 5)

        # Front leg
        front_x = cx + 4
        front_y_top = cy + 8
        front_y_bot = cy + 42 + int(leg_sway)

        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["shadow_deep"],
                            (front_x + 1, front_y_top + 1),
                            (front_x + 1, front_y_bot + 1), 8)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["cloak_darkest"],
                            (front_x, front_y_top), (front_x, front_y_bot), 7)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["cloak_dark"],
                            (front_x, front_y_top), (front_x, front_y_bot), 5)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["cloak_mid"],
                            (front_x - 1, front_y_top), (front_x - 1, front_y_bot), 2)

        # Sandals with bandages
        for foot_x, foot_y in ((back_x, back_y_bot), (front_x, front_y_bot)):
            pygame.draw.ellipse(surface, _NS_morvath.PALETTE["shadow_deep"],
                                (foot_x - 5, foot_y - 1, 12, 6))
            pygame.draw.ellipse(surface, _NS_morvath.PALETTE["bandage_dark"],
                                (foot_x - 4, foot_y, 10, 4))
            pygame.draw.ellipse(surface, _NS_morvath.PALETTE["bandage_mid"],
                                (foot_x - 4, foot_y, 10, 3))
            # Bandage wrap on shin (visible above sandal)
            pygame.draw.line(surface, _NS_morvath.PALETTE["bandage_dark"],
                             (foot_x - 3, foot_y - 3), (foot_x + 4, foot_y - 3), 2)
            pygame.draw.line(surface, _NS_morvath.PALETTE["bandage_mid"],
                             (foot_x - 3, foot_y - 3), (foot_x + 4, foot_y - 3), 1)

    def _draw_torso(surface, cx, cy, facing, phase):
        """Upper body with cloak, V-collar opens."""
        # Base torso shape
        torso_pts = [
            (cx - 13, cy - 8),
            (cx - 15, cy - 2),
            (cx - 14, cy + 6),
            (cx - 9, cy + 10),
            (cx + 9, cy + 10),
            (cx + 14, cy + 6),
            (cx + 15, cy - 2),
            (cx + 13, cy - 8),
            (cx + 6, cy - 12),
            (cx - 6, cy - 12),
        ]
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in torso_pts])
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["cloak_darkest"], torso_pts)
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["cloak_dark"], [
            (cx - 12, cy - 6),
            (cx - 14, cy - 1),
            (cx - 13, cy + 5),
            (cx - 8, cy + 9),
            (cx + 8, cy + 9),
            (cx + 13, cy + 5),
            (cx + 14, cy - 1),
            (cx + 12, cy - 6),
            (cx + 5, cy - 10),
            (cx - 5, cy - 10),
        ])
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["cloak_mid"], [
            (cx - 10, cy - 4),
            (cx - 11, cy + 2),
            (cx - 7, cy + 7),
            (cx + 7, cy + 7),
            (cx + 11, cy + 2),
            (cx + 10, cy - 4),
            (cx + 4, cy - 9),
            (cx - 4, cy - 9),
        ])

        # V-collar opening (showing blue chest skin)
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["skin_darkest"], [
            (cx - 4, cy - 10),
            (cx + 4, cy - 10),
            (cx, cy - 2),
        ])
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["skin_dark"], [
            (cx - 3, cy - 9),
            (cx + 3, cy - 9),
            (cx, cy - 3),
        ])
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["skin_mid"], [
            (cx - 2, cy - 8),
            (cx + 2, cy - 8),
            (cx, cy - 4),
        ])

        # Red cloud on chest
        _NS_morvath._draw_red_cloud(surface, cx - 8, cy - 3, 2)
        _NS_morvath._draw_red_cloud(surface, cx + 8, cy + 3, 2)

        # Belt/rope (over cloak)
        pygame.draw.rect(surface, _NS_morvath.PALETTE["shadow_deep"],
                         (cx - 13, cy + 7, 27, 4))
        pygame.draw.rect(surface, _NS_morvath.PALETTE["bandage_dark"],
                         (cx - 12, cy + 8, 25, 3))
        pygame.draw.rect(surface, _NS_morvath.PALETTE["bandage_mid"],
                         (cx - 12, cy + 8, 25, 1))
        # Small knot
        pygame.draw.rect(surface, _NS_morvath.PALETTE["bandage_dark"],
                         (cx - 2, cy + 7, 4, 5))

        # Diagonal strap (sword harness across chest)
        strap_start_x = cx + facing * 12
        strap_start_y = cy - 6
        strap_end_x = cx - facing * 10
        strap_end_y = cy + 8
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["shadow_deep"],
                            (strap_start_x + 1, strap_start_y + 1),
                            (strap_end_x + 1, strap_end_y + 1), 3)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["bandage_dark"],
                            (strap_start_x, strap_start_y),
                            (strap_end_x, strap_end_y), 3)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["bandage_mid"],
                            (strap_start_x, strap_start_y),
                            (strap_end_x, strap_end_y), 1)

    def _draw_head(surface, cx, cy, facing, phase):
        """Blue shark-skin head with fin-like hair, gills, forehead protector."""
        # HAIR (spiky blue-gray, backward-swept)
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["shadow_deep"], [
            (cx - 7, cy + 4),
            (cx - 10, cy - 2),
            (cx - 11, cy - 8),
            (cx - 8, cy - 12),
            (cx - 3, cy - 14),
            (cx + 3, cy - 14),
            (cx + 8, cy - 12),
            (cx + 11, cy - 8),
            (cx + 10, cy - 2),
            (cx + 7, cy + 4),
        ])
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["hair_dark"], [
            (cx - 6, cy + 3),
            (cx - 9, cy - 2),
            (cx - 10, cy - 8),
            (cx - 7, cy - 11),
            (cx - 3, cy - 13),
            (cx + 3, cy - 13),
            (cx + 7, cy - 11),
            (cx + 10, cy - 8),
            (cx + 9, cy - 2),
            (cx + 6, cy + 3),
        ])
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["hair_mid"], [
            (cx - 8, cy - 8),
            (cx - 6, cy - 11),
            (cx - 2, cy - 12),
            (cx + 2, cy - 12),
            (cx + 6, cy - 11),
            (cx + 8, cy - 8),
            (cx + 6, cy - 4),
            (cx - 6, cy - 4),
        ])
        # Hair spikes at top (shark-fin style)
        for spike_i, sx_off in enumerate((-4, -1, 2, 5)):
            _NS_morvath._poly(surface, _NS_morvath.PALETTE["hair_dark"], [
                (cx + sx_off, cy - 12),
                (cx + sx_off + 1, cy - 15),
                (cx + sx_off + 2, cy - 12),
            ])
            _NS_morvath._poly(surface, _NS_morvath.PALETTE["hair_mid"], [
                (cx + sx_off, cy - 12),
                (cx + sx_off + 1, cy - 14),
                (cx + sx_off + 2, cy - 12),
            ])
        pygame.draw.rect(surface, _NS_morvath.PALETTE["hair_light"],
                         (cx - 1, cy - 10, 2, 1))

        # FACE (blue shark skin)
        face_pts = [
            (cx - 6, cy + 5),
            (cx - 7, cy - 2),
            (cx - 5, cy - 7),
            (cx + 5, cy - 7),
            (cx + 7, cy - 2),
            (cx + 6, cy + 5),
        ]
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["skin_darkest"], face_pts)
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["skin_dark"], [
            (cx - 5, cy + 4),
            (cx - 6, cy - 2),
            (cx - 4, cy - 6),
            (cx + 4, cy - 6),
            (cx + 6, cy - 2),
            (cx + 5, cy + 4),
        ])
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["skin_mid"], [
            (cx - 4, cy + 3),
            (cx - 5, cy - 2),
            (cx - 3, cy - 5),
            (cx + 3, cy - 5),
            (cx + 5, cy - 2),
            (cx + 4, cy + 3),
        ])
        # Highlight (cheekbone/forehead)
        pygame.draw.rect(surface, _NS_morvath.PALETTE["skin_light"],
                         (cx - 3, cy - 4, 2, 1))
        pygame.draw.rect(surface, _NS_morvath.PALETTE["skin_light"],
                         (cx + 2, cy - 4, 2, 1))
        pygame.draw.rect(surface, _NS_morvath.PALETTE["skin_shine"],
                         (cx - 3, cy - 4, 1, 1))

        # GILL MARKS (3 vertical lines on cheeks — signature shark feature)
        for gill_x_side in (-facing, facing):
            for gill_i in range(3):
                gill_x = cx + gill_x_side * 4
                gill_y = cy - 1 + gill_i * 2
                pygame.draw.line(surface, _NS_morvath.PALETTE["skin_darkest"],
                                 (gill_x, gill_y), (gill_x + gill_x_side, gill_y), 1)

        # FOREHEAD PROTECTOR (metal band with slash mark)
        pygame.draw.rect(surface, _NS_morvath.PALETTE["shadow_deep"],
                         (cx - 7, cy - 8, 14, 4))
        pygame.draw.rect(surface, _NS_morvath.PALETTE["metal_dark"],
                         (cx - 7, cy - 8, 14, 3))
        pygame.draw.rect(surface, _NS_morvath.PALETTE["metal_mid"],
                         (cx - 7, cy - 8, 14, 2))
        pygame.draw.rect(surface, _NS_morvath.PALETTE["metal_light"],
                         (cx - 7, cy - 8, 14, 1))
        # Slash mark through the emblem (missing-nin)
        pygame.draw.line(surface, _NS_morvath.PALETTE["shadow_deep"],
                         (cx - 4, cy - 8), (cx + 4, cy - 5), 1)

        # EYES (small piercing yellow-white)
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        for eye_x_off in (-2, 2):
            ex = cx + eye_x_off * facing
            ey = cy - 3
            # Dark socket
            pygame.draw.rect(surface, _NS_morvath.PALETTE["shadow_deep"],
                             (ex - 1, ey, 2, 1))
            # Glow
            for r in range(3, 0, -1):
                alpha = _NS_morvath._alpha(80 * (3 - r) / 3 * eye_pulse)
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["eye_mid"], alpha),
                                      (ex, ey), r)
            pygame.draw.rect(surface, _NS_morvath.PALETTE["eye_light"],
                             (ex, ey, 1, 1))

        # SHARK GRIN (jagged teeth mouth line)
        for tooth_i in range(5):
            tx = cx - 3 + tooth_i * 2
            ty = cy + 2
            # Tooth (small triangle)
            _NS_morvath._poly(surface, _NS_morvath.PALETTE["tooth_mid"], [
                (tx, ty),
                (tx + 1, ty + 2),
                (tx + 2, ty),
            ])
            pygame.draw.rect(surface, _NS_morvath.PALETTE["tooth_light"],
                             (tx + 1, ty, 1, 1))
        # Mouth line
        pygame.draw.line(surface, _NS_morvath.PALETTE["shadow_deep"],
                         (cx - 4, cy + 1), (cx + 4, cy + 1), 1)

    def _draw_back_arm(surface, cx, cy, facing, phase, action, atk_prog):
        """Back arm - not holding anything."""
        sway = math.sin(phase * 0.9) * 1
        back_shoulder_x = cx - facing * 12
        back_shoulder_y = cy - 6
        back_hand_x = back_shoulder_x - facing * 2 + int(sway)
        back_hand_y = cy + 10

        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["shadow_deep"],
                            (back_shoulder_x + 1, back_shoulder_y + 1),
                            (back_hand_x + 1, back_hand_y + 1), 6)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["cloak_darkest"],
                            (back_shoulder_x, back_shoulder_y),
                            (back_hand_x, back_hand_y), 5)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["cloak_dark"],
                            (back_shoulder_x, back_shoulder_y),
                            (back_hand_x, back_hand_y), 3)
        # Back hand (blue skin)
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["skin_darkest"],
                              (back_hand_x, back_hand_y), 3)
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["skin_dark"],
                              (back_hand_x, back_hand_y), 2)

    def _draw_front_arm(surface, cx, cy, facing, phase, action, atk_prog):
        """Front arm — during attack, holds giant sword."""
        sway = math.sin(phase * 0.9) * 2
        front_shoulder_x = cx + facing * 12
        front_shoulder_y = cy - 6

        # Sword angle
        if action == "attack":
            if atk_prog < 0.4:
                # Wind-up: sword raised HIGH above head
                t = atk_prog / 0.4
                sword_angle = -math.pi * 0.25 - t * math.pi * 0.85
                hand_off_x = facing * int(-8 - t * 4)
                hand_off_y = int(-6 - t * 12)
            elif atk_prog < 0.65:
                # SWING: heavy downward
                t = (atk_prog - 0.4) / 0.25
                ease = 1 - (1 - t) ** 2
                sword_angle = -math.pi * 1.1 + ease * math.pi * 1.25
                hand_off_x = facing * int(-12 + ease * 26)
                hand_off_y = int(-18 + ease * 22)
            else:
                # Recovery
                t = (atk_prog - 0.65) / 0.35
                sword_angle = math.pi * 0.15 - t * math.pi * 0.2
                hand_off_x = facing * int(14 - t * 10)
                hand_off_y = int(4 - t * 4)
        elif action == "walk":
            sword_angle = 0
            hand_off_x = facing * 8
            hand_off_y = int(4 + sway)
        else:
            sword_angle = 0
            hand_off_x = facing * 8
            hand_off_y = int(4 - sway)

        front_hand_x = front_shoulder_x + hand_off_x
        front_hand_y = front_shoulder_y + hand_off_y

        # Elbow
        elbow_x = int((front_shoulder_x + front_hand_x) / 2) + facing * 3
        elbow_y = int((front_shoulder_y + front_hand_y) / 2) + 1

        # Upper arm (cloak sleeve)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["shadow_deep"],
                            (front_shoulder_x + 1, front_shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 6)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["cloak_darkest"],
                            (front_shoulder_x, front_shoulder_y),
                            (elbow_x, elbow_y), 5)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["cloak_dark"],
                            (front_shoulder_x, front_shoulder_y),
                            (elbow_x, elbow_y), 3)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["cloak_mid"],
                            (front_shoulder_x - 1, front_shoulder_y - 1),
                            (elbow_x - 1, elbow_y - 1), 1)

        # Forearm (blue skin exposed)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (front_hand_x + 1, front_hand_y + 1), 5)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["skin_darkest"],
                            (elbow_x, elbow_y),
                            (front_hand_x, front_hand_y), 4)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["skin_dark"],
                            (elbow_x, elbow_y),
                            (front_hand_x, front_hand_y), 2)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["skin_mid"],
                            (elbow_x, elbow_y - 1),
                            (front_hand_x, front_hand_y - 1), 1)

        # Hand (blue with claw-like fingers)
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["skin_darkest"],
                              (front_hand_x, front_hand_y), 4)
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["skin_dark"],
                              (front_hand_x, front_hand_y), 3)
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["skin_mid"],
                              (front_hand_x, front_hand_y), 2)
        pygame.draw.rect(surface, _NS_morvath.PALETTE["skin_light"],
                         (front_hand_x - 1, front_hand_y - 1, 1, 1))

        # SWORD IN HAND (during attack)
        if action == "attack":
            _NS_morvath._draw_giant_sword_held(surface, front_hand_x, front_hand_y,
                                                sword_angle, facing)

    def _draw_giant_sword_held(surface, hand_x, hand_y, angle, facing):
        """Giant bandaged sword held in hand — same style as on back."""
        actual_angle = angle if facing > 0 else math.pi - angle

        # Sword extends from hand
        sword_length = 42
        base_width = 9
        tip_width = 7

        tip_x = hand_x + int(math.cos(actual_angle) * sword_length)
        tip_y = hand_y + int(math.sin(actual_angle) * sword_length)

        # Handle extends slightly back from hand
        handle_len = 8
        handle_end_x = hand_x - int(math.cos(actual_angle) * handle_len)
        handle_end_y = hand_y - int(math.sin(actual_angle) * handle_len)

        perp_x = -math.sin(actual_angle)
        perp_y = math.cos(actual_angle)

        # BLADE BODY (bandaged, tapered)
        # Where blade starts (just above hand)
        blade_start_x = hand_x + int(math.cos(actual_angle) * 2)
        blade_start_y = hand_y + int(math.sin(actual_angle) * 2)

        blade_pts = [
            (blade_start_x + int(perp_x * base_width),
             blade_start_y + int(perp_y * base_width)),
            (tip_x + int(perp_x * tip_width),
             tip_y + int(perp_y * tip_width)),
            (tip_x - int(perp_x * tip_width),
             tip_y - int(perp_y * tip_width)),
            (blade_start_x - int(perp_x * base_width),
             blade_start_y - int(perp_y * base_width)),
        ]
        # Shadow
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["shadow_deep"],
                          [(px + 3, py + 3) for px, py in blade_pts])
        # Base bandage
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["bandage_dark"], blade_pts)

        # Inner brighter bandage
        inner_pts = [
            (blade_start_x + int(perp_x * (base_width - 2)),
             blade_start_y + int(perp_y * (base_width - 2))),
            (tip_x + int(perp_x * (tip_width - 2)),
             tip_y + int(perp_y * (tip_width - 2))),
            (tip_x - int(perp_x * (tip_width - 2)),
             tip_y - int(perp_y * (tip_width - 2))),
            (blade_start_x - int(perp_x * (base_width - 2)),
             blade_start_y - int(perp_y * (base_width - 2))),
        ]
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["bandage_mid"], inner_pts)

        # Bandage wrap lines
        num_wraps = 10
        for i in range(num_wraps):
            wrap_t = (i + 0.5) / num_wraps
            wx = int(blade_start_x + (tip_x - blade_start_x) * wrap_t)
            wy = int(blade_start_y + (tip_y - blade_start_y) * wrap_t)
            w = base_width + (tip_width - base_width) * wrap_t
            wa = (wx + int(perp_x * w), wy + int(perp_y * w))
            wb = (wx - int(perp_x * w), wy - int(perp_y * w))
            pygame.draw.line(surface, _NS_morvath.PALETTE["bandage_dark"],
                             wa, wb, 1)

        # Highlight edge
        pygame.draw.line(surface, _NS_morvath.PALETTE["bandage_light"],
                         (blade_start_x + int(perp_x * (base_width - 1)),
                          blade_start_y + int(perp_y * (base_width - 1))),
                         (tip_x + int(perp_x * (tip_width - 1)),
                          tip_y + int(perp_y * (tip_width - 1))), 1)

        # Rounded tip
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["bandage_dark"],
                              (tip_x, tip_y), tip_width - 1)
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["bandage_mid"],
                              (tip_x, tip_y), tip_width - 2)
        pygame.draw.rect(surface, _NS_morvath.PALETTE["bandage_light"],
                         (tip_x, tip_y, 1, 1))

        # Pommel/guard at hand
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["shadow_deep"],
                              (hand_x, hand_y), base_width + 1)
        _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["bandage_dark"],
                              (hand_x, hand_y), base_width)

        # Handle extends back
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["shadow_deep"],
                            (hand_x + 1, hand_y + 1),
                            (handle_end_x + 1, handle_end_y + 1), 5)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["bandage_dark"],
                            (hand_x, hand_y), (handle_end_x, handle_end_y), 4)
        _NS_morvath._aaline(surface, _NS_morvath.PALETTE["bandage_mid"],
                            (hand_x, hand_y), (handle_end_x, handle_end_y), 2)

    # ============================================================
    # BASIC ATTACK — SWORD WATER SLASH
    # ============================================================
    def _draw_sword_water_slash(surface, boss, x, y, progress):
        """Water arc during heavy sword swing."""
        if progress < 0.4 or progress > 0.8:
            return

        facing = boss.direction
        if progress < 0.65:
            t = (progress - 0.4) / 0.25
        else:
            t = 1 - (progress - 0.65) / 0.15
        intensity = math.sin(t * math.pi)

        cx = x + facing * 22
        cy = y - 4

        arc_radius = int(35 + t * 10)  # bigger for heavy sword
        segments = 20
        prev = None
        for i in range(segments + 1):
            seg_t = i / segments
            base_angle = -math.pi * 0.6 * facing
            seg_angle = base_angle + seg_t * math.pi * facing
            sx = cx + int(math.cos(seg_angle) * arc_radius)
            sy = cy + int(math.sin(seg_angle) * arc_radius * 0.7)

            if prev is not None and seg_t <= t * 1.2:
                fade = 1.0 - max(0, (t * 1.2 - seg_t) * 1.5)
                alpha_outer = _NS_morvath._alpha(200 * intensity * fade)
                alpha_core = _NS_morvath._alpha(255 * intensity * fade)

                # Thick water arc
                pygame.draw.line(surface,
                                 (*_NS_morvath.PALETTE["water_darkest"], alpha_outer),
                                 prev, (sx, sy), 8)
                pygame.draw.line(surface,
                                 (*_NS_morvath.PALETTE["water_dark"], alpha_outer),
                                 prev, (sx, sy), 6)
                pygame.draw.line(surface,
                                 (*_NS_morvath.PALETTE["water_mid"], alpha_core),
                                 prev, (sx, sy), 4)
                pygame.draw.line(surface,
                                 (*_NS_morvath.PALETTE["water_light"], alpha_core),
                                 prev, (sx, sy), 2)
                pygame.draw.line(surface,
                                 (*_NS_morvath.PALETTE["water_foam"], alpha_core),
                                 prev, (sx, sy), 1)

                # Water droplets flying
                if i % 3 == 0 and fade > 0.4:
                    for pi in range(2):
                        p_off_x = int(math.cos(seg_angle) * (pi + 2) * 2)
                        p_off_y = int(math.sin(seg_angle) * (pi + 2) * 2)
                        pygame.draw.rect(surface,
                                         (*_NS_morvath.PALETTE["water_light"], alpha_core),
                                         (sx + p_off_x, sy + p_off_y, 2, 2))
                        pygame.draw.rect(surface,
                                         (*_NS_morvath.PALETTE["water_foam"], alpha_core),
                                         (sx + p_off_x, sy + p_off_y, 1, 1))
            prev = (sx, sy)

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 28), pygame.SRCALPHA)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 14 - radius,
                                 110 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, 170), (5, 8, 120, 12))
        surface.blit(shadow, (x - 65, y - 14))

    def _draw_water_aura(surface, x, y, phase):
        """Deep water aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75

        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for radius in range(80, 5, -5):
            alpha = _NS_morvath._alpha((80 - radius) * 0.8 * pulse)
            if alpha > 0:
                _NS_morvath._aacircle(aura,
                                      (*_NS_morvath.PALETTE["water_darkest"], alpha),
                                      (100, 85), radius)
        for radius in range(50, 5, -4):
            alpha = _NS_morvath._alpha((50 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_morvath._aacircle(aura,
                                      (*_NS_morvath.PALETTE["water_dark"], alpha),
                                      (100, 85), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_morvath._alpha((30 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_morvath._aacircle(aura,
                                      (*_NS_morvath.PALETTE["water_mid"], alpha),
                                      (100, 85), radius)
        surface.blit(aura, (x - 100, y - 85))

        # Water droplets floating
        for i in range(10):
            angle = phase * 0.3 + i * math.pi / 5
            radius = 34 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            pygame.draw.rect(surface, _NS_morvath.PALETTE["water_mid"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_morvath.PALETTE["water_light"], (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Water ripples on ground."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_morvath.PALETTE["water_darkest"], 200),
                            (5, 17, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_morvath.PALETTE["water_dark"], 220),
                            (14, 19, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_morvath.PALETTE["water_mid"], 200),
                            (25, 21, 110, 16), 1)

        # Ripples expanding
        for i in range(3):
            r_off = int((phase * 20 + i * 30) % 60)
            alpha = _NS_morvath._alpha(150 * (1 - r_off / 60))
            pygame.draw.ellipse(ring, (*_NS_morvath.PALETTE["water_light"], alpha),
                                (25 - r_off // 4, 21 - r_off // 8,
                                 110 + r_off // 2, 16 + r_off // 4), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_morvath.PALETTE["water_shine"],
                                 _NS_morvath._alpha(180 * pulse)),
                                (15, 10, 130, 34), 1)
        surface.blit(ring, (x - 80, y - 25))

    # ============================================================
    # SKILL Q — SHARK BOMB (water shark projectile)
    # ============================================================
    def _draw_shark_bomb_fx(surface, boss, x, y, timer, phase):
        """Shark-shaped water bomb traveling to target."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morvath._target_position(boss, x, y)

        start_x = x + facing * 20
        start_y = y - 6

        if progress < 0.15:
            # Charge in hands (forming shark)
            t = progress / 0.15
            cx = start_x
            cy = start_y
            r = int(6 + t * 8)
            for lr in range(r + 4, 0, -1):
                alpha = _NS_morvath._alpha(150 * (r + 4 - lr) / (r + 4))
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["water_dark"], alpha),
                                      (cx, cy), lr)
            _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["water_darkest"],
                                  (cx, cy), r - 2)
            _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["water_mid"],
                                  (cx, cy), r - 4)
            _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["water_light"],
                                  (cx, cy), max(1, r - 6))
        else:
            # Traveling shark
            t = (progress - 0.15) / 0.85
            t = min(1.0, t)
            bx = int(start_x + (tx - start_x) * t)
            by = int(start_y + (ty - start_y) * t)

            # Direction the shark is facing
            travel_angle = math.atan2(ty - start_y, tx - start_x)

            # Water trail behind
            for i in range(8):
                trail_t = max(0.0, t - i * 0.06)
                px = int(start_x + (tx - start_x) * trail_t)
                py = int(start_y + (ty - start_y) * trail_t)
                alpha = _NS_morvath._alpha(220 - i * 25)
                size = max(1, 7 - i)
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["water_dark"], alpha),
                                      (px, py), size)
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["water_mid"], alpha),
                                      (px, py), max(1, size - 2))
                # Droplets
                if i < 4:
                    for si in range(2):
                        sp_off = math.sin(t * 5 + i + si) * (size + 2)
                        sp_x = px + int(math.cos(travel_angle + math.pi / 2) * sp_off)
                        sp_y = py + int(math.sin(travel_angle + math.pi / 2) * sp_off)
                        pygame.draw.rect(surface,
                                         (*_NS_morvath.PALETTE["water_light"], alpha),
                                         (sp_x, sp_y, 1, 1))

            # SHARK SHAPE (main body)
            _NS_morvath._draw_water_shark(surface, bx, by, travel_angle, facing,
                                           size_mult=1.2)

            # Impact splash
            if t > 0.9:
                st = (t - 0.9) / 0.1
                r = int(15 + st * 25)
                alpha = _NS_morvath._alpha(240 * (1 - st))
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["water_darkest"], alpha),
                                      (tx, ty), r + 3, 3)
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["water_dark"], alpha),
                                      (tx, ty), r, 3)
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["water_mid"], alpha),
                                      (tx, ty), max(1, r - 5), 2)
                for i in range(10):
                    a = i * math.pi / 5
                    ex = tx + int(math.cos(a) * r)
                    ey = ty + int(math.sin(a) * r * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_morvath.PALETTE["water_foam"], alpha),
                                     (ex, ey, 2, 2))

    def _draw_water_shark(surface, cx, cy, angle, facing, size_mult=1.0):
        """Draw a shark shape made of water."""
        # Shark body (elongated ellipse in direction of travel)
        body_len = int(18 * size_mult)
        body_w = int(6 * size_mult)

        # Rotate shark based on angle
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Body oval (approximated with several circles)
        for offset in range(-body_len // 2, body_len // 2 + 1, 2):
            # Width tapers toward tail
            t = offset / (body_len // 2)  # -1 (tail) to +1 (head)
            if t > 0.5:
                # Head part
                w = int(body_w * (1 - (t - 0.5) * 0.4))
            elif t < -0.5:
                # Tail part - narrower
                w = int(body_w * (1 - (abs(t) - 0.5) * 1.5))
            else:
                w = body_w

            if w < 1:
                w = 1

            sx = cx + int(cos_a * offset)
            sy = cy + int(sin_a * offset)
            _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["water_darkest"],
                                  (sx, sy), w)
            _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["water_dark"],
                                  (sx, sy), max(1, w - 1))
            _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["water_mid"],
                                  (sx, sy), max(1, w - 2))
            if w > 3:
                _NS_morvath._aacircle(surface, _NS_morvath.PALETTE["water_light"],
                                      (sx, sy - 1), max(1, w - 4))

        # Head (front of shark)
        head_x = cx + int(cos_a * body_len // 2)
        head_y = cy + int(sin_a * body_len // 2)

        # DORSAL FIN (top)
        perp_x = -sin_a
        perp_y = cos_a
        fin_base_x = cx - int(cos_a * 2)
        fin_base_y = cy - int(sin_a * 2)
        fin_tip_x = fin_base_x + int(perp_x * body_w * 1.5)
        fin_tip_y = fin_base_y + int(perp_y * body_w * 1.5)

        fin_pts = [
            (fin_base_x - int(cos_a * 4), fin_base_y - int(sin_a * 4)),
            (fin_tip_x, fin_tip_y),
            (fin_base_x + int(cos_a * 3), fin_base_y + int(sin_a * 3)),
        ]
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["water_darkest"], fin_pts)
        _NS_morvath._poly(surface, _NS_morvath.PALETTE["water_dark"], [
            fin_pts[0],
            (int((fin_pts[1][0] + fin_pts[0][0]) / 2),
             int((fin_pts[1][1] + fin_pts[0][1]) / 2)),
            fin_pts[2],
        ])

        # TAIL FIN (back)
        tail_base_x = cx - int(cos_a * body_len // 2)
        tail_base_y = cy - int(sin_a * body_len // 2)
        # Two tail flukes
        for fluke_sign in (-1, 1):
            fluke_tip_x = tail_base_x + int(perp_x * body_w * fluke_sign)
            fluke_tip_y = tail_base_y + int(perp_y * body_w * fluke_sign)
            fluke_pts = [
                tail_base_x, tail_base_y,
            ]
            _NS_morvath._poly(surface, _NS_morvath.PALETTE["water_darkest"], [
                (tail_base_x + int(cos_a * 2), tail_base_y + int(sin_a * 2)),
                (fluke_tip_x, fluke_tip_y),
                (tail_base_x, tail_base_y),
            ])
            _NS_morvath._poly(surface, _NS_morvath.PALETTE["water_dark"], [
                (tail_base_x + int(cos_a * 1), tail_base_y + int(sin_a * 1)),
                (int(fluke_tip_x * 0.7 + tail_base_x * 0.3),
                 int(fluke_tip_y * 0.7 + tail_base_y * 0.3)),
                (tail_base_x, tail_base_y),
            ])

        # EYE (small dark spot near head)
        eye_x = head_x - int(cos_a * 4) + int(perp_x * body_w * 0.4)
        eye_y = head_y - int(sin_a * 4) + int(perp_y * body_w * 0.4)
        pygame.draw.rect(surface, _NS_morvath.PALETTE["shadow_deep"],
                         (eye_x, eye_y, 2, 2))
        pygame.draw.rect(surface, _NS_morvath.PALETTE["eye_light"],
                         (eye_x, eye_y, 1, 1))

        # TEETH (row of white spikes at mouth)
        mouth_x = head_x - int(cos_a * 2)
        mouth_y = head_y - int(sin_a * 2)
        for tooth_i in range(3):
            toff = (tooth_i - 1) * 2
            tx = mouth_x + int(perp_x * toff)
            ty = mouth_y + int(perp_y * toff)
            pygame.draw.rect(surface, _NS_morvath.PALETTE["tooth_light"],
                             (tx, ty, 1, 2))
            pygame.draw.rect(surface, _NS_morvath.PALETTE["tooth_mid"],
                             (tx, ty + 1, 1, 1))

    # ============================================================
    # SKILL W — WATER PRISON (dome around target)
    # ============================================================
    def _draw_water_prison_ground(surface, boss, x, y, timer, phase):
        """Water pool base under target."""
        tx, ty = _NS_morvath._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(30 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_morvath.PALETTE["water_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_morvath.PALETTE["water_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))

    def _draw_water_prison_fg(surface, boss, x, y, timer, phase):
        """Sphere/dome of water around target."""
        tx, ty = _NS_morvath._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Sphere radius
        breath = math.sin(phase * 2) * 2
        r = 22 + int(breath)

        # Draw sphere with alpha
        sphere = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        center = (r + 10, r + 10)

        # Layered sphere
        for i in range(r, 0, -2):
            alpha = _NS_morvath._alpha(60 + (r - i) * 4)
            _NS_morvath._aacircle(sphere,
                                  (*_NS_morvath.PALETTE["water_dark"], alpha),
                                  center, i)
        # Bright inner core (target visible through it)
        _NS_morvath._aacircle(sphere,
                              (*_NS_morvath.PALETTE["water_mid"], 100),
                              center, r - 5)

        # Outer ring (bright)
        _NS_morvath._aacircle(sphere, _NS_morvath.PALETTE["water_light"],
                              center, r, 2)
        _NS_morvath._aacircle(sphere, _NS_morvath.PALETTE["water_foam"],
                              center, r, 1)

        # Rotating highlights (water swirling)
        for i in range(12):
            angle = phase * 2 + i * math.pi / 6
            sx = center[0] + int(math.cos(angle) * (r - 3))
            sy = center[1] + int(math.sin(angle) * (r - 3))
            pygame.draw.rect(sphere, _NS_morvath.PALETTE["water_shine"],
                             (sx, sy, 2, 2))
            pygame.draw.rect(sphere, _NS_morvath.PALETTE["water_foam"],
                             (sx, sy, 1, 1))

        # Bright vertical streams (water flowing down)
        for stream_i in range(4):
            stream_angle = stream_i * math.pi / 2 + phase * 0.3
            sx = center[0] + int(math.cos(stream_angle) * r)
            for drop_i in range(3):
                drop_t = (phase + drop_i * 0.3) % 1.0
                dy = center[1] - r + int(drop_t * r * 2)
                dx = sx
                alpha = _NS_morvath._alpha(200 * (1 - drop_t))
                pygame.draw.rect(sphere,
                                 (*_NS_morvath.PALETTE["water_foam"], alpha),
                                 (dx, dy, 1, 2))

        surface.blit(sphere, (tx - r - 10, ty - r - 10))

        # Small ripples at base
        for i in range(3):
            rip_r = int(20 + i * 8 + math.sin(phase * 2) * 3)
            alpha = _NS_morvath._alpha(150 - i * 50)
            _NS_morvath._aacircle(surface,
                                  (*_NS_morvath.PALETTE["water_light"], alpha),
                                  (tx, ty + r - 2), rip_r, 1)

        # Boss hand pointing at prison (energy line)
        facing = boss.direction
        start_x = x + facing * 20
        start_y = y - 4
        alpha = _NS_morvath._alpha(180)
        pygame.draw.line(surface, (*_NS_morvath.PALETTE["water_light"], alpha),
                         (start_x, start_y), (tx - r, ty), 2)

    # ============================================================
    # SKILL E — SHARK BULLETS (multiple small sharks)
    # ============================================================
    def _draw_shark_bullets_fx(surface, boss, x, y, timer, phase):
        """Multiple small water sharks piercing forward."""
        facing = boss.direction
        duration = 55
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_morvath._target_position(boss, x, y)

        start_x = x + facing * 18
        start_y = y - 4

        # 5 mini sharks with slight spread and timing
        num_sharks = 5
        for shark_i in range(num_sharks):
            offset_y = (shark_i - 2) * 10
            delay = shark_i * 0.08
            t = max(0.0, min(1.0, (progress - delay) / max(0.05, 1.0 - delay)))
            if t <= 0:
                continue

            end_x = tx
            end_y = ty + offset_y

            bx = int(start_x + (end_x - start_x) * t)
            by = int(start_y + (end_y - start_y) * t)
            angle = math.atan2(end_y - start_y, end_x - start_x)

            # Trail
            for i in range(6):
                trail_t = max(0.0, t - i * 0.06)
                px = int(start_x + (end_x - start_x) * trail_t)
                py = int(start_y + (end_y - start_y) * trail_t)
                alpha = _NS_morvath._alpha(200 - i * 30)
                size = max(1, 4 - i)
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["water_dark"], alpha),
                                      (px, py), size)
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["water_mid"], alpha),
                                      (px, py), max(1, size - 1))

            # Small shark (smaller size)
            _NS_morvath._draw_water_shark(surface, bx, by, angle, facing,
                                           size_mult=0.7)

            # Impact
            if t > 0.9:
                st = (t - 0.9) / 0.1
                r = int(6 + st * 12)
                alpha = _NS_morvath._alpha(230 * (1 - st))
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["water_mid"], alpha),
                                      (end_x, end_y), r, 2)
                for i in range(6):
                    a = i * math.pi / 3
                    ex = end_x + int(math.cos(a) * r)
                    ey = end_y + int(math.sin(a) * r)
                    pygame.draw.rect(surface,
                                     (*_NS_morvath.PALETTE["water_foam"], alpha),
                                     (ex, ey, 2, 2))

    # ============================================================
    # SKILL R — GREAT SHARK SUMMONING
    # ============================================================
    def _draw_great_shark_ground(surface, boss, x, y, timer, phase):
        """Massive water pool erupting."""
        tx, ty = _NS_morvath._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(65 * min(1.0, progress * 2.5))

        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_morvath.PALETTE["water_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_morvath.PALETTE["water_dark"], 200),
                                (tx - r + 5, ty - r // 3 + 3,
                                 r * 2 - 10, r * 2 // 3 - 6))
            pygame.draw.ellipse(surface, (*_NS_morvath.PALETTE["water_mid"], 180),
                                (tx - r + 12, ty - r // 3 + 6,
                                 r * 2 - 24, r * 2 // 3 - 12))

    def _draw_great_shark_fg(surface, boss, x, y, timer, phase):
        """Massive shark rising from water pool + chomp animation."""
        tx, ty = _NS_morvath._target_position(boss, x, y)
        duration = 120
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.25:
            # Wind-up: water gathering
            t = progress / 0.25
            for i in range(15):
                p_angle = i * math.pi * 2 / 15
                p_r = int(60 * (1 - t))
                px = tx + int(math.cos(p_angle) * p_r)
                py = ty + int(math.sin(p_angle) * p_r * 0.4)
                alpha = _NS_morvath._alpha(200 * t)
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["water_mid"], alpha),
                                      (px, py), 3)
                pygame.draw.rect(surface,
                                 (*_NS_morvath.PALETTE["water_light"], alpha),
                                 (px, py, 1, 1))
        else:
            # Massive shark rises
            t = (progress - 0.25) / 0.75
            rise = math.sin(min(1.0, t * 1.5) * math.pi * 0.5)

            # Shark head position (rising from below)
            shark_cx = tx
            shark_cy = ty - int(50 * rise)

            # HUGE shark head
            head_w = 60
            head_h = 55

            # Head outline
            head_pts = [
                (shark_cx - head_w // 2, shark_cy),
                (shark_cx - head_w // 2 + 5, shark_cy - head_h // 2),
                (shark_cx - 5, shark_cy - head_h // 2 - 5),
                (shark_cx + 5, shark_cy - head_h // 2 - 5),
                (shark_cx + head_w // 2 - 5, shark_cy - head_h // 2),
                (shark_cx + head_w // 2, shark_cy),
                (shark_cx + head_w // 2 - 3, shark_cy + head_h // 4),
                (shark_cx + head_w // 4, shark_cy + head_h // 2),
                (shark_cx - head_w // 4, shark_cy + head_h // 2),
                (shark_cx - head_w // 2 + 3, shark_cy + head_h // 4),
            ]
            _NS_morvath._poly(surface, _NS_morvath.PALETTE["shadow_deep"],
                              [(px + 3, py + 3) for px, py in head_pts])
            _NS_morvath._poly(surface, _NS_morvath.PALETTE["water_darkest"], head_pts)
            # Highlight upper
            _NS_morvath._poly(surface, _NS_morvath.PALETTE["water_dark"], [
                (shark_cx - head_w // 2 + 2, shark_cy - 2),
                (shark_cx - head_w // 2 + 6, shark_cy - head_h // 2 + 2),
                (shark_cx - 4, shark_cy - head_h // 2 - 3),
                (shark_cx + 4, shark_cy - head_h // 2 - 3),
                (shark_cx + head_w // 2 - 6, shark_cy - head_h // 2 + 2),
                (shark_cx + head_w // 2 - 2, shark_cy - 2),
                (shark_cx, shark_cy),
            ])
            _NS_morvath._poly(surface, _NS_morvath.PALETTE["water_mid"], [
                (shark_cx - head_w // 2 + 8, shark_cy - head_h // 3),
                (shark_cx, shark_cy - head_h // 2),
                (shark_cx + head_w // 2 - 8, shark_cy - head_h // 3),
                (shark_cx, shark_cy - head_h // 6),
            ])
            # Bright top
            _NS_morvath._poly(surface, _NS_morvath.PALETTE["water_light"], [
                (shark_cx - 10, shark_cy - head_h // 2),
                (shark_cx, shark_cy - head_h // 2 - 2),
                (shark_cx + 10, shark_cy - head_h // 2),
                (shark_cx, shark_cy - head_h // 3),
            ])

            # GILL MARKS
            for gill_side in (-1, 1):
                for gill_i in range(3):
                    gill_x = shark_cx + gill_side * (head_w // 2 - 8)
                    gill_y = shark_cy - 8 + gill_i * 4
                    pygame.draw.line(surface, _NS_morvath.PALETTE["water_darkest"],
                                     (gill_x, gill_y),
                                     (gill_x + gill_side * 4, gill_y), 1)

            # EYES (angry red glowing)
            for eye_x_side in (-1, 1):
                ex = shark_cx + eye_x_side * 12
                ey = shark_cy - 15
                pygame.draw.rect(surface, _NS_morvath.PALETTE["shadow_deep"],
                                 (ex - 2, ey - 1, 4, 3))
                # Angry red glow
                for r in range(4, 0, -1):
                    alpha = _NS_morvath._alpha(120 * (4 - r) / 4)
                    _NS_morvath._aacircle(surface, (200, 50, 50, alpha), (ex, ey), r)
                pygame.draw.rect(surface, (255, 150, 100), (ex, ey, 1, 1))
                pygame.draw.rect(surface, _NS_morvath.PALETTE["white"], (ex, ey, 1, 1))

            # MOUTH (huge open jaw with teeth)
            # Mouth opens/closes with chomp animation
            chomp = abs(math.sin(phase * 4)) * 8 + 4  # 4-12 mouth height
            mouth_top_y = shark_cy - 4
            mouth_bot_y = shark_cy + int(chomp)

            # Dark mouth cavity
            _NS_morvath._poly(surface, _NS_morvath.PALETTE["shadow_deep"], [
                (shark_cx - head_w // 2 + 8, mouth_top_y),
                (shark_cx + head_w // 2 - 8, mouth_top_y),
                (shark_cx + head_w // 3, mouth_bot_y),
                (shark_cx - head_w // 3, mouth_bot_y),
            ])
            _NS_morvath._poly(surface, _NS_morvath.PALETTE["water_darkest"], [
                (shark_cx - head_w // 2 + 10, mouth_top_y + 1),
                (shark_cx + head_w // 2 - 10, mouth_top_y + 1),
                (shark_cx + head_w // 3 - 2, mouth_bot_y - 1),
                (shark_cx - head_w // 3 + 2, mouth_bot_y - 1),
            ])

            # TEETH (upper row)
            num_teeth = 8
            for tooth_i in range(num_teeth):
                tooth_t = tooth_i / (num_teeth - 1)
                tx_pos = int(shark_cx - head_w // 2 + 10 +
                             tooth_t * (head_w - 20))
                tooth_h = int(4 + math.sin(tooth_t * math.pi) * 3)
                _NS_morvath._poly(surface, _NS_morvath.PALETTE["tooth_dark"], [
                    (tx_pos - 1, mouth_top_y),
                    (tx_pos, mouth_top_y + tooth_h),
                    (tx_pos + 1, mouth_top_y),
                ])
                _NS_morvath._poly(surface, _NS_morvath.PALETTE["tooth_mid"], [
                    (tx_pos - 1, mouth_top_y),
                    (tx_pos, mouth_top_y + tooth_h - 1),
                    (tx_pos + 1, mouth_top_y),
                ])
                pygame.draw.rect(surface, _NS_morvath.PALETTE["tooth_light"],
                                 (tx_pos, mouth_top_y + 1, 1, 1))

            # TEETH (lower row)
            for tooth_i in range(num_teeth):
                tooth_t = tooth_i / (num_teeth - 1)
                tx_pos = int(shark_cx - head_w // 3 + tooth_t *
                             (head_w * 2 // 3))
                tooth_h = int(3 + math.sin(tooth_t * math.pi) * 2)
                _NS_morvath._poly(surface, _NS_morvath.PALETTE["tooth_dark"], [
                    (tx_pos - 1, mouth_bot_y),
                    (tx_pos, mouth_bot_y - tooth_h),
                    (tx_pos + 1, mouth_bot_y),
                ])
                _NS_morvath._poly(surface, _NS_morvath.PALETTE["tooth_mid"], [
                    (tx_pos - 1, mouth_bot_y),
                    (tx_pos, mouth_bot_y - tooth_h + 1),
                    (tx_pos + 1, mouth_bot_y),
                ])

            # Water splashing around shark base
            for i in range(15):
                sp_angle = i * math.pi * 2 / 15 + phase * 0.3
                sp_r = 40 + int(math.sin(phase * 3 + i) * 8)
                sx = tx + int(math.cos(sp_angle) * sp_r)
                sy = ty + int(math.sin(sp_angle) * sp_r * 0.4)
                alpha = _NS_morvath._alpha(230)
                # Water splash droplet
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["water_dark"], alpha),
                                      (sx, sy), 3)
                _NS_morvath._aacircle(surface,
                                      (*_NS_morvath.PALETTE["water_mid"], alpha),
                                      (sx, sy), 2)
                pygame.draw.rect(surface, _NS_morvath.PALETTE["water_foam"],
                                 (sx, sy, 1, 1))

            # Vertical water spray behind shark
            for i in range(10):
                sp_t = (phase * 0.8 + i * 0.1) % 1.0
                sx_off = int(math.sin(phase + i) * 30)
                sy_off = -int(sp_t * 40)
                pygame.draw.rect(surface, _NS_morvath.PALETTE["water_light"],
                                 (tx + sx_off, ty - 30 + sy_off, 2, 2))
                pygame.draw.rect(surface, _NS_morvath.PALETTE["water_foam"],
                                 (tx + sx_off, ty - 30 + sy_off, 1, 1))


# ====================================================================
# ALIAS
# ====================================================================
draw_morvath = _NS_morvath.draw_morvath


# ====================================================================================================
# PYRHAAN - MINI BOSS
# ====================================================================================================

class _NS_pyrhaan:
    """Namespace pyrhaan - HD rendering untuk mini boss Pyrhaan."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Fire (main - orange/red/yellow)
        "fire_darkest": (30, 5, 0),
        "fire_dark": (90, 20, 5),
        "fire_deep": (150, 40, 10),
        "fire_mid": (220, 90, 20),
        "fire_bright": (255, 150, 40),
        "fire_light": (255, 200, 80),
        "fire_hot": (255, 230, 130),
        "fire_shine": (255, 250, 200),
        "fire_white": (255, 255, 240),

        # Ember (dark red-brown armor)
        "armor_darkest": (25, 10, 8),
        "armor_dark": (60, 25, 18),
        "armor_mid": (110, 45, 30),
        "armor_light": (170, 75, 45),
        "armor_edge": (220, 130, 80),

        # Gold trim on armor
        "gold_dark": (85, 55, 15),
        "gold_mid": (170, 130, 40),
        "gold_light": (240, 200, 90),
        "gold_shine": (255, 240, 170),

        # Skin (dark bronze - burnt)
        "skin_dark": (70, 35, 25),
        "skin_mid": (135, 75, 50),
        "skin_light": (200, 130, 90),
        "skin_shine": (240, 180, 130),

        # Blade (glowing molten)
        "blade_dark": (60, 20, 5),
        "blade_mid": (200, 80, 20),
        "blade_light": (255, 170, 60),
        "blade_hot": (255, 230, 140),
        "blade_core": (255, 255, 220),

        # Chain (dark iron with fire)
        "chain_dark": (30, 20, 15),
        "chain_mid": (80, 55, 35),
        "chain_light": (140, 100, 60),

        # Cape (dark red)
        "cape_darkest": (25, 5, 8),
        "cape_dark": (75, 20, 20),
        "cape_mid": (140, 40, 35),
        "cape_light": (200, 75, 60),

        # Belt/sash
        "belt_dark": (55, 30, 15),
        "belt_mid": (110, 65, 30),
        "belt_light": (180, 130, 70),

        # Eyes (glowing yellow-white)
        "eye_dark": (80, 40, 5),
        "eye_mid": (220, 150, 30),
        "eye_light": (255, 220, 130),

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
        color = _NS_pyrhaan._clamp(color)
        if _NS_pyrhaan.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_pyrhaan._clamp(color)
        if _NS_pyrhaan.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_pyrhaan._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 120 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_pyrhaan(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_pyrhaan._detect_moving(boss)
        _NS_pyrhaan._update_attack_anim(boss)
        attacking = getattr(boss, "_py_attack_active", False)

        # Draw remnant (behind actual boss) if R skill active
        if active_skill == "r":
            _NS_pyrhaan._draw_remnant(surface, boss, x, y, skill_timer, pulse)

        # Ambient
        _NS_pyrhaan._draw_shadow(surface, x, y + 52)
        _NS_pyrhaan._draw_fire_aura(surface, x, y, pulse)
        _NS_pyrhaan._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX (behind body)
        if active_skill == "e":
            _NS_pyrhaan._draw_phoenix_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_pyrhaan._draw_body_attack(surface, boss, x, y)
        elif moving:
            _NS_pyrhaan._draw_body_walk(surface, boss, x, y)
        else:
            _NS_pyrhaan._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX
        if active_skill == "q":
            _NS_pyrhaan._draw_chains_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_pyrhaan._draw_flame_fist_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_pyrhaan._draw_phoenix_fg(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 35)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_py_attack_active", False))

        if not active:
            if timer >= cooldown - 20:
                boss._py_attack_active = True
                boss._py_attack_frame = 0
                active = True

        if active:
            boss._py_attack_frame = int(getattr(boss, "_py_attack_frame", 0)) + 1
            attack_duration = 22
            if boss._py_attack_frame >= attack_duration:
                boss._py_attack_active = False
                boss._py_attack_frame = 0
                active = False

        attack_duration = 22
        boss._py_attack_progress = (
            min(1.0, getattr(boss, "_py_attack_frame", 0) / attack_duration)
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_py_last_x"):
            boss._py_last_x = boss.x
            boss._py_last_y = boss.y
            return False
        dx = abs(boss.x - boss._py_last_x)
        dy = abs(boss.y - boss._py_last_y)
        boss._py_last_x = boss.x
        boss._py_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.7) * 3)
        _NS_pyrhaan._draw_full_body(surface, x, y + bob,
                                    boss.direction, boss.pulse, "idle", 0)

    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.2
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_pyrhaan._draw_full_body(surface, x + sway, y + bob,
                                    boss.direction, phase, "walk", 0)

    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_py_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        # Dual-blade fast attack
        if progress < 0.3:
            t = progress / 0.3
            lunge = -int(t * 3) * boss.direction
            lift = int(t * 3)
        elif progress < 0.55:
            t = (progress - 0.3) / 0.25
            ease = 1 - (1 - t) ** 3
            lunge = int((-3 + ease * 16)) * boss.direction
            lift = int(3 - ease * 5)
        else:
            t = (progress - 0.55) / 0.45
            lunge = int(13 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)

        _NS_pyrhaan._draw_full_body(surface, x + lunge, y - lift,
                                    boss.direction, boss.pulse, "attack", progress)
        # Dual flame slash arc
        _NS_pyrhaan._draw_dual_flame_slash(surface, boss, x + lunge,
                                            y - lift, progress)

    # ============================================================
    # FULL BODY (fire warrior with 2 blades)
    # ============================================================
    def _draw_full_body(surface, cx, cy, facing, phase, action, atk_prog):
        # 1. Cape (behind)
        _NS_pyrhaan._draw_cape(surface, cx, cy, facing, phase)
        # 2. Legs
        _NS_pyrhaan._draw_legs(surface, cx, cy, facing, phase, action)
        # 3. BACK arm + BACK BLADE
        _NS_pyrhaan._draw_back_arm_with_blade(surface, cx, cy, facing,
                                                phase, action, atk_prog)
        # 4. Torso armor
        _NS_pyrhaan._draw_torso(surface, cx, cy, facing, phase)
        # 5. Head + flame hair
        _NS_pyrhaan._draw_head(surface, cx, cy - 24, facing, phase)
        # 6. FRONT arm + FRONT BLADE
        _NS_pyrhaan._draw_front_arm_with_blade(surface, cx, cy, facing,
                                                phase, action, atk_prog)

    def _draw_cape(surface, cx, cy, facing, phase):
        """Dark red cape."""
        sway = math.sin(phase * 0.5) * 3
        back_dir = -facing

        cape_pts = [
            (cx + back_dir * 3, cy - 8),
            (cx + back_dir * 8, cy - 5),
            (cx + back_dir * 12, cy + 2),
            (cx + back_dir * 15 + int(sway * back_dir), cy + 12),
            (cx + back_dir * 17 + int(sway * back_dir * 1.5), cy + 24),
            (cx + back_dir * 15 + int(sway * back_dir * 2), cy + 36),
            (cx + back_dir * 10 + int(sway * back_dir), cy + 42),
            (cx + back_dir * 3, cy + 40),
            (cx, cy + 25),
            (cx + back_dir * 2, cy + 8),
        ]
        _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                          [(px + 2, py + 3) for px, py in cape_pts])
        _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["cape_darkest"], cape_pts)
        _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["cape_dark"], [
            (cx + back_dir * 2, cy - 7),
            (cx + back_dir * 7, cy - 4),
            (cx + back_dir * 11, cy + 3),
            (cx + back_dir * 13 + int(sway * back_dir), cy + 12),
            (cx + back_dir * 15 + int(sway * back_dir * 1.5), cy + 24),
            (cx + back_dir * 12, cy + 36),
            (cx + back_dir * 7, cy + 40),
            (cx + back_dir * 2, cy + 38),
        ])
        _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["cape_mid"], [
            (cx + back_dir * 4, cy - 2),
            (cx + back_dir * 8, cy + 6),
            (cx + back_dir * 10 + int(sway * back_dir), cy + 18),
            (cx + back_dir * 8, cy + 28),
            (cx + back_dir * 3, cy + 30),
            (cx + back_dir * 2, cy + 8),
        ])
        # Cape highlights
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["cape_light"],
                            (cx + back_dir * 4, cy),
                            (cx + back_dir * 6, cy + 15), 1)

        # Fire embers rising along cape
        for i in range(4):
            e_t = (phase * 0.6 + i * 0.25) % 1.0
            ex = cx + back_dir * (8 + int(math.sin(phase + i) * 4))
            ey = cy + 10 - int(e_t * 30)
            alpha = _NS_pyrhaan._alpha(200 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface, (*_NS_pyrhaan.PALETTE["fire_light"], alpha),
                             (ex, ey, 1, 1))

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Armored legs."""
        leg_sway = 0
        if action == "walk":
            leg_sway = math.sin(phase) * 3

        # Back leg
        back_x = cx - 4
        back_y_top = cy + 8
        back_y_knee = cy + 24
        back_y_bot = cy + 42 + int(-leg_sway)

        # Thigh
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                            (back_x + 1, back_y_top + 1),
                            (back_x + 1, back_y_knee + 1), 8)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                            (back_x, back_y_top), (back_x, back_y_knee), 7)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                            (back_x, back_y_top), (back_x, back_y_knee), 5)
        # Greave
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                            (back_x + 1, back_y_knee + 1),
                            (back_x + 1, back_y_bot + 1), 8)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                            (back_x, back_y_knee), (back_x, back_y_bot), 7)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                            (back_x, back_y_knee), (back_x, back_y_bot), 5)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_mid"],
                            (back_x - 1, back_y_knee), (back_x - 1, back_y_bot), 2)
        # Knee gold trim
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["gold_dark"],
                         (back_x - 3, back_y_knee - 1, 6, 2))
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["gold_mid"],
                         (back_x - 3, back_y_knee, 6, 1))

        # Front leg
        front_x = cx + 4
        front_y_top = cy + 8
        front_y_knee = cy + 24
        front_y_bot = cy + 42 + int(leg_sway)

        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                            (front_x + 1, front_y_top + 1),
                            (front_x + 1, front_y_knee + 1), 8)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                            (front_x, front_y_top), (front_x, front_y_knee), 7)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                            (front_x, front_y_top), (front_x, front_y_knee), 5)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_mid"],
                            (front_x - 1, front_y_top), (front_x - 1, front_y_knee), 2)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                            (front_x + 1, front_y_knee + 1),
                            (front_x + 1, front_y_bot + 1), 8)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                            (front_x, front_y_knee), (front_x, front_y_bot), 7)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                            (front_x, front_y_knee), (front_x, front_y_bot), 5)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_mid"],
                            (front_x - 1, front_y_knee), (front_x - 1, front_y_bot), 2)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_edge"],
                            (front_x - 2, front_y_knee + 2),
                            (front_x - 2, front_y_bot - 2), 1)
        # Front knee gold trim
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["gold_dark"],
                         (front_x - 3, front_y_knee - 1, 6, 2))
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["gold_mid"],
                         (front_x - 3, front_y_knee, 6, 1))
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["gold_shine"],
                         (front_x, front_y_knee, 1, 1))

        # Boots with fire trim
        for foot_x, foot_y in ((back_x, back_y_bot), (front_x, front_y_bot)):
            pygame.draw.ellipse(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                                (foot_x - 5, foot_y - 1, 12, 6))
            pygame.draw.ellipse(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                                (foot_x - 4, foot_y, 10, 4))
            pygame.draw.ellipse(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                                (foot_x - 4, foot_y, 10, 3))
            # Small fire embers under feet
            for i in range(2):
                pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["fire_bright"],
                                 (foot_x - 2 + i * 3, foot_y + 3, 1, 1))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Red/gold chestplate."""
        breath = math.sin(phase * 0.7) * 1

        torso_pts = [
            (cx - 13, cy - 8),
            (cx - 15, cy - 2),
            (cx - 14, cy + 6),
            (cx - 9, cy + 10),
            (cx + 9, cy + 10),
            (cx + 14, cy + 6),
            (cx + 15, cy - 2),
            (cx + 13, cy - 8),
            (cx + 6, cy - 13),
            (cx - 6, cy - 13),
        ]
        _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in torso_pts])
        _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["armor_darkest"], torso_pts)
        _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["armor_dark"], [
            (cx - 12, cy - 6),
            (cx - 14, cy - 1),
            (cx - 13, cy + 5),
            (cx - 8, cy + 9),
            (cx + 8, cy + 9),
            (cx + 13, cy + 5),
            (cx + 14, cy - 1),
            (cx + 12, cy - 6),
            (cx + 5, cy - 11),
            (cx - 5, cy - 11),
        ])
        _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["armor_mid"], [
            (cx - 10, cy - 4),
            (cx - 11, cy + 2),
            (cx - 7, cy + 7),
            (cx + 7, cy + 7),
            (cx + 11, cy + 2),
            (cx + 10, cy - 4),
            (cx + 4, cy - 9),
            (cx - 4, cy - 9),
        ])
        # Highlight
        _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["armor_light"], [
            (cx - 4, cy - 6),
            (cx + 4, cy - 6),
            (cx + 5, cy),
            (cx - 5, cy),
        ])

        # CENTER GEM (fire orb on chest)
        gem_pulse = math.sin(phase * 2) * 0.3 + 0.7
        for r in range(5, 0, -1):
            alpha = _NS_pyrhaan._alpha(150 * (5 - r) / 5 * gem_pulse)
            _NS_pyrhaan._aacircle(surface,
                                  (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                  (cx, cy - 2), r)
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_dark"], (cx, cy - 2), 3)
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_mid"], (cx, cy - 2), 2)
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_hot"], (cx, cy - 2), 1)
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["fire_shine"], (cx, cy - 2, 1, 1))

        # Gold trim around chest emblem
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["gold_dark"],
                              (cx, cy - 2), 4, 1)
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["gold_mid"],
                              (cx, cy - 2), 3, 1)

        # SHOULDER PAULDRONS (with fire glow)
        for shoulder_x_off, shoulder_side in [(-13, -1), (13, 1)]:
            sx = cx + shoulder_x_off
            sy = cy - 8
            pygame.draw.ellipse(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                                (sx - 5, sy - 4, 12, 10))
            pygame.draw.ellipse(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                                (sx - 5, sy - 4, 11, 10))
            pygame.draw.ellipse(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                                (sx - 4, sy - 3, 9, 8))
            pygame.draw.ellipse(surface, _NS_pyrhaan.PALETTE["armor_mid"],
                                (sx - 3, sy - 2, 7, 6))
            # Gold spike on top
            _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["gold_dark"], [
                (sx + shoulder_side * 3, sy - 4),
                (sx + shoulder_side * 4, sy - 9),
                (sx + shoulder_side * 5, sy - 4),
            ])
            _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["gold_mid"], [
                (sx + shoulder_side * 3, sy - 4),
                (sx + shoulder_side * 4, sy - 8),
                (sx + shoulder_side * 4, sy - 4),
            ])
            pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["gold_shine"],
                             (sx + shoulder_side * 4, sy - 8, 1, 1))
            # Pauldron highlight
            pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["armor_edge"],
                             (sx - 1, sy - 2, 2, 1))

        # BELT/SASH
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                         (cx - 13, cy + 7, 27, 5))
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["belt_dark"],
                         (cx - 12, cy + 8, 25, 4))
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["belt_mid"],
                         (cx - 12, cy + 8, 25, 2))
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["belt_light"],
                         (cx - 10, cy + 8, 20, 1))
        # Center gold buckle
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["gold_dark"],
                         (cx - 3, cy + 7, 6, 6))
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["gold_mid"],
                         (cx - 2, cy + 8, 4, 4))
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["gold_shine"],
                         (cx - 1, cy + 9, 1, 1))

    def _draw_head(surface, cx, cy, facing, phase):
        """Head with FLAME HAIR (dynamic)."""
        # Face
        face_pts = [
            (cx - 6, cy + 5),
            (cx - 7, cy - 2),
            (cx - 5, cy - 7),
            (cx + 5, cy - 7),
            (cx + 7, cy - 2),
            (cx + 6, cy + 5),
        ]
        _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                          [(px + 2, py + 2) for px, py in face_pts])
        _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["skin_dark"], face_pts)
        _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["skin_mid"], [
            (cx - 5, cy + 4),
            (cx - 6, cy - 2),
            (cx - 4, cy - 6),
            (cx + 4, cy - 6),
            (cx + 6, cy - 2),
            (cx + 5, cy + 4),
        ])
        # Skin highlights
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["skin_light"],
                         (cx - 2, cy - 3, 4, 1))
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["skin_shine"],
                         (cx - 1, cy - 3, 2, 1))

        # FLAME HAIR (dynamic, always animated)
        # Multiple flame tongues rising from head
        flame_tongues = [
            (-4, -6, 4, 0),    # left small
            (-3, -8, 6, 0.3),  # left mid
            (-1, -9, 8, 0.6),  # center-left tall
            (2, -9, 8, 0.4),   # center-right tall
            (4, -8, 6, 0.7),   # right mid
            (5, -6, 4, 0.2),   # right small
            (0, -10, 10, 0.5), # tallest center
        ]

        for base_off_x, base_off_y, flame_h, offset in flame_tongues:
            fx = cx + base_off_x
            fy = cy + base_off_y
            # Animate the flame tip
            wobble_x = int(math.sin(phase * 3 + offset * 5) * 2)
            wobble_h = int(math.sin(phase * 2 + offset * 3) * 2)
            tip_x = fx + wobble_x
            tip_y = fy - flame_h - wobble_h
            # Flame width
            w = max(2, flame_h // 3)

            # Flame shape
            _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["fire_darkest"], [
                (tip_x, tip_y),
                (fx - w, fy),
                (fx + w, fy),
            ])
            _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["fire_dark"], [
                (tip_x, tip_y),
                (fx - w + 1, fy),
                (fx + w - 1, fy),
            ])
            _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["fire_deep"], [
                (tip_x, tip_y + 1),
                (fx - w + 1, fy - 1),
                (fx + w - 1, fy - 1),
            ])
            _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["fire_mid"], [
                (tip_x, tip_y + 2),
                (fx - 1, fy - 1),
                (fx + 1, fy - 1),
            ])
            _NS_pyrhaan._poly(surface, _NS_pyrhaan.PALETTE["fire_bright"], [
                (tip_x, tip_y + 3),
                (fx, fy - 1),
                (fx + 1, fy - 1),
            ])
            # Bright core near tip
            pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["fire_light"],
                             (tip_x, tip_y + 1, 1, 2))
            pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["fire_hot"],
                             (tip_x, tip_y + 2, 1, 1))

        # Small ember sparks around head
        for i in range(5):
            e_t = (phase * 1.2 + i * 0.2) % 1.0
            e_angle = i * math.pi / 2.5 + phase * 0.5
            ex = cx + int(math.cos(e_angle) * (8 + e_t * 5))
            ey = cy - 5 - int(e_t * 12)
            alpha = _NS_pyrhaan._alpha(230 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_pyrhaan.PALETTE["fire_hot"], alpha),
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, (*_NS_pyrhaan.PALETTE["fire_shine"], alpha),
                             (ex, ey, 1, 1))

        # EYES (yellow glowing)
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        for eye_x_off in (-2, 2):
            ex = cx + eye_x_off * facing
            ey = cy - 3
            pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))
            # Glow
            for r in range(4, 0, -1):
                alpha = _NS_pyrhaan._alpha(90 * (4 - r) / 4 * eye_pulse)
                _NS_pyrhaan._aacircle(surface,
                                      (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                      (ex, ey), r)
            pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["white"],
                             (ex, ey, 1, 1))

        # Mouth (fierce)
        pygame.draw.line(surface, _NS_pyrhaan.PALETTE["skin_dark"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["fire_deep"],
                         (cx, cy + 2, 1, 1))

    def _draw_back_arm_with_blade(surface, cx, cy, facing, phase, action, atk_prog):
        """Back arm holding second blade."""
        sway = math.sin(phase * 0.9) * 1
        back_shoulder_x = cx - facing * 12
        back_shoulder_y = cy - 6

        # Back arm blade angle
        if action == "attack":
            # Back blade swings OPPOSITE direction (crossing slash)
            if atk_prog < 0.3:
                t = atk_prog / 0.3
                back_angle = math.pi * 0.3 + t * math.pi * 0.4
                hand_off_x = -facing * int(4 + t * 2)
                hand_off_y = int(2 - t * 6)
            elif atk_prog < 0.55:
                t = (atk_prog - 0.3) / 0.25
                ease = 1 - (1 - t) ** 3
                back_angle = math.pi * 0.7 - ease * math.pi * 0.7
                hand_off_x = -facing * int(6 - ease * 12)
                hand_off_y = int(-4 + ease * 12)
            else:
                t = (atk_prog - 0.55) / 0.45
                back_angle = -t * 0.2
                hand_off_x = -facing * int(-6 + t * 10)
                hand_off_y = int(8 - t * 6)
        else:
            back_angle = math.pi * 0.35 + math.sin(phase * 0.5) * 0.05
            hand_off_x = -facing * 4
            hand_off_y = int(3 + sway)

        back_hand_x = back_shoulder_x + hand_off_x
        back_hand_y = back_shoulder_y + hand_off_y

        # Arm
        elbow_x = int((back_shoulder_x + back_hand_x) / 2) - facing * 2
        elbow_y = int((back_shoulder_y + back_hand_y) / 2) + 1

        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                            (back_shoulder_x + 1, back_shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 6)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                            (back_shoulder_x, back_shoulder_y),
                            (elbow_x, elbow_y), 5)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                            (back_shoulder_x, back_shoulder_y),
                            (elbow_x, elbow_y), 3)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (back_hand_x + 1, back_hand_y + 1), 5)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y),
                            (back_hand_x, back_hand_y), 4)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                            (elbow_x, elbow_y),
                            (back_hand_x, back_hand_y), 2)

        # Gauntlet
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                              (back_hand_x, back_hand_y), 3)
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                              (back_hand_x, back_hand_y), 2)

        # BACK BLADE (curved sabre, flame-shaped)
        _NS_pyrhaan._draw_flame_blade(surface, back_hand_x, back_hand_y,
                                       back_angle, facing, is_back=True)

    def _draw_front_arm_with_blade(surface, cx, cy, facing, phase, action, atk_prog):
        """Front arm holding main blade."""
        sway = math.sin(phase * 0.9) * 2
        front_shoulder_x = cx + facing * 12
        front_shoulder_y = cy - 6

        # Front blade angle
        if action == "attack":
            if atk_prog < 0.3:
                t = atk_prog / 0.3
                blade_angle = -math.pi * 0.7 - t * math.pi * 0.3
                hand_off_x = facing * int(-6 - t * 2)
                hand_off_y = int(-4 - t * 6)
            elif atk_prog < 0.55:
                t = (atk_prog - 0.3) / 0.25
                ease = 1 - (1 - t) ** 3
                blade_angle = -math.pi * 1.0 + ease * math.pi * 1.1
                hand_off_x = facing * int(-8 + ease * 22)
                hand_off_y = int(-10 + ease * 14)
            else:
                t = (atk_prog - 0.55) / 0.45
                blade_angle = math.pi * 0.1 - t * math.pi * 0.3
                hand_off_x = facing * int(14 - t * 10)
                hand_off_y = int(4 - t * 6)
        elif action == "walk":
            blade_angle = -math.pi * 0.15 + math.sin(phase) * 0.05
            hand_off_x = facing * 8
            hand_off_y = int(4 + sway)
        else:
            # IDLE: blade held down and to the side
            blade_angle = -math.pi * 0.25 + math.sin(phase * 0.5) * 0.03
            hand_off_x = facing * 8
            hand_off_y = int(4 - sway)

        front_hand_x = front_shoulder_x + hand_off_x
        front_hand_y = front_shoulder_y + hand_off_y

        elbow_x = int((front_shoulder_x + front_hand_x) / 2) + facing * 3
        elbow_y = int((front_shoulder_y + front_hand_y) / 2) + 1

        # Arm
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                            (front_shoulder_x + 1, front_shoulder_y + 1),
                            (elbow_x + 1, elbow_y + 1), 6)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                            (front_shoulder_x, front_shoulder_y),
                            (elbow_x, elbow_y), 5)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                            (front_shoulder_x, front_shoulder_y),
                            (elbow_x, elbow_y), 3)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_mid"],
                            (front_shoulder_x - 1, front_shoulder_y - 1),
                            (elbow_x - 1, elbow_y - 1), 1)

        # Elbow armor
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                              (elbow_x, elbow_y), 3)
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                              (elbow_x, elbow_y), 2)

        # Forearm
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                            (elbow_x + 1, elbow_y + 1),
                            (front_hand_x + 1, front_hand_y + 1), 5)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                            (elbow_x, elbow_y),
                            (front_hand_x, front_hand_y), 4)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                            (elbow_x, elbow_y),
                            (front_hand_x, front_hand_y), 2)

        # Gauntlet
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["armor_darkest"],
                              (front_hand_x, front_hand_y), 4)
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["armor_dark"],
                              (front_hand_x, front_hand_y), 3)
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["armor_mid"],
                              (front_hand_x, front_hand_y), 2)
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["armor_edge"],
                         (front_hand_x - 1, front_hand_y - 1, 1, 1))

        # FRONT BLADE (main flame sabre)
        _NS_pyrhaan._draw_flame_blade(surface, front_hand_x, front_hand_y,
                                       blade_angle, facing, is_back=False)

    def _draw_flame_blade(surface, hand_x, hand_y, angle, facing, is_back=False):
        """Curved flame-shaped blade (sabre/scimitar with fire glow)."""
        actual_angle = angle if facing > 0 else math.pi - angle

        blade_length = 24 if not is_back else 22

        # Curved blade — main line
        # Tip position (slightly curved)
        curve_offset = 0.15  # curvature
        tip_x = hand_x + int(math.cos(actual_angle) * blade_length)
        tip_y = hand_y + int(math.sin(actual_angle) * blade_length)
        # Curve control point
        mid_x = hand_x + int(math.cos(actual_angle) * blade_length * 0.5)
        mid_y = hand_y + int(math.sin(actual_angle) * blade_length * 0.5)
        # Perpendicular for curve
        perp_x = -math.sin(actual_angle) * blade_length * curve_offset
        perp_y = math.cos(actual_angle) * blade_length * curve_offset
        mid_x += int(perp_x)
        mid_y += int(perp_y)

        # Draw blade in segments (Bezier-like)
        segments = 8
        prev_x, prev_y = hand_x, hand_y
        blade_pts = [(hand_x, hand_y)]

        for i in range(1, segments + 1):
            t = i / segments
            # Quadratic bezier
            bx = int((1 - t) ** 2 * hand_x + 2 * (1 - t) * t * mid_x + t ** 2 * tip_x)
            by = int((1 - t) ** 2 * hand_y + 2 * (1 - t) * t * mid_y + t ** 2 * tip_y)
            blade_pts.append((bx, by))
            prev_x, prev_y = bx, by

        # Draw thick blade line (bottom edge)
        for i in range(len(blade_pts) - 1):
            thickness = max(2, 5 - i // 2)
            _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["shadow_deep"],
                                (blade_pts[i][0] + 1, blade_pts[i][1] + 1),
                                (blade_pts[i + 1][0] + 1, blade_pts[i + 1][1] + 1),
                                thickness + 1)
            _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["blade_dark"],
                                blade_pts[i], blade_pts[i + 1], thickness)
            _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["blade_mid"],
                                blade_pts[i], blade_pts[i + 1],
                                max(1, thickness - 1))
            _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["blade_light"],
                                blade_pts[i], blade_pts[i + 1],
                                max(1, thickness - 2))

        # Bright center core (flame)
        for i in range(len(blade_pts) - 1):
            _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["blade_hot"],
                                blade_pts[i], blade_pts[i + 1], 1)

        # Blade tip (bright)
        _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_hot"], (tip_x, tip_y), 2)
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["fire_shine"], (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["white"], (tip_x, tip_y, 1, 1))

        # Fire aura around blade
        for pt in blade_pts[2::2]:
            for r in range(3, 0, -1):
                alpha = _NS_pyrhaan._alpha(60 * (3 - r) / 3)
                _NS_pyrhaan._aacircle(surface,
                                      (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                      pt, r)

        # Guard (small gold cross)
        perp_x2 = -math.sin(actual_angle)
        perp_y2 = math.cos(actual_angle)
        guard_a = (hand_x + int(perp_x2 * 4), hand_y + int(perp_y2 * 4))
        guard_b = (hand_x - int(perp_x2 * 3), hand_y - int(perp_y2 * 3))
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["gold_dark"],
                            guard_a, guard_b, 3)
        _NS_pyrhaan._aaline(surface, _NS_pyrhaan.PALETTE["gold_mid"],
                            guard_a, guard_b, 1)
        pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["gold_shine"],
                         (hand_x, hand_y, 1, 1))

    # ============================================================
    # BASIC ATTACK — DUAL FLAME SLASH ARC
    # ============================================================
    def _draw_dual_flame_slash(surface, boss, x, y, progress):
        """Twin flame arcs during swing."""
        if progress < 0.35 or progress > 0.75:
            return

        facing = boss.direction
        if progress < 0.55:
            t = (progress - 0.35) / 0.2
        else:
            t = 1 - (progress - 0.55) / 0.2
        intensity = math.sin(t * math.pi)

        # 2 arcs (X-cross slash)
        for arc_i, (v_off, angle_bias) in enumerate([
            (-4, -0.2),   # top arc going down-forward
            (4, 0.2),     # bottom arc going up-forward
        ]):
            cx = x + facing * 18
            cy = y - 4 + v_off

            arc_radius = 24
            segments = 15
            prev = None
            for i in range(segments + 1):
                seg_t = i / segments
                base_angle = -math.pi * 0.5 * facing + angle_bias
                seg_angle = base_angle + seg_t * math.pi * facing
                sx = cx + int(math.cos(seg_angle) * arc_radius)
                sy = cy + int(math.sin(seg_angle) * arc_radius * 0.7)

                if prev is not None and seg_t <= t * 1.3:
                    fade = 1.0 - max(0, (t * 1.3 - seg_t) * 1.2)
                    alpha_outer = _NS_pyrhaan._alpha(180 * intensity * fade)
                    alpha_mid = _NS_pyrhaan._alpha(220 * intensity * fade)
                    alpha_core = _NS_pyrhaan._alpha(255 * intensity * fade)

                    pygame.draw.line(surface,
                                     (*_NS_pyrhaan.PALETTE["fire_darkest"], alpha_outer),
                                     prev, (sx, sy), 6)
                    pygame.draw.line(surface,
                                     (*_NS_pyrhaan.PALETTE["fire_deep"], alpha_mid),
                                     prev, (sx, sy), 4)
                    pygame.draw.line(surface,
                                     (*_NS_pyrhaan.PALETTE["fire_bright"], alpha_core),
                                     prev, (sx, sy), 2)
                    pygame.draw.line(surface,
                                     (*_NS_pyrhaan.PALETTE["fire_hot"], alpha_core),
                                     prev, (sx, sy), 1)

                    # Fire particles trailing
                    if i % 3 == 0 and fade > 0.4:
                        for pi in range(2):
                            p_off_x = int(math.cos(seg_angle) * (pi + 1) * 2)
                            p_off_y = int(math.sin(seg_angle) * (pi + 1) * 2)
                            pygame.draw.rect(surface,
                                             _NS_pyrhaan.PALETTE["fire_light"],
                                             (sx + p_off_x, sy + p_off_y, 2, 2))
                            pygame.draw.rect(surface,
                                             _NS_pyrhaan.PALETTE["fire_hot"],
                                             (sx + p_off_x, sy + p_off_y, 1, 1))

                prev = (sx, sy)

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

    def _draw_fire_aura(surface, x, y, phase):
        """Intense fire aura."""
        pulse = math.sin(phase * 0.7) * 0.3 + 0.7

        aura = pygame.Surface((200, 170), pygame.SRCALPHA)
        for radius in range(85, 5, -5):
            alpha = _NS_pyrhaan._alpha((85 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_pyrhaan._aacircle(aura,
                                      (*_NS_pyrhaan.PALETTE["fire_dark"], alpha),
                                      (100, 85), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_pyrhaan._alpha((55 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_pyrhaan._aacircle(aura,
                                      (*_NS_pyrhaan.PALETTE["fire_deep"], alpha),
                                      (100, 85), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_pyrhaan._alpha((30 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_pyrhaan._aacircle(aura,
                                      (*_NS_pyrhaan.PALETTE["fire_mid"], alpha),
                                      (100, 85), radius)
        surface.blit(aura, (x - 100, y - 85))

        # Rising fire embers
        for i in range(12):
            e_t = (phase * 0.6 + i * 0.08) % 1.0
            e_angle = i * math.pi / 6 + phase * 0.2
            e_r = 30 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(e_angle) * e_r)
            sy = y + 5 - int(e_t * 40)
            alpha = _NS_pyrhaan._alpha(240 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_pyrhaan.PALETTE["fire_hot"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_pyrhaan.PALETTE["fire_shine"], alpha),
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Fire ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_pyrhaan.PALETTE["fire_darkest"], 200),
                            (5, 17, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_pyrhaan.PALETTE["fire_dark"], 220),
                            (14, 19, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_pyrhaan.PALETTE["fire_deep"], 200),
                            (25, 21, 110, 16), 1)

        # Fire runes
        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 28 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 28 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_pyrhaan.PALETTE["fire_bright"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_pyrhaan.PALETTE["fire_hot"],
                                 _NS_pyrhaan._alpha(180 * pulse)),
                                (15, 10, 130, 34), 1)
        surface.blit(ring, (x - 80, y - 25))

    # ============================================================
    # SKILL Q — SEARING CHAINS (fire chains to target)
    # ============================================================
    def _draw_chains_fx(surface, boss, x, y, timer, phase):
        """Fiery chains launching to target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_pyrhaan._target_position(boss, x, y)

        # Chain origin (from boss front hand)
        start_x = x + facing * 20
        start_y = y - 4

        # Chain extends toward target
        if progress < 0.4:
            t = progress / 0.4
        else:
            t = 1.0

        end_x = int(start_x + (tx - start_x) * t)
        end_y = int(start_y + (ty - start_y) * t)

        # Draw chain segments (link balls)
        chain_dist = math.hypot(end_x - start_x, end_y - start_y)
        num_links = max(5, int(chain_dist / 8))

        for link_i in range(num_links + 1):
            link_t = link_i / max(1, num_links)
            # Wavy chain motion
            wave = math.sin(phase * 3 + link_t * math.pi * 4) * 3
            perp_angle = math.atan2(end_y - start_y, end_x - start_x) + math.pi / 2
            wave_x = int(math.cos(perp_angle) * wave)
            wave_y = int(math.sin(perp_angle) * wave)

            lx = int(start_x + (end_x - start_x) * link_t) + wave_x
            ly = int(start_y + (end_y - start_y) * link_t) + wave_y

            # Chain link (small ball with fire glow)
            # Outer glow (fire)
            for r in range(6, 0, -1):
                alpha = _NS_pyrhaan._alpha(80 * (6 - r) / 6)
                _NS_pyrhaan._aacircle(surface,
                                      (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                      (lx, ly), r)
            # Chain link core
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["chain_dark"], (lx, ly), 3)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["chain_mid"], (lx, ly), 2)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_hot"], (lx, ly), 1)
            pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["fire_shine"],
                             (lx, ly, 1, 1))

        # Big fireball at end (impact/latch on target)
        if progress > 0.4:
            impact_pulse = math.sin(phase * 4) * 0.2 + 0.8
            for r in range(12, 3, -1):
                alpha = _NS_pyrhaan._alpha(150 * (12 - r) / 12 * impact_pulse)
                _NS_pyrhaan._aacircle(surface,
                                      (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                      (end_x, end_y), r)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_darkest"],
                                  (end_x, end_y), 6)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_dark"],
                                  (end_x, end_y), 5)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_deep"],
                                  (end_x, end_y), 4)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_mid"],
                                  (end_x, end_y), 3)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_bright"],
                                  (end_x, end_y), 2)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_hot"],
                                  (end_x, end_y), 1)
            pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["fire_shine"],
                             (end_x, end_y, 1, 1))

            # Sparks around impact
            for i in range(8):
                sp_angle = phase * 2 + i * math.pi / 4
                sp_r = 10 + int(math.sin(phase * 3 + i) * 3)
                sx = end_x + int(math.cos(sp_angle) * sp_r)
                sy = end_y + int(math.sin(sp_angle) * sp_r)
                pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["fire_hot"],
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL W — FLAME FIST (dash + fiery punch)
    # ============================================================
    def _draw_flame_fist_fx(surface, boss, x, y, timer, phase):
        """Dash trail + fiery punch impact."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Dash trail (afterimages behind boss)
        for i in range(6):
            trail_off = (i + 1) * 12
            trail_x = x - facing * trail_off
            alpha = _NS_pyrhaan._alpha(150 - i * 25)

            # Ghost silhouette
            ghost_pts = [
                (trail_x - 8, y - 10),
                (trail_x - 10, y),
                (trail_x - 8, y + 10),
                (trail_x + 8, y + 10),
                (trail_x + 10, y),
                (trail_x + 8, y - 10),
            ]
            _NS_pyrhaan._poly(surface,
                              (*_NS_pyrhaan.PALETTE["fire_deep"], alpha),
                              ghost_pts)

            # Fire particles trailing
            for pi in range(3):
                px = trail_x + int(math.sin(phase * 3 + i + pi) * 6)
                py = y + pi * 8 - 12
                pygame.draw.rect(surface,
                                 (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                 (px, py, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_pyrhaan.PALETTE["fire_hot"], alpha),
                                 (px, py, 1, 1))

        # BIG FIST IMPACT at front (during middle of skill)
        if 0.3 < progress < 0.7:
            fist_t = (progress - 0.3) / 0.4
            fist_intensity = math.sin(fist_t * math.pi)

            fist_x = x + facing * 30
            fist_y = y - 4

            # Explosive fist
            for r in range(20, 3, -2):
                alpha = _NS_pyrhaan._alpha(180 * (20 - r) / 20 * fist_intensity)
                _NS_pyrhaan._aacircle(surface,
                                      (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                      (fist_x, fist_y), r)

            # Core fist
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_darkest"],
                                  (fist_x, fist_y), 10)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_dark"],
                                  (fist_x, fist_y), 8)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_deep"],
                                  (fist_x, fist_y), 6)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_mid"],
                                  (fist_x, fist_y), 4)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_bright"],
                                  (fist_x, fist_y), 3)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_hot"],
                                  (fist_x, fist_y), 2)
            pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["fire_shine"],
                             (fist_x, fist_y, 1, 1))

            # Radial spikes (impact sunburst)
            for i in range(12):
                sp_angle = i * math.pi / 6 + phase * 0.5
                sp_len = int(15 + fist_intensity * 8)
                ex = fist_x + int(math.cos(sp_angle) * sp_len)
                ey = fist_y + int(math.sin(sp_angle) * sp_len)
                alpha = _NS_pyrhaan._alpha(220 * fist_intensity)
                pygame.draw.line(surface,
                                 (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                 (fist_x, fist_y), (ex, ey), 2)
                pygame.draw.rect(surface,
                                 (*_NS_pyrhaan.PALETTE["fire_hot"], alpha),
                                 (ex, ey, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_pyrhaan.PALETTE["fire_shine"], alpha),
                                 (ex, ey, 1, 1))

    # ============================================================
    # SKILL E — PHOENIX LEAP (slam ground)
    # ============================================================
    def _draw_phoenix_ground(surface, boss, x, y, timer, phase):
        """Impact ground crater at target."""
        tx, ty = _NS_pyrhaan._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Wind-up: warning circle
        if progress < 0.4:
            t = progress / 0.4
            r = int(15 + t * 15)
            alpha = _NS_pyrhaan._alpha(200 * t)
            pygame.draw.ellipse(surface,
                                (*_NS_pyrhaan.PALETTE["fire_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
        else:
            # Impact crater
            t = (progress - 0.4) / 0.6
            r = int(35 + t * 15)
            alpha = _NS_pyrhaan._alpha(220 * (1 - t * 0.3))
            pygame.draw.ellipse(surface,
                                (*_NS_pyrhaan.PALETTE["fire_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_pyrhaan.PALETTE["fire_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_pyrhaan.PALETTE["fire_deep"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
            pygame.draw.ellipse(surface,
                                (*_NS_pyrhaan.PALETTE["fire_mid"], alpha),
                                (tx - r + 14, ty - r // 3 + 6,
                                 r * 2 - 28, r * 2 // 3 - 12))

    def _draw_phoenix_fg(surface, boss, x, y, timer, phase):
        """Rising fire pillars + falling meteor animation."""
        tx, ty = _NS_pyrhaan._target_position(boss, x, y)
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.4:
            # Wind-up: falling meteor animation
            t = progress / 0.4
            meteor_y = ty - int((1 - t) * 100)

            # Meteor with trail
            for r in range(10, 3, -1):
                alpha = _NS_pyrhaan._alpha(180 * (10 - r) / 10)
                _NS_pyrhaan._aacircle(surface,
                                      (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                      (tx, meteor_y), r)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_darkest"],
                                  (tx, meteor_y), 8)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_deep"],
                                  (tx, meteor_y), 6)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_mid"],
                                  (tx, meteor_y), 4)
            _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_hot"],
                                  (tx, meteor_y), 2)

            # Trail behind meteor
            for i in range(8):
                trail_y = meteor_y - (i + 1) * 8
                if trail_y < 0:
                    break
                alpha = _NS_pyrhaan._alpha(200 - i * 25)
                size = max(1, 6 - i)
                _NS_pyrhaan._aacircle(surface,
                                      (*_NS_pyrhaan.PALETTE["fire_deep"], alpha),
                                      (tx, trail_y), size)
                _NS_pyrhaan._aacircle(surface,
                                      (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                      (tx, trail_y), max(1, size - 1))
                pygame.draw.rect(surface,
                                 (*_NS_pyrhaan.PALETTE["fire_hot"], alpha),
                                 (tx, trail_y, 1, 1))
        else:
            # Impact + rising fire pillars
            t = (progress - 0.4) / 0.6

            # Multiple fire pillars around impact point
            num_pillars = 8
            for i in range(num_pillars):
                p_angle = i * math.pi * 2 / num_pillars + phase * 0.2
                p_dist = int(15 + math.sin(phase + i) * 5)
                px = tx + int(math.cos(p_angle) * p_dist)
                py = ty + int(math.sin(p_angle) * p_dist * 0.4)

                # Rising fire column
                pillar_h = int(30 * math.sin(min(1.0, t * 2) * math.pi * 0.8))
                if pillar_h < 3:
                    continue

                # Draw flame column
                for layer_i in range(6):
                    layer_t = layer_i / 6
                    layer_y = py - int(layer_t * pillar_h)
                    layer_w = int(6 - layer_t * 4)
                    layer_alpha = _NS_pyrhaan._alpha(230 * (1 - layer_t))

                    pygame.draw.ellipse(surface,
                                        (*_NS_pyrhaan.PALETTE["fire_darkest"], layer_alpha),
                                        (px - layer_w, layer_y - 2,
                                         layer_w * 2, 4))
                    pygame.draw.ellipse(surface,
                                        (*_NS_pyrhaan.PALETTE["fire_deep"], layer_alpha),
                                        (px - layer_w + 1, layer_y - 1,
                                         layer_w * 2 - 2, 3))
                    pygame.draw.ellipse(surface,
                                        (*_NS_pyrhaan.PALETTE["fire_bright"], layer_alpha),
                                        (px - layer_w + 2, layer_y - 1,
                                         layer_w * 2 - 4, 2))
                    pygame.draw.rect(surface,
                                     (*_NS_pyrhaan.PALETTE["fire_hot"], layer_alpha),
                                     (px, layer_y, 1, 1))

                # Bright tip
                if pillar_h > 5:
                    tip_y = py - pillar_h
                    _NS_pyrhaan._aacircle(surface, _NS_pyrhaan.PALETTE["fire_hot"],
                                          (px, tip_y), 2)
                    pygame.draw.rect(surface, _NS_pyrhaan.PALETTE["fire_shine"],
                                     (px, tip_y, 1, 1))

            # Central explosion
            explode_r = int(20 + t * 20)
            explode_alpha = _NS_pyrhaan._alpha(200 * (1 - t))
            for layer_r in range(explode_r, 3, -3):
                alpha = _NS_pyrhaan._alpha(explode_alpha *
                                            (explode_r - layer_r) / explode_r)
                _NS_pyrhaan._aacircle(surface,
                                      (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                      (tx, ty), layer_r)

            # Sparks flying outward
            for i in range(15):
                sp_angle = i * math.pi / 7.5 + phase
                sp_dist = int(15 + t * 25)
                sx = tx + int(math.cos(sp_angle) * sp_dist)
                sy = ty + int(math.sin(sp_angle) * sp_dist * 0.7)
                alpha = _NS_pyrhaan._alpha(230 * (1 - t))
                pygame.draw.rect(surface,
                                 (*_NS_pyrhaan.PALETTE["fire_hot"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_pyrhaan.PALETTE["fire_shine"], alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL R — CINDER REMNANT (fire clone silhouette)
    # ============================================================
    def _draw_remnant(surface, boss, x, y, timer, phase):
        """Fire silhouette copy of boss standing to the side."""
        facing = boss.direction
        # Position remnant behind current position
        remnant_x = x - facing * 60
        remnant_y = y

        # Pulsing intensity
        pulse = math.sin(phase * 2) * 0.2 + 0.8

        # Draw silhouette (all fire colors, no detail)
        # Body silhouette
        body_pts = [
            (remnant_x - 12, remnant_y + 40),
            (remnant_x - 14, remnant_y),
            (remnant_x - 10, remnant_y - 8),
            (remnant_x - 8, remnant_y - 22),
            (remnant_x + 8, remnant_y - 22),
            (remnant_x + 10, remnant_y - 8),
            (remnant_x + 14, remnant_y),
            (remnant_x + 12, remnant_y + 40),
            (remnant_x + 6, remnant_y + 42),
            (remnant_x - 6, remnant_y + 42),
        ]

        # Layered fire silhouette (outer glow to bright core)
        # Outer aura
        for r in range(35, 5, -3):
            alpha = _NS_pyrhaan._alpha(60 * (35 - r) / 30 * pulse)
            _NS_pyrhaan._aacircle(surface,
                                  (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                                  (remnant_x, remnant_y + 5), r)

        # Body silhouette layers
        alpha_outer = _NS_pyrhaan._alpha(200 * pulse)
        _NS_pyrhaan._poly(surface, (*_NS_pyrhaan.PALETTE["fire_dark"], alpha_outer),
                          body_pts)

        inner_pts = [(int(px * 0.85 + remnant_x * 0.15),
                      int(py * 0.85 + (remnant_y + 5) * 0.15))
                     for px, py in body_pts]
        _NS_pyrhaan._poly(surface,
                          (*_NS_pyrhaan.PALETTE["fire_deep"], alpha_outer),
                          inner_pts)

        core_pts = [(int(px * 0.7 + remnant_x * 0.3),
                     int(py * 0.7 + (remnant_y + 5) * 0.3))
                    for px, py in body_pts]
        _NS_pyrhaan._poly(surface,
                          (*_NS_pyrhaan.PALETTE["fire_bright"], alpha_outer),
                          core_pts)

        # Bright center
        center_pts = [(int(px * 0.5 + remnant_x * 0.5),
                       int(py * 0.5 + (remnant_y + 5) * 0.5))
                      for px, py in body_pts]
        _NS_pyrhaan._poly(surface, (*_NS_pyrhaan.PALETTE["fire_hot"], alpha_outer),
                          center_pts)

        # Glowing eyes
        for eye_x_off in (-2, 2):
            ex = remnant_x + eye_x_off
            ey = remnant_y - 27
            for r in range(4, 0, -1):
                a = _NS_pyrhaan._alpha(120 * (4 - r) / 4 * pulse)
                _NS_pyrhaan._aacircle(surface,
                                      (*_NS_pyrhaan.PALETTE["fire_shine"], a),
                                      (ex, ey), r)

        # Rising embers from remnant
        for i in range(6):
            e_t = (phase * 0.8 + i * 0.15) % 1.0
            ex = remnant_x + int(math.sin(phase + i) * 8)
            ey = remnant_y + 20 - int(e_t * 40)
            alpha = _NS_pyrhaan._alpha(230 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_pyrhaan.PALETTE["fire_bright"], alpha),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface, (*_NS_pyrhaan.PALETTE["fire_hot"], alpha),
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, (*_NS_pyrhaan.PALETTE["fire_shine"], alpha),
                             (ex, ey, 1, 1))

        # Fire trail connecting boss to remnant (recast path)
        line_alpha = _NS_pyrhaan._alpha(120 * pulse)
        segments = 10
        for i in range(segments):
            t1 = i / segments
            t2 = (i + 1) / segments
            x1 = int(x + (remnant_x - x) * t1)
            y1 = int(y + (remnant_y - y) * t1)
            x2 = int(x + (remnant_x - x) * t2)
            y2 = int(y + (remnant_y - y) * t2)
            wave = math.sin(phase * 2 + i * 0.5) * 3
            y1 += int(wave)
            y2 += int(wave)
            pygame.draw.line(surface,
                             (*_NS_pyrhaan.PALETTE["fire_deep"], line_alpha),
                             (x1, y1), (x2, y2), 4)
            pygame.draw.line(surface,
                             (*_NS_pyrhaan.PALETTE["fire_bright"], line_alpha),
                             (x1, y1), (x2, y2), 2)


# ====================================================================
# ALIAS
# ====================================================================
draw_pyrhaan = _NS_pyrhaan.draw_pyrhaan


# ====================================================================================================
# KAITHROS - TRUE BOSS
# ====================================================================================================

class _NS_kaithros:
    """Namespace kaithros - HD rendering untuk mini boss Kaithros."""

    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")

    PALETTE = {
        # Fire (main - orange/red/yellow gradient)
        "fire_darkest": (30, 5, 0),
        "fire_dark": (90, 20, 5),
        "fire_deep": (150, 40, 10),
        "fire_mid": (220, 90, 20),
        "fire_bright": (255, 150, 40),
        "fire_light": (255, 200, 80),
        "fire_hot": (255, 230, 130),
        "fire_shine": (255, 250, 200),
        "fire_white": (255, 255, 240),

        # Haori (white with fire pattern)
        "haori_shadow": (55, 50, 45),
        "haori_dark": (140, 130, 120),
        "haori_mid": (200, 190, 180),
        "haori_light": (235, 225, 215),
        "haori_shine": (255, 250, 245),

        # Uniform inner (dark)
        "uniform_darkest": (8, 8, 12),
        "uniform_dark": (22, 22, 28),
        "uniform_mid": (48, 48, 58),
        "uniform_light": (85, 85, 100),

        # Hair (flame red-gold-orange mane)
        "mane_darkest": (55, 15, 5),
        "mane_dark": (130, 40, 10),
        "mane_deep": (200, 80, 15),
        "mane_mid": (240, 140, 30),
        "mane_light": (255, 200, 80),
        "mane_shine": (255, 235, 140),

        # Skin (tanned warrior)
        "skin_dark": (110, 70, 45),
        "skin_mid": (180, 130, 90),
        "skin_light": (230, 185, 145),
        "skin_shine": (250, 220, 190),

        # Eyes (piercing gold-yellow)
        "eye_dark": (60, 40, 10),
        "eye_mid": (200, 150, 30),
        "eye_light": (255, 220, 100),
        "eye_shine": (255, 245, 180),

        # Katana blade
        "blade_dark": (60, 65, 80),
        "blade_mid": (140, 150, 170),
        "blade_light": (215, 220, 235),
        "blade_shine": (250, 253, 255),
        "blade_edge": (255, 255, 255),

        # Hilt/tsuka
        "hilt_dark": (20, 20, 30),
        "hilt_mid": (55, 55, 75),
        "hilt_wrap": (60, 30, 20),
        "guard_dark": (60, 45, 15),
        "guard_mid": (140, 110, 50),
        "guard_light": (220, 190, 110),

        # Belt (dark leather)
        "belt_dark": (35, 25, 15),
        "belt_mid": (85, 60, 30),
        "belt_light": (155, 115, 60),

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
        color = _NS_kaithros._clamp(color)
        if _NS_kaithros.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)

    def _aaline(surface, color, start, end, width=1):
        color = _NS_kaithros._clamp(color)
        if _NS_kaithros.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)

    def _poly(surface, color, points):
        pygame.draw.polygon(surface, _NS_kaithros._clamp(color), points)

    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 120 * getattr(boss, "direction", 1)), int(y)

    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kaithros(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kaithros._detect_moving(boss)
        _NS_kaithros._update_attack_anim(boss)
        attacking = getattr(boss, "_ka_attack_active", False)

        # Ambient
        _NS_kaithros._draw_shadow(surface, x, y + 52)
        _NS_kaithros._draw_flame_aura(surface, x, y, pulse)
        _NS_kaithros._draw_ground_ring(surface, x, y + 48, pulse, active_skill)

        # Skill ground FX (behind body)
        if active_skill == "e":
            _NS_kaithros._draw_pillar_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaithros._draw_emberlion_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaithros._draw_rising_sun_ground(surface, boss, x, y, skill_timer, pulse)

        # Body
        if attacking:
            _NS_kaithros._draw_body_attack(surface, boss, x, y)
        elif moving:
            _NS_kaithros._draw_body_walk(surface, boss, x, y)
        else:
            _NS_kaithros._draw_body_idle(surface, boss, x, y)

        # Foreground skill FX
        if active_skill == "q":
            _NS_kaithros._draw_unknowing_fire_fx(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kaithros._draw_rising_sun_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kaithros._draw_pillar_fg(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kaithros._draw_emberlion_fg(surface, boss, x, y, skill_timer, pulse)

    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 42)))
        timer = int(getattr(boss, "timer", 0))
        active = bool(getattr(boss, "_ka_attack_active", False))

        if not active:
            if timer >= cooldown - 22:
                boss._ka_attack_active = True
                boss._ka_attack_frame = 0
                active = True

        if active:
            boss._ka_attack_frame = int(getattr(boss, "_ka_attack_frame", 0)) + 1
            attack_duration = 28
            if boss._ka_attack_frame >= attack_duration:
                boss._ka_attack_active = False
                boss._ka_attack_frame = 0
                active = False

        attack_duration = 28
        boss._ka_attack_progress = (
            min(1.0, getattr(boss, "_ka_attack_frame", 0) / attack_duration)
            if active else 0.0
        )

    def _detect_moving(boss):
        if not hasattr(boss, "_ka_last_x"):
            boss._ka_last_x = boss.x
            boss._ka_last_y = boss.y
            return False
        dx = abs(boss.x - boss._ka_last_x)
        dy = abs(boss.y - boss._ka_last_y)
        boss._ka_last_x = boss.x
        boss._ka_last_y = boss.y
        return dx + dy > 0.3

    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_body_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.55) * 3)
        _NS_kaithros._draw_full_body(surface, x, y + bob,
                                     boss.direction, boss.pulse, "idle", 0)

    def _draw_body_walk(surface, boss, x, y):
        phase = boss.pulse * 2.0
        bob = int(math.sin(phase * 0.9) * 4)
        sway = int(math.sin(phase * 0.7) * 2)
        _NS_kaithros._draw_full_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "walk", 0)

    def _draw_body_attack(surface, boss, x, y):
        progress = getattr(boss, "_ka_attack_progress", 0.0)
        progress = max(0.0, min(1.0, progress))

        if progress < 0.35:
            t = progress / 0.35
            lunge = -int(t * 5) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.35) / 0.25
            ease = 1 - (1 - t) ** 2
            lunge = int((-5 + ease * 20)) * boss.direction
            lift = int(3 - ease * 5)
        else:
            t = (progress - 0.6) / 0.4
            lunge = int(15 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)

        _NS_kaithros._draw_full_body(surface, x + lunge, y - lift,
                                     boss.direction, boss.pulse, "attack", progress)
        _NS_kaithros._draw_katana_flame_slash(surface, boss, x + lunge,
                                                y - lift, progress)

    # ============================================================
    # FULL BODY
    # ============================================================
    def _draw_full_body(surface, cx, cy, facing, phase, action, atk_prog):
        # 1. Cape/haori (behind, flowing)
        _NS_kaithros._draw_haori_back(surface, cx, cy, facing, phase)
        # 2. Legs
        _NS_kaithros._draw_legs(surface, cx, cy, facing, phase, action)
        # 3. Back arm
        _NS_kaithros._draw_back_arm(surface, cx, cy, facing, phase, action)
        # 4. Haori lower/front
        _NS_kaithros._draw_haori_front(surface, cx, cy, facing, phase)
        # 5. Torso
        _NS_kaithros._draw_torso(surface, cx, cy, facing, phase)
        # 6. Head + FLAME MANE
        _NS_kaithros._draw_head(surface, cx, cy - 24, facing, phase)
        # 7. Front arm + KATANA
        _NS_kaithros._draw_front_arm_with_katana(surface, cx, cy, facing,
                                                  phase, action, atk_prog)

    def _draw_haori_back(surface, cx, cy, facing, phase):
        """White haori flowing behind (with flame pattern on edges)."""
        sway = math.sin(phase * 0.5) * 3
        back_dir = -facing

        haori_pts = [
            (cx + back_dir * 4, cy - 10),
            (cx + back_dir * 10, cy - 6),
            (cx + back_dir * 15, cy + 2),
            (cx + back_dir * 20 + int(sway * back_dir), cy + 14),
            (cx + back_dir * 22 + int(sway * back_dir * 1.5), cy + 28),
            (cx + back_dir * 19 + int(sway * back_dir * 2), cy + 40),
            (cx + back_dir * 12 + int(sway * back_dir), cy + 46),
            (cx + back_dir * 4, cy + 44),
            (cx, cy + 30),
            (cx + back_dir * 2, cy + 8),
            (cx + back_dir * 3, cy - 5),
        ]
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["shadow_deep"],
                           [(px + 2, py + 3) for px, py in haori_pts])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["haori_shadow"], haori_pts)
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["haori_dark"], [
            (cx + back_dir * 3, cy - 9),
            (cx + back_dir * 9, cy - 5),
            (cx + back_dir * 14, cy + 3),
            (cx + back_dir * 18 + int(sway * back_dir), cy + 14),
            (cx + back_dir * 20 + int(sway * back_dir * 1.5), cy + 28),
            (cx + back_dir * 16, cy + 38),
            (cx + back_dir * 10, cy + 44),
            (cx + back_dir * 3, cy + 42),
        ])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["haori_mid"], [
            (cx + back_dir * 4, cy - 3),
            (cx + back_dir * 12, cy + 4),
            (cx + back_dir * 15 + int(sway * back_dir), cy + 18),
            (cx + back_dir * 13, cy + 32),
            (cx + back_dir * 5, cy + 32),
            (cx + back_dir * 3, cy + 10),
        ])
        # Cape highlight (bright white)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["haori_light"],
                             (cx + back_dir * 5, cy - 2),
                             (cx + back_dir * 9, cy + 16), 1)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["haori_shine"],
                             (cx + back_dir * 6, cy + 2),
                             (cx + back_dir * 8, cy + 14), 1)

        # FLAME PATTERN on bottom edge (red-orange tongues)
        for flame_i in range(5):
            base_off = flame_i * 4 - 8
            fbase_x = cx + back_dir * (16 + base_off + int(sway * back_dir))
            fbase_y = cy + 38 + int(math.sin(phase + flame_i) * 2)
            ftip_x = fbase_x + int(math.sin(phase * 2 + flame_i) * 2)
            ftip_y = fbase_y + 6  # flames droop down

            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_darkest"], [
                (fbase_x - 3, fbase_y),
                (ftip_x, ftip_y),
                (fbase_x + 3, fbase_y),
            ])
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_deep"], [
                (fbase_x - 2, fbase_y),
                (ftip_x, ftip_y - 1),
                (fbase_x + 2, fbase_y),
            ])
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_bright"], [
                (fbase_x - 1, fbase_y),
                (ftip_x, ftip_y - 2),
                (fbase_x + 1, fbase_y),
            ])
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["fire_hot"],
                             (ftip_x, ftip_y - 2, 1, 1))

        # Rising embers along cape
        for i in range(4):
            e_t = (phase * 0.6 + i * 0.25) % 1.0
            ex = cx + back_dir * (8 + int(math.sin(phase + i) * 4))
            ey = cy + 10 - int(e_t * 30)
            alpha = _NS_kaithros._alpha(200 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_bright"], alpha),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                             (ex, ey, 1, 1))

    def _draw_haori_front(surface, cx, cy, facing, phase):
        """Front hem of the haori — split flowing."""
        sway = math.sin(phase * 0.6) * 2
        # Only draw partial front hem (asymmetric — draped over one shoulder)
        front_dir = facing
        front_pts = [
            (cx + front_dir * 2, cy - 8),
            (cx + front_dir * 8, cy - 4),
            (cx + front_dir * 12, cy + 6),
            (cx + front_dir * 14, cy + 20),
            (cx + front_dir * 12 + int(sway * front_dir), cy + 34),
            (cx + front_dir * 6, cy + 40),
            (cx, cy + 36),
            (cx + front_dir * 3, cy + 12),
            (cx + front_dir * 2, cy - 4),
        ]
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in front_pts])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["haori_shadow"], front_pts)
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["haori_dark"], [
            (cx + front_dir * 3, cy - 6),
            (cx + front_dir * 7, cy - 3),
            (cx + front_dir * 11, cy + 6),
            (cx + front_dir * 13, cy + 20),
            (cx + front_dir * 10 + int(sway * front_dir), cy + 32),
            (cx + front_dir * 5, cy + 38),
            (cx + front_dir * 1, cy + 34),
        ])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["haori_mid"], [
            (cx + front_dir * 5, cy - 2),
            (cx + front_dir * 9, cy + 6),
            (cx + front_dir * 10, cy + 20),
            (cx + front_dir * 6, cy + 30),
            (cx + front_dir * 3, cy + 12),
        ])
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["haori_light"],
                             (cx + front_dir * 6, cy + 2),
                             (cx + front_dir * 8, cy + 24), 1)

        # Flame pattern on front bottom edge
        for flame_i in range(3):
            base_off = flame_i * 3
            fbase_x = cx + front_dir * (7 + base_off + int(sway * front_dir))
            fbase_y = cy + 32 + int(math.sin(phase + flame_i) * 1)
            ftip_x = fbase_x + int(math.sin(phase * 2 + flame_i) * 2)
            ftip_y = fbase_y + 5

            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_darkest"], [
                (fbase_x - 2, fbase_y),
                (ftip_x, ftip_y),
                (fbase_x + 2, fbase_y),
            ])
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_bright"], [
                (fbase_x - 1, fbase_y),
                (ftip_x, ftip_y - 1),
                (fbase_x + 1, fbase_y),
            ])

    def _draw_legs(surface, cx, cy, facing, phase, action):
        """Legs in dark hakama."""
        leg_sway = 0
        if action == "walk":
            leg_sway = math.sin(phase) * 3

        # Back leg
        back_x = cx - 4
        back_y_top = cy + 8
        back_y_bot = cy + 42 + int(-leg_sway)

        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["shadow_deep"],
                             (back_x + 1, back_y_top + 1),
                             (back_x + 1, back_y_bot + 1), 8)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_darkest"],
                             (back_x, back_y_top), (back_x, back_y_bot), 7)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_dark"],
                             (back_x, back_y_top), (back_x, back_y_bot), 5)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_mid"],
                             (back_x - 1, back_y_top), (back_x - 1, back_y_bot), 2)

        # Front leg
        front_x = cx + 4
        front_y_top = cy + 8
        front_y_bot = cy + 42 + int(leg_sway)

        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["shadow_deep"],
                             (front_x + 1, front_y_top + 1),
                             (front_x + 1, front_y_bot + 1), 8)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_darkest"],
                             (front_x, front_y_top), (front_x, front_y_bot), 7)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_dark"],
                             (front_x, front_y_top), (front_x, front_y_bot), 5)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_mid"],
                             (front_x - 1, front_y_top), (front_x - 1, front_y_bot), 2)

        # Sandals
        for foot_x, foot_y in ((back_x, back_y_bot), (front_x, front_y_bot)):
            pygame.draw.ellipse(surface, _NS_kaithros.PALETTE["shadow_deep"],
                                (foot_x - 5, foot_y - 1, 12, 6))
            pygame.draw.ellipse(surface, _NS_kaithros.PALETTE["uniform_darkest"],
                                (foot_x - 4, foot_y, 10, 4))
            pygame.draw.ellipse(surface, _NS_kaithros.PALETTE["uniform_dark"],
                                (foot_x - 4, foot_y, 10, 3))

    def _draw_torso(surface, cx, cy, facing, phase):
        """Dark uniform torso under haori."""
        torso_pts = [
            (cx - 12, cy - 8),
            (cx - 14, cy - 2),
            (cx - 13, cy + 6),
            (cx - 8, cy + 10),
            (cx + 8, cy + 10),
            (cx + 13, cy + 6),
            (cx + 14, cy - 2),
            (cx + 12, cy - 8),
            (cx + 5, cy - 12),
            (cx - 5, cy - 12),
        ]
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in torso_pts])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["uniform_darkest"], torso_pts)
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["uniform_dark"], [
            (cx - 11, cy - 6),
            (cx - 13, cy - 1),
            (cx - 12, cy + 5),
            (cx - 7, cy + 9),
            (cx + 7, cy + 9),
            (cx + 12, cy + 5),
            (cx + 13, cy - 1),
            (cx + 11, cy - 6),
            (cx + 4, cy - 10),
            (cx - 4, cy - 10),
        ])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["uniform_mid"], [
            (cx - 9, cy - 4),
            (cx - 10, cy + 2),
            (cx - 6, cy + 7),
            (cx + 6, cy + 7),
            (cx + 10, cy + 2),
            (cx + 9, cy - 4),
            (cx + 3, cy - 8),
            (cx - 3, cy - 8),
        ])

        # HAORI OPEN COLLAR (V-neck showing chest)
        # White haori draped over shoulders
        for shoulder_x_off in (-11, 11):
            sx = cx + shoulder_x_off
            sy = cy - 6
            pygame.draw.ellipse(surface, _NS_kaithros.PALETTE["shadow_deep"],
                                (sx - 4, sy - 3, 10, 8))
            pygame.draw.ellipse(surface, _NS_kaithros.PALETTE["haori_dark"],
                                (sx - 4, sy - 3, 9, 7))
            pygame.draw.ellipse(surface, _NS_kaithros.PALETTE["haori_mid"],
                                (sx - 3, sy - 2, 7, 5))
            pygame.draw.ellipse(surface, _NS_kaithros.PALETTE["haori_light"],
                                (sx - 2, sy - 2, 5, 3))
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["haori_shine"],
                             (sx - 1, sy - 2, 2, 1))

        # V-collar showing chest (skin visible)
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["skin_dark"], [
            (cx - 3, cy - 10),
            (cx + 3, cy - 10),
            (cx, cy - 3),
        ])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["skin_mid"], [
            (cx - 2, cy - 9),
            (cx + 2, cy - 9),
            (cx, cy - 4),
        ])

        # BELT (dark leather with buckle)
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["shadow_deep"],
                         (cx - 13, cy + 7, 27, 5))
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["belt_dark"],
                         (cx - 12, cy + 8, 25, 4))
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["belt_mid"],
                         (cx - 12, cy + 8, 25, 2))
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["belt_light"],
                         (cx - 10, cy + 8, 20, 1))
        # Metal buckle center
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["guard_dark"],
                         (cx - 3, cy + 7, 6, 6))
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["guard_mid"],
                         (cx - 2, cy + 8, 4, 4))
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["guard_light"],
                         (cx - 1, cy + 9, 1, 1))

    def _draw_head(surface, cx, cy, facing, phase):
        """Head with LION-LIKE FLAME MANE hair."""
        # ==== FLAME MANE HAIR (BACKDROP - large silhouette) ====
        # Mane extends far out from head like a lion
        mane_pts = [
            (cx - 12, cy + 12),
            (cx - 16, cy + 4),
            (cx - 18, cy - 4),
            (cx - 18, cy - 12),
            (cx - 15, cy - 18),
            (cx - 10, cy - 22),
            (cx - 4, cy - 24),
            (cx + 4, cy - 24),
            (cx + 10, cy - 22),
            (cx + 15, cy - 18),
            (cx + 18, cy - 12),
            (cx + 18, cy - 4),
            (cx + 16, cy + 4),
            (cx + 12, cy + 12),
            (cx + 14, cy + 20),
            (cx + 10, cy + 22),
            (cx + 5, cy + 20),
            (cx, cy + 20),
            (cx - 5, cy + 20),
            (cx - 10, cy + 22),
            (cx - 14, cy + 20),
        ]
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in mane_pts])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["mane_darkest"], mane_pts)

        # Mid layer of mane (deeper red)
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["mane_dark"], [
            (cx - 11, cy + 11),
            (cx - 15, cy + 3),
            (cx - 17, cy - 4),
            (cx - 17, cy - 12),
            (cx - 14, cy - 17),
            (cx - 9, cy - 21),
            (cx + 9, cy - 21),
            (cx + 14, cy - 17),
            (cx + 17, cy - 12),
            (cx + 17, cy - 4),
            (cx + 15, cy + 3),
            (cx + 11, cy + 11),
            (cx + 12, cy + 18),
            (cx - 12, cy + 18),
        ])
        # Deeper layer (orange)
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["mane_deep"], [
            (cx - 10, cy + 8),
            (cx - 13, cy + 1),
            (cx - 15, cy - 6),
            (cx - 14, cy - 14),
            (cx - 8, cy - 18),
            (cx + 8, cy - 18),
            (cx + 14, cy - 14),
            (cx + 15, cy - 6),
            (cx + 13, cy + 1),
            (cx + 10, cy + 8),
        ])
        # Mid orange
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["mane_mid"], [
            (cx - 8, cy + 4),
            (cx - 12, cy - 4),
            (cx - 12, cy - 12),
            (cx - 6, cy - 16),
            (cx + 6, cy - 16),
            (cx + 12, cy - 12),
            (cx + 12, cy - 4),
            (cx + 8, cy + 4),
        ])

        # ==== Individual flame spikes around mane edge ====
        mane_spikes = [
            (-16, -8, 5),   # left mid
            (-14, -16, 6),  # left upper
            (-8, -22, 5),   # left top
            (-2, -24, 5),   # top left
            (2, -24, 5),    # top right
            (8, -22, 5),    # right top
            (14, -16, 6),   # right upper
            (16, -8, 5),    # right mid
            (-15, 6, 4),    # left lower
            (15, 6, 4),     # right lower
        ]
        for base_x, base_y, length in mane_spikes:
            fbase_x = cx + base_x
            fbase_y = cy + base_y
            # Direction outward from center
            dx = base_x
            dy = base_y - 2
            norm = math.hypot(dx, dy) or 1
            dx /= norm
            dy /= norm
            wobble = math.sin(phase * 1.5 + base_x * 0.3) * 1.5
            ftip_x = int(fbase_x + dx * (length + wobble))
            ftip_y = int(fbase_y + dy * (length + wobble))

            # Flame spike
            perp_x = -dy * 2
            perp_y = dx * 2
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["mane_darkest"], [
                (fbase_x + int(perp_x), fbase_y + int(perp_y)),
                (ftip_x, ftip_y),
                (fbase_x - int(perp_x), fbase_y - int(perp_y)),
            ])
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["mane_dark"], [
                (fbase_x + int(perp_x * 0.5), fbase_y + int(perp_y * 0.5)),
                (ftip_x, ftip_y),
                (fbase_x - int(perp_x * 0.5), fbase_y - int(perp_y * 0.5)),
            ])
            # Bright tip
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["mane_deep"], [
                (int((fbase_x + ftip_x) / 2 + perp_x * 0.3),
                 int((fbase_y + ftip_y) / 2 + perp_y * 0.3)),
                (ftip_x, ftip_y),
                (int((fbase_x + ftip_x) / 2 - perp_x * 0.3),
                 int((fbase_y + ftip_y) / 2 - perp_y * 0.3)),
            ])
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["mane_light"],
                             (ftip_x, ftip_y, 1, 1))
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["mane_shine"],
                             (ftip_x, ftip_y, 1, 1))

        # Small flame embers rising from mane
        for i in range(6):
            e_t = (phase * 1.2 + i * 0.16) % 1.0
            e_angle = i * math.pi / 3 + phase * 0.3
            e_r = 18 + int(e_t * 8)
            ex = cx + int(math.cos(e_angle) * e_r)
            ey = cy - 10 - int(e_t * 15) + int(math.sin(e_angle) * e_r * 0.3)
            alpha = _NS_kaithros._alpha(230 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_shine"], alpha),
                             (ex, ey, 1, 1))

        # ==== FACE ====
        face_pts = [
            (cx - 5, cy + 5),
            (cx - 6, cy - 2),
            (cx - 4, cy - 7),
            (cx + 4, cy - 7),
            (cx + 6, cy - 2),
            (cx + 5, cy + 5),
        ]
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["skin_dark"], face_pts)
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["skin_mid"], [
            (cx - 4, cy + 4),
            (cx - 5, cy - 2),
            (cx - 3, cy - 6),
            (cx + 3, cy - 6),
            (cx + 5, cy - 2),
            (cx + 4, cy + 4),
        ])
        # Skin highlight
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["skin_light"],
                         (cx - 3, cy - 3, 6, 1))
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["skin_shine"],
                         (cx - 1, cy - 3, 2, 1))

        # Front bangs (red hair falling over forehead)
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["mane_darkest"], [
            (cx - 5, cy - 6),
            (cx - 4, cy - 8),
            (cx - 2, cy - 5),
            (cx, cy - 7),
            (cx + 2, cy - 5),
            (cx + 4, cy - 8),
            (cx + 5, cy - 6),
            (cx + 4, cy - 4),
            (cx - 4, cy - 4),
        ])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["mane_dark"], [
            (cx - 4, cy - 5),
            (cx - 2, cy - 4),
            (cx, cy - 6),
            (cx + 2, cy - 4),
            (cx + 4, cy - 5),
            (cx + 3, cy - 3),
            (cx - 3, cy - 3),
        ])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["mane_deep"], [
            (cx - 2, cy - 4),
            (cx, cy - 5),
            (cx + 2, cy - 4),
            (cx, cy - 3),
        ])

        # ==== EYES (piercing gold) ====
        eye_pulse = math.sin(phase * 2) * 0.2 + 0.8
        for eye_x_off in (-2, 2):
            ex = cx + eye_x_off * facing
            ey = cy - 3
            # Eye white
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["skin_shine"],
                             (ex - 1, ey, 2, 1))
            # Gold iris
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["eye_dark"],
                             (ex, ey, 1, 1))
            # Glow
            for r in range(3, 0, -1):
                alpha = _NS_kaithros._alpha(90 * (3 - r) / 3 * eye_pulse)
                _NS_kaithros._aacircle(surface,
                                       (*_NS_kaithros.PALETTE["eye_mid"], alpha),
                                       (ex, ey), r)
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["eye_shine"],
                             (ex, ey, 1, 1))

        # ==== MOUTH (stern) ====
        pygame.draw.line(surface, _NS_kaithros.PALETTE["skin_dark"],
                         (cx - 2, cy + 2), (cx + 2, cy + 2), 1)

        # Small stubble/beard shadow
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["skin_dark"],
                         (cx - 2, cy + 4, 4, 1))

    def _draw_back_arm(surface, cx, cy, facing, phase, action):
        """Back arm - hidden behind body."""
        sway = math.sin(phase * 0.9) * 1
        back_shoulder_x = cx - facing * 10
        back_shoulder_y = cy - 6
        back_hand_x = back_shoulder_x - facing * 3 + int(sway)
        back_hand_y = cy + 8

        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["shadow_deep"],
                             (back_shoulder_x + 1, back_shoulder_y + 1),
                             (back_hand_x + 1, back_hand_y + 1), 6)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_darkest"],
                             (back_shoulder_x, back_shoulder_y),
                             (back_hand_x, back_hand_y), 5)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_dark"],
                             (back_shoulder_x, back_shoulder_y),
                             (back_hand_x, back_hand_y), 3)
        # Back hand
        _NS_kaithros._aacircle(surface, _NS_kaithros.PALETTE["skin_dark"],
                               (back_hand_x, back_hand_y), 3)
        _NS_kaithros._aacircle(surface, _NS_kaithros.PALETTE["skin_mid"],
                               (back_hand_x, back_hand_y), 2)

    def _draw_front_arm_with_katana(surface, cx, cy, facing, phase, action, atk_prog):
        """Front arm holding katana."""
        sway = math.sin(phase * 0.9) * 2
        front_shoulder_x = cx + facing * 10
        front_shoulder_y = cy - 6

        # Katana angle
        if action == "attack":
            if atk_prog < 0.35:
                # Wind-up: sword raised HIGH
                t = atk_prog / 0.35
                sword_angle = -math.pi * 0.25 - t * math.pi * 0.75
                hand_off_x = facing * int(-6 - t * 2)
                hand_off_y = int(-6 - t * 8)
            elif atk_prog < 0.6:
                # SWING: fast downward
                t = (atk_prog - 0.35) / 0.25
                ease = 1 - (1 - t) ** 2
                sword_angle = -math.pi * 1.0 + ease * math.pi * 1.15
                hand_off_x = facing * int(-8 + ease * 24)
                hand_off_y = int(-14 + ease * 18)
            else:
                # Recovery
                t = (atk_prog - 0.6) / 0.4
                sword_angle = math.pi * 0.15 - t * math.pi * 0.15
                hand_off_x = facing * int(16 - t * 10)
                hand_off_y = int(4 - t * 4)
        elif action == "walk":
            sword_angle = -math.pi * 0.15 + math.sin(phase) * 0.05
            hand_off_x = facing * 8
            hand_off_y = int(4 + sway)
        else:
            # Idle: katana held ready horizontally
            sword_angle = -math.pi * 0.15 + math.sin(phase * 0.5) * 0.02
            hand_off_x = facing * 8
            hand_off_y = int(4 - sway)

        front_hand_x = front_shoulder_x + hand_off_x
        front_hand_y = front_shoulder_y + hand_off_y

        # Elbow
        elbow_x = int((front_shoulder_x + front_hand_x) / 2) + facing * 3
        elbow_y = int((front_shoulder_y + front_hand_y) / 2) + 1

        # Upper arm (uniform + haori sleeve)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["shadow_deep"],
                             (front_shoulder_x + 1, front_shoulder_y + 1),
                             (elbow_x + 1, elbow_y + 1), 6)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_darkest"],
                             (front_shoulder_x, front_shoulder_y),
                             (elbow_x, elbow_y), 5)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_dark"],
                             (front_shoulder_x, front_shoulder_y),
                             (elbow_x, elbow_y), 3)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_mid"],
                             (front_shoulder_x - 1, front_shoulder_y - 1),
                             (elbow_x - 1, elbow_y - 1), 1)

        # Forearm
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 1),
                             (front_hand_x + 1, front_hand_y + 1), 5)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_darkest"],
                             (elbow_x, elbow_y),
                             (front_hand_x, front_hand_y), 4)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["uniform_dark"],
                             (elbow_x, elbow_y),
                             (front_hand_x, front_hand_y), 2)

        # Hand
        _NS_kaithros._aacircle(surface, _NS_kaithros.PALETTE["skin_dark"],
                               (front_hand_x, front_hand_y), 4)
        _NS_kaithros._aacircle(surface, _NS_kaithros.PALETTE["skin_mid"],
                               (front_hand_x, front_hand_y), 3)
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["skin_light"],
                         (front_hand_x - 1, front_hand_y - 1, 1, 1))

        # KATANA
        _NS_kaithros._draw_katana(surface, front_hand_x, front_hand_y,
                                   sword_angle, facing, phase, action)

    def _draw_katana(surface, hand_x, hand_y, angle, facing, phase, action):
        """Long curved katana blade with flame aura (always burning)."""
        actual_angle = angle if facing > 0 else math.pi - angle

        blade_length = 34
        tip_x = hand_x + int(math.cos(actual_angle) * blade_length)
        tip_y = hand_y + int(math.sin(actual_angle) * blade_length)

        # Perpendicular
        perp_x = -math.sin(actual_angle)
        perp_y = math.cos(actual_angle)
        guard_a = (hand_x + int(perp_x * 4), hand_y + int(perp_y * 4))
        guard_b = (hand_x - int(perp_x * 4), hand_y - int(perp_y * 4))

        # Blade polygon
        blade_side_x = -math.sin(actual_angle) * 2
        blade_side_y = math.cos(actual_angle) * 2

        blade_pts = [
            (hand_x + int(blade_side_x), hand_y + int(blade_side_y)),
            (tip_x + int(blade_side_x * 0.3), tip_y + int(blade_side_y * 0.3)),
            (tip_x, tip_y),
            (hand_x - int(blade_side_x), hand_y - int(blade_side_y)),
        ]
        # Shadow
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["shadow_deep"],
                           [(px + 2, py + 2) for px, py in blade_pts])
        # Blade
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["blade_dark"], blade_pts)
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["blade_mid"], [
            (hand_x + int(blade_side_x * 0.5), hand_y + int(blade_side_y * 0.5)),
            (tip_x + int(blade_side_x * 0.2), tip_y + int(blade_side_y * 0.2)),
            (tip_x, tip_y),
            (hand_x, hand_y),
        ])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["blade_light"], [
            (hand_x, hand_y),
            (tip_x, tip_y),
            (int((hand_x + tip_x) / 2), int((hand_y + tip_y) / 2)),
        ])
        # Bright edge
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["blade_shine"],
                             (hand_x, hand_y), (tip_x, tip_y), 1)
        # Tip
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["blade_edge"],
                         (tip_x, tip_y, 1, 1))
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["white"],
                         (tip_x, tip_y, 1, 1))

        # FLAME AURA on blade (always burning)
        flame_pulse = math.sin(phase * 3) * 0.2 + 0.8

        # Fire particles along blade
        num_flames = 5
        for i in range(1, num_flames + 1):
            flame_t = i / num_flames
            fx = int(hand_x + (tip_x - hand_x) * flame_t)
            fy = int(hand_y + (tip_y - hand_y) * flame_t)

            wobble = math.sin(phase * 4 + i) * 2
            flame_h = 4 + int(math.sin(phase * 2 + i) * 2)

            # Flame tongue pointing perpendicular to blade
            f_dir_x = perp_x
            f_dir_y = perp_y
            f_tip_x = fx + int(f_dir_x * flame_h + wobble)
            f_tip_y = fy + int(f_dir_y * flame_h)

            for r in range(3, 0, -1):
                alpha = _NS_kaithros._alpha(120 * (3 - r) / 3 * flame_pulse)
                _NS_kaithros._aacircle(surface,
                                       (*_NS_kaithros.PALETTE["fire_bright"], alpha),
                                       (fx, fy), r)

            # Flame tongue upward
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_darkest"], [
                (fx - int(perp_y * 1.5), fy + int(perp_x * 1.5)),
                (f_tip_x, f_tip_y),
                (fx + int(perp_y * 1.5), fy - int(perp_x * 1.5)),
            ])
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_deep"], [
                (fx - int(perp_y * 1), fy + int(perp_x * 1)),
                (f_tip_x, f_tip_y - 1),
                (fx + int(perp_y * 1), fy - int(perp_x * 1)),
            ])
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_bright"], [
                (fx, fy),
                (f_tip_x, f_tip_y - 2),
                (fx, fy),
            ])
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["fire_hot"],
                             (f_tip_x, f_tip_y - 2, 1, 1))
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["fire_shine"],
                             (f_tip_x, f_tip_y - 2, 1, 1))

        # Sparks along blade edge
        for i in range(3):
            sp_t = (phase * 0.8 + i * 0.35) % 1.0
            sp_x = int(hand_x + (tip_x - hand_x) * sp_t)
            sp_y = int(hand_y + (tip_y - hand_y) * sp_t)
            sp_off_x = int(perp_x * 4)
            sp_off_y = int(perp_y * 4)
            alpha = _NS_kaithros._alpha(240 * (1 - sp_t))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                             (sp_x + sp_off_x, sp_y + sp_off_y, 1, 1))

        # Bright tip glow
        for r in range(5, 0, -1):
            alpha = _NS_kaithros._alpha(150 * (5 - r) / 5 * flame_pulse)
            _NS_kaithros._aacircle(surface,
                                   (*_NS_kaithros.PALETTE["fire_bright"], alpha),
                                   (tip_x, tip_y), r)

        # GUARD (tsuba)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["guard_dark"],
                             guard_a, guard_b, 3)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["guard_mid"],
                             guard_a, guard_b, 1)
        pygame.draw.rect(surface, _NS_kaithros.PALETTE["guard_light"],
                         (hand_x, hand_y, 1, 1))

        # HILT (backward)
        back_x = hand_x - int(math.cos(actual_angle) * 6)
        back_y = hand_y - int(math.sin(actual_angle) * 6)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["hilt_dark"],
                             (hand_x, hand_y), (back_x, back_y), 4)
        _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["hilt_wrap"],
                             (hand_x, hand_y), (back_x, back_y), 2)

    # ============================================================
    # BASIC ATTACK — FLAME KATANA SLASH
    # ============================================================
    def _draw_katana_flame_slash(surface, boss, x, y, progress):
        """Flame arc during swing."""
        if progress < 0.35 or progress > 0.75:
            return

        facing = boss.direction
        if progress < 0.6:
            t = (progress - 0.35) / 0.25
        else:
            t = 1 - (progress - 0.6) / 0.15
        intensity = math.sin(t * math.pi)

        cx = x + facing * 20
        cy = y - 4

        arc_radius = int(30 + t * 8)
        segments = 20
        prev = None
        for i in range(segments + 1):
            seg_t = i / segments
            base_angle = -math.pi * 0.6 * facing
            seg_angle = base_angle + seg_t * math.pi * facing
            sx = cx + int(math.cos(seg_angle) * arc_radius)
            sy = cy + int(math.sin(seg_angle) * arc_radius * 0.7)

            if prev is not None and seg_t <= t * 1.2:
                fade = 1.0 - max(0, (t * 1.2 - seg_t) * 1.5)
                alpha_outer = _NS_kaithros._alpha(200 * intensity * fade)
                alpha_core = _NS_kaithros._alpha(255 * intensity * fade)

                # Multi-layer flame arc
                pygame.draw.line(surface,
                                 (*_NS_kaithros.PALETTE["fire_darkest"], alpha_outer),
                                 prev, (sx, sy), 8)
                pygame.draw.line(surface,
                                 (*_NS_kaithros.PALETTE["fire_deep"], alpha_outer),
                                 prev, (sx, sy), 6)
                pygame.draw.line(surface,
                                 (*_NS_kaithros.PALETTE["fire_mid"], alpha_core),
                                 prev, (sx, sy), 4)
                pygame.draw.line(surface,
                                 (*_NS_kaithros.PALETTE["fire_bright"], alpha_core),
                                 prev, (sx, sy), 2)
                pygame.draw.line(surface,
                                 (*_NS_kaithros.PALETTE["fire_hot"], alpha_core),
                                 prev, (sx, sy), 1)

                # Fire embers flying off
                if i % 3 == 0 and fade > 0.4:
                    for pi in range(3):
                        p_off_x = int(math.cos(seg_angle) * (pi + 1) * 3)
                        p_off_y = int(math.sin(seg_angle) * (pi + 1) * 3)
                        pygame.draw.rect(surface,
                                         (*_NS_kaithros.PALETTE["fire_hot"], alpha_core),
                                         (sx + p_off_x, sy + p_off_y, 2, 2))
                        pygame.draw.rect(surface,
                                         (*_NS_kaithros.PALETTE["fire_shine"], alpha_core),
                                         (sx + p_off_x, sy + p_off_y, 1, 1))

            prev = (sx, sy)

    # ============================================================
    # AMBIENT / GROUND
    # ============================================================
    def _draw_shadow(surface, x, y):
        shadow = pygame.Surface((130, 28), pygame.SRCALPHA)
        for radius in range(13, 0, -1):
            alpha = max(0, (13 - radius) * 16)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha),
                                (10 - radius, 14 - radius,
                                 110 + radius * 2, radius * 2))
        pygame.draw.ellipse(shadow, (3, 5, 2, 170), (5, 8, 120, 12))
        surface.blit(shadow, (x - 65, y - 14))

    def _draw_flame_aura(surface, x, y, phase):
        """Fire aura."""
        pulse = math.sin(phase * 0.7) * 0.3 + 0.7

        aura = pygame.Surface((220, 180), pygame.SRCALPHA)
        for radius in range(90, 5, -5):
            alpha = _NS_kaithros._alpha((90 - radius) * 1.0 * pulse)
            if alpha > 0:
                _NS_kaithros._aacircle(aura,
                                       (*_NS_kaithros.PALETTE["fire_dark"], alpha),
                                       (110, 90), radius)
        for radius in range(55, 5, -4):
            alpha = _NS_kaithros._alpha((55 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kaithros._aacircle(aura,
                                       (*_NS_kaithros.PALETTE["fire_deep"], alpha),
                                       (110, 90), radius)
        for radius in range(30, 5, -3):
            alpha = _NS_kaithros._alpha((30 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_kaithros._aacircle(aura,
                                       (*_NS_kaithros.PALETTE["fire_mid"], alpha),
                                       (110, 90), radius)
        surface.blit(aura, (x - 110, y - 90))

        # Rising embers
        for i in range(12):
            e_t = (phase * 0.5 + i * 0.08) % 1.0
            e_angle = i * math.pi / 6 + phase * 0.2
            e_r = 32 + int(math.sin(phase + i) * 10)
            sx = x + int(math.cos(e_angle) * e_r)
            sy = y + 5 - int(e_t * 45)
            alpha = _NS_kaithros._alpha(240 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_bright"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_shine"], alpha),
                             (sx, sy, 1, 1))

    def _draw_ground_ring(surface, x, y, phase, skill):
        """Fire ground ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((160, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (*_NS_kaithros.PALETTE["fire_darkest"], 200),
                            (5, 17, 150, 24), 3)
        pygame.draw.ellipse(ring, (*_NS_kaithros.PALETTE["fire_dark"], 220),
                            (14, 19, 132, 20), 2)
        pygame.draw.ellipse(ring, (*_NS_kaithros.PALETTE["fire_deep"], 200),
                            (25, 21, 110, 16), 1)

        for i in range(8):
            angle = phase * 0.3 + i * math.pi / 4
            x1 = 80 + int(math.cos(angle) * 42)
            y1 = 28 + int(math.sin(angle) * 7)
            x2 = 80 + int(math.cos(angle) * 68)
            y2 = 28 + int(math.sin(angle) * 11)
            pygame.draw.line(ring, (*_NS_kaithros.PALETTE["fire_bright"], 220),
                             (x1, y1), (x2, y2), 1)

        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_kaithros.PALETTE["fire_hot"],
                                 _NS_kaithros._alpha(180 * pulse)),
                                (15, 10, 130, 34), 1)
        surface.blit(ring, (x - 80, y - 25))

    # ============================================================
    # SKILL Q — UNKNOWING FIRE (swift horizontal slash)
    # ============================================================
    def _draw_unknowing_fire_fx(surface, boss, x, y, timer, phase):
        """Fast crescent flame wave forward."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Wave travels FAST forward
        travel_dist = int(240 * progress)
        wave_center_x = x + facing * (25 + travel_dist)
        wave_center_y = y - 4

        wave_w = 50
        wave_h = 55
        fade = 1.0 - progress * 0.3

        # Crescent arc points
        arc_points = []
        segments = 22
        for i in range(segments + 1):
            t = i / segments
            angle = -math.pi * 0.5 + t * math.pi
            ax = wave_center_x + int(math.cos(angle) * wave_w * 0.5) * facing
            ay = wave_center_y + int(math.sin(angle) * wave_h * 0.6)
            arc_points.append((ax, ay))

        # Multi-layer flame crescent
        for i in range(len(arc_points) - 1):
            alpha = _NS_kaithros._alpha(240 * fade)
            pygame.draw.line(surface,
                             (*_NS_kaithros.PALETTE["fire_darkest"], alpha),
                             arc_points[i], arc_points[i + 1], 12)
            pygame.draw.line(surface,
                             (*_NS_kaithros.PALETTE["fire_deep"], alpha),
                             arc_points[i], arc_points[i + 1], 8)
            pygame.draw.line(surface,
                             (*_NS_kaithros.PALETTE["fire_mid"], alpha),
                             arc_points[i], arc_points[i + 1], 5)
            pygame.draw.line(surface,
                             (*_NS_kaithros.PALETTE["fire_bright"], alpha),
                             arc_points[i], arc_points[i + 1], 3)
            pygame.draw.line(surface,
                             (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                             arc_points[i], arc_points[i + 1], 1)

        # Fire particles trailing
        for i in range(20):
            sp_angle = phase * 2 + i * math.pi / 10
            sp_r = 25 + int(math.sin(phase * 3 + i) * 10)
            dx = wave_center_x + int(math.cos(sp_angle) * sp_r) * facing
            dy = wave_center_y + int(math.sin(sp_angle) * sp_r * 0.6)
            alpha = _NS_kaithros._alpha(220 * fade)
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                             (dx, dy, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_shine"], alpha),
                             (dx, dy, 1, 1))

        # Trailing echoes behind wave
        for echo_i in range(3):
            echo_dist = travel_dist - (echo_i + 1) * 25
            if echo_dist < 0:
                break
            echo_x = x + facing * (25 + echo_dist)
            echo_alpha = _NS_kaithros._alpha(150 * fade * (1 - echo_i * 0.3))
            for i in range(0, segments, 2):
                t = i / segments
                angle = -math.pi * 0.5 + t * math.pi
                ax = echo_x + int(math.cos(angle) * wave_w * 0.4) * facing
                ay = wave_center_y + int(math.sin(angle) * wave_h * 0.5)
                pygame.draw.rect(surface,
                                 (*_NS_kaithros.PALETTE["fire_bright"], echo_alpha),
                                 (ax, ay, 2, 2))

    # ============================================================
    # SKILL W — RISING SUN (spinning flame vortex)
    # ============================================================
    def _draw_rising_sun_ground(surface, boss, x, y, timer, phase):
        """Ground fire ring."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(50 * min(1.0, progress * 3))

        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_kaithros.PALETTE["fire_darkest"], 220),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface,
                                (*_NS_kaithros.PALETTE["fire_dark"], 200),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)

    def _draw_rising_sun_fg(surface, boss, x, y, timer, phase):
        """Vertical spinning flame vortex around boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Vortex height
        vh = int(60 * min(1.0, progress * 2))
        # Vortex spinning speed
        spin = phase * 4

        # Draw spiraling flame arcs
        num_arms = 4
        for arm_i in range(num_arms):
            arm_offset = arm_i * math.pi * 2 / num_arms
            prev = None
            for step in range(40):
                t = step / 40
                spiral_angle = spin + arm_offset + t * math.pi * 4
                r = int(30 * (1 - t * 0.3))
                # 3D-ish: horizontal radius shrinks toward top
                sx = x + int(math.cos(spiral_angle) * r)
                sy = y + 30 - int(t * vh) + int(math.sin(spiral_angle) * r * 0.3)
                alpha = _NS_kaithros._alpha(230 * (1 - t * 0.4))

                if prev is not None:
                    pygame.draw.line(surface,
                                     (*_NS_kaithros.PALETTE["fire_darkest"], alpha),
                                     prev, (sx, sy), 6)
                    pygame.draw.line(surface,
                                     (*_NS_kaithros.PALETTE["fire_deep"], alpha),
                                     prev, (sx, sy), 4)
                    pygame.draw.line(surface,
                                     (*_NS_kaithros.PALETTE["fire_mid"], alpha),
                                     prev, (sx, sy), 3)
                    pygame.draw.line(surface,
                                     (*_NS_kaithros.PALETTE["fire_bright"], alpha),
                                     prev, (sx, sy), 2)
                    pygame.draw.line(surface,
                                     (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                                     prev, (sx, sy), 1)

                # Sparks at tip
                if step % 4 == 0:
                    pygame.draw.rect(surface,
                                     (*_NS_kaithros.PALETTE["fire_shine"], alpha),
                                     (sx, sy, 2, 2))
                prev = (sx, sy)

        # Central bright column
        for r in range(6, 0, -1):
            alpha = _NS_kaithros._alpha(150 * (6 - r) / 6)
            _NS_kaithros._aacircle(surface,
                                   (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                                   (x, y - 10), r)

        # Rising embers
        for i in range(12):
            e_t = (phase * 1.5 + i * 0.1) % 1.0
            ex = x + int(math.sin(phase * 2 + i) * 25)
            ey = y + 20 - int(e_t * vh + 20)
            alpha = _NS_kaithros._alpha(240 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_shine"], alpha),
                             (ex, ey, 1, 1))

    # ============================================================
    # SKILL E — BLAZING PILLAR (upward fire column)
    # ============================================================
    def _draw_pillar_ground(surface, boss, x, y, timer, phase):
        """Ground crack where pillar erupts."""
        tx, ty = _NS_kaithros._target_position(boss, x, y)
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))

        r = int(25 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface,
                                (*_NS_kaithros.PALETTE["fire_darkest"], 220),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface,
                                (*_NS_kaithros.PALETTE["fire_deep"], 200),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface,
                                (*_NS_kaithros.PALETTE["fire_bright"], 180),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))

    def _draw_pillar_fg(surface, boss, x, y, timer, phase):
        """Massive vertical fire pillar from ground."""
        tx, ty = _NS_kaithros._target_position(boss, x, y)
        duration = 65
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.15:
            # Wind-up: warning glow
            t = progress / 0.15
            warn_alpha = _NS_kaithros._alpha(180 * t)
            r = int(20 * t)
            _NS_kaithros._aacircle(surface,
                                   (*_NS_kaithros.PALETTE["fire_bright"], warn_alpha),
                                   (tx, ty), r)
        else:
            t = (progress - 0.15) / 0.85
            intensity = math.sin(min(1.0, t * 2) * math.pi * 0.7)

            # Pillar dimensions
            pillar_h = int(120 * intensity)
            pillar_w = 24

            # Draw pillar bottom to top
            layers = [
                (pillar_w, 100),
                (pillar_w - 6, 180),
                (pillar_w - 12, 220),
                (pillar_w - 18, 255),
            ]
            colors = [
                _NS_kaithros.PALETTE["fire_deep"],
                _NS_kaithros.PALETTE["fire_mid"],
                _NS_kaithros.PALETTE["fire_bright"],
                _NS_kaithros.PALETTE["fire_hot"],
            ]
            for (w, base_a), color in zip(layers, colors):
                actual_alpha = _NS_kaithros._alpha(base_a * intensity)
                pygame.draw.rect(surface, (*color, actual_alpha),
                                 (tx - w // 2, ty - pillar_h, w, pillar_h))

            # Flame licks/tongues rising along pillar edges
            for side in (-1, 1):
                for i in range(6):
                    lick_t = (phase * 2 + i * 0.15) % 1.0
                    lick_y = ty - int(lick_t * pillar_h)
                    lick_x = tx + side * (pillar_w // 2 + 2)
                    wobble = int(math.sin(phase * 3 + i) * 3)
                    tip_x = lick_x + side * (3 + wobble)
                    tip_y = lick_y - 6
                    _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_deep"], [
                        (lick_x, lick_y),
                        (tip_x, tip_y),
                        (lick_x + side, lick_y - 2),
                    ])
                    _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_bright"], [
                        (lick_x, lick_y),
                        (tip_x, tip_y),
                        (lick_x + side, lick_y - 1),
                    ])
                    pygame.draw.rect(surface, _NS_kaithros.PALETTE["fire_hot"],
                                     (tip_x, tip_y, 1, 1))

            # Bright top (flame explosion at pillar top)
            top_y = ty - pillar_h
            for r in range(15, 3, -2):
                alpha = _NS_kaithros._alpha(180 * (15 - r) / 15 * intensity)
                _NS_kaithros._aacircle(surface,
                                       (*_NS_kaithros.PALETTE["fire_bright"], alpha),
                                       (tx, top_y), r)
            _NS_kaithros._aacircle(surface, _NS_kaithros.PALETTE["fire_hot"],
                                   (tx, top_y), 4)
            _NS_kaithros._aacircle(surface, _NS_kaithros.PALETTE["fire_shine"],
                                   (tx, top_y), 2)

            # Rising sparks along pillar
            for i in range(15):
                sp_t = (phase * 3 + i * 0.12) % 1.0
                sp_y = ty - int(sp_t * pillar_h)
                sp_x = tx + int(math.sin(phase * 4 + i) * (pillar_w // 2))
                alpha = _NS_kaithros._alpha(240 * intensity * (1 - sp_t * 0.5))
                pygame.draw.rect(surface,
                                 (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                                 (sp_x, sp_y, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_kaithros.PALETTE["fire_shine"], alpha),
                                 (sp_x, sp_y, 1, 1))

            # Ground splash
            for i in range(12):
                spl_angle = i * math.pi / 6
                spl_r = int(15 + math.sin(phase * 5 + i) * 5)
                sx = tx + int(math.cos(spl_angle) * spl_r)
                sy = ty + int(math.sin(spl_angle) * spl_r * 0.4)
                alpha = _NS_kaithros._alpha(220 * intensity)
                pygame.draw.rect(surface,
                                 (*_NS_kaithros.PALETTE["fire_bright"], alpha),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                                 (sx, sy, 1, 1))

    # ============================================================
    # SKILL R — EMBERLION (fire tiger/lion charges forward)
    # ============================================================
    def _draw_emberlion_ground(surface, boss, x, y, timer, phase):
        """Fire trail on ground where lion has traveled."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        # Charge distance
        max_dist = 260
        current_dist = int(max_dist * min(1.0, progress * 1.5))

        # Draw fire trail on ground
        trail_start_x = x + facing * 20
        trail_end_x = x + facing * (20 + current_dist)
        ground_y = y + 45

        # Multiple layers of trail
        for i in range(current_dist // 10):
            seg_t = i * 10
            sx = trail_start_x + facing * seg_t
            seg_alpha = _NS_kaithros._alpha(200 * (1 - i * 10 / max(1, current_dist)))
            pygame.draw.ellipse(surface,
                                (*_NS_kaithros.PALETTE["fire_darkest"], seg_alpha),
                                (sx - 20, ground_y - 6, 40, 12))
            pygame.draw.ellipse(surface,
                                (*_NS_kaithros.PALETTE["fire_dark"], seg_alpha),
                                (sx - 18, ground_y - 5, 36, 10))
            pygame.draw.ellipse(surface,
                                (*_NS_kaithros.PALETTE["fire_deep"], seg_alpha),
                                (sx - 15, ground_y - 4, 30, 8))
            pygame.draw.ellipse(surface,
                                (*_NS_kaithros.PALETTE["fire_bright"], seg_alpha),
                                (sx - 10, ground_y - 3, 20, 6))

    def _draw_emberlion_fg(surface, boss, x, y, timer, phase):
        """Massive fire tiger/lion charges forward."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))

        if progress < 0.15:
            # Wind-up: fire gathering in front of boss
            t = progress / 0.15
            gather_x = x + facing * 30
            gather_y = y - 4
            r = int(10 + t * 15)
            for lr in range(r + 5, 0, -1):
                alpha = _NS_kaithros._alpha(150 * (r + 5 - lr) / (r + 5))
                _NS_kaithros._aacircle(surface,
                                       (*_NS_kaithros.PALETTE["fire_bright"], alpha),
                                       (gather_x, gather_y), lr)
        else:
            t = (progress - 0.15) / 0.85
            # Lion position (charges forward)
            lion_x = x + facing * (30 + int(t * 260))
            lion_y = y - 4

            _NS_kaithros._draw_fire_lion(surface, lion_x, lion_y, facing, phase, t)

            # Trailing embers behind lion
            for i in range(8):
                trail_t = max(0.0, t - i * 0.05)
                tx_pos = x + facing * (30 + int(trail_t * 260))
                ty_pos = y - 4 + int(math.sin(phase * 2 + i) * 4)
                alpha = _NS_kaithros._alpha(200 - i * 25)
                if alpha > 0:
                    _NS_kaithros._aacircle(surface,
                                           (*_NS_kaithros.PALETTE["fire_deep"], alpha),
                                           (tx_pos, ty_pos), 8)
                    _NS_kaithros._aacircle(surface,
                                           (*_NS_kaithros.PALETTE["fire_bright"], alpha),
                                           (tx_pos, ty_pos), 5)
                    _NS_kaithros._aacircle(surface,
                                           (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                                           (tx_pos, ty_pos), 2)

    def _draw_fire_lion(surface, cx, cy, facing, phase, t):
        """A crouching lion/tiger made entirely of flame."""
        # Body dimensions
        body_w = 60
        body_h = 30

        # Body ellipse (crouching)
        body_pts = [
            (cx - body_w // 2 * facing, cy),
            (cx - body_w // 2 * facing + facing * 5, cy - body_h // 2),
            (cx - facing * 10, cy - body_h // 2 - 3),
            (cx + facing * 10, cy - body_h // 2 - 3),
            (cx + body_w // 2 * facing - facing * 5, cy - body_h // 2),
            (cx + body_w // 2 * facing, cy),
            (cx + body_w // 2 * facing - facing * 3, cy + body_h // 2 - 5),
            (cx + facing * 10, cy + body_h // 2),
            (cx - facing * 10, cy + body_h // 2),
            (cx - body_w // 2 * facing + facing * 3, cy + body_h // 2 - 5),
        ]
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_darkest"], body_pts)
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_dark"], [
            (px + facing * 2, py + 1) if i % 2 == 0 else (px, py)
            for i, (px, py) in enumerate(body_pts)
        ])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_deep"], [
            (cx - body_w // 2 * facing + facing * 3, cy - 2),
            (cx - facing * 8, cy - body_h // 2),
            (cx + facing * 8, cy - body_h // 2),
            (cx + body_w // 2 * facing - facing * 5, cy - 2),
            (cx + facing * 8, cy + body_h // 4),
            (cx - facing * 8, cy + body_h // 4),
        ])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_mid"], [
            (cx - facing * 15, cy - 5),
            (cx - facing * 5, cy - body_h // 2 + 3),
            (cx + facing * 5, cy - body_h // 2 + 3),
            (cx + facing * 15, cy - 5),
            (cx + facing * 5, cy + body_h // 6),
            (cx - facing * 5, cy + body_h // 6),
        ])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_bright"], [
            (cx - facing * 8, cy - 4),
            (cx, cy - body_h // 3),
            (cx + facing * 8, cy - 4),
            (cx, cy + 4),
        ])

        # HEAD (front of body)
        head_x = cx + body_w // 2 * facing - facing * 2
        head_y = cy - 8
        head_r = 15

        # Head shape
        _NS_kaithros._aacircle(surface, _NS_kaithros.PALETTE["fire_darkest"],
                               (head_x, head_y), head_r + 2)
        _NS_kaithros._aacircle(surface, _NS_kaithros.PALETTE["fire_dark"],
                               (head_x, head_y), head_r)
        _NS_kaithros._aacircle(surface, _NS_kaithros.PALETTE["fire_deep"],
                               (head_x, head_y), head_r - 2)
        _NS_kaithros._aacircle(surface, _NS_kaithros.PALETTE["fire_mid"],
                               (head_x, head_y), head_r - 5)

        # MANE around head (flames radiating)
        for i in range(12):
            m_angle = i * math.pi / 6
            m_len = 8 + int(math.sin(phase * 2 + i) * 3)
            m_tip_x = head_x + int(math.cos(m_angle) * (head_r + m_len))
            m_tip_y = head_y + int(math.sin(m_angle) * (head_r + m_len))
            m_base_x = head_x + int(math.cos(m_angle) * head_r)
            m_base_y = head_y + int(math.sin(m_angle) * head_r)
            perp_x = -math.sin(m_angle)
            perp_y = math.cos(m_angle)
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_darkest"], [
                (m_base_x + int(perp_x * 2), m_base_y + int(perp_y * 2)),
                (m_tip_x, m_tip_y),
                (m_base_x - int(perp_x * 2), m_base_y - int(perp_y * 2)),
            ])
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_deep"], [
                (m_base_x + int(perp_x * 1.5), m_base_y + int(perp_y * 1.5)),
                (m_tip_x, m_tip_y),
                (m_base_x - int(perp_x * 1.5), m_base_y - int(perp_y * 1.5)),
            ])
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_bright"], [
                (m_base_x, m_base_y),
                (m_tip_x, m_tip_y),
                (m_base_x, m_base_y),
            ])
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["fire_hot"],
                             (m_tip_x, m_tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["fire_shine"],
                             (m_tip_x, m_tip_y, 1, 1))

        # EYES (glowing white)
        for eye_off_y in (-3, -3):
            for eye_off_x_side in (-1, 1):
                ex = head_x + facing * (2 + eye_off_x_side * 2)
                ey = head_y - 3
                for r in range(3, 0, -1):
                    alpha = _NS_kaithros._alpha(200 * (3 - r) / 3)
                    _NS_kaithros._aacircle(surface,
                                           (*_NS_kaithros.PALETTE["fire_shine"], alpha),
                                           (ex, ey), r)
                pygame.draw.rect(surface, _NS_kaithros.PALETTE["white"],
                                 (ex, ey, 1, 1))

        # MOUTH (open with teeth)
        chomp = abs(math.sin(phase * 3)) * 4 + 3
        mouth_top_y = head_y + 2
        mouth_bot_y = head_y + 2 + int(chomp)
        mouth_x1 = head_x + facing * 4
        mouth_x2 = head_x + facing * 12

        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["shadow_deep"], [
            (mouth_x1, mouth_top_y),
            (mouth_x2, mouth_top_y),
            (mouth_x2 - facing * 2, mouth_bot_y),
            (mouth_x1 + facing * 1, mouth_bot_y),
        ])
        _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_darkest"], [
            (mouth_x1 + facing * 1, mouth_top_y + 1),
            (mouth_x2 - facing * 1, mouth_top_y + 1),
            (mouth_x2 - facing * 3, mouth_bot_y - 1),
            (mouth_x1 + facing * 2, mouth_bot_y - 1),
        ])

        # Teeth (upper row)
        for tooth_i in range(3):
            tt = tooth_i / 2
            tx = int(mouth_x1 + (mouth_x2 - mouth_x1) * tt)
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_hot"], [
                (tx - 1, mouth_top_y),
                (tx, mouth_top_y + 3),
                (tx + 1, mouth_top_y),
            ])
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_shine"], [
                (tx - 1, mouth_top_y),
                (tx, mouth_top_y + 2),
                (tx + 1, mouth_top_y),
            ])

        # LEGS (running gesture - 4 legs)
        leg_dance = math.sin(phase * 5) * 5
        for leg_i, (lx_off, is_front) in enumerate([
            (-body_w // 2 * facing + facing * 6, False),   # back
            (-body_w // 2 * facing + facing * 12, False),  # back-mid
            (facing * 4, True),   # front-mid
            (facing * 14, True),  # front
        ]):
            leg_x = cx + lx_off
            leg_y_top = cy + body_h // 2 - 5
            # Alternate leg positions for running
            phase_off = leg_dance * (1 if leg_i % 2 == 0 else -1)
            leg_y_bot = leg_y_top + 18 + int(phase_off * 0.4)

            _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["fire_darkest"],
                                 (leg_x, leg_y_top), (leg_x, leg_y_bot), 6)
            _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["fire_deep"],
                                 (leg_x, leg_y_top), (leg_x, leg_y_bot), 4)
            _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["fire_bright"],
                                 (leg_x, leg_y_top), (leg_x, leg_y_bot), 2)
            # Paw
            pygame.draw.ellipse(surface, _NS_kaithros.PALETTE["fire_hot"],
                                (leg_x - 3, leg_y_bot, 6, 3))

        # TAIL (long flaming tail curving back)
        tail_base_x = cx - body_w // 2 * facing
        tail_base_y = cy - 5
        tail_wave = math.sin(phase * 3) * 8
        tail_end_x = tail_base_x - facing * 25
        tail_end_y = tail_base_y - 20 + int(tail_wave)

        # Bezier-like tail curve
        segs = 6
        prev = (tail_base_x, tail_base_y)
        for i in range(1, segs + 1):
            tt = i / segs
            mid_x = tail_base_x - facing * 12
            mid_y = tail_base_y - 15 + int(tail_wave * 0.5)
            bx = int((1 - tt) ** 2 * tail_base_x + 2 * (1 - tt) * tt * mid_x
                     + tt ** 2 * tail_end_x)
            by = int((1 - tt) ** 2 * tail_base_y + 2 * (1 - tt) * tt * mid_y
                     + tt ** 2 * tail_end_y)
            thickness = max(2, 8 - i)
            _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["fire_darkest"],
                                 prev, (bx, by), thickness + 1)
            _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["fire_deep"],
                                 prev, (bx, by), thickness)
            _NS_kaithros._aaline(surface, _NS_kaithros.PALETTE["fire_bright"],
                                 prev, (bx, by), max(1, thickness - 2))
            prev = (bx, by)

        # Tail tuft (flame at end)
        for i in range(4):
            tuft_angle = math.pi / 2 + i * math.pi / 4 - math.pi / 2
            tuft_x = tail_end_x + int(math.cos(tuft_angle) * 6)
            tuft_y = tail_end_y + int(math.sin(tuft_angle) * 6)
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_darkest"], [
                (tail_end_x, tail_end_y),
                (tuft_x, tuft_y),
                (tail_end_x + int(math.cos(tuft_angle + 0.3) * 3),
                 tail_end_y + int(math.sin(tuft_angle + 0.3) * 3)),
            ])
            _NS_kaithros._poly(surface, _NS_kaithros.PALETTE["fire_bright"], [
                (tail_end_x, tail_end_y),
                (tuft_x, tuft_y),
                (tail_end_x, tail_end_y),
            ])
            pygame.draw.rect(surface, _NS_kaithros.PALETTE["fire_shine"],
                             (tuft_x, tuft_y, 1, 1))

        # Rising embers around whole lion
        for i in range(15):
            e_t = (phase * 1.2 + i * 0.08) % 1.0
            e_angle = i * math.pi / 7.5 + phase * 0.4
            e_r = 40 + int(math.sin(phase + i) * 12)
            ex = cx + int(math.cos(e_angle) * e_r)
            ey = cy - int(e_t * 30) + int(math.sin(e_angle) * e_r * 0.4)
            alpha = _NS_kaithros._alpha(230 * (1 - e_t))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_hot"], alpha),
                             (ex, ey, 2, 2))
            pygame.draw.rect(surface, (*_NS_kaithros.PALETTE["fire_shine"], alpha),
                             (ex, ey, 1, 1))


# ====================================================================
# ALIAS
# ====================================================================
draw_kaithros = _NS_kaithros.draw_kaithros


# ====================================================================================================
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ====================================================================================================
def draw_aurelian(surface, boss, x, y):
    """Entry point aurelian."""
    return _NS_aurelian.draw_aurelian(surface, boss, x, y)

def draw_morvath(surface, boss, x, y):
    """Entry point morvath."""
    return _NS_morvath.draw_morvath(surface, boss, x, y)

def draw_pyrhaan(surface, boss, x, y):
    """Entry point pyrhaan."""
    return _NS_pyrhaan.draw_pyrhaan(surface, boss, x, y)

def draw_kaithros(surface, boss, x, y):
    """Entry point kaithros."""
    return _NS_kaithros.draw_kaithros(surface, boss, x, y)
