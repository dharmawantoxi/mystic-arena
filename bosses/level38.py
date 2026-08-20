"""
bosses/level38.py - Semua boss Level 38

Berisi:
  - azkharion   (mini boss - MELEE ashen warlord)
  - thargoroth  (mini boss - MELEE primordial colossus)
  - zahkareth   (mini boss - MELEE golden tyrant)
  - kyrenzai    (TRUE BOSS - RANGED crimson devourer, kagune)

Tiap boss dibungkus kelas namespace `_NS_<nama>` supaya
PALETTE dan fungsi helper-nya TIDAK saling menimpa.

Catatan prefix state (atribut di object boss):
  - _az_ (azkharion), _th_ (thargoroth), _kn_ (kyrenzai) sudah unik.
  - _zk_ (zahkareth) di-rename -> _zkt_ (bentrok dengan zharakzuul
    level 33), termasuk atribut _last_x/_last_y.
  Nama fungsi namespace (_draw_*) TIDAK disentuh.

Penanda bundle: heroes/__init__.py tidak menebak fungsi draw_*
secara longgar kalau file berisi banyak boss.
"""

import math
import pygame

_IS_LEVEL_BUNDLE = True




# ====================================================================
# AZKHARION (ASHEN WARLORD) - Mini Boss
# ====================================================================

class _NS_azkharion:
    """Namespace azkharion - Ashen Warlord king boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Dark royal armor (deep purple-black)
        "armor_darkest": (8, 5, 15),
        "armor_dark": (25, 15, 40),
        "armor_mid": (55, 35, 80),
        "armor_light": (100, 75, 140),
        "armor_shine": (170, 145, 205),
        # Purple magic (main glow - blades, aura)
        "purple_darkest": (15, 5, 30),
        "purple_dark": (50, 15, 90),
        "purple_mid": (130, 45, 200),
        "purple_light": (200, 100, 245),
        "purple_hot": (230, 160, 255),
        "purple_shine": (245, 220, 255),
        # Gold ornaments (armor trim, crown)
        "gold_dark": (85, 60, 15),
        "gold_mid": (180, 140, 45),
        "gold_light": (240, 205, 100),
        "gold_shine": (255, 240, 180),
        # Skin (pale warrior)
        "skin_shadow": (95, 75, 85),
        "skin_dark": (160, 130, 130),
        "skin_mid": (215, 185, 175),
        "skin_light": (240, 215, 205),
        "skin_shine": (255, 240, 230),
        # Hair (silver-white flowing)
        "hair_darkest": (55, 55, 75),
        "hair_dark": (110, 110, 135),
        "hair_mid": (170, 170, 190),
        "hair_light": (220, 220, 235),
        "hair_shine": (250, 250, 255),
        # Blade metal (dark with purple energy)
        "blade_dark": (20, 15, 30),
        "blade_mid": (60, 45, 85),
        "blade_light": (120, 100, 165),
        "blade_shine": (200, 180, 235),
        # Eye (purple/violet glowing)
        "eye_socket": (5, 3, 15),
        "eye_dark": (50, 15, 90),
        "eye_mid": (170, 60, 230),
        "eye_light": (220, 150, 250),
        "eye_glow": (240, 220, 255),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 5),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_azkharion._clamp(color)
        if _NS_azkharion.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_azkharion._clamp(color)
        if _NS_azkharion.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_azkharion._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_azkharion(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_azkharion._detect_moving(boss)
        _NS_azkharion._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_az_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_azkharion._draw_royal_aura(surface, x, y, pulse)
        _NS_azkharion._draw_ground_sigil(surface, x, y + 48, pulse, active_skill)
        # Ground skill FX
        if active_skill == "q":
            _NS_azkharion._draw_crescent_dash_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_azkharion._draw_whirling_tempest_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_azkharion._draw_earthshatter_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_azkharion._draw_ashura_ascension_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (floating)
        if attacking:
            _NS_azkharion._draw_az_attack(surface, boss, x, y)
        elif moving:
            _NS_azkharion._draw_az_float_move(surface, boss, x, y)
        else:
            _NS_azkharion._draw_az_idle(surface, boss, x, y)
        # R skill: transformed aura overlay
        if active_skill == "r":
            _NS_azkharion._draw_ashura_overlay(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_azkharion._draw_crescent_dash_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_azkharion._draw_whirling_tempest_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_azkharion._draw_earthshatter_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_azkharion._draw_ashura_ascension_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_az_previous_timer", 0))
        active = bool(getattr(boss, "_az_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._az_attack_active = True
            boss._az_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._az_attack_frame = int(getattr(boss, "_az_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._az_attack_active = False
            boss._az_attack_frame = 0
            active = False
        boss._az_previous_timer = timer
        boss._az_attack_progress = (
            min(1.0, getattr(boss, "_az_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_az_last_x"):
            boss._az_last_x = boss.x
            boss._az_last_y = boss.y
            return False
        dx = abs(boss.x - boss._az_last_x)
        dy = abs(boss.y - boss._az_last_y)
        boss._az_last_x = boss.x
        boss._az_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_az_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_azkharion._draw_float_shadow(surface, x, y + 52, boss.pulse)
        _NS_azkharion._draw_purple_wisps(surface, x, y + 40, boss.pulse)
        _NS_azkharion._draw_az_body(surface, x, y + bob,
                                     boss.direction, boss.pulse, "idle")
    def _draw_az_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_azkharion._draw_float_shadow(surface, x + sway, y + 52, phase)
        _NS_azkharion._draw_purple_wisps(surface, x + sway, y + 40, phase,
                                          trail=True, facing=boss.direction)
        _NS_azkharion._draw_az_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "float")
    def _draw_az_attack(surface, boss, x, y):
        """Dual blade melee swing."""
        progress = getattr(boss, "_az_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind up → forward swing → recovery
        if progress < 0.35:
            t = progress / 0.35
            body_shift = -int(t * 4) * boss.direction
            lift = int(t * 4)
        elif progress < 0.65:
            t = (progress - 0.35) / 0.3
            body_shift = int((-4 + t * 14)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.65) / 0.35
            body_shift = int(10 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_azkharion._draw_float_shadow(surface, x + body_shift, y + 52, boss.pulse)
        _NS_azkharion._draw_purple_wisps(surface, x + body_shift, y + 40, boss.pulse,
                                          intense=True)
        _NS_azkharion._draw_az_body(surface, x + body_shift, y - lift + bob,
                                     boss.direction, boss.pulse, "attack", progress)
        # Crescent slash arc
        _NS_azkharion._draw_dual_blade_arc(surface, boss, x + body_shift,
                                            y - lift + bob, progress)
    # ============================================================
    # BODY - Ashura King (long coat, chest exposed, dual crescent lances, silver hair)
    # ============================================================
    def _draw_az_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Ashura King body: long coat, torso, dual lances, silver hair, crown."""
        # Long trailing coat/cape bottom
        _NS_azkharion._draw_royal_coat(surface, cx, cy + 6, facing, phase)
        # Long silver hair (behind)
        _NS_azkharion._draw_silver_hair(surface, cx, cy - 22, facing, phase)
        # Torso (bare chest visible under open coat)
        _NS_azkharion._draw_royal_torso(surface, cx, cy - 4, facing, phase)
        # Arms with DUAL crescent lances (one on each side)
        blade_swing = 0
        if action == "attack":
            if attack_progress < 0.35:
                blade_swing = -int(attack_progress / 0.35 * 8) * facing
            elif attack_progress < 0.65:
                t = (attack_progress - 0.35) / 0.3
                blade_swing = int((-8 + t * 20)) * facing
            else:
                t = (attack_progress - 0.65) / 0.35
                blade_swing = int(12 * (1 - t)) * facing
        _NS_azkharion._draw_dual_arms_lances(surface, cx, cy - 2, facing, phase,
                                              blade_swing, action, attack_progress)
        # Head with silver hair front, glowing eyes
        _NS_azkharion._draw_king_head(surface, cx, cy - 24, facing, phase, action)
    def _draw_royal_coat(surface, cx, cy, facing, phase):
        """Long flowing royal purple coat with gold trim."""
        wave1 = math.sin(phase * 0.6) * 3
        wave2 = math.sin(phase * 0.6 + 1.5) * 3
        # Main coat silhouette
        coat_pts = [
            (cx - 10, cy),
            (cx + 10, cy),
            (cx + 14, cy + 10),
            (cx + 18 + int(wave1), cy + 22),
            (cx + 22 + int(wave2), cy + 34),
            (cx + 18, cy + 44),
            (cx + 10, cy + 48),
            (cx - 10, cy + 48),
            (cx - 18, cy + 44),
            (cx - 22 + int(wave1), cy + 34),
            (cx - 18 + int(wave2), cy + 22),
            (cx - 14, cy + 10),
        ]
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in coat_pts])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_darkest"], coat_pts)
        # Second layer
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_dark"], [
            (cx - 9, cy + 2),
            (cx + 9, cy + 2),
            (cx + 12, cy + 12),
            (cx + 16 + int(wave1 * 0.7), cy + 24),
            (cx + 18 + int(wave2 * 0.7), cy + 34),
            (cx + 14, cy + 42),
            (cx - 14, cy + 42),
            (cx - 18 + int(wave1 * 0.7), cy + 34),
            (cx - 16 + int(wave2 * 0.7), cy + 24),
            (cx - 12, cy + 12),
        ])
        # Mid layer with more purple tint
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_mid"], [
            (cx - 7, cy + 4),
            (cx + 7, cy + 4),
            (cx + 10, cy + 16),
            (cx + 12, cy + 30),
            (cx + 6, cy + 40),
            (cx - 6, cy + 40),
            (cx - 12, cy + 30),
            (cx - 10, cy + 16),
        ])
        # Highlight
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_light"], [
            (cx - 3, cy + 6),
            (cx + 3, cy + 6),
            (cx + 4, cy + 24),
            (cx + 2, cy + 36),
            (cx - 2, cy + 36),
            (cx - 4, cy + 24),
        ])
        # Purple glowing veins running down coat
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for i, y_off in enumerate((8, 16, 24, 32, 40)):
            alpha = _NS_azkharion._alpha(200 * pulse)
            pygame.draw.line(surface, _NS_azkharion.PALETTE["purple_dark"],
                             (cx - 6, cy + y_off), (cx - 3, cy + y_off), 1)
            pygame.draw.line(surface, _NS_azkharion.PALETTE["purple_hot"],
                             (cx - 5, cy + y_off), (cx - 4, cy + y_off), 1)
            pygame.draw.line(surface, _NS_azkharion.PALETTE["purple_dark"],
                             (cx + 3, cy + y_off), (cx + 6, cy + y_off), 1)
            pygame.draw.line(surface, _NS_azkharion.PALETTE["purple_hot"],
                             (cx + 4, cy + y_off), (cx + 5, cy + y_off), 1)
        # Gold trim at bottom edges
        for rx in (-16, -8, 0, 8, 16):
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["gold_dark"],
                             (cx + rx - 1, cy + 44, 3, 2))
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["gold_light"],
                             (cx + rx, cy + 44, 1, 1))
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["gold_shine"],
                             (cx + rx, cy + 44, 1, 1))
        # Gold trim strip vertically (chest opening line)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["gold_dark"],
                         (cx - 2, cy + 2), (cx - 2, cy + 20), 1)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["gold_mid"],
                         (cx + 2, cy + 2), (cx + 2, cy + 20), 1)
        # Purple particles rising from coat
        for i in range(6):
            spark_t = (phase * 0.5 + i * 0.16) % 1.0
            sx = cx - 10 + int((i % 3) * 10) + int(math.sin(phase + i) * 2)
            sy = cy + 14 + int(spark_t * 32)
            alpha = _NS_azkharion._alpha(220 * (1 - spark_t))
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["purple_hot"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["purple_shine"], (sx, sy, 1, 1))
    def _draw_royal_torso(surface, cx, cy, facing, phase):
        """Bare muscular chest with open royal coat (Martis-style)."""
        # Torso base (V-shape muscular)
        torso_pts = [
            (cx - 10, cy - 6),
            (cx + 10, cy - 6),
            (cx + 12, cy),
            (cx + 10, cy + 6),
            (cx + 8, cy + 10),
            (cx - 8, cy + 10),
            (cx - 10, cy + 6),
            (cx - 12, cy),
        ]
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_pts])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_darkest"], torso_pts)
        # Coat sides (armor around torso, but chest exposed in middle)
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_dark"], [
            (cx - 10, cy - 5),
            (cx - 5, cy - 5),
            (cx - 5, cy + 9),
            (cx - 10, cy + 5),
            (cx - 11, cy),
        ])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_dark"], [
            (cx + 10, cy - 5),
            (cx + 5, cy - 5),
            (cx + 5, cy + 9),
            (cx + 10, cy + 5),
            (cx + 11, cy),
        ])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_mid"], [
            (cx - 9, cy - 4),
            (cx - 5, cy - 4),
            (cx - 5, cy + 8),
            (cx - 9, cy + 4),
        ])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_mid"], [
            (cx + 9, cy - 4),
            (cx + 5, cy - 4),
            (cx + 5, cy + 8),
            (cx + 9, cy + 4),
        ])
        # Exposed chest skin (V-cut in middle)
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["skin_shadow"], [
            (cx - 5, cy - 5),
            (cx + 5, cy - 5),
            (cx + 5, cy + 2),
            (cx, cy + 8),
            (cx - 5, cy + 2),
        ])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["skin_dark"], [
            (cx - 4, cy - 4),
            (cx + 4, cy - 4),
            (cx + 4, cy + 2),
            (cx, cy + 6),
            (cx - 4, cy + 2),
        ])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["skin_mid"], [
            (cx - 3, cy - 3),
            (cx + 3, cy - 3),
            (cx + 3, cy + 1),
            (cx, cy + 4),
            (cx - 3, cy + 1),
        ])
        # Muscle definition
        # Pec split
        pygame.draw.line(surface, _NS_azkharion.PALETTE["skin_shadow"],
                         (cx, cy - 4), (cx, cy + 4), 1)
        # Pec highlights
        pygame.draw.line(surface, _NS_azkharion.PALETTE["skin_light"],
                         (cx - 3, cy - 3), (cx - 2, cy - 1), 1)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["skin_light"],
                         (cx + 2, cy - 3), (cx + 3, cy - 1), 1)
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["skin_shine"],
                         (cx - 2, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["skin_shine"],
                         (cx + 2, cy - 3, 1, 1))
        # Gold trim on coat edges (chest opening)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["gold_dark"],
                         (cx - 5, cy - 5), (cx - 5, cy + 9), 1)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["gold_dark"],
                         (cx + 5, cy - 5), (cx + 5, cy + 9), 1)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["gold_mid"],
                         (cx - 4, cy - 5), (cx - 4, cy + 5), 1)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["gold_light"],
                         (cx + 4, cy - 5), (cx + 4, cy + 5), 1)
        # Chest gem (purple crystal at center of chest)
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_azkharion._alpha(150 * (4 - r) / 4 * pulse)
            _NS_azkharion._aacircle(surface,
                                    (*_NS_azkharion.PALETTE["purple_light"], alpha),
                                    (cx, cy + 2), r)
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["armor_darkest"],
                         (cx - 1, cy + 1, 2, 3))
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["purple_dark"],
                         (cx - 1, cy + 1, 2, 2))
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["purple_hot"],
                         (cx, cy + 2, 1, 1))
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["purple_shine"],
                         (cx, cy + 2, 1, 1))
        # Shoulder pauldrons (massive spiked, both sides)
        for side in (-1, 1):
            # Base pauldron
            _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["shadow_deep"], [
                (cx + side * 9, cy - 7),
                (cx + side * 16, cy - 6),
                (cx + side * 17, cy),
                (cx + side * 13, cy + 3),
                (cx + side * 9, cy),
            ])
            _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_darkest"], [
                (cx + side * 9, cy - 8),
                (cx + side * 15, cy - 7),
                (cx + side * 16, cy),
                (cx + side * 12, cy + 2),
                (cx + side * 9, cy - 1),
            ])
            _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_dark"], [
                (cx + side * 10, cy - 7),
                (cx + side * 14, cy - 6),
                (cx + side * 15, cy - 1),
                (cx + side * 11, cy + 1),
            ])
            _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_mid"], [
                (cx + side * 11, cy - 6),
                (cx + side * 13, cy - 5),
                (cx + side * 14, cy - 2),
                (cx + side * 12, cy - 1),
            ])
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["armor_light"],
                             (cx + side * 12, cy - 5, 2, 1))
            # Gold trim on pauldron
            pygame.draw.line(surface, _NS_azkharion.PALETTE["gold_dark"],
                             (cx + side * 10, cy - 7),
                             (cx + side * 14, cy - 7), 1)
            pygame.draw.line(surface, _NS_azkharion.PALETTE["gold_light"],
                             (cx + side * 11, cy - 7),
                             (cx + side * 13, cy - 7), 1)
            # Multiple spikes on pauldron
            for spike_config in [(11, -9, 5), (14, -7, 4)]:
                sp_off_x, sp_off_y, sp_h = spike_config
                sp_x = cx + side * sp_off_x
                sp_y = cy + sp_off_y
                sp_tip_y = sp_y - sp_h
                _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["shadow_deep"], [
                    (sp_x + 1, sp_tip_y + 1),
                    (sp_x - 2 + 1, sp_y + 1),
                    (sp_x + 2 + 1, sp_y + 1),
                ])
                _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_darkest"], [
                    (sp_x, sp_tip_y),
                    (sp_x - 2, sp_y),
                    (sp_x + 2, sp_y),
                ])
                _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["armor_dark"], [
                    (sp_x, sp_tip_y + 1),
                    (sp_x - 1, sp_y),
                    (sp_x + 1, sp_y),
                ])
                # Purple glow at tip
                pygame.draw.rect(surface, _NS_azkharion.PALETTE["purple_hot"],
                                 (sp_x, sp_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_azkharion.PALETTE["purple_shine"],
                                 (sp_x, sp_tip_y, 1, 1))
    def _draw_dual_arms_lances(surface, cx, cy, facing, phase, swing, action,
                                attack_progress):
        """Both arms holding crescent lances."""
        wave = math.sin(phase * 0.7) * 1
        # BACK ARM (drawn first, behind body)
        # In idle: lance held back-down
        # In attack: swings forward
        back_shoulder_x = cx - facing * 8
        back_shoulder_y = cy - 2
        if action == "attack":
            # Back hand comes forward
            back_hand_x = cx + facing * (2 + swing // 3)
            back_hand_y = cy + 8 + int(wave)
        else:
            # Back hand rests behind
            back_hand_x = cx - facing * 10
            back_hand_y = cy + 8 + int(wave)
        back_elbow_x = (back_shoulder_x + back_hand_x) // 2
        back_elbow_y = (back_shoulder_y + back_hand_y) // 2 + 2
        # Draw back arm (armored)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["shadow_deep"],
                              (back_shoulder_x + 1, back_shoulder_y + 1),
                              (back_elbow_x + 1, back_elbow_y + 1), 5)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["armor_darkest"],
                              (back_shoulder_x, back_shoulder_y),
                              (back_elbow_x, back_elbow_y), 4)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["armor_dark"],
                              (back_shoulder_x, back_shoulder_y),
                              (back_elbow_x, back_elbow_y), 3)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["armor_mid"],
                              (back_shoulder_x, back_shoulder_y - 1),
                              (back_elbow_x, back_elbow_y - 1), 2)
        # Elbow guard (gold)
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["gold_dark"],
                         (back_elbow_x - 2, back_elbow_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["gold_mid"],
                         (back_elbow_x - 2, back_elbow_y - 1, 4, 2))
        # Back forearm
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["shadow_deep"],
                              (back_elbow_x + 1, back_elbow_y + 1),
                              (back_hand_x + 1, back_hand_y + 1), 5)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["armor_darkest"],
                              (back_elbow_x, back_elbow_y),
                              (back_hand_x, back_hand_y), 4)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["armor_dark"],
                              (back_elbow_x, back_elbow_y),
                              (back_hand_x, back_hand_y), 3)
        # Back hand
        _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["armor_darkest"],
                                (back_hand_x, back_hand_y), 3)
        _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["armor_dark"],
                                (back_hand_x, back_hand_y), 2)
        # Draw BACK LANCE (points down-back in idle, sweeps forward in attack)
        back_lance_angle = math.pi * 0.35 if action != "attack" else \
            math.pi * (0.35 - attack_progress * 0.7)
        _NS_azkharion._draw_crescent_lance(surface, back_hand_x, back_hand_y, facing,
                                            phase, back_lance_angle, is_back=True)
        # FRONT ARM
        front_shoulder_x = cx + facing * 10
        front_shoulder_y = cy - 2
        if action == "attack":
            # Front hand extends forward-down during swing
            front_hand_x = cx + facing * (16 + swing)
            front_hand_y = cy + 4 + int(wave)
        else:
            front_hand_x = cx + facing * 16
            front_hand_y = cy + 6 + int(wave)
        front_elbow_x = (front_shoulder_x + front_hand_x) // 2 + facing
        front_elbow_y = (front_shoulder_y + front_hand_y) // 2 + 2
        # Front arm (armored)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["shadow_deep"],
                              (front_shoulder_x + 1, front_shoulder_y + 1),
                              (front_elbow_x + 1, front_elbow_y + 1), 5)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["armor_darkest"],
                              (front_shoulder_x, front_shoulder_y),
                              (front_elbow_x, front_elbow_y), 4)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["armor_dark"],
                              (front_shoulder_x, front_shoulder_y),
                              (front_elbow_x, front_elbow_y), 3)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["armor_mid"],
                              (front_shoulder_x, front_shoulder_y - 1),
                              (front_elbow_x, front_elbow_y - 1), 2)
        # Elbow guard
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["gold_dark"],
                         (front_elbow_x - 2, front_elbow_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["gold_mid"],
                         (front_elbow_x - 2, front_elbow_y - 1, 4, 2))
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["gold_light"],
                         (front_elbow_x - 1, front_elbow_y - 1, 2, 1))
        # Front forearm
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["shadow_deep"],
                              (front_elbow_x + 1, front_elbow_y + 1),
                              (front_hand_x + 1, front_hand_y + 1), 5)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["armor_darkest"],
                              (front_elbow_x, front_elbow_y),
                              (front_hand_x, front_hand_y), 4)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["armor_dark"],
                              (front_elbow_x, front_elbow_y),
                              (front_hand_x, front_hand_y), 3)
        # Front hand
        _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["armor_darkest"],
                                (front_hand_x, front_hand_y), 3)
        _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["armor_dark"],
                                (front_hand_x, front_hand_y), 2)
        # FRONT LANCE (points forward-down in idle, extends during swing)
        front_lance_angle = -math.pi * 0.15 if action != "attack" else \
            -math.pi * (0.15 + attack_progress * 0.4)
        _NS_azkharion._draw_crescent_lance(surface, front_hand_x, front_hand_y, facing,
                                            phase, front_lance_angle, is_back=False)
    def _draw_crescent_lance(surface, hand_x, hand_y, facing, phase, angle_offset,
                              is_back=False):
        """Crescent-shaped purple lance/blade (Martis-style dual weapons).
        angle_offset: rotation from horizontal (0 = forward horizontal)
                      negative = up, positive = down
        """
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        # Base direction (facing forward)
        if facing == 1:
            base_angle = 0 + angle_offset  # forward
        else:
            base_angle = math.pi - angle_offset  # backward (mirror)
        # Lance length
        lance_len = 36
        # Direction vectors
        dx = math.cos(base_angle)
        dy = math.sin(base_angle)
        perp_x = -math.sin(base_angle)
        perp_y = math.cos(base_angle)
        # Lance handle (short - from hand outward)
        handle_len = 6
        handle_end_x = hand_x + int(dx * handle_len)
        handle_end_y = hand_y + int(dy * handle_len)
        # Handle
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["shadow_deep"],
                              (hand_x + 1, hand_y + 1),
                              (handle_end_x + 1, handle_end_y + 1), 4)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["armor_darkest"],
                              (hand_x, hand_y),
                              (handle_end_x, handle_end_y), 3)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["gold_dark"],
                              (hand_x, hand_y),
                              (handle_end_x, handle_end_y), 2)
        _NS_azkharion._aaline(surface, _NS_azkharion.PALETTE["gold_mid"],
                              (hand_x, hand_y - 1),
                              (handle_end_x, handle_end_y - 1), 1)
        # Guard (crossguard)
        guard_a_x = handle_end_x + int(perp_x * 4)
        guard_a_y = handle_end_y + int(perp_y * 4)
        guard_b_x = handle_end_x - int(perp_x * 4)
        guard_b_y = handle_end_y - int(perp_y * 4)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["shadow_deep"],
                         (guard_a_x + 1, guard_a_y + 1),
                         (guard_b_x + 1, guard_b_y + 1), 3)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["gold_dark"],
                         (guard_a_x, guard_a_y),
                         (guard_b_x, guard_b_y), 3)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["gold_mid"],
                         (guard_a_x, guard_a_y),
                         (guard_b_x, guard_b_y), 2)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["gold_light"],
                         (guard_a_x, guard_a_y),
                         (guard_b_x, guard_b_y), 1)
        # CRESCENT BLADE (curves outward from handle end)
        # Blade curves like a moon/scimitar
        curve_dir = 1 if not is_back else -1  # opposite curves for symmetry
        # Generate curve points
        blade_outer_points = []
        blade_inner_points = []
        num_segs = 10
        curve_amount = 20  # how much the blade curves perpendicular
        blade_extend = lance_len - handle_len  # how far blade extends
        for seg in range(num_segs + 1):
            seg_t = seg / num_segs
            # Parametric position
            # Along axis (forward)
            along = seg_t * blade_extend
            # Perpendicular offset (curve using sin)
            perp_amt = math.sin(seg_t * math.pi) * curve_amount * curve_dir
            base_x = handle_end_x + int(dx * along + perp_x * perp_amt)
            base_y = handle_end_y + int(dy * along + perp_y * perp_amt)
            blade_outer_points.append((base_x, base_y))
            # Inner edge (offset by blade width)
            width_here = 4 * math.sin(seg_t * math.pi) + 1  # thickest at middle
            inner_x = base_x - int(perp_x * width_here * curve_dir)
            inner_y = base_y - int(perp_y * width_here * curve_dir)
            blade_inner_points.append((inner_x, inner_y))
        # Draw blade as filled polygon
        blade_poly = blade_outer_points + list(reversed(blade_inner_points))
        # Shadow
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["shadow_deep"],
                            [(p[0] + 2, p[1] + 2) for p in blade_poly])
        # Base
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["blade_dark"], blade_poly)
        # Mid tone (slightly narrower)
        mid_outer = blade_outer_points[1:-1]
        mid_inner = blade_inner_points[1:-1]
        if len(mid_outer) >= 2:
            _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["blade_mid"],
                                mid_outer + list(reversed(mid_inner)))
        # GLOWING PURPLE OUTER EDGE (crescent's sharp side)
        for i in range(len(blade_outer_points) - 1):
            pygame.draw.line(surface, _NS_azkharion.PALETTE["purple_darkest"],
                             blade_outer_points[i], blade_outer_points[i + 1], 3)
            pygame.draw.line(surface, _NS_azkharion.PALETTE["purple_dark"],
                             blade_outer_points[i], blade_outer_points[i + 1], 2)
            pygame.draw.line(surface, _NS_azkharion.PALETTE["purple_mid"],
                             blade_outer_points[i], blade_outer_points[i + 1], 1)
        # HOT PURPLE inner glow line
        pygame.draw.line(surface, _NS_azkharion.PALETTE["purple_hot"],
                         blade_outer_points[len(blade_outer_points) // 3],
                         blade_outer_points[-2], 1)
        # Sharp tip (bright)
        if blade_outer_points:
            tip = blade_outer_points[-1]
            for r in range(4, 0, -1):
                alpha = _NS_azkharion._alpha(200 * (4 - r) / 4 * pulse)
                _NS_azkharion._aacircle(surface,
                                        (*_NS_azkharion.PALETTE["purple_hot"], alpha),
                                        tip, r)
            _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["purple_shine"],
                                    tip, 1)
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["white"], (tip[0], tip[1], 1, 1))
        # Base connector (where blade meets handle)
        _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["shadow_deep"],
                                (handle_end_x + 1, handle_end_y + 1), 3)
        _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["gold_dark"],
                                (handle_end_x, handle_end_y), 3)
        _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["gold_mid"],
                                (handle_end_x, handle_end_y), 2)
        # Purple gem at connector
        for r in range(3, 0, -1):
            alpha = _NS_azkharion._alpha(160 * (3 - r) / 3 * pulse)
            _NS_azkharion._aacircle(surface,
                                    (*_NS_azkharion.PALETTE["purple_light"], alpha),
                                    (handle_end_x, handle_end_y), r)
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["purple_hot"],
                         (handle_end_x, handle_end_y, 1, 1))
        # Energy sparks along blade
        for i in range(3):
            spark_t = (phase + i * 0.4) % 1.0
            idx = int(spark_t * (len(blade_outer_points) - 1))
            if idx < len(blade_outer_points):
                bp = blade_outer_points[idx]
                sx = bp[0] + int(math.sin(phase * 4 + i) * 3)
                sy = bp[1] + int(math.cos(phase * 4 + i) * 3)
                alpha_sp = _NS_azkharion._alpha(230 * (1 - spark_t))
                pygame.draw.rect(surface,
                                 (*_NS_azkharion.PALETTE["purple_shine"], alpha_sp),
                                 (sx, sy, 1, 1))
    def _draw_silver_hair(surface, cx, cy, facing, phase):
        """Long flowing silver-white hair behind body."""
        wave1 = math.sin(phase * 0.6) * 3
        wave2 = math.sin(phase * 0.6 + 1.5) * 3
        # Hair mass behind head (long flowing)
        hair_pts = [
            (cx - 8, cy),
            (cx + 8, cy),
            (cx + 12, cy + 8),
            (cx + 14 + int(wave1), cy + 20),
            (cx + 12 + int(wave2), cy + 32),
            (cx + 6, cy + 40),
            (cx - 6, cy + 40),
            (cx - 12 + int(wave2), cy + 32),
            (cx - 14 + int(wave1), cy + 20),
            (cx - 12, cy + 8),
        ]
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in hair_pts])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["hair_darkest"], hair_pts)
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["hair_dark"], [
            (cx - 7, cy + 2),
            (cx + 7, cy + 2),
            (cx + 10, cy + 10),
            (cx + 11 + int(wave1 * 0.7), cy + 22),
            (cx + 9, cy + 32),
            (cx - 9, cy + 32),
            (cx - 11 + int(wave1 * 0.7), cy + 22),
            (cx - 10, cy + 10),
        ])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["hair_mid"], [
            (cx - 5, cy + 4),
            (cx + 5, cy + 4),
            (cx + 7, cy + 14),
            (cx + 6, cy + 26),
            (cx - 6, cy + 26),
            (cx - 7, cy + 14),
        ])
        # Hair strand highlights
        for i, x_off in enumerate((-6, -2, 4)):
            strand_x = cx + x_off + int(math.sin(phase * 0.7 + i) * 2)
            pygame.draw.line(surface, _NS_azkharion.PALETTE["hair_light"],
                             (strand_x, cy + 6),
                             (strand_x + int(math.sin(phase + i)), cy + 28), 1)
        # Bright shine strands
        pygame.draw.line(surface, _NS_azkharion.PALETTE["hair_shine"],
                         (cx, cy + 8), (cx, cy + 24), 1)
    def _draw_king_head(surface, cx, cy, facing, phase, action):
        """King head with silver bangs, glowing purple eyes."""
        # Face shape
        face_pts = [
            (cx - 5, cy - 4),
            (cx + 5, cy - 4),
            (cx + 6, cy),
            (cx + 5, cy + 4),
            (cx + 2, cy + 7),
            (cx - 2, cy + 7),
            (cx - 5, cy + 4),
            (cx - 6, cy),
        ]
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["shadow_deep"],
                            [(px + 1, py + 2) for px, py in face_pts])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["skin_shadow"], face_pts)
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["skin_dark"], [
            (cx - 4, cy - 4),
            (cx + 4, cy - 4),
            (cx + 5, cy),
            (cx + 4, cy + 3),
            (cx + 2, cy + 6),
            (cx - 2, cy + 6),
            (cx - 4, cy + 3),
            (cx - 5, cy),
        ])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["skin_mid"], [
            (cx - 3, cy - 3),
            (cx + 3, cy - 3),
            (cx + 4, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
            (cx - 4, cy),
        ])
        # Highlight
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["skin_light"],
                         (cx - 1, cy - 2, 3, 2))
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["skin_shine"],
                         (cx, cy - 2, 1, 1))
        # SILVER HAIR BANGS (falling in front, split down middle)
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["hair_darkest"], [
            (cx - 6, cy - 5),
            (cx + 6, cy - 5),
            (cx + 6, cy - 2),
            (cx + 3, cy),
            (cx - 3, cy),
            (cx - 6, cy - 2),
        ])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["hair_dark"], [
            (cx - 5, cy - 4),
            (cx + 5, cy - 4),
            (cx + 5, cy - 2),
            (cx + 2, cy - 1),
            (cx - 2, cy - 1),
            (cx - 5, cy - 2),
        ])
        _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["hair_mid"], [
            (cx - 4, cy - 3),
            (cx + 4, cy - 3),
            (cx + 4, cy - 2),
            (cx + 1, cy - 1),
            (cx - 1, cy - 1),
            (cx - 4, cy - 2),
        ])
        pygame.draw.line(surface, _NS_azkharion.PALETTE["hair_light"],
                         (cx - 3, cy - 3), (cx - 1, cy - 1), 1)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["hair_light"],
                         (cx + 1, cy - 3), (cx + 3, cy - 1), 1)
        pygame.draw.rect(surface, _NS_azkharion.PALETTE["hair_shine"],
                         (cx, cy - 3, 1, 1))
        # GLOWING PURPLE EYES
        _NS_azkharion._draw_purple_eyes(surface, cx, cy - 1, facing, phase)
        # Nose (subtle)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["skin_shadow"],
                         (cx, cy + 2), (cx, cy + 4), 1)
        # Lips (stern)
        pygame.draw.line(surface, _NS_azkharion.PALETTE["skin_shadow"],
                         (cx - 1, cy + 5), (cx + 1, cy + 5), 1)
    def _draw_purple_eyes(surface, cx, cy, facing, phase):
        """Two glowing purple eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy
            # Socket
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 2, 2))
            # Glow halo
            for r in range(5, 0, -1):
                alpha = _NS_azkharion._alpha(140 * (5 - r) / 5 * pulse)
                _NS_azkharion._aacircle(surface,
                                        (*_NS_azkharion.PALETTE["eye_mid"], alpha),
                                        (ex, ey), r)
            # Core
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["eye_dark"],
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["eye_mid"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))
    # ============================================================
    # MELEE DUAL BLADE ARC (both crescents swipe together)
    # ============================================================
    def _draw_dual_blade_arc(surface, boss, x, y, progress):
        """Two crescent arc trails from dual blades."""
        if progress < 0.35 or progress > 0.72:
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.37
        arc_cx = x + facing * 18
        arc_cy = y - 2
        arc_radius = 42
        # Two arcs (staggered slightly for dual-blade effect)
        for arc_i, (start_a, end_a, offset) in enumerate([
            (-math.pi * 0.55, math.pi * 0.55, -3),  # first blade arc (higher)
            (-math.pi * 0.45, math.pi * 0.65, 3),   # second blade arc (lower)
        ]):
            trail_length = 0.45
            start_seg_t = max(0.0, t - trail_length)
            end_seg_t = min(1.0, t)
            for layer_i, (thick, alpha_val, color) in enumerate([
                (6, 90, _NS_azkharion.PALETTE["purple_darkest"]),
                (5, 130, _NS_azkharion.PALETTE["purple_dark"]),
                (4, 180, _NS_azkharion.PALETTE["purple_mid"]),
                (3, 220, _NS_azkharion.PALETTE["purple_light"]),
                (2, 245, _NS_azkharion.PALETTE["purple_hot"]),
                (1, 255, _NS_azkharion.PALETTE["purple_shine"]),
            ]):
                arc_points = []
                num_segments = 22
                for seg in range(num_segments):
                    seg_t = start_seg_t + (end_seg_t - start_seg_t) * (seg / (num_segments - 1))
                    a = start_a + (end_a - start_a) * seg_t
                    ax = arc_cx + int(math.cos(a) * arc_radius * facing)
                    ay = arc_cy + int(math.sin(a) * arc_radius) + offset
                    arc_points.append((ax, ay))
                if len(arc_points) >= 2:
                    for i in range(len(arc_points) - 1):
                        fade = i / max(1, len(arc_points) - 1)
                        actual_alpha = _NS_azkharion._alpha(alpha_val * fade)
                        pygame.draw.line(surface, (*color, actual_alpha),
                                         arc_points[i], arc_points[i + 1], thick)
            # Bright tip at leading edge
            if 0.05 < t < 0.95:
                tip_a = start_a + (end_a - start_a) * t
                tip_x_arc = arc_cx + int(math.cos(tip_a) * arc_radius * facing)
                tip_y_arc = arc_cy + int(math.sin(tip_a) * arc_radius) + offset
                for r in range(8, 0, -1):
                    alpha = _NS_azkharion._alpha(220 * (8 - r) / 8)
                    _NS_azkharion._aacircle(surface,
                                            (*_NS_azkharion.PALETTE["purple_hot"], alpha),
                                            (tip_x_arc, tip_y_arc), r)
                _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["purple_shine"],
                                        (tip_x_arc, tip_y_arc), 2)
                pygame.draw.rect(surface, _NS_azkharion.PALETTE["white"],
                                 (tip_x_arc, tip_y_arc, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = _NS_azkharion._alpha((14 - radius) * 15 * pulse)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius // 2,
                 120 + radius * 2, radius),
            )
        pygame.draw.ellipse(shadow, (10, 5, 20, 170), (10, 10, 120, 10))
        pygame.draw.ellipse(shadow, (60, 20, 100, 100), (18, 12, 104, 6))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_purple_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Purple wisps below boss."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(34, 3, -3):
            alpha = _NS_azkharion._alpha((34 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_azkharion.PALETTE["purple_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(22, 3, -2):
            alpha = _NS_azkharion._alpha((22 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_azkharion.PALETTE["purple_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising purple particles
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_azkharion._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_azkharion._aacircle(surface,
                                    (*_NS_azkharion.PALETTE["purple_dark"], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_azkharion.PALETTE["purple_hot"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_azkharion.PALETTE["purple_shine"], alpha),
                             (sx, sy - 2, 1, 1))
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_azkharion._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_azkharion._aacircle(surface,
                                        (*_NS_azkharion.PALETTE["purple_darkest"], alpha),
                                        (sx, sy), max(2, 7 - i))
                _NS_azkharion._aacircle(surface,
                                        (*_NS_azkharion.PALETTE["purple_dark"], alpha),
                                        (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface,
                                 (*_NS_azkharion.PALETTE["purple_hot"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_royal_aura(surface, x, y, phase):
        """Royal purple aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 210), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_azkharion._alpha((100 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_azkharion._aacircle(aura,
                                        (*_NS_azkharion.PALETTE["purple_darkest"], alpha),
                                        (120, 105), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_azkharion._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_azkharion._aacircle(aura,
                                        (*_NS_azkharion.PALETTE["purple_dark"], alpha),
                                        (120, 105), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_azkharion._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_azkharion._aacircle(aura,
                                        (*_NS_azkharion.PALETTE["purple_mid"], alpha),
                                        (120, 105), radius)
        surface.blit(aura, (x - 120, y - 105))
        # Floating embers
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 42 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_azkharion.PALETTE["purple_hot"] if i % 2 == 0 \
                else _NS_azkharion.PALETTE["purple_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["purple_shine"], (sx, sy, 1, 1))
    def _draw_ground_sigil(surface, x, y, phase, skill):
        """Ground royal sigil ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 58), pygame.SRCALPHA)
        for i, (rw, rh, alpha) in enumerate([
            (82, 24, 200), (68, 20, 220), (54, 15, 220), (40, 11, 200),
        ]):
            offset = int(math.sin(phase * 1.5 + i * 0.5) * 2)
            pygame.draw.ellipse(ring,
                                (*_NS_azkharion.PALETTE["purple_dark"], alpha),
                                (90 - rw + offset, 29 - rh, rw * 2, rh * 2), 2)
            pygame.draw.ellipse(ring,
                                (*_NS_azkharion.PALETTE["purple_mid"], alpha),
                                (90 - rw + offset + 1, 29 - rh + 1,
                                 rw * 2 - 2, rh * 2 - 2), 1)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 29 + int(math.sin(angle) * 10)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 29 + int(math.sin(angle) * 14)
            pygame.draw.line(ring,
                             (*_NS_azkharion.PALETTE["purple_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_azkharion.PALETTE["purple_light"],
                                 _NS_azkharion._alpha(180 * pulse)),
                                (15, 12, 150, 34), 1)
        surface.blit(ring, (x - 90, y - 29))
    # ============================================================
    # SKILL Q - CRESCENT DASH (dash + slash)
    # ============================================================
    def _draw_crescent_dash_ground(surface, boss, x, y, timer, phase):
        """Ground streak from dash."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Ground streak line
        streak_len = int(80 * progress)
        for i in range(streak_len // 4):
            sx = x - facing * (i * 4)
            alpha = _NS_azkharion._alpha(200 * (1 - i * 4 / max(1, streak_len)))
            pygame.draw.line(surface, (*_NS_azkharion.PALETTE["purple_dark"], alpha),
                             (sx, y + 45), (sx - facing * 3, y + 45), 3)
            pygame.draw.rect(surface, (*_NS_azkharion.PALETTE["purple_hot"], alpha),
                             (sx, y + 45, 2, 1))
    def _draw_crescent_dash_foreground(surface, boss, x, y, timer, phase):
        """Big crescent slash from dash."""
        facing = boss.direction
        duration = 40
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Charge glow at both hands
            t = progress / 0.3
            for hand_off in (-8, 12):
                hand_x = x + facing * hand_off
                hand_y = y + 4
                cr = int(4 + t * 6)
                for r in range(cr + 3, 0, -1):
                    alpha = _NS_azkharion._alpha(200 * (cr + 3 - r) / (cr + 3))
                    _NS_azkharion._aacircle(surface,
                                            (*_NS_azkharion.PALETTE["purple_dark"], alpha),
                                            (hand_x, hand_y), r)
                _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["purple_hot"],
                                        (hand_x, hand_y), max(1, cr - 2))
                _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["purple_shine"],
                                        (hand_x, hand_y), max(1, cr - 4))
        else:
            # Massive crescent extending forward
            t = (progress - 0.3) / 0.7
            arc_cx = x + facing * 12
            arc_cy = y - 4
            arc_radius = int(60 + t * 40)
            start_a = -math.pi * 0.7
            end_a = math.pi * 0.7
            trail_length = 0.55
            start_seg_t = max(0.0, t - trail_length)
            end_seg_t = min(1.0, t)
            for layer_i, (thick, alpha_mult, color) in enumerate([
                (7, 0.3, _NS_azkharion.PALETTE["purple_darkest"]),
                (6, 0.5, _NS_azkharion.PALETTE["purple_dark"]),
                (5, 0.7, _NS_azkharion.PALETTE["purple_mid"]),
                (4, 0.9, _NS_azkharion.PALETTE["purple_light"]),
                (3, 1.0, _NS_azkharion.PALETTE["purple_hot"]),
                (2, 1.0, _NS_azkharion.PALETTE["purple_shine"]),
                (1, 1.0, _NS_azkharion.PALETTE["white"]),
            ]):
                arc_alpha_base = _NS_azkharion._alpha(240 * alpha_mult * (1 - t * 0.4))
                arc_points = []
                num_segments = 26
                for seg in range(num_segments):
                    seg_t = start_seg_t + (end_seg_t - start_seg_t) * (seg / (num_segments - 1))
                    a = start_a + (end_a - start_a) * seg_t
                    ax = arc_cx + int(math.cos(a) * arc_radius * facing)
                    ay = arc_cy + int(math.sin(a) * arc_radius)
                    arc_points.append((ax, ay))
                if len(arc_points) >= 2:
                    for i in range(len(arc_points) - 1):
                        fade = i / max(1, len(arc_points) - 1)
                        actual_alpha = _NS_azkharion._alpha(arc_alpha_base * fade)
                        pygame.draw.line(surface, (*color, actual_alpha),
                                         arc_points[i], arc_points[i + 1], thick)
            # Sparks at leading edge
            if 0.05 < t < 0.95:
                tip_a = start_a + (end_a - start_a) * t
                tip_x = arc_cx + int(math.cos(tip_a) * arc_radius * facing)
                tip_y = arc_cy + int(math.sin(tip_a) * arc_radius)
                for r in range(10, 0, -1):
                    alpha = _NS_azkharion._alpha(220 * (10 - r) / 10)
                    _NS_azkharion._aacircle(surface,
                                            (*_NS_azkharion.PALETTE["purple_hot"], alpha),
                                            (tip_x, tip_y), r)
                _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["purple_shine"],
                                        (tip_x, tip_y), 2)
                pygame.draw.rect(surface, _NS_azkharion.PALETTE["white"],
                                 (tip_x, tip_y, 1, 1))
    # ============================================================
    # SKILL W - WHIRLING TEMPEST (spinning AoE around boss)
    # ============================================================
    def _draw_whirling_tempest_ground(surface, boss, x, y, timer, phase):
        """Ground marks under spinning boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_azkharion.PALETTE["purple_darkest"], 200),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_azkharion.PALETTE["purple_dark"], 180),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
    def _draw_whirling_tempest_foreground(surface, boss, x, y, timer, phase):
        """Multiple crescent blades spinning around boss."""
        duration = 90
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 * min(1.0, progress * 3))
        if r < 5:
            return
        # Draw 4 large crescent arcs rotating around boss at different angles
        num_arcs = 4
        for arc_i in range(num_arcs):
            arc_angle_offset = phase * 3 + arc_i * (math.pi * 2 / num_arcs)
            arc_center_x = x + int(math.cos(arc_angle_offset) * r * 0.3)
            arc_center_y = y - 4 + int(math.sin(arc_angle_offset) * r * 0.15)
            # Arc parameters (crescent moon shape)
            arc_r = r
            arc_start = arc_angle_offset - math.pi * 0.3
            arc_end = arc_angle_offset + math.pi * 0.3
            # Layered arc
            for layer_i, (thick, alpha_val, color) in enumerate([
                (5, 150, _NS_azkharion.PALETTE["purple_dark"]),
                (3, 200, _NS_azkharion.PALETTE["purple_mid"]),
                (2, 240, _NS_azkharion.PALETTE["purple_hot"]),
                (1, 255, _NS_azkharion.PALETTE["purple_shine"]),
            ]):
                prev_pt = None
                for seg in range(16):
                    seg_t = seg / 15
                    a = arc_start + (arc_end - arc_start) * seg_t
                    ax = x + int(math.cos(a) * arc_r)
                    ay = y - 4 + int(math.sin(a) * arc_r * 0.7)
                    if prev_pt:
                        pygame.draw.line(surface, (*color, alpha_val),
                                         prev_pt, (ax, ay), thick)
                    prev_pt = (ax, ay)
            # Bright tip
            tip_a = arc_angle_offset
            tip_x = x + int(math.cos(tip_a) * arc_r)
            tip_y = y - 4 + int(math.sin(tip_a) * arc_r * 0.7)
            for tr in range(6, 0, -1):
                alpha = _NS_azkharion._alpha(200 * (6 - tr) / 6)
                _NS_azkharion._aacircle(surface,
                                        (*_NS_azkharion.PALETTE["purple_hot"], alpha),
                                        (tip_x, tip_y), tr)
            _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["purple_shine"],
                                    (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["white"], (tip_x, tip_y, 1, 1))
        # Small energy sparkles flying outward
        for i in range(20):
            angle = phase * 4 + i * math.pi / 10
            dist = int(r * (0.7 + 0.3 * math.sin(phase * 2 + i)))
            sx = x + int(math.cos(angle) * dist)
            sy = y - 4 + int(math.sin(angle) * dist * 0.7)
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["purple_shine"], (sx, sy, 1, 1))
    # ============================================================
    # SKILL E - EARTHSHATTER (slam ground + shockwave spikes)
    # ============================================================
    def _draw_earthshatter_ground(surface, boss, x, y, timer, phase):
        """Cracked ground marks."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_azkharion.PALETTE["purple_darkest"], 200),
                                (x - r, y + 42 - r // 3, r * 2, r * 2 // 3))
            # Cracks
            for i in range(8):
                angle = i * math.pi / 4 + phase * 0.1
                x1 = x + int(math.cos(angle) * 8)
                y1 = y + 42 + int(math.sin(angle) * 4)
                x2 = x + int(math.cos(angle) * r)
                y2 = y + 42 + int(math.sin(angle) * r * 0.5)
                pygame.draw.line(surface, _NS_azkharion.PALETTE["purple_dark"],
                                 (x1, y1), (x2, y2), 2)
                pygame.draw.line(surface, _NS_azkharion.PALETTE["purple_hot"],
                                 (x1, y1), (x2, y2), 1)
    def _draw_earthshatter_foreground(surface, boss, x, y, timer, phase):
        """Purple spikes erupting from ground in a line/AoE."""
        facing = boss.direction
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.15:
            # Wind up gathering at ground
            t = progress / 0.15
            gather_x = x + facing * 8
            gather_y = y + 40
            for r in range(int(10 * t), 0, -1):
                alpha = _NS_azkharion._alpha(200 * t * (10 - r) / 10)
                _NS_azkharion._aacircle(surface,
                                        (*_NS_azkharion.PALETTE["purple_hot"], alpha),
                                        (gather_x, gather_y), r)
            return
        # Erupt phase: spikes rise in cluster + line forward
        t = (progress - 0.15) / 0.85
        rise_t = min(1.0, t * 3)
        fade_t = max(0, (t - 0.7) / 0.3)
        # Central big cluster
        cluster_configs = [
            (0, 40, 30, 8),      # center tallest
            (-16, 42, 22, 6),
            (16, 42, 22, 6),
            (-30, 44, 15, 5),
            (30, 44, 15, 5),
            (-8, 41, 24, 6),
            (8, 41, 24, 6),
        ]
        # Additional spikes in line forward
        for i in range(4):
            fwd_dist = facing * (40 + i * 20)
            cluster_configs.append((fwd_dist, 42 + i * 2, 18 - i * 3, 5))
        for dx, dy, max_h, width in cluster_configs:
            spike_x = x + dx
            spike_y = y + dy
            cur_h = int(max_h * rise_t)
            if cur_h < 2:
                continue
            spike_tip_y = spike_y - cur_h
            alpha_s = _NS_azkharion._alpha(240 * (1 - fade_t))
            # Shadow
            _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x - width + 1, spike_y + 1),
                (spike_x + width + 1, spike_y + 1),
            ])
            # Dark
            _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["purple_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x - width, spike_y),
                (spike_x + width, spike_y),
            ])
            # Mid
            _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["purple_dark"], [
                (spike_x, spike_tip_y),
                (spike_x - width + 1, spike_y),
                (spike_x + width - 1, spike_y),
            ])
            _NS_azkharion._poly(surface, _NS_azkharion.PALETTE["purple_mid"], [
                (spike_x, spike_tip_y + 1),
                (spike_x - width + 2, spike_y),
                (spike_x + width - 2, spike_y),
            ])
            # Glow core down middle
            pygame.draw.line(surface, _NS_azkharion.PALETTE["purple_hot"],
                             (spike_x, spike_tip_y + 2),
                             (spike_x, spike_y - 1), 1)
            # Bright tip
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["purple_shine"],
                             (spike_x, spike_tip_y, 1, 2))
            pygame.draw.rect(surface, _NS_azkharion.PALETTE["white"],
                             (spike_x, spike_tip_y, 1, 1))
            # Sparkles
            for i in range(2):
                sp_angle = phase * 3 + i * math.pi
                sxx = spike_x + int(math.cos(sp_angle) * (width + 3))
                syy = spike_y - cur_h // 2 + int(math.sin(sp_angle) * (cur_h // 2))
                pygame.draw.rect(surface,
                                 (*_NS_azkharion.PALETTE["purple_hot"], alpha_s),
                                 (sxx, syy, 1, 1))
    # ============================================================
    # SKILL R - ASHURA ASCENSION (transform + finisher wave)
    # ============================================================
    def _draw_ashura_ascension_ground(surface, boss, x, y, timer, phase):
        """Ground marks."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(65 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_azkharion.PALETTE["purple_darkest"], 220),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_azkharion.PALETTE["purple_dark"], 200),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_azkharion.PALETTE["purple_mid"], 180),
                                (x - r + 8, y + 40 - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_ashura_overlay(surface, boss, x, y, timer, phase):
        """Ascension aura around boss during R."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Pulsing purple aura enveloping boss (transformation)
        pulse = math.sin(phase * 3) * 0.3 + 0.7
        for r in range(50, 20, -3):
            alpha = _NS_azkharion._alpha(150 * (50 - r) / 50 * pulse)
            _NS_azkharion._aacircle(surface,
                                    (*_NS_azkharion.PALETTE["purple_dark"], alpha),
                                    (x, y), r)
        # Rising energy tendrils around body
        for i in range(12):
            angle = phase * 2 + i * math.pi / 6
            base_r = 30
            fx = x + int(math.cos(angle) * base_r)
            fy_base = y + 20 + int(math.sin(angle) * base_r * 0.5)
            rise_t = (phase * 1.5 + i * 0.12) % 1.0
            fy = fy_base - int(rise_t * 50)
            alpha = _NS_azkharion._alpha(230 * (1 - rise_t))
            _NS_azkharion._aacircle(surface,
                                    (*_NS_azkharion.PALETTE["purple_dark"], alpha),
                                    (fx, fy), 3)
            _NS_azkharion._aacircle(surface,
                                    (*_NS_azkharion.PALETTE["purple_hot"], alpha),
                                    (fx, fy), 2)
            pygame.draw.rect(surface,
                             (*_NS_azkharion.PALETTE["purple_shine"], alpha),
                             (fx, fy, 1, 1))
    def _draw_ashura_ascension_foreground(surface, boss, x, y, timer, phase):
        """Massive crescent wave finisher unleashed."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_azkharion._target_position(boss, x, y)
        if progress < 0.4:
            # Charging: energy gathering around boss + at blades
            t = progress / 0.4
            # Big gathering charge in front
            gather_x = x + facing * 20
            gather_y = y - 4
            cr = int(4 + t * 14)
            for r in range(cr + 8, 0, -1):
                alpha = _NS_azkharion._alpha(200 * (cr + 8 - r) / (cr + 8))
                _NS_azkharion._aacircle(surface,
                                        (*_NS_azkharion.PALETTE["purple_darkest"], alpha),
                                        (gather_x, gather_y), r)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_azkharion._alpha(220 * (cr + 4 - r) / (cr + 4))
                _NS_azkharion._aacircle(surface,
                                        (*_NS_azkharion.PALETTE["purple_dark"], alpha),
                                        (gather_x, gather_y), r)
            _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["purple_mid"],
                                    (gather_x, gather_y), cr - 2)
            _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["purple_hot"],
                                    (gather_x, gather_y), max(1, cr - 5))
            _NS_azkharion._aacircle(surface, _NS_azkharion.PALETTE["purple_shine"],
                                    (gather_x, gather_y), max(1, cr - 7))
            # Sparks orbiting
            for i in range(8):
                angle = phase * 5 + i * math.pi / 4
                sx = gather_x + int(math.cos(angle) * (cr + 4))
                sy = gather_y + int(math.sin(angle) * (cr + 4))
                pygame.draw.rect(surface, _NS_azkharion.PALETTE["purple_shine"], (sx, sy, 2, 2))
        elif progress < 0.75:
            # UNLEASH: massive crescent wave shoots forward
            t = (progress - 0.4) / 0.35
            intensity = math.sin(t * math.pi)
            # Wave expands outward from boss to target
            wave_center_x = x + facing * (20 + t * 60)
            wave_center_y = y - 4
            # Massive crescent
            arc_radius = int(70 + t * 40)
            start_a = -math.pi * 0.75
            end_a = math.pi * 0.75
            for layer_i, (thick, alpha_mult, color) in enumerate([
                (10, 0.3, _NS_azkharion.PALETTE["purple_darkest"]),
                (8, 0.5, _NS_azkharion.PALETTE["purple_dark"]),
                (6, 0.7, _NS_azkharion.PALETTE["purple_mid"]),
                (4, 0.9, _NS_azkharion.PALETTE["purple_light"]),
                (3, 1.0, _NS_azkharion.PALETTE["purple_hot"]),
                (2, 1.0, _NS_azkharion.PALETTE["purple_shine"]),
                (1, 1.0, _NS_azkharion.PALETTE["white"]),
            ]):
                arc_alpha = _NS_azkharion._alpha(240 * alpha_mult * intensity)
                prev_pt = None
                for seg in range(30):
                    seg_t = seg / 29
                    a = start_a + (end_a - start_a) * seg_t
                    ax = wave_center_x + int(math.cos(a) * arc_radius * facing)
                    ay = wave_center_y + int(math.sin(a) * arc_radius)
                    if prev_pt:
                        pygame.draw.line(surface, (*color, arc_alpha),
                                         prev_pt, (ax, ay), thick)
                    prev_pt = (ax, ay)
            # Sparks flying outward
            for i in range(20):
                spark_angle = start_a + (end_a - start_a) * (i / 19)
                spark_r = arc_radius + int(math.sin(phase * 4 + i) * 8)
                sx = wave_center_x + int(math.cos(spark_angle) * spark_r * facing)
                sy = wave_center_y + int(math.sin(spark_angle) * spark_r)
                pygame.draw.rect(surface,
                                 (*_NS_azkharion.PALETTE["purple_shine"], _NS_azkharion._alpha(220 * intensity)),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_azkharion.PALETTE["white"], _NS_azkharion._alpha(220 * intensity)),
                                 (sx, sy, 1, 1))
            # Impact burst at target
            impact_r = int(20 + t * 30)
            impact_alpha = _NS_azkharion._alpha(240 * intensity)
            _NS_azkharion._aacircle(surface,
                                    (*_NS_azkharion.PALETTE["purple_darkest"], impact_alpha),
                                    (tx, ty), impact_r + 4, 3)
            _NS_azkharion._aacircle(surface,
                                    (*_NS_azkharion.PALETTE["purple_dark"], impact_alpha),
                                    (tx, ty), impact_r, 3)
            _NS_azkharion._aacircle(surface,
                                    (*_NS_azkharion.PALETTE["purple_mid"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 6), 2)
            _NS_azkharion._aacircle(surface,
                                    (*_NS_azkharion.PALETTE["purple_light"], impact_alpha),
                                    (tx, ty), max(1, impact_r - 12), 1)
            _NS_azkharion._aacircle(surface,
                                    (*_NS_azkharion.PALETTE["purple_shine"], impact_alpha),
                                    (tx, ty), max(1, impact_r // 4))
            # Radial burst spikes
            for i in range(16):
                angle_s = i * math.pi / 8
                ex = tx + int(math.cos(angle_s) * impact_r)
                ey = ty + int(math.sin(angle_s) * impact_r * 0.7)
                pygame.draw.line(surface,
                                 (*_NS_azkharion.PALETTE["purple_hot"], impact_alpha),
                                 (tx, ty), (ex, ey), 2)
                pygame.draw.rect(surface,
                                 (*_NS_azkharion.PALETTE["purple_shine"], impact_alpha),
                                 (ex, ey, 2, 2))
        else:
            # Aftermath
            t = (progress - 0.75) / 0.25
            for i in range(15):
                rise_t = (phase * 0.8 + i * 0.1) % 1.0
                rx = tx + int(math.sin(phase + i) * 28)
                ry = ty - int(rise_t * 45)
                alpha = _NS_azkharion._alpha(220 * (1 - t) * (1 - rise_t))
                if alpha > 0:
                    _NS_azkharion._aacircle(surface,
                                            (*_NS_azkharion.PALETTE["purple_dark"], alpha),
                                            (rx, ry), 3)
                    _NS_azkharion._aacircle(surface,
                                            (*_NS_azkharion.PALETTE["purple_hot"], alpha),
                                            (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_azkharion.PALETTE["purple_shine"], alpha),
                                     (rx, ry, 1, 1))



# ====================================================================
# THARGOROTH (PRIMORDIAL COLOSSUS) - Mini Boss
# ====================================================================

class _NS_thargoroth:
    """Namespace thargoroth - Primordial Colossus titan boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Stone/rock body (weathered)
        "stone_darkest": (25, 20, 15),
        "stone_dark": (55, 45, 30),
        "stone_mid": (110, 90, 55),
        "stone_light": (170, 145, 90),
        "stone_shine": (220, 195, 140),
        # Rusted metal (armor plates)
        "metal_darkest": (30, 22, 12),
        "metal_dark": (75, 55, 25),
        "metal_mid": (140, 105, 45),
        "metal_light": (200, 160, 75),
        "metal_shine": (240, 210, 130),
        # Crystal cyan (main glow - Elder Titan's signature)
        "crystal_darkest": (5, 30, 40),
        "crystal_dark": (15, 70, 90),
        "crystal_mid": (30, 155, 175),
        "crystal_light": (90, 220, 235),
        "crystal_hot": (160, 245, 250),
        "crystal_shine": (220, 255, 255),
        # Green nature (E skill, veins)
        "nature_dark": (30, 65, 20),
        "nature_mid": (90, 175, 55),
        "nature_hot": (170, 245, 100),
        "nature_shine": (220, 255, 180),
        # Dark bronze
        "bronze_dark": (60, 35, 15),
        "bronze_mid": (130, 85, 30),
        "bronze_light": (200, 150, 65),
        # Eye (glowing cyan)
        "eye_socket": (5, 15, 20),
        "eye_dark": (15, 60, 90),
        "eye_mid": (60, 170, 200),
        "eye_light": (170, 230, 245),
        "eye_glow": (220, 250, 255),
        # Bone/horns (ancient)
        "bone_dark": (50, 40, 25),
        "bone_mid": (135, 115, 75),
        "bone_light": (215, 195, 145),
        "bone_shine": (245, 230, 190),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 2, 3),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_thargoroth._clamp(color)
        if _NS_thargoroth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_thargoroth._clamp(color)
        if _NS_thargoroth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_thargoroth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_thargoroth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_thargoroth._detect_moving(boss)
        _NS_thargoroth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_th_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_thargoroth._draw_ancient_aura(surface, x, y, pulse)
        _NS_thargoroth._draw_ground_runes(surface, x, y + 50, pulse, active_skill)
        # Ground skill FX
        if active_skill == "q":
            _NS_thargoroth._draw_crystal_sunder_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thargoroth._draw_seismic_pulse_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thargoroth._draw_earthrift_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (floating)
        if attacking:
            _NS_thargoroth._draw_th_attack(surface, boss, x, y)
        elif moving:
            _NS_thargoroth._draw_th_float_move(surface, boss, x, y)
        else:
            _NS_thargoroth._draw_th_idle(surface, boss, x, y)
        # W skill: spirit overlay
        if active_skill == "w":
            _NS_thargoroth._draw_spirit_walk_overlay(surface, boss, x, y, skill_timer, pulse)
        # Foreground FX
        if active_skill == "q":
            _NS_thargoroth._draw_crystal_sunder_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_thargoroth._draw_seismic_pulse_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_thargoroth._draw_earthrift_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_th_previous_timer", 0))
        active = bool(getattr(boss, "_th_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._th_attack_active = True
            boss._th_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._th_attack_frame = int(getattr(boss, "_th_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._th_attack_active = False
            boss._th_attack_frame = 0
            active = False
        boss._th_previous_timer = timer
        boss._th_attack_progress = (
            min(1.0, getattr(boss, "_th_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
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
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_th_idle(surface, boss, x, y):
        # Slower bob (heavy titan)
        bob = int(math.sin(boss.pulse * 0.4) * 3)
        _NS_thargoroth._draw_float_shadow(surface, x, y + 54, boss.pulse)
        _NS_thargoroth._draw_crystal_wisps(surface, x, y + 42, boss.pulse)
        _NS_thargoroth._draw_th_body(surface, x, y + bob,
                                      boss.direction, boss.pulse, "idle")
    def _draw_th_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.3
        bob = int(math.sin(phase * 0.7) * 3)
        sway = int(math.sin(phase * 0.4) * 2)
        _NS_thargoroth._draw_float_shadow(surface, x + sway, y + 54, phase)
        _NS_thargoroth._draw_crystal_wisps(surface, x + sway, y + 42, phase,
                                            trail=True, facing=boss.direction)
        _NS_thargoroth._draw_th_body(surface, x + sway, y + bob,
                                      boss.direction, phase, "float")
    def _draw_th_attack(surface, boss, x, y):
        """Melee: massive slam/punch animation."""
        progress = getattr(boss, "_th_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind up (rear back) → forward slam → recovery
        if progress < 0.35:
            t = progress / 0.35
            body_shift = -int(t * 5) * boss.direction
            lift = int(t * 5)
        elif progress < 0.65:
            t = (progress - 0.35) / 0.3
            body_shift = int((-5 + t * 14)) * boss.direction
            lift = int(5 - t * 8)
        else:
            t = (progress - 0.65) / 0.35
            body_shift = int(9 * (1 - t)) * boss.direction
            lift = int(-3 + t * 3)
        bob = int(math.sin(boss.pulse * 0.4) * 2)
        _NS_thargoroth._draw_float_shadow(surface, x + body_shift, y + 54, boss.pulse)
        _NS_thargoroth._draw_crystal_wisps(surface, x + body_shift, y + 42, boss.pulse,
                                            intense=True)
        _NS_thargoroth._draw_th_body(surface, x + body_shift, y - lift + bob,
                                      boss.direction, boss.pulse, "attack", progress)
        # Slam impact arc
        _NS_thargoroth._draw_slam_impact(surface, boss, x + body_shift,
                                          y - lift + bob, progress)
    # ============================================================
    # BODY - Massive Titan (huge shoulders, small head, stubby legs, glowing crystals)
    # ============================================================
    def _draw_th_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Titan body: heavy stone/metal armor, glowing crystals, tiny head, big fists."""
        # Back crystals (behind body)
        _NS_thargoroth._draw_back_crystals(surface, cx, cy - 8, facing, phase)
        # Legs/hip
        _NS_thargoroth._draw_titan_legs(surface, cx, cy + 12, facing, phase)
        # HUGE torso (main body)
        _NS_thargoroth._draw_titan_torso(surface, cx, cy - 2, facing, phase)
        # Massive shoulder armor + horns
        _NS_thargoroth._draw_titan_shoulders(surface, cx, cy - 8, facing, phase)
        # Arms
        arm_thrust = 0
        if action == "attack":
            if attack_progress < 0.35:
                arm_thrust = -int(attack_progress / 0.35 * 6) * facing
            elif attack_progress < 0.65:
                t = (attack_progress - 0.35) / 0.3
                arm_thrust = int((-6 + t * 20)) * facing
            else:
                t = (attack_progress - 0.65) / 0.35
                arm_thrust = int(14 * (1 - t)) * facing
        # Front arm with fist (massive)
        _NS_thargoroth._draw_front_arm_fist(surface, cx, cy - 2, facing, phase,
                                             arm_thrust, action)
        # Back arm
        _NS_thargoroth._draw_back_arm(surface, cx, cy - 2, facing, phase)
        # Tiny head at top with horns
        _NS_thargoroth._draw_titan_head(surface, cx, cy - 22, facing, phase, action)
    def _draw_back_crystals(surface, cx, cy, facing, phase):
        """Large crystal shards behind body (like Elder Titan's back crystals)."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # 3 tall crystals rising from back
        for crystal_i, (x_off, y_off, height, width) in enumerate([
            (-14, 0, 22, 4),   # left tall
            (0, -4, 26, 5),    # center tallest
            (14, 0, 22, 4),    # right tall
        ]):
            base_x = cx + x_off
            base_y = cy + y_off
            tip_x = base_x
            tip_y = base_y - height
            # Crystal shape (elongated diamond)
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"], [
                (tip_x + 1, tip_y + 1),
                (base_x + width + 1, base_y - height // 2 + 1),
                (base_x + 1, base_y + 1),
                (base_x - width + 1, base_y - height // 2 + 1),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["crystal_darkest"], [
                (tip_x, tip_y),
                (base_x + width, base_y - height // 2),
                (base_x, base_y),
                (base_x - width, base_y - height // 2),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["crystal_dark"], [
                (tip_x, tip_y + 1),
                (base_x + width - 1, base_y - height // 2),
                (base_x, base_y - 1),
                (base_x - width + 1, base_y - height // 2),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["crystal_mid"], [
                (tip_x, tip_y + 2),
                (base_x + width - 2, base_y - height // 2),
                (base_x, base_y - 2),
                (base_x - width + 2, base_y - height // 2),
            ])
            # Bright inner core
            pygame.draw.line(surface, _NS_thargoroth.PALETTE["crystal_light"],
                             (tip_x, tip_y + 3), (base_x, base_y - 3), 1)
            pygame.draw.line(surface, _NS_thargoroth.PALETTE["crystal_hot"],
                             (tip_x, tip_y + 4), (base_x, base_y - 4), 1)
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["crystal_shine"],
                             (tip_x, tip_y + 3, 1, 2))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["white"],
                             (tip_x, tip_y + 3, 1, 1))
            # Facet highlights
            pygame.draw.line(surface, _NS_thargoroth.PALETTE["crystal_light"],
                             (tip_x - 1, tip_y + 2),
                             (base_x - width + 2, base_y - height // 2), 1)
            # Glow around crystal tip
            for r in range(4, 0, -1):
                alpha = _NS_thargoroth._alpha(150 * (4 - r) / 4 * pulse)
                _NS_thargoroth._aacircle(surface,
                                        (*_NS_thargoroth.PALETTE["crystal_hot"], alpha),
                                        (tip_x, tip_y), r)
    def _draw_titan_legs(surface, cx, cy, facing, phase):
        """Stubby thick legs with armor."""
        # Legs are thick and short (titan style)
        # Two leg columns
        for side, side_mult in [("front", facing), ("back", -facing)]:
            leg_x = cx + side_mult * 6
            leg_top_y = cy - 2
            leg_bottom_y = cy + 20
            # Leg base (dark)
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"], [
                (leg_x - 6 + 1, leg_top_y + 1),
                (leg_x + 6 + 1, leg_top_y + 1),
                (leg_x + 7 + 1, leg_bottom_y + 1),
                (leg_x - 7 + 1, leg_bottom_y + 1),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_darkest"], [
                (leg_x - 6, leg_top_y),
                (leg_x + 6, leg_top_y),
                (leg_x + 7, leg_bottom_y),
                (leg_x - 7, leg_bottom_y),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_dark"], [
                (leg_x - 5, leg_top_y + 1),
                (leg_x + 5, leg_top_y + 1),
                (leg_x + 6, leg_bottom_y - 1),
                (leg_x - 6, leg_bottom_y - 1),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_mid"], [
                (leg_x - 4, leg_top_y + 2),
                (leg_x + 4, leg_top_y + 2),
                (leg_x + 5, leg_bottom_y - 2),
                (leg_x - 5, leg_bottom_y - 2),
            ])
            # Highlight
            pygame.draw.line(surface, _NS_thargoroth.PALETTE["stone_light"],
                             (leg_x - 2, leg_top_y + 3),
                             (leg_x - 3, leg_bottom_y - 3), 1)
            # Metal armor plates on leg
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["metal_dark"], [
                (leg_x - 5, leg_top_y),
                (leg_x + 5, leg_top_y),
                (leg_x + 6, leg_top_y + 5),
                (leg_x - 6, leg_top_y + 5),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["metal_mid"], [
                (leg_x - 4, leg_top_y + 1),
                (leg_x + 4, leg_top_y + 1),
                (leg_x + 5, leg_top_y + 4),
                (leg_x - 5, leg_top_y + 4),
            ])
            # Metal rivets
            for rivet_x in (-3, 0, 3):
                pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_light"],
                                 (leg_x + rivet_x, leg_top_y + 2, 1, 1))
                pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_shine"],
                                 (leg_x + rivet_x, leg_top_y + 2, 1, 1))
            # Knee guard (metal circle)
            knee_y = leg_top_y + 10
            _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["shadow_deep"],
                                    (leg_x + 1, knee_y + 1), 4)
            _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["metal_darkest"],
                                    (leg_x, knee_y), 4)
            _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["metal_dark"],
                                    (leg_x, knee_y), 3)
            _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["metal_mid"],
                                    (leg_x, knee_y), 2)
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_light"],
                             (leg_x - 1, knee_y - 1, 2, 1))
            # Foot (big flat)
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"], [
                (leg_x - 8 + 1, leg_bottom_y - 1 + 1),
                (leg_x + 8 + 1, leg_bottom_y - 1 + 1),
                (leg_x + 9 + 1, leg_bottom_y + 3 + 1),
                (leg_x - 9 + 1, leg_bottom_y + 3 + 1),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_darkest"], [
                (leg_x - 8, leg_bottom_y - 1),
                (leg_x + 8, leg_bottom_y - 1),
                (leg_x + 9, leg_bottom_y + 3),
                (leg_x - 9, leg_bottom_y + 3),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_dark"], [
                (leg_x - 7, leg_bottom_y),
                (leg_x + 7, leg_bottom_y),
                (leg_x + 8, leg_bottom_y + 2),
                (leg_x - 8, leg_bottom_y + 2),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_mid"], [
                (leg_x - 6, leg_bottom_y + 1),
                (leg_x + 6, leg_bottom_y + 1),
                (leg_x + 7, leg_bottom_y + 2),
                (leg_x - 7, leg_bottom_y + 2),
            ])
    def _draw_titan_torso(surface, cx, cy, facing, phase):
        """Massive stone-metal armored torso."""
        # HUGE torso shape (wide, blocky)
        torso_pts = [
            (cx - 18, cy - 8),
            (cx + 18, cy - 8),
            (cx + 22, cy - 2),
            (cx + 20, cy + 8),
            (cx + 14, cy + 14),
            (cx - 14, cy + 14),
            (cx - 20, cy + 8),
            (cx - 22, cy - 2),
        ]
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"],
                             [(px + 2, py + 3) for px, py in torso_pts])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_darkest"], torso_pts)
        # Stone layer
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_dark"], [
            (cx - 17, cy - 7),
            (cx + 17, cy - 7),
            (cx + 21, cy - 2),
            (cx + 19, cy + 7),
            (cx + 13, cy + 13),
            (cx - 13, cy + 13),
            (cx - 19, cy + 7),
            (cx - 21, cy - 2),
        ])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_mid"], [
            (cx - 15, cy - 6),
            (cx + 15, cy - 6),
            (cx + 19, cy - 2),
            (cx + 16, cy + 6),
            (cx + 10, cy + 11),
            (cx - 10, cy + 11),
            (cx - 16, cy + 6),
            (cx - 19, cy - 2),
        ])
        # Stone highlights (weathered rock texture)
        pygame.draw.line(surface, _NS_thargoroth.PALETTE["stone_light"],
                         (cx - 12, cy - 5), (cx + 12, cy - 5), 1)
        pygame.draw.line(surface, _NS_thargoroth.PALETTE["stone_light"],
                         (cx - 10, cy - 1), (cx - 8, cy + 3), 1)
        pygame.draw.line(surface, _NS_thargoroth.PALETTE["stone_light"],
                         (cx + 8, cy - 1), (cx + 10, cy + 3), 1)
        # METAL CHEST PLATE (rectangular armor)
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"], [
            (cx - 12, cy - 5),
            (cx + 12, cy - 5),
            (cx + 12, cy + 10),
            (cx - 12, cy + 10),
        ])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["metal_darkest"], [
            (cx - 12, cy - 6),
            (cx + 12, cy - 6),
            (cx + 12, cy + 9),
            (cx - 12, cy + 9),
        ])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["metal_dark"], [
            (cx - 11, cy - 5),
            (cx + 11, cy - 5),
            (cx + 11, cy + 8),
            (cx - 11, cy + 8),
        ])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["metal_mid"], [
            (cx - 10, cy - 4),
            (cx + 10, cy - 4),
            (cx + 10, cy + 7),
            (cx - 10, cy + 7),
        ])
        # Rivets around plate
        for rivet_pos in [(-9, -3), (9, -3), (-9, 6), (9, 6), (-9, 2), (9, 2)]:
            rx, ry = rivet_pos
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_darkest"],
                             (cx + rx - 1, cy + ry - 1, 2, 2))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_light"],
                             (cx + rx, cy + ry, 1, 1))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_shine"],
                             (cx + rx, cy + ry, 1, 1))
        # HUGE CRYSTAL EMBEDDED IN CHEST (glowing)
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        # Diamond crystal shape
        crystal_top_y = cy - 3
        crystal_bot_y = cy + 6
        crystal_left_x = cx - 5
        crystal_right_x = cx + 5
        # Crystal frame
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"], [
            (cx, crystal_top_y - 1),
            (crystal_right_x + 1, cy + 1),
            (cx, crystal_bot_y + 1),
            (crystal_left_x - 1, cy + 1),
        ])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["crystal_darkest"], [
            (cx, crystal_top_y),
            (crystal_right_x, cy + 1),
            (cx, crystal_bot_y),
            (crystal_left_x, cy + 1),
        ])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["crystal_dark"], [
            (cx, crystal_top_y + 1),
            (crystal_right_x - 1, cy + 1),
            (cx, crystal_bot_y - 1),
            (crystal_left_x + 1, cy + 1),
        ])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["crystal_mid"], [
            (cx, crystal_top_y + 2),
            (crystal_right_x - 2, cy + 1),
            (cx, crystal_bot_y - 2),
            (crystal_left_x + 2, cy + 1),
        ])
        # Bright center
        pygame.draw.line(surface, _NS_thargoroth.PALETTE["crystal_light"],
                         (cx, crystal_top_y + 3), (cx, crystal_bot_y - 3), 1)
        pygame.draw.line(surface, _NS_thargoroth.PALETTE["crystal_hot"],
                         (cx, crystal_top_y + 4), (cx, crystal_bot_y - 4), 1)
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["crystal_shine"],
                         (cx, crystal_top_y + 3, 1, 2))
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["white"],
                         (cx, cy, 1, 1))
        # Glow around chest crystal
        for r in range(8, 0, -1):
            alpha = _NS_thargoroth._alpha(120 * (8 - r) / 8 * pulse)
            _NS_thargoroth._aacircle(surface,
                                    (*_NS_thargoroth.PALETTE["crystal_hot"], alpha),
                                    (cx, cy + 1), r)
        # Belt/hip trim (bronze)
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"], [
            (cx - 15, cy + 10),
            (cx + 15, cy + 10),
            (cx + 14, cy + 14),
            (cx - 14, cy + 14),
        ])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["bronze_dark"], [
            (cx - 14, cy + 10),
            (cx + 14, cy + 10),
            (cx + 13, cy + 13),
            (cx - 13, cy + 13),
        ])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["bronze_mid"], [
            (cx - 13, cy + 11),
            (cx + 13, cy + 11),
            (cx + 12, cy + 13),
            (cx - 12, cy + 13),
        ])
        # Bronze studs on belt
        for stud_x in (-10, -5, 0, 5, 10):
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["bronze_light"],
                             (cx + stud_x, cy + 11, 1, 1))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_shine"],
                             (cx + stud_x, cy + 11, 1, 1))
    def _draw_titan_shoulders(surface, cx, cy, facing, phase):
        """Massive shoulder pauldrons with horns and crystals."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for side in (-1, 1):
            # Huge shoulder plate
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"], [
                (cx + side * 14, cy + 1),
                (cx + side * 22, cy),
                (cx + side * 24, cy + 6),
                (cx + side * 20, cy + 10),
                (cx + side * 14, cy + 8),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_darkest"], [
                (cx + side * 14, cy),
                (cx + side * 22, cy - 1),
                (cx + side * 23, cy + 6),
                (cx + side * 19, cy + 9),
                (cx + side * 14, cy + 7),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_dark"], [
                (cx + side * 15, cy + 1),
                (cx + side * 21, cy),
                (cx + side * 22, cy + 5),
                (cx + side * 18, cy + 8),
                (cx + side * 15, cy + 6),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_mid"], [
                (cx + side * 16, cy + 2),
                (cx + side * 20, cy + 1),
                (cx + side * 21, cy + 5),
                (cx + side * 17, cy + 7),
                (cx + side * 16, cy + 5),
            ])
            # Highlight
            pygame.draw.line(surface, _NS_thargoroth.PALETTE["stone_light"],
                             (cx + side * 17, cy + 2),
                             (cx + side * 19, cy + 3), 1)
            # Metal band around shoulder edge
            pygame.draw.line(surface, _NS_thargoroth.PALETTE["metal_dark"],
                             (cx + side * 14, cy),
                             (cx + side * 22, cy - 1), 1)
            pygame.draw.line(surface, _NS_thargoroth.PALETTE["metal_light"],
                             (cx + side * 15, cy - 1),
                             (cx + side * 21, cy - 2), 1)
            # HORN protruding from shoulder (like Elder Titan)
            horn_base_x = cx + side * 19
            horn_base_y = cy
            horn_tip_x = cx + side * 22
            horn_tip_y = cy - 10
            # Curved horn
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"], [
                (horn_tip_x + 1, horn_tip_y + 1),
                (horn_base_x - 2 + 1, horn_base_y + 1),
                (horn_base_x + 2 + 1, horn_base_y + 1),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["bone_dark"], [
                (horn_tip_x, horn_tip_y),
                (horn_base_x - 2, horn_base_y),
                (horn_base_x + 2, horn_base_y),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["bone_mid"], [
                (horn_tip_x, horn_tip_y + 1),
                (horn_base_x - 1, horn_base_y),
                (horn_base_x + 1, horn_base_y),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["bone_light"], [
                (horn_tip_x, horn_tip_y + 2),
                (horn_base_x, horn_base_y),
                (horn_base_x + 1, horn_base_y - 1),
            ])
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["bone_shine"],
                             (horn_tip_x, horn_tip_y, 1, 1))
            # Small crystal on shoulder
            crystal_x = cx + side * 17
            crystal_y = cy + 4
            for r in range(4, 0, -1):
                alpha = _NS_thargoroth._alpha(140 * (4 - r) / 4 * pulse)
                _NS_thargoroth._aacircle(surface,
                                        (*_NS_thargoroth.PALETTE["crystal_hot"], alpha),
                                        (crystal_x, crystal_y), r)
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["crystal_darkest"],
                             (crystal_x - 1, crystal_y - 1, 2, 2))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["crystal_mid"],
                             (crystal_x, crystal_y, 1, 1))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["crystal_shine"],
                             (crystal_x, crystal_y, 1, 1))
    def _draw_front_arm_fist(surface, cx, cy, facing, phase, thrust, action):
        """Massive front arm with huge fist."""
        wave = math.sin(phase * 0.6) * 1
        shoulder_x = cx + facing * 16
        shoulder_y = cy + 4
        if action == "attack":
            hand_x = cx + facing * (24 + thrust)
            hand_y = cy + 8 + int(wave)
        else:
            hand_x = cx + facing * 22
            hand_y = cy + 12 + int(wave)
        elbow_x = (shoulder_x + hand_x) // 2 + facing * 2
        elbow_y = (shoulder_y + hand_y) // 2 + 2
        # Upper arm (thick)
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["shadow_deep"],
                               (shoulder_x + 1, shoulder_y + 1),
                               (elbow_x + 1, elbow_y + 1), 7)
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["stone_darkest"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 6)
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["stone_dark"],
                               (shoulder_x, shoulder_y), (elbow_x, elbow_y), 5)
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["stone_mid"],
                               (shoulder_x, shoulder_y - 1),
                               (elbow_x, elbow_y - 1), 3)
        # Metal elbow guard
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["shadow_deep"],
                         (elbow_x - 3, elbow_y - 2, 6, 5))
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_darkest"],
                         (elbow_x - 3, elbow_y - 2, 6, 4))
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_dark"],
                         (elbow_x - 2, elbow_y - 2, 5, 3))
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_mid"],
                         (elbow_x - 2, elbow_y - 2, 4, 2))
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_light"],
                         (elbow_x - 1, elbow_y - 2, 2, 1))
        # Spike on elbow
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"], [
            (elbow_x + facing * 4 + 1, elbow_y + 1),
            (elbow_x + 1, elbow_y - 2 + 1),
            (elbow_x + 1, elbow_y + 2 + 1),
        ])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["bone_dark"], [
            (elbow_x + facing * 4, elbow_y),
            (elbow_x, elbow_y - 2),
            (elbow_x, elbow_y + 2),
        ])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["bone_mid"], [
            (elbow_x + facing * 3, elbow_y),
            (elbow_x + facing, elbow_y - 1),
            (elbow_x + facing, elbow_y + 1),
        ])
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["bone_light"],
                         (elbow_x + facing * 3, elbow_y, 1, 1))
        # Forearm (thick)
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["shadow_deep"],
                               (elbow_x + 1, elbow_y + 1),
                               (hand_x + 1, hand_y + 1), 7)
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["stone_darkest"],
                               (elbow_x, elbow_y), (hand_x, hand_y), 6)
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["stone_dark"],
                               (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["stone_mid"],
                               (elbow_x, elbow_y - 1),
                               (hand_x, hand_y - 1), 3)
        # HUGE FIST (bigger than head)
        fist_r = 7
        _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["shadow_deep"],
                                (hand_x + 2, hand_y + 2), fist_r + 1)
        _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["stone_darkest"],
                                (hand_x, hand_y), fist_r + 1)
        _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["stone_dark"],
                                (hand_x, hand_y), fist_r)
        _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["stone_mid"],
                                (hand_x, hand_y), fist_r - 2)
        # Highlight
        _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["stone_light"],
                                (hand_x - 1, hand_y - 2), 2)
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["stone_shine"],
                         (hand_x - 1, hand_y - 3, 1, 1))
        # Metal knuckle plates
        for knuckle_off in (-3, 0, 3):
            kx = hand_x + int(math.cos(0) * knuckle_off * facing)
            ky = hand_y - 4
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_dark"],
                             (kx - 1, ky, 3, 3))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_mid"],
                             (kx - 1, ky, 3, 2))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_light"],
                             (kx, ky, 1, 1))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_shine"],
                             (kx, ky, 1, 1))
        # Small crystal embedded in fist top
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(4, 0, -1):
            alpha = _NS_thargoroth._alpha(150 * (4 - r) / 4 * pulse)
            _NS_thargoroth._aacircle(surface,
                                    (*_NS_thargoroth.PALETTE["crystal_hot"], alpha),
                                    (hand_x, hand_y - 5), r)
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["crystal_darkest"],
                         (hand_x - 1, hand_y - 6, 2, 2))
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["crystal_mid"],
                         (hand_x, hand_y - 5, 1, 1))
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["crystal_shine"],
                         (hand_x, hand_y - 5, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase):
        """Back arm with fist (partial visibility)."""
        wave = math.sin(phase * 0.6) * 1
        shoulder_x = cx - facing * 14
        shoulder_y = cy + 4
        elbow_x = cx - facing * 20
        elbow_y = cy + 10 + int(wave)
        hand_x = cx - facing * 18
        hand_y = cy + 18 + int(wave)
        # Upper arm
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["shadow_deep"],
                               (shoulder_x + 1, shoulder_y + 1),
                               (elbow_x + 1, elbow_y + 1), 6)
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["stone_darkest"],
                               (shoulder_x, shoulder_y),
                               (elbow_x, elbow_y), 5)
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["stone_dark"],
                               (shoulder_x, shoulder_y),
                               (elbow_x, elbow_y), 4)
        # Forearm
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["shadow_deep"],
                               (elbow_x + 1, elbow_y + 1),
                               (hand_x + 1, hand_y + 1), 6)
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["stone_darkest"],
                               (elbow_x, elbow_y), (hand_x, hand_y), 5)
        _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["stone_dark"],
                               (elbow_x, elbow_y), (hand_x, hand_y), 4)
        # Fist (partial)
        _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["stone_darkest"],
                                (hand_x, hand_y), 5)
        _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["stone_dark"],
                                (hand_x, hand_y), 4)
        _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["stone_mid"],
                                (hand_x, hand_y), 2)
    def _draw_titan_head(surface, cx, cy, facing, phase, action):
        """Small head at top with horns."""
        # Small head (tiny compared to body - Elder Titan style)
        head_pts = [
            (cx - 4, cy - 3),
            (cx + 4, cy - 3),
            (cx + 5, cy),
            (cx + 4, cy + 3),
            (cx + 2, cy + 5),
            (cx - 2, cy + 5),
            (cx - 4, cy + 3),
            (cx - 5, cy),
        ]
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"],
                             [(px + 1, py + 2) for px, py in head_pts])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_darkest"], head_pts)
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_dark"], [
            (cx - 3, cy - 3),
            (cx + 3, cy - 3),
            (cx + 4, cy),
            (cx + 3, cy + 3),
            (cx + 2, cy + 4),
            (cx - 2, cy + 4),
            (cx - 3, cy + 3),
            (cx - 4, cy),
        ])
        _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["stone_mid"], [
            (cx - 2, cy - 2),
            (cx + 2, cy - 2),
            (cx + 3, cy),
            (cx + 2, cy + 3),
            (cx - 2, cy + 3),
            (cx - 3, cy),
        ])
        # Highlight
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["stone_light"],
                         (cx - 1, cy - 1, 2, 1))
        # MASSIVE curved horns (like Elder Titan bull horns)
        _NS_thargoroth._draw_titan_horns(surface, cx, cy, facing, phase)
        # GLOWING CYAN EYES
        _NS_thargoroth._draw_cyan_eyes(surface, cx, cy, facing, phase)
        # Small crystal on forehead
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        for r in range(3, 0, -1):
            alpha = _NS_thargoroth._alpha(180 * (3 - r) / 3 * pulse)
            _NS_thargoroth._aacircle(surface,
                                    (*_NS_thargoroth.PALETTE["crystal_hot"], alpha),
                                    (cx, cy - 3), r)
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["crystal_mid"],
                         (cx, cy - 3, 1, 1))
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["crystal_shine"],
                         (cx, cy - 3, 1, 1))
    def _draw_titan_horns(surface, cx, cy, facing, phase):
        """Massive bull-like horns curving outward."""
        for side in (-1, 1):
            # Horn starts at side of head, curves up-out
            base_x = cx + side * 4
            base_y = cy - 2
            mid_x = cx + side * 10
            mid_y = cy - 6
            tip_x = cx + side * 14
            tip_y = cy - 12
            # Multi-segment curved horn
            for seg_i, ((s_x, s_y), (e_x, e_y), thick) in enumerate([
                ((base_x, base_y), (mid_x, mid_y), 4),
                ((mid_x, mid_y), (tip_x, tip_y), 3),
            ]):
                _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["shadow_deep"],
                                       (s_x + 1, s_y + 1), (e_x + 1, e_y + 1),
                                       thick + 1)
                _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["bone_dark"],
                                       (s_x, s_y), (e_x, e_y), thick)
                _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["bone_mid"],
                                       (s_x, s_y - 1), (e_x, e_y - 1),
                                       max(1, thick - 1))
                _NS_thargoroth._aaline(surface, _NS_thargoroth.PALETTE["bone_light"],
                                       (s_x, s_y - 2), (e_x, e_y - 2),
                                       max(1, thick - 2))
            # Sharp tip
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["bone_light"],
                             (tip_x, tip_y, 1, 1))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["bone_shine"],
                             (tip_x, tip_y, 1, 1))
            # Metal band around horn base
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_dark"],
                             (base_x - 1, base_y - 1, 3, 2))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["metal_light"],
                             (base_x, base_y - 1, 1, 1))
    def _draw_cyan_eyes(surface, cx, cy, facing, phase):
        """Two glowing cyan eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy + 1
            # Deep socket
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 2, 2))
            # Glow halo
            for r in range(4, 0, -1):
                alpha = _NS_thargoroth._alpha(160 * (4 - r) / 4 * pulse)
                _NS_thargoroth._aacircle(surface,
                                        (*_NS_thargoroth.PALETTE["eye_mid"], alpha),
                                        (ex, ey), r)
            # Bright core
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))
    # ============================================================
    # MELEE SLAM IMPACT (fist smash effect)
    # ============================================================
    def _draw_slam_impact(surface, boss, x, y, progress):
        """Cyan shockwave burst from fist during slam."""
        if progress < 0.5 or progress > 0.85:
            return
        facing = boss.direction
        t = (progress - 0.5) / 0.35
        # Impact point (at fist end position)
        impact_x = x + facing * 30
        impact_y = y + 10
        # Radial shockwave rings
        for ring_i in range(3):
            ring_t = t - ring_i * 0.15
            if ring_t <= 0 or ring_t > 1:
                continue
            ring_r = int(ring_t * 32)
            alpha = _NS_thargoroth._alpha(240 * (1 - ring_t))
            _NS_thargoroth._aacircle(surface,
                                    (*_NS_thargoroth.PALETTE["crystal_darkest"], alpha),
                                    (impact_x, impact_y), ring_r + 2, 3)
            _NS_thargoroth._aacircle(surface,
                                    (*_NS_thargoroth.PALETTE["crystal_dark"], alpha),
                                    (impact_x, impact_y), ring_r, 2)
            _NS_thargoroth._aacircle(surface,
                                    (*_NS_thargoroth.PALETTE["crystal_mid"], alpha),
                                    (impact_x, impact_y), max(1, ring_r - 3), 1)
        # Central burst
        burst_r = int(6 + t * 12)
        burst_alpha = _NS_thargoroth._alpha(240 * (1 - t * 0.7))
        for r in range(burst_r, 0, -1):
            alpha = _NS_thargoroth._alpha(150 * (burst_r - r) / burst_r * (1 - t * 0.5))
            _NS_thargoroth._aacircle(surface,
                                    (*_NS_thargoroth.PALETTE["crystal_light"], alpha),
                                    (impact_x, impact_y), r)
        _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["crystal_hot"],
                                (impact_x, impact_y), max(1, burst_r // 3))
        _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["crystal_shine"],
                                (impact_x, impact_y), 2)
        pygame.draw.rect(surface, _NS_thargoroth.PALETTE["white"],
                         (impact_x, impact_y, 1, 1))
        # Radial spikes (small crystals shooting outward)
        for i in range(8):
            spike_a = i * math.pi / 4
            spike_r = int(15 + t * 15)
            sx = impact_x + int(math.cos(spike_a) * spike_r)
            sy = impact_y + int(math.sin(spike_a) * spike_r * 0.6)
            spike_alpha = _NS_thargoroth._alpha(220 * (1 - t * 0.5))
            pygame.draw.rect(surface,
                             (*_NS_thargoroth.PALETTE["crystal_hot"], spike_alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_thargoroth.PALETTE["crystal_shine"], spike_alpha),
                             (sx, sy, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((160, 32), pygame.SRCALPHA)
        for radius in range(16, 0, -1):
            alpha = _NS_thargoroth._alpha((16 - radius) * 13 * pulse)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 16 - radius // 2,
                 140 + radius * 2, radius),
            )
        pygame.draw.ellipse(shadow, (5, 15, 20, 170), (10, 12, 140, 10))
        pygame.draw.ellipse(shadow, (20, 80, 100, 100), (18, 14, 124, 6))
        surface.blit(shadow, (x - 80, y - 16))
    def _draw_crystal_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Cyan crystal wisps below boss."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((160, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(36, 3, -3):
            alpha = _NS_thargoroth._alpha((36 - radius) * 2.6 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_thargoroth.PALETTE["crystal_darkest"], alpha),
                    (80 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(22, 3, -2):
            alpha = _NS_thargoroth._alpha((22 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_thargoroth.PALETTE["crystal_dark"], alpha),
                    (80 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 80, cy - 10))
        # Rising crystal particles (small diamonds)
        for i, offset in enumerate((-28, -20, -12, -4, 4, 12, 20, 28, -32)):
            t = (phase * 0.4 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_thargoroth._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            # Small crystal shape (diamond)
            pygame.draw.rect(surface,
                             (*_NS_thargoroth.PALETTE["crystal_dark"], alpha),
                             (sx, sy - 1, 1, 3))
            pygame.draw.rect(surface,
                             (*_NS_thargoroth.PALETTE["crystal_mid"], alpha),
                             (sx - 1, sy, 3, 1))
            pygame.draw.rect(surface,
                             (*_NS_thargoroth.PALETTE["crystal_hot"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_thargoroth.PALETTE["crystal_shine"], alpha),
                             (sx, sy, 1, 1))
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_thargoroth._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_thargoroth._aacircle(surface,
                                        (*_NS_thargoroth.PALETTE["crystal_darkest"], alpha),
                                        (sx, sy), max(2, 7 - i))
                _NS_thargoroth._aacircle(surface,
                                        (*_NS_thargoroth.PALETTE["crystal_dark"], alpha),
                                        (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface,
                                 (*_NS_thargoroth.PALETTE["crystal_hot"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_ancient_aura(surface, x, y, phase):
        """Massive cyan aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((260, 220), pygame.SRCALPHA)
        for radius in range(110, 5, -5):
            alpha = _NS_thargoroth._alpha((110 - radius) * 1.2 * pulse)
            if alpha > 0:
                _NS_thargoroth._aacircle(aura,
                                        (*_NS_thargoroth.PALETTE["crystal_darkest"], alpha),
                                        (130, 110), radius)
        for radius in range(70, 5, -4):
            alpha = _NS_thargoroth._alpha((70 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_thargoroth._aacircle(aura,
                                        (*_NS_thargoroth.PALETTE["crystal_dark"], alpha),
                                        (130, 110), radius)
        for radius in range(40, 5, -3):
            alpha = _NS_thargoroth._alpha((40 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_thargoroth._aacircle(aura,
                                        (*_NS_thargoroth.PALETTE["crystal_mid"], alpha),
                                        (130, 110), radius)
        surface.blit(aura, (x - 130, y - 110))
        # Floating crystal fragments
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 45 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_thargoroth.PALETTE["crystal_hot"] if i % 3 != 0 \
                else _NS_thargoroth.PALETTE["nature_hot"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["crystal_shine"], (sx, sy, 1, 1))
    def _draw_ground_runes(surface, x, y, phase, skill):
        """Ground rune ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((200, 60), pygame.SRCALPHA)
        for i, (rw, rh, alpha) in enumerate([
            (92, 26, 200), (76, 22, 220), (60, 17, 220), (44, 12, 200),
        ]):
            offset = int(math.sin(phase * 1.5 + i * 0.5) * 2)
            pygame.draw.ellipse(ring,
                                (*_NS_thargoroth.PALETTE["crystal_dark"], alpha),
                                (100 - rw + offset, 30 - rh, rw * 2, rh * 2), 2)
            pygame.draw.ellipse(ring,
                                (*_NS_thargoroth.PALETTE["crystal_mid"], alpha),
                                (100 - rw + offset + 1, 30 - rh + 1,
                                 rw * 2 - 2, rh * 2 - 2), 1)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 100 + int(math.cos(angle) * 56)
            y1 = 30 + int(math.sin(angle) * 11)
            x2 = 100 + int(math.cos(angle) * 86)
            y2 = 30 + int(math.sin(angle) * 15)
            pygame.draw.line(ring,
                             (*_NS_thargoroth.PALETTE["crystal_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_thargoroth.PALETTE["crystal_light"],
                                 _NS_thargoroth._alpha(180 * pulse)),
                                (15, 12, 170, 36), 1)
        surface.blit(ring, (x - 100, y - 30))
    # ============================================================
    # SKILL Q - CRYSTAL SUNDER (crystal spikes erupt at target)
    # ============================================================
    def _draw_crystal_sunder_ground(surface, boss, x, y, timer, phase):
        """Ground marks at target."""
        tx, ty = _NS_thargoroth._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(45 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_thargoroth.PALETTE["crystal_darkest"], 200),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_thargoroth.PALETTE["crystal_dark"], 180),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            # Cracks
            for i in range(6):
                angle = i * math.pi / 3 + phase * 0.1
                x1 = tx + int(math.cos(angle) * 6)
                y1 = ty + int(math.sin(angle) * 3)
                x2 = tx + int(math.cos(angle) * r)
                y2 = ty + int(math.sin(angle) * r * 0.5)
                pygame.draw.line(surface, _NS_thargoroth.PALETTE["crystal_hot"],
                                 (x1, y1), (x2, y2), 1)
    def _draw_crystal_sunder_foreground(surface, boss, x, y, timer, phase):
        """Cluster of crystal spikes erupting at target."""
        tx, ty = _NS_thargoroth._target_position(boss, x, y)
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.15:
            # Warning charge
            t = progress / 0.15
            r = int(6 + t * 10)
            for r_o in range(r, 0, -1):
                alpha = _NS_thargoroth._alpha(200 * t * (r - r_o) / r)
                _NS_thargoroth._aacircle(surface,
                                        (*_NS_thargoroth.PALETTE["crystal_hot"], alpha),
                                        (tx, ty), r_o)
            return
        t = (progress - 0.15) / 0.85
        rise_t = min(1.0, t * 3)
        fade_t = max(0, (t - 0.7) / 0.3)
        # Cluster of crystal spikes (like broken glass rising)
        spike_configs = [
            (0, 0, 32, 6),      # center tallest
            (-14, 2, 22, 5),
            (14, 2, 22, 5),
            (-24, 4, 15, 4),
            (24, 4, 15, 4),
            (-8, -2, 26, 5),
            (8, -2, 26, 5),
        ]
        for dx, dy, max_h, width in spike_configs:
            spike_x = tx + dx
            spike_y = ty + dy
            cur_h = int(max_h * rise_t)
            if cur_h < 2:
                continue
            spike_tip_y = spike_y - cur_h
            alpha_s = _NS_thargoroth._alpha(240 * (1 - fade_t))
            # Diamond crystal shape (tapered)
            mid_y = spike_y - cur_h // 2
            # Shadow
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x + width + 1, mid_y + 1),
                (spike_x + 1, spike_y + 1),
                (spike_x - width + 1, mid_y + 1),
            ])
            # Dark
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["crystal_darkest"], [
                (spike_x, spike_tip_y),
                (spike_x + width, mid_y),
                (spike_x, spike_y),
                (spike_x - width, mid_y),
            ])
            # Mid
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["crystal_dark"], [
                (spike_x, spike_tip_y + 1),
                (spike_x + width - 1, mid_y),
                (spike_x, spike_y - 1),
                (spike_x - width + 1, mid_y),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["crystal_mid"], [
                (spike_x, spike_tip_y + 2),
                (spike_x + width - 2, mid_y),
                (spike_x, spike_y - 2),
                (spike_x - width + 2, mid_y),
            ])
            # Bright center line
            pygame.draw.line(surface, _NS_thargoroth.PALETTE["crystal_light"],
                             (spike_x, spike_tip_y + 3),
                             (spike_x, spike_y - 3), 1)
            pygame.draw.line(surface, _NS_thargoroth.PALETTE["crystal_hot"],
                             (spike_x, spike_tip_y + 4),
                             (spike_x, spike_y - 4), 1)
            # Bright tip
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["crystal_shine"],
                             (spike_x, spike_tip_y, 1, 2))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["white"],
                             (spike_x, spike_tip_y, 1, 1))
            # Sparkles around spike
            for i in range(2):
                sp_angle = phase * 3 + i * math.pi
                sxx = spike_x + int(math.cos(sp_angle) * (width + 3))
                syy = spike_y - cur_h // 2 + int(math.sin(sp_angle) * (cur_h // 2))
                pygame.draw.rect(surface,
                                 (*_NS_thargoroth.PALETTE["crystal_hot"], alpha_s),
                                 (sxx, syy, 1, 1))
    # ============================================================
    # SKILL W - SPIRIT WALK (translucent spirit overlay)
    # ============================================================
    def _draw_spirit_walk_overlay(surface, boss, x, y, timer, phase):
        """Cyan spirit silhouette overlaid on boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        # Silhouette spirit form (rising/floating up from boss body)
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Draw translucent spirit silhouette going up
        spirit_offset_y = int(math.sin(phase * 1.5) * 5)
        # Spirit body shape (simple humanoid silhouette)
        spirit_surf = pygame.Surface((60, 90), pygame.SRCALPHA)
        local_cx = 30
        local_cy = 50
        # Aura glow around body
        for r in range(35, 5, -3):
            alpha = _NS_thargoroth._alpha(100 * (35 - r) / 35 * pulse)
            _NS_thargoroth._aacircle(spirit_surf,
                                    (*_NS_thargoroth.PALETTE["crystal_hot"], alpha),
                                    (local_cx, local_cy), r)
        # Ghost outline (torso + head)
        # Head
        _NS_thargoroth._aacircle(spirit_surf,
                                (*_NS_thargoroth.PALETTE["crystal_light"], 180),
                                (local_cx, local_cy - 20), 5)
        _NS_thargoroth._aacircle(spirit_surf,
                                (*_NS_thargoroth.PALETTE["crystal_shine"], 220),
                                (local_cx, local_cy - 20), 3)
        # Torso
        _NS_thargoroth._poly(spirit_surf,
                             (*_NS_thargoroth.PALETTE["crystal_light"], 180), [
                                 (local_cx - 8, local_cy - 15),
                                 (local_cx + 8, local_cy - 15),
                                 (local_cx + 10, local_cy),
                                 (local_cx + 6, local_cy + 15),
                                 (local_cx - 6, local_cy + 15),
                                 (local_cx - 10, local_cy),
                             ])
        _NS_thargoroth._poly(spirit_surf,
                             (*_NS_thargoroth.PALETTE["crystal_shine"], 200), [
                                 (local_cx - 6, local_cy - 12),
                                 (local_cx + 6, local_cy - 12),
                                 (local_cx + 8, local_cy),
                                 (local_cx + 4, local_cy + 12),
                                 (local_cx - 4, local_cy + 12),
                                 (local_cx - 8, local_cy),
                             ])
        # Rising particles inside
        for i in range(8):
            drop_t = (phase * 0.8 + i * 0.12) % 1.0
            dx = local_cx + int(math.sin(phase + i) * 8)
            dy = local_cy + 30 - int(drop_t * 60)
            alpha = _NS_thargoroth._alpha(220 * (1 - drop_t))
            pygame.draw.rect(spirit_surf,
                             (*_NS_thargoroth.PALETTE["crystal_shine"], alpha),
                             (dx, dy, 1, 1))
            pygame.draw.rect(spirit_surf,
                             (*_NS_thargoroth.PALETTE["white"], alpha),
                             (dx, dy, 1, 1))
        surface.blit(spirit_surf, (x - 30, y - 50 + spirit_offset_y))
    # ============================================================
    # SKILL E - SEISMIC PULSE (concentric shockwave rings)
    # ============================================================
    def _draw_seismic_pulse_ground(surface, boss, x, y, timer, phase):
        """Ground rings expanding."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 2.5))
        if r > 3:
            for ring_i in range(3):
                ring_r = int(r * (0.4 + ring_i * 0.3))
                alpha = _NS_thargoroth._alpha(220 - ring_i * 40)
                pygame.draw.ellipse(surface,
                                    (*_NS_thargoroth.PALETTE["nature_dark"], alpha),
                                    (x - ring_r, y + 42 - ring_r // 3,
                                     ring_r * 2, ring_r * 2 // 3), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_thargoroth.PALETTE["nature_hot"], alpha),
                                    (x - ring_r + 1, y + 42 - ring_r // 3 + 1,
                                     ring_r * 2 - 2, ring_r * 2 // 3 - 2), 1)
    def _draw_seismic_pulse_foreground(surface, boss, x, y, timer, phase):
        """Radial shockwave rings expanding + sparkles."""
        duration = 70
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(70 * min(1.0, progress * 2.5))
        if r < 5:
            return
        # Multiple expanding rings (concentric shockwaves)
        num_rings = 3
        for ring_i in range(num_rings):
            ring_t = (phase * 1.5 + ring_i * 0.4) % 1.0
            ring_r = int(r * ring_t)
            if ring_r < 5:
                continue
            alpha = _NS_thargoroth._alpha(240 * (1 - ring_t))
            for layer_i, (thick, alpha_mult, color) in enumerate([
                (4, 0.5, _NS_thargoroth.PALETTE["nature_dark"]),
                (3, 0.7, _NS_thargoroth.PALETTE["nature_mid"]),
                (2, 1.0, _NS_thargoroth.PALETTE["nature_hot"]),
                (1, 1.0, _NS_thargoroth.PALETTE["nature_shine"]),
            ]):
                actual_alpha = _NS_thargoroth._alpha(alpha * alpha_mult)
                pygame.draw.ellipse(surface,
                                    (*color, actual_alpha),
                                    (x - ring_r, y - ring_r // 3,
                                     ring_r * 2, ring_r * 2 // 3), thick)
        # Sparkles flying outward
        for i in range(24):
            angle = i * math.pi / 12
            spark_dist = int(r * (0.6 + 0.4 * math.sin(phase * 3 + i)))
            sx = x + int(math.cos(angle) * spark_dist)
            sy = y + int(math.sin(angle) * spark_dist * 0.5)
            alpha = _NS_thargoroth._alpha(220)
            pygame.draw.rect(surface,
                             (*_NS_thargoroth.PALETTE["nature_hot"], alpha),
                             (sx, sy, 2, 2))
            pygame.draw.rect(surface,
                             (*_NS_thargoroth.PALETTE["nature_shine"], alpha),
                             (sx, sy, 1, 1))
        # Center bright glow
        for r_inner in range(8, 0, -1):
            alpha = _NS_thargoroth._alpha(150 * (8 - r_inner) / 8)
            _NS_thargoroth._aacircle(surface,
                                    (*_NS_thargoroth.PALETTE["nature_hot"], alpha),
                                    (x, y), r_inner)
    # ============================================================
    # SKILL R - EARTHRIFT (massive fissure with crystal spikes)
    # ============================================================
    def _draw_earthrift_ground(surface, boss, x, y, timer, phase):
        """Long ground fissure."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            return
        # Long fissure extending forward
        t = (progress - 0.2) / 0.8
        fissure_len = int(150 * min(1.0, t * 2))
        alpha = _NS_thargoroth._alpha(240 * (1 - t * 0.3))
        start_x = x + facing * 15
        end_x = x + facing * (15 + fissure_len)
        base_y = y + 44
        # Fissure zigzag
        prev_x, prev_y = start_x, base_y
        segments = fissure_len // 8
        for i in range(1, segments + 1):
            seg_t = i / segments
            seg_x = int(start_x + (end_x - start_x) * seg_t)
            seg_y = base_y + int(math.sin(seg_t * 8 + phase) * 3)
            # Fissure crack
            pygame.draw.line(surface,
                             (*_NS_thargoroth.PALETTE["shadow_deep"], alpha),
                             (prev_x, prev_y + 1), (seg_x, seg_y + 1), 4)
            pygame.draw.line(surface,
                             (*_NS_thargoroth.PALETTE["stone_darkest"], alpha),
                             (prev_x, prev_y), (seg_x, seg_y), 3)
            pygame.draw.line(surface,
                             (*_NS_thargoroth.PALETTE["nature_dark"], alpha),
                             (prev_x, prev_y), (seg_x, seg_y), 2)
            pygame.draw.line(surface,
                             (*_NS_thargoroth.PALETTE["nature_hot"], alpha),
                             (prev_x, prev_y), (seg_x, seg_y), 1)
            prev_x, prev_y = seg_x, seg_y
    def _draw_earthrift_foreground(surface, boss, x, y, timer, phase):
        """Massive line of crystal spikes erupting along fissure."""
        facing = boss.direction
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.2:
            # Warning: energy gathering at fist / ground
            t = progress / 0.2
            gather_x = x + facing * 20
            gather_y = y + 10
            cr = int(6 + t * 10)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_thargoroth._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_thargoroth._aacircle(surface,
                                        (*_NS_thargoroth.PALETTE["nature_dark"], alpha),
                                        (gather_x, gather_y), r)
            _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["nature_hot"],
                                    (gather_x, gather_y), cr - 2)
            _NS_thargoroth._aacircle(surface, _NS_thargoroth.PALETTE["nature_shine"],
                                    (gather_x, gather_y), max(1, cr - 5))
            return
        t = (progress - 0.2) / 0.8
        # Spikes erupt along a line forward
        fissure_len = int(150 * min(1.0, t * 2))
        rise_t = min(1.0, t * 2)
        fade_t = max(0, (t - 0.7) / 0.3)
        num_spikes = 10
        for i in range(num_spikes):
            spike_progress = (i + 1) / num_spikes
            if spike_progress > t * 2:
                continue  # not yet appeared
            spike_x = x + facing * int(15 + spike_progress * fissure_len)
            spike_y = y + 42
            spike_wave_offset = int(math.sin(spike_progress * 6 + phase) * 3)
            spike_y += spike_wave_offset
            # Height varies (taller at center, smaller at edges)
            spike_h = int((30 - abs(i - num_spikes / 2) * 3) * rise_t)
            if spike_h < 3:
                continue
            width = 4
            spike_tip_y = spike_y - spike_h
            mid_y = spike_y - spike_h // 2
            alpha_s = _NS_thargoroth._alpha(240 * (1 - fade_t))
            # Diamond crystal shape
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["shadow_deep"], [
                (spike_x + 1, spike_tip_y + 1),
                (spike_x + width + 1, mid_y + 1),
                (spike_x + 1, spike_y + 1),
                (spike_x - width + 1, mid_y + 1),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["nature_dark"], [
                (spike_x, spike_tip_y),
                (spike_x + width, mid_y),
                (spike_x, spike_y),
                (spike_x - width, mid_y),
            ])
            _NS_thargoroth._poly(surface, _NS_thargoroth.PALETTE["nature_mid"], [
                (spike_x, spike_tip_y + 1),
                (spike_x + width - 1, mid_y),
                (spike_x, spike_y - 1),
                (spike_x - width + 1, mid_y),
            ])
            # Bright center
            pygame.draw.line(surface, _NS_thargoroth.PALETTE["nature_hot"],
                             (spike_x, spike_tip_y + 2),
                             (spike_x, spike_y - 2), 1)
            # Bright tip
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["nature_shine"],
                             (spike_x, spike_tip_y, 1, 2))
            pygame.draw.rect(surface, _NS_thargoroth.PALETTE["white"],
                             (spike_x, spike_tip_y, 1, 1))
            # Sparks
            for s in range(2):
                sp_angle = phase * 3 + s * math.pi
                sxx = spike_x + int(math.cos(sp_angle) * (width + 2))
                syy = spike_y - spike_h // 2 + int(math.sin(sp_angle) * (spike_h // 2))
                pygame.draw.rect(surface,
                                 (*_NS_thargoroth.PALETTE["nature_hot"], alpha_s),
                                 (sxx, syy, 1, 1))



# ====================================================================
# ZAHKARETH (GOLDEN TYRANT) - Mini Boss
# ====================================================================

class _NS_zahkareth:
    """Namespace zahkareth - Golden Tyrant desert boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Dark armor (deep charcoal-black with gold accent)
        "armor_darkest": (5, 5, 8),
        "armor_dark": (18, 15, 20),
        "armor_mid": (45, 38, 45),
        "armor_light": (85, 75, 80),
        "armor_shine": (150, 135, 140),
        # Gold (main theme - chains, ornaments, sand magic)
        "gold_darkest": (30, 20, 5),
        "gold_dark": (95, 65, 15),
        "gold_mid": (200, 155, 35),
        "gold_light": (250, 215, 90),
        "gold_hot": (255, 240, 150),
        "gold_shine": (255, 250, 210),
        # Sand (dust particles, magic - warm yellow)
        "sand_dark": (80, 55, 15),
        "sand_mid": (200, 160, 60),
        "sand_light": (245, 210, 120),
        "sand_shine": (255, 240, 180),
        # Skin (pale desert warrior)
        "skin_shadow": (85, 65, 75),
        "skin_dark": (150, 115, 115),
        "skin_mid": (205, 170, 160),
        "skin_light": (235, 205, 190),
        "skin_shine": (250, 235, 220),
        # Hair (long black)
        "hair_darkest": (5, 5, 10),
        "hair_dark": (20, 20, 30),
        "hair_mid": (50, 50, 65),
        "hair_light": (110, 110, 130),
        "hair_shine": (170, 175, 195),
        # Eye (glowing yellow-gold)
        "eye_socket": (10, 8, 5),
        "eye_dark": (80, 55, 10),
        "eye_mid": (220, 170, 40),
        "eye_light": (255, 220, 100),
        "eye_glow": (255, 250, 200),
        # Metal chain (dark iron with gold sheen)
        "chain_dark": (25, 20, 25),
        "chain_mid": (75, 60, 55),
        "chain_light": (150, 130, 100),
        "chain_shine": (220, 200, 150),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 1, 2),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_zahkareth._clamp(color)
        if _NS_zahkareth.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_zahkareth._clamp(color)
        if _NS_zahkareth.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_zahkareth._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_zahkareth(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_zahkareth._detect_moving(boss)
        _NS_zahkareth._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_zkt_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_zahkareth._draw_golden_aura(surface, x, y, pulse)
        _NS_zahkareth._draw_ground_sigil(surface, x, y + 48, pulse, active_skill)
        # Ground skill FX
        if active_skill == "e":
            _NS_zahkareth._draw_sand_vortex_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zahkareth._draw_sand_prison_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (floating)
        if attacking:
            _NS_zahkareth._draw_zkt_attack(surface, boss, x, y)
        elif moving:
            _NS_zahkareth._draw_zkt_float_move(surface, boss, x, y)
        else:
            _NS_zahkareth._draw_zkt_idle(surface, boss, x, y)
        # Foreground FX
        if active_skill == "q":
            _NS_zahkareth._draw_chain_hook(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_zahkareth._draw_sand_sphere(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_zahkareth._draw_sand_vortex_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_zahkareth._draw_sand_prison_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_zkt_previous_timer", 0))
        active = bool(getattr(boss, "_zkt_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._zkt_attack_active = True
            boss._zkt_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._zkt_attack_frame = int(getattr(boss, "_zkt_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._zkt_attack_active = False
            boss._zkt_attack_frame = 0
            active = False
        boss._zkt_previous_timer = timer
        boss._zkt_attack_progress = (
            min(1.0, getattr(boss, "_zkt_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_zkt_last_x"):
            boss._zkt_last_x = boss.x
            boss._zkt_last_y = boss.y
            return False
        dx = abs(boss.x - boss._zkt_last_x)
        dy = abs(boss.y - boss._zkt_last_y)
        boss._zkt_last_x = boss.x
        boss._zkt_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_zkt_idle(surface, boss, x, y):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_zahkareth._draw_float_shadow(surface, x, y + 52, boss.pulse)
        _NS_zahkareth._draw_sand_wisps(surface, x, y + 40, boss.pulse)
        _NS_zahkareth._draw_zkt_body(surface, x, y + bob,
                                     boss.direction, boss.pulse, "idle")
    def _draw_zkt_float_move(surface, boss, x, y):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_zahkareth._draw_float_shadow(surface, x + sway, y + 52, phase)
        _NS_zahkareth._draw_sand_wisps(surface, x + sway, y + 40, phase,
                                        trail=True, facing=boss.direction)
        _NS_zahkareth._draw_zkt_body(surface, x + sway, y + bob,
                                     boss.direction, phase, "float")
    def _draw_zkt_attack(surface, boss, x, y):
        """Ranged attack - throw chain forward."""
        progress = getattr(boss, "_zkt_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind up (pull back) → throw → recovery
        if progress < 0.4:
            t = progress / 0.4
            body_shift = -int(t * 4) * boss.direction
            lift = int(t * 3)
        elif progress < 0.6:
            t = (progress - 0.4) / 0.2
            body_shift = int((-4 + t * 10)) * boss.direction
            lift = int(3 - t * 4)
        else:
            t = (progress - 0.6) / 0.4
            body_shift = int(6 * (1 - t)) * boss.direction
            lift = int(-1 + t)
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_zahkareth._draw_float_shadow(surface, x + body_shift, y + 52, boss.pulse)
        _NS_zahkareth._draw_sand_wisps(surface, x + body_shift, y + 40, boss.pulse,
                                        intense=True)
        _NS_zahkareth._draw_zkt_body(surface, x + body_shift, y - lift + bob,
                                     boss.direction, boss.pulse, "attack", progress)
        # Chain-hook projectile
        _NS_zahkareth._draw_chain_projectile(surface, boss, x + body_shift,
                                              y - lift + bob, progress)
    # ============================================================
    # BODY - Golden Tyrant
    # ============================================================
    def _draw_zkt_body(surface, cx, cy, facing, phase, action, attack_progress=0):
        """Tyrant body: robe, torso, arms with chains, head with long hair."""
        # Floating chains behind body (decorative)
        _NS_zahkareth._draw_floating_chains_back(surface, cx, cy, facing, phase)
        # Robe/coat bottom
        _NS_zahkareth._draw_royal_robe(surface, cx, cy + 6, facing, phase)
        # Long hair behind
        _NS_zahkareth._draw_long_hair(surface, cx, cy - 22, facing, phase)
        # Torso armor
        _NS_zahkareth._draw_tyrant_torso(surface, cx, cy - 4, facing, phase)
        # Arms (with chains at hand for Q signature)
        chain_swing = 0
        if action == "attack":
            if attack_progress < 0.4:
                chain_swing = -int(attack_progress / 0.4 * 8) * facing
            elif attack_progress < 0.6:
                t = (attack_progress - 0.4) / 0.2
                chain_swing = int((-8 + t * 18)) * facing
            else:
                t = (attack_progress - 0.6) / 0.4
                chain_swing = int(10 * (1 - t)) * facing
        # Back arm
        _NS_zahkareth._draw_back_arm(surface, cx, cy - 2, facing, phase)
        # Front arm holding chain end
        _NS_zahkareth._draw_front_arm_chain(surface, cx, cy - 2, facing, phase,
                                             chain_swing, action, attack_progress)
        # Head + face
        _NS_zahkareth._draw_tyrant_head(surface, cx, cy - 24, facing, phase, action)
    def _draw_floating_chains_back(surface, cx, cy, facing, phase):
        """Long golden chains floating around body (signature Khufra effect)."""
        back = -facing
        # Multiple large chain loops floating behind body
        for chain_i in range(3):
            # Each chain loop at different position
            loop_center_x = cx + back * (10 + chain_i * 8)
            loop_center_y = cy - 6 + chain_i * 8
            loop_r = 18 + chain_i * 3
            # Chain forms a circular loop with wave animation
            num_links = 12
            for link_i in range(num_links):
                link_angle = link_i * math.pi * 2 / num_links + phase * 0.5 + chain_i * 0.5
                # Wobbling loop
                lx = loop_center_x + int(math.cos(link_angle) * loop_r)
                ly = loop_center_y + int(math.sin(link_angle) * loop_r * 0.6)
                ly += int(math.sin(phase * 2 + link_i) * 2)
                # Chain link (alternating dark/light for chain texture)
                if link_i % 2 == 0:
                    _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                                            (lx + 1, ly + 1), 3)
                    _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_darkest"],
                                            (lx, ly), 3)
                    _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                            (lx, ly), 2)
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                     (lx, ly - 1, 1, 1))
                else:
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                                     (lx - 1, ly - 1, 4, 4))
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                     (lx - 1, ly - 1, 3, 3))
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                     (lx - 1, ly - 1, 3, 2))
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                                     (lx, ly - 1, 1, 1))
    def _draw_royal_robe(surface, cx, cy, facing, phase):
        """Dark robe with gold accents."""
        wave1 = math.sin(phase * 0.6) * 3
        wave2 = math.sin(phase * 0.6 + 1.5) * 3
        robe_pts = [
            (cx - 10, cy),
            (cx + 10, cy),
            (cx + 14, cy + 10),
            (cx + 18 + int(wave1), cy + 22),
            (cx + 20 + int(wave2), cy + 34),
            (cx + 16, cy + 44),
            (cx + 8, cy + 48),
            (cx - 8, cy + 48),
            (cx - 16, cy + 44),
            (cx - 20 + int(wave1), cy + 34),
            (cx - 18 + int(wave2), cy + 22),
            (cx - 14, cy + 10),
        ]
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in robe_pts])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["armor_darkest"], robe_pts)
        # Second layer
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["armor_dark"], [
            (cx - 9, cy + 2),
            (cx + 9, cy + 2),
            (cx + 12, cy + 12),
            (cx + 16 + int(wave1 * 0.7), cy + 24),
            (cx + 17 + int(wave2 * 0.7), cy + 34),
            (cx + 12, cy + 42),
            (cx - 12, cy + 42),
            (cx - 17 + int(wave2 * 0.7), cy + 34),
            (cx - 16 + int(wave1 * 0.7), cy + 24),
            (cx - 12, cy + 12),
        ])
        # Mid highlight
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["armor_mid"], [
            (cx - 7, cy + 4),
            (cx + 7, cy + 4),
            (cx + 10, cy + 16),
            (cx + 12, cy + 30),
            (cx + 6, cy + 40),
            (cx - 6, cy + 40),
            (cx - 12, cy + 30),
            (cx - 10, cy + 16),
        ])
        # Gold trim details
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # Central gold stripe running down
        for i, y_off in enumerate((8, 16, 24, 32, 40)):
            alpha = _NS_zahkareth._alpha(220 * pulse)
            pygame.draw.line(surface, _NS_zahkareth.PALETTE["gold_dark"],
                             (cx - 1, cy + y_off), (cx + 1, cy + y_off), 1)
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                             (cx, cy + y_off, 1, 1))
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_shine"],
                             (cx, cy + y_off, 1, 1))
        # Gold trim at bottom edges
        for rx in (-16, -8, 0, 8, 16):
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_dark"],
                             (cx + rx - 1, cy + 44, 3, 2))
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                             (cx + rx, cy + 44, 1, 1))
        # Gold ornamental stripes on sides
        for side in (-1, 1):
            for y_pos in (10, 20, 30):
                pygame.draw.line(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                 (cx + side * 6, cy + y_pos),
                                 (cx + side * 10, cy + y_pos), 1)
                pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                 (cx + side * 8, cy + y_pos, 1, 1))
        # Sand particles rising from robe
        for i in range(6):
            spark_t = (phase * 0.5 + i * 0.16) % 1.0
            sx = cx - 10 + int((i % 3) * 10) + int(math.sin(phase + i) * 2)
            sy = cy + 14 + int(spark_t * 32)
            alpha = _NS_zahkareth._alpha(220 * (1 - spark_t))
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["sand_light"], (sx, sy, 1, 1))
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["sand_shine"], (sx, sy, 1, 1))
    def _draw_tyrant_torso(surface, cx, cy, facing, phase):
        """Muscular armored torso with gold ornaments."""
        # Torso base (broad V-shape)
        torso_pts = [
            (cx - 11, cy - 6),
            (cx + 11, cy - 6),
            (cx + 12, cy),
            (cx + 10, cy + 6),
            (cx + 8, cy + 10),
            (cx - 8, cy + 10),
            (cx - 10, cy + 6),
            (cx - 12, cy),
        ]
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_pts])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["armor_darkest"], torso_pts)
        # Armor plates
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["armor_dark"], [
            (cx - 10, cy - 5),
            (cx + 10, cy - 5),
            (cx + 11, cy),
            (cx + 9, cy + 5),
            (cx + 7, cy + 9),
            (cx - 7, cy + 9),
            (cx - 9, cy + 5),
            (cx - 11, cy),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["armor_mid"], [
            (cx - 8, cy - 4),
            (cx + 8, cy - 4),
            (cx + 9, cy),
            (cx + 6, cy + 5),
            (cx - 6, cy + 5),
            (cx - 9, cy),
        ])
        # Skin peek (V-cut chest under armor)
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["skin_shadow"], [
            (cx - 4, cy - 5),
            (cx + 4, cy - 5),
            (cx + 3, cy - 2),
            (cx, cy + 2),
            (cx - 3, cy - 2),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["skin_dark"], [
            (cx - 3, cy - 4),
            (cx + 3, cy - 4),
            (cx + 2, cy - 1),
            (cx, cy + 1),
            (cx - 2, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["skin_mid"],
                         (cx - 1, cy - 3, 3, 1))
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["skin_light"],
                         (cx, cy - 3, 1, 1))
        # Chest gold ornament (Egyptian-style pectoral)
        pulse = math.sin(phase * 2.5) * 0.3 + 0.7
        # Big gold curved chest piece
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["shadow_deep"], [
            (cx - 8, cy - 1),
            (cx + 8, cy - 1),
            (cx + 10, cy + 3),
            (cx, cy + 8),
            (cx - 10, cy + 3),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_darkest"], [
            (cx - 8, cy - 2),
            (cx + 8, cy - 2),
            (cx + 10, cy + 2),
            (cx, cy + 7),
            (cx - 10, cy + 2),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_dark"], [
            (cx - 7, cy - 1),
            (cx + 7, cy - 1),
            (cx + 9, cy + 2),
            (cx, cy + 6),
            (cx - 9, cy + 2),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_mid"], [
            (cx - 5, cy),
            (cx + 5, cy),
            (cx + 7, cy + 2),
            (cx, cy + 5),
            (cx - 7, cy + 2),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_light"], [
            (cx - 3, cy + 1),
            (cx + 3, cy + 1),
            (cx + 4, cy + 2),
            (cx, cy + 4),
            (cx - 4, cy + 2),
        ])
        # Central gem (glowing gold/amber)
        for r in range(5, 0, -1):
            alpha = _NS_zahkareth._alpha(200 * (5 - r) / 5 * pulse)
            _NS_zahkareth._aacircle(surface,
                                    (*_NS_zahkareth.PALETTE["gold_hot"], alpha),
                                    (cx, cy + 3), r)
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_dark"],
                         (cx - 1, cy + 2, 3, 3))
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                         (cx - 1, cy + 2, 2, 2))
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_hot"],
                         (cx, cy + 3, 1, 1))
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_shine"],
                         (cx, cy + 3, 1, 1))
        # Shoulder pauldrons (curved, gold-trimmed)
        for side in (-1, 1):
            _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["shadow_deep"], [
                (cx + side * 9, cy - 7),
                (cx + side * 16, cy - 5),
                (cx + side * 17, cy + 1),
                (cx + side * 13, cy + 3),
                (cx + side * 9, cy),
            ])
            _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["armor_darkest"], [
                (cx + side * 9, cy - 8),
                (cx + side * 15, cy - 6),
                (cx + side * 16, cy + 1),
                (cx + side * 12, cy + 2),
                (cx + side * 9, cy - 1),
            ])
            _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["armor_dark"], [
                (cx + side * 10, cy - 6),
                (cx + side * 14, cy - 5),
                (cx + side * 15, cy),
                (cx + side * 11, cy + 1),
            ])
            _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["armor_mid"], [
                (cx + side * 11, cy - 5),
                (cx + side * 13, cy - 4),
                (cx + side * 14, cy - 1),
                (cx + side * 12, cy),
            ])
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["armor_light"],
                             (cx + side * 12, cy - 4, 2, 1))
            # Gold trim on pauldron
            pygame.draw.line(surface, _NS_zahkareth.PALETTE["gold_dark"],
                             (cx + side * 10, cy - 6),
                             (cx + side * 14, cy - 6), 1)
            pygame.draw.line(surface, _NS_zahkareth.PALETTE["gold_light"],
                             (cx + side * 11, cy - 6),
                             (cx + side * 13, cy - 6), 1)
            # Gold decorative dot
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                             (cx + side * 12, cy - 3, 1, 1))
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_shine"],
                             (cx + side * 12, cy - 3, 1, 1))
    def _draw_front_arm_chain(surface, cx, cy, facing, phase, chain_swing, action,
                                attack_progress):
        """Front arm holding chain."""
        wave = math.sin(phase * 0.7) * 1
        shoulder_x = cx + facing * 10
        shoulder_y = cy - 2
        # Hand position varies with attack
        if action == "attack":
            if attack_progress < 0.4:
                # Wind up - hand goes back and up
                t = attack_progress / 0.4
                hand_x = int(cx + facing * (8 - t * 10))
                hand_y = int(cy - t * 6)
            elif attack_progress < 0.6:
                # Throw forward
                t = (attack_progress - 0.4) / 0.2
                hand_x = int(cx + facing * (-2 + t * 22))
                hand_y = int(cy - 6 + t * 10)
            else:
                # Recovery extended
                t = (attack_progress - 0.6) / 0.4
                hand_x = int(cx + facing * (20 - t * 6))
                hand_y = int(cy + 4 - t * 2)
        else:
            hand_x = cx + facing * 16
            hand_y = cy + 6 + int(wave)
        elbow_x = (shoulder_x + hand_x) // 2 + facing
        elbow_y = (shoulder_y + hand_y) // 2 + 2
        # Upper arm (armored)
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 1),
                              (elbow_x + 1, elbow_y + 1), 5)
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["armor_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["armor_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["armor_mid"],
                              (shoulder_x, shoulder_y - 1),
                              (elbow_x, elbow_y - 1), 2)
        # Gold bracer at elbow
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_dark"],
                         (elbow_x - 2, elbow_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                         (elbow_x - 2, elbow_y - 1, 4, 2))
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                         (elbow_x - 1, elbow_y - 1, 2, 1))
        # Forearm
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1),
                              (hand_x + 1, hand_y + 1), 5)
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["armor_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 4)
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["armor_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        # Gold wrist bracer
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_dark"],
                         (hand_x - facing * 3 - 1, hand_y - 1, 4, 3))
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                         (hand_x - facing * 3 - 1, hand_y - 1, 4, 2))
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                         (hand_x - facing * 3, hand_y - 1, 2, 1))
        # Hand (with clawed grip)
        _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                                (hand_x + 1, hand_y + 1), 3)
        _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["armor_darkest"],
                                (hand_x, hand_y), 3)
        _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["armor_dark"],
                                (hand_x, hand_y), 2)
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                         (hand_x, hand_y - 1, 1, 1))
        # HOLD CHAIN in hand (visible when not throwing)
        show_chain = True
        if action == "attack" and 0.45 < attack_progress < 0.9:
            show_chain = False  # chain being thrown = projectile
        if show_chain:
            _NS_zahkareth._draw_hand_chain(surface, hand_x, hand_y, facing, phase)
    def _draw_hand_chain(surface, hand_x, hand_y, facing, phase):
        """Chain dangling from hand (idle state)."""
        # Chain drapes down from hand with slight swing
        wave = math.sin(phase * 1.5) * 3
        prev_x = hand_x
        prev_y = hand_y + 2
        for i in range(6):
            t = i / 5
            drop_x = prev_x + int(math.sin(phase * 1.2 + i * 0.5) * 2) - facing
            drop_y = prev_y + 4
            # Chain link
            if i % 2 == 0:
                _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                                        (drop_x + 1, drop_y + 1), 2)
                _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_darkest"],
                                        (drop_x, drop_y), 2)
                _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                        (drop_x, drop_y), 1)
                pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                 (drop_x, drop_y, 1, 1))
            else:
                pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                 (drop_x - 1, drop_y - 1, 3, 3))
                pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                 (drop_x - 1, drop_y - 1, 3, 2))
                pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                                 (drop_x, drop_y - 1, 1, 1))
            prev_x = drop_x
            prev_y = drop_y
        # HOOK at end (curved spike)
        hook_x = prev_x
        hook_y = prev_y + 4
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["shadow_deep"], [
            (hook_x + 1, hook_y - 2 + 1),
            (hook_x - 3 + 1, hook_y + 3 + 1),
            (hook_x + 3 + 1, hook_y + 3 + 1),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_dark"], [
            (hook_x, hook_y - 3),
            (hook_x - 3, hook_y + 2),
            (hook_x + 3, hook_y + 2),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_mid"], [
            (hook_x, hook_y - 2),
            (hook_x - 2, hook_y + 2),
            (hook_x + 2, hook_y + 2),
        ])
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                         (hook_x, hook_y - 2, 1, 1))
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_shine"],
                         (hook_x, hook_y - 2, 1, 1))
    def _draw_back_arm(surface, cx, cy, facing, phase):
        """Back arm (partial visibility)."""
        wave = math.sin(phase * 0.7) * 1
        shoulder_x = cx - facing * 8
        shoulder_y = cy - 2
        elbow_x = cx - facing * 12
        elbow_y = cy + 4 + int(wave)
        hand_x = cx - facing * 8
        hand_y = cy + 10 + int(wave)
        # Upper arm
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                              (shoulder_x + 1, shoulder_y + 1),
                              (elbow_x + 1, elbow_y + 1), 4)
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["armor_darkest"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["armor_dark"],
                              (shoulder_x, shoulder_y), (elbow_x, elbow_y), 2)
        # Bracer
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_dark"],
                         (elbow_x - 1, elbow_y - 1, 3, 3))
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                         (elbow_x - 1, elbow_y - 1, 3, 2))
        # Forearm
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                              (elbow_x + 1, elbow_y + 1),
                              (hand_x + 1, hand_y + 1), 4)
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["armor_darkest"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_zahkareth._aaline(surface, _NS_zahkareth.PALETTE["armor_dark"],
                              (elbow_x, elbow_y), (hand_x, hand_y), 2)
        # Fist
        _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["armor_darkest"],
                                (hand_x, hand_y), 2)
        _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["armor_dark"],
                                (hand_x, hand_y), 1)
    def _draw_long_hair(surface, cx, cy, facing, phase):
        """Long black flowing hair (Khufra-style)."""
        wave1 = math.sin(phase * 0.6) * 3
        wave2 = math.sin(phase * 0.6 + 1.5) * 3
        # Hair mass behind head
        hair_pts = [
            (cx - 7, cy),
            (cx + 7, cy),
            (cx + 10, cy + 8),
            (cx + 12 + int(wave1), cy + 18),
            (cx + 10 + int(wave2), cy + 28),
            (cx + 4, cy + 36),
            (cx - 4, cy + 36),
            (cx - 10 + int(wave2), cy + 28),
            (cx - 12 + int(wave1), cy + 18),
            (cx - 10, cy + 8),
        ]
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in hair_pts])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["hair_darkest"], hair_pts)
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["hair_dark"], [
            (cx - 6, cy + 2),
            (cx + 6, cy + 2),
            (cx + 8, cy + 10),
            (cx + 9 + int(wave1 * 0.7), cy + 20),
            (cx + 7, cy + 28),
            (cx - 7, cy + 28),
            (cx - 9 + int(wave1 * 0.7), cy + 20),
            (cx - 8, cy + 10),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["hair_mid"], [
            (cx - 4, cy + 4),
            (cx + 4, cy + 4),
            (cx + 6, cy + 12),
            (cx + 4, cy + 22),
            (cx - 4, cy + 22),
            (cx - 6, cy + 12),
        ])
        # Hair strand highlights
        for i, x_off in enumerate((-5, -1, 3)):
            strand_x = cx + x_off + int(math.sin(phase * 0.7 + i) * 2)
            pygame.draw.line(surface, _NS_zahkareth.PALETTE["hair_light"],
                             (strand_x, cy + 6),
                             (strand_x + int(math.sin(phase + i)), cy + 24), 1)
    def _draw_tyrant_head(surface, cx, cy, facing, phase, action):
        """Sinister head with pale skin, dark bangs, glowing gold eyes."""
        # Face shape
        face_pts = [
            (cx - 5, cy - 4),
            (cx + 5, cy - 4),
            (cx + 6, cy),
            (cx + 5, cy + 4),
            (cx + 2, cy + 7),
            (cx - 2, cy + 7),
            (cx - 5, cy + 4),
            (cx - 6, cy),
        ]
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                            [(px + 1, py + 2) for px, py in face_pts])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["skin_shadow"], face_pts)
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["skin_dark"], [
            (cx - 4, cy - 4),
            (cx + 4, cy - 4),
            (cx + 5, cy),
            (cx + 4, cy + 3),
            (cx + 2, cy + 6),
            (cx - 2, cy + 6),
            (cx - 4, cy + 3),
            (cx - 5, cy),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["skin_mid"], [
            (cx - 3, cy - 3),
            (cx + 3, cy - 3),
            (cx + 4, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
            (cx - 4, cy),
        ])
        # Highlight
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["skin_light"],
                         (cx - 1, cy - 2, 3, 2))
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["skin_shine"],
                         (cx, cy - 2, 1, 1))
        # HAIR BANGS (dark, falling over forehead)
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["hair_darkest"], [
            (cx - 6, cy - 5),
            (cx + 6, cy - 5),
            (cx + 5, cy - 2),
            (cx + 2, cy),
            (cx - 2, cy),
            (cx - 5, cy - 2),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["hair_dark"], [
            (cx - 5, cy - 4),
            (cx + 5, cy - 4),
            (cx + 4, cy - 2),
            (cx + 1, cy - 1),
            (cx - 1, cy - 1),
            (cx - 4, cy - 2),
        ])
        # Bang highlight
        pygame.draw.line(surface, _NS_zahkareth.PALETTE["hair_light"],
                         (cx - 3, cy - 3), (cx - 1, cy - 1), 1)
        pygame.draw.line(surface, _NS_zahkareth.PALETTE["hair_light"],
                         (cx + 1, cy - 3), (cx + 3, cy - 1), 1)
        # GLOWING GOLD EYES (sinister)
        _NS_zahkareth._draw_gold_eyes(surface, cx, cy - 1, facing, phase)
        # Sharp cheekbones (subtle shadow)
        pygame.draw.line(surface, _NS_zahkareth.PALETTE["skin_shadow"],
                         (cx - 4, cy + 2), (cx - 3, cy + 4), 1)
        pygame.draw.line(surface, _NS_zahkareth.PALETTE["skin_shadow"],
                         (cx + 3, cy + 2), (cx + 4, cy + 4), 1)
        # Nose (subtle)
        pygame.draw.line(surface, _NS_zahkareth.PALETTE["skin_shadow"],
                         (cx, cy + 2), (cx, cy + 4), 1)
        # Cruel smile / stern lips
        pygame.draw.line(surface, _NS_zahkareth.PALETTE["skin_shadow"],
                         (cx - 2, cy + 5), (cx + 2, cy + 5), 1)
    def _draw_gold_eyes(surface, cx, cy, facing, phase):
        """Two glowing gold/yellow eyes."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        for eye_off in (-2, 2):
            ex = cx + eye_off
            ey = cy
            # Socket
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                             (ex - 1, ey - 1, 2, 2))
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["eye_socket"],
                             (ex - 1, ey - 1, 2, 2))
            # Glow halo
            for r in range(5, 0, -1):
                alpha = _NS_zahkareth._alpha(140 * (5 - r) / 5 * pulse)
                _NS_zahkareth._aacircle(surface,
                                        (*_NS_zahkareth.PALETTE["eye_mid"], alpha),
                                        (ex, ey), r)
            # Core
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["eye_dark"],
                             (ex - 1, ey, 2, 1))
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["eye_mid"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["eye_light"],
                             (ex, ey, 1, 1))
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["eye_glow"],
                             (ex, ey, 1, 1))
    # ============================================================
    # BASIC ATTACK - CHAIN PROJECTILE (throw hook forward)
    # ============================================================
    def _draw_chain_projectile(surface, boss, x, y, progress):
        """Chain with hook flying to target."""
        if progress < 0.5:
            return
        facing = boss.direction
        tx, ty = _NS_zahkareth._target_position(boss, x, y)
        start_x = x + facing * 22
        start_y = y - 2
        t = (progress - 0.5) / 0.5
        t = min(1.0, t)
        end_x = int(start_x + (tx - start_x) * t)
        end_y = int(start_y + (ty - start_y) * t)
        # Draw chain from source to current end position
        segments = int(15 * t)
        prev_x, prev_y = start_x, start_y
        for i in range(1, segments + 1):
            seg_t = i / max(1, segments)
            cx_c = int(start_x + (end_x - start_x) * seg_t)
            cy_c = int(start_y + (end_y - start_y) * seg_t)
            # Slight sag/wave
            sag = math.sin(seg_t * math.pi) * 3
            cy_c += int(sag)
            # Chain link
            if i % 2 == 0:
                _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                                        (cx_c + 1, cy_c + 1), 3)
                _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_darkest"],
                                        (cx_c, cy_c), 3)
                _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                        (cx_c, cy_c), 2)
                pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                 (cx_c, cy_c, 1, 1))
                pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                                 (cx_c, cy_c, 1, 1))
            else:
                pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                 (cx_c - 1, cy_c - 1, 3, 3))
                pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                 (cx_c - 1, cy_c - 1, 3, 2))
        # HOOK at end
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["shadow_deep"], [
            (end_x + facing * 5 + 1, end_y + 1),
            (end_x - facing * 2 + 1, end_y - 3 + 1),
            (end_x - facing * 2 + 1, end_y + 3 + 1),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_darkest"], [
            (end_x + facing * 5, end_y),
            (end_x - facing * 2, end_y - 3),
            (end_x - facing * 2, end_y + 3),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_dark"], [
            (end_x + facing * 4, end_y),
            (end_x - facing * 1, end_y - 2),
            (end_x - facing * 1, end_y + 2),
        ])
        _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_mid"], [
            (end_x + facing * 3, end_y),
            (end_x, end_y - 1),
            (end_x, end_y + 1),
        ])
        # Bright hook tip
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                         (end_x + facing * 4, end_y, 1, 1))
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_shine"],
                         (end_x + facing * 4, end_y, 1, 1))
        # Sparks near hook
        for i in range(3):
            angle = phase_offset = i * math.pi / 1.5 + t * 4
            sx = end_x + int(math.cos(angle) * 5) * facing
            sy = end_y + int(math.sin(angle) * 5)
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_shine"], (sx, sy, 1, 1))
        # Impact
        if t > 0.9:
            st = (t - 0.9) / 0.1
            radius = int(8 + st * 15)
            alpha = _NS_zahkareth._alpha(230 * (1 - st))
            _NS_zahkareth._aacircle(surface, (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                                    (tx, ty), radius + 3, 2)
            _NS_zahkareth._aacircle(surface, (*_NS_zahkareth.PALETTE["gold_mid"], alpha),
                                    (tx, ty), radius, 1)
            _NS_zahkareth._aacircle(surface, (*_NS_zahkareth.PALETTE["gold_hot"], alpha),
                                    (tx, ty), max(1, radius - 4))
            for i in range(8):
                angle_s = i * math.pi / 4
                ex = tx + int(math.cos(angle_s) * radius)
                ey = ty + int(math.sin(angle_s) * radius * 0.7)
                pygame.draw.rect(surface, (*_NS_zahkareth.PALETTE["gold_shine"], alpha),
                                 (ex, ey, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = _NS_zahkareth._alpha((14 - radius) * 15 * pulse)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius // 2,
                 120 + radius * 2, radius),
            )
        pygame.draw.ellipse(shadow, (15, 10, 5, 170), (10, 10, 120, 10))
        pygame.draw.ellipse(shadow, (80, 60, 15, 100), (18, 12, 104, 6))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_sand_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Golden sand particles below boss."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(34, 3, -3):
            alpha = _NS_zahkareth._alpha((34 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_zahkareth.PALETTE["gold_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(22, 3, -2):
            alpha = _NS_zahkareth._alpha((22 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising sand particles
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_zahkareth._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_zahkareth._aacircle(surface,
                                    (*_NS_zahkareth.PALETTE["sand_dark"], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_zahkareth.PALETTE["sand_light"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_zahkareth.PALETTE["sand_shine"], alpha),
                             (sx, sy - 2, 1, 1))
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_zahkareth._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_zahkareth._aacircle(surface,
                                        (*_NS_zahkareth.PALETTE["gold_darkest"], alpha),
                                        (sx, sy), max(2, 7 - i))
                _NS_zahkareth._aacircle(surface,
                                        (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                                        (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface,
                                 (*_NS_zahkareth.PALETTE["gold_hot"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_golden_aura(surface, x, y, phase):
        """Massive golden aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 210), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_zahkareth._alpha((100 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_zahkareth._aacircle(aura,
                                        (*_NS_zahkareth.PALETTE["gold_darkest"], alpha),
                                        (120, 105), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_zahkareth._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_zahkareth._aacircle(aura,
                                        (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                                        (120, 105), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_zahkareth._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_zahkareth._aacircle(aura,
                                        (*_NS_zahkareth.PALETTE["gold_mid"], alpha),
                                        (120, 105), radius)
        surface.blit(aura, (x - 120, y - 105))
        # Floating golden embers
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 42 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_zahkareth.PALETTE["gold_hot"] if i % 2 == 0 \
                else _NS_zahkareth.PALETTE["sand_light"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_shine"], (sx, sy, 1, 1))
    def _draw_ground_sigil(surface, x, y, phase, skill):
        """Golden sigil ring on ground."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 58), pygame.SRCALPHA)
        for i, (rw, rh, alpha) in enumerate([
            (82, 24, 200), (68, 20, 220), (54, 15, 220), (40, 11, 200),
        ]):
            offset = int(math.sin(phase * 1.5 + i * 0.5) * 2)
            pygame.draw.ellipse(ring,
                                (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                                (90 - rw + offset, 29 - rh, rw * 2, rh * 2), 2)
            pygame.draw.ellipse(ring,
                                (*_NS_zahkareth.PALETTE["gold_mid"], alpha),
                                (90 - rw + offset + 1, 29 - rh + 1,
                                 rw * 2 - 2, rh * 2 - 2), 1)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 29 + int(math.sin(angle) * 10)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 29 + int(math.sin(angle) * 14)
            pygame.draw.line(ring,
                             (*_NS_zahkareth.PALETTE["gold_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_zahkareth.PALETTE["gold_light"],
                                 _NS_zahkareth._alpha(180 * pulse)),
                                (15, 12, 150, 34), 1)
        surface.blit(ring, (x - 90, y - 29))
    # ============================================================
    # SKILL Q - CHAIN HOOK (long chain grabs target and pulls)
    # ============================================================
    def _draw_chain_hook(surface, boss, x, y, timer, phase):
        """Extended chain that grabs target and pulls."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zahkareth._target_position(boss, x, y)
        start_x = x + facing * 22
        start_y = y - 2
        if progress < 0.2:
            # Wind up glow
            t = progress / 0.2
            hand_x = x + facing * 20
            hand_y = y
            cr = int(4 + t * 8)
            for r in range(cr + 4, 0, -1):
                alpha = _NS_zahkareth._alpha(200 * (cr + 4 - r) / (cr + 4))
                _NS_zahkareth._aacircle(surface,
                                        (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_hot"],
                                    (hand_x, hand_y), cr - 2)
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_shine"],
                                    (hand_x, hand_y), max(1, cr - 4))
        elif progress < 0.55:
            # CHAIN EXTENDS to target (throw phase)
            t = (progress - 0.2) / 0.35
            end_x = int(start_x + (tx - start_x) * t)
            end_y = int(start_y + (ty - start_y) * t)
            # Draw chain segments
            segments = 18
            for i in range(1, int(segments * t) + 1):
                seg_t = i / segments
                if seg_t > t:
                    break
                cx_c = int(start_x + (tx - start_x) * seg_t)
                cy_c = int(start_y + (ty - start_y) * seg_t)
                sag = math.sin(seg_t * math.pi) * 4
                cy_c += int(sag)
                if i % 2 == 0:
                    _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                                            (cx_c + 1, cy_c + 1), 4)
                    _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_darkest"],
                                            (cx_c, cy_c), 4)
                    _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                            (cx_c, cy_c), 3)
                    _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                            (cx_c, cy_c), 2)
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                                     (cx_c, cy_c - 1, 1, 1))
                else:
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                                     (cx_c - 2, cy_c - 2, 5, 5))
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_darkest"],
                                     (cx_c - 2, cy_c - 2, 4, 4))
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                     (cx_c - 1, cy_c - 1, 3, 3))
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                     (cx_c - 1, cy_c - 1, 3, 2))
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                                     (cx_c, cy_c - 1, 1, 1))
            # BIG HOOK at end
            angle_to = math.atan2(ty - start_y, tx - start_x)
            hook_forward_x = int(math.cos(angle_to) * 6)
            hook_forward_y = int(math.sin(angle_to) * 6)
            hook_perp_x = int(-math.sin(angle_to) * 3)
            hook_perp_y = int(math.cos(angle_to) * 3)
            _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["shadow_deep"], [
                (end_x + hook_forward_x + 1, end_y + hook_forward_y + 1),
                (end_x + hook_perp_x + 1, end_y + hook_perp_y + 1),
                (end_x - hook_perp_x + 1, end_y - hook_perp_y + 1),
            ])
            _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_darkest"], [
                (end_x + hook_forward_x, end_y + hook_forward_y),
                (end_x + hook_perp_x, end_y + hook_perp_y),
                (end_x - hook_perp_x, end_y - hook_perp_y),
            ])
            _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_dark"], [
                (end_x + hook_forward_x, end_y + hook_forward_y),
                (end_x + hook_perp_x // 2, end_y + hook_perp_y // 2),
                (end_x - hook_perp_x // 2, end_y - hook_perp_y // 2),
            ])
            _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_mid"], [
                (end_x + hook_forward_x, end_y + hook_forward_y),
                (end_x, end_y),
                (end_x - hook_perp_x // 3, end_y - hook_perp_y // 3),
            ])
            # Bright hook tip
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                             (end_x + hook_forward_x, end_y + hook_forward_y, 1, 1))
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_shine"],
                             (end_x + hook_forward_x, end_y + hook_forward_y, 1, 1))
            # Bright glow around hook
            for r in range(6, 0, -1):
                alpha = _NS_zahkareth._alpha(180 * (6 - r) / 6)
                _NS_zahkareth._aacircle(surface,
                                        (*_NS_zahkareth.PALETTE["gold_hot"], alpha),
                                        (end_x, end_y), r)
        else:
            # PULL BACK phase: chain reels in
            t = (progress - 0.55) / 0.45
            # Static chain returning
            segments = 18
            for i in range(1, segments + 1):
                seg_t = i / segments
                cx_c = int(start_x + (tx - start_x) * seg_t)
                cy_c = int(start_y + (ty - start_y) * seg_t)
                sag = math.sin(seg_t * math.pi) * (4 * (1 - t))
                cy_c += int(sag)
                if i % 2 == 0:
                    _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_darkest"],
                                            (cx_c, cy_c), 3)
                    _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                            (cx_c, cy_c), 2)
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                     (cx_c, cy_c, 1, 1))
                else:
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                     (cx_c - 1, cy_c - 1, 3, 3))
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                     (cx_c - 1, cy_c - 1, 3, 2))
            # Pull impact at target
            pull_r = int(10 + t * 20)
            alpha = _NS_zahkareth._alpha(220 * (1 - t))
            _NS_zahkareth._aacircle(surface, (*_NS_zahkareth.PALETTE["gold_darkest"], alpha),
                                    (tx, ty), pull_r + 3, 3)
            _NS_zahkareth._aacircle(surface, (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                                    (tx, ty), pull_r, 2)
            _NS_zahkareth._aacircle(surface, (*_NS_zahkareth.PALETTE["gold_hot"], alpha),
                                    (tx, ty), max(1, pull_r - 6), 1)
            # Arrows pointing toward boss (pull direction)
            angle_pull = math.atan2(start_y - ty, start_x - tx)
            for i in range(4):
                offset_angle = angle_pull + (i - 1.5) * 0.3
                arrow_x = tx + int(math.cos(offset_angle) * pull_r * 0.7)
                arrow_y = ty + int(math.sin(offset_angle) * pull_r * 0.7)
                pygame.draw.line(surface, (*_NS_zahkareth.PALETTE["gold_hot"], alpha),
                                 (arrow_x, arrow_y),
                                 (arrow_x + int(math.cos(offset_angle) * 6),
                                  arrow_y + int(math.sin(offset_angle) * 6)), 2)
    # ============================================================
    # SKILL W - SAND SPHERE (bouncing ball projectile)
    # ============================================================
    def _draw_sand_sphere(surface, boss, x, y, timer, phase):
        """Golden sand sphere bouncing toward target."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_zahkareth._target_position(boss, x, y)
        if progress < 0.15:
            # Charge glow at hand
            t = progress / 0.15
            hand_x = x + facing * 22
            hand_y = y - 2
            cr = int(6 + t * 10)
            for r in range(cr + 6, 0, -1):
                alpha = _NS_zahkareth._alpha(200 * (cr + 6 - r) / (cr + 6))
                _NS_zahkareth._aacircle(surface,
                                        (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                    (hand_x, hand_y), cr - 2)
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_hot"],
                                    (hand_x, hand_y), max(1, cr - 4))
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_shine"],
                                    (hand_x, hand_y), max(1, cr - 6))
        else:
            # BOUNCING BALL trajectory
            t = (progress - 0.15) / 0.85
            start_x = x + facing * 24
            start_y = y - 2
            # Ball position: parabolic bounces
            # 3 bounces on the way to target
            num_bounces = 3
            bounce_progress = t * num_bounces
            bounce_index = int(bounce_progress)
            bounce_t = bounce_progress - bounce_index
            # Interpolate horizontal position (linear from start to target)
            bx = int(start_x + (tx - start_x) * t)
            # Vertical: parabolic arc for each bounce
            base_y_at_t = int(start_y + (ty - start_y) * t)
            bounce_height = 30 - bounce_index * 5  # each bounce lower
            bounce_y_offset = -int(math.sin(bounce_t * math.pi) * bounce_height)
            by = base_y_at_t + bounce_y_offset
            # Ball itself (golden sand sphere)
            ball_r = 8
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            # Shadow underneath
            shadow_y = base_y_at_t + 20
            pygame.draw.ellipse(surface, (*_NS_zahkareth.PALETTE["shadow_deep"], 120),
                                (bx - ball_r, shadow_y - 2, ball_r * 2, 4))
            # Ball layers (sand ball)
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["shadow_deep"],
                                    (bx + 2, by + 2), ball_r + 1)
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_darkest"],
                                    (bx, by), ball_r + 1)
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                    (bx, by), ball_r)
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_mid"],
                                    (bx, by), ball_r - 2)
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_hot"],
                                    (bx, by - 1), ball_r - 4)
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_shine"],
                                    (bx - 1, by - 2), 2)
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["white"],
                             (bx - 1, by - 2, 1, 1))
            # Sand texture cracks on ball
            for i in range(4):
                crack_angle = i * math.pi / 2 + phase
                cx1 = bx + int(math.cos(crack_angle) * 3)
                cy1 = by + int(math.sin(crack_angle) * 3)
                cx2 = bx + int(math.cos(crack_angle) * (ball_r - 2))
                cy2 = by + int(math.sin(crack_angle) * (ball_r - 2))
                pygame.draw.line(surface, _NS_zahkareth.PALETTE["gold_dark"],
                                 (cx1, cy1), (cx2, cy2), 1)
            # Glowing halo
            for r in range(ball_r + 6, ball_r, -1):
                alpha = _NS_zahkareth._alpha(120 * (ball_r + 6 - r) / 6 * pulse)
                _NS_zahkareth._aacircle(surface,
                                        (*_NS_zahkareth.PALETTE["gold_hot"], alpha),
                                        (bx, by), r)
            # Trail of sand particles behind ball
            for i in range(6):
                trail_t = max(0.0, t - i * 0.06)
                trail_bx = int(start_x + (tx - start_x) * trail_t)
                trail_bp = trail_t * num_bounces
                trail_bi = int(trail_bp)
                trail_bt = trail_bp - trail_bi
                trail_by = int(start_y + (ty - start_y) * trail_t) - \
                    int(math.sin(trail_bt * math.pi) * (30 - trail_bi * 5))
                alpha = _NS_zahkareth._alpha(180 - i * 25)
                _NS_zahkareth._aacircle(surface,
                                        (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                                        (trail_bx, trail_by), max(1, 4 - i))
                pygame.draw.rect(surface,
                                 (*_NS_zahkareth.PALETTE["sand_light"], alpha),
                                 (trail_bx, trail_by, 1, 1))
            # Sand puff at bounce points (when ball hits ground)
            if bounce_t < 0.1 and bounce_index > 0:
                # Sand puff
                puff_x = int(start_x + (tx - start_x) * (bounce_index / num_bounces))
                puff_y = int(start_y + (ty - start_y) * (bounce_index / num_bounces)) + 3
                for r in range(6, 0, -1):
                    alpha = _NS_zahkareth._alpha(180 * (6 - r) / 6)
                    _NS_zahkareth._aacircle(surface,
                                            (*_NS_zahkareth.PALETTE["sand_mid"], alpha),
                                            (puff_x, puff_y), r)
    # ============================================================
    # SKILL E - SAND VORTEX (pull enemies to center)
    # ============================================================
    def _draw_sand_vortex_ground(surface, boss, x, y, timer, phase):
        """Vortex rings at boss location."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))
        if r > 3:
            for i, (mult, alpha_val) in enumerate([
                (1.0, 200), (0.85, 180), (0.7, 160),
                (0.55, 140), (0.4, 120), (0.25, 100),
            ]):
                cur_r = int(r * mult)
                rot = phase * 2 + i * 0.5
                offset_x = int(math.cos(rot) * 3)
                pygame.draw.ellipse(surface,
                                    (*_NS_zahkareth.PALETTE["gold_darkest"], alpha_val),
                                    (x - cur_r + offset_x, y + 40 - cur_r // 3,
                                     cur_r * 2, cur_r * 2 // 3), 2)
                pygame.draw.ellipse(surface,
                                    (*_NS_zahkareth.PALETTE["gold_dark"], alpha_val),
                                    (x - cur_r + offset_x + 1, y + 40 - cur_r // 3 + 1,
                                     cur_r * 2 - 2, cur_r * 2 // 3 - 2), 1)
    def _draw_sand_vortex_foreground(surface, boss, x, y, timer, phase):
        """Sand vortex pulling in - swirling particles + arrows."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(60 * min(1.0, progress * 3))
        if r < 5:
            return
        # Swirling sand particles spiraling inward
        for i in range(30):
            spiral_t = (phase * 1.5 + i * 0.1) % 1.0
            dist = r * (1 - spiral_t * 0.85)
            angle = phase * 3 + i * math.pi / 15 + spiral_t * math.pi * 3
            sx = x + int(math.cos(angle) * dist)
            sy = y + int(math.sin(angle) * dist * 0.55)
            alpha = _NS_zahkareth._alpha(240 * spiral_t)
            _NS_zahkareth._aacircle(surface,
                                    (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                                    (sx, sy), 2)
            _NS_zahkareth._aacircle(surface,
                                    (*_NS_zahkareth.PALETTE["gold_mid"], alpha),
                                    (sx, sy), 1)
            pygame.draw.rect(surface,
                             (*_NS_zahkareth.PALETTE["gold_hot"], alpha),
                             (sx, sy, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_zahkareth.PALETTE["gold_shine"], alpha),
                             (sx, sy, 1, 1))
        # Pull arrows (pointing inward from edge)
        for i in range(8):
            angle = phase * 1.5 + i * math.pi / 4
            arrow_out_x = x + int(math.cos(angle) * r)
            arrow_out_y = y + int(math.sin(angle) * r * 0.55)
            arrow_in_x = x + int(math.cos(angle) * (r - 10))
            arrow_in_y = y + int(math.sin(angle) * (r - 10) * 0.55)
            pygame.draw.line(surface, _NS_zahkareth.PALETTE["gold_hot"],
                             (arrow_out_x, arrow_out_y),
                             (arrow_in_x, arrow_in_y), 2)
            # Arrow head at inner point
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_shine"],
                             (arrow_in_x, arrow_in_y, 2, 2))
        # Central bright glow
        for r_inner in range(10, 0, -1):
            alpha = _NS_zahkareth._alpha(150 * (10 - r_inner) / 10)
            _NS_zahkareth._aacircle(surface,
                                    (*_NS_zahkareth.PALETTE["gold_hot"], alpha),
                                    (x, y), r_inner)
        _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_shine"], (x, y), 2)
        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["white"], (x, y, 1, 1))
    # ============================================================
    # SKILL R - SAND PRISON (dome cage at target)
    # ============================================================
    def _draw_sand_prison_ground(surface, boss, x, y, timer, phase):
        """Ground marks under prison."""
        tx, ty = _NS_zahkareth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Warning circle
            t = progress / 0.3
            r = int(50 * t)
            alpha = _NS_zahkareth._alpha(180 * t)
            pygame.draw.ellipse(surface, (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3), 3)
            pygame.draw.ellipse(surface, (*_NS_zahkareth.PALETTE["gold_hot"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4), 2)
        else:
            # Prison base circle
            r = 50
            alpha = _NS_zahkareth._alpha(240)
            pygame.draw.ellipse(surface, (*_NS_zahkareth.PALETTE["gold_darkest"], alpha),
                                (tx - r, ty - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                                (tx - r + 3, ty - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_zahkareth.PALETTE["gold_mid"], alpha),
                                (tx - r + 8, ty - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_sand_prison_foreground(surface, boss, x, y, timer, phase):
        """Golden dome prison at target."""
        tx, ty = _NS_zahkareth._target_position(boss, x, y)
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Boss leaps toward target - gathering energy above
            t = progress / 0.3
            gather_y = ty - int((1 - t) * 80)
            gather_r = int(6 + t * 12)
            for r in range(gather_r + 5, 0, -1):
                alpha = _NS_zahkareth._alpha(200 * (gather_r + 5 - r) / (gather_r + 5))
                _NS_zahkareth._aacircle(surface,
                                        (*_NS_zahkareth.PALETTE["gold_dark"], alpha),
                                        (tx, gather_y), r)
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_hot"],
                                    (tx, gather_y), gather_r - 2)
            _NS_zahkareth._aacircle(surface, _NS_zahkareth.PALETTE["gold_shine"],
                                    (tx, gather_y), max(1, gather_r - 5))
        else:
            # DOME PRISON active
            t = (progress - 0.3) / 0.7
            grow_t = min(1.0, t * 3)  # dome grows quickly
            # Dome dimensions
            dome_r = int(50 * grow_t)
            dome_h = int(65 * grow_t)  # dome height (top point)
            dome_cx = tx
            dome_cy = ty  # base of dome
            if dome_r < 5:
                return
            pulse = math.sin(phase * 2) * 0.3 + 0.7
            # Draw dome shell (semi-ellipse)
            # Base semi-circle
            dome_rect = (dome_cx - dome_r, dome_cy - dome_h,
                        dome_r * 2, dome_h * 2)
            # Multi-layer dome for glow effect
            # Draw filled dome first (translucent)
            dome_surf = pygame.Surface((dome_r * 2 + 20, dome_h * 2 + 20), pygame.SRCALPHA)
            local_cx = dome_r + 10
            local_cy = dome_h + 10
            # Filled dome (transparent gold)
            fill_alpha = _NS_zahkareth._alpha(80 * pulse * (1 - t * 0.4))
            pygame.draw.ellipse(dome_surf,
                                (*_NS_zahkareth.PALETTE["gold_mid"], fill_alpha),
                                (local_cx - dome_r, local_cy - dome_h,
                                 dome_r * 2, dome_h * 2))
            # Hide bottom half
            pygame.draw.rect(dome_surf, (0, 0, 0, 0),
                             (0, local_cy, dome_r * 2 + 20, dome_h + 20))
            # Dome outline layers
            for layer_i, (thick, alpha_val, color) in enumerate([
                (4, 220, _NS_zahkareth.PALETTE["gold_darkest"]),
                (3, 240, _NS_zahkareth.PALETTE["gold_dark"]),
                (2, 250, _NS_zahkareth.PALETTE["gold_mid"]),
                (1, 255, _NS_zahkareth.PALETTE["gold_hot"]),
            ]):
                # Semi-ellipse outline (top half only)
                # Draw as series of line segments
                prev_pt = None
                for angle_deg in range(180, 361, 6):  # 180 to 360 = top half
                    a = math.radians(angle_deg)
                    px = local_cx + int(math.cos(a) * dome_r)
                    py = local_cy + int(math.sin(a) * dome_h)
                    if prev_pt:
                        pygame.draw.line(dome_surf, (*color, alpha_val),
                                         prev_pt, (px, py), thick)
                    prev_pt = (px, py)
            surface.blit(dome_surf, (dome_cx - dome_r - 10, dome_cy - dome_h - 10))
            # Gold chain lattice pattern on dome
            # Vertical lines (meridians)
            for merid_i in range(9):
                merid_angle = merid_i * math.pi / 8
                # Line from top of dome to base
                for h_step in range(0, 20, 2):
                    h_t = h_step / 19  # 0 = top, 1 = base
                    # Position on dome surface
                    y_offset = int(math.cos(h_t * math.pi / 2) * dome_h)
                    x_scale = math.sin(h_t * math.pi / 2)
                    lx = dome_cx + int(math.cos(merid_angle) * dome_r * x_scale)
                    ly = dome_cy - y_offset
                    # Skip if too close to previous
                    pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_light"],
                                     (lx, ly, 1, 1))
                    if h_step % 4 == 0:
                        pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_shine"],
                                         (lx, ly, 1, 1))
            # Horizontal rings on dome (latitudes)
            for lat_i in range(1, 4):
                lat_h_t = lat_i / 4  # 0 = top, 1 = base
                y_offset = int(math.cos(lat_h_t * math.pi / 2) * dome_h)
                x_scale = math.sin(lat_h_t * math.pi / 2)
                ring_r = int(dome_r * x_scale)
                if ring_r > 3:
                    pygame.draw.ellipse(surface,
                                        _NS_zahkareth.PALETTE["gold_hot"],
                                        (dome_cx - ring_r, dome_cy - y_offset - 3,
                                         ring_r * 2, 6), 1)
            # Top spike/apex
            _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["shadow_deep"], [
                (dome_cx + 1, dome_cy - dome_h - 8 + 1),
                (dome_cx - 3 + 1, dome_cy - dome_h + 1),
                (dome_cx + 3 + 1, dome_cy - dome_h + 1),
            ])
            _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_darkest"], [
                (dome_cx, dome_cy - dome_h - 8),
                (dome_cx - 3, dome_cy - dome_h),
                (dome_cx + 3, dome_cy - dome_h),
            ])
            _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_dark"], [
                (dome_cx, dome_cy - dome_h - 7),
                (dome_cx - 2, dome_cy - dome_h),
                (dome_cx + 2, dome_cy - dome_h),
            ])
            _NS_zahkareth._poly(surface, _NS_zahkareth.PALETTE["gold_mid"], [
                (dome_cx, dome_cy - dome_h - 5),
                (dome_cx - 1, dome_cy - dome_h),
                (dome_cx + 1, dome_cy - dome_h),
            ])
            # Bright glow at apex
            for r in range(5, 0, -1):
                alpha = _NS_zahkareth._alpha(180 * (5 - r) / 5 * pulse)
                _NS_zahkareth._aacircle(surface,
                                        (*_NS_zahkareth.PALETTE["gold_hot"], alpha),
                                        (dome_cx, dome_cy - dome_h - 4), r)
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_shine"],
                             (dome_cx, dome_cy - dome_h - 5, 1, 1))
            pygame.draw.rect(surface, _NS_zahkareth.PALETTE["white"],
                             (dome_cx, dome_cy - dome_h - 5, 1, 1))
            # Sparkles around dome
            for i in range(12):
                angle = phase * 2 + i * math.pi / 6
                sp_r = dome_r + 4
                sp_h = dome_h + 4
                sx = dome_cx + int(math.cos(angle) * sp_r)
                sy = dome_cy - int(math.sin(abs(math.sin(angle))) * sp_h * 0.9)
                pygame.draw.rect(surface, _NS_zahkareth.PALETTE["gold_shine"], (sx, sy, 1, 1))



# ====================================================================
# KYRENZAI (CRIMSON DEVOURER) - TRUE BOSS
# ====================================================================

class _NS_kyrenzai:
    """Namespace kyrenzai - Crimson Devourer half-ghoul boss."""
    HAS_AACIRCLE = hasattr(pygame.draw, "aacircle")
    HAS_AALINES = hasattr(pygame.draw, "aalines")
    PALETTE = {
        # Dark clothing (black jacket, pants)
        "cloth_darkest": (5, 3, 5),
        "cloth_dark": (18, 12, 18),
        "cloth_mid": (40, 30, 35),
        "cloth_light": (75, 60, 65),
        "cloth_shine": (130, 115, 120),
        # KAGUNE red (main theme - blood tentacles)
        "kagune_darkest": (25, 0, 5),
        "kagune_dark": (80, 5, 15),
        "kagune_mid": (170, 20, 35),
        "kagune_light": (230, 55, 65),
        "kagune_hot": (255, 110, 100),
        "kagune_shine": (255, 200, 180),
        # Skin (pale ghoul skin)
        "skin_shadow": (100, 85, 90),
        "skin_dark": (170, 145, 145),
        "skin_mid": (220, 195, 190),
        "skin_light": (245, 225, 220),
        "skin_shine": (255, 245, 240),
        # White hair (Kaneki's signature)
        "hair_darkest": (100, 100, 110),
        "hair_dark": (155, 155, 165),
        "hair_mid": (200, 200, 210),
        "hair_light": (230, 230, 235),
        "hair_shine": (250, 250, 255),
        # Mask (black leather + zipper)
        "mask_dark": (8, 5, 8),
        "mask_mid": (30, 25, 28),
        "mask_light": (60, 55, 58),
        "mask_shine": (110, 105, 108),
        # Ghoul teeth (sharp white)
        "teeth_light": (240, 230, 225),
        "teeth_shine": (255, 250, 250),
        # Left eye (RED ghoul kakugan - one-eyed king signature!)
        "eye_socket": (5, 0, 2),
        "eye_dark": (60, 5, 10),
        "eye_mid": (200, 30, 35),
        "eye_light": (255, 90, 80),
        "eye_glow": (255, 200, 170),
        # Right eye (normal grey - human side)
        "eye_normal_dark": (40, 40, 50),
        "eye_normal_mid": (100, 100, 115),
        # Blood particles
        "blood_dark": (60, 3, 8),
        "blood_hot": (200, 30, 40),
        "blood_shine": (255, 100, 90),
        "shadow": (0, 0, 0),
        "shadow_deep": (2, 0, 2),
        "white": (255, 255, 255),
    }
    def _clamp(color):
        return tuple(max(0, min(255, int(c))) for c in color)
    def _alpha(v):
        return max(0, min(255, int(v)))
    def _aacircle(surface, color, center, radius, width=0):
        color = _NS_kyrenzai._clamp(color)
        if _NS_kyrenzai.HAS_AACIRCLE and radius > 1:
            try:
                pygame.draw.aacircle(surface, color, center, radius, width)
                return
            except Exception:
                pass
        pygame.draw.circle(surface, color, center, radius, width)
    def _aaline(surface, color, start, end, width=1):
        color = _NS_kyrenzai._clamp(color)
        if _NS_kyrenzai.HAS_AALINES and width == 1:
            try:
                pygame.draw.aaline(surface, color, start, end)
                return
            except Exception:
                pass
        pygame.draw.line(surface, color, start, end, width)
    def _poly(surface, color, points):
        if len(points) < 3:
            return
        pygame.draw.polygon(surface, _NS_kyrenzai._clamp(color), points)
    def _target_position(boss, x, y):
        target = getattr(boss, "target", None)
        if target is not None and getattr(target, "alive", True):
            return int(target.x), int(target.y)
        return int(x + 220 * getattr(boss, "direction", 1)), int(y)
    # ============================================================
    # ENTRY POINT
    # ============================================================
    def draw_kyrenzai(surface, boss, x, y):
        pulse = float(getattr(boss, "pulse", 0.0))
        active_skill = getattr(boss, "active_skill", None)
        skill_timer = int(getattr(boss, "active_skill_timer", 0))
        moving = _NS_kyrenzai._detect_moving(boss)
        _NS_kyrenzai._update_attack_anim(boss)
        attacking = (
            getattr(boss, "_kn_attack_active", False)
            or getattr(boss, "timer", 0) > getattr(boss, "attack_cooldown", 40) - 15
        )
        # Ambient
        _NS_kyrenzai._draw_blood_aura(surface, x, y, pulse)
        _NS_kyrenzai._draw_ground_seal(surface, x, y + 48, pulse, active_skill)
        # Ground skill FX
        if active_skill == "e":
            _NS_kyrenzai._draw_crimson_bloom_ground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kyrenzai._draw_ghoul_awakening_ground(surface, boss, x, y, skill_timer, pulse)
        # Body (floating)
        # During R (transformed): draw full kagune wings behind
        r_active = active_skill == "r"
        if attacking:
            _NS_kyrenzai._draw_kn_attack(surface, boss, x, y, r_active)
        elif moving:
            _NS_kyrenzai._draw_kn_float_move(surface, boss, x, y, r_active)
        else:
            _NS_kyrenzai._draw_kn_idle(surface, boss, x, y, r_active)
        # Foreground FX
        if active_skill == "q":
            _NS_kyrenzai._draw_kagune_slash(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "w":
            _NS_kyrenzai._draw_tendril_snare(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "e":
            _NS_kyrenzai._draw_crimson_bloom_foreground(surface, boss, x, y, skill_timer, pulse)
        elif active_skill == "r":
            _NS_kyrenzai._draw_ghoul_awakening_foreground(surface, boss, x, y, skill_timer, pulse)
    # ============================================================
    # ANIMATION STATE
    # ============================================================
    def _update_attack_anim(boss):
        cooldown = max(2, int(getattr(boss, "attack_cooldown", 48)))
        timer = int(getattr(boss, "timer", 0))
        previous = int(getattr(boss, "_kn_previous_timer", 0))
        active = bool(getattr(boss, "_kn_attack_active", False))
        if timer >= cooldown - 1 and previous <= 1:
            boss._kn_attack_active = True
            boss._kn_attack_frame = 0
            active = True
        elif active and timer > 0:
            boss._kn_attack_frame = int(getattr(boss, "_kn_attack_frame", 0)) + 1
        elif timer <= 0:
            boss._kn_attack_active = False
            boss._kn_attack_frame = 0
            active = False
        boss._kn_previous_timer = timer
        boss._kn_attack_progress = (
            min(1.0, getattr(boss, "_kn_attack_frame", 0) / max(1, cooldown - 1))
            if active else 0.0
        )
    def _detect_moving(boss):
        if not hasattr(boss, "_kn_last_x"):
            boss._kn_last_x = boss.x
            boss._kn_last_y = boss.y
            return False
        dx = abs(boss.x - boss._kn_last_x)
        dy = abs(boss.y - boss._kn_last_y)
        boss._kn_last_x = boss.x
        boss._kn_last_y = boss.y
        return dx + dy > 0.3
    # ============================================================
    # POSE ROUTERS
    # ============================================================
    def _draw_kn_idle(surface, boss, x, y, r_active=False):
        bob = int(math.sin(boss.pulse * 0.5) * 4)
        _NS_kyrenzai._draw_float_shadow(surface, x, y + 52, boss.pulse)
        _NS_kyrenzai._draw_blood_wisps(surface, x, y + 40, boss.pulse)
        _NS_kyrenzai._draw_kn_body(surface, x, y + bob,
                                    boss.direction, boss.pulse, "idle", 0, r_active)
    def _draw_kn_float_move(surface, boss, x, y, r_active=False):
        phase = boss.pulse * 1.5
        bob = int(math.sin(phase * 0.8) * 4)
        sway = int(math.sin(phase * 0.5) * 2)
        _NS_kyrenzai._draw_float_shadow(surface, x + sway, y + 52, phase)
        _NS_kyrenzai._draw_blood_wisps(surface, x + sway, y + 40, phase,
                                        trail=True, facing=boss.direction)
        _NS_kyrenzai._draw_kn_body(surface, x + sway, y + bob,
                                    boss.direction, phase, "float", 0, r_active)
    def _draw_kn_attack(surface, boss, x, y, r_active=False):
        """Melee: kagune tentacle slash."""
        progress = getattr(boss, "_kn_attack_progress", None)
        if progress is None:
            progress = 1 - boss.timer / max(1, boss.attack_cooldown)
        progress = max(0.0, min(1.0, progress))
        # Wind up → slash forward → recovery
        if progress < 0.35:
            t = progress / 0.35
            body_shift = -int(t * 5) * boss.direction
            lift = int(t * 4)
        elif progress < 0.65:
            t = (progress - 0.35) / 0.3
            body_shift = int((-5 + t * 16)) * boss.direction
            lift = int(4 - t * 6)
        else:
            t = (progress - 0.65) / 0.35
            body_shift = int(11 * (1 - t)) * boss.direction
            lift = int(-2 + t * 2)
        bob = int(math.sin(boss.pulse * 0.5) * 3)
        _NS_kyrenzai._draw_float_shadow(surface, x + body_shift, y + 52, boss.pulse)
        _NS_kyrenzai._draw_blood_wisps(surface, x + body_shift, y + 40, boss.pulse,
                                        intense=True)
        _NS_kyrenzai._draw_kn_body(surface, x + body_shift, y - lift + bob,
                                    boss.direction, boss.pulse, "attack", progress,
                                    r_active)
        # Kagune slash arc
        _NS_kyrenzai._draw_kagune_swing_arc(surface, boss, x + body_shift,
                                             y - lift + bob, progress)
    # ============================================================
    # BODY - Half-Ghoul (kagune tentacles, jacket, mask/face)
    # ============================================================
    def _draw_kn_body(surface, cx, cy, facing, phase, action, attack_progress=0,
                       r_active=False):
        """Ghoul body: kagune tentacles behind, jacket, torso, mask."""
        # Kagune tentacles behind body (SIGNATURE - many red flowing tentacles)
        _NS_kyrenzai._draw_kagune_tentacles(surface, cx, cy - 4, facing, phase,
                                             action, attack_progress, r_active)
        # Long jacket tail
        _NS_kyrenzai._draw_jacket_tail(surface, cx, cy + 6, facing, phase)
        # Legs (pants)
        _NS_kyrenzai._draw_pants(surface, cx, cy + 12, facing, phase)
        # Torso (jacket)
        _NS_kyrenzai._draw_torso_jacket(surface, cx, cy - 4, facing, phase)
        # Arms with claws
        claw_thrust = 0
        if action == "attack":
            if attack_progress < 0.35:
                claw_thrust = -int(attack_progress / 0.35 * 6) * facing
            elif attack_progress < 0.65:
                t = (attack_progress - 0.35) / 0.3
                claw_thrust = int((-6 + t * 18)) * facing
            else:
                t = (attack_progress - 0.65) / 0.35
                claw_thrust = int(12 * (1 - t)) * facing
        _NS_kyrenzai._draw_arms_claws(surface, cx, cy - 2, facing, phase,
                                       claw_thrust, action)
        # Head with mask, white hair, red eye
        _NS_kyrenzai._draw_ghoul_head(surface, cx, cy - 22, facing, phase, action, r_active)
    def _draw_kagune_tentacles(surface, cx, cy, facing, phase, action, attack_progress,
                                r_active):
        """Multiple red kagune tentacles flowing from back (signature Kaneki look)."""
        # Number of tentacles increases when R active
        num_tentacles = 4 if not r_active else 8
        for tent_i in range(num_tentacles):
            # Each tentacle at different angle and length
            base_angle_offset = tent_i * math.pi * 2 / num_tentacles
            # Tentacles fan outward and back
            base_angle = math.pi * 0.5 + base_angle_offset * 0.5 - math.pi * 0.25
            if tent_i % 2 == 0:
                base_angle = -base_angle  # mirror for symmetry
            # Base position at back-shoulder area
            back = -facing
            base_x = cx + back * 4 + int(math.sin(phase * 0.5 + tent_i) * 2)
            base_y = cy - 4 + int(math.cos(phase * 0.5 + tent_i) * 2)
            # Tentacle length and wave animation
            base_length = 32 + tent_i * 3
            if r_active:
                base_length += 15  # longer in R form
            length = base_length
            # Attack animation: extend forward during E/W
            wave_intensity = math.sin(phase * 1.5 + tent_i * 0.4)
            wave_amp = 6 + wave_intensity * 3
            # Draw tentacle as curve (Bezier-like)
            num_segments = 12
            prev_x = base_x
            prev_y = base_y
            for seg in range(1, num_segments + 1):
                seg_t = seg / num_segments
                # Parametric position
                # Goes up-back-out
                fwd_dist = length * seg_t
                # Angle at this segment (curves outward)
                seg_angle = base_angle - seg_t * math.pi * 0.15 * (1 if tent_i % 2 else -1)
                seg_x = base_x + int(math.cos(seg_angle) * fwd_dist) * back
                seg_y = base_y - int(math.sin(seg_angle) * fwd_dist)
                # Wave motion perpendicular to curve
                perp_angle = seg_angle + math.pi / 2
                wave = math.sin(phase * 2 + seg_t * math.pi * 3 + tent_i) * wave_amp * seg_t
                seg_x += int(math.cos(perp_angle) * wave) * back
                seg_y += int(math.sin(perp_angle) * wave)
                # Tentacle thickness (tapers toward tip)
                thickness = max(1, 6 - seg)
                # Shadow
                _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                                     (prev_x + 1, prev_y + 1),
                                     (seg_x + 1, seg_y + 1), thickness + 1)
                # Base dark
                _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["kagune_darkest"],
                                     (prev_x, prev_y), (seg_x, seg_y), thickness)
                # Dark red
                _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["kagune_dark"],
                                     (prev_x, prev_y), (seg_x, seg_y),
                                     max(1, thickness - 1))
                # Mid red
                _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["kagune_mid"],
                                     (prev_x, prev_y - 1), (seg_x, seg_y - 1),
                                     max(1, thickness - 3))
                # Bright glow inner
                if seg > num_segments // 3:
                    pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["kagune_hot"],
                                     (seg_x, seg_y, 1, 1))
                prev_x = seg_x
                prev_y = seg_y
            # Sharp bladed tip at end
            tip_x = prev_x
            tip_y = prev_y
            # Tapered tip (small pointed shape)
            tip_dir_x = tip_x - base_x
            tip_dir_y = tip_y - base_y
            tip_dir_len = math.sqrt(tip_dir_x ** 2 + tip_dir_y ** 2)
            if tip_dir_len > 0:
                tip_dir_x /= tip_dir_len
                tip_dir_y /= tip_dir_len
                # Tip extends a bit further
                sharp_tip_x = int(tip_x + tip_dir_x * 4)
                sharp_tip_y = int(tip_y + tip_dir_y * 4)
                perp_x = -tip_dir_y
                perp_y = tip_dir_x
                _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["shadow_deep"], [
                    (sharp_tip_x + 1, sharp_tip_y + 1),
                    (tip_x + int(perp_x * 2) + 1, tip_y + int(perp_y * 2) + 1),
                    (tip_x - int(perp_x * 2) + 1, tip_y - int(perp_y * 2) + 1),
                ])
                _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["kagune_darkest"], [
                    (sharp_tip_x, sharp_tip_y),
                    (tip_x + int(perp_x * 2), tip_y + int(perp_y * 2)),
                    (tip_x - int(perp_x * 2), tip_y - int(perp_y * 2)),
                ])
                _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["kagune_mid"], [
                    (sharp_tip_x, sharp_tip_y),
                    (tip_x + int(perp_x * 1), tip_y + int(perp_y * 1)),
                    (tip_x - int(perp_x * 1), tip_y - int(perp_y * 1)),
                ])
                pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["kagune_hot"],
                                 (sharp_tip_x, sharp_tip_y, 1, 1))
                pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["kagune_shine"],
                                 (sharp_tip_x, sharp_tip_y, 1, 1))
    def _draw_jacket_tail(surface, cx, cy, facing, phase):
        """Long dark jacket tail."""
        wave1 = math.sin(phase * 0.6) * 3
        wave2 = math.sin(phase * 0.6 + 1.5) * 3
        jacket_pts = [
            (cx - 9, cy),
            (cx + 9, cy),
            (cx + 12, cy + 8),
            (cx + 14 + int(wave1), cy + 20),
            (cx + 12 + int(wave2), cy + 30),
            (cx + 6, cy + 38),
            (cx - 6, cy + 38),
            (cx - 12 + int(wave2), cy + 30),
            (cx - 14 + int(wave1), cy + 20),
            (cx - 12, cy + 8),
        ]
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                            [(px + 2, py + 3) for px, py in jacket_pts])
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_darkest"], jacket_pts)
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_dark"], [
            (cx - 8, cy + 2),
            (cx + 8, cy + 2),
            (cx + 10, cy + 10),
            (cx + 12 + int(wave1 * 0.7), cy + 22),
            (cx + 9 + int(wave2 * 0.7), cy + 30),
            (cx + 4, cy + 36),
            (cx - 4, cy + 36),
            (cx - 9 + int(wave2 * 0.7), cy + 30),
            (cx - 12 + int(wave1 * 0.7), cy + 22),
            (cx - 10, cy + 10),
        ])
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_mid"], [
            (cx - 6, cy + 4),
            (cx + 6, cy + 4),
            (cx + 8, cy + 14),
            (cx + 8, cy + 26),
            (cx + 3, cy + 34),
            (cx - 3, cy + 34),
            (cx - 8, cy + 26),
            (cx - 8, cy + 14),
        ])
        # Highlight
        pygame.draw.line(surface, _NS_kyrenzai.PALETTE["cloth_light"],
                         (cx - 2, cy + 8), (cx - 3, cy + 30), 1)
        pygame.draw.line(surface, _NS_kyrenzai.PALETTE["cloth_light"],
                         (cx + 2, cy + 8), (cx + 3, cy + 30), 1)
        # Jacket rip/tears at edges (small red gashes)
        for i in range(3):
            gash_x = cx - 8 + i * 8
            gash_y = cy + 20 + int(math.sin(phase + i) * 2)
            pygame.draw.line(surface, _NS_kyrenzai.PALETTE["kagune_darkest"],
                             (gash_x, gash_y), (gash_x - 2, gash_y + 4), 1)
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["kagune_dark"],
                             (gash_x - 1, gash_y + 2, 1, 1))
    def _draw_pants(surface, cx, cy, facing, phase):
        """Dark pants (legs)."""
        # Two leg columns
        for side in (-1, 1):
            leg_x = cx + side * 4
            leg_top_y = cy - 2
            leg_bottom_y = cy + 18
            # Leg base
            _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["shadow_deep"], [
                (leg_x - 4 + 1, leg_top_y + 1),
                (leg_x + 4 + 1, leg_top_y + 1),
                (leg_x + 4 + 1, leg_bottom_y + 1),
                (leg_x - 4 + 1, leg_bottom_y + 1),
            ])
            _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_darkest"], [
                (leg_x - 4, leg_top_y),
                (leg_x + 4, leg_top_y),
                (leg_x + 4, leg_bottom_y),
                (leg_x - 4, leg_bottom_y),
            ])
            _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_dark"], [
                (leg_x - 3, leg_top_y + 1),
                (leg_x + 3, leg_top_y + 1),
                (leg_x + 3, leg_bottom_y - 1),
                (leg_x - 3, leg_bottom_y - 1),
            ])
            _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_mid"], [
                (leg_x - 2, leg_top_y + 2),
                (leg_x + 2, leg_top_y + 2),
                (leg_x + 2, leg_bottom_y - 2),
                (leg_x - 2, leg_bottom_y - 2),
            ])
            # Highlight
            pygame.draw.line(surface, _NS_kyrenzai.PALETTE["cloth_light"],
                             (leg_x - 1, leg_top_y + 3),
                             (leg_x - 1, leg_bottom_y - 3), 1)
            # Boots
            _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["shadow_deep"], [
                (leg_x - 5 + 1, leg_bottom_y - 2 + 1),
                (leg_x + 5 + 1, leg_bottom_y - 2 + 1),
                (leg_x + 6 + 1, leg_bottom_y + 3 + 1),
                (leg_x - 6 + 1, leg_bottom_y + 3 + 1),
            ])
            _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_darkest"], [
                (leg_x - 5, leg_bottom_y - 2),
                (leg_x + 5, leg_bottom_y - 2),
                (leg_x + 6, leg_bottom_y + 3),
                (leg_x - 6, leg_bottom_y + 3),
            ])
            _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_dark"], [
                (leg_x - 4, leg_bottom_y - 1),
                (leg_x + 4, leg_bottom_y - 1),
                (leg_x + 5, leg_bottom_y + 2),
                (leg_x - 5, leg_bottom_y + 2),
            ])
            # Boot highlight
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["cloth_light"],
                             (leg_x - 3, leg_bottom_y, 6, 1))
    def _draw_torso_jacket(surface, cx, cy, facing, phase):
        """Torso with black leather jacket."""
        # Torso base
        torso_pts = [
            (cx - 9, cy - 6),
            (cx + 9, cy - 6),
            (cx + 11, cy),
            (cx + 9, cy + 6),
            (cx + 7, cy + 10),
            (cx - 7, cy + 10),
            (cx - 9, cy + 6),
            (cx - 11, cy),
        ]
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                            [(px + 2, py + 2) for px, py in torso_pts])
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_darkest"], torso_pts)
        # Jacket layer
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_dark"], [
            (cx - 8, cy - 5),
            (cx + 8, cy - 5),
            (cx + 10, cy),
            (cx + 8, cy + 5),
            (cx + 6, cy + 9),
            (cx - 6, cy + 9),
            (cx - 8, cy + 5),
            (cx - 10, cy),
        ])
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_mid"], [
            (cx - 6, cy - 4),
            (cx + 6, cy - 4),
            (cx + 8, cy),
            (cx + 6, cy + 4),
            (cx + 4, cy + 8),
            (cx - 4, cy + 8),
            (cx - 6, cy + 4),
            (cx - 8, cy),
        ])
        # Jacket highlights
        pygame.draw.line(surface, _NS_kyrenzai.PALETTE["cloth_light"],
                         (cx - 5, cy - 3), (cx - 3, cy - 1), 1)
        pygame.draw.line(surface, _NS_kyrenzai.PALETTE["cloth_light"],
                         (cx + 3, cy - 3), (cx + 5, cy - 1), 1)
        # Jacket zipper (vertical line down center)
        pygame.draw.line(surface, _NS_kyrenzai.PALETTE["cloth_darkest"],
                         (cx, cy - 5), (cx, cy + 8), 1)
        # Zipper teeth (small dashes)
        for zy in range(int(cy - 4), int(cy + 8), 2):
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["mask_light"],
                             (cx, zy, 1, 1))
        # Belt/strap at waist
        pygame.draw.line(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                         (cx - 8, cy + 8), (cx + 8, cy + 8), 2)
        pygame.draw.line(surface, _NS_kyrenzai.PALETTE["cloth_darkest"],
                         (cx - 8, cy + 7), (cx + 8, cy + 7), 2)
        # Belt buckle
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["mask_light"],
                         (cx - 2, cy + 7, 4, 2))
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["mask_shine"],
                         (cx - 1, cy + 7, 2, 1))
        # Shoulder details (small pauldrons)
        for side in (-1, 1):
            _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["shadow_deep"], [
                (cx + side * 8, cy - 7),
                (cx + side * 12, cy - 5),
                (cx + side * 11, cy - 1),
                (cx + side * 8, cy),
            ])
            _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_darkest"], [
                (cx + side * 8, cy - 8),
                (cx + side * 11, cy - 5),
                (cx + side * 10, cy - 1),
                (cx + side * 8, cy - 1),
            ])
            _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["cloth_dark"], [
                (cx + side * 9, cy - 7),
                (cx + side * 10, cy - 5),
                (cx + side * 9, cy - 2),
            ])
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["cloth_mid"],
                             (cx + side * 9, cy - 5, 1, 1))
        # Blood stains on jacket (small red spots)
        for i, (bx, by) in enumerate([(-4, -1), (2, 3), (-2, 5)]):
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["blood_dark"],
                             (cx + bx, cy + by, 2, 1))
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["blood_hot"],
                             (cx + bx, cy + by, 1, 1))
    def _draw_arms_claws(surface, cx, cy, facing, phase, thrust, action):
        """Both arms with sharp clawed hands."""
        wave = math.sin(phase * 0.7) * 1
        # Front arm (extended forward slightly, ghoul crouch pose)
        shoulder_x = cx + facing * 10
        shoulder_y = cy - 2
        if action == "attack":
            hand_x = cx + facing * (18 + thrust)
            hand_y = cy + 4 + int(wave)
        else:
            hand_x = cx + facing * 16
            hand_y = cy + 6 + int(wave)
        elbow_x = (shoulder_x + hand_x) // 2 + facing
        elbow_y = (shoulder_y + hand_y) // 2 + 2
        # Front upper arm
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                             (shoulder_x + 1, shoulder_y + 1),
                             (elbow_x + 1, elbow_y + 1), 5)
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["cloth_darkest"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 4)
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["cloth_dark"],
                             (shoulder_x, shoulder_y), (elbow_x, elbow_y), 3)
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["cloth_mid"],
                             (shoulder_x, shoulder_y - 1),
                             (elbow_x, elbow_y - 1), 2)
        # Forearm (bare skin exposed)
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                             (elbow_x + 1, elbow_y + 1),
                             (hand_x + 1, hand_y + 1), 4)
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["skin_shadow"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 3)
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["skin_dark"],
                             (elbow_x, elbow_y), (hand_x, hand_y), 2)
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["skin_mid"],
                             (elbow_x, elbow_y - 1), (hand_x, hand_y - 1), 1)
        # Sleeve cuff (dark line where sleeve ends)
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["cloth_darkest"],
                         (elbow_x - 1, elbow_y - 1, 3, 2))
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["cloth_mid"],
                         (elbow_x, elbow_y - 1, 1, 1))
        # Hand (with claws)
        _NS_kyrenzai._aacircle(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                                (hand_x + 1, hand_y + 1), 3)
        _NS_kyrenzai._aacircle(surface, _NS_kyrenzai.PALETTE["skin_dark"],
                                (hand_x, hand_y), 3)
        _NS_kyrenzai._aacircle(surface, _NS_kyrenzai.PALETTE["skin_mid"],
                                (hand_x, hand_y), 2)
        # Sharp claws (3-4 protruding from hand)
        for claw_i, spread in enumerate((-2, 0, 2)):
            claw_tip_x = hand_x + facing * 5
            claw_tip_y = hand_y + spread
            pygame.draw.line(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                             (hand_x + 1, hand_y + 1),
                             (claw_tip_x + 1, claw_tip_y + 1), 2)
            pygame.draw.line(surface, _NS_kyrenzai.PALETTE["mask_dark"],
                             (hand_x, hand_y), (claw_tip_x, claw_tip_y), 2)
            pygame.draw.line(surface, _NS_kyrenzai.PALETTE["mask_light"],
                             (hand_x, hand_y - 1),
                             (claw_tip_x, claw_tip_y - 1), 1)
            # Bright claw tip
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["mask_shine"],
                             (claw_tip_x, claw_tip_y, 1, 1))
            # Blood drip
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["blood_hot"],
                             (claw_tip_x, claw_tip_y, 1, 1))
        # Back arm (partial, slightly behind)
        b_shoulder_x = cx - facing * 8
        b_shoulder_y = cy - 2
        b_elbow_x = cx - facing * 14
        b_elbow_y = cy + 4 + int(wave)
        b_hand_x = cx - facing * 12
        b_hand_y = cy + 10 + int(wave)
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                             (b_shoulder_x + 1, b_shoulder_y + 1),
                             (b_elbow_x + 1, b_elbow_y + 1), 4)
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["cloth_darkest"],
                             (b_shoulder_x, b_shoulder_y),
                             (b_elbow_x, b_elbow_y), 3)
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["cloth_dark"],
                             (b_shoulder_x, b_shoulder_y),
                             (b_elbow_x, b_elbow_y), 2)
        # Back forearm (skin)
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["skin_shadow"],
                             (b_elbow_x, b_elbow_y), (b_hand_x, b_hand_y), 3)
        _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["skin_dark"],
                             (b_elbow_x, b_elbow_y), (b_hand_x, b_hand_y), 2)
        # Back fist with claws
        _NS_kyrenzai._aacircle(surface, _NS_kyrenzai.PALETTE["skin_dark"],
                                (b_hand_x, b_hand_y), 2)
        # Back claws
        for spread in (-1, 1):
            ct_x = b_hand_x - facing * 3
            ct_y = b_hand_y + spread
            pygame.draw.line(surface, _NS_kyrenzai.PALETTE["mask_dark"],
                             (b_hand_x, b_hand_y), (ct_x, ct_y), 1)
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["mask_light"], (ct_x, ct_y, 1, 1))
    def _draw_ghoul_head(surface, cx, cy, facing, phase, action, r_active):
        """Ghoul head with white hair, black leather mask, red eye."""
        # Face shape (pale skin visible around mask)
        face_pts = [
            (cx - 5, cy - 4),
            (cx + 5, cy - 4),
            (cx + 6, cy),
            (cx + 5, cy + 4),
            (cx + 2, cy + 7),
            (cx - 2, cy + 7),
            (cx - 5, cy + 4),
            (cx - 6, cy),
        ]
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                            [(px + 1, py + 2) for px, py in face_pts])
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["skin_shadow"], face_pts)
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["skin_dark"], [
            (cx - 4, cy - 4),
            (cx + 4, cy - 4),
            (cx + 5, cy),
            (cx + 4, cy + 3),
            (cx + 2, cy + 6),
            (cx - 2, cy + 6),
            (cx - 4, cy + 3),
            (cx - 5, cy),
        ])
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["skin_mid"], [
            (cx - 3, cy - 3),
            (cx + 3, cy - 3),
            (cx + 4, cy),
            (cx + 3, cy + 3),
            (cx - 3, cy + 3),
            (cx - 4, cy),
        ])
        # Face highlight
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["skin_light"],
                         (cx - 1, cy - 2, 3, 2))
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["skin_shine"],
                         (cx, cy - 2, 1, 1))
        # WHITE HAIR (Kaneki's iconic hair - spiky messy hair)
        _NS_kyrenzai._draw_white_hair(surface, cx, cy, facing, phase)
        # LEATHER MASK (covers mouth/nose area - Kaneki style with zipper)
        _NS_kyrenzai._draw_ghoul_mask(surface, cx, cy, facing, phase, r_active)
        # LEFT EYE - RED GHOUL EYE (kakugan!) - signature one-eyed king
        # RIGHT EYE - normal grey
        _NS_kyrenzai._draw_asymmetric_eyes(surface, cx, cy, facing, phase, r_active)
    def _draw_white_hair(surface, cx, cy, facing, phase):
        """Messy spiky white hair (Kaneki's iconic look)."""
        wave = math.sin(phase * 0.5) * 1
        # Main hair mass on top
        hair_pts = [
            (cx - 6, cy - 3),
            (cx - 7, cy - 5),
            (cx - 5, cy - 8),
            (cx - 2, cy - 9 + int(wave)),
            (cx, cy - 10 + int(wave)),
            (cx + 2, cy - 9 + int(wave)),
            (cx + 5, cy - 8),
            (cx + 7, cy - 5),
            (cx + 6, cy - 3),
        ]
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                            [(px + 1, py + 2) for px, py in hair_pts])
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["hair_darkest"], hair_pts)
        # Hair mid layer
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["hair_dark"], [
            (cx - 5, cy - 3),
            (cx - 6, cy - 5),
            (cx - 4, cy - 7),
            (cx - 1, cy - 8),
            (cx + 1, cy - 8),
            (cx + 4, cy - 7),
            (cx + 6, cy - 5),
            (cx + 5, cy - 3),
        ])
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["hair_mid"], [
            (cx - 4, cy - 4),
            (cx - 5, cy - 5),
            (cx - 3, cy - 6),
            (cx, cy - 7),
            (cx + 3, cy - 6),
            (cx + 5, cy - 5),
            (cx + 4, cy - 4),
        ])
        # Hair highlights (light strands)
        pygame.draw.line(surface, _NS_kyrenzai.PALETTE["hair_light"],
                         (cx - 3, cy - 5), (cx - 1, cy - 7), 1)
        pygame.draw.line(surface, _NS_kyrenzai.PALETTE["hair_light"],
                         (cx + 1, cy - 7), (cx + 3, cy - 5), 1)
        pygame.draw.line(surface, _NS_kyrenzai.PALETTE["hair_shine"],
                         (cx, cy - 8), (cx, cy - 6), 1)
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["hair_shine"],
                         (cx - 2, cy - 6, 1, 1))
        # Spiky hair strands falling in front of face (bangs)
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["hair_darkest"], [
            (cx - 5, cy - 4),
            (cx + 5, cy - 4),
            (cx + 4, cy - 1),
            (cx + 2, cy - 2),
            (cx, cy - 1),
            (cx - 2, cy - 2),
            (cx - 4, cy - 1),
        ])
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["hair_dark"], [
            (cx - 4, cy - 3),
            (cx + 4, cy - 3),
            (cx + 3, cy - 1),
            (cx + 1, cy - 2),
            (cx - 1, cy - 2),
            (cx - 3, cy - 1),
        ])
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["hair_light"],
                         (cx - 1, cy - 2, 1, 1))
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["hair_light"],
                         (cx + 1, cy - 2, 1, 1))
    def _draw_ghoul_mask(surface, cx, cy, facing, phase, r_active):
        """Leather mask covering mouth/lower face."""
        # Mask covers lower half of face
        mask_top_y = cy + 1
        mask_bottom_y = cy + 7
        # Mask base
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["shadow_deep"], [
            (cx - 5, mask_top_y),
            (cx + 5, mask_top_y),
            (cx + 4, mask_bottom_y),
            (cx + 2, mask_bottom_y + 1),
            (cx - 2, mask_bottom_y + 1),
            (cx - 4, mask_bottom_y),
        ])
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["mask_dark"], [
            (cx - 4, mask_top_y),
            (cx + 4, mask_top_y),
            (cx + 4, mask_bottom_y),
            (cx + 2, mask_bottom_y + 1),
            (cx - 2, mask_bottom_y + 1),
            (cx - 4, mask_bottom_y),
        ])
        _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["mask_mid"], [
            (cx - 3, mask_top_y + 1),
            (cx + 3, mask_top_y + 1),
            (cx + 3, mask_bottom_y - 1),
            (cx - 3, mask_bottom_y - 1),
        ])
        # Mask highlight
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["mask_light"],
                         (cx - 2, mask_top_y + 1, 4, 1))
        # SHARP TEETH visible on mask (Kaneki's signature - stitched sharp teeth pattern)
        # Zigzag teeth line across middle of mask
        teeth_y = mask_top_y + 3
        for i, tx_off in enumerate((-3, -1, 1, 3)):
            # Upper tooth triangle
            _NS_kyrenzai._poly(surface, _NS_kyrenzai.PALETTE["teeth_light"], [
                (cx + tx_off, teeth_y - 1),
                (cx + tx_off + 1, teeth_y + 1),
                (cx + tx_off - 1, teeth_y + 1),
            ])
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["teeth_shine"],
                             (cx + tx_off, teeth_y - 1, 1, 1))
        # Zipper line down center (vertical)
        pygame.draw.line(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                         (cx, mask_top_y), (cx, mask_bottom_y + 1), 1)
        # Zipper teeth
        for zy in range(int(mask_top_y + 1), int(mask_bottom_y + 1), 2):
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["mask_shine"],
                             (cx, zy, 1, 1))
        # Straps on side of mask
        for side in (-1, 1):
            pygame.draw.line(surface, _NS_kyrenzai.PALETTE["mask_dark"],
                             (cx + side * 4, mask_top_y + 2),
                             (cx + side * 6, mask_top_y + 3), 1)
            pygame.draw.line(surface, _NS_kyrenzai.PALETTE["mask_light"],
                             (cx + side * 4, mask_top_y + 2),
                             (cx + side * 5, mask_top_y + 3), 1)
    def _draw_asymmetric_eyes(surface, cx, cy, facing, phase, r_active):
        """Asymmetric eyes: LEFT is RED ghoul kakugan, RIGHT is normal grey."""
        pulse = math.sin(phase * 2) * 0.3 + 0.7
        # LEFT EYE (from character's perspective = viewer's right)
        # But for boss - we make the "kagune eye" always face-visible
        # We'll put red eye on facing side (visible/dramatic)
        red_eye_side = facing  # visible eye is red
        # RED KAKUGAN EYE (BLACK sclera + RED iris - ghoul signature)
        red_ex = cx + red_eye_side * 2
        red_ey = cy - 1
        # Deep black sclera (ghoul eye whites are BLACK)
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                         (red_ex - 2, red_ey - 1, 4, 3))
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["mask_dark"],
                         (red_ex - 2, red_ey - 1, 4, 3))
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["eye_socket"],
                         (red_ex - 2, red_ey - 1, 4, 3))
        # Red glow halo (bigger if R active)
        halo_max = 6 if r_active else 4
        for r in range(halo_max, 0, -1):
            alpha = _NS_kyrenzai._alpha(160 * (halo_max - r) / halo_max * pulse)
            _NS_kyrenzai._aacircle(surface,
                                    (*_NS_kyrenzai.PALETTE["eye_mid"], alpha),
                                    (red_ex, red_ey), r)
        # Red iris center
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["eye_dark"],
                         (red_ex - 1, red_ey, 2, 1))
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["eye_mid"],
                         (red_ex, red_ey, 1, 1))
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["eye_light"],
                         (red_ex, red_ey, 1, 1))
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["eye_glow"],
                         (red_ex, red_ey, 1, 1))
        # Red veins radiating from eye (kakugan pattern)
        for i in range(4):
            vein_angle = i * math.pi / 2 + phase * 0.5
            vx1 = red_ex + int(math.cos(vein_angle) * 2)
            vy1 = red_ey + int(math.sin(vein_angle) * 2)
            vx2 = red_ex + int(math.cos(vein_angle) * 3)
            vy2 = red_ey + int(math.sin(vein_angle) * 3)
            alpha_v = _NS_kyrenzai._alpha(180 * pulse)
            pygame.draw.line(surface, (*_NS_kyrenzai.PALETTE["kagune_hot"], alpha_v),
                             (vx1, vy1), (vx2, vy2), 1)
        # NORMAL GREY EYE (right, human side - covered by hair)
        normal_ex = cx - red_eye_side * 2
        normal_ey = cy - 1
        # Barely visible - covered by hair shadow
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                         (normal_ex - 1, normal_ey - 1, 2, 2))
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["eye_normal_dark"],
                         (normal_ex, normal_ey, 1, 1))
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["eye_normal_mid"],
                         (normal_ex, normal_ey, 1, 1))
        # Hair shadow over this eye
        pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["hair_darkest"],
                         (normal_ex - 1, normal_ey - 1, 3, 1))
    # ============================================================
    # MELEE SWING ARC (kagune slash - red crescent trail)
    # ============================================================
    def _draw_kagune_swing_arc(surface, boss, x, y, progress):
        """Red kagune crescent arc trail (from top to bottom)."""
        if progress < 0.35 or progress > 0.72:
            return
        facing = boss.direction
        t = (progress - 0.35) / 0.37
        arc_cx = x + facing * 18
        arc_cy = y - 2
        arc_radius = 42
        # Swing from top to bottom-forward
        start_a = -math.pi * 0.6
        end_a = math.pi * 0.6
        # Trail: only draw segments up to current progress
        trail_length = 0.45
        start_seg_t = max(0.0, t - trail_length)
        end_seg_t = min(1.0, t)
        # Layered arc for glow
        for layer_i, (thick, alpha_val, color) in enumerate([
            (6, 90, _NS_kyrenzai.PALETTE["kagune_darkest"]),
            (5, 130, _NS_kyrenzai.PALETTE["kagune_dark"]),
            (4, 180, _NS_kyrenzai.PALETTE["kagune_mid"]),
            (3, 220, _NS_kyrenzai.PALETTE["kagune_light"]),
            (2, 245, _NS_kyrenzai.PALETTE["kagune_hot"]),
            (1, 255, _NS_kyrenzai.PALETTE["kagune_shine"]),
        ]):
            arc_points = []
            num_segments = 22
            for seg in range(num_segments):
                seg_t = start_seg_t + (end_seg_t - start_seg_t) * (seg / (num_segments - 1))
                a = start_a + (end_a - start_a) * seg_t
                ax = arc_cx + int(math.cos(a) * arc_radius * facing)
                ay = arc_cy + int(math.sin(a) * arc_radius)
                arc_points.append((ax, ay))
            if len(arc_points) >= 2:
                for i in range(len(arc_points) - 1):
                    fade = i / max(1, len(arc_points) - 1)
                    actual_alpha = _NS_kyrenzai._alpha(alpha_val * fade)
                    pygame.draw.line(surface, (*color, actual_alpha),
                                     arc_points[i], arc_points[i + 1], thick)
        # Bright tip at leading edge
        if 0.05 < t < 0.95:
            tip_a = start_a + (end_a - start_a) * t
            tip_x_arc = arc_cx + int(math.cos(tip_a) * arc_radius * facing)
            tip_y_arc = arc_cy + int(math.sin(tip_a) * arc_radius)
            for r in range(8, 0, -1):
                alpha = _NS_kyrenzai._alpha(220 * (8 - r) / 8)
                _NS_kyrenzai._aacircle(surface,
                                        (*_NS_kyrenzai.PALETTE["kagune_hot"], alpha),
                                        (tip_x_arc, tip_y_arc), r)
            _NS_kyrenzai._aacircle(surface, _NS_kyrenzai.PALETTE["kagune_shine"],
                                    (tip_x_arc, tip_y_arc), 2)
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["white"],
                             (tip_x_arc, tip_y_arc, 1, 1))
            # Blood droplet sparks
            for i in range(6):
                sp_a = tip_a + (i - 3) * 0.15
                sp_len = 8 + i
                spx = tip_x_arc + int(math.cos(sp_a) * sp_len * facing)
                spy = tip_y_arc + int(math.sin(sp_a) * sp_len)
                pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["blood_hot"], (spx, spy, 1, 1))
    # ============================================================
    # AMBIENT
    # ============================================================
    def _draw_float_shadow(surface, x, y, phase):
        pulse = math.sin(phase * 0.6) * 0.15 + 0.85
        shadow = pygame.Surface((140, 30), pygame.SRCALPHA)
        for radius in range(14, 0, -1):
            alpha = _NS_kyrenzai._alpha((14 - radius) * 15 * pulse)
            pygame.draw.ellipse(
                shadow, (0, 0, 0, alpha),
                (10 - radius, 15 - radius // 2,
                 120 + radius * 2, radius),
            )
        pygame.draw.ellipse(shadow, (15, 3, 5, 170), (10, 10, 120, 10))
        pygame.draw.ellipse(shadow, (100, 15, 20, 100), (18, 12, 104, 6))
        surface.blit(shadow, (x - 70, y - 15))
    def _draw_blood_wisps(surface, cx, cy, phase, trail=False, facing=1, intense=False):
        """Red blood particles below boss."""
        strength = 1.5 if intense else 1.0
        mist = pygame.Surface((150, 50), pygame.SRCALPHA)
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        for radius in range(34, 3, -3):
            alpha = _NS_kyrenzai._alpha((34 - radius) * 2.8 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kyrenzai.PALETTE["kagune_darkest"], alpha),
                    (75 - radius * 2, 25 - radius // 3,
                     radius * 4, max(3, radius // 2)),
                )
        for radius in range(22, 3, -2):
            alpha = _NS_kyrenzai._alpha((22 - radius) * 3.5 * pulse * strength)
            if alpha > 0:
                pygame.draw.ellipse(
                    mist, (*_NS_kyrenzai.PALETTE["kagune_dark"], alpha),
                    (75 - radius, 25 - radius // 4,
                     radius * 2, max(2, radius // 3)),
                )
        surface.blit(mist, (cx - 75, cy - 10))
        # Rising blood particles
        for i, offset in enumerate((-26, -18, -10, -2, 6, 14, 22, 30, -32)):
            t = (phase * 0.5 + i * 0.13) % 1.0
            sx = cx + offset + int(math.sin(phase + i) * 3)
            sy = cy + 6 - int(t * 28)
            alpha = _NS_kyrenzai._alpha(220 * (1 - t) * strength)
            if alpha <= 0:
                continue
            _NS_kyrenzai._aacircle(surface,
                                    (*_NS_kyrenzai.PALETTE["kagune_darkest"], alpha),
                                    (sx, sy), 2)
            pygame.draw.rect(surface,
                             (*_NS_kyrenzai.PALETTE["kagune_hot"], alpha),
                             (sx, sy - 1, 1, 1))
            pygame.draw.rect(surface,
                             (*_NS_kyrenzai.PALETTE["kagune_shine"], alpha),
                             (sx, sy - 2, 1, 1))
        # Trail
        if trail:
            for i in range(6):
                sx = cx - (i + 1) * 14 * facing
                sy = cy + int(math.sin(phase + i) * 2)
                alpha = _NS_kyrenzai._alpha(160 - i * 25)
                if alpha <= 0:
                    continue
                _NS_kyrenzai._aacircle(surface,
                                        (*_NS_kyrenzai.PALETTE["kagune_darkest"], alpha),
                                        (sx, sy), max(2, 7 - i))
                _NS_kyrenzai._aacircle(surface,
                                        (*_NS_kyrenzai.PALETTE["kagune_dark"], alpha),
                                        (sx, sy), max(1, 5 - i))
                pygame.draw.rect(surface,
                                 (*_NS_kyrenzai.PALETTE["kagune_hot"], alpha),
                                 (sx, sy - 1, 2, 2))
    def _draw_blood_aura(surface, x, y, phase):
        """Massive red blood aura."""
        pulse = math.sin(phase * 0.5) * 0.25 + 0.75
        aura = pygame.Surface((240, 210), pygame.SRCALPHA)
        for radius in range(100, 5, -5):
            alpha = _NS_kyrenzai._alpha((100 - radius) * 1.3 * pulse)
            if alpha > 0:
                _NS_kyrenzai._aacircle(aura,
                                        (*_NS_kyrenzai.PALETTE["kagune_darkest"], alpha),
                                        (120, 105), radius)
        for radius in range(65, 5, -4):
            alpha = _NS_kyrenzai._alpha((65 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kyrenzai._aacircle(aura,
                                        (*_NS_kyrenzai.PALETTE["kagune_dark"], alpha),
                                        (120, 105), radius)
        for radius in range(35, 5, -3):
            alpha = _NS_kyrenzai._alpha((35 - radius) * 1.5 * pulse)
            if alpha > 0:
                _NS_kyrenzai._aacircle(aura,
                                        (*_NS_kyrenzai.PALETTE["kagune_mid"], alpha),
                                        (120, 105), radius)
        surface.blit(aura, (x - 120, y - 105))
        # Floating blood embers
        for i in range(16):
            angle = phase * 0.3 + i * math.pi / 8
            radius = 42 + int(math.sin(phase + i) * 15)
            sx = x + int(math.cos(angle) * radius)
            sy = y - 5 + int(math.sin(angle) * radius * 0.5)
            color = _NS_kyrenzai.PALETTE["kagune_hot"] if i % 2 == 0 \
                else _NS_kyrenzai.PALETTE["blood_hot"]
            pygame.draw.rect(surface, color, (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["kagune_shine"], (sx, sy, 1, 1))
    def _draw_ground_seal(surface, x, y, phase, skill):
        """Ground seal ring."""
        pulse = math.sin(phase * 1.2) * 0.25 + 0.75
        ring = pygame.Surface((180, 58), pygame.SRCALPHA)
        for i, (rw, rh, alpha) in enumerate([
            (82, 24, 200), (68, 20, 220), (54, 15, 220), (40, 11, 200),
        ]):
            offset = int(math.sin(phase * 1.5 + i * 0.5) * 2)
            pygame.draw.ellipse(ring,
                                (*_NS_kyrenzai.PALETTE["kagune_dark"], alpha),
                                (90 - rw + offset, 29 - rh, rw * 2, rh * 2), 2)
            pygame.draw.ellipse(ring,
                                (*_NS_kyrenzai.PALETTE["kagune_mid"], alpha),
                                (90 - rw + offset + 1, 29 - rh + 1,
                                 rw * 2 - 2, rh * 2 - 2), 1)
        for i in range(12):
            angle = phase * 0.3 + i * math.pi / 6
            x1 = 90 + int(math.cos(angle) * 50)
            y1 = 29 + int(math.sin(angle) * 10)
            x2 = 90 + int(math.cos(angle) * 78)
            y2 = 29 + int(math.sin(angle) * 14)
            pygame.draw.line(ring,
                             (*_NS_kyrenzai.PALETTE["kagune_hot"], 230),
                             (x1, y1), (x2, y2), 1)
        if skill:
            pygame.draw.ellipse(ring,
                                (*_NS_kyrenzai.PALETTE["kagune_light"],
                                 _NS_kyrenzai._alpha(180 * pulse)),
                                (15, 12, 150, 34), 1)
        surface.blit(ring, (x - 90, y - 29))
    # ============================================================
    # SKILL Q - KAGUNE SLASH (extended slash - big crescent)
    # ============================================================
    def _draw_kagune_slash(surface, boss, x, y, timer, phase):
        """Massive kagune crescent slash extended."""
        facing = boss.direction
        duration = 45
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.25:
            # Wind up glow
            t = progress / 0.25
            hand_x = x + facing * 16
            hand_y = y - 4
            cr = int(5 + t * 8)
            for r in range(cr + 5, 0, -1):
                alpha = _NS_kyrenzai._alpha(200 * (cr + 5 - r) / (cr + 5))
                _NS_kyrenzai._aacircle(surface,
                                        (*_NS_kyrenzai.PALETTE["kagune_dark"], alpha),
                                        (hand_x, hand_y), r)
            _NS_kyrenzai._aacircle(surface, _NS_kyrenzai.PALETTE["kagune_light"],
                                    (hand_x, hand_y), cr - 2)
            _NS_kyrenzai._aacircle(surface, _NS_kyrenzai.PALETTE["kagune_shine"],
                                    (hand_x, hand_y), max(1, cr - 5))
        else:
            t = (progress - 0.25) / 0.75
            arc_cx = x + facing * 12
            arc_cy = y - 4
            arc_radius = int(55 + t * 40)
            start_a = -math.pi * 0.7
            end_a = math.pi * 0.7
            # Trail
            trail_length = 0.5
            start_seg_t = max(0.0, t - trail_length)
            end_seg_t = min(1.0, t)
            for layer_i, (thick, alpha_mult, color) in enumerate([
                (7, 0.3, _NS_kyrenzai.PALETTE["kagune_darkest"]),
                (6, 0.5, _NS_kyrenzai.PALETTE["kagune_dark"]),
                (5, 0.7, _NS_kyrenzai.PALETTE["kagune_mid"]),
                (4, 0.9, _NS_kyrenzai.PALETTE["kagune_light"]),
                (3, 1.0, _NS_kyrenzai.PALETTE["kagune_hot"]),
                (2, 1.0, _NS_kyrenzai.PALETTE["kagune_shine"]),
                (1, 1.0, _NS_kyrenzai.PALETTE["white"]),
            ]):
                arc_alpha_base = _NS_kyrenzai._alpha(240 * alpha_mult * (1 - t * 0.4))
                arc_points = []
                num_segments = 26
                for seg in range(num_segments):
                    seg_t = start_seg_t + (end_seg_t - start_seg_t) * (seg / (num_segments - 1))
                    a = start_a + (end_a - start_a) * seg_t
                    ax = arc_cx + int(math.cos(a) * arc_radius * facing)
                    ay = arc_cy + int(math.sin(a) * arc_radius)
                    arc_points.append((ax, ay))
                if len(arc_points) >= 2:
                    for i in range(len(arc_points) - 1):
                        fade = i / max(1, len(arc_points) - 1)
                        actual_alpha = _NS_kyrenzai._alpha(arc_alpha_base * fade)
                        pygame.draw.line(surface, (*color, actual_alpha),
                                         arc_points[i], arc_points[i + 1], thick)
            # Blood drops flying off arc
            if 0.05 < t < 0.95:
                tip_a = start_a + (end_a - start_a) * t
                tip_x = arc_cx + int(math.cos(tip_a) * arc_radius * facing)
                tip_y = arc_cy + int(math.sin(tip_a) * arc_radius)
                for i in range(6):
                    drop_a = tip_a + (i - 3) * 0.2
                    drop_r = arc_radius + 5 + i * 2
                    dx = arc_cx + int(math.cos(drop_a) * drop_r * facing)
                    dy = arc_cy + int(math.sin(drop_a) * drop_r)
                    pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["kagune_hot"], (dx, dy, 1, 1))
                    pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["blood_hot"], (dx, dy, 1, 1))
            # Sweet spot at center
            if t > 0.4:
                sweet_a = 0
                sweet_x = arc_cx + int(math.cos(sweet_a) * arc_radius * facing)
                sweet_y = arc_cy + int(math.sin(sweet_a) * arc_radius)
                st = (t - 0.4) / 0.6
                burst_r = int(10 + st * 20)
                burst_alpha = _NS_kyrenzai._alpha(240 * (1 - st))
                _NS_kyrenzai._aacircle(surface,
                                        (*_NS_kyrenzai.PALETTE["kagune_darkest"], burst_alpha),
                                        (sweet_x, sweet_y), burst_r + 3, 3)
                _NS_kyrenzai._aacircle(surface,
                                        (*_NS_kyrenzai.PALETTE["kagune_dark"], burst_alpha),
                                        (sweet_x, sweet_y), burst_r, 2)
                _NS_kyrenzai._aacircle(surface,
                                        (*_NS_kyrenzai.PALETTE["kagune_light"], burst_alpha),
                                        (sweet_x, sweet_y), max(1, burst_r - 6), 1)
                for i in range(10):
                    angle_s = i * math.pi / 5
                    ex = sweet_x + int(math.cos(angle_s) * burst_r)
                    ey = sweet_y + int(math.sin(angle_s) * burst_r * 0.7)
                    pygame.draw.rect(surface,
                                     (*_NS_kyrenzai.PALETTE["kagune_shine"], burst_alpha),
                                     (ex, ey, 2, 2))
    # ============================================================
    # SKILL W - TENDRIL SNARE (kagune tentacles shoot forward to grab)
    # ============================================================
    def _draw_tendril_snare(surface, boss, x, y, timer, phase):
        """Kagune tendrils shoot forward, wrap around target, pull."""
        facing = boss.direction
        duration = 60
        progress = max(0.0, min(1.0, 1 - timer / duration))
        tx, ty = _NS_kyrenzai._target_position(boss, x, y)
        start_x = x + facing * 8
        start_y = y - 6
        if progress < 0.2:
            # Charge at back (kagune building up)
            t = progress / 0.2
            for i in range(5):
                base_angle = i * math.pi / 2.5 + phase
                cx_charge = start_x + int(math.cos(base_angle) * 8)
                cy_charge = start_y + int(math.sin(base_angle) * 8)
                cr = int(3 + t * 5)
                for r in range(cr + 3, 0, -1):
                    alpha = _NS_kyrenzai._alpha(200 * (cr + 3 - r) / (cr + 3))
                    _NS_kyrenzai._aacircle(surface,
                                            (*_NS_kyrenzai.PALETTE["kagune_dark"], alpha),
                                            (cx_charge, cy_charge), r)
        elif progress < 0.65:
            # TENDRILS EXTEND to target
            t = (progress - 0.2) / 0.45
            # Multiple tendrils reaching for target
            num_tendrils = 4
            for tend_i in range(num_tendrils):
                # Each tendril offset slightly
                offset_angle = (tend_i - 1.5) * 0.2
                # Ending point
                end_x = int(start_x + (tx - start_x) * t)
                end_y = int(start_y + (ty - start_y) * t)
                # Draw wavy tendril path
                num_segs = int(20 * t)
                prev_x, prev_y = start_x, start_y
                for seg in range(1, num_segs + 1):
                    seg_t = seg / max(1, num_segs)
                    sx = int(start_x + (end_x - start_x) * seg_t)
                    sy = int(start_y + (end_y - start_y) * seg_t)
                    # Wave
                    perp_angle = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
                    wave = math.sin(seg_t * math.pi * 4 + phase * 2 + tend_i) * 6
                    sx += int(math.cos(perp_angle) * (wave + offset_angle * 15))
                    sy += int(math.sin(perp_angle) * (wave + offset_angle * 15))
                    thickness = max(1, 4 - seg // 6)
                    _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                                         (prev_x + 1, prev_y + 1),
                                         (sx + 1, sy + 1), thickness + 1)
                    _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["kagune_darkest"],
                                         (prev_x, prev_y), (sx, sy), thickness)
                    _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["kagune_dark"],
                                         (prev_x, prev_y), (sx, sy),
                                         max(1, thickness - 1))
                    _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["kagune_mid"],
                                         (prev_x, prev_y - 1), (sx, sy - 1),
                                         max(1, thickness - 2))
                    prev_x, prev_y = sx, sy
                # Sharp tip at end (bladed)
                if num_segs > 0:
                    tip_x = prev_x
                    tip_y = prev_y
                    _NS_kyrenzai._aacircle(surface, _NS_kyrenzai.PALETTE["kagune_hot"],
                                            (tip_x, tip_y), 2)
                    _NS_kyrenzai._aacircle(surface, _NS_kyrenzai.PALETTE["kagune_shine"],
                                            (tip_x, tip_y), 1)
                    pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["white"],
                                     (tip_x, tip_y, 1, 1))
        else:
            # PULL PHASE: tendrils locked on target, pulling
            t = (progress - 0.65) / 0.35
            # Static tendrils
            num_tendrils = 4
            for tend_i in range(num_tendrils):
                offset_angle = (tend_i - 1.5) * 0.2
                num_segs = 20
                prev_x, prev_y = start_x, start_y
                for seg in range(1, num_segs + 1):
                    seg_t = seg / num_segs
                    sx = int(start_x + (tx - start_x) * seg_t)
                    sy = int(start_y + (ty - start_y) * seg_t)
                    perp_angle = math.atan2(ty - start_y, tx - start_x) + math.pi / 2
                    wave = math.sin(seg_t * math.pi * 4 + phase * 3 + tend_i) * (6 * (1 - t))
                    sx += int(math.cos(perp_angle) * (wave + offset_angle * 15))
                    sy += int(math.sin(perp_angle) * (wave + offset_angle * 15))
                    thickness = max(1, 4 - seg // 6)
                    _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["kagune_darkest"],
                                         (prev_x, prev_y), (sx, sy), thickness)
                    _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["kagune_mid"],
                                         (prev_x, prev_y), (sx, sy),
                                         max(1, thickness - 1))
                    prev_x, prev_y = sx, sy
            # Pull impact at target
            pull_r = int(12 + t * 15)
            alpha = _NS_kyrenzai._alpha(220 * (1 - t))
            _NS_kyrenzai._aacircle(surface, (*_NS_kyrenzai.PALETTE["kagune_darkest"], alpha),
                                    (tx, ty), pull_r + 3, 3)
            _NS_kyrenzai._aacircle(surface, (*_NS_kyrenzai.PALETTE["kagune_dark"], alpha),
                                    (tx, ty), pull_r, 2)
            _NS_kyrenzai._aacircle(surface, (*_NS_kyrenzai.PALETTE["kagune_hot"], alpha),
                                    (tx, ty), max(1, pull_r - 6), 1)
            # Pull arrows
            angle_pull = math.atan2(start_y - ty, start_x - tx)
            for i in range(4):
                offset_angle_p = angle_pull + (i - 1.5) * 0.3
                arrow_x = tx + int(math.cos(offset_angle_p) * pull_r * 0.7)
                arrow_y = ty + int(math.sin(offset_angle_p) * pull_r * 0.7)
                pygame.draw.line(surface, (*_NS_kyrenzai.PALETTE["kagune_hot"], alpha),
                                 (arrow_x, arrow_y),
                                 (arrow_x + int(math.cos(offset_angle_p) * 6),
                                  arrow_y + int(math.sin(offset_angle_p) * 6)), 2)
    # ============================================================
    # SKILL E - CRIMSON BLOOM (tentacles erupt around boss AoE)
    # ============================================================
    def _draw_crimson_bloom_ground(surface, boss, x, y, timer, phase):
        """Ground marks around boss."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_kyrenzai.PALETTE["kagune_darkest"], 200),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_kyrenzai.PALETTE["kagune_dark"], 180),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
    def _draw_crimson_bloom_foreground(surface, boss, x, y, timer, phase):
        """Multiple kagune tentacles erupting around boss in AoE."""
        duration = 80
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(55 * min(1.0, progress * 3))
        if r < 5:
            return
        # 8 tentacles erupting outward from boss center
        num_tents = 8
        for tent_i in range(num_tents):
            base_angle = tent_i * math.pi * 2 / num_tents + phase * 0.3
            # Tentacle grows outward + up
            growth_t = min(1.0, progress * 3)
            tent_length = int(r * growth_t)
            # Draw tentacle segments
            num_segs = 10
            prev_x = x
            prev_y = y - 4
            for seg in range(1, num_segs + 1):
                seg_t = seg / num_segs
                # Along angle, curves upward at end
                fwd_dist = tent_length * seg_t
                seg_x = x + int(math.cos(base_angle) * fwd_dist)
                # Curves upward
                seg_y = y - 4 + int(math.sin(base_angle) * fwd_dist * 0.5)
                seg_y -= int(math.sin(seg_t * math.pi) * 15)  # arch upward
                # Wave
                wave = math.sin(phase * 2 + seg_t * math.pi * 3 + tent_i) * 4 * seg_t
                perp_a = base_angle + math.pi / 2
                seg_x += int(math.cos(perp_a) * wave)
                seg_y += int(math.sin(perp_a) * wave)
                thickness = max(1, 5 - seg // 2)
                _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["shadow_deep"],
                                     (prev_x + 1, prev_y + 1),
                                     (seg_x + 1, seg_y + 1), thickness + 1)
                _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["kagune_darkest"],
                                     (prev_x, prev_y), (seg_x, seg_y), thickness)
                _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["kagune_dark"],
                                     (prev_x, prev_y), (seg_x, seg_y),
                                     max(1, thickness - 1))
                _NS_kyrenzai._aaline(surface, _NS_kyrenzai.PALETTE["kagune_mid"],
                                     (prev_x, prev_y - 1), (seg_x, seg_y - 1),
                                     max(1, thickness - 2))
                prev_x, prev_y = seg_x, seg_y
            # Sharp tip
            tip_x = prev_x
            tip_y = prev_y
            for tr in range(5, 0, -1):
                alpha = _NS_kyrenzai._alpha(200 * (5 - tr) / 5)
                _NS_kyrenzai._aacircle(surface,
                                        (*_NS_kyrenzai.PALETTE["kagune_hot"], alpha),
                                        (tip_x, tip_y), tr)
            _NS_kyrenzai._aacircle(surface, _NS_kyrenzai.PALETTE["kagune_shine"],
                                    (tip_x, tip_y), 1)
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["white"], (tip_x, tip_y, 1, 1))
        # Blood spatter around boss
        for i in range(15):
            spatter_a = i * math.pi / 7.5
            spatter_r = int(r * (0.5 + 0.5 * math.sin(phase * 2 + i)))
            sx = x + int(math.cos(spatter_a) * spatter_r)
            sy = y + int(math.sin(spatter_a) * spatter_r * 0.5)
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["blood_hot"], (sx, sy, 2, 2))
            pygame.draw.rect(surface, _NS_kyrenzai.PALETTE["blood_shine"], (sx, sy, 1, 1))
    # ============================================================
    # SKILL R - GHOUL AWAKENING (full transformation + burst)
    # ============================================================
    def _draw_ghoul_awakening_ground(surface, boss, x, y, timer, phase):
        """Ground marks (large ring)."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        r = int(65 * min(1.0, progress * 3))
        if r > 3:
            pygame.draw.ellipse(surface, (*_NS_kyrenzai.PALETTE["kagune_darkest"], 220),
                                (x - r, y + 40 - r // 3, r * 2, r * 2 // 3))
            pygame.draw.ellipse(surface, (*_NS_kyrenzai.PALETTE["kagune_dark"], 200),
                                (x - r + 3, y + 40 - r // 3 + 2,
                                 r * 2 - 6, r * 2 // 3 - 4))
            pygame.draw.ellipse(surface, (*_NS_kyrenzai.PALETTE["kagune_mid"], 180),
                                (x - r + 8, y + 40 - r // 3 + 4,
                                 r * 2 - 16, r * 2 // 3 - 8))
    def _draw_ghoul_awakening_foreground(surface, boss, x, y, timer, phase):
        """Awakening burst + kagune wings expanding + shockwave."""
        duration = 100
        progress = max(0.0, min(1.0, 1 - timer / duration))
        if progress < 0.3:
            # Charging: gathering red energy around boss
            t = progress / 0.3
            # Rising energy
            for i in range(12):
                angle = phase * 2 + i * math.pi / 6
                dist = 30 * (1 - t)
                gx = x + int(math.cos(angle) * dist)
                gy = y + int(math.sin(angle) * dist * 0.7)
                alpha = _NS_kyrenzai._alpha(200 * t)
                _NS_kyrenzai._aacircle(surface,
                                        (*_NS_kyrenzai.PALETTE["kagune_dark"], alpha),
                                        (gx, gy), 3)
                _NS_kyrenzai._aacircle(surface,
                                        (*_NS_kyrenzai.PALETTE["kagune_hot"], alpha),
                                        (gx, gy), 2)
                pygame.draw.rect(surface,
                                 (*_NS_kyrenzai.PALETTE["kagune_shine"], alpha),
                                 (gx, gy, 1, 1))
        elif progress < 0.6:
            # BURST: massive expanding red shockwave + tentacle wings
            t = (progress - 0.3) / 0.3
            intensity = math.sin(t * math.pi)
            # Multiple expanding shockwave rings
            for ring_i in range(4):
                ring_t = (phase * 2 + ring_i * 0.3) % 1.0
                ring_r = int(80 * ring_t)
                if ring_r < 5:
                    continue
                alpha = _NS_kyrenzai._alpha(230 * (1 - ring_t) * intensity)
                for layer_i, (thick, alpha_mult, color) in enumerate([
                    (5, 0.4, _NS_kyrenzai.PALETTE["kagune_darkest"]),
                    (4, 0.6, _NS_kyrenzai.PALETTE["kagune_dark"]),
                    (3, 0.8, _NS_kyrenzai.PALETTE["kagune_mid"]),
                    (2, 1.0, _NS_kyrenzai.PALETTE["kagune_hot"]),
                    (1, 1.0, _NS_kyrenzai.PALETTE["kagune_shine"]),
                ]):
                    actual_alpha = _NS_kyrenzai._alpha(alpha * alpha_mult)
                    _NS_kyrenzai._aacircle(surface, (*color, actual_alpha),
                                            (x, y - 2), ring_r, thick)
            # Central burst
            for r in range(20, 0, -1):
                alpha = _NS_kyrenzai._alpha(200 * (20 - r) / 20 * intensity)
                _NS_kyrenzai._aacircle(surface,
                                        (*_NS_kyrenzai.PALETTE["kagune_hot"], alpha),
                                        (x, y - 2), r)
            _NS_kyrenzai._aacircle(surface, _NS_kyrenzai.PALETTE["kagune_shine"],
                                    (x, y - 2), 4)
            _NS_kyrenzai._aacircle(surface, _NS_kyrenzai.PALETTE["white"],
                                    (x, y - 2), 2)
            # Blood particles flying outward
            for i in range(20):
                spatter_a = i * math.pi / 10 + phase
                spatter_r = int(50 * intensity + i * 2)
                sx = x + int(math.cos(spatter_a) * spatter_r)
                sy = y + int(math.sin(spatter_a) * spatter_r * 0.7)
                alpha_s = _NS_kyrenzai._alpha(240 * intensity)
                pygame.draw.rect(surface,
                                 (*_NS_kyrenzai.PALETTE["kagune_hot"], alpha_s),
                                 (sx, sy, 2, 2))
                pygame.draw.rect(surface,
                                 (*_NS_kyrenzai.PALETTE["kagune_shine"], alpha_s),
                                 (sx, sy, 1, 1))
        else:
            # Sustained transformation - extra tentacles already drawn on body via r_active
            # Add lingering red aura
            t = (progress - 0.6) / 0.4
            pulse = math.sin(phase * 3) * 0.3 + 0.7
            aura_r = int(50 + math.sin(phase * 2) * 5)
            for r in range(aura_r, aura_r - 8, -1):
                alpha = _NS_kyrenzai._alpha(120 * (1 - t) * pulse)
                _NS_kyrenzai._aacircle(surface,
                                        (*_NS_kyrenzai.PALETTE["kagune_dark"], alpha),
                                        (x, y - 4), r)
            # Rising red embers
            for i in range(12):
                rise_t = (phase * 0.8 + i * 0.12) % 1.0
                rx = x + int(math.sin(phase + i) * 30)
                ry = y - int(rise_t * 40)
                alpha = _NS_kyrenzai._alpha(220 * (1 - rise_t))
                if alpha > 0:
                    _NS_kyrenzai._aacircle(surface,
                                            (*_NS_kyrenzai.PALETTE["kagune_dark"], alpha),
                                            (rx, ry), 2)
                    pygame.draw.rect(surface,
                                     (*_NS_kyrenzai.PALETTE["kagune_hot"], alpha),
                                     (rx, ry, 1, 1))
                    pygame.draw.rect(surface,
                                     (*_NS_kyrenzai.PALETTE["kagune_shine"], alpha),
                                     (rx, ry, 1, 1))

# ═══════════════════════════════════════════════════════
# ENTRY POINTS (level modul) - dipakai bosses/base_boss.py
# ═══════════════════════════════════════════════════════
def draw_azkharion(surface, boss, x, y):
    """Entry point azkharion."""
    return _NS_azkharion.draw_azkharion(surface, boss, x, y)


def draw_thargoroth(surface, boss, x, y):
    """Entry point thargoroth."""
    return _NS_thargoroth.draw_thargoroth(surface, boss, x, y)


def draw_zahkareth(surface, boss, x, y):
    """Entry point zahkareth."""
    return _NS_zahkareth.draw_zahkareth(surface, boss, x, y)


def draw_kyrenzai(surface, boss, x, y):
    """Entry point kyrenzai."""
    return _NS_kyrenzai.draw_kyrenzai(surface, boss, x, y)
